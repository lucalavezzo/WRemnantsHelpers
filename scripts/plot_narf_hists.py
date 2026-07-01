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
import hist
from hist import Hist
import datetime

from hist_selection import (
    apply_selections,
    collect_selections,
    format_selection_label,
)

hep.style.use("CMS")


def load_results_h5py(h5file):

    if "results" in h5file.keys():
        return ioutils.pickle_load_h5py(h5file["results"])
    else:
        return {k: ioutils.pickle_load_h5py(v) for k, v in h5file.items()}


def is_regex(pattern):

    if any([x in pattern for x in ["*", "/"]]):
        try:
            re.compile(pattern)
            return True
        except re.error:
            return False
    else:
        return False


def match_regex(pattern, list):
    """
    Return elements from list that match the regex pattern.
    """
    return [item for item in list if re.match(pattern, item)]


def main():

    parser = argparse.ArgumentParser(description="Read in a hdf5 file.")
    parser.add_argument(
        "infile",
        type=str,
        help="hdf5 file.",
    )
    parser.add_argument("--axes", nargs="+", type=str, default=[], help="Axes to plot.")
    parser.add_argument(
        "--filterProcs",
        nargs="+",
        type=str,
        default=[],
        help="Filter processes by name, e.g. 'ZmumuPostVFP'. If empty, all processes are loaded.",
    )
    parser.add_argument(
        "--hists",
        nargs="+",
        type=str,
        default=[],
        help="Specify histogram names to filter output. If empty, all histograms are loaded. Supports regex.",
    )
    parser.add_argument("--binwnorm", type=int, default=None)
    parser.add_argument(
        "--xlabel",
        type=str,
        default=None,
        help="Label for the x-axis of the histograms. If not provided, label from histogram is used.",
    )
    parser.add_argument(
        "--ylabel",
        type=str,
        default=None,
        help="Label for the y-axis of the histograms. If not provided, label from histogram is used.",
    )
    parser.add_argument(
        "--labels",
        nargs="+",
        type=str,
        default=[],
        help="Name of histograms to display in legend. Must be of same length as --hists.",
    )
    parser.add_argument(
        "--legLoc",
        type=float,
        nargs=2,
        default=None,
        help="Location of the legend. Default is outside the plot on the right.",
    )
    parser.add_argument(
        "--xlim",
        type=float,
        nargs=2,
        default=None,
        help="Limits for the x-axis of the histograms. Default is automatic.",
    )
    parser.add_argument(
        "--ylim",
        type=float,
        nargs=2,
        default=None,
        help="Limits for the y-axis of the histograms. Default is automatic.",
    )

    parser.add_argument(
        "--logy",
        action="store_true",
        help="Use logarithmic scale for the y-axis of the histograms. Default is linear scale.",
    )
    parser.add_argument(
        "--rrange",
        default=(0.5, 1.5),
        type=float,
        nargs=2,
        help="Range for the ratio plot (default: 0.5, 1.5).",
    )
    parser.add_argument("--noErrorBars", action="store_true")
    parser.add_argument("--noRatioErrorBars", action="store_true")
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
        "--rebin",
        nargs="+",
        type=lambda x: x.split(),
        default=[],
        help="Rebin the histograms. Provide pairs of axis name and rebin factor. E.g. --rebin 'ptll 2' 'mll 5' will rebin the 'ptll' axis by a factor of 2 and the 'mll' axis by a factor of 5.",
    )
    parser.add_argument(
        "--outname",
        type=str,
        default=None,
        help="Base name for the output files. Default is based on input file name.",
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
        default=os.path.join(
            os.environ.get("MY_PLOT_DIR", "."),
            datetime.datetime.now().strftime("%y%m%d") + "_plot_narf_hists/",
        ),
        help="Output directory for the plots. Default is current directory.",
    )
    args = parser.parse_args()

    if args.selectByHist and len(args.selectByHist) != len(args.hists):
        raise Exception(
            f"Length of selections passed ({len(args.selectByHist)}), number of hists to plot ({len(args.hists)}) does not match"
        )

    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)
        print(f"Output directory '{args.outdir}' created.")

    with h5py.File(args.infile, "r") as h5file:
        results = load_results_h5py(h5file)
        print("Keys in h5 file:", h5file.keys())

        procs = list(results.keys())
        if args.filterProcs:
            procs = [proc for proc in procs if proc in args.filterProcs]
            print(f"Filtered results to processes: {procs}")
        else:
            print("No filtering applied, all processes loaded.")

        for proc in procs:
            print(f"Process: {proc}")

            if type(results[proc]) is dict:
                output = results[proc].get("output", {})
                if not output:
                    print(f"No output found for process {proc}.")
                    continue
                available_hists = list(output.keys())
            elif type(results[proc]) is Hist:
                available_hists = [proc]
                output = results

            hists_to_plot = []
            if args.hists:

                for hist_name in args.hists:

                    if is_regex(hist_name):
                        matched_hists = match_regex(hist_name, available_hists)
                        if matched_hists:
                            hists_to_plot.extend(matched_hists)
                        else:
                            print(
                                f"No histograms matched the regex '{hist_name}' in process '{proc}'."
                            )
                    else:
                        if hist_name in available_hists:
                            hists_to_plot.append(hist_name)
                        else:
                            print(
                                f"Histogram '{hist_name}' not found in process '{proc}'. Available histograms: {available_hists}"
                            )

            else:
                hists_to_plot = available_hists

            if len(args.labels):
                if len(args.labels) != len(hists_to_plot):
                    raise Exception(
                        f"Length of labels passed ({len(args.labels)}), number of hists to plot ({len(hists_to_plot)}) does not match"
                    )
                labels_to_plot = args.labels
            else:
                labels_to_plot = hists_to_plot

            h_ref = output[hists_to_plot[0]]
            if not (type(h_ref) is Hist):
                h_ref = h_ref.get()
            ref_selection = collect_selections(args.selection, args.selectByHist, 0)
            h_ref = apply_selections(h_ref, ref_selection)
            if args.axes:
                h_ref = h_ref.project(*args.axes)
            if len(h_ref.axes) > 1:
                h_ref = hh.unrolledHist(h_ref, binwnorm=args.binwnorm)
            if args.rebin:
                for rebin in args.rebin:
                    axis_name = rebin[0]
                    if axis_name.isdigit():
                        axis_name = int(axis_name)
                    h_ref = h_ref[{axis_name: np.s_[:: hist.rebin(int(rebin[1]))]}]

            fig, ax1, ratio_axes = plot_tools.figureWithRatio(
                h_ref,
                "(" + ",".join(args.axes) + ") bin" if len(args.axes) else "bin",
                "Events",
                ylim=np.max(h_ref.values()) * 1.1,
                rlabel=f"1/ref.",
                rrange=args.rrange,
                base_size=10,
            )
            ax2 = ratio_axes[-1]

            hep.histplot(
                h_ref,
                ax=ax1,
                label=labels_to_plot[0] + " (ref.)",
                histtype="step",
                binwnorm=args.binwnorm if len(h_ref.axes) == 1 else None,
                color="black",
                yerr=not args.noErrorBars,
            )

            for ihist, hist_to_plot in enumerate(hists_to_plot):
                if ihist == 0:
                    continue  # already plotted

                h = output[hist_to_plot]
                if not (type(h) is Hist):
                    h = h.get()
                h_selection = collect_selections(
                    args.selection, args.selectByHist, ihist
                )
                h = apply_selections(h, h_selection)
                if args.axes:
                    h = h.project(*args.axes)
                if len(h.axes) > 1:
                    h = hh.unrolledHist(h, binwnorm=args.binwnorm)
                if args.rebin:
                    for rebin in args.rebin:
                        axis_name = rebin[0]
                        if axis_name.isdigit():
                            axis_name = int(axis_name)
                        h = h[{axis_name: np.s_[:: hist.rebin(int(rebin[1]))]}]
                hep.histplot(
                    h,
                    ax=ax1,
                    label=labels_to_plot[ihist],
                    histtype="step",
                    binwnorm=args.binwnorm if len(h_ref.axes) == 1 else None,
                    yerr=not args.noErrorBars,
                )

                hr = hh.divideHists(
                    h,
                    h_ref,
                    cutoff=1e-8,
                    rel_unc=True,
                    flow=False,
                    by_ax_name=False,
                )
                hep.histplot(
                    hr,
                    ax=ax2,
                    histtype="step",
                    label=labels_to_plot[ihist],
                    yerr=not args.noRatioErrorBars,
                )

            # Prepare selection strings to include in the legend instead of a separate text box.
            global_sel_label = format_selection_label(args.selection)
            if global_sel_label:
                global_sel_label = "Selections:\n" + global_sel_label

            per_hist_selections = None
            if args.selectByHist:
                per_hist_selections = [
                    format_selection_label(
                        [p.strip() for p in raw.split(";") if p.strip()]
                    )
                    for raw in args.selectByHist
                ]
            if args.logy:
                ax1.set_yscale("log")
            if args.xlabel:
                ax2.set_xlabel(args.xlabel)
            if args.ylabel:
                ax1.set_ylabel(args.ylabel)
            if args.xlim:
                ax1.set_xlim(args.xlim)
                ax2.set_xlim(args.xlim)
            # in case of only one axis being used, we want to set the x_ticks_ndp to a reasonable number, since they represent actual values, not bin numbers
            if len(h_ref.axes) == 1:
                centers = h_ref.axes[0].centers
                diff = np.diff(centers)
                min_diff = np.min(diff)
                # grab the number of decimal places in min_diff
                if min_diff < 1:
                    x_ticks_ndp = abs(int(np.floor(np.log10(min_diff)))) - 1
                else:
                    x_ticks_ndp = 0
            else:
                x_ticks_ndp = None
            plot_tools.fix_axes(ax1, ax2, fig, logy=args.logy, x_ticks_ndp=x_ticks_ndp)
            plot_tools.add_cms_decor(ax1, "Preliminary", lumi=16.8, loc=0)
            # Build legend so selections are included inside it.
            handles, labels = ax1.get_legend_handles_labels()
            # Append per-hist selections under each histogram label (if provided)
            if per_hist_selections:
                # labels correspond to the plotted histograms in order (ref first)
                for i in range(min(len(labels), len(per_hist_selections))):
                    sel = per_hist_selections[i]
                    if sel:
                        labels[i] = labels[i] + "\n" + sel

            # If there is a global selection, insert it as the first legend entry using a dummy handle
            if global_sel_label:
                dummy = Line2D([], [], color="none")
                handles.insert(0, dummy)
                labels.insert(0, global_sel_label)

            ax1.legend(
                handles,
                labels,
                loc=args.legLoc if args.legLoc else (1.01, 0),
                fontsize="small",
            )
            ax1.invert_yaxis()  # I have no idea why I have to do this
            if args.ylim:
                ax1.set_ylim(args.ylim)

            _postfix = "" if not args.postfix else f"_{args.postfix}"
            base_name = (
                args.outname if args.outname else proc + "_" + "_".join(hists_to_plot)
            )
            oname = os.path.join(args.outdir, f"{base_name}{_postfix}")
            fig.savefig(oname + ".pdf", bbox_inches="tight")
            fig.savefig(oname + ".png", bbox_inches="tight", dpi=300)
            plt.close(fig)
            output_tools.write_index_and_log(
                args.outdir, oname.split("/")[-1], args=args
            )
            print(f"Saved {oname}(.png)(.png)(.log)")


if __name__ == "__main__":
    main()
