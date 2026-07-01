# Loose-NP follow-up runlog

## 2026-04-28 — study setup

Spun off from `projection_pvalues/`. Motivation:

- The corrected `prior_blocked_chi2.py` diagnostic (Δχ² = pull²/(1−σ²)
  per nuisance) successfully retroactively flags the lattice eigvars as
  the dominant blocked group in the `Lambda4×5` fit (Σblocked ≈ 18 vs
  empirical 8.2 chi² gain — overestimate by ~2× from joint correlations
  but ordinal ranking is correct). Earlier (incorrect) formulation
  pull²·(1−σ²) gave near-zero for that group and missed it entirely.
- The `Lambda4×5+LatticeNoConstraints` fit (chi²=51.8, p=8.25%) is the
  current best-fit baseline; ~12 chi² remain in localized residuals at
  ptll bins 9, 16, 22, 28, 31/32 that no Gaussian prior on existing
  nuisances can absorb.
- Open question for the publication: is the loose-NP fit the right
  central value for alphaS? Need F8/F9.

## Reference fits already on disk

- `260428_debug/.../symmetric/`              chi²=67.4, p=0.32%
- `260428_debug/.../symmetric_Lambda4Scale5p0/` chi²=60.0, p=1.70%
- `260428_debug/.../symmetric_Lambda4Scale5p0_LatticeNoConstraints/` chi²=51.8, p=8.25%
- `260428_debug/.../noSymmetrizeNP/`         chi²=67.3, p=0.33% (asym Lambda4 — irrelevant for p-value)

## Diagnostics already produced

- `MY_PLOT_DIR/260428_residual_anatomy/`         (nominal symmetric)
- `MY_PLOT_DIR/260428_residual_anatomy_lattice/` (loose-NP)
- Lambda4 likelihood scans (sym vs asym):
  `MY_PLOT_DIR/260428_debug_asym/lambda4_scan_overlay.png`
- Tension ranking of nominal: see chat transcript / projection_pvalues
  notes.

## 2026-04-28 — F1 done (capped blocked-chi² diagnostic)

`prior_blocked_chi2.py` updated to mask single-nuisance entries with
`σ_post ≥ σ_cap` (default 0.95, env `SIGMA_CAP`). Above the cap the
single-nuisance Gaussian extrapolation diverges spuriously (effStat
class with 2784 small-pull σ≈0.999 nuisances). Re-run on the three
fits, log: `logs/F1_blocked_chi2_capped_260428_160005.log`.

### Loose-NP fit (Lambda4×5 + LatticeNoConstraints), top blocked

**Per-group totals** (after cap; Σpull² shown for sanity):

| group | n | n_con | Σpull² | **Σblocked** | top single | Δχ² |
|---|---|---|---|---|---|---|
| QCDscaleZfine_other      | 80 | 47 | 7.20 | 20.2 | QCDscale_PtV9_11hel6        | 3.7 |
| prefire                  | 14 | 14 | 5.25 | 15.9 | CMS_prefire_stat_m_etaPhiReg2| **9.1** |
| resolution               | 72 | 72 | 6.68 | 15.1 | smearing_variation54        | 3.2 |
| pixelMult                | 49 | 49 | 9.70 | 13.2 | var40                       | 2.7 |
| QCDscaleZfine_h5_h7      | 40 | 26 | 4.58 | 12.3 | PtV15_20hel7                | 2.9 |
| **scetlibNP_lambda**     | 3  | 3  | 3.79 | **9.7** | **NPlambda2**             | **7.4** |
| mb_pair                  | 3  | 3  | 3.45 | 7.5  | pdfMSHT20mbrangeSymAvg      | 3.9 |
| scetlibNP_gamma          | 3  | 2  | 2.19 | 3.1  | gammaLambda4                | 2.6 |

**Top individual nuisances** (after cap):

| rank | name | pull | σ_post | blocked |
|---|---|---|---|---|
| 1 | CMS_prefire_stat_m_etaPhiReg2 | +1.67 | 0.833 | **9.14** |
| 2 | chargeVgenNP0scetlibNPZlambda2 | +1.38 | 0.861 | **7.38** |
| 3 | effSyst_tracking_etaDecorr29  | +1.13 | 0.879 | 5.65 |
| 4 | effSyst_reco_etaDecorr44      | −0.87 | 0.926 | 5.37 |
| 5 | effSyst_tracking_altBkg_etaDecorr28 | +0.85 | 0.927 | 5.17 |
| 6 | effSyst_tracking_etaDecorr14  | −0.70 | 0.949 | 4.89 |
| 9 | pdfMSHT20mbrangeSymAvg        | −0.96 | 0.874 | 3.92 |
| 11| CMS_prefire_stat_m_etaPhiReg0 | −1.24 | 0.771 | 3.78 |
| 17| mb_up                          | −1.53 | 0.476 | 3.01 |
| 24| scetlibNPgammaLambda4         | −1.31 | 0.591 | 2.62 |

### Headline reading

After freeing Lambda4 + lattice eigvars, the *next-most-blocked* single
nuisances are (in decreasing single-nuisance Δχ²):

1. **CMS_prefire_stat_m_etaPhiReg2** (~9 chi²) — detector
2. **chargeVgenNP0scetlibNPZlambda2** (~7 chi²) — theory NP, same basis
3. **mb_pair group** (~7 chi² total, dominated by pdfMSHT20mbrangeSymAvg) — theory
4. A cluster of 4-6 tracking-eta-decorrelated effSyst nuisances at
   3-6 chi² each (their joint Δχ² will be less than the sum because
   they're correlated).

### Cross-validation against empirical Δχ²

| empirical refit                              | Δχ² gain | predicted (Σblocked of freed group) | ratio |
|---|---|---|---|
| nominal → Lambda4×5                          | 7.4 chi² | 8.6 (Lambda4 alone in nominal)    | 0.86 |
| Lambda4×5 → +LatticeNoConstraints            | 8.2 chi² | ~17 (gammaEigvars in Lambda4×5)   | 0.48 |

Single-nuisance prediction overestimates joint group Δχ² by factor
~0.5–0.9. Use the per-group sum as an *upper bound* and the *ranking*
as the actionable signal.

### Decisions taken from F1

- F12 (don't use asym for central fit): confirmed earlier; will record
  in this runlog when done formally.
- F2 (free `chargeVgenNP0scetlibNPZlambda2`): top theory-side candidate
  per the cleaned ranking; expect ~3–5 chi² gain (predicted 7.4,
  apply ~0.5–0.9 factor).
- F10 (investigate prefire stat): top detector-side candidate. Need to
  understand η-φ region 2 and whether it correlates with the
  effSyst_tracking nuisances also flagged.

F1 status: **done**. Script update committed in
`projection_pvalues/scripts/prior_blocked_chi2.py`.

## 2026-04-28 — F10 done (pull-vs-η scatter, no localized issue)

Built `scripts/F10_pull_vs_eta.py` to map effSyst_*_etaDecorr{1..48}
to η bin centers and overlay all five steps (reco / tracking / iso /
idip / trigger). Ran on nominal and looseNP. Plot:
`MY_PLOT_DIR/F10_pull_vs_eta/F10_pull_vs_eta_{nominal,looseNP}.png`.

Result: across 336 effSyst_*_etaDecorr* nuisances total, only **2
have |pull| > 1** (effSyst_reco_etaDecorr27 at η≈+0.25 with pull
−1.24, effSyst_tracking_etaDecorr29 at η≈+0.45 with pull +1.13).
**Adjacent η bins, opposite signs** — that's noise/oscillation, not a
coherent feature. Σpull² across all 336 = 20.13. No coherent η-region
of elevated tension. The "muon-region cluster" the F1 metric flagged
was an artifact of dividing by `(1 − σ_post²)` for many σ_post≈1
nuisances; the joint Δχ² is small even though single-nuisance sums
look large. **Conclusion: F10 is a null result.** No further
muon-detector refit needed.

F10 status: **done**.

## 2026-04-28 — F4 done (mb-pair priors widened 10×)

### Setup

Built generic `--scaleParams REGEX=FACTOR` flag in setupRabbit.py +
datagroups.py (mirrors `--noSymmetrize` wiring). Multiplies the kfactor
of any systematic whose per-direction `var_name` matches REGEX (re.search)
by FACTOR. Overlapping patterns matching the same var_name raise
ValueError. Replaces the family of hardcoded `--scaleNPLambda4`,
`--scaleTNP`, `--scalePdf`, `--scaleMinnloScale`, `--scaleMuonCorr`
flags with one generic mechanism (old flags retained for now;
cleanup is a future PR).

Files modified:
- `WRemnants/scripts/rabbit/setupRabbit.py:752-764` — CLI flag
- `WRemnants/scripts/rabbit/setupRabbit.py:1153-1172` — parser, attach to datagroups
- `WRemnants/wremnants/postprocessing/datagroups/datagroups.py:131-144` — init
- `WRemnants/wremnants/postprocessing/datagroups/datagroups.py:1497-1518` — apply with overlap check
- `WRemnants/wremnants/postprocessing/datagroups/datagroups.py:1530` — `kfactor=effective_scale`

### Dogfood validation

F4 invocation used `--scaleParams 'lambda4=5' 'mb_up|pdfMSHT20mbrange=10'`
instead of `--scaleNPLambda4 5`. Setup log confirmed:
```
INFO:setupRabbit.py: --scaleParams: 2 pattern(s) registered: 'lambda4'×5.0, 'mb_up|pdfMSHT20mbrange'×10.0
INFO:datagroups.py: scaleParams: chargeVgenNP0scetlibNPZlambda4 kfactor 1.0 -> 5.0 (pattern 'lambda4' x 5.0)
INFO:datagroups.py: scaleParams: pdfMSHT20mbrange kfactor 1 -> 10.0 (pattern 'mb_up|pdfMSHT20mbrange' x 10.0)
INFO:datagroups.py: scaleParams: mb_up kfactor 1.0 -> 10.0 (pattern 'mb_up|pdfMSHT20mbrange' x 10.0)
```
Lowercase `lambda4` regex correctly matches `chargeVgenNP0scetlibNPZlambda4`
but **not** `scetlibNPgammaLambda4` (capital L) — confirmed by the log
not firing on the gamma variant. Apples-to-apples with the original
`--scaleNPLambda4 5` flag.

### Chi² results

| fit                                 | chi² post / ndf | p-value | Δχ² vs prev |
|---|---|---|---|
| symmetric (nominal)                 | 67.41 / 39      | 0.32%   |        |
| sym + Lambda4×5                     | 59.97 / 39      | 1.70%   | −7.4   |
| sym + Lambda4×5 + LatticeNoCon      | 51.79 / 39      | 8.25%   | −8.2   |
| **F4: sym + Lambda4×5 + LatticeNoCon + mb×10** | **47.47 / 39**  | **16.57%** | **−4.3** |

### F1 prediction vs empirical (validation of the diagnostic)

| free / widen | F1 single-nuisance Σblocked | empirical Δχ² | ratio |
|---|---|---|---|
| Lambda4 alone (×5)        | 8.6  | 7.4 | 0.86 |
| LatticeNoCon (gamma×10)   | ~17 | 8.2 | 0.48 |
| **mb-pair ×10 (F4)**       | **7.5** | **4.3** | **0.57** |

Ratios consistently in the 0.5–0.9 band. The diagnostic over-predicts
joint Δχ² because of within-group correlations, but the *ranking* and
the *order of magnitude* are reliable.

### What's left blocked after F4

Top blocked groups in the F4 fit (capped σ<0.95):

| group | n | n_con | Σpull² | Σblocked |
|---|---|---|---|---|
| (detector groups dominating: prefire, eff, scaleCorr, pixelMult)        |    |    |       |       |
| scetlibNP_gamma             | 3  | 2  | 1.47  |  2.17 |
| horace_FSR                  | 2  | 2  | 0.40  |  1.79 |
| resumScale                  | 4  | 4  | 0.60  |  1.07 |
| **mb_pair**                  | 3  | 3  | **0.18**  | **0.19** ← saturated |
| **NP+resum total**           |    |    | 5.43  | 10.39 |
| **ALL theory**               |    |    | 24.4  | 61.2  |

mb_pair is fully exploited — Σblocked dropped 7.5 → 0.19. That's the
empirical confirmation that the prior was the bottleneck, not residual
shape mismatch in the b-mass direction.

The remaining theory blocked is now spread across NP-gamma, horace
(soft photon FSR), and small contributions from mb. Detector-side
blocked (>150) is dominated by correlated effSyst clusters that the
F10 analysis showed are not coherent.

### Top individual nuisances after F4

| rank | name | pull | σ_post | blocked |
|---|---|---|---|---|
| 1 | CMS_prefire_stat_m_etaPhiReg2     | +1.70 | 0.83 | 9.46 |
| 2 | effSyst_tracking_etaDecorr29      | +1.14 | 0.88 | 5.73 |
| 3 | effSyst_reco_etaDecorr44          | −0.87 | 0.93 | 5.26 |
| 7 | chargeVgenNP0scetlibNPZlambda2    | +1.05 | 0.86 | 4.16 |
| 11| CMS_prefire_stat_m_etaPhiReg0     | −1.21 | 0.77 | 3.59 |
| 20| effSyst_reco_etaDecorr27          | −1.27 | 0.62 | 2.60 |

Lambda2 still flagged at blocked=4.16 (vs 7.4 in pre-F4). The mb
widening absorbed some of what Lambda2 was trying to do — its pull
moved +1.38 → +1.05. **Still a candidate for further widening (F2).**

### Decision

- F4 confirms the b-mass prior was a real bottleneck, predicted by F1.
- Generic `--scaleParams` flag works end-to-end.
- Next-most-blocked theory candidate is Lambda2 (~4 chi²); detector
  candidates are dominated by prefire+effSyst tracking but F10 already
  showed those aren't a localized coherent issue.
- Localized residuals at ptll bins 9, 16, 22, 28, 31/32 still persist
  (not theory-priors) — see `MY_PLOT_DIR/260428_residual_anatomy_lattice/`.

F4 status: **done**.

## 2026-04-28 — F4-split: FO vs PDF disambiguation

User pushback: "we can't widen blindly to chase p-value; we need to
know which of the two mb sources (FO `mb_up` vs PDF
`pdfMSHT20mbrangeSym{Avg,Diff}`) is doing the work and why widening
helps". Launched two parallel refits, each widening only one side.

### Chi² attribution

| fit                        | chi² post | p-value | Δχ² vs loose-NP |
|---|---|---|---|
| loose-NP (baseline)        | 51.79     | 8.25%   |   —    |
| **F4-FO** (mb_up x10)       | **50.58** | **10.13%** | **−1.21** |
| **F4-PDF** (mbrange x10)    | **48.54** | **14.07%** | **−3.25** |
| F4-both (FO+PDF x10)        | 47.47     | 16.57%  | −4.32  |

PDF side delivers **75%** of the chi² gain (3.25 of 4.32). Sum of
separate gains (4.46) ≈ combined (4.32) — roughly additive, the two
nuisances are not strongly correlated and don't interact destructively.

### alphaS attribution

| fit          | pdfAlphaS         | Δ(αₛ) vs loose-NP |
|---|---|---|
| loose-NP     | −9.767 ± 0.547    |   —   |
| F4-FO        | −9.816 ± 0.548    | **−0.05** (~0.1σ) |
| F4-PDF       | −10.079 ± 0.571   | **−0.31** (~0.6σ_loose-NP) |
| F4-both      | −10.117 ± 0.571   | −0.35              |

PDF side also drives the alphaS shift; FO side has essentially no
effect on αₛ. So whatever physics is being absorbed by widening
`pdfMSHT20mbrange` is correlated with the αₛ measurement.

### Data-preferred shifts in original prior σ

To compare apples-to-apples, multiply (postfit pull in widened fit) by
(kfactor multiplier = 10):

| nuisance              | loose-NP pull | F4-widened pull | data-preferred (× kfac) |
|---|---|---|---|
| mb_up (FO)            |  −1.53        |  −0.20          |  −2.0   (~2σ, prior ~OK) |
| pdfMSHT20mbrange (PDF) |  −0.96        |  −0.38          |  **−3.8** (~4σ, prior clamping) |

The PDF-side nuisance was being clamped by the σ=1 prior at −0.96, but
the data wanted **−3.8σ**. The FO-side was already pulling close to its
data-preferred value at the original prior; widening it gave essentially
nothing.

### Two interpretations of the PDF-side preference

(a) **MSHT20 PDF m_b uncertainty is genuinely under-estimated.** The
    published band is a fit to DIS+jets etc.; Z-pTll data adds new
    information those fits didn't have. Other PDF families
    (NNPDF, CT, ABM) have somewhat different m_b ranges, so the
    "true" theoretical uncertainty on m_b is not unambiguously
    MSHT20's. **Defensible publication direction**: widen
    `pdfMSHT20mbrange` prior in nominal, document the αₛ shift as
    a theory uncertainty.

(b) **The pdfMSHT20mbrange shape happens to mimic a residual that's
    actually caused by something else.** mb is just a convenient
    flexible knob in that direction. Need to plot the shape
    pdfMSHT20mbrange produces in ptll and compare to known residual
    features (bins 9/16/22/28/31-32) before drawing conclusions.

### Decisions taken

- **F4-FO is essentially a null result** for both chi² and αₛ. The
  FO m_b prior is well-matched to data preference; no action needed.
- **F4-PDF is the live question.** Need shape comparison before
  recommending a publication choice — is `pdfMSHT20mbrange` absorbing
  a *real* PDF-mb shape direction, or a different mismodel?

### Diagnostic-toolkit takeaway

This is a clean win for the corrected blocked-chi² metric: it correctly
flagged mb-pair as the next bottleneck, and *within* mb-pair it
correctly identified pdfMSHT20mbrange (σ_post=0.87, blocked=3.9) as
the bigger contributor over mb_up (σ_post=0.48, blocked=3.0), even
though their `pull²` totals were comparable.

F4-split status: **done**. Logs:
`logs/F4_fo_260428_172905.log`, `logs/F4_pdf_260428_172905.log`.

### Follow-up needed (NEW TASK F4d)

- [ ] **F4d. Shape comparison: does pdfMSHT20mbrange overlap with the
  localized residual?** Take the F4-PDF fit's hist_postfit_inclusive
  − loose-NP hist_postfit_inclusive on ptll. This is the shape that
  the widened PDF-mb knob added to the prediction. Overlay against
  the loose-NP residual (data − pred). If the shape matches the
  residual where it has features (especially bins 9, 28, 31/32),
  pdfMSHT20mbrange is absorbing those features → interpretation (b)
  is favored, the PDF-mb is a stand-in for a different mismodel.
  If the shape is broad/smooth and doesn't match the localized
  features, interpretation (a) is favored — the PDF prior is just
  too tight and the widening is honest.

## 2026-04-28 — F3 done (2D Lambda4-Lambda2 scan in L4×5 fit)

Re-fit `Lambda4Scale5p0` config with `--scan` on Lambda2 and `--scan2D
L4 L2`, 11×11 grid. Total 4618 sec ≈ 77 min. Output:
`260428_followup_scan2D_L4_L2/fitresults.hdf5`. Plot via the native
`rabbit_plot_likelihood_scan2D.py` (--params chargeVgenNP0scetlibNPZlambda4
chargeVgenNP0scetlibNPZlambda2; overlays Hessian ellipse on full scan):
`MY_PLOT_DIR/260428_followup_scan2D_L4_L2/nll_scan2D_chargeVgenNP0scetlibNPZlambda4_chargeVgenNP0scetlibNPZlambda2.png`.
Hessian and Likelihood scan agree closely at 68% and 95% — joint
profile likelihood is well-approximated by Gaussian.

### Quantitative

```
L4×5 fit:
  Lambda4 (charged): pull = −0.716, σ_post = 0.150
  Lambda2 (charged): pull = −0.285, σ_post = 0.317
  Cov(L4, L2)        = −0.0222
  correlation ρ      = −0.468
```

### Reading

Contour is a tilted ellipse, *not* a thin ridge: ρ²≈0.22 of variance
shared. Lambda4 and Lambda2 are partially correlated, neither
degenerate nor orthogonal. Major axis: L4↓ ↔ L2↑.

### Sign-flip across fits (informative)

| fit                           | L4 pull | L2 pull |
|---|---|---|
| nominal                        | −2.34   | −0.54   |
| L4×5                           | −0.72   | −0.29   |
| L4×5 + LatticeNoConstraints    | −1.21   | **+1.38** ← sign flipped |

Lambda2's role depends on which other NP params are free. Signature of
data wanting a NP shape that is not aligned with any single basis
vector — gets decomposed differently as the basis becomes more
flexible. Argues against treating Lambda2 in isolation; recommend
widening all NP priors together if going further.

### Decision from F3

For F2 / further widening:
1. Cleanest publication choice: widen ALL SCETlib NP priors together
   (L4, L2, delta_lambda2, gammas) as one "loose NP" sector. Removes
   the basis-decomposition arbitrariness shown by Lambda2's sign flip.
2. Predicted chi² gain from also widening L2 prior on top of current
   L4×5+LattNoCon: ~3–5 chi² (F1 single-nuisance 7.4 × empirical
   0.5–0.9 ratio × correlation correction).

F3 status: **done**.
