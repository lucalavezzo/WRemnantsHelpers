#!/usr/bin/env python3
"""Step 4 table: each fit vs NOMSTIFF. BLINDED: alphaS only as differences in sigma_NOM and sigma ratios.

Vector-only NLL split (no cache load), at each fit's stored x:
  wall     = exp(2 tau) * sum relu2 of the armed NPDampingWall conditions (margin 0, the -r object itself, card A)
  lattice  = NOMSTIFF / T8: the card's Gaussian external term (1D / 2D) ; LATCHI*: the LatticeCSChi2 term 1/2(chi2 - min)
  priors   = 1/2 sum w theta^2 over the card's constrained systs (theta0 = 0) + the ParamModel Gaussian priors (meta
             'param_priors': TMD lambdas, TNPs, PDF eigenvectors)
  data+BB  = nllvalreduced - wall - lattice - priors      (Poisson data term + Barlow-Beeston)
For every fit also: the EXACT lattice chi2 (syst=J and stat-only, k1 profiled) at its CS point, the active wall faces,
the CS/TMD lambdas, k1_hat (frozen table). For an alpha_s-LIVE fit pass kind "none": the live term then stays inside
"data_bb" (data + BB + live lattice), so no alpha_s-dependent lattice value is published; every lattice chi2 / k1_hat
column is the FROZEN-table value at the fit's lambdas. Usage: compare.py LABEL=fitresult[@tau][#lattice-kind] ...  (kind: 1d | 2d | exact | none)
Writes ../compare.json."""
import json
import os
import sys

import h5py
import numpy as np
import tensorflow as tf

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
# copy of 261006-lattice-chi2-in-fit/scripts/compare.py (read-only use of that task's lattice_cs_chi2 copy), writing
# into THIS task; plus a column with the NATIVE term's Delta chi2 at alpha_s = 0.118 (frozen at the anchor, so publishable
# for live fits) at each fit's CS lambdas and CS TNPs.
sys.path.insert(
    0, os.path.join(os.path.dirname(TASK), "261006-lattice-chi2-in-fit", "scripts")
)
import lattice_cs_chi2 as L  # noqa: E402
from rabbit import inputdata, io_tools  # noqa: E402
from rabbit.mappings import helpers as mh  # noqa: E402
from rabbit.regularization import helpers as rh  # noqa: E402

from wremnants.postprocessing.scetlib_ad import np_damping_wall as WALLM  # noqa: E402

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
CARD_A = (
    f"{A}/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5"
)
CARD_1D = f"{A}/260923_lattice_fits/cards/cardA_latticeASWZ_l4zero_statsyst.hdf5"
CARD_2D = f"{A}/260923_lattice_fits/cards/cardA_latticeASWZ_statsyst.hdf5"
NOMSTIFF = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
ACTIVE_TOL = 1e-5
LAMS = ["lambda2", "lambda4", "delta_lambda2", "lambda2_nu", "lambda4_nu"]
TNPS = ["resumTNP_gamma_nu", "resumTNP_gamma_cusp", "resumTNP_gamma_mu_q", "resumTNP_s"]

indata = inputdata.FitInputData(CARD_A)
with h5py.File(CARD_A, "r") as f:
    SYSTS = [s.decode() if isinstance(s, bytes) else str(s) for s in f["hsysts"][...]]
    CW = np.asarray(f["hconstraintweights"][...], float)


def ext_term(card):
    with h5py.File(card, "r") as f:
        t = f["external_terms/lattice_cs"]
        nm = [n.decode() if isinstance(n, bytes) else str(n) for n in t["params"][...]]
        g = t["grad_values"][...].reshape(t["grad_values"].attrs["original_shape"])
        H = t["hess_dense"][...].reshape(t["hess_dense"].attrs["original_shape"])
    mu = -np.linalg.solve(H, g)
    return nm, g, H, 0.5 * mu @ H @ mu


EXT = {"1d": ext_term(CARD_1D), "2d": ext_term(CARD_2D)}
WALL = rh.load_regularizer(
    "wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingWall",
    mh.load_mapping(
        "wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingMapping",
        indata,
        "margin=0",
    ),
    dtype=tf.float64,
)
CORE = {s: L.LatticeCSCore(syst=s) for s in ("J", "none", "Jnf+Jbt", "Jnf+Jbt+pert")}
MIN = {s: c.fit()[0].fun for s, c in CORE.items()}


def lat_reg(tau):
    m = mh.load_mapping(
        "lattice_cs_chi2.LatticeCSMapping", indata, "syst=J", "offset=min", f"tau={tau}"
    )
    return rh.load_regularizer("lattice_cs_chi2.LatticeCSChi2", m, dtype=tf.float64)


from wremnants.postprocessing.scetlib_ad import lattice_cs_term as LT  # noqa: E402
from wremnants.postprocessing.scetlib_ad import xsec_backend as XB  # noqa: E402

_conf, _sig = XB.configure(
    f"{A}/ad_scetlib_caches/pdf62_y35_260921_y25/cache.conf", threads=4
)
_sing = _sig.sub_pieces()[0]
_sing.set_pdf_eig_params(29)
_NAMES = list(_sing.gradient_param_names())
NATIVE = LT.LatticeCSNativeCore(
    _sing, np.array(_sing.gradient_central(), float), require_rules=False
)


def native_dchi2(phys, xd):
    p = NATIVE.p_ref.copy()
    p[_NAMES.index("np_gnu_lambda2")] = phys["lambda2_nu"]
    p[_NAMES.index("np_gnu_lambda4")] = phys.get("lambda4_nu", 0.0)
    p[_NAMES.index("tnp_gamma_nu")] = xd.get("resumTNP_gamma_nu", 0.0)
    p[_NAMES.index("tnp_gamma_cusp")] = xd.get("resumTNP_gamma_cusp", 0.0)
    return NATIVE.chi2_full(p) - NATIVE.chi2_min, NATIVE.k1hat(p)


SNAP_META = f"{A}/261006_lattice_chi2_in_fit/fitresults_LATCHI5R.hdf5"  # param_priors source for flat snapshots


class _Snap(dict):
    """A flat rabbit snapshot (x, parms, attrs loss) dressed as a fitresult: no covariance, nllvalreduced = the
    snapshot's loss. Priors bookkeeping uses SNAP_META's param_priors (same 44-prior configuration).
    """


def load(path):
    if "snapshot_" in os.path.basename(path):
        with h5py.File(path, "r") as f:
            x, nm, loss = (
                f["x"][...],
                f["parms"][...].astype(str),
                float(f.attrs["loss"]),
            )
        _, meta = io_tools.get_fitresult(SNAP_META, None, meta=True)
        fr = _Snap(nllvalreduced=loss)
        return fr, meta, np.array(nm), np.asarray(x, float), np.full(len(x), np.nan)
    fr, meta = io_tools.get_fitresult(path, None, meta=True)
    h = fr["parms"].get()
    nm = np.array([str(n) for n in h.axes[0]])
    return (
        fr,
        meta,
        nm,
        np.asarray(h.values(), float),
        np.sqrt(np.asarray(h.variances(), float)),
    )


def row(label, path, tau, kind, ref=None):
    fr, meta, nm, x, s = load(path)
    WALL.set_expectations(tf.constant(x), None, parms=nm)
    xt = tf.constant(x)
    phys = {k: float(v) for k, v in WALL._physical(xt).items()}
    vals = {k: v for k, v in phys.items()}
    pen = float(WALL.compute_nll_penalty(xt, None)) * np.exp(2 * tau)
    faces = {}
    for c in WALL._active:
        faces[c.label] = float(c.value(vals, WALLM.numpy_relu2) - c.bound)
    active = [k for k, v in faces.items() if abs(v) < ACTIVE_TOL or v < 0]
    lam = dict(
        lambda_inf_nu=2.0,
        lambda2_nu=phys["lambda2_nu"],
        lambda4_nu=phys.get("lambda4_nu", 0.0),
    )
    if kind in EXT:
        enm, g, H, c0 = EXT[kind]
        v = np.array([x[list(nm).index(n)] if n in nm else 0.0 for n in enm])
        lat = float(g @ v + 0.5 * v @ H @ v + c0)
    elif kind == "exact":
        reg = lat_reg(tau)
        reg.set_expectations(xt, None, parms=nm)
        lat = float(reg.compute_nll_penalty(xt, None)) * np.exp(2 * tau)
    else:
        lat = 0.0
    xd = dict(zip(nm, x))
    lc_syst = 0.5 * sum(w * xd[sy] ** 2 for sy, w in zip(SYSTS, CW) if w > 0)
    pp = meta.get("param_priors")
    pn = [n.decode() if isinstance(n, bytes) else str(n) for n in pp["params"]]
    msk, sg, mu = (
        np.asarray(pp["mask"]),
        np.asarray(pp["sigmas"], float),
        np.asarray(pp["means"], float),
    )
    lc_pm = float(
        sum(0.5 * ((xd[n] - mu[i]) / sg[i]) ** 2 for i, n in enumerate(pn) if msk[i])
    )
    npri = int(np.sum(msk))
    nll = float(fr["nllvalreduced"])
    try:
        edm = float(fr["edmval"])
    except Exception:
        edm = None
    out = dict(
        path=path,
        tau=tau,
        lattice_kind=kind,
        nll=nll,
        wall=pen,
        lattice=lat,
        priors=lc_syst + lc_pm,
        priors_card=lc_syst,
        priors_model=lc_pm,
        n_model_priors=npri,
        data_bb=nll - pen - lat - lc_syst - lc_pm,
        edm=edm,
        lambdas={k: phys.get(k) for k in LAMS},
        sigma_lambdas_phys={
            k: float(s[list(nm).index(k)] * WALL.inputs["specs"][k][1][1])
            for k in LAMS
            if k in nm
        },
        k1hat_J=CORE["J"].k1hat(lam),
        k1hat_stat=CORE["none"].k1hat(lam),
        lat_chi2_exact_J=CORE["J"].chi2(lam) - MIN["J"],
        lat_chi2_exact_stat=CORE["none"].chi2(lam) - MIN["none"],
        # frozen-table (alpha_s = 0.118) values at the fit's lambdas: alpha_s-independent, safe to publish for live fits
        lat_chi2_frozen_JnfJbt=CORE["Jnf+Jbt"].chi2(lam) - MIN["Jnf+Jbt"],
        lat_chi2_frozen_JnfJbtpert=CORE["Jnf+Jbt+pert"].chi2(lam) - MIN["Jnf+Jbt+pert"],
        lat_chi2_native_JnfJbt_as0118=native_dchi2(phys, xd)[0],
        k1hat_native_as0118=native_dchi2(phys, xd)[1],
        faces=faces,
        active=active,
        tnps={
            k: dict(theta=float(xd[k]), sigma=float(s[list(nm).index(k)]))
            for k in TNPS
            if k in xd
        },
    )
    if ref is not None:
        ia = list(nm).index("alphaS")
        ra = list(ref["nm"]).index("alphaS")
        out["dalphaS_over_sigNOM"] = float((x[ia] - ref["x"][ra]) / ref["s"][ra])
        out["sigma_ratio"] = (
            float(s[ia] / ref["s"][ra]) if np.isfinite(s[ia]) and s[ia] > 0 else None
        )
        for k in ("nll", "wall", "lattice", "priors", "data_bb"):
            out[f"d_{k}"] = out[k] - ref["row"][k]
    return out, dict(nm=nm, x=x, s=s)


def main():
    rows = {}
    r, refv = row("NOMSTIFF", NOMSTIFF, 8.0, "1d")
    refv["row"] = r
    r["dalphaS_over_sigNOM"], r["sigma_ratio"] = 0.0, 1.0
    rows["NOMSTIFF"] = r
    for spec in sys.argv[1:]:
        lab, rest = spec.split("=", 1)
        rest, _, kind = rest.partition("#")
        path, _, tau = rest.partition("@")
        if not os.path.exists(path):
            print(f"[{lab}] missing {path}")
            continue
        rows[lab], _ = row(lab, path, float(tau or 8), kind or "exact", ref=refv)
    json.dump(
        rows, open(os.path.join(TASK, "compare.json"), "w"), indent=1, default=float
    )
    for k, v in rows.items():
        print(f"== {k}")
        for kk, vv in v.items():
            print(f"   {kk}: {vv}")


if __name__ == "__main__":
    main()
