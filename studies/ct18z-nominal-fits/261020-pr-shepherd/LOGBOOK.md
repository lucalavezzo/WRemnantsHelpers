---
title: PR shepherd (rabbit #194-196, WRemnants #736-739 + second wave)
slug: 261020-pr-shepherd
study: ct18z-nominal-fits
status: paused        # active | done | paused | abandoned
created: 2026-10-20
updated: 2026-10-20
owner: study-worker
---

# PR shepherd

**Task:** Can every open PR (rabbit #194/#195/#196, WRemnants #736–#739, then the second wave E–I) be brought to merged or READY (CI green on head incl. hodor, all comments resolved), with every choice needing Luca listed for him?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-10-20 14:40 UTC)

- **Answer:** merged: rabbit #194, WRemnants #736. READY (CI green on the head incl. hodor, every comment
  answered): rabbit #195 (4532443), #196 (1ecae8a); WRemnants #737, #738, #739. #195 and #196 merge cleanly together.
- **Next action:** when #739 merges, push and open the prepared second wave as drafts off main (E, F, H, I, K; G after
  E), dispatch hodor, and mark each ready once green. Branches are listed in the Log.
- **Blocking on:** maintainers merging #737, then #739; #738 needs the theory-correction producers' sign-off.
- **Running:** nothing.

---

## Log

<!-- Newest first. What was tried, what happened, why — with an evidence path. -->

### 2026-10-20
- 14:40: #195 full CI rerun 20/20 green → comment issuecomment-6293215588 → READY. All first-wave PRs merged or ready.
- Survey (09:xx): MERGED rabbit #194 (2026-10-19 17:56, merge df99d93) and WRemnants #736 (2026-10-19 18:46).
  rabbit #195/#196: open, not draft, CONFLICTING with main after #194 + #141 (mcstat-debias, which reworked
  `Fitter.minimize`, impacts signatures and the saturated sub-fit); David Walter on both: "Need to be rebased". No
  unresolved threads anywhere. WRemnants #737/#738/#739: mergeable/clean, CI green, hodor "Patch is correct" on each
  head, 0 threads; #737's `review` check was red from a later hodor run (11:12 on 10-19) that died in `bun install`
  (ENOENT copying @mistralai/mistralai from the runner cache) = infrastructure, not a finding → re-ran it: success.
- #195 rebased (tc-warmstart 4532443 on cf0d9ad): conflicts in `build_nonlinear_constraints`/`build_scipy_constraints`
  (now take both the #194 `transform`/chain-rule args and `hold_feasible`), `Fitter.minimize` (main split it into
  `minimize(mcstat_warm_start)` → `_minimize()`; now `minimize(warm_start=False, mcstat_warm_start=True)`, the caller's
  `warm_start` passed to both MC-stat legs), the saturated sub-fit and global asym impacts (`warm_start=True,
  mcstat_warm_start=False`). First time warm start + preconditioner coexist on one branch outside the validation
  build rabbit-all3 (SATWSPC used that).
- #196 rebased: squashed its 3 commits (e50a872, bf9dfb1, 8b3f180; the last one removes code the first adds, so a
  per-commit rebase would resolve dead code) into 1ecae8a on cf0d9ad (old head kept as local branch
  `face-held-impacts-pre-rebase`). Conflict: main's `impacts_parms(hess, cov=None, mcstat_extra_var=None)`; the
  face-held path now takes the same `cov`/`mcstat_extra_var` (main refuses `--constraints` with `--mcStatDebias`, so at a
  face they are always self.cov / None). black+isort clean on changed files (container).
- Full suites running in the container (worktree prepended): logs/pytest_195.log, logs/pytest_196.log (node load
  ~700, slow). Pushed both rebased heads with lease (#195 4532443, #196 1ecae8a), commented the resolutions
  (#195 issuecomment-6284946688, #196 issuecomment-6284946976), and moved both back to DRAFT until CI + hodor are green
  on the new heads (Luca's rule).
- Local suites: a single-process `pytest tests` ABORTS (Fatal Python error) in main's new mcstat tests on both
  branches under node load ~700. That is why main's CI now runs one process per file (95d985d). Reran CI-style with
  `run_suite_per_file.sh`: #195 and #196 both have every file passing (logs/suite_195.txt, logs/suite_196.txt,
  per-file logs in logs/s195, logs/s196).
- #196: CI 20/20 green + hodor "Patch is correct" on 1ecae8a, comment posted (issuecomment-6287568566) → READY.
- #195: hodor "Patch is correct" on 4532443; all-unit-tests failed ONCE on
  `test_snapshot.py::test_sigterm_writes_a_snapshot_before_the_process_dies` (elapsed 16.3 s vs the 15 s limit: a
  wall-clock assertion on the loaded runner, a main test this PR does not touch; passes locally on this head) →
  failed job re-run.
- #195 and #196 merge cleanly into each other (`git merge-tree`), so whichever merges second needs no rebase.
- (12:20, after an API rate-limit stop) #195 re-run: all-unit-tests PASS, but every downstream job failed with
  FileNotFoundError on test_tensor.hdf5 — `gh run rerun --failed` reuses the first attempt's tensors, which its
  `copy-clean` job had already deleted. Infrastructure; LESSON: rerun the WHOLE rabbit CI workflow, never `--failed`.
  Full rerun of run 39381088449 dispatched.
- Second wave prepared locally (worktree /work/submit/lavezzo/wrem-pr-build; nothing pushed): E/F/H/I rebased onto D
  34f53134, G onto E (old heads kept as `<branch>-pre261020`): E ad-np-constraints 325f9aae, F ad-lattice-term
  6412fb82, G ad-np-plots 6dd57702, I ad-cache-to-theorycorr 852b4afc (standalone, unchanged).
  H ad-validation-tools 51b6c2fe now holds only compare_to_scetlib_run.py, validate_reco.py, validation_plots.py;
  validate_variations.py + make_debug_card.py moved to WRemnantsHelpers scripts/scetlib_ad/ (Helpers commit d5508b5,
  not pushed). New K ad-response-group-rename 8ec6a087 (off D): aux group `scetlib_np` → `response_matrix`, the
  default reader falls back to the old name (toy check: new name, old name, missing → error, explicit custom group
  does not fall back). The `scetlib_np` aux group is the only `scetlib_np` key in C/D (no meta key carries it).
  Historical-comment scan of E–I diffs: nothing to cut. Numbers in F/G are published inputs (lattice-matching
  α_s(mZ) input, MAP22 parameters), not fit results.

---

## Result

No physics here; this is the PR state. Merged: rabbit #194, WRemnants #736. READY by Luca's rule: rabbit #195 (warm
start), #196 (face-held impacts); WRemnants #737 (C), #738 (J, still needs the producers' sign-off), #739 (D, merge
after #737). The rebases of #195/#196 onto main after #194 + #141 (mcstat-debias) were real semantic merges, not
just mechanical ones: `Fitter.minimize`/`impacts_parms` signatures changed, and on #195 the warm start and the
preconditioner now coexist for the first time. Both full suites and CI pass. The second wave is built locally and not
pushed: E, F, G, H (split per Luca: two tools moved to Helpers), I (standalone), and K (rename `scetlib_np` →
`response_matrix`, with a fallback for the old name).

<!-- The answer, and what it means physically. State comparability caveats BEFORE the
     numbers: blinding family, Asimov vs data, PDF/order swap, card or freeze-list
     difference, excluded points. Check the read against AN-25-085 / knowledge/, not
     against the code. A number without a physics read is not a finished task. -->

---

## Findings

<!-- One line each. A finding that generalizes beyond the parent study → tell the
     orchestrator; it belongs in ../../../knowledge/. -->

1. A single-process `pytest tests` of rabbit main (post-#141) aborts in the mcstat tests on our node; run one
   process per file, as CI does (`run_suite_per_file.sh`). — (evidence: logs/pytest_195.log, logs/pytest_196.log)
2. In rabbit CI, never `gh run rerun --failed`: downstream jobs then read tensors that `copy-clean` already deleted
   (FileNotFoundError test_tensor.hdf5). Rerun the whole workflow. — (evidence: run 39381088449 attempt 2)
3. `test_snapshot.py::test_sigterm_writes_a_snapshot_before_the_process_dies` has a 15 s wall-clock assert that can
   flake on a loaded runner (16.3 s seen). — (evidence: run 39381088449 attempt 1)
4. A hodor `review` red check can be pure infrastructure (`bun install` ENOENT from the runner cache); a re-run
   fixes it. — (evidence: WRemnants run 39242966057)

---

## Open questions

- K's aux-group name `response_matrix` is my choice (Luca asked for a model-neutral name); easy to change before
  the PR opens.
- Helpers commit d5508b5 (the two moved tools) is local, not pushed.
- D's `build_scetlib_ad_cache.py --subset` help still names `validate_variations`, now a Helpers tool, and its
  `R_info_from_auxiliary`/N_gen error strings still say 'prefsr' where C now uses `prefsr_full` (K fixes the first
  string only).
- Second-wave branches are on D 34f53134. If #739 is squash-merged instead of merge-committed, rebase them onto main.
