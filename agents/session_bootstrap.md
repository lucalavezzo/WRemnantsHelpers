# Session Bootstrap Runbook

Use this at the start of each new Codex session to provide stable context quickly.

## 1) Enter Runtime Environment
Run in this order:

```bash
singularity run --bind /scratch/,/work/,/home/,/ceph/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling\:latest
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh
```

## 2) Quick Sanity Checks
```bash
echo "$WREM_BASE"
echo "$MY_WORK_DIR"
echo "$MY_OUT_DIR"
echo "$NANO_DIR"
which python
python --version
bin/run --help
```

Expected conventions:
- `WREM_BASE` must point to the canonical WRemnants tree chosen by `setup.sh`.
- In this Codex setup, `$WREM_BASE` is inside the editable workspace, so edits under `$WREM_BASE` should be treated like normal in-repo edits (no extra permission request just for that path).
- `MY_WORK_DIR` should be this repo.
- `bin/` from this repo should be on `PATH`.
- Python environment should include required analysis packages (`hist`, `ROOT`).

Optional package smoke check:
```bash
python -c "import hist, ROOT; print('imports_ok')"
```

## 2b) Codex Container Notes
- In Codex tool execution, container commands may need unsandboxed permissions to work.
- If a long inline `singularity run ... -lc '...'` command acts strangely, prefer:
  - small container commands, or
  - running a script file from this repo (for example under `agents/`) inside the container.
- Avoid `set -u` in bootstrap/debug scripts that source project setup files, since some setup scripts assume variables like `PYTHONPATH` may be initially unset.

## 3) Session Start Prompt for Codex
At the beginning of each session, provide:

```text
Read AGENTS.md and agents/session_bootstrap.md first.
Then help me with: <task>.
```

For study-slide sessions, include:

```text
Also read agents/study_slides.md and prepare/update slides for agents/studies/<topic>/.
```

## 4) Study Task Template
Fill this before asking Codex to automate a workflow:

```text
Goal:
Input datasets/configs:
Exact command I run today:
Expected outputs (files/plots/tables):
Output location:
Validation checks:
```

## 5) Update Policy
- If path conventions change, update `setup.sh` first.
- Then update `AGENTS.md` and this runbook in the same commit.
- For active studies, keep `agents/studies/<topic>/README.md` and `agents/studies/<topic>/runlog.md` updated incrementally during the session.
- For each active study README:
  - maintain a small "Guiding questions" section near the top;
  - log newly learned facts and emerging questions, with status (`answered`, `partial`, `open`).
  - when a new hypothesis/check is requested, add it to the study notes before execution and update the status immediately after the run.
- If slide output is requested, keep `agents/studies/<topic>/slides/outline.json` updated and regenerate `.tex` with `scripts/study_slides.py`.
