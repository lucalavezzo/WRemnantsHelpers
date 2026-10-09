#!/usr/bin/env python3
"""Stage 1 of the headline NP-function figures (261008-np-function-figures): everything that needs SCETlib or the
scetlib_ad fit machinery, written to ../np_figs_data.npz + ../np_figs_data.json. Stage 2 (plot.py) only draws.

Run in the container with the gamma-nu-points SCETlib build (no cache load, no fit):
  agent_setup.sh --scetlib /work/submit/lavezzo/alphaS/scetlib-gamma-nu-points/scetlib-cms/build -- python3 compute.py

What is computed
* The lattice term exactly as LATFROZ_V3 builds it: LatticeCSNativeCore at the frozen reference p_ref (anchor with
  alpha_s(mZ) := 0.1168, CS TNPs := 0), syst=Jnf, nfmatch=4.18, nfscheme=full. From it:
  lattice-only (lambda2_nu, lambda4_nu) and cov = 2 H^-1 (fit_final), k1hat at that optimum (final C).
* gamma_zeta(b_T; mu = 2 GeV) = 1/2 gamma_nu from SCETlib DrellYan.gamma_nu_points at p_ref with ONLY
  (lambda2_nu, lambda4_nu) replaced: the perturbative part is the same frozen kernel in every curve, so no fitted
  alpha_s enters anywhere (blinding-safe). Bands: Gaussian sampling of (lambda2_nu, lambda4_nu) through the exact
  kernel (16/84 % envelope) and, as a cross-check, linear propagation J C J^T with the SCETlib gradient (order=1).
* Physical NP lambdas + their covariance from the fitresults (theta -> physical via the NPDampingWall's own map, the
  same one the fit uses; all maps are linear 'unit' maps). Never reads or stores alphaS.
* Gaussian toys of ALL floating NP lambdas (TMD + CS) for the F_NP bands of figure 2.
* The exact lattice Delta chi^2 surface on a (lambda2_nu, lambda4_nu) grid for figure 3.
"""
import json
import os
import sys

import h5py
import numpy as np
import tensorflow as tf

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
from rabbit import inputdata, io_tools  # noqa: E402
from rabbit.mappings import helpers as mh  # noqa: E402
from rabbit.regularization import helpers as rh  # noqa: E402

from wremnants.postprocessing.scetlib_ad import lattice_cs_term as LT  # noqa: E402
from wremnants.postprocessing.scetlib_ad import xsec_backend as XB  # noqa: E402

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
CARD_A = (
    f"{A}/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5"
)
CONF = f"{A}/scetlib_ad_caches/pdf62_y35_260921_y25/cache.conf"
FITS = {
    "LATFROZ_V3": f"{A}/261008_latfroz_nf_variants/fitresults_LATFROZ_V3.hdf5",
    "XWSTIFF": f"{A}/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5",
    "NOMSTIFF": f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5",
}
AFZ = 0.1168
NTOY = int(os.environ.get("NTOY", "2000"))
NP_LAMS = [
    "lambda_inf",
    "lambda2",
    "lambda4",
    "delta_lambda2",
    "lambda_inf_nu",
    "lambda2_nu",
    "lambda4_nu",
]
SC = {"lambda2_nu": "np_gnu_lambda2", "lambda4_nu": "np_gnu_lambda4"}
rng = np.random.default_rng(20261008)

# ---------------------------------------------------------------- the frozen kernel and the lattice term (V3)
_, sigma = XB.configure(CONF, threads=8)
SING = sigma.sub_pieces()[0]
SING.set_pdf_eig_params(29)  # as compare_froz.py (registry identical to the fit's)
NAMES = list(SING.gradient_param_names())
ANCHOR = np.array(SING.gradient_central(), float)
PFZ = LT.frozen_reference(NAMES, ANCHOR, AFZ)
CORE = LT.LatticeCSNativeCore(
    SING, PFZ, syst="Jnf", require_rules=False, nf_match=4.18, nf_scheme="full"
)
IL = [NAMES.index(SC["lambda2_nu"]), NAMES.index(SC["lambda4_nu"])]
print(
    "[compute] frozen reference:",
    {
        n: float(PFZ[NAMES.index(n)])
        for n in (
            "alphas",
            "tnp_gamma_nu",
            "tnp_gamma_cusp",
            "np_gnu_lambda_inf",
            "np_gnu_b0_bmax",
            "np_gnu_lambda2",
            "np_gnu_lambda4",
        )
    },
)
FF = CORE.fit_final
LAM_LAT = np.array(FF["lam"], float)
COV_LAT = 2.0 * np.linalg.inv(FF["hess"])
P_LAT = CORE._p_lam(LAM_LAT)
K1 = CORE.k1hat(P_LAT)
print(
    f"[compute] lattice-only V3: lam = {LAM_LAT}, sigma = {np.sqrt(np.diag(COV_LAT))}, "
    f"rho = {COV_LAT[0,1]/np.sqrt(COV_LAT[0,0]*COV_LAT[1,1]):.3f}, chi2_min = {CORE.chi2_min:.4f}, k1hat = {K1:.4f}"
)


def p_of(l2, l4):
    p = PFZ.copy()
    p[IL[0]], p[IL[1]] = l2, l4
    return p


def zeta(bT, l2, l4, order=0):
    r = SING.gamma_nu_points(
        np.ascontiguousarray(bT, float),
        2.0,
        np.ascontiguousarray(p_of(l2, l4)),
        order,
        0,
        0.0,
    )
    v = 0.5 * np.asarray(r["value"])
    if order == 0:
        return v
    return v, 0.5 * np.asarray(r["grad"])[:, IL]


FM = CORE.fm_to_gevinv
B_LAT = np.linspace(0.02, 1.0, 197)  # fm
B_FULL = np.concatenate(
    [np.linspace(0.005, 0.1, 20, endpoint=False), np.linspace(0.1, 2.6, 251)]
)  # fm
BMAX_FM = 12.6 / FM

# ---------------------------------------------------------------- fitresults -> physical NP lambdas (no alphaS)
indata = inputdata.FitInputData(CARD_A)
WALL = rh.load_regularizer(
    "wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingWall",
    mh.load_mapping(
        "wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingMapping",
        indata,
        "margin=0",
    ),
    dtype=tf.float64,
)
SPECS = WALL.inputs["specs"]
ANCH = WALL.inputs["anchors"]
print(
    "[compute] wall forms:",
    WALL.inputs["np_model"],
    WALL.inputs["np_model_nu"],
    "ymax",
    WALL.inputs["ymax"],
)
print("[compute] specs:", SPECS)
print("[compute] anchors:", ANCH)


def phys_lin(name):
    kind, c = SPECS[name]
    if kind is None:
        return 0.0, 1.0
    assert kind == "quad" and c[2] == 0.0, (name, kind, c)
    return c[0], c[1]


def read_fit(path):
    fr = io_tools.get_fitresult(path, None, meta=False)
    h = fr["parms"].get()
    nm = [str(n) for n in h.axes[0]]
    x = np.asarray(h.values(), float)
    cov = np.asarray(fr["cov"].get().values(), float)
    WALL.set_expectations(tf.constant(x), None, parms=np.array(nm))
    phys_wall = {k: float(v) for k, v in WALL._physical(tf.constant(x)).items()}
    floating = [n for n in NP_LAMS if n in nm]
    idx = [nm.index(n) for n in floating]
    c0 = np.array([phys_lin(n)[0] for n in floating])
    c1 = np.array([phys_lin(n)[1] for n in floating])
    th = x[idx]
    mu = c0 + c1 * th
    C = cov[np.ix_(idx, idx)] * np.outer(c1, c1)
    for n, m in zip(floating, mu):
        assert abs(m - phys_wall[n]) < 1e-12, (n, m, phys_wall[n])
    held = {
        n: float(phys_wall.get(n, ANCH.get(n))) for n in NP_LAMS if n not in floating
    }
    faces = {
        c.label: float(c.value(phys_wall, lambda z: np.maximum(0.0, z) ** 2) - c.bound)
        for c in WALL._active
    }
    return dict(
        floating=floating,
        mu=mu,
        cov=C,
        held=held,
        phys=phys_wall,
        theta=dict(zip(floating, th)),
        faces=faces,
        edm=float(fr["edmval"]),
    )


FR = {k: read_fit(p) for k, p in FITS.items()}
for k, r in FR.items():
    s = np.sqrt(np.diag(r["cov"]))
    print(
        f"[compute] {k}: "
        + ", ".join(
            f"{n}={m:+.5f}+-{e:.5f}" for n, m, e in zip(r["floating"], r["mu"], s)
        )
        + f" | held {r['held']}"
    )
    print(
        f"           faces (value - bound): "
        + ", ".join(f"{a}: {b:+.3e}" for a, b in r["faces"].items())
    )


def cs_block(r):
    """(mu, cov) of (lambda2_nu, lambda4_nu); a held lambda4_nu gets zero variance."""
    mu = np.zeros(2)
    C = np.zeros((2, 2))
    for i, n in enumerate(("lambda2_nu", "lambda4_nu")):
        if n in r["floating"]:
            mu[i] = r["mu"][r["floating"].index(n)]
        else:
            mu[i] = r["held"][n]
    fl = [i for i, n in enumerate(("lambda2_nu", "lambda4_nu")) if n in r["floating"]]
    for i in fl:
        for j in fl:
            n_i, n_j = ("lambda2_nu", "lambda4_nu")[i], ("lambda2_nu", "lambda4_nu")[j]
            C[i, j] = r["cov"][r["floating"].index(n_i), r["floating"].index(n_j)]
    return mu, C


TUNES = {"lattice": (LAM_LAT, COV_LAT)}
for k in FR:
    TUNES[k] = cs_block(FR[k])
for k, (m, C) in TUNES.items():
    print(f"[compute] CS block {k}: mu={m}, sigma={np.sqrt(np.diag(C))}")

# ---------------------------------------------------------------- kernel curves and bands
out = dict(
    b_lat=B_LAT,
    b_full=B_FULL,
    bmax_fm=BMAX_FM,
    fm_to_gevinv=FM,
    k1hat=K1,
    data_b=CORE.b_fm,
    data_a=CORE.a_fm,
    data_y=CORE.y,
    data_cov=CORE.cov_stat,
    data_cov_final=CORE.cov,
    data_ens=np.load(CORE.data_path)["ens"],
    lam_lat=LAM_LAT,
    cov_lat=COV_LAT,
)
out["pert_lat"] = zeta(B_LAT * FM, 0.0, 0.0)
out["pert_full"] = zeta(B_FULL * FM, 0.0, 0.0)
out["pert_pts"] = zeta(CORE.bT, 0.0, 0.0)
summary = dict(
    lattice_only=dict(
        lam=LAM_LAT.tolist(),
        sigma=np.sqrt(np.diag(COV_LAT)).tolist(),
        rho=float(COV_LAT[0, 1] / np.sqrt(COV_LAT[0, 0] * COV_LAT[1, 1])),
        chi2_min=CORE.chi2_min,
        k1hat=K1,
        nf_shift=[float(CORE.nf_shift.min()), float(CORE.nf_shift.max())],
    ),
    frozen_reference={
        n: float(PFZ[NAMES.index(n)])
        for n in (
            "alphas",
            "tnp_gamma_nu",
            "tnp_gamma_cusp",
            "np_gnu_lambda_inf",
            "np_gnu_b0_bmax",
        )
    },
    fits={},
    bands={},
)
for k, (m, C) in TUNES.items():
    for tag, bgrid in (("lat", B_LAT), ("full", B_FULL)):
        v, J = zeta(bgrid * FM, m[0], m[1], order=1)
        out[f"{k}_{tag}_c"] = v
        out[f"{k}_{tag}_lin"] = np.sqrt(np.einsum("ni,ij,nj->n", J, C, J))
        if k == "XWSTIFF":
            continue
        # sampling: Gaussian in (lambda2_nu, lambda4_nu); a degenerate direction (held lambda4_nu) stays fixed
        L = (
            np.linalg.cholesky(C + 1e-300 * np.eye(2))
            if np.all(np.diag(C) > 0)
            else np.diag(np.sqrt(np.diag(C)))
        )
        draws = m[None, :] + rng.standard_normal((NTOY, 2)) @ L.T
        Z = np.array([zeta(bgrid * FM, d[0], d[1]) for d in draws])
        lo, md, hi = np.percentile(Z, [15.865, 50, 84.135], axis=0)
        out[f"{k}_{tag}_lo"], out[f"{k}_{tag}_md"], out[f"{k}_{tag}_hi"] = lo, md, hi
        dev = np.max(np.abs(0.5 * (hi - lo) - out[f"{k}_{tag}_lin"]))
        summary["bands"][f"{k}_{tag}"] = dict(
            max_abs_halfwidth_sampled_minus_linear=float(dev),
            max_halfwidth=float(np.max(0.5 * (hi - lo))),
        )
    out[f"{k}_pts"] = zeta(CORE.bT, m[0], m[1])
    chi2 = CORE.chi2_full(p_of(*m))
    summary["fits"][k] = dict(
        lam_cs=m.tolist(),
        sigma_cs=np.sqrt(np.diag(C)).tolist(),
        rho_cs=(
            float(C[0, 1] / np.sqrt(C[0, 0] * C[1, 1]))
            if np.all(np.diag(C) > 0)
            else None
        ),
        chi2_lat=chi2,
        dchi2_lat=chi2 - CORE.chi2_min,
        k1hat_own=CORE.k1hat(p_of(*m)),
    )
    # NP part from SCETlib itself (cross-check of the tanh_2 formula in stage 2)
    out[f"{k}_np_full"] = zeta(B_FULL * FM, m[0], m[1]) - out["pert_full"]
    print(
        f"[compute] {k}: chi2_lat = {chi2:.3f} (dchi2 {chi2 - CORE.chi2_min:.3f}), k1hat own = "
        f"{summary['fits'][k]['k1hat_own']:.4f}"
    )

for k, r in FR.items():
    summary["fits"][k].update(
        floating=r["floating"],
        mu=r["mu"].tolist(),
        sigma=np.sqrt(np.diag(r["cov"])).tolist(),
        held=r["held"],
        theta=r["theta"],
        faces=r["faces"],
        edm=r["edm"],
        path=FITS[k],
    )
    out[f"{k}_np_names"] = np.array(r["floating"])
    out[f"{k}_np_mu"] = r["mu"]
    out[f"{k}_np_cov"] = r["cov"]
    out[f"{k}_np_toys"] = rng.multivariate_normal(
        r["mu"], r["cov"], size=NTOY, method="eigh"
    )
    out[f"{k}_np_held_names"] = np.array(list(r["held"]))
    out[f"{k}_np_held_vals"] = np.array(list(r["held"].values()))

# ---------------------------------------------------------------- exact lattice Delta chi2 surface (figure 3)
l2g = np.linspace(-0.05, 0.36, 83)
l4g = np.linspace(-0.026, 0.056, 83)
S = np.array([[CORE.chi2_full(p_of(a, b)) for a in l2g] for b in l4g]) - CORE.chi2_min
out.update(l2g=l2g, l4g=l4g, dchi2_lat_grid=S)
print(f"[compute] grid min dchi2 {S.min():.4f}")

np.savez(os.path.join(TASK, "np_figs_data.npz"), **out)
json.dump(
    summary, open(os.path.join(TASK, "np_figs_data.json"), "w"), indent=1, default=float
)
print("[compute] wrote np_figs_data.npz / .json")
print(json.dumps(summary, indent=1, default=float))
