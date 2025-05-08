import numpy as np
import mplhep as hep
import matplotlib.pyplot as plt
from combinetf2 import io_tools
import sys

hep.style.use(hep.style.ROOT)

BASE_DIR = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/"
OUT_DIR = "/home/submit/lavezzo/public_html/alphaS/mc_stats_study/"
fittype = "2D" # "1D" or "4D"

fitresults4D = {
    "unfolding_full_mcstats": {
        "1": "/250508_unfolding_3D/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/ZMassDilepton_ptVGen_absYVGen_helicitySig_theoryfit/fitresults.hdf5",
    },
    "unfolding_half_mcstats": {
        "1": "/250508_unfolding_3D_oneMCfileEvery2/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/ZMassDilepton_ptVGen_absYVGen_helicitySig_theoryfit/fitresults.hdf5",
    },
    "unfolding_full": {
        "1": "/250508_unfolding_3D_noBinByBinStat/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/ZMassDilepton_ptVGen_absYVGen_helicitySig_theoryfit/fitresults.hdf5",
    },
    "unfolding_half": {
        "1": "/250508_unfolding_3D_oneMCfileEvery2_noBinByBinStat/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/ZMassDilepton_ptVGen_absYVGen_helicitySig_theoryfit/fitresults.hdf5",
    },
    "full": {
        "1": "/250505_4DFit_rebin1/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5",
        "2": "/250505_4DFit_rebin2/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5",
        "4": "/250505_4DFit_rebin4/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5"
    },
    "half": {
        "1": "/250505_oneMCfileEvery2/250505_4D_rebin1/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5",
        "2": "/250505_oneMCfileEvery2/250505_4D_rebin2/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5",
        "4": "/250505_oneMCfileEvery2/250505_4D_rebin4/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5"
    },
    "full_mcstats": {
        "1": "/250505_4DFit_rebin1_MCstats/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5",
        "2": "/250505_4DFit_rebin2_MCstats/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5",
        "4": "/250505_4DFit_rebin4_MCstats/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5"
    },
    "half_mcstats": {
        "1": "/250505_oneMCfileEvery2/250505_4D_rebin1_MCstats/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5",
        "2": "/250505_oneMCfileEvery2/250505_4D_rebin2_MCstats/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5",
        "4": "/250505_oneMCfileEvery2/250505_4D_rebin4_MCstats/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5"
    },
}
fitresults1D = {
    "full": {
        "1": "/250506_1DFit_rebin1/ZMassDilepton_ptll/fitresults.hdf5",
        "2": "/250506_1DFit_rebin2/ZMassDilepton_ptll/fitresults.hdf5",
        "4": "/250506_1DFit_rebin4/ZMassDilepton_ptll/fitresults.hdf5"
    },
    "half": {
        "1": "/250505_oneMCfileEvery2/250506_1DFit_rebin1/ZMassDilepton_ptll/fitresults.hdf5",
        "2": "/250505_oneMCfileEvery2/250506_1DFit_rebin2/ZMassDilepton_ptll/fitresults.hdf5",
        "4": "/250505_oneMCfileEvery2/250506_1DFit_rebin4/ZMassDilepton_ptll/fitresults.hdf5"
    },
    "full_mcstats": {
        "1": "/250506_1DFit_rebin1_MCstats/ZMassDilepton_ptll/fitresults.hdf5",
        "2": "/250506_1DFit_rebin2_MCstats/ZMassDilepton_ptll/fitresults.hdf5",
        "4": "/250506_1DFit_rebin4_MCstats/ZMassDilepton_ptll/fitresults.hdf5"
    },
    "half_mcstats": {
        "1": "/250505_oneMCfileEvery2/250506_1DFit_rebin1_MCstats/ZMassDilepton_ptll/fitresults.hdf5",
        "2": "/250505_oneMCfileEvery2/250506_1DFit_rebin2_MCstats/ZMassDilepton_ptll/fitresults.hdf5",
        "4": "/250505_oneMCfileEvery2/250506_1DFit_rebin4_MCstats/ZMassDilepton_ptll/fitresults.hdf5"
    },
}
fitresults2D = {
    "unfolding_full_mcstats": {
        "1": "/250507_unfolding_2D/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/ZMassDilepton_ptVGen_absYVGen_helicitySig_theoryfit/fitresults.hdf5",
    },
    "unfolding_half_mcstats": {
        "1": "/250507_unfolding_2D_oneMCfileEvery2/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/ZMassDilepton_ptVGen_absYVGen_helicitySig_theoryfit/fitresults.hdf5",
    },
    "unfolding_full": {
        "1": "/250507_unfolding_2D_noBinByBinStat/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/ZMassDilepton_ptVGen_absYVGen_helicitySig_theoryfit/fitresults.hdf5",
    },
    "unfolding_half": {
        "1": "/250507_unfolding_2D_oneMCfileEvery2_noBinByBinStat/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/ZMassDilepton_ptVGen_absYVGen_helicitySig_theoryfit/fitresults.hdf5",
    },
    "full": {
        "1": "/250506_2DFit_rebin1/ZMassDilepton_ptll_yll/fitresults.hdf5",
        "2": "/250506_2DFit_rebin2/ZMassDilepton_ptll_yll/fitresults.hdf5",
        "4": "/250506_2DFit_rebin4/ZMassDilepton_ptll_yll/fitresults.hdf5"
    },
    "half": {
        "1": "/250505_oneMCfileEvery2/250506_2DFit_rebin1/ZMassDilepton_ptll_yll/fitresults.hdf5",
        "2": "/250505_oneMCfileEvery2/250506_2DFit_rebin2/ZMassDilepton_ptll_yll/fitresults.hdf5",
        "4": "/250505_oneMCfileEvery2/250506_2DFit_rebin4/ZMassDilepton_ptll_yll/fitresults.hdf5"
    },
    "full_mcstats": {
        "1": "/250506_2DFit_rebin1_MCstats/ZMassDilepton_ptll_yll/fitresults.hdf5",
        "2": "/250506_2DFit_rebin2_MCstats/ZMassDilepton_ptll_yll/fitresults.hdf5",
        "4": "/250506_2DFit_rebin4_MCstats/ZMassDilepton_ptll_yll/fitresults.hdf5"
    },
    "half_mcstats": {
        "1": "/250505_oneMCfileEvery2/250506_2DFit_rebin1_MCstats/ZMassDilepton_ptll_yll/fitresults.hdf5",
        "2": "/250505_oneMCfileEvery2/250506_2DFit_rebin2_MCstats/ZMassDilepton_ptll_yll/fitresults.hdf5",
        "4": "/250505_oneMCfileEvery2/250506_2DFit_rebin4_MCstats/ZMassDilepton_ptll_yll/fitresults.hdf5"
    },
}
uncerts = {}

xlabels = {
    "1": "Default binning",
    "2": "1/2 bins",
    "4": "1/4 bins",
}
mc_stat_labels = {
    "full": "All MC events (--noBinByBinStat)",
    "half": "Half MC events (--noBinByBinStat)",
    "full_mcstats": "All MC events",
    "half_mcstats": "Half MC events",
    "unfolding_half": "Unfolding - Half MC events (--noBinByBinStat)",
    "unfolding_full": "Unfolding - All MC events (--noBinByBinStat)",
    "unfolding_half_mcstats": "Unfolding - Half MC events",
    "unfolding_full_mcstats": "Unfolding - All MC events",
}
markers = {
    "full": "o",
    "half": "o",
    "full_mcstats": "s",
    "half_mcstats": "s",
    "unfolding_half": "+",
    "unfolding_full": "+",
    "unfolding_half_mcstats": "x",
    "unfolding_full_mcstats": "x",
}
colors = {
    "full": "blue",
    "half": "red",
    "full_mcstats": "blue",
    "half_mcstats": "red",
    "unfolding_full": "blue",
    "unfolding_half": "red",
    "unfolding_full_mcstats": "blue",
    "unfolding_half_mcstats": "red",
}

if fittype == "1D":
    fitresults = fitresults1D
elif fittype == "2D":
    fitresults = fitresults2D
elif fittype == "4D":
    fitresults = fitresults4D
for mc_stat, files in fitresults.items():

    uncerts[mc_stat] = {}

    for rebin, file in files.items():   

        print(BASE_DIR+file)     

        fitresult, meta = io_tools.get_fitresult(BASE_DIR+file, None, meta=True)

        out = io_tools.read_impacts_poi(
            fitresult,
            'pdfAlphaS',
            False,
            pulls=True,
            asym=False,
            add_total=True,
        )
        pulls, pulls_prefit, constraints, constraints_prefit, impacts, labels = out

        idx = np.where(labels == 'pdfAlphaS')
        total = impacts[idx]
        uncerts[mc_stat][rebin] = total * 1.5

fig, (ax, axr) = plt.subplots(2,1,figsize=(15, 10),gridspec_kw={'height_ratios': [2, 1]}, sharex=True)
ax.set_ylabel(r"Uncertainty on $\alpha_\mathrm{S}$ in $10^{-3}$")

xlabels = [xlabels[b] for b in uncerts["full_mcstats"].keys()]
axr.set_xticks(np.arange(len(xlabels)))
axr.set_xticklabels(xlabels)

for mc_stat in uncerts.keys():
    y = []
    for rebin in uncerts[mc_stat].keys():
        y.append(uncerts[mc_stat][rebin])
    ax.scatter(np.arange(len(y)), y, label=mc_stat_labels[mc_stat], marker=markers[mc_stat], color=colors[mc_stat])

if "full_mcstats" in uncerts.keys():
    ratio_mcstats = [uncerts["full_mcstats"][b] / uncerts["half_mcstats"][b] for b in uncerts['full_mcstats'].keys()]
    axr.scatter(np.arange(len(ratio_mcstats)), ratio_mcstats, label=f"{mc_stat_labels["full_mcstats"]}/{mc_stat_labels['half_mcstats']}", marker=markers["full_mcstats"], color='purple')
if "unfolding_full_mcstats" in uncerts.keys():
    ratio_unfolding = [uncerts['unfolding_full_mcstats'][b] / uncerts['unfolding_half_mcstats'][b] for b in uncerts['unfolding_full_mcstats'].keys()]
    axr.scatter(np.arange(len(ratio_unfolding)), ratio_unfolding, label=f"{mc_stat_labels["unfolding_full_mcstats"]}/{mc_stat_labels['unfolding_half_mcstats']}", marker=markers["unfolding_full_mcstats"], color='purple')
if 'full' in uncerts.keys():
    ratio_nomcstats = [uncerts['full'][b] / uncerts['half'][b] for b in uncerts['full'].keys()]
    axr.scatter(np.arange(len(ratio_nomcstats)), ratio_nomcstats, label=f"{mc_stat_labels["full"]}/{mc_stat_labels['half']}", marker=markers["full"], color='purple')
if 'unfolding_full' in uncerts.keys():
    ratio_unfolding = [uncerts['unfolding_full'][b] / uncerts['unfolding_half'][b] for b in uncerts['unfolding_full'].keys()]
    axr.scatter(np.arange(len(ratio_unfolding)), ratio_unfolding, label=f"{mc_stat_labels["unfolding_full"]}/{mc_stat_labels['unfolding_half']}", marker=markers["unfolding_full"], color='purple')

axr.axhline(1, color='black', linestyle='--', linewidth=0.5)
ax.set_title(f"{fittype} Fit")
ax.legend(loc=(1.02, 0), fontsize='x-small')
axr.set_ylabel("Ratio Full/Half MC", fontsize='small')
fig.tight_layout()
fig.savefig(OUT_DIR + f"mc_stat_study_{fittype}.png", dpi=300, bbox_inches="tight")   
fig.savefig(OUT_DIR + f"mc_stat_study_{fittype}.pdf", bbox_inches="tight")   