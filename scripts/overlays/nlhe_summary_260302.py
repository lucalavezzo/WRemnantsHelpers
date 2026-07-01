import numpy as np
from utilities.io_tools import input_tools
from wums import boostHistHelpers as hh

f_massive = "/scratch/submit/cms/alphaS/260302_gen_massiveBottom_nlhe/w_z_gen_dists_maxFiles_m1_hadronsSel_massive_nlheSel_260302.hdf5"
f_massless = "/scratch/submit/cms/alphaS/260302_gen_massiveBottom_nlhe/w_z_gen_dists_maxFiles_1000_nnpdf31_hadronsSel_massless_nlheSel_260302.hdf5"

resM, _, _ = input_tools.read_infile(f_massive)
resN, _, _ = input_tools.read_infile(f_massless)


def materialize(h):
    return h.get() if hasattr(h, "get") else h


hM = hh.scaleHist(
    materialize(resM["Zbb_MiNNLO"]["output"]["nominal_gen"]),
    resM["Zbb_MiNNLO"]["dataset"]["xsec"] / resM["Zbb_MiNNLO"]["weight_sum"],
    createNew=True,
)
hN = hh.scaleHist(
    materialize(resN["Zmumu_MiNNLO"]["output"]["nominal_gen"]),
    resN["Zmumu_MiNNLO"]["dataset"]["xsec"] / resN["Zmumu_MiNNLO"]["weight_sum"],
    createNew=True,
)

hN_b0 = hN[{"bottom_sel": 0}]
hN_b1 = hN[{"bottom_sel": 1}]
hM_b1 = hM[{"bottom_sel": 1}]

corr = hh.addHists(hN_b0, hM_b1)
scale = np.sum(hN_b1.values()) / np.sum(hM_b1.values())
corr_norm = hh.addHists(hN_b0, hh.scaleHist(hM_b1, scale, createNew=True))

for name, hcorr in [("unnorm", corr), ("norm", corr_norm)]:
    for axis in ["ptVgen", "absYVgen"]:
        hcn = hcorr.project(axis)
        hnn = hN.project(axis)
        r = hh.divideHists(hcn, hnn)
        v = r.values()
        ref = hnn.values()
        m = ref > 0
        vv = v[m]
        ww = ref[m]
        print(
            name,
            axis,
            f"min={np.min(vv):.6f}",
            f"max={np.max(vv):.6f}",
            f"mean={np.mean(vv):.6f}",
            f"wmean={np.average(vv, weights=ww):.6f}",
        )

print(
    f"selected_ratio_massless_over_massive={np.sum(hN_b1.values())/np.sum(hM_b1.values()):.6f}"
)
print(f"massive_sel_frac={np.sum(hM_b1.values())/np.sum(hM.values()):.6f}")
print(f"massless_sel_frac={np.sum(hN_b1.values())/np.sum(hN.values()):.6f}")
