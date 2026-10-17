#!/usr/bin/env python3
"""Compare complete warm-start STRATEGIES for trust-constr on the toy of
toy_warmstart.py (production tolerances), over several problem seeds.

  S0 rabbit-now   rabbit's keep_feasible rule, scipy's start (mu0 0.1, s0 max(1.5(c-lb),1))
  S1 scipy-none   no row held feasible, scipy's start
  S2 safe-warm    no row held feasible, s0 = max(c-lb, 1e-8), mu0 = tol0 = 1e-5
  S3 fast-warm    no row held feasible, s0 = max(c-lb, 1e-12), mu0 = 1e-9, tol0 = 1e-6
  S4 fast+verify  S3, then a KKT dual-sign check; if a near-bound row has a
                  multiplier of the releasing sign, S2 from S3's end point
  S5 safe+verify  S2, then the same check (and S1 if it fails)

  python toy_strategies.py --seeds 3 5 7 11 13 --out toy_strategies.json
"""

import argparse
import json
import multiprocessing as mp

import numpy as np

import toy_grid as G
import toy_warmstart as T

P = G.PROD
STRATS = {
    "S0 rabbit-now": dict(keep="rabbit"),
    "S1 scipy-none": dict(keep="none"),
    "S2 safe-warm": dict(
        keep="none", slack="consistent", slack_floor=1e-8, mu0=1e-5, tol0=1e-5
    ),
    "S3 fast-warm": dict(
        keep="none", slack="consistent", slack_floor=1e-12, mu0=1e-9, tol0=1e-6
    ),
}


ALL = list(STRATS) + [
    "S4 fast+verify",
    "S5 safe+verify",
    "S6 centred",
    "S7 centred+verify",
    "S8 centred+release",
]


def _centred_leg(p, x0):
    from rabbit.constraints.warm_start import centred_barrier

    mu0 = centred_barrier(
        p["g"](x0), p["cval"](x0), p["cjac"](x0), p["lb"], np.full(len(p["lb"]), np.inf)
    )
    kw = dict(
        keep="none", slack="consistent", slack_floor=1e-3 * mu0, mu0=mu0, tol0=mu0
    )
    return T.solve(p, x0, **P, **kw), mu0


def _release_step(p, x):
    from rabbit.constraints.warm_start import classify_near_rows, release_direction

    lb, ub = p["lb"], np.full(len(p["lb"]), np.inf)
    g, c, J = p["g"](x), p["cval"](x), p["cjac"](x)
    rows, side, _, _, bad = classify_near_rows(g, c, J, lb, ub)
    d = release_direction(J, rows[bad], side[bad], rows[~bad])
    if d is None or not g @ d < 0:
        return None
    curv = d @ p["hp"](x, d)
    t = -(g @ d) / curv if curv > 0 else 1e-3
    f0, v0 = p["f"](x), max(0.0, float(np.max(lb - c)))
    for _ in range(40):
        xt = x + t * d
        if p["f"](xt) < f0 and max(0.0, float(np.max(lb - p["cval"](xt)))) <= v0:
            return xt
        t *= 0.5
    return None


def dual_sign_ok(p, x, near_tol=1e-6, rel=1e-6):
    """True if no near-bound row has a multiplier of the releasing sign.

    grad f = sum_i lam_i grad c_i over the near rows (c_i >= lb_i), lam >= 0 at
    a constrained minimum. A negative lam_i means moving into the interior
    along row i lowers the loss: the row should be released.
    """
    c = p["cval"](x) - p["lb"]
    near = c < near_tol * np.maximum(1.0, np.abs(p["lb"]))
    if not near.any():
        return True, np.array([])
    J = p["cjac"](x)[near]
    g = p["g"](x)
    lam, *_ = np.linalg.lstsq(J.T, g, rcond=None)
    scale = np.linalg.norm(J, axis=1) * 0 + max(1.0, np.max(np.abs(lam)))
    return bool(np.all(lam > -rel * scale)), lam


def run(args):
    seed, sname, st, strat = args
    pseed, scale, itoy, x0 = st
    p = T.make_problem(seed=seed) if pseed is None else G.perturbed(pseed, scale, itoy)
    (xs, fs), rc = G.reference(p, np.zeros(p["n"]))
    out = dict(seed=seed, start=sname, strat=strat, cold_nit=int(rc.nit))
    if strat in STRATS:
        r, h = T.solve(p, x0, **P, **STRATS[strat])
        nit, legs = r.nit, [r.nit]
    elif strat.startswith("S8"):
        x, nit, legs, h = x0, 0, [], []
        for rnd in range(4):
            (r, hh), mu0 = _centred_leg(p, x)
            out.setdefault("mu0", mu0)
            x, nit, h = r.x, nit + r.nit, h + hh
            legs.append(int(r.nit))
            ok, _ = dual_sign_ok(p, x)
            if ok:
                break
            out["verify_failed"] = True
            xr = _release_step(p, x) if rnd < 3 else None
            if xr is None:
                r, h2 = T.solve(p, x, **P, **STRATS["S1 scipy-none"])
                nit, h = nit + r.nit, h + h2
                legs.append(-int(r.nit))  # negative: the last-resort cold leg
                break
            h.append(dict(fun=float(p["f"](xr))))
            x = xr
    elif strat.startswith("S6") or strat.startswith("S7"):
        from rabbit.constraints.warm_start import centred_barrier

        mu0 = centred_barrier(
            p["g"](x0),
            p["cval"](x0),
            p["cjac"](x0),
            p["lb"],
            np.full(len(p["lb"]), np.inf),
        )
        out["mu0"] = mu0
        kw = dict(
            keep="none", slack="consistent", slack_floor=1e-3 * mu0, mu0=mu0, tol0=mu0
        )
        r, h = T.solve(p, x0, **P, **kw)
        nit, legs = r.nit, [r.nit]
        if strat.startswith("S7"):
            ok, lam = dual_sign_ok(p, r.x)
            out["verify_failed"] = not ok
            if not ok:
                r, h2 = T.solve(p, r.x, **P, **STRATS["S1 scipy-none"])
                nit += r.nit
                legs.append(r.nit)
                h = h + h2
    else:
        first, second = (
            ("S3 fast-warm", "S2 safe-warm")
            if strat == "S4 fast+verify"
            else ("S2 safe-warm", "S1 scipy-none")
        )
        r, h = T.solve(p, x0, **P, **STRATS[first])
        nit, legs = r.nit, [r.nit]
        ok, lam = dual_sign_ok(p, r.x)
        out["verify_failed"] = not ok
        if not ok:
            r, h2 = T.solve(p, r.x, **P, **STRATS[second])
            nit += r.nit
            legs.append(r.nit)
            h = h + h2
    s = T.summarize(r, h, fs, xstar=xs, f0=p["f"](x0), tol=1e-6)
    out.update(
        s,
        nit=int(nit),
        legs=legs,
        f0_minus_fstar=float(p["f"](x0) - fs),
        ok=bool((abs(r.fun - fs) < 1e-5 or r.fun < fs) and r.constr_violation < 1e-6),
    )
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[3, 5, 7, 11, 13])
    ap.add_argument("--out", default="toy_strategies.json")
    ap.add_argument("--procs", type=int, default=8)
    a = ap.parse_args()
    jobs = []
    for seed in a.seeds:
        starts, info = G.build_starts(seed)
        print("cold", seed, info)
        for sname, st in starts.items():
            for strat in ALL:
                jobs.append((seed, sname, st, strat))
    with mp.Pool(a.procs) as pool:
        res = pool.map(run, jobs, chunksize=2)
    json.dump(res, open(a.out, "w"), indent=0)
    # table
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
        f"{'strategy':16s} | "
        + " | ".join(f"{c:>13s}" for c in classes)
        + " | fail/n | verify-retries | worst exc (min/face)"
    )
    for strat in ALL:
        rs = [r for r in res if r["strat"] == strat and r["cold_nit"] < P["maxiter"]]
        cells = []
        for c in classes:
            nits = [r["nit"] for r in rs if cls(r["start"]) == c]
            cells.append(f"{int(np.median(nits)):4d} [{max(nits):4d}]")
        fail = sum(not r["ok"] for r in rs)
        retr = sum(r.get("verify_failed", False) for r in rs)
        exc = max(
            r["excursion"] for r in rs if cls(r["start"]) in ("at_min", "on_face")
        )
        print(
            f"{strat:16s} | "
            + " | ".join(f"{c:>13s}" for c in cells)
            + f" | {fail:3d}/{len(rs):3d} | {retr:3d} | {exc:.0e}"
        )
    nexc = sum(
        r["cold_nit"] >= P["maxiter"] for r in res if r["strat"] == "S0 rabbit-now"
    )
    print(f"(starts whose own cold reference hit maxiter, excluded: {nexc})")


if __name__ == "__main__":
    main()
