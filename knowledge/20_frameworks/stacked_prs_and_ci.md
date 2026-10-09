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
- WMass/rabbit issue #173 — the CI unit-test matrix is hand-maintained, so a
  test file not listed in it never runs anywhere (~137 of ~152 tests were dead).
  A PR that adds tests goes green either way. **Always add a new test file to
  the `unit-tests` matrix in the same PR.**
