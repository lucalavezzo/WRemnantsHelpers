#!/usr/bin/env python3
"""Old (trust-krylov + NPDampingWall) vs new (cold trust-constr + NPDomainConstraints) minima, cache-free.

For every fit, at its stored x (BLINDED frame; alphaS only as differences, never an absolute value):
  NLL split    data_bb = nllvalreduced - wall - lattice - card constraints - model priors
               wall    = exp(2 tau) * NPDampingWall penalty, with the fit's OWN smoothing (relu2 for the pre-2026-10-08
                         fits, c2 delta=1e-3 for C2A); the hard-constraint fits have none
               lattice = frozen native LatticeCSTerm (LATFROZ_V3 options = today's defaults) 1/2 (chi2 - chi2_min);
                         NOMSTIFF/C2A/NOMTMDFREE: the old 1D Gaussian card term (card external_terms/lattice_cs)
               priors  = card constraints 1/2 sum cw theta^2 + the ParamModel Gaussian priors from meta param_priors
  physical NP lambdas (theta -> lambda through np_damping_wall's maps), every damping condition (margin 0) and
  which are active / violated.
Cross-objective values (data_bb is the same function of x in every fit: same card A data, same model; checked in
rabbit by the warm refits' start losses, LATatV3 / NOLATatXW):
  F_LAT(x)   = data_bb + card + LAT's 41 model priors + V3 lattice term       (+ hard constraints: report violation)
  F_NOLAT(x) = data_bb + card + LAT's 41 model priors
  F_old(x_new) = the old objective (its priors + its wall + its lattice) at the new minimum (reverse direction).
Newton (one step) from the old minimum to the new objective: remove the old NP priors (and the wall's relu^2 is kept
in the old Hessian, i.e. its active faces are held), dx = (H_old - P)^-1 * grad P; compared with x_new - x_old over all
3720 parameters.
Writes ../compare_minima.json and prints the tables.
"""
import json
import os

import h5py
import numpy as np
import tensorflow as tf

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
TAU = 8.0
LAMS = ["lambda2", "lambda4", "delta_lambda2", "lambda2_nu", "lambda4_nu"]
ACTIVE_TOL = 1e-6

# label: (fitresult with x, fitresult with cov or None, card, wall smoothing or None, lattice kind or None)
FITS = dict(
    LAT=(
        f"{A}/261015_ct18z_nominal_fits/fitresults_LAT.hdf5",
        f"{A}/261016_face_held_impacts/fitresults_LAT_facefix.hdf5",
        CARD_A,
        None,
        "V3",
    ),
    NOLAT=(
        f"{A}/261016_nolat_postfit/fitresults_NOLAT_PF.hdf5",
        f"{A}/261016_nolat_postfit/fitresults_NOLAT_PF.hdf5",
        CARD_A,
        None,
        None,
    ),
    LATFROZ_V3=(
        f"{A}/261008_latfroz_nf_variants/fitresults_LATFROZ_V3.hdf5",
        f"{A}/261008_latfroz_nf_variants/fitresults_LATFROZ_V3.hdf5",
        CARD_A,
        "relu2",
        "V3",
    ),
    V2=(
        f"{A}/261013_constraints_class_validation/fitresults_V2.hdf5",
        # HESSV2's cov is the plain (released) Hessian of a hard-constraint fit: no curvature holds the face, so a
        # Newton step off it walks through the face. V2 is V3's point (<= 3e-7 in lambda), so V3's walled cov is used.
        f"{A}/261008_latfroz_nf_variants/fitresults_LATFROZ_V3.hdf5",
        CARD_A,
        None,
        "V3",
    ),
    XWSTIFF=(
        f"{A}/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5",
        f"{A}/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5",
        CARD_A,
        "relu2",
        None,
    ),
    CMR1B=(  # the second, higher walled Z-only minimum (C seed; 261005-cold-min-restart)
        f"{A}/261005_cold_min_restart/fitresults_CMR1B.hdf5",
        f"{A}/261005_cold_min_restart/fitresults_CMR1B.hdf5",
        CARD_A,
        "relu2",
        None,
    ),
    NOMSTIFF=(
        f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5",
        f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5",
        CARD_1D,
        "relu2",
        "1d",
    ),
    NOMTMDFREE=(
        f"{A}/261005_tmd_priors_free/fitresults_NOMTMDFREE.hdf5",
        f"{A}/261005_tmd_priors_free/fitresults_NOMTMDFREE.hdf5",
        CARD_1D,
        "relu2",
        "1d",
    ),
    C2A=(
        f"{A}/261008_c2_wall_test/fitresults_C2A.hdf5",
        f"{A}/261008_c2_wall_test/fitresults_C2A.hdf5",
        CARD_1D,
        "c2",
        "1d",
    ),
)
PAIRS = [  # (new, old, objective of the new fit)
    ("LAT", "LATFROZ_V3", "LAT"),
    ("LAT", "V2", "LAT"),
    ("LAT", "NOMSTIFF", "LAT"),
    ("LAT", "C2A", "LAT"),
    ("LAT", "NOMTMDFREE", "LAT"),
    ("NOLAT", "XWSTIFF", "NOLAT"),
    ("NOLAT", "CMR1B", "NOLAT"),
]

INDATA = {c: inputdata.FitInputData(c) for c in (CARD_A, CARD_1D)}
SYSTS, CW = {}, {}
for c in (CARD_A, CARD_1D):
    with h5py.File(c, "r") as f:
        SYSTS[c] = [
            s.decode() if isinstance(s, bytes) else str(s) for s in f["hsysts"][...]
        ]
        CW[c] = np.asarray(f["hconstraintweights"][...], float)
with h5py.File(CARD_1D, "r") as f:
    t = f["external_terms/lattice_cs"]
    E_NM = [n.decode() if isinstance(n, bytes) else str(n) for n in t["params"][...]]
    E_G = t["grad_values"][...].reshape(t["grad_values"].attrs["original_shape"])
    E_H = t["hess_dense"][...].reshape(t["hess_dense"].attrs["original_shape"])
E_MU = -np.linalg.solve(E_H, E_G)
E_C0 = 0.5 * E_MU @ E_H @ E_MU


def make_wall(card, smooth):
    args = ["margin=0"]
    if smooth == "relu2":
        args.append("smooth=relu2")
    elif smooth == "c2":
        args += ["smooth=c2", "delta=1e-3"]
    else:  # only to read physical lambdas / conditions
        args.append("smooth=relu2")
    return rh.load_regularizer(
        "wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingWall",
        mh.load_mapping(
            "wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingMapping",
            INDATA[card],
            *args,
        ),
        dtype=tf.float64,
    )


WALLS = {}
_, _sig = XB.configure(
    f"{A}/scetlib_ad_caches/pdf62_y35_260921_y25/cache.conf", threads=4
)
SING = _sig.sub_pieces()[0]
SING.set_pdf_eig_params(29)
NAMES = list(SING.gradient_param_names())
PFZ = LT.frozen_reference(NAMES, np.array(SING.gradient_central(), float), 0.1168)
CORE_V3 = LT.LatticeCSNativeCore(
    SING, PFZ, syst="Jnf", require_rules=False, nf_match=4.18, nf_scheme="full"
)


def lat_v3(phys):
    p = CORE_V3.p_ref.copy()
    p[NAMES.index("np_gnu_lambda2")] = phys["lambda2_nu"]
    p[NAMES.index("np_gnu_lambda4")] = phys.get("lambda4_nu", 0.0)
    return 0.5 * (CORE_V3.chi2_full(p) - CORE_V3.chi2_min)


def lat_1d(xd):
    v = np.array([xd.get(n, 0.0) for n in E_NM])
    return float(E_G @ v + 0.5 * v @ E_H @ v + E_C0)


def priors_of(meta):
    pp = meta["param_priors"]
    pn = [n.decode() if isinstance(n, bytes) else str(n) for n in pp["params"]]
    msk, sg, mu = (
        np.asarray(pp["mask"]),
        np.asarray(pp["sigmas"], float),
        np.asarray(pp["means"], float),
    )
    return {n: (float(sg[i]), float(mu[i])) for i, n in enumerate(pn) if msk[i]}


def prior_val(pri, xd):
    return float(
        sum(0.5 * ((xd[n] - m) / s) ** 2 for n, (s, m) in pri.items() if n in xd)
    )


def card_val(card, xd):
    return 0.5 * sum(w * xd[sy] ** 2 for sy, w in zip(SYSTS[card], CW[card]) if w > 0)


def load(lab):
    path, covpath, card, smooth, latk = FITS[lab]
    fr, meta = io_tools.get_fitresult(path, None, meta=True)
    h = fr["parms"].get()
    nm = [str(n) for n in h.axes[0]]
    x = np.asarray(h.values(), float)
    xd = dict(zip(nm, x))
    cov = None
    if covpath:
        fc = io_tools.get_fitresult(covpath, None)
        if "cov" in fc:
            hc = fc["cov"].get()
            cov = np.asarray(hc.values(), float)
            nmc = [str(n) for n in fc["parms"].get().axes[0]]
            assert nmc == nm, f"{lab}: cov parameter list differs"
            # (V2 borrows V3's cov: cov_dx records how far the cov's own point is from x)
            xc = np.asarray(fc["parms"].get().values(), float)
            dxc = float(np.max(np.abs(xc - x)))
        else:
            dxc = None
    key = (card, smooth)
    if key not in WALLS:
        WALLS[key] = make_wall(card, smooth)
    W = WALLS[key]
    W.set_expectations(tf.constant(x), None, parms=np.array(nm))
    phys = {k: float(v) for k, v in W._physical(tf.constant(x)).items()}
    wall = (
        float(W.compute_nll_penalty(tf.constant(x), None)) * np.exp(2 * TAU)
        if smooth
        else 0.0
    )
    conds = {
        c.label: float(c.value(phys, WALLM.numpy_relu2) - c.bound) for c in W._active
    }
    if latk == "V3":
        lat = lat_v3(phys)
    elif latk == "1d":
        lat = lat_1d(xd)
    else:
        lat = 0.0
    pri = priors_of(meta)
    pm = prior_val(pri, xd)
    pm_np = prior_val({n: v for n, v in pri.items() if n in LAMS}, xd)
    cs = card_val(card, xd)
    nll = float(fr["nllvalreduced"])
    return dict(
        lab=lab,
        nm=nm,
        x=x,
        xd=xd,
        cov=cov,
        cov_dx=dxc if covpath else None,
        card=card,
        smooth=smooth,
        latk=latk,
        phys=phys,
        wall=wall,
        conds=conds,
        lat=lat,
        pri=pri,
        prior_model=pm,
        prior_np=pm_np,
        card_c=cs,
        nll=nll,
        data_bb=nll - wall - lat - pm - cs,
        W=W,
    )


def main():
    F = {k: load(k) for k in FITS}
    newpri = F["LAT"]["pri"]  # 41 non-NP model priors
    assert newpri == F["NOLAT"]["pri"]
    WA = WALLS[(CARD_A, None)]
    out = dict(fits={}, pairs={})
    print("\n=== per-fit NLL split and NP point (alphaS: never absolute) ===")
    for k, f in F.items():
        # new objectives at this point (map to card-A parameter list: a missing lambda4_nu = held at its anchor)
        xd = dict(f["xd"])
        if "lambda4_nu" not in xd:
            sp = WA.inputs["specs"]["lambda4_nu"]
            assert sp[0] == "quad" and sp[1][2] == 0.0
            xd["lambda4_nu"] = (0.0 - sp[1][0]) / sp[1][
                1
            ]  # physical 0 (NOMSTIFF/C2A/NOMTMDFREE hold it at 0)
        base = f["data_bb"] + card_val(CARD_A, xd) + prior_val(newpri, xd)
        physA = dict(f["phys"])
        physA.setdefault("lambda4_nu", 0.0)
        F_LAT = base + lat_v3(physA)
        F_NOLAT = base
        condsA = {}
        WA.set_expectations(
            tf.constant(F["LAT"]["x"]), None, parms=np.array(F["LAT"]["nm"])
        )
        for c in WA._active:
            condsA[c.label] = float(c.value(physA, WALLM.numpy_relu2) - c.bound)
        viol = {l: v for l, v in condsA.items() if v < 0}
        act = {l: v for l, v in condsA.items() if abs(v) < ACTIVE_TOL}
        r = dict(
            nll=f["nll"],
            data_bb=f["data_bb"],
            wall=f["wall"],
            lattice=f["lat"],
            card_constraints=f["card_c"],
            model_priors=f["prior_model"],
            np_priors=f["prior_np"],
            n_model_priors=len(f["pri"]),
            np_prior_sigmas={n: f["pri"][n][0] for n in LAMS if n in f["pri"]},
            lambdas={n: physA.get(n) for n in LAMS},
            conditions=condsA,
            active=act,
            violated=viol,
            F_LAT_at_point=F_LAT,
            F_NOLAT_at_point=F_NOLAT,
            cov_point_maxdx=f["cov_dx"],
        )
        out["fits"][k] = r
        print(
            f"-- {k}: NLL {f['nll']:.7f} = data+BB {f['data_bb']:.7f} + card {f['card_c']:.5f} + model priors "
            f"{f['prior_model']:.5f} (NP part {f['prior_np']:.5f}, {len(f['pri'])} priors) + lattice {f['lat']:.6f} "
            f"+ wall {f['wall']:.3e}"
        )
        print(
            "   lambdas: "
            + ", ".join(f"{n}={physA.get(n, float('nan')):+.6f}" for n in LAMS)
        )
        print(
            "   conditions (value - bound): "
            + "; ".join(f"{l.split(' (')[0]}: {v:+.3e}" for l, v in condsA.items())
        )
        print(
            f"   F_LAT(x) = {F_LAT:.7f}   F_NOLAT(x) = {F_NOLAT:.7f}   violated: {viol}"
        )

    print("\n=== pairs ===")
    for new, old, obj in PAIRS:
        fn, fo = F[new], F[old]
        common = [n for n in fn["nm"] if n in fo["xd"]]
        inew = [fn["nm"].index(n) for n in common]
        iold = [fo["nm"].index(n) for n in common]
        dx = fn["x"][inew] - fo["x"][iold]
        sn = np.sqrt(np.clip(np.diag(fn["cov"]), 0, None))[inew]
        so = np.sqrt(np.diag(fo["cov"]))[iold] if fo["cov"] is not None else None
        # a bound-held parameter has zero variance in the face-held cov (NOLAT's lambda2_nu): use the old sigma
        zero = sn < 1e-12
        if zero.any():
            print(
                f"   [{new} vs {old}] zero face-held sigma for {[common[i] for i in np.where(zero)[0]]}: old sigma used"
            )
            sn = np.where(zero, so if so is not None else np.inf, sn)
        ia = common.index("alphaS")
        pull = dx / sn
        order = np.argsort(-np.abs(pull))
        top = [(common[i], float(dx[i]), float(pull[i])) for i in order[:12]]
        topraw = [(common[i], float(dx[i])) for i in np.argsort(-np.abs(dx))[:8]]
        Fnew_at_old = out["fits"][old][f"F_{obj}_at_point"]
        # reverse: old objective at the new point = data_bb(new) + old card/priors/wall/lattice at new x
        xdn = dict(fn["xd"])
        Wo = fo["W"]
        xo_at_new = np.array([xdn.get(n, fo["xd"][n]) for n in fo["nm"]])
        if "lambda4_nu" not in fo["xd"]:
            xo_note = f"(new lambda4_nu = {fn['phys']['lambda4_nu']:.4g} dropped: old fit holds it at 0)"
        else:
            xo_note = ""
        xdo = dict(zip(fo["nm"], xo_at_new))
        Wo.set_expectations(tf.constant(xo_at_new), None, parms=np.array(fo["nm"]))
        physo = {k: float(v) for k, v in Wo._physical(tf.constant(xo_at_new)).items()}
        wall_o = (
            float(Wo.compute_nll_penalty(tf.constant(xo_at_new), None))
            * np.exp(2 * TAU)
            if fo["smooth"]
            else 0.0
        )
        lat_o = (
            lat_v3(physo)
            if fo["latk"] == "V3"
            else (lat_1d(xdo) if fo["latk"] == "1d" else 0.0)
        )
        Fold_at_new = (
            fn["data_bb"]
            + card_val(fo["card"], xdo)
            + prior_val(fo["pri"], xdo)
            + wall_o
            + lat_o
        )
        # Newton from old to new objective: remove old NP priors (sigma, mean) not in the new objective
        newton = None
        if fo["cov"] is not None and fo["card"] == fn["card"]:
            Ho = np.linalg.inv(fo["cov"])
            g = np.zeros(len(fo["nm"]))
            P = np.zeros_like(Ho)
            for n in LAMS:
                if n in fo["pri"] and n not in fn["pri"]:
                    j = fo["nm"].index(n)
                    s, m = fo["pri"][n]
                    g[j] = (fo["xd"][n] - m) / s**2  # gradient of the removed prior
                    P[j, j] = 1.0 / s**2
            Hn = Ho - P
            dxN = np.linalg.solve(Hn, g)  # new grad = -g ; dx = -Hn^-1 (-g)
            dF = -0.5 * g @ dxN
            Fpred = (fo["nll"] - fo["prior_np"] - fo["wall"]) + float(dF)
            if obj == "LAT" and fo["latk"] != "V3":
                Fpred = None
            dxN_c = dxN[iold]
            res = dx - dxN_c
            np.savez(
                os.path.join(TASK, f"newton_{new}_vs_{old}.npz"),
                names=np.array(common),
                dx=dx,
                dx_newton=dxN_c,
                sigma_new=sn,
                sigma_old=so,
            )
            newton = dict(
                F_pred=Fpred,
                dF=float(dF),
                dalphaS_pred_over_sig_new=float(dxN_c[ia] / sn[ia]),
                max_abs_residual_over_sig_new=float(np.max(np.abs(res / sn))),
                worst_residual=[
                    (common[i], float(dx[i] / sn[i]), float(dxN_c[i] / sn[i]))
                    for i in np.argsort(-np.abs(res / sn))[:6]
                ],
                lambdas_pred={
                    n: float(
                        WA.inputs["specs"][n][1][0]
                        + WA.inputs["specs"][n][1][1]
                        * (fo["xd"][n] + dxN[fo["nm"].index(n)])
                    )
                    for n in LAMS
                    if n in fo["xd"]
                },
                norm_dx_over_sig_new=float(np.linalg.norm(dx / sn)),
                norm_residual_over_sig_new=float(np.linalg.norm(res / sn)),
            )
        r = dict(
            objective=obj,
            NLL_new_min=fn["nll"],
            F_new_at_old_point=Fnew_at_old,
            dF_new_old_minus_new=Fnew_at_old - fn["nll"],
            F_old_at_new_point=Fold_at_new,
            F_old_min=fo["nll"],
            dF_old_new_minus_old=Fold_at_new - fo["nll"],
            reverse_note=xo_note,
            dalphaS_over_sig_new=float(pull[ia]),
            dalphaS_over_sig_old=float(dx[ia] / so[ia]) if so is not None else None,
            sigma_ratio_new_over_old=float(sn[ia] / so[ia]) if so is not None else None,
            max_abs_dtheta=float(np.max(np.abs(dx))),
            top_raw=topraw,
            max_abs_pull_new=float(np.max(np.abs(pull))),
            top_movers=top,
            n_params_over_0p01sig=int(np.sum(np.abs(pull) > 0.01)),
            n_params_over_0p1sig=int(np.sum(np.abs(pull) > 0.1)),
            norm_dx_over_sig_new=float(np.linalg.norm(pull)),
            dlambda={n: fn["phys"].get(n, 0.0) - fo["phys"].get(n, 0.0) for n in LAMS},
            newton=newton,
        )
        out["pairs"][f"{new}_vs_{old}"] = r
        print(f"-- {new} vs {old} (objective {obj})")
        for kk, vv in r.items():
            print(f"   {kk}: {vv}")
    json.dump(
        out,
        open(os.path.join(TASK, "compare_minima.json"), "w"),
        indent=1,
        default=float,
    )


if __name__ == "__main__":
    main()
