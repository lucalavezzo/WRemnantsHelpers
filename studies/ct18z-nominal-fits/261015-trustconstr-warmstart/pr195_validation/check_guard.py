#!/usr/bin/env python3
"""PR #195 check: with the scipy-internals guard failing, a warm-hinted fit is
exactly the cold fit (bit-identical x and iteration count)."""
import sys

import numpy as np

sys.path.insert(0, "/work/submit/lavezzo/rabbit-tc-warmstart")
from rabbit.constraints import warm_start  # noqa: E402
from tests.test_trust_constr_warmstart import _cold, _fitter, _setup  # noqa: E402
import tempfile  # noqa: E402

with tempfile.TemporaryDirectory() as tmp:
    fn, names, cons, _ = _setup(tmp)
    cold = _cold(fn, cons)
    nobs = cold.indata.data_obs.numpy() * 1.3  # a moved minimum

    def run(warm):
        f = _fitter(fn, "trust-constr", cons=cons())
        f.set_nobs(nobs)
        f.x.assign(cold.x.numpy())
        f.minimize(warm_start=warm)
        return f.x.numpy(), f.minimizer_status()

    xa, sa = run(False)
    warm_start.scipy_supports_slack_override = lambda: (False, "simulated scipy change")
    xb, sb = run(True)
    ok = (
        np.array_equal(xa, xb)
        and sa["nit"] == sb["nit"]
        and "warm_start_legs" not in sb
    )
    print(
        f"[check] guard failing -> cold fit bit-identical: {'PASS' if ok else 'FAIL'} :: "
        f"max|dx| {np.max(np.abs(xa - xb)):.3g}, nit {sa['nit']} vs {sb['nit']}"
    )
