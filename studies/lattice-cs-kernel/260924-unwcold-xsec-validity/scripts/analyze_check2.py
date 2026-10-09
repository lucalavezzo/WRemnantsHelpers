"""Metrics + plots from check2_model_eval.npz (alpha_s at the cache anchor everywhere)."""

import argparse, json, os, sys
import numpy as np
import hist

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_output import save_plot
from wums import plot_tools
import matplotlib.pyplot as plt

p = argparse.ArgumentParser()
p.add_argument(
    "--outdir", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
p.add_argument("--qtlow", type=float, default=10.0)
args = p.parse_args()
d = np.load(os.path.join(args.outdir, "check2_model_eval.npz"))
bins = d["bins"]
names = list(d["param_names"])
Yb = np.unique(bins[:, 2:4], axis=0)
keys = sorted({k.split("__")[0] for k in d.files if "__sigma" in k})
sig_anchor = d["anchor__sigma"]
ir = {n: i for i, n in enumerate(names)}


def rows(v):
    """list over Y rows of (qT edges, values), qT-ordered."""
    out = []
    for ylo, yhi in Yb:
        m = (bins[:, 2] == ylo) & (bins[:, 3] == yhi)
        o = np.argsort(bins[m, 4])
        e = np.append(bins[m, 4][o], bins[m, 5][o][-1])
        out.append((e, v[m][o]))
    return out


def osc(v):
    """max over Y rows of the max |2nd difference| of sigma/sigma_anchor at qT < qtlow, and its row."""
    best = (0.0, None)
    for iy, ((e, r), (_, a)) in enumerate(zip(rows(v), rows(sig_anchor))):
        rr = (r / a)[e[:-1] < args.qtlow]
        d2 = np.abs(rr[2:] - 2 * rr[1:-1] + rr[:-2])
        if d2.max() > best[0]:
            best = (float(d2.max()), iy)
    return best


def ad_fd(k, c):
    J, f, b = d[f"{k}__J__{c}"], d[f"{k}__fwd__{c}"], d[f"{k}__bwd__{c}"]
    cen = 0.5 * (f + b)
    s = np.max(np.abs(J))
    return dict(
        ad_vs_cfd=float(np.max(np.abs(cen - J)) / s),
        fwd_vs_bwd=float(np.max(np.abs(f - b)) / s),
    )


summary = {}
for k in keys:
    v = d[f"{k}__sigma"]
    pv = d[f"{k}__p"]
    cols = sorted({x.split("__")[2] for x in d.files if x.startswith(k + "__J__")})
    o = osc(v)
    summary[k] = dict(
        L2_25=float(pv[ir["lambda2"]] + 6.25 * pv[ir["delta_lambda2"]]),
        lambda2=float(pv[ir["lambda2"]]),
        delta_lambda2=float(pv[ir["delta_lambda2"]]),
        min_sigma=float(v.min()),
        n_nonpos=int((v <= 0).sum()),
        min_ratio_to_anchor=float((v / sig_anchor).min()),
        max_ratio_to_anchor=float((v / sig_anchor).max()),
        osc_max_d2=o[0],
        osc_row=None if o[1] is None else Yb[o[1]].tolist(),
        adfd={c: ad_fd(k, c) for c in cols},
    )
    s = summary[k]
    print(
        f"{k:22s} L2(2.5)={s['L2_25']:+.4f} minσ={s['min_sigma']:.4g} n≤0={s['n_nonpos']} r∈[{s['min_ratio_to_anchor']:.3f},{s['max_ratio_to_anchor']:.3f}] "
        f"osc={s['osc_max_d2']:.2e}@Y{s['osc_row']}  "
        + "  ".join(
            f"{c}:AD/cFD {x['ad_vs_cfd']:.1e} f/b {x['fwd_vs_bwd']:.1e}"
            for c, x in s["adfd"].items()
        )
    )
json.dump(
    summary, open(os.path.join(args.outdir, "check2_summary.json"), "w"), indent=1
)


def mkh(e, v):
    h = hist.Hist(hist.axis.Variable(e, name="qT"), storage=hist.storage.Weight())
    h.values()[...] = v
    h.variances()[...] = 0.0
    return h


# (a) postfit-tune spectra vs anchor, per Y row (forward rows are where L2<0)
for iy in [0, 8, 9, 10]:
    hs, labs = [], []
    for k, lab in [
        ("anchor", "cache anchor (all params)"),
        ("fitB", "LATL4ZUNWCOLD tune (NP+TNP+PDF), $\\alpha_s$=anchor"),
        ("fitA", "LATL4ZUNWCOLD NP only, rest anchor"),
        ("selfA", "CCCOLDSELF NP only, rest anchor"),
    ]:
        e, v = rows(d[f"{k}__sigma"])[iy]
        m = e[:-1] < 40
        hs.append(mkh(e[: m.sum() + 1], v[m]))
        labs.append(lab)
    L2y = summary["fitB"]["lambda2"] + summary["fitB"]["delta_lambda2"] * Yb[iy][1] ** 2
    fig = plot_tools.makePlotWithRatioToRef(
        hs,
        labs,
        colors=["black", "tab:red", "tab:orange", "tab:blue"],
        linestyles=["solid", "solid", "dashed", "dotted"],
        xlabel=r"$q_T$ (GeV)",
        ylabel=r"$d\sigma/dq_T$ (cache units)",
        rlabel=["x/anchor"],
        rrange=[[0.8, 1.3]],
        binwnorm=1.0,
        cms_label="Preliminary",
        logoPos=0,
        legtext_size=13,
        extra_text=[
            f"gen level, {Yb[iy][0]:.2f}<|Y|<{Yb[iy][1]:.2f}",
            f"fit tune: L2(|Y|={Yb[iy][1]:.2f})={L2y:+.3f}",
            r"$\alpha_s$ held at cache anchor 0.118",
        ],
        extra_text_loc=(0.45, 0.45),
        ratio_legend=False,
    )
    save_plot(
        args.outdir,
        f"check2_sigma_gen_Yrow{iy}",
        fig=fig,
        args=args,
        meta_info={"Y": Yb[iy].tolist()},
    )

# (b) scan summary vs L2(|Y|=2.5)
fig, axs = plt.subplots(3, 1, figsize=(9, 13), sharex=True)
for mode, col, lab in [
    ("dl2", "tab:red", r"via $\delta\lambda_2$ ($\lambda_2$ at fit)"),
    ("l2", "tab:blue", r"via $\lambda_2$ ($\delta\lambda_2$ at fit)"),
]:
    ks = sorted(
        [k for k in keys if k.startswith(f"scan_{mode}_")],
        key=lambda k: summary[k]["L2_25"],
    )
    x = [summary[k]["L2_25"] for k in ks]
    ref0 = rows(d[f"scan_{mode}_+0.000__sigma"])[-1][1][0]
    axs[0].plot(
        x,
        [rows(d[f"{k}__sigma"])[-1][1][0] / ref0 for k in ks],
        "o-",
        color=col,
        label=lab,
    )
    axs[1].semilogy(x, [summary[k]["osc_max_d2"] for k in ks], "o-", color=col)
    for c, mk in [("lambda2", "o-"), ("delta_lambda2", "s--")]:
        axs[2].semilogy(
            x,
            [summary[k]["adfd"][c]["ad_vs_cfd"] for k in ks],
            mk,
            color=col,
            label=f"{lab}: col {c}",
        )
for ax in axs:
    ax.axvline(summary["fitB"]["L2_25"], color="k", ls=":", lw=1)
    ax.axvline(0, color="gray", lw=0.5)
axs[0].set_ylabel(r"$\sigma$(2<|Y|<2.5, $q_T$<0.5)/same at $L_2$=0", fontsize=12)
axs[0].set_ylim(-1, 1.2)
axs[0].legend(fontsize=9)
axs[1].set_ylabel(
    rf"max $|\Delta^2(\sigma/\sigma_{{\rm anchor}})|$, $q_T<${args.qtlow:g}",
    fontsize=12,
)
axs[2].set_ylabel(r"max$|$AD$-$cFD$|$/max$|$AD$|$ (h=1e-4)", fontsize=12)
axs[2].legend(fontsize=7)
axs[2].set_xlabel(
    r"$L_2(|Y|=2.5)=\lambda_2+6.25\,\delta\lambda_2$  (dotted: LATL4ZUNWCOLD postfit)",
    fontsize=13,
)
axs[0].set_title(r"AD cache, LATL4ZUNWCOLD tune, $\alpha_s$ at anchor", fontsize=11)
fig.tight_layout()
save_plot(args.outdir, "check2_L2_scan_summary", fig=fig, args=args, meta_info={})

# (c) forward row spectra along the dl2 scan
iy = len(Yb) - 1
ks = sorted(
    [k for k in keys if k.startswith("scan_dl2_")], key=lambda k: -summary[k]["L2_25"]
)[::2]
hs, labs = [], []
for k in ["scan_dl2_+0.000", "fitB"] + [x for x in ks if x != "scan_dl2_+0.000"]:
    e, v = rows(d[f"{k}__sigma"])[iy]
    m = e[:-1] < 6
    hs.append(mkh(e[: m.sum() + 1], v[m]))
    labs.append(
        "LATL4ZUNWCOLD tune, L2(2.5)=%+.3f" % summary[k]["L2_25"]
        if k == "fitB"
        else f"L2(2.5)={summary[k]['L2_25']:+.3f}"
    )
cm = plt.get_cmap("coolwarm")
fig = plot_tools.makePlotWithRatioToRef(
    hs,
    labs,
    colors=["gray", "black"] + [cm(i / (len(ks) - 2)) for i in range(len(ks) - 1)],
    linestyles=["dashed", "solid"] + ["solid"] * (len(ks) - 1),
    xlabel=r"$q_T$ (GeV)",
    ylabel=r"$d\sigma/dq_T$ (cache units)",
    rlabel=["x/(L2(2.5)=0)"],
    rrange=[[-0.5, 1.5]],
    binwnorm=1.0,
    cms_label="Preliminary",
    logoPos=0,
    legtext_size=11,
    nlegcols=2,
    extra_text=[
        f"gen level, {Yb[iy][0]:.1f}<|Y|<{Yb[iy][1]:.1f}",
        r"scan via $\delta\lambda_2$, $\alpha_s$ at anchor",
    ],
    extra_text_loc=(0.45, 0.35),
    ratio_legend=False,
)
save_plot(args.outdir, "check2_forward_row_dl2_scan", fig=fig, args=args, meta_info={})
