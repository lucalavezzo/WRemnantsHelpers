#!/usr/bin/env python3
"""Gaussian prediction of the frozen-CS shift, from the plain arm's covariance.

If the likelihood were exactly quadratic around the plain arm's minimum, fixing a
subset f of parameters at theta_f^0 and reminimising over the rest r gives

    theta_r* = theta_r_hat + Sigma_rf Sigma_ff^-1 (theta_f^0 - theta_f_hat),
    Sigma_rr* = Sigma_rr - Sigma_rf Sigma_ff^-1 Sigma_fr,

i.e. the conditional mean and the conditional covariance of the postfit Gaussian.
So the plain arm's OWN covariance already predicts both the alpha_s shift under
the freeze and the sigma(alpha_s) it collapses to -- and comparing that to the
refit says how much of the answer is degeneracy geometry and how much is
genuine nonlinearity in SCETlib's response.

The 2 x 2 sub-block also gives the SLOPE d(alpha_s)/d(lambda2_nu) along the
frozen scan, which IS the "near-degenerate reshuffle" question in one number.

No alphaS value is printed: only shifts, sigmas and slopes.

usage: gaussian_predict.py <fitresult.hdf5> [frozen names, comma separated]
"""
import os
import shutil
import sys

import numpy as np

SCRATCH = "/tmp/frzcs_read"
WIDTH = {
    "alphaS": 0.002,
    "lambda2": 0.5,
    "lambda4": 0.5,
    "delta_lambda2": 0.5,
    "lambda2_nu": 0.1,
    "lambda4_nu": 0.5,
}
ANCHOR = {
    "alphaS": None,
    "lambda2": 0.4,
    "lambda4": 0.4,
    "delta_lambda2": 0.0,
    "lambda2_nu": 0.15,
    "lambda4_nu": 0.0,
}

from rabbit import io_tools  # noqa: E402


def local_copy(path):
    os.makedirs(SCRATCH, exist_ok=True)
    dst = os.path.join(SCRATCH, os.path.basename(path))
    if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(path):
        shutil.copy2(path, dst)
    return dst


path = sys.argv[1]
frozen = (sys.argv[2] if len(sys.argv) > 2 else "lambda2_nu,lambda4_nu").split(",")

res = io_tools.get_fitresult(local_copy(path))
hp = res["parms"].get()
names = [str(n) for n in hp.axes[0]]
theta = hp.values()
hc = res["cov"].get()
cnames = [str(x) for x in hc.axes[0]]
C = np.asarray(hc.values(), dtype=np.float64)
assert cnames == names, "parms and cov axes differ"

idx = {n: i for i, n in enumerate(names)}
f = [idx[n] for n in frozen]
r = [i for i in range(len(names)) if i not in set(f)]
ja = idx["alphaS"]
ja_r = r.index(ja)

Sff = C[np.ix_(f, f)]
Srf = C[np.ix_(r, f)]
Sff_inv = np.linalg.inv(Sff)
G = Srf @ Sff_inv  # regression coefficients, r <- f
Srr_cond = C[np.ix_(r, r)] - G @ C[np.ix_(f, r)]

print("=" * 78)
print(f"Gaussian (conditional) prediction from {os.path.basename(path)}")
print(f"frozen: {frozen}")
print("=" * 78)
print("  postfit theta of the frozen pair, and their physical values:")
for n in frozen:
    print(
        f"    {n:14s} theta = {theta[idx[n]]:+.5f}   physical = "
        f"{ANCHOR[n] + WIDTH[n] * theta[idx[n]]:+.6f}   "
        f"(anchor {ANCHOR[n]:+.4f}, sigma_theta {np.sqrt(C[idx[n], idx[n]]):.4f})"
    )
print()
print("  d(theta_alphaS) / d(theta_f)  [conditional regression coefficients]:")
for k, n in enumerate(frozen):
    g = G[ja_r, k]
    print(
        f"    d(alphaS)/d({n}) = {g:+.5f} theta/theta "
        f"= {g * WIDTH['alphaS'] / WIDTH[n]:+.6f} d(alpha_s)/d({n}) [physical]"
    )
print()
print(
    f"  sigma(alpha_s), plain        = " f"{np.sqrt(C[ja, ja]) * WIDTH['alphaS']:.6f}"
)
print(
    f"  sigma(alpha_s), CONDITIONAL  = "
    f"{np.sqrt(Srr_cond[ja_r, ja_r]) * WIDTH['alphaS']:.6f}"
    f"   (what freezing should collapse it to)"
)
print()
print("  predicted alpha_s shift when the frozen pair is moved to a target:")
print(
    f"    {'target lambda2_nu':>20s} {'theta_f':>10s} "
    f"{'d(alpha_s)':>14s} {'in sigma_plain':>16s}"
)
sig_plain = np.sqrt(C[ja, ja]) * WIDTH["alphaS"]
for lam in (0.00, 0.05, 0.087, 0.15, 0.19):
    t2 = (lam - ANCHOR["lambda2_nu"]) / WIDTH["lambda2_nu"]
    d_f = np.array([t2 - theta[idx["lambda2_nu"]], 0.0 - theta[idx["lambda4_nu"]]])
    d_as = (G @ d_f)[ja_r] * WIDTH["alphaS"]
    print(f"    {lam:20.3f} {t2:+10.3f} {d_as:+14.6f} {d_as / sig_plain:+16.3f}")
print()
print("  the same, splitting the two frozen parameters:")
for k, n in enumerate(frozen):
    d_f = np.zeros(len(frozen))
    d_f[k] = 0.0 - theta[idx[n]]
    d_as = (G @ d_f)[ja_r] * WIDTH["alphaS"]
    print(
        f"    moving only {n:14s} to its anchor: d(alpha_s) = {d_as:+.6f} "
        f"= {d_as / sig_plain:+.3f} sigma"
    )
print("GAUSSPRED_DONE")
