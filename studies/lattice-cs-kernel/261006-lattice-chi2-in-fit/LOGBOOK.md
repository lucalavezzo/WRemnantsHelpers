---
title: Exact lattice chi2 inside the alpha_s fit
slug: 261006-lattice-chi2-in-fit
study: lattice-cs-kernel
status: done          # active | done | paused | abandoned
created: 2026-10-06
updated: 2026-10-07
owner: study-worker
---

# Exact lattice chi2 inside the alpha_s fit

**Task:** If the 2D Gaussian summary of the ASWZ lattice CS-kernel constraint is replaced by the exact lattice chi2 (a rabbit regularizer, k1 profiled), where does the walled Z fit (NOMSTIFF config + free lambda4_nu) land, and how do alpha_s and the NP lambdas move?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-10-07 15:00)

> **DONE (phases 1–3).** The exact ASWZ lattice χ² is inside the α_s fit as a rabbit `-r` regularizer: WRemnants
> **3ef3efb9** (phase 3; phase 2 was 44f8a5c0), `wremnants/postprocessing/scetlib_ad/lattice_cs_chi2.py`, pushed (origin/scetlib-ad-param-model).
> - k1 is profiled analytically.
> - The systematics are a covariance (default n_f + b_T window; k-form and μ0 scale opt-in only).
> - `pert=live` makes the perturbative kernel follow α_s and the CS-kernel TNPs (resumTNP_gamma_nu, gamma_cusp), with
>   maps read from the param model.
> **Nominal LATFULL8 (`syst=Jnf+Jbt pert=live`) vs NOMSTIFF: Δ`alphaS` = −0.09σ_NOM, σ ratio 0.979,** λ4_ν +0.0098
> (interior), λ2_ν 0.036. The CS TNPs gain no constraint from the lattice (θ_γν 0.44 → 0.31, σ stays 1.01).
> **Checks:**
> - blinding A–E exact (α_s and TNP sources);
> - Asimov closures of `pert=alphas` and `pert=live` PASS (|θ| ≤ 3e-7 / 6e-10);
> - direct_nf vs Jnf: 0.007σ (Newton), no fit needed.
> Real data, `alphaS` blinded (differences only).

- **Fits** (ceph `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261006_lattice_chi2_in_fit/`):
  - LATCHI8 (phase 1);
  - LATLIVE8Y (phase 2, α_s live);
  - **LATFULL8** (phase 3, fully live).
  - Checks: BLINDCHK, BLINDFULL, ASIMLIVE2, ASIMFULL, SUBCHK8B.
  - Nothing of this task is running; all chains have ended (chain7 log: "all stages done").
- **Next action:** none for this task. For Luca to decide:
  - push 3ef3efb9;
  - the default n_f form (Jnf vs direct_nf; equivalent for α_s);
  - the b_T window (theorist);
  - retiring the 1D/2D Gaussian cards, which still carry the k-form systematic.
- **Blocking on:** nothing.

---

## Log

<!-- Newest first. What was tried, what happened, why — with an evidence path. -->

### 2026-10-07 14:50 — LATFULL8 done; phase-3 comparison
- LATFULL5 exit 0 at 14:16; LATFULL8 exit 0 at 14:48, EDM 1.2e-17. chain7 skipped LATDNF (no flag) and ended.
- `compare.py` now records the TNP pulls (`tnps`). Result §7; [kernel_space_LATFULL8.png](kernel_space_LATFULL8.png).

### 2026-10-07 11:50–13:30 — phase 3: plugin `pert=live` (3ef3efb9), direct_nf Newton, BLINDFULL + ASIMFULL PASS, LATFULL
- See Result §7. Commands: `scripts/build_cmds3.py` → `cmds/{BLINDFULL,ASIMFULL,LATFULL5,LATFULL8,LATDNF5,LATDNF8}.cmd`
  (diffs in [logs/build_cmds3.log](logs/build_cmds3.log)). Seeds: `seeds/seed_LATLIVE8Y_flat.hdf5`,
  `seeds/seed_ASIMFULL_displaced.hdf5`.
- `blindcheck.py` gained check E (TNP source identity + AD = FD) and takes the command file as an argument.

### 2026-10-07 10:40 — SUBCHK PASS; LATLIVE5Y/8Y done; comparison
- SUBCHK8B: NLL(subset cache) − NLL(LATCHI8, full cache) = **+0.000e+00** ([logs/subchk.log](logs/subchk.log)).
- LATLIVE5Y: exit 0 at 10:08, 25 iterations. LATLIVE8Y: exit 0 at 10:32, EDM 2.1e-17. Both logs show "Gaussian priors
  on 44" and the live arming line. Result §6 B5.
- `compare.py` now has frozen-table lattice columns for live fits (kind `none`).
  [compare.json](compare.json) holds NOMSTIFF / LATCHI8 / LATLIVE5Y / LATLIVE8Y; the phase-1 version is
  [compare_phase1.json](compare_phase1.json).

### 2026-10-07 09:40 — SUBCHK8 restarted as SUBCHK8B (`--noEDM`); chain6
- SUBCHK8 (`--noFit --noHessian`) loaded the subset cache (≈20 min from ceph) and then sat in the postfit EDM
  conjugate-gradient solve. CG is slow on this 3720-parameter blinded problem, and it is not needed for an NLL replay.
  My design error. I stopped chain5 (PID 4144822) and SUBCHK8 (rabbit_fit 4145994), both mine.
  - A first `kill $(pgrep -f …)` matched my own shell (the pkill self-match pitfall) and killed only that shell.
    Retried with explicit, verified PIDs; nothing else was touched.
- Relaunched as **SUBCHK8B** (`--noFit --noHessian --noEDM`, allowed with `--externalPostfit` and no fit) under
  **chain6** (`scripts/chain6.sh` = chain5 with that one change; [logs/chain6.log](logs/chain6.log)).
  The gate showed `alive 1/2` (another worker's job).

### 2026-10-07 09:05 — Asimov closure PASS (overnight false-fail); LATLIVE on the |Y| ≤ 2.5 subset cache (chain5)
- **The overnight "Asimov closure FAILED" (chain4, 18:59) was a script bug, not physics.** `asimov_check.py` called
  `get_fitresult(path, None)`, which looks for `results_asimov`, but a `-t 1` toy is stored as `results_toy1`, so the
  script raised. The fix is `get_fitresult(path, "toy1")`. The orchestrator's scratch rerun and my regenerated
  [asimov_closure.json](asimov_closure.json) are identical.
- **Asimov closure (ASIMLIVE2: live term, `syst=Jnf+Jbt+pert`, `ydata=asimov`, τ = 8): PASS.**
  - Start: α_s θ +1 (α_s 0.120), λ2_ν θ −0.5, λ4_ν θ +0.01.
  - Every θ returns to the truth 0 within |θ| ≤ 2.7e-7 (α_s 0.11800000053; Asimov, so absolute values are fine).
  - EDM 1.4e-13, NLL −2.5e-10, 62 iterations.
  - This closes the live α_s path end to end. A term reading the wrong α_s, or the wrong sign, would not return
    α_s to 0.118.
- chain4 stopped there, as it should have, so LATLIVE5/8 on the full cache never ran.
- **chain5** (`scripts/chain5.sh`, [logs/chain5.log](logs/chain5.log)) runs on the orchestrator's new |Y| ≤ 2.5
  subset cache `ad_scetlib_caches/pdf62_y35_260921_y25` (242 GB, exact for card A; mem_gate budget 260 via `GATE_GB`):
  - **SUBCHK8:** LATCHI8's own command on the subset cache, `--noFit --noHessian` at LATCHI8's vector. Its NLL must
    equal LATCHI8's to < 1e-6, else the chain stops. It also cross-checks the v2 plugin (`syst=J`) against the v1 one
    LATCHI8 ran.
  - **LATLIVE5Y → LATLIVE8Y:** the LATLIVE commands with only the cache paths changed (postfix suffix Y = subset).
- Commands: `cmds/{SUBCHK8,LATLIVE5Y,LATLIVE8Y}.cmd`, cache-path-only diffs vs LATCHI8 / LATLIVE5 / LATLIVE8.

### 2026-10-06 17:15–17:50 — blinding check PASS; Asimov via -t -1 is unusable; chain4
- BLINDCHK ([logs/BLINDCHK.log](logs/BLINDCHK.log)): fitter on data with blinding armed, at LATCHI8's vector:
  - **A** α_s(term) − α_s(param model) = **+0.000e+00** (exact).
  - **B** the term's α_s differs from the map on the blinded internal `Fitter.x` when armed (True), and equals it when
    disarmed (True). So the term reads the offset-applied physical frame, not x.
  - **C** autodiff vs FD of the term in x[alphaS]: 1.4e-9.
  - **D** ∂α_s(model)/∂x = 0.002 = the term's slope.
  - Map: the param model's own (0.118 + 0.002θ), identical to the correction-runcard map.
- **The code path** (rabbit 2a59246):
  - `Fitter._compute_yields_noBBB` hands the model `concat(get_poi(), get_model_nui())`.
  - `_compute_nll_components` hands every regularizer `get_x() = concat(get_poi(), get_model_nui(), get_theta())`.
  - `get_poi()` = `blinding.apply_poi(x[:npoi])`, i.e. x + offset when armed.
  - The plugin then applies `SCETlibADParamModel._rp_c[:, alphaS]` (read in `set_expectations` from
    `fitter.param_model`) to `params[i_alphaS]`. So it is the same tensor and the same map as the model's.
- ASIMLIVE (`-t -1`) is **not a result**: `bin/rabbit_fit.py` sets `dofit = ifit >= 0`, so it only evaluated the truth
  point and was then stuck in the postfit EDM CG. I stopped chain3 and then that job (both mine). Redone as ASIMLIVE2
  with `-t 1 --toysDataMode expected --toysDataRandomize none --toysSystRandomize none`, which is minimised and
  unblinded (blinded_fits only for observed-mode toys).

### 2026-10-06 17:12 — phase 2: plugin committed (WRemnants 44f8a5c0), D table, chain3 launched
- Orchestrator / Luca: (A) move the plugin into WRemnants; (B) α_s-live done under blinding, plus a pert-kernel scale
  systematic; (C) keep the systematics as a covariance; (D) Newton table for dropping systematics; then: drop the
  k-form systematic (default `Jnf+Jbt`). Results: Result §6.
- chain3 (`scripts/chain3.sh`, log [logs/chain3.log](logs/chain3.log)) runs BLINDCHK → ASIMLIVE → LATLIVE5 → LATLIVE8
  strictly one at a time through mem_gate (400 GB; at most 2 gated jobs node-wide). Commands:
  `scripts/build_cmds2.py` → `cmds/{BLINDCHK,ASIMLIVE,LATLIVE5,LATLIVE8}.cmd`, diffs in
  [logs/build_cmds2.log](logs/build_cmds2.log). Seeds: `seeds/seed_LATCHI8_flat.hdf5` (LATCHI8's vector, no cov) and
  `seeds/seed_ASIM_displaced.hdf5` (all θ = 0 except alphaS +1, λ2_ν −0.5, λ4_ν +0.01).

### 2026-10-06 16:05 — LATCHI8 done; comparison and kernel plot
- LATCHI5R: exit 0 at 15:20 (38 iterations, loss 375.45449). The chain2 watcher launched LATCHI8 at 15:21 (gate 400 GB,
  1330 GB available).
- LATCHI8: exit 0 at 15:50, EDM 3.09e-17. The log shows "Gaussian priors on 44", the wall armed 6/8, and the lattice term
  armed with the live τ = 8.
- `compare.py` gained a reader for flat snapshots, so T8's last T8C5 snapshot can be shown for orientation (T8 is closed,
  with no converged fit). Output [compare.json](compare.json) → Result §5.
- [kernel_space_LATCHI8.png](kernel_space_LATCHI8.png) → Result §5.

### 2026-10-06 14:30 — reboot recovery: LATCHI5R launched + chain2 (orchestrator / Luca: resume)
- LATCHI5 was SIGKILLed at 13:14 (exit 137) in a node memory overload, and the node rebooted at about 13:50.
  - Its log shows iteration 11 (loss 375.9503) at about 12:28 and then nothing until the kill, so it had stalled
    (memory pressure).
  - The 12:24 `fitresults_LATCHI5.hdf5` on ceph is not a result: the fit never finished. It is left in place and not
    used.
  - chain.sh died with the node.
- The last periodic snapshot is from 12:45: iteration 11, loss 375.9647, 3720 params. It was frozen as
  `seeds/seed_LATCHI5_snapshot_1245.hdf5`.
- `build_cmds.py` gained the stage LATCHI5R. It is LATCHI5 with only the postfix, the snapshot file and
  `--externalPostfit` changed (token diff in [logs/build_cmds_1430.log](logs/build_cmds_1430.log)). LATCHI8 now warms
  from fitresults_LATCHI5R. LATCHI5.cmd was regenerated byte-identical.
- Launched LATCHI5R through mem_gate at 400 GB (1262 GB available, slot 1). New watcher `chain2.sh`, PID 95819.

### 2026-10-06 12:40 — LATCHI8 gate raised to 400 GB (orchestrator)
- The node OOM-killed three fits between 12:05 and 12:23, while LATCHI5 was loading alongside others. LATCHI5 survived:
  PID 43883 was alive and iterating at 12:31.
- `scripts/launch.sh`, which the chain watcher calls for LATCHI8, now gates at 400 GB instead of 330. It also refuses to
  launch while any LATCHI* rabbit_fit of this task is alive, so this task has at most one cache load at a time.
- `chain.sh` itself was NOT edited: it is running (PID 4069958), and bash reads a running script incrementally. It
  invokes `launch.sh` fresh at LATCHI5's exit, so the change applies to LATCHI8.
- Nothing else changed: `alphas=frozen` stays (Luca has not decided on live).

### 2026-10-06 12:07 — LATCHI5 launched (rabbit_fit PID 43883)
- The gate waited 62 min for memory (three T8 fits and TCC1 held about 1.2 TB).
- Run header: WRemnants a008faa5 (clean), rabbit 2a59246 (clean), scetlib 2dd978a, plugin md5 dbaae121…, inputs md5 bde9d60f….
- Arming lines verified (START HERE). Iteration 0 loss 376.611. Snapshots go to the ceph dir every 0.25 h.
- `compare.json` currently holds only the NOMSTIFF / XWSTIFF test rows of `compare.py`. These are the NLL split
  references: NOMSTIFF data+BB 354.908, priors 19.182, 1D lattice 2.525, wall 7e-6.

### 2026-10-06 11:20 — cache-free Newton prediction (`scripts/newton.py` → [newton.json](newton.json))
- Same construction as T8's step 2. It re-uses T8's stored HVP column along λ4_ν and the gradient at NOMSTIFF (read-only,
  `261006_t8_l4nu_lattice2d/l4nu_hvp_column_at_NOMSTIFF.npz`). The 2D card term is swapped for the EXACT term (gradient
  and Hessian by finite differences, θ units).
- **Prediction:** λ4_ν = +0.0036 (interior), λ2_ν 0.064 → 0.041, **Δ`alphaS` = −0.09σ_NOM**, σ ratio 1.002,
  ΔNLL −1.41, Δχ²_lat at the predicted point 6.6.
- T8's Gaussian version predicted −0.10σ, λ2_ν 0.035, λ4_ν 0.0037. The exact-term curvature along λ4_ν is larger
  (1.30e5 vs 0.92e5 θ⁻²), which offsets its stronger pull. A quadratic estimate from one point: the fit is the measurement.

### 2026-10-06 11:05 — LATCHI5 queued (gate PID 4069841), chain watcher PID 4069958
- Commands built by `scripts/build_cmds.py` from NOMSTIFF's OWN meta_info command; token diff in
  [logs/build_cmds.log](logs/build_cmds.log). Changes: card → plain card A; `fit_params` += `lambda4_nu`;
  `prior_sigmas=lambda2_nu=nan,lambda4_nu=nan,lambda2=1,lambda4=1,delta_lambda2=1`; a second
  `-r lattice_cs_chi2.LatticeCSChi2 lattice_cs_chi2.LatticeCSMapping syst=J offset=min alphas=frozen inputs=<npz>`
  next to NOMSTIFF's `NPDampingWall margin=0`; τ 8 → 5 (stage 1, `--noHessian --noEDM`). Stage 2 = τ 8 with Hessian/EDM.
  Main rabbit tree (2a59246, clean), as NOMSTIFF.
- Seed: `seeds/seed_A_NOMSTIFF_l4nu0.hdf5`, copied (md5 6fbe403b…) from T8's ceph dir; `build_cmds.py` re-checks it is
  NOMSTIFF's vector bit-for-bit plus λ4_ν θ = 0 (3720 params, no covariance).
- Dry run (`scripts/dryparse.py`): rabbit_fit's own parser takes the command, 2 `-r` entries, both regularizers load on
  card A, card carries no external term.

### 2026-10-06 11:00 — step 2: closure and exact-vs-Gaussian Δχ² (`scripts/closure.py` → [closure.json](closure.json), [closure.txt](closure.txt))
- The TF regularizer minimised ALONE (BFGS on θ, card A θ map, λ∞_ν held 2) reproduces the separate fit to all printed
  digits for every syst mode; see Result §2.
- Exact vs Gaussian Δχ² at the reference points: Result §3. α_s / TNP sensitivity of the frozen pert table: Result §4.

### 2026-10-06 10:55 — step 1: the term (`scripts/build_inputs.py`, `scripts/lattice_cs_chi2.py`, `scripts/test_lattice_cs_chi2.py`)
- Frozen inputs [lattice_aswz_inputs.npz](lattice_aswz_inputs.npz) (+ [.json](lattice_aswz_inputs.json)): 21 points, the
  block-diagonal covariance, the n_f = 5 pert table (identical to `260923-scetlib-kernel-fit/pert_tables.npz` to 1e-12), the
  three systematic shift vectors, dpert/dα_s and dpert/dTNP.
- Unit tests [test_lattice_cs_chi2.txt](test_lattice_cs_chi2.txt): **13/13 PASS** (pert table and full model vs
  `our_cs_kernel.py` to 2e-16; analytic k1 profile vs `kernel_fit.chi2_at` to 3e-16 at six tunes; lattice-only minimum;
  Woodbury identity; TF value and gradient; τ compensation; α_s-live mode).
- Lint: container black + isort (profile black) clean; flake8 with WRemnants' CI selection (F-codes) clean.
- One test initially "failed" by design error, not by the code: the exact-χ² Hessian σ is 2–5 % larger than the
  Gauss–Newton σ the card term uses (second-order residual term of the tanh). The test now compares like with like
  (GN vs GN, 3e-6) and prints the exact-Hessian ratio.

### 2026-10-06 10:50 — setup
- Read AGENTS.md, the study START HERE, 260923-conventions-map / -lattice-data-refit / -scetlib-kernel-fit / -lattice-fits,
  walled-multistart-census (10-06) and its T8 task (Gaussian-summary version, fits running: T8B, T8C5, T8P5).
- rabbit facts that shape the design (rabbit 2a59246 = the tree NOMSTIFF ran on, clean):
  - `-r` is `nargs="+", action="append"`: several regularizers compose; `_compute_nll_components` sums their penalties.
  - **Every regularizer penalty is multiplied by `exp(2 tau)`** (one common `fitter.tau`, `--regularizationStrength`).
    A lattice ½χ² added via `-r` would be scaled by exp(16) = 8.9e6 at τ = 8. The plugin must divide it back out.
  - Penalties are not stored in the fitresult: the NLL split has to be recomputed from the end-point vector.
  - A regularizer cannot own extra fit parameters (the parameter vector is the card + ParamModel), so k1 is profiled
    analytically inside the term.
- Card check: card A `260916_Z_2D_card_adcorr/.../ZMassDilepton.hdf5` md5 013135fa… unchanged since 09-23; NOMSTIFF's card
  `cardA_latticeASWZ_l4zero_statsyst.hdf5` = card A + the `external_terms/lattice_cs` group and nothing else
  (`../260923-lattice-fits/logs/diffcards_l4zero_statsyst.log`).
- Cache `pdf62_y35_260921/merged_full_bin0xzero`: α_s(m_Z) = 0.118 at n3ll, tanh_2 / tanh_2, anchors λ2_ν 0.15, λ4_ν 0,
  λ∞_ν 2 (frozen) — the same α_s convention as the 260923 kernel fit.

---

## Result

### Caveats first (apply to everything below)
- **Lattice side:** block-diagonal ASWZ covariance (author-confirmed adequate, 2026-09-29); tanh_2, λ∞_ν = 2 frozen; our
  pert kernel n_f = 5, N3LL, α_s(m_Z) = 0.118 (the lattice is n_f = 4: carried as the n_f systematic group). The
  systematic covariance is a modelling choice (below), not a lattice-provided number.
- **"Exact"** means the full tanh model χ² with k1 profiled; the systematic part is still a covariance built from
  variant-fit shifts (as in the summary term). The exact χ² is therefore exact in the λ dependence, not in the
  systematics.
- **The Gaussian comparison terms** are the existing cards: 2D = `cardA_latticeASWZ_statsyst` (T8's), 1D =
  `cardA_latticeASWZ_l4zero_statsyst` (NOMSTIFF's). All Δχ² are against each term's own minimum.

### 1. The plugin: `scripts/lattice_cs_chi2.py`
`-r lattice_cs_chi2.LatticeCSChi2 lattice_cs_chi2.LatticeCSMapping [syst=J|direct_nf|none] [offset=min|<float>] [alphas=frozen|live] [inputs=<npz>] [tau=<float>]`
- **What it adds:** ½(χ²_lat − χ²_min) to the NLL, with χ²_lat = min_k1 rᵀC⁻¹r and
  r_i = γ_pert(b_i) + ½γ_ν^NP(b_i; λ∞_ν, λ2_ν, λ4_ν[, λ6_ν]) + k1·a_i/b_i − y_i over the 21 ASWZ points. These are the
  conventions of `260923-scetlib-kernel-fit/kernel_fit.py` (NP at bare b_T; γ_q ≡ γ̃_ζ = ½Γ_ν).
  χ²_min = 6.713 is the lattice-only minimum at λ∞_ν = 2, so the term is ½Δχ²: zero at the lattice best fit, like the
  Gaussian terms it replaces.
- **k1: profiled analytically.** A rabbit regularizer cannot own fit parameters, but the term is quadratic in k1:
  χ² = r0ᵀ M r0 with M = W − (Wv)(Wv)ᵀ/(vᵀWv), W = C⁻¹, v = a/b. This is identical to a free k1 parameter: same
  minimum, and the curvature in the other parameters is the k1-marginal (Schur complement). k̂1 = −vᵀW r0 / vᵀWv is
  reported offline at each end point.
- **Systematics (`syst=J`, default):** the same three groups and the same chosen variants as the 2D card term:
  - n_f scheme: n_f = 5 matched at μ = 1 GeV;
  - k-form: k2 only;
  - b_T window: drop b_T < 0.2 fm.

  Each chosen parameter shift d_g = (Δλ2_ν, Δλ4_ν) is mapped onto the points with the NP Jacobian at the lattice best
  fit, δ_g = J_NP·d_g. Then C = C_stat + Σ δ_g δ_gᵀ.
  - Why this form: by Woodbury, (Jᵀ(V + JSJᵀ)⁻¹J)⁻¹ = (JᵀV⁻¹J)⁻¹ + S. So the profiled (λ2_ν, λ4_ν) covariance is exactly
    the card term's stat+syst covariance (verified to 3e-6), and the minimum and χ²_min do not move. Away from the
    minimum the term stays the full tanh χ².
  - `syst=direct_nf` puts the n_f group in as the direct point shift pert(n_f 5 at μ=1) − pert(n_f 5). It moves the
    minimum by 0.06σ (Result §2).
- **α_s:** `alphas=frozen` (default; like-for-like with the card terms, which have no α_s dependence). `alphas=live`
  adds the linear response (α_s − 0.118)·∂γ_pert/∂α_s. It reads the POI from `get_x()`, which is the physical,
  offset-applied value the model itself uses, so it is blinding-consistent and never printed. It is tested, but
  not used in the nominal fit; see §4.
- **The exp(2τ) trap:** rabbit multiplies every regularizer penalty by exp(2τ) (8.9e6 at τ = 8). The term divides it
  back out with the live `fitter.tau` variable, which it finds on the call stack at `set_expectations`. A `tau=` on the
  -r line is cross-checked against it, and a mismatch raises.
- **θ → physical:** the same map as NPDampingWall (`resolve_wall_inputs`: REPARAM width + correction anchor). The CS λ
  are resolved by name; λ∞_ν is held at its anchor (2).
- **Tests:** [test_lattice_cs_chi2.txt](test_lattice_cs_chi2.txt), 13/13 PASS.
- **Lint:** container black + isort clean; WRemnants CI flake8 selection clean.

### 2. Closure: the term minimised alone reproduces the separate lattice fit

| | χ²_min (ndf 18) | λ2_ν | λ4_ν | k̂1 | σ(λ2_ν), σ(λ4_ν), ρ — Gauss–Newton | same — exact-χ² Hessian |
|---|---|---|---|---|---|---|
| 260923 separate fit (`tanh2 \| linf=2 \| k1`) | 6.713 | 0.18443 | −0.00592 | 0.241 | 0.0383, 0.00325, −0.883 (stat) | – |
| term, `syst=none` | 6.713 | 0.18443 | −0.00592 | 0.241 | 0.0383, 0.00325, −0.883 | 0.0391, 0.00341, −0.888 |
| term, **`syst=J` (nominal)** | 6.713 | 0.18443 | −0.00592 | 0.241 | **0.0567, 0.00400, −0.911** = card 2D term | 0.0575, 0.00419, −0.914 |
| term, `syst=direct_nf` | 6.696 | 0.18673 | −0.00602 | 0.236 | 0.0570, 0.00401, −0.910 | 0.0578, 0.00420, −0.913 |

- Minimised in θ by BFGS through the TF graph rabbit uses: |∇| ≤ 3e-6.
- The exact-χ² Hessian is 2–5 % softer than Gauss–Newton. That is the tanh non-linearity at the minimum (second-order
  residual term), and is exactly what a Gaussian summary cannot carry.

### 3. Exact vs Gaussian Δχ²_lat at the reference points (λ∞_ν = 2)

| point (λ2_ν, λ4_ν) | exact, stat+syst (`J`) | exact, stat only | Gaussian 2D card (stat+syst) | Gaussian 2D, stat only | Gaussian 1D l4zero (NOMSTIFF's card) | k̂1 (J) |
|---|---|---|---|---|---|---|
| NOMSTIFF (0.0643, 0) | **7.17** | 17.10 | 5.69 | 13.93 | 5.05 | 0.19 |
| T8 Newton point (0.0351, 0.0037) | **7.58** | 18.45 | 6.95 | 16.28 | – | 0.18 |
| XWSTIFF = W (−1e-6, 0.0444) | **24.98** | 34.38 | **554.96** | 592.92 | – | 0.15 |
| card anchor (0.15, 0) | 2.28 | 2.37 | 5.42 | 5.58 | 0.24 | 0.23 |
| *W − NOMSTIFF* | *+17.8* | *+17.3* | *+549* | *+579* | | |
| *T8 Newton − NOMSTIFF* | *+0.41* | *+1.35* | *+1.25* | *+2.35* | | |

- **At W the Gaussian is 31× too steep (549 vs 17.8),** which confirms the T8 number (+17.3, stat-only) with the systematic
  covariance included. W is still disfavoured by the exact lattice (Δχ² +17.8 against the Z data's 2ΔNLL preference of 1.9).
- **Near NOMSTIFF the Gaussian is roughly right in value** (5.7 vs 7.2). It is wrong in direction: at NOMSTIFF's point
  the exact term pulls λ4_ν up 1.6× harder (∂χ²/∂λ4_ν = −2069 vs −1326 GeV⁻⁴). Its conditional minimum along
  λ2_ν = 0.0643 sits at λ4_ν = +0.0037, against the card's +0.0018. So the combined fit should end at larger λ4_ν than
  T8's Gaussian version predicts.
- The T8 Newton move costs only +0.41 in the exact term against +1.25 in the Gaussian.
- At the card anchor the 2D Gaussian (5.4) over-penalises λ4_ν = 0, compared with the exact 2.3. That is the tanh
  saturation the Gaussian cannot follow.

### 4. α_s and TNP dependence of the frozen pert table (`closure.json` → `sensitivity`)
- ∂γ_pert/∂α_s(m_Z) per point ranges from −3.0 to +2.7. It changes sign with b_T, so it is not a pure offset.
- Linear in α_s to 2e-3 σ_lat per point over ±0.002.
- **At NOMSTIFF's CS point:** ∂χ²_lat/∂α_s = −196. With σ(α_s) = 1.16e-3 that is Δχ² = −0.23 per σ, and a pull on
  α_s of **≈ +0.11 σ** if the term were made α_s-live. This is a first-order estimate, −σ·½∂χ²/∂α_s, using the
  combined covariance. It is the same at the T8 Newton point.
  - **So the α_s dependence is small but not negligible next to the ~0.1σ effects under study.** The frozen table drops
    a ≈ +0.1σ pull that the lattice points would exert through the perturbative kernel. For the same reason the
    Gaussian summary terms (NOMSTIFF, T8) drop it too, so the like-for-like comparison stands.
  - `alphas=live` exists and is tested if Luca wants that variant. It is a physics choice, because it lets the lattice
    data constrain α_s through our perturbative kernel at small b_T.
- **TNPs:** the CS-kernel TNPs at NOMSTIFF's postfit (θ_γν = +0.69, θ_cusp = −0.15) shift the points by ≤ 0.0044
  (≤ 0.05 σ_lat) and change χ²_lat by +0.24. The term holds the pert kernel at TNP = 0, as the summary does.

---

### 5. The nominal fit: exact lattice χ² in the α_s fit (LATCHI8) vs NOMSTIFF

**Caveats first.**
- Real data. `alphaS` is blinded: Δ in units of σ_NOM = σ(`alphaS`) of NOMSTIFF, and σ ratios only. All fits share
  card A, the y35 bin0xzero cache, NOMSTIFF's minimiser and flags, and the same 44 Gaussian priors (TMD priors pinned;
  "Gaussian priors on 44" checked in every log). The NOMSTIFF and LATCHI blinding offsets are the same (same base
  card).
- **The lattice term differs by construction.** NOMSTIFF carries the 1D Gaussian (λ2_ν = 0.1345 ± 0.031, λ4_ν ≡ 0).
  LATCHI8 carries the exact 2D χ² with λ4_ν free. So the "lattice" NLL column compares different terms; the data+BB
  and prior columns are like-for-like.
- σ comes from each fit's stored covariance, which includes the stiff τ = 8 spring on the active face. That is the
  same face for both fits, so the ratio is like-for-like.
- The code tree is WRemnants a008faa5, not NOMSTIFF's.
- LATCHI8 history: LATCHI5 (τ = 5) was SIGKILLed in the node overload. It was resumed from its iteration-11 snapshot
  as LATCHI5R, then run at τ = 8 (LATCHI8). The resume reproduced the snapshot loss exactly.
- The pert table is frozen at α_s = 0.118. At LATCHI8's point an α_s-live term would pull `alphaS` by about
  **+0.08σ** (∂χ²_lat/∂α_s = −140; §4).
- The T8C5 row is a periodic **snapshot** of the T8 Gaussian-2D τ = 5 fit, OOM-killed and reported "essentially
  converged" (iteration 22). It has no EDM or covariance and is not certified. It is shown for orientation only; T8 was
  closed without a converged fit.

| | NOMSTIFF | **LATCHI8** (exact χ², λ4_ν free, τ = 8) | LATCHI5R (same, τ = 5) | T8C5 snapshot (2D Gaussian, τ = 5) | XWSTIFF (no lattice; orientation) |
|---|---|---|---|---|---|
| lattice term | 1D Gaussian, λ4_ν ≡ 0 | exact, `syst=J` | exact | 2D Gaussian card | none (CS priors on) |
| Δ`alphaS` / σ_NOM | 0 | **−0.111** | −0.111 | −0.073 | −0.367 |
| σ(`alphaS`) / σ_NOM | 1 | **0.981** | – (no Hessian) | – | 0.933 |
| EDM | 3e-14 | **3.1e-17** | – | – | 7e-18 |
| λ2_ν | 0.0643 ± 0.023 | **0.0295 ± 0.030** | 0.0295 | 0.0350 | −1e-6 (wall) |
| λ4_ν | 0 (frozen) | **+0.0073 ± 0.0045** (interior) | +0.0073 | +0.0037 | +0.0444 |
| k̂1 (exact term, `J`) | 0.190 | **0.173** | 0.173 | 0.178 | 0.155 |
| TMD λ2 / λ4 / δλ2 | 0.0256 / 0.0876 / −0.0041 | **0.0536 / 0.0866 / −0.0086** | same | 0.0482 / 0.0935 / −0.0077 | 0.119 / −7e-5 / −0.0094 |
| active wall face(s) | L2(\|Y\|=2.5) = 0 | **L2(\|Y\|=2.5) = 0** | same | same | λ2_ν = 0, B(\|Y\|=2.5) = 0 |
| NLL total | 376.615 | **375.455** | 375.454 | 375.785 (2D card) | 371.328 (no lattice) |
| data + BB | 354.908 | **353.474 (−1.434)** | 353.474 | 353.663 (−1.245) | 352.568 (−2.339) |
| priors (card + 44 model) | 19.182 | **18.542 (−0.640)** | 18.543 | 18.646 | 18.760 |
| lattice term in the NLL | 2.525 (1D Gauss) | **3.438 (= ½ Δχ²_exact)** | 3.438 | 3.476 (2D Gauss) | 0 |
| wall penalty | 7e-6 | **2e-7** | 8e-5 | 3e-4 | 1e-5 |
| **exact Δχ²_lat (stat+syst)** at the end point | **7.17** | **6.88** | 6.88 | 7.57 | 24.98 |
| exact Δχ²_lat, stat only | 17.10 | 13.07 | 13.07 | 18.41 | 34.38 |
| 2D Gaussian card Δχ² at the end point | 5.69 | 11.35 | – | 6.95 | 555 |

- NOMSTIFF's own point evaluated on LATCHI8's configuration is 376.615 − 2.525 + ½·7.17 = 377.68. LATCHI8 is 2.22 below it.
- Of LATCHI8's 1.16 total gain over NOMSTIFF: the data gain 1.43 and the priors 0.64, and the lattice pays 0.91
  (different terms; see the caveat).
- **The exact lattice χ² is LOWER at LATCHI8 than at NOMSTIFF** (6.88 vs 7.17). Freeing λ4_ν lets the data and the lattice
  agree better at the same time. The 2D Gaussian would have charged this point 11.35, against 5.69 at NOMSTIFF.
- Newton (cache-free, §Log 11:20) predicted λ2_ν 0.041, λ4_ν 0.0036, Δ`alphaS` −0.09σ. The fit went further along the
  λ2_ν/λ4_ν degeneracy (0.030 / 0.0073), and the `alphaS` shift is close to the prediction.

![Kernel space: NOMSTIFF vs the exact-lattice fit LATCHI8, with the ASWZ points](kernel_space_LATCHI8.png)

*Caveats for the figure:*
- The points are the per-ensemble ASWZ values minus k̂1·a/b_T with k̂1 = 0.17, the exact term's profile at LATCHI8's CS
  point. The k1 uncertainty is not in the error bars, and NOMSTIFF's own k̂1 is 0.19.
- Block-diagonal lattice covariance; n_f = 5 pert; λ∞_ν = 2 frozen.
- The postfit bands are 68 % from each fit's CS covariance only (CS–TMD correlations ignored). The hatched blue band is
  the lattice-only stat MCMC band.

**Physics read.**
1. With the exact lattice χ² in place of its Gaussian summary, and λ4_ν floated, the fit finds an interior λ4_ν =
   +0.0073 ± 0.0045. The CS kernel damps less at small b_T (λ2_ν 0.030) and more at large b_T, reaching the λ∞_ν/2 cap
   by about 0.8 fm.
   - Over 0.2–0.6 fm, where the lattice points are precise, it stays on the lattice points: Δχ²_lat = 6.9 above the
     lattice-only minimum for 2 dof, lower than NOMSTIFF's 7.2.
   - The Z data gain 2Δ(data+BB) = −2.9.
   - The 2D Gaussian card would have mis-charged this point by a factor of 1.6 (11.3), and it under-shoots λ4_ν by 2×
     (T8 snapshot +0.0037).
2. **α_s is insensitive to the treatment.** Floating λ4_ν under the exact lattice constraint moves `alphaS` by
   −0.11σ_NOM with σ ratio 0.98. The Gaussian-2D variants (Newton −0.10σ; T8C5 snapshot −0.07σ) agree to ≤ 0.04σ.
   - This is consistent with the study's earlier finding that, within a basin, α_s barely follows the NP tune
     (Findings 7, and 260911 +0.005σ).
   - The one unmodelled piece of the same size is the lattice's own α_s pull through the perturbative kernel, about
     +0.08σ, dropped by the frozen pert table (§4).
3. The TMD side is unchanged in kind. The fit stays on the same single active face, L2(|Y|=2.5) = 0. TMD λ2 rises
   0.026 → 0.054, through the CS–TMD degeneracy, as λ2_ν falls. The W route (λ2_ν = 0, λ4_ν = 0.044) remains excluded
   by the exact lattice term: Δχ²_lat 25.0 against the Z data's preference of 2Δ(data+BB) = −1.8 relative to LATCHI8.

---

### 6. Phase 2 (2026-10-06, evening): WRemnants port, no k-form, pert-scale systematic, α_s-live

**Decisions (Luca, via the orchestrator).**
- The plugin moves into WRemnants.
- α_s-live is the consistent choice, together with a perturbative-kernel uncertainty.
- The **k-form systematic is removed**: k1·a/b_T is the lattice authors' prescription, not a choice of ours to vary.
  - The new default systematic set is **n_f scheme + b_T window** (`syst=Jnf+Jbt`); `Jk` is opt-in only.
  - The fits add the pert-scale group: `syst=Jnf+Jbt+pert`.
- Lattice systematics stay a covariance. A linear point shift δ in C is identical to a profiled unit-Gaussian
  nuisance on δ.
- **NOTE:** NOMSTIFF's 1D card (`cardA_latticeASWZ_l4zero_statsyst`) and the 2D card (`cardA_latticeASWZ_statsyst`)
  still contain the k-form systematic. They are not re-injected: the exact term replaces them.

**A. WRemnants commit `44f8a5c0`** on `scetlib-ad-param-model`, not pushed:
- `wremnants/postprocessing/scetlib_ad/lattice_cs_chi2.py`;
- `wremnants/postprocessing/scetlib_ad/data/lattice_aswz_inputs.{npz,json}`, the package-data inputs, found
  automatically;
- `scripts/tests/test_lattice_cs_chi2.py`, self-contained: 12/12 PASS without the study code. The study-side
  cross-checks against `our_cs_kernel.py` are in [test_lattice_cs_chi2.txt](test_lattice_cs_chi2.txt), 19/19 PASS.
- Lint: container black, isort (profile black, line length 88), and flake8 with the CI F-selection, all clean. Committed
  inside the container; the pre-commit hook (black, isort, pylint) ran.
- `alphas=frozen` stays the default. The phase-1 copy that LATCHI8 ran is archived as `scripts/lattice_cs_chi2_v1_LATCHI8.py`
  (md5 dbaae121…).
- The inputs file gained the pert-scale vectors and a more accurate ∂γ_pert/∂α_s:
  - h = 1e-4 instead of 1e-3; the old secant carried a 0.75 % curvature bias.
  - Every array LATCHI8 used is bit-identical (checked; the old file is kept on ceph as
    `lattice_aswz_inputs_phase1_md5_bde9d60f.npz`).

**B4. Perturbative-kernel scale variation** (`scripts/pert_scale.py`, via `our_cs_kernel` internals):
- The variation scales the b-space boundary scale, μ0 → κμ0, κ = 2 and 1/2, floored scale included. L_b follows μ0, so
  it is the RG-consistent variation.
- Point shifts:

  | variation | shift range | max \|δ\|/σ_lat |
  |---|---|---|
  | κ = 1/2 | +0.005 to +0.047 | 0.53 |
  | κ = 2 | −0.015 to −0.003 | 0.15 |
  | canonical-only κ (floor kept) | ≤ 0.011 | – |
  | N4LL − N3LL | +0.001 to +0.008 | – |

- κ = 1/2 is taken (the larger under the stat metric, 1.45 vs 0.14) as a **direct point shift**.
- **Size:** it adds 0.70 σ_stat in quadrature to λ2_ν and 0.38 σ_stat to λ4_ν: σ(λ2_ν) 0.0429 → 0.0507, σ(λ4_ν)
  0.00337 → 0.00359. That is **larger than the n_f group** (0.47 / 0.23 σ_stat).
- It moves the lattice minimum slightly: λ2_ν 0.1844 → 0.1882, χ²_min −0.02.

**Per-systematic size** (the summary's chosen shift per group, in units of the stat σ: 0.0383 for λ2_ν, 0.00325 for λ4_ν):

| group | Δλ2_ν | Δλ4_ν | Δλ2_ν/σ_stat | Δλ4_ν/σ_stat | χ²_stat(d) |
|---|---|---|---|---|---|
| n_f scheme (μ = 1 GeV match) | −0.0179 | +0.00075 | −0.47 | +0.23 | 0.37 |
| **k-form (k2 only) — removed** | −0.0370 | +0.00215 | **−0.97** | +0.66 | 1.10 |
| b_T window (drop < 0.2 fm) | +0.0075 | −0.00047 | +0.19 | −0.14 | 0.04 |
| pert scale κ = 1/2 (direct shift; quadrature excess) | – | – | 0.70 | 0.38 | 1.45 (point metric) |

The k-form dominated the old summary systematic, as the 260923 note says.

**Closure under each systematic set** (lattice only, α_s frozen, λ∞_ν = 2; `scripts/phase2_newton.py` →
[phase2_newton.json](phase2_newton.json)). Δχ²_lat is against each set's own minimum.

| syst | χ²_min | λ2_ν | λ4_ν | GN σ(λ2_ν), σ(λ4_ν), ρ | exact-Hessian σ, σ, ρ | NOMSTIFF | LATCHI8 | T8 Newton | W |
|---|---|---|---|---|---|---|---|---|---|
| `J` (old, = 2D card) | 6.713 | 0.1844 | -0.00592 | 0.0567, 0.00400, -0.911 | 0.0575, 0.00419, -0.914 | 7.17 | 6.88 | 7.58 | 24.98 |
| `none` (stat only) | 6.713 | 0.1844 | -0.00592 | 0.0383, 0.00325, -0.883 | 0.0391, 0.00341, -0.888 | 17.10 | 13.07 | 18.45 | 34.38 |
| `Jnf` | 6.713 | 0.1844 | -0.00592 | 0.0423, 0.00334, -0.874 | 0.0430, 0.00350, -0.879 | 12.58 | 11.06 | 14.08 | 28.72 |
| `Jk` | 6.713 | 0.1844 | -0.00592 | 0.0532, 0.00390, -0.913 | 0.0543, 0.00409, -0.916 | 8.60 | 7.34 | 8.80 | 27.34 |
| `Jbt` | 6.713 | 0.1844 | -0.00592 | 0.0390, 0.00329, -0.885 | 0.0399, 0.00345, -0.890 | 16.49 | 12.60 | 17.72 | 33.96 |
| **`Jnf+Jbt` (new default)** | 6.713 | 0.1844 | -0.00592 | **0.0429, 0.00337, -0.877** | 0.0436, 0.00353, -0.881 | **12.24** | **10.75** | 13.64 | **28.54** |
| **`Jnf+Jbt+pert` (LATLIVE)** | 6.692 | 0.1882 | -0.00609 | **0.0507, 0.00359, -0.878** | 0.0511, 0.00374, -0.881 | **8.72** | **8.88** | 10.04 | **25.87** |

**D. What dropping systematics does: Newton steps from LATCHI8.**
- Construction: LATCHI8's stored covariance (data + priors + the exact `J` term + the stiff spring on its active face)
  with the (λ2_ν, λ4_ν) block of the `J` term swapped for the variant's. The step comes from the gradient change at
  LATCHI8 (cache-free, quadratic, from one point). α_s is frozen in all rows.

| lattice syst | Δ`alphaS`/σ_NOM | Δ vs LATCHI8 /σ_NOM | σ ratio (vs NOM) | λ2_ν | λ4_ν | Δχ²_lat (own set) |
|---|---|---|---|---|---|---|
| `J` (LATCHI8 itself; check) | -0.111 | -0.000 | 0.981 | 0.0295 | 0.00728 | 6.88 |
| (i) `none`, stat only | -0.127 | **-0.016** | 0.981 | 0.0437 | 0.00913 | 8.81 |
| (ii) stat + n_f | -0.124 | -0.013 | 0.981 | 0.0412 | 0.00877 | 8.65 |
| (iii) stat + k-form | -0.116 | -0.005 | 0.981 | 0.0310 | 0.00786 | 7.16 |
| (iv) stat + b_T window | -0.126 | -0.015 | 0.981 | 0.0429 | 0.00909 | 8.71 |
| **new default `Jnf+Jbt`** | **-0.123** | **-0.012** | 0.981 | 0.0406 | 0.00871 | 8.55 |
| `Jnf+Jbt+pert` | -0.117 | -0.006 | 0.981 | 0.0355 | 0.00800 | 8.16 |

- **Stat-only moves `alphaS` by only −0.016σ_NOM against LATCHI8**, below the 0.05σ flag, so no real fit is needed. Every
  systematic choice is within 0.016σ, and σ(`alphaS`) does not change (0.981 throughout). λ4_ν stays interior
  (+0.0073 to +0.0091) in every case.
- **NOMSTIFF without the k-form in its 1D card** (σ(λ2_ν) 0.0313 → 0.0258, Newton from NOMSTIFF's covariance):
  Δ`alphaS` = **+0.031σ_NOM**, σ ratio 1.000, λ2_ν 0.064 → 0.079.

**B1. α_s source: verified (BLINDCHK, data, blinding armed).**
- α_s(term) − α_s(param model) = **0 exactly**.
- The term reads the offset-applied `get_poi()` frame, not the blinded `Fitter.x`. Under blinding it differs from the map
  on x; disarmed, it equals it.
- Autodiff vs FD in x[alphaS]: 1.4e-9. Slopes match (0.002).
- The map is the param model's own `_rp_c` for alphaS, read from `fitter.param_model` in `set_expectations`, and it
  equals the correction-runcard map. Code path: Log 2026-10-06 17:15.

**B2. Logging.**
- The class prints only α_s-independent numbers: the frozen-table offset, the map coefficients, the armed parameter
  names.
- For live fits, `compare.py` is run with kind `none`: the live lattice term stays inside the published "data_bb"
  (data + BB + live lattice) and is never isolated. Every lattice χ² / k̂1 column of the live rows is a FROZEN-table
  value at the fit's λ.
- The live χ²_lat, k̂1 and residuals were not computed at all: that would need the true α_s, i.e. unblinding.
- The fit logs carry only the total loss, as for every other fit.

**B3. Validation.**
- (a) **Asimov closure** (ASIMLIVE2: one non-randomised expected toy; live term with `ydata=asimov`; τ = 8; start α_s
  θ +1, λ2_ν θ −0.5, λ4_ν θ +0.01): every θ returns to 0 within |θ| ≤ 2.7e-7, i.e. α_s = 0.11800000053. EDM 1.4e-13.
  **PASS** ([asimov_closure.json](asimov_closure.json)).
- (b) **∂χ²_lat/∂α_s:**
  - analytic vs FD of the exact evaluator re-run at 0.118 ± 1e-4: 6e-5 (study test 7a);
  - vs FD of the linear model: 2e-11 (WRemnants test 5);
  - TF autodiff vs FD: 1e-9 (WRemnants test 6 and BLINDCHK C).

**B5. LATLIVE: the α_s-live fit.**

**Caveats first.**
- Real data. `alphaS` is blinded: Δ in σ_NOM, σ ratios only.
- LATLIVE ran on the **|Y| ≤ 2.5 subset cache** (`pdf62_y35_260921_y25`). It is exact for card A: SUBCHK8B replayed
  LATCHI8's own command on it with ΔNLL = **+0.000e+00** vs LATCHI8 on the full cache.
- LATLIVE differs from LATCHI8 in two things at once:
  - (i) α_s-live;
  - (ii) the lattice covariance, `Jnf+Jbt+pert` instead of `J`: k-form removed, pert-scale added.

  The Newton table above isolates (ii): −0.006σ_NOM from LATCHI8. So essentially all of the LATCHI8 → LATLIVE shift is
  (i).
- Same card, priors (44, checked in the log), wall, minimiser and code tree (WRemnants 44f8a5c0) as LATCHI8. Chain:
  τ = 5 warm from LATCHI8 → τ = 8 with the Hessian.

| | NOMSTIFF | LATCHI8 (exact, `J`, α_s frozen) | **LATLIVE8Y** (exact, `Jnf+Jbt+pert`, **α_s live**) | LATLIVE5Y (τ = 5) |
|---|---|---|---|---|
| Δ`alphaS` / σ_NOM | 0 | −0.111 | **−0.042** | −0.042 |
| Δ`alphaS` vs LATCHI8 / σ_NOM | +0.111 | 0 | **+0.069** | +0.069 |
| σ(`alphaS`) / σ_NOM | 1 | 0.981 | **0.985** | – |
| EDM | 3e-14 | 3.1e-17 | **2.1e-17** | – |
| λ2_ν | 0.0643 ± 0.023 | 0.0295 ± 0.030 | **0.0339 ± 0.030** | 0.0340 |
| λ4_ν | 0 (frozen) | +0.0073 ± 0.0045 | **+0.0080 ± 0.0053** (interior) | +0.0080 |
| TMD λ2 / λ4 / δλ2 | 0.0256 / 0.0876 / −0.0041 | 0.0536 / 0.0866 / −0.0086 | **0.0502 / 0.0838 / −0.0080** | same |
| active wall face | L2(\|Y\|=2.5) = 0 | L2(\|Y\|=2.5) = 0 | **L2(\|Y\|=2.5) = 0** | same |
| priors (card + 44 model) | 19.182 | 18.542 | 18.626 | 18.627 |
| Δχ²_lat, FROZEN table, `Jnf+Jbt+pert`, at the fit's λ | 8.72 | 8.88 | **8.31** | 8.30 |
| Δχ²_lat, frozen, `Jnf+Jbt` | 12.24 | 10.75 | 9.62 | 9.61 |
| k̂1 (frozen table, `J`) | 0.190 | 0.173 | 0.174 | 0.174 |

- The live row's lattice values are frozen-table evaluations at its λ, by design (B2). The live term's own value is not
  published.
- **Prediction vs measurement.** The live α_s pull estimated in §4 at LATCHI8's point is +0.080σ; the syst-set change
  (Newton) is −0.006σ; together +0.074σ. **Measured: +0.069σ.**

![Kernel space: NOMSTIFF, LATCHI8 and the alpha_s-live fit LATLIVE8Y with the ASWZ points](kernel_space_LATLIVE8Y.png)

*Caveats for the figure:*
- The points are shown minus k̂1·a/b_T with k̂1 = 0.17 (frozen table at LATCHI8's CS point). The legend Δχ² values are
  frozen-table `syst=J` values.
- All curves are n_f = 5 pert at α_s(m_Z) = 0.118. LATLIVE8Y's pert part would move with its blinded α_s by about
  0.002 per 0.001 of α_s, invisible here.
- The bands are CS-only covariances.

**Physics read (phase 2).**
1. Making the lattice term α_s-live is the consistent choice, and it is now validated three ways under blinding:
   source identity, Asimov closure, AD = FD. It pulls `alphaS` by **+0.07σ_NOM**, as predicted from the lattice
   gradient (+0.08σ). The lattice CS kernel carries a small amount of α_s information through our perturbative kernel at
   small b_T.
2. Net effect against the NOMSTIFF nominal: **Δ`alphaS` = −0.04σ_NOM, σ ratio 0.985.** Floating λ4_ν under the exact
   term (−0.11σ) and the live α_s pull (+0.07σ) largely cancel.
   - The lattice-systematic choices are all ≤ 0.016σ (table D).
   - Removing the k-form from NOMSTIFF's own 1D term would move it by only +0.03σ.
3. The NP picture is unchanged: λ4_ν = +0.008 interior, λ2_ν ≈ 0.03, the same single active TMD face, and the lattice
   Δχ² (frozen table) about 8.3 for 2 dof. Every lattice-treatment variant studied moves `alphaS` by at most 0.11σ_NOM,
   well inside σ.

---

### 7. Phase 3 (2026-10-07): fully live perturbative kernel (α_s + CS TNPs), no μ0 scale variation, direct n_f

**Decisions (Luca, via the orchestrator).** In the live variant pert_i follows every fitted parameter that enters the
perturbative CS kernel. Missing higher orders are the TNPs' job, so the μ0 scale-variation systematic is dropped from
the default (opt-in `mu0scale`, alias `pert`). The default systematics are `Jnf+Jbt`; the b_T window stays pending the
theorist's answer.

**What enters pert_i at (b_T, μ = 2 GeV), and why** (SCETlib `include/scetlib/qT/Gamma_nu.hpp`, `src/qT/*.cpp`):
- `qT::Gamma_nu::TNPs` holds exactly two TNPs: **gamma_cusp** (on Γ3) and **gamma_nu** (on the 3-loop γ_ν boundary
  constant). The beam and soft set the same two on their γ_ν objects (`Beam.cpp:192,200`, `Singular.cpp:122-130`).
  - Both are included: `resumTNP_gamma_nu` and `resumTNP_gamma_cusp`.
- **No β-function TNP exists in SCETlib's TNP sets**, so the running coupling has none.
- **Not included, and why:**
  - `resumTNP_gamma_mu_q`, `resumTNP_s` and `resumTNP_b_*`/`h_*` sit in the μ-anomalous dimension and the hard/beam/soft
    boundary terms, not in the rapidity anomalous dimension.
  - `resumTransition2` is `Calculation_settings.transition_points[1]`, a qT-space profile transition. The kernel
    γ_ζ(b_T, μ) has no qT.
  - μ0_min, b0/bmax_nu and κ-type scale factors are fixed runcard settings, not fitted.
  - The PDF eigenvectors and the NP λs: the λs are already the NP part.
- θ → physical: the TNPs are identity maps in the param model (physical = θ). The plugin reads them, like α_s, from
  `fitter.param_model._rp_*`, on `get_x()`. TNPs are unblinded nuisances; the α_s safeguards are unchanged.

**Expansion** (`pert=live`):
- pert + Δα dP_α + ½Δα² dP_αα + Σ_t [t dP_t + Δα t dP_αt].
- The TNPs enter **exactly linearly**: FD at steps 0.1 and 2 agree to 3e-13.
- dP_t / σ_lat ≤ 0.066 per unit θ_γν and ≤ 0.009 per unit θ_cusp.
- Joint accuracy against the exact evaluator over |TNP| ≤ 2: **4.2e-3 σ_lat for |Δα_s| ≤ 0.002** (2.2e-2 at 0.004).
  Purely linear would be 3.5e-2 at 0.002, hence the second-order and cross terms.
- Inputs: `dpert_dalphas2`, `dpert_dtnp_{nu,cusp}1`, `dpert_das_tnp_{nu,cusp}`. Earlier arrays are bit-identical.
  The phase-2 file is kept on ceph as `lattice_aswz_inputs_phase2_md5_*.npz`.

**Code: WRemnants `3ef3efb9`** on `scetlib-ad-param-model`, not pushed:
- `pert=frozen|alphas|live` (`alphas=live` is kept as the spelling of `pert=alphas`; LATLIVE commands still run
  bit-identically);
- the `mu0scale` opt-in; default syst `Jnf+Jbt`;
- tests: WRemnants `scripts/tests/test_lattice_cs_chi2.py`, all PASS (TNP paths: TF = numpy, AD = FD, maps from the
  param model). Study tests 8a–8c (TNP derivatives vs FD of `our_cs_kernel`; expansion accuracy) PASS, 22/22 in
  [test_lattice_cs_chi2.txt](test_lattice_cs_chi2.txt);
- lint (container black/isort/flake8 CI selection) clean; committed inside the container.
- The v2 plugin copy LATLIVE ran is archived as `scripts/lattice_cs_chi2_v2_LATLIVE.py`.

**direct_nf vs Jnf (cache-free Newton from LATLIVE8Y; `scripts/newton_dnf.py` → [newton_dnf.json](newton_dnf.json)).**
- Construction: LATLIVE8Y's Hessian with the lattice (α_s, λ2_ν, λ4_ν) block swapped.
- Caveat: the live term's derivatives are evaluated at Δα_s = 0, because the fit's true α_s is blinded. The error is
  second order in a covariance difference.
- pert = α_s-linear, as in LATLIVE8Y; the TNP-live part is not in these rows.

| lattice syst | lattice-only GN σ(λ2_ν), σ(λ4_ν), ρ | Δ`alphaS`/σ_NOM | Δ vs LATLIVE8Y | σ ratio | λ2_ν (shift/σ) | λ4_ν (shift/σ) |
|---|---|---|---|---|---|---|
| LATLIVE8Y's own set (closure row) | 0.0507, 0.00359, -0.878 | -0.0420 | -0.0000 | 0.9850 | 0.0339 (+0.00σ) | 0.00797 (+0.00σ) |
| **Jnf+Jbt** (default; LATFULL) | 0.0429, 0.00337, -0.877 | -0.0311 | +0.0109 | 0.9845 | 0.0381 (+0.14σ) | 0.00923 (+0.26σ) |
| **direct_nf+Jbt** | 0.0432, 0.00338, -0.875 | -0.0382 | +0.0038 | 0.9845 | 0.0373 (+0.11σ) | 0.00947 (+0.31σ) |
| stat only (orientation) | 0.0383, 0.00325, -0.883 | -0.0281 | +0.0139 | 0.9841 | 0.0402 (+0.21σ) | 0.00995 (+0.44σ) |

- **`direct_nf+Jbt` vs `Jnf+Jbt`: Δ`alphaS` = 0.007σ_NOM** (below the 0.01σ threshold). λ2_ν moves by −0.03σ and λ4_ν
  by +0.05σ (below 0.3σ). **So no LATDNF fit was run.** The `RUN_LATDNF` flag of chain7 was not set.
- **The two shift patterns are very different point by point** (correlation −0.04):
  - **direct is a constant −0.042 at every b_T** (the n_f = 5 μ = 1 GeV-matched kernel minus ours is b-independent
    over 0.09–0.9 fm, since μ0 ≥ 1 GeV there). It behaves like a free offset nuisance of width 0.042 (≤ 0.5σ_lat).
  - **J-mapped is a rising ramp:** +0.002 at 0.09 fm, +0.036 at 0.6 fm, back to +0.02 at 0.9 fm; ≤ 0.33σ_lat. It is
    nearly the same linearised at LATLIVE8Y's λ instead of the lattice best fit (≤ 0.37σ_lat, the shape bends only
    above 0.7 fm).
  - The fit barely distinguishes the two because neither shape is degenerate with the NP b² / b⁴ directions in a way
    that moves α_s.
- Keep `Jnf+Jbt` as the default; Luca decides.
- Side result: dropping `mu0scale` from LATLIVE8Y's set predicts +0.011σ_NOM, λ4_ν 0.0080 → 0.0092.

**Fits (chain7, subset cache, mem_gate 260 GB).**
- **BLINDFULL** (data, blinding armed, the LATFULL8 command):
  - A: α_s(term) − α_s(model) = **0 exactly**;
  - B: the term reads `get_poi()`, not x;
  - C: AD = FD to 1.4e-10;
  - **E: resumTNP_gamma_nu and resumTNP_gamma_cusp as seen by the term − as handed to SCETlib by the model = 0
    exactly**, AD = FD to 1e-10 / 1.7e-9.
  - Logs: [logs/BLINDFULL.log](logs/BLINDFULL.log).
- **ASIMFULL** (`pert=live`, `ydata=asimov`, one non-randomised expected toy, τ = 8):
  - start: α_s θ +1, λ2_ν θ −0.5, λ4_ν θ +0.01, θ_γν +1, θ_cusp −1;
  - every θ back to the truth within **|θ| ≤ 6e-10**, both TNPs included; EDM 5.3e-18. **PASS**
    ([asimov_closure_full.json](asimov_closure_full.json)).
- LATFULL5 (exit 0, 14:16) → **LATFULL8** (exit 0, 14:48, EDM 1.2e-17). Both logs show "Gaussian priors on 44" and
  the `pert live in: alphaS, resumTNP_gamma_nu …, resumTNP_gamma_cusp …` arming line.

**Result: LATFULL8 (fully live pert) vs LATLIVE8Y vs NOMSTIFF** ([compare.json](compare.json) = [compare_phase3.json](compare_phase3.json)).

**Caveats first.**
- Real data. `alphaS` is blinded: Δ in σ_NOM, σ ratios only.
- LATFULL8 differs from LATLIVE8Y in two things:
  - (i) pert also follows the CS TNPs (plus the α_s second-order and cross terms);
  - (ii) `mu0scale` is dropped from the covariance.

  The Newton table above puts (ii) at +0.011σ_NOM, so (i) is about −0.055σ.
- Both ran on the subset cache (exact for card A, checked).
- The lattice χ² columns are FROZEN-table values at each fit's λ (the live term is not published, B2).
- TNP θ are unit nuisances with N(0, 1) priors, unblinded.
- XWSTIFF (no lattice) is shown for orientation only.

| | NOMSTIFF | LATCHI8 | LATLIVE8Y | **LATFULL8** | XWSTIFF (no lattice) |
|---|---|---|---|---|---|
| lattice term | 1D Gaussian, λ4_ν ≡ 0 | exact, `J`, pert frozen | exact, `Jnf+Jbt+mu0scale`, pert α_s | **exact, `Jnf+Jbt`, pert α_s + TNPs** | none |
| Δ`alphaS` / σ_NOM | 0 | −0.111 | −0.042 | **−0.086** | −0.367 |
| σ(`alphaS`) / σ_NOM | 1 | 0.981 | 0.985 | **0.979** | 0.933 |
| EDM | 3e-14 | 3e-17 | 2e-17 | **1.2e-17** | 7e-18 |
| λ2_ν | 0.0643 ± 0.023 | 0.0295 ± 0.030 | 0.0339 ± 0.030 | **0.0357 ± 0.030** | 0 (wall) |
| λ4_ν | 0 | 0.0073 ± 0.0045 | 0.0080 ± 0.0053 | **0.0098 ± 0.0056** | 0.0444 |
| TMD λ2 / λ4 / δλ2 | 0.026 / 0.088 / −0.0041 | 0.054 / 0.087 / −0.0086 | 0.050 / 0.084 / −0.0080 | **0.049 / 0.078 / −0.0078** | 0.119 / −7e-5 / −0.0094 |
| **θ(resumTNP_gamma_nu) ± σ** | 0.69 ± 1.01 | 0.38 ± 1.01 | 0.44 ± 1.01 | **0.31 ± 1.01** | 0.29 ± 1.01 |
| **θ(resumTNP_gamma_cusp) ± σ** | −0.15 ± 1.00 | −0.07 ± 1.00 | −0.09 ± 1.00 | **−0.07 ± 1.00** | −0.05 ± 1.00 |
| θ(gamma_mu_q), θ(s) (not in the kernel) | 0.14, 0.36 | 0.12, 0.22 | 0.13, 0.25 | 0.13, 0.26 | 0.12, 0.17 |
| active wall face | L2(\|Y\|=2.5) | same | same | **same** | λ2_ν, B(\|Y\|=2.5) |
| frozen-table Δχ²_lat, `Jnf+Jbt`, at the fit's λ | 12.24 | 10.75 | 9.62 | **9.01** | 28.54 |

![Kernel space: NOMSTIFF, LATFULL8 and LATLIVE8Y with the ASWZ points](kernel_space_LATFULL8.png)

*Caveats for the figure:*
- The points are shown minus k̂1·a/b_T (frozen table, `J`, at LATFULL8's CS point).
- The curves use the frozen pert part (α_s 0.118, TNPs 0). LATFULL8's TNP shift of the kernel is ≤ 0.3 × 0.066σ_lat,
  invisible here.
- The legend Δχ² are frozen-table `J` values. The bands are CS-only covariances.

**Do the CS TNPs move when the lattice sees them?** Barely, and they gain no constraint.
- θ_γν goes 0.44 → 0.31 (LATLIVE8Y → LATFULL8), a shift of −0.12 prior σ. θ_cusp moves by +0.02. Their posterior
  widths stay at the prior: 1.013 and 1.001.
- That is expected. One unit of θ_γν moves the lattice points by ≤ 0.066σ_lat, coherently (0.0018–0.0062 in γ_ζ), so
  the lattice has almost no lever arm on it.
- The bigger TNP differences across fits come from the Z-side NP rearrangement, not from the lattice coupling.
  θ_γν is 0.69 in NOMSTIFF, 0.29 without any lattice term (XWSTIFF), and 0.38–0.44 in the lattice fits that do not
  couple it.

**Physics read (phase 3).**
1. With the perturbative kernel fully live (α_s and the two CS-kernel TNPs, the only fitted parameters that enter it),
   and only the n_f and b_T-window lattice systematics, the nominal moves **Δ`alphaS` = −0.09σ_NOM vs NOMSTIFF, σ ratio
   0.979**.
   - λ4_ν = +0.0098 stays interior, λ2_ν = 0.036.
   - The single active TMD face is unchanged.
   - The lattice tension (frozen table) is the lowest of all lattice fits, Δχ² 9.0 for 2 dof.
2. Against the α_s-only-live LATLIVE8Y it is −0.044σ, of which about −0.055σ comes from the TNP coupling and +0.011σ
   from dropping the μ0 systematic (Newton).
   - The TNP coupling acts through the Z side (the TNP–α_s correlation of the data fit), not through any lattice
     constraint on the TNPs, which is nil.
3. Every lattice treatment explored lands within [−0.11, −0.04]σ_NOM of NOMSTIFF, with σ(`alphaS`) within 2.1 %. The
   CS-kernel treatment is not a significant α_s systematic once the lattice constraint is applied exactly.


---

## Findings

1. A rabbit `-r` Regularizer can carry an exact external χ², but **rabbit multiplies every regularizer by exp(2τ)**.
   A likelihood term must divide that out; here it uses the live `fitter.tau` taken from the call stack. Two `-r`
   compose additively. — (evidence: rabbit 2a59246 `fitter.py` `_compute_nll_components`; [test_lattice_cs_chi2.txt](test_lattice_cs_chi2.txt) 5c/5d; [logs/LATCHI5.log](logs/LATCHI5.log))
2. A nuisance that enters linearly (k1·a/b_T) can be profiled in closed form inside the term (χ² = r0ᵀMr0). That is
   exactly equivalent to a free parameter. — (evidence: test 2, closure §2)
3. Mapping a parameter-space systematic shift onto the points as J·d and adding it to the covariance reproduces the
   summary's stat+syst covariance exactly (Woodbury), and keeps the term exact in λ. — (evidence: test 4)
4. **The 2D Gaussian summary is 31× too steep at the W point** (Δχ² 549 vs 17.8, stat+syst). Near NOMSTIFF it is
   about right in value (5.7 vs 7.2) but pulls λ4_ν 1.6× too weakly. — (evidence: [closure.json](closure.json), Result §3)
6. **α_s is insensitive to how the lattice CS constraint is applied.** With the exact χ² and λ4_ν free, `alphaS` moves
   −0.11σ_NOM (σ ratio 0.98) vs NOMSTIFF. The 2D-Gaussian versions agree to ≤ 0.04σ. λ4_ν ends interior at +0.0073.
   — (evidence: [compare.json](compare.json), Result §5)
5. The frozen pert table drops an α_s pull of about +0.11σ(α_s) that the lattice points would exert through our
   perturbative kernel. That is small but not negligible against the 0.1σ effects being compared. The Gaussian summaries
   drop it too. — (evidence: Result §4)

---

7. **α_s-live lattice term:** the lattice points pull `alphaS` by +0.07σ_NOM through our perturbative kernel
   (predicted +0.08). Net LATLIVE8Y vs NOMSTIFF: −0.04σ_NOM, σ ratio 0.985. — (evidence: [compare.json](compare.json), Result §6 B5)
8. **The lattice-systematic choice is irrelevant for α_s:** stat-only vs any combination of the systematics moves
   `alphaS` by ≤ 0.016σ (Newton). The k-form dominated the old summary systematic (Δλ2_ν −0.97 σ_stat). The b-space
   scale variation of our pert kernel (μ0 × ½) is the largest remaining one (0.70 σ_stat on λ2_ν).
   — (evidence: [phase2_newton.json](phase2_newton.json))
9. **For knowledge/ (rabbit):**
   - `-t -1` is never minimised by rabbit_fit (`dofit = ifit >= 0`). An Asimov FIT needs
     `-t 1 --toysDataMode expected --toysDataRandomize none --toysSystRandomize none`, and that result is stored as
     `results_toy1`.
   - A `--noFit` replay should add `--noEDM`: the CG EDM is very slow on the blinded 3720-parameter problem.
   — (evidence: Log 2026-10-06 17:15, 2026-10-07 09:05/09:40)

---

10. **Fully live perturbative kernel:** only resumTNP_gamma_nu and resumTNP_gamma_cusp enter SCETlib's γ_ν (there is
    no β TNP). They enter linearly, and the lattice cannot constrain them (≤ 0.066σ_lat per unit θ). The nominal
    LATFULL8 is at Δ`alphaS` −0.09σ_NOM, σ ratio 0.979. The direct vs J-mapped n_f systematic differs by 0.007σ, even
    though the shapes differ (a constant −0.042 offset vs a ramp). — (evidence: Result §7, [newton_dnf.json](newton_dnf.json))

---

## Open questions

- ~~α_s-live lattice term~~: done in phase 2 (Result §6).
- **The systematic covariance is a choice.** J-mapped shifts (like-for-like with the summary) vs `direct_nf`. The two
  give the same minimum to 0.06σ. A more faithful treatment would be nuisance parameters per systematic, profiled the
  same way as k1 (all linear in the points).
- **TNPs.** The term holds the pert kernel at TNP = 0. NOMSTIFF's postfit CS TNPs would move χ²_lat by +0.24. A live TNP
  dependence (θ_γν, θ_cusp) is a small extension, as for α_s.
- **Code tree.** WRemnants HEAD is now a008faa5 (TMD priors off by default, committed). The explicit prior pin restores
  NOMSTIFF's 44 priors (verified in the log), but the tree is not NOMSTIFF's 29c884d-era one, and the same holds for T8.
- ~~Moving to WRemnants~~: committed as 44f8a5c0 (package data next to the module, not wremnants-data); not pushed.
- The 1D/2D Gaussian lattice cards still include the k-form systematic (not re-injected; the exact term replaces them).
