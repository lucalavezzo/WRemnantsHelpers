# studies/

One folder per investigation. A study folder holds **everything** for that study
— its code, its artifacts, and its logbook, together:

```
studies/<slug>/
├── LOGBOOK.md          # the study record (copied from _TEMPLATE/LOGBOOK.md)
├── <YYMMDD>-<task>/    # one folder per delegated task
│   ├── LOGBOOK.md      # the task record (copied from _TEMPLATE/TASK_LOGBOOK.md)
│   └── *.png, *.pdf    # its plots, via plot_output.save_plot
├── scripts/            # study-specific code
└── *.png, *.pdf …      # study-level plots / outputs
```

`<slug>` is 2–4 kebab-case words (e.g. `physical-lambda`, `xterm-closure`).
Study-specific code lives here; general-purpose tools go in `../scripts/`,
standard recipe chains in `../workflows/`, and executables in `../bin/`
(see `../AGENTS.md` for the full layout and tooling order).

## The logbook (soft contract)

Every study keeps a `LOGBOOK.md`. The **START HERE** block is the contract; the
rest is optional detail.

1. **Resuming a study** → open `LOGBOOK.md`, read **START HERE** first (current
   state · next action · what's blocking). Don't re-derive what's recorded; don't
   re-open settled Decisions.
2. **New study** → `mkdir studies/<slug>` and copy `_TEMPLATE/LOGBOOK.md` into it;
   fill the frontmatter and `Goal`.
3. **While working** → append dated bullets under `## Log`; promote durable
   conclusions to `## Findings` and choices to `## Decisions`.
4. **Ending a session** → refresh **START HERE** and bump `updated:`. This is the
   one non-optional step — it's what makes the next session cheap.

A finding that generalizes beyond the study belongs in `../knowledge/`
(*"what's true"*), not the logbook (*"what we're doing"*).

## Tasks

A study is usually run by an orchestrator that delegates pieces of it to workers. Each
delegated piece gets its own folder, `<YYMMDD>-<task-slug>`, with its own `LOGBOOK.md`
copied from `_TEMPLATE/TASK_LOGBOOK.md`.

- **A task folder is any subfolder containing a `LOGBOOK.md`** — that's how tools find
  them. So `scripts`, `logs`, `slides`, `docs`, `inputs`, `sessions` and `__pycache__` are
  never task names.
- **The worker writes only inside its own task folder**; the orchestrator owns the study
  `LOGBOOK.md` and adds one dated line per finished task, linking to it rather than copying
  its numbers. That keeps the study logbook short and lets several workers run at once.
- Plots go in the task folder via `plot_output.save_plot`, which also leaves the gallery
  and the per-plot provenance log.

## On the web

`scripts/webpublish_study.sh <slug>` symlinks a study into the webdir; it is then live at
`https://submit.mit.edu/~lavezzo/alphaS/studies/#<slug>`, tasks included, with no build
step. `~/public_html` has no authentication — see `../AGENTS.md` for what must therefore
never go in a study folder.
