#!/usr/bin/env python3
"""Stage 2 of the headline NP-function figures (261008-np-function-figures): draws from ../np_figs_data.npz
(written by compute.py; SCETlib kernel, lattice term, fit lambdas). No SCETlib, no fitresult access here.

Run in the container with the scetlib-np-param-model worktree first on PYTHONPATH (np_function_plots, btgrid_tf,
plot_output live only there):
  PYTHONPATH=/home/submit/lavezzo/alphaS/WRemnants-scetlib-np-param-model:$PYTHONPATH python3 plot.py

Reused: wums.plot_tools.figure / figureWithRatio / add_cms_decor (frames + CMS label), scetlib_np.plot_output.save_plot
(png + pdf + .log + index.php), scetlib_np.np_function_plots.{gamma_nu_curve, f_eff_curve, map22_F_eff, _band}
(the fit's own tanh_2 forms through btgrid_tf, the MAP22 reference) and params.NPTune (form/lambda validation).
The curves are function evaluations, not histograms, so they are drawn on the wums frames with matplotlib
(makePlotWithRatioToRef has no notion of a function band).

Figures
  1  cs_kernel_vs_lattice       gamma_zeta(b_T, 2 GeV) vs the 21 ASWZ points, lattice range, pulls panel
  1b cs_kernel_full_range       same curves out to b_T = 2.6 fm with the lattice range shaded
  2  np_functions               gamma_zeta^NP, CS factor at m_Z, F_NP(b_T, Y), total NP factor (2x2)
  3  lambda_nu_plane            (lambda2_nu, lambda4_nu) 68/95 % contours, physical region, PG tension
"""
import argparse
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from wums import plot_tools  # noqa: E402  (import at top: styles every figure the same)

from wremnants.postprocessing.scetlib_np import np_function_plots as NPF  # noqa: E402
from wremnants.postprocessing.scetlib_np.params import NPTune  # noqa: E402
from wremnants.postprocessing.scetlib_np.plot_output import save_plot  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
D = np.load(os.path.join(TASK, "np_figs_data.npz"))
J = json.load(open(os.path.join(TASK, "np_figs_data.json")))
FM = float(D["fm_to_gevinv"])
K1 = float(D["k1hat"])
MZ = 91.1876
B0 = 2.0 * np.exp(-np.euler_gamma)

COL = {
    "lattice": "#5790fc",
    "LATFROZ_V3": "#e42536",
    "XWSTIFF": "#f89c20",
    "NOMSTIFF": "#964a8b",
    "pert": "#717581",
}
LAB = {
    "lattice": "Lattice only (ASWZ)",
    "LATFROZ_V3": "Z + lattice (LATFROZ V3)",
    "XWSTIFF": "Z only (XWSTIFF), central",
    "NOMSTIFF": r"Z + 1D lattice prior, $\lambda_4^\nu$=0 (NOMSTIFF)",
}
ENS = {0: ("o", "a = 0.15 fm"), 1: ("s", "a = 0.12 fm"), 2: ("^", "a = 0.09 fm")}
ENS_C = {0: "0.05", 1: "0.30", 2: "0.55"}
META = dict(
    data="np_figs_data.npz from compute.py (SCETlib DrellYan.gamma_nu_points, gamma-nu-points build)",
    kernel="gamma_zeta = gamma_nu/2 at mu=2 GeV; pert part frozen at alpha_s(mZ)=0.1168, TNPs=0 (LATFROZ reference)",
    lattice_term="LatticeCSNativeCore syst=Jnf nfmatch=4.18 nfscheme=full (V3), k1 profiled",
    fits=json.dumps({k: v.get("path") for k, v in J["fits"].items() if k != "lattice"}),
)


def lbl_fit(k, oneline=False):
    f = J["fits"][k]
    c = rf"$\chi^2_{{\rm lat}}$ = {f['chi2_lat']:.1f}"
    return LAB[k] + (", " if oneline else "\n  ") + c


# ------------------------------------------------------------------------------------------- figure 1
def kernel_curves(ax, tag, nom=True, oneline=False):
    b = D[f"b_{tag}"]
    ax.plot(
        b,
        D[f"pert_{tag}"],
        color=COL["pert"],
        ls=":",
        lw=1.6,
        label=r"pert. only ($\lambda_2^\nu=\lambda_4^\nu=0$)",
    )
    for k, ls in (("lattice", "-"), ("LATFROZ_V3", "-")):
        ax.fill_between(
            b,
            D[f"{k}_{tag}_lo"],
            D[f"{k}_{tag}_hi"],
            color=COL[k],
            alpha=0.30,
            lw=0,
            zorder=2,
        )
        ax.plot(
            b,
            D[f"{k}_{tag}_c"],
            color=COL[k],
            lw=2.4,
            ls=ls,
            zorder=3,
            label=lbl_fit(k, oneline),
        )
    if nom:
        k = "NOMSTIFF"
        ax.fill_between(
            b,
            D[f"{k}_{tag}_lo"],
            D[f"{k}_{tag}_hi"],
            facecolor="none",
            edgecolor=COL[k],
            hatch="////",
            lw=0,
            alpha=0.55,
            zorder=2,
        )
        ax.plot(
            b,
            D[f"{k}_{tag}_c"],
            color=COL[k],
            lw=2.0,
            ls="-.",
            zorder=3,
            label=lbl_fit(k, oneline),
        )
    k = "XWSTIFF"
    ax.plot(
        b,
        D[f"{k}_{tag}_c"],
        color=COL[k],
        lw=2.6,
        ls="--",
        zorder=4,
        label=lbl_fit(k, oneline),
    )


def data_points(ax, k1=K1, label=True):
    dx = {0: -0.007, 1: 0.0, 2: 0.007}
    s = np.sqrt(np.diag(D["data_cov"]))
    for e in range(3):
        m = D["data_ens"] == e
        ax.errorbar(
            D["data_b"][m] + dx[e],
            D["data_y"][m] - k1 * D["data_a"][m] / D["data_b"][m],
            s[m],
            fmt=ENS[e][0],
            ms=7,
            color=ENS_C[e],
            mfc=ENS_C[e],
            capsize=0,
            elinewidth=1.4,
            zorder=6,
            label=("ASWZ, " + ENS[e][1]) if label else None,
        )


def pulls(ax, k):
    """(y - k1hat_own a/b - model)/sigma_stat, k1 profiled at THIS curve's lambdas (as in its chi2)."""
    f = J["fits"][k]
    s = np.sqrt(np.diag(D["data_cov"]))
    r = (D["data_y"] - f["k1hat_own"] * D["data_a"] / D["data_b"] - D[f"{k}_pts"]) / s
    return r


NOTE = (
    r"points: raw $-\,\hat k_1 a/b_T$, $\hat k_1$ = %.3f (lattice-only optimum); $\chi^2_{\rm lat}$: 21 pts, "
    r"own $\hat k_1$"
    "\n"
    r"all curves: pert. part frozen at $\alpha_s(m_Z)$ = 0.1168, TNPs = 0; only $(\lambda_2^\nu, \lambda_4^\nu)$ "
    r"differ; bands 68 %%" % K1
)


def split_legends(ax, pts_loc, curve_loc, curve_ncol, curve_anchor=None, fs=12.5):
    h, l = ax.get_legend_handles_labels()
    ip = [i for i, x in enumerate(l) if x.startswith("ASWZ")]
    ic = [i for i, x in enumerate(l) if not x.startswith("ASWZ")]
    leg = None
    if ip:
        leg = ax.legend(
            [h[i] for i in ip],
            [l[i] for i in ip],
            loc=pts_loc,
            fontsize=fs,
            frameon=False,
        )
        ax.add_artist(leg)
    kw = dict(bbox_to_anchor=curve_anchor) if curve_anchor else {}
    ax.legend(
        [h[i] for i in ic],
        [l[i] for i in ic],
        loc=curve_loc,
        fontsize=fs,
        ncol=curve_ncol,
        frameon=False,
        handlelength=2.6,
        columnspacing=1.2,
        **kw,
    )


def fig1(args):
    tag = "lat"
    import hist

    href = hist.Hist(
        hist.axis.Regular(100, 0.0, 1.0, name="bT")
    )  # frame only (figureWithRatio needs a hist)
    fig, ax, rax = plot_tools.figureWithRatio(
        href,
        r"$b_T$ [fm]",
        r"$\gamma_\zeta(b_T,\ \mu = 2\ \mathrm{GeV})$",
        ylim=(-2.15, 2.0),
        rlabel=r"Pull",
        rrange=(-3.5, 3.5),
        xlim=(0.0, 1.0),
        automatic_scale=False,
        width_scale=1.5,
        subplotsizes=[5, 2],
    )
    rax = rax[0] if isinstance(rax, (list, tuple)) else rax
    ax.tick_params(labelbottom=False)  # shared x: labels only on the pull panel
    ax.set_xlabel("")
    kernel_curves(ax, tag, oneline=True)
    data_points(ax)
    ax.axhline(0, color="0.7", lw=0.8, zorder=0)
    split_legends(ax, "lower left", "upper left", 2, curve_anchor=(0.0, 0.86), fs=12.5)
    ax.text(0.01, 0.985, NOTE, transform=ax.transAxes, ha="left", va="top", fontsize=12)
    plot_tools.add_cms_decor(ax, "Preliminary", loc=0, data=True, no_energy=True)
    rax.axhline(0, color="0.5", lw=1)
    for v in (-2, 2):
        rax.axhline(v, color="0.75", lw=0.8, ls=":")
    for k, off, mk in (("lattice", -0.008, "o"), ("LATFROZ_V3", +0.008, "D")):
        p = pulls(ax, k)
        rax.plot(
            D["data_b"] + off,
            p,
            mk,
            color=COL[k],
            ms=6,
            mfc=COL[k] if k == "lattice" else "white",
            mew=1.6,
            label={"lattice": "vs lattice only", "LATFROZ_V3": "vs Z + lattice"}[k],
        )
    rax.legend(loc="upper left", ncol=2, fontsize=11.5, frameon=False)
    rax.text(
        0.99,
        0.04,
        r"pull = (point $-$ curve)/$\sigma_{\rm stat}$ (diag.; points correlated), own $\hat k_1$ per curve",
        transform=rax.transAxes,
        ha="right",
        va="bottom",
        fontsize=10.5,
    )
    save_plot(TASK, "cs_kernel_vs_lattice", fig=fig, args=args, meta_info=META)
    plt.close(fig)

    # ---- 1b full b_T range
    b = D["b_full"]
    fig, ax = plot_tools.figure(
        b,
        r"$b_T$ [fm]",
        r"$\gamma_\zeta(b_T,\ \mu = 2\ \mathrm{GeV})$",
        ylim=(-2.75, 1.9),
        xlim=(0.0, 2.8),
        automatic_scale=False,
        width_scale=1.5,
    )
    bl = (D["data_b"].min(), D["data_b"].max())
    ax.axvspan(*bl, color="#5790fc", alpha=0.08, lw=0, zorder=0)
    ax.text(
        0.5 * sum(bl),
        1.12,
        "lattice\npoints",
        ha="center",
        va="top",
        fontsize=13,
        color="#3a6bc4",
    )
    kernel_curves(ax, "full", oneline=True)
    data_points(ax, label=False)
    bmax = float(D["bmax_fm"])
    ax.axvline(bmax, color="0.4", ls=(0, (2, 2)), lw=1.2)
    ax.text(
        bmax - 0.03,
        1.80,
        r"$b_T$ = 12.6 GeV$^{-1}$" + "\n(NP-wall $b_{\\max}$)",
        ha="right",
        va="top",
        fontsize=11.5,
        color="0.3",
    )
    ax.axhline(0, color="0.7", lw=0.8, zorder=0)
    l2, l4 = D["lam_lat"]
    bflip = np.sqrt(l2 / -l4) / FM if l4 < 0 else None
    if bflip:
        ax.annotate(
            r"lattice-only NP part changes sign"
            + "\n"
            + r"($\lambda_4^\nu<0$): $b_T$ = %.2f fm" % bflip,
            xy=(bflip, float(np.interp(bflip, b, D["lattice_full_c"]))),
            xytext=(1.2, 0.30),
            fontsize=11.5,
            arrowprops=dict(arrowstyle="->", color=COL["lattice"]),
            color="#3a6bc4",
        )
    ax.legend(
        loc="lower right",
        fontsize=12,
        ncol=1,
        frameon=False,
        handlelength=2.6,
        borderaxespad=0.3,
    )
    ax.text(
        0.01,
        0.985,
        NOTE.replace("; $\\chi^2_{\\rm lat}$: 21 pts, own $\\hat k_1$", ""),
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=11.5,
    )
    plot_tools.add_cms_decor(ax, "Preliminary", loc=0, data=True, no_energy=True)
    save_plot(TASK, "cs_kernel_full_range", fig=fig, args=args, meta_info=META)
    plt.close(fig)


# ------------------------------------------------------------------------------------------- figure 2
def tune_dict(k, toys=False):
    names = list(D[f"{k}_np_names"])
    held = dict(zip(list(D[f"{k}_np_held_names"]), D[f"{k}_np_held_vals"]))
    if toys:
        T = D[f"{k}_np_toys"]
        v = {n: T[:, i][:, None] for i, n in enumerate(names)}
        v.update({n: np.full((T.shape[0], 1), x) for n, x in held.items()})
    else:
        v = dict(zip(names, D[f"{k}_np_mu"]))
        v.update(held)
    return v


def np_set(k, toys=False):
    v = tune_dict(k, toys)
    if not toys:  # validate form + lambda set once through the registry
        NPTune.create("tanh_2", "tanh_2", values={n: v[n] for n in v})
    gnu = {n: v[n] for n in ("lambda_inf_nu", "lambda2_nu", "lambda4_nu")}
    gnu["np_model_nu"] = "tanh_2"
    eff = {n: v[n] for n in ("lambda_inf", "lambda2", "lambda4", "delta_lambda2")}
    eff["np_model"] = "tanh_2"
    return gnu, eff


def lattice_gnu(toys=False, n=2000):
    rng = np.random.default_rng(7)
    mu, C = D["lam_lat"], D["cov_lat"]
    if toys:
        d = rng.multivariate_normal(mu, C, size=n)
        return dict(
            lambda_inf_nu=np.full((n, 1), 2.0),
            lambda2_nu=d[:, :1],
            lambda4_nu=d[:, 1:],
            np_model_nu="tanh_2",
        )
    return dict(
        lambda_inf_nu=2.0, lambda2_nu=mu[0], lambda4_nu=mu[1], np_model_nu="tanh_2"
    )


def fig2(args):
    bT = np.linspace(1e-3, 12.6, 400)  # GeV^-1
    bcol = bT[None, :]
    L = np.log(MZ * bT / B0)  # canonical rapidity log, nu_B = m_Z, nu_S = b0/b_T
    Ys = (0.0, 2.5)
    fig, axs = plt.subplots(2, 2, figsize=(17, 13))
    (aG, aC), (aF, aT) = axs
    curves = {}
    for k in ("lattice", "LATFROZ_V3", "XWSTIFF"):
        if k == "lattice":
            g = lattice_gnu()
            gt = lattice_gnu(True)
            eff = efft = None
        else:
            g, eff = np_set(k)
            gt, efft = np_set(k, True)
        gz = 0.5 * NPF.gamma_nu_curve(bT, g)
        # cross-check: the NP part of SCETlib's own kernel (compute.py) == the fit's tanh_2 form here
        snp = np.interp(bT / FM, D["b_full"], D[f"{k}_np_full"])
        m = (bT / FM >= D["b_full"][0]) & (bT / FM <= D["b_full"][-1])
        dev = float(np.max(np.abs(snp[m] - gz[m])))
        assert dev < 2e-3, (
            k,
            dev,
        )  # interpolation of a 271-pt grid; the exact equality is checked in compute log
        band = k != "XWSTIFF"
        gzt = 0.5 * NPF.gamma_nu_curve(bcol, gt) if band else None
        cs = np.exp(2.0 * gz * L)
        cst = np.exp(2.0 * gzt * L[None, :]) if band else None
        curves[k] = dict(gz=gz, cs=cs)
        ls = "--" if k == "XWSTIFF" else "-"
        lab = LAB[k] if k != "XWSTIFF" else LAB[k] + " (no band)"
        for ax, c, ct in ((aG, gz, gzt), (aC, cs, cst)):
            if band:
                lo, hi = NPF._band(ct, (15.865, 84.135))
                ax.fill_between(bT, lo, hi, color=COL[k], alpha=0.28, lw=0)
            ax.plot(bT, c, color=COL[k], lw=2.4, ls=ls, label=lab)
        if eff is None:
            continue
        for yi, Y in enumerate(Ys):
            lsY = ls if yi == 0 else (":" if k == "XWSTIFF" else (0, (6, 1.5, 1, 1.5)))
            f = NPF.f_eff_curve(bT, Y, eff)
            ft = NPF.f_eff_curve(bcol, Y, efft) if band else None
            curves[k][f"F{Y}"] = f
            labY = (
                LAB[k].split(" (")[0] if k != "XWSTIFF" else "Z only (XWSTIFF)"
            ) + f", |Y| = {Y:g}"
            if band:
                lo, hi = NPF._band(ft, (15.865, 84.135))
                aF.fill_between(
                    bT, lo, hi, color=COL[k], alpha=0.22 if yi == 0 else 0.12, lw=0
                )
            aF.plot(bT, f, color=COL[k], lw=2.4 if yi == 0 else 1.9, ls=lsY, label=labY)
            if yi == 0:
                tot = f * cs
                curves[k]["tot"] = tot
                if band:
                    tott = ft * cst
                    lo, hi = NPF._band(tott, (15.865, 84.135))
                    aT.fill_between(bT, lo, hi, color=COL[k], alpha=0.28, lw=0)
                aT.plot(
                    bT,
                    tot,
                    color=COL[k],
                    lw=2.4,
                    ls=ls,
                    label=LAB[k].split(" (")[0] + (" (no band)" if not band else ""),
                )
    for yi, Y in enumerate(Ys):
        aF.plot(
            bT,
            NPF.map22_F_eff(bT, Y),
            color="0.35",
            lw=1.8,
            ls=(0, (1, 1.3)) if yi == 0 else (0, (3, 1, 1, 1, 1, 1)),
            label=f"MAP22 (N3LL, intrinsic), |Y| = {Y:g}",
        )
    blat = (D["data_b"].min() * FM, D["data_b"].max() * FM)
    for ax in (aG, aC):
        ax.axvspan(*blat, color="#5790fc", alpha=0.08, lw=0, zorder=0)
    aG.text(
        0.5 * sum(blat),
        -1.08,
        "lattice points",
        ha="center",
        va="bottom",
        fontsize=13,
        color="#3a6bc4",
    )
    aG.set_ylim(-1.15, 1.15)
    aG.axhline(0, color="0.6", lw=0.8)
    aG.set_ylabel(
        r"$\tilde\gamma_\zeta^{\rm NP}(b_T) = \frac{1}{2}\tilde\gamma_\nu^{\rm NP}(b_T)$"
    )
    aG.legend(
        loc="center right",
        fontsize=12.5,
        frameon=False,
        title=r"CS kernel, NP part ($\lambda_\infty^\nu$ = 2)",
        title_fontsize=13.5,
    )
    aC.set_ylim(0, 1.25)
    aC.set_ylabel(r"$\exp[\tilde\gamma_\nu^{\rm NP}(b_T)\,\ln(m_Z b_T/b_0)]$")
    aC.legend(
        loc="center right",
        fontsize=12.5,
        frameon=True,
        facecolor="white",
        edgecolor="0.7",
        framealpha=0.92,
        title="CS NP factor at $Q = m_Z$, canonical log\n"
        r"$\nu_B = m_Z$, $\nu_S = b_0/b_T$ (illustrative;"
        "\nnot SCETlib's profile scales)",
        title_fontsize=12.5,
    )
    aF.set_ylim(0, 1.25)
    aF.set_ylabel(r"$F^{\rm NP}(b_T, Y)$  (two-beam TMD NP factor)")
    aF.legend(loc="upper right", fontsize=12, frameon=False, ncol=1, handlelength=3.2)
    aF.text(
        0.98,
        0.33,
        "TMD NP boundary factor ($\\lambda_\\infty$ = 1 GeV)\n"
        "MAP22: evolution factor stripped,\n$x_{1,2} = (m_Z/\\sqrt{s})e^{\\pm Y}$, $\\sqrt{s}$ = 13 TeV",
        transform=aF.transAxes,
        ha="right",
        va="bottom",
        fontsize=12,
    )
    aT.set_ylim(0, 1.25)
    aT.set_ylabel(r"CS factor $\times$ $F^{\rm NP}(b_T, Y=0)$")
    aT.legend(
        loc="upper right",
        fontsize=13,
        frameon=False,
        title="total NP damping at $Q = m_Z$, $Y = 0$\n(canonical rapidity log as upper right)",
        title_fontsize=12.5,
    )
    aT.text(
        0.98,
        0.42,
        "Z + lattice and Z only give the same product:\nthe Z data fix CS $\\times$ TMD, the lattice\n"
        "moves damping from the TMD to the CS side",
        transform=aT.transAxes,
        ha="right",
        va="bottom",
        fontsize=12.5,
        color="0.2",
    )
    for ax in axs.flat:
        ax.set_xlim(0, 12.6)
        ax.set_xlabel(r"$b_T$ [GeV$^{-1}$]")
        plot_tools.add_cms_decor(ax, "Preliminary", loc=0, data=True, no_energy=True)
    fig.tight_layout()
    save_plot(TASK, "np_functions", fig=fig, args=args, meta_info=META)
    plt.close(fig)
    # numbers for the logbook
    out = {}
    for bq in (1.0, 2.0, 3.0, 4.0, 6.0):
        i = int(np.argmin(np.abs(bT - bq)))
        out[f"b={bq:g}"] = {
            k: {kk: float(vv[i]) for kk, vv in c.items()} for k, c in curves.items()
        }
    json.dump(out, open(os.path.join(TASK, "np_functions_values.json"), "w"), indent=1)


# ------------------------------------------------------------------------------------------- figure 3
def ellipse(mu, C, dchi2, n=400):
    t = np.linspace(0, 2 * np.pi, n)
    w, V = np.linalg.eigh(C)
    pts = V @ (
        np.sqrt(np.maximum(w, 0) * dchi2)[:, None] * np.vstack([np.cos(t), np.sin(t)])
    )
    return mu[0] + pts[0], mu[1] + pts[1]


def fig3(args):
    D68, D95 = 2.2977, 6.1801  # 2D 1 sigma / 2 sigma (68.27 / 95.45 %)
    l2g, l4g, S = D["l2g"], D["l4g"], D["dchi2_lat_grid"]
    fig, ax = plot_tools.figure(
        l2g,
        r"$\lambda_2^\nu$ [GeV$^2$]",
        r"$\lambda_4^\nu$ [GeV$^4$]",
        xlim=(-0.05, 0.33),
        ylim=(-0.022, 0.07),
        automatic_scale=False,
        width_scale=1.25,
    )
    # unphysical region (tanh_2 CS damping: lambda2_nu >= 0 and lambda4_nu >= 0)
    ax.fill_between(
        [-0.05, 0.0],
        -0.022,
        0.07,
        facecolor="0.88",
        edgecolor="0.6",
        hatch="\\\\",
        lw=0,
        zorder=0,
    )
    ax.fill_between(
        [0.0, 0.33],
        -0.022,
        0.0,
        facecolor="0.88",
        edgecolor="0.6",
        hatch="\\\\",
        lw=0,
        zorder=0,
    )
    ax.text(
        0.31,
        -0.0175,
        r"unphysical: $\lambda_4^\nu<0$ (anti-damping at large $b_T$)",
        ha="right",
        fontsize=12,
        color="0.3",
    )
    ax.text(
        -0.046,
        0.066,
        r"$\lambda_2^\nu<0$",
        ha="left",
        va="top",
        fontsize=12,
        color="0.3",
    )
    # lattice only: exact Delta chi2 (non-Gaussian) + its Gaussian ellipse
    ax.contourf(
        l2g, l4g, S, levels=[0, D68], colors=[COL["lattice"]], alpha=0.45, zorder=2
    )
    ax.contourf(
        l2g, l4g, S, levels=[D68, D95], colors=[COL["lattice"]], alpha=0.2, zorder=2
    )
    ax.contour(
        l2g,
        l4g,
        S,
        levels=[D68, D95],
        colors=[COL["lattice"]],
        linewidths=[2.0, 1.4],
        zorder=3,
    )
    for dc, lw in ((D68, 1.2), (D95, 1.0)):
        x, y = ellipse(D["lam_lat"], D["cov_lat"], dc)
        ax.plot(x, y, color="#2a4f9a", ls=":", lw=lw, zorder=3)
    ax.plot(*D["lam_lat"], "*", color=COL["lattice"], mec="k", ms=17, zorder=6)
    # joint
    k = "LATFROZ_V3"
    f = J["fits"][k]
    mu = np.array(f["lam_cs"])
    names = list(D[f"{k}_np_names"])
    ii = [names.index("lambda2_nu"), names.index("lambda4_nu")]
    C = D[f"{k}_np_cov"][np.ix_(ii, ii)]
    for dc, lw, a in ((D68, 2.2, 0.35), (D95, 1.5, 0.15)):
        x, y = ellipse(mu, C, dc)
        ax.fill(x, y, color=COL[k], alpha=a, lw=0, zorder=4)
        ax.plot(x, y, color=COL[k], lw=lw, zorder=4)
    ax.plot(*mu, "P", color=COL[k], mec="k", ms=14, zorder=6)
    # Z only: on the lambda2_nu = 0 face
    k = "XWSTIFF"
    f = J["fits"][k]
    mz = np.array(f["lam_cs"])
    names = list(D[f"{k}_np_names"])
    ii = [names.index("lambda2_nu"), names.index("lambda4_nu")]
    Cz = D[f"{k}_np_cov"][np.ix_(ii, ii)]
    x, y = ellipse(mz, Cz, D68)
    ax.plot(x, y, color=COL[k], lw=1.6, ls="--", zorder=5)
    ax.plot(max(mz[0], 0.0), mz[1], "o", color=COL[k], mec="k", ms=13, zorder=6)
    ax.annotate(
        "Z only (XWSTIFF): on the $\\lambda_2^\\nu = 0$ wall face;\n"
        "its walled Hessian (dashed sliver) is not a data constraint",
        xy=(0.0, mz[1]),
        xytext=(0.012, 0.060),
        fontsize=12,
        color="#b06d00",
        arrowprops=dict(arrowstyle="->", color=COL[k]),
    )
    # NOMSTIFF: lambda4_nu = 0 frozen, 1D
    k = "NOMSTIFF"
    f = J["fits"][k]
    ax.errorbar(
        f["lam_cs"][0],
        0.0,
        xerr=f["sigma_cs"][0],
        fmt="s",
        color=COL[k],
        mec="k",
        ms=10,
        capsize=4,
        lw=2,
        zorder=6,
    )
    # PG tension
    pg = json.load(
        open(os.path.join(TASK, "..", "261008-latfroz-nf-variants", "pg_tension.json"))
    )
    pg = pg["fits"]["LATFROZ_V3"]["FZ_min_est"]
    pgv, pgp, pgz = pg["PG"], pg["p"], pg["z_two_sided"]
    ax.annotate(
        "",
        xy=tuple(D["lam_lat"]),
        xytext=(max(mz[0], 0.0), mz[1]),
        arrowprops=dict(
            arrowstyle="<->", color="0.25", lw=1.3, ls="--", shrinkA=9, shrinkB=12
        ),
        zorder=5,
    )
    ax.text(
        0.165,
        0.026,
        "Z vs lattice: PG = %.1f / 2 dof\np = %.2f %%  (%.1f$\\sigma$)"
        % (pgv, 100 * pgp, pgz),
        fontsize=13,
        rotation=0,
        ha="left",
        color="0.15",
    )
    handles = [
        Patch(
            facecolor=COL["lattice"],
            alpha=0.5,
            edgecolor=COL["lattice"],
            label=r"Lattice only (ASWZ, V3 $n_f$ row): exact $\Delta\chi^2$",
        ),
        Line2D(
            [], [], color="#2a4f9a", ls=":", label="  its Gaussian approx. (2 H$^{-1}$)"
        ),
        Patch(
            facecolor=COL["LATFROZ_V3"],
            alpha=0.45,
            edgecolor=COL["LATFROZ_V3"],
            label="Z + lattice (LATFROZ V3), Hessian",
        ),
        Line2D(
            [],
            [],
            marker="o",
            color=COL["XWSTIFF"],
            mec="k",
            ls="--",
            ms=10,
            label="Z only (XWSTIFF), walled",
        ),
        Line2D(
            [],
            [],
            marker="s",
            color=COL["NOMSTIFF"],
            mec="k",
            ms=9,
            label=r"Z + 1D lattice prior, $\lambda_4^\nu$ = 0 (NOMSTIFF)",
        ),
    ]
    ax.legend(
        handles=handles,
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        fontsize=12.5,
        frameon=False,
        title="contours: 68.3 % / 95.4 % (2D, $\\Delta\\chi^2$ = 2.30 / 6.18)\n"
        r"$\lambda_\infty^\nu$ = 2, pert. part frozen ($\alpha_s$ = 0.1168, TNPs = 0)",
        title_fontsize=12,
    )
    ax.axhline(0, color="0.5", lw=0.8)
    ax.axvline(0, color="0.5", lw=0.8)
    plot_tools.add_cms_decor(ax, "Preliminary", loc=0, data=True, no_energy=True)
    fig.set_size_inches(17, 8)
    fig.subplots_adjust(left=0.08, right=0.60, bottom=0.12, top=0.92)
    save_plot(TASK, "lambda_nu_plane", fig=fig, args=args, meta_info=META)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--only", nargs="*", default=["1", "2", "3"], choices=["1", "2", "3"]
    )
    args = ap.parse_args()
    plt.rcParams.update({"axes.labelsize": 22, "legend.fontsize": 13})
    if "1" in args.only:
        fig1(args)
    if "2" in args.only:
        fig2(args)
    if "3" in args.only:
        fig3(args)


if __name__ == "__main__":
    main()
