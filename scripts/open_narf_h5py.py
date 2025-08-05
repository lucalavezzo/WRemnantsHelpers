import os, sys
sys.path.append("../../WRemnants/")
import argparse
import h5py
from wums import ioutils

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
    "--noShowHists",
    action='store_true',
    help="Don't print all histograms, for all samples."
)
parser.add_argument(
    "--filterProcs",
    nargs="+",
    default=[],
    help="Filter processes to show info about. Supports multiple process names."
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
   
    if not args.notShowHists:
        for sample in results.keys():
            if args.filterProcs and sample not in args.filterProcs:
                continue
            print(f"Sample: {sample}\n")
            hists = results[sample].keys()
            if args.filterHists:
                hists = [h for h in hists if args.filterHists in h]
            print(f"Histograms: {hists}\n")