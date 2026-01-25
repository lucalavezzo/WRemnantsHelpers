import sys

sys.path.append("../../WRemnants/")
import argparse
import h5py
import pprint
import lz4.frame
import pickle

parser = argparse.ArgumentParser(description="Read in a .pkl.lz4 file.")
parser.add_argument(
    "infile",
    type=str,
    help="Input file.",
)
parser.add_argument(
    "--path",
    type=str,
    default="",
    help="Path inside the pickle data to print.",
)
args = parser.parse_args()

with lz4.frame.open(args.infile, "rb") as f:
    data = pickle.load(f)

print("Keys in the file:")
pprint.pprint(data.keys())

if args.path:
    full_path = args.path.split("/")
    subdata = data
    print(f"Navigating to path: {args.path}")
    for p in full_path:
        subdata = subdata[p]
    if hasattr(subdata, "keys"):
        print(f"Keys at path {args.path}:")
        pprint.pprint(subdata.keys())
    pprint.pprint(subdata)
