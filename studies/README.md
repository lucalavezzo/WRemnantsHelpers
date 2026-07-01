# studies/

One folder per investigation. A study folder holds **everything** for that study
— its code, its artifacts, and its logbook, together:

```
studies/<slug>/
├── LOGBOOK.md      # the progress record (copied from _TEMPLATE/LOGBOOK.md)
├── scripts/        # study-specific code
└── *.png, *.pdf …  # plots / outputs
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
