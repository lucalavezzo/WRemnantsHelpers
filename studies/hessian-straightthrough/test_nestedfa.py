"""Fast probe: can a nested ForwardAccumulator (forward-over-forward, what K needs)
trace through the real fold functions UNDER @tf.function? Reproduces the rabbit
crash site (gamma_nu_NP_tf -> _safe_div) without loading the btgrid, so we can
iterate in ~30 s instead of ~10 min.

PASS  => nested FA works under tf.function with the patched fold -> run full-K in rabbit.
FAIL  => nested FA is fundamentally incompatible with tf.function -> different strategy.
"""

import numpy as np
import tensorflow as tf
from wremnants.postprocessing.scetlib_np import btgrid_tf as fz

DT = tf.float64
bT = tf.constant(np.linspace(0.01, 4.0, 64), dtype=DT)
Yv = tf.constant(0.3, dtype=DT)
c = lambda x: tf.constant(x, dtype=DT)


def scalar(lam):
    # lam = [lambda2, lambda4, lambda2_nu] (the floating ones), through BOTH fold fns
    Feff = fz.F_eff_tf(
        Yv,
        bT,
        lambda_inf=c(1.0),
        lambda2=lam[0],
        lambda4=lam[1],
        lambda6=c(0.0),
        delta_lambda2=c(0.0),
        np_model="tanh_2",
    )
    gnu = fz.gamma_nu_NP_tf(
        bT,
        lambda_inf_nu=c(2.0),
        lambda2_nu=lam[2],
        lambda4_nu=c(0.0),
        np_model_nu="tanh_2",
    )
    return tf.reduce_sum(Feff * tf.exp(gnu))


def hess_diag(lam):
    n = int(lam.shape[0])
    out = []
    for i in range(n):
        ti = tf.one_hot(i, n, dtype=DT)
        with tf.autodiff.ForwardAccumulator(lam, ti) as a2:  # forward-over-forward
            with tf.autodiff.ForwardAccumulator(lam, ti) as a1:
                v = scalar(lam)
            d1 = a1.jvp(v)
        out.append(a2.jvp(d1))
    return tf.stack(out)


lam0 = tf.constant([0.4, 0.4, 0.15], dtype=DT)

He = hess_diag(lam0).numpy()  # eager = ground truth
print("eager nested-FA hess diag :", He, flush=True)

try:
    Ht = tf.function(hess_diag)(lam0).numpy()  # the actual question
    print("tf.function nested-FA    :", Ht, flush=True)
    print(f"max|tf.function - eager| : {np.max(np.abs(Ht - He)):.3e}", flush=True)
    print("RESULT: PASS — nested FA traces under tf.function with the patched fold")
except Exception as e:
    print(f"tf.function nested-FA FAILED: {type(e).__name__}: {str(e)[:160]}")
    print(
        "RESULT: FAIL — nested FA incompatible with tf.function even without comparisons"
    )
