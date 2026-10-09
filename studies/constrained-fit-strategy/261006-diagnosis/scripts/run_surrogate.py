#!/usr/bin/env python3
"""Minimiser experiments on the quadratic surrogate of the nominal walled fit (scripts/surrogate.py).

No cache load. Each experiment records loss+grad evaluations (n_f) and HVPs (n_hvp), so it can be
costed in real-fit units, and the instrumented trust-region loop below logs what rabbit's logs cannot
(trust radius, rho, hits_boundary, face value per iteration).

The trust-region loop is a line-for-line copy of scipy 1.18 optimize/_trustregion.py
(_minimize_trust_region) with the same trlib subproblem that method='trust-krylov' uses
(tol_rel_i=-2, tol_rel_b=-3, initial radius 1, max radius 1000, eta 0.15), plus logging.

usage: run_surrogate.py <experiment> [...]   (see EXPERIMENTS at the bottom)
"""
import json
import os
import sys
import time

import h5py
import numpy as np
import scipy.optimize as so
import scipy.sparse.linalg as sla
from scipy.optimize._trlib import get_trlib_quadratic_subproblem

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from surrogate import Surrogate  # noqa: E402

TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = f"{TASK}/surrogate"
C = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
STARTS = {
    "CENS03R": f"{C}/261001_census_nominal/snapshot_fitresults_CENS03R.hdf5",
    "C1A": f"{C}/261005_cold_min_restart/seeds/seed_1a_C_in_NOMSTIFF.hdf5",
    "pert000": f"{C}/261001_census_nominal/seeds/pert_000.hdf5",
    "cold000": f"{C}/261001_census_nominal/seeds/cold_000.hdf5",
    "pert002": f"{C}/261001_census_nominal/seeds/pert_002.hdf5",
}


def load_start(key, names):
    with h5py.File(STARTS[key], "r") as f:
        x = np.asarray(f["x"][()], float)
        pn = np.asarray(f["parms"][()]).astype(str)
    if len(pn) == len(names) and (pn == names).all():
        return x
    m = {n: v for n, v in zip(pn, x)}
    return np.array([m[n] for n in names])


# ------------------------------------------------------------------ trust-krylov (instrumented scipy copy)
def trust_krylov(S, x0, maxiter=4000, ftarget=None, T=None, log_every=0, max_nf=None):
    """scipy trust-krylov; optional linear change of variables x = x0 + T y (preconditioning)."""
    n = len(x0)
    if T is None:
        to_x = lambda y: x0 + y  # noqa: E731
        fun = lambda y: S.fun(to_x(y))  # noqa: E731
        hessp = lambda y, p: S.hessp(to_x(y), p)  # noqa: E731
    else:
        to_x = lambda y: x0 + T @ y  # noqa: E731

        def fun(y):
            f, g = S.fun(to_x(y))
            return f, T.T @ g

        hessp = lambda y, p: T.T @ S.hessp(to_x(y), T @ p)  # noqa: E731
    cache = {}

    def f_only(y):
        k = y.tobytes()
        if k not in cache:
            cache.clear()
            cache[k] = fun(y)
        return cache[k][0]

    def g_only(y):
        f_only(y)
        return cache[y.tobytes()][1]

    sub = get_trlib_quadratic_subproblem(tol_rel_i=-2.0, tol_rel_b=-3.0)
    y = np.zeros(n)
    r = 1.0
    m = sub(y, f_only, g_only, None, hessp)
    hist = []
    t0 = time.time()
    f0 = m.fun
    for k in range(maxiter):
        h0 = S.n_hvp
        p, hb = m.solve(r)
        pred_val = m(p)
        yp = y + p
        mp = sub(yp, f_only, g_only, None, hessp)
        ared = m.fun - mp.fun
        pred = m.fun - pred_val
        if pred <= 0:
            hist.append(dict(k=k, stop="pred<=0"))
            break
        rho = ared / pred
        r_used = r
        if rho < 0.25:
            r *= 0.25
        elif rho > 0.75 and hb:
            r = min(2 * r, 1000.0)
        acc = rho > 0.15
        if acc:
            y, m = yp, mp
        x = to_x(y)
        cface = S.conds(x)[0]
        hist.append(
            dict(
                k=k,
                f=float(m.fun),
                acc=bool(acc),
                rho=float(rho),
                r=float(r_used),
                hb=bool(hb),
                step=float(np.linalg.norm(p)),
                dhvp=S.n_hvp - h0,
                nf=S.n_f,
                nhvp=S.n_hvp,
                face=float(cface[S.iface]),
                cmin=float(cface.min()),
            )
        )
        if log_every and k % log_every == 0:
            print(
                f"  it {k:5d} f {m.fun:.10f} acc {int(acc)} rho {rho:.3g} r {r_used:.3g} hb {int(hb)} "
                f"face {cface[S.iface]:.3e} nhvp {S.n_hvp}",
                flush=True,
            )
        if ftarget is not None and m.fun <= ftarget:
            break
        if max_nf and S.n_f > max_nf:
            break
    return to_x(y), hist, time.time() - t0, f0


# ------------------------------------------------------------------ trust-constr (scipy) with hard constraints
def trust_constr(S, x0, mu0=0.1, maxiter=2000, T=None, ftarget=None):
    n = len(x0)
    wall_was = S.wall
    S.wall = False  # hard constraints: penalty OFF
    if T is None:
        T = np.eye(n)
        ident = True
    else:
        ident = False
    to_x = (lambda y: x0 + y) if ident else (lambda y: x0 + T @ y)

    def fun(y):
        f, g = S.fun(to_x(y))
        return f, (g if ident else T.T @ g)

    def hessp(y, p):
        return S.hessp(to_x(y), p) if ident else T.T @ S.hessp(to_x(y), T @ p)

    def cfun(y):
        return S.conds(to_x(y))[0]

    def cjac(y):
        J = S.conds(to_x(y))[1]
        return J if ident else J @ T

    def chess(y, v):
        _, _, Hs = S.conds(to_x(y))
        vecs, ws = [], []
        for i, h in enumerate(Hs):
            if h is not None and v[i] != 0:
                s, jL = h
                vecs.append(jL if ident else T.T @ jL)
                ws.append(v[i] * s)
        V = np.array(vecs) if vecs else np.zeros((0, n))
        w = np.array(ws)
        return sla.LinearOperator(
            (n, n),
            matvec=lambda p: V.T @ (w * (V @ np.ravel(p))) if len(w) else np.zeros(n),
            dtype=float,
        )

    con = so.NonlinearConstraint(
        cfun, 0.0, np.inf, jac=cjac, hess=chess, keep_feasible=False
    )
    hist = []
    t0 = time.time()

    def cb(intermediate_result):
        res = intermediate_result
        hist.append(
            dict(
                k=int(res.nit),
                f=float(res.fun),
                opt=float(res.optimality),
                cv=float(res.constr_violation),
                mu=float(res.barrier_parameter),
                tr=float(res.tr_radius),
                cg=int(res.cg_niter),
                cgstop=int(res.cg_stop_cond),
                nf=S.n_f,
                nhvp=S.n_hvp,
                face=float(S.conds(to_x(res.x))[0][S.iface]),
            )
        )
        if ftarget is not None and res.fun <= ftarget and res.constr_violation < 1e-9:
            raise StopIteration

    res = so.minimize(
        fun,
        np.zeros(n),
        jac=True,
        hessp=hessp,
        method="trust-constr",
        constraints=[con],
        callback=cb,
        options=dict(
            maxiter=maxiter,
            gtol=1e-8,
            xtol=1e-10,
            barrier_tol=1e-9,
            initial_barrier_parameter=mu0,
            initial_barrier_tolerance=mu0,
        ),
    )
    S.wall = wall_was
    return to_x(res.x), hist, time.time() - t0, res


# ------------------------------------------------------------------ active set on the linear face (exact)
def face_reduced(S, x0, iface):
    """Eliminate the LINEAR face c_iface = 0 (null-space of its gradient), returns (x0_on_face, Z basis map)."""
    _, J, Hs = S.conds(x0)
    assert Hs[iface] is None, "face must be linear in theta"
    a = J[iface]
    c0 = S.conds(x0)[0][iface]
    x_on = x0 - c0 * a / (a @ a)
    # T = I - a a^T/|a|^2 restricted: use a projector as the change of variables (rank n-1, y in R^n)
    P = np.eye(len(x0)) - np.outer(a, a) / (a @ a)
    return x_on, P


def summarise(hist, S, x, fstar, f0, wall_s):
    acc = [h for h in hist if h.get("acc")]
    out = dict(
        iters=len(hist),
        accepted=len(acc),
        n_f=S.n_f,
        n_hvp=S.n_hvp,
        seconds=wall_s,
        f_end_minus_fstar=float(S.fun(x)[0] - fstar),
        f0_minus_fstar=float(f0 - fstar),
        face_end=float(S.conds(x)[0][S.iface]),
        cmin_end=float(S.conds(x)[0].min()),
        dist_to_ref=float(np.linalg.norm(x - S.x_ref)),
    )
    for thr in (1e-1, 1e-3, 1e-6, 1e-9):
        it = next((h for h in hist if "f" in h and h["f"] - fstar <= thr), None)
        out[f"to_{thr:g}"] = (
            None if it is None else dict(k=it["k"], nf=it["nf"], nhvp=it["nhvp"])
        )
    return out


def fstar_walled(S):
    """Walled-surrogate minimum value: on the face direction the minimiser sits at v = mu/(2K|a|^2_eff).

    Computed numerically by an exact solve: Newton on the active face with the spring engaged, which is
    a pure quadratic (L2(2.5) is linear in theta): (H + 2K a a^T) d = -g + 2K * 0 ...  -> d.
    """
    a = S.conds(S.x_ref)[1][S.iface]
    Hw = S.H + 2 * S.K * np.outer(a, a)
    # minimise g.d + 1/2 d H d + K (a.d)^2  (face value at ref is ~0; engaged side a.d < 0)
    d = -np.linalg.solve(Hw, S.g)
    x = S.x_ref + d
    f = S.fun(x)[0]
    S.n_f -= 1
    return f, x


def run(exp, start, **kw):
    S = Surrogate(tau=kw.get("tau", 8.0))
    x0 = load_start(start, S.names)
    fstar, xstar = fstar_walled(S) if S.wall else (0.0, S.x_ref)
    f_hard = (
        0.0  # constrained minimum of the surrogate is theta_ref, f = 0 by construction
    )
    res = dict(
        exp=exp,
        start=start,
        tau=S.tau,
        fstar_walled=fstar,
        start_face=float(S.conds(x0)[0][S.iface]),
        start_cmin=float(S.conds(x0)[0].min()),
        start_f=float(S.fun(x0)[0]),
    )
    S.n_f = 0
    S.n_hvp = 0
    if exp == "tk":  # trust-krylov + relu^2 wall
        x, hist, sec, f0 = trust_krylov(
            S,
            x0,
            maxiter=kw.get("maxiter", 4000),
            ftarget=fstar + 1e-10,
            log_every=kw.get("log_every", 0),
        )
        res.update(summarise(hist, S, x, fstar, f0, sec))
    elif (
        exp == "tk_pc"
    ):  # whitened by the data Hessian at the start (wall NOT in the reference: start feasible)
        L = np.linalg.cholesky(S.H)
        T = np.linalg.inv(L).T  # x = x0 + L^-T y  => T^T H T = I
        x, hist, sec, f0 = trust_krylov(
            S, x0, maxiter=kw.get("maxiter", 4000), ftarget=fstar + 1e-10, T=T
        )
        res.update(summarise(hist, S, x, fstar, f0, sec))
    elif (
        exp == "tk_face"
    ):  # active set: the known face eliminated exactly, wall kept on the other 4 (slack)
        xon, P = face_reduced(S, x0, S.iface)
        res["start_f_on_face"] = float(S.fun(xon)[0])
        S.n_f = 0
        S.n_hvp = 0
        x, hist, sec, f0 = trust_krylov(
            S, xon, maxiter=kw.get("maxiter", 4000), ftarget=f_hard + 1e-10, T=P
        )
        res.update(summarise(hist, S, x, f_hard, f0, sec))
    elif exp == "tc":  # trust-constr, hard constraints
        x, hist, sec, r = trust_constr(
            S, x0, mu0=kw.get("mu0", 0.1), maxiter=kw.get("maxiter", 2000)
        )
        S.wall = False
        res.update(summarise(hist, S, x, f_hard, hist[0]["f"] if hist else np.nan, sec))
        res.update(
            status=int(r.status),
            message=str(r.message),
            cg_total=int(r.cg_niter),
            opt_end=float(r.optimality),
            mu_end=float(r.barrier_parameter),
        )
    elif exp == "tc_pc":
        L = np.linalg.cholesky(S.H)
        T = np.linalg.inv(L).T
        x, hist, sec, r = trust_constr(
            S, x0, mu0=kw.get("mu0", 0.1), maxiter=kw.get("maxiter", 2000), T=T
        )
        S.wall = False
        res.update(summarise(hist, S, x, f_hard, hist[0]["f"] if hist else np.nan, sec))
        res.update(
            status=int(r.status),
            message=str(r.message),
            cg_total=int(r.cg_niter),
            opt_end=float(r.optimality),
            mu_end=float(r.barrier_parameter),
        )
    else:
        raise SystemExit(f"unknown experiment {exp}")
    os.makedirs(OUT, exist_ok=True)
    tag = f"{exp}_{start}_tau{kw.get('tau', 8.0):g}" + (
        f"_mu{kw['mu0']:g}" if "mu0" in kw else ""
    )
    json.dump(dict(summary=res, hist=hist), open(f"{OUT}/{tag}.json", "w"))
    print(tag, json.dumps({k: v for k, v in res.items()}, default=str), flush=True)
    return res


if __name__ == "__main__":
    exp, start = sys.argv[1], sys.argv[2]
    kw = {}
    for a in sys.argv[3:]:
        k, v = a.split("=")
        kw[k] = float(v) if k in ("tau", "mu0") else int(v)
    run(exp, start, **kw)
