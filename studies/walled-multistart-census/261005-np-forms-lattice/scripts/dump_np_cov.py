"""Dump physical NP lambdas + their Hessian covariance (fitted ones) for the census-study NP-form plots.
physical = anchor + width*theta (widths/anchors as printed by physical_lambdas.py for these cards).
"""

import json, sys
import numpy as np
from rabbit import io_tools

C = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/"
FITS = {
    "NOMSTIFF": "260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5",
    "LATWARM": "260928_lattice_y35_fits/fitresults_LATL4ZY35WALLWARM.hdf5",
}
MAP = {
    "lambda2": (0.4, 0.5),
    "lambda4": (0.4, 0.5),
    "delta_lambda2": (0.0, 0.5),
    "lambda2_nu": (0.15, 0.1),
}
out = {}
for k, f in FITS.items():
    r = io_tools.get_fitresult(C + f, None)
    h = r["parms"].get()
    names = [str(x) for x in h.axes[0]]
    v = h.values()
    cov = r["cov"].get().values()
    idx = [names.index(n) for n in MAP]
    w = np.array([MAP[n][1] for n in MAP])
    mu = np.array([MAP[n][0] + MAP[n][1] * v[i] for n, i in zip(MAP, idx)])
    cv = cov[np.ix_(idx, idx)] * np.outer(w, w)
    out[k] = {"names": list(MAP), "mu": mu.tolist(), "cov": cv.tolist()}
    print(k, dict(zip(MAP, np.round(mu, 6))), "sig", np.round(np.sqrt(np.diag(cv)), 5))
json.dump(out, open(sys.argv[1], "w"), indent=1)
