import numpy as np
from rabbit import inputdata

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
cards = {
    "A(2D)": f"{A}/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5",
    "ptll": f"{A}/260925_Z_1D_card_adcorr/ZMassDilepton_ptll_adexclpdf/ZMassDilepton.hdf5",
    "yll": f"{A}/260925_Z_1D_card_adcorr/ZMassDilepton_yll_adexclpdf/ZMassDilepton.hdf5",
}
S = {}
tot = {}
for k, p in cards.items():
    ind = inputdata.FitInputData(p)
    systs = [s.decode() if isinstance(s, bytes) else str(s) for s in ind.systs]
    d = np.asarray(ind.data_obs)
    S[k] = set(systs)
    tot[k] = d.sum()
    print(
        f"{k:6s} nbins={d.size:4d} data_sum={d.sum():.0f} nsyst={len(systs)} axes={[a.name for a in ind.channel_info['ch0']['axes']]}"
    )
for k in ["ptll", "yll"]:
    print(
        k,
        "systs only in A:",
        len(S["A(2D)"] - S[k]),
        "only in 1D:",
        len(S[k] - S["A(2D)"]),
        sorted(S["A(2D)"] - S[k])[:5],
        sorted(S[k] - S["A(2D)"])[:5],
        "data ratio to A:",
        tot[k] / tot["A(2D)"],
    )
