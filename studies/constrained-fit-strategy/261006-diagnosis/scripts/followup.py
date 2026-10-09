#!/usr/bin/env python3
"""Follow-up (orchestrator, 2026-10-06): cheapest parameter/tolerance-level fixes for the trust-krylov crawl,
on the quadratic surrogate (scripts/surrogate.py). No cache load, no real fit.

Recipes (all trust-krylov, i.e. scipy's outer loop + trlib, unless stated):
  R0      rabbit defaults as used by the census: --earlyStopping 20, --stallRelTol 0, --maxRestarts -1
  RS      restart-on-stall: --earlyStopping N --stallRelTol r --maxRestarts -1, N in {10,20}, r in {1e-9,1e-8,1e-7}
  C2      a C^2 wall: relu^3 at matched equilibrium overshoot, and relu^2 with its curvature ramped over delta
  TC      tau-continuation 5 -> 8 (-> 11), every stage a fresh rabbit fit (fresh minimize, R0 flags)
  NCG     the same with scipy's Steihaug-CG subproblem (= rabbit tf-trust-ncg's algorithm)

Semantics copied from the code, not guessed:
  * outer loop: scipy 1.18 optimize/_trustregion.py _minimize_trust_region (radius x1/4 if rho < 0.25, x2 if
    rho > 0.75 and the step hits the boundary, accept if rho > 0.15, initial radius 1, max 1000; the callback is
    called EVERY iteration, accepted or not, with the current accepted (x, fun)). rabbit's native
    minimizer/base.py _minimize_trust_region has the identical update rule and callback placement.
  * stall test: rabbit/callbacks.py FitterCallback.__call__: once len(history) > N, ref = history[-N]; stall if
    loss >= ref - r*|ref| (r = 0: loss >= ref); checked BEFORE appending, so on a stall xval is the PREVIOUS
    iteration's x. Raised as an exception, which ends that minimize().
  * restart loop: rabbit/fitter.py fit(): restart from cb.xval with a fresh minimize() (radius back to 1.0) while
    the loss keeps improving: stop if not stalled, or if last_loss >= prev_loss - 1e-9*max(1,|prev_loss|)
    (RESTART_MIN_IMPROVEMENT), or if the restart cap is reached.
  * losses passed to the stall/restart tests are offset by NOMSTIFF's NLL (376.61) so the relative tolerances act
    at the real scale (the surrogate's own f is ~0 at its minimum).
Cost: n_f = loss+grad evaluations (one per iteration), n_hvp = HVPs; real hours ~ 2 x (27 n_f + 13 n_hvp)/3600.
Metrics per run: E_conv = n_f when f - f* first < 1e-6 (f* = that recipe's own walled minimum), E_total = n_f when
the fit stops by itself, final f - f*, face overshoot.
"""
import json
import os
import sys
import time

import numpy as np
from scipy.optimize._trlib import get_trlib_quadratic_subproblem
from scipy.optimize._trustregion_ncg import CGSteihaugSubproblem

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_surrogate import STARTS, load_start  # noqa: E402
from surrogate import A, Surrogate  # noqa: E402

TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTD = f"{TASK}/followup"
L0 = 376.6146329237086  # NOMSTIFF NLL: the real loss scale for the relative stall tests
CAP = 8000  # total iteration cap per run -> "fail"
RESTART_MIN_IMPROVEMENT = 1e-9


class Stall(Exception):
    pass


class CB:
    """rabbit FitterCallback stall logic, verbatim in effect."""

    def __init__(self, xv, N, r):
        self.N, self.r, self.hist, self.xval = N, r, [], xv

    def __call__(self, x, loss):
        if self.N > 0 and len(self.hist) > self.N:
            ref = self.hist[-self.N]
            budget = self.r * abs(ref) if self.r else 0.0
            if loss >= ref - budget:
                raise Stall()
        self.hist.append(loss)
        self.xval = x


def fstar(S):
    """Walled minimum of the surrogate for the current penalty: single active linear face L2(2.5).

    Stationarity g + H d - phi'(t) a = 0 with t = -a.d the violation and g = mu a gives
    d = -(mu - phi'(t)) H^-1 a, and t solves t = (mu - phi'(t)) * alpha, alpha = a^T H^-1 a (bisection).
    """
    a = S.conds(S.x_ref)[1][S.iface]
    Hia = np.linalg.solve(S.H, a)
    alpha = float(a @ Hia)
    lo, hi = 0.0, S.mu * alpha
    for _ in range(200):
        t = 0.5 * (lo + hi)
        if t - (S.mu - float(S.dphi(np.array(t)))) * alpha > 0:
            hi = t
        else:
            lo = t
    w = S.mu - float(S.dphi(np.array(t)))
    return -S.mu * w * alpha + 0.5 * w * w * alpha + float(S.phi(np.array(t))), t


def one_round(S, x0, cb, sub, rec, cap_left):
    """scipy _minimize_trust_region from x0 (fresh radius); cb called every iteration; returns (x, stalled, it)."""
    cache = {}

    def f_only(x):
        k = x.tobytes()
        if k not in cache:
            cache.clear()
            cache[k] = S.fun(x)
        return cache[k][0]

    def g_only(x):
        f_only(x)
        return cache[x.tobytes()][1]

    hessp = lambda x, p: S.hessp(x, p)  # noqa: E731
    x = x0.copy()
    r = 1.0
    m = sub(x, f_only, g_only, None, hessp)
    it = 0
    while it < cap_left:
        p, hb = m.solve(r)
        pv = m(p)
        xp = x + p
        mp = sub(xp, f_only, g_only, None, hessp)
        pred = m.fun - pv
        if pred <= 0:
            return x, False, it, "pred<=0"
        rho = (m.fun - mp.fun) / pred
        if rho < 0.25:
            r *= 0.25
        elif rho > 0.75 and hb:
            r = min(2 * r, 1000.0)
        if rho > 0.15:
            x, m = xp, mp
        it += 1
        rec(m.fun)
        try:
            cb(x.copy(), L0 + m.fun)
        except Stall:
            return cb.xval, True, it, "stall"
    return x, False, it, "cap"


def fit(S, x0, N=20, r=0.0, max_restarts=-1, sub=None, fs=None):
    """rabbit fit() restart loop around one_round."""
    sub = sub or get_trlib_quadratic_subproblem(tol_rel_i=-2.0, tol_rel_b=-3.0)
    trace = []
    E = dict(conv=None)

    def rec(f):
        trace.append(f)
        if E["conv"] is None and f - fs < 1e-6:
            E["conv"] = (S.n_f, S.n_hvp)

    xval, prev, attempt, total, stops = x0, None, 0, 0, []
    while True:
        cb = CB(xval, N, r)
        xval, stalled, it, why = one_round(S, xval, cb, sub, rec, CAP - total)
        total += it
        stops.append(why)
        last = cb.hist[-1] if cb.hist else None
        if not stalled or total >= CAP:
            break
        if (
            prev is not None
            and last is not None
            and last >= prev - RESTART_MIN_IMPROVEMENT * max(1.0, abs(prev))
        ):
            stops.append("restart-bought-nothing")
            break
        if 0 <= max_restarts <= attempt:
            break
        attempt += 1
        prev = last
    return xval, dict(
        restarts=attempt,
        iters=total,
        stops=stops[-3:],
        capped=total >= CAP,
        conv=E["conv"],
    )


def configure(S, pen="relu2", tau=8.0, K3=None, delta=None):
    S.K = np.exp(2 * tau)
    S.tau = tau
    S.pen = pen
    S.K3 = K3
    S.delta = delta


def run(S, start, label, stages, N=20, r=0.0, sub=None):
    x = START_X[start]
    S.n_f = S.n_hvp = 0
    t0 = time.time()
    info = []
    conv_total = None
    for cfg in stages:
        configure(S, **cfg)
        fs, tstar = fstar(S)
        nf0, nh0 = S.n_f, S.n_hvp
        x, inf = fit(S, x, N=N, r=r, sub=sub, fs=fs)
        inf.update(
            cfg=cfg,
            n_f=S.n_f - nf0,
            n_hvp=S.n_hvp - nh0,
            fstar=fs,
            overshoot_star=tstar,
        )
        info.append(inf)
    # E_conv: the LAST stage's first entry below f*+1e-6 (for continuation, earlier stages are part of the cost)
    last = info[-1]
    conv = None
    if last["conv"] is not None:
        conv = dict(n_f=last["conv"][0], n_hvp=last["conv"][1])
    f_end = S.fun(x)[0] - info[-1]["fstar"]
    S.n_f -= 1
    face = float(S.conds(x)[0][S.iface])
    res = dict(
        label=label,
        start=start,
        N=N,
        r=r,
        stages=info,
        E_conv=conv,
        E_total=dict(n_f=S.n_f, n_hvp=S.n_hvp),
        f_end_minus_fstar=float(f_end),
        face_end=face,
        failed=conv is None,
        restarts=sum(i["restarts"] for i in info),
        seconds=time.time() - t0,
    )
    os.makedirs(OUTD, exist_ok=True)
    json.dump(res, open(f"{OUTD}/{label}__{start}.json", "w"), indent=1, default=float)
    print(
        f"{label:22s} {start:8s} E_conv {conv} E_total {res['E_total']} restarts {res['restarts']} "
        f"f-f* {f_end:.1e} face {face:.2e} fail {res['failed']}",
        flush=True,
    )
    return res


STARTS = dict(STARTS)
START_KEYS = ["NOMSTIFF", "CENS03R", "C1A", "pert000", "cold000", "pert002"]
START_X = {}

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    S = Surrogate(tau=8.0)
    START_X["NOMSTIFF"] = np.load(f"{A}/NOMSTIFF.npz")["x"]
    for k in START_KEYS[1:]:
        START_X[k] = load_start(k, S.names)
    v0 = 9.15e-7  # relu^2 tau=8 equilibrium overshoot on L2(2.5) (NOMSTIFF)
    K3m = S.mu / (3 * v0**2)  # relu^3 with the SAME equilibrium overshoot
    R = {
        "R0_default": dict(stages=[dict()], N=20, r=0.0),
        **{
            f"RS_N{N}_r{r:g}": dict(stages=[dict()], N=N, r=r)
            for N in (10, 20)
            for r in (1e-9, 1e-8, 1e-7)
        },
        # beyond the requested grid: where the stall test starts to fire on the lock-in
        **{
            f"RSX_N{N}_r{r:g}": dict(stages=[dict()], N=N, r=r)
            for N in (10, 20)
            for r in (1e-6, 1e-5, 1e-4)
        },
        "C2_relu3_tau8": dict(stages=[dict(pen="relu3", K3=np.exp(16))]),
        "C2_relu3_matched": dict(stages=[dict(pen="relu3", K3=K3m)]),
        **{
            f"C2_smooth_d{d:g}": dict(stages=[dict(pen="smooth2", delta=d)])
            for d in (1e-6, 1e-5, 1e-4)
        },
        "TC_5_8": dict(stages=[dict(tau=5.0), dict(tau=8.0)]),
        "TC_5_8_11": dict(stages=[dict(tau=5.0), dict(tau=8.0), dict(tau=11.0)]),
        "NCG_R0": dict(stages=[dict()], sub="ncg"),
        "NCG_RS_N10_r1e-8": dict(stages=[dict()], N=10, r=1e-8, sub="ncg"),
    }
    for label, spec in R.items():
        if which != "all" and not label.startswith(which):
            continue
        sub = CGSteihaugSubproblem if spec.get("sub") == "ncg" else None
        for st in START_KEYS:
            run(
                S,
                st,
                label,
                spec["stages"],
                N=spec.get("N", 20),
                r=spec.get("r", 0.0),
                sub=sub,
            )
