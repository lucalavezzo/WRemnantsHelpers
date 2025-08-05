import numpy as np
import mplhep as hep
import matplotlib.pyplot as plt
from rabbit import io_tools
import sys, os

hep.style.use(hep.style.CMS)

BASE_DIR = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/"
OUT_DIR = "/home/submit/lavezzo/public_html/alphaS/250803_mc_stats_study/"
ALPHA_S = 0.118
ALPHA_S_SIGMA = 1.5
fittype = "4D" # "1D" or "4D" or "2D"

fitresults4D = {

    # unfolding
    #"unfolding_full_mcstats": "/250508_unfolding_3D/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/ZMassDilepton_ptVGen_absYVGen_helicitySig_theoryfit/fitresults.hdf5",
    
    # unfolding no MC stats
    #"unfolding_full_rebin1": "/250508_unfolding_3D_noBinByBinStat/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/ZMassDilepton_ptVGen_absYVGen_helicitySig_theoryfit/fitresults.hdf5",
    #"unfolding_half_rebin1": "/250508_unfolding_3D_oneMCfileEvery2_noBinByBinStat/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/ZMassDilepton_ptVGen_absYVGen_helicitySig_theoryfit/fitresults.hdf5",
    #"unfolding_all_fit_half_rebin1": "/250513_unfoldingAllEvents_3D_noBinByBinStat_fitHalfEvents/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/ZMassDilepton_ptVGen_absYVGen_helicitySig_theoryfit/fitresults.hdf5",

    # detector-level
    #"full_mcstats": "/250505_4DFit_rebin1_MCstats/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5",
    #"full_2D_mcstats": "/250506_2DFit_rebin1_MCstats/ZMassDilepton_ptll_yll/fitresults.hdf5",
    
    # detector-level no MC stats
    "full_rebin1_new": "250803_dilepton_full/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults_noBinByBinStat.hdf5",
    "half_rebin1_new": "250803_dilepton_half/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults_noBinByBinStat.hdf5",
    "full_rebin1": "/250505_4DFit_rebin1/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5",
    "half_rebin1": "/250505_oneMCfileEvery2/250505_4D_rebin1/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5",
    #"full_2D_rebin1": "/250506_2DFit_rebin1/ZMassDilepton_ptll_yll/fitresults.hdf5",
    #"half_2D_rebin1": "/250505_oneMCfileEvery2/250506_2DFit_rebin1/ZMassDilepton_ptll_yll/fitresults.hdf5",

    # "unfolding_half_mcstats": {
    #     "1": "/250508_unfolding_3D_oneMCfileEvery2/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/ZMassDilepton_ptVGen_absYVGen_helicitySig_theoryfit/fitresults.hdf5",
    # },
    
   
    #"2": "/250505_4DFit_rebin2/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5",
    #"4": "/250505_4DFit_rebin4/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5"

        #"2": "/250505_oneMCfileEvery2/250505_4D_rebin2/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5",
        #"4": "/250505_oneMCfileEvery2/250505_4D_rebin4/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5"
    #"full_mcstats": "/250505_4DFit_rebin1_MCstats/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5",
    #     "2": "/250505_4DFit_rebin2_MCstats/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5",
    #     "4": "/250505_4DFit_rebin4_MCstats/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5"
    # },
    #"half_mcstats": "/250505_oneMCfileEvery2/250505_4D_rebin1_MCstats/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5",
    #     "2": "/250505_oneMCfileEvery2/250505_4D_rebin2_MCstats/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5",
    #     "4": "/250505_oneMCfileEvery2/250505_4D_rebin4_MCstats/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5"
    # },
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
    "full_rebin1": "Detector-level 4D\nAll MC events\n(no bin-by-bin stat.)",
    "half_rebin1": "Detector-level 4D\nHalf MC events\n(no bin-by-bin stat.)",
    "full_rebin1_new": "Detector-level 4D\nAll MC events\n(no bin-by-bin stat.)\n(smooth PDFs)",
    "half_rebin1_new": "Detector-level 4D\nHalf MC events\n(no bin-by-bin stat.)\n(smooth PDFs)",
    "full_2D_rebin1": "Detector-level 2D\nAll MC events\n(no bin-by-bin stat.)",
    "full_2D_mcstats": "Detector-level 2D\nAll MC events",
    "half_2D_rebin1": "Detector-level 2D\nHalf MC events\n(no bin-by-bin stat.)",
    "full_mcstats": "Detector-level 4D\nAll MC events",
    "half_mcstats": "Detector-level 4D\nHalf MC events",
    "unfolding_half_rebin1": "(Unfolding, fit) = (half, all) MC events\n(no bin-by-bin stat.)",
    "unfolding_full_rebin1": "(Unfolding, fit) = (all, all) MC events\n(no bin-by-bin stat.)",
    "unfolding_half_mcstats": "(Unfolding, fit) = (half, all) MC events",
    "unfolding_full_mcstats": "(Unfolding, fit) = (all, all) MC events",
    "unfolding_all_fit_half_rebin1": "(Unfolding, fit) = (all, half) MC events\n(no bin-by-bin stat.)",
}
markers = {
    "full_rebin1": "o",
    "half_rebin1": "o",
    "full_rebin1_new": "o",
    "half_rebin1_new": "o",
    "full_2D_rebin1": "s",
    "full_2D_mcstats": "s",
    "half_2D_rebin1": "s",
    "full_mcstats": "s",
    "half_mcstats": "s",
    "unfolding_half_rebin1": "^",
    "unfolding_full_rebin1": "^",
    "unfolding_half_mcstats": "^",
    "unfolding_full_mcstats": "^",
    "unfolding_all_fit_half_rebin1": "^"
}
colors = {
    "full_rebin1": "blue",
    "half_rebin1": "red",
    "full_rebin1_new": "darkblue",
    "half_rebin1_new": "darkred",
    "full_2D_rebin1": "blue",
    "full_2D_mcstats": "blue",
    "half_2D_rebin1": "red",
    "full_mcstats": "blue",
    "half_mcstats": "red",
    "unfolding_full_rebin1": "blue",
    "unfolding_half_rebin1": "red",
    "unfolding_full_mcstats": "blue",
    "unfolding_half_mcstats": "red",
    "unfolding_all_fit_half_rebin1": "red"
}

def main():

    if fittype == "1D":
        fitresults = fitresults1D
    elif fittype == "2D":
        fitresults = fitresults2D
    elif fittype == "4D":
        fitresults = fitresults4D

    for mc_stat, file in fitresults.items():

        uncerts[mc_stat] = {}

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
        uncerts[mc_stat] = total * ALPHA_S_SIGMA

    fig, ax = plt.subplots(1,1,figsize=(15, 10))
    ax.set_xlabel(r"Uncertainty on $\alpha_\mathrm{S}$ in $10^{-3}$")

    xlabels = [mc_stat_labels[b] for b in uncerts.keys()]
    ax.set_yticks(np.arange(len(xlabels)))
    ax.set_yticklabels(xlabels)

    for i, mc_stat in enumerate(uncerts.keys()):
        ax.scatter(uncerts[mc_stat], i, marker=markers[mc_stat], color=colors[mc_stat], s=100)

    # ax.axvline(0.9, linestyle='--', color='black')
    # ax.text(0.89, 0.3, r"ATLAS (N4LLa)", fontsize=20, color='black', ha='right', va='center')

    # ax.axvline(1.1, linestyle='--', color='black')
    # ax.text(1.09, 0.3, r"ATLAS (N3LL+N3LO)", fontsize=20, color='black', ha='right', va='center')

    fig.tight_layout()
    if not os.path.isdir(OUT_DIR):
        os.mkdir(OUT_DIR)
    fig.savefig(OUT_DIR + f"mc_stat_study_full_{fittype}.png", dpi=300, bbox_inches="tight")   
    fig.savefig(OUT_DIR + f"mc_stat_study_full_{fittype}.pdf", bbox_inches="tight")   

if __name__ == "__main__":
    main()