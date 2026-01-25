import os
from datetime import datetime
import matplotlib.pyplot as plt
import mplhep as hep

from wums import boostHistHelpers as hh
from utilities.io_tools import input_tools
from wums import logging, output_tools, plot_tools  # isort: skip

f_mass = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS//260124_gen_massiveBottom/w_z_gen_dists_maxFiles_m1_massive.hdf5"
f_massless = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260124_gen_massiveBottom/w_z_gen_dists_maxFiles_1000_nnpdf31_massless.hdf5"
normalize = False

res_massive, meta, _ = input_tools.read_infile(f_mass)
res_massless, meta, _ = input_tools.read_infile(f_massless)

outdir = os.path.join(os.environ["MY_PLOT_DIR"], datetime.now().strftime("%y%m%d_z_bb"))
if not os.path.exists(outdir):
    os.makedirs(outdir)
    print(f"Output directory '{outdir}' created.")


def read_h(res, proc, h):
    h = hh.scaleHist(
        h, res[proc]["dataset"]["xsec"] * 10e6 / res[proc]["weight_sum"], createNew=True
    )
    return h


h_massless_gen_bhadrons = read_h(
    res_massless,
    f"ZmumuPostVFP",
    res_massless[f"ZmumuPostVFP"]["output"][f"n_gen_bhadrons"].get(),
)
h_massless_lhe_b = read_h(
    res_massless,
    f"ZmumuPostVFP",
    res_massless[f"ZmumuPostVFP"]["output"][f"n_lhe_b"].get(),
)
h_massless_lhe_init_fin_b = read_h(
    res_massless,
    f"ZmumuPostVFP",
    res_massless[f"ZmumuPostVFP"]["output"][f"n_lhe_init_fin_b"].get(),
)
h_massive_lhe_init_fin_b = read_h(
    res_massive,
    f"Zbb_MiNNLO",
    res_massive[f"Zbb_MiNNLO"]["output"][f"n_lhe_init_fin_b"].get(),
)
print("Fraction of events with at least 1 B hadron (status 1, 2):")
print(h_massless_gen_bhadrons[1j:].sum().value / h_massless_gen_bhadrons.sum().value)
print("Fraction of events with at least 1 LHE b/bbar quark (status 1, -1):")
print(1 - h_massless_lhe_init_fin_b[0, 0].value / h_massless_lhe_init_fin_b.sum().value)
print(
    "Fraction of events with at least 1 LHE b/bbar quark in initial state (status -1):"
)
print(
    h_massless_lhe_init_fin_b[1j:, sum].sum().value
    / h_massless_lhe_init_fin_b.sum().value
)
print("Fraction of events with at least 1 LHE b/bbar quark in final state (status 1):")
print(
    h_massless_lhe_init_fin_b[sum, 1j:].sum().value
    / h_massless_lhe_init_fin_b.sum().value
)
print(
    "Ratio of events with at least 1 LHE b/bbar quark (status 1, -1) between massless and massive:"
)
print(h_massless_lhe_init_fin_b[0j, 2j].value / h_massive_lhe_init_fin_b[0j, 2j].value)
exit()

# n bottom
for var, xlabel in zip(
    ["n_lhe_bottom", "n_lhe_antibottom", "n_lhe_b", "n_gen_bhadrons"],
    [
        "Number of LHE $b$ quarks",
        "Number of LHE $\\bar{b}$ quarks",
        "Number of LHE $b+\\bar{b}$ quarks",
        "Number of gen-level B hadrons (status 1, 2)",
    ],
):
    h_massive = read_h(
        res_massive,
        f"Zbb_MiNNLO",
        res_massive[f"Zbb_MiNNLO"]["output"][f"{var}"].get(),
    )
    h_massless = read_h(
        res_massless,
        f"ZmumuPostVFP",
        res_massless[f"ZmumuPostVFP"]["output"][f"{var}"].get(),
    )
    fig = plot_tools.makePlotWithRatioToRef(
        [h_massless, h_massive],
        labels=["Nominal MiNNLO", "Massive b's MiNNLO"],
        ratio_legend=False,
        nlegcols=1,
        legtext_size=16,
        binwnorm=1,
        logy=True,
        ylim=(1e5, 3e10),
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


h_massive = read_h(
    res_massive,
    f"Zbb_MiNNLO",
    res_massive[f"Zbb_MiNNLO"]["output"]["nominal_gen"].get(),
)
h_massless = read_h(
    res_massless,
    f"ZmumuPostVFP",
    res_massless[f"ZmumuPostVFP"]["output"]["nominal_gen"].get(),
)

print(
    h_massless[{"bottom_sel": 1}].sum().value / h_massive[{"bottom_sel": 1}].sum().value
)

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
            "Massive b's MiNNLO (1b, 1bbar)",
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
            "Nominal MiNNLO (0b)",
            "Corrected MiNNLO (inclusive)",
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

# ratio 2d plot
vars = ["ptVgen", "absYVgen"]
nominal = h_massless.project(*vars)
nominal_nobottom = h_massless[{"bottom_sel": 0}].project(*vars)
massive = h_massive[{"bottom_sel": 1}].project(*vars)
corrected = hh.addHists(nominal_nobottom, massive)
h2_ratio = hh.divideHists(corrected, nominal)
fig = hep.hist2dplot(h2_ratio)
rel_oname = "inclusive_2d_" + "_".join(vars)
oname = os.path.join(outdir, rel_oname)
plt.xlim(0, 100)
plt.savefig(oname + ".pdf", bbox_inches="tight")
plt.savefig(oname + ".png", bbox_inches="tight", dpi=300)
output_tools.write_index_and_log(outdir, rel_oname)
plt.close()
for var in vars:
    h_ratio = hh.divideHists(corrected.project(var), nominal.project(var))
    hep.histplot(h_ratio)
    plt.axhline(1, color="black", alpha=0.5, linestyle="--")
    plt.xlim(0, 100) if var == "ptVgen" else None
    plt.ylim(0.9, 1.1)
    rel_oname = "inclusive_ratio_" + var
    oname = os.path.join(outdir, rel_oname)
    plt.savefig(oname + ".pdf", bbox_inches="tight")
    plt.savefig(oname + ".png", bbox_inches="tight", dpi=300)
    plt.close()
    output_tools.write_index_and_log(outdir, rel_oname)

outpath = "."
generator = "MiNNLO_Zbb"
import numpy as np

h2_ratio_out_vals = h2_ratio.project("absYVgen", "ptVgen").values()[
    np.newaxis, :, :, np.newaxis
]  # (Q, Y, pt, vars)
output_dict = {
    f"{generator}_minnlo_ratio": h2_ratio,
    f"{generator}_hist": corrected,
    "minnlo_ref_hist": nominal,
}
outfile = f"{outpath}/{generator}_CorrZ.pkl.lz4"
output_tools.write_lz4_pkl_output(outfile, "Z", output_dict, outdir, [], {})

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
