import os
from datetime import datetime
import matplotlib.pyplot as plt

from wums import boostHistHelpers as hh
from utilities.io_tools import input_tools
from wums import logging, output_tools, plot_tools  # isort: skip

f_wplus = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS//251211_gen_massiveCharm/w_z_gen_dists_maxFiles_1000_nnpdf31_wplus_nnpdf31.hdf5"
f_wminus = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS//251211_gen_massiveCharm/w_z_gen_dists_maxFiles_1000_nnpdf31_wminus_nnpdf31.hdf5"
f_massless = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS//251211_gen_massiveCharm/w_z_gen_dists_maxFiles_1000_nnpdf31_massless_nnpdf31.hdf5"

res_plus_massive, meta, _ = input_tools.read_infile(f_wplus)
res_minus_massive, meta, _ = input_tools.read_infile(f_wminus)
res_massless, meta, _ = input_tools.read_infile(f_massless)


def read_h(res, proc, h):
    h = hh.scaleHist(
        h, res[proc]["dataset"]["xsec"] * 10e6 / res[proc]["weight_sum"], createNew=True
    )
    return h


for charge in ["plus", "minus"]:

    res_massive = res_plus_massive if charge == "plus" else res_minus_massive
    h_massive = read_h(
        res_massive,
        f"W{charge}CharmToMuNu",
        res_massive[f"W{charge}CharmToMuNu"]["output"]["prefsr_lep"].get(),
    )
    h_massless = read_h(
        res_massless,
        f"W{charge}munuPostVFP",
        res_massless[f"W{charge}munuPostVFP"]["output"]["prefsr_lep"].get(),
    )

    for vars in [["ptGen"], ["absEtaGen"]]:

        nominal = h_massless.project(*vars)
        nominal_charm = h_massless[{"charm": 1}].project(*vars)
        nominal_nocharm = h_massless[{"charm": 0}].project(*vars)
        massive = h_massive[{"charm": 1}].project(*vars)
        massive_nocharm = h_massive[{"charm": 0}].project(
            *vars
        )  # this is empty, as it should be
        massive = hh.scaleHist(massive, nominal_charm.sum().value / massive.sum().value)
        corrected = hh.addHists(nominal_nocharm, massive)

        fig = plot_tools.makePlotWithRatioToRef(
            [nominal, nominal_charm, nominal_nocharm, massive, corrected],
            labels=[
                "Nominal",
                "Nominal (charm)",
                "Nominal (no charm)",
                "Massive charm",
                "Nominal corrected",
            ],
            rrange=[[0.95, 1.05]],
            ratio_legend=False,
            nlegcols=1,
            legtext_size=16,
        )
        rel_oname = (
            "samples_comparison_" + "_".join(vars) + "_w" + charge + "_normalized1c"
        )
        outdir = os.path.join(
            os.environ["MY_PLOT_DIR"], datetime.now().strftime("%y%m%d_w_charm")
        )
        oname = os.path.join(outdir, rel_oname)
        if not os.path.exists(outdir):
            os.makedirs(outdir)
            print(f"Output directory '{outdir}' created.")
        fig.savefig(oname + ".pdf", bbox_inches="tight")
        fig.savefig(oname + ".png", bbox_inches="tight", dpi=300)
        plt.close(fig)
        output_tools.write_index_and_log(outdir, rel_oname)
