# AGENTS

## Overview
This repo is a set of scripts that use the `WRemnants` framework to run various studies (`scripts/`), or common operations (`workflows/`).

## Runtime Environment
- **Python runtime:** Provided by the `wmassdevrolling` Singularity image (`singularity run --bind /scratch/,/ceph/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest`), which ships the CMS WRemnants software stack and Python 3.
- **Key packages:** Core `WRemnants` dependencies including `rabbit` (handles fitting procedures), `wums` (a series of helpers for HDF5 files, plotting, etc.).
- **Environment variables:** Exported by `setup.sh` — `MY_WORK_DIR`, `MY_PLOT_DIR`, `MY_OUT_DIR`, `NANO_DIR`, `SCRATCH_DIR`, `PYTHON_JULIAPKG_PROJECT`, and `JULIA_DEPOT_PATH`; plus any variables defined by `../WRemnants/setup.sh`.

## Setup Checklist
1. Clone both repos side-by-side: `git clone --recurse-submodules git@github.com:WRemnants/WRemnants.git` and `git clone git@github.com:WRemnants/WRemnantsHelpers.git`.
2. Enter the `WRemnantsHelpers` directory and source the helper setup: `source setup.sh`.
3. Ensure the base `WRemnants` environment is initialized via `../WRemnants/setup.sh` (invoked automatically by `setup.sh`).
4. Confirm the required singularity container is available and run `singularity run --bind /scratch/,/ceph/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest`.
5. Verify expected environment variables (`MY_WORK_DIR`, `MY_PLOT_DIR`, `MY_OUT_DIR`, `NANO_DIR`, `SCRATCH_DIR`, `PYTHON_JULIAPKG_PROJECT`, `JULIA_DEPOT_PATH`) are set, then run a smoke test (e.g. `bin/run --help`).

## Development Guidelines

## Troubleshooting
- **Logs & monitoring:** logs should be saved in `logs/` with timestamps.

## Roadmap / TODOs

## Revision History
- **YYYY-MM-DD:** Created skeleton (Codex).
- **YYYY-MM-DD:** TODO first content draft.
