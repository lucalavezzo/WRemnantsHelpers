---
title: Does the CS sector matter for alpha_s? Freeze the CS lambda and refit
slug: 260911-freeze-cs
study: scetlib-ad-param-model
status: done
created: 2026-09-11
updated: 2026-09-11
owner: study-worker
---

# Does the CS sector matter for alpha_s? Freeze the CS lambda and refit

**Task:** `knowledge/30_physics_global/np_parametrization_constraints.md` §11 item 3 asks
whether the wrong-sign Collins-Soper-kernel pull our blinded data fit shows is a
CS-kernel *statement* at all, or a near-degenerate reshuffle against the TMD b^4 term
(`rho(lambda4, lambda2_nu) = -0.996` is quoted there). The operational test: **freeze the
CS lambda at the theory correction's own values and refit. Does `alpha_s` move by much
less than `sigma(alpha_s)`?** If it does, the whole CS-bound question is moot for
`alpha_s`.

---

## START HERE (status as of 2026-09-11)

> ### NO -- freezing moves `alpha_s` by **1.03 sigma**, so the CS bound is NOT moot.
>
> Freezing the CS kernel (`lambda2_nu`, `lambda4_nu`; the rest of the CS sector is already
> held by `params.DEFAULT_FROZEN`) at the theory correction's own values and refitting moves
> `alpha_s` by `|d(alpha_s)|/sigma(alpha_s) = ` **1.03**, and at the lattice central by
> **0.66**. (Every ratio on this page divides by the PLAIN arm's `sigma = 0.001321`, the
> conservative choice since it is the larger of the two; against the frozen arm's own
> `sigma = 0.001151` the anchor shift is **1.19**.) §11 item 3's *mechanism* is confirmed -- the TMD block absorbs the CS move with
> slope -1.9, which is why a quadratic forecast overstates the shift by 24x and gets its
> sign wrong -- but the compensation is incomplete and what survives is of order one sigma.
>
> The response is **linear**, `d(alpha_s)/d(lambda2_nu) = +8.3e-03 GeV^-2` (max residual
> 0.025 sigma), so the
> frozen-scan NP-CS systematic is that slope times the adopted range: **+-2.7e-04**
> (lattice +-1 sigma, interpolated) to **+-8.0e-04** (lattice 3 sigma box, from the fitted
> points), against `sigma(alpha_s) = 0.00115` and the AN's total 0.00099.
>
> The chain is **reversible** (a backward step returns to the forward point at L2 = 0.001),
> so the spread is a systematic and not an artefact of the scan direction.
>
> **Read the two method caveats before quoting.** (1) Scan by CONTINUATION: a cold restart
> at each point crosses NP branches and gives a non-monotonic, up-to-`D(chi2)=19.9`-worse
> scan. (2) §11's quoted `rho(lambda4, lambda2_nu) = -0.996` is **+0.906** on this card --
> it came from a different (1D, `tanh_6_sigmoid`) fit.

- **Next action:** none -- task closed. The piece of work that converts this into a number for the AN is §11
  item 4: measure the credible `lambda2_nu` range from published CS-kernel functions and
  multiply by the slope.
- **Blocking on:** nothing.

**Figures.** `frozen_cs_scan.png` -- the answer: `d(alpha_s)/sigma`, the saturated
`2*dNLL`, and `sigma(alpha_s)` against the frozen `lambda2_nu`, for both the cold and the
single-branch scans, with the lattice band and the anchor marked.
`frozen_cs_basin.png` -- the L2 map that shows which arms changed branch.

**Fitresults** (ceph): `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260911_freeze_cs/fitresults_{DATAFRZCS,FRZCSL000,FRZCSL050,FRZCSL087,FRZCSL190,CFRZ150,CFRZ190,WFRZ*,BFRZ087}.hdf5`; warm/continuation seeds under `.../260911_freeze_cs/seeds/`.

---

## Log

### 2026-09-11 - reversibility: the chain has no hysteresis

Evidence: `logs/fit_BFRZ087_260911_005022.log`, `logs/analyse_260911_010711.log`,
`scripts/launch_backfrz.sh`.

A frozen scan is only a systematic if it is a single-valued family of the frozen parameter.
Stepping BACKWARD from the converged `cfrz@0.15` down to `lambda2_nu = 0.087` returns to
the forward point exactly:

| | forward `frzCS@0.087` | backward `bfrz@0.087` |
|---|---|---|
| saturated `2*dNLL` | 819.29 | **819.29** |
| `d(alpha_s)` vs plain | +8.663e-04 | **+8.667e-04** |
| `sigma(alpha_s)` | 0.001152 | **0.001152** |
| TMD `Lambda_2` | -0.03559 | **-0.03559** |
| **L2 over the 46 model params** | -- | **0.001** |

So the up-scan and the down-scan agree to 1e-3 in a space where the chain's own steps are
0.42-0.71 and the branch change is 2.07. **The scan is a path-independent one-parameter
family, and the spread quoted from it is a systematic rather than an artefact of the
direction it was walked.**

The two "warm from plain" arms that did converge make the same point from the other side:
`wfrz@0.19` reproduces the COLD `frzCS@0.19` minimum to **L2 = 0.001** (same `2*dNLL`
832.44, same `d(alpha_s)` -0.470 sigma), i.e. there really are two distinct minima at
`lambda2_nu = 0.19` and the continuation finds the better one (826.29 vs 832.44).
`wfrz@0.15` found a THIRD point (`2*dNLL` 833.67) and stopped at EDM 4.1e-04, badly
converged -- it is reported, not used.

### 2026-09-11 - the continuation scan: monotonic, linear, and the answer

Evidence: `logs/analyse_260911_004623.log`, `logs/fit_CFRZ{150,190}_*.log`,
`frozen_cs_scan.png`, `frozen_cs_basin.png`.

Stepping from the converged `frzCS@0.087` postfit (`scripts/launch_contfrz.sh`) instead of
restarting cold, the 0.15 and 0.19 points land in **much better** minima and the scan
becomes monotonic and linear:

| `lambda2_nu` | 0.00 | 0.05 | 0.087 | 0.15 | 0.19 |
|---|---|---|---|---|---|
| `d(alpha_s)/sigma_plain`, cold | +0.09 | +0.44 | +0.66 | **-0.80** | **-0.47** |
| `d(alpha_s)/sigma_plain`, **single branch** | +0.09 | +0.44 | +0.66 | **+1.03** | **+1.30** |
| `2*dNLL`, cold | 817.94 | 817.91 | 819.29 | **842.96** | **832.44** |
| `2*dNLL`, **single branch** | 817.94 | 817.91 | 819.29 | **823.06** | **826.29** |
| EDM, single branch | 4.3e-10 | 2.6e-09 | 7.6e-08 | **2.9e-16** | **3.4e-16** |

The continuation arms are better by `D(chi2) = 19.9` and 6.2 and converge in 19 and 22
iterations at EDM 3e-16 -- the best-converged fits in this campaign. `frozen_cs_basin.png`
shows why the cold ones were wrong: `frzCS@0.15` sits **1.88-2.55** from every other arm in
the 41 non-NP parameters, where the chain's own steps are 0.13-0.44.

**The tried-and-failed alternative, recorded so it is not retried.** The first attempt at a
basin-controlled scan seeded each point from the PLAIN arm's postfit with only the CS pair
moved (`scripts/launch_warmfrz.sh`, postfixes `WFRZ*`). That is not a warm start:
`lambda4_nu` has postfit `sigma(theta) = 0.024`, so setting it to its anchor while holding
the other 3718 parameters lands at a loss of **1e3 to 2e6** -- farther from any minimum
than the cold start's ~3425 -- and those arms then stall at 416-441, worse than both series
above (`WFRZ190` reproduces the cold `FRZCSL190` minimum to 8 digits, 416.2206). The seed
has to come from a fit that already has `lambda4_nu = 0`, which is what the continuation
does.

### 2026-09-11 - the COLD scan is complete, and it is not monotonic: the 0.15 and 0.19 arms changed basin

Evidence: `logs/analyse_260911_000800.log`, `logs/checkmin_260911_0002*.log`,
`logs/fit_{DATAFRZCS,FRZCSL000,FRZCSL050,FRZCSL087,FRZCSL190}_*.log`.
All five are `Exit status: 0`, scipy `status: 2`, and **genuine minima** -- 0 negative
covariance eigenvalues, Cholesky clean, on the FLOATING sub-block (the frozen rows are
exactly `cov[i,i] = 1`, off-diagonal 0, i.e. prefit, as predicted).

**Convergence FIRST.** Every frozen arm converges far better than the plain arm it is
compared to:

| | plain | frz@0.00 | frz@0.05 | frz@0.087 | **frz@0.15 (anchor)** | frz@0.19 |
|---|---|---|---|---|---|---|
| EDM | 1.386e-03 | **4.31e-10** | 2.64e-09 | 7.60e-08 | **8.24e-09** | 6.26e-07 |
| iterations / nhev | 221 / 766 | 64 / 339 | 57 / 291 | 63 / 318 | 178 / 741 | 169 / 664 |
| wall clock | 1:04:19 | 19:30 | 19:03 | 20:42 | **32:59** (`--doImpacts`) | 31:13 |
| **kappa(cov)** | **2.98e+09** | **1.03e+05** | 1.08e+05 | 1.12e+05 | -- | -- |
| saturated `2*dNLL` | 811.12 | 817.94 | 817.91 | 819.29 | **842.96** | 832.44 |
| p [%], ndf corrected to 735 | 2.33 (733) | 1.77 | 1.77 | 1.63 | **0.34** | 0.71 |
| `sigma(alpha_s)` | 0.001321 | 0.001144 | 0.001154 | 0.001152 | **0.001088** | 0.001004 |
| **d(alpha_s) = frozen - plain** | -- | +1.15e-04 | +5.86e-04 | +8.66e-04 | **-1.06e-03** | -6.20e-04 |
| **in sigma(alpha_s)_plain** | -- | **+0.087** | **+0.444** | **+0.656** | **-0.802** | **-0.470** |

**The condition number is the cleanest by-product.** Freezing the two CS lambdas takes
`kappa(cov)` from **2.98e+09 to 1.0e+05**, four orders of magnitude. The pathological
anisotropy of the data basin -- the thing `../260910-spectral-precond` built a
preconditioner for -- **is the CS-versus-TMD degenerate direction**, and removing it
removes the illness.

**But the scan is NOT monotonic, and the reason is a basin change.** The three lower
points move `alpha_s` UP, monotonically; 0.15 and 0.19 move it DOWN. The L2 map says why:
`frzCS@0.15` sits **2.07-2.86** from every other arm, of which **1.96-2.55 is in the 41
non-NP parameters**, while the {0.00, 0.05, 0.087} family is 0.13-0.44 apart in that same
block. The NP tune says the same thing in physics: the TMD `lambda4` is 0.10-0.13 in the
three lower arms and **0.0002 / 0.015** at 0.15 / 0.19. So the cold scan crosses a TMD
branch boundary between 0.087 and 0.15, and -- this study having already measured
`alpha_s` to be basin-dependent at the 3.5 sigma level (`../260910-basins`) -- the cold
0.15 point's `+0.80 sigma` is **not a clean CS response**. Quoted as it stands, the cold
spread would be **1.93e-03 = 1.46 sigma** over [0, 0.19] and 1.25 sigma over [0.05, 0.15],
with an unknown fraction of that being the branch change.

**The reshuffle mechanism, explicitly.** Over the three same-branch points the TMD
small-`b` coefficient tracks the frozen CS one with slope
`d(lambda2)/d(lambda2_nu) = -1.8`: `lambda2` = 0.123 / 0.034 / -0.036 at
`lambda2_nu` = 0.00 / 0.05 / 0.087. That is §11 item 3's "reshuffle against the TMD term",
seen directly rather than inferred from a correlation -- and it carries the same cost the
lattice arm found: by `lambda2_nu = 0.087` the TMD `L2` has gone negative and the TMD
small-`b` damping condition fails at both rapidities. **Constraining the CS kernel does not
make the NP function physical; it moves the violation into the TMD boundary condition.**

### 2026-09-11 - so the scan is being repeated basin-controlled (warm)

`scripts/launch_warmfrz.sh` + `scripts/make_seed.py`: the same five frozen points, each
started from the **plain arm's own postfit** with only `lambda2_nu` and `lambda4_nu` moved
to the target. That is the literal form of §11 item 3 -- *stand at the plain minimum, fix
the CS kernel, reminimise* -- and it cannot change basin by accident. Seeds (flat
`x`/`parms` hdf5, the layout `fitter.load_fitresult` accepts) on ceph at
`260911_freeze_cs/seeds/`.

### 2026-09-11 - first frozen arm home, and the Gaussian forecast is wrong by 24x

`FRZCSL000` -- CS frozen at `lambda2_nu = 0`, `lambda4_nu = 0` -- finished in 19:30
(64 iterations, 339 hvp, scipy `status: 2`, 193.6 GiB peak, `Exit status: 0`).
Evidence: `logs/fit_FRZCSL000_260910_233317.log`, `logs/analyse_260910_235838.log`.

| | plain | **frzCS@0.00** |
|---|---|---|
| EDM | 1.386e-03 | **4.311e-10** |
| saturated `2*dNLL` | 811.12 | **817.94** |
| `sigma(alpha_s)` | 0.001321 | **0.001144** |
| **`d(alpha_s)` = frozen - plain** | -- | **+1.15e-04 = +0.087 sigma_plain** |
| predicted by the Gaussian forecast | -- | -0.00273 = **-2.06 sigma** |

**The forecast is wrong in sign and by a factor 24 in size.** So the reshuffle is real and it is far MORE
complete than the quadratic model around the plain minimum can represent: the refit finds
a place where the CS sector can be moved by 2.1 prior-sigma with `alpha_s` essentially
unchanged. It does that by moving the TMD block -- `lambda2` 0.301 -> 0.123 and `lambda4`
-0.003 -> **+0.126** -- which is exactly §11 item 3's hypothesis, confirmed by
construction rather than by correlation.

### 2026-09-11 - pre-flight probe: what is frozen, what is priored, and where the anchors are

Evidence: `logs/probe_260910_232542.log`, `scripts/probe.py`.

**The CS sector's entire floating content on this card is `lambda2_nu` and `lambda4_nu`.**
The SCETlib runcard's CS form is `tanh_2` -- the cache registers 53 parameters and
`lambda6_nu` is **not among them**, so there is no CS b^6 term to freeze. Of the remaining
CS names, `lambda_inf_nu` and `b0_over_bmax_nu` **are** already held by
`params.DEFAULT_FROZEN` (which is `lambda_inf, lambda_inf_nu, b0_over_bmax_nu,
resumTNP_b_qqDS, resumTransition1, resumTransition3`). So freezing `lambda2_nu` and
`lambda4_nu` freezes the CS kernel completely.

**The arms are NOT "NP free", confirming the brief's correction.** The model declares
Gaussian priors on **46 of 47** parameters; only `alphaS` is free. Every prior is
`sigma = 1` in THETA, and the physical width lives in `params.REPARAM`
(`physical = anchor + width * theta`), so in physical units the NP priors are

| parameter | anchor (= prior mean) | width (= physical 1 sigma) |
|---|---|---|
| `lambda2` (TMD `Lambda_2`) | 0.40 GeV^2 | 0.50 |
| `lambda4` (TMD `Lambda_4`) | 0.40 GeV^4 | 0.50 |
| `delta_lambda2` (TMD `Delta Lambda_2`) | 0.00 GeV^2 | 0.50 |
| **`lambda2_nu` (CS `lambda_2`)** | **0.15 GeV^2** | **0.10** |
| **`lambda4_nu` (CS `lambda_4`)** | **0.00 GeV^4** | **0.50** |
| `lambda_inf_nu` (CS `lambda_inf`) | 2.0 (held) | -- |

**The anchor is not the AN's NP tune, and this matters for how the scan is read.** The
card's correction is `scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_...`, i.e.
"Frank's values". `AN-25-085/theory.tex` eq. `nplunc` gives the CS centrals as the LATTICE
fit of Cridge et al.: `lambda_inf = 1.6853 +- 0.5069`, `lambda_2 = 0.0870 +- 0.0332 GeV^2`,
`lambda_4 = 0.0074 +- 0.0066 GeV^4`; the TMD b.c. centrals as `Lambda_2 = 0.25`,
`Delta Lambda_2 = 0.125`, `Lambda_4 = 0.06`, `Lambda_inf = 1`. **Our anchor differs from
both**: CS `lambda_2 = 0.15` is 1.7x the lattice central (+1.9 sigma_lat), CS `lambda_inf`
is 2 rather than 1.6853, and the TMD block sits at (0.4, 0.4, 0) rather than
(0.25, 0.06, 0.125). So "freeze at the theory correction's own values" is NOT the same as
"freeze at the lattice central", and the scan below deliberately spans both.

### 2026-09-11 - what the plain arm's covariance PREDICTS, before any refit

Evidence: `logs/gauss_260910_234152.log`, `scripts/gaussian_predict.py`. If the likelihood
were quadratic about the plain minimum, fixing a subset `f` and reminimising gives the
conditional mean `theta_r* = theta_r + Sigma_rf Sigma_ff^-1 (theta_f^0 - theta_f)` and the
conditional covariance. That is a free, exact-in-the-Gaussian-limit forecast of the freeze,
and comparing it to the refit measures how much of the answer is degeneracy geometry and
how much is genuine nonlinearity in SCETlib's response.

Plain arm postfit CS pair, in theta and physical:

| | theta | sigma(theta) | physical | anchor | lattice (AN eq. nplunc) |
|---|---|---|---|---|---|
| `lambda2_nu` | **-2.083** | 0.771 | **-0.0583 GeV^2** | +0.15 | 0.0870 +- 0.0332 |
| `lambda4_nu` | **+0.107** | **0.0244** | **+0.0537 GeV^4** | 0.00 | 0.0074 +- 0.0066 |

`lambda4_nu` is the **stiff** direction -- `sigma(theta) = 0.024`, i.e. physical
+-0.012 GeV^4 -- and the conditional slope is correspondingly violent:

    d(theta_alphaS)/d(theta_lambda2_nu) = +0.70    -> d(alpha_s)/d(lambda2_nu) = +0.0140 /GeV^2
    d(theta_alphaS)/d(theta_lambda4_nu) = +16.50   -> d(alpha_s)/d(lambda4_nu) = +0.0660 /GeV^4

**The predicted freeze-at-anchor shift is a near-cancellation of two large pulls.** Moving
`lambda2_nu` alone from -0.058 to the anchor +0.15 predicts **+2.21 sigma**; moving
`lambda4_nu` alone from +0.054 to the anchor 0 predicts **-2.68 sigma**; together
**-0.47 sigma**. That IS §11's "near-degenerate reshuffle", quantified -- but it makes the
small net shift an *accident of where the anchor sits*, not evidence that the CS sector is
irrelevant.

Predicted shift along the scan (both CS parameters frozen; `lambda4_nu` always at 0):

| frozen `lambda2_nu` | 0.00 | 0.05 | 0.087 | 0.15 (anchor) | 0.19 |
|---|---|---|---|---|---|
| predicted d(alpha_s) | -0.00273 | -0.00203 | -0.00151 | -0.00062 | -0.00006 |
| in sigma(alpha_s)_plain | **-2.06** | **-1.53** | **-1.14** | **-0.47** | **-0.05** |

and `sigma(alpha_s)` is predicted to collapse from 0.001321 to **0.001000** (-24 %) --
consistent with the 65 % `scetlibNPgammaNu` impact.

So the Gaussian forecast already says the answer is *not* "much less than sigma" once the
frozen value is scanned: the predicted spread over [0.05, 0.15] is ~1.1 sigma and over
[0, 0.19] is ~2.0 sigma. The refits below are the measurement; these extrapolations run
over 2 sigma of displacement in a likelihood this study has shown to be multimodal, so
they are a forecast, not a result.

### 2026-09-11 - the plain arm's OWN impacts already answer part of the question

Evidence: `logs/impacts_260910_233717.log`, `scripts/read_impacts.py`. This needs no
refit: the model registers an impact group `scetlibNPgammaNu` that is **exactly the CS
sector** (`lambda2_nu`, `lambda4_nu` + the held `lambda_inf_nu`, `b0_over_bmax_nu`), and
`scetlibNPFeff` which is the TMD boundary condition. Read off `DATABLIND`
(`sigma(alpha_s) = 0.001321`):

| group on `alphaS` | impact (alpha_s units) | as a fraction of sigma |
|---|---|---|
| `stat` | 0.001044 | 79.0 % |
| `resumNonpert` (CS + TMD) | 0.001009 | 76.4 % |
| `pdfEig` | 0.000953 | 72.2 % |
| **`scetlibNPgammaNu` (CS kernel)** | **0.000862** | **65.3 %** |
| `scetlibNPFeff` (TMD b.c.) | 0.000707 | 53.5 % |
| `resumTNP` | 0.000558 | 42.3 % |
| `resumScale` | 0.000279 | 21.1 % |

and per parameter, `lambda4` (0.000597, 45.2 %) and **`lambda2_nu` (0.000584, 44.3 %)**
are the two largest single contributions to `sigma(alpha_s)` after `alphaS` itself --
larger than any PDF eigenvector (the largest is `pdfEig25` at 32.3 %).

So the CS sector is **not** a spectator in the uncertainty budget: it carries 65 % of
`sigma(alpha_s)` in quadrature. That is a statement about the WIDTH, not about the
central value, and §11 item 3 asks about the central value -- but it already predicts the
freeze will tighten `sigma(alpha_s)` substantially.

### 2026-09-11 - the correlations quoted in the note do NOT reproduce here

`np_parametrization_constraints.md` §11 item 3 says *"our own fit has
rho(lambda4, lambda2_nu) = -0.996, rho(lambda4, lambda4_nu) = -0.953"*. Read off the
**plain `DATABLIND` postfit covariance** on this card (`scripts/probe.py` §4):

| pair | §11 quotes | **`DATABLIND`, measured** |
|---|---|---|
| rho(`lambda4`, `lambda2_nu`) | **-0.996** | **+0.906** |
| rho(`lambda4`, `lambda4_nu`) | **-0.953** | **-0.423** |
| rho(`lambda2`, `lambda4`) | -- | -0.948 |
| rho(`lambda2`, `lambda2_nu`) | -- | -0.927 |
| rho(`lambda2_nu`, `lambda4_nu`) | -- | -0.617 |
| rho(`alphaS`, `lambda2_nu`) | -- | +0.443 |
| rho(`alphaS`, `lambda4`) | -- | +0.452 |

The §11 numbers are **not from this fit**. Tracing them: they come from
`studies/np-wall-local-minima/LOGBOOK.md` line 2743, a **1D ptll** fit of the OLD
`scetlib_np` model in the `tanh_6_sigmoid` form with a `bT_cutoff` -- a configuration whose
own entry records that the cutoff *"collapses lambda4's curvature ~200x: sigma(lambda4)
0.605 -> 8.654"*, which is precisely what manufactured the -0.996. They should not be
carried into the 2D `scetlib_ad` fit, and §11's premise has to be restated with the
measured numbers.

**What survives is the qualitative claim.** The TMD and CS blocks ARE strongly entangled
here: |rho| = 0.91 between `lambda4` and `lambda2_nu`, 0.95 between `lambda2` and
`lambda4`, 0.93 between `lambda2` and `lambda2_nu`. What does NOT survive is the
suggestion that `alphaS` is insulated from it: rho(`alphaS`, `lambda2_nu`) = +0.44 and
rho(`alphaS`, `lambda4`) = +0.45 are not small, so freezing is not obviously free.

### 2026-09-11 - setup

Harness copied from `../260910-blinding/scripts/` (`run.sh` with `D=` repointed here,
`incontainer.sh` byte-identical, md5 `f6f87d5222a4d7d0342e3a940ea8f81e` -- it pins the
fit-770 `scetlib_tf.py` and asserts the imported `rabbit.fitter` carries the additive
blinding change). Assertion passed on every launch.

**`--freezeParameters`, not the model's `fit_params`** -- `scripts/launch_frzcs.sh` carries
the full argument. In short: `--freezeParameters` keeps the registered vector identical to
the plain arm (47 params, same POI/POU split, same order, same priors, same impact groups,
same SCETlib rule set), so the only difference is two `tf.stop_gradient`s and the postfit
vector stays index-aligned with the five arms in `../260910-basins/basins.json`.
`fit_params` would drop them from rabbit's vector (npou 46 -> 44), changing the Hessian
dimension and the impact groups for no physics gain. Frozen parameters are handled
correctly downstream (`fitter.edmval_cov` inverts only the floating submatrix;
`_resolved_param_impact_groups` drops frozen indices). **One caveat that comes with the
choice:** `self.cov` is initialised to `diag(var_prefit)` and only the floating block is
overwritten, so a frozen parameter's reported sigma in the fitresult is its PREFIT width
(1.0 in theta), not a measurement -- never quote it.

Freeze registered, verified in the log:
`DEBUG:fitter.py: Updated list of frozen params: [b'lambda2_nu', b'lambda4_nu']`.

---

## Result

### Comparability, stated before any number

1. **Blinded real data (`-t 0`), `alphaS` blinded ADDITIVELY.** No central value appears
   here or in any log or JSON in this directory. `sigma`, EDM, losses, p-values and
   **differences between arms in units of sigma** are safe -- the last only because the
   offset is the same deterministic `sha256(param_name)` draw on the same card in every
   arm, so the difference is offset-free. Sign convention throughout:
   **`d(alpha_s) = frozen - plain`.**
2. **Every frozen arm is a one-variable change against the plain `DATABLIND` arm.** Same
   card `study_scratch/260910-anchor-verify/card_none.hdf5` (2D `ptll x yll`, 780 bins,
   3673 card nuisances + 47 model parameters), same cache
   `scetlib_ad_caches/pdf62_corrgrid_260827/merged_full`, same SCETlib `b66f8de`
   (`libscet-qT.so` md5 `71b5e68a0cfed89326ff4ed521d37300`), same model file
   `260908-fit-770/lib/scetlib_tf.py` md5 `e60ed930...`, same fitter
   (`rabbit.fitter` from the `blinding-additive` worktree at `0f64bbb`, asserted at every
   launch), `-v 4 --jitCompile off --noBinByBinStat --earlyStopping 100`, `threads=128`,
   `--snapshotFile`. The only difference is `--freezeParameters lambda2_nu lambda4_nu`
   (plus, per scan point, `xparam_default=lambda2_nu=<theta>`).
3. **The arms are NOT "NP free".** 46 of 47 model parameters carry `sigma = 1` THETA
   priors; only `alphaS` floats free. In physical units that is `lambda2_nu = 0.15 +- 0.10`
   and `lambda4_nu = 0.00 +- 0.50`, so "freezing" is the `sigma -> 0` limit of a prior
   that was already there, not the removal of an unconstrained direction.
4. **`ndfsat` does not know about `--freezeParameters`.** `rabbit_fit.py:705` computes
   `nobs - param_model.nparams - nsystnoconstraint` over ALL model parameters, so every
   frozen arm is reported at 733 d.o.f. when it has 735. Both are given below; the
   `2*dNLL` itself is the statistic used to rank arms (`../260910-basins` finding 8: the
   postfit "Linear chi2" is selected by `--noPostfitProfileBB` and cannot rank arms).
5. **A frozen parameter's reported `sigma` is its PREFIT width, not a measurement.**
   `self.cov` is initialised to `diag(var_prefit)` and only the floating block is written
   back, verified: `cov[i,i] = 1` exactly, max off-diagonal 0, in every frozen arm.
6. **`--doImpacts` only on the anchor arm.** The others skipped it (~20 min each). In a
   frozen arm the `scetlibNPgammaNu` impact group resolves to nothing and disappears from
   the output by construction, which is correct rather than a bug.
7. **The anchor is not the AN's NP tune.** Our correction's CS centrals are
   `lambda2_nu = 0.15`, `lambda4_nu = 0`, `lambda_inf_nu = 2` (read straight off
   `cache.conf`, `np_model_nu = tanh_2`); `AN-25-085` eq. `nplunc` uses the lattice values
   `0.0870 +- 0.0332`, `0.0074 +- 0.0066`, `1.6853 +- 0.5069`. Freezing "at the theory
   correction's own values" therefore sits at **+1.9 sigma_lat** in `lambda_2`.

### The answer

**No. Freezing the CS kernel at the theory correction's own values moves `alpha_s` by
`|d(alpha_s)| / sigma(alpha_s) = 1.03`, not by much less than sigma. The bound question is
NOT moot.** (Ratios throughout divide by the PLAIN arm's `sigma = 0.001321` -- the larger
of the two and so the conservative denominator; against the frozen arm's own
`sigma = 0.001151` the same shift is **1.19**.) §11 item 3's *mechanism* is real and is confirmed -- most of the CS move is
absorbed by the TMD block -- but the compensation is incomplete, and what survives is of
order one sigma.

**The scan, on a single branch** (the three lower points are the cold fits; 0.15 and 0.19
are continuation steps from the converged `frzCS@0.087`, which find better minima than the
cold fits at those values -- see below). `lambda4_nu` is frozen at 0 (its anchor)
throughout; the sign convention is `d(alpha_s) = frozen - plain`:

| frozen `lambda2_nu` [GeV^2] | 0.00 | 0.05 | **0.087 (lattice)** | **0.15 (anchor)** | 0.19 |
|---|---|---|---|---|---|
| `d(alpha_s)` | +1.15e-04 | +5.86e-04 | **+8.66e-04** | **+1.364e-03** | +1.711e-03 |
| **in `sigma(alpha_s)_plain`** | **+0.09** | **+0.44** | **+0.66** | **+1.03** | **+1.30** |
| `sigma(alpha_s)` | 0.001144 | 0.001154 | 0.001152 | 0.001151 | 0.001155 |
| saturated `2*dNLL` (plain: 811.12) | 817.94 | 817.91 | 819.29 | 823.06 | 826.29 |
| p [%], ndf corrected to 735 | 1.77 | 1.77 | 1.63 | 1.29 | 1.06 |
| EDM | 4.3e-10 | 2.6e-09 | 7.6e-08 | **2.9e-16** | **3.4e-16** |
| TMD `Lambda_2` (free) | +0.123 | +0.035 | -0.036 | -0.159 | -0.237 |
| damping conditions violated | 1/8 | 1/8 | 2/8 | 2/8 | 2/8 |

**The response is linear**: a least-squares line through all five points gives
`d(alpha_s)/d(lambda2_nu) = +8.3e-03 GeV^-2` with a maximum residual of **3.3e-05 in
`alpha_s`, i.e. 0.025 sigma** -- so a straight line describes the whole scan to well inside
a tenth of a sigma. Consequently the
candidate **NP-CS systematic** from a frozen scan is simply that slope times whatever
credible range is adopted:

| range for `lambda2_nu` | where it comes from | half-spread in `alpha_s` | in sigma |
|---|---|---|---|
| [0.054, 0.120] | lattice **+-1 sigma**, `AN-25-085` eq. `nplunc` | **+-2.7e-04** * | **+-0.21** |
| [0.05, 0.15] | §11 item 4's *expected* (explicitly unmeasured) range | +-3.9e-04 | +-0.30 |
| [0, 0.19] | lattice marginal **3 sigma** box, §10 | +-8.0e-04 | +-0.60 |

The second and third rows are **half-differences of fitted points** (0.05 and 0.15; 0 and
0.19). The first, marked `*`, is the only one that is interpolated -- no fit was run at
0.054 or 0.120, so it is the measured slope times the half-range.

For scale: `sigma(alpha_s)` is 0.00115 in these arms and `AN-25-085` quotes a total
uncertainty of 0.00099 (Asimov, 4D). A **+-2.7e-04 to +-8.0e-04** NP-CS systematic is
therefore between a quarter and four fifths of the entire uncertainty budget. It is not a
footnote.

**Two things are true at once, and both matter.**

*The reshuffle is real, and the naive estimate of it is badly wrong.* The quadratic
(conditional-mean) forecast built at the plain minimum predicted **-2.06 sigma** for the
freeze at `lambda2_nu = 0`; the refit gives **+0.09 sigma** -- wrong in sign and 24x too
large. The reason is visible in the tune: the TMD small-`b` coefficient follows the frozen
CS one with slope **`d(Lambda_2)/d(lambda2_nu) = -1.9`**, all the way across the scan, and
a Hessian at one point cannot know that. §11's hypothesis that the wrong-sign CS pull is
"a near-degenerate reshuffle against the TMD term, not a CS-kernel statement" is
**confirmed as a mechanism**.

*The reshuffle is not complete.* `gamma_nu^NP` enters the `b_T` integrand multiplied by
`C_nu` and `f^NP` does not, so the two cannot cancel exactly, and the residue grows
linearly with the displacement: 0.09 sigma at `lambda2_nu = 0`, 0.66 at the lattice
central, **1.03 at the anchor**.

**The freeze is not free in goodness of fit.** The saturated `2*dNLL` goes 811.1 (plain,
CS free) -> 817.9 at `lambda2_nu = 0` -> **823.1 at the anchor**, i.e. `D(chi2) = +6.8` to
**+12.0**. The data prefer no CS NP damping at all, and dislike the correction's own CS
kernel most of the scan -- the same direction of tension `../260910-wall-port`,
`../260911-lattice-constraints` and §10 already record.

**And it relocates the unphysicality rather than removing it.** With the CS pair frozen
the CS damping conditions hold by construction, but the TMD small-`b` condition
`Lambda_2 + DLambda_2 y^2 >= 0` then fails -- at `|Y| = 2.5` from `lambda2_nu = 0.05`, at
both rapidities from 0.087, and by `Lambda_2 = -0.237` at 0.19. This is the same failure
`../260911-lattice-constraints` found with a lattice prior (`Lambda_2 = -0.138`).
**Constraining only the CS side of the NP model does not make the NP function physical; it
moves the violation into the sector that has no external constraint.**

### Why the cold scan had to be redone, and what that says on its own

The five COLD arms are all genuine minima (0 negative covariance eigenvalues on the
floating block, Cholesky clean) and all converge well, but the scan they trace is **not
monotonic**: `+0.09 / +0.44 / +0.66 / -0.80 / -0.47 sigma`. The 0.15 and 0.19 cold arms
changed branch -- `frzCS@0.15` sits 1.88-2.55 away in the 41 non-NP parameters from every
other arm (the chain's own steps are 0.13-0.44), and its TMD `lambda4` collapses to 0.0002
where the chain holds 0.09-0.13. They are also **worse** minima: `2*dNLL` 842.96 and
832.44 against the continuation's 823.06 and 826.29, i.e. up to `D(chi2) = 19.9` worse.

The continuation arms found those better minima in **19 and 22 iterations** with
**EDM 3e-16** -- the best-converged fits anywhere in this campaign. So the lesson is
general and cheap: **scan a frozen parameter by continuation, not by restarting cold at
each point.** A cold restart at each point of a multimodal likelihood samples branches, and
the resulting "systematic" is then a mixture of the parameter's effect and the optimizer's
path -- which is precisely the failure `../260910-basins` documented at the 3.5 sigma level.

**The chain is reversible, so the spread is a systematic and not a path.** Stepping
BACKWARD from `cfrz@0.15` to `lambda2_nu = 0.087` returns to the forward `frzCS@0.087`
point at **L2 = 0.001** over the 46 model parameters, with `2*dNLL` 819.29 and
`d(alpha_s)` +8.667e-04 against the forward 819.29 and +8.663e-04 -- in a space where the
chain's own steps are 0.42-0.71 and the branch change is 2.07.

**A seeding strategy that does NOT work, recorded so it is not retried.** The obvious
alternative -- seed each frozen point from the *plain* arm's postfit with only the CS pair
moved -- is not a warm start at all. `lambda4_nu` has postfit `sigma(theta) = 0.024`, so
setting it to its anchor while holding the other 3718 parameters lands at a loss of
**1e3 to 2e6**, farther from any minimum than the cold start's ~3425, and those arms then
stall in worse minima than either series above. Two of them did converge and are
informative anyway: `wfrz@0.19` reproduces the COLD `frzCS@0.19` minimum to L2 = 0.001
(same `2*dNLL` 832.44, same `d(alpha_s)` -0.470 sigma), confirming there really are two
distinct minima at `lambda2_nu = 0.19`; `wfrz@0.15` found a third (`2*dNLL` 833.67) and
stopped at EDM 4.1e-04, badly converged. The seed has to come from a fit that already has
`lambda4_nu = 0`.

### One clean by-product: the CS-vs-TMD direction IS the ill-conditioning

`kappa(cov)` over all 3720 parameters: **2.98e+09** in the plain arm, **1.03-1.12e+05** in
the frozen arms -- four orders of magnitude, from freezing two parameters. The degenerate
direction that motivated `../260910-spectral-precond`'s preconditioner, and that makes the
data basin "pathologically anisotropic in a way the Asimov one is not", **is the
CS-versus-TMD near-degeneracy**. Freezing it also buys the best convergence in the
campaign: EDM 3e-16 against the plain arm's 1.4e-03.

### Physics read, against AN-25-085

The CS kernel `gamma_nu^NP` is the one NP object in this model with an external
determination: `AN-25-085/theory.tex` §`sec:npmodel` calls it "flavor-universal" and
lattice-computable, and eq. `nplunc` carries the Cridge et al. lattice fit with its full
3x3 covariance, used as the analysis' **nominal** centrals plus three eigenvariations. The
TMD boundary condition `f^NP` is explicitly the opposite: its parameters "do not have
robust external constraints, therefore we use generous prefit variations and largely
determine their values in the fit to the data".

That asymmetry is exactly what this measurement exposes. The fit answers a
constrained-sector move by moving the **unconstrained** sector 1.9x as far in the same
small-`b` region, and pays for it by pushing the TMD boundary condition outside its own
physical region. So the 0.2-0.6 sigma NP-CS systematic above is not cleanly "the theory
uncertainty on the CS kernel": it is what is left after the TMD sector has absorbed as
much as its (absent) constraints allow. Tightening the TMD side would make the CS
systematic **larger**, not smaller.

Two numbers make the external tension concrete, and they are worse than §10 records. Our
free fit's `lambda2_nu = -0.058` is **-4.4 sigma_lat** from the lattice central
(0.0870 +- 0.0332), and its `lambda4_nu = +0.054 +- 0.012` is **+7.0 sigma_lat**
(0.0074 +- 0.0066) -- §10 quotes -2.5 / +4.0 sigma_lat from the older `scetlib_np` walled
fits. And the anchor the correction was built at, `lambda2_nu = 0.15`, is itself
**+1.9 sigma_lat**: the frozen point the brief calls "the theory correction's own values"
is not the lattice central, and the two differ by 0.37 sigma in `alpha_s`.

---

## Findings

1. **The answer to §11 item 3 is NO.** Freezing the CS kernel at the theory correction's
   own values moves `alpha_s` by **+1.03 sigma**, and at the lattice central by
   **+0.66 sigma**. It is not "much less than sigma", so the CS-bound question is not moot
   -- (evidence: `logs/analyse_260911_004623.log`, `frozen_cs_scan.png`).
2. **The reshuffle §11 hypothesised is real, and it is what makes the shift SMALL rather
   than zero.** The TMD small-`b` coefficient follows the frozen CS one with slope
   `d(Lambda_2)/d(lambda2_nu) = -1.9`; the quadratic forecast built at the plain minimum,
   which cannot see that, predicts -2.06 sigma where the refit gives +0.09 sigma -- wrong
   in sign and 24x in size -- (evidence: `logs/gauss_260910_234152.log` vs
   `logs/analyse_260911_004623.log`).
3. **The CS response is LINEAR**: `d(alpha_s)/d(lambda2_nu) = +8.3e-03 GeV^-2` over
   [0, 0.19], max residual 3.3e-05 in `alpha_s` (0.025 sigma). A frozen-value NP-CS systematic is therefore
   just that slope times the adopted range: **+-2.7e-04 (lattice +-1 sigma, interpolated)**,
   +-3.9e-04 (§11's expected [0.05, 0.15], from the fitted points), +-8.0e-04 (lattice
   3 sigma box, from the fitted points) -- (evidence: same).
4. **§11's quoted correlations do not hold on this card.** `rho(lambda4, lambda2_nu)` is
   **+0.906**, not -0.996, and `rho(lambda4, lambda4_nu)` is **-0.423**, not -0.953. The
   quoted pair comes from a 1D-ptll `tanh_6_sigmoid`-with-`bT_cutoff` fit of the OLD
   `scetlib_np` model, a configuration whose own record says the cutoff collapsed
   `sigma(lambda4)` by 200x -- (evidence: `logs/probe_260910_232542.log`;
   `studies/np-wall-local-minima/LOGBOOK.md:2743`).
5. **Freezing the two CS lambdas takes `kappa(cov)` from 2.98e+09 to 1.0e+05.** The
   degenerate direction behind the preconditioner work and the "pathologically
   anisotropic" data basin IS the CS-versus-TMD near-degeneracy -- (evidence:
   `logs/checkmin_260911_0002*.log`).
6. **Scan a frozen parameter by CONTINUATION, not by restarting cold.** The cold scan is
   non-monotonic because its 0.15 and 0.19 arms changed branch and landed in minima up to
   `D(chi2) = 19.9` worse; stepping from the converged neighbour found those better minima
   in 19-22 iterations at **EDM 3e-16**. This generalises beyond this task -- (evidence:
   `logs/fit_{DATAFRZCS,FRZCSL190,CFRZ150,CFRZ190}_*.log`, `frozen_cs_basin.png`).
7. **A "warm start" from the plain postfit is not warm.** `lambda4_nu` has postfit
   `sigma(theta) = 0.024`, so moving it to its anchor while holding the rest of the plain
   vector starts at loss 1e3-2e6 -- worse than a cold start -- and those arms stall in
   worse minima. Seed from a fit that already has `lambda4_nu = 0` --
   (evidence: `logs/fit_WFRZ*_*.log`).
8. **Constraining only the CS side does not make the NP function physical.** With the CS
   pair frozen, the TMD small-`b` condition fails instead, from `lambda2_nu = 0.05` upward,
   reaching `Lambda_2 = -0.237` at 0.19 -- the same relocation
   `../260911-lattice-constraints` found with a lattice prior -- (evidence:
   `logs/analyse_260911_004623.log`, damping-conditions block).
9. **`rabbit`'s `ndfsat` ignores `--freezeParameters`** (`rabbit_fit.py:705` subtracts
   `param_model.nparams`, frozen entries included), so every frozen arm is reported at 733
   d.o.f. when it has 735. Already known from `studies/np-wall-local-minima`; still
   unfixed -- (evidence: `logs/analyse_260911_004623.log`, "ndf as logged" vs "corrected").

*Findings 5, 6, 7 and 9 are facts about this likelihood and about rabbit rather than about
this task; 6 and 7 in particular belong in `knowledge/` -- they will bite any frozen scan.*

---

## Open questions

- **The frozen range is still asserted, not measured.** §11 item 4's actual piece of work
  -- fitting our `tanh_2` form to the published CS-kernel FUNCTIONS (SV19, ART23, MAPNN25,
  the Nov-2025 continuum lattice band) over `b_T` = 0.5-3 GeV^-1 and reading off the
  `lambda2_nu` spread -- was **not done here**. The three ranges quoted above come from
  `AN-25-085` eq. `nplunc` and §10's 3 sigma box, i.e. from the covariance `knowledge/`
  says not to trust. With the slope now measured, that work converts directly into the
  systematic: multiply by 8.3e-03 GeV^-2.
- **`lambda4_nu` was frozen at its anchor 0 throughout, and never scanned.** The lattice
  gives `0.0074 +- 0.0066 GeV^4`, and the plain arm's `+0.054 +- 0.012` is +7.0 sigma_lat
  from it, so this is the more discrepant of the two CS parameters. Its conditional slope
  in the plain arm is 4.7x `lambda2_nu`'s per unit theta. A 2D frozen scan is the honest
  version of item 2 and was out of scope here.
- ~~Is the continuation chain reversible?~~ **ANSWERED: yes.** The backward step from
  `cfrz@0.15` to 0.087 returns to the forward `frzCS@0.087` point at **L2 = 0.001** with an
  identical `2*dNLL` and `d(alpha_s)`. No hysteresis.
- **Is there a better minimum still, at the anchor?** The continuation beat the cold fit
  by `D(chi2) = 19.9` at `lambda2_nu = 0.15`. Nothing rules out a third, lower one; the
  N-random-start basin census `../260910-basins` proposed would settle it.
- **`-v 4` prints scipy's `x` once per fit, and its first element is the blinded `alphaS`
  coordinate** (`logs/fit_DATAFRZCS_*.log:273`, elided by numpy to the first two entries).
  Since the offset is a deterministic `sha256(param_name)` draw recomputable from rabbit's
  source (`../260910-blinding` finding 3) and this directory is world-readable, that is a
  recoverable value. `-v 4` was used deliberately here, matching `../260910-blinding` and
  `../260910-basins`, whose logs carry the same line and whose own reasoning was that the
  printed coordinate is blinded. Flagging it once for the study to decide, not changing the
  convention unilaterally.
- **The systematic is conditional on the TMD sector being free.** Every number here assumes
  `Lambda_2`, `Lambda_4`, `DLambda_2` float with their `sigma = 1` theta priors and are
  allowed to go unphysical. Under the damping wall the compensation is blocked and the CS
  systematic should grow; that arm (wall + frozen CS) was not run.
