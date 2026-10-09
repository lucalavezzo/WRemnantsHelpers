#!/usr/bin/env python3
"""Classify every sub-fit iteration from the log alone (reads cost_breakdown.json).

  rejected      loss unchanged (trust radius x1/4, trlib hot-start: no new HVPs for the NEXT solve)
  ladder        accepted, gain / previous accepted gain in [1.6, 2.5]: the radius doubling back after a collapse
                (scipy grows the radius x2 only for a boundary step with rho > 0.75; in the linear regime gain ~ radius)
  polish        accepted, gain ratio < 0.3: Newton-like convergence in the stiff subspace after a big step
  big           accepted, gain ratio > 2.5: a step that suddenly gets much further (a deep Krylov solve, typically)
  other         accepted, ratio in [0.3, 1.6)
Also: runs of consecutive rejections (radius collapse by 4^n) and the ladder length that follows each.
Writes step_classes.json, prints a table.
"""
import json
import os

import numpy as np

T = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cb = json.load(open(f"{T}/cost_breakdown.json"))
out = {}
for name in ["SATB8", "SATB8SA", "SATC2", "SATP"]:
    rows = cb[name]["rows"]
    L = np.array([r["loss"] for r in rows])
    dt = np.array([r["dt"] for r in rows])
    acc = np.array([r["acc"] for r in rows])
    start = 376.6751
    gains = -np.diff(np.r_[start, L])
    cls = []
    prev = None
    for k in range(len(L)):
        if not acc[k]:
            cls.append("rejected")
            continue
        if prev is None or prev <= 0:
            cls.append("other")
        else:
            r = gains[k] / prev
            cls.append(
                "ladder"
                if 1.6 <= r <= 2.5
                else "polish" if r < 0.3 else "big" if r > 2.5 else "other"
            )
        prev = gains[k]
    cls = np.array(cls)
    # the wall time of a class = the dt of the iterations of that class (dt_k includes the solve that PRODUCED step k)
    summ = {
        c: dict(
            n=int((cls == c).sum()),
            wall_s=float(dt[cls == c].sum()),
            frac=float(dt[cls == c].sum() / dt.sum()),
        )
        for c in ["rejected", "ladder", "polish", "big", "other"]
    }
    # rejection runs
    runs = []
    k = 0
    while k < len(cls):
        if cls[k] == "rejected":
            j = k
            while j + 1 < len(cls) and cls[j + 1] == "rejected":
                j += 1
            # ladder after
            m = j + 1
            while m + 1 < len(cls) and cls[m + 1] == "ladder":
                m += 1
            runs.append(
                dict(
                    start=int(k),
                    n_rej=int(j - k + 1),
                    ladder_after=int(m - j - 1),
                    wall_rej=float(dt[k : j + 1].sum()),
                    wall_ladder=float(dt[j + 1 : m + 1].sum()),
                )
            )
            k = j + 1
        else:
            k += 1
    # expensive iterations
    heavy = [
        dict(it=int(k), dt=float(dt[k]), cls=str(cls[k]), gain=float(gains[k]))
        for k in np.nonzero(dt >= 300)[0]
    ]
    out[name] = dict(
        classes=summ,
        rejection_runs=runs,
        heavy=heavy,
        cls=cls.tolist(),
        heavy_wall_s=float(dt[dt >= 300].sum()),
        heavy_frac=float(dt[dt >= 300].sum() / dt.sum()),
    )
    print(
        f"\n### {name}: total {dt.sum():.0f} s; iterations with dt>=300 s: {len(heavy)}, "
        f"{out[name]['heavy_wall_s']:.0f} s ({out[name]['heavy_frac']:.2f})"
    )
    for c, v in summ.items():
        print(f"  {c:9s} n={v['n']:4d} wall={v['wall_s']:7.0f} s ({v['frac']:.2f})")
    print(
        "  rejection runs (start it, n_rej, ladder steps after):",
        [(r["start"], r["n_rej"], r["ladder_after"]) for r in runs],
    )
    print(
        "  heavy:",
        [(h["it"], round(h["dt"]), h["cls"], f"{h['gain']:.2g}") for h in heavy],
    )
json.dump(out, open(f"{T}/step_classes.json", "w"), indent=1)
