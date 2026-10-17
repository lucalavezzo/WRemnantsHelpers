#!/usr/bin/env python3
"""Aggregate a toy_grid json over seeds: per variant, the iterations by start class
(median [max]), the number of runs that did not reach the reference minimum
(|f_end - f*| > 1e-5; a start whose own cold reference hit maxiter is excluded), and
the worst loss rise above the start for the restarts from the minimum itself."""
import json
import sys
from collections import defaultdict

import numpy as np

d = json.load(open(sys.argv[1]))
R = d["results"]
cls = lambda s: (
    "at_min"
    if s == "at_min"
    else (
        "on_face"
        if s == "on_face"  # noqa: E731
        else "infeas" if s.startswith("infeas") else "0.1sig" if "0.1s" in s else "1sig"
    )
)
groups = defaultdict(list)
for r in R:
    groups[(r["keep"], r["slack"], r["mu0"], r.get("tol0"))].append(r)
classes = ["at_min", "on_face", "infeas", "0.1sig", "1sig"]
print(
    f"{'keep':5s} {'slack':6s} {'mu0':6s} {'tol0':5s} | "
    + " | ".join(f"{c:>12s}" for c in classes)
    + " | fail | exc(min/face)"
)
for k, rs in groups.items():
    cells, fail = [], 0
    for c in classes:
        sel = [r for r in rs if cls(r["start"]) == c and r["cold_nit"] < 2000]
        nits = [r["nit"] for r in sel]
        cells.append(f"{int(np.median(nits)):4d} [{max(nits):4d}]")
        fail += sum(abs(r["f_end_minus_fstar"]) > 1e-5 for r in sel)
    exc = max(r["excursion"] for r in rs if cls(r["start"]) in ("at_min", "on_face"))
    print(
        f"{k[0]:5s} {k[1]:6s} {str(k[2]):6s} {str(k[3]):5s} | "
        + " | ".join(f"{c:>12s}" for c in cells)
        + f" | {fail:4d} | {exc:.0e}"
    )
