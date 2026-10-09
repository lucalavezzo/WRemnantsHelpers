#!/usr/bin/env python3
"""T8 step 1 (no cache): the lattice terms at NOMSTIFF / the W point, and how Gaussian the 2D term is there.

Gaussian terms are exactly what the cards carry (numbers re-derived from the injector's inputs, checked against
260923-lattice-fits/logs/inject_statsyst.log): 2D stat+syst on (lambda2_nu, lambda4_nu), 1D l4zero on lambda2_nu.
The exact lattice chi2 is the 260923-scetlib-kernel-fit machinery (tanh_2, linf_nu = 2, k1 profiled, nf5 pert,
block-diagonal per-ensemble STAT covariance). Host python. Writes ../lattice_cheap.json and a plot.
"""
import json, os, sys
import numpy as np

T = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KFD = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/lattice-cs-kernel/260923-scetlib-kernel-fit"
LFD = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/lattice-cs-kernel/260923-lattice-fits/scripts"
sys.path.insert(0, KFD)
sys.path.insert(0, LFD)
import kernel_fit as KF  # noqa
import inject_aswz_cs_prior_theta as INJ  # noqa  (build_constraint only; no rabbit import at module level)

ref = json.load(open(f"{T}/ref_points.json"))
L2N = ref["NOMSTIFF"]["lambdas"]["lambda2_nu"]["physical"]
W = (
    ref["XWSTIFF"]["lambdas"]["lambda2_nu"]["physical"],
    ref["XWSTIFF"]["lambdas"]["lambda4_nu"]["physical"],
)
NOM = (L2N, 0.0)

mu, ctot, ex = INJ.build_constraint(INJ.KFIT, "default")
cstat = ex["cstat"]
l4z = json.load(open(INJ.KFIT_L4Z))["lambda2_nu"]
mu1, s1 = l4z["central"], l4z["tot"]


def chi2g(p, m, c):
    d = np.asarray(p) - m
    return float(d @ np.linalg.solve(c, d))


def cond(m, c, l2):
    mean = m[1] + c[0, 1] / c[0, 0] * (l2 - m[0])
    return mean, np.sqrt(c[1, 1] - c[0, 1] ** 2 / c[0, 0])


out = dict(
    lambda2_nu_NOM=L2N,
    W_point=W,
    mu_2d=mu.tolist(),
    cov_2d_statsyst=ctot.tolist(),
    cov_2d_stat=cstat.tolist(),
    l4zero_1d=dict(mu=mu1, sigma=s1),
)
for lab, c in [("statsyst (card)", ctot), ("stat only", cstat)]:
    m4, s4 = cond(mu, c, L2N)
    out[f"cond_{lab}"] = dict(mean=m4, sigma=s4, pull_of_zero=(0 - m4) / s4)
    print(
        f"[gauss {lab}] lambda4_nu | lambda2_nu={L2N:.5f}: mean {m4:+.5f} sigma {s4:.5f}; lambda4_nu=0 is {(0-m4)/s4:+.2f} sigma"
    )
    cN, cW = chi2g(NOM, mu, c), chi2g(W, mu, c)
    out[f"chi2_{lab}"] = dict(NOM=cN, W=cW, W_minus_NOM=cW - cN)
    print(
        f"[gauss {lab}] chi2 NOM {cN:.3f}  W {cW:.3f}  W-NOM {cW-cN:+.3f}  (NLL units: x0.5)"
    )
# 1D (nominal card) term at NOM, for the NLL bookkeeping between cards
c1N = (L2N - mu1) ** 2 / s1**2
out["chi2_1d_NOM"] = c1N
print(
    f"[gauss 1D l4zero] chi2 at NOM {c1N:.4f}  (NOMSTIFF's lattice term = {0.5*c1N:.4f} NLL)"
)
print(
    f"[cards] at NOM: 2D statsyst term - 1D term = {0.5*(out['chi2_statsyst (card)']['NOM']-c1N):+.4f} NLL"
)

# ---- exact lattice chi2 (stat cov, k1 profiled): conditional line at lambda2_nu = L2N, and the two points
D = KF.load_data()
Pt = np.load(f"{KFD}/pert_tables.npz")
pert = Pt["data_nf5"]


def chi2x(l2, l4, pk="nf5"):
    return KF.chi2_at(D, Pt[f"data_{pk}"], dict(linf=2.0, l2=l2, l4=l4), ks=("k1",))[
        "chi2"
    ]


best = KF.Fit(D, pert, ["l2", "l4", "k1"], fixed=dict(linf=2.0)).run()
cmin = best["chi2"]
print(f"[exact] 2D best chi2 {cmin:.4f} at {best['x']}")
g4 = np.linspace(-0.004, 0.012, 33)
xs = np.array([chi2x(L2N, v) for v in g4]) - cmin
gs = np.array(
    [chi2g((L2N, v), mu, cstat) for v in g4]
)  # stat Gaussian, its own min = 0 at mu
i0 = int(np.argmin(xs))
a = np.polyfit(g4[max(0, i0 - 4) : i0 + 5], xs[max(0, i0 - 4) : i0 + 5], 2)
xmin_exact = -a[1] / (2 * a[0])
s_exact = 1 / np.sqrt(a[0])
m4s, s4s = cond(mu, cstat, L2N)
print(
    f"[exact stat] conditional at lambda2_nu={L2N:.5f}: min at lambda4_nu {xmin_exact:+.5f}, curvature sigma {s_exact:.5f}"
    f"  (Gaussian stat: {m4s:+.5f} / {s4s:.5f}); min chi2 above 2D best: exact {xs.min():.3f}, Gaussian {gs.min():.3f}"
)
xN, xW = chi2x(*NOM), chi2x(*W)
print(
    f"[exact stat] chi2 NOM {xN-cmin:.3f}  W {xW-cmin:.3f}  W-NOM {xW-xN:+.3f}  (Gaussian stat: {out['chi2_stat only']['W_minus_NOM']:+.3f})"
)
# systematic variants of the exact W-NOM difference
var = {}
for pk in ["nf4", "nf5_mu1match"]:
    var[pk] = chi2x(*W, pk) - chi2x(*NOM, pk)
print(f"[exact stat] W-NOM in n_f variants: {var}")
out["exact_stat"] = dict(
    best_chi2=cmin,
    best=best["x"],
    cond_min_l4=xmin_exact,
    cond_sigma_l4=s_exact,
    cond_min_dchi2=float(xs.min()),
    NOM=xN - cmin,
    W=xW - cmin,
    W_minus_NOM=xW - xN,
    W_minus_NOM_variants=var,
    scan_l4=g4.tolist(),
    scan_exact=xs.tolist(),
    scan_gauss=gs.tolist(),
)
# MCMC (flat prior, linf=2): how many samples near the NOM slice, and their lambda4_nu
ch = np.load(f"{KFD}/chain_B_linf2.npy")
sel = np.abs(ch[:, 0] - L2N) < 0.015
out["mcmc"] = dict(
    n=int(len(ch)),
    n_slice=int(sel.sum()),
    l4_slice_mean=float(ch[sel, 1].mean()) if sel.sum() > 5 else None,
    l4_slice_std=float(ch[sel, 1].std()) if sel.sum() > 5 else None,
)
print(
    f"[mcmc] samples with |lambda2_nu-{L2N:.3f}|<0.015: {sel.sum()}/{len(ch)}; lambda4_nu there {out['mcmc']['l4_slice_mean']} +- {out['mcmc']['l4_slice_std']}"
)
json.dump(out, open(f"{T}/lattice_cheap.json", "w"), indent=1)

# plot: conditional line, exact vs Gaussian(stat), and the card's (stat+syst) Gaussian
sys.argv = sys.argv[:1]
import matplotlib

matplotlib.use("Agg")
from wums import plot_tools

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_output import save_plot

gt = np.array([chi2g((L2N, v), mu, ctot) for v in g4])
gt -= 0  # card term, own min 0 at mu
fig, ax = plot_tools.figure(
    g4,
    r"$\lambda_4^\nu$ [GeV$^4$]",
    r"$\Delta\chi^2_{\rm lat}$ (vs 2D best)",
    xlim=(g4[0], g4[-1]),
    ylim=(0, 25),
    automatic_scale=False,
)
ax.plot(g4, xs, "k-", label="exact lattice $\\chi^2$ (stat cov, $k_1$ profiled)")
ax.plot(g4, gs, "b--", label="2D Gaussian, stat (Hessian of the exact fit)")
ax.plot(g4, gt, "r-.", label="2D Gaussian, stat+syst (the card's term)")
ax.axvline(0, color="grey", lw=0.8)
ax.set_title(
    rf"conditional on $\lambda_2^\nu$ = {L2N:.4f} (NOMSTIFF), $\lambda_\infty^\nu$ = 2",
    fontsize=11,
)
ax.legend(fontsize=9, loc="upper left")
save_plot(
    outdir=T,
    basename="lattice_conditional_l4nu",
    fig=fig,
    args=None,
    meta_info=dict(script=__file__),
)
