#!/usr/bin/env python3
"""Candidate recipes on the quadratic surrogate, in the BOUND basis of the NP damping conditions.

Basis change for the 4 fitted NP lambdas of the nominal (lambda4_nu held at 0, lambda_inf = 1):
    p = L2(|Y|=0) = lambda2            q = L2(|Y|=2.5) = lambda2 + 6.25 delta_lambda2
    r = 3 lambda4 + min(p, q)^3        nu = lambda2_nu
i.e. lambda2 = p, delta_lambda2 = (q - p)/6.25, lambda4 = (r - min(p,q)^3)/3. Then ALL 5 armed
NPDampingWall conditions are the 4 simple bounds p, q, r, nu >= 0 (B at the other |Y| is r + |p^3-q^3|/... >= r).
min(p,q) is a kink only where delta_lambda2 = 0; every minimum seen so far has delta_lambda2 < 0 (q < p).

Recipes compared (wall OFF in all of them -- the constraints are exact by construction):
  as   : active-set trust-krylov on the bounds (TRON-lite): trust-krylov on the free variables; a step
         that crosses a bound is cut at the bound and that variable is frozen (rabbit: a freeze mask);
         at inner convergence, a frozen variable whose gradient points INTO the feasible side is released.
  sq   : squares reparametrisation p = a^2, ... (unconstrained, smooth; zero gradient at a = 0).
Costs are reported in loss+grad evaluations (n_f) and HVPs (n_hvp), as for run_surrogate.py.
"""
import json
import os
import sys
import time

import numpy as np
from scipy.optimize._trlib import get_trlib_quadratic_subproblem

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_surrogate import OUT, load_start  # noqa: E402
from surrogate import Surrogate  # noqa: E402

KEYS = ("lambda2", "delta_lambda2", "lambda4", "lambda2_nu")
ULAB = (
    "p=L2(0)",
    "q=L2(2.5)",
    "r=B",
    "nu=lambda2_nu",
)  # what each of those slots holds in the bound basis


class BoundBasis:
    def __init__(self, S, squares=False, rq=False):
        self.S = S
        self.sq = squares
        self.rq = (
            rq  # r = 3 lambda4 + q^3 (no min(p,q) kink); B(0) left to the (slack) wall
        )
        self.ix = [S.idx[k] for k in KEYS]

    # u = (p, q, r, nu)  [or their square roots]  <->  theta
    def lam_from_u(self, u):
        p, q, r, nu = u**2 if self.sq else u
        m = q if self.rq else min(p, q)
        return np.array([p, (q - p) / 6.25, (r - m**3) / 3.0, nu])

    def theta_np(self, u):
        l2, dl2, l4, nu = self.lam_from_u(u)
        return np.array(
            [(l2 - 0.4) / 0.5, dl2 / 0.5, (l4 - 0.4) / 0.5, (nu - 0.15) / 0.1]
        )

    def u_from_theta(self, x):
        t = x[self.ix]
        l2, dl2, l4, nu = (
            0.4 + 0.5 * t[0],
            0.5 * t[1],
            0.4 + 0.5 * t[2],
            0.15 + 0.1 * t[3],
        )
        p, q = l2, l2 + 6.25 * dl2
        r = 3 * l4 + (q if self.rq else min(p, q)) ** 3
        u = np.array([p, q, r, nu])
        if self.sq:
            assert (u >= 0).all(), u
            u = np.sqrt(u)
        return u

    def x_of(self, z):
        """z = full vector with the 4 NP slots holding u."""
        x = z.copy()
        x[self.ix] = self.theta_np(z[self.ix])
        return x

    def jac(self, u, eps=1e-7):
        J = np.zeros((4, 4))
        for j in range(4):
            e = np.zeros(4)
            e[j] = eps
            J[:, j] = (self.theta_np(u + e) - self.theta_np(u - e)) / (2 * eps)
        return J

    def fun(self, z):
        x = self.x_of(z)
        f, g = self.S.fun(x)
        gz = g.copy()
        gz[self.ix] = self.jac(z[self.ix]).T @ g[self.ix]
        return f, gz

    def hessp(self, z, v):
        u = z[self.ix]
        x = self.x_of(z)
        J = self.jac(u)
        w = v.copy()
        w[self.ix] = J @ v[self.ix]
        hw = self.S.hessp(x, w)
        out = hw.copy()
        out[self.ix] = J.T @ hw[self.ix]
        # second-order term of the map: sum_k g_k d2theta_k/du2 v
        _, g = self.S.fun(x)
        self.S.n_f -= 1
        eps = 1e-5
        e = v[self.ix]
        Jp, Jm = self.jac(u + eps * e), self.jac(u - eps * e)
        out[self.ix] += ((Jp - Jm) / (2 * eps)).T @ g[self.ix]
        return out


TRACE = (
    []
)  # (f, n_f, n_hvp) after every accepted step, filled by tr_loop; read by main()
EDM_STOP = (
    1e-11  # inner stop: an INTERIOR step predicting less than this (~EDM) = converged
)


def tr_loop(fun, hessp, z0, free, maxiter, on_accept=None, gstop=1e-10, S=None):
    """scipy trust-krylov loop (copy of _minimize_trust_region) on the free coordinates only.

    Extra stop (not in scipy): an interior (not boundary) step whose predicted reduction is below
    EDM_STOP -- for an interior Newton step pred = 1/2 g^T H^-1 g = EDM, the certification measure.
    """
    n = len(z0)
    P = free.astype(float)
    cache = {}

    def fg(y):
        k = y.tobytes()
        if k not in cache:
            cache.clear()
            f, g = fun(z0 + P * y)
            cache[k] = (f, P * g)
        return cache[k]

    hp = lambda y, p: P * hessp(z0 + P * y, P * p)  # noqa: E731
    sub = get_trlib_quadratic_subproblem(tol_rel_i=-2.0, tol_rel_b=-3.0)
    y = np.zeros(n)
    r = 1.0
    m = sub(y, lambda y: fg(y)[0], lambda y: fg(y)[1], None, hp)
    k = 0
    event = None
    for k in range(maxiter):
        if m.jac_mag < gstop:
            break
        p, hb = m.solve(r)
        pv = m(p)
        yp = y + p
        mp = sub(yp, lambda y: fg(y)[0], lambda y: fg(y)[1], None, hp)
        pred = m.fun - pv
        if pred <= 0 or (pred < EDM_STOP and not hb):
            break
        rho = (m.fun - mp.fun) / pred
        if rho < 0.25:
            r *= 0.25
        elif rho > 0.75 and hb:
            r = min(2 * r, 1000.0)
        if rho > 0.15:
            if on_accept is not None:
                event = on_accept(z0 + P * y, z0 + P * yp)
                if event is not None:
                    return event, k + 1
            y, m = yp, mp
            if S is not None:
                TRACE.append((float(m.fun), S.n_f, S.n_hvp))
    return ("converged", z0 + P * y), k + 1


def active_set(BB, z0, maxiter=5000):
    S = BB.S
    bidx = np.array(BB.ix)  # the 4 bound variables live at these slots (u >= 0)
    act = set(int(i) for i in bidx if z0[i] <= 0)
    z = z0.copy()
    for i in act:
        z[i] = 0.0
    log = []
    total_it = 0
    for outer in range(50):
        free = np.ones(len(z), bool)
        free[list(act)] = False

        def on_accept(zold, znew):
            neg = [i for i in bidx if free[i] and znew[i] < 0]
            if not neg:
                return None
            # cut the step at the first bound crossing (TRON breakpoint)
            alphas = [zold[i] / (zold[i] - znew[i]) for i in neg]
            j = int(np.argmin(alphas))
            zc = zold + alphas[j] * (znew - zold)
            zc[neg[j]] = 0.0
            return ("hit", zc, neg[j])

        ev, nit = tr_loop(BB.fun, BB.hessp, z, free, maxiter, on_accept, S=S)
        total_it += nit
        if ev[0] == "hit":
            z = ev[1]
            act.add(ev[2])
            log.append(
                dict(
                    outer=outer,
                    event="hit",
                    var=ULAB[list(bidx).index(ev[2])],
                    it=nit,
                    f=float(S.fun(BB.x_of(z))[0]),
                )
            )
            S.n_f -= 1
            continue
        z = ev[1]
        _, g = BB.fun(z)
        S.n_f -= 1
        rel = [
            i for i in act if g[i] < -1e-8
        ]  # gradient wants u_i to INCREASE -> release
        log.append(
            dict(
                outer=outer,
                event="converged",
                it=nit,
                f=float(S.fun(BB.x_of(z))[0]),
                active=[ULAB[list(bidx).index(i)] for i in act],
                mult={ULAB[list(bidx).index(i)]: float(g[i]) for i in act},
            )
        )
        S.n_f -= 1
        if not rel:
            break
        act.remove(min(rel, key=lambda i: g[i]))
    return z, log, total_it


def main():
    rec, start = sys.argv[1], sys.argv[2]
    S = Surrogate(tau=8.0)
    rq = rec.endswith("rq")
    S.wall = (
        rq  # rq: the wall stays on as the guard for B(0) only (slack whenever q <= p)
    )
    x0 = load_start(start, S.names)
    BB = BoundBasis(S, squares=rec.startswith("sq"), rq=rq)
    z0 = x0.copy()
    z0[BB.ix] = BB.u_from_theta(x0)
    S.n_f = S.n_hvp = 0
    t0 = time.time()
    if rec.startswith("as"):
        z, log, nit = active_set(BB, z0)
    elif rec.startswith("sq"):
        free = np.ones(len(z0), bool)
        ev, nit = tr_loop(BB.fun, BB.hessp, z0, free, 20000, S=S)
        z, log = ev[1], []
    x = BB.x_of(z)
    f = S.fun(x)[0]
    S.n_f -= 1
    c = S.conds(x)[0]
    tr = {}
    for thr in (1e-1, 1e-3, 1e-6, 1e-9):
        hit = next((t for t in TRACE if t[0] <= thr), None)
        tr[f"to_{thr:g}"] = None if hit is None else dict(nf=hit[1], nhvp=hit[2])
    res = dict(
        recipe=rec,
        start=start,
        f_end=float(f),
        iters=nit,
        n_f=S.n_f,
        n_hvp=S.n_hvp,
        **tr,
        seconds=time.time() - t0,
        conds=dict(zip(S.labels, c.tolist())),
        dist_to_ref=float(np.linalg.norm(x - S.x_ref)),
        log=log,
    )
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(f"{OUT}/{rec}_{start}.json", "w"), indent=1)
    print(
        f"{rec}_{start}: f_end {f:.3e} iters {nit} n_f {S.n_f} n_hvp {S.n_hvp} |x-ref| {res['dist_to_ref']:.2e} "
        f"face {c[S.iface]:.2e} cmin {c.min():.2e} to1e-6 {tr['to_1e-06']} to1e-3 {tr['to_0.001']} log {log}",
        flush=True,
    )


if __name__ == "__main__":
    main()
