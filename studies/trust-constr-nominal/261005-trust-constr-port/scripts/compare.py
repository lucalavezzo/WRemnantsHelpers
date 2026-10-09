#!/usr/bin/env python3
"""Certify trust-constr results and compare them with NOMSTIFF. BLINDED: alphaS only as differences in sigma.

For each fitresults_<pf>.hdf5 (trust-constr, penalty NOT in the loss):
  - minimizer_status (optimality, constr_violation, barrier, multipliers, constraint values), iterations, wall time
  - NLL (data + constraints, no penalty) vs NOMSTIFF's nllvalreduced minus its stiff penalty
  - Delta alphaS / sigma_NOM, ||Delta theta / sigma_NOM|| over all parameters, top-10 |Delta theta / sigma_NOM|
  - physical NP lambdas and the 5 constraint values (margin 0)
If fitresults_HESS<pf>.hdf5 (data-only Hessian, --noFit, no -r) exists: sigma(alphaS) free / stiff (2e16 spring on
the active face, NOMSTIFF's definition) / projected (face held), via Sherman-Morrison, each / sigma_NOM.
Writes compare.json next to the task logbook and prints a markdown table.
"""
import json
import os
import sys

import numpy as np
import tensorflow as tf

from rabbit import inputdata, io_tools
from rabbit.mappings import helpers as mh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import npwall_tc  # noqa: E402

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
REF = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
CARD = f"{A}/260923_lattice_fits/cards/cardA_latticeASWZ_l4zero_statsyst.hdf5"
OUT = f"{A}/261005_trust_constr_nominal"
TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAU = 8.0
K = 2.0 * np.exp(2 * TAU)  # relu^2 spring constant of the engaged wall
POI = "alphaS"
ACTIVE_TOL = 1e-6  # |constraint value| below which a face counts as active


def load(path):
    fr = io_tools.get_fitresult(path, None)
    h = fr["parms"].get()
    names = np.array([str(n) for n in h.axes[0]])
    x = np.asarray(h.values(), float)
    var = np.asarray(h.variances(), float)
    return fr, names, x, var


def get(fr, key, default=None):
    try:
        v = fr[key]
    except Exception:
        return default
    return v.get() if hasattr(v, "get") and not isinstance(v, dict) else v


fr_n, names, x_n, var_n = load(REF)
sig_n = np.sqrt(var_n)
nll_n = float(fr_n["nllvalreduced"])
ipoi = int(np.where(names == POI)[0][0])

indata = inputdata.FitInputData(CARD)
mapping = mh.load_mapping(
    "wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingMapping",
    indata,
    "margin=0",
)
wall = npwall_tc.NPDampingWallTC(mapping, dtype=tf.float64)
wall.set_expectations(tf.constant(x_n), None, parms=names)
labels = [c.label for c in wall._active]


def constraints(x):
    xv = tf.Variable(tf.constant(x))
    with tf.GradientTape(persistent=True) as t:
        v, lb = wall.constraint_spec(xv, None)
    jac = t.jacobian(v, xv, experimental_use_pfor=False).numpy()
    return v.numpy(), lb.numpy(), jac


def penalty(x):
    return float(wall.compute_nll_penalty(tf.constant(x), None)) * np.exp(2 * TAU)


def sm(cov, a, kinv):
    """(C^-1 + a a^T / kinv)^-1 via Sherman-Morrison; kinv = 1/k (0 = hard projection). a: [m, n]."""
    Ca = cov @ a.T
    M = a @ Ca + kinv * np.eye(a.shape[0])
    return cov - Ca @ np.linalg.solve(M, Ca.T)


def phys(x):
    return {k: float(v) for k, v in wall._physical(tf.constant(x)).items()}


c_n, _, _ = constraints(x_n)
pen_n = penalty(x_n)
rows = {}
rows["NOMSTIFF"] = dict(
    nll_nopen=nll_n - pen_n, penalty=pen_n, constraints=c_n.tolist(), lambdas=phys(x_n)
)


# NOMSTIFF's own covariance, "un-sprung": its Hessian is data + K a a^T on the engaged face (relu^2 past the
# bound), so C_free = (C_nom^-1 - K a a^T)^-1 = sm(C_nom, a, -1/K); and the hard projection sm(C_nom, a, 0).
_, _, jac_n = constraints(x_n)
act_n = np.where(np.abs(c_n) < ACTIVE_TOL)[0]
cov_n = np.asarray(fr_n["cov"].get().values(), float)
a_n = jac_n[act_n]
rows["NOMSTIFF"]["active"] = [labels[i] for i in act_n]
rows["NOMSTIFF"]["sigma_alphaS_over_sigNOM"] = dict(
    stored=float(np.sqrt(cov_n[ipoi, ipoi]) / sig_n[ipoi]),
    free_unsprung=float(np.sqrt(sm(cov_n, a_n, -1.0 / K)[ipoi, ipoi]) / sig_n[ipoi]),
    proj=float(np.sqrt(sm(cov_n, a_n, 0.0)[ipoi, ipoi]) / sig_n[ipoi]),
    edmval=float(get(fr_n, "edmval", np.nan)),
)

for pf in sys.argv[1:]:
    path = f"{OUT}/fitresults_{pf}.hdf5"
    if not os.path.exists(path):
        print(f"[{pf}] missing {path}")
        continue
    fr, nm, x, _ = load(path)
    assert (nm == names).all(), "parameter layout differs from NOMSTIFF"
    st = get(fr, "minimizer_status", {}) or {}
    loss = (
        np.asarray(get(fr, "epoch_loss").values())
        if get(fr, "epoch_loss") is not None
        else []
    )
    t = (
        np.asarray(get(fr, "epoch_time").values())
        if get(fr, "epoch_time") is not None
        else []
    )
    c, lb, jac = constraints(x)
    d = (x - x_n) / sig_n
    order = np.argsort(-np.abs(d))[:10]
    r = dict(
        nll_nopen=float(fr["nllvalreduced"]),
        dnll_vs_nom_nopen=float(fr["nllvalreduced"]) - (nll_n - pen_n),
        penalty_at_x=penalty(x),
        dalphaS_over_sigNOM=float(d[ipoi]),
        norm_dtheta_over_sig=float(np.linalg.norm(d)),
        max_abs_dtheta_over_sig=float(np.max(np.abs(d))),
        top10=[(str(names[i]), float(d[i])) for i in order],
        constraints=c.tolist(),
        active=[labels[i] for i in np.where(np.abs(c - lb) < ACTIVE_TOL)[0]],
        lambdas=phys(x),
        status=st,
        iterations=len(loss),
        wall_s=float(t[-1]) if len(t) else None,
    )
    hpath = f"{OUT}/fitresults_HESS{pf}.hdf5"
    if os.path.exists(hpath):
        frh, nmh, xh, _ = load(hpath)
        assert (nmh == names).all() and np.allclose(
            xh, x, atol=0, rtol=0
        ), "HESS pass not at the TC point"
        cov = np.asarray(frh["cov"].get().values(), float)
        act = np.where(np.abs(c - lb) < ACTIVE_TOL)[0]
        a = jac[act]
        s_free = np.sqrt(cov[ipoi, ipoi])
        out = dict(free=s_free / sig_n[ipoi], n_active=int(len(act)))
        if len(act):
            out["stiff"] = np.sqrt(sm(cov, a, 1.0 / K)[ipoi, ipoi]) / sig_n[ipoi]
            out["proj"] = np.sqrt(sm(cov, a, 0.0)[ipoi, ipoi]) / sig_n[ipoi]
            # correlation of alphaS with the active-face direction (data-only covariance)
            ga = a @ cov[:, ipoi]
            out["rho_alphaS_face"] = (
                ga / np.sqrt(np.diag(a @ cov @ a.T)) / s_free
            ).tolist()
        out["edmval_dataonly"] = float(get(frh, "edmval", np.nan))
        r["sigma_alphaS_over_sigNOM"] = {
            k: (float(v) if not isinstance(v, list) else v) for k, v in out.items()
        }
    rows[pf] = r

json.dump(rows, open(f"{TASK}/compare.json", "w"), indent=1, default=float)
for pf, r in rows.items():
    print(f"== {pf}")
    for k, v in r.items():
        print(f"   {k}: {v}")
