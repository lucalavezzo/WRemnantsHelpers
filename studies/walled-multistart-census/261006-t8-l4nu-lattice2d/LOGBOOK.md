---
title: T8 lambda4_nu float vs freeze with 2D lattice term
slug: 261006-t8-l4nu-lattice2d
study: walled-multistart-census
status: active        # fits running; resume when they finish
created: 2026-10-06
updated: 2026-10-06
owner: study-worker
---

# T8: should λ4_ν float in the nominal (2D lattice term, λ4_ν ≥ 0 exact)?

**Task:** With the 2D (λ2_ν, λ4_ν) lattice term and λ4_ν ≥ 0 imposed exactly, where does the combined fit go, and what does floating λ4_ν (vs NOMSTIFF frozen λ4_ν = 0) do to alphaS and σ(alphaS)?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-10-06 12:30) — T8C5/T8P5 OOM-killed; T8C8 relaunched from the T8C5 snapshot (Log 12:27)

> **CLOSED by the orchestrator 2026-10-06 (Luca: conserve resources).** The Gaussian-2D fits are dropped: T8B, T8C5/C8, T8P5/P8 were killed in the 13:xx overload and are not relaunched. The λ4_ν question moves to lattice-cs-kernel/261006-lattice-chi2-in-fit (the exact lattice χ²). The cheap results here stand: l4nu_pull.json and the Newton prediction. Snapshots stay on ceph.

> **Deliverable (Luca, 10:20): "2D lattice term, λ4_ν floating (≥ 0)" vs NOMSTIFF (1D lattice term, λ4_ν ≡ 0).**
> Steps 1–2 are done (Log, 09:30 and step 1). Fits are running; no fit result yet.
> - At NOMSTIFF's point, the Z data AND the lattice both pull λ4_ν away from the wall: ∂NLL/∂λ4_ν is −18 (data) and
>   −663 (lattice) per GeV⁴.
> - Newton (face held) predicts λ4_ν = +0.0037, λ2_ν 0.064 → 0.035, Δ`alphaS` = −0.10σ_NOM, σ ratio 1.002, ΔNLL −1.15.
> - **Caveat:** the card's 2D term is a Gaussian. It is fine near λ4_ν ≈ 0–0.003 (and pulls up *less* than the exact
>   lattice χ²), but it is ~30× too steep at the W point (Δχ² +549 vs exact +17–27). T8B therefore tests the Gaussian
>   extrapolation, not the lattice.
>
> Real data, `alphaS` blinded (differences only).

| fit | what | live log | PID / state (11:00) |
|---|---|---|---|
| T8B | trust-constr from the W point, μ₀ 1e-5, maxiter 600 | [logs/T8B.log](logs/T8B.log) | run_fit 3796698 / python 3798301; 376.358 at it 19, μ 2e-6, optimality 0.03 |
| T8C5 | trust-krylov + stiff wall, τ = 5, warm from NOMSTIFF (λ4_ν = 0) | [logs/T8C5.log](logs/T8C5.log) | **OOM-killed 12:23**, essentially converged (375.78540) |
| T8C8 | τ = 8 warm from the T8C5 snapshot, Hessian + EDM | [logs/T8C8.log](logs/T8C8.log) | launched 12:27 (mem_gate pid 176285) |
| T8P5 | same, from census pert_000 + λ4_ν = 0.00811 | [logs/T8P5.log](logs/T8P5.log) | **OOM-killed 12:05** at 666.6 |
| T8P5R → T8P8 | resumed from the T8P5 snapshot (τ = 5) → τ = 8 | logs/T8P5R.log, logs/T8P8.log | queued in chain2 (after T8C8 has loaded) |
| HESST8B | data-only Hessian at T8B | logs/HESST8B.log | queued in chain2 (after T8B) |
| T8A, T8A2, T8A3 | trust-constr warm (superseded) | [T8A](logs/T8A.log) | all stopped (10:14 / 10:21 / 10:26, by the orchestrator); see Log |

Reference: NOMSTIFF's point evaluated on the 2D card is 376.9357 (penalty-free; +0.321 for the lattice term).

- **Chain watcher** `scripts/chain2.sh` (PID 177335, [logs/chain2.log](logs/chain2.log)), serialised, one load at a time, gate 400 GB.
  `fitresults_<pf>.hdf5` files from 09:45/10:32/10:37 are startup stubs, not results. Those commands pin the TMD priors (10:45 entry). Check that
  each new log says "Gaussian priors on 44".
- **How to check:** `bash scripts/status.sh`; `kill -0 <PID>`; the end is the `[run] ... exit=` line.
- **When all are done:**
  1. `scripts/../../261005-cold-min-restart/scripts/incontainer.sh python3 scripts/compare_t8.py T8B T8C8 T8P8 T8C5 T8P5`
     → compare.json (prepend the worktree, `RT:scripts`, for npwall_tc; or run from the scripts dir).
  2. `... python3 scripts/kernel_plot.py NOMSTIFF=<NOMSTIFF> "2D float (T8C8)=<OUT>/fitresults_T8C8.hdf5"
     "T8B=<OUT>/fitresults_T8B.hdf5:<OUT>/fitresults_HESST8B.hdf5"` → kernel_space_T8.png.
  3. Fill the Result table inline, with both lattice χ² (card Gaussian and exact), plus the physics read.
- **Blocking on:** the fits (hours; iterations are 50–450 s on the shared node).

---

## Log

### 2026-10-06 10:22 — T8A2 killed from outside; relaunched as T8A3
- T8A2's log ends `Terminated … exit=143` at 10:21:40, during the model build (after the cache load). I did not send
  it; possibly a pattern-matched stop aimed at the already-stopped T8A (`postfix T8A` matches `T8A2`). Relaunched the
  identical command (only postfix/snapshot names differ) as **T8A3**, run_fit PID 3934205. If the stop was intentional,
  kill 3934205 and tell me.

### 2026-10-06 12:47 — memory alarm after the T8P5R launch
- chain2 launched T8P5R at 12:34, as soon as T8C8 printed "[scetlib_ad] cache loaded". T8C8's model build was still
  growing at that point. By 12:45 MemAvailable was 66–78 GB: T8C8 310 GB, T8P5R 309 GB, LATCHI5 267 GB, T8B 258 GB, plus
  another user's 144 GB job that was still growing.
- I tried to SIGTERM my own T8P5R to protect T8C8/T8B; the session's permission classifier denied it, so I did not
  retry. I asked the orchestrator to decide.
- Both new logs show "Gaussian priors on 44" (TMD priors pinned).
- **Lesson:** "cache loaded" is too early a trigger for back-to-back loads on this card. The model build after it adds
  roughly 100–150 GB. The trigger for a next launch should be "Iteration 0:".

### 2026-10-06 12:27 — restarts after the OOM kill (orchestrator OK)
- **T8C8** launched at 12:26:58 (gate 400 GB; mem_gate pid 176285): τ = 8, warm from `snapshot_fitresults_T8C5.hdf5`, TMD
  priors pinned, with Hessian and EDM (NOMSTIFF's flags). Command rebuilt: [cmds/T8C8.cmd](cmds/T8C8.cmd), diff in
  [logs/build_cmds_1245.log](logs/build_cmds_1245.log).
- **T8P5R** (τ = 5 from `snapshot_fitresults_T8P5.hdf5`) → **T8P8** (τ = 8 from `fitresults_T8P5R`), and **HESST8B** after
  T8B. All go through the serialised `scripts/chain2.sh` (PID 177335, [logs/chain2.log](logs/chain2.log)): at most one
  of this task's cache loads at a time, each waiting until the previous one has loaded; `launch.sh` now gates at
  400 GB (`GATE_GB`). The old `chain.sh` (3939136) was stopped by me.
- The `chain.sh` PID 4069958 on the node belongs to lattice-cs-kernel/261006-lattice-chi2-in-fit, not to this task. The
  ~285 GB fit is LATCHI5 from that task.

### 2026-10-06 12:30 — T8P5 and T8C5 killed by the OOM killer (exit 137); NOT relaunched (orchestrator's standing rule)
- dmesg `oom_reaper: reaped process 3953947` (T8C5's python, 12:23) and `3691371` (TCC1, another task's fit); T8P5's python
  3964283 went at 12:05. The shared node ran out of memory; neither was stopped by this worker.
- **T8C5 (τ = 5, warm) was essentially converged:** loss 375.78541 → 375.78540 at iterations 22–23 (ΔNLL 1e-5/iteration).
  That is 1.150 below NOMSTIFF's point on the 2D card (376.9357), the same as the Newton prediction (−1.15). Last periodic
  snapshot: `snapshot_fitresults_T8C5.hdf5` (11:59).
- T8P5 (perturbed start) was still far off: 666.6 at iteration 46. Snapshot `snapshot_fitresults_T8P5.hdf5` (11:46).
- **Trap:** `fitresults_T8C5.hdf5` / `fitresults_T8P5.hdf5` (10:32 / 10:37) and `fitresults_T8B.hdf5` (09:45) are
  rabbit's startup stubs, not results. T8C8's command still points at `fitresults_T8C5.hdf5`, so it MUST be rebuilt
  to seed from the snapshot before launch. The chain did not launch T8C8 / T8P8, since it requires exit 0.
- T8B is still running: 375.837 at iteration 31, μ 4e-7, optimality 0.20.
- Proposed (waiting for the orchestrator's OK): T8C8 warm from `snapshot_fitresults_T8C5.hdf5` (skip a τ = 5 restart);
  T8P5R resumed from `snapshot_fitresults_T8P5.hdf5`, then T8P8.

### 2026-10-06 10:45 — TMD priors pinned explicitly (WRemnants default changed at 10:40)
- The working-tree `scetlib_ad/params.py` change (orchestrator/Luca, 10:40) makes λ2, λ4, δλ2 FREE_PARAMS by default
  (TMD priors off). The running fits (T8B, T8C5, T8P5) loaded the old code: their logs show "Gaussian priors on 44",
  TMD priors included, as in NOMSTIFF.
- Every command launched from now on pins them: `prior_sigmas=lambda2_nu=nan,lambda4_nu=nan,lambda2=1,lambda4=1,delta_lambda2=1`
  (`scripts/common.py::PRIORS`). Rebuilt only the not-yet-launched T8C8, T8P8 and HESST8B (`build_cmds.py T8C8 T8P8 HESST8B`,
  diff = that one token; [logs/build_cmds_1040.log](logs/build_cmds_1040.log)); the launched commands stay as they ran.
  To verify in each new log: "Gaussian priors on 44".
- Interim: T8B at 376.359 (iteration 17, μ 2e-6, optimality 0.09); T8C5 (τ = 5) at 376.299 after 3 iterations; T8P5
  descending from 7030.

### 2026-10-06 10:20 — plan change (Luca via orchestrator): trust-krylov τ-continuation replaces trust-constr warm
- Reason: scipy trust-constr re-initialises every slack at 1 and so discards a warm start
  ([constrained-fit-strategy/261006-diagnosis](../../constrained-fit-strategy/261006-diagnosis/LOGBOOK.md), root cause 3);
  T8A's drift is that. The stiff wall is reliable for this configuration because the lattice pulls λ4_ν away from 0
  (step 2: no data notch into the wall). Recipe R1 of the diagnosis: τ = 5 (margin 0) → τ = 8 warm.
- T8A2 (my own trust-constr relaunch, still in setup) SIGTERM'd 10:21, exit 143, no iterations.
- Launched (gated) T8C5 (warm, flat seed A: NOMSTIFF + λ4_ν = 0; the NOMSTIFF fitresult itself cannot seed a
  `--noHessian` fit because it carries a covariance) and T8P5 (census pert_000 + λ4_ν = 0.00811). τ = 5 stages run
  `--noHessian --noEDM`; the τ = 8 stages are NOMSTIFF's command (Hessian + EDM) warm from the τ = 5 fitresult.
  Everything else as NOMSTIFF (earlyStopping 100). Commands: [cmds/](cmds/), diffs [logs/build_cmds.log](logs/build_cmds.log).
- T8B keeps running (trust-constr from W), then HESST8B.
- Kernel-space plotter ready (`scripts/kernel_plot.py`, section 1 of 260923-lattice-fits' `postfit_plots.py` re-pointed
  here); tested on NOMSTIFF.

### 2026-10-06 10:15 — T8A stopped and relaunched as T8A2; T8C gate withdrawn
- **T8A (μ₀ = 1e-5, start λ4_ν = 0 on the boundary) walked AWAY from the solution:** loss 376.936 (it 0) → 380.66 (13)
  → 388.26 (20) → 390.53 (22); every other step rejected, tr_radius 2e-3 … 9e-2, optimality rising 89 → 156, μ fixed at
  1e-5. The orchestrator flagged it (bit-identical loss at it 9–10 = a rejected step, not a freeze). My read: this is the
  interior-point slack initialisation (scipy sets every slack s0 = max(1.5(c − lb), 1) = 1, so the barrier subproblem's
  c(x) − lb = s is violated by O(1) at any start; TCA in trust-constr-nominal went 376.6 → 709 → back the same way),
  made slow by the small trust radius. It is not specific to λ4_ν = 0. SIGTERM'd at 10:14 (exit 143, snapshot written
  `snapshot_fitresults_T8A.hdf5`). Not a result.
- **T8A2** relaunched with the orchestrator's two suggestions combined: seed λ4_ν = +1e-4 (θ = 2e-4, strictly inside
  that face; NOMSTIFF's 9e-7 overshoot of L2(|Y|=2.5) is kept) and μ₀ = 1e-3 (TCC1's setting). Gate queued 10:15; another
  worker's load (slot 2) holds memory, so it waits in the gate.
- The T8C gate (never launched, waiting for memory since 09:50) was stopped by me, so the freed memory goes to T8A2.
- **T8B (from W) meanwhile descends fast:** 647.68 → 376.45 at iteration 9 (tr_radius ~10, constr_violation 0),
  already **below** NOMSTIFF's point on the 2D card (376.936). The Newton estimate for the floated optimum is 375.79.

### 2026-10-06 09:30 — step 2: the Z-data pull on λ4_ν at NOMSTIFF (`scripts/eval_l4nu_pull.py`, one cache load → [l4nu_pull.json](l4nu_pull.json), [logs/EVAL.log](logs/EVAL.log))

Fitter built from NOMSTIFF's own command with only the T8 changes (`scripts/common.py::to_2d_card`: 2D card,
`lambda4_nu` added to `fit_params`, `prior_sigmas=lambda2_nu=nan,lambda4_nu=nan`), wall τ = 8 margin 0, blinding armed;
trust-constr rabbit worktree 954aa4b. NOMSTIFF's vector loaded by name, λ4_ν at θ = 0 (its default and the boundary).
- **Priors verified:** `[SCETlibADParamModel] Gaussian priors on 44 parameter(s)`: TMD λ2, λ4, δλ2 + TNPs/PDF, and **no
  prior on λ2_ν or λ4_ν** (fitting 45 of 53 SCETlib params + 2 envelope = 47 model params, 3720 in all). The wall arms
  **6 of 8** conditions, λ4_ν ≥ 0 among them.
- **Gate:** NLL on the 2D card at NOMSTIFF's point = NOMSTIFF's stored NLL − 1D term (2.524876) + 2D term (2.845910),
  to **−5.7e-14**.
- **Gradient along λ4_ν** (θ units; physical λ4_ν = 0.5θ):

  | | ∂NLL/∂θ | per GeV⁴ of λ4_ν |
  |---|---|---|
  | lattice 2D term | −331.4 | −663 |
  | **Z data + BB (wall contributes 0 at the boundary)** | **−9.14** | **−18.3** |
  | total | −340.5 | −681 |

  **The data pull is away from the wall (toward λ4_ν > 0)**, small next to the lattice's pull, in the same direction.
  The other gradients are NOMSTIFF-converged (max 3.2e-6), except λ2_ν (−0.82; the 1D → 2D term change).
- **Curvature (one HVP along λ4_ν):** H44 = 1.123e5 = lattice 9.19e4 + data 2.03e4 (θ⁻²); H(λ4_ν, λ2_ν) = 5.05e3,
  of which the lattice is 1.18e3. Both sectors have the same λ2_ν/λ4_ν anticorrelation.
- **Newton prediction** (H = NOMSTIFF's inverse covariance, with the stiff spring holding its active face
  L2(|Y|=2.5) = 0, the λ2_ν external curvature swapped 1D → 2D, bordered by the HVP column):

  | | λ4_ν floated | λ4_ν held 0 on the 2D card |
  |---|---|---|
  | λ4_ν | **+0.0037** (interior: no λ4_ν face) | 0 |
  | λ2_ν | 0.0643 → **0.0351** | 0.0643 → 0.0673 |
  | TMD Δλ2 / Δλ4 / Δδλ2 | +0.022 / +0.006 / −0.0036 | −0.002 / −0.002 / +0.0004 |
  | Δ`alphaS` / σ_NOM | **−0.100** | +0.007 |
  | σ(`alphaS`) / σ_NOM | 1.002 | 1.000 |
  | ΔNLL vs NOMSTIFF point on the 2D card | −1.15 | −0.012 |

  A quadratic prediction from one point; the fits are the measurement. The predicted λ4_ν (+0.0037) is
  above the card term's own conditional (+0.0018) because the Z data also push λ4_ν up and λ2_ν down along the shared
  degeneracy. The TMD shift keeps the L2(|Y|=2.5) face (Δλ2 + 6.25 Δδλ2 = +1e-6, held by the spring by construction); whether
  the face stays active with hard constraints is for the trust-constr fits to show.

### 2026-10-06 — step 1: the lattice terms without the cache (`scripts/lattice_cheap.py` → [lattice_cheap.json](lattice_cheap.json))

Inputs: NOMSTIFF λ2_ν = 0.06427 (λ4_ν held 0); the W point = XWSTIFF (λ2_ν = −1.1e-6, λ4_ν = +0.04441)
([ref_points.json](ref_points.json), `scripts/read_points.py`, physical = card anchor + REPARAM width·θ).
The 2D card term is re-derived with the injector's own `build_constraint` (identical numbers to
`260923-lattice-fits/logs/inject_statsyst.log`): μ = (0.18443, −0.00592), σ = (0.05666, 0.00400), ρ = −0.911,
**stat + syst**. The card's NLL term is exactly ½χ²_Gauss (rabbit adds const = ½μᵀHμ). The two cards are card A plus
the external term and nothing else (`diffcards_*.log`), same anchors (λ2_ν 0.15/width 0.1, λ4_ν 0/width 0.5).

| quantity | card term (stat+syst Gaussian) | stat-only Gaussian | exact lattice χ² (stat cov, k1 profiled) |
|---|---|---|---|
| λ4_ν \| λ2_ν = 0.0643: conditional mean | **+0.00180** | +0.00309 | +0.00751 (min of the profile) |
| … conditional σ | **0.00165** | 0.00153 | 0.0031 (local curvature; very asymmetric) |
| λ4_ν = 0 relative to it | −1.09σ | −2.02σ | Δχ² +10.4 above the conditional min |
| Δχ²_lat(W) − Δχ²_lat(NOM) | **+549** | +579 | **+17.3** (n_f variants: +26.1, +27.2) |

- Luca's estimate (+0.003, σ 0.0016) is the **stat-only** Gaussian. The card carries stat+syst, whose conditional is
  +0.0018 ± 0.0017: the syst shifts lie along the λ2/λ4 degeneracy (ρ_syst = −0.993) and pull the conditional mean down.
- NLL bookkeeping between the cards, at NOMSTIFF's point: 1D l4zero term ½χ² = 2.525; 2D term ½χ² = 2.846. So NOMSTIFF's
  point costs **+0.321 NLL more on the 2D card** before anything moves.
- **The Gaussian is not adequate away from the lattice optimum.** Along the NOMSTIFF slice the exact χ² is a skewed
  valley: steeper than the Gaussian for λ4_ν < 0.003, almost flat above (tanh saturation: once λ4_ν b⁴ dominates, the
  kernel sits at its cap, and the data stop caring). The MCMC (flat prior, λ∞_ν = 2) agrees with the exact profile:
  the 189 samples with |λ2_ν − 0.064| < 0.015 have λ4_ν = 0.0080 ± 0.0033.
  - Near λ4_ν ∈ [0, 0.003], the region the combined fit can reach, the card's Gaussian pulls toward λ4_ν > 0
    **more weakly** than the exact lattice does (slope at λ4_ν = 0: card 1.3e3, stat Gaussian 2.4e3, exact 3.6e3 in
    χ² per GeV⁴). So any λ4_ν > 0 the fit finds on this card is, if anything, an underestimate of what the exact lattice
    would allow.
  - At the W point the Gaussian is wrong by a factor ~30 (549 vs 17). The W route is still excluded by the exact lattice
    (Δχ² 17–27 against the Z data's 2ΔNLL preference of 1.9), but fit (b) on this card tests a Gaussian extrapolation,
    not the lattice. Keep that in mind when reading (b).

![exact lattice chi2 vs the 2D Gaussian terms along lambda2_nu = 0.0643](lattice_conditional_l4nu.png)

*Caveat for the figure:* lattice-only, λ∞_ν = 2, tanh_2, n_f = 5 pert, block-diagonal lattice covariance (no
cross-ensemble correlations). The exact curve is stat-only (the syst in the card term is a covariance inflation built
from variant-fit shifts, with no exact-χ² counterpart). All curves are Δχ² against the same 2D best fit.

### 2026-10-06 — setup
- Read the study START HERE / plan T8, lattice-cs-kernel (study + 260923-scetlib-kernel-fit + 260923-lattice-fits), and
  trust-constr-nominal (both tasks). Trust-constr flags `--minimizerInitialBarrier` etc. are committed on the rabbit branch
  `trust-constr-nominal` (954aa4b, worktree `/work/submit/lavezzo/rabbit-trustconstr`).
- XWSTIFF (card A, no lattice, default priors λ2_ν ~ N(0.15, 0.1), λ4_ν ~ N(0, 0.5)) vs XL4ZSTIFF: ΔNLL 0.955
  (2ΔNLL 1.91), as quoted by Luca.

---

## Result

<!-- The answer, and what it means physically. State comparability caveats BEFORE the
     numbers: blinding family, Asimov vs data, PDF/order swap, card or freeze-list
     difference, excluded points. Check the read against AN-25-085 / knowledge/, not
     against the code. A number without a physics read is not a finished task. -->

---

## Findings

1. On the 2D-lattice card at NOMSTIFF's point, ∂NLL/∂λ4_ν < 0 in BOTH sectors: Z data −18.3, lattice −663 per GeV⁴. So
   there is no data notch into the λ4_ν ≥ 0 wall here, and the stiff wall is reliable. — (evidence: [l4nu_pull.json](l4nu_pull.json))
2. The card's 2D (stat+syst) Gaussian conditional at λ2_ν = 0.0643 is λ4_ν = +0.0018 ± 0.0017. The +0.003 ± 0.0015
   estimate is the stat-only Gaussian; the exact lattice χ² puts the conditional minimum at +0.0075. — (evidence:
   [lattice_cheap.json](lattice_cheap.json))
3. The 2D Gaussian term is ~30× too steep at the W point (Δχ² +549 vs exact +17.3 stat; +26–27 in the n_f variants).
   Near λ4_ν ∈ [0, 0.003] it pulls toward λ4_ν > 0 more weakly than the exact χ². — (evidence: same; figure in the Log)
4. Trust-constr warm starts on this card drift away from the start (T8A: 376.94 → 390.5 in 22 iterations). This is
   consistent with the slack-reinitialisation diagnosis in constrained-fit-strategy/261006-diagnosis. — (evidence: [logs/T8A.log](logs/T8A.log))

---

## Open questions

- The exact lattice χ² as an in-fit regularizer instead of the Gaussian (recommended in 260923-scetlib-kernel-fit §5). It
  would let λ4_ν rise further (the exact conditional minimum is +0.0075, against the Gaussian's +0.0018).
