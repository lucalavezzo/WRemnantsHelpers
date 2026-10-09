#!/usr/bin/env python3
"""Newton slope d(alphaS)/dc at the active wall face c = L2(|Y|=2.5) = lambda2 + 6.25*delta_lambda2.

BLINDED: alphaS only as ratios to sigma_NOM (NOMSTIFF's sigma(alphaS)); no central alphaS value is printed.

theta -> physical (the wall's own print in LATB8.log): lambda2 = 0.4 + 0.5 th, delta_lambda2 = 0.5 th, so in theta
space c = 0.4 + 0.5 th_l2 + 3.125 th_dl2 and g = grad c is constant (c is linear) -> the wall's Hessian is EXACTLY
2 k g g^T (k = exp(2 tau) = e^16) while the face is active, and zero otherwise.

Two estimates of the slope S = Cov_f(alphaS, c) / Var_f(c), Cov_f = (Hessian of data + priors + lattice)^-1:
  (A) from the WALL-FREE Hessian pass YNOWALL8 (--noFit at LATB8's vector, the NPDampingWall -r dropped);
  (B) from LATB8's own (walled) covariance: with H = H_f + 2k g g^T, Cov g = Cov_f g / (1 + 2k V_f), so the RATIO
      Cov(alphaS, c)/Var(c) is identical to (A) for any k (Sherman-Morrison); only precision differs.
Multiplier: mu = d(rest)/dc at the constrained minimum. From the wall: mu = 2k * relu(-c*). From YNOWALL8: the edm
of the rest is 1/2 mu^2 V_f if the rest's gradient is mu*g (pure single-face stationarity) -> mu = sqrt(2 edm / V_f).
Also the full-release orientation number (LABELLED, unphysical point): Newton step that removes the face, i.e.
Delta theta = -Cov_f grad_rest = -mu * Cov_f g  ->  Delta alphaS = -mu Cov_f(alphaS, c), Delta c = -mu V_f.
"""
import json
import os
import sys

import numpy as np
from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
LATB8 = f"{A}/261007_lattice_term_native/fitresults_LATB8.hdf5"
NOMSTIFF = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
YNOWALL8 = f"{A}/261007_y_shape_first_look/fitresults_YNOWALL8.hdf5"
TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = np.exp(16.0)
YMAX2 = 2.5**2


def load(path):
    fr = io_tools.get_fitresult(path)
    parms = fr["parms"].get()
    names = [str(n) for n in parms.axes[0]]
    x = parms.values()
    cov = fr["cov"].get().values()
    out = dict(names=names, x=x, cov=cov)
    for k in ("edmval", "nllvalreduced"):
        if k in fr:
            v = fr[k]
            v = v.get() if hasattr(v, "get") else v
            out[k] = float(np.asarray(v.value if hasattr(v, "value") else v).ravel()[0])
    return out


def gvec(names):
    g = np.zeros(len(names))
    g[names.index("lambda2")] = 0.5
    g[names.index("delta_lambda2")] = 0.5 * YMAX2
    return g


def phys(r):
    n, x = r["names"], r["x"]
    l2 = 0.4 + 0.5 * x[n.index("lambda2")]
    dl2 = 0.5 * x[n.index("delta_lambda2")]
    l4 = 0.4 + 0.5 * x[n.index("lambda4")]
    return l2, dl2, l4


def slope(r, sig_nom, label):
    n, cov = r["names"], r["cov"]
    ia = n.index("alphaS")
    g = gvec(n)
    cg = cov @ g
    V = float(g @ cg)
    cac = float(cg[ia])
    S = cac / V  # theta_alphaS per unit c
    rho = cac / np.sqrt(V * cov[ia, ia])
    l2, dl2, l4 = phys(r)
    c = l2 + YMAX2 * dl2
    out = dict(
        label=label,
        V_c=V,
        sigma_c=np.sqrt(V),
        rho_alphaS_c=rho,
        slope_sigmaNOM_per_unit_c=S / sig_nom,
        slope_sigmaNOM_per_0p01GeV2=0.01 * S / sig_nom,
        sigma_alphaS_over_sigmaNOM=np.sqrt(cov[ia, ia]) / sig_nom,
        c_star=c,
        L2_0=l2,
        delta_lambda2=dl2,
        lambda4=l4,
    )
    return out, cg, V


def main():
    nom = load(NOMSTIFF)
    sig_nom = np.sqrt(
        nom["cov"][nom["names"].index("alphaS"), nom["names"].index("alphaS")]
    )
    res = {"sigma_NOM_theta": float(sig_nom)}
    lat = load(LATB8)
    rB, cgB, VB = slope(
        lat, sig_nom, "B: LATB8 walled covariance (Sherman-Morrison identity)"
    )
    cstar = rB["c_star"]
    mu_wall = 2 * K * max(0.0, -cstar)
    rB["mu_from_wall"] = mu_wall
    res["B"] = rB
    # NOMSTIFF for comparison (its own walled covariance, same identity)
    rN, _, _ = slope(nom, sig_nom, "NOMSTIFF walled covariance (identity)")
    rN["mu_from_wall"] = 2 * K * max(0.0, -rN["c_star"])
    res["NOMSTIFF"] = rN
    if os.path.exists(YNOWALL8):
        fr = load(YNOWALL8)
        assert fr["names"] == lat["names"], "parameter order differs"
        dx = np.max(np.abs(fr["x"] - lat["x"]))
        rA, cgA, VA = slope(
            fr, sig_nom, "A: YNOWALL8 wall-free Hessian at LATB8's vector"
        )
        rA["max_abs_dtheta_vs_LATB8"] = float(dx)
        edm = fr.get("edmval")
        rA["edm_rest"] = edm
        if edm is not None:
            rA["mu_from_edm"] = float(np.sqrt(2 * edm / VA))
        ia = fr["names"].index("alphaS")
        for mu_lab, mu in (("wall", mu_wall), ("edm", rA.get("mu_from_edm"))):
            if mu is None:
                continue
            rA[f"ORIENTATION_full_release_dalphaS_sigmaNOM_mu_{mu_lab}"] = float(
                -mu * cgA[ia] / sig_nom
            )
            rA[f"ORIENTATION_full_release_dc_mu_{mu_lab}"] = float(-mu * VA)
            rA[f"ORIENTATION_full_release_d2nll_mu_{mu_lab}"] = float(
                -(mu**2) * VA
            )  # Delta(2 NLL) = -mu^2 V
        # shape check of the identity: Cov_full g == Cov_f g / (1 + 2k V_f)
        pred = cgA / (1 + 2 * K * VA)
        sel = np.abs(pred) > 1e-12 * np.max(np.abs(pred))
        rA["identity_check_max_rel_dev_Covfull_g"] = float(
            np.max(np.abs(cgB[sel] - pred[sel]) / np.abs(pred[sel]))
        )
        res["A"] = rA
    with open(os.path.join(TASK, "slope.json"), "w") as f:
        json.dump(res, f, indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    sys.exit(main())
