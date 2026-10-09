---
title: Phase-0 diagnosis of the walled-fit minimisers
slug: 261006-diagnosis
study: constrained-fit-strategy
status: done          # active | done | paused | abandoned
created: 2026-10-06
updated: 2026-10-06
owner: study-worker
---

# Phase-0 diagnosis of the walled-fit minimisers

**Task:** Why do the current minimisers of the walled SCETlib-AD NP fit misbehave (relu² wall leaking on λ4_ν, trust-krylov crawl plateaus, trust-constr stalling in its first barrier stage), and which 2–4 concrete recipes, at what cost, should the benchmark test?

---

## START HERE (status as of 2026-10-06, after the follow-up)

> **Three root causes, each with evidence. Four candidate recipes, costed.**
> 1. **The crawl is a limit cycle, not a minimum.** scipy's trust region grows only when ρ > 0.75 *and* the step hits the boundary. The relu² wall is C¹, not C², so on the slack side the model has no wall curvature. The iterate then zig-zags across the face, and neither half of the cycle ever meets the growth condition. The radius freezes at ~1e-6–3e-5, so the loss falls by a constant amount each iteration. The same period-2 signature is in the real CENS03 and CMR1A logs. Its severity grows steeply with τ.
> 2. **The λ4_ν leak is not a units problem.** At the C notch the *data* curvature along λ4_ν (7.6e8) is 40× the wall's 2k (1.8e7). Excluding that point to a 1e-3 tolerance would take τ ≈ 14, a κ ~ 1e12 Hessian, whatever units the conditions are written in.
> 3. **trust-constr has three problems.** Its μ₀ = 0.1 barrier stage sits ~0.3σ / +0.38 NLL off the answer and needs a sup-norm optimality below 0.1 to end. Its slack initialisation (s₀ = 1) throws away a warm start (TCA went to +333 NLL at iteration 3). Its unpreconditioned projected CG runs only 1–3 HVPs per step in the tail.
>
> Evidence:
> - the logs;
> - the stored covariances;
> - a quadratic surrogate built from the real data Hessian. It reproduces CENS01 and CENS09 (95 and 90 real iterations, 100 and 95 on the surrogate) and the CENS03 non-convergence.
>
> Real data, `alphaS` blinded: no `alphaS` values were read.

- **Next action (orchestrator, with Luca):** pick the recipes from the [table](#candidate-recipes). Proposed benchmark: [run list](#proposed-benchmark-run-list-and-cost). Nothing in it has been launched.
- **Follow-up done (2026-10-06 afternoon):** cheap fixes, tested on the surrogate; see the [follow-up section](#follow-up-2026-10-06-afternoon-cheap-fixes-at-the-level-of-parameters-and-tolerances).
  - Ranking: τ-continuation 5 → 8 (zero code) > C²-ramped relu² (a few lines) > relu³ at matched stiffness.
  - Restart-on-stall flags do not break the lock-in, and `tf-trust-krylov` shares scipy's radius rule.
- **Done:** the gated cache load (b_T reach of the y35 cache) ran 10:15–10:18 and gave max 12.64 GeV⁻¹, the same as the
  old cache. Nothing of mine is running.
- **Blocking on:** nothing for the recipe decision.

---

## Diagnosis 1 — wall condition scaling

**Caveats first.** These numbers come from stored fitresults only (`scripts/wall_scaling.py` → [wall_scaling.json](wall_scaling.json)).
- The data force along an engaged condition is `g = 2k·v` (stationarity at a converged walled minimum, k = e¹⁶). It is not
  defined for slack conditions.
- σ_free is the data-only 1σ of the condition: the stored covariance with the engaged springs removed (Woodbury). The
  HESSTCA data-only Hessian cross-checks it: same eigenvalues to 4 digits.
- Configurations differ: NOMSTIFF (card A + lattice, λ4_ν ≡ 0), XL4ZSTIFF (card A, λ4_ν ≡ 0), XWSTIFF / CMR1B
  (card A, λ4_ν free).
- b_max = 12.6 GeV⁻¹ is the largest b_T kept by the compressed rules of the **old** 260827 cache
  ([walled-two-minima/260930-gen-xsec-lambda-scan](../../walled-two-minima/260930-gen-xsec-lambda-scan/LOGBOOK.md)). The
  y35 cache's reach was measured later the same day: 12.64 GeV⁻¹, the same as the old cache (see the follow-up). Nothing below changes at the factor-2 level if it differs.

**Raw units of the conditions** (λ_∞ = 1, λ_∞^ν = 2 held; θ → λ map from every fit's `[NPDampingWall]` line:
λ2, λ4 = 0.4 + 0.5θ; δλ2 = 0.5θ; λ2_ν = 0.15 + 0.1θ; λ4_ν = 0.5θ):

| condition | raw unit | what it multiplies in the NP exponent | natural scale s (exponent per unit of c, at b_max) | wall eigenvalue 2k\|∂c/∂θ\|² |
|---|---|---|---|---|
| λ2_ν ≥ 0 | GeV² | P = λ2_ν b² + λ4_ν b⁴ (γ_ν ≈ −P) | b_max² = 159 | 1.78e5 |
| λ4_ν ≥ 0 | GeV⁴ | same | b_max⁴ = 2.5e4 | 4.4e6 |
| L2(Y) = λ2 + δλ2 Y² ≥ 0 | GeV² | ln F ≈ −2(L2 b² + B b⁴) | 2 b_max² = 318 | 4.4e6 (Y = 0), **1.78e8 (Y = 2.5)** |
| 3λ_∞²λ4 + L2³ = 3B ≥ 0 | GeV⁶ | same | (2/3) b_max⁴ = 1.7e4 | 4.0e7 |

For comparison, the data-only Hessian at the nominal minimum has eigenvalues in θ of [0.459, 4.31e4] (κ = 9.4e4; HESSTCA).
The wall on L2(|Y|=2.5), the face of every nominal fit, adds an eigenvalue of 1.78e8, about 4100× the stiffest data
direction, because its θ-gradient carries the Y² = 6.25 factor. The walled Hessian of NOMSTIFF has κ = 3.9e8.

**Equilibrium violations at the converged walled minima**, and what they mean physically:

| fit | engaged condition | v (raw) | g = 2kv | pull in σ_free (= g·σ_free) | physical size of v |
|---|---|---|---|---|---|
| NOMSTIFF | L2(\|Y\|=2.5) | 9.2e-7 GeV² | 16.3 | 1.5 | max \|Δ ln F^NP\| = 4.7e-6 (at b ≈ 1.9) |
| XL4ZSTIFF | λ2_ν | 7.4e-7 GeV² | 13.2 | 0.83 | \|Δγ_ν\| ≤ 1.2e-4 |
| XWSTIFF | λ2_ν | 1.1e-6 GeV² | 19.9 | 1.6 | \|Δγ_ν\| ≤ 4e-6 |
| XWSTIFF | B(\|Y\|=2.5) | 2.0e-7 GeV⁶ | 3.6 | — (data curvature along it is **negative**, −5.1) | Δ ln F^NP = 2.0e-3 at b_max; inside the cache harmless, but B < 0 makes direct SCETlib (b → ∞) diverge |
| **CMR1B** | **λ4_ν** | **1.64e-4 GeV⁴** | **2915** | — (data curvature 7.6e8 ≫ 2k) | **γ_ν(b_max) = +1.94** (anti-damped at all b; +0.21 at b = 6) |
| CMR1B | λ2_ν | 2.3e-7 GeV² | 4.1 | — | negligible |

Read:
- **For the ordinary faces the τ = 8 relu² wall is physically exact.** Expressed in the exponent at b_max, the leaks are
  1e-4 to 3e-4 on the L2 and λ2_ν faces. XW's B(2.5) leaks 2.0e-3 in ln F at b_max; it is harmless for the cache, which
  stops at b_max, but not for the true model.
- **The λ4_ν leak at CMR1B is a different mechanism.** Near the C notch the data likelihood itself has curvature 7.6e8 per
  (GeV⁴)² along λ4_ν (σ_data = 3.6e-5). At XWSTIFF the same quantity is 8.2e3 (σ = 0.011): the notch is 10⁵× sharper.
  - With P_data ≫ 2k the equilibrium is v ≈ v_data·P_data/(P_data + 2k): the point sits at the notch's own bottom, and
    the wall is a small correction.
  - Excluding it would need 2k ≫ 7.6e8. To bring the leak down to 1e-3 in P(b_max) takes 2k ≈ 3e12, i.e. τ ≈ 14,
    a wall eigenvalue ~8e11 in θ and κ ~ 2e12, assuming the notch's local curvature holds. At τ = 12 the leak is still
    γ_ν(b_max) ≈ +0.06. **No relu² wall is a practical exact constraint there, in any units.**
  - The notch lives where the cache is unvalidated (λ4_ν < 0, anti-damping reaching the rule-site cutoff). It is
    excluded by the physics, not by the likelihood.
- **Proposal for physically normalised conditions.** Write each condition in units of the NP exponent at b_max, c̃ = s·c,
  with s from the table above. Then quote and gate every fit on a single dimensionless tolerance, e.g.
  max_i |min(c̃_i, 0)| ≤ 1e-3.
  - Use it for certification and for setting a search-phase wall per condition: k_i = g̃_i/(2·tol), so τ_i ≈ 7–8.6 for the
    observed pulls.
  - **Not** as the exactness mechanism. Normalising with one common τ multiplies every wall eigenvalue by s² (up to 6e8),
    which makes diagnosis 2 worse.
  - Today's τ = 8 already corresponds to tol ≈ 3e-4 on the L2 and λ2_ν faces.

---

## Diagnosis 2 — the trust-krylov crawl

**Caveats first.**
- scipy's trust-krylov callback receives only (x, fun). rabbit therefore logs no trust radius, no ρ and no
  hits-boundary flag. The real-fit statements below come from the loss sequence (`scripts/parse_logs.py`,
  `scripts/analyze_logs.py` → [log_analysis.json](log_analysis.json)).
- The radius-level mechanism comes from an **instrumented line-for-line copy of scipy's trust-region loop** (same trlib
  subproblem, same constants), run on a **quadratic surrogate**:
  `f = gᵀd + ½dᵀH d + k Σ relu²(−c_i)`.
  - H is the real data-only Hessian at TCA (HESSTCA, 3719²).
  - g = 16.27·a_face, so that TCA is exactly its constrained minimum.
  - c_i are the five exact nominal wall conditions (cubic B included).
  - Code: `scripts/surrogate.py`, `scripts/run_surrogate.py`. No cache load.
- The surrogate covers the **nominal (lattice, λ4_ν ≡ 0) configuration only**. The no-lattice configuration has a
  non-convex data Hessian and the notch; there it is not a valid model.
- Validation against the real fits, at τ = 8 from the same seeds:

  | seed | surrogate iterations | real fit |
  |---|---|---|
  | pert_000 | 100 | CENS01: 95 |
  | cold_000 | 95 | CENS09: 90 |
  | pert_002 | 5172 (lock-in) | CENS03: not converged after 390 |
  | C1A | 31 | CMR1A: 151 (it had a crawl the surrogate did not have) |

  Real wall time is about 1.7–2.1× the surrogate's cost estimate (non-quadratic far from the minimum, shared node). The lock-in
  is path-dependent: the surrogate reproduces the phenomenon and its signature, not every individual occurrence.

**The trust radius did not collapse to zero. It froze, in a limit cycle.** scipy (`_trustregion.py`):
- ρ < 0.25 → radius ×¼;
- ρ > 0.75 **and** the step hits the boundary → radius ×2;
- otherwise unchanged.

relu² is only C¹, so a model built at a point on the slack side carries no wall curvature.

![zig-zag mechanism](zigzag_mechanism.png)

*(a) Surrogate, τ = 8, from CENS03's seed (pert_002). After ~50 iterations of rejections the radius is frozen at 3.8e-6
(θ units). The face value alternates every iteration: −1.93e-6, then +6e-8.*
- On the engaged side the model includes 2k aaᵀ. The step lands just on the slack side; it is interior (no boundary hit)
  with ρ = 1, so there is no growth.
- On the slack side the model has no wall. The boundary step crosses the face again and the penalty eats ~30 % of the
  predicted gain, so ρ ≈ 0.71 < 0.75 and again there is no growth.

The cycle gains a constant ~1e-4 per iteration and ran 5000 iterations. *(b) The real CENS03 (iterations 90–128) and CMR1A
(60–105) logs show exactly this signature:* every step accepted, gains alternating between two values (CMR1A 8.3e-6 /
6.8e-6, i.e. the "constant 7.5e-6 per iteration" plateau), no rejections. *(c) The surrogate's gain sequence.*

What the crawl signatures look like:
- **Rejected steps follow two patterns.**
  - The frozen period-2 zig-zag above, with no rejections.
  - A period-~7 sawtooth: 4–5 accepted steps, each gaining 2× the last (the radius doubling in the linear regime, gain ∝
    radius), then 2–3 rejections (×1/16 to 1/64) when the doubled step crosses the face from the slack side. This is
    CENS03R throughout, CMR1A at iterations 37–60, and XW's staircase.

  The fraction of consecutive accepted pairs with gain ratio ≈ 1 (the period-2 lock) tells the two kinds of fit apart
  (`log_analysis.json`):
  - **40 % in CENS03 and 44 % in CMR1A**, the two crawls;
  - 1–9 % in the eight census fits that converged normally.

  Pairs with ratio ≈ 2 (radius doubling) make up 13–45 % in every fit.
- **Restarting does not help, as observed in CENS03R.** A restart resets the radius to 1, the first steps cross the face
  and are rejected, and the radius falls back into the same cycle.
- **Yes, the plateau sits on a face where the penalty adds ~2k.** On L2(|Y|=2.5) the wall eigenvalue is 1.78e8 against the
  data's top 4.3e4. But the culprit is the curvature *discontinuity* together with the growth rule, not the condition
  number as such.
  - Once the active face is eliminated exactly, the same κ ~ 1e5 data Hessian converges in 9–45 iterations from every
    start (`tk_face`).
  - The frozen radius scales as ~1/k, so the crawl time grows with e^{2τ}:

![tau scan](tau_scan.png)

*Surrogate iterations to f − f* < 1e-6 vs τ, five starts. τ ≤ 6 converges in 15–45 for every start, and τ = 7 in ≤ 174.
τ = 8 locks in for pert_002 (5172) and is slow from the CENS03R point (265). τ = 9 locks in for 2 of 5 starts. τ = 10 does not converge in 20 000
for 3 of 5. The two black stars are the real census fits (their iteration counts match the surrogate). Caveat: nominal
configuration only; the surrogate is quadratic.*

**Would rabbit's `--precondition` options fix it? No.**
- The reference Hessian is taken at the *start*. All census seeds are strictly feasible, and relu² has zero curvature on
  the slack side, so the transform never sees the wall: the kink survives the change of variables.
- On the surrogate, full data-Hessian whitening with τ = 8 helped 2 of 5 starts (pert000 100 → 20, C1A 32 → 25). It made 3
  worse (CENS03R 265 → 1177, cold000 95 → 1181, pert002 5172 → 1814).
- The `spectral` / `gaussnewton` / blocking variants change only how the data part is whitened, so the same argument
  applies.
- rabbit also refuses `--precondition` with trust-constr.

---

## Diagnosis 3 — trust-constr cost

**Caveats first.** The per-iteration split is inferred, not measured directly.
- scipy's own counters, printed at the end of each log (nfev, cg_niter), give two equations.
  - TCA: 201 loss+grad, 1591 CG HVPs, 25 886 s.
  - TCB1: 600 loss+grad, 2552 HVPs, 49 108 s.
- Solving them: **t_f ≈ 27 s per loss+grad and t_HVP ≈ 13 s per HVP** (shared node, 128 threads).
- This is consistent with trust-krylov's dt after a rejected step (median 17–48 s ≈ one loss+grad, since the Krylov space
  is reused) and after an accepted step (45–136 s ≈ t_f + 2–8 HVPs).

![trust-constr traces](tc_traces.png)

| fit | iterations | μ stages | CG per iteration | s per iteration | outcome |
|---|---|---|---|---|---|
| TCA (warm, AT the minimum) | 140 | 0.1 for 44 iterations (3.0 h), then 10 more stages | 11.4 | 185 | converged. But the slack init kicked it to **+333 NLL at iteration 3**, so 7.2 h for a point it started on |
| TCB1 (cold_000) | 600 | **0.1 for all 600** (13.6 h) | 4.3 (late: 1–3) | 82 (late: 35–62) | maxiter, optimality 0.22 > 0.1, +0.38 NLL |
| TCB2 (pert_000) | 118 | 0.1 | n/a (stopped by SIGTERM, no counters) | 174 | stopped, +394 |

**Why the μ = 0.1 stage never finished for TCB1.**
- **(a) The stage-1 target is itself ~0.3σ off.** The barrier puts a force μ/s_i on every constraint. At TCB1's end
  the active face sits s = 0.0067 inside, which is μ/λ = 0.1/16.4 (the barrier equilibrium). The inactive faces feel
  forces 0.4–3.3 per unit, e.g. L2(0): 0.1/0.035 = 2.9.

  TCB1's −0.33σ in `alphaS` and +0.38 NLL are (mostly) the μ = 0.1 subproblem's own solution, not lack of progress
  alone.
- **(b) The stage ends only on a sup-norm Lagrangian-gradient test** (optimality < barrier_tol = 0.1). On this likelihood
  the gradient does not rank convergence (`knowledge/20_frameworks/rabbit_minimizer_tolerances.md`, "EDM is not the
  gradient").
- **(c) The inner projected CG is unpreconditioned with a loose forcing term.** It stops when ‖r‖² < max(min(0.01‖r₀‖,
  0.1‖r₀‖²)), i.e. a 3–10× residual reduction. In the tail it therefore ran only 1–3 HVPs per step. Optimality crept
  2.3 → 0.22 over ~570 iterations.

**On the quadratic surrogate, scipy trust-constr converges from every start** in 20–22 loss+grad and 600–740 HVPs, for
μ₀ = 0.1 and 1e-3 alike. Whitening (the change of variables a preconditioner would make) cuts this to 4 loss+grad and 25
HVPs from the CENS03R point. So the real-fit stall needs the non-quadratic landscape.

Hypothesis (not verified): nonlinearity keeps re-exciting the stiff-direction residual, so the 1–3-HVP CG never reaches
the soft directions.

**Would a small μ₀ plus a preconditioner fix it?**
- **μ₀ = 1e-3** removes (a): barrier forces become 100× smaller. TCC1 (another worker's run, [261006-tc-from-C](../../trust-constr-nominal/261006-tc-from-C/LOGBOOK.md))
  is testing it right now. At its iteration 31 (25 min) it had optimality 0.98, and it still made an excursion to +518
  NLL at iteration 22. Read only, not my run.
- **A preconditioner** would address (c). It needs a small rabbit change: transform the constraint Jacobian, `jac @ T`.
- **Neither fixes the slack initialisation.** scipy hard-codes s₀ = max(1.5·slack, 1) in `tr_interior_point`, which
  ignores the start. Every warm or polish use of trust-constr pays an O(100 NLL) detour, as TCA did.
- **Projected CG is not fundamentally the bottleneck at 3719 parameters.** The constraint block has 5 rows, and the
  surrogate needs only ~25 CG per iteration. The bottlenecks are the barrier strategy, the slack initialisation and the
  stopping test. Each trust-constr iteration also costs one loss+grad plus ~5–11 HVPs, as much as or more than a
  trust-krylov iteration. **trust-constr is the right certifier, not the right default.**

---

## Candidate recipes

All costs come from the surrogate (loss+grad n_f, HVP n_h → hours = (27 n_f + 13 n_h)/3600 s), scaled ×2 to real
(calibrated on CENS01/CENS09). The **surrogate covers the nominal configuration only**. Columns "CENS03R…pert002" give
the surrogate n_f to f − f* < 1e-6.

| | recipe | what changes / code | effort | exactness | surrogate n_f (CENS03R / C1A / pert000 / cold000 / pert002) | est. real h per start | main risks |
|---|---|---|---|---|---|---|
| R0 | **status quo** (trust-krylov, relu² τ = 8, margin 0) | nothing | 0 | L2/λ2_ν faces ≤ 3e-4 in exponent; **not** the λ4_ν notch | 266 / 32 / 100 / 95 / **5173** | 3–7, unbounded on a lock-in | the crawl (CENS03), CMR1B |
| **R1** | **τ-continuation**: τ = 5 (margin 0) from any start → warm τ = 8 → (optional) warm τ = 11; certify by EDM + faces | **zero code** (existing flags, `--externalPostfit`). Optional: a τ-schedule inside one process (make e^{2τ} a tf.Variable; ~½ day) to avoid one cache load per stage | 0 (½ d) | τ = 8: as R0. τ = 11: overshoot 2e-9 on L2 faces. **Still not exact on a notch** (λ4_ν config) | 27 / 26 / 40 / 43 / 36 total; the polish stages cost **6 and 2** n_f, because they start engaged (the model already has the wall curvature) | 2–3 (2–3 cache loads unless scheduled) | the soft τ = 5 stage may pick a different branch or active set than the exact problem (it makes the C notch *easier* to enter); the no-lattice cold walled history at τ = 5 was poor ("700+ iterations", walled-two-minima) |
| **R2** | **bound basis + squares**: fit (p, q, r, λ2_ν, λ4_ν) = (L2(0), L2(Y_max), 3λ4 + L2(Y_max)³, …) as **s²**; no wall at all | WRemnants `SCETlibADParamModel`: joint TMD reparam θ(s) (λ2 = p, δλ2 = (q−p)/Y², λ4 = (r − q³)/3). TMD priors re-expressed on θ(s) or dropped ([they do no work](../../walled-multistart-census/261005-tmd-priors-free/LOGBOOK.md)). Map back for λ tables. No rabbit change | 1–2 d + closure gate | **exact by construction** on all 5–6 conditions; the notch is unreachable | 17 / 30 / 49 / 35 / 30 | 1.5–3 | zero gradient at s = 0 (never start exactly on a face; slow if a multiplier ≈ 0); B(0) needs a guard if δλ2 > 0 (q > p); σ of an active-face coordinate is meaningless (σ(`alphaS`) = face-held projection = today's stiff-wall definition); mirror minima ±s (harmless) |
| **R3** | **bound basis + active-set trust-krylov** (TRON-lite): same (p, q, r, …) basis, plain bounds ≥ 0; trust-krylov on the free variables; a step that crosses a bound is cut at the breakpoint and the variable frozen; at inner convergence release any frozen variable whose gradient points inside | WRemnants reparam as R2 (without squares) + rabbit: an outer loop in `fit()` with a numpy freeze mask in `scipy_loss` / `scipy_hessp`, StopIteration from the callback on a crossing, KKT release. No retrace needed | 3–5 d + tests | **exact**: faces held at exactly 0; multipliers come out directly | 15 / 11 / 28 / 65 (rq) / 31 | 1.5–3 | more code; anti-cycling on degenerate faces; the min(p,q) kink at δλ2 = 0 (the cold anchor sits exactly on it) |
| R4 | **trust-constr, repaired** (certifier): μ₀ = 1e-3 (flag exists on branch `trust-constr-nominal`), + whitening preconditioner (constraint Jacobian ·T) | ½ d (preconditioner); a slack-init patch would mean copying scipy's `tr_interior_point` (brittle) | ½–1 d | exact | 21 / – / 20 / 21 / –; with whitening 4 (CENS03R) | warm 7 h (TCA), cold ≥ 14 h (TCB1, not converged); TCC1 will tell for μ₀ = 1e-3 | slack-init detour on every start; real non-quadratic stall; refuses `--freezeParameters` + `-r` |

Ranking:
1. **R2** as the candidate default: exact, trust-krylov speed, no rabbit change.
2. **R3** if R2's zero-gradient caveat bites, or if Luca wants explicit KKT multipliers.
3. **R1** first in time, because it is free and runnable today. It is the expected crawl fix for the **nominal**, but it
   is not exact for the λ4_ν configuration.
4. **R4** only as an independent certifier of the chosen recipe's minimum.

Not a recipe, but worth knowing: running several starts in one process.
- It amortises only initialisation: 326 s (TCB1) against fits of 2–7 h, i.e. under 5 %.
- The real win would be memory. Fits sharing one 330 GB cache could run K starts at once, where today 3 per node is the
  limit; the benchmark is memory-bound.
- It means rabbit `Fitter` state per start plus TF threading in one process: large effort, not recommended for Phase 1.

---

## Proposed benchmark run list and cost

The study's benchmark, plus one start: **pert_002, CENS03's seed and the known lock-in.** It is the most discriminating
start there is.

| config | start | R0 (exists) | R1 | R2 | R3 | R4 |
|---|---|---|---|---|---|---|
| nominal | warm NOMSTIFF | NOMSTIFF (T2) | new | new | new | TCA (exists) |
| nominal | cold_000 | CENS09 | new | new | new | TCB1 (exists, failed) |
| nominal | pert_000 | CENS01 | new | new | new | TCB2 (exists, stopped) |
| nominal | C1A | CMR1A | new | new | new | — |
| nominal | **pert_002** | CENS03 (not converged) | new | new | new | — |
| no-lattice, λ4_ν free | warm XWSTIFF | XWSTIFF | new | new | new | — |
| no-lattice, λ4_ν free | C (seed 1b) | CMR1B (leaks) | new | new | new | TCC1 (running) |

Cost, at about 3 concurrent fits per node (memory), each followed by a ~15 min Hessian pass:

| recipe | new fits | est. h per fit | fit-hours | cache loads | implementation before it can run |
|---|---|---|---|---|---|
| R0 | 0 | — | 0 | 0 | — |
| R1 | 7 | 2.5 | ~18 | 14 (2 stages; 21 with τ = 11) | none |
| R2 | 7 | 2 | ~14 | 7 | 1–2 d + closure gate (one load: the reparam must reproduce NOMSTIFF's loss at the mapped point) |
| R3 | 7 | 2 | ~14 | 7 | 3–5 d |
| R4 | 0–2 | 7–14 | 0–28 | 0–2 | none (wait for TCC1) |

Total for R1 + R2: **~32 fit-hours, ~21 cache loads, ≈ 11–12 h of wall time** at 3 concurrent fits. Add R3 and it is ~46
fit-hours, ~16 h of wall time.

Suggested order:
1. R1 now (no code).
2. Implement R2 in parallel.
3. R3 only if R2 shows its caveat.

Metrics per fit:
- converged: EDM < 1e-10, or for R3 the KKT conditions;
- the same point as the reference: |ΔNLL| < 1e-4 and ‖Δθ/σ‖ < 1e-4;
- the maximum normalised violation max_i |min(c̃_i, 0)| from Diagnosis 1;
- wall time, loss+grad count and number of cache loads.

---

## Log

### 2026-10-06
- Read the study logbook; the census, stiff-wall, cold-min-restart and trust-constr-port task logbooks;
  `knowledge/20_frameworks/rabbit_minimizer_tolerances.md`; `np_damping_wall.py`; rabbit `fitter.py` (`fit()`) and the
  `--precondition*` options; scipy 1.18 `_trustregion.py`, `_trustregion_krylov.py` and `_trustregion_constr/`
  (container image).
- Extracted x, cov, edmval and NLL for NOMSTIFF, XWSTIFF, XL4ZSTIFF, CMR1A, CMR1B, HESSTCA, TCA and TCB1, plus the
  CENS03R / TCB2 snapshots, into `/ceph/.../alphaS/261006_constrained_fit_diagnosis/*.npz`
  (`scripts/extract_fitresults.py`, no cache).
  - The CMR1A snapshot is the converged point: the iteration-25 snapshot no longer exists, because `--snapshotInterval`
    overwrites.
- `scripts/wall_scaling.py` → `wall_scaling.json`. My condition algebra was asserted equal to the wall module's
  `damping_conditions` (to 1e-14).
- `scripts/parse_logs.py` + `scripts/analyze_logs.py` over 19 fit logs → `logs_parsed.json`, `log_analysis.json`.
- Built the surrogate (`scripts/surrogate.py`). Its constrained minimum is TCA exactly (KKT by construction). Experiments
  `scripts/run_surrogate.py` (tk / tk_face / tk_pc / tc / tc_pc), `scripts/reparam_surrogate.py` (as / asrq / sq / sqrq)
  and `scripts/cont_surrogate.py` (τ-continuation). Outputs in [surrogate/](surrogate/).
  - These are fast numpy runs. The cold000 start fails for the `as` and `sq` variants with min(p,q): that is a harness
    artefact, because the cold anchor has δλ2 = 0 exactly, so p = q and my finite-difference Jacobian straddles the kink.
    The `rq` variants (r referred to q) converge from it. A real AD implementation picks a branch.
  - `sqrq_pert000` stopped early, at f = 495. This pert seed has δλ2 > 0, so q > p, and the rq basis then leaves B(0) to
    the slack wall guard, which engaged. This is the B(0) caveat of R2 in action: the guard needs the min(p,q) form or a
    second bound.
- One cache load queued through mem_gate (b_T reach of the y35 cache). Still waiting for memory at 10:05.
- Figures: `zigzag_mechanism.png`, `tau_scan.png`, `tc_traces.png` (`scripts/make_plots.py`, via save_plot).
- The four non-converged τ ≥ 10 surrogate traces were truncated to their first 2000 iterations, to stay under the 5 MB
  web limit. The full traces are in `/ceph/.../alphaS/261006_constrained_fit_diagnosis/surrogate_full/`.

---

## Findings

1. **trust-krylov + relu² wall crawls in a limit cycle of scipy's radius update.** The radius grows only if ρ > 0.75 and
   the step hits the boundary; the C¹ kink makes the iterate alternate between a slack-side boundary step with ρ ≈ 0.7
   and an engaged-side interior step with ρ ≈ 1. The radius freezes (∝ 1/k) and the loss falls by a constant amount
   per iteration. Seen in the real CENS03 and CMR1A logs (period-2 gains, all accepted) and reproduced on a
   real-Hessian surrogate.
   - Evidence: `zigzag_mechanism.png`, `surrogate/tk_pert002_tau8.json`, `log_analysis.json`.
   - **Knowledge candidate:** `rabbit_minimizer_tolerances.md`.
2. Crawl severity rises steeply with wall stiffness: on the surrogate, τ ≤ 6 converges from all 5 starts in ≤ 45
   iterations (τ = 7: ≤ 174), τ = 8 locks in for 1 of 5, τ = 9 for 2 of 5, and τ = 10 does not converge in 20 000 for 3 of 5. Evidence:
   `tau_scan.png`.
3. τ-continuation (5 → 8 → 11) removes the crawl on the surrogate from every start: 26–45 loss+grad in total. The stages
   after the first cost only 6 and 2 evaluations, because they start on the engaged side of the face. Evidence:
   `surrogate/cont_*.json`.
4. rabbit's `--precondition` does not cure the crawl. The reference Hessian at a feasible start has no wall curvature;
   on the surrogate whitening helped 2 of 5 starts and hurt 3. Evidence: `surrogate/tk_pc_*.json`.
5. Eliminating the active face exactly (bound basis, active set, or squares) converges from every start in 11–65
   loss+grad, with no wall. Evidence: `surrogate/{tk_face,as,asrq,sq,sqrq}_*.json`.
6. The data-only Hessian at the nominal minimum spans [0.459, 4.31e4] in θ (κ = 9.4e4). The L2(|Y|=2.5) wall adds 1.78e8,
   which makes κ = 3.9e8. Evidence: HESSTCA and NOMSTIFF covariances, `wall_scaling.py`.
7. **The CMR1B λ4_ν leak is a data notch sharper than the wall.** The data curvature along λ4_ν there is 7.6e8, against
   8.2e3 at W and the wall's 2k = 1.8e7. A relu² penalty cannot be exact there in any units, and the leak means
   γ_ν(b_max) = +1.94. Evidence: `wall_scaling.json`, the CMR1B covariance. **Knowledge candidate:** the wall note.
8. On the ordinary faces the τ = 8 wall leaks only 1e-4 to 3e-4 in the NP exponent at b_max (XW's B(2.5): 2.0e-3 in
   ln F).
   Evidence: `wall_scaling.json`.
9. trust-constr's real costs are t_f ≈ 27 s per loss+grad and t_HVP ≈ 13 s per HVP (two-equation solve from scipy's
   counters). TCB1 used 4.3 CG per iteration on average and 1–3 in the tail. scipy's slack initialisation s₀ = max(1.5·slack, 1)
   discards warm starts (TCA: +333 NLL at iteration 3). Evidence: the TCA/TCB1 logs, `tc_traces.png`.
10. At μ₀ = 0.1 the first barrier subproblem's own solution sits about μ/λ = 0.006 inside the active face and is pushed by
    forces of 0.4–3 on the inactive faces. TCB1's −0.33σ / +0.38 NLL is mostly that. Evidence: the TCB1 minimizer_status
    (multipliers, constraint values).

---

## Open questions

- ~~The b_T reach of the y35 cache~~: answered in the follow-up. It is 12.64 GeV⁻¹, the same as the old cache.
- **Why TCB1's inner CG ran only 1–3 HVPs in the tail** while the quadratic surrogate's runs ~25. The hypothesis is that
  nonlinearity re-excites the stiff residual. Testable cheaply by logging `cg_niter` and `cg_stop_cond` per iteration in
  the rabbit trust-constr callback (a branch change, not mine to make).
- **The no-lattice configuration is not covered by the surrogate.** XW's data Hessian is indefinite once unsprung (−8.5),
  and it has the notch. Every recipe's behaviour there has to come from the real benchmark.
- **Should R2/R3 keep the TMD priors** (re-expressed on θ(s)) or drop them? 261005-tmd-priors-free says dropping moves
  `alphaS` by −0.02σ. That is Luca's call.
- **A one-line diagnostic gap in rabbit:** trust-krylov's radius, ρ and hits-boundary are invisible in the logs. A
  callback-side estimate (step norm ‖x_k − x_{k−1}‖ per accepted step) would have made diagnosis 2 visible from the logs
  alone.

---

## Follow-up 2026-10-06 (afternoon): cheap fixes at the level of parameters and tolerances

**Question (orchestrator, for Luca):** trust-krylov stays and trust-constr is out; R2/R3 (reparametrisation) are parked.
Which fix works at the level of rabbit flags, or a line or two of wall code: restart-on-stall, a C² wall,
τ-continuation, or rabbit's native `tf-trust-krylov`?

**Caveats first.**
- Everything below runs on the **quadratic surrogate of the nominal configuration** (lattice, λ4_ν ≡ 0): the real data
  Hessian HESSTCA plus the exact wall conditions. No real fit and no cache load.
- The surrogate reproduced CENS01 and CENS09 (and CENS03's lock-in) but **not CMR1A's crawl**. Lock-in is
  path-dependent, so treat single entries as indicative and the pattern across six starts as the result.
- The no-lattice configuration (the λ4_ν notch) is not covered. **None of these fixes removes the CMR1B notch leak:**
  diagnosis 1 still holds.
- Script: `scripts/followup.py`, summarised by `scripts/followup_table.py` → [followup_table.md](followup_table.md),
  `followup_summary.json`, per-run JSON in [followup/](followup/).
- Six starts: warm NOMSTIFF, the CENS03R crawl point, C1A, census pert_000, cold_000, and **pert_002 (CENS03's seed, the
  lock-in)**.

**Semantics were copied from the code, not guessed.**
- Outer loop: scipy 1.18's `_minimize_trust_region` (trlib subproblem). The callback runs every iteration, accepted or
  rejected, with the current accepted (x, f).
- Stall test (`rabbit/callbacks.py`): once more than N losses are recorded, ref = history[−N], and the fit has stalled if
  loss ≥ ref − r·|ref|. The test runs before the append, so a stall returns the previous iteration's x.
- Restart loop (`rabbit/fitter.py` `fit()`): a fresh `minimize()` from that x, with the radius back at 1. It stops when a
  round ends without a stall, or when the restart bought less than 1e-9·max(1, |loss|).
- The losses fed to those tests are offset by NOMSTIFF's 376.61, so r acts at the real scale.
- Metrics:
  - **E_conv** = loss+grad evaluations until f − f* < 1e-6, with f* the recipe's own walled minimum (computed
    analytically);
  - **E_total** = evaluations until the fit stops by itself;
  - cap 8000 iterations, after which the fit counts as "n/c";
  - est. real hours = 2 × (27 s · n_f + 13 s · n_HVP), worst start, calibrated on CENS01/CENS09 (rough).

### Ranked table

Cells are E_conv / E_total. The overshoot column is the equilibrium violation of L2(|Y|=2.5) at the nominal minimum;
its physical size is max |Δ ln F^NP(|Y|=2.5)| ≈ 5.1 × overshoot [GeV²], at b ≈ 1.9 GeV⁻¹.

| rank | recipe | NOMSTIFF | CENS03R | C1A | pert000 | cold000 | **pert002** | failures | worst est. real h | overshoot L2(2.5) [GeV²] (Δ ln F) | code |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **1** | **τ-continuation 5 → 8**: two ordinary fits, the second warm via `--externalPostfit`, default stall flags | 26/44 | 54/72 | 32/35 | 43/55 | 51/67 | **36/49** | 0 | 5.0 | 9.2e-7 (4.7e-6), identical to today's τ = 8 answer | **none** (2 processes = 2 cache loads; ½ d to schedule τ inside one process) |
| 2 | **C² wall: relu² with its curvature ramped linearly over v ∈ [0, δ]**, at the same K = e¹⁶; δ = 1e-6 / 1e-5 GeV² | 2/22 · 3/18 | 67/72 · 46/61 | 31/46 · 33/45 | 69/79 · 55/69 | 95/109 · 99/116 | **56/66 · 58/67** | 0 | 5.2 · 5.5 | 1.4e-6 (7e-6) · 4.3e-6 (2.2e-5); in general relu² + δ/2 | **a few lines** in `np_damping_wall.py` (penalty function + a `smooth=` keyword) |
| 3 | **C² wall: relu³ at matched overshoot** (K₃ = μ/(3v₀²) = 6.5e12, i.e. strength ≈ 14.6) | 2/12 | 79/91 | 36/51 | 61/78 | 149/159 | **58/60** | 0 | 6.8 | 9.1e-7 (4.7e-6) on this face; ∝ √(g/K₃) elsewhere | **one line** (cube instead of square) + a new τ |
| — | relu³ at the literal τ = 8 (K₃ = e¹⁶) | 12/14 | 18/24 | 19/24 | 33/45 | 44/48 | 33/36 | 0 | 3.0 | **7.8e-4 (4.0e-3)**: 850× softer; it is a different wall, not a fix | one line |
| 4 | restart-on-stall, r = 1e-4, N = 10 (outside the requested grid) | 2/7 | 53/61 | 32/37 | 100/109 | 95/100 | 60/68 | 0 | 5.2 | 9.2e-7 | none, but **not robust**: N = 20, r = 1e-4 fails on pert002 (361 restarts) |
| 5 | **restart-on-stall, requested grid** N ∈ {10, 20} × r ∈ {1e-9, 1e-8, 1e-7}, `--maxRestarts -1` | 2/7–16 | 238/245–250 | 32/37–45 | 100/109–113 | 95/100–110 | **5172/5180–5185** | 0 within cap, but lock-in | 154 | 9.2e-7 | none. **Identical to R0**: the stall test never fires during the crawl |
| 5 | R0 = census defaults (N = 20, r = 0, maxRestarts −1) | 2/16 | 238/250 | 32/46 | 100/113 | 95/112 | **5172/5185** | 0 within cap, but lock-in | 154 | 9.2e-7 | — |
| 6 | restart-on-stall, r ∈ {1e-6, 1e-5} (N = 10) or {1e-5, 1e-4} (N = 20) | as R0 | as R0 | as R0 | as R0 | as R0 | **n/c (361–662 restarts)** | 1 | > 220 | 9.2e-7 | none |
| 7 | **Steihaug-CG subproblem** (= rabbit `tf-trust-ncg`'s algorithm), R0 flags / N = 10, r = 1e-8 | 2/20 | 1499 / 813 | 1261 | 1912 / 2079 | 1912 | 1168 / 1083 | 0 | 70–75 | 9.2e-7 | — |

**1. Restart-on-stall does not break the cycle.**
- **In the requested grid the stall test never fires during a crawl.** The lock-in gains about 1e-4 per two iterations
  at a loss of ~805, i.e. ~6e-7 relative over 10 iterations. CMR1A's real crawl (7.5e-6 per iteration at 378) is 4e-7
  relative over 20. Both exceed every r ≤ 1e-7, so all six combinations reproduce R0 exactly. The first fire is at r ≳ 6e-7.
- **Where the test does fire, the restart re-enters the cycle.**
  - The fresh radius of 1 is cut back by the same face-crossing rejections into the same frozen cycle.
  - Each round buys more than 1e-9·|loss|, so rabbit keeps restarting: 361–662 restarts and no convergence in 8000
    iterations on pert002, for r = 1e-6 to 1e-4.
  - N = 10, r = 1e-4 happened to converge (60 evaluations) and N = 20, r = 1e-4 did not: luck, not a fix. This is the
    real CENS03R finding again.
- **Cost near a genuine minimum is small.** Every variant ends with one restart that buys nothing. The tail after
  convergence is 5–9 evaluations at N = 10 and 12–17 at N = 20, about 0.1–0.5 h real. So a restart is cheap, but useless
  against this cycle.

**2. A C² wall removes the lock-in.**
- With relu² the cost of crossing the face by Δx is kΔx², of the same order as the linear gain once Δx ~ g/k. That
  keeps ρ below 0.75 on the boundary step, so the radius freezes.
- With a C² penalty the crossing cost is cubic. For relu² ramped over δ it is kΔx³/(3δ), negligible for Δx ≪ δ, so the
  boundary step keeps ρ > 0.75 and the radius can grow.
- On the surrogate this removes the lock-in from all six starts: 18–159 evaluations in total, no failures.

Overshoot at τ = 8 (K = e¹⁶) on the TMD faces:
- **relu³, literal K:** v = √(g/3K), i.e. 7.8e-4 GeV² on L2(2.5) (Δ ln F 4e-3, against 4.7e-6 for relu²). On XW's B(2.5)
  (g = 3.6) it would be ≈ 3.7e-4 GeV⁶, i.e. **O(1) in ln F at b_max: unphysical.** relu³ needs K₃ ≈ 6.5e12 to match
  relu²'s overshoot on L2(2.5).
  - Because the overshoot ∝ √g, weak-pull faces leak more than strong ones. With matched K₃, XW's B(2.5) would sit at
    ~4e-7 GeV⁶, 2× relu²'s.
- **Smoothed relu²:** v = g/(2K) + δ/2, so the leak is today's plus δ/2 **on every face, in that face's raw units.**
  - δ must therefore be set per condition. It is natural in the physically normalised units of Diagnosis 1: δ̃ ≈ 1e-3 in
    the NP exponent at b_max gives δ ≈ 3e-6 GeV² for L2, 6e-6 GeV² for λ2_ν, 6e-8 GeV⁶ for 3B and 4e-8 GeV⁴ for λ4_ν.
  - A single raw δ = 1e-5 would leak 5e-6 GeV⁶ on B, i.e. ~0.05 in ln F at b_max: too much.
  - The surrogate tested δ = 1e-6 to 1e-4 on L2(2.5) only; 1e-6 and 1e-5 bracket the recommended 3e-6.

**3. τ-continuation (R1)** is the cleanest by evaluations.
- **35–72 evaluations to its natural stop, from every start, including pert002.** The τ = 8 overshoot (9.2e-7) is
  exactly today's answer, so the τ = 8 point is unchanged.
- The warm NOMSTIFF start pays 44 evaluations (against 16 for R0), because the τ = 5 stage first walks to its own minimum
  at 3.7e-4 past the face.
- Adding a τ = 11 stage costs about 5 more evaluations and gives an overshoot of 2.3e-9. That is not needed on the
  nominal, where 9e-7 is already Δ ln F ~ 5e-6.
- Cost beyond evaluations: one cache load plus ~5 min of initialisation per stage, unless the strength is made a
  `tf.Variable` and scheduled inside one process (½ day).
- Risk, unchanged from the main section: the τ = 5 stage may pick a different branch in the no-lattice configuration.

**4. rabbit's native `tf-trust-krylov` has the same lock-in.**
- `rabbit/minimizer/base.py` `_minimize_trust_region` is shared by `tf-trust-exact`, `tf-trust-ncg` and
  `tf-trust-krylov`. Its radius rule is scipy's verbatim: ×¼ if ρ < 0.25, ×2 if ρ > 0.75 and the step hits the boundary,
  accept if ρ > 0.15, initial radius 1, maximum 1000. Its callback is placed the same way.
- The only differences are a NaN-ρ guard and the subproblem: native GLTR with tolerance min(0.5, √‖g‖)·‖g‖, against
  trlib's forcing. The lock-in is a property of the shared outer rule, so it is expected there too. Not run: the native
  path needs TF and the real model.
- **A cheaper subproblem makes it much worse.** The surrogate run with scipy's Steihaug-CG subproblem (the algorithm
  `tf-trust-ncg` ports) needed 1083–2079 evaluations from every non-warm start, against R0's 32–238 (pert002 aside).
  Steihaug stops CG at the boundary, so many more steps are radius-limited.

**Recommendation.** If Luca wants zero code: **τ-continuation 5 → 8.** If one process and one cache load matter: **relu²
with a C² ramp**, a few lines in `np_damping_wall.py`, with δ set per condition in normalised units (δ̃ ≈ 1e-3). Do not
spend real fits on restart flags. Either fix should be confirmed on the real problem with pert_002, cold_000 and C1A
(three fits each) before it becomes the default.

**Side result: the b_T reach of the y35 cache** (the one gated load, 10:15–10:18 on 2026-10-06, exit 0; [cache_breach.json](cache_breach.json)).
- The largest compressed-rule site is at b_T = 11.4–12.64 GeV⁻¹ for qT < 0.5, then 10.4–12.4 for 0.5–1, 10.1–11.1 for
  1–1.5, 9.4–10.9 for 1.5–2, 8.6–9.4 for 2–2.5, 7.5 for 2.5–3 and 4.2 at qT 4.5–5.
- The same holds at |Y| > 2.5, and idx-ok = 1.000 in all 300 bins with qT ≤ 10.
- This is the same reach as the old cache, so **b_max = 12.6 GeV⁻¹ is confirmed** for the normalisation of Diagnosis 1.
