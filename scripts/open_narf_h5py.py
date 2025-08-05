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
   
    print(results['WplusmunuPostVFP']['output']['nominal_gen_scetlib_dyturboCT18Z_pdfasCorr'].get())
    print(results.keys())
    print(results['WplusmunuPostVFP']['output']['nominal_gen_pdfCT18Z'].get())
    

    # print(results['ZmumuPostVFP']['output'].keys())
    # var_old = results['ZmumuPostVFP']['output']['nominal_pdfCT18Z'].get()[{'pdfVar': 'pdf1CT18ZDown'}]

    # var = results['ZmumuPostVFP']['output']['nominal_pdfUncertByHelicity'].get()[{'pdfVar': 'pdf1CT18ZUp'}]
    # nom = results['ZmumuPostVFP']['output']['nominal'].get()

    #print(var)
    #print(var.values() / var_old.values())