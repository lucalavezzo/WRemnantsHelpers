#!/usr/bin/env python3
"""Kernel-space plot for T8: full CS kernel gamma_zeta(b_T, mu=2 GeV) = SCETlib pert (n_f=5) + (1/2) gamma_nu^NP(postfit)
for NOMSTIFF and the T8 2D-float results, against the ASWZ per-ensemble lattice points and the two lattice bands that the
cards encode (1D lambda4_nu=0 fit; 2D lambda_inf_nu=2 fit, MCMC 16-84 %). Section 1 of
lattice-cs-kernel/260923-lattice-fits/scripts/postfit_plots.py, re-pointed at this task dir and at fitresults directly.
Postfit bands: 16-84 % of Gaussian toys from each fit's (lambda2_nu[, lambda4_nu]) covariance (theta -> physical).
Usage: kernel_plot.py LABEL=fitresult[:covfitresult] ...   (alphaS is never read)"""
import argparse
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import json  # noqa: E402
import numpy as np  # noqa: E402
from wums import plot_tools  # noqa: E402
from rabbit import io_tools  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common as C  # noqa: E402
from plot_output import save_plot  # noqa: E402

KFDIR = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/lattice-cs-kernel/260923-scetlib-kernel-fit"
sys.path.insert(0, KFDIR)
import kernel_fit as KF  # noqa: E402

ENS_COL = {0: "#3f90da", 1: "#ffa90e", 2: "#bd1f01"}
ENS_LAB = {0: "L32, a=0.15 fm", 1: "L48, a=0.12 fm", 2: "L64, a=0.09 fm"}
COLS = ["#964a8b", "#e42536", "#f89c20", "#7a21dd", "#9c9ca1"]
W = dict(lambda2_nu=(0.15, 0.1), lambda4_nu=(0.0, 0.5))


def cs_point(path, covpath):
    fr = io_tools.get_fitresult(path, None)
    h = fr["parms"].get()
    nm = [str(n) for n in h.axes[0]]
    x = np.asarray(h.values(), float)
    names = [n for n in ("lambda2_nu", "lambda4_nu") if n in nm]
    ph = {n: W[n][0] + W[n][1] * x[nm.index(n)] for n in names}
    ph.setdefault("lambda4_nu", 0.0)
    frc = io_tools.get_fitresult(covpath, None) if covpath else fr
    hc = frc["parms"].get()
    nmc = [str(n) for n in hc.axes[0]]
    cov = np.asarray(frc["cov"].get().values(), float)
    idx = [nmc.index(n) for n in names]
    w = np.array([W[n][1] for n in names])
    return ph, names, cov[np.ix_(idx, idx)] * np.outer(w, w)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fits", nargs="+")
    ap.add_argument("--ntoys", type=int, default=2000)
    ap.add_argument("--basename", default="kernel_space_T8")
    args = ap.parse_args()
    B = np.load(f"{KFDIR}/bands.npz")
    Z = np.load(f"{KFDIR}/bands_l4zero.npz")
    J = json.load(open(f"{KFDIR}/fit_l4zero.json"))
    D = KF.load_data()
    bg, pert = B["bgrid"], B["pert_nf5"]
    k1z = J["fits"]["L4=0 | linf=2 | k1 [nominal]"]["x"]["k1"]
    Lz = J["lambda2_nu"]
    rng = np.random.default_rng(1)
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
        bg, tb[0] + pert, tb[2] + pert, color="#5790fc", alpha=0.15, lw=0, zorder=2
    )
    ax.plot(
        bg,
        zb[2] + pert,
        color="#5790fc",
        lw=2,
        label=r"lattice fit, $\lambda_4^\nu$=0 (NOMSTIFF's 1D term): $\lambda_2^\nu$=%.3f$\pm$%.3f (tot)"
        % (Lz["central"], Lz["tot"]),
    )
    b2 = B["lat_B_linf2_np"]
    ax.fill_between(
        bg,
        b2[1] + pert,
        b2[3] + pert,
        facecolor="none",
        edgecolor="#3f90da",
        hatch="///",
        lw=0,
        zorder=2,
    )
    ax.plot(
        bg,
        b2[2] + pert,
        color="#3f90da",
        lw=1.2,
        ls="--",
        label=r"lattice fit, free $\lambda_2^\nu,\lambda_4^\nu$ (the 2D term; stat MCMC 68%)",
    )
    for i, spec in enumerate(args.fits):
        lab, rest = spec.split("=", 1)
        path, _, covp = rest.partition(":")
        ph, names, cov = cs_point(path, covp or None)
        mu = np.array([ph[n] for n in names])
        X = (
            mu
            + rng.standard_normal((args.ntoys, len(names)))
            @ np.linalg.cholesky(cov + 1e-30 * np.eye(len(names))).T
        )
        curves = []
        for xx in X:
            d = dict(ph)
            d.update(dict(zip(names, xx)))
            curves.append(KF.np_zeta(bg, 2.0, d["lambda2_nu"], d["lambda4_nu"]))
        lo, hi = np.percentile(np.array(curves), [16, 84], axis=0)
        col = COLS[i % len(COLS)]
        ax.fill_between(bg, lo + pert, hi + pert, color=col, alpha=0.25, lw=0, zorder=3)
        ax.plot(
            bg,
            pert + KF.np_zeta(bg, 2.0, ph["lambda2_nu"], ph["lambda4_nu"]),
            color=col,
            lw=2,
            zorder=4,
            label=r"%s: $\lambda_2^\nu$=%.4f, $\lambda_4^\nu$=%.4f"
            % (lab, ph["lambda2_nu"], ph["lambda4_nu"]),
        )
        print(f"[kernel] {lab}: {ph}  sigma {np.sqrt(np.diag(cov))}")
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
    ax.legend(loc="lower left", ncol=1, fontsize=9, frameon=False)
    ax.text(
        0.98,
        0.97,
        "tanh_2, $\\lambda_\\infty^\\nu$=2 frozen\npoints shifted by $\\hat k_1$=%.2f ($\\lambda_4^\\nu$=0 lattice fit)\n"
        "postfit bands: 68%% from postfit CS cov." % k1z,
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=10,
    )
    plot_tools.add_cms_decor(ax, "Preliminary", loc=0, data=True, no_energy=True)
    save_plot(
        C.TASK,
        args.basename,
        fig=fig,
        args=args,
        meta_info=dict(note="alphaS blinded; not read"),
    )
    plt.close(fig)


if __name__ == "__main__":
    main()
