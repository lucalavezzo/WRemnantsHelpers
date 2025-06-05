import sys
sys.path.append("../../WRemnants/")
import os
from wums import ioutils
import argparse
import h5py
import pprint
from wums import ioutils
from wums import boostHistHelpers as hh
import numpy as np
import mplhep as hep
import matplotlib.pyplot as plt

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
args = parser.parse_args()

with h5py.File(args.infile, "r") as h5file:
    results = load_results_h5py(h5file)
    print("Keys in h5 file:", h5file.keys())

    print([x for x in results['ZmumuPostVFP']['output'].keys() if 'pdf' in x])

    h = results['ZmumuPostVFP']['output']['pdfMSHT20mbrange_0']
    print(h.get())