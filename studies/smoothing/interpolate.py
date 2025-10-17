"""
Fit a histogram from a narf file with PySR.
"""

import os, sys
import argparse
from datetime import datetime
import h5py
import numpy as np
import copy
import hist
import matplotlib.pyplot as plt
import itertools

sys.path.append("../../WRemnants/")

from wums import ioutils
from wums import output_tools
from wums import plot_tools
from wums import boostHistHelpers as hh
from utilities import parsing

def load_results_h5py(h5file):
    if "results" in h5file.keys():
        return ioutils.pickle_load_h5py(h5file["results"])
    else:
        return {k: ioutils.pickle_load_h5py(v) for k, v in h5file.items()}

parser = argparse.ArgumentParser(
    description="Read in a hdf5 file."
)
parser.add_argument(
    "infile",
    type=str,
    help="hdf5 file.",
)
parser.add_argument(
    "--checkpoint",
    type=str,
    default=None,
    help="Directory containing checkpoint.pkl from which to initialize a regressor."
    "Will start training from this checkpoint, inheriting regressor parameters,"
    "but will impose this script's arguments to the regressor."
    "Will overwrite the existing checkpoint.pkl.",
)
parser.add_argument(
    "--select",
    nargs="+",
    dest="selection",
    type=str,
    default=None,
    help="Apply a selection to the histograms, if the axis exists."
    "This option can be applied to any of the axis, not necessarily one of the fitaxes, unlike --axlim."
    "Use complex numbers for axis value, integers for bin number."
    "e.g. --select 'ptll 0 10"
    "e.g. --select 'ptll 0j 10j",
)
parser.add_argument(
    "--refHistSelect",
    nargs="+",
    dest="refHistSelection",
    type=str,
    default=None,
    help="Apply a selection to the reference histogram, if the axis exists."
    "If left empty, the --select will apply to the reference hist."
)
parser.add_argument(
    "--hist",
    type=str,
    default="nominal",
    help="Histogram to fit."
)
parser.add_argument(
    "--refHist",
    type=str,
    default=None,
    help="Fit the ratio of --hist to --refHist."
)
parser.add_argument(
    "--axes",
    nargs="+",
    type=str,
    default=["ptll"],
    help="Axes to fit."
)
parser.add_argument(
    "--sample",
    type=str,
    default="ZmumuPostVFP",
    help="Sample to fit."
)
parser.add_argument(
    "--ylim",
    nargs=2,
    type=float,
    default=None,
    help="y limits."
)
parser.add_argument(
    "-o",
    "--outdir",
    type=str,
    required=True,
    help="Output directory for the plots. Default is current directory.",
)
parser.add_argument(
    "-p",
    "--postfix",
    type=str,
    default=None,
    help="Postfix to add to the output file names.",
)
args = parser.parse_args()


with h5py.File(args.infile, "r") as h5file:
    results = load_results_h5py(h5file)
    print(f"Samples in file: {results.keys()}\n")
    h = results[args.sample]['output'][args.hist].get()
    if args.refHist:
        h_ref = results[args.sample]['output'][args.refHist].get()

# needed for the weights
if h.storage_type != hist.storage.Weight and h.storage_type != hist.storage.Double:
    raise Exception()

# prepare the histogram
def prepare_hist(_h, axes, selection):
    for sel in selection:
        sel = sel.split()
        if len(sel) == 3:
            sel_ax, sel_lb, sel_ub = sel
            sel_lb = parsing.str_to_complex_or_int(sel_lb)
            sel_ub = parsing.str_to_complex_or_int(sel_ub)
            _h = _h[{sel_ax: slice(sel_lb, sel_ub, sum)}]
        elif len(sel) == 2:
            sel_ax, sel_val = sel
            try:
                sel_val = parsing.str_to_complex_or_int(sel_val)
            except argparse.ArgumentTypeError as e:
                print(e)
                print("Trying to use as string...")
                pass
            _h = _h[{sel_ax: sel_val}]
    if axes:
        _h = _h.project(*axes)
    _h_unroll = hh.unrolledHist(_h, binwnorm=1)
    _h_unroll = hh.normalize(_h_unroll, scale=1)
    return _h, _h_unroll

h, h_unroll = prepare_hist(h, args.axes, args.selection)
if args.refHist:
    h_ref, _ = prepare_hist(h_ref, args.axes, args.refHistSelection if args.refHistSelection else args.selection)
    h = hh.divideHists(h, h_ref)
    h_unroll = hh.unrolledHist(h)
    #h_unroll = hh.normalize(h_unroll, scale=1)
    y = h.values()
    y_err = h_unroll.variances() ** 0.5
else:
    y = h_unroll.values()
    y_err = h_unroll.variances()**0.5
x = [ax.centers for ax in h.axes]

from scipy.interpolate import RegularGridInterpolator

print(x)
print(y.shape)
interp = RegularGridInterpolator((x[0], x[1]), y)
x = np.array(list(itertools.product(*[ax.centers for ax in h.axes])))
interps = interp(x)
h_pred = copy.deepcopy(h_unroll)
h_pred.values()[...] = interps

fig = plot_tools.makePlotWithRatioToRef(
    [h_unroll, h_pred],
    ["Data", "Pred"],
    ["black", "red"],
    xlabel="Bin",
    ylim=args.ylim,
    yerr=True,
    base_size=10,
)        
fig.axes[0].legend(loc=(1.01,0))
fig.axes[1].legend(loc=(1.01,0)).remove()
if not os.path.isdir(args.outdir):
    os.makedirs(args.outdir)
plot_tools.save_pdf_and_png(args.outdir, f"results_RegularGridInterpolator_{args.postfix}" if args.postfix else f"results_RegularGridInterpolator", fig)