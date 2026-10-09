#!/usr/bin/env python3
"""Refit of the ASWZ 2024 (arXiv:2402.06725) lattice CS kernel.

Model (paper Eq. CSkernelparam / DNP, main.tex L312-331):
  gamma(bT, mu, a) = -2 D_res(b*, mu) - 2 bT b* [c0 + c1 ln(b*/B_NP)]
                     + k1 a/bT + k2 (a/bT)^2
  b* = bT / sqrt(1 + bT^2/B_NP^2),  mu_b* = 2 e^{-gamma_E} / b*
  D_res (supp. Eq. dres) = int_{mu_b*}^{mu} dmu'/mu' Gamma_cusp[a_s(mu')] + d[a_s(mu_b*)]
  mu = 2 GeV, n_f = 4, alpha_s(2 GeV) = 0.293, Gamma_0..3, d_2..3 (N3LL).
For fixed B_NP the model is LINEAR in (c0, c1, k1, k2) -> exact GLS.

Usage: python3 cs_fit.py [--dres numeric|paper] [--noplots] [--dshift-bug]
"""
import argparse
import importlib.util
import functools
import json
import os

import numpy as np
from scipy.integrate import quad, solve_ivp
from scipy.optimize import minimize_scalar
from scipy.special import zeta

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
FM = 5.067730716  # GeV^-1 per fm
GE = np.euler_gamma
NF = 4
MU = 2.0
AS0 = 0.293
z3, z5 = zeta(3), zeta(5)
pi = np.pi
ENS = [("L32", 0.15), ("L48", 0.12), ("L64", 0.09)]
DSHIFT_BUG = False  # set by --dshift-bug (old, wrong d-index reading)
BNP_BOUNDS = (1.0, 2.5)  # GeV^-1

# --- anomalous dimensions, a_s = alpha_s/(4 pi) (supp. Eq. cusp-pert, beta) ---
G = [
    16 / 3,
    1072 / 9 - 16 * pi**2 / 3 - 160 / 27 * NF,
    352 * z3
    + 176 * pi**4 / 15
    - 2144 * pi**2 / 9
    + 1960
    + NF * (-832 * z3 / 9 + 320 * pi**2 / 27 - 5104 / 27)
    - 64 / 81 * NF**2,
    (
        -1536 * z3**2
        - 704 * pi**2 * z3
        + 28032 * z3
        - 34496 * z5 / 3
        + 337112 / 9
        - 178240 * pi**2 / 27
        + 3608 * pi**4 / 5
        - 32528 * pi**6 / 945
    )
    + NF
    * (
        1664 * pi**2 * z3 / 9
        - 616640 * z3 / 81
        + 25472 * z5 / 9
        - 1377380 / 243
        + 51680 * pi**2 / 81
        - 2464 * pi**4 / 135
    )
    + NF**2 * (16640 * z3 / 81 + 71500 / 729 - 1216 * pi**2 / 243 - 416 * pi**4 / 405)
    + NF**3 * (256 * z3 / 81 - 128 / 243),
]
# Non-cusp rapidity AD, d[a_s] = sum_n D[n] a_s^{n+1}.
# NB paper index typo: the supplement writes "d_0 = d_1 = 0, d_2 = -56 z3 + 1616/27 - 224/81 n_f, d_3 = ...".
# But that "d_2" is the TWO-loop coefficient d^(2,0) = C_F[C_A(404/27 - 14 z3) - 112/27 T_F n_f]
# (the rapidity AD non-cusp term starts at a_s^2), so with the same one-loop start as Gamma_n
# it belongs at a_s^2 and "d_3" (three-loop) at a_s^3.  Read literally (as this script did
# before 2026-09-24) the 2-loop term sits at a_s^3 and 3-loop at a_s^4:
# -2 D_res(0.9 fm) goes -0.633 (wrong) -> -0.382 (right).  --dshift-bug restores the old behaviour.
_d2 = -56 * z3 + 1616 / 27 - 224 / 81 * NF
_d3 = (
    (
        176 * pi**2 * z3 / 3
        - 24656 * z3 / 9
        + 1152 * z5
        + 594058 / 243
        - 6392 * pi**2 / 81
        - 154 * pi**4 / 45
    )
    + NF * (7856 * z3 / 81 - 166316 / 729 + 824 * pi**2 / 243 + 4 * pi**4 / 405)
    + NF**2 * (64 * z3 / 27 + 3712 / 2187)
)
D = [0.0, _d2, _d3, 0.0]
D_BUGGY = [0.0, 0.0, _d2, _d3]
B = [
    11 - 2 / 3 * NF,
    102 - 38 / 3 * NF,
    2857 / 2 - 5033 / 18 * NF + 325 / 54 * NF**2,
    3564 * z3
    + 149753 / 6
    - NF * (6508 * z3 / 27 + 1078361 / 162)
    + NF**2 * (6472 * z3 / 81 + 50065 / 162)
    + 1093 / 729 * NF**3,
]


_AS_SOL = None


def as_numeric(mu):
    """a_s(mu) from 4-loop beta, d a_s/d ln mu = -2 sum b_n a_s^{n+2} (one dense solve, cached)."""
    global _AS_SOL
    if _AS_SOL is None:
        a0 = AS0 / (4 * pi)
        f = lambda t, a: [-2 * sum(B[n] * a[0] ** (n + 2) for n in range(4))]
        _AS_SOL = solve_ivp(
            f, [0.0, np.log(0.3 / MU)], [a0], rtol=1e-12, atol=1e-15, dense_output=True
        )
    return float(_AS_SOL.sol(np.log(mu / MU))[0])


def as_paper(mu):
    """Paper's closed-form 4-loop a_s (supp. eq. after K), X = 1 + 2 a0 b0 ln(mu/mu0)."""
    a0 = AS0 / (4 * pi)
    b0, b1, b2, b3 = B
    X = 1 + 2 * a0 * b0 * np.log(mu / MU)
    L = np.log(X)
    inv = X / a0 + b1 * L / b0
    inv += a0 * (b1**2 / b0**2 * (1 / X + L / X - 1) + b2 / b0 * (1 - 1 / X))
    inv += a0**2 * (
        -(b1**3) / (2 * b0**3) * L**2 / X**2
        + b1 * b2 / b0**2 * L / X**2
        + (1 - 1 / X)
        * (-b1 * b2 / b0**2 + b3 / (2 * b0) * (1 / X + 1) + 0.5 * (1 - 1 / X))
        - (1 - (b1 / b0) ** 3) * (1 - X) ** 2 / (2 * X**2)
    )
    return 1 / inv


def K_paper(mu, mu0, asf):
    a = asf(mu)
    r = a / asf(mu0)
    b0, b1, b2, b3 = B
    G0, G1, G2, G3 = G
    t = np.log(r) + a * (G1 / G0 - b1 / b0) * (r - 1)
    t += (
        0.5
        * a**2
        * (b1**2 / b0**2 - b1 * G1 / (b0 * G0) - b2 / b0 + G2 / G0)
        * (r**2 - 1)
    )
    t += (
        (1 / 3)
        * a**3
        * (
            G1 / G0 * (b1**2 / b0**2 - b2 / b0)
            - b1 / b0 * (b1**2 / b0**2 - 2 * b2 / b0 + G2 / G0)
            - b3 / b0
            + G3 / G0
        )
        * (r**3 - 1)
    )
    return -G0 / b0 * t


@functools.lru_cache(maxsize=None)
def Dres(bstar, mode):
    """D_res(b*, mu=2 GeV); bstar in GeV^-1."""
    mub = 2 * np.exp(-GE) / bstar
    if mode == "numeric":
        asf = as_numeric
        cusp = lambda lnm: sum(G[n] * asf(np.exp(lnm)) ** (n + 1) for n in range(4))
        K2 = quad(cusp, np.log(mub), np.log(MU), epsabs=1e-10)[0]  # = K/2
    else:
        asf = as_paper
        K2 = 0.5 * K_paper(MU, mub, asf)
    ab = asf(mub)
    Dl = D_BUGGY if DSHIFT_BUG else D
    return K2 + sum(Dl[n] * ab ** (n + 1) for n in range(4))


# ------------------------------------------------------------------ data
def load():
    out = []
    for name, a in ENS:
        d = np.loadtxt(
            os.path.join(DATA, "CS_lattice_results", f"CS_Pz_x_ave_{name}.csv"),
            delimiter=",",
        )
        c = np.loadtxt(
            os.path.join(
                DATA, "CS_lattice_results", f"CS_Pz_x_ave_{name}_covariance.csv"
            ),
            delimiter=",",
        )
        out.append(dict(name=name, a=a, b=d[:, 0], y=d[:, 1], s=d[:, 2], cov=c))
    b = np.concatenate([e["b"] for e in out])
    y = np.concatenate([e["y"] for e in out])
    s = np.concatenate([e["s"] for e in out])
    a = np.concatenate([np.full(len(e["b"]), e["a"]) for e in out])
    ens = np.concatenate([np.full(len(e["b"]), i) for i, e in enumerate(out)])
    n = len(b)
    cov = np.zeros((n, n))
    i0 = 0
    for e in out:
        m = len(e["b"])
        cov[i0 : i0 + m, i0 : i0 + m] = e["cov"]
        i0 += m
    cont = np.loadtxt(
        os.path.join(DATA, "CS_ASWZ_2024_data-1.csv"), delimiter=",", skiprows=1
    )
    return out, dict(b=b, y=y, s=s, a=a, ens=ens, cov=cov, cont=cont)


# ------------------------------------------------------------------ fits
PARS = ["c0", "c1", "k1", "k2"]


def design(b_fm, a_fm, BNP, mode):
    bt = b_fm * FM
    bs = bt / np.sqrt(1 + bt**2 / BNP**2)
    off = np.array([-2 * Dres(float(round(x, 12)), mode) for x in bs])
    cols = dict(
        c0=-2 * bt * bs,
        c1=-2 * bt * bs * np.log(bs / BNP),
        k1=a_fm / b_fm,
        k2=(a_fm / b_fm) ** 2,
    )
    return off, cols


def gls(y, cov, off, cols, free):
    X = np.column_stack([cols[p] for p in free])
    W = np.linalg.inv(cov)
    C = np.linalg.inv(X.T @ W @ X)
    th = C @ X.T @ W @ (y - off)
    r = y - off - X @ th
    return th, C, float(r @ W @ r)


def fit(y, cov, b, a, free, BNP=2.0, BNP_free=False, mode="numeric"):
    if BNP_free:
        f = lambda B_: fit(y, cov, b, a, free, B_, False, mode)["chi2"]
        # upper bound: mu_b*(b_T=0.9 fm) must stay above the 4-loop n_f=4 Landau pole (~0.47 GeV)
        res = minimize_scalar(
            f, bounds=BNP_BOUNDS, method="bounded", options=dict(xatol=1e-5)
        )
        BNP = res.x
        # sigma(B_NP) from profile chi2 curvature
        h = 1e-2
        c2 = (f(BNP + h) - 2 * f(BNP) + f(BNP - h)) / h**2
        sB = np.sqrt(2 / c2) if c2 > 0 else np.nan
    off, cols = design(b, a, BNP, mode)
    th, C, chi2 = gls(y, cov, off, cols, free)
    npar = len(free) + (1 if BNP_free else 0)
    out = dict(
        free=list(free) + (["B_NP"] if BNP_free else []),
        BNP=BNP,
        theta=dict(zip(free, th)),
        err=dict(zip(free, np.sqrt(np.diag(C)))),
        cov=C,
        chi2=chi2,
        ndf=len(y) - npar,
        aic=chi2 + 2 * npar,
    )
    if BNP_free:
        out["err_BNP"] = sB
    return out


def fmt(r):
    s = ", ".join(f"{p}={r['theta'][p]:+.4f}({r['err'][p]:.4f})" for p in r["theta"])
    if "err_BNP" in r:
        s += f", B_NP={r['BNP']:.3f}({r['err_BNP']:.3f})"
        if abs(r["BNP"] - BNP_BOUNDS[1]) < 1e-3 or abs(r["BNP"] - BNP_BOUNDS[0]) < 1e-3:
            s += " [AT BOUND]"
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dres", default="numeric", choices=["numeric", "paper"])
    ap.add_argument("--noplots", action="store_true")
    ap.add_argument(
        "--dshift-bug",
        action="store_true",
        help="reproduce the pre-2026-09-24 WRONG reading of the paper's d_n index (record only)",
    )
    args = ap.parse_args()
    global DSHIFT_BUG
    DSHIFT_BUG = args.dshift_bug
    mode = args.dres
    ens, D_ = load()
    b, y, a, cov, s = D_["b"], D_["y"], D_["a"], D_["cov"], D_["s"]
    cont = D_["cont"]
    res = {}

    print(f"alpha_s check: numeric vs paper closed form at mu = 0.5, 0.6, 1, 4 GeV")
    for m in [0.5, 0.6, 1.0, 4.0]:
        print(f"  mu={m}: {4*pi*as_numeric(m):.4f}  {4*pi*as_paper(m):.4f}")
    print(
        "D_res numeric vs paper at b*=0.3,1,2 GeV^-1:",
        [
            (round(Dres(x, "numeric"), 4), round(Dres(x, "paper"), 4))
            for x in [0.3, 1, 2]
        ],
    )

    # --- 1. diagonal errors in the per-ensemble file == sqrt(diag cov)?
    print("\nmax |s - sqrt(diag cov)|:", np.max(np.abs(s - np.sqrt(np.diag(cov)))))

    # --- 2. continuum-file hypothesis
    assert np.allclose(cont[:, 0], b, atol=1e-9)
    shift = y - cont[:, 1]
    k1_implied = shift / (a / b)
    print("continuum file: implied k1 per point:", np.round(k1_implied, 6))
    print(
        "  k1 mean, std:",
        k1_implied.mean(),
        k1_implied.std(),
        " sigma equal:",
        np.max(np.abs(cont[:, 2] - s)),
    )
    res["k1_implied"] = float(k1_implied.mean())

    # --- 3. correlation matrices
    for e in ens:
        sd = np.sqrt(np.diag(e["cov"]))
        corr = e["cov"] / np.outer(sd, sd)
        off = corr[~np.eye(len(sd), dtype=bool)]
        print(
            f"{e['name']}: offdiag corr min/median/max = {off.min():+.3f} {np.median(off):+.3f} {off.max():+.3f}"
        )
        e["corr"] = corr

    # --- 4. fit table on per-ensemble data, full covariance and diag-only
    cfgs = [
        ("c0", ["c0"], False),
        ("c0,k1 [paper AIC-best]", ["c0", "k1"], False),
        ("c0,k2", ["c0", "k2"], False),
        ("c0,k1,k2", ["c0", "k1", "k2"], False),
        ("c0,c1,k1", ["c0", "c1", "k1"], False),
        ("c0,k1,B_NP", ["c0", "k1"], True),
        ("c0,c1,k1,k2,B_NP", ["c0", "c1", "k1", "k2"], True),
    ]
    rows = []
    for covname, C in [("full", cov), ("diag", np.diag(np.diag(cov)))]:
        print(f"\n=== per-ensemble fits, {covname} covariance, D_res={mode} ===")
        for lab, free, bf in cfgs:
            r = fit(y, C, b, a, free, BNP_free=bf, mode=mode)
            print(
                f"  {lab:22s} chi2={r['chi2']:6.2f} ndf={r['ndf']:2d} chi2/ndf={r['chi2']/r['ndf']:.3f} "
                f"AIC={r['aic']:6.2f}  {fmt(r)}"
            )
            rows.append(
                dict(
                    cov=covname,
                    model=lab,
                    chi2=r["chi2"],
                    ndf=r["ndf"],
                    aic=r["aic"],
                    theta=r["theta"],
                    err=r["err"],
                    BNP=r["BNP"],
                    err_BNP=r.get("err_BNP"),
                )
            )
            res[(covname, lab)] = r

    # --- 5. what the continuum file loses
    print("\n=== information loss, model (c0) at a=0, B_NP=2 ===")
    ycont = cont[:, 1]
    r_ref = res[("full", "c0,k1 [paper AIC-best]")]
    rho = r_ref["cov"][0, 1] / np.sqrt(r_ref["cov"][0, 0] * r_ref["cov"][1, 1])
    print(
        f"  (b) per-ensemble + free k1, full cov : {fmt(r_ref)}  rho(c0,k1)={rho:+.3f}"
    )
    ra = fit(ycont, np.diag(cont[:, 2] ** 2), b, np.zeros_like(a), ["c0"], mode=mode)
    print(
        f"  (a) continuum file, diag errors      : {fmt(ra)} chi2={ra['chi2']:.2f}/{ra['ndf']}"
    )
    rc = fit(ycont, cov, b, np.zeros_like(a), ["c0"], mode=mode)
    print(
        f"  (c) continuum file, full ens. cov    : {fmt(rc)} chi2={rc['chi2']:.2f}/{rc['ndf']}"
    )
    # (d) continuum file + k1 nuisance with the published prior 0.22(8) wrt the file's k1
    #     = shift back by k1_implied and refit with Gaussian constraint (double-counting check)
    Xk = a / b
    Cd = np.diag(cont[:, 2] ** 2) + 0.08**2 * np.outer(Xk, Xk)
    rd = fit(ycont, Cd, b, np.zeros_like(a), ["c0"], mode=mode)
    print(f"  (d) continuum file, diag + k1 prior 0.08 as correlated syst: {fmt(rd)}")
    Cd2 = cov + 0.08**2 * np.outer(Xk, Xk)
    rd2 = fit(ycont, Cd2, b, np.zeros_like(a), ["c0"], mode=mode)
    print(
        f"  (e) continuum file, full cov + k1 prior 0.08 as correlated syst: {fmt(rd2)}"
    )
    loss = {
        k: dict(c0=v["theta"]["c0"], err=v["err"]["c0"], chi2=v["chi2"], ndf=v["ndf"])
        for k, v in dict(
            b_full_k1=r_ref,
            a_cont_diag=ra,
            c_cont_fullcov=rc,
            d_cont_diag_k1syst=rd,
            e_cont_full_k1syst=rd2,
        ).items()
    }

    # --- 6. b_T < 0.2 fm / 0.9 fm edge
    print("\n=== sensitivity to b_T range, (c0,k1) full cov ===")
    rng = {}
    for lo, hi in [(0.0, 1.0), (0.2, 1.0), (0.0, 0.8), (0.2, 0.8), (0.25, 1.0)]:
        m = (b >= lo - 1e-9) & (b <= hi + 1e-9)
        r = fit(y[m], cov[np.ix_(m, m)], b[m], a[m], ["c0", "k1"], mode=mode)
        print(
            f"  b in [{lo},{hi}] npts={m.sum():2d}: chi2/ndf={r['chi2']:.2f}/{r['ndf']}  {fmt(r)}"
        )
        rng[f"{lo}-{hi}"] = dict(
            n=int(m.sum()), chi2=r["chi2"], ndf=r["ndf"], theta=r["theta"], err=r["err"]
        )
    # pull of each point wrt best fit (paper model)
    off, cols = design(b, a, 2.0, mode)
    pred = off + r_ref["theta"]["c0"] * cols["c0"] + r_ref["theta"]["k1"] * cols["k1"]
    print("  pulls (diag):", np.round((y - pred) / s, 2))

    with open(
        os.path.join(
            HERE, f"fit_results_{mode}{'_dshiftbug' if DSHIFT_BUG else ''}.json"
        ),
        "w",
    ) as f:
        json.dump(
            dict(
                k1_implied=res["k1_implied"],
                table=rows,
                loss=loss,
                ranges=rng,
                rho_c0_k1=rho,
            ),
            f,
            indent=1,
            default=float,
        )

    if not args.noplots:
        plots(ens, D_, res, r_ref, ra, mode, args)


def plots(ens, D_, res, r_ref, ra, mode, args):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from wums import (
        plot_tools,
    )  # noqa: F401  (loads the mplhep style up front: same style on all plots)

    plt.rcParams.update(
        {"axes.labelsize": 16, "xtick.labelsize": 13, "ytick.labelsize": 13}
    )
    spec = importlib.util.spec_from_file_location(
        "plot_output",
        "/home/submit/lavezzo/alphaS/PR710/WRemnants/wremnants/postprocessing/scetlib_np/plot_output.py",
    )
    po = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(po)
    meta = dict(
        dres=mode,
        dshift_bug=DSHIFT_BUG,
        mu="2 GeV",
        nf=4,
        alphas_2GeV=AS0,
        BNP="2 GeV^-1",
        data="/work/submit/lavezzo/cs_kernel/CS_lattice_results.tar",
    )
    sfx = "_dshiftbug" if DSHIFT_BUG else ""
    # paper Fig. 2 style: a=0.15 orange circles, 0.12 green squares, 0.09 purple triangles
    sty = {
        "L32": ("tab:orange", "o"),
        "L48": ("tab:green", "s"),
        "L64": ("tab:purple", "^"),
    }
    bb = np.linspace(0.02, 1.0, 300)
    th, C = r_ref["theta"], r_ref["cov"]
    ylab = r"$\gamma_q^{\overline{\rm MS}}(b_T,\mu=2\,{\rm GeV}%s)$"

    def curve(aa, c0, k1):
        off, cl = design(bb, np.full_like(bb, aa), 2.0, mode)
        return off + c0 * cl["c0"] + k1 * cl["k1"], cl

    c0v, cl = curve(0.0, th["c0"], th["k1"])
    # full (c0,k1) covariance propagated at a=0 (k1 column vanishes at a=0, so only C[c0,c0] survives)
    J = np.column_stack([cl["c0"], cl["k1"]])
    sig = np.sqrt(np.einsum("ij,jk,ik->i", J, C, J))
    sig_paper = np.abs(cl["c0"]) * 0.012  # paper-quoted sigma(c0), for comparison
    dx = {"L32": 0.0, "L48": 0.0, "L64": 0.0}

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 10))
    for e in ens:
        c, m = sty[e["name"]]
        lab = f"a = {e['a']} fm"
        ax1.errorbar(
            e["b"],
            e["y"],
            e["s"],
            fmt=m,
            mfc="none",
            color=c,
            ms=7,
            capsize=2,
            label=lab,
        )
        cv, _ = curve(e["a"], th["c0"], th["k1"])
        ax1.plot(bb, cv, "--", color=c, lw=1.5)
        ax2.errorbar(
            e["b"],
            e["y"] - th["k1"] * e["a"] / e["b"],
            e["s"],
            fmt=m,
            mfc="none",
            color=c,
            ms=7,
            capsize=2,
            label=lab,
        )
    ax1.plot(bb, c0v, "k-", lw=2, label=r"$a=0$")
    ax2.plot(
        bb,
        c0v,
        "-",
        color="gray",
        lw=1.5,
        label=rf"$a=0$: $c_0$={th['c0']:.4f}({r_ref['err']['c0']:.4f}) GeV$^2$, $\hat k_1$={th['k1']:.3f}({r_ref['err']['k1']:.3f})",
    )
    ax2.fill_between(
        bb,
        c0v - sig,
        c0v + sig,
        color="tab:red",
        alpha=0.2,
        lw=0,
        label=r"1$\sigma$ ($c_0,k_1$ cov), ours",
    )
    ax2.plot(bb, c0v - sig_paper, ":", color="tab:red", lw=1)
    ax2.plot(
        bb,
        c0v + sig_paper,
        ":",
        color="tab:red",
        lw=1,
        label=r"$\pm\sigma(c_0)$=0.012 (paper-quoted)",
    )
    for ax, yl in [(ax1, ylab % ",a"), (ax2, ylab % "")]:
        ax.axhline(0, color="gray", lw=0.5)
        ax.set_xlim(0, 1)
        ax.set_ylim(-2, 1)
        ax.set_xlabel(r"$b_T$ [fm]")
        ax.set_ylabel(yl)
        ax.legend(fontsize=9, loc="lower left")
    ax1.set_title(
        f"per-ensemble data, fit (c0,k1), B_NP=2 GeV$^{{-1}}$, D_res={mode}, "
        f"$\\chi^2$/ndf={r_ref['chi2']:.2f}/{r_ref['ndf']}",
        fontsize=9,
    )
    ax2.set_title(
        r"$\hat k_1 a/b_T$ subtracted (error bars = raw diagonal)", fontsize=9
    )
    fig.tight_layout()
    po.save_plot(HERE, "paper_fig2_style" + sfx, fig=fig, args=args, meta_info=meta)
    plt.close(fig)

    # (2) continuum file vs a=0 curve from per-ensemble fit and from a diag fit to the file
    fig, ax = plt.subplots(figsize=(7, 5))
    cont = D_["cont"]
    for i, e in enumerate(ens):
        c, m_ = sty[e["name"]]
        m = D_["ens"] == i
        ax.errorbar(
            cont[m, 0],
            cont[m, 1],
            cont[m, 2],
            fmt=m_,
            mfc="none",
            color=c,
            ms=6,
            capsize=2,
            label=f"continuum file, a={e['a']} fm points",
        )
    ax.plot(
        bb,
        c0v,
        "k-",
        label=f"per-ens + free k1 (full cov): c0={th['c0']:.4f}({r_ref['err']['c0']:.4f})",
    )
    ax.fill_between(bb, c0v - sig, c0v + sig, color="k", alpha=0.2)
    ca, cla = curve(0.0, ra["theta"]["c0"], 0.0)
    siga = np.abs(cla["c0"]) * ra["err"]["c0"]
    ax.plot(
        bb,
        ca,
        "r--",
        label=f"continuum file, diag errors: c0={ra['theta']['c0']:.4f}({ra['err']['c0']:.4f})",
    )
    ax.fill_between(bb, ca - siga, ca + siga, color="r", alpha=0.2)
    ax.set_xlabel(r"$b_T$ [fm]")
    ax.set_ylabel(ylab % "")
    ax.set_title(
        "continuum file (= raw - 0.2136 a/b_T) vs per-ensemble fit, B_NP=2 GeV$^{-1}$",
        fontsize=9,
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(-2, 1)
    ax.legend(fontsize=8, loc="lower left")
    po.save_plot(
        HERE, "continuum_file_vs_fit" + sfx, fig=fig, args=args, meta_info=meta
    )
    plt.close(fig)

    # (3) correlation matrices
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.4))
    for axx, e in zip(axs, ens):
        im = axx.imshow(e["corr"], vmin=-1, vmax=1, cmap="RdBu_r")
        lab = [f"{x:.2f}" for x in e["b"]]
        axx.set_xticks(range(len(lab)), lab, rotation=90, fontsize=7)
        axx.set_yticks(range(len(lab)), lab, fontsize=7)
        for i in range(len(lab)):
            for j in range(len(lab)):
                axx.text(
                    j, i, f"{e['corr'][i, j]:.2f}", ha="center", va="center", fontsize=6
                )
        axx.set_title(f"{e['name']} (a={e['a']} fm) correlation, b_T [fm]", fontsize=9)
    fig.colorbar(im, ax=axs, shrink=0.8)
    po.save_plot(HERE, "correlation_matrices", fig=fig, args=args, meta_info=meta)
    plt.close(fig)


if __name__ == "__main__":
    main()
