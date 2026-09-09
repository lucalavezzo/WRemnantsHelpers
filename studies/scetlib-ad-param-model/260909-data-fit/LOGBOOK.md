---
task: data-fit
updated: 2026-09-09
---

# First fit to data with the scetlib_ad param model

## START HERE

**State.** Three runs. Card
`260908_Z_2D_card_acceptfix/ZMassDilepton_ptll_yll_adexclpdf` (**2D**, 780 reco
bins), cache `pdf62_corrgrid_260827/merged_full`, SCETlib `b66f8de` + the hvp
zero-skip. **Blinded** -- no `--unblind`, so an unknown shift is added to the
alphaS POI; uncertainties, pulls and impacts are meaningful, the central value
is not.

| run | rabbit | what | outcome |
|---|---|---|---|
| `DATA` | main tree `5bc7aad` | as-is, nothing frozen | **FAILED** 23:37, non-PD Hessian |
| `DATANOH` | main tree `5bc7aad` | `--noHessian` (Hessian-free CG) | running |
| `DATAPC` | **PR #150** `0709702` | `--precondition` | running |

**Logs** are in this directory: `01_data_fit.log`, `02_data_noh.log`,
`03_data_pc.log`. **Fitresults** at
`/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/study_scratch/260909-data-fit/fitresults_{DATA,DATANOH,DATAPC}.hdf5`.

**Next step.** Read the postfit p-value off whichever run reaches the postfit
block. For scale, not as a criterion: Luca recalls old 2D fits landing near
80%, offered explicitly as a rule of thumb rather than a benchmark. The useful
comparison is against the **26.6% prefit** on this same card -- a converged fit
should be clearly above it, and a postfit p near 26% would mean the minimiser
barely moved the likelihood.

**Blocking.** Nothing.

## Findings

### The as-is fit stalled short of a minimum, in the PDF block

619 iterations over 2404 s, loss 4.74e7 -> 2.96e4, then it died in `edmval_cov`:

```
LinAlgError: Internal potrf return info = 27
ValueError: Cholesky decomposition failed, Hessian is not positive-definite
```

The last **100 iterations are bit-identical** (29634.19096568575 from iteration
518), i.e. `--earlyStopping 100` fired on a stall: outer steps were being
rejected and it stopped short of a stationary point, so the Hessian there has a
negative direction. Total wall 44:49 -- NOT the "very slow" branch.

`potrf info = 27` is the 27th leading minor. `alphaS` is the unpriored POI at
fit index 1 and the 46 POUs follow in the order the prior list prints them, so
index 27 = POU 26 = **`pdfEig8`**. The bad direction is in the PDF eigenvector
block, **not** the NP sector. That is consistent with the reco-variation
validation, where PDF directions have the worst residual *as a fraction of
their own response* (`rel_total` = 0.10 for `pdf3`).

### The reference Hessian is indefinite by a wide margin, and the preconditioner says so out loud

PR #150's block finder reports, at the reference point:

```
Preconditioning block auto30 has no positive diagonal (max diag = -5310.73); skipping.
Preconditioning block auto32 has no positive diagonal (max diag = -28696.84); skipping.
Preconditioning block auto33 has no positive diagonal (max diag = -2124.63); skipping.
Preconditioned 13 of 34 block(s), 26 parameters; correlation condition number
median 1, worst 1.8e+03 -> 1 at the reference point
```

So this is not a marginal numerical failure: whole blocks have **negative
diagonal curvature**, one at -2.9e+04. Cholesky cannot touch those and the
preconditioner correctly skips them. Where it did apply, it flattened the worst
correlation condition number from 1.8e+03 to 1.

### The p-value quoted from the failed run was PREFIT

chi2 = 804 / 780 dof, p = 26.56% sits at log line 73; `Perform iterative fit`
is at line 77. So it describes the model at the cache anchor with nothing
fitted. A converged run prints `Linear chi2` **twice** (prefit and postfit) --
the Asimov fit does; the data fit printed it once. **There is no postfit
goodness-of-fit from that run.** I reported it as "the fit quality was fine",
which was wrong.

Read positively, a 26.6% prefit p is a healthy starting point: the anchor
already describes the data before any parameter moves.

### Defaults applied Gaussian priors to 46 of 47 model parameters

`lambda2` mu=0.4 sigma=0.5, `lambda4` mu=0.4 sigma=0.5, `delta_lambda2` sigma=0.5,
`lambda2_nu` mu=0.15 sigma=0.1, `lambda4_nu` sigma=0.5, the resumTNP/scale/transition
set, and the PDF eigenvectors at sigma=1. Only `alphaS` is unpriored. Luca's
standing preference on record is lambdas free with no priors, so "run it as is"
and that preference disagree -- flagged, not yet changed.

This also matters for the preconditioner: its DEFAULT target is every
*unconstrained* parameter, which here is `alphaS` alone. The block that fails
is the priored PDF eigenvectors, so `--preconditionParams` names the theory
block explicitly and `--preconditionBlocks auto` finds the clusters from the
correlation matrix rather than trusting that naming.

## Decisions

`--earlyStopping 100` on every data run. With `tol=0.0` every scipy tolerance
is 0 and trust-krylov otherwise runs to `maxiter = len(x)*200`; we have seen
63,554 iterations over 21.8 h. 100 is what the toys used and is well above the
~20 that silently aborts a healthy fit.

`--noHessian` **without** `--noEDM`: the EDM then comes from Hessian-free CG,
which avoids the Cholesky that killed the first run while still giving a
convergence measure. Adding `--noEDM` would have thrown that away.

## Log

**2026-09-08 22:52.** Launched the as-is data fit. Failed 23:37.

**2026-09-09 09:12 / 09:14.** Launched the `--noHessian` diagnostic and the
preconditioned run. Fetched rabbit PR #150 and verified it is a superset of our
WIP for everything the model needs (`paramPriors`, `prior_sigmas`,
`externalPostfit`, `doImpacts`, `edmval` all present at >= our counts;
`workspace.py` and `svd.py` byte-identical). Ours-only are
`rabbit_merge_fitresults.py` and `io_tools.py`, neither used by a fit.
Worktree at `/work/submit/lavezzo/alphaS/rabbit-pr150`.
