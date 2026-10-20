#!/usr/bin/env python3
"""Actual shift (new - old minimum) vs the one-step Newton prediction from the old minimum (old NP priors removed), for
every one of the 3720 parameters, in units of the new fit's sigma. Points on the diagonal = the new minimum is the old
one moved by the configuration change. BLINDED: alphaS appears only as a difference in sigma.
"""
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_output import save_plot  # noqa: E402

TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAIRS = [
    ("LAT", "LATFROZ_V3", "TMD priors removed (σ=1 on θ of λ2, λ4, δλ2)"),
    ("NOLAT", "XWSTIFF", "TMD + CS priors removed (σ=1 on θ of all 5 NP λ)"),
]
NP = ["lambda2", "lambda4", "delta_lambda2", "lambda2_nu", "lambda4_nu"]
fig, axs = plt.subplots(1, 2, figsize=(12, 5.6))
meta = {}
for ax, (new, old, what) in zip(axs, PAIRS):
    d = np.load(os.path.join(TASK, f"newton_{new}_vs_{old}.npz"))
    nm, dx, dn, sn = list(d["names"]), d["dx"], d["dx_newton"], d["sigma_new"]
    a, b = dn / sn, dx / sn
    ax.scatter(a, b, s=6, c="0.55", label="nuisances (3720 parameters)")
    for n, col in zip(NP, ["C0", "C1", "C2", "C3", "C4"]):
        i = nm.index(n)
        ax.scatter([a[i]], [b[i]], s=60, c=col, marker="D", label=n, zorder=3)
    i = nm.index("alphaS")
    ax.scatter(
        [a[i]], [b[i]], s=90, c="k", marker="*", label="alphaS (Δ only)", zorder=4
    )
    lim = 1.15 * max(np.max(np.abs(a)), np.max(np.abs(b)))
    ax.plot([-lim, lim], [-lim, lim], "k--", lw=0.8)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_xlabel(f"Newton prediction from {old}:  Δθ / σ({new})")
    ax.set_ylabel(f"actual  θ({new}) − θ({old})  / σ({new})")
    res = np.linalg.norm(b - a)
    tot = np.linalg.norm(b)
    ax.set_title(
        f"{new} vs {old}\n{what}\n‖actual − Newton‖ = {res:.1e},  ‖actual‖ = {tot:.3f}  (σ units)",
        fontsize=9,
    )
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, loc="upper left")
    meta[f"{new}_vs_{old}"] = dict(norm_residual=float(res), norm_shift=float(tot))
fig.suptitle(
    "Real data, blinded (differences only). One Newton step with the old fit's walled Hessian "
    "reproduces the new minimum",
    fontsize=10,
)
fig.tight_layout()
save_plot(outdir=TASK, basename="newton_vs_actual_shift", fig=fig, meta_info=meta)
print(meta)
