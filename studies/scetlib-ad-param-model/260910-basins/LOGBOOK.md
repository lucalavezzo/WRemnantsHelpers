---
title: Which basin? Warm restarts, and the wall with preconditioning
slug: 260910-basins
study: scetlib-ad-param-model
status: done          # active | done | paused | abandoned
created: 2026-09-10
updated: 2026-09-10
owner: study-worker
---

# Which basin? Warm restarts, and the wall with preconditioning

**Task:** Two experiments on the basin problem. **(1)** Restarting each of the four
blinded-data arms from its own postfit, how far does each parameter move in units of its
own postfit sigma — i.e. are these stopping points usable as measurements? **(2)** Does the
NP damping wall **pin** the basin, or is the basin set by the numerics — run the walled fit
*with* ridge preconditioning and see which of the existing four it lands with.

---

## START HERE (status as of 2026-09-10)

> **Both answered. (1) All four arms are genuine, *stable* minima — restarted from their
> own postfits nothing moves more than 7.0e-04 sigma anywhere, and `alphaS` moves at most
> 3.4e-04 sigma. (2) The wall does NOT pin the basin: walled + ridge preconditioning lands
> on a FIFTH minimum, 2.50 away from the walled arm in a space where plain and walled are
> 1.34 apart.**
>
> So the basin spread is not a convergence problem — running longer cannot touch it — and
> the wall is not the thing that resolves it. What the wall *does* fix is the NP function's
> physicality: both walled arms reach 1 violated damping condition of 8 and a bare penalty
> of 3–5e-05, from opposite ends of the map. `alpha_s` spans **0.0054** across the five
> basins, 4–6x a single arm's sigma, so on this card with the NP sector free it is a
> property of the basin rather than a measurement.
>
> One bonus, and it is a trap worth knowing: rabbit's postfit **"Linear chi2" is selected by
> `--noPostfitProfileBB`**, not by the fit. At a bit-identical parameter vector it reads 818
> vs 773. That closes `../260910-spectral-precond`'s "One number I do not believe".

- **Next action:** none — task closed. The three follow-ups worth doing are in
  *Open questions*: the missing `spectral + wall` arm, an N-random-start basin census, and
  `--doImpacts` under the wall.
- **Blocking on:** nothing.

**Figures.** `warm_restart_shifts.png` — experiment 1, every parameter's `|dx|/sigma` for all
four arms on a log axis, `alphaS` starred. `basin_map.png` — experiment 2, the five-way `L2`
matrix over all 46 model parameters and split into the NP block and the rest, plus the
physical NP tune each arm landed on.

**Fitresults** (all on ceph, 111 MB each):
`/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260910_basins/fitresults_{DATAWALLPC,WARMPLAIN,WARMRIDGE,WARMSPEC,WARMWALL}.hdf5`

---

## Log

### 2026-09-10 — setup

Harness copied from `../260910-blinding/scripts/` (`run.sh` with `D=` repointed here,
`incontainer.sh` byte-identical, md5 `f6f87d5222a4d7d0342e3a940ea8f81e` — it pins the
fit-770 `scetlib_tf.py` and *asserts* the imported `rabbit.fitter` carries the additive
blinding change, refusing to start otherwise). Assertion passed on every launch.

Five fits launched, all on the **same** card `study_scratch/260910-anchor-verify/card_none.hdf5`,
cache `scetlib_ad_caches/pdf62_corrgrid_260827/merged_full`, SCETlib `b66f8de`
(`libscet-qT.so` md5 `71b5e68a…`), model file `260908-fit-770/lib/scetlib_tf.py`
md5 `e60ed930…`, rabbit `blinding-additive` @ `0f64bbb`, real data `-t 0`, production
config with the NP sector free, `threads=128`:

| run | what | script |
|---|---|---|
| `DATAWALLPC` | **experiment 2** — wall (tau=5) **and** ridge preconditioning | `scripts/launch_wallpc.sh` |
| `WARMPLAIN` / `WARMRIDGE` / `WARMSPEC` / `WARMWALL` | **experiment 1** — each arm restarted from its own postfit | `scripts/launch_warm.sh <arm>` |

`--externalPostfit` is the warm-restart mechanism: `load_fitresult()` assigns `self.x` from
the external file (`rabbit/fitter.py:546-548`), so without `--noFit` the minimiser simply
starts there. `--noPostfitProfileBB` is mandatory alongside `--noBinByBinStat`, or
`_profile_beta` dies with `ValueError: None values not supported` *after* writing a ~44 KB
stub that looks like an output.

### 2026-09-10 — experiment 1, the plain arm: it does not move at all

`DATABLIND` restarted from `DATABLIND`. **Largest shift over all 3720 parameters:
1.37e-09 sigma**; `alphaS` moves **1.66e-12 sigma**; zero parameters beyond 0.1 sigma.
25 iterations, 22 of them rejected, total loss improvement **9.5e-11**.
- evidence: `logs/warmcmp_plain.log`, `warm_plain.json`, `logs/warm_WARMPLAIN_260910_210343.log`

So `DATABLIND`'s **EDM of 1.39e-03 is a quadratic-model artefact**, exactly the reading
`compare_warm.py`'s docstring anticipated: the quadratic model says 1.4e-03 of loss is on
the table and the trust-region line search cannot find any of it, because the model is
built on a Hessian whose full condition number is 2.98e+09. The stop *is* the minimum.

**A byproduct that settles an open question from `../260910-spectral-precond`** (its
"One number I do not believe", and Open question 3): the postfit **linear chi2 is not
reproducible at a fixed point**. Between `DATABLIND` and a restart of it that moved
1.4e-09 sigma:

| statistic | `DATABLIND` | `WARMPLAIN` |
|---|---|---|
| prefit linear chi2 / 780 | 804, p = 26.61 % | **804, p = 26.61 %** (identical) |
| saturated 2*dNLL / 733 | 811.12, p = 2.33 % | **811.12, p = 2.33 %** (identical) |
| **postfit** linear chi2 / 780 | 809, p = 22.66 % | **766, p = 63.67 %** |

The saturated statistic and the prefit chi2 reproduce bit-for-bit; the postfit linear chi2
moves by 43 units. It is computed from `fitter.expected_events(..., compute_chi2=…)`, i.e.
from the postfit *covariance*, not from the point alone — so either it is hypersensitive at
the 1e-9-sigma level or it carries run-to-run threading noise. Either way it cannot rank
arms, and the spectral task's instruction to **trust the saturated `2*dNLL`** is correct.
The spectral arm's suspiciously good 775/780 needs no "different code path" explanation.
- evidence: both logs above, `Linear chi2:` / `Saturated chi2:` blocks

### 2026-09-10 — experiment 1, the walled arm: bit-identical

`DATAWALL5` restarted from `DATAWALL5`. **Largest shift over all 3720 parameters:
exactly 0.0** — the loss is bit-identical (411.9912132618329) at every one of the 18
iterations, all 18 rejected, and the recomputed EDM reproduces to all 16 digits
(9.632386862470065e-07). The walled stop is a fixed point of the minimiser.
- evidence: `logs/warmcmp_walled.log`, `warm_walled.json`, `logs/warm_WARMWALL_260910_210352.log`

### 2026-09-10 — the linear-chi2 anomaly is explained, and it is a FLAG, not a fit

The two warm restarts pin this down completely, because `WARMWALL` sits at a **bit-identical
parameter vector** to `DATAWALL5` and still prints a postfit linear chi2 of **773 (p = 56.72 %)**
against `DATAWALL5`'s **818 (p = 16.54 %)**; likewise `WARMPLAIN` 766 vs `DATABLIND` 809.
The saturated `2*dNLL` and the *prefit* linear chi2 are identical in both pairs.

The cause is in the source, not in the fit. `bin/rabbit_fit.py:1030-1036` calls

```python
save_hists(..., prefit=False, profile=not args.noPostfitProfileBB)
```

and that `profile` reaches `fitter.chi2()` (`rabbit/fitter.py:2011-2016`), which switches
between **two different residual definitions**:

```python
if profile:  residuals, res_cov = self._residuals_profiled(fun)
else:        residuals, res_cov = self._residuals(fun, fun_data)
```

So `--noPostfitProfileBB` silently changes *which* linear chi2 is printed. Every run that
loads an `--externalPostfit` under `--noBinByBinStat` is **forced** to pass that flag (or
crash in `_profile_beta`), so it necessarily reports the other definition.

That resolves `../260910-spectral-precond`'s "One number I do not believe" and its Open
question 3: the spectral arm's suspiciously good **775/780 (p = 54.17 %)** came from its
`--noFit --externalPostfit` readout pass, which had to pass `--noPostfitProfileBB`, while
plain/ridge/walled (809/820/818) did not. The two numbers were never on the same
definition. Nothing is wrong with the spectral minimum, and **the saturated `2*dNLL`
remains the statistic to rank arms by** — it is unaffected.
- evidence: `logs/warm_WARMWALL_260910_210352.log`, `logs/warm_WARMPLAIN_260910_210343.log`,
  `/work/submit/lavezzo/alphaS/rabbit-blinding/{bin/rabbit_fit.py,rabbit/fitter.py}`

### 2026-09-10 — experiment 1 complete: all four arms are stable

All four restarts finished cleanly (`Exit status: 0`). Every one of them is stationary.

| arm | seed (its own postfit) | max abs(dx)/sigma, all 3720 params | `alphaS` `dx/sigma` | n > 0.1 sig | loss change | EDM seed -> warm |
|---|---|---|---|---|---|---|
| plain | `fitresults_DATABLIND` | 1.37e-09 | +1.7e-12 | 0 | −9.5e-11 | 1.386e-03 -> 1.386e-03 |
| ridge | `fitresults_DATAPC2` | **6.98e-04** | **+3.4e-04** | 0 | −2.0e-08 | 4.909e-06 -> **2.572e-06** |
| spectral | `fitresults_DATASPECPF` | 1.56e-08 | −1.6e-09 | 0 | −2.8e-10 | 1.457e-07 -> 1.457e-07 |
| walled | `fitresults_DATAWALL5` | **0.0 (exactly)** | 0.0 | 0 | 0 (bit-identical) | 9.632e-07 -> 9.632e-07 |

`sigma(alpha_s)` is unchanged to six decimals in every arm (0.001321 / 0.000877 / 0.000856 /
0.001097). The saturated `2*dNLL` reproduces exactly in every arm (811.12 / 822.15 / 825.57 /
823.98 on 733 d.o.f.).
- evidence: `logs/warmcmp_{plain,ridge,spectral,walled}.log`, `warm_*.json`,
  `logs/warm_WARM*.log`

**Two of these deserve a note.**

`DATASPEC` was stopped by SIGTERM at iteration 719 *"still descending"* — it is not
descending. Restarted with the spectral transform **rebuilt at that point**, where it
reaches `kappa = 1` exactly from `5.98e+09` (against `4.22e+04 -> 1` at the cold start,
because the cold start point is indefinite), it moves **1.6e-08 sigma** and gains 2.8e-10
in loss over 22 iterations. The right statement is that it was descending by ~3e-4 per
iteration at ~500 s per iteration when it was stopped, and that from a fresh trust radius
with a far better transform there is nothing left to descend into. Its numbers are
measurements at a minimum after all.

The **preconditioner is a different object on a warm restart**, and that is the point, not
a flaw. Built at the *anchor* start point the reference Hessian is indefinite and the ridge
escalates to 5.9 % of `max|diag|` (`4.22e+04 -> 1.75e+04`); built at the *postfit* it is
positive definite, the default `1e-08` ridge suffices, and `2.17e+10 -> 204`. So the warm
restart is a **harder** stationarity test than the cold run's own numerics were, not an
easier one — and it still finds nothing to gain.

**The linear-chi2 explanation gets its control.** Three of the four seeds were produced
*without* `--noPostfitProfileBB`; the spectral seed `DATASPECPF` was produced *with* it
(its `--externalPostfit` readout had no choice). Every warm restart necessarily passes it.
Prediction: the three restarts move to the other definition, the spectral one does not.

| arm | seed postfit linear chi2 / 780 | warm restart |
|---|---|---|
| plain | 809 (p = 22.66 %) | 766 (p = 63.67 %) |
| ridge | 820 (p = 15.74 %) | 773 (p = 56.03 %) |
| walled | 818 (p = 16.54 %) | 773 (p = 56.72 %) |
| **spectral** (seed already had the flag) | **775 (p = 54.17 %)** | **775 (p = 54.17 %)** — identical |

That is the control, and it passes. The statistic is a function of the flag, not of the
fit. `sigma(alpha_s)`, EDM and the saturated `2*dNLL` are unaffected in all four.

### 2026-09-10 — experiment 2: `DATAWALLPC` is a **fifth** minimum, not either cluster

The walled fit with `DATAPC2`'s ridge preconditioning ran 1:00:41 (263 iterations,
2126 Hessian-vector products, 3437 s of `minimize()`), exited `status: 2` / `rc 0`, and is a
genuine minimum (0 negative covariance eigenvalues, Cholesky clean — same test as the other
four, `../260910-blinding/scripts/check_minimum.py`).
- evidence: `logs/fit_DATAWALLPC_260910_210224.log`, `logs/analyse_all_260910_220343.log`

It does **not** land where the walled arm landed, and it does not land with the
preconditioned pair either. `L2` over the 46 non-`alphaS` model parameters
(`basin_map.png`, left):

| | plain | ridge | spectral | walled | **wall+ridge** |
|---|---|---|---|---|---|
| plain | 0 | 4.19 | 4.06 | **1.34** | 2.37 |
| ridge | 4.19 | 0 | **1.26** | 4.08 | 3.30 |
| spectral | 4.06 | 1.26 | 0 | 4.06 | 3.62 |
| walled | 1.34 | 4.08 | 4.06 | 0 | 2.50 |
| **wall+ridge** | **2.37** | 3.30 | 3.62 | **2.50** | 0 |

The two known clusters are 1.26–1.34 wide internally and ~4.1 apart. `wall+ridge` is
**2.37 from plain and 2.50 from walled** — nearer that side, but ~1.9x the cluster's own
width away from either member, and 3.30–3.62 from the preconditioned pair. It is its own
point.

**Splitting the same distance is where it gets interesting.** The 46 parameters are 5 NP
lambdas plus 41 profile scales / resummation TNPs / PDF eigenvectors, and the two halves
disagree:

| nearest arm to `wall+ridge` | distance | runner-up |
|---|---|---|
| **NP block (5 lambdas)** | **spectral, 0.29** | ridge 0.80, walled 0.90, plain 1.52 |
| **everything else (41)** | **plain, 1.82** | walled 2.33, ridge 3.20, spectral 3.61 |

So `DATAWALLPC` is a **hybrid**: the *preconditioned* cluster's NP tune (closer to
`DATASPEC` than `DATASPEC` is to `DATAPC2`) bolted onto the *unpreconditioned* cluster's
scale/TNP/PDF tune. The wall and the preconditioner are each steering a different block.

---

## Result

### Comparability, stated before any number

All five fits share **card** `study_scratch/260910-anchor-verify/card_none.hdf5` (2D
`ptll x yll`, 780 bins, 3673 card nuisances + 47 model parameters), **cache**
`scetlib_ad_caches/pdf62_corrgrid_260827/merged_full`, **SCETlib** `b66f8de`
(`libscet-qT.so` md5 `71b5e68a0cfed89326ff4ed521d37300`), **model file**
`260908-fit-770/lib/scetlib_tf.py` md5 `e60ed930…`, **fitter** `rabbit.fitter` from the
`blinding-additive` worktree at `0f64bbb` (asserted at every launch), **real data** `-t 0`,
**production config with the NP sector free**, `threads=128`, `--earlyStopping 100`.

1. **`alphaS` is blinded.** No central value appears here or in any log in this directory.
   `sigma`, EDM, losses, p-values, and **differences between arms in units of sigma** are
   safe — the last only because the blinding is *additive* and the offset is the same
   deterministic function of the same card in every arm.
2. **The two walled losses carry the wall penalty inside `fun`.** Every `Delta` below has it
   removed (`bare penalty x exp(2 tau)`, `tau = 5`): 0.6490 for `DATAWALL5`, 0.9921 for
   `DATAWALLPC`.
3. **`DATAWALLPC` ran without `--doImpacts`**, matching `DATAWALL5` and unlike `DATAPC2`, so
   its *total* wall clock is short by ~20 min against the ridge arm; `minimize()` seconds,
   `nit` and `nhev` are comparable to all four. The NP-group impact on `alphaS` under the
   wall is still unmeasured.
4. **Two flags come with the preconditioner, not with the wall**: `--stallRelTol 1e-5` and
   the `--preconditionParams` scope. Both are copied verbatim from `DATAPC2`, including its
   `--preconditionParams 'b0_over_bmax_nu' matched no parameters` warning.
5. **`DATASPEC`'s numbers come from a second process** (`--noFit --externalPostfit` at its
   SIGTERM snapshot). Experiment 1 shows that point is stationary, so this is a measurement
   at a minimum — but its `nhev` does not exist and cannot be recovered.
6. **The postfit "Linear chi2" is not comparable across these runs.** It is selected by
   `--noPostfitProfileBB` (see the log entry above); it is excluded from every conclusion
   below. The saturated `2*dNLL` is the statistic used.
7. **`sigma` on a railed parameter is not a measurement.** `DATAWALL5`'s `lambda2_nu` sits at
   the 5e-3 wall margin, so its error is the wall width.

### Experiment 1 — all four stops are minima, and they are usable

| arm | max abs(dx)/sigma, all 3720 params | `alphaS` `dx/sigma` | n > 0.1 sig | EDM seed -> warm |
|---|---|---|---|---|
| plain `DATABLIND` | 1.37e-09 | +1.7e-12 | 0 | 1.386e-03 -> 1.386e-03 |
| ridge `DATAPC2` | 6.98e-04 | +3.4e-04 | 0 | 4.909e-06 -> 2.572e-06 |
| spectral `DATASPECPF` | 1.56e-08 | −1.6e-09 | 0 | 1.457e-07 -> 1.457e-07 |
| walled `DATAWALL5` | **0.0 exactly** | 0.0 | 0 | 9.632e-07 -> 9.632e-07 |

**Verdict: stable.** The largest move anywhere, across four arms and 14 880 parameter
slots, is **7.0e-04 sigma**, and `alphaS` never moves more than **3.4e-04 sigma**.
`sigma(alpha_s)` and the saturated `2*dNLL` reproduce exactly in every arm. And the test is
harder than it looks: on a warm restart the preconditioner is rebuilt at the *postfit*,
where the reference Hessian is positive definite and the ridge reaches `2.17e+10 -> 204`
(against `4.22e+04 -> 1.75e+04` from the indefinite anchor), and the spectral transform
reaches `kappa = 1` exactly — better conditioning than the cold runs ever had, and it still
finds nothing.

So **the residual EDMs are quadratic-model artefacts, not unfinished minimisation.** Plain's
1.39e-03 is the clearest case: the model claims 1.4e-03 of loss is available and the
minimiser recovers 9.5e-11 of it, because that model is built on a Hessian of condition
number 2.98e+09. And **`DATASPEC` was not "still descending"** when it was stopped — from a
fresh trust radius with a `kappa = 1` transform it gains 2.8e-10 in 22 iterations.

**Consequence: the spread between the arms is real physics-or-numerics, not sloppy
minimisation.** Nothing can be fixed by running longer.

### Experiment 2 — the wall pins the *physics*, not the *basin*

| | plain | ridge | spectral | walled | **wall+ridge** |
|---|---|---|---|---|---|
| loss (`fun`) | 405.561 | 411.075 | 412.785 | 411.991 | **419.547** |
| `Delta(chi2)` vs plain, penalty removed | 0 | +11.03 | +14.45 | +11.56 | **+25.99** |
| iterations / `nhev` / `minimize()` | 221 / 766 / 2645 s | 292 / 2087 / 4049 s | 719 / n.a. / 8594 s | 138 / 624 / 1509 s | 263 / 2126 / 3437 s |
| **EDM** | 1.386e-03 | 4.909e-06 | 1.457e-07 | 9.632e-07 | **3.283e-11** |
| saturated `2*dNLL` / 733 | 811.12 | 822.15 | 825.57 | 823.98 | **839.09** |
| saturated p | 2.33 % | 1.20 % | 0.96 % | 1.07 % | **0.39 %** |
| `sigma(alpha_s)` | 0.001321 | 0.000877 | 0.000856 | 0.001097 | **0.001230** |
| NP conditions violated | 2/8 | 2/8 | 3/8 | **1/8** | **1/8** |
| NP bare penalty | 4.10e-03 | 1.22e-02 | 1.16e-04 | **2.95e-05** | **4.50e-05** |
| card nuisances: max abs pull, n > 2 sig | 1.219, 0 | 2.173, 1 | 2.265, 1 | 1.315, 0 | 1.764, 0 |
| postfit cov: negative eigenvalues | 0 | 0 | 0 | 0 | **0** |

**The answer is the troubling one.** Combining the two interventions does not reproduce
either. It produces a fifth minimum, 2.50 from `DATAWALL5` in a space where the walled arm
and the plain arm are 1.34 apart — so the wall does **not** determine where the fit lands.
What the wall *does* determine is that the NP function is **physical**: both walled arms sit
at 1 violated condition of 8 and a bare penalty of 3–5e-05, two orders of magnitude below
plain's and ridge's. The basin is still chosen by the numerics.

And `alphaS` follows the basin. Differences between arms, in units of the larger of the two
postfit sigmas (offset-free under additive blinding):

| | plain | ridge | spectral | walled | wall+ridge |
|---|---|---|---|---|---|
| plain | 0 | **+3.51** | **+4.08** | +0.13 | +1.02 |
| ridge | −3.51 | 0 | +0.85 | −4.08 | −2.68 |
| spectral | −4.08 | −0.85 | 0 | **−4.76** | −3.29 |
| walled | −0.13 | +4.08 | **+4.76** | 0 | +0.96 |
| wall+ridge | −1.02 | +2.68 | +3.29 | −0.96 | 0 |

The widest pair (`walled` vs `spectral`) differs by **0.0054 in `alpha_s`** — 4.1x the
loosest of the five sigmas and 6.3x the tightest — while `sigma(alpha_s)` itself spans 54 %
(0.000856–0.001321). `wall+ridge` again sits with the `{plain, walled}` side in `alphaS`
(±1 sigma) and 2.7–3.3 sigma from the preconditioned pair.
- evidence: `logs/alphas_offsets.log`, `scripts/alphas_offsets.py`

### Physics read

**Checked against `AN-25-085`, not against the code.** `detector_extraction.tex`
Tab. `tab:z-reco-ho-results` quotes `alpha_s(mZ) = 0.11800 +/- 0.00099` for SCETlib
N3+0LL + DYTurbo NNLO. Two caveats come first: that table is **Asimov** — the section
opens *"The analysis is blinded. All results shown in this sub-section are produced with
the Asimov dataset"* — and it is a **4D** `ptll x yll x cosTheta* x phi*` fit in
40x20x8x8 = 51 200 bins with the NP model entering as the standard constrained theory
variations. Our arms are **blinded real data**, **2D** `ptll x yll` in 780 bins (and on a
finer low-`ptll` binning than the AN's, with no 44–100 GeV bin), with **8 NP lambdas
floating**. The right use of the AN number is as an order-of-magnitude anchor, not a
cross-check: our `sigma(alpha_s)` of 0.000856–0.001321 straddles it, which says the
sensitivity is in the right place.

**The number that matters is that `alpha_s` moves by 0.0054 between basins** — about
5.5x the AN's total quoted uncertainty, and 4–6x the internal sigma of any single arm.
Taken with experiment 1, which rules out "run it longer", this says plainly: **with the NP
sector free on this card, `alpha_s` is not yet a well-defined quantity.** It is a property
of which minimum the optimizer stopped in, and that is currently chosen by preconditioning.

**What the NP functions say about the five points** (formulas as ported in
`np_damping_wall.py` from the SCETlib source the fit links, `tanh_2` branches, evaluated at
the raw `b_T` since `b0_over_bmax_global = 0`):

| arm | `lambda2_nu` | `lambda4` | CS kernel anti-damps for | conditions violated |
|---|---|---|---|---|
| plain | **−0.0583** | −0.0027 | `b_T < 1.04 GeV^-1` — **inside** the constrained region | 2/8 |
| ridge | +0.1687 | +0.0014 | `b_T > 11.1 GeV^-1` | 2/8 |
| spectral | +0.1192 | −0.0023 | `b_T > 10.8 GeV^-1` | 3/8 |
| walled | +0.0049 *(railed)* | +0.1240 | `b_T > 3.38 GeV^-1` | 1/8 |
| **wall+ridge** | **+0.0910** | +0.0006 | `b_T > 10.5 GeV^-1` | 1/8 |

This is the one place where combining the two interventions is clearly *better* than either.
`DATAWALL5` satisfies the CS small-`b` condition only by **railing against the wall** at the
5e-3 margin, which is a constraint being enforced, not a preference being expressed — and it
pays for it with `lambda4 = +0.124`, an order of magnitude above any other arm, and with the
anti-damping still starting at 3.4 GeV^-1. `DATAWALLPC` lands at `lambda2_nu = +0.091`
**in the interior**, a factor 19 further from the wall, only 40 % below the lattice anchor
0.15 that `knowledge/30_physics_global/np_parametrization_constraints.md` records, with
`lambda4` back to ~0 and the anti-damping pushed out to 10.5 GeV^-1 where `f^NP` has long
since killed the integrand. So *preconditioning is what lets the walled fit find a physical
NP function it actually likes, rather than one it is being held at.*

The price is the saturated p-value, and it is steep: **0.39 %**, the worst of the five, at
`Delta(chi2) = +14.4` above `DATAWALL5` and `+26.0` above the unwalled plain arm. The
direction of every one of these numbers is the same tension the `np-wall-local-minima` study
and the NP-constraints note already record — *the data prefer an unphysical NP function* —
and this task sharpens it: the more physical the NP tune, the worse the description of the
data, monotonically across all five arms. Meanwhile the experimental sector stays clean in
every arm (max card-nuisance pull 1.22–2.27 over 3673, at most one beyond 2 sigma), so none
of this is the detector model absorbing the strain.

---

## Findings

1. **All four existing stops are minima and are usable.** Restarted from their own postfits,
   the largest move anywhere across 4 arms x 3720 parameters is 7.0e-04 sigma and `alphaS`
   moves at most 3.4e-04 sigma. The residual EDMs (up to 1.39e-03) are quadratic-model
   artefacts of a Hessian with condition number ~3e+09, not unfinished minimisation —
   (evidence: `logs/warmcmp_*.log`, `warm_*.json`, `warm_restart_shifts.png`).
2. **`DATASPEC` was not "still descending".** Restarted with its transform rebuilt at that
   point (`kappa = 1` exactly, from `5.98e+09`) it gains 2.8e-10 in 22 iterations. Its EDM /
   sigma / saturated chi2 are measurements at a minimum — (evidence:
   `logs/warm_WARMSPEC_260910_210857.log`, `logs/warmcmp_spectral.log`).
3. **The wall does not pin the basin.** Wall + ridge preconditioning lands 2.50 from the
   walled arm in a space where plain and walled are 1.34 apart, and 3.30–3.62 from the
   preconditioned pair: a fifth minimum, positive definite, `EDM 3.28e-11` — (evidence:
   `logs/analyse_all_260910_220343.log`, `basin_map.png`).
4. **The wall pins the NP function's physicality, and only that.** Both walled arms reach
   1 violated condition of 8 with a bare penalty of 3–5e-05, two orders below plain
   (4.10e-03) and ridge (1.22e-02), from opposite ends of the map — (evidence: same).
5. **The wall and the preconditioner steer different blocks.** Split by sector,
   `wall+ridge` is nearest `spectral` in the 5 NP lambdas (0.29, closer than
   `spectral`–`ridge` at 0.55) and nearest `plain` in the 41 scales/TNPs/PDF eigenvectors
   (1.82) — (evidence: `logs/spec_split.log`, `basin_map.png`).
6. **`alpha_s` spans 0.0054 across the five basins** — 4.1–6.3x a single arm's sigma and
   ~5.5x the AN's total quoted uncertainty — with `sigma(alpha_s)` itself spanning 54 %.
   Combined with Finding 1, `alpha_s` on this card with the NP sector free is a property of
   the basin, not yet a measurement — (evidence: `logs/alphas_offsets.log`).
7. **Preconditioning lets the walled fit be physical *by preference* rather than *by
   constraint*.** `DATAWALL5` rails `lambda2_nu` at the 5e-3 margin; `DATAWALLPC` sits at
   +0.091, interior, 40 % below the lattice anchor 0.15, with `lambda4` back to ~0 and the
   CS anti-damping pushed from 3.4 to 10.5 GeV^-1 — (evidence: same log, `basin_map.png`).
8. **rabbit's postfit "Linear chi2" is selected by `--noPostfitProfileBB`**, which routes
   `fitter.chi2()` to `_residuals` instead of `_residuals_profiled`
   (`bin/rabbit_fit.py:1030-1036`, `rabbit/fitter.py:2011-2016`). At a *bit-identical*
   parameter vector it reads 818 vs 773. Any `--externalPostfit` run under
   `--noBinByBinStat` is forced to pass that flag, so its linear chi2 is never comparable to
   a direct fit's. The saturated `2*dNLL` is unaffected — (evidence:
   `logs/warm_WARM*.log`; this closes `../260910-spectral-precond`'s Open question 3).

*Findings 1, 2 and 8 are facts about rabbit and this likelihood rather than about this
study; 8 in particular belongs in `knowledge/` — it is a reporting trap that will bite any
two-pass fit.*

---

## Open questions

- **Which basin to quote is still open, and is now harder.** Experiment 1 removes
  "unconverged" as an explanation and experiment 2 removes "the wall decides it". The
  remaining discriminators are all physics: the saturated p-value prefers `plain` (2.33 %)
  whose NP function is the *least* physical, and `wall+ridge` (0.39 %) is the most physical
  and the worst-fitting. Ranking them needs a criterion nobody has stated yet.
- **Is there a sixth?** Five configurations have produced five minima. The obvious test is
  cheap and was not run: the same card from N randomised starts with no preconditioning and
  no wall, to measure how many basins there are and how the likelihood is distributed over
  them, rather than sampling them one flag at a time.
- **Spectral + wall was not run.** `wall+ridge` differs from `walled` by the ridge; the
  spectral transform reaches `kappa = 1` where the ridge manages `1.45e+04`, and on the NP
  block `wall+ridge` already sits closest to `spectral`. That is the one arm of the 2x2 that
  is missing.
- **`--doImpacts` under the wall is still unmeasured** (both walled arms skipped it), so the
  NP-group impact on `alpha_s` in the physical basin is unknown. It is the number that would
  say how much of the 54 % `sigma` spread is the NP block.
- **`lambda2_nu` vs the lattice.** `DATAWALLPC` reaches +0.091 against the anchor 0.15
  without being held there. A 1D scan of the loss against `lambda2_nu` fixed at
  0 / 0.05 / 0.10 / 0.15, *with* preconditioning, would now separate "the data dislike the
  lattice tune" from "the data dislike damping" much more cleanly than it could from the
  railed walled arm. (Carried over from `../260910-wall-port`; this task makes it sharper,
  not answered.)
- **The `--stallRelTol 1e-5` preconditioner refresh never fires** in any arm, walled
  included (`Preconditioner reference matrix` appears once, `restarting` zero times). Every
  preconditioned result here is therefore a transform built once, at the start point. The
  warm restarts show that a transform built at the *minimum* is far better conditioned
  (`2.17e+10 -> 204` vs `4.22e+04 -> 1.75e+04`), so a refresh that actually fired might
  change which basin a cold fit reaches.
