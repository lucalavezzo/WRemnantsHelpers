---
title: Restart the nominal walled fit at the cold walled minimum C
slug: 261005-cold-min-restart
study: walled-multistart-census
status: done          # active | done | paused | abandoned
created: 2026-10-05
updated: 2026-10-05
owner: study-worker
---

# Restart the nominal walled fit at the cold walled minimum C

**Task:** Started at the cold walled minimum C (CCWALLCOLDR), does the nominal stiff-wall fit (NOMSTIFF config: card A + lattice, lambda4_nu=0, new |Y|<=3.5 cache, tau=8, margin 0) return to NOMSTIFF's minimum or stay elsewhere? And (1b) does C survive the stiff wall in its own configuration (no lattice, lambda4_nu free; XWSTIFF config)?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-10-05 18:45)

> **1a: the nominal goes back to NOMSTIFF exactly. 1b: C survives the stiff wall as a distinct, certified, UNPHYSICAL minimum.**
> - **CMR1A** (lattice, λ4_ν ≡ 0, seeded at C) ends at NOMSTIFF: ΔNLL 4e-11, ‖Δθ/σ‖ 2.6e-7, EDM 1.8e-14. On the way it spent
>   1.5 h in a trust-radius crawl at +2.01, which was not a minimum.
> - **CMR1B** (no lattice, λ4_ν free) ends +0.670 above XWSTIFF, with EDM 1.2e-17 and Δ`alphaS` = +0.37σ_XW
>   (σ ratio 1.10). It sits at λ4_ν = −1.6e-4 and λ2_ν = 0, on the λ4_ν face (violated, wall cost 0.24) and the λ2_ν face.
>   That makes γ_ν > 0 at every b. It is C re-minimised: ‖Δθ‖ = 0.30σ_C, Δ`alphaS` = +0.03σ_C.
> Real data, `alphaS` blinded (differences only). Each fit is compared only with its own configuration's minimum. The cache is
> unvalidated at λ4_ν < 0.

- **Next action:** compare the vector-only term split (Result) with the exact one in `term_split_CMR1B.json`.
  - That file is written by `scripts/run_term_eval.sh`, queued detached in mem_gate (gate PID 2056198), which was blocked by
    node memory at 19:00. Log: [logs/term_eval.log](logs/term_eval.log), gate log: `logs/term_eval.gate`.
  - Its `[gate]` line must reproduce XWSTIFF's NLL (diff ≈ 1e-11) before its split is trusted.
  - Nothing else is pending. Physics review is advised before quoting.
- **Blocking on:** only that cross-check (node memory). All the results above are final.

---

## Log

### 2026-10-05 (final, evening)
- **Both fits finished with exit=0** (CMR1B at 17:55, CMR1A at 18:19). `analyze_restart.py --plot` gives `analysis.json` and `loss_trace.png`.
  `compare_C.py --plot` gives `compare_C.json` and `gamma_nu_CMR1B_C_XW.png`.
- **CMR1A: how it escaped the +2.0 crawl.**
  - Iterations 14–106 (about 1.5 h): the loss fell by a near-constant 7.5e-6 per iteration from +2.015 to +2.0117. That constant
    per-step gain is a collapsed trust radius taking fixed-size steps along a slope, not a stationary point.
  - From iteration 107 every accepted step gained about TWICE the previous one (1.5e-5, 3e-5, 6e-5, … up to 0.47 at it 125), i.e.
    the trust radius re-expanded by ×2 per step. By it 125 it was at +0.125, by it 134 at +8e-5, and from it 139 at NOMSTIFF to
    1e-10.
  - Parameter trajectory: NOT recorded. `--snapshotInterval` overwrites one file, so only the it-25 snapshot (λ2_ν 0.0185,
    on L2(2.5)) and the final point (λ2_ν 0.0643, on L2(2.5)) exist. What I can say: the face set did not change (L2(2.5) = 0 at
    the start of the crawl and at the end), and λ2_ν went 0.0185 → 0.0643. I cannot say which coordinate unlocked at it 107.
  - Final CMR1A = NOMSTIFF: ΔNLL 3.9e-11, ‖Δθ/σ_NOM‖ 2.6e-7 over all 3719 parameters, Δ`alphaS` 4e-8σ, EDM 1.8e-14.
- **CMR1B: a distinct certified walled minimum** (EDM 1.2e-17, Hessian computed, σ ratio 1.10). See Result.
- **Term split for CMR1B vs XWSTIFF.**
  - Exact: `scripts/term_eval.py`, a verbatim copy of census `step0_eval.py`, one gated cache load. Queued in mem_gate at
    18:29; still blocked by node memory at 19:00.
  - Vector-only estimate: `scripts/prior_split.py`. data+BB −0.48, syst priors +0.71, param-model priors +0.21, wall +0.24.

### 2026-10-05
- **Interim at 14:30 (snapshots at 14:25 / 14:26, `analysis_interim.json`, `loss_trace.png`).** These are NOT minima.

(The interim figure was regenerated at the end with the full traces; it is shown under Result.)

  | (snapshot) | loss − ref | Δ`alphaS`/σ_ref | ‖Δθ/σ_ref‖ (from seed) | λ2 | λ4 | δλ2 | λ2_ν | λ4_ν | faces on |
  |---|---|---|---|---|---|---|---|---|---|
  | CMR1A it 25 | +2.014 | −0.054 | 2.86 (0.72) | 0.0582 | 0.1123 | −0.0093 | 0.0185 | 0 (held) | L2(2.5) (= NOMSTIFF's face) |
  | CMR1B it ~17 | +0.749 | +0.324 | 418 (8.9) | 0.0787 | 0.1161 | −0.0091 | 0.0071 | **−2.2e-4** | λ4_ν (violated) |

  - **1a.** After 12 accepted steps the loss fell from +3.07 to +2.01. The run is now moving about 3e-5 per iteration. λ2_ν has
    gone 0.0073 → 0.0185 (NOMSTIFF: 0.064, lattice-pulled), and λ2 is drifting down onto the L2(2.5) = 0 face. Both are heading
    towards NOMSTIFF, but slowly, with every other step rejected. Remaining distance: λ2_ν −2.0σ, resumTNP_b_qg −1.0σ.
  - **1b.** The first 6 steps were rejected; then the loss fell by 0.305 in one step, and it has been crawling down since. The λ4_ν
    notch was NOT left. λ4_ν went further negative, −1.85e-4 → −2.2e-4, so the data gain inside the notch outweighs the τ = 8
    wall: the penalty is e^16·(2.2e-4)² ≈ 0.43, assuming λ4_ν ≥ 0 is the only violated face, which the analysis confirms.
    `alphaS` has stayed at C's +0.32σ_XW.
- **Start costs (iteration 0, walled loss − reference NLL; NLL is not blinded):**
  - CMR1A: 379.6883 − 376.6146 = **+3.07** above NOMSTIFF. The wall term at the seed is 0, so all of it is data + priors +
    the lattice term.
  - CMR1B: 372.4692 − 371.3284 = **+1.14** above XWSTIFF, of which **0.30 is the stiff wall's λ4_ν penalty** (computed). So C
    without its wall cost is only +0.84 above XWSTIFF on the new cache.
    For comparison: on the old cache with the τ = 5 wall, C − W was +1.235, about half of it wall (walled-two-minima).
  CMR1B's first step was rejected (same loss at iteration 1). (evidence: `logs/CMR1{A,B}.log`)
- **Launched (14:03 / 14:04)** through the shared `mem_gate.sh` (330 GB). Cache load 34 s (page cache warm).
  - CMR1A: NOMSTIFF's own meta_info command.
  - CMR1B: XWSTIFF's own meta_info command.
  Only `-o`, `--postfix`, `--snapshotFile`, `--externalPostfit` and `--earlyStopping` were changed. `--earlyStopping` is 20 in
  both: NOMSTIFF had 100, and XWSTIFF had none, which is rabbit's default of 20, so 1b is unchanged in effect. Each job runs the
  main fit plus its postfit Hessian, as in the census.
  (evidence: `logs/build_cmds.log`, `cmds/CMR1{A,B}.cmd`, `scripts/{build_cmds.py,run_fit.sh,launch.sh}`)
- **Seed mapping: C → the new frames** (`scripts/make_seeds.py`, `logs/make_seeds.log`, `seed_mapping.json`).
  1. *Parameter lists, mapped by name.*
     - 1a: NOMSTIFF has 3719 parameters and C has 3720. Every NOMSTIFF name is present in C. The only C parameter dropped
       is `lambda4_nu`, which is held at its anchor (0) in the lattice configuration. No parameter had to take NOMSTIFF's
       value. The seed nonetheless carries NOMSTIFF's full name list, because `load_fitresult` intersects names and any
       name missing from the seed would stay at its cold default.
     - 1b: XWSTIFF and C have identical name lists in identical order, so C's vector is used verbatim.
  2. *θ anchors.* θ = (λ − c0)/width, where c0 comes from the anchor of the card's theory correction (`param_model._resolve_anchor`,
     `anchor_source=correction`), not from the cache directly.
     - All three fits log the same correction tag (`..._LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_adcorrAV`)
       with "largest shift from the cache's own anchor: 0".
     - The two `cache.conf` files differ only in `Grid_Y` (the old cache stops at 2.5, the new one at 3.5).
     - All 16 param-model anchor values read from C's meta chain equal those of NOMSTIFF and XWSTIFF.
     - The REPARAM widths are today's code: the walled-chord gate reproduced C's stored NLL at its stored x with today's code.
     **So θ carries over 1:1 and no conversion was needed.**
  3. *`alphaS` blinding.* The offset is `blind_additive_scale × N(0, 5)`, seeded by sha256("alphaS" + "_data" if
     data_obs is all-integral). The SCETlib-AD model declares no scale, so the scale is 1.
     `scripts/blinding_check.py` builds rabbit's own `Blinding` on both cards. Both have integral data_obs (780 bins), and the
     **offsets are identical**. No offset value is printed. The blinded x of `alphaS` therefore carries over verbatim.
     As a cross-check, the walled-chord gate reproduced C's NLL with today's rabbit (2a59246), so C's stored x is in today's frame.
- **What C is, in each frame** (differences in σ of the reference, from `seed_mapping.json`; λ in physical units):

| | λ2 | λ4 | δλ2 | λ2_ν | λ4_ν | Δ`alphaS`/σ_ref | ‖Δθ/σ_ref‖ (param model / nuisances) | wall pen. at seed (τ 8) |
|---|---|---|---|---|---|---|---|---|
| C (CCWALLCOLDR, old cache, τ 5) | 0.0783 | 0.1186 | −0.0090 | 0.0073 | −1.85e-4 | | | |
| NOMSTIFF (ref 1a) | 0.0256 | 0.0876 | −0.0041 | 0.0643 | 0 (held) | | | 7e-6 |
| seed 1a = C, λ4_ν → 0 | as C | as C | as C | as C | 0 (held) | −0.064 | 3.43 (3.38 / 0.61) | 0 |
| XWSTIFF (ref 1b) | 0.1188 | −7e-5 | −0.0094 | −1e-6 | 0.0444 | | | 1e-5 |
| seed 1b = C | as C | as C | as C | as C | −1.85e-4 | +0.325 | 427 (427 / 0.41) | 0.304 (λ4_ν face) |

  - 1a: C and NOMSTIFF are both on the TMD-damping route (λ4 ≈ 0.09–0.12, λ4_ν ≈ 0). The largest differences are in
    λ2_ν (−2.49σ: C has no lattice term pulling λ2_ν up), λ2 (+1.23σ), λ4 (+1.14σ), resumTNP_b_qg (−1.01σ) and δλ2 (−0.72σ).
    PDF/TNP differences are ≤ 0.47σ (pdfEig28 +0.36). No wall face is active at the seed.
  - 1b: XWSTIFF is on the CS route (W), with λ4 = −7e-5 sitting on the B(2.5) face and λ2_ν on its face. Its σ(λ4) is the
    wall-pinned (meaningless) walled σ, which is why Δλ4 reads as 426σ. The physical gap is λ4 0.119 vs 0.000 and λ4_ν
    −1.85e-4 vs +0.044. C violates the λ4_ν ≥ 0 face by 1.85e-4, which costs 0.30 in the stiff wall.
  - The NLL at the seed will be read from each fit's iteration 0. No separate gated step-0 evaluation was run: it would be a
    third cache load on a shared node, and the wall term is computed above in numpy with the wall's own Conditions.

---

## Result

**Caveats first.**
- Real data, `alphaS` blinded: only differences are shown. The blinding offset is verified identical across the two cards.
- Each fit is compared with its OWN configuration's minimum: 1a (lattice, λ4_ν = 0) vs NOMSTIFF, 1b (no lattice, λ4_ν free)
  vs XWSTIFF. The two configurations have different objectives (lattice term, one parameter fewer), so their NLLs are never
  compared with each other.
- C (CCWALLCOLDR) was fit on the OLD 260827 cache (|Y| ≤ 2.5 build) with a τ = 5, margin 5e-3 wall. Its NLL (372.675) belongs
  to that objective and is not comparable.
- A wall-pinned λ has a meaningless walled σ: XWSTIFF's λ4 sits on B(2.5), and CMR1B's λ2_ν sits on its face. Those entries
  inflate any ‖Δθ/σ‖ by orders of magnitude, so the distance to C is also given in C's own σ.
- The AD cache has not been validated at λ4_ν < 0 (`knowledge/20_frameworks/scetlib_ad_cache_validity.md`). CMR1B lives there.

| | CMR1A (1a) | CMR1B (1b) |
|---|---|---|
| configuration = reference | NOMSTIFF (card A + lattice, λ4_ν ≡ 0) | XWSTIFF (card A, λ4_ν free) |
| start, loss − ref | +3.074 | +1.141 (wall 0.30 of it) |
| **final NLL − ref** | **+3.9e-11** | **+0.6697** |
| EDM | 1.8e-14 | 1.2e-17 |
| Δ`alphaS` / σ_ref | +4e-8 | **+0.366** |
| σ(`alphaS`) / σ_ref | 1.0000 | 1.103 |
| ‖Δθ/σ_ref‖ | 2.6e-7 (identical point) | 432 (λ4 wall-pinned in XWSTIFF; in σ_CMR1B it is 1241, dominated by λ4_ν) |
| top differences (σ_ref) | all ≤ 1.5e-7 | λ4 +432 (pinned σ), λ4_ν −4.0, λ2 −0.43, `alphaS` +0.37, QCDscaleZ PtV0_3 hel2 −0.18, lumi −0.16, QCDscaleZ PtV3_5 hel0 −0.11, weak_default −0.11, resumTNP_b_qg −0.11 |
| λ2 / λ4 / δλ2 | 0.0256 / 0.0876 / −0.0041 (= NOMSTIFF) | 0.0933 / 0.1204 / −0.0093 (XW: 0.1188 / −7e-5 / −0.0094) |
| λ2_ν / λ4_ν | 0.0643 / 0 held (= NOMSTIFF) | **−2.3e-7 / −1.64e-4** (XW: −1.1e-6 / +0.0444) |
| active faces (coeff < 1e-5) | L2(2.5) (= NOMSTIFF) | **λ4_ν (violated by 1.64e-4) + λ2_ν** (XW: λ2_ν + B(2.5)) |
| wall penalty e^{2τ}Σrelu² | ≈ 7e-6 | **0.240** (λ4_ν term; λ2_ν 5e-7) vs XW 1.1e-5 |
| iterations (rejected) | 151 (33) | 58 (14) |
| minimize / Hessian / wall time | 4.01 h / 11 min / 4.27 h | 3.43 h / 21 min / 3.85 h |
| scipy message | "bad approximation …" (stops at machine precision; the EDM certifies it) | same |

![loss trace](loss_trace.png)

*Walled loss minus the reference's NLL along each full restart, on a log axis. Points at or below 1e-9 are clipped to 1e-9, so
CMR1A's drop to NOMSTIFF (1e-10) shows at the floor. The loss is not blinded. Each curve's reference is the minimum of that fit's
own configuration (NOMSTIFF for 1a, XWSTIFF for 1b), so the two curves are not comparable with each other.*

**CMR1B term split vs XWSTIFF (data / constraints / BB / wall):** estimated from the stored vectors (`scripts/prior_split.py`, `prior_split_CMR1B.json`), with no cache load:

  | term | CMR1B − XWSTIFF |
  |---|---|
  | Gaussian priors on the card's 3673 systs, ½Σwθ² | +0.706 |
  | param-model priors (λ, TNP, PDF eig, envelope; σ = 1 in θ) | +0.208 |
  | NP wall, e^{16}Σrelu² | +0.240 (λ4_ν face; XW pays 1e-5) |
  | **data + BB (remainder)** | **−0.484** |
  | total reduced NLL | +0.670 |

  So C fits the DATA better than W by 0.48. It loses on nuisance priors (+0.91) and on the wall (+0.24).
  The syst-prior cost is spread over many small moves. The largest syst moves are the QCDscaleZ helicity terms, lumi and
  weak_default, each ≤ 0.18σ_XW. Per-parameter prior contributions were not computed. ASSUMPTION: rabbit's constraint term is ½Σw(θ−θ0)² with θ0 = 0 on real data. The exact split
  (`scripts/term_eval.py` = census `step0_eval.py`, one gated cache load, output `term_split_CMR1B.json`) is QUEUED in mem_gate.
  It was blocked at 18:30–19:00 by node memory (about 460 GB free, 480 needed). When it lands, check the estimate above against it.

**CMR1B is C, re-minimised on the new cache with the stiff wall** (`compare_C.json`):
- In C's own σ, ‖Δθ‖ = 0.295 over all 3720 parameters, and no parameter moved by more than 0.15σ_C. The largest moves are
  λ2_ν −0.15, λ2 +0.15, resumTransition2 −0.07 and pdfEig18/22 +0.07.
- Δ`alphaS`(CMR1B − C) = +0.034σ_C, and σ(`alphaS`) changed by a factor 0.93 relative to C.
- The visible change is λ2_ν: 0.0073 in C → 0 in CMR1B (on its face). It reads −30.6σ only in CMR1B's own σ, which is wall-pinned.
  λ4_ν went −1.85e-4 → −1.64e-4: the stiff wall pushes it out only 11 %.

**How unphysical is it?** γ_ν^NP(b) = −2·tanh((λ2_ν b² + λ4_ν b⁴)/2):

![gamma_nu at CMR1B, C, XWSTIFF](gamma_nu_CMR1B_C_XW.png)

*Lines are the tanh_2 CS kernel at each tune (formula from `np_damping_wall.py`, the same form SCETlib's Gamma_nu uses). The
dotted vertical line marks the cache's largest b_T (about 12.6 GeV⁻¹). C is the soft-wall, old-cache fit. γ_ν > 0 means
CS anti-damping.*

- **CMR1B:** λ2_ν ≈ 0, so γ_ν > 0 at EVERY b (the formal crossing is at b = 0.04 GeV⁻¹).
  - γ_ν = +1.6e-4 at b = 1, +0.013 at 3, +0.042 at 4, +0.21 at 6, +0.65 at 8, +1.35 at 10, +1.94 at 12.6 GeV⁻¹, i.e. it saturates
    at +λ∞_ν = +2.
  - So the anti-damping is negligible below b ≈ 3 GeV⁻¹ (qT ≳ 0.4 GeV) and order one beyond 7–8 GeV⁻¹. TMD damping
    (B ≈ 0.36, large) takes over there.
- **Soft-wall C:** γ_ν < 0 up to b = 6.27 GeV⁻¹ (minimum −0.07 near 4.5) and positive beyond (+0.29 at 8, +1.88 at 12.6).
- **XWSTIFF:** CS-damped, γ_ν → −2 by b ≈ 4. Its λ2_ν = −1.1e-6 (the τ-8 overshoot) gives a formal crossing at 0.005 GeV⁻¹,
  which is invisible.

**Physics read.**
1. With the stiff wall the nominal (lattice, λ4_ν = 0) fit started at C goes back to NOMSTIFF exactly (ΔNLL 4e-11), after a
   1.5 h trust-radius crawl at +2.01. That crawl was a minimiser artefact, not a minimum, so the nominal is single-valued from
   this start too.
2. In the no-lattice configuration, C survives as a certified minimum +0.67 above W (XWSTIFF), with Δ`alphaS` = +0.37σ_XW.
   It fits the data better than W by about 0.48 and pays it back in nuisance priors (+0.91) and in the wall (+0.24). It
   sits OUTSIDE the physical region: λ4_ν = −1.6e-4 is past the wall, paying 0.24. The stiff τ = 8, margin-0 wall does not
   remove C, because C is a narrow data notch whose pull beats e^{2τ}·relu² at this depth. A relu² wall is "exact" only up to
   the overshoot g/(2e^{2τ}), and g is large in the notch.
3. So C is excluded by the physics constraint (CS anti-damping at all b), not by the likelihood. Any statement that the
   cross-check configuration has "one walled minimum" needs a hard constraint (trust-constr) or a stiffer wall, or should
   simply be read as λ4_ν ≥ 0 imposed and C excluded. The nominal (λ4_ν ≡ 0) cannot reach C at all.

---

## Findings

1. C's θ maps 1:1 into both new frames. The anchors are identical (same correction; the caches differ only in Grid_Y), and the
   `alphaS` blinding offset is identical across the lattice and plain card-A cards. — (evidence: `logs/make_seeds.log`,
   `scripts/blinding_check.py`)
2. Seeded at C, the nominal stiff-wall fit (lattice, λ4_ν ≡ 0) returns to NOMSTIFF to 4e-11 in NLL. — (evidence: `analysis.json`)
3. With λ4_ν free, a τ = 8, margin-0 relu² wall does NOT remove C. C re-minimises to a certified minimum at λ4_ν = −1.6e-4 and
   λ2_ν = 0 (CS anti-damping at all b), +0.67 above W, with Δ`alphaS` = +0.37σ_W. A stiff relu² wall is not an exact constraint
   against a narrow data notch. — (evidence: `analysis.json`, `compare_C.json`) → knowledge candidate
   (`knowledge/20_frameworks/scetlib_ad_cache_validity.md` or the wall note).
4. trust-krylov can crawl at a fixed small trust radius for about 90 iterations (constant gain per step, +2.01 above the minimum)
   and then recover by itself (gain ×2 per step). A slow constant-rate loss decrease is not evidence of a minimum. — (evidence:
   `logs/CMR1A.log`, `loss_trace.png`)

---

## Open questions

- The C notch is at λ4_ν ≈ −1e-4..−2e-4. walled-two-minima found it to be a data-term feature where the cache shows ±1 % steps
  from discrete b_T sites, and it has never been validated against direct SCETlib. If CMR1B converges inside it, the τ = 8 wall
  is not "exact" for a notch this narrow: the wall equilibrium overshoot is g/(2e^{2τ}), and g is large in the notch.
