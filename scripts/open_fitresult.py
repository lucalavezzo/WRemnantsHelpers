import sys
sys.path.append("../../WRemnants/")
import matplotlib.pyplot as plt
import mplhep as hep
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

#print(fitresult['parms'].get())
print(fitresult['parms'].get()['pdfAlphaS'])

# print( fitresult['physics_models']['Project ch0 ptll yll']['channels']['ch0'].keys())
# hobs = fitresult['physics_models']['Project ch0 ptll yll']['channels']['ch0']['hist_data_obs'].get()
# h = fitresult['physics_models']['Project ch0 ptll yll']['channels']['ch0']['hist_prefit_inclusive'].get()

# hvars = fitresult['physics_models']['Project ch0 ptll yll']['channels']['ch0']['hist_prefit_inclusive_variations'].get()
# hdown = hvars[:, :, :, -2j]
# hup = hvars[:, :, :, 2j]
#variations = [n for n in hup.axes[2]]

# import numpy as np
# h_values = h.values()
# hobs_values = hobs.values()
# print(h)
# print(h_values.shape)
# print(np.max(h_values, axis=1))
# ratio = hobs_values / h_values
# print(np.max(ratio), np.min(ratio))
# for v in variations:
#     ratio = h_values/hup[:, :, v].values()
#     #print(np.max(ratio), np.min(ratio), v)
#     if np.max(ratio) > 5:
#         print(f"Variation: {v}")
#     if np.min(ratio) < 0.2:
#         print(f"Variation: {v}")

# print(f"Fit physics_models: {fitresult['physics_models']}")
# print(f"Fit physics_models keys: {fitresult['physics_models'].keys()}")

# for physics_model in fitresult["physics_models"].keys():
#     print(f"Physics model: {physics_model}")
    
#     channels = fitresult["physics_models"][physics_model]["channels"].keys()
#     for channel in channels:
#         print(f"\t\tChannel: {channel}")
#         hists = fitresult["physics_models"][physics_model]["channels"][channel].keys()

#         for hist in hists:
#             print(f"\t\t\tHist: {hist}")
#             #h = fitresult["physics_models"][physics_model]["channels"][channel][hist].get()
#             #print("\t\t", h)

# print(fitresult['parms'].get()[0])