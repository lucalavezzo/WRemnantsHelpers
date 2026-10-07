---
name: study
description: Run a study as an orchestrator — start or resume studies/<slug>, dispatch study-worker subagents onto scoped tasks, keep the study LOGBOOK.md as the campaign record, have its standalone SUMMARY.md written at major updates and at close, and publish it to the webdir. Use when starting or picking up a study, when delegating a piece of analysis, when asked "where are we on <study>", or when asked to summarize or close a study.
---

# Orchestrating a study

You are the orchestrator of one study. A team is **one orchestrator + N workers on one
study**: you hold the plan and the narrative, workers do the tasks and each keeps its own
logbook under yours.

This file holds **process**. The **state** lives in `studies/<slug>/LOGBOOK.md`. Keep that
split: don't copy state into here, don't copy process into the logbook. (Same split as the
`fit-queue` skill, which owns fit-campaign process.)

A study has two documents with two audiences:

| | `LOGBOOK.md` | `SUMMARY.md` (+ `SUMMARY.pdf`) |
|---|---|---|
| reader | the next session, and anyone auditing a number | a member of the analysis who was not in the study |
| content | everything: attempts, numbers, commands, dead ends | why, what we did, findings, what changed, conclusions |
| written | continuously, every session | at major updates and at close (§4) |
| length | unbounded | one to two pages |

The logbook is a superset of the summary. The summary never holds a number the logbook
doesn't.

## Who does what, when

| when | who | what |
|---|---|---|
| start / resume | you (`study` skill) | read SUMMARY → START HERE → task START HEREs; `webpublish_study.sh` |
| a piece of work | `study-worker`, one per task | owns `<YYMMDD>-<task>/`, returns a ≤15-line verdict |
| a fit is launched or finishes | `fit-queue` skill | queue, warm starts, results views |
| worker returns | you | one dated `## Log` line + link; promote to Findings/Decisions once settled |
| major update, or asked (`/summarize`) | `study-summarizer` | writes/refreshes `SUMMARY.md` + PDF |
| result leaves the room (collaborators, AN, meeting) | `physics-reviewer` (read-only) | checks the task logbook *and* the SUMMARY |
| close | summarizer → reviewer → `knowledge-curator` → you | §6 |
| end of every session | you | refresh START HERE, bump `updated:` |

## 1. Start or resume

```
studies/<slug>/
├── LOGBOOK.md            # yours
├── <YYMMDD>-<task>/      # one per delegated task, worker-owned
│   └── LOGBOOK.md
└── scripts/ QUEUE.md …   # study-wide, unchanged
```

**Resuming** — read in this order and stop:

0. `studies/<slug>/SUMMARY.md`, if there is one: the whole study in two pages. Note its
   `covers:` date; anything in the log after it is not in the summary yet.
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
  the settled decisions it must not contradict (pointing it at `SUMMARY.md`, when one
  exists, is the cheapest way to hand over the context),
- explicitly **what not to redo**, and what's out of scope.

A worker's context is fresh. Anything you don't pass, it either re-derives at cost or gets
wrong.

**Parallel is fine** — several workers at once, each on its own task dir. That is safe
precisely because workers never write your logbook. Do not give two workers the same task
dir.

Use `physics-reviewer` (read-only) on any result that will be quoted to collaborators, go
into the AN, or become a `knowledge/` note. Use `knowledge-curator` when closing the study
(§6).

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

## 4. The summary

`studies/<slug>/SUMMARY.md` is the standalone write-up of the study: why it was opened,
the driving questions, what was done, the findings with their figures and tables, what it
changed (code, defaults, cards, `knowledge/`), and the conclusions and open items. Its
audience is an analysis member who knows the analysis and the code but not this study.
One to two pages. The template is `studies/_TEMPLATE/SUMMARY.md`, and the writing rules
live in `.claude/agents/study-summarizer.md`.

**When.** Not after every task. Write or refresh it:

- **at close**: always, before `status: done`;
- **on request**: Luca asks for a summary or write-up;
- **at a major update**: a Findings entry that changes the study's answer, a Decision that
  changes analysis code, defaults or cards, or a result about to go to collaborators or a
  meeting. If you're unsure whether something counts, ask Luca, or offer to write it.

**Who.** Dispatch the `study-summarizer` agent with the target (`studies/<slug>`) and the
occasion. It reads the logbooks cold, the way the audience will, and it keeps your context
free. For a small study you may write it yourself, under the same rules. Either way it
also builds `SUMMARY.pdf` (`scripts/summary_pdf.py <slug>`), and the viewer then shows the
summary as the study's front page, with the logbook one tab away.

**After.** Read it. Its `UNTRACED / INCONSISTENT` line names logbook problems: fix them in
your logbook or put them in front of Luca. Log one dated line ("summary refreshed, covers
through …"). If the summary is going out to collaborators, run `physics-reviewer` on it
first.

**A task gets its own `SUMMARY.md`** only when it is really a sub-study: several sessions,
several results, or something that will be shown on its own. Dispatch the summarizer on
`studies/<slug>/<YYMMDD>-<task>`. An ordinary task's `## Result` is its summary already.

## 5. Before you stop

1. Refresh **START HERE**. It is now a short resume block for the next session (state,
   next action, blocking, what's running, how current the summary is), not the study's
   narrative, which is the summary's job. This is the one non-optional step, because it's
   what makes the next session cheap.
2. Bump `updated:` in the frontmatter, and `status:` if it changed.
3. If the session produced a major update (§4), write or refresh the summary now, or say
   in START HERE that it is stale.
4. Nothing to publish. The web page reads the files live; a logbook edit is visible on
   reload, and a new task dir appears in the sidebar as soon as the worker creates it.

## 6. Closing a study

1. `study-summarizer` writes the final `SUMMARY.md` + PDF.
2. `physics-reviewer` reviews the summary, together with the task logbooks it cites. Fix
   whatever blocks, and refresh the summary if needed.
3. `knowledge-curator` promotes what generalizes into `knowledge/` and the memory index.
4. You set `status: done` in the logbook and the summary, and log the close with a link
   to the summary.

## 7. The web view

`https://submit.mit.edu/~lavezzo/alphaS/studies/#<slug>` — the study rendered, with its
tasks in the sidebar. `#<slug>/<YYMMDD>-<task>` for a task, and each task links to its own
plot gallery. Where a `SUMMARY.md` exists the page opens on it, with a Summary / Logbook
toggle (`#<slug>:logbook` links straight to the logbook), a `pdf` link, and a warning when
the logbook has moved past the summary's `covers:` date.

**Every figure belonging to this study goes in a task directory** — `save_plot(outdir=<task
dir>, ...)` — and never in a hand-rolled `~/public_html/alphaS/YYMMDD_something/`. The
`plots ↗` link points at the task directory, so that is the only place a figure sits one
click from the logbook entry that explains it. Tell workers this when you brief them; it
applies to a polished standalone deliverable page just as much as to a scratch check, and
subfolders are fine (the gallery lists them).

**A figure can go inline in a logbook, at either layer.** Markdown `![alt](<relative
path>)` — the viewer rewrites relative image paths against the logbook's own directory, so
a worker writes `![...](my_plot.png)` and you, from the study logbook, write
`![...](<YYMMDD>-<task>/my_plot.png)`. Optional, and not a box to tick: most entries need
no picture. But when a task's answer IS a plot, a bare path is a result nobody looks at, so
pull it into the page — and that is one of the few things worth copying up from a task,
because a picture is the cheapest possible summary. The rule against copying up is about
numbers and tables; it does not mean your logbook has to be text only. Keep the caveat
beside the image.

`~/public_html` has **no authentication**. The symlink publishes everything in the study
dir, now and later. So: no unblinded numbers, no credentials, no raw session transcripts,
and bulk outputs stay on ceph with a path in the logbook.
