#!/usr/bin/env python3
"""Grid over the trust-constr interior-point start knobs on the toy of
toy_warmstart.py, at rabbit's production tolerances (gtol 1e-8, xtol 1e-10,
barrier_tol 1e-9).

Knobs: keep_feasible rule (rabbit / none), slack init (scipy's
max(1.5(c-lb),1) or max(c-lb, delta)), mu0 (= initial barrier tolerance), tr0.
Starts: the cold minimum itself, the same point projected exactly onto its
active faces, 1e-4 past them (a penalty-walled fit), and the old minimum used
as the start of perturbed problems (toy data shifted by 0.1 sigma and 1 sigma:
scans / toys / saturated sub-fit analogues).

  python toy_grid.py --out toy_grid.json [--procs 4]
"""

import argparse
import itertools
import json
import multiprocessing as mp

import numpy as np

import toy_warmstart as T

PROD = dict(gtol=1e-8, xtol=1e-10, barrier_tol=1e-9, maxiter=2000)


def perturbed(seed, scale, itoy):
    p = T.make_problem(seed=seed)
    eig, Q = np.linalg.eigh(p["H"])
    rng = np.random.default_rng(1000 * itoy + int(100 * scale))
    p["a"][:] = p["a"] + Q @ (scale * rng.normal(size=p["n"]) / np.sqrt(eig))
    return p


def reference(p, x0):
    """Cold + polish: the minimum to compare against."""
    r, _ = T.solve(p, x0, **PROD)
    r2, _ = T.solve(
        p,
        r.x,
        mu0=1e-12,
        tol0=1e-12,
        gtol=1e-12,
        xtol=1e-14,
        barrier_tol=1e-13,
        maxiter=3000,
    )
    return (r2.x, r2.fun) if r2.fun < r.fun else (r.x, r.fun), r


def build_starts(seed):
    p0 = T.make_problem(seed=seed)
    n = p0["n"]
    (xs, fs), rcold = reference(p0, np.zeros(n))
    c = p0["cval"](xs) - p0["lb"]
    act = c < 1e-6
    x_face = xs.copy()
    for _ in range(30):
        r = p0["cval"](x_face)[act] - p0["lb"][act]
        J = p0["cjac"](x_face)[act]
        x_face -= J.T @ np.linalg.solve(J @ J.T, r)
    J = p0["cjac"](x_face)[act]
    x_inf = x_face - J.T @ np.linalg.solve(J @ J.T, np.full(act.sum(), 1e-4))
    starts = {
        "at_min": (None, 0.0, 0, xs),
        "on_face": (None, 0.0, 0, x_face),
        "infeas_1e-4": (None, 0.0, 0, x_inf),
    }
    for scale in (0.1, 1.0):
        for itoy in range(3):
            starts[f"toy{scale:g}s_{itoy}"] = (seed, scale, itoy, xs)
    return starts, dict(
        cold_nit=int(rcold.nit),
        cold_status=int(rcold.status),
        fstar=float(fs),
        active=[lab for lab, a_ in zip(p0["labels"], act) if a_],
    )


_REF = {}


def job(args):
    seed, sname, (pseed, scale, itoy, x0), keep, slack, mu0, tr0, tol0 = args
    p = T.make_problem(seed=seed) if pseed is None else perturbed(pseed, scale, itoy)
    key = (seed, sname)
    if key not in _REF:
        (xs, fs), rc = reference(p, np.zeros(p["n"]))
        _REF[key] = (xs, fs, int(rc.nit))
    xs, fs, cold_nit = _REF[key]
    kw = dict(PROD, keep=keep)
    if slack != "scipy":
        kw.update(slack="consistent", slack_floor=float(slack))
    if mu0 is not None:
        kw.update(mu0=mu0, tol0=mu0 if tol0 in (None, "mu0") else max(mu0, tol0))
    if tr0 is not None:
        kw.update(tr0=tr0)
    r, h = T.solve(p, x0, **kw)
    s = T.summarize(r, h, fs, xstar=xs, f0=p["f"](x0), tol=1e-6)
    s.update(
        seed=seed,
        start=sname,
        keep=keep,
        slack=str(slack),
        mu0=mu0,
        tr0=tr0,
        tol0=str(tol0),
        cold_nit=cold_nit,
        f0_minus_fstar=float(p["f"](x0) - fs),
    )
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="toy_grid.json")
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--seeds", type=int, nargs="+", default=[3])
    ap.add_argument("--grid", type=int, default=1)
    args = ap.parse_args()
    if args.grid == 1:
        # first pass: what each knob does
        grid = list(
            itertools.product(
                ["rabbit", "none"],
                ["scipy", 1e-2, 1e-4, 1e-6, 1e-8],
                [None, 1e-3, 1e-5, 1e-7, 1e-9],
                [None],
                [None],
            )
        )
    else:
        # second pass: the warm-start candidates (tol0 = initial barrier tolerance)
        grid = list(
            itertools.product(
                ["none", "near"],
                [1e-12, 1e-8, 1e-6],
                [1e-5, 1e-7, 1e-9],
                [None],
                ["mu0", 1e-6],
            )
        )
    jobs, infos = [], {}
    for seed in args.seeds:
        starts, info = build_starts(seed)
        infos[seed] = info
        print("cold:", seed, info)
        jobs += [(seed, sname, st, *g) for sname, st in starts.items() for g in grid]
    with mp.Pool(args.procs) as pool:
        res = pool.map(job, jobs, chunksize=4)
    with open(args.out, "w") as fh:
        json.dump(dict(info=infos, results=res), fh, indent=0)
    print("wrote", args.out, len(res))


if __name__ == "__main__":
    main()
