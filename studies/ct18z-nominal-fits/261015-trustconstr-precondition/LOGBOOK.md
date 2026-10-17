---
title: trust-constr + preconditioning
slug: 261015-trustconstr-precondition
study: ct18z-nominal-fits
status: done          # active | done | paused | abandoned
created: 2026-10-15
updated: 2026-10-16
owner: study-worker
---

# trust-constr + preconditioning

**Task:** Can rabbit's `--minimizerMethod trust-constr` with hard `--constraints` be made to work together with `--precondition` (in particular the full-scope spectral preconditioner), and would it pay off for the main fit and the projected-saturated sub-fit?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-10-16)

- **Answer:** feasible, implemented and validated; **PR opened: https://github.com/WMass/rabbit/pull/194** (branch
  `lucalavezzo:tc-precond-pr`, one commit c76c226 on WMass/rabbit main 2d9f380, without the local `--blindingFrame`).
  Real-fit validation (LAT's saturated ptll sub-fit, by task 261016-saturated-subfit-diagnosis, measured TOGETHER
  with the warm-start change): same point (<= 1.3e-4 sigma), q 79.10711 vs 79.10694, 89 it / 982 HVPs / 3.6 h vs
  226 / 4667 / 12.8 h (3.9x). Use it on warm fits only: from cold it is slower (Log 2026-10-15 16:10).
- **Next action:** none (review on the PR). **Running:** nothing.

---

## START HERE (previous, 2026-10-16 09:10)


- **SATPC_NOLAT CANCELLED; PR NOT opened (orchestrator, Luca's instruction).** NOLAT was stopped by SIGTERM at 08:57
  during its saturated sub-fit (15 h, not converged), so no `fitresults_NOLAT.hdf5` exists. The launcher (pid
  2669526) saw the non-normal exit at 08:58, did NOT queue anything, and exited ([logs/satpc_launch.out](logs/satpc_launch.out)).
  Whether to open the PR is now decided by task 261016-saturated-subfit-diagnosis, which tests the preconditioner
  together with the warm-start fix on LAT's saturated sub-fit.
- **Ready for that decision:** PR branch `tc-precond-pr` = WMass/rabbit main 2d9f380 + a606337; full suite 471 passed;
  PR body draft [pr_body_draft.md](pr_body_draft.md). Add the cold-start caveat (Log 2026-10-15 16:10) to it.
- **Running:** nothing. PCLAT was stopped by the orchestrator (SIGTERM, Luca's instruction) on 2026-10-15 at
  16:32; its log ends with the SIGTERM snapshot line.
- **Next action:** none for this task until the 261016 result.

---

## START HERE (previous, 2026-10-15 16:10)


- **Diagnosis (16:10):** PCLAT is slower because the preconditioner was applied from a far cold start (toy
  reproduces it, also under trust-krylov). It is not a bug: the chain rule was verified on the real constraint rows at
  PCLAT's own iterate. See Log 16:10. Implication: precondition only warm fits (the saturated sub-fit); keep the cold
  main fit unpreconditioned. PCLAT continues as a diagnostic unless Luca says stop.


- **Answer so far:** feasible and implemented; toy-validated (Result §1–2). PR branch `tc-precond-pr` =
  WMass/rabbit main 2d9f380 + **a606337** (no `--blindingFrame`); full suite on it: 471 passed. PR NOT opened yet
  (conditional on SATPC_NOLAT passing).
- **Running (all detached, all importing rabbit from the PINNED worktree `/work/submit/lavezzo/rabbit-tc-precond-val` @ a606337):**
  - **PCLAT** = LAT's exact fitterAD command (same card/cache/SCETlib build/`-f 'threads=128 -v 4'`, fitterAD md5
    2dce383684b2 = LAT's) + the four full-scope spectral `--precondition*` flags passed via `-f`. Launched 15:05:50
    through mem_gate with MAXRUN=3 (831 GB available), gate pid 2845470. Log `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261015_tc_precond_validation/PCLAT.log`
    (gate `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261015_tc_precond_validation/PCLAT.gate`). Its own saturated sub-fit is preconditioned too.
  - **SATPC_NOLAT launcher** pid 2669526: waits for NOLAT (pid 1792824) to exit, then queues in mem_gate (MAXRUN=2).
    Logs: [logs/satpc_launch.out](logs/satpc_launch.out), [logs/SATPC_NOLAT.log](logs/SATPC_NOLAT.log).
- **NOT done (permission denied by the session's safety classifier, left for Luca):**
  - the opt-in `--tc-precondition` flag in the shared `workflows/fitterAD.sh` (PCLAT passes the flags through `-f`
    instead, which is equivalent: with `--constraints` fitterAD only drops its own `precond_arg`);
  - queueing **PCNOLAT** (NOLAT's command + the preconditioner) in mem_gate;
  - log symlinks for PCLAT in `logs/` (use the absolute paths above).
- **Next action:** when PCLAT and SATPC_NOLAT finish: `compare_satpc.py` (in this dir, run in the container) for the
  saturated test; PCLAT vs LAT for the main fit (iterations, nfev, time to within 1e-3 / 1e-6 of the final loss, final
  loss, faces, blinded alpha_s); then open the PR if SATPC passes.

---

## Log

### 2026-10-16
- PR opened, Luca approved: https://github.com/WMass/rabbit/pull/194 ([pr_body.md](pr_body.md)). Before pushing:
  the `--precondition` help gained the warm-vs-cold advice; container black/isort/flake8 clean; preconditioner and
  trust-constr tests 54 passed; commit amended to c76c226 (only change since a606337: that help text). Companion PRs
  (warm start `tc-warmstart`, face-held impacts `face-held-impacts`) are independent off main, not stacked; a small
  conflict with the warm-start one in `scipy_adapter`/`build_scipy_constraints` is flagged in the body.
- Correction: PCLAT was stopped by the orchestrator (SIGTERM, Luca's instruction) on 2026-10-15 at 16:32, not still running as START HERE had said; nothing of this task is running.

### 2026-10-15 16:10 (diagnosis: why PCLAT is slower than LAT — requested by Luca)
**Verdict: not a bug in the change. A preconditioner applied far from the minimum makes the cold fit slower, and
the toy reproduces this with unconstrained trust-krylov too.** Evidence ([diag_pclat.py](diag_pclat.py), output
[diag_pclat.out](diag_pclat.out); toy scripts in the scratchpad, numbers below):
- **(a) Chain rule on the REAL rows: correct.** The six NPDomainConstraints rows (margin=0, incl. the cubic TMD
  large-b ones) were evaluated at PCLAT's own iterate (its 15:49 snapshot) through rabbit's adapter, with a dense
  spectral T over all 3720 parameters. J_y p agrees with finite differences of c(x_ref + T y) to ≤ 3.4e-8 rel;
  (T^T d2c T) p agrees with an FD of J_y to ≤ 2e-11 abs (scale 3e-2).
- **Where PCLAT went (snapshot at ~iteration 12, loss ~3.4e4).** Displacement from the cold anchor (anchor = V2's
  prefit vector, same card): the constrained nuisances are at |d| = 17.3 (max 11.4 sigma, pdfMSHT20mbrangeSymAvg;
  QCDscale −5.4 sigma), against 5.45 (max 1.9 sigma) at LAT's minimum. Their prior term sum(theta^2)/2 is 150, against 14.8 at LAT's minimum.
  The TNP model parameters are far off too: resumTNP_b_qqS −10.8 (LAT +0.30), h_qqV +8.1 (LAT −0.63),
  gamma_nu −3.9 (LAT +0.44). PCLAT's move projects onto the anchor→LAT-minimum direction at only 0.08 for the
  model parameters and 0.59 for the nuisances; the rest (15.6 and 17.0 in norm) is orthogonal, i.e. a detour.
  The violated row is λ4_ν ≥ 0 (−0.0075). It starts ON its face, so it is not held feasible, in both runs.
- **Mechanism.** At the cold anchor the spectral transform sees lam in [−2.65e3, 5.73e4] (14 negative): κ 6.9e4 → 1.
  A unit step in y is then ≲ 1.1 physical units along the soft (prior-dominated) directions. scipy grew the
  y-radius to 343–730, i.e. hundreds of prior sigma in physical units. The anchor-quadratic model is wrong that far
  out, so steps get rejected (iterations 4, 5, 10, 12) and the iterate wanders off orthogonally. The merit
  function and barrier themselves are frame-independent (f, c, s are unchanged by the transform); what the frame
  changes is the shape of the trust region and the step proposed, so (c) and (d) are consequences, not causes.
- **Toy reproduction** (polynomial tensor, constraints as in the unit test, cold start with the poly coefficients
  displaced to ±shift):

  | order, shift (start loss) | plain trust-constr HVPs | precond (T at start) | precond (T at the MINIMUM) |
  |---|---|---|---|
  | 8, 0 (8.9) | 474 | **357** | — |
  | 8, 20 (2953) | **432** | 885 | 838 |
  | 8, 60 (19498) | **478** | 515 | 1551 |
  | 10, 60 (15929) | 1971 (xtol, not converged) | **555** | — |

  All runs reach the same minimum (|dx| ≤ 8e-8 sigma). A transform built AT THE MINIMUM is just as bad or worse
  from far away. So the cause is not that the anchor Hessian is the wrong one: any whitened metric loses far from
  the minimum. Unconstrained trust-krylov does the same (order 10, shift 60: 137 HVPs plain vs 2279 preconditioned;
  counts include rabbit's stall restarts), so this is not specific to trust-constr or to the new code. Prior
  evidence agrees: no cold main fit was ever shown faster with spectral preconditioning. The cold spectral
  DATASPEC (studies/scetlib-ad-param-model/260910-basins) ran 719 trust-krylov iterations; the measured 3x win
  (SATP) was the WARM saturated sub-fit.
- PCLAT vs LAT at equal elapsed time (iteration clock, after PCLAT's 739 s reference Hessian): 2195 s: 796 vs ~390.
  It is catching up but is behind. It is now diagnostic only; whether to stop it is Luca's call (not stopped).
- Side note for the slack question: LAT's own saturated sub-fit, started at its minimum, went 376.47 → 349.69 at
  iteration 1. It made **no upward detour** at the start.

### 2026-10-15 15:05 (main-fit speed test, requested by Luca)
- Orchestrator: also test the MAIN cold fit with the preconditioner next to LAT/NOLAT. The `--tc-precondition` edit
  of the shared `workflows/fitterAD.sh` was DENIED by the permission classifier (nothing written: the shared file
  is live under two running fitterAD bash processes). Equivalent route used: the same fitterAD.sh, `--constraints`,
  with the preconditioner flags in `-f` ([pc_main_inner.sh](pc_main_inner.sh); `set -f`, so `.*` is not globbed).
- PCLAT launched (MAXRUN=3, 831 GB available, 2/3 gated jobs alive), command verified in its log: LatticeCSTerm,
  NPDomainConstraints, `threads=128 -v 4 --precondition --preconditionParams .* --preconditionBlocks none
  --preconditionTransform spectral`; rabbit a606337 imported from the pinned worktree.
- PCLAT started cleanly: cache loaded in 667 s; preconditioner reference Hessian 739 s; 1 block of 3720 parameters,
  condition number 6.89e4 -> 1 at the COLD anchor (degeneracy 1.79e4); trust-constr start loss 114396.06;
  Iteration 0 at ~15:31.
- Queueing PCNOLAT was DENIED by the classifier (and so were the PCLAT log symlinks) — not retried; for Luca.
- NOLAT at 14:55: main-fit iteration 52, 16274 s, barrier 1.28e-6, optimality 4.3e-6 (some iterations take
  ~23 min, e.g. it 48: 1379 s).

### 2026-10-15 (PR + real-fit validation, approved by Luca)
- Rebased onto WMass/rabbit main (2d9f380) as branch `tc-precond-pr`, commit a606337 (the local 196bfca
  `--blindingFrame` is NOT in it). Self-review: diff minimal (5 files); fixed a sign in the adapter docstring
  (scipy's Lagrangian gradient is grad f + J^T v); added to the `--precondition` help that trust-constr +
  `--constraints` now work and that gtol/xtol/trust radius are then in the preconditioned frame. The refusal text
  existed only in `fitter.py` (removed). Container black/isort/flake8 (CI's F-select) clean.
- Real-fit validation set up: SATPC_NOLAT (saturated sub-fit only, from NOLAT's final postfit, preconditioned).
  NOLAT at 13:10 was at main-fit iteration 45 (10669 s, ~92 s/it, barrier 1.6e-4); `fitresults_NOLAT.hdf5` exists
  but is held open by the live process (written at the end), so the launcher waits for the process to exit.

### 2026-10-15 (later)
- Implemented and committed `2a64792` on `tc-precond` (4 files, +361/-23): `Preconditioner.jac_to_internal` (J T);
  `scipy_adapter.build_nonlinear_constraints(jac_to_internal=, hessp_to_internal=)`;
  `Fitter.build_scipy_constraints(transform=)` (current preconditioner looked up per call, so a restart rebuild is
  followed); the refusal in `fit()` removed; `minimizer_status` gains `optimality_frame` and, when preconditioned,
  `optimality_physical`. black/isort clean, flake8 F-codes clean (container tools).
- Toy scan (polynomial background, linear row poly1+poly2 <= free-1sigma, ball row on poly3/poly4 centred off the
  start; scratch script, not kept): table in Result §2.
- Tests: `tests/test_trust_constr.py` 27 passed (3 new + the saturated test refactored into `_run_saturated`);
  full suite `pytest tests/` **472 passed in 18 min** ([pytest_full.log](pytest_full.log); it ran before the last
  test was added and the loss checks were made barrier-aware, both then re-run within the 27).
- First version of the end-to-end saturated test FAILED on |dNLL| = 6.1e-6 > 1e-7: the preconditioned fit's gtol
  exit came at barrier mu = 6.4e-6 (in y the residual was 1.6e-12; in the physical frame 1.2e-10 > gtol). That is
  scipy's known "gtol exit does not wait for mu" trap, made frame-dependent; the test now allows 2 mu, like the
  existing `test_binding_constraint_matches_the_profile_on_the_face`.
- Dry run of the proposed real-fit command on the toy (scratchpad): `--externalPostfit <main> --noFit` runs the
  saturated sub-fit preconditioned (`optimality_frame` = preconditioned, residual 2.9e-11 in y vs 4.6e-9 physical).
  `--noHessian` is refused next to `--externalPostfit` ("external covariance was provided"); `--saveHists` is needed
  for the mapping results to be written.

### 2026-10-15
- Worktree `/work/submit/lavezzo/rabbit-tc-precond`, branch `tc-precond` off `main-plus-ours` 196bfca. Production
  checkout untouched.
- Code read: the refusal (`fitter.py` fit(), "does not support --precondition"), `scipy_adapter.build_nonlinear_constraints`
  (values via `to_physical`, J and the constraint HVP passed through UNtransformed), `preconditioner.py`
  (theta = theta_ref + T y, T = L^-T, linear). The orchestrator's reading is right: an implementation gap (chain rule
  on J and on the constraint HVP), not a method limitation. scipy 1.18.0 trust-constr internals checked
  (`_trustregion_constr/{minimize_trustregion_constr,tr_interior_point}.py`): lagrangian_grad = grad + J^T v,
  optimality = ||lagrangian_grad||_inf, slack scaling is per constraint (frame-independent), s0 = max(-1.5 c, 1).
- First toy (polynomial tensor of `tests/test_preconditioner.py`, linear + non-convex quadratic row): plain and
  preconditioned agree when they reach the same KKT point; with a NON-convex row (order 8) the two frames took
  different paths into DIFFERENT constrained local minima (loss 4.633 vs 5.326, both KKT, gtol/xtol exits) -- a frame
  change alters the path, so on a multimodal problem the basin can change. Tests therefore use a convex ball row.
- Found on the way (pre-existing, not preconditioning): a constraint row whose gradient is ZERO at the start point
  (e.g. a ball centred at the start) is classified "depends only on frozen parameters" and silently DROPPED
  (`live = |J|.sum(1) > 0` at xstart). See Open questions.

---

## Result

**Comparability caveats first.** Everything below is from toys (rabbit's own polynomial-background test tensor, 7–11
parameters, Poisson pseudo-data from `tests/test_preconditioner.py::make_polynomial_tensor`), not from the SCETlib-AD nominal. HVP counts are
those the minimizer asked for and exclude the one dense reference Hessian the transform is built from. No real fit
was run (both big-job slots are held by NOLAT/LAT); the real payoff is a prediction until the test below is run.

### 1. What has to be transformed, and why it is only the chain rule

With preconditioning scipy iterates in y, theta = theta_ref + T y, T = L^-T (block-wise, `rabbit/preconditioner.py`).
theta is **affine** in y, so for every constraint row

| quantity | in y | needed a change? |
|---|---|---|
| value c(theta(y)) | same numbers | no (already via `to_physical`) |
| Jacobian | J_y = J T | **yes** (was passed in theta) |
| constraint HVP | T^T (sum v_i d2c_i) T p, no term from the map (it is linear) | **yes** |
| bounds, row type | unchanged; linear rows stay linear | no |
| multipliers v | T^T (grad f + J^T v) = 0 iff grad f + J^T v = 0 (T invertible): identical | no |
| per-row keep_feasible, start-on-face, dead rows | decided from c(x_start) and the support of J: identical | no |
| slack scaling of the barrier subproblem | per row, in constraint units (scipy `tr_interior_point.scaling`) | no |
| face-held post-fit (`constraints/postfit.py`) | computed after fit() at the physical point | no |
| trust radius, `initial_tr_radius`, xtol, `optimality` vs gtol | measured in y | **meaning changes** |

So the orchestrator's reading is right. The whitened frame is also the better one for the constrained step:
the trust region is spherical in y (an H0-aligned ellipsoid in theta), and scipy's projected CG, which has no
preconditioner of its own, then sees a well-conditioned reduced Hessian. A transform built at the start stays useful
when a face becomes active later: restricting a matrix to the tangent space of the active rows cannot raise its
condition number (Cauchy interlacing), and the barrier part lives in the slack block, which scipy scales separately.
What it does not whiten is the constraint-curvature term v d2c of a nonlinear face, and nothing is rebuilt mid-fit in
production (`--maxRestarts 0`). A rebuild needs a restart, and under trust-constr a restart resets the barrier to
mu0 = 0.1 and re-inits the slacks (`s0 = max(-1.5 c, 1)`), so a rebuild does not come for free here.

What does change meaning: scipy's `optimality` is the y-norm of the KKT residual, i.e. roughly per-sigma (the
EDM-like, invariant measure; with T = H0^-1/2 its 2-norm squared is r^T H0^-1 r). `minimizer_status` now says which
frame it is in (`optimality_frame`) and also reports `optimality_physical` = ||grad f + J^T v||_inf in fitter
units. Consequence seen in the tests: **the gtol exit can come at a different barrier parameter mu in y than in
theta** (scipy does not wait for mu at a gtol exit). The fit then sits ~mu/v inside each active face, with an NLL
excess ~mu per face. Seen: 6.4e-6 (end-to-end toy); for a saturated q this is negligible (< 1e-4).

### 2. Toy: same answer, cheaper when ill-conditioned

Full-scope spectral (`--precondition --preconditionParams '.*' --preconditionBlocks none --preconditionTransform
spectral`) vs none; trust-constr gtol = xtol = barrier_tol = 1e-10, maxiter 500; both rows binding.

| poly order | cond(H) at free min | plain: nit / HVPs / exit | preconditioned: nit / HVPs / exit | max abs dx / sigma | multipliers |
|---|---|---|---|---|---|
| 6  | 2.9e3 | 40 / 303 / gtol at mu = 3.2e-5 | 42 / 293 / gtol at mu = 2e-9 | 4e-6 | agree to 4e-6 rel. |
| 8  | 1.1e5 | 57 / 474 / gtol | 53 / 357 / gtol | 1.6e-9 | agree to 1e-9 rel. |
| 10 | 4.5e6 | 169 / 1336 / **xtol** (optimality 6.9e-8, not converged to gtol) | 96 / 594 / gtol | 4.4e-6 | agree to 4e-7 rel. |

The face-held covariance agrees to 3e-9 (order 8) whenever both runs flag the same active faces. In the order-6 and
order-10 rows the PLAIN run did not flag the weakly-binding ball face (multiplier 0.13, 0.0022): it stopped mu/v =
2.5e-4 and 3.3e-5 inside the face, more than the post-fit's `active_tol` = 1e-5. That is a pre-existing
trap (Open questions), not the transform. With a NON-convex row (poly3^2 + poly4 >= lb, order 8) the two frames went
into **different constrained local minima** (NLL 4.633 vs 5.326, both KKT points). A change of frame changes the
path, so on a multimodal problem (and the NP likelihood is multimodal: `np-wall-local-minima`) the loss of a
preconditioned fit must be compared, not assumed equal.

### 3. Expected payoff (prediction, unmeasured)

- **Saturated ptll sub-fit**: this is the target. It starts at the main-fit minimum, where the reference Hessian is
  representative. That was the regime in which full-scope spectral cut trust-krylov from 2150 to 614 HVPs (SATP,
  `constrained-fit-strategy/261008-saturated-subfit-diagnosis`). trust-constr's projected CG has a loose forcing term,
  so its ill-conditioning shows up as extra outer iterations, not as long CG solves. On the toy the gain grows with
  kappa (1.0x, 1.3x, 2.25x in HVPs at kappa 3e3, 1e5, 4.5e6). At kappa 1e9–1e10 I expect at least the
  trust-krylov factor (~3x). Fixed costs it does not touch: one dense Hessian (~5 min) and scipy's warm-start slack
  detour (`s0 = max(-1.5 c, 1)`, +333 NLL / hours in TCA), which is frame-independent. The plain trust-constr
  saturated sub-fit has never been timed; NOLAT/LAT will give the first baseline.
- **Main cold fit**: uncertain. The transform is built at the cold anchor and never rebuilt (`--maxRestarts 0`);
  V2 already converges in 104 it / 2.3 h. Worth testing only after the saturated test passes.

### 4. Proposed real-fit test (for Luca to approve; NOT run)

Test A, the saturated sub-fit only, from NOLAT's finished postfit (no main refit, so no main-fit trust-constr
detour). Run when NOLAT is done and a 260 GB slot is free, through mem_gate as in `../261015-cold-tc-fits/logs/launches.txt`.
Note: mem_gate runs `bash -c "$*"`, so pass `"'.*'"` there or the regex is globbed.

```
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261015_ct18z_nominal_fits
CARD=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5
CACHE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_y35_260921_y25
/home/submit/lavezzo/alphaS/WRemnantsHelpers/agent_setup.sh \
  --scetlib /work/submit/lavezzo/alphaS/scetlib-gamma-nu-points/scetlib-cms/build \
  --prepend-pythonpath /work/submit/lavezzo/rabbit-tc-precond -- \
python /work/submit/lavezzo/rabbit-tc-precond/bin/rabbit_fit.py $CARD --jitCompile off -o $OUT -t 0 \
  --postfix SATPC_NOLAT --externalPostfit $OUT/fitresults_NOLAT.hdf5 --noFit --saveHists \
  --precondition --preconditionParams '.*' --preconditionBlocks none --preconditionTransform spectral \
  -m Project ch0 ptll --computeSaturatedProjectionTests \
  --constraints wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDomainConstraints margin=0 \
  --minimizerMethod trust-constr --earlyStopping -1 --maxRestarts 0 --minimizerGtol 1e-8 \
  --minimizerXtol 1e-10 --minimizerBarrierTol 1e-9 --minimizerMaxiter 600 \
  --snapshotFile $OUT/snapshot_fitresults_SATPC_NOLAT.hdf5 --snapshotInterval 0.25 \
  --paramModel wremnants.postprocessing.scetlib_ad.SCETlibADParamModel \
  cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128 -v 4
```

(`--noHessian` cannot be used: it is refused next to an external covariance. The main postfit Hessian at NOLAT's
point is therefore recomputed once, about 5–15 min. No `--doImpacts` / `--globalImpacts`.)
Compare against NOLAT's own saturated sub-fit, which ran plain trust-constr from the same point
(`fitresults_NOLAT.hdf5` → `results/mappings/Project ch0 ptll/saturated_fit`: `nllvalreduced`, `minimizer_status`,
the `epoch`/`time` hists). For equal node load, a twin `SATPL_NOLAT` (same command without the four
`--precondition*` flags) run alongside is the clean timing reference. **Pass:** |dq| (q = saturated 2 dNLL) < 0.01
(expect ~1e-5 = barrier), the same `constraint_values`/active faces, the same (blinded) alpha_s in the saturated fit to <0.01 sigma (both runs are real data, so they share one blinding frame and offset),
`optimality_physical` small; **payoff:** wall time and nit vs the plain one.
Test B (only if A pays): a cold main fit = `fitterAD.sh --constraints` with the preconditioner kept (one-line change
in fitterAD.sh, which today drops `precond_arg` under `--constraints`), against NOLAT: dNLL within 2 mu, same faces
and multipliers, d alpha_s < 0.01 sigma, wall time vs NOLAT.

---

## Findings

1. trust-constr + `--precondition` is an implementation gap, closed by the chain rule: J_y = J T and constraint HVP
   T^T d2c T; values, bounds, multipliers, keep_feasible and the face-held post-fit are frame-independent —
   (evidence: rabbit `tc-precond` 2a64792, `tests/test_trust_constr.py::test_preconditioned_constraint_jacobian_and_hvp_follow_the_chain_rule`)
2. Same constrained minimum / multipliers / face-held cov with and without full-scope spectral preconditioning; HVP
   savings grow with kappa (1.3x at 1e5, 2.25x at 4.5e6; at 4.5e6 the plain fit did not even reach gtol) —
   (evidence: Result §2 table; `test_preconditioning_does_not_move_the_constrained_fit`, `test_saturated_test_is_unchanged_by_preconditioning`)
3. Under preconditioning scipy's gtol/xtol/trust radius are in the whitened frame; a gtol exit can come at a
   different barrier mu (NLL excess ~mu per active face, ~mu/v inside the face). Use `optimality_physical` /
   `optimality_frame` from `minimizer_status` — (evidence: ## Log, the failed first saturated test; generalizes:
   `knowledge/20_frameworks/rabbit_minimizer_tolerances.md` should get it)
4. A change of frame changes the minimizer's path: with a non-convex constraint set the two frames found
   different constrained local minima on the toy — compare losses, never assume — (evidence: ## Log, first toy)

---

## Open questions

- **Weak faces missed by the post-fit (pre-existing, both frames).** A gtol/xtol exit leaves a row ~mu/v inside its
  face; with a small multiplier that exceeds `active_tol` = 1e-5 and `constrained_postfit` does not hold the face
  (toy: v = 0.13 at mu = 3.2e-5; v = 0.0022 after an xtol exit). V2's weakly binding L2(|Y| = 2.5) face is the
  real-fit analogue: check NOLAT/LAT's `constraint_values` against the bounds and the multipliers.
- **Rows with zero gradient at the start are silently dropped (pre-existing bug).** `scipy_adapter` decides "depends
  only on frozen parameters" from `|J(x_start)|.sum(1) > 0`, so a row stationary at the start (e.g. a quadratic
  centred there) is treated as a constant and never enforced. The fix would be to use the frozen mask /
  `parameter_indices`, not the numeric Jacobian. Not touched here.
- **Warm-start slack detour of trust-constr** (`s0 = max(-1.5 c, 1)`) applies to the saturated sub-fit, which
  starts at the main minimum. It may dominate that sub-fit's cost under trust-constr whatever the frame. NOLAT/LAT's
  saturated step will show its size.
- Mid-fit preconditioner rebuilds: under trust-constr only via a restart, which resets mu and the slacks — probably
  not worth it; not explored.
