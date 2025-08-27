import sys
sys.path.append("../../WRemnants/")
import matplotlib.pyplot as plt
import mplhep as hep
import rabbit.io_tools
import argparse

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
    default=['pdfAlphaS'],
    type=str,
    help="Parms in the fitresult to print the pull of."
)
args = parser.parse_args()

fitresult, meta = rabbit.io_tools.get_fitresult(
    args.infile, result=args.result, meta=True
)

print(f"Fit result keys: {fitresult.keys()}")
print(f"Meta data keys: {meta.keys()}")
print()
print('edmval', fitresult['edmval'])
parms = fitresult['parms'].get()
for p in args.parms:
    print(p, parms[p])