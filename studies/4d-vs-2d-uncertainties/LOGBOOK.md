---
title: 4D vs 2D fit uncertainty comparison
slug: 4d-vs-2d-uncertainties
status: active
created: 2026-07-14
updated: 2026-07-14
---

# 4D vs 2D fit uncertainty comparison — logbook

**Goal:** Understand how the α_s uncertainty budget changes going from the 2D
(ptll, yll) fit to the 4D (ptll, yll, cosθ*_CS quantile, φ*_CS quantile) fit;
in particular whether the impact gains/losses per nuisance group are genuine
or binning artifacts.

---

## START HERE (status as of 2026-07-14)

> **Muon calibration group impact ×4.4 in 4D (0.055 → 0.242 raw, ×2 plot scale
> → 0.11 vs 0.48 ×10⁻³) — real, in the covariance, mechanism understood; open
> question is how much of it is MC-stat template noise vs genuine.**
> 4D fit: `/ceph/.../alphaS/260714_l6nu0p01_l60p01/` (datacard 260623_Zhistmaker,
> 49920 bins). 2D fit: `/ceph/.../alphaS/260702_2D_l6nu0p01_l60p01/` (datacard
> 260701_Z_2D, 780 bins). Same 3746 nuisances. σ(αs): 0.501 → 0.431.

- **Next action:** half-MC test via `mz_dilepton.py --oneMCfileEveryN 2`
  (Luca's call — file-level halving, no new axis, setupRabbit unchanged,
  weightsum renormalizes automatically, quantile edges from the pre-computed
  file so binning identical); then same setupRabbit + fit chain on real data
  and compare muonCalibration constraints/impacts to the full-MC fit — see
  2026-07-14 log entries for the readout.
- **Blocking on:** nothing

---

## Log

### 2026-07-14 (half-MC route settled: --oneMCfileEveryN 2)
- Luca: use `--oneMCfileEveryN 2` instead of `--splitSampleInN`. Verified in
  `wremnants/utilities/data_paths.py:195-201`: keeps MC files with `i%N==0`
  (data untouched), so nominal + ALL variation templates come from half MC
  with the standard output structure — setupRabbit unchanged, and
  normalization is automatic (weightsum summed over the same halved subset).
  Quantile axes use the pre-computed edges file → 4D binning identical.
- Limitation: no offset flag, so only one half out of the box. Enough for the
  primary readout (half-MC vs full-MC calibration constraints); the A-vs-B
  pull-coherence check would need a one-line offset patch — do only if the
  first comparison is ambiguous.

### 2026-07-14 (half-MC test design)
- Decided a half-MC test is the direct discriminator for noise- vs
  physics-driven calibration constraints. Machinery survey:
  - `mz_dilepton.py --splitSampleInN N` (+ `--randomSeedForSplit`) adds a
    random per-event `sample_n` axis; since `axes`/`cols` are extended
    (mz_dilepton.py:974-975) *before* the syst blocks (:1277+), the split axis
    lands on nominal AND all variation hists — one histmaker run gives both
    halves. An unsplit `nominal_asimov` is also written.
  - `isEvenEvent` (+ `--flipEventNumberSplitting`) exists (:558) but no Filter
    uses it in mz_dilepton — deterministic-split route would need a one-line
    patch and 2× histmaker runs.
  - Gap: nothing in setupRabbit consumes `sample_n` — need to slice
    `sample_n==k` and renormalize each half (per-process, by the full/half
    nominal integral ratio, not blind ×2) before writing the card.
  - Zero-refit shift-vs-noise check is NOT possible from the histmaker output:
    variation hists are written with `hist.storage.Double()` (no sumw2), e.g.
    `muonScaleSyst_responseWeights`; and for weight-based systs the var−nom
    noise is suppressed by weight correlation anyway, so nominal sumw2 would
    overestimate it. Half-MC measures the noise dependence directly.
- Readout: fit the SAME real data with half-A and half-B 4D datacards + the
  full-MC fit as reference. Noise-driven → calib constraints tighten ~1/√2 vs
  full (fake sensitivity ∝ template noise), group impact grows ~×√2 more, and
  the A-vs-B calib pull vectors are uncorrelated. Genuine → A ≈ B ≈ full
  (constraints marginally weaker with noisier templates, pulls coherent).

### 2026-07-14
- Compared traditional grouped impacts on pdfAlphaS, 4D vs 2D
  (plot: `~/public_html/alphaS/260714_alphaS_pulls_and_impacts/traditional_impacts_grouped_pdfAlphaS.png`).
  Muon calibration 0.11 → 0.48 (×10⁻³, plot units incl. `--scaleImpacts 2`).
- Decomposed the muonCalibration group (338 members: 144 `Scale_correction_unc*`,
  72 `Resolution_correction_smearing_variation*`, 72 `ScaleClos_correction_unc*`,
  49 `pixel_multiplicity_syst_var*`, 1 `ScaleClosA`). Quad-sum of per-member
  impacts 0.046 → 0.168 raw; growth is broad-based: scale ×24 (0.004→0.094),
  resolution ×3 (0.032→0.092), pixel-multiplicity ×3 (0.033→0.102). Group
  impact (0.242) > quad-sum (0.168) → positive correlations among members.
- Constraints: 2D mean 0.982 (essentially prior, ρ(αs)≈0.001); 4D mean 0.809,
  min 0.149 (`pixel_multiplicity_syst_var48`), pulls up to 1.4, per-nuisance
  ρ(αs) up to ±0.016. The angular quantile axes constrain the calibration
  nuisances and correlate them with αs; neither happens in 2D.
- Bin counts: 780 → 49920 (×64 = 8×8 angular quantile grid), so per-bin data
  stats ~64× smaller and per-bin relative MC-stat noise of variation templates
  ~8× larger. Resolution variations are single smearing throws → prime
  suspects for noise-driven fake constraints.

---

## Findings

1. The 4D muon-calibration impact blowup is real (present in the fit covariance,
   not a plotting/merge issue): calibration nuisances go from unconstrained and
   αs-uncorrelated in 2D to constrained (mean 0.81, min 0.15) and weakly
   αs-correlated in 4D; 338 members sum to a ×4.4 group impact — (evidence:
   `260714_l6nu0p01_l60p01/cov/fitresults.hdf5` vs
   `260702_2D_l6nu0p01_l60p01/fitresults_t0_cov_impacts.hdf5`).
2. 4D gains ~15% on σ(αs) (0.501 → 0.431) but muon calibration becomes the
   3rd-largest group; the new angular shape information is partly degenerate
   with calibration effects (migrations across equal-population quantile edges).

---

## Open questions

- How much of the 4D calibration constraint is MC-stat noise in the variation
  templates (esp. the stochastic resolution smearing throws) at 49920 bins?
  `--binByBinStat` covers nominal MC stat only, not variation-template noise.
- Does coarsening the angular quantile grid (e.g. 4×4) drop the calibration
  impact much faster than it inflates σ(αs)? If yes, the fine bins were buying
  fake information.

---

## Decisions

- (none yet)
