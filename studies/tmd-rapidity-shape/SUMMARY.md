---
title: Rapidity dependence of the TMD NP model
slug: tmd-rapidity-shape
status: done
period: 2026-10-07 – 2026-10-08
updated: 2026-10-08
covers: 2026-10-08
---

# Rapidity dependence of the TMD NP model

> **The Y² form of the TMD NP width, L2(Y) = λ2 + δλ2·Y², is adequate, and a Y⁴ or x-dependent term is not worth building. `alphaS` is insensitive to the rapidity *shape* of L2. It does depend on the overall *level*, which is held up by the one active wall face, L2(|Y| = 2.5) ≥ 0. Raising that floor to a MAP22-like value would move `alphaS` by about −0.17σ.**

## Why

In the nominal walled fits the only active NP-wall face is L2(|Y| = 2.5) = 0, the edge of the Y² extrapolation. Our δλ2 is small and negative; the AN tune has ΔΛ2 = +0.125 ± 0.02 GeV² (theory.tex l. 297). The study asked whether Y² is adequate, how much `alphaS` depends on the forward shape, and whether a Y⁴ or x-dependent term is warranted.

## What we did

All numbers are evaluated at the minimum of **LATB8**, the nominal walled real-data fit of the [lattice-cs-kernel](https://submit.mit.edu/~lavezzo/alphaS/studies/#lattice-cs-kernel) study: card A, the |Y| ≤ 2.5 subset of the `pdf62_y35_260921` AD cache, wall τ = 8, the exact lattice CS-kernel χ² in the likelihood, and λ4_ν floating. **NOMSTIFF** is the earlier nominal fit: Gaussian lattice constraint and λ4_ν = 0, with `alphaS` 0.11σ above LATB8 and the same single active face [261007-y-shape-first-look]. A Hessian-only pass at LATB8's exact parameter vector, without the wall, gives the wall-free covariance and the linear (Newton) responses to the face value c = L2(2.5). We added residuals by |yll|, MAP22's x dependence (251 replicas), and a Y⁴ costing from the code.

| Task | Question | Answer |
|---|---|---|
| [261007-y-shape-first-look](https://submit.mit.edu/~lavezzo/alphaS/studies/#tmd-rapidity-shape/261007-y-shape-first-look) | Is Y² adequate, and how sensitive is `alphaS` to the forward L2? | Y² is adequate. `alphaS` follows the level of L2, not its shape. Y⁴ is not worth it. |

## Findings

*All numbers: real data, `alphaS` blinded. Shifts are in σ_NOM, the Hessian σ(`alphaS`) of NOMSTIFF (0.58 in raw `pdfAlphaS` nuisance units); no central value is used. L2, λ2 and δλ2 are in GeV². Responses are linear, at LATB8's physical point.*

1. **`alphaS` follows the level of L2, not its rapidity shape.** In the wall-free covariance, ρ(`alphaS`, L2(0)) = −0.44 and ρ(`alphaS`, L2(2.5) − L2(0)) = −0.025. The |Y| = 2.5 face is in effect a floor on Λ2 (0.049 ± 0.135); δλ2 only sets where it binds first. [261007-y-shape-first-look]

2. **The shape is measured, and it agrees with MAP22 rather than the AN tune.** We fit δλ2 = −0.0078 ± 0.0078 (wall-free), against −0.0079 ± 0.0011 derived from MAP22. The AN's +0.125 is 17σ away using our σ, or 6.6σ using the AN's own ±0.02. The prior is 64× wider than this σ. [261007-y-shape-first-look]

3. **The active face is a mild floor on `alphaS`.** The slope is d`alphaS`/dc = −3.19 σ_NOM/GeV², i.e. −0.032 σ_NOM per +0.01 GeV² of forward L2 (NOMSTIFF: −0.026). Removing the face would gain only Δχ² = 0.50 in the likelihood without the wall (data + priors + lattice), so there is no tension. Raising the floor to MAP22's forward value (0.052) moves `alphaS` by −0.17σ_NOM, at Δχ² ≈ 0.6. The boundary narrows σ(`alphaS`) from 1.074 to 0.972 σ_NOM. [261007-y-shape-first-look]

   ![L2(Y) for LATB8 with wall-free band, NOMSTIFF, MAP22, AN nominal](261007-y-shape-first-look/L2_of_Y.png)

   *L2(Y): LATB8 (note the floor at |Y| = 2.5), NOMSTIFF, MAP22 (central replica, Z/13 TeV) and the AN nominal (off scale). The LATB8 band is wall-free, so it extends into the unphysical L2 < 0.*

4. **No forward-rapidity pattern in the residuals.** In all 5 |yll| × 4 ptll windows, data/postfit − 1 is within 1.7σ of zero, and the most forward slice is the quietest (Σr² = 44.1 over 78 bins). Data-stat-only residuals at LATB8, not pulls ([plot](261007-y-shape-first-look/ratio_by_absy_LATB8.png)). [261007-y-shape-first-look]

5. **A non-quadratic shape is below resolution, and Y⁴ is expensive.** Y² is the leading even term of an expansion in ln x, since x_{a,b} = (Q/√s)·e^{±Y}. For MAP22, Y² alone misses L2(Y) by at most 0.0025, which is 20–30× below our σ of the shape and worth ≤ 0.008 σ_NOM. Adding a Y⁴ parameter would change the SCETlib-AD cache layout and fingerprint, so it needs a full cache rebuild plus a new interior-minimum wall: about a week, by code reading. [261007-y-shape-first-look]

## What changed

No code, defaults or cards changed (diagnostic; Luca decided 2026-10-08 against a Y⁴ term). New note `knowledge/20_frameworks/active_wall_face_sensitivity.md`: how to read a POI's slope and the multiplier at an active wall face from the walled covariance alone. The result supports the existing §16c decision in `np_parametrization_constraints.md`.

## Conclusions and open items

The TMD rapidity form needs no new parameter. The NP lever for α_s is the **level** of L2: the floor position and the Λ2 ↔ λ2_ν degeneracy (wall-free ρ = −0.90), carried forward as a systematic question for the nominal. Open, unassigned: a refit with L2(2.5) ≥ 0.05 to confirm −0.17σ_NOM; why σ(δλ2) is 0.0078 here but ≈ 0.002 in the 2026-07/08 2D fits.

<small>Full record: [logbook](https://submit.mit.edu/~lavezzo/alphaS/studies/#tmd-rapidity-shape:logbook) · fitresults on ceph under `alphaS/261007_y_shape_first_look/`</small>
