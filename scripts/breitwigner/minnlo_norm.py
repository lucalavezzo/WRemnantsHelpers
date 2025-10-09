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

    parser = argparse.ArgumentParser(
        description="Read in a hdf5 file."
    )
    parser.add_argument(
        "infile",
        type=str,
        help="hdf5 file.",
    )
    parser.add_argument(
        "--axes",
        nargs="+",
        type=str,
        default=['pt', 'eta'],
        help="Axes to plot."
    )
    parser.add_argument(
        "--filterProcs",
        nargs="+",
        type=str,
        default=[],
        help="Filter processes by name, e.g. 'ZmumuPostVFP'. If empty, all processes are loaded.",
    )
    parser.add_argument(
        "--hist",
        type=str,
        default="nominal_massWeightW",
        help="Specify histogram names to filter output. If empty, all histograms are loaded. Supports regex.",
    )
    parser.add_argument(
        "--binwnorm",
        type=int,
        default=None
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
        "--labels",
        nargs="+",
        type=str,
        default=[],
        help="Name of histograms to display in legend. Must be of same length as --hists."
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
        help="Use logarithmic scale for the y-axis of the histograms. Default is linear scale."
    )
    parser.add_argument(
        "--rrange",
        default=(0.5, 1.5),
        type=float,
        nargs=2,
        help="Range for the ratio plot (default: 0.5, 1.5).",
    )
    parser.add_argument(
        "--noErrorBars",
        action='store_true'
    )
    parser.add_argument(
        "--noRatioErrorBars",
        action='store_true'
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

            if type(results[proc]) is dict:
                output = results[proc].get("output", {})
                if not output:
                    print(f"No output found for process {proc}.")
                    continue
                available_hists = list(output.keys())
            elif type(results[proc]) is Hist:
                available_hists = [proc]
                output = results

            h = output[args.hist]
            if not (type(h) is Hist):
                h = h.get()

            h_bw = output.get("nominal_breitwigner")
            if not (type(h_bw) is Hist):
                h_bw = output.get("nominal_breitwigner").get()

            if args.selection:
                for sel in args.selection:
                    sel = sel.split()
                    if len(sel) == 3:
                        sel_ax, sel_lb, sel_ub = sel
                        sel_lb = parsing.str_to_complex_or_int(sel_lb)
                        sel_ub = parsing.str_to_complex_or_int(sel_ub)
                        h = h[{sel_ax: slice(sel_lb, sel_ub, sum)}]
                    elif len(sel) == 2:
                        sel_ax, sel_val = sel
                        try:
                            sel_val = parsing.str_to_complex_or_int(sel_val)
                        except argparse.ArgumentTypeError as e:
                            print(e)
                            print("Trying to use as string...")
                            pass
                        h = h[{sel_ax: sel_val}]

            # for each massShift value in the hist, make a separate histogram
            massShift_values = [n for n in h.axes['massShift']]
            hists_to_plot = []
            for massShift in massShift_values:
                h_i = h[{ 'massShift': massShift }]
            #     if args.axes:
            #         h_i = h_i.project(*args.axes)
            #     if len(h_i.axes) > 1:
            #         h_i = hh.unrolledHist(h_i)
                hists_to_plot.append(h_i)
            # fig = plot_tools.makePlotWithRatioToRef(
            #     hists_to_plot,
            #     massShift_values
            # )
            # plot_tools.save_pdf_and_png(
            #     args.outdir,
            #     "massShift_hists",
            #     fig
            # )

            # def breit_wigner_weight(mass=80.379, massW=80.379, widthW=2.085):
            #     """
            #     Return the Breit-Wigner weight for a given mass.
            #     """
            #     m0 = massW
            #     m = mass
            #     gamma = (m0**2 * (m0**2 + widthW**2))**0.5
            #     k = 2*2**0.5/np.pi * m0* widthW * gamma / (m0**2 + widthW**2)
            #     bw = (k/((m**2 - m0**2)**2 + (m0*gamma)**2))
            #     return bw

            # breit_wigner_weights = [ breit_wigner_weight(massW+100) / breit_wigner_weight(massW) for massW in range(-100,101,10)]

            
            # integrate each histogram, plot as a function of massShift
            bw_values = [n for n in h_bw.axes['breitwignerVar']]
            # for bw in bw_values:
            #     h_bw[{ 'breitwignerVar': bw }] *= h_bw[{ 'breitwignerVar': bw }].sum() / h[{ 'massShift': bw }].sum()
            corrections = np.array([h[{'massShift': i}].sum() / h_bw[{ 'breitwignerVar': i }].sum() for i in range(len(bw_values))])
            # h_bw.values()[...] = h_bw.values()[...] * corrections
            print(corrections)
            
            bw_hists = [h_bw[{ 'breitwignerVar': bw }] for bw in bw_values]
            xsec_per_massShiftBW = [h_i.sum() for h_i in bw_hists]
            xsec_per_massShift = [h_i.sum() for h_i in hists_to_plot]
            clean_massShift_values = [m.strip("massShiftW").strip("MeV") for m in massShift_values]
            clean_bw_values = [m.strip("massShift").strip("MeV") for m in bw_values]
            fig, ax = plt.subplots()
            ax.plot(clean_massShift_values, xsec_per_massShift, marker='o', label='massWeightW')
            ax.plot(clean_massShift_values, xsec_per_massShiftBW, marker='o', label='breitwignerVar')
            ax.set_xlabel("massShift")
            ax.set_ylabel("Integrated cross section")
            ax.legend()
            plt.setp(ax.get_xticklabels(), rotation=90)
            plot_tools.save_pdf_and_png(
                args.outdir,
                "massShift_xsec",
                fig
            )
            
                                
if __name__ == "__main__":
    main()