import sys

sys.path.append("../../WRemnants/")
import argparse
import h5py
import pprint

parser = argparse.ArgumentParser(description="Read in a hdf5 file.")
parser.add_argument(
    "infile",
    type=str,
    help="hdf5 file.",
)
args = parser.parse_args()

h5file = h5py.File(args.infile, "r")
print(h5file.keys())

print(h5file["meta"]["pickle_data"].keys())
print(h5file["hpseudodata"][()])
print(h5file["hsumw"][()])

print(h5file["hpseudodata"][()] - h5file["hsumw"][()] < 1e-5)
