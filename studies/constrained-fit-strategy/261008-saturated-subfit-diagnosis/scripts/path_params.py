#!/usr/bin/env python3
"""Which parameters does the projected-ptll sub-fit move, start (LATB8 main minimum) -> end (SATB8 sub-fit minimum)?

Reads only stored fitresults (no cache). Displacements in units of LATB8's postfit sigma (M0 covariance). alphaS is
blinded: only its displacement in sigma is reported, never a value. Also: the seeded run's start (LATL4ZY35WALLWARM
sub-fit snapshot, scope all) vs the same end point, and the bin scales s_j = x_j**2.
Writes path_params.json.
"""
import json
import os
import sys

import h5py
import numpy as np

sys.path.insert(0, "/home/submit/lavezzo/alphaS/WRemnants/wums")
from wums import ioutils  # noqa: E402

T = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
D = f"{C}/261007_lattice_term_native"


def load(path):
    return ioutils.pickle_load_h5py(h5py.File(path)["results"])


def hvals(h):
    hh = h.get()
    return (
        list(hh.axes[0]),
        hh.values(),
        (hh.variances() if hh.variances() is not None else None),
    )


m0 = load(f"{D}/fitresults_LATB8.hdf5")
n0, x0, v0 = hvals(m0["parms"])
cov0 = m0["cov"].get().values()
s1 = load(f"{D}/fitresults_SATB8.hdf5")["mappings"]["Project ch0 ptll"]["saturated_fit"]
n1, x1, _ = hvals(s1["parms"])
sa = load(f"{D}/fitresults_SATB8SA.hdf5")["mappings"]["Project ch0 ptll"][
    "saturated_fit"
]
na, xa, _ = hvals(sa["parms"])
seed = h5py.File(
    f"{C}/260928_lattice_y35_fits/snapshot_fitresults_LATL4ZY35WALLWARM_saturated_Project_ch0_ptll.hdf5"
)
ns = [p.decode() if isinstance(p, bytes) else str(p) for p in seed["parms"][...]]
xs = seed["x"][...]

i0 = {p: k for k, p in enumerate(n0)}
i1 = {p: k for k, p in enumerate(n1)}
sig0 = np.sqrt(np.diag(cov0))
out = dict(n_main=len(n0), n_sub=len(n1))

common = [p for p in n0 if p in i1]
d = np.array([x1[i1[p]] - x0[i0[p]] for p in common])
s = np.array([sig0[i0[p]] for p in common])
z = d / s
order = np.argsort(-np.abs(z))
out["top_moves_in_M0_sigma"] = [dict(p=common[k], dz=float(z[k])) for k in order[:40]]
out["norm_dz"] = float(np.linalg.norm(z))
out["n_abs_dz_gt"] = {str(t): int((np.abs(z) > t).sum()) for t in [0.1, 0.5, 1, 3, 10]}
# Mahalanobis length of the move in M0 metric (what the M0 Hessian charges for it, ~ prior+data cost, quadratic)
idx = np.array([i0[p] for p in common])
H0 = np.linalg.inv(cov0)
out["quad_cost_M0"] = float(0.5 * d @ H0[np.ix_(idx, idx)] @ d)

sat = [p for p in n1 if p.startswith("saturated_")]
xsat = np.array([x1[i1[p]] for p in sat])
out["bin_scales_s"] = dict(
    min=float((xsat**2).min()),
    max=float((xsat**2).max()),
    mean=float((xsat**2).mean()),
    rms_minus1=float(np.sqrt(((xsat**2 - 1) ** 2).mean())),
)
out["bin_scales_list"] = [float(v) for v in xsat**2]

# seeded run: distance seed -> end, in M0 sigma, over the common parameters
iS = {p: k for k, p in enumerate(ns)}
cs = [p for p in common if p in iS]
dzs = np.array([(x1[i1[p]] - xs[iS[p]]) / sig0[i0[p]] for p in cs])
dz0 = np.array([(x1[i1[p]] - x0[i0[p]]) / sig0[i0[p]] for p in cs])
out["seed_vs_end_norm_dz"] = float(np.linalg.norm(dzs))
out["start_vs_end_norm_dz"] = float(np.linalg.norm(dz0))
out["seed_top"] = [
    dict(p=cs[k], dz=float(dzs[k])) for k in np.argsort(-np.abs(dzs))[:15]
]
ias = {p: k for k, p in enumerate(na)}
out["SATB8_vs_SATB8SA_max_abs_dx"] = float(
    max(abs(x1[i1[p]] - xa[ias[p]]) for p in n1 if p in ias)
)


# groups
def grp(p):
    for pre, g in [
        ("saturated_", "bin scales"),
        ("pdfEig", "pdfEig"),
        ("resumTNP", "resumTNP"),
        ("lambda", "NP lambda"),
        ("delta_lambda", "NP lambda"),
        ("alphaS", "alphaS"),
        ("resum", "resum other"),
    ]:
        if p.startswith(pre):
            return g
    return "card nuisances"


gz = {}
for p, zz in zip(common, z):
    gz.setdefault(grp(p), []).append(zz)
out["group_norm_dz"] = {
    g: dict(n=len(v), norm=float(np.linalg.norm(v)), max=float(np.max(np.abs(v))))
    for g, v in gz.items()
}
json.dump(out, open(f"{T}/path_params.json", "w"), indent=1)
print(
    json.dumps(
        {k: v for k, v in out.items() if k not in ("bin_scales_list",)}, indent=1
    )[:6000]
)
