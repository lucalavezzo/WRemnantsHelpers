"""Fit OUR SCETlib CS kernel (pert + NP tanh) + lattice-spacing terms to the ASWZ
per-ensemble lattice data (arXiv:2402.06725), full block-diagonal covariance.

    model_i = pert(b_i; scheme) + 1/2 gamma_nu^NP(b_i; lambda) + k1 a_i/b_i + k2 (a_i/b_i)^2

pert  : our_cs_kernel.py (260923-conventions-map), lambda_inf_nu = 0, mu = 2 GeV, N3LL,
        alpha_s(mZ) = 0.118, fit's mu0 floor / sextic b*.  Validated vs SCETlib to 5e-11.
NP    : SCETlib gamma_nu units, gamma_zeta^NP = -(linf/2) tanh((l2 b^2 + l4 b^4 [+ l6 b^6])/linf).
data  : 260923-lattice-data-refit/cs_fit.py::load() (per-ensemble L32/L48/L64, block-diag cov;
        NO cross-ensemble correlations -- assumption, open question to the authors).

Outputs: fit_results.json, fit_output.txt, pert_tables.npz (all in this dir).
"""

import importlib.util
import json
import os
import sys

import numpy as np
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


K = _load(
    "our_cs_kernel", os.path.join(STUDY, "260923-conventions-map", "our_cs_kernel.py")
)
CSF = _load("cs_fit", os.path.join(STUDY, "260923-lattice-data-refit", "cs_fit.py"))
FM = K.FM_TO_GEVINV

TACKMANN_MU = np.array(
    [1.6853, 0.0870, 0.0074]
)  # (linf, l2, l4), AN theory.tex L257-282
TACKMANN_SIG = np.array([0.5069, 0.0332, 0.0066])
TACKMANN_CORR = np.array(
    [[1, 0.5212, -0.7249], [0.5212, 1, -0.9135], [-0.7249, -0.9135, 1]]
)
TACKMANN_COV = np.outer(TACKMANN_SIG, TACKMANN_SIG) * TACKMANN_CORR


# ------------------------------------------------------------------ perturbative tables
def pert_tables(b_fm):
    """pert kernel at each b in the schemes used here (all at mu = 2 GeV, lattice units)."""
    b_fm = np.asarray(b_fm, float)
    lam0 = {"lambda_inf_nu": 0.0}
    out = {}
    out["nf5"] = K.our_cs_kernel(b_fm, lam0, mu=2.0, scheme="fit")
    out["nf4"] = K.our_cs_kernel(b_fm, lam0, mu=2.0, scheme="lattice")
    # n_f=5 <-> n_f=4 identified at mu = 1 GeV instead of 2 GeV: our nf5 kernel at 1 GeV, evolved
    # to 2 GeV with the n_f=4 cusp (what the lattice kernel does between 1 and 2 GeV).
    p5_1 = K.our_cs_kernel(b_fm, lam0, mu=1.0, scheme="fit")
    p4_1 = K.our_cs_kernel(b_fm, lam0, mu=1.0, scheme="lattice")
    out["nf5_mu1match"] = p5_1 + (out["nf4"] - p4_1)
    return out


def np_zeta(b_fm, linf, l2, l4, l6=0.0):
    b2 = (np.asarray(b_fm) * FM) ** 2
    arg = (l2 * b2 + l4 * b2**2 + l6 * b2**3) / linf
    return -0.5 * linf * np.tanh(arg)


# ------------------------------------------------------------------ data
def load_data():
    ens, D = CSF.load()
    return D


# ------------------------------------------------------------------ fit machinery
ALL = ["linf", "l2", "l4", "l6", "k1", "k2"]
BOUNDS = dict(
    linf=(1e-3, 50.0),
    l2=(-2.0, 2.0),
    l4=(-1.0, 1.0),
    l6=(-1.0, 1.0),
    k1=(-5, 5),
    k2=(-5, 5),
)


class Fit:
    def __init__(self, D, pert, free, fixed=None, mask=None, extra_cov=None):
        self.m = np.ones(len(D["b"]), bool) if mask is None else mask
        self.b, self.a, self.y = D["b"][self.m], D["a"][self.m], D["y"][self.m]
        cov = D["cov"][np.ix_(self.m, self.m)]
        if extra_cov is not None:
            cov = cov + extra_cov[np.ix_(self.m, self.m)]
        self.cov = cov
        self.L = np.linalg.cholesky(cov)
        self.pert = pert[self.m]
        self.free = list(free)
        self.fixed = dict(linf=1.6853, l2=0.0, l4=0.0, l6=0.0, k1=0.0, k2=0.0)
        self.fixed.update(fixed or {})

    def full(self, x):
        p = dict(self.fixed)
        p.update(dict(zip(self.free, x)))
        return p

    def model(self, p, b=None, a=None):
        b = self.b if b is None else b
        a = self.a if a is None else a
        return (
            None
            if b is None
            else (
                np_zeta(b, p["linf"], p["l2"], p["l4"], p["l6"])
                + p["k1"] * a / b
                + p["k2"] * (a / b) ** 2
            )
        )

    def resid(self, x):
        p = self.full(x)
        r = self.y - self.pert - self.model(p)
        return np.linalg.solve(self.L, r)

    def chi2(self, x):
        r = self.resid(x)
        return float(r @ r)

    def run(self, starts=None, seed=0):
        rng = np.random.default_rng(seed)
        lo = np.array([BOUNDS[n][0] for n in self.free])
        hi = np.array([BOUNDS[n][1] for n in self.free])
        base = dict(linf=1.7, l2=0.09, l4=0.007, l6=0.0, k1=0.2, k2=0.0)
        x0s = [np.array([base[n] for n in self.free])]
        for _ in range(40):
            x0s.append(
                np.array(
                    [
                        dict(
                            linf=rng.uniform(0.3, 6),
                            l2=rng.uniform(-0.1, 0.4),
                            l4=rng.uniform(-0.02, 0.06),
                            l6=rng.uniform(-0.005, 0.01),
                            k1=rng.uniform(-0.3, 0.6),
                            k2=rng.uniform(-0.3, 0.6),
                        )[n]
                        for n in self.free
                    ]
                )
            )
        if starts:
            x0s += [np.array(s) for s in starts]
        best = None
        for x0 in x0s:
            x0 = np.clip(x0, lo + 1e-9, hi - 1e-9)
            try:
                r = least_squares(
                    self.resid,
                    x0,
                    bounds=(lo, hi),
                    method="trf",
                    x_scale="jac",
                    xtol=1e-14,
                    ftol=1e-14,
                    gtol=1e-14,
                    max_nfev=20000,
                )
            except Exception:
                continue
            c = float(2 * r.cost)
            if best is None or c < best[0] - 1e-10:
                best = (c, r)
        c, r = best
        self.x = r.x
        J = r.jac
        H = J.T @ J
        try:
            C = np.linalg.inv(H)
        except np.linalg.LinAlgError:
            C = np.linalg.pinv(H)
        at_bound = [
            n
            for n, v in zip(self.free, r.x)
            if abs(v - BOUNDS[n][0]) < 1e-6 * max(1, abs(BOUNDS[n][0]))
            or abs(v - BOUNDS[n][1]) < 1e-6 * max(1, abs(BOUNDS[n][1]))
        ]
        n = len(self.y)
        k = len(self.free)
        sig = np.sqrt(np.clip(np.diag(C), 0, None))
        corr = C / np.outer(sig, sig) if np.all(sig > 0) else C * np.nan
        # flat directions: eigen-decomposition of the Fisher matrix in units of each parameter's own sigma
        Hs = H * np.outer(sig, sig)
        w, v = np.linalg.eigh(Hs)
        return dict(
            free=self.free,
            x=dict(zip(self.free, r.x.tolist())),
            err=dict(zip(self.free, sig.tolist())),
            cov=C.tolist(),
            corr=corr.tolist(),
            chi2=c,
            n=n,
            npar=k,
            ndf=n - k,
            aic=c + 2 * k,
            at_bound=at_bound,
            fixed={kk: vv for kk, vv in self.fixed.items() if kk not in self.free},
            fisher_eig_scaled=w.tolist(),
            fisher_evec_scaled=v.T.tolist(),
            cond_scaled=float(w.max() / max(w.min(), 1e-300)),
        )


def chi2_at(D, pert, lam, ks=("k1",), mask=None, extra_cov=None):
    """chi2 of a FIXED NP tune (dict linf,l2,l4[,l6]) with the lattice-spacing terms floated (linear)."""
    f = Fit(D, pert, list(ks), fixed=dict(lam), mask=mask, extra_cov=extra_cov)
    r = f.run()
    return r


def profile(D, pert, free, name, grid, fixed=None, mask=None):
    """Profile chi2 in one NP parameter (others in `free` re-minimised)."""
    out = []
    others = [f for f in free if f != name]
    for g in grid:
        fx = dict(fixed or {})
        fx[name] = g
        f = Fit(D, pert, others, fixed=fx, mask=mask)
        out.append(f.run()["chi2"])
    return np.array(out)


# ------------------------------------------------------------------ main
CONFIGS = [
    # label, free, fixed, pert key, mask key
    ("tanh2 | linf free | k1", ["linf", "l2", "l4", "k1"], {}, "nf5", None),
    ("tanh2 | linf free | k2", ["linf", "l2", "l4", "k2"], {}, "nf5", None),
    ("tanh2 | linf free | k1+k2", ["linf", "l2", "l4", "k1", "k2"], {}, "nf5", None),
    ("tanh2 | linf free | no k", ["linf", "l2", "l4"], {}, "nf5", None),
    ("tanh2 | linf=1.6853 | k1", ["l2", "l4", "k1"], {"linf": 1.6853}, "nf5", None),
    ("tanh2 | linf=2 | k1", ["l2", "l4", "k1"], {"linf": 2.0}, "nf5", None),
    ("tanh2 | l4=0, linf free | k1", ["linf", "l2", "k1"], {"l4": 0.0}, "nf5", None),
    ("tanh2 | l4=0, linf=2 | k1", ["l2", "k1"], {"l4": 0.0, "linf": 2.0}, "nf5", None),
    ("tanh6 | linf free | k1", ["linf", "l2", "l4", "l6", "k1"], {}, "nf5", None),
    ("tanh6 | linf=2 | k1", ["l2", "l4", "l6", "k1"], {"linf": 2.0}, "nf5", None),
    # systematics on the nominal (tanh2, linf free, k1)
    ("SYST nf4 scheme", ["linf", "l2", "l4", "k1"], {}, "nf4", None),
    (
        "SYST nf5, nf matched at mu=1",
        ["linf", "l2", "l4", "k1"],
        {},
        "nf5_mu1match",
        None,
    ),
    ("SYST drop bT<0.2 fm", ["linf", "l2", "l4", "k1"], {}, "nf5", "b>=0.2"),
    ("SYST drop bT<0.2 fm, k2", ["linf", "l2", "l4", "k2"], {}, "nf5", "b>=0.2"),
    ("SYST nf4 scheme, linf=2", ["l2", "l4", "k1"], {"linf": 2.0}, "nf4", None),
    (
        "SYST nf matched mu=1, linf=2",
        ["l2", "l4", "k1"],
        {"linf": 2.0},
        "nf5_mu1match",
        None,
    ),
    ("SYST drop bT<0.2 fm, linf=2", ["l2", "l4", "k1"], {"linf": 2.0}, "nf5", "b>=0.2"),
    ("SYST k2, linf=2", ["l2", "l4", "k2"], {"linf": 2.0}, "nf5", None),
    ("SYST k1+k2, linf=2", ["l2", "l4", "k1", "k2"], {"linf": 2.0}, "nf5", None),
    (
        "SYST nf-syst in cov, linf free",
        ["linf", "l2", "l4", "k1"],
        {},
        "nf5",
        "COVSYST",
    ),
    (
        "SYST nf-syst in cov, linf=2",
        ["l2", "l4", "k1"],
        {"linf": 2.0},
        "nf5",
        "COVSYST",
    ),
]


def main():
    D = load_data()
    P = pert_tables(D["b"])
    bgrid = np.linspace(0.05, 1.2, 116)
    Pg = pert_tables(bgrid)
    np.savez(
        os.path.join(HERE, "pert_tables.npz"),
        b=D["b"],
        bgrid=bgrid,
        **{f"data_{k}": v for k, v in P.items()},
        **{f"grid_{k}": v for k, v in Pg.items()},
    )
    delta = P["nf5"] - P["nf4"]
    covsyst = np.outer(delta, delta)
    lines = []

    def pr(s=""):
        print(s)
        lines.append(s)

    pr(
        f"N points = {len(D['b'])};  pert(nf5)-pert(nf4) at data b: min {delta.min():+.4f} max {delta.max():+.4f}"
    )
    pr(f"nf5_mu1match - nf5 at data b: {np.round(P['nf5_mu1match'] - P['nf5'], 4)}")
    res = {}
    for lab, free, fixed, pk, mk in CONFIGS:
        mask, extra = None, None
        if mk == "b>=0.2":
            mask = D["b"] >= 0.2 - 1e-9
        if mk == "COVSYST":
            extra = covsyst
        f = Fit(D, P[pk], free, fixed=fixed, mask=mask, extra_cov=extra)
        r = f.run()
        r["label"], r["pert"], r["mask"] = lab, pk, mk
        res[lab] = r
        s = "  ".join(f"{n}={r['x'][n]:+.4f}({r['err'][n]:.4f})" for n in free)
        pr(
            f"{lab:38s} chi2={r['chi2']:6.2f} n={r['n']} ndf={r['ndf']} AIC={r['aic']:6.2f} {s}"
            + (f"  AT BOUND {r['at_bound']}" if r["at_bound"] else "")
        )
    pr()
    for lab in [
        "tanh2 | linf free | k1",
        "tanh2 | linf=2 | k1",
        "tanh2 | linf=1.6853 | k1",
        "tanh6 | linf free | k1",
        "tanh6 | linf=2 | k1",
    ]:
        r = res[lab]
        pr(f"[{lab}] correlation ({', '.join(r['free'])}):")
        for row in r["corr"]:
            pr("   " + " ".join(f"{v:+.3f}" for v in row))
        pr(
            f"   scaled-Fisher eigenvalues {np.round(r['fisher_eig_scaled'], 4)}  (1 = independent; ~0 = flat)"
        )
        v0 = np.array(r["fisher_evec_scaled"][0])
        pr(
            f"   softest direction (in sigma units): "
            + ", ".join(f"{n}:{c:+.2f}" for n, c in zip(r["free"], v0))
        )
    # profiles in linf for the nominal
    grid = np.array(
        [0.3, 0.5, 0.75, 1.0, 1.25, 1.5, 1.6853, 2.0, 2.5, 3.0, 4.0, 6.0, 10.0, 20.0]
    )
    prof = profile(D, P["nf5"], ["linf", "l2", "l4", "k1"], "linf", grid)
    res["_profile_linf"] = dict(grid=grid.tolist(), chi2=prof.tolist())
    pr()
    pr(
        "profile chi2(linf) [tanh2, k1]: "
        + ", ".join(f"{g}:{c:.2f}" for g, c in zip(grid, prof))
    )
    json.dump(res, open(os.path.join(HERE, "fit_results.json"), "w"), indent=1)
    open(os.path.join(HERE, "fit_output.txt"), "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
