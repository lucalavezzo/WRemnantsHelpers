#!/usr/bin/env python3
"""Figures for the frozen-CS question.

FIG 1 `frozen_cs_scan` -- the answer, and the candidate systematic. Against the
frozen CS lambda2_nu: (a) the alpha_s shift relative to the plain (CS-free) arm
in units of sigma(alpha_s)_plain; (b) the cost in the saturated 2*dNLL; (c)
sigma(alpha_s) itself. Two series: the COLD scan (cold start, free to change
basin) and the WARM scan (started from the plain arm's own postfit with only the
CS pair moved, so the basin is controlled). The lattice band of AN-25-085 eq.
nplunc, the theory correction's own anchor, and the plain arm's own free-fit
lambda2_nu are marked, because the answer is only readable against them.

FIG 2 `frozen_cs_basin` -- where each frozen fit landed: L2 over the 46
non-alphaS model parameters against the reference arms of ../260910-basins and
../260911-lattice-constraints, split into the NP block and the rest.

Bare matplotlib, not wums.plot_tools: none of this is a histogram, and
plot_tools' entry points take hists. The SAVE goes through the same wums
helpers scetlib_np's save_plot wraps (save_pdf_and_png + write_index_and_log),
so the png/pdf/.log/index.php gallery contract is identical; scetlib_np is not
checked out on this branch, hence the direct call -- as in
../260910-basins/scripts/plot_basins.py.

POLICY: alphaS's central value is never drawn or printed. Differences in units
of sigma, and sigma itself, are safe under additive blinding.

usage: plot_frzcs.py <outdir> <frzcs.json>
"""
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from wums import output_tools, plot_tools  # noqa: E402

outdir = os.path.abspath(sys.argv[1])
spec_path = os.path.abspath(sys.argv[2])
spec = json.load(open(spec_path))
arms = spec["arms"]

# The frozen lambda2_nu each scan arm was pinned at (physical GeV^2).
FRZ = {
    "frzCS@0.00": 0.00,
    "frzCS@0.05": 0.05,
    "frzCS@0.087": 0.087,
    "frzCS@0.15": 0.15,
    "frzCS@0.19": 0.19,
}
WFRZ = {
    "wfrz@0.00": 0.00,
    "wfrz@0.05": 0.05,
    "wfrz@0.087": 0.087,
    "wfrz@0.15": 0.15,
    "wfrz@0.19": 0.19,
}
# the continuation arms replay the three lower COLD points (they are the same
# fits) and add 0.15 / 0.19 stepped from frzCS@0.087, so the series is drawn as
# {cold 0.00, 0.05, 0.087} + {cont 0.15, 0.19}.
CONT = {
    "frzCS@0.00": 0.00,
    "frzCS@0.05": 0.05,
    "frzCS@0.087": 0.087,
    "cfrz@0.15": 0.15,
    "cfrz@0.19": 0.19,
}
LAT_MU, LAT_SIG = 0.0870, 0.0332  # AN-25-085 eq. nplunc (Cridge et al.)
ANCHOR = 0.15  # the theory correction's own value

# The "warm from the plain postfit" arms are deliberately NOT drawn: setting
# lambda4_nu (postfit sigma(theta) = 0.024) to 0 while holding the rest of the
# plain postfit starts at a loss of 1e3-2e6, i.e. farther from any minimum than
# a cold start, and those arms stall in worse minima than both series below.
# They are recorded in the logbook as a failed seeding strategy, not as points.
SERIES = [
    ("cold start (free to change branch)", FRZ, "--", 1.6, 0.60, "tab:blue", 11),
    (
        "single branch: cold 0.00/0.05/0.087 + continuation 0.15/0.19",
        CONT,
        "-",
        2.4,
        1.0,
        "tab:orange",
        -16,
    ),
]
live = [
    (
        lab,
        sorted(((m[t], arms[t]) for t in arms if t in m), key=lambda z: z[0]),
        ls,
        lw,
        al,
        c,
        dy,
    )
    for lab, m, ls, lw, al, c, dy in SERIES
]
live = [s for s in live if s[1]]
if not live:
    print("no frozen arms yet; nothing to plot")
    sys.exit(0)
plain = arms.get("plain")

fig, axes = plt.subplots(3, 1, figsize=(9.6, 12.4), sharex=True)


def context(ax):
    ax.axvspan(
        LAT_MU - LAT_SIG, LAT_MU + LAT_SIG, color="tab:green", alpha=0.13, zorder=0
    )
    ax.axvline(LAT_MU, color="tab:green", lw=1.3, zorder=1)
    ax.axvline(ANCHOR, color="tab:purple", ls="--", lw=1.5, zorder=1)
    if plain is not None:
        ax.axvline(
            plain["phys"]["lambda2_nu"], color="tab:red", ls=":", lw=1.7, zorder=1
        )
    ax.tick_params(labelsize=11)


def draw(ax, key, marker, scale=1.0, annot=None):
    for lab, pts, ls, lw, al, colour, dy in live:
        xs = np.array([p[0] for p in pts])
        ys = np.array([p[1].get(key, np.nan) for p in pts], dtype=float) * scale
        ax.plot(xs, ys, marker + ls, color=colour, ms=8, lw=lw, alpha=al, zorder=3)
        if annot:
            for xi, yi in zip(xs, ys):
                # The two series SHARE the 0.00 / 0.05 / 0.087 fits, so label
                # those once (on the continuation series) rather than twice.
                if colour == "tab:blue" and xi < 0.12:
                    continue
                if np.isfinite(yi):
                    ax.annotate(
                        format(yi, annot),
                        (xi, yi),
                        fontsize=9.5,
                        textcoords="offset points",
                        xytext=(0, dy),
                        ha="center",
                        color=colour,
                        zorder=4,
                    )


# ---- (a) the answer
ax = axes[0]
context(ax)
ax.axhspan(-1, 1, color="0.88", zorder=0)
ax.axhline(0.0, color="k", lw=1.0, zorder=2)
draw(ax, "d_over_sigma_plain", "o", annot="+.2f")
ax.set_ylabel(r"$\Delta\alpha_s\,/\,\sigma(\alpha_s)_{\rm plain}$", fontsize=13)
ax.set_title(
    "Freezing the CS kernel: how far does $\\alpha_s$ move?\n"
    "shift relative to the CS-free 'plain' arm; grey band $=\\pm1\\sigma$",
    fontsize=12,
)

# ---- (b) the cost
ax = axes[1]
context(ax)
if plain is not None and plain.get("sat_2dnll"):
    ax.axhline(plain["sat_2dnll"], color="tab:red", ls=":", lw=1.7)
    ax.annotate(
        "plain (CS free), 811.1",
        (0.005, plain["sat_2dnll"]),
        textcoords="offset points",
        xytext=(0, 5),
        fontsize=9.5,
        color="tab:red",
    )
draw(ax, "sat_2dnll", "s")
ax.set_ylabel(r"saturated $2\Delta\mathrm{NLL}$  (733 d.o.f.)", fontsize=13)
ax.set_title("the cost of freezing, in the statistic that ranks arms", fontsize=11)

# ---- (c) the uncertainty
ax = axes[2]
context(ax)
if plain is not None:
    ax.axhline(plain["sigma_alphas"], color="tab:red", ls=":", lw=1.7)
    ax.annotate(
        "plain, 0.001321",
        (0.005, plain["sigma_alphas"]),
        textcoords="offset points",
        xytext=(0, -14),
        fontsize=9.5,
        color="tab:red",
    )
draw(ax, "sigma_alphas", "^")
ax.set_ylabel(r"$\sigma(\alpha_s)$", fontsize=13)
ax.set_xlabel(
    r"frozen CS $\lambda_2^\nu$   [GeV$^2$]   "
    r"($\lambda_4^\nu$ frozen at 0 throughout)",
    fontsize=13,
)
ax.set_title("and what it does to the uncertainty", fontsize=11)

handles = [
    Line2D(
        [],
        [],
        color="tab:green",
        lw=7,
        alpha=0.35,
        label=r"lattice $\lambda_2 = 0.087\pm0.033$ (AN-25-085 eq. nplunc)",
    ),
    Line2D(
        [],
        [],
        color="tab:purple",
        ls="--",
        lw=1.5,
        label=r"theory correction anchor, $\lambda_2^\nu=0.15$",
    ),
    Line2D(
        [],
        [],
        color="tab:red",
        ls=":",
        lw=1.7,
        label=r"plain arm's own free-fit $\lambda_2^\nu=-0.058$",
    ),
] + [
    Line2D([], [], color=c, ls=ls, marker="o", lw=lw, alpha=al, label=lab)
    for lab, _, ls, lw, al, c, _ in live
]
axes[0].legend(handles=handles, fontsize=9.5, loc="lower left", framealpha=0.95)
fig.suptitle(
    "Blinded data. No $\\alpha_s$ value shown -- differences only.",
    fontsize=10.5,
    y=0.997,
)
fig.tight_layout(rect=(0, 0, 1, 0.978))
plot_tools.save_pdf_and_png(outdir, "frozen_cs_scan", fig=fig)
output_tools.write_index_and_log(
    outdir,
    "frozen_cs_scan",
    analysis_meta_info={
        "spec": spec_path,
        "policy": "alphaS central value never drawn",
    },
    args=None,
)
print(f"wrote {outdir}/frozen_cs_scan.png")

# ------------------------------------------------------------------ FIG 2
# The five `wfrz` arms are deliberately left out of this map: they are a failed
# seeding strategy (see the logbook), they all stall in worse minima, and at 19
# rows the cells stop being readable. Their distances are in
# logs/analyse_*.log if wanted -- in particular wfrz@0.19 sits 0.001 from
# frzCS@0.19, which is the point they are quoted for.
tags = (
    [
        t
        for t in ("plain", "ridge", "spectral", "walled", "wall+ridge", "lattice")
        if t in arms
    ]
    + [t for t in FRZ if t in arms]
    + [t for t in ("cfrz@0.15", "cfrz@0.19", "bfrz@0.087") if t in arms]
)
if len(tags) > 1:
    keys = spec["keys"]
    npk = spec["npkeys"]
    rest = [k for k in keys if k not in npk]
    fig2, axes2 = plt.subplots(1, 3, figsize=(19.5, 6.6))
    for ax, (label, kk) in zip(
        axes2,
        (
            (f"all {len(keys)} model params", keys),
            (f"NP block ({len(npk)})", npk),
            (f"scales / TNPs / PDF ({len(rest)})", rest),
        ),
    ):
        M = np.array(
            [
                [
                    np.linalg.norm(
                        [arms[a]["theta"][k] - arms[b]["theta"][k] for k in kk]
                    )
                    for b in tags
                ]
                for a in tags
            ]
        )
        im = ax.imshow(M, cmap="viridis")
        ax.set_xticks(range(len(tags)))
        ax.set_xticklabels(tags, rotation=55, ha="right", fontsize=8)
        ax.set_yticks(range(len(tags)))
        ax.set_yticklabels(tags, fontsize=8)
        for i in range(len(tags)):
            for j in range(len(tags)):
                ax.text(
                    j,
                    i,
                    f"{M[i, j]:.2f}",
                    ha="center",
                    va="center",
                    fontsize=6.5,
                    color="w" if M[i, j] < 0.6 * M.max() else "k",
                )
        ax.set_title(f"L2, {label}", fontsize=11)
        fig2.colorbar(im, ax=ax, fraction=0.046)
    fig2.suptitle(
        "Which basin does each frozen-CS fit land in?  "
        "L2 over model parameters in theta units ($\\alpha_s$ excluded)",
        fontsize=12,
    )
    fig2.tight_layout(rect=(0, 0, 1, 0.945))
    plot_tools.save_pdf_and_png(outdir, "frozen_cs_basin", fig=fig2)
    output_tools.write_index_and_log(
        outdir,
        "frozen_cs_basin",
        analysis_meta_info={
            "spec": spec_path,
            "policy": "alphaS excluded from every distance",
        },
        args=None,
    )
    print(f"wrote {outdir}/frozen_cs_basin.png")
print("PLOT_DONE")
