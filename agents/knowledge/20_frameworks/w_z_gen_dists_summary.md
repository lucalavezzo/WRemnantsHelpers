# `w_z_gen_dists.py` Summary

## Scope
Operational behavior of `${WREM_BASE}/scripts/histmakers/w_z_gen_dists.py`.

## Canonical Facts
- GEN-level histmaker for W/Z processes.
- Produces nominal GEN distributions and optional theory/EW/helicity/systematic outputs.
- Writes analysis output HDF5 and optionally helicity-xsec HDF5.

## Rules I Should Follow
- Do not use data samples with this script.
- If `--addHelicityAxis` is used, separate helicity-xsec file writing is skipped by design.
- For bottom-enriched studies, verify exact `bottom_sel` implementation before interpreting swap results.

## Important Modes
- Default correction binning.
- `--finePtVBinning`
- `--useTheoryAgnosticBinning`
- `--useUnfoldingBinning`

## Common Pitfalls
- Misreading help text for `--skipEWHists`.
- Assuming optional single-lepton+bottom paths are robust without testing.

## Last Updated
- 2026-02-16

## Source
- Migration from legacy `w_z_gen_dists.py` summary notes (2026-02-16)
