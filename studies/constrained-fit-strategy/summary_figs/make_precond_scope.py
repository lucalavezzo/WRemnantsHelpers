#!/usr/bin/env python3
"""Summary figure for studies/constrained-fit-strategy (SUMMARY.tex): why the FULL-scope spectral preconditioner works.

  precond_scope : for each preconditioner scope, built (as rabbit would) from the sub-fit START Hessian H_s and applied
                  to the sub-fit END Hessian H_e (SATB8's minimum, LATB8 configuration, 3759 parameters):
                  left  = plain-CG iterations (= Hessian-vector products) to reach a relative residual, on T^T H_e T
                          (a late Krylov solve; exact-arithmetic stand-in for trlib's interior solve);
                  right = condition number kappa of T^T H_e T.
                  Numbers read from 261008-saturated-subfit-diagnosis/spectra.json (key "precond"), written by that
                  task's scripts/spectra.py from the HDIAG dense Hessians. No fit, no cache: reading and plotting only.

Run in the WRemnants container (needs wums):  python3 summary_figs/make_precond_scope.py
"""
import json
import os

import wums.plot_tools as plot_tools  # noqa: F401  (import first: it sets the global style)
from wums import output_tools

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
SRC = f"{STUDY}/261008-saturated-subfit-diagnosis/spectra.json"

# key in spectra.json -> (label, colour)
SCOPES = [
    ("none", "none (raw coordinates)", "#9c9ca1"),
    ("jacobi", "Jacobi: diagonal of $H_s$ only", "#f89c20"),
    ("saturated block", "spectral, 39 bin scales only", "#964a8b"),
    ("cw==0 block (rabbit default scope)", "spectral, rabbit default scope", "#5790fc"),
    ("full", "spectral, full scope (all 3759)", "#e42536"),
]
RES = ["0.1", "0.01", "0.001", "0.0001", "1e-06"]


def save_plot(outdir, basename, fig, meta):
    os.makedirs(outdir, exist_ok=True)
    plot_tools.save_pdf_and_png(outdir, basename, fig=fig)
    output_tools.write_index_and_log(
        outdir, basename, analysis_meta_info=meta, args=None
    )


def main():
    d = json.load(open(SRC))["precond"]
    fig, ax = plt.subplots(
        1, 2, figsize=(22, 7.5), gridspec_kw=dict(width_ratios=[1.25, 1])
    )
    x = np.array([float(r) for r in RES])
    for key, lab, col in SCOPES:
        it = d[key]["cg_late_solve"]["iters"]
        y = np.array([np.nan if it[r] is None else it[r] for r in RES], dtype=float)
        lw = 4 if key == "full" else 2.5
        ax[0].plot(x, y, "-o", ms=9, lw=lw, color=col, label=lab)
    ax[0].set_xscale("log")
    ax[0].invert_xaxis()
    ax[0].set_xlabel("relative residual of the Newton solve")
    ax[0].set_ylabel("CG iterations (= Hessian-vector products)")
    ax[0].set_ylim(0, 1000)
    ax[0].legend(fontsize=16, loc="upper left", frameon=True, framealpha=1)
    ax[0].grid(alpha=0.3)

    kap = [d[k]["end_spectrum"]["kappa"] for k, _, _ in SCOPES]
    cols = [c for _, _, c in SCOPES]
    ypos = np.arange(len(SCOPES))[::-1]
    ax[1].barh(ypos, kap, color=cols, height=0.6)
    ax[1].set_xscale("log")
    ax[1].set_xlim(1e6, 1e15)
    ax[1].set_yticks(ypos)
    ax[1].set_yticklabels(["none", "Jacobi", "scales only", "rabbit default", "full"])
    ax[1].set_xlabel(r"condition number $\kappa$ of the preconditioned $H_e$")
    for yy, kk in zip(ypos, kap):
        e = int(np.floor(np.log10(kk)))
        ax[1].text(
            kk * 1.6,
            yy,
            rf"${kk / 10**e:.1f}\times10^{{{e}}}$",
            va="center",
            fontsize=17,
        )
    ax[1].grid(alpha=0.3, axis="x")
    fig.tight_layout()
    save_plot(
        HERE,
        "precond_scope",
        fig,
        dict(
            note="reading spectra.json only; preconditioners built from H_s (sub-fit start), applied to H_e (SATB8 end); plain CG on the dense matrix",
            source=SRC,
        ),
    )


if __name__ == "__main__":
    main()
