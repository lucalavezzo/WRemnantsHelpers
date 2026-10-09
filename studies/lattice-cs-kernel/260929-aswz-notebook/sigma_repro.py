#!/usr/bin/env python3
"""Reproduce the ASWZ quoted parameter uncertainties from their notebook's resampling rule.

The notebook's pseudo-experiment (summarised in LOGBOOK.md, not copied here) shifts the data of
each ensemble e by  z_e * (Corr_e . sigma_e)  with ONE standard-normal scalar z_e per ensemble,
refits, and quotes the 68% central-interval half-width of the refitted parameters (200 samples).
The fit itself is the ordinary correlated chi2 with the full per-ensemble covariance.

For fixed B_NP the model is linear in the free parameters, so the spread is analytic:
  theta_hat = A (y - off),  A = (X^T W X)^-1 X^T W
  Var_nb(theta) = sum_e (A u_e)(A u_e)^T,   u_e = Corr_e sigma_e  (zero outside ensemble e)
We give that, a 200-sample Monte Carlo with the notebook's CI estimator (and the spread of that
estimate over seeds), and the proper Hessian/GLS sigma for comparison.

Uses the design matrix and data loader of ../260923-lattice-data-refit/cs_fit.py (unchanged).
Run: python3 sigma_repro.py   (plain python3, ~seconds)
"""
import importlib.util
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "cs_fit", os.path.join(HERE, "..", "260923-lattice-data-refit", "cs_fit.py")
)
cs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cs)

ens, D_ = cs.load()
b, y, a, cov, s, ensid = D_["b"], D_["y"], D_["a"], D_["cov"], D_["s"], D_["ens"]
W = np.linalg.inv(cov)

# u_e = Corr_e . sigma_e embedded in the 21-vector
U = []
for i in range(3):
    m = ensid == i
    se = s[m]
    Ce = cov[np.ix_(m, m)]
    Re = Ce / np.outer(se, se)
    u = np.zeros_like(y)
    u[m] = Re @ se
    U.append(u)
U = np.array(U)  # (3, 21)

LQ, UQ = 0.15865525393145707, 0.8413447460685429


def CI(x):
    return 0.5 * (np.quantile(x, UQ) - np.quantile(x, LQ))


def columns(model, BNP):
    off, cols = cs.design(b, a, BNP, "numeric")
    bt = b * cs.FM
    cols = dict(cols)
    cols["g2"] = -(bt**2)  # notebook BLNY: gamma_NP = -g * bT^2 (bT in GeV^-1)
    return off, np.column_stack([cols[p] for p in model])


def analyse(model, BNP=2.0, nboot=200, nseeds=400):
    off, X = columns(model, BNP)
    Cgls = np.linalg.inv(X.T @ W @ X)
    A = Cgls @ X.T @ W
    th = A @ (y - off)
    r = y - off - X @ th
    chi2 = float(r @ W @ r)
    AU = A @ U.T  # (npar, 3)
    Cnb = AU @ AU.T
    # MC with the notebook's estimator: 200 samples, CI half-width; distribution over seeds
    rng = np.random.default_rng(12345)
    est = []
    for _ in range(nseeds):
        z = rng.standard_normal((nboot, 3))
        thb = th[None, :] + z @ AU.T
        est.append([CI(thb[:, k]) for k in range(len(model))])
    est = np.array(est)
    # control: proper parametric bootstrap (full-covariance multivariate draws), same estimator
    L = np.linalg.cholesky(cov)
    z = rng.standard_normal((20000, len(y)))
    thp = th[None, :] + (z @ L.T) @ A.T
    out = dict(
        model=model,
        BNP=BNP,
        chi2=chi2,
        ndf=len(y) - len(model),
        theta=th.tolist(),
        sig_gls=np.sqrt(np.diag(Cgls)).tolist(),
        sig_nb_analytic=np.sqrt(np.diag(Cnb)).tolist(),
        sig_nb_mc200_median=np.median(est, 0).tolist(),
        sig_nb_mc200_16_84=[
            np.quantile(est, 0.16, 0).tolist(),
            np.quantile(est, 0.84, 0).tolist(),
        ],
        sig_proper_boot=[CI(thp[:, k]) for k in range(len(model))],
        rho_gls=(
            float(Cgls[0, 1] / np.sqrt(Cgls[0, 0] * Cgls[1, 1]))
            if len(model) > 1
            else None
        ),
        rho_nb=(
            float(Cnb[0, 1] / np.sqrt(Cnb[0, 0] * Cnb[1, 1]))
            if len(model) > 1
            else None
        ),
    )
    return out


def main():
    print("u_e / sigma (how coherent the per-ensemble shift is):")
    for i, e in enumerate(ens):
        m = ensid == i
        print(f"  {e['name']}: {np.round(U[i][m] / s[m], 3).tolist()}")
    res = []
    for model, BNP in [
        (["c0", "k1"], 2.0),
        (["c0", "k2"], 2.0),
        (["c0", "k1", "k2"], 2.0),
        (["c0", "c1", "k1"], 2.0),
        (["c0"], 2.0),
        (["g2", "k1"], 1.5),
    ]:
        r = analyse(model, BNP)
        res.append(r)
        print(
            f"\n{model} B_NP={BNP}: chi2={r['chi2']:.3f}/{r['ndf']}  theta={np.round(r['theta'], 5).tolist()}"
        )
        for k, p in enumerate(model):
            print(
                f"  {p:3s}: GLS {r['sig_gls'][k]:.4f} | notebook rule analytic {r['sig_nb_analytic'][k]:.4f}"
                f" | MC(200, CI) median {r['sig_nb_mc200_median'][k]:.4f}"
                f" [16-84% over seeds {r['sig_nb_mc200_16_84'][0][k]:.4f}-{r['sig_nb_mc200_16_84'][1][k]:.4f}]"
                f" | proper full-cov bootstrap {r['sig_proper_boot'][k]:.4f}"
            )
        if r["rho_gls"] is not None:
            print(
                f"  rho(p0,p1): GLS {r['rho_gls']:+.3f}, notebook rule {r['rho_nb']:+.3f}"
            )
    json.dump(res, open(os.path.join(HERE, "sigma_repro.json"), "w"), indent=1)


if __name__ == "__main__":
    main()


def alt_vector_rule():
    """Control: if the draw were one normal PER POINT (vector) times (Corr.sigma)_i, instead of one per ensemble."""
    uall = U.sum(0)
    for model, BNP in [(["c0", "k1"], 2.0), (["c0", "k2"], 2.0), (["g2", "k1"], 1.5)]:
        off, X = columns(model, BNP)
        A = np.linalg.inv(X.T @ W @ X) @ X.T @ W
        Cv = A @ np.diag(uall**2) @ A.T
        print(
            f"  vector-draw control {model}: sigma = {np.round(np.sqrt(np.diag(Cv)), 4).tolist()}"
        )


if __name__ == "__main__":
    alt_vector_rule()
