"""Postfit NP plots for 260923-lattice-fits, from ../analysis.json (written by analyze_fits.py).

1. kernel_space_postfit: full CS kernel gamma_zeta(b_T, mu=2 GeV) = SCETlib pert (n_f=5, from
   260923-scetlib-kernel-fit/bands.npz) + (1/2) gamma_nu^NP(lambda_postfit), for the lattice arms and the cold
   references, against the ASWZ lattice points (shifted by the lambda4_nu=0 fit's k1) and the lambda4_nu=0
   lattice band (bands_l4zero.npz). Postfit bands: 16-84 % of Gaussian toys from each arm's postfit NP covariance
   (CS lambdas only; CS-TMD correlations do not enter a CS-only curve).
2. np_forms_postfit: the two NP form factors (gamma_nu^NP and F_eff at |Y| = 0, 2.5) via the existing
   scetlib_np.np_function_plots.plot_np_functions, toys from the full 5x5 (4x4 when lambda4_nu is frozen) NP cov.

Run in the container with the scetlib-np-param-model worktree FIRST on PYTHONPATH (np_function_plots lives there;
nothing here needs scetlib_ad):
  PYTHONPATH=/home/submit/lavezzo/alphaS/WRemnants-scetlib-np-param-model:$PYTHONPATH python postfit_plots.py
"""

import argparse
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from wums import plot_tools  # noqa: E402

from wremnants.postprocessing.scetlib_np import np_function_plots as NPF  # noqa: E402
from wremnants.postprocessing.scetlib_np.params import NPTune  # noqa: E402
from wremnants.postprocessing.scetlib_np.plot_output import save_plot  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KFDIR = os.path.join(os.path.dirname(HERE), "260923-scetlib-kernel-fit")
sys.path.insert(0, KFDIR)
import kernel_fit as KF  # noqa: E402

ENS_COL = {0: "#3f90da", 1: "#ffa90e", 2: "#bd1f01"}
ENS_LAB = {0: "L32, a=0.15 fm", 1: "L48, a=0.12 fm", 2: "L64, a=0.09 fm"}
STYLE = {
    "LATL4ZUNW": (
        "#e42536",
        "-",
        "lattice $\\lambda_2^\\nu$ term, $\\lambda_4^\\nu$=0, no wall (cold)",
    ),
    "LATL4ZUNWWARM": (
        "#7a21dd",
        "-.",
        "lattice $\\lambda_2^\\nu$ term, $\\lambda_4^\\nu$=0, no wall (warm, from walled min.)",
    ),
    "LATL4ZWALL": (
        "#964a8b",
        "-",
        "lattice $\\lambda_2^\\nu$ term, $\\lambda_4^\\nu$=0, wall (cold)",
    ),
    "CCCOLDSELF": ("#9c9ca1", "--", "reference: no wall, cold (2nd min.)"),
    "CCKRYLOVWARM": ("#7a7a7a", ":", "reference: no wall, main min. (warm)"),
    "CCWALLCOLDR": ("#f89c20", "--", "reference: wall, cold"),
    "CCWALLWARMPF": ("#5790fc", "-.", "reference: wall, warm"),
}
ANCHOR = dict(
    lambda2=0.4,
    lambda4=0.4,
    delta_lambda2=0.0,
    lambda2_nu=0.15,
    lambda4_nu=0.0,
    lambda_inf=1.0,
    lambda_inf_nu=2.0,
)


def toys(arm, n, rng):
    names = arm["np_cov_phys"]["names"]
    C = np.array(arm["np_cov_phys"]["cov"])
    mu = np.array([arm["phys"][k] for k in names])
    L = np.linalg.cholesky(C + 1e-18 * np.eye(len(names)))
    X = mu + rng.standard_normal((n, len(names))) @ L.T
    out = []
    for x in X:
        d = dict(arm["phys"])
        d.update(dict(zip(names, x)))
        out.append(d)
    return out


def tune(d):
    v = {
        k: float(d[k])
        for k in (
            "lambda2",
            "lambda4",
            "delta_lambda2",
            "lambda_inf",
            "lambda2_nu",
            "lambda4_nu",
            "lambda_inf_nu",
        )
    }
    return NPTune.create("tanh_2", "tanh_2", v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--analysis", default=os.path.join(HERE, "analysis.json"))
    ap.add_argument(
        "--arms",
        nargs="+",
        default=["LATL4ZUNW", "LATL4ZWALL", "CCCOLDSELF", "CCWALLCOLDR"],
    )
    ap.add_argument("--ntoys", type=int, default=2000)
    ap.add_argument(
        "--np-arms",
        nargs="+",
        default=["LATL4ZUNWWARM", "LATL4ZUNW", "LATL4ZWALL", "CCWALLWARMPF"],
        help="arms on the NP-form-factor figure (kept few: np_function_plots draws y-shaded ramps)",
    )
    ap.add_argument("--ylim-cs", dest="ylim_cs", type=float, nargs=2, default=None)
    ap.add_argument(
        "--ylim-tmd", dest="ylim_tmd", type=float, nargs=2, default=(0.0, 1.4)
    )
    args = ap.parse_args()
    R = json.load(open(args.analysis))
    arms = [a for a in args.arms if a in R]
    missing = [a for a in args.arms if a not in R]
    if missing:
        print(f"[warn] not in {args.analysis}: {missing}")
    rng = np.random.default_rng(1)
    for a in arms:
        R[a]["phys"].setdefault("lambda_inf", 1.0)
        R[a]["phys"].setdefault("lambda_inf_nu", 2.0)

    # ---------------- 1. kernel space
    B = np.load(os.path.join(KFDIR, "bands.npz"))
    Z = np.load(os.path.join(KFDIR, "bands_l4zero.npz"))
    J = json.load(open(os.path.join(KFDIR, "fit_l4zero.json")))
    D = KF.load_data()
    bg, pert = B["bgrid"], B["pert_nf5"]
    assert np.allclose(Z["bgrid"], bg)
    k1z = J["fits"]["L4=0 | linf=2 | k1 [nominal]"]["x"]["k1"]
    Lz = J["lambda2_nu"]
    fig, ax = plot_tools.figure(
        bg,
        r"$b_T$ [fm]",
        r"$\gamma_\zeta(b_T,\mu=2\,\mathrm{GeV})$",
        ylim=(-1.6, 0.9),
        xlim=(0.08, 1.0),
        automatic_scale=False,
        width_scale=1.3,
    )
    ax.plot(bg, pert, color="k", ls=":", lw=1.5, label="SCETlib pert. only ($n_f$=5)")
    zb, tb = Z["lat_l4zero_np"], Z["lat_l4zero_totband_np"]
    ax.fill_between(
        bg, tb[0] + pert, tb[2] + pert, color="#5790fc", alpha=0.18, lw=0, zorder=2
    )
    ax.fill_between(
        bg, zb[1] + pert, zb[3] + pert, color="#5790fc", alpha=0.35, lw=0, zorder=2
    )
    ax.plot(
        bg,
        zb[2] + pert,
        color="#5790fc",
        lw=2,
        label=r"ASWZ lattice, $\lambda_4^\nu$=0: $\lambda_2^\nu$=%.3f$\pm$%.3f (stat, dark) / $\pm$%.3f (tot, light)"
        % (Lz["central"], Lz["stat"], Lz["tot"]),
    )
    for a in arms:
        col, ls, lab = STYLE.get(a, ("k", "-", a))
        p = R[a]["phys"]
        cs = [n for n in R[a]["np_cov_phys"]["names"] if n.endswith("_nu")]
        T = toys(R[a], args.ntoys, rng)
        curves = np.array(
            [KF.np_zeta(bg, 2.0, t["lambda2_nu"], t["lambda4_nu"]) for t in T]
        )
        lo, hi = np.percentile(curves, [16, 84], axis=0)
        ax.fill_between(bg, lo + pert, hi + pert, color=col, alpha=0.25, lw=0, zorder=3)
        ax.plot(
            bg,
            pert + KF.np_zeta(bg, 2.0, p["lambda2_nu"], p["lambda4_nu"]),
            color=col,
            ls=ls,
            lw=2,
            label=f"Z postfit: {lab}",
            zorder=4,
        )
        print(
            f"[kernel] {a}: lambda2_nu {p['lambda2_nu']:+.4f} lambda4_nu {p['lambda4_nu']:+.5f}  (band from {cs})"
        )
    dx = {0: -0.006, 1: 0.0, 2: 0.006}
    for e in range(3):
        m = D["ens"] == e
        ax.errorbar(
            D["b"][m] + dx[e],
            D["y"][m] - k1z * D["a"][m] / D["b"][m],
            D["s"][m],
            fmt="o",
            ms=5,
            color=ENS_COL[e],
            label=ENS_LAB[e] + r" ($-\hat k_1 a/b_T$)",
            zorder=5,
        )
    ax.axhline(0, color="0.6", lw=0.8)
    ax.legend(loc="lower left", ncol=1, fontsize=10, frameon=False)
    ax.text(
        0.98,
        0.97,
        "tanh_2, $\\lambda_\\infty^\\nu$=2 frozen\npoints shifted by $\\hat k_1$=%.2f ($\\lambda_4^\\nu$=0 lattice fit)\n"
        "postfit bands: 68%% from postfit CS cov." % k1z,
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=11,
    )
    plot_tools.add_cms_decor(ax, "Preliminary", loc=0, data=True, no_energy=True)
    meta = dict(
        analysis=args.analysis,
        lattice="260923-scetlib-kernel-fit fit_l4zero.json / bands_l4zero.npz",
        pert="bands.npz pert_nf5 (our_cs_kernel.py N3LL n_f=5 mu=2 GeV)",
        note="alpha_s blinded; nothing here depends on it",
    )
    save_plot(HERE, "kernel_space_postfit", fig=fig, args=args, meta_info=meta)
    plt.close(fig)

    # ---------------- 2. both NP form factors via np_function_plots
    SHORT = {
        "LATL4ZUNWWARM": "lat., no wall (warm)",
        "LATL4ZUNW": "lat., no wall",
        "LATL4ZWALL": "lat. + wall",
        "CCWALLWARMPF": "old wall (warm)",
        "CCWALLCOLDR": "old wall (cold)",
        "CCCOLDSELF": "old no wall (cold)",
    }
    CMAP = {
        "LATL4ZUNWWARM": "Greens",
        "LATL4ZUNW": "Reds",
        "LATL4ZWALL": "Purples",
        "CCWALLWARMPF": "Blues",
        "CCWALLCOLDR": "Oranges",
        "CCCOLDSELF": "Greys",
    }
    series = [
        NPF.Series(label="anchor", lam=tune(ANCHOR), color="k", linestyle=":", lw=1.5)
    ]
    for a in [x for x in args.np_arms if x in R]:
        series.append(
            NPF.Series(
                label=SHORT.get(a, a),
                lam=tune(R[a]["phys"]),
                cmap=CMAP.get(a),
                toys=[tune(t) for t in toys(R[a], 400, rng)],
            )
        )
    NPF.plot_np_functions(
        series,
        y_values=(0.0, 2.5),
        bT_max=4.0,
        outpath=os.path.join(HERE, "np_forms_postfit.png"),
        insets=[(s.label, s) for s in series[1:]],
        lattice_reference=False,
        map22_reference=True,
        args=args,
    )
    print("PLOTS_DONE")


if __name__ == "__main__":
    main()
