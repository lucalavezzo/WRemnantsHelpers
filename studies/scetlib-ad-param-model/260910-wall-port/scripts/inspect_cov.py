#!/usr/bin/env python3
"""NP-block covariance of the walled vs unwalled fit: sigmas, correlations with
alphaS, eigenvalues and condition number.

PROVENANCE NOTE: this was first run as /tmp/wallport_cov.py, so
logs/cov_260910_172731.log records that path rather than this one. The bytes are
identical apart from this docstring; the log is the record of what ran.
"""
import sys
import numpy as np

sys.path.insert(0, "/work/submit/lavezzo/alphaS/rabbit-blinding")
from rabbit import io_tools

NP = ["alphaS", "lambda2", "lambda4", "delta_lambda2", "lambda2_nu", "lambda4_nu"]
for tag, f in (
    (
        "unwalled",
        "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260910_blinding_final/fitresults_DATABLIND.hdf5",
    ),
    (
        "walled",
        "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260910_wall_port/fitresults_DATAWALL5.hdf5",
    ),
):
    res = io_tools.get_fitresult(f)
    print("===", tag, "keys:", sorted(res.keys()))
    if "cov" not in res:
        continue
    h = res["cov"].get()
    names = [str(n) for n in h.axes[0]]
    C = h.values()
    idx = [names.index(n) for n in NP if n in names]
    sub = C[np.ix_(idx, idx)]
    d = np.sqrt(np.diag(sub))
    print("  sigma:", {NP[i]: f"{d[i]:.6g}" for i in range(len(idx))})
    corr = sub / np.outer(d, d)
    print(
        "  corr (alphaS row):",
        {NP[i + 1]: f"{corr[0,i+1]:+.3f}" for i in range(len(idx) - 1)},
    )
    w = np.linalg.eigvalsh(sub)
    print(f"  NP-block cov eigenvalues: {np.array2string(w, precision=3)}")
    print(f"  NP-block cov condition number: {w.max()/w.min():.3g}")
    wf = np.linalg.eigvalsh(C)
    print(
        f"  FULL cov: min eig {wf.min():.4g}  max eig {wf.max():.4g}  cond {wf.max()/max(wf.min(),1e-300):.4g}"
    )
