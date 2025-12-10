import sys

sys.path.append("../../WRemnants/")
import matplotlib.pyplot as plt
import mplhep as hep
import rabbit.io_tools
import argparse
import pprint
import wums.ioutils

parser = argparse.ArgumentParser(
    description="Read fit result from hdf5 file from rabbit or root file from combinetf1"
)
parser.add_argument(
    "infile",
    type=str,
    help="hdf5 file from rabbit or root file from combinetf1",
)
parser.add_argument(
    "--result",
    default=None,
    type=str,
    help="fitresults key in file (e.g. 'asimov'). Leave empty for data fit result.",
)
parser.add_argument(
    "--parms",
    nargs="+",
    default=[],
    type=str,
    help="Parms in the fitresult to print the pull of.",
)
parser.add_argument(
    "--path",
    default="",
    type=str,
    help="Open a specific, slash-separated, path inside the HDF5 file.",
)
args = parser.parse_args()

fitresult, meta = rabbit.io_tools.get_fitresult(
    args.infile, result=args.result, meta=True
)

print(f"Fit result keys: {fitresult.keys()}")
print(f"Meta data keys: {meta.keys()}")
for k, v in meta.items():
    if "meta" in k:
        continue  # suppress verbose meta info
    print(f"{k}: {v}")
print()
print("edmval", fitresult["edmval"])
parms = fitresult["parms"].get()
for p in args.parms:
    print(p, parms[p])

if args.path:
    print()
    full_path = args.path.split("/")
    h = fitresult

    print("-" * 20)
    print(f"Navigating to path: {args.path}")
    print()

    for p in full_path:
        print("-" * 20)
        print(f"At path: {p}")
        h = h[p]
        if type(h) is wums.ioutils.H5PickleProxy:
            h = h.get()

        if type(h) is dict:
            print(p, "has keys:", list(h.keys()))
            pprint.pprint(h)
        else:
            print(f"{p}: {h}")
        print()
