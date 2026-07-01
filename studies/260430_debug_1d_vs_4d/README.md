# 260430_debug — 4D vs 1D ptll refit

## Question
For each of the systematic-stress configurations under
`$MY_OUT_DIR/260430_debug/`, compare the nominal 4D fit
(ptll × yll × cosThetaStar × phiStar) to a 1D refit using only ptll.
Specifically: do λ₂/λ₄ pulls and the saturated projection p-value
behave consistently between the two fits?

## Guiding questions
- For each configuration, how do the λ₂ (`chargeVgenNP0scetlibNPZlambda2`)
  and λ₄ (`chargeVgenNP0scetlibNPZlambda4`) postfit values and constraints
  change going from 4D → 1D?
- How does the saturated-likelihood test on the ptll projection (4D) compare
  to the saturated test on the standalone 1D fit?
- Are the configuration-vs-configuration trends preserved between 4D and 1D?

## Inputs
- 4D fits: `$MY_OUT_DIR/260430_debug/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_*/`
- 1D fits: `$MY_OUT_DIR/260430_debug/ZMassDilepton_ptll_*/` (produced in this session)

## Output
- `results_table.tex` / `results_table.pdf` — two tables (4D and 1D)
  with postfit pulls, physical postfit shifts (pull × kfactor scale),
  saturated p-values, and Δpull/Δσ on $\alpha_S$ (4D only).
- `scripts/build_tables.py` — regenerates `results_table.tex`.
  Reads `fitresults.hdf5` for all 9 configs in 4D and 1D, plus the
  rabbit_fit logs for 1D saturated p-values.
- `scripts/extract_pulls.py`, `scripts/extract_pvalues.py`,
  `scripts/run_ptll_debug_fits.sh` — earlier helpers used to drive the
  9 1D fits and extract α_s pulls / saturated p-values.

## Notes / caveats
- `--computeSaturatedProjectionTests` was dropped from the 1D `rabbit_fit`
  calls because the 1D saturated covariance is not positive definite
  (1D fit is too low-dim for the saturated post-processing). The saturated
  chi2 itself is still computed and printed by `rabbit_fit.py`.
- `setupRabbit.py --fakelumi` had `default=1.1` mid-session — bug was fixed
  to `default=0` and the 9 1D fits were re-run so non-fakelumi variants no
  longer carry a free `fakelumi` norm parameter.
- The `_scetlibNoConstraint` configuration originally required a local
  source patch in `wremnants/postprocessing/rabbit_theory_helper.py`
  (uncommenting three `# noConstraint=True` lines around the
  `scetlibNP` / `rename` blocks). The 1D `_scetlibNoConstraint` fits
  in this study were produced that way, then the patch reverted.
  As of 2026-05-04 a `--noConstrainParams REGEX` flag is wired into
  `setupRabbit.py` (mirrors `--scaleParams` / `--noSymmetrize`); the
  same configuration can now be reproduced with
  `--noConstrainParams 'scetlibNP'`. Verified: the six SCETlib NP pulls
  agree to 4 decimals with the patched run.
- `_fakelumi_noAlphaS` and the plain `LatticeNoConstraints` row have been
  excluded from the combined table per request.
- NP table cells are the **physical postfit shift** of each NP in its
  natural units, computed as
  `cell = rabbit_pull × scaleParams_factor × σ_phys`,
  where `σ_phys = base_kfactor × template_half_range` is the prefit
  prior σ of the NP in the Nominal config (constant per column,
  printed in the column header). For chargeV NPs `base_kfactor = 1`
  (`rabbit_theory_helper.py:866`); for gamma NPs `base_kfactor = 10`
  from `LatticeNoConstraints` (`:737`). `scaleParams_factor` is the
  multiplier applied via `--scaleParams REGEX=FACTOR` for that
  (config, NP) — 1 in Nominal, 5 in matching Scale5p0 cells.
  Template half-ranges are taken from `np_map` (`:828–830`) and
  `lattice_vals` (`:686–693`).
- α_s columns: both `Δpull(α_s)` (vs Nominal) and the absolute postfit
  total `σ(α_s)` are multiplied ×2, matching
  `pullsAndImpacts.sh --scaleImpacts 2.0`, so they're in 10⁻³ units on
  the analysis's 1σ_α_s = 0.002 scale.
- The script accepts `--physical` (default) / `--no-physical` to toggle
  between physical units and raw rabbit pulls (Nominal-prior σ).
  Run `python scripts/build_tables.py --no-physical > results_table.tex`
  to get the raw-pull table.
