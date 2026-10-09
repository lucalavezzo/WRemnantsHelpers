---
title: Where does the ptll projected-saturated tension of the walled lattice fit live?
slug: 260924-ptll-tension-localization
study: lattice-cs-kernel
status: active
created: 2026-09-24
updated: 2026-09-24
owner: main session (Luca)
---

# Where does the ptll projected-saturated tension of the walled lattice fit live?

**Task:** LATL4ZWALLCOLD passes the full 2D saturated test (748/778, p 77 %) but fails the ptll projected one
(80.85/39, p 0.009 %). Where in ptll is that tension, does the ptll correction it wants depend on yll, and does
the yll marginal have a complaint of its own? The aim is to tell apart a wrong/missing ptll theory piece from an
experimental (efficiency/calibration) ptll-shape effect.

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-09-24 17:40)

> **Localisation done (Result). Test 1 done.** The q values are 80.9 with everything free, 76.9 with α_s held,
> and 76.1 with α_s + NP λ held. So neither α_s's freedom nor the NP λ explain the tension.
> The wanted ptll shape (`ptll_wanted_shape.png`) is carried by narrow correlated modes (σ ≈ 0.4 %).
> The most-pulled nuisance is the MiNNLO **A0** scale variation `QCDscaleZfine_PtV15_20helicity_0` (−1.9σ).
> The leading-mode plot's 15–20 GeV dip is built into the covariance and is NOT independent evidence (see the
> retraction entry).

- **Next action:** Luca to decide the template tests: A0-in-ptV-bins vs σ_UL candidates (b-mass, the nonsingular
  cutoff, QED); cosθ* as the discriminator.
- **Blocking on:** nothing. Nothing is running.

---

## Log

### 2026-09-25 — postfit ptll AND yll: good-p fit vs bad-p fits
- **Method:** each converged fit is re-evaluated at its own postfit (`--externalPostfit --noFit`, same card /
  model args / wall; `scripts/run_eval.sh`). The original results only stored the ptll projection; the
  re-evaluation also saves yll. Outputs in `/ceph/.../alphaS/260925_postfit_eval/<TAG>/`. Plot:
  `scripts/plot_postfit_good_vs_bad.py`, log `logs/postfit_good_vs_bad.log`.
  - All six fits are included (updated when the last two finished).

![postfit good vs bad](postfit_good_vs_bad_ptll_yll.png)
- **Stat-only Σpull²** (the fit's projection q in brackets):
  | fit | ptll (39 bins) | yll (20 bins) |
  |---|---|---|
  | CCKRYLOVWARM (56) | 34.2 | 18.7 |
  | CCWALLWARMPF (70) | 39.8 | 18.8 |
  | CCWALLCOLDR (72) | 39.9 | 18.8 |
  | LATL4ZUNWWARM (79) | 42.5 | 18.8 |
  | LATL4ZWALLCOLD (81) | 42.3 | 18.8 |
  | CCCOLDSELF (89) | 42.2 | 18.3 |

  The ptll Σpull² tracks the q ranking only loosely (a 34→42 spread against 56→89). The worst fit, CCCOLDSELF,
  is off mainly in the first two bins (−1.9, +1.4).
- **Read:**
  1. **The yll postfit is identical in all fits**, and fine (18.8/20). The yll projection test's 42/20 is
     therefore NOT a visible yll residual. Like ptll, it is the cost of the configuration (pulls/priors and 2D
     structure) the fit needs to reach it. The yll pull pattern (about ±1.5, alternating) is roughly symmetric in
     ±y.
  2. **The ptll marginal is fine in every fit** (34–42/39). Good and bad differ by only ~6–8 units, at 3–10 GeV.
  3. **So the ~15-unit projection-q difference between the good and bad fits is mostly NOT in either marginal's
     residuals.** It is in what the fit pays to get them: nuisance pulls, priors, and the ptll×yll structure.

### 2026-09-25 — which part of ptll the unphysical-NP minimum changes (CCKRYLOVWARM vs CCWALLWARMPF, card A)
- `scripts/plot_krylov_vs_walled.py`, `logs/krylov_vs_walled.log`. Both fits are on card A without the lattice.
  The prediction change includes the α_s, λ and nuisance differences between the two minima.

![unwalled vs walled ptll](krylov_vs_walled_ptll.png)
- **The postfit prediction shapes differ by ≤ 0.18 % per bin, all at ptll < 10 GeV.** The pattern:
  - oscillating ±0.1–0.18 % at 0–5 GeV;
  - −0.1 % at 4.5–6 GeV;
  - +0.15 % at 7–8.5 GeV;
  - < 0.03 % above 10 GeV.
- **Stat pulls of the ptll marginal, Σpull²** (unwalled vs walled): 1.5 vs 1.1 at 0–3 GeV, **13.4 vs 19.6 at
  3–10 GeV**, 19.4 vs 19.1 above 10 GeV. Total 34.2 vs 39.8.
- **Read:** the region the NP freedom "fixes" is ptll 3–10 GeV, at the per-mille level. The biggest single moves
  are 5–5.5 GeV (−2.66 → −2.07), 4.5–5 and 7.5–8.5 GeV.
  - Only ~6 of the ~14 units of projection-q difference show up in the marginal residuals. The rest is in the
    pulls/priors and the 2D fit, as in the walled decomposition.
  - The remaining large residuals above 10 GeV (11.5–12, 17–18, 20–22, 22–24 GeV, each ~±2) are untouched by
    either fit.

### 2026-09-25 — the ptll projection across all card-A fits: what the unwalled CCKRYLOVWARM covers
- `scripts/proj_q_across_fits.py`; the NP λ (physical) are from `../260923-lattice-fits/analysis.json`.
  | fit | NLL | proj q / 39 | p | λ2_ν | λ2 | λ4 | A0 15–20 |
  |---|---|---|---|---|---|---|---|
  | **CCKRYLOVWARM** (unwalled, deepest) | 365.49 | **55.96** | **3.8 %** | **−0.091** | 0.273 | 0.203 | −1.67 |
  | CCCOLDSELF (unwalled, 2nd minimum) | 379.20 | 88.52 | 1e-5 | −0.083 | 0.374 | −0.018 | −1.64 |
  | CCWALLWARMPF (walled) | 371.44 | 70.39 | 0.15 % | 0.0045 | 0.108 | 0.002 | −1.83 |
  | CCWALLCOLDR (walled) | 372.68 | 72.27 | 0.09 % | 0.0073 | 0.078 | 0.119 | −1.90 |
  | LATL4ZUNWWARM (lattice, unwalled) | 375.53 | 78.71 | 0.02 % | 0.091 | −0.078 | 0.096 | −1.98 |
  | LATL4ZWALLCOLD (lattice, walled) | 376.72 | 80.85 | 0.009 % | 0.063 | 0.028 | 0.087 | −1.88 |
- **Read:**
  - Only CCKRYLOVWARM reaches an acceptable projection (~15 units below the walled fits). It is not "the wall
    removed" in general: the other unwalled minimum is worse (88.5), and the lattice unwalled fit is 78.7.
  - What differs is the NP sector. CCKRYLOVWARM has the CS-kernel coefficient λ2_ν = −0.091, the wrong sign:
    unphysical, and ~7σ from the lattice value 0.135 ± 0.031. It also has a large TMD λ2/λ4. The card
    nuisances (A0 15–20 at −1.67) are essentially unchanged.
  - So the shape the data want can be partly mimicked by an effective CS kernel of the wrong sign, and not by
    the card systematics.
  - That fits a missing effect in the rapidity evolution at large b. A b/c flavour-threshold effect in the CS
    kernel is one such candidate (speculative).
  - It also fits FRZASNP: inside the physical region, the NP λ are worth < 1 unit.

### 2026-09-24 ~19:20 — RETRACTION: "the current nuisances cannot cover the excess" was overstated
- **What is established:**
  - The main fit already profiles every nuisance within its prior, and q = 81/39 is what remains. So at
    their CURRENT prior widths the nuisances do not cover it: they cover part of it, paying 16.5 (card) +
    6.1 (model) units in pulls.
  - The deviation sits along narrow correlated modes (σ ≈ 0.4 %) of a covariance that includes the nuisance
    envelope.
- **What I overstated:**
  - "No single nuisance / group can fix it" came from the per-nuisance constraint relief (largest 3.5). That
    split is NOT the amount q would drop if a prior were loosened. Loosening also lets a nuisance improve the
    data term, and 3.5 is only a LOWER bound for A0 PtV15_20.
  - So "freeing existing nuisances adds little" was not justified. How much q drops, and at what prior
    inflation, is unmeasured.
- **The right test is Luca's original one:** inflate the priors by group (×2, or free) and measure Δq, the
  inflation needed, and Δα_s. If covering the excess needs ≫ 1× the prior, or if α_s moves, that is the finding.

### 2026-09-24 ~19:00 — does the badly described ptll region affect α_s? (Q&A, no new runs)
- **Yes, at ~1.5–2σ**, from the region sub-fits (Result table):
  | freed region | Δα_s / σ_main |
  |---|---|
  | 0–5 GeV | −1.5 |
  | 5–15 GeV | −2.2 |
  | 15–30 GeV | −0.45 |
  | 30–44 GeV | −0.07 |
  | yll | +4.2 |

  σ(α_s) is unchanged except for yll (×1.56).
- **Mechanism:** the low-ptll bins carry little α_s information of their own (σ unchanged). Freeing them relaxes
  the coordinated pull (lumi 0.45, weak 0.33, mb 0.28 e-3 impacts; A0 itself only 0.09), and that moves α_s.
- **Caveat:** the free per-bin absorption is maximal flexibility, so treat these as ~upper estimates of the bias,
  good to ±50 %.
- **What would show it does not matter:** a physical template that resolves q and moves α_s by < 0.3σ, or α_s
  stability against the ptll fit range.

### 2026-09-24 ~18:45 — pulls sorted by |pull| (walled fits)
- `scripts/pulls_abspull.sh` = `workflows/pullsAndImpacts.sh -P alphaS -e "-s abspull"` on LATL4ZWALLCOLD,
  CCWALLCOLDR and CCWALLWARMPF. Output in `pulls_abspull/<fit>/` (traditional and global).
- **LATL4ZWALLCOLD:** the largest |pull| is `QCDscaleZfine_PtV15_20helicity_0` (A0, −1.9). Its traditional α_s
  impact is only **0.09e-3** (≈ 8 % of σ(α_s) = 1.16e-3). That is why it never showed in the impact-sorted top
  entries (λ4 0.78, TNP BF qqV 0.47, lumi 0.45, pdfEig25 0.42…).
  - The other high-pull entries: mb_up, resumFOScaleEnvSymDiff, lumi, EW FSR, weak, pdfEig28, and the other A0
    bins. Also `Resolution_correction_smearing_variation3/6` at about +1 (muon resolution; candidate 3).

![LATL4ZWALLCOLD pulls sorted by |pull|](pulls_abspull/LATL4ZWALLCOLD/pulls_and_traditional_impacts_alphaS.png)

### 2026-09-24 ~18:30 — is A0 really wrong? What the existing 4D fits say
- **Idea:** in (ptll, yll) alone, A0 acts only through the lepton acceptance, where it is degenerate with a σ_UL
  ptll-shape deficit. In cosθ*, A0 has its own (1 − 3cos²θ) signature. So compare the A0 pulls with and without
  the angular dimensions.
- **Data used** (`scripts/a0_pulls_2d_vs_4d.py`, `scripts/ai_pulls_2d_vs_4d.py`): the matched July pair from
  `../../4d-vs-2d-uncertainties` (same 3746 nuisances, older SCETlibNP model):
  - 2D `260702_2D_l6nu0p01_l60p01`;
  - 4D `260714_l6nu0p01_l60p01` (ptll × yll × cosθ* × φ* quantiles);
  - plus the April 4D `260427_debug_allproj`.

  These files hold no per-nuisance errors (nan).
  | fit | A0 PtV15_20 | Σ A0 pull² | Σ A1–A7 pull² |
  |---|---|---|---|
  | 2D Jul (older model) | −1.32 | 3.9 | 0.3 |
  | **4D Jul (same nuisances)** | **−0.77** | 2.4 | **9.8**, spread over all A_i, each ≲ 1σ |
  | 4D Apr | −0.63 | 3.2 | 13.7, spread |
  | 2D Sep, LATL4ZWALLCOLD (AD model) | −1.88 | 6.8 | 0.3 |
- **Read:**
  - The A0 pattern is present in 2D under BOTH theory models (July SCETlibNP, September AD), so it is not
    specific to the AD model.
  - Once the angular dimensions are added, the A0 PtV15_20 pull roughly halves. A0 is then no more pulled than
    the other A_i, which become active when cosθ*/φ* are resolved.
  - That favours "in 2D, A0 is a proxy lever for a ptll-shape need" over "A0 is mismodelled". It is NOT
    conclusive: one old-model pair, no errors in these files, and −0.77 is still the largest A0 entry there.
- **Definitive test:** a 4D fit on the current AD model with the A0 nuisances unconstrained (setupRabbit
  `--noConstrainParams 'helicity_0'`), so the data measure A0(ptV) directly against the MiNNLO band. Two things to
  check: whether the 2D ptll tension survives in 4D, and whether α_s moves.

### 2026-09-24 ~18:10 — the A0 pull pattern is the same in every card-A fit
- The A0 pulls are from the MAIN fits' postfit `parms`, not from the sub-fits (in the sub-fits they relax, e.g.
  PtV15_20 → −0.15). Across all seven card-A data fits (`scripts/a0_pulls_across_fits.py`):
  | fit | PtV5_7 | PtV7_9 | PtV9_11 | PtV15_20 | PtV40+ | incl | Σ A0 pull² |
  |---|---|---|---|---|---|---|---|
  | LATL4ZWALLCOLD (lattice, walled) | −0.73 | +0.62 | +0.84 | −1.88 | +0.95 | −0.70 | 6.9 |
  | LATL4ZUNWCOLD (lattice, unwalled) | −0.86 | +0.57 | +0.95 | −1.89 | +0.97 | −0.69 | 8.2 |
  | LATL4ZUNWWARM | −0.67 | +0.67 | +0.84 | −1.98 | +0.94 | −0.82 | 7.4 |
  | CCWALLCOLDR (no lattice, walled) | −0.59 | +0.65 | +0.79 | −1.90 | +0.92 | −0.82 | 6.8 |
  | CCWALLWARMPF | −0.64 | +0.62 | +0.76 | −1.83 | +0.91 | −0.78 | 6.4 |
  | CCKRYLOVWARM (no lattice, unwalled) | −0.57 | +0.24 | +0.72 | −1.67 | +0.87 | −0.68 | 5.3 |
  | CCCOLDSELF (unwalled, 2nd minimum) | −0.75 | +0.06 | +0.70 | −1.64 | +0.85 | −0.70 | 6.0 |
- **Read:** the pattern does not depend on the lattice term, the wall, or which minimum the fit lands in. It is a
  stable feature of card A's data against its model, outside the NP sector the fits vary. That fits the
  tension being unfixable by NP choices.

### 2026-09-24 ~18:00 — where the A0 pull comes from; how to read the bands
- **Source:** the LATL4ZWALLCOLD postfit `parms` (`scripts/qcdscale_pulls.py`). All QCDscaleZ nuisances with
  |pull| > 0.5 are helicity_0 (= A0):
  | nuisance | pull |
  |---|---|
  | PtV15_20 | −1.88 ± 0.88 |
  | PtV40+ | +0.95 |
  | PtV9_11 | +0.84 |
  | PtV5_7 | −0.73 |
  | inclusive | −0.70 |
  | PtV7_9 | +0.62 |

  Σpull² by helicity: A0 6.9, A2 0.5, all others 0.0.
- **The naming is confirmed in the card:** 176 QCDscaleZ nuisances, helicity indices 0–7 only (no UL; the UL scale
  uncertainty comes from SCETlib). rabbit_theory_helper.py:441 maps `helicity_{i}` → `angularCoeffs_A{i}`.
- **Caveat:** A0 is the angular coefficient whose acceptance effect survives in the (cosθ*, φ*)-integrated ptll.
  With a symmetric acceptance, A1 and A3–A7 mostly integrate away. So A0 being the pulled one fits BOTH "A0
  mismodelled" and "A0 is the only angular lever that can shape ptll".
- **Bands:** they are marginal (per-bin) 1σ errors with neighbour correlations ~0.8. A curve can sit inside
  every band and still be highly significant along a correlated direction (here q ≈ 76 while every bin is
  within ~1σ). So "inside or outside the band" is not the test; q (or the Wald χ²) is.

### 2026-09-24 17:45 — plots redrawn on a linear ptll axis
- `ptll_wanted_shape.png` and `ptll_scales_by_yll_band.png` had a log x axis starting at 0.5 GeV. That hid half
  of the [0,1] bin and distorted the bin widths. Both are now linear 0–44 GeV at the real bin edges. No
  numbers changed.

### 2026-09-24 — RETRACTION / caveat on the "leading mode" read (17:40 entry)
- **How the mode is built:**
  - d = R − 1, with C_R the ratio covariance;
  - C_R = V Λ Vᵀ, with z_k = v_kᵀ d / √λ_k (Σ z_k² = the Wald χ²);
  - the plotted curve is z_k √λ_k v_k for the k with the largest z_k².
- **Its SHAPE v_k is an eigenvector of the covariance, which comes from the model's nuisance templates, not from
  the data.** The data only choose which mode wins and set its amplitude.
- **So the 15–20 GeV dip with its step at 20 GeV was built into the covariance** by the PtV15_20 A0-scale
  template. Its coincidence with that nuisance's bin is partly circular and is NOT independent evidence. I
  called it evidence at 17:40; that was wrong.
- **The direct central values (top panel) show no clear 15–20 dip** (FRZASNP: +0.45, +0.52, −0.24, +0.36, +0.26 %).
- **Selection:** picking the max z² of 38 modes is a look-elsewhere choice (the null expectation of the max is
  ~9). z² = 41 (FRZASNP) is well above it; 16.7 (FRZAS) is not striking.
- **What survives as data evidence for A0:** only the pull itself (−1.9σ, 3.5 units relieved in every test).
- **The right tool is the template test,** which fits the A0 variation's own reco shape against the data.

### 2026-09-24 17:40 — test 1 result: the wanted ptll shape
- **q:** α_s held 76.91 (EDM 2.9e-12); α_s + NP λ held 76.08.
  - The latter's sub-fit EDM is 8.7e-5, looser than the others (≤2e-7). It ran 13170 s and was probably stopped by
    `--earlyStopping`, with a loss change of ~1e-6 per iteration at the end. Its q is a lower bound, but it cannot
    exceed 76.91 since it is nested.
  - **So:** α_s's own freedom is worth ~4 of the 81 and the NP λ freedom <1. The tension is a ptll shape the model
    lacks at the measured α_s. The NP form cannot supply it.

![ptll correction the data want](ptll_wanted_shape.png)
*Top: fitted squared per-bin scales, each divided by its own ptll > 5 GeV plateau. The plateau level (~0.94) is
degenerate with the normalisation nuisances and not meaningful. Band: full sub-fit covariance. The α_s-free
curve is off scale: it absorbs the α_s shift. Bottom: the leading eigenmode of that covariance, i.e. the
correlated direction carrying the largest share of the deviation. Diagnostic sub-fits, not GoF tests.*

- **Reading the bands:** the per-bin errors are large (±4.6 % at 0–1 GeV, even with NP held), but the bins are
  strongly correlated (median |ρ| = 0.78–0.81). That is the theory-nuisance envelope moving coherently. The
  deviation is significant only along narrow modes: the leading one has σ ≈ 0.38 % and z² = 41.
  - The Wald d^T C⁺ d is 63 (α_s held) and 102 (α_s + NP held), against the LR q of 77 / 76. The rough agreement
    shows the covariance picture is not crazy; the difference is non-linearity plus the loose EDM.
- **Leading mode:**
  - At 0–3 GeV the two variants disagree (−0.4 against +1.0 % at 0–1): this region is NP-sensitive, and the mode
    there is not robust.
  - At 10–20 GeV both variants agree: a rise peaking at 11.5–12 (+0.5 %), then a dip over 15–20 (to −0.9 %),
    with a sharp step back to ~0 at 20 GeV.
- **The 15–20 GeV dip coincides with the gen-ptV bin of `QCDscaleZfine_PtV15_20helicity_0`.** helicity_0 is A0:
  rabbit_theory_helper.py groups `.*helicity_{i}` into `angularCoeffs_A{i}`, so this is the MiNNLO μR/μF
  variation of A0 in ptV 15–20. It is the most-pulled nuisance (−1.88σ, 3.5 units). The neighbouring A0 bins are
  pulled too: PtV9_11 +0.84, PtV5_7 −0.73, PtV7_9 +0.63, PtV40+ +0.95.
  - **Read:** in the main fit, the fine-ptV-binned A0 scale nuisances act as a piecewise ptll-shape freedom, and
    the fit uses it. The "wanted shape" of the sub-fit is largely the release of those pulls. Its sharp step
    edges are inherited from the nuisance binning; the underlying feature may be smoother.
  - **Two readings, not yet separable:** (i) A0 really is mismodelled around 15–20 GeV; A_i come from MiNNLO,
    not SCETlib. (ii) A σ_UL shape deficit that the A0 nuisances happen to be the cheapest levers for.
  - **Discriminator:** A0 acts through the cosθ* acceptance, and σ_UL does not. A cosθ*-resolved view (the 4D
    card) or a template test with the A0 variation's own reco shape separates them.
- Scripts: `scripts/plot_wanted_shape.py`, `scripts/wald_modes.py`. Logs: `logs/plot_wanted_shape.log`,
  `logs/wald_modes.log`. Data: `wanted_shape.json`.

### 2026-09-24 16:25 — FRZAS done (α_s held); FRZASNP still running
- **FRZAS:** q = 76.91 (against 80.85 with α_s free), sub-fit EDM 2.9e-12. α_s is unchanged in the sub-fit
  (Δθ = 0.0), which confirms the freeze.
- **So only ~4 of the 81 come from α_s's own freedom.** The tension is NOT mainly "the α_s from ptll against the
  α_s from the rest". It survives with α_s fixed.
- **The fitted squared scales** relative to their ptll > 5 GeV plateau (0.943, a normalisation that is degenerate
  with the normalisation nuisances, not meaningful):
  - +5.3 % at 0–1 GeV, falling smoothly to 0 by ~4.5 GeV;
  - flat within ~±1 % above that.
- **The per-bin errors are large at low ptll** (±6.3 % at 0–1, ±2.8 % at 4.5–5), from the full sub-fit
  covariance, because the still-free NP λ are degenerate with the low-ptll scales. So the FRZAS shape is ONE
  point in a flat valley, not a measurement. FRZASNP (NP held too) should pin it.
- Scripts: `scripts/peek_frz.py`, `scripts/frz_shape.py`.

### 2026-09-24 13:32–13:58 — test 1 launched: the shape the data want, α_s held
- **Why:** in the free projection sub-fit, α_s moves −10σ_main and the 39 scales absorb the resulting ptll shape
  change, so the scales are not the mismatch. Holding α_s (and then the NP λ) at the main-fit values makes the
  scales show the correction still needed.
  - These are diagnostics, not GoF tests: with parameters frozen, q is not χ²₃₉.
  - Freezing everything would be useless: the scales would just be data/postfit, which is 42/39. The mismatch
    lives in the pulls.
- **Jobs**, via `scripts/run_loc.sh` from the LATL4ZWALLCOLD postfit, `-m Project ch0 ptll`:
  - `FRZAS`: `--freezeParameters alphaS`;
  - `FRZASNP`: `--freezeParameters alphaS lambda2 lambda4 delta_lambda2 lambda2_nu`.

  rabbit matches freeze names exactly (`re.fullmatch`, common.py:24), so nothing else is caught.
  Frozen = held at the loaded blinded coordinate; nothing is unblinded.
- **Verified in the logs:**
  - "Updated list of frozen params" shows [alphaS] and [alphaS, λ2, λ4, δλ2, λ2_ν], both in the main-fit setup
    and again in the sub-fit;
  - the full saturated 2ΔNLL at the loaded point is 753.44, unchanged;
  - both sub-fits are iterating.
- **Slow start:** the cache load took 1380 s, against 279 s this morning, because ceph was contended by two
  other card-A fits and by the scratch copy below.
- **Cache mirror:** the cache is now also on `/scratch/submit/cms/alphaS/ad_scetlib_caches/pdf62_corrgrid_260827/merged_full/`
  (md5-identical, with a PROVENANCE.txt). `run_loc.sh` reads from there for future launches. These two jobs
  still read ceph.

### 2026-09-24 — discussion with Luca: candidate causes (no runs)
- **Scale of the effect:** the per-bin data stat is ~0.2–0.25 % and the region data terms are ~2 per bin, so the
  missing ptll shape is at the few-per-mille level. Many small effects are therefore big enough.
- **yll-independence of the needed ptll correction** disfavours the causes that change the flavour mix with y:
  PDF, flavour-dependent NP, and the primary bb̄→Z channel. It favours universal ones: evolution / flavour
  thresholds, QED, and ptll-only detector effects.
- **Candidate ranking (mine):**
  1. b/c mass effects in the resummation. The qT ~ m_b…3m_b scale matches where the tension is. The AN
     (uncerts.tex:246) says this is the largest expected mass effect and has no estimate yet. In our SCETlib
     tree, a grep finds only top decoupling in the hard function and no b/c threshold in the qT evolution or
     beam functions.
  2. QED at low ptll: FSR modelling at reco (the horace/photos FSR nuisance is pulled −1.2), and QED ISR, which
     is absent from the QCD resummation.
  3. Muon resolution at low ptll: the 0.5 GeV bins are comparable to the dimuon pT resolution. The band flatness
     argues against it but does not exclude it.
  4. NP functional form, rather than its parameter count.
  5. PDF, which fits the yll tension better than the ptll one. So the MSHT20 test predicts that yll improves more
     than ptll.

### 2026-09-24 12:59 — all six finished; harvested
- All exited cleanly. The full-ptll reproduction gives 80.85 exactly, the same as the original sub-fit. Numbers
  are in Result. Evidence: `logs/harvest.log`, `harvest.json`, `ptll_scales_by_yll_band.png`.

### 2026-09-24 11:46 — update
- **Final:** PT1530 23.69/10 (EDM 1.9e-8), YLL 42.05/20 (EDM 3.2e-14), PT3044 region 1.59/3.
- **Loss flat, not yet exited:** PT0005 38.57/9 and PT0515 50.22/17.
- **Still running:** PTxYB6 at 270.2/234; the full-ptll reproduction at 78.8, still descending towards 80.85.

### 2026-09-24 11:14 — provisional (running losses, NOT final)
- q = 2·(376.7216 − the current sub-fit loss); the losses are still decreasing slowly, so each q is a lower bound:
  | tag | q / ndf | p (χ²) |
  |---|---|---|
  | PT0005 | 37.6/9 | 2e-5 |
  | PT0515 | 50.2/17 | 4e-5 |
  | PT1530 | 23.7/10 | 0.8 % |
  | PT3044 | 1.59/3, **final** (EDM 5.7e-7) | 66 % |
  | YLL | 42.0/20 | 0.3 % |
  | PTxYB6 | 269.4/234 | 5.6 % |
- The PT3044 process is now running its second mapping, the full-ptll reproduction.

### 2026-09-24 10:30 — design
- Background, from `../260923-lattice-fits/LOGBOOK.md` (2026-09-24 Q&A entry):
  - the ptll marginal postfit residual is fine (stat-only 42.3/39);
  - the 81 comes from re-profiling once ptll is freed: data 53.0, card constraints 16.5, model priors 6.1,
    lattice 5.2;
  - the relief is spread over ~10 nuisances, the largest single term being 3.5;
  - in the sub-fit, the rest of the data returns near the priors.
- **Method:** `scripts/run_loc.sh` = the LATL4ZWALLCOLD command with:
  - the same card (`cardA_latticeASWZ_l4zero_statsyst`), wall, 44 fit_params (read from the original log),
    `prior_sigmas` and `--earlyStopping 100`;
  - `--externalPostfit <LATL4ZWALLCOLD fitresult> --noFit`, then `--saveHists --computeSaturatedProjectionTests`
    with the mapping(s) under test;
  - dropped: impacts and hist errors;
  - `threads=64` per job, so all jobs together stay within half the machine.
- **Jobs.** In rabbit's `Select`, a bin outside the selection keeps scale 1, so each test frees only its own
  region:
  | tag | mapping | free scales |
  |---|---|---|
  | PT0005 | `Select ch0 ptll:slice(0,9),yll:sum` | 9 |
  | PT0515 | `Select ch0 ptll:slice(9,26),yll:sum` | 17 |
  | PT1530 | `Select ch0 ptll:slice(26,36),yll:sum` | 10 |
  | PT3044 | `Select ch0 ptll:slice(36,39),yll:sum` + `Project ch0 ptll` (the latter reproduces 80.85) | 3 (+39) |
  | YLL | `Project ch0 yll` | 20 |
  | PTxYB6 | `Select ch0 yll:rebin(-2.5,-1.5,-0.7,0,0.7,1.5,2.5)`: ptll in 6 signed yll bands | 234 |
- **Reading:**
  - The region tests are not additive, since each re-profiles separately; compare their q/ndf.
  - PTxYB6 contains the ptll projection. So q(PTxYB6) − q(ptll) on 195 dof measures how much the needed ptll
    correction differs across yll bands. A theory ptll error should be roughly common to all bands; an
    efficiency or calibration effect should follow |yll|. The bands are signed, so ±y symmetry is a free
    check.

### 2026-09-24 10:27–10:40 — launched
- **First attempt failed:** value slices (`slice(30j,44j)`) crash in the TF select (helpers.py:220 accepts only
  integers). I switched to bin indices: [0,5) = `slice(0,9)`, [5,15) = `slice(9,26)`, [15,30) = `slice(26,36)`,
  [30,44) = `slice(36,39)`. The failed log is kept as `PT3044/fit_PT3044_failed_complexslice.log`.
- **Validation (PT3044 log):**
  - the full saturated 2ΔNLL at the loaded point is 753.44, identical to the original;
  - the region mapping has ndof 3, and the others unblind 9 / 17 / 10 / 20 / 234 scale parameters, as designed.
- **Resources:** ~53 GB and ~260 threads per job; ~40 cores each, ~240 in total. That is within the half-machine
  budget. A separate AD-cache build from another session uses ~160 cores.
- Outputs are in `/ceph/.../alphaS/260924_ptll_tension_loc/<TAG>/`, each with its own `fit_<TAG>.log`.
