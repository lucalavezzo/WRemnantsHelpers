"""Compatibility of fixed NP tunes (Tackmann/AN, scetlib_ad real-data postfits) with the lattice
data (k floated), lattice-fit posterior samples, and kernel-space curves/bands for plotting.
Host python (numpy/scipy). Inputs: kernel_fit.py (module), ad_postfits.json, pert_tables.npz.
Outputs: compat.json, compat.txt, bands.npz."""

import json
import os
import sys

import numpy as np
from scipy.stats import chi2 as chi2dist, norm

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kernel_fit as KF  # noqa: E402

D = KF.load_data()
T = np.load(os.path.join(HERE, "pert_tables.npz"))
P = {k[5:]: T[k] for k in T.files if k.startswith("data_")}
PG = {k[5:]: T[k] for k in T.files if k.startswith("grid_")}
bgrid = T["bgrid"]
FIT = json.load(open(os.path.join(HERE, "fit_results.json")))
AD = json.load(open(os.path.join(HERE, "ad_postfits.json")))
delta = P["nf5"] - P["nf4"]
COVSYST = np.outer(delta, delta)

# ---------------------------------------------------------------- tunes
TUNES = [
    dict(
        label="Tackmann/Cridge (AN)",
        short="Tackmann",
        lam=dict(linf=1.6853, l2=0.0870, l4=0.0074),
        names=["linf", "l2", "l4"],
        cov=KF.TACKMANN_COV,
    )
]
for e in AD:
    p = e["params"]
    names_map = {"lambda2_nu": "l2", "lambda4_nu": "l4"}
    cov = np.array(e["cov_physical"])
    cn = e["cov_names"]
    idx = [cn.index(n) for n in ("lambda2_nu", "lambda4_nu")]
    TUNES.append(
        dict(
            label=e["name"],
            short=e["name"].split()[-1],
            lam=dict(
                linf=2.0, l2=p["lambda2_nu"]["physical"], l4=p["lambda4_nu"]["physical"]
            ),
            names=["l2", "l4"],
            cov=cov[np.ix_(idx, idx)],
        )
    )
TUNES.append(
    dict(
        label="SCETlib AD anchor / FranksVals (card)",
        short="anchor",
        lam=dict(linf=2.0, l2=0.15, l4=0.0),
        names=["l2", "l4"],
        cov=np.zeros((2, 2)),
    )
)


def np_jac(lam, names, b):
    J = []
    for n in names:
        h = 1e-6 * max(1.0, abs(lam[n]))
        lp, lm = dict(lam), dict(lam)
        lp[n] += h
        lm[n] -= h
        J.append(
            (
                KF.np_zeta(b, lp["linf"], lp["l2"], lp["l4"])
                - KF.np_zeta(b, lm["linf"], lm["l2"], lm["l4"])
            )
            / (2 * h)
        )
    return np.array(J).T


def chi2_fixed(lam, ks=("k1",), pert="nf5", extra=None, tune_cov=None, names=None):
    y = D["y"] - P[pert] - KF.np_zeta(D["b"], lam["linf"], lam["l2"], lam["l4"])
    cov = D["cov"].copy()
    if extra is not None:
        cov = cov + extra
    if tune_cov is not None:
        J = np_jac(lam, names, D["b"])
        cov = cov + J @ tune_cov @ J.T
    X = (
        np.column_stack(
            [{"k1": D["a"] / D["b"], "k2": (D["a"] / D["b"]) ** 2}[k] for k in ks]
        )
        if ks
        else None
    )
    W = np.linalg.inv(cov)
    if X is not None:
        th = np.linalg.solve(X.T @ W @ X, X.T @ W @ y)
        r = y - X @ th
    else:
        th, r = [], y
    return float(r @ W @ r), list(np.atleast_1d(th))


def zsig(dchi2, dof):
    p = chi2dist.sf(max(dchi2, 0), dof)
    return p, float(norm.isf(p / 2)) if p > 0 else np.inf


lines = []


def pr(s=""):
    print(s)
    lines.append(s)


ref_free = FIT["tanh2 | linf free | k1"]["chi2"]
ref_l2 = FIT["tanh2 | linf=2 | k1"]["chi2"]
ref_l16 = FIT["tanh2 | linf=1.6853 | k1"]["chi2"]
ref_free_k2 = FIT["tanh2 | linf free | k2"]["chi2"]
ref_l2_k2 = FIT["SYST k2, linf=2"]["chi2"]
pr(
    f"reference minima (k1): linf free {ref_free:.2f}; linf=2 {ref_l2:.2f}; linf=1.6853 {ref_l16:.2f}"
)
pr(
    "Columns: chi2 at the tune (k1 floated), Delta vs free-linf best (3 dof), Delta vs best at the tune's own "
    "linf (2 dof) -> Gaussian-equivalent sigma; chi2 incl. the tune's own covariance; k2-only variant; "
    "nf-syst-in-cov variant."
)
out = []
for t in TUNES:
    lam = t["lam"]
    c, th = chi2_fixed(lam)
    ref_same = ref_l16 if abs(lam["linf"] - 1.6853) < 1e-6 else ref_l2
    d3, d2 = c - ref_free, c - ref_same
    p3, z3 = zsig(d3, 3)
    p2, z2 = zsig(d2, 2)
    cc, _ = chi2_fixed(lam, tune_cov=t["cov"], names=t["names"])
    ck2, _ = chi2_fixed(lam, ks=("k2",))
    csy, _ = chi2_fixed(lam, extra=COVSYST)
    c4, _ = chi2_fixed(lam, pert="nf4")
    ent = dict(
        label=t["label"],
        lam=lam,
        chi2=c,
        k1=th[0],
        d_free=d3,
        z_free=z3,
        d_same=d2,
        z_same=z2,
        chi2_with_tune_cov=cc,
        chi2_k2=ck2,
        d_same_k2=ck2 - (ref_l2_k2 if lam["linf"] == 2.0 else np.nan),
        chi2_nfsyst=csy,
        chi2_nf4=c4,
    )
    out.append(ent)
    pr(
        f"{t['label']:46s} l2={lam['l2']:+.4f} l4={lam['l4']:+.5f} linf={lam['linf']:.4f} | chi2={c:6.2f} k1={th[0]:+.3f} "
        f"| d3={d3:6.2f} ({z3:.1f}s) | d2={d2:6.2f} ({z2:.1f}s) | chi2(+tune cov)={cc:6.2f} | k2: {ck2:6.2f} "
        f"| nf-syst cov: {csy:6.2f} | nf4: {c4:6.2f}"
    )


# ---------------------------------------------------------------- posterior samples (Metropolis, flat priors)
def logL(x, free, fixed, pert="nf5", mask=None):
    p = dict(fixed)
    p.update(dict(zip(free, x)))
    if p["linf"] <= 0.05 or p["linf"] > 20:
        return -np.inf
    if fixed.get("_phys") and (p["l2"] < 0 or p["l4"] < 0):
        return -np.inf
    m = np.ones(len(D["b"]), bool) if mask is None else mask
    y = (
        D["y"][m]
        - P[pert][m]
        - KF.np_zeta(D["b"][m], p["linf"], p["l2"], p["l4"], p.get("l6", 0.0))
        - p.get("k1", 0) * D["a"][m] / D["b"][m]
        - p.get("k2", 0) * (D["a"][m] / D["b"][m]) ** 2
    )
    return (
        -0.5 * float(y @ WINV[np.ix_(m, m)] @ y)
        if mask is not None
        else -0.5 * float(y @ WINV @ y)
    )


WINV = np.linalg.inv(D["cov"])


def mcmc(free, fixed, x0, step, n=120000, seed=1, burn=10000, thin=10):
    rng = np.random.default_rng(seed)
    x = np.array(x0, float)
    lp = logL(x, free, fixed)
    chain = []
    acc = 0
    for i in range(n):
        xn = x + step @ rng.normal(size=len(x))
        lpn = logL(xn, free, fixed)
        if np.log(rng.uniform()) < lpn - lp:
            x, lp = xn, lpn
            acc += 1
        if i >= burn and i % thin == 0:
            chain.append(x.copy())
    return np.array(chain), acc / n


def chol_step(label, scale=0.6):
    C = np.array(FIT[label]["cov"])
    return scale * np.linalg.cholesky(C + 1e-12 * np.eye(len(C)))


samples = {}
# A: nominal, linf free (flat prior on (0.05, 20]); Hessian at the bound is useless -> hand step
free = ["linf", "l2", "l4", "k1"]
stepA = np.diag([0.8, 0.02, 0.0015, 0.03])
chA, aA = mcmc(free, {}, [2.0, 0.18, -0.005, 0.24], stepA, n=300000)
samples["A_linffree"] = (free, chA)
pr(f"\nMCMC A (tanh2, linf free in (0.05,20], k1): acc {aA:.2f}, N={len(chA)}")
# B: linf = 2 frozen (the scetlib_ad config)
free = ["l2", "l4", "k1"]
chB, aB = mcmc(
    free, {"linf": 2.0}, [0.18, -0.006, 0.24], chol_step("tanh2 | linf=2 | k1")
)
samples["B_linf2"] = (free, chB)
pr(f"MCMC B (tanh2, linf=2, k1): acc {aB:.2f}")
# B_phys: linf=2 + physical (l2>=0, l4>=0)
chBp, aBp = mcmc(
    free,
    {"linf": 2.0, "_phys": True},
    [0.14, 0.001, 0.21],
    chol_step("tanh2 | linf=2 | k1"),
)
samples["Bphys_linf2"] = (free, chBp)
pr(f"MCMC B_phys (linf=2, l2>=0, l4>=0, k1): acc {aBp:.2f}")
# C: linf = 1.6853 frozen (the old lat-cov config)
chC, aC = mcmc(
    free, {"linf": 1.6853}, [0.18, -0.005, 0.24], chol_step("tanh2 | linf=1.6853 | k1")
)
samples["C_linf16853"] = (free, chC)

for key, (free, ch) in samples.items():
    q = np.percentile(ch, [2.5, 16, 50, 84, 97.5], axis=0)
    pr(
        f"  {key}: "
        + "; ".join(
            f"{n}: med {q[2, i]:+.4f} [68% {q[1, i]:+.4f},{q[3, i]:+.4f}] [95% {q[0, i]:+.4f},{q[4, i]:+.4f}]"
            for i, n in enumerate(free)
        )
    )
    if "l2" in free and "l4" in free:
        i2, i4 = free.index("l2"), free.index("l4")
        cc = np.corrcoef(ch[:, i2], ch[:, i4])[0, 1]
        pr(
            f"     posterior mean (l2,l4) = ({ch[:, i2].mean():+.4f}, {ch[:, i4].mean():+.5f}), sd = ({ch[:, i2].std():.4f}, "
            f"{ch[:, i4].std():.5f}), rho = {cc:+.3f}"
        )


# ---------------------------------------------------------------- kernel-space curves on bgrid
def np_curve(linf, l2, l4, l6=0.0):
    return KF.np_zeta(bgrid, linf, l2, l4, l6)


bands = dict(
    bgrid=bgrid, pert_nf5=PG["nf5"], pert_nf4=PG["nf4"], pert_mu1=PG["nf5_mu1match"]
)
for key, (free, ch) in samples.items():
    fx = {
        "A_linffree": {},
        "B_linf2": {"linf": 2.0},
        "Bphys_linf2": {"linf": 2.0},
        "C_linf16853": {"linf": 1.6853},
    }[key]
    sub = ch[:: max(1, len(ch) // 4000)]
    curves = []
    for x in sub:
        p = dict(fx)
        p.update(dict(zip(free, x)))
        curves.append(np_curve(p["linf"], p["l2"], p["l4"]))
    curves = np.array(curves)
    bands[f"lat_{key}_np"] = np.percentile(curves, [2.5, 16, 50, 84, 97.5], axis=0)
# best-fit curves
for lab in [
    "tanh2 | linf free | k1",
    "tanh2 | linf=2 | k1",
    "tanh2 | l4=0, linf=2 | k1",
    "tanh6 | linf free | k1",
]:
    x = dict(dict(linf=1.6853, l2=0, l4=0, l6=0), **FIT[lab]["fixed"], **FIT[lab]["x"])
    bands["best_" + lab.replace(" ", "").replace("|", "_").replace("=", "")] = np_curve(
        x["linf"], x["l2"], x["l4"], x.get("l6", 0)
    )
rng = np.random.default_rng(7)
for i, t in enumerate(TUNES):
    lam = t["lam"]
    cen = np_curve(lam["linf"], lam["l2"], lam["l4"])
    if np.any(t["cov"]):
        xs = rng.multivariate_normal([lam[n] for n in t["names"]], t["cov"], size=4000)
        cs = []
        for x in xs:
            p = dict(lam)
            p.update(dict(zip(t["names"], x)))
            if p["linf"] <= 0:
                continue
            cs.append(np_curve(p["linf"], p["l2"], p["l4"]))
        q = np.percentile(np.array(cs), [2.5, 16, 50, 84, 97.5], axis=0)
    else:
        q = np.vstack([cen] * 5)
    bands[f"tune{i}_np"] = q
    bands[f"tune{i}_cen"] = cen
json.dump(
    dict(
        tunes=[
            dict(
                label=t["label"],
                lam=t["lam"],
                names=t["names"],
                cov=np.asarray(t["cov"]).tolist(),
            )
            for t in TUNES
        ],
        compat=out,
    ),
    open(os.path.join(HERE, "compat.json"), "w"),
    indent=1,
)
np.savez(os.path.join(HERE, "bands.npz"), **bands)
for key, (free, ch) in samples.items():
    np.save(os.path.join(HERE, f"chain_{key}.npy"), ch)
# kernel-space numbers at reference b
pr("\nNP part gamma_zeta^NP at reference b_T [fm] (68% band):")
bref = [0.2, 0.3, 0.45, 0.6, 0.75, 0.9]
ib = [int(np.argmin(abs(bgrid - x))) for x in bref]
for key in ["lat_A_linffree_np", "lat_B_linf2_np", "lat_Bphys_linf2_np"] + [
    f"tune{i}_np" for i in range(len(TUNES))
]:
    q = bands[key]
    name = (
        key
        if not key.startswith("tune")
        else TUNES[int(key[4:].split("_")[0])]["label"]
    )
    pr(
        f"  {name:46s} "
        + "  ".join(
            f"{bgrid[j]:.2f}:{q[2, j]:+.3f}[{q[1, j]:+.3f},{q[3, j]:+.3f}]" for j in ib
        )
    )
open(os.path.join(HERE, "compat.txt"), "w").write("\n".join(lines) + "\n")
