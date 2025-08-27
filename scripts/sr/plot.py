"""
Plot the results from a fit.
"""

import pysr
import os, sys
import argparse
import h5py
import numpy as np
import copy
import hist
import matplotlib.pyplot as plt
import lz4.frame
import pickle

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
    "--sample",
    type=str,
    default="ZmumuPostVFP",
    help="Sample to fit."
)
parser.add_argument(
    "--hist",
    type=str,
    default="nominal",
    help="Histogram to fit."
)
parser.add_argument(
    "--axes",
    nargs="+",
    type=str,
    default=["ptll"],
    help="Axes to fit."
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

# TODO could output only the histogram we care about from fit.py 
with lz4.frame.open(f"{args.model}/hist.pkl.lz4") as f:
    input = pickle.load(f)
    h = input['input']['h']

y = h.values()
y_err = h.variances()**0.5
x = np.array([h.axes[0].centers]).T

model = pysr.PySRRegressor()
model = model.from_file(run_directory=args.model)
model.set_params(extra_sympy_mappings={'inv': lambda x: 1/x})

colors = plt.cm.rainbow(np.linspace(0, 1, args.n))
h_preds = []
labels = []
for i in range(args.n):

    pred = model.predict(x, i)

    h_pred = copy.deepcopy(h)
    h_pred.values()[...] = pred
    h_preds.append(h_pred)
    labels.append(f"${model.latex(i)}$")

fig = plot_tools.makePlotWithRatioToRef(
    [h, *h_preds],
    ["Data", *labels],
    ["black", *colors],
    xlabel="Bin",
    yerr=True,
    base_size=10,
)
fig.axes[0].legend(loc=(1.01,0))
fig.axes[1].legend(loc=(1.01,0)).remove()
if not os.path.isdir(args.outdir):
    os.makedirs(args.outdir)
plot_tools.save_pdf_and_png(args.outdir, f"results_{args.postfix}" if args.postfix else "results", fig)