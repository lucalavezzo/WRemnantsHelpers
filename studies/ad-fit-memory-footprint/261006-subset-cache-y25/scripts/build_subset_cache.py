#!/usr/bin/env python3
"""Build a |Y| <= YMAX bin subset of a SCETlib-AD cache (rules v13 / fo v14) -- the inverse of
scetlib_cache.merge_bin_caches, done by streaming.

Bins are self-contained (merge_bin_caches docstring), so a subset is a GATHER:
  rules  header (magic..member identities) verbatim, n_bins rewritten, kept records verbatim, source order.
         Streamed from the source's flat cache.rules.bin, never held in memory (143.5 GB).
  fo     parsed with scetlib_cache.parse_fo_blob (1.05 GB) and re-emitted for the kept bins in the SAME
         order as the rules (the replay indexes fo member deltas by rule position). The emitter is first
         checked to reproduce the full source blob byte for byte.
  bins   bins[keep]; format/n_eig/has_as/has_muf/anchor/names copied as their raw .npy bytes.
  conf   cache.conf with Grid_Y cut at YMAX (Grid_* are not in any fingerprint; the bins come from `bins`).
The npz is written member by member in the source order with ZIP_DEFLATED (np.savez_compressed's
settings); rules.npy is streamed through the zip writer.

usage: build_subset_cache.py --src DIR --out DIR [--ymax 2.5]
"""
import argparse
import hashlib
import io
import json
import os
import re
import shutil
import sys
import time
import zipfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cache_io  # noqa: E402
import scetlib_cache  # noqa: E402  (SCETlib py/, on PYTHONPATH via agent_setup.sh)

SMALL = ("format", "n_eig", "has_as", "has_muf", "anchor", "names")
CHUNK = 1 << 26


def log(*a):
    print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ymax", type=float, default=2.5)
    ap.add_argument(
        "--conf-only",
        action="store_true",
        help="only (re)write cache.conf + build log copy",
    )
    ap.add_argument(
        "--dry-run", action="store_true", help="walk + fo checks only, write nothing"
    )
    a = ap.parse_args()
    src_npz = os.path.join(a.src, "cache.npz")
    src_rules = os.path.join(a.src, "cache.rules.bin")
    if not a.dry_run:
        os.makedirs(a.out, exist_ok=True)
    out_npz = os.path.join(a.out, "cache.npz")
    if a.conf_only:
        with np.load(src_npz, allow_pickle=False) as d:
            bins = np.ascontiguousarray(d["bins"], dtype="<f8")
        keep = np.flatnonzero(bins[:, 3] <= a.ymax + 1e-12)
        write_conf(a, keep, bins[keep])
        log("conf written")
        return
    if os.path.exists(out_npz):
        raise SystemExit(f"{out_npz} exists; refusing to overwrite")

    # the flat rules file must be the current extraction of THIS npz's rules member
    with open(os.path.join(a.src, "cache.rules.json")) as f:
        side = json.load(f)
    with zipfile.ZipFile(src_npz) as z:
        names = [i.filename for i in z.infolist()]
        ri = z.getinfo("rules.npy")
        if (ri.CRC, ri.file_size, ri.compress_size) != (
            side["crc32"],
            side["file_size"],
            side["compress_size"],
        ):
            raise SystemExit(
                "source cache.rules.bin sidecar does not match cache.npz's rules member"
            )
        raw_small = {k: z.read(k + ".npy") for k in SMALL}
    if os.path.getsize(src_rules) != side["payload_bytes"]:
        raise SystemExit("source cache.rules.bin is truncated")
    log("source members:", names)

    with np.load(src_npz, allow_pickle=False) as d:
        bins = np.ascontiguousarray(d["bins"], dtype="<f8")
        fo_src = d["fo"].tobytes()
        fmt = int(d["format"])
    if fmt != scetlib_cache.FORMAT:
        raise SystemExit(
            f"cache format {fmt}, this scetlib_cache reads {scetlib_cache.FORMAT}"
        )
    nb = bins.shape[0]
    keep = np.flatnonzero(bins[:, 3] <= a.ymax + 1e-12)
    drop = np.flatnonzero(bins[:, 3] > a.ymax + 1e-12)
    straddle = np.flatnonzero(
        (bins[:, 2] < a.ymax - 1e-12) & (bins[:, 3] > a.ymax + 1e-12)
    )
    if straddle.size:
        raise SystemExit(
            f"{straddle.size} bins straddle |Y| = {a.ymax}; not a clean cut"
        )
    log(f"{nb} bins; keeping {keep.size} with Y_hi <= {a.ymax}, dropping {drop.size}")

    # ---- rules: walk the source (seeks only) ----
    t0 = time.time()
    W = cache_io.walk_rules(src_rules)
    log(
        f"rules walked in {time.time() - t0:.1f} s: v{W['version']} sizes {W['sizes']} n_bins {W['n_bins']} end {W['end']}"
    )
    if W["n_bins"] != nb:
        raise SystemExit("rule count != bins")
    for j, (_, _, key) in enumerate(W["records"]):
        if key != bins[j].tobytes():
            raise SystemExit(f"rule {j} key is not bins[{j}]")
    # the header must be what SCETlib's own parser consumes before the bins: a zero-bin blob made of it parses
    p0 = scetlib_cache.parse_rule_blob(W["header"] + cache_io.U64.pack(0))
    if len(p0["head"]) + 28 + len(p0["meta_tail_raw"]) != W["nb_pos"]:
        raise SystemExit("header length disagrees with scetlib_cache._parse_rules")
    log(
        f"rules header {W['nb_pos']} B, opts {len(p0['opts_raw'])} B, meta {p0['meta']}"
    )
    rec = [W["records"][j] for j in keep]
    payload = W["nb_pos"] + 8 + sum(e - s for s, e, _ in rec)
    log(
        f"subset rules payload {payload} B ({payload / 1e9:.3f} GB) vs source {W['end'] / 1e9:.3f} GB"
    )

    # ---- fo ----
    t0 = time.time()
    P = scetlib_cache.parse_fo_blob(fo_src)
    vb = np.asarray(P["var_bins"]).reshape(-1, 6)
    if not np.array_equal(vb.view(np.uint64), bins.view(np.uint64)):
        raise SystemExit("fo variation bins are not the cache bins (order)")
    if set(P["grid"]) != {bins[j].tobytes() for j in range(nb)}:
        raise SystemExit("fo grid keys are not the cache bins")
    rt = cache_io.emit_fo(P, np.arange(nb))
    if rt != fo_src:
        raise SystemExit(
            "fo emitter does not round-trip the full source blob; refusing to subset"
        )
    log(
        f"fo parsed + round-trip byte-identical ({len(fo_src)} B) in {time.time() - t0:.1f} s; "
        f"members {len(P['deltas'])} bilin nd {P['bilin'].get('nd')} poly windows {len(P['poly'])} "
        f"var_g {None if P['var_g'] is None else len(P['var_g'])}"
    )
    fo_sub = cache_io.emit_fo(P, keep)
    P2 = scetlib_cache.parse_fo_blob(fo_sub)  # parses exactly (no trailing bytes)
    log(
        f"fo subset {len(fo_sub)} B; windows emptied: {[j for j, b in P2['poly'].items() if not b]}"
    )
    del rt, P2

    bins_sub = np.ascontiguousarray(bins[keep], dtype="<f8")
    # the streamed .npy header must be exactly what write_array emits for a uint8 array
    for n in (5, 70000, payload):
        hb = io.BytesIO()
        np.lib.format.write_array_header_1_0(
            hb, {"descr": "|u1", "fortran_order": False, "shape": (n,)}
        )
        if n != payload:
            ref = io.BytesIO()
            np.lib.format.write_array(
                ref, np.zeros(n, dtype=np.uint8), allow_pickle=False
            )
            assert ref.getvalue()[: len(hb.getvalue())] == hb.getvalue(), n
    log(f"npy header for the rules member: {hb.getvalue()!r}")
    if a.dry_run:
        log("dry run: stopping before any write")
        return

    # ---- npz, member by member in source order ----
    t0 = time.time()
    tmp = out_npz + ".part"
    md5 = hashlib.md5()
    with zipfile.ZipFile(
        tmp, mode="w", compression=zipfile.ZIP_DEFLATED, allowZip64=True
    ) as zo:
        for m in names:
            k = m[: -len(".npy")]
            with zo.open(m, "w", force_zip64=True) as fid:
                if k in SMALL:
                    fid.write(raw_small[k])
                elif k == "bins":
                    np.lib.format.write_array(fid, bins_sub, allow_pickle=False)
                elif k == "fo":
                    np.lib.format.write_array(
                        fid, np.frombuffer(fo_sub, dtype=np.uint8), allow_pickle=False
                    )
                elif k == "rules":
                    # the .npy header write_array would emit for a uint8 array of this length
                    hb = io.BytesIO()
                    np.lib.format.write_array_header_1_0(
                        hb,
                        {"descr": "|u1", "fortran_order": False, "shape": (payload,)},
                    )
                    fid.write(hb.getvalue())
                    head = W["header"] + cache_io.U64.pack(len(keep))
                    fid.write(head)
                    md5.update(head)
                    done = len(head)
                    with open(src_rules, "rb") as fs:
                        for i, (s, e, _) in enumerate(rec):
                            fs.seek(s)
                            n = e - s
                            while n:
                                b = fs.read(min(n, CHUNK))
                                if not b:
                                    raise SystemExit("short read from the source rules")
                                fid.write(b)
                                md5.update(b)
                                n -= len(b)
                                done += len(b)
                            if i % 50 == 0:
                                el = time.time() - t0
                                log(
                                    f"  rules {i}/{len(rec)}  {done / 1e9:.1f}/{payload / 1e9:.1f} GB  {el:.0f} s  "
                                    f"{done / 1e6 / max(el, 1e-9):.0f} MB/s"
                                )
                    if done != payload:
                        raise SystemExit(f"wrote {done} rule bytes, expected {payload}")
                else:
                    raise SystemExit(f"unexpected member {m}")
            log(f"  wrote {m}")
    os.replace(tmp, out_npz)
    log(
        f"npz written in {time.time() - t0:.0f} s: {os.path.getsize(out_npz)} B; rules payload md5 {md5.hexdigest()}"
    )
    with open(os.path.join(a.out, "rules_payload.md5"), "w") as f:
        f.write(
            f"{md5.hexdigest()}  cache.rules.bin (as streamed into cache.npz:rules.npy)\n"
        )

    write_conf(a, keep, bins_sub)


def write_conf(a, keep, bins_sub):
    """cache.conf = the source runcard with the [Grid_Y] values line cut to the kept edges (line-based)."""
    lines = open(os.path.join(a.src, "cache.conf")).read().split("\n")
    edges = sorted(set(bins_sub[:, 2].tolist()) | set(bins_sub[:, 3].tolist()))
    i0 = lines.index("[Grid_Y]")
    iv = next(
        i
        for i in range(i0 + 1, len(lines))
        if lines[i].startswith("values = [") or lines[i].startswith("[")
    )
    if not lines[iv].startswith("values = ["):
        raise SystemExit("no values line in [Grid_Y]")
    lines[iv] = "values = [" + ", ".join(f"{e:g}" for e in edges) + "]"
    note = (
        f"# SUBSET of {a.src}: only the {keep.size} bins with |Y| <= {a.ymax} (Grid_Y cut below);\n"
        f"# built by build_subset_cache.py on {time.strftime('%Y-%m-%d')}. Everything else is the source runcard.\n"
    )
    with open(os.path.join(a.out, "cache.conf"), "w") as f:
        f.write(note + "\n".join(lines))
    shutil.copy2(
        os.path.join(a.src, "build_of_source_cache.log"),
        os.path.join(a.out, "build_of_source_cache.log"),
    )
    log(
        "Grid_Y ->", sorted(set(bins_sub[:, 2].tolist()) | set(bins_sub[:, 3].tolist()))
    )
    log("DONE")


if __name__ == "__main__":
    main()
