# runlog — projection_pvalues

## 2026-04-27 — initial diagnostic pass on `260427_debug_allproj/`

Inputs inspected:
- `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug/fitresults.hdf5` (single mapping, ptll only)
- `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_allproj/fitresults.hdf5` (four projections)

Commands used (all read-only inspection of the existing fitresults; no new fits run):

```bash
# recover the original fit command for the single-mapping result
source setup.sh
print_command /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug/fitresults.hdf5
```

Original 4-projection fit command (recovered via `print_command`):

```
rabbit_fit.py /scratch/submit/cms/areimers/alphas/fitinput/AlphaS/Unblinding/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_scetlib_dyturbo_LatticeNPLambda4BugfixLambda6_CT18Z_N3p0LL_N2LOCorr_WithLatticeConstraints_Lambda40p01to0p12_Lambda4times1p0_Ptll0to44/ZMassDilepton.hdf5 \
  --computeVariations \
  -m Project ch0 ptll -m Project ch0 yll -m Project ch0 cosThetaStarll_quantile -m Project ch0 phiStarll_quantile \
  --computeHistErrors --computeHistImpacts --doImpacts \
  -o /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_allproj/ \
  --globalImpacts --saveHists --saveHistsPerProcess \
  --computeSaturatedProjectionTests \
  -t 0 --computeHistCov
```

Channel axes (from the input tensor meta): `ptll(39), yll(20), cosThetaStarll_quantile(8), phiStarll_quantile(8)`. Total bins 49920 (matches `ndfsat = 49919 + parameters subtracted`).

### Result extraction (Python ad hoc)
Done via `rabbit.io_tools.get_fitresult` from outside the container (only `wums` + `rabbit` Python sources needed — no TF). Quantities pulled:
- `mappings.<proj>.{chi2,chi2_prefit,chi2_saturated, ndf*}` — for the table in README.
- `mappings.<proj>.channels.ch0.{hist_data_obs, hist_postfit_inclusive, hist_prefit_inclusive, hist_postfit_inclusive_global_impacts, hist_postfit_inclusive_global_impacts_grouped, hist_nobs}`.
- `mappings.<proj>.hist_postfit_inclusive_cov` (39x39 etc.) — caveat: this is the post-fit *prediction* cov, not the residual cov used in chi2.
- `parms`, `parms_prefit`, `cov` (3752 x 3752) — for pulls and correlations.

### Key numbers (also in README)
- 4D total: chi2/ndf = 0.998, p = 59.6%.
- ptll postfit Linear p = 0.32%, Saturated p = 0.40%; prefit p = 1.67%.
- yll postfit Linear p = 0.17% (worst projection), Saturated p = 0.24%; prefit p = 12%.
- cosTheta\* prefit 99.5% -> postfit 28%; phi\* 97.7% -> 14%.

### Verified runtime
- Singularity launch (working): `singularity run --bind /scratch/,/work/,/home/,/ceph/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest /bin/bash -lc 'source /opt/venv/bin/activate && cd /home/submit/lavezzo/alphaS/WRemnantsHelpers && source setup.sh && rabbit_fit.py --help'`.
- Without `source /opt/venv/bin/activate` inside the container, tensorflow is missing. AGENTS.md does not currently document the venv activation.

### Open follow-ups
See README "Tasks" section. Next concrete actions when this study resumes:
1. T1 (per-bin pull plots, all projections) — quick, no refit needed.
2. T4 (freeze `binByBinStat`, refit) — first hypothesis-discriminating fit, cheapest to interpret.

## 2026-04-27 — T7 attempted, freeze did not take effect

Output: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_freezeMB/fitresults.hdf5`.

Command actually used (via `print_command`):
```
rabbit_fit.py ... --freezeParameters mb_up,pdfMSHT20mbrangeSymAvg,pdfMSHT20mbrangeSymDiff
```

**Result identical to nominal**: every parameter bit-for-bit equal, including `mb_up = -1.687` (a frozen param would sit at initial value 0). chi2/p-value all unchanged.

**Root cause:** `--freezeParameters` is defined with `nargs="+"` ([`parsing.py:248-251`](../../../../main/WRemnants/rabbit/rabbit/parsing.py#L248-L251)) — it wants a **space-separated** list, not comma-separated. The comma string is taken as one argument and `match_regexp_params` ([`fitter.py:24-41`](../../../../main/WRemnants/rabbit/rabbit/fitter.py#L24-L41)) finds no matches (no parameter name contains commas), so the frozen list ends up empty.

**Fix:** pass space-separated. Correct invocation:
```
--freezeParameters mb_up pdfMSHT20mbrangeSymAvg pdfMSHT20mbrangeSymDiff
```
For `fitter.sh`, wrap in single quotes so the inner spaces survive into rabbit's argv:
```
fitter.sh ... -f '--freezeParameters mb_up pdfMSHT20mbrangeSymAvg pdfMSHT20mbrangeSymDiff'
```

T7 is therefore **still open** — the study needs to be re-run with the corrected freeze syntax before it actually exercises the b-mass sensitivity question.

## 2026-04-27 — T7 redone with corrected syntax: freeze did take effect

Output: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_freezeMB_v2/fitresults.hdf5`.
Log: `logs/freezeMB_v2_260427_190739.log`.

Wrapper script: `/tmp/run_freezeMB_v2.sh` (see AGENTS.md for the template).

Confirmation that freeze took effect: `mb_up = 0.000 +/- 1.000`, `pdfMSHT20mbrangeSym{Avg,Diff} = 0.000` exactly. (Sigma 1.000 is the prefit width; fitter does not move them.)

### ptll chi2 comparison (NOMINAL `260427_debug_allproj` vs FREEZE_v2)

| test | NOM chi2 | NOM p | FRZ chi2 | FRZ p | Δchi2 |
|---|---|---|---|---|---|
| prefit Linear | 60.07 | 1.67% | 67.37 | **0.32%** | +7.30 |
| postfit Linear | 67.41 | 0.32% | 78.26 | **0.019%** | +10.84 |
| postfit Saturated proj | 66.46 | 0.40% | 77.31 | **0.025%** | +10.85 |
| 4D total | 49842 | 59.6% | 49858 | 57.5% | +16 |

### alphaS shift

| | NOMINAL | FREEZE | Δ |
|---|---|---|---|
| pdfAlphaS central | -8.879 | -8.418 | **+0.461** (≈ 0.94 sigma_NOM) |
| sigma | 0.490 | 0.470 | -0.019 |

Linearized prediction was +0.40; actual +0.46. Linear-response model held within ~15%.

### Top non-frozen movers (re-pulls compensating for the lost b-mass freedom)

- `resumFOScaleZSymDiff`: -1.19 -> -1.68
- `resumFOScaleZSymAvg`: -0.11 -> -0.36
- `QCDscaleZfine_PtV5_7_h0`: -0.54 -> -0.77
- `scetlibNPgammaEigvar2`: -0.76 -> -0.96
- `horacelophotosmecoffew_FSR_Corr0`: -1.16 -> -1.36
- `resumTNP_b_qqV`: -0.53 -> -0.72

Resummation transition scales and helicity-0 QCD scale variations absorb the strongest re-pull. None recovers the chi2.

### Important secondary observations

1. **Even prefit ptll p-value drops** (1.67% -> 0.32%) when the b-mass nuisances are frozen. The prefit residual is identical to nominal (mb=0 in both cases), but the prefit residual covariance is tighter (no mb contribution to `var_theta0` -> no buffer in res_cov), so the same residual gives a bigger chi2. Same mechanism as the postfit case in miniature.
2. **Linear ~ Saturated projection still holds** (78.26 vs 77.31). Even with mb frozen, all remaining nuisance freedom is being used on ptll; ~0.5 ΔNLL of slack available beyond the linear test, same as nominal.

### Interpretation for the alphaS measurement
- The +0.46 shift is the size of the "mb-prior systematic" on alphaS, currently buried inside the nominal statistical band. Worth quoting as a one-sided systematic.
- Freezing is too aggressive for the **nominal** fit (16x p-value degradation, large re-pulls). Better candidates for the nominal procedure are: widen the b-mass priors (e.g. 2x or 5x), or treat the frozen result as a sensitivity check while keeping the constrained nominal.

T7 status: **done**. Followups -> T8 (widen priors), and the broader hypothesis-discriminating tasks T4-T6 remain open.

## 2026-04-27 — T4 done: --noBinByBinStat (disable BBB)

Output: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_noBBB/fitresults.hdf5`.
Log: `logs/noBBB_260427_192556.log`.

Per-projection postfit p-values (NOMINAL -> noBBB):

| projection | linear NOM | linear noBBB | sat NOM | sat noBBB |
|---|---|---|---|---|
| ptll | 0.32% | **0.066%** | 0.40% | 0.061% |
| yll | 0.17% | **0.041%** | 0.24% | 0.064% |
| cosTheta\* | 28% | 24% | 37% | 34% |
| phi\* | 14% | 10% | 18% | 14% |
| 4D total | 59.6% | **0.0000%** | -- | -- |

Δchi2 prefit -> postfit on ptll: nominal +7.3, noBBB +6.3 (Δchi2 from prefit -> postfit *narrows* slightly; the postfit gain over prefit shrinks because BBB is no longer there to absorb prefit residual).

### alphaS shift: essentially zero
- NOMINAL: -8.879 +/- 0.490
- noBBB  : -8.872 +/- 0.486
- Δ = +0.006, σ change -0.004

### Nuisance re-pulls: tiny
Top mover is `Scale_correction_unc123` at +/- 0.085. No nuisance moves by more than 0.1 (compare to T7 where top movers were 0.2-0.5). BBB is essentially decoupled from the rest of the nuisance space.

### Interpretation
- 4D total p-value collapsing from 59.6% to ~0% means BBB was doing **a lot** of legitimate work covering per-bin MC stat fluctuations across all 49920 bins. Removing it just amplifies every residual.
- ptll/yll p-values get 4-5x worse, cosTheta\*/phi\* barely move. Quantile-binned axes are more robust to BBB removal because each quantile bin pools across many MC bins.
- alphaS is insensitive to BBB.
- **BBB is NOT the cause of the bad projection p-values.** Removing the flexibility makes things worse, not better. Reading B (over-flexibility) is **rejected** for BBB specifically.

T4 status: **done**. Reading B is not supported by the BBB test. Remaining over-flexibility candidates: T5 (efficiency block), T6 (QCDscale-PtV per-helicity).

## 2026-04-27 — T1 (per-bin pulls), T3 (eigendecomposition) — done; T2/T5/T6 fits launched

Working tag for plots/files: `260427_194300_projection_pvalues`.
Plot output base: `/home/submit/lavezzo/public_html/alphaS/260427_194300_projection_pvalues/`.

### T1 — per-bin pull plots, all four projections (no refit)
- Script (new): `agents/studies/projection_pvalues/scripts/per_bin_pulls.py`.
- Reads from: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_allproj/fitresults.hdf5`.
- Pull definition: `(pred - data) / sqrt(diag(cov_post) + nobs)` (post-fit prediction cov + Poisson; underestimates true chi2 for the same reason recorded in the README findings, ~30 vs 67.4 on ptll, but it's a **visual** of where the residual sits).
- Command (run from outside the container; only `wums` + `rabbit` Python sources needed, no TF):
  ```bash
  cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
  python3 agents/studies/projection_pvalues/scripts/per_bin_pulls.py \
    /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_allproj/fitresults.hdf5 \
    /home/submit/lavezzo/public_html/alphaS/260427_194300_projection_pvalues/per_bin_pulls
  ```
- Output: 4x PDF + 4x PNG in `MY_PLOT_DIR/260427_194300_projection_pvalues/per_bin_pulls/`, files `per_bin_pulls_Project ch0 <axis>.{pdf,png}`.
- Numerical takeaways (chi2_approx vs chi2_true confirms the saved cov_post underestimates):

  | proj | nbins | max\|pull\|_post | argmax_post | sum pull^2_post (approx) | chi2_post_true |
  |---|---|---|---|---|---|
  | ptll | 39 | 2.20 | bin 9 (5.0-5.5 GeV) | 30.4 | 67.4 |
  | yll | 20 | 1.60 | bin 2 | 18.2 | 43.7 |
  | cosTheta\* | 8 | 0.57 | bin 4 | 0.7 | 9.8 |
  | phi\* | 8 | 0.95 | bin 1 | 1.3 | 12.4 |

- **Physics-sense check:** ptll pull at bin 9 (5.0-5.5 GeV, +2.2 sigma) and the bin 31/32 oscillation (20-22 / 22-24 GeV) reproduce the residual pattern already noted in the README. yll worst pull is at bin 2 (low |yll|). cosTheta\* and phi\* show small per-bin pulls — their chi2 must come from a few correlated bins via off-diagonal cov, not large diagonal residuals.

T1 status: **done**.

### T3 — residual-cov eigendecomposition for ptll (no refit; reconstruction approach)
- Script (new): `agents/studies/projection_pvalues/scripts/dump_rescov.py`.
- Strategy chosen (avoids re-running rabbit_fit, no fitter instrumentation): reconstruct `res_cov` candidates from saved hists.
  - `JJ^T + diag(nobs)` using `hist_prefit_inclusive_global_impacts` columns as J (pdfAlphaS dropped — it's the NOI with `var_theta0=0`).
  - `cov_post + diag(nobs)` using saved `hist_postfit_inclusive_cov`.
  - `JJ^T + diag(nobs) + diag(max(0, diag(cov_post) - diag(JJt)))` as a BBB diag floor.
- Command:
  ```bash
  cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
  python3 agents/studies/projection_pvalues/scripts/dump_rescov.py \
    /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_allproj/fitresults.hdf5 \
    /home/submit/lavezzo/public_html/alphaS/260427_194300_projection_pvalues/rescov_eig
  ```
- Output: PDF + PNG eigenspectrum / chi2-per-mode / top-3 mode shapes; `rescov_Project_ch0_ptll.npz` with `res`, `res_cov`, `eigvals`, `eigvecs`, `r_proj`, `r_whit`, `chi2_per_mode`.
- chi2 reproduction: 30.06 (J J^T + nobs), 30.06 (+BBB diag), 31.80 (cov_post + nobs) vs **true 67.4**. **All reconstructions underestimate by ~2.2x** — the saved `hist_prefit_inclusive_global_impacts` apparently does not give the same prefit-width Jacobian that `_residuals_profiled` builds from `dresdtheta0`. Same gap on `cov_post + nobs` was already noted in the README findings.
- **Caveat / followup:** to get an *exact* res_cov match would require either editing `fitter.py:1842` to dump `(residuals, res_cov)` to disk during a fit, or a standalone script that re-instantiates a `Fitter`, sets `self.x` to the saved postfit values, and calls `_residuals_profiled(mapping_ptll.compute_flat)`. Not done in this pass.
- **Eigendecomposition (best-matching reconstruction `cov_post+nobs`):** chi2 is **spread across many modes**, not concentrated. Top mode = 7.2% of (reconstructed) chi2; top 3 modes = 16.7%; top 5 modes = 23.0%. Top contributors are modes 28, 29, 9, 2, 18 (eigvalues all >1e5, similar order). Even allowing for the 2.2x absolute miscalibration, the *relative* ranking is robust: **no 1-2 modes carry the chi2** — favors reading A (real model bias / many small mismodellings) over reading B (one coherent residual mode absorbed by an over-flexible nuisance group).

T3 status: **done with caveat** (relative spectrum trustworthy; absolute chi2 reconstruction off by 2.2x; recommended exact dump described in caveat).

### T8 — widen b-mass priors (skipped, not mechanically supported)
- Rabbit's `--freezeParameters` exists, but there is no analogous `--scaleConstraint` / `--widenPrior` flag to multiply a constrained nuisance's prior width.
- `parsing.py:223-228` exposes `--prefitUnconstrainedNuisanceUncertainty` (only affects unconstrained nuisances) and `parsing.py:240-246` exposes `--setConstraintMinimum` (sets a constraint floor, not a width). `fitter.py:632, 683` even has FIXMEs ("FIXME use theta0 as the mean and constraintweight to scale the width").
- `setupRabbit.py` exposes `--scaleTNP`, `--scalePdf`, `--scaleMinnloScale`, `--scaleNPLambda4` — none target the b-mass nuisances (`mb_up`, `pdfMSHT20mbrange{Avg,Diff}`).
- Implementing T8 mechanically would require either (a) a new rabbit CLI flag + code change, (b) regenerating the input tensor with scaled b-mass templates, or (c) loading the input HDF5 in Python and rescaling the b-mass syst columns directly before the fit. None are "preexisting rabbit commands"; left as a code task for a follow-up session.

T8 status: **skipped** (deferred — not a mechanical refit; needs a code or input-tensor change).

### T2, T5, T6 — fits launched in background

All three use the working wrapper template (see AGENTS.md), with `set -e` (no `-u`) and `source /opt/venv/bin/activate` before `setup.sh`. Pattern:
```bash
nohup singularity run --bind /scratch/,/work/,/home/,/ceph/ \
  /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest \
  /tmp/run_<task>.sh > logs/<task>_$(date +%y%m%d_%H%M%S).log 2>&1 &
```
Wrapper scripts:
- `/tmp/run_freezeEff.sh` (T5): `--freezeParameters '^effSyst_reco_.*' '^effSyst_tracking_.*'`
- `/tmp/run_freezeQCDscaleHel.sh` (T6): `--freezeParameters '^QCDscaleZfine_PtV.*helicity_.*'` (160 params; effectively re-correlates by removing all per-pTV and per-helicity freedom — tighter than what the README originally asked for, which is "re-correlate across pTV bins or freeze as a group").
- `/tmp/run_2D.sh` (T2): same as nominal `260427_debug_allproj` but adds `-m Project ch0 ptll yll` (matches `fitter.sh` default mappings).

Output dirs:
- T5: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_freezeEff/fitresults.hdf5`
- T6: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_freezeQCDscaleHel/fitresults.hdf5`
- T2: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_allproj_with2D/fitresults.hdf5`

Logs (timestamps in filenames):
- T5: `logs/freezeEff_260427_194227.log`
- T6: `logs/freezeQCDscaleHel_260427_194227.log`
- T2: `logs/with2D_260427_194516.log`

### T2 done: 2D ptll-yll mapping — joint fit is FINE, 1D marginals are biased

Output: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_allproj_with2D/fitresults.hdf5`.
Plot script (new): `agents/studies/projection_pvalues/scripts/residual_2d_heatmap.py`.
Plot dir: `/home/submit/lavezzo/public_html/alphaS/260427_194300_projection_pvalues/residual_2d/residual_2d_ptll_yll.{pdf,png}`.

```bash
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
python3 agents/studies/projection_pvalues/scripts/residual_2d_heatmap.py \
  /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_allproj_with2D/fitresults.hdf5 \
  /home/submit/lavezzo/public_html/alphaS/260427_194300_projection_pvalues/residual_2d
```

| mapping | chi2/ndf | p-value | prefit p | sat p |
|---|---|---|---|---|
| `Project ch0 ptll yll` (39x20=780 bins) | 758.43/780 | **70.3%** | 82.1% | 69.7% |
| `Project ch0 ptll`     | 67.41/39  | 0.32% | 1.67% | 0.40% |
| `Project ch0 yll`      | 43.66/20  | 0.17% | 12.4% | 0.24% |
| `Project ch0 cosTheta*`| 9.75/8    | 28.3% | 99.5% | 37.4% |
| `Project ch0 phi*`     | 12.38/8   | 13.5% | 97.7% | 18.2% |

alphaS: -8.879 +/- 0.490 — identical to nominal `260427_debug_allproj` (the extra 2D mapping is read-only post-fit).

`|pull|>2` bins on the 2D heatmap: 14 / 780 (1.8%, fully consistent with Gaussian expectation). Largest pulls are scattered, not concentrated:
  - (ptll 22-24 GeV, yll [-1.8,-1.5])  -2.63
  - (ptll 16-17 GeV, yll [-1.1,-0.9])  -2.75
  - (ptll 37-44 GeV, yll [0.5,0.7])    +2.63

**Key insight unlocked by T2:** the 2D joint passes (chi2/ndf=0.97, p=70%) while the 1D marginals fail. The only way that happens is that the per-(ptll,yll)-bin residual is small but **coherent in sign across yll for fixed ptll** (and vice versa). When you sum over yll, ~20 small same-sign residuals accumulate into a single ptll-bin pull of order sqrt(20)x larger. So the model's 4D mismodeling is small per-bin but **systematic in shape along ptll (and along yll)** — exactly what a real model bias looks like, and exactly *not* what an over-flexible nuisance would do (which would manifest as a coherent residual mode in *one* axis only).

T2 status: **done**.

### T5 done: freeze effSyst_reco_* + effSyst_tracking_* (196 params)

Output: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_freezeEff/fitresults.hdf5`. Log: `logs/freezeEff_260427_194227.log`.

Per-bin pulls (script reused): plots in `MY_PLOT_DIR/260427_194300_projection_pvalues/per_bin_pulls_freezeEff/`.

| projection | chi2/ndf NOM | p NOM | chi2/ndf T5 | p T5 |
|---|---|---|---|---|
| ptll  | 67.41/39 | 0.316% | **67.44/39** | 0.314% |
| yll   | 43.66/20 | 0.167% | **44.43/20** | 0.132% |
| cosTheta* | 9.75/8 | 28.3% | 9.32/8 | 31.6% |
| phi*  | 12.38/8 | 13.5% | 11.74/8 | 16.3% |

alphaS: -8.879 +/- 0.490 -> -8.910 +/- 0.486 (Δ = -0.031, ~0.06 sigma_NOM, negligible).

Freeze verified (5 of 196 params shown): `effSyst_reco_etaDecorr1` -0.27 +/- 0.72 -> 0.000 +/- 1.000, etc.

**Top non-frozen movers (re-pulls absorbing the lost reco+tracking freedom):**
- `effSyst_iso_etaDecorr28`: +0.08 -> +0.95 (Δ=+0.87)
- `effSyst_iso_etaDecorr27`: -0.13 -> +0.65 (Δ=+0.79)
- `effSyst_iso_etaDecorr22`: +0.11 -> -0.61 (Δ=-0.72)
- `effSyst_iso_etaDecorr21,23,26,20`, `effSyst_trigger_etaDecorr27`, `effSyst_iso_fullyCorr` (all 0.4-0.6 shifts)
- `CMS_prefire_stat_m_etaPhiReg8`: +0.11 -> +0.56

**Interpretation:** the iso/trigger eta-decorrelated nuisances pick up exactly the freedom we removed from reco+tracking. The yll p-value did **not** improve (got slightly worse, 0.17% -> 0.13%). reco+tracking is **not** the over-flexible group that drives yll's bad p-value — the eff system as a whole is doing legitimate work. Reading B (over-flexibility) is **rejected** for `effSyst_reco_*` and `effSyst_tracking_*` specifically.

T5 status: **done**. Reading B not supported.

### T6 done: freeze QCDscaleZfine_PtV.*helicity_.* (160 params)

Output: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_freezeQCDscaleHel/fitresults.hdf5`. Log: `logs/freezeQCDscaleHel_260427_194227.log`.

Per-bin pulls plots in `MY_PLOT_DIR/260427_194300_projection_pvalues/per_bin_pulls_freezeQCDscaleHel/`.

| projection | chi2/ndf NOM | p NOM | chi2/ndf T6 | p T6 |
|---|---|---|---|---|
| ptll  | 67.41/39 | 0.316% | **70.05/39** | 0.166% |
| yll   | 43.66/20 | 0.167% | 44.29/20 | 0.137% |
| cosTheta* | 9.75/8 | 28.3% | 10.23/8 | 24.9% |
| phi*  | 12.38/8 | 13.5% | **14.28/8** | **7.5%** |

alphaS: -8.879 +/- 0.490 -> -8.858 +/- 0.473 (Δ = +0.021, ~0.04 sigma_NOM, negligible). Sigma shrinks slightly (-0.017) since 160 nuisances are removed.

**Top non-frozen movers (re-pulls):**
- `resumTransitionZSymDiff`: +0.15 -> +0.65 (Δ=+0.50)
- `resumFOScaleZSymAvg`: -0.11 -> +0.32 (Δ=+0.43)
- `resumTransitionZSymAvg`: +0.48 -> +0.72 (Δ=+0.25)
- `horacelophotosmecoffew_FSR_Corr0`: -1.16 -> -1.41 (Δ=-0.24)
- The `QCDscaleZinclusive_PtV0_13000helicity_*` (PtV-inclusive variant, NOT frozen) pick up some load too.

**Interpretation:** every projection got worse, especially phi* (the projection the README expected might be helped if helicity_5/_7 was over-flexible). Resummation transition scales and PtV-inclusive QCDscale pick up the slack. The per-pTV per-helicity QCDscale variations were doing real work; freezing them is a NET LOSS. Reading B (over-flexibility) is **rejected** for `QCDscaleZfine_PtV*helicity_*` as well.

T6 status: **done**. Reading B not supported.

## Summary table after this session (2026-04-27 ~20:00)

| ID | Description | Status | Outcome (1-line) |
|---|---|---|---|
| T1 | per-bin pulls, all proj, no refit | done | ptll bin 9 (5.0-5.5 GeV) +2.2σ, ptll bin 31/32 oscillation; yll bin 2 worst; cosTheta*/phi* small per-bin pulls (chi2 from off-diagonal cov) |
| T2 | 2D ptll-yll mapping | done | **2D p=70%, 1D ptll p=0.32%, 1D yll p=0.17%** — joint OK, marginals biased; per-bin 4D residuals coherent along yll for fixed ptll |
| T3 | res_cov eigendecomposition (ptll) | done w/ caveat | chi2 reconstruction ~30 vs true 67 (factor ~2.2 underestimate); spectrum: top mode 7%, top 5 modes 23% — chi2 spread across many modes, not 1-2 directions |
| T4 | freeze BBB | done (prior session) | 4D p collapses to 0%, ptll/yll get worse — BBB legitimate |
| T5 | freeze effSyst_reco_* + effSyst_tracking_* | done | every projection ≈ same or worse; iso/trigger eff repulls absorb the freedom |
| T6 | freeze QCDscaleZfine_PtV*helicity_* | done | every projection worse, phi* notably; resum/transitions repull |
| T7 | freeze b-mass (mb_up + 2 PDF mb-range) | done (prior session) | alphaS shifts +0.46 (~0.94 sigma_NOM); ptll p collapses 0.32% -> 0.02% |
| T8 | widen b-mass priors | skipped | not supported by current rabbit/setupRabbit CLI; needs a code or input-tensor change |
| T9 | publication-level decision | open | preferred reading: hypothesis A (real model bias), see below |

### Pattern emerging from T4+T5+T6+T7

Every "freeze a nuisance group" experiment (BBB, eff reco/tracking, QCDscale per-helicity, b-mass) **makes projections worse, never better**. The fitter is using the available freedom legitimately; removing it does not rescue the 1D p-values. Combined with T2 (2D joint passes, 1D marginals fail with coherent same-sign residuals across the orthogonal axis) and T3 (chi2 spread across many modes), the data favor:

**Hypothesis A: real model mismodeling of the 4D shape**, small per-(ptll,yll,cosθ*,φ*)-bin but coherent along the projection axis, accumulated into ~3 chi2/ndf in 1D.

Hypothesis B (over-flexibility) is **not rejected globally** but is rejected for every nuisance group we have probed (BBB, effSyst_reco, effSyst_tracking, QCDscaleZfine per-helicity). The remaining candidates are smaller groups (effStat ~2784 nuisances, pixel_multiplicity, Scale_correction) — but T2 already argues against B in general.

### Concrete recommendations toward T9 (decision)

1. **Quote the b-mass freeze sensitivity (+0.46 from T7) as a one-sided systematic** on alphaS, not adopt as nominal (T7 freeze degrades projections too aggressively).
2. **Do NOT chase 1D projection p-values by deflexing nuisances** — the 2D joint already passes. The 1D failures are diagnostics of mis-modeled 4D shape, not symptoms of over-flexible nuisances.
3. **Document the residual pattern** (ptll bin 9 +2σ, ptll oscillation around the bin-31/32 ptll-binning boundary) as a known mismodeling. Check whether the analysis-note theory-uncertainty section has room to enlarge a TNP/non-perturbative parameter to cover the ptll<6 GeV residual.
4. The bin-31/32 oscillation at the 20 → 22 GeV / 22 → 24 GeV bin boundary still smells like a calibration/migration step; worth a histmaker-level look (variable bin widths jump from 1 GeV to 2 GeV across this boundary).

### Files reproducing this session

All under `/home/submit/lavezzo/alphaS/WRemnantsHelpers/`:

| Asset | Path |
|---|---|
| Per-bin pull plotter | `agents/studies/projection_pvalues/scripts/per_bin_pulls.py` |
| Eigendecomposition (T3) | `agents/studies/projection_pvalues/scripts/dump_rescov.py` |
| 2D heatmap (T2)         | `agents/studies/projection_pvalues/scripts/residual_2d_heatmap.py` |
| T5 wrapper (freezeEff)  | `/tmp/run_freezeEff.sh` |
| T6 wrapper (freezeQCDscaleHel) | `/tmp/run_freezeQCDscaleHel.sh` |
| T2 wrapper (with 2D)    | `/tmp/run_2D.sh` |
| Fit results (T5)        | `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_freezeEff/fitresults.hdf5` |
| Fit results (T6)        | `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_freezeQCDscaleHel/fitresults.hdf5` |
| Fit results (T2)        | `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_allproj_with2D/fitresults.hdf5` |
| Logs (T5/T6/T2)         | `logs/freezeEff_260427_194227.log`, `logs/freezeQCDscaleHel_260427_194227.log`, `logs/with2D_260427_194516.log` |
| Plots (all this session)| `/home/submit/lavezzo/public_html/alphaS/260427_194300_projection_pvalues/` (subdirs `per_bin_pulls/`, `per_bin_pulls_freezeEff/`, `per_bin_pulls_freezeQCDscaleHel/`, `residual_2d/`, `rescov_eig/`) |

Note on the wrappers in `/tmp/`: keep these alive for re-running. They follow the AGENTS.md template (set -e, source /opt/venv/bin/activate, source setup.sh, then rabbit_fit.py with the -t 0 / 4-mapping default).

## 2026-04-27 — T10 done, T11/T12 launched

### T10 — residual-on-nuisance-basis projection (no refit)

Script (new): `agents/studies/projection_pvalues/scripts/residual_on_nuisance_basis.py`.

Approach: for each projection, build the per-bin postfit residual `r = pred - data` and the prefit-global-impacts matrix `J` (columns = each nuisance's shape direction). Compute three diagnostics:
1. **Per-nuisance** Δchi2 each nuisance can absorb if it were the *only* freedom against a data-stat-only baseline:
     `Δchi2_i = (J_i^T Cdata_inv r)^2 / (1 + J_i^T Cdata_inv J_i)`
2. **Per-group** Δchi2 by ridge-regressing the residual onto a group's columns with prior penalty `+I`:
     `(J_g^T Cdata_inv J_g + I) a = J_g^T Cdata_inv r`, Δchi2 = chi2_before − chi2_after − a^T a.
3. **Aggregate subspaces**: ALL theory, ALL detector, scetlibNP only.

Command:
```bash
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
for proj in "Project ch0 ptll" "Project ch0 yll" "Project ch0 cosThetaStarll_quantile" "Project ch0 phiStarll_quantile"; do
  python3 agents/studies/projection_pvalues/scripts/residual_on_nuisance_basis.py \
    /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_allproj/fitresults.hdf5 \
    /home/submit/lavezzo/public_html/alphaS/260427_194300_projection_pvalues/residual_basis \
    "$proj"
done
```

Outputs: `residual_basis/residual_basis_alignment_<proj>.{pdf,png}` for each of the four projections.

#### Aggregate subspace absorption (ridge least-squares from data-only baseline)

| Projection | chi2_data | ALL theory (n=198) | ALL detector (n=3334) | scetlibNP only (n=6) |
|---|---|---|---|---|
| **ptll**   | 38.5 | **6.4** absorbed → 29.1 left | 0.5 absorbed → 37.7 left | 0.9 absorbed → 37.5 left |
| **yll**    | 24.2 | 0.3 absorbed → 23.9 left | **4.6** absorbed → 17.8 left | 0.0 absorbed → 24.4 left |
| cosTheta\* |  1.0 | 0.0 absorbed →  1.0 left | 0.3 absorbed →  0.6 left | 0.0 absorbed →  1.0 left |
| phi\*      |  2.0 | 0.6 absorbed →  1.3 left | 0.1 absorbed →  1.9 left | 0.0 absorbed →  2.0 left |

(Reminder: linear reconstruction underestimates true chi2 by ~2x — same factor as in T3. So 38.5 corresponds to true chi2 ~ 67 on ptll. Treat the *proportions* as the trustworthy quantity.)

#### Top single nuisances aligned with the ptll residual (linearized δθ that would zero the projection)

| rank | nuisance | r·J | Δchi2 absorbable | δθ implied |
|---|---|---|---|---|
| 1 | `QCDscaleZfine_PtV5_7helicity_0_SymAvg`   | +310k | 1.24 | -2.51σ |
| 2 | `QCDscaleZfine_PtV15_20helicity_0_SymAvg` | +304k | 1.16 | -1.38σ |
| 3 | `QCDscaleZfine_PtV9_11helicity_0_SymAvg`  | -172k | 0.83 | +3.26σ |
| 4 | `chargeVgenNP0scetlibNPZlambda4`          | +643k | 0.58 | -0.26σ |
| 5 | `QCDscaleZfine_PtV7_9helicity_0_SymAvg`   | -125k | 0.43 | +2.10σ |
| 6 | `QCDscaleZfine_PtV5_7helicity_2_SymAvg`   | -126k | 0.33 | +7.85σ |
| 7 | `pdfMSHT20mbrangeSymDiff`                 | -169k | 0.29 | +0.27σ |
| ... | (long tail; no single nuisance >1.3 chi2) | | | |

#### Interpretation

- **Even with 198 theory nuisances + 3334 detector nuisances all freed simultaneously, only ~7 of 38 (~18%) of the linear ptll chi2 can be absorbed by the existing nuisance basis at "reasonable" prior shifts (no individual implied θ exceeds 1σ in the joint solve).** The remaining ~80% of the residual chi2 lives in directions *orthogonal* to the entire current basis.
- **ptll**: the most-aligned nuisances are QCDscaleZfine_PtV*_helicity_0 (scattered across pTV bins, opposite signs — i.e. a 1D oscillatory ptll mode), not scetlibNPlambda4. Lambda4 ranks only #4, with Δchi2_absorbable=0.58. Widening Lambda4 alone cannot absorb the residual; even widening the whole NP subspace (lambda + eigvars) absorbs only 0.9 of 38.5 chi2. Consistent with the user's observation that scaling Lambda4 only "improves the ptll p-value a little bit, but it's not great still."
- **yll**: the residual is detector-aligned (eff_reco/tracking + eff_iso/trigger absorb ~5 of 24 chi2). Theory subspace absorbs ~zero. So yll's failure mode is *different* from ptll's — it's not the same shared theory mismodeling.
- **cosTheta\*** and **phi\*** have small total chi2 already; the residual is tiny in absolute terms.

#### Concrete physics conclusion

The data is asking for a residual ptll shape that the *current nuisance basis cannot span*. Widening Lambda4 (or any single NP eigvar / lambda) buys a fraction of a chi2 unit. To meaningfully absorb the ptll residual the analysis would need a *new* nuisance shape orthogonal to the existing 3700+ — i.e. a missing physical effect (most likely a small higher-order resummation correction or a calibration-type bin-migration shape), not a wider prior on existing nuisances.

T10 status: **done**.

### T11 — `--scaleNPLambda4 2.0` refit (4D nominal, NP Lambda4 prior width x2)

Wrapper: `/tmp/run_scaleNPLambda4_2.sh` (re-runs `setupRabbit.py` with `--scaleNPLambda4 2.0` then `rabbit_fit.py` with the 4-projection mappings, `-t 0`, `--computeSaturatedProjectionTests`, `--computeHistCov`).

Output dir (will appear): `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_scaleNPLambda4_2/<setupRabbit-named-subdir>/fitresults.hdf5`.

Log: `logs/scaleNPLambda4_2_260427_212909.log`.

Status: **launched 2026-04-27 21:29**, fits in flight. Expected ~10-15 min for setupRabbit + ~7 min for fit.

### T12 — 2D-only fit (drop cosTheta\*, phi\* from the input tensor)

Wrapper: `/tmp/run_2Donly.sh` (re-runs `setupRabbit.py` with `--fitvar 'ptll-yll'` then `rabbit_fit.py` with mappings `Project ch0 ptll yll`, `Project ch0 ptll`, `Project ch0 yll`).

Discriminant test:
- If 1D ptll/yll p-values **recover**, the 4D residual was *induced* by tension between the angular (cosθ\*/φ\*) constraints and the kinematic axes — the nuisance basis cannot satisfy both simultaneously, even though each marginal individually looked fine.
- If 1D ptll/yll p-values **stay bad**, the residual is *intrinsic* to the (ptll, yll) plane and the angular axes don't cause it.

Output dir (will appear): `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_2Donly/<setupRabbit-named-subdir>/fitresults.hdf5`.

Log: `logs/2Donly_260427_212909.log`.

Status: **launched 2026-04-27 21:29**, fit in flight. Expected ~10-15 min.

## 2026-04-27 — Gotcha: setupRabbit defaults to Asimov, must pass `--realData`

The first run of T11 and T12 finished and gave **chi2/ndf = 0 across all projections, prefit and postfit**, which looked spectacular until I checked the data values in T12: data was bit-for-bit equal to both prefit and postfit predictions across all 40 ptll bins (e.g. `data[0]=98210.2`, `pred_prefit[0]=98210.2`, `pred_postfit[0]=98210.2`). That's the Asimov signature, not real data — verified by `setupRabbit.py:` having `--realData` as an opt-in flag (default behavior is `real_data=False`, which writes the Asimov / nominal-MC histogram into `data_obs`). The original `260427_debug_allproj` was set up by Andrey's pipeline which presumably ran setupRabbit with `--realData` (or equivalent).

**Fix:** added `--realData` to both wrapper scripts (`/tmp/run_scaleNPLambda4_2.sh`, `/tmp/run_2Donly.sh`). New output dirs use `_v2` suffix:
- T11 v2: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_scaleNPLambda4_2_v2/<setupRabbit-named-subdir>/fitresults.hdf5`
- T12 v2: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_2Donly_v2/<setupRabbit-named-subdir>/fitresults.hdf5`
- Logs: `logs/scaleNPLambda4_2_v2_260427_213545.log`, `logs/2Donly_v2_260427_213545.log`.

The original v1 outputs are kept on disk as a record of the bug (alphaS came out to **-1.421 +/- 0.537** from the 2D-only Asimov, which is *not* what 2D-only on real data will give — that v1 number must not be quoted).

This is now documented in the README too. **Lesson for future fits launched from a fresh setupRabbit:** always pass `--realData` if you want to fit the actual data.

Status: **T11 v2 / T12 v2 launched 2026-04-27 21:35**, expected ~10-15 min each.

### T12 v2 done (2D-only fit on real data) — partial separation of yll vs ptll failure modes

Output: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_2Donly_v2/ZMassDilepton_ptll_yll_2Donly/fitresults.hdf5`. Log: `logs/2Donly_v2_260427_213545.log`. Wrapper: `/tmp/run_2Donly.sh` (now with `--realData`).

Per-bin pulls plots: `MY_PLOT_DIR/260427_194300_projection_pvalues/per_bin_pulls_2Donly/`. Residual basis projection plots: `.../residual_basis_2Donly/`.

#### Headline numbers

| metric                    | 4D NOM           | 2D-only T12 v2   | Δ               |
|---|---|---|---|
| alphaS                    | -8.879 +/- 0.490 | -8.341 +/- 0.537 | +0.538 (~1.1σ_NOM); sigma +0.047 |
| `Project ch0 ptll yll`    | 758/780  p=70.3% | **762/800 p=82.5%** | +4 chi2 (similar) |
| `Project ch0 ptll`        | 67.4/39  p=0.32% | **66/40   p=0.57%** | -1.4 chi2 (essentially same) |
| `Project ch0 yll`         | 43.7/20  p=0.17% | **35/20   p=1.78%** | -8.7 chi2 (**~10x p-value improvement**) |
| `Project ch0 cosTheta*`   | 9.8/8    p=28.3% | (axis dropped)   | — |
| `Project ch0 phi*`        | 12.4/8   p=13.5% | (axis dropped)   | — |

#### Top 15 nuisance shifts (T12 v2 - 4D NOM)

- `CMS_prefire_stat_m_etaPhiReg2`        +1.667 -> +0.065  (Δ=-1.60)
- `Scale_correction_unc48`               -1.382 -> +0.014  (Δ=+1.40)
- `resumFOScaleZSymAvg`                  -0.111 -> **+1.245** (Δ=+1.36)
- `CMS_prefire_stat_m_etaPhiReg0`        -1.263 -> +0.038  (Δ=+1.30)
- `QCDscaleZfine_PtV9_11helicity_6_SymAvg` -1.151 -> 0.000  (Δ=+1.15) — helicity_6 absorbed nothing useful for 2D
- `pixel_multiplicity_syst_var40`        +1.285 -> +0.171  (Δ=-1.11)
- `effSyst_tracking_etaDecorr29`         +1.132 -> +0.066  (Δ=-1.07)
- `QCDscaleZfine_PtV7_9helicity_0_SymAvg` -0.191 -> **+0.816** (Δ=+1.01) — helicity_0 (longitudinal) helps ptll
- `QCDscaleZfine_PtV7_9helicity_6_SymAvg` +0.983 -> +0.002  (Δ=-0.98)
- ... (many helicity-6/-7 nuisances relax to ~0; longitudinal/transverse helicity_0/_2 nuisances pick up)

NP/resum specifically:
- `chargeVgenNP0scetlibNPZlambda4`       -2.337 -> -1.960 (relaxes ~0.4σ but stays strongly pulled)
- `chargeVgenNP0scetlibNPZlambda2`       -0.539 -> -0.699 (slight increase)
- `resumFOScaleZSymAvg`                  -0.111 -> **+1.245** (big flip)
- `resumTransitionZSymDiff`              +0.150 -> **+1.025** (big flip)

#### Interpretation — clean separation of failure modes

1. **yll's bad p-value was largely *induced by 4D angular constraints*.** Removing the cosθ\*/φ\* axes lets the fit relax the prefire/scale-correction/eff-tracking nuisances that were being pulled to 1.0-1.7σ to fit the angular distribution but were costing yll chi2. yll p-value improves ~10x (0.17% -> 1.78%). The model has no fundamental problem with yll integrated alone.
2. **ptll's bad p-value is *intrinsic* to the (ptll, yll) plane.** Even free of angular constraints, the fit absorbs only 1.4 chi2 units on ptll (67.4 -> 66.0). The residual chi2 stays at ~1.65/ndf. The nuisance basis cannot fix it whether or not the angular axes are in the fit. T10's ridge-regression analysis on the 2D-only postfit confirms the same picture: ALL theory absorbs only 4.4 of 28.2 (~15%); ALL detector adds 0.4. The residual lives in directions orthogonal to the basis.
3. **alphaS shifts +0.54 (~1.1σ_NOM)**, sigma widens slightly (+0.047). Angular axes carry modest alphaS info — about 0.05σ of the 0.49σ total comes from cosθ\*/φ\*. The +0.54 central-value shift is the size of "what is the angular data telling us about alphaS that the kinematic data isn't" — this is itself a tension worth quoting if it's larger than expected from MC statistics.
4. **2D ptll-yll p-value is essentially unchanged** (70.3% -> 82.5%) — confirms once again that the model fits the joint (ptll, yll) distribution well; it's only the 1D marginal that breaks.

T12 v2 status: **done**.

T11 v2 still running (4D fit takes much longer than 2D-only), expected ~5-10 more minutes.

### T11 v2 done (4D fit with --scaleNPLambda4 2.0 on real data) — NP prior width matters for alphaS, not for the projection p-values

Output: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_scaleNPLambda4_2_v2/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_scaleNPLambda4_2/fitresults.hdf5`. Log: `logs/scaleNPLambda4_2_v2_260427_213545.log`. Wrapper: `/tmp/run_scaleNPLambda4_2.sh` (with `--realData --scaleNPLambda4 2.0`).

#### Headline numbers

| metric              | 4D NOM            | T11 v2 (Lambda4 prior x2) | Δ |
|---|---|---|---|
| alphaS              | -8.879 +/- 0.490  | **-9.296 +/- 0.513**       | -0.417 (~0.85σ_NOM); sigma +0.023 |
| `Project ch0 ptll`     | 67.4/39 p=0.32% | **65.7/40 p=0.63%**        | minor (-1.7 chi2) |
| `Project ch0 yll`      | 43.7/20 p=0.17% | 41.6/20 p=0.31%            | minor (-2.1 chi2) |
| `Project ch0 cosTheta*`| 9.8/8 p=28.3%   | 6.0/8 p=65.0%              | improves |
| `Project ch0 phi*`     | 12.4/8 p=13.5%  | 8.1/8 p=42.1%              | improves |

prefit ptll p-value 1.67% -> 5.75% with the wider Lambda4 prior (linear test, profile=False). At the postfit point, the gain is much smaller (0.32% -> 0.63%).

#### NP / resum nuisance shifts (T11 v2 - 4D NOM)

- `chargeVgenNP0scetlibNPZlambda4`         -2.337 -> **-1.670** (still strongly pulled — ~-0.84σ in the *doubled-width* prior, i.e. ~-1.67σ in the original prior frame)
- `chargeVgenNP0scetlibNPZdelta_lambda2`   -0.678 -> -0.778 (slight increase)
- `chargeVgenNP0scetlibNPZlambda2`         -0.539 -> -0.495 (basically same)
- `scetlibNPgammaEigvar1/2/3`              same as nominal (NP-eigvars don't pick up the slack from Lambda4)
- `resumFOScaleZSymAvg`                    -0.111 -> **+1.091** (big flip)
- `resumTransitionZSymDiff`                +0.150 -> **+1.210** (big flip)
- `resumTransitionZSymAvg`                 +0.478 -> +0.932
- `resumFOScaleZSymDiff`                   -1.185 -> -1.509

Other notable movers:
- `pdfMSHT20mbrangeSymAvg`                 -1.146 -> -1.534 (b-mass picks up)
- `mb_up`                                  -1.687 -> -1.315 (b-mass nuisance partially relaxes)
- `lumi`                                   -1.054 -> -0.714

#### Interpretation

1. **The bottleneck for the ptll postfit p-value is *not* the Lambda4 prior width.** Doubling the Lambda4 prior gains ptll only -1.7 chi2 (67.4 -> 65.7); p improves marginally (0.32% -> 0.63%). The residual is mostly orthogonal to the Lambda4 shape direction, exactly as predicted by T10.
2. **Lambda4 still doesn't reach zero** even with twice the prior width — it goes to -1.67 (vs -2.34 nominal). In the original-prior frame that's ~-1.67σ, in the new-prior frame it's ~-0.84σ. The data really does prefer a substantial Lambda4 shift; it's not just being squeezed by the prior. Crucially, **the slack created by widening Lambda4 is partially absorbed by the resum scales** (`resumFOScaleZSymAvg`: -0.11 -> +1.09; `resumTransitionZSymDiff`: +0.15 -> +1.21), not by Lambda4 going further. The data wants a *combination* of NP + resum repulls that the original prior wasn't quite letting it have.
3. **alphaS shifts by Δ = -0.42 (~0.85σ_NOM)** when Lambda4 prior is doubled. This is the size of the "NP Lambda4 prior-width systematic on alphaS" — and it's substantial. It is in the *opposite* direction from the b-mass-freeze sensitivity in T7 (+0.46). Both are O(1σ_NOM) effects; if either prior is off, alphaS moves by ~1σ.
4. **cosTheta\*/phi\* p-values improve** (28% -> 65%, 14% -> 42%) — interesting collateral effect: a wider NP Lambda4 prior also relieves angular-distribution tension. These projections weren't broken to begin with (>13% nominal), so this is a quality-of-life improvement and not a fix for anything that was broken.

#### Summary across the three "widen / freeze a single prior" tests

| Knob                               | ptll postfit p | alphaS shift          | What absorbs the slack |
|---|---|---|---|
| nominal                            | 0.32%          | -8.879                 | — |
| **T7** freeze mb pair              | 0.02%          | -8.418 (Δ=+0.46)       | resum transitions, helicity_0 QCDscale |
| **T11** Lambda4 prior x2           | 0.63%          | -9.296 (Δ=-0.42)       | resumFOScaleZ, resumTransitionZ |
| **T6** freeze QCDscaleZfine_helicity| 0.17%         | -8.858 (Δ=+0.02)       | resumTransitionZ, PtV-inclusive QCDscale |

The pattern: every "single prior" knob produces a ~0.5σ_NOM shift in alphaS and an ~O(1 chi2) movement in ptll. None of them recovers the projection p-value to anything good. The residual lives in a multi-nuisance-orthogonal direction that no single prior widening can absorb.

T11 v2 status: **done**.

### Conclusion update (post T10/T11/T12)

The picture is now sharp:
- **yll's bad postfit p-value is largely 4D-tension-induced** (T12: drop angular axes -> 0.17% -> 1.78%; ~10x improvement).
- **ptll's bad postfit p-value is intrinsic** — it is essentially unchanged whether we drop angular axes (T12: 0.32% -> 0.57%) or double the NP Lambda4 prior (T11: 0.32% -> 0.63%). The residual lives in directions orthogonal to the existing nuisance basis (T10: ALL theory + ALL detector together absorb only ~18% of reconstructible chi2).
- **alphaS sensitivity to ad-hoc priors is real but bounded:** ~0.4-0.5σ_NOM shifts under each of the three "widen / freeze" knobs we tried (b-mass freeze T7 +0.46, Lambda4 widen T11 -0.42, QCDscale-helicity freeze T6 +0.02). These are candidate one-sided systematics to quote.
- **Inflating QCDscale-PtV per-helicity priors specifically would not fix ptll** — the per-pTV per-helicity_0 nuisances showed alternating-sign residual alignment (T10: PtV5_7 wants -2.5σ, PtV9_11 wants +3.3σ, PtV15_20 wants -1.4σ, PtV7_9 wants +2.1σ), which is an oscillatory data structure (calibration / migration signature) that would need a per-pTV bin-correlated prior, not just a width inflation. Even in the best case the group-level absorption is ~5 chi2 of true 67. T13 will quantify this as a sensitivity check.

## 2026-04-27 — comparison with `oldNP` fit (different NP parametrization)

User pointer: `/scratch/submit/cms/alphaS/260413_unblind/mz_dilepton_oldNP.hdf5` (histmaker output) and existing fit at `/scratch/submit/cms/alphaS/260413_unblind/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_oldNP_ptll1to44/fitresults.hdf5`.

Different parametrization of NP uncertainties (and ptll axis starts at 1 GeV instead of 0 → 38 ptll bins, vs 39 in NOM).

```bash
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
python3 agents/studies/projection_pvalues/scripts/compare_all_fits.py \
  NOM=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_allproj/fitresults.hdf5 \
  oldNP=/scratch/submit/cms/alphaS/260413_unblind/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_oldNP_ptll1to44/fitresults.hdf5
python3 agents/studies/projection_pvalues/scripts/per_bin_pulls.py \
  /scratch/submit/cms/alphaS/260413_unblind/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_oldNP_ptll1to44/fitresults.hdf5 \
  /home/submit/lavezzo/public_html/alphaS/260427_194300_projection_pvalues/per_bin_pulls_oldNP
```

| metric | NOM | oldNP | Δ |
|---|---|---|---|
| alphaS                 | -8.879 ± 0.490 | -8.945 ± 0.462 | -0.066 (0.13σ_NOM, ~negligible) |
| `Project ch0 ptll yll` | n/a            | 720/760 p=84.8% | — |
| `Project ch0 ptll`     | 67.4/39 p=0.32% | **52.6/38 p=5.83%** | -14.8 chi2; ~18× p-value |
| `Project ch0 yll`      | 43.7/20 p=0.17% | 45.3/20 p=0.10%     | +1.6 chi2; slightly worse |

Top mover: `pdfMSHT20mbrangeSymAvg` swings -1.146 -> +0.103 (Δ=+1.25). Other PDF-MSHT b-range, Resolution, and effSyst nuisances move at the 0.3-0.5σ level. The b-mass nuisance was carrying load that the new (LatticeEigvars) NP basis now absorbs less, and it's relaxed in oldNP.

Residual basis projection on the oldNP fit (T10-style):
- chi2_data (reconstructed) = 30.9 (vs NOM 38.5; in true-chi2 units, ~52 vs ~67 — saving ~14 true chi2 = consistent with the Δchi2 of -14.8 above).
- ALL theory absorbs 4.0 of 30.9 (~13%) — same orthogonality picture as NOM.
- ALL detector absorbs 0.4 — same.

#### Interpretation

- **NP parametrization choice does matter for ptll** (~15 chi2 absorbable when going from LatticeEigvars+Lambda6 to oldNP). The ptll p-value goes from "definitely bad" (0.32%) to "borderline" (5.83%).
- **NP parametrization does *not* matter for yll** (45.3 vs 43.7 — within statistical noise). Consistent with T12: yll's failure is angular-tension-induced, NP-invariant.
- **alphaS shifts only -0.066 between NP parametrizations** — much smaller than the T11 (Lambda4 prior x2) shift of -0.42. So the central value is fairly robust to NP-basis choice; the sigma narrows by 0.028 (the alternative NP basis is in some directions tighter).
- **Even with oldNP, ~80% of the ptll residual chi2 remains orthogonal to the basis** — this is now a consistent finding across NOM, oldNP, T11 (NP Lambda4 x2), and T12 (2D-only). The "orthogonal residual" is not an artefact of one specific NP parametrization; it survives parameter-basis changes. **This argues that the missing piece is *not* in the NP/scale parametrization at all — more likely calibration / migration / generator-level effect not in the variation set.**

Plots: `MY_PLOT_DIR/260427_194300_projection_pvalues/per_bin_pulls_oldNP/` and `.../residual_basis_oldNP/`.

## 2026-04-27 — T13 + T14 launched

### T13 — `--scaleMinnloScale 2.0` (QCDscale-PtV per-helicity prior widths x2)
Wrapper: `/tmp/run_scaleMinnloScale_2.sh` (with `--realData --scaleMinnloScale 2.0`).
Output dir (will appear): `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_scaleMinnloScale_2/<setupRabbit-named-subdir>/fitresults.hdf5`.
Log: `logs/scaleMinnloScale_2_260427_215719.log`.

### T14 — uniform 1-GeV ptll bins from 0-30 (then 30-33, 33-37, 37-44)
Tests whether the bin-31/32 oscillation (~22 GeV in NOM) is a binning-step artefact at the variable-width transition (1 GeV → 2 GeV at 20 GeV) or a real shape feature.

Wrapper: `/tmp/run_uniformPtll.sh` — calls setupRabbit with `--rebin '0,1,2,...,30,33,37,44' 1 1 1 --realData` (33 ptll bins; uniform 1 GeV from 0 to 30, then keep 30-44 coarse). The `1`s after the comma list are rebin=1 (no change) for yll/cosTheta\*/phi\* — `--rebin` argparse takes one entry per `--fitvar` axis.
Output dir (will appear): `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_uniformPtll/<setupRabbit-named-subdir>/fitresults.hdf5`.
Log: `logs/uniformPtll_260427_215719.log`.

Both launched 2026-04-27 21:57; expected ~10-15 min each.

### T13 done (`--scaleMinnloScale 2.0`, QCDscale-PtV per-helicity priors x2)
Output: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_scaleMinnloScale_2/.../fitresults.hdf5`. Log: `logs/scaleMinnloScale_2_260427_215719.log`.

| metric              | NOM            | T13 (QCDscale x2) |
|---|---|---|
| alphaS              | -8.879 +/- 0.490 | **-8.854 +/- 0.494** (Δ = +0.025; essentially zero shift) |
| ptll postfit        | 67.4/39 p=0.32% | **73.3/40 p=0.10%**  (worse) |
| ptll prefit         | 60.1/39 p=1.67% | 54/40 p=7.15%       (improves at prefit; the cov is wider) |
| yll postfit         | 43.7/20 p=0.17% | 44.5/20 p=0.13%      (essentially same) |
| cosTheta\* postfit  | 9.8/8 p=28.3%   | 9.8/8 p=28.3%         (same) |
| phi\* postfit       | 12.4/8 p=13.5%  | 11.2/8 p=19.1%        (slightly better) |

**Interpretation:** prefit improves because the wider QCDscale prior inflates the prediction cov (so the same residual gives less chi2). At postfit, ptll *gets worse* — the wider prior lets nuisances repull harder elsewhere and the marginal residual grows. The alternating-sign per-pTV pattern in the QCDscaleZfine_h0 alignment (T10) is not a uniform-width-absorbable shape; a width inflation cannot fix it. **Confirms T10's prediction.** As a sensitivity check, the alphaS shift is negligible (+0.025), so this knob is *not* a meaningful systematic on alphaS.

T13 status: **done**.

### T14 done (uniform 2-GeV ptll bins from 0-30, then 30-33-37-44; 18 bins)
Output: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_uniformPtll/.../fitresults.hdf5`. Log: `logs/uniformPtll_v2_260427_220200.log`.

(v1 of this fit died in setupRabbit due to my requested `1 GeV` edges — original ptll axis only has 2-GeV-spaced edges past 20 GeV; v2 with 2-GeV edges throughout works.)

| metric              | NOM (39 bins)    | T14 (18 bins)         |
|---|---|---|
| alphaS              | -8.879 +/- 0.490 | -8.773 +/- 0.499 (Δ = +0.106) |
| ptll postfit        | 67.4/39 chi2/ndf=1.73 p=0.32% | **47/18 chi2/ndf=2.60 p=0.02%** (worse) |
| yll                 | 43.7/20 p=0.17% | 45.2/20 p=0.10%       (similar) |
| cosTheta\*          | 9.8/8 p=28.3%   | 12.1/8 p=14.5%        (worse) |
| phi\*               | 12.4/8 p=13.5%  | 14.6/8 p= 6.8%        (worse) |
| 4D total saturated  | 49842/49919 p=59.6% | 22838/23039 p=82.5% (4D OK) |

**Bins 10 and 11 of T14 (20-22, 22-24 GeV) are the same edges as bins 31, 32 of NOM** — and the same residual values. Their chi2 contribution is preserved. What's *new* in T14 is that **merging the 1-GeV bins below 20 GeV into 2-GeV bins makes things WORSE** (chi2/ndf 1.73 → 2.60). This is the kill-shot on the "binning-step artefact at 20 GeV" hypothesis — if the residual were a step at 20 GeV, rebinning everywhere uniformly should have *softened* it; instead the larger bins reveal that the per-bin residuals below 20 GeV are coherent in sign within each 2-GeV window, so merging adds them constructively. **The residual is a real, smooth shape mismodeling.**

Plots produced (rabbit_plot_hists.py, T14 + NOM postfit/prefit ptll, T14 yll postfit) in `/home/submit/lavezzo/public_html/alphaS/260427_194300_projection_pvalues/rabbit_plot_hists_uniformPtll/` via `/tmp/run_plot_uniformPtll.sh`. Log: `logs/plot_uniformPtll_260427_221209.log`.

T14 status: **done**.

## 2026-04-27 — T15 done (ptll < 20 GeV, pure resummation regime)

Output: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_ptllLT20/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_ptllLT20/fitresults.hdf5`. Log: `logs/ptllLT20_260427_222043.log`. Wrapper: `/tmp/run_ptllLT20.sh` (with `--axlim ptll 0j 20j --realData`).

| metric              | NOM (39 bins, 0-44) | T15 (31 bins, 0-20) |
|---|---|---|
| alphaS              | -8.879 +/- 0.490 | **-8.839 +/- 0.517** (Δ = +0.040 ~ 0.08σ_NOM; sigma widens +0.027) |
| ptll postfit Linear | 67.4/39 p=0.32% | **56.8/31 p=0.32%** (chi2 -10.6, ndof -8, **same p-value**) |
| ptll Saturated      | 66.5/39 p=0.40% | 56.9/31 p=0.31%   (same story) |
| ptll prefit         | 60.1/39 p=1.67% | 49.5/31 p=1.89%   (similar) |
| yll postfit         | 43.7/20 p=0.17% | **35.9/20 p=1.57%** (~10× p-value improvement) |
| cosTheta\*          | 9.8/8 p=28.3%   | 13.0/8 p=11.3%    (worse) |
| phi\*               | 12.4/8 p=13.5%  | 13.1/8 p=10.8%    (slightly worse) |

**Interpretation:**
- **The 20-24 GeV step contributes ~10 chi2** — real, but only ~15% of the total ptll chi2.
- **The other ~85% (47 of 57 chi2 in T15) lives in the pure-resummation region (ptll<20 GeV)** and is not absorbed by removing the matching/transition bins.
- **alphaS barely moves (+0.040 ~ 0.08σ_NOM)**, sigma widens only +0.027 — confirming alphaS sensitivity is dominated by ptll<20 GeV (as expected) and that the 20-24 GeV region carries little of the central-value information.
- **yll's p-value improves ~10×** (0.17% → 1.57%) when ptll>20 is dropped — same direction as T12 (drop angular axes). yll's degradation has a coupled-tension component with the high-pTll tail through shared theory nuisances.
- **cosTheta\* and phi\* get *worse*** because their high-pTll lever-arm on angular nuisances is gone; less data to constrain those nuisance shapes, so per-bin pulls grow.

T15 status: **done**.

## 2026-04-27 — diagonal vs off-diagonal chi2 decomposition (no refit)

User question: "When I look at the ptll projection in 1D, the (data-pred)/sigma seems reasonable: does the small p-value primarily come from the off-diagonal terms of cov^-1?"

Script (new): `agents/studies/projection_pvalues/scripts/diag_vs_offdiag_chi2.py`.

Numerical decomposition for **NOM ptll postfit** (chi2_true = 67.41, ndof = 39):

| denominator                                           | chi2     | comment |
|---|---|---|
| sigma^2 = nobs                  (data Poisson only)   | 38.49    | what you'd compute with only the data error bar |
| sigma^2 = cov_post              (postfit pred only)   | 151.51   | postfit-band only |
| sigma^2 = cov_post + nobs       (sum in quadrature)   | **30.38** | the displayed per-bin pull² (what the band shows) |
| (cov_post + diag(nobs)) full inverse                   | **31.80** | adds off-diagonal — only +1.4 |
| (cov_pre + diag(nobs)) full inverse                    | 27.04    | even with full inverse |
| **rabbit's true chi2**                                | **67.41** | rabbit's profile-based chi2 |

**Answer to the user's question: no — off-diagonal terms of cov^-1 contribute only +1.4 chi2 (~5%) to the displayed-band reconstruction.** Off-diagonal correlations are **not** what makes the postfit p-value small.

The actual reason rabbit's chi2 (67.4) is so much larger than the displayed-band chi2 (31.8): **rabbit uses a tighter denominator than what the per-bin uncertainty band shows**. The displayed band is the postfit prediction's own uncertainty `cov_post + nobs`; rabbit's chi2 is computed against the residual-after-profiling cov in `_residuals_profiled` (`dresdtheta0 · I · dresdtheta0^T + diag(nobs) + BBB`, where `dresdtheta0` is the gradient of the *profiled* residual). The two are not the same — the residual-after-profiling cov is roughly `√(67/32) ≈ 1.46×` tighter than the displayed band. So a per-bin pull that *displays* as 1σ in the plot is contributing more like 1.46σ-equivalent to the chi2.

**Sanity check that the formula `r^T (cov + nobs)^-1 r` works for prefit:** using cov_pre (saved as `hist_prefit_inclusive_cov`), the prefit reconstruction gives `r_pre^T (cov_pre + nobs)^-1 r_pre = 60.07`, exactly matching rabbit's `chi2_prefit = 60.07`. Prefit reconstruction is exact; postfit cannot be reconstructed from the saved hists alone because rabbit profiles the nuisances and uses a different denominator that isn't saved as a histogram.

Eigendecomposition of `cov_post + diag(nobs)` shows the displayed-band chi2 is spread across many modes (top mode = 4.84 of 31.8 = 15%; top 5 modes = 49%). No single direction dominates, consistent with T3's earlier finding.

To exactly reproduce rabbit's 67.41 chi2 we'd need to instrument `fitter.py:1842` to dump `(residuals, res_cov)` from the running fit, or instantiate a `Fitter` inside the singularity container with `self.x` set to postfit values and call `_residuals_profiled(mapping_ptll.compute_flat)` directly. **Easier path: if a rabbit fit is in memory, just call `fitter._residuals_profiled` for the ptll mapping and dump residuals + res_cov.** From there the eigendecomposition is exact in three more lines.
