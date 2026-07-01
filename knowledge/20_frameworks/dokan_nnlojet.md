# dokan / NNLOJET production driver

`dokan` is the workflow orchestrator we use to drive NNLOJET on HTCondor for fixed-order Z theory predictions. The `nnlojet-run` CLI you see in tmux sessions is dokan's entry point — they are the same thing.

## Install

- Editable install of dokan v1.0.2: `/work/submit/lavezzo/alphaS/NNLOJET/dokan/` (separate `dokan_pristine_control/` checkout sits next to it for diffing).
- Venv python: `/work/submit/lavezzo/alphaS/NNLOJET/nnlojet/bin/python3.12`
- CLI: `/work/submit/lavezzo/alphaS/NNLOJET/nnlojet/bin/nnlojet-run` — entry point is `dokan:main` (per `dokan/pyproject.toml`).
- Deps: `luigi`, `numpy`, `rich`, `sqlalchemy` (state lives in a per-run `db.sqlite`).

## Subcommands

`nnlojet-run {init,config,submit,doctor,finalize}`.

- `init` — initialise a new run directory.
- `config` — set defaults for the run configuration.
- `submit` — submit + drive jobs through the cluster (HTCondor policy at submit06). Long-lived process; manages the merge pipeline as parts complete.
- `doctor RUN` — read-only diagnostic. Prints the last DB log row and counts of `active parts / active jobs / failed jobs`. Safe to run while submit is alive.
- `finalize RUN` — explicit final merge step (see below). Required after submit exits if you want consolidated outputs.

`finalize` flags: `--trim-threshold` (outlier σ-cut, default 4.0), `--trim-max-fraction` (max fraction trimmed, default 0.007), `--k-scan-nsteps` (default 3), `--k-scan-maxdev-steps` (default 0.2).

## Internal pipeline

`Entry::run` (luigi DAG) flows: **preproductions → MergeAll → dispatch (production) → MergeFinal**. Inside `submit`, the production loop continuously dispatches new jobs (`DBDispatch` / `DBRunner`), tracks them (`HTCondorTracker`), and runs incremental `MergePart` as parts complete.

`MergePart` only consumes jobs with `JobStatus == DONE` (`dokan/src/dokan/db/_dbmerge.py:145`). Stale `QUEUED/DISPATCHED/RUNNING/RECOVER` jobs in the DB are silently ignored at merge time — they only matter for the submit-loop's accounting.

`JobStatus` enum (`dokan/src/dokan/db/_jobstatus.py`):

- `QUEUED=0`, `DISPATCHED=1`, `RUNNING=2`, `DONE=3`, `MERGED=4`, `FAILED=-1`, `RECOVER=-2`
- `terminated_list()` = `(DONE, MERGED, FAILED)`
- `active_list()` = `(QUEUED, DISPATCHED, RUNNING, RECOVER)`

## Run directory layout

A run dir (e.g. `/scratch/submit/cms/alphaS/CMS_Z_NNLO_condor_msht20an3lo_as120_20260427/`) contains:

- `db.sqlite` — sqlalchemy state. Authoritative for "what jobs exist, what's done".
- `log.sqlite` — full structured log history (`Log` table).
- `config.json` — run config.
- `template.run`, `nnlojet_wrapper.sh`, `lxplus.template` — NNLOJET runcard + dispatch scaffolding.
- `raw/production/<part_id>/sNN-MM/` — per-job worker dirs (one batch per seed range).
- `result/final/` — merged final outputs after `finalize`. Files are `nnlo_only.ptz__<ylow>__<yhi>.dat` for the Z-pT-vs-rapidity production used in this analysis.
- `submit.restart_<timestamp>.log` — one per submit reattach.
- `finalize_<timestamp>.log` — local convention (tee'd during finalize).

## How to recover a wedged `submit` (validated 2026-05-28)

Symptoms of a wedge: the submit log goes silent for hours/days, `condor_q <user>` shows zero of your jobs, `ps` shows the master `nnlojet-run` python alive (often `D+` or `R+`) with one or more `<defunct>` child workers.

Procedure:

1. **Diagnose first** — from a separate shell, run `nnlojet-run doctor <RUN>`. The `active parts / active jobs / failed jobs` counts tell you how much was lost from HTCondor's side. Doctor is read-only and safe while submit is alive.
2. **Send SIGINT** to the submit's tmux pane: `tmux send-keys -t <session> C-c`. If the process is in uninterruptible sleep (`D+`), the signal will only be delivered when it returns from the kernel call.
3. **If SIGINT is ignored** (we saw this — process moved from `D+` to `R+` but did not handle the signal): `kill -TERM <pid>`. Wait for exit. The cmdline argv getting wiped to `[nnlojet-run]` in `ps` is the normal "running atexit finalizers" state.
4. **Never** use `kill -9` (SIGKILL): it leaves SQLite half-written and `finalize` will refuse / crash on the DB.
5. **Run `nnlojet-run finalize <RUN>`** in the same env. It rebuilds `MergeFinal` from scratch via luigi and tees through trim + k-scan. Stale "active" jobs in the DB are ignored.
6. **Verify completion** by grepping the finalize log for `(sig_comp): complete` (dokan's done marker) and inspecting `result/final/`. The shell prompt returning in the pane is also a clean signal.

`finalize` is **deterministic** — re-running it on the same DB produces bitwise-identical per-Part results (validated 2026-05-28 by matching `RRa_7` and `RRa_8` numbers across two finalize runs separated by 8 days).

## What the final log tells you

Key markers in a clean finalize log:

- `MergePart[<Part>, …]::run:  TIMING merge total: <s>s (<N> files)` — per-part merge started.
- `MergePart[<Part>, …]::run:  DONE in <s>s — <Part>: result=<x> +/- <%>` — per-part merge finished.
- `MergeAll::run` — all per-part merges done, starting the aggregate.
- `(sig_updxs): cross = <fb>` — first inclusive cross-section estimate (pre-trim).
- `MergeFinal::run` — last step (trim + k-scan).
- `(sig_comp): complete` — dokan's success marker.
- `cross = (<x> +/- <e>) fb  [<rel%>]` — final trimmed inclusive σ.
- `reached rel. acc. <%> on cross_hist (requested: <%>)` — differential precision achieved vs target.

Cosmetic warnings (ignore): `DBTask::_distribute_time:  skipping negative elapsed time in Job(id=…, timestamp=0.0, …)` — flags jobs whose elapsed time wasn't recorded; does not affect physics output.

## See also

- Wedge / SIGTERM / finalize walkthrough: `studies/dokan-aS120-finalize-recovery/runlog.md`.
- The NNLOJET runcard used for the αs=0.120 production: `CMS_Z_NNLO_condor_msht20an3lo_as120_20260427/template.run` in the run dir.
