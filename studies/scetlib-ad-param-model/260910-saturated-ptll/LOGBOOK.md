---
title: Saturated projection test on ptll, walled vs unwalled
slug: 260910-saturated-ptll
study: scetlib-ad-param-model
status: done
created: 2026-09-10
updated: 2026-09-10
owner: study-worker
---

# Saturated projection test on ptll, walled vs unwalled

**Task:** Does rabbit's projected (ptll-shape) saturated chi2 test run on our param
model, and if so, is the ptll shape better or worse described by the walled than by
the unwalled blinded-data fit?

---

## START HERE (status as of 2026-09-10)

> **The test does NOT run in stock rabbit — a genuine incompatibility, confirmed
> end to end. The physics question is answered anyway, two independent ways, and
> both say the same thing: the ptll SHAPE is described by both fits, and the wall
> costs it very little.**
> Exact, penalty-free lower bound on the projected saturated statistic:
> **q = 38.88 / 39 dof (p ≤ 47.5 %) unwalled, 42.57 / 39 (p ≤ 32.0 %) walled**.
> The whole-fit tension (2.33 % → 1.07 %) is therefore **not** a ptll-shape
> failure: an exact partition of the Poisson deviance puts only **+3.70** of the
> wall's **+8.71** deviance cost in the ptll marginal — and **+2.99 of that
> +3.70 sits at qT < 10 GeV**, where the NP form factor acts. The rest is in the
> rapidity structure within each ptll bin.

- **Next action:** none for the physics question. Two patched runs that produce
  the *exact* statistic were launched and were **still minimising after 2 h**
  (see *The patched runs*); they are resumable from their snapshots. Collecting
  them would sharpen the bound but is not needed for the answer, and their
  arm-to-arm comparison would be *less* trustworthy than the bound's — see the
  degeneracy caveat.
- **Blocking on:** nothing.

---

## Log

### 2026-09-10 — is the clash real? Yes, and it is not a flag to override

`--computeSaturatedProjectionTests` builds
`CompositeParamModel([fitter.param_model, SaturatedProjectModel(...)])`
(`bin/rabbit_fit.py:410`). Both submodels carry POIs and they disagree on
`allowNegativeParam`, so `CompositeParamModel.__init__` raises
(`rabbit/param_models/param_model.py:180`).

Established twice, cheap first and then for real:

1. **Cheap probe** (`scripts/probe_saturated.py`, 9.5 s, evidence
   `logs/probe_260910_173652.log`) — the REAL card, the REAL `Project ch0 ptll`
   mapping and the REAL `SaturatedProjectModel` built from its
   `output_indices()`, against a stub carrying only our model's fitter-facing
   declaration (`npoi=1`, `allowNegativeParam=True`, `blind_additive=True`; the
   flags are read straight out of `scetlib_ad/param_model.py:731`, so the stub
   avoids the 8.7 GB cache load without softening the test). Result:
   ```
   [probe] SaturatedProjectModel: npoi=39 npou=0 allowNegativeParam=False
   [probe] RESULT: RAISED ValueError: CompositeParamModel: submodels with POIs
           disagree on allowNegativeParam; ...
   ```
   It also pins the ndof: the card is `ch0` with `ptll` (39) x `yll` (20) = 780
   bins, so the projected test has **ndf = 39**.
2. **End to end**, both arms, stock driver, `--noFit --externalPostfit` on the
   matched blinded fitresult (`logs/sat_UNWALL_260910_174546.log`,
   `logs/sat_WALL5_260910_174548.log`). Both reach the postfit mapping, print
   the projected *linear* chi2, and then die with the same `ValueError`
   (`Exit status: 1`; 455 s / 341 s of CPU, ~4 min wall, essentially all of it
   the cache load). So it does raise — the parent session's 2-minute timeout had
   simply cut it off inside the cache load.

**Why this is genuine and not a flag to flip.** `SaturatedProjectModel`'s
parameters are per-bin *yield* scale factors; `allowNegativeParam=False` makes
the fitter store them as `sqrt(value)`, which is what keeps expected yields
positive. Our POI is `alphaS` as a unit nuisance, which must be allowed
negative — and rabbit *refuses* `blind_additive=True` without it
(`fitter.py:272`), additive blinding being the whole reason `sigma(alphaS)` and
the impacts come out unblinded. One squaring transform cannot serve both.

**Two rabbit gotchas found on the way**, both worth knowing before anyone tries
this again:

- `--computeSaturatedProjectionTests` is a **silent no-op without
  `--saveHists`**: the block lives inside `save_hists()`'s postfit mapping loop.
- The block calls `fitter_saturated.minimize()` **unconditionally** — it does
  **not** respect `--noFit`. So "reuse the converged postfit" only skips the
  *main* fit; the saturated fit is always a fresh minimisation.
- `--externalPostfit` with `--noBinByBinStat` needs `--noPostfitProfileBB`, or
  `load_fitresult()` ends in `_profile_beta()` on `None` tensors
  (`ValueError: None values not supported`, `fitter.py:1902`). That killed the
  first pair of runs.

### 2026-09-10 — control: the machinery itself is fine

`scripts/launch_mu_control.sh` → `logs/mu_control_260910_174614.log`. Same card,
same data, same `-m Project ch0 ptll`, but the default `Mu` param model, which
has `npoi = 0` on this card — so the saturated model is the only POI-carrying
submodel and the vote is unanimous. It ran in ~1 minute and printed

```
Saturated chi2:  ndof: 39   2*deltaNLL: 1491.37   p-value: 0.0%
```

The p-value is meaningless (a bare template fit of this card without the theory
model is a terrible fit — its whole-fit saturated chi2 is 2271.82/780), but that
is not what the control is for: **the machinery works, and our model is the
obstacle.**

### 2026-09-10 — the number, without the machinery

The projected saturated statistic is
`q = 2 [ NLL(main postfit) - NLL(saturated) ]` on 39 dof, where the saturated
reference minimises over 39 free per-ptll-bin yield scales `r_j` *and* all the
model's parameters. Hold the model's parameters at the main postfit and the
remaining minimisation is **closed form** for rabbit's Poisson likelihood
(`fitter.py:_compute_ln`, no `--chisqFit`, `--noBinByBinStat`): within output
bin `j` the dependence is `sum_i [ r_j N_i - D_i log(r_j N_i) ]`, minimised at
`r_j = D_j / N_j`, giving the grouped Poisson deviance

```
q_fixed = 2 sum_j [ N_j - D_j + D_j log(D_j / N_j) ] .
```

Letting the other parameters move can only lower `NLL(saturated)`, so
**`q_true >= q_fixed` and `p_true <= p_fixed`**: an upper bound on the p-value.
Two things make it the right quantity to compare the arms with:

- the **wall penalty and the Gaussian constraint term cancel identically**
  (they depend only on the held parameters), so no penalty subtraction is needed
   — unlike the whole-fit saturated chi2, where the walled 1.07 % had to be
  hand-corrected to 1.16 %;
- it is **insensitive to how well the main fit converged**, because the same
  point enters both sides. That matters here: the unwalled arm stopped at
  EDM 1.386e-03 against the walled arm's 9.632e-07.

`scripts/projected_deviance.py` (evidence `logs/deviance2_260910_175319.log`)
reads `hist_postfit_inclusive` and `hist_nobs` out of each fitresult, and first
**validates itself** against rabbit's own numbers: summed over all 780 bins it
gives 777.7317 (unwalled) and 786.4367 (walled) against rabbit's
`2*nllvalreduced` of 811.1217 and 823.9824, the difference being exactly the
constraint term (and, walled, the wall penalty), which this construction does
not include. A Gaussian cross-check `sum (D-N)^2/N` agrees with the Poisson
deviance to 3e-3.

### 2026-09-10 — the patched runs (the exact statistic)

`patched/rabbit_fit_satpatch.py` (diff: `patched/satpatch.diff`, 113 lines) is a
study-local copy of the driver — byte-identical base, md5 `729e4014...`, and
the shared checkout's `bin/rabbit_fit.py` and the worktree's are the same file,
so it is exactly the driver that ran above — with two changes:

1. **`allowNegativeParam` passed through** from the parent model. Safe *for this
   fit*, and measured rather than assumed: the closed-form single-bin optima are
   `r_j = D_j/N_j` in **[0.9949, 1.0049]** in both arms, so no bin is anywhere
   near the positivity boundary the squaring exists to protect. It would **not**
   be safe in general — a bin whose data wanted `r_j <= 0` could drive the
   expected yield negative and the Poisson `log()` to NaN.
2. **Blinding re-armed, and the composite fit warm-started** at the main postfit
   with the bin scales at 1. Both halves fix real defects (see *Findings*), and
   the warm start is self-validating: the log prints

   ```
   [satpatch] 2*reduced_nll at the warm start = 811.1217 (main fit: 811.1217)
   [satpatch] 2*reduced_nll at the warm start = 823.9824 (main fit: 823.9824)
   ```

   i.e. the composite's `[poi_o | poi_sat | pou_o | theta]` layout, the
   blinded-coordinate copy and the re-armed offsets together land *exactly* on
   the main fit's point, so `q >= 0` by construction and cannot be inflated by a
   failed reference fit. `--unblind 'saturated_.*'` unblinds the 39 bin scales
   and **only** those (the log names all 39; `alphaS` is not among them). For
   the walled arm the wall re-arms itself on the composite layout by name,
   `armed on 6 of 8 condition(s)`, as the port was designed to.

**Status: both were still minimising after 2 h of wall clock and were left
running.** They are not needed for the answer, and there is a reason to prefer
the bound to them even when they land. Freeing 39 per-ptll-bin scales removes
essentially all of the constraint on the model's own ptll-shaping parameters —
the NP lambdas, the TNPs, the resummation scales, and `alphaS` itself, whose
effect on this fit *is* a ptll shape — so the composite likelihood has a large,
nearly flat degenerate subspace. rabbit's own code comments on this for the
Hessian ("the saturated parameters can be degenerate with parameters of the
original model"); here it also makes the *minimisation* crawl. The bin scales
had drifted to 0.958–1.039 after 80 min, far outside the [0.9953, 1.0048] band
their single-bin optima occupy, i.e. the fit is wandering along the degenerate
direction rather than converging. Two arms stopping at unequally converged
points in a flat valley would make the *difference* of their exact `q` values
less reliable than the difference of the `q_fixed` values, which are exact and
identically conditioned by construction. **So `q_fixed` is the number to quote.**

Evidence: `logs/satpatch_UNWALL_260910_174856.log`,
`logs/satpatch_WALL5_260910_174858.log`, progress probes
`logs/snapprog*.log` (`scripts/read_snapshot.py`);
outputs under
`/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260910_saturated_ptll/`.
To resume either arm rather than restart it, add
`--externalPostfit .../snapshot_SATPATCH{UNWALL,WALL5}.hdf5` (snapshots are
written every 15 min).

---

## Result

### Comparability caveats, first

- **Blinded real data** (`-t 0`) in both arms, `alphaS` blinded **additively**;
  no central value appears in this directory or in any log in it. sigma and
  p-values are unaffected by additive blinding (unit Jacobian).
- Same card `study_scratch/260910-anchor-verify/card_none.hdf5`, same cache
  `scetlib_ad_caches/pdf62_corrgrid_260827/merged_full`, SCETlib **b66f8de**
  (`libscet-qT.so` md5 `71b5e68a0cfed89326ff4ed521d37300`), rabbit worktree
  `rabbit-blinding` @ **0f64bbb**, driver `bin/rabbit_fit.py` md5
  `729e4014a0bf810f53cce086c6125771`. So the two arms differ **only** by
  `--regularizationStrength 5 -r ...NPDampingWall`.
- Both main fits stop at scipy `status: 2`. The walled one is 1439x better
  converged (EDM 9.632e-07 vs 1.386e-03), so where a number depends on the
  reference fit having found its minimum, the unwalled arm is the weaker of the
  two. `q_fixed` does not depend on that (same point both sides); the *linear*
  chi2 and the patched exact `q` do.
- The **linear** chi2 uses `V_pred + V_data` (`fitter.py:_residuals`). For a fit
  that used these data the postfit residual covariance is `V_data - V_pred`, so
  adding them over-covers: those p-values are **conservative**. They are also
  the only numbers here that see the wall's *curvature* — the walled `V_pred`
  comes from the walled Hessian, which the wall stiffens by ~1e5 in `lambda4`'s
  direction. `q_fixed` and the patched `q` are free of both effects.
- `q_fixed` is a **bound**, not the statistic: `p_true <= p_fixed`.

### The numbers

| ptll-shape test (39 ptll bins) | unwalled | walled tau=5 | ndf |
|---|---|---|---|
| `q_fixed` (exact, penalty-free lower bound) | **38.88** | **42.57** | 39 |
| → p (upper bound on p_true) | **≤ 47.5 %** | **≤ 32.0 %** | |
| linear chi2, postfit (conservative)* | 35.1 → p = 64.76 % | 37.6 → p = 53.51 % | 39 |
| linear chi2, prefit (the anchor tune) | 40.6 → p = 40.17 % | same | 39 |

\* the runs that printed these died at the composite construction before
`ws.dump_and_flush()`, so their fitresults hold only `meta`; the chi2 values are
back-solved from the p-values rabbit printed (which are given to 2 decimals),
not read from a file. The p-values themselves are the log's own.

For reference, the whole-fit numbers these sit inside: saturated 811.12/733
(p = 2.33 %) unwalled, 823.98/733 (p = 1.07 %, 1.16 % penalty-removed) walled.

### Is the ptll shape better or worse described walled?

**Slightly worse, and by an amount that does not matter.** `Delta q = +3.70` on
39 dof, i.e. the walled tune describes the ptll marginal about one tenth of a
dof worse per dof. Both arms sit at `q/ndf` = 1.00 and 1.09 — the ptll shape is
described by both, and the p-value stays above 32 % even at the bound.

### Where the wall's cost actually goes — an exact partition

The Poisson deviance splits **identically** (no approximation; closure 1.8e-10
numerically) into the marginal and the conditional piece,

```
D(780 bins)  =  D_ptll(39 groups)  +  D( D_ij || N_ij r_j )
```

the second term being the yll shape *within* each ptll bin, at the ptll
normalisation the data prefer:

| | unwalled | walled | Delta |
|---|---|---|---|
| `D(780)` | 777.73 | 786.44 | **+8.71** |
| `D_ptll(39)` | 38.88 | 42.57 | **+3.70** |
| `D_cond` | 738.85 | 743.86 | **+5.01** |

Adding back the constraint term (which is held, so it belongs entirely to the
conditional piece) and using rabbit's own dof accounting, the residual after the
ptll projection is 772.24/694 → p = 2.05 % unwalled and 781.41/694 → p = 1.15 %
walled. **That is where the whole-fit tension lives.** Projecting onto ptll
marginalises essentially all of it away.

### Physics read

The wall exists to stop the NP form factor from *anti-damping*: the unwalled
minimum had `lambda2_nu = -0.058` with `lambda4_nu = +0.054`, so
`gamma_nu^NP > 0` for `b_T < 1.04 GeV^-1` — a sign violation of the
Collins–Soper kernel's damping requirement (`knowledge/30_physics_global/
np_parametrization_constraints.md`; the port's own reading is in
`../260910-wall-port/LOGBOOK.md`). Imposing it costs `Delta chi2 = +11.6` in the
full likelihood.

This task says **where** that cost is paid, and it is not in the observable's
own shape. Of the +8.71 units of *data–model* deviance the wall costs, only
+3.70 appear in the ptll marginal, and they are localised exactly where the NP
form factor acts: **+2.99 of the +3.70 is at `qT < 10 GeV`** and only +0.71
above it. The single largest change is the **lowest** bin, `ptll ∈ [0,1)`, where
the per-bin contribution goes 0.99 → 2.61 — the bin most sensitive to the
large-`b_T` behaviour of `F_eff`, which is precisely what the wall's
`3 lambda_inf^2 lambda4 + L_2^3 >= 0` condition governs (that condition is the
large-`b_T` limit of `arg(F_eff) >= 0`: at large `b` the cubic terms
`lambda4 b^3/linf + L_2^3 b^3/(3 linf^3)` dominate).
This is exactly where AN-25-085 puts the NP sensitivity — *"It affects the
\ptVGen spectrum, particularly at low values around and below the Sudakov peak,
which is also the region most sensitive to \alphaS"* (`AN-25-085/theory.tex`,
Sec. "Nonperturbative effects"); the Sudakov peak in this data sits at
`ptll ~ 4.5 GeV`. Above ~20 GeV the two tunes are nearly indistinguishable, as
expected once the fixed-order matching dominates.
(Per-bin table: `scripts/per_bin_delta.py` output in the log below and
`projected_deviance.npz`.) The remaining +5.01 is in the *rapidity* structure — which
is consistent with the wall's binding condition being the `|Y| = 2.5` cubic
`3 lambda_inf^2 lambda4 + L_2(Y)^3 >= 0`, a rapidity-dependent constraint
(`L_2(Y) = lambda2 + delta_lambda2 Y^2`): pushing `lambda4` from -0.0027 to
+0.124 to satisfy it at large `|Y|` is paid for in the yll description, not the
qT one.

So: **the wall does not damage the ptll description.** Anyone worried that
enforcing physical NP damping breaks the fit to the measured spectrum can be
told that the ptll shape test is comfortably passed both ways, and that the
residual tension in this fit — which is real, at the ~1–2 % level — is a
2D (qT, y) structure question, not a qT-shape question.

---

## Findings

1. **The projected saturated test cannot run on `SCETlibADParamModel` in stock
   rabbit.** `CompositeParamModel` refuses the POI-flag mix; it is a real
   representational limit (one squaring transform, two kinds of POI), not a
   missing flag. Confirmed by cheap probe and end to end in both arms —
   (evidence: `logs/probe_260910_173652.log`, `logs/sat_UNWALL_260910_174546.log`,
   `logs/sat_WALL5_260910_174548.log`)
2. **The machinery is sound; our model is the obstacle.** A `Mu`-model control
   on the same card and mapping produces a projected saturated chi2 —
   (evidence: `logs/mu_control_260910_174614.log`)
3. **The statistic is computable exactly and cheaply as a bound**, with the wall
   penalty cancelling by construction: `q_fixed` = grouped Poisson deviance of
   the projected residuals, validated against rabbit's own `nllvalreduced` —
   (evidence: `logs/deviance2_260910_175319.log`, `scripts/projected_deviance.py`)
4. **The ptll marginal is not where this fit's tension is.** Exact deviance
   partition: +3.70 of the wall's +8.71 in ptll, +5.01 in yll-within-ptll; the
   post-projection residual still gives p = 2.05 % / 1.15 % —
   (evidence: `logs/deviance2_260910_175319.log`)
5. **rabbit bug: the saturated-projection path silently DISARMS blinding.**
   `init_fit_parms(composite_model)` re-creates `_blinding_offsets_poi`/`_poi_add`
   at the composite size, i.e. ones/zeros, and nothing arms them again
   (`set_blinding_offsets` is never called after it, and `defaultassign()` — the
   one place that would — is not on this path). So the saturated fit runs in an
   **unblinded frame** and its `x` is written straight into
   `results["mappings"][...]["saturated_fit"]["parms"]`. This is independent of
   our model and affects any blinded analysis that uses the flag —
   (evidence: `rabbit/fitter.py:248-280,704-745`, `bin/rabbit_fit.py:429-450`)
6. **rabbit design issue: the saturated composite fit COLD-starts** from
   `x0default` (the model anchor) and ignores `--noFit`. For a multimodal
   likelihood like ours (`studies/np-wall-local-minima`, and the warm-vs-cold
   `Delta nll = 11.7` in memory) a cold start under-finds `NLL(saturated)`,
   which biases the statistic **low** and the p-value **high** — i.e. the test
   as implemented is optimistic exactly where it is least trustworthy —
   (evidence: `bin/rabbit_fit.py:450`, `patched/satpatch.diff`)
7. **Even patched, the composite fit is near-degenerate and slow.** Freeing the
   whole ptll marginal removes the constraint on every ptll-shaping parameter of
   the model, `alphaS` included; after 80 min the bin scales were at 0.958–1.039
   against single-bin optima inside [0.9953, 1.0048], i.e. still travelling along
   a flat direction. A practical consequence: `--computeSaturatedProjectionTests`
   on a model whose POI *is* the projected shape is expensive and its arm-to-arm
   comparison is fragile — (evidence: `logs/snapprog3.log`)
8. **Three flag traps**, all costing a run each: the test is a no-op without
   `--saveHists`; `--noHessian` cannot be combined with an `--externalPostfit`
   that carries a covariance (`fitter.py:550` raises); and
   `--externalPostfit --noBinByBinStat` needs `--noPostfitProfileBB` —
   (evidence: `logs/sat_UNWALL_260910_174150.log` for the last one)

---

## Open questions

- **Should rabbit's `SaturatedProjectModel` learn a per-submodel transform?**
  Passing `allowNegativeParam` through is a one-line fix that happens to be safe
  here (`r_j` within 0.5 % of 1) but is unsafe in general. The clean fix is for
  the fitter to apply the squaring per POI-carrying submodel rather than to the
  whole composite POI block. That is a rabbit change, not ours; worth an issue.
- **Findings 5 and 6 are upstream bugs and are not fixed anywhere but in this
  task's private copy of the driver.** Nothing in the shared tree was touched.
- The residual (post-projection) tension at p = 1–2 % is real and unexplained by
  anything in this task. A `Project ch0 yll` companion test would say whether it
  is a rapidity-shape problem or a genuine 2D correlation one. Not chased here.
- The prefit (anchor) ptll chi2 is 40.6/39 while both postfits are *better*
  (35.1, 37.6) — the fit buys very little in the ptll marginal. Consistent with
  the tension being elsewhere, but worth a glance.
