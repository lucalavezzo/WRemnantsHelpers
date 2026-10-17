---
title: Cold trust-constr fits, no lattice (NOLAT) and lattice (LAT)
slug: 261015-cold-tc-fits
study: ct18z-nominal-fits
status: done          # active | done | paused | abandoned
created: 2026-10-15
updated: 2026-10-17
owner: orchestrator
---

# Cold trust-constr fits, no lattice (NOLAT) and lattice (LAT)

**Task:** Do the two nominal CT18Z reco fits (no lattice / lattice) converge from the cold anchor under trust-constr
with hard NP constraints, and what are their minima, active faces, GoF and covariance?

---

## START HERE (status as of 2026-10-15)

- **Answer:** both minimising (started ~10:12).
- **Next action:** wait for `minimizer status`, then the postfit (Hessian, impacts, saturated ptll); check `[constraints] active:`.
- **Blocking on:** nothing.
- **Running:** NOLAT, LAT (rabbit under mem_gate; logs [logs/NOLAT.log](logs/NOLAT.log), [logs/LAT.log](logs/LAT.log)).

---

## Log

### 2026-10-15
- Output: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261015_ct18z_nominal_fits/fitresults_{NOLAT,LAT}.hdf5`,
  logs next to them (`{NOLAT,LAT}.log`, symlinked into [logs/](logs/)).
- Launch (one line per fit, through the shared mem_gate, 260 GB):
  `mem_gate.sh 260 <OUT>/<PF>.log -- agent_setup.sh --scetlib <gamma-nu build> -- bash workflows/fitterAD.sh <card>
  -c <cache> -o <OUT> -p <PF> --constraints [--lattice] -f "threads=128 [prior_sigmas=lambda2_nu=nan,lambda4_nu=nan] -v 4"`
  (exact commands in [logs/launches.txt](logs/launches.txt)).
- 09:37 relaunch after the CS-prior change (WRemnants cc3859f4); out of the gate ~10:00.
- 10:12 both minimising. Priors on 41/47 model params (free: alphaS, λ2, λ4, δλ2, λ2_ν, λ4_ν); 6 hard rows;
  `lambda4_nu >= 0` starts on its bound, not held feasible (as designed). LAT: LatticeCSTerm armed, τ = 8. Start loss
  NOLAT 114394.9200471485, LAT 114396.0578614644 (= V2's start loss exactly). Iteration 1: 83402.93 / 83464.21;
  ~50–80 s/iteration.
- 12:16 (2h20 in): LAT it 46, loss 376.4727, μ 6.4e-6, optimality 1.4e-5 (near convergence). NOLAT it 35, loss 369.7899,
  μ 0.02, optimality ~2e-2. 120–200 s/iteration (node load; V2 was 80 s). RSS ~236 GB each.
- 14:16 (4h20 in): LAT it 90, loss 376.4726427, μ 1.0e-8, optimality 1.1e-8 (V2-like rejected-step tail, about to
  exit). NOLAT it 48, loss 369.7187821, μ 3.2e-5, optimality 5.6e-5; one iteration took 1379 s.
- 14:40 timing anatomy. Not the ~1 h hoped for: the ~1 h references were the colleague's problem on the old smaller
  cache (55 min) and V1 (48 min); our nominal (V2: lattice, y25 cache) was 2.32 h at 80 s/it alone on the node.
  Today mean s/it LAT 151, NOLAT 290 (V2 80): both fits concurrent, load ~295; NOLAT has 14 iterations > 300 s
  (23–25 min each recently: long projected-CG subproblems). LAT: within 1e-3 of its final loss at it 39 / 1.6 h,
  within 1e-6 at it 67 / 3.2 h, then the rejected-step tail at a frozen x (it 67 → 105+, 1.3 h so far), which only
  ends when μ < barrier_tol = 1e-9 (V2: same tail, it 58–104). NOLAT: within 1e-3 at it 46 / 3.3 h.
- **15:00 LAT minimisation DONE**: status 1 (gtol), nit 113, nfev 75, 4.79 h, optimality 3.2e-9, constr_violation 0,
  μ 4.1e-10, loss 376.472642734532. ONE active face: L2(|Y|=2.5) (`lambda2 + delta_lambda2*Y^2 >= 0 at |Y|=2.5`)
  = 6.4e-11, multiplier −6.41 (the same face as V2/LATFROZ_V3). Other rows inside: λ4_ν 0.0105, λ2_ν 0.0395,
  L2(0) 0.0455, cubic(0) 0.216, cubic(2.5) 0.216 (multipliers ≤ 3e-8). Postfit (Hessian, impacts, saturated ptll)
  running. Expect `--doImpacts` to be SKIPPED (face active).
- 15:08 LAT postfit (log only; rabbit writes the file at the end): edmval on the face 2.3e-17, released 0.456. Face
  L2(|Y|=2.5) active, multiplier 6.41, release ΔNLL 0.456 → WEAKLY binding (< 0.5): the α_s interval along it is
  one-sided, needs a likelihood scan. Global impacts done (warning: grouped `stat` remainder undefined at the face).
  Full saturated test: 2ΔNLL = 752.95, ndof 774 (780 bins − 6 free model params), p = 69.95 % (whether the lattice
  χ² is inside nllvalreduced: to check). Now in save_hists → saturated ptll sub-fit (warm-start reset expected).
  Luca asked whether to stop both before the sub-fits; the permission check blocked my SIGTERM → awaiting his explicit OK.
- 15:50 Luca: let both saturated sub-fits run. LAT postfit ptll LINEAR χ² = 92 for 39 bins (rabbit prints the raw χ² as
  "chi2/ndf"), p ≈ 0; prefit 953. The saturated-projection q comes from the sub-fit (running; μ still 0.1 at it 19).
- **17:35 NOLAT minimisation DONE**: status 1 (gtol), nit 62, nfev 59, 7.38 h, optimality 3.8e-9, μ 1.0e-8, loss
  369.7186970935704. TWO active faces: λ2_ν ≥ 0 (value 2.6e-10, multiplier −32.4) and the TMD large-b cubic at |Y|=2.5
  (1.6e-9, multiplier −4.10). Others: λ4_ν 0.0448, L2(0) 0.115, cubic(0) 0.00133 (inside, multiplier 7e-6), L2(2.5)
  0.056. I.e. without the lattice the CS small-b coefficient goes to its physical bound (as in the colleague's
  no-lattice problem). Now in its postfit.
- NOLAT postfit (log): face λ2_ν release ΔNLL 15.63 (strongly binding), cubic(2.5) release inf. Full saturated
  2ΔNLL 739.44, p 80.92 %. Postfit ptll linear χ² p 0.4 %. Saturated ptll sub-fit started ~17:45, still running
  2026-10-16 08:00 (it 197, μ 2.6e-7, optimality 1.6e-5).
- **2026-10-16 03:57 LAT DONE** (64778 s = 18.0 h total: 4.8 h minimise, ~10 min postfit, 12.8 h saturated sub-fit).
  fitresults_LAT.hdf5 334 MB. Saturated ptll sub-fit: status 2 (xtol, tr_radius 1e-11), 226 it, optimality 6.6e-4
  (NOT converged to gtol — the false-status-2 signature, cause (c) of 261015-trustconstr-warmstart); in the saturated
  model λ4_ν goes to its face (3.3e-7, multiplier −207) and L2(2.5) ≈ 9e-6 (−1.9). Saturated ptll: 2ΔNLL 79.11 / 39,
  p 0.02 %. An under-minimised saturated leg makes q too SMALL, so p ≤ 0.02 % is if anything an overestimate: the
  ptll projection is a poor fit either way (linear χ² 92/39).
- Full-fit saturated, LAT − NOLAT: 752.95 − 739.44 = 13.51 = 2 × (376.4726 − 369.7187): LAT's reduced NLL includes the
  lattice χ² (ndof counts only the 780 bins). Δ = 13.5 for the 2 lattice-constrained CS λ — the same 13.5/2 dof PG
  tension found in lattice-cs-kernel.
- 08:10 LAT deliverables (pullsAndImpacts.sh -P alphaS, plotPtll.sh, plotNPFunctions.sh; all rc 0) in [LAT/](LAT/).
  Only GLOBAL impacts exist (traditional skipped at the active face). Grouped global: total 1.14 (α_s ×1e-3), pdfEig
  0.76, TNP 0.57, lumi 0.41, EW 0.34, b/c masses 0.25, sim stat 0.21, angular coeffs 0.20 … BUT "Data stat." = 0.00:
  that is the undefined grouped remainder at an active face (rabbit's warning), not a real zero; the prior-free NP
  λ groups are 0 by construction in global impacts (no constraint source). So the grouped breakdown is INCOMPLETE.
  The traditional-impacts call of pullsAndImpacts.sh crashes (no traditional impacts in the file; script still rc 0).

- 2026-10-16 08:57 NOLAT STOPPED (SIGTERM, Luca) during its saturated ptll sub-fit: 15 h, 227 it, not converged (loss
  335.53695). No fitresults_NOLAT.hdf5 from this run. Kept: snapshot_fitresults_NOLAT.hdf5 (main-fit minimum, 17:35),
  snapshot_fitresults_NOLAT_saturated_Project_ch0_ptll.hdf5 (where the sub-fit stopped). NOLAT's postfit (cov,
  impacts, hists, saturated ptll) to be rerun from the snapshot once the sub-fit recipe is validated.

![LAT postfit ptll](LAT/ptll/postfit_ptll_ch0_Project_ch0_ptll_preliminary.png)
![LAT grouped global impacts (Data stat. is undefined at the face, shown 0)](LAT/impacts/global_impacts_grouped_alphaS.png)
![LAT NP functions](LAT/np_functions/np_functions.png)

---

## Result

**Caveats first.** Real data, CT18Z, N3LL+NNLO AD cache `pdf62_y35_260921_y25`, card `260916_Z_2D_card_adcorr`
(adexclpdf, 2D ptll×yll). No NP λ prior (WRemnants cc3859f4); LAT = NOLAT + the ASWZ lattice χ² (LATFROZ_V3 defaults,
τ = 8). Both cold, trust-constr + `NPDomainConstraints`. `alphaS` blinded (same family): differences only. LAT's
post-fit numbers come from the face-held-impacts rerun (fitresults_LAT_facefix) and its saturated ptll q is confirmed
by the converged combined-fix sub-fit (79.107); NOLAT's post-fit is the all3-local rerun (fitresults_NOLAT_PF). LAT's
GoF NLL contains the lattice χ² but its ndof counts only the 780 bins.

| | LAT (Z + lattice) | NOLAT (Z only) |
|---|---|---|
| cold minimisation | 4.79 h, 113 it, status 1 (1.6 h to 1e-3) | 7.38 h, 62 it, status 1 (3.3 h to 1e-3) |
| final NLL | 376.4726427 | 369.7186971 |
| active faces | L2(\|Y\|=2.5) (weak, release ΔNLL 0.46) | λ2_ν ≥ 0 (release ΔNLL 15.6); TMD cubic \|Y\|=2.5 |
| full saturated GoF | 752.95 / 774, p 70.0 % | 739.44 / 774, p 80.9 % |
| ptll saturated projection | 79.11 / 39, p 0.02 % | 68.36 / 39, p 0.25 % |
| σ(α_s) (×1e-3, traditional total) | 1.14 | 1.09 |
| Δα_s (LAT − NOLAT) | +0.21 σ_NOLAT (σ ratio 1.049) | |
| CS λ2_ν / λ4_ν (physical) | 0.0395 / 0.0105 | 0 (face) / 0.0448 |
| TMD λ2 / λ4 / δλ2 (physical) | 0.0455 / 0.0720 / −0.0073 | 0.1147 / −0.0001 / −0.0094 |

**Physics read.**
1. *Cold minimisation works* with no warm start in both configurations (status 1, optimality ≤ 4e-9), but it is not
   fast: 4.8 / 7.4 h, of which a large part is the barrier tail after the loss has stopped moving.
2. *The lattice* costs 2ΔNLL = 13.5 for the 2 CS λ it constrains — the same 13.5 / 2 dof (≈ 3.2σ) Z–lattice tension as
   lattice-cs-kernel. Without it the Z data put the CS small-b coefficient on its physical bound (λ2_ν = 0) and saturate
   the CS kernel early (large λ4_ν), with a weak TMD damping (λ4 → its cubic face); with it the CS kernel moves onto
   the lattice reference and the TMD side damps more strongly — the lattice moves damping from CS to TMD, as before.
   α_s moves by +0.21σ and σ(α_s) grows by 5 % (cf. +0.245σ, ×1.05 vs XWSTIFF in lattice-cs-kernel).
3. *Goodness of fit*: the full 2D fit is good in both (p 70 % / 81 %), but the ptll projection is poor in both (p 0.02 %
   / 0.25 %; ratio panel scatter of a few per mille at 5, 17, 21 GeV), and the lattice makes it worse by Δq = 10.7.
4. *Impacts*: NP is the leading group (0.93 / 0.86 ×1e-3), then Data stat (0.86 / 0.79), PDF (0.79 / 0.71), TNP
   (0.76 / 0.65). In NOLAT the CS-kernel group (scetlibNPgammaNu 0.83) dominates the NP; in LAT the TMD group
   (scetlibNPFeff 0.83) does — the lattice pins the CS sector.

![NP functions, NOLAT vs LAT](np_functions_NOLAT_vs_LAT/np_functions.png)
![LAT traditional grouped impacts](LAT/impacts_faceheld/traditional_impacts_grouped_alphaS.png)
![NOLAT traditional grouped impacts](NOLAT/impacts/traditional_impacts_grouped_alphaS.png)
![NOLAT postfit ptll](NOLAT/ptll/postfit_ptll_ch0_Project_ch0_ptll_preliminary.png)

*NP figure caveats:* the grey "lattice fit" curve is the plotter's built-in 2506.13874 reference, not our ASWZ fit;
NOLAT's |Y| = 2.5 F_eff band runs away upward because Gaussian toys around a point on the (curved) cubic face cross
it — the band is not physical there.

---

## Findings

---

## Open questions
