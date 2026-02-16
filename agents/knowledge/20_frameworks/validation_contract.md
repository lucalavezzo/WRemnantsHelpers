# Validation Contract

## Scope
Minimal pass/fail checks for nominal workflow steps.

## Global Preconditions
1. Container started with standard singularity command.
2. `source setup.sh` succeeds.
3. `WREM_BASE`, `MY_WORK_DIR`, `MY_OUT_DIR`, `NANO_DIR` are non-empty.
4. `python -c "import hist, ROOT; print('imports_ok')"` passes.

## Step 1 (Histmaker)
Pass when:
1. Exit code is `0`.
2. Log has `Output saved in <...>.hdf5`.
3. Output file exists and is non-empty.

## Step 2 (Fitter)
Pass when:
1. setup stage writes `ZMassDilepton.hdf5`.
2. fit stage writes `fitresults.hdf5`.
3. `fitresults.hdf5` exists and is non-empty.
4. wrapper exits `0`.

## Step 3 (Impacts/FoM)
Pass when:
1. `rabbit_print_impacts.py` runs for traditional and global impacts.
2. scaled checks (`--scale 2.0`) run successfully.
3. output includes `Total:` line for `pdfAlphaS`.

## Nominal Convention
- Report scaled FoM (`--scale 2.0`) in units of `1e-3` on alphaS.

## Last Updated
- 2026-02-16

## Source
- Migration from legacy validation contract notes (2026-02-16)
