# Nominal Workflow

This file captures the current "nominal histmaker" procedure for the alphaS analysis.

## Purpose
- Build nominal dilepton histograms from NanoAOD using WRemnants histmaker:
  - Wrapper: `workflows/histmaker.sh`
  - Core script: `${WREM_BASE}/scripts/histmakers/mz_dilepton.py`

## Environment Prerequisites
Run in this order:
```bash
singularity run --bind /scratch/,/work/,/home/,/ceph/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling\:latest
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh
```

## Default Wrapper Behavior
`workflows/histmaker.sh` currently runs:
```bash
python ${WREM_BASE}/scripts/histmakers/mz_dilepton.py \
  --dataPath /scratch/submit/cms/wmass/NanoAOD/ \
  -o ${MY_OUT_DIR}/<YYMMDD>_histmaker_dilepton/ \
  --maxFiles -1 \
  --axes ptll yll \
  --csVarsHist \
  --forceDefaultName \
  ${extra_args} ${postfix}
```

Notes:
- `--maxFiles -1` is full-stat run (can take about 1 hour).
- Output directory is date-stamped by the wrapper.
- Output filename can change (depends on options and postfix).

## Recommended Launch Mode (Background)
Use the helper launcher so logs are timestamped in `logs/`:
```bash
run workflows/histmaker.sh
```

With custom options:
```bash
run workflows/histmaker.sh -e " --theoryCorr <...> " -p "<tag>"
```

Important wrapper parsing note:
- For options with values passed through `-e`, prefer single-token form with `=`:
  - Good: `-e "--maxFiles=10"`
  - Risky: `-e "--maxFiles 10"` (can be parsed incorrectly and drop the value)

## Debug Mode
For fast checks before full run:
```bash
run workflows/histmaker.sh -e "--maxFiles=2"
```

## How To Find the Output File Reliably
The definitive output path is printed by the core writer at the end of the run:
- log line pattern: `Output saved in <full_path_to_hdf5>`

Example helper:
```bash
rg -n "Output saved in" logs/*.log | tail -n 1
```

## Current Open Point
- NP/theory correction choices (for example `--theoryCorr ...`) are still under active development.
- Treat default wrapper options as nominal baseline unless explicitly overridden.

## Step 2: Detector-Level Fit (Rabbit)

### Purpose
- Run the detector-level Z fit in 4D:
  - `ptll`, `yll`, `cosThetaStarll_quantile`, `phiStarll_quantile`
- Wrapper: `workflows/fitter.sh`
- Core tools:
  - setup stage: `${WREM_BASE}/scripts/rabbit/setupRabbit.py`
  - fit stage: `rabbit_fit.py` (from rabbit submodule)

### Two-Step Flow
1. **Setup Rabbit**
   - Build fit input tensor ("carrot") from histmaker output:
     - nominal prediction
     - observed data
     - systematic variations
   - Set `alphaS` as parameter/noi via `--noi alphaS`.
2. **Run Fit**
   - Minimize likelihood and produce impacts/hist outputs via `rabbit_fit.py`.

### Default Wrapper Behavior
`workflows/fitter.sh` runs:
```bash
python ${WREM_BASE}/scripts/rabbit/setupRabbit.py \
  -i <histmaker_hdf5> \
  --fitvar ptll-yll-cosThetaStarll_quantile-phiStarll_quantile \
  -o <output_dir> \
  --noi alphaS \
  [--postfix <tag>] \
  [extra_setup_args]
```

Then:
```bash
rabbit_fit.py <carrot_file> \
  --computeVariations \
  -m Project ch0 ptll \
  --computeHistErrors \
  --doImpacts \
  -o <carrot_dir> \
  --globalImpacts \
  --saveHists \
  --saveHistsPerProcess \
  [extra_fit_args]
```

### Tested Smoke Example
Input:
```bash
/scratch/submit/cms/alphaS/260213_histmaker_dilepton/mz_dilepton_codex.hdf5
```

Command:
```bash
workflows/fitter.sh /scratch/submit/cms/alphaS/260213_histmaker_dilepton/mz_dilepton_codex.hdf5 -p codex
```

Observed outputs:
```bash
/scratch/submit/cms/alphaS/260213_histmaker_dilepton/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_codex/ZMassDilepton.hdf5
/scratch/submit/cms/alphaS/260213_histmaker_dilepton/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_codex/fitresults.hdf5
```

### Notes / Wrapper Caveats
- `-p` short option is fixed to require an argument (`-p codex` now works).
- In non-interactive shells, `tee /dev/tty` may fail; wrapper now handles non-TTY by printing captured output directly.
- If `-o` is omitted, output defaults to `dirname(<input_hdf5>)`.
- For nominal workflow, keep both `--doImpacts` and `--globalImpacts` enabled.
- Additional rabbit mappings can be inspected as needed, but are not required for basic nominal validation.

### Optional Modes
- Setup only:
```bash
workflows/fitter.sh <input_hdf5> --noFit -p <tag>
```
- Fit only (reuse prebuilt carrot):
```bash
workflows/fitter.sh <carrot_hdf5> --noSetup
```
- 2D fit variant:
```bash
workflows/fitter.sh <input_hdf5> --2D -p <tag>
```

## Step 3: Analyze Fit (Impacts / Figure of Merit)

### Purpose
- Quantify uncertainty on `pdfAlphaS` from fit outputs.
- Typical analysis endpoint for this stage: inspect pulls/impacts and total uncertainty.

### Plot-Based Wrapper
- Wrapper: `workflows/pullsAndImpacts.sh`
- Example:
```bash
workflows/pullsAndImpacts.sh <fitresults.hdf5> -p <tag>
```
- Produces pulls/impacts plots (traditional and global impacts) for `pdfAlphaS`.

### Text-Based Numeric Check (Rabbit Utility)
- Utility script:
  - `/home/submit/lavezzo/alphaS/gh/WRemnants/rabbit/bin/rabbit_print_impacts.py`
- Example:
```bash
python /home/submit/lavezzo/alphaS/gh/WRemnants/rabbit/bin/rabbit_print_impacts.py <fitresults.hdf5>
python /home/submit/lavezzo/alphaS/gh/WRemnants/rabbit/bin/rabbit_print_impacts.py <fitresults.hdf5> --globalImpacts
```
- This prints impact tables directly in terminal (useful for quick validation in Codex sessions).
- To match `workflows/pullsAndImpacts.sh` convention, apply scaling:
```bash
python /home/submit/lavezzo/alphaS/gh/WRemnants/rabbit/bin/rabbit_print_impacts.py <fitresults.hdf5> --scale 2.0
python /home/submit/lavezzo/alphaS/gh/WRemnants/rabbit/bin/rabbit_print_impacts.py <fitresults.hdf5> --globalImpacts --scale 2.0
```

### Tested Output (Codex Smoke)
Using:
```bash
/scratch/submit/cms/alphaS/260213_histmaker_dilepton/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_codex/fitresults.hdf5
```

Observed:
- Unscaled: `Total: 1.5105` (traditional and global).
- Scaled (matching pulls/impacts plotting convention): `Total: 3.02099` (traditional and global).
- Numeric impact tables are available without relying on plots.
