---
title: Multistart profile of alphaS at ±1σ, ±2σ
slug: 261002-multistart-profile
study: walled-multistart-census
status: done          # active | done | paused | abandoned
created: 2026-10-02
updated: 2026-10-04
owner: study-worker
---

# Multistart profile of alphaS at ±1σ, ±2σ

**Task:** Is the profile likelihood of `alphaS` single-valued in the nominal (NOMSTIFF) configuration — at fixed Δα_s = −2σ, −1σ, +1σ, +2σ, do independent starts (warm / perturbed / PDF+TNP-kicked) with `alphaS` frozen converge to the same point?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-10-04 18:10): DONE

> **Yes: the profile likelihood of `alphaS` in the nominal configuration is single-valued at −2σ, −1σ, +1σ and +2σ.**
> All 12 fits converged (3 starts × 4 points: warm, census-perturbed, 2σ PDF/TNP kick). At every point the three starts
> are the same solution: |ΔNLL| ≤ 4.2e-10 and ||Δθ/σ|| ≤ 1.6e-5 over the 3718 floating parameters, with EDM ≤ 2.5e-10.
> 2ΔNLL is 4.271 at −2σ, 1.032 at −1σ, 0.972 at +1σ and 3.786 at +2σ, i.e. 1.000 k² − 0.030 k³ + 0.002 k⁴.
> 2ΔNLL = 1 at **[−0.985, +1.015] σ_NOM**.
> Caveats: real data, blinded (differences only), nominal configuration, independent fits with `alphaS` frozen.
> Three of the ±2σ results (PROFM2RS, PROFM2KS, PROFP2WS) come from fits resumed from their own pre-kill snapshots,
> after the originals were SIGKILLed (exit 137).

- **Next action:** none; task closed. For the orchestrator, a knowledge candidate is Finding 5 (the fitresult stub).
- **Blocking on:** nothing. No process of this task is running: the watcher exited at 17:56 once all heads had finished,
  and the queue exited on 10-03.
- **Regenerate everything:** `bash scripts/incontainer.sh python3 scripts/analyze_profile.py --plot > analysis.out`
  - Outputs: [analysis.out](analysis.out), `profile.json` and `profile_alphas_multistart.png`.

Status: `bash /home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/walled-multistart-census/261002-multistart-profile/scripts/status.sh`

| fit (chain) | point k | start | result | live logs |
|---|---|---|---|---|
| PROFM1W | −1 | warm | done | [PROFM1W](logs/PROFM1W.log) |
| PROFM1R | −1 | perturbed | done (stall stop) | [PROFM1R](logs/PROFM1R.log) |
| PROFM1K | −1 | PDF/TNP kick | done | [PROFM1K](logs/PROFM1K.log) |
| PROFP1W | +1 | warm | done | [PROFP1W](logs/PROFP1W.log) |
| PROFP1R | +1 | perturbed | done | [PROFP1R](logs/PROFP1R.log) |
| PROFP1K | +1 | PDF/TNP kick | done | [PROFP1K](logs/PROFP1K.log) |
| PROFM2W | −2 | warm | done | [PROFM2W](logs/PROFM2W.log) |
| PROFM2R → **PROFM2RS** | −2 | perturbed | killed 137 → resumed, done | [PROFM2R](logs/PROFM2R.log), [PROFM2RS](logs/PROFM2RS.log) |
| PROFM2K → **PROFM2KS** | −2 | PDF/TNP kick | killed 137 → resumed, done | [PROFM2K](logs/PROFM2K.log), [PROFM2KS](logs/PROFM2KS.log) |
| PROFP2W → **PROFP2WS** | +2 | warm | killed 137 → resumed, done | [PROFP2W](logs/PROFP2W.log), [PROFP2WS](logs/PROFP2WS.log) |
| PROFP2R | +2 | perturbed | done | [PROFP2R](logs/PROFP2R.log) |
| PROFP2K | +2 | PDF/TNP kick | done | [PROFP2K](logs/PROFP2K.log) |

Gate logs are `logs/<fit>.gate`. Seeds and fitresults are in
`/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261002_multistart_profile/`. rabbit writes a ~99 kB
`fitresults_<fit>.hdf5` stub at the start of every fit; a fit that was killed leaves only that stub. A result is a file
larger than 1 MB, so never read a stub.

---

## Method

**Why by hand.** rabbit's `--scan` warm-starts every point from the previous one (`knowledge/20_frameworks/likelihood_scans.md`),
so it follows one branch, and the step size can change the basin. Here every point is an independent fit with `alphaS`
frozen, from three unrelated starts — the recipe of `alphas-scan-discontinuity/260921-two-solutions`.

**Configuration.** NOMSTIFF's own `meta_info["command"]` (card A + lattice, λ4_ν = 0, `pdf62_y35_260921/merged_full_bin0xzero`,
τ = 8, `-r ... NPDampingMapping margin=0`, same `fit_params`, `prior_sigmas`, threads). `scripts/build_cmds.py` changes
exactly: `-o`, `--postfix PROF<pt><start>`, `--snapshotFile`, `--externalPostfit <seed>`, `--earlyStopping 100 → 15`, and
appends `--stallRelTol 1e-11 --maxRestarts 0 --freezeParameters alphaS` (diff in `logs/build_cmds.log`). Main fit +
postfit Hessian only (NOMSTIFF has no saturated / impacts / hists). Code: WRemnants ccb2adb8 (wall margin committed),
rabbit 2a59246, scetlib as NOMSTIFF (stamped per fit in the `[run]` line).

**Freeze collision check (done before launch).** NOMSTIFF's command has no `--freezeParameters`. The param model's
`fit_params=` does not use rabbit's freeze mask: `SCETlibADParamModel._register_params` simply leaves unlisted SCETlib
directions out of rabbit's parameter vector (`param_model.py:668ff`), and `alphaS` IS in `fit_params`. rabbit resolves
`--freezeParameters` with `re.fullmatch` (`rabbit/common.py:24`), so `alphaS` matches only `alphaS`. The freeze is a
`stop_gradient` mask on the POI (`fitter.py:get_poi`), set at Fitter construction; `--externalPostfit` then overwrites
`x`, so the frozen value is the seed's. To be verified on the output: fitresult x[`alphaS`] == seed x[`alphaS`] bit-exactly.

**Points.** x[`alphaS`] = x_NOM + k·σ_NOM, k ∈ {−2, −1, +1, +2}, σ_NOM = √cov_NOM[`alphaS`,`alphaS`] (additive blinding,
so σ in x = σ in `alphaS`). Seed check: (x_seed − x_NOM)/σ = k to 1e-15. Blinded x only; no absolute value anywhere.

**Starts** (`scripts/make_profile_seeds.py`, master seed **20261002**, log `logs/make_seeds.log`, manifests in [seeds/](seeds/)):
- **W (warm):** the NOMSTIFF vector, only `alphaS` moved.
- **R (perturbed):** the census generator (T3 `make_random_starts.py`, run unmodified as a subprocess) with `--s 0.5
  --alphas-u 0 --n 4 --seed 20261002`, default physical NP boxes, rejection on the wall at margin 0 (all four accepted on
  the first draw, none near-active); child j → point j in the order M1, P1, M2, P2; then `alphaS` overwritten with the
  point. Drawn NP (physical): M1 λ2 0.133 λ4 0.121 δλ2 −0.016 λ2_ν 0.278; P1 0.187 / 0.167 / −0.009 / 0.268;
  M2 0.255 / 0.068 / −0.007 / 0.143; P2 0.285 / 0.148 / −0.025 / 0.128 (NOMSTIFF: 0.026 / 0.088 / −0.004 / 0.064).
- **K (PDF/TNP kick):** NOMSTIFF + 2·σ_post,i·sign_i on all **38** of `pdfEig0–28` and `resumTNP_*` (9 TNPs; `resumTransition2`
  is not a TNP and is not kicked), signs ±1 from `SeedSequence([20261002, 1]).spawn(4)[j]`; signs in
  [seeds/manifest_kick_signs.csv](seeds/manifest_kick_signs.csv), σ_post (0.68–1.46) in
  [seeds/kick_block_sigma_post.csv](seeds/kick_block_sigma_post.csv). ||Δθ/σ_post|| = 2√38 = 12.3 in that block.

Quadratic start-cost estimate ½ dᵀ C_NOM⁻¹ d (from NOMSTIFF's postfit cov; only indicative, and meaningless for R, whose
NP draw is far outside the quadratic region): W ±1σ 466, ±2σ 1865 (with the nuisances held, moving `alphaS` alone is
expensive: σ_conditional ≈ σ/30); K 5.9k–54k (the random-sign kick fights the strong PDF–TNP–`alphaS` correlations).
The real start NLLs are the iteration-0 losses in the logs.

**Queue.** `scripts/queue.sh` (rolling, at most 3 of ours alive or gating, MemAvailable ≥ 500 GB), each launch through
`studies/alphas-scan-discontinuity/scripts/mem_gate.sh 330` (unmodified); `launch.sh` symlinks the log into `logs/` at
launch. Order M1{W,R,K}, P1{W,R,K}, M2{W,R,K}, P2{W,R,K}: the three starts of a point are launched together; with
rolling slots a slow fit does not hold back the next point.

---

## Log

<!-- Newest first. What was tried, what happened, why — with an evidence path. -->

### 2026-10-04
- 18:10 **All 12 done.** The watcher exited at 17:56 with no relaunch needed (`logs/watcher.log`), and the
  orchestrator reran `analyze_profile.py --plot`.
  - The resumed fits converged: PROFM2RS EDM 2.4e-17, PROFM2KS 3.5e-17, PROFP2WS 3.9e-15. Each was resumed from its
    own pre-kill periodic snapshot, with the same command and `alphaS` still bit-identical to the seed.
  - Every pair at every point is the same solution, and the profile and intervals did not change.
  - Logbook finalised: status done.
- 16:30 Plot cosmetics (orchestrator): an off-scale point is now an arrow at the top edge, with a small label centred
  under it, so it no longer collides with the legend. The content is unchanged.
- 15:50 First version of the profile plot and analysis. `scripts/analyze_profile.py` reuses the census helpers by
  import. Output: [analysis.out](analysis.out) and `profile.json`.
  - Every number the orchestrator gave was reproduced to the digits it quoted: the pairwise agreement at M1, P1 and P2
    (R–K), the four 2ΔNLL values, and the symmetric / antisymmetric parts.
  - **One correction to the interval.** A least-squares fit of a k² + c k³ to all four points gives [−0.982, +1.012].
    That model cannot fit both |k| = 1 and |k| = 2: their symmetric parts are 1.0018 and 4.0287/4 = 1.0072, so there is
    a small k⁴ term.
  - Adding d k⁴ gives a = 1.0000, c = −0.0303, d = +0.0018 and the interval [−0.9846, +1.0148]. That is identical to the
    cubic drawn exactly through the k = ±1 points, which is the orchestrator's +1.015 / −0.985.
  - The quartic (equivalently, the ±1 interpolation) is the number to quote. The plain cubic is drawn because it was asked
    for, and its 0.003σ difference is the size of the model ambiguity.
- 15:26 Watcher `scripts/watcher.sh` started, detached (PID 2733897).
  - First version: its liveness check matched itself (awk on its own command line) and matched by prefix
    (`run_fit.sh PROFM2R` is a prefix of `PROFM2RS`). Both fixed: the mem_gate match now requires comm == bash, and the
    run_fit match is anchored to the end of the command line.
  - Verified before start: alive for the three S fits, not alive for the dead PROFM2R / PROFP2W.
  - `scripts/status.sh` now lists the relaunch chains, counts a fitresult only above 1 MB, and shows the watcher.
- **Recorded from the orchestrator (I was not running).**
  - Three fits were SIGKILLed (exit 137 from `run_fit.sh`; probably OOM on the shared node, not checked):
    - PROFM2K at 2026-10-03 06:47, after 102 iterations (last loss 430.216, 2ΔNLL 107);
    - PROFM2R at 07:02, after 168 iterations (402.482, 2ΔNLL 51.7);
    - PROFP2W at 13:34, after 32 iterations (378.5086, 2ΔNLL 3.788, already 8.5e-4 NLL from the R/K value).
  - None of them got a Hessian; each left a 99 kB stub.
  - The orchestrator relaunched them on 2026-10-04 at about 15:17 as PROFM2RS, PROFM2KS and PROFP2WS, through this
    task's `launch.sh`, with the logs symlinked.
    - `cmds/PROF*S.cmd` = the original command with `--postfix`, `--snapshotFile` and `--externalPostfit` set to the dead
      fit's last periodic snapshot, which predates the kill (`alphaS` stays frozen at the seed value, since the snapshot
      carries it).
    - Their iteration-0 losses are above the last logged loss before the kill because the snapshot is older than the
      kill: PROFM2RS 409.77, PROFM2KS 593.09.
    - The S fit is treated as the result of its start.
- 9 of 12 done (orchestrator, 10-04): M1 W/R/K, P1 W/R/K, M2W, P2R, P2K. The queue script exited after launching all 12
  (2026-10-03 13:50).

### 2026-10-02
- 14:25 first wave running (PROFM1W 14:07, PROFM1R 14:11, PROFM1K 14:15). Every log shows
  `Updated list of frozen params: [b'alphaS']`, the wall "armed on 5 of 8 condition(s) at margin=0", `alphaS` blinded.
  Iteration-0 losses (NOMSTIFF = 376.6146): W 526.83 (+150), R 5728.1 (+5351), **K 153768.6 (+1.5e5)**.
  - The K start is far more expensive than the quadratic estimate (5.4e4): a 2σ_post random-sign kick on 38 strongly
    correlated PDF/TNP directions is a very large move in the data term. It is what the task asked for; watch it for a crawl.
  - The W quadratic estimate (466) also overshoots the real +150, so `quad_cost_est` in the manifest is not a usable
    predictor (likely the e^16 wall curvature makes C_NOM⁻¹ inaccurate); the iteration-0 losses are the real start costs.
  - PROFM1W at iteration 8: 377.919 (+1.30 over NOMSTIFF; parabolic expectation at k = −1 is +0.5), still descending.
- mem_gate released each slot ~90 s after launch on `[scetlib_ad] cache loaded` (same as the census); node at 455 GB
  available with 3 fits running.
- Freeze check: snapshot of PROFM1W after 3 iterations: x[`alphaS`] bit-identical to the seed, others moved (max 0.16).
- 14:07 queue started (PID in `logs/queue.pid`); PROFM1W through the gate first. Node idle at launch (1383 GB available,
  my threads 461).
- Commands built (`logs/build_cmds.log`): token diff vs NOMSTIFF is exactly the intended 5 replacements + 6 appended tokens.
- Seeds written (`logs/make_seeds.log`): 12 files, round-trip bit-exact (T3 `write_seed`), Δ`alphaS`/σ = k to 1e-15.

---

## Result

**Caveats first.**
- Real-data fits with `alphaS` blinded. k is the blinded difference x[`alphaS`] − x_NOM[`alphaS`], in units of
  NOMSTIFF's σ(`alphaS`). No absolute value is computed anywhere.
- Every fit uses NOMSTIFF's objective (card A + lattice, λ4_ν = 0, wall margin 0, τ = 8, the bin0xzero cache), so the
  NLLs compare directly with NOMSTIFF's 376.6146.
- Each point is an independent fit with `alphaS` frozen: no warm-start chain between points, unlike `--scan`.
- k = 0 is NOMSTIFF itself; it was not re-fit here, because the census settled it.
- Three ±2σ results come from fits **resumed from their own pre-kill snapshots**: PROFM2R → PROFM2RS, PROFM2K → PROFM2KS,
  PROFP2W → PROFP2WS. The originals were SIGKILLed (exit 137). The resumed fits used the same command, only the start
  vector differs, so they are legitimate continuations of the same start.
- "Converged" means EDM < 1e-6 on the floating subspace. All 12 fits pass, the largest EDM being 2.5e-10 (PROFM1R,
  stall stop).

### The profile

![Profile likelihood of alphaS from independent frozen-alphaS fits. Upper panel: 2ΔNLL against Δα_S/σ_NOMSTIFF at k = −2, −1, +1, +2, three starts per point (circle W warm, square R perturbed, triangle K PDF/TNP kick), all converged and filled, all three overlapping at every point; NOMSTIFF star at 0. The grey dashed Hessian parabola k², the k²+k³ fit and the k²+k³+k⁴ fit are drawn; dotted verticals mark the 2ΔNLL = 1 crossings. Lower panel: 2ΔNLL − k²: +0.27 at −2, +0.032 at −1, −0.028 at +1, −0.21 at +2, a k³ skew.](profile_alphas_multistart.png)

*Caveat for the figure:* real data, blinded differences only, nominal configuration, independent fits with `alphaS`
frozen at each k. All 12 markers are converged fits. Those at ±2σ include three that were resumed from their pre-kill
snapshots.

| k | starts converged | 2ΔNLL (lowest) | spread over starts | k² | 2ΔNLL − k² |
|---|---|---|---|---|---|
| −2 | 3 of 3 | 4.271274 | 7.8e-10 | 4 | +0.271 |
| −1 | 3 of 3 | 1.032080 | 6.0e-10 | 1 | +0.032 |
| +1 | 3 of 3 | 0.971529 | 2.4e-10 | 1 | −0.028 |
| +2 | 3 of 3 | 3.786219 | 8.5e-10 | 4 | −0.214 |

Shape:
- **Symmetric part:** 1.0018 at |k| = 1 and 4.0287 at |k| = 2 (k² = 1 and 4).
- **Antisymmetric part** ½[q(+k) − q(−k)]: −0.0303 and −0.2425. That ratio is 8.0, so it is ∝ k³.
- **Fits:**
  - a k² + c k³ + d k⁴ gives a = 1.0000, c = −0.0303, d = +0.0018, so 2ΔNLL = 1 at **[−0.985, +1.015] σ_NOM**. A cubic
    drawn exactly through k = ±1 gives the same interval.
  - A least-squares a k² + c k³ fit gives a = 1.0069, c = −0.0303 and [−0.982, +1.012]. It cannot fit |k| = 1 and 2 at
    once (the k⁴ term), so the quartic / ±1 interval is the one to quote. The 0.003σ difference is the model ambiguity.

### Agreement between starts (same point)

Δθ is in units of σ_NOM over all 3718 floating parameters (`alphaS` is frozen and bit-identical to the seed in every fit).
The criterion is the census one: |ΔNLL| < 1e-4 and ||Δθ/σ|| < 1e-4.

| point | pair | ΔNLL | ‖Δθ/σ‖ | max \|Δθ/σ\| | PDF+TNP block ‖Δθ/σ‖ | same |
|---|---|---|---|---|---|---|
| −2 | W–R | −1.1e-10 | 9.2e-9 | 4.9e-9 (pdfEig19) | 6.7e-9 | yes |
| −2 | W–K | +2.8e-10 | 1.1e-8 | 6.3e-9 (pdfEig19) | 9.7e-9 | yes |
| −2 | R–K | +3.9e-10 | 9.6e-9 | 4.0e-9 (pdfEig28) | 7.4e-9 | yes |
| −1 | W–R | +2.4e-10 | 1.6e-5 | 5.3e-6 (pdfEig14) | 9.1e-6 | yes |
| −1 | W–K | −5.9e-11 | 4.8e-7 | 2.0e-7 (pdfEig28) | 3.9e-7 | yes |
| −1 | R–K | −3.0e-10 | 1.6e-5 | 5.3e-6 (pdfEig14) | 9.2e-6 | yes |
| +1 | W–R | −3.7e-11 | 5.0e-8 | 1.4e-8 (pdfEig27) | 2.7e-8 | yes |
| +1 | W–K | +8.4e-11 | 2.2e-8 | 1.2e-8 (pdfEig12) | 1.7e-8 | yes |
| +1 | R–K | +1.2e-10 | 5.6e-8 | 1.6e-8 (pdfEig12) | 3.3e-8 | yes |
| +2 | W–R | +2.6e-10 | 1.3e-7 | 4.9e-8 (pdfEig19) | 1.0e-7 | yes |
| +2 | W–K | −1.6e-10 | 1.7e-7 | 5.8e-8 (pdfEig19) | 1.3e-7 | yes |
| +2 | R–K | −4.2e-10 | 1.6e-7 | 3.9e-8 (pdfEig11) | 1.0e-7 | yes |

The −1 W–R / R–K residual (1.6e-5) is PROFM1R's. That fit ended on the stall rule at EDM 2.5e-10, and
√(2·EDM) = 2.3e-5 is the expected distance, so it sits at its own convergence floor (census Finding 2).

### Per fit

The iterations column sums the whole chain: a killed original plus its resumed fit.

| fit | k | frozen x_aS == seed | 2ΔNLL | EDM | iterations | ‖Δθ/σ_NOM‖ to NOMSTIFF | of which PDF+TNP | faces on | λ2 | λ4 | δλ2 | λ2_ν |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PROFM2W | −2 | yes | 4.271274 | 1.0e-16 | 82 | 2.73 | 1.89 | L2(2.5) | 0.0332 | 0.0520 | −0.0053 | 0.0628 |
| PROFM2R→RS | −2 | yes | 4.271274 | 2.4e-17 | 186 | 2.73 | 1.89 | L2(2.5) | 0.0332 | 0.0520 | −0.0053 | 0.0628 |
| PROFM2K→KS | −2 | yes | 4.271274 | 3.5e-17 | 208 | 2.73 | 1.89 | L2(2.5) | 0.0332 | 0.0520 | −0.0053 | 0.0628 |
| PROFM1W | −1 | yes | 1.032080 | 6.7e-14 | 65 | 1.35 | 0.93 | L2(2.5) | 0.0285 | 0.0696 | −0.0046 | 0.0633 |
| PROFM1R | −1 | yes | 1.032080 | 2.5e-10 | 1095 (stall stop) | 1.35 | 0.93 | L2(2.5) | 0.0285 | 0.0696 | −0.0046 | 0.0633 |
| PROFM1K | −1 | yes | 1.032080 | 6.0e-14 | 195 | 1.35 | 0.93 | L2(2.5) | 0.0285 | 0.0696 | −0.0046 | 0.0633 |
| PROFP1W | +1 | yes | 0.971529 | 1.7e-17 | 29 | 1.34 | 0.90 | L2(2.5) | 0.0245 | 0.1065 | −0.0039 | 0.0656 |
| PROFP1R | +1 | yes | 0.971529 | 2.8e-15 | 376 | 1.34 | 0.90 | L2(2.5) | 0.0245 | 0.1065 | −0.0039 | 0.0656 |
| PROFP1K | +1 | yes | 0.971529 | 2.9e-15 | 313 | 1.34 | 0.90 | L2(2.5) | 0.0245 | 0.1065 | −0.0039 | 0.0656 |
| PROFP2W→WS | +2 | yes | 3.786219 | 3.9e-15 | 52 | 2.67 | 1.77 | L2(2.5) | 0.0249 | 0.1270 | −0.0040 | 0.0672 |
| PROFP2R | +2 | yes | 3.786219 | 6.4e-15 | 112 | 2.67 | 1.77 | L2(2.5) | 0.0249 | 0.1270 | −0.0040 | 0.0672 |
| PROFP2K | +2 | yes | 3.786219 | 1.0e-14 | 197 | 2.67 | 1.77 | L2(2.5) | 0.0249 | 0.1270 | −0.0040 | 0.0672 |

NOMSTIFF itself: λ2 0.0256, λ4 0.0876, δλ2 −0.0041, λ2_ν 0.0643, on face L2(2.5).

Start costs (iteration-0 loss − NOMSTIFF):
- W: +150 to +1820;
- R: +1.7e3 to +8.7e3;
- K: +1.4e4 to +1.5e5.
No fit got stuck the way CENS03 did. Every start converged; the only intervention was resuming the three OOM-killed
fits from their snapshots. The slowest was PROFM1R: 1095 iterations, ending on the stall rule at EDM 2.5e-10, still the
same point.

### Physics read

- **Single-valued.** In the nominal configuration the profile likelihood of `alphaS` has one solution at each tested
  value out to ±2σ. Three unrelated starts reach the same 3718-parameter vector to the EDM floor.
  - One start is a 2σ_post random-sign kick in all 38 PDF-eigenvector and TNP directions, beginning up to 1.5e5 NLL
    uphill. That is the direction that carried the old unwalled second solution. It finds nothing else.
  - So there is no second branch, no kick and no jump: unlike the unwalled scans of `alphas-scan-discontinuity`, there
    is nothing for a warm-started `--scan` to follow off.
- **What the profile moves.** Along the profile, `alphaS` is traded mainly against the CT18Z PDF eigenvectors and the
  resummation TNPs, which carry about 2/3 of the displacement (‖Δθ/σ‖ 0.93 of 1.35 at −1σ). This is consistent with the
  AN treating them as the dominant theory systematics on `alphaS`.
  - Among the NP parameters, λ4 tracks `alphaS` monotonically: 0.052 → 0.127 from −2σ to +2σ.
  - λ2, δλ2 and λ2_ν barely move.
  - Every point sits on the same single wall face as NOMSTIFF, L2(|Y| = 2.5) = 0. No other face switches on, so the
    constrained minimum keeps its topology over ±2σ.
- **Shape.** The likelihood is close to Gaussian: the symmetric part matches the Hessian k² to 0.2 % at |k| = 1 and
  0.7 % at |k| = 2. There is a small skew, −0.030 k³: 2ΔNLL is lower on the high-`alphaS` side.
- **Interval.** The 2ΔNLL = 1 interval is [−0.985, +1.015] σ_NOM: 1.5 % wider above than below, with the same total
  width as the Hessian ±1σ. The Hessian σ is therefore an accurate symmetric summary. If an asymmetric interval is
  quoted, the shift is +0.015σ at the centre of the interval.

## Findings

1. **The nominal walled profile of `alphaS` is single-valued at −2σ, −1σ, +1σ and +2σ.** At every point, 3 of 3
   independent frozen-`alphaS` starts (warm, census-perturbed, 2σ PDF/TNP kick) agree to |ΔNLL| ≤ 4.2e-10 and
   ||Δθ/σ|| ≤ 1.6e-5 (the EDM floor) — (evidence: `analysis.out`, `profile.json`)
2. Profile shape: 2ΔNLL = 1.000 k² − 0.030 k³ + 0.002 k⁴, so 2ΔNLL = 1 at [−0.985, +1.015] σ_NOM. The Hessian σ is
   accurate to about 1.5 %, with a small upward skew. A least-squares k² + k³ fit alone gives [−0.982, +1.012] (model
   ambiguity 0.003σ) — (evidence: `profile_alphas_multistart.png`)
3. Along the profile, `alphaS` trades against the PDF+TNP block (about 2/3 of the displacement) and against λ4
   (monotonic). The fit stays on the single face L2(|Y| = 2.5) = 0 — (evidence: `analysis.out` per-fit table)
4. A frozen parameter really is frozen: x[`alphaS`] in every final fitresult is bit-identical to its seed, including the
   fits resumed from snapshots (stop_gradient mask, set before `--externalPostfit` loads x) — (evidence: `analysis.out`
   "frozen" column)
5. rabbit writes a ~99 kB `fitresults_*.hdf5` stub at the start of a fit. A killed fit leaves only that stub, so judge
   "done" by size > 1 MB plus `[run] exit=0`, never by existence. Resuming a SIGKILLed fit from its own periodic snapshot
   (same command, `--externalPostfit <snapshot>`) converges cleanly: 3 of 3 here, EDM ≤ 3.9e-15 — (evidence:
   `logs/PROF*S.log`, `logs/watcher.log`)

---

## Open questions

- The exit-137 kills of PROFM2R, PROFM2K and PROFP2W (2026-10-03) were not diagnosed; most likely OOM on the shared node.
- Points beyond ±2σ and starts aimed at the other wall faces were not tested.
