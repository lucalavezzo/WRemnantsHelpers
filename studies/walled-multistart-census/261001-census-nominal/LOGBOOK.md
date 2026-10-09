---
title: Census of nominal walled minima
slug: 261001-census-nominal
study: walled-multistart-census
status: done        # active | done | paused | abandoned
created: 2026-10-01
updated: 2026-10-02
owner: study-worker
---

# Census of nominal walled minima

**Task:** Does the NOMINAL walled fit (NOMSTIFF config: margin 0, τ=8, pdf62_y35_260921/merged_full_bin0xzero, card A, lattice CS, λ4_ν=0) have more than one physical minimum, in particular a deeper one than NOMSTIFF? Where is each, and does `alphaS` depend on which minimum the fit lands in?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-10-02)

> **No. The nominal walled fit has ONE minimum in this census: all 9 starts that converged landed on NOMSTIFF itself,
> so `alphaS` does not depend on where the fit starts.** The 9 are 7 of 8 perturbed starts and both cold starts, all
> beginning 1.2k–11.5k NLL above NOMSTIFF. They all agree with NOMSTIFF to |ΔNLL| ≤ 2.3e-10, Δ`alphaS` ≤ 6.7e-7 σ and
> ||Δθ/σ|| ≤ 3.6e-6 over all 3719 parameters. All sit on the same face, L2(|Y| = 2.5) = 0, with EDM ≤ 5.2e-12.
> The 10th start (CENS03) did **not converge** and is **not a minimum**: it crawled on the active wall face at +430
> (gradient 3.9, nuisances unrelaxed). It is reported, not dropped.
> Caveats: real data, blinded (only Δ`alphaS`); 10 starts can show a basin exists but cannot rule out a rare one.

- **Next action:** none; task closed. For the orchestrator:
  - the knowledge line on restarts (Finding 3);
  - runs_ad.yaml rows, if wanted (the census fits are identical to NOMSTIFF, so one row like "census ×9 = NOMSTIFF"
    is enough).
- **Blocking on:** nothing.

| fit | seed | result file | live log | gate log |
|---|---|---|---|---|
| CENS01 | pert_000 | `fitresults_CENS01.hdf5` | [logs/CENS01.log](logs/CENS01.log) | [gate](logs/CENS01.gate) |
| CENS02 | pert_001 | `fitresults_CENS02.hdf5` | [logs/CENS02.log](logs/CENS02.log) | [gate](logs/CENS02.gate) |
| CENS03 | pert_002 | not converged: snapshot `snapshot_fitresults_CENS03R.hdf5` | [CENS03](logs/CENS03.log), [CENS03R](logs/CENS03R.log) | [gate](logs/CENS03.gate), [R gate](logs/CENS03R.gate) |
| CENS04 | pert_003 | `fitresults_CENS04.hdf5` | [logs/CENS04.log](logs/CENS04.log) | [gate](logs/CENS04.gate) |
| CENS05 | pert_004 | `fitresults_CENS05.hdf5` | [logs/CENS05.log](logs/CENS05.log) | [gate](logs/CENS05.gate) |
| CENS06 | pert_005 | `fitresults_CENS06.hdf5` | [logs/CENS06.log](logs/CENS06.log) | [gate](logs/CENS06.gate) |
| CENS07 | pert_006 | `fitresults_CENS07.hdf5` | [logs/CENS07.log](logs/CENS07.log) | [gate](logs/CENS07.gate) |
| CENS08 | pert_007 | `fitresults_CENS08.hdf5` | [logs/CENS08.log](logs/CENS08.log) | [gate](logs/CENS08.gate) |
| CENS09 | cold_000 | `fitresults_CENS09PF.hdf5` (Hessian-only pass on the converged snapshot) | [CENS09](logs/CENS09.log), [CENS09PF](logs/CENS09PF.log) | [gate](logs/CENS09.gate), [PF gate](logs/CENS09PF.gate) |
| CENS10 | cold_001 | `fitresults_CENS10.hdf5` | [logs/CENS10.log](logs/CENS10.log) | [gate](logs/CENS10.gate) |

The result files are under `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261001_census_nominal/`.
`fitresults_CENS03.hdf5`, `fitresults_CENS03R.hdf5` and `fitresults_CENS09.hdf5` (about 99 kB each) are **unreadable
stubs** left by the SIGTERMs (h5py: "bad object header"); never use them. The analysis is `scripts/analyze_census.py --floor 1e-4 --plot`
(run in the container), which writes [analysis.out](analysis.out), `analysis.json` and `census_summary.png`. Its run without
a floor is [analysis_nofloor.out](analysis_nofloor.out). No process of this task is still running.

---

## Log

<!-- Newest first. What was tried, what happened, why — with an evidence path. -->

### 2026-10-02 (Step 3, after the orchestrator resumed me)
- `scripts/analyze_census.py` was extended for the two irregular fits:
  - CENS09's result is read from CENS09PF. Its iterations come from CENS09.log, its Hessian time from CENS09PF.log, and
    its wall time is the sum of the two.
  - CENS03 is described from the last `snapshot_fitresults_CENS03R.hdf5` (reason `signal-SIGTERM`). Its NLL split comes
    from `cens03_hybrid_eval.json`, which matches the last logged loss 806.5778 = 376.6146 + 429.963. It is flagged NOT CONVERGED.
  - Timings are now parsed directly from the logs. `loghist` only reads them after a scipy result dump, and there is none
    after a stall stop or a `--noFit` pass.
- First run without a floor ([analysis_nofloor.out](analysis_nofloor.out)) to see the pairwise distances, then
  `--floor 1e-4 --plot` ([analysis.out](analysis.out), `analysis.json`, `census_summary.png`). The floor choice is under
  Result.
- **Cross-check of the orchestrator's numbers: all reproduced.**
  - |ΔNLL| ≤ 2.26e-10 (CENS05 is the largest).
  - max |Δθ/σ| = 1.98e-6 on CENS08 (pdfEig3, EDM 5.2e-12). For all others it is ≤ 2.64e-7 (CENS02, on `alphaS`).
  - EDM ≤ 5.2e-12 for all 9.
  - 9 of 9 converged fits are the NOMSTIFF point.
- The orchestrator's statement "cost scaled with how far the start was" is only **partly** supported; see Result,
  "Minimiser cost". Within the census, iterations do not track the start distance (Spearman ρ = 0.25, p = 0.5, vs the
  step-0 ΔNLL; ρ = −0.12 vs the NP-λ distance). Against T2's warm refits, census starts cost 2–4× as many iterations.
  That comparison holds.
- Removed the first summary plot (`census_dnll_vs_dalphas`): all 9 points sat on top of each other at (0, 0), so it
  carried no information. It was replaced by the three-panel `census_summary`.

### 2026-10-01 (evening, while I was stopped; done by the orchestrator, recorded here)
- **The 7 queued fits (CENS03–08, CENS10) ran with `--earlyStopping 15 --stallRelTol 1e-11 --maxRestarts 0`** (Luca)
  instead of `--earlyStopping 20`. The original commands are kept as `cmds/CENS<NN>.cmd.orig_es20`. CENS01, 02 and 09
  ran with the original `--earlyStopping 20` (no restart happened in any fit). Only CENS08 actually stopped on the stall rule
  ("Minimizer still stalling ... after 0 restart(s) and the loss was still coming down"), at EDM 5.2e-12. It is still the
  NOMSTIFF point, to 3.6e-6 σ.
- **CENS09** (cold start) converged ("A bad approximation...", snapshot reason `converged`, ΔNLL 2.7e-11). It was then
  SIGTERM'd. rabbit's SIGTERM handler writes a snapshot and **exits**, so no Hessian was computed. The Hessian came from a
  `--noFit` pass on that snapshot, **CENS09PF** (`cmds/CENS09PF.cmd`, 14:15–14:56, EDM 1.1e-15). CENS09PF is CENS09's result.
- **CENS03** (pert_002, start +1950) crawled:
  - It reached 806.85 by iteration 39, then 806.704 at iteration 128 (2.7 h). It was SIGTERM'd at 16:47.
  - It was restarted from its snapshot as **CENS03R** (`cmds/CENS03R.cmd`, the same flags). That gave 806.704 → 806.578
    in 260 iterations (4.5 h), loss falling about linearly and slowing down. It was SIGTERM'd again at 21:31.
    **The restart did not help.**
- **CENS03 diagnosis** (orchestrator: `scripts/run_hybrid_eval.sh`, one gated load with `step0_eval.py`, output
  [cens03_hybrid_eval.json](cens03_hybrid_eval.json)):
  - At the CENS03R snapshot, ΔNLL = +429.96 = data +5.59, constraints +423.26, BB-stat +0.68; |grad|max = 3.93.
    That is not a stationary point. The fit is crawling with unrelaxed nuisances: eff-stat carries (25.5/29.3)² = 76 % of
    ||Δθ/σ||², which my family split confirms.
  - A hybrid point, CENS03R's param-model parameters with NOMSTIFF's nuisances, gives +115 (data +99.7). That is inconclusive.
  - Classified as "not converged, not a minimum".

### 2026-10-01
- **Seeds written** (no cache load; `scripts/make_seeds.sh` → `logs/make_seeds.log`). Generator: T3's
  `make_random_starts.py`, run read-only from `../260930-random-starts/scripts/`. `--ref` NOMSTIFF, master `--seed 20261001`
  (T3's test draws used 20260930).
  - census, perturbed: `--n 8 --s 0.5 --alphas-u 2`, default T3 physical boxes (λ2 ∈ [0, 0.5], λ4 ∈ [0, 0.3],
    δλ2 ∈ [−0.03, 0.01], λ2_ν ∈ [0, 0.3]); every seed accepted on the first draw, none near-active.
  - census, cold: `--mode cold_except_alphas --n 2 --cold-alphas-u 2`. Everything at rabbit's x0default (the NP λ's at
    the runcard anchors λ2 = 0.4, λ4 = 0.4, δλ2 = 0, λ2_ν = 0.15), only `alphaS` differs (u = −0.88, −0.97 σ_ref, blinded x).
  - step-0 variants for seeds 000-002 (same master seed, so component-identical to census pert_000-002):
    (a) `a_nponly` = `--s 0 --alphas-u 0`; (b) `b_nonnponly` = `--alphas-u 0 --no-np-draw`; (c0) `c0_both_noalphas` =
    `--alphas-u 0`; (c) = the census pert_000-002 themselves (with `alphaS` u). The generator flags (b) as "not feasible
    at margin 0" only because NOMSTIFF itself sits 9.2e-7 past the L2(|Y|=2.5) face (the τ = 8 overshoot); harmless.
  - Seeds: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261001_census_nominal/seeds/` (+ `step0/`). Manifests
    copied to [seeds/](seeds/).
  - Quadratic expectation for the non-NP kick: s²·z·z/2 = 0.25 × (3640–3950)/2 ≈ 455–495 NLL.
- **Census commands** built by `scripts/build_cmds.py` from NOMSTIFF's own `meta_info["command"]` → `cmds/CENS<NN>.cmd`
  (`cmds/seedmap.csv`). Exactly 5 tokens change: `-o`, `--postfix`, `--snapshotFile`, `--externalPostfit`, `--earlyStopping
  100 → 20`. τ 8, `-r ... NPDampingMapping margin=0`, card, cache, freeze list, `prior_sigmas`, threads unchanged.
  CENS01-08 = pert_000-007, CENS09/10 = cold_000/001.
- Versions: WRemnants df3c30f7 + uncommitted `np_damping_wall.py` diff, now md5 81d32026… (T2 ran with 060a9a36…; the
  difference is the orchestrator's default-margin change 5e-3 → 0 + docstrings; our command passes `margin=0` explicitly,
  so the loss is the same). rabbit 2a59246, scetlib 2dd978a — same as NOMSTIFF.
- The task brief names `WRemnantsHelpers/scripts/mem_gate.sh`; it does not exist. Using the canonical v3 gate
  `studies/alphas-scan-discontinuity/scripts/mem_gate.sh` (md5-identical to every study-local copy), run unmodified.
- Node at 09:39: 1316 GB available, my threads 281; only other big job jbenke's 55 GB rabbit fit.
- Step 0 launched 09:39:52 through the gate (`logs/step0.gate`, `logs/step0.log`, `scripts/step0_eval.py`); done
  09:49 (load + model 235 s, 21 evaluations 3–35 s each). Result in the Result section: NP draw dominates, all finite.
- 09:49:26 queue `scripts/queue.sh` started (PID 1213883; at most 3 of ours alive or gating, and MemAvailable ≥ 500 GB,
  each launch through `mem_gate.sh 330`). CENS01 09:49:27, CENS09 09:53:27, CENS02 09:57:27. All three: wall "armed on
  5 of 8 condition(s) at margin=0", `alphaS` blinded, and iteration-0 loss = 376.615 + the step-0 start ΔNLL (warm
  full-vector load confirmed). Node after the third load: 393 GB available, my threads 6287.
- `scripts/analyze_census.py` (Step 3) written and smoke-tested against NOMSTIFF alone (lists unfinished fits with their
  state). Helpers copied: `scripts/loghist.py` (T2), `scripts/plot_output.py` (T3's local copy of scetlib_np's
  save_plot; that module is not on this WRemnants branch).

## Result

### Step 0: what a census start costs, NP draw vs non-NP kick (done)

**Caveats first.** Real data, blinded. NLL differences to NOMSTIFF on NOMSTIFF's own objective (walled, τ = 8,
margin 0), evaluated in one gated load of the same Fitter rebuilt from NOMSTIFF's `meta_info` command. Gate:
`reduced_nll(NOMSTIFF) − stored nllvalreduced = 0.0`. These are start costs, not fit results. The iteration-0 loss of each
launched fit reproduces these numbers (CENS01 6940.587 = 376.615 + 6563.97), so rabbit loaded the seeds as intended.

Components: total ΔNLL (Δ data / Δ constraints / Δ BB-stat). (a) NP draw only: non-NP and `alphaS` at NOMSTIFF.
(b) non-NP kick only (s = 0.5): NP and `alphaS` at NOMSTIFF. (c0) both, `alphaS` at NOMSTIFF. (c) the census seed itself
(c0 plus the `alphaS` kick u). "NP share" = a / (a + b).

| seed | (a) NP only | (b) non-NP only | (c0) both | c0 − a − b | (c) census seed | NP share |
|---|---|---|---|---|---|---|
| 000 | +5660 (+5022 / −0 / +641) | +557 (+63 / +487 / +8) | +6778 (+5583 / +486 / +710) | +561 | +6564 (+5393 / +486 / +687), u = −0.12 | 0.91 |
| 001 | +7729 (+6865 / −0 / +865) | +841 (+322 / +477 / +42) | +10733 (+9125 / +476 / +1132) | +2163 | +11535 (+9840 / +476 / +1219), u = +0.38 | 0.90 |
| 002 | +1286 (+1136 / −0 / +150) | +593 (+119 / +459 / +15) | +1870 (+1246 / +459 / +165) | −8 | +1950 (+1321 / +459 / +171), u = −0.93 | 0.68 |

Source: [step0_seed_cost.json](step0_seed_cost.json), log `logs/step0.log`.

Read:
- **The NP draw dominates** (68–91 %), so the NP boxes stay as T3 set them. The NP cost is almost all data (Δln) plus
  its BB-stat partner; the constraint term barely moves (Δlc ≈ −0.3, not attributed: it does not track the λ2_ν
  distance to the lattice centre, so the lattice term is presumably carried elsewhere in the card, not checked).
- **The non-NP kick costs what the Gaussian picture says, in the constraint term:** Δlc = 459–487, against
  s²·z·z/2 = 455–495 from the manifest. Its data term (63–322) is extra: the postfit covariance is not the
  curvature at a point this far off.
- The two are **not additive**: c0 − a − b is +561 and +2163 for seeds 000 and 001, which have a large λ2 (0.45–0.47);
  it is −8 for seed 002 (λ2 = 0.24). Far from the reference in λ, the non-NP kick no longer points along a flat direction.
- The `alphaS` kick (u ≤ 1σ) moves the start NLL by −214 to +802. At these points the data pull on `alphaS` is large, so
  even a sub-σ move is not small. That costs nothing: it is the start, not the answer.
- All 10 census seeds are finite, NLL and gradient, with wall penalty 0 (all strictly inside the physical region).
  Start ΔNLL: 1182 (pert_004) to 11535 (pert_001); the two cold starts +10116 and +9777. No seed needed a redraw.

### Census (Step 3): one minimum, the NOMSTIFF point

**Caveats first.**
- Real-data fits, `alphaS` blinded. Only blinded differences to NOMSTIFF of the same parameter, in the same
  integer-count data family, are shown, in units of σ_NOMSTIFF. No absolute `alphaS` was computed or saved.
- Every fit uses NOMSTIFF's objective: card A + lattice, λ4_ν held at 0, τ = 8, margin 0, the `bin0xzero` cache, and the
  same code (WRemnants df3c30f7 plus the uncommitted wall diff, rabbit 2a59246, scetlib 2dd978a). So NLLs compare directly.
- Minimiser flags differ between fits (earlyStopping 20 vs 15 + stallRelTol 1e-11 + maxRestarts 0; see Log). That changes
  only where a fit stops, not the objective, and every converged fit is certified by its EDM.
- CENS03 is shown at its last snapshot. It is **not a minimum**. It is kept in the tables and in the figure, not dropped.
- Ten starts: 8 drawn uniformly over the physical NP box with s = 0.5, plus 2 cold starts. A basin that catches
  ≲ 10 % of starts could still be missed. "One minimum" means one minimum **found**.

**Same-minimum criterion.** Two fits are the same minimum if |ΔNLL| < 1e-4 AND ||Δθ/σ_NOMSTIFF|| < 1e-4, over all 3719
parameters (single linkage).
- **The re-convergence floor:** re-converged fits sit 2.3e-7 to 5.4e-7 from NOMSTIFF, 9e-9 to 3.9e-7 from each other,
  and CENS08 sits at 3.6e-6.
  - This matches the EDM scale √(2·EDM): 2.4e-7 for EDM 3e-14 (NOMSTIFF), 3.2e-6 for CENS08's 5.2e-12.
  - The best-converged census fits (CENS04, 05, 07, 10) sit about 1e-8 from each other but 2.7e-7 from NOMSTIFF. NOMSTIFF itself is
    the least converged member (EDM 3e-14).
- The next-nearest object is CENS03, at 29 (and +430 in NLL). So any floor between 4e-6 and 29 gives the same clustering;
  the 1e-4 used here is not tuned.

**Per start** (from [analysis.out](analysis.out); faces evaluated at margin 0, a face is "on" when its coefficient is
< 1e-5). Columns:
- "start ΔNLL" is the Step 0 start cost. ΔNLL and EDM are at the end of the fit.
- "iters" counts minimiser iterations (CENS03: CENS03 + CENS03R). "rej (run)" is rejected steps (longest run).
- "min / hess / wall" is in h / min / h; the wall time is from the run stamps, with up to 3 fits running at once.
- "stop" is how the minimiser ended. "bad approx" is scipy's "A bad approximation caused failure to predict
  improvement", the normal exit for these fits.

| fit | seed | start ΔNLL | minimum | ΔNLL | EDM | Δ`alphaS`/σ | σ ratio | ‖Δθ/σ‖ | largest \|Δθ/σ\| | faces on | iters | rej (run) | min / hess / wall | stop |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CENS01 | pert_000 | +6564 | M0 | +1.2e-10 | 8.9e-15 | +1.4e-7 | 1.000000 | 3.2e-7 | `alphaS` 1.4e-7 | L2(2.5) | 95 | 23 (4) | 3.6 / 19 / 4.0 | bad approx |
| CENS02 | pert_001 | +11535 | M0 | −1.6e-10 | 3.0e-14 | +2.6e-7 | 1.000000 | 5.4e-7 | `alphaS` 2.6e-7 | L2(2.5) | 173 | 48 (9) | 3.8 / 14 / 4.1 | bad approx |
| **CENS03** | pert_002 | +1950 | **not converged** | **+430.0** | — | **−0.17** | — | **29** | effStat_trigger 1.8 | L2(2.5) | 129 + 261 | 73 (7) | — / — / 7.6 | SIGTERM ×2 |
| CENS04 | pert_003 | +9019 | M0 | +3.2e-11 | 2.9e-17 | +1.1e-7 | 1.000000 | 2.7e-7 | `alphaS` 1.1e-7 | L2(2.5) | 145 | 34 (5) | 4.7 / 19 / 5.1 | bad approx |
| CENS05 | pert_004 | +1182 | M0 | +2.3e-10 | 3.4e-17 | +1.1e-7 | 1.000000 | 2.7e-7 | `alphaS` 1.1e-7 | L2(2.5) | 110 | 25 (8) | 5.6 / 23 / 6.1 | bad approx |
| CENS06 | pert_005 | +5828 | M0 | −1.9e-11 | 1.1e-15 | +7.6e-8 | 1.000000 | 2.3e-7 | γ_ν 8.8e-8 | L2(2.5) | 83 | 26 (9) | 2.7 / 15 / 3.0 | bad approx |
| CENS07 | pert_006 | +3630 | M0 | +1.1e-10 | 5.6e-15 | +1.1e-7 | 1.000000 | 2.8e-7 | `alphaS` 1.1e-7 | L2(2.5) | 132 | 30 (6) | 6.8 / 22 / 7.3 | bad approx |
| CENS08 | pert_007 | +9623 | M0 | −2.2e-11 | 5.2e-12 | −6.7e-7 | 1.000000 | 3.6e-6 | pdfEig3 2.0e-6 | L2(2.5) | 175 | 47 (11) | 6.0 / 6 / 6.2 | stall stop |
| CENS09 | cold_000 | +10116 | M0 | +2.7e-11 | 1.1e-15 | +1.1e-7 | 1.000000 | 2.8e-7 | `alphaS` 1.1e-7 | L2(2.5) | 90 | 22 (4) | 4.2 / 33 / 5.0 | bad approx → SIGTERM, Hessian from CENS09PF |
| CENS10 | cold_001 | +9777 | M0 | +1.3e-11 | 5.2e-17 | +1.1e-7 | 1.000000 | 2.8e-7 | `alphaS` 1.1e-7 | L2(2.5) | 110 | 27 (4) | 4.7 / 15 / 5.1 | bad approx |

The ||Δθ/σ|| split by parameter family for every fit (`alphaS`, NP λ, resum TNP, PDF, QCD scale, muon calibration,
eff stat, eff syst, other) is printed in [analysis.out](analysis.out). For the 9 converged fits no family exceeds
2.9e-6 (CENS08, PDF); for the others every family is ≤ 3.1e-7.

**Per minimum.**

| minimum | starts reaching it | NLL − NLL(NOMSTIFF) | Δ`alphaS`/σ | σ(`alphaS`) ratio | faces on (margin 0) | λ2 | λ4 | δλ2 | λ2_ν (λ4_ν held 0) |
|---|---|---|---|---|---|---|---|---|---|
| **M0 = NOMSTIFF** | **9 of 10** (7/8 perturbed, 2/2 cold) | ≤ 2.3e-10 in magnitude | ≤ 6.7e-7 in magnitude | 1.000000 | L2(\|Y\|=2.5) = 0 only | 0.025581 | 0.087583 | −0.004093 | 0.064270 |
| (not a minimum) CENS03 snapshot | 1 of 10 | +430.0 (data +5.6, constraints +423, BB +0.7) | −0.17 | — | L2(2.5) = 0 | 0.0460 | 0.0847 | −0.00736 | 0.0584 |

The λ's are physical values (anchors λ2 = λ4 = 0.4, δλ2 = 0, λ2_ν = 0.15 from the runcard; λ_inf = 1, λ_inf_ν = 2,
λ4_ν = 0 held). They are identical to 6 digits across all 9 M0 fits.
At M0 the other armed faces have slack: λ2_ν 0.064, L2(0) 0.026, B(0) 0.263, B(2.5) 0.263.

![Census summary: (a) |ΔNLL| vs ||Δθ/σ|| to NOMSTIFF, log-log, with the same-minimum cuts dashed; the 9 converged starts cluster at about (3e-7, 1e-10), CENS03 sits alone at (29, 430). (b) Δalpha_S/σ per start: 0 for all 9 converged, −0.17 for the unconverged CENS03. (c) minimiser iterations vs step-0 start ΔNLL.](census_summary.png)

*Figure caveats:* real data, blinded differences only. The red point (CENS03) is an **unconverged** snapshot, not a
minimum. Its −0.17σ is where a stuck fit happens to be, not a second answer. In (a), |ΔNLL| is plotted because 3 of
the 9 converged fits sit *below* NOMSTIFF by ≤ 1.6e-10, which is round-off. Panel (c) iterations are what the fit ran,
under two early-stopping settings (see caveats).

**Minimiser cost.**
- Converged starts took 83–175 iterations and 2.7–6.8 h in `minimize()` (3 fits at a time on a shared node, so wall
  times are only indicative). The Hessian took 6–33 min.
- Compared with T2's warm NOMSTIFF refit (41 iterations, 1.2 h, starting 0.08 NLL away), starting 10³–10⁴ away costs
  2–4× the iterations. In that coarse sense the cost scales with the distance of the start.
- **Within** the census it does not:
  - iterations vs step-0 ΔNLL: Spearman ρ = +0.25 (p = 0.52);
  - iterations vs the NP-λ distance (box-normalised): ρ = −0.12 (p = 0.75);
  - `minimize()` time vs ΔNLL: ρ = −0.25.
  The closest start, CENS05 (+1182), took 110 iterations. The second closest, CENS03 (+1950), never converged.
  What decides the cost is the path the fit takes onto the active face, not how far the start is.

**CENS03: why it is not a second minimum.**
- **Not stationary:** it has |grad|max = 3.9, against ≤ 1e-5 at a certified minimum.
- **The excess is all in the constraints:** of its +430, 423 is constraint penalty and only 5.6 is the data term.
  The fit has matched the data almost as well as NOMSTIFF, but with ~3700 nuisances still displaced: ||Δθ/σ|| = 29, of
  which eff-stat is 25.5 (76 % of the squared norm).
- **It sits on the same face as M0**, L2(|Y| = 2.5) = 0 (coefficient 1e-8), at a different point on it: λ2 = 0.046 vs
  0.026 and δλ2 = −0.0074 vs −0.0041, with λ2 + 6.25 δλ2 = 0 in both.
- **The loss kept falling:** −0.13 over the 260 restarted iterations, about linearly and slowing down. That is the
  "stuck, not slow" signature in the fit-queue skill.
- **Interpretation:** sliding along a face held by a τ = 8 wall (curvature e¹⁶ normal to the face) makes the trust-region
  subproblem ill-conditioned. Each step is held to a tiny radius, while the thousands of nuisances need many small
  coordinated moves to relax.
- **Not tested:** whether a fit continued from this point would reach M0. The +115 hybrid point (its param-model
  parameters + NOMSTIFF's nuisances) is not a minimisation, so it decides nothing.

### Physics read

With an exact physical constraint on the NP damping (margin 0, stiff wall), the nominal fit is **unimodal as far as
10 random starts can tell**. That includes two starts from the cold anchors and starts spread over the whole physical
NP box (λ2 up to 0.47, λ2_ν up to 0.27).
- Every converged start ends at the NOMSTIFF point: the same NP tune, on the same single active face L2(|Y| = 2.5) = 0
  (TMD small-b turn-on at the edge of the gen acceptance), with the same `alphaS` to 7e-7 σ and the same σ(`alphaS`).
- So, in the nominal configuration, **`alphaS` does not depend on the start**, and NOMSTIFF is the (found) global
  walled minimum. There is no deeper one.
- This contrasts with the earlier configurations:
  - The unwalled likelihood is multimodal, with an unphysical global optimum (np-wall-local-minima).
  - The no-lattice card-A fit has two damping routes 0.96 NLL and 0.26σ in `alphaS` apart (T2).
  - The lattice term on λ2_ν and λ4_ν = 0 remove the CS-sector freedom that made the second route possible. What is left
    has one basin.
- The one non-converged start is a minimiser pathology, not physics: a crawl along the active face, with nuisances still
  displaced. It is fixable by better minimisation, not a competing solution. Its momentary −0.17σ in `alphaS` shows what
  an uncertified fit could report, so certify by EDM and gradient.


---

## Findings

1. **The nominal walled fit (card A + lattice, λ4_ν = 0, margin 0, τ = 8, bin0xzero cache) has one minimum in a 10-start
   census.** 9 of 9 converged starts (7 perturbed, 2 cold) re-converge onto NOMSTIFF: |ΔNLL| ≤ 2.3e-10, Δ`alphaS` ≤ 6.7e-7 σ,
   ||Δθ/σ|| ≤ 3.6e-6, the same face L2(|Y|=2.5) = 0, EDM ≤ 5.2e-12. `alphaS` is start-independent — (evidence:
   `analysis.out`, `analysis.json`, `census_summary.png`).
2. The distance between re-converged fits follows the EDM scale √(2·EDM): about 2e-7 σ at EDM 1e-14, about 3e-6 σ at
   5e-12. A reproducible "same minimum" floor is therefore set by the EDM, not chosen by hand — (evidence:
   `analysis_nofloor.out` pairwise matrix).
3. **For knowledge (`rabbit_minimizer_tolerances.md`): restarting trust-krylov from its own snapshot does not un-stick a
   crawl on an active stiff-wall face.** CENS03R went 806.704 → 806.578 in 260 iterations (4.5 h), at |grad| 3.9 and
   +423 in unrelaxed constraints. Such a crawl looks like slow convergence, but it never certifies (no EDM), and it can
   sit 0.17σ away in `alphaS` — (evidence: `logs/CENS03R.log`, `cens03_hybrid_eval.json`).
4. Start cost: at s = 0.5 the uniform NP box draw (not the non-NP kick) dominates the start NLL (68–91 %). Census starts
   cost 2–4× the iterations of a warm refit, but within the census the iteration count does not track the start distance
   (Spearman ρ = 0.25 vs the start ΔNLL, −0.12 vs the NP distance) — (evidence: `step0_seed_cost.json`, `analysis.json`).
5. rabbit's SIGTERM handler snapshots and exits, so a SIGTERM after convergence loses the Hessian. Recovery is a `--noFit`
   pass on the snapshot (CENS09 → CENS09PF, EDM 1.1e-15). It leaves an unreadable ~99 kB `fitresults_*.hdf5` stub
   behind — (evidence: `logs/CENS09PF.log`).
6. `--earlyStopping 15 --stallRelTol 1e-11 --maxRestarts 0` stopped one fit (CENS08) on the stall rule at EDM 5.2e-12,
   still the right minimum (3.6e-6 σ). The others ended on scipy's normal "bad approximation" exit — (evidence:
   `logs/CENS08.log`).

---

## Open questions

- Would a basin that catches fewer than about 10 % of starts show up with more starts? 10 starts cannot exclude one. A
  cheaper probe would aim starts at the other faces (λ2_ν → 0, B(0) → 0) rather than draw them uniformly.
- Would CENS03 reach M0 if it were driven off the face, for example with a softer τ for a few iterations and then τ = 8, or
  with BFGS? Not tested (out of scope).
- The constraint change Δlc ≈ −0.3 at the NP-only starts (step 0) is not attributed.
