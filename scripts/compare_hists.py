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
from wums import ioutils
from wums import boostHistHelpers as hh  # isort: skip
from wums import logging, output_tools, plot_tools  # isort: skip

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
        help="The inputs files were created with narf (a histmaker). Will be read accordingly."
    )
    parser.add_argument(
        "--proc",
        default="ZmumuPostVFP",
        type=str,
        help="Process name to grab from the narf file (default: ZmumuPostVFP).",
    )
    parser.add_argument(
        "--histName",
        default="hist_prefit_inclusive_variations",
        type=str,
        help="Name of the histogram to read from the fit result (default: hist_prefit_inclusive_variations).",
    )
    parser.add_argument(
        "--labels",
        nargs="+",
        type=str,
        help="Labels for the input files, must match the number of input files.",
    )
    parser.add_argument(
        "--plotAxes",
        nargs="+",
        type=str,
        default=["ptll", "yll"],
        help="Axes to plot in the histograms (default: ptll, yll).",
    )
    parser.add_argument(
        "--selectionAxes",
        nargs="+",
        type=str,
        default=[],
        help="For each bin of these axes, a different histogram will be created with the axes selected via --plotAxes."
    )
    parser.add_argument(
        "--select",
        nargs="+",
        dest="selection",
        type=str,
        default=[],
        help="Apply a selection to the histograms, if the axis exists. This option can be applied to any of the axis, not necessarily one of the fitaxes, unlike --axlim. e.g. '--select 'ptll 0 10'"
    )
    parser.add_argument(
        "--compareVars",
        nargs="+",
        type=str,
        default=[],
        help="Variables to compare in the histograms. Applicable only if the 'vars' axis is present in the histogram.",
    )
    parser.add_argument(
        "--rrange",
        default=(0.5, 1.5),
        type=float,
        nargs=2,
        help="Range for the ratio plot (default: 0.5, 1.5).",
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
        default=".",
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
        args.plotAxes.append('pdfVar')

    files_hists = {}
    for infile in args.infiles:
        print(f"Processing file: {infile}")
        
        hists = {}

        if args.narf:

            with h5py.File(infile, "r") as h5file:
                results = load_results_h5py(h5file)
                try:
                    h = results[args.proc]['output'][args.histName].get()
                except KeyError:
                    raise KeyError(f"Histogram '{args.histName}' not found in file '{infile}'. Available histograms: {list(results[args.proc]['output'].keys())}")
        else:
                

            # Load fit result and metadata
            fitresult, meta = rabbit.io_tools.get_fitresult(
                infile, result=args.result, meta=True
            )

            # grab the histogram
            try:
                h = fitresult['physics_models']['Basemodel']['channels']['ch0'][args.histName].get()
            except KeyError:
                raise KeyError(f"Histogram '{args.histName}' not found in fit result. Available histograms: {list(fitresult['physics_models']['Basemodel']['channels']['ch0'].keys())}")

        # apply selections if specified
        for sel in args.selection:
            split =  sel.split()
            if len(split) == 3:
                sel_ax, sel_lb, sel_ub = split
                sel_lb = complex(sel_lb)
                sel_ub = complex(sel_ub)
                if sel_ax not in h.axes.name:
                    raise ValueError(f"Selection axis '{sel_ax}' not found in histogram axes. Available axes: {h.axes.name}")
                h = h[{sel_ax: slice(sel_lb, sel_ub, hist.sum)}]
            else:
                # not supported yet
                pass

        # take only relevant axes for plotting        
        h = h.project(*args.plotAxes, *args.selectionAxes)

        # this really only works for the fitresult
        if args.compareVars:
            
            # convert vars in case they are a grep pattern
            # check if each var exists in the vars axis
            vars_to_compare = []
            available_vars = [n for n in h.axes['pdfVar']]
            for var in args.compareVars:

                # check if it's a regex pattern
                if any(c in var for c in ['*', '?', '[', ']', '{', '}', '^', '$']):
                    # use regex to find matching vars
                    import re
                    pattern = re.compile(var)
                    vars_to_compare.extend([n for n in available_vars if pattern.match(n)])
                else:
                    # check if the var exists in the vars axis
                    if var in available_vars:
                        vars_to_compare.append(var)
                    else:
                        raise ValueError(f"Variable '{var}' not found in 'vars' axis. Available vars: {available_vars}")
                    
            for var in vars_to_compare:
                hists[var] = h[{'pdfVar': var}]

        else:
            hists[args.histName] = h
        
        files_hists[infile] = hists

    if args.labels:
        if len(args.labels) != len(files_hists):
            raise ValueError("Number of labels must match number of input files.")
    else:
        args.labels = [f"File {i+1}" for i in range(len(files_hists))]

    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)

    common_vars = set.intersection(*[set(hists.keys()) for hists in files_hists.values()])
    for var in common_vars:

        print("Plotting variable:", var)

        h_ref = files_hists[args.infiles[0]][var]

        selection_axes = [ax for ax in h_ref.axes if ax.name in args.selectionAxes]
        selection_axes_lenghts = [len(ax) for ax in selection_axes]
        ranges = [range(b) for b in selection_axes_lenghts]
        combinations = list(product(*ranges))

        for combination in combinations:

            _h_ref = h_ref[{ax.name: combination[i] for i, ax in enumerate(selection_axes)}]
            _h_ref = hh.unrolledHist(_h_ref, binwnorm=1)

            fig, ax1, ratio_axes = plot_tools.figureWithRatio(
                _h_ref,
                "("  + ",".join(args.plotAxes) + ") bin",
                "Events",
                ylim=np.max(_h_ref.values()) * 1.2,
                rlabel=f"1/{args.labels[0]}",
                rrange=args.rrange
            )
            ax2 = ratio_axes[-1]

            hep.histplot(_h_ref, ax=ax1, label=args.labels[0], histtype="step", color="black")

            for i, (infile, hists) in enumerate(files_hists.items()):
                if i == 0: continue # already plotted

                h = hists[var]
                h = h[{ax.name: combination[i] for i, ax in enumerate(selection_axes)}]
                h = hh.unrolledHist(h, binwnorm=1)

                hep.histplot(h, ax=ax1, label=args.labels[i], histtype="step")

                hr = hh.divideHists(
                    h,
                    _h_ref,
                    cutoff=1e-8,
                    rel_unc=True,
                    flow=False,
                    by_ax_name=False,
                )
                hep.histplot(hr, ax=ax2, histtype="step", label=args.labels[i])

            plot_tools.fix_axes(ax1, ax2, fig)
            ax1.legend()
            ax1.invert_yaxis() # I have no idea why I have to do this
            _postfix = "_"+args.postfix if args.postfix else ""
            selection_label = "_".join([f"{ax.name}_{combination[i]}" for i, ax in enumerate(selection_axes)]) if selection_axes else ""
            if selection_label:
                selection_label = f"_{selection_label}"
            else:
                selection_label = ""
            ax1.set_title(f"{var}{selection_label}")
            oname = args.outdir + f"/{var}{selection_label}{_postfix}.png"
            print(f"Saving plot to {oname}(.pdf)")
            fig.tight_layout()
            fig.savefig(oname, dpi=300, bbox_inches='tight')
            fig.savefig(oname.replace(".png", ".pdf"), bbox_inches='tight')
            plt.close(fig)


if __name__ == "__main__":
    main()