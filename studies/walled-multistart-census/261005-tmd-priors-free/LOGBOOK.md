---
title: TMD priors free (NOMTMDFREE)
slug: 261005-tmd-priors-free
study: walled-multistart-census
status: done
created: 2026-10-05
updated: 2026-10-05
owner: study-worker
---

# TMD priors free (NOMTMDFREE)

**Task:** In the nominal walled configuration (card A, lattice λ4_ν=0, `pdf62_y35_260921/merged_full_bin0xzero`, stiff wall τ=8 margin 0), warm-started from NOMSTIFF, how much do the TMD λs (λ2, λ4, δλ2), Δ`alphaS` and σ(`alphaS`) move when the NP Gaussian priors on λ2, λ4, δλ2 are removed (TMD constrained only by data + wall)?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-10-05 15:10)

> **Removing the TMD priors changes nothing that matters: Δ`alphaS` = −0.020 σ_NOM, σ(`alphaS`) ratio 0.998,
> the TMD λs move by ≤ 0.06 σ.** The fit converged (EDM 5.5e-17) at the same wall face (L2(|Y|=2.5) = 0) as NOMSTIFF.
> The data (plus the wall) constrain λ2, λ4, δλ2 12–70× more tightly than the width-0.5 priors, so the priors were not
> doing any work. A one-Newton-step prediction made before launch matched the fit to 1 %.

- **Next action:** none. Task closed.
- **Blocking on:** nothing.
- Fit: NOMTMDFREE, PID 1500752 (finished 14:51, exit 0). Log [logs/NOMTMDFREE.log](logs/NOMTMDFREE.log);
  result `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261005_tmd_priors_free/fitresults_NOMTMDFREE.hdf5`.

---

## Log

### 2026-10-05
- 15:00 NP-function plot ([scripts/run_np_function_plots.sh](scripts/run_np_function_plots.sh), the existing
  `np_function_plots.py` with `--num-cov/--den-cov` = the fitted-λ Hessian blocks [cov_NOMTMDFREE.json](cov_NOMTMDFREE.json),
  [cov_NOMSTIFF.json](cov_NOMSTIFF.json)). The two curves and bands overlap completely.
- 14:55 Comparison ([scripts/compare.py](scripts/compare.py) → [compare.json](compare.json); it reuses the census
  `analyze_census.py` helpers for the physical λs and the wall faces).
- 14:51 NOMTMDFREE finished, exit 0. minimize() 2172 s, 6 iterations, stopped on "A bad approximation caused failure to
  predict improvement" (the same stop as NOMSTIFF; this message says nothing about convergence). Postfit Hessian 587 s;
  **EDM 5.5e-17** → converged. Saturated: 2ΔNLL 752.27, ndof 775 (= 780 − 5 free param-model params), p = 71.4 %
  (NOMSTIFF: 753.23, ndof 778, p = 73.2 %. The 0.96 difference is mostly the 2 × 0.476 prior term that is now gone).
- 14:12 Iteration 2 already at 376.136598, within 2e-6 of the final NLL.
- **Configuration** (built by [scripts/build_cmds.py](scripts/build_cmds.py) from NOMSTIFF's own `meta_info["command"]`
  → [cmds/NOMTMDFREE.cmd](cmds/NOMTMDFREE.cmd)). Token diff vs NOMSTIFF, nothing else:
  `-o` → `261005_tmd_priors_free`; `--postfix NOMTMDFREE`; `--snapshotFile`; `--externalPostfit` = NOMSTIFF's fitresult
  (full-vector warm start); `--earlyStopping 100 → 20` (census convention);
  `prior_sigmas=lambda2_nu=nan` → `prior_sigmas=lambda2_nu=nan,lambda2=nan,lambda4=nan,delta_lambda2=nan`.
  Card A + lattice (`cardA_latticeASWZ_l4zero_statsyst.hdf5`, λ4_ν = 0, lattice term on λ2_ν lives in the card), cache
  `pdf62_y35_260921/merged_full_bin0xzero`, wall τ = 8, margin 0. WRemnants ccb2adb8 (= NOMSTIFF's df3c30f7 + the
  margin change, the commit the census reproduced NOMSTIFF with), rabbit 2a59246, scetlib 2dd978a.
- **The TMD priors that are being removed** (SCETlibADParamModel, `params.py` REPARAM "unit"): θ ~ N(0,1),
  physical = anchor + 0.5·θ, anchor = the correction runcard = the cache anchor (`cache.conf [Nonperturbative]`):
  λ2 = 0.4 ± 0.5, λ4 = 0.4 ± 0.5, δλ2 = 0 ± 0.5. NOMSTIFF had priors on 44 of 46 param-model params (free: `alphaS`,
  λ2_ν) (NOMSTIFF.log line "Gaussian priors on 44").
- **Where NOMSTIFF sits** ([prefit_prediction.json](prefit_prediction.json), [scripts/prefit_prediction.py](scripts/prefit_prediction.py)):

  | λ | NOMSTIFF (phys) | σ_post | pull vs prior (θ) | σ_post/σ_prior | ρ(`alphaS`, λ) |
  |---|---|---|---|---|---|
  | λ2 | 0.0256 | 0.0427 | −0.749 | 0.085 | −0.046 |
  | λ4 | 0.0876 | 0.0272 | −0.625 | 0.054 | **+0.676** |
  | δλ2 | −0.0041 | 0.0068 | −0.008 | 0.014 | +0.046 |
  | λ2_ν (free, lattice in card) | 0.0643 | 0.0229 | — | — | +0.050 |

  ½Σθ²_TMD at NOMSTIFF = 0.476: that is the whole prior contribution to NOMSTIFF's NLL (376.615).
  The data constrain the TMD λs 12–70× better than the priors, so the priors should barely matter.
- **Prediction** (one Newton step: H_free = H_NOM − P, dx = H_free⁻¹ P θ_NOM, H_NOM = inverse of NOMSTIFF's postfit
  covariance incl. the wall curvature; exact if the NLL is quadratic):
  Δ`alphaS` = **−0.020 σ_NOM**, σ(`alphaS`) ratio **1.0007**, Δλ2 = −0.0026 (−0.06σ), Δλ4 = −0.0008 (−0.03σ),
  Δδλ2 = +0.0004 (+0.06σ), Δλ2_ν = +0.0009 (+0.04σ); ΔNLL_free (from NOMSTIFF's point) = −0.0024.
  Caveat: NOMSTIFF sits on the active wall face L2(|Y|=2.5) = 0, where the τ = 8 wall is not quadratic; a move into the
  face is resisted harder than the Hessian says.
- Launched 14:00:25 (`scripts/launch.sh NOMTMDFREE`; gate slot 1, 1410 GB available).
- **Prior removal verified** from the log: "Gaussian priors on 41 parameter(s)" (NOMSTIFF: 44); the set difference
  is exactly {lambda2, lambda4, delta_lambda2}; λ2_ν still free in the param model (its lattice term is in the card,
  same card file). Wall armed on 5 of 8 conditions, as in NOMSTIFF.
- Iteration 0 loss 376.13822. NOMSTIFF minus its TMD prior term = 376.61463 − 0.47562 = 376.13901 (exact: rabbit's
  prior term is ½·cw·(θ − x0)² with x0 = 0, cw = 1, `fitter._compute_lc`; NOMSTIFF.log "lambda2: μ=0 σ=1"), so the
  first step already gained 0.0008 of the predicted 0.0024.

---

## Result

**Comparability caveats first.**
- Real data, blinded: `alphaS` appears only as a difference in units of σ_NOM. Both fits use the same card, the same data
  family and the same blinding offset, so the offset cancels in the difference.
- Same card (A + lattice, λ4_ν = 0), cache (`pdf62_y35_260921/merged_full_bin0xzero`) and wall (τ = 8, margin 0).
  The only change to the objective is that the three Gaussian prior terms ½θ² on λ2, λ4, δλ2 were removed.
- So the raw NLLs differ by construction. The like-for-like reference is NOMSTIFF minus its TMD prior term, evaluated at
  NOMSTIFF's own point. That is exact, not an approximation: rabbit's prior is the additive ½·cw·(θ − x0)² with x0 = 0,
  cw = 1 (`fitter._compute_lc`).
- Software: NOMTMDFREE ran at WRemnants ccb2adb8. NOMSTIFF ran at df3c30f7 plus the then-uncommitted margin diff, which
  ccb2adb8 committed; the census reproduced NOMSTIFF at ccb2adb8 to ≤ 2e-10 in NLL.

| | NOMSTIFF (TMD priors) | NOMTMDFREE (TMD free) | shift / σ_NOM | prediction (Newton step) |
|---|---|---|---|---|
| λ2 | 0.0256 ± 0.0427 | 0.0230 ± 0.0428 | −0.061 | 0.0230 (−0.061) |
| λ4 | 0.0876 ± 0.0272 | 0.0868 ± 0.0271 | −0.028 | 0.0868 (−0.028) |
| δλ2 | −0.0041 ± 0.0068 | −0.0037 ± 0.0069 | +0.061 | −0.0037 (+0.061) |
| λ2_ν (free; lattice term in card) | 0.0643 ± 0.0229 | 0.0652 ± 0.0229 | +0.041 | +0.0009 phys (+0.041) |
| Δ`alphaS` | — | — | **−0.020** | −0.020 |
| σ(`alphaS`) ratio free/NOM | 1 | **0.998** | | 1.0007 |
| ρ(`alphaS`, λ2) | −0.046 | −0.049 | | −0.047 |
| ρ(`alphaS`, λ4) | **+0.676** | **+0.677** | | +0.677 |
| ρ(`alphaS`, δλ2) | +0.046 | +0.049 | | +0.047 |
| ρ(λ2, δλ2) | −1.0000 | −1.0000 | | |
| active wall faces | L2(\|Y\|=2.5) = 0 | L2(\|Y\|=2.5) = 0 | | |
| EDM | 3.0e-14 | 5.5e-17 | | |
| NLL (reduced) | 376.61463 | 376.13660 | | |
| NLL without the TMD prior term | 376.13901 (= 376.61463 − ½Σθ² = 0.47562) | 376.13660 | **ΔNLL = −0.00242** | −0.00242 |

λ in physical units (anchor + 0.5·θ; λ2_ν: 0.15 + 0.1·θ), errors are the postfit Hessian σ. The shift column is
Δθ/σ_NOM. Full parameter vector: ||Δθ/σ_NOM|| = 0.110, of which NP λ 0.099; no other parameter moves by more than
0.014 σ (largest: pdfEig14). σ changes by at most 0.3 % for any parameter.

![NP functions, NOMTMDFREE vs NOMSTIFF](np_functions_NOMTMDFREE_vs_NOMSTIFF.png)

*NP functions: CS kernel γ̃_ν^NP (left) and F_eff at |Y| = 0, 1, 2, 2.5 (right). Both postfits use the same card, cache
and wall; the bands are 1000-toy 68 % bands from each fit's λ Hessian block. The two fits overlap completely.*

**Cache validity.** Without the priors the TMD λs moved by 0.003 / 0.001 / 0.0004 in physical units (≤ 0.006 θ, i.e.
≤ 0.01 prior widths). They sit where NOMSTIFF sat, 0.75 (λ2) and 0.63 (λ4) prior widths below the cache anchor
(0.4, 0.4, 0). The validation in [knowledge/…/scetlib_ad_cache_validity.md](../../../knowledge/20_frameworks/scetlib_ad_cache_validity.md)
found the cache exact (≤ 0.01 %) for λ2 and λ4 moved anywhere down to 0, and for δλ2. Its only failure mode is
λ2_ν < 0, and here λ2_ν = 0.065 > 0. So the cache is validated at this point, and no new territory was entered.

**Physics read.** The prior on the TMD λs (±0.5 around 0.4, 0.4, 0) is ≥ 12× looser than what the ptll × yll data
constrain: λ2 ± 0.043, λ4 ± 0.027, and δλ2 ± 0.007, the last pinned through the active L2(|Y| = 2.5) wall face (ρ(λ2, δλ2)
= −1). The priors therefore pulled the fit by only ~0.06 σ_post, and dropping them changes `alphaS` by −0.02 σ and its
error by −0.2 %. The `alphaS` sensitivity to the TMD sector runs through λ4 (ρ = +0.68, unchanged), and that sector is
data-determined. So the nominal σ(`alphaS`) contains no hidden prior-driven NP constraint. The tiny σ decrease (where a
quadratic model predicts +0.07 %) is the Hessian evaluated at a slightly different point on the stiff wall face, i.e.
non-quadratic wall curvature at the 0.3 % level, not a physical effect.

---

## Findings

1. The TMD λ priors (width 0.5) are inert in the nominal walled fit: Δ`alphaS` = −0.020 σ_NOM, σ ratio 0.998,
   ΔNLL (prior-free objective) = −0.0024 — (evidence: [compare.json](compare.json)).
2. The data constrain λ2, λ4, δλ2 12×, 18× and 73× more tightly than the prior; δλ2 is fixed through the active
   L2(|Y|=2.5) wall face (ρ(λ2, δλ2) = −1.0000) — (evidence: [prefit_prediction.json](prefit_prediction.json)).
3. A one-Newton-step prediction from the NOMSTIFF Hessian (H_free = H_NOM − P) reproduced the refit's λ and `alphaS`
   shifts and ΔNLL to ~1 %. This is a cheap way to answer "what if prior X is removed or rescaled" without a 50-min fit,
   as long as the move is small compared with the wall's nonlinearity. Generalizable; tell the orchestrator. —
   (evidence: [scripts/prefit_prediction.py](scripts/prefit_prediction.py) vs [compare.json](compare.json)).
4. ρ(`alphaS`, λ4) = +0.68 is the TMD channel into `alphaS`; ρ(`alphaS`, λ2) and ρ(`alphaS`, δλ2) are ≈ ±0.05 — (evidence: [compare.json](compare.json)).

---

## Open questions

- None from this task. A cousin question, not chased: the same Newton-step estimate applied to the TNP / PDF priors would
  show which priors actually carry σ(`alphaS`). That is cheap, from NOMSTIFF's covariance alone.
