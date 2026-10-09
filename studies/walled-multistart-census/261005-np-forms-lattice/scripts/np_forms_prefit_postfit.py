#!/usr/bin/env python3
"""NP functions for the nominal lattice configuration: lattice-constrained prefit vs the walled warm postfits.

Prefit  : CS kernel from the lattice constraint the card carries (lambda2_nu = 0.1345 +- 0.031, lambda4_nu = 0,
          lambda_inf_nu = 2); TMD F_eff at the card anchor (lambda2 = lambda4 = 0.4, delta_lambda2 = 0).
Postfit : NOMSTIFF (wall margin 0, tau 8; the nominal) with a 68 % band from Gaussian draws of the fitted NP lambdas
          using its Hessian covariance, and LATL4ZY35WALLWARM (margin 5e-3, tau 5) as a line.
Physical lambdas and covariance come from dump_np_cov.py (np_lambdas_cov.json).
Curves use the plotter's own form functions (np_function_plots -> btgrid_tf tanh_2), as in
walled-two-minima/260930-np-forms. gamma_nu is SCETlib's convention, gamma_nu = 2 * gamma_zeta (AN eq:npgamma).
"""
import argparse
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import wums.plot_tools  # noqa: F401,E402

from wremnants.postprocessing.scetlib_np import np_function_plots as NPF  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_output import save_plot  # noqa: E402

LATT = dict(l2nu=0.134549, sig=0.031275)
ANCHOR = dict(lambda2=0.4, lambda4=0.4, delta_lambda2=0.0)
YS = (0.0, 1.0, 2.0, 2.5)
C_PRE, C_NOM, C_OLD = "0.35", "#1f6f8b", "#c0582b"


def gnu(l2nu):
    return dict(
        lambda_inf_nu=2.0, lambda2_nu=l2nu, lambda4_nu=0.0, np_model_nu="tanh_2"
    )


def eff(l2, l4, dl2):
    return dict(
        lambda_inf=1.0, lambda2=l2, lambda4=l4, delta_lambda2=dl2, np_model="tanh_2"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    ap.add_argument("-o", "--outdir", required=True)
    ap.add_argument("--bT-max", type=float, default=4.0)
    ap.add_argument("--ndraw", type=int, default=2000)
    a = ap.parse_args()
    d = json.load(open(a.json))
    nom, old = d["NOMSTIFF"], d["LATWARM"]
    names = nom["names"]
    mu = dict(zip(names, nom["mu"]))
    muo = dict(zip(names, old["mu"]))
    rng = np.random.default_rng(20261005)
    draws = rng.multivariate_normal(
        np.array(nom["mu"]), np.array(nom["cov"]), size=a.ndraw
    )
    D = {n: draws[:, i] for i, n in enumerate(names)}
    bT = np.linspace(1e-4, a.bT_max, 400)
    caveat = (
        "Real data, nominal: card A + lattice, $\\lambda_4^\\nu$=0, new cache, wall margin 0, $\\tau$=8.\n"
        "Postfit band: Gaussian draws from the walled Hessian (the active wall face makes it one-sided in reality)."
    )

    # ---------------- CS kernel ----------------
    fig, (ax, rx) = plt.subplots(
        2,
        1,
        figsize=(7.5, 7.5),
        sharex=True,
        gridspec_kw=dict(height_ratios=[3, 1.3], hspace=0.05),
    )
    pre = NPF.gamma_nu_curve(bT, gnu(LATT["l2nu"]))
    lo = NPF.gamma_nu_curve(bT, gnu(LATT["l2nu"] - LATT["sig"]))
    hi = NPF.gamma_nu_curve(bT, gnu(LATT["l2nu"] + LATT["sig"]))
    ax.fill_between(
        bT, np.minimum(lo, hi), np.maximum(lo, hi), color=C_PRE, alpha=0.18, lw=0
    )
    ax.plot(
        bT,
        pre,
        color=C_PRE,
        ls="--",
        lw=1.8,
        label=r"prefit: lattice constraint ($\lambda_2^\nu$ = 0.135 $\pm$ 0.031, $\lambda_4^\nu$ = 0)",
    )
    G = np.array([NPF.gamma_nu_curve(bT, gnu(x)) for x in D["lambda2_nu"]])
    g16, g50, g84 = np.percentile(G, [16, 50, 84], axis=0)
    post = NPF.gamma_nu_curve(bT, gnu(mu["lambda2_nu"]))
    ax.fill_between(bT, g16, g84, color=C_NOM, alpha=0.25, lw=0)
    ax.plot(
        bT,
        post,
        color=C_NOM,
        lw=2.2,
        label=rf"postfit NOMSTIFF ($\lambda_2^\nu$ = {mu['lambda2_nu']:.4f} $\pm$ {np.sqrt(np.array(nom['cov'])[3, 3]):.4f})",
    )
    ax.plot(
        bT,
        NPF.gamma_nu_curve(bT, gnu(muo["lambda2_nu"])),
        color=C_OLD,
        lw=1.5,
        ls="-.",
        label=rf"postfit LATL4ZY35WALLWARM (margin 5e-3, $\tau$=5; $\lambda_2^\nu$ = {muo['lambda2_nu']:.4f})",
    )
    ax.set_ylabel(r"$\gamma_\nu^{\rm NP}(b_T)$  ($=2\,\tilde\gamma_\zeta$)")
    ax.set_ylim(-2.1, 0.15)
    ax.legend(loc="lower left", fontsize=10, frameon=False)
    ax.text(
        0.98,
        0.97,
        caveat,
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=8,
        color="0.3",
    )
    rx.axhline(0, color="0.5", lw=1)
    rx.fill_between(bT, g16 - pre, g84 - pre, color=C_NOM, alpha=0.25, lw=0)
    rx.plot(bT, post - pre, color=C_NOM, lw=2.2)
    rx.set_ylabel("postfit $-$ prefit")
    rx.set_xlabel(r"$b_T$ [GeV$^{-1}$]")
    save_plot(
        a.outdir,
        "gamma_nu_prefit_postfit",
        fig=fig,
        args=a,
        meta_info={"mu_nom": mu, "mu_latwarm": muo, "lattice": LATT},
    )
    plt.close(fig)

    # ---------------- TMD F_eff ----------------
    fig, axes = plt.subplots(1, len(YS), figsize=(4.2 * len(YS), 4.8), sharey=True)
    for ax, y in zip(axes, YS):
        ax.plot(
            bT,
            NPF.f_eff_curve(
                bT,
                y,
                eff(ANCHOR["lambda2"], ANCHOR["lambda4"], ANCHOR["delta_lambda2"]),
            ),
            color=C_PRE,
            ls="--",
            lw=1.8,
            label=r"prefit: card anchor ($\lambda_2$ = $\lambda_4$ = 0.4, $\delta\lambda_2$ = 0)",
        )
        F = np.array(
            [
                NPF.f_eff_curve(bT, y, eff(l2, l4, dl2))
                for l2, l4, dl2 in zip(D["lambda2"], D["lambda4"], D["delta_lambda2"])
            ]
        )
        f16, f84 = np.percentile(F, [16, 84], axis=0)
        ax.fill_between(bT, f16, f84, color=C_NOM, alpha=0.25, lw=0)
        ax.plot(
            bT,
            NPF.f_eff_curve(
                bT, y, eff(mu["lambda2"], mu["lambda4"], mu["delta_lambda2"])
            ),
            color=C_NOM,
            lw=2.2,
            label="postfit NOMSTIFF (68 % band)",
        )
        ax.plot(
            bT,
            NPF.f_eff_curve(
                bT, y, eff(muo["lambda2"], muo["lambda4"], muo["delta_lambda2"])
            ),
            color=C_OLD,
            lw=1.5,
            ls="-.",
            label="postfit LATL4ZY35WALLWARM",
        )
        ax.set_yscale("log")
        ax.set_ylim(1e-4, 1.5)
        ax.set_title(rf"$|Y|$ = {y:g}", fontsize=12)
        ax.set_xlabel(r"$b_T$ [GeV$^{-1}$]")
    axes[0].set_ylabel(r"$F_{\rm eff}(b_T, Y)$")
    axes[0].legend(loc="lower left", fontsize=9, frameon=False)
    fig.suptitle(
        "TMD form factor, lattice-constrained nominal fit. " + caveat.split("\n")[0],
        fontsize=10,
    )
    save_plot(
        a.outdir,
        "F_eff_prefit_postfit",
        fig=fig,
        args=a,
        meta_info={"mu_nom": mu, "mu_latwarm": muo},
    )
    plt.close(fig)


if __name__ == "__main__":
    main()
