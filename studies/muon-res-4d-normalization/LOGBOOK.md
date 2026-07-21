---
title: Muon resolution variation blowup in 4D card
slug: muon-res-4d-normalization
status: active
created: 2026-07-15
updated: 2026-07-15
---

# Muon resolution variation blowup in 4D card — logbook

**Goal:** Understand why `Resolution_correction_smearing_variation15` shows a
~10^12 normalization when plotted from the 4D
(ptll–yll–cosθ*q–φ*q) datacard but is fine in the 2D (ptll–yll) card.

---

## START HERE (status as of 2026-07-15)

> **Diagnosed AND fixed via clipping. Root cause: log(k) noise from
> weight-cancellation bins in Ztautau/Other, unclipped by rabbit.**
> In every log_normal 4D card, ~200 near-empty Ztautau bins (n_eff to 1e-7) have
> a nominal that is a ± NLO weight-cancellation residual; any log_normal syst
> ratio there is floating-point noise → |logk| up to 55, so nominal·e^{|logk|}
> reaches 1e20. Affects ALL systs (αs, scetlibNP, prefire, effStat), not just
> resolution; the blow-up bins carry only 0.08% of the Ztautau yield.
> **Fix implemented:** `--clipSystVariations x` in setupRabbit clamps each bin's
> up/down factor to [1/x, x]. Also fixed a real return-bug in rabbit `get_logk`
> (it clipped `_logk` but returned the unclipped `_logk_view`).

- **Next action:** disentangling clip-vs-zero (ACTION vs FOOTPRINT). Two fits
  RUNNING (CPU, tanh_6+wall): (1) `260720_l6nu0p01_l60p01_allProcZeroNeff1`
  (all-proc per-bin zero — clean clip comparison, matches clip's process
  coverage); (2) `260721_l6nu0p01_l60p01_zeroClipFootprint` (zeros EXACTLY the
  1382 entries clip touched → clip-vs-this = pure ACTION, bounded-10x vs 0).
- **Blocking on:** the two fits (~2-4h each).

### Disentangling design (2026-07-21)
clip != zero differ in (A) ACTION (bounded-10x vs 0 on a modified entry) and
(B) FOOTPRINT (clip touches only >10x entries; per-bin-zero kills ALL systs in
n_eff<1 bins). To isolate (A): `zero_clipped_entries.py` diffs clipped vs
unclipped (260623) hlogk and zeros EXACTLY those 1382 entries (Ztautau 1341,
Other 41; max zeroed |logk|=41.3). Card
`..._realdata_zeroClipFootprint`. Ladder:
| card | σ(αs) | role |
|---|---|---|
| unclipped | 0.431 | huge variations (footprint entries) |
| clip 10x | 0.467 | bounded 10x (same footprint) |
| zeroClipFootprint | ? | 0 (same footprint) -> clip-vs-this = ACTION |
| allProcZeroNeff1 | ? | per-bin zero -> vs zeroClipFootprint = FOOTPRINT |
Earlier caveat: the 0.467(clip,all-proc) vs 0.471(zero,Ztautau-only) was
apples-to-oranges (process coverage); allProcZeroNeff1 fixes it.
Impacts diff (zero-Ztautau vs clip) already localized the gap to the
muon-calibration groups (scale/resolution/eff): webdir
`~/public_html/alphaS/260721_zero_vs_clip_impacts/`.

### Phase-3 FINAL (2026-07-20/21) — three-way, all tanh_6 + wall, all converged
| fix (tanh_6+wall, real config) | pdfAlphaS | σ(αs) | EDM | Δσ vs unclipped |
|---|---|---|---|---|
| unclipped (260623) | -8.847 | 0.431 | 9e-18 | — |
| clipped 10x        | -8.778 | 0.467 | 4e-13 | +8.5% |
| zeroed n_eff<1     | -8.765 | 0.471 | 4e-18 | +9.3% |
- **Clip ≈ zero** (σ 0.467 vs 0.471, ΔaS 0.013≈0.03σ) — the two fixes are
  interchangeable; result is independent of HOW you tame the bins.
- **Both are ~+9% looser than unclipped.** The pathological Ztautau bins inject
  spurious constraining power that artificially TIGHTENS σ(αs) by ~9%. Removing
  them (either way) → σ≈0.47 = the trustworthy value; unclipped 0.431 is the
  outlier to distrust.
- Dirs: unclipped `260714_l6nu0p01_l60p01`, clipped
  `260715_l6nu0p01_l60p01_clipped`, zeroed `260720_l6nu0p01_l60p01_ztautauZeroNeff1`
  (σ in each `cov/fitresults.hdf5`). Ran via fitterSCETlibNP.py (matches Luca's
  clipped/unclipped exactly). Fits on CPU ~2-4h.

### Phase-3 finding (2026-07-20) — STRIKING, with a confound [RESOLVED, see FINAL above]
> RETRACTION: the "baseline did not converge (EDM=109)" below was the STALE
> 2026-07-01 fit (old tanh_2/no-wall config or older code). In Luca's real config
> (tanh_6 + wall, current code) the UNMASKED card converges fine (EDM 9e-18). So
> the pathological bins do NOT stall the minimizer here; they instead artificially
> TIGHTEN σ(αs) by ~9% (see FINAL table). The tanh_2 numbers below are not the
> right comparison — use the tanh_6+wall three-way.
Exact baseline recipe (fit `--noHessian --noEDM` + straight-through GN hessian),
card swapped only. pdfAlphaS blinded, same seed (shift real, absolute offset).
| card | pdfAlphaS | σ(αs) | EDM | converged? |
|---|---|---|---|---|
| baseline unmasked (OLD, 2026-07-01) | -7.640 | 0.703 | **1.1e2** | NO — 3410/3746 nuis stuck <0.05 |
| Ztautau zeroed n_eff<1 (current code) | -8.797 | 0.500 | **4.8e-12** | YES |
- The baseline **did not converge** (EDM=109, 91% of nuisances frozen at prefit).
  The masked fit converges cleanly to a lower NLL (24935 vs 25029). => the
  pathological near-singular Ztautau bins plausibly STALL the minimizer; masking
  fixes it. If confirmed, the fix is necessary-for-convergence, not cosmetic.
- **CONFOUND**: the OLD baseline is from 2026-07-01, possibly older code. Cannot
  attribute EDM 109→1e-12 (and σ 0.703→0.500) to the mask alone vs a code change.
- **RESOLUTION (running)**: rerun UNMASKED baseline + CLIPPED card with CURRENT
  code + exact recipe → clean 4-way. Dirs: baseline `.../realdata/baseline_currentcode`,
  clipped `.../260715_Z_4d_datacard_clipped/...realdata`. Scripts `exact_fit.sh`
  / `exact_fit_masked.sh`. NB fits run on CPU (login node), ~4h each; NOT GPU
  (SCETlib model OOMs small GPUs).

### Recommended clip value
- `--clipSystVariations 10` → bounds every bin to [0.1x, 10x]. Safe because in
  well-populated bins (n_eff≥1) the largest genuine variation is 3.66x, and
  there is a legitimate flat **2x lnN on PhotonInduced** (logk=log2=0.693) a
  tighter clip would corrupt. 10 leaves all of that untouched and kills the 1e20
  overflow. Going tighter (~2-3x) cleans the debug output more but risks the 2x
  lnN — don't go below it. Value 10 and 0.1 are equivalent (code uses |log|).

### Files changed (local; WRemnants ffbe5b46 / rabbit main 948a94a)
- `rabbit/rabbit/tensorwriter.py`: add `clip_syst_variations` ctor arg; define
  `self.clip`; fix `get_logk` to clip the RETURNED `_logk_view` (was a no-op);
  harden the two other clip guards for the False/None default.
- `scripts/rabbit/setupRabbit.py`: add `--clipSystVariations` (default 0=off),
  pass to `TensorWriter`.
- Unit test `/tmp/test_clip.py`: noise bin −38.67→−2.303 (=10x), +10% and 2x lnN
  bins unchanged. PASS in container.

---

## Log

### 2026-07-15
- Read `hlogk` for syst 3453 (`Resolution_correction_smearing_variation15`)
  from both cards directly with h5py+hdf5plugin (login node, no container needed).
  - 2D card (`260701_Z_2D/ZMassDilepton_ptll_yll_realdata/ZMassDilepton.hdf5`):
    max |logk| = 0.016 across all procs. Clean.
  - 4D card (`260623_Zhistmaker/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_realdata/ZMassDilepton.hdf5`):
    Zmumu clean (max |logk| = 0.12), **Ztautau has 14 bins with |logk| > 1,
    extremes −37.43 / +12.1**. `Other`/`PhotonInduced` have no resolution syst
    (logk ≡ 0).
- Worst bin = flat 8814 = ptll ∈ [3.5,4), yll ∈ [1.3,1.5), cosθ*q bin 5,
  φ*q bin 6. There: Ztautau sumw = 1.25e−4, sumw2 = 6.5e−3 → √sumw2 = 0.08,
  n_eff = 2.4e−6. Nominal is a cancellation residual ~650× below its own MC-stat
  error. logk = −37.43 ⇒ varied content ≈ 6.9e−21: the ± weights cancel even
  more completely in the variation. Ratio is meaningless.
- The 14 bins with |logk|>1 are **exactly** the 14 Ztautau bins with
  n_eff < 1e−4 (153 bins have n_eff < 0.01; `Other` has ~106 such bins but
  carries no resolution systs, so it doesn't blow up).
- rabbit `tensorwriter.py`: `logk = log(syst/nom)` with fallback
  `logkepsilon = log(1e-3) = −6.908` only when `sign(nom·syst) ≠ 1`
  (that's the wall of −6.908 entries visible for many systs in bin 8814,
  i.e. variations that went negative). Tiny **positive** varied contents pass
  unclipped. `self.clipSystVariations = False` is hardcoded (the
  `if self.clipSystVariations > 0.0` branch is dead) and setupRabbit exposes
  no flag.
- Same-bin systs with the −6.908 clip: many (effSyst_*, horace FSR, mb_up,
  pixel_multiplicity, other resolution variations) — confirms the bin itself
  is pathological, not variation15.
- Real-data 4D fit (`fitresults.hdf5`): variation15 pulled +0.48. Positive
  pull drives the bad bin → 0 (harmless direction); a negative pull would have
  multiplied it by e^{+18.7} (~10^8). The fit survived, but the nuisance
  response is wildly asymmetric/nonlinear in that bin — a stability and
  Hessian-quality hazard.

---

### 2026-07-15 (later) — cross-card comparisons

**Red herring first:** the unfolding card
`260411_histmaker_dilepton_unfolding/.../ZMassDilepton.hdf5` (masked gen channel)
was built with `--systematicType normal` (additive pred = nom + θ·δ). It has the
same nominal noise bins but no blowup, because additive systs can't exponentiate
a garbage ratio. This was NOT actually the colleague's card (Luca corrected me).

**The real colleague card** —
`/scratch/submit/cms/areimers/alphas/fitinput/AlphaS/Theorymodels/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksVals_CT18Z_N3p0LL_N2LOCorr_FrankNoConstraints_Lambda2x1_Lambda4x1_Ptll0to44/ZMassDilepton.hdf5`
— is a true apples-to-apples match: same 39×20×8×8 binning, `log_normal`, NOT
unfolding (masked=False). **It has the identical disease.**
- Ztautau: 152 bins n_eff<0.01, **14 bins n_eff<1e-4** (same as ours).
- variation15 alone: their worst Ztautau logk is only +9.713 / clipped −6.908
  (worst varied bin ≈ 4 events) → plotting variation15 looks clean. Pure luck of
  the floating-point draw in that one syst.
- **But over ALL systs in the noise bins**: worst |logk| = 34.7 (e³⁴·⁷≈1.2e15),
  worst single varied Ztautau bin = **2.68e11 events** (bin 8203, nominal 2.24e-4).
  Ours: worst |logk| = 41.3, worst bin = 1.2e14 (bin 1365). Same order, same bug.
- Why the same variation differs between cards: in these cancellation-residual
  bins whether log(varied/nom) lands at −37 (same sign, unclipped) or −6.908
  (sign flip, clipped to logkepsilon) is set by which side of zero the residual
  falls. Different histmaker inputs → different residual signs → different
  variation exposes the spike. Structural bug is identical.

**Verdict on Luca's hypothesis:** it is NOT the unfolding. Both standard 4D
log_normal cards are affected; the colleague only "doesn't see it" because they
happened to plot variation15, whose worst excursion in their card is tiny. A
different nuisance would show them a 1e11 spike too.

### 2026-07-15 (third card) — 260714_Zhistmaker_oneMCfileEvery2
- `260714_Zhistmaker_oneMCfileEvery2/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_realdata/ZMassDilepton.hdf5`
  — log_normal, 39×20×8×8, not unfolding. **Same disease, worst so far.**
- Ztautau: 93 bins n_eff<0.01, 9 bins n_eff<1e-4.
- variation15 directly: Ztautau logk −10.22 → 63.6-event down-var spike
  (nominal ~2e-3). Visible-but-not-catastrophic on THIS syst.
- Over all systs in noise bins: worst |logk| = **55.6** (e⁵⁵·⁶≈1.4e24),
  worst varied bin = **2.84e20 events** (bin 15231, nominal 2e-4). Deepest of
  the three log_normal cards.
- Half the MC input (oneMCfileEvery2) → fewer effective events → residuals
  closer to zero → DEEPER log ratios. Confirms the mechanism: more MC stats
  would reduce but not remove it.

### Scoreboard (all four cards)
| card | type | 4D | Ztautau n_eff<1e-4 | worst |logk| | worst varied bin |
|---|---|---|---|---|---|
| 260623 (yours) | log_normal | y | 14 | 41.3 | 1.2e14 |
| FranksVals (colleague) | log_normal | y | 14 | 34.7 | 2.7e11 |
| 260714 oneMCfileEvery2 | log_normal | y | 9 | 55.6 | 2.8e20 |
| 260411 unfolding | normal | y | 11 | (additive) | ~5e-4 shift |

**Every log_normal 4D card is affected; only the additive (normal) card escapes.
Severity is a random draw of cancellation depth; less MC stats = worse.**

### 2026-07-15 (fourth angle) — concentration in bad bins (FranksVals card)
- Luca ran `rabbit_debug_inputdata.py` and saw many unrelated systs with huge
  Ztautau/Other up-ratios (pdfAlphaS 107x, scetlibNPZlambda2 201x, lambda4 130x,
  delta_lambda2 60x, CMS_prefire_ecal 45x, prefire_stat 48-71x, ...). Asked if
  it's concentrated in a few bad bins. **YES — confirmed.**
- **Collapse test**: recomputing each syst's max/min ratio over only bins with
  n_eff≥1 makes EVERY one collapse to ~1.0x (107.82→1.05, 201.41→1.09,
  130.51→1.03, 45.25→1.09, 71→1.00, ...). The worst bin for every listed syst
  has n_eff = 1e-7..1e-6 (a millionth of an effective event).
- **Not systematic-specific**: pdfAlphaS, scetlib NP, prefire, effStat all blow
  up because the problem is the NOMINAL denominator (cancellation residual), not
  the variations.
- **Concentration**: across all 3750 systs only 198 Ztautau bins (of 34652 pop.)
  and 8 Other bins ever exceed |logk|>1. Yield in the blow-up bins:
  Ztautau 4.6 / 5697 events = **0.08%**; Other 0.003 events = **0.00002%**.
  (Bins with n_eff<1: Ztautau 4134 bins = 5.2% of yield, Other 3018 = 0.5%.)
- Physically negligible, numerically catastrophic under log_normal exp().

### 2026-07-20 — AIMED FIX: zero low-n_eff Ztautau syst bins (Phases 1-3)
Decision (Luca): aimed fix instead of the global 10x clip. Zero Ztautau `logk`
(all systs) in bins with **n_eff < 1**, keep nominal, Ztautau-only. Threshold
chosen after seeing the footprint/tradeoff table (n_eff<1 = 4143 bins = 5.26% of
Ztautau systs, worst-remaining 3.66x, fully removes hazard; tighter cuts are
cheaper but LEAVE 1000x blow-ups because blow-ups reach n_eff~0.47; n_eff<2 =
41%, too much). 5.26% of Ztautau systs = ~0.004% of total prediction; central
prediction untouched.

- **Tools** (login-node, h5py): `zero_lowstat_systs.py` (copy-then-patch card
  editor, `--process`/`--neff`, never mutates original) + `verify_cards_diff.py`
  (independent per-process diff).
- **Phase 1 DONE**: zeroed card at
  `.../ZMassDilepton_..._realdata_ztautauZeroNeff1/ZMassDilepton.hdf5`
  (4143 Ztautau rows zeroed).
- **Phase 2 DONE (verified only Ztautau changed)**: hnorm/hsumw/hsumw2/hdata_obs
  BYTE-IDENTICAL; Other/PhotonInduced/Zmumu logk 0 rows changed / max|diff|=0;
  Ztautau 4143 rows changed, all now zero. Post-fix max|logk|: Ztautau 41.3→1.30
  (3.66x); flagged bins 328→56 (harmless 1≤n_eff<2, 0.09% yield).
  **NB: `Other` still has a 3260x blow-up in ~7 low-n_eff bins** (we only did
  Ztautau by request) — a fully-clean card wants `--process Ztautau Other`.
- **Phase 3 RUNNING (CPU, login node)**: EXACT reproduction of the 260623
  baseline recipe on the masked card — the two baseline rabbit_fit.py commands
  (fit `--noHessian --noEDM`; hessian `hessian_straightthrough=1 hessian_gn=1
  --externalPostfit ... --postfix HessianEDM`) with only card/-o swapped. Script
  `exact_fit_masked.sh`. Compare directly to existing baseline σ(αs)=**0.703**
  (pdfAlphaS=-7.640) — no baseline rerun needed.
  - NB (process notes): (1) fits here run on CPU (login node submit82 is
    GPU-less, 1.4TB RAM/768 cores); do NOT submit to slurm GPU — the SCETlib
    param-model fold OOMs on the small GPUs (11-24GB). (2) Do NOT use the
    fitterSCETlibNP.py wrapper for exact-baseline reproduction: it adds
    --fullNll and drops --noEDM (harmless for σ but not exact). Use
    print_command.py / meta_info commands verbatim.

### Tool: flagged_bin_yields.py (reproducible, login-node)
- `studies/muon-res-4d-normalization/flagged_bin_yields.py CARD [--process P]
  [--threshold T] [--top N] [--by-syst]`. Prints per flagged bin (any syst with
  |logk|>logT): yield sumw, √sumw2, n_eff, max|logk|, worst syst, ptll/yll/cos*/φ*
  coords. `--by-syst`: same-bins-vs-different cross-tab + systematics sorted by
  SIZE of largest variation (max|logk|→up-factor), the actual hazard.
- Same-bins finding (FranksVals): 328 bins tripped by 631 systs, avg 8.6 systs/bin;
  top 15 bins = 63% of trips; 7 bins tripped by >100 systs (n_eff~1e-6 → anything
  trips), but 89 bins by exactly 1 syst (private resolution-smearing tails). Both
  a shared core AND private tails. Sorted by size, top offenders are ALL
  Resolution_smearing (up-factors 1e6–1e15) landing on the shared-core bins.

### 2026-07-15 (fifth angle) — yields in the debug-flagged bins (FranksVals)
- Pulled Ztautau yields for every bin `rabbit_debug_inputdata` flags
  (|logk|>log2 → >2x or <0.5x in any syst): **328 bins**.
- They carry **13.2 / 5697 events = 0.23%** of Ztautau. Median nominal yield
  0.02 ev, median n_eff 0.03; **274/328 have n_eff<1; max n_eff over all 328 =
  1.98** (not one flagged bin has 2 effective events).
- Smoking gun = yield vs error: worst bin holds 0.00022 ± 0.215 ev — the MC stat
  error is ~1000× the content. Every flagged bin is a cancellation residual
  consistent with zero. That residual in the denominator → logk 20–35.
- Worst offenders dominated by Resolution_smearing variations (widest per-event
  weight spread → deepest log ratio on a degenerate bin), but pdf/Scale/pixel
  also appear. Confirms: it's the BINS, not the systematic.
- Physics: flagged bins are low-ptll (<6 GeV) Ztautau (small bkg, ~5700 ev)
  sliced into 49920 4D cells → tails get a few high-weight events per cell.

Mitigation options: (1) expose/enable `clipSystVariations` (dead code in
tensorwriter, no CLI; ALSO has a return-value bug in the dense get_logk path
where the clip is computed but `_logk_view` is returned instead — FIXME in
source); (2) n_eff-based syst pruning at setupRabbit (cleanest: zero systs where
the process nominal is stat-noise); (3) build with `--systematicType normal`
(fit-wide model change + neg predictions, needs validation, not a drop-in).

## Findings

- The 10^12 in `rabbit_plot_inputdata.py` is the θ=−1 mirror of
  logk = −37.43 in one Ztautau bin: 1.25e−4 · e^{+37.43} = 2.2×10^12,
  dominating the ptll projection.
- Root cause: 4D binning isolates Ztautau bins whose nominal is a
  floating-point cancellation of ± event weights; any weight-based syst ratio
  there is noise. The 2D card dilutes the same events into 780 populated bins.
- rabbit clips logk only for sign flips (to log(1e-3)), not for magnitude;
  `clipSystVariations` exists but is dead code (`False` hardcoded, no CLI).

## Decisions

- (pending) mitigation choice: magnitude clip in tensorwriter vs n_eff-based
  syst pruning at setupRabbit level.
