#!/usr/bin/env python3
"""What the analytic muF evolution COSTS: a PAIRED, interleaved timing A/B.

The first pass timed all the off reps then all the on reps and could not tell 0%
from 15%: the login node carries other jobs, so the two blocks saw different
load. Here each round times off then on back to back and the statistic is the
per-round RATIO, which cancels any drift slower than one round. Same process,
same cache, same threads, warm (a discarded round 0).
"""
import argparse
import os
import sys
import time

import numpy as np

WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
sys.path.insert(0, WREM)
sys.path.insert(0, os.path.join(WREM, "scripts", "rabbit", "scetlib_ad"))

ap = argparse.ArgumentParser()
ap.add_argument("--cache", required=True)
ap.add_argument("--conf", required=True)
ap.add_argument("--threads", type=int, default=16)
ap.add_argument("--rounds", type=int, default=6)
a = ap.parse_args()

import scetlib_qT  # noqa: E402
from wremnants.postprocessing.scetlib_ad.xsec_backend import ScetlibADXsec  # noqa: E402

assert scetlib_qT.DrellYan.muf_analytic() == 1, "not the default-on build"
core = ScetlibADXsec(a.conf, a.cache, threads=a.threads)
p = core.anchor.copy()


def arm(mode):
    scetlib_qT.DrellYan.set_muf_analytic(mode)
    core.tf_fn._cache_key = None
    core.tf_fn._hess_cache_key = None


rows = []
for r in range(a.rounds + 1):
    t = {}
    for tag, mode in (("off", 0), ("on", 1)):
        arm(mode)
        t0 = time.perf_counter(); core.values_and_jacobian(p)
        t1 = time.perf_counter(); core.hessian(p); t2 = time.perf_counter()
        t[tag] = (t1 - t0, t2 - t1)
    if r:
        rows.append(t)
        print(f"round {r}: v+J off {t['off'][0]:.3f} on {t['on'][0]:.3f} "
              f"(x{t['on'][0]/t['off'][0]:.3f})   H off {t['off'][1]:.2f} "
              f"on {t['on'][1]:.2f} (x{t['on'][1]/t['off'][1]:.3f})", flush=True)

for k, nm in ((0, "value+jacobian"), (1, "hessian")):
    off = np.array([x["off"][k] for x in rows])
    on = np.array([x["on"][k] for x in rows])
    rat = on / off
    print(f"\n{nm}: off median {np.median(off):.4f} s   on median "
          f"{np.median(on):.4f} s")
    print(f"  paired ratio on/off: median {np.median(rat):.4f}   "
          f"min {rat.min():.4f}   max {rat.max():.4f}   "
          f"mean {rat.mean():.4f} +- {rat.std(ddof=1)/np.sqrt(len(rat)):.4f} (sem)")
scetlib_qT.DrellYan.set_muf_analytic(1)
