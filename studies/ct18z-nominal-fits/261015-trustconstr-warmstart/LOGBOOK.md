---
title: trust-constr warm start
slug: 261015-trustconstr-warmstart
study: ct18z-nominal-fits
status: done        # active | done | paused | abandoned
created: 2026-10-15
updated: 2026-10-19
owner: study-worker
---

# trust-constr warm start

**Task:** Can rabbit's trust-constr (hard `--constraints`) restart from a point at or near the constrained minimum WITHOUT walking away from it (saturated sub-fits, `--externalPostfit` refits, toys, scans), and what exactly fixes it?

---

## START HERE (status as of 2026-10-19)

- **Answer:** yes. There are three separate mechanisms, not one, and rabbit branch `tc-warmstart` (commit `f84e0a8`,
  off WMass main 2d9f380, now PR #195) fixes them with `--minimizerWarmStart {auto,on,off}`, default auto. On the toy the
  warm start converges with no loss excursion (worst 5e-12, against 0.5 before) and no wrong answers (0/44 runs,
  against 11/44). On rabbit's own saturated test the sub-fit takes 18 iterations instead of 82.
- **Next action:** none in this task: #195 is ready and waiting for review. The pinned worktree
  `/work/submit/lavezzo/rabbit-pr195-run` and the base worktree `/work/submit/lavezzo/rabbit-base-2d9f380` can be
  removed.
- **Blocking on:** nothing. #195 is READY at b2b965e (CI green, bot clean, 0 open threads).
- **Running:** nothing.

---

## Log

### 2026-10-19
- **PR195_LAT finished** (18:22 on 2026-10-18; this PR only, 117cc67, no preconditioner; script
  `pr195_validation/compare_lat_real.py`). One warm leg, started from the centred barrier 4.1e-10; no face released.
  - Result: status 2 (radius < xtol, barrier 4.1e-10), optimality 3.0e-4, no violation, 115 iterations / 11.3 h.
  - q = **79.107113**, against 79.107113 for SATWSPC_LAT (this PR + preconditioner: status 1, 89 iterations / 3.6 h),
    Δq 6e-8. The point agrees with SATWSPC_LAT to <= 2.5e-6 sigma over all 3759 parameters.
  - The plain sub-fit (main) took 226 iterations / 12.8 h and ended frozen at status 2, with the active face at a
    slack of 9e-6. It sits 8.7e-5 higher in loss, so its q of 79.10694 is 1.7e-4 low.
  - **Read:** no regression. This PR alone reaches the same minimum in half the plain run's iterations; the speed
    comes from the preconditioner.
- Added as a "second real check" to the #195 validation comment (edited in place; copy in
  `pr195_validation/pr_comment.md`). #195 stays ready.

### 2026-10-18
- **PR195_NOLAT finished** (10:56; isolated: #195 only, no preconditioner; `fitresults_PR195_NOLAT.hdf5`; comparison
  script `pr195_validation/compare_nolat_real.py`). The NOLAT_PF reference is f84e0a8 + preconditioner.
  - Legs `warm, release-step, warm`; scipy's start was never used.
  - The warm leg stopped on cubic(|Y|=2.5) (mu -1.48, distance 1.6e-9), exactly as in NOLAT_PF. The release step
    (0.000217 along the normal) LOWERED the loss, 335.5372832 -> 335.5370706.
  - Neither leg rose above its own start loss, and the constraint violation stayed 0 throughout.
  - q = 68.363489 vs 68.363489 for NOLAT_PF (diff 3.4e-7). Saturated loss 335.5369528 vs 335.5369526. All 3759
    parameters agree to <= 8.6e-5 sigma. Same constraint values.
  - It ended at status 2 (xtol with barrier 7e-10 < barrier_tol), optimality 6.6e-4. NOLAT_PF, which had the
    preconditioner, reached status 1.
  - Cost: 237 iterations / 13.0 h (125 + 112, each leg with a ~38-iteration radius-collapse tail), against about 173
    iterations / ~2.7 h for NOLAT_PF with the preconditioner. The wall times are not comparable: the node load is
    shared (~600). NOLAT's plain sub-fit was killed (SIGTERM), so this case has no plain reference.
  - **Read:** the fix solves the correctness problem (frozen stop on the face, walk-away) without the preconditioner.
    The speed on this fit comes mostly from the preconditioner.
- New rule (Luca): mark a PR ready only when CI is green AND every comment, from the bot and from humans, is
  resolved. So #195 went back to draft. The hodor bot (on 117cc67) had flagged a P3: the `--minimizerWarmStart` help
  text still said the fit "continues from scipy's own start". Fixed in **b2b965e** (help text; the PR description is
  updated too; the `fit()` docstring and the `warm_start` module were already right). I replied on the PR with the
  SHA. The bot skips drafts, so its re-review was dispatched by hand (`gh workflow run hodor-review.yml -f
  pr_number=195`). Result on b2b965e: all CI jobs pass (all-unit-tests, fits, scans, linting, ...); the hodor
  re-review says "No issues found" (the P3 is fixed); there are 0 unresolved review threads and no human comments.
  Marked ready.
- Posted the validation comment on #195 (claim -> test -> result: the real check above plus the local CI-gap table;
  copy in `pr195_validation/pr_comment.md`) and marked #195 ready. LAT is marked pending in the comment.

### 2026-10-17
- **Real-fit bug in the first version (f84e0a8).** It showed up on NOLAT's ptll saturated sub-fit (NOLAT_PF, branch
  all3-local d573c1d, which combines this fix with the preconditioner; log
  `/ceph/.../261016_nolat_postfit/NOLAT_PF.log`).
  - The warm leg converged in 44 iterations / 58 min to 335.537283. It then spent 38 rejected iterations / 33 min with
    the trust radius collapsing ON the curved face cubic(|Y|=2.5), at status 2. That face's multiplier had turned
    releasing (-1.48, distance 1.6e-9).
  - The dual-sign check fired and fell back to scipy's start (mu 0.1). That walked away (335.537 -> 335.92, lambda2
    0.14 -> 0.24, cubic violated by 3.4e-3) and took 90 iterations / 72 min to converge at 335.536953 (q 68.36).
  - Why the warm leg stops on the face: in the scaled interior-point step, a slack of 1e-9 has a loss gradient
    mu_i*s_i of about 1e-17 and a barrier push mu of about 1e-8. Neither survives scipy's relative CG stop next to the
    2.8e-6 residual left in the other directions, nor the loss noise. Inside one leg only a large barrier pushes off a
    face, and a large barrier is exactly the walk-away. So the warm leg cannot avoid stopping there.
- **Fix, commit 117cc67, pushed to the PR.** When the check fires, take a release step and start a new centred warm
  leg from there, for at most 3 rounds. scipy's start is now only the last resort.
  - The release step: a Newton step on the loss along the releasing rows' unit normals, with the binding near rows held
    to first order (their gradients projected out), using one HVP. It is halved until the loss decreases and no row is
    violated (`warm_start.release_direction`, `Fitter._release_step`).
  - New test `test_warm_leg_stopped_on_a_releasing_face_is_released_warm`. It simulates the stalled warm leg on the
    test model: the data are scaled by 1.3, so the curved cubic face must release. Result: legs
    `warm, release-step, warm`; no scipy-start leg; no loss rise above the start; no violated row; the reference
    minimum is reached.
  - Toy S8 (`toy_strategies.txt`): the 3 releasing cases now take [42, 15], [28, 26] and [32, 20] iterations, against
    [42, 613], [28, 294] and [32, 534] with the old fallback (S7). Still 0/44 wrong answers.
  - Suite: 483 passed, 1 failed. The failure is `test_snapshot.py::test_sigterm_writes_a_snapshot_before_the_process_dies`,
    a wall-clock assertion (19.9 s > 15 s at load average 680). It passes alone (11/11). Lint is clean.
- Launched (through mem_gate, MAXRUN=2), both isolated from the preconditioner, from the pinned worktree
  `/work/submit/lavezzo/rabbit-pr195-run` @ 117cc67:
  - PR195_NOLAT: NOLAT's ptll saturated sub-fit only, from `fitresults_NOLAT_PF.hdf5` with `--noFit`. This is the
    releasing-face case.
  - PR195_LAT: the same for LAT, from `fitresults_LAT.hdf5`. Its plain sub-fit took 226 iterations / 12.8 h,
    q 79.10694.

  Outputs go to `/ceph/.../261017_pr_validation/`. Both are queued in the shared gate behind 7 others.
- Local before/after checks for what CI does not cover: `pr195_validation/run_checks.sh`, comparing WMass main
  2d9f380 (BASE) with the PR at 117cc67 (NEW). The table comes from `recompare.sh` (`recompare.out`); outputs are in
  `/ceph/.../261017_pr_validation/local_checks/`.
  - **Bit-identical (worst |diff| = 0 over every stored leaf, every results group):**
    - the CI nominal fit (impacts plus 6 mappings), the CI blinded fit, toys `-t 3`, and the saturated test plus scan,
      all with the default minimizer;
    - a cold trust-constr fit with constraints;
    - `--minimizerWarmStart off` at every warm site: saturated test, `--externalPostfit` refit, scan, toys;
    - toys under auto, since they start cold;
    - with the scipy guard forced to fail, the warm-hinted fit equals the cold fit (dx = 0, nit 34 = 34).
  - **Caveat on the CI blinded config:** it is nondeterministic run to run on the base as well. The first base run
    converged at trust-krylov status 2 in 19 iterations; three repeats each of base and new all took the
    stalled-and-restarted path. The parameters are identical either way, so `minimizer_status` is excluded for that
    row.
  - **Warm sites under auto, compared with before:**
    - saturated test: worst |diff| 3.9e-10; the sub-fit takes 38 iterations at status 1, against 69 at status 2;
    - `--externalPostfit` refit: identical; 1 iteration against 5;
    - scan: the curve is equal to 3.2e-5 in dNLL. The PR's points are lower or equal everywhere, i.e. better minimised:
      the base's cold restarts stop at gtol with a larger barrier gap. Per point it takes 3–4 iterations (one point 16)
      against 11–26 (`--scanSaveDetail`). The total wall time on the toy was 34 s against 19 s, which is one-off
      tracing of the extra TF functions and node load; per-point wall time is lower.
  - Suite: 483 passed, 1 timing flake (see above).

### 2026-10-16
- The real-fit validation was done elsewhere, in task 261016-saturated-subfit-diagnosis, on branch satdiag-ws-pc
  0395383. That branch combines this fix with the trust-constr preconditioner, so the two fixes' shares are not
  separated. The run was LAT's saturated ptll sub-fit:
  - plain run: ended FROZEN at status 2 (this task's cause (c)), q 79.10694, 226 iterations / 4667 HVPs / 12.8 h;
  - combined run: status 1, optimality 2.5e-9, q 79.10711, the same point to <= 1.3e-4 sigma, 89 iterations / 982 HVPs
    / 3.6 h, so 3.9x faster.
- Luca approved the PR. The suite was rerun on f84e0a8: 482 passed, and lint is clean. Pushed and opened
  https://github.com/WMass/rabbit/pull/195 (separate, not stacked).
- Findings 1-4 (plus: the saturated `edmval` is the unconstrained EDM) were added to
  `knowledge/20_frameworks/rabbit_minimizer_tolerances.md`. That section also says how to recognise a frozen status 2.
  The note's old line "fixing needs copying the driver" is marked as superseded.

### 2026-10-15
- Worktree `/work/submit/lavezzo/rabbit-tc-warmstart`, branch `tc-warmstart` off WMass main 2d9f380.
- Read the scipy 1.18 internals (`tr_interior_point.py`, `equality_constrained_sqp.py`, `qp_subproblem.py`,
  `minimize_trustregion_constr.py`). One detail the brief did not have: when a row has `keep_feasible=True`,
  `BarrierSubproblem._compute_function` overwrites that row's slack IN PLACE with c - lb. It writes into scipy's own `s0`
  array before `z = hstack((x0, s0))` is built. So rabbit's held rows (every row of a strictly feasible start) already
  start with a consistent slack. The `max(1.5(c-lb), 1)` init only affects rows that are NOT held: rows exactly on their
  bound, and every row of an infeasible start (TCA's case).
- Toy (`toy_warmstart.py`): 40 parameters, kappa 1e3, 8 rows (4 linear, exp, cubic, a ball on a 3-d projection), 3-5 of
  them active depending on the seed. With kappa >= 3e3, unpreconditioned trust-constr does not converge cold within 3000
  iterations, so the toy uses kappa = 1e3. Production tolerances throughout (gtol 1e-8, xtol 1e-10, barrier_tol 1e-9).
  The scripts are knob grids (`toy_grid.py`, tables `print_grid.py`, `summarize_grid.py`), whole strategies
  (`toy_strategies.py`, output `toy_strategies.txt`), fallback chains (`toy_fallback.py`) and the trust radius
  (`toy_tr0.py`, `toy_tr0.txt`). Raw results are in `toy_*.json`.
- First grid (`toy_grid.json`). Rabbit's keep_feasible rule FREEZES warm starts of a modified problem: from the old
  minimum of a toy with the data moved, every run stops at status 2 ("success") or at maxiter, away from the new
  minimum. With only linear rows the same starts converge (scratch check), so it is the held CURVED rows that freeze.
  This was a third mechanism, not in the brief.
- Second grid (`toy_grid2.json`, 3 seeds). A small mu0 with slack = c - lb is fast, but when the active set has to
  change it stops at status 1 on a face it should leave. scipy's KKT test does not check the multipliers' sign. A
  dual-sign check catches every case (`toy_strategies.py` S4: 8/8).
- Implemented in rabbit, first with a fixed warm mu0 = 1e-9. On rabbit's saturated test the warm sub-fit then sat at its
  start slack, 2.1e-7, for 43 iterations, and for 113 with mu0 = 1e-5. Instrumenting scipy's SQP
  (scratch `dbgsqp/eqsqp_dbg.py`) showed the cause. The slack residual -mu + v*s (6e-8) is left untouched by the
  projected CG next to a 2e-7 x-gradient. The resulting x-steps predict 1e-14 to 1e-16 of gain, while rabbit's loss has
  noise of about 1e-12 between evaluations, so every step is rejected and the radius collapses. Fix: start the barrier
  ON the start's central path, mu0 = max over near rows of multiplier*slack (`centred_barrier`). That gives 2.56e-7,
  which is exactly the main fit's final mu, and the sub-fit then converges in 18 iterations.
- The cold LAT saturated ptll sub-fit, which is running now in LAT.log, is the real-data reference. At 16:38 it had run
  82 min and reached iteration 10, with mu still 0.1 and the loss down from 376.473 to 337.896.
- Suite: `tests/` 482 passed in the container (27.6 min, worktree prepended to PYTHONPATH so the subprocess tests import it); container black/isort/flake8 clean (CI flake8 selection: 0) on the changed files. Commit
  `f84e0a8` on `tc-warmstart`.

---

## Result

**Caveats first.** All numbers below are from a toy (scipy only, exact arithmetic) and from rabbit's 3-parameter test
model. Nothing ran on real data. The toy is kept at kappa = 1e3 because unpreconditioned trust-constr cannot solve
kappa >= 3e3 cold. That is a separate problem, handled by branch `tc-precond`. The "same minimum" comparisons carry a
barrier gap of about multiplier x slack (the barrier parameter mu) per active face, because scipy's gtol exit does not
wait for mu. For LAT that gap is 4e-10.

### 1. Mechanism: three separate effects, plus one rabbit-specific trap

![toy restarts](toy_restart_loss_vs_iteration.png)

*The toy at seed 3 and production tolerances. Loss minus the constrained minimum (symlog) against iteration. Red is
rabbit before this change, orange is scipy's start with no row held, blue is the warm start. A toy, not a real fit.*

The toy has 5 seeds x 9 starts, with "before" being rabbit at 2d9f380. The cold fit itself takes 80-116 iterations.

| effect | what it costs (toy) | what fixes it |
|---|---|---|
| **(a) slack init** `s0 = max(1.5(c-lb), 1)`. It only affects rows *not* held feasible: rows exactly on a bound, and all rows of an infeasible start | start on the active faces: loss **+0.3 to 0.5**, back after 75-170 iterations. Start 1e-4 past them: **+0.2 to 0.9**. The excursion scales with the initial slack: delta = 1e-2 / 1e-4 / 1e-6 gives 4e-2 / 2e-4 / 2e-6 (`toy_grid.json`). This is TCA's +333 NLL. | `s0 = max(c - lb, floor)` |
| **(b) mu0 = 0.1**, reduced by only x0.2 per stage | restart AT the minimum (rows held, so no slack problem): no excursion, but **11-78 iterations** to re-descend the barrier ladder | mu0 on the start's central path: **1 iteration** (median) |
| **(c) keep_feasible pinning** (new). Every row of a strictly feasible start is held, and its slack stays at c - lb, about 1e-9 on an active face | start at the old minimum after the data moved (toys, scans, saturated): **11/44 runs end away from the new minimum**, at status 2 ("success") or maxiter, f - f* = 0.03 to 14. Linear-only rows converge, so the culprit is the curved held rows, which reject every step that crosses them | hold no row feasible in a warm leg |
| **(d) scipy status 1 does not check the multipliers' sign** | aggressive warm start (mu0 = 1e-9): **8/44 false stops** on faces the loss wants to leave, f - f* = +0.04 to 0.31 | dual-sign check, then continue from scipy's start (catches 8/8) |
| trust radius `initial_tr_radius` | **none**: 1, 1e-2 and 1e-4 give the same excursion and +-20 % iterations (`toy_tr0.txt`) | — |

Rabbit-specific trap (e). A warm mu0 that is far off the start's central path stalls in rabbit, although it does not
stall in the toy. This happens with mu0 << v*s and also with mu0 >> v*s. Two things combine. scipy's projected CG uses a
relative stopping rule and skips the small slack residual. rabbit's loss has about 1e-12 of noise between evaluations,
so the remaining tiny x-steps are all rejected. On rabbit's saturated test this meant 43 iterations stuck at mu0 = 1e-9,
and 113 at mu0 = 1e-5. The centred mu0 = 2.56e-7 took 18 iterations. So the warm mu0 cannot be a constant.

### 2. The fix (rabbit `tc-warmstart`, commit `f84e0a8`)

- New module `rabbit/constraints/warm_start.py`:
  - `consistent_slacks(floor)`: sets trust-constr's starting slacks to `max(c - lb, floor)` by subclassing scipy's
    private `BarrierSubproblem` for the duration of the scipy call. It overwrites the `s0` array in place, and that is
    the same array scipy then stacks into its starting point. It is not a vendored copy of the driver.
  - `scipy_supports_slack_override()`: run-time guard. If scipy's internals change, the warm start falls back to the
    cold start with a warning.
  - `centred_barrier`: mu0 = max_i mu_i*s_i over the rows near a bound, using least-squares multipliers of the binding
    sign, clipped to [1e-12, 1e-3]; 1e-9 if no row binds.
  - `releasing_rows`: the dual-sign check.
- `Fitter.fit(warm_start=False)` and `Fitter.minimize(warm_start=False)`. The warm leg (trust-constr + `--constraints`
  only) does four things:
  - holds no row feasible (new `hold_feasible` argument of `scipy_adapter.build_nonlinear_constraints`);
  - starts the slacks consistently, with floor 1e-3*mu0;
  - uses mu0 = initial barrier tolerance = `centred_barrier`, unless `--minimizerInitialBarrier*` are given;
  - checks the multiplier signs at the end. If a face should have been left, it takes a release step and starts a
    new centred warm leg from there, for at most 3 rounds. The release step is a Newton step on the loss along the
    releasing rows' normals, with the binding rows held, cut back until the loss decreases and no row is violated.
    scipy's own start is only the last resort.

    That is the 117cc67 version. The first version (f84e0a8) went straight to scipy's start, and on NOLAT's ptll
    sub-fit that walked away and cost an hour; see the 2026-10-17 Log.

  `minimizer_status` records `warm_start_legs`, `warm_start_releasing` and `warm_start_barrier`.
- `--minimizerWarmStart {auto,on,off}`, default `auto`. Under auto the warm start is used where rabbit knows the start
  is a minimum: the saturated sub-fit, a fit after `--externalPostfit`, `nll_scan`/`nll_scan2D` points, and the
  global-asymmetric-impact refits. Every other fit takes the old code path unchanged (`test_cold_path_is_unchanged`:
  bit-identical x and nit).
- Not changed: toys (`-t N`, which start from the defaults), `contour_scan` (its own scipy call), the early-stopping
  restart loop of a cold fit, the main cold fit.

### 3. Toy numbers for the implemented strategy (S7) vs before (S0)

Iterations, median [max], over 5 seeds. "fail" counts runs that ended more than 1e-5 from the reference minimum, out of
44 (one start whose own cold reference hit maxiter is excluded). "worst exc" is the largest loss rise above the
minimum for starts at or on it.

| strategy | at min | on face | 1e-4 infeasible | data moved 0.1 sigma | data moved 1 sigma | fail | worst exc |
|---|---|---|---|---|---|---|---|
| before (S0) | 11 [78] | 86 [170] | 109 [177] | 164 [2000] | 1311 [2000] | 11/44 | 0.5 |
| scipy start, no row held (S1) | 97 [121] | 91 [107] | 109 [177] | 93 [130] | 242 [1938] | 0/44 | 0.9 |
| warm start, f84e0a8 (S7) | 1 [24] | 3 [13] | 8 [14] | 14 [83] | 136 [1779] | 0/44 | 5e-12 |
| **warm start + release step, 117cc67 (S8)** | **1 [24]** | **3 [13]** | **8 [14]** | **14 [83]** | **92 [1779]** | **0/44** | **5e-12** |

For comparison, cold fits of the 1-sigma toys take a median of 212 iterations. In 3 of 44 runs the warm leg stopped
falsely and the dual-sign check sent it to the release leg; those are in the 1-sigma column. The `[24]` at the minimum
is two seeds where the least-squares multipliers put the start's optimality just above gtol. Those runs make no change
to the loss, and the 24 rejected iterations only collapse the radius down to xtol (status 2). That is about 11 min of
loss+gradient calls on the real fit.

### 4. Tests (`tests/test_trust_constr_warmstart.py`, 13 tests)

The scipy-internals tests fail loudly if scipy changes:
- `test_scipy_internals_still_support_the_slack_override`;
- `test_scipy_slack_init_is_what_the_warm_start_works_around` pins scipy's `[1, 1, 1.5*(c-lb)]` and `[1, c-lb, c-lb]`
  initial slacks;
- `test_consistent_slacks_reach_the_first_iterate` spies on the z that the first SQP starts from.

The rabbit-level tests:
- Restart at the minimum: at most 3 iterations, no excursion above 1e-6, the same x (1e-6), the same multipliers and the
  same face-held covariance (1e-4).
- Start exactly on a face: no excursion. The old start's excursion of more than 1e-2 is asserted as well.
- A moved minimum (Poisson toy data) is found.
- A face that must be released is released.
- The cold path is bit-identical.
- The scipy fallback and the no-constraints case are inert.
- The saturated test end to end: the warm sub-fit has fewer iterations than the cold one, and |dNLL_sat| < 1e-6.

`tests/test_trust_constr.py` passes unchanged (24/24), and the full suite is 482 passed in the container (27.6 min, worktree prepended to PYTHONPATH so the subprocess tests import it). On the test model: restart at the
minimum takes 1 iteration (3 before). The on-face start takes 3 iterations with no excursion (19 iterations and +0.218
before). The saturated sub-fit takes 18 iterations (82 before), with its NLL 1e-8 above the cold one; both are within
their barrier gaps.

### 5. Proposed real-fit test (NOT run; for Luca to approve)

> **Superseded 2026-10-18.** SATWS_LAT below was never run as proposed. It was replaced by three runs:
> - SATWSPC_LAT: the combined warm start + preconditioner run, in
>   [261016-saturated-subfit-diagnosis](../261016-saturated-subfit-diagnosis/LOGBOOK.md);
> - PR195_NOLAT (done): this PR only;
> - PR195_LAT (done 2026-10-18, q 79.107113): this PR only.
>
> The PR195 runs are in the 2026-10-17 and 2026-10-18 Log entries, and in the #195 validation comment
> https://github.com/WMass/rabbit/pull/195#issuecomment-6253853702. The proposal is kept below as written.

**SATWS_LAT** reruns only the saturated ptll sub-fit, warm, from LAT's own final postfit. It goes through mem_gate like
the other big loads, and the flags are LAT's own (LAT.log line 3), minus the impacts. Run it after LAT has finished and
rewritten `fitresults_LAT.hdf5`; the current file dates from 10:12 and is not the final one. LAT's own sub-fit, cold
path, which is running now, is the reference.

```
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261015_ct18z_nominal_fits
CARD=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5
CACHE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_y35_260921_y25
mem_gate.sh 260 $OUT/SATWS_LAT.log -- /home/submit/lavezzo/alphaS/WRemnantsHelpers/agent_setup.sh \
  --scetlib /work/submit/lavezzo/alphaS/scetlib-gamma-nu-points/scetlib-cms/build \
  --prepend-pythonpath /work/submit/lavezzo/rabbit-tc-warmstart -- \
python /work/submit/lavezzo/rabbit-tc-warmstart/bin/rabbit_fit.py $CARD --jitCompile off -o $OUT -t 0 \
  --postfix SATWS_LAT --externalPostfit $OUT/fitresults_LAT.hdf5 --noFit --saveHists \
  -m Project ch0 ptll --computeSaturatedProjectionTests \
  --regularizationStrength 8 \
  -r wremnants.postprocessing.scetlib_ad.lattice_cs_term.LatticeCSTerm wremnants.postprocessing.scetlib_ad.lattice_cs_term.LatticeCSTermMapping \
  --constraints wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDomainConstraints margin=0 \
  --minimizerMethod trust-constr --earlyStopping -1 --maxRestarts 0 --minimizerGtol 1e-8 \
  --minimizerXtol 1e-10 --minimizerBarrierTol 1e-9 --minimizerMaxiter 600 \
  --snapshotFile $OUT/snapshot_fitresults_SATWS_LAT.hdf5 --snapshotInterval 0.25 \
  --paramModel wremnants.postprocessing.scetlib_ad.SCETlibADParamModel \
  cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128 -v 4
```

`--minimizerWarmStart` is left at auto, which makes the saturated sub-fit warm. With `--noFit` the main fit is not
rerun, but the main postfit Hessian is recomputed once, which takes about 5-15 min.

- **Expect** in `results/mappings/Project ch0 ptll/saturated_fit/minimizer_status`: `warm_start_legs == ['warm']`, and
  `warm_start_barrier` approximately equal to LAT's final barrier parameter, 4.1e-10. The L2(|Y|=2.5) face multiplier
  is 6.41 and its slack 6.4e-11.
- **Pass:**
  - |Δq| < 0.01 against LAT's own saturated test, where q = 2 dNLL. Expect about 1e-6 or less, since both carry only
    the barrier gap.
  - The same `constraint_values` and active faces.
  - Saturated-fit parameters within 0.01 sigma. Compare blinded values only as differences, and only if both runs use
    the same blinding frame: my branch lacks the local `--blindingFrame` commit 196bfca, and LAT uses its default
    `auto`.
- **Payoff:** nit and wall time against LAT's cold sub-fit, which at 82 min was at iteration 10 with mu still 0.1.
  The expectation is about 15-30 iterations, against the cold ladder of 11 barrier stages.
- **Optional, cheap: RESTART_LAT.** The same command without `--noFit`, without `-m`, and without the saturated flags.
  This is the "restart from its own minimum" case, TCA's 7.2 h. Expect 1 to a few iterations, the loss equal to 1e-6,
  and the same multipliers.

### 6. Risks

- **scipy internals.** The fix depends on a private class (`BarrierSubproblem`), on its argument names `s0` and
  `constr_ineq0`, and on `tr_interior_point` stacking the same `s0` array it passed on. Two things guard this: a run-time
  check, which falls back to the cold start with a warning, and three tests that fail loudly. The subclass swap is not
  thread safe, but rabbit makes one scipy call at a time.
- **Rows not held feasible.** A warm leg holds no row feasible, so its iterates can step slightly past a face before
  the fit ends feasible to gtol. The NP model is finite there, but the AD cache is not exact for lambda2_nu < 0
  (`knowledge/20_frameworks/scetlib_ad_cache_validity.md`). Cold fits keep rabbit's rule.
- **Rebase against `tc-precond`.** Both branches change the signature of `build_nonlinear_constraints` and the
  `build_scipy_constraints(...)` call in the trust-constr branch of `fit`. The conflict is small and mechanical. The
  slack hook, the centred mu0 and the dual check do not depend on the frame (multipliers and feasibility are
  frame-invariant), but this has not been tested together with `--precondition`.

---

## Findings

1. scipy trust-constr overwrites the slacks of `keep_feasible` rows with c - lb in place. The
   `s0 = max(1.5(c-lb), 1)` walk-away therefore only hits rows not held feasible: rows exactly on a bound, and every row
   of an infeasible start such as a penalty-walled fit. That was TCA's +333 NLL. (evidence: scipy
   `tr_interior_point.py` l.325 plus `BarrierSubproblem._compute_function`; toy `toy_grid.json`, where the excursion
   scales with the initial slack)
2. rabbit's keep_feasible rule freezes warm starts of a MODIFIED problem: 11/44 toy runs stop at status 2 or maxiter
   away from the minimum. The cause is the held curved rows at about 1e-9 slack; linear rows do not freeze. (evidence:
   `toy_strategies.txt` S0; scratch linear-only check in the Log)
3. scipy's status 1 does not check the multipliers' sign, so a small barrier on a face that should be released stops
   there and reports "success". (evidence: `toy_grid2.json`, `toy_strategies.txt` S3: 8/44)
4. In rabbit a warm mu0 must sit on the start's central path, mu0 = multiplier x slack. Off it, in either direction, the
   fit stalls: the relative CG stop skips the slack residual, and loss noise of about 1e-12 rejects every remaining
   step. (evidence: Log, rabbit saturated test 43/113 vs 18 iterations)
5. The initial trust radius does not contribute to the walk-away. (evidence: `toy_tr0.txt`)
6. Generalizes → knowledge: findings 1-4 belong in `knowledge/20_frameworks/rabbit_minimizer_tolerances.md` §"Even with
   tolerances set, trust-constr is a certifier". Its line "Fixing it means copying scipy's interior-point driver" is
   superseded, because a subclass hook suffices.

---

## Open questions

- A cold constrained fit can also stop falsely at status 1 on a face it should leave, since finding 3 is generic. A
  warn-only dual-sign check at the end of every constrained fit would cost one gradient. It is not added, to keep the
  cold path untouched.
- The early-stopping restart loop of a cold fit still restarts from scipy's start: the TCA-type reset, plus
  keep_feasible pinning.
- Toys from the postfit (`-t N`) start cold. Whether they should start warm depends on where their start is meant to be.
- The certification tail: at an exact minimum whose least-squares optimality sits just above gtol, 24 rejected
  iterations are spent collapsing the radius (2 of 5 toy seeds).
- `contour_scan` has its own trust-constr call, which is untouched.
