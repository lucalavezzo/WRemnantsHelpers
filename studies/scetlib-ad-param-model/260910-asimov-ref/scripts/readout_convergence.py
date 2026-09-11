#!/usr/bin/env python3
"""CONVERGENCE FIRST: is this fit a minimum, before anyone reads a sigma.

usage: readout_convergence.py <fitresult.hdf5> <fit.log>

Reports, in this order: exit status, the minimiser's own verdict, EDM, the
postfit Hessian's eigenvalue spectrum (negative count + extremes), and the
Cholesky statement. Only then is a sigma worth looking at.

WHY THE SPECTRUM IS COMPUTED FROM `cov` AND NOT FROM THE LOG. The 260908-fit-770
arms got their eigenvalue spectrum from a harness that MONKEY-PATCHES
`Fitter.edmval_cov` to call `eigh` on the Hessian on the way in. This arm runs
plain `rabbit_fit.py` -- deliberately, so that it matches the DATABLIND arm
command for command -- so no spectrum is in the log. It is recoverable anyway:
rabbit saves `cov`, which is H^-1 on the floating block, so
  eig(cov) = 1 / eig(H),
sign-for-sign (inversion preserves sign), and a negative eigenvalue of cov is a
negative eigenvalue of H. The smallest eigenvalue of H is 1/max(eig(cov)).

THE CHOLESKY STATEMENT IS FREE. rabbit's `edmval_cov` Cholesky-factorises the
Hessian to get `cov` at all; if that factorisation had failed it would have
raised `LinAlgError: potrf return info = k` and written NO covariance. So "a
covariance exists and the process exited 0" IS the statement that rabbit's
Cholesky on the Hessian succeeded. It is re-verified here independently on cov.

ROUNDOFF FLOOR, per 260908-fit-770/summarize.py: `eigh` on a float64 matrix
resolves eigenvalues to about eps*||M||, so any |lambda| below 100*eps*||M|| is
indistinguishable from exactly zero. Counting those as negative directions
would call a converged fit a saddle -- that is what mislabelled TOY770NP.
"""
import re
import sys

import numpy as np

sys.path.insert(0, "/home/submit/lavezzo/alphaS/WRemnants/rabbit")
from rabbit import io_tools  # noqa: E402

FR, LOG = sys.argv[1], sys.argv[2]
ANSI = re.compile(r"\x1b\[[0-9;]*m")
txt = ANSI.sub("", open(LOG, errors="replace").read())

print("=" * 72)
print("1. EXIT STATUS AND THE MINIMISER'S OWN VERDICT")
print("=" * 72)
m = re.search(r"^\tExit status: (\d+)", txt, re.M)
print(f"  /usr/bin/time Exit status : {m.group(1) if m else 'NOT FOUND'}")
for key in ("message", "success", "status", "fun", "nit", "nfev", "njev", "nhev"):
    mm = re.search(rf"^\s*{key}: (.*)$", txt, re.M)
    if mm:
        print(f"  {key:25s}: {mm.group(1).strip()}")
else_ = "  (no scipy OptimizeResult in the log)"
if "message:" not in txt:
    print(else_)
    print("  For an Asimov fit this is EXPECTED: rabbit runs ifit = -1, so the")
    print("  minimiser is never invoked -- there is no OptimizeResult to print.")

print()
print("=" * 72)
print("2. EDM")
print("=" * 72)
res, meta = io_tools.get_fitresult(FR, meta=True)
edm = float(res["edmval"])
print(f"  edmval (from fitresult)   : {edm:.6e}")
mm = re.search(r"edmval: ([0-9eE.+-]+)", txt)
print(f"  edmval (from log)         : {mm.group(1) if mm else 'not in log'}")
print("  EDM = 0.5 g^T H^-1 g, i.e. the loss still on the table.")
print("  Converged references in this study sit at 1e-9 .. 1e-27; the gate")
print("  used by 260908-fit-770/summarize.py is EDM < 1e-5.")

print()
print("=" * 72)
print("3. POSTFIT HESSIAN SPECTRUM (via cov = H^-1)")
print("=" * 72)
cov = res["cov"].get()
C = np.asarray(cov.values(), dtype=np.float64)
print(f"  cov shape                 : {C.shape}")
Cs = 0.5 * (C + C.T)
asym = np.max(np.abs(C - C.T))
print(f"  max |cov - cov^T|         : {asym:.3e}")
ev = np.linalg.eigvalsh(Cs)
nrm = np.max(np.abs(ev))
floor = 100 * np.finfo(np.float64).eps * nrm
n_neg_raw = int((ev < 0).sum())
n_neg_sig = int((ev < -floor).sum())
print(f"  ||cov||                   : {nrm:.6e}")
print(f"  roundoff floor (100*eps)  : {floor:.3e}")
print(f"  negative eigenvalues      : {n_neg_raw} of {len(ev)}  (as computed)")
print(f"  negative ABOVE the floor  : {n_neg_sig} of {len(ev)}  <== THE NUMBER")
print(f"  10 smallest eig(cov)      : {np.array2string(ev[:10], precision=4)}")
print(f"  10 largest  eig(cov)      : {np.array2string(ev[-10:], precision=8)}")
print("  implied Hessian extremes (eig(H) = 1/eig(cov)):")
print(f"    smallest eig(H) = 1/max(eig(cov)) : {1.0 / ev[-1]:+.8f}")
print(f"    largest   eig(H) = 1/min(eig(cov)) : {1.0 / ev[0]:+.6e}")
print("  A smallest eig(H) of ~+1 is the EXPECTED floor, not a coincidence:")
print("  a nuisance the data cannot constrain still has unit curvature from")
print("  its own Gaussian prior, so +1 is the least-constrained direction.")

print()
print("=" * 72)
print("4. CHOLESKY")
print("=" * 72)
print("  rabbit's Fitter.edmval_cov Cholesky-factorises the Hessian to produce")
print("  cov; a failure raises LinAlgError (potrf) and writes NO covariance.")
print(f"  -> a covariance of shape {C.shape} EXISTS in the fitresult, so")
print("     rabbit's Cholesky on the postfit Hessian SUCCEEDED.")
try:
    np.linalg.cholesky(Cs)
    print("  independent re-check: np.linalg.cholesky(cov) SUCCEEDED")
    print("     -> cov positive definite -> H positive definite -> a MINIMUM.")
except np.linalg.LinAlgError as e:
    print(f"  independent re-check: cholesky(cov) FAILED: {e}")

print()
print("=" * 72)
print("5. GOODNESS OF FIT AND TIMINGS (from the log)")
print("=" * 72)
for blk in ("Saturated chi2", "Linear chi2"):
    i = txt.find(blk)
    if i >= 0:
        print("  " + blk + ":")
        for ln in txt[i : i + 260].splitlines()[1:4]:
            s = ln.split("rabbit_fit.py:")[-1].strip()
            if s:
                print("     " + s)
print(f"  nllvalreduced             : {float(res['nllvalreduced']):.6f}")
print(f"  ndfsat                    : {int(res['ndfsat'])}")
for pat in (
    r"(\d+\.?\d*) seconds total time",
    r"(\d+\.?\d*) seconds initialization time",
    r"(\d+\.?\d*) seconds for fit",
    r"(\d+\.?\d*) seconds for postfit",
):
    mm = re.search(pat, txt)
    if mm:
        print(
            f"  {pat.split('(')[0].strip() or 'time'}{mm.group(1)} s"
            f"  [{pat.split(') ')[-1]}]"
        )
mm = re.search(r"^\tMaximum resident set size \(kbytes\): (\d+)", txt, re.M)
if mm:
    print(f"  peak RSS                  : {int(mm.group(1)) / 1048576:.1f} GiB")
mm = re.search(r"^\tElapsed \(wall clock\) time.*?: (.*)$", txt, re.M)
if mm:
    print(f"  wall clock                : {mm.group(1).strip()}")
