#!/usr/bin/env python3
"""Split a real cache's members into two shards and merge them back.

If merge(split(A, [0,2)), split(A, [2,4))) reproduces A byte for byte, then the
member merge -- the header meta union, the per-rule var concatenation, the
fixed-order delta list and the muF whole-grid transplant -- is right, on real
data, without building anything.
"""

import importlib.util
import json
import os
import struct
import sys

import numpy as np

spec = importlib.util.spec_from_file_location(
    "bcp",
    "/home/submit/lavezzo/alphaS/WRemnants/scripts/rabbit/scetlib_ad/build_cache_parallel.py",
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

U64, I32, F64 = m._U64, m._I32, m._F64


def split_rules(pr, lo, hi, meta):
    out = [pr["head"]]
    out.append(
        I32.pack(meta["n_eig"])
        + I32.pack(meta["as_index"])
        + F64.pack(meta["as_cen"])
        + F64.pack(meta["as_step"])
        + I32.pack(meta["muf_index"])
        + F64.pack(meta["muf_lnstep"])
    )
    out.append(U64.pack(len(pr["rules"])))
    for r in pr["rules"]:
        out.append(bytes(pr["buf"][r["shared"][0] : r["shared"][1]]))
        out.append(U64.pack(hi - lo))
        for v0, v1 in r["var"][lo:hi]:
            out.append(bytes(pr["buf"][v0:v1]))
    return b"".join(out)


def split_fo(pf, lo, hi, meta, keep_muf):
    out = [
        m._FO_MAGIC + pf["version"],
        U64.pack(len(pf["fingerprint"])),
        pf["fingerprint"],
        m._emit_fo_grid(pf["grid"]),
    ]
    d = pf["deltas"][lo:hi]
    out.append(U64.pack(len(d)))
    out.append(
        I32.pack(meta["n_eig"])
        + F64.pack(meta["as_cen"])
        + F64.pack(meta["as_step"])
        + F64.pack(meta["as_anchor"])
        + F64.pack(meta["muf_lnstep"])
        + I32.pack(meta["muf_index"])
    )
    out.append(U64.pack(pf["var_bins"].size))
    out.append(pf["var_bins"].astype("<f8").tobytes())
    for x in d:
        out.append(U64.pack(len(x) // 8))
        out.append(x)
    for g in pf["muf"]:
        out.append(
            b"\x01" + m._emit_fo_grid(g) if (keep_muf and g is not None) else b"\x00"
        )
    return b"".join(out)


def main(path, tmp="/tmp/split_merge"):
    d = np.load(path, allow_pickle=False)
    pr = m.parse_rule_blob(d["rules"].tobytes())
    pf = m.parse_fo_blob(d["fo"].tobytes())
    n = len(pf["deltas"])
    assert n == 4, f"this test wants the 4-member layout, got {n}"
    os.makedirs(tmp, exist_ok=True)
    # [0,2) = the alphaS pair, [2,4) = the muF pair, which is how a two-way
    # --members split of this cache would have been built.
    parts = [
        (
            0,
            2,
            dict(
                as_index=pr["meta"]["as_index"],
                as_step=pr["meta"]["as_step"],
                muf_index=-1,
                muf_lnstep=0.0,
            ),
            dict(as_step=pf["meta"]["as_step"], muf_lnstep=0.0, muf_index=-1),
            False,
        ),
        (
            2,
            4,
            dict(
                as_index=-1,
                as_step=0.0,
                muf_index=pr["meta"]["muf_index"],
                muf_lnstep=pr["meta"]["muf_lnstep"],
            ),
            dict(
                as_step=0.0,
                muf_lnstep=pf["meta"]["muf_lnstep"],
                muf_index=pf["meta"]["muf_index"],
            ),
            True,
        ),
    ]
    paths = []
    for lo, hi, rm, fm, keep in parts:
        rmeta = dict(pr["meta"])
        rmeta.update(rm)
        rmeta["n_eig"] = 0
        fmeta = dict(pf["meta"])
        fmeta.update(fm)
        fmeta["n_eig"] = 0
        out = os.path.join(tmp, f"m{lo}{hi}")
        np.savez_compressed(
            out,
            format=d["format"],
            n_eig=d["n_eig"],
            has_as=d["has_as"],
            has_muf=d["has_muf"],
            rules=np.frombuffer(split_rules(pr, lo, hi, rmeta), dtype=np.uint8),
            fo=np.frombuffer(split_fo(pf, lo, hi, fmeta, keep), dtype=np.uint8),
            bins=d["bins"],
            anchor=d["anchor"],
            names=d["names"],
        )
        with open(out + ".shard.json", "w") as f:
            json.dump(
                dict(
                    lo=lo,
                    hi=hi,
                    n_members=4,
                    n_eig=0,
                    has_as=True,
                    has_muf=True,
                    pairs=[[0, 2, "alphaS"], [2, 4, "muF"]],
                    sets=["a", "b", "c", "d"],
                    pdf_members=[0, 0, 0, 0],
                    as_cen=pr["meta"]["as_cen"],
                    as_step=pr["meta"]["as_step"],
                ),
                f,
            )
        paths.append(out + ".npz")
    merged = m.merge_shards(paths, os.path.join(tmp, "merged"))
    e = np.load(merged, allow_pickle=False)
    ok = True
    for k in d.files:
        same = np.array_equal(d[k], e[k])
        ok &= bool(same)
        print(f"  {k:8s} {'same' if same else 'DIFFER'}")
    print("split -> merge reproduces the original cache byte for byte:", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
