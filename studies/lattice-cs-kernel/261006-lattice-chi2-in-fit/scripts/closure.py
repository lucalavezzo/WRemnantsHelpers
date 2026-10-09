#!/usr/bin/env python3
"""Step 2 closure: minimise the LatticeCSChi2 regularizer ALONE (the TF object rabbit would use, card A theta map, linf
held at 2), and compare with the separate lattice fit (260923-scetlib-kernel-fit 'tanh2 | linf=2 | k1': chi2 6.713/18,
l2 0.1844, l4 -0.00592, GN cov sigma 0.0383/0.00325 rho -0.8825 stat; card 2D term stat+syst 0.0567/0.0040 rho -0.911).
Then exact vs Gaussian Delta chi2 at the reference points (NOMSTIFF, XWSTIFF = W, T8 Newton point), and the alpha_s /
TNP sensitivity of the frozen pert table. Writes ../closure.json. alphaS is never read (only the TNP thetas of NOMSTIFF).
"""

import json
import os
import sys

import numpy as np
import tensorflow as tf
from scipy.optimize import minimize

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from rabbit import inputdata, io_tools  # noqa: E402
from rabbit.mappings import helpers as mh  # noqa: E402
from rabbit.regularization import helpers as rh  # noqa: E402

import lattice_cs_chi2 as L  # noqa: E402

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
CARD_A = (
    f"{A}/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5"
)
NOMSTIFF = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
REF = {  # physical CS lambdas, linf = 2 (walled-multistart-census/261006-t8-l4nu-lattice2d/ref_points.json, l4zero_pull)
    "NOMSTIFF (1D card, l4nu = 0)": (0.06427, 0.0),
    "XWSTIFF = W (no lattice)": (-1.1216e-06, 0.044408),
    "T8 Newton point (2D card)": (0.0351, 0.0037),
    "card anchor": (0.15, 0.0),
}
L4Z = dict(
    mu=0.13454936442162735, sig=0.03127467886885041
)  # the 1D l4zero card term (NOMSTIFF's)
names = np.array(["alphaS", "lambda2_nu", "lambda4_nu"])
indata = inputdata.FitInputData(CARD_A)


def build(syst):
    m = mh.load_mapping(
        "lattice_cs_chi2.LatticeCSMapping", indata, f"syst={syst}", "offset=0"
    )
    r = rh.load_regularizer("lattice_cs_chi2.LatticeCSChi2", m, dtype=tf.float64)
    r.set_expectations(tf.zeros(3, tf.float64), None, parms=names)
    return r


def th(l2, l4):
    return np.array([0.0, (l2 - 0.15) / 0.1, l4 / 0.5])


def minimise(reg):
    @tf.function
    def vg(x):
        with tf.GradientTape() as t:
            t.watch(x)
            f = 2.0 * reg.compute_nll_penalty(x, None)  # chi2
        return f, t.gradient(f, x)

    def fun(z):
        f, g = vg(tf.constant(np.concatenate([[0.0], z])))
        return float(f), g.numpy()[1:]

    r = minimize(
        fun, th(0.15, 0.0)[1:], jac=True, method="BFGS", options=dict(gtol=1e-10)
    )
    x = tf.constant(np.concatenate([[0.0], r.x]))
    with tf.GradientTape() as t2:
        t2.watch(x)
        with tf.GradientTape() as t1:
            t1.watch(x)
            f = 2.0 * reg.compute_nll_penalty(x, None)
        g = t1.gradient(f, x)
    H = t2.jacobian(g, x).numpy()[1:, 1:]  # d2 chi2 / dtheta2
    W = np.diag([0.1, 0.5])
    C = W @ np.linalg.inv(0.5 * H) @ W  # physical
    s = np.sqrt(np.diag(C))
    l2, l4 = 0.15 + 0.1 * r.x[0], 0.5 * r.x[1]
    return dict(
        chi2=float(r.fun),
        l2=l2,
        l4=l4,
        sigma=s.tolist(),
        rho=float(C[0, 1] / s[0] / s[1]),
        cov=C.tolist(),
        k1=reg.core.k1hat(dict(lambda_inf_nu=2.0, lambda2_nu=l2, lambda4_nu=l4)),
        nit=int(r.nit),
        grad=float(np.max(np.abs(r.jac))),
    )


def gn_cov(core, l2, l4):
    u = core.u
    s2 = 1.0 / np.cosh((l2 * u + l4 * u * u) / 2.0) ** 2
    X = np.column_stack([-0.5 * s2 * u, -0.5 * s2 * u * u, core.v])
    C = np.linalg.inv(X.T @ core.W @ X)[:2, :2]
    s = np.sqrt(np.diag(C))
    return dict(sigma=s.tolist(), rho=float(C[0, 1] / s[0] / s[1]))


def main():
    out = dict(closure={}, points={}, sensitivity={})
    regs = {s: build(s) for s in ("none", "J", "Jk+Jbt+direct_nf")}
    for s, reg in regs.items():
        m = minimise(reg)
        m["gauss_newton"] = gn_cov(reg.core, m["l2"], m["l4"])
        out["closure"][s] = m
        print(
            f"[closure syst={s:9s}] chi2_min {m['chi2']:.4f} (ndf 18) l2 {m['l2']:.5f} l4 {m['l4']:.6f} k1 {m['k1']:.4f} | "
            f"exact-Hessian sigma {np.round(m['sigma'], 5)} rho {m['rho']:+.4f} | GN sigma {np.round(m['gauss_newton']['sigma'], 5)} "
            f"rho {m['gauss_newton']['rho']:+.4f}  (nit {m['nit']}, |g| {m['grad']:.1e})",
            flush=True,
        )
    d = np.load(L.DEFAULT_INPUTS)
    mu2, C2, Cs2 = d["card2d_mu"], d["card2d_cov"], d["card2d_cstat"]
    H2, Hs2 = np.linalg.inv(C2), np.linalg.inv(Cs2)
    for k, (l2, l4) in REF.items():
        lam = dict(lambda_inf_nu=2.0, lambda2_nu=l2, lambda4_nu=l4)
        row = {}
        for s, reg in regs.items():
            row[f"exact_{s}"] = reg.core.chi2(lam) - out["closure"][s]["chi2"]
            row[f"k1hat_{s}"] = reg.core.k1hat(lam)
        dv = np.array([l2, l4]) - mu2
        row["gauss2d_statsyst (card)"] = float(dv @ H2 @ dv)
        row["gauss2d_stat"] = float(dv @ Hs2 @ dv)
        row["gauss1d_l4zero (NOMSTIFF card)"] = (
            float(((l2 - L4Z["mu"]) / L4Z["sig"]) ** 2) if l4 == 0.0 else None
        )
        out["points"][k] = row
    keys = list(REF)
    base = out["points"][keys[0]]
    for k in keys:
        out["points"][k]["minus_NOMSTIFF"] = {
            c: (
                v - base[c]
                if (v is not None and base[c] is not None and not c.startswith("k1"))
                else None
            )
            for c, v in out["points"][k].items()
            if c != "minus_NOMSTIFF"
        }
    for k, r in out["points"].items():
        print(
            f"[point] {k}: "
            + ", ".join(
                f"{c} {v:.2f}" if isinstance(v, float) else f"{c} {v}"
                for c, v in r.items()
                if c != "minus_NOMSTIFF"
            )
        )
    # sensitivity of the frozen pert table to alpha_s(mZ) and to the CS-kernel TNPs
    fr = io_tools.get_fitresult(NOMSTIFF, None)
    h = fr["parms"].get()
    nm = [str(n) for n in h.axes[0]]
    x = np.asarray(h.values(), float)
    s_as = np.sqrt(np.asarray(h.variances(), float))[
        nm.index("alphaS")
    ]  # sigma only (a width, not blinded value)
    tnp = {
        n: float(x[nm.index(n)]) for n in ("resumTNP_gamma_nu", "resumTNP_gamma_cusp")
    }
    sig_as_mz = None
    try:
        from wremnants.postprocessing.scetlib_ad import params as P

        rp = P.reparam("alphaS")
        sig_as_mz = (
            float(s_as * rp[1][0]) if rp is not None and rp[0] == "unit" else None
        )
        out["sensitivity"]["alphaS_reparam"] = str(rp)
    except Exception as e:  # report, do not hide
        out["sensitivity"]["alphaS_reparam_error"] = repr(e)
    core = regs["J"].core
    for k in (keys[0], keys[2]):
        l2, l4 = REF[k]
        lam = dict(lambda_inf_nu=2.0, lambda2_nu=l2, lambda4_nu=l4)
        r = core.r0(lam)
        g_as = float(2 * r @ core.M @ core.dpert_dalphas)  # d chi2 / d alpha_s(mZ)
        c_as = float(2 * core.dpert_dalphas @ core.M @ core.dpert_dalphas)
        dt = (
            tnp["resumTNP_gamma_nu"] * d["dpert_dtnp_nu"]
            + tnp["resumTNP_gamma_cusp"] * d["dpert_dtnp_cusp"]
        )
        rt = r + dt
        row = dict(
            dchi2_dalphas=g_as,
            d2chi2_dalphas2=c_as,
            sigma_alphaS_mZ_NOMSTIFF=sig_as_mz,
            dchi2_per_sigma_alphaS=(g_as * sig_as_mz if sig_as_mz else None),
            nll_pull_on_alphaS_in_sigma=(
                -0.5 * g_as * sig_as_mz if sig_as_mz else None
            ),
            tnp_thetas_NOMSTIFF=tnp,
            dchi2_from_postfit_tnps=float(rt @ core.M @ rt - r @ core.M @ r),
            max_abs_point_shift_tnps=float(np.max(np.abs(dt))),
        )
        out["sensitivity"][k] = row
        print(f"[sens] {k}: {row}")
    json.dump(
        out, open(os.path.join(TASK, "closure.json"), "w"), indent=1, default=float
    )


if __name__ == "__main__":
    main()
