#!/usr/bin/env python3
"""Cache-free Newton steps from LATFULL8 (old table term, pert=live, syst=Jnf+Jbt) to the native term and its variants,
and the decomposition of old -> new into (kernel: exact -> analytic RGE, table expansion -> exact SCETlib) and
(covariance: old n_f definition / old J -> SCETlib-native rows).

H = inv(C_LATFULL8) with the lattice term's block (alphaS, lambda2_nu, lambda4_nu, resumTNP_gamma_nu, resumTNP_gamma_cusp)
swapped old -> variant; g = variant - old lattice gradient; dx = -H^-1 g. Term derivatives by central FD in theta.
APPROXIMATION (blinding): the terms are evaluated at alpha_s = 0.118 (Delta alpha_s = 0), not at LATFULL8's blinded
alpha_s; the nativecheck.py job repeats the native-term rows AT the point (exact) as the check of this approximation.
Only Delta(alphaS)/sigma_NOM, sigma ratios and the (unblinded) lambdas / TNPs are written.

  O    old term (= LATFULL8's): table pert (exact RGE) + 2nd-order expansion in alpha_s / TNPs, old Jnf + Jbt rows
  K    kernel swap only: SCETlib analytic kernel, exact (no expansion), OLD covariance (old Jnf + Jbt rows)
  N    the native term, default (SCETlib kernel, SCETlib-native Jnf (identified at 1 GeV) + Jbt)
  N variants: Jnf only (no b_T window), Jbt only (no n_f), none, direct_nf+Jbt, nfmatch = 2 GeV (n_f shift -> 0)
Writes ../newton_decomp.json.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
sys.path.insert(0, WREM)
from rabbit import io_tools  # noqa: E402

from wremnants.postprocessing.scetlib_ad import lattice_cs_chi2 as OLD  # noqa: E402
from wremnants.postprocessing.scetlib_ad import lattice_cs_term as NEW  # noqa: E402
from wremnants.postprocessing.scetlib_ad import xsec_backend as xb  # noqa: E402

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
L8 = f"{A}/261006_lattice_chi2_in_fit/fitresults_LATFULL8.hdf5"
NOM = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
CONF = f"{A}/ad_scetlib_caches/pdf62_y35_260921_y25/cache.conf"
BLOCK = (
    "alphaS",
    "lambda2_nu",
    "lambda4_nu",
    "resumTNP_gamma_nu",
    "resumTNP_gamma_cusp",
)
MAP = dict(
    alphaS=(0.118, 0.002),
    lambda2_nu=(0.15, 0.1),
    lambda4_nu=(0.0, 0.5),
    resumTNP_gamma_nu=(0.0, 1.0),
    resumTNP_gamma_cusp=(0.0, 1.0),
)
SC = dict(
    alphaS="alphas",
    lambda2_nu="np_gnu_lambda2",
    lambda4_nu="np_gnu_lambda4",
    resumTNP_gamma_nu="tnp_gamma_nu",
    resumTNP_gamma_cusp="tnp_gamma_cusp",
)


def load(p):
    fr = io_tools.get_fitresult(p, None)
    h = fr["parms"].get()
    return (
        [str(n) for n in h.axes[0]],
        np.asarray(h.values(), float),
        np.asarray(fr["cov"].get().values(), float),
    )


def main():
    nN, xN, CN = load(NOM)
    n8, x8, C8 = load(L8)
    sN = np.sqrt(CN[nN.index("alphaS"), nN.index("alphaS")])
    ib = [n8.index(k) for k in BLOCK]
    th8 = x8[ib].copy()
    th8[0] = 0.0  # Delta alpha_s = 0 (blinded); see the docstring
    phys8 = {k: MAP[k][0] + MAP[k][1] * th8[i] for i, k in enumerate(BLOCK)}
    print(
        "LATFULL8 point used (alpha_s at 0.118 by construction):",
        {k: round(v, 6) for k, v in phys8.items() if k != "alphaS"},
    )

    conf, sigma = xb.configure(CONF, threads=8)
    sing, _ = sigma.sub_pieces()
    sing.set_pdf_eig_params(29)
    names = list(sing.gradient_param_names())
    pref = np.array(sing.gradient_central(), float)
    isc = [names.index(SC[k]) for k in BLOCK]

    def pfull(th):
        p = pref.copy()
        for j, k in enumerate(BLOCK):
            p[isc[j]] = MAP[k][0] + MAP[k][1] * th[j]
        return p

    # ---- the terms as functions of the 5 thetas: 1/2 (chi2 - offset)
    old = OLD.LatticeCSCore(syst="Jnf+Jbt")
    old_off = old.fit()[0].fun

    def f_old(th):
        lam = dict(
            lambda_inf_nu=2.0,
            lambda2_nu=MAP["lambda2_nu"][0] + 0.1 * th[1],
            lambda4_nu=0.5 * th[2],
        )
        da = 0.002 * th[0]
        return 0.5 * (
            old.chi2(
                lam,
                da,
                {"resumTNP_gamma_nu": th[3], "resumTNP_gamma_cusp": th[4]},
                mode="live",
            )
            - old_off
        )

    cores = {}
    for key, kw in (
        ("N Jnf+Jbt (default)", dict(syst="Jnf+Jbt")),
        ("N Jnf (no b_T window)", dict(syst="Jnf")),
        ("N Jbt (no n_f syst)", dict(syst="Jbt")),
        ("N none (stat only)", dict(syst="none")),
        ("N direct_nf+Jbt", dict(syst="direct_nf+Jbt")),
        ("N Jnf+Jbt, n_f identified at 2 GeV", dict(syst="Jnf+Jbt", nf_match=2.0)),
    ):
        cores[key] = NEW.LatticeCSNativeCore(sing, pref, require_rules=False, **kw)
    base = cores["N Jnf+Jbt (default)"]

    def f_new(core):
        def f(th):
            return 0.5 * (core.chi2_full(pfull(th)) - core.chi2_min)

        return f

    # K: SCETlib kernel (exact, live) with the OLD covariance
    M_old = old.M

    def f_K(th):
        r = base.zeta(pfull(th)) - old.y
        return 0.5 * (float(r @ M_old @ r) - kmin)

    from scipy.optimize import minimize

    kmin = 0.0
    kmin = float(
        minimize(
            lambda q: 2 * f_K(np.array([0, q[0], q[1], 0, 0])),
            [0.35, -0.012],
            method="Nelder-Mead",
            options=dict(xatol=1e-10, fatol=1e-12),
        ).fun
    )

    variants = {"O old (LATFULL8)": f_old, "K kernel swap only (old cov)": f_K}
    variants.update({k: f_new(c) for k, c in cores.items()})
    steps = np.array([1e-3, 1e-3, 1e-3, 1e-2, 1e-2])

    def gh(f):
        g, H = np.zeros(5), np.zeros((5, 5))
        f0 = f(th8)
        for i in range(5):
            ei = np.eye(5)[i] * steps[i]
            g[i] = (f(th8 + ei) - f(th8 - ei)) / (2 * steps[i])
            H[i, i] = (f(th8 + ei) - 2 * f0 + f(th8 - ei)) / steps[i] ** 2
            for j in range(i):
                ej = np.eye(5)[j] * steps[j]
                H[i, j] = H[j, i] = (
                    f(th8 + ei + ej)
                    - f(th8 + ei - ej)
                    - f(th8 - ei + ej)
                    + f(th8 - ei - ej)
                ) / (4 * steps[i] * steps[j])
        return g, H

    gO, HO = gh(f_old)
    H0 = np.linalg.inv(C8)
    out = dict(
        point={k: float(v) for k, v in phys8.items() if k != "alphaS"},
        approx="terms at Delta alpha_s = 0 (blinded); FD derivatives in theta",
        newton={},
    )
    ia = n8.index("alphaS")
    for key, f in variants.items():
        g, H_ = gh(f)
        H = H0.copy()
        H[np.ix_(ib, ib)] += H_ - HO
        dg = np.zeros(len(n8))
        dg[ib] = g - gO
        dx = -np.linalg.solve(H, dg)
        Cn = np.linalg.inv(H)
        row = dict(
            dalphaS_vs_LATFULL8_over_sigNOM=float(dx[ia] / sN),
            dalphaS_vs_NOMSTIFF_over_sigNOM=float(
                (x8[ia] + dx[ia] - xN[nN.index("alphaS")]) / sN
            ),
            sigma_ratio_vs_NOM=float(np.sqrt(Cn[ia, ia]) / sN),
        )
        for j, k in enumerate(BLOCK[1:], start=1):
            i = ib[j]
            row[k] = float(MAP[k][0] + MAP[k][1] * (x8[i] + dx[i]))
            row[f"d_{k}_over_sigma"] = float(dx[i] / np.sqrt(Cn[i, i]))
        row["dchi2lat_at_LATFULL8"] = float(2 * f(th8))
        out["newton"][key] = row
        print(
            f"{key:40s} dalphaS vs LATFULL8 {row['dalphaS_vs_LATFULL8_over_sigNOM']:+.4f}  vs NOM "
            f"{row['dalphaS_vs_NOMSTIFF_over_sigNOM']:+.4f}  sig {row['sigma_ratio_vs_NOM']:.4f}  l2nu "
            f"{row['lambda2_nu']:.4f} ({row['d_lambda2_nu_over_sigma']:+.2f}s)  l4nu {row['lambda4_nu']:.5f} "
            f"({row['d_lambda4_nu_over_sigma']:+.2f}s)  Dchi2lat(L8) {row['dchi2lat_at_LATFULL8']:.3f}",
            flush=True,
        )
    out["load_time"] = {k: c.summary() for k, c in cores.items()}
    out["old_offset"] = float(old_off)
    out["K_offset"] = kmin
    json.dump(
        out,
        open(os.path.join(TASK, "newton_decomp.json"), "w"),
        indent=1,
        default=float,
    )


if __name__ == "__main__":
    main()
