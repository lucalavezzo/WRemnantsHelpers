"""Key plots from the follow-up: forward-row spectrum at the fit tune vs its smooth L2=0 twin, lambda4>0 rescue,
and the edge; plus the baselines (walled lattice fit, CCCOLDSELF) per rapidity row. alpha_s at the cache anchor.
"""

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
d = np.load(f"{T}/check2b_followup.npz")
d0 = np.load(f"{T}/check2_model_eval.npz")
b = d["bins"]
Yb = np.unique(b[:, 2:4], axis=0)
S = {k.split("__")[0]: d[k] for k in d.files if k.endswith("__sigma")}
S.update({k.split("__")[0]: d0[k] for k in d0.files if k.endswith("__sigma")})


def h(k, iy, qmax):
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


common = dict(
    xlabel=r"$q_T$ (GeV)",
    ylabel=r"$d\sigma/dq_T$ (cache units)",
    binwnorm=1.0,
    cms_label="Preliminary",
    logoPos=0,
    legtext_size=12,
    nlegcols=1,
    ratio_legend=False,
)
# (1) KEY: forward row
ks = [
    ("scan_dl2_+0.000", "fit tune but L2(2.5)=0 (smooth twin)"),
    ("fitB", "LATL4ZUNWCOLD tune, L2(2.5)=-0.031, $\\lambda_4$=-2.5e-5"),
    ("fitB_l4_0.001", "same, $\\lambda_4$=+0.001"),
    ("fine_dl2_-0.033", "L2(2.5)=-0.033 (via $\\delta\\lambda_2$)"),
    ("fine_dl2_-0.034", "L2(2.5)=-0.034"),
]
fig = plot_tools.makePlotWithRatioToRef(
    [h(k, 10, 8) for k, _ in ks],
    [l for _, l in ks],
    colors=["gray", "black", "tab:green", "tab:orange", "tab:red"],
    linestyles=["dashed", "solid", "dotted", "solid", "solid"],
    rlabel=["x/smooth twin"],
    rrange=[[-0.1, 1.3]],
    extra_text=[
        "gen level, 2.0<|Y|<2.5",
        r"$\alpha_s$ at cache anchor (0.118)",
        "other params: fit postfit",
    ],
    extra_text_loc=(0.5, 0.3),
    **common,
)
save_plot(T, "key_forward_row_fit_vs_smooth", fig=fig, args=args, meta_info={})
# (2) baselines, three rows
for iy in [0, 8, 10]:
    ks = [
        ("anchor", "cache anchor"),
        ("fitB", "LATL4ZUNWCOLD (unwalled lattice)"),
        ("wallB", "LATL4ZWALLCOLD (walled lattice, snapshot)"),
        ("selfB", "CCCOLDSELF (unwalled reference)"),
    ]
    fig = plot_tools.makePlotWithRatioToRef(
        [h(k, iy, 8) for k, _ in ks],
        [l for _, l in ks],
        colors=["gray", "black", "tab:green", "tab:blue"],
        linestyles=["dashed", "solid", "solid", "solid"],
        rlabel=["x/anchor"],
        rrange=[[0.3, 2.0]],
        extra_text=[
            f"gen level, {Yb[iy][0]:.2f}<|Y|<{Yb[iy][1]:.2f}",
            r"each fit's full tune, $\alpha_s$ at anchor",
        ],
        extra_text_loc=(0.5, 0.3),
        **common,
    )
    save_plot(T, f"baselines_Yrow{iy}", fig=fig, args=args, meta_info={})
