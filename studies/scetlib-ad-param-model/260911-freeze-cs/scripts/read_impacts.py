#!/usr/bin/env python3
"""Grouped impacts on alphaS, for whatever arms have them.

The model registers a `scetlibNPgammaNu` impact group that is EXACTLY the CS
sector (lambda2_nu, lambda4_nu, and the held lambda6_nu/lambda_inf_nu/
b0_over_bmax_nu), and a `scetlibNPFeff` group that is the TMD boundary
condition. So the plain arm's own impacts already answer "how much of
sigma(alpha_s) is the CS kernel" independently of any refit.

usage: read_impacts.py <fitresult.hdf5> [...]
"""
import os
import shutil
import sys

import numpy as np

SCRATCH = "/tmp/frzcs_read"
WIDTH_AS = 0.002

from rabbit import io_tools  # noqa: E402


def local_copy(path):
    os.makedirs(SCRATCH, exist_ok=True)
    dst = os.path.join(SCRATCH, os.path.basename(path))
    if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(path):
        shutil.copy2(path, dst)
    return dst


for path in sys.argv[1:]:
    print("=" * 78)
    print(os.path.basename(path))
    print("=" * 78)
    res = io_tools.get_fitresult(local_copy(path))
    h = res["parms"].get()
    names = [str(n) for n in h.axes[0]]
    j = names.index("alphaS")
    sig = float(np.sqrt(h.variances()[j])) * WIDTH_AS
    print(f"  sigma(alpha_s) = {sig:.6f}")
    for key in ("impacts_grouped", "impacts"):
        if key not in res:
            continue
        hi = res[key].get()
        ax0 = [str(x) for x in hi.axes[0]]
        ax1 = [str(x) for x in hi.axes[1]]
        if "alphaS" not in ax0:
            print(f"  [{key}] no alphaS row; axes0={ax0[:4]}...")
            continue
        i = ax0.index("alphaS")
        v = np.asarray(hi.values())[i]
        order = np.argsort(-np.abs(v))
        print(f"  --- {key} on alphaS (in alpha_s units), top 18 of {len(v)} ---")
        for k in order[:18]:
            print(
                f"    {ax1[k]:36s} {abs(v[k]) * WIDTH_AS:.6f}"
                f"   ({100 * abs(v[k]) * WIDTH_AS / sig:5.1f} % of sigma)"
            )
        for want in (
            "scetlibNPgammaNu",
            "scetlibNPFeff",
            "resumNonpert",
            "resumTNP",
            "pdfEig",
            "resumScale",
            "stat",
            "binByBinStat",
        ):
            if want in ax1:
                k = ax1.index(want)
                print(
                    f"  [{want:18s}] {abs(v[k]) * WIDTH_AS:.6f}"
                    f"   ({100 * abs(v[k]) * WIDTH_AS / sig:5.1f} % of sigma)"
                )
print("IMPACTS_DONE")
