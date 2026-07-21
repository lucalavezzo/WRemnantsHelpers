# Baseline invariants (before reorg) — captured 2026-07-02

Inputs:
- datacard: `260623_Zhistmaker/.../ZMassDilepton.hdf5` (realdata Z)
- theory-corr: `scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksVals_CT18Z_N3p0LL_N2LO_CorrZ.pkl.lz4`
- btgrid: script default `_default_btgrid_dir()`

These NUMBERS must be identical after the pure-refactor reorg (physics/rebin fixes deferred).

## Test 1 — σ_gen (cardless core) vs theory-corr (`sigma_gen_at_lambda`)
- `Σ model / Σ corr = 0.99796`
- `model / corr per bin : min 0.9858  max 0.9995` (last bin 0.9858 = the [44,100] truncation overflow, |Y|<5)
- neg spectrum: `neg_area_frac=6.43e-05`, worst neg cell σ=-0.09199 at Y=+3.5,qT=100; 152 in-|Y|≤2.5 / 224 out

## Test 3 — σ_reco(λc) vs card norm[signal] (`param_model_diagnostics` reco)
- `yield-weighted mean|shape−1| = 0.120%`
- `worst bin = -2.97% at (ptll=38, yll=19, cosThetaStarll_quantile=3, phiStarll_quantile=0)`

## Test 2 — σ_gen(λc) vs card N_gen (`param_model_diagnostics` gen)
- global-norm `yield-weighted mean|shape−1| = 3.803%`, `worst = -16.80% at (ptVGen=20, absYVGen=2)`
- resolved-qT (overflow-excluded) bulk `yield-weighted mean|shape−1| = 0.067%`

Full stdout: `baseline/test1_*.txt`, `baseline/test23_*.txt`. Plots under `baseline/plots/`.
Re-run "after" with: `scripts/run_validation_tests.sh after` then diff (ignore timing lines).
