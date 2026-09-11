#!/usr/bin/env python3
"""Projected saturated statistic on ptll, computed OFFLINE from the saved
postfit histograms -- no fit, no refit, no rabbit composite model.

WHAT THIS IS.  rabbit's --computeSaturatedProjectionTests reports

    q = 2 * ( NLL(main postfit) - NLL(saturated) ),   ndf = n_ptll = 39

where NLL(saturated) is the minimum over 39 free per-ptll-bin yield scale
factors r_j AND all the model's own parameters.  This script computes the same
statistic with the model's parameters HELD at the main postfit, i.e. it
profiles only the 39 r_j.  For the Poisson likelihood rabbit uses
(fitter.py:_compute_ln, no --chisqFit, --noBinByBinStat) that profile is
CLOSED FORM: within one output bin j the r_j-dependence is
sum_i [ r_j N_i - D_i log(r_j N_i) ], minimised at r_j = D_j / N_j with
D_j, N_j the projected data and prediction.  So

    q_fixed = 2 * sum_j [ N_j - D_j + D_j log(D_j / N_j) ] ,

which is the grouped Poisson deviance of the projected residuals.

WHY IT IS A BOUND, AND WHICH WAY.  Letting the other parameters move as well
can only lower NLL(saturated), so

    q_true >= q_fixed        and        p_true <= p_fixed .

The number below is therefore an UPPER BOUND on the projected saturated
p-value: a small p_fixed is conclusive, a large one is not.

WHY IT IS PENALTY-FREE.  The wall penalty and the Gaussian constraint term lc
depend only on the model's parameters, which are held, so they cancel
identically in the difference.  The walled and unwalled q_fixed are therefore
directly comparable with no penalty subtraction -- unlike the whole-fit
saturated chi2, where the walled value has to be corrected by hand.
"""
import sys

import numpy as np
from scipy.stats import chi2

sys.path.insert(0, "/work/submit/lavezzo/alphaS/rabbit-blinding")
from rabbit import io_tools  # noqa: E402

ARMS = [
    ("unwalled (DATABLIND)", sys.argv[1]),
    ("walled tau=5 (DATAWALL5)", sys.argv[2]),
]
out = {}

for label, fr in ARMS:
    res, meta = io_tools.get_fitresult(fr, meta=True)
    ch = res["mappings"]["BaseMapping"]["channels"]["ch0"]
    hN = ch["hist_postfit_inclusive"].get()
    hD = ch["hist_nobs"].get()
    N2 = hN.values()  # (ptll, yll) postfit prediction
    D2 = hD.values()  # (ptll, yll) observed
    ptll_edges = np.asarray(hN.axes["ptll"].edges)

    # --- validation: reproduce rabbit's own reduced NLL from these two hists.
    # reduced ln = sum_ij [ N - D + D log(D/N) ] / 1  (fitter.py:2153-2157)
    dev_bin = N2 - D2 + np.where(D2 > 0, D2 * np.log(np.where(D2 > 0, D2, 1) / N2), 0.0)
    ln_full = dev_bin.sum()
    nllred = float(res["nllvalreduced"])
    ndfsat = int(res["ndfsat"])
    chi2_full_rabbit = 2.0 * nllred

    # --- the projection
    Nj = N2.sum(axis=1)
    Dj = D2.sum(axis=1)
    rj = Dj / Nj
    q_bin = 2.0 * (Nj - Dj + Dj * np.log(Dj / Nj))
    q = q_bin.sum()
    ndf = len(Nj)
    p = chi2.sf(q, ndf)
    # Gaussian cross-check of the same thing
    q_gauss = float(np.sum((Dj - Nj) ** 2 / Nj))

    print("=" * 78)
    print(f"{label}\n  {fr}")
    print(
        f"  hists: postfit_inclusive / nobs, ({N2.shape[0]} ptll x {N2.shape[1]} yll)"
    )
    print(
        f"  total data {Dj.sum():.6g}   total postfit {Nj.sum():.6g}   "
        f"ratio {Dj.sum() / Nj.sum():.6f}"
    )
    print("  -- validation against rabbit's own whole-fit numbers")
    print(f"     2*sum_ij deviance/2 (Poisson part only) = {2 * ln_full:.4f}")
    print(
        f"     rabbit 2*nllvalreduced (ln + lc [+ wall]) = {chi2_full_rabbit:.4f}"
        f"   (ndfsat={ndfsat})"
    )
    print(
        f"     difference = 2*(lc [+ penalty])          = "
        f"{chi2_full_rabbit - 2 * ln_full:.4f}"
    )
    print("  -- projected onto ptll (39 bins)")
    print(
        f"     q_fixed = {q:.3f}   ndf = {ndf}   "
        f"p_fixed = {100 * p:.3f}%   (UPPER bound on p_true)"
    )
    print(f"     Gaussian cross-check sum (D-N)^2/N = {q_gauss:.3f}")
    print(
        f"     r_j = D_j/N_j : min {rj.min():.4f}  max {rj.max():.4f}  "
        f"mean {rj.mean():.4f}"
    )
    print(
        f"     any r_j <= 0 ? {bool((rj <= 0).any())}   "
        f"min N_j = {Nj.min():.4g}  min D_j = {Dj.min():.4g}"
    )
    # --- EXACT partition of the whole-fit deviance.  For the Poisson
    # deviance D(D||N) = 2 sum [N - D + D log(D/N)], writing N'_ij = N_ij r_j
    # with r_j the group ratio gives, identically,
    #     D(780 bins) = D_ptll(39 groups) + D(D_ij || N_ij r_j) ,
    # i.e. "the ptll marginal" plus "the yll shape within each ptll bin".
    # (The cross terms cancel because sum_ij D_ij log r_j = sum_j D_j log r_j.)
    Np = N2 * rj[:, None]
    d_cond = 2.0 * np.sum(
        Np - D2 + np.where(D2 > 0, D2 * np.log(np.where(D2 > 0, D2, 1) / Np), 0.0)
    )
    print("  -- exact partition of the whole-fit Poisson deviance")
    print(f"     D(780)      = {2 * ln_full:.4f}")
    print(f"     D_ptll(39)  = {q:.4f}")
    print(f"     D_cond      = {d_cond:.4f}   (yll shape within each ptll bin)")
    print(f"     closure     = {2 * ln_full - q - d_cond:+.3e}")
    # rabbit's whole-fit saturated chi2 includes the Gaussian constraint term
    # lc (the constraints are auxiliary measurements, which is why ndfsat =
    # nbins - nparams(model) and the 3673 constrained nuisances cancel out of
    # it).  lc is held, so it belongs entirely to the conditional piece.
    q_cond_rabbit = chi2_full_rabbit - q
    ndf_cond = ndfsat - ndf
    print(
        f"     rabbit-convention residual = {q_cond_rabbit:.3f} on ndf "
        f"{ndf_cond}  ->  p = {100 * chi2.sf(q_cond_rabbit, ndf_cond):.3f}%"
    )
    print(
        f"     (whole fit was {chi2_full_rabbit:.3f} on {ndfsat}  ->  p = "
        f"{100 * chi2.sf(chi2_full_rabbit, ndfsat):.3f}%)"
    )

    worst = np.argsort(-q_bin)[:6]
    print("     largest contributions (bin: ptll range, q_bin, pull, r_j):")
    for i in worst:
        pull = (Dj[i] - Nj[i]) / np.sqrt(Nj[i])
        print(
            f"       {i:2d}: [{ptll_edges[i]:5.1f},{ptll_edges[i + 1]:5.1f}) "
            f"q={q_bin[i]:7.3f} pull={pull:+6.2f} r={rj[i]:.4f}"
        )
    out[label] = dict(
        Nj=Nj,
        Dj=Dj,
        rj=rj,
        q_bin=q_bin,
        q=q,
        ndf=ndf,
        p=p,
        edges=ptll_edges,
        fr=fr,
    )

print("=" * 78)
(la, a), (lb, b) = list(out.items())
print("SIDE BY SIDE (projected saturated statistic, ptll, ndf=39)")
print(f"  {la:28s} q_fixed={a['q']:8.3f}  p_fixed={100 * a['p']:7.3f}%")
print(f"  {lb:28s} q_fixed={b['q']:8.3f}  p_fixed={100 * b['p']:7.3f}%")
print(f"  Delta q (walled - unwalled) = {b['q'] - a['q']:+.3f}")
np.savez(
    sys.argv[3],
    **{
        f"{k}_{n}": v
        for k, d in out.items()
        for n, v in d.items()
        if isinstance(v, np.ndarray)
    },
)
print(f"wrote {sys.argv[3]}")
