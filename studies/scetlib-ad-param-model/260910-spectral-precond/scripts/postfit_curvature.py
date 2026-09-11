#!/usr/bin/env python3
"""Negative-curvature census of the POSTFIT Hessian, per arm.

rabbit does not report this on the iterative path: its Cholesky
positive-definiteness check (fitter.py:2675) lives in the --forceLinear
quadratic branch only. But the saved covariance IS H^-1 at the postfit point,
and a symmetric matrix and its inverse have eigenvalues of the same sign, so
counting negative eigenvalues of `cov` counts them in the postfit Hessian.

Reported per arm: n_negative, lambda_min, lambda_max, kappa, and whether any
variance came out negative (which is how an indefinite Hessian shows up
downstream: sqrt(var) -> NaN in every sigma).

usage: postfit_curvature.py <fitresult.hdf5> [<fitresult.hdf5> ...]
"""
import os
import shutil
import sys

import numpy as np

SCRATCH = "/tmp/spectral_precond_arms"
from rabbit import io_tools  # noqa: E402

MODEL_PREFIXES = (
    "alphaS",
    "lambda",
    "delta_lambda",
    "b0_over_bmax",
    "resumTNP_",
    "resumScale",
    "resumTransition",
    "pdfEig",
)


def local(path):
    os.makedirs(SCRATCH, exist_ok=True)
    dst = os.path.join(SCRATCH, os.path.basename(path))
    if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(path):
        shutil.copy2(path, dst)
    return dst


for path in sys.argv[1:]:
    tag = os.path.basename(path)
    res = io_tools.get_fitresult(local(path))
    if "cov" not in res:
        print(f"{tag}: no covariance saved")
        continue
    hc = res["cov"].get()
    C = np.asarray(hc.values(), dtype=np.float64)
    names = [str(n) for n in hc.axes[0]]
    hp = res["parms"].get()
    var = hp.variances()

    C = 0.5 * (C + C.T)
    w = np.linalg.eigvalsh(C)
    n_neg = int((w < 0).sum())
    n_nan = int(np.isnan(w).sum())
    n_negvar = int((var < 0).sum())
    n_nanvar = int(np.isnan(var).sum())
    kappa = abs(w).max() / abs(w).min() if abs(w).min() > 0 else np.inf

    print(f"### {tag}   ({C.shape[0]} parameters)")
    print(f"  postfit cov eigenvalues: {n_neg} negative, {n_nan} NaN")
    print(f"  lambda range [{w[0]:.4e}, {w[-1]:.4e}]   kappa(|lam|) {kappa:.3e}")
    print(f"  negative variances: {n_negvar}   NaN variances: {n_nanvar}")
    if n_neg:
        # which parameters carry the negative directions
        wv, Q = np.linalg.eigh(C)
        for k in range(min(n_neg, 5)):
            v = np.abs(Q[:, k])
            top = np.argsort(-v)[:4]
            desc = ", ".join(f"{names[i]}({v[i]:.2f})" for i in top)
            print(f"    lam={wv[k]:+.4e}  led by {desc}")
    # the 47-parameter model block, as a marginal covariance (the physically
    # meaningful object: it is what the reported sigmas come from)
    idx = [i for i, n in enumerate(names) if n.startswith(MODEL_PREFIXES)]
    B = C[np.ix_(idx, idx)]
    wb = np.linalg.eigvalsh(0.5 * (B + B.T))
    print(
        f"  model block ({len(idx)} params, marginal cov): "
        f"{int((wb < 0).sum())} negative, lambda range "
        f"[{wb[0]:.4e}, {wb[-1]:.4e}]"
    )
print("POSTFIT_CURVATURE_DONE")
