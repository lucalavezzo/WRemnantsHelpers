#!/usr/bin/env python3
"""ptll saturated-projection forensics from SAVED fitresults only (no fit, no cache).

Inputs: arrays_<cfg>.npz written by extract.py (M0 = analysis fit, M1 = saturated ptll sub-fit).
All quantities below are LINEAR (Gaussian) surrogates built from the saved covariances, NOT rabbit
fits; each is labelled as such in the logbook and is to be confirmed in rabbit (Phase 2).

  A. data-only residuals of the ptll marginal: z_j = (data-post)/sqrt(data), sum z^2, lag-1 autocorr.
  B. M1-frame quadratic ("Wald") view of q: profile quadratic around the M1 minimum in the scale
     parameters x = sqrt(s) (rabbit's own coordinates), f(x) = (x-xhat)^T V^-1 (x-xhat), V = cov1[x,x].
       - eigenmode split of f(1)
       - q absorbed by a free SMOOTH shape (Legendre basis of order K) instead of 39 free scales
       - q absorbed by freeing only a window of ptll bins; single-bin score
  C. linear prior-release / prior-inflation prediction, per nuisance and per group:
       Delta_M(p) = g^T [(F+pI)^-1 - (F+I)^-1] g ,  g = C_GG^-1 x_G , F = C_GG^-1 - I
     (Gaussian prior N(0,1) replaced by N(0,1/p); p = 1/f^2; p -> 0 = release), applied to
     M0 and M1:  q(f) = q - [Delta_M0(f) - Delta_M1(f)].
  D. ptll templates of every parameter at the M1 point, from H1 = cov1^-1:
       t_jk = H1[s_j, theta_k] / (s_j H1[s_j, s_j])  = (BB-weighted) mean relative template in ptll bin j.

alphaS is never printed or written (it is excluded from every table).
"""

import argparse
import json
import os
import re
import sys

import numpy as np
from numpy.polynomial import legendre

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_output import save_plot  # noqa: E402

S = slice(47, 86)  # the 39 saturated_ch0_ptll<j> parameters in M1 ordering
NJ = 39
GROUPS = [
    (
        "A0 scale (QCDscaleZfine/incl helicity_0)",
        r"QCDscaleZ(fine|inclusive)_.*helicity_0_",
    ),
    (
        "A1-A7 scale (QCDscaleZ helicity_1..7)",
        r"QCDscaleZ(fine|inclusive)_.*helicity_[1-7]_",
    ),
    ("SCETlib FO scale env (resumFOScaleEnv*)", r"resumFOScaleEnv"),
    ("SCETlib TNP (resumTNP_*)", r"resumTNP_"),
    ("resumTransition2", r"resumTransition2$"),
    ("PDF eigen (pdfEig*)", r"pdfEig\d+$"),
    ("b/c mass (mb_*, pdfMSHT20mb/mc range)", r"(mb_|pdfMSHT20m[bc]range)"),
    ("lumi", r"lumi$"),
    ("EW: weak_*, sin2thetaZ, widthZ", r"(weak_|sin2thetaZ|widthZ)"),
    ("QED FSR (horace*)", r"horace"),
    ("pythia shower kt", r"pythia_shower_kt"),
    ("muon resolution (Resolution_*)", r"Resolution_"),
    ("muon scale (Scale*, ScaleClos*, pixel*)", r"(Scale|ScaleClos|pixel)"),
    ("efficiency syst (effSyst*)", r"effSyst"),
    ("efficiency stat (effStat*)", r"effStat"),
    ("prefire (CMS_prefire*)", r"CMS_prefire"),
    ("backgrounds (CMS_background, PhotonInduced)", r"CMS_(background|PhotonInduced)"),
]


def load(wd, cfg):
    d = np.load(f"{wd}/arrays_{cfg}.npz")
    n0 = [str(s) for s in d["names0"]]
    n1 = [str(s) for s in d["names1"]]
    idx1 = np.array([n1.index(n) for n in n0])
    return d, n0, n1, idx1


# ---------------------------------------------------------------- A
def part_A(d):
    data = d["h_hist_data_obs"]
    post = d["h_hist_postfit_inclusive"]
    z = (data - post) / np.sqrt(data)
    out = dict(
        sum_z2=float((z**2).sum()),
        lag1=float(np.corrcoef(z[:-1], z[1:])[0, 1]),
        nsignchange=int((np.sign(z[1:]) != np.sign(z[:-1])).sum()),
    )
    # smooth Legendre fits to z (data-only metric): chi2 absorbed vs order
    t = np.linspace(-1, 1, NJ)
    out["legendre_absorbed_dataonly"] = {}
    for K in range(0, 9):
        B = legendre.legvander(t, K)
        c, *_ = np.linalg.lstsq(B, z, rcond=None)
        out["legendre_absorbed_dataonly"][K] = float(
            (z**2).sum() - ((z - B @ c) ** 2).sum()
        )
    return z, out


# ---------------------------------------------------------------- B
def q_capture(Iinfo, delta, B):
    """q absorbed when s is restricted to 1 + span(B) instead of free (quadratic f)."""
    g = B.T @ Iinfo @ delta
    M = B.T @ Iinfo @ B
    return float(g @ np.linalg.solve(M, g))


def part_B(d, q_lr):
    x = d["x1"][S]
    V = d["cov1"][S, S]
    Iinfo = np.linalg.inv(V)
    delta = x - 1.0  # f(1) uses (1 - xhat); sign irrelevant in quadratic forms
    qW = float(delta @ Iinfo @ delta)
    s = x**2
    Vs = V * np.outer(2 * x, 2 * x)
    qW_s = float((s - 1) @ np.linalg.solve(Vs, s - 1))
    lam, U = np.linalg.eigh(Iinfo)
    order = np.argsort(-lam)  # best-measured first
    lam, U = lam[order], U[:, order]
    contrib = lam * (U.T @ delta) ** 2
    nsc = np.array([(np.sign(U[1:, k]) != np.sign(U[:-1, k])).sum() for k in range(NJ)])
    t_idx = np.linspace(-1, 1, NJ)
    edges = d["edges"]
    ctr = 0.5 * (edges[1:] + edges[:-1])
    t_log = np.log(ctr + 1.0)
    t_log = 2 * (t_log - t_log.min()) / (t_log.max() - t_log.min()) - 1
    smooth = {}
    for name, tt in (("bin-index", t_idx), ("log(1+ptll)", t_log)):
        smooth[name] = {
            K: q_capture(Iinfo, delta, legendre.legvander(tt, K)) for K in range(0, 12)
        }
    # windows: rabbit card-A region boundaries + sliding windows
    regions = {
        "[0,5)": (0, 9),
        "[5,15)": (9, 26),
        "[15,30)": (26, 36),
        "[30,44)": (36, 39),
        "[0,10)": (0, 19),
        "[10,20)": (19, 31),
        "[20,44)": (31, 39),
    }
    win = {}
    for k, (a, b) in regions.items():
        B = np.zeros((NJ, b - a))
        B[np.arange(a, b), np.arange(b - a)] = 1
        win[k] = (q_capture(Iinfo, delta, B), b - a)
    sliding = {}
    for w in (1, 2, 3, 5):
        vals = []
        for a in range(0, NJ - w + 1):
            B = np.zeros((NJ, w))
            B[np.arange(a, a + w), np.arange(w)] = 1
            vals.append(q_capture(Iinfo, delta, B))
        sliding[w] = vals
    single = (Iinfo @ delta) ** 2 / np.diag(Iinfo)
    # same in s = x^2 coordinates (a different quadratic surrogate: spread = nonlinearity)
    Is = np.linalg.inv(Vs)
    ds = s - 1
    smooth_s = {
        K: q_capture(Is, ds, legendre.legvander(t_idx, K)) for K in range(0, 12)
    }
    win_s = {}
    for k, (a, b) in regions.items():
        B = np.zeros((NJ, b - a))
        B[np.arange(a, b), np.arange(b - a)] = 1
        win_s[k] = q_capture(Is, ds, B)
    return dict(
        smooth_s=smooth_s,
        win_s=win_s,
        qW=qW,
        qW_s=qW_s,
        q_lr=q_lr,
        lam=lam,
        contrib=contrib,
        nsc=nsc,
        U=U,
        smooth=smooth,
        win=win,
        sliding=sliding,
        single=single,
        s=s,
        sig_s=np.sqrt(np.diag(Vs)),
    )


# ---------------------------------------------------------------- C
def delta_prior(C, x, p):
    """Gain in 2NLL at the minimum when the N(0,1) priors on this block become N(0,1/p)."""
    Ci = np.linalg.inv(C)
    g = Ci @ x
    F = Ci - np.eye(len(x))
    F = 0.5 * (F + F.T)
    w, U = np.linalg.eigh(F)
    w = np.clip(w, 1e-9, None)  # data-only information on the block, floored
    gt = U.T @ g
    return float((gt**2 * (1.0 / (w + p) - 1.0 / (w + 1.0))).sum())


def part_C(d, n0, idx1):
    con = d["var_prefit"] > 0
    x0, C0 = d["x0"], d["cov0"]
    x1, C1 = d["x1"][idx1], d["cov1"][np.ix_(idx1, idx1)]
    res = {"groups": {}, "singles": []}
    fs = {"x2": 0.25, "x3": 1 / 9.0, "x10": 0.01}
    for gname, pat in GROUPS:
        ii = np.array([i for i, n in enumerate(n0) if con[i] and re.match(pat, n)])
        if len(ii) == 0:
            continue
        r = {
            "n": int(len(ii)),
            "pull2_M0": float((x0[ii] ** 2).sum()),
            "pull2_M1": float((x1[ii] ** 2).sum()),
        }
        for k, p in fs.items():
            d0 = delta_prior(C0[np.ix_(ii, ii)], x0[ii], p)
            d1 = delta_prior(C1[np.ix_(ii, ii)], x1[ii], p)
            r[k] = dict(dM0=d0, dM1=d1, dq=d0 - d1)
        res["groups"][gname] = r
    # all constrained together
    ii = np.where(con)[0]
    for k, p in {"x2": 0.25}.items():
        d0 = delta_prior(C0[np.ix_(ii, ii)], x0[ii], p)
        d1 = delta_prior(C1[np.ix_(ii, ii)], x1[ii], p)
        res["all_constrained_x2"] = dict(dM0=d0, dM1=d1, dq=d0 - d1)
    # singles (release = x^2/(1-c); inflate x2)
    for i in np.where(con)[0]:
        if n0[i] == "alphaS":
            continue
        c0, c1 = C0[i, i], C1[i, i]
        row = dict(
            name=n0[i],
            pull0=float(x0[i]),
            pull1=float(x1[i]),
            sig0=float(np.sqrt(c0)),
            sig1=float(np.sqrt(c1)),
            dpen=float(x0[i] ** 2 - x1[i] ** 2),
        )
        for k, p in fs.items():
            d0 = delta_prior(np.array([[c0]]), np.array([x0[i]]), p)
            d1 = delta_prior(np.array([[c1]]), np.array([x1[i]]), p)
            row[k] = d0 - d1
        res["singles"].append(row)
    res["singles"].sort(key=lambda r: -r["x10"])
    # free-parameter freeze sanity (alphaS excluded from output; NP lambda block only)
    fr = [i for i in range(len(n0)) if not con[i] and n0[i] != "alphaS"]
    dl = x1[fr] - x0[fr]
    res["freeze_NPlambda_dq"] = float(dl @ np.linalg.solve(C1[np.ix_(fr, fr)], dl))
    return res


# ---------------------------------------------------------------- D
def part_D(d, n0, idx1):
    x = d["x1"][S]
    s = x**2
    H1 = np.linalg.inv(d["cov1"])
    J = 1.0 / (2 * x)
    Iss = np.diag(H1[S, S]) * J**2
    T = H1[S][:, idx1] * J[:, None]
    t_rel = T / (s * Iss)[:, None]  # relative ptll template per unit theta
    bbfac = Iss * s**2 / d["h_hist_data_obs"]
    return t_rel, bbfac


# ---------------------------------------------------------------- plots
def plots(outdir, res, args):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import mplhep as hep

    hep.style.use(hep.style.CMS)
    cols = {"LAT": "tab:blue", "NOLAT": "tab:orange"}
    meta = {
        "inputs": "arrays_<cfg>.npz from extract.py (fitresults paths in extract.py)",
        "note": "linear/quadratic surrogates from saved covariances, not rabbit fits",
    }
    any_ = next(iter(res.values()))
    edges = any_["edges"]
    ctr = 0.5 * (edges[1:] + edges[:-1])
    wid = edges[1:] - edges[:-1]

    # 1. per-bin view
    fig, axs = plt.subplots(3, 1, figsize=(11, 13), sharex=True)
    for cfg, r in res.items():
        axs[0].errorbar(
            ctr,
            r["z"],
            xerr=wid / 2,
            fmt="o",
            ms=4,
            color=cols[cfg],
            label=f"{cfg}: $\\Sigma z^2$={r['A']['sum_z2']:.1f}/39",
        )
        axs[1].step(
            edges,
            np.r_[r["B"]["single"], r["B"]["single"][-1]],
            where="post",
            color=cols[cfg],
            label=f"{cfg} (quadratic q = {r['B']['qW']:.1f}; rabbit q = {r['B']['q_lr']:.1f})",
        )
        sv = r["B"]["s"] - 1
        axs[2].errorbar(
            ctr,
            sv,
            yerr=r["B"]["sig_s"],
            xerr=wid / 2,
            fmt="o",
            ms=4,
            color=cols[cfg],
            label=cfg,
        )
    axs[0].axhline(0, color="k", lw=0.8)
    axs[0].set_ylabel("(data - postfit)/$\\sqrt{data}$")
    axs[0].legend(fontsize=13, loc="upper right")
    axs[1].set_ylabel("single-bin score $q_j$")
    axs[1].legend(fontsize=12)
    axs[2].axhline(0, color="k", lw=0.8)
    axs[2].set_ylabel("$\\hat{s}_j - 1$ (M1 free scales)")
    axs[2].set_xlabel("$p_T^{\\mu\\mu}$ (GeV)")
    axs[2].legend(fontsize=13)
    axs[0].set_title(
        "ptll projection, per bin (z: data stat only; $q_j$, $\\hat s$: saturated sub-fit)",
        fontsize=14,
    )
    save_plot(args.outdir, "perbin_view", fig=fig, args=args, meta_info=meta)
    plt.close(fig)

    # 2. eigenmodes
    fig, axs = plt.subplots(1, 2, figsize=(16, 6.5))
    for cfg, r in res.items():
        B = r["B"]
        k = np.arange(NJ)
        axs[0].bar(
            k + (0.2 if cfg == "NOLAT" else -0.2),
            B["contrib"],
            width=0.4,
            color=cols[cfg],
            label=cfg,
        )
        axs[1].plot(B["nsc"], B["contrib"], "o", color=cols[cfg], label=cfg)
    axs[0].axhline(1, color="k", ls="--", lw=0.8)
    axs[0].set_xlabel("eigenmode (0 = best measured)")
    axs[0].set_ylabel("contribution to quadratic q")
    axs[0].legend()
    axs[1].axhline(1, color="k", ls="--", lw=0.8)
    axs[1].set_xlabel("sign changes of the mode (0 = smooth)")
    axs[1].set_ylabel("contribution to quadratic q")
    axs[1].legend()
    save_plot(args.outdir, "eigenmodes", fig=fig, args=args, meta_info=meta)
    plt.close(fig)

    # 3. smooth capture
    fig, ax = plt.subplots(figsize=(10, 7))
    for cfg, r in res.items():
        B = r["B"]
        for name, ls in (("bin-index", "-"), ("log(1+ptll)", "--")):
            Ks = sorted(B["smooth"][name])
            frac = [B["smooth"][name][K] / B["qW"] for K in Ks]
            ax.plot(
                np.array(Ks) + 1,
                frac,
                ls,
                marker="o",
                color=cols[cfg],
                label=f"{cfg}, Legendre in {name}",
            )
    Ks = np.arange(1, 13)
    ax.plot(Ks, Ks / 39.0, ":", color="k", label="pure noise expectation (k/39)")
    ax.set_xlabel("number of free smooth shape parameters k (Legendre order + 1)")
    ax.set_ylabel("fraction of quadratic q absorbed")
    ax.set_ylim(0, 1)
    ax.legend(fontsize=12)
    save_plot(args.outdir, "smooth_capture", fig=fig, args=args, meta_info=meta)
    plt.close(fig)

    # 4. sliding windows
    fig, ax = plt.subplots(figsize=(11, 6.5))
    for cfg, r in res.items():
        for w, ls in ((1, ":"), (3, "-"), (5, "--")):
            v = np.array(r["B"]["sliding"][w])
            lo = edges[: NJ - w + 1]
            ax.step(
                np.r_[lo, edges[NJ - w + 1]],
                np.r_[v, v[-1]],
                where="post",
                ls=ls,
                color=cols[cfg],
                label=f"{cfg}, {w} adjacent bins free",
            )
    ax.set_xlabel("first bin of the freed window, $p_T^{\\mu\\mu}$ (GeV)")
    ax.set_ylabel("quadratic q absorbed")
    ax.legend(fontsize=11, ncol=2)
    save_plot(args.outdir, "window_scan", fig=fig, args=args, meta_info=meta)
    plt.close(fig)

    # 5. group release
    fig, ax = plt.subplots(figsize=(12, 9))
    names = list(any_["C"]["groups"].keys())
    yy = np.arange(len(names))
    for j, (cfg, r) in enumerate(res.items()):
        g = r["C"]["groups"]
        ax.barh(
            yy + (0.2 if j else -0.2),
            [g[n]["x2"]["dq"] for n in names],
            height=0.2,
            color=cols[cfg],
            label=f"{cfg}: prior x2",
        )
        ax.barh(
            yy + (0.2 if j else -0.2),
            [g[n]["x3"]["dq"] for n in names],
            height=0.2,
            color=cols[cfg],
            alpha=0.35,
            label=f"{cfg}: prior x3",
            zorder=0,
        )
    ax.set_yticks(yy)
    ax.set_yticklabels(names, fontsize=11)
    ax.set_xlabel(
        "linear predicted drop of q (ptll projection) when the group prior is widened"
    )
    ax.axvline(0, color="k", lw=0.8)
    ax.legend(fontsize=11)
    save_plot(args.outdir, "group_release", fig=fig, args=args, meta_info=meta)
    plt.close(fig)

    # 6. templates x pull. One fixed colour per nuisance in both panels (union of each fit's top-7 by prior relief),
    # so a colour means the same nuisance everywhere (2026-10-18 fix: the colours used to follow each panel's own order).
    fig, axs = plt.subplots(2, 1, figsize=(12, 12), sharex=True)
    tops = []
    for cfg in res:
        r = res[cfg]
        x0, x1, n0, con = r["x0"], r["x1"], r["n0"], r["con"]
        for i in sorted(
            [i for i in range(len(n0)) if con[i]],
            key=lambda i: -(x0[i] ** 2 - x1[i] ** 2),
        )[:7]:
            if n0[i] not in tops:
                tops.append(n0[i])
    palette = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#17becf",
        "#bcbd22",
    ]
    colour = {n: palette[k % len(palette)] for k, n in enumerate(tops)}
    for ax, cfg in zip(axs, res):
        r = res[cfg]
        t = r["t_rel"]
        x0, x1 = r["x0"], r["x1"]
        n0 = r["n0"]
        con = r["con"]
        w = r["data"] / r["data"].sum()

        def shape_only(v):
            return v - (w * v).sum()

        for nm in tops:
            i = n0.index(nm)
            sh = shape_only(t[:, i] * (x0[i] - x1[i]) * 100)
            ax.step(
                edges,
                np.r_[sh, sh[-1]],
                where="post",
                color=colour[nm],
                label=f"{nm} ({x0[i]:+.2f} -> {x1[i]:+.2f})",
            )
        tot_full = (t[:, con] @ (x0[con] - x1[con])) * 100
        print(
            f"[{cfg}] normalisation part of the M0-M1 nuisance shape: {(w * tot_full).sum():+.2f} %"
        )
        tot = shape_only(tot_full)
        ax.step(
            edges,
            np.r_[tot, tot[-1]],
            where="post",
            color="k",
            lw=2.5,
            label="sum, all constrained nuisances",
        )
        resid = r["resid_rel"] * 100
        ax.errorbar(
            ctr,
            resid,
            yerr=100 / np.sqrt(r["data"]),
            fmt="o",
            color="gray",
            ms=4,
            label="(data-postfit)/postfit",
        )
        ax.axhline(0, color="k", lw=0.6)
        ax.set_ylabel("shape only (%)")
        ax.text(
            0.01,
            0.95,
            cfg,
            transform=ax.transAxes,
            fontsize=18,
            fontweight="bold",
            va="top",
        )
        ax.set_ylim(-1.2, 1.4)
        ax.legend(fontsize=8.5, ncol=2, loc="upper right")
    axs[-1].set_xlabel("$p_T^{\\mu\\mu}$ (GeV)")
    axs[0].set_title(
        "M0 - M1 ptll shape (normalisation removed) from the nuisance pulls that relax when ptll is freed\n(linear: templates from the saturated sub-fit Hessian x (pull M0 - pull M1))",
        fontsize=12,
    )
    save_plot(args.outdir, "pull_shapes", fig=fig, args=args, meta_info=meta)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wd", required=True, help="dir with arrays_<cfg>.npz")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--cfgs", nargs="+", default=["LAT", "NOLAT"])
    args = ap.parse_args()
    res = {}
    summary = {}
    for cfg in args.cfgs:
        d, n0, n1, idx1 = load(args.wd, cfg)
        z, A = part_A(d)
        B = part_B(d, float(d["q"]))
        C = part_C(d, n0, idx1)
        t_rel, bbfac = part_D(d, n0, idx1)
        con = d["var_prefit"] > 0
        res[cfg] = dict(
            z=z,
            A=A,
            B=B,
            C=C,
            t_rel=t_rel,
            edges=d["edges"],
            x0=d["x0"],
            x1=d["x1"][idx1],
            n0=n0,
            con=con,
            data=d["h_hist_data_obs"],
            resid_rel=d["h_hist_data_obs"] / d["h_hist_postfit_inclusive"] - 1,
        )
        summary[cfg] = dict(
            q=float(d["q"]),
            chi2lin=float(d["chi2"]),
            A=A,
            B=dict(
                qW=B["qW"],
                qW_s=B["qW_s"],
                smooth_s=B["smooth_s"],
                win_s=B["win_s"],
                win={k: list(v) for k, v in B["win"].items()},
                smooth={k: v for k, v in B["smooth"].items()},
                top_modes=[
                    (
                        int(k),
                        float(B["lam"][k]),
                        int(B["nsc"][k]),
                        float(B["contrib"][k]),
                    )
                    for k in np.argsort(-B["contrib"])[:8]
                ],
                single=[float(v) for v in B["single"]],
            ),
            C=dict(
                groups=C["groups"],
                all_constrained_x2=C["all_constrained_x2"],
                freeze_NPlambda_dq=C["freeze_NPlambda_dq"],
                top_singles=C["singles"][:25],
            ),
            bbfac=[float(v) for v in bbfac],
            prior_relief=float(
                np.sum(np.where(con, d["x0"] ** 2 - d["x1"][idx1] ** 2, 0.0))
            ),
        )
    with open(os.path.join(args.outdir, "forensics_numbers.json"), "w") as f:
        json.dump(summary, f, indent=1)
    plots(args.outdir, res, args)
    # terse printout
    for cfg, sm in summary.items():
        print(
            f"===== {cfg}: rabbit q {sm['q']:.2f}, linear chi2 {sm['chi2lin']:.2f}, quadratic(x) {sm['B']['qW']:.2f}, quadratic(s) {sm['B']['qW_s']:.2f}, prior relief {sm['prior_relief']:.2f}"
        )
        print(
            "  A:",
            {
                k: (round(v, 3) if isinstance(v, float) else v)
                for k, v in sm["A"].items()
                if k != "legendre_absorbed_dataonly"
            },
            "legendre(data-only) absorbed:",
            {k: round(v, 1) for k, v in sm["A"]["legendre_absorbed_dataonly"].items()},
        )
        print(
            "  windows (q absorbed, nbins):",
            {k: (round(v[0], 1), v[1]) for k, v in sm["B"]["win"].items()},
        )
        print(
            "  windows s-space:", {k: round(v, 1) for k, v in sm["B"]["win_s"].items()}
        )
        print(
            "  smooth s-space k=1..12:",
            [round(sm["B"]["smooth_s"][K], 1) for K in sorted(sm["B"]["smooth_s"])],
        )
        for nm, dd in sm["B"]["smooth"].items():
            print(f"  smooth[{nm}] k=1..12:", [round(dd[K], 1) for K in sorted(dd)])
        print(
            "  top modes (idx, lambda, signchanges, contrib):",
            [(a, f"{b:.3g}", c, round(e, 1)) for a, b, c, e in sm["B"]["top_modes"]],
        )
        print(
            "  single-bin top:",
            sorted(
                [(round(v, 1), j) for j, v in enumerate(sm["B"]["single"])],
                reverse=True,
            )[:8],
        )
        print("  groups dq (x2 / x3 / x10):")
        for g, r in sm["C"]["groups"].items():
            print(
                f"    {g:45s} n={r['n']:5d} pull2 M0 {r['pull2_M0']:7.2f} M1 {r['pull2_M1']:7.2f}  dq {r['x2']['dq']:+6.2f} {r['x3']['dq']:+6.2f} {r['x10']['dq']:+6.2f}   (dM0 x10 {r['x10']['dM0']:.2f}, dM1 {r['x10']['dM1']:.2f})"
            )
        print(
            "  all constrained x2:",
            sm["C"]["all_constrained_x2"],
            " freeze NP-lambda dq",
            round(sm["C"]["freeze_NPlambda_dq"], 2),
        )
        print("  top singles by x10 dq:")
        for r in sm["C"]["top_singles"][:15]:
            print(
                f"    {r['name']:48s} pull {r['pull0']:+.2f}->{r['pull1']:+.2f} sig {r['sig0']:.2f}/{r['sig1']:.2f} dpen {r['dpen']:+.2f} dq x2 {r['x2']:+.2f} x3 {r['x3']:+.2f} x10 {r['x10']:+.2f}"
            )
        print(
            "  BB info factor per ptll bin: min %.3f max %.3f"
            % (min(sm["bbfac"]), max(sm["bbfac"]))
        )


if __name__ == "__main__":
    main()
