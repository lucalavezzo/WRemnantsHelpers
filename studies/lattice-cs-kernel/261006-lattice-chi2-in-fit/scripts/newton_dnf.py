#!/usr/bin/env python3
"""Cache-free Newton steps from LATLIVE8Y: lattice syst Jnf+Jbt vs direct_nf+Jbt (and the reference Jnf+Jbt+mu0scale
that LATLIVE8Y itself used, as the closure row).
H = inv(C_LATLIVE8Y) with the lattice term's (alpha_s, lambda2_nu, lambda4_nu) block swapped ref -> variant; g = the
variant-minus-ref lattice gradient. APPROXIMATION (blinding): the live term's gradient/Hessian are evaluated at
dalpha_s = 0, because the true alpha_s of the fit is blinded; the error is O(dalpha_s * d g / d alpha_s), small next
to the difference between two covariances. Only differences / sigma_NOM are written. Also: lattice-only sigma/rho per
covariance, and the point-by-point n_f shift patterns (J-mapped at the lattice best fit, J-mapped at LATLIVE8Y's
lambdas, direct). Writes ../newton_dnf.json."""
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
LL = f"{A}/261006_lattice_chi2_in_fit/fitresults_LATLIVE8Y.hdf5"
WID = dict(alphaS=0.002, lambda2_nu=0.1, lambda4_nu=0.5)
REF = "Jnf+Jbt+mu0scale"
VARS = [REF, "Jnf+Jbt", "direct_nf+Jbt", "none"]


def load(p):
    fr = io_tools.get_fitresult(p, None)
    h = fr["parms"].get()
    return (
        [str(n) for n in h.axes[0]],
        np.asarray(h.values(), float),
        np.asarray(fr["cov"].get().values(), float),
    )


def gn(c, l2, l4):
    s2 = 1.0 / np.cosh((l2 * c.u + l4 * c.u**2) / 2.0) ** 2
    X = np.column_stack([-0.5 * s2 * c.u, -0.5 * s2 * c.u**2, c.v])
    C = np.linalg.inv(X.T @ c.W @ X)[:2, :2]
    s = np.sqrt(np.diag(C))
    return [float(s[0]), float(s[1]), float(C[0, 1] / s[0] / s[1])]


def main():
    nN, xN, CN = load(NOM)
    nl, xl, Cl = load(LL)
    sN = np.sqrt(CN[nN.index("alphaS"), nN.index("alphaS")])
    ia, i2, i4 = (nl.index(k) for k in ("alphaS", "lambda2_nu", "lambda4_nu"))
    l2, l4 = 0.15 + 0.1 * xl[i2], 0.5 * xl[i4]
    da0 = 0.0  # blinded: see the docstring

    def nll(core, off, z):  # z = theta offsets (alphaS, l2nu, l4nu) around the point
        lam = dict(
            lambda_inf_nu=2.0, lambda2_nu=l2 + 0.1 * z[1], lambda4_nu=l4 + 0.5 * z[2]
        )
        return 0.5 * (core.chi2(lam, da0 + 0.002 * z[0], mode="alphas") - off)

    def gh(core, off, e=1e-4):
        g, H = np.zeros(3), np.zeros((3, 3))
        f0 = nll(core, off, np.zeros(3))
        for i in range(3):
            ei = np.eye(3)[i] * e
            g[i] = (nll(core, off, ei) - nll(core, off, -ei)) / (2 * e)
            H[i, i] = (nll(core, off, ei) - 2 * f0 + nll(core, off, -ei)) / e**2
            for j in range(i):
                ej = np.eye(3)[j] * e
                H[i, j] = H[j, i] = (
                    nll(core, off, ei + ej)
                    - nll(core, off, ei - ej)
                    - nll(core, off, -ei + ej)
                    + nll(core, off, -ei - ej)
                ) / (4 * e * e)
        return g, H

    cores = {v: L.LatticeCSCore(syst=v) for v in VARS}
    mins = {v: c.fit() for v, c in cores.items()}
    gR, HR = gh(cores[REF], mins[REF][0].fun)
    H0 = np.linalg.inv(Cl)
    blk = [ia, i2, i4]
    out = dict(
        newton={},
        lattice_only={},
        point_patterns={},
        approx="live-term derivatives at dalpha_s = 0 (blinded)",
    )
    for v in VARS:
        res, lm = mins[v]
        out["lattice_only"][v] = dict(
            chi2_min=float(res.fun),
            l2=float(lm["lambda2_nu"]),
            l4=float(lm["lambda4_nu"]),
            gn_sigma_l2_sigma_l4_rho=gn(cores[v], lm["lambda2_nu"], lm["lambda4_nu"]),
        )
        gV, HV = gh(cores[v], res.fun)
        H = H0.copy()
        H[np.ix_(blk, blk)] += HV - HR
        g = np.zeros(len(nl))
        g[blk] = gV - gR
        dx = -np.linalg.solve(H, g)
        Cn = np.linalg.inv(H)
        out["newton"][v] = dict(
            dalphaS_over_sigNOM=float((xl[ia] + dx[ia] - xN[nN.index("alphaS")]) / sN),
            dalphaS_vs_LATLIVE8Y_over_sigNOM=float(dx[ia] / sN),
            sigma_ratio_vs_NOM=float(np.sqrt(Cn[ia, ia]) / sN),
            lambda2_nu=float(l2 + 0.1 * dx[i2]),
            lambda4_nu=float(l4 + 0.5 * dx[i4]),
            sigma_lambda2_nu=float(0.1 * np.sqrt(Cn[i2, i2])),
            sigma_lambda4_nu=float(0.5 * np.sqrt(Cn[i4, i4])),
            dl2_over_sigma=float(0.1 * dx[i2] / (0.1 * np.sqrt(Cn[i2, i2]))),
            dl4_over_sigma=float(0.5 * dx[i4] / (0.5 * np.sqrt(Cn[i4, i4]))),
        )
        print(
            f"[{v:18s}] lattice-only {out['lattice_only'][v]}\n{'':20s} newton {out['newton'][v]}",
            flush=True,
        )
    d = np.load(L.DEFAULT_INPUTS)
    jn = d["syst_J"][0]
    dr = d["syst_direct_nf"][0]
    s2 = 1.0 / np.cosh((l2 * cores["none"].u + l4 * cores["none"].u ** 2) / 2.0) ** 2
    Jend = np.column_stack(
        [-0.5 * s2 * cores["none"].u, -0.5 * s2 * cores["none"].u ** 2]
    )
    dnf = np.linalg.lstsq(np.asarray(d["jac_ref"]), jn, rcond=None)[0]
    jend = Jend @ dnf
    sig = np.sqrt(np.diag(d["cov_stat"]))
    out["point_patterns"] = dict(
        b_fm=d["b_fm"].tolist(),
        J_at_lattice_bestfit=jn.tolist(),
        J_at_LATLIVE8Y=jend.tolist(),
        direct=dr.tolist(),
        sigma_stat=sig.tolist(),
        corr_J_direct=float(np.corrcoef(jn, dr)[0, 1]),
        corr_Jend_direct=float(np.corrcoef(jend, dr)[0, 1]),
        max_abs=dict(
            J=float(np.max(np.abs(jn))),
            J_end=float(np.max(np.abs(jend))),
            direct=float(np.max(np.abs(dr))),
        ),
        max_over_sigma=dict(
            J=float(np.max(np.abs(jn) / sig)),
            J_end=float(np.max(np.abs(jend) / sig)),
            direct=float(np.max(np.abs(dr) / sig)),
        ),
    )
    pp = out["point_patterns"]
    print(
        "[patterns] corr(J, direct) %.3f, corr(J@end, direct) %.3f, max|.|/sigma J %.3f J@end %.3f direct %.3f"
        % (pp["corr_J_direct"], pp["corr_Jend_direct"], *pp["max_over_sigma"].values())
    )
    for b, a1, a2, a3, s in zip(pp["b_fm"], jn, jend, dr, sig):
        print(
            f"   b {b:.2f} fm   J@best {a1:+.4f}   J@LATLIVE8Y {a2:+.4f}   direct {a3:+.4f}   sigma {s:.3f}"
        )
    json.dump(out, open(os.path.join(TASK, "newton_dnf.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
