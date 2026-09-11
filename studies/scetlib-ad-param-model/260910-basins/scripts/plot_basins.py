#!/usr/bin/env python3
"""Two figures for the basin question.

FIG 1 `warm_restart_shifts` -- experiment 1.  For each arm, how far the warm
restart moved from its own seed, in units of that seed's postfit sigma.  Left:
the whole distribution over all ~3720 parameters, so a single bad direction
cannot hide in a mean.  Right: the directions that carry the physics -- alphaS,
the five NP lambdas, the profile scales -- as signed shifts.

FIG 2 `basin_map` -- experiment 2.  Left: the L2 distance matrix between every
pair of arms over the 46 non-alphaS model parameters (alphaS EXCLUDED so nothing
unblinds), which is the operational definition of "same basin" used throughout
this study.  Right: the physical NP tune of each arm, which is what a basin
means physically.

Bare matplotlib, not wums.plot_tools: none of this is a histogram, and
plot_tools' entry points (makePlotWithRatioToRef and friends) take hists.  The
SAVE goes through the wums helpers that scetlib_np's save_plot wraps
(save_pdf_and_png + write_index_and_log), so the png/pdf/.log/index.php gallery
contract is identical; the scetlib_np package is not checked out on this branch,
hence the direct call -- same as ../260910-wall-port/scripts/plot_np_forms.py.

POLICY: alphaS's central value is never drawn or printed.  Shifts in units of
sigma, and sigma itself, are safe under additive blinding.

usage: plot_basins.py <outdir> <arms.json>
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

outdir, spec_path = sys.argv[1], sys.argv[2]
spec = json.load(open(spec_path))

COL = {
    "plain": "#1f77b4",
    "ridge": "#d62728",
    "spectral": "#9467bd",
    "walled": "#2ca02c",
    "wall+ridge": "#ff7f0e",
}
PHYS = [
    "alphaS",
    "lambda2",
    "lambda4",
    "delta_lambda2",
    "lambda2_nu",
    "lambda4_nu",
    "resumScaleMuR",
    "resumScaleMuF",
    "resumTransition2",
]


# ----------------------------------------------------------------- FIG 1
warm = spec.get("warm", {})
if warm:
    arms = [a for a in ("plain", "ridge", "spectral", "walled") if a in warm]
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(12.4, 4.8))

    FLOOR = 1e-13  # below this a shift is exactly zero (the walled arm) -- drawn
    # on the axis floor and called out in the text, never dropped
    rs = np.random.RandomState(7)
    for i, a in enumerate(arms):
        w = warm[a]
        pull = np.abs(
            np.array([x for x in w["pull_all"] if x is not None], dtype=float)
        )
        y = len(arms) - 1 - i
        x = np.clip(pull, FLOOR, None)
        axL.scatter(
            x,
            y + (rs.rand(len(x)) - 0.5) * 0.34,
            s=3,
            alpha=0.22,
            color=COL[a],
            edgecolors="none",
            zorder=2,
        )
        axL.plot(
            [max(np.median(pull), FLOOR)],
            [y],
            marker="|",
            ms=16,
            mew=2.2,
            color=COL[a],
            zorder=4,
        )
        axL.plot(
            [max(pull.max(), FLOOR)],
            [y],
            marker="D",
            ms=6,
            color="k",
            mfc="none",
            mew=1.4,
            zorder=5,
        )
        axL.plot(
            [max(abs(w["alphaS"]["shift_in_sigma"]), FLOOR)],
            [y],
            marker="*",
            ms=17,
            color="k",
            mfc="gold",
            mew=1.0,
            zorder=6,
        )
        tag = f"{a}   max {pull.max():.1e}" + (
            "  (exactly 0)" if pull.max() == 0 else ""
        )
        axL.text(1.3 * FLOOR, y + 0.26, tag, fontsize=8.5, color=COL[a], va="bottom")
    axL.axvline(0.1, color="0.6", lw=0.9, ls=":")
    axL.axvline(1.0, color="0.35", lw=1.1, ls="--")
    axL.text(1.02, -0.52, "1$\\sigma$", fontsize=8, color="0.35")
    axL.text(0.105, -0.52, "0.1$\\sigma$", fontsize=8, color="0.6")
    axL.set_xscale("log")
    axL.set_xlim(FLOOR, 4)
    axL.set_ylim(-0.62, len(arms) - 0.1)
    axL.set_yticks([])
    axL.set_xlabel(r"$|\Delta x| \,/\, \sigma_{\rm postfit}$")
    axL.set_title("every one of the 3720 parameters", fontsize=10)
    axL.legend(
        handles=[
            Line2D(
                [],
                [],
                marker="*",
                ls="",
                ms=13,
                mfc="gold",
                color="k",
                label=r"$\alpha_s$",
            ),
            Line2D(
                [],
                [],
                marker="D",
                ls="",
                ms=6,
                mfc="none",
                color="k",
                label="largest anywhere",
            ),
            Line2D(
                [], [], marker="|", ls="", ms=12, mew=2, color="0.4", label="median"
            ),
        ],
        fontsize=8,
        loc="lower right",
        framealpha=0.92,
    )

    names = [p for p in PHYS if p in warm[arms[0]]["pull_named"]]
    w_bar = 0.8 / len(arms)
    for i, a in enumerate(arms):
        v = [max(abs(warm[a]["pull_named"][n]), FLOOR) for n in names]
        axR.bar(
            np.arange(len(names)) + (i - (len(arms) - 1) / 2) * w_bar,
            v,
            width=w_bar * 0.92,
            color=COL[a],
            label=a,
            bottom=FLOOR,
        )
    axR.set_yscale("log")
    axR.set_ylim(FLOOR, 4)
    axR.axhline(1.0, color="0.35", lw=1.1, ls="--")
    axR.axhline(0.1, color="0.6", lw=0.9, ls=":")
    axR.text(len(names) - 0.55, 1.15, "1$\\sigma$", fontsize=8, color="0.35")
    axR.text(len(names) - 0.55, 0.115, "0.1$\\sigma$", fontsize=8, color="0.6")
    axR.set_xticks(np.arange(len(names)))
    axR.set_xticklabels(names, rotation=40, ha="right", fontsize=8)
    axR.set_ylabel(r"$|\Delta x| \,/\, \sigma_{\rm postfit}$")
    axR.set_title(
        r"the directions that carry the physics" "\n(walled: identically zero, no bar)",
        fontsize=10,
    )
    axR.legend(fontsize=8, loc="lower right", ncol=2, framealpha=0.95)
    fig.suptitle(
        "Warm restart from each arm's own postfit -- nothing moves. "
        "Blinded data; no $\\alpha_s$ value shown.",
        fontsize=11,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    plot_tools.save_pdf_and_png(outdir, "warm_restart_shifts", fig=fig)
    output_tools.write_index_and_log(
        outdir,
        "warm_restart_shifts",
        analysis_meta_info={
            "spec": spec_path,
            "seeds": spec.get("seeds"),
            "policy": "alphaS central value never drawn",
        },
        args=None,
    )
    print(f"wrote {outdir}/warm_restart_shifts.png")

# ----------------------------------------------------------------- FIG 2
bas = spec.get("basin", {})
if bas:
    tags = bas["tags"]
    fig2, axes = plt.subplots(2, 2, figsize=(11.6, 9.2))
    axes = axes.ravel()
    mats = [
        ("all 46 model parameters", np.array(bas["L2"], dtype=float)),
        (
            f"NP block only ({len(bas['np_keys'])} $\\lambda$)",
            np.array(bas["L2_np"], dtype=float),
        ),
        (
            f"everything else ({bas['n_rest']}: scales / TNP / PDF)",
            np.array(bas["L2_rest"], dtype=float),
        ),
    ]
    for ax1, (ttl, D) in zip(axes[:3], mats):
        im = ax1.imshow(D, cmap="viridis_r", vmin=0.0)
        ax1.set_xticks(range(len(tags)))
        ax1.set_xticklabels(tags, rotation=28, ha="right", fontsize=8.5)
        ax1.set_yticks(range(len(tags)))
        ax1.set_yticklabels(tags, fontsize=8.5)
        for i in range(len(tags)):
            for j in range(len(tags)):
                ax1.text(
                    j,
                    i,
                    f"{D[i, j]:.2f}",
                    ha="center",
                    va="center",
                    fontsize=8.5,
                    fontweight="bold",
                    color="w" if D[i, j] > 0.55 * D.max() else "0.05",
                )
        ax1.set_title(r"$L_2$, " + ttl, fontsize=10)
        fig2.colorbar(im, ax=ax1, fraction=0.046)

    # Only the FITTED lambdas. lambda_inf (1.0) and lambda_inf_nu (2.0) are held
    # at the correction's anchor in every arm, so plotting them would only set a
    # scale that hides the five parameters that actually differ.
    ax2 = axes[3]
    held = {"lambda_inf", "lambda_inf_nu"}
    lams = [n for n in bas["lambda_names"] if n not in held]
    w_bar = 0.8 / len(tags)
    for i, t in enumerate(tags):
        ax2.bar(
            np.arange(len(lams)) + (i - (len(tags) - 1) / 2) * w_bar,
            [bas["phys"][t][n] for n in lams],
            width=w_bar * 0.92,
            color=COL.get(t, "0.5"),
            label=t,
        )
    ax2.plot(
        np.arange(len(lams)),
        [bas["anchors"][n] for n in lams],
        "k_",
        ms=26,
        mew=2.2,
        label="anchor (correction)",
    )
    ax2.axhline(0.0, color="0.4", lw=0.9)
    ax2.set_xticks(np.arange(len(lams)))
    ax2.set_xticklabels(
        [
            r"$\lambda_2$",
            r"$\lambda_4$",
            r"$\delta\lambda_2$",
            r"$\lambda_2^\nu$",
            r"$\lambda_4^\nu$",
        ][: len(lams)],
        fontsize=11,
    )
    ax2.set_ylabel("physical value")
    ax2.set_title(
        "the NP tune each arm landed on\n"
        "(held: $\\lambda_\\infty=1$, $\\lambda_\\infty^\\nu=2$ in all five)",
        fontsize=10,
    )
    ax2.legend(fontsize=8, ncol=2)
    fig2.suptitle(
        "Where the five arms sit -- same card / cache / SCETlib b66f8de / "
        "rabbit 0f64bbb, blinded data,\nNP sector free; "
        r"$\alpha_s$ excluded from every distance so nothing unblinds",
        fontsize=11,
    )
    fig2.tight_layout(rect=(0, 0, 1, 0.93))
    plot_tools.save_pdf_and_png(outdir, "basin_map", fig=fig2)
    output_tools.write_index_and_log(
        outdir,
        "basin_map",
        analysis_meta_info={
            "spec": spec_path,
            "fitresults": bas.get("fits"),
            "policy": "alphaS excluded from the L2 so nothing unblinds",
        },
        args=None,
    )
    print(f"wrote {outdir}/basin_map.png")
print("PLOT_BASINS_DONE")
