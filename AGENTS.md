# AGENTS

## Overview
This repo is a set of scripts that use the `WRemnants` framework to run various studies (`scripts/`), or common operations (`workflows/`).

## Runtime Environment
- **Python runtime:** Provided by the `wmassdevrolling` Singularity image. Start an interactive shell with:
  `singularity run --bind /scratch/,/work/,/home/,/ceph/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling\:latest`
- **Codex container execution note:** In this Codex environment, Singularity may require unsandboxed execution permissions. When debugging through Codex tools, prefer simple commands or script files over complex inline quoting.
- **Key packages:** Core `WRemnants` dependencies including `rabbit` (handles fitting procedures), `wums` (a series of helpers for HDF5 files, plotting, etc.).
- **Environment variables:** Exported by `setup.sh` — `MY_WORK_DIR`, `MY_PLOT_DIR`, `MY_OUT_DIR`, `NANO_DIR`, `SCRATCH_DIR`, `PYTHON_JULIAPKG_PROJECT`, and `JULIA_DEPOT_PATH`; plus any variables defined by the WRemnants `setup.sh` sourced internally by this repo.
- **Canonical WRemnants location:** Always follow the path referenced by `WRemnantsHelpers/setup.sh`. It can change over time and takes precedence over assumptions in docs.
- **Workspace/editing rule for Codex:** In this setup, the `WREM_BASE` path selected by `setup.sh` is within the editable workspace. Codex should treat files under `$WREM_BASE` as normal editable project files and should not request extra permission solely because a file is under `$WREM_BASE`.
- **Analysis note repository:** Physics context for this project is in `/home/submit/lavezzo/alphaS/AN-25-085` (main file: `AN-25-085.tex`).

## Setup Checklist
1. Start the container first:
   `singularity run --bind /scratch/,/work/,/home/,/ceph/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling\:latest`
2. Enter `WRemnantsHelpers` and source:
   `source setup.sh`
3. Let `setup.sh` initialize the linked WRemnants environment (do not hardcode relative paths elsewhere).
4. Verify key variables (`MY_WORK_DIR`, `MY_PLOT_DIR`, `MY_OUT_DIR`, `NANO_DIR`, `SCRATCH_DIR`, `PYTHON_JULIAPKG_PROJECT`, `JULIA_DEPOT_PATH`) and run a smoke test, e.g. `bin/run --help`.

## Session Quickstart
```bash
singularity run --bind /scratch/,/work/,/home/,/ceph/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling\:latest
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh
echo "$WREM_BASE" "$MY_WORK_DIR" "$MY_OUT_DIR" "$NANO_DIR"
bin/run --help
```

## Codex Session Handoff
- At the start of a session, ask Codex to read `AGENTS.md` and `agents/knowledge/00_index.md`.
- Use `agents/knowledge/` as the canonical long-lived knowledge base by topic.
- Keep `agents/studies/<topic>/` as run-by-run lab notebooks and promote stable lessons into `agents/knowledge/`.
- For physics source of truth, keep using `/home/submit/lavezzo/alphaS/AN-25-085`.
- When canonical paths change (for example WRemnants location), update `setup.sh` first, then update docs.

## Development Guidelines
- Keep workflows reproducible: prefer scriptable commands over ad hoc shell history.
- Keep logs in `logs/` with timestamps; `bin/run` is the default launcher for detached jobs.
- Treat documentation as a living artifact: when Codex learns new workflow, physics-context, environment, or failure-mode details, update the relevant files in `agents/knowledge/` and `AGENTS.md` in the same working session.
- Prefer small, incremental doc updates over delayed large rewrites, so future sessions start from current reality.

## Study Recording Convention
- Default for research studies: create a study folder under `agents/studies/<topic>/`.
- Required files:
  - `README.md`: study question, guiding questions, current understanding, decisions taken, and next steps.
  - `runlog.md`: dated command log with output locations and brief interpretation.
- Optional file:
  - `results_index.md`: add only when outputs/plots become numerous and hard to track.
  - `slides/outline.json`: slide blueprint used by `scripts/study_slides.py` to generate a study summary deck.
- Live-update rule:
  - During study sessions, Codex should update the study files incrementally as new understanding is gained (not only at the end of the chat).
  - Record both technical decisions and physics assumptions in `README.md`, and append executed commands/quick outcomes to `runlog.md`.
  - Continuously capture newly learned facts and emerging questions from discussion and outputs; mark whether each question is answered, partially answered, or open.
  - For every newly requested check or hypothesis, add a corresponding note entry before running commands and then update that same entry with outcome/status immediately after results are available.
- Guiding-questions rule:
  - Each study must define a short list of guiding questions near the top of `README.md`.
  - As new questions appear during discussion, add them to the study notes and track their status.
- Standard iteration loop for studies:
  - Implement requested code/config changes.
  - Run the study workflow end-to-end (hist production and plotting/summary), using a fresh unique run tag/postfix on every run for traceability.
  - Inspect outputs directly (plots and/or printed histogram values).
  - Update study docs with new knowledge and question status.
  - When requested, update `slides/outline.json`, regenerate slides via `scripts/study_slides.py`, and iterate with the user on slide content.
  - Summarize concise physics takeaways and propose concrete suggestions for the next iteration.
- In new Codex sessions, when a study is requested, follow this structure unless explicitly overridden.

## Troubleshooting
- **Logs & monitoring:** logs should be saved in `logs/` with timestamps.
- **Container checks from Codex:** If an inline `singularity run ... bash -lc '...'` command behaves unexpectedly, run a small script file from `/home/submit/lavezzo/alphaS/WRemnantsHelpers/agents/` inside the container instead.

## Roadmap / TODOs

## Revision History
- **YYYY-MM-DD:** Created skeleton (Codex).
- **2026-02-13:** Added container-first setup order, canonical path policy, and Codex session handoff notes.
- **2026-02-13:** Added live-update policy for `agents/studies/<topic>/` documentation during active studies.
- **2026-02-13:** Documented that `$WREM_BASE` is inside the editable workspace for Codex sessions.
- **2026-02-13:** Added study-to-slides workflow (`agents/knowledge/70_slides/study_slides_workflow.md`) and `slides/outline.json` convention.
- **2026-02-16:** Migrated reusable documentation into `agents/knowledge/` and made it the canonical long-lived knowledge base.
