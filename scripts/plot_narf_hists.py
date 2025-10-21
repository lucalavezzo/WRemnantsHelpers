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
        "--xlim",
        type=float,
        nargs=2,
        default=None,
        help="Limits for the x-axis of the histograms. Default is automatic.",
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
        "--selectRefHist",
        nargs="+",
        dest="selectRefHist",
        type=str,
        default=None,
        help="Apply a selection to the reference histograms, if the axis exists."
        "Reference histogram will be applied --select, if this option is not specified."
        "This option can be applied to any of the axis, not necessarily one of the fitaxes, unlike --axlim."
        "Use complex numbers for axis value, integers for bin number."
        "e.g. --select 'ptll 0 10"
        "e.g. --select 'ptll 0j 10j",
    )
    parser.add_argument(
        "--rebin",
        nargs="+",
        type=lambda x: x.split(),
        default=[],
        help="Rebin the histograms. Provide pairs of axis name and rebin factor. E.g. --rebin 'ptll 2' 'mll 5' will rebin the 'ptll' axis by a factor of 2 and the 'mll' axis by a factor of 5.",
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
            if args.selectRefHist is None:
                args.selectRefHist = args.selection
            if args.selectRefHist:
                for sel in args.selectRefHist:
                    sel = sel.split()
                    if len(sel) == 3:
                        sel_ax, sel_lb, sel_ub = sel
                        sel_lb = parsing.str_to_complex_or_int(sel_lb)
                        sel_ub = parsing.str_to_complex_or_int(sel_ub)
                        h_ref = h_ref[{sel_ax: slice(sel_lb, sel_ub)}]
                    elif len(sel) == 2:
                        sel_ax, sel_val = sel
                        try:
                            sel_val = parsing.str_to_complex_or_int(sel_val)
                        except argparse.ArgumentTypeError as e:
                            print(e)
                            print("Trying to use as string...")
                            pass
                        if sel_ax not in h_ref.axes.name:
                            print(
                                f"Axis '{sel_ax}' not found in histogram axes {h_ref.axes.name}. Available axes: {h_ref.axes.name}"
                            )
                        else:
                            h_ref = h_ref[{sel_ax: sel_val}]
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
                ylim=np.max(h_ref.values()) * 1.3,
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
                if args.selection:
                    for sel in args.selection:
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
                            h = h[{sel_ax: sel_val}]
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

            selections_text = ""
            if args.selection or args.selectRefHist:
                selections_text = "Selections:\n"
                if args.selection:
                    for sel in args.selection:
                        sel = sel.split()
                        if len(sel) == 3:
                            sel_ax, sel_lb, sel_ub = sel
                            selections_text += f"{sel_ax}: [{sel_lb}, {sel_ub})\n"
                        elif len(sel) == 2:
                            sel_ax, sel_val = sel
                            selections_text += f"{sel_ax}: {sel_val}\n"
                if args.selectRefHist is None:
                    args.selectRefHist = args.selection
                selections_text += "\nref. hist:\n"
                for sel in args.selectRefHist:
                    sel = sel.split()
                    if len(sel) == 3:
                        sel_ax, sel_lb, sel_ub = sel
                        selections_text += f"{sel_ax}: [{sel_lb}, {sel_ub})\n"
                    elif len(sel) == 2:
                        sel_ax, sel_val = sel
                        selections_text += f"{sel_ax}: {sel_val}\n"
                ax1.text(
                    1.01, 0, selections_text, transform=ax1.transAxes, fontsize="small"
                )
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
            plot_tools.add_cms_decor(ax1, "Preliminary", lumi=16.8, loc=2)
            ax1.legend()
            ax1.invert_yaxis()  # I have no idea why I have to do this

            _postfix = "" if not args.postfix else f"_{args.postfix}"
            oname = os.path.join(
                args.outdir, f"{proc}_{"_".join(hists_to_plot)}{_postfix}"
            )
            fig.savefig(oname + ".pdf", bbox_inches="tight")
            fig.savefig(oname + ".png", bbox_inches="tight", dpi=300)
            plt.close(fig)
            output_tools.write_index_and_log(
                args.outdir, f"{proc}_{"_".join(hists_to_plot)}{_postfix}", args=args
            )
            print(f"Saved {oname}(.log)(.png)(.log)")


if __name__ == "__main__":
    main()
