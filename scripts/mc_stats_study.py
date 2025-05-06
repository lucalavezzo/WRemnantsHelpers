import numpy as np
import mplhep as hep
import matplotlib.pyplot as plt
from combinetf2 import io_tools
import sys

hep.style.use(hep.style.ROOT)

BASE_DIR = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/"
OUT_DIR = "/home/submit/lavezzo/public_html/alphaS/mc_stats_study/"

fitresults4D = {
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
uncerts = {}

xlabels = {
    "1": "Default binning",
    "2": "1/2 bins",
    "4": "1/4 bins",
}
mc_stat_labels = {
    "full": "All MC events (--noBinByBinStat)",
    "half": "1/2 MC events (--noBinByBinStat)",
    "full_mcstats": "All MC events",
    "half_mcstats": "1/2 MC events",
}
markers = {
    "full": "o",
    "half": "o",
    "full_mcstats": "*",
    "half_mcstats": "*",
}
colors = {
    "full": "blue",
    "half": "red",
    "full_mcstats": "blue",
    "half_mcstats": "red",
}


for mc_stat, files in fitresults4D.items():

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
        uncerts[mc_stat][rebin] = total

fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111)
ax.set_ylabel(r"Uncertainty on $\alpha_\mathrm{S}$ in $10^{-3}$")

xlabels = [xlabels[b] for b in uncerts["full"].keys()]
ax.set_xticks(np.arange(len(xlabels)))
ax.set_xticklabels(xlabels)

for mc_stat in uncerts.keys():
    y = []
    for rebin in uncerts[mc_stat].keys():
        y.append(uncerts[mc_stat][rebin])
    ax.scatter(np.arange(len(xlabels)), y, label=mc_stat_labels[mc_stat], marker=markers[mc_stat], color=colors[mc_stat])

ax.set_title("4D Fit")
ax.legend()
fig.tight_layout()
fig.savefig(OUT_DIR + "mc_stat_study_4D.png", dpi=300, bbox_inches="tight")   
fig.savefig(OUT_DIR + "mc_stat_study_4D.pdf", bbox_inches="tight")   