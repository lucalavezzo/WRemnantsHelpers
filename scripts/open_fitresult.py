import sys
sys.path.append("../../WRemnants/")

import combinetf2.io_tools
import argparse

parser = argparse.ArgumentParser(
    description="Read fit result from hdf5 file from combinetf2 or root file from combinetf1"
)
parser.add_argument(
    "infile",
    type=str,
    help="hdf5 file from combinetf2 or root file from combinetf1",
)
parser.add_argument(
    "--result",
    default=None,
    type=str,
    help="fitresults key in file (e.g. 'asimov'). Leave empty for data fit result.",
)
args = parser.parse_args()

fitresult, meta = combinetf2.io_tools.get_fitresult(
    args.infile, result=args.result, meta=True
)

print(f"Fit result: {fitresult}")
print(f"Meta data: {meta}")
print(f"Fit result keys: {fitresult.keys()}")
print(f"Meta data keys: {meta.keys()}")

print(f"Fit physics_models: {fitresult['physics_models']}")
print(f"Fit physics_models keys: {fitresult['physics_models'].keys()}")

h = fitresult["physics_models"]["Basemodel"]['channels']['ch0']["hist_prefit_inclusive_variations"].get()
print(h)
print()
ax = h.axes[2]
for i in range(len(ax)):
    if 'alpha' in ax[i].lower():
        print(ax[i])