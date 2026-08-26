#!/usr/bin/env python3
"""The guard that has to stay: a CROSS-BUILD member merge must be impossible.

Members are stored as differences against the nominal rule and the frozen
fixed-order grid, and those are not reproducible between processes -- the bin
loop is a tbb::parallel_for over integrators that keep internal buffers, so two
identical builds retain different numbers of sites. Nothing downstream would
notice: the C++ loaders check the settings fingerprint, the struct sizes and the
format version, all of which two independent builds of the same runcard AGREE
on. The only thing standing between that and a silently wrong cache is
merge_shards comparing the nominal rule byte for byte.

So: take members [0,2) from one build and [2,4) from an independent build of the
SAME runcard, and require the merge to refuse. Merging each build's own halves
back together must still succeed, so the refusal is not just "this merge never
works".

    ./incontainer.sh python3 cross_build_guard.py A.npz B.npz
"""
import importlib.util
import os
import sys

import numpy as np

STUDY = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model"
spec = importlib.util.spec_from_file_location(
    "sms", os.path.join(STUDY, "split_merge_selftest.py")
)
sms = importlib.util.module_from_spec(spec)
sys.modules["sms"] = sms
spec.loader.exec_module(sms)
m = sms.m


def shard(path, lo, hi, out):
    """Write members [lo, hi) of `path` as a partial cache plus its sidecar."""
    import json

    d = np.load(path, allow_pickle=False)
    pr = m.parse_rule_blob(d["rules"].tobytes())
    pf = m.parse_fo_blob(d["fo"].tobytes())
    first = lo == 0
    rmeta = dict(pr["meta"])
    rmeta["n_eig"] = 0
    fmeta = dict(pf["meta"])
    fmeta["n_eig"] = 0
    if first:
        rmeta.update(muf_index=-1, muf_lnstep=0.0)
        fmeta.update(muf_lnstep=0.0, muf_index=-1)
    else:
        rmeta.update(as_index=-1, as_step=0.0)
        fmeta.update(as_step=0.0)
    np.savez_compressed(
        out,
        format=d["format"],
        n_eig=d["n_eig"],
        has_as=d["has_as"],
        has_muf=d["has_muf"],
        rules=np.frombuffer(sms.split_rules(pr, lo, hi, rmeta), dtype=np.uint8),
        fo=np.frombuffer(sms.split_fo(pf, lo, hi, fmeta, not first), dtype=np.uint8),
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
    return out + ".npz"


def main(pa, pb, tmp="/tmp/cross_build_guard"):
    os.makedirs(tmp, exist_ok=True)
    a0 = shard(pa, 0, 2, os.path.join(tmp, "a_lo"))
    a1 = shard(pa, 2, 4, os.path.join(tmp, "a_hi"))
    b1 = shard(pb, 2, 4, os.path.join(tmp, "b_hi"))

    # The two builds agree on everything the C++ loaders check.
    da, db = (np.load(p, allow_pickle=False) for p in (pa, pb))
    ra, rb = (m.parse_rule_blob(d["rules"].tobytes()) for d in (da, db))
    print("independent builds of the same runcard:")
    for f in ("version", "sizes", "fingerprint", "opts"):
        print(f"   {f:<12} agree: {ra[f] == rb[f]}")
    print(f"   {'anchor':<12} agree: {np.array_equal(ra['anchor'], rb['anchor'])}")
    nb = sum(
        1
        for x, y in zip(ra["rules"], rb["rules"])
        if bytes(ra["buf"][x["shared"][0] : x["shared"][1]])
        != bytes(rb["buf"][y["shared"][0] : y["shared"][1]])
    )
    print(f"   nominal rules differing byte for byte: {nb} of {len(ra['rules'])}")

    rc = 0
    print("\nA[0,2) + A[2,4) (one build) ->", end=" ")
    try:
        m.merge_shards([a0, a1], os.path.join(tmp, "same"), verbose=False)
        print("merged, as it must")
    except SystemExit as e:
        print(f"REFUSED, which is wrong: {e}")
        rc = 1

    print("A[0,2) + B[2,4) (two builds) ->", end=" ")
    try:
        m.merge_shards([a0, b1], os.path.join(tmp, "cross"), verbose=False)
        print("MERGED. The guard is GONE.")
        rc = 1
    except SystemExit as e:
        print("refused:")
        print("   " + str(e).replace("\n", "\n   "))
    print("\nguard intact" if rc == 0 else "\nGUARD BROKEN")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
