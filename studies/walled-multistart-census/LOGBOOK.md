---
title: Walled multistart census
slug: walled-multistart-census
status: active        # active | paused | done | abandoned
created: 2026-09-30
updated: 2026-10-05
---

# Walled multistart census — logbook

**Goal:** under an exact physical NP constraint (wall margin 0, very stiff), find the minima of the nominal fit, certify
each, and say whether `alphaS` depends on which one the fit lands in. Done when the census table exists for the nominal
configuration, with a physics read and a physics review.

**Configuration (Luca, 2026-09-30):** nominal = card A + lattice CS constraint (λ4_ν = 0, 1D lattice term on
λ2_ν = 0.1345 ± 0.031) on the new `pdf62_y35_260921/merged_full_bin0xzero` cache. Cross-check = card A without lattice
(λ4_ν free), same cache. `alphaS` blinded: differences only, everywhere.

**Background:** [walled-two-minima](../walled-two-minima/LOGBOOK.md) (W and C, the two damping routes, and the fact that every
converged walled fit descends from a single warm start).

---

## START HERE (status as of 2026-10-04)

> **PAUSED 2026-10-06 ~13:30 (Luca):** node memory overloaded, everything stopped, reboot pending. Our gated fits were
> SIGKILLed (exit 137) between about 12:05 and 13:20: T8C5, T8P5, TCC1 and LATCHI5. T8B has no exit line. The cause:
> mem_gate serialises only load PEAKS, so about 5 jobs at ~320 GB steady state stacked up, plus other users' jobs.
> Snapshots are on ceph. /tmp (gate locks, scratchpad) will NOT survive the reboot. Restart plan: at most 2 of our big
> jobs alive at once, in priority order; see the walled-multistart-census study log, 2026-10-06.

> **The nominal fit is single-valued, at its minimum AND along the `alphaS` profile.**
> - Census (T4): 9 of 9 converged starts give the same point as NOMSTIFF.
> - Profile (T6): at Δ`alphaS` = ±1σ and ±2σ, 3 of 3 independent frozen-`alphaS` starts per point (warm, random-NP,
>   PDF/TNP kick) agree to |ΔNLL| ≤ 4e-10 and ||Δθ/σ|| ≤ 2e-5, with EDM ≤ 2.5e-10.
> - Profile 2ΔNLL = 1.000 k² − 0.030 k³ + 0.002 k⁴, so the interval is [−0.985, +1.015] σ_NOM (cubic-only fit:
>   [−0.982, +1.012]). The width matches the Hessian σ.
> - Wall settings: margin 0 + τ 8 move the nominal `alphaS` by +0.012σ. Committed and pushed (WRemnants ccb2adb8, Helpers aa0ad24).
> Configuration: card A + lattice, λ4_ν = 0, new bin0xzero cache. Real data, blinded.

- **Running (2026-10-05):** 261005-cold-min-restart (seeded at C, plus 1b without lattice) and 261005-tmd-priors-free; trust-constr is in study trust-constr-nominal.
- **Next action:** close-out (physics review of T4 and T6; knowledge-curator), or Luca's open items: T8 (λ4_ν float vs
  freeze), T5 (σ vs wall settings), finishing CENS03, and the blinding-exposure redaction.
- **Blocking on:** nothing.

---

## Plan

| # | task | depends on |
|---|---|---|
| T1 | `margin=` keyword on `NPDampingWall` (`-r` arg; default 5e-3 unchanged) + test + lint + loss gate | — |
| T2 | re-minimise the known minima at margin 0, τ = 8 (LATL4ZY35WALLWARM; cross-check Y35ZWALLWARM, Y35ZWALLL4ZR); record minimiser difficulty. **Decision:** is the stiff wall enough, or port trust-constr (T2b)? | T1 |
| T2b | (only if needed) port the trust-constr hard-constraint path from rabbit `local-wip-260818` | T2 |
| T3 | randomised-start generator: non-NP ~ N(0, s²cov), NP λ uniform over the physical region (λ2_ν up to about 0.3), `alphaS` ±2σ in blinded x | T1 |
| T4 | the census: about 8 perturbed + 2 "cold except `alphaS`" starts (nominal), a smaller set (cross-check); certify each fit | T2, T3 |
| T5 | σ(`alphaS`) vs τ and margin at the best minimum | T4 |
| T6 | (only if more than one minimum within ~2 NLL) `alphaS` profile scans from each minimum, lower envelope | T4 |
| T7 | physics read, physics review, knowledge notes | all |
| T8 | (Luca's question) λ4_ν floating vs frozen in the nominal fit: Δ`alphaS`, σ(`alphaS`), 2ΔNLL | T1, T2 |

---

## Log

### 2026-10-06
- Luca agreed: drop the T8 Gaussian-2D fits and TCC1 (both task logbooks marked closed). Pushed WRemnants a008faa5 (TMD
  priors off by default) and Helpers 851f47f (τ-continuation default). Running: only the LATCHI chain and the memory-
  profiling job.
- 14:30, after the reboot (Luca: resume everything). Sequenced with at most 2 big AD jobs alive at once:
  - slot A: LATCHI5R → LATCHI8 (the exact lattice χ², lattice-cs-kernel/261006-lattice-chi2-in-fit);
  - slot B: one memory-profiling job (new study ad-fit-memory-footprint).
  - Queued behind them, launched by the orchestrator only: T8C5/T8P5 resumed from snapshots, TCC1 from its snapshot, and
    the crawl-fix confirmation fit.
  - The surrogate crawl tests (no memory) were resumed now.
- ~13:30 PAUSE (Luca): memory overload, reboot pending. Restart plan, in priority order with at most 2 big jobs alive:
  1. LATCHI: the exact lattice χ² nominal fit (τ 5 → 8, warm from NOMSTIFF). The closure is already done in its task dir.
  2. The crawl-fix confirmation fit (CENS03 seed). It waits on the surrogate test (no memory).
  3. T8 Gaussian-2D fits: optional, superseded by LATCHI for the decision.
  - Dropped: T8B (it tests the Gaussian's extrapolation) and TCC1. TCC1 had reached +0.964 vs XWSTIFF on the λ4_ν = 0
    face, uncertified; its snapshot is on ceph.
  - Needs Luca's OK: a run cap (MAXRUN) in the shared mem_gate.sh. The edit was blocked as a shared-resource change.
- 12:05–12:23 the OOM killer took T8C5, T8P5 and TCC1 (exit 137). Five or more cache-loaded fits were sharing the node.
  - T8C5 had essentially converged: −1.150 vs NOMSTIFF-on-2D-card, as the Newton step predicted.
  - Restarts were approved from snapshots: T8C8 (τ = 8, warm from the T8C5 snapshot), then T8P5R → T8P8, and TCC1R.
  - Each worker runs at most one load at a time, gated at 400 GB.
- T8 interim ([task](261006-t8-l4nu-lattice2d/LOGBOOK.md)). At λ2_ν = 0.0643 the lattice-preferred λ4_ν is:
  - +0.0018 ± 0.0017 with the card's stat+syst Gaussian (the orchestrator's +0.003 was the stat-only Gaussian);
  - **+0.0075 with the exact χ²** (MCMC 0.0080 ± 0.0033). The Gaussian is too weak here and ~30× too steep at W.

  The exact lattice Δχ²(W − NOM) is +17 to +27, so the lattice excludes the W route against the data's 2ΔNLL of 1.9. The
  data pull on λ4_ν at NOMSTIFF is away from the wall. Fits: T8B at 376.358, below NOMSTIFF-on-2D-card (376.936); T8C5 at
  376.19; T8P5 descending. The chain watcher launches T8C8 / T8P8 / HESST8B with the TMD priors pinned.
- 10:40 Luca: drop the TMD priors in the default param model. Done in WRemnants
  `wremnants/postprocessing/scetlib_ad/params.py`: λ2, λ4 and δλ2 were added to FREE_PARAMS, and the REPARAM widths are
  unchanged. Uncommitted; black clean. Evidence: 261005-tmd-priors-free.
  - To get the old priors back: `prior_sigmas=lambda2=1,lambda4=1,delta_lambda2=1`.
  - Caveat: unwalled fits now have nothing holding the TMD physical.
  - Running fits keep the old code (T8B, T8C5, T8P5 and TCC1 all log "Gaussian priors on 44").
  - The T8 and TCC1 workers must pin the old priors in every later command (T8C8, T8P8, HESS*) so the comparisons stay
    like-for-like.
- 10:26: a second live orchestrator session (7f9fbb62 / [1be6eb]) had relaunched the superseded T8A as T8A3. Luca:
  **session 66bf4f owns** this study, trust-constr-nominal and constrained-fit-strategy. The other session is told to stand
  down. T8A3 was stopped (SIGTERM, exit 143). Single-babysitter rule.
- Luca on the CS kernel: try the 2D lattice constraint on (λ2_ν, λ4_ν), both floating with λ4_ν ≥ 0 held exactly, and
  compare it with NOMSTIFF (1D term from the λ4_ν = 0 lattice fit, λ4_ν frozen at 0).
  - The lattice term is the Gaussian summary of our separate lattice fit. It is not a simultaneous fit of the lattice
    points.
  - The physical bound is applied once, in the combined fit, not in the lattice summary.
  - T8 worker resumed with that deliverable. T8A was replaced: trust-constr discards the warm start. The new T8C is
    trust-krylov with τ-continuation 5 → 8.
  - Expected from the Newton step: λ4_ν ≈ +0.004, inside the physical region, and Δ`alphaS` ≈ −0.10σ.
- Luca: λ4_ν = 0 is not something our Z fit derives. Without lattice the Z data mildly prefer W, λ4_ν = +0.044
  (2ΔNLL 1.9; Δ`alphaS` 0.26σ between the routes).
  - The lattice side is already known (lattice-cs-kernel/260923-scetlib-kernel-fit): the free lattice fit gives
    λ4_ν = −0.0059 ± 0.0033 (ρ = −0.88 with λ2_ν), and freezing λ4_ν = 0 costs Δχ² = 1.87. So under λ4_ν ≥ 0 the
    lattice optimum is the boundary.
  - T8 delegated as [261006-t8-l4nu-lattice2d](261006-t8-l4nu-lattice2d/LOGBOOK.md): λ4_ν floated with the existing 2D
    lattice card and λ4_ν ≥ 0 held exactly by trust-constr. Starts: warm NOMSTIFF and the W point.
  - The broader minimiser question is a new study, [constrained-fit-strategy](../constrained-fit-strategy/LOGBOOK.md).

### 2026-10-05
- Luca: two new fits, each delegated to a study-worker (nominal config: stiff wall, margin 0, lattice, new cache).
  - [261005-cold-min-restart](261005-cold-min-restart/LOGBOOK.md): NOMSTIFF's configuration seeded at C (CCWALLCOLDR, the
    higher walled minimum of walled-two-minima). C comes from the old cache and the no-lattice card, so the seed is mapped
    by name, with θ re-anchored if the caches' anchors differ. λ4_ν < 0 cannot be carried, since it is frozen at 0 under the
    lattice. Added by the orchestrator: 1b, the same seed in the no-lattice stiff-wall config (XWSTIFF), where C's
    λ4_ν < 0 can exist. This tests whether C survives the stiff wall at all.
  - [261005-tmd-priors-free](261005-tmd-priors-free/LOGBOOK.md): NOMSTIFF without the TMD priors (λ2, λ4, δλ2), warm
    from NOMSTIFF.
  - 261005-cold-min-restart interim (both running, PIDs 1516769 / 1521106): CMR1A crawls on NOMSTIFF's face at +2.0 vs
    NOMSTIFF. CMR1B keeps C's notch: λ4_ν went deeper, to −2.2e-4, while paying a 0.43 wall penalty at τ = 8, so the stiff wall
    is not exact for this notch. Not certified yet. [task](261005-cold-min-restart/LOGBOOK.md)
  - 261005-cold-min-restart, both fits finished (18:19 / 17:55, exit 0). CMR1A returned to NOMSTIFF: loss 376.6146329237,
    identical to NOMSTIFF; EDM 1.8e-14. **CMR1B is a distinct certified minimum** in the no-lattice stiff-wall config:
    +0.670 above XWSTIFF, EDM 1.2e-17, so C survives τ = 8. Worker resumed to analyse both.
  - [261005-cold-min-restart](261005-cold-min-restart/LOGBOOK.md) DONE.
    - CMR1A = NOMSTIFF (ΔNLL 4e-11). The +2.01 plateau at iterations 14–106 was a fixed-step crawl; it escaped at
      iteration 107.
    - CMR1B = C survives the stiff wall in the no-lattice config: +0.670 above XWSTIFF, Δ`alphaS` +0.37σ_XW,
      λ4_ν = −1.64e-4 (wall penalty 0.24), γ_ν > 0 at every b_T. Same point as soft-wall C (0.30σ_C apart).
    - Consequence: a τ = 8 relu² wall does not exclude a narrow data notch. A "single minimum" claim for the no-lattice
      cross-check needs a hard constraint (trust-constr) or λ4_ν ≥ 0 imposed explicitly. The nominal (lattice, λ4_ν ≡ 0) is
      unaffected: 10/10 starts reach NOMSTIFF.
  - CMR1B exact term split (cache evaluation, `term_split_CMR1B.json`; the reference reproduces its stored NLL to 0.0):
    data −0.429, priors +0.914, BB −0.055, wall +0.240, total +0.670 (the estimate was data −0.48).
  - [261005-tmd-priors-free](261005-tmd-priors-free/LOGBOOK.md) DONE: the TMD priors do no work. NOMTMDFREE moves `alphaS` by
    −0.020σ_NOM and σ(`alphaS`) by −0.2 %. The TMD λs move ≤ 0.06σ, the active face is the same, and EDM is 5.5e-17. A
    Newton step from NOMSTIFF's Hessian predicted the result to ~1 %.
  - trust-constr instead of trust-krylov + wall: a new study, [trust-constr-nominal](../trust-constr-nominal/LOGBOOK.md).
- [261005-np-forms-lattice](261005-np-forms-lattice/LOGBOOK.md) (Luca, quick): NP functions for the lattice-constrained prefit
  vs the NOMSTIFF / LATL4ZY35WALLWARM postfits. The postfit CS kernel is about half as steep as the lattice (λ2_ν 2.3σ below:
  the known ptll tension); the two postfits are indistinguishable.

### 2026-10-04
- T6 DONE (17:56): all 12 converged; at ±2σ the 3 starts agree too (M2 ≤ 3.9e-10, P2 ≤ 4.2e-10). The ±2σ R/K/W results
  came from fits resumed from their pre-kill snapshots. The final plot was regenerated.
- T6 worker handback (provisional; ±2σ starts are still running, under a watcher):
  - single-valued; 2ΔNLL = 1.0000 k² − 0.0303 k³ + 0.0018 k⁴; interval [−0.985, +1.015] σ_NOM;
  - λ4 rises monotonically with `alphaS`; PDF+TNP carry about 2/3 of the displacement along the profile; every point is on
    the single face L2(|Y|=2.5) = 0.
  CORRECTIONS to orchestrator chat: (a) a plain least-squares k² + c·k³ fit gives [−0.982, +1.012], not "every way ≈
  [−0.985, +1.015]", and the 0.003σ spread is model ambiguity; (b) PROFM2KS is NOT a CENS03-type crawl, since its steps are
  growing (2ΔNLL ≈ 52 at iteration 41).

![alphaS profile, multistart](261002-multistart-profile/profile_alphas_multistart.png)
- Luca: drive T6 to conclusion and make the profile plot now. T6 worker resumed: a watcher auto-relaunches killed fits from
  their snapshots, a live-updated profile plot, and the final analysis.
- T6 status (orchestrator):
  - 9 of 12 fits done. PROFM2R, PROFM2K and PROFP2W were SIGKILLed (exit 137, probably the OOM killer on the shared node) on
    10-03 at 06:47, 07:02 and 13:34, while unwatched. They were relaunched from their last snapshots as PROFM2RS, PROFM2KS
    and PROFP2WS (15:20, gated).
  - Agreement (pairwise, all 3719 parameters): at −1σ, W/R/K agree to |ΔNLL| ≤ 3e-10 and max |Δθ/σ| ≤ 5.3e-6; at +1σ, W/R/K
    agree to ≤ 1.2e-10 and ≤ 1.6e-8; at +2σ, R/K agree to 4e-10 and 3.9e-8. Single-valued wherever ≥ 2 starts converged.
  - Profile 2ΔNLL: −2σ 4.271 (W only), −1σ 1.032, +1σ 0.972, +2σ 3.786. The symmetric part (1.002, 4.029) means the
    profile width matches the Hessian σ to ≲ 0.5 %. The antisymmetric part scales as k³ (0.030 → 0.243), a small cubic
    term: interval ≈ +1.015σ / −0.985σ. Essentially parabolic.

### 2026-10-02
- T6 launched: 12 frozen-`alphaS` fits queued, 3 running (k = −1: W, R, K). The freeze is verified (`alphaS` bit-identical
  to the seed after 3 iterations), with no collision with fit_params.
  Start costs at k = −1: W +150, R +5.4e3, K +1.5e5 (the K kick is large; watch it for a CENS03-like crawl).
  PROFM1W: +1.30 after 8 iterations, still descending (parabolic expectation +0.5). Last fits are expected overnight.
- Luca: `alphaS` scans warm-chain, so the step size changed which basin they followed; do the profile BY HAND.
  Dispatched T6 [261002-multistart-profile](261002-multistart-profile/LOGBOOK.md):
  - frozen-`alphaS` independent fits at Δ = ±1σ and ±2σ;
  - 3 starts each: warm NOMSTIFF, census-perturbed, and a large PDF/TNP kick (the old second-solution direction);
  - 12 fits, at most 3 at a time; ±1σ first.
- Wall changes COMMITTED and PUSHED (Luca): WRemnants origin/scetlib-ad-param-model ae9c6865..ccb2adb8 (this included ~20
  earlier local commits and the upstream/main merge d81150c6); WRemnantsHelpers origin/main 18bda4a..aa0ad24.
  - WRemnants `ccb2adb8` on `scetlib-ad-param-model` (np_damping_wall.py: margin keyword + default 0; committed inside the
    container, because the pre-commit hook needs pylint);
  - WRemnantsHelpers `aa0ad24` on `main` (fitterAD.sh τ 8 + margin=0; knowledge note).
  - `scripts/fit_summary_plotly.py` is UNTRACKED in WRemnantsHelpers, so its one-line margin-label change is not committed.
- [261001-census-nominal](261001-census-nominal/LOGBOOK.md) DONE: one minimum (9 of 9 converged = NOMSTIFF; floor 1e-4 in
  ΔNLL and ||Δθ/σ||, next object CENS03 at 29). Summary plot inline there.
  CORRECTION: the orchestrator's "cost scaled with how far the start was" does NOT hold within the census (Spearman 0.25,
  p = 0.5); it holds only relative to the warm T2 refits.
  Caveat: 10 starts cannot rule out a rare basin. Starts aimed at the other wall faces are untested.

![census summary](261001-census-nominal/census_summary.png)
- All census fits done overnight. Orchestrator check against NOMSTIFF: CENS01, 02, 04, 05, 06, 07, 08, 09PF and 10 all have
  |ΔNLL| ≤ 2.3e-10 and max |Δθ/σ| ≤ 2.6e-7, except CENS08 (2.0e-6, pdfEig3; EDM 5.2e-12). → ONE minimum.
  CENS03 is not converged (see 10-01). The T4 worker was resumed to write up.
- 261001-reproduce-nominal: validate_step5 OVERALL PASS.

### 2026-10-01
- CENS03 diagnosis result (`261001-census-nominal/cens03_hybrid_eval.json`). Gate: NOMSTIFF reproduced exactly.
  - Control (CENS03R snapshot): ΔNLL +429.96 = data +5.6, constraints +423.3, BB +0.7; |grad|max 3.9 (NOMSTIFF 3e-6).
    So CENS03 fits the DATA almost as well as NOMSTIFF. The excess is the prior cost of displaced nuisances, and it is NOT
    stationary: a crawl, not a minimum.
  - Hybrid (CENS03 param-model params + NOMSTIFF nuisances): ΔNLL +115 (data +100, BB +12.5). INCONCLUSIVE as a same-basin
    test. CENS03's TNP / PDF-eigenvector / `alphaS` offsets (up to 0.9σ) are compensating its nuisance offsets, so swapping
    one block breaks the balance. The orchestrator's prediction ("within a few units of NOMSTIFF if same basin") was too
    naive. Retracted as a criterion.
- 21:31: CENS03R SIGTERM'd at 806.578 (260 iterations; Luca: ok).
  - Snapshot vs NOMSTIFF: param-model block (46) max |Δθ/σ| 0.93 (resumTNP_b_qqbarV), ||·|| 2.6, Δ`alphaS` −0.18σ;
    nuisance block ||·|| 29.2, with ½||·||² = 426 of the 430 excess.
  - Hybrid seed written (CENS03R param-model params + NOMSTIFF nuisances) plus the snapshot as a control.
  - The gated NLL evaluation `scripts/run_hybrid_eval.sh` → `cens03_hybrid_eval.json` is waiting for memory.
- Self-match pitfall hit again: `until ! pgrep -f "postfix CENS03R "` matched the waiting shell itself and never ended.
  Wait on the PID instead.
- 21:30 status:
  - CENS04 and CENS05 DONE at NOMSTIFF's NLL (EDM 2.9e-17 / 3.4e-17). CENS06 is at +1.6e-7, settling. CENS07 is running (983).
    CENS08 and CENS10 are queued.
  - **The restart did NOT help CENS03:** CENS03R's first 8 iterations were rejected, then it crawled at the same rate,
    806.704 → 806.578 in 256 iterations (4.5 h).
  - **CENS03 is not a separate NP minimum.** Its NP λ are at NOMSTIFF's, and the gap is in the nuisances: no parameter is more
    than 3σ off, 117 are more than 1σ off, and ||Δθ/σ|| = 29.3, so ½||Δθ/σ||² ≈ 430 = the whole excess NLL. 76 % of it is
    effStat and 10 % effSyst, i.e. the un-relaxed s = 0.5 kick in near-diagonal, prior-dominated directions. A Newton step
    would fix this in one go; trust-krylov can't, because the active stiff-wall face (L2(|Y|=2.5) = 0) caps the trust radius.
  - Answer for knowledge/ (restart, open item): restarting trust-krylov does NOT un-stick a crawl caused by an active
    stiff-wall face.
- 16:47 (Luca: ok): CENS03 SIGTERM'd at 806.704 (129 iterations) and relaunched as CENS03R from its SIGTERM snapshot, with the
  same command and tolerance. This tests whether a fresh trust radius un-sticks a mid-descent crawl on an active wall face
  (an open item in knowledge/20_frameworks/rabbit_minimizer_tolerances.md).
- 16:30 status:
  - CENS09PF (Hessian for the cold start) has EDM 1.1e-15. Against NOMSTIFF: ΔNLL 2.7e-11, max |Δθ/σ| 1.1e-7, so the same point.
    That makes 3 of 3 finished starts at NOMSTIFF.
  - CENS03 is CRAWLING: 806.7 after 116 iterations, about 430 above the minimum, improving by only ~0.003 per 12 iterations.
    Its NP λ are already close to the minimum (λ2 0.046 vs 0.026, on the L2(|Y|=2.5) = 0 face), so the excess is in the non-NP
    sector. Likely the stiff-wall kink: with the face active the trust radius stays small for ALL directions.
  - CENS04 (478, falling in steps) and CENS05 (391.3, about 15 above the minimum, creeping) are on the same face.
    No basin evidence yet.
- Orchestrator parameter check (14:20) of CENS01 and CENS02 against NOMSTIFF:
  - ΔNLL +1.2e-10 / −1.6e-10;
  - largest |Δθ/σ| over all 3719 parameters 1.4e-7 / 2.6e-7 (the largest mover is `alphaS` itself);
  - ||Δθ|| 2.7e-7 / 4.5e-7.
  So both are the SAME point as NOMSTIFF, from starts with λ2 ≈ 0.45, λ4 ≈ 0.10, λ2_ν 0.12 / 0.19 (NOMSTIFF: 0.026, 0.088,
  0.064). CENS09PF (the Hessian for the cold start) is gated; CENS03–05 are running.
- 14:11: CENS01 (95 iterations, EDM 3.0e-14) and CENS02 (173 iterations, EDM 8.9e-15) finished on their own at NOMSTIFF's NLL.
  CENS09 was at ΔNLL 2.7e-11 and was SIGTERM'd (Luca: stop if converged). CORRECTION (same entry, 14:12): the SIGTERM handler writes
  a snapshot and EXITS (143); there is no Hessian. So CENS09PF was launched: a `--noFit` pass from
  `snapshot_fitresults_CENS09.hdf5`, gated, with its log symlinked. CENS03 is running with the new tolerance.
- T4 in progress (13:40): CENS01, 02 and 09 are all at NOMSTIFF's NLL (ΔNLL ≤ 5e-7), but crawling at 10–20 min per
  iteration, with `--earlyStopping 20` needing 20 iterations of literally no improvement.
  Luca: use a tolerance, not babysitting. The queued CENS03–08 and 10 now run with
  `--earlyStopping 15 --stallRelTol 1e-11 --maxRestarts 0`:
  - stop when the improvement over 15 iterations is below 1e-11 relative, about 4e-9 NLL;
  - the window of 15 is longer than the longest plateau of rejected steps T2 saw (11);
  - no restart, which would rebuild the Hessian;
  - the postfit Hessian still runs, and EDM certifies the minimum.
  Not `--minimizerGtol`: here the gradient norm is not a convergence measure (stiff NP directions keep |g| large at a true
  minimum). Originals are kept as `cmds/*.cmd.orig_es20`.
- CACHE_HOWTO.md rewritten as a GENERAL how-to (Luca: not tied to reproducing the nominal cache). Rendered as a private
  claude.ai artifact (https://claude.ai/artifact/3o1K2tD5b3AogUaxG3TbfF) and on the website as
  [261001-reproduce-nominal/CACHE_HOWTO.html](261001-reproduce-nominal/CACHE_HOWTO.html). The `cache_howto/` copies of the nominal runcard
  and the patch scripts stay as reference.
- Luca asked for a short cache-build doc: written at [261001-reproduce-nominal/CACHE_HOWTO.md](261001-reproduce-nominal/CACHE_HOWTO.md), with the runcard and the
  bin-0 patch scripts copied into `cache_howto/`.
  - Access: the builder and extractor are on the PUBLIC fork (lucalavezzo/WRemnants `scetlib-ad-param-model`, identical to
    local). scetlib-cms `ca15aec` is on CERN GitLab, SCETlib group only.
  - The wrapper scripts and patch scripts were untracked study files and are now copied next to the doc.
  - The local WRemnants HEAD has unpushed commits (df3c30f7, ff625d85, ...), but none of them touch the builder.
- [261001-reproduce-nominal](261001-reproduce-nominal/LOGBOOK.md) DONE: REPRODUCE.md v2 for the NOMSTIFF chain.
  - Every flag of the cache build is explained. The step-5 argv check passes, and the lattice-injection and bin0xzero patch
    re-runs are byte- and CRC-identical to production. 13 known gaps are listed. The NLL check is queued behind mem_gate
    (`261001-reproduce-nominal/logs/validate_step5.out`, launched 10:32).
  - Corrections for knowledge/: the cache was BUILT by scetlib ca15aec (2da973d + MR !13), and 2dd978a only reads it; it has
    60 PDF members, not 62; df3c30f7 and 2a59246 are on no remote.
  - A superseded banner was added to the old 260922 guide.
  - **Blinding exposure flagged, Luca to decide:** the offset is a deterministic function of public code and the parameter
    name, so any published blinded θ(`alphaS`) can be turned into an absolute value. Published θ values: the old guide
    (line ~207), the AD table pdf (θ̂ column), and the interactive fit-summary HTML. All are on ~/public_html, which has no auth.
- Luca asked whether 260922-reproduce is still valid. No: it pins b66f8de, the 260827 cache, rabbit f77f10e, and the UNWALLED
  CCKRYLOVWARM reference. Dispatched [261001-reproduce-nominal](261001-reproduce-nominal/LOGBOOK.md) to write a v2 for the
  current nominal, with the cache-build flags explained and validated against NOMSTIFF.
- Blinding and warm starts (code read, rabbit `blinding.py` + `Fitter.load_fitresult`):
  - The offset is drawn deterministically from sha256(name + "_data" when data_obs is integer) as N(0, 5)·blind_additive_scale.
    So every real-data fit with the same parameter name shares ONE offset.
  - `--externalPostfit` copies the stored BLINDED x verbatim, with no offset correction, so a warm start lands on exactly the
    seed's physical point.
  - Trap: seeding across frames moves the physical start by the offset difference. That happens with a seed from an
    Asimov/MC card, from a non-integer-data card, or from a run with `--unblind` / a different `--blindingGroup` /
    blind_additive_scale.
  - A COLD start begins at x0default in the blinded frame, i.e. physical = default + offset, far off in `alphaS`.
- T4 launched (09:49 onward). Step 0, s = 0.5, 3 seeds: the NP draw costs +1.3k to +7.7k and the non-NP kick +0.56k to +0.84k,
  so the NP draw is 68–91 % of the start cost (the cross term is up to +2.2k at large λ2). Ranges kept.
  All 10 starts are finite, 1.2k–11.5k above NOMSTIFF. 3 running, 7 queued; expect all done around 22:00–24:00.
  Check with `bash 261001-census-nominal/scripts/status.sh`.
  Note: there is no `WRemnantsHelpers/scripts/mem_gate.sh`; the canonical copy is `studies/alphas-scan-discontinuity/scripts/mem_gate.sh`.
- Luca: go for T4, configuration confirmed (walled, margin 0, τ 8, new cache, card A, lattice, λ4_ν = 0).
  Dispatched [261001-census-nominal](261001-census-nominal/LOGBOOK.md), from reference NOMSTIFF:
  - first a seed-cost split (NP draw vs non-NP kick, s = 0.5);
  - then 8 perturbed + 2 cold-except-`alphaS` starts, earlyStopping 20, at most 3 at a time;
  - logs symlinked into the task dir.
- T2 [260930-stiff-wall-refits](260930-stiff-wall-refits/LOGBOOK.md) DONE: verdict "stiff wall is enough, no trust-constr".
  Overshoot past each face is at most 1.1e-6; XW's two-face walk took 3× the iterations of the one-face fits.
  T4 settings: about 3 h per start, earlyStopping ≥ 15, certify by EDM + faces (scipy `success` is False on every fit).
  Caveat: the no-lattice fits put λ2_ν exactly at 0, the edge of the cache's validity region.
- **Defaults changed (Luca: "margin = 0 and stiff wall should be default"). All UNCOMMITTED:**
  - `WRemnants/wremnants/postprocessing/scetlib_ad/np_damping_wall.py`: `NP_DAMPING_MARGIN` 5e-3 → 0. Docstring and knob
    comment updated, the example uses `--regularizationStrength 8`, and `margin=5e-3` reproduces old fits. Container
    black/isort pass; flake8 count unchanged (49, all pre-existing).
  - `WRemnantsHelpers/workflows/fitterAD.sh`: `--wall` now gives `--regularizationStrength 8 ... NPDampingMapping margin=0`,
    written explicitly so the margin is recorded in every fit's meta_info.
  - `WRemnantsHelpers/scripts/fit_summary_plotly.py`: a fit with no margin keyword is labelled "default (5e-3 before 2026-10-01)".
  - `knowledge/30_physics_global/np_parametrization_constraints.md`: the default is restated.
  - Not touched: `workflows/fitterSCETlibNP.py`, which drives the OLD scetlib_np model, whose wall module no longer exists.
- runs_ad.yaml: the three T2 fits added under a new "stiff wall" block. The table was rebuilt at
  ~/public_html/alphaS/260925_fit_summary_ad/fit_summary.pdf; the pdf was compiled outside the container, since there is no
  pdflatex inside.
- T2 fits finished (by 17:55 on 09-30). XL4ZSTIFF: NLL 372.2832, EDM 3.4e-17, 42 iterations, Δ`alphaS` −0.024σ vs Y35ZWALLL4ZR.
  Against XWSTIFF: ΔNLL +0.955, Δ`alphaS` +0.259σ (old wall: 0.907 and 0.25σ). The two-route ambiguity in the no-lattice
  configuration does not depend on the margin. The T2 worker was resumed to write up.

### 2026-09-30
- **T2 partial (orchestrator read at 17:37; the T2 worker died at the session restart, but its fits kept running):**

  | fit | NLL (τ=8, margin 0) | ref NLL (τ=5, 5e-3) | EDM | Δ`alphaS`/σ_ref | σ/σ_ref | iterations | new faces at 0 |
  |---|---|---|---|---|---|---|---|
  | NOMSTIFF | 376.6146 | 376.6942 | 3.0e-14 | **+0.012** | 0.999 | 40 (about 1.4 h) | L2(\|Y\|=2.5) = 0 (TMD small-b) |
  | XWSTIFF | 371.3284 | 371.4430 | 7.4e-18 | −0.038 | 0.999 | 127 (about 2.5 h; the reference took 10) | λ2_ν = 0, B(2.5) = 0; B(0) = 4.9e-4 |
  | XL4ZSTIFF | running (372.283 at iteration 42) | 372.350 | | | | | λ2_ν = 0 |

  - Nominal `alphaS` and σ(`alphaS`) are unchanged by removing the margin.
  - With the margin gone, EVERY fit slides onto the zero faces. The 5e-3 margin was hiding faces that the data push against.
  - XW now sits 4.9e-4 in B(0) from the TMD cliff onset. That is close; check the cache validity at this tune before trusting it.
  - The stiff wall converges (tiny EDM) but slowly. XW walked the face in a staircase: plateaus, then drops.
- 15:50 T2 status (orchestrator; the T2 worker's session ended, but the detached fits and the XL4Z queue script are alive):
  - NOMSTIFF: 75 min, 40 iterations, loss 376.694 → 376.6146 (still creeping, 2e-9/iteration, up to 714 s/iteration).
    It slid ONTO the margin-0 TMD small-b face: L2(|Y|=2.5) = 0.0000 (it was 0.0046, held by the 5e-3 margin).
  - XWSTIFF: 98 iterations, 371.438 → 371.333, descending in a staircase (flat stretches, then drops). The reference converged in
    10 iterations at τ = 5. It slides along both W faces towards 0: 3B(2.5) = 0.0000, λ2_ν = 0.0008, physical λ4 = −6e-5.
    B(0) = 4.6e-4, i.e. close to the B(0) = 0 cliff but on the safe side.
  - Read so far: with the margin removed, the data push BOTH configurations onto the new boundary. The minimiser shows the
    expected face-crossing difficulty (staircase, growing iteration cost). Not yet a verdict.
- T3 [260930-random-starts](260930-random-starts/LOGBOOK.md) DONE:
  - `make_random_starts.py` writes rabbit-snapshot-format seeds in blinded x, feasible at margin 0, with no `alphaS` leak.
  - The default s = 2 starts sit FAR uphill: ΔNLL +16k to +277k, against about 7.7k expected from the non-NP kick alone.
    For T4 use s ≈ 0.5–1 and separate the NP and non-NP contributions first.
  - Seeds must carry every parameter name: rabbit silently cold-starts any name that is missing.
  - The same `--seed` gives the same draws across references.
- Killed a stray `bfs / -name ad_kernel.hpp` filesystem crawler (2 h 50 m old), left by one of this session's agent shells.
- T1 [260930-wall-margin-keyword](260930-wall-margin-keyword/LOGBOOK.md) DONE:
  - `margin=` added. The default is bit-identical, and margin 0 matches the eager penalty to 1e-14 on the nominal fit.
  - Syntax: `--regularizationStrength 8 -r ...NPDampingWall ...NPDampingMapping margin=0`, with the margin after the mapping.
  - The margin is read at construction only; `fitterAD.sh --wall -f` can't pass it.
  - The diff in np_damping_wall.py is uncommitted and awaits Luca.
  - At the nominal fit the margin-0 wall is inactive everywhere.
  - Its λ2_ν = 0.063 is 2.3σ below the lattice term: the known ptll-shape tension (lattice-cs-kernel), not a card error.
- Dispatched T2 [260930-stiff-wall-refits](260930-stiff-wall-refits/LOGBOOK.md): NOM / XW / XL4Z warm refits at τ = 8,
  margin 0, at most 2 at a time.
- Luca: go. Dispatched [260930-wall-margin-keyword](260930-wall-margin-keyword/LOGBOOK.md) (T1: `margin=` on `-r`, no commit, one gated
  cache load) and [260930-random-starts](260930-random-starts/LOGBOOK.md) (T3: seed writer, blinded x only, feasible at margin 0).
- Study opened (Luca). Configuration fixed as above.
- **λ4_ν: float or freeze? (orchestrator read of existing evidence)**
  - Lattice alone (`lattice-cs-kernel/260923-scetlib-kernel-fit`): the free (λ2_ν, λ4_ν) fit prefers λ4_ν ≈ −0.006
    (UNPHYSICAL). Freezing at 0 costs Δχ² = 1.87 (about 1.4σ). So with λ4_ν ≥ 0 enforced, the lattice's best fit is AT the
    boundary λ4_ν = 0, and refitting the lattice with λ4_ν ≥ 0 reproduces the frozen fit's central value. What it adds is
    only a one-sided allowance.
  - CMS alone (card A, no lattice, new cache): λ4_ν free (Y35ZWALLWARM, λ4_ν = 0.043) vs frozen (Y35ZWALLL4ZR):
    2ΔNLL = 1.81. With the boundary, the LRT null distribution is ½χ²₀ + ½χ²₁, so p ≈ 0.09. AIC: Δ = 1.81 < 2, so no.
  - Neither dataset requires the parameter, and they pull in OPPOSITE directions (lattice negative, CMS positive).
  - For a nuisance in a measurement, the deciding question is not model selection but "does freezing it bias `alphaS` or
    shrink σ(`alphaS`)?". That is T8: one fit with λ4_ν floating (margin-0 wall at λ4_ν ≥ 0 plus a lattice term), against
    the frozen nominal.
  - Trap: the 2D Gaussian lattice constraint (±0.0567 / ±0.0040, ρ −0.911) is centred at λ4_ν < 0, and its conditional
    at λ4_ν = 0 gives λ2_ν = 0.108, against the direct refit's 0.1345 ("biased low", lattice-cs-kernel decision 2026-09-23).
    So T8 needs the actual lattice χ²(λ2_ν, λ4_ν) as the constraint term, or at least a Gaussian refit restricted to
    λ4_ν ≥ 0, NOT the 2D Gaussian.
- Removed a stray 65-byte file accidentally created at the WRemnants repo root by a worker's shell line (untracked).

---

## Findings

4. The `alphaS` profile of the nominal fit is single-valued over ±2σ (3 independent starts per point) and close to the Hessian parabola: [−0.985, +1.015] σ — (evidence: 261002-multistart-profile/LOGBOOK.md)

1. The nominal walled fit (card A + lattice, λ4_ν = 0, margin 0, τ 8, new cache) has ONE minimum across 10 broad starts; `alphaS` does not depend on the start — (evidence: 261001-census-nominal/LOGBOOK.md)
2. Removing the 5e-3 wall margin moves the nominal `alphaS` by +0.012σ and leaves σ(`alphaS`) unchanged — (evidence: 260930-stiff-wall-refits/LOGBOOK.md)
3. Restarting trust-krylov does not un-stick a crawl on an active stiff-wall face (CENS03R) — (evidence: 261001-census-nominal/LOGBOOK.md)

---

## Open questions

- Does the nominal (lattice) fit have more than one physical minimum?
- Does freezing λ4_ν = 0 bias `alphaS` or shrink σ(`alphaS`) (T8)?

---

## Decisions

- 2026-10-01 — wall default = margin 0, `--regularizationStrength 8` (module + fitterAD.sh) — T2: nominal α_s +0.012σ, overshoot ≤ 1.1e-6, warm fits converge (Luca).

- 2026-09-30 — every fit's live log is symlinked into its task dir `logs/` at launch and listed in START HERE — Luca follows fits from the web (Luca).
- 2026-09-30 — T2 fits drop the saturated / impacts / saveHists postfit products (main fit + Hessian only) — speed; T2 needs only the NLL, EDM, σ and λ's.

- 2026-09-30 — nominal configuration = card A + lattice (λ4_ν = 0, 1D λ2_ν term), new bin0xzero cache — AN nominal uses the
  lattice-constrained CS kernel (Luca).
- 2026-09-30 — wall margin 0 with a stiff wall (τ ≈ 8) first; trust-constr only if the minimiser struggles — cheaper, and a
  stiff relu² is exactly quadratic on the violated side (Luca).
