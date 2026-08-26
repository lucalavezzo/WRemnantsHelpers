# Decomposing a matched SCETlib prediction (resummed vs nonsingular)

## Scope
How to attribute a difference between two `*Corr<boson>.pkl.lz4` theory
corrections to the resummed piece, the fixed order, or the PDF.

## Canonical facts

- A matched prediction is built by `input_tools.read_matched_scetlib_hist` as

  ```
  sigma_matched = sigma_resum + (sigma_FO - sigma_FO,sing)
                                 \_______________________/
                                        nonsingular
  ```

  from three inputs: the SCETlib resummed pkl, the SCETlib fixed-order-singular
  pkl (`*_nnlo_sing_*` / `*_n3lo_sing_*`), and the FO generator output (DYTurbo
  txt or an NNLOJET `ptz` directory).
- **The corr file stores only the sum.** The individual pieces are not saved, so
  any resummed-vs-FO statement requires rebuilding from the raw inputs.
- **The raw input paths are recoverable**: every corr file carries
  `meta_data['command']`, the full `make_theory_corr.py` command line.
- **Get the pieces without re-implementing the matching.** Call the production
  function twice per setup, after rebinning the trio to the common edge
  intersection yourself:
  - `read_matched_scetlib_hist(resum, sing, fo)`  → matched
  - `read_matched_scetlib_hist(resum, sing, sing)` → resummed alone, because the
    nonsingular is then identically zero
  - nonsingular = matched − resummed

  Rebin *before* both calls: the function's internal `rebinHistsToCommon` uses
  the FO binning, and NNLOJET is coarser in Y and qT than the SCETlib
  resummation, so the two calls would otherwise land on different binnings.
- Working implementation:
  `studies/n4ll-n3lo-vs-n3ll-nnlo/scripts/decompose_resum_fo.py`. It also
  validates the rebuilt matched spectrum against the shipped corr file
  (agreement is exact, 0.0000%).

## Rules I should follow

- **Change one thing at a time.** Corr files routinely differ in PDF set,
  resummation order *and* FO generator/order simultaneously (the names encode all
  three: `..._<PDF>_<N?p?LL>_<N?LO>_Corr<boson>`). Build a ladder of
  intermediate files so each rung isolates one change; otherwise the PDF term,
  usually the largest, gets misread as a theory-order effect.
- **`sigma_FO` and `sigma_FO,sing` are individually divergent as qT → 0.** Only
  their difference is meaningful. Do not quote or plot the FO / singular-expansion
  sub-split below a few GeV — and note that `--qtCutoff` zeroes the nonsingular
  below the cutoff but not the two pieces separately, so the sub-split does not
  even close there.
- **"Resummed vs nonsingular" is not a qT-local statement at high qT.** Above
  ~30 GeV the matching moves large amounts between the two (they can be +6% and
  −6% of the total while the sum moves 0.2%). Interpret the split only where the
  resummed piece dominates, roughly qT ≲ 20 GeV for the Z.
- **Select Q and |Y| by explicit bin-edge index, not by value.** The SCETlib runs
  carry Q bins outside 60–120 GeV, and value-based slicing (`60j`) fails on an
  axis that is already exactly [60, 120] because `axis.index()` clamps to the
  last bin and boost-histogram rejects the resulting empty slice.

## Gotcha: `--select` in `plot_corr_hists.py` is index-based

`parsing.str_to_complex_or_int` returns an `int` unless the string ends in `j`,
so `--select 'ptVgen 0 44'` selects **bin indices** 0–43, not 0–44 GeV. Corr
files with different qT binnings then get different physical ranges (70-bin
DYTurbo: qT < 29 GeV; 55-bin NNLOJET: qT < 48 GeV), and `--rebinToCommon`
silently truncates to the overlap. Use `'ptVgen 0j 44j'` for a value selection.

## Last Updated
- 2026-08-03

## Source
- `studies/n4ll-n3lo-vs-n3ll-nnlo/LOGBOOK.md`
