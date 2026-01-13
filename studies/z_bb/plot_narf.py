import os
from datetime import datetime
import matplotlib.pyplot as plt

from wums import boostHistHelpers as hh
from utilities.io_tools import input_tools
from wums import logging, output_tools, plot_tools  # isort: skip

f_mass = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS//260111_gen_massiveBottom/w_z_gen_dists_maxFiles_m1.hdf5"
f_massless = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260111_gen_massiveBottom/w_z_gen_dists_maxFiles_1000_nnpdf31_massless_nnpdf31.hdf5"

res_massive, meta, _ = input_tools.read_infile(f_mass)
res_massless, meta, _ = input_tools.read_infile(f_massless)


def read_h(res, proc, h):
    h = hh.scaleHist(
        h, res[proc]["dataset"]["xsec"] * 10e6 / res[proc]["weight_sum"], createNew=True
    )
    return h


h_massive = read_h(
    res_massive,
    f"Zbb_MiNNLO",
    res_massive[f"Zbb_MiNNLO"]["output"]["nominal_gen"].get(),
)
h_massless = read_h(
    res_massless,
    f"ZmumuPostVFP",
    res_massless[f"ZmumuPostVFP"]["output"]["nominal_gen_pdfNNPDF31"].get(),
)

for vars in [["ptVgen"], ["absYVgen"]]:

    nominal = h_massless.project(*vars)
    nominal_bottom = h_massless[{"bottom": 1}].project(*vars)
    nominal_nobottom = h_massless[{"bottom": 0}].project(*vars)
    massive = h_massive[{"bottom": 1}].project(*vars)
    massive_nobottom = h_massive[{"bottom": 0}].project(
        *vars
    )  # this is empty, as it should be
    massive = hh.scaleHist(massive, nominal_bottom.sum() / massive.sum().value)
    corrected = hh.addHists(nominal_nobottom, massive)

    fig = plot_tools.makePlotWithRatioToRef(
        [nominal, nominal_bottom, nominal_nobottom, massive, corrected],
        labels=[
            "Nominal",
            "Nominal (bottom)",
            "Nominal (no bottom)",
            "Massive bottom",
            "Nominal corrected",
        ],
        rrange=[[0.95, 1.01]] if vars[0] == "ptVgen" else [[0.95, 1.05]],
        ratio_legend=False,
        nlegcols=1,
        legtext_size=16,
        binwnorm=1,
        xlim=(0, 100) if vars[0] == "ptVgen" else None,
        ylim=(0, 1e9),
    )
    rel_oname = "samples_comparison_" + "_".join(vars) + "_normalized1b"
    outdir = os.path.join(
        os.environ["MY_PLOT_DIR"], datetime.now().strftime("%y%m%d_z_bb")
    )
    oname = os.path.join(outdir, rel_oname)
    if not os.path.exists(outdir):
        os.makedirs(outdir)
        print(f"Output directory '{outdir}' created.")
    fig.savefig(oname + ".pdf", bbox_inches="tight")
    fig.savefig(oname + ".png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    output_tools.write_index_and_log(outdir, rel_oname)
