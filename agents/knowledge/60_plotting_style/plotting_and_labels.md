# Plotting And Labels

## Scope
General plot presentation conventions for collaborator-facing comparison plots.

## Canonical Rules
- Use human-readable axis labels; avoid internal variable names in labels.
- Keep selection details in slide bullets/captions, not overlong axis text.
- For multiplicity-like diagnostics with long tails, prefer log-y.
- For sample comparison, always provide both shape comparison and ratio panel.

## Study-Derived Lessons
- B-hadron plots are more interpretable when labels avoid code-like names (for example not `nBhad_pt5`).
- Distinguish clearly normalized vs unnormalized swap results in filenames and slide text.

## File/Tag Conventions
- Use explicit run tag in output folder names.
- Keep normalized variants with a deterministic suffix (for example `_norm`).

## Last Updated
- 2026-02-16

## Source
- `agents/studies/z_bmass_uncertainty/runlog.md`
- `studies/z_bb/plot_narf.py`
