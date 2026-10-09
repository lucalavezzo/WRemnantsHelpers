#!/usr/bin/env python3
"""Asimov closure read-out of ASIMNAT (native term; copy of 261006 asimov_check.py, paths changed) (non-randomised expected toy; truth = every theta 0). Absolute values are
fine here (Asimov, truth known). Prints the largest |theta| over all parameters, and alphaS / CS lambdas / TMD thetas,
and their size relative to the postfit-independent prior widths. Exit 1 if |theta| of alphaS, lambda2_nu, lambda4_nu
> 0.02 (i.e. 4e-5 in alpha_s, 2e-3 in lambda2_nu, 0.01 in lambda4_nu)."""
import json
import sys

import h5py
import numpy as np
from rabbit import io_tools

OUT = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261007_lattice_term_native"
OLD = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261006_lattice_chi2_in_fit"
# the -t 1 (expected, non-randomised) toy is stored as results_toy1, not results_asimov (false-fail 2026-10-06 18:59)
PF = sys.argv[2] if len(sys.argv) > 2 else "ASIMNAT"
SEED = sys.argv[3] if len(sys.argv) > 3 else f"{OLD}/seeds/seed_ASIMFULL_displaced.hdf5"
fr = io_tools.get_fitresult(f"{OUT}/fitresults_{PF}.hdf5", "toy1")
h = fr["parms"].get()
nm = [str(n) for n in h.axes[0]]
x = np.asarray(h.values(), float)
with h5py.File(SEED, "r") as f:
    x0 = f["x"][...]
keys = ["alphaS", "lambda2_nu", "lambda4_nu", "lambda2", "lambda4", "delta_lambda2"]
keys += [k for k in ("resumTNP_gamma_nu", "resumTNP_gamma_cusp") if k in nm]
res = {k: dict(start=float(x0[nm.index(k)]), end=float(x[nm.index(k)])) for k in keys}
i = int(np.argmax(np.abs(x)))
res["_max_abs_theta"] = dict(name=nm[i], value=float(x[i]))
try:
    res["_nll"] = float(fr["nllvalreduced"])
    res["_edm"] = float(fr["edmval"])
except Exception as e:
    res["_err"] = repr(e)
res["_alphaS_phys_end"] = 0.118 + 0.002 * res["alphaS"]["end"]
print(json.dumps(res, indent=1))
json.dump(res, open(sys.argv[1], "w"), indent=1)
ok = all(
    abs(res[k]["end"]) < 0.02
    for k in (
        "alphaS",
        "lambda2_nu",
        "lambda4_nu",
        "resumTNP_gamma_nu",
        "resumTNP_gamma_cusp",
    )
    if k in res
)
print("ASIMOV CLOSURE", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
