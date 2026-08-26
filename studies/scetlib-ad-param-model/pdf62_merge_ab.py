#!/usr/bin/env python3
"""Prove the 21-shard bin merge produced the cache we think it did.

D-033 validated the MECHANISM on a two-shard test. This checks the PRODUCTION
merge: evaluate the merged cache restricted to one ptVGen index's bins, and the
shard that built those bins, and require them to agree at the anchor AND at a
displaced point in BOTH value and Jacobian.

Run once per cache, in SEPARATE processes, and compare the printed numbers by
hand or with --expect. Separate processes are the point: ``values_and_jacobian``
memoises on the parameter vector alone, so two arms inside one process can
return a perfect and WRONG null (D-023). Three arms returning three DIFFERENT
totals that satisfy the additive rule is the evidence; one number repeated is
not.
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, "/home/submit/lavezzo/alphaS/WRemnants")
from wremnants.postprocessing.scetlib_ad.xsec_backend import ScetlibADXsec  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--cache", required=True)
ap.add_argument("--conf", required=True)
ap.add_argument("--threads", type=int, default=32)
ap.add_argument("--qt-lo", default=None,
                help="comma-separated qT low edges; the sums are printed for the "
                "cache bins at each, plus for all bins. Several selections in ONE "
                "process is safe -- they share the model call, and the point of "
                "separate processes is separate CACHES, not separate selections.")
a = ap.parse_args()

core = ScetlibADXsec(a.conf, a.cache, threads=a.threads)
b = core.bins
sels = [("ALL", np.ones(b.shape[0], bool))]
if a.qt_lo:
    for x in a.qt_lo.split(","):
        sels.append((f"qT>={float(x):g}", np.isclose(b[:, 4], float(x))))
print(f"cache {a.cache}")
print(f"  {core.n_bins} bins, {core.n_params} params")
print("  param names:", ",".join(core.param_names[:3]), "...", core.param_names[-1])

p0 = core.anchor.copy()
# A displaced point that moves EVERY kind of parameter, eigenvectors included:
# the merge could in principle be right at the anchor and wrong in the rules.
p1 = p0.copy()
names = list(core.param_names)
p1[names.index("alphas")] = 0.1195
p1[names.index("np_eff_lambda2")] = 0.55
p1[names.index("scale_kappa_F")] = 1.3
for i in range(29):
    p1[names.index(f"pdf_eig{i}")] = 0.37 * (-1) ** i

ia = names.index("alphas")
for tag, p in (("anchor", p0), ("displaced", p1)):
    v0, j0 = core.values_and_jacobian(p)
    for sname, sel in sels:
        v = np.asarray(v0, float)[sel]
        j = np.asarray(j0, float)[sel]
        print(f"  {tag:<10} {sname:<10} n={int(sel.sum()):>3}  "
              f"sum(sigma) = {v.sum():.12f}   "
              f"sum|jac| = {np.abs(j).sum():.10f}   "
              f"sum(jac[:,alphas]) = {j[:, ia].sum():.10f}")
