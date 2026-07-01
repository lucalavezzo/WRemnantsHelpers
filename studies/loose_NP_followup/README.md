# Loose-NP follow-up study

Spin-off from `projection_pvalues/`. The bad ptll postfit p-value
(0.32%) was substantially absorbed by widening the SCETlib NP priors:

| fit                                       | chi² post / ndf | p-value |
|-------------------------------------------|-----------------|---------|
| symmetric (nominal)                       | 67.4 / 39       | 0.32%   |
| symmetric, Lambda4×5                      | 60.0 / 39       | 1.70%   |
| symmetric, Lambda4×5 + LatticeNoConstraints | 51.8 / 39      | **8.25%** |

≈15 chi² units lived behind NP priors. ≈12 chi² units remain in the
`Lambda4×5+LatticeNoConstraints` fit and are localized features that
the Gaussian-prior nuisance basis cannot absorb at any prior width
(see `projection_pvalues/scripts/residual_anatomy.py` output for the
shape).

## Study question

After loosening the NP priors, what (if anything) can be done about the
remaining ~12 chi² units? In particular:

- Are the localized residuals at ptll bins 9 (5.0–5.5 GeV), 16
  (8.5–9.0 GeV), 22 (11.5–12.0 GeV), 28 (17.0–18.0 GeV), and the
  31/32 sign-flip (20–22 / 22–24 GeV) explainable by a known
  detector or modelling effect, or are they irreducible at this level?
- Does loosening the NP priors change the alphaS measurement (i.e., is
  the loose-NP fit a defensible central value)?
- Are there other nuisances the corrected blocked-chi² diagnostic flags
  as next-most-blocked, and would loosening them help further?

## Tools developed in this study

- `projection_pvalues/scripts/residual_anatomy.py` — 4-panel residual
  anatomy + eigendecomposition of residual cov on a 1D projection.
  Built during this investigation. Output for the loose-NP fit at
  `MY_PLOT_DIR/260428_residual_anatomy_lattice/`.
- `projection_pvalues/scripts/prior_blocked_chi2.py` — per-nuisance
  diagnostic for chi² blocked by Gaussian prior:
      Δchi²_i = pull_i² / (1 − sigma_post,i²)   [for prior sigma=1]
  Validated against the empirical Lambda4×5 (7.4 chi²) and
  +LatticeNoConstraints (8.2 chi²) gains; predicts 8.4 and ~17.5
  respectively (single-nuisance sums overestimate joint Δchi² by
  factor ~1-2 due to within-group correlations).
  *Caveat:* numerically unstable for σ_post ≳ 0.95 (single-nuisance
  approximation breaks down for highly correlated groups like effStat);
  apply a `σ_post < 0.95` filter when reading group sums.

## Decisions taken

- Track in `agents/studies/loose_NP_followup/`.
- Reference fit: `260428_debug/...symmetric_Lambda4Scale5p0_LatticeNoConstraints/`.
- New refits use `MY_OUT_DIR/260428_followup_<tag>/`.

## Tasks

Format: `- [ ]` open, `- [x]` done. Add date and short outcome on completion.

### Diagnostic refinement
- [x] **F1. Cap σ_post < 0.95 in `prior_blocked_chi2.py` and re-run on
  the loose-NP fit.** *Done 2026-04-28; see runlog F1 entry.* Outcome:
  `SIGMA_CAP` env var (default 0.95) drops single-nuisance entries
  above the cap from the per-nuisance sum, which removes the spurious
  effStat / iso-stat inflation. Cleaned ranking on loose-NP fit:
  top individual blocked nuisances are CMS_prefire_stat_m_etaPhiReg2
  (9.1), scetlibNPlambda2 (7.4), 4-6 effSyst_tracking_etaDecorr* at
  ~5 each, and mb_pair group at 7.5 total. Cross-validation: empirical
  Δχ² from refits are 50–90% of single-nuisance predicted sum
  (correlations within groups bring the joint gain down). Log:
  `logs/F1_blocked_chi2_capped_260428_160005.log`.

### Hypothesis-driven refits
- [ ] **F2. Free `scetlibNPlambda2` in addition.** In the loose-NP fit,
  Lambda2 went from −0.54 (constrained) → +1.38 (free) — a sign-flip
  with substantial blocked chi² (~7). Refit with NPlambda2 also freed
  to see if the NP sector still has unabsorbed shape, or if Lambda2 is
  just rebalancing against Lambda4. Output dir:
  `MY_OUT_DIR/260428_followup_freeLambda2/`.
- [x] **F3. 2D likelihood scan Lambda4 vs Lambda2** in the
  Lambda4×5 fit (eigvars constrained). *Done 2026-04-28; see runlog
  F3 entry.* Outcome: ρ(L4, L2) = **−0.468** — moderately correlated
  but NOT degenerate. Tilted-ellipse contour. Lambda2 sign-flips
  (−0.29 → +1.38) when lattice eigvars are freed, signature that NP
  basis decomposition is ambiguous. Recommendation: widen ALL SCETlib
  NP priors together for cleanest publication, not Lambda2 in isolation.
  Plot: `MY_PLOT_DIR/260428_followup_scan2D_L4_L2/L4_L2_scan2D.png`.
- [x] **F4. Inflate b-mass priors 10× in the loose-NP fit.** *Done
  2026-04-28; see runlog F4 entry.* Outcome: chi²=47.47 / 39, p=16.6%
  (vs loose-NP 51.79, 8.25%). Δχ² = **−4.3** vs F1 single-nuisance
  prediction 7.5 (ratio 0.57, consistent with the 0.5–0.9 band).
  mb_pair Σblocked drops 7.5 → 0.19 (saturated). NP_total Σblocked
  drops 13 → 9 — Lambda2 partially absorbed via correlation with mb.
  Used the new `--scaleParams 'lambda4=5' 'mb_up|pdfMSHT20mbrange=10'`
  flag (dogfood test of the generic flag). Log:
  `logs/F4_260428_165951.log`. Output:
  `MY_OUT_DIR/260428_followup/.../L4x5_LattNoCon_mbScale10/`.

### Detector-side cross-check
- [ ] **F10. Investigate `CMS_prefire_stat_m_etaPhiReg2` (pull +1.67,
  blocked ~9).** Same η-φ region as `effSyst_reco_etaDecorr27`
  (pull −1.24)? If yes, there's a coherent muon-region story to
  document. If no, incidental.

## Eventual deliverable

- [ ] **F11. One-paragraph statement for the publication** characterising:
  (a) the residual ptll p-value, (b) what fraction is theory-prior
  under-coverage vs irreducible localized features, (c) the alphaS
  stability, (d) the recommended central-value choice (nominal vs
  loose-NP) with justification.

## Cross-references

- Parent study: `agents/studies/projection_pvalues/`
- Tools used: `projection_pvalues/scripts/residual_anatomy.py`,
  `projection_pvalues/scripts/prior_blocked_chi2.py`,
  `projection_pvalues/scripts/residual_on_nuisance_basis.py`
- Singularity launch pattern: see `projection_pvalues/README.md`
  Runtime notes section.
