#!/usr/bin/env python3
"""Kernel-space plot: full CS kernel gamma_zeta(b_T, mu = 2 GeV) = SCETlib pert (n_f = 5) + 1/2 gamma_nu^NP(postfit) for
NOMSTIFF and the exact-lattice fit(s), against the ASWZ per-ensemble points. Adapted from
walled-multistart-census/261006-t8-l4nu-lattice2d/scripts/kernel_plot.py (itself section 1 of
260923-lattice-fits/scripts/postfit_plots.py), re-pointed at this task dir.
Points are shown minus k1_hat * a/b_T, with k1_hat the analytic profile of the exact term (syst=J) at the FIRST
non-reference fit's CS point (so they are what that fit is compared to); the k1 uncertainty is not in the error bars.
Postfit bands: 16-84 % of Gaussian toys from each fit's (lambda2_nu[, lambda4_nu]) covariance, theta -> physical.
Usage: kernel_plot.py LABEL=fitresult ...   (alphaS is never read)"""
import argparse
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from rabbit import io_tools  # noqa: E402
from wums import plot_tools  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import lattice_cs_chi2 as L  # noqa: E402
from plot_output import save_plot  # noqa: E402

KFDIR = os.path.join(os.path.dirname(TASK), "260923-scetlib-kernel-fit")
sys.path.insert(0, KFDIR)
import kernel_fit as KF  # noqa: E402

ENS_COL = {0: "#3f90da", 1: "#ffa90e", 2: "#bd1f01"}
ENS_LAB = {0: "L32, a=0.15 fm", 1: "L48, a=0.12 fm", 2: "L64, a=0.09 fm"}
COLS = ["#964a8b", "#e42536", "#f89c20", "#7a21dd", "#9c9ca1"]
W = dict(lambda2_nu=(0.15, 0.1), lambda4_nu=(0.0, 0.5))


def cs_point(path):
    fr = io_tools.get_fitresult(path, None)
    h = fr["parms"].get()
    nm = [str(n) for n in h.axes[0]]
    x = np.asarray(h.values(), float)
    names = [n for n in ("lambda2_nu", "lambda4_nu") if n in nm]
    ph = {n: W[n][0] + W[n][1] * x[nm.index(n)] for n in names}
    ph.setdefault("lambda4_nu", 0.0)
    cov = np.asarray(fr["cov"].get().values(), float)
    idx = [nm.index(n) for n in names]
    w = np.array([W[n][1] for n in names])
    return ph, names, cov[np.ix_(idx, idx)] * np.outer(w, w)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fits", nargs="+")
    ap.add_argument("--ntoys", type=int, default=2000)
    ap.add_argument("--basename", default="kernel_space_LATCHI8")
    args = ap.parse_args()
    B = np.load(f"{KFDIR}/bands.npz")
    D = KF.load_data()
    bg, pert = B["bgrid"], B["pert_nf5"]
    core = L.LatticeCSCore(syst="J")
    res, lmin = core.fit()
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
        pert + KF.np_zeta(bg, 2.0, lmin["lambda2_nu"], lmin["lambda4_nu"]),
        color="#3f90da",
        lw=1.2,
        ls="--",
        label=r"lattice-only best fit: $\lambda_2^\nu$=%.3f, $\lambda_4^\nu$=%.4f (band: stat MCMC 68%%)"
        % (lmin["lambda2_nu"], lmin["lambda4_nu"]),
    )
    k1 = None
    for i, spec in enumerate(args.fits):
        lab, path = spec.split("=", 1)
        ph, names, cov = cs_point(path)
        lam = dict(lambda_inf_nu=2.0, **ph)
        if k1 is None and i > 0:
            k1 = core.k1hat(lam)
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
        dchi = core.chi2(lam) - res.fun
        ax.plot(
            bg,
            pert + KF.np_zeta(bg, 2.0, ph["lambda2_nu"], ph["lambda4_nu"]),
            color=col,
            lw=2,
            zorder=4,
            label=r"%s: $\lambda_2^\nu$=%.4f, $\lambda_4^\nu$=%.4f, $\Delta\chi^2_\mathrm{lat}$=%.1f"
            % (lab, ph["lambda2_nu"], ph["lambda4_nu"], dchi),
        )
        print(
            f"[kernel] {lab}: {ph}  sigma {np.sqrt(np.diag(cov))}  dchi2_lat(exact, J) {dchi:.2f}  k1hat {core.k1hat(lam):.3f}"
        )
    k1 = core.k1hat(lmin) if k1 is None else k1
    dx = {0: -0.006, 1: 0.0, 2: 0.006}
    for e in range(3):
        m = D["ens"] == e
        ax.errorbar(
            D["b"][m] + dx[e],
            D["y"][m] - k1 * D["a"][m] / D["b"][m],
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
        "tanh_2, $\\lambda_\\infty^\\nu$=2 frozen, $n_f$=5 pert.\npoints shifted by $\\hat k_1$=%.2f "
        "(exact term at the fit's CS point)\npostfit bands: 68%% from postfit CS cov."
        % k1,
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=10,
    )
    plot_tools.add_cms_decor(ax, "Preliminary", loc=0, data=True, no_energy=True)
    save_plot(
        TASK,
        args.basename,
        fig=fig,
        args=args,
        meta_info=dict(note="alphaS blinded; not read"),
    )
    plt.close(fig)


if __name__ == "__main__":
    main()
