# Plotting And Labels

## Scope
General plot presentation conventions for collaborator-facing comparison plots.

## Canonical Rules
- Use human-readable axis labels; avoid internal variable names in labels.
- Keep selection details in slide bullets/captions, not overlong axis text.
- For multiplicity-like diagnostics with long tails, prefer log-y.
- For sample comparison, always provide both shape comparison and ratio panel.
- Use CMS qualitative palettes for multi-curve comparisons:
  - for `n <= 6`: `#5790fc`, `#f89c20`, `#e42536`, `#964a8b`, `#9c9ca1`, `#7a21dd`
  - for `n > 6`: `#3f90da`, `#ffa90e`, `#bd1f01`, `#94a4a2`, `#832db6`, `#a96b59`, `#e76300`, `#b9ac70`, `#717581`, `#92dadd`

## Study-Derived Lessons
- B-hadron plots are more interpretable when labels avoid code-like names (for example not `nBhad_pt5`).
- Distinguish clearly normalized vs unnormalized swap results in filenames and slide text.

## File/Tag Conventions
- Use explicit run tag in output folder names.
- Keep normalized variants with a deterministic suffix (for example `_norm`).
- Shared implementation for color defaults lives in `scripts/common_plot_style.py` (`CMS_DEFAULT_COLORS`, `build_cms_color_cycle`).

## Last Updated
- 2026-02-28

## Source
- `agents/studies/z_bmass_uncertainty/runlog.md`
- `studies/z_bb/plot_narf.py`
