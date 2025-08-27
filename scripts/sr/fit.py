"""
Fit a histogram from a narf file with PySR.
"""

import pysr
from pysr import TensorBoardLoggerSpec
import os, sys
import argparse
import h5py
import numpy as np
import copy
import hist
import matplotlib.pyplot as plt

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
    "infile",
    type=str,
    help="hdf5 file.",
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
    "--sample",
    type=str,
    default="ZmumuPostVFP",
    help="Sample to fit."
)
parser.add_argument(
    "-n",
    "--nprocs",
    type=int,
    default=100,
    help="Number of processes to use.",
)
parser.add_argument(
    "-i",
    "--niterations",
    type=int,
    default=20,
    help="Number of iterations to run for.",
)
parser.add_argument(
    "--tensorboard",
    action='store_true',
    help="Use tensorboard."
)
parser.add_argument(
    "-p",
    "--postfix",
    type=str,
    default=None,
    help="Postfix to add to the output file names.",
)
parser.add_argument(
    "-o",
    "--outdir",
    type=str,
    default="./",
    help="Output directory for the plots. Default is current directory.",
)
args = parser.parse_args()


with h5py.File(args.infile, "r") as h5file:
    results = load_results_h5py(h5file)
    print(f"Samples in file: {results.keys()}\n")
    h = results[args.sample]['output'][args.hist].get()

if h.storage_type != hist.storage.Weight:
    raise Exception()

# TODO support n-dimensions
if len(args.axes) > 1:
    raise Exception()

h = h.project(*args.axes)
h = hh.normalize(h, scale=1)
h = hh.unrolledHist(h, binwnorm=1)

y = h.values()
y_err = h.variances()**0.5
x = np.array([h.axes[0].centers]).T

# see https://ai.damtp.cam.ac.uk/pysr/tuning/
model = pysr.PySRRegressor(

    # search size
    niterations=args.niterations,
    maxsize=20,
    population_size=len(y), # TODO testing this
    populations=args.nprocs/10, 
    ncycles_per_iteration=5000, # TODO testing this
    #parsimony=0.001, # TODO test this
    weight_optimize=0.001, # TODO testing this
    
    # operators and constraints
    binary_operators=[
        "+",
        "*",
        "^"
    ],
    unary_operators=[
        "exp",
        "sin",
        "inv",
        "abs"
    ],
    extra_sympy_mappings={"inv": lambda x: 1 / x},
    constraints={ # TODO play with this
        "^": (-1, 2),
        "sin": 5
    },
    nested_constraints={  # TODO play with this
        "sin": {"sin": 1, "exp": 0},
        "exp": {"exp": 0, "sin": 1},
        "abs": {"abs": 3}
    },
    # TODO custom loss to set sum(helicities)=0, when we get there

    # computing
    turbo=True,
    procs=args.nprocs,
    output_directory="pysr_runs",
    logger_spec=TensorBoardLoggerSpec(
        log_dir="pysr_runs/logs",
        log_interval=1, 
    ) if args.tensorboard else None
)

model.fit(x, y, weights=y_err)
print(model)

# only plot results if you specify outdir, else use other scripts
if args.outdir:

    # show top 5
    show_n = 5
    colors = plt.cm.rainbow(np.linspace(0, 1, show_n))
    h_preds = []
    for i in range(show_n):

        pred = model.predict(x, i)

        h_pred = copy.deepcopy(h)
        h_pred.values()[...] = pred
        h_preds.append(h_pred)

    fig = plot_tools.makePlotWithRatioToRef(
        [h, *h_preds],
        ["Data", *[f"Prediction {i}" for i in range(show_n)]],
        ["black", *colors],
        xlabel="Bin",
        yerr=True,
        base_size=10
    )
    if not os.path.isdir(args.outdir):
        os.makedirs(args.outdir)
    plot_tools.save_pdf_and_png(args.outdir, f"runresults_{args.runid}_{args.postfix}" if args.postfix else f"results_{args.runid}", fig)