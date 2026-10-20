#!/usr/bin/env python3
"""Check the P2 cards: C0 (rebuilt, no change) must equal the nominal card; each variant must differ from C0 only by the
intended factor on the intended nuisances (logk ratio), with the same constraint weights.
usage: python compare_cards.py <nominal.hdf5> <C0.hdf5> [<variant.hdf5> ...]"""
import sys, re
import hdf5plugin  # noqa: F401 (compressed card datasets)
import h5py, numpy as np


def load(p):
    f = h5py.File(p, "r")
    syst = [s.decode() if isinstance(s, bytes) else str(s) for s in f["hsysts"][...]]
    d = {k: f[k][...] for k in ("hnorm", "hlogk", "hdata_obs", "hconstraintweights")}
    nsys = len(syst)
    d["hlogk"] = (
        d["hlogk"].reshape(-1, nsys) if d["hlogk"].size % nsys == 0 else d["hlogk"]
    )
    return syst, d


ref_s, ref = load(sys.argv[1])
c0_s, c0 = load(sys.argv[2])
print(
    "C0 vs nominal: same systs",
    ref_s == c0_s,
    "| max|dnorm|/norm",
    float(
        np.max(
            np.abs(c0["hnorm"] - ref["hnorm"]) / np.maximum(np.abs(ref["hnorm"]), 1e-30)
        )
    ),
    "| max|dlogk|",
    float(np.max(np.abs(c0["hlogk"] - ref["hlogk"]))),
    "| data equal",
    bool(np.array_equal(c0["hdata_obs"], ref["hdata_obs"])),
    "| cw equal",
    bool(np.array_equal(c0["hconstraintweights"], ref["hconstraintweights"])),
)
for p in sys.argv[3:]:
    s, d = load(p)
    assert s == c0_s, "syst list differs"
    a, b = d["hlogk"], c0["hlogk"]
    out = []
    for j, n in enumerate(s):
        nz = np.abs(b[:, j]) > 1e-9
        if not nz.any():
            continue
        r = a[nz, j] / b[nz, j]
        if np.max(np.abs(r - 1)) > 1e-6:
            out.append((n, float(np.median(r)), float(r.min()), float(r.max())))
    print(
        p.split("/")[-2],
        "changed systs:",
        len(out),
        "| norm max rel diff",
        float(
            np.max(
                np.abs(d["hnorm"] - c0["hnorm"])
                / np.maximum(np.abs(c0["hnorm"]), 1e-30)
            )
        ),
        "| cw equal",
        bool(np.array_equal(d["hconstraintweights"], c0["hconstraintweights"])),
    )
    for o in out:
        print("    %-50s ratio median %.4f [%.4f, %.4f]" % o)
