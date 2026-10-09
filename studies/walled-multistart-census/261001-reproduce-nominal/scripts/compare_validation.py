#!/usr/bin/env python3
"""Compare the step-5 --noFit evaluations against the stored NOMSTIFF numbers. alphaS is not read."""
import os, sys
from rabbit import io_tools

OUT = sys.argv[1]
REF = {
    "VALNOM": ("NOMSTIFF nllvalreduced", 376.6146329237086),
    "VALIT0": (
        "NOMSTIFF Iteration 0 loss (at the LATL4ZY35WALLWARM seed)",
        376.69103432608273,
    ),
}
ok = True
for pf, (what, ref) in REF.items():
    p = os.path.join(OUT, f"fitresults_{pf}.hdf5")
    if not os.path.exists(p):
        print(f"{pf}: MISSING {p}")
        ok = False
        continue
    v = float(io_tools.get_fitresult(p)["nllvalreduced"])
    d = v - ref
    good = abs(d) < 1e-10
    ok &= good
    print(
        f"{pf}: {v!r} vs {what} {ref!r}: diff {d:+.3e} -> {'PASS' if good else 'FAIL'} (tol 1e-10)"
    )
print("OVERALL:", "PASS" if ok else "FAIL")
