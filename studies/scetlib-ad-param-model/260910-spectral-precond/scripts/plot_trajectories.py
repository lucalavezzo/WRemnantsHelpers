#!/usr/bin/env python3
"""Loss trajectory of the four arms, per iteration and per second.

This is the figure the whole task turns on. A preconditioner is meant to reduce
the Krylov work per outer step, so the honest way to judge it is progress
against BOTH axes: iterations (does the outer loop take fewer steps?) and wall
seconds (was the per-step saving real, or eaten by the extra Hessian-vector
products?). The `nhev` counter in the panel legend is the load-independent cost.

Bare matplotlib rather than wums.plot_tools on purpose: these are optimizer
traces over a continuous iteration index, not histograms, which is what
plot_tools' entry points take. The SAVE goes through the wums helpers
(save_pdf_and_png + write_index_and_log) exactly as scetlib_np's save_plot
wraps them, so the png/pdf/.log/index.php gallery contract is unchanged --
scetlib_np is not checked out on this branch, hence the direct call. Same route
as ../260910-wall-port/scripts/plot_np_forms.py.

usage: plot_trajectories.py <outdir>
"""
import os
import re
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from wums import output_tools, plot_tools  # noqa: E402

S = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model"
ARMS = [
    (
        "plain (no preconditioner)",
        "#000000",
        "-",
        f"{S}/260910-blinding/logs/fit_DATABLIND_260910_151034.log",
        766,
    ),
    (
        "ridge preconditioner",
        "#d62728",
        "-",
        f"{S}/260910-blinding/logs/fit_DATAPC2_260910_162332.log",
        2087,
    ),
    # nhev is None for spectral and cannot be recovered: it was stopped with
    # SIGTERM, so scipy never returned an OptimizeResult. Say so on the legend
    # rather than leaving the endpoint dot to be read as convergence.
    (
        "spectral preconditioner  [SIGTERM at 719, still descending]",
        "#1f77b4",
        "-",
        f"{S}/260910-spectral-precond/logs/fit_DATASPEC_260910_173516.log",
        None,
    ),
    (
        "walled, no preconditioner",
        "#2ca02c",
        "--",
        f"{S}/260910-wall-port/logs/fit_DATAWALL5_260910_165137.log",
        624,
    ),
]
PAT = re.compile(
    r"Iteration (\d+): loss ([-\d.eE+]+)\s+\[dt=([\d.]+)s elapsed=([\d.]+)s\]"
)
ESC = re.compile(r"\x1b\[[0-9;]*m")


def load(path):
    it, loss, el = [], [], []
    if not os.path.exists(path):
        return None
    with open(path, errors="replace") as fh:
        for line in fh:
            m = PAT.search(ESC.sub("", line))
            if m:
                it.append(int(m.group(1)))
                loss.append(float(m.group(2)))
                el.append(float(m.group(4)))
    if not it:
        return None
    return np.array(it), np.array(loss), np.array(el)


def main():
    outdir = sys.argv[1]
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.4))

    for ax, xlab in zip(axes, ("minimizer iteration", "minimize() elapsed [s]")):
        ax.set_xlabel(xlab, fontsize=13)
        ax.set_ylabel("loss (NLL)", fontsize=13)
        ax.tick_params(labelsize=11)
        ax.grid(alpha=0.25, lw=0.5)

    for label, color, ls, path, nhev in ARMS:
        d = load(path)
        if d is None:
            print(f"[skip] no trajectory in {path}")
            continue
        it, loss, el = d
        tag = label if nhev is None else f"{label}  [nhev {nhev}]"
        for ax, x in zip(axes, (it, el)):
            ax.plot(x, loss, color=color, ls=ls, lw=1.4, label=tag)
            ax.plot(x[-1:], loss[-1:], "o", color=color, ms=5)
        print(
            f"{label:28s} nit {it[-1]:4d}  final loss {loss[-1]:.4f}  "
            f"elapsed {el[-1]:.0f} s"
        )

    for ax in axes:
        # The interesting range is the endgame; the first 20 iterations fall
        # from 4750 and would flatten everything else onto the axis.
        ax.set_ylim(400, 720)
        ax.legend(fontsize=9.5, loc="upper right", framealpha=0.92)
    axes[0].set_title("progress per outer iteration", fontsize=12)
    axes[1].set_title(
        "progress per second\n(wall time is load-confounded: " "see LOGBOOK)",
        fontsize=12,
    )
    fig.suptitle(
        "Blinded data fit, same card / cache / SCETlib b66f8de / "
        "rabbit 0f64bbb — preconditioning arms",
        fontsize=11.5,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))

    meta = output_tools.make_meta_info_dict(args=None, wd=outdir)
    plot_tools.save_pdf_and_png(outdir, "loss_trajectories", fig=fig)
    output_tools.write_index_and_log(
        outdir, "loss_trajectories", analysis_meta_info=meta, args=None
    )
    print(f"wrote {outdir}/loss_trajectories.png / .pdf / .log")
    print("PLOT_TRAJECTORIES_DONE")


if __name__ == "__main__":
    main()
