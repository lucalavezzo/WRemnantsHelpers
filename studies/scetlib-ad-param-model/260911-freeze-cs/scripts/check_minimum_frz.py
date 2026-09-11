#!/usr/bin/env python3
"""Is the frozen-CS postfit a genuine MINIMUM, on the FLOATING block?

Same test as ../260910-blinding/scripts/check_minimum.py (a negative eigenvalue
of cov = H^-1 is a direction still going down, which EDM cannot distinguish from
a minimum), with one correction that the frozen arm needs.

rabbit initialises `self.cov` to diag(var_prefit) and `edmval_cov()` scatters
back only the FLOATING block (fitter.py:1016-1037), so the frozen parameters'
rows and columns in the written covariance are the PREFIT ones -- variance 1.0
in theta, zero off-diagonal. They are positive, so they cannot fake a minimum,
but they are not part of the fit's Hessian and they inflate kappa's numerator.
So the spectrum is taken on the submatrix with them removed.

Prints eigenvalues and counts only. No parameter value, no alphaS.

usage: check_minimum_frz.py <frozen-name,...> <fitresult.hdf5> [...]
"""
import os
import shutil
import sys

import numpy as np

SCRATCH = "/tmp/frzcs_read"
from rabbit import io_tools  # noqa: E402


def local_copy(path):
    os.makedirs(SCRATCH, exist_ok=True)
    dst = os.path.join(SCRATCH, os.path.basename(path))
    if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(path):
        shutil.copy2(path, dst)
    return dst


frozen = [s for s in sys.argv[1].split(",") if s]
for path in sys.argv[2:]:
    tag = path.rsplit("fitresults_", 1)[-1].replace(".hdf5", "")
    try:
        res = io_tools.get_fitresult(local_copy(path))
        hc = res["cov"].get()
        labels = [str(x) for x in hc.axes[0]]
        cov = np.asarray(hc.values(), dtype=np.float64)
    except Exception as exc:  # noqa: BLE001
        print(f"{tag:14s}  cov unavailable: {type(exc).__name__}: {exc}")
        continue
    for label, keep in (
        ("full", np.ones(len(labels), dtype=bool)),
        ("floating only", np.array([l not in frozen for l in labels])),
    ):
        if label == "floating only" and keep.all():
            print(f"{'':14s}  (no frozen name matched; 'full' is the answer)")
            continue
        C = cov[np.ix_(keep, keep)]
        n = C.shape[0]
        ev = np.linalg.eigvalsh(0.5 * (C + C.T))
        floor = float(np.finfo(np.float64).eps * n * np.max(np.abs(ev)))
        n_neg_raw = int((ev < 0).sum())
        n_neg = int((ev < -floor).sum())
        print(
            f"{tag:14s} [{label:13s}] n={n}  min(eig)={ev[0]:+.4e}  "
            f"max(eig)={ev[-1]:.4e}  kappa={ev[-1] / ev[0]:.2e}"
        )
        print(
            f"{'':14s} {'':15s} negative: {n_neg_raw} raw, {n_neg} beyond the "
            f"{floor:.2e} floor  ->  "
            f"{'MINIMUM' if n_neg == 0 else 'NOT a minimum (saddle)'}"
        )
        try:
            np.linalg.cholesky(C)
            print(f"{'':14s} {'':15s} Cholesky: OK (positive definite)")
        except np.linalg.LinAlgError:
            print(f"{'':14s} {'':15s} Cholesky: FAILED")
    # what the frozen rows actually hold, so the caveat is evidenced not asserted
    for f in frozen:
        if f in labels:
            i = labels.index(f)
            off = np.abs(np.delete(cov[i], i)).max()
            print(
                f"{'':14s}  frozen {f:12s}: cov[i,i] = {cov[i, i]:.6g}, "
                f"max|off-diagonal| = {off:.3g}  (prefit row, not a measurement)"
            )
    print()
print("CHECKMIN_DONE")
