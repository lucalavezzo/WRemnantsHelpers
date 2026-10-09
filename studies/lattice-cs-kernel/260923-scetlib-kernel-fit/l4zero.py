"""2026-09-23 (Luca): refit with lambda4_nu FIXED at 0 (tanh_2), because the AD cache / tanh_2
form break for lambda4_nu < 0. Separate outputs (fit_l4zero.json, l4zero_output.txt,
chain_l4zero.npy, bands_l4zero.npz) so the earlier fit_results.json -- which
260923-lattice-fits/scripts/inject_aswz_cs_prior_theta.py READS -- stays untouched.

Stat+syst sigma(lambda2_nu) built as in that injector: one shift per group (n_f scheme; k-form;
b_T window), the larger chi2_stat(d) within a group, C_syst = sum d d^T."""

import json
import os
import sys

import numpy as np
from scipy.stats import chi2 as chi2dist, norm

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kernel_fit as KF  # noqa: E402
import compare as CP  # noqa: E402  (re-runs nothing heavy? -> see guard below)

D, P, FIT = CP.D, CP.P, CP.FIT
lines = []


def pr(s=""):
    print(s)
    lines.append(s)


L4 = {"l4": 0.0}
CONF = [
    # label, free, fixed, pert, mask
    ("L4=0 | linf=2 | k1 [nominal]", ["l2", "k1"], dict(linf=2.0, **L4), "nf5", None),
    ("L4=0 | linf free | k1", ["linf", "l2", "k1"], dict(L4), "nf5", None),
    ("L4=0 | linf=2 | k2", ["l2", "k2"], dict(linf=2.0, **L4), "nf5", None),
    ("L4=0 | linf=2 | k1+k2", ["l2", "k1", "k2"], dict(linf=2.0, **L4), "nf5", None),
    (
        "L4=0 | linf=2 | k1 | nf4 scheme",
        ["l2", "k1"],
        dict(linf=2.0, **L4),
        "nf4",
        None,
    ),
    (
        "L4=0 | linf=2 | k1 | nf matched mu=1",
        ["l2", "k1"],
        dict(linf=2.0, **L4),
        "nf5_mu1match",
        None,
    ),
    (
        "L4=0 | linf=2 | k1 | drop bT<0.2",
        ["l2", "k1"],
        dict(linf=2.0, **L4),
        "nf5",
        "cut",
    ),
    (
        "L4=0 | linf=2 | k1 | nf-syst in cov",
        ["l2", "k1"],
        dict(linf=2.0, **L4),
        "nf5",
        "cov",
    ),
    ("L4=0 | linf=2 | no k", ["l2"], dict(linf=2.0, **L4), "nf5", None),
]
res = {}
for lab, free, fx, pk, mk in CONF:
    mask = (D["b"] >= 0.2 - 1e-9) if mk == "cut" else None
    extra = CP.COVSYST if mk == "cov" else None
    r = KF.Fit(D, P[pk], free, fixed=fx, mask=mask, extra_cov=extra).run()
    res[lab] = r
    s = "  ".join(f"{n}={r['x'][n]:+.4f}({r['err'][n]:.4f})" for n in free)
    pr(
        f"{lab:40s} chi2={r['chi2']:6.2f}/{r['ndf']:2d}  AIC={r['aic']:6.2f}  {s}"
        + (f"  AT BOUND {r['at_bound']}" if r["at_bound"] else "")
    )

nom = res["L4=0 | linf=2 | k1 [nominal]"]
mu, s_stat = nom["x"]["l2"], nom["err"]["l2"]
groups = {
    "n_f scheme": [
        "L4=0 | linf=2 | k1 | nf4 scheme",
        "L4=0 | linf=2 | k1 | nf matched mu=1",
    ],
    "k-form": ["L4=0 | linf=2 | k2", "L4=0 | linf=2 | k1+k2"],
    "b_T window": ["L4=0 | linf=2 | k1 | drop bT<0.2"],
}
pr()
csyst = 0.0
chosen = {}
for g, vs in groups.items():
    ds = [(v, res[v]["x"]["l2"] - mu) for v in vs]
    for v, dd in ds:
        pr(f"[syst] {g:11s} {v:40s} d = {dd:+.5f}  ({dd / s_stat:+.2f} sigma_stat)")
    v, dd = max(ds, key=lambda t: abs(t[1]))
    chosen[g] = (v, dd)
    csyst += dd**2
s_syst = np.sqrt(csyst)
s_tot = np.hypot(s_stat, s_syst)
pr(
    f"==> lambda2_nu (lambda4_nu=0, linf=2, k1) = {mu:.4f} +- {s_stat:.4f} (stat) +- {s_syst:.4f} (syst) = +- {s_tot:.4f} (tot)"
)
pr(
    f"    taken: "
    + "; ".join(f"{g}: {v.split('| ')[-1]} {d:+.4f}" for g, (v, d) in chosen.items())
)

# ---- cost of freezing lambda4_nu, vs the free-(l2,l4) fit at linf=2
f2 = FIT["tanh2 | linf=2 | k1"]
pr()
pr(
    f"Delta chi2 (l4=0) - (l2,l4 free), linf=2, k1: {nom['chi2'] - f2['chi2']:.3f}  (1 dof -> "
    f"{norm.isf(chi2dist.sf(nom['chi2'] - f2['chi2'], 1) / 2):.2f} sigma); vs linf-free global best "
    f"{nom['chi2'] - FIT['tanh2 | linf free | k1']['chi2']:.3f}"
)
pr(
    f"lattice-preferred lambda4_nu (2D fit) = {f2['x']['l4']:+.4f} +- {f2['err']['l4']:.4f} -> lambda4_nu=0 is "
    f"{abs(f2['x']['l4']) / f2['err']['l4']:.2f} sigma_stat away"
)
# Gaussian conditional of the 2D fit at l4=0: stat-only and stat+syst (injector's covariance)
m2 = np.array([f2["x"]["l2"], f2["x"]["l4"]])
Cst = np.array(f2["cov"])[:2, :2]
Csy = np.zeros((2, 2))
for g, vs in {
    "n_f": ["SYST nf4 scheme, linf=2", "SYST nf matched mu=1, linf=2"],
    "k": ["SYST k2, linf=2", "SYST k1+k2, linf=2"],
    "bT": ["SYST drop bT<0.2 fm, linf=2"],
}.items():
    ci = np.linalg.inv(Cst)
    best = max(
        ([FIT[v]["x"]["l2"] - m2[0], FIT[v]["x"]["l4"] - m2[1]] for v in vs),
        key=lambda d: np.array(d) @ ci @ np.array(d),
    )
    Csy += np.outer(best, best)
for lab, C in [("stat", Cst), ("stat+syst (injector)", Cst + Csy)]:
    cm = m2[0] - C[0, 1] / C[1, 1] * m2[1]
    cs = np.sqrt(C[0, 0] - C[0, 1] ** 2 / C[1, 1])
    pr(
        f"Gaussian conditional of 2D fit at l4=0 [{lab}]: lambda2_nu = {cm:.4f} +- {cs:.4f}"
    )

# ---- compatibility with l4=0 constraint
pr()
pr(
    "Compatibility (tune fixed, k1 floated). Delta vs l4=0 best (1 dof: the lambda2_nu direction) and vs the free "
    "(l2,l4) best at linf=2 (2 dof). 1D pull uses the stat+syst sigma."
)
tunes = [
    ("card anchor / FranksVals", dict(linf=2.0, l2=0.15, l4=0.0)),
    (
        "Tackmann/AN as is (linf 1.6853, l4 0.0074)",
        dict(linf=1.6853, l2=0.087, l4=0.0074),
    ),
    ("Tackmann l2 centre at l4=0, linf=2", dict(linf=2.0, l2=0.087, l4=0.0)),
    ("Tackmann l2 +1sigma (0.1202) at l4=0, linf=2", dict(linf=2.0, l2=0.1202, l4=0.0)),
    ("lambda2_nu=0 (switched off)", dict(linf=2.0, l2=0.0, l4=0.0)),
]
comp = []
for lab, lam in tunes:
    c, th = CP.chi2_fixed(lam)
    d1 = c - nom["chi2"]
    d2 = c - f2["chi2"]
    pull = (lam["l2"] - mu) / s_tot if lam["l4"] == 0 and lam["linf"] == 2.0 else np.nan
    z1 = norm.isf(chi2dist.sf(max(d1, 0), 1) / 2)
    z2 = norm.isf(chi2dist.sf(max(d2, 0), 2) / 2)
    comp.append(
        dict(
            label=lab,
            lam=lam,
            chi2=c,
            d_l4zero=d1,
            z1=z1,
            d_2d=d2,
            z2=z2,
            pull_tot=pull,
            k1=th[0],
        )
    )
    pr(
        f"  {lab:46s} chi2={c:6.2f}  d(l4=0 best)={d1:6.2f} ({z1:.1f}s, 1dof)  d(2D best)={d2:6.2f} ({z2:.1f}s, 2dof)"
        f"  pull(stat+syst)={pull:+.2f}"
    )
for t in CP.TUNES[1:6]:
    c, _ = CP.chi2_fixed(t["lam"])
    pr(
        f"  [postfit] {t['label']:46s} chi2={c:6.2f}  d(l4=0 best)={c - nom['chi2']:6.2f}"
    )

# ---- MCMC band for the l4=0 fit (flat prior on l2, k1)
free = ["l2", "k1"]
ch, acc = CP.mcmc(
    free,
    {"linf": 2.0, "l4": 0.0},
    [0.135, 0.21],
    CP.chol_step("tanh2 | l4=0, linf=2 | k1"),
)
q = np.percentile(ch, [16, 50, 84], axis=0)
pr(
    f"\nMCMC (l4=0, linf=2, k1): acc {acc:.2f}; l2 median {q[1, 0]:.4f} [68% {q[0, 0]:.4f}, {q[2, 0]:.4f}]"
)
bg = CP.bgrid
sub = ch[:: max(1, len(ch) // 4000)]
curves = np.array([KF.np_zeta(bg, 2.0, x[0], 0.0) for x in sub])
np.save(os.path.join(HERE, "chain_l4zero.npy"), ch)
np.savez(
    os.path.join(HERE, "bands_l4zero.npz"),
    bgrid=bg,
    lat_l4zero_np=np.percentile(curves, [2.5, 16, 50, 84, 97.5], axis=0),
    lat_l4zero_totband_np=np.array(
        [
            KF.np_zeta(bg, 2.0, mu - s_tot, 0.0),
            KF.np_zeta(bg, 2.0, mu, 0.0),
            KF.np_zeta(bg, 2.0, mu + s_tot, 0.0),
        ]
    ),
)
json.dump(
    dict(
        fits=res,
        lambda2_nu=dict(
            central=mu,
            stat=s_stat,
            syst=s_syst,
            tot=s_tot,
            chosen={g: [v, d] for g, (v, d) in chosen.items()},
        ),
        compat=comp,
    ),
    open(os.path.join(HERE, "fit_l4zero.json"), "w"),
    indent=1,
)
open(os.path.join(HERE, "l4zero_output.txt"), "w").write("\n".join(lines) + "\n")
