#!/usr/bin/env python3
"""Fallback chains after a failed KKT dual-sign check (toy_strategies.py S3 legs).

Every chain starts with the fast warm leg (no row held, s0 = max(c-lb, 1e-12),
mu0 = tol0 = 1e-9) and, while the dual-sign check fails, runs the next leg
from the previous end point (at most 3 legs).

  python toy_fallback.py --seeds 3 5 7 11 13
"""
import argparse
import json
import multiprocessing as mp

import numpy as np

import toy_grid as G
import toy_strategies as S
import toy_warmstart as T

FAST = dict(keep="none", slack="consistent", slack_floor=1e-12, mu0=1e-9, tol0=1e-9)


def leg(kind, p, x, lam_bad=None):
    if kind == "fast":
        return FAST
    if kind == "mu1e-5":
        return dict(FAST, mu0=1e-5, tol0=1e-5)
    if kind == "mu1e-3":
        return dict(FAST, mu0=1e-3, tol0=1e-3)
    if kind == "scipy":
        return dict(keep="none")
    if kind.startswith("release"):
        # the rows with a releasing multiplier get slack mu_r/|lam| (centred at
        # mu_r for the multiplier they would need), the rest as FAST
        mu_r = float(kind.split("=")[1])
        c = p["cval"](x) - p["lb"]
        floor = np.full(len(c), 1e-12)
        near = c < 1e-6 * np.maximum(1.0, np.abs(p["lb"]))
        idx = np.where(near)[0]
        for i, lam in zip(idx, lam_bad):
            if lam < 0:
                floor[i] = mu_r / max(abs(lam), 1e-3)
        return dict(FAST, slack_floor=floor, mu0=mu_r, tol0=mu_r)
    raise ValueError(kind)


CHAINS = {
    "fast>mu1e-5>scipy": ["fast", "mu1e-5", "scipy"],
    "fast>mu1e-3>scipy": ["fast", "mu1e-3", "scipy"],
    "fast>scipy": ["fast", "scipy"],
    "fast>release1e-5>scipy": ["fast", "release=1e-5", "scipy"],
    "fast>release1e-3>scipy": ["fast", "release=1e-3", "scipy"],
}


def run(args):
    seed, sname, st, chain = args
    pseed, scale, itoy, x0 = st
    p = T.make_problem(seed=seed) if pseed is None else G.perturbed(pseed, scale, itoy)
    (xs, fs), rc = G.reference(p, np.zeros(p["n"]))
    x, nit, legs, lam = x0, 0, [], None
    for kind in CHAINS[chain]:
        r, _ = T.solve(p, x, **G.PROD, **leg(kind, p, x, lam))
        x, nit = r.x, nit + r.nit
        legs.append(int(r.nit))
        ok, lam = S.dual_sign_ok(p, x)
        if ok:
            break
    return dict(
        seed=seed,
        start=sname,
        chain=chain,
        nit=nit,
        legs=legs,
        cold_nit=int(rc.nit),
        ok=bool((abs(r.fun - fs) < 1e-5 or r.fun < fs) and r.constr_violation < 1e-6),
        df=float(r.fun - fs),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[3, 5, 7, 11, 13])
    ap.add_argument("--procs", type=int, default=8)
    ap.add_argument("--out", default="toy_fallback.json")
    a = ap.parse_args()
    jobs = []
    for seed in a.seeds:
        starts, _ = G.build_starts(seed)
        for sname, st in starts.items():
            for chain in CHAINS:
                jobs.append((seed, sname, st, chain))
    with mp.Pool(a.procs) as pool:
        res = pool.map(run, jobs, chunksize=2)
    json.dump(res, open(a.out, "w"), indent=0)
    cls = lambda s: (
        "at_min"
        if s == "at_min"
        else (
            "on_face"
            if s == "on_face"  # noqa: E731
            else (
                "infeas"
                if s.startswith("infeas")
                else "0.1sig" if "0.1s" in s else "1sig"
            )
        )
    )
    classes = ["at_min", "on_face", "infeas", "0.1sig", "1sig"]
    print(
        f"{'chain':24s} | "
        + " | ".join(f"{c:>13s}" for c in classes)
        + " | fail | multi-leg | cold 1sig median"
    )
    for chain in CHAINS:
        rs = [
            r for r in res if r["chain"] == chain and r["cold_nit"] < G.PROD["maxiter"]
        ]
        cells = []
        for c in classes:
            nits = [r["nit"] for r in rs if cls(r["start"]) == c]
            cells.append(f"{int(np.median(nits)):4d} [{max(nits):4d}]")
        cold1 = int(np.median([r["cold_nit"] for r in rs if cls(r["start"]) == "1sig"]))
        print(
            f"{chain:24s} | "
            + " | ".join(f"{c:>13s}" for c in cells)
            + f" | {sum(not r['ok'] for r in rs):3d}/{len(rs)} | {sum(len(r['legs']) > 1 for r in rs):3d} | {cold1}"
        )


if __name__ == "__main__":
    main()
