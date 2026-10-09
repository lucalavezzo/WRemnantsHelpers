"""Plot rabbit's stored postfit ptll projection (inclusive in yll) vs data, LATL4ZUNWCOLD vs CCCOLDSELF."""

import argparse, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_output import save_plot
from rabbit import io_tools
from wums import plot_tools

CEPH = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
p = argparse.ArgumentParser()
p.add_argument(
    "--outdir", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
args = p.parse_args()
F = {
    "LATL4ZUNWCOLD": f"{CEPH}/260923_lattice_fits/l4zero_unwalled/fitresults_LATL4ZUNWCOLD.hdf5",
    "CCCOLDSELF": f"{CEPH}/260917_cc_selfrestart/fitresults_CCCOLDSELF.hdf5",
    "LATL4ZUNWWARM": f"{CEPH}/260923_lattice_fits/l4zero_unwalled_warm/fitresults_LATL4ZUNWWARM.hdf5",
    "LATL4ZWALLCOLD": f"{CEPH}/260923_lattice_fits/l4zero_walled/fitresults_LATL4ZWALLCOLD.hdf5",
}
H = {}
for k, fn in F.items():
    try:
        ch = io_tools.get_fitresult(fn)["mappings"]["Project ch0 ptll"]["channels"][
            "ch0"
        ]
    except Exception as e:
        print("skip", k, type(e).__name__)
        continue
    H[k] = ch["hist_postfit_inclusive"].get()
    H["data"] = ch["hist_data_obs"].get()
LAB = {
    "LATL4ZUNWCOLD": (
        "Postfit LATL4ZUNWCOLD (lattice, unwalled, cold)",
        "tab:red",
        "solid",
    ),
    "CCCOLDSELF": ("Postfit CCCOLDSELF (reference)", "tab:blue", "dashed"),
    "LATL4ZUNWWARM": (
        "Postfit LATL4ZUNWWARM (lattice, unwalled, warm)",
        "tab:purple",
        "solid",
    ),
    "LATL4ZWALLCOLD": (
        "Postfit LATL4ZWALLCOLD (lattice, walled)",
        "tab:green",
        "dotted",
    ),
}
ks = [k for k in LAB if k in H]
fig = plot_tools.makePlotWithRatioToRef(
    [H["data"]] + [H[k] for k in ks],
    ["Data"] + [LAB[k][0] for k in ks],
    colors=["black"] + [LAB[k][1] for k in ks],
    linestyles=["none"] + [LAB[k][2] for k in ks],
    ratio_legend=False,
    xlabel=r"$p_{T}^{\ell\ell}$ (GeV)",
    ylabel="Events/GeV",
    rlabel=["Postfit/data"],
    rrange=[[0.985, 1.015]],
    binwnorm=1.0,
    dataIdx=0,
    logx=False,
    cms_label="Preliminary",
    logoPos=0,
    extra_text=[
        "Stored rabbit postfit, projection on ptll",
        "(summed over yll; per-yll hists not saved)",
    ],
    extra_text_loc=(0.35, 0.55),
    legtext_size=14,
    yerr=False,
)
save_plot(
    args.outdir,
    "check1_postfit_ptll_projection",
    fig=fig,
    args=args,
    meta_info={k: v for k, v in F.items()},
)
