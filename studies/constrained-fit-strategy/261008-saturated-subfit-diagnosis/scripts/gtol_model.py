#!/usr/bin/env python3
"""Estimate what --minimizerGtol g would stop at under SATP's preconditioner, from HDIAG's matrices (no cache).

scipy's trust-krylov stops when ||grad_y|| < gtol, grad_y = T^T grad_theta, T = the spectral |H_s|^-1/2 that rabbit built
at the sub-fit start (lambda in [-4.38, 1.78e8], the same H_s HDIAG saved). Along the approach to x_e the local
quadratic gives, for a displacement delta from the minimum,
    dL = 1/2 delta^T H_e delta,   grad_y = T^T H_e delta,
both scaling with the size of delta (dL ~ c^2, ||grad_y|| ~ c), so each direction gives dL_stop(gtol) = r * gtol^2,
r = dL / ||grad_y||^2. Directions used:
  ray  : the actual final approach, theta part -0.1 D_theta (D = x_e - x_s), bin scales profiled quadratically
         (delta_s = -H_ss^-1 H_s,theta delta_theta). Its predicted dL is checked against HDIAG's measured 0.403 at
         that point (theta = x_s + 0.9 D, scales profiled).
  eig  : the eigenvectors of T^T H_e T (r = 1/(2 mu) for eigenvalue mu): the range r can take.
Writes gtol_model.json.
"""
import json
import os

import numpy as np

T_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = (
    "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261008_saturated_subfit_diag"
)
S = np.load(f"{OUT}/hess_start.npz", allow_pickle=True)
E = np.load(f"{OUT}/hess_end.npz", allow_pickle=True)
N = np.load(f"{OUT}/newton_start.npz")
Hs, He, D = S["H"], E["H"], N["D"]
isat = S["isat"].astype(int)
n = Hs.shape[0]
th = np.setdiff1d(np.arange(n), isat)
w, Q = np.linalg.eigh(Hs)
aw = np.maximum(np.abs(w), np.finfo(float).eps * n * np.abs(w).max())
T = Q / np.sqrt(
    aw
)  # same whitened spectrum as rabbit's Cholesky-of-|H| (differs by an orthogonal factor)
d = np.zeros(n)
d[th] = -0.1 * D[th]
d[isat] = -np.linalg.solve(He[np.ix_(isat, isat)], He[np.ix_(isat, th)] @ d[th])
dL = 0.5 * d @ He @ d
gy = T.T @ (He @ d)
r_ray = dL / (gy @ gy)
mu = np.linalg.eigvalsh(T.T @ He @ T)
res = dict(
    ray=dict(
        dL_pred=float(dL),
        dL_measured_HDIAG=0.40282789899765703,
        gy_norm=float(np.linalg.norm(gy)),
        r=float(r_ray),
    ),
    eig_r_range=[float(1 / (2 * np.abs(mu).max())), float(1 / (2 * np.abs(mu).min()))],
    eig_r_median=float(np.median(1 / (2 * np.abs(mu)))),
)
for g in [0.3, 0.1, 0.03, 0.01]:
    res[f"dL_stop_ray_gtol{g:g}"] = float(r_ray * g * g)
json.dump(res, open(f"{T_}/gtol_model.json", "w"), indent=1)
print(json.dumps(res, indent=1))
