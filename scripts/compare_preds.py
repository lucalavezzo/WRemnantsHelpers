import os
import sys

sys.path.append("../../WRemnants/")
import argparse
import h5py
import pprint
import lz4.frame
import pickle
import matplotlib.pyplot as plt
from datetime import datetime

from wums import logging, output_tools, plot_tools  # isort: skip
from utilities import parsing

parser = argparse.ArgumentParser(description="Read in a .pkl.lz4 file.")
parser.add_argument(
    "infiles",
    type=str,
    nargs="+",
    help="Input files.",
)
parser.add_argument(
    "--path",
    type=str,
    required=True,
    nargs="+",
    help="Path(s) inside the pickle data to print. Either pass one path for all files or one path per file.",
)
parser.add_argument(
    "--labels",
    type=str,
    nargs="+",
    required=False,
    help="Labels for the histograms, in the same order as the input files.",
)
parser.add_argument(
    "--axes",
    nargs="+",
    default=["qT"],
    help="Axes to keep before plotting. Remaining axes are unrolled.",
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
    "--selectByHist",
    nargs="+",
    type=str,
    help="Use instead to pass one selection per histogram to plot."
    "The index of the selection matches the index of the histogram."
    "Can be used on top of --select to have a base selection and then per-histogram selections."
    "Each --selectByHist item may contain multiple selections separated by ';' (e.g. 'pt 0 10;eta -2 2').",
)
parser.add_argument(
    "--rrange",
    default=(0.5, 1.5),
    type=float,
    nargs=2,
    help="Range for the ratio plot (default: 0.5, 1.5).",
)
parser.add_argument(
    "--oname",
    type=str,
    default="compare_preds",
    help="Output name prefix.",
)
parser.add_argument(
    "--outdir",
    type=str,
    default=os.path.join(
        os.environ["MY_PLOT_DIR"], datetime.now().strftime("%y%m%d_compare_preds")
    ),
    help="Output directory.",
)
args = parser.parse_args()

hists = []
paths = (
    args.path
    if len(args.path) == len(args.infiles)
    else [args.path[0]] * len(args.infiles)
)
for i, infile in enumerate(args.infiles):
    print(f"Reading file: {infile}")
    with lz4.frame.open(infile, "rb") as f:
        data = pickle.load(f)

    full_path = paths[args.infiles.index(infile)].split("/")
    subdata = data
    print(f"Navigating to path: {full_path}")
    for p in full_path:
        if p in subdata:
            subdata = subdata[p]
        else:
            raise KeyError(
                f"Path '{p}' not found in data at current level. Available keys: {list(subdata.keys())}"
            )
    if hasattr(subdata, "keys"):
        print(f"Keys at path {args.path}:")
        pprint.pprint(subdata.keys())
    print(subdata)
    h_selection = []
    if args.selectByHist:
        # support multiple selections per-hist separated by ';'
        raw = args.selectByHist[i]
        parts = [p.strip() for p in raw.split(";") if p.strip()]
        for part in parts:
            h_selection.append(part)
    if args.selection:
        h_selection.extend(args.selection)
    for sel in h_selection:
        sel = sel.split()
        if len(sel) == 3:
            sel_ax, sel_lb, sel_ub = sel
            sel_lb = parsing.str_to_complex_or_int(sel_lb)
            sel_ub = parsing.str_to_complex_or_int(sel_ub)
            h = h[{sel_ax: slice(sel_lb, sel_ub)}]
        elif len(sel) == 2:
            sel_ax, sel_val = sel
            try:
                sel_val = parsing.str_to_complex_or_int(sel_val)
            except argparse.ArgumentTypeError as e:
                print(e)
                print("Trying to use as string...")
                pass
            print(sel_ax, sel_val)
            subdata = subdata[{sel_ax: sel_val}]
    if args.axes:
        subdata = subdata.project(*args.axes)
    hists.append(subdata)

fig = plot_tools.makePlotWithRatioToRef(
    hists,
    args.labels if args.labels else [f.split("/")[-1] for f in args.infiles],
    rrange=[args.rrange],
    ratio_legend=False,
)
handles, labels = fig.axes[0].get_legend_handles_labels()
fig.axes[0].legend(handles, labels, loc=(1.01, 0), fontsize="small")
rel_oname = args.oname
oname = os.path.join(args.outdir, rel_oname)
if not os.path.exists(args.outdir):
    os.makedirs(args.outdir)
    print(f"Output directory '{args.outdir}' created.")
fig.savefig(oname + ".pdf", bbox_inches="tight")
fig.savefig(oname + ".png", bbox_inches="tight", dpi=300)
plt.close(fig)
output_tools.write_index_and_log(args.outdir, rel_oname, args=args)
print(f"Saved {oname}(.log)(.png)(.log)")
