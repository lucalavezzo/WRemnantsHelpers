"""XWSTIFF configuration (card A, no lattice, lambda4_nu FREE): which wall conditions NPDampingWallTC arms, and their
values (margin 0) at the seed (C mapped into XWSTIFF's frame), XWSTIFF, CMR1B and XL4ZSTIFF (mapped by name; its
held lambda4_nu / lambda_inf* take XWSTIFF's... no: the param-model anchors, i.e. 0 offsets -> we set them from the
seed only where names are missing and report which). Never prints alphaS (only norms over all parameters).
Writes seed_feasibility.json next to the logbook."""

import json
import os

import h5py
import numpy as np
import tensorflow as tf

import npwall_tc
from rabbit import inputdata, io_tools
from rabbit.mappings import helpers as mh

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
REF = f"{A}/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5"
CARD = (
    f"{A}/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5"
)
SEED = f"{A}/261005_cold_min_restart/seeds/seed_1b_C_in_XWSTIFF.hdf5"
OTHERS = {
    "XWSTIFF": REF,
    "CMR1B": f"{A}/261005_cold_min_restart/fitresults_CMR1B.hdf5",
    "XL4ZSTIFF": f"{A}/260930_stiff_wall_fits/fitresults_XL4ZSTIFF.hdf5",
}
TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(p):
    h = io_tools.get_fitresult(p, None)["parms"].get()
    return (
        np.array([str(n) for n in h.axes[0]]),
        np.asarray(h.values(), float),
        np.sqrt(np.asarray(h.variances(), float)),
    )


names, xr, sr = load(REF)
indata = inputdata.FitInputData(CARD)
mapping = mh.load_mapping(
    "wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingMapping",
    indata,
    "margin=0",
)
reg = npwall_tc.NPDampingWallTC(mapping, dtype=tf.float64)
reg.set_expectations(tf.constant(xr), None, parms=names)
labels = reg.constraint_labels()
print("armed conditions:", labels)
out = dict(armed=labels, points={})

with h5py.File(SEED) as f:
    n = np.array(
        [v.decode() if isinstance(v, bytes) else str(v) for v in f["parms"][...]]
    )
    xs = np.asarray(f["x"][...], float)
assert (n == names).all()
pts = {"seed_C": xs}
for k, p in OTHERS.items():
    nm, x, _ = load(p)
    if len(nm) == len(names) and (nm == names).all():
        pts[k] = x
    else:  # XL4ZSTIFF: lambda4_nu etc. held -> not in its vector; they sit at the anchor (theta = 0)
        idx = {s: i for i, s in enumerate(nm)}
        missing = [s for s in names if s not in idx]
        xx = np.array([x[idx[s]] if s in idx else 0.0 for s in names])
        print(f"{k}: {len(missing)} names absent, set to theta=0 (anchor): {missing}")
        out[f"{k}_absent"] = missing
        pts[k] = xx
for k, x in pts.items():
    v, lb = reg.constraint_spec(tf.constant(x), None)
    v, lb = v.numpy(), lb.numpy()
    lam = {kk: float(vv) for kk, vv in reg._physical(tf.constant(x)).items()}
    d = (x - xr) / sr
    out["points"][k] = dict(
        c_minus_lb=(v - lb).tolist(),
        feasible=bool(np.all(v >= lb)),
        lambdas=lam,
        norm_dtheta_over_sigXW=float(np.linalg.norm(d)),
    )
    print(
        f"{k:10s} feasible={bool(np.all(v>=lb))} c-lb=[{', '.join(f'{c:+.4g}' for c in v-lb)}] "
        f"||dtheta/sigXW||={np.linalg.norm(d):.1f}"
    )
    print("           lambdas:", {kk: round(vv, 7) for kk, vv in lam.items()})
json.dump(out, open(f"{TASK}/seed_feasibility.json", "w"), indent=1)
