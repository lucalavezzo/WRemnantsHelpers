# Study Slides Workflow

## Scope
Reproducible generation of study slides and style conventions for review iterations.

## Canonical Facts
- Generator script: `scripts/study_slides.py`
- Study input root: `agents/studies/<topic>/`
- Outline file: `agents/studies/<topic>/slides/outline.json`

## Standard Commands
```bash
python scripts/study_slides.py --study-dir agents/studies/<topic>
python scripts/study_slides.py --study-dir agents/studies/<topic> --compile
python scripts/study_slides.py --study-dir agents/studies/<topic> --compile --copy-pdf-to-plot-dir
```

## Rules I Should Follow
- One main message per slide.
- Source claims from study docs and produced outputs.
- Keep explicit open questions and conclusions in deck.
- Use math mode in slide text where symbols/inequalities matter.

## Formatting Lessons From Iterations
- Put object-selection definitions in bullets above figures.
- Keep figure sizes constrained when needed (`width` and `height` with keepaspectratio).
- Prefer plain physics phrasing over code symbols in collaborator-facing slides.

## Last Updated
- 2026-02-16

## Source
- Migration from legacy study-slides workflow notes (2026-02-16)
- `agents/studies/z_bmass_uncertainty/runlog.md`
