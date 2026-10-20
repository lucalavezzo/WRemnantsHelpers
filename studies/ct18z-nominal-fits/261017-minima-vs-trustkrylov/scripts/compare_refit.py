#!/usr/bin/env python3
"""Warm refit end point (new objective, seeded at the old minimum) vs the cold new minimum: max |dtheta|, in sigma of
the cold fit (face-held cov; zero-variance bound-held params reported raw), physical NP lambdas. Blinded: differences only.
usage: compare_refit.py REFIT COLD"""
import sys
import numpy as np
from rabbit import io_tools
from wremnants.postprocessing.scetlib_ad import np_damping_wall as W
from rabbit import inputdata

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
CARD = (
    f"{A}/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5"
)
inp = W.resolve_wall_inputs(inputdata.FitInputData(CARD))
r, c = (io_tools.get_fitresult(p, None) for p in sys.argv[1:3])
nm = [str(n) for n in r["parms"].get().axes[0]]
assert nm == [str(n) for n in c["parms"].get().axes[0]]
xr, xc = r["parms"].get().values(), c["parms"].get().values()
s = np.sqrt(np.clip(np.diag(c["cov"].get().values()), 0, None))
d = xr - xc
ok = s > 1e-12
p = np.where(ok, d / np.where(ok, s, 1), np.nan)
print(
    "NLL refit",
    repr(float(r["nllvalreduced"])),
    "cold",
    repr(float(c["nllvalreduced"])),
    "diff",
    float(r["nllvalreduced"]) - float(c["nllvalreduced"]),
)
print("max|dtheta|", np.max(np.abs(d)), nm[int(np.argmax(np.abs(d)))])
print(
    "max|dtheta/sigma|",
    np.nanmax(np.abs(p)),
    nm[int(np.nanargmax(np.abs(p)))],
    " zero-sigma params:",
    [(nm[i], d[i]) for i in np.where(~ok)[0]],
)
print("dalphaS/sigma", p[nm.index("alphaS")])
for n in ["lambda2", "lambda4", "delta_lambda2", "lambda2_nu", "lambda4_nu"]:
    k, cf = inp["specs"][n]
    i = nm.index(n)
    print(f"  {n}: refit {cf[0]+cf[1]*xr[i]:+.8f} cold {cf[0]+cf[1]*xc[i]:+.8f}")
