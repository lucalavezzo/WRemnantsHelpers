"""Validate the compact forward-mode Jacobian against finite differences on the
REAL SCETlib NP fold (not the toy). Confirms _ratio_compact_jac is correct for
the actual param model; combined with the toy (which proved the straight-through
math is exact given correct J/K), this validates the real straight-through path.

Run (isolated checkout, in the container, cwd = checkout so imports resolve there):
  cd $DEST && source ./setup.sh && python3 hessian_dev/validate_real_jac.py
"""

import os
import numpy as np
import tensorflow as tf

FIT = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260528_debug_SCETlibPOIModel/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_excludeSCETlibNP/ZMassDilepton.hdf5"
UNFOLD = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260411_histmaker_dilepton_unfolding/mz_dilepton.hdf5"
BT = "/ceph/submit/data/user/l/lavezzo/zstuff/Z_COM13_CT18Z_N3p0LL_btgrid_fineall/"
FREEZE = ["lambda_inf", "lambda6", "lambda_inf_nu", "lambda4_nu", "^scetlibNP.*"]

from rabbit import inputdata
from wremnants.postprocessing.scetlib_np.param_model import SCETlibNPParamModel

print(">>> constructing param model (loads btgrid + R + nonsingular) ...", flush=True)
indata = inputdata.FitInputData(FIT)
pm = SCETlibNPParamModel(indata, UNFOLD, BT, freezeParameters=FREEZE)
order = list(pm._param_order)
param = tf.constant(pm.xparamdefault.numpy(), dtype=indata.dtype)
print(">>> param order:", order, flush=True)
print(">>> param (λ):", np.round(param.numpy(), 4), flush=True)

r0 = pm._ratio_from_param(param).numpy()
print(
    f">>> ratio at λ_central: shape={r0.shape}, range=[{r0.min():.6f}, {r0.max():.6f}] (expect ~1)",
    flush=True,
)

print(">>> computing compact forward-mode J (8 JVPs) ...", flush=True)
J = pm._ratio_compact_jac(param).numpy()  # [N_reco, nparam]

eps = 1e-6
pv = param.numpy()
print(">>> J vs central finite-difference (per floating param):", flush=True)
worst = 0.0
for name in ("lambda2", "lambda4", "lambda2_nu", "delta_lambda2"):
    i = order.index(name)
    e = np.zeros_like(pv)
    e[i] = eps
    rp = pm._ratio_from_param(tf.constant(pv + e, dtype=indata.dtype)).numpy()
    rm = pm._ratio_from_param(tf.constant(pv - e, dtype=indata.dtype)).numpy()
    Jfd = (rp - rm) / (2 * eps)
    absd = np.max(np.abs(J[:, i] - Jfd))
    scale = np.max(np.abs(Jfd)) + 1e-30
    print(
        f"    {name:14s} max|J_fwd - J_fd| = {absd:.3e}   rel = {absd/scale:.3e}   (|dratio/dλ|max={scale:.3e})",
        flush=True,
    )
    worst = max(worst, absd / scale)

print()
print(
    "RESULT:",
    (
        "PASS — real compact J matches finite-diff"
        if worst < 1e-5
        else f"CHECK (worst rel {worst:.2e})"
    ),
    flush=True,
)
