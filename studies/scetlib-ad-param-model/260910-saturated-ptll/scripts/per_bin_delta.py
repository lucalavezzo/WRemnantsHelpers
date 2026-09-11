#!/usr/bin/env python3
"""Walled-minus-unwalled per-bin contribution to the projected ptll statistic,
from the npz written by projected_deviance.py.  No container needed."""
import sys

import numpy as np

d = np.load(sys.argv[1] if len(sys.argv) > 1 else "projected_deviance.npz")
qu = d["unwalled (DATABLIND)_q_bin"]
qw = d["walled tau=5 (DATAWALL5)_q_bin"]
e = d["unwalled (DATABLIND)_edges"]
dq = qw - qu
print(f"{'bin':>4} {'ptll range':>14} {'q_unw':>8} {'q_wall':>8} {'delta':>8}")
for i in np.argsort(-np.abs(dq))[:8]:
    print(
        f"{i:4d} [{e[i]:5.1f},{e[i + 1]:5.1f}) {qu[i]:8.3f} {qw[i]:8.3f} {dq[i]:+8.3f}"
    )
lo = e[:-1] < 10
print(f"\nsum delta q, ptll < 10 GeV : {dq[lo].sum():+.3f}")
print(f"sum delta q, ptll > 10 GeV : {dq[~lo].sum():+.3f}")
print(f"total                      : {dq.sum():+.3f}")
