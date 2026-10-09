#!/usr/bin/env python3
"""Certify a trust-constr result in the XWSTIFF configuration and compare it with XWSTIFF, XL4ZSTIFF and CMR1B.
BLINDED: alphaS only as differences in sigma (sigma_XW = XWSTIFF's stored sigma). Never prints an absolute alphaS.

For fitresults_<pf>.hdf5 (trust-constr, penalty NOT in the loss; its nllvalreduced is penalty-free):
  - minimizer_status (status, optimality, constr_violation, final barrier mu, multipliers), iterations, wall time
  - penalty-free NLL minus each reference's penalty-free NLL (reference nllvalreduced minus its stiff tau=8 penalty,
    recomputed with the wall's own conditions)
  - Delta alphaS / sigma_XW against each reference; ||Delta theta / sigma_ref|| (each ref's own stored sigma, over the
    names both vectors share), and the same norm with wall-pinned entries (|.| > 50) dropped, plus the top entries
  - physical NP lambdas, the 6 constraint values (margin 0), the active faces (|c - lb| < 1e-6) and their multipliers
If fitresults_HESS<pf>.hdf5 (data-only Hessian, --noFit, no -r) exists: sigma(alphaS) free (data only) / stiff (2e16
relu^2 spring on each active face, XWSTIFF's definition) / face-held (hard projection), via Sherman-Morrison, / sigma_XW.
Writes compare.json next to the task logbook.
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
REFS = {
    "XWSTIFF": f"{A}/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5",
    "XL4ZSTIFF": f"{A}/260930_stiff_wall_fits/fitresults_XL4ZSTIFF.hdf5",
    "CMR1B": f"{A}/261005_cold_min_restart/fitresults_CMR1B.hdf5",
}
CARD = (
    f"{A}/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5"
)
OUT = f"{A}/261006_tc_from_C"
TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAU = 8.0
K = 2.0 * np.exp(2 * TAU)  # relu^2 spring constant of the engaged wall
POI = "alphaS"
ACTIVE_TOL = 1e-5  # stiff-wall references sit up to ~1e-6 PAST a face (g/2e^{2tau}); count those as active
PINNED = 50.0  # |Delta theta / sigma_ref| above this = a wall-pinned reference sigma


def load(path):
    fr = io_tools.get_fitresult(path, None)
    h = fr["parms"].get()
    names = np.array([str(n) for n in h.axes[0]])
    return (
        fr,
        names,
        np.asarray(h.values(), float),
        np.sqrt(np.asarray(h.variances(), float)),
    )


def get(fr, key, default=None):
    try:
        v = fr[key]
    except Exception:
        return default
    return v.get() if hasattr(v, "get") and not isinstance(v, dict) else v


fr_xw, names, x_xw, sig_xw = load(REFS["XWSTIFF"])
ipoi = int(np.where(names == POI)[0][0])
SXW = sig_xw[ipoi]

indata = inputdata.FitInputData(CARD)
mapping = mh.load_mapping(
    "wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingMapping",
    indata,
    "margin=0",
)
wall = npwall_tc.NPDampingWallTC(mapping, dtype=tf.float64)
wall.set_expectations(tf.constant(x_xw), None, parms=names)
labels = wall.constraint_labels()
SHORT = {
    "lambda4_nu >= 0": "λ4_ν",
    "lambda2_nu >= 0": "λ2_ν",
    "lambda2 + delta_lambda2*Y^2 >= 0 at |Y|=0": "L2(0)",
    "3*lambda_inf^2*lambda4 + L2^3 >= 0 at |Y|=0": "B(0)",
    "lambda2 + delta_lambda2*Y^2 >= 0 at |Y|=2.5": "L2(2.5)",
    "3*lambda_inf^2*lambda4 + L2^3 >= 0 at |Y|=2.5": "B(2.5)",
}
short = [next(v for k, v in SHORT.items() if lab.startswith(k)) for lab in labels]


def embed(nm, x):
    """Map a vector onto XWSTIFF's names (absent names, e.g. XL4ZSTIFF's held lambda4_nu, at theta = 0)."""
    idx = {s: i for i, s in enumerate(nm)}
    return np.array([x[idx[s]] if s in idx else 0.0 for s in names])


def constraints(x):
    xv = tf.Variable(tf.constant(x))
    with tf.GradientTape(persistent=True) as t:
        v, lb = wall.constraint_spec(xv, None)
    jac = t.jacobian(v, xv, experimental_use_pfor=False).numpy()
    return v.numpy(), lb.numpy(), jac


def penalty(x):
    return float(wall.compute_nll_penalty(tf.constant(x), None)) * np.exp(2 * TAU)


def sm(cov, a, kinv):
    """(C^-1 + a^T a / kinv)^-1 via Sherman-Morrison-Woodbury; kinv = 1/k (0 = hard projection). a: [m, n]."""
    Ca = cov @ a.T
    M = a @ Ca + kinv * np.eye(a.shape[0])
    return cov - Ca @ np.linalg.solve(M, Ca.T)


def phys(x):
    return {k: float(v) for k, v in wall._physical(tf.constant(x)).items()}


refs = {}
for rn, p in REFS.items():
    fr, nm, x, s = load(p)
    xe = embed(nm, x)
    c, lb, _ = constraints(xe)
    pen = penalty(xe)
    refs[rn] = dict(fr=fr, names=nm, x=x, sig=s, xe=xe)
    refs[rn]["row"] = dict(
        nll_walled=float(fr["nllvalreduced"]),
        penalty=pen,
        nll_nopen=float(fr["nllvalreduced"]) - pen,
        c_minus_lb=dict(zip(short, (c - lb).tolist())),
        active=[
            short[i]
            + (" (held 0)" if short[i] == "λ4_ν" and len(nm) != len(names) else "")
            for i in np.where(np.abs(c - lb) < ACTIVE_TOL)[0]
        ],
        lambdas=phys(xe),
        n_params=int(len(nm)),
        dalphaS_vs_XW_over_sigXW=float((xe[ipoi] - x_xw[ipoi]) / SXW),
        sigma_alphaS_over_sigXW=float(s[list(nm).index(POI)] / SXW),
        edmval=float(get(fr, "edmval", np.nan)),
    )
rows = {rn: r["row"] for rn, r in refs.items()}


def distances(x):
    out = {}
    for rn, r in refs.items():
        nm = r["names"]
        idx = {s: i for i, s in enumerate(names)}
        sel = np.array([idx[s] for s in nm])
        d = (x[sel] - r["x"]) / r["sig"]
        keep = np.abs(d) <= PINNED
        order = np.argsort(-np.abs(d))[:8]
        out[rn] = dict(
            dnll_nopen=None,
            dalphaS_over_sigXW=float((x[ipoi] - r["xe"][ipoi]) / SXW),
            norm_dtheta_over_sigref=float(np.linalg.norm(d)),
            norm_dtheta_over_sigref_unpinned=float(np.linalg.norm(d[keep])),
            pinned_dropped=[str(nm[i]) for i in np.where(~keep)[0]],
            top=[(str(nm[i]), round(float(d[i]), 4)) for i in order if nm[i] != POI],
        )
    return out


for pf in sys.argv[1:]:
    path = f"{OUT}/fitresults_{pf}.hdf5"
    if not os.path.exists(path):
        path = f"{OUT}/snapshot_fitresults_{pf}.hdf5"
        if not os.path.exists(path):
            print(f"[{pf}] missing")
            continue
        print(f"[{pf}] using SNAPSHOT {path}")
    fr, nm, x, _ = load(path)
    assert (nm == names).all(), "parameter layout differs from XWSTIFF"
    st = get(fr, "minimizer_status", {}) or {}
    el, et = get(fr, "epoch_loss"), get(fr, "epoch_time")
    loss = np.asarray(el.values()) if el is not None else []
    t = np.asarray(et.values()) if et is not None else []
    c, lb, jac = constraints(x)
    nll = (
        float(fr["nllvalreduced"])
        if "nllvalreduced" in fr
        else (float(loss[-1]) if len(loss) else np.nan)
    )
    act = np.where(np.abs(c - lb) < ACTIVE_TOL)[0]
    mult = st.get("multipliers")
    r = dict(
        source=path,
        nll_nopen=nll,
        penalty_at_x_if_walled=penalty(x),
        vs=distances(x),
        c_minus_lb=dict(zip(short, (c - lb).tolist())),
        active=[short[i] for i in act],
        multipliers=(
            dict(zip(short, mult))
            if mult is not None and len(mult) == len(short)
            else mult
        ),
        lambdas=phys(x),
        status={
            k: v
            for k, v in st.items()
            if k not in ("constraint_values", "constraint_lower_bounds")
        },
        iterations=int(len(loss)),
        wall_s=float(t[-1]) if len(t) else None,
    )
    for rn in refs:
        r["vs"][rn]["dnll_nopen"] = nll - rows[rn]["nll_nopen"]
    hpath = f"{OUT}/fitresults_HESS{pf}.hdf5"
    if os.path.exists(hpath):
        frh, nmh, xh, _ = load(hpath)
        assert (nmh == names).all() and np.array_equal(
            xh, x
        ), "HESS pass not at the TC point"
        cov = np.asarray(frh["cov"].get().values(), float)
        a = jac[act]
        s_free = np.sqrt(cov[ipoi, ipoi])
        out = dict(free=s_free / SXW, n_active=int(len(act)))
        if len(act):
            out["stiff"] = np.sqrt(sm(cov, a, 1.0 / K)[ipoi, ipoi]) / SXW
            out["face_held"] = np.sqrt(sm(cov, a, 0.0)[ipoi, ipoi]) / SXW
            ga = a @ cov[:, ipoi]
            out["rho_alphaS_face"] = dict(
                zip(
                    [short[i] for i in act],
                    (ga / np.sqrt(np.diag(a @ cov @ a.T)) / s_free).tolist(),
                )
            )
        out["edmval_dataonly"] = float(get(frh, "edmval", np.nan))
        r["sigma_alphaS_over_sigXW"] = {
            k: (float(v) if not isinstance(v, dict) else v) for k, v in out.items()
        }
    rows[pf] = r

json.dump(rows, open(f"{TASK}/compare.json", "w"), indent=1, default=float)
for pf, r in rows.items():
    print(f"== {pf}")
    for k, v in r.items():
        print(f"   {k}: {v}")
