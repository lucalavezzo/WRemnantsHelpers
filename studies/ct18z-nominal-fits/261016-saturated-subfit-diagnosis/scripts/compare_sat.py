#!/usr/bin/env python3
"""Compare the saturated-projection sub-fit of two rabbit fitresults (blinded: alphaS as a difference only).
usage: compare_sat.py REF.hdf5 NEW.hdf5 [mapping]"""
import sys, json, numpy as np, h5py
from wums import ioutils

ref, new = sys.argv[1], sys.argv[2]
mp = sys.argv[3] if len(sys.argv) > 3 else "Project ch0 ptll"


def load(p):
    r = ioutils.pickle_load_h5py(h5py.File(p, "r")["results"])
    m = r["mappings"][mp]
    s = m["saturated_fit"]
    h = s["parms"].get()
    names = np.array(h.axes["parms"]).astype(str)
    cov = s["cov"].get().values() if "cov" in s else None
    return dict(
        nll_main=float(r["nllvalreduced"]),
        nll_sat=float(s["nllvalreduced"]),
        q=float(m["chi2_saturated"]),
        ms={
            k: (v if not hasattr(v, "tolist") else v.tolist())
            for k, v in s["minimizer_status"].items()
        },
        x=h.values(),
        names=names,
        cov=cov,
    )


a, b = load(ref), load(new)
out = {}
for k, d in (("ref", a), ("new", b)):
    q = 2 * (d["nll_main"] - d["nll_sat"])
    out[k] = dict(
        nll_main=d["nll_main"],
        nll_sat=d["nll_sat"],
        q_stored=d["q"],
        q_recomputed=q,
        status=d["ms"],
    )
out["dq_new_minus_ref"] = out["new"]["q_recomputed"] - out["ref"]["q_recomputed"]
assert (a["names"] == b["names"]).all()
dx = b["x"] - a["x"]
sig = (
    np.sqrt(np.clip(np.diag(b["cov"]), 0, None))
    if b["cov"] is not None
    else np.ones_like(dx)
)
with np.errstate(divide="ignore", invalid="ignore"):
    pull = np.where(sig > 0, dx / sig, np.nan)
order = np.argsort(-np.nan_to_num(np.abs(pull)))
out["max_abs_dx"] = float(np.max(np.abs(dx)))
out["largest_dx_over_sigma_sat"] = [
    (str(a["names"][i]), float(dx[i]), float(pull[i])) for i in order[:12]
]
ia = list(a["names"]).index("alphaS")
out["alphaS_dx_over_sigma_sat (blinded difference only)"] = float(pull[ia])
print(json.dumps(out, indent=1, default=str))
