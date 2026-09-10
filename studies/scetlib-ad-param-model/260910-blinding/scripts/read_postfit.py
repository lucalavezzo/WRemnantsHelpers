#!/usr/bin/env python3
"""Read a blinded fitresult: sigma(alphaS), and whether anything blew up.

POLICY: alphaS's CENTRAL value is blinded and must NOT be printed. sigma IS
safe -- with additive blinding it is exact, which is the whole point. The 46
POUs are never blinded by rabbit, so their values are printed as-is.
"""
import sys

import numpy as np

sys.path.insert(0, "/home/submit/lavezzo/alphaS/WRemnants/rabbit")
from rabbit import io_tools  # noqa: E402

fr = sys.argv[1]
res, meta = io_tools.get_fitresult(fr, meta=True)

h = res["parms"].get()
names = [str(n) for n in h.axes[0]]
vals = h.values()
errs = np.sqrt(h.variances())

WIDTH = 0.002  # alphaS: theta -> Delta(alpha_s) per unit theta

# The MODEL's parameters only: alphaS, the 8 NP lambdas, 10 TNPs, the profile
# scales and the 29 pdfEig. The 3673 card nuisances are printed separately as a
# summary, since listing them all buries the point.
MODEL_PREFIXES = (
    "alphaS",
    "lambda",
    "delta_lambda",
    "b0_over_bmax",
    "resumTNP_",
    "resumScale",
    "resumTransition",
    "pdfEig",
)
model = [n for n in names if n.startswith(MODEL_PREFIXES)]
print(f"MODEL PARAMETERS ({len(model)} of {len(names)} total)")
print(f"{'parameter':24s} {'value':>12s} {'sigma':>12s}")
print("-" * 50)
for n in model:
    i = names.index(n)
    if n == "alphaS":
        print(f"{'alphaS (theta)':24s} {'[BLINDED]':>12s} {errs[i]:12.6f}")
        print(f"{'  -> sigma(alpha_s)':24s} {'':>12s} {errs[i] * WIDTH:12.6f}")
    else:
        flag = ""
        if abs(vals[i]) > 3:
            flag = "  <== |pull| > 3"
        elif abs(vals[i]) > 2:
            flag = "  <== |pull| > 2"
        print(f"{n:24s} {vals[i]:12.4f} {errs[i]:12.4f}{flag}")

# Card nuisances: summary rather than 3673 lines.
card = [n for n in names if not n.startswith(MODEL_PREFIXES)]
ci = [names.index(n) for n in card]
cv = np.array([vals[i] for i in ci])
print()
print(
    f"CARD NUISANCES ({len(card)}): max |pull| = {np.max(np.abs(cv)):.3f}"
    f"  ({card[int(np.argmax(np.abs(cv)))]})"
)
for thr in (5, 4, 3, 2):
    n_over = int((np.abs(cv) > thr).sum())
    print(f"  |pull| > {thr}: {n_over}")
worst = np.argsort(-np.abs(cv))[:8]
print("  worst 8:")
for k in worst:
    print(f"    {card[k]:34s} {cv[k]:+8.4f}")
