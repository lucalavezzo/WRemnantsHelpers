---
title: Native (SCETlib-AD) lattice CS-kernel chi2 term
slug: 261007-lattice-term-native
study: lattice-cs-kernel
status: done          # active | done | paused | abandoned
created: 2026-10-07
updated: 2026-10-08
owner: study-worker
---

# Native (SCETlib-AD) lattice CS-kernel chi2 term

**Task:** Can the lattice CS-kernel chi2 term be computed natively by SCETlib-AD at every fit step (same analytic-RGE kernel as the fit cache, no shipped theory tables), validated against the old table term, and what do the LATB5->LATB8 fit and the n_f / b_T-window / RGE systematics give?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-10-08 00:30) — DONE (orchestrator note 2026-10-08: SATB8/SATB8SA finished; all commits below pushed)

- **Answer (main task):** native lattice term built and validated (scetlib-cms 069c326 + 6ab371a; WRemnants b14f84f4);
  LATB8 −0.027σ_NOM vs LATFULL8 (−0.113σ vs NOMSTIFF). Result §0–8.
- **Follow-ups:** `CompositeParamModel` support (WRemnants **4e7e481e**), SATCHK all PASS. Full saturated χ² LATB8
  753.35/777 (p 72.2 %) vs NOMSTIFF 753.23/778 (73.2 %): each includes its own (different) lattice term, so this is not
  like-for-like; Z data+BB of LATB8 is ≈ 1.46 NLL better than NOMSTIFF (lattice at α_s 0.118). **Projected ptll: q = 78.40/39,
  p 0.019 %** (NOMSTIFF lineage 80.73/39). Sub-fit seeding: rabbit **9bfe73f** (`saturated-subfit-seed`, worktree
  `/work/submit/lavezzo/alphaS/rabbit-satseed`, pushed to the luca fork, no PR); seeded run 2.0× faster, same minimum to 2e-9.
- **Next action:** none. Task closed; the line continues in 261008-latfroz-nf-variants.
- **Blocking on:** nothing.
- **Running:** nothing. SATB8 and SATB8SA both exited 0 overnight 2026-10-07/08 ([logs/SATB8.log](logs/SATB8.log), [logs/SATB8SA.log](logs/SATB8SA.log)).

---

## Log

<!-- Newest first. What was tried, what happened, why — with an evidence path. -->

### 2026-10-07 (18:15–) — follow-up (Luca approved): CompositeParamModel support + saturated test on LATB8
- **WRemnants 4e7e481e** (committed in the container, not pushed): `LatticeCSTerm` accepts a rabbit
  `CompositeParamModel` with exactly one `SCETlibADParamModel` among its direct submodels (none, two, or nested →
  refused). The submodel's native [poi | pou] vector is obtained by running the composite class's OWN `compute()` on
  recorder stand-ins (`lattice_cs_term.submodel_vector`), i.e. the composite's permutation, not a re-derivation; that
  vector goes to `scetlib_full_vector_tf`. The load-time core is reused when the SCETlib calculation is the same object
  (the saturated fitter's deepcopy). Arming checks the submodel's names at the layout's positions.
- Tests: WRemnants `scripts/tests/test_lattice_cs_term.py` 15/15 PASS with a toy composite in both submodel orders
  (vector == what `compute()` hands the submodel; χ² == plain model's at the same physical point, bitwise; two SCETlib
  submodels refused) ([logs/wrem_test_lattice_cs_term_v2.log](logs/wrem_test_lattice_cs_term_v2.log)); task offline
  tests still 13/13 ([logs/test_term_v2.log](logs/test_term_v2.log)).
- **Where NOMSTIFF's 753.2/778 (p 73 %) comes from:** not a projection test. It is rabbit's default "Saturated chi2"
  printed by EVERY fit: 2 × `reduced_nll()` at the minimum, ndof = bins − free param-model parameters
  (`bin/rabbit_fit.py` ~l. 1015–1046). NOMSTIFF ran no `--computeSaturatedProjectionTests` (its command has no `-m`);
  the walled-lattice fits with a projected-ptll test are the 260928 ones (`fitterAD.sh` flags
  `-m Project ch0 ptll --computeSaturatedProjectionTests`, projected ptll 80.73/39 for LATL4ZY35WALLWARM, NOMSTIFF's seed).
  So LATB8's full saturated χ² already exists in its own log; the projected-ptll test needs a new pass.
- Launched (mem_gate, logs symlinked): **SATB8** = LATB8's command + `--noFit --noHessian --noEDM --saveHists --noChi2
  -m Project ch0 ptll --computeSaturatedProjectionTests`, `--externalPostfit fitresults_LATB8.hdf5` (TMD priors pinned
  as in LATB8, same 44 priors) ([cmds/SATB8.cmd](cmds/SATB8.cmd), [logs/SATB8.log](logs/SATB8.log)); **SATCHK**
  ([scripts/satcheck.py](scripts/satcheck.py)): the term inside the saturated fitter, built as rabbit builds it, on data
  with blinding armed ([logs/SATCHK.log](logs/SATCHK.log)).
- Ordering issue (walled + saturated + blinded, WMass/rabbit#180): fixed in the rabbit tree used (2a59246 contains #180,
  0f6653d): `save_hists` arms ALL regularizers before the blinded-start loss check, so two regularizers are covered the
  same way. Confirmed by SATB8 reaching the saturated sub-fit (see below).
- **SATCHK: all PASS** (exit 0 18:38; [satcheck.json](satcheck.json), [logs/SATCHK.log](logs/SATCHK.log)). Saturated fitter
  built as rabbit builds it (Project ch0 ptll, 39 bin scales), data, blinding armed, at LATB8's vector:
  S1 lattice term (saturated) − (main) = **0**; S2 total loss (saturated, bin scales 1) − (main) = **0**;
  A p_full(term) − p_full(vector the composite's own `compute()` hands the SCETlib model) = **0** (53 entries), and vs the
  main fitter's p_full = 0; B armed differs / disarmed equal: True / True; C AD vs FD ≤ 7e-9 (λ4_ν 3e-4, FD step-limited
  as before); D no nonzero term gradient outside the 5 kernel parameters (39 bin scales included); E snapshot status 1.
- SATB8 first try failed at start (18:34): `--externalPostfit` with a covariance + `--noHessian` is refused by
  `load_fitresult`. Relaunched 18:40 from a flat seed (`seeds/seed_LATB8_flat.hdf5`, LATB8's vector bit-for-bit, no
  cov). The failed try's log is `logs/SATB8_try1.log`; its meta-only fitresult was renamed `*_try1_metaonly.hdf5`.
- **Full saturated χ² replayed** in SATB8 at LATB8's point: 753.35/777, p 72.21 % (identical to LATB8's own). SATB8's
  saturated sub-fit armed the term on `CompositeParamModel (SCETlib submodel #0)`, 86 parameters, with blinding: the
  walled + saturated + blinded ordering bug does NOT fire with two regularizers (rabbit 2a59246 contains #180).
- 21:00 (orchestrator / Luca): SATB8's sub-fit crawls (trust-krylov staircase). **Option (b), seed the sub-fit:**
  - rabbit had NO way to seed it: not on 2a59246 (main-plus-ours), and `fix/saturated-fit-own-snapshot-path` (04cef1f,
    already merged there as c2ee813) only gives the sub-fit its own snapshot path. The sub-fit always starts at the main
    minimum with the 39 bin scales at 1.
  - **NOMSTIFF has no projected-ptll result** (it ran no projection). Most recent compatible converged sub-fit:
    **LATL4ZY35WALLWARM** (260928; NOMSTIFF's own seed; card A + lattice + wall, y35 cache, same 39 ptll bins),
    `260928_lattice_y35_fits/snapshot_fitresults_LATL4ZY35WALLWARM_saturated_Project_ch0_ptll.hdf5` (`reason=converged`,
    projected q = 80.73/39).
  - **rabbit 9bfe73f** on a NEW branch `saturated-subfit-seed` (off 2a59246), worktree
    `/work/submit/lavezzo/alphaS/rabbit-satseed`, not pushed: `--saturatedSeed <snapshot|fitresult>` +
    `--saturatedSeedScope projection|all`; values copied BY NAME after the warm start; kept only if the start loss is
    finite and not above the warm start's. `rabbit/snapshot.py`: `read_vector`, `seed_by_name`. Tests
    `tests/test_saturated_seed.py` (6) + the existing saturated/snapshot tests: 57 passed.
  - **SATB8S** = SATB8 + `--saturatedSeed <LATL4ZY35WALLWARM sub-fit> --saturatedSeedScope projection` (bin scales from
    the old sub-fit, model at LATB8's minimum), run with the worktree rabbit ([scripts/run_fit_seed.sh](scripts/run_fit_seed.sh),
    [cmds/SATB8S.cmd](cmds/SATB8S.cmd), [logs/SATB8S.log](logs/SATB8S.log)). Queued 21:12 behind the 2-alive cap
    (SATB8 + another worker's YNOWALL).
- **SATB8S (scope `projection`) REJECTED by the guard** (21:37): bin scales from the old sub-fit on LATB8's model give a
  start loss of 25848 vs 376.68. The bin scales and the normalisation nuisances are degenerate in the saturated model:
  the old sub-fit sits at bin scales ≈ 1.02 with `lumi` ≈ 0, while the main fits have `lumi` ≈ −1.5. Copying the scales
  without the nuisances double-counts the normalisation. The guard did its job (it fell back to the warm start). I
  stopped that duplicate of SATB8 (my own PID 3634197) and relaunched as **SATB8SA** with `--saturatedSeedScope all`.
  SATB8SA's seeded start is 345.82, below the warm start's 376.68, so it was accepted (3758 parameters, all 39 bin
  scales) ([cmds/SATB8SA.cmd](cmds/SATB8SA.cmd), [logs/SATB8SA.log](logs/SATB8SA.log)).
- Early comparison: SATB8SA reached 337.70 in 516 s (11 iterations); unseeded SATB8 needed ≈ 8600 s (108 iterations)
  for that. Both then crawl, with SATB8 lower at 22:13 (337.497 vs 337.655).
- **The "full saturated" equality, 753.35/777 vs 753.23/778.** rabbit's default "Saturated chi2" is just
  2 × `reduced_nll()` at the minimum. That is the whole loss: Poisson data relative to the saturated model, BB, the card
  constraints and model priors, the wall, every `-r` term and the card's external terms. There is no second "leg"
  for a term to cancel in. Each fit's own lattice term enters once, and the terms differ: NOMSTIFF has the 1D Gaussian
  card term (2 × 2.525 = 5.05), while LATB8 has the live native term. ndof counts only the 780 Z bins; no lattice points.
  So the near-equality is a coincidence of different sums, not a like-for-like Z GoF. Split (×2, NLL units ×2), with the
  live term replaced by its value at α_s = 0.118 ([scripts/lattice_split.py](scripts/lattice_split.py) →
  [lattice_split.json](lattice_split.json)):

  | 2 × | NOMSTIFF | LATB8 (lattice at α_s 0.118) |
  |---|---|---|
  | Z data + BB | 709.82 | 706.90 |
  | lattice | 5.05 (1D Gaussian) | 9.48 (native exact) |
  | priors (card + 44 model) | 38.36 | 36.97 |
  | wall | 0.00 | 0.00 |
  | total = rabbit's "saturated χ²" | 753.23 | 753.35 |

  **Z data+BB of LATB8 is ≈ 1.46 NLL BETTER than NOMSTIFF, not +1.9 worse.** The substitution's error is
  dL/dα_s × (α_s,true − 0.118) with dL/dα_s = −0.088 NLL per 0.001 at LATB8's λ, so ±0.18 NLL per 0.002 of the
  (unknown) blinded offset. That cannot flip the sign. The orchestrator's +1.9 matches doubling the lumped difference
  to χ² units (2 × 3.28 = 6.56) but subtracting the lattice term in NLL units (4.74): 6.56 − 4.74 = 1.82. I can't
  reconstruct the exact arithmetic. The exact live split must NOT be published: with λ and TNPs public, the live
  lattice value (equivalently the exact data+BB) is a known function of α_s and would unblind it.
- **2026-10-08 00:25 — seeded vs unseeded sub-fit, and the projected-ptll test** (both jobs still alive in the
  minimiser tail; the numbers below are their logged losses, already identical between the two):

  | | SATB8 (unseeded) | SATB8SA (seeded, scope all, from LATL4ZY35WALLWARM's sub-fit) |
  |---|---|---|
  | start loss of the sub-fit | 376.675 (warm start = main) | 345.816 (seed) |
  | reached final −1e-3 | it. 147, 15 375 s | it. 57, 6 236 s |
  | reached final −1e-6 | it. 153, 17 511 s | it. 63, 8 598 s |
  | iterations / restarts (dt ≥ 300 s) so far | 157 / 15 | 66 / 6 |
  | sub-fit loss now | 337.4761620599 | 337.4761620582 (Δ 2e-9) |

  Seeding halves the wall time (2.0× to 1e-6, 2.5× to 1e-3) and cuts the restarts from 15 to 6. Both land on the same
  minimum to 2e-9 in NLL.
- **Projected-ptll saturated test, LATB8:** q = 2 × (376.6751 − 337.4762) = **78.40 for 39 bins, p = 0.019 %**.
  NOMSTIFF never ran a projection. Its lineage seed LATL4ZY35WALLWARM (same card A, lattice + wall, y35 cache; λ4_ν = 0,
  1D card lattice term, τ 5) gave 80.73/39 (p 0.010 %). The ptll tension is essentially unchanged (−2.3 in q), consistent
  with λ4_ν free and the native lattice term not touching the ptll shape problem. Caveat: q here is the loss
  difference incl. the lattice term and the wall in both legs; those are common to both fits at the same model point
  only to the extent the sub-fit moves the model parameters (it does move them), so q is not a pure Z-data number.
- Note: `scripts/run_fit.sh` was edited (a new `case` branch) a minute after SATB8 started; bash reads scripts
  incrementally, so SATB8's final `[run] exit=` line may be garbled. The fit itself is unaffected.

### 2026-10-07 (15:30-18:10) — results
- ASIMNAT exit 0 at 16:37: closure PASS ([asimov_closure.json](asimov_closure.json), read from `results_toy1`).
- LATB5 exit 0 15:49; LATB8 exit 0 16:23 (EDM 5.2e-17); NCHK2 exit 0 16:27 (adds the kernel-swap-only row K).
- compare: [compare.json](compare.json) → Result §7. Impact table → Result §6. No new fits (load average ~650).

### 2026-10-07 (15:00-15:30) — n_f alternative, WRemnants term, offline tests, gated checks
- **scetlib-cms 6ab371a**: `gamma_nu_points(..., nf, mu_match)` (n_f-scheme alternative: n_f flavours in β, cusp and
  boundary, α_s^(nf)(μ_match) := α_s^(5)(μ_match)); the n_f-dependent block of `_build_global` moved into
  `Ad_evaluator::fill_gamma_nu_coeffs` — exact refactor (snapshot from the new code == GlobalData in rules built by the
  old code, bitwise). n_f = 4 values == the `Gamma_nu` class (n_f 4, started at α_s^(5)(1 GeV)) to 0
  ([test_nf_alt.json](test_nf_alt.json)).
- **The SCETlib-native n_f shift is −0.0092 (flat in b_T), 4.6× smaller than the old table's −0.0423**
  ([logs/test_nf_alt.log](logs/test_nf_alt.log)). The design expected "a few %". Reason in Result §4.
- Data-only file `data/lattice_aswz_data.{npz,json}` from the six author files ([scripts/build_data.py](scripts/build_data.py)):
  bitwise the phase-3 arrays.
- **WRemnants b14f84f4** (committed in the container, pylint hook ran; not pushed): `param_model.scetlib_full_vector_tf`,
  `lattice_cs_term.py`, the data file, `scripts/tests/test_lattice_cs_term.py` (ALL PASS with the branch build, SKIP
  with the stock one; [logs/wrem_test_lattice_cs_term.log](logs/wrem_test_lattice_cs_term.log)).
- Offline term tests [scripts/test_term.py](scripts/test_term.py) → [test_term.json](test_term.json), **13/13 PASS**.
- Cache-free Newton decomposition from LATFULL8 ([scripts/newton_decomp.py](scripts/newton_decomp.py) →
  [newton_decomp.json](newton_decomp.json), Δα_s = 0 approximation).
- Gated jobs (mem_gate 260 GB, ≤ 2 alive; commands [scripts/build_cmds.py](scripts/build_cmds.py) →
  `cmds/*.cmd`, diffs in [logs/build_cmds.log](logs/build_cmds.log); run with the branch build via
  [scripts/run_fit.sh](scripts/run_fit.sh)):
  - NCHK ([scripts/nativecheck.py](scripts/nativecheck.py), data, blinding armed, at LATFULL8's vector): exit 0 at
    15:24 ([logs/NCHK.log](logs/NCHK.log), [nativecheck.json](nativecheck.json)). All replay and blinding checks pass.
  - ASIMNAT (Asimov closure), LATB5 (τ 5 warm from LATFULL8), NCHK2 (= NCHK + the kernel-swap-only Newton row) queued.

### 2026-10-07
- 14:45 Read the study logbook, 261007-lattice-term-design (in full), 261006-lattice-chi2-in-fit, AGENTS.md.
  LATFULL8 (PID 1215740) is running on `$WREM_BASE/scetlib-cms/build`, so that build is NOT touched.
- SCETlib branch `gamma-nu-points` (off 2dd978a, the commit the running fits use) as a git worktree at
  `/work/submit/lavezzo/alphaS/scetlib-gamma-nu-points/scetlib-cms`, with its OWN build dir (`.../build`;
  [scripts/build_scetlib.sh](scripts/build_scetlib.sh); data dir = the main checkout's `share/scetlib`).
- **scetlib-cms 069c326** (committed, not pushed): `ad::gnu_point_value` + clad `gnu_point_grad/hess`,
  `Ad_evaluator::gnu_point_scalars`, `DrellYan::gamma_nu_points` + `gamma_nu_snapshot_status` (bitwise snapshot check
  against the first loaded rule), pybind, `scetlib_tf.ScetlibGammaNuTF`, `stage0/test_gamma_nu_points.py` (ALL PASS,
  [logs/stage0_test_gamma_nu_points.log](logs/stage0_test_gamma_nu_points.log)).
- Entry-point validation [scripts/test_gnu_points.py](scripts/test_gnu_points.py) with a reference driver around the
  `qT::Gamma_nu` CLASS ([classdrv/gz_class.cpp](classdrv/gz_class.cpp)): P = 53 with the 4-bin
  `pdf62_y35_bilincut_test` cache loaded, **41/41 PASS** ([test_gnu_points_P53.json](test_gnu_points_P53.json),
  [logs/test_gnu_points_P53.log](logs/test_gnu_points_P53.log)).

---

## Result

### 0. Caveats first
- Real data, `alphaS` **blinded**: shifts are in σ_NOM = σ(`alphaS`) of NOMSTIFF, σ as ratios. Nothing evaluated at a
  live (blinded) parameter vector is published: no live γ_ζ, χ²_lat, k̂1 or term value. Lattice Δχ² columns are at
  α_s = 0.118 (the public anchor) and the fit's λ / TNPs.
- All fits and checks use the **|Y| ≤ 2.5 subset cache** (`pdf62_y35_260921_y25`, exact for card A), card A, NOMSTIFF's
  minimiser settings, the 44 Gaussian priors (TMD priors pinned), λ4_ν floating, the wall at τ = 8; the only change
  between LATFULL8 and LATB8 is the lattice term (old table term → native term), plus the SCETlib build (same cache
  reader; replay checked identical, V5a).
- The "cache-free Newton" numbers evaluate both terms at Δα_s = 0 (α_s = 0.118) because the true α_s is blinded. The
  NCHK job repeats the native-term rows AT LATFULL8's (blinded) point with exact derivatives; the two differ by
  0.016σ_NOM, because the new − old kernel difference is α_s-dependent (−8.5 % slope). The at-the-point numbers are
  the prediction for the fit.
- The lattice covariance is block-diagonal across ensembles (author-confirmed adequate); λ∞_ν = 2 held.

### 1. What was built
**SCETlib** (scetlib-cms branch `gamma-nu-points`, worktree `/work/submit/lavezzo/alphaS/scetlib-gamma-nu-points/scetlib-cms`,
own build dir; **069c326 + 6ab371a**, not pushed):
- `ad::gnu_point_value` (= `gamma_nu_resummed` at a staged `ad_gpt` point) + clad `gnu_point_grad` / `gnu_point_hess`
  (bucketed 8/24/64), throwing stubs without clad.
- `Ad_evaluator::gnu_point_scalars`: {b*_global(b_T), μ0, fz(μ0), fz(μ)} exactly as `fill_node`, μ0 from the
  evaluator's own `Scale_provider`.
- `DrellYan::gamma_nu_points(bT, mu, p, order, nf=0, mu_match=0)` → {value, value_pert, grad (N,P), hess (N,P,P)} over
  `gradient_param_names()`, and `gamma_nu_snapshot_status()`. The coefficients are a one-time `GlobalData` snapshot
  copied under `s_ad_mutex` and **compared bitwise with the first loaded rule's** (every field γ_ν reads, plus the
  rule's μ0-profile settings vs this calculation's `Scale_provider`); a mismatch raises. Evaluation saves/restores the
  calling thread's `ad_g`/`ad_beta`/`ad_gpt` and takes no lock. Refused for the FO piece and for
  `b0_over_bmax_global ≠ 0`. `nf > 0`: n_f-scheme alternative (n_f flavours in β, cusp, boundary; coupling identified
  at `mu_match`); the n_f-dependent `GlobalData` block now lives in `Ad_evaluator::fill_gamma_nu_coeffs` (shared with
  `_build_global`, exact refactor).
- `scetlib_tf.ScetlibGammaNuTF(_XsecTFBase)`: value/Jacobian/Hessian from one call (3.4 ms for 21 points at P = 53),
  hoisted-Hessian second order. `stage0/test_gamma_nu_points.py` (ALL PASS).
- No kernel, rule or cache-format change: existing caches load unchanged (V5a).

**WRemnants** (`scetlib-ad-param-model`, **b14f84f4**, not pushed):
- `SCETlibADParamModel.scetlib_full_vector_tf(param)`: the one θ → physical map, factored out of `_sigma_gen`.
- `lattice_cs_term.LatticeCSTerm` / `LatticeCSTermMapping` (`-r`): ½(χ²_lat − offset)·e^{−2τ},
  r = ½γ_ν^SCETlib(b_i, 2 GeV; p_full) + k1·a_i/b_i − y_i, k1 profiled, p_full = `pm.scetlib_full_vector_tf(get_x()[:nparams])`.
  Load-time systematics from SCETlib at the anchor: `Jnf` (n_f identified at `nfmatch` = 1 GeV), `Jbt` (b_T ≥ 0.2 fm),
  `direct_nf`, `none`; default `Jnf+Jbt`. No μ0 variation, no k-form, no double-counting guards (Luca).
- `data/lattice_aswz_data.{npz,json}`: data only (bitwise the phase-3 arrays; md5 of the six author files).
- `lattice_cs_chi2.py` (table term) untouched: still the validation reference.

### 2. Validation

| check | result | evidence |
|---|---|---|
| V1 kernel vs `qT::Gamma_nu` class (analytic), 21 points, anchor + 3 displaced (α_s 0.114–0.122, TNPs ±2, λ4_ν < 0) | ≤ 2.8e-16 (full and NP-off) | [test_gnu_points_P53.json](test_gnu_points_P53.json) |
| V1 vs the design prototype (12 printed digits) / its clad gradient | 4.9e-13 / 4.5e-11 rel | same |
| V1 n_f = 4 alternative vs the class (n_f 4, α_s^(5)(1 GeV) at 1 GeV), μ = 1 and 2 GeV | 0 | [test_nf_alt.json](test_nf_alt.json) |
| V1 **new pert vs the OLD table** | **−2.3e-4 … +1.88e-3** (≤ 0.019 σ_lat) | [test_gnu_points_P53.json](test_gnu_points_P53.json) |
| V1 class with the EXACT RGE vs the old table | 5e-14 | same |
| V2 snapshot bitwise == first loaded rule (4-bin test cache; and the y25 cache in NCHK) | status 1 | same, [logs/NCHK.log](logs/NCHK.log) |
| V2 rule replay bitwise unchanged across an interleaved `gamma_nu_points` call; live `sigma_grad` likewise | 0 | P53 json, [logs/stage0_test_gamma_nu_points.log](logs/stage0_test_gamma_nu_points.log) |
| V3 clad gradient / Hessian vs Richardson FD (4 points, P = 24 and 53) | ≤ 5e-9 / ≤ 4e-8 rel | P24 / P53 json |
| V3 Jacobian & Hessian outside {α_s, CS TNPs, np_gnu_*}; TNP–TNP block | exactly 0 | same |
| V3 term through TF (tape gradient, nested-tape Hessian, fwd-over-rev hessp) vs Richardson FD | 1.4e-12 / 9.4e-11 / 2.4e-16 | [test_term.json](test_term.json) |
| V4 new χ² == old term's formula with the table pert replaced by SCETlib's (5 λ points × 3 α_s × 2 TNP settings) | 5.8e-16 rel | same |
| V4 lattice-only minimum on SCETlib's kernel vs the design | χ² 6.7032, λ2_ν 0.18553, λ4_ν −0.005969 (design 6.703 / 0.1855 / −0.00597) | same |
| V5a loss at LATFULL8's vector, new SCETlib build + old term − LATFULL8's stored NLL | −3.1e-11 | [nativecheck.json](nativecheck.json) |
| V5b data+BB+constraint part, new-term config − old-term config | 0 (bitwise) | same |
| V5c ΔNLL total (new term − old term) at LATFULL8's point | +0.274 | same |
| V6A p_full seen by the term − p_full the param model builds (53 entries, blinding armed) | 0 | same |
| V6B term's α_s vs the map on the blinded internal x: armed differs / disarmed equal | True / True | same |
| V6C AD vs FD of χ²_lat in x (α_s, λ2_ν, TNP_ν, TNP_cusp; λ4_ν) | ≤ 5.5e-9; 6.7e-5 (λ4_ν: FD step-limited, 1e-12 with Richardson offline) | same |
| V6D term gradient outside the 5 kernel parameters | exactly 0 | same |
| V6E kernel snapshot vs the y25 cache's first rule, in the fit process | status 1 (bitwise) | same; also printed in every LATB/ASIMNAT log |
| V7 Asimov closure (ASIMNAT: expected toy, `ydata=asimov offset=0`, τ 8, start α_s θ +1, λ2_ν θ −0.5, λ4_ν θ +0.01, θ_γν +1, θ_cusp −1) | **PASS**: every θ back to 0 within 7.2e-7 (α_s 0.11800000094), EDM 4.1e-11, NLL −2e-10 | [asimov_closure.json](asimov_closure.json), [logs/ASIMNAT.log](logs/ASIMNAT.log) |

**Physics read.** The native term is the old term's construction with exactly one thing changed — the kernel — and that
kernel is now provably the one the replayed cross section uses (bitwise snapshot check, same `p_full` tensor). V4 shows
the new χ² equals the old formula with SCETlib's pert to 6e-16, so every difference to LATFULL8 is the kernel swap (§3)
and the SCETlib-native n_f row (§4).

### 3. Why the shipped table differed: exact vs analytic RGE (Luca's question 1)
- **The fit can only be analytic.** The AD path refuses anything else: `DrellYan::_ad_config()` throws "only available
  for analytic RGE solutions" unless `_ad_rge_type == RGE_solution::analytic` (`py/qT/DrellYanAD.cpp`, ~l. 569), and the
  AD kernel's coupling `ad::alphas_run` is the fixed-n_f analytic solution (`ad_kernel.hpp:248`). `cache.conf` records
  `alphas_solution = rge_solution = analytic`. So every AD cache and every fit uses the analytic RGE.
- **The table was exact because of the evaluator it came from.** `lattice_aswz_inputs.npz:pert` was built by
  261006 `build_inputs.py` → 260923-scetlib-kernel-fit `kernel_fit.pert_tables()` → 260923-conventions-map
  `our_cs_kernel.py`, a numpy/scipy re-implementation that integrates the running with `solve_ivp` and the cusp with
  `quad` (its docstring: "Running and the cusp integral are solved numerically ("exact")"). It was written that way
  because (i) SCETlib's `Gamma_nu` has no Python binding, so a standalone evaluator was needed, and (ii) it had to also
  produce the n_f = 4 "lattice scheme" with α_s decoupled at m_b, which SCETlib's fixed-n_f `RunningCoupling` cannot do;
  a numerical ODE handles both schemes the same way.
- **Was it checked against `cache.conf`? Yes, and the gap was known and accepted, but not carried forward.** The
  conventions-map test driver (`driver/gamma_zeta_driver.cpp`, `GZ_EXACT=0/1`) compared `our_cs_kernel` against SCETlib's
  `Gamma_nu` in both modes: exact 5e-11, **analytic ("fit default") 1.88e-3, tol 3e-3, PASS**
  (260923-conventions-map/test_our_cs_kernel.txt; its convention table also lists "analytic solution" for the fit). At
  the time the table was frozen at α_s = 0.118 and 2e-3 is 0.02σ_lat, so this was judged negligible. Two things were
  then lost: the plugin docstring quoted only the exact-mode "5e-11", and when the term became α_s-live (phase 2/3)
  nobody re-checked the **slope**: ∂γ_ζ/∂α_s(m_Z) is −2.67…−2.79 (SCETlib) vs −2.93…−3.03 (table) on the plateau,
  **−6 % to −8.6 % for b_T ≥ 0.18 fm** (−20 % at 0.15 fm, where the slope crosses zero).
- **Impact** (cache-free Newton from LATFULL8, the kernel swapped at fixed (old) covariance, row K of §6):
  **Δ`alphaS` = −0.020σ_NOM at LATFULL8's point** (λ4_ν +0.04σ). Evaluated instead at α_s = 0.118 (cache-free) it is
  −0.006σ; the design's first-order estimate was ≈ −0.004σ. The difference is the α_s-dependence of the slope mismatch.

### 4. The SCETlib-native n_f systematic (Luca's decision 2) — 4.6× smaller than the old one
- Alternative kernel (design §6.3): our n_f = 5 kernel at μ = 1 GeV, evolved to 2 GeV with the n_f = 4 cusp, α_s^(4)
  **identified** with α_s^(5) at 1 GeV — all from `gamma_nu_points(nf=4, mu_match=1)`.
- The point shift is **−0.00920, flat in b_T** (μ0 ≥ 1 GeV everywhere), against **−0.0423** in the old table, which
  decoupled α_s at m_b(m_b) = 4.18 GeV (3-loop MSbar). The difference is the coupling in the 1→2 GeV n_f = 4 evolution:
  decoupled, α_s^(4)(1 GeV) = 0.461 vs α_s^(5)(1 GeV) = 0.407 (+13 %, 260923-conventions-map §3), and the cusp integral
  scales with it. Identified at 1 GeV, only the β/cusp coefficients' n_f dependence remains. The design's expectation
  ("a few % of the shift") was wrong; the definition choice is a factor 4.6.
- Mapped onto (λ2_ν, λ4_ν) (`Jnf`): d = (−0.0040, +0.00017) vs the old (−0.0179, +0.00075), i.e. 0.10 / 0.05 σ_stat.
  With n_f identified at 2 GeV the shift is exactly 0 (the row is then empty).
- Impact on `alphaS`: ≤ 0.0004σ_NOM in every variant (table §6). It does not matter for α_s; it is a convention question
  for the theorists (Q1).

### 5. The lattice authors' MSbar kernel at μ = 2 GeV (ASWZ, arXiv:2402.06725) and whether we compare consistently
From the paper (text in 260923-conventions-map/papers/2402.06725.txt; Eqs. 1–8, Suppl. Sec. D–E):
- **The data points** are γ_q^MS(b_T, μ = 2 GeV) = 2 d ln f/d ln ζ, extracted from quasi-TMD wave-function ratios,
  renormalised RI/xMOM → MSbar, with the perturbative matching correction δγ^MS at **"b_T-unexpanded resummed NNLO"
  (uNNLL)** order plus a **leading-renormalon subtraction (LRR, N_m = 0.552 for n_f = 4)**, in **n_f = 4** QCD (2+1+1
  HISQ sea), with **α_s(μ0 = 2 GeV) = 0.293, n_f = 4**. Per-ensemble, with the discretisation artefact k1·a/b_T (+k2).
- **Their perturbative kernel D_res** enters ONLY their parametrisation curve, not the data: D_res(b*, μ) = ∫_{μ_b*}^{μ}
  Γ_cusp + d[α_s(μ_b*)], μ_b* = 2e^{−γE}/b*, b* = b_T/√(1 + b_T²/B_NP²) with B_NP = 2 GeV; at **N3LL**: Γ_cusp to 4 loops
  (5-loop approximated), the non-cusp d to 4 loops (d0 = d1 = 0, d2, d3), 4-loop running, and the cusp kernel K(μ, μ0) in
  the **analytic, re-expanded** form (their Eq. 33), n_f = 4, α_s(2 GeV) = 0.293.
- **Our comparison**: our γ_ζ (SCETlib N3+0LL, n_f = 5, analytic RGE, boundary at μ0 = ((b0/b_T)⁴ + 1 GeV⁴)^¼, sextic b*
  in L_b, NP at bare b_T, d through the 3-loop constant) vs their DATA points, never vs their D_res.
  - Consistent: scheme (MSbar), scale (μ = 2 GeV), normalisation (γ_q = γ̃_ζ = ½γ̃_ν, coefficient-verified in
    260923-conventions-map), and the fact that their D_res (and its truncation) plays no role.
  - Not identical, and carried or open: (a) **n_f = 4 vs 5** — our n_f systematic (§4); (b) **the α_s inside the data**:
    the matching correction uses α_s^(4)(2 GeV) = 0.293 (≈ α_s(m_Z) = 0.1168 under m_b decoupling, 260923), fixed,
    while our term is α_s-live; the data's own ∂γ/∂α_s is not given in the paper (Q3); (c) the order of the matching
    (uNNLL + LRR) is the authors' systematic, already in their errors.
  - Our RGE truncation (analytic) and theirs (analytic K, Eq. 33) are the same kind, but that only concerns D_res.
- **Verdict: yes, the comparison is consistent with their convention** up to (a) and (b); (a) is a ≤ 0.0004σ_NOM effect
  and (b) is not quantifiable from the paper.


### 6. Impact table (Newton from LATFULL8, at its blinded point, exact term derivatives; NCHK2)
Caveats: Newton = one quadratic step from LATFULL8 with LATFULL8's covariance and the lattice block swapped (old term →
variant); shifts are vs LATFULL8 in σ_NOM. The default row is confirmed by the full fit LATB8 (§7) to 0.002σ. Rows
differ from each other by the stated quantity only.

| variant (native term unless stated) | Δ`alphaS` vs LATFULL8 /σ_NOM | σ ratio vs NOM | λ2_ν (shift/σ) | λ4_ν (shift/σ) |
|---|---|---|---|---|
| LATFULL8 itself (old table term, exact RGE, old Jnf + Jbt) | 0 | 0.979 | 0.0357 | 0.00981 |
| K: kernel swap only (SCETlib analytic-RGE kernel, OLD covariance) | **−0.0196** | 0.973 | 0.0358 (+0.00) | 0.01001 (+0.04) |
| **native default `Jnf+Jbt`** | **−0.0256** | 0.970 | 0.0359 (+0.01) | 0.01095 (+0.23) |
| native `Jnf` (b_T window off) | −0.0260 | 0.969 | 0.0363 (+0.02) | 0.01107 (+0.25) |
| native `Jbt` (n_f systematic off) | −0.0259 | 0.970 | 0.0360 (+0.01) | 0.01098 (+0.24) |
| native `none` (stat only) | −0.0262 | 0.969 | 0.0363 (+0.02) | 0.01111 (+0.26) |
| native `direct_nf+Jbt` | −0.0258 | 0.970 | 0.0359 (+0.01) | 0.01095 (+0.23) |

**The three impacts Luca asked for** (Δ`alphaS` in σ_NOM; Δλ in units of their postfit σ):

| question | Δ`alphaS` | Δλ2_ν, Δλ4_ν |
|---|---|---|
| b_T window on vs off (`Jnf+Jbt` − `Jnf`) | **+0.0004** | −0.01σ, −0.02σ |
| SCETlib-native n_f systematic vs none (`Jnf+Jbt` − `Jbt`) | **+0.0003** | 0.00σ, −0.01σ |
| (n_f: direct shift vs J-mapped) | −0.0002 | 0.00σ, 0.00σ |
| analytic vs exact RGE (K − LATFULL8: kernel swap at fixed covariance) | **−0.020** | +0.00σ, +0.04σ |
| rest of old → native (n_f redefinition + rows recomputed on SCETlib's kernel; native − K) | −0.006 | +0.01σ, +0.19σ |

- σ(`alphaS`) changes by < 1 % in every row.
- Cache-free cross-check ([newton_decomp.json](newton_decomp.json); both terms at α_s = 0.118 instead of the blinded
  point): K −0.006, native −0.0095; window +0.0004, n_f +0.0001. The systematic rows agree; the kernel row is 3× larger
  at the real point, because the new − old kernel difference has an α_s-dependent slope (§3), so its size depends on
  where α_s sits. The at-the-point numbers are the ones the fit reproduces (§7).

### 7. The fit: LATB5 → LATB8 vs LATFULL8 / LATLIVE8Y / NOMSTIFF
Caveats: real data, blinded (σ_NOM units). Identical card, cache (y25 subset), priors (44, checked in each log), wall
(τ 8), minimiser; LATB warm-started from LATFULL8's full vector (flat seed), τ 5 then τ 8 + Hessian. LATB differs from
LATFULL8 ONLY in the lattice term (and the SCETlib build, replay-identical: V5a). The "lattice Δχ²" columns are at
α_s = 0.118 with each fit's λ and TNPs (not the live term, which stays inside the NLL). LATFULL8 differs from LATLIVE8Y
by `pert=live` (TNPs live) and dropping μ0-scale (261006 §7).

| | NOMSTIFF | LATLIVE8Y | LATFULL8 (old term, TNP-live) | **LATB8 (native term)** | LATB5 (τ 5) |
|---|---|---|---|---|---|
| Δ`alphaS` / σ_NOM | 0 | −0.042 | −0.085 | **−0.113** | −0.112 |
| Δ`alphaS` vs LATFULL8 | +0.085 | +0.043 | 0 | **−0.027** (Newton −0.026) | −0.027 |
| σ(`alphaS`) / σ_NOM | 1 | 0.985 | 0.979 | **0.972** | – |
| EDM | 3e-14 | 2.1e-17 | 1.2e-17 | **5.2e-17** | – |
| λ2_ν | 0.064 ± 0.023 | 0.034 ± 0.030 | 0.036 ± 0.030 | **0.036 ± 0.030** | 0.036 |
| λ4_ν | 0 (frozen) | 0.0080 ± 0.0053 | 0.0098 ± 0.0056 | **0.0111 ± 0.0054** (+0.24σ; Newton 0.0110) | 0.0111 |
| TMD λ2 / λ4 / δλ2 | 0.026 / 0.088 / −0.0041 | 0.050 / 0.084 / −0.0080 | 0.048 / 0.078 / −0.0078 | **0.049 / 0.074 / −0.0078** | same |
| θ_γν, θ_cusp | +0.69, −0.15 | +0.44, −0.09 | +0.31, −0.07 | **+0.30, −0.06** | same |
| active wall face | L2(\|Y\|=2.5) = 0 | same | same | **same** | same |
| NLL total | 376.615 | 376.079 | 376.481 | **376.675** | 376.675 (τ 5) |
| lattice Δχ², native kernel, α_s 0.118 | 17.15 | 11.15 | 9.71 | **9.48** | 9.47 |
| lattice Δχ², old table `Jnf+Jbt`, α_s 0.118 | 12.24 | 9.62 | 9.01 | 9.09 | 9.09 |

Evidence: [compare.json](compare.json) ([logs/compare.log](logs/compare.log), task copy
[scripts/compare.py](scripts/compare.py)); fit logs [logs/LATB5.log](logs/LATB5.log), [logs/LATB8.log](logs/LATB8.log);
fitresults `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261007_lattice_term_native/fitresults_LATB{5,8}.hdf5`.

**Physics read.**
1. Computing the lattice kernel from SCETlib itself, with the cache's analytic RGE and every kernel parameter shared with
   the Z prediction, moves `alphaS` by **−0.027σ_NOM** relative to the table term (σ −0.7 %), as predicted (−0.026).
   Net vs NOMSTIFF: −0.11σ_NOM. The NP picture is unchanged: λ4_ν interior (+0.011 ± 0.005, +0.24σ), λ2_ν ≈ 0.036, same
   single TMD face, lattice Δχ² ≈ 9.5 for 2 dof at α_s 0.118.
2. Three-quarters of the move is the RGE truncation of the kernel (−0.020σ): the exact-RGE table had an α_s slope 6–9 %
   steeper than the kernel the cross section uses, so the old term pulled α_s with the wrong lever arm. This was a real
   inconsistency between the two halves of the likelihood, now removed by construction (bitwise snapshot check).
3. The lattice systematics are irrelevant for α_s: n_f (native) and the b_T window each move it by ≤ 0.0004σ, and
   stat-only by 0.0006σ. The n_f definition change (m_b decoupling → identified at 1 GeV) shrinks that systematic 4.6×
   but changes α_s by < 0.006σ (with the row recomputation).

### 8. Draft questions for the theorists (NOT sent; Luca decides)
Context line for the email: *we now fit the ASWZ per-ensemble points simultaneously with our Z data, with our own
SCETlib N3LL CS kernel (n_f = 5, α_s-live, CS TNPs live) + our NP form, k1·a/b_T profiled; the impacts below are on our
α_s(m_Z) in units of its uncertainty (Newton steps at our nominal fit, cross-checked by a full fit).*

1. **n_f scheme.** Your kernel is computed in n_f = 4 QCD (2+1+1, α_s(2 GeV) = 0.293), ours in fixed n_f = 5 run from
   α_s^(5)(m_Z). We currently assign a systematic from an n_f = 4 alternative of our kernel: our n_f = 5 kernel at
   1 GeV, evolved to 2 GeV with the n_f = 4 cusp, and the two couplings *identified* at 1 GeV. That shift is −0.009,
   flat in b_T; decoupling α_s at m_b instead gives −0.042, and identifying at 2 GeV gives 0. (a) Is a b_T-independent
   offset of this size the right way to think about the n_f = 4 vs 5 mismatch for the MSbar CS kernel at 2 GeV, or is
   there a preferred matching (scale, decoupling) we should use? (b) Would you consider it covered by your quoted errors?
   *Measured impact (Newton at our nominal):* with vs without this systematic Δα_s = +0.0003σ, λ shifts ≤ 0.01σ;
   direct offset vs λ-mapped −0.0002σ; switching from m_b decoupling to 1 GeV identification (with the rest of the
   covariance recomputation) ≤ 0.006σ.
2. **b_T window.** We currently add a systematic from dropping your points with b_T < 0.2 fm (b_T ≈ a … 2a, where
   a/b_T artefacts are largest and the points mostly calibrate k1). Is that a sensible robustness check, or do you
   recommend a minimum b_T (in fm or in units of a) for using the points quantitatively? Should k2·a²/b_T² be kept
   available? *Measured impact:* Δα_s = +0.0004σ (with vs without the window systematic), λ2_ν / λ4_ν ≤ 0.02σ.
3. **Your MSbar conventions and the α_s in the data.** We read the data points as γ_q^MS(b_T, μ = 2 GeV) in n_f = 4
   with uNNLL + LRR matching evaluated at α_s^(4)(2 GeV) = 0.293 (≈ α_s(m_Z) = 0.1168 with standard decoupling), and
   compare them to our kernel at μ = 2 GeV, γ_q ≡ ½γ_ν (coefficient-verified). (a) Is that right, including that the
   points do not depend on your D_res / B_NP? (b) Since we let α_s float in our kernel, how do the data points depend on
   the α_s used in the matching correction (∂γ̂/∂α_s(2 GeV), or the points at e.g. 0.28 / 0.31)? (c) Is the matching
   order (uNNLL vs NLL/NNLO) part of your quoted errors? *Measured impact of our own perturbative-kernel convention
   (analytic vs exact RGE, same N3LL): −0.020σ — the largest single item, i.e. α_s is ~50× more sensitive to how the
   perturbative kernel is truncated than to the n_f / b_T systematics.* The α_s-dependence of the
   data is not modelled; its impact is unknown until (b) is answered.

---

## Findings

1. SCETlib's AD kernel can evaluate γ_ν(b_T, μ) outside the cross section with exact clad gradient and Hessian, from a
   `GlobalData` snapshot that is bitwise the one stored in the cache rules; 21 points with full Hessian cost 3.4 ms. —
   (evidence: [test_gnu_points_P53.json](test_gnu_points_P53.json), [nativecheck.json](nativecheck.json))
2. **The shipped lattice pert table was the exact-RGE kernel; every AD fit is analytic-only** (`_ad_config` refuses
   anything else). The slope ∂γ_ζ/∂α_s differs by −6 … −9 % on the plateau, and swapping the kernel moves `alphaS` by
   −0.020σ_NOM at LATFULL8's point. — (evidence: Result §3, §6)
3. **The SCETlib-native n_f alternative (α_s^(4) identified with α_s^(5) at 1 GeV) shifts the points by −0.0092, 4.6×
   less than the m_b-decoupled one (−0.042).** The n_f systematic is still irrelevant for α_s (≤ 0.0004σ). — (evidence:
   [test_nf_alt.json](test_nf_alt.json), Result §4)
4. Native term in the fit: LATB8 −0.027σ_NOM vs LATFULL8 (Newton −0.026), λ4_ν +0.24σ; b_T window and n_f systematics
   ≤ 0.0004σ each. — (evidence: [compare.json](compare.json), Result §6–7)
5. Blinding: the term reads `p_full` from the param model's own `scetlib_full_vector_tf` (difference 0 in all 53
   entries, armed), never the blinded internal x. — (evidence: [nativecheck.json](nativecheck.json))
6. For knowledge/ (rabbit + SCETlib-AD): a Newton step that swaps an α_s-live term must be evaluated at the fit's own
   (blinded) point, inside a job; at Δα_s = 0 it was 3× too small here (−0.006 vs −0.020σ), because the swapped
   kernels differ in their α_s slope. — (evidence: Result §6)

---

## Open questions

- **The data's own α_s dependence** (ASWZ matching at α_s^(4)(2 GeV) = 0.293) is not modelled while our kernel is
  α_s-live; impact unknown (theorist Q3b).
- `scetlib_tf_native.py` is stale for CS NP forms other than tanh_2 (design task); not touched.
- The AD kernel always runs the analytic coupling, but `_ad_config` checks only `rge_solution`: a runcard with
  `alphas_solution = exact` would silently get analytic running in the AD path. Not chased (our caches are analytic).
- `LatticeCSTerm` refuses a `CompositeParamModel` (the saturated test); a saturated GoF with the native term needs a
  small extension.
- Retire the theory arrays of `lattice_aswz_inputs.npz` and the table term once Luca accepts the native term (design
  step 7); the Gaussian 1D/2D lattice cards are now doubly obsolete.
- V6C: AD vs FD in λ4_ν was 6.7e-5 in the job (FD step-limited; 1e-12 with Richardson offline).
