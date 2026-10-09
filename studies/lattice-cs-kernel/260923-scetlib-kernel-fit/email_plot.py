"""2026-09-24: one clean comparison figure for the email to the lattice authors (Luca).

  gamma(b_T, mu = 2 GeV) vs b_T, one panel, plain label (no CMS logo).
  1. ASWZ per-ensemble points minus k1*a/b_T with THEIR fit's k1: the (c0,k1) reproduction in
     ../260923-lattice-data-refit/cs_fit.py (d_n index fix of 2026-09-24).
  2. Their Eq. (6)-(8) at a = 0 (B_NP = 2 GeV^-1), 1 sigma band from our (c0,k1) covariance, plus
     the paper-quoted sigma(c0) = 0.012 band (dotted).
  3. Our SCETlib tanh_2 kernel (n_f = 5, N3LL, alpha_s(mZ) = 0.118, fit mu0 floor + sextic b*)
     at the lambda4_nu = 0 fit (l4zero.py): lambda_inf_nu = 2, lambda2_nu +- stat+syst; the
     free-(lambda2_nu, lambda4_nu) fit as a thin dashed line.
Run in the container, scetlib-np-param-model worktree first on PYTHONPATH (for save_plot).
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

from wremnants.postprocessing.scetlib_np.plot_output import save_plot  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kernel_fit as KF  # noqa: E402

CSF = KF.CSF  # ../260923-lattice-data-refit/cs_fit.py, imported, not re-derived
ENS_COL = {0: "#3f90da", 1: "#ffa90e", 2: "#bd1f01"}
ENS_MK = {0: "o", 1: "s", 2: "^"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quoted-sigma-c0", type=float, default=0.012)
    args = ap.parse_args()
    plt.rcParams.update({"axes.labelsize": 22, "legend.fontsize": 12})

    ens, D = CSF.load()
    b, y, a, cov, s = D["b"], D["y"], D["a"], D["cov"], D["s"]
    theirs = CSF.fit(y, cov, b, a, ["c0", "k1"], BNP=2.0, mode="numeric")
    c0, k1, sc0 = theirs["theta"]["c0"], theirs["theta"]["k1"], theirs["err"]["c0"]
    print(
        f"their (c0,k1) reproduction: c0={c0:.4f}({sc0:.4f}) k1={k1:.4f}({theirs['err']['k1']:.4f}) "
        f"chi2={theirs['chi2']:.2f}/{theirs['ndf']}"
    )

    bb = np.linspace(0.03, 1.0, 195)
    off, cols = CSF.design(bb, np.zeros_like(bb), 2.0, "numeric")
    g_th = off + c0 * cols["c0"]
    # at a=0 only c0 enters -> the (c0,k1) 1-sigma band is |dgamma/dc0| * sigma(c0) (k1 marginalised)
    s_th = np.abs(cols["c0"]) * sc0
    s_q = np.abs(cols["c0"]) * args.quoted_sigma_c0

    Z = json.load(open(os.path.join(HERE, "fit_l4zero.json")))
    L = Z["lambda2_nu"]
    k1_ours = Z["fits"]["L4=0 | linf=2 | k1 [nominal]"]["x"]["k1"]
    free2 = json.load(open(os.path.join(HERE, "fit_results.json")))[
        "tanh2 | linf=2 | k1"
    ]["x"]
    pert = KF.K.our_cs_kernel(bb, {"lambda_inf_nu": 0.0}, mu=2.0, scheme="fit")
    g_us = pert + KF.np_zeta(bb, 2.0, L["central"], 0.0)
    g_lo = pert + KF.np_zeta(bb, 2.0, L["central"] - L["tot"], 0.0)
    g_hi = pert + KF.np_zeta(bb, 2.0, L["central"] + L["tot"], 0.0)
    g_free = pert + KF.np_zeta(bb, 2.0, free2["l2"], free2["l4"])

    fig, ax = plot_tools.figure(
        bb,
        r"$b_T$ [fm]",
        r"$\gamma_q(b_T,\mu=2\,\mathrm{GeV})$",
        ylim=(-2.0, 1.0),
        xlim=(0.0, 1.0),
        automatic_scale=False,
        width_scale=1.3,
    )
    ax.fill_between(
        bb, g_th - s_th, g_th + s_th, color="0.55", alpha=0.35, lw=0, zorder=1
    )
    ax.plot(
        bb,
        g_th,
        color="0.2",
        lw=2,
        label=rf"ASWZ Eq. (6)-(8), $a$=0, $B_{{NP}}$=2 GeV$^{{-1}}$: $c_0$={c0:.4f}$\pm${sc0:.4f} (our refit)",
    )
    ax.plot(bb, g_th - s_q, color="0.2", lw=1.2, ls=":")
    ax.plot(
        bb,
        g_th + s_q,
        color="0.2",
        lw=1.2,
        ls=":",
        label=rf"same, paper-quoted $\sigma(c_0)$={args.quoted_sigma_c0}",
    )
    ax.fill_between(bb, g_lo, g_hi, color="#e42536", alpha=0.25, lw=0, zorder=2)
    ax.plot(
        bb,
        g_us,
        color="#e42536",
        lw=2.2,
        zorder=3,
        label=(
            r"SCETlib tanh$_2$ ($n_f$=5): $\lambda_\infty^\nu$=2, $\lambda_4^\nu$=0, "
            rf"$\lambda_2^\nu$={L['central']:.3f}$\pm${L['tot']:.3f} GeV$^2$ (own $k_1$={k1_ours:.2f})"
        ),
    )
    ax.plot(
        bb,
        g_free,
        color="#e42536",
        lw=1.0,
        ls="--",
        zorder=3,
        label=rf"SCETlib, free $\lambda_2^\nu$={free2['l2']:.3f}, $\lambda_4^\nu$={free2['l4']:.4f}",
    )
    names = {0: "a=0.15 fm (L32)", 1: "a=0.12 fm (L48)", 2: "a=0.09 fm (L64)"}
    dx = {0: -0.006, 1: 0.0, 2: 0.006}
    for e in range(3):
        m = D["ens"] == e
        ax.errorbar(
            b[m] + dx[e],
            y[m] - k1 * a[m] / b[m],
            s[m],
            fmt=ENS_MK[e],
            ms=6,
            color=ENS_COL[e],
            zorder=5,
            label=rf"ASWZ lattice, {names[e]}, $-k_1 a/b_T$ with $k_1$={k1:.3f} (ASWZ fit)",
        )
    ax.axhline(0, color="0.7", lw=0.8)
    ax.legend(loc="lower left", fontsize=10.5, frameon=False)
    ax.text(
        0.0,
        1.01,
        r"MS-bar, $\mu$ = 2 GeV; lattice errors: diagonal of per-ensemble cov.",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=13,
    )
    meta = dict(
        theirs=f"cs_fit.fit c0,k1 B_NP=2 numeric: c0={c0} sc0={sc0} k1={k1}",
        ours=f"l4zero nominal lambda2_nu={L['central']} tot={L['tot']} k1={k1_ours}; nf=5 N3LL as=0.118",
        data="/work/submit/lavezzo/cs_kernel/CS_lattice_results.tar",
    )
    save_plot(HERE, "email_lattice_comparison", fig=fig, args=args, meta_info=meta)
    plt.close(fig)


if __name__ == "__main__":
    main()
