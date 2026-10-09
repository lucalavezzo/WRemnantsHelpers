---
title: A reliable minimisation strategy for the walled NP fit
slug: constrained-fit-strategy
status: active        # active | paused | done | abandoned
created: 2026-10-06
updated: 2026-10-08
---

# A reliable minimisation strategy for the walled NP fit — logbook

**Goal (Luca, 2026-10-06):** a minimisation strategy for the SCETlib-AD walled fits that (i) enforces the physical NP region
exactly (or to a physically negligible violation, for every condition), (ii) reaches the same certified minimum from warm,
cold and perturbed starts, and (iii) does so in a predictable time without babysitting. Done when one recipe passes a
fixed benchmark (below) and is written up as the default.

## What we know going in

| strategy | exactness | speed / reliability | evidence |
|---|---|---|---|
| trust-krylov + relu² wall, τ = 8, margin 0 (current default) | violation ≈ (data gradient)/(2k) per condition. Negligible for the TMD faces (9e-7), **not** for λ4_ν ≥ 0 (−1.6e-4, so γ_ν ≈ +0.2 at b = 6): CMR1B | 10/10 nominal starts reach NOMSTIFF. But there are fixed-step crawl plateaus lasting hours (CENS03; CMR1A spent 1.5 h at +2.01 before escaping), which look like false minima | walled-multistart-census |
| trust-constr + hard constraints (rabbit branch `trust-constr-nominal`) | exact | from a warm start: converged, equal to NOMSTIFF to 2e-6σ. From cold/perturbed starts: did not converge in 600 iterations, stuck in the first barrier stage (μ₀ = 0.1); ~2–3× the per-iteration cost | trust-constr-nominal |

Suspected root causes, to be tested, not assumed:
1. **Condition scaling.** The wall penalises each condition in its raw units, so a single k means very different physical
   tolerances.
2. **Penalty ill-conditioning.** A stiff penalty adds a Hessian eigenvalue of ~2k along each active face normal. That may
   be what makes trust-krylov crawl on a face.
3. **trust-constr's first barrier stage:** μ₀ = 0.1, and scipy's projected-CG step has no preconditioner.

## Benchmark (fixed, so strategies are comparable)

- Nominal configuration (card A + lattice, λ4_ν = 0). Starts: warm (NOMSTIFF), census cold_000, census pert_000, C (CMR1A seed).
- No-lattice configuration with λ4_ν free. Starts: warm XWSTIFF, C (seed_1b). This is where λ4_ν ≥ 0 matters.
- Metrics:
  - converged (EDM, or optimality + constraint violation);
  - the same point as the reference;
  - maximum physical violation;
  - wall time and number of cache loads.

---

## START HERE (status as of 2026-10-08 17:30)

> Summary: [SUMMARY.md](SUMMARY.md) (covers 2026-10-08).

- **Main-fit crawl: SOLVED.** The C² ramp on the NPDampingWall removes the trust-krylov lock-in and reaches the same
  minimum ([261008-c2-wall-test](261008-c2-wall-test/LOGBOOK.md)). C² is now the default (WRemnants 692f9483, pushed);
  τ-continuation is opt-in again (WRemnantsHelpers 3c0a9fb, not pushed).
- **Saturated sub-fit: slow for a different reason.** The cause is the saturated model's conditioning, not the wall
  ([261008-saturated-subfit-diagnosis](261008-saturated-subfit-diagnosis/LOGBOOK.md)).
- **SATP done:** preconditioning makes the saturated sub-fit about 3× cheaper with the same answer. Nothing running.
- **Next:** adopt the preconditioning flags for saturated runs and toys (pending Luca); a summary refresh adds SATP.
- **Blocking on:** nothing.

---

## Log

### 2026-10-08
- SATP PASSES ([261008-saturated-subfit-diagnosis](261008-saturated-subfit-diagnosis/LOGBOOK.md) Result §5). Full-scope
  spectral preconditioning (CLI only) reaches SATB8's minimum (Δloss −1.7e-10, same q 78.40/39) with 614 HVPs vs 2150, in
  1.32 h + 306 s preconditioner Hessian vs 5.82 h, about 3× at equal load. `--minimizerGtol 0.03` is NOT safe (stop error
  up to Δq 0.86); a safe early stop needs an EDM-style criterion or a mid-fit preconditioner rebuild. Untested on toys.
- SATC2 done (C² saturated sub-fit): same path as SATB8 (157 vs 153 it), same q = 78.4/39; no iteration gain.
- Saturated sub-fit diagnosis DONE ([261008-saturated-subfit-diagnosis](261008-saturated-subfit-diagnosis/LOGBOOK.md)). The
  cost is in the saturated model's conditioning (κ ~ 2e9–1e10, a long curved α_s–shape valley), not in the wall. 89–91 % of
  the time is HVPs, and 27–56 % is spent in a tail below Δq 0.01. Top remedy: full-scope spectral preconditioning (estimated
  2–3×), then gtol ~0.03 under it. Proposed test SATP awaits Luca.
- Luca: `smooth=c2` becomes the NPDampingWall default (WRemnants 692f9483, pushed; tanh_6 interior discriminants keep relu² by default, explicit smooth=c2 refuses them, smooth=relu2 is the bitwise opt-out).
  τ-continuation is now opt-in in fitterAD.sh (WRemnantsHelpers 3c0a9fb, `--tau-continuation`).
- Luca: queue the study SUMMARY once the C² default commit lands; it must list the code changes (commits).
- C2A verdict: C² removes the main-fit crawl and lands on NOMSTIFF (Δα_s 4e-6σ), 1.11 h vs relu² never
  ([261008-c2-wall-test](261008-c2-wall-test/LOGBOOK.md)). The saturated sub-fit is different: SATC2 retraces SATB8
  iteration for iteration, with no crawl signature in either. Its cost is not the wall.
- Luca: diagnose the slow saturated sub-fit. Delegated as
  [261008-saturated-subfit-diagnosis](261008-saturated-subfit-diagnosis/LOGBOOK.md): diagnosis from existing outputs, at
  most one diagnostic job, and a ranked remedy proposal before any test.
- Luca: test the C² wall on real fits, starting from a mid-crawl snapshot (CENS03R). Delegated as
  [261008-c2-wall-test](261008-c2-wall-test/LOGBOOK.md). Two tests:
  - the main fit from CENS03R at τ = 8;
  - a saturated sub-fit from LATB8, compared with SATB8.
  The C² wall is opt-in; the default is unchanged.
- 11:14 Luca: stop R2A (relu² control) early, overriding the stop rule declared before launch (max(6 h, 3× C2A)).
  It had already answered the question: from the same CENS03R snapshot, relu² gained 0.024 in 219 iterations (1h41 of
  fit time), while C2A reached NOMSTIFF's loss in about 45 iterations. R2A was also holding one of the two run slots that
  SATC2 needs. SIGTERM, exit 143; snapshot kept at
  `/ceph/.../261008_c2_wall_test/snapshot_fitresults_R2A.hdf5`. The worker has stopped; the orchestrator now babysits C2A
  and SATC2.

### 2026-10-06
- τ-continuation is now the `fitterAD.sh --wall` default: WRemnantsHelpers 851f47f (pushed; reverted to opt-in by 3c0a9fb on 2026-10-08). `--no-tau-continuation`
  skips the τ = 5 stage. Dry-run with a stubbed rabbit: stage 1 is τ = 5 with `--noHessian --noEDM`; stage 2 is τ = 8 with
  `--externalPostfit <stage1>` appended last, so it overrides any `-f` seed.
- Luca: no confirmation study; conserve resources. τ-continuation becomes the fitterAD.sh `--wall` default, and real fits
  will show whether it works. The confirmation task was cancelled before it launched anything, and its empty dir removed.
- Luca OK'd the real-fit confirmation: 261006-tau-continuation-confirm (cancelled before launch, directory removed). Three
  τ 5 → 8 chains (pert_002, cold_000, C) on the nominal config, run one at a time, queued behind the LATCHI chain and the
  memory-profiling job. The worker enforces "≤ 2 big AD jobs alive" with a study-local check before its mem_gate call.
- Surrogate crawl-fix follow-up DONE (`261006-diagnosis/followup_table.md`, 132 runs):
  - **τ-continuation 5 → 8** converges from all 6 starts, including the CENS03 lock-in seed, with zero code and the same
    overshoot as τ = 8.
  - A C²-ramped relu² also works, but δ has to be set per face.
  - relu³ at the literal τ = 8 overshoots badly.
  - **Restart-on-stall does NOT work.** Either the stall test never fires, or each restart falls back into the same cycle.
    This retracts the orchestrator's earlier suggestion.
  - tf-trust-krylov uses scipy's radius rule, so it has the same lock-in.
  - Next: confirm τ-continuation on real fits from pert_002, cold_000 and C1A (nominal config), then make it the
    fitterAD.sh default.
- Luca: trust-krylov is fine and trust-constr is out. He wants a parameter/tolerance-level fix first; R2/R3 are parked.
  The diagnosis worker was resumed for a surrogate-only comparison of:
  - restart-on-stall (`--stallRelTol` + `--maxRestarts`, zero code; NOMSTIFF and the census ran with stallRelTol 0, so a
    crawl was never detected);
  - a C² wall (relu³);
  - τ-continuation;
  - rabbit's native tf-trust-krylov.
- Committed the TMD-priors default change: WRemnants a008faa5 on scetlib-ad-param-model (pushed).
- Phase 0 DONE ([261006-diagnosis](261006-diagnosis/LOGBOOK.md)). Three separate causes:
  1. **The trust-krylov crawl is a limit cycle in scipy's radius update.** The iterate zig-zags across a C¹ relu² face,
     and neither step type grows the radius, which freezes at about 1/k. Reproduced on a quadratic surrogate. It worsens
     with τ: lock-ins at τ = 6 / 8 / 10 were 0/5, 1/5, 3/5. `--precondition` doesn't fix it.
  2. **The CMR1B λ4_ν leak is a data notch.** The data curvature along λ4_ν there is 7.6e8, against the wall's
     2k = 1.8e7. Rescaling the conditions makes it exact only at an impractical conditioning (κ ~ 1e12). On the ordinary
     faces τ = 8 is already physically exact.
  3. **trust-constr:** the μ₀ = 0.1 stage is biased; slack initialisation at 1 discards the warm start; the unpreconditioned
     projected CG takes 1–3 HVPs per step.
  - Recipes, ranked:
    - R2: square-root reparametrisation of the bound basis, no wall; exact; 1–2 days of param-model work;
    - R3: bounds plus an active-set trust-krylov in rabbit; 3–5 days;
    - R1: τ-continuation 5 → 8, zero code, cures the crawl but not the notch;
    - R4: trust-constr as a certifier only.
  - Benchmark R1 + R2: ~32 fit-hours, ~12 h wall time. Waiting on Luca.
- b_T reach of the y35 cache (`261006-diagnosis/cache_breach.json`, 300 low-qT rows): site b_T max 12.64 GeV⁻¹, p99 11.1. This
  is the same as the old cache, so the b_max = 12.6 used to normalise the conditions stands.
- Opened at Luca's request ("we need to really find a working and reliable strategy for the minimization"), after
  CMR1B (the wall leaks on λ4_ν) and TCB1/TCB2 (trust-constr too slow from distant starts).

---

## Findings

- The hours-long walled-fit crawl is scipy trust-krylov's radius rule locking up at the relu² wall's curvature jump. A C²
  ramp removes it and lands on the same minimum (Δα_s 4e-6σ, face overshoot 2.4e-6 GeV²)
  ([261008-c2-wall-test](261008-c2-wall-test/LOGBOOK.md); mechanism in [261006-diagnosis](261006-diagnosis/LOGBOOK.md)).
- Restart-on-stall does not fix the crawl. τ-continuation does, but costs an extra cache load.
- The projected-saturated sub-fit's slowness is intrinsic to the saturated model (κ ~ 1e9–1e10, an α_s–shape valley, 89–91 %
  of the time in HVPs), and the wall plays no part
  ([261008-saturated-subfit-diagnosis](261008-saturated-subfit-diagnosis/LOGBOOK.md)).

---

## Decisions

- 2026-10-06 (Luca): trust-krylov stays and trust-constr is out as a production minimiser (warm certifier only). No
  confirmation studies; conserve resources.
- 2026-10-08 (Luca): `smooth=c2` is the NPDampingWall default (692f9483); τ-continuation is opt-in (3c0a9fb).
- 2026-10-08 (Luca): run SATP (spectral preconditioning of the saturated sub-fit).
