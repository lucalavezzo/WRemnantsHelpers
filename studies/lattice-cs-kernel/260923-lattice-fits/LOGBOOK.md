---
title: Real-data card-A fits with the ASWZ lattice CS-kernel constraint
slug: 260923-lattice-fits
study: lattice-cs-kernel
status: done
created: 2026-09-23
updated: 2026-09-24
owner: study-worker
---

# Real-data card-A fits with the ASWZ lattice CS-kernel constraint

**Task:** When the ASWZ lattice CS-kernel constraint replaces the default CS priors in the real-data card-A fit (current AD param model), where do the cold-start fits land, walled and unwalled: NP λ, Δχ²_data resistance to the lattice, TMD physicality, and Δα_s (blinded, σ units)?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-09-24 10:20)

> **All three l4zero lattice fits are done. Nothing is running.**
> - Walled lattice fit vs the old walled fits: Δα_s +0.01σ / +0.32σ; Δχ²_data +5.0 / +4.7; σ(α_s) 1.158.
> - The warm unwalled lattice fit reaches 375.53, below both the cold unwalled fit (382.43) and the walled one
>   (376.72), but only with TMD λ2 = −0.078 < 0 (unphysical; ~1σ). Its α_s is +0.37σ from the walled lattice fit.
> - Comparable: rabbit 2a59246 ≡ f77f10e bit-for-bit on NLL and the blinding frame (Result caveats).

- **Next action:** none; waiting on the orchestrator/Luca.
- **Blocking on:** nothing.

---

## Log

### 2026-09-24 — why ptll-projected saturated is 81/39 when the 2D test is 748/778 (Q&A with Luca)
- The projection test = main fit vs the same fit plus 39 free per-ptll scales (common to all yll), re-profiled.
  It is nested inside the full saturated test, so q_full = q_proj + q_rest: 748.2 = 80.9 (39 dof) + 667.4 (739 dof).
  The excess over expectation (~+42) is only ~1σ of χ²_778, so the 2D test is diluted. The rest sits 1.9σ **low**
  (CDF 2.8 %) and partly masks it.
- **Data-vs-postfit on the ptll marginal is fine:** stat-only Σ(d−p)²/d = 42.3/39 (p 33 %). The 81 does not come
  from marginal residuals.
- The split of 2ΔNLL (main − sub-fit) closes exactly: data 53.0, card constraints 16.5, model priors 6.1, lattice 5.2,
  wall 0.01. In the sub-fit the nuisances relax: lumi −1.46→0, QCDscaleZfine_PtV15_20 −1.88→−0.15, FSR, weak,
  resumFOScaleEnvSymDiff −1.5→0, mb_up −1.57→−0.89, and λ2_ν 0.063→0.128, next to the lattice (0.1345).
- α_s moves by −6.09 θ in the sub-fit, where σ_sub = 3.32 θ against 0.58 θ in the main fit. Nested-shift sd ≈ 3.27, so
  this is 1.9σ. The ptll marginal carries ~97 % of the α_s information (1 − (0.58/3.32)²).
- The squared scales tilt 0.889→1.126 across ptll, but they mostly absorb the α_s/λ shift and cannot be read as a
  data/model mismatch.
- Read: the fit reproduces the ptll marginal only through a coordinated pull of nuisances + α_s + NP. The yll/2D
  information and the priors (and the lattice) prefer a different configuration. This is not a machinery bug:
  the sub-fit converged (EDM 1.9e-7), started warm, and the blinding frame is shared.
  (`scripts/decompose_projection_sat.py`, `scripts/sat_cov.py`, `logs/decompose_projection_sat_LATL4ZWALLCOLD.log`)
- Follow-up. **Units:** −6.09 θ is Δα_s = −0.0122, i.e. −10.5 σ_main, but only 1.9σ against the nested sd, because
  σ_sub = 6.6e-3.
- **Blinding is excluded as the cause.** The offset is x_phys = x + N(0,5)·scale, seeded by sha256("alphaS_data").
  The same seed is logged for both fits (log lines 44, 832). SCETlibADParamModel declares no
  `blind_additive_scale` (so it is 1.0), and CompositeParamModel concatenates the per-POI scales. The offsets are
  therefore identical, and the Δ is physical.
- The sub-fit's first logged loss (353.74) comes after the first scipy step (scipy calls the callback after each
  iteration), so the start is not logged directly.
- Defensibility read: the full 2D p-value is not the relevant metric for α_s, because ~97 % of the α_s information
  is the ptll marginal, and the ptll marginal is where the test fails (Z ≈ 3.7). What is still needed: does added
  ptll-shape freedom (a few smooth yll-independent modes) resolve the tension without moving α_s by a significant
  fraction of σ? Plus a toy calibration of q_proj.

### 2026-09-24 09:20–10:00 — LATL4ZWALLCOLD fitresult written; comparison vs old walled; rabbit-version check
- The walled l4zero fit exited rc 0 at 09:20: main NLL 376.72164572, EDM 3.7e-17, 685 iterations. The ptll-projection
  saturated sub-fit converged (EDM 1.9e-7, 236 iterations) at 80.85/39. Tables are in Result §1.
- **Found:** all three l4zero fits ran on rabbit **2a59246**, not f77f10e. The shared `WRemnants/rabbit` was switched
  to `main-plus-ours` on 09-23 at 18:07 by another session (reflog); the fit stamps show it. **Verified that this does
  not break comparability:**
  - the old CCWALLWARMPF vector, re-evaluated with the new rabbit, gives a bit-identical NLL (371.43972904973504)
    and the same saturated 742.88;
  - its stored blinded α_s is identical (difference 0.000e+00);
  - the blinding offset code is line-identical.

  (`scripts/nll_crosscheck.sh`, `logs/nll_crosscheck_result.txt`, out dir `/ceph/.../260923_lattice_fits/nll_crosscheck/`)
- Bug fixed in `analyze_fits.py`: the wall penalty had counted the held condition λ4_ν ≥ 0.005 (+0.551) that the wall
  itself drops. It now counts armed conditions only. LATL4ZWALL lpen went from 0.554 to 0.003, which matches the
  0.00317 computed from the snapshot.
- Impacts: `impacts_LATL4ZWALLCOLD/`, `impacts_LATL4ZUNWCOLD/` (same command as 260917), `grouped_impacts.json`,
  `logs/grouped_impacts.log`. Plots: `kernel_space_postfit.png`, `np_forms_postfit.png`.
- LATL4ZUNWWARM: main fit converged at **375.53389** (EDM 3.6e-16, 17 iterations, 494 s). Its fitresult waits on its
  projection sub-fit. The λ values below come from its converged snapshot (`scripts/snapshot_penalty.py`).

### 2026-09-24 08:31 — LATL4ZUNWWARM launched (WARM: seeded with the full vector from LATL4ZWALLCOLD's minimum)
- Luca approved it via the orchestrator. Same card (l4zero statsyst) and the same settings as LATL4ZUNWCOLD, no wall,
  plus `--externalPostfit <seed>`.
- **The seed** is rabbit's own converged snapshot of the walled arm, `snapshot_fitresults_LATL4ZWALLCOLD.hdf5`:
  - written 07:37 at log line 810 ("Wrote parameter snapshot (converged)"), immediately after the main minimisation
    ended at loss 376.72164572, EDM 3.7e-17;
  - copied byte-identical (md5 e8ccdb69…) to `l4zero_unwalled_warm/seed_from_LATL4ZWALLCOLD_converged.hdf5`. Nothing
    was hand-converted;
  - it is rabbit's documented resume format ("resume with --externalPostfit <snapshot>"). CCWALLCOLDR was resumed the
    same way;
  - it has the same card and freeze list (46 model params), and differs only in the wall, which is exactly the
    fit-queue rule;
  - the walled `fitresults` was not written yet: its projection sub-fit was still running.
- `workflows/fitterAD.sh` has no `--seedFrom` (that flag belongs to fitterSCETlibNP.py). `--externalPostfit` IS the
  full-vector warm start: rabbit loads every parameter.
- Resources: MemAvailable 1174 GB, since the other session's y35 fits had exited, so it runs alongside the walled
  arm's sub-fit (61 GB). Threads 2356.
- **Startup check:**
  - still 44 of 53 SCETlib + 2 envelope = 46, so λ4_ν is held at 0 as before;
  - iteration 0 loss **376.67951**. Expected ≤ walled minimum 376.72165 − wall penalty 0.00317 = 376.71848. It sits
    0.039 lower; the likeliest cause is the binByBinStat β being re-profiled at the start of the new process. It is
    consistent with "≤ 376.7" and is still falling (iteration 1: 376.65169).
- At the walled minimum (from the snapshot): λ2_ν = 0.0632 (lattice term lext = 2.605, −2.3σ), λ2 = 0.028,
  δλ2 = −0.0037, λ4 = 0.0869. So L2(|Y|=2.5) = 0.028 − 0.0234 = 0.0046, at the wall's 0.005 margin.

### 2026-09-24 ~04:50 — LATL4ZWALLCOLD startup verified
- Fitting **44 of 53 + 2 envelope = 46**, with priors on 44, so λ4_ν is not fitted. `[NPDampingWall] armed on 5 of 8`.
  Held at the anchor: {λ∞ 1, λ∞_ν 2, **λ4_ν 0**}. Dropped as constant: "λ4_ν ≥ 0 (CS large-b) = 0", as predicted.
- The active conditions are λ2_ν ≥ 0.005 (the only CS one left), plus the four TMD ones at |Y| = 0 and 2.5.
- Iteration 0 loss 71190.34, identical to the unwalled arm: the start is inside the wall, so there is no penalty at
  the anchor.

### 2026-09-24 04:31 — LATL4ZUNWCOLD done; LATL4ZWALLCOLD launched 04:33
- **Unwalled l4zero arm finished**, rc 0, 193 GB max RSS.
  - Minimiser: 1465 iterations; a no-improvement early stop, then one restart that stayed at the same point. Loss
    382.43121737. scipy status 2 carries no convergence information (see the rabbit_minimizer_tolerances note).
  - Postfit covariance: **EDM 6.3e-7**, 0 negative eigenvalues, cond 5.5e9. ‖grad‖ is not in the fitresult; the
    log prints only a truncated jac, whose largest visible entries are ~3e-4.
  - Saturated GoF: 2ΔNLL 764.86 / 778, p = 62.5 %. This includes the lattice term (lext = 0.378, so the effect is
    at most 0.76).
  - The ptll-projection saturated sub-fit did NOT converge (EDM 0.026 after 445 iterations). Its 94.2/39 is not
    usable.
  - Full read: `logs/analyze_unw.log`. Tables go in **Result** once the walled arm is in.
- **Walled l4zero arm** `LATL4ZWALLCOLD` launched 04:33, into `/ceph/.../260923_lattice_fits/l4zero_walled/`. The
  unwalled arm had exited, so this is still one fit at a time. MemAvailable was 511 GB; the other session's three
  y35 fits were at 270–314 GB each.

### 2026-09-23 18:55 — RETRACTION: the killed LATWALLCOLD was not stuck; cold fits on card A are just slow
- My 17:45 note called LATWALLCOLD's slow, near-linear decline "stuck, not slow". **That was wrong.** The reference
  cold fits trace the same staircase at the same pace:
  | iteration | CCKRYLOV (cold, unwalled) | CCWALLCOLD (cold, walled) | LATWALLCOLD (killed) |
  |---|---|---|---|
  | 100 | 1780.7 | 1623.0 | ~1545 |
  | 200 | 1424.0 | 1273.1 | — |
  | 290 | ~1180 | — | 1156 |
  CCKRYLOV reached its 379.2 minimum only at **iteration ~1675, 4.1 h** (then 42 more iterations in the
  CCCOLDSELF restart). So LATWALLCOLD was on schedule, not stuck. Its λ state at the kill was mid-descent and says
  nothing about where it would have landed. (evidence:
  `../../scetlib-ad-param-model/260915-cachecorr-ab/logs/fix_krylov_cold_114000.log`, `fit_wall_cold_141258.log`)
- Consequence for planning: expect ~3–5 h of minimisation per l4zero arm, plus the Hessian, impacts and saturated
  test. With the arms run one after the other, both should be done in ~10–12 h.

### 2026-09-23 18:35 — new design: λ4_ν frozen at 0 + 1D λ2_ν lattice term; LATL4ZUNWCOLD launched
- **Design (Luca, via orchestrator).** Two changes from the original brief; everything else is unchanged (card A,
  old cache, authval, same runners and flags):
  1. **Constraint: 1D on λ2_ν.** It is the direct lattice refit at λ4_ν = 0 (λ∞_ν = 2, k1 profiled), from
     `../260923-scetlib-kernel-fit/fit_l4zero.json`:
     - λ2_ν = **0.134549**, σ_stat 0.020071, σ_syst 0.023984, **σ_tot 0.031275**;
     - syst = √Σδ² over: n_f matched at μ=1 (−0.0131), k2 only (−0.0177), drop b_T<0.2 (−0.0095). All three are
       negative, so the syst is one-sided toward lower λ2_ν;
     - NOT the Gaussian conditional of the 2D fit (0.108), which is biased low.
  2. **λ4_ν frozen at its anchor 0.** Done exactly as λ∞_ν: it is left out of `fit_params`, so it is held at the
     correction's anchor and never reaches rabbit. `fit_params` = the reference arms' 45 fitted SCETlib names minus
     λ4_ν = 44 (`logs/fit_params_l4zero.txt`, built from CCCOLDSELF's param_priors; order kept). Model args become
     `threads=128 fit_params=<44> prior_sigmas=lambda2_nu=nan`. Only λ2_ν needs a prior override, and a frozen
     parameter never reaches `_setup_priors`, so there is nothing to override for it.
- **Wall with λ4_ν held.** The wall's CS large-b condition λ4_ν ≥ 0.005 depends only on a held lambda. The wall
  evaluates such conditions once, without the margin (value 0 ≥ 0 passes), and drops them as constant
  (`np_damping_wall.py:795-816`, written for exactly this freeze). **So the only CS condition left is
  λ2_ν ≥ 0.005, and the wall acts mainly on the TMD side** (L2 ≥ margin and 3λ∞²λ4 + L2³ ≥ margin, at |Y| = 0
  and 2.5).
- **Cards** (injector `--l4zero` mode):
  - `/ceph/.../260923_lattice_fits/cards/cardA_latticeASWZ_l4zero_statsyst.hdf5` (primary) and `..._statonly.hdf5`;
  - the injector refuses to run unless the card's λ4_ν anchor = 0 and λ∞_ν = 2 (both are);
  - θ: μ = −0.1545, σ = 0.3127 (stat+syst) / 0.2007 (stat); H = 10.224. This is a mild constraint, only ~3× the
    default N(0,1) prior's precision (it replaces that prior);
  - χ²_lat at the card anchor = 0.24 (stat+syst) / 0.59 (stat);
  - checks: map diff 0.0, χ² invariance 1.0e-15, rabbit const 0.122032915 = ours, external_terms == ['lattice_cs'];
  - `diff_cards.py`: 27 shared, 0 differ; only the 3 lattice datasets were added; card A md5 unchanged. (evidence:
    `logs/inject_l4zero_*.log`, `logs/diffcards_l4zero_*.log`)
- **Resources at launch:**
  - MemAvailable 422 GB;
  - the other session's three y35 fits (Y35WALLCOLD, Y35COLD, Y35WARM, out dir `260923_y35_fits`) use ~326 GB RSS
    each;
  - two ~185 GB lattice fits would leave no clear headroom, so they run one after the other, unwalled first.
  Threads 6314 of 32768.
- **Startup verified** (`fit_LATL4ZUNWCOLD.log`):
  - "fitting **44 of 53** SCETlib parameter(s) + 2 envelope = 46 total"; the references had 45 + 2 = 47, so λ4_ν
    is gone from the fit;
  - "Gaussian priors on 44 parameter(s)": λ2_ν is freed and λ4_ν is not a fitted parameter at all;
  - anchor read from the correction runcard (22 of 53 values), and λ4_ν is held at its anchor there, so physical
    λ4_ν = 0 exactly (there is no θ for it);
  - the model took `prior_sigmas=lambda2_nu=nan` plus the `fit_params` list without complaint;
  - cold start: iteration 0 loss 71190.34, iteration 1 28488.28.
- Analysis/plot tooling is ready and was tested on the references:
  - `scripts/analyze_fits.py` (1D-aware, `LAT_L4ZERO=1` default). Basin markers are now lumi / resumTNP_b_qqV /
    pdfEig14 (+ b_qg, pdfEig23). `resumScaleMuF` is not a fitted parameter in this build (DEFAULT_FROZEN, replaced
    by the scale envelope), so the 260911 marker set cannot be used;
  - `scripts/postfit_plots.py`: kernel space + both NP form factors via `np_function_plots.plot_np_functions`.
- Runner `scripts/run_fit_l4zero.sh` = `run_fit.sh`, with the fit_params list injected and asserted (44 names,
  no λ4_ν). Out dir `/ceph/.../260923_lattice_fits/l4zero_unwalled/`, log `fit_LATL4ZUNWCOLD.log` there.

### 2026-09-23 18:06 — LATWALLCOLD killed (Luca)
- Before the kill: last iteration 293, loss 1156.15. I sent SIGTERM to the rabbit python pid only, not with
  pkill, and it exited with rc 143 after iteration 294 (loss **1130.64**, elapsed 1588 s of minimisation). rabbit
  wrote its `signal-SIGTERM` snapshot. `run_fit.sh`, `time` and `fitterAD.sh` exited with it, and process group
  2693365 is empty. `fitresults_LATWALLCOLD.hdf5` is only the 99 KB meta placeholder, with no results.
- **λ state at the kill** (from `snapshot_fitresults_LATWALLCOLD.hdf5`, via `scripts/read_snapshot.py` →
  `logs/snapshot_LATWALLCOLD_at_kill.txt`). This is **not a minimum**: the loss was ~760 above the walled reference.
  | λ | θ | physical |
  |---|---|---|
  | λ2_ν | −1.4443 | **+0.00557**, on the wall's 0.005 margin, i.e. railed as in the old walled arms |
  | λ4_ν | −0.00015 | **−0.000076**, just below 0 but inside the probe's clean zone (≥ −0.001) |
  | λ2 | +0.5531 | +0.6765 |
  | λ4 | −1.0143 | **−0.1072**: the TMD large-b coefficient is negative (the wall checks the 3λ∞²λ4 + L2³ combination, not λ4 alone) |
  | δλ2 | +0.0038 | +0.0019 |
  At this point the lattice term is paying heavily on λ2_ν (0.0056 against the lattice's 0.184 ± 0.057, about −3.2σ
  marginal), and λ2_ν is resting on the wall's floor: the data pull it down, and the lattice and the wall hold it up.

### 2026-09-23 ~17:45 — orchestrator: hold; LATWALLCOLD progress
- Orchestrator: Luca has not decided on the guard or on LATWALLCOLD yet. Leave it running, launch nothing else, and
  report once, when it finishes or fails.
- Loss by iteration: 19: 26609 · 39: 2284 · 59: 1630 · 99: 1545 · 139: 1468 · 179: 1394.5, at ~7 s/iteration.
  **(RETRACTED 18:55, see above)** **This is still far above the walled reference minimum** (CCWALLCOLDR 372.7; the lattice term adds only O(1–10)
  to that), and it is decreasing slowly and roughly linearly. The fit-queue skill describes this pattern as "stuck,
  not slow", but the fit is still moving, so no verdict yet.

### 2026-09-23 17:25 — LATWALLCOLD launched (cold, walled, lattice stat+syst)
- `scripts/run_fit.sh <statsyst card> LATWALLCOLD /ceph/.../260923_lattice_fits/walled --wall`. This is
  `agent_setup.sh --scetlib authval` → `workflows/fitterAD.sh --wall` with `threads=128
  prior_sigmas=lambda2_nu=nan,lambda4_nu=nan -v 4 --earlyStopping 100`. Apart from the card and prior_sigmas, it is
  identical to CCWALLCOLD, which CCWALLCOLDR resumed.
  The reference arms were checked from their fitresult meta_info:
  - CCCOLDSELF is a self-restart of the cold CCKRYLOV (`--externalPostfit CCKRYLOV`, earlyStopping 20).
  - CCWALLCOLDR is a resume of the cold CCWALLCOLD from its converged snapshot (earlyStopping 100).
  - Both ran on authval + rabbit f77f10e with 46/47 priors.
  - The held unwalled arm will use the default earlyStopping 20, as CCKRYLOV did.
- Confirmed in the log:
  - priors on **44** params (λ2_ν, λ4_ν freed);
  - NPDampingWall armed on 6/8 conditions, binding |Y| = 2.5, margin 0.005;
  - cold start, iteration 0 loss 71216.45.
- **Code versions (stamped in the fit log):**
  - libscet-qT.so md5 `71b5e68a…` (authval b66f8de, same as the references);
  - scetlib_tf.py md5 `77b82b2e…` (hvp zero-seed skip present);
  - WRemnants `ede643dc` + dirty tree. The scetlib_ad/*.py files were last modified 2026-09-17 08:59, i.e. before
    both reference launches (14:12 and 19:37 that day);
  - rabbit `f77f10e` + local diff (md5 `3493934b…`): the saturated-fit regularizer arming and a sibling snapshot
    path, modified 09-17 19:28. CCCOLDSELF (launched 19:37) ran this exact rabbit. CCWALLCOLDR (launched 14:47)
    predates the 19:28 edit. That edit touches only the postfit saturated test and the snapshot paths, not the
    minimisation.
  - **α_s×pdfEig clad adjoint fix: NOT in this build.** authval b66f8de is the frozen build that carries the defect
    (260922-clad-adjoint-fix: no C++ was changed; the authval .so is untouched, md5 71b5e68a). The reference arms
    share it, so the comparison is like-for-like, and both inherit the 0.49 %-of-σ(α_s) gradient bias.

### 2026-09-23 — λ4_ν probe on the PRODUCTION cache: ERRATIC below λ4_ν ≈ −0.001, so the unwalled arm is HELD
- `scripts/probe_l4nu.py`. Cache `pdf62_corrgrid_260827/merged_full`, authval `b66f8de`. All 770 gen bins, every other
  parameter at the anchor, λ4_ν ∈ {0, −0.001, …, −0.012} along two lines: λ2_ν = 0.15 (anchor) and 0.184 (lattice mean).
  At each point it records σ and J, compares with fwd/bwd FDs at h = 1e-4, and compares σ/σ(0) with the linear AD prediction.
  (evidence: `logs/probe_l4nu.log`, `probe_l4nu.json`)
- **Result: the cached value function breaks down just below λ4_ν = 0.** The breakdown is confined to qT ≲ 4 GeV.
  | λ2_ν | λ4_ν | max\|σ/σ(0)−1\| at qT<5 | linear prediction | FD vs AD (frac. of max\|J\|) | σ ≤ 0 bins |
  |---|---|---|---|---|---|
  | 0.184 | −0.001 | 0.0003 | 0.0003 | 3e-4 (clean) | 0 |
  | 0.184 | −0.002 | **0.18** | 0.0005 | 0.64 / 1.86 | 0 |
  | 0.184 | −0.004 | 0.52 | | 0.07 / 0.11 | 0 |
  | 0.184 | −0.006 (≈ lattice) | **1.65** | | 0.07 | 0 |
  | 0.184 | −0.008 | 2.39 | | 0.03 | **6** |
  | 0.15 | −0.002 | 0.16 | | 0.46 / 0.43 | 0 |
  | 0.15 | −0.007 | 2.26 | | 0.03 | **6** |
  | 0.15 | −0.012 | 12.8 | | 0.02 | **33** |
  At λ4_ν = 0 and −0.001 the response is linear and AD = FD to 3–4e-4, as it should be. From −0.002 the low-qT bins
  oscillate from bin to bin by O(1) (figure), d ln σ/dλ4_ν swings between ±10³, and σ goes negative from −0.007/−0.008.
  This is the same pathology the Q-split cache showed (260923-qsplit-fisher). It is the known negative-λ4 trap: with
  λ4_ν<0 the tanh_2 CS kernel changes sign at b_T ~ √(λ2_ν/|λ4_ν|) ≈ 5.6 GeV⁻¹ and anti-damps at large b_T. The
  cache's b_T rules were trained at λ4_ν = 0 and cannot represent an integrand that grows there.
  ![σ(λ4_ν)/σ(0) vs qT on the lowest |Y| row](probe_l4nu_ratio.png)
  *Production cache, gen level, lowest |Y| row, other parameters at the anchor (left: λ2_ν = 0.15, right: 0.184). This
  is the cached AD prediction, not the SCETlib truth: it says the cache cannot be evaluated there, not what physics
  does there.*
- **Consequence (per the brief): the unwalled lattice arm is NOT launched.** The lattice central value λ4_ν = −0.006
  (σ 0.004) lies well inside the region where the model cannot be evaluated, so an unwalled fit would be steered by
  cache artefacts. It needs a λ4_ν ≥ 0 guard, and I have not improvised one. Reported to the orchestrator.
- **The walled arm is at risk too.** τ=5 is weaker than this lattice term in the stiff direction. The wall's λ4_ν
  condition is λ4_ν ≥ 0.005 with a penalty e^{2τ}·relu(0.005−λ4_ν)², i.e. a curvature of 4.4e4 in λ4_ν. The lattice's
  marginal curvature is 1/σ² = 6.25e4 (stat+syst, σ 0.004). Ignoring the data, the two balance at
  λ4_ν ≈ (6.25e4·(−0.006) + 4.4e4·0.005)/1.07e5 ≈ **−0.0015**, which is right at the onset of the erratic zone. The
  data (walled references sit at λ4_ν ≈ +0.04) should pull it positive, but nothing guarantees that. Launched anyway,
  as the brief says. Whether λ4_ν ends ≥ −0.001 has to be checked before any of its numbers are believed.
- **Node memory incident (not mine), 17:20–17:23.** The other session's `backend_check.py` and `cache_to_theorycorr.py`
  on the new y35 cache each grew to ~640 GB RSS. MemAvailable fell to **13 GB** and swap to 139 GB. It recovered on its
  own. I launched nothing during it and touched nothing of theirs.

### 2026-09-23 — setup, and a plan change that was reverted
- **Plan changes from the orchestrator (Luca):** (1) first *"don't launch on card A; use the new |Y|≤3.5 cache
  `pdf62_y35_260921` + pin 2da973d; prepare only"*; (2) then **REVERTED**: *"forget the new cache, back to the
  original brief: card A, old cache, the same build as CCCOLDSELF/CCWALLCOLDR"*. I never loaded or touched the new
  cache or the 2da973d pin, so nothing needed stopping. The new-cache version is deferred.
- **Constraint** (from `../260923-scetlib-kernel-fit/fit_results.json`, entry `tanh2 | linf=2 | k1`; the 2×2 block
  is the k1 marginal): μ = (λ2_ν, λ4_ν) = (0.184433, −0.005920); σ_stat = (0.03828, 0.00325), ρ −0.8825.
  - Systematic covariance = Σ d dᵀ over three independent shifts, one per group. In each group the larger shift is
    taken, with "larger" judged by χ² in the stat metric:
    | group | variants (d_λ2ν, d_λ4ν; χ²_stat) | taken |
    |---|---|---|
    | n_f scheme | nf4 (−0.0180, +0.00084; 0.33) · nf5 matched at μ=1 (−0.0179, +0.00075; 0.37) | matched μ=1 |
    | k-form | k2 only (−0.0370, +0.00215; 1.10) · k1+k2 (+0.0278, −0.00151; 0.67) | k2 only |
    | b_T window | drop b_T<0.2 fm (+0.0075, −0.00047; 0.04) | it |
  - n_f4 and n_f-matched are two answers to one question (their shifts agree to 3 %), so adding both would count it
    twice. The same goes for the two k-forms.
  - σ_syst = (0.0418, 0.0023), ρ −0.993. **Stat+syst (primary): σ = (0.0567, 0.0040), ρ −0.911.** The syst roughly
    doubles the variance along the loose direction and hardly touches the stiff one (eigenvalue in θ
    9.35e-6 → 1.09e-5).
  - Anchor under the constraint: χ²_lat(θ=0) = 5.42 (stat+syst) / 5.58 (stat only), on 2 dof.
- **Injector** `scripts/inject_aswz_cs_prior_theta.py`, adapted from 260911. It reads the numbers from the JSON
  rather than retyping them, applies no conditioning, and refuses to run if the card's λ∞_ν anchor ≠ 2. Card
  anchors: λ2_ν 0.15, λ4_ν 0, λ∞_ν 2; REPARAM widths 0.10 / 0.50. All checks pass: map vs `wall.physical_from_theta`
  0.0; χ² invariance 4.6e-15; 1 along each eigenvector; 1/(1−ρ²) along each axis; rabbit's own `const`
  2.711910762 = ours; `FitInputData(out).external_terms == ['lattice_cs']`.
  In θ: H = [[18.304, 1181.69], [1181.69, 91932.8]], g = (7.6897, 681.673), cond(C_θ) = 2.95e4. That is 5× stiffer
  than 260911's 5731, so watch for trust-krylov stalls. (evidence: `logs/inject_statsyst.log`,
  `logs/inject_statonly.log`, `logs/inject_dryrun_*.log`)
- **Cards** (on ceph): `/ceph/.../alphaS/260923_lattice_fits/cards/cardA_latticeASWZ_statsyst.hdf5` (primary) and
  `..._statonly.hdf5`. Card A is unchanged (md5 013135fa… before and after, `logs/cardA.md5`).
  `diff_cards.py`: 27 shared datasets, 0 differ (11 decoded, 16 by raw-chunk md5); the only additions are the 3
  `external_terms/lattice_cs/*` datasets. (evidence: `logs/diffcards_statsyst.log`)

---

## Result

### Comparability caveats (read first)

- **All rows use the same card A data, cache `pdf62_corrgrid_260827`, SCETlib authval `b66f8de` and WRemnants tree.**
  The old reference rows all lack the α_s×pdfEig clad adjoint fix, and so do the new ones.
- **rabbit differs, and I only found this at 09:30 on 09-24.**
  - The three l4zero fits ran on rabbit **2a59246** (`main-plus-ours`). Another session checked it out into the shared
    `WRemnants/rabbit` on 09-23 at 18:07, 28 min before LATL4ZUNWCOLD launched. My runner stamped it, but I did not
    read the stamp.
  - The references ran on **f77f10e** + local fixes.
  - The difference is blinding moved into its own module (#178), the saturated-fit fixes (#180/#181), global impacts
    from an external covariance (#158) and scan detail.
  - **Checked directly:** I evaluated CCWALLWARMPF's own parameter vector on card A with the new rabbit (`--noFit`,
    walled; `scripts/nll_crosscheck.sh`).
    - It gives nllvalreduced **371.43972904973504, bit-identical** to the old fit.
    - Its saturated 2ΔNLL is 742.88, the same as before.
    - The stored blinded α_s differs by **0.000e+00** (`logs/nll_crosscheck_result.txt`).
  - So NLLs, GoF and the blinding frame are directly comparable across the two versions. The blinding offset
    generator is also line-identical (sha256(name + "_data"), N(0, 5)).
- **Blinded:** only Δα_s in σ units appears, never an absolute value. Every row is an integer-data fit of the same
  parameter name, so all rows share one offset.
- **The l4zero arms FREEZE λ4_ν = 0** (46 model parameters, 44 priors) and replace the λ2_ν prior with the 1D ASWZ
  term. The old arms float λ4_ν (47 parameters, 46 priors). So `lc` counts different priors, and the old walls also
  enforce λ4_ν ≥ 0.005. The walled old arms pay for that (CCWALLCOLDR lpen 0.592: λ4_ν = −0.0002 against the 0.005
  margin). The new walls do not, because the held λ4_ν = 0 condition is dropped.
- **CCWALLWARM = CCWALLWARMPF:** the original CCWALLWARM fitresult is a 99 KB placeholder (postfit crash, 260915).
  CCWALLWARMPF is the recovery pass at the same converged point (NLL 371.43972905), with errors, so it stands in for
  CCWALLWARM everywhere below.
- **Global impacts leave out the lattice term.** `scetlibNPgammaNu` global is 0.000 in the lattice arms: its only
  parameter, λ2_ν, carries no prior; it is constrained by the external term, which the global-impact decomposition
  does not count as a source. The global `stat` group is NaN in 4 of the 6 fits (a known rabbit output issue, not
  specific to these fits).

### 1. Walled: new lattice + wall (LATL4ZWALLCOLD) vs the old walled fits

| | **LATL4ZWALLCOLD** (new, cold) | CCWALLCOLDR (old, cold) | CCWALLWARM(PF) (old, warm, deepest) |
|---|---|---|---|
| NLL (reduced) | **376.7216** | 372.6747 | 371.4397 |
| EDM / iterations / negative eigenvalues | 3.7e-17 / 685 / 0 | 6.6e-10 / 114 (resumed) / 0 | 8.1e-16 / — / 0 |
| ln(data) | 354.998 | 352.474 | 352.641 |
| lc (priors: model + card) | 19.115 (4.120 + 14.995) | 19.608 (4.627 + 14.982) | 18.794 (4.484 + 14.310) |
| lpen (wall, τ=5) | 0.003 | 0.592 | 0.005 |
| lext (lattice) | 2.605 | — | — |
| **Δχ²_data (new − old)** | — | **+5.05** | **+4.71** |
| full saturated 2ΔNLL / ndof, p (as printed) | 753.44 / 778, 73.0 % | 745.35 / 779, 80.2 % | 742.88 / 779, 81.9 % |
| same, lattice term removed (−2·lext) | **748.23 / 778, p = 77.3 %** | = | = |
| **projected-ptll saturated** 2ΔNLL / 39 | **80.85, p = 0.009 %** (sub-fit EDM 1.9e-7, converged) | 72.27, p = 0.095 % | 70.39, p = 0.15 % |
| σ(α_s) [1e-3] | **1.158** | 1.290 | 1.085 |
| **Δα_s (new − old)** / σ_old | — | **+0.01σ** | **+0.32σ** |
| basin markers θ: lumi / b_qqV / pdfEig14 / b_qg / pdfEig23 | −1.46 / −0.66 / −0.35 / −0.16 / −0.34 | −1.56 / −0.36 / −0.41 / −0.82 / −0.35 | −1.44 / −0.29 / −0.39 / −0.75 / −0.31 |
| L2 distance in model θ (45 common, α_s excluded) | — | 1.18 | 1.21 |

The ptll-projection numbers are the SATURATED 2ΔNLL, not rabbit's "Linear chi2 … chi2/ndf" printout (which says 83
for this fit). The projection sub-fit includes the lattice term in both of its fits, so it is not removed there.

**NP λ (physical) and damping checks**, at |Y| = 0 and 2.5 (the binding |Y|):

| | λ2_ν | λ4_ν | λ2 (TMD) | λ4 (TMD) | δλ2 | lattice pull (λ2_ν), χ²_lat (stat+syst / stat) | damping |
|---|---|---|---|---|---|---|---|
| **LATL4ZWALLCOLD** | +0.0632 ± 0.0229 | 0 (frozen) | +0.028 ± 0.043 | +0.0869 ± 0.027 | −0.0037 | **−2.28σ**, 5.2 / 12.6 | all pass. L2(2.5) = +0.0046, on the 0.005 wall margin |
| CCWALLCOLDR | +0.0073 ± 0.050 | −0.0002 | +0.078 | +0.119 | −0.0090 | −4.07σ, 16.6 / 40.2 | λ4_ν −0.0002 < 0 (the wall's hinge equilibrium) |
| CCWALLWARM(PF) | +0.0045 ± 0.0048 | +0.0434 | +0.108 | +0.0016 | −0.0093 | −4.16σ, 17.3 / 42.0 | λ2_ν and the TMD large-b condition at |Y|=2.5 are both on the margin |
| (lattice, λ4_ν = 0) | 0.1345 ± 0.0313 | 0 | | | | | |

**Grouped α_s impacts** [units of 1e-3; traditional / global; same tool and grouping as
`scetlib-ad-param-model/260917-cachecorr-physics/impacts_walled/`, i.e. `rabbit_plot_pulls_and_impacts.py
--grouping alphaS --scaleImpacts 2.0`; numbers read from each fitresult's own `impacts_grouped` /
`global_impacts_grouped` by `scripts/grouped_impacts.py`. That reader reproduces the old 260917 table exactly, e.g.
CCWALLWARMPF pdfEig 0.705 / 0.629]:

| group | **LATL4ZWALL** | CCWALLCOLDR | CCWALLWARM(PF) | LATL4ZUNW | CCKRYLOVWARM | CCCOLDSELF |
|---|---|---|---|---|---|---|
| `pdfEig` | 0.801 / 0.761 | 0.888 / 0.873 | 0.705 / 0.629 | 0.791 / 0.857 | 0.805 / 0.723 | 0.431 / 0.256 |
| `resumTNP` | 0.782 / 0.571 | 0.844 / 0.641 | 0.642 / 0.424 | 0.839 / 0.881 | 0.808 / 0.531 | 0.431 / 0.338 |
| `resumNonpert` | 0.953 / 0.042 | 1.114 / 0.292 | 0.861 / 0.034 | 0.852 / 0.036 | 1.111 / 0.132 | 0.498 / 0.076 |
| … `scetlibNPFeff` | 0.779 / 0.042 | 0.949 / 0.136 | 0.242 / 0.029 | 0.393 / 0.036 | 1.001 / 0.128 | 0.484 / 0.059 |
| … `scetlibNPgammaNu` | 0.051 / 0.000* | 0.518 / 0.258 | 0.822 / 0.018 | 0.498 / 0.000* | 0.521 / 0.029 | 0.479 / 0.048 |
| `resumScale` | 0.285 / 0.118 | 0.276 / 0.114 | 0.316 / 0.130 | 0.084 / 0.041 | 0.376 / 0.158 | 0.198 / 0.085 |
| `stat` | 0.860 / NaN | 0.925 / NaN | 0.783 / 0.337 | 0.839 / NaN | 0.855 / 0.126 | 0.486 / 0.371 |
| `binByBinStat` | 0.155 / 0.222 | 0.188 / 0.283 | 0.155 / 0.226 | 0.175 / 0.238 | 0.109 / 0.179 | 0.097 / 0.125 |
| `experiment` | 0.514 / 0.461 | 0.633 / 0.579 | 0.501 / 0.448 | 0.406 / 0.367 | 0.624 / 0.573 | 0.339 / 0.272 |
| `luminosity` | 0.446 / 0.416 | 0.551 / 0.524 | 0.425 / 0.395 | 0.367 / 0.333 | 0.544 / 0.520 | 0.223 / 0.195 |
| `theory_ew` | 0.405 / 0.355 | 0.468 / 0.426 | 0.401 / 0.339 | 0.301 / 0.273 | 0.470 / 0.416 | 0.225 / 0.157 |
| `theory_qcd` | 0.327 / 0.305 | 0.356 / 0.336 | 0.320 / 0.298 | 0.324 / 0.315 | 0.279 / 0.254 | 0.175 / 0.162 |
| `bcQuarkMass` | 0.358 / 0.259 | 0.367 / 0.275 | 0.338 / 0.246 | 0.308 / 0.266 | 0.348 / 0.235 | 0.196 / 0.145 |
| **σ(α_s)** | **1.158** | 1.290 | 1.085 | 1.062 | 1.217 | 0.690 |
| Σ_quad global (partition†) / σ | 1.047 (no stat) | 1.112 (no stat) | 1.019 | 1.316 (no stat) | 1.012 | 1.018 |

\* The lattice term is not a global-impact source (caveats above). † Partition: stat, binByBinStat, experiment,
pdfEig, resumTNP, resumNonpert, resumScale, resumTransition, theory_ew, theory_qcd, bcQuarkMass, widthZ,
sin2thetaZ, massShift, CMS_background. Rows with global stat = NaN skip it, so they are lower bounds. That these
still exceed 1 says the partition is not exactly disjoint.

![LATL4ZWALLCOLD global grouped α_s impacts](impacts_LATL4ZWALLCOLD/global_impacts_grouped_alphaS.png)
*Global grouped impacts for LATL4ZWALLCOLD, made with the same command as the 260917 walled plots. "Data stat." shows
0.00 because the stored value is NaN. The lattice term is not an impact source. The old walled plot is at
`../../scetlib-ad-param-model/260917-cachecorr-physics/impacts_walled/global_impacts_grouped_alphaS.png`.*

**Read, walled.**
- **α_s does not move:** +0.01σ vs the like-for-like cold walled fit, +0.32σ vs the deepest old walled fit.
- **σ(α_s) shrinks by 10 %** vs CCWALLCOLDR (1.158 vs 1.290) but is 7 % above CCWALLWARM (1.085).
- **Where the lattice moves the fit:** the new walled fit sits in the same basin as the old walled ones. The markers
  agree to ≲0.3 except resumTNP_b_qg (−0.16 vs −0.8). The model-θ distance is 1.2 to both, against 0.3 between the
  two old walled fits.
- **The lattice moves the CS kernel** off the wall, from λ2_ν ≈ 0.005 (railed) to 0.063 ± 0.023, which is 2.3σ
  below the lattice. The CS NP impact collapses: `scetlibNPgammaNu` trad 0.52–0.82 → 0.05.
- **In exchange, the TMD side** now carries the NP dependence (`scetlibNPFeff` trad 0.78). L2 at |Y| = 2.5 sits on the
  wall margin (+0.0046), so the TMD small-b condition is what the wall is holding.
- **The price** is Δχ²_data = +5.0 (vs cold) / +4.7 (vs warm) and a worse ptll projection (80.9/39, against
  72.3 / 70.4).

### 2. Unwalled rows

| | **LATL4ZUNWWARM** (warm: seeded from the LATL4ZWALLCOLD minimum) | LATL4ZUNWCOLD (cold) | CCKRYLOVWARM (old, main min., warm) | CCCOLDSELF (old, cold 2nd min.) |
|---|---|---|---|---|
| NLL | **375.5339** | 382.4312 | 365.4881 | 379.2001 |
| EDM / iterations / negative eigenvalues | 3.6e-16 / 17 / 0 | 6.3e-7 / 1486 / 0 | 3.2e-15 / 31 / 0 | 4.5e-10 / 42 / 0 |
| ln(data) / lc / lext | 354.478 / 20.065 / 0.991 | 362.378 / 19.676 / 0.378 | 348.250 / 17.238 / — | 353.338 / 25.862 / — |
| Δχ²_data vs CCKRYLOVWARM / vs CCCOLDSELF | +12.5 / +2.3 | +28.3 / +18.1 | 0 / −10.2 | +10.2 / 0 |
| Δχ²_data vs CCWALLCOLDR / vs CCWALLWARM(PF) | +4.0 / +3.7 | +19.8 / +19.5 | | |
| full saturated, p (raw; with −2·lext) | 751.07/778, 75.0 %; 749.09, 76.5 % | 764.86/778, 62.5 %; 764.10, 63.2 % | — | — |
| projected-ptll saturated /39 | **78.71, p = 0.02 %** (sub-fit EDM 6.1e-9) | 94.2, **sub-fit NOT converged (EDM 0.026)** | 55.96, 3.8 % (260917) | — |
| σ(α_s) [1e-3] | **1.163** | 1.062 | 1.217 | 0.690 |
| Δα_s / σ_ref vs CCKRYLOVWARM / CCCOLDSELF | +1.46σ / +9.8σ | −0.88σ / +5.7σ | | |
| Δα_s / σ_ref vs CCWALLCOLDR / CCWALLWARM(PF) | +0.34σ / +0.71σ | −1.87σ / −1.91σ | | |
| Δα_s vs the new walled fit (/σ_walled) | +0.37σ | −2.09σ | | |
| λ2_ν | +0.0905 ± 0.029 (−1.41σ from the lattice, χ²_lat 2.0) | +0.107 ± 0.025 (−0.87σ) | −0.091 | −0.083 |
| λ2 / λ4 / δλ2 (TMD) | **−0.078 ± 0.083** / +0.096 / −0.0095 | +0.052 / −0.00003 / −0.0133 | +0.273 / +0.203 / −0.007 | +0.374 / −0.018 / −0.003 |
| TMD damping | **FAIL**: L2 = −0.078 at \|Y\|=0 and −0.138 at 2.5 (small-b anti-damping, F_eff up to ~1.1 at \|Y\|=2.5); large-b ok | **FAIL**: L2(2.5) = −0.031, large-b(2.5) −0.0001 | ok | large-b FAIL |
| CS damping | ok | ok | λ2_ν < 0 FAIL | λ2_ν < 0 FAIL |
| basin markers lumi / b_qqV / pdfEig14 / b_qg / pdfEig23 | −1.64 / −0.48 / −0.45 / −0.63 / −0.38 (the walled basin) | −0.46 / −0.41 / −0.13 / +0.97 / −0.08 | −1.07 / +0.05 / −0.18 / −0.82 / −0.13 | +0.89 / +1.91 / +1.53 / −0.19 / +0.09 |

Grouped impacts for LATL4ZUNWWARM [1e-3, trad / glob]:
- pdfEig 0.767 / 0.703; resumTNP 0.719 / 0.495; resumNonpert 0.969 / 0.067;
- scetlibNPFeff 0.844 / 0.067; scetlibNPgammaNu 0.200 / 0.000* (lattice term not a global source);
- resumScale 0.309 / 0.127; stat 0.840 / 0.188; binByBinStat 0.159 / 0.242; experiment 0.546 / 0.494;
- luminosity 0.468 / 0.439; theory_ew 0.431 / 0.372; theory_qcd 0.337 / 0.316; bcQuarkMass 0.356 / 0.261;
- **σ 1.163**. The global partition sums to 1.018 σ.

Plots: `impacts_LATL4ZUNWWARM/`. (evidence: `logs/analyze_all.log`, `logs/grouped_impacts.log`,
`logs/delta_as_lattice_arms.txt`)

**Read, unwalled.**
- **The warm start confirms the multi-basin picture.** Seeded from the walled minimum, the unwalled fit reaches
  375.53. That is 6.9 below the cold unwalled 382.43, so the cold unwalled fit landed in a worse local minimum, in a
  different basin (b_qg +0.97 against −0.6 to −0.8 everywhere else). It is 1.19 below the walled 376.72: removing the
  wall buys 1.19.
- **It buys it by taking the TMD unphysical,** λ2 = −0.078 < 0, i.e. anti-damping at small b_T at every rapidity.
  The significance is only ~1σ (±0.083), but the fit does walk there once the wall is off. This is the same rerouting
  260911 found with the 2D Tackmann prior: constraining the CS kernel with a lattice term moves the violation into
  the unconstrained TMD boundary condition.
- **α_s is stable across the physical and near-physical lattice fits:** warm unwalled vs walled +0.37σ, and within
  0.34–0.71σ of the old walled fits. The cold unwalled fit is the outlier (−2.1σ vs walled), consistent with its
  being a worse, different basin.
- σ(α_s) is 1.16 in both good lattice fits, against 1.22 for the old unwalled main minimum.
- The CS kernel stays physical and near the lattice in every lattice fit: λ2_ν 0.063 / 0.091 / 0.107, i.e. −2.3σ /
  −1.4σ / −0.9σ.

![Postfit CS kernels in kernel space vs the ASWZ lattice](kernel_space_postfit.png)
*The full CS kernel γ_ζ(b_T, μ=2 GeV) = SCETlib pert (n_f=5) + ½γ_ν^NP(postfit λ). Lattice points are shifted by the
λ4_ν=0 fit's k̂1 = 0.21. The blue band is the λ4_ν=0 ASWZ fit (dark: stat, light: stat+syst). Postfit bands are
68 % from each fit's postfit CS covariance only (they ignore CS–TMD correlations). Blinded fits: nothing here depends
on α_s.*

![NP form factors, postfit](np_forms_postfit.png)
*γ̃_ν^NP (left) and F_eff at |Y| = 0 and 2.5 (right), via `np_function_plots.plot_np_functions`. Bands are 68 % of
400 Gaussian toys of each fit's postfit NP covariance. The unwalled lattice fit's F_eff at |Y|=2.5 rises above 1,
i.e. anti-damps.*

---

## Findings

1. **The production AD cache (pdf62_corrgrid_260827, authval b66f8de) cannot be evaluated for λ4_ν ≲ −0.002.**
   Low-qT σ is off by O(1) from the linear response and AD ≠ FD. σ < 0 from λ4_ν ≈ −0.007. At −0.001 it is still
   clean (3e-4). This is the same failure as the Q-split cache, so it is a property of the cached b_T rules, not of
   one build. Any fit that lets λ4_ν go negative (unwalled, or a lattice constraint centred at −0.006) is unsafe on
   it. — (evidence: `logs/probe_l4nu.log`, `probe_l4nu_ratio.png`) *Generalises → knowledge
   (negative-λ4 trap, AD-cache version).*
2. **The τ=5 wall is softer than the ASWZ lattice term along λ4_ν** (curvature 4.4e4 vs 6.25e4 marginal). Ignoring the
   data, wall + lattice balance at λ4_ν ≈ −0.0015. So the wall does not by itself guarantee λ4_ν ≥ 0 under this
   constraint. — (evidence: arithmetic in Log; wall constants in `np_damping_wall.py:222-223`)
3. **ASWZ constraint including systematics:** λ2_ν = 0.1844 ± 0.0567, λ4_ν = −0.0059 ± 0.0040, ρ = −0.911.
   Stat-only it is ± 0.0383 / 0.0033, ρ −0.883. The k-form choice dominates the systematic. The card anchor
   (0.15, 0) is at χ²_lat = 5.4 on 2 dof. — (evidence: `logs/inject_statsyst.log`)

---

## Open questions

- Which λ4_ν ≥ 0 guard to use for the unwalled arm (orchestrator's call; not improvised here). Options seen so far:
  freeze λ4_ν = 0 and put a 1D conditional lattice constraint on λ2_ν; a hard bound; or a CS-only wall.
- Does LATWALLCOLD land at λ4_ν ≥ −0.001? If it does not, its numbers are cache artefacts (Finding 2).
- Is the orchestrator's premise right? The brief says the Q-split cache, not the production one, was the problem
  for λ4_ν < 0. The production cache has the same pathology (Finding 1).
- The other session's y35 jobs reached ~640 GB RSS each (MemAvailable 13 GB at 17:22). Worth flagging to whoever
  owns 260923-y35-fit-prep before anyone runs two lattice fits at once (~185 GB peak each).
