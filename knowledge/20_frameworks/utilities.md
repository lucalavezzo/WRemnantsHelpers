# Useful Utilities

## Scope
Repo-provided helpers that come up frequently when reverse-engineering or inspecting outputs.

## `print_command` — see how an output file was produced
- `setup.sh` defines the alias `print_command` → `python ${WREM_BASE}/scripts/inspect/print_command.py`.
- Pass any WRemnants output (`.root`, `.pkl.lz4`, `.hdf5` datagroup, fit result, etc.) and it prints the exact command stored in the file's `meta_info`.
- Flags: `--timestamp`, `--hash` (git hash at production time), `--diff` (git diff at production time), `-a/--all` (dump full metadata).
- This should be the default first move when reverse-engineering an existing output before re-running anything.

## Last Updated
- 2026-05-01

## Source
- Migrated from `AGENTS.md` (2026-05-01).
