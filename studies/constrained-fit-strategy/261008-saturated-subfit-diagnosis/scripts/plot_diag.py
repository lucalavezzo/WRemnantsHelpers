#!/usr/bin/env python3
"""Figures from HDIAG (hess_diag.json + ceph spectra_eigs.npz written by spectra.py). No cache.

  hessian_spectra : sorted |eigenvalues| of the sub-fit Hessian at its start (H_s) and end (H_e), and of H_e in the
                    coordinates each candidate preconditioner (built from H_s, as rabbit would at the sub-fit start)
                    defines; dashed: the Schur complement with the 39 bin scales profiled out (variable projection).
  valley_line     : loss - final along the straight line x_s -> x_e, raw and with the scales profiled at each point.
Bare matplotlib (eigenvalue / line traces, not histograms), saved through save_plot.
"""
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_output import save_plot  # noqa: E402

T = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = (
    "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261008_saturated_subfit_diag"
)
R = json.load(open(f"{T}/hess_diag.json"))
META = dict(
    note="HDIAG: dense Hessians of the SATB8 saturated sub-fit (LATB8 card/model, tau 8 relu2 wall, lattice term); "
    "loss differences only, alphaS blinded"
)


def spectra():
    E = np.load(f"{OUT}/spectra_eigs.npz")
    plt.rcdefaults()
    fig, ax = plt.subplots(figsize=(9, 5.2))
    sty = {
        "H_s": ("k", "-", "H at the sub-fit start (raw)"),
        "H_e": ("#1f77b4", "-", "H at the sub-fit end (raw)"),
        "pc_jacobi": ("#ff7f0e", "-", "end, Jacobi-scaled (diag of H_s)"),
        "pc_saturated block": ("#9467bd", "-", "end, 39 bin-scale block whitened"),
        "pc_cw==0 block (rabbit default scope)": (
            "#8c564b",
            "-",
            "end, unconstrained block whitened (rabbit default)",
        ),
        "pc_full": ("#2ca02c", "-", "end, fully whitened by H_s (spectral)"),
        "varpro_schur": (
            "#d62728",
            "--",
            "end, bin scales profiled out (Schur complement, raw)",
        ),
    }
    for k, (c, ls, lab) in sty.items():
        if k not in E.files:
            continue
        a = np.sort(np.abs(E[k]))[::-1]
        kap = a.max() / a.min()
        ax.semilogy(
            np.arange(len(a)),
            a,
            ls,
            color=c,
            lw=1.3,
            label=f"{lab}: $\\kappa$ = {kap:.2g}",
        )
    ax.set_xlabel("eigenvalue index (sorted)")
    ax.set_ylabel("|eigenvalue|")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7.5, loc="upper right")
    ax.set_title(
        "projected-ptll saturated sub-fit Hessian (3759 params): conditioning",
        fontsize=10,
    )
    fig.tight_layout()
    save_plot(T, "hessian_spectra", fig=fig, meta_info=META)


def line():
    plt.rcdefaults()
    fig, ax = plt.subplots(figsize=(8, 4.8))
    Le = R["L_e"]
    tr = sorted((float(k), v) for k, v in R["line_raw"].items())
    tp = sorted((float(k), v) for k, v in R["line_prof"].items())
    t0 = [0.0] + [t for t, _ in tr] + [1.0]
    v0 = [R["L_s"]] + [v for _, v in tr] + [Le]
    ax.plot(
        t0,
        np.array(v0) - Le,
        "o-",
        color="#1f77b4",
        label="raw straight line x_s $\\to$ x_e",
    )
    ax.plot(
        [t for t, _ in tp],
        np.array([v for _, v in tp]) - Le,
        "s-",
        color="#d62728",
        label="same $\\theta$, 39 bin scales profiled analytically",
    )
    ax.set_xlabel("t  (x = x_s + t (x_e $-$ x_s))")
    ax.set_ylabel("loss $-$ loss(x_e)  [NLL]")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    ax.set_title(
        "the sub-fit valley along the straight line from its start to its minimum",
        fontsize=10,
    )
    fig.tight_layout()
    save_plot(T, "valley_line", fig=fig, meta_info=META)


if __name__ == "__main__":
    line()
    spectra()
