# `w_z_gen_dists.py` Summary (Working Note)

Source analyzed:
- `../gh/WRemnants/scripts/histmakers/w_z_gen_dists.py`

## Purpose
- GEN-level histmaker for W/Z processes in WRemnants.
- Produces boson-level histograms (mass, rapidity, `ptVgen` or `ptqVgen`, charge) and optional theory/EW/helicity/systematic outputs.
- Writes standard analysis output (`w_z_gen_dists.hdf5`-style naming via `write_analysis_output`) and can also write a separate helicity-xsec file (`w_z_helicity_xsecs*.hdf5`).

## Core Flow
1. Parse common histmaker options plus GEN-specific flags.
2. Load MC datasets via `getDatasets` (era default `13TeVGen`, default `filterProcs=common.vprocs`).
3. In `build_graph`:
 - Reject data samples (`RuntimeError` for `dataset.is_data`).
 - Build nominal event weight from `sign(genWeight)` plus special sample fixes.
 - Define theory weights/corrections (`theory_tools.define_theory_weights_and_corrs`).
 - Choose binning (default corr binning, theory-agnostic, or unfolding-based).
 - Build nominal GEN histogram axes/columns for W or Z.
 - Optionally add charm/bottom/helicity axes and extra histograms.
 - Optionally add EW histograms and auxiliary single-lepton/photon histograms.
 - Optionally add theory/systematic and helicity variation histograms.
 - Always fill:
   - `nominal_gen`
   - `nominal_gen_pdf_uncorr`
   - `nominal_gen_theory_uncorr`
4. Run with `narf.build_and_run`.
5. Optionally aggregate groups and scale-to-data (when `aggregateGroups` requested).
6. Optionally produce combined helicity-xsec outputs unless `--addHelicityAxis` or `--skipHelicityXsecs`.

## Nominal Observable Definition
- Base boson dimensions:
 - `massVgen`:
   - Z: `[60, 120, 13000]`
   - W: `[0, 75, 80, 85, 120, 13000]`
 - rapidity:
   - default `absYVgen`
   - `--signedY` uses signed `yVgen`
 - transverse variable:
   - default `ptVgen`
   - `--ptqVgen` uses `ptqVgen`
 - charge axis:
   - Z fixed neutral bin
   - W ± charge bins

## Binning Modes (important for studies)
- Default: correction-oriented binning (`common.ptZgen_binning_corr` / `common.ptWgen_binning_corr`, and matching absY binning).
- `--finePtVBinning`: 0.5 GeV `ptVgen` bins up to 100 GeV, then overflow bin.
- `--useTheoryAgnosticBinning`: uses `differential.get_theoryAgnostic_axes(...)`.
- `--useUnfoldingBinning` (Z path): uses `differential.get_dilepton_axes(...)` with unfolding-style edges.
- `--genPtBinningAsReco`: modifies the unfolding-binning behavior (disables rebinning).

## Flags Most Relevant to Your alphaS Workflow
- `--addHelicityAxis`: append helicity index/moment axes directly to nominal histograms.
- `--propagatePDFstoHelicity`: propagate PDF uncertainties into helicity xsecs.
- `--theoryCorr`, `--ewTheoryCorr`, `--theoryCorrections`, `--quarkMassCorr`, `--centralBosonPDFWeight`: theory-reweighting controls.
- `--fiducial {masswindow,dilepton,singlelep}`: apply fiducial unfolding selection.
- `--singleLeptonHists`, `--photonHists`, `--auxiliaryHistograms`: additional diagnostic outputs.
- `--addBottomAxis`, `--addCharmAxis`: append flavor-tag-style axes and related extra histograms.

## Bottom-axis Behavior (for Zbb studies)
- With `--addBottomAxis`, the script defines `bottom_sel` from final-state B-hadron kinematics (`subB_pt > 5`) and appends that axis to nominal GEN histograms.
- It also computes several b-jet / b-hadron helper quantities and stores a small set of dedicated 1D B-hadron histograms (`leadB_pt`, `subB_pt`, `subB_aeta`).
- This is an analysis-specific enrichment embedded in the core histmaker and is not a purely minimal “generic GEN boson” mode.

## Output Conventions
- Main output includes per-dataset hist collections with nominal and systematic/theory variants.
- Extra helicity cross section file is produced when allowed:
 - base: `w_z_helicity_xsecs.hdf5`
 - suffixes depend on options (e.g. `_signedY`, `_theoryAgnosticBinning`).

## Caveats To Remember
- Data input is unsupported by design.
- If `--addHelicityAxis` is used, the post-processing block that writes `w_z_helicity_xsecs*.hdf5` is intentionally skipped.
- `--skipEWHists` help text is misleading (it says “Also store…” but flag behavior is to skip those histograms).
- In the single-lepton optional block, `addBottomAxis` appends a `bottom` column name while earlier code defines `bottom_sel`; avoid relying on `--singleLeptonHists --addBottomAxis` without testing this path.
