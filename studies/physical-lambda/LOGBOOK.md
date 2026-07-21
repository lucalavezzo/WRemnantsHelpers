# Physical-λ enforcement study — logbook

**Goal:** set up the SCETlib NP param-model fit (real-data Z, `260623_Zhistmaker`)
so it robustly allows **only physical (damping) NP λ**, *without* masking genuine
data–model tension. Stay `tanh_2`; add extra terms (`tanh_6`/λ6) only if a
demonstrated need survives.

---

## START HERE (status as of 2026-07-02)

> **ACTIVE NOW (2026-07-02 PM) — testing `wall + λ4_ν=0.01`, and the b0=1 re-fit.**
> (Full state + exact commands: Log entry "2026-07-02 — b0=1 grid + wall+λ4_ν=0.01 fit".)
> - Asimov of the wall+λ4_ν=0.01 config **PASSED** (EDM 2.7e-27, zero bias, λ physical);
>   real fit running. σ(pdfAlphaS) comes from **step 2** (cov), not step 1.
> - **Grid:** use `/scratch/.../wmass` (b0=1, = `_default_btgrid_dir()`), NEVER
>   `/ceph/.../zstuff` (buggy b0=0). The production 0.442 was computed on the buggy grid.
> - **Two open deliverable Qs:** (a) does σ(pdfAlphaS) shift when the λ4_ν-frozen config
>   is re-fit on the FIXED b0=1 grid? (b) the wall+λ4_ν=0.01 σ from step-2 cov — watch
>   conditioning (λ2↔δλ2 ρ≈−1 + active wall).

> **2026-07-02 — σ(αs) OLD-vs-NEW investigation CLOSED (details in Log 07-01/07-02).**
> Chased "why σ(pdfAlphaS) went 0.554 (260611) → 0.442 (260623, λ4_ν-frozen)".
> 1. The base real-data fit's 0.71/0.64 numbers were **off-minimum garbage** (EDM ~98/236;
>    the floating-λ4_ν ρ=−1 degeneracy never converged). The **λ4_ν-frozen fit (0.442,
>    EDM 5.6e-14) is THE number**; always gate σ on `edmval≪1` and drop `--noEDM` from pass-1.
> 2. OLD (0.554) and NEW (0.442) are both converged, but OLD sat at **unphysical, noise-driven
>    λ** (λ4=−0.021<0, perched on the F_eff-cubic divergence cliff at |Y|=2.5), statistically
>    **consistent with NEW within ~1σ** (the individual λ are degenerate, not measured). OLD is
>    NOT a sound reference ⇒ **dropped**. The R/btgrid differences were a red herring.
> 3. **NEW machinery validated vs ground truth (|Y|<2.5, λ_central, all sub-%):** σ_gen vs
>    official SCETlib+DYTurbo **0.07% norm / ~0.1% shape**; σ_gen vs gen MC 0.28%; σ_reco vs
>    nominal 0.145%; λ-response vs Corr[var]/Corr[pdf0] 0.005–0.05%. Plots in
>    `~/public_html/alphaS/260701_np_variation_closure/`.
> **Remaining (deferred):** SCETlib-templates-AT-the-postfit-λ closure — the only NEW-λ-DIRECT
> validation (everything above is near λ_central); safe to extrapolate since NEW λ4=+0.12>0
> (smooth, no cliff). Hacky /tmp scripts (not committed): test1_sensitivity.py, make_inject.py,
> scan_cliff.py.

## Physical-λ resolution (still current)

> **RESOLVED 2026-06-30 (PM): freeze λ4_ν=0 — one flag, no wall (Finding 10).**
> The fix is `--freezeParameters lambda4_nu` and nothing else. Validated end-to-end on
> the real-data frozen refit (`..._lambda4nuFrozen/cov`): (1) **physical** — γ_ν damps,
> σ(qT) negativity back to the λ_central baseline (6.46e-5; the −10.8% qT=0.5 ridge
> gone); (2) **σ(αs) unchanged** — 0.44218→0.4423 (+0.03%), because ρ(αs,λ4_ν)=0.07
> (the conditioning estimate −0.25% agreed); (3) **λ2_ν self-cures to +0.045** (physical,
> +0.37σ) — freezing λ4_ν breaks the ρ=−1 degeneracy, so NO wall is needed. The whole
> soft-wall/reparam debate collapses: freezing the redundant, αs-decoupled λ4_ν is the
> simplest correct fix. (tanh_6 with fixed λ6_ν=7e-4 is a validated alternative that
> keeps λ4_ν floating — for a transportable physical NP function — but not needed here.)
>
> _Earlier framing (now superseded): the deciding inputs (Findings 8–9) showed
> enforcing physicality is statistically free and the negativity is laundered/out-of-
> acceptance, which first suggested "soft wall sufficient." The freeze refit is
> cleaner: it removes the pathology AT THE SOURCE rather than penalizing it._

The investigation has converged on a clear picture; the **one blocking input** is
the postfit **uncertainties + correlation matrix** (Hessian/EDM), which the user
is running. The pending decision is **binary**:

- **(A) keep the soft wall** (`NPDampingWall`, what we have) — fixes the real
  pathology but is fiddly for the degenerate directions; OR
- **(B) hand-rolled positivity reparametrization** in the param model (float `α`,
  use `λ = α²`/softplus per-parameter) — a *hard* guarantee of physical λ, but a
  significant change touching many downstream scripts (the fit basis changes).

**The Hessian σ decides (B)-worth-it:** if σ(λ4_ν) is large / the negativity is
insignificant (expected, given the degeneracy) → the *simple* wall fixing only
λ2_ν likely suffices and (B) isn't worth the blast radius. If the data genuinely
fights physicality (small σ, real Δχ²) → that's real tension to confront.

There is **no cheap middle option**: rabbit's `allowNegativeParam=False` square is
**POI-only** and the λ are POUs → it's a no-op for them (checked, see Finding 7).

---

## Physics: the exact tanh_2 damping conditions (from `btgrid_tf`)

- **CS** `γ_ν^NP(b) = −λ∞_ν·tanh((λ2_ν + λ4_ν·b²)·b²/λ∞_ν)`.
  Damping (γ_ν ≤ 0 ∀b) ⟺ **λ∞_ν>0, λ2_ν≥0, λ4_ν≥0**. λ4_ν is the lone b⁴ term in
  the argument → **no compensation**: λ4_ν<0 ⇒ γ_ν flips to anti-damping (→ +λ∞_ν)
  at large b.
- **TMD** `F_eff = exp(−2λ∞·b·tanh(a))`, `a = (λ2_Y/λ∞)·b + B·b³`,
  `B = [λ4 + λ2_Y³/(3λ∞²)]/λ∞`, `λ2_Y = λ2 + δλ2·Y²`.
  Damping (a ≥ 0 ∀b) ⟺ **λ∞>0, λ2_Y≥0 (small-b turn-on), 3λ∞²λ4 + λ2_Y³ ≥ 0
  (the "cubic", large-b limit)**. λ4 enters F_eff *only* through the cubic, so
  λ4<0 **is allowed** if λ2_Y³ compensates. Evaluate at Y=0 and Y=Y_MAX (λ2_Y is
  monotonic in Y², so the binding |Y| is an endpoint).
- **Why enforce monotone-over-all-b, not just the limits:** with b* + tanh the
  integral never diverges, so "convergence" is *not* the failure mode. The failure
  is **σ(qT) < 0** — the Hankel transform of a non-monotone bT profile dips
  negative — and the qT→ptVGen binning *launders* that out of the σ_gen/σ_reco/NLL,
  so the fit can't see it. Monotone damping ⇒ σ(qT) ≥ 0.

## The wall (`np_damping_wall.NPDampingWall`)

rabbit `Regularizer`; hinge `relu²` on the conditions above, per-side & per-form
(tanh_2/tanh_6), forms+λ-order DERIVED from the registered model
(`indata.scetlib_np_param_model`). Only CLI option is `smallb` (0 drops the
small-b turn-on walls). `Y_MAX`, `LAMBDA_INF_FLOOR`, `NP_DAMPING_MARGIN` are FIXED
module constants (currently `Y_MAX=5`, `margin=0.01` — both UNDER TEST). Hardness
via `--regularizationStrength` τ (penalty × `exp(2τ)`; τ is a fixed multiplier,
not fit). See [[scetlib_np_damping_wall]].

---

## Key findings (2026-06-30)

1. **The free-fit pathology is λ2_ν < 0** (the *leading* CS small-b term; free fit
   λ2_ν = −0.056). λ4_ν is **fine** in the free fit (+0.0019). So λ2_ν<0 is the
   real disease; λ4_ν was never the problem.
2. **The λ are highly correlated / degenerate** — esp. **λ2_ν ↔ λ4_ν
   anti-correlated**: freeze λ4_ν=0 → λ2_ν=+0.045; freeze λ4_ν=0.1 → λ2_ν=−0.1.
   The data pins *combinations*, not individual λ.
3. **The wall fixes λ2_ν≥0 (good) and, via the anti-correlation, drags λ4_ν
   slightly negative** (−0.0003 … −0.004, config-dependent). So **λ4_ν<0 in walled
   fits is a correlation artifact of fixing λ2_ν, NOT an independent data
   preference.**
4. **The soft (relu², finite-τ) wall is fragile for the degenerate directions** —
   they slide to the physical *edge* and the wall fights *noise* (the whole λ4_ν
   saga). The τ/margin/Y knobs interact and have side effects: Y_MAX=5 reshaped
   λ2/δλ2 and dragged λ4_ν *more* negative; the margin meant to lift λ4_ν was
   overwhelmed by the correlation.
5. **Fits converge** — `jac ≈ 1e-8` on the shown params incl. λ4_ν (x[1]); the
   trust-krylov `status 2 "failure to predict improvement"` is **benign/normal**
   for these flat minima (user confirms it's always that). So the postfit λ4_ν is a
   genuine (data+wall) stationary point, not a stall.
6. **σ interpretation:** a large σ(λ4_ν) (expected from the degeneracy) means the
   data does *not* significantly prefer negative → enforcing physicality costs
   ≈0 Δχ² (free). It does NOT make a negative *central* prediction physical — it
   means you can pin it physical at no cost. *Small* σ would mean real data-vs-
   physics tension. So σ = the **cost/significance of enforcing physicality**.
7. **`allowNegativeParam=False` is POI-only** (checked): `get_poi` squares only
   `x[:npoi]`; `get_model_nui` returns POUs unsquared; `set_param_default`
   docstring says so explicitly. The NP λ are all POUs → the flag is a **no-op**.
   The POI-workaround also fails (square is all-or-nothing → would force δλ2≥0;
   POIs entangle blinding offsets + the priors-need-allowNeg constraint). ⇒ robust
   positivity must be **hand-rolled** in the model.
8. **Hessian σ + correlations (DONE — walled τ5/Y5/margin5e-3 `cov2`):**
   λ2_ν=+0.082±**0.127** (+0.6σ), λ4_ν=−0.0037±0.0031 (−1.2σ), λ2=+0.060±0.188,
   **λ4=+0.138±0.059 (+2.4σ, physical — the one genuinely measured λ)**,
   δλ2=−0.0022±0.0075. ρ(λ2_ν,λ4_ν)=**−1.000**, ρ(λ2,δλ2)=**−1.000**,
   ρ(λ2_ν,λ2)=−0.98 → the cov is **near-singular**: data constrains ~2 directions
   (λ4 + one small-b combo); the other λ are wall/start-driven. So free-fit
   λ2_ν=−0.056 is **−0.4σ (noise)** → enforcing physicality costs ≈0. σ(λ2_ν) is
   clean DATA σ (soft wall adds no curvature where the param sits physical), so a
   free-fit Hessian gives σ ≥ this — insignificance is conservative. λ4_ν<0 is the
   ρ=−1 mirror of walling λ2_ν up: the *soft* wall structurally can't hold both
   ends of a perfectly anti-correlated pair (Finding 4, now numerical).
9. **Postfit negativity LOCALIZED (open Q answered):** at the walled postfit,
   γ_ν^NP flips sign (anti-damps) at bT≳5 (→ +λ∞_ν=+2); native σ(Y,qT) is negative
   in 518 cells, neg_area_frac=0.00105 (16× the λ_central 6.4e-5 baseline, but
   below the 1% "bad" flag). It is a **low-qT ridge — every neg cell at qT=0.5 GeV
   — that deepens with |Y|**: −22% of peak at |Y|≈3.75 (worst), −10.8% at the
   |Y|=2.5 acceptance edge. **The binned σ_gen is everywhere POSITIVE (min 1.066)**:
   the qT→ptVGen rebin launders every negative native cell. ⇒ invisible to the αs
   fit, and the deepest part is OUT of acceptance. Real defect for a *physical-NP*
   claim, not for the *binned fit*. Tool: `sigma_gen_at_lambda.py --fitresult`
   (already ran np_physical_report; now also prints neg-cell locations + in/out-
   acceptance split, via new location keys on `spectrum_negativity`).
10. **Freeze λ4_ν=0 is the SOLUTION (validated, `..._lambda4nuFrozen/cov`):** config
    is `--freezeParameters lambda4_nu` ONLY (no wall, no `-r`, no λ6_ν). Results:
    λ2_ν=+0.045±0.121 (physical, self-cured — freezing breaks the ρ=−1 degeneracy),
    λ4=+0.121 (+2.3σ physical), δλ2=−0.012. σ(αs)=**0.4423 vs 0.44218 floating
    (+0.03%)** — confirms freezing doesn't shrink σ(αs) (ρ(αs,λ4_ν)=0.07; conditioning
    predicted −0.25%). Postfit σ(qT)≥0 at the λ_central baseline (neg_area_frac
    6.46e-5; γ_ν damps). So the redundant, αs-decoupled λ4_ν was the lever; pinning
    it = physical at zero cost. **σ(αs)-shrink-from-freezing = ρ(αs,frozen)²/2** is the
    general rule — freeze freely whenever the frozen param is αs-decorrelated.
11. **Alt (validated, NOT needed): fixed λ6_ν via tanh_6 numerator.** tanh_6 adds
    `+λ6_ν·b⁶/λ∞_ν` inside the tanh (`btgrid_tf.py`); damping ⟺ λ2_ν≥0 AND
    (λ4_ν≥0 OR 4λ2_ν·λ6_ν ≥ λ4_ν²). SCETlib's own γ_ν has λ6_ν=7e-4 → tanh_2 (λ6_ν=0)
    DROPPED it; the "λ4_ν≥0" requirement was a tanh_2-truncation artifact. At the walled
    postfit, restoring λ6_ν=7e-4 (λ4_ν=−0.0037 untouched) → physical (neg→baseline).
    Keeps λ4_ν FLOATING (no DOF removed → no σ(αs) shrink), more faithful to SCETlib —
    use IF a transportable physical NP function is the deliverable. Still needs the
    λ2_ν wall (λ6_ν only fixes large-b). `--np-model-nu tanh_6 --lambdas lambda6_nu=7e-4`.

## Run inventory (real-data, `260623_Zhistmaker/..._realdata_<tag>/`)

| config | λ2 | δλ2 | λ4 | λ2_ν | λ4_ν |
|---|---|---|---|---|---|
| free ("Nominal", no wall) | 0.34 | −0.01 | −0.007 | **−0.056** | +0.0019 |
| freeze λ4_ν=0 | 0.05 | −0.01 | 0.12 | 0.045 | 0 (fix) |
| tight τ=5 | 0.044 | −0.007 | 0.137 | 0.093 | −0.0004 |
| tight τ=6 | 0.092 | −0.007 | 0.145 | 0.064 | −0.0003 |
| tight τ=7 | 0.177 | −0.011 | 0.143 | 0 | −0.00017 |
| loose τ=6 (smallb=0) | 0.088 | −0.008 | 0.148 | 0.061 | −0.0032 |
| freeze λ4_ν=0.1 | 0.326 | −0.02 | −0.002 | −0.1 | 0.1 (fix) |
| τ=5, Y=5, margin=5e-3 | 0.060 | −0.002 | 0.138 | 0.082 | −0.0037 |

"tight" = smallb=1; "loose" = smallb=0 (no small-b enforcement). λ4_ν trends → 0
with τ in the tight runs; the worse (−0.003…−0.004) values are the loose / Y=5
configs (correlation-driven). λ_inf, λ_inf_nu frozen throughout; tau5/Y5 run has
the 9-param model (incl. lambda6_nu, inert under tanh_2).

## Open questions

- **(DONE — Finding 8)** σ(λ) + correlation matrix via the post-fit
  straight-through GN Hessian. Ran on the *walled* τ5/Y5 `cov2` (not the free fit),
  but the conclusion is conservative: the soft wall adds no curvature where a param
  sits physical, so σ(λ2_ν)=0.127 is the data's and a free-fit Hessian gives ≥ that.
  ρ(λ2_ν,λ4_ν)=−1.000 as expected; cov near-singular.
- **(ANSWERED — Finding 9)** Yes, λ4_ν<0 pushes σ(qT) negative — but it's a low-qT
  ridge, deepest OUT of acceptance, and **fully laundered** (binned σ_gen all
  positive). So it does not reach the binned fit.
- Free-vs-walled **Δχ²** (true tension number) — not yet measured cleanly (the
  absolute GOF χ² ≈ ndf ≈ 49865 over ~49920 bins is a *good* fit, NOT a penalty;
  the tension is the *difference* between free and walled).
- Y_MAX = acceptance (2.5) vs kinematic ceiling (5)? Decided to TEST 5 (btgrid
  spans ±5 = kinematic ceiling ln(√s/Q)≈4.7–5.4); but Y=5 strongly constrains δλ2
  (pulls −0.021→−0.002) — physical-everywhere vs data-nuisance is a real modeling
  call, not settled.

## Decision / next steps

1. Read the Hessian σ + correlations (the deciding input).
2. **If λ4_ν (etc.) insignificant** (large σ): use the **simple wall** —
   `smallb=1`, Y_MAX=acceptance, **no margin/no Y=5**, moderate τ — which fixes the
   real problem (λ2_ν<0); leave the degenerate λ4/λ4_ν to float (their negativity
   is within σ). Don't over-engineer; don't add tanh_6.
3. **If the data genuinely fights physicality** (small σ, real Δχ²): that's a real
   CS-side tension to investigate (model? data?), not something to wall away.
4. **If a hard guarantee is required**: hand-roll the **positivity reparametrization**
   (CS pair first: λ2_ν=α², λ4_ν=β², exact for γ_ν; TMD via the λ2_Y endpoints +
   the cubic slack). Contain the blast radius by keeping λ as the model's *public*
   interface (fit α internally, propagate to λ + cov). Big change — only if (2)/(3)
   say it's warranted.

## Log

### 2026-07-01 — validating a smaller-than-expected σ on the freeze+wall config

User is running **freeze `lambda4_nu=0` + the NPDampingWall** (the resolved config in
Finding 10 was freeze-ONLY, no wall) and sees σ smaller than expected; LR scan +
Hessian look self-consistent, asking whether to also do Asimov.

Discussed validation plan (nothing run yet):
- **Attribution first:** freeze alone does NOT shrink σ(αs) (Finding 10: +0.03%,
  ρ(αs,λ4_ν)=0.07), so freeze+wall shrinking it ⇒ the **wall** is the suspect. The
  relu² wall only adds curvature when *active* (a λ pushed to the unphysical edge);
  per Finding 6 that regime = "data fighting physicality," so the small σ may be the
  wall importing info the data lacks. Compare σ(αs) across floating / freeze-only /
  freeze+wall; check wall activity via `param_model_diagnostics.py`
  (`np_damping_ok`/`np_physical_report`) — is any λ pinned at the wall edge?
- **Scan+Hessian agreeing** only proves local parabolicity; both carry the wall, so it
  does NOT validate coverage near a boundary (Wilks breaks there).
- **Asimov (yes):** inject the physical frozen-point λ, refit freeze+wall (wall dormant)
  → expected σ. σ_data ≪ σ_Asimov ⇒ data fluctuated to the boundary, wall grabbed it.
- **Toys = arbiter:** `toys_suite.py` — RMS of fitted αs across toys is the frequentist
  σ (no Hessian); pull width ~1 checks coverage directly.
- Open clarification: is the small σ on **αs** (worrying — wall leaking into the
  deliverable) or on a **λ** (expected — that's the wall's job)?

### 2026-07-01 — EDM gate: floating-λ4_ν base fits never converged (σ garbage)

Chased "why does σ(αs) differ across fits?" through a chain and it bottomed out at
**convergence (EDM), not physics/config**. Tool: `io_tools.get_fitresult(fn)["edmval"]`.

Numbers (real-data Z, 260623 unless noted):
| fit | σ(αs) | EDM | verdict |
|---|---|---|---|
| **λ4_ν frozen** (`_lambda4nuFrozen/cov`) | 0.442 | **5.6e-14** | ✅ converged, σ real |
| 260611 freeze (`freeze/cov/..._fixed`) | 0.554 | 1.2e-12 | ✅ converged, σ real |
| base realdata, hessian (`/cov/fitresults`) | 0.710 | **97.8** | ❌ off-min garbage |
| base realdata, impacts (`_impacts`) | 0.638 | **236** | ❌ off-min garbage |

- **The 0.710 vs 0.638 "constraint difference" is not physics.** Both cov jobs load the
  SAME pass-1 external postfit (same code b56a7db9, empty git_diff — param model did NOT
  change; user's hypothesis ruled out) and differ only by `--doImpacts`. The base fit is
  **not at its minimum** (EDM≫1), so `H⁻¹` isn't an uncertainty. `--doImpacts` fires extra
  `loss_val_grad_hess(profile=False)` + bbstat re-profiling → drifts to a *different*
  off-min point (NLL 25014.84 → 25161.70) → different garbage σ.
- **EDM never "got worse."** Pass-1 ran `--noHessian --noEDM` (`edmval=None`) → convergence
  was never measured, only *assumed* from trust-krylov stopping on "failure to predict
  improvement" (a flat-direction stall). The cov job is the FIRST gradient eval → EDM 98.
  Proof it's the same point: pass-1 `nllvalreduced=25014.841532263126` == cov-hessian's
  to every digit, pdfAlphaS=−7.64142 both — yet grad huge ⇒ that point was never stationary.
- **Root cause = floating λ4_ν.** Only structural diff between base (EDM 98) and frozen
  (EDM 5.6e-14) is freezing λ4_ν: the ρ(λ2_ν,λ4_ν)=−1 degeneracy is a flat valley the
  minimizer can't resolve. ⇒ **independent evidence for the freeze-λ4_ν decision**, and
  it CONTRADICTS Finding 5's "status-2 is benign" — for the FLOATING fit, status-2 =
  genuinely unconverged (EDM 100), not a benign flat minimum.
- **The original question (0.554→0.442) is legit** (both EDM~1e-12) → the histmaker/datacard
  rebuild explanation stands (integrated unfolding response + `--quarkMassCorr MiNNLO_Zbb`
  + PDF/αs/MiNNLO-unc-from-corr-by-default; see the histmaker diff below).
- **Rules:** (1) gate every quoted σ on `edmval ≪ 1` (e.g. <1e-6); (2) **drop `--noEDM`
  from pass-1** so convergence is checked at fit time, not assumed; (3) never trust a
  floating-λ4_ν covariance.

### 2026-07-01 (cont.) — the 0.554↔0.442 delta IS the NP→αs coupling; param model was rewritten

Both fits converged (EDM 1.2e-12 / 5.6e-14), identical fit method + frozen/floating set,
so 0.554→0.442 is real and upstream. **NP-group impact decomposition from the saved covs
(read-only, both converged so reliable):**
| | OLD (0.554) | NEW (0.442) |
|---|---|---|
| σ(αs) total | 0.5545 | 0.4423 |
| σ(αs) \| NP-λ frozen (stat+pdf+other) | 0.4386 | 0.4144 |
| **NP-group impact on αs** | **0.339** | **0.155** |
The stat+pdf part barely moves (~6%); **the whole delta is the NP-λ→αs impact collapsing
2.2× (0.34→0.15).** ⇒ NOT data/binning/stats — it's how the NP nuisances couple to αs,
i.e. the response-fold / λ handling.

**Param model was WHOLESALE rewritten OLD→NEW (I was wrong to call it "identical").** The
recorded run-hash `b56a7db9` is unresolvable (`fatal: not a valid object` — the run tree
`main/WRemnants` is deleted), so "same hash" meant nothing. git diffstat over the window:
`param_model.py` ±1334, `lambda_central.py` ±385, `btgrid_tf.py` ±337, new `sigma_gen.py`/
`params.py`/`response_matrix.py`, +4344/−1255. Behavior-affecting commits: **`7201d529`
"read R from the datacard"** (the response-source swap, in code) and **`8e113ea1` "propagate
NP runcard to histmaker meta"** (λ_central now from histmaker meta). So the "cleanup" was
NOT purely behavior-preserving → leading suspect for the NP-impact collapse.

**PDF/αs-from-corrections verification (from setupRabbit args):** NEW `pdfUncFromWeights=False`
+ `asUncFromWeights=False` ⇒ both from corrections ✅. OLD `pdfUncFromCorr=True` ⇒ PDF from
corr ✅, but the αs-source flag didn't exist yet ⇒ αs-source unconfirmed from metadata;
circumstantially fine (the NP-λ-frozen σ, which holds the αs self-constraint, is stable
0.439↔0.414). Clean check = compare the per-unit pdfAlphaS template between the two datacards.

**btgrid:** current default grid `Z_COM13_CT18Z_N3p0LL_btgrid_fineall` (same NAME as OLD's
explicit `btgrid_dir`, relocated /scratch/submit/cms/wmass vs OLD /ceph/.../zstuff) ⇒ same
values, just moved; only `btgrid_tf.py` loader rewritten. Low-priority suspect.

**DECISIVE validation (Luca's idea) = template closure at the postfit λ.** Generate real
SCETlib+DYTurbo at postfit λ_central + small ± steps (small variations ⇒ no negative-σ /
F_eff-blowup pathology — that's the key), fold through the same R, fit morphing templates,
compare σ(αs) + the 0.155 NP-impact to the param model. This tells us if 0.442 is *correct*
(archaeology only says what changed, not which is right). Tooling: `sigma_gen_at_lambda.py`
(`--fitresult` → param-model σ_gen at postfit λ, overlays the official SCETlib prediction —
gen-level, pre-fold); `validation/export_spectrum.py`, `response_matrix.py`. Cheap first
step (no new SCETlib): run `sigma_gen_at_lambda --fitresult <NEW>` (caveat: official hist is
at FranksVals λ, so it's a self-consistency check at postfit, not a full independent closure).
New dev = fresh SCETlib at postfit λ + the reco-fold/template-fit wrapper.

### 2026-07-01 (cont.) — param-model λ-variations VALIDATED on NEW → 0.442 is the real number

Ran `validation/histmaker_validation.py --variation` on the NEW setup (datacard + theory
model = `260623`), comparing param-model `rnorm=σ_reco(λ)/σ_reco(λ_c)` (the R-fold used in
the fit) to the histmaker `Corr[var]/Corr[pdf0]` (nominal reco MC reweighted by each NP
variation of the scetlib_dyturbo correction — `--theoryCorr`-driven, so present despite
`--npUnc none`; confirmed the `vars` axis + λ labels exist in the NEW theory model).

Per-reco-bin double ratio model/hist, yield-weighted |dr−1|:
| var | step | \|dr−1\| |
|---|---|---|
| λ2 | 0.4→1.0 | 0.049% |
| λ4 | 0.4→1.0 | 0.026% |
| λ2_ν | 0.15→0.25 | 0.022% |
| δλ2 | 0→0.02 | 0.005% |
Central reco closure 0.145% yield-wt (only the top ptll bin [37,44] trips 0.5% = known
qT>100 grid truncation). All λ close to <0.05%.

**Conclusion:** the NEW param model's λ-sensitivity reproduces the true MC event-by-event
folding to <0.05% ⇒ the rewrite did NOT break/​inflate the variations; the halved σ(λ) /
collapsed NP-impact is FAITHFUL physics. ⇒ **0.442 is the trustworthy number; OLD 0.554 was
inflated** (its external `260411` response under-folded the λ-variation → too-weak λ-response
→ too-loose λ → inflated NP→αs impact). Answers the turn-1 worry: the smaller σ is CORRECT.
Caveat: only NEW is directly validatable (OLD param-model code is in the deleted `main/WRemnants`
tree); OLD is inferred (NEW matches MC truth, OLD is the outlier). Clean follow-up to make OLD
explicit = pure-histmaker `Corr[var]/Corr[pdf0]` OLD-vs-NEW (no param model, no GPU).

**CORRECTION (2026-07-01, after Luca pushback) — the two ⇒-claims above are TOO STRONG:**
1. The test varies λ around λ_CENTRAL (all positive/physical: λ2 0.4→1.0, λ2_ν 0.15→0.25, …).
   σ in the fit is set by dσ_reco/dλ at the POSTFIT λ, which is OUTSIDE the tested range:
   OLD postfit (λ2=0.48, λ4=**−0.02**, λ2_ν=**−0.11**), NEW postfit (λ2=**0.05**, λ4=0.12,
   λ2_ν=0.045). So the test validates the MACHINERY near λ_central; it does NOT validate σ,
   and "0.442 validated" is too strong.
2. "OLD inflated" is UNPROVEN — the test says nothing about OLD; OLD was likely validated at its
   own λ_central too. The σ difference may be a real SETUP difference, not an OLD bug.
3. OLD can't be re-validated with current code: OLD datacard built WITHOUT `--storeResponseMatrix`
   (R came via external `unfolding_hdf5_path`); current code reads R only from the datacard
   (7201d529) and the external-R path was removed → can't construct the model from OLD.

**OPEN leading hypothesis (Luca's): the σ diff is driven by the different POSTFIT λ location.**
Nonlinear tanh/b* forms ⇒ dσ/dλ depends on where you sit (λ2_ν even flips sign −0.11→+0.045),
entangled with R (J = R·dσ_gen/dλ). **Clean test:** with FIXED NEW machinery, compute the
param-model λ-sensitivity (dσ_reco/dλ or rnorm slope) at OLD-λ vs NEW-λ — isolates location from
machinery, no fit, no off-minimum trap. Literal "inject OLD λ + --noFit" works but is off-minimum
(fix λ, re-profile the rest, then read curvature). Deepest = SCETlib template closure AT the postfit λ.
Plots: `~/public_html/alphaS/260701_np_variation_closure/` (central ptll/yll + per-λ response).
Run cmd in `/tmp/histmaker_validation_NEW*.log`; btgrid = `/ceph/.../zstuff/...fineall` (script
default = OLD's explicit path; NEW-fit-inherited grid differs in file count 11 vs 6 — rerun with
`/scratch/.../wmass/...` if a grid mismatch is suspected, but central 0.145% closure says it's fine).

### 2026-07-01 (cont.) — RAN Tests 1&2; found F_eff divergence CLIFF at OLD-λ; DECIDED to drop OLD

/tmp scripts (no repo mod), current tree 948a94ac (OLD ran on deleted main/WRemnants @ b56a7db9):
- **Integration range (Luca's Q):** GEN absYVGen ∈ [0,**2.5**] (10), ptVGen ∈ [0,100] (21); RECO
  yll ∈ [−2.5,2.5] (20), ptll ∈ [0,44] (**39**). High-|Y|>2.5 excluded from the fold.
- **σ_reco(OLD-λ) folded/fit-level is ALL POSITIVE** (min 0.96, 0/49920 neg). The negative σ_gen in
  Luca's `sigma_gen_at_lambda` fine plot (dσ_gen/dptV: +68,−75,+102 low-qT, |Y|<2.5) is laundered
  by the gen→reco fold + |Y|≤2.5.
- **scan_cliff.py: σ_reco has a real CLIFF (~1e45, in yll bin 19 = |Y|≈2.5 edge).** λ2≲0.467 or
  λ4≲−0.0225 → explode; above → normal. **OLD (λ2=0.479, λ4=−0.0207) sits ~0.012 / ~0.002 ABOVE
  the lip.** Test1 δ=0.01 down-step crossed it (1e46 "Jacobian"); **Test 2 (rabbit GN Hessian at
  OLD-λ) CRASHED non-positive-definite** (Cholesky). Test 2 froze the RIGHT λ (same as NEW: floats
  {λ2,λ4,λ2_ν,δλ2}); same freeze at NEW-λ converges ⇒ crash is the λ-location/cliff, not freezing.
- **Mechanism (confirmed by yll=19):** B=[λ4+λ2_Y³/(3λ∞²)]/λ∞; **B<0 at |Y|=2.5 ⇒ a<0 at large b ⇒
  tanh→−1 ⇒ F_eff=exp(+2λ∞b) GROWS ⇒ b-integral explodes** (capped by b_max). λ2,λ4,δλ2 feed B
  (cliff); λ2_ν CS-side (stable, ratio 1.003). **Cliff exists ONLY for λ4<0.** NEW λ4=+0.121>0 ⇒
  B>0 ⇒ no cliff ⇒ robust. OLD λ4<0 ⇒ on the lip.
- **"Why crash now / worked before":** OLD's Hessian (PD, σ=0.554) was the deleted pre-rewrite
  machinery; current machinery has the divergence ~0.01 from OLD-λ. Same λ, different code ⇒ Tests
  1&2 are CONFOUNDED (current machinery can't judge OLD's number). NOT proven: regression vs
  form-genuinely-diverges (SHELVED — low value once we drop OLD). R/btgrid diffs are a RED HERRING
  (Luca): the cliff is a λ4<0 FORM feature, machinery-independent in origin.
- **GEN-level closure (Luca asked):** σ_gen (bt-integral, NO R) vs gen MC truth (histmaker,
  260519 FranksVals gen file) = **0.28% yield-wt**, per-bin ≤0.5% (ptV proj), worst 1.4%, 210 gen
  bins (ptV×|Y|<2.5), at λ_central. Plot `260701_np_variation_closure/hist_comp_gen.png`.

**DECISION (Luca, 2026-07-01): STOP validating against OLD.** Its postfit λ4<0 sits on the F_eff
divergence cliff at unphysical λ ⇒ 0.554 is the curvature of a model on the edge of divergence, not
a sound reference. **Focus: validate NEW against ground truth (SCETlib / SCETlib-corrected
histmaker).** Status (all near λ_central, sub-%): σ_gen-vs-gen-MC 0.28%, σ_reco-central 0.145%,
λ-variation-vs-Corr 0.005–0.05%. **Remaining airtight test = SCETlib templates AT the NEW postfit λ**
(λ2=0.05, λ4=+0.12 are BELOW the histmaker's tested variation range; NEW is in the smooth λ4>0
region so fidelity extrapolates, but the σ at the postfit point is not yet directly validated).

### 2026-07-02 — official-prediction closure + "how did OLD land unphysical" answered

- **σ_gen vs official SCETlib+DYTurbo** (`sigma_gen_at_lambda.py --theory-corr
  .../scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksVals_CT18Z_N3p0LL_N2LO_CorrZ.pkl.lz4
  --meta-from <NEW dc> --btgrid <zstuff> --plot-axis ptVGen [--absy-edges 0,2.5]`), var=pdf0,
  λ_central: **|Y|<2.5 → Σmodel/Σcorr=0.99933 (0.07% norm), per-bin 0.9925–1.0018 (~0.1%)**;
  |Y|<5 → 0.985 (1.5% norm, ~1% shape). ⇒ the 1.5% is ENTIRELY high-|Y| (2.5–5, outside the fit,
  where bt-grid is least precise); inside acceptance the bt-integral matches the official
  prediction to ~0.1%. Note: `--meta-from` did NOT override the gen grid (fell back to built-in
  40×[0,40]×1); `--absy-edges` does restrict |Y|. Plots `official_closure_ptv{,_absy2p5}.png`.
  (Norm offset is fit-irrelevant anyway — the analysis fits shapes with floating normalization.)
- **"How did OLD land on unphysical λ with ~everything the same?"** Because it DIDN'T really —
  OLD vs NEW postfit λ are statistically consistent: δλ2 identical; λ2 0.9σ; λ2_ν 0.6σ; λ4 1.2σ(OLD)
  /2.7σ(NEW) (λ4 the one genuinely tighter+physical in NEW). The individual λ are near-perfectly
  degenerate (ρ(λ2_ν,λ4)≈−1, ρ(λ2,δλ2)≈−1) ⇒ data pins only ~2 combos, not the 4 λ ⇒ the
  individual values are noise on flat directions. A ~1σ fluctuation + flat valley + start/λ_central
  tips them to the physical or unphysical side; OLD's landed slightly negative (λ4<0 → cliff),
  NEW's slightly positive. Not a mechanism/machinery effect — the fit simply does not determine
  the individual λ (⇒ the whole reason to enforce physicality).

_Histmaker diff (for the 0.554↔0.442 real difference):_ OLD `260611` theory model
(7.01 GB, histmaker git ab0aba9d) vs NEW `260623` (7.50 GB, git 563a5b2b) — NEW adds
`--unfolding --poiAsNoi --unfoldingAxes ptVGen absYVGen helicitySig --unfoldingInclusive`
(integrated gen-level response matrix; OLD used the external `260411_histmaker_dilepton_unfolding`
via `unfolding_hdf5_path`) and `--quarkMassCorr MiNNLO_Zbb`. Datacard: OLD `--pdfUncFromCorr`
+ `--npUnc LatticeNoConstraintsFranks`; NEW corrections-by-default (commit cc0d216d7,
Jun 16) + `--npUnc none`. `^scetlibNP.*` matches 0 params in both; floating set
`{λ2,λ4,λ2_ν}` identical.

### 2026-07-02 — b0=1 grid + wall+λ4_ν=0.01 fit (pre-compaction snapshot)

**b0=1 grid (touches the deliverable).** The production σ(αs)=0.442 (`260623 …_lambda4nuFrozen`)
was computed on the **BUGGY b0=0** btgrid — that fit ran Jun 24 08:39→13:56, BEFORE the b0=1
fix was swapped into the production path `/scratch/submit/cms/wmass/scetlib_np/Z_COM13_CT18Z_N3p0LL_btgrid_fineall/`
(Jun 24 20:50; old grid kept as `.b0nu0_OLD_PREFIX`). Fixed grid VERIFIED b0=1
(`config['Nonperturbative']['b0_over_bmax_nu']=1`), closes σ_gen vs the official theory-corr to
**0.07%** (|Y|<2.5, no wiggle). The fit's `_default_btgrid_dir()` now points at the fixed grid, so
a re-run today is correct. ⇒ **OPEN: re-fit the λ4_ν-frozen config on the fixed grid; does 0.442 shift?**
(Full grid story in [[btgrid-precision]]; the low-qT wiggle I "rediscovered" this session was that
known bug, hit because I used the buggy `/ceph/.../zstuff` grid by mistake.)

**New config under test: wall (τ=5) + λ4_ν=0.01 fixed.** Verified two-pass recipe:
- Set λ4_ν=0.01: param-model kwarg **`xparam_default=lambda4_nu=0.01`** (parsed via `parse_args`
  split("=",1)) + `--freezeParameters lambda4_nu` pins it. Floating (walled): λ2, λ4, λ2_ν, δλ2.
- Wall: **`-r wremnants.postprocessing.scetlib_np.np_damping_wall.NPDampingWall
  wremnants.postprocessing.scetlib_np.np_damping_wall.NPDampingMapping --regularizationStrength 5`**
  (needs BOTH the Wall + Mapping class; `smallb` defaults 1).
- **Step 1 (minimize):** `-t <mode> --noHessian` — **NO** `hessian_straightthrough`/`hessian_gn`
  (those are STEP-2 ONLY; can't be used with --noHessian). Drop `--noEDM` so EDM is computed
  (hessian-free CG). Step-1's POI/NOI σ is UNRELIABLE (no straight-through in step 1) —
  **σ(pdfAlphaS)=NaN here is EXPECTED, not an error**; the real σ is a step-2 deliverable.
- **Step 2 (cov):** `--externalPostfit <step1> --noFit` **WITH** `hessian_straightthrough=1 hessian_gn=1`
  → real σ(pdfAlphaS) + full cov (GN exact for Asimov). Match `-t` to step 1 (Asimov step-2 needs `-t -1`).

**Asimov result** (`260702_l4nu0p01_walled/fitresults.hdf5`, `-t -1`, step 1): **EDM=2.7e-27**
(perfect — the wall+fix config has no convergence pathology), **postfit=prefit EXACTLY** (zero bias:
αs & λ recover truth), λ4_ν=0.01 pinned, λ2_ν=0.15±0.11, all λ physical. σ(pdfAlphaS)=NaN (step-1
CG limitation above). ⇒ config VALIDATES on Asimov; get σ from step 2.

**OPEN / next:** (a) step-2 cov on the Asimov → expected σ(pdfAlphaS), **watch conditioning**
(λ4_ν fixed breaks ρ(λ2_ν,λ4_ν)=−1, but λ2↔δλ2 ρ≈−1 + active wall could still make σ near-singular);
(b) real fit step-1→step-2; (c) the b0=1 re-fit of the frozen config.

**Machinery banked this session:** the matching is IDENTICAL to `make_theory_corr` /
`read_matched_scetlib_hist` (resum ⊕ (DYTurbo−SCETlib_singular), zero nonsingular below qt_cutoff);
the disagreement was the b0_nu bug, NOT matching/sampling; 3-node Simpson rebin is sufficient for the
fit (5-node → 0.007% vs 3-node 0.045%, unneeded; only in point-mode, no bt-grid 5pt exists); bt-grid
σ_gen validated to 0.07% vs the official prediction (|Y|<2.5). Validation scripts had hardcoded btgrid
paths (6 pointed at the buggy grid) — refactored to `_default_btgrid_dir()` + datacard/histmaker
required (uncommitted on `scetlib-np-param-model`). Validation-script reorg parked: see
[[scetlib-np-validation-reorg]] handoff.

### 2026-07-02 — real-data wall+λ4_ν=0.01 result + CANDIDATE FITS (ideas)

**Real-data result** (`260702_l4nu0p01_walled/fitresults_t0.hdf5`, step-1 `-t 0 --noHessian`):
EDM=**6.35e-13** (converged; the earlier "hang" was just the ill-conditioned step-1 EDM CG
finishing slowly — the minimize was done at 2321s). postfit: pdfAlphaS=−8.610, λ2=0.136,
λ4=0.101, **λ2_ν=0.0046 (σ=0.0047)**, δλ2=−0.0053, λ4_ν=0.010(fix). σ(pdfAlphaS)=NaN (step-1
CG; only λ2_ν's row solved). **Reproduces a prior freeze-λ4_ν=0.01 + regularization fit → stable.**
KEY (DEFENSIBLE — central value only): **λ2_ν landed pinned at the physical boundary (≈0)**,
while the free fit wants **λ2_ν<0** (via ρ(λ2_ν,λ4_ν)≈−1 with λ4_ν=+0.01 fixed). So the τ=5
(hard, e^{2τ}≈2.2e4) wall is **ACTIVE** — holding λ2_ν off the data's preference. This is read
from the POINT ESTIMATE, which is trustworthy.
CORRECTION (was overstated as a finding — now a HYPOTHESIS): the "σ(λ2_ν)=0.0047, 25× below free"
is NOT evidence the wall over-constrains σ(αs). (i) That 0.0047 is a step-1 `--noHessian` CG byproduct
(only λ2_ν's row solved, σ(pdfAlphaS)=NaN) — not a real Hessian error, so the "25× below free 0.12"
is apples-to-oranges (0.12 IS a proper Hessian error). (ii) A symmetric ± is meaningless at an active
one-sided boundary anyway (curvature is one-sided → need MINOS/asymmetric). (iii) σ(λ2_ν) is a nuisance,
not σ(αs) — the quantity we care about. Whether the active wall SHRINKS σ(αs) is UNPROVEN and needs P1.
CONFOUND for P1: fixing λ4_ν=0.01 *by itself* breaks ρ(λ2_ν,λ4_ν)=−1 and would shrink σ(αs) with OR
without the wall — so even σ(αs)<0.442 at step-2 does NOT implicate the wall. Must compare against
{λ4_ν=0.01 fixed, wall OFF} to attribute.

**Candidate fits to run (prioritized by NEW decision-relevant info). Each = step-2 cov + toys
(Asimov+toy); use `--noEDM` in step-1 to dodge the CG hang; gate on edmval≪1.**
1. **[P1] Wall's effect on σ(αs) — the attribution matrix** {λ4_ν=0, 0.01} × {wall off, on}:
   - have: freeze λ4_ν=0, no wall → **σ=0.442**; λ4_ν=0.01 + wall → current (σ from step-2).
   - RUN: **λ4_ν=0.01 fixed, wall OFF** (drop `-r`). Compare σ(pdfAlphaS).
   - Read: σ(αs) stable across all ⇒ wall is COSMETIC (only enforces λ2_ν≥0), 0.442 robust.
     wall-on < wall-off ⇒ wall IMPORTS info ⇒ use freeze, not wall. (wall-off lets λ2_ν go ~−0.05,
     unphysical — fine, we're measuring σ(αs) not physicality.)
2. **[P2] NP-truncation systematic — tanh_6 / λ6_ν.** `--np-model-nu tanh_6` with **λ6_ν=7e-4
   fixed** (SCETlib's own value; relaxes the F_eff cubic that caused the cliff → more faithful).
   The σ(αs)/central shift vs tanh_2 = the NP-order systematic for the αs result. Optionally also
   float λ6_ν (walled) to confirm the data doesn't constrain it. Could bundle λ6 (TMD b⁶) similarly.
3. **[skip/confirm-only] wall + λ4_ν FLOATING** — already explored (the fragile soft-wall config
   the study left for the freeze); no new info unless re-demonstrating the fragility.

Decision framework: these build (a) σ(αs) robustness + wall attribution (P1), and (b) the NP-order
systematic (P2). The resolved central config is still freeze-λ4_ν=0 no-wall (Finding 10); these
stress-test around it. Note b0=1 grid caveat: re-fit the frozen config on the fixed grid too (0.442
used the buggy b0=0 grid — see the b0=1 Log entry).

### 2026-07-02 — RESULTS: σ(αs) resolved + muonCalibration anomaly (λ↔muon degeneracy REFUTED)

Read all fitresults directly with h5py + `wums.ioutils.pickle_load_h5py` on the login node (no
container needed): `results*/parms` (hist: value+variance), `cov`, `impacts_grouped`. Reader recipe
banked. **UNITS: raw parms σ(pdfAlphaS) = 0.553 (Asim-nom) / 0.429 (data) / 0.473 (Asim@data-λ) —
these are ~½ the "1.11/0.88" quoted verbally but MATCH the older 0.554/0.442; 1.11/0.88 were a doubled
convention. Work in the raw σ / ratios.**

**σ(αs) question RESOLVED.** Asim@data-λ (0.473) sits between Asim-nom (0.553) and data (0.429) ⇒ the
λ *location* explains ~65% of the Asim→data drop. Mechanism from grouped impacts: the NP form-factor
impact on αs COLLAPSES when λ2_ν is pinned — resumNonpert 0.317→0.138→0.106, scetlibNPFeff
0.307→0.132→0.100, scetlibNPgammaNu 0.076→0.005→0.004 (nom→@data-λ→data). CAVEAT: Asim@data-λ edm=4.9e-3
(NOT machine-zero like nom's 1e-28; wall-kink/slightly off-min) ⇒ treat 0.473 as approximate. The
residual 0.473→0.429 (~10%) is non-λ (experimental) + the edm slop.

**muonCalibration ANOMALY (Luca flagged; never seen this high before).** Group impact on αs:
0.029 (Asim-nom) / 0.026 (Asim@data-λ) / **0.267 (data)** — a ~10× jump, DATA ONLY. Group = 216
`Scale_correction_*` + `Resolution_correction_*` (+ pixel_multiplicity). Diagnostics:
- NOT a conditioning artifact: cond#(C_GG)≈84 both; conditional-impact only ×1.5 above quadrature sum.
- Real but modest pulls in data: RMS 0.31σ over 216 (only 1 >1σ, max 1.41); all 0 in Asimov.
- **The ×10 jump lives in C[αs, muon-scale]** — αs is ~10× more covariant with the scale field in data.
- Real-DATA effect: BOTH Asimovs tiny (incl. NP-pinned Asim@data-λ) ⇒ needs a real spectral feature;
  not caused by the NP-wall config.
**Luca's λ↔muon degeneracy hypothesis ("λ pulled weird, muons compensate") — REFUTED.** Partialling the
4 λ out of the cov: muon→αs impact 0.207 → 0.192 = **93% survives** freezing λ. And muon→λ impacts are
negligible (≤0.006; 0.000 on λ2_ν). corr(αs,λ2_ν)=0.009. ⇒ αs↔muon coupling is **DIRECT**, not routed
through the NP λ. Suspicion moves OFF the NP model, ONTO the **angular observables** (cosθ*/φ* are built
from muon momenta → muon scale, and carry αs/pt info → direct αs↔muon channel absent in ptll/mll-only).
Nuance: freezing *current* λ ≠ testing whether *richer/old* NP would absorb the feature (config C probes
that). CONCERN: αs is blinded and directly entangled with a data-driven muon-scale pull → possible bias.
**Next tests (sharpest first):** (1) drop angular observables (ptll/yll only) — does the αs↔muon coupling
vanish? (2) config C (NP off) — predicted to barely move muonCal if NP-independent; if it drops, richer
NP absorbs the feature. (3) diff observables vs the older-NP-model data fit.

### 2026-07-02 — SANS-WALL comparison: wall & NP both INNOCENT for muons; λ2_ν error is asymmetric

Compared the walled data fit (l4nu=0.01+wall) vs the **sans-wall** data fit
(`...realdata_lambda4nuFrozen/cov/fitresults.hdf5`, λ4_ν frozen=0, NO wall, edm 5.6e-14, σ(αs)=0.442):
| | WALLED | SANS-WALL |
|---|---|---|
| σ(αs) | 0.4293 | 0.4423 |
| λ2_ν | +0.0046±0.0048 (pinned) | **+0.0450±0.1211 (free, PHYSICAL)** |
| muonCal impact on αs | 0.2073 | 0.2312 |
| muon pulls (RMS/max) | 0.31/1.41 | 0.31/1.41 (IDENTICAL: unc48=−1.41,unc29≈−0.97…) |
| corr(αs,λ2_ν) | +0.009 | +0.262 |

**muonCal blow-up is UPSTREAM, not wall/NP.** Impact ~identical (0.21 vs 0.23) and the muon pulls are
identical to 2 decimals whether λ2_ν is pinned or free → the muon scale chases a feature **orthogonal to
the NP** (a momentum-scale-shaped feature baked into the 260623 histmaker: prediction+data+calibration).
Richer NP won't relieve it (config C will look the same). Muons are NOT pulled weirdly (RMS 0.31σ, 1/216
>1σ, max 1.41σ) — the big *impact* is collective correlation of mild pulls with αs, not wild pulls.
Suspects: muon-calibration inputs or a data/MC scale mismatch in 260623. **Angular obs are NOT new (Luca
uses them routinely)** — so not the cause. NEXT: diff vs a pre-260623 data fit (muonCal impact + pulls +
theoryCorr/calibration in meta). CONCERN: αs blinded & directly entangled with this scale pull → bias risk.

**Wall IS in rabbit's Hessian (resolves the `-r`-in-Hessian question).** Proof: turning the wall on
shrinks σ(λ2_ν) 0.12→0.005 and collapses corr(αs,λ2_ν) 0.262→0.009 — only a Hessian-level term does that.

**Walled σ(λ2_ν)=0.0048 is a MISLEADING symmetric error (Luca spotted).** One-sided wall → asymmetric
profile: down-side stiff (relu² wall), up-side shallow (data) once past the boundary. Symmetric Hessian
reports only the stiff side. True interval ≈ **+0.12/−0.005** ⟹ λ2_ν∈~[0,0.12], = the sans-wall
(+0.045±0.12) folded at the boundary. Generic Hessian-at-boundary failure, not a rabbit bug; use
`asym_impacts` (contour) or a λ2_ν scan for the real interval. **CORRECTION (Luca pushed; I was wrong
to call it "benign"): the wall DOES tighten σ(αs), by ~3%, and the reported symmetric value UNDER-states
the truth.** Direct proof via conditional σ within a single fit: SANS-WALL σ(αs) 0.4423 (free) → 0.4269
(λ2_ν FIXED); WALLED marginal = 0.4293 ≈ the λ2_ν-fixed value, and fixing λ2_ν in the walled fit changes
nothing (already frozen by the wall). ⟹ **the wall ACTS LIKE fixing λ2_ν**, shrinking σ(αs) ~3.5%. Because
the wall is one-sided, the symmetric σ(αs)=0.429 is the λ2_ν-*pinned* side; the honest (λ2_ν free to float
up) value is ~0.442 — reported value under-states σ(αs) by ~3% (direction = looks more precise than honest).
So the turn-1 "wall over-constrains σ(αs)" worry is REAL but small (~3%). (all-4-λ fixed floor: 0.414–0.416.)
PRACTICAL: honest σ(αs) = the λ2_ν-free value (~0.442); the λ4_ν=0 no-wall fit already has λ2_ν physical
(+0.045) so needs no wall — that config (0.442) is both physical AND honest. Config C = honest σ for λ4_ν=0.01.
**Does the wall affect the ASIMOV σ? Only if the Asimov sits against it** (Asimov-vs-data is irrelevant; LOCATION
is what matters — the wall is one-sided, dormant in the bulk, bites only at the boundary). Demonstrated:
Asimov NOMINAL (λ2_ν=0.15, physical) → λ2_ν FREE (σ 0.11), fixing it moves σ(αs) 0.553→0.548 (−1%), wall
DORMANT ⟹ 0.553 is wall-free. Asimov@data-λ (λ2_ν≈0.005, boundary) → λ2_ν stiff (σ 0.005), fixing it moves
σ(αs) 0.473→0.473 (0%), wall ALREADY active ⟹ tightened like data. ⟹ real data wants λ2_ν<0 → pushed to
boundary → wall active → ~3% tighter; a nominal-truth Asimov would NOT show this (reports wall-free expected σ).
**LIKELIHOOD SCAN of pdfAlphaS (Luca ran it; `..._tau5_margin5em3_Y5_lambda4nuFrozen0p01/fitresults_scanPdfAlphaS.hdf5`,
--scanRange 1.5 --scanRangeUsePrefit --scanPoints 15; SAME config: Hessian σ=0.4293, λ2_ν=0.0046±0.0048).**
Curve = clean SYMMETRIC parabola (2ΔNLL: ±1→0.25, ±3→2.28, ±5→6.36, ±7→12.4; step=0.214 prefit-σ/idx).
1σ crossings −1.984/+1.987 idx → **σ(αs)≈0.426, SYMMETRIC, matches Hessian 0.429 to ~1%.** ⟹ **For αs the
Hessian is RELIABLE — NO boundary asymmetry** (corrects my earlier over-worry that σ(αs) was mis-estimated).
Reason: corr(αs,λ2_ν)=0.009 at the walled min ⟹ scanning αs profiles λ2_ν but it stays pinned, doesn't drag
αs. So the boundary asymmetry is CONFINED to λ2_ν's own error (real, +0.12/−0.005); αs is clean. The ~3%
(0.429 walled vs 0.442 sans-wall) is NOT a Hessian error — it's the legit wall-on(λ2_ν≥0 prior) vs wall-off
choice, correctly computed both ways. ⟹ real σ(αs) = 0.426 WITH wall (scan-validated) or 0.442 WITHOUT.
(contourScan file had no results — MINOS didn't complete; the 1D scan suffices.) HOW-TO for asymmetric errors:
`--scan <poi> --scanRange<N> --scanRangeUsePrefit --scanPoints<M>` then 2ΔNLL=1 crossings; or `--contourScan`.

### 2026-07-02 — Asimov-vs-data σ(αs) (1.11 vs 0.88): the diagnostic test + blinding correction

**Question:** why does Asimov σ(pdfAlphaS)=1.11 > data 0.88? In pure Gauss-Newton (step-2 uses
`hessian_gn=1`), the Hessian JᵀV⁻¹J depends **only on the postfit LOCATION**, not on the observed
data. So the two are just f(θ at nominal)=1.11 vs f(θ at data-postfit)=0.88 — both endpoints already
known (data step-2 IS the full-location σ). Injecting ALL postfits into an Asimov just returns 0.88
(redundant). The useful move is **incremental attribution**: inject a subset and see which coordinate
drops σ.
**Blinding correction (I had this wrong):** the αs pull (≈−8.61) is a **name-seeded constant blinding
offset**, NOT a physical location — same across every fit; the theory is evaluated near the true
(~nominal) αs. So (a) do NOT inject −8.61; (b) σ(αs) is unblinded (offset shifts center not width) →
ALL our σ comparisons are valid; (c) central-value deltas between fits are comparable, absolute hidden.
Recorded in `knowledge/20_frameworks/nominal_workflow.md`.
**Consequence — sharpens the running test (Asimov @ data-postfit λ, WALL OFF):** with αs ~nominal in
both fits and experimental systs near-linear, **the λ location is the ONLY substantial nonlinear
coordinate** ⇒ λ-only injection should reproduce ~the ENTIRE 1.11→0.88 gap in GN (attribution AND
validation in one). Read: **λ-only ≈ 0.88** ⇒ fully understood (drop = λ *location*; wall only
*relocated* λ2_ν there, didn't add curvature). **λ-only ≠ 0.88** ⇒ red flag: residual = wall's own
curvature (if `-r` enters the Hessian & active) OR a boundary/conditioning artifact in the data 0.88
⇒ finish the `-r`-in-Hessian code check. NOTE: `-t -1 --noHessian` is step-1 only (σ=NaN); needs step-2
`--externalPostfit … --noFit hessian_straightthrough=1 hessian_gn=1 -t -1` for σ.
**Traditional vs global impacts (from rabbit source):** traditional = postfit-cov decomposition
("fix-and-shift" / "conditional uncertainty", uses *postfit* nuisance σ); global = "shifted global
observable" (arXiv:2307.04007, uses *prefit* input σ + data-stat). Both implemented variants are
**Gaussian** (the fully-nonlinear shift-and-refit one is TODO/unimplemented) ⇒ **global won't separate
wall-vs-nonlinearity either**, and it re-diffs yields (flaky w/ param model). Don't bother running
global for this question.

### 2026-07-02 — saturated ptll-projection test: flags trap

Ran `--externalPostfit fitresults_t0.hdf5 -m Project ch0 ptll --computeSaturatedProjectionTests`
on `260702_l4nu0p01_walled` — log showed `nit: 0, success: False, status: 2` and only ONE
"Saturated chi2" block (ndof 49912, p=54.88%). Two separate things (from rabbit source):
1. **`nit: 0` is expected, not the failure.** Without `--noFit`, the minimizer still runs but
   starts at the loaded (already-converged) t0 point; gradient ≈1e-7, trust-krylov can't predict
   improvement → exits at iteration 0 with a scary-but-harmless status 2 (~330 s of Hessian-vector
   products wasted). Add `--noFit`.
2. **The projection test never ran.** It lives inside `save_hists` (`rabbit_fit.py:397-466`),
   which is only called with `--saveHists` — without it, `-m Project … --computeSaturatedProjectionTests`
   is silently ignored. The printed "Saturated chi2" (ndof 49912 = 49920 bins − nparams −
   nsystnoconstraint, `rabbit_fit.py:671`) is the always-printed GLOBAL full-channel test, easy to
   mistake for the projection one (which would print ndof = 39 ptll bins).
   Caveat: with `--noHessian`, `--saveHists` must be paired with `--noChi2` (linear χ² needs the
   covariance; the saturated ΔNLL test doesn't). The projection test runs its own real minimization
   (composite model + 39 saturated params; walls/`tau` are carried over into it).
   **Fix:** rerun adding `--saveHists --noChi2 --noFit`.

### 2026-07-03 — np_function_plots: fitresult mode was drawing the CARD form, not the FIT form

Plotting `260702_2D_l6nu0p01_l60p01` (tanh_6/tanh_6 numerator override, λ6=λ6_ν=0.01 frozen)
dropped λ6/λ6_ν from the parameter insets — and, worse, drew the curves with `tanh_2`:
`fitresult_lambdas._resolve_models` took `np_model`/`np_model_nu` from `lambda_central`
(histmaker metadata = the card-locked DENOMINATOR form), blind to the `np_model_(nu_)fit`
numerator override. So any override fit plotted the wrong form factor (λ6 b⁶ term silently
absent), not just a cosmetic legend gap.

**Fix (WRemnants, `scetlib-np-param-model` tree):** the override tokens are recoverable
offline from `meta_info.args["paramModel"]` in the fitresults HDF5 (rabbit stores the parsed
argparse args). New `_fit_form_overrides()` reads them; `_resolve_models` now layers
explicit args > fit override > card form > defaults, mirroring `param_model`
(`np_model_fit or core.np_model`). Also made the plotter's `--np-model/--np-model-nu`
actually reach fitresult mode (defaults now None; raw mode falls back to tanh_2 as before).
Regenerated `~/public_html/alphaS/260703_np_functions/lambda6_2D.png`: both insets show
λ6=+0.01, `model: tanh_6`; regression on raw mode (inert-λ6 hard error under tanh_2) and the
`fitresult_lambdas` CLI table pass. No toy band on this plot — the fit was `--noHessian`
(no `cov`), expected.

**Same hole in `sigma_gen_at_lambda`, fixed too.** Its `--fitresult` pulled only the postfit
λ VALUES; the evaluation form came from the base tune (canonical/card `tanh_2`), so λ6 was
inert AND the tune was evaluated at an unphysical point. A/B on `260702_2D_l6nu0p01_l60p01`:
under the correct `tanh_6` eval Σσ_gen=1699.2 (all bins positive); forcing `tanh_2` gives
Σσ_gen≈−7e45 — the known λ4<0 F_eff runaway (absY default bin reaches Y=5) — i.e. the
pre-fix output for this fit was catastrophic garbage, not a subtle bias. Fix: `--fitresult`
now (a) defaults `--meta-from` to the fitresults (base/construction = card λ_central from its
metadata), (b) reads `np_model_(nu_)fit` via `_fit_form_overrides` and passes them as the
EVALUATION forms to `core.sigma_gen(..., np_model=, np_model_nu=)` — construction stays at
the card form, exactly param_model's denominator/numerator split. Explicit
`--np-model(-nu)` still wins. `validate_agreement` checked: no `--fitresult` mode, validates
at card λ_central where the card form is correct by design — no change needed.

### 2026-07-03 — "σ=−3.5e47 at qT=75" in sigma_gen_at_lambda's validity block: THIRD instance of the card-vs-fit form hole (diagnostics), NOT a physics pathology

With the fixed `--fitresult` mode the binned σ_gen and the plot are correct (tanh_6), but
the "NP physical-validity" block still evaluates the CARD form: `np_physical_report(core,
eff, gnu)` → `np_damping_ok` probes `core.np_model(_nu)` (documented in its docstring) and
`spectrum_negativity` → `core.sigma_YqT_native(eff, gnu)` without form kwargs → construction
= card tanh_2. Mechanism of the e47: under tanh_2 the F_eff tanh argument is
a = (λ2_Y+λ4b²)b/λ_inf + (λ2_Y b/λ_inf)³/3; postfit λ4=−0.018<0 flips a→−∞ at large b
(the λ6 b⁵ rescue term exists only in tanh_6), tanh→−1, F_eff→exp(+2λ_inf b) — at the
grid tail b_max=50 GeV⁻¹ that's e^100≈3e43, × I_pert row weights → |σ|~e47, sign
oscillating with J0(qT b) (worst cell qT=75, Y=0 where I_pert is largest). Under the true
tanh_6 eval the point damps fine (form plot decays; binned σ_gen positive). γ_ν check
unaffected (postfit γν λ all ≥0 → damping under either form). NOT YET FIXED: thread the
eval forms into `np_physical_report`/`np_damping_ok`/`spectrum_negativity` (kwargs down to
`sigma_YqT_native(np_model=, np_model_nu=)`) + pass from sigma_gen_at_lambda.

### 2026-07-03 — module-wide audit of the card-vs-fit form hole

Swept every caller of the form-sensitive entry points (`F_eff_tf`/`gamma_nu_NP_tf`,
`sigma_YqT_native`/`sigma_gen`, the three detectors, `read_lambda_central`, fitresult λ
readers). Verdicts:
- **Holes (FIXED, see next entry):** (1) `param_model_diagnostics` detectors — card form
  only (the e47 entry above); sole caller sigma_gen_at_lambda:344. (2)
  `validation/export_spectrum.py`: `_sigma_YqT_native_at(eff,gnu)` no form kwargs → card
  form, no --np-model flag. [CORRECTION to the first write-up: `_fill_missing_params` no
  longer fills inert λ (name historical), so `--lambdas lambda6=…` hard-errored rather
  than being silently inert — the tool simply couldn't express a tanh_6 export at all.]
- **Correct by design (card form is the right form):** param_model fit path (numerator
  `self._np_model_fit` everywhere, denominator card-locked); `np_damping_wall` (derives
  `fit_forms` off indata); in-fit reco guard + `run_card_diagnostics` (card-vs-card at
  λ_central; an override form that broke central equivalence SHOULD trip it);
  `validate_agreement` both modes (histmaker/card references are card-form objects; it
  cannot validate an override form — that's the separate known "validate fit-form vs
  SCETlib reference" item, a scope limit not silent wrongness).
- **Value-only, unaffected:** closure_suite / toys_suite / toys_make_table /
  injection_analyze / fitresult_lambdas table CLI (read parms, never evaluate forms).
- **Self-consistent hardcoded tunes:** gen_level_smoke, timing, factorized_parity,
  agreement CANONICAL_BASE, native/resum validation, truth_start_grid.
- **Fixed this session:** np_function_plots + fitresult_lambdas series/toys;
  sigma_gen_at_lambda main eval (not its diagnostics block).

### 2026-07-03 — central form resolver `lambda_central.read_np_models` + both audit holes closed

One canonical function now answers "which NP forms apply to this hdf5":
`lambda_central.read_np_models(hdf5_path) -> (np_model, np_model_nu)` — card forms from
the propagated `scetlib_np_lambda_central` metadata, overridden per sector by the
`np_model_(nu_)fit` tokens in `meta_info.args["paramModel"]` when present (mirrors
param_model's `np_model_fit or card`). Works on fitresults AND datacards (datacard has no
paramModel args → card forms). Companion `read_fit_form_overrides_from_meta(meta)` exposes
the raw override; both live in `lambda_central` (metadata-owning, plot-stack-free).
Verified: fitresults → (tanh_6, tanh_6); its input datacard → (tanh_2, tanh_2).

Refactors/fixes on top: `fitresult_lambdas._resolve_models` and `sigma_gen_at_lambda` now
call the central resolver (local `_fit_form_overrides` deleted). Audit hole (1) closed:
`np_damping_ok` / `spectrum_negativity` / `np_physical_report` grew `np_model(_nu)` kwargs
(default: card forms, docstrings say when to pass fit forms) and sigma_gen_at_lambda passes
its eval forms — the validity block on `260702_2D_l6nu0p01_l60p01` now reads
neg_area_frac=6.45e-5 ≈ λ_central baseline 6.43e-5, worst cell −0.6% of peak at the qT=100
grid edge (benign known edge dip), F_eff decays OK — i.e. the postfit point IS physical
under its own tanh_6 form; yesterday's −3.5e47 was purely the wrong-form probe. Audit hole
(2) closed: export_spectrum grew `--np-model(-nu)` eval-form flags, λ-override routing by
EFF/GNU_PARAMS membership (so lambda6 can be supplied for a tanh_6 export), cache bypass on
form override. All compile + CLI regressions pass; σ_gen unchanged (1699.2).

## 2026-07-10 — cross-run summary table of all fits since 07-02

New general tool `scripts/fit_summary_table.py` (LaTeX+pdf; discovers fit/hessian/
saturated/merged chains per run dir via `--externalPostfit` links). Rendered to
`~/public_html/alphaS/260710_fit_summary/fit_summary.pdf`. Headlines across the
10 chains (postfit λ, EDM, σ(αs) from the cov pass, ptll saturated p):

| run | θ̂(αs) | σ(αs) | sat p (ptll) |
|---|---|---|---|
| 260702_l4nu0p01 | −8.01 | — | — (EDM **5.3** — NOT converged) |
| 260702_l4nu0p01_walled | −8.61 | 0.429 | 0.18% |
| 260702_2D_l4nu0p01_walled | −8.09 | — | 1.11% |
| 260702_2D_l6nu0p01_l60p01 | −8.41 | 0.501 | 3.53% |
| … [t0_newbtgrid] | −8.41 | — | — |
| 260702_2D_l6nu0p01_l60p01_nowall | −7.54 | 0.537 | 0.78% |
| 260706_2D_l4nu0p01_l6nu0p01_l60p01_nowall | −7.51 | — | 0.79% |
| 260707_l2nu0p15_TMDtanh2float | −7.47 | 0.543 | 0.06% |
| 260707_l2nu0p15_TMDtanh2float_wall | −8.04 | — | 0.51% |

Physics read: the wall consistently pins λ2ν≈0 (walled/wall rows) and pulls αs
down ~0.5–1 unit of the prior vs the free (nowall/float) configs, which all sit
at λ2ν≈+0.3, λ2≈−0.5 (the unphysical enhancement corner). Best ptll sat p is the
2D tanh_6 walled fit (3.5%); the λ2ν=0.15-prior float fit has the worst (0.06%).

**Missing passes to (re)run** (all via `fitterSCETlibNP.py` steps):
1. `260702_l4nu0p01` — refit entirely (EDM 5.3, off minimum), then hessian + saturated.
2. `260702_2D_l4nu0p01_walled` — hessian (cov) pass for σ(αs).
3. `260702_2D_l6nu0p01_l60p01` newbtgrid variant — hessian + saturated.
4. `260706_2D_l4nu0p01_l6nu0p01_l60p01_nowall` — `fitresults_t0_hess.hdf5` holds NO
   cov (edm None too; pass incomplete) — re-run hessian.
5. `260707_l2nu0p15_TMDtanh2float_wall` — `cov/fitresults.hdf5` was OVERWRITTEN on
   07-09 by a saveHists-only externalPostfit pass (no cov inside), and `merged/` was
   made before it — re-run hessian, re-merge. NB the non-wall twin survived only
   because `merged/` (07-09 13:02) predates its cov overwrite (15:41).

Gotcha for the tool: `fitresults_tm1_cov_impacts_globalImpacts.hdf5` is an aborted
stub (no results group) — skipped with a warning.

**Addendum (same day):** table gained a `wall` column (detected via the
`regularization` meta arg containing `NPDampingWall`; strength shown) and a
**full saturated χ²** column (2×`nllvalreduced`/`ndfsat`). Key read: the full
GOF is fine EVERYWHERE (2D fits 73–86%, 4D 53–55%) regardless of wall — the
tension lives only in the ptll marginal, same joint-vs-marginal pattern as the
projection_pvalues study. The wall costs essentially nothing globally
(nowall 734.8 vs walled 726.9 on 770 ndf) while improving the ptll sat p.
Tool also now merges duplicate chain roots at bit-identical postfit points
(e.g. `fitresults.hdf5` copied from `fitresults_t0.hdf5` to feed
fitterSCETlibNP.py naming) and skips h5py-locked files being written by
in-flight jobs — a 260706 hessian/cov re-run was in flight at 16:21 (also new
`merged.hdf5` there), so regenerate the table when it lands to pick up σ(αs).

## 2026-07-10 (evening) — priors fit added to the summary table

`260710_2D_l6nu0p01_l60p01_priors` = the 260702_2D_l6nu0p01_l60p01 config
(tanh_6/tanh_6, wall 5, λ6/λ6ν frozen at 0.01) + `priors=1` (registry Gaussian
priors on the 5 floating λ, centered on the fit start). Result: **practically
identical to the no-priors twin** — αs −8.414 vs −8.413, λ unchanged to ≤0.002,
full sat χ² 730.0/770 (85%) vs 726.9/770, ptll sat p 3.68% vs 3.53%,
EDM 3.6e−16. Physics read: at this fit point the wall+freeze already dominate;
the registry priors (λ2±0.5, δλ2±0.2, λ2ν±0.1, λ4(ν)±0.5) are loose relative
to the data constraint and add nothing — they'd only matter for the unwalled
configs where λ run away to the λ2ν≈+0.3/λ2≈−0.5 corner.

Two cov-pass failures noted while updating the table:
- `260710_..._priors/cov/fitresults.hdf5`: written (53 min run) but contains NO
  cov/impacts and NaN parms variances despite `--doImpacts` — same 7.5MB
  signature as the overwritten 260707 cov files. σ(αs) still missing; check the
  hessian-step log and re-run.
- `260706_.../cov/fitresults.hdf5`: h5py "bad object header version number" —
  corrupt/dead write from the 16:21 attempt. Re-run.

**2026-07-14 ROOT CAUSE FOUND + FIXED:** every cov-less 7.5MB stub since 07-09
(260707_wall overwrite, 260710_priors, 260714) came from `fitterSCETlibNP.py`
hardcoding `--noEDM` in the hessian step. rabbit_fit.py gates the ENTIRE
exact-Hessian block (cov, impacts, parms variances) on
`not noEDM and not noHessian`, and the CG fallback on `not noEDM` — so
`--noEDM` without `--noHessian` falls through BOTH branches and rabbit writes
the results (hists, mappings) with no covariance at all, silently. Fixed by
dropping `--noEDM` from the hessian step (the EDM is a near-free by-product of
the exact Hessian). The good 112MB Jul-3 cov passes were hand-run without
--noEDM, which is why they worked. Hessian steps for 260706 / 260707_wall /
260710_priors / 260714 need re-running with the fixed wrapper.

**Rename (2026-07-14):** the 260707 runs used the 2D card (260701_Z_2D
ptll_yll, ndf 772), so the dirs were renamed
`260707_l2nu0p15_TMDtanh2float[_wall]` → `260707_2D_l2nu0p15_TMDtanh2float[_wall]`.
Older log entries keep the old names. The stale absolute `--externalPostfit`
paths inside their cov/saturated/merged metas are harmless
(fit_summary_table.py falls back to basename matching within the run dir).

- Memories: [[scetlib_np_damping_wall]], [[scetlib_np_numerator_form_override]],
  [[scetlib_np_hessian_solution]], [[scetlib_np_fitpoint_breakdown]],
  [[scetlib_np_negative_lambda_trap]], [[scetlib_np_module_reorg]].
- Code: `wremnants/postprocessing/scetlib_np/` — `np_damping_wall.py`,
  `param_model.py`, `sigma_gen.py`, `params.py` (`active_params`,
  `DEFAULT_PRIOR_SIGMAS`), `lambda_central.py` (`_fill_missing_params`),
  `param_model_diagnostics.py` (postfit `np_damping_ok`/`spectrum_negativity`/
  `np_physical_report`).
- Inspect a run's command + git diff: `scripts/inspect/print_command.py <fit> [--diff]`
  (fitresults store ONLY args — no scipy status/EDM; convergence is in the fit log).
- Env: `singularity exec --cleanenv <wmassdevrolling> bash -c "source WRemnants/setup.sh && …"`,
  bind `/tmp,/run,/home,/work,/ceph,/scratch`.
