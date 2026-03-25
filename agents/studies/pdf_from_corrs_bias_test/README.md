# PDF From Correlations Bias Test

## Study Question
When alternate PDF sets are used as pseudo-data, how large is the fitted $\alpha_s$ bias relative to uncertainties from the nominal central PDF fit?

## Guiding Questions
- [in progress] Are there central/pseudo-data PDF pairings that produce large $|\Delta\alpha_s|/\sigma$ outliers?
- [open] Are the largest shifts concentrated in specific PDF families (e.g. HERA, NNPDF, MSHT, CT)?
- [open] How sensitive are conclusions to uncertainty normalization choice (`total`, `pdf-only`, `pdf-only-trad`, `contour`)?
- [open] Are there implementation mismatches in PDF naming/mapping that could bias interpretation?

## Current Understanding
- Existing workflow scripts are present in `studies/pdf_from_corrs_bias_test/`:
  - `run_histmakers.py`
  - `run_fitter.py`
  - `plot_results.py`
- Intended flow: produce histograms per central PDF with alternates as theory corrections, fit each central configuration using alternate PDFs as pseudo-data, and inspect $\alpha_s$ pull patterns.

## Live Notes
- 2026-02-26: New study notebook initialized for this session.
- 2026-02-26: Hypothesis added before running checks: significant tension should appear as red cells/points in `plot_results.py` outputs where $|\Delta\alpha_s|$ exceeds chosen uncertainty.
- 2026-02-26: Preliminary code inspection indicates naming sets are mostly aligned, but there may be key mismatches to validate before production run:
  - `ct18` appears in `run_histmakers.py` while fitter/plot choices are keyed to `ct18z`.
  - `msht20an3lo` appears in histmaker logic while fitter/plot use `msht20aN3LO`.
- 2026-02-26: Added histogram-level comparison script for this study:
  - `studies/pdf_from_corrs_bias_test/plot_nominal_vs_alternate_pdfs.py`
  - Reads histmaker `.hdf5` output directly.
  - Plots `nominal` vs alternate-PDF central templates with configurable `--axes` projection and unrolling.
- 2026-02-26: Extended the plotting script to optionally include MINNLO weight PDFs (`nominal_pdf{PDFNAME}`) in the same figure for cross-validation against theory-correction PDFs.
  - New option: `--include-minnlo-pdfs`.
- 2026-02-26: Added a standing workflow policy request from discussion: every produced plot should be checked for physics plausibility and that interpretation should be documented in study notes.
- 2026-02-26: `run_histmakers.py` was refactored for the current workaround (multi-theory-correction limitation):
  - now loops over theory-correction keys and runs one `mz_dilepton.py` command per correction set;
  - no longer relies on `workflows/histmaker.sh` defaults that inject extra theory corrections.
- 2026-02-26: Added directory-based comparison plotting script:
  - `studies/pdf_from_corrs_bias_test/plot_nominal_vs_alternate_pdfs_from_dir.py`
  - Scans a histmaker output directory and infers central PDF from filename suffix (`mz_dilepton_*_<pdf>.hdf5`), consistent with `run_histmakers.py` naming.
  - Uses inferred PDF to map to expected theory-correction histogram and optionally overlays MINNLO (`nominal_pdf...`) curves.
- 2026-02-27: Standardized the study-level key to `msht20an3lo` (lowercase) across fitter and plotting scripts to avoid dropped entries during file/directory parsing.
- 2026-02-27: Coverage check on current split-fit outputs confirms the limited matrix is from missing fit pairs, not plotting logic (currently populated centrals: `ct18z`, `herapdf20`, `msht20`).
- 2026-02-28: Plot styling convention updated for this study: use CMS default qualitative palette (`#3f90da`, `#ffa90e`, `#bd1f01`, `#94a4a2`, `#832db6`, `#a96b59`, `#e76300`, `#b9ac70`, `#717581`, `#92dadd`) as the default for multi-curve/category overlays.
- 2026-03-01: For a reduced `ct18z/msht20` split-fit check, plotting with
  `plot_results_from_split_fits.py` showed only one populated point because only one
  split fit directory existed (`..._msht20_pseudoct18z`). This is a coverage issue in
  produced fit outputs, not a plotting bug.
- 2026-03-01: Running `run_fitter.py` on the same reduced matrix produced the missing
  pair (`..._ct18z_pseudomsht20`), after which split-fit plots populated both
  expected off-diagonal entries.

## Decisions
- Decision pending: first pass will focus on validating input/output naming consistency, then run a reduced matrix smoke test before full grid.

## Next Steps
- Confirm the intended PDF key list and naming conventions for this campaign.
- Run one small end-to-end smoke test (2 central x 2 pseudo-data).
- If clean, launch full matrix and produce heatmap/scatter outputs for interpretation.
- 2026-02-28: Grouped nuisance-variation plotting is now available directly in rabbit plotting via `--varGroupNames` (with labels/colors), using fitresult meta mapping (`systs/systgroups/systgroupidxs`) and combining member nuisance histogram variations in quadrature around nominal.
