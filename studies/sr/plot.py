"""
Plot the results from a fit.
"""

import pysr
import pysr.sr
import os, sys
import argparse
import h5py
import numpy as np
import copy
import hist
import matplotlib.pyplot as plt
import lz4.frame
import pickle
import itertools

sys.path.append("../../WRemnants/")

from wums import ioutils
from wums import plot_tools
from wums import boostHistHelpers as hh

def load_results_h5py(h5file):
    if "results" in h5file.keys():
        return ioutils.pickle_load_h5py(h5file["results"])
    else:
        return {k: ioutils.pickle_load_h5py(v) for k, v in h5file.items()}

parser = argparse.ArgumentParser(
    description="Read in a hdf5 file."
)
parser.add_argument(
    "model",
    type=str,
    help="model file directory.",
)
parser.add_argument(
    "-n",
    type=int,
    default=5,
    help="Show top -n equations."
)
parser.add_argument(
    "--axes",
    nargs="+",
    type=str,
    default=[],
    help="Axes to plot. Default is all the present axes, unrolled."
)
parser.add_argument(
    "--ylim",
    nargs=2,
    type=float,
    default=None,
    help="y limits."
)
parser.add_argument(
    "-p",
    "--postfix",
    default=None,
    help="Postfix to add to the output file names.",
)
parser.add_argument(
    "-o",
    "--outdir",
    type=str,
    required=True,
    help="Output directory for the plots. Default is current directory.",
)
args = parser.parse_args()

# read the input hisotgram from the run directory
with lz4.frame.open(f"{args.model}/hist.pkl.lz4") as f:
    input = pickle.load(f)
    h = input['input']['h']
    h_unroll = input['input']['h_unroll']
    isratio = input['input']['isratio']

x = np.array(list(itertools.product(*[ax.centers for ax in h.axes])))

# load the omdel from the run directory
model = pysr.PySRRegressor()
model = model.from_file(run_directory=args.model)
model.set_params(extra_sympy_mappings={'inv': lambda x: 1/x})

# plot the top equations sorted by sortbys, and the best equation
eqns = model.equations_
sortbys = ['loss', 'score']
for sortby in sortbys:

    colors = plt.cm.rainbow(np.linspace(0, 1, args.n+1))
    h_preds = []
    labels = []
    sorted_args = np.argsort(eqns[sortby])
    if sortby == 'score':
        sorted_args = sorted_args[::-1]
        round_digits = 3
    else:
        round_digits = 9
    sorted_args = sorted_args[:args.n]

    # get the best
    pred = model.predict(x) 
    pred = np.reshape(pred, [len(ax.centers) for ax in h.axes])
    h_pred = hist.Hist(*[ax for ax in h.axes], storage=hist.storage.Weight())
    h_pred.view(flow=False)[...] = np.stack(
        [pred, np.zeros_like(pred)],
        axis=-1
    )
    h_preds.append(h_pred)
    best_idx = pysr.sr.idx_model_selection(eqns, "best")
    labels.append(f"{sortby}={round(eqns[sortby][best_idx],round_digits)} (Best): ${model.latex()}$")

    # plot the top N (minus the best, if in top N)
    if best_idx in sorted_args.values:
        sorted_args = sorted_args[sorted_args != best_idx]
        colors = colors[:-1]
    for i in sorted_args:
        pred = model.predict(x, i)
        pred = np.reshape(pred, [len(ax.centers) for ax in h.axes])
        h_pred = hist.Hist(*[ax for ax in h.axes], storage=hist.storage.Weight())
        h_pred.view(flow=False)[...] = np.stack(
            [pred, np.zeros_like(pred)],
            axis=-1
        )
        h_preds.append(h_pred)
        labels.append(f"{sortby}={round(eqns[sortby][i],round_digits)}: ${model.latex(i)}$")

    # unroll before plotting
    h_plot = copy.deepcopy(h)

    # TODO needed?
    if isratio:
        h_plot = hh.unrolledHist(h_plot)
    else:
        h_plot = hh.unrolledHist(h_plot, binwnorm=1)
    h_plot = hh.normalize(h_plot, scale=1)
    vals = np.reshape(h_plot.values(), [len(ax.centers) for ax in h.axes])
    h_plot = hist.Hist(*[ax for ax in h.axes], storage=hist.storage.Weight())
    h_plot.view(flow=False)[...] = np.stack(
        [vals, np.zeros_like(vals)],
        axis=-1
    )

    if args.axes:
        h_plot = h_plot.project(*args.axes)
        h_preds = [_h.project(*args.axes) for _h in h_preds]
    h_plot = hh.unrolledHist(h_plot)
    #h_plot = hh.normalize(h_plot, scale=1)
    h_preds = [hh.unrolledHist(_h) for _h in h_preds]
    print(args.ylim)
    fig = plot_tools.makePlotWithRatioToRef(
        [h_plot, *h_preds],
        ["Data", *labels],
        ["black", *colors],
        xlabel="Bin",
        ylim=args.ylim,
        yerr=True,
        base_size=10,
        plot_title=f"Best and top {args.n} sorted by {sortby}"
    )        
    fig.axes[0].legend(loc=(1.01,0))
    fig.axes[1].legend(loc=(1.01,0)).remove()
    if not os.path.isdir(args.outdir):
        os.makedirs(args.outdir)
    plot_tools.save_pdf_and_png(args.outdir, f"results_{sortby}_{args.postfix}" if args.postfix else f"results_{sortby}", fig)