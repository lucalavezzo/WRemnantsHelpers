#!/usr/bin/env python3
"""Parse rabbit trust-constr / trust-krylov iteration logs into per-iteration records.

Splits a rabbit log into minimisation legs (each starts at 'Iteration 0:'), and for each
iteration records loss, dt, elapsed, and (trust-constr) optimality, barrier, tr_radius.
A step is 'rejected' when the loss is unchanged and the trust radius shrank.
Usage: parse_tc_log.py LOG [LOG...] --json out.json
"""
import argparse, json, re, sys

ANSI = re.compile(r"\x1b\[[0-9;]*m")
IT = re.compile(
    r"Iteration (\d+): loss ([-0-9.eE+naninf]+)\s+\[dt=([0-9.]+)s elapsed=([0-9.]+)s\]"
)
TC = re.compile(
    r"trust-constr: optimality ([-0-9.eE+naninf]+) constr_violation ([-0-9.eE+]+) barrier ([-0-9.eE+]+) tr_radius ([-0-9.eE+]+)"
)


def parse(path):
    legs = []
    cur = None
    for line in open(path, errors="replace"):
        line = ANSI.sub("", line)
        m = IT.search(line)
        if m:
            it = int(m.group(1))
            if it == 0:
                cur = []
                legs.append(cur)
            cur.append(
                dict(
                    it=it,
                    loss=float(m.group(2)),
                    dt=float(m.group(3)),
                    el=float(m.group(4)),
                )
            )
            continue
        m = TC.search(line)
        if m and cur:
            cur[-1].update(
                opt=float(m.group(1)),
                cv=float(m.group(2)),
                mu=float(m.group(3)),
                tr=float(m.group(4)),
            )
    return legs


def summarize(leg, final=None):
    if final is None:
        final = min(r["loss"] for r in leg)
    n = len(leg) - 1
    rej = 0
    for a, b in zip(leg[:-1], leg[1:]):
        b["rej"] = (b["loss"] == a["loss"]) and (
            "tr" in b and b["tr"] < a.get("tr", 1e99)
        )
        rej += b["rej"]
    T = leg[-1]["el"]
    out = dict(
        n_iter=n,
        wall_s=T,
        start=leg[0]["loss"],
        last=leg[-1]["loss"],
        final_ref=final,
        n_rejected=rej,
        t_rejected=sum(r["dt"] for r in leg[1:] if r.get("rej")),
    )
    # barrier stages
    if "mu" in leg[0]:
        stages = []
        for r in leg[1:]:
            if not stages or stages[-1]["mu"] != r["mu"]:
                stages.append(dict(mu=r["mu"], n=0, t=0.0, rej=0, loss_in=r["loss"]))
            s = stages[-1]
            s["n"] += 1
            s["t"] += r["dt"]
            s["rej"] += r.get("rej", 0)
            s["loss_out"] = r["loss"]
        out["stages"] = stages
        first_cut = next((r for r in leg[1:] if r["mu"] < leg[0]["mu"]), None)
        out["mu0_iters"] = (first_cut["it"] - 1) if first_cut else n
        out["mu0_wall_s"] = (first_cut["el"] - first_cut["dt"]) if first_cut else T
    # q-to-go bands
    bands = [(10, 1e99), (1, 10), (0.1, 1), (0.01, 0.1), (0.001, 0.01), (0, 0.001)]
    bres = []
    for lo, hi in bands:
        sel = [r for r in leg[1:] if lo <= 2 * (r["loss"] - final) < hi]
        bres.append(
            dict(q_to_go=f"[{lo},{hi})", n=len(sel), t=sum(r["dt"] for r in sel))
        )
    out["bands"] = bres
    reach = {}
    for thr in (10, 1, 0.1, 0.01, 1e-3):
        r = next((r for r in leg if 2 * (r["loss"] - final) < thr), None)
        reach[f"q<{thr}"] = dict(it=r["it"], el=r["el"]) if r else None
    out["reach"] = reach
    dts = sorted((r["dt"] for r in leg[1:]), reverse=True)
    out["dt_median"] = dts[len(dts) // 2] if dts else None
    out["dt_max"] = dts[0] if dts else None
    out["n_dt_ge_600"] = sum(d >= 600 for d in dts)
    out["t_dt_ge_600"] = sum(d for d in dts if d >= 600)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("logs", nargs="+")
    ap.add_argument("--json")
    ap.add_argument(
        "--final",
        type=float,
        nargs="*",
        help="reference final loss per leg (default min seen)",
    )
    a = ap.parse_args()
    res = {}
    for p in a.logs:
        legs = parse(p)
        for i, leg in enumerate(legs):
            key = f"{p.split('/')[-1]}#leg{i}"
            res[key] = dict(summary=summarize(leg), iters=leg)
            s = res[key]["summary"]
            print(
                key,
                {k: v for k, v in s.items() if k not in ("stages", "bands", "reach")},
            )
            for st in s.get("stages", []):
                print(
                    f"   mu={st['mu']:.3g} n={st['n']} rej={st['rej']} t={st['t']:.0f}s loss {st['loss_in']:.6f}->{st['loss_out']:.6f}"
                )
            print(
                "   bands:", [(b["q_to_go"], b["n"], round(b["t"])) for b in s["bands"]]
            )
            print("   reach:", s["reach"])
    if a.json:
        json.dump(res, open(a.json, "w"), indent=1)
