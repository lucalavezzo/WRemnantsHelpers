# Nominal Frozen Spec

Purpose:
- Single source of truth for the currently frozen nominal workflow commands.
- Update this file whenever nominal flags/paths/conventions change.

## Scope
- Analysis stage: detector-level Z workflow for alphaS extraction.
- Channels in this spec: Z reco-level (`ptll`, `yll`, `cosThetaStarll_quantile`, `phiStarll_quantile`).

## Environment
Run in this order:
```bash
singularity run --bind /scratch/,/work/,/home/,/ceph/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling\:latest
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh
```

## Step 1 (Histmaker)
Frozen command pattern:
```bash
workflows/histmaker.sh
```

Current nominal behavior (from wrapper):
- `--maxFiles -1`
- `--axes ptll yll`
- `--csVarsHist`
- `--forceDefaultName`
- output directory: `${MY_OUT_DIR}/<YYMMDD>_histmaker_dilepton/`

Debug override pattern:
```bash
workflows/histmaker.sh -e "--maxFiles=10" -p <tag>
```

## Step 2 (Fitter)
Frozen command pattern:
```bash
workflows/fitter.sh <histmaker_hdf5>
```

Current nominal behavior (from wrapper):
- setup stage:
  - `setupRabbit.py ... --fitvar ptll-yll-cosThetaStarll_quantile-phiStarll_quantile --noi alphaS`
- fit stage:
  - `rabbit_fit.py ... --computeVariations -m Project ch0 ptll --computeHistErrors --doImpacts --globalImpacts --saveHists --saveHistsPerProcess`

Optional postfix:
```bash
workflows/fitter.sh <histmaker_hdf5> -p <tag>
```

## Step 3 (Impacts / Figure of Merit)
Plot-based:
```bash
workflows/pullsAndImpacts.sh <fitresults_hdf5> -p <tag>
```

Text-based (equivalent numeric check):
```bash
python /home/submit/lavezzo/alphaS/gh/WRemnants/rabbit/bin/rabbit_print_impacts.py <fitresults_hdf5> --scale 2.0
python /home/submit/lavezzo/alphaS/gh/WRemnants/rabbit/bin/rabbit_print_impacts.py <fitresults_hdf5> --globalImpacts --scale 2.0
```

## Last Verified Smoke Configuration
- Date: 2026-02-13
- Histmaker smoke:
  - `workflows/histmaker.sh -p codex -e "--maxFiles=10"`
  - output: `/scratch/submit/cms/alphaS/260213_histmaker_dilepton/mz_dilepton_codex.hdf5`
- Fitter smoke:
  - `workflows/fitter.sh /scratch/submit/cms/alphaS/260213_histmaker_dilepton/mz_dilepton_codex.hdf5 -p codex`
  - outputs:
    - `/scratch/submit/cms/alphaS/260213_histmaker_dilepton/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_codex/ZMassDilepton.hdf5`
    - `/scratch/submit/cms/alphaS/260213_histmaker_dilepton/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_codex/fitresults.hdf5`
- FoM smoke:
  - scaled `Total` on `pdfAlphaS`: `3.02099` (traditional and global)

## Known Caveats
- `workflows/histmaker.sh` extra-arg parsing:
  - prefer `-e "--maxFiles=10"` over `-e "--maxFiles 10"`.
- `workflows/fitter.sh` non-TTY output handling has been patched for Codex/non-interactive execution.
