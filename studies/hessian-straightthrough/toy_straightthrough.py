"""Toy validation of the straight-through compact-derivative Hessian trick.

Mirrors the SCETlib NP ParamModel structure WITHOUT the heavy fold:
  - nlam (<=8) lambda parameters,
  - a big [Ng, M] intermediate (grid x bT) that depends NONLINEARLY on lambda
    and is reduced over M -> [Ng] (Simpson-like),
  - a linear response R: [Ng] -> [Nreco]  (the rebin+R fold),
  - a Poisson NLL over Nreco bins whose signal is scaled by ratio(lambda) and
    by many nuisances theta (the ~3750 nuisances).

Goal: show that replacing the exact fold with
    ratio_st = stop_gradient(val) + J . d + 0.5 d^T K d ,   d = lam - stop_gradient(lam)
(J, K = compact forward-mode derivatives of ratio wrt the <= nlam lambda)
reproduces the EXACT loss gradient and Hessian, while the differentiated graph
no longer carries the [Ng, M] slab (so the Hessian does not tile it over all
params -- the fix that avoids the 32.8 TB OOM).

Run (in the isolated checkout, inside the container):
    singularity exec --cleanenv $IMG /opt/venv/bin/python3 hessian_dev/toy_straightthrough.py
"""

import numpy as np
import tensorflow as tf

tf.keras.utils.set_random_seed(0)
DT = tf.float64
rng = np.random.default_rng(0)

# ---- toy dimensions (small so the FULL naive Hessian fits, as the oracle) ----
NLAM = 4  # floating lambda
M = 300  # "bT" points  -> the axis that blows up in the real model
NG = 200  # "grid" bins
NRECO = 60  # reco bins
NTHETA = 120  # nuisances (stand in for the ~3750)
NPAR = NLAM + NTHETA

# ---- fixed toy constants (the lambda-independent pieces) ----
A = tf.constant(
    rng.normal(size=(NG, M)) ** 2 + 0.1, dtype=DT
)  # kernel*I_pert-like, [Ng, M]
bgrid = tf.constant(np.linspace(0.0, 4.0, M), dtype=DT)  # "bT" grid
w = tf.constant(
    (np.linspace(0.0, 4.0, M)[1]) * np.ones(M), dtype=DT
)  # Simpson-like weights (uniform toy)
Ymix = tf.constant(rng.normal(size=(NG,)), dtype=DT)  # per-grid "Y" entering F_eff
R = tf.constant(
    rng.uniform(0.0, 1.0, size=(NRECO, NG)), dtype=DT
)  # response matrix [Nreco, Ng]
s = tf.constant(rng.uniform(5.0, 20.0, size=(NRECO,)), dtype=DT)  # signal nominal
syst = tf.constant(
    rng.normal(scale=0.05, size=(NRECO, NTHETA)), dtype=DT
)  # nuisance response log-coeffs

LAM0 = tf.constant([0.4, 0.4, 0.15, 0.0], dtype=DT)  # "lambda_central"-like


def sigma_grid(lam):
    """The expensive fold: builds the [Ng, M] integrand nonlinearly in lam, reduces over M -> [Ng]."""
    l2, l4, lnu, dl2 = lam[0], lam[1], lam[2], lam[3]
    # F_eff-like, depends on (Y, bT) and lambda nonlinearly (tanh) -> [Ng, M]
    l2Y = l2 + dl2 * Ymix[:, None] ** 2  # [Ng,1]
    arg = (l2Y + l4 * bgrid[None, :] ** 2) * bgrid[None, :]  # [Ng, M]
    Feff = tf.tanh(arg)  # [Ng, M]
    # gamma_nu-like, depends on lnu, [M]
    gnu = tf.tanh(lnu * bgrid**2)  # [M]
    integrand = A * Feff * tf.exp(-0.3 * gnu)[None, :]  # [Ng, M]  <-- the big slab
    return tf.reduce_sum(integrand * w[None, :], axis=1)  # [Ng]


def ratio_exact(lam):
    """lambda -> ratio[Nreco], the differentiable map (sigma_grid folded through R, normalized)."""
    sig = sigma_grid(lam)  # [Ng]
    reco = tf.linalg.matvec(R, sig)  # [Nreco]
    reco0 = tf.linalg.matvec(R, sigma_grid(LAM0))
    return reco / reco0


# ---- compact forward-mode derivatives of ratio wrt the NLAM lambda ----
def compact_J(lam):
    cols = []
    for i in range(NLAM):
        t = tf.one_hot(i, NLAM, dtype=DT)
        with tf.autodiff.ForwardAccumulator(lam, t) as acc:
            r = ratio_exact(lam)
        cols.append(acc.jvp(r))  # [Nreco] = dratio/dlam_i
    return tf.stack(cols, axis=1)  # [Nreco, NLAM]


def compact_K(lam):
    out = np.empty((NLAM, NLAM), dtype=object)
    for i in range(NLAM):
        ti = tf.one_hot(i, NLAM, dtype=DT)
        for j in range(NLAM):
            tj = tf.one_hot(j, NLAM, dtype=DT)
            with tf.autodiff.ForwardAccumulator(lam, tj) as acc_j:
                with tf.autodiff.ForwardAccumulator(lam, ti) as acc_i:
                    r = ratio_exact(lam)
                di = acc_i.jvp(r)  # [Nreco]
            out[i, j] = acc_j.jvp(di)  # [Nreco] = d2ratio/dlam_i dlam_j
    # assemble [Nreco, NLAM, NLAM]
    K = tf.stack(
        [tf.stack([out[i, j] for j in range(NLAM)], axis=1) for i in range(NLAM)],
        axis=2,
    )
    return K


def ratio_straightthrough(lam):
    """Exact value, but autodiff sees only the compact quadratic in lam (no [Ng,M] slab)."""
    val = ratio_exact(lam)
    J = tf.stop_gradient(compact_J(lam))  # [Nreco, NLAM]
    K = tf.stop_gradient(compact_K(lam))  # [Nreco, NLAM, NLAM]
    d = lam - tf.stop_gradient(lam)  # 0 value, unit gradient
    return (
        tf.stop_gradient(val)
        + tf.linalg.matvec(J, d)
        + 0.5 * tf.einsum("rij,i,j->r", K, d, d)
    )


def make_loss(ratio_fn, n_obs):
    def loss(x):
        lam = x[:NLAM]
        theta = x[NLAM:]
        ratio = ratio_fn(lam)  # [Nreco]
        mu = ratio * s * tf.exp(tf.linalg.matvec(syst, theta))  # [Nreco]
        nll = tf.reduce_sum(mu - n_obs * tf.math.log(mu))
        return nll + 0.5 * tf.reduce_sum(theta**2)  # Gaussian constraints

    return loss


def grad_hess(loss_fn, x):
    with tf.GradientTape() as t2:
        with tf.GradientTape() as t1:
            L = loss_fn(x)
        g = t1.gradient(L, x)
    H = t2.jacobian(g, x)
    return L, g, H


def main():
    # evaluation point: lambda off-truth, theta small (mimics a postfit-ish point)
    x0 = np.concatenate([[0.55, 0.30, 0.18, 0.05], rng.normal(scale=0.1, size=NTHETA)])
    x = tf.Variable(x0, dtype=DT)

    # Asimov observed counts at the SAME x (so residuals ~0 -> tests GN limit too,
    # but we keep generic by using a *different* truth so residuals are nonzero and K matters)
    lam_truth = tf.constant([0.4, 0.4, 0.15, 0.0], dtype=DT)
    theta_truth = tf.zeros(NTHETA, dtype=DT)
    mu_truth = ratio_exact(lam_truth) * s * tf.exp(tf.linalg.matvec(syst, theta_truth))
    n_obs = tf.constant(
        mu_truth.numpy(), dtype=DT
    )  # nonzero residuals at x0 -> K contributes

    # ---- 1. forward value identical ----
    v_exact = ratio_exact(x[:NLAM]).numpy()
    v_st = ratio_straightthrough(x[:NLAM]).numpy()
    print(
        f"[1] max |ratio_st - ratio_exact|          = {np.max(np.abs(v_st - v_exact)):.3e}  (want ~0)"
    )

    # ---- 2. compact J vs finite difference ----
    lam = x[:NLAM]
    J = compact_J(lam).numpy()
    eps = 1e-6
    Jfd = np.zeros_like(J)
    for i in range(NLAM):
        dp = lam.numpy().copy()
        dp[i] += eps
        dm = lam.numpy().copy()
        dm[i] -= eps
        Jfd[:, i] = (
            ratio_exact(tf.constant(dp, dtype=DT)).numpy()
            - ratio_exact(tf.constant(dm, dtype=DT)).numpy()
        ) / (2 * eps)
    print(
        f"[2] max |J_fwdmode - J_finitediff|        = {np.max(np.abs(J - Jfd)):.3e}  (want <1e-6)"
    )

    # ---- 3. loss gradient: straight-through vs exact ----
    loss_exact = make_loss(ratio_exact, n_obs)
    loss_st = make_loss(ratio_straightthrough, n_obs)
    Le, ge, He = grad_hess(loss_exact, x)
    Ls, gs, Hs = grad_hess(loss_st, x)
    print(
        f"[3] |loss_st - loss_exact|                 = {abs(float(Ls) - float(Le)):.3e}  (want ~0)"
    )
    print(
        f"    max |grad_st - grad_exact|             = {np.max(np.abs(gs.numpy() - ge.numpy())):.3e}  (want <1e-9)"
    )

    # ---- 4. THE KEY TEST: full Hessian straight-through vs exact (oracle) ----
    He_np, Hs_np = He.numpy(), Hs.numpy()
    absdiff = np.max(np.abs(Hs_np - He_np))
    reldiff = absdiff / np.max(np.abs(He_np))
    print(f"[4] max |Hess_st - Hess_exact|             = {absdiff:.3e}")
    print(f"    relative                               = {reldiff:.3e}  (want <1e-8)")
    # break down by block
    ll = np.max(np.abs((Hs_np - He_np)[:NLAM, :NLAM]))
    lt = np.max(np.abs((Hs_np - He_np)[:NLAM, NLAM:]))
    tt = np.max(np.abs((Hs_np - He_np)[NLAM:, NLAM:]))
    print(
        f"    block diffs:  H(lam,lam)={ll:.2e}  H(lam,theta)={lt:.2e}  H(theta,theta)={tt:.2e}"
    )

    # ---- 5. sanity: exact Hessian vs finite-difference of the gradient ----
    Hfd = np.zeros((NPAR, NPAR))
    xv = x.numpy()
    for k in range(NPAR):
        dp = xv.copy()
        dp[k] += eps
        dm = xv.copy()
        dm[k] -= eps
        _, gp, _ = grad_hess(loss_exact, tf.Variable(dp, dtype=DT))
        _, gm, _ = grad_hess(loss_exact, tf.Variable(dm, dtype=DT))
        Hfd[:, k] = (gp.numpy() - gm.numpy()) / (2 * eps)
    print(
        f"[5] max |Hess_exact - Hess_finitediff|     = {np.max(np.abs(He_np - Hfd)):.3e}  (want <1e-5)"
    )

    ok = (
        np.max(np.abs(v_st - v_exact)) < 1e-10
        and np.max(np.abs(J - Jfd)) < 1e-6
        and reldiff < 1e-8
    )
    print()
    print(
        "RESULT:",
        "PASS -- straight-through reproduces the exact Hessian" if ok else "FAIL",
    )


if __name__ == "__main__":
    main()
