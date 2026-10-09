"""Plots for 260923-scetlib-kernel-fit. Run in the WRemnants container with the
scetlib-np-param-model worktree first on PYTHONPATH (for np_function_plots / plot_output):

  PYTHONPATH=/home/submit/lavezzo/alphaS/WRemnants-scetlib-np-param-model:$PYTHONPATH python plot.py

Reused: wums.plot_tools.figure / add_cms_decor (frame + label), scetlib_np.plot_output.save_plot
(png+pdf+log+index), scetlib_np.np_function_plots._band (percentile envelope) and its
LATTICE_CS_MU / LATTICE_CS_COV (the AN/Cridge tune). The full kernel (pert + NP) against lattice
points is not something np_function_plots draws (it plots the NP part only), so the pert table
from our_cs_kernel.py is added here.
"""

import argparse
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from wums import (
    plot_tools,
)  # noqa: E402,F401  (import at top: styles every figure the same)

from wremnants.postprocessing.scetlib_np import np_function_plots as NPF  # noqa: E402
from wremnants.postprocessing.scetlib_np.plot_output import save_plot  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kernel_fit as KF  # noqa: E402

CMS6 = ["#5790fc", "#f89c20", "#e42536", "#964a8b", "#9c9ca1", "#7a21dd"]
ENS_COL = {0: "#3f90da", 1: "#ffa90e", 2: "#bd1f01"}
ENS_LAB = {0: "L32, a=0.15 fm", 1: "L48, a=0.12 fm", 2: "L64, a=0.09 fm"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nsamp", type=int, default=4000)
    ap.add_argument(
        "--only",
        choices=["all", "l4zero"],
        default="all",
        help="l4zero: only the 2026-09-23 lambda4_nu=0 overlay (needs l4zero.py outputs)",
    )
    args = ap.parse_args()
    plt.rcParams.update({"axes.labelsize": 22, "legend.fontsize": 13})

    D = KF.load_data()
    B = np.load(os.path.join(HERE, "bands.npz"))
    FIT = json.load(open(os.path.join(HERE, "fit_results.json")))
    CMP = json.load(open(os.path.join(HERE, "compat.json")))
    T = np.load(os.path.join(HERE, "pert_tables.npz"))
    bg = B["bgrid"]
    pert = B["pert_nf5"]
    assert np.allclose(NPF.LATTICE_CS_MU, KF.TACKMANN_MU) and np.allclose(
        NPF.LATTICE_CS_COV, KF.TACKMANN_COV
    )
    meta = dict(
        data="/work/submit/lavezzo/cs_kernel/CS_lattice_results.tar (per-ensemble, block-diag cov)",
        kernel="our_cs_kernel.py N3LL nf=5 mu=2 GeV alpha_s(mZ)=0.118, fit mu0 floor + sextic b*",
        lattice_band="MCMC, flat priors, k1 floated; 16-84% envelope (np_function_plots._band)",
        postfits="scetlib_ad card A fits, lambda physical = anchor + width*theta (ad_postfits.json)",
    )

    k1_b = FIT["tanh2 | linf=2 | k1"]["x"]["k1"]
    xlab = r"$b_T$ [fm]"
    if args.only == "l4zero":
        return plot_l4zero(D, B, pert, bg, xlab, args, meta)

    def data_points(ax, k1):
        dx = {0: -0.006, 1: 0.0, 2: 0.006}
        for e in range(3):
            m = D["ens"] == e
            ax.errorbar(
                D["b"][m] + dx[e],
                D["y"][m] - k1 * D["a"][m] / D["b"][m],
                D["s"][m],
                fmt="o",
                ms=6,
                color=ENS_COL[e],
                label=ENS_LAB[e] + r" ($-\hat k_1 a/b_T$)",
                zorder=5,
            )

    def band(ax, key, color, label, hatch=None, alpha=0.35, add=pert, ls="-"):
        q = B[key]
        lo, hi = NPF._band(np.array([q[1], q[3]]), (0, 100))
        if hatch:
            ax.fill_between(
                bg,
                lo + add,
                hi + add,
                facecolor="none",
                edgecolor=color,
                hatch=hatch,
                lw=0,
                zorder=2,
            )
        else:
            ax.fill_between(
                bg, lo + add, hi + add, color=color, alpha=alpha, lw=0, zorder=2
            )
        ax.plot(bg, q[2] + add, color=color, lw=2, ls=ls, label=label, zorder=3)

    # ---------------- 1. kernel-space comparison, full kernel, all tunes (real-data postfits shown -> CMS Prelim.)
    fig, ax = plot_tools.figure(
        bg,
        xlab,
        r"$\gamma_\zeta(b_T,\mu=2\,\mathrm{GeV})$",
        ylim=(-1.9, 1.0),
        xlim=(0.08, 1.0),
        automatic_scale=False,
        width_scale=1.3,
    )
    ax.plot(bg, pert, color="k", ls=":", lw=1.5, label="SCETlib pert. only ($n_f$=5)")
    band(
        ax,
        "lat_B_linf2_np",
        "#5790fc",
        r"lattice fit, $\lambda_\infty^\nu$=2, $k_1$ (68%)",
    )
    band(
        ax,
        "lat_A_linffree_np",
        "#5790fc",
        r"lattice fit, $\lambda_\infty^\nu$ free (68%)",
        hatch="///",
        ls="--",
    )
    band(ax, "tune0_np", "#9c9ca1", "Tackmann/Cridge (AN) $\\pm1\\sigma$", alpha=0.45)
    labs = {
        1: "unwalled, main min. (warm)",
        2: "unwalled, 2nd min. (cold)",
        3: "walled, main (warm)",
        4: "walled, cold-resumed",
        5: "walled, from unwalled 2nd",
    }
    cols = {1: "#e42536", 2: "#e42536", 3: "#f89c20", 4: "#964a8b", 5: "#7a21dd"}
    lss = {1: "-", 2: "--", 3: "-", 4: "-.", 5: ":"}
    for i in range(1, 6):
        q = B[f"tune{i}_np"]
        ax.fill_between(
            bg, q[1] + pert, q[3] + pert, color=cols[i], alpha=0.25, lw=0, zorder=2
        )
        ax.plot(
            bg,
            q[2] + pert,
            color=cols[i],
            ls=lss[i],
            lw=2,
            label="Z postfit: " + labs[i],
            zorder=3,
        )
    data_points(ax, k1_b)
    ax.axhline(0, color="0.6", lw=0.8)
    ax.legend(loc="lower left", ncol=2, fontsize=11, frameon=False)
    ax.text(
        0.98,
        0.97,
        r"postfits: $\lambda_\infty^\nu$=2 frozen, tanh_2"
        "\n"
        r"points: $-\hat k_1 a/b_T$, $\hat k_1$=%.2f" % k1_b,
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=12,
    )
    plot_tools.add_cms_decor(ax, "Preliminary", loc=0, data=True, no_energy=True)
    save_plot(HERE, "kernel_space_comparison", fig=fig, args=args, meta_info=meta)
    plt.close(fig)

    # ---------------- 2. lattice-only: per-ensemble data vs fitted model at each a (no CMS label)
    fig, ax = plot_tools.figure(
        bg,
        xlab,
        r"$\gamma_\zeta(b_T,\mu=2\,\mathrm{GeV};a)$",
        ylim=(-2.2, 1.0),
        xlim=(0.05, 1.0),
        automatic_scale=False,
        width_scale=1.3,
    )
    for lab, ls in [("tanh2 | linf=2 | k1", "-"), ("tanh2 | linf free | k1", "--")]:
        r = FIT[lab]
        x = dict(
            dict(linf=1.6853, l2=0, l4=0, l6=0, k1=0, k2=0), **r["fixed"], **r["x"]
        )
        for e, a in enumerate([0.15, 0.12, 0.09]):
            ax.plot(
                bg,
                pert
                + KF.np_zeta(bg, x["linf"], x["l2"], x["l4"])
                + x["k1"] * a / bg
                + x["k2"] * (a / bg) ** 2,
                color=ENS_COL[e],
                ls=ls,
                lw=1.5,
            )
        ax.plot(
            bg,
            pert + KF.np_zeta(bg, x["linf"], x["l2"], x["l4"]),
            color="k",
            ls=ls,
            lw=2,
            label=(
                r"$a$=0, "
                + (
                    r"$\lambda_\infty^\nu$=2"
                    if "linf=2" in lab
                    else r"$\lambda_\infty^\nu$ free"
                )
            )
            + f": $\\chi^2$/ndf={r['chi2']:.2f}/{r['ndf']}",
        )
    for e in range(3):
        m = D["ens"] == e
        ax.errorbar(
            D["b"][m],
            D["y"][m],
            D["s"][m],
            fmt="o",
            ms=6,
            color=ENS_COL[e],
            label=ENS_LAB[e] + " (raw)",
        )
    ax.plot(bg, pert, color="k", ls=":", lw=1.2, label="SCETlib pert. only")
    ax.legend(loc="lower left", fontsize=12, frameon=False)
    ax.text(
        0.98,
        0.97,
        "our kernel (tanh_2) + $k_1 a/b_T$, full cov.\ncoloured: model at each ensemble's $a$",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=12,
    )
    save_plot(HERE, "lattice_fit_per_ensemble", fig=fig, args=args, meta_info=meta)
    plt.close(fig)

    # ---------------- 3. lambda space (linf=2 slice): lattice contours vs postfits, Tackmann, anchor, syst variants
    D2 = D
    l2g = np.linspace(-0.15, 0.32, 160)
    l4g = np.linspace(-0.02, 0.05, 160)
    W = np.linalg.inv(D2["cov"])
    X = (D2["a"] / D2["b"])[:, None]
    A_ = np.linalg.inv(X.T @ W @ X) @ X.T @ W
    Z = np.zeros((len(l4g), len(l2g)))
    Z16 = np.zeros_like(Z)
    for i, l4 in enumerate(l4g):
        for j, l2 in enumerate(l2g):
            for Zm, li in ((Z, 2.0), (Z16, 1.6853)):
                y = D2["y"] - T["data_nf5"] - KF.np_zeta(D2["b"], li, l2, l4)
                r = y - X @ (A_ @ y)
                Zm[i, j] = r @ W @ r
    Z -= Z.min()
    Z16 -= Z16.min()
    fig, ax = plot_tools.figure(
        l2g,
        r"$\lambda_2^\nu$ [GeV$^2$]",
        r"$\lambda_4^\nu$ [GeV$^4$]",
        xlim=(l2g[0], l2g[-1]),
        ylim=(l4g[0], l4g[-1]),
        automatic_scale=False,
        width_scale=1.25,
    )
    cs = ax.contour(
        l2g,
        l4g,
        Z,
        levels=[2.30, 6.18, 11.83],
        colors=["#5790fc"] * 3,
        linestyles=["-", "--", ":"],
        linewidths=2,
    )
    ax.contour(
        l2g,
        l4g,
        Z16,
        levels=[2.30],
        colors=["#9c9ca1"],
        linestyles=["-"],
        linewidths=1.5,
    )
    ax.plot(
        [],
        [],
        color="#5790fc",
        ls="-",
        label=r"lattice, $\lambda_\infty^\nu$=2: 1/2/3$\sigma$ (2D, $k_1$ prof.)",
    )
    ax.plot(
        [],
        [],
        color="#9c9ca1",
        ls="-",
        label=r"lattice, $\lambda_\infty^\nu$=1.6853: 1$\sigma$",
    )
    # Tackmann: conditional on linf = 1.6853 is what the old lat-cov term used; show the MARGINAL 2D ellipse
    C = KF.TACKMANN_COV[1:, 1:]
    t = np.linspace(0, 2 * np.pi, 200)
    Lc = np.linalg.cholesky(C) * np.sqrt(2.30)
    el = KF.TACKMANN_MU[1:, None] + Lc @ np.vstack([np.cos(t), np.sin(t)])
    ax.plot(
        el[0],
        el[1],
        color="k",
        lw=1.5,
        ls="-.",
        label=r"Tackmann/Cridge (AN), marginal 1$\sigma$ ($\lambda_\infty^\nu$=1.69)",
    )
    ax.plot(*KF.TACKMANN_MU[1:], "k*", ms=14)
    for i in range(1, 6):
        tu = CMP["tunes"][i]
        Cp = np.array(tu["cov"])
        mu = np.array([tu["lam"]["l2"], tu["lam"]["l4"]])
        Lp = np.linalg.cholesky(Cp + 1e-14 * np.eye(2)) * np.sqrt(2.30)
        ep = mu[:, None] + Lp @ np.vstack([np.cos(t), np.sin(t)])
        ax.plot(ep[0], ep[1], color=cols[i], lw=1.5, ls=lss[i])
        ax.plot(*mu, "o", color=cols[i], ms=8, label="Z postfit: " + labs[i])
    ax.plot(
        0.15,
        0.0,
        "s",
        color="#9c9ca1",
        ms=10,
        mfc="none",
        mew=2,
        label="card anchor (FranksVals)",
    )
    for lab, mk in [
        ("SYST nf4 scheme, linf=2", "v"),
        ("SYST nf matched mu=1, linf=2", "^"),
        ("SYST drop bT<0.2 fm, linf=2", "<"),
        ("SYST k2, linf=2", ">"),
        ("SYST k1+k2, linf=2", "D"),
    ]:
        x = FIT[lab]["x"]
        ax.plot(x["l2"], x["l4"], mk, color="#5790fc", ms=7, mfc="none")
    xb = FIT["tanh2 | linf=2 | k1"]["x"]
    ax.plot(
        xb["l2"],
        xb["l4"],
        "P",
        color="#5790fc",
        ms=12,
        label="lattice best fit (open: syst. variants)",
    )
    ax.axhline(0, color="0.6", lw=0.8)
    ax.axvline(0, color="0.6", lw=0.8)
    ax.axhspan(l4g[0], 0, xmin=0, xmax=1, color="0.85", alpha=0.3, lw=0)
    ax.text(
        0.30,
        -0.017,
        r"$\lambda_4^\nu<0$: turns over (wall)",
        ha="right",
        fontsize=11,
        color="0.4",
    )
    ax.legend(loc="upper right", fontsize=10.5, frameon=False)
    plot_tools.add_cms_decor(ax, "Preliminary", loc=0, data=True, no_energy=True)
    save_plot(HERE, "lambda_space_linf2", fig=fig, args=args, meta_info=meta)
    plt.close(fig)

    # ---------------- 4. lattice-only NP-part: fit configurations / systematics vs Tackmann (no CMS label)
    fig, ax = plot_tools.figure(
        bg,
        xlab,
        r"$\gamma_\zeta^{\rm NP}(b_T)$ (SCETlib scheme)",
        ylim=(-1.2, 0.15),
        xlim=(0.08, 1.0),
        automatic_scale=False,
        width_scale=1.25,
    )
    band(
        ax, "lat_B_linf2_np", "#5790fc", r"lattice, $\lambda_\infty^\nu$=2 (68%)", add=0
    )
    band(
        ax,
        "lat_A_linffree_np",
        "#5790fc",
        r"lattice, $\lambda_\infty^\nu$ free (68%)",
        hatch="///",
        add=0,
        ls="--",
    )
    band(
        ax,
        "lat_Bphys_linf2_np",
        "#964a8b",
        r"lattice, $\lambda_\infty^\nu$=2, $\lambda_{2,4}^\nu\geq0$ (68%)",
        add=0,
        alpha=0.3,
    )
    band(
        ax,
        "tune0_np",
        "#9c9ca1",
        "Tackmann/Cridge (AN) $\\pm1\\sigma$",
        add=0,
        alpha=0.45,
    )
    variants = [
        ("SYST nf4 scheme, linf=2", r"$n_f$=4 scheme"),
        ("SYST nf matched mu=1, linf=2", r"$n_f$ matched at 1 GeV"),
        ("SYST drop bT<0.2 fm, linf=2", r"drop $b_T<0.2$ fm"),
        ("SYST k2, linf=2", r"$k_2$ only"),
        ("SYST k1+k2, linf=2", r"$k_1+k_2$"),
        ("tanh6 | linf=2 | k1", "tanh_6"),
    ]
    for (lab, name), c in zip(variants, CMS6):
        x = dict(dict(linf=2.0, l6=0.0), **FIT[lab]["fixed"], **FIT[lab]["x"])
        ax.plot(
            bg,
            KF.np_zeta(bg, x["linf"], x["l2"], x["l4"], x.get("l6", 0.0)),
            color=c,
            lw=1.5,
            ls="--",
            label=name,
        )
    ax.axhline(0, color="0.6", lw=0.8)
    ax.legend(loc="lower left", fontsize=11, ncol=2, frameon=False)
    save_plot(HERE, "np_part_variants", fig=fig, args=args, meta_info=meta)
    plt.close(fig)

    # ---------------- 5. profile chi2 in linf
    pf = FIT["_profile_linf"]
    fig, ax = plot_tools.figure(
        np.array(pf["grid"]),
        r"$\lambda_\infty^\nu$",
        r"$\chi^2_{\rm min}-\chi^2_{\rm best}$",
        xlim=(0.25, 25),
        ylim=(0, 10),
        automatic_scale=False,
        logx=True,
    )
    g = np.array(pf["grid"])
    c = np.array(pf["chi2"]) - min(pf["chi2"])
    ax.plot(
        g,
        c,
        "o-",
        color="#5790fc",
        lw=2,
        label=r"tanh_2 + $k_1$, $\lambda_{2,4}^\nu$, $k_1$ profiled",
    )
    ax.axhline(1, color="0.5", ls="--")
    ax.axhline(4, color="0.5", ls=":")
    ax.axvline(1.6853, color="k", ls="-.", lw=1, label="Tackmann 1.6853")
    ax.axvline(2.0, color="#e42536", ls="-.", lw=1, label="fits: 2 (frozen)")
    ax.legend(loc="upper right", frameon=False)
    save_plot(HERE, "profile_linf", fig=fig, args=args, meta_info=meta)
    plt.close(fig)


def plot_l4zero(D, B, pert, bg, xlab, args, meta):
    """2026-09-23: lambda4_nu = 0 fit band vs the free-(l2,l4) band, full kernel, lattice points.
    Lattice-only + reference tunes (no real-data postfit) -> no CMS label."""
    Z = np.load(os.path.join(HERE, "bands_l4zero.npz"))
    J = json.load(open(os.path.join(HERE, "fit_l4zero.json")))
    k1z = J["fits"]["L4=0 | linf=2 | k1 [nominal]"]["x"]["k1"]
    L = J["lambda2_nu"]
    fig, ax = plot_tools.figure(
        bg,
        xlab,
        r"$\gamma_\zeta(b_T,\mu=2\,\mathrm{GeV})$",
        ylim=(-1.6, 0.8),
        xlim=(0.08, 1.0),
        automatic_scale=False,
        width_scale=1.3,
    )
    ax.plot(bg, pert, color="k", ls=":", lw=1.5, label="SCETlib pert. only ($n_f$=5)")
    q = B["lat_B_linf2_np"]
    ax.fill_between(
        bg,
        q[1] + pert,
        q[3] + pert,
        facecolor="none",
        edgecolor="#5790fc",
        hatch="///",
        lw=0,
        zorder=2,
    )
    ax.plot(
        bg,
        q[2] + pert,
        color="#5790fc",
        ls="--",
        lw=2,
        label=r"free $\lambda_2^\nu,\lambda_4^\nu$ ($\lambda_\infty^\nu$=2, $k_1$), 68%",
    )
    z = Z["lat_l4zero_np"]
    t = Z["lat_l4zero_totband_np"]
    ax.fill_between(
        bg, t[0] + pert, t[2] + pert, color="#e42536", alpha=0.18, lw=0, zorder=2
    )
    ax.fill_between(
        bg, z[1] + pert, z[3] + pert, color="#e42536", alpha=0.35, lw=0, zorder=2
    )
    ax.plot(
        bg,
        z[2] + pert,
        color="#e42536",
        lw=2,
        label=r"$\lambda_4^\nu$=0: $\lambda_2^\nu$=%.3f$\pm$%.3f(stat)$\pm$%.3f(syst)"
        % (L["central"], L["stat"], L["syst"]),
    )
    ax.plot(
        [],
        [],
        color="#e42536",
        alpha=0.18,
        lw=8,
        label=r"$\lambda_4^\nu$=0: stat (dark) / stat+syst (light)",
    )
    ax.plot(
        bg,
        pert + KF.np_zeta(bg, 2.0, 0.15, 0.0),
        color="#9c9ca1",
        lw=1.8,
        ls="-.",
        label=r"card anchor $\lambda_2^\nu$=0.15",
    )
    ax.plot(
        bg,
        pert + KF.np_zeta(bg, *KF.TACKMANN_MU),
        color="k",
        lw=1.5,
        ls="-.",
        label="Tackmann/Cridge (AN) central",
    )
    dx = {0: -0.006, 1: 0.0, 2: 0.006}
    for e in range(3):
        m = D["ens"] == e
        ax.errorbar(
            D["b"][m] + dx[e],
            D["y"][m] - k1z * D["a"][m] / D["b"][m],
            D["s"][m],
            fmt="o",
            ms=6,
            color=ENS_COL[e],
            label=ENS_LAB[e] + r" ($-\hat k_1 a/b_T$)",
            zorder=5,
        )
    ax.axhline(0, color="0.6", lw=0.8)
    ax.legend(loc="lower left", ncol=2, fontsize=11, frameon=False)
    ax.text(
        0.98,
        0.97,
        r"tanh_2, $\lambda_\infty^\nu$=2; points shifted by $\hat k_1$=%.2f ($\lambda_4^\nu$=0 fit)"
        % k1z,
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=12,
    )
    save_plot(HERE, "kernel_space_l4zero", fig=fig, args=args, meta_info=meta)
    plt.close(fig)


if __name__ == "__main__":
    main()
