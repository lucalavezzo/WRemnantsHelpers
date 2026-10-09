"""Toy (rabbit's test tensor): trust-constr from an INFEASIBLE start, with mu0 = 0.1 (default) and 1e-3.
Checks it neither errors nor returns x0 unchanged, and lands on the face of a binding bound.
"""

import sys
import tempfile

import numpy as np

sys.path.insert(0, "/work/submit/lavezzo/rabbit-trustconstr")
from tests.test_trust_constr import (
    LinearBound,
    _fitter,
    _free_fit,
    _names,
)  # noqa: E402
from tests.test_sparse_fit import make_test_tensor  # noqa: E402

with tempfile.TemporaryDirectory() as tmp:
    fn = make_test_tensor(tmp)
    free = _free_fit(fn)
    i = _names(free).index("sig")
    xf = free.x.numpy()
    lb = xf[i] + 0.1  # binding: the free optimum violates it by 0.1
    for mu0 in (None, 1e-3):
        kw = {} if mu0 is None else dict(minimizerInitialBarrier=mu0)
        tc = _fitter(fn, "trust-constr", regs=[LinearBound({"sig": 1.0}, lb)], **kw)
        x0 = xf.copy()
        x0[i] = lb - 1e-3  # infeasible start, just past the face (like C's lambda4_nu)
        tc.x.assign(x0)
        tc.minimize()
        st = tc.minimizer_status()
        print(
            f"mu0={mu0}: start c-lb={x0[i]-lb:+.1e} -> final c-lb={tc.x.numpy()[i]-lb:+.2e} "
            f"status={st.get('status')} nit={st.get('nit')} constr_violation={st['constr_violation']:.1e} "
            f"barrier={st.get('barrier_parameter')} multiplier={st['multipliers'][0]:+.4g} "
            f"moved={not np.allclose(tc.x.numpy(), x0)}"
        )
