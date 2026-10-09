"""N_data of card A (real data, 60<mll<120 by construction of the card) per ptll cut, and the Zmumu share."""

import h5py, numpy as np
from wums import ioutils

C = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5"
f = h5py.File(C, "r")
m = ioutils.pickle_load_h5py(f["meta"])
ax = m["channel_info"]["ch0"]["axes"]
pt = np.asarray(ax[0].edges)
ny = len(ax[1].edges) - 1
d = f["hdata_obs"][...].reshape(len(pt) - 1, ny)
norm = f["hnorm"][...].reshape(len(pt) - 1, ny, 4)
for cut in (20, 30, 44):
    k = np.searchsorted(pt, cut)
    print(
        f"ptll<{cut}: N_data={d[:k].sum():.0f}  pred total={norm[:k].sum():.0f}  Zmumu frac={norm[:k,:,2].sum()/norm[:k].sum():.4f}"
    )
print(
    m["meta_info_input"].get("command", "")[:600]
    if isinstance(m["meta_info_input"], dict)
    else ""
)
