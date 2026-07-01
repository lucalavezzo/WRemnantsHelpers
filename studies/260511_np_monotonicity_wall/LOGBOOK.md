# runlog — 260511 NP monotonicity wall

## 2026-05-11

### Implementation
- Wrote `main/WRemnants/wremnants/postprocessing/np_monotonicity.py` (hardcoded `PARAM_MAP` + `NPMonotonicityMapping` + `NPMonotonicityWall`). Classes lazily resolved via PEP-562 `__getattr__` so the module imports without rabbit/TF on the histmaker side.
- Verified all six PARAM_MAP nuisance names match the user's existing HDF5 (`260511_debug/...LatticeNoConstraints/ZMassDilepton.hdf5`).

### Setup
- Re-ran setupRabbit on the histmaker output to neutralize the helper's `scale=10` CS inflation (`--scaleParams 'scetlibNPgamma=0.1'`) and to drop the lattice Gaussian priors on all six NP nuisances (`--noConstrainParams ...`). New output: `260511_npwall/...NPMonotonicity/ZMassDilepton.hdf5`.
- Confirmed in the new HDF5: all 6 NP names appear in both `hsysts` (always) AND `hsystsnoconstraint` (free-floating). Good.

### Fit
- rabbit_fit 4D real-data with criterion (b) regularizer at τ=0. Converged in 609s, edm=7.9e-13, saturated p=61.66%.
- The penalty contribution to NLL was 0.047, matching the per-term hinge accounting exactly (cross-check passes). Only firing term is the CS λ₂≥0 small-bT positivity hinge (λ₂ went to −0.217 at θ_λ₂ = +9.14).

### Physics interpretation
- See README for the postfit table. Headline: pulls are huge (θ_λ∞ = −259), physical values are pathological (λ∞ = +133, Λ₄ = −0.216), but **criterion (b) is silent** because:
  - λ₂ clamped to 0 inside the CS sqrt → CS λ₄ floor becomes 0 → λ₄ > 0 trivially holds.
  - TMD c₁(y)³ term grows fast with L₂(y); since the fit pushed Λ₂ up to 0.79, the c₁ floor loosens enough that Λ₄ can sit at −0.216 without triggering.
- α_S pulled by ~5σ (−10.28 in rabbit's 0.001 units): the NP nuisances are absorbing systematics they shouldn't, dragging α_S.

### Next options surfaced (not pursued yet, awaiting user direction)
1. ~~Switch to criterion (a) — tighter, should catch Λ₄<0.~~ **WRONG, corrected.** (b) is strictly tighter than (a) on both walls ($\sqrt 3 < \sqrt 4$, $\sqrt{20} < \sqrt{36}$ ⇒ (b)'s floor is closer to zero, so the wall bites earlier under (b)). Switching to (a) would loosen, not tighten.
2. Add a soft Tikhonov restraint per-nuisance on top of the wall (σ much wider than the dropped lattice prior).
3. Selectively re-introduce Gaussian priors on the wall-unconstrained nuisances (λ∞, ΔΛ₂).

## 2026-05-11 — second fit, CS λ∞ frozen

### Setup
- Same HDF5 as before; rabbit_fit with `--freezeParameters scetlibNPgammaLambdaInf` and removed `--doImpacts --globalImpacts` (the first attempt with impacts crashed at `MatrixInverse` — Hessian non-invertible at the new minimum, before fitresults were flushed; second attempt without impacts ran clean, 289s, edm=1.1e-17, p(sat)=61.5%).

### Postfit
| Param | λ∞-free θ | λ∞-frozen θ | Δθ |
|---|---|---|---|
| pdfAlphaS | −10.28 | −10.27 | ~0 |
| scetlibNPgammaLambda2 | +9.14 | +9.46 | +0.32 |
| scetlibNPgammaLambda4 | −8.08 | **−21.95** | **−13.87** |
| scetlibNPgammaLambdaInf | −259.21 | frozen | — |
| chargeVgenNP0scetlibNPZlambda2 | +2.16 | +2.29 | +0.13 |
| chargeVgenNP0scetlibNPZdelta_lambda2 | −0.76 | −0.76 | ~0 |
| chargeVgenNP0scetlibNPZlambda4 | −5.53 | **−8.81** | **−3.28** |

Physical values (rabbit pull → param via `param(θ) = nom + max(θ,0)·delta_up − max(−θ,0)·delta_down`):

| Param | physical | σ_phys | nominal |
|---|---|---|---|
| λ₂ | **−0.227** ⚠ | 0.088 | 0.0870 |
| λ₄ | +0.152 | 0.046 | 0.0074 |
| λ∞ | 1.6853 (frozen) | — | 1.6853 |
| Λ₂ | +0.822 | 0.191 | 0.25 |
| ΔΛ₂ | +0.110 | 0.008 | 0.125 |
| Λ₄ | **−0.381** ⚠ | 0.117 | 0.06 |

### Findings
- **α_S is blinded** — its central value carries an unknown random offset. Absolute pull magnitudes on `pdfAlphaS` reported in earlier drafts (and in the README) are NOT informative about physics. What *is* informative: postfit σ(α_S) and *differences* between fit configurations (blinding offset cancels in differences).
- The freedom λ∞ used to absorb went into λ₄ (θ shifted by −14) and Λ₄ (θ shifted by −3.3). Λ₄ deepened from −0.22 → −0.38 — this is real, not blinded.
- **TMD c₁(y=0) wall now slightly violated** (margin = −0.074, hinge penalty 0.0054) — first time the monotonicity wall actually fires.
- **Hessian still non-invertible at the new minimum** — the remaining NP nuisances are still nearly degenerate with each other or with α_S. Impacts can't be computed.
- Total penalty 0.0570 NLL units, matches arithmetic exactly (0.0515 CS λ₂≥0 + 0.0054 TMD c₁(0) violation).

## 2026-05-11 — τ=3 scan, both freeze options

### Setup
- Two fits at `--regularizationStrength 3.0` (penalty × e⁶ ≈ ×403): one freezing only λ∞, one freezing both λ∞ and λ₄. Both real-data, criterion (b), `-t 0`, no `--doImpacts`.
- Outputs in `260511_npwall/.../NPMonotonicity/tau3_freezeInf/` and `.../tau3_freezeInfL4/`.

### Quality
- Both converged with edm ~ 10⁻¹⁸ – 10⁻¹⁴. Saturated p-value 60.2–60.5%. Run time 130–170 s.

### Physical NP postfit values (real, not blinded)

| Param | τ=0 (λ∞ frz) | τ=3 (λ∞ frz) | τ=3 (λ∞+λ₄ frz) | AN nominal |
|---|---|---|---|---|
| λ₂ (CS) | −0.227 | −0.035 | −0.013 | 0.087 |
| λ₄ (CS) | +0.152 | +0.038 | FROZEN +0.0074 | 0.0074 |
| Λ₂ (TMD) | +0.822 | +0.366 | +0.319 | 0.25 |
| ΔΛ₂ (TMD) | +0.110 | +0.109 | +0.109 | 0.125 |
| Λ₄ (TMD) | −0.381 | −0.133 | −0.082 | 0.06 |

### α_S behaviour across configs (BLINDED — only Δ between configs is meaningful)
- σ(α_S) in σ_AN units: 1.15 (τ=0), 1.06 (τ=3 frz Inf), 1.07 (τ=3 frz Inf+L4). [convention: rabbit σ_θ × 2 = σ in σ_AN, since 1 rabbit θ-unit = 1 σ_AN = 0.002 absolute, and the "×2 scale" in workflows converts to template-step display.]
- Δ(α_S central) between configs: < 0.1 σ_AN. **The regularizer barely perturbs the POI**.

### Findings
- τ=3 makes the wall actually bite: λ₂ pulled from −0.227 to −0.035 (CS), Λ₂ from 0.82 to 0.37, Λ₄ from −0.38 to −0.13. All much closer to physical/AN values.
- Freezing λ₄ further reduces residual NP pulls (λ₂ to −0.013, Λ₄ to −0.08) — but at this point the wall is barely firing (penalty 0.07 NLL units).
- **At τ=3+freezeInf+freezeL4, the wall is essentially silent** — the fit has settled inside the feasible region of monotonicity, but Λ₄ still slightly negative and Λ₂ still ~25% above AN nominal. The wall isn't pulling these back any further because monotonicity doesn't require them at AN central — just non-pathological.

### Methodology concern: Asimov σ(α_S) > data σ(α_S)
- Asimov σ(α_S) = 1.33 σ_AN; data σ = 1.07 σ_AN. Discrepancy ~24%.
- Root cause: regularizer is a *hinge* (zero curvature inside feasible region, quadratic outside). At Asimov truth, all NPs sit at θ=0 where the hinge is silent → no curvature contribution to Hessian. At data postfit, λ₂ falls into the firing region → hinge adds curvature → tighter σ(α_S) via profile.
- Implication: the reported σ(α_S) on data depends on which side of the hinge boundary the data lands — not standard. Part of the data-uncertainty tightening is coming from the wall (theoretical prior) rather than from data.

## 2026-05-11 — Methodology checklist (going forward, do on Asimov first)

Before quoting any data result for the NP-related sensitivity, run this checklist:

1. **Uninflated baseline**: setupRabbit with `--scaleParams 'scetlibNPgamma=0.1'` to undo the helper's ×10, no `--noConstrainParams`, no inflation of TMD priors. Use the AN/lattice σ as quoted. Freeze only CS λ_∞ (physics-motivated, large-bT asymptote).
   - **Acceptance**: data pulls within ±1σ_prior → priors are reasonable. Postfit NPs physical. σ(α_S) well-defined.
   - **Failure modes**:
     - Pulls > 2-3 σ_prior on any nuisance → priors are too tight; consider inflation.
     - Hessian singular → degeneracy not lifted; consider inflation.
     - NPs land far from nominal (even with priors anchoring) → look for which one is fighting.
2. **If baseline fails**: try modest inflation (e.g., ×2-3) on the offending nuisances. Re-check.
3. **If still issues**: data-driven inflation factors (use unconstrained fit pulls to set widths).
4. **Last resort**: unconstrained NP fit + LR scan for σ(α_S), no Gaussian priors. Smooth function shapes guaranteed by the regularizer wall.

Each step expands the prior trust band; we want to use the tightest defensible priors.

## 2026-05-11 — Free-λ_4 (CS) test, inflated priors

### Motivation
After the CS Up/Down sign-convention correction and the `delta_lambda2` nominal correction, re-questioned whether freezing CS λ_4 was actually necessary or just a precaution against the (sign-convention-corrupted) earlier reads. Original freeze was justified by Hessian non-invertibility under the *regularizer + dropped-priors* setup. Did it persist under the inflated-priors setup?

### Setup
- HDF5: `NPInflatedFreeLambda4` — same as `NPInflated` but with `--scaleParams 'scetlibNPgammaLambda4=0.35'` added (inflates CS λ_4 by ×3.5 net, matching the ×3.5 inflation on CS λ_2 and TMD Λ_4).
- Fit: same as inflated, freeze ONLY `scetlibNPgammaLambdaInf` (not λ_4). Both real-data + Asimov + `--doImpacts --globalImpacts`.

### Results
- **Hessian invertible — `--doImpacts` ran successfully**. No `MatrixInverse: not invertible` error. The inflated Gaussian priors provide enough curvature to lift the degeneracy that broke the regularizer+free-NPs setup.
- λ_4 (CS) physical postfit = **+0.013 ± 0.006**, about 1σ_lat above AN nominal 0.0074. Modest, physical.
- σ(α_S) = 1.071 σ_AN vs 1.070 with λ_4 frozen. **Difference < 0.1%** — the freeze did not artificially tighten σ(α_S).
- Asimov σ(α_S) = 1.087 σ_AN (vs data 1.071) — clean methodology, no hinge artifact.
- ptll saturated p-value: 2.67% (free-L4) vs 2.18% (frozen-L4) — small improvement from the extra absorption knob.
- Other parameters barely shifted. Strongest effect: TMD Λ_4 dropped from +0.025 to +0.011 (some correlation between CS λ_4 and TMD Λ_4, both controlling b_T^3-ish behavior).

### Verdict
**The CS λ_4 freeze was not necessary under the inflated-priors setup.** The original Hessian-degeneracy concern (which justified the freeze) was specific to the regularizer-without-priors configuration. With inflated Gaussian priors, the parameters separate cleanly.

Recommendation: drop the CS λ_4 freeze. Keep only the CS λ_∞ freeze, which is physically motivated (large-bT asymptote, weakest data leverage).

## 2026-05-11 — delta_lambda2 nominal correction

When making the canonical np_param_map.json with a collaborator in mind, realized that in the `LatticeNoConstraints` branch the histmaker uses **delta_lambda2 nominal = 0** (no y-dependence in central), NOT the AN-quoted 0.125 GeV². The templates at ±0.02 are absolute, consistent with the other lowercase entries in that branch (lambda2 at [0.0, 0.5] and lambda4 at [0.01, 0.12], both absolute).

The AN's quoted `Delta_Lambda_2 = 0.125` only applies to the uppercase `Delta_Lambda` parametrization branch (lines 836-844 of rabbit_theory_helper.py), where the templates are interpreted as variations around the AN central. We were inadvertently mixing the two conventions.

**Impact on previous reports**:
- Postfit physical ΔΛ_2 values I quoted as +0.109–+0.112 are actually around **−0.013 to −0.016** (small negative shift from 0).
- TMD wall evaluations using L_2(y) = Λ_2 + ΔΛ_2·y² were wrong by ΔΛ_2 ≈ 0.125 ≈ the AN-side offset that doesn't apply.
- Re-running the table with the corrected map shows ΔΛ_2 around 0 ± 0.008 across all configurations — consistent with "data prefers nominal value of 0".

**PARAM_MAP correction** in `np_monotonicity.py`: `nominal=0.0, up_value=0.02, down_value=-0.02` for `chargeVgenNP0scetlibNPZdelta_lambda2`.

Canonical JSON now lives at `WRemnantsHelpers/scripts/np_param_map.json`. A table-making script `WRemnantsHelpers/scripts/print_np_postfit_table.py` reads this JSON and converts rabbit postfit pulls to physical λ values for any number of fitresults.hdf5 files.

## 2026-05-11 — CS Up/Down convention FIXED in rabbit_theory_helper.py

Changed `rabbit_theory_helper.py:706-715` (LatticeNoConstraints branch of `add_gamma_np_uncertainties`):
- `for direction in ["Up", "Down"]` → `for direction in ["Down", "Up"]`

`lattice_vals` is ordered `[smaller, larger]` per pair (e.g. `lambda2_nu0.0538` before `lambda2_nu0.1202`). With the new iteration order, the smaller-value template is now paired with `Down` and the larger-value template with `Up` — **standard convention restored**: positive rabbit pull on `scetlibNPgammaLambda*` corresponds to LARGER physical λ.

Files updated:
- `main/WRemnants/wremnants/postprocessing/rabbit_theory_helper.py` — the actual fix.
- `main/WRemnants/wremnants/postprocessing/np_monotonicity.py` — PARAM_MAP entries swapped (up_value ↔ down_value, hist_up_label ↔ hist_down_label).
- `WRemnantsHelpers/scripts/np_param_map.json` — canonical JSON updated.

**CAVEAT for existing HDF5s**: HDF5s produced BEFORE this fix used the inverted convention. To re-interpret postfit pulls from old HDF5s under the standard convention, flip the sign of the rabbit θ for the three CS-gamma nuisances. New HDF5s produced from setupRabbit after the fix use the standard convention directly. The `print_np_postfit_table.py` script reads the JSON (which now reflects the post-fix convention), so it will give correct physical values for NEW HDF5s but inverted-sign values for OLD HDF5s.

Other branches (`LatticeEigvars`, uppercase `Lambda` family, Omega) untouched — their conventions were already consistent or not affected.

## 2026-05-11 — CS Up/Down convention inversion (originally identified)

When comparing pulls/physical values with a colleague's analysis on the same fit, the major-looking discrepancies turned out to be the Up/Down sign convention applied at the post-processing step, not anything wrong with the fit itself.

**rabbit_theory_helper.py:686-711 pairs positionally:**
- `scetlibNPgammaLambda2`**Up** ↔ `lambda2_nu0.0538` (the *smaller* physical value, ≈ −1σ_lat)
- `scetlibNPgammaLambda2`**Down** ↔ `lambda2_nu0.1202` (the *larger* physical value, ≈ +1σ_lat)

Same inversion for `Lambda4` and `LambdaInf`. So a *positive* rabbit pull on these nuisances corresponds to the *smaller* physical value — opposite of the standard "Up = larger" reading.

A colleague reading rabbit's printed θ=+1.23 under the standard convention would infer "physical λ_2 went UP by 1.23 σ_lat" → λ_2 ≈ 0.087 + 1.23·0.0332 = +0.128. The actual rabbit-encoded interpretation is "physical λ_2 went DOWN" → λ_2 ≈ 0.087 − 0.041 = +0.048. Mirror images around the central.

PARAM_MAP in `wremnants/postprocessing/np_monotonicity.py` correctly encodes this (`up_value < nominal` so `delta_up < 0`), but the inversion has been documented inline with a ⚠️ block so future readers don't trip on it.

The earlier reports of "wildly negative physical λ_2 (−0.31)" combined the inversion with the helper's internal `scale=10` for `LatticeNoConstraints`, amplifying a 0.04 shift to 0.4. With the standard convention OR with scale=1, the shift stays sane.

## 2026-05-11 — Alternative test: inflated Gaussian priors (no regularizer)

### Motivation
Replace the hinge with smooth Gaussian priors, inflated empirically so that the regularizer-postfit pulls land within ±1σ_prior. Sidesteps the hinge-non-smoothness methodology issue.

### Setup
- Re-ran setupRabbit with `--scaleParams 'scetlibNPgammaLambda2=0.35' 'chargeVgenNP0scetlibNPZlambda4=3.5'` and NO `--noConstrainParams`. Other 4 NPs left at default scale.
- The CS λ₂ factor of 0.35 composes with the helper's internal ×10 to give net ×3.5 inflation on the CS prior. TMD Λ₄ factor 3.5 directly.
- Output: `260511_npwall/.../NPInflated/{data,asimov}/fitresults.hdf5`.
- Same `--freezeParameters scetlibNPgammaLambdaInf|scetlibNPgammaLambda4` at fit time. NO `-r` regularizer, NO `--regularizationStrength`. Standard rabbit_fit.

### Results

**Physical NP postfit values** (compared with τ=3 regularizer):

| Param | Regularizer (τ=3) | Inflated priors | AN nominal | Verdict |
|---|---|---|---|---|
| λ₂ (CS) | θ=+3.01 → −0.013 ❌ | θ=+1.12 → **+0.050** ✅ | 0.087 | now positive! |
| Λ₂ (TMD) | θ=+0.27 → +0.319 | θ=+0.48 → +0.370 | 0.25 | both fine |
| ΔΛ₂ (TMD) | θ=−0.79 → +0.109 | θ=−0.67 → +0.112 | 0.125 | both fine |
| Λ₄ (TMD) | θ=−2.84 → −0.082 ❌ | θ=−0.70 → **+0.025** ✅ | 0.06 | now positive! |

**σ(α_S)** (in σ_AN units; θ × 2):

|  | Data | Asimov | Discrepancy |
|---|---|---|---|
| Regularizer (τ=3) | 1.07 | 1.33 | +24% (hinge artifact) |
| Inflated priors | **1.07** | **1.09** | **+2% (consistent)** |

### Findings
1. **NP postfit values now physical** — both λ₂ and Λ₄ land at *positive* physical values, in line with the OPE/variance-interpretation expectation. The regularizer alone could not achieve this; inflated Gaussian priors do.
2. **σ(α_S) Asimov ≈ data**, fixing the methodology concern. Constant curvature from Gaussian priors means the Hessian-derived σ is the same at any postfit point (locally).
3. **σ(α_S) data is unchanged** at 1.07 σ_AN ≈ ±0.00107 — the inflated-priors approach gives the same data uncertainty as the regularizer, just with a cleaner Asimov estimate to back it.
4. All NP pulls within ±1.2σ of their inflated priors — the 3.5× inflation was sized correctly.

### Trade-off
This is *not* equivalent to the regularizer with smoother penalty. The Gaussian priors are an explicit "anchor near AN nominal with σ ≥ |postfit pull|" — a transparent statement that we trust the AN nominals to 3.5×lattice σ but no tighter. The monotonicity wall was a more agnostic constraint (only "no pathologies"), but in practice it failed to anchor the parameters because monotonicity alone doesn't pick out the AN region.

**Conclusion**: for this fit configuration, **inflated Gaussian priors are a cleaner and more controlled alternative to the hinge regularizer**. Recommend adopting unless we specifically want the "no theoretical anchor beyond monotonicity" stance.

### Pointers
- Setup script: `/tmp/test_np_monotonicity_setup.sh`
- Fit script: `/tmp/test_np_monotonicity_fit.sh`
- New input HDF5: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_NPMonotonicity/ZMassDilepton.hdf5`
- Fit result: `.../fitresults.hdf5`
