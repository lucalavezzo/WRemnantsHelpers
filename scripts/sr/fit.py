"""
Fit a histogram from a narf file with PySR.
"""

import pysr
from pysr import TensorBoardLoggerSpec
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
    help="Directory containing checkpoint.pkl from which to initialize a regressor.",
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
    "-t",
    "--timeout",
    type=int,
    default=None,
    help="Number of seconds to run for.",
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
    h_unroll = hh.normalize(h_unroll, scale=1)
    y = h_unroll.values()
    y_err = h_unroll.variances() ** 0.5
else:
    y = h_unroll.values()
    y_err = h_unroll.variances()**0.5
x = np.array(list(itertools.product(*[ax.centers for ax in h.axes])))

# unique identifier to store run results, input histogram
run_id = datetime.now().strftime("%y%m%d_%H%M")
if args.postfix:
    run_id += f"_{args.postfix}"

# store the histogram with the model
if not os.path.isdir(f"pysr_runs/{run_id}/"):
    os.makedirs(f"pysr_runs/{run_id}/")
output_tools.write_lz4_pkl_output(
    f"pysr_runs/{run_id}/hist",
    "input",
    {"h":h, "h_unroll":h_unroll,"isratio": True if args.refHist else False},
    "./",
    args
)

if args.checkpoint:
    # initialize model from an existing checkpoint
    model = pysr.PySRRegressor()
    model = model.from_file(
        run_directory=args.checkpoint,
        warm_start=True, # start where we left off

        # update parameters that are dependent on arguments of this script
        niterations=args.niterations,
        timeout_in_seconds=args.timeout,
        populations=args.nprocs/10,
        procs=args.nprocs,

    )
    model.set_params(extra_sympy_mappings={'inv': lambda x: 1/x})
else:
    # initialize a new model
    # see https://ai.damtp.cam.ac.uk/pysr/tuning/
    model = pysr.PySRRegressor(

        # search size
        niterations=args.niterations,
        timeout_in_seconds=args.timeout,

        # TODO test these parameters
        maxsize=30,
        population_size=len(y),
        populations=args.nprocs/10,
        ncycles_per_iteration=5000,
        #parsimony=0.001,
        weight_optimize=0.001,
        
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
        extra_sympy_mappings={
            "inv": lambda x: 1 / x
        },
        constraints={ # TODO play with this
            "^": (-1, 2),
            "sin": 5
        },
        nested_constraints={  # TODO play with this
            "sin": {"sin": 0, "exp": 1},
            "exp": {"exp": 0, "sin": 1},
            "abs": {"abs": 3},
            "^": {"sin": 0, "exp": 0}
        },
        # TODO customize loss

        # computing
        turbo=True,
        procs=args.nprocs,
        output_directory="pysr_runs",
        run_id=run_id,
        logger_spec=TensorBoardLoggerSpec(
            log_dir="pysr_runs/logs",
            log_interval=1, 
        ) if args.tensorboard else None
    )

model.fit(x, y, weights=y_err)
print(model)