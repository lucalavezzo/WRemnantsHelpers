#!/usr/bin/env python3
"""Results table, cache-free: each fit vs NOMSTIFF and vs LATB8. BLINDED: alphaS only as differences in sigma_NOM and
sigma ratios. Vector-only NLL split at each fit's stored x (as 261007-lattice-term-native/scripts/compare.py):
  wall    = exp(2 tau) * NPDampingWall penalty (margin 0, card A)
  lattice = NOMSTIFF: the 1D Gaussian card term; LATFROZ_*: the frozen native term 1/2 (chi2 - chi2_min) with the fit's
            own options (alpha_s-independent: it depends on the public CS lambdas only); LATB8 (live): not computable
            without alpha_s -> left inside data_bb, the published alpha_s = 0.118 estimate is quoted separately
  priors  = card constraints + the ParamModel Gaussian priors (meta param_priors)
  data_bb = nllvalreduced - wall - lattice - priors
Also, for every fit, the frozen-term Delta chi2 of each n_f variant at the fit's CS lambdas (public), and the tension
p-values: p(Delta chi2_lat; 2 dof) and the lattice GoF chi2_lat,total / 18.
Usage: compare_froz.py LABEL=fitresult[#V1|V2|V3|live|1d] ...   Writes ../compare_froz.json.
"""
import json
import os
import sys

import h5py
import numpy as np
import tensorflow as tf
from scipy.stats import chi2 as CHI2

TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from rabbit import inputdata, io_tools  # noqa: E402
from rabbit.mappings import helpers as mh  # noqa: E402
from rabbit.regularization import helpers as rh  # noqa: E402

from wremnants.postprocessing.scetlib_ad import lattice_cs_term as LT  # noqa: E402
from wremnants.postprocessing.scetlib_ad import np_damping_wall as WALLM  # noqa: E402
from wremnants.postprocessing.scetlib_ad import xsec_backend as XB  # noqa: E402

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
CARD_A = (
    f"{A}/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5"
)
CARD_1D = f"{A}/260923_lattice_fits/cards/cardA_latticeASWZ_l4zero_statsyst.hdf5"
NOMSTIFF = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
TAU = 8.0
ACTIVE_TOL = 1e-5
LAMS = ["lambda2", "lambda4", "delta_lambda2", "lambda2_nu", "lambda4_nu"]
TNPS = ["resumTNP_gamma_nu", "resumTNP_gamma_cusp"]
VOPT = {
    "V1": dict(nf_match=1.0),
    "V2": dict(nf_match=4.18, nf_switch=1.0),
    "V3": dict(nf_match=4.18, nf_scheme="full"),
    "V3lit": dict(nf_match=4.18),
}

indata = inputdata.FitInputData(CARD_A)
with h5py.File(CARD_A, "r") as f:
    SYSTS = [s.decode() if isinstance(s, bytes) else str(s) for s in f["hsysts"][...]]
    CW = np.asarray(f["hconstraintweights"][...], float)
with h5py.File(CARD_1D, "r") as f:
    t = f["external_terms/lattice_cs"]
    E_NM = [n.decode() if isinstance(n, bytes) else str(n) for n in t["params"][...]]
    E_G = t["grad_values"][...].reshape(t["grad_values"].attrs["original_shape"])
    E_H = t["hess_dense"][...].reshape(t["hess_dense"].attrs["original_shape"])
E_MU = -np.linalg.solve(E_H, E_G)
E_C0 = 0.5 * E_MU @ E_H @ E_MU
WALL = rh.load_regularizer(
    "wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingWall",
    mh.load_mapping(
        "wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingMapping",
        indata,
        "margin=0",
    ),
    dtype=tf.float64,
)
_, _sig = XB.configure(
    f"{A}/scetlib_ad_caches/pdf62_y35_260921_y25/cache.conf", threads=4
)
SING = _sig.sub_pieces()[0]
SING.set_pdf_eig_params(29)
NAMES = list(SING.gradient_param_names())
PFZ = LT.frozen_reference(NAMES, np.array(SING.gradient_central(), float), 0.1168)
CORES = {
    k: LT.LatticeCSNativeCore(SING, PFZ, syst="Jnf", require_rules=False, **o)
    for k, o in VOPT.items()
}
CORE_STAT = LT.LatticeCSNativeCore(SING, PFZ, syst="none", require_rules=False)


def frozen_dchi2(core, phys):
    p = core.p_ref.copy()
    p[NAMES.index("np_gnu_lambda2")] = phys["lambda2_nu"]
    p[NAMES.index("np_gnu_lambda4")] = phys.get("lambda4_nu", 0.0)
    return core.chi2_full(p) - core.chi2_min, core.chi2_full(p)


def row(path, kind):
    fr, meta = io_tools.get_fitresult(path, None, meta=True)
    h = fr["parms"].get()
    nm = np.array([str(n) for n in h.axes[0]])
    x = np.asarray(h.values(), float)
    s = np.sqrt(np.asarray(h.variances(), float))
    WALL.set_expectations(tf.constant(x), None, parms=nm)
    xt = tf.constant(x)
    phys = {k: float(v) for k, v in WALL._physical(xt).items()}
    pen = float(WALL.compute_nll_penalty(xt, None)) * np.exp(2 * TAU)
    faces = {
        c.label: float(c.value(phys, WALLM.numpy_relu2) - c.bound) for c in WALL._active
    }
    active = [k for k, v in faces.items() if abs(v) < ACTIVE_TOL or v < 0]
    xd = dict(zip(nm, x))
    if kind == "1d":
        v = np.array([xd.get(n, 0.0) for n in E_NM])
        lat = float(E_G @ v + 0.5 * v @ E_H @ v + E_C0)
    elif kind in CORES:
        lat = 0.5 * frozen_dchi2(CORES[kind], phys)[0]
    else:
        lat = None  # live: alpha_s-dependent, stays in data_bb
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
    nll = float(fr["nllvalreduced"])
    out = dict(
        path=path,
        kind=kind,
        nll=nll,
        wall=pen,
        lattice=lat,
        priors=lc_syst + lc_pm,
        n_model_priors=int(np.sum(msk)),
        data_bb=nll - pen - (lat or 0.0) - lc_syst - lc_pm,
        data_bb_includes_live_lattice=lat is None,
        edm=float(fr["edmval"]),
        lambdas={k: phys.get(k) for k in LAMS},
        sigma_lambdas_phys={
            k: float(s[list(nm).index(k)] * WALL.inputs["specs"][k][1][1])
            for k in LAMS
            if k in nm
        },
        faces=faces,
        active=active,
        tnps={
            k: dict(theta=float(xd[k]), sigma=float(s[list(nm).index(k)]))
            for k in TNPS
            if k in xd
        },
    )
    out["frozen_dchi2_by_variant"] = {
        k: frozen_dchi2(c, phys)[0] for k, c in CORES.items()
    }
    out["frozen_dchi2_stat_only"] = frozen_dchi2(CORE_STAT, phys)[0]
    if kind in CORES:
        d, tot = frozen_dchi2(CORES[kind], phys)
        out["tension"] = dict(
            dchi2_lat=d,
            dof=2,
            p=float(CHI2.sf(d, 2)),
            chi2_lat_total=tot,
            gof_dof=18,
            p_gof=float(CHI2.sf(tot, 18)),
            lattice_only_chi2_min=CORES[kind].chi2_min,
        )
    return out, dict(nm=nm, x=x, s=s)


def main():
    rows, vec = {}, {}
    rows["NOMSTIFF"], vec["NOMSTIFF"] = row(NOMSTIFF, "1d")
    for spec in sys.argv[1:]:
        lab, rest = spec.split("=", 1)
        path, _, kind = rest.partition("#")
        if not os.path.exists(path):
            print(f"[{lab}] missing {path}")
            continue
        rows[lab], vec[lab] = row(path, kind or "live")
    for ref in ("NOMSTIFF", "LATB8"):
        if ref not in vec:
            continue
        rv = vec[ref]
        ra = list(rv["nm"]).index("alphaS")
        rN = vec["NOMSTIFF"]
        sN = rN["s"][list(rN["nm"]).index("alphaS")]
        for lab, v in vec.items():
            ia = list(v["nm"]).index("alphaS")
            rows[lab][f"dalphaS_vs_{ref}_over_sigNOM"] = float(
                (v["x"][ia] - rv["x"][ra]) / sN
            )
            rows[lab][f"sigma_ratio_vs_{ref}"] = float(v["s"][ia] / rv["s"][ra])
            for k in ("nll", "wall", "priors"):
                rows[lab][f"d_{k}_vs_{ref}"] = rows[lab][k] - rows[ref][k]
    json.dump(
        rows,
        open(os.path.join(TASK, "compare_froz.json"), "w"),
        indent=1,
        default=float,
    )
    for k, v in rows.items():
        print(f"== {k}")
        for kk, vv in v.items():
            print(f"   {kk}: {vv}")


if __name__ == "__main__":
    main()
