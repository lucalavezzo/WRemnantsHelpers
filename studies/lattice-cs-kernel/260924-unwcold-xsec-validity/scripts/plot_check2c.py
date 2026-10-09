"""Warm unwalled fit LATL4ZUNWWARM: gen spectra at its tune (alpha_s at anchor) vs its lambda4 scan and the walled fit."""

import argparse, os, sys
import numpy as np, hist

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_output import save_plot
from wums import plot_tools

p = argparse.ArgumentParser()
p.add_argument(
    "--outdir", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
args = p.parse_args()
T = args.outdir
dc = np.load(f"{T}/check2c_warm.npz")
db = np.load(f"{T}/check2b_followup.npz")
b = dc["bins"]
Yb = np.unique(b[:, 2:4], axis=0)
S = {k.split("__")[0]: db[k] for k in db.files if k.endswith("__sigma")}
S.update({k.split("__")[0]: dc[k] for k in dc.files if k.endswith("__sigma")})


def h(k, iy, qmax=8):
    m = b[:, 2] == Yb[iy][0]
    o = np.argsort(b[m, 4])
    lo, hi, v = b[m, 4][o], b[m, 5][o], S[k][m][o]
    s = lo < qmax
    hh = hist.Hist(
        hist.axis.Variable(np.append(lo[s], hi[s][-1]), name="qT"),
        storage=hist.storage.Weight(),
    )
    hh.values()[...] = v[s]
    hh.variances()[...] = 0
    return hh


ks = [
    ("warmB", "LATL4ZUNWWARM tune ($\\lambda_4$=0.096, L2(2.5)=-0.138)"),
    ("warmB_l4_0.03", "same, $\\lambda_4$=0.03"),
    ("warmB_l4_0.01", "same, $\\lambda_4$=0.01"),
    ("warmB_l4_0.002", "same, $\\lambda_4$=0.002"),
    ("wallB", "LATL4ZWALLCOLD tune (walled)"),
]
for iy in [0, 10]:
    fig = plot_tools.makePlotWithRatioToRef(
        [h(k, iy) for k, _ in ks],
        [l for _, l in ks],
        colors=["black", "tab:blue", "tab:orange", "tab:red", "tab:green"],
        linestyles=["solid", "solid", "solid", "solid", "dashed"],
        xlabel=r"$q_T$ (GeV)",
        ylabel=r"$d\sigma/dq_T$ (cache units)",
        rlabel=["x/warm tune"],
        rrange=[[0.6, 1.5]],
        binwnorm=1.0,
        cms_label="Preliminary",
        logoPos=0,
        legtext_size=11,
        nlegcols=1,
        ratio_legend=False,
        extra_text=[
            f"gen level, {Yb[iy][0]:.2f}<|Y|<{Yb[iy][1]:.2f}",
            r"$\alpha_s$ at cache anchor (0.118)",
        ],
        extra_text_loc=(0.5, 0.3),
    )
    save_plot(T, f"warm_Yrow{iy}_lambda4_scan", fig=fig, args=args, meta_info={})
