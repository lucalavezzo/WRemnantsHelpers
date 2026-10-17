#!/usr/bin/env python3
"""Toy: why does scipy trust-constr walk away from a warm start at its own minimum?

Ill-conditioned objective (kappa ~ 1e7, mildly nonlinear), 8 inequality rows
(linear + nonlinear), several active at the constrained minimum. Solve cold,
then restart from the minimum (and from nearby points) under variants that
separate the three suspects:

  mu0     initial_barrier_parameter (scipy default 0.1) + initial_barrier_tolerance
  slack   scipy's s0 = max(1.5*(c-lb), 1) vs a consistent s0 = max(c-lb, floor)
  keep    rabbit's keep_feasible rule (strictly feasible rows held feasible,
          rows on their bound not) vs no row held feasible (any infeasible start)
  tr0     initial_tr_radius

Run inside the WRemnants container (scipy 1.18):
  python toy_warmstart.py [--json out.json]
"""

import argparse
import contextlib
import json

import numpy as np
import scipy
from scipy.optimize import NonlinearConstraint, minimize
from scipy.optimize._trustregion_constr import tr_interior_point as _tip
from scipy.sparse.linalg import LinearOperator

# ---------------------------------------------------------------- the problem


def make_problem(seed=3, n=40, kappa=1e3):
    rng = np.random.default_rng(seed)
    eig = np.logspace(0, np.log10(kappa), n) / np.sqrt(kappa)  # 3e-4 .. 3e3
    Q, _ = np.linalg.qr(rng.normal(size=(n, n)))
    H = (Q * eig) @ Q.T
    Hinv = (Q / eig) @ Q.T
    # unconstrained optimum ~ 2 sigma away from 0 along every eigendirection
    a = Q @ (2.0 * rng.normal(size=n) / np.sqrt(eig))
    eps_nl = 0.02  # mild quartic-ish nonlinearity: sum logcosh(x/sigma_scale)
    scale = 1.0 / np.sqrt(np.diag(Hinv))  # ~ 1/sigma_i per coordinate

    def f(x):
        d = x - a
        u = x * scale
        return 0.5 * d @ H @ d + eps_nl * np.sum(np.logaddexp(u, -u) - np.log(2))

    def g(x):
        u = x * scale
        return H @ (x - a) + eps_nl * scale * np.tanh(u)

    def hp(x, p):
        u = x * scale
        return H @ p + eps_nl * scale**2 * (1 - np.tanh(u) ** 2) * p

    # constraint rows c_i(x) >= lb_i. Directions picked so that a VIOLATES the
    # "active" ones; 0 is strictly feasible for all (cold start).
    sig = lambda w: np.sqrt(w @ Hinv @ w)  # noqa: E731

    rows = []
    # 4 linear rows: 3 meant active, 1 inactive close (1 sigma from the
    # unconstrained optimum)
    for k, kind in enumerate(["act", "act", "act", "close"]):
        w = rng.normal(size=n)
        w /= np.linalg.norm(w)
        if w @ a > 0:
            w = -w
        gap = -(w @ a)  # c(0) - c(a) > 0
        if kind == "act":
            lb = (w @ a) + 0.5 * gap  # a violates by gap/2
        else:
            lb = (w @ a) - 1.0 * sig(w)
            lb = min(lb, -0.5 * gap)  # keep 0 feasible
        rows.append(("lin", w, lb))
    # nonlinear 1: exp(u.x / s_u) >= lb, active
    u = rng.normal(size=n)
    u /= np.linalg.norm(u)
    if u @ a > 0:
        u = -u
    su = sig(u)
    rows.append(("exp", (u, su), np.exp(0.5 * (u @ a) / su)))
    # nonlinear 2: cubic t^3 + t >= lb with t = v.x / s_v, active
    v = rng.normal(size=n)
    v /= np.linalg.norm(v)
    if v @ a > 0:
        v = -v
    sv = sig(v)
    t_a = (v @ a) / sv
    rows.append(("cub", (v, sv), (0.5 * t_a) ** 3 + 0.5 * t_a))
    # nonlinear 3: ball on a 3-dim projection, -(|P x|^2) >= -r^2, inactive close
    P = rng.normal(size=(3, n))
    P /= np.linalg.norm(P, axis=1, keepdims=True)
    sP = np.array([sig(p) for p in P])
    r2 = 1.2 * np.sum(((P @ a) / sP) ** 2)
    rows.append(("ball", (P, sP), -r2))
    # linear far-away row
    w = rng.normal(size=n)
    w /= np.linalg.norm(w)
    rows.append(("lin", w, (w @ a) - 50.0 * sig(w) - abs(w @ a)))

    lb = np.array([r[2] for r in rows])

    def cval(x):
        out = []
        for kind, p, _ in rows:
            if kind == "lin":
                out.append(p @ x)
            elif kind == "exp":
                uu, s = p
                out.append(np.exp((uu @ x) / s))
            elif kind == "cub":
                vv, s = p
                t = (vv @ x) / s
                out.append(t**3 + t)
            elif kind == "ball":
                PP, s = p
                out.append(-np.sum(((PP @ x) / s) ** 2))
        return np.array(out)

    def cjac(x):
        J = []
        for kind, p, _ in rows:
            if kind == "lin":
                J.append(p)
            elif kind == "exp":
                uu, s = p
                J.append(np.exp((uu @ x) / s) * uu / s)
            elif kind == "cub":
                vv, s = p
                t = (vv @ x) / s
                J.append((3 * t**2 + 1) * vv / s)
            elif kind == "ball":
                PP, s = p
                J.append(-2 * ((PP @ x) / s**2) @ PP)
        return np.array(J)

    def chess(x, lam):
        Hc = np.zeros((n, n))
        for li, (kind, p, _) in zip(lam, rows):
            if kind == "exp":
                uu, s = p
                Hc += li * np.exp((uu @ x) / s) * np.outer(uu, uu) / s**2
            elif kind == "cub":
                vv, s = p
                t = (vv @ x) / s
                Hc += li * 6 * t * np.outer(vv, vv) / s**2
            elif kind == "ball":
                PP, s = p
                Hc += li * (-2) * (PP.T / s**2) @ PP
        return Hc

    labels = ["lin0", "lin1", "lin2", "lin3_close", "exp", "cubic", "ball", "lin_far"]
    return dict(
        n=n,
        f=f,
        g=g,
        hp=hp,
        cval=cval,
        cjac=cjac,
        chess=chess,
        lb=lb,
        H=H,
        a=a,
        labels=labels,
    )


# --------------------------------------------- the consistent-slack hook


@contextlib.contextmanager
def consistent_slack(floor):
    """Patch scipy so tr_interior_point starts each slack at max(c - lb, floor).

    scipy computes s0 = max(1.5*(c-lb), 1) and hands the SAME array to
    BarrierSubproblem.__init__ and then to z = hstack((x0, s0)); overwriting it
    in place in __init__ therefore sets the slack the iteration starts from.
    """
    orig = _tip.BarrierSubproblem

    class _Warm(orig):
        def __init__(self, x0, s0, *args):
            constr_ineq0 = args[15]  # (fun..., constr_ineq0 is the 18th arg)
            s0[:] = np.maximum(
                -np.asarray(constr_ineq0), floor
            )  # floor: scalar or per row
            super().__init__(x0, s0, *args)

    _tip.BarrierSubproblem = _Warm
    try:
        yield
    finally:
        _tip.BarrierSubproblem = orig


# ---------------------------------------------------------------- the solver


def solve(
    prob,
    x0,
    mu0=None,
    tol0=None,
    tr0=None,
    keep="rabbit",
    slack="scipy",
    slack_floor=None,
    gtol=1e-10,
    xtol=1e-12,
    barrier_tol=1e-10,
    maxiter=3000,
):
    f, g, hp = prob["f"], prob["g"], prob["hp"]
    lb = prob["lb"]
    c0 = prob["cval"](x0)
    atol = 64 * np.finfo(float).eps * np.maximum(1.0, np.abs(lb))
    if keep == "rabbit":
        if np.any(lb - c0 > atol):
            kf = np.zeros(len(lb), bool)
        else:
            kf = ~(np.abs(c0 - lb) <= atol)
    elif keep == "none":
        kf = np.zeros(len(lb), bool)
    elif keep == "near":
        # warm-start rule: rows within 1e-3 of their bound are NOT held feasible
        kf = (c0 - lb) > 1e-3 * np.maximum(1.0, np.abs(lb))
    else:
        kf = np.ones(len(lb), bool)

    con = NonlinearConstraint(
        prob["cval"],
        lb,
        np.inf,
        jac=prob["cjac"],
        hess=lambda x, v: prob["chess"](x, v),
        keep_feasible=kf,
    )
    hist = []

    def cb(intermediate_result):
        state = intermediate_result
        hist.append(
            dict(
                nit=state.nit,
                fun=float(state.fun),
                mu=float(state.barrier_parameter),
                tr=float(state.tr_radius),
                opt=float(state.optimality),
                viol=float(state.constr_violation),
            )
        )
        return False

    opts = dict(gtol=gtol, xtol=xtol, barrier_tol=barrier_tol, maxiter=maxiter)
    if mu0 is not None:
        opts["initial_barrier_parameter"] = mu0
    if tol0 is not None:
        opts["initial_barrier_tolerance"] = tol0
    if tr0 is not None:
        opts["initial_tr_radius"] = tr0
    ctx = (
        consistent_slack(
            np.asarray(slack_floor) if slack_floor is not None else (mu0 or 0.1)
        )
        if slack == "consistent"
        else contextlib.nullcontext()
    )
    with ctx:
        res = minimize(
            lambda x: (f(x), g(x)),
            x0,
            jac=True,
            hessp=lambda x, p: hp(x, p),
            method="trust-constr",
            constraints=[con],
            options=opts,
            callback=cb,
        )
    return res, hist


def summarize(res, hist, fstar, xstar=None, f0=None, tol=1e-8):
    funs = np.array([h["fun"] for h in hist])
    ref = f0 if f0 is not None else fstar
    excursion = float(np.max(funs) - ref) if len(funs) else 0.0
    # first iteration from which |f - f*| stays below tol
    ok = np.abs(funs - fstar) < tol
    back = None
    for i in range(len(ok)):
        if ok[i:].all():
            back = int(hist[i]["nit"])
            break
    out = dict(
        nit=int(res.nit),
        status=int(res.status),
        nfev=int(res.nfev),
        cg=int(res.cg_niter),
        f_end_minus_fstar=float(res.fun - fstar),
        excursion=excursion,
        nit_to_return=back,
        mu_end=float(res.barrier_parameter),
    )
    if xstar is not None:
        out["dx_inf"] = float(np.max(np.abs(res.x - xstar)))
    return out


def multipliers(prob, x, active_tol=1e-6):
    c = prob["cval"](x) - prob["lb"]
    act = np.abs(c) < active_tol
    J = prob["cjac"](x)[act]
    lam, *_ = np.linalg.lstsq(J.T, prob["g"](x), rcond=None)
    return act, lam, c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    ap.add_argument("--seed", type=int, default=3)
    args = ap.parse_args()
    print("scipy", scipy.__version__)
    prob = make_problem(seed=args.seed)
    n = prob["n"]
    x_cold = np.zeros(n)
    out = {"seed": args.seed}

    # ------------------------------------------------ 1. cold reference
    res, hist = solve(prob, x_cold)
    xs, fs = res.x, res.fun
    act, lam, c = multipliers(prob, xs)
    print(
        f"cold: nit={res.nit} status={res.status} f*={fs:.10f} mu_end={res.barrier_parameter:.1e}"
    )
    print("  rows  c-lb:", np.array2string(c, precision=3))
    print(
        "  active:", [lab for lab, a_ in zip(prob["labels"], act) if a_], "lambda:", lam
    )
    out["cold"] = summarize(res, hist, fs, f0=prob["f"](x_cold))
    out["cold"]["slack_at_min"] = c.tolist()
    out["cold"]["active"] = [lab for lab, a_ in zip(prob["labels"], act) if a_]
    out["cold"]["lambda"] = lam.tolist()
    # polish to a very tight reference minimum
    res2, _ = solve(prob, xs, mu0=1e-12, tol0=1e-12, barrier_tol=1e-13, gtol=1e-12)
    xs, fs = res2.x, min(res2.fun, fs)
    print(f"reference f* = {fs:.12f}")

    # x exactly on the active faces (what a face projection / penalty fit gives):
    # Newton-project the active rows to c = lb
    x_face = xs.copy()
    for _ in range(20):
        r = prob["cval"](x_face)[act] - prob["lb"][act]
        J = prob["cjac"](x_face)[act]
        x_face -= J.T @ np.linalg.solve(J @ J.T, r)
    # slightly infeasible point (penalty-walled-like): 1e-4 past each active face
    x_inf = x_face.copy()
    J = prob["cjac"](x_face)[act]
    x_inf -= J.T @ np.linalg.solve(J @ J.T, np.full(act.sum(), 1e-4))

    starts = {"at_min": xs, "on_face": x_face, "infeasible_1e-4": x_inf}
    variants = {
        "scipy_default": dict(),
        "mu0=1e-8": dict(mu0=1e-8, tol0=1e-8),
        "mu0=1e-4": dict(mu0=1e-4, tol0=1e-4),
        "tr0=1e-3": dict(tr0=1e-3),
        "consistent_slack": dict(slack="consistent", slack_floor=1e-8),
        "consistent_slack+mu0=1e-8": dict(
            slack="consistent", mu0=1e-8, tol0=1e-8, slack_floor=1e-8
        ),
        "consistent_slack+mu0=1e-8+tr0=1e-3": dict(
            slack="consistent", mu0=1e-8, tol0=1e-8, slack_floor=1e-8, tr0=1e-3
        ),
        "keep=none (scipy slack)": dict(keep="none"),
        "keep=none+mu0=1e-8": dict(keep="none", mu0=1e-8, tol0=1e-8),
    }
    out["restart"] = {}
    for sname, x0 in starts.items():
        f0 = prob["f"](x0)
        print(f"\n=== restart from {sname}: f0 - f* = {f0 - fs:.3e}")
        out["restart"][sname] = {"f0_minus_fstar": float(f0 - fs)}
        for vname, kw in variants.items():
            r, h = solve(prob, x0, **kw)
            s = summarize(r, h, fs, xstar=xs, f0=fs)
            out["restart"][sname][vname] = s
            print(
                f"  {vname:38s} nit={s['nit']:4d} st={s['status']} "
                f"exc={s['excursion']:10.3e} back@{s['nit_to_return']} "
                f"f-f*={s['f_end_minus_fstar']:.1e} dx={s['dx_inf']:.1e} mu_end={s['mu_end']:.0e}"
            )

    # ------------------------------------------- 2. near starts (moved minimum)
    # perturb the data: a -> a + delta (a "toy" around the old minimum); start
    # from the OLD minimum, compare with a cold solve of the perturbed problem
    out["near"] = {}
    rng = np.random.default_rng(100 + args.seed)
    for itoy in range(4):
        H = prob["H"]
        eig, Q = np.linalg.eigh(H)
        delta = Q @ (rng.normal(size=n) / np.sqrt(eig))  # a 1-sigma toy
        p2 = make_problem(seed=args.seed)
        a2 = p2["a"] + delta
        p2["a"][:] = a2  # closures read prob["a"] by reference
        rc, hc = solve(p2, x_cold)
        rr, _ = solve(p2, rc.x, mu0=1e-12, tol0=1e-12, barrier_tol=1e-13, gtol=1e-12)
        fs2, xs2 = min(rc.fun, rr.fun), rr.x
        act2, _, _ = multipliers(p2, xs2)
        res_t = {
            "cold": summarize(rc, hc, fs2, xstar=xs2),
            "active_changed": bool((act2 != act).any()),
            "f_old_minus_fstar": float(p2["f"](xs) - fs2),
        }
        for vname, kw in {
            "scipy_default": dict(),
            "mu0=1e-8": dict(mu0=1e-8, tol0=1e-8),
            "mu0=1e-6": dict(mu0=1e-6, tol0=1e-6),
            "mu0=1e-4": dict(mu0=1e-4, tol0=1e-4),
            "mu0=1e-2": dict(mu0=1e-2, tol0=1e-2),
            "consistent+mu0=1e-6": dict(
                slack="consistent", mu0=1e-6, tol0=1e-6, slack_floor=1e-8
            ),
        }.items():
            r, h = solve(p2, xs, **kw)
            res_t[vname] = summarize(r, h, fs2, xstar=xs2, f0=p2["f"](xs))
        out["near"][f"toy{itoy}"] = res_t
        print(
            f"\n--- near toy{itoy}: f(old x*) - f*_toy = {res_t['f_old_minus_fstar']:.3f}, "
            f"active set changed: {res_t['active_changed']}"
        )
        for k, s in res_t.items():
            if isinstance(s, dict):
                print(
                    f"  {k:24s} nit={s['nit']:4d} st={s['status']} "
                    f"f-f*={s['f_end_minus_fstar']:.1e} dx={s['dx_inf']:.1e}"
                )

    if args.json:
        with open(args.json, "w") as fh:
            json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
