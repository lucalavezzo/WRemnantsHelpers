"""Per-op probe: which ops on the straight-through path survive nested
ForwardAccumulator under @tf.function? Maps exactly what needs a comparison-free
rewrite for inline full-K.
"""

import numpy as np
import tensorflow as tf

DT = tf.float64
bT = tf.constant(np.linspace(0.01, 4.0, 32), dtype=DT)
c = lambda x: tf.constant(x, dtype=DT)


def op_smooth(lam):  # baseline: smooth ops only
    x = lam[0] * bT + lam[1] * bT**2
    return tf.reduce_sum(tf.tanh(x) * tf.exp(-x))


def op_maximum(lam):  # tf.maximum on a λ-dependent tensor
    x = lam[0] * bT + lam[1] * bT**2
    return tf.reduce_sum(tf.maximum(x, c(0.05)))


def op_softplus(lam):  # tf.math.softplus (may use internal where)
    x = lam[0] * bT + lam[1] * bT**2
    return tf.reduce_sum(tf.math.softplus(x))


def op_floor(lam):  # exact mimic of param_model.py:1050
    r = 1.0 + lam[0] * bT
    s = c(1e-3)
    rr = tf.maximum(s * tf.math.softplus(r / s), c(1e-300))
    return tf.reduce_sum(rr)


def op_gather_where(lam):  # mimic btgrid_integrate.py:100 (where on const idx)
    idx = tf.constant([0, 2, -1, 1, -1], dtype=tf.int32)
    idx_safe = tf.where(tf.equal(idx, -1), tf.constant(0, dtype=tf.int32), idx)
    vals = lam[0] * tf.constant([1.0, 2.0, 3.0, 4.0, 5.0], dtype=DT)
    return tf.reduce_sum(tf.gather(vals, idx_safe))


def hess00(fn, lam):  # d²fn/dλ0² via forward-over-forward
    e0 = tf.one_hot(0, int(lam.shape[0]), dtype=DT)
    with tf.autodiff.ForwardAccumulator(lam, e0) as a2:
        with tf.autodiff.ForwardAccumulator(lam, e0) as a1:
            v = fn(lam)
        d1 = a1.jvp(v)
    return a2.jvp(d1)


lam0 = tf.constant([0.4, 0.4, 0.15], dtype=DT)
for name, fn in [
    ("smooth", op_smooth),
    ("maximum", op_maximum),
    ("softplus", op_softplus),
    ("floor(1050)", op_floor),
    ("gather+where(100)", op_gather_where),
]:
    try:
        he = float(hess00(fn, lam0))  # eager
    except Exception as e:
        print(f"{name:20s} EAGER FAIL: {type(e).__name__}: {str(e)[:80]}")
        continue
    try:
        ht = float(tf.function(lambda l: hess00(fn, l))(lam0))
        tag = (
            "PASS" if abs(ht - he) < 1e-6 * (abs(he) + 1) else f"MISMATCH {ht} vs {he}"
        )
        print(f"{name:20s} tf.function: {tag}")
    except Exception as e:
        print(f"{name:20s} tf.function FAIL: {type(e).__name__}: {str(e)[:90]}")
