---
id: dokan_aS120_finalize_recovery_20260528
title: Recover the αs=0.120 NNLO Z theory predictions from a wedged dokan submit
status: completed
question: How do we cleanly stop a wedged `dokan` (`nnlojet-run submit`) and still produce the final merged NNLO predictions?
owner: lavezzo
created: 2026-05-28
updated: 2026-05-28
tags: [dokan, nnlojet, production, msht20an3lo, alphaS, recovery]
parent: null
investigates_regions: []
investigates_methods: []
investigates_fits: []
investigates_background_estimates: []
investigates_uncertainties: []
next_action: Decide whether to re-submit additional jobs to push `cross_hist` from 1.51% down to the 1.0% target, or accept the current 1.51% as the theory input for AN-25-085.
current_hypotheses:
  - dokan's `finalize` subcommand will produce a usable merged result even with ~110k jobs stuck in DB-active state, because `MergePart` only counts `JobStatus == DONE`.
  - SIGTERM to the wedged `nnlojet-run submit` will let the SQLite DB close cleanly, so `finalize` can re-open it.
success_criteria:
  - submit process exits without corrupting the SQLite DB.
  - `nnlojet-run finalize` runs to completion and writes `result/final/*.dat`.
  - Inclusive cross-section value is reported with a sensible uncertainty.
blockers: []
pending_signoffs: []
---

## Status

Recovery complete. The 13-day-old `dokan_aS120-0` tmux session was running
`nnlojet-run submit CMS_Z_NNLO_condor_msht20an3lo_as120_20260427` (dokan v1.0.2,
editable install in `/work/submit/lavezzo/alphaS/NNLOJET/dokan/`). It had been
silent since 2026-05-20 10:54 with zero HTCondor jobs in the queue and two
zombie subprocesses — the submit driver was wedged. SIGTERM brought it down
cleanly (Ctrl-C was ignored, process was in `D+` then `R+` but did not handle
the signal), `nnlojet-run doctor` reported 206 active parts / 109,787
DB-active jobs / 438 failed jobs, and `nnlojet-run finalize …` ran the full
MergePart → MergeAll → MergeFinal cascade in ~52 minutes on the 64-core local
pool. Final inclusive `σ(Z) = 1.812942 ± 0.003967 nb (0.219%)`; the
differential `cross_hist` reached 1.51% vs the 1.0% configured target. Final
result files landed in
`/scratch/submit/cms/alphaS/CMS_Z_NNLO_condor_msht20an3lo_as120_20260427/result/final/`
as `nnlo_only.ptz__<ylow>__<yhi>.dat`. The tmux session was killed after
finalize exited. Next action: decide whether to re-submit to push cross_hist
to 1.0%, or accept 1.51% for AN-25-085.

## Guiding Question

How do we cleanly stop a wedged `dokan` (`nnlojet-run submit`) and still produce the final merged NNLO predictions?

## Hypotheses

- dokan's `finalize` subcommand will produce a usable merged result even with ~110k jobs stuck in DB-active state, because `MergePart` only counts `JobStatus == DONE`. [confirmed]
- SIGTERM to the wedged `nnlojet-run submit` will let the SQLite DB close cleanly, so `finalize` can re-open it. [confirmed]

## Ideas / Methods Explored

- `nnlojet-run doctor RUN` as the pre-action diagnostic: prints last log line + counts of active parts / active jobs / failed jobs.
- Send Ctrl-C to the tmux pane first (cleanest); fall back to `kill -TERM <pid>` if the process is in uninterruptible sleep and ignores SIGINT.
- Run `finalize` in the same tmux pane it was killed in so the shell cwd is already the run's parent dir.

## Dead-Ends

- (None.)

## Findings

- The wedged submit process showed `R+` then `D+` kernel state with two `<defunct>` `nnlojet-run` child zombies, and no condor jobs in queue — symptom of a submit loop whose worker pool died but whose master kept polling. (evidence: `ps --forest` 2026-05-28 ~10:30)
- SIGINT (Ctrl-C via tmux send-keys) was not honored on the first try; SIGTERM `kill -TERM 3998619` took it down within seconds. SIGKILL was deliberately avoided to preserve the SQLite DB. (evidence: pane capture + ps before/after)
- `nnlojet-run finalize` ran 206 MergePart → MergeAll → MergeFinal in ~52 min wall on 64 local cores, with no errors. Per-part merge times grew with file counts from ~5 min (12k files) up to ~50 min (390k files). (evidence: `/scratch/submit/cms/alphaS/finalize_20260528.log`)
- Two parts (RRa_7, RRa_8) produced **bitwise-identical results** to the 2026-05-20 log — confirms the dokan merge is deterministic and the DB state was consistent after the wedge. (evidence: `RRa_7: 6482 +/- 162.93%` and `RRa_8: 7424 +/- 94.43%` both runs)
- Final inclusive σ(Z) = 1.812942 ± 0.003967 nb [0.219%]; differential `cross_hist` reached 1.51% vs the configured 1.0% target (we lost statistics during the 8-day wedge). Total CPU invested: 39542 days (~949,000 CPU-hours). (evidence: `finalize_20260528.log` lines around 2026-05-28 11:25:53 `sig_comp: complete`)
- Final output layout: `CMS_Z_NNLO_condor_msht20an3lo_as120_20260427/result/final/nnlo_only.ptz__<ylow>__<yhi>.dat` — Z-pT spectra binned in rapidity from 0.25 up. (evidence: `find result/final` 2026-05-28)
- The 109,787 jobs that remained in DB-active state were silently ignored by `MergePart` (it filters on `Job.status == JobStatus.DONE`); they do not need to be cleaned up to get a usable result, but they remain in the DB. (evidence: `dokan/src/dokan/db/_dbmerge.py:145`)

## Open Questions

- Should we re-submit ~1 job worth (dokan estimate at exit: "still require about 0 seconds of runtime to reach desired target accuracy (approx. 1 jobs)") to push `cross_hist` from 1.51% to 1.0%? Or is 1.51% acceptable as theory input for AN-25-085?
- Are the 109k stale "active" jobs and 438 failed jobs worth cleaning out of `db.sqlite` before any future use of this run dir, or do we just leave it?

## Decisions

- 2026-05-28 — Use SIGTERM (not SIGKILL) to bring down the wedged submit — preserves SQLite DB integrity so `finalize` can re-open it. — Reason: dokan's writer cleanup happens during normal exit; SIGKILL leaves DB half-written.
- 2026-05-28 — Run `nnlojet-run finalize` with default trim/k-scan settings (`trim_threshold=4.0, trim_max_fraction=0.007, k_scan_nsteps=3, k_scan_maxdev_steps=0.2`). — Reason: no signal we need to deviate; defaults are dokan's vetted choices.
- 2026-05-28 — Kill the `dokan_aS120-0` tmux session after finalize exited. — Reason: result files are durable on disk under `result/final/`; tmux session no longer carrying state.

## Next Action

Decide whether to re-submit additional jobs to push `cross_hist` from 1.51% down to the 1.0% target, or accept the current 1.51% as the theory input for AN-25-085.
