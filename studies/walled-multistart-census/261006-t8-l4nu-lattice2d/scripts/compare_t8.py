#!/usr/bin/env python3
"""T8 results table: each fit vs NOMSTIFF (and XWSTIFF for orientation). BLINDED: alphaS only as differences / sigma_NOM.

NLL bookkeeping (cards differ only by the lattice external term):
  nll_nopen   = nllvalreduced minus the stiff tau=8 penalty at x (0 for trust-constr results: penalty not in their loss)
  lat_term    = the card's own external term at x (= 1/2 chi2_Gauss); NOMSTIFF: 1D term; T8 fits: 2D term
  z_part      = nll_nopen - lat_term  (data + BB + the 44 card/model priors; identical definition on both cards)
  dNLL_2Dcard = nll_nopen - NOMSTIFF's point evaluated on the 2D card (376.9356603, step-2 gate)
Constraints: the 6 armed NPDampingWallTC conditions on the 2D card (margin 0); active = |c - lb| < 1e-5.
sigma(alphaS) from HESS<pf> (data + priors + lattice, no wall): free / stiff (2e16 spring on active faces) / face-held,
via Sherman-Morrison (as trust-constr-nominal); for walled trust-krylov results their stored covariance too.
Exact lattice chi2 (stat cov, k1 profiled; 260923-scetlib-kernel-fit machinery) at each end point, minus the 2D best.
Writes ../compare.json."""
import json
import os
import sys

import numpy as np
import tensorflow as tf

from rabbit import inputdata, io_tools
from rabbit.mappings import helpers as mh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common as C  # noqa: E402
import npwall_tc  # noqa: E402

KFD = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/lattice-cs-kernel/260923-scetlib-kernel-fit"
sys.path.insert(0, KFD)
import kernel_fit as KF  # noqa: E402

TAU = 8.0
K = 2.0 * np.exp(2 * TAU)
ACTIVE_TOL = 1e-5
POI = "alphaS"
LAT_D = KF.load_data()
LAT_P = np.load(f"{KFD}/pert_tables.npz")["data_nf5"]
LAT_BEST = KF.Fit(LAT_D, LAT_P, ["l2", "l4", "k1"], fixed=dict(linf=2.0)).run()["chi2"]


def exact_lat(l2, l4):
    return (
        KF.chi2_at(LAT_D, LAT_P, dict(linf=2.0, l2=l2, l4=l4), ks=("k1",))["chi2"]
        - LAT_BEST
    )


def load(path):
    fr = io_tools.get_fitresult(path, None)
    h = fr["parms"].get()
    return (
        fr,
        np.array([str(n) for n in h.axes[0]]),
        np.asarray(h.values(), float),
        np.sqrt(np.asarray(h.variances(), float)),
    )


def get(fr, key, default=None):
    try:
        v = fr[key]
    except Exception:
        return default
    return v.get() if hasattr(v, "get") and not isinstance(v, dict) else v


def ext_term(card):
    import h5py

    with h5py.File(card, "r") as f:
        t = f["external_terms/lattice_cs"]
        nm = [n.decode() if isinstance(n, bytes) else str(n) for n in t["params"][...]]
        g = t["grad_values"][...].reshape(t["grad_values"].attrs["original_shape"])
        H = t["hess_dense"][...].reshape(t["hess_dense"].attrs["original_shape"])
    mu = -np.linalg.solve(H, g)
    return nm, g, H, 0.5 * mu @ H @ mu


T1, T2 = ext_term(C.CARD_1D), ext_term(C.CARD_2D)

frN, nN, xN, sN = load(C.NOMSTIFF)
names = np.array(
    list(nN) + ["lambda4_nu"]
)  # the 2D-card layout is checked against each result below
ipoi = int(np.where(names == POI)[0][0])
SN = sN[list(nN).index(POI)]
indata = inputdata.FitInputData(C.CARD_2D)
mapping = mh.load_mapping(
    "wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingMapping",
    indata,
    "margin=0",
)
wall = npwall_tc.NPDampingWallTC(mapping, dtype=tf.float64)
wall.set_expectations(tf.constant(np.zeros(len(names))), None, parms=names)
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
    idx = {s: i for i, s in enumerate(nm)}
    return np.array([x[idx[s]] if s in idx else 0.0 for s in names])


def constraints(x):
    xv = tf.Variable(tf.constant(x))
    with tf.GradientTape(persistent=True) as t:
        v, lb = wall.constraint_spec(xv, None)
    return v.numpy(), lb.numpy(), t.jacobian(v, xv, experimental_use_pfor=False).numpy()


def penalty(x):
    return float(wall.compute_nll_penalty(tf.constant(x), None)) * np.exp(2 * TAU)


def sm(cov, a, kinv):
    Ca = cov @ a.T
    return cov - Ca @ np.linalg.solve(a @ Ca + kinv * np.eye(a.shape[0]), Ca.T)


def lat(term, x):
    nm, g, H, c = term
    v = np.array([x[list(names).index(n)] for n in nm])
    return float(g @ v + 0.5 * v @ H @ v + c)


def row(path, xe, nll_stored, term, walled, fr=None, nm=None):
    c, lb, jac = constraints(xe)
    pen = penalty(xe) if walled else 0.0
    ph = {k: float(v) for k, v in wall._physical(tf.constant(xe)).items()}
    act = np.where(np.abs(c - lb) < ACTIVE_TOL)[0]
    nll = nll_stored - pen
    lt = lat(term, xe)
    r = dict(
        source=path,
        nll_nopen=nll,
        penalty=pen,
        lat_term=lt,
        z_part=nll - lt,
        dalphaS_over_sigNOM=float((xe[ipoi] - xN[list(nN).index(POI)]) / SN),
        lambdas=ph,
        c_minus_lb=dict(zip(short, (c - lb).tolist())),
        active=[short[i] for i in act],
        lat_chi2_card2D=2 * lat(T2, xe),
        lat_chi2_exact_stat=exact_lat(ph["lambda2_nu"], ph["lambda4_nu"]),
    )
    return r, act, jac


rows = {}
xNe = embed(nN, xN)
r, _, _ = row(C.NOMSTIFF, xNe, float(frN["nllvalreduced"]), T1, True)
r["note"] = "1D lattice card, lambda4_nu held 0"
r["sigma_alphaS_over_sigNOM"] = {"stored(stiff)": 1.0}
rows["NOMSTIFF"] = r
NOM_NOPEN, NOM_Z = r["nll_nopen"], r["z_part"]
NOM_ON_2D = NOM_NOPEN - r["lat_term"] + lat(T2, xNe)
frW, nW, xW, sW = load(C.XWSTIFF)
r, _, _ = row(C.XWSTIFF, embed(nW, xW), float(frW["nllvalreduced"]), T2, True)
r["note"] = (
    "NO lattice card (CS priors on); its lat_term/z_part are what the 2D term WOULD be (not in its NLL)"
)
r["z_part"] = None
rows["XWSTIFF"] = r

for pf in sys.argv[1:]:
    path = f"{C.OUT}/fitresults_{pf}.hdf5"
    snap = False  # never open a running fit's snapshot: an HDF5 read lock can make its snapshot write fail
    if not os.path.exists(path):
        print(f"[{pf}] no fitresult yet")
        continue
    fr, nm, x, s = load(path)
    assert sorted(nm) == sorted(names), "layout"
    xe = embed(nm, x)
    st = get(fr, "minimizer_status", {}) or {}
    tc = st.get("method", "") == "trust-constr" or "optimality" in st
    el, et = get(fr, "epoch_loss"), get(fr, "epoch_time")
    loss = np.asarray(el.values()) if el is not None else []
    tt = np.asarray(et.values()) if et is not None else []
    nlls = float(fr["nllvalreduced"]) if "nllvalreduced" in fr else float(loss[-1])
    r, act, jac = row(path, xe, nlls, T2, walled=not tc)
    r.update(
        snapshot=snap,
        trust_constr=tc,
        dNLL_vs_NOMSTIFF_nopen=r["nll_nopen"] - NOM_NOPEN,
        dNLL_vs_NOMpoint_on_2Dcard=r["nll_nopen"] - NOM_ON_2D,
        dz_part_vs_NOMSTIFF=r["z_part"] - NOM_Z,
        status={
            k: v
            for k, v in st.items()
            if k not in ("constraint_values", "constraint_lower_bounds")
        },
        iterations=int(len(loss)),
        wall_s=float(tt[-1]) if len(tt) else None,
        edmval=float(get(fr, "edmval", np.nan)),
    )
    mult = st.get("multipliers")
    if mult is not None and len(mult) == len(short):
        r["multipliers"] = dict(zip(short, [float(m) for m in mult]))
    d = (x[[list(nm).index(n) for n in nN]] - xN) / sN
    r["norm_dtheta_over_sigNOM"] = float(np.linalg.norm(d))
    sig = {}
    covs = []
    if not tc and get(fr, "cov") is not None:
        covs.append(("stored", np.asarray(fr["cov"].get().values(), float), nm))
    hpath = f"{C.OUT}/fitresults_HESS{pf}.hdf5"
    if os.path.exists(hpath):
        frh, nmh, xh, _ = load(hpath)
        assert np.array_equal(embed(nmh, xh), xe), "HESS pass not at the fit point"
        covs.append(("HESS", np.asarray(frh["cov"].get().values(), float), nmh))
        sig["edmval_HESS"] = float(get(frh, "edmval", np.nan))
    for lab, cov, nmc in covs:
        P = np.array([list(nmc).index(n) for n in names])
        cov = cov[np.ix_(P, P)]
        sig[f"{lab}_free"] = float(np.sqrt(cov[ipoi, ipoi]) / SN)
        if len(act):
            a = jac[act]
            sig[f"{lab}_stiff"] = float(np.sqrt(sm(cov, a, 1.0 / K)[ipoi, ipoi]) / SN)
            sig[f"{lab}_face_held"] = float(np.sqrt(sm(cov, a, 0.0)[ipoi, ipoi]) / SN)
            ga = a @ cov[:, ipoi]
            sig[f"{lab}_rho_alphaS_face"] = dict(
                zip(
                    [short[i] for i in act],
                    (
                        ga / np.sqrt(np.diag(a @ cov @ a.T)) / np.sqrt(cov[ipoi, ipoi])
                    ).tolist(),
                )
            )
        i4 = list(names).index("lambda4_nu")
        sig[f"{lab}_sigma_lambda4_nu_phys"] = float(0.5 * np.sqrt(cov[i4, i4]))
        sig[f"{lab}_rho_alphaS_lambda4_nu"] = float(
            cov[ipoi, i4] / np.sqrt(cov[ipoi, ipoi] * cov[i4, i4])
        )
    r["sigma_alphaS_over_sigNOM"] = sig
    rows[pf] = r

rows["_meta"] = dict(NOMSTIFF_point_on_2D_card=NOM_ON_2D, lat_exact_best_chi2=LAT_BEST)
json.dump(rows, open(f"{C.TASK}/compare.json", "w"), indent=1, default=float)
for pf, r in rows.items():
    print(f"== {pf}")
    for k, v in (r.items() if isinstance(r, dict) else []):
        print(f"   {k}: {v}")
