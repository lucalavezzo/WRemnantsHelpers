#!/usr/bin/env python3
"""Postfit ptll and yll projections: the one fit with an acceptable ptll projected-saturated p (CCKRYLOVWARM,
unwalled, lambda2_nu < 0) against the fits with bad p. Each fit's postfit comes from a --noFit re-evaluation at
its own converged point (scripts/run_eval.sh), which saves both projections.

Top row: postfit / data - 1 (%). Bottom row: stat pull (data - postfit)/sqrt(data), with sum of pull^2 in the legend.
usage: plot_postfit_good_vs_bad.py   (inside the container, after setup.sh)
"""
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from wums import plot_tools  # noqa: E402

from rabbit import io_tools  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(TASK, "..", "260923-lattice-fits", "scripts"))
from plot_output import save_plot  # noqa: E402

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260925_postfit_eval"
# tag, label (with the ptll projected-saturated q/39 of the ORIGINAL fit), colour, linestyle
FITS = [
    ("CCKRYLOVWARM", "unwalled, $\\lambda_2^\\nu<0$ (q=56)", "#d62728", "-"),
    ("CCCOLDSELF", "unwalled 2nd min. (q=89)", "#ff9896", "--"),
    ("CCWALLWARMPF", "walled (q=70)", "#1f77b4", "-"),
    ("CCWALLCOLDR", "walled cold (q=72)", "#aec7e8", "--"),
    ("LATL4ZWALLCOLD", "lattice walled (q=81)", "#2ca02c", "-"),
    ("LATL4ZUNWWARM", "lattice unwalled (q=79)", "#98df8a", "--"),
]


def load(tag, proj):
    r = io_tools.get_fitresult(f"{A}/{tag}/fitresults_{tag}.hdf5")
    ch = r["mappings"][f"Project ch0 {proj}"]["channels"]["ch0"]
    d = ch["hist_data_obs"].get()
    p = ch["hist_postfit_inclusive"].get()
    return d.axes[0].edges, d.values(), p.values()


def main():
    fig, axes = plt.subplots(
        2, 2, figsize=(14, 8), sharex="col", gridspec_kw=dict(hspace=0.05, wspace=0.25)
    )
    lines = []
    for j, proj in enumerate(["ptll", "yll"]):
        for tag, lab, col, ls in FITS:
            try:
                e, D, P = load(tag, proj)
            except (
                Exception
            ) as ex:  # a missing evaluation must be visible, not silently dropped
                print(f"MISSING {tag} {proj}: {ex}")
                continue
            rel = 100 * (P / D - 1)
            pull = (D - P) / np.sqrt(D)
            axes[0, j].stairs(rel, e, color=col, ls=ls, lw=1.6, label=lab)
            axes[1, j].stairs(
                pull,
                e,
                color=col,
                ls=ls,
                lw=1.6,
                label=f"$\\Sigma$pull$^2$={np.sum(pull**2):.1f}",
            )
            lines.append(
                f"{proj:4s} {tag:15s} sum pull^2 = {np.sum(pull**2):6.2f} over {len(D)} bins"
            )
        axes[0, j].axhline(0, color="k", lw=0.6)
        axes[1, j].axhline(0, color="k", lw=0.6)
        axes[1, j].legend(fontsize=8, ncol=2, loc="lower right")
    axes[0, 0].legend(fontsize=8, loc="upper right")
    axes[0, 0].set_ylabel("postfit / data $-$ 1 (%)")
    axes[1, 0].set_ylabel("stat. pull")
    axes[1, 0].set_xlabel(r"$p_{T}^{\ell\ell}$ (GeV)")
    axes[1, 1].set_xlabel(r"$y^{\ell\ell}$")
    axes[1, 0].set_xlim(0, 44)
    axes[1, 1].set_xlim(-2.5, 2.5)
    plot_tools.add_cms_decor(
        axes[0, 0], "Preliminary", data=True, lumi=16.8, loc=0, text_size=14
    )
    save_plot(
        TASK,
        "postfit_good_vs_bad_ptll_yll",
        fig=fig,
        meta_info={
            "note": "q = ptll projected-saturated 2dNLL of the original fit; postfits from --noFit re-evaluations"
        },
    )
    print("\n".join(lines))


if __name__ == "__main__":
    main()
