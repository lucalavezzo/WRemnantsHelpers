# Stacked PRs on WMass/rabbit, and the CI trap

Written after landing the five-PR blinding/saturated stack (#159, #171, #161,
#170, #172) on 2026-09-14. See `studies/rabbit-pr-stack/LOGBOOK.md`.

## The trap: a stacked PR gets NO CI, and it looks fine

`.github/workflows/main.yml` is triggered by

```yaml
on:
  pull_request:
    branches: [ main ]
```

so a PR whose **base** is anything other than `main` never runs CI. It does not
fail — the checks list is simply **empty**, which reads like "nothing to report"
rather than "nothing ran". Every PR in a `stack/*` layout is silently untested
until it is retargeted.

**Worse: retargeting alone does not fix it.** Changing a PR's base fires the
`edited` activity type, which is not in the default `pull_request` trigger set
(`opened`, `synchronize`, `reopened`). The workflow still does not run. The PR
has to be **closed and reopened** (or pushed to) to trigger it.

Do not mistake a pending `review` check for CI: that is the hodor review bot
(`hodor-review.yml`), which has its own trigger and runs regardless of base.

### If stacking again

Add `stack/**` to the trigger's branch list **before** opening the stack, or
accept that each PR is tested only once it becomes the head of the queue.

## When stacked bases are worth it

They are a review-time tool, not a merge-time one.

- **For**: each PR shows only its own diff. Without them a child PR shows every
  ancestor's diff baked in (ours were showing 416 extra lines), and the reviewer
  re-reads the parent in every child. The reviewer explicitly said the restack
  "made this much easier to read".
- **Against**: no CI (above), and the base branches live in the shared repo.

So: stack during review, **unwind before merging**. Retargeting to `main` needs
no rebase if the branches already sit on current `main` — it is a base change
only, nothing force-pushed. Diffs become cumulative again, which resolves itself
as each one lands.

**Order matters:** retarget the child BEFORE deleting its base branch. Deleting
a branch that a PR points at auto-closes that PR.

## Mechanics

- `git -c credential.helper='!gh auth git-credential' push origin ...` — the
  `origin` remote is HTTPS with no stored credentials; the fork remote is SSH
  and works directly.
- Commit from **inside the container**: `.githooks/pre-commit` runs `pylint`,
  which is not on the login node.
- CI lints with `black`, `isort`, and `flake8` **restricted to pyflakes F-codes**
  — so `E501`/`E203` noise is not a gate, but `black` is.
- Do not develop in `WRemnants/rabbit`: that checkout is used for production
  fits. Use a throwaway `git worktree`.

## Related

- `knowledge/20_frameworks/durable_code_comments.md` — the comment convention
  that came out of the same review.
- WMass/rabbit issue #173 — the CI unit-test matrix was hand-maintained, so a
  test file not listed in it never ran anywhere (~137 of ~152 tests were dead).
  *(Fixed on main by 2026-10-19: CI now collects `tests/` and runs every collected
  file in its own process, 95d985d; `tests/test_ci_registration.py` fails on an
  uncollectable file. No matrix entry needed any more.)*

## PR readiness, and CI traps seen on rabbit #194–#196 / WRemnants #732–#739 (2026-10-17 → 10-20)

Source: `studies/ct18z-nominal-fits/261017-wremnants-pr-split/`, `261020-pr-shepherd/`.

- **Readiness rule (Luca, 2026-10-18).** Open every PR as DRAFT. Mark it ready only when (1) every CI check is green
  on the CURRENT head, including the hodor `review` job, and (2) every bot finding and human thread is answered and
  resolved. A rebase or push that re-opens either sends it back to draft.
- **hodor cannot review a WRemnants PR from a fork.** `hodor-review.yml` runs on `pull_request_target`, and
  `actions/checkout` refuses fork code there ("Refusing to check out fork pull request code"), so `review` is red on
  every fork PR. Decision (Luca): push WRemnants PR branches to WMass/WRemnants itself and open from there (#736–#739).
  rabbit's hodor does review fork PRs.
- **A red `review` can be infrastructure.** Seen: `bun install` ENOENT copying a package from the runner cache
  (WRemnants run 39242966057), and hodor hanging 6 h on its own `find /` (rabbit #194). Read the log; re-run it.
- **rabbit CI: never `gh run rerun --failed`.** Downstream jobs then read tensors that `copy-clean` already deleted
  (`FileNotFoundError ... test_tensor.hdf5`, run 39381088449 attempt 2). Re-run the whole workflow.
- **Known flake:** `test_snapshot.py::test_sigterm_writes_a_snapshot_before_the_process_dies` asserts 15 s wall
  clock; 16.3 s on a loaded runner. Re-run, not a finding.
- **Local rabbit suite: one pytest process per file**, as CI does (`run_suite_per_file.sh` in `261020-pr-shepherd/`).
  A single `pytest tests` aborts (Fatal Python error) in the mcstat tests: XLA keeps every compiled fitter mapped and
  the suite exceeds `vm.max_map_count` (95d985d's message).
- **WRemnants lint CI never checks paths containing "rabbit"** (`scripts/rabbit/**`, `rabbit_theory_helper.py`): its
  isort `--skip`/flake8 `--exclude` patterns match any path component and black's regex any substring. Lint those
  files explicitly (container tools; `wremnants_ci_linting` in memory has the command).
- **Build upstream-bound branches as squashed commits from the final tree, never from history**, when the history ever
  held something private: the ASWZ lattice data were committed and later deleted on the #715 branch (44f8a5c0,
  b14f84f4, 3ef3efb9 → 1b3732bb, 1bc2bbaa) and remain public on the fork and in WMass `refs/pull/715/head`.
- **Squash before rebasing a PR whose later commit removes code an earlier one adds** (#196: 3 commits → 1ecae8a),
  or the per-commit rebase resolves conflicts in dead code.
