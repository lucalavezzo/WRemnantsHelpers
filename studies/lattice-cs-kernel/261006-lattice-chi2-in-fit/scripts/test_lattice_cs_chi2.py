#!/usr/bin/env python3
"""Unit tests of lattice_cs_chi2.py (run in the container; no cache load, card A only for the theta map).

 1. pert table == our_cs_kernel(scheme=fit) re-evaluated now; full model (k1 = 0) == our_cs_kernel with the lambdas.
 2. numpy core chi2 (syst=none, k1 profiled analytically) == kernel_fit.chi2_at (scipy least_squares with k1 floated)
    at a set of lambda points, incl. NOMSTIFF, XWSTIFF (W) and the T8 Newton point.
 3. lattice-only minimum (syst=none) == 260923-scetlib-kernel-fit 'tanh2 | linf=2 | k1' (chi2, l2, l4, k1).
 4. syst=J: same minimum as stat-only (Woodbury) and the Hessian covariance of (l2, l4) == the 2D card term's stat+syst cov.
 5. TF regularizer on card A: theta->physical map, chi2_tf == numpy, gradient == central finite differences,
    exp(2 tau) compensation via a fake fitter (live variable) and via tau= on the -r line; mismatch raises.
Prints PASS/FAIL per test; exits 1 on any failure."""

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(STUDY, "260923-scetlib-kernel-fit"))
import kernel_fit as KF  # noqa: E402

import lattice_cs_chi2 as L  # noqa: E402

CARD_A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5"
POINTS = {
    "lattice-ish": dict(lambda_inf_nu=2.0, lambda2_nu=0.18, lambda4_nu=-0.006),
    "NOMSTIFF": dict(lambda_inf_nu=2.0, lambda2_nu=0.06427, lambda4_nu=0.0),
    "XWSTIFF (W)": dict(lambda_inf_nu=2.0, lambda2_nu=-1.1e-6, lambda4_nu=0.04441),
    "T8 Newton": dict(lambda_inf_nu=2.0, lambda2_nu=0.0351, lambda4_nu=0.0037),
    "card anchor": dict(lambda_inf_nu=2.0, lambda2_nu=0.15, lambda4_nu=0.0),
    "Tackmann": dict(lambda_inf_nu=1.6853, lambda2_nu=0.087, lambda4_nu=0.0074),
}
FAIL = []


def check(name, ok, msg=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {msg}", flush=True)
    if not ok:
        FAIL.append(name)


def kf_pt(lam):
    return dict(linf=lam["lambda_inf_nu"], l2=lam["lambda2_nu"], l4=lam["lambda4_nu"])


def main():
    core = L.LatticeCSCore(syst="none")
    D = KF.load_data()
    # 1
    p_now = KF.K.our_cs_kernel(core.b_fm, {"lambda_inf_nu": 0.0}, mu=2.0, scheme="fit")
    check(
        "1a pert table == our_cs_kernel now",
        np.max(np.abs(p_now - core.pert)) < 1e-12,
        f"max|d| {np.max(np.abs(p_now - core.pert)):.2e}",
    )
    md = 0.0
    for lam in POINTS.values():
        full = KF.K.our_cs_kernel(core.b_fm, lam, mu=2.0, scheme="fit")
        md = max(md, np.max(np.abs((core.r0(lam) + core.y) - full)))
    check("1b model(k1=0) == our_cs_kernel(lambda)", md < 1e-12, f"max|d| {md:.2e}")
    # 2
    md = 0.0
    for k, lam in POINTS.items():
        ref = KF.chi2_at(D, core.pert, kf_pt(lam), ks=("k1",))
        c, kh = core.chi2(lam), core.k1hat(lam)
        md = max(md, abs(c - ref["chi2"]) / max(1.0, ref["chi2"]))
        print(
            f"      {k:14s} chi2 core {c:10.5f}  kernel_fit {ref['chi2']:10.5f}  k1 {kh:+.5f} vs {ref['x']['k1']:+.5f}"
        )
    check(
        "2  analytic k1 profile == kernel_fit chi2_at", md < 1e-8, f"max rel {md:.2e}"
    )
    # 3
    res, lam = core.fit()
    nom = KF.Fit(D, core.pert, ["l2", "l4", "k1"], fixed=dict(linf=2.0)).run()
    ok = (
        abs(res.fun - nom["chi2"]) < 1e-7
        and abs(lam["lambda2_nu"] - nom["x"]["l2"]) < 1e-5
        and abs(lam["lambda4_nu"] - nom["x"]["l4"]) < 1e-6
    )
    check(
        "3  lattice-only minimum == 260923 'tanh2|linf=2|k1'",
        ok,
        f"chi2 {res.fun:.6f} vs {nom['chi2']:.6f}; l2 {lam['lambda2_nu']:.6f} vs {nom['x']['l2']:.6f}; l4 {lam['lambda4_nu']:.7f} vs {nom['x']['l4']:.7f}; k1 {core.k1hat(lam):.4f} vs {nom['x']['k1']:.4f}",
    )
    # 4
    cj = L.LatticeCSCore(syst="J")
    rj, lj = cj.fit()
    d = np.load(L.DEFAULT_INPUTS)

    def hess(cc, lam0, h=(2e-4, 2e-5)):
        f = lambda a, b: cc.chi2(
            dict(
                lam0,
                lambda2_nu=lam0["lambda2_nu"] + a,
                lambda4_nu=lam0["lambda4_nu"] + b,
            )
        )  # noqa: E731
        H = np.zeros((2, 2))
        H[0, 0] = (f(h[0], 0) - 2 * f(0, 0) + f(-h[0], 0)) / h[0] ** 2
        H[1, 1] = (f(0, h[1]) - 2 * f(0, 0) + f(0, -h[1])) / h[1] ** 2
        H[0, 1] = H[1, 0] = (
            f(h[0], h[1]) - f(h[0], -h[1]) - f(-h[0], h[1]) + f(-h[0], -h[1])
        ) / (4 * h[0] * h[1])
        return H

    Cj = np.linalg.inv(0.5 * hess(cj, lj))
    Cs = np.linalg.inv(0.5 * hess(core, lam))
    sj, ss = np.sqrt(np.diag(Cj)), np.sqrt(np.diag(Cs))
    sc = np.sqrt(np.diag(d["card2d_cov"]))
    sst = np.sqrt(np.diag(d["card2d_cstat"]))

    def gn(cc, lam0):
        # Gauss-Newton (J^T W J)^-1 over (l2, l4, k1) at lam0: the covariance definition of the 2D card term
        u = cc.u
        s2 = (
            1.0
            / np.cosh(
                (lam0["lambda2_nu"] * u + lam0["lambda4_nu"] * u * u)
                / lam0["lambda_inf_nu"]
            )
            ** 2
        )
        X = np.column_stack([-0.5 * s2 * u, -0.5 * s2 * u * u, cc.v])
        return np.linalg.inv(X.T @ cc.W @ X)[:2, :2]

    Gs, Gj = gn(core, lam), gn(cj, lj)
    gs, gj = np.sqrt(np.diag(Gs)), np.sqrt(np.diag(Gj))
    print(
        f"      syst=J  min chi2 {rj.fun:.4f} at l2 {lj['lambda2_nu']:.5f} l4 {lj['lambda4_nu']:.6f}"
    )
    print(
        f"      stat    min chi2 {res.fun:.4f} at l2 {lam['lambda2_nu']:.5f} l4 {lam['lambda4_nu']:.6f}"
    )
    print(
        f"      Gauss-Newton  stat sigma {gs} rho {Gs[0, 1] / gs[0] / gs[1]:+.4f} | syst=J sigma {gj} rho {Gj[0, 1] / gj[0] / gj[1]:+.4f}"
    )
    print(
        f"      card 2D term  stat sigma {sst} | stat+syst sigma {sc} rho {d['card2d_cov'][0, 1] / sc[0] / sc[1]:+.4f}"
    )
    print(
        f"      exact-chi2 Hessian (incl. 2nd-order residual term): stat sigma {ss} rho {Cs[0, 1] / ss[0] / ss[1]:+.4f}"
        f" | syst=J sigma {sj} rho {Cj[0, 1] / sj[0] / sj[1]:+.4f}  (ratio to GN: {ss / gs}, {sj / gj})"
    )
    ok = (
        abs(lj["lambda2_nu"] - lam["lambda2_nu"]) < 1e-3 * ss[0]
        and abs(rj.fun - res.fun) < 1e-6
        and np.max(np.abs(Gs - d["card2d_cstat"]) / np.outer(sst, sst)) < 1e-4
        and np.max(np.abs(Gj - d["card2d_cov"]) / np.outer(sc, sc)) < 1e-4
    )
    check(
        "4  syst=J: same minimum and chi2_min as stat; Gauss-Newton cov == card stat / stat+syst cov (Woodbury)",
        ok,
        f"max rel cov diff stat {np.max(np.abs(Gs - d['card2d_cstat']) / np.outer(sst, sst)):.1e}, "
        f"J {np.max(np.abs(Gj - d['card2d_cov']) / np.outer(sc, sc)):.1e}",
    )
    # 5 TF
    import tensorflow as tf
    from rabbit import inputdata
    from rabbit.mappings import helpers as mh
    from rabbit.regularization import helpers as rh

    indata = inputdata.FitInputData(CARD_A)
    names = np.array(["alphaS", "lambda2", "lambda2_nu", "lambda4_nu", "pdfEig0"])

    def build(*args):
        m = mh.load_mapping("lattice_cs_chi2.LatticeCSMapping", indata, *args)
        return rh.load_regularizer("lattice_cs_chi2.LatticeCSChi2", m, dtype=tf.float64)

    reg = build("syst=none", "offset=0")
    reg.set_expectations(tf.zeros(len(names), tf.float64), None, parms=names)
    md, mg = 0.0, 0.0
    for lam in POINTS.values():
        if lam["lambda_inf_nu"] != 2.0:
            continue
        th = np.zeros(len(names))
        th[2] = (lam["lambda2_nu"] - 0.15) / 0.1
        th[3] = lam["lambda4_nu"] / 0.5
        x = tf.Variable(th)
        with tf.GradientTape() as t:
            p = reg.compute_nll_penalty(x, None)
        g = t.gradient(p, x).numpy()
        md = max(md, abs(2 * float(p) - core.chi2(lam)) / max(1, core.chi2(lam)))
        for i, w in ((2, 0.1), (3, 0.5)):
            h = 1e-6
            lp = dict(lam)
            lm = dict(lam)
            key = "lambda2_nu" if i == 2 else "lambda4_nu"
            lp[key] += w * h
            lm[key] -= w * h
            fd = 0.5 * (core.chi2(lp) - core.chi2(lm)) / (2 * h)
            mg = max(mg, abs(g[i] - fd) / max(1.0, abs(fd)))
        assert g[0] == 0 and g[1] == 0 and g[4] == 0
    check(
        "5a TF chi2 == numpy (theta map 0.15+0.1t, 0+0.5t; linf held 2)",
        md < 1e-10,
        f"max rel {md:.2e}",
    )
    check("5b TF gradient == finite differences", mg < 1e-5, f"max rel {mg:.2e}")

    class FakeFitter:
        def __init__(self, tau, reg):
            self.tau = tf.Variable(tau, dtype=tf.float64)
            self.regularizers = [reg]

        def arm_regularizers(self):
            for r in self.regularizers:
                r.set_expectations(tf.zeros(len(names), tf.float64), None, parms=names)

    th = tf.constant([0.0, 0.0, (0.06427 - 0.15) / 0.1, 0.0, 0.0], tf.float64)
    base = float(reg.compute_nll_penalty(th, None))
    reg2 = build("syst=none", "offset=0")
    ff = FakeFitter(8.0, reg2)
    ff.arm_regularizers()
    v8 = float(reg2.compute_nll_penalty(th, None)) * np.exp(2 * 8.0)
    ff.tau.assign(5.0)  # the LIVE variable is used, not a copy
    v5 = float(reg2.compute_nll_penalty(th, None)) * np.exp(2 * 5.0)
    reg3 = build("syst=none", "offset=0", "tau=8")
    reg3.set_expectations(tf.zeros(len(names), tf.float64), None, parms=names)
    v8b = float(reg3.compute_nll_penalty(th, None)) * np.exp(2 * 8.0)
    check(
        "5c exp(2 tau) compensation (live fitter.tau 8 -> 5, and tau= arg)",
        abs(v8 / base - 1) < 1e-12
        and abs(v5 / base - 1) < 1e-12
        and abs(v8b / base - 1) < 1e-12,
        f"{v8 / base - 1:.1e} {v5 / base - 1:.1e} {v8b / base - 1:.1e}",
    )
    try:
        FakeFitter(5.0, build("syst=none", "tau=8")).arm_regularizers()
        check("5d tau mismatch raises", False)
    except ValueError as e:
        check("5d tau mismatch raises", True, str(e)[:80])
    regm = build("syst=J")  # offset=min, the 2D card covariance
    regm.set_expectations(tf.zeros(len(names), tf.float64), None, parms=names)
    th = tf.constant(
        [0.0, 0.0, (lj["lambda2_nu"] - 0.15) / 0.1, lj["lambda4_nu"] / 0.5, 0.0],
        tf.float64,
    )
    check(
        "5e default (syst=J, offset=min) is 0 at the lattice minimum",
        abs(float(regm.compute_nll_penalty(th, None))) < 1e-9,
        f"{float(regm.compute_nll_penalty(th, None)):.2e}",
    )
    # 6 alphas=live: linearity of the pert table in alpha_s(mZ), and TF live == numpy core with dalphas
    sig = np.sqrt(np.diag(np.load(L.DEFAULT_INPUTS)["cov_stat"]))
    lin = 0.0
    for das in (-0.002, 0.002):
        pn = KF.K.our_cs_kernel(
            core.b_fm,
            {"lambda_inf_nu": 0.0},
            alphas_mz=0.118 + das,
            mu=2.0,
            scheme="fit",
        )
        lin = max(lin, np.max(np.abs(pn - core.pert - das * core.dpert_dalphas) / sig))
    check(
        "6a pert linear in alpha_s over +-0.002 (|nonlinear| / sigma_lat)",
        lin < 5e-3,
        f"max {lin:.1e}",
    )
    regl = build("syst=none", "offset=0", "alphas=live")
    regl.set_expectations(tf.zeros(len(names), tf.float64), None, parms=names)
    lam = POINTS["NOMSTIFF"]
    md = 0.0
    for t_as in (-0.6, 0.0, 0.7):  # theta of alphaS: physical = 0.118 + 0.002 theta
        thv = tf.constant(
            [t_as, 0.0, (lam["lambda2_nu"] - 0.15) / 0.1, 0.0, 0.0], tf.float64
        )
        md = max(
            md,
            abs(
                2 * float(regl.compute_nll_penalty(thv, None))
                - core.chi2(lam, dalphas=0.002 * t_as)
            ),
        )
    check("6b alphas=live TF == numpy core(dalphas)", md < 1e-9, f"max |d| {md:.1e}")
    # 7 phase 2: live alpha_s derivative, the param model's own map, Asimov ydata, syst components
    h = 1e-4
    md = 0.0
    for lam in POINTS.values():
        an = core.dchi2_dalphas(lam)
        cp = [L.LatticeCSCore(syst="none") for _ in range(2)]
        for cc, sg in zip(cp, (+1, -1)):
            cc.pert = KF.K.our_cs_kernel(
                core.b_fm,
                {"lambda_inf_nu": 0.0},
                alphas_mz=0.118 + sg * h,
                mu=2.0,
                scheme="fit",
            )
            cc.c = cc.pert - cc.y
        fd = (cp[0].chi2(lam) - cp[1].chi2(lam)) / (2 * h)
        md = max(md, abs(an - fd) / max(1.0, abs(fd)))
        print(
            f"      dchi2/dalpha_s {an:+10.3f} analytic vs {fd:+10.3f} FD (our_cs_kernel re-evaluated at 0.118 +- 1e-4)"
        )
    check(
        "7a analytic d chi2/d alpha_s == FD of the exact evaluator",
        md < 1e-4,
        f"max rel {md:.1e}",
    )
    regl2 = build("syst=J+pert", "offset=0", "alphas=live")
    regl2.set_expectations(tf.zeros(len(names), tf.float64), None, parms=names)
    mg = 0.0
    for t_as in (-0.6, 0.4):
        x = tf.Variable(
            [t_as, 0.0, (0.06427 - 0.15) / 0.1, 0.002, 0.0], dtype=tf.float64
        )
        with tf.GradientTape() as tp:
            p = regl2.compute_nll_penalty(x, None)
        g = tp.gradient(p, x).numpy()[0]
        e = 1e-6
        xp, xm = x.numpy().copy(), x.numpy().copy()
        xp[0] += e
        xm[0] -= e
        fd = (
            float(regl2.compute_nll_penalty(tf.constant(xp), None))
            - float(regl2.compute_nll_penalty(tf.constant(xm), None))
        ) / (2 * e)
        mg = max(mg, abs(g - fd) / max(1.0, abs(fd)))
    check("7b TF d/d theta_alphaS (live) == FD", mg < 1e-6, f"max rel {mg:.1e}")

    class FakePM:
        _scetlib_order = ("alphaS", "lambda2", "lambda2_nu", "lambda4_nu", "pdfEig0")
        _rp_quad = np.array([True, True, True, True, False])
        _rp_c = np.array(
            [[0.118, 0.4, 0.15, 0.0, 0.0], [0.002, 0.5, 0.1, 0.5, 0.0], [0.0] * 5]
        )
        npoi, npou = 1, 4
        params = np.array([n.encode() for n in _scetlib_order])

    class FakeFitter2(FakeFitter):
        def __init__(self, tau, reg, pm):
            super().__init__(tau, reg)
            self.param_model = pm

    regl3 = build("syst=J+pert", "offset=0", "alphas=live")
    FakeFitter2(8.0, regl3, FakePM()).arm_regularizers()
    check(
        "7c live map taken from the fitter's param model",
        regl3.as_map == (0.118, 0.002),
        str(regl3.as_map),
    )
    bad = FakePM()
    bad._rp_c = bad._rp_c.copy()
    bad._rp_c[0, 0] = 0.119
    try:
        FakeFitter2(
            8.0, build("syst=J+pert", "offset=0", "alphas=live"), bad
        ).arm_regularizers()
        check("7d param-model anchor != pert-table alpha_s raises", False)
    except ValueError as e:
        check("7d param-model anchor != pert-table alpha_s raises", True, str(e)[:70])
    rega = build("syst=J+pert", "offset=0", "alphas=live", "ydata=asimov")
    rega.set_expectations(tf.zeros(len(names), tf.float64), None, parms=names)
    v0 = float(rega.compute_nll_penalty(tf.zeros(len(names), tf.float64), None))
    v1 = float(
        rega.compute_nll_penalty(tf.constant([0.5, 0, 0, 0, 0], tf.float64), None)
    )
    check(
        "7e ydata=asimov: term == 0 at the truth (theta = 0), > 0 off it",
        abs(v0) < 1e-12 and v1 > 0,
        f"{v0:.1e}, {v1:.3e}",
    )
    cJ = L.LatticeCSCore(syst="J")
    c3 = L.LatticeCSCore(syst="Jnf+Jk+Jbt")
    check(
        "7f syst components: J == Jnf+Jk+Jbt",
        np.allclose(cJ.cov, c3.cov, rtol=0, atol=1e-15),
    )
    # 8 phase 3 (pert=live): TNP derivatives vs FD of the validated evaluator; expansion accuracy over the fit range
    sig = np.sqrt(np.diag(np.load(L.DEFAULT_INPUTS)["cov_stat"]))

    def pk(a=0.118, tn=0.0, tc=0.0):
        return KF.K.our_cs_kernel(
            core.b_fm,
            {"lambda_inf_nu": 0.0},
            alphas_mz=a,
            mu=2.0,
            scheme="fit",
            tnp_nu=tn,
            tnp_cusp=tc,
        )

    md = 0.0
    for key, kw in (("resumTNP_gamma_nu", "tn"), ("resumTNP_gamma_cusp", "tc")):
        d1 = core.dpert_tnp[key][0]
        for e in (0.1, 2.0):
            fd = (pk(**{kw: e}) - pk(**{kw: -e})) / (2 * e)
            md = max(md, np.max(np.abs(fd - d1)) / max(np.max(np.abs(d1)), 1e-12))
    check(
        "8a dpert/dTNP == FD of our_cs_kernel (steps 0.1, 2: exactly linear)",
        md < 1e-9,
        f"max rel {md:.1e}",
    )
    md = 0.0
    for key, kw in (("resumTNP_gamma_nu", "tn"), ("resumTNP_gamma_cusp", "tc")):
        dx = core.dpert_tnp[key][1]
        h = 1e-4
        fd = (
            (pk(0.118 + h, **{kw: 1.0}) - pk(0.118 - h, **{kw: 1.0}))
            - (pk(0.118 + h, **{kw: -1.0}) - pk(0.118 - h, **{kw: -1.0}))
        ) / (4 * h)
        md = max(md, np.max(np.abs(fd - dx)) / max(np.max(np.abs(dx)), 1e-12))
    check(
        "8b d2pert/(dalpha_s dTNP) == FD (h 1e-4 vs the 1e-3 table)",
        md < 2e-2,
        f"max rel {md:.1e}",
    )
    w = {}
    for A in (0.002, 0.004):
        worst = 0.0
        for a in (0.118 - A, 0.118 + A):
            for tn in (-2.0, 0.0, 2.0):
                for tc in (-2.0, 0.0, 2.0):
                    exp_ = core.pert + core.pert_shift(
                        a - 0.118,
                        {"resumTNP_gamma_nu": tn, "resumTNP_gamma_cusp": tc},
                        "live",
                    )
                    worst = max(worst, np.max(np.abs(pk(a, tn, tc) - exp_) / sig))
        w[A] = worst
    check(
        "8c pert=live expansion vs the exact evaluator, |TNP| <= 2: <= 5e-3 sigma_lat at |da| <= 0.002",
        w[0.002] < 5e-3,
        f"{w[0.002]:.1e} (|da| <= 0.004: {w[0.004]:.1e})",
    )
    print("ALL PASS" if not FAIL else f"FAILED: {FAIL}")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
