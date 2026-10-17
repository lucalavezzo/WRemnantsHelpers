#!/usr/bin/env python3
"""Print toy_grid.json as a table: per start, 'nit/status' with '!' when the run
did NOT reach the reference minimum (|f_end - f*| > 1e-5), plus the max loss rise
above the start loss."""
import json
import sys

d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "toy_grid.json"))
R = d["results"]
starts = list(dict.fromkeys(r["start"] for r in R))
print("cold:", d["info"])
print(
    "f0-f*:",
    {
        s: round(next(r["f0_minus_fstar"] for r in R if r["start"] == s), 4)
        for s in starts
    },
)
print(
    "cold nit:", {s: next(r["cold_nit"] for r in R if r["start"] == s) for s in starts}
)
print(
    f"{'keep':6s} {'slack':6s} {'mu0':5s} | "
    + " | ".join(f"{s[:11]:>13s}" for s in starts)
)
keys = list(dict.fromkeys((r["keep"], r["slack"], r["mu0"]) for r in R))
for k in keys:
    row = [
        next(r for r in R if (r["keep"], r["slack"], r["mu0"]) == k and r["start"] == s)
        for s in starts
    ]
    cells = []
    for r in row:
        bad = "!" if abs(r["f_end_minus_fstar"]) > 1e-5 else " "
        cells.append(f"{r['nit']:4d}/{r['status']}{bad} {r['excursion']:.0e}")
    print(
        f"{k[0]:6s} {k[1]:6s} {str(k[2]):5s} | "
        + " | ".join(f"{c:>13s}" for c in cells)
    )
