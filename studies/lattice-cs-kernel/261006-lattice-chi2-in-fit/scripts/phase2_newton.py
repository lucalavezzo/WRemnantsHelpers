#!/usr/bin/env python3
"""Phase 2 (cache-free): closure of the lattice term under each systematic set, and Newton steps from LATCHI8.

1. Closure per syst set (lattice only, alpha_s frozen, lambda_inf_nu = 2): minimum, chi2_min, Gauss-Newton and exact
   Hessian (l2, l4) covariance, and Delta chi2 at NOMSTIFF / LATCHI8 / T8 Newton / W.
2. Per-systematic size: the summary's chosen (dl2, dl4) shift per group / stat sigma, and the pert-scale group's GN
   effect.
3. (D) Newton from LATCHI8: H = inv(C_LATCHI8) (data + priors + exact term syst=J + the stiff spring on the active face)
   with the (l2_nu, l4_nu) block of the J term swapped for the variant's; g = g_variant - g_J at LATCHI8 (the converged
   total gradient is ~0). d = -H^-1 g. Reports dalphaS/sigma_NOM, sigma ratio, l2_nu, l4_nu, Delta chi2_lat (variant).
4. NOMSTIFF: Newton estimate of dropping the k-form group from its 1D l4zero card term (sigma 0.0313 -> stat+nf+bt).
alphaS: differences / sigma_NOM only. Writes ../phase2_newton.json."""
import json
import os
import sys

import numpy as np
from rabbit import io_tools

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import lattice_cs_chi2 as L  # noqa: E402

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
NOM = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
L8 = f"{A}/261006_lattice_chi2_in_fit/fitresults_LATCHI8.hdf5"
W2, W4 = 0.1, 0.5  # REPARAM widths; anchors 0.15, 0
SETS = ["J", "none", "Jnf", "Jk", "Jbt", "Jnf+Jbt", "Jnf+Jbt+pert"]
L1D = json.load(
    open(
        os.path.join(
            os.path.dirname(TASK), "260923-scetlib-kernel-fit", "fit_l4zero.json"
        )
    )
)["lambda2_nu"]


def load(p):
    fr = io_tools.get_fitresult(p, None)
    h = fr["parms"].get()
    return (
        [str(n) for n in h.axes[0]],
        np.asarray(h.values(), float),
        np.asarray(fr["cov"].get().values(), float),
    )


def lam(l2, l4):
    return dict(lambda_inf_nu=2.0, lambda2_nu=l2, lambda4_nu=l4)


def term_theta(core, off, t2, t4):
    return 0.5 * (core.chi2(lam(0.15 + W2 * t2, W4 * t4)) - off)


def grad_hess(core, off, t2, t4, e=1e-4):
    f = lambda a, b: term_theta(core, off, a, b)  # noqa: E731
    g = np.array(
        [
            (f(t2 + e, t4) - f(t2 - e, t4)) / (2 * e),
            (f(t2, t4 + e) - f(t2, t4 - e)) / (2 * e),
        ]
    )
    f0 = f(t2, t4)
    H = np.zeros((2, 2))
    H[0, 0] = (f(t2 + e, t4) - 2 * f0 + f(t2 - e, t4)) / e**2
    H[1, 1] = (f(t2, t4 + e) - 2 * f0 + f(t2, t4 - e)) / e**2
    H[0, 1] = H[1, 0] = (
        f(t2 + e, t4 + e) - f(t2 + e, t4 - e) - f(t2 - e, t4 + e) + f(t2 - e, t4 - e)
    ) / (4 * e * e)
    return g, H


def gn(core, l2, l4):
    s2 = 1.0 / np.cosh((l2 * core.u + l4 * core.u**2) / 2.0) ** 2
    X = np.column_stack([-0.5 * s2 * core.u, -0.5 * s2 * core.u**2, core.v])
    return np.linalg.inv(X.T @ core.W @ X)[:2, :2]


def sig_rho(C):
    s = np.sqrt(np.diag(C))
    return [float(s[0]), float(s[1]), float(C[0, 1] / s[0] / s[1])]


def main():
    nN, xN, CN = load(NOM)
    n8, x8, C8 = load(L8)
    ia_N, ia_8 = nN.index("alphaS"), n8.index("alphaS")
    sN = np.sqrt(CN[ia_N, ia_N])
    i2, i4 = n8.index("lambda2_nu"), n8.index("lambda4_nu")
    t2_8, t4_8 = x8[i2], x8[i4]
    pts = {
        "NOMSTIFF": (0.15 + W2 * xN[nN.index("lambda2_nu")], 0.0),
        "LATCHI8": (0.15 + W2 * t2_8, W4 * t4_8),
        "T8 Newton": (0.0351, 0.0037),
        "W (XWSTIFF)": (-1.1216e-06, 0.044408),
    }
    out = dict(closure={}, newton={}, syst_size={}, nomstiff_1d_no_kform={})
    cores = {}
    for s in SETS:
        c = L.LatticeCSCore(syst=s)
        r, lm = c.fit()
        cores[s] = (c, float(r.fun))
        Hx = np.zeros((2, 2))
        f = lambda a, b: c.chi2(
            lam(lm["lambda2_nu"] + a, lm["lambda4_nu"] + b)
        )  # noqa: E731
        h = (2e-4, 2e-5)
        Hx[0, 0] = (f(h[0], 0) - 2 * f(0, 0) + f(-h[0], 0)) / h[0] ** 2
        Hx[1, 1] = (f(0, h[1]) - 2 * f(0, 0) + f(0, -h[1])) / h[1] ** 2
        Hx[0, 1] = Hx[1, 0] = (
            f(h[0], h[1]) - f(h[0], -h[1]) - f(-h[0], h[1]) + f(-h[0], -h[1])
        ) / (4 * h[0] * h[1])
        out["closure"][s] = dict(
            chi2_min=float(r.fun),
            l2=float(lm["lambda2_nu"]),
            l4=float(lm["lambda4_nu"]),
            k1=c.k1hat(lm),
            gn_sigma_rho=sig_rho(gn(c, lm["lambda2_nu"], lm["lambda4_nu"])),
            exact_sigma_rho=sig_rho(np.linalg.inv(0.5 * Hx)),
            dchi2={k: float(c.chi2(lam(*v)) - r.fun) for k, v in pts.items()},
        )
        print(f"[closure {s:13s}] {out['closure'][s]}", flush=True)
    # 2. per-systematic sizes (the summary's chosen parameter shifts), relative to stat
    d = np.load(L.DEFAULT_INPUTS)
    sst = np.sqrt(np.diag(d["card2d_cstat"]))
    meta = json.load(open(os.path.join(TASK, "lattice_aswz_inputs.json")))
    Jst = gn(
        cores["none"][0], out["closure"]["none"]["l2"], out["closure"]["none"]["l4"]
    )
    for g, row in zip(meta["groups"], d["syst_J"]):
        dl = np.linalg.lstsq(
            np.column_stack(
                [
                    *(lambda s2, u: (-0.5 * s2 * u, -0.5 * s2 * u * u))(
                        1.0
                        / np.cosh(
                            (
                                out["closure"]["none"]["l2"] * cores["none"][0].u
                                + out["closure"]["none"]["l4"] * cores["none"][0].u ** 2
                            )
                            / 2.0
                        )
                        ** 2,
                        cores["none"][0].u,
                    )
                ]
            ),
            row,
            rcond=None,
        )[0]
        out["syst_size"][g] = dict(
            dl2=float(dl[0]),
            dl4=float(dl[1]),
            dl2_over_stat=float(dl[0] / sst[0]),
            dl4_over_stat=float(dl[1] / sst[1]),
            chi2_stat=float(dl @ np.linalg.inv(Jst) @ dl),
        )
    Cp = gn(
        cores["Jnf+Jbt+pert"][0],
        out["closure"]["Jnf+Jbt+pert"]["l2"],
        out["closure"]["Jnf+Jbt+pert"]["l4"],
    )
    Cd = gn(
        cores["Jnf+Jbt"][0],
        out["closure"]["Jnf+Jbt"]["l2"],
        out["closure"]["Jnf+Jbt"]["l4"],
    )
    out["syst_size"]["pert scale (kappa 1/2, direct point shift)"] = dict(
        sigma_l2_with=float(np.sqrt(Cp[0, 0])),
        sigma_l2_without=float(np.sqrt(Cd[0, 0])),
        sigma_l4_with=float(np.sqrt(Cp[1, 1])),
        sigma_l4_without=float(np.sqrt(Cd[1, 1])),
        quad_extra_l2_over_stat=float(np.sqrt(max(Cp[0, 0] - Cd[0, 0], 0)) / sst[0]),
        quad_extra_l4_over_stat=float(np.sqrt(max(Cp[1, 1] - Cd[1, 1], 0)) / sst[1]),
        dchi2min=out["closure"]["Jnf+Jbt+pert"]["chi2_min"]
        - out["closure"]["Jnf+Jbt"]["chi2_min"],
        max_point_shift_over_sigma=meta["pert_scale_max_over_sigma"],
    )
    for k, v in out["syst_size"].items():
        print(f"[size] {k}: {v}", flush=True)
    # 3. Newton from LATCHI8
    cJ, oJ = cores["J"]
    gJ, HJ = grad_hess(cJ, oJ, t2_8, t4_8)
    H8 = np.linalg.inv(C8)
    blk = np.ix_([i2, i4], [i2, i4])
    for s in SETS:
        c, o = cores[s]
        gV, HV = grad_hess(c, o, t2_8, t4_8)
        H = H8.copy()
        H[blk] += HV - HJ
        g = np.zeros(len(n8))
        g[[i2, i4]] = gV - gJ
        dx = -np.linalg.solve(H, g)
        Cn = np.linalg.inv(H)
        l2n, l4n = 0.15 + W2 * (t2_8 + dx[i2]), W4 * (t4_8 + dx[i4])
        out["newton"][s] = dict(
            dalphaS_over_sigNOM=float((x8[ia_8] + dx[ia_8] - xN[ia_N]) / sN),
            dalphaS_vs_LATCHI8_over_sigNOM=float(dx[ia_8] / sN),
            sigma_ratio_vs_NOM=float(np.sqrt(Cn[ia_8, ia_8]) / sN),
            lambda2_nu=float(l2n),
            lambda4_nu=float(l4n),
            lambda4_nu_below_wall=bool(l4n < 0),
            dchi2_lat=float(c.chi2(lam(l2n, l4n)) - o),
            dNLL_pred=float(0.5 * g @ dx),
        )
        print(f"[newton {s:13s}] {out['newton'][s]}", flush=True)
    # 4. NOMSTIFF 1D card without the k-form group
    ch = L1D["chosen"]
    s_old = L1D["tot"]
    s_new = float(
        np.sqrt(L1D["stat"] ** 2 + ch["n_f scheme"][1] ** 2 + ch["b_T window"][1] ** 2)
    )
    j2 = nN.index("lambda2_nu")
    tmu = (L1D["central"] - 0.15) / W2
    dH = W2**2 * (1 / s_new**2 - 1 / s_old**2)
    HN = np.linalg.inv(CN)
    HN[j2, j2] += dH
    g = np.zeros(len(nN))
    g[j2] = dH * (xN[j2] - tmu)
    dx = -np.linalg.solve(HN, g)
    CNn = np.linalg.inv(HN)
    out["nomstiff_1d_no_kform"] = dict(
        sigma_old=s_old,
        sigma_new=s_new,
        dalphaS_over_sigNOM=float(dx[ia_N] / sN),
        sigma_ratio=float(np.sqrt(CNn[ia_N, ia_N]) / sN),
        lambda2_nu=float(0.15 + W2 * (xN[j2] + dx[j2])),
    )
    print(f"[NOMSTIFF 1D no k-form] {out['nomstiff_1d_no_kform']}", flush=True)
    json.dump(out, open(os.path.join(TASK, "phase2_newton.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
