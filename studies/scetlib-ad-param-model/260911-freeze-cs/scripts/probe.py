#!/usr/bin/env python3
"""Pre-flight probe for the frozen-CS fit.

Answers, before any fit is launched:
  1. which parameters the model actually registers on THIS card+cache, and which
     are already held by params.DEFAULT_FROZEN (the brief asks specifically
     about lambda_inf_nu / b0_over_bmax_nu);
  2. what prior each fitted parameter carries -- the brief's correction says the
     arms are NOT "NP free", so this has to be established before anything is
     interpreted;
  3. the CS anchors, i.e. the values --freezeParameters will hold at;
  4. rho(lambda4, lambda2_nu) and rho(lambda4, lambda4_nu) in OUR OWN postfit
     covariance (the note quotes -0.996 / -0.953; verify, do not repeat).

Nothing here prints alphaS's central value.
"""
import os
import shutil
import sys

import numpy as np

CEPH = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
CARD = f"{CEPH}/study_scratch/260910-anchor-verify/card_none.hdf5"
CACHE = f"{CEPH}/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full"
PLAIN = f"{CEPH}/260910_blinding_final/fitresults_DATABLIND.hdf5"
SCRATCH = "/tmp/frzcs_read"


def local_copy(path):
    os.makedirs(SCRATCH, exist_ok=True)
    dst = os.path.join(SCRATCH, os.path.basename(path))
    if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(path):
        shutil.copy2(path, dst)
    return dst


from rabbit import inputdata, io_tools  # noqa: E402

from wremnants.postprocessing.scetlib_ad import np_damping_wall as wall  # noqa: E402
from wremnants.postprocessing.scetlib_ad import params as adp  # noqa: E402

print("=" * 78)
print("1. params.DEFAULT_FROZEN / FREE_PARAMS, as the module declares them")
print("=" * 78)
print(f"  DEFAULT_FROZEN = {list(adp.DEFAULT_FROZEN)}")
print(f"  FREE_PARAMS    = {sorted(adp.FREE_PARAMS)}")
print("  REPARAM widths for the NP block:")
for n in (
    "lambda2",
    "lambda4",
    "lambda6",
    "delta_lambda2",
    "lambda2_nu",
    "lambda4_nu",
    "lambda6_nu",
    "alphaS",
):
    print(f"    {n:16s} {adp.reparam(n)}   prior_sigma={adp.prior_sigma(n)}")

print()
print("=" * 78)
print("2. what the model registers on this card + cache")
print("=" * 78)
indata = inputdata.FitInputData(CARD)
from wremnants.postprocessing.scetlib_ad import SCETlibADParamModel  # noqa: E402

pm = SCETlibADParamModel(
    indata,
    cache=f"{CACHE}/cache.npz",
    conf=f"{CACHE}/cache.conf",
    threads=8,
    jitCompile="off",
)
names = [p.decode() if isinstance(p, bytes) else str(p) for p in pm.params]
print(f"  npoi={pm.npoi} npou={pm.npou} total={len(names)}")
print(f"  fitted: {names}")
avail = list(pm.rabbit_names)
print(f"  available in cache ({len(avail)}): {avail}")
held = [n for n in avail if n not in names]
print(f"  HELD (not fitted): {held}")
ps = getattr(pm, "prior_sigmas", None)
if ps is None:
    print("  prior_sigmas: NOT DECLARED -> everything free")
else:
    ps = np.asarray(ps, dtype=float)
    free = [n for n, s in zip(names, ps) if not np.isfinite(s) or s <= 0]
    print(f"  prior_sigmas declared; FREE (no prior): {free}")
    print(
        f"  constrained at sigma=1 in theta: {sum(1 for s in ps if np.isfinite(s) and s > 0)} of {len(names)}"
    )

print()
print("=" * 78)
print("3. CS anchors -- the values --freezeParameters will hold at")
print("=" * 78)
inp = wall.resolve_wall_inputs(indata)
for n in inp["names"]:
    spec = inp["specs"].get(n)
    fitted = "FITTED" if n in names else "held"
    print(
        f"  {n:18s} anchor={float(inp['anchors'][n]):+12.6g}   {fitted:6s}  spec={spec}"
    )

print()
print("=" * 78)
print("4. rho in OUR postfit covariance (plain DATABLIND arm)")
print("=" * 78)
res = io_tools.get_fitresult(local_copy(PLAIN))
print(f"  fitresult keys: {sorted(res.keys())}")
covkey = None
for k in ("cov", "covariance", "cov_matrix"):
    if k in res:
        covkey = k
        break
if covkey is None:
    print("  NO covariance object in the fitresult; keys above.")
else:
    hcov = res[covkey].get()
    labels = [str(x) for x in hcov.axes[0]]
    C = hcov.values()
    idx = {n: i for i, n in enumerate(labels)}
    want = ["alphaS", "lambda2", "lambda4", "delta_lambda2", "lambda2_nu", "lambda4_nu"]
    want = [w for w in want if w in idx]
    d = np.sqrt(np.diag(C))
    print("  correlation matrix over the NP block + alphaS:")
    print("      " + "".join(w.rjust(15) for w in want))
    for a in want:
        row = "".join(
            format(C[idx[a], idx[b]] / (d[idx[a]] * d[idx[b]]), "+.4f").rjust(15)
            for b in want
        )
        print(f"  {a:16s}{row}")
    print()
    for a, b in (
        ("lambda4", "lambda2_nu"),
        ("lambda4", "lambda4_nu"),
        ("lambda2_nu", "lambda4_nu"),
        ("alphaS", "lambda2_nu"),
        ("alphaS", "lambda4_nu"),
        ("alphaS", "lambda4"),
    ):
        if a in idx and b in idx:
            r = C[idx[a], idx[b]] / (d[idx[a]] * d[idx[b]])
            print(f"  rho({a}, {b}) = {r:+.4f}")
print("PROBE_DONE")
