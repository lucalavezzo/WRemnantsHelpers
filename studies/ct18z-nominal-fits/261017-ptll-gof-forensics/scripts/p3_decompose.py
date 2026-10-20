#!/usr/bin/env python3
"""P3: exact (linear) decomposition of the ptll postfit chi2 from rabbit's saved postfit covariance.

Inputs: the P3 fitresults (--externalPostfit --noFit --computeHistCov) holding, per mapping, data, postfit and the
postfit prediction covariance V_pred.  The residual covariance of a profiled fit is, to first order,
    R = V_meas - V_pred,     V_meas = diag(N_j / b_j)
with b_j the BB-lite information factor of each ptll bin (MC stat inflates the data variance; b_j from the saturated
sub-fit Hessian, extracted by forensics.py).  R is validated by reproducing rabbit's own linear chi2 (which rabbit
computes from the exact profiled residual covariance) before anything is decomposed.

Decompositions of chi2 = r^T R^-1 r:
  - eigenmodes of R (contribution (u.r)^2/lambda), with each mode's smoothness (sign changes)
  - per bin: r_j (R^-1 r)_j (sums to chi2), and single-bin score (R^-1 r)_j^2 / (R^-1)_jj
  - chi2 absorbed by a free smooth Legendre shape of k parameters, and by freeing windows / the P1 coarse binnings
  - yll bands: ptll x 6 signed yll bands mapping, chi2 per band and chi2_234 - chi2_39 (y-dependence of the residual)
No alphaS value is read or printed.
"""

import argparse
import json
import os
import sys

import h5py
import numpy as np
from numpy.polynomial import legendre
from scipy.stats import chi2 as chi2d
from wums import ioutils

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_output import save_plot  # noqa: E402

PTLL = "Project ch0 ptll"
BAND = "Select yll:rebin(-2.5,-1.5,-0.7,0,0.7,1.5,2.5)"
YLL = "Project ch0 yll"
COARSE = {
    "k3": [0, 5, 15, 44],
    "k6": [0, 2, 5, 10, 15, 22, 44],
    "k10": [0, 1, 2, 3.5, 5, 7, 10, 12, 15, 22, 44],
}
REGIONS = {"[0,5)": (0, 9), "[5,15)": (9, 26), "[15,30)": (26, 36), "[30,44)": (36, 39)}


def load_map(r, key):
    m = r["mappings"][key]
    ch = m["channels"]["ch0"]
    out = dict(
        data=ch["hist_data_obs"].get().values().ravel(),
        post=ch["hist_postfit_inclusive"].get().values().ravel(),
        chi2=float(m["chi2"]),
        ndf=int(m["ndf"]),
        axes=ch["hist_postfit_inclusive"].get().axes,
    )
    out["Vpred"] = m["hist_postfit_inclusive_cov"].get().values()
    return out


def capture(Ri, r, B):
    g = B.T @ Ri @ r
    return float(g @ np.linalg.solve(B.T @ Ri @ B, g))


CARD = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5"
YEDGES = [
    -2.5,
    -1.8,
    -1.5,
    -1.3,
    -1.1,
    -0.9,
    -0.7,
    -0.5,
    -0.3,
    -0.15,
    0,
    0.15,
    0.3,
    0.5,
    0.7,
    0.9,
    1.1,
    1.3,
    1.5,
    1.8,
    2.5,
]
BANDS = [-2.5, -1.5, -0.7, 0, 0.7, 1.5, 2.5]


def card_bb():
    """2D data, MC-stat variance at data level (BB-lite) and the projection matrices (ptll-major 39 x 20)."""
    import hdf5plugin  # noqa: F401

    c = h5py.File(CARD, "r")
    sw = c["hsumw"][...].reshape(780, -1).sum(1)
    sw2 = c["hsumw2"][...].reshape(780, -1).sum(1)
    n = c["hdata_obs"][...]
    var_mc = sw2 * (n / sw) ** 2
    yb = np.searchsorted(BANDS, np.array(YEDGES[:-1]) + 1e-6, side="right") - 1
    P = {
        "ptll": np.zeros((39, 780)),
        "yll": np.zeros((20, 780)),
        "band": np.zeros((234, 780)),
    }
    for j in range(39):
        for y in range(20):
            i = j * 20 + y
            P["ptll"][j, i] = 1
            P["yll"][y, i] = 1
            P["band"][j * 6 + yb[y], i] = 1
    return n, var_mc, P


def resid_cov(n, var_mc, Pm, Vpred):
    """R = (1-f) (P diag(n + var_mc) P^T - V_pred) (1-f): BB-lite shrinks the profiled residual by (1-f) per bin,
    f = var_mc/(n+var_mc) (projected as a yield-weighted mean). Validated against rabbit's printed linear chi2.
    """
    f = var_mc / (n + var_mc)
    fo = (Pm @ (f * n)) / (Pm @ n)
    return np.diag(1 - fo) @ (Pm @ np.diag(n + var_mc) @ Pm.T - Vpred) @ np.diag(1 - fo)


def analyse(fit, arrays, edges):
    r_ = fit["ptll"]
    data, post, Vp = r_["data"], r_["post"], r_["Vpred"]
    r = data - post
    n2, var_mc, P = card_bb()
    res = {
        "rabbit_chi2": r_["chi2"],
        "rabbit_ndf": r_["ndf"],
        "R_used": "(1-f)(N+varMC-Vpred)(1-f)",
    }
    Rm = resid_cov(n2, var_mc, P["ptll"], Vp)
    res["chi2_rebuilt"] = float(r @ np.linalg.solve(Rm, r))
    Ri = np.linalg.inv(Rm)
    c = float(r @ Ri @ r)
    res["chi2"] = c
    lam, U = np.linalg.eigh(Rm)
    contrib = (U.T @ r) ** 2 / lam
    nsc = np.array(
        [(np.sign(U[1:, k]) != np.sign(U[:-1, k])).sum() for k in range(len(lam))]
    )
    res["modes"] = dict(lam=lam.tolist(), contrib=contrib.tolist(), nsc=nsc.tolist())
    res["perbin_split"] = (r * (Ri @ r)).tolist()
    ktop = int(np.argmax(contrib))
    res["top_mode_component_rel"] = ((U[:, ktop] @ r) * U[:, ktop] / post).tolist()
    res["resid_rel"] = (r / post).tolist()
    res["resid_rel_err"] = (np.sqrt(np.diag(Rm)) / post).tolist()
    for K in (6, 9):
        B = legendre.legvander(np.linspace(-1, 1, 39), K)
        cc = np.linalg.solve(B.T @ Ri @ B, B.T @ Ri @ r)
        res[f"smooth_fit_rel_k{K + 1}"] = ((B @ cc) / post).tolist()
    res["single"] = ((Ri @ r) ** 2 / np.diag(Ri)).tolist()
    res["z_dataonly"] = (r / np.sqrt(data)).tolist()
    res["sigma_res_over_sigma_data"] = np.sqrt(np.diag(Rm) / data).tolist()
    t = np.linspace(-1, 1, 39)
    res["smooth"] = {K + 1: capture(Ri, r, legendre.legvander(t, K)) for K in range(12)}
    win = {}
    for k, (a, bb) in REGIONS.items():
        B = np.zeros((39, bb - a))
        B[np.arange(a, bb), np.arange(bb - a)] = 1
        win[k] = capture(Ri, r, B)
    res["windows"] = win
    co = {}
    for k, ed in COARSE.items():
        idx = np.searchsorted(ed, edges[:-1], side="right") - 1
        B = np.zeros((39, len(ed) - 1))
        B[np.arange(39), idx] = 1
        co[k] = capture(Ri, r, B)
    res["coarse"] = co
    # yll bands
    bd = fit["band"]
    rb = bd["data"] - bd["post"]
    nb = len(rb) // 39
    shape = [len(a) for a in bd["axes"]]
    res["band_axes"] = [a.name for a in bd["axes"]]
    res["band_shape"] = shape
    Vb = bd["Vpred"]
    # ptll is the first axis (39), bands second: flat index = i_ptll * nb + i_band
    Rb = resid_cov(n2, var_mc, P["band"], Vb)
    evb = np.linalg.eigvalsh(Rb)
    res["band_Rmin"] = float(evb.min())
    res["band_chi2"] = float(rb @ np.linalg.solve(Rb, rb))
    res["band_rabbit_chi2"] = bd["chi2"]
    per = {}
    for ib in range(nb):
        sel = np.arange(39) * nb + ib
        per[ib] = float(rb[sel] @ np.linalg.solve(Rb[np.ix_(sel, sel)], rb[sel]))
    res["band_per"] = per
    res["band_z"] = (rb / np.sqrt(bd["data"])).reshape(39, nb).tolist()
    yl = fit["yll"]
    res["yll_rabbit_chi2"] = yl["chi2"]
    ry = yl["data"] - yl["post"]
    res["yll_chi2_rebuilt"] = float(
        ry @ np.linalg.solve(resid_cov(n2, var_mc, P["yll"], yl["Vpred"]), ry)
    )
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fits", nargs="+", required=True, help="TAG=fitresults.hdf5")
    ap.add_argument(
        "--arrays",
        required=True,
        help="dir with arrays_<TAG>.npz (for the BB factor) and forensics json",
    )
    ap.add_argument(
        "--surrogate", required=True, help="forensics_numbers.json from phase 1"
    )
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    sur = json.load(open(args.surrogate))
    allres = {}
    edges = None
    for spec in args.fits:
        tag, path = spec.split("=", 1)
        f = h5py.File(path, "r")
        r = ioutils.pickle_load_h5py(f["results"])
        fit = dict(ptll=load_map(r, PTLL), band=load_map(r, BAND), yll=load_map(r, YLL))
        edges = fit["ptll"]["axes"][0].edges
        arrays = dict(bbfac=np.array(sur[tag]["bbfac"]))
        allres[tag] = analyse(fit, arrays, edges)
        allres[tag]["q_saturated"] = sur[tag]["q"]
        f.close()
    json.dump(allres, open(os.path.join(args.outdir, "p3_numbers.json"), "w"), indent=1)
    for tag, res in allres.items():
        s = sur[tag]
        qW = s["B"]["qW"]
        c = res["chi2"]
        print(
            f"===== {tag}: rabbit linear chi2 {res['rabbit_chi2']:.2f}/{res['rabbit_ndf']} | rebuilt {res['chi2_rebuilt']:.2f} ({res['R_used']}); saturated q {res['q_saturated']:.2f}"
        )
        print(
            f"  p(lin) {chi2d.sf(c, 39) * 100:.3f}%  sigma_res/sigma_data range {min(res['sigma_res_over_sigma_data']):.3f}-{max(res['sigma_res_over_sigma_data']):.3f}"
        )
        lam = np.array(res["modes"]["lam"])
        con = np.array(res["modes"]["contrib"])
        nsc = np.array(res["modes"]["nsc"])
        o = np.argsort(-con)[:6]
        print(
            "  top modes (sqrt(lam)/sqrt(Nmean) , signchanges, contrib):",
            [
                (f"{np.sqrt(lam[i]):.0f}", int(nsc[i]), round(float(con[i]), 1))
                for i in o
            ],
        )
        print(
            "  smallest-eigenvalue 5 modes contrib:",
            [round(float(x), 1) for x in con[:5]],
            "nsc",
            nsc[:5].tolist(),
        )
        print(
            "  smooth k=1..12 (exact):",
            [round(res["smooth"][k], 1) for k in sorted(res["smooth"])],
        )
        print(
            "  smooth k=1..12 (surrogate, x frac of qW):",
            [
                round(s["B"]["smooth"]["bin-index"][str(k - 1)] / qW, 3)
                for k in range(1, 13)
            ],
            " exact frac:",
            [round(res["smooth"][k] / c, 3) for k in sorted(res["smooth"])],
        )
        print(
            "  windows exact frac:",
            {k: round(v / c, 3) for k, v in res["windows"].items()},
            " surrogate:",
            {k: round(v[0] / qW, 3) for k, v in s["B"]["win"].items() if k in REGIONS},
        )
        print(
            "  coarse (P1 bases) exact:",
            {k: round(v, 1) for k, v in res["coarse"].items()},
            "remainder",
            {k: round(c - v, 1) for k, v in res["coarse"].items()},
        )
        sg = np.array(res["single"])
        print(
            "  single-bin top (exact):",
            sorted([(round(float(v), 1), j) for j, v in enumerate(sg)], reverse=True)[
                :6
            ],
            " surrogate:",
            sorted(
                [(round(v, 1), j) for j, v in enumerate(s["B"]["single"])], reverse=True
            )[:6],
        )
        print(
            f"  bands {res['band_shape']} {res['band_axes']}: rabbit chi2 {res['band_rabbit_chi2']:.1f} rebuilt {res['band_chi2']:.1f} (Rmin {res['band_Rmin']:.3g}); minus ptll -> {res['band_chi2'] - c:.1f} / {39 * 5}"
        )
        print(
            "  per-band chi2 (39 bins each):",
            {k: round(v, 1) for k, v in res["band_per"].items()},
        )
        print(
            f"  yll projection rabbit linear chi2 {res['yll_rabbit_chi2']:.1f}/20 rebuilt {res['yll_chi2_rebuilt']:.1f}"
        )
    plots(args, allres, edges, sur)


def plots(args, allres, edges, sur):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import mplhep as hep

    hep.style.use(hep.style.CMS)
    cols = {"LAT": "tab:blue", "NOLAT": "tab:orange"}
    meta = {
        "note": "exact linear decomposition from rabbit postfit covariance (P3 rerun)"
    }
    ctr = 0.5 * (edges[1:] + edges[:-1])
    wid = edges[1:] - edges[:-1]
    # per bin
    fig, axs = plt.subplots(2, 1, figsize=(11, 10), sharex=True)
    for tag, res in allres.items():
        sp = np.array(res["perbin_split"])
        sg = np.array(res["single"])
        axs[0].step(
            edges,
            np.r_[sp, sp[-1]],
            where="post",
            color=cols[tag],
            label=f"{tag}: $r_j(R^{{-1}}r)_j$, sum = {res['chi2']:.1f}",
        )
        axs[1].step(
            edges,
            np.r_[sg, sg[-1]],
            where="post",
            color=cols[tag],
            label=f"{tag}: single-bin score",
        )
        su = np.array(sur[tag]["B"]["single"])
        axs[1].step(
            edges,
            np.r_[su, su[-1]],
            where="post",
            color=cols[tag],
            ls=":",
            label=f"{tag}: phase-1 surrogate",
        )
    axs[0].axhline(0, color="k", lw=0.6)
    axs[0].set_ylabel("per-bin share of linear $\\chi^2$")
    axs[1].set_ylabel("single-bin score")
    axs[1].set_xlabel("$p_T^{\\mu\\mu}$ (GeV)")
    for a in axs:
        a.legend(fontsize=11)
    save_plot(
        os.path.join(args.outdir, "p3"),
        "perbin_exact",
        fig=fig,
        args=args,
        meta_info=meta,
    )
    plt.close(fig)
    # modes
    fig, axs = plt.subplots(1, 2, figsize=(16, 6.5))
    for tag, res in allres.items():
        lam = np.array(res["modes"]["lam"])
        con = np.array(res["modes"]["contrib"])
        nsc = np.array(res["modes"]["nsc"])
        axs[0].plot(np.arange(len(lam)), con, "o-", color=cols[tag], label=f"{tag}")
        axs[1].plot(nsc, con, "o", color=cols[tag], label=tag)
    axs[0].axhline(1, color="k", ls="--", lw=0.8)
    axs[0].set_xlabel("eigenmode of R (0 = smallest variance)")
    axs[0].set_ylabel("contribution to linear $\\chi^2$")
    axs[1].axhline(1, color="k", ls="--", lw=0.8)
    axs[1].set_xlabel("sign changes of the mode")
    axs[1].set_ylabel("contribution to linear $\\chi^2$")
    for a in axs:
        a.legend()
    save_plot(
        os.path.join(args.outdir, "p3"),
        "eigenmodes_exact",
        fig=fig,
        args=args,
        meta_info=meta,
    )
    plt.close(fig)
    # smooth capture exact vs surrogate
    fig, ax = plt.subplots(figsize=(10, 7))
    for tag, res in allres.items():
        Ks = sorted(res["smooth"])
        ax.plot(
            Ks,
            [res["smooth"][k] / res["chi2"] for k in Ks],
            "o-",
            color=cols[tag],
            label=f"{tag}: exact (linear $\\chi^2$ = {res['chi2']:.1f})",
        )
        qW = sur[tag]["B"]["qW"]
        ax.plot(
            Ks,
            [sur[tag]["B"]["smooth"]["bin-index"][str(k - 1)] / qW for k in Ks],
            "s:",
            color=cols[tag],
            label=f"{tag}: phase-1 surrogate",
        )
    ax.plot(Ks, np.array(Ks) / 39, "k:", label="noise expectation k/39")
    ax.set_xlabel("free smooth shape parameters k")
    ax.set_ylabel("fraction absorbed")
    ax.set_ylim(0, 1)
    ax.legend(fontsize=11)
    save_plot(
        os.path.join(args.outdir, "p3"),
        "smooth_capture_exact",
        fig=fig,
        args=args,
        meta_info=meta,
    )
    plt.close(fig)
    # leading mode and smooth fits
    fig, axs = plt.subplots(
        len(allres), 1, figsize=(12, 5.5 * len(allres)), sharex=True
    )
    for ax, (tag, res) in zip(np.atleast_1d(axs), allres.items()):
        rr = 100 * np.array(res["resid_rel"])
        ee = 100 * np.array(res["resid_rel_err"])
        ax.errorbar(
            ctr,
            rr,
            yerr=ee,
            xerr=wid / 2,
            fmt="o",
            color="gray",
            ms=4,
            label="(data - postfit)/postfit, error = sqrt(diag R)",
        )
        tm = 100 * np.array(res["top_mode_component_rel"])
        ax.step(
            edges,
            np.r_[tm, tm[-1]],
            where="post",
            color="tab:red",
            lw=2,
            label=f"component along the leading mode ({max(res['modes']['contrib']):.1f} of {res['chi2']:.1f})",
        )
        for K, ls in ((7, "--"), (10, "-")):
            sf = 100 * np.array(res[f"smooth_fit_rel_k{K}"])
            ax.plot(
                ctr,
                sf,
                ls,
                color="tab:blue",
                label=f"best smooth shape, {K} Legendre parameters (absorbs {res['smooth'][K]:.1f})",
            )
        ax.axhline(0, color="k", lw=0.6)
        ax.set_ylabel("relative to postfit (%)")
        ax.text(
            0.01,
            0.95,
            tag,
            transform=ax.transAxes,
            fontsize=18,
            fontweight="bold",
            va="top",
        )
        ax.set_ylim(-0.9, 0.9)
        ax.legend(fontsize=10, loc="lower right")
    np.atleast_1d(axs)[-1].set_xlabel("$p_T^{\\mu\\mu}$ (GeV)")
    save_plot(
        os.path.join(args.outdir, "p3"),
        "leading_mode_and_smooth_fit",
        fig=fig,
        args=args,
        meta_info=meta,
    )
    plt.close(fig)
    # bands
    fig, axs = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    for ax, (tag, res) in zip(axs, allres.items()):
        z = np.array(res["band_z"])
        labels = [
            "[-2.5,-1.5]",
            "[-1.5,-0.7]",
            "[-0.7,0]",
            "[0,0.7]",
            "[0.7,1.5]",
            "[1.5,2.5]",
        ]
        for ib in range(z.shape[1]):
            ax.step(
                edges,
                np.r_[z[:, ib], z[-1, ib]],
                where="post",
                label=f"yll {labels[ib]}: $\\chi^2$ {res['band_per'][ib]:.1f}/39",
            )
        zp = np.array(res["z_dataonly"])
        ax.plot(ctr, zp, "ko", ms=4, label="ptll projection")
        ax.axhline(0, color="k", lw=0.6)
        ax.set_ylabel(f"{tag}: (data-post)/$\\sqrt{{data}}$")
        ax.legend(fontsize=9, ncol=2)
    axs[-1].set_xlabel("$p_T^{\\mu\\mu}$ (GeV)")
    save_plot(
        os.path.join(args.outdir, "p3"), "yll_bands", fig=fig, args=args, meta_info=meta
    )
    plt.close(fig)


if __name__ == "__main__":
    main()
