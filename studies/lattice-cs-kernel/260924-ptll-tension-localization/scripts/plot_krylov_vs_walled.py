#!/usr/bin/env python3
"""Where does the unphysical-NP minimum (CCKRYLOVWARM, projected ptll q 56/39) change the ptll spectrum,
relative to the walled fit on the same card (CCWALLWARMPF, 70/39)?

Top: postfit ptll prediction ratio KRYLOV / WALLWARM, normalised to the same total (lumi etc. differ).
Bottom: stat-only residual (data - postfit)/sqrt(data) of each fit.
The prediction change includes the alpha_s, lambda AND nuisance differences between the two minima.
usage: plot_krylov_vs_walled.py   (inside the container, after setup.sh)
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

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
FITS = {
    "CCKRYLOVWARM": (
        "260917_cc_fits_hvpfix/fitresults_CCKRYLOVWARM.hdf5",
        "unwalled ($\\lambda_2^\\nu<0$), q=56.0",
        "#d62728",
    ),
    "CCWALLWARMPF": (
        "260917_cc_fits_wall/fitresults_CCWALLWARMPF.hdf5",
        "walled, q=70.4",
        "#1f77b4",
    ),
}


def get(f):
    r = io_tools.get_fitresult(f"{A}/{f}")
    ch = r["mappings"]["Project ch0 ptll"]["channels"]["ch0"]
    d = ch["hist_data_obs"].get()
    p = ch["hist_postfit_inclusive"].get()
    return d.axes[0].edges, d.values(), p.values(), p.variances()


def main():
    res = {k: get(v[0]) for k, v in FITS.items()}
    edges, D, Pk, Vk = res["CCKRYLOVWARM"]
    _, _, Pw, Vw = res["CCWALLWARMPF"]
    ratio = (Pk / Pk.sum()) / (Pw / Pw.sum())
    fig, (ax, axr) = plt.subplots(
        2, 1, figsize=(8, 7.5), sharex=True, gridspec_kw=dict(height_ratios=[1, 1])
    )
    ax.stairs(
        100 * (ratio - 1),
        edges,
        color="k",
        lw=1.8,
        label="postfit prediction: unwalled / walled (shape only)",
    )
    ax.axhline(0, color="k", lw=0.6)
    ax.set_ylabel("unw./wall. $-$ 1 (%)")
    ax.legend(loc="upper right", fontsize=9)
    for k, (f, lab, col) in FITS.items():
        _, Dk, P, V = res[k]
        pull = (Dk - P) / np.sqrt(Dk)
        axr.stairs(
            pull,
            edges,
            color=col,
            lw=1.6,
            label=f"{lab}: $\\Sigma$pull$^2$={np.sum(pull**2):.1f}",
        )
    axr.axhline(0, color="k", lw=0.6)
    axr.set_ylabel("stat. pull")
    axr.set_xlabel(r"$p_{T}^{\ell\ell}$ (GeV)")
    axr.set_xlim(0, 44)
    axr.legend(loc="lower right", fontsize=9)
    plot_tools.add_cms_decor(ax, "Preliminary", data=True, lumi=16.8, loc=0)
    save_plot(
        TASK,
        "krylov_vs_walled_ptll",
        fig=fig,
        meta_info={
            "note": "prediction change includes alpha_s, lambda and nuisance differences between minima"
        },
    )
    for i in range(len(D)):
        print(
            f"{edges[i]:5.1f}-{edges[i+1]:5.1f}  unw/wall-1 {100*(ratio[i]-1):+6.3f}%   "
            f"pull_unw {(D[i]-Pk[i])/np.sqrt(D[i]):+5.2f}  pull_wall {(D[i]-Pw[i])/np.sqrt(D[i]):+5.2f}"
        )


if __name__ == "__main__":
    main()
