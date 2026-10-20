---
title: Gen-level cold NOLAT/LAT fits on unfolded real data
slug: 261017-gen-cold-fits
study: ct18z-nominal-fits
status: done          # active | done | paused | abandoned
created: 2026-10-17
updated: 2026-10-19
owner: study-worker
---

# Gen-level cold NOLAT/LAT fits on unfolded real data

**Task:** What do the cold NOLAT and LAT fits (trust-constr + hard NPDomainConstraints, no NP priors; LAT = ASWZ lattice chi2 at tau=8) give at GEN level on the unfolded real CT18Z data, and how do they compare with the two reco fits of ct18z-nominal-fits/261015-cold-tc-fits?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-10-19 05:30) — DONE

- **Answer:** both gen-level fits converge cold. Each one ends on the same active faces as its reco counterpart. The lattice
  does the same thing at gen as at reco: it moves the NP damping from CS to TMD, costs 2ΔNLL = 11.0 (reco 13.5) and
  moves α_s by +0.35σ (reco +0.21σ). Gen − reco Δα_s, blinded, same frame: NOLAT −0.61σ_reco, LAT −0.42σ_reco.
  σ(α_s) at gen is 1.17 / 1.18 ×1e-3 (reco 1.09 / 1.14). The ptV shape fails at gen too (ptVGen saturated 52.5 / 60.3
  for 20 bins). See the Result table.
- **Next action:** none for this task. See the open questions.
- **Blocking on:** nothing.
- **Running:** nothing. All four rabbit passes exited 0.

---

## Setup (decided 2026-10-17)

- **Input (gen-level card):** `/ceph/.../261009_ad_genlevel_iter0/sigmaUL_iter0_ad_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_adcorrAV_alphaS.hdf5`
  — σ_UL (helicitySig:0) of the **iteration-0 real-data unfolding** `261001_unfolding_data_iter0` (setupRabbit `--realData`,
  rabbit `-t 0` → toys [0]), 20 ptVGen × 10 absYVGen = 200 bins, data covariance (`hdata_cov_inv`), 6 card nuisances
  (`mb_fo`, `pdfMSHT20m{b,c}range{SymAvg,SymDiff}`, `pythiaew_ISR_Corr`); every template the AD model replaces excluded.
  Same card as GEND/GENDF (z-data-unfolding/261009-ad-genlevel-fit, 261013-gen-reco-alphas-delta).
  - **Why iter0 and not the later 5-|Y|-bin card** (`261013_ad_genlevel_y5`, from `261012_unfolding_y5pairs`): iter0 is the
    nominal (HEAD-binning, main-tree histmaker 261001) unfolding; the y5 one is an exploratory binning from a worktree hack
    (`WRemnants-y5-reco10`, uncommitted `edges_yll`) whose adoption is "awaiting Luca" in z-data-unfolding START HERE.
    The iteration question is settled (261008-iteration: converged, one iteration moves σ_UL ≤ 0.13σ) → iteration 0.
    The 261013_unfolding_* dirs are A/B variants (bb-stat options, smearing splines, trust-exact, axlim), not nominals.
- **AD cache:** `scetlib_ad_caches/pdf62_y35_260921_y25` — the SAME cache as the reco nominal fits; `gen_level=1` folds the
  770 cache bins onto the 200 gen bins (`fold_for` checks coverage; GEND ran on this card+cache).
- **Model tokens:** `gen_level=1 threads=128`, otherwise defaults (WRemnants 74c7e3e3 ⊃ cc3859f4: no NP λ prior; GEND's
  explicit `prior_sigmas=...lambda2=1,lambda4=1,delta_lambda2=1` NOT used).
- **Likelihood:** `--covarianceFit --noBinByBinStat --noPostfitProfileBB` (gen-level: covariance χ²; the last is the
  known `--externalPostfit` + no-BB crash workaround).
- **Minimisation = fitterAD.sh `--constraints` [+ `--lattice`] verbatim** (NPDomainConstraints margin=0, trust-constr,
  V2 tolerances; LAT: LatticeCSTerm defaults = LATFROZ_V3, τ = 8). fitterAD.sh itself cannot run a gen card (hardcodes
  `-m Project ch0 ptll`, no `--covarianceFit`), so the same flags are composed in [scripts/common.sh](scripts/common.sh);
  fitterAD.sh untouched.
- **Two passes** ([scripts/chain.sh](scripts/chain.sh)): pass 1 [run_fit.sh](scripts/run_fit.sh) = COLD main fit, no
  preconditioner, `--noHessian --noEDM`; pass 2 [run_pf.sh](scripts/run_pf.sh) = `--externalPostfit <pass1> --noFit`
  + `--minimizerWarmStart auto` + full-scope spectral preconditioner (only the warm saturated sub-fits minimise) +
  `--doImpacts --globalImpacts --globalImpactsDisableJVP --saveHists --computeHistErrors` + mappings
  `BaseMapping`, `Project chSigmaUL ptVGen`, `Project chSigmaUL absYVGen` + `--computeSaturatedProjectionTests`.
- **Blinding:** `--blindingFrame data` in both passes = the frame the reco fits get from `auto` (integer data_obs);
  the σ_UL card is non-integral (auto → mc). Same mechanism as GENDF (261013-gen-reco-alphas-delta). Only differences
  and σ are ever computed; no α_s value or offset.
- **rabbit:** new local worktree `/work/submit/lavezzo/rabbit-all3-bf`, branch `all3-bf-local` ece1d16 = all3-local
  d573c1d (warm start + trust-constr precond + face-held impacts) + cherry-pick of 196bfca (`--blindingFrame`, clean).
  Needed because all3-local lacks `--blindingFrame`. Not pushed.
- **SCETlib:** gamma-ν-points build (LatticeCSTerm). **Gate:** shared mem_gate, 260 GB, MAXRUN 2.
- **Output:** `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261017_gen_nominal_fits/` (fitresults_GEN_{NOLAT,LAT}{,_PF}.hdf5, logs).

---

## Log

<!-- Newest first. What was tried, what happened, why — with an evidence path. -->

### 2026-10-17
- 10:55 launched both chains (exact commands: [logs/launches.txt](logs/launches.txt)). GEN_NOLAT out of the gate at once
  (pid in launches.txt); GEN_LAT waits for a run slot.
- GEN_NOLAT: the cache load took ~2.4 h (10:55 → first iteration ~13:20; node load ~730/768 cores; NOLAT_PF loaded in
  22 min yesterday). Log confirms `Blinding frame forced to 'data'`, `Blind parameter alphaS`. Start loss 20105.49
  (GEND cold start was 19614 with priors+lattice), it 1 12955.98; it 48 (16575 s) loss 113.19244, optimality 1.5e-6,
  barrier 1.3e-6, no violation. RSS 232 GB.
- NB rabbit writes `fitresults_<PF>.hdf5` already at the start (51 kB at 13:22): chain.sh's `-s` check cannot tell a
  crashed pass 1 from a finished one → check the log's `exit 0` + minimizer status by hand before trusting pass 2.
- **18:51 GEN_NOLAT pass 1 DONE**, exit 0: trust-constr status 1 (gtol), nit 57, nfev 49, 19703 s (5.5 h) of
  minimisation (~10 min/iteration in the tail on the loaded node), optimality 3.3e-9, constr_violation 0, barrier 1.0e-8,
  final loss 113.19243145. Constraint values / multipliers (row order of NPDomainConstraints): 0.0305 / ~0,
  **8.1e-10 / −26.87**, 0.171 / ~0, 0.00288 / ~0, 0.129 / ~0, **1.5e-9 / −3.33** → two active faces; with reco NOLAT's
  multipliers (−32.4 on λ2_ν ≥ 0, −4.10 on the TMD cubic at |Y| = 2.5) these are very likely the same two rows — labels
  read from the postfit's `[constraints] active:` lines. Full saturated test: 2ΔNLL 226.38, ndof 194 (200 bins − 6
  free model params), p 5.55 % (log). (evidence: logs/GEN_NOLAT.log)
- 18:51 GEN_LAT out of the gate (pid 4126027); GEN_NOLAT_PF queued in the gate behind other workers' jobs.
  Row order of NPDomainConstraints (from the log's `constraint_labels`): [λ4_ν ≥ 0, λ2_ν ≥ 0, L2(|Y|=0), cubic(|Y|=0),
  L2(|Y|=2.5), cubic(|Y|=2.5)] → GEN_NOLAT's active rows are **λ2_ν ≥ 0 (−26.87)** and **cubic(|Y|=2.5) (−3.33)**,
  exactly reco NOLAT's two faces (−32.4, −4.10).
- **20:49 GEN_LAT pass 1 DONE**, exit 0: cache load 25 min (node quieter), status 1 (gtol), nit 46, nfev 43, 5754 s
  (1.6 h), optimality 7.4e-9, violation 0, final loss 118.68767522. LatticeCSTerm armed (21 ASWZ points, τ = 8),
  frame forced to data. Constraint values [0.00504, 0.0792, 0.0178, 0.1275, **2.0e-9**, 0.1275], multipliers ~0 except
  **L2(|Y|=2.5): −5.09** → one active face, the same as reco LAT (−6.41). Full saturated 2ΔNLL 237.38 / 194, p 1.83 %.
- Lattice cost at gen level: 2 × (118.68768 − 113.19243) = **10.99** (reco 13.51), for the 2 lattice-constrained CS λ.
  Both full-saturated values include the lattice χ² in LAT's case (as on reco).

### 2026-10-18
- GEN_NOLAT_PF: out of the gate 2026-10-17 23:50 (waited 5 h for a run slot), exit 0 at 06:16. Loaded the pass-1
  minimum exactly (Iteration 0 loss 113.19243145098531 = pass 1). Faces (face-held postfit): **λ2_ν ≥ 0, multiplier
  26.87, release ΔNLL 14.06** (strongly binding; reco 15.63) and **TMD cubic at |Y| = 2.5, multiplier 3.33, release
  ΔNLL 4.87** (reco: release "inf"). edmval on the faces 1.6e-16. Full saturated 226.38/194, p 5.55 %. Linear χ²
  216/200 (p 21 %; the χ² rabbit prints as "chi2/ndf"), ptVGen projection linear 31/20, absYVGen 5/10.
  - **ptVGen saturated projection: q = 52.50 / 20, p 0.01 %.** Sub-fit (warm start + spectral precond, 73 params):
    status 2 (xtol, tr_radius 1e-11) after 155 it / 4.9 h, optimality 3.3e-7, violation 0 → converged for practical
    purposes (cf. reco LAT's status-2 at 6.6e-4 was off by only 1.7e-4 in q). Saturated covariance: Cholesky failed
    (not positive definite) — only the q is used.
  - **absYVGen saturated projection: q = 16.62 / 10, p 8.3 %.** Status 1, 26 it, 41 min, optimality 1.2e-9.
  - save_hists (both sub-fits) 22047 s = 6.1 h of the 6.4 h pass.
- GEN_NOLAT deliverables ([scripts/deliverables.sh](scripts/deliverables.sh), all rc 0): [GEN_NOLAT/impacts/](GEN_NOLAT/impacts/)
  (traditional face-held + global, grouped + ungrouped), [GEN_NOLAT/postfit/](GEN_NOLAT/postfit/) (ptVGen, absYVGen),
  [GEN_NOLAT/np_functions/](GEN_NOLAT/np_functions/). σ(α_s) = 1.17e-3 (reco NOLAT 1.09e-3). Traditional grouped
  (×1e-3): Data stat 1.05, NP 0.89 (γ_ν 0.85, F_eff 0.29), pdfEig 0.77, TNP 0.69, b/c masses 0.45, EW 0.25, resumScale 0.23.
  NB at gen level "Data stat." = the whole unfolded-data covariance (data stat + the unfolding's experimental,
  lumi and response-level theory nuisances profiled into it), not data statistics alone.
- Blinded, same frame: α_s(GEN_NOLAT) − α_s(RECO_NOLAT) = **−0.61 σ_reco** (−0.33 θ). [compare_partial.json](compare_partial.json).
- GEN_LAT_PF: out of the gate 10:56, exit 0 at 18:17 (7.3 h; save_hists 7.0 h). It reloaded the pass-1 minimum. One active
  face, **L2(|Y| = 2.5), multiplier 5.09, release ΔNLL 0.34 → WEAKLY binding** (reco LAT 0.46). The α_s interval along
  that face is one-sided, so the face-held σ is a lower-side curvature, as on reco.
  - Full saturated 237.38/194, p 1.83 %. Linear χ² 219/200 (p 17 %), ptVGen linear 32/20, absYVGen 6/10.
  - **ptVGen saturated projection q = 60.33 / 20 (p 6.3e-6).** Sub-fit status 2 (xtol), 182 it / 5.4 h, optimality 1.8e-6.
  - **absYVGen q = 16.37 / 10, p 9.0 %.** Status 2, 61 it / 1.1 h, optimality 4.9e-7.
  - The saturated covariance again failed Cholesky (q only).
- GEN_LAT deliverables: all rc 0. NP overlays: [np_gen_vs_reco_NOLAT/](np_gen_vs_reco_NOLAT/), [np_gen_vs_reco_LAT/](np_gen_vs_reco_LAT/),
  [np_GEN_NOLAT_vs_LAT/](np_GEN_NOLAT_vs_LAT/). Four-way numbers: [compare.json](compare.json) ([scripts/compare.py](scripts/compare.py)).

---

## Result

**Caveats first.**
- **Blinding.** All four fits are in the real-data blinding frame. Reco gets it from `auto` (integer data). Gen gets it
  from `--blindingFrame data`, confirmed in both gen logs. The param `alphaS` has the same name and no additive scale,
  so stored differences are physical differences. No α_s value or offset was computed or printed. The α_s columns
  below are differences only.
- **Not nested; different likelihoods on the same events.**
  - Reco: 780-bin ptll×yll Poisson card, 3673 nuisances plus bin-by-bin stat. Card 260916, histmaker 260916.
  - Gen: 200-bin σ_UL of the iteration-0 unfolding (261001, HEAD histmaker), covariance χ², 6 card nuisances.
    Unfolding-level systematics enter only through the data covariance.
  - So gen "Data stat." = the whole unfolded covariance (data stat, experimental, lumi, profiled response theory). It is
    not comparable to reco "Data stat.".
  - The two cards also come from different histmaker revisions (cf. the gen-total drift note).
  - Same AD cache, SCETlib build, model defaults (no NP prior), constraints and lattice settings (LATFROZ_V3, τ = 8).
- **GoF NLLs.** LAT's NLL and full-saturated q contain the lattice χ²; ndof counts only the bins. Gen NLLs are χ²/2 of
  the covariance fit and cannot be compared with reco NLLs in absolute terms. Only within-level differences mean anything.
- **σ(α_s) at an active face** is the face-held covariance (rabbit all3 face-held impacts). Both LAT fits sit on a
  weakly binding face (release ΔNLL 0.34 gen / 0.46 reco), so their intervals are one-sided along it.

| | RECO_NOLAT | GEN_NOLAT | RECO_LAT | GEN_LAT |
|---|---|---|---|---|
| cold minimisation (status, it, wall) | 1, 62, 7.4 h | 1, 57, 5.5 h | 1, 113, 4.8 h | 1, 46, 1.6 h |
| final NLL (reduced) | 369.7187 | 113.1924 | 376.4726 | 118.6877 |
| lattice cost 2ΔNLL (LAT − NOLAT) | | | 13.51 | **10.99** |
| active faces (multiplier, release ΔNLL) | λ2_ν≥0 (32.4, 15.6); cubic(2.5) (4.10, inf) | λ2_ν≥0 (26.9, 14.1); cubic(2.5) (3.33, 4.87) | L2(2.5) (6.41, 0.46) | L2(2.5) (5.09, 0.34) |
| full saturated q / ndof, p | 739.44/774, 81 % | 226.38/194, 5.6 % | 752.95/774, 70 % | 237.38/194, 1.8 % |
| saturated projection: ptll (reco) / ptVGen (gen) | 68.36/39, 0.25 % | **52.50/20, p 9.6e-5** | 79.11/39, 0.02 % | **60.33/20, p 6.3e-6** |
| absYVGen projection (gen) | | 16.62/10, 8.3 % | | 16.37/10, 9.0 % |
| σ(α_s) ×1e-3 (traditional total) | 1.09 | 1.17 | 1.14 | 1.18 |
| Δα_s LAT − NOLAT (same level) | | | +0.21 σ_RECO_NOLAT | **+0.35 σ_GEN_NOLAT** |
| **Δα_s gen − reco (same config)** | | **−0.61 σ_RECO_NOLAT** (−0.00066) | | **−0.42 σ_RECO_LAT** (−0.00048) |
| CS λ2_ν / λ4_ν (physical) | 0 (face) / 0.0448 | 0 (face) / 0.0305 | 0.0395 / 0.0105 | 0.0792 / 0.0050 |
| TMD λ2 / λ4 / δλ2 (physical) | 0.115 / −0.0001 / −0.0094 | 0.171 / −0.0007 / −0.0068 | 0.0455 / 0.0720 / −0.0073 | 0.0178 / 0.0425 / −0.0028 |
| traditional grouped impacts ×1e-3 (leading) | NP 0.86 (γ_ν 0.83), Data stat 0.79, pdfEig 0.71, TNP 0.65 | Data stat* 1.05, NP 0.89 (γ_ν 0.85), pdfEig 0.77, TNP 0.69, b/c 0.45 | NP 0.93 (F_eff 0.83), Data stat 0.86, pdfEig 0.79, TNP 0.77 | Data stat* 1.09, NP 0.91 (F_eff 0.81), pdfEig 0.79, TNP 0.77, b/c 0.42 |
| global grouped ×1e-3 (leading) | pdfEig 0.64, TNP 0.42, lumi 0.39, EW 0.34, stat 0.33 | stat* 0.72, pdfEig 0.70, TNP 0.47, b/c 0.34 | pdfEig 0.76, TNP 0.57, lumi 0.41, EW 0.34 (stat NaN) | pdfEig 0.77, stat* 0.60, TNP 0.59, b/c 0.32 |

\* gen "Data stat." = the full unfolded-data covariance (see caveats). In global impacts the prior-free NP λ groups
are 0 by construction (no constraint source), as on reco.

![NP functions, GEN_LAT vs RECO_LAT](np_gen_vs_reco_LAT/np_functions.png)
![NP functions, GEN_NOLAT vs RECO_NOLAT](np_gen_vs_reco_NOLAT/np_functions.png)

*NP figure caveats:* the grey "lattice fit" curve is the plotter's built-in 2506.13874 reference, not our ASWZ term.
Bands are Gaussian toys around the face-held covariance. On a curved face (NOLAT's cubic at |Y| = 2.5) they cross the
face, so the |Y| = 2.5 F_eff band is not physical there.

**Physics read.**
1. *Minimisation.* The cold trust-constr + hard-constraint recipe works at gen level unchanged: both fits reach status 1
   with optimality ≤ 7e-9. The postfit saturated sub-fits are the cost: 4.9–5.4 h for ptVGen, even warm-started and
   preconditioned. They end at status 2 (xtol) with optimality ≤ 2e-6, so q is reliable to ≪ 1e-3.
2. *The NP picture is the same at both levels.* Without the lattice, both reco and gen put the CS small-b coefficient on
   its physical bound (λ2_ν = 0, strongly binding: release ΔNLL 14–16) and the TMD large-b cubic on its |Y| = 2.5 face.
   With the lattice, both move onto the lattice CS kernel and sit on the same weak L2(|Y| = 2.5) face. Again the lattice
   moves damping from CS to TMD: the γ_ν group gives way to F_eff in the impacts at both levels.
   - The gen fits want somewhat more CS damping at small b (GEN_LAT λ2_ν = 0.079 vs RECO_LAT 0.040) and less TMD λ2.
     This is the same shift GENDF showed (0.077) with the old priors.
   - The lattice tension is smaller at gen (2ΔNLL 11.0 vs 13.5, both for the 2 lattice-constrained CS λ, ≈ 2.9σ vs 3.2σ).
3. *α_s.* Gen and reco agree within the expected spread: −0.61σ (NOLAT) and −0.42σ (LAT) in the reco σ.
   - The LAT number is identical to GENDF − LATFROZ_V3 (−0.42σ, z-data-unfolding/261013-gen-reco-alphas-delta), although
     the TMD λ have lost their unit priors since then. That attribution (mostly λ2_ν, higher at gen) applies here.
   - Without the lattice the CS sector is unconstrained on both sides and the gap grows slightly.
   - The lattice moves α_s up at both levels (+0.21σ reco, +0.35σ gen).
   - σ(α_s) is 3–8 % larger at gen than at reco.
4. *Goodness of fit.* Full fits:
   - Gen: p 5.6 % (NOLAT), 1.8 % (LAT); with the lattice χ² included in LAT.
   - Reco: p 81 % / 70 %.
   - Projections:
     - ptVGen fails badly at gen (52.5/20, 60.3/20) while absYVGen is fine (p 8–9 %). This repeats GEND's 60.4/20 and
       the reco ptll projection (68/39, 79/39).
     - Read: the model's qT shape does not describe the data at the ~3σ–4σ level at either level, and the lattice makes
       it worse by Δq ≈ 8 (gen) / 11 (reco).
   - The gen ptVGen postfit ratio sits ~3–4 % below 1 at most ptV. This is a coherent normalization offset that the
     correlated unfolded covariance allows (linear χ² 216/200, p 21 %). Diagonal error bars make it look worse than it is.

<!-- The answer, and what it means physically. State comparability caveats BEFORE the
     numbers: blinding family, Asimov vs data, PDF/order swap, card or freeze-list
     difference, excluded points. Check the read against AN-25-085 / knowledge/, not
     against the code. A number without a physics read is not a finished task. -->

---

## Findings

<!-- One line each. A finding that generalizes beyond the parent study → tell the
     orchestrator; it belongs in ../../../knowledge/. -->

1. The cold trust-constr + `NPDomainConstraints` recipe converges at gen level as it does at reco, with the same
   active faces per configuration (NOLAT: λ2_ν ≥ 0 + cubic(2.5); LAT: L2(2.5)). Evidence: logs/GEN_*.log.
2. Gen − reco Δα_s (blinded, data frame): NOLAT −0.61σ_reco, LAT −0.42σ_reco. The LAT value is identical to the old
   GENDF − V3, so the gen–reco offset does not depend on the TMD priors. Evidence: compare.json.
3. Lattice tension is smaller at gen (2ΔNLL 11.0 vs 13.5); the lattice shifts α_s +0.35σ at gen (+0.21σ reco).
4. The ptV-shape GoF failure persists at gen in both configurations (ptVGen saturated 52.5/20, 60.3/20); |Y| is fine.
5. fitterAD.sh cannot run a gen-level card (it hardcodes `-m Project ch0 ptll` and has no `--covarianceFit`); the
   gen-level equivalent lives in scripts/common.sh + run_fit.sh/run_pf.sh. Worth a `--genLevel` option (orchestrator).
6. rabbit writes `fitresults_<PF>.hdf5` already at fit start (prefit content), so a "file exists" check does not
   prove a pass finished. Evidence: 51 kB file at 13:22 while GEN_NOLAT was still iterating.

---

## Open questions

- **Blinding policy tension:** z-data-unfolding (Luca 2026-10-09) says "never publish post-fit plots of the α_s fit".
  This task made the requested postfit ptVGen/absYVGen plots (GEN_*/postfit/), as the reco study did for ptll. Decide
  whether they stay on the web.
- Both LAT fits sit on a weakly binding face: the one-sided α_s interval needs a likelihood scan to quote.
- The saturated sub-fit covariance fails Cholesky in all four gen sub-fits (q unaffected). Rabbit just warns.
- The gen ptVGen sub-fits still take ~5 h even warm + preconditioned and end at xtol (status 2). That is a rabbit cost
  issue, not a correctness one.
- The 5-|Y|-bin unfolding (261013_ad_genlevel_y5) was not used; if it becomes the nominal, rerun these two fits on it.
- New local rabbit branch `all3-bf-local` (ece1d16, worktree /work/submit/lavezzo/rabbit-all3-bf) = all3-local +
  `--blindingFrame`. Not pushed; it can be deleted once the PRs merge.
