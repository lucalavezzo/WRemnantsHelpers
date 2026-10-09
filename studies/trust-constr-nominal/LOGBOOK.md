---
title: trust-constr on the nominal walled fit
slug: trust-constr-nominal
status: active        # active | paused | done | abandoned
created: 2026-10-05
updated: 2026-10-06
---

# trust-constr on the nominal walled fit — logbook

**Goal:** check whether the nominal minimum (NOMSTIFF: card A + lattice, λ4_ν = 0, `pdf62_y35_260921/merged_full_bin0xzero`
cache, trust-krylov + stiff `NPDampingWall` τ = 8, margin 0) is robust to a different minimiser: `trust-constr` with the
physical NP region imposed as hard inequality constraints instead of the penalty. Done when a trust-constr fit is certified
(optimality / constraint violation / EDM-type check) and compared with NOMSTIFF in NLL, Δ`alphaS`/σ, NP λs and active faces.

**Background:** [trustconstr-np-fit](../trustconstr-np-fit/LOGBOOK.md) (2026-08: the hard-constraint machinery, on rabbit
`local-wip-260818`, old cards and old cache; the "slow tail is not convergence" lesson);
[walled-multistart-census](../walled-multistart-census/LOGBOOK.md) (NOMSTIFF is single-valued over 9 starts and along the
`alphaS` profile); `knowledge/20_frameworks/rabbit_minimizer_tolerances.md` (trust-constr exits, `--earlyStopping` traps,
the frozen-parameter constraint-Jacobian bug). `alphaS` blinded: differences only.

---

## START HERE (status as of 2026-10-06)

> **PAUSED 2026-10-06 ~13:30 (Luca):** node memory overloaded, everything stopped, reboot pending. Our gated fits were
> SIGKILLed (exit 137) between about 12:05 and 13:20: T8C5, T8P5, TCC1 and LATCHI5. T8B has no exit line. The cause:
> mem_gate serialises only load PEAKS, so about 5 jobs at ~320 GB steady state stacked up, plus other users' jobs.
> Snapshots are on ceph. /tmp (gate locks, scratchpad) will NOT survive the reboot. Restart plan: at most 2 of our big
> jobs alive at once, in priority order; see the walled-multistart-census study log, 2026-10-06.

> **trust-constr reproduces NOMSTIFF.** TCA (warm) converged: Δ`alphaS` −2.2e-6σ, same face, σ(`alphaS`) the same to 2e-7.
> From a cold start trust-constr is too slow to converge: TCB1 hit maxiter at +0.38, still at μ = 0.1.
> See [261005-trust-constr-port](261005-trust-constr-port/LOGBOOK.md).

- **Next action:** Luca's decisions: whether to push rabbit branch `trust-constr-nominal`, and whether to tune the
  interior-point start (μ₀) for cold starts. Close-out after that: physics review, then knowledge notes (barrier stall, μ₀
  detour).
- **Blocking on:** Luca.

---

## Log

### 2026-10-07
- Draft PR opened: https://github.com/WMass/rabbit/pull/189 (branch luca/trust-constr, 3 commits rebased on WMass main
  8918140, without scan-save-detail). Full rabbit suite: 374 passed, 0 failed. Lint is clean (no new warnings). The only
  edit beyond the port is `minimizer_status` added to the sharding-safe list.
- WRemnants companion 2a8825be (`NPDampingWall.constraint_spec()/constraint_labels()`; trust-constr only), not pushed.
- Usage: certifier from warm starts only; impractical as a search method from distant starts.

### 2026-10-06
- Luca: CMR1B's λ4_ν < 0 "minimum" is suspicious. It is a wall-scaling artefact: k·λ4_ν² = 0.24, while λ4_ν·b⁴ ≈ −0.21 at
  b = 6. Agreed: run trust-constr in the XWSTIFF configuration from C. Delegated as
  [261006-tc-from-C](261006-tc-from-C/LOGBOOK.md), with μ₀ = 1e-3 via new flags on the rabbit branch.
- T1 results (orchestrator; the worker died on an expired login): TCA converged onto NOMSTIFF, TCB1 did not converge (maxiter, μ never reduced). Table in the task logbook.

### 2026-10-05
- Study opened at Luca's request ("try trust-constr again instead of trust-krylov + wall, test if our minimum is robust").
  T1 delegated to a study-worker.
- T1 interim: the trust-constr path is ported to rabbit branch `trust-constr-nominal`, in worktree
  /work/submit/lavezzo/rabbit-trustconstr (2fa9a01, 4df0074; not pushed). The WIP had two bugs, both fixed: the penalty
  stayed in the compiled loss, and the constraints were evaluated in shifted coordinates. Gates pass: frozen λs are not in
  rabbit's vector, and the constraints at NOMSTIFF equal the wall's own values. TCA (warm from NOMSTIFF) is running; TCB1
  (cold_000) and TCB2 (pert_000) come next. Worker resumed to drive the task to completion.
  [task](261005-trust-constr-port/LOGBOOK.md)
- 21:37: TCB2 (pert_000) stopped with SIGTERM on Luca's OK. After 117 iterations it was still +394 above NOMSTIFF, with
  barrier 0.1 and optimality 17.8, gaining ~0.7 per iteration; it could not converge within maxiter 300. A snapshot was
  written. trust-krylov reached NOMSTIFF from this same seed, so this is trust-constr being slow from a distant start, not
  a different minimum. Status at 21:35: TCA +0.021 (μ 0.02, optimality 0.88); TCB1 +1.74 (μ 0.1, optimality 1.7). Neither
  violates a constraint.
- 22:31: TCA is at the NOMSTIFF point: 376.6146724 vs 376.6146255 (penalty-free), +4.7e-5. μ is 6.4e-6, optimality
  1.2e-5, constraint violation 0. Not formally converged at gtol 1e-8. TCB1 is at +1.38 (iteration 137); μ is still 0.1
  and optimality 1.4.

---

## Findings

---

## Open questions

- Does the trust-constr path still exist in a usable form (it lives on rabbit `local-wip-260818`, not `main-plus-ours`)?
- Frozen-parameter bug: our freezes go through the param model's `fit_params` (not `--freezeParameters`), so the frozen λs are
  not in rabbit's vector at all. To be verified, not assumed.

---

## Decisions
