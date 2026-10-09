---
title: trust-constr from C (XWSTIFF config)
slug: 261006-tc-from-C
study: trust-constr-nominal
status: active        # active | done | paused | abandoned
created: 2026-10-06
updated: 2026-10-06
owner: study-worker
---

# trust-constr from C (XWSTIFF config)

**Task:** In the XWSTIFF configuration (card A, new cache, stiff wall, λ4_ν free, no lattice), started from C, where does trust-constr with hard constraints (λ4_ν ≥ 0 exact) converge — back to XWSTIFF, onto the λ4_ν = 0 face near XL4ZSTIFF, or elsewhere?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-10-06 12:30)

> **CLOSED by the orchestrator 2026-10-06 (Luca: conserve resources).** TCC1 is dropped, not relaunched. It was killed in the overload at +0.964 above XWSTIFF, feasible, optimality ~0.03, on the λ4_ν = 0 face (TMD route), i.e. as predicted, but uncertified. Snapshot on ceph.

> **TCC1 was OOM-killed at iteration 65; restarted from its it-63 snapshot as TCC1R (queued in mem_gate). No converged
> result yet.** Where it was going is already clear: onto the λ4_ν = 0 face on the TMD route, next to XL4ZSTIFF. At it 63
> λ4_ν = +1.5e-6, λ2_ν = +3.5e-5, Δ`alphaS` = +0.016σ_XW from XL4ZSTIFF, loss +0.9587 above XWSTIFF (XL4ZSTIFF +0.9549),
> μ = 4e-5. Real data, `alphaS` blinded: differences only.

| fit | what | live log | gate log | PID |
|---|---|---|---|---|
| TCC1 | trust-constr from C, μ₀ 1e-3 | [logs/TCC1.log](logs/TCC1.log) | [logs/TCC1.gate](logs/TCC1.gate) | **dead**: OOM-killed (exit 137) at it 65, 12:14–12:23 |
| TCC1R | restart from TCC1's it-63 snapshot (`seed_TCC1_it63.hdf5`), μ₀ 1e-4, TMD priors pinned | [logs/TCC1R.log](logs/TCC1R.log) | [logs/TCC1R.gate](logs/TCC1R.gate) | mem_gate 176329 (queued 12:27, 400 GB) |
| HESSTCC1R | data-only Hessian at TCC1R (`--noFit`, no `-r`, TMD priors pinned) | not launched (one cache load at a time) | | |

- **Owner:** this study-worker session (resumed by the orchestrator; the other instance stood down). One babysitter only.
- **How to check:** `bash scripts/trace.sh TCC1R` (it, loss, loss − XWSTIFF, optimality, constr_violation, μ, tr_radius);
  `scripts/incontainer_tc.sh python3 scripts/snapshot_state.py TCC1R` (λs, faces, Δ`alphaS`/σ from the latest snapshot);
  the end is the `[run] ... exit=` line in `logs/TCC1R.log`; PID of run_fit is in `logs/TCC1R.gate`.
- **Next action:** check TCC1R's "Gaussian priors on 46" line and its start loss (must be TCC1's it-63 loss, 372.2870331).
  When it exits 0: `bash scripts/launch.sh HESSTCC1R` (check "Gaussian priors on 46"), then
  `scripts/incontainer_tc.sh python3 scripts/compare.py TCC1R` → table in Result.
- **Blocking on:** node memory (mem_gate).

---

## Log

### 2026-10-06
- **Rabbit flags (step 1).** Commit `954aa4b` on branch `trust-constr-nominal` (worktree
  `/work/submit/lavezzo/rabbit-trustconstr`, not pushed): `--minimizerInitialBarrier`, `--minimizerInitialBarrierTol`,
  `--minimizerInitialTrRadius` → scipy `initial_barrier_parameter` / `initial_barrier_tolerance` / `initial_tr_radius`.
  Unset = not passed = scipy's defaults (0.1, 0.1, 1.0). New test `test_interior_point_start_options_reach_scipy` (spies
  on `scipy.optimize.minimize`: the three keys arrive when set and are absent when unset; with μ₀ = 1e-3 the toy still
  lands on the face). `tests/test_trust_constr.py`: 7/7 pass. CI's black / isort / flake8 selection clean in the container.
- **Infeasible start (step 2).** scipy (container, `_trustregion_constr/tr_interior_point.py`):
  - slack init `s0 = max(-1.5·c_ineq0, 1)`, with `c_ineq = lb − c(x)`. So s0 = max(1.5·(c − lb), 1): **1 for every
    constraint here** (all c − lb < 0.67), whatever the sign. The barrier subproblem's equality `c(x) − lb = s` is
    therefore violated by O(1) at ANY start, feasible or not; C's 1.85e-4 violation is negligible next to that.
  - No error path for infeasible x0. The only feasibility machinery is `keep_feasible` (objective = inf whenever a
    kept constraint is violated). rabbit sets `keep_feasible=False` when x0 is infeasible (warning logged), so the
    minimiser can walk in.
  - Toy (`scripts/toy_infeasible_start.py`, [logs/toy_infeasible_start.log](logs/toy_infeasible_start.log)): start 1e-3
    past a binding face; μ₀ = 0.1 → status 1, 60 it, on the face to 7e-14; μ₀ = 1e-3 → status 2, 56 it, 2e-12. No error.
  - **Decision: C used verbatim** (λ4_ν = −1.85e-4), no +1e-6 shift.
- **Wall arming (step 2).** `scripts/seed_feasibility.py` → [seed_feasibility.json](seed_feasibility.json). On XWSTIFF's
  card and names, `NPDampingWallTC` arms **6 of 8** conditions, `lambda4_nu >= 0 (CS large-b leading)` first; only the two
  held-λ conditions (λ_inf, λ_inf_ν > 0) are dropped. Values (c − lb, margin 0) in the order
  [λ4_ν, λ2_ν, L2(0), B(0), L2(2.5), B(2.5)]:

  | point | λ4_ν | λ2_ν | L2(0) | B(0) | L2(2.5) | B(2.5) |
  |---|---|---|---|---|---|---|
  | seed = C | **−1.85e-4** | +0.0073 | +0.078 | +0.356 | +0.022 | +0.356 |
  | XWSTIFF (W) | +0.0444 | **−1.1e-6** | +0.119 | +0.0015 | +0.060 | **−2.0e-7** |
  | CMR1B | **−1.64e-4** | **−2.3e-7** | +0.093 | +0.362 | +0.035 | +0.361 |
  | XL4ZSTIFF (λ4_ν held 0) | 0 (held) | **−7.4e-7** | +0.091 | +0.362 | +0.032 | +0.362 |

  CMR1B and XL4ZSTIFF are close in the TMD λs (λ2 0.093 vs 0.091, λ4 0.1204 vs 0.1205): CMR1B is the λ4_ν = 0 face
  minimum pushed 1.6e-4 past the face.
- **12:30 — OOM kill and restart.** The kernel OOM killer reaped TCC1 (python 3691371) at 12:14:49 together with
  another session's fit (3953947) (`dmesg`: "oom_reaper: reaped process 3691371"); run_fit reported exit=137 at 12:23:40.
  Last iterations: it 62 +0.9587 (feasible again after the it-52 overshoot, λ4_ν back to +1.5e-6), it 63 +0.9584,
  it 64 +0.9581, it 65 +0.9572 (optimality 0.06, μ 4e-5, tr_radius 0.096). The it-63 snapshot (loss 372.2870331 = it 62's
  accepted point) is copied to `seed_TCC1_it63.hdf5`; the 98 KB startup stub is renamed
  `fitresults_TCC1.startup_stub.hdf5` so nothing reads it as a result.
  Restart on the orchestrator's OK as **TCC1R**: TCC1's command with `--externalPostfit seed_TCC1_it63.hdf5`,
  `--minimizerInitialBarrier 1e-4` (TCC1 had reached 4e-5), and `prior_sigmas=lambda2=1,lambda4=1,delta_lambda2=1`
  (10:40 default change). Gate raised to 400 GB, one cache load of mine at a time (HESS waits for TCC1R).
  Expected cost: the restart re-initialises every slack at s0 = 1, so another interior-point excursion like TCC1's
  it 16–24 is likely before it settles again.
- **12:00, iteration 60 — overshoot through the λ4_ν face, then a trust-radius collapse.** The accepted step at it 52
  (taken with trust radius 17.9) put **λ4_ν = −8.1e-5** (constr_violation 8.1e-5; keep_feasible is off because the start
  was infeasible) and lowered the loss to +0.9589. Optimality jumped 0.01 → 0.65. Since then every step is rejected
  (it 53–60), the trust radius halving 17.9 → 5.6e-4. Snapshot it 57: λ2 0.0906, λ4 0.1211, δλ2 −0.0097, λ2_ν 3.5e-5;
  Δ`alphaS` +0.017σ_XW vs XL4ZSTIFF. The data pull is towards λ4_ν < 0 (the CMR1B notch); the quadratic model of the
  merit function fails there. With xtol = 1e-10 the collapse ends the barrier subproblem after ~22 more halvings.
- **11:40, iteration 54.** TCC1's process has **107 GB in swap** (VmSwap), pushed out by the other sessions' fits; iteration
  52 took 1087 s. Loss +0.9589 at it 52 (XL4ZSTIFF +0.9549); its 53–54 rejected. Not my processes, nothing killed.
- **11:20, snapshot it 52** (`snapshot_state.py`): λ2 0.0912, λ4 0.1196, δλ2 −0.0093 (XL4ZSTIFF: 0.0906 / 0.1205 / −0.0094);
  Δ`alphaS` = **+0.004σ_XW vs XL4ZSTIFF**, +0.263 vs XWSTIFF, −0.102 vs CMR1B. But λ4_ν = +3.0e-4 and λ2_ν = +3.9e-5 have
  hardly moved since it 34 (3.1e-4 / 4.0e-5) although μ fell 25×: the slacks are not μ-limited (expected μ/|v| ~ 1e-6),
  the interior-point steps toward the faces are just slow. Loss still 0.008 above XL4ZSTIFF.
- **11:10, iteration 50.** μ 2e-4 → 4e-5 at it 48; +0.9628 above XWSTIFF, optimality 1.0e-2, feasible. The node is now
  heavily loaded (load ~690, three other ~310 GB fits started by other sessions, 140 GB swap in use, 227 GB available), so
  iterations cost 330–490 s. HESSTCC1 (330 GB gate) will wait in mem_gate until memory frees up.
- **10:45 — WRemnants default changed under us (orchestrator notice).** At 10:40 `scetlib_ad/params.py` (uncommitted
  edit in the main checkout) put λ2, λ4, δλ2 into `FREE_PARAMS`, i.e. no TMD priors by default. TCC1 is unaffected (it
  imported the code at 09:12; its log reads `Gaussian priors on 46 parameter(s)`, λ2/λ4/δλ2 at σ = 1, the same as XWSTIFF).
  HESSTCC1 would import the new default, so `build_cmds.py` now inserts `prior_sigmas=lambda2=1,lambda4=1,delta_lambda2=1`
  after `threads=128` in the HESS command only (TCC1.cmd regenerated byte-identical). `run_fit.sh` now also records
  `params_diff_md5`. **Check at HESSTCC1 launch: its "Gaussian priors on N" line must read 46 with the same keys.**
- **10:20, iteration 41.** The first barrier subproblem converged at it 38 (optimality 0.089 < initial barrier tolerance
  0.1) and μ went 1e-3 → 2e-4, i.e. μ₀ = 1e-3 does what it was meant to (TCB1 never left μ = 0.1 in 600 iterations).
  Loss +0.9696 above XWSTIFF and still falling ~3e-3 per iteration.
- **Interim 09:50 (iteration 34, snapshot; NOT a minimum).** Trace ([trace_TCC1.png](trace_TCC1.png), `scripts/trace.sh`,
  `scripts/snapshot_state.py`):
  - it 1–12: 12 rejected steps (trust radius 1 → 2.4e-4). it 13–15: the loss fell to +0.426 above XWSTIFF (penalty-free)
    while still infeasible (constr_violation 2.2e-4, i.e. deeper into the λ4_ν < 0 notch).
  - it 16–23: the trust radius grew to 9.4 and the fit jumped out to +518 (it 22) — the same interior-point excursion TCA
    showed (scipy's slack init s0 = 1 makes every slack equation violated by O(1), and the merit function trades data NLL for
    it). From it 22 constr_violation = 0 (feasible).
  - it 24–34: back down, +24.9 → +1.005, optimality 7.7 → ~1, μ still 1e-3.
  - At it 34: λ4_ν = +3.1e-4, λ2_ν = +4.0e-5 (both just inside their faces), λ2 0.100, λ4 0.1216, δλ2 −0.0090 — the TMD
    route (XL4ZSTIFF: 0.091 / 0.1205 / −0.0094). Δ`alphaS` = +0.38σ_XW vs XWSTIFF, +0.12σ_XW vs XL4ZSTIFF, +0.01 vs CMR1B.
  - NB `fitresults_TCC1.hdf5` (98 KB, 09:15) already exists on ceph: a startup stub, not a result. Do not read it until the
    `[run] ... exit=0` line.
- **Start gate: PASS.** TCC1 logs `trust-constr start loss (no penalty) = 372.1648314225`, `start feasible=False`
  (1/6 violated, worst 1.851e-4 = λ4_ν), and `options={..., 'initial_barrier_parameter': 0.001}`. Expected: CMR1B's
  iteration-0 walled loss at the same seed, 372.4691929, minus the stiff penalty e^16·(1.850712e-4)² = 0.304362, gives
  372.164831. Same objective, penalty out. Iteration 0: optimality 6.1e3, constr_violation 1.85e-4, μ 1e-3, tr_radius 1.
- **Launch (step 3).** `scripts/build_cmds.py` → [cmds/TCC1.cmd](cmds/TCC1.cmd), [cmds/HESSTCC1.cmd](cmds/HESSTCC1.cmd)
  (token diff in [logs/build_cmds.log](logs/build_cmds.log)). Versus XWSTIFF's own command: worktree rabbit, `-o`,
  postfix, snapshot file, `--externalPostfit seed_1b_C_in_XWSTIFF.hdf5`, wall class → `npwall_tc.NPDampingWallTC`, and
  `--earlyStopping -1 --maxRestarts 0 --minimizerMethod trust-constr --minimizerGtol 1e-8 --minimizerXtol 1e-10
  --minimizerBarrierTol 1e-9 --minimizerInitialBarrier 1e-3 --minimizerMaxiter 600 --noHessian --noEDM`. Initial barrier
  tolerance and trust radius left at scipy's defaults (0.1, 1.0). Launched 09:12 through `mem_gate.sh` (330 GB; node had
  1377 GB available, no other fits). Outputs: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261006_tc_from_C/`.

---

## Result

<!-- The answer, and what it means physically. State comparability caveats BEFORE the
     numbers: blinding family, Asimov vs data, PDF/order swap, card or freeze-list
     difference, excluded points. Check the read against AN-25-085 / knowledge/, not
     against the code. A number without a physics read is not a finished task. -->

---

## Findings

<!-- One line each. A finding that generalizes beyond the parent study → tell the
     orchestrator; it belongs in ../../../knowledge/. -->

1. <finding> — (evidence: <path>)

---

## Open questions

- <what this task turned up but did not chase>
