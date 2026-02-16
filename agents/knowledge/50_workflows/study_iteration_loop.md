# Study Iteration Loop

## Scope
Standard operating loop for `agents/studies/<topic>/` work.

## Required Study Files
- `README.md`
- `runlog.md`

Optional:
- `results_index.md`
- `slides/outline.json`

## Canonical Loop
1. Implement requested code/config changes.
2. Run workflow end-to-end with fresh unique tag/postfix.
3. Inspect outputs directly (plots and/or key printed values).
4. Update study `README.md` and `runlog.md` immediately.
5. Promote stable lessons to `agents/knowledge/`.

## Rules I Should Follow
- Add each new check/hypothesis to study notes before running.
- Update that same entry with `answered`, `partial`, or `open` right after results.
- Keep guiding questions near top of study `README.md`.

## Last Updated
- 2026-02-16

## Source
- `AGENTS.md`
- `agents/knowledge/10_environment/runtime_bootstrap.md`
- `agents/studies/z_bmass_uncertainty/README.md`
