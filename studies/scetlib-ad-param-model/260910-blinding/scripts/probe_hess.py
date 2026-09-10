#!/usr/bin/env python3
"""Why is the toy model's POI Hessian element zero?"""
import sys
import numpy as np
import tensorflow as tf

sys.path.insert(0, "/home/submit/lavezzo/alphaS/WRemnants/rabbit")
sys.path.insert(0, "/home/submit/lavezzo/alphaS/WRemnants/rabbit/tests")
from rabbit import fitter as fitter_mod  # noqa: E402
from rabbit.inputdata import FitInputData  # noqa: E402
from rabbit.param_models.param_model import ParamModel  # noqa: E402
from test_external_term import make_options  # noqa: E402

TENSOR = sys.argv[1]
START = 0.3


class ToyModel(ParamModel):
    def __init__(self, indata):
        super().__init__(indata)
        self.npoi = 1
        self.npou = 0
        self.params = np.array([b"alphaS"])
        self.xparamdefault = tf.constant([START], dtype=indata.dtype)
        self.is_linear = True
        self.allowNegativeParam = True

    def compute(self, param, full=False):
        nproc = self.indata.nproc
        col = tf.reshape(1.0 + 0.1 * param[0], [1, 1])
        return tf.concat([col, tf.ones([1, nproc - 1], dtype=col.dtype)], axis=1)


indata = FitInputData(TENSOR)
print(f"nproc = {indata.nproc}  nsyst = {indata.nsyst}")
print(
    f"procs = {[p.decode() if isinstance(p, bytes) else p for p in indata.procs][:6]}"
)
f = fitter_mod.Fitter(indata, ToyModel(indata), make_options(), do_blinding=False)
f.defaultassign()

loss, grad, hess = f.loss_val_grad_hess()
h = hess.numpy()
g = grad.numpy()
print(f"hess shape = {h.shape}   grad shape = {g.shape}")
print(f"H[0,0] = {h[0,0]!r}   grad[0] = {g[0]!r}")
print(f"H diag [first 6] = {np.diag(h)[:6]}")
print(f"nonzero H diag entries: {int((np.abs(np.diag(h)) > 0).sum())} / {h.shape[0]}")

# Does the POI move the loss at all?  Finite difference on the PHYSICAL value.
print("\nfinite difference in the POI:")
base = float(f.x[0].numpy())
for d in (0.0, 0.1, 1.0, 10.0):
    f.x[0:1].assign(tf.constant([base + d], dtype=f.x.dtype))
    l = float(f.loss_val_grad_hess()[0].numpy())
    print(f"  x0 = {base + d:8.3f}   loss = {l!r}")
f.x[0:1].assign(tf.constant([base], dtype=f.x.dtype))

# Which processes are 'signal'?  A POI scaling a process with no yield in the
# unmasked channels would give zero curvature.
print(f"\nsignals mask = {getattr(indata, 'signals', None)}")
norm = indata.norm if hasattr(indata, "norm") else None
if norm is not None:
    n = np.asarray(norm)
    print(
        f"norm shape {n.shape}; per-process sums = {n.sum(axis=tuple(range(n.ndim - 1)))[:6]}"
    )
