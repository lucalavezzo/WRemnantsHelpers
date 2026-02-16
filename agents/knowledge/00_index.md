# Knowledge Base Index

This directory is the canonical long-lived knowledge base for Codex in this repo.

## Purpose
- Keep reusable guidance separate from per-study run logs.
- Store only knowledge that should survive across sessions and studies.
- Keep one canonical owner page per topic to avoid drift.

## Folder Semantics
- `10_environment/`
  - What it is: runtime/bootstrap/container/setup facts and constraints.
  - Write here if: the fact is about environment initialization, paths, or execution caveats.
  - Do not put here: analysis physics, plotting style, or per-study outcomes.
- `20_frameworks/`
  - What it is: framework/tool behavior (`WRemnants`, rabbit, key scripts/wrappers) and frozen usage contracts.
  - Write here if: the fact is about how a framework component works or should be run.
  - Do not put here: analysis-specific conclusions from one study.
- `30_physics_global/`
  - What it is: analysis-wide physics context and stable interpretation guides.
  - Write here if: the point applies broadly to this analysis beyond one run tag.
  - Do not put here: framework internals or one-off study notes.
- `50_workflows/`
  - What it is: repeatable operating procedures and session process rules.
  - Write here if: it is a reusable workflow loop/checklist/policy.
  - Do not put here: low-level framework options that belong in `20_frameworks/`.
- `60_plotting_style/`
  - What it is: collaborator-facing plotting conventions and labeling rules.
  - Write here if: it governs plot readability, naming, style, or comparison presentation.
  - Do not put here: slide-specific layout behavior (use `70_slides/`).
- `70_slides/`
  - What it is: study-slide generation workflow and slide formatting conventions.
  - Write here if: it controls slide generation, structure, formatting, or compile/copy behavior.
  - Do not put here: generic plotting rules (use `60_plotting_style/`).
- Root pages (for example `90_glossary.md`)
  - What it is: cross-cutting reference material.
  - Write here if: information is used by multiple folders and does not fit one owner folder.

## How This Integrates With Existing Docs
- `agents/studies/<topic>/` remains the active lab notebook for each study.
- `agents/knowledge/` is curated memory promoted from studies and workflow docs.
- Legacy top-level files in `agents/*.md` are now thin redirects to these canonical pages.

## Promotion Rule
Promote a note from a study to `agents/knowledge/` when all are true:
1. Reusable outside one run tag/postfix.
2. Validated in at least one rerun or independent check.
3. Expressed as a stable rule/fact (or labeled `provisional`).

## Topic Map
- Environment and bootstrap:
  - `agents/knowledge/10_environment/runtime_bootstrap.md`
- Framework and nominal workflow:
  - `agents/knowledge/20_frameworks/nominal_workflow.md`
  - `agents/knowledge/20_frameworks/frozen_nominal_spec.md`
  - `agents/knowledge/20_frameworks/validation_contract.md`
  - `agents/knowledge/20_frameworks/w_z_gen_dists_summary.md`
- Process workflow recipes:
  - `agents/knowledge/50_workflows/study_iteration_loop.md`
- Physics global context:
  - `agents/knowledge/30_physics_global/an25_085_digest.md`
- Analysis/study-specific physics conclusions:
  - keep in `agents/studies/<topic>/README.md` (do not duplicate in canonical KB unless requested)
- Plotting conventions:
  - `agents/knowledge/60_plotting_style/plotting_and_labels.md`
- Slide workflow and style:
  - `agents/knowledge/70_slides/study_slides_workflow.md`
- Shared terminology:
  - `agents/knowledge/90_glossary.md`

## Write Routing (Decision Tree)
1. Is it run-specific, tag-specific, or hypothesis-tracking?
   - Write to `agents/studies/<topic>/README.md` and `agents/studies/<topic>/runlog.md`.
2. Is it about runtime/setup/container/path behavior?
   - Write to `agents/knowledge/10_environment/`.
3. Is it about framework/tool behavior, command semantics, or frozen defaults?
   - Write to `agents/knowledge/20_frameworks/`.
4. Is it analysis-wide physics context that should persist across studies?
   - Write to `agents/knowledge/30_physics_global/`.
5. Is it a reusable procedure/checklist for how we execute work?
   - Write to `agents/knowledge/50_workflows/`.
6. Is it about plot conventions (labels/scales/comparison format)?
   - Write to `agents/knowledge/60_plotting_style/`.
7. Is it about slide generation/content/layout conventions?
   - Write to `agents/knowledge/70_slides/`.
8. Is it cross-cutting terminology?
   - Write to `agents/knowledge/90_glossary.md`.

## Update Protocol
- Update `agents/studies/<topic>/README.md` and `runlog.md` live during work.
- At the end of a session (or when a fact stabilizes), promote key points to topic pages here.
- Add `Source` and `Last updated` fields on each page.
