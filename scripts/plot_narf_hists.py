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

hep.style.use("CMS")

def load_results_h5py(h5file):

    if "results" in h5file.keys():
        return ioutils.pickle_load_h5py(h5file["results"])
    else:
        return {k: ioutils.pickle_load_h5py(v) for k, v in h5file.items()}

def is_regex(pattern):

    try:
        re.compile(pattern)
        return True
    except re.error:
        return False
    
def match_regex(pattern, list):
    """
    Return elements from list that match the regex pattern.
    """
    return [item for item in list if re.match(pattern, item)]

def main():

    parser = argparse.ArgumentParser(
        description="Read in a hdf5 file."
    )
    parser.add_argument(
        "infile",
        type=str,
        help="hdf5 file.",
    )
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
    parser.add_argument(
        "--xlabel",
        type=str,
        default=None,
        help="Label for the x-axis of the histograms. If not provided, label from histogram is used."
    )
    parser.add_argument(
        "--ylabel",
        type=str,
        default=None,
        help="Label for the y-axis of the histograms. If not provided, label from histogram is used."
    )
    parser.add_argument(
        "--logy",
        action="store_true",
        help="Use logarithmic scale for the y-axis of the histograms. Default is linear scale."
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
            output = results[proc].get("output", {})
            if not output:
                print(f"No output found for process {proc}.")
                continue
            
            available_hists = list(output.keys())
            hists_to_plot = []
            if args.hists:

                for hist_name in args.hists:
                    
                    if is_regex(hist_name):
                        matched_hists = match_regex(hist_name, available_hists)
                        if matched_hists:
                            hists_to_plot.extend(matched_hists)
                        else:
                            print(f"No histograms matched the regex '{hist_name}' in process '{proc}'.")
                    else:
                        if hist_name in available_hists:
                            hists_to_plot.append(hist_name)
                        else:
                            print(f"Histogram '{hist_name}' not found in process '{proc}'. Available histograms: {available_hists}")
            else:
                hists_to_plot = available_hists


            for hist in hists_to_plot:

                h = output[hist].get()
                fig, ax = plt.subplots(figsize=(10, 6))
                hep.histplot(
                    h,
                    ax=ax,
                    histtype="step",
                    linewidth=2,
                    yerr=False
                )
                if args.logy: ax.set_yscale("log")
                if args.xlabel:
                    ax.set_xlabel(args.xlabel)
                if args.ylabel:
                    ax.set_ylabel(args.ylabel)
                ax.set_title(f"{proc} - {hist}")
                fig.tight_layout()
                _postfix = "" if not args.postfix else f"_{args.postfix}"
                oname=f"{args.outdir}{proc}_{hist}{_postfix}.pdf"
                fig.savefig(oname,  bbox_inches="tight")
                fig.savefig(oname.replace(".pdf", ".png"), bbox_inches="tight", dpi=300)
                plt.close(fig)
                print(f"Saved {oname}(.png)")
                                
if __name__ == "__main__":
    main()