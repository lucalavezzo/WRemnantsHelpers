# Study-to-Slides Workflow

Purpose:
- Provide a reproducible way to build a slide deck from an active study folder.
- Support quick iteration on slide content with the user.

## Standard Inputs
- Study folder: `agents/studies/<topic>/`
- Required context files:
  - `README.md`
  - `runlog.md`
- Slide outline file:
  - `agents/studies/<topic>/slides/outline.json`

## Generator Script
- Script: `scripts/study_slides.py`
- Minimal usage:
```bash
python scripts/study_slides.py --study-dir agents/studies/<topic>
```
- This writes a `.tex` deck into:
  - `agents/studies/<topic>/slides/`

## Iteration Protocol
1. User asks for slides for a study.
2. Codex proposes/updates `slides/outline.json` with:
   - objective,
   - key findings,
   - open questions,
   - selected plots.
3. Codex renders `.tex` and shares produced path.
4. User reviews requested additions/removals/reordering.
5. Codex updates outline and regenerates.
6. Once stable, codify conventions in `AGENTS.md` and this file.

## Content Rules
- Prefer concise slides with one message each.
- Source all claims from study docs/logged outputs.
- Use only plots already produced by the study run unless user asks for new production.
- Keep a short "Open Questions" slide to anchor next iteration.

## Optional Compile Step
- Add `--compile` to request local `pdflatex` compilation:
```bash
python scripts/study_slides.py --study-dir agents/studies/<topic> --compile
```
- If LaTeX tools are not in PATH, run this in the usual container runtime.

## Optional Auto-Copy To MY_PLOT_DIR
- Compile and auto-copy PDF to `$MY_PLOT_DIR/<YYMMDD>_study_slides`:
```bash
python scripts/study_slides.py --study-dir agents/studies/<topic> --compile --copy-pdf-to-plot-dir
```
- Use a custom subdirectory under `$MY_PLOT_DIR`:
```bash
python scripts/study_slides.py --study-dir agents/studies/<topic> --compile --copy-pdf-to-plot-dir --plot-subdir <custom_subdir>
```
