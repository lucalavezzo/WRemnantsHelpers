---
name: study
description: Run a study as an orchestrator — start or resume studies/<slug>, dispatch study-worker subagents onto scoped tasks, keep the study LOGBOOK.md as the campaign record, and publish it to the webdir. Use when starting or picking up a study, when delegating a piece of analysis, or when asked "where are we on <study>".
---

# Orchestrating a study

You are the orchestrator of one study. A team is **one orchestrator + N workers on one
study**: you hold the plan and the narrative, workers do the tasks and each keeps its own
logbook under yours.

This file holds **process**. The **state** lives in `studies/<slug>/LOGBOOK.md`. Keep that
split: don't copy state into here, don't copy process into the logbook. (Same split as the
`fit-queue` skill, which owns fit-campaign process.)

## 1. Start or resume

```
studies/<slug>/
├── LOGBOOK.md            # yours
├── <YYMMDD>-<task>/      # one per delegated task, worker-owned
│   └── LOGBOOK.md
└── scripts/ QUEUE.md …   # study-wide, unchanged
```

**Resuming** — read in this order and stop:

1. `studies/<slug>/LOGBOOK.md` → the **START HERE** block. Current state, next action,
   what's blocking.
2. `studies/<slug>/*/LOGBOOK.md` → only the **START HERE** blocks of the task logbooks
   (`grep -A 12 'START HERE'`, or read the frontmatter + that section). A task dir is any
   subdir containing a `LOGBOOK.md`.

That's enough to pick up. Don't read whole logbooks — some are hundreds of KB — and don't
re-derive what's recorded or re-open settled `## Decisions`.

**Starting new** — `mkdir studies/<slug>`, copy `studies/_TEMPLATE/LOGBOOK.md` into it,
fill the frontmatter and `Goal`. `<slug>` is 2–4 kebab-case words.

Either way, then run:

```
bash scripts/webpublish_study.sh <slug>
```

Idempotent — a no-op if the study is already published. It prints the URL; hand that to
Luca.

## 2. Dispatch

Spawn `study-worker` subagents. **One task = one question = one task directory.**

Cut tasks so each has a single answerable question. "Investigate the NP wall" is not a
task; "does the B=4 wall change σ(α_s) at fixed λ init" is.

The spawn prompt must carry:

- the **study slug** and the **task dir** to create (`studies/<slug>/<YYMMDD>-<task>`),
- the **one question**, stated as a question,
- the **evidence already established** — run dirs, numbers, the relevant `knowledge/` note,
  the settled decisions it must not contradict,
- explicitly **what not to redo**, and what's out of scope.

A worker's context is fresh. Anything you don't pass, it either re-derives at cost or gets
wrong.

**Parallel is fine** — several workers at once, each on its own task dir. That is safe
precisely because workers never write your logbook. Do not give two workers the same task
dir.

Use `physics-reviewer` (read-only) on any result that will be quoted to collaborators, go
into the AN, or become a `knowledge/` note. Use `knowledge-curator` when closing the study.

## 3. When a worker returns

The worker's summary is lossy; its logbook is the artifact. So:

- Append **one** dated line under `## Log` — the verdict and a link to the task logbook:

  ```
  ### 2026-08-26
  - B-scan: B=4 flattens the wall without moving σ(α_s) (0.547 → 0.548) —
    (evidence: studies/np-wall-local-minima/260826-b-scan/LOGBOOK.md)
  ```

- **Do not copy the worker's numbers, tables, or plots up into your logbook.** Link to the
  task logbook. `studies/np-wall-local-minima/LOGBOOK.md` reached 300 KB by absorbing every
  worker's detail; that is the failure mode this layout exists to prevent.
- Promote to `## Findings` only once a result is settled, as one line with the task logbook
  as evidence. Promote a choice to `## Decisions` with its reason.
- A finding that holds beyond this study → `knowledge/`, not a longer logbook.

If a worker reports something that contradicts a settled decision, say so in the log
entry — don't silently overwrite the old conclusion.

## 4. Before you stop

1. Refresh **START HERE**: current state, the single most important next action, what's
   blocking. This is the one non-optional step — it's what makes the next session cheap.
2. Bump `updated:` in the frontmatter, and `status:` if it changed.
3. Nothing to publish. The web page reads the files live; a logbook edit is visible on
   reload, and a new task dir appears in the sidebar as soon as the worker creates it.

## 5. The web view

`https://submit.mit.edu/~lavezzo/alphaS/studies/#<slug>` — the study logbook rendered, with
its tasks in the sidebar. `#<slug>/<YYMMDD>-<task>` for a task, and each task links to its
own plot gallery.

**Every figure belonging to this study goes in a task directory** — `save_plot(outdir=<task
dir>, ...)` — and never in a hand-rolled `~/public_html/alphaS/YYMMDD_something/`. The
`plots ↗` link points at the task directory, so that is the only place a figure sits one
click from the logbook entry that explains it. Tell workers this when you brief them; it
applies to a polished standalone deliverable page just as much as to a scratch check, and
subfolders are fine (the gallery lists them).

`~/public_html` has **no authentication**. The symlink publishes everything in the study
dir, now and later. So: no unblinded numbers, no credentials, no raw session transcripts,
and bulk outputs stay on ceph with a path in the logbook.
