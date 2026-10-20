---
title: ptll GoF forensics
slug: 261017-ptll-gof-forensics
study: ct18z-nominal-fits
status: done          # active | done | paused | abandoned
created: 2026-10-17
updated: 2026-10-20
owner: study-worker
---

# ptll GoF forensics

**Task:** Why is the ptll saturated-projection p-value bad (q = 79.1/39 LAT, 68.4/39 NOLAT on the 2D ptll × yll
CT18Z real-data card), where in bins / modes / slices / nuisances does q come from, and what decisive (not yet run)
tests would localise it or justify it as a genuine, uncaptured mis-modelling? Phase 1 is forensics only: no new fits
and no cache loads.

---

## START HERE (status as of 2026-10-20)

- **Answer:** Result "Phase 2 verdict". The ptll q has two parts:
  - a **normalisation-vs-shape tension**, 4.0σ: free normalisation −12 ± 3 %, α_s +4.2σ, σ ×1.5;
  - a **y-independent smooth ±0.2–0.3 % wave** at 3–22 GeV. It is uncaptured: the A0 / FO-envelope pulls run with
    their priors. α_s is robust to it (theory ×2: Δα_s −0.01σ, ptll p → 2.3 %).
- **Next action:** none queued. Optional, not launched (ask Luca): NOLAT free-normalisation refit, to show the
  normalisation tension is not lattice-driven. P1 suggests it is the same (q3 22.0).
- **Blocking on:** nothing.
- **Running:** nothing.

---

## Log

### 2026-10-20 (orchestrator note)
- Luca decided on the Phase 2 verdict: no remedy adopted (no normalisation-free systematic, no shape nuisance); the ptll misfit is reported as a characterised mis-modelling. NOLAT FREELUMI not run.

### 2026-10-20 — P2 (A0x2, THx2) and P5a (FREELUMI) done; final read-off
- Read-off scripts and outputs: `scripts/p2_summary.py` → `p2/p2_summary.{out,json}`; physical λ and faces from
  `scripts/np_lambdas.py` (container).
- All three runs: main fit status 1, optimality 2–5e-6; saturated sub-fit status 1, optimality 4–10e-6. Both are
  below gtol 1e-5, at the noise floor P1 saw, so Δq against a gtol-1e-8 point is ≲ 1e-6 by the P1 evidence.
- In all three, the same single face L2(|Y| = 2.5) is active (release ΔNLL 1.2 / 2.2 / 3.1).
- The linear χ² of the FREELUMI ptll projection (37981) is meaningless: the free normalisation makes the
  residual covariance singular. Ignore it.

### 2026-10-19 16:40 — P1_NOLAT read-off
Source: `p1_NOLAT_readoff.out`. M0 is identical to NOLAT_PF. All three sub-fits end at status 2 (xtol) with
optimality ≈ 2e-6. Nested results, q39 = 68.364:

| k | q_k / k | p | q39 − q_k | p | P3 linear capture |
|---|---|---|---|---|---|
| 3 | 22.01 / 3 | 7e-5 | 46.35 / 36 | 11.6 % | 1.5 |
| 6 | 27.30 / 6 | 1.3e-4 | 41.06 / 33 | 15.8 % | 12.6 |
| 10 | 33.63 / 10 | 2.1e-4 | 34.74 / 29 | 21 % | 31.6 (pred. remainder 35.5/29, matches) |

- **The same normalisation valley as LAT.**
  - Equal scales: 0.897 / 0.892 / 0.888 (k3) and 0.915–0.924 (k10).
  - lumi, weak and FSR relax (+1.5 / +1.1 / +0.8σ), and A0 PtV15_20 relaxes by +1.6σ.
  - α_s moves +3.7σ0 (k3) / +2.3σ0 (k10). On the NP side, λ4_ν moves +2.7–3.2σ0.
  - Prior relief 11.3, data 10.7.
  - Three faces are active in the coarse sub-fits: λ2_ν ≥ 0, the L2 face and the cubic face.
- **Read for NOLAT:** after the ~22-unit normalisation release, the remaining ptll structure is consistent with
  statistics (p 12–21 %).
- **LAT differs:** its remainder is 45.5/29, p 2.6 % at k10. LAT keeps ~10 more units of finer structure.
  - That roughly matches LAT − NOLAT in q (10.7). It is the part that P3 could not reproduce linearly, because the
    rebuilt LAT covariance misses the lattice term.
  - So the lattice's extra tension lives in the finer (wave) structure, not in the normalisation.

### 2026-10-19 15:55 — P5a (free normalisation) prepared and queued
- **`--fakelumi` no longer exists.** It was removed in WRemnants 0769d44b (2026-06-12) and replaced by
  `--lumiUncertainty 0`, which makes the existing `lumi` nuisance unconstrained with its automatic 1.2 % variation.
  - The likelihood is equivalent to the May fakelumi: a free overall normalisation of the lumi-normalised MC. In May
    the constrained lumi went to 0 and fakelumi carried the shift; now `lumi` itself carries it.
  - The fitted value is in units of 1.2 % per unit θ.
- **Card FREELUMI** (`build_cards_p2.sh FREELUMI`): the only difference from C0 is `lumi`'s constraint weight
  1 → 0. It also moves to the noconstraint list, which reorders hsysts. logk, norm and data are identical after name
  matching (`p2_card_check.txt`).
- **Fit** (`scripts/run_p5a.sh`): as P2, plus `--computeHistCov --doImpacts --globalImpacts`.
  - Warm from LAT_facefix, gtol 1e-5, preconditioner on the warm leg, the ptll saturated test.
  - `lumi` exists in the source result, so `--externalPostfit` loads its −1.46 as the start. No missing-parameter
    issue.
  - Expectations: ndfsat becomes 773. The free normalisation is exactly the sum of the 39 ptll scales (d = 1), so
    the true projected ndf is **38**; rabbit will still print 39.
- **Queued** by `scripts/chain_p5a.sh`, which enters the gate only after P2_THx2_LAT has launched.
- **Notation:** σ0 in the P1 read-off = the LAT postfit (face-held) uncertainty of that parameter. "α_s +3.6σ0"
  = Δα_s / σ(α_s, LAT postfit).
- **P2_A0x2_LAT:** at iteration 7 the loss is already 370.16, against 376.47 at the LAT minimum.

### 2026-10-19 15:15 — P1_LAT read-off; P2 launched
- **P1_LAT** (`fitresults_P1_LAT.hdf5`; read-off in `p1_LAT_readoff.out`): M0 is identical to LAT_facefix.
  - All three sub-fits end at status 2 (xtol), optimality 2e-7 / 1.5e-6 / 2e-7, which counts as converged.
  - Nested results, q39 = 79.107:

    | k | q_k / k | p | q39 − q_k | p | P3 linear capture / remainder |
    |---|---|---|---|---|---|
    | 3 | 22.19 / 3 | 6e-5 | 56.92 / 36 | 1.5 % | 2.0 / 72.1 |
    | 6 | 26.79 / 6 | 1.6e-4 | 52.31 / 33 | 1.8 % | 14.8 / 59.3 |
    | 10 | 33.59 / 10 | 2.2e-4 | 45.51 / 29 | 2.6 % | 37.7 / 36.4 |

- **Why q3 = 22 on 3 bins is large.** It is a normalisation release, not a coarse shape.
  - The coarse scales come out **equal**: s = 0.896 / 0.892 / 0.888 (k3) and 0.927–0.935 (k10). So the coarse
    models use essentially ONE degree of freedom, a free overall normalisation.
  - With it free, lumi, weak and FSR return to their priors (+1.6 / +1.1 / +0.8σ). A0 PtV15_20 relaxes by 1.7σ.
  - α_s moves +3.6σ0 (k3) / +1.3σ0 (k10), and λ4 moves +2.7 / +1.7σ0.
  - q3 splits as 11.4 prior relief + 10.7 data(+lattice).
  - The overall level (s = 0.89 vs 0.93 between k3 and k10) is not determined, because it trades against α_s and λ4.
- **This is not a contradiction with P3; it is nonlinearity.** P3's linear analysis gives the same k3 basis only
  2.0 units. Locally, a free flat scale is almost degenerate with the free α_s/λ (low information), so the linear
  χ² sees ~0. The likelihood ratio finds 22 units far along that normalisation–α_s–λ4 valley.
  - So there is a **genuine likelihood gain of ~20 units on effectively one dof**: with the absolute normalisation
    free, the ptll shape prefers a different (α_s, λ4).
  - Read physically, this is a tension between the shape-preferred α_s/NP and the normalisation allowed by
    lumi (1.2 %) + EW + FSR + σ_tot.
  - Wilks along such a nonlinear, degenerate direction is not guaranteed.
- **The remainder after the coarse shapes** (45.5/29, p 2.6 %) is larger than P3's linear prediction (36.4/29,
  LAT approximate). The P3 wave is only partly captured by piecewise-constant 2–7 GeV bins.
- **P2 launched 15:13:** P2_A0x2_LAT is out of the gate. P2_THx2_LAT is gated, waiting for P1_NOLAT to end. Both use
  gtol 1e-5.

### 2026-10-19 — P2 minimiser tolerance changed (Luca approved, via the orchestrator)
- **P2 uses `--minimizerGtol 1e-5`; P1 used 1e-8.**
- **Why:** a warm leg starts with the barrier already at or below `barrier_tol`, so the only stop condition still
  open is gtol. Optimality never reaches 1e-8 (its noise floor is ~1e-6–1e-5), so the fit sits in an xtol tail at a
  frozen point for 30–40 % of its run time.
- **Evidence from P1:**
  - LAT k3 reached optimality 1.4e-5 at iteration 40, with the loss already within 3e-8 of its final value.
  - NOLAT k3 reached 1.4e-5 at iteration 50, within 1e-7.
- **Check at the P2 read-off:** each run's final optimality, and that Δq relative to a gtol-1e-8 point would be
  negligible (≤ 1e-6).

### 2026-10-19 — P3 done (exact postfit covariance); P1 launched
- **P3_LAT and P3_NOLAT** finished on 2026-10-18 (18:53 / 19:12, ~35 min each once out of the gate):
  `fitresults_P3_{LAT,NOLAT}.hdf5`.
- **Reproduction:** both reproduce the reference numbers exactly (full saturated 752.95 / 739.44; ptll linear χ²
  91.59 / 66.46).
- **New rabbit numbers** (exact profiled residual covariance):

  | | LAT | NOLAT |
  |---|---|---|
  | ptll × 6 signed yll bands, linear χ² | 302.2/234 | 255.5/234 |
  | yll projection, linear χ² | 38.3/20 | 38.0/20 |

- **The decomposition needs the residual covariance R**, which rabbit does not save; only V_pred (`--computeHistCov`)
  is saved.
  - I rebuilt R = (1−f)(P diag(n + var_MC) Pᵀ − V_pred)(1−f), with the BB-lite MC variance from the card's
    `hsumw/hsumw2` and f = var_MC/(n + var_MC) ≈ 0.11.
  - **NOLAT:** reproduces rabbit's ptll χ² to 1 % (67.14 vs 66.46). Validated.
  - **LAT:** 74.1 vs 91.6. The rebuilt R misses the lattice term (−J C P_lat C Jᵀ), which needs the cross-covariance
    that is not saved. **LAT's decomposition is approximate.**
  - yll and the bands: 8–25 % off. Use rabbit's own band and ptll χ² for the y-test.
  - Variants that fail: with no BB, R is not positive-definite; ignoring the (1−f) shrinkage gives 53 / 59.
- **Script and output:** `scripts/p3_decompose.py` → `p3/` (`p3_numbers.json`, `p3_decompose.out`, figures).
- **P1_LAT and P1_NOLAT** launched 05:06 through the gate (node idle). Each runs 3 nested coarse-rebin saturated
  sub-fits.
- **Mapping keys:** rabbit drops the channel from the `Select` key (`Select yll:rebin(...)`). The P1 keys will be
  `Select ptll:rebin(...),yll:sum`.

### 2026-10-18 15:20 — `pull_shapes.png` fixed (labelling bug, not physics)
- **What the summarizer saw.** The y-labels of the two panels overlapped. The colours followed each panel's own
  top-7 ordering, so in the NOLAT panel the colour of the stepped curve was not the one LAT used for it, and the
  figure could be read as "lumi carries the 20 GeV step".
- **The data were never wrong.** In both fits the 20 GeV step is the SCETlib FO scale envelope
  (`resumFOScaleEnvSymDiff`, which switches on at ptVGen = 20 GeV). Lumi is pure normalisation, so once the
  normalisation is removed its curve is flat at 0.
- **Fix:** each nuisance now has one fixed colour in both panels (the union of the two fits' top-7), with a short
  y-label and an in-panel fit tag. The figure is regenerated through save_plot; no number changed.

### 2026-10-18 — Phase 2 launched (Luca approved P3 → P1 → P2)
- **P3** (`scripts/run_p3.sh`): postfit-only reruns of LAT and NOLAT.
  - Starting points: LAT `fitresults_LAT_facefix` (face-held cov), NOLAT `fitresults_NOLAT_PF`.
  - Flags: `--externalPostfit --noFit --computeHistCov --computeHistErrors --saveHists`. There is no minimisation and
    no Hessian, because the covariance is read from the external result.
  - Mappings: `Project ch0 ptll`, `Select ch0 yll:rebin(-2.5,-1.5,-0.7,0,0.7,1.5,2.5)` (ptll × 6 signed yll bands,
    234 bins), and `Project ch0 yll`.
  - Gated 15:00, waiting behind 2/2 alive gated jobs.
- **P1 design** (`scripts/run_p1.sh`, not launched yet). Nested coarse piecewise-constant ptll shapes, flat in yll:
  - k3 = [0,5,15,44] ⊂ k6 = [0,2,5,10,15,22,44] ⊂ k10 = [0,1,2,3.5,5,7,10,12,15,22,44];
  - each run as `-m Select ch0 'ptll:rebin(...),yll:sum'` with the saturated test, from the same minima;
  - q39 is already known at the same point. q39 − q_k ~ χ²(39 − k).
  - Surrogate predictions (absorbed / non-smooth remainder):

    | | k3 | k6 | k10 |
    |---|---|---|---|
    | LAT | 21.2 / 38.5 on 36 | 26.4 / 33.2 on 33 | 30.0 / 29.7 on 29 |
    | NOLAT | 13.9 / 38.8 | 18.7 / 34.0 | 26.9 / 25.8 |

    Piecewise-constant shapes absorb less than Legendre at equal k.
- **P2 cards** (`scripts/build_cards_p2.sh`): the nominal card's exact setupRabbit command (from its meta_info,
  made at WRemnants c838fc63), re-run on the current tree (74c7e3e3 + local diffs). Variants:
  - **C0** = control, no change. It must reproduce the nominal card (`scripts/compare_cards.py`).
  - **A0x2** = `--scaleParams 'helicity_0=2'` (22 nuisances).
  - **A0x3** = the same with factor 3.
  - **THx2** = A0 ×2 + `mb_|pdfMSHT20m[bc]range=2` + `^weak_|sin2thetaZ|widthZ=2` + `horace=2` + `--lumiUncertainty
    1.024144` (= 1.012², lumi is lnN), plus the ParamModel token `prior_sigmas=resumFOScaleEnvSymAvg=2,resumFOScaleEnvSymDiff=2`.
  - Fits: `scripts/run_p2.sh`, a warm refit from LAT's minimum + Hessian + ptll saturated sub-fit.

### 2026-10-17
- Task opened. Read the study logbook and the 261015-cold-tc-fits Result.
- Record sweep, delegated read-only. It covered every study logbook and summary, `knowledge/`, memory and AN-25-085.
  The condensed inventory is in Result §1.
- Extracted the saved fitresults into numpy arrays (`scripts/extract.py`; arrays kept outside the repo, in the
  session scratchpad):
  - LAT: M0 from `261016_face_held_impacts/fitresults_LAT_facefix.hdf5`, M1 (the converged saturated sub-fit) from
    `261016_saturated_subfit_diagnosis/fitresults_SATWSPC_LAT.hdf5`;
  - NOLAT: M0 and M1 both from `261016_nolat_postfit/fitresults_NOLAT_PF.hdf5`.

  M0 parms agree bit for bit between the two LAT files, and 2(NLL_M0 − NLL_M1) reproduces q exactly
  (79.1071 / 68.3635).
- Found that the fitresults hold only the ptll projection hists (data, prefit, postfit + diagonal variance). No 2D
  postfit and no ptll postfit covariance are saved. So the exact M0-side decomposition of the linear χ² and the
  per-yll-slice residuals cannot be done without a rabbit rerun (→ P3).
- First attempt: rebuild the M0 residual covariance R = I_data − V_pred from the M1 Hessian templates and the M0
  covariance (`scripts/linearize.py`). **It failed.** R has huge negative eigenvalues, because V_pred is a near
  cancellation of large α_s/λ terms and the templates at the M1 point (α_s and λ far away) break it. Abandoned.
  I kept only two pieces that do not depend on it: the per-bin BB-lite information factor, and the exact s–θ
  templates at M1.
- Built the analysis that does work (`scripts/forensics.py`, output in `forensics.out` and
  `forensics_numbers.json`):
  - (A) data-only residual statistics;
  - (B) a quadratic surrogate of q around the M1 minimum (eigenmodes, smooth-shape capture, windows, single bins);
  - (C) a linear prediction of the q change when a nuisance or group prior is widened (Sherman–Morrison-type, from
    the M0 and M1 covariances);
  - (D) ptll templates of every parameter from the M1 Hessian.
- Checked the (B) surrogate against rabbit. The card-A region sub-fits of
  [260924-ptll-tension-localization](../../lattice-cs-kernel/260924-ptll-tension-localization/LOGBOOK.md) freed
  [0,5) / [5,15) / [15,30) / [30,44) GeV and got q = 38.6 / 50.2 / 23.7 / 1.6 of 80.85, i.e. 48 / 62 / 29 / 2 %. The
  surrogate on LAT gives 40 / 60 / 32 / 2 % of its quadratic q. The pattern matches. The absolute scale does not:
  the quadratic q is 59.7 against rabbit's 79.1, so it is 25 % low.

---

## Result

**Caveats, read these first.**
1. The inputs are real data, CT18Z, the N3LL+NNLO AD cache `pdf62_y35_260921_y25`, card `260916_Z_2D_card_adcorr`
   (2D ptll × yll, 780 bins), trust-constr with hard NP constraints, BB-lite on. α_s is blinded, and no α_s value or
   shift appears here.
2. **Everything in §2–3 below "rabbit q" is a linear or quadratic surrogate built from the saved covariances. None
   of it is a rabbit fit.**
   - The surrogate around the M1 minimum reproduces rabbit's localisation pattern but underestimates q by 25 %
     (59.7 vs 79.1 LAT, 52.7 vs 68.4 NOLAT). The cause is the strong nonlinearity of M1: α_s and the NP λ wander far
     (σ ×6–130) when the 39 scales are free.
   - Read the surrogate numbers as fractions and rankings, ±30 %.
   - The prior-inflation predictions (§3) are linear in each model. At ×10 (≈ release) they are numerically
     unreliable for groups whose posterior width is close to the prior (PDF, TNP), so only ×2 and ×3 are quoted.
3. The LAT M1 is the converged combined-fix sub-fit (SATWSPC). The plain LAT sub-fit is 1.7e-4 off in q.

### Phase 2 verdict (P1 + P2 + P5a, rabbit; 2026-10-20)

**Caveats first.**
- Real data, LAT configuration (CT18Z, N3LL+NNLO AD cache, lattice, hard NP constraints), all refits warm from LAT's
  minimum.
- α_s is blinded: only differences, in units of LAT's postfit σ(α_s).
- P2 cards scale the template kfactor. A pull is therefore in units of the *widened* prior; multiply by f to get
  original σ.
- P5a uses `--lumiUncertainty 0` (the successor of `--fakelumi`). Its free normalisation is degenerate with the sum
  of the ptll scales, so the ptll ndf is 38, while rabbit prints 39.
- P2 and P5a ran at gtol 1e-5 (see Log). NOLAT variants were not run.

| run | full 2ΔNLL (Δ vs 752.95) | p | ptll q (Δ vs 79.11) | p | Δα_s / σ_LAT | σ(α_s) ratio |
|---|---|---|---|---|---|---|
| A0 ×2 | 740.25/774 (−12.7) | 80 % | 67.54/39 (−11.6) | 0.31 % | −0.44 | 0.995 |
| theory ×2 (A0, FO env, b/c mass, EW, FSR, lumi) | 730.47/774 (−22.5) | 87 % | 58.58/39 (−20.5) | 2.3 % | −0.01 | 1.26 |
| free normalisation | 736.80/773 (−16.1) | 82 % | 62.96/38 (−16.1) | 0.66 % | **+4.2** | **1.53** |

**1. Inflating the theory priors helps, but the pulls run with the prior.**
- A0 ×2 gives exactly the Δq the linear prediction gave (−11.6). Theory ×2 gives −20.5 (linear, all priors ×2:
  −24).
- The pulled nuisances do *not* relax back inside the wider prior. They sit at 1–2σ of the new width:

  | nuisance | A0 ×2 | theory ×2 |
  |---|---|---|
  | A0 PtV15_20 | −2.13 → −4.3σ original | −1.89 → −3.8σ |
  | FO envelope SymDiff | — | −2.06 → −4.1σ |
  | FSR | — | −0.99 → −2.0σ |
  | lumi | — | −1.07 → −2.1σ |

  So the data keep pulling them further: the shape these levers supply is *wanted at any width*. That is the
  signature of an uncaptured shape, not of a too-narrow envelope.
- α_s is stable against this: −0.01σ with every theory prior doubled, −0.44σ for A0 ×2. σ(α_s) grows ×1.26.
- **A0 ×3 is not needed.** The linear predictor is validated (A0 ×2 measured = predicted) and gives q ≈ 60. The
  runaway pattern is already established.

**2. The normalisation is a separate, large tension (P5a; also P1's q3 ≈ 22).**
- With the overall normalisation free, the data prefer **−12.3 ± 3.0 %** (lumi θ = −11.0 ± 2.5 in 1.2 % units).
- LR against the nominal fit: 2ΔNLL = 16.1, 1 dof → **4.0σ**.
- α_s moves **+4.2σ_LAT**, with σ(α_s) ×1.53. The NP λ (physical) move as follows:

  | λ | LAT | free normalisation |
  |---|---|---|
  | λ4 | 0.072 | 0.181 |
  | λ2 | 0.046 | 0.030 |
  | λ2_ν | 0.040 | 0.018 |
  | λ4_ν | 0.0105 | 0.0127 |
  | δλ2 | −0.0073 | −0.0048 |

- The relaxing nuisances are weak (→ 0), FSR, A0 PtV15_20 (−1.9 → −1.0) and the FO envelope (−1.5 → −1.0).
- The read: the ptll × yll *shape* prefers a different α_s/NP point, whose larger total cross-section the lumi
  (1.2 %), EW and FSR constraints forbid. The nominal fit sits at a compromise held by those priors.
- **Compared with May** (franks-vals-fit, old template NP model, walled): 6.1σ (LR 37.6) then, 4.0σ now. The
  tension is smaller with the AD model and hard constraints, but it is still there.
- Even with the normalisation free, the ptll projection is still poor: 62.96/38, p 0.66 %. That is the wave.

**3. How the 79 units decompose** (rabbit, nested):
- ~16–22: the normalisation and α_s/NP valley (P5a: 16.1; P1 coarse k3: 22.2, with equal scales).
- ~11: the coarse-to-fine wave (P1: k3 → k10, +11.4).
- 45.5/29 (p 2.6 %): what is left after k10.
- NOLAT has the same valley (q3 22.0). Its remainder after k10 is statistical (34.7/29, p 21 %). LAT's extra ~10
  units are in the finer structure.

**What the AN can say.** The ptll-projected saturated test of the 2D fit has p = 0.02 % (LAT) / 0.25 % (NOLAT). The
asymptotic p is validated by toys on the walled card. The full 2D test is good (p 70 / 81 %).

The misfit is not localised in bins and not detector-like. It is common to all rapidities (bands − ptll =
211/195, 189/195). It has two parts:

1. **A tension between the absolute normalisation and the shape-preferred α_s/NP.** Freeing the normalisation
   gains 4.0σ, at −12 ± 3 % and +4.2σ in α_s. The α_s precision therefore relies on the luminosity/σ_tot
   constraint.
2. **A y-independent, smooth ±0.2–0.3 % wave in ptll at 3–22 GeV.** The A0 scale and FO-envelope nuisances absorb
   it only by running with their priors (pulls stay at 2σ of a doubled prior). It is genuinely uncaptured. α_s is
   insensitive to it: doubling every theory prior moves α_s by 0.01σ and raises σ by 26 %. The ptll p-value then
   improves to 2.3 %.

Item 1 is the one with α_s consequences and needs a decision. Options are a normalisation-free α_s fit as a
systematic, or a closer look at σ_tot (PDF/α_s normalisation) versus lumi.

### P3 (rabbit, exact postfit covariance): where the ptll misfit lives (2026-10-19)

**Caveats first.**
- These numbers decompose the **linear** postfit χ², not the saturated q. The two agree for NOLAT (66.5 vs q 68.4);
  for LAT the linear χ² (91.6) is above q (79.1).
- The residual covariance is rebuilt from rabbit's V_pred plus the card's BB-lite MC variance. It is **validated for
  NOLAT** (1 %) and **approximate for LAT** (74 vs 92, the lattice term missing).
- Every y-band statement below uses rabbit's own printed χ² values, which are exact.

| | LAT | NOLAT | Phase-1 surrogate said |
|---|---|---|---|
| ptll linear χ² (rabbit) | 91.6/39 | 66.5/39 | — |
| **y-dependence**: χ²(ptll × 6 yll bands) − χ²(ptll) (rabbit) | 302.2 − 91.6 = **210.6 / 195, p 21 %** | 255.5 − 66.5 = **189.1 / 195, p 61 %** | (card-A record: 189/195) |
| share in flat + linear + quadratic + cubic shape (k ≤ 4 Legendre) | 1.6 % | 1.2 % | 41 % / 28 % (**wrong**) |
| share absorbed by 7 / 10 smooth Legendre parameters | 42 % / 53 % | 37 % / 48 % | 52 % / 54 % |
| non-smooth remainder after 10 Legendre parameters | (34.6/29, approx.) | 35.0/29, p 20 % | 29/29 |
| region share [0,5) / [5,15) / [15,30) / [30,44) GeV | 16 / 55 / 23 / 3 % | 14 / 54 / 25 / 3 % | 40 / 60 / 32 / 2 % (low ptll **×3 too high**) |
| leading eigenmode of R | 24.8 of 74.1 (6 sign changes) | 18.8 of 67.1 (6 sign changes) | — |
| largest single-bin score | 13.4, bin 5.0–5.5 GeV | 11.0, bin 5.0–5.5 GeV | 7.5 (**too low**) |

**The y-independence is now exact** on the current fits: the ptll residual is common to all six yll bands
(p 21 % / 61 %).

**Where the surrogate was wrong.** It saw "low-order (flat/linear)" content. That was the α_s/NP-degenerate drift of
the saturated minimum, not misfit: at M0 the fit has already absorbed every flat, linear and quadratic component
(< 2 %). The misfit is a **mid-frequency wave**. It overestimated the share below 5 GeV by ×3 (NP degeneracy) and
underestimated the 5.0–5.5 GeV bin.

**The wave** (NOLAT, validated):
- −0.15 to −0.2 % at 5–6 GeV;
- +0.25 to +0.3 % at 9–12 GeV;
- −0.15 to −0.25 % at 16–20 GeV, returning to 0 at 20 GeV.

A 10-parameter smooth shape absorbs half of the χ². What remains (35/29, p 20 %) is χ²-consistent. One covariance
mode with 6 sign changes over 0–44 GeV carries 19–25 units, against ~1 expected.

The 5.0–5.5 GeV bin alone has single-bin score 11.0 (local p 9e-4, ≈ 3.5 % after 39 trials). So it is a visible
dip, but alone it would not make the test fail.

![P3: residual, leading mode and best smooth shapes](p3/leading_mode_and_smooth_fit.png)

*The red curve's shape is an eigenvector of R, so it is built from the model covariance (cf. the 2026-09-24
retraction in the record); only its amplitude comes from the data. The blue Legendre fits are not covariance-shaped,
and they show the same wave.*

![P3: exact smooth capture vs the phase-1 surrogate](p3/smooth_capture_exact.png)

**Read.** Revised from Phase 1 ("smooth, low-order"):
- the misfit is a smooth **wave of ±0.2–0.3 % with a ~10 GeV period between 3 and 22 GeV**;
- it is common to all rapidities;
- it is in neither the normalisation nor the overall tilt;
- the bin-to-bin structure beyond it is statistical.

A ~10 GeV wave is above the dimuon pT resolution scale (≲ 1 GeV), so it is not resolution or binning. Its nodes sit
near the gen-ptV edges of the A0 scale nuisances (5, 7, 9, 11, 15, 20 GeV) and the FO-envelope switch-on (20 GeV).
This is a suggestive coincidence, not evidence (the nuisances are pulled to follow the data).

### 1. What the record has already tested

This is the condensed inventory. The record sweep is not reproduced. Every line has its evidence path.

Prefixes: `S/` = `WRemnantsHelpers/studies/`, `K/` = `knowledge/`.

#### Statistical / technical

| hypothesis | test done | result | evidence | status |
|---|---|---|---|---|
| under-minimised saturated sub-fit | converged rerun (warm start + preconditioner) | q 79.10711 vs 79.10694; NOLAT release leg Δq 6.7e-4 | `S/ct18z-nominal-fits/261016-saturated-subfit-diagnosis/` | **ruled out** |
| Wilks / asymptotic p wrong | 112 toys, walled card-A fit CCWALLWARMPF | toy mean 37.7 (sd 8.5) vs 39; data 70.39: 0/112 above, p < 2.6 % (95 % CL), scaled tail 0.08 % | `K/20_frameworks/saturated_test_toys.md` | **ruled out** for card A walled; not redone for LAT/NOLAT |
| ndf miscount (d ≠ 0) | rank check of the M1 Hessian | d = 0, ndf 39 correct; α_s 98 % degenerate with the scales | `K/20_frameworks/saturated_gof_tests.md` §4 | **ruled out** |
| BB-lite / MC stat | `--noBinByBinStat` (Apr); BBB on/off at a fixed point (Sep) | ptll gets worse without BBB | `S/projection_pvalues/LOGBOOK.md` T4; `S/scetlib-ad-param-model/260911-gof-vs-scetlibnp/` | **ruled out** |
| blinding / machinery | Asimov closure; same blinding seed in M0 and M1 | Asimov q = 0 exactly | `S/scetlib-ad-param-model/260914-saturated-projection-fix/` | **ruled out** |

#### Theory

| hypothesis | test done | result | evidence | status |
|---|---|---|---|---|
| NP form / physicality | wall on/off, NP λ frozen, λ∞_ν free, λ4_ν = 0, tanh_2/6, lattice | only unphysical minima reach q ≈ 56 (λ2_ν < 0); NP λ freedom worth < 1 unit inside the physical region | `S/lattice-cs-kernel/260924-ptll-tension-localization/`; `S/lattice-cs-kernel/260925-1d-fits/` | **ruled out** inside the physical region |
| PDF | MSHT20 AD fits | 68.0–68.4 vs CT18Z 70.3 | `S/msht20-ad-campaign/260929-fits-msht20/` | **ruled out** |
| matching / transition, 20 GeV step | ptll < 20 GeV fit (T15); 2-GeV rebin (T14) | ~10 of 67 units above 20 GeV; coarser bins make it worse ("real, smooth shape") | `S/projection_pvalues/LOGBOOK.md` T14, T15 | **weakened** as the main source |
| qT [0, 0.5] / low-ptll cache | ptll > 1.5 GeV cut; `merged_full_bin0xzero` | 70.39 → 68.30/37 | `S/alphas-scan-discontinuity/260925-ptll-gt1p5-fit/` | **ruled out** |
| A0 (MiNNLO helicity_0 scale) mis-modelled | pulls across 7 fits; 2D vs 4D pulls; freeze (T6); ×2 (T13, 4D old model) | PtV15_20 at −1.9σ in every fit; the pull halves in 4D; T13 made the *linear* ptll χ² worse (73.3/40, old model) | `S/lattice-cs-kernel/260924-ptll-tension-localization/`; `S/projection_pvalues/LOGBOOK.md` T6, T13 | **open** (template / 4D test never run) |
| b/c-mass effects in the resummation | freeze mb (T7, worse); mb ×10 in loose-NP (51.8 → 47.5); mb_up pulled −1.5 to −2 | absent from SCETlib qT evolution (AN `uncerts.tex:246`) | `S/projection_pvalues/LOGBOOK.md` T7; `S/loose_NP_followup/` | **open**, never tested directly |
| QED / FSR | FSR nuisance pulled −1.0 to −1.2 | — | localisation task | **open**, never tested |
| resummation order (N4LL / N3LO), helicity smoothing | — | no ptll-projection GoF result exists | — | **never tested** |

#### Detector

| hypothesis | test done | result | evidence | status |
|---|---|---|---|---|
| muon resolution / calibration / smearing | Apr T10: all 3334 detector nuisances absorb 0.5 of 38.5; smearing splines tried on the unfolding card only | — | `S/projection_pvalues/LOGBOOK.md` T10; `S/z-data-unfolding/261012-ab-muon-calib/` | **weakened** (§3 below); never tested with a template on the reco card |
| efficiencies, prefire | freeze effSyst (T5: 67.41 → 67.44); prefire / eta (F10: null) | — | `S/projection_pvalues/LOGBOOK.md` T5; `S/loose_NP_followup/` | **ruled out** |

#### Binning / dimensionality

| hypothesis | test done | result | evidence | status |
|---|---|---|---|---|
| 4D angular tension leaking into ptll | 2D-only refit (T12) | ptll unchanged | `S/projection_pvalues/LOGBOOK.md` T12 | **ruled out** |
| yll-dependent cause (PDF, flavour mix, efficiency vs \|y\|) | ptll in 6 signed yll bands vs ptll (PTxYB6) | 189 / 195 extra dof: the wanted ptll correction is **y-independent** | `S/lattice-cs-kernel/260924-ptll-tension-localization/` | **ruled out** |
| unfolding-specific | gen-level ptV saturated test | also fails (60.4/20) | `S/z-data-unfolding/261009-saturated-ptvgen/` | consistent with a model-side cause |

**History.** The ptll projection has been poor in every physical-NP fit since April 2026, across:
- the scetlib_np, btgrid and AD models;
- CT18Z and MSHT20;
- with and without the lattice;
- the 1D, 2D and 4D cards.

The values run from 56 to 81 out of 39. The only exceptions are unphysical NP minima (q ≈ 52–56) and loose priors
(p 5–8 %).

**The AN** (AN-25-085) has no GoF or projection discussion. Its results are Asimov placeholders
(`detector_extraction.tex:69`).

### 2. Where q comes from (this task; LAT / NOLAT)

**(a) The visible residuals are white noise.** In the data-stat-only metric, z_j = (data − postfit)/√data:

| | LAT | NOLAT | white-noise expectation |
|---|---|---|---|
| Σz² | 41.5/39 (p 36 %) | 39.7/39 | ≈ 39 |
| lag-1 autocorrelation | 0.15 | 0.11 | ≈ 0 |
| sign changes | 19 | 18 | ≈ 19 |

- Smooth Legendre fits to z absorb what noise would (order 5: 5.6 units).
- The bins at 5.0–5.5, 17–18 and 20–22 GeV are z = −2.7, −2.4 and −2.1. In 39 bins, 4 entries with |z| > 2 against
  1.8 expected has P(≥ 4) ≈ 10 %.
- **The ratio-panel excursions are not where q comes from.** No single bin is anomalous: the largest single-bin
  score in the surrogate is 7.5 (5.0–5.5 GeV), below the ~9 expected for the maximum of 39 χ²(1) terms.

![per-bin view: data-only pulls, single-bin scores, saturated free scales](perbin_view.png)

*Caveat for the figure:* the middle and bottom panels come from the quadratic surrogate at the M1 minimum (not
rabbit). The free scales ŝ (bottom) are large and smooth (−11 % … +12 %) because they are degenerate with α_s and
the NP λ, which move far in M1. They are not the "wanted correction".

**(b) q is in what the fit pays, not in the residual.** This split is exact, from the saved parameter vectors:

| | LAT | NOLAT |
|---|---|---|
| q | 79.11 | 68.36 |
| constrained-nuisance prior relief, Σ(θ₀² − θ₁²) | 21.3 | 19.6 |
| data + BB (+ lattice for LAT) improvement | 57.8 | 48.7 |

- The relief comes from the same handful of nuisances in both fits. Units are 2ΔNLL, pulls go M0 → M1:

  | nuisance | pull, LAT (M0 → M1) | relief, LAT | relief, NOLAT |
  |---|---|---|---|
  | A0 scale `QCDscaleZfine_PtV15_20helicity_0` | −1.89 → −0.15 | 3.5 | 3.3 |
  | SCETlib FO scale envelope `resumFOScaleEnvSymDiff` | −1.48 → −0.05 | 2.2 | 2.0 |
  | lumi | −1.46 → 0.00 | 2.1 | 2.1 |
  | mb_up | −1.56 → −0.89 | 1.6 | 1.5 |
  | `weak_default` | −1.13 → −0.02 | 1.3 | 1.2 |
  | FSR (`horace…FSR_Corr0`) | −1.10 → −0.05 | 1.2 | 0.9 |

  The other A0 PtV bins add 0.4–0.7 each.
- Same structure as card A (data 53, card 16.5, model 6.1, lattice 5.2 of 81;
  `S/lattice-cs-kernel/260923-lattice-fits/`).
- The muon resolution, scale and efficiency nuisances do not relax: Resolution Σpull² goes only 4.9 → 4.0, muon
  scale 2.5 → 2.7.

**(c) Where in ptll (surrogate).** Fraction of the quadratic q absorbed by freeing only a region:

| region (GeV) | LAT | NOLAT | card-A rabbit (LATL4ZWALLCOLD) |
|---|---|---|---|
| [0, 5) | 40 % | 49 % | 48 % |
| [5, 15) | 60 % | 51 % | 62 % |
| [15, 30) | 32 % | 26 % | 29 % |
| [30, 44) | 2 % | 1 % | 2 % |

- The fractions overlap because each region is re-profiled separately.
- The tension spans 0–22 GeV, with no single localised window. The sliding windows peak at 1–5 GeV and 16–22 GeV
  (`window_scan.png`).

> **SUPERSEDED 2026-10-19 by P3 (Result "P3").** The low-order capture below (k = 1–5, flat mode 16–21 units) is the
> α_s/NP drift of the saturated minimum, not misfit. In rabbit's postfit covariance, flat to cubic shapes carry < 2 %,
> and the misfit is a ±0.2–0.3 % wave with a ~10 GeV period; 10 smooth parameters leave 35/29. The share below 5 GeV
> was ×3 too high. Kept for the record.

**(d) Smooth versus bin-to-bin (surrogate, SUPERSEDED).** Replace the 39 free scales by a free
smooth shape with k Legendre parameters, flat in yll:
- k = 5 absorbs 31 of 59.7 units (LAT) and 26–31 of 52.7 (NOLAT), against ~5 expected from noise.
- The non-smooth remainder is χ²-consistent:

  | | non-smooth remainder | p |
  |---|---|---|
  | LAT | 29/34 (26/34 in s = x² coordinates) | 72 % |
  | NOLAT | 26/34 (22/34) | 82 % |

  Scaled up by the 25 % surrogate deficit it becomes ~35–38/34, still p ~ 30 %.
- **So the excess is a smooth, low-order ptll shape. It is not bin-to-bin structure** (resolution, binning or MC
  stat would show up as bin-to-bin).
- This agrees with April T14, where coarser bins made it worse. It is the opposite of the "no smooth shape can
  reproduce it" branch of the question.
- The k = 1 (flat normalisation) mode alone carries 16–21 units for LAT but 5–12 for NOLAT. That part depends on
  the coordinates (nonlinear) and is not interpreted further (→ P5a).

![fraction of the quadratic q absorbed by a free smooth shape with k parameters](smooth_capture.png)

*Surrogate, not rabbit: the confirming test is P1.*

> **Partly superseded 2026-10-19:** the templates are exact, but the summed "wanted shape" is a linear surrogate. Read
> it only as which nuisances carry which ptll features. The data-side shape is P3's wave
> (`p3/leading_mode_and_smooth_fit.png`).

**(e) What the pulled nuisances do to ptll.** Each pulled nuisance's ptll template (exact, from the M1 Hessian)
is multiplied by its M0 → M1 pull change, with the normalisation removed:
- the sum is a smooth +0.4 % bump at 8–14 GeV and a −0.7 % trough at 20–33 GeV;
- the 20 GeV edge comes from the SCETlib FO scale envelope, which "vanishes for ptVGen < 20 GeV"
  (AN `uncerts.tex:178`), and from A0 PtV15_20;
- in normalisation, the pulls lower the prediction by ~5 % at the M1 point (lumi, EW, FSR).

![nuisance-induced ptll shape, M0 − M1](pull_shapes.png)

*Linear templates evaluated at the M1 point.* The step edges are inherited from how the nuisances are binned in
gen ptV, so the underlying data feature may be smoother (cf. the localisation-task retraction).

**(f) Other diagnostics.**
- **yll slices:** not computable from these files, since no 2D postfit is saved (→ P3). The card-A band test
  already showed the wanted correction is y-independent.
- **BB-lite:** MC stat reduces each ptll bin's information by 10–13 % (σ_MC/σ_data ≈ 0.35). It is already in q.
- **Eigenmodes:** the eigenmodes of the scale information are not ordered by smoothness, so that split is less
  telling (`eigenmodes.png`). LAT has one 6-sign-change mode carrying 17 units.

### 3. Would wider priors absorb it? (linear prediction, never run in rabbit)

Predicted drop of q (LAT / NOLAT) when a group's prior is widened. The method is in the Log (part C):

| group | ×2 | ×3 |
|---|---|---|
| A0 scale (helicity_0, 22) | −11.6 / −10.8 | −18.9 / −17.7 |
| lumi | −4.6 / −4.4 | −8.3 / −8.0 |
| b/c mass (mb, MSHT20 mb/mc range) | −4.4 / −3.8 | −8.4 / −6.9 |
| QED FSR | −3.2 / −2.6 | −6.6 / −5.4 |
| EW (weak, sin²θ, Γ_Z) | −3.2 / −3.1 | −6.5 / −6.3 |
| effSyst | −2.6 / −2.8 | −4.6 / −4.8 |
| PDF eigen | −2.5 / −2.0 | −6.3 / −4.8 |
| SCETlib TNP | −2.4 / −2.2 | −5.5 / −4.7 |
| SCETlib FO env | −2.3 / −2.1 | −2.9 / −2.7 |
| muon resolution | −1.6 / −1.5 | −3.0 / −2.5 |
| muon scale | +0.3 / +0.3 | +0.4 / +0.5 |
| **all constrained ×2** | **−24.3 / −21.8** | |

Read as predicted q and p (LAT / NOLAT):

| change | predicted q | p |
|---|---|---|
| A0 ×2 | 67.5 / 57.6 | 0.3 % / 2.8 % |
| A0 ×3 | 60.2 / 50.7 | 1.6 % / 10 % |
| all constrained ×2 | 54.8 / 46.6 | 4.8 % / 19 % |

![linear Δq for prior inflation by group](group_release.png)

**The record has a counter-indication.** April T13 (A0 ×2, 4D card, old scetlib_np model) made the *linear*
postfit ptll χ² worse, 67.4 → 73.3/40. That is a different statistic, model and card, and an era whose
projected-test numbers were not reproducible (`S/projection_pvalues/`). So it does not refute these numbers, but
it is the reason to confirm them in rabbit (P2).

### Physics read

The ptll projection fails because:
- the data's ptll spectrum carries a **smooth, few-per-mille shape** below ~22 GeV;
- that shape is **y-independent**;
- the model can reproduce it only by a coordinated 1–2σ pull of the theory-type nuisances (A0 scale in 15–20 GeV,
  the SCETlib FO envelope, mb, EW, FSR, lumi);
- the yll-differential data, the other priors and (in LAT) the lattice do not want that pull.

The 2D test (p 70 / 81 %) dilutes this in 774 dof. The projection concentrates it in a few smooth modes.

It is not:
- a bin-level feature (the residuals are white; the non-smooth part is χ²-consistent);
- detector resolution or scale (no relaxation, and ≤ 1.6 units even at ×2);
- MC stat, the minimiser, ndf or Wilks (record + §2);
- the NP form within the physical region (record).

That makes it, as far as the existing tests go, a **genuine mis-modelling of the ptll shape at the 0.2–0.5 % level
that the current nuisance model captures only at ~1.5–2σ tension**. Its size is of the order of the A0 / scale
envelopes (×2–3 of the A0 prior, or ×2 of everything, would absorb most of it, per the linear prediction).

Candidate physics already ranked in the record are open and never tested with templates:
- b/c mass effects in the resummation (AN `uncerts.tex:246`: "no estimation is available yet");
- QED;
- the A0 modelling.

Whether α_s cares is P2's Δα_s, not answered here.

### 4. Phase-2 proposals, ranked by decisiveness per cost (none run)

| # | test | how | cost | pass / fail reading | what the AN could say |
|---|---|---|---|---|---|
| **P1** | **rabbit smooth-shape test** (iii) | one `--externalPostfit --noFit --computeSaturatedProjectionTests` job per fit, with extra mappings `Select ch0 ptll:rebin(<k+1 edges on existing bin edges>),yll:sum` for k = 3, 5, 7. Piecewise-constant coarse free shapes are nested in the 39-scale model, so q₃₉ − q_k ~ χ²(39 − k) if the rest is noise. No new code. (Variant: a Legendre `ParamModel`, ~50 lines.) | 1 cache load + 3 warm/preconditioned sub-fits per fit, ~4–8 h, ~260 GB | **pass**: q₃₉ − q₅ ≈ 34 ± 8 and q₅ ≫ 5 → smooth. **fail**: remainder ≫ 34 → bin-to-bin structure (resolution, binning, MC stat). The surrogate predicts pass. | "The projected tension is carried by a smooth ptll distortion of a few per mille. With a k-parameter smooth correction the remaining ptll structure is consistent with statistics (p = …)." |
| **P2** | **group prior inflation** (ii); the never-run test Luca proposed on 2026-09-24 | new cards via setupRabbit `--scaleParams 'helicity_0=2'` (and ×3), mb/mc range, FSR, EW, lumi; ParamModel groups via `prior_sigmas`. Warm main fit from LAT / NOLAT + postfit + sub-fit. Do NOLAT first (faster); 4 variants: A0 ×2, A0 ×3, all theory ×2, all ×2. | per variant: card build (minutes, no cache) + ~5 h fit chain; 4 variants ≈ 1 day of node time per fit | **pass**: one physically motivated group at ≤ ×2–3 brings q to ≲ 50 (linear: A0 ×3 → 50.7 NOLAT) → "the tension is within ~×N of our theory envelope", and Δα_s under that inflation becomes an AN systematic check. **fail**: q stays > 60 even with everything ×2 → genuinely uncaptured. | either a quoted inflation factor plus Δα_s, or "not covered by any ×2 inflation" |
| **P3** | **exact M0-side decomposition + yll slices** (new: the record never saved it) | `--externalPostfit --noFit --computeHistCov --saveHists` with `-m 'Project ch0 ptll'`, `-m 'Select ch0 yll:rebin(-2.5,-1.5,-0.7,0,0.7,1.5,2.5)'` (the ptll × yll-band 2D), on LAT and NOLAT. Gives the profiled residual covariance behind the linear χ² 92 / 66, so the eigenmode, bin and smooth decompositions become exact (they replace §2's surrogate), plus per-yll-band ptll residuals for the current fits. | 1 cache load + postfit, no minimisation, ~1–1.5 h per fit | not pass/fail: removes the surrogate caveat from §2, and checks the y-independence on the current card | supporting figures: residual modes and per-yll-band residuals |
| P4 | **toy calibration of LAT / NOLAT** (iv) | `saturated_test_toys.md` recipe adapted to trust-constr + hard constraints (truth = postfit vector, faces active). Several sequential toys per process, since each process loads a 236 GB cache. | ~50 toys ≈ 2 processes × 25 × ~3 h ≈ 3 days | **pass**: toy mean ≈ 39 → Wilks p stands. NOLAT has active bound faces (λ2_ν = 0), so a χ²-mixture shift is possible. | "toy-calibrated p = …". Low priority: card-A toys already validate Wilks for this statistic (0/112 above 70.4). |
| P5a | **shape vs normalisation** (new) | card with lumi unconstrained (`--noConstrainParams lumi`, d = 1, ndf 38), or a free overall norm | card + warm fit chain, ~5 h | separates the flat-mode share (surrogate: 5–21 units, unstable) from the shape share | whether the tension involves the absolute σ_fid × lumi or the shape only |
| P5b | **step artefacts of our own nuisance model** (new) | the FO scale envelope switches on at ptVGen = 20 GeV, and A0 is decorrelated in PtV bins with edges at 5, 7, 9, 11, 15, 20, 40. Test a smooth turn-on (or a correlated A0 across PtV) and measure Δq. | card variant + fit chain, ~5 h | if q moves by ≫ 2 units, part of the projected tension is an artefact of how the uncertainty is parametrised, not of the data | robustness of the GoF to the nuisance parametrisation |
| P6 | **physics templates** (b/c mass in the resummation, QED ISR/FSR, 4D with A0 free) | need new theory inputs or a 4D fit (proposed 2026-09-24, never run) | days to weeks | this is the route to *identifying* the cause, beyond characterising it | — |

**Recommended order:** P3 (cheap, exact) → P1 (answers smooth vs bin-to-bin in rabbit) → P2 (answers "covered by
inflation?" and gives the α_s systematic). P4 only if the AN reviewers ask for toys on this exact setup.

---

## Findings

1. The ptll marginal postfit residuals of LAT / NOLAT are statistically ordinary (data-only Σz² 41.5 / 39.7 of 39, no
   autocorrelation, no anomalous single bin). The 5 / 17 / 21 GeV excursions are not the source of q. (evidence:
   `forensics.out`, `perbin_view.png`)
2. Exact q partition: 21.3 / 19.6 units are constrained-prior relief, led by A0 PtV15_20, FO env SymDiff, lumi,
   mb_up, weak and FSR. This is the same pattern as all card-A fits. (evidence: `forensics_numbers.json`)
3. **SUPERSEDED 2026-10-19 by P3:** the misfit is a mid-frequency wave (~10 GeV period, ±0.2–0.3 %), not a
   low-order shape. 10 smooth parameters leave 35/29 (NOLAT, validated).
   Original surrogate text: a 5-parameter smooth ptll correction absorbs the whole excess, and the remainder is 29/34 (LAT) and
   26/34 (NOLAT). The tension is smooth, not bin-to-bin. To be confirmed by P1. (evidence: `smooth_capture.png`)
4. Linear prediction: A0 prior ×2 lowers q by ~11, ×3 by ~18, all priors ×2 by ~22–24. Detector groups by ≤ 1.6.
   Never tested in rabbit; P2. (evidence: `group_release.png`)
5. **Method:** the saturated sub-fit Hessian gives exact ptll templates of every parameter
   (H1[s_j, θ_k] / (s_j H1[s_j, s_j])), with no cache needed.
   - The M1-frame quadratic surrogate reproduces rabbit's region-localisation fractions but underestimates q by
     ~25 %.
   - Rebuilding the M0 residual covariance from M1 templates FAILS, because the near-degenerate α_s/λ cancellation
     breaks. Do not try it.
   - Worth a line in `K/20_frameworks/saturated_gof_tests.md`; tell the orchestrator.
6. BB-lite costs each ptll bin 10–13 % of its information (σ_MC/σ_data ≈ 0.35 at projection level).

---

## Open questions

- The flat (normalisation) mode carries a coordinate-dependent 5–21 units of the surrogate q. It differs between
  LAT and NOLAT by about the full LAT − NOLAT Δq (10.7). Does the lattice's extra tension go mainly into the
  normalisation (via the CS kernel's effect on σ_fid)? → P5a / P3.
- **The fitresults should save the ptll postfit covariance by default** (`--computeHistCov`). It costs nothing at
  postfit, and without it every decomposition is a surrogate. Suggest adding it to `workflows/fitterAD.sh`.
- The A0-scale and FO-envelope nuisances have hard gen-ptV edges (5, 7, 9, 11, 15, 20, 40 GeV; FO env only above 20
  GeV). The fit uses them as piecewise levers. Their step shapes are a modelling choice that the GoF partly measures
  (P5b).
