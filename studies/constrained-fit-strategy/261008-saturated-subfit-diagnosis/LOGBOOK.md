---
title: Saturated projected sub-fit cost diagnosis
slug: 261008-saturated-subfit-diagnosis
study: constrained-fit-strategy
status: done          # active | done | paused | abandoned
created: 2026-10-08
updated: 2026-10-09
owner: study-worker
---

# Saturated projected sub-fit cost diagnosis

**Task:** Why does the projected-ptll saturated sub-fit (`-m Project ch0 ptll --computeSaturatedProjectionTests`, 39 free `saturated_ch0_ptll*` params, `--noFit` at LATB8's walled point) take ~150 trust-krylov iterations / ~5 h, and what would make it substantially cheaper (needed once per toy)?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-10-08 18:30)

- **Answer:** the sub-fit is slow because of the geometry of M1, not because of the wall's kink.
  - Once the ptll shape is free, alphaS (rho^2 = 0.979 with the 39 scales) and the free NP lambdas become nearly flat.
  - The M1 minimum then sits 9.6 sigma_M0 away along a long, curved valley, with kappa ~ 1e9-1e10.
  - 89-91 % of the time goes into Hessian-vector products (HVPs). C2 changes nothing.
- **The fix is tested and PASSES.** SATP is SATB8 plus full-scope spectral preconditioning, a CLI-only change.
  - Work: nhev 614 vs 2150 (3.5x fewer HVPs; criterion was <= 700), nfev 71 vs 156, iterations 69 vs 158.
  - Same minimum: final loss 337.47616205795, -1.7e-10 from SATB8's; q = 78.40/39 unchanged; max |dx| = 4e-8.
  - Minimiser wall time 1.32 h (+306 s preconditioner Hessian) vs SATB8 5.82 h and SATC2 4.08 h.
  - At SATB8's node load the same work would take ~1.9 h, ~3x faster.
  - Details in [Result §5](#5-the-test-satp-full-spectral-preconditioning-passes).
- **Gtol 0.03 is NOT a safe add-on.** ||g_y|| is not logged, and in the start-built whitened frame the soft alphaS
  direction's curvature drifts down to ~1e-3. So a gtol of 0.03 could stop anywhere between Delta q ~ 1e-7 and 0.9.
  What a stop at q-to-go 0.01 would have saved on SATP: 1766 s (37 % of the minimiser time).
- **Next action:** none; the study is closed. (Orchestrator, 2026-10-09: the flags were adopted in fitterAD.sh and the toy recipe, 1c5d93a.)
  - Parked:
  - Optionally: variable projection (remedy 3), or a mid-fit preconditioner rebuild (remedy 4), to attack the remaining
    linear tail.
- **Blocking on:** nothing.
- **Running:** nothing. SATP exited 0 at 18:19. Log: [logs/SATP.log](logs/SATP.log). Fitresult:
  `/ceph/.../261008_saturated_subfit_diag/fitresults_SATP.hdf5`.

---

## Log

<!-- Newest first. What was tried, what happened, why — with an evidence path. -->

### 2026-10-08
- **18:19 SATP finished (exit 0) and PASSES** ([Result §5](#5-the-test-satp-full-spectral-preconditioning-passes)).
  - Counts vs SATB8: nhev 614 vs 2150, nfev 71 vs 156, 69 iterations vs 158.
  - Same minimum: final loss -1.7e-10 from SATB8's; q 78.40; max |dx| 4e-8.
  - Wall time: 1.32 h minimiser + 306 s reference Hessian. Cache load took 419 s.
  - Analysis scripts:
    - [scripts/cost_breakdown.py](scripts/cost_breakdown.py) and [scripts/step_classes.py](scripts/step_classes.py),
      now including SATP;
    - [scripts/compare_satp.py](scripts/compare_satp.py) -> [compare_satp.json](compare_satp.json);
    - [scripts/gtol_model.py](scripts/gtol_model.py) -> [gtol_model.json](gtol_model.json).
- **16:42 SATP launched** (Luca approved the proposed test; [cmds/SATP.cmd](cmds/SATP.cmd), [scripts/run_satp.sh](scripts/run_satp.sh)).
  - Pre-launch checks on the production rabbit checkout (2a59246, unmodified):
    - `--precondition*` exist.
    - `select_index_blocks` matches `'.*'` with re.fullmatch: all 3759 parameters, frozen ones excluded.
    - `--preconditionBlocks none` makes one block.
    - `spectral` does: eigh, then |Lambda|, then a floor at eps*m*max, then a Cholesky of |H|.
    - The deepcopied saturated fitter carries the flags. Its `fit()` builds the transform at the sub-fit's own warm
      start, so the main `--noFit` builds nothing.
    - Under preconditioning scipy sees grad_y, so a gtol would test \|g_y\|.
  - SATP command dry-parsed in the container: OK. `'.*'` is quoted in the inner script so that it cannot glob.
- **16:35 remedy ranking and test proposal written** ([Result](#result)). No remedy was run then.
- **SATC2 finished** (c2 task). Refreshed [cost_breakdown.json](cost_breakdown.json) and [step_classes.json](step_classes.json).
  - SATC2: 161 iterations, nfev = 159, **nhev = 2141, the same as SATB8's 2150**. HVPs are 89 % of its time.
  - It is faster in wall time only because the node was lighter: t_HVP = 6.1 s and t_f = 9.8 s, against 8.9 s and 12.2 s for SATB8.
  - C2 does not change the amount of work.
- **Offline spectra.** [scripts/spectra.py](scripts/spectra.py) wrote [spectra.json](spectra.json), and
  [scripts/spectra_extra.py](scripts/spectra_extra.py) wrote [spectra_extra.json](spectra_extra.json). The numbers are in
  [Result](#result).
- **HDIAG done.** 15:34–16:19, exit 0, one cache load. Log: [logs/HDIAG.log](logs/HDIAG.log); output: [hess_diag.json](hess_diag.json).
  - Checks: the start loss equals the main loss to 2e-11. It differs from the SATB8 log's value by −1.3e-5, which is that
    value's rounding. The end loss equals SATB8's final loss bit for bit.
  - Dense Hessians took 869, 748 and 656 s on the loaded node.
  - The in-job loss+grad and HVP timings (3.5 ms and 8.6 ms) are **cache hits**: the model memoises repeated points.
    They are not real costs and are discarded. Per-call costs come from the logs instead.
- 13:55: HDIAG queued. It waited behind SATC2 and LATFROZ_V1, and launched at 15:33.
- **13:55 HDIAG queued** ([scripts/hess_diag.py](scripts/hess_diag.py), [scripts/launch_diag.sh](scripts/launch_diag.sh)): one gated
  cache load, no minimisation. Dense Hessians at the sub-fit start and end (and at a point near the end), straight-line
  loss checks (raw, and with the 39 scales profiled analytically), exact Newton steps from the start and from near the
  end. Offline follow-up in [scripts/spectra.py](scripts/spectra.py) (smoke-tested on synthetic matrices).
- **Wall faces from stored values** ([scripts/wall_faces.py](scripts/wall_faces.py) -> [wall_faces.json](wall_faces.json)).
  - Start (LATB8): on L2(|Y|=2.5) only (-2.8e-7 GeV^2); lambda4_nu = +0.011 is slack.
  - End (SATB8): L2(2.5) still engaged (-1.1e-7), and **lambda4_nu has run onto its face** (-1.09e-5 GeV^4, engaged).
  - lambda2 and delta_lambda2 moved by +1.79 and -1.79 sigma_M0, exactly opposite: the sub-fit slides *along* the
    L2(2.5) face.
- **What the sub-fit moves** ([scripts/path_params.py](scripts/path_params.py) -> [path_params.json](path_params.json); stored
  fitresults only, displacement in LATB8 postfit sigma).
  - alphaS -9.6 sigma_M0 (a displacement only; no value read); lambda2_nu +3.5; resumFOScaleEnvSymDiff +2.4; lambda4_nu
    -2.1; lambda2 / delta_lambda2 +/-1.8; lumi +1.6. 12 parameters move by more than 1 sigma, 107 by more than 0.1.
  - The bin scales end as a smooth monotone tilt, s = 0.908 (lowest ptll bin) to 1.106 (highest), rms(s-1) = 8 %.
  - In the M0 metric that displacement costs 0.5 D^T cov^-1 D = 1.5e4 NLL; in M1 it gains 39.2. So it is a long valley
    in the joint (theta, s) space: every theta step must come with a compensating ~10 % scale change.
  - SATB8 and SATB8SA end at the same point (max |dx| 2.6e-9).
- **Stop-rule replay** ([scripts/replay_stop.py](scripts/replay_stop.py) -> [replay_stop.json](replay_stop.json)).
  `--earlyStopping N --stallRelTol` is not a safe way to cut the tail. Every setting that saves real time fires on a
  false plateau: q errors 0.36-20 (SATB8SA at it. 11-34; SATB8 at it. 16, 37, 60). The settings that fire late enough
  to be right save at most 27 %.
- **Step classes** ([scripts/step_classes.py](scripts/step_classes.py) -> [step_classes.json](step_classes.json)).
  - Rejection cascades of 1-7 steps (radius x1/4 each). Each is followed by a doubling "ladder" (gain ratio ~2); in
    SATB8SA the ladder at it. 30-41 runs over 12 doublings.
  - In SATB8, 16 iterations with dt >= 300 s take 61 % of the time; in SATB8SA, 7 take 67 %. They are deep Krylov solves
    late in the fit (up to ~270 HVPs).
  - Each deep solve gains about 35-40 % of what is left (linear convergence, ratio ~0.6-0.7 per cycle), followed by 3-4
    cheap "polish" steps with fast-shrinking gains.
- **Cost breakdown** ([scripts/cost_breakdown.py](scripts/cost_breakdown.py) -> [cost_breakdown.json](cost_breakdown.json)).
  t_f is the median dt after a rejection (trlib hot start, so no new HVPs); t_HVP = (sum dt - nfev t_f) / nhev.
  - SATB8: t_f = 12.2 s, t_HVP = 8.9 s, nhev = 2150, nfev = 156. **HVPs are 91 % of the 20 941 s.**
  - SATB8SA: t_f = 17.5 s, t_HVP = 9.9 s, nhev = 1002, nfev = 69, so 89 %.
  - Compare the main fits: 7-27 HVPs per iteration (LATB8 warm: 133 / 5 it.; C2A: 400 / 54 it.).
- Read the study logbook, 261006-diagnosis, 261008-c2-wall-test, the three knowledge notes, and the SATB8 / SATB8SA /
  SATC2 logs. Task dir created.

---

## Result

**Caveats first.**
- Real data, alphaS blinded. Every alphaS statement here is a displacement or a sigma ratio; no value was read.
- Configuration is LATB8's:
  - card A plus the native lattice term;
  - the |Y|<=2.5 subset cache;
  - relu² wall at τ = 8, TMD priors pinned;
  - `Project ch0 ptll` (39 scales), with the sub-fit started from LATB8's minimum.
- Hessians come from one diagnostic job (HDIAG) at three points:
  - x_s, the sub-fit start;
  - x_e, SATB8's minimum;
  - a point 0.4 NLL above x_e (θ = x_s + 0.9·(x_e − x_s), scales profiled).
- HVP counts per solve come from **plain CG on the dense matrices**. That is an exact-arithmetic stand-in for trlib's
  interior Lanczos solve, not a replay of trlib.
- Wall time depends on node load: t_HVP was 6.1–9.9 s across the three runs. Compare counts (nfev, nhev), not hours.
- Nothing below has been run as a fit. Every gain quoted is an estimate.

### 1. Where the time goes

![progress](subfit_progress.png)

*Plotted: q still to go = 2·(loss − final), against wall time and against iteration. All three runs end at
q = 78.40 / 39 (p = 0.019 %).*

| run | iterations | nfev | nhev | minimiser wall time | HVP share | to q-to-go < 0.1 | to < 0.01 | to final − 1e-6 |
|---|---|---|---|---|---|---|---|---|
| SATB8 (relu²) | 158 | 156 | 2150 | 5.82 h | 91 % | 3.10 h (it. 126) | 4.03 h (142) | 4.86 h (153) |
| SATC2 (C²) | 161 | 159 | 2141 | 4.08 h | 89 % | 2.26 h (128) | 2.99 h (147) | 3.49 h (157) |
| SATB8SA (seeded, scope all) | 67 | 69 | 1002 | 3.10 h | 89 % | 0.74 h (41) | 1.36 h (52) | 2.39 h (63) |

![dt per iteration](subfit_dt.png)

*Plotted: dt per iteration, coloured by step class. The right axis is the implied number of HVPs,
(dt − t_f)/t_HVP.*

- **The cost is HVPs, and most of it sits in a few deep Krylov solves.**
  - In SATB8, 16 iterations with dt ≥ 300 s take 61 % of the time. In SATB8SA, 7 such iterations take 67 %.
  - These solves come late, at small gradient, where scipy's inexact forcing asks for a relative residual of order
    |g|. Each needs ~50–270 HVPs.
  - Each one gains only ~35–40 % of what is left. The tail therefore converges linearly, at ~0.6–0.7 per cycle (one
    deep solve plus 3–4 cheap polish steps).
- **The tail below q-to-go 0.01 is 31 % of SATB8, 27 % of SATC2 and 56 % of SATB8SA.** Precision there is irrelevant:
  at q = 78 with 39 dof, Δq = 0.01 moves p by ~0.3 % relative.
- **A stall-window stop cannot cut that tail safely.** Replaying `--earlyStopping N --stallRelTol` on these logs
  ([replay_stop.json](replay_stop.json)): every setting that saves time fires on a false plateau, with q errors of
  0.36–20.
- Rejection cascades (up to 7 in a row, shrinking the radius by 4⁷) cost 19 % of the time, and the doubling ladders
  that follow them another 8–10 %. Both are real but secondary.

### 2. Diagnosis: which hypotheses hold

![spectra](hessian_spectra.png)

*Plotted: sorted |eigenvalues| of the sub-fit Hessian.*
- *Bulk: ~3700 prior-dominated directions at ~1.*
- *Top 41:*
  - *the L2(|Y|=2.5) wall face, 1.78e8 (δλ2/λ2);*
  - *the λ4_ν wall face, 4.5e6, engaged at the end only;*
  - *the 39 bin scales, 3.5e5–9.4e5 (= 4 N_j in the √s parametrisation).*
- *Bottom: directions dominated by alphaS, mixed with resumTNP_b_qqV / s / gamma_nu and λ2_ν. λ_min is 0.014 at the
  start, plus one negative eigenvalue (−4.4), and 0.090 at the end.*

| hypothesis | verdict | evidence |
|---|---|---|
| H1: ill-conditioning / a long flat valley | **holds; the main cause** | κ(H_s) = 1.3e10 and κ(H_e) = 2.0e9. On H_e, CG needs 59 / 98 / 170 / 290 HVPs to reach residual 1e-1 / 1e-2 / 1e-3 / 1e-6, which matches the observed deep solves (up to ~270). alphaS is 97.9 % degenerate with the scales: ρ² = 0.979 and σ ×6.9 from H_e, the same as CCWALLWARMPF's 0.978 / ×6.71 (`knowledge/20_frameworks/saturated_gof_tests.md`). The M1 minimum is 9.6 σ_M0 away in alphaS (λ2_ν +3.5, λ4_ν −2.1, lumi +1.6, ...), and the scales tilt smoothly from 0.908 to 1.106. In the M0 metric that displacement costs 1.5e4 NLL; in M1 it gains 39.2. So the valley is long and, in raw coordinates, narrow. |
| H1b: the valley is curved and non-quadratic | **holds** | On the raw straight line x_s → x_e the loss is 371.4 at t = 0.1 and still 340.7 at t = 0.9 ([valley_line](valley_line.png)): the straight path leaves the valley floor. The exact Newton step from x_s points AWAY from the minimum (cos = −0.53 with D, 4.3× its length). Its quadratic model predicted 328; the actual loss is 1.7e4 a quarter of the way along it and NaN at the full step. Even 0.4 NLL above the minimum (EDM there 3.3, against 0.40 actually left), one exact Newton step goes to +1.8e9, out through a wall face. Along the path, the curvature of the soft alphaS+TNP directions changes by 1e3–1e4 (the outliers in spectra_extra). |
| H2: scaling of the bin scales | **contributes, but not by itself** | The scales are stored as √s, with curvature 4N_j ~ 4e5–9e5. Their own block is well conditioned (κ 2.2). Rescaling only part of the problem makes it WORSE. Jacobi gives κ 5.5e7, but CG then needs 217–682 HVPs. Whitening only the scale block, or only rabbit's default cw == 0 block, gives κ ~ 1e12. |
| H3: the start point | **holds in part** | The first 4 iterations do nothing but profile the scales: the analytically profiled start is 353.5127, exactly SATB8's loss at iteration 3. The remaining 16 NLL is the walk in θ. `--saturatedSeed all` copies a previous sub-fit's vector; it measured 2× faster, but it needs an earlier sub-fit on the same data, which toys never have. No analytic θ seed works, because a single Newton step diverges (H1b). |
| H4: wall interplay | **not the kink; the faces shape the spectrum** | C² gives the same work (nhev 2141 vs 2150). The fit slides along the engaged L2(2.5) face (λ2 +1.79 σ, δλ2 −1.79 σ). λ4_ν runs onto its own face during the fit (+0.011 → −1.09e-5 GeV⁴). Adding that face's curvature to a start-built preconditioner barely changes the whitened spectrum (κ 1.21e7 → 1.27e7). What goes stale is the alphaS valley, not the wall. |
| H5: minimiser and tolerances | **holds** | trust-krylov runs with rabbit's tol = 0. The inexact forcing makes the late interior solves deep. There is no usable stopping rule either: \|g\| is dominated by the stiff scales (all of the start's \|g\| = 5730 is in the scales), and EDM is not computed. |

**Physics read.** The slowness is a property of the alternative model M1, not a pathology of the code.
- Freeing the ptll shape releases the parameters whose constraining power was mostly ptll shape: alphaS and the free
  NP λ_ν.
- Only the yll structure within each ptll bin, the lattice term and the priors still hold them. They drift ~1.4 σ_M1 to
  where those prefer, and the 39 scales absorb the ±10 % ptll tilt this produces.
- The minimiser has to walk this curved, ill-conditioned valley.
- The answer is unaffected: SATB8, SATB8SA and SATC2 all give q = 78.40 / 39, and their minima agree to 2.6e-9 in x.

### 3. Ranked remedies

**1. Full-scope spectral preconditioning of the sub-fit.**
- How: `--precondition --preconditionParams '.*' --preconditionBlocks none --preconditionTransform spectral`. rabbit
  builds it at the sub-fit's own start: the deepcopied fitter's `fit()` calls `_build_preconditioner()` at the warm start.
- Code: none (CLI only).
- Expected gain:
  - HVPs per deep solve drop 3–4× on H_e: 290 → 77 at 1e-6, 170 → 66 at 1e-3, with κ going from 2e9 to 1.2e7.
  - The effect on outer iterations is unknown, because the stale alphaS curvature (H1b) remains.
  - **Estimate: 2–3× overall**, i.e. 5.8 h → ~2–3 h at SATB8's node load.
- Evidence: `precond.full` in spectra.json.
- Cost to test: 1 cache load, ~2–4 h.

**2. A stop at a meaningful Δq.**
- How: under full whitening (remedy 1), ½‖g_y‖² ≈ EDM, so `--minimizerGtol 0.03` means EDM ≲ 5e-4.
- Code: none (CLI), but it only works together with remedy 1.
- Expected gain: it removes the tail below q-to-go ~0.01, which is 27–56 % of the time, i.e. ×1.3–2.3.
- Evidence: the q bands in cost_breakdown. The replay shows the stall-window rule cannot do this.
- Cost to test: read it off the remedy-1 run's log, or a second run.

**3. Variable projection of the 39 scales.**
- How: compute s_j(θ) = N_j/ν_j(θ) inside the sub-fit loss, so autodiff gives the reduced gradient directly. Then run
  a few polish iterations with the scales free.
- Code: a rabbit branch, ~1 day with tests.
- What it changes:
  - It removes the 39 stiff directions and the curved compensation between θ and the scales.
  - With the scales profiled, the loss falls smoothly and monotonically along the straight line in θ, from 16.0 NLL to
    0, and close to a quadratic.
  - At the minimum the profiled point equals the joint optimum to 2e-10, so the BB-lite treatment costs nothing.
  - κ stays at ~2e9 (wall plus alphaS), so it should be combined with remedy 1.
- Expected gain: **3–10× in combination with remedy 1. This is the least certain estimate.**
- Evidence: valley_line, `line_prof` in hess_diag, the Schur-complement κ.
- Cost to test: the code change plus 1 cache load.

**4. Rebuild the preconditioner once mid-fit.**
- How: rebuild at q-to-go ~1, or when λ4_ν engages its face. The stall trigger is unreliable here, so this needs a
  small rabbit change.
- What it addresses: the stale alphaS curvature that remedy 1 leaves behind (evidence: spectra_extra).
- When: after remedy 1 has been tested.

**Not worth testing:**
- the C² wall (no effect);
- the stall-restart flags;
- Jacobi, block-only or default-scope preconditioning (all worse);
- exact-Newton or trust-exact seeding (the Newton step diverges, and every iteration costs a 650–870 s Hessian);
- `--saturatedSeed` for toys (there is no earlier sub-fit to seed from).

### 4. Proposed minimal test (approved and run as SATP: see §5)

- **SATP** = SATB8's command (`261007-lattice-term-native/cmds/SATB8.cmd`: relu², τ 8, the same flat LATB8 seed,
  rabbit 2a59246) plus `--precondition --preconditionParams '.*' --preconditionBlocks none --preconditionTransform
  spectral`. No gtol, so that the comparison is clean.
- **Compare with SATB8 and SATC2**, which are identical apart from this flag, and with SATB8SA:
  - nfev and nhev (not hours);
  - iterations to q-to-go < 0.1, < 0.01 and < 1e-6;
  - the time to build the preconditioner;
  - the final loss, which must be 337.47616206 ± 1e-6 (q = 78.40).
- **Success:** nhev ≤ 700 (3× below 2150) at the same final loss.
- **If it succeeds:** add `--minimizerGtol 0.03` (SATPG), or read the stop point off SATP's log if rabbit logs
  ‖g_y‖. Then build remedy 3 on a rabbit worktree branch.
- **If it fails** (no fewer HVPs, or rejections from the stale alphaS curvature): go straight to remedy 3.
- Cost: one cache load, ~260 GB through mem_gate, ~2–4 h.

### 5. The test: SATP (full spectral preconditioning) PASSES

**Caveats first.**
- SATP is SATB8's command with only two changes:
  - the preconditioner flags;
  - `smooth=relu2`, written out explicitly so the wall is the same relu2 wall: the default became C2 in WRemnants
    692f9483.

  Everything else is the same: seed, cache (the `scetlib_ad_caches` path is the same directory as SATB8's
  `ad_scetlib_caches` symlink), rabbit 2a59246, and the SCETlib gamma-nu-points build 6ab371a. As a replay check,
  SATP's full saturated chi2 reproduces 753.35/777.
- Node load differed between runs. t_HVP was 6.25 s for SATP, 6.1 s for SATC2 and 8.9 s for SATB8. Compare the
  counts; the wall times are shown for completeness.
- One run, one start point (the data), so this measures nothing about scatter. Toys have a shorter valley
  (q ~ 39 per toy), so the gain there is not measured.

| run | wall | preconditioner | iterations | nfev | nhev | minimiser wall | + reference Hessian | to q-to-go < 0.1 | < 0.01 | < 2e-6 | final loss - SATB8 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SATB8 | relu2 | none | 158 | 156 | 2150 | 5.82 h | - | 3.10 h (it. 126) | 4.03 h (142) | 4.86 h (153) | 0 |
| SATC2 | C2 | none | 161 | 159 | 2141 | 4.08 h | - | 2.26 h (128) | 2.99 h (147) | 3.49 h (157) | -4.9e-6 (C2 equilibrium shift, a different wall) |
| SATB8SA | relu2, seeded | none | 67 | 69 | 1002 | 3.10 h | - | 0.74 h (41) | 1.36 h (52) | 2.39 h (63) | +1.2e-11 |
| **SATP** | relu2 | **full spectral** | **69** | **71** | **614** | **1.32 h** | +306 s | **0.62 h (52)** | **0.82 h (59)** | **1.14 h (66)** | **-1.7e-10** |

![progress with SATP](subfit_progress.png)

*All four sub-fits. SATP is purple. The q-to-go axis is measured against each run's own final loss. The runs had
different node loads, so read the right panel (per iteration) for the like-for-like comparison.*

- **Success criterion met: nhev 614 <= 700.** That is 3.5x fewer HVPs and 2.2x fewer loss+gradient evaluations than
  SATB8.
  - Converted to SATB8's per-call costs (t_f 12.2 s, t_HVP 8.9 s), plus the 306 s reference Hessian: 71 x 12.2 +
    614 x 8.9 + 306 = 6.6e3 s = 1.8 h, against 5.82 h. **About 3x at equal load**, at the top of the predicted 2-3x.
  - Against SATC2, at a similar load: 1.40 h vs 4.08 h including the reference Hessian, 2.9x.
- **Same answer.**
  - Final loss 337.47616205795, 1.7e-10 below SATB8's.
  - q = 78.398 vs 78.398, ndf 39, p = 0.02 %.
  - Converged vectors agree to max |dx| = 4.0e-8 in the internal coordinate. The largest difference is in alphaS; it is
    a difference only, and no value was read.
- **What the preconditioner did** (SATP.log). The reference Hessian at the sub-fit start took 306 s, with lambda in
  [-4.38, 1.78e8], one negative and none floored, the same spectrum as HDIAG's H_s. The condition number went 1.26e10 -> 1.
- **What is left: the predicted stale-curvature tail.**
  - Steps were large up to q-to-go ~ 4 (it. 0-11, 4 min).
  - After that it is linear convergence again: one deep solve (130-340 s, up to 93 HVPs) per cycle, gaining ~0.6x per
    cycle. That is the alphaS-direction curvature drifting away from the start-built transform.
  - Its deepest solves are about 3x shallower than SATB8's: max 93 HVPs, against 267.
  - 40 % of the time sits in 4 solves of >= 300 s, all below q-to-go 0.01.
- **The gtol question.**
  - rabbit does not log ||g_y||, so the trajectory cannot say where `--minimizerGtol 0.03` would have fired.
  - The model bound ([scripts/gtol_model.py](scripts/gtol_model.py) -> [gtol_model.json](gtol_model.json)) uses
    T^T H_e T in the start-built frame. Along its eigendirections, dL/||g_y||^2 ranges from 4e-5 to 477, the large end
    being the soft alphaS direction. So gtol 0.03 could stop anywhere between Delta q ~ 1e-7 and 0.86: not a safe stop.
    A guaranteed Delta q <= 0.01 needs gtol <~ 3e-3.
  - I also tried a one-ray quadratic model; it is off by 28x against HDIAG's measured point, so I do not use it.
  - The prize, for scale: stopping exactly at q-to-go 0.01 (it. 59, 2969 s) would have saved **1766 s, 37 % of SATP's
    minimiser time**. A safe version needs an EDM-type test (rabbit change), or remedy 4 (rebuild the preconditioner
    mid-fit, which would also shorten the tail).

**Physics read.** Nothing physical changes: the same M1 minimum and q = 78.40/39 (p = 0.02 %). The preconditioner is a
pure reparametrisation, as rabbit documents and as the 4e-8 vector agreement confirms. For the saturated p-value toys
this cuts the sub-fit cost about 3x at equal load. Each toy also pays one ~300-900 s reference Hessian (one per sub-fit,
and one more per main fit if the flag also applies there: it is a fitter-wide option).


---

## Findings

1. The projected-ptll saturated sub-fit spends 89–91 % of its time in Hessian-vector products. At LATB8 that is
   ~2150 per sub-fit, with up to ~270 in a single late Krylov solve. The C² wall changes neither the iteration count
   nor the HVP count (2141 vs 2150). (evidence: [cost_breakdown.json](cost_breakdown.json))
2. M1's Hessian has κ ~ 1e9–1e10. The active wall face(s) and the 39 bin scales (4N_j ~ 1e6) set the top of the
   spectrum; alphaS+resumTNP directions set the bottom (ρ²(alphaS, scales) = 0.979). The minimum lies 9.6 σ_M0 away
   along a curved valley, and the soft curvature changes by 1e3–1e4 along it.
   (evidence: [spectra.json](spectra.json), [path_params.json](path_params.json))
3. An exact Newton step is useless for this sub-fit, even 0.4 NLL from the minimum. A trust region is required.
   (evidence: `newton` and `N2` in [hess_diag.json](hess_diag.json))
4. Profiling the bin scales out analytically (s_j = N_j/ν_j) straightens the valley. The loss falls monotonically
   along the profiled straight line, and the profiled point matches the joint optimum to 2e-10.
   (evidence: [valley_line.png](valley_line.png))
5. **Tested (SATP).** Full-scope spectral preconditioning of the saturated sub-fit (`--precondition --preconditionParams '.*'
   --preconditionBlocks none --preconditionTransform spectral`) reaches the same minimum (ΔL −1.7e-10, q unchanged)
   with 3.5× fewer HVPs (614 vs 2150) and 2.2× fewer loss+gradient evaluations. That is ~3× in time at equal load,
   including a 306 s reference Hessian. A `--minimizerGtol` stop is NOT safe in the start-built whitened frame: the
   soft alphaS curvature drifts, so ||g_y|| maps to Δq anywhere in 1e-7–0.9. (evidence:
   [cost_breakdown.json](cost_breakdown.json), [compare_satp.json](compare_satp.json), [gtol_model.json](gtol_model.json))
6. Offline, full-scope spectral whitening cuts the CG work per solve 3–4×. Partial scopes make the conditioning worse: rabbit's
   default cw == 0 block, the scale block alone, and Jacobi. This deserves a line in `knowledge/` once SATP confirms
   it. (evidence: `precond` in [spectra.json](spectra.json))
7. `--earlyStopping N --stallRelTol` cannot safely shorten a sub-fit: it fires on false plateaus, with q errors of
   0.36–20. (evidence: [replay_stop.json](replay_stop.json))
8. HDIAG's in-job per-call timings were memoised cache hits. Any timing measurement must use distinct points.

---

## Open questions

- At the M1 minimum λ4_ν sits on its face with a relu² leak of −1.09e-5 GeV⁴. That is |Δγ_ν| ~ 0.27 at b_max, against
  γ_ν ~ −22 there, so it is small inside the cache. It is the same class of leak as CMR1B's, but in the saturated
  model. Not chased.
- Toys have q ~ 39 per toy, so their valley is shorter but has the same structure. The same relative gains are
  expected; this has not been measured.
- Should rabbit print ‖g_y‖ or EDM per iteration under `--precondition`? That would let remedy 2 be read off a log.
