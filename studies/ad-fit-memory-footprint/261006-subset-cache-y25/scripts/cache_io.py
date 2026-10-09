"""Shared helpers for the |Y|-subset of a SCETlib-AD cache (rules v13 / fo v14, scetlib-cms 2dd978a).

walk_rules(path)       seek-only walk of a flat rules payload (cache.rules.bin): header end, per-record
                       (start, end, key). Mirrors DrellYan::_load_bin_rules (py/qT/DrellYanAD.cpp:10542)
                       and scetlib_cache._parse_rules field for field.
emit_fo(parsed, idx)   the inverse of scetlib_cache.parse_fo_blob restricted to the bins at positions
                       `idx` (source order kept). emit_fo(parsed, all) must reproduce the source blob
                       byte for byte -- checked by the build before anything is written.
"""

import struct

import numpy as np

U64 = struct.Struct("<Q")
I32 = struct.Struct("<i")
U32 = struct.Struct("<I")
F64 = struct.Struct("<d")


class _F:
    def __init__(self, f):
        self.f, self.pos = f, 0

    def read(self, n):
        b = self.f.read(n)
        if len(b) != n:
            raise EOFError(f"truncated at {self.pos} (+{n})")
        self.pos += n
        return b

    def skip(self, n):
        if n:
            self.f.seek(n, 1)
            self.pos += n

    def u64(self):
        return U64.unpack(self.read(8))[0]

    def vec(self, es):
        n = self.u64()
        self.skip(n * es)
        return n


def walk_rules(path, opts_size=80):
    """Return dict(header=bytes up to (excluding) the n_bins u64, nb_pos, n_bins, records=[(start,end,key)],
    sizes, n_sites=[...], n_var=[...], end)."""
    with open(path, "rb") as fh:
        r = _F(fh)
        magic = r.read(8)
        assert magic[:7] == b"SCTRULE", magic
        ver = U32.unpack(r.read(4))[0] if magic[7:8] == b"V" else magic[7] - 48
        sz_site, sz_g, sz_h, sz_nd = (U32.unpack(r.read(4))[0] for _ in range(4))
        fn = r.u64()
        r.skip(fn)  # fingerprint
        na = r.u64()
        r.skip(8 * na)  # anchor
        r.skip(opts_size)  # Bin_rule_opts (one raw POD)
        r.skip(4 + 4 + 8 + 8 + 4)  # n_eig, as_idx, as_cen, as_step, muf_idx
        nm = r.u64()
        for _ in range(nm):
            ls = r.u64()
            r.skip(ls)
            r.skip(4)
        nb_pos = r.pos
        nb = r.u64()
        recs, nsites, nvar = [], [], []
        for _ in range(nb):
            s = r.pos
            key = r.read(48)
            r.vec(32)  # grid
            ns = r.vec(sz_site)  # sites
            r.vec(sz_g)  # g
            r.vec(sz_h)  # h_incl
            r.vec(sz_h)  # h_asym
            r.vec(1)  # has_asym
            r.vec(sz_nd)  # nd
            r.skip(8)  # c_val
            r.vec(8)  # c_grad
            r.vec(8)  # c_hess
            r.vec(8)  # fo_w
            r.skip(8 + 8 + 4 + 1)  # n_sites_full, resid, n_iter, capped
            nv = r.u64()
            for _ in range(nv):
                r.vec(8)  # w
                r.vec(sz_nd)  # nd
                r.skip(8)  # c_val
                r.vec(8)  # c_grad
            recs.append((s, r.pos, key))
            nsites.append(ns)
            nvar.append(nv)
        end = r.pos
        fh.seek(0, 2)
        fsize = fh.tell()
        fh.seek(0)
        header = fh.read(nb_pos)
    if end != fsize:
        raise ValueError(f"{path}: walk ended at {end}, file is {fsize} bytes")
    return dict(
        version=ver,
        sizes=(sz_site, sz_g, sz_h, sz_nd),
        header=header,
        nb_pos=nb_pos,
        n_bins=nb,
        records=recs,
        n_sites=nsites,
        n_var=nvar,
        end=end,
    )


def emit_fo(p, idx):
    """Fixed-order blob (fo v14, SCETFOGE) with only the bins at positions `idx` of the source order.

    Every block is re-emitted exactly as scetlib_cache.parse_fo_blob consumed it:
      grid      {key: node block}, source (file) order, filtered by key
      deltas    per member, 9 doubles per bin (kFoVarStride), gathered by position
      var_bins  6 doubles per bin, gathered
      bilin     B[mslot][d1][d2][bin][k=9], gathered on the bin axis, with its own bins list
      poly      {window: {key: raw}}, every window kept (even if it empties), keys filtered in file order
      var_g     one (mu, data) block per bin, gathered
    """
    idx = np.asarray(idx, dtype=np.int64)
    vb = np.asarray(p["var_bins"]).reshape(-1, 6)
    nb = vb.shape[0]
    keys = [vb[i].astype("<f8").tobytes() for i in idx]
    keyset = set(keys)
    out = [b"SCETFOG" + p["version"], U64.pack(len(p["fingerprint"])), p["fingerprint"]]
    g = [(k, v) for k, v in p["grid"].items() if k in keyset]
    if len(g) != len(keys):
        raise ValueError("fixed-order grid does not cover the kept bins")
    out.append(U64.pack(len(g)) + b"".join(k + v for k, v in g))
    out.append(U64.pack(len(p["deltas"])))
    if p["deltas"]:
        m = p["meta"]
        out.append(
            I32.pack(m["n_eig"])
            + F64.pack(m["as_cen"])
            + F64.pack(m["as_step"])
            + F64.pack(m["as_anchor"])
            + I32.pack(m["muf_index"])
        )
        out.append(U64.pack(6 * len(idx)))
        out.append(vb[idx].astype("<f8").tobytes())
        for d in p["deltas"]:
            a = np.frombuffer(d, dtype="<f8")
            if a.size != 9 * nb:
                raise ValueError(
                    f"member delta has {a.size} doubles, expected 9 x {nb}"
                )
            s = a.reshape(nb, 9)[idx]
            out.append(U64.pack(s.size))
            out.append(np.ascontiguousarray(s).tobytes())
    b = p["bilin"]
    if b is None:
        pass  # pre-v7: no form block at all (cannot happen for v14; parse would have left r not at end)
    elif b["nd"] > 1:
        bb = np.asarray(b["bins"]).reshape(-1, 6)
        if not np.array_equal(bb.view(np.uint64), vb.view(np.uint64)):
            raise ValueError("quadratic-form bins are not the variation bins")
        B = np.asarray(b["B"]).reshape(b["nmuf"], b["nd"], b["nd"], nb, 9)[
            :, :, :, idx, :
        ]
        out.append(
            I32.pack(b["nd"])
            + I32.pack(b["nmuf"])
            + F64.pack(b["as_anchor"])
            + I32.pack(b["n_eig"])
        )
        out.append(U64.pack(6 * len(idx)) + bb[idx].astype("<f8").tobytes())
        out.append(U64.pack(B.size) + np.ascontiguousarray(B, dtype="<f8").tobytes())
    else:
        out.append(I32.pack(b["nd"]))
    if p["poly"] or p["var_g"] is not None:
        out.append(U64.pack(len(p["poly"])))
        for j0, bins2 in p["poly"].items():
            kept = [(k, v) for k, v in bins2.items() if k in keyset]
            out.append(
                I32.pack(j0) + U64.pack(len(kept)) + b"".join(k + v for k, v in kept)
            )
    if p["var_g"] is not None:
        if len(p["var_g"]) != nb:
            raise ValueError("group-resolved member rows do not have one block per bin")
        out.append(U64.pack(len(idx)))
        for i in idx:
            mu, data = p["var_g"][i]
            out.append(
                U64.pack(mu.size)
                + mu.astype("<f8").tobytes()
                + U64.pack(data.size)
                + data.astype("<f8").tobytes()
            )
    return b"".join(out)
