# Physical-λ enforcement study — logbook

**Goal:** set up the SCETlib NP param-model fit (real-data Z, `260623_Zhistmaker`)
so it robustly allows **only physical (damping) NP λ**, *without* masking genuine
data–model tension. Stay `tanh_2`; add extra terms (`tanh_6`/λ6) only if a
demonstrated need survives.

---

## START HERE (status as of 2026-06-30)

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

## Pointers

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
