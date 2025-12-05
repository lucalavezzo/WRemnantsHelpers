from cProfile import label
import sys

sys.path.append("../../WRemnants/")
import os
import re
from wums import ioutils
import argparse
import h5py
import pprint
from wums import ioutils
from wums import boostHistHelpers as hh
import numpy as np
import mplhep as hep
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from wums import logging, output_tools, plot_tools  # isort: skip
from utilities import common, parsing
import hist
from hist import Hist
import datetime

hep.style.use("CMS")


def load_results_h5py(h5file):

    if "results" in h5file.keys():
        return ioutils.pickle_load_h5py(h5file["results"])
    else:
        return {k: ioutils.pickle_load_h5py(v) for k, v in h5file.items()}


# infile = f"{os.environ['MY_OUT_DIR']}/251124_gen_alphaSByHelicity/w_z_gen_dists_scetlib_dyturboN3p1LL_pdfasCorr_maxFiles_m1.hdf5"

# with h5py.File(infile, "r") as h5file:
#     results = load_results_h5py(h5file)

#     nominal = results['ZmumuPostVFP']['output']['nominal_gen'].get()
#     nominal = nominal.project("ptVgen", "absYVgen", "helicity")

#     var_minnlo = results['ZmumuPostVFP']['output']['nominal_gen_pdfCT18ZalphaS002'].get()
#     var_minnlo = var_minnlo[{'alphasVar': 'as0120'}]
#     var_minnlo = var_minnlo.project("ptVgen", "absYVgen", "helicity")

#     nominal_scdy = results['ZmumuPostVFP']['output']['nominal_gen_scetlib_dyturboN3p1LL_pdfasCorr'].get()
#     nominal_scdy = nominal_scdy[{'vars': 0}]
#     nominal_scdy = nominal_scdy.project("ptVgen", "absYVgen", "helicity")

#     var_scdy = results['ZmumuPostVFP']['output']['nominal_gen_scetlib_dyturboN3p1LL_pdfasCorr'].get()
#     var_scdy = var_scdy[{'vars': 2}]
#     var_scdy = var_scdy.project("ptVgen", "absYVgen", "helicity")

infile = f"{os.environ['MY_OUT_DIR']}/251022_pdfsByHelicity/w_z_gen_dists_maxFiles_m1_ct18zByHelicity.hdf5"

with h5py.File(infile, "r") as h5file:
    results = load_results_h5py(h5file)

    nominal = results["ZmumuPostVFP"]["output"]["nominal_gen"].get()
    nominal = nominal.project("ptVgen", "absYVgen", "helicity")

    var_minnlo = results["ZmumuPostVFP"]["output"][
        "nominal_gen_pdfCT18ZalphaS002"
    ].get()
    var_minnlo = var_minnlo[{"alphasVar": "as0120"}]
    var_minnlo = var_minnlo.project("ptVgen", "absYVgen", "helicity")

infile = f"{os.environ['MY_OUT_DIR']}/251124_gen_alphaSByHelicity/w_z_gen_dists_scetlib_dyturboN3p1LL_pdfasCorr_maxFiles_m1.hdf5"

with h5py.File(infile, "r") as h5file:
    results = load_results_h5py(h5file)

    nominal_scdy = results["ZmumuPostVFP"]["output"][
        "nominal_gen_scetlib_dyturboN3p1LL_pdfasCorr"
    ].get()
    nominal_scdy = nominal_scdy[{"vars": 0}]
    nominal_scdy = nominal_scdy.project("ptVgen", "absYVgen", "helicity")

    var_scdy = results["ZmumuPostVFP"]["output"][
        "nominal_gen_scetlib_dyturboN3p1LL_pdfasCorr"
    ].get()
    var_scdy = var_scdy[{"vars": 2}]
    var_scdy = var_scdy.project("ptVgen", "absYVgen", "helicity")


# h_i
for i in range(8):
    hi_nominal = hh.unrolledHist(nominal[{"helicity": i}], binwnorm=1)
    hi_minnlo = hh.unrolledHist(var_minnlo[{"helicity": i}], binwnorm=1)
    hi_nominal_scdy = hh.unrolledHist(nominal_scdy[{"helicity": i}], binwnorm=1)
    hi_scdy = hh.unrolledHist(var_scdy[{"helicity": i}], binwnorm=1)
    fig = plot_tools.makePlotWithRatioToRef(
        [hi_nominal, hi_minnlo, hi_nominal_scdy, hi_scdy],
        ["nominal minnlo", "minnlo aS up", "nominal sc+dy", "sc+dy aS up"],
        rrange=[[0.9, 1.1]],
        ratio_legend=False,
        xlabel="(ptV, absYV)",
    )
    fig.savefig(
        f"{os.environ['MY_PLOT_DIR']}/{datetime.datetime.now().strftime("%y%m%d")}_ais/h{i}.pdf"
    )
    fig.savefig(
        f"{os.environ['MY_PLOT_DIR']}/{datetime.datetime.now().strftime("%y%m%d")}_ais/h{i}.png"
    )

# A_i
for i in range(7):
    ai_nominal = hh.divideHists(
        nominal[{"helicity": i + 1, "absYVgen": hist.sum}],
        nominal[{"helicity": 0, "absYVgen": hist.sum}],
    )
    ai_minnlo = hh.divideHists(
        var_minnlo[{"helicity": i + 1, "absYVgen": hist.sum}],
        var_minnlo[{"helicity": 0, "absYVgen": hist.sum}],
    )
    ai_nominal_scdy = hh.divideHists(
        nominal_scdy[{"helicity": i + 1, "absYVgen": hist.sum}],
        nominal_scdy[{"helicity": 0, "absYVgen": hist.sum}],
    )
    ai_scdy = hh.divideHists(
        var_scdy[{"helicity": i + 1, "absYVgen": hist.sum}],
        var_scdy[{"helicity": 0, "absYVgen": hist.sum}],
    )
    ai_nominal = hh.unrolledHist(ai_nominal, binwnorm=1)
    ai_minnlo = hh.unrolledHist(ai_minnlo, binwnorm=1)
    ai_nominal_scdy = hh.unrolledHist(ai_nominal_scdy, binwnorm=1)
    ai_scdy = hh.unrolledHist(ai_scdy, binwnorm=1)
    fig = plot_tools.makePlotWithRatioToRef(
        [ai_nominal, ai_minnlo, ai_nominal_scdy, ai_scdy],
        ["nominal minnlo", "minnlo aS up", "nominal sc+dy", "sc+dy aS up"],
        rrange=[[0.95, 1.05]],
        ratio_legend=False,
        xlabel="ptV",
        width_scale=2.5,
    )
    fig.get_axes()[0].legend(loc=(1.01, 0))
    fig.tight_layout()
    fig.savefig(
        f"{os.environ['MY_PLOT_DIR']}/{datetime.datetime.now().strftime("%y%m%d")}_ais/a{i}.pdf",
        bbox_inches="tight",
    )
    fig.savefig(
        f"{os.environ['MY_PLOT_DIR']}/{datetime.datetime.now().strftime("%y%m%d")}_ais/a{i}.png",
        bbox_inches="tight",
    )

# A_i^var / A_i^nominal
for i in range(7):
    ai_nominal_minnlo = hh.divideHists(
        nominal[{"helicity": i + 1, "absYVgen": hist.sum}],
        nominal[{"helicity": 0, "absYVgen": hist.sum}],
    )
    ai_minnlo = hh.divideHists(
        var_minnlo[{"helicity": i + 1, "absYVgen": hist.sum}],
        var_minnlo[{"helicity": 0, "absYVgen": hist.sum}],
    )
    ai_scdy = hh.divideHists(
        var_scdy[{"helicity": i + 1, "absYVgen": hist.sum}],
        var_scdy[{"helicity": 0, "absYVgen": hist.sum}],
    )
    ai_nominal_scdy = hh.divideHists(
        nominal_scdy[{"helicity": i + 1, "absYVgen": hist.sum}],
        nominal_scdy[{"helicity": 0, "absYVgen": hist.sum}],
    )

    ai_var_nominal_minnlo = hh.divideHists(ai_minnlo, ai_nominal_minnlo)
    ai_var_nominal_scdy = hh.divideHists(ai_scdy, ai_nominal_scdy)

    ai_var_nominal_minnlo = hh.unrolledHist(ai_var_nominal_minnlo, binwnorm=1)
    ai_var_nominal_scdy = hh.unrolledHist(ai_var_nominal_scdy, binwnorm=1)

    print(ai_var_nominal_minnlo)
    print(ai_var_nominal_scdy)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    hep.histplot(
        [ai_var_nominal_minnlo, ai_var_nominal_scdy],
        label=["minnlo", "sc+dy"],
        ax=ax,
        yerr=False,
        linewidth=2,
    )
    ax.legend()
    ax.set_ylabel("A_i variation / A_i nominal")
    ax.axhline(1, color="black", linestyle="--")
    ax.set_xlabel("ptV")
    plot_tools.fix_axes(ax)
    fig.savefig(
        f"{os.environ['MY_PLOT_DIR']}/{datetime.datetime.now().strftime("%y%m%d")}_ais/a{i}_ratio.pdf"
    )
    fig.savefig(
        f"{os.environ['MY_PLOT_DIR']}/{datetime.datetime.now().strftime("%y%m%d")}_ais/a{i}_ratio.png"
    )
