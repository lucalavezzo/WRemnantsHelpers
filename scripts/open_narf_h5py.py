import sys
sys.path.append("../../WRemnants/")

from wums import ioutils
import argparse
import h5py
import pprint
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

h5file = h5py.File(args.infile, "r")
results = load_results_h5py(h5file)
print(results.keys())
pprint.pprint(results['meta_info'])
print(results['ZtautauPostVFP'].keys())
#print(results['ZtautauPostVFP']['output'].keys())

print(results['ZtautauPostVFP']['weight_sum'])
print(results['ZtautauPostVFP']['event_count'])

# h = results['ZtautauPostVFP']['output']['nominal_muonResolutionSyst_responseWeights'].get()
# print(h)

h_ref = results['ZtautauPostVFP']['output']['nominal_asimov'].get()
print(h_ref)
h_ref = h_ref[:, :, :, :]
ref_vals = h_ref.values()

scale=253054471 / (1161.553608621 * 1000)
h_raw = results['ZtautauPostVFP']['output']['nominal_unweighted'].get()
h_raw = h_raw[:, :, :, :]
raw_vals = h_raw.values()
# print(raw_vals[:10, 0, 0, 0], ref_vals[:10, 0, 0, 0])

h_w = results['ZtautauPostVFP']['output']['nominal_unweighted_withWeights'].get()
print(h_w)

for i in range(50):
    #h = results['ZtautauPostVFP']['output']['nominal_muonResolutionSyst_responseWeights'].get()

    #h = h[:, ::sum, ::sum, ::sum, i, 0]
    #print(h.shape)

    #h_ref = results['ZtautauPostVFP']['output']['nominal_asimov'].get()
    #h_ref = h_ref[:, ::sum, ::sum, ::sum]

    #hep.histplot(h, label=f"Variation 0, Toy {i}")
    #hep.histplot(h_ref, label="Nominal Asimov")
    #plt.legend()
    #plt.savefig(f"/home/submit/lavezzo/public_html/alphaS/debugging/test_toy{i}.png")
    #plt.close()

    h = results['ZtautauPostVFP']['output']['nominal_muonResolutionSyst_responseWeights'].get()
    
    h = h[:, :, :,:, i]
    # h = hh.unrolledHist(
    #     h
    # )
    
    # h_ref = hh.unrolledHist(
    #     h_ref
    # )

    vals = h.values()
    #print(vals)
    #print(np.nanmax(vals/ref_vals))
    #print(np.nanmin(vals/ref_vals))
    arr = vals/ref_vals
    #print(np.nanargmax(arr))
    max_idx = np.unravel_index(np.nanargmax(arr), arr.shape)
    #print(max_idx)
    if np.nanmax(arr) > 3:
        print("value of variation histogram at problematic point:", h[max_idx[0], max_idx[1], max_idx[2], max_idx[3]])
        print("value of nominal histogram at problematic point:", h_ref[max_idx[0], max_idx[1], max_idx[2], max_idx[3]])
        print("their ratio:", np.nanmax(arr))
        print("which happens at bin:")
        for i in range(len(max_idx)):
            print(h.axes[i].name, ":", h.axes[i].edges[max_idx[i]], h.axes[i].edges[max_idx[i]+1])
        print("which has this many events: ", scale*h_raw[max_idx[0], max_idx[1], max_idx[2], max_idx[3]].value)
        print()
    # print(ref_vals[np.nanargmax(vals/ref_vals)])
    # print(vals[np.nanargmax(vals/ref_vals)])
    
    # hep.histplot(h, label=f"Variation 0, Toy {i}")
    # hep.histplot(h_ref, label="Nominal Asimov")
    # plt.legend()
    # plt.savefig(f"/home/submit/lavezzo/public_html/alphaS/debugging/test_unroll_toy{i}.png")
    # plt.close()