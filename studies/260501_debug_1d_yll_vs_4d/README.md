# 260501_debug — 4D vs 1D yll refit

## Question
For each of the 9 systematic-stress configurations under
`$MY_OUT_DIR/260430_debug/`, compare the existing 4D fit
(ptll × yll × cosθ* × φ*) to a 1D refit using only **yll**.
Pair study to `260430_debug_1d_vs_4d/` (same configs, ptll fitvar);
this isolates yll's response so the rapidity nuisances can be diagnosed
in isolation rather than competing with ptll's resummation channel.

This study was triggered by the freeze-LRT diagnostic in
`fitAlphaSRapidityDecorr_freeze_partial_LRT/`, which showed PDF–αS
degeneracy (CT18Z) is the dominant absorber of the per-bin αS spread,
while scetlibNP / m_b are coupled-but-load-bearing. Looking at yll
alone — without ptll's grip — should help separate which nuisances are
genuinely y-dependent vs which are dragged into yll-shape by their
ptll-correlation.

## Guiding questions
1. For each config, how do λ₂ (`chargeVgenNP0scetlibNPZlambda2`) and
   λ₄ (`chargeVgenNP0scetlibNPZlambda4`) pulls and constraints change
   1D yll vs 4D vs 1D ptll?
2. How does the saturated-likelihood test on the yll projection (4D)
   compare to the saturated test on the 1D yll fit?
3. Are the configuration-vs-configuration trends the same in 1D yll as
   in 1D ptll? Where they differ, the difference identifies a nuisance
   whose role is mostly ptll- (or yll-) shape rather than both.
4. Does the αS central value in 1D yll move differently from 1D ptll
   under the scaleParams stresses — i.e. is yll's αS sensitivity
   coming from PDFs (CT18Z) or NP shape (scetlibNP)?

## Inputs
- 4D fits (already produced): `$MY_OUT_DIR/260430_debug/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_*/`
- 1D ptll fits (already produced): `$MY_OUT_DIR/260430_debug/ZMassDilepton_ptll_*/`
- 1D yll fits (this study): `$MY_OUT_DIR/260430_debug/ZMassDilepton_yll_*/`

## Plan
1. `scripts/run_yll_debug_fits.sh` — copy of the ptll wrapper with
   `--fitvar 'yll'`, `-m Project ch0 yll`, output prefix
   `ZMassDilepton_yll_*`. Keep `--axlim ptll 0j 44j` so yll is fit on
   the same ptll-restricted data slice as the 4D and 1D-ptll runs.
2. Drop `--computeSaturatedProjectionTests` (1D saturated cov is
   non-PD, same as for ptll-1D).
3. `_scetlibNoConstraint` requires the same temporary source-patch in
   `wremnants/postprocessing/rabbit_theory_helper.py` as documented in
   `260430_debug_1d_vs_4d/runlog.md` (lines 751, 880, 979 — uncomment
   `noConstraint=True`); patch and revert in-session.
4. Extraction scripts — re-use `/tmp/extract_pulls.py` and
   `/tmp/extract_pvalues.py` from the ptll study with the yll path
   prefix.
5. Build a combined LaTeX table: 1D yll pull / constraint / saturated
   p-value, alongside the existing 4D and 1D ptll columns where
   informative.

## Status
- 2026-05-01: study folder created; wrapper next.
