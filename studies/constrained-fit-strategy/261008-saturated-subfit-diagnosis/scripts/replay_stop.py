#!/usr/bin/env python3
"""Replay rabbit's --earlyStopping N --stallRelTol tol (--maxRestarts 0) rule over the logged sub-fit loss sequences.

Rule (rabbit/callbacks.py FitterCallback, rabbit 2a59246): at the callback of iteration k (history L_0..L_{k-1}),
if k > N and L_k >= L_{k-N} - tol*|L_{k-N}| -> stop; the kept iterate is the last accepted one (loss L_{k-1}).
The budget is quoted as an absolute dNLL = tol * 337.5 (the loss is ~337-376 throughout).
Reports, per (N, dNLL budget): the iteration and wall time at which it fires, and q_err = 2 (L_kept - L_final).
Writes replay_stop.json; prints a markdown table.
"""
import json
import os

T = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cb = json.load(open(f"{T}/cost_breakdown.json"))
res = {}
for name in ["SATB8", "SATB8SA"]:
    rows = cb[name]["rows"]
    L = [r["loss"] for r in rows]
    dt = [r["dt"] for r in rows]
    final = min(L)
    tot = sum(dt)
    res[name] = []
    for N in [3, 5, 8, 10, 15, 20]:
        for budget in [1e-1, 3e-2, 1e-2, 3e-3, 1e-3]:
            tol = budget / 337.5
            fire = None
            for k in range(len(L)):
                if k > N and L[k] >= L[k - N] - tol * abs(L[k - N]):
                    fire = k
                    break
            if fire is None:
                res[name].append(
                    dict(N=N, budget=budget, fires=None, q_err=0.0, wall_frac=1.0)
                )
                continue
            kept = L[fire - 1]
            wall = sum(dt[: fire + 1])
            res[name].append(
                dict(
                    N=N,
                    budget=budget,
                    fires=fire,
                    q_err=2 * (kept - final),
                    wall_s=wall,
                    wall_frac=wall / tot,
                )
            )
json.dump(res, open(f"{T}/replay_stop.json", "w"), indent=1)
for name, rr in res.items():
    print(f"\n### {name} (total {cb[name]['wall_s']:.0f} s)")
    print("| N | dNLL budget | fires at it. | q error | wall s | wall frac |")
    print("|---|---|---|---|---|---|")
    for r in rr:
        if r["fires"] is None:
            print(f"| {r['N']} | {r['budget']:g} | never | 0 | - | 1 |")
        else:
            print(
                f"| {r['N']} | {r['budget']:g} | {r['fires']} | {r['q_err']:.3g} | {r['wall_s']:.0f} | {r['wall_frac']:.2f} |"
            )
