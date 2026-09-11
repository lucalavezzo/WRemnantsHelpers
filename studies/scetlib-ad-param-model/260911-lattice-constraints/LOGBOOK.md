---
title: Lattice CS-kernel constraint ported to scetlib_ad
slug: 260911-lattice-constraints
study: scetlib-ad-param-model
status: done
created: 2026-09-11
updated: 2026-09-11
owner: study-worker
---

# Lattice CS-kernel constraint ported to scetlib_ad

**Task:** Can the lattice CS-kernel constraint used in the `scetlib_np` work be ported to the
`scetlib_ad` param model — where the fitted lambdas are *unit nuisances*, not physical
lambdas — and under it, does the blinded data fit keep the NP sector physical with
**data-determined** uncertainties, unlike the wall where `lambda2_nu` rails?

---

## START HERE (status as of 2026-09-11)

> **Ported, verified, fitted. The lattice prior works mechanically and gives the
> best-converged arm of the five — but it does NOT keep the NP function physical: it
> relocates the violation from the CS kernel into the unconstrained TMD boundary
> condition.**
>
> The CS sector is fixed properly (`lambda2_nu` **-0.0583 -> +0.1260**, inside the lattice
> 1 sigma, `chi2_lat = 2.12` on 2 dof, p = 35 %) and the uncertainties there are
> **interior and part-data** — along the prior's loose eigendirection the posterior is
> 81.5 % narrower in variance than the prior, against the wall where `lambda2_nu`'s sigma
> is **98.6 % of the barrier width**. Cost: `D(chi2_data) = +11.7` vs the free fit, i.e. **p = 0.29 %, ~3
> sigma** as a 2-dof test — real tension, but 3 sigma and not the 15 sigma the raw
> `chi2_lat = 229.6` at the free minimum suggests.
>
> **The catch:** `lambda2` goes **-0.138**, so `L2 < 0` at every rapidity and the TMD form
> factor **anti-damps by up to 29 %** out to `b_T = 1.6 GeV^-1` — inside the alpha_s-sensitive
> window. 3 of 8 damping conditions fail (1 of 8 walled). Constraining only the CS side
> reroutes the pathology.
>
> Convergence: **EDM 9.83e-08**, 134 iterations, 0 negative eigenvalues — the best of the
> five arms. `sigma(alpha_s) = 0.000980`; saturated p **0.82 %** (external term removed).
> **Basin: `{plain, walled}`** (L2 1.41 / 2.52) not `{ridge, spectral}` (3.95 / 4.10) — the
> basin is set by the perturbative/PDF block, not by the lambdas.
>
> Read the first caveat in **Result** before quoting anything: `knowledge/` explicitly says
> this covariance must not be used as a fit prior.

- **Next action:** none — task closed. The obvious follow-up is **lattice prior + damping
  wall** (one 25-minute arm), see *Open questions*.
- **Blocking on:** nothing.

---

## Log

### 2026-09-11 — which mechanism the `scetlib_np` work used

Found in `studies/np-wall-local-minima/`: the lattice constraint rode as a rabbit
**EXTERNAL LIKELIHOOD TERM written into a copy of the datacard**
(`scripts/inject_lattice_cs_prior.py`, cards `ZMassDilepton_latticeCS{,2}.hdf5`),
**not** as `prior_sigmas` and **not** as a `Regularizer`. Both alternatives were
considered and rejected in that script's own docstring, for reasons that still hold:

* `prior_sigmas` is a **1-D array — diagonal only**. The lattice constraint's content is
  largely its *correlation*: `rho(lambda2_nu, lambda4_nu) = -0.9135` marginal. A `b^2`
  and a `b^4` coefficient fitted to the same curve are near-degenerate, and in the 2x2
  used here the constrained eigendirection is **5731x** narrower than the free one.
  Dropping the correlation is not a small approximation.
* a `Regularizer` would work algebraically, but `fitter.py` multiplies **every**
  regularizer by the one shared `exp(2*tau)` — already spoken for by the damping wall at
  `--regularizationStrength 5`, i.e. `e^10 = 22026`.

The external mechanism is a separate additive term (`Fitter._compute_external_nll`), is
not scaled by tau, and resolves names against
`concat([param_model.params, indata.systs])` — so the model's lambdas are addressable.
For a Gaussian `N(mu, C)` on a subset, `H = C^-1`, `g = -C^-1 mu`.

Two things the `scetlib_np` runs did alongside it, both carried over here:

* **condition, don't marginalise.** `lambda_inf_nu` is frozen in the fit, so the 3x3
  lattice covariance is conditioned on that held value. With it *floating* under the 3x3
  the `scetlib_np` fit drove it to **0.0098**, switching the CS kernel off entirely — its
  30% lattice uncertainty is too loose to prevent that (`QUEUE.md`, run `latticeCov_priors`,
  "PATHOLOGICAL, do not use").
* **free the lambdas the external term now constrains**, or the model's own priors
  double-count. In `scetlib_np` that was `prior_sigmas=lambda2_nu=nan,lambda4_nu=nan`;
  the same token exists here and is used.

**Numbers** (unchanged, physical units): AN-25-085 eq. `nplunc` == Cridge/Marinelli/Tackmann
[arXiv:2506.13874](https://arxiv.org/abs/2506.13874) Eqs. (3.34)/(3.35) —
`lambda_inf_nu = 1.6853 +- 0.5069`, `lambda2_nu = 0.0870 +- 0.0332`,
`lambda4_nu = 0.0074 +- 0.0066`, `rho = (+0.5212, -0.7249, -0.9135)`. That fit used the
**tanh_2** form; this card's `np_model_nu` is `tanh_2`, so the parametrisations match and
the injector **refuses** any other CS form.

### 2026-09-11 — the card: what "Lattice" in its name does and does not mean

The card's recorded correction is
`scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_CorrZ.pkl.lz4`.
The brief asked whether its central tune is already lattice-derived, so that a lattice
prior would double-count. **It is not, and there is no double count. Three separate
checks** (evidence: `logs/probe_260910_214542.log`):

1. **The central is not the lattice central.** The runcard's `Nonperturbative` section has
   `lambda2_nu = 0.15`, `lambda4_nu = 0.`, `lambda_inf_nu = 2.` — the "FranksVals" tune,
   which sits **+1.90 / -1.12 / +0.62 sigma_lat** from the lattice marginals. "Lattice" in
   the tag names the *variation templates* the correction carries, not its central.
   (Consistent with `studies/np-wall-local-minima/LOGBOOK.md`, which records the same
   +1.9/-1.1/+0.62.)
2. **Those variation templates are not in this card.** Of 3673 systematics, **zero** match
   `scetlibNP*` / `*Lattice*` / `*ambda*` / `*gamma*`. The param model replaces the NP
   template nuisances outright, so no lattice-derived Gaussian is already in the
   likelihood. The card also carries **no `external_terms` group**.
3. **But the MODEL does put a prior on these lambdas, and that one had to be removed.**
   `SCETlibADParamModel` has `priors=True` by default and `params.FREE_PARAMS` frees only
   `alphaS` and the frozen shape constants — so all five reparametrised lambdas carry a
   `sigma = 1` **theta** prior, which is physically `lambda2_nu = 0.15 +- 0.10` and
   `lambda4_nu = 0 +- 0.50` (the `params.REPARAM` widths). The existing arms are therefore
   "NP free" only in the sense of *no wall and no external input*; the NP sector was
   constrained at the card's own widths all along. Under the plain arm's tune that prior is
   already a **-2.08 sigma** pull on `lambda2_nu`. The lattice arm passes
   `prior_sigmas=lambda2_nu=nan,lambda4_nu=nan` so the lattice term is the sole constraint
   on the CS kernel; the three TMD lambdas keep their `sigma = 1` priors, because the
   lattice says nothing about the TMD boundary condition and AN-25-085 is explicit that it
   has no robust external constraint.

### 2026-09-11 — THE THETA CONVERSION, verified before fitting

`scripts/inject_lattice_cs_prior_theta.py` (evidence: `logs/inject_260910_215009.log`).
Anchors and widths come from the same authority the model and the wall use —
`np_damping_wall.resolve_wall_inputs`, i.e. `params.REPARAM` for the width and the card's
recorded correction runcard for the anchor. Nothing is hardcoded.

Conditioning the 3x3 on `lambda_inf_nu = 2.0` (the card's own held value, **not** the
lattice mean 1.6853, so the means shift as well as tighten):

| | marginal | conditional on `lambda_inf_nu = 2.0` |
|---|---|---|
| `lambda2_nu` | 0.0870 +- 0.0332 | **0.097743 +- 0.028334** |
| `lambda4_nu` | 0.0074 +- 0.0066 | **0.004430 +- 0.004546** |
| `rho` | -0.9135 | **-0.911192** |

Pushed through `physical = anchor + width*theta` with `W = diag(0.10, 0.50)`:

    mu_theta = W^-1 (mu - anchor)      C_theta = W^-1 C W^-1
    H_theta  = W C^-1 W                g_theta = -W C^-1 (mu - anchor)

giving `lambda2_nu: theta ~ N(-0.522572, 0.283340)` and
`lambda4_nu: theta ~ N(+0.008859, 0.009093)`, `rho` unchanged at -0.911192.
Note the direction of `W`: `H` is pre- and post-multiplied by `W`, **not** by `W^-1`.
Getting that backwards is silent and would scale `lambda2_nu`'s prior by 100x one way and
1/100 the other.

Four numerical checks, all before the card was written:

1. **the map is the model's own map** — `anchor + width*theta` against
   `np_damping_wall.physical_from_theta` over 20 000 draws: max abs diff **0.000e+00**.
2. **chi2 invariance** physical vs theta over the same draws: max rel diff **7.49e-15**.
3. **zero at the prior mean**: `-5.3e-15`; **1 along each covariance eigendirection**:
   `1.000000000` both.
4. **the correlation is really carried**: walking one axis by its *marginal* sigma gives
   `chi2 = 5.891709`, and `1/(1-rho^2) = 5.891709`. That number **is** the reason a
   diagonal `prior_sigmas` is not this constraint.

Round-tripped through `rabbit.read_external_terms_from_h5` **and**
`build_tf_external_terms`; rabbit's own recomputed `const` (3.169948) matches ours to
1e-9, so the term is exactly 0 at the prior mean and NLLs stay comparable.

**Conditioning matters for the conditioning number too.** In theta the 2x2 has covariance
eigenvalues `1.40e-05 / 8.04e-02` (cond **5731**) and Hessian eigenvalues
**12.4 / 71 320**. That stiff direction is ~70 000x the O(1) curvature of a `sigma=1`
prior, and it is the reason `QUEUE.md` warns that the lattice term can stall `trust-krylov`.
Watch the iteration count and the EDM before believing anything else.

### 2026-09-11 — the fit

`scripts/launch_lattice_fit.sh` -> `logs/fit_DATALAT_*.log`. Identical to the plain
`DATABLIND` and walled `DATAWALL5` arms in everything else: same cache
`pdf62_corrgrid_260827/merged_full`, SCETlib `b66f8de` (`libscet-qT.so` md5 `71b5e68a...`),
rabbit `blinding-additive` @ `0f64bbb` (the additive-blinding assertion in
`scripts/incontainer.sh`, md5 `f6f87d52...`, passed), real data `-t 0`,
`--earlyStopping 100`, `threads=128`, `--snapshotFile`. Two differences, both the
measurement: the card carries the `lattice_cs` external term, and
`prior_sigmas=lambda2_nu=nan,lambda4_nu=nan`. No wall. `--doImpacts` dropped, as in the
walled arm.

Card: `/ceph/.../study_scratch/260911-lattice/card_latticeCS.hdf5` (a copy of
`card_none.hdf5` plus one `external_terms` group; nothing else moves).
Fitresult: `/ceph/.../260911_lattice/fitresults_DATALAT.hdf5`.

### 2026-09-11 — the fit landed

`logs/fit_DATALAT_260910_215144.log`, 23:48 wall clock, 184.7 GiB peak, scipy
`status: 2` ("a bad approximation caused failure to predict improvement") at iteration 134.
Read out five-way with `scripts/compare_lattice.py`
(-> `logs/compare_260910_221613.log`), which imports
`../260910-spectral-precond/scripts/compare_arms.py` for the four existing arms' numbers
and the wall's theta->physical resolver, reads the lattice prior back **out of the card**
rather than re-typing it, and decomposes every arm's loss into
`ln(data) + lc + lpenalty + lext`. Figures from `scripts/plot_np_forms_lattice.py`.

Two checks worth recording separately. The lattice term was **demonstrably active**: with
its own `sigma = 1` prior removed, nothing else pulls `lambda2_nu` upward (the removed
prior's mean was 0.15, and the free fit with it landed at -0.058), yet the arm lands at
+0.126 with `lambda4_nu` inside the lattice's +-0.0045 rather than the free fit's +0.054.
And the card is the production card plus exactly three datasets, verified dataset by
dataset (`logs/diffcards_221333.log`).

---

## Result

**Comparability caveats, first.**

* **This constraint is one `knowledge/` says not to use.**
  `knowledge/30_physics_global/np_parametrization_constraints.md` section 10: *"DO NOT USE
  THIS COVARIANCE AS A FIT PRIOR"* (Luca, 2026-07-29, from the lattice authors: the
  covariance is not ready to be trusted), and section 11 recommends "bracket, don't prior".
  This task implements the prior on the brief's instruction so the tension can be measured.
  Every number below inherits that caveat. The **central** curve is on much firmer ground
  than the band (section 13), which matters: the conclusions here that depend only on the
  central are more robust than those that depend on the widths.
* Blinded real data (`-t 0`), alphaS blinded **additively**; no central value appears here
  or in any log in this directory. Same card contents, cache, SCETlib build, rabbit build
  and flags as the plain `DATABLIND` and walled `DATAWALL5` arms, so losses, EDM and
  p-values are directly comparable — the card differs *only* by the added
  `external_terms/lattice_cs` group (all 27 shared datasets byte-identical, 11 decoded and
  16 by raw-chunk md5; evidence: `logs/diffcards_221333.log`).
* **`fun` is not comparable across arms as printed.** Each arm's loss carries a different
  mix of penalty terms, so everything below is quoted from an explicit decomposition
  `fun = ln(data) + lc(model+card priors) + lpenalty(wall) + lext(lattice)`, computed from
  each arm's own postfit theta.
* The lattice arm **frees** `lambda2_nu` and `lambda4_nu` from the model's default
  `sigma = 1` theta priors, so it has 44 rather than 46 constrained model parameters. That
  is required (or the CS sector is double-counted), and it is why `lc` differs.
* `--doImpacts` was not run, as in the walled arm. The NP-group impact on alpha_s under a
  lattice prior is therefore unmeasured.

### Convergence FIRST

| | plain | ridge | spectral | walled | **lattice** |
|---|---|---|---|---|---|
| `fun` (mixed content) | 405.5609 | 411.0754 | 412.7846 | 411.9912 | **415.0831** |
| scipy status | 2 | 2 | SIGTERM | 2 | **2** |
| iterations | 221 | 292 | 719 (stopped) | 138 | **134** |
| minimize() [s] | 2645 | 4049 | 8594 | 1509 | **1209** |
| **EDM** | 1.386e-03 | 4.909e-06 | 1.457e-07 | 9.632e-07 | **9.831e-08** |
| negative Hessian eigenvalues | 0 | 0 | 0 | 0 | **0** |
| full-cov condition number | 2.98e+09 | 4.62e+10 | 1.08e+10 | 2.06e+08 | **4.86e+08** |
| **sigma(alpha_s)** | 0.001321 | 0.000877 | 0.000856 | 0.001097 | **0.000980** |
| saturated 2*dNLL / 733 | 811.12 | 822.15 | 825.57 | 823.98 | **830.17** |
| saturated p, as logged | 2.33 % | 1.20 % | 0.96 % | 1.07 % | **0.71 %** |
| saturated p, penalty removed | 2.33 % | 1.20 % | 0.96 % | 1.16 % | **0.82 %** |
| card nuisances > 2 sigma (of 3673) | 0 | 1 | 1 | 0 | **0** |

**It is the best-converged arm of the five.** EDM `9.83e-08`, in the fewest iterations and
the least minimiser time, with zero negative eigenvalues. The `QUEUE.md` warning that the
lattice term stalls `trust-krylov` did **not** materialise — because in theta the
conditional 2x2 has condition number 5731 against 7.5e4 for the physical 3x3 the
`scetlib_np` runs used, a 13x improvement that comes free with the unit-nuisance
reparametrisation. There were a few 30-80 s Krylov solves near the end, but scipy
terminated on its own at iteration 134. Total wall clock **23:48**.

Quote the **penalty-removed** saturated p-value, 0.82 %: the external term's value at the
postfit (`lext = 1.0601`) enters the fit NLL and so the saturated statistic twice over.
(The same correction is why the walled arm is quoted at 1.16 % rather than 1.07 %.)

### The NP tune, and whether the damping conditions hold

| physical lambda | anchor | plain | walled | **lattice** | lattice prior |
|---|---|---|---|---|---|
| `lambda2` | 0.4 | 0.300643 | 0.108109 | **-0.138292** | (unconstrained) |
| `lambda4` | 0.4 | -0.002666 | 0.124033 | **+0.086381** | (unconstrained) |
| `delta_lambda2` | 0 | -0.024343 | -0.013023 | **-0.010744** | (unconstrained) |
| `lambda2_nu` | 0.15 | -0.058284 | +0.004872 (railed) | **+0.125951** | 0.097743 +- 0.028334 |
| `lambda4_nu` | 0 | +0.053686 | -0.000427 | **-0.001685** | 0.004430 +- 0.004546 |

**The CS sector is fixed, and fixed properly.** `lambda2_nu` goes -0.0583 -> **+0.1260**, so
the CS kernel no longer anti-damps at small `b_T`, and the postfit CS pair sits **inside the
lattice 1 sigma ellipse**: `chi2_lat = 2.12` on 2 dof, **p = 35 %**. As a function,
`gamma_nu^NP(b_T=1,2,3) = -0.124 / -0.468 / -0.922` against the lattice central
`-0.102 / -0.454 / -1.101` — see `np_form_factors_lattice.png`, top panels, where the blue
curve tracks the band. Compare the walled arm, whose CS kernel is
`-0.004 / -0.013 / -0.009`, i.e. switched **off**.

**But the NP function as a whole is now MORE unphysical, not less: 3 of 8 damping
conditions fail, against 1 of 8 walled and 2 of 8 free.** The excursion did not go away; it
**moved into the TMD boundary condition**, which the lattice does not constrain:

| condition | plain | walled | **lattice** |
|---|---|---|---|
| `lambda2_nu >= 0` (CS small-b) | **-0.0583** | +0.0049 | **+0.1260** ok |
| `lambda4_nu >= 0` (CS large-b) | +0.0537 | **-4.3e-4** | **-1.7e-3** |
| `L2 >= 0` at `|Y|=0` (TMD small-b) | ok | ok | **-0.1383** |
| `L2 >= 0` at `|Y|=2.5` | ok | ok | **-0.2054** |
| `3 linf^2 lambda4 + L2^3 >= 0` at `|Y|=2.5` | **-0.0047** | ok | ok |

and the TMD failure is the **consequential** kind, not the cheap kind:

| | max `f^NP` | at `b_T` | `f^NP > 1` out to |
|---|---|---|---|
| anchor / plain / walled | 1.0000 | — | never |
| **lattice**, `|Y| = 0` | **1.118** | 0.90 | 1.27 GeV^-1 |
| **lattice**, `|Y| = 2.5` | **1.286** | 1.11 | 1.57 GeV^-1 |

The TMD form factor **anti-damps by up to 29 %** over `b_T < 1.6 GeV^-1` — inside the
`b_T = 0.5-3 GeV^-1` window the qT spectrum is sensitive to
(`np_parametrization_constraints.md` section 10, fact 1). `f^NP` multiplies the integrand
directly, so this is a larger effect on the prediction than the free fit's CS violation
(`gamma_nu^NP` reaching only +0.005 at `b_T = 1`). The remaining CS failure,
`lambda4_nu = -1.7e-3`, is the cheap one: it moves anti-damping to `b_T > 8.65 GeV^-1`,
where the tanh is saturated and `f^NP` has already killed the integrand.

**Physics read.** The data want *less* net NP damping at intermediate `b_T` than any
physical tune of this parametrisation provides. The free fit buys that with a wrong-sign CS
kernel; the wall forbids that and the fit buys it instead by switching the CS kernel off;
the lattice prior forbids *both* and the fit buys it from the TMD boundary condition,
which is the one sector with no external constraint at all (AN-25-085 says so outright, and
section 11 of the knowledge note repeats it). **Constraining only the CS side reroutes the
pathology rather than removing it.** That is the single most important thing this task
found, and it is exactly what one should expect once
`rho(lambda4, lambda2_nu) = -0.996` (recorded in the `scetlib_np` work) is taken seriously:
the two sectors are near-degenerate in their effect on the spectrum.

### What the lattice constraint costs, and what it adjudicates

| arm | `ln(data)` | `D(chi2_data)` vs plain | `chi2_lat` at its tune | lattice p |
|---|---|---|---|---|
| plain | 388.8658 | 0 | **229.6** | 0.0000 % (15.0 sigma) |
| walled | 393.2183 | +8.705 | **107.6** | 0.0000 % (10.1 sigma) |
| ridge | 393.7990 | +9.866 | 12.28 | 0.216 % (3.1 sigma) |
| spectral | 395.0609 | +12.390 | **2.10** | 35.1 % (0.9 sigma) |
| **lattice** | 394.7112 | **+11.691** | **2.12** | 34.6 % (0.9 sigma) |

Read as a 2-dof test on the CS sector, imposing the lattice costs
`D(chi2_data) = 11.69`, i.e. **p = 0.29 %, about 3 sigma**. So the disagreement is real but
it is *three* sigma, not the *fifteen* sigma that the raw `chi2_lat = 229.6` at the free
minimum suggests — most of that 229.6 is absorbed by the other 45 model parameters once
they are allowed to move. Quoting 229.6 as "the tension" would be wrong.

**The lattice constraint does adjudicate between the existing basins, and the answer is not
the one the free fit picked.** Evaluated at the four pre-existing tunes, the lattice term
excludes `plain` (15 sigma) and `walled` (10 sigma) outright, disfavours `ridge` (3.1
sigma) and is perfectly happy with `spectral` (0.9 sigma). The `{ridge, spectral}` cluster
— the one only the preconditioners found, and the one with the smallest
`sigma(alpha_s)` — is the lattice-compatible one. That is a genuine, if uncomfortable,
external handle on a choice that until now was made by the minimiser.

### Basin: it lands with `{plain, walled}`, NOT with `{ridge, spectral}`

L2 over the 46 model parameters, alphaS excluded:

| | plain | ridge | spectral | walled | lattice |
|---|---|---|---|---|---|
| plain | 0.000 | 4.190 | 4.062 | 1.343 | **2.524** |
| ridge | | 0.000 | 1.256 | 4.079 | **3.950** |
| spectral | | | 0.000 | 4.055 | **4.100** |
| walled | | | | 0.000 | **1.411** |

**1.411 from walled and 2.524 from plain, against 3.95 / 4.10 from ridge / spectral.** So
the lattice arm is in the `{plain, walled}` basin, even though its CS lambdas moved all the
way onto the lattice values that `{ridge, spectral}` also carry.

That is worth stating plainly: **the basin is not set by the NP sector.** What separates
the two clusters is the perturbative / PDF block — `resumScaleMuF` differs by **2.2**,
`resumTNP_b_qg` by **1.7-1.9**, `pdfEig23` by **1.15-1.25** between the lattice arm and
`ridge`/`spectral`, while the NP lambdas differ by far less. Against `plain` and `walled`
the top contributors are instead `lambda2_nu` (1.84, 1.21) and `lambda2` (0.88, 0.49) —
i.e. exactly the parameters the lattice prior moved, and nothing else. **A cold-started fit
with a lattice prior stays in the basin a cold start finds; it moves the CS kernel within
it.** So the lattice constraint and the preconditioner are answering different questions,
and combining them (warm-start a lattice fit from the spectral postfit) is the obvious next
measurement.

### THE KEY JUDGEMENT: are the NP uncertainties data-determined?

**Yes — qualitatively unlike the wall.**

| arm | postfit `sigma(theta)` on `(lambda2_nu, lambda4_nu)` | rho | reference | verdict |
|---|---|---|---|---|
| walled | **0.04696**, 0.00014 | -0.63 | wall's own width `1/sqrt(2 e^{2tau} w^2)` = **0.04764** | **railed**: sigma is 98.6 % of the barrier width |
| lattice | **0.12196**, 0.00028 | -0.94 | lattice prior 0.28334, 0.00909 | **interior**, mixed |

The lattice arm sits at an **interior** minimum — eigen pulls `(+1.06, -1.00)` against the
prior, i.e. ~1 sigma in each eigendirection, with no boundary anywhere near — so its
covariance is an ordinary posterior width rather than the curvature of a barrier.
Decomposing the posterior precision along the prior's own eigendirections:

| prior eigendirection | prior sigma | marginal posterior sigma | **variance reduction** |
|---|---|---|---|
| loose (~`lambda2_nu`, `[-1.00, +0.03]`) | 0.28346 | 0.12192 | **81.5 %** |
| stiff (~`lambda4_nu`, `[-0.03, -1.00]`) | 0.00374 | 0.00330 | **22.2 %** |

So the `lambda2_nu` magnitude is **data-determined**: the posterior is 81.5 % narrower in
variance than the prior along that direction, and the constraint tightens 2.3x below
lattice alone (physical
`sigma(lambda2_nu) = 0.0122` postfit against the prior's 0.0283). The `lambda4_nu`
direction is **prior-determined** — only 22 % variance reduction — which is honest and
expected — the data have
almost no handle on a `b^4` coefficient once `b^2` is pinned, which is precisely why
`rho = -0.91` exists in the lattice fit too.

Contrast the wall, where `lambda2_nu`'s sigma reproduces the analytic barrier width to
1.4 % and carries no information about the data at all.

**The caveat that undoes half of this.** "Data-determined" here means the *posterior* is
dominated by data along one direction. It does **not** make the result safe to quote,
because the prior's *centre* is doing the work that matters: it is what moved
`lambda2_nu` by +0.18 and what is being paid for at `D(chi2_data) = +11.7`. And a prior
whose own authors say its covariance is not ready cannot supply a defensible width. The
honest reading is: **a lattice prior gives uncertainties with the right statistical
character, on a constraint we have been told not to trust, while making the TMD sector
unphysical.** It is a better diagnostic than the wall and not yet a better measurement.

### Figures

* `np_form_factors_lattice.png` — both NP form factors at the anchor / free / walled /
  lattice-prior tunes, with the lattice `+-1 sigma` band (conditional 2x2, propagated
  through the tanh with the full correlation) drawn on the CS panels. The bottom panels are
  the finding: the blue TMD curve rises **above 1** before it decays.
* `cs_lambda_plane.png` — the `(lambda2_nu, lambda4_nu)` plane with the lattice 1/2/3 sigma
  ellipses and the four tunes on it. The free fit is off the top-left corner; the walled
  tune sits on the `lambda2_nu = 0` axis; the lattice arm is inside 1 sigma; the card
  anchor is on the ~2 sigma contour.

---

## Findings

1. **The mechanism is a rabbit external likelihood term written into a copy of the card**,
   not `prior_sigmas` (diagonal, cannot carry `rho = -0.91`) and not a `Regularizer`
   (scaled by the wall's shared `exp(2 tau)`). Ported unchanged from
   `studies/np-wall-local-minima/scripts/inject_lattice_cs_prior.py` —
   (evidence: `scripts/inject_lattice_cs_prior_theta.py`, `logs/inject_260910_215009.log`).
2. **The theta conversion is the affine push-forward `H_theta = W C^-1 W`,
   `g_theta = -W C^-1 (mu - anchor)`**, with `W = diag(0.10, 0.50)` from `params.REPARAM`
   and the anchor from the card's recorded correction. Verified before fitting: the map
   agrees with `np_damping_wall.physical_from_theta` to **0.000e+00** over 20 000 draws and
   the chi2 is invariant to **7.5e-15** — (evidence: `logs/inject_260910_215009.log`).
3. **The card's "Lattice" tag does not mean its central is the lattice central.**
   `LatticeNPLambda4Bugfix_FranksValsVars` has `lambda2_nu = 0.15`, `lambda4_nu = 0`,
   `lambda_inf_nu = 2` — **+1.90 / -1.12 / +0.62 sigma_lat**. The lattice-derived pieces it
   names are the *variation templates*, and **none of those 3673 card nuisances is an NP
   one**, so there is no double count from the card — (evidence:
   `logs/probe_260910_214542.log`).
4. **The existing arms are not "NP free":** `SCETlibADParamModel(priors=True)` puts a
   `sigma = 1` theta prior on all five reparametrised lambdas, i.e. physically
   `lambda2_nu = 0.15 +- 0.10`. Under the plain arm's tune that is already a **-2.08
   sigma** pull. Any lattice term must free those two, or it double-counts —
   (evidence: the prior declarations at line 28 of
   `logs/fit_DATALAT_260910_215144.log` — 44 params — and of
   `../260910-blinding/logs/fit_DATABLIND_260910_151034.log` — 46; the -2.08 is
   `(-0.058284 - 0.15)/0.10` on the tune table in `logs/compare_260910_221613.log`).
5. **The lattice prior does not make the NP function physical — it relocates the
   violation.** CS fixed (`lambda2_nu` -0.058 -> +0.126, inside the lattice 1 sigma,
   `p = 35 %`), TMD broken: `L2 < 0` at every rapidity, `f^NP` up to **1.29** out to
   `b_T = 1.6 GeV^-1`, inside the alpha_s-sensitive window. 3 of 8 conditions fail against
   1 of 8 walled — (evidence: `logs/compare_260910_221613.log`,
   `np_form_factors_lattice.png`).
6. **It converges better than every other arm**: EDM **9.83e-08** in 134 iterations /
   1209 s, 0 negative eigenvalues. The `scetlib_np` warning that the lattice term stalls
   `trust-krylov` does not carry over, because the unit-nuisance reparametrisation drops the
   term's condition number from 7.5e4 (physical 3x3) to **5731** (theta, conditional 2x2) —
   (evidence: same log; `studies/np-wall-local-minima/QUEUE.md`).
7. **The lattice term adjudicates between the known basins.** At the four existing tunes:
   `plain` 229.6 (15 sigma), `walled` 107.6 (10 sigma), `ridge` 12.3 (3.1 sigma),
   `spectral` **2.10 (0.9 sigma)**. The preconditioner basin is the lattice-compatible one —
   (evidence: `logs/compare_260910_221613.log`).
8. **But the basin is not set by the NP sector.** The lattice arm lands at L2 **1.41** from
   walled and **2.52** from plain, against **3.95 / 4.10** from ridge / spectral. What
   separates the clusters is `resumScaleMuF` (2.2), `resumTNP_b_qg` (1.7-1.9) and `pdfEig23`
   (1.15-1.25) — the perturbative/PDF block, not the lambdas — (evidence: same log).
9. **Under the lattice prior the NP uncertainties are interior and part-data**: eigen pulls
   `(+1.06, -1.00)`, and the marginal posterior is **81.5 %** narrower in variance than the
   prior along its loose eigendirection (22.2 % along the stiff one). "Variance reduction",
   not "share of the precision": the posterior 2x2 is marginal over the other 3718
   parameters, so precisions do not simply add. Under the wall, `sigma(theta_lambda2_nu) = 0.04696` is
   **98.6 % of the analytic barrier width 0.04764** — a rail, not a measurement —
   (evidence: same log).
10. **The saturated p-value of any externally-constrained arm must have the term removed.**
    The external NLL enters the fit NLL and so the saturated statistic: lattice
    **0.71 % -> 0.82 %**, walled 1.07 % -> 1.16 %. Same trap `np-wall-local-minima` recorded
    for its `latticeCS2` cards — (evidence: same log).

*Findings 1, 2, 3, 4, 5, 6 and 10 generalise beyond this task — they are facts about the
model, the card and the mechanism. Candidates for `knowledge/`.*

---

## Open questions

- **`knowledge/` says not to do this.** Section 10 of
  `np_parametrization_constraints.md` forbids the covariance as a prior and section 11
  prescribes "bracket, don't prior" (freeze the CS lambdas over a scan and take the alpha_s
  spread as a systematic). This task's result does **not** overturn that: it shows what the
  prior does, and finding 5 is an argument *for* the bracket prescription, since a prior on
  one sector alone is demonstrably reroutable. The orchestrator should decide whether the
  lattice arm is quotable at all.
- **THE OBVIOUS NEXT FIT: lattice prior + damping wall.** One 25-minute arm. The lattice
  term handles the CS side (where a wall only rails) and the wall handles the TMD side
  (where nothing external exists). If that arm keeps 8 of 8 conditions at a tolerable
  `D(chi2_data)`, it is the first configuration in this study that is both physical and
  measured. If it does not, the parametrisation itself is the problem. Deliberately not run
  here: one task, one question, and the single-arm rule.
- **Warm-start a lattice fit from the spectral postfit.** Finding 8 says the basin is chosen
  by the perturbative block, and finding 7 says the spectral basin is the lattice-compatible
  one. A lattice fit seeded there would say whether the two effects combine — and it is the
  configuration with both the smallest `sigma(alpha_s)` (0.000856) and the best lattice
  agreement.
- **Should `lambda_inf_nu` be held at 2.0 or at the lattice 1.6853?** Conditioning at 2.0 is
  self-consistent with the card, but 2.0 is a hand-chosen FranksVals number sitting +0.62
  sigma_lat away, and it sets the CS kernel's saturation cap exactly (`|gamma_nu| <=
  lambda_inf_nu`, section 12). The conditional means shift by +0.011 / -0.003 between the
  two choices; the injector takes `--condition-linf-nu` so this is one flag.
- **`--doImpacts` was not run**, so the NP-group impact on alpha_s under a lattice prior is
  unmeasured — the number that would say whether any of this moves the final uncertainty.
- **The TMD b.c. has no external constraint and now carries the whole excursion.** Section
  11's "fit our tanh_2 to published CS-kernel CURVES and read off the spread" has a TMD
  analogue (MAP22 replicas were used that way in `scetlib_np`); building it is the piece of
  work that would close this properly.
