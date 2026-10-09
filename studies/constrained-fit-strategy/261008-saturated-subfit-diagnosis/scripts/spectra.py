#!/usr/bin/env python3
"""Offline (numpy only, no cache): conditioning of the projected-ptll saturated sub-fit, from HDIAG's dense Hessians.

Inputs (ceph, written by hess_diag.py): hess_start.npz (H at the warm start x_s), hess_end.npz (H at SATB8's minimum
x_e), newton_start.npz (exact Newton step d from x_s, actual displacement D = x_e - x_s).

1. Spectra of H_s and H_e: extremes, kappa = max|lam| / min|lam|, negatives, and what the extreme eigenvectors are.
2. Preconditioners as rabbit would build them AT THE SUB-FIT START (from H_s), applied to H_e (the end of the path):
   none | jacobi (diag H_s) | 'saturated_.*' block (spectral) | cw == 0 block (rabbit's default --preconditionParams
   scope, spectral) | full (spectral |H_s|^-1/2).  For each: spectrum of T^T H_e T, and conjugate-gradient iteration
   counts (= HVPs of an interior Krylov solve) to relative residuals 1e-1 .. 1e-6, for two right-hand sides:
   T^T g_s on T^T H_s T (the first solve) and a fixed random vector on T^T H_e T (a late solve).
3. Variable projection: the Schur complement of the 39 bin-scale block at x_e (the Hessian of the problem with the
   scales profiled out), raw and Jacobi-scaled kappa.
4. The Newton step from the start vs the actual displacement: cosine and projection, raw and in the H_e metric.
5. alphaS: sigma(M1)/sigma(M0-like) and rho^2(alphaS, scales | rest) from H_e (ratios only; no alphaS value).
Writes spectra.json.
"""
import json
import os

import numpy as np

T = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get(
    "SPECTRA_DIR",
    "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261008_saturated_subfit_diag",
)


def load(f):
    z = np.load(f"{OUT}/{f}", allow_pickle=True)
    return {k: z[k] for k in z.files}


def eigsum(w):
    a = np.abs(w)
    return dict(
        min=float(w.min()),
        max=float(w.max()),
        n_neg=int((w < 0).sum()),
        absmin=float(a.min()),
        kappa=float(a.max() / a.min()),
        n_abs_lt_1e_2=int((a < 1e-2).sum()),
        n_abs_gt_1e4=int((a > 1e4).sum()),
        pct=[float(np.percentile(a, p)) for p in (0, 1, 10, 50, 90, 99, 100)],
    )


def top_comp(v, names, k=6):
    o = np.argsort(-np.abs(v))[:k]
    return [(str(names[i]), round(float(v[i]), 3)) for i in o]


def spectral_inv_sqrt(A):
    w, Q = np.linalg.eigh(0.5 * (A + A.T))
    a = np.maximum(np.abs(w), np.abs(w).max() * 1e-14)
    return Q / np.sqrt(a)  # T with T^T |A| T = I


def build_T(Hs, sel):
    n = Hs.shape[0]
    Tm = np.eye(n)
    if sel is None:
        return Tm
    if isinstance(sel, str) and sel == "jacobi":
        return np.diag(1.0 / np.sqrt(np.maximum(np.abs(np.diag(Hs)), 1e-300)))
    idx = np.asarray(sel)
    Tm[np.ix_(idx, idx)] = spectral_inv_sqrt(Hs[np.ix_(idx, idx)])
    return Tm


def cg_counts(A, b, tols=(1e-1, 1e-2, 1e-3, 1e-4, 1e-6), itmax=20000):
    """Plain CG on A x = b from x = 0 (what a Krylov interior solve does in exact arithmetic). Counts matvecs until
    ||r|| <= tol ||b||; stops on negative curvature (trlib would then go to the boundary).
    """
    x = np.zeros_like(b)
    r = b.copy()
    p = r.copy()
    rr = r @ r
    nb = np.sqrt(rr)
    out, k, todo = {}, 0, list(tols)
    neg = None
    while todo and k < itmax:
        Ap = A @ p
        pAp = p @ Ap
        k += 1
        if pAp <= 0:
            neg = k
            break
        a = rr / pAp
        x += a * p
        r -= a * Ap
        rr_new = r @ r
        while todo and np.sqrt(rr_new) <= todo[0] * nb:
            out[f"{todo.pop(0):g}"] = k
        p = r + (rr_new / rr) * p
        rr = rr_new
    for t in todo:
        out[f"{t:g}"] = None
    return dict(iters=out, negative_curvature_at=neg)


def main():
    S = load("hess_start.npz")
    E = load("hess_end.npz")
    names = S["names"].astype(str)
    Hs, He, gs = S["H"], E["H"], S["g"]
    cw = S["cw"]
    isat = S["isat"].astype(int)
    n = len(names)
    res = dict(n=n)
    eigs = {}

    for lab, H in [("H_s", Hs), ("H_e", He)]:
        w, Q = np.linalg.eigh(H)
        eigs[lab] = w
        res[lab] = eigsum(w)
        res[lab]["top"] = [
            dict(lam=float(w[-1 - i]), comp=top_comp(Q[:, -1 - i], names))
            for i in range(4)
        ]
        o = np.argsort(np.abs(w))
        res[lab]["soft"] = [
            dict(lam=float(w[o[i]]), comp=top_comp(Q[:, o[i]], names)) for i in range(6)
        ]
        res[lab]["diag_sat"] = dict(
            min=float(np.diag(H)[isat].min()), max=float(np.diag(H)[isat].max())
        )
        print(
            f"{lab}: {json.dumps({k: v for k, v in res[lab].items() if k not in ('top', 'soft')})}"
        )
        for t in res[lab]["top"][:2] + res[lab]["soft"][:3]:
            print("   ", t)

    unc = np.nonzero(cw == 0)[0]
    res["unconstrained"] = [str(names[i]) for i in unc]
    rng = np.random.default_rng(7)
    brand = rng.standard_normal(n)
    pcs = {
        "none": None,
        "jacobi": "jacobi",
        "saturated block": isat,
        "cw==0 block (rabbit default scope)": unc,
        "full": np.arange(n),
    }
    res["precond"] = {}
    for lab, sel in pcs.items():
        Tm = build_T(Hs, sel)
        Ae = Tm.T @ He @ Tm
        As = Tm.T @ Hs @ Tm
        w = np.linalg.eigvalsh(0.5 * (Ae + Ae.T))
        eigs[f"pc_{lab}"] = w
        a = np.abs(w)
        r = dict(
            end_spectrum=eigsum(w),
            n_outside_0p1_10=int(((a < 0.1) | (a > 10)).sum()),
            cg_first_solve=cg_counts(0.5 * (As + As.T), Tm.T @ gs),
            cg_late_solve=cg_counts(0.5 * (Ae + Ae.T), brand),
        )
        res["precond"][lab] = r
        print(
            f"[{lab}] end kappa {r['end_spectrum']['kappa']:.3g}, outside [0.1,10]: {r['n_outside_0p1_10']}, "
            f"CG first {r['cg_first_solve']}, late {r['cg_late_solve']}"
        )

    # 3. variable projection: profile the scales out
    th = np.setdiff1d(np.arange(n), isat)
    Hss = He[np.ix_(isat, isat)]
    Hts = He[np.ix_(th, isat)]
    Sred = He[np.ix_(th, th)] - Hts @ np.linalg.solve(Hss, Hts.T)
    w = np.linalg.eigvalsh(0.5 * (Sred + Sred.T))
    dj = 1 / np.sqrt(np.abs(np.diag(Sred)))
    wj = np.linalg.eigvalsh((Sred * dj[:, None]) * dj[None, :])
    wss = np.linalg.eigvalsh(Hss)
    eigs["varpro_schur"] = w
    res["varpro"] = dict(
        H_ss=eigsum(wss),
        schur=eigsum(w),
        schur_jacobi=eigsum(wj),
        theta_block_raw=eigsum(np.linalg.eigvalsh(He[np.ix_(th, th)])),
    )
    print(
        "varpro:",
        json.dumps(
            {
                k: {kk: v[kk] for kk in ("kappa", "min", "max", "n_neg")}
                for k, v in res["varpro"].items()
            }
        ),
    )

    # 4. Newton step vs actual displacement
    try:
        N = load("newton_start.npz")
        d, D = N["d"], N["D"]
        res["newton_vs_D"] = dict(
            cos=float(d @ D / np.linalg.norm(d) / np.linalg.norm(D)),
            proj=float(d @ D / (D @ D)),
            cos_He=float(d @ He @ D / np.sqrt((d @ He @ d) * (D @ He @ D))),
            quad_cost_D_at_He=float(0.5 * D @ He @ D),
            quad_cost_D_at_Hs=float(0.5 * D @ Hs @ D),
        )
        print("newton vs D:", res["newton_vs_D"])
    except FileNotFoundError:
        pass

    # 5. alphaS degeneracy with the scales, from H_e (ratios only)
    ia = int(np.nonzero(names == "alphaS")[0][0])
    Ce = np.linalg.inv(He)
    keep = np.setdiff1d(np.arange(n), isat)
    C0 = np.linalg.inv(He[np.ix_(keep, keep)])  # scales FIXED at their x_e values
    ka = int(np.nonzero(keep == ia)[0][0])
    res["alphaS"] = dict(
        sigma_ratio_free_vs_fixed_scales=float(np.sqrt(Ce[ia, ia] / C0[ka, ka])),
        rho2_with_scales=float(1 - C0[ka, ka] / Ce[ia, ia]),
    )
    print("alphaS:", res["alphaS"])
    np.savez(os.path.join(OUT, "spectra_eigs.npz"), **eigs)
    json.dump(
        res, open(os.environ.get("SPECTRA_OUT", f"{T}/spectra.json"), "w"), indent=1
    )


if __name__ == "__main__":
    main()
