import sys
sys.path.append("../../WRemnants/")

from wums import ioutils
import argparse
import h5py
import pprint

def load_results_h5py(h5file):
    if "results" in h5file.keys():
        return ioutils.pickle_load_h5py(h5file["results"])
    else:
        return {k: ioutils.pickle_load_h5py(v) for k, v in h5file.items()}

parser = argparse.ArgumentParser(
    description="Read in a hdf5 file."
)
parser.add_argument(
    "-i",
    "--infile",
    type=str,
    help="hdf5 file.",
)
args = parser.parse_args()

h5file = h5py.File(args.infile, "r")
results = load_results_h5py(h5file)
print(results.keys())
pprint.pprint(results['meta_info'])
print(results['ZmumuPostVFP']['output']['nominal_MCtoys'].get())
print(results['ZmumuPostVFP']['output']['nominal'].get())
print(results['ZmumuPostVFP']['output']['nominal_MCtoys'].get()[0.0j, 0.0j,0.0j,0.0j,1.0j])
print(results['ZmumuPostVFP']['output']['nominal'].get()[0.0j, 0.0j,0.0j,0.0j,1.0j])