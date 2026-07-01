"""Toy validation of Route B: one-pass @tf.custom_gradient.

Same structure as toy_straightthrough.py (few lambda -> big [Ng,M] slab -> reduce
-> R -> ratio -> loss with many nuisances), but the lambda->ratio map is wrapped
in a nested custom_gradient so that:
  * the FIRST derivative (the fit) is a single cheap reverse pass through the fold
    and NEVER computes K,
  * the SECOND derivative (rabbit's Hessian jacobian) uses the compact K only,
    so the [Ng,M] slab never enters the differentiated graph.

We assert: exact gradient, exact Hessian (vs the naive oracle), and that K is
computed 0 times for a gradient-only call and only a few times for the Hessian.
"""

import numpy as np
import tensorflow as tf

tf.keras.utils.set_random_seed(0)
DT = tf.float64
rng = np.random.default_rng(0)

NLAM, M, NG, NRECO, NTHETA = 4, 300, 200, 60, 120
NPAR = NLAM + NTHETA

A = tf.constant(rng.normal(size=(NG, M)) ** 2 + 0.1, dtype=DT)
bgrid = tf.constant(np.linspace(0.0, 4.0, M), dtype=DT)
w = tf.constant(np.full(M, np.linspace(0.0, 4.0, M)[1]), dtype=DT)
Ymix = tf.constant(rng.normal(size=(NG,)), dtype=DT)
R = tf.constant(rng.uniform(0.0, 1.0, size=(NRECO, NG)), dtype=DT)
s = tf.constant(rng.uniform(5.0, 20.0, size=(NRECO,)), dtype=DT)
syst = tf.constant(rng.normal(scale=0.05, size=(NRECO, NTHETA)), dtype=DT)
LAM0 = tf.constant([0.4, 0.4, 0.15, 0.0], dtype=DT)

CALLS = {"fold": 0, "J": 0, "K": 0}


def sigma_grid(lam):
    CALLS["fold"] += 1
    l2, l4, lnu, dl2 = lam[0], lam[1], lam[2], lam[3]
    l2Y = l2 + dl2 * Ymix[:, None] ** 2
    arg = (l2Y + l4 * bgrid[None, :] ** 2) * bgrid[None, :]
    Feff = tf.tanh(arg)
    gnu = tf.tanh(lnu * bgrid**2)
    integrand = A * Feff * tf.exp(-0.3 * gnu)[None, :]  # [Ng, M] slab
    return tf.reduce_sum(integrand * w[None, :], axis=1)


def ratio_exact(lam):
    reco = tf.linalg.matvec(R, sigma_grid(lam))
    reco0 = tf.linalg.matvec(R, sigma_grid(LAM0))
    return reco / reco0


def compact_J(lam):
    CALLS["J"] += 1
    cols = []
    for i in range(NLAM):
        t = tf.one_hot(i, NLAM, dtype=DT)
        with tf.autodiff.ForwardAccumulator(lam, t) as acc:
            r = ratio_exact(lam)
        cols.append(acc.jvp(r))
    return tf.stack(cols, axis=1)  # [NRECO, NLAM]


def compact_K(lam):
    CALLS["K"] += 1
    n = NLAM
    rows = []
    for i in range(n):
        ti = tf.one_hot(i, n, dtype=DT)
        cols = []
        for j in range(n):
            tj = tf.one_hot(j, n, dtype=DT)
            with tf.autodiff.ForwardAccumulator(lam, tj) as acc_j:
                with tf.autodiff.ForwardAccumulator(lam, ti) as acc_i:
                    r = ratio_exact(lam)
                di = acc_i.jvp(r)
            cols.append(acc_j.jvp(di))
        rows.append(tf.stack(cols, axis=1))
    return tf.stack(rows, axis=2)  # [NRECO, i, j]


@tf.custom_gradient
def ratio_cg(lam):
    val = ratio_exact(lam)  # exact forward value

    def grad_fn(dy):
        # dy is an EXPLICIT input to vjp (not captured) so the outer tape can
        # differentiate through its x-dependence -> recovers the Gauss-Newton
        # term J^T A J and the full cross block, not just the K (residual) term.
        @tf.custom_gradient
        def vjp(lam2, dy2):
            with tf.GradientTape() as tp:
                tp.watch(lam2)
                r = ratio_exact(lam2)
            g = tp.gradient(
                r, lam2, output_gradients=dy2
            )  # [NLAM] = dy2 @ J (1 reverse pass)

            def grad_grad_fn(dg):
                J = compact_J(lam2)  # [NRECO, NLAM]; Hessian path only
                K = compact_K(lam2)  # [NRECO, i, j]; Hessian path only
                dlam = tf.einsum("rik,r,i->k", K, dy2, dg)  # d/dlam2 [ dg . (dy2@J) ]
                ddy = tf.linalg.matvec(J, dg)  # d/ddy2  [ dg . (dy2@J) ] = J @ dg
                return dlam, ddy

            return g, grad_grad_fn

        return vjp(lam, dy)

    return val, grad_fn


def make_loss(ratio_fn, n_obs):
    def loss(x):
        lam, theta = x[:NLAM], x[NLAM:]
        mu = ratio_fn(lam) * s * tf.exp(tf.linalg.matvec(syst, theta))
        return tf.reduce_sum(mu - n_obs * tf.math.log(mu)) + 0.5 * tf.reduce_sum(
            theta**2
        )

    return loss


def grad_only(loss_fn, x):
    with tf.GradientTape() as t1:
        L = loss_fn(x)
    return t1.gradient(L, x)


def grad_hess(loss_fn, x):
    with tf.GradientTape() as t2:
        with tf.GradientTape() as t1:
            L = loss_fn(x)
        g = t1.gradient(L, x)
    return g, t2.jacobian(g, x)


def main():
    x0 = np.concatenate([[0.55, 0.30, 0.18, 0.05], rng.normal(scale=0.1, size=NTHETA)])
    x = tf.Variable(x0, dtype=DT)
    lam_truth = tf.constant([0.4, 0.4, 0.15, 0.0], dtype=DT)
    mu_truth = ratio_exact(lam_truth) * s
    n_obs = tf.constant(mu_truth.numpy(), dtype=DT)

    loss_exact = make_loss(ratio_exact, n_obs)
    loss_cg = make_loss(ratio_cg, n_obs)

    # ---- fit-path cost probe: a gradient-only call must NOT compute K ----
    CALLS["K"] = 0
    _ = grad_only(loss_cg, x)
    k_after_grad = CALLS["K"]
    print(
        f"[A] K computations during a GRADIENT-only (fit) call = {k_after_grad}  (want 0)"
    )

    # ---- gradient exactness ----
    g_e = grad_only(loss_exact, x).numpy()
    g_c = grad_only(loss_cg, x).numpy()
    print(
        f"[B] max |grad_cg - grad_exact|             = {np.max(np.abs(g_c - g_e)):.3e}  (want <1e-9)"
    )

    # ---- Hessian exactness (vs naive oracle) ----
    _, H_e = grad_hess(loss_exact, x)
    CALLS["K"] = 0
    _, H_c = grad_hess(loss_cg, x)
    k_after_hess = CALLS["K"]
    He, Hc = H_e.numpy(), H_c.numpy()
    absdiff = np.max(np.abs(Hc - He))
    reldiff = absdiff / np.max(np.abs(He))
    print(
        f"[C] K computations during the HESSIAN call = {k_after_hess}  (want small, not ~{NPAR})"
    )
    print(f"[D] max |Hess_cg - Hess_exact|             = {absdiff:.3e}")
    print(f"    relative                               = {reldiff:.3e}  (want <1e-8)")
    ll = np.max(np.abs((Hc - He)[:NLAM, :NLAM]))
    lt = np.max(np.abs((Hc - He)[:NLAM, NLAM:]))
    tt = np.max(np.abs((Hc - He)[NLAM:, NLAM:]))
    print(f"    block diffs: H(l,l)={ll:.2e}  H(l,th)={lt:.2e}  H(th,th)={tt:.2e}")

    ok = k_after_grad == 0 and np.max(np.abs(g_c - g_e)) < 1e-9 and reldiff < 1e-8
    print()
    print(
        "RESULT:",
        (
            "PASS -- one-pass custom_gradient: cheap exact fit + exact Hessian"
            if ok
            else "FAIL"
        ),
    )


if __name__ == "__main__":
    main()
