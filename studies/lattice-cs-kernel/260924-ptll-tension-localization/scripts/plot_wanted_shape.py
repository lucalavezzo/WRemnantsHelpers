#!/usr/bin/env python3
"""The ptll correction the data want, from the ptll projected-saturated sub-fits of LATL4ZWALLCOLD.

Squared per-bin scales of three sub-fits, each divided by its own ptll > 5 GeV plateau (the overall level is
degenerate with the normalisation nuisances and not meaningful). Uncertainties propagate the full sub-fit
covariance through that ratio.
  free    : PT3044 'Project ch0 ptll' (alpha_s free -> the scales mostly absorb the alpha_s shift)
  FRZAS   : alpha_s held at the main-fit value
  FRZASNP : alpha_s + NP lambdas held
usage: plot_wanted_shape.py   (inside the container, after setup.sh)
"""
import json
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

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260924_ptll_tension_loc"
RUNS = [
    ("free", "PT3044", r"$\alpha_S$ free", "#999999"),
    ("FRZAS", "FRZAS", r"$\alpha_S$ held", "#1f77b4"),
    ("FRZASNP", "FRZASNP", r"$\alpha_S$ + NP $\lambda$ held", "#d62728"),
]
EDGES = np.array(
    [
        0,
        1,
        1.5,
        2,
        2.5,
        3,
        3.5,
        4,
        4.5,
        5,
        5.5,
        6,
        6.5,
        7,
        7.5,
        8,
        8.5,
        9,
        9.5,
        10,
        10.5,
        11,
        11.5,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        22,
        24,
        26,
        28,
        30,
        33,
        37,
        44,
    ],
    float,
)
PLATEAU = list(range(9, 39))  # ptll > 5 GeV


def shape(tag):
    r = io_tools.get_fitresult(f"{A}/{tag}/fitresults_{tag}.hdf5")
    mp = r["mappings"]["Project ch0 ptll"]
    sf = mp["saturated_fit"]
    h = sf["parms"].get()
    n = [str(x) for x in h.axes[0]]
    idx = [n.index(f"saturated_ch0_ptll{i}") for i in range(39)]
    s = h.values()[idx]
    Cs = sf["cov"].get().values()[np.ix_(idx, idx)]
    S = s**2
    CS = np.diag(2 * s) @ Cs @ np.diag(2 * s)
    w = np.zeros(39)
    w[PLATEAU] = 1 / len(PLATEAU)
    P = S @ w
    J = np.eye(39) / P - np.outer(S, w) / P**2
    CR = J @ CS @ J.T
    return (
        S / P,
        np.sqrt(np.diag(CR)),
        CR,
        float(mp["chi2_saturated"]),
        float(sf["edmval"]),
        float(P),
    )


def main():
    fig, (ax, axm) = plt.subplots(
        2, 1, figsize=(8, 8), sharex=True, gridspec_kw=dict(height_ratios=[3, 2])
    )
    out = {}
    for key, tag, label, col in RUNS:
        R, e, CR, q, edm, P = shape(tag)
        out[key] = dict(R=R.tolist(), err=e.tolist(), q=q, edm=edm, plateau=P)
        y = 100 * (R - 1)
        if key == "free":
            # absorbs the sub-fit's alpha_s shift (-10 sigma_main): off scale, legend entry only
            ax.plot(
                [],
                [],
                color=col,
                ls="--",
                label=f"{label}  (q = {q:.1f}/39; absorbs the $\\alpha_S$ shift, off scale)",
            )
            continue
        ax.stairs(y, EDGES, color=col, lw=1.8, label=f"{label}  (q = {q:.1f}/39)")
        # dominant correlated mode of the ratio covariance (the direction carrying the most chi2)
        w, V = np.linalg.eigh(CR)
        keep = w > 1e-12 * w.max()
        z = (V[:, keep].T @ (R - 1)) / np.sqrt(w[keep])
        k = int(np.argmax(z**2))
        c = 100 * z[k] * np.sqrt(w[keep][k]) * V[:, keep][:, k]
        sig = 100 * np.sqrt(w[keep][k]) * np.abs(V[:, keep][:, k])
        axm.stairs(c + sig, EDGES, baseline=c - sig, fill=True, color=col, alpha=0.2)
        axm.stairs(
            c, EDGES, color=col, lw=1.8, label=f"{label}: mode $z^2$ = {z[k]**2:.1f}"
        )
        out.setdefault("modes", {})[key] = dict(contrib=c.tolist(), z2=float(z[k] ** 2))
        if key != "free":
            ax.stairs(
                y + 100 * e,
                EDGES,
                baseline=y - 100 * e,
                fill=True,
                color=col,
                alpha=0.2,
            )
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xlim(0, 44)  # linear: the real bin edges, 0 included
    axm.axhline(0, color="k", lw=0.8)
    axm.set_xlabel(r"$p_{T}^{\ell\ell}$ (GeV)")
    ax.set_ylabel("wanted change (%)")
    axm.set_ylabel("leading mode (%)")
    ax.set_ylim(-8, 14)
    ax.legend(loc="upper right", fontsize=9)
    axm.legend(loc="lower left", fontsize=9)
    plot_tools.add_cms_decor(ax, "Preliminary", data=True, lumi=16.8, loc=0)
    save_plot(
        TASK,
        "ptll_wanted_shape",
        fig=fig,
        meta_info={
            "note": "band = full sub-fit covariance of the ratio; alpha_s-free curve absorbs the alpha_s shift; "
            "diagnostic sub-fits, not GoF"
        },
    )
    with open(os.path.join(TASK, "wanted_shape.json"), "w") as fo:
        json.dump(out, fo, indent=1)
    for i in range(39):
        print(
            f"{EDGES[i]:5.1f}-{EDGES[i+1]:5.1f} "
            + "  ".join(
                f"{k}: {100*(out[k]['R'][i]-1):+6.2f}+-{100*out[k]['err'][i]:.2f}"
                for k in ("FRZAS", "FRZASNP")
            )
        )
    for k, v in out.items():
        if k == "modes":
            continue
        print(
            k, "q", round(v["q"], 2), "edm", v["edm"], "plateau", round(v["plateau"], 4)
        )


if __name__ == "__main__":
    main()
