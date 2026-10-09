#!/usr/bin/env python3
"""Gen-level stat-only Fisher forecast: Q-integrated vs 3 vs 5 mll windows.

Inputs: jacobians.npz (extract_jacobians.py). Model = SCETlibADParamModel's fitted
parameter set on a --pdf-eig 0 cache (no pdfEig*), in rabbit's theta units:

  free        alphaS (width 0.002), and the 5 NP lambdas in the 'free' arm
  N(0,1)      9 TNPs (b_qqDS frozen: inert), resumTransition2 (quad map, dx2/dtheta=0.2),
              resumFOScaleEnvSymAvg/SymDiff (3-pt mu_R envelope, zeroed for qT lower edge < 20)
  prior arm   the NP lambdas also N(0,1) in theta = physical widths 0.5,0.5,0.5,0.1,0.5
              (what the real card-A fits do: params.prior_sigma / REPARAM)
  frozen      lambda_inf, lambda_inf_nu, b0_over_bmax_nu, tnp_b_qqDS, x1, x3, kappa_R, kappa_F

V = diag(n), n = eps * w_k * sigma (Poisson, gen level; w_k = 1, or 0.5 off-peak in the
robustness variant). F = J^T V^-1 J + diag(prior). Merged arms sum n and J over windows.
"""
import argparse
import json
import os
import sys

import numpy as np
import wums.plot_tools as plot_tools  # noqa: F401  (import at top: sets the CMS style)
import matplotlib.pyplot as plt

TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(TASK, "scripts"))
from plot_output import save_plot  # noqa: E402

WINDOWS = [(60, 76), (76, 86), (86, 96), (96, 106), (106, 120)]
ARMS = {
    "Q-integrated": [[0, 1, 2, 3, 4]],
    "3 windows": [[0, 1], [2], [3, 4]],
    "5 windows": [[0], [1], [2], [3], [4]],
}
# fitted parameters: (label, cache name or special, theta width)
NPPAR = [
    ("lambda2", "np_eff_lambda2", 0.5),
    ("lambda4", "np_eff_lambda4", 0.5),
    ("delta_lambda2", "np_eff_delta_lambda2", 0.5),
    ("lambda2_nu", "np_gnu_lambda2", 0.1),
    ("lambda4_nu", "np_gnu_lambda4", 0.5),
]
TNPS = [
    "tnp_gamma_cusp",
    "tnp_gamma_mu_q",
    "tnp_gamma_nu",
    "tnp_s",
    "tnp_b_qqV",
    "tnp_b_qqbarV",
    "tnp_b_qqS",
    "tnp_b_qg",
    "tnp_h_qqV",
]
N_DATA_PT30 = None  # filled from card below
SQRT3 = np.sqrt(3.0)


def load(path, point):
    z = np.load(path)
    names = list(z["names"])
    bins, val, jac, env = [], [], [], []
    for lo, hi in WINDOWS:
        t = f"q{lo}_{hi}"
        b = z[f"{t}_bins"]
        bins.append(b)
        v0 = z[f"{t}_anchor_val"]
        v = z[f"{t}_{point}_val"]
        val.append(v)
        jac.append(z[f"{t}_{point}_jac"])
        # 3-point mu_R envelope at the anchor, rabbit 'quadratic' symmetrization
        r = np.log(np.stack([z[f"{t}_kr05"], z[f"{t}_kr2"]]) / v0)
        up = np.maximum(r.max(0), 0.0)
        dn = -np.minimum(r.min(0), 0.0)
        kavg, kdiff = 0.5 * (up + dn), 0.5 * SQRT3 * (up - dn)
        mask = b[:, 4] >= 20.0 - 1e-9
        env.append(np.stack([kavg * mask, kdiff * mask], 1))
    return names, bins, val, jac, env


def design(names, val, jac, env):
    """Per window: (sigma, J_theta) with columns [alphaS, NP..., TNPs, x2, envAvg, envDiff]."""
    labels = (
        ["alphaS"]
        + [p[0] for p in NPPAR]
        + ["resumTNP_" + t[4:] for t in TNPS]
        + ["resumTransition2", "resumFOScaleEnvSymAvg", "resumFOScaleEnvSymDiff"]
    )
    widths = np.array(
        [0.002] + [p[2] for p in NPPAR] + [1.0] * len(TNPS) + [0.2, 1.0, 1.0]
    )
    cols = ["alphas"] + [p[1] for p in NPPAR] + TNPS + ["scale_x2"]
    out = []
    for v, j, e in zip(val, jac, env):
        J = np.column_stack(
            [j[:, names.index(c)] for c in cols] + [v * e[:, 0], v * e[:, 1]]
        )
        out.append((v, J * widths))
    return labels, widths, out


def fisher(des, groups, eps, w, prior):
    F = (
        np.diag(prior).astype(float)
        if np.ndim(prior) == 1
        else np.array(prior, dtype=float)
    )
    for g in groups:
        n = sum(eps * w[k] * des[k][0] for k in g)
        J = sum(eps * w[k] * des[k][1] for k in g)
        F += (J / n[:, None]).T @ J
    return F


def analyse(F, labels, widths, np_idx):
    ev = np.linalg.eigvalsh(F)
    C = np.linalg.inv(F)
    sig_th = np.sqrt(np.diag(C))
    rho = C / np.outer(sig_th, sig_th)
    Cnp = C[np.ix_(np_idx, np_idx)]
    e, U = np.linalg.eigh(Cnp)
    return dict(
        minev=ev.min(),
        maxev=ev.max(),
        sig_phys=sig_th * widths,
        rho=rho,
        np_eig=np.sqrt(e[::-1]),
        np_vec=U[:, ::-1],
        C=C,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jac", default=os.path.join(TASK, "jacobians.npz"))
    ap.add_argument("--point", default="anchor", choices=["anchor", "lattice"])
    ap.add_argument(
        "--ndata", type=float, required=True, help="N_data(card A, ptll < ptcut)"
    )
    ap.add_argument("--ptcut", type=float, default=30.0)
    ap.add_argument("--plots", action="store_true")
    args = ap.parse_args()

    names, bins, val, jac, env = load(args.jac, args.point)
    labels, widths, des = design(names, val, jac, env)
    allb = np.concatenate(bins)
    allv = np.concatenate(val)
    sig_cut = allv[allb[:, 5] <= args.ptcut + 1e-9].sum()
    eps = args.ndata / sig_cut
    print(
        f"point={args.point}  sigma_gen(60-120,|Y|<2.5,qT<{args.ptcut:g}) = {sig_cut:.2f} pb, "
        f"total qT<40 {allv.sum():.2f} pb;  eps = {eps:.1f} events/pb  -> N(qT<40) = {eps*allv.sum():.4g}"
    )
    np_idx = [labels.index(p[0]) for p in NPPAR]
    ias, il2, il2n = (
        labels.index("alphaS"),
        labels.index("lambda2"),
        labels.index("lambda2_nu"),
    )
    nuis_prior = np.array(
        [0.0] * (1 + len(NPPAR)) + [1.0] * (len(labels) - 1 - len(NPPAR))
    )
    np_prior = nuis_prior.copy()
    np_prior[np_idx] = 1.0

    variants = {
        "NP free": (nuis_prior, [1] * 5),
        "NP free, off-peak x0.5": (nuis_prior, [0.5, 0.5, 1, 0.5, 0.5]),
        "NP real-fit priors": (np_prior, [1] * 5),
    }
    # lattice CS prior (260923-scetlib-kernel-fit, lambda_inf_nu = 2): s(l2nu)=0.038, s(l4nu)=0.0033, rho=-0.88,
    # in theta units (widths 0.1, 0.5); TMD lambdas free. Illustrative only: a Gaussian stand-in for the lattice chi2.
    il4n = labels.index("lambda4_nu")
    Clat = np.array(
        [
            [(0.038 / 0.1) ** 2, -0.88 * (0.038 / 0.1) * (0.0033 / 0.5)],
            [-0.88 * (0.038 / 0.1) * (0.0033 / 0.5), (0.0033 / 0.5) ** 2],
        ]
    )
    Plat = np.diag(nuis_prior).astype(float)
    Plat[np.ix_([il2n, il4n], [il2n, il4n])] += np.linalg.inv(Clat)
    variants["NP free + lattice CS prior"] = (Plat, [1] * 5)
    res = {}
    for vname, (prior, w) in variants.items():
        print(f"\n===== {vname} =====")
        print(
            f"{'arm':14s} {'minEV(F)':>9s} {'s(l2nu)':>8s} {'s(l4nu)':>8s} {'s(L2)':>7s} {'s(L4)':>7s} "
            f"{'s(dL2)':>7s} {'rho(l2nu,L2)':>12s} {'s(aS)':>8s}   NP-block sqrt-eig (theta)"
        )
        for arm, groups in ARMS.items():
            F = fisher(des, groups, eps, w, prior)
            a = analyse(F, labels, widths, np_idx)
            res[(vname, arm)] = a
            s = a["sig_phys"]
            print(
                f"{arm:14s} {a['minev']:9.2e} {s[il2n]:8.4f} {s[labels.index('lambda4_nu')]:8.4f} "
                f"{s[il2]:7.4f} {s[labels.index('lambda4')]:7.4f} {s[labels.index('delta_lambda2')]:7.4f} "
                f"{a['rho'][il2n, il2]:12.4f} {s[ias]:8.2e}   "
                + " ".join(f"{x:.3g}" for x in a["np_eig"])
            )
        for arm in ARMS:
            a = res[(vname, arm)]
            print(f"  [{arm}] NP correlation (order {[p[0] for p in NPPAR]}):")
            print(
                "   "
                + np.array2string(
                    a["rho"][np.ix_(np_idx, np_idx)], precision=3, suppress_small=True
                ).replace("\n", "\n   ")
            )
            v = a["np_vec"][:, 0]
            print(
                f"   flattest NP direction (theta units, sqrt-eig {a['np_eig'][0]:.3g}): "
                + " ".join(f"{p[0]}={x:+.3f}" for p, x in zip(NPPAR, v))
            )
            print(
                f"   rho(alphaS, NP) = "
                + " ".join(
                    f"{p[0]}={a['rho'][ias, i]:+.3f}" for p, i in zip(NPPAR, np_idx)
                )
            )
    # NP-only conditional (every nuisance and alphaS fixed): the pure lambda degeneracy
    print(
        "\n===== conditional: only the 5 NP lambdas float (alphaS, TNPs, x2, envelope fixed) ====="
    )
    for arm, groups in ARMS.items():
        F = fisher(des, groups, eps, [1] * 5, nuis_prior)[np.ix_(np_idx, np_idx)]
        C = np.linalg.inv(F)
        s = np.sqrt(np.diag(C))
        r = C / np.outer(s, s)
        print(
            f"{arm:14s} s(l2nu)={s[3]*0.1:.4f} s(L2)={s[0]*0.5:.4f} rho(l2nu,L2)={r[3,0]:+.4f}  "
            f"minEV={np.linalg.eigvalsh(F).min():.3g}"
        )

    # which non-NP parameter does the Q split disentangle? (NP free, nominal yields)
    print(
        "\n===== attribution: s(l2nu), s(aS) [NP free] with ONE non-NP parameter added to the NP-only set / removed from the full set ====="
    )
    oth = [i for i in range(len(labels)) if i not in np_idx]
    Fs = {arm: fisher(des, g, eps, [1] * 5, nuis_prior) for arm, g in ARMS.items()}

    def sig(F, keep):
        C = np.linalg.inv(F[np.ix_(keep, keep)])
        d = np.sqrt(np.diag(C))
        k2n = keep.index(il2n)
        return d[k2n] * 0.1, (d[keep.index(ias)] * 0.002 if ias in keep else np.nan)

    print(
        f"{'param':26s} {'NP+it: Qint':>12s} {'5win':>7s} | {'all-it: Qint':>12s} {'5win':>7s} | {'s(aS) all-it Qint':>17s} {'5win':>8s}"
    )
    for i in oth:
        a1 = sig(Fs["Q-integrated"], np_idx + [i])
        a5 = sig(Fs["5 windows"], np_idx + [i])
        keep = [k for k in range(len(labels)) if k != i]
        b1 = sig(Fs["Q-integrated"], keep)
        b5 = sig(Fs["5 windows"], keep)
        print(
            f"{labels[i]:26s} {a1[0]:12.4f} {a5[0]:7.4f} | {b1[0]:12.4f} {b5[0]:7.4f} | {b1[1]:17.2e} {b5[1]:8.2e}"
        )
    print("\n  NP + alphaS + ONE other:   s(l2nu) Qint / 5win,  s(aS) Qint / 5win")
    for i in oth:
        if i == ias:
            continue
        a1 = sig(Fs["Q-integrated"], np_idx + [ias, i])
        a5 = sig(Fs["5 windows"], np_idx + [ias, i])
        print(
            f"  {labels[i]:26s} {a1[0]:.4f} / {a5[0]:.4f}   {a1[1]:.2e} / {a5[1]:.2e}"
        )
    tnp_idx = [labels.index("resumTNP_" + t[4:]) for t in TNPS]
    for tag, extra in [
        ("NP+aS+all 9 TNPs", tnp_idx),
        ("NP+all 9 TNPs (aS fixed)", tnp_idx[:0] + tnp_idx),
    ]:
        ks = np_idx + ([ias] if "aS+" in tag else []) + extra
        a1 = sig(Fs["Q-integrated"], ks)
        a5 = sig(Fs["5 windows"], ks)
        print(f"  {tag:26s} {a1[0]:.4f} / {a5[0]:.4f}   {a1[1]:.2e} / {a5[1]:.2e}")

    json.dump(
        {
            f"{k[0]}|{k[1]}": {
                "sig_phys": dict(zip(labels, v["sig_phys"].tolist())),
                "rho_np": v["rho"][np.ix_(np_idx, np_idx)].tolist(),
                "rho_as_np": v["rho"][ias, np_idx].tolist(),
                "np_sqrt_eig_theta": v["np_eig"].tolist(),
                "np_eigvec_theta": v["np_vec"].tolist(),
                "minev": v["minev"],
            }
            for k, v in res.items()
        }
        | {"eps": eps, "point": args.point, "labels": labels},
        open(os.path.join(TASK, f"forecast_{args.point}.json"), "w"),
        indent=1,
    )

    if not args.plots:
        return
    meta = {
        "point": args.point,
        "eps_events_per_pb": eps,
        "ndata": args.ndata,
        "ptcut": args.ptcut,
        "jacobians": args.jac,
    }
    nwin = [1, 3, 5]
    cms = dict(label="Simulation Preliminary", loc=0, data=False, no_energy=False)
    # sigma vs windows
    fig, ax = plot_tools.figure(
        None,
        "Number of m$_{\\ell\\ell}$ windows in [60, 120] GeV",
        "$\\sigma$ / $\\sigma$(Q-integrated)",
        xlim=(0.5, 5.5),
        ylim=(0.0, 1.3),
        automatic_scale=False,
    )
    cols = ["#5790fc", "#f89c20", "#e42536", "#964a8b", "#9c9ca1", "#7a21dd"]
    for c, (lab, key) in zip(
        cols,
        [
            ("$\\lambda_{2,\\nu}$", "lambda2_nu"),
            ("$\\lambda_{4,\\nu}$", "lambda4_nu"),
            ("$\\Lambda_2$", "lambda2"),
            ("$\\Lambda_4$", "lambda4"),
            ("$\\delta\\Lambda_2$", "delta_lambda2"),
            ("$\\alpha_S$", "alphaS"),
        ],
    ):
        i = labels.index(key)
        for vname, ls in (("NP free", "-"), ("NP free, off-peak x0.5", "--")):
            y = np.array([res[(vname, a)]["sig_phys"][i] for a in ARMS])
            ax.plot(
                nwin,
                y / y[0],
                ls,
                marker="o",
                color=c,
                label=lab if ls == "-" else None,
            )
    ax.plot([], [], "k-", label="nominal yields")
    ax.plot([], [], "k--", label="off-peak yields $\\times$0.5")
    ax.axhline(1, color="grey", lw=0.8)
    ax.set_xticks(nwin)
    plot_tools.addLegend(ax, ncols=3, text_size="small", loc="lower left")
    plot_tools.add_cms_decor(
        ax, "Simulation Preliminary", loc=0, data=False, no_energy=True
    )
    ax.text(
        0.97,
        0.97,
        "gen level, stat. only, fixed PDF\nNP $\\lambda$ unconstrained",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=14,
    )
    save_plot(TASK, f"sigma_vs_nwin_{args.point}", fig=fig, args=args, meta_info=meta)
    plt.close(fig)
    # rho vs windows
    fig, ax = plot_tools.figure(
        None,
        "Number of m$_{\\ell\\ell}$ windows in [60, 120] GeV",
        "correlation",
        xlim=(0.5, 5.5),
        ylim=(-1.05, 1.9),
        automatic_scale=False,
    )
    pairs = [
        ("lambda2_nu", "lambda2"),
        ("lambda2_nu", "lambda4_nu"),
        ("lambda2_nu", "lambda4"),
        ("lambda2_nu", "delta_lambda2"),
        ("lambda2_nu", "alphaS"),
        ("lambda2", "alphaS"),
    ]
    tex = {
        "lambda2_nu": "\\lambda_{2,\\nu}",
        "lambda4_nu": "\\lambda_{4,\\nu}",
        "lambda2": "\\Lambda_2",
        "lambda4": "\\Lambda_4",
        "delta_lambda2": "\\delta\\Lambda_2",
        "alphaS": "\\alpha_S",
    }
    for c, (p, q) in zip(cols, pairs):
        i, j = labels.index(p), labels.index(q)
        for vname, ls in (("NP free", "-"), ("NP free, off-peak x0.5", "--")):
            y = [res[(vname, a)]["rho"][i, j] for a in ARMS]
            ax.plot(
                nwin,
                y,
                ls,
                marker="o",
                color=c,
                label=f"$\\rho({tex[p]}, {tex[q]})$" if ls == "-" else None,
            )
    ax.set_xticks(nwin)
    ax.axhline(0, color="grey", lw=0.8)
    ax.plot([], [], "k-", label="nominal yields")
    ax.plot([], [], "k--", label="off-peak $\\times$0.5")
    plot_tools.addLegend(ax, ncols=2, text_size="small", loc="upper left")
    plot_tools.add_cms_decor(
        ax, "Simulation Preliminary", loc=0, data=False, no_energy=True
    )
    save_plot(TASK, f"rho_vs_nwin_{args.point}", fig=fig, args=args, meta_info=meta)
    plt.close(fig)
    # derivative ratio vs Q
    fig, ax = plot_tools.figure(
        None,
        "m$_{\\ell\\ell}$ window centre (GeV)",
        "$(\\partial\\sigma/\\partial\\lambda_{2,\\nu}) / (\\partial\\sigma/\\partial\\Lambda_2)$",
        xlim=(60, 120),
        ylim=(0.0, 3.0),
        automatic_scale=False,
    )
    qc = [0.5 * (lo + hi) for lo, hi in WINDOWS]
    iN, iT = names.index("np_gnu_lambda2"), names.index("np_eff_lambda2")
    qtsel = [(0, 1), (1, 2), (2, 3), (4, 5), (8, 10), (14, 17)]
    for c, (a, b) in zip(cols, qtsel):
        y = []
        for bb, jj in zip(bins, jac):
            m = np.isclose(bb[:, 4], a) & np.isclose(bb[:, 5], b)
            y.append(jj[m, iN].sum() / jj[m, iT].sum())
        ax.plot(qc, y, "-o", color=c, label=f"$q_T \\in [{a}, {b}]$ GeV")
    for lo, hi in WINDOWS[1:]:
        ax.axvline(lo, color="grey", lw=0.5, ls=":")
    plot_tools.addLegend(ax, ncols=2, text_size="small", loc="upper left")
    plot_tools.add_cms_decor(
        ax, "Simulation Preliminary", loc=0, data=False, no_energy=True
    )
    ax.text(
        0.97,
        0.03,
        "$|Y|<2.5$ summed, " + args.point,
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=14,
    )
    save_plot(
        TASK, f"deriv_ratio_vs_Q_{args.point}", fig=fig, args=args, meta_info=meta
    )
    plt.close(fig)


if __name__ == "__main__":
    main()
