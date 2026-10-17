---
title: CT18Z nominal reco fits, with and without the lattice, cold trust-constr
slug: ct18z-nominal-fits
status: active        # active | paused | done | abandoned
created: 2026-10-15
updated: 2026-10-16
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

## START HERE (status as of 2026-10-17)

- **State:** both fits DONE with all deliverables; answers in [261015-cold-tc-fits](261015-cold-tc-fits/LOGBOOK.md)
  Result. rabbit PRs: #194 open (CI green), #195 + #196 back to draft, being fixed by their authors.
- **Next action:** #195 (release leg warm) and #196 (CI test) fixes → ready again; then the SUMMARY.
- **Blocking on:** the two PR fixes.
- **Running:** no fits. Workers on 261015-trustconstr-warmstart and 261016-face-held-impacts.
- **Summary:** not written yet.

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
### 2026-10-17
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

---

## Open questions

- At an active constraint face rabbit SKIPS `--doImpacts` (only global impacts run, with the face-held covariance;
  the grouped `stat` remainder can be NaN). V2 (lattice) had one weakly binding face, L2(|Y|=2.5). Traditional impacts
  then need a face-held route.

---

## Decisions

- 2026-10-15 — No NP λ carries a prior (Luca): TMD free (code default since 2026-10-06) AND now the CS λ too
  (WRemnants cc3859f4, `lambda2_nu`/`lambda4_nu` in `FREE_PARAMS`). The only external NP information is the lattice
  χ² in fit 2. So fit 2 − fit 1 = the lattice term, nothing else. (First launch, with the old CS priors in NOLAT and
  `prior_sigmas=...nan` in LAT, was killed in the gate before it started.) Differs from LATFROZ_V3/V2 (old TMD priors).
- 2026-10-15 — No warm start (Luca: cold), overriding the fit-queue warm default.
