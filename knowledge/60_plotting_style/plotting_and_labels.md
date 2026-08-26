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

## wums plotting quirks
- **`wums.plot_tools.makePlot2D` never draws the values.** It builds the figure
  (`figure(...)`), computes `zlim`, writes the title and the `hep.cms.label`, and
  then `return fig` -- there is no `pcolormesh`, `imshow` or `hist2dplot` call
  anywhere in it, and the `colormap` / `zlim` / `logz` / `zsymmetrize` arguments
  are computed but never consumed. The symptom is a correctly sized, correctly
  labelled, correctly CMS-badged plot with an EMPTY axes and no colorbar --
  which is easy to mistake for a bad z-range or an all-NaN array. Until it is
  fixed upstream, 2D maps have to be drawn with bare matplotlib
  (`ax.pcolormesh`) even though the project rule is that histogram plotting goes
  through wums. Seen 2026-08-25 in
  `studies/scetlib-ad-param-model/residual_structure_map.py`, which carries the
  bare-matplotlib fallback and a comment saying why.

## File/Tag Conventions
- Use explicit run tag in output folder names.
- Keep normalized variants with a deterministic suffix (for example `_norm`).
- Shared implementation for color defaults lives in `scripts/common_plot_style.py` (`CMS_DEFAULT_COLORS`, `build_cms_color_cycle`).

## Last Updated
- 2026-08-25

## Source
- `studies/scetlib-ad-param-model/` (wums 2D plotter)
- `studies/z_bmass_uncertainty/runlog.md`
- `studies/z_bb/plot_narf.py`
