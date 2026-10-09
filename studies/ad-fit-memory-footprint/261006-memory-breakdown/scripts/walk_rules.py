#!/usr/bin/env python3
"""Walk a SCETlib compressed-rule blob (rules v13, SCTRULEV) WITHOUT loading it:
read every length prefix and seek over the payloads. Mirrors
DrellYan::_load_bin_rules at scetlib-cms 2dd978a (py/qT/DrellYanAD.cpp:10542).

--old-v8 --opts-size 56: the rules v8 layout of b66f8de (260827 cache).
Also accepts a stream (e.g. a zip member opened via zipfile) via --stream, which
reads-and-discards payloads instead of seeking (used for the old v8 cache).

Prints per-component byte totals, and per-rule (nsites, nv) so the runtime
caches that the replay allocates per rule can be predicted:
  muf_fit      = nsites * 16*2*23*6 doubles            (nominal muF fits)
  muf_fit_var  = nsites * nv * nlive * 4 floats        (member-row muF fits)
"""
import argparse, json, struct, sys, zipfile
import numpy as np


class R:
    def __init__(self, f, seekable):
        self.f, self.seekable, self.pos = f, seekable, 0

    def read(self, n):
        b = self.f.read(n)
        if len(b) != n:
            raise EOFError(f"truncated at {self.pos}")
        self.pos += n
        return b

    def skip(self, n):
        if n == 0:
            return
        if self.seekable:
            self.f.seek(n, 1)
            self.pos += n
        else:
            while n:
                k = min(n, 1 << 26)
                self.read(k)
                n -= k

    def u64(self):
        return struct.unpack("<Q", self.read(8))[0]

    def u32(self):
        return struct.unpack("<I", self.read(4))[0]

    def i32(self):
        return struct.unpack("<i", self.read(4))[0]

    def f64(self):
        return struct.unpack("<d", self.read(8))[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--member", default=None, help="zip member (stream mode)")
    ap.add_argument("--opts-size", type=int, default=80)
    ap.add_argument("--out", default=None, help="json with per-rule counts")
    ap.add_argument(
        "--old-v8",
        action="store_true",
        help="rules v8 layout (b66f8de): see layout notes in logbook",
    )
    a = ap.parse_args()
    if a.member:
        z = zipfile.ZipFile(a.path)
        fh = z.open(a.member)
        # skip the .npy header: magic(6) ver(2) hlen(2 or 4) header
        m = fh.read(8)
        assert m[:6] == b"\x93NUMPY", m
        hl = (
            struct.unpack("<H", fh.read(2))[0]
            if m[6] == 1
            else struct.unpack("<I", fh.read(4))[0]
        )
        hdr = fh.read(hl)
        print("npy header", hdr[:120])
        r = R(fh, False)
    else:
        r = R(open(a.path, "rb"), True)
    magic = r.read(8)
    print("magic", magic)
    if magic[7:8] == b"V":
        ver = r.u32()
    else:
        ver = magic[7] - 48
    print("version", ver)
    sz_site, sz_g, sz_h, sz_nd = r.u32(), r.u32(), r.u32(), r.u32()
    print(f"sizeof Site={sz_site} GlobalData={sz_g} HardData={sz_h} NodeData={sz_nd}")
    fn = r.u64()
    fp = r.read(fn).decode(errors="replace")
    na = r.u64()
    r.skip(8 * na)
    r.skip(a.opts_size)
    n_eig = r.i32()
    as_idx = r.i32()
    r.f64()
    r.f64()
    muf_idx = r.i32()
    if a.old_v8:
        r.f64()
        nm = 0  # muf_lnstep; no member-identity block before v12
    else:
        nm = r.u64()
        for _ in range(nm):
            ls = r.u64()
            r.skip(ls)
            r.i32()
    nb = r.u64()
    print(
        f"n_params(anchor)={na} n_eig={n_eig} as_idx={as_idx} muf_idx={muf_idx} n_member_ids={nm} n_rules={nb}"
    )
    tot = dict(
        grid=0,
        sites=0,
        g=0,
        h=0,
        has_asym=0,
        nd=0,
        c_hess=0,
        c_grad=0,
        fo_w=0,
        var_w=0,
        var_nd=0,
        var_cgrad=0,
        prefixes=0,
    )
    per = []

    def vec(es, key):
        n = r.u64()
        tot["prefixes"] += 8
        tot[key] += n * es
        r.skip(n * es)
        return n

    for ib in range(nb):
        key = struct.unpack("<6d", r.read(48))
        ngrid = vec(32, "grid")
        ns = vec(sz_site, "sites")
        ng = vec(sz_g, "g")
        vec(sz_h, "h")
        vec(sz_h, "h")
        vec(1, "has_asym")
        nnd = vec(sz_nd, "nd")
        r.f64()
        vec(8, "c_grad")
        vec(8, "c_hess")
        vec(8, "fo_w")
        r.u64()
        r.f64()
        r.u32()
        r.read(1)
        nv = r.u64()
        for _ in range(nv):
            vec(8, "var_w")
            vec(sz_nd, "var_nd")
            r.f64()
            vec(8, "var_cgrad")
            if a.old_v8:
                r.f64()
                r.f64()
                r.i32()  # g_muf_ratio, g_v_muf, is_muf
        per.append(dict(key=key, ngrid=ngrid, nsites=ns, ng=ng, nnd=nnd, nv=nv))
        if ib % 100 == 0:
            print(
                f"  rule {ib}: qT[{key[4]},{key[5]}] Y[{key[2]},{key[3]}] grid={ngrid} sites={ns} nv={nv} pos={r.pos/1e9:.2f}GB",
                flush=True,
            )
    print("end pos", r.pos)
    S = sum(p["nsites"] for p in per)
    SV = sum(p["nsites"] * p["nv"] for p in per)
    out = dict(
        path=a.path,
        version=ver,
        sizes=dict(site=sz_site, g=sz_g, h=sz_h, nd=sz_nd),
        n_rules=nb,
        n_eig=n_eig,
        total_bytes=r.pos,
        components=tot,
        sum_sites=S,
        sum_sites_x_nv=SV,
        per_rule=per,
    )
    for k, v in tot.items():
        print(f"  {k:10s} {v/1e9:10.3f} GB")
    print(
        f'sum nsites={S}  sum nsites*nv={SV}  median nsites={int(np.median([p["nsites"] for p in per]))}  nv set={sorted(set(p["nv"] for p in per))}'
    )
    if a.out:
        json.dump(out, open(a.out, "w"))


main()
