#!/usr/bin/env python3
"""Is each postfit a genuine MINIMUM, or a saddle?

EDM measures local stationarity -- how much loss a quadratic model says is left
-- but a SADDLE is stationary too. What separates them is the sign of the
curvature, so eigendecompose the postfit covariance (= H^-1). A negative
eigenvalue of cov is a negative eigenvalue of H, i.e. a direction the fit could
still go DOWN: not a minimum.

Prints eigenvalues and counts only. No parameter value, no alphaS.
"""
import sys

import numpy as np

sys.path.insert(0, "/work/submit/lavezzo/alphaS/rabbit-blinding")
from rabbit import io_tools  # noqa: E402

for path in sys.argv[1:]:
    tag = path.rsplit("fitresults_", 1)[-1].replace(".hdf5", "")
    try:
        res = io_tools.get_fitresult(path)
        cov = np.asarray(res["cov"].get().values(), dtype=np.float64)
    except Exception as exc:  # noqa: BLE001
        print(f"{tag:12s}  cov unavailable: {type(exc).__name__}: {exc}")
        continue
    n = cov.shape[0]
    ev = np.linalg.eigvalsh(0.5 * (cov + cov.T))
    # roundoff floor: eigenvalues below this are numerically zero, not negative
    floor = float(np.finfo(np.float64).eps * n * np.max(np.abs(ev)))
    n_neg_raw = int((ev < 0).sum())
    n_neg = int((ev < -floor).sum())
    print(f"{tag:12s}  n={n}  min(eig)={ev[0]:+.4e}  max(eig)={ev[-1]:.4e}")
    print(
        f"{'':12s}  negative: {n_neg_raw} raw, {n_neg} beyond the {floor:.2e} floor"
        f"  ->  {'MINIMUM' if n_neg == 0 else 'NOT a minimum (saddle)'}"
    )
    try:
        np.linalg.cholesky(cov)
        print(f"{'':12s}  Cholesky on cov: OK (positive definite)")
    except np.linalg.LinAlgError:
        print(f"{'':12s}  Cholesky on cov: FAILED (not positive definite)")
    print()
