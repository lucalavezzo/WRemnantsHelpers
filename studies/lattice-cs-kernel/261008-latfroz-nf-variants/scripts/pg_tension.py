#!/usr/bin/env python3
"""Parameter-goodness-of-fit (PG) tension between the Z data and the ASWZ lattice, from existing fits (no new fit).

  PG = 2 [ F_joint(joint min) - F_Z(Z-only min) ] ,  F_joint = F_Z + 1/2 (chi2_lat - chi2_lat,min)
     = Delta chi2_Z + Delta chi2_lat ,   dof = 2 (lambda2_nu, lambda4_nu: the parameters both constrain)
where F_Z = Poisson data + BB + card constraints + the 44 common model priors + the relu^2 wall (tau 8, margin 0). The
lattice-only chi2_min is already removed by the term's offset=min, so nothing else is subtracted.

Z-only reference: XWSTIFF (full |Y|<=3.5 cache, card A, wall margin 0 tau 8 relu^2, warm; the lower of the two walled
Z-only minima; CMR1B is the other). XWSTIFF ran with the DEFAULT priors, i.e. 46 = the joint fits' 44 + Gaussian
priors on theta(lambda2_nu) and theta(lambda4_nu) (sigma 1, mean 0). Those two are subtracted exactly from its vector
(F_Z(XW point) = nll - prior_nu). Because XW's point minimises F_Z + prior_nu rather than F_Z, F_Z(XW point) >= min F_Z;
the residual is estimated by one Newton step with XW's own covariance with the prior Hessian removed
(dF = -1/2 g^T C' g, g = prior gradient, C' = inv(inv(C_XW) - P)).
Wall terms re-evaluated with smooth=relu2 (all fits here ran with the pre-2026-10-08 relu^2 wall). BLINDED: only NLL
differences are printed (all NLLs involved are already published), no alpha_s. Writes ../pg_tension.json.
"""
import json
import os

import h5py
import numpy as np
import tensorflow as tf
from scipy.stats import chi2 as CHI2
from scipy.stats import norm

TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from rabbit import inputdata, io_tools  # noqa: E402
from rabbit.mappings import helpers as mh  # noqa: E402
from rabbit.regularization import helpers as rh  # noqa: E402

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
CARD_A = (
    f"{A}/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5"
)
TAU = 8.0
FITS = dict(
    XWSTIFF=f"{A}/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5",
    CMR1B=f"{A}/261005_cold_min_restart/fitresults_CMR1B.hdf5",
    LATFROZ_V1=f"{A}/261008_latfroz_nf_variants/fitresults_LATFROZ_V1.hdf5",
    LATFROZ_V2=f"{A}/261008_latfroz_nf_variants/fitresults_LATFROZ_V2.hdf5",
    LATFROZ_V3=f"{A}/261008_latfroz_nf_variants/fitresults_LATFROZ_V3.hdf5",
    LATB8=f"{A}/261007_lattice_term_native/fitresults_LATB8.hdf5",
)
NU = ("lambda2_nu", "lambda4_nu")
indata = inputdata.FitInputData(CARD_A)
with h5py.File(CARD_A, "r") as f:
    SYSTS = [s.decode() if isinstance(s, bytes) else str(s) for s in f["hsysts"][...]]
    CW = np.asarray(f["hconstraintweights"][...], float)
WALL = rh.load_regularizer(
    "wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingWall",
    mh.load_mapping(
        "wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingMapping",
        indata,
        "margin=0",
        "smooth=relu2",
    ),
    dtype=tf.float64,
)


def load(path):
    fr, meta = io_tools.get_fitresult(path, None, meta=True)
    h = fr["parms"].get()
    nm = [str(n) for n in h.axes[0]]
    x = np.asarray(h.values(), float)
    xd = dict(zip(nm, x))
    WALL.set_expectations(tf.constant(x), None, parms=np.array(nm))
    wall = float(WALL.compute_nll_penalty(tf.constant(x), None)) * np.exp(2 * TAU)
    pp = meta["param_priors"]
    pn = [n.decode() if isinstance(n, bytes) else str(n) for n in pp["params"]]
    msk, sg, mu = (
        np.asarray(pp["mask"]),
        np.asarray(pp["sigmas"], float),
        np.asarray(pp["means"], float),
    )
    pri = {n: (float(sg[i]), float(mu[i])) for i, n in enumerate(pn) if msk[i]}
    lc_pm = {n: 0.5 * ((xd[n] - m) / s) ** 2 for n, (s, m) in pri.items()}
    lc_syst = 0.5 * sum(w * xd[sy] ** 2 for sy, w in zip(SYSTS, CW) if w > 0)
    cmd = meta.get("meta_info", {}).get("command", "")
    return dict(
        fr=fr,
        nm=nm,
        x=x,
        xd=xd,
        wall=wall,
        pri=pri,
        lc_pm=lc_pm,
        lc_syst=lc_syst,
        cmd=cmd,
        nll=float(fr["nllvalreduced"]),
        edm=float(fr["edmval"]),
    )


def main():
    F = {k: load(p) for k, p in FITS.items()}
    out = dict(checks={}, fits={})
    ref = F["LATFROZ_V3"]
    for k, f in F.items():
        out["checks"][k] = dict(
            same_parameter_list_as_V3=f["nm"] == ref["nm"],
            card=CARD_A in f["cmd"],
            wall_args="'margin=0'" in f["cmd"]
            and "smooth=" not in f["cmd"]
            and "--regularizationStrength 8" in f["cmd"],
            priors_equal_V3_except_nu=(
                {n: v for n, v in f["pri"].items() if n not in NU} == ref["pri"]
            ),
            nu_priors={n: f["pri"][n] for n in NU if n in f["pri"]},
            cache=[t for t in f["cmd"].split() if "cache=" in t],
            nll=f["nll"],
            edm=f["edm"],
            wall=f["wall"],
            lambda2_nu_theta=float(f["xd"]["lambda2_nu"]),
            lambda4_nu_theta=float(f["xd"]["lambda4_nu"]),
        )
    # Z-only objective at the Z-only minima: subtract their lambda_nu priors exactly
    for k in ("XWSTIFF", "CMR1B"):
        f = F[k]
        pnu = sum(f["lc_pm"].get(n, 0.0) for n in NU)
        fz = f["nll"] - pnu
        # Newton estimate of how much lower min F_Z is than F_Z(this point) once the nu priors are removed
        C = np.asarray(f["fr"]["cov"].get().values(), float)
        H = np.linalg.inv(C)
        g = np.zeros(len(f["nm"]))
        P = np.zeros_like(H)
        for n in NU:
            if n in f["pri"]:
                j = f["nm"].index(n)
                s, m = f["pri"][n]
                g[j] = (
                    -(f["xd"][n] - m) / s**2
                )  # gradient of F_Z = (gradient of F_Z+prior = 0) - prior gradient
                P[j, j] = 1.0 / s**2
        Cz = np.linalg.inv(H - P)
        dF = -0.5 * g @ Cz @ g
        dx = -Cz @ g
        out["fits"][k] = dict(
            nll=f["nll"],
            prior_nu=pnu,
            FZ_at_point=fz,
            newton_dFZ=float(dF),
            FZ_min_est=fz + float(dF),
            newton_dtheta={n: float(dx[f["nm"].index(n)]) for n in NU},
            sigma_theta={
                n: float(np.sqrt(C[f["nm"].index(n), f["nm"].index(n)])) for n in NU
            },
        )
    zref = out["fits"]["XWSTIFF"]
    for k in ("LATFROZ_V1", "LATFROZ_V2", "LATFROZ_V3", "LATB8"):
        f = F[k]
        row = dict(nll=f["nll"])
        for lab, fz in (
            ("FZ_at_XW_point", zref["FZ_at_point"]),
            ("FZ_min_est", zref["FZ_min_est"]),
            ("XW_nll_with_its_nu_priors", zref["nll"]),
        ):
            pg = 2.0 * (f["nll"] - fz)
            p = float(CHI2.sf(pg, 2))
            row[lab] = dict(PG=pg, dof=2, p=p, z_two_sided=float(norm.isf(p / 2)))
        out["fits"][k] = row
    cm = out["fits"]["CMR1B"]
    out["CMR1B_minus_XWSTIFF_FZ"] = cm["FZ_at_point"] - zref["FZ_at_point"]
    json.dump(
        out, open(os.path.join(TASK, "pg_tension.json"), "w"), indent=1, default=float
    )
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
