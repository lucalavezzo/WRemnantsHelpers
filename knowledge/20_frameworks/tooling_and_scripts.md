# Development Guidelines

## Scope
How to add or modify code/scripts/plots in this repo without creating drift or duplication.

## Reproducibility
- Prefer scriptable commands over ad hoc shell history.
- Save logs to `logs/` with timestamps; `bin/run` is the default launcher for detached jobs.

## Tooling Preference Order (always check in this order)
1. **Rabbit's `bin/` tools first** (`$WREM_BASE/rabbit/bin/`): `rabbit_fit.py`, `rabbit_plot_hists.py`, `rabbit_plot_hists_uncertainties.py`, `rabbit_plot_pulls_and_impacts.py`, `rabbit_plot_likelihood_scan.py`, `rabbit_plot_cov.py`, `rabbit_plot_inputdata.py`, `rabbit_print_impacts.py`, `rabbit_print_pulls_and_constraints.py`, `rabbit_debug_inputdata.py`, `merge_inputs.py`, `rabbit_text2hdf5.py`. Canonical for fitting, plotting fit inputs/outputs, pulls/impacts, likelihood scans, etc. — use them rather than rewriting equivalents.
2. **This repo's `scripts/` next** for things rabbit doesn't cover: `plot_narf_hists.py` (narf histograms — usually already supports the case), `compare_file_hists.py`, `compare_preds.py`, `open_h5py.py`, `open_narf_h5py.py`, `open_fitresult.py`, `open_corr_file.py`, `plot_corr_hists.py`, `study_slides.py`, etc. Read `--help` and existing flags before writing a new script — these are the canonical entry points and are usually already extendable.
3. Only after both fall short should new ad hoc plotting/analysis code be written. If a new capability ends up in a one-off place, prefer extending the relevant `scripts/` entry point and reusing it across studies.

## Plotting
- Prefer `wums` plotting/output utilities (`plot_tools`, `boostHistHelpers`, `output_tools`) over ad hoc matplotlib-only helpers.
- Style and labeling rules: `knowledge/60_plotting_style/plotting_and_labels.md`.

## Documentation As A Living Artifact
- When new workflow / physics-context / environment / failure-mode details are learned, update the relevant files in `knowledge/` (and `AGENTS.md` if it's a top-level pointer change) in the same working session.
- Prefer small, incremental doc updates over delayed large rewrites.
- Always perform an explicit physics-sense check on plots/results — record the interpretation in the active study notes, not just "ran successfully".
- Promote stable, cross-study findings/rules from `studies/` into `knowledge/` during the same session.

## Last Updated
- 2026-05-01

## Source
- Migrated from `AGENTS.md` (2026-05-01).
