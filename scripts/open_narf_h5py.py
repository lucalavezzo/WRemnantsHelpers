import os, sys
sys.path.append("../../WRemnants/")
import argparse
import h5py
from wums import ioutils
from hist import Hist

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
    "--noListHists",
    action='store_true',
    help="Don't list all histograms, for all samples."
)
parser.add_argument(
    "--printHists",
    action='store_true',
    help="Print histograms. (default=False)"
)
parser.add_argument(
    "--filterProcs",
    nargs="+",
    default=[],
    help="Filter processes to show info about. Supports multiple process names."
)
parser.add_argument(
    "--excludeProcs",
    nargs="+",
    default=['meta_info'],
    help="Don't show info about these processes. Supports multiple process names."
)
parser.add_argument(
    "--filterHists",
    type=str,
    default=None,
    help="Filter histograms to print. Supports one string that will be checked against all histogram names in the file."
)
args = parser.parse_args()

with h5py.File(args.infile, "r") as h5file:
    results = load_results_h5py(h5file)
    print(f"Samples in file: {results.keys()}\n")
   
    if not args.noListHists:
        for sample in results.keys():
            if args.filterProcs and sample not in args.filterProcs:
                continue
            if args.excludeProcs and sample in args.excludeProcs:
                continue
            print(f"Sample: {sample}")

            if type(results[sample]) == dict:
                hists = results[sample]['output'].keys()
                if args.filterHists:
                    hists = [h for h in hists if args.filterHists in h]
                print(f"Histograms: {hists}\n")
                if args.printHists:
                    for h in hists:
                        print(h, "\n", results[sample]['output'][h].get(), "\n")
            elif type(results[sample]) == Hist:
                if args.printHists:
                    print(results[sample])
            print()