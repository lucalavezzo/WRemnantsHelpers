#!/usr/bin/env python3
"""Step 2 + context plots for 261007-y-shape-first-look.

  residual_map_LATB8     (data - postfit) / sigma_data on the reco ptll x yll grid at LATB8's point
  ratio_by_absy_LATB8    data / postfit - 1 vs ptll, folded into five |yll| groups
  L2_of_Y                L2(Y) = lambda2 + delta_lambda2 Y^2: LATB8 (+-1 sigma from the WALL-FREE covariance YNOWALL8),
                         NOMSTIFF, MAP22 (small-b, central replica, CS evolution stripped), AN nominal

Postfit hists come from YNOWALL8 (= LATB8's vector, --noFit --saveHists; the wall changes the loss, not the prediction).
Residuals use the DATA statistical error only (no postfit / systematic / bin-by-bin MC-stat uncertainty: the pass ran
without --computeHistErrors), so they are normalised residuals, not pulls.
"""
import argparse
import json
import os
import sys

import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
from rabbit import io_tools
from wums import plot_tools

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from plot_output import save_plot  # noqa: E402

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
YNOWALL8 = f"{A}/261007_y_shape_first_look/fitresults_YNOWALL8.hdf5"
NOMSTIFF = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
GROUPS = [(0, 0.5), (0.5, 1.1), (1.1, 1.5), (1.5, 1.8), (1.8, 2.5)]


def lam(fr):
    parms = fr["parms"].get()
    n = [str(x) for x in parms.axes[0]]
    x = parms.values()
    return n, x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--outdir", default=TASK)
    args = ap.parse_args()
    meta = {"postfit_source": YNOWALL8, "note": "residuals in data-stat units only"}

    fr = io_tools.get_fitresult(YNOWALL8)
    ch = fr["mappings"]["BaseMapping"]["channels"]["ch0"]
    hd = ch["hist_data_obs"].get()
    hp = ch["hist_postfit_inclusive"].get()
    D, V, P = hd.values(), hd.variances(), hp.values()
    pt, y = hd.axes[0].edges, hd.axes[1].edges
    r = (D - P) / np.sqrt(V)

    # 1. residual map
    fig, ax = plot_tools.figure(
        hd,
        r"$p_{T}^{\ell\ell}$ (GeV)",
        r"$y^{\ell\ell}$",
        xlim=(0, 44),
        ylim=(-2.5, 2.5),
    )
    pc = ax.pcolormesh(pt, y, r.T, cmap="RdBu_r", vmin=-3, vmax=3)
    cb = fig.colorbar(pc, ax=ax)
    cb.set_label(r"(data $-$ postfit) / $\sigma_{\rm data}$")
    ax.text(
        0.97,
        0.03,
        r"LATB8 postfit, $\chi^2_{\rm data\,stat}$ = "
        + f"{(r**2).sum():.0f} / {r.size}",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=13,
        bbox=dict(facecolor="white", alpha=0.8, edgecolor="none"),
    )
    plot_tools.add_cms_decor(ax, "Preliminary", data=True, lumi=None, loc=0)
    save_plot(args.outdir, "residual_map_LATB8", fig=fig, args=args, meta_info=meta)
    plt.close(fig)

    # 2. folded |yll| ratio vs ptll, ptll merged into coarse windows (edges are a subset of the card's)
    yc = 0.5 * (y[1:] + y[:-1])
    cw = np.array([0, 2, 4, 6, 8, 10, 13, 16, 20, 26, 33, 44], dtype=float)
    iw = np.searchsorted(pt, cw)
    fig, ax = plot_tools.figure(
        hd,
        r"$p_{T}^{\ell\ell}$ (GeV)",
        "data / postfit $-$ 1 (%)",
        xlim=(0, 44),
        ylim=(-1.5, 1.5),
    )
    ax.axhline(0, color="grey", lw=1)
    cols = plt.cm.viridis(np.linspace(0, 0.9, len(GROUPS)))
    summary = {}
    for k, ((a, b), c) in enumerate(zip(GROUPS, cols)):
        sel = (np.abs(yc) > a) & (np.abs(yc) < b)
        dd, pp, vv = D[:, sel].sum(1), P[:, sel].sum(1), V[:, sel].sum(1)
        summary[f"{a}-{b}"] = dict(
            chi2=float((((dd - pp) / np.sqrt(vv)) ** 2).sum()), n=int(len(dd))
        )
        dw, pw, vw = (np.add.reduceat(q, iw[:-1]) for q in (dd, pp, vv))
        rel, err = 100 * (dw / pw - 1), 100 * np.sqrt(vw) / pw
        off = (k - 2) * 0.07 * np.diff(cw)
        ctr = 0.5 * (cw[1:] + cw[:-1]) + off
        ax.errorbar(
            ctr,
            rel,
            yerr=err,
            fmt="o",
            ms=5,
            color=c,
            label=rf"${a}<|y^{{\ell\ell}}|<{b}$",
        )
    plot_tools.addLegend(ax, ncols=2, text_size=12)
    plot_tools.add_cms_decor(ax, "Preliminary", data=True, lumi=None, loc=0)
    save_plot(args.outdir, "ratio_by_absy_LATB8", fig=fig, args=args, meta_info=meta)
    plt.close(fig)

    # 3. L2(Y)
    n, x = lam(fr)
    cov = fr["cov"].get().values()  # WALL-FREE covariance at LATB8's point
    il2, idl = n.index("lambda2"), n.index("delta_lambda2")
    Y = np.linspace(0, 2.5, 101)
    L2 = 0.4 + 0.5 * x[il2] + 0.5 * x[idl] * Y**2
    G = np.zeros((len(Y), 2))
    G[:, 0], G[:, 1] = 0.5, 0.5 * Y**2
    C2 = cov[np.ix_([il2, idl], [il2, idl])]
    sL2 = np.sqrt(np.einsum("ij,jk,ik->i", G, C2, G))
    nn, xn = lam(io_tools.get_fitresult(NOMSTIFF))
    L2n = (
        0.4 + 0.5 * xn[nn.index("lambda2")] + 0.5 * xn[nn.index("delta_lambda2")] * Y**2
    )
    mp = json.load(open(os.path.join(TASK, "map22_y4.json")))["central_curve"]

    fig, ax = plot_tools.figure(
        hd, r"$|Y|$", r"$L_2(Y)$ (GeV$^2$)", xlim=(0, 2.5), ylim=(-0.25, 0.4)
    )
    ax.axhline(0, color="k", lw=1)
    ax.fill_between(
        Y,
        L2 - sL2,
        L2 + sL2,
        color="C0",
        alpha=0.25,
        label=r"LATB8 $\pm1\sigma$ (wall-free cov.)",
    )
    ax.plot(
        Y,
        L2,
        color="C0",
        lw=2,
        label=rf"LATB8: $\Lambda_2$={L2[0]:.3f}, $\Delta\Lambda_2$={0.5*x[idl]:.4f}",
    )
    ax.plot(
        Y,
        L2n,
        color="C1",
        lw=2,
        ls="--",
        label=rf"NOMSTIFF: $\Lambda_2$={L2n[0]:.3f}, $\Delta\Lambda_2$={(L2n[-1]-L2n[0])/6.25:.4f}",
    )
    ax.plot(
        mp["Y"],
        mp["L2"],
        color="C2",
        lw=2,
        ls=(0, (1, 1.3)),
        label=r"MAP22 (small-$b$, central replica)",
    )
    ax.plot(
        Y,
        0.25 + 0.125 * Y**2,
        color="C3",
        lw=2,
        ls="-.",
        label=r"AN nominal: 0.25 + 0.125$Y^2$ (to 1.03)",
    )
    ax.axvline(2.5, color="grey", lw=1)
    plot_tools.addLegend(ax, ncols=1, text_size=11, loc="lower left")
    plot_tools.add_cms_decor(
        ax, "Preliminary", data=False, lumi=None, loc=0, no_energy=True
    )
    save_plot(args.outdir, "L2_of_Y", fig=fig, args=args, meta_info=meta)
    plt.close(fig)

    out = dict(
        groups=summary,
        sigma_L2_wallfree={f"{yy:g}": float(s) for yy, s in zip(Y[::25], sL2[::25])},
        L2_LATB8={f"{yy:g}": float(v) for yy, v in zip(Y[::25], L2[::25])},
    )
    json.dump(out, open(os.path.join(TASK, "y_shape_plots.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
