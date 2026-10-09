---
title: Is the LATL4ZUNWCOLD postfit prediction a valid cross section?
slug: 260924-unwcold-xsec-validity
study: lattice-cs-kernel
status: done
created: 2026-09-24
updated: 2026-09-24
owner: study-worker
---

# Is the LATL4ZUNWCOLD postfit prediction a valid cross section?

**Task:** At the converged minimum of the unwalled cold lattice fit LATL4ZUNWCOLD, is the predicted cross section valid (positive, smooth in qT, AD Jacobian = finite differences), or did the fit converge onto a nonsense prediction where the TMD anti-damps (L2 = λ2 + δλ2·Y² < 0 at |Y| = 2.5)?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-09-24)

> **COLD (LATL4ZUNWCOLD): invalid at the minimum.** It converged onto a numerical artefact of the AD cache in the most forward gen bin (2.0<|Y|<2.5, qT<1.5 GeV): the qT 0–0.5 GeV bin is ×0.52 of its smooth value, the tune sits 0.003 in L2 from σ<0, and λ4 is parked on a kink about 1e-4 wide at 0.
> **WARM (LATL4ZUNWWARM, lower loss 375.53): numerically valid.** σ is positive and smooth in all 770 bins, and AD = FD to 1e-9, even though L2 < 0 at every |Y| (−0.078 at 0, −0.138 at 2.5). Its large λ4 = 0.096 restores damping at large b_T. It is still **physically** anti-damped at small b_T: f^NP > 1, up to +3% at |Y|=0 and +11% at |Y|=2.5, for b_T ≲ 1–1.5 GeV⁻¹. That is outside the wall's L2(Y) ≥ 0 region.
> **What sets the validity edge is λ4, not L2 alone.** Invalid ⇔ L2(Y)<0 with Λ4 + L2³/3 ≲ 0, i.e. no large-b damping. At λ4≈0 the edge is at L2(2.5) ≈ −0.015 to −0.02 (onset), with σ<0 at −0.034. At λ4 = 0.096, L2(2.5) down to −0.15 is clean. At the warm L2, degradation starts at λ4 ≲ 0.03 and is catastrophic at λ4 = 0.
> Caveats first: in all model evaluations α_s is held at the cache anchor (0.118), not the fitted value. The rabbit-stored postfit is only the yll-summed ptll projection. The warm fit's stored postfit (check 1) is **deferred**: its fitresult is still locked by the running projection sub-fit.

- **Next action:** none for this task. Check 1 for WARM is one command once its fitresult is closed: `./agent_setup.sh -- python <task>/scripts/check1_ptll.py && ./agent_setup.sh -- python <task>/scripts/plot_check1.py`. Both scripts already include LATL4ZUNWWARM.
- **Blocking on:** nothing, apart from WARM check 1, which waits on its running sub-fit (iteration 110 at 09:27; the cold one took 445).

---

## Log

### 2026-09-24 (scope addition from the orchestrator: LATL4ZUNWWARM)
- **Warm fit, check 2.** Input: the converged snapshot `l4zero_unwalled_warm/snapshot_fitresults_LATL4ZUNWWARM.hdf5` (the log says "snapshot (converged)", EDM 3.6e-16). α_s is dropped at read time, so it sits at the cache anchor. Everything else is the warm postfit.
  - Physical tune: λ2 −0.0784, δλ2 −0.00949, λ4 0.0956, λ2_ν 0.0905, λ4_ν 0. So L2 = −0.078 at |Y|=0 and −0.138 at |Y|=2.5.
  - **Result:** min σ 0.143, nothing ≤ 0. The oscillation metric is 0.029, at the smooth baseline of ~0.02–0.03.
  - AD vs central FD agrees to 1e-9 at h = 1e-6 to 1e-4 for λ2, δλ2 and λ4 alike, and fwd/bwd agree to 1e-3 even at h = 1e-4. **Numerically valid.**
  - Evidence: `check2c_summary.json`, `logs/check2c_warm.log`, `logs/analyze_check2c.log`.
- **L2 scan from the warm tune** to L2(2.5) = −0.15, via δλ2 (λ2 fixed, so L2(0) stays at −0.078) and via λ2 (δλ2 fixed), step 0.01: **clean at every point**. σ>0, oscillation at baseline (≤0.03), AD=FD ≤ 1e-8.
- **Cold-tune scan extended** to −0.15 (λ4 = −2.5e-5): σ reaches −1e3 at −0.07, −1e5 at −0.10, and −1e6 at −0.138. Garbage.
- **λ4 scan at the warm L2** (λ2, δλ2 at the warm values):

  | λ4 | oscillation | forward qT<0.5 vs warm | AD/FD |
  |---|---|---|---|
  | 0.06 | 0.036 | — | clean |
  | 0.03 | 0.045 | +10% | clean |
  | 0.01 | 0.083 | +21% | clean |
  | 0.005 | 0.13 | — | — |
  | 0.002 | 0.22 | +32% | 1e-3, fwd/bwd 9% |
  | 0 | σ = −4e5 in 20 bins | — | — |

  So at this L2 the prediction starts to go non-smooth below λ4 ≈ 0.03. The warm tune (0.096) has about a factor 3 of margin.
  ![warm forward row](warm_Yrow10_lambda4_scan.png)
  *Gen level, 2.0<|Y|<2.5, α_s at the cache anchor. Black is the warm tune. Coloured lines are the warm tune with λ4 lowered. Green dashed is the walled-fit tune, within ~3% of the warm tune at qT<1 GeV.*
- **Physics of the edge:** f^NP(b_T,Y) is evaluated from the tanh_2 form (Λ∞=1; the cache runs `np_model = tanh_2`) for the three lattice fits.
  - **Cold:** f^NP grows without bound at |Y|=2.5, reaching 1.7e4 at b_T=12 GeV⁻¹. This is the artefact source: the b-space integrand explodes.
  - **Warm:** f^NP peaks at 1.03 (|Y|=0) and 1.11 (|Y|=2.5), at b_T ≈ 0.6–0.9 GeV⁻¹, then damps like the walled fit.
  - **Walled:** f^NP ≤ 1 everywhere.
  - Evidence: `logs/plot_tmd_fnp.log`.
  ![TMD NP factor](tmd_fnp_three_fits.png)
  *Analytic, from the fits' physical TMD λ. No α_s and no cache involved. The form is from knowledge/…/np_parametrization_constraints.md §1 (tanh_6 minus the Λ6 term).*
- **LATL4ZWALLCOLD fitresult is now written.** Its final θ equals the 07:37 snapshot used as `wallB` (λ2 0.028, λ4 0.0869), so the walled baseline above is the final walled fit.
  - Check 1: min postfit 1.02e5 and no bin ≤ 0. It has the best lowest-ptll bin of the four fits: postfit/data 1.0007, vs 1.0052 (cold unwalled) and 1.0060 (CCCOLDSELF). Projection χ² 83.1/39, sub-fit EDM 1.9e-7. (evidence: `logs/check1_ptll.log`)
- The LATL4ZUNWWARM fitresult is locked by its running sub-fit, so it was not read and **check 1 for WARM is deferred**. The running job was not touched.

### 2026-09-24
- **Check 1, rabbit-stored postfit yields.** `--saveHists` with `-m Project ch0 ptll` stores only the 39-bin ptll projection (summed over yll). The full 2D (ptll, yll) postfit is **not** in the fitresult, so the per-yll check cannot be done from it (evidence: `logs/check1_ptll.log`).
  - LATL4ZUNWCOLD: no bin ≤ 0 (min 1.02e5). The projection is smooth, and postfit/data is within ±0.65% in every bin. The low-ptll pattern matches CCCOLDSELF's to a few 0.1%. The projection χ² is 93.2/39, vs 77.4/39 for CCCOLDSELF.
  - The main-fit EDM is 6.3e-7. The ptll sub-fit failed with trust-krylov "bad approximation" after 445 iterations, EDM 0.026. (CCCOLDSELF's sub-fit also ends on "bad approximation", but with EDM 2.9e-5.)
  - LATL4ZWALLCOLD's fitresult is locked by its running process, so it was **not read** (the running job was not touched).

  ![stored postfit ptll projection](check1_postfit_ptll_projection.png)
  *Summed over yll. Per-yll postfit hists are not saved. A defect confined to one yll bin at ptll<1.5 GeV would be diluted here.*
- **Check 2, direct model evaluation.** Cache `pdf62_corrgrid_260827/merged_full`, build authval b66f8de (`agent_setup.sh --scetlib authval`), `ScetlibADXsec` directly on the 770 cache bins (11 |Y| rows × 70 qT bins, |Y| ≤ 2.5).
  - **α_s is at the cache anchor (θ_αS = 0, i.e. 0.118) at every point.** The fitted α_s is never read: `alphaS` is dropped when the fitresult is parsed, and an assert checks the slot.
  - θ→physical is the model's own map (params.REPARAM, pdfEig × 0.607903). The model anchor equals the cache anchor (fit log: "largest shift 0").
  - Point `fitA` = the fit's NP λ with everything else at the anchor. Point `fitB` = NP + TNPs + 29 PDF eigenvectors + transition2 from the fit. The two agree, so everything below is quoted for fitB.
  - Memory: the node had 1.28 TB free. One model load is about 8 GB of cache, and loading took 8 min from ceph (evidence: `logs/check2_model_eval.log`, `logs/check2b_followup.log`).
  - **Why anchor α_s is a valid proxy:** the pathology is O(1) in a single bin and set by L2 and λ4. A shift in α_s moves σ at the percent level, smoothly, so it cannot create or remove a 48% see-saw.
- **Results at the fit tune (fitB).**
  - Physical tune: λ2 0.0521, δλ2 −0.01328, λ4 −2.5e-5, λ2_ν 0.1074, λ4_ν 0. So L2(Y) < 0 for |Y| > 1.98, and only the last gen row [2.0, 2.5] is anti-damped.
  - min σ = 0.136 > 0.
  - Forward row, qT bins 0–0.5 / 0.5–1 / 1–1.5 GeV: **0.239 / 1.332 / 1.862**. The same tune with L2(2.5) moved to 0 gives **0.456 / 1.302 / 1.971**. Every row with |Y| < 2 is unchanged.
  - Oscillation metric (max |second difference| of σ/σ_anchor, qT<10) is 0.81 vs a baseline of 0.025, a factor 30.
  - The deficit is 0.30 cache units, **3.4% of the all-|Y| gen σ at qT<1 GeV**.
  - Evidence: `check2_summary.json`, `check2b_summary.json`, `logs/analyze_check2b.log`.
- **AD vs FD at the fit tune.**
  - AD matches the central FD as h→0: δλ2 3e-7 at h=1e-6, λ2 1e-8, λ4 1.5e-4. This is **not** the λ4_ν-probe failure, where AD≠FD. The Jacobian is correct.
  - The surface, however, is violently curved. At h=1e-4 the forward and backward FDs disagree by 5.2 (λ4, relative to max|J|) and by 0.14 (δλ2), and AD vs FD in λ4 is off by 1.9.
  - Reason: σ(fwd, qT<0.5) is **0.239 at λ4 = −2.5e-5, 0.370 at λ4 = 0, and 0.467 at λ4 = +0.001**, a kink about 1e-4 wide in λ4 (about 2e-4 in θ). **The fit parked λ4 on it** (θ = −0.80005, i.e. physical 0 to 5 digits).
  - This is consistent with the trust-region "bad approximation" failure of the sub-fit. Plausible, not proven.
- **L2 scan from the fit tune.** L2(|Y|=2.5) ∈ [+0.05, −0.05] in steps of 0.005, via δλ2 (λ2 fixed) and via λ2 (δλ2 fixed), plus a fine scan −0.031…−0.034. The two directions agree, since only L2 in the forward row matters. The bin-0 values below are the forward qT<0.5 bin relative to its smooth twin.
  - L2(2.5) ≥ −0.01: clean. AD=FD better than 1e-3, oscillation at baseline.
  - −0.015: the oscillation metric starts to rise (0.04).
  - −0.02: oscillation 0.08.
  - −0.025: bin 0 at 0.9, oscillation 0.22.
  - −0.030: bin 0 at 0.62.
  - **−0.031 (fit):** bin 0 at 0.52.
  - −0.033: bin 0 at 0.20.
  - **−0.034: σ < 0.**
  - −0.05: σ = −17 to −27 in cache units, in 3 bins.

  ![forward-row spectrum at the fit tune](key_forward_row_fit_vs_smooth.png)
  *Gen level, 2.0<|Y|<2.5, α_s at the cache anchor 0.118, all other parameters at the LATL4ZUNWCOLD postfit. The "smooth twin" is the same tune with δλ2 moved so that L2(2.5)=0. The green dotted line is the fit tune with λ4=+0.001 instead of −2.5e-5, which fully restores the smooth shape. Cache units, not events.*

  ![L2 scan summary](check2_L2_scan_summary.png)
  *Same caveats. Top: forward bin qT<0.5, relative to its value at L2(2.5)=0. Middle: oscillation metric (baseline 0.025 is the smooth curvature of σ/σ_anchor). Bottom: AD vs central FD at h=1e-4, where the growth for L2<0 is curvature, not a wrong Jacobian (see the h→0 numbers above). The dotted line marks the fit.*
- **λ4 at fixed L2(2.5) = −0.031.** λ4 = 0 still gives bin 0 at 0.81 and oscillation 0.37. λ4 = +0.001, 0.01, 0.05 or 0.087 all give a clean result: bin 0 at 1.02 to 0.93, oscillation at baseline, AD=FD to 1e-7.
  - **Physics read** (TMD form in `knowledge/30_physics_global/np_parametrization_constraints.md` §1):
    - The form is f^NP = exp[−2Λ∞ b tanh B], with B = L2·b/Λ∞ + (Λ4 + L2³/3Λ∞²)·b³/Λ∞ + …, and Λ∞ = 1.
    - With L2 < 0 and Λ4 ≤ 0, B < 0 at every b_T, so f^NP grows like exp(+2b_T) at large b_T: the b-space integrand anti-damps.
    - Any Λ4 > |L2|³/3 (about 1e-5 here) turns B positive at large b and restores damping.
    - So the artefact is the large-b_T anti-damping of the TMD boundary condition. This is the TMD analogue of the λ4_ν<0 CS failure found in 260923-lattice-fits.
    - The walled fit sits on the physical side: L2(2.5) = +0.005, λ4 = 0.087.
- **Baselines** (each fit's full tune, α_s at the anchor).
  - **LATL4ZWALLCOLD**, read from its main-fit snapshot of 07:37 (near-final; the fitresult is locked): clean in every row. Bin 0 at 1.007, oscillation 0.028, AD=FD to 5e-9.
  - **CCCOLDSELF is NOT a sane baseline.** It sees-saws at qT<1 GeV in **every** |Y| row: at |Y|<0.15 the first two bins are 1.56× and 0.88× the anchor, and at 2.0<|Y|<2.5 they are 0.815 then 0.384. Its oscillation metric is 2.8, and AD vs FD at h=1e-5 is off by 1% (δλ2 and λ4).
  - Its tune: λ4 = −0.018, with Λ4 + L2³/3 < 0 at both Y=0 and Y=2.5, i.e. the negative-λ4 trap. It also has an anti-damping CS kernel (λ2_ν = −0.083).
  - Evidence: `baselines_Yrow0.png`, `baselines_Yrow8.png`, `baselines_Yrow10.png`.

  ![baselines, central row](baselines_Yrow0.png)
  *Gen level, 0<|Y|<0.15, α_s at the anchor. Ratios to the anchor mix a tune difference with the artefact. The signal is the bin-to-bin see-saw of CCCOLDSELF (blue) in its first two bins.*

---

## Result

**Caveats before the numbers.** (i) Check 2 is not the fitted prediction. α_s is held at 0.118 (cache anchor) to stay blind; the argument that this is a valid proxy is above: an O(1) single-bin artefact vs a percent-level smooth α_s dependence. (ii) Check 2 is at gen level on the cache's own 770 bins. The fit folds these through the response, and the stored reco postfit is only the yll-summed ptll projection. (iii) The walled baseline comes from a main-fit snapshot, not its final fitresult. (iv) Cache units are the cache's own normalisation. Only ratios are quoted.

**Answer.** The LATL4ZUNWCOLD minimum predicts a cross section that is positive everywhere and has a correct local AD Jacobian. It is still **not a valid prediction**:
- In the most forward gen bin (2.0<|Y|<2.5, qT<1.5 GeV), σ is a numerical artefact of the anti-damped TMD: ×0.52 in qT<0.5, a see-saw up to 1.5 GeV.
- The artefact is worth 3.4% of the all-|Y| gen σ below 1 GeV. That is large compared with the ~0.5% data precision in the lowest ptll bins, but invisible in the yll-summed stored postfit.
- The fit sits 0.003 in L2(2.5) from σ<0, and on a λ4 kink about 1e-4 wide. There, the quadratic model a trust-region minimizer relies on breaks down over steps far smaller than one σ.

**Validity edge along the TMD direction**, at λ4 ≈ 0 (fit value), for other λ4 ≤ 0 it is not scanned. The edge is set by L2 in the forward row alone, and moving δλ2 or λ2 gives the same result.

| L2(\|Y\|=2.5) | state |
|---|---|
| ≳ −0.01 | clean |
| ≈ −0.015 to −0.02 | first visible distortion |
| −0.025 | about 10% distortion |
| −0.034 | σ < 0 |

With any λ4 ≥ +0.001, L2(2.5) = −0.031 is clean. So the invalid region is L2(Y) < 0 **and** λ4 ≲ 0, not L2 < 0 alone.

Physically: L2(Y)<0 means the TMD anti-damps at forward rapidity. Our wall (np_damping_wall, knowledge §15) already forbids exactly that, and the AN's physical NP requirement is damping at large b_T. The unwalled minimum is therefore unphysical and numerically unreliable at the same time. Its loss, 5.7 above the walled fit, together with the failed sub-fit, fits the picture of a spurious minimum sitting on an artefact kink. That link is not proven.

**Warm unwalled fit (LATL4ZUNWWARM, the lower-loss unwalled minimum).** The same caveats apply: α_s is at the anchor, and the evaluation is at gen level. Its prediction is **valid as a cross-section computation**: positive, smooth, and with AD = FD. So its lower loss is not bought with a cache artefact, unlike the cold minimum.
- It is not a physical TMD. L2 < 0 at all rapidities makes f^NP > 1 (up to +11%) at b_T ≲ 1 GeV⁻¹, which the wall's L2(Y) ≥ 0 condition forbids.
- It is numerically safe only because λ4 = 0.096 is large. The warm tune would go non-smooth if λ4 fell below about 0.03 at its L2.
- An unwalled fit on this cache can therefore land on artefacts wherever λ4 → 0 with L2 < 0. The cold fit did exactly that.

---

## Findings

1. At the LATL4ZUNWCOLD tune (α_s at the anchor), gen σ at 2.0<|Y|<2.5, qT<0.5 GeV is 0.52× its smooth value, with a see-saw to 1.5 GeV. σ is still >0 everywhere. — (evidence: `check2b_summary.json`, `key_forward_row_fit_vs_smooth.png`)
2. The AD cache's TMD validity edge at λ4≈0: distortion from L2(|Y|=2.5) ≈ −0.015 to −0.02, σ<0 at −0.034. It does not depend on whether δλ2 or λ2 moves. — (evidence: `check2_summary.json`, `check2_L2_scan_summary.png`)
3. The artefact needs L2<0 **and** λ4≲0. λ4 = +0.001 removes it completely at the same L2. This is the TMD analogue of the λ4_ν<0 CS failure, and a candidate for `knowledge/` (NP constraints / cache validity). — (evidence: `check2b_summary.json`)
4. At the fit tune the AD Jacobian is correct (AD=FD to 1e-7 as h→0), but σ has a kink about 1e-4 wide in λ4 at 0, and the fit parked λ4 on it. FD at h=1e-4 disagrees O(1). — (evidence: `logs/analyze_check2b.log`)
5. The rabbit-stored postfit for these fits is only the yll-summed ptll projection (39 bins). It is smooth and positive (postfit/data within ±0.65%) and cannot reveal a per-yll artefact. — (evidence: `logs/check1_ptll.log`)
6. **The reference CCCOLDSELF tune is itself in an artefact region:** a qT<1 GeV see-saw in every |Y| row (λ4 = −0.018 → negative-λ4 trap, plus λ2_ν<0). The walled lattice fit is clean. — (evidence: `baselines_Yrow*.png`, `check2b_summary.json`)
7. LATL4ZUNWWARM (λ2 −0.078, δλ2 −0.0095, λ4 0.096): σ is positive and smooth, and AD=FD to 1e-9 (α_s at the anchor). It is numerically valid but anti-damped at small b_T (f^NP ≤ 1.11). An L2(2.5) scan to −0.15 at its λ4 is clean everywhere. — (evidence: `check2c_summary.json`, `tmd_fnp_three_fits.png`)
8. The numerical validity of the cache in the TMD sector is set by large-b damping, Λ4 + L2³/3 > 0 with margin, not by the sign of L2. At the warm L2, degradation starts at λ4 ≲ 0.03 and is catastrophic at λ4 = 0. — (evidence: `check2c_summary.json`)

---

## Open questions

- CCCOLDSELF (and probably the other unwalled references, CCKRYLOVWARM with λ4>0 aside) has a qT<1 GeV artefact at every |Y|. Comparisons of Δχ² and Δα_s against it inherit that. Not chased: out of scope. Worth the same check on CCKRYLOVWARM and CCWALLCOLDR.
- Does the fit exploit the artefact? Feeding the artefact bin through the response (reco per-yll postfit) needs the full 2D postfit, which is not saved. It could be recomputed with the model loaded against the card at the postfit θ (a rabbit `--noFit` with `--externalPostfit` and full `--saveHists`), but that needs α_s handling and is out of scope.
- Check 1 (stored postfit) for LATL4ZUNWWARM is deferred until its fitresult closes. The scripts are ready (see START HERE).
- A guard for the fitter: bound λ4 ≥ small positive, or apply the TMD wall with the B_wall = Λ4 + L2³/3 condition, when L2 can go negative. This is already the wall's job, and it argues for not using unwalled TMD fits at all on this cache.
