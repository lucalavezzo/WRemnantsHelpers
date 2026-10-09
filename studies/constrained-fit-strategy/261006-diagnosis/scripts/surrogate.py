#!/usr/bin/env python3
"""Quadratic surrogate of the NOMINAL walled fit, built from stored fitresults only (no cache load).

    f(theta) = g^T d + 1/2 d^T H d + K * sum_i relu(-c_i(theta))^2,   d = theta - theta_ref

* H     : the DATA-ONLY Hessian at the trust-constr point TCA (= NOMSTIFF to 2e-5 sigma), i.e. the
          inverse of the HESSTCA covariance (a --noFit pass without -r). 3719 x 3719, eigenvalues in
          theta [0.459, 4.31e4].
* theta_ref = TCA's x (on the face L2(|Y|=2.5) = 0 to 6e-10).
* g     : mu * a_face with a_face = dc_{L2(2.5)}/dtheta and mu = TCA's KKT multiplier (16.27), so that
          theta_ref is EXACTLY the constrained minimum of the surrogate (KKT by construction).
* c_i   : the 5 NPDampingWall conditions armed in the nominal (lambda2_nu, L2(0), B(0), L2(2.5), B(2.5)),
          margin 0, with the exact theta -> physical map (the B conditions are cubic). K = exp(2 tau).

What it is good for: the SPECTRUM, the wall geometry and the kink are the real ones, so it isolates how
each minimiser copes with "stiff relu^2 face + 1e5-conditioned data Hessian" from everything the
quadratic model leaves out (likelihood non-quadraticity, which matters far from the minimum).
Counters: n_f (loss+grad evaluations) and n_hvp, so a surrogate run can be costed in real-fit units.
"""
import numpy as np

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261006_constrained_fit_diagnosis"
YMAX = 2.5
MAP = {
    "lambda2": (0.4, 0.5),
    "lambda4": (0.4, 0.5),
    "delta_lambda2": (0.0, 0.5),
    "lambda2_nu": (0.15, 0.1),
}


class Surrogate:
    def __init__(self, tau=8.0, hess_src="HESSTCA", ref="TCA", mu=None, wall=True):
        d = np.load(f"{A}/{hess_src}.npz")
        self.names = d["names"].astype(str)
        cov = d["cov"]
        H = np.linalg.inv(cov)
        self.H = 0.5 * (H + H.T)
        r = np.load(f"{A}/{ref}.npz")
        assert (r["names"].astype(str) == self.names).all()
        self.x_ref = r["x"].copy()
        self.idx = {n: int(np.where(self.names == n)[0][0]) for n in MAP}
        self.K = np.exp(2 * tau)
        # penalty shape phi(v), v = relu(-c): "relu2" K v^2 (NPDampingWall), "relu3" K3 v^3 (C^2),
        # "smooth2" relu^2 with the curvature ramped linearly from 0 to 2K over v in [0, delta] (C^2).
        self.pen = "relu2"
        self.K3 = None
        self.delta = None
        self.tau = tau
        self.wall = wall
        c, J, _ = self.conds(self.x_ref)
        self.labels = ["lambda2_nu", "L2(0)", "B(0)", "L2(2.5)", "B(2.5)"]
        self.iface = 3
        if mu is None:
            mu = 16.27  # TCA KKT multiplier of L2(2.5) (261005-trust-constr-port)
        self.mu = mu
        self.g = mu * J[self.iface]
        self.n_f = 0
        self.n_hvp = 0

    # ---- conditions: values, theta-Jacobian, theta-Hessians (only B has one) ----
    def lam(self, x):
        return {n: c0 + w * x[self.idx[n]] for n, (c0, w) in MAP.items()}

    def conds(self, x):
        v = self.lam(x)
        n = len(x)
        i2, i4, id_, inu = (
            self.idx[k] for k in ("lambda2", "lambda4", "delta_lambda2", "lambda2_nu")
        )
        jnu = np.zeros(n)
        jnu[inu] = 0.1
        c, J, Hs = [v["lambda2_nu"]], [jnu], [None]
        for y in (0.0, YMAX):
            L2 = v["lambda2"] + v["delta_lambda2"] * y * y
            jL = np.zeros(n)
            jL[i2] = 0.5
            jL[id_] = 0.5 * y * y
            jb = 3 * L2**2 * jL
            jb[i4] += 1.5
            c += [L2, 3 * v["lambda4"] + L2**3]
            J += [jL, jb]
            Hs += [None, (6 * L2, jL)]
        # order: lambda2_nu, L2(0), B(0), L2(2.5), B(2.5)
        return np.array(c), np.array(J), Hs

    # ---- objective ----
    def data(self, x):
        dx = x - self.x_ref
        Hd = self.H @ dx
        return float(self.g @ dx + 0.5 * dx @ Hd), self.g + Hd

    def fun(self, x):
        self.n_f += 1
        f, gr = self.data(x)
        if self.wall:
            c, J, _ = self.conds(x)
            v = np.maximum(0.0, -c)
            f += float(np.sum(self.phi(v)))
            gr = gr - (self.dphi(v) @ J)
        return f, gr

    def phi(self, v):
        if self.pen == "relu2":
            return self.K * v * v
        if self.pen == "relu3":
            return self.K3 * v**3
        d = self.delta
        return np.where(
            v < d, self.K * v**3 / (3 * d), self.K * (v * v - d * v + d * d / 3)
        )

    def dphi(self, v):
        if self.pen == "relu2":
            return 2 * self.K * v
        if self.pen == "relu3":
            return 3 * self.K3 * v * v
        d = self.delta
        return np.where(v < d, self.K * v * v / d, self.K * (2 * v - d))

    def d2phi(self, v):
        if self.pen == "relu2":
            return 2 * self.K * (v > 0)
        if self.pen == "relu3":
            return 6 * self.K3 * v
        d = self.delta
        return np.where(v < d, 2 * self.K * v / d, 2 * self.K)

    def hessp(self, x, p):
        self.n_hvp += 1
        hp = self.H @ p
        if self.wall:
            c, J, Hs = self.conds(x)
            for i in range(len(c)):
                if c[i] < 0:
                    v = -c[i]
                    hp += float(self.d2phi(np.array(v))) * (J[i] @ p) * J[i]
                    if Hs[i] is not None:  # -phi'(v) * Hess(c) p
                        s, jL = Hs[i]
                        hp += -float(self.dphi(np.array(v))) * s * (jL @ p) * jL
        return hp

    def data_only_value(self, x):
        return self.data(x)[0]

    def violations(self, x):
        c, _, _ = self.conds(x)
        return dict(zip(self.labels, c.tolist()))
