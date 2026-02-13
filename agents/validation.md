# Validation Contract

Purpose:
- Define minimal pass/fail checks for nominal workflow steps.
- Keep checks lightweight and automation-friendly.

## Global Preconditions
Pass conditions:
1. Running inside singularity container started via:
   - `singularity run --bind /scratch/,/work/,/home/,/ceph/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling\:latest`
2. `source setup.sh` succeeds.
3. `WREM_BASE`, `MY_WORK_DIR`, `MY_OUT_DIR`, `NANO_DIR` are non-empty.
4. Python imports succeed:
   - `python -c "import hist, ROOT; print('imports_ok')"`

## Step 1 Validation (Histmaker)
Input:
- NanoAOD base path reachable:
  - `/scratch/submit/cms/wmass/NanoAOD/`

Pass conditions:
1. Histmaker exits code `0`.
2. Log contains:
   - `Output saved in <...>.hdf5`
3. Output file exists and is non-empty.
4. File name/path follows expected pattern:
   - directory like `${MY_OUT_DIR}/<YYMMDD>_histmaker_dilepton/`
   - file like `mz_dilepton*.hdf5`

Quick failure hints:
- If parser complains about missing maxFiles value, use `-e "--maxFiles=<N>"`.

## Step 2 Validation (Fitter)
Input:
- Histmaker output HDF5 file exists.

Pass conditions:
1. `setupRabbit.py` stage produces carrot file:
   - `<...>/ZMassDilepton.hdf5`
2. `rabbit_fit.py` stage produces fit output:
   - `<...>/fitresults.hdf5`
3. `fitresults.hdf5` exists and is non-empty.
4. Wrapper exits code `0` (after non-TTY fixes in `workflows/fitter.sh`).

Quick failure hints:
- If postfix flag fails, use `-p <tag>` (fixed short-option parsing).

## Step 3 Validation (Impacts / FoM)
Input:
- `fitresults.hdf5` from Step 2.

Pass conditions:
1. `rabbit_print_impacts.py` runs successfully:
   - unscaled and `--globalImpacts`
2. Scaled check runs successfully:
   - `--scale 2.0` and `--globalImpacts --scale 2.0`
3. Output includes a `Total:` line for `pdfAlphaS`.

Nominal FoM convention:
- Report scaled value (`--scale 2.0`) to match pulls/impacts plotting convention.
- Units: `1e-3` on alphaS.

## Smoke Baseline (2026-02-13)
- Input fit result:
  - `/scratch/submit/cms/alphaS/260213_histmaker_dilepton/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_codex/fitresults.hdf5`
- Observed:
  - unscaled total: `1.5105`
  - scaled total: `3.02099`
  - same total for traditional and global impacts in this smoke setup

## Contract Update Rule
- When nominal commands/options change, update:
  1. `agents/nominal_config.md`
  2. this file (`agents/validation.md`)
  3. related workflow doc snippets in `agents/workflow_nominal.md`
