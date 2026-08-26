#!/usr/bin/env python3
"""Turn the 1 Hz thread sample into the member-barrier diagnostic."""
import sys

import numpy as np

t, ntot, nrun, cores = [], [], [], []
for line in open(sys.argv[1]).read().splitlines()[1:]:
    f = line.split(",")
    if len(f) < 4 or not f[3]:
        continue
    t.append(float(f[0])); ntot.append(int(f[1]))
    nrun.append(int(f[2])); cores.append(float(f[3]))
t = np.array(t); nrun = np.array(nrun); cores = np.array(cores)
lo = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
hi = float(sys.argv[3]) if len(sys.argv) > 3 else t[-1] + 1
m = (t >= lo) & (t <= hi)
c = cores[m]; tt = t[m]
print(f"window [{lo:.0f}, {hi:.0f}] s   {m.sum()} samples")
print(f"cores: mean {c.mean():.1f}  median {np.median(c):.1f}  "
      f"p10 {np.percentile(c,10):.1f}  p90 {np.percentile(c,90):.1f}  max {c.max():.1f}")
nt = int(sys.argv[4]) if len(sys.argv) > 4 else 48
print(f"utilisation vs --threads={nt}: mean {c.mean()/nt*100:.0f}%")
for thr in (0.9, 0.75, 0.5, 0.25):
    print(f"  fraction of time above {thr*100:3.0f}% of the pool: "
          f"{(c > thr*nt).mean()*100:5.1f}%   below: {(c <= thr*nt).mean()*100:5.1f}%")
# wasted core-seconds relative to a perfectly packed pool
span = tt[-1] - tt[0]
print(f"span {span:.0f} s;  core-s used {c.sum():.0f};  "
      f"core-s available {nt*span:.0f};  idle {100*(1 - c.sum()/(nt*span)):.1f}%")
# crude sawtooth detection: count downward crossings of half the pool
below = c < 0.5 * nt
runs, cur = [], 0
for b in below:
    if b:
        cur += 1
    elif cur:
        runs.append(cur); cur = 0
if cur:
    runs.append(cur)
print(f"episodes below 50% of the pool: {len(runs)}, "
      f"lengths {sorted(runs, reverse=True)[:20]}")
