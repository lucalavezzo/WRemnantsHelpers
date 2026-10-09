#!/usr/bin/env python3
"""Is the alphaS blinding offset identical for the two cards (C's card A vs NOMSTIFF's lattice card)?

Uses rabbit's own Blinding class (no re-implementation). Prints ONLY equality booleans and the
data-integrality flag, never an offset value. The SCETlib AD model declares no blind_additive_scale /
blind_exempt (grep of wremnants/postprocessing/scetlib_ad), so a stub with npoi=1, params=['alphaS'] is exact.
"""
import numpy as np
from rabbit import inputdata
from rabbit.blinding import Blinding

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
CARDS = {
    "cardA (C, XWSTIFF)": f"{A}/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5",
    "lattice l4zero (NOMSTIFF)": f"{A}/260923_lattice_fits/cards/cardA_latticeASWZ_l4zero_statsyst.hdf5",
}


class Stub:
    npoi = 1
    params = ["alphaS"]
    allowNegativeParam = True


vals = {}
for k, p in CARDS.items():
    ind = inputdata.FitInputData(p, None, host_memory=False)
    d = np.asarray(ind.data_obs)
    b = Blinding(ind, Stub(), enabled=True)
    if b.values_poi_add is None:
        b._init_values()
    vals[k] = (
        np.array(b.values_poi_add),
        np.array(b.values_theta),
        [s for s in ind.systs],
    )
    print(
        f"{k}: nbins {d.size}, data_obs all-integral = {bool(np.all(d == np.floor(d)))}, "
        f"nsyst {ind.nsyst}, n NOI {len(ind.noiidxs)}, alphaS offset nonzero = {bool(vals[k][0][0] != 0)}"
    )
(a, ta, sa), (b_, tb, sb) = vals.values()
print("alphaS offset IDENTICAL across cards:", bool(np.array_equal(a, b_)))
print("NOI offsets nonzero in either card:", bool(np.any(ta != 0) or np.any(tb != 0)))
