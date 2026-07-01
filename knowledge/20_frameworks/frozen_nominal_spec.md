# Frozen Nominal Spec

## Scope
Frozen command patterns and defaults for nominal detector-level Z alphaS workflow.

## Canonical Facts
- Step 1:
  - `workflows/histmaker.sh`
  - nominal defaults include `--maxFiles -1 --axes ptll yll --csVarsHist --forceDefaultName`
- Step 2:
  - `workflows/fitter.sh <histmaker_hdf5>`
  - rabbit setup uses `--fitvar ptll-yll-cosThetaStarll_quantile-phiStarll_quantile --noi alphaS`
  - rabbit fit keeps impacts/hist outputs enabled (`--doImpacts --globalImpacts --saveHists --saveHistsPerProcess`)
- Step 3:
  - `workflows/pullsAndImpacts.sh <fitresults_hdf5> -p <tag>`
  - numeric equivalent uses `rabbit_print_impacts.py --scale 2.0`

## Last Verified Smoke
- Date: 2026-02-13
- Histmaker smoke output:
  - `/scratch/submit/cms/alphaS/260213_histmaker_dilepton/mz_dilepton_codex.hdf5`
- Fitter smoke outputs:
  - `/scratch/submit/cms/alphaS/260213_histmaker_dilepton/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_codex/ZMassDilepton.hdf5`
  - `/scratch/submit/cms/alphaS/260213_histmaker_dilepton/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_codex/fitresults.hdf5`
- FoM smoke:
  - scaled `Total` on `pdfAlphaS`: `3.02099`

## Rules I Should Follow
- Update this file whenever nominal commands/flags change.
- Keep this aligned with validation contract.

## Last Updated
- 2026-02-16

## Source
- Migration from legacy frozen nominal spec notes (2026-02-16)
