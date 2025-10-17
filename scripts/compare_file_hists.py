import os
import sys

sys.path.append("../../WRemnants/")
import hist
import numpy as np
import matplotlib.pyplot as plt
import mplhep as hep
import rabbit.io_tools
import argparse
import h5py
from itertools import product
from utilities import common, parsing
from wums import ioutils
from wums import boostHistHelpers as hh  # isort: skip
from wums import logging, output_tools, plot_tools  # isort: skip
import datetime

hep.style.use("CMS")


def load_results_h5py(h5file):
    if "results" in h5file.keys():
        return ioutils.pickle_load_h5py(h5file["results"])
    else:
        return {k: ioutils.pickle_load_h5py(v) for k, v in h5file.items()}


def main():

    parser = argparse.ArgumentParser(
        description="Read fit result from hdf5 file from rabbit or root file from combinetf1"
    )
    parser.add_argument(
        "infiles",
        nargs="+",
        type=str,
        help="One or more hdf5 files",
    )
    parser.add_argument(
        "--narf",
        action="store_true",
        help="The inputs files were created with narf (a histmaker). Will be read accordingly.",
    )
    parser.add_argument(
        "--proc",
        default=None,
        type=str,
        help="Process name to grab from the narf file (default: None).",
    )
    parser.add_argument(
        "--hist",
        nargs="+",
        default=["hist_prefit_inclusive_variations"],
        type=str,
        help="Name of the histogram to read from the fit result (default: hist_prefit_inclusive_variations)."
        "If multiple names are passed, the assumption is that they match the number of files.",
    )
    parser.add_argument(
        "--labels",
        nargs="+",
        type=str,
        help="Labels for the input files, must match the number of input files.",
    )
    parser.add_argument(
        "--axes",
        nargs="+",
        type=str,
        default=[],
        help="Axes to plot in the histograms. Leave empty for all available axes. (default: []).",
    )
    parser.add_argument(
        "--selectionAxes",
        nargs="+",
        type=str,
        default=[],
        help="For each bin of these axes, a different histogram will be created with the axes selected via --axes.",
    )
    parser.add_argument(
        "--select",
        nargs="+",
        dest="selection",
        type=str,
        default=[],
        help="Apply a selection to the histograms, if the axis exists. This option can be applied to any of the axis, not necessarily one of the fitaxes, unlike --axlim. e.g. '--select 'ptll 0 10'",
    )
    parser.add_argument(
        "--compareVars",
        nargs="+",
        type=str,
        default=[],
        help="Variables to compare in the histograms. Applicable only if the 'vars' axis is present in the histogram.",
    )
    parser.add_argument(
        "--range",
        default=None,
        type=float,
        nargs=2,
        help="Range for the plot (default: None).",
    )
    parser.add_argument(
        "--rrange",
        default=(0.5, 1.5),
        type=float,
        nargs=2,
        help="Range for the ratio plot (default: 0.5, 1.5).",
    )
    parser.add_argument(
        "--binwnorm",
        default=1,
        type=float,
        help="Bin width normalization factor (default: 1).",
    )
    parser.add_argument(
        "--norm", action="store_true", help="Normalize the hists to unity."
    )
    parser.add_argument(
        "--result",
        default=None,
        type=str,
        help="fitresults key in file (e.g. 'asimov'). Leave empty for data fit result.",
    )
    parser.add_argument(
        "-o",
        "--outdir",
        default=os.path.join(
            os.environ.get("MY_PLOT_DIR", "."),
            f"{datetime.datetime.now().strftime('%y%m%d')}_compare_file_hists/",
        ),
        type=str,
        help="Output directory for the plots. Default is current directory.",
    )
    parser.add_argument(
        "--postfix",
        default="",
        type=str,
        help="Postfix for the output files. Default is empty.",
    )
    args = parser.parse_args()

    if args.compareVars:
        args.axes.append("vars")

    if len(args.hist) > 1:
        if len(args.hist) != len(args.infiles):
            raise Exception("Either pass one hist, or one per file.")
    else:
        args.hist = args.hist * len(args.infiles)

    files_hists = {}
    for infile, hist_name in zip(args.infiles, args.hist):
        print(f"Processing file: {infile}")

        hists = {}

        if args.narf:

            with h5py.File(infile, "r") as h5file:
                results = load_results_h5py(h5file)
                try:
                    if args.proc is None:
                        h = results[hist_name]
                    else:
                        h = results[args.proc]["output"][hist_name].get()
                except KeyError:
                    raise KeyError(
                        f"Histogram '{hist_name}' not found in file '{infile}'. Available histograms: {list(results[args.proc]['output'].keys())}"
                    )
        else:

            # Load fit result and metadata
            fitresult, meta = rabbit.io_tools.get_fitresult(
                infile, result=args.result, meta=True
            )

            # grab the histogram
            try:
                h = fitresult["physics_models"]["Basemodel"]["channels"]["ch0"][
                    hist_name
                ].get()
            except KeyError:
                raise KeyError(
                    f"Histogram '{hist_name}' not found in fit result. Available histograms: {list(fitresult['physics_models']['Basemodel']['channels']['ch0'].keys())}"
                )

        # apply selections if specified
        for sel in args.selection:
            split = sel.split()
            if len(split) == 3:
                sel_ax, sel_lb, sel_ub = split
                sel_lb = parsing.str_to_complex_or_int(sel_lb)
                sel_ub = parsing.str_to_complex_or_int(sel_ub)
                if sel_ax not in h.axes.name:
                    print(
                        f"Selection axis '{sel_ax}' not found in histogram axes. Available axes: {h.axes.name}"
                    )
                else:
                    h = h[{sel_ax: slice(sel_lb, sel_ub, sum)}]
            else:
                sel_ax, sel_val = split
                try:
                    sel_val = parsing.str_to_complex_or_int(sel_val)
                except argparse.ArgumentTypeError as e:
                    print(e)
                    print("Trying to use as string...")
                    pass
                if sel_ax not in h.axes.name:
                    print(
                        f"Selection axis '{sel_ax}' not found in histogram axes. Available axes: {h.axes.name}"
                    )
                else:
                    h = h[{sel_ax: sel_val}]

        # take only relevant axes for plotting
        if len(args.axes):
            h = h.project(*args.axes, *args.selectionAxes)
        if args.norm:
            norm = h.sum()
            if hasattr(norm, "value"):
                norm = norm.value
            if not (norm > 0):
                raise ValueError
            h /= norm

        # this really only works for the fitresult
        if args.compareVars:

            # convert vars in case they are a grep pattern
            # check if each var exists in the vars axis
            vars_to_compare = []
            available_vars = [n for n in h.axes["vars"]]
            for var in args.compareVars:

                # check if it's a regex pattern
                if any(c in var for c in ["*", "?", "[", "]", "{", "}", "^", "$"]):
                    # use regex to find matching vars
                    import re

                    pattern = re.compile(var)
                    vars_to_compare.extend(
                        [n for n in available_vars if pattern.match(n)]
                    )
                else:
                    # check if the var exists in the vars axis
                    if var in available_vars:
                        vars_to_compare.append(var)
                    else:
                        raise ValueError(
                            f"Variable '{var}' not found in 'vars' axis. Available vars: {available_vars}"
                        )

            for var in vars_to_compare:
                hists[var] = h[{"vars": var}]

        else:
            hists[hist_name] = h

        files_hists[infile] = hists

    if args.labels:
        if len(args.labels) != len(files_hists):
            raise ValueError("Number of labels must match number of input files.")
    else:
        args.labels = [f"File {i+1}" for i in range(len(files_hists))]

    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)
    output_tools.write_indexfile(args.outdir)

    # TODO I think this made sense when doing args.compareVars. Should set up to support this again
    # print(files_hists)
    # common_vars = set.intersection(*[set(hists.keys()) for hists in files_hists.values()])
    # print(common_vars)
    # for var in common_vars:

    var = "_".join([list(d.keys())[0] for d in files_hists.values()])
    print("Plotting variable:", var)

    h_ref = list(files_hists[args.infiles[0]].values())[0]

    selection_axes = [ax for ax in h_ref.axes if ax.name in args.selectionAxes]
    selection_axes_lenghts = [len(ax) for ax in selection_axes]
    ranges = [range(b) for b in selection_axes_lenghts]
    combinations = list(product(*ranges))

    for combination in combinations:

        _h_ref = h_ref[{ax.name: combination[i] for i, ax in enumerate(selection_axes)}]
        if len(_h_ref.axes) > 1:
            _h_ref = hh.unrolledHist(_h_ref, binwnorm=args.binwnorm)

        fig, ax1, ratio_axes = plot_tools.figureWithRatio(
            _h_ref,
            "(" + ",".join(args.axes) + ") bin" if len(args.axes) else "bin",
            "Events",
            ylim=np.max(_h_ref.values()) * 1.2,
            rlabel=f"1/{args.labels[0]}",
            rrange=args.rrange,
        )
        ax2 = ratio_axes[-1]

        hep.histplot(
            _h_ref,
            ax=ax1,
            label=args.labels[0] + " - " + list(files_hists[args.infiles[0]].keys())[0],
            binwnorm=args.binwnorm if len(_h_ref.axes) == 1 else None,
            histtype="step",
            color="black",
            yerr=not args.norm,
        )

        for i, (infile, hists) in enumerate(files_hists.items()):
            if i == 0:
                continue  # already plotted

            h = list(hists.values())[0]
            h = h[{ax.name: combination[i] for i, ax in enumerate(selection_axes)}]
            if len(h.axes) > 1:
                h = hh.unrolledHist(h, binwnorm=args.binwnorm)

            hep.histplot(
                h,
                ax=ax1,
                label=args.labels[i] + " - " + list(hists.keys())[0],
                binwnorm=args.binwnorm if len(h.axes) == 1 else None,
                histtype="step",
                yerr=not args.norm,
            )

            hr = hh.divideHists(
                h,
                _h_ref,
                cutoff=1e-8,
                rel_unc=True,
                flow=False,
                by_ax_name=False,
            )
            hep.histplot(
                hr,
                ax=ax2,
                histtype="step",
                label=args.labels[i] + " - " + list(hists.keys())[0],
                yerr=not args.norm,
            )

        plot_tools.fix_axes(ax1, ax2, fig)
        ax1.legend()
        ax1.invert_yaxis()  # I have no idea why I have to do this
        _postfix = "_" + args.postfix if args.postfix else ""
        selection_label = (
            "_".join(
                [f"{ax.name}_{combination[i]}" for i, ax in enumerate(selection_axes)]
            )
            if selection_axes
            else ""
        )
        if selection_label:
            selection_label = f"_{selection_label}"
        else:
            selection_label = ""
        if selection_label:
            ax1.set_title(f"{selection_label}")
        if args.range:
            ax1.set_ylim(args.range[0], args.range[1])
        fname = f"{var}{selection_label}{_postfix}"
        oname = os.path.join(args.outdir, fname)
        fig.tight_layout()
        fig.savefig(oname + ".png", dpi=300, bbox_inches="tight")
        fig.savefig(oname + ".pdf", bbox_inches="tight")
        plt.close(fig)
        output_tools.write_index_and_log(args.outdir, fname, args=args)
        print(f"Saved {oname}(.png)(.log)")


if __name__ == "__main__":
    main()
