---
title: trust-constr port + nominal fit
slug: 261005-trust-constr-port
study: trust-constr-nominal
status: active        # active | done | paused | abandoned
created: 2026-10-05
updated: 2026-10-05
owner: study-worker
---

# trust-constr port + nominal fit

**Task:** Is the nominal minimum NOMSTIFF (trust-krylov + stiff NPDampingWall, margin 0) robust to switching the minimiser to `trust-constr` with the physical NP region as hard inequality constraints (penalty off), warm from NOMSTIFF and from a start away from it?

---

## START HERE (status as of 2026-10-06 09:10, written by the orchestrator; the worker died on an auth error)

> **trust-constr with hard constraints reproduces NOMSTIFF.** TCA, warm from NOMSTIFF, converged (status 1, gtol;
> optimality 6.1e-9, no violation) at Δ`alphaS` = −2.2e-6 σ_NOM, ‖Δθ/σ‖ = 2.0e-5. The active face is the same
> (L2(|Y|=2.5) = 0, multiplier −16.3), and σ(`alphaS`) agrees to 2e-7 with the face held. TCB1 (cold) did NOT converge:
> it hit maxiter at +0.38, still in the first barrier stage (μ = 0.1). TCB2 was stopped. Blinded: differences only.

- **Next action:** none needed for Luca's question. Optional: expose `initial_barrier_parameter` as a rabbit flag and
  re-run the cold start (TCB1 spent all 600 iterations at μ = 0.1). Decide about pushing branch `trust-constr-nominal`.
- **Blocking on:** nothing. No fits running.

### Result (`scripts/compare.py TCA TCB1`, writes `compare.json`)

| | TCA (warm from NOMSTIFF) | TCB1 (census cold_000) | TCB2 (pert_000) |
|---|---|---|---|
| status | **1, converged** (gtol; optimality 6.1e-9) | 0, maxiter 600 (optimality 0.22) | stopped (SIGTERM) at iteration 117 |
| barrier μ at end | 1.0e-8 | **0.1** (never reduced) | 0.1 |
| NLL − NOMSTIFF (penalty-free) | **+1.49e-5** | +0.380 | +394 |
| Δ`alphaS` / σ_NOM | **−2.2e-6** | −0.33 (not a minimum) | — |
| ‖Δθ/σ_NOM‖ | 2.0e-5 | 0.92 | — |
| active faces | L2(\|Y\|=2.5) = 6e-10 (multiplier −16.27) | none: held 0.0067 inside by the barrier | — |
| constraint violation | 0 | 0 | 0 |
| iterations / wall time | 140 / 7.2 h | 600 / 13.6 h | 117 / 6.5 h |

σ(`alphaS`) at TCA from the data-only Hessian pass (HESSTCA), in units of σ_NOM: **face held 1.0000000, stiff spring
(NOMSTIFF's definition) 1.0000002, face released 1.0275**. ρ(`alphaS`, face) = −0.23. The data-only EDM is 1.11: the
distance to the unconstrained (unphysical) optimum, as expected at an active face.

**Physics read.**
- The nominal minimum does not depend on the minimiser: hard constraints and the τ = 8 penalty give the same point, the same
  face and the same σ.
- The +1.49e-5 is exactly 2 × NOMSTIFF's wall penalty (7.44e-6). That is the data cost of moving NOMSTIFF's 9.2e-7
  overshoot back onto the face.
- TCB1's −0.33σ is a barrier-held transient, not a second minimum. Its loss was still falling, with the face still 0.0067
  inside, when the fit hit maxiter.

(previous START HERE, 2026-10-05 14:55, superseded)
### old START HERE (status as of 2026-10-05 14:55)

> **The port is done and gated. Fit TCA (warm from NOMSTIFF) launched at 14:51 and is loading the cache. No
> trust-constr result yet.**
> The trust-constr path is on rabbit branch `trust-constr-nominal` (worktree `/work/submit/lavezzo/rabbit-trustconstr`,
> commits 2fa9a01 and 4df0074, not pushed). Gates (a) and (b, cheap half) pass, and so do the unit tests.
> - New finding: without an `xtol` the interior-point barrier stalls, so the fits pass `--minimizerXtol 1e-10
>   --minimizerBarrierTol 1e-9`.
> - Covariance preview from NOMSTIFF's own covariance: the stiff wall gives the same σ(`alphaS`) as holding the face
>   fixed. Releasing the face gives 1.027 σ_NOM.

- **Next action:**
  1. TCA's first `[minimize] trust-constr start loss (no penalty)` line must read **376.6146255**, the gate (b)
     objective. If it does and the iterations look sane, TCB1 and TCB2 are already queued (14:53, orchestrator's instruction).
  2. After each TC fit finishes, launch `bash scripts/launch.sh HESSTC<x>` (data-only Hessian).
  3. Then run `scripts/incontainer_tc.sh python3 scripts/compare.py TCA TCB1 TCB2`, which writes `compare.json`, and
     put its table in Result.
- **Blocking on:** nothing; TCA is running.
- The first TCA attempt died at 14:51:18 (exit 2) on a quoting bug in `run_fit.sh`; it is fixed, and that log is kept
  as `TCA.attempt1.log` on ceph.

| fit | start | live log | gate log | PID |
|---|---|---|---|---|
| TCA | NOMSTIFF (warm, via `seed_NOMSTIFF_nocov.hdf5`) | [logs/TCA.log](logs/TCA.log) | [logs/TCA.gate](logs/TCA.gate) | run_fit PID 2038567, launched 18:2x (attempt 3) |
| TCB1 | census cold_000 | [logs/TCB1.log](logs/TCB1.log) | [logs/TCB1.gate](logs/TCB1.gate) | run_fit PID 1699954, launched 14:58 |
| TCB2 | census pert_000 | [logs/TCB2.log](logs/TCB2.log) | [logs/TCB2.gate](logs/TCB2.gate) | **stopped by the orchestrator, with Luca's OK, at 21:37** (SIGTERM, exit 143; snapshot written). Not relaunched. |

Status: `bash scripts/status.sh` (all fits). Or `grep -E "minimize\]|Iteration|trust-constr: opt|Traceback|exit=" logs/TCA.log | tail`.
The per-iteration KKT state (optimality, constr_violation, barrier, tr_radius) is logged at debug level, and the final
status is in the `minimizer status:` line and in `results["minimizer_status"]`. Outputs go to
`/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261005_trust_constr_nominal/`.

---

## Log

### 2026-10-05 — port, gates, launch

**What already exists.** `main-plus-ours` already has the parts of the 2026-08 WIP (5bc7aad) that went upstream:
`arm_regularizers`, `set_expectations(parms=)` and `minimizer_status`. It is missing the `trust-constr` choice,
`Regularizer.constraint_spec`, `regularizers_as_constraints`, `_constraint_val_jac`, `_build_scipy_constraints`, and the
KKT fields of `minimizer_status`. The current WRemnants `NPDampingWall` (scetlib_ad, with `margin=`) has **no**
`constraint_spec`, but it exposes everything that method needs: the armed conditions `_active`, each with `.value` and
`.bound`, and `_physical`.

**What I ported.** Branch `trust-constr-nominal` off `main-plus-ours`, in worktree `/work/submit/lavezzo/rabbit-trustconstr`,
commit `2fa9a01`. I bypassed the hooks because rabbit's hook fails on pre-existing issues, and ran CI's black, isort and
flake8 selection by hand in the container instead (clean).
- `rabbit/parsing.py`: adds the `trust-constr` choice and two new trust-constr-only flags, `--minimizerXtol` and
  `--minimizerBarrierTol`.
- `rabbit/regularization/regularizer.py`: `constraint_spec()`, default `None`.
- `rabbit/fitter.py`:
  - `regularizers_as_constraints` is set **when the parameter layout is built, from the method**. The WIP set it inside
    `fit()`. But the loss is a traced `tf.function` that reads the flag at trace time, so any loss evaluation before
    `fit()` would have baked the penalty in (`knowledge/20_frameworks/rabbit_minimizer_tolerances.md`, "baked in at
    trace time").
  - `_constraint_val_jac`: frozen Jacobian columns are zeroed.
  - `_build_scipy_constraints`: constant rows are dropped (refused if violated), and `keep_feasible` is taken from the
    start point.
  - a log line with the start loss (penalty excluded).
  - `minimizer_status` gains optimality, constr_violation, barrier, tr_radius, the multipliers and the constraint
    values and bounds.
- **A bug the WIP code would have hit on this branch.** `fit()` iterates in *shifted* internal coordinates
  (`y = x − x_start`, from `Preconditioner.identity`) even with preconditioning off. The constraints must therefore be
  evaluated at `pc.to_physical(y)`. The unit test caught this: the constrained fit returned its start unchanged. Fixed,
  and trust-constr now refuses `--precondition`.
- `rabbit/callbacks.py`: keeps the trust-constr KKT state of the last accepted iterate, because scipy discards its
  result when the callback raises.
- `tests/test_trust_constr.py`, 6 tests:
  - the penalty is absent from the constrained loss;
  - an inactive constraint reproduces the free fit;
  - a binding constraint lands on the conditional minimum on the face (x to 1e-4, loss to 1e-7, multiplier nonzero);
  - a frozen parameter is not moved, and its Jacobian column is zero;
  - a constraint on frozen parameters only is dropped, or refused when violated;
  - a penalty-only regularizer is refused.

  All 6 pass, as do `test_restart.py` and `test_sparse_fit.py` (34 tests in total).
- WRemnants side: a task-local shim, so the main checkout stays untouched. [scripts/npwall_tc.py](scripts/npwall_tc.py)
  defines `NPDampingWallTC(NPDampingWall)`. Its `constraint_spec` returns (`c.value(physical λ)`, `c.bound`) for each
  **armed** condition. The proposed permanent change is the same method on `NPDampingWall`.

**Finding: trust-constr needs an `xtol`, or its barrier stalls.** rabbit passes `tol=0.0`, so `xtol=0`. A barrier
subproblem then ends only when its optimality drops below the (decaying) barrier tolerance, or when the trust radius
drops below `xtol`. If the trust radius collapses first:
- the barrier parameter μ stops decreasing;
- the fit stays about μ above the constrained minimum;
- it sits about μ/multiplier inside the active face.

The toy, with a binding constraint:

| setting | iterations | barrier μ | result |
|---|---|---|---|
| no `xtol` | 500 | stuck at 1.3e-6 (trust radius 1e-153) | loss 1.3e-6 above the true constrained minimum; status 0 (maxiter) |
| `xtol = barrier_tol = 1e-10` | 69 | 8e-11 | status 1 (gtol) |

This may also be why the 2026-08 trust-constr fits "dribbled".

**Gate (a): frozen parameters.** NOMSTIFF's freezes go through `fit_params`:
- rabbit's vector has 3719 entries, and the only λs in it are `lambda2, lambda4, delta_lambda2, lambda2_nu`;
- `lambda4_nu`, `lambda_inf` and `lambda_inf_nu` are not in it at all, and no `--freezeParameters` is used, so
  `frozen_indices` is empty;
- at NOMSTIFF, the constraint Jacobian has non-zero columns **only** for those four λs;
- the three conditions on held λs (λ_inf_ν > 0, λ4_ν ≥ 0, λ_inf > 0) are satisfied, and the wall itself drops them.

That leaves 5 constraints. Evidence: [gate_b_constraints.json](gate_b_constraints.json),
[scripts/gate_b_constraints.py](scripts/gate_b_constraints.py).

**Gate (b): constraint values (the half that needs no cache).** At NOMSTIFF's x, three evaluations of the five
constraint values agree exactly (max |diff| = 0): `constraint_spec`, the wall's own numpy evaluator, and
`Fitter._constraint_val_jac`.

| condition (margin 0, lower bound 0) | value at NOMSTIFF |
|---|---|
| λ2_ν ≥ 0 | 0.0643 |
| L2(\|Y\|=0) = λ2 ≥ 0 | 0.0256 |
| 3λ_inf²λ4 + L2³ ≥ 0 at \|Y\|=0 | 0.2628 |
| **L2(\|Y\|=2.5) = λ2 + 6.25 δλ2 ≥ 0** | **−9.15e-7** (active, slightly past the face) |
| 3λ_inf²λ4 + L2³ ≥ 0 at \|Y\|=2.5 | 0.2627 |

- NOMSTIFF's stiff penalty there is 7.44e-6. Its NLL without the penalty is therefore 376.6146329 − 0.0000074 =
  **376.6146255**. Fit A logs the trust-constr start loss (penalty excluded) at NOMSTIFF's x, and it must equal this
  number.
- NOMSTIFF sits 9.2e-7 *past* the face. There the relu² spring force, 2e¹⁶ × 9.15e-7 ≈ 16.3, balances the data. So the
  expected multiplier of the active constraint is about 16 NLL units per unit of L2.
- All 10 census seeds are strictly feasible, with minimum slack 0.027–0.21
  ([scripts/seed_feasibility.py](scripts/seed_feasibility.py)).

**Covariance decision.** A stiff-penalty Hessian taken with `--noFit` at the trust-constr point is NOT NOMSTIFF's σ
definition. The trust-constr point sits ON the face, where the relu² spring is not engaged (its second derivative is
zero for value ≥ bound), so that pass would just return the data-only Hessian. The plan instead:
1. One data-only Hessian pass per result: `HESS<pf>`, with `--noFit` and no `-r`.
2. Offline, three covariances via Sherman–Morrison, with a the gradient of the active constraint:
   - σ_free: the data-only Hessian;
   - σ_stiff = (H + 2e¹⁶ a aᵀ)⁻¹: NOMSTIFF's definition, with the spring engaged;
   - σ_proj: the k → ∞ limit, i.e. the face held fixed (the reduced Hessian ZᵀHZ).

A cheap preview from NOMSTIFF's own stored covariance, [scripts/compare.py](scripts/compare.py). Its Hessian is the data
Hessian plus K a aᵀ, with K = 2e¹⁶ (the spring is engaged, because NOMSTIFF sits past the face). Removing the spring
("un-springing") and taking the hard projection gives, in units of σ_NOM(`alphaS`):

| covariance at NOMSTIFF | σ(`alphaS`) / σ_NOM |
|---|---|
| stored (stiff spring) | 1 |
| projected (face held) | 1.0000 (to 2e-7) |
| free (spring removed, data only) | **1.027** |

So the stiff penalty is numerically the hard projection, and releasing the active face widens σ(`alphaS`) by only
2.7 %. In the language of the 2026-08 study, the asymmetric constrained interval is bracketed by [1.000, 1.027] σ_NOM.
The 2026-08 old-card fit had 0.52 → 0.81; here the face is almost uncorrelated with `alphaS`.

The trust-constr fits themselves run `--noHessian --noEDM`. An EDM is meaningless at an active face, and a failed
Cholesky must not cost the fit.

**Fit settings.** Built by [scripts/build_cmds.py](scripts/build_cmds.py) from NOMSTIFF's own meta_info command; the
token diffs are in [cmds/](cmds/).
- `-r npwall_tc.NPDampingWallTC ...NPDampingMapping margin=0`.
- `--minimizerMethod trust-constr --minimizerGtol 1e-8 --minimizerXtol 1e-10 --minimizerBarrierTol 1e-9`.
- `--minimizerMaxiter 300` for A, 600 for B.
- `--earlyStopping -1 --maxRestarts 0`. A restart would reset the barrier parameter to 0.1 and push the point off the
  face.
- Snapshots every 0.25 h; `--noHessian --noEDM`.
- Everything else is NOMSTIFF's.

**TCA attempts 1 and 2 failed.**
- Attempt 1 died at startup on a quoting bug in `run_fit.sh`; the inner command now goes through a file.
- Attempt 2 (14:55) died in `load_fitresult`: NOMSTIFF's fitresult carries a covariance, and with `--noHessian`
  rabbit refuses to load an external covariance.
- Fix: [scripts/make_nomstiff_seed.py](scripts/make_nomstiff_seed.py) writes NOMSTIFF's x as a flat seed with no
  covariance (x + parms). The fitresult's parms values *are* the raw `Fitter.x` vector, so the seed is the identical
  point. TCA was requeued at 15:23.
- The crash stub is kept as `fitresults_TCA.attempt2_crashstub.hdf5`.

**TCB1 / TCB2 start.** Their start losses, 10492.7088 and 6940.5872, equal the census trust-krylov starts from the same
seeds (CENS09 10492.7088, CENS01 6940.5872). That confirms the loss definition is unchanged apart from the penalty: the
penalty is zero at these strictly feasible seeds. Iterations cost about 300 s, against about 140 s for trust-krylov.

Launched TCA at 14:19 through `mem_gate.sh` ([scripts/launch.sh](scripts/launch.sh) → [scripts/run_fit.sh](scripts/run_fit.sh),
with the worktree and `scripts/` prepended to PYTHONPATH; the log records which `rabbit` was imported).

---

## Log addendum 2026-10-05 16:55
- TCB1 is at iteration 18 (loss 400.14; NOMSTIFF without penalty is 376.61), with barrier μ still 0.1 and optimality
  about 11.
- TCB2 is at iteration 23 (loss 847.3; optimality about 15).
- Iterations cost 230–500 s, versus about 140 s for trust-krylov. At this pace the 600-iteration cap is tens of hours.
- TCA has been in the memory gate since 15:23. 135 GB is available and it needs 480. The other workers' fits plus
  TCB1/TCB2 hold the node.

## Log addendum 2026-10-05 18:30 — gate (b) objective half: PASS
- **TCA start loss, penalty excluded, at NOMSTIFF's x = 376.6146254794.** Expected NOMSTIFF nllvalreduced − stiff
  penalty = 376.61462547941585: the two agree to every printed digit. The penalty is genuinely out of the loss, and the
  objective is otherwise NOMSTIFF's.
- TCA iteration 0 reports constr_violation 9.153e-7. That is exactly NOMSTIFF's overshoot past the L2(|Y|=2.5) face,
  so the scipy-side constraint evaluation is consistent too.
- TCB1 at iteration 33: loss 379.028 (+2.4 above NOMSTIFF), barrier μ still 0.1, optimality 2.3.
- TCB2 at iteration 48: loss 821.6 (+445), optimality 9.5, and still descending slowly (about 1 unit per iteration).

## Log addendum 2026-10-05 21:40
- **TCB2 was stopped by the orchestrator, with Luca's OK, at 21:37.** After 117 iterations (6.5 h) its loss was
  770.40, i.e. +394 above NOMSTIFF. μ was still 0.1 and optimality 17.8, and the descent was about 0.7 per iteration
  (loss 852 → 830 → 812 → 797 → 782 at iterations 19/39/59/79/99), so it could not converge within the cap. No HESS
  pass. Its last state is in `snapshot_fitresults_TCB2.hdf5`.
- **TCA (warm) left NOMSTIFF and came back, as the interior-point start predicts.** scipy initialises every slack at
  s0 = max(−1.5·c, 1) = 1, whatever the start. The first steps therefore push the λs into the interior: the loss went
  376.61 → **709.2 at iteration 3**. After that it returned (420.5 at 6, 385.8 at 12, 376.64 at 24) while μ decays.
  At iteration 47 (3.1 h): loss 376.63580 (+0.021 above the start), μ = 4e-3, optimality 0.012, constr_violation 0.
  The leftover +0.021 is the barrier term's footprint. It should fall to about 1e-5 as μ → 1e-9.
- **TCB1** at iteration 95 (6.6 h): loss 378.3297 (+1.7). μ is **still 0.1** and optimality 1.65. Its first barrier
  subproblem has not converged yet.

## Result

Pending.

---

## Findings

1. With rabbit's `tol=0.0`, trust-constr's barrier parameter stalls as soon as the trust radius collapses before a
   barrier subproblem converges. The fit then sits about μ above the constrained minimum. Pass
   `--minimizerXtol` (1e-10). Toy: 500 iterations stuck vs status 1 in 69. (evidence: the Log above; `tests/test_trust_constr.py`)
2. rabbit's `fit()` iterates in shifted coordinates even with preconditioning off, so any extra callable handed to
   scipy (constraints) must map through `pc.to_physical`. (evidence: the Log above)
3. `--noHessian` combined with `--externalPostfit <a fitresult that has a cov>` crashes in `load_fitresult`. To
   warm-start a `--noHessian` fit, pass a flat x+parms seed. (evidence: `TCA.attempt2.log` on ceph)
4. With our `fit_params` freezes, the frozen-parameter / constraint-Jacobian bug cannot occur: the frozen λs are not in
   rabbit's vector. (evidence: [gate_b_constraints.json](gate_b_constraints.json))

---

## Open questions

- Proposed commits (not made): (1) rabbit `trust-constr-nominal` 2fa9a01 as a PR; (2) `constraint_spec` on WRemnants
  `NPDampingWall` (body of `scripts/npwall_tc.py`).
