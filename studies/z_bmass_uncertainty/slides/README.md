# Slides for z_bmass_uncertainty

This folder stores the editable slide outline and generated deck files.

## Files
- `outline.json`: primary slide content and plot selections.
- `z_b_mass_uncertainty_study.tex`: generated Beamer source (from `scripts/study_slides.py`).

## Regenerate
```bash
python scripts/study_slides.py --study-dir agents/studies/z_bmass_uncertainty
```

Optional PDF compile (in an environment with `pdflatex`):
```bash
python scripts/study_slides.py --study-dir agents/studies/z_bmass_uncertainty --compile
```
