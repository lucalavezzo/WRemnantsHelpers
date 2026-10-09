---
title: 1D ptll-only and yll-only fits — is the 2D tension in ptll, in yll, or in combining them?
slug: 260925-1d-fits
study: lattice-cs-kernel
status: active
created: 2026-09-25
updated: 2026-09-25
owner: main session (Luca)
---

# 1D ptll-only and yll-only fits — is the 2D tension in ptll, in yll, or in combining them?

**Task:** card A (2D, no lattice) fails the ptll projected-saturated test (walled ~70/39; the unwalled deepest
minimum 56/39, but only with λ2_ν < 0). The yll marginal also has its own tension (42/20), and it pulls α_s
the other way. Does the model describe ptll alone and yll alone? And how does α_s from a 1D ptll fit compare
with the 2D one?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-09-25 ~16:50)

> **All 1D ptll fits done** (the unwalled δλ2 = 0 one is NOT converged, EDM 0.03). Nothing is running.
> Freezing δλ2 = 0 brings 1D α_s back to within 0.6σ of 2D (walled), and makes the 1D fit behave like 2D:
> - the 2D-like A0 / lumi / weak / FSR pulls return;
> - the unwalled escape moves to the CS kernel, λ2_ν = −0.11, just as in 2D.

- **Next action:** Luca to decide whether to resume P1DUNWNODL2W from its snapshot until it converges.
- **Blocking on:** nothing.

---

## Log

### 2026-09-25 ~16:50 — P1DUNWNODL2W (unwalled, δλ2 = 0, warm from P1DUNW) finished, NOT converged
- 716 iterations, 24242 s, EDM **0.030** (the others: ≤ 1e-11). NLL 29.741, which is below the walled δλ2 = 0 minimum
  of 30.603, as it must be. q = 59.48 / 38, p = 1.45 %, an UPPER bound given the EDM.
- **λ:** TMD λ2 = 0.41, λ4 = −0.026, **λ2_ν = −0.107**. With δλ2 unavailable, the unwalled fit escapes through
  the CS kernel, exactly as the 2D unwalled fit does (CCKRYLOVWARM: λ2_ν = −0.09), not through the TMD as 1D
  with δλ2 did.
- **Pulls:** A0 −1.10, lumi −0.86, weak −0.67, FSR −0.65, mb_up −1.84, i.e. 2D-like.
- **α_s:** −1.80e-3 vs CCWALLWARMPF (−1.66σ). The 2D unwalled fit is at −0.92σ. σ(α_s) = 1.77, a Hessian at a
  non-converged point, so provisional.
- **Read:** with δλ2 frozen, the 1D ptll fits reproduce the 2D pattern (the same pulls, the same unphysical
  escape, α_s near 2D). So the 1D/2D differences were δλ2, not yll per se.
  - The escape buys less in 1D (61.2 → ≤ 59.5) than in 2D (70.4 → 56.0), but this fit is not converged.
  - Resuming from `snapshot_P1DUNWNODL2W.hdf5` would settle it.

### 2026-09-25 ~15:55 — P1DWALLNODL2W (walled, δλ2 = 0, warm) done; P1DUNWNODL2W still running
- **Result:** 2ΔNLL_sat 61.21 / 38, p = 0.99 % (against 55.13, 3.6 % with δλ2 free); NLL 30.603 (against
  27.564), so freezing δλ2 costs 2ΔNLL = 6.1.
  - My mid-run "~16" estimate (13:50) was premature; the converged cost is 6.1.
  - EDM 1e-17, 8305 s.
  - The "2.45 %" in the log is the postfit linear χ², not the saturated test.
- **α_s:** Δ vs CCWALLWARMPF = −0.68e-3 (**−0.63σ**), against −3.20e-3 (−2.95σ) with δλ2 free.
  σ(α_s) = 1.43e-3, against 1.87 with δλ2 free.
  **So the 1D-vs-2D α_s gap is ~80 % δλ2**, confirming the regression.
- **Pulls come back to the 2D pattern:** A0 15–20 −1.23, lumi −1.09, weak −0.84, FSR −0.74, mb_up −1.94 (with
  δλ2 free: −0.68 / −0.36 / −0.29 / −0.47 / −1.99). TMD λ2 = 0.16, off the wall.
- **REFINES Result point 3:** those pulls are not caused by "combining ptll with yll" as such. They are what the
  fit uses to shape low ptll once δλ2 is unavailable, whether yll pins it (2D) or we do (here).

### 2026-09-25 ~14:15 — δλ2-frozen fits relaunched WARM (Luca); the cold ones killed
- The cold P1DWALLNODL2 / P1DUNWNODL2 were killed (SIGTERM to their python pids) before iterating. Their dirs
  hold nothing usable.
- **Warm:** P1DWALLNODL2W = `--externalPostfit P1DWALL/fitresults`, P1DUNWNODL2W = `--externalPostfit
  P1DUNW/fitresults`, each with the 44-name fit_params (no δλ2).
  - `load_fitresult` (fitter.py:499) copies the INTERSECTION of parameter names, so the seed's δλ2 is simply
    dropped.
  - δλ2 is held at the anchor: the wall log gives δλ2 = 0 + 0.5θ, so the physical δλ2 = 0 exactly.
  - Deviation from the fit-queue seeding rule (a seed may differ only in the wall): here it differs by the
    frozen δλ2, deliberately, since that is the test.

### 2026-09-25 ~14:00 — ptll fits without δλ2 launched
- **Why (Luca):** "δλ2 and λ2 have the same effect". Checked: L2(Y) = λ2 + δλ2·Y² (NP_models_formulas.hpp:55),
  so a pure shift of the effective L2 is degenerate with λ2. But the 1D fits use δλ2 for something else:
  - walled: L2 runs from 0.004 at Y = 0 (on the wall) to ~1.9 at |Y| = 2.5;
  - unwalled: from −0.36 to ~+4.3.

  That is, they build the y-integrated ptll shape from a MIXTURE of very different NP shapes across rapidity,
  which λ2 alone cannot do.
- **Test:** freeze δλ2, i.e. leave it out of fit_params (44 SCETlib names; `logs/fit_params_nodl2.txt`), the
  same method as λ4_ν in the l4zero fits.
  - `scripts/run_1d.sh` now takes extra model args.
  - Tags P1DWALLNODL2 and P1DUNWNODL2, cold, with the same settings as P1DWALL / P1DUNW.
- **Prediction if the reading holds:** the p-value gets worse, towards the 2D projection level, and α_s moves
  back towards 2D.

### 2026-09-25 — what the better 1D ptll p-value means (discussion, no runs)
- **1D walled 55/38 vs the 2D ptll projection 70/39** (the same card, walled): the ~15 units gained in 1D line up
  with δλ2 being free in 1D (+0.63θ; ρ(α_s, δλ2) = −0.67). In 2D the y-dependence pins δλ2 ≈ 0.
- **Read:**
  - The model CAN make the y-integrated ptll shape, within physical NP, through δλ2, but δλ2 is a
    RAPIDITY-DEPENDENT knob.
  - In 2D the data reject its y-dependence. The band test showed the wanted ptll correction is
    y-INDEPENDENT (189/195).
  - So the 2D tension is plausibly "the data want a y-independent low-ptll shape that the model can only produce
    in a y-dependent way (δλ2), or unphysically (λ2 < 0, λ2_ν < 0)".
  - That also explains why the ptll projection is bad in 2D but the ptll marginal residuals are fine in every fit.
- **Caveat:** 3.6 % is asymptotic (the calibrated value is likely lower), and it is not "good". The 53 % needs
  TMD λ2 = −0.36.
- **Test:** the δλ2-fixed 1D fit checks this AND the α_s story at once. With δλ2 held at its 2D value, the 1D p
  should drop towards the 2D-projection level and α_s should return towards 2D.

### 2026-09-25 ~13:40 — why 1D α_s is low: δλ2 is unconstrained in 1D
- `scripts/alphas_correlations.py`, `scripts/delta_lambda2_regression.py`.
- **The strongest α_s correlation in the 1D fits is δλ2**, the rapidity-dependent TMD NP term: ρ = −0.67
  (walled) and −0.50 (unwalled).
  - In 1D, δλ2 moves from its 2D value by +0.63θ (walled) and +1.51θ (unwalled). Nothing in 1D pins it; in 2D
    the y-dependence of the ptll shape does.
- **Linear regression of α_s on δλ2 inside each 1D fit** predicts shifts of −3.7e-3 (walled) and −5.0e-3
  (unwalled). The observed shifts are −3.2e-3 and −4.8e-3.
- **Read:**
  - The 1D-vs-2D α_s shift is almost entirely δλ2 absorbing low-ptll shape in 1D, and α_s moving with it.
  - That is an information/degeneracy effect of dropping yll, not an independent sign of inconsistency.
  - But it shows again that α_s sits on an NP degeneracy. The top α_s correlations in 2D are also NP λ:
    λ4_ν (+0.76 walled), λ4 (+0.72) and λ2 (−0.64) in the unwalled fit.
- **Test:** a 1D fit with δλ2 fixed at its 2D value should bring α_s back near 2D.

### 2026-09-25 13:00 — P1DWALL / P1DUNW finished; harvested
- `scripts/harvest_1d.py`. Both exited rc 0.
  - P1DWALL: 515 iterations, EDM 2.1e-15, 11126 s.
  - P1DUNW: 361 iterations, EDM 1.1e-11, 6653 s.
  - rabbit ndof = 39 bins − 1 free (α_s) = 38.

### 2026-09-25 — cache used; yll dropped
- **Cache:** both ptll fits use the OLD cache `pdf62_corrgrid_260827` (the authval build), read from the
  /scratch mirror. Load times from the logs: 275 s and 476 s.
  - It is the cache card A and all the 2D reference fits used, so the 1D ↔ 2D comparison is like-for-like.
  - It is NOT the new |Y| ≤ 3.5 cache `pdf62_y35_260921`, which needs its own card.
- **The yll-only fit is dropped** (Luca).

### 2026-09-25 ~11:00 — startup checks; the yll fit killed (model/card ptll-range mismatch)
- **All three:**
  - "fitting 45 of 53 SCETlib parameter(s) + 2 envelope", the same as the card-A reference fits;
  - the wall is armed on 6 of 8 conditions (walled runs);
  - "marginalized R over reco axes [...] (fit channel is 1D)" is printed. The printed "Linear chi2" (ptll
    30/39, yll 27/20) is the PREFIT card-nominal χ², not the model's.
- **Problem (yll only):**
  - The stored response R has reco ptll 0–100 GeV in 40 bins, the last one 44–100. It is identical in all three
    cards, and `sum R` is the same too.
  - For 2D and ptll-only, `crop_R_to_fit` (response.py:54) crops ptll to the fit's 0–44.
  - For yll-only, `marginalize_R_reco` (response.py:101) SUMS the dropped ptll axis over all 40 bins, 44–100
    included. The yll data (`--presel ptll:sum 0j 44j`) exclude it.
  - So the model overcounts by 3.4 % overall, and that is y-dependent (2.2 % at the outer bins, 3.8 % in the
    centre), which distorts the shape.
  - Y1DWALL was killed with SIGTERM to its python pid; nothing to reuse.
- **Fix options** (needs Luca's OK, since it touches the AD model):
  - (a) a param-model option to crop a dropped reco axis to a range before marginalising, e.g.
    `marginal_ranges=ptll:0:44`, or to read the card's presel from its meta_info;
  - (b) store an R that is already cropped to ptll < 44 in the card.

  (a) is ~10 lines in `response.py` / `param_model.py`.

### 2026-09-25 ~10:15 — cards built (with card A's own code) and validated; fits launched
- **Current main cannot rebuild card A.**
  - ptll: `add_pdf_alphas_variation` fails ("…CT18Z_N3p0LL_N2LO_pdfas_Corr not found"). Card A was built from
    WRemnants c838fc6 PLUS an uncommitted `_sidecar_corr_hist` resolver, recorded in card A's meta_info
    git_diff. It never reached main; `ede643dc` replaced it with a different fix.
  - yll: `--axlim ptll` is refused for a non-fit axis.
  - Failed logs: `logs/make_card_*_failed_main.log`.
- **Fix:**
  - worktree `/work/submit/lavezzo/alphaS/wrem-cardA-c838fc6` = c838fc6 + card A's recorded diff (WRemnants files
    only);
  - submodules symlinked from the main tree. narf / wums / wremnants-data are at card A's exact commits;
    rabbit is 2a59246 instead of f77f10e;
  - `git rm --cached` of the 4 submodule gitlinks in the worktree index only, so the provenance `git diff` does
    not choke on the symlinks (first retry failed on that: `logs/make_card_*_failed_gitdiff.log`);
  - yll uses `--presel ptll:sum 0j 44j` (restrict ptll to [0,44], then sum) in place of `--axlim ptll 0j 44j`.
- **Validation** (`scripts/check_cards.py`): both 1D cards have the same 3673 nuisances as card A (0 differ) and
  the same total data count, 7,243,186. So the yll ptll cut reproduces card A's selection.
- **Launched** `scripts/run_1d.sh`: threads=64 each, cache from the /scratch mirror.

### 2026-09-25 — design (agreed with Luca)
- **Cards:** card A's exact setupRabbit command, read from its meta_info, with only `--fitvar` (`ptll` /
  `yll`) and `-o` (`/ceph/.../alphaS/260925_Z_1D_card_adcorr/`) changed. `scripts/make_cards.sh`, logs in
  `logs/make_card_*.log`.
- **Fits:** all COLD. A warm start from a 2D fit is not allowed across cards. No lattice. Settings are copied from
  the card-A references:
  - walled = the CCWALLCOLDR command (wall regulariser, strength 5, `--earlyStopping 100`);
  - unwalled = the CCKRYLOV command;
  - SCETlib build authval; cache from the /scratch mirror.
  - In 1D the full saturated test IS the projection test, so no `-m` is needed.
  - yll: walled only. In a yll-only fit the NP λ are barely constrained, so an unwalled run would mostly
    explore the NP degeneracy.
- **Comparisons:**
  - ptll walled ↔ CCWALLWARMPF / CCWALLCOLDR (2D projected 70–72/39);
  - ptll unwalled ↔ CCKRYLOVWARM (56/39);
  - yll ↔ the 2D YLL projection test (42/20).
  - Δα_s 1D − 2D in σ units only (same blinding family: integer data, same parameter name).
- **Earlier 1D reference:** July 1D walled on the OLD model (`260723_Z_1D`) was fine after toys (p ≈ 7 %,
  effective ndof ≈ 35). It used a different model and card, so it is not directly comparable.

---

## Result

**Caveats first:**
- Cold fits, 1D ptll card = card A projected (validated: same nuisances, same data), no lattice, old cache.
- α_s only as Δ in σ units. It is the same blinding family: integer data, the same parameter name.
- The p-values are asymptotic. The July 1D toys found an effective ndof below rabbit's count, which makes the
  honest p SMALLER than printed.
- 1D and 2D minima can sit in different basins.

| fit | 2ΔNLL_sat / ndof | p | NLL | σ(α_s) [1e-3] | Δα_s vs CCWALLWARMPF [1e-3] (σ_ref) | TMD λ2 | λ4 | δλ2 | λ2_ν | λ4_ν | A0 15–20 | lumi | mb_up | weak | FSR |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **P1DWALL** (1D, walled) | **55.13 / 38** | **3.6 %** | 27.56 | 1.866 | −3.20 (−2.95) | +0.004 | +0.002 | **+0.31** | +0.003 | +0.050 | −0.68 | −0.36 | **−1.99** | −0.29 | −0.47 |
| **P1DUNW** (1D, unwalled) | **36.74 / 38** | **53 %** | 18.37 | 1.425 | −4.76 (−4.39) | **−0.36** | +0.020 | **+0.74** | +0.012 | +0.136 | 0.00 | +0.13 | −0.42 | +0.10 | +0.22 |
| CCWALLWARMPF (2D, walled) | ptll proj. 70.4/39 | 0.15 % | 371.44 | 1.085 | 0 (ref.) | +0.108 | +0.002 | −0.009 | +0.005 | +0.043 | −1.83 | −1.43 | −1.52 | −1.12 | −1.00 |
| CCKRYLOVWARM (2D, unwalled) | ptll proj. 56.0/39 | 3.8 % | 365.49 | 1.217 | −1.00 (−0.92) | +0.273 | +0.203 | −0.007 | **−0.091** | +0.001 | −1.67 | −1.07 | −1.39 | −0.86 | −0.72 |

**Δα_s:**
- 1D walled − 2D walled: −2.95σ (vs CCWALLWARMPF) / −2.74σ (vs CCWALLCOLDR), in 2D σ. That is **−2.1σ** against
  the nested sd √(σ_1D² − σ_2D²).
- 1D unwalled − 2D unwalled: −3.09σ_2D (−5.1 nested). The two are different NP configurations, so treat the
  nested number with care.
- 1D unwalled − 1D walled: −0.84σ.

**Read:**
1. **The ptll spectrum alone is NOT well described by the physical (walled) model:** p = 3.6 %, and lower once
   the ndof is calibrated. So the tension is not only "ptll vs yll". But it is smaller than the 2D ptll projection
   (55 vs 70).
2. **The NP model can describe ptll alone perfectly (p = 53 %), but only unphysically.** The wall costs 18.4
   units in 1D (≈ 12 in 2D).
   - In 1D the fit goes unphysical in the TMD sector: λ2 = −0.36, δλ2 = +0.74.
   - In 2D (CCKRYLOVWARM) it goes unphysical in the CS kernel instead (λ2_ν = −0.09).
   - Two different escapes, so the missing shape is "NP-like" but has no physical NP realisation.
3. **(REFINED 15:55)** In 1D walled the A0 / lumi / weak / FSR pulls shrink to −0.3…−0.7, but they come back
   (−0.7…−1.2) once δλ2 is frozen at 0. They are the levers the fit uses for the low-ptll shape when δλ2 is
   pinned, not a ptll-vs-yll effect as such.
4. **mb_up stays pulled at −2.0 in 1D walled** (−1.5 in 2D). This is the only big pull that survives ptll-alone
   within physical NP, which is consistent with a missing quark-mass effect in the ptll shape. mb_up is the
   MiNNLO Z+bb̄ fixed-order mass correction, not a resummation mass effect. Suggestive, not proof.
5. **α_s:** ptll alone gives a lower α_s than 2D, by ~2σ nested (walled). The direction matches the region
   tests (freeing low-ptll bins moved α_s down), and is opposite to freeing yll.
