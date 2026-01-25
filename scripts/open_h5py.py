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
parser.add_argument(
    "--path",
    type=str,
    default="",
    help="Path inside the hdf5 file to explore.",
)
args = parser.parse_args()

h5file = h5py.File(args.infile, "r")
print(h5file.keys())

if args.path:
    group = h5file[args.path]
    if type(group) is h5py.Dataset:
        # print the data
        print(f"Contents of group {args.path}:")
        print(group[()])
        for g in group:
            if "mb" in str(g):
                print(g)
    elif hasattr(group, "keys"):
        print(f"Keys of group {args.path}:")
        print(group.keys())
    else:
        pprint.pprint(group.attrs.items())
