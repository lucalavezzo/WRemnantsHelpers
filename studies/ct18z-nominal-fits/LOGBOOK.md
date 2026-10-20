---
title: CT18Z nominal reco fits, with and without the lattice, cold trust-constr
slug: ct18z-nominal-fits
status: done          # active | paused | done | abandoned
created: 2026-10-15
updated: 2026-10-20
---

# CT18Z nominal reco fits, with and without the lattice — logbook

**Goal (Luca, 2026-10-15):** back to the main physics. Two CT18Z reco-level fits at the nominal prediction order
(N3LL+NNLO AD cache), latest card + cache, both COLD, both trust-constr with the physical NP region as hard
constraints (`NPDomainConstraints`): (1) no lattice, (2) the ASWZ lattice CS-kernel χ² in the likelihood. For each:
traditional + global impacts (grouped and ungrouped) and pulls (`workflows/pullsAndImpacts.sh`), the fit p-value,
the postfit ptll with its saturated-projection p-value (`workflows/plotPtll.sh`), and the NP functions. Questions:
(1) does the minimisation now work cold, with no warm starts; (2) what do the lattice constraints do to the fit and
the NP parameters; (3) is the fit good. Done when all three are answered with the deliverables in task dirs.

---

## START HERE (status as of 2026-10-20) — CLOSED

- **State:** done. Four cold trust-constr fits (reco/gen × NOLAT/LAT) and their comparison; ptll GoF characterised
  (normalisation-vs-shape tension + a smooth few-per-mille wave), no remedy adopted (Luca). Final SUMMARY v2.
- **Next action:** none in this study. PRs continue under [261020-pr-shepherd](261020-pr-shepherd/LOGBOOK.md)
  (rabbit #195/#196, WRemnants #737–#739 ready; second wave E–I after #739 merges).
- **Open (outside this study):** LAT sits on a weakly binding face → its α_s interval needs a likelihood scan.
- **Running:** nothing.
- **Summary:** [SUMMARY.pdf](SUMMARY.pdf), final, covers through 2026-10-20.

---

## Request ledger (everything Luca asked to dispatch; keep current)

Status: ✅ done · 🔄 in progress · ⏸ waiting on Luca · ⏳ queued (node slots)

**2026-10-15 — the two nominal fits**

| # | request | status | where |
|---|---|---|---|
| F1 | NOLAT + LAT reco fits, CT18Z, latest card/cache, cold, trust-constr + NP constraints | ✅ both converged (4.8 h / 7.4 h) | [261015-cold-tc-fits](261015-cold-tc-fits/LOGBOOK.md) |
| F2 | pulls + traditional & global impacts, grouped & ungrouped (pullsAndImpacts.sh) | ✅ LAT + NOLAT (traditional via the face-held branch) | same, `LAT/`, `NOLAT/` |
| F3 | fit p-value | ✅ 70 % / 81 % | same |
| F4 | postfit ptll + saturated ptll p-value (plotPtll.sh) | ✅ 0.02 % / 0.25 % | same |
| F5 | NP functions with the existing plotter (two-panel CS \| TMD); record the recipe | ✅ plotter ported + committed; recipe in knowledge + memory | [261015-np-functions-tool](261015-np-functions-tool/LOGBOOK.md) |
| Q1 | does the cold minimisation work without warm starts? | ✅ yes (status 1, optimality ≤ 4e-9) | 261015-cold-tc-fits Result |
| Q2 | impact of the lattice on the fit and the NP parameters | ✅ 2ΔNLL 13.5 (2 CS λ), Δα_s +0.21σ, σ ×1.05 | same |
| Q3 | is it a good fit? | ✅ 2D yes; ptll projection no | same |
| C1 | CS λ prior-free by default (priors only from the lattice) | ✅ WRemnants cc3859f4 (pushed to #715) | — |
| C2 | use workflows/fitterAD.sh, no runners | ✅ `--constraints`/`--lattice` flags, Helpers 010d37b | — |
| C3 | trust-constr + preconditioner: make it work, validate, PR | ✅ #194 MERGED | [261015-trustconstr-precondition](261015-trustconstr-precondition/LOGBOOK.md) |
| C4 | warm-start fix (sub-fit), PR | ✅ #195 READY (rebased on main, LAT + NOLAT checks posted) | [261015-trustconstr-warmstart](261015-trustconstr-warmstart/LOGBOOK.md) |
| C5 | traditional impacts at active faces, PR | ✅ #196 READY | [261016-face-held-impacts](261016-face-held-impacts/LOGBOOK.md) |
| P1 | why are the saturated sub-fits slow / not converging? | ✅ μ0 restart + conditioning; precond 3.1×, + warm start 4.75× | [261016-saturated-subfit-diagnosis](261016-saturated-subfit-diagnosis/LOGBOOK.md) |
| P2 | rerun NOLAT postfit with the fixes | ✅ NOLAT_PF | same |

**2026-10-17 — code**

| # | request | status | where |
|---|---|---|---|
| K1 | push everything to the WRemnants PR | ✅ #715 branch + Helpers pushed | — |
| K2 | split #715 into digestible PRs + code review | ✅ first wave READY (CI green + hodor clean on each head): #736 (A), #737 (C), #738 (J; needs the theory-correction producers' sign-off), #739 (D; merge after #737); B dropped; split worker stopped (token budget) | [261017-wremnants-pr-split](261017-wremnants-pr-split/LOGBOOK.md) |
| K2a | remaining split PRs E, F, G, H, I | ⏸ open after #739 merges. Decided 2026-10-19 (Luca): H — keep the cache-checking tools (backend comparison, reco validation) in WRemnants, rest to Helpers; I — standalone script; docs — trim kept, comments concise and non-historical; rename the `scetlib_np` group/meta key with a fallback reader for the old name | same |
| K3 | rabbit PRs fixed + one validation check comment each | 🔄 #194 ✅ posted; #195, #196 real jobs ⏳ | C3–C5 above |

**2026-10-17 — physics**

| # | request | status | where |
|---|---|---|---|
| X1 | are the new minima the same as the old trust-krylov + wall ones? | ✅ SAME minima, shifted only by dropping the NP priors: rabbit start losses = predictions to 1e-10 (+0.0023 above the new minima); warm refits from the old points land on LAT/NOLAT (≤ 5e-6σ); Δα_s ∓0.017σ; NOLAT ≠ CMR1B | [261017-minima-vs-trustkrylov](261017-minima-vs-trustkrylov/LOGBOOK.md) |
| X2 | write up the summary of the comparison (SUMMARY.pdf) | ✅ [SUMMARY.pdf](SUMMARY.pdf) v1 (2026-10-18); refresh after the ptll tests | — |
| X3 | gen-level repeat of both fits, four-way comparison | ✅ done: same faces as reco; Δα_s gen−reco −0.61σ / −0.42σ; ptVGen projection also fails; postfit plots stay on the web (Luca) | [261017-gen-cold-fits](261017-gen-cold-fits/LOGBOOK.md) |
| X4 | bad ptll p-value: forensics + a decisive test | ✅ two causes: normalisation-vs-shape tension (free norm −12.3 ± 3.0 %, 4.0σ; **α_s +4.2σ, σ ×1.53**) + a smooth y-independent ±0.2–0.3 % wave (absorbed partly by wider theory priors; α_s stable, −0.01σ); no remedy adopted (Luca 2026-10-20): reported as a characterised mis-modelling; NOLAT FREELUMI not run | [261017-ptll-gof-forensics](261017-ptll-gof-forensics/LOGBOOK.md) |

**Open suggestions (not requested):** fitterAD.sh always saving the ptll postfit covariance; a gen-level mode for
fitterAD.sh; looser `--minimizerBarrierTol` (1e-8) to cut the frozen tail of the main fits.

---

## Log

### 2026-10-15
- Study opened. Inputs: card `260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf` (latest CT18Z 2D card; the
  later CT18Z cards are variants: 1D, ptll1p5, W371, y4), cache `pdf62_y35_260921_y25` (the 770-bin |Y| ≤ 2.5 subset of
  `merged_full_bin0xzero`; what V2 and LATFROZ_V3 ran on). SCETlib: the gamma-nu-points build (2dd978a + the two
  `gamma_nu_points` commits = in-tree 2dd978a + what LatticeCSTerm needs) for BOTH fits. rabbit: production
  `main-plus-ours` 196bfca (trust-constr #189 merged).
- `workflows/fitterAD.sh` gained `--constraints` (NPDomainConstraints margin=0 + V2's trust-constr tolerances; drops
  the spectral preconditioner, which trust-constr refuses) and `--lattice` (LatticeCSTerm, its defaults = LATFROZ_V3,
  τ = 8). Defaults unchanged. Luca: use the workflow, no per-study runners.
- 09:37 relaunched both (after the CS-prior change), `-f 'threads=128 -v 4'`, no prior override; waiting in mem_gate.
- NP-function tool DONE: `workflows/plotNPFunctions.sh` / `scripts/np_functions/` make the 261008 figures for any
  1..N fitresults; reproduces 261008 byte-identically in numbers (two legend strings differ); handles a face-held
  (singular) cov. Uncommitted. ([261015-np-functions-tool](261015-np-functions-tool/LOGBOOK.md))
- Luca: the NP plot wanted is just two 1D figures, the CS kernel and the TMD boundary condition. Tool default changed to
  those two (the 261008 set behind `--all`); same worker.
- NP tool default is now the two 1D figures `cs_kernel` + `tmd_bc` (fits overlaid, bands; lattice-only band on the CS
  one); `--all` = the 261008 set, still reproduced. ([261015-np-functions-tool](261015-np-functions-tool/LOGBOOK.md) §4)
- Luca: we already have the plotter — `np_function_plots.py` (one figure, two panels: CS | TMD), on the old
  `scetlib-np-param-model` branch, whose reader expects physical λ. Decision: port it to the analysis branch with an
  AD-fitresult (θ → λ) reader; `plotNPFunctions.sh` wraps it; `scripts/np_functions/` retired. Same worker.
- Luca: precond + trust-constr approved → validate on a real saturated sub-fit (SATPC_NOLAT, after NOLAT finishes),
  then PR to WMass/rabbit (rebased on main, without the local --blindingFrame commit). Same worker.
- Luca: leave the missed-weak-face activity criterion as is (no rabbit change). NP plotter: consolidate the 3 files
  into one (same worker).
- Luca: test the preconditioned trust-constr speed on the MAIN fit now → PCLAT (LAT + spectral preconditioner, cold;
  launched with MAXRUN=3 if ≥ 500 GB free) and PCNOLAT (queued), compared with LAT/NOLAT (precondition worker).
- Delegated [261015-trustconstr-warmstart](261015-trustconstr-warmstart/LOGBOOK.md): fix the trust-constr warm-start
  walk-away (scipy slack init s0 = max(1.5(c−lb),1) + μ0 = 0.1); own worktree off WMass main; toy + tests, no real fits.
- 15:50 Luca: let the saturated sub-fits run (LAT's and NOLAT's) until there is a better solution; commit the NP
  plotter → WRemnants 74c7e3e3 (np_function_plots.py only), Helpers 5c80345 (plotNPFunctions.sh); not pushed.
- PCLAT (preconditioned, cold) is ~70× behind LAT in loss at equal wall time (33664 vs 483 at ~840 s), with large
  whitened-frame trust radii, rejected steps and non-zero constraint violation → precondition worker diagnosing
  (bug in the transformed constraint derivatives vs a cold-anchor metric vs unscaled slacks).
- PCLAT diagnosis ([261015-trustconstr-precondition](261015-trustconstr-precondition/LOGBOOK.md) Log 16:10): NOT a bug —
  chain rule verified on all 6 real rows at PCLAT's iterate (FD ≤ 3.4e-8). Cause: spectral whitening from a COLD
  start; unit y-steps are ~1σ in soft directions, scipy grows the radius to hundreds → physical steps of hundreds of σ,
  rejected steps, constrained nuisances detour to 11σ. Toy: cold starts are slower preconditioned even with T built
  at the minimum; no cold main fit was ever faster with it (the 3× was always the warm saturated sub-fit). → keep the
  cold main fit unpreconditioned; SATPC (warm) goes ahead; PR change correct, description to say "warm fits only".
### 2026-10-16
- LAT done 03:57 (18 h; 12.8 h of it the saturated ptll sub-fit, which ended NOT converged: status 2, optimality
  6.6e-4); deliverables in [261015-cold-tc-fits/LAT/](261015-cold-tc-fits/LAT/) (global impacts only; grouped
  "Data stat." undefined at the face). NOLAT's sub-fit still running (> 14 h).
- Luca: find out why the saturated sub-fits are so slow and do not converge — warm start, wall/constraints, lattice,
  preconditioner, or the minimizer? Delegated [261016-saturated-subfit-diagnosis](261016-saturated-subfit-diagnosis/LOGBOOK.md):
  log forensics first, then a one-factor-at-a-time set of sub-fits from LAT's result (A warm-start fix, B precond,
  C both, D trust-krylov + C² wall + precond), ≤ 2 of its jobs at once.
- Luca: conditioning is already known to be the big lever (261008: SATB8 5.8 h → SATP 1.3 h preconditioned) → diagnosis
  scoped down to ONE sub-fit with both fixes (warm start + preconditioner) from LAT's result; trust-krylov + C² wall +
  precond only as fallback.
- [261016-saturated-subfit-diagnosis](261016-saturated-subfit-diagnosis/LOGBOOK.md) DONE: the plain sub-fit is slow
  mainly because it restarts the barrier at μ0 = 0.1 from a minimum (that stage = 74 % of LAT's 12.6 h; ~half the
  total a no-progress zig-zag), made expensive by the ill-conditioned saturated Hessian. Combined fix C (warm start +
  full spectral preconditioner, branch `satdiag-ws-pc` 0395383, local) PASSES: status 1, optimality 2.5e-9, q = 79.10711
  vs LAT's 79.10694 (LAT's stuck status 2 was off by only 1.7e-4), same point (≤ 1.3e-4σ), 89 it / 982 HVPs / 3.6 h vs
  226 it / 4667 HVPs / 12.8 h → 3.9×. Shares of the two fixes inferred, not measured. Saturated `edmval` (2.5) is the
  unconstrained EDM — no convergence measure at an active face. → LAT's saturated ptll q = 79.1/39 (p 0.02 %) STANDS.
- Luca: go. (1) NOLAT full postfit from its snapshot on one local branch with all three rabbit changes (warm start +
  precond + face-held impacts), then NOLAT deliverables + NOLAT-vs-LAT NP overlay + LAT impacts redone face-held
  (diagnosis worker). (2) Three separate PRs to WMass/rabbit off main, not stacked (tc-precond-pr, tc-warmstart,
  face-held-impacts), each by its author; warm-start worker also updates rabbit_minimizer_tolerances.md.
- PR opened: preconditioner under trust-constr, https://github.com/WMass/rabbit/pull/194 (c76c226 on main 2d9f380).
- PR opened: trust-constr warm start, https://github.com/WMass/rabbit/pull/195 (f84e0a8 on main; suite 482). knowledge/20_frameworks/rabbit_minimizer_tolerances.md: new warm-start section (frozen status 2, saturated edmval).
- PR opened: face-held impacts, https://github.com/WMass/rabbit/pull/196 (e50a872 + bf9dfb1 on main; suite 476). Cross-link comments added to #194/#195/#196.
- 16:40 NOLAT_PF (branch all3-local d573c1d, suite 493): main postfit fine (NLL = snapshot exactly; faces λ2_ν
  [release ΔNLL 15.6] + cubic(2.5); traditional impacts computed; full saturated 739.44/774 p 80.9 %; ptll linear χ²
  66/39 p 0.4 %). ptll saturated sub-fit: warm leg fast (q-to-go ≈ 0 at 0.8 h) but stopped status 2 ON the cubic face
  with a RELEASING multiplier (+1.48); true minimum 3.3e-4 lower, face released (Δq 6.7e-4, negligible). The
  dual-sign check then started a release leg with scipy's COLD interior-point start (μ 0.1, scipy slacks) → walked
  away (loss 335.92, cubic violated 3.4e-3). Flaw in PR #195's release leg. Awaiting Luca: (a) let run, (b) stop +
  postfit without the ptll test (~45 min) + ptll separately, (c) fix the release leg to start warm.
### 2026-10-20
- Final SUMMARY v2 (4 pages): physics review passed, no blocking; its 5 non-blocking fixes applied (Wilks caveat on the 4.0σ, softer model-vs-detector wording, preconditioner 3.1× + warm start 1.5×, σ(α_s) lattice cost +5 % reco / +1 % gen, gen ptVGen 3–4 % low offset).
- Luca: fold the gen-level study into this one. `gen-level-nominal-fits/261017-gen-cold-fits` moved here as task [261017-gen-cold-fits](261017-gen-cold-fits/LOGBOOK.md); the separate study removed (its log copied below).

#### (from the former gen-level-nominal-fits logbook)
##### 2026-10-17
- Study opened. Reco reference: ct18z-nominal-fits/261015-cold-tc-fits (Result table).
- Setup ([261017-gen-cold-fits](261017-gen-cold-fits/LOGBOOK.md)): iter0 real-data σ_UL card
  261009_ad_genlevel_iter0 (20 ptV × 10 |Y| = 200 bins; y5 binning not yet adopted), same y25 cache as reco with
  gen_level=1, no NP priors; `--blindingFrame data` (= reco's auto frame) so α_s differences gen vs reco are meaningful;
  rabbit all3-bf-local ece1d16 (all3-local + 196bfca), local. fitterAD.sh can't take a gen card (hardcoded ptll, no
  --covarianceFit) → task scripts/common.sh + chain.sh, two passes (cold fit without preconditioner; warm postfit with
  preconditioner, impacts, ptVGen/absYVGen saturated projections). GEN_NOLAT near convergence (cache load 2.4 h on the
  loaded node); GEN_LAT queued.
- Both gen main fits converged cold (status 1). GEN_NOLAT 57 it / 5.5 h: faces λ2_ν ≥ 0 and cubic(|Y|=2.5) (= reco NOLAT);
  full saturated 226.38/194, p 5.6 %; λ2 0.171, λ4 −0.0007, δλ2 −0.0068, λ2_ν 0, λ4_ν 0.0305. GEN_LAT 46 it / 1.6 h: face
  L2(|Y|=2.5) (= reco LAT); 237.38/194, p 1.8 %; λ2 0.0178, λ4 0.0425, δλ2 −0.0028, λ2_ν 0.079, λ4_ν 0.0050. Lattice cost
  2ΔNLL 10.99 (gen) vs 13.51 (reco). Postfits queued in mem_gate.
- 2026-10-19 [261017-gen-cold-fits](261017-gen-cold-fits/LOGBOOK.md) DONE: four-way comparison (reco NOLAT / gen NOLAT / reco LAT /
  gen LAT): σ(α_s) 1.09/1.17/1.14/1.18 ×1e-3; Δα_s gen − reco −0.61σ (NOLAT), −0.42σ (LAT; = old GENDF − V3); LAT − NOLAT
  +0.21σ reco, +0.35σ gen; lattice cost 13.5 reco / 11.0 gen; full saturated p 81/5.6/70/1.8 %; ptVGen projection fails
  too (52.5/20, 60.3/20), absYVGen fine (p 8–9 %); λ2_ν 0/0/0.040/0.079. OPEN: policy conflict — z-data-unfolding says
  no postfit plots of the α_s fit, but postfit ptVGen/absYVGen (and reco ptll) plots are on the web → Luca.

---

- Luca: none of the normalisation options adopted — report the ptll misfit as a known, characterised mis-modelling. Close the study: final SUMMARY (covering gen-level-nominal-fits too) → physics review → knowledge-curator → status done. NOLAT FREELUMI not run.
- [261017-ptll-gof-forensics](261017-ptll-gof-forensics/LOGBOOK.md) Phase 2 DONE (LAT; all converged < gtol 1e-5, single face
  L2(|Y|=2.5)): A0×2 full −12.7, ptll 67.54 (p 0.31 %), Δα_s −0.44σ, σ ×1.00; theory×2 full −22.5, ptll 58.58 (p 2.3 %),
  Δα_s −0.01σ, σ ×1.26 — pulls keep running with the wider prior (A0 PtV15_20 −3.8σ, FO env −4.1σ in original units);
  FREELUMI full −16.1, ptll 62.96/38 (p 0.66 %), free normalisation −12.3 ± 3.0 %, LR 16.1 = 4.0σ (May, old model:
  6.1σ), **Δα_s +4.2σ, σ(α_s) ×1.53**; λ4 0.072→0.181, λ2 0.046→0.030, λ2_ν 0.040→0.018. VERDICT: two causes — (i) the
  absolute normalisation is in 4σ tension with the α_s/NP point the ptll shape prefers; (ii) a y-independent smooth
  few-per-mille wave (3–22 GeV), genuinely uncaptured, that barely moves α_s. α_s is stable against (ii) but depends
  on (i) at +4σ → needs a decision. A0×3 / more NOLAT inflation not needed; NOLAT FREELUMI (~5 h) optional.
- [261020-pr-shepherd](261020-pr-shepherd/LOGBOOK.md): rabbit #194 and WRemnants #736 MERGED. rabbit #195 (4532443) and #196
  (1ecae8a) rebased onto main after the mcstat-debias merge (#141; non-mechanical), READY (20/20 CI, hodor clean, comments
  answered); they merge cleanly into each other. WRemnants #737, #738, #739 READY. Infra-only CI failures noted (hodor
  `bun install`; a 15 s wall-clock test limit on a loaded runner; rabbit `--failed` re-runs break downstream jobs → re-run
  the whole workflow). Second wave built locally on #739's head, not pushed: E, F, G (on E), I standalone, H trimmed
  (validate_variations + make_debug_card → Helpers commit d5508b5, unpushed), new K renames the `scetlib_np` group to
  `response_matrix` with an old-name fallback. For Luca: merge #737 → #739; #738 sign-off; push d5508b5?; OK with the name
  `response_matrix`?

### 2026-10-19
- ptll P1_NOLAT: q3/q6/q10 = 22.0/27.3/33.6; remainders 46.4/36, 41.1/33, 34.7/29 (p 12/16/21 %). Same normalisation valley (scales ≈ 0.89–0.92; α_s +3.7σ₀ at k3, +2.3σ₀ at k10; λ4_ν ≈ +3σ₀), but NOTHING significant beyond it; k10 remainder = P3's validated prediction (35.5/29). LAT keeps ~10 extra units of finer wave structure (45.5/29) ≈ its whole extra q over NOLAT → the lattice's extra tension sits in the fine ptll structure, not the normalisation.
- P5a: `--fakelumi` was removed (WRemnants 0769d44b, June); replacement `--lumiUncertainty 0` (lumi unconstrained, 1.2 % per unit) = same likelihood. Card FREELUMI differs from the control only in lumi's constraint weight; warm refit from LAT_facefix (lumi starts at −1.46) + full postfit incl. ptll saturated test (true ptll ndf 38, rabbit prints 39 → corrected). Queued after P2_THx2_LAT. σ₀ in the P1 read-off = σ(α_s) at the LAT postfit, i.e. the coarse saturated model moves α_s by +3.6 POSTFIT σ. Early P2: A0×2 already ≥ 12.6 lower in 2ΔNLL at iteration 7.
- Luca: P5a as a `--fakelumi` card + warm refit + postfit with the ptll saturated test (tests both the main fit and the sub-fit). Prior art: studies/franks-vals-fit (May, old template model): walled NP → 6.1σ fakelumi tension (LR 37.6), unwalled 0.4–2σ. LAT first.
- ptll P1_LAT read-off: q3/q6/q10 = 22.19/26.79/33.59; remainders q39 − q_k = 56.9/36, 52.3/33, 45.5/29 (p 1.5/1.8/2.6 %).
  The coarse q is mostly ONE freed overall normalisation (coarse scales equal, 0.89–0.93), worth ~20 units, nonlinear:
  P3's linear analysis gives 2.0 for the same basis — near the minimum a flat scale is degenerate with α_s and the NP λ,
  far along the normalisation–α_s–λ4 valley the LR finds ~20. With the normalisation free, lumi/EW/FSR/A0 relax and α_s
  moves +3.6σ₀, λ4 +2.7σ₀ → a tension between the ptll SHAPE and the normalisation allowed by lumi/EW/FSR/σ_tot. Wilks
  may not hold along that valley. P2_A0x2_LAT launched 15:13 (gtol 1e-5); THx2 queued. Proposed P5a: one free
  normalisation only (ptll:rebin(0,44)) to isolate the ~20 units — awaiting Luca.
- P1 check: all three rabbit improvements are active (warm start, full spectral preconditioner per sub-fit). Slowness = each coarse sub-fit is a genuine new minimisation (ΔNLL ~11, 40–60 it), a fresh preconditioner Hessian per sub-fit (10–18 min), a 30–40 % xtol tail (warm barrier already ≤ barrier_tol, optimality floor ~1e-6 never reaches gtol 1e-8), node load 300–380. Luca: P2 uses `--minimizerGtol 1e-5` (P1 evidence: Δloss ≤ 3e-8 at that point); no preconditioner reuse change.
- Luca's decisions for the second wave (E–I): H split (cache checks in WRemnants, rest to Helpers); I standalone; doc trim accepted (comments concise, not historical); rename `scetlib_np` key with old-name fallback.
- WRemnants #737 (c01b1dc) and #739 (34f5313): CI 23/23, hodor clean → marked READY (orchestrator). All four first-wave PRs ready. Split worker stopped to save tokens.
- Luca: leave the postfit plots (reco ptll, gen ptVGen/absYVGen) on the web. #194 READY (Luca fixed the hodor hang).
- ptll P3 (exact, rabbit-based): misfit = a y-INDEPENDENT smooth ±0.2–0.3 % WAVE in 3–22 GeV (−0.2 % at 5–6, +0.3 % at
  9–12, −0.2 % at 16–20 GeV); y-independence from rabbit's χ² (ptll×6 yll bands − ptll: 210.6/195 LAT, 189.1/195 NOLAT).
  Flat/linear/quadratic/cubic parts < 2 %; one 6-sign-change mode holds 19–25 units; after 10 smooth params the remainder
  is 35/29 (p 20 %). OVERTURNS phase 1's "low-order" reading (the surrogate put ~40 % in flat/tilt modes = α_s/NP drift
  in the saturated fit). Exact 5.0–5.5 GeV single-bin score 11–13 (global p ~3.5 %). yll projection linear χ² 38/20
  (p 0.8 %). pull_shapes.png was a colour/label bug (fixed). P1 LAT/NOLAT launched 05:06; P2 cards built (control
  bit-identical to nominal), P2 next.
- PR195_LAT (#195 alone): one warm leg, no release, no violation; status 2 (optimality 3.0e-4) after 115 it / 11.3 h (plain: 226 it / 12.8 h, frozen on the face); q 79.107113 = SATWSPC_LAT (Δ 6e-8), same point ≤ 2.5e-6σ. #195 stays ready; task closed.
- #196 READY (https://github.com/WMass/rabbit/pull/196#issuecomment-6263662760): on NOLAT, holding the λ2_ν ≥ 0 face ≡ freezing λ2_ν — cov and every impact array identical (Δ = 0); CI green, bot clean on 8b3f180. Task closed.
- #194: reply to David posted, CI 19/19 green on 7b4ae42, 0 open threads; NO bot review — hodor hung 6 h on its own `find / -name minimize_trustregion_constr.py` on the runner, 2 of 2 runs on #194 (a hodor/runner problem, not a finding). Stays draft pending Luca's call.
- Workers stopped by the API rate limit again (~19:40 → 05:00); all jobs finished meanwhile: PR195_LAT, PR196_NOLAT_frozen,
  GEN_LAT_PF, P3_LAT, P3_NOLAT. PR state 05:05: #195 ready (meets the rule); #194 draft (thread resolved, CI green, no
  bot review on head yet); #196 draft (bot clean, CI green; frozen comparison to post); WRemnants #736/#738 bot clean +
  CI green; #737/#739 bot "blocking issues" + 1 CI failure each. All six workers resumed.

### 2026-10-18
- hodor `review` job on WRemnants fork PRs: pull_request_target + actions/checkout refuses fork code ("pwn request" guard); rabbit's hodor does review fork PRs. Luca: option 1 — push the 4 branches to WMass/WRemnants (he has maintain rights) and reopen as drafts from there; he will raise the fork issue with the hodor maintainer. Delegated to the PR-split worker.
- Luca: a PR goes ready only when CI is green AND all bot + human comments are resolved. → #194 (open David Walter thread on a perf-assertion test; review job failed), #195 (hodor P3: stale --minimizerWarmStart help), WRemnants #732–#735 (review job fails: hodor cannot review fork PRs) moved back to DRAFT; #196 stays draft. Workers told.
- SUMMARY v1 written (study-summarizer; 4 pages, covers through 2026-10-18). It flagged stale task logbooks (subfit-diagnosis START HERE/Result shares, face-held-impacts held/frozen entries + START HERE, precondition §3–4 and warmstart §5 proposals since run) and a garbled y-label in ptll-forensics pull_shapes.png → owners asked to fix.
- #195 READY (https://github.com/WMass/rabbit/pull/195#issuecomment-6253853702): correctness fix confirmed on the releasing-face case; alone it does not speed up the sub-fit (status 2, optimality 6.6e-4, same point as NOLAT_PF to 8.6e-5σ). PR195_LAT pending.
- [261017-minima-vs-trustkrylov](261017-minima-vs-trustkrylov/LOGBOOK.md) DONE: same minima as LATFROZ_V3/V2 and XWSTIFF, moved only by dropping the NP priors (rabbit-confirmed). Summarizer dispatched.
- ~00:40–14:57 workers stopped by an API rate limit; jobs kept running. Done overnight: LATatV3, NOLATatXW, PR195_NOLAT,
  PR196_NOLAT_held, GEN_NOLAT_PF. Running: PR195_LAT (8 h, sub-fit), GEN_LAT_PF. P3 had not been launched. All six workers resumed.
- Luca: go for the ptll tests P3 → P1 → P2 (forensics worker); first wave of the #715 split being opened (A, C, J, then D; B dropped).
- #194 check DONE and posted (https://github.com/WMass/rabbit/pull/194#issuecomment-6244958708): preconditioner ALONE on
  LAT's saturated sub-fit converges (gtol; plain stopped on xtol), 4667 → 1504 HVPs (3.1×), 226 → 167 it, same point
  (3e-8σ, Δq −5e-8); + warm start 982 HVPs (4.75×). RETRACTION: the 2026-10-17 interim statement (mine and the
  worker's) that "most of the gain comes from the warm start" was WRONG — the preconditioner gives 3.1× of the 4.75×,
  the warm start the remaining 1.5× and removes the μ0 stage. All CI-gap checks pass (bit-identical where expected).
- Luca: leave the lattice data in #715's history alone; #715 to be closed once the split PRs are open.

### 2026-10-17
- [261017-wremnants-pr-split](261017-wremnants-pr-split/LOGBOOK.md) DONE: #715 → 10 squashed PRs (A setuprabbit fixes,
  B theory-corr sidecars, C response inputs, J ptzgen binning → main; D core param model after C; E NP constraints, F
  lattice term, H validation tools, I cache→theorycorr after D; G NP plots after E), built locally, lint + tests pass,
  nothing pushed; +10.5k vs #715's +14.2k. Review fixes: `--responseGenBinning` default (was silently mis-normalising
  the gen total for 2-Q-bin corrections), `--presel` overflow, tests that only passed on the branch, real-data λ / an
  α_s value in comments/README removed, ~60 Helpers-study references removed, docs vs code. BLOCKER (verified by me):
  private ASWZ lattice files (lattice_aswz_inputs.{json,npz}, lattice_aswz_data.{json,npz}) are in commits 44f8a5c0,
  b14f84f4, 3ef3efb9 on the public fork branch origin/scetlib-ad-param-model (and in WMass refs/pull/715). Awaiting
  Luca on (a) purge, (b) #715 close/reuse, (c) wremnants-data MR for B, (d)–(g).
- #195: release-leg fix pushed (117cc67: Newton release step + a new centred warm leg; scipy cold start only as last
  resort); toy releasing cases 15–26 it (was 294–613); suite 483 (+1 wall-clock flake under load). CI-gap checks vs
  main: everything that should not change is bit-identical (CI configs, cold trust-constr, toys, `off`, forced guard
  failure); warm on: saturated sub-fit 38 vs 69 it, --externalPostfit refit 1 vs 5, scan curve within 3.2e-5. Real jobs
  PR195_NOLAT/LAT queued; comment + ready after NOLAT.
- #196: CI fully green at 8b3f180. RETRACTION (worker): the 2026-10-16 curved-face correction to the GLOBAL stat
  remainder was wrong (the plain remainder matches an exact elimination test to 1e-8) and is removed; NOLAT_PF's
  global stat² is too large by 7.8e-5, its traditional impacts are unaffected. No-face bit-identity vs main: identical
  for every config tested. Two NOLAT validation jobs (λ2_ν held vs frozen) queued in mem_gate since 10:56; then the
  check comment and ready.
- [261017-minima-vs-trustkrylov](261017-minima-vs-trustkrylov/LOGBOOK.md) interim (offline; rabbit cross-evaluations
  queued): LAT vs LATFROZ_V3/V2 SAME BASIN — the only relevant change is dropping the TMD priors; LAT's objective at
  V3's point is +0.00225 above LAT; one Newton step from V3 (no TMD priors) predicts LAT to 3.4e-4σ; Δα_s −0.017σ;
  same face. NOLAT vs XWSTIFF SAME BASIN after dropping the 5 NP priors (+0.00229; Newton to 8e-3σ; Δα_s +0.017σ;
  same two faces); not CMR1B (0.57 higher). NOMSTIFF/C2A = different objective (1D lattice term, λ4_ν = 0). 2ΔNLL(LAT −
  NOLAT) 13.51 vs the old PG 13.48. Nothing concluded from the old fits changes. To be confirmed by the rabbit start
  losses (predicted 376.4748905 LATatV3, 369.7209822 NOLATatXW).
- ~13:40–18:00 all six workers stopped by an API rate limit; their detached jobs kept running. 18:02: running PR194_SATPC_LAT
  (precond ONLY, LAT sub-fit 3.7 h, it 51, μ still 0.02 → the preconditioner alone does not fix the μ0 restart; the
  combined fix took 3.6 h for the whole sub-fit) and GEN_NOLAT (near convergence); queued in mem_gate: PR195_LAT,
  PR195_NOLAT, LATatV3, NOLATatXW, GEN_LAT. Node load 410–560. All workers resumed.
- [261017-ptll-gof-forensics](261017-ptll-gof-forensics/LOGBOOK.md) Phase 1 DONE: ptll q is NOT bin-driven (data-only
  Σz² 41.5/39 LAT, 39.7/39 NOLAT; the 5/17/21 GeV points z −2.7/−2.4/−2.1, P≈10 % for four |z|>2 in 39) — it is a
  smooth, y-independent few-per-mille ptll shape the 2D fit only reaches by pulling ~6 theory-type nuisances 1–2σ
  (prior relief 21 of 79: A0 PtV15_20 −1.9σ, FO env SymDiff −1.5σ, lumi −1.5σ, mb_up, weak, FSR). Record rules out:
  stuck sub-fit, Wilks/ndf, BB/MC stat, blinding, PDF, NP form, yll dependence, 4D leakage, efficiencies, qT bin 0.
  Never template-tested: A0 modelling, b/c mass in resummation, QED, resummation order. SURROGATE (quadratic, not
  rabbit): a 5-parameter smooth ptll shape absorbs it all; prior inflation ×2 → q −22–24. Proposed (none run): P3
  postfit rerun with --computeHistCov + yll-band mappings (~1 h/fit); P1 rabbit smooth test via nested coarse-rebin
  mappings (~4–8 h); P2 group prior inflation via --scaleParams (~1 day); P4 toys (~3 days); P5 shape vs norm, step
  artefacts (FO env at 20 GeV, A0 PtV bin edges).
- Luca (code): push everything → WRemnants #715 branch pushed (cc3859f4, 74c7e3e3); Helpers 010d37b pushed (study,
  fitterAD.sh flags, knowledge notes; plotly .html left out). Split #715 into digestible PRs + code review →
  [261017-wremnants-pr-split](261017-wremnants-pr-split/LOGBOOK.md) (local branches only, plan to Luca first). rabbit
  #194/#195/#196: each author fixes (if needed) AND posts a validation check comment (isolated real-fit effect, plus the
  regressions CI does not cover).
- Luca (physics): (1) are the new minima the same as the old trust-krylov + wall ones? →
  [261017-minima-vs-trustkrylov](261017-minima-vs-trustkrylov/LOGBOOK.md) (cross-evaluation of likelihoods at each
  other's minima); then the study SUMMARY. (2) gen-level repeat → new study
  [261017-gen-cold-fits](261017-gen-cold-fits/LOGBOOK.md). (3) the bad ptll p-value: forensics of the whole record
  + where q comes from, then a ranked proposal of decisive tests → [261017-ptll-gof-forensics](261017-ptll-gof-forensics/LOGBOOK.md).
- NOLAT_PF finished 2026-10-16 17:56 (3.66 h total; sub-fit 3.07 h). The release leg converged: status 1, optimality
  1.2e-9, loss 335.536953 (= the plain sub-fit's point). NOLAT ptll saturated q = 68.36/39, p 0.25 %. Full fit
  739.44/774, p 80.9 %. fitresults: /ceph/.../261016_nolat_postfit/fitresults_NOLAT_PF.hdf5 (224 MB).
- PR #195 → DRAFT (release leg starts cold; fix to the warm-start worker). PR #196 → DRAFT (its new curved-face test
  fails on CI at the FD comparison, rtol 2e-3; fix to its author). #194: CI green (one cancelled job).
- NOLAT deliverables + NOLAT-vs-LAT NP overlay being made (orchestrator, all3-local branch on PYTHONPATH).

- [261015-cold-tc-fits](261015-cold-tc-fits/LOGBOOK.md) DONE: both converge cold; full fits good (70 % / 81 %), ptll
  poor (0.02 % / 0.25 %); lattice Δ2NLL 13.5 (2 CS λ), Δα_s +0.21σ, σ ×1.05; NOLAT puts λ2_ν on its bound.
- [261016-face-held-impacts](261016-face-held-impacts/LOGBOOK.md) DONE: rabbit branch `face-held-impacts` e50a872 + bf9dfb1
  (off WMass main, not pushed): stat/bbb covariances from the face-held Lagrangian Hessian, groups conditioned only on
  face-free directions, bound-held params exactly zero variance, skips removed; exact-reference tests (freeze, linear
  elimination, curved face), no-face output bit-identical; suite passes. LAT traditional grouped (α_s ×1e-3): total
  1.14, NP 0.93, Data stat 0.86, NPFeff 0.83, pdfEig 0.79, TNP 0.76, lumi 0.44, EW 0.38, bbb 0.14. Global "Data stat."
  stays NaN on LAT: not the face (linear) — the non-prior Hessian (data + lattice + profiled bbb) has negative
  eigenvalues (lowest −0.55), so the remainder is −0.022. Impacts are AT the weakly binding face (released total 1.28).

![LAT traditional grouped impacts, face held](261016-face-held-impacts/LAT_impacts/traditional_impacts_grouped_alphaS.png)

- 08:57 NOLAT stopped (Luca) in its saturated sub-fit (15 h, not converged); minimum safe in its snapshot. SATPC_NOLAT
  cancelled; the combined warm-start + preconditioner test on LAT replaces it. NOLAT's postfit reruns afterwards.
- Delegated [261016-face-held-impacts](261016-face-held-impacts/LOGBOOK.md): face-held traditional impacts (+ the
  global-impacts stat remainder) in rabbit — the missing piece is the stat-block covariance (plain inverse, not
  face-held); exact references (freeze for a bound face, elimination for a linear one); real check = LAT postfit.

- PCLAT stopped (Luca: no point; diagnostic only). Snapshot kept in 261015_tc_precond_validation/.
- [261015-trustconstr-warmstart](261015-trustconstr-warmstart/LOGBOOK.md) DONE (toy + rabbit): three causes, not one —
  (a) scipy slack init bites only NON-held rows (exactly on a bound, or infeasible start = TCA); (b) μ0 = 0.1
  restart; (c) rabbit's keep_feasible holds every row of a feasible start, pinning curved rows' slacks → false status-2
  "success"/maxiter after the data/model changes (saturated sub-fit, scans, toys). Fix: rabbit `tc-warmstart` f84e0a8
  (off WMass main, not pushed): `--minimizerWarmStart auto|on|off` (auto: saturated sub-fit, --externalPostfit refits,
  scan points, asym-impact refits), consistent slacks via a guarded subclass of scipy's private BarrierSubproblem,
  centred μ0, dual-sign check; cold path bit-identical. Toy: 0/44 failures (was 11/44), restart at the minimum 1 it;
  rabbit saturated toy 18 vs 82 iterations. 13 tests, suite 482. Real test SATWS_LAT proposed (after LAT finishes).
  CAVEAT for the running fits: their plain saturated sub-fits may end at a false status-2 success (cause c) → check
  optimality/multiplier signs before trusting the saturated ptll q.
- NP plotter consolidated: one file `scetlib_ad/np_function_plots.py` (728 lines; was 3 files / 2622), θ→λ and face
  detection imported from `np_damping_wall`; same figure (pixel-identical), curves to 2e-16. Uncommitted.
- scipy warm-start reset confirmed at the source: `tr_interior_point.py:325`, `s0 = max(1.5·(c−lb), 1)` — slacks are
  not initialised from x0, so any row with c−lb < 2/3 (every row on a face) starts inconsistent by O(1); plus μ0 = 0.1.
- [261015-trustconstr-precondition](261015-trustconstr-precondition/LOGBOOK.md) DONE: feasible and implemented — the
  missing chain rule (J·T, Tᵀ∇²cT); rabbit branch `tc-precond` 2a64792 (worktree /work/submit/lavezzo/rabbit-tc-precond,
  not pushed), 3 new tests, suite 472 passed. Toy: gain grows with κ (1336 → 594 HVPs at κ 4.5e6). Real-fit test
  SATPC_NOLAT proposed, awaiting Luca. Flags: weakly binding face can be missed by the postfit (gap μ/v > active_tol);
  zero-gradient rows silently dropped; scipy's warm-start slack reset may dominate the saturated sub-fit cost.
- Port DONE (uncommitted): `WRemnants/wremnants/postprocessing/scetlib_ad/{np_function_plots,np_forms,np_fit_lambdas}.py`;
  `workflows/plotNPFunctions.sh` wraps it (≤ 2 fits, num/den); `scripts/np_functions/` deleted. Curves equal the
  earlier tool's to 0. Caveats: no central-only mode (a walled fit's released cov gives a runaway band across a face;
  face-held covs from `--constraints` fits should not); the grey lattice curve is the plotter's built-in 2506.13874
  reference, not our ASWZ V3 lattice-only fit. ([261015-np-functions-tool](261015-np-functions-tool/LOGBOOK.md))
- ~10:00 both fits out of the gate, loading the cache.
- Delegated [261015-trustconstr-precondition](261015-trustconstr-precondition/LOGBOOK.md): can trust-constr + hard
  constraints run with the spectral preconditioner (chain rule on the constraint Jacobian/HVP), and does it pay off?
  Own rabbit worktree; no real fits without approval.
- Standard post-fit recipe recorded: `knowledge/20_frameworks/nominal_workflow.md` §"SCETlib-AD fits" + memory.

---

## Findings

1. Cold trust-constr + hard NP constraints converges for all four fits (reco/gen × NOLAT/LAT); each configuration ends
   on the same faces at reco and gen. — (261015-cold-tc-fits, 261017-gen-cold-fits)
2. The new minima are the old trust-krylov + wall minima, moved only by dropping the NP priors (rabbit-confirmed;
   Δα_s ±0.017σ). — (261017-minima-vs-trustkrylov)
3. The lattice costs 2ΔNLL 13.5 (reco) / 11.0 (gen) for the 2 CS λ, moves NP damping from CS to TMD, shifts α_s
   +0.21σ / +0.35σ; σ(α_s) +5 % (reco) / ~+1 % (gen). gen − reco: −0.61σ (NOLAT), −0.42σ (LAT). — (261015-cold-tc-fits, 261017-gen-cold-fits)
4. The ptll (and gen ptVGen) projection fails while the 2D fit is good: a normalisation-vs-shape tension (free
   normalisation −12.3 ± 3.0 %, 4.0σ, Δα_s +4.2σ, σ ×1.53) plus a smooth y-independent ±0.2–0.3 % wave at 3–22 GeV
   that no existing nuisance spans even widened ×2 (α_s stable, −0.01σ). Not bin-localised, not detector-like. —
   (261017-ptll-gof-forensics)
5. Saturated sub-fit: preconditioner 3.1×, + warm start 4.75×, properly converged; traditional impacts at active
   faces now exact. — (rabbit #194 merged, #195, #196)

---

## Open questions

- [SOLVED by rabbit #196, 2026-10-19] At an active constraint face rabbit SKIPS `--doImpacts` (only global impacts run, with the face-held covariance;
  the grouped `stat` remainder can be NaN). V2 (lattice) had one weakly binding face, L2(|Y|=2.5). Traditional impacts
  then need a face-held route.

---

## Decisions

- 2026-10-15 — No NP λ carries a prior (Luca): TMD free (code default since 2026-10-06) AND now the CS λ too
  (WRemnants cc3859f4, `lambda2_nu`/`lambda4_nu` in `FREE_PARAMS`). The only external NP information is the lattice
  χ² in fit 2. So fit 2 − fit 1 = the lattice term, nothing else. (First launch, with the old CS priors in NOLAT and
  `prior_sigmas=...nan` in LAT, was killed in the gate before it started.) Differs from LATFROZ_V3/V2 (old TMD priors).
- 2026-10-15 — No warm start (Luca: cold), overriding the fit-queue warm default.

- 2026-10-20 — ptll GoF: no remedy adopted (no normalisation-free systematic, no shape nuisance); quote it as a characterised mis-modelling (Luca).
