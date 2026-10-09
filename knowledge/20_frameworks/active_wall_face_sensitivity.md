# Reading a POI's sensitivity to an active wall face from the walled covariance

Source: `studies/tmd-rapidity-shape/261007-y-shape-first-look/` (`scripts/slope.py` → `slope.json`), measured
2026-10-07 on LATB8 (NPDampingWall, τ = 8) against a dedicated wall-free Hessian pass (YNOWALL8).
Last updated: 2026-10-09 (the multiplier under the C² wall default).

## Question it answers

A walled fit (`NPDampingWall` via `-r`, or any relu²/C²-ramp regularizer) sits on an active face c(θ) = 0. Two things you want:

- the **constrained slope** dPOI/dc: how far the POI moves if the face is moved (floor raised/lowered by δ);
- the **multiplier** μ = d(NLL_rest)/dc: how hard the data push on the face, i.e. what releasing it would buy.

Neither needs a new fit, and the slope does not even need a wall-free Hessian pass.

## The identity

Penalty k·relu(−c)², k = e^{2τ} (`fitter.py` multiplies by exp(2τ)). If c is **linear in θ** (gradient g constant),
the wall's Hessian on the active side is exactly 2k·g gᵀ, so H_walled = H_f + 2k·g gᵀ. Sherman–Morrison:

    C_w g = C_f g / (1 + 2k·V_f),     V_f = gᵀ C_f g

Hence the ratio

    dPOI/dc = C(POI, c) / V(c)

is **the same from the walled covariance as from the wall-free one, for any k**. The walled V(c) is tiny (~1/2k:
σ(c) = 2.4e-4 vs 0.143 wall-free at LATB8) but float64 handles it: at LATB8 the two routes agree to 1e-10 relative,
and the vector C·g in shape to 4e-7.

Multiplier, two independent ways:

- from the wall: μ = 2k·|c*|, with c* the (slightly negative) face value at the walled minimum; a relu² wall settles
  past the knee by μ/(2k), ~1e-7…1e-5 at τ = 8, so read c* at full precision. **That formula is relu² only.** The
  `NPDampingWall` is C² by default since 2026-10-08 (`../30_physics_global/np_parametrization_constraints.md` §21):
  then μ = k·P′(|c*|) = k·c*²/d while |c*| < d, and k·(2|c*| − d) beyond, with d the face's ramp width (printed when
  the wall arms). Check: C2A's L2(|Y|=2.5) face at −2.401e-6 GeV², d = 3.15e-6, k = e¹⁶ gives μ = 16.3, the data
  force measured at the relu² fit NOMSTIFF (`studies/constrained-fit-strategy/261008-c2-wall-test`). The slope
  identity above is unaffected: the C² spring is still rank one along g (k·P″·g gᵀ), so the ratio is k-independent;
- from a wall-free pass at the same θ: if the rest's gradient is purely μ·g (single-face stationarity),
  edm_free = ½μ²V_f ⇒ μ = √(2·edm_free / V_f). At LATB8 both give 4.93 GeV⁻² to 1e-9, which is itself the check
  that only one face is active.

Derived numbers (Newton, quadratic approximation):

- releasing the face: Δc = −μ·V_f, ΔPOI = slope·Δc, **Δχ² = μ²·V_f = 2·edm_free** (0.50 at LATB8);
- the wall's trim on σ(POI): σ_w² = σ_f² − C_f(POI,c)²/V_f (the one-sided-boundary effect; ×0.905 at LATB8).

## When it does not apply

- **c nonlinear in θ** (e.g. the B condition, cubic in L₂, or anything in a log/tanh reparametrisation): the wall
  Hessian gains 2k·relu(−c)·∇²c ≈ μ·∇²c, not negligible. The identity is then approximate; use a wall-free
  `--noFit` pass.
- **More than one active face:** use the Woodbury form (projection on the span of the active g's). Check first:
  if μ from the wall and μ from edm disagree, more than one face (or a nonlinear one) is active.
- **"Full release" is a step INTO the forbidden region.** Quote it only as a labelled orientation number; the local
  slope on the physical side is the result. For NP faces the region past the wall is also where the AD cache is not
  validated (`scetlib_ad_cache_validity.md`).

## Wall-free pass, if you want one

LATB8's command with the `-r` regularizer dropped, `--noFit --saveHists --externalPostfit <seed with the walled
vector, no covariance>` (rabbit then recomputes the Hessian), no `--earlyStopping`. One cache load plus the Hessian
(503 s at LATB8); max |Δθ| vs the walled fit = 0. Example: `studies/tmd-rapidity-shape/261007-y-shape-first-look/cmds/YNOWALL8.cmd`.
