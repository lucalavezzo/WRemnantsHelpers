import argparse
import os
from datetime import datetime
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np

from wums import boostHistHelpers as hh
from utilities.io_tools import input_tools
from wums import logging, output_tools, plot_tools  # isort: skip


def parse_args():
    parser = argparse.ArgumentParser(description="Plot z_bb comparison histograms.")
    parser.add_argument(
        "--massive-file",
        required=True,
        help="HDF5 file for massive-b sample (Zbb_MiNNLO).",
    )
    parser.add_argument(
        "--massless-file",
        required=True,
        help="HDF5 file for massless sample (Zmumu_MiNNLO).",
    )
    parser.add_argument(
        "--outdir",
        default=None,
        help="Output directory. Default: $MY_PLOT_DIR/<date>_z_bb/hadrons/<tag>",
    )
    parser.add_argument(
        "--tag",
        default=datetime.now().strftime("%H%M%S"),
        help="Tag to append in default output path.",
    )
    parser.add_argument(
        "--normalize",
        action="store_true",
        help="Normalize swapped massive component to nominal bottom component.",
    )
    return parser.parse_args()


args = parse_args()
f_mass = args.massive_file
f_massless = args.massless_file
normalize = args.normalize

res_massive, meta, _ = input_tools.read_infile(f_mass)
res_massless, meta, _ = input_tools.read_infile(f_massless)

outdir = args.outdir or os.path.join(
    os.environ["MY_PLOT_DIR"], datetime.now().strftime("%y%m%d_z_bb/hadrons/"), args.tag
)
if not os.path.exists(outdir):
    os.makedirs(outdir)
    print(f"Output directory '{outdir}' created.")


def read_h(res, proc, h):
    h = hh.scaleHist(
        h, res[proc]["dataset"]["xsec"] * 10e6 / res[proc]["weight_sum"], createNew=True
    )
    return h


def print_nB_table(h, label):
    centers = h.axes[0].centers
    vals = h.values()
    total = np.sum(vals)
    print(f"\n{label}: nBhad_pt5 weighted bin contents")
    for c, v in zip(centers, vals):
        frac = (v / total) if total != 0 else np.nan
        print(f"  nB={int(round(c))}: yield={v:.6e}, frac={frac:.6f}")


# 2d
# for var in [
#     "n_lhe_init_bbbar_vs_n_lhe_fin_bbbar"
# ]:
#     h_massless = read_h(
#         res_massless,
#         f"Zmumu_MiNNLO",
#         res_massless[f"Zmumu_MiNNLO"]["output"][f"{var}"].get(),
#     )
#     fig = plt.figure()
#     ax = fig.add_subplot()
#     for bin in range(len(h_massless.axes[0].centers)):
#         hep.histplot(
#             h_massless[bin, :],
#             label=f"n_lhe_init_bbbar = {bin}",
#             ax=ax
#         )
#     ax.set_yscale("log")
#     ax.legend()
#     rel_oname = f"samples_comparison_{var}"
#     oname = os.path.join(outdir, rel_oname)
#     if not os.path.exists(outdir):
#         os.makedirs(outdir)
#         print(f"Output directory '{outdir}' created.")
#     fig.savefig(oname + ".pdf", bbox_inches="tight")
#     fig.savefig(oname + ".png", bbox_inches="tight", dpi=300)
#     plt.close(fig)
#     output_tools.write_index_and_log(outdir, rel_oname)

# massless only
# for var, xlabel in zip(
#     [
#         "lhe_fin_bbbar_pt",
#         "lhe_fin_bbbar_abseta",
#     ],
#     [
#         "Final b/bbar pt",
#         "Final b/bbar abseta"
#     ],
# ):
#     print("Plotting", var)

#     h_massless = read_h(
#         res_massless,
#         f"Zmumu_MiNNLO",
#         res_massless[f"Zmumu_MiNNLO"]["output"][f"{var}"].get(),
#     )

#     fig = plot_tools.makePlotWithRatioToRef(
#         [h_massless],
#         labels=["Nominal MiNNLO",],
#         ratio_legend=False,
#         nlegcols=1,
#         legtext_size=16,
#         binwnorm=1,
#         rrange=[[0.2, 1.5]],
#         xlabel=xlabel,
#     )
#     rel_oname = f"samples_comparison_{var}"
#     oname = os.path.join(outdir, rel_oname)
#     if not os.path.exists(outdir):
#         os.makedirs(outdir)
#         print(f"Output directory '{outdir}' created.")
#     fig.savefig(oname + ".pdf", bbox_inches="tight")
#     fig.savefig(oname + ".png", bbox_inches="tight", dpi=300)
#     plt.close(fig)
#     output_tools.write_index_and_log(outdir, rel_oname)


plot_specs = [
    ("nBhad_pt5", "Number of B hadrons", True),
    ("leadB_pt5", "Leading B-hadron $p_T$ [GeV]", True),
    ("subB_pt5", "Subleading B-hadron $p_T$ [GeV]", True),
    ("softB_pt5", "Softest B-hadron $p_T$ [GeV]", True),
    ("leadB_pt5_b2", "Leading B-hadron $p_T$ [GeV]", True),
    ("subB_pt5_b2", "Subleading B-hadron $p_T$ [GeV]", True),
    ("m_bb_had", "$m_{bb}$ from B hadrons [GeV]", True),
    ("dR_bb_had", "$\\Delta R_{bb}$ from B hadrons", True),
    ("n_bjets", "Number of gen b-jets", True),
    ("lead_bjet_pt", "Leading gen b-jet pT", True),
    ("sublead_bjet_pt", "Subleading gen b-jet pT", True),
    ("lead_bjet_eta", "Leading gen b-jet eta", False),
    ("sublead_bjet_eta", "Subleading gen b-jet eta", False),
    ("m_bb_jet", "m_bb from gen b-jets", True),
    ("dR_bb_jet", "DeltaR_bb from gen b-jets", True),
    ("n_bjets_parton", "Number of gen b-jets (parton flavour)", True),
    ("lead_bjet_pt_parton", "Leading gen b-jet $p_T$ [GeV] (parton flavour)", True),
    (
        "sublead_bjet_pt_parton",
        "Subleading gen b-jet $p_T$ [GeV] (parton flavour)",
        True,
    ),
    ("lead_bjet_eta_parton", "Leading gen b-jet $\\eta$ (parton flavour)", False),
    ("sublead_bjet_eta_parton", "Subleading gen b-jet $\\eta$ (parton flavour)", False),
    ("m_bb_jet_parton", "$m_{bb}$ from gen b-jets [GeV] (parton flavour)", True),
    ("dR_bb_jet_parton", "$\\Delta R_{bb}$ from gen b-jets (parton flavour)", True),
    ("n_lhe_init_bbbar", "LHE initial-state bb multiplicity", True),
    ("n_lhe_fin_bbbar", "LHE final-state bb multiplicity", True),
    ("n_lhe_bbbar", "LHE total bb multiplicity", True),
    ("lhe_bbbar_fin_min_pt", "LHE final-state min b pT", True),
    ("lhe_bbbar_fin_max_pt", "LHE final-state max b pT", True),
    ("m_bb_lhe", "m_bb from LHE b quarks", True),
    ("dR_bb_lhe", "DeltaR_bb from LHE b quarks", True),
]


# 1D hists
for var, xlabel, logy in plot_specs:
    print("Plotting", var)

    if (
        var not in res_massive["Zbb_MiNNLO"]["output"]
        or var not in res_massless["Zmumu_MiNNLO"]["output"]
    ):
        print(f"Skipping {var}: histogram not found in one of the inputs")
        continue

    h_massive = read_h(
        res_massive,
        f"Zbb_MiNNLO",
        res_massive[f"Zbb_MiNNLO"]["output"][f"{var}"].get(),
    )
    h_massless = read_h(
        res_massless,
        f"Zmumu_MiNNLO",
        res_massless[f"Zmumu_MiNNLO"]["output"][f"{var}"].get(),
    )

    fig = plot_tools.makePlotWithRatioToRef(
        [h_massless, h_massive],
        labels=["Nominal MiNNLO", "Massive b's MiNNLO"],
        ratio_legend=False,
        nlegcols=1,
        legtext_size=16,
        binwnorm=1,
        logy=logy,
        rrange=[[0.2, 1.5]],
        xlabel=xlabel,
    )
    rel_oname = f"samples_comparison_{var}"
    oname = os.path.join(outdir, rel_oname)
    if not os.path.exists(outdir):
        os.makedirs(outdir)
        print(f"Output directory '{outdir}' created.")
    fig.savefig(oname + ".pdf", bbox_inches="tight")
    fig.savefig(oname + ".png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    output_tools.write_index_and_log(outdir, rel_oname)


if (
    "nBhad_pt5" in res_massive["Zbb_MiNNLO"]["output"]
    and "nBhad_pt5" in res_massless["Zmumu_MiNNLO"]["output"]
):
    h_nB_massive = read_h(
        res_massive,
        "Zbb_MiNNLO",
        res_massive["Zbb_MiNNLO"]["output"]["nBhad_pt5"].get(),
    )
    h_nB_massless = read_h(
        res_massless,
        "Zmumu_MiNNLO",
        res_massless["Zmumu_MiNNLO"]["output"]["nBhad_pt5"].get(),
    )

    def frac_nB_geq(h, nmin):
        centers = h.axes[0].centers
        vals = h.values()
        den = np.sum(vals)
        if den == 0:
            return np.nan
        return np.sum(vals[centers >= nmin]) / den

    print("B-hadron multiplicity fractions from nBhad_pt5:")
    print(
        "Nominal MiNNLO: f(nB>=1)={:.4f}, f(nB>=2)={:.4f}".format(
            frac_nB_geq(h_nB_massless, 1), frac_nB_geq(h_nB_massless, 2)
        )
    )
    print(
        "Massive b's MiNNLO: f(nB>=1)={:.4f}, f(nB>=2)={:.4f}".format(
            frac_nB_geq(h_nB_massive, 1), frac_nB_geq(h_nB_massive, 2)
        )
    )
    print_nB_table(h_nB_massless, "Nominal MiNNLO")
    print_nB_table(h_nB_massive, "Massive b's MiNNLO")


h_massive = read_h(
    res_massive,
    f"Zbb_MiNNLO",
    res_massive[f"Zbb_MiNNLO"]["output"]["nominal_gen"].get(),
)
h_massless = read_h(
    res_massless,
    f"Zmumu_MiNNLO",
    res_massless[f"Zmumu_MiNNLO"]["output"]["nominal_gen"].get(),
)

print("Ratio of events with at least 1 b or bbar: ")
print(
    h_massless[{"bottom_sel": 1}].sum().value / h_massive[{"bottom_sel": 1}].sum().value
)
print("% of massive MiNNLO sample being selected for swap:")
print(h_massive[{"bottom_sel": 1}].sum().value / h_massive.sum().value)
print("% of massless MiNNLO sample being selected for swap:")
print(h_massless[{"bottom_sel": 1}].sum().value / h_massless.sum().value)

# comparison of 1b,1bbar events
for vars in [["ptVgen"], ["absYVgen"]]:

    nominal_bottom = h_massless[{"bottom_sel": 1}].project(*vars)
    massive = h_massive[{"bottom_sel": 1}].project(*vars)
    if normalize:
        massive = hh.scaleHist(
            massive, nominal_bottom.sum().value / massive.sum().value
        )

    fig = plot_tools.makePlotWithRatioToRef(
        [nominal_bottom, massive],
        labels=[
            "Nominal MiNNLO (1b, 1bbar)",
            (
                "Massive b's MiNNLO (1b, 1bbar, normalized)"
                if normalize
                else "Massive b's MiNNLO (1b, 1bbar)"
            ),
        ],
        rrange=[[0.5, 1.5]] if vars[0] == "ptVgen" else [[0.95, 1.05]],
        ratio_legend=False,
        nlegcols=1,
        legtext_size=16,
        binwnorm=1,
        xlim=(0, 100) if vars[0] == "ptVgen" else None,
    )
    rel_oname = "bb_" + "_".join(vars)
    if normalize:
        rel_oname += "_normalized"
    oname = os.path.join(outdir, rel_oname)
    fig.savefig(oname + ".pdf", bbox_inches="tight")
    fig.savefig(oname + ".png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    output_tools.write_index_and_log(outdir, rel_oname)

# comparison of final distributions
for vars in [["ptVgen"], ["absYVgen"]]:

    nominal = h_massless.project(*vars)
    nominal_nobottom = h_massless[{"bottom_sel": 0}].project(*vars)
    massive = h_massive[{"bottom_sel": 1}].project(*vars)
    if normalize:
        nominal_bottom = h_massless[{"bottom_sel": 1}].project(*vars)
        massive = hh.scaleHist(
            massive, nominal_bottom.sum().value / massive.sum().value
        )
    corrected = hh.addHists(nominal_nobottom, massive)

    fig = plot_tools.makePlotWithRatioToRef(
        [nominal, nominal_nobottom, corrected],
        labels=[
            "Nominal MiNNLO (inclusive)",
            "Nominal MiNNLO (b's subtracted)",
            (
                "Corrected MiNNLO (inclusive, normalized swap)"
                if normalize
                else "Corrected MiNNLO (inclusive)"
            ),
        ],
        rrange=[[0.95, 1.05]],
        ratio_legend=False,
        nlegcols=1,
        legtext_size=16,
        binwnorm=1,
        xlim=(0, 100) if vars[0] == "ptVgen" else None,
    )
    rel_oname = "inclusive_" + "_".join(vars)
    if normalize:
        rel_oname += "_normalized"
    oname = os.path.join(outdir, rel_oname)
    fig.savefig(oname + ".pdf", bbox_inches="tight")
    fig.savefig(oname + ".png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    output_tools.write_index_and_log(outdir, rel_oname)

# # ratio 2d plot
# vars = ["ptVgen", "absYVgen"]
# nominal = h_massless.project(*vars)
# nominal_nobottom = h_massless[{"bottom_sel": 0}].project(*vars)
# massive = h_massive[{"bottom_sel": 1}].project(*vars)
# corrected = hh.addHists(nominal_nobottom, massive)
# h2_ratio = hh.divideHists(corrected, nominal)
# fig = hep.hist2dplot(h2_ratio)
# rel_oname = "inclusive_2d_" + "_".join(vars)
# oname = os.path.join(outdir, rel_oname)
# plt.xlim(0, 100)
# plt.savefig(oname + ".pdf", bbox_inches="tight")
# plt.savefig(oname + ".png", bbox_inches="tight", dpi=300)
# output_tools.write_index_and_log(outdir, rel_oname)
# plt.close()
# for var in vars:
#     h_ratio = hh.divideHists(corrected.project(var), nominal.project(var))
#     hep.histplot(h_ratio)
#     plt.axhline(1, color="black", alpha=0.5, linestyle="--")
#     plt.xlim(0, 100) if var == "ptVgen" else None
#     plt.ylim(0.9, 1.1)
#     rel_oname = "inclusive_ratio_" + var
#     oname = os.path.join(outdir, rel_oname)
#     plt.savefig(oname + ".pdf", bbox_inches="tight")
#     plt.savefig(oname + ".png", bbox_inches="tight", dpi=300)
#     plt.close()
#     output_tools.write_index_and_log(outdir, rel_oname)

# outpath = "."
# generator = "MiNNLO_Zbb"
# import numpy as np

# h2_ratio_out_vals = h2_ratio.project("absYVgen", "ptVgen").values()[
#     np.newaxis, :, :, np.newaxis
# ]  # (Q, Y, pt, vars)
# output_dict = {
#     f"{generator}_minnlo_ratio": h2_ratio,
#     f"{generator}_hist": corrected,
#     "minnlo_ref_hist": nominal,
# }
# outfile = f"{outpath}/{generator}_CorrZ.pkl.lz4"
# output_tools.write_lz4_pkl_output(outfile, "Z", output_dict, outdir, [], {})

# # angular coefficients
# h_massive = read_h(
#     res_massive,
#     f"Zbb_MiNNLO",
#     res_massive[f"Zbb_MiNNLO"]["output"]["nominal_gen_helicity_xsecs_scale"].get(),
# )
# h_massless = read_h(
#     res_massless,
#     f"ZmumuPostVFP",
#     res_massless[f"ZmumuPostVFP"]["output"]["nominal_gen_helicity_xsecs_scale"].get(),
# )
# for vars in [["ptVgen"], ["absYVgen"]]:

#     h_massive_sigmaUL = h_massive[{"helicity": -1j, "bottom_sel": 1}].project(*vars)
#     h_nominal_sigmaUL = h_massless[{"helicity": -1j}].project(*vars)
#     h_nominal_nobottom_sigmaUL = h_massless[{"helicity": -1j, "bottom_sel": 0}].project(*vars)
#     h_corrected_sigmaUL = hh.addHists(h_nominal_nobottom_sigmaUL, h_massive_sigmaUL)

#     for i in range(0, 8):
#         coeff = f"A{i}"

#         h_massive_hel = h_massive[{"helicity": i, "bottom_sel": 1}].project(*vars)
#         h_nominal_hel = h_massless[{"helicity": i}].project(*vars)
#         h_nominal_nobottom_hel = h_massless[{"helicity": i, "bottom_sel": 0}].project(*vars)
#         h_corrected_hel = hh.addHists(h_nominal_nobottom_hel, h_massive_hel)

#         h_nominal_ai = hh.divideHists(h_nominal_hel, h_nominal_sigmaUL, createNew=True)
#         h_corrected_ai = hh.divideHists(h_corrected_hel, h_corrected_sigmaUL, createNew=True)
#         h_nominal_nobottom_ai = hh.divideHists(
#             h_nominal_nobottom_hel, h_nominal_nobottom_sigmaUL, createNew=True
#         )

#         fig = plot_tools.makePlotWithRatioToRef(
#             [h_nominal_ai, h_nominal_nobottom_ai, h_corrected_ai],
#             labels=[
#                 f"Nominal MiNNLO (inclusive)",
#                 f"Nominal MiNNLO (0b)",
#                 f"Corrected MiNNLO (inclusive)",
#             ],
#             rrange=[[0.95, 1.05]],
#             ratio_legend=False,
#             nlegcols=1,
#             legtext_size=16,
#             #binwnorm=1,
#             xlim=(0, 100) if vars[0] == "ptVgen" else None,
#             ylabel=f"{coeff}",
#         )
#         rel_oname = f"{coeff}_" + "_".join(vars)
#         oname = os.path.join(outdir, rel_oname)
#         fig.savefig(oname + ".pdf", bbox_inches="tight")
#         fig.savefig(oname + ".png", bbox_inches="tight", dpi=300)
#         plt.close(fig)
#         output_tools.write_index_and_log(outdir, rel_oname)
