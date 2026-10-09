#!/usr/bin/env python3
"""Loss and KKT trace of a trust-constr fit, from its log (the logged loss is the penalty-free NLL; NLL is not
blinded). References (penalty-free NLL minus XWSTIFF's, from compare.json / compare.py): XWSTIFF 0, CMR1B +0.4300,
XL4ZSTIFF +0.9549. A trace is not a parameter plot, so plain matplotlib (no histogram to hand to wums).
"""
import argparse
import os
import re
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_output import save_plot  # noqa: E402

TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XW = 371.3283536451264
REFS = {
    "XWSTIFF (W)": 0.0,
    "CMR1B (λ4_ν<0, walled)": 0.43,
    "XL4ZSTIFF (λ4_ν held 0)": 0.9549,
}
p = argparse.ArgumentParser()
p.add_argument("pf", nargs="?", default="TCC1")
args = p.parse_args()
it, loss, opt, cv, mu = [], [], [], [], []
cur = None
for line in open(f"{TASK}/logs/{args.pf}.log", errors="replace"):
    line = re.sub(r"\x1b\[[0-9;]*m", "", line)
    m = re.search(r"Iteration (\d+): loss ([-\d.eE+]+)", line)
    if m:
        cur = (int(m.group(1)), float(m.group(2)))
        continue
    m = re.search(
        r"optimality ([\d.eE+-]+) constr_violation ([\d.eE+-]+) barrier ([\d.eE+-]+)",
        line,
    )
    if m and cur:
        it.append(cur[0]), loss.append(cur[1] - XW)
        opt.append(float(m.group(1))), cv.append(float(m.group(2))), mu.append(
            float(m.group(3))
        )
fig, (a1, a2) = plt.subplots(
    2, 1, figsize=(8, 7), sharex=True, gridspec_kw=dict(height_ratios=[3, 2])
)
a1.plot(
    it, loss, "k.-", lw=0.8, ms=3, label=f"{args.pf} (trust-constr, hard constraints)"
)
for (lab, v), c in zip(REFS.items(), ["C0", "C3", "C2"]):
    a1.axhline(v, color=c, ls="--", lw=1, label=lab)
a1.set_yscale("symlog", linthresh=1e-2)
a1.set_ylim(-0.01, max(loss + [1.0]) * 2)
a1.set_ylabel("NLL − NLL(XWSTIFF), penalty-free")
a1.legend(fontsize=8)
a1.set_title(
    "XWSTIFF configuration (card A, λ4_ν free, no lattice); start = C", fontsize=9
)
a2.plot(it, opt, label="optimality (KKT residual)")
a2.plot(it, [max(c, 1e-12) for c in cv], label="constr_violation (floored 1e-12)")
a2.plot(it, mu, label="barrier μ")
a2.set_yscale("log")
a2.set_xlabel("iteration")
a2.legend(fontsize=8)
save_plot(outdir=TASK, basename=f"trace_{args.pf}", fig=fig, args=args, meta_info=None)
print(f"{len(it)} iterations plotted")
