# Projection p-values study

## Study question
Why are the per-projection (1D) post-fit p-values from the 4D rabbit fit
(ptll x yll x cosThetaStarll_quantile x phiStarll_quantile, ~50k bins) so bad
when the 4D total saturated chi2 looks fine, and is this a reason to worry
about the alphaS measurement?

Reference fit results inspected:
- `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug/fitresults.hdf5` (single mapping `Project ch0 ptll`)
- `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_allproj/fitresults.hdf5` (four projection mappings)

## Guiding questions
- Is the bad p-value an artefact of how the chi2 / covariance is constructed, or a real model/data discrepancy?
- Are NOIs (alphaS) protected from contributing to the projection chi2? (No, only protected in the 4D saturated test — see findings.)
- Is blinding affecting the projection chi2? (No, chi2 is blinding-invariant.)
- Are the nuisances being pulled in a way that causes the small p-values, or do the small p-values exist already at prefit?
- Which nuisance sectors drive each projection's degradation (theory vs detector)?
- Is the issue over-flexible nuisances absorbing 4D structure at the cost of 1D marginals, or a real model bias revealed by the data precision?
- How much does the alphaS measurement depend on ad-hoc nuisance priors (in particular the b-mass pair)?

## Current understanding (summary of findings as of 2026-04-27)

### Machinery (verified in code)
- chi2 in rabbit uses `solve(res_cov, res)` i.e. C^-1 r — confirmed at [`fitter.py:1866`](../../../../main/WRemnants/rabbit/rabbit/fitter.py#L1866).
- The covariance saved as `hist_postfit_inclusive_cov` (and plotted by `rabbit_plot_cov.py`) is the post-fit *prediction* cov from `dexpdx · self.cov · dexpdx^T` (+ BBB) — see [`fitter.py:1042-1080`](../../../../main/WRemnants/rabbit/rabbit/fitter.py#L1042-L1080). It is **not** the residual cov used in chi2.
- chi2 actually uses the residual cov from `_residuals_profiled`: prefit-width nuisance term + data-stat term + BBB — see [`fitter.py:1787-1842`](../../../../main/WRemnants/rabbit/rabbit/fitter.py#L1787-L1842).
- For NOIs, `var_theta0 = 0` ([`fitter.py:327-331`](../../../../main/WRemnants/rabbit/rabbit/fitter.py#L327-L331)) so they contribute no buffer to res_cov. ndf for projection chi2 is just nbins; NOIs are subtracted from ndf only in the 4D saturated test ([`rabbit_fit.py:328-330`](../../../../main/WRemnants/rabbit/bin/rabbit_fit.py#L328-L330)).
- Blinding adds a deterministic offset N(0, 5) to NOI values ([`fitter.py:444-494`](../../../../main/WRemnants/rabbit/rabbit/fitter.py#L444-L494)) but is applied inside `get_theta()` ([`fitter.py:519-520`](../../../../main/WRemnants/rabbit/rabbit/fitter.py#L519-L520)) so the model uses `theta + offset`. The chi2 at the minimum is invariant under blinding; only the displayed parameter values change.

### Numbers (post-fit, 4-projection fit)

| Test | chi2 | ndf | chi2/ndf | p-value |
|---|---|---|---|---|
| 4D total saturated | 49842 | 49919 | 0.998 | **59.6%** |
| ptll prefit | 60.07 | 39 | 1.54 | 1.67% |
| ptll postfit Linear | 67.41 | 39 | 1.73 | **0.32%** |
| ptll postfit Saturated proj | 66.46 | 39 | 1.70 | 0.40% |
| yll prefit | 27.40 | 20 | 1.37 | 12.4% |
| yll postfit Linear | 43.66 | 20 | 2.18 | **0.17%** |
| yll postfit Saturated proj | 42.43 | 20 | 2.12 | 0.24% |
| cosTheta\* prefit | 1.37 | 8 | 0.17 | 99.5% |
| cosTheta\* postfit Linear | 9.75 | 8 | 1.22 | 28.3% |
| phi\* prefit | 2.13 | 8 | 0.27 | 97.7% |
| phi\* postfit Linear | 12.38 | 8 | 1.55 | 13.5% |

### Findings
1. **All four projections degrade postfit.** No "tension partner" pattern — the fit is not improving one projection at the expense of another. yll is actually the *worst* projection postfit (0.17%), not ptll.
2. **Linear chi2 ~ Saturated projection chi2** for ptll (67.4 vs 66.5). The nuisances have already absorbed nearly all available slack on the projection. There is no rescue from "letting nuisances repull on the projection".
3. **Per-bin residuals on ptll are a bin-by-bin oscillation, not a smooth tilt.** Examples: bins 31/32 (20-22 / 22-24 GeV) flip +1.5 sigma / -1.5 sigma; bin 9 (5.0-5.5 GeV) at +2.2 sigma. Looks like a binning/calibration/migration signature, not a soft-physics modeling failure.
4. **Different projections fail through different nuisance sectors:**
   - ptll: SCETlib NP (lambda4 -2.34 sigma, lambda2 -0.54 sigma), QCDscale-PtV helicity 0/2, b-mass pair (`mb_up` -1.69 sigma, `pdfMSHT20mbrangeSymAvg` -1.15 sigma).
   - yll: muon efficiency (`effSyst_reco_etaDecorr*`), `CMS_prefire_stat_m_*`, `pixel_multiplicity_syst_var*`.
   - cosTheta\*: QCDscale-PtV helicity 0/2 (longitudinal / A2).
   - phi\*: QCDscale-PtV helicity 5/7 (A5 / A7 angular coefficients).
5. **Postfit residuals are much smaller than prefit residuals** (Delta |r^2| ~ -750 chi2-units on ptll using a fixed cov), but the postfit cov shrinks even faster, so chi2 goes up. Classical signature of "data informs nuisances faster than residuals can keep up" — the model can't reach the precision the data is now demanding.
6. **`mb_up` correlation with `pdfAlphaS` is +0.14** (postfit). Largely orthogonal. Linearized: freezing `mb_up` shifts pdfAlphaS by ~+0.25 (≈ 0.5 sigma_alphaS); freezing both b-mass nuisances shifts it by ~+0.40 (≈ 0.8 sigma_alphaS). Sigma_alphaS essentially unchanged.

### Working hypotheses (not yet discriminated)
- **A) Real model bias**: small systematic mis-modeling that statistics now resolve. Supports: prefit ptll already at 1.67%, residual oscillation pattern, saturated test confirms no nuisance rescue.
- **B) Over-flexible nuisances**: ~3700 nuisances (3127 efficiency, 176 QCDscale-PtV, 144 scale-corrections, 49 pixel-multiplicity) absorbing 4D structure that should be modelled, putting coherent residuals into the marginals. Supports: every projection degrades postfit, BBB / per-bin nuisances at the top of the impact ranking.
- Both can be true simultaneously.

## Decisions taken
- Track this study in `agents/studies/projection_pvalues/`.
- Anchor analyses on the existing fit `260427_debug_allproj/`; only re-run `rabbit_fit.py` when a task explicitly requires a refit (freeze / decorrelate / sensitivity).
- For each new fit, use a fresh tag `proj_pvals_<YYMMDD_HHMMSS>` in the output dir.
- Use `MY_OUT_DIR=/ceph/submit/data/group/cms/store/user/$USER/alphaS/` for fit outputs and `MY_PLOT_DIR=/home/submit/$USER/public_html/alphaS/` for plots.

## Tasks (cross off as we go)

Format: `- [ ]` open, `- [x]` done. Add date and short outcome on completion.

### Quick diagnostics (no new fit needed; reuse `260427_debug_allproj/`)
- [x] **T1. Per-bin pull plots for all four projections.** *Done 2026-04-27, see runlog 19:43 entry.* Outcome: ptll bin 9 (5.0-5.5 GeV) +2.2σ peak; ptll bin 31/32 oscillation reproduced (calibration/migration signature near the 20→22 GeV bin width step); yll worst per-bin pull at bin 2 (low |yll|); cosTheta\*/phi\* small per-bin pulls (their chi2 comes from off-diagonal cov rather than diagonal residuals). Script: `scripts/per_bin_pulls.py`. Plots: `MY_PLOT_DIR/260427_194300_projection_pvalues/per_bin_pulls/`.
- [x] **T2. 2D residual map (ptll, yll).** *Done 2026-04-27, see runlog 20:03 entry.* Outcome: 2D ptll-yll fit p-value = **70.3%** (chi2/ndf = 758/780) — the 4D model is fine on the joint distribution. The 1D marginals (ptll 0.32%, yll 0.17%) fail because residuals in the joint plane are coherent in sign along the orthogonal axis, so summing over yll accumulates ~sqrt(20)x into the 1D pull. **This argues for hypothesis A (real shape mismodeling) and against hypothesis B**, since over-flexible nuisances would absorb 4D structure and leave the marginals fine. Script: `scripts/residual_2d_heatmap.py`. Output: `260427_debug_allproj_with2D/`. Plots: `MY_PLOT_DIR/260427_194300_projection_pvalues/residual_2d/`.
- [x] **T3. Eigendecomposition of res_cov for ptll.** *Done 2026-04-27 with caveat, see runlog 19:55 entry.* Outcome: chi2 reconstruction from `J J^T + diag(nobs)` (J = `hist_prefit_inclusive_global_impacts`) underestimates true chi2 by ~2.2x (30 vs 67); same factor as the README-noted `cov_post + diag(nobs)` approximation. Relative ranking of modes is robust: top mode = 7.2% of chi2, top 3 = 16.7%, top 5 = 23%. **Spread across many modes — favors hypothesis A.** Exact dump still TODO: requires editing `fitter.py:1842` to write `(residuals, res_cov)` to disk, or a standalone script that re-instantiates a `Fitter` and calls `_residuals_profiled` with postfit `self.x` set from saved parms. Script: `scripts/dump_rescov.py`. Plots: `MY_PLOT_DIR/260427_194300_projection_pvalues/rescov_eig/`.

### Hypothesis-discriminating fits (each is one full rabbit_fit re-run)
- [x] **T4. Disable BBB via `--noBinByBinStat`.** *Done 2026-04-27, see runlog 19:25 entry.* Outcome: 4D total p-value collapses 59.6% → ~0%, ptll/yll projections get 4-5x worse, cosTheta\*/phi\* barely move, alphaS shifts by only +0.006 (0.01 σ_NOM). BBB is doing legitimate work covering per-bin MC stat across 49920 bins. **BBB is not the cause** of the bad projection p-values — Reading B (over-flexibility) is rejected for BBB. Output: `260427_debug_noBBB/`.
- [x] **T5. Freeze the muon-efficiency nuisance group** (`effSyst_reco_*` and `effSyst_tracking_*`). *Done 2026-04-27, see runlog 19:57 entry.* Outcome: yll p-value 0.17% -> 0.13% (slightly worse), ptll/cosTheta\*/phi\* essentially unchanged; alphaS shifts by only -0.031 (~0.06 sigma_NOM). The fit reabsorbs the lost reco+tracking freedom into iso/trigger eta-decorrelated nuisances (top movers: `effSyst_iso_etaDecorr28` Δ+0.87, `effSyst_iso_etaDecorr27` Δ+0.79, etc.). **Reading B rejected** for `effSyst_reco_*`/`effSyst_tracking_*`: the eff system as a whole is doing legitimate work on yll. Output: `260427_debug_freezeEff/`.
- [x] **T6. Re-correlate `QCDscaleZfine_PtV*helicity_*` across pTV bins** (implemented as freezing all 160 per-pTV per-helicity QCDscale params). *Done 2026-04-27, see runlog 19:56 entry.* Outcome: every projection got worse, especially phi\* (13.5% -> 7.5%) and ptll (0.32% -> 0.17%); alphaS shifts by only +0.021 (~0.04 sigma_NOM). Resummation transition scales (`resumTransitionZSym{Avg,Diff}`) and the PtV-inclusive QCDscale variant absorb the slack but cannot recover the chi2. **Reading B rejected** for QCDscaleZfine per-helicity. Output: `260427_debug_freezeQCDscaleHel/`.

### Residual / dimensionality diagnostics
- [x] **T10. Residual-on-nuisance-basis projection (no refit).** *Done 2026-04-27, see runlog 21:29 entry.* Question: is the 1D ptll residual aligned with any nuisance shape direction in the current basis? Method: project per-bin postfit residual onto each `hist_prefit_inclusive_global_impacts` column; group-level absorption via ridge regression with prior penalty. Outcome: **ALL 198 theory nuisances + 3334 detector nuisances together absorb only ~7 of 38 (~18%) of the linear ptll chi2 reconstruction at reasonable prior shifts**; the remaining ~80% lives in directions orthogonal to the entire current basis. scetlibNPlambda4 ranks only #4 in alignment (single-nuisance Δchi2=0.58). Most-aligned ptll nuisances are `QCDscaleZfine_PtV*helicity_0_SymAvg` across pTV bins with alternating signs — a 1D-oscillatory mode. yll residual is *detector*-aligned (effSyst_reco_track absorbs 4 of 24); cosTheta\*/phi\* residuals are small in absolute terms. Conclusion: **widening any existing nuisance prior (including the full NP subspace) cannot absorb the residual** — the data wants a new shape direction that isn't in the basis.
- [ ] **T11. `--scaleNPLambda4 2.0` refit.** Refit the 4D nominal with the NP Lambda4 prior width doubled (`setupRabbit.py --scaleNPLambda4 2.0`). If the postfit `scetlibNP*lambda4` pull relaxes toward 0 and ptll p-value rises, NP-prior-width is the issue. If pull stays at the boundary or projections don't move much, T10's prediction (NP cannot absorb the residual) is confirmed. Output dir: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_scaleNPLambda4_2/`. *Launched 2026-04-27 21:29.*
- [ ] **T12. 2D-only fit (drop cosTheta\*/phi\* from the input tensor).** Refit with `setupRabbit.py --fitvar 'ptll-yll'`. If 1D ptll/yll p-values recover, the 4D bad p-values were induced by tension between angular constraints and the kinematic plane (no single nuisance set fits both simultaneously). If they stay bad, residual is intrinsic to (ptll, yll). Output dir: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260427_debug_2Donly/`. *Launched 2026-04-27 21:29.*

### Sensitivity to ad-hoc priors
- [x] **T7. Freeze b-mass pair as a sensitivity check.** *Done 2026-04-27, see runlog 19:07 entry.* Outcome: alphaS shifts by **+0.461** (≈ 0.94 sigma_NOM), sigma 0.490 → 0.470. ptll postfit Linear chi2 67.4 → 78.3 (p 0.32% → 0.02%); Saturated proj 66.5 → 77.3 (p 0.40% → 0.025%). Resummation/transition-scale and helicity-0 QCDscale-PtV nuisances repull harder to compensate but cannot recover the chi2. **Note:** `--freezeParameters` requires space-separated args, not comma-separated. Output: `260427_debug_freezeMB_v2/`.
- [ ] **T8. (Optional) Widen b-mass priors instead of freezing.** *Skipped 2026-04-27.* Rabbit's CLI has no flag to scale a constrained nuisance's prior width (`fitter.py:632, 683` even has explicit FIXMEs for this), and `setupRabbit.py`'s scale flags (`--scaleTNP`, `--scalePdf`, `--scaleMinnloScale`, `--scaleNPLambda4`) do not target the b-mass nuisances. To do this mechanically, either (a) add a `--scaleConstraint` flag to rabbit, (b) regenerate the input HDF5 with widened b-mass templates via `setupRabbit.py`, or (c) load the input HDF5 in Python and rescale the b-mass syst columns before the fit. Deferred to a follow-up session that includes a code change.

### Eventual deliverable
- [ ] **T9. Decide whether to act on the bad projection p-values for the publication.**
  - Outcome A (model bias): document the mis-modeling, quote the effect on alphaS, possibly enlarge a theory uncertainty.
  - Outcome B (over-flexibility): de-flex the offending nuisance group(s), re-quote the alphaS measurement.
  - Outcome both: most likely; combine the two responses.
  - **Status after T1-T7 (2026-04-27): evidence strongly favors A.** Every "freeze a nuisance group" experiment (BBB, eff reco/tracking, QCDscale per-helicity, b-mass) **degrades** projections rather than improving them — the fitter is using the available freedom legitimately. T2 shows the 2D ptll-yll joint passes (p=70%) while 1D marginals fail; this is the signature of a small per-4D-bin shape mismodeling that becomes coherent in 1D after summing the orthogonal axis. T3 shows the chi2 is spread across many modes, not concentrated in 1-2 directions an over-flexible nuisance could absorb. **Recommended action toward publication:** quote the T7 b-mass-freeze sensitivity (+0.46 σ_alphaS_NOM ~= 0.94 sigma_NOM) as a one-sided systematic; document the residual pattern (ptll bin 9 at 5.0-5.5 GeV at +2σ, ptll bin-31/32 oscillation across the 20→22 GeV bin width step) as a known mismodeling; do not chase the 1D projection p-values by deflexing nuisances.

## Runtime notes (verified 2026-04-27)
- Singularity launch + setup pattern that works for rabbit (tensorflow lives in a venv inside the container — not currently documented in `AGENTS.md`):
  ```bash
  singularity run --bind /scratch/,/work/,/home/,/ceph/ \
    /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest \
    /bin/bash -lc 'source /opt/venv/bin/activate && \
      cd /home/submit/lavezzo/alphaS/WRemnantsHelpers && source setup.sh && \
      <your_command>'
  ```
- Without `source /opt/venv/bin/activate`, `import tensorflow` fails in the container and `rabbit_fit.py` will not run. (`fitter.sh` assumes the user has already activated the venv interactively.)
- `print_command <fitresults.hdf5>` (alias defined in `setup.sh`) recovers the exact `rabbit_fit.py` invocation that produced a given result.
