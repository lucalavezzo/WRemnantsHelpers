#!/usr/bin/env python3
"""Diagnosis 1: NPDampingWall condition scaling, from stored fitresults only (no cache load).

For every armed condition c(lambda) >= 0 (margin 0) of NPDampingWall, at each reference fit:
  * raw value c, its theta-gradient a = dc/dtheta, raw units;
  * equilibrium violation v = max(0, -c). At a converged walled minimum stationarity gives the
    data force along the condition g = 2 k v, k = exp(2 tau) = e^16 (relu^2 penalty k*relu(-c)^2);
  * sigma_c: the data-only (wall removed, "unsprung") 1-sigma of c, sqrt(a^T C_free a), where
    C_free = (C^-1 - 2k sum_active a a^T)^-1 removes the engaged spring from the stored covariance;
  * pull = g * sigma_c  (how many sigma_c past the face a linear data model would go if unwalled);
  * kappa_face = 2 k sigma_c^2  (wall curvature / data curvature along the face normal), so that
    v / sigma_c = pull / kappa_face;
  * the wall's eigenvalue in theta, 2 k |a|^2, against the data Hessian's spectrum;
  * physical size of v: Delta gamma_nu (CS) or Delta ln F^NP (TMD) on b in [0, b_max] when the
    violation is removed (lambda moved back onto the face).
Writes wall_scaling.json and prints a markdown table. Conditions follow
WRemnants/wremnants/postprocessing/scetlib_ad/np_damping_wall.py (tanh_2 / tanh_2, Y_max = 2.5); if
that module imports, its damping_conditions values are asserted equal to the ones here.

alphaS is never read.
"""
import json
import os

import numpy as np

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261006_constrained_fit_diagnosis"
TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAU = 8.0
K = np.exp(2 * TAU)  # penalty = K * relu(-c)^2
YMAX = 2.5
LINF, LINF_NU = 1.0, 2.0
BMAX = float(
    os.environ.get("BMAX", "12.6")
)  # GeV^-1, cache rule-site reach (see logbook)
# theta -> physical (from every fit log's [NPDampingWall] line)
MAP = {
    "lambda2": (0.4, 0.5),
    "lambda4": (0.4, 0.5),
    "delta_lambda2": (0.0, 0.5),
    "lambda2_nu": (0.15, 0.1),
    "lambda4_nu": (0.0, 0.5),
}


def phys(names, x):
    v = {"lambda_inf": LINF, "lambda_inf_nu": LINF_NU, "lambda4_nu": 0.0}
    for n, (c0, w) in MAP.items():
        idx = np.where(names == n)[0]
        if len(idx):
            v[n] = c0 + w * x[idx[0]]
    return v


def conditions(v):
    """(label, raw units, value) for each condition; same algebra as np_damping_wall.py."""
    out = [
        ("lambda4_nu >= 0 (CS large-b)", "GeV^4", v["lambda4_nu"]),
        ("lambda2_nu >= 0 (CS small-b)", "GeV^2", v["lambda2_nu"]),
    ]
    for y in (0.0, YMAX):
        L2 = v["lambda2"] + v["delta_lambda2"] * y * y
        out.append((f"L2(|Y|={y:g}) >= 0 (TMD small-b)", "GeV^2", L2))
        out.append(
            (
                f"3 linf^2 lambda4 + L2^3 >= 0 at |Y|={y:g} (TMD large-b)",
                "GeV^6",
                3 * LINF**2 * v["lambda4"] + L2**3,
            )
        )
    return out


def jac(names, x, fitted, eps=1e-7):
    """dc/dtheta for every condition (central differences on the linear/cubic map: exact to eps^2)."""
    base = [c for _, _, c in conditions(phys(names, x))]
    J = np.zeros((len(base), len(x)))
    for n in fitted:
        i = np.where(names == n)[0][0]
        xp, xm = x.copy(), x.copy()
        xp[i] += eps
        xm[i] -= eps
        cp = [c for _, _, c in conditions(phys(names, xp))]
        cm = [c for _, _, c in conditions(phys(names, xm))]
        J[:, i] = (np.array(cp) - np.array(cm)) / (2 * eps)
    return np.array(base), J


# ---- physics of a violation -------------------------------------------------
B = np.linspace(1e-4, BMAX, 4000)


def gamma_nu(v, b):
    P = v["lambda2_nu"] * b**2 + v["lambda4_nu"] * b**4
    return -LINF_NU * np.tanh(P / LINF_NU)


def lnF(v, b, y):
    L2 = v["lambda2"] + v["delta_lambda2"] * y * y
    Bc = v["lambda4"] + L2**3 / (3 * LINF**2)
    a = b * (L2 + Bc * b * b) / LINF
    return -2 * LINF * b * np.tanh(a)


def physical_effect(v, label, viol):
    """Effect of removing the violation `viol` (raw units) of condition `label`, on b in [0, BMAX]."""
    w = dict(v)
    if label.startswith("lambda4_nu"):
        w["lambda4_nu"] += viol
        d = gamma_nu(v, B) - gamma_nu(w, B)
        return dict(
            quantity="Delta gamma_nu",
            at_bmax=float(d[-1]),
            max_abs=float(np.max(np.abs(d))),
            gamma_nu_at_bmax=float(gamma_nu(v, B)[-1]),
            b_where_gamma_nu_positive=(
                float(B[np.argmax(gamma_nu(v, B) > 0)])
                if np.any(gamma_nu(v, B) > 0)
                else None
            ),
        )
    if label.startswith("lambda2_nu"):
        w["lambda2_nu"] += viol
        d = gamma_nu(v, B) - gamma_nu(w, B)
        return dict(
            quantity="Delta gamma_nu",
            at_bmax=float(d[-1]),
            max_abs=float(np.max(np.abs(d))),
        )
    y = 0.0 if "|Y|=0" in label else YMAX
    if label.startswith("L2"):
        # move lambda2 so L2(y) goes back to 0 (keeps delta_lambda2)
        w["lambda2"] += viol
    else:
        w["lambda4"] += viol / (3 * LINF**2)
    d = lnF(v, B, y) - lnF(w, B, y)
    return dict(
        quantity=f"Delta ln F^NP(|Y|={y:g})",
        at_bmax=float(d[-1]),
        max_abs=float(np.max(np.abs(d))),
        b_at_max=float(B[np.argmax(np.abs(d))]),
    )


def sherman_unspring(cov, a_rows, k2):
    """(C^-1 - k2 * sum a a^T)^-1 via Woodbury (k2 = 2K: relu^2 curvature)."""
    if len(a_rows) == 0:
        return cov
    Ca = cov @ a_rows.T
    M = a_rows @ Ca - np.eye(a_rows.shape[0]) / k2
    return cov - Ca @ np.linalg.solve(M, Ca.T)


def main():
    fits = ["NOMSTIFF", "XL4ZSTIFF", "XWSTIFF", "CMR1B", "CMR1A"]
    res = {}
    try:  # fidelity check against the wall module (container only)
        from wremnants.postprocessing.scetlib_ad import np_damping_wall as ndw

        mod_conds = ndw.damping_conditions("tanh_2", "tanh_2", YMAX, margin=0.0)
    except Exception as ex:  # noqa: BLE001
        print(f"[warn] wall module not importable ({ex}); skipping the cross-check")
        mod_conds = None
    for f in fits:
        d = np.load(f"{A}/{f}.npz")
        names, x, cov = d["names"].astype(str), d["x"], d["cov"]
        fitted = [n for n in MAP if n in set(names)]
        v = phys(names, x)
        conds = conditions(v)
        if mod_conds is not None:
            mv = {c.label: float(c.value(v, ndw.numpy_relu2)) for c in mod_conds}
            mine = [c for _, _, c in conds]
            theirs = [
                mv[k]
                for k in mv
                if not k.startswith("lambda_inf") and "saturation" not in k
            ]
            assert np.allclose(sorted(mine), sorted(theirs), rtol=0, atol=1e-14), (
                mine,
                theirs,
            )
        c, J = jac(names, x, fitted)
        armed = [i for i, (lab, _, _) in enumerate(conds) if np.any(J[i] != 0)]
        engaged = [i for i in armed if c[i] < 0]
        cov_free = sherman_unspring(cov, J[engaged], 2 * K)
        rows = []
        for i in armed:
            lab, unit, val = conds[i]
            a = J[i]
            sig_free = float(np.sqrt(a @ cov_free @ a))
            sig_wall = float(np.sqrt(a @ cov @ a))
            viol = max(0.0, -val)
            g = 2 * K * viol
            r = dict(
                label=lab,
                unit=unit,
                value=float(val),
                engaged=bool(val < 0),
                violation=viol,
                force_g=g,
                a_norm=float(np.linalg.norm(a)),
                wall_eig_theta=float(2 * K * a @ a),
                sigma_free=sig_free,
                sigma_walled=sig_wall,
                kappa_face=float(2 * K * sig_free**2),
                pull_sigma=float(g * sig_free),
                viol_over_sigma=float(viol / sig_free) if sig_free > 0 else None,
            )
            if viol > 0:
                r["physical"] = physical_effect(v, lab, viol)
            rows.append(r)
        # spectrum of the data Hessian (free) for scale
        ev = np.linalg.eigvalsh(np.linalg.inv(cov_free))
        res[f] = dict(
            lambdas={k: float(val) for k, val in v.items()},
            conditions=rows,
            hess_free_eig_min=float(ev[0]),
            hess_free_eig_max=float(ev[-1]),
            edmval=float(d["edmval"]),
        )
        print(
            f"\n## {f}  (EDM {float(d['edmval']):.1e}; free data Hessian eig in theta: "
            f"[{ev[0]:.2e}, {ev[-1]:.2e}], cond {ev[-1]/ev[0]:.1e})"
        )
        print(
            "| condition | units | value | engaged | v | g=2kv | sigma_free | kappa=2k sig^2 | pull [sig] | v/sig | 2k|a|^2 |"
        )
        print("|---|---|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            print(
                f"| {r['label']} | {r['unit']} | {r['value']:.3e} | {'yes' if r['engaged'] else ''} | "
                f"{r['violation']:.2e} | {r['force_g']:.3g} | {r['sigma_free']:.3e} | {r['kappa_face']:.2e} | "
                f"{r['pull_sigma']:.3g} | {(r['viol_over_sigma'] or 0):.2e} | {r['wall_eig_theta']:.2e} |"
            )
        for r in rows:
            if "physical" in r:
                print(f"   {r['label']}: {r['physical']}")
    json.dump(res, open(f"{TASK}/wall_scaling.json", "w"), indent=1)


if __name__ == "__main__":
    main()
