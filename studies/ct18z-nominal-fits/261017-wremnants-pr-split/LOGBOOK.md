---
title: WRemnants PR #715 split + review
slug: 261017-wremnants-pr-split
study: ct18z-nominal-fits
status: done          # active | done | paused | abandoned
created: 2026-10-17
updated: 2026-10-19
owner: study-worker
---

# WRemnants PR #715 split + review

**Task:** How should WRemnants PR #715 (differentiable SCETlib prediction as a rabbit param model, branch
`scetlib-ad-param-model`) be split into smaller reviewable/mergeable PRs, and what does a code review of each
piece find?

---

## START HERE (status as of 2026-10-17)

- **Answer:** #715 can be split into 10 squashed, independently linted PRs (A–J; table in Result).
  A, B, C and J go straight to main; then D (the core param model, about 4.0k lines after a doc trim
  that changed no code); then E (NP wall), F (lattice), H (validation scripts) and I
  (cache_to_theorycorr); then G (NP plots). All are built locally and nothing is pushed. **Blocker:
  the ASWZ lattice data sit in #715's public history**; the split avoids it, but purging it is
  Luca's decision. Tests: NP wall 122/122, lattice 38/38, core smoke fit converged.
- **Next action:** CI is green on #732–#735 apart from the hodor `review` job, which refuses fork PRs. Get reviews and merge C (#733) before D (#735). After #735 merges, rebase and open E, F, H and I, then G.
- **Blocking on:** reviewers; sign-off from the theory-correction producers on #734.
- **Running:** nothing.

---

## Log

### 2026-10-20 (orchestrator note)
- The first-wave PRs were reopened from WMass branches: #732–#735 → #736 (A), #737 (C), #738 (J), #739 (D); #736 merged, #737–#739 ready. Continued in [261020-pr-shepherd](../261020-pr-shepherd/LOGBOOK.md).

### 2026-10-18
- Luca's decisions:
  - (a) the lattice data stay in #715's history, untouched;
  - B (`ad-theorycorr-sidecars`) is DROPPED and stays local only, because the AD card excludes the
    pdfvars/pdfas nuisances;
  - #715 is closed once D is open.
- Pushed A, C, J and D to the fork and opened them against WMass main, with fresh descriptions:
  - A: [#732](https://github.com/WMass/WRemnants/pull/732)
  - C: [#733](https://github.com/WMass/WRemnants/pull/733)
  - J: [#734](https://github.com/WMass/WRemnants/pull/734), whose body asks for sign-off from the
    theory-correction producers
  - D: [#735](https://github.com/WMass/WRemnants/pull/735), which contains #733's commit; its body
    says to review the top commit only and to merge after #733.
- Closed #715 with a comment listing the new PRs and the follow-ups (E, F, G, H, I after #735).
- CI: the `review` check (hodor bot) fails on all four. That is infrastructure: it refuses to check
  out fork PRs under `pull_request_target`. The `linting` job is queued on the self-hosted runner.
- CI finished on all four PRs: **23 checks pass and 1 fails** on each. Linting passes, and so does
  every analysis job (gen, dilepton, dilepton-unfolding, dilepton-mll, alphas-z-histmaker, wlike,
  w-analysis, lowpu-w, lowpu-z).
  - The one failure is `review`, the hodor AI-review workflow (`hodor-review.yml`), which runs on
    `pull_request_target`. Its log says: "Refusing to check out fork pull request code from a
    'pull_request_target' workflow".
  - So it is infrastructure, not a code failure, and not exactly an approval gate either: the bot
    simply cannot review a PR from a fork.

### 2026-10-19
- **#736 (A).** Hodor flagged a P3: `--decorrRebin -2,0,2` was taken as an option.
  - Fixed in cd5f1ba2 by extending the argv normalization used for `--axlim`/`--presel`.
  - Re-review: "Patch is correct". CI green. Marked ready.
- **#738 (J).** Hodor: "Patch is correct". CI green. Marked ready; its body asks the
  theory-correction producers for sign-off.
- **#737 (C).** Hodor P3: `--responseGenBinning` was silently ignored without `--unfolding`; it
  now raises.
- **#739 (D).** Hodor P2: on the default `--responseMatrixGenBinning unfolding` path, R summed
  over gen acceptance but was divided by the acceptance-filtered `prefsr` gen total.
  - The fix lives in C, since that is where `response_matrix.py` is: `DEFAULT_GENTOTAL =
    "prefsr_full"` (60 < m < 120, no acceptance cut, same gen axes).
  - On the full Z histmaker output (`261012_Z_histmaker_ct18z_y5pairs`), N_gen(prefsr_full) =
    N_gen(prefsr) in every in-range gen bin and R is unchanged, so the numbers do not move there.
- Both C fixes are in c01b1dc4. D was rebased onto it (head 34f53134) and force-pushed with lease
  to `upstream/ad-pm-core`. I replied on both PRs with the SHA and re-dispatched hodor.
- **CI failure on C and D:** both failed the `w-bsm` job, with NaN in the
  `WtoNMuMass50_mixing` systematic in the fake estimate (histselections). C and D do not touch that
  code, A and J pass the same job on the same base, and C's `add_xnorm_histograms` change is a no-op
  for `selection=None` callers. Treated as flaky; the failed jobs were rerun. The new heads rerun the
  full CI anyway.
- The local branches E–I are still based on the old D (f13663b3). Rebase them onto 34f53134 before
  they are opened.

### 2026-10-18 (later)
- Luca: the review bot fails on fork PRs, so the PRs move into WMass itself. Pushed the four branches
  to `upstream` (WMass/WRemnants) under the same names, after checking that none existed. Reopened
  them as **drafts**:
  - A: [#736](https://github.com/WMass/WRemnants/pull/736)
  - C: [#737](https://github.com/WMass/WRemnants/pull/737)
  - J: [#738](https://github.com/WMass/WRemnants/pull/738)
  - D: [#739](https://github.com/WMass/WRemnants/pull/739), whose body now points at #737
- Closed #732–#735 with a one-line pointer to the replacements, and noted the new numbers on #715.
  Deleted the four fork copies of the branches (`origin`).
- Luca's rule: a PR is marked ready only when CI is green on its current head (including the
  `review` bot job) AND every bot and human comment is resolved. D stays a draft at least until C
  is merged or reviewed.
- The hodor `review` job skips drafts (`if: !draft`, see `hodor-review.yml`). It was therefore
  started by hand: `gh workflow run hodor-review.yml --ref main -f pr_number=<n>`, one run each for
  736–739.

### 2026-10-17
- Five read-only reviews returned (core, NP wall, lattice, scripts, framework); their findings are folded
  into Result. Every claim used was re-checked here before acting:
  - `blind_additive` is not read anywhere in rabbit 2d9f380, where POI blinding is additive with
    `blind_additive_scale`;
  - the default correction `scetlib_dyturbo_CT18Z_N3p0LL_N2LO` has Q edges [10, 60, 120], while all
    LatticeNPLambda4Bugfix* corrections have [60, 120];
  - the lattice-data commits are as stated below;
  - none of the B correction files are in wremnants-data `master` (789d061) or at the pinned commit.
- `--presel`: a toy hist with 6 entries, of which 1 is overflow and 1 underflow, cut at
  [1, last edge]. Results: the PR version gives 3 entries for the sliced form and 3 for `:sum`; the
  fixed version gives 4 and 4; main gives 6, i.e. the cut is a no-op on totals
  (`scratchpad/presel_test.py`).
- `response_matrix.py` rewritten (359 → 165 lines). `load_R` old vs new on
  `/ceph/.../261012_Z_histmaker_ct18z_y5pairs/mz_dilepton_..._adcorrAV_...ct18zy5pairs.hdf5`: R, N_gen,
  axes and shapes are **bit-identical** for both `nominal_prefsr_yieldsResponse`
  (40×10×8×8×70×11) and `nominal_prefsr_yieldsUnfolding` (40×10×8×8×21×5).
- `lambda_central.py` became `corr_config.py`, which writes only `scetlib_corr_config`. The recorded
  metadata is **identical** to the PR's for 4 corrections × applied/not
  (adcorr, FranksValsVars, default CT18Z, pdfvars).
  - A reviewer suggested raising on "several resummed basenames". That would have broken it: the
    default W correction combines W+ and W- (two resummed runcards), so the old skip-the-proc
    semantics were kept.
- NP wall test on `ad-np-constraints`: 122 PASS, 0 FAIL. The PR had 128; the 6 removed checks
  compared against git revision 2f1c3df4.
- Lattice test on `ad-lattice-term`, run with SCETlib `/work/.../scetlib-gamma-nu-points` and the
  pdf62_y35_260921_y25 runcard: **38 PASS, ALL PASS**.
- Doc trim by four agents, done in scratch copies. Each file was checked `ast_same.py` = identical
  AST minus docstrings before being applied.
  - Library narrative: param_model 37→24 %, params 54→31 %, xsec_backend 41→28 %,
    scale_envelope 52→33 %, np_damping_wall 39→20 %, lattice_cs_term 21→14 %; scripts ~20→12 %.
  - README rewritten (230 → 94 lines). The fitted α_s value that the PR's README quoted was removed.
- All ten branches pass the CI-equivalent lint, and all merge together cleanly
  (`/work/submit/lavezzo/wrem-pr-merge`, detached). The union is 32 files, +10532/−45, against the
  PR's 36 files, +14189/−54.
- Found while linting: CI's `flake8 --exclude=...,rabbit,...` and black's `--exclude '...|rabbit|...'`
  match ANY path containing "rabbit". So `scripts/rabbit/**` and `rabbit_theory_helper.py` are never
  linted by CI; every changed file here was linted explicitly.
- End-to-end smoke test of the split code. Test checkout detached at `ad-validation-tools`, so it
  contains C + D + H. SCETlib gamma-nu-points build; cache `pdf62_y35_260921/clean_smoke12`
  (12 bins, 53 parameters); Asimov.
  - `backend_check.py`: **all checks passed**. The anchor re-evaluation is bit-identical; finite
    differences agree to 4e-9; the Hessian is exactly symmetric; the gen-fold sum rule holds exactly.
  - `make_debug_card.py`: wrote a 12-bin card.
  - `rabbit_fit.py -t -1 --paramModel ...SCETlibADParamModel gen_level=1 scale_envelope=0`:
    converged, **edmval 6.2e-29**, fitresults written.
  - The first attempt used the old `yext_probe_260916` cache. It failed on the cache format, as
    expected for a pre-v10 cache; it is not a code problem.
  - Logs: `scratchpad/e2e/e2e_smoke12.log`, in the session scratchpad, not kept. Parameter values
    were not inspected.
- Inventory: PR #715 head 74c7e3e3 (draft), 65 commits, 36 files, +14189/−54 vs upstream/main
  ebe4f4f7.
  - The last full CI run (10-15) was green, and a new run was queued today. There are no review
    comments and no reviews.
  - #701, the old scetlib_np model, is CLOSED (2026-09-28); none of it is on main, which is why
    `compare_to_np_model.py` is dead.
  - The PR's setupRabbit diff also reverted upstream's `writer_kwargs` shim (from commit 8e46936b),
    which is unrelated to the model. It is dropped from the split.
- rabbit submodule: upstream main is already at 2d9f380 (WMass #729), so the PR's rabbit bump drops out.
- Worktrees, all mine:
  - `/work/submit/lavezzo/wrem-pr-split` is the detached PR head, the read-only reference for the
    reviewers;
  - `/work/submit/lavezzo/wrem-pr-build` is where the split branches are built;
  - `/work/submit/lavezzo/wrem-pr-test` is a detached checkout for the test runs;
  - `/work/submit/lavezzo/wrem-pr-merge` is the all-branches test merge.

  The main checkout (`~/alphaS/WRemnants`, which holds someone else's edits) was not touched,
  except that the new branches live in its `.git`.
- Five read-only review subagents were dispatched: core library, NP wall/constraints, lattice term,
  scripts/tools, and framework (shared-file) changes.
- Lattice reviewer: the ASWZ data were COMMITTED in 44f8a5c0 / b14f84f4 (`scetlib_ad/data/*.npz|json`),
  modified in 3ef3efb9, and deleted in 1b3732bb / 1bc2bbaa. Those commits are on the public fork
  branch and in WMass `refs/pull/715/head`. Consequence: the split branches are built as squashed
  commits off upstream/main, never by cherry-picking history.
- Side incident: `git submodule update` in the build worktree started an LFS checkout of
  wremnants-data, 2.5 GB under `.git/worktrees/wrem-pr-build/modules/`. I killed it and removed
  that directory, which was mine.

---

## Result

**Caveats first.** Nothing was pushed and no PR was opened or closed. All branches are local in the
`~/alphaS/WRemnants` repo (worktree `/work/submit/lavezzo/wrem-pr-build`). Each was built as one
squashed commit from the PR's final tree (never from its history; see the lattice-data finding).
"Lint clean" means the exact `main.yml` isort / flake8 / black commands in the CI image (v67), plus
the same flake8 / black run explicitly on every changed file. CI's own lint never checks
`scripts/rabbit/*` or `rabbit_theory_helper.py` (see Findings). The doc trims were checked
mechanically: the AST minus docstrings is identical, so no code changed.

### Proposed split

Branch heads: A `92e717c6`, B `dfc42d2e`, C `e06e283e`, D `f13663b3`, E `a6d98817`, F `e5ead636`, G `a8e682df`,
H `ed1d07ba`, I `4ea2af86`, J `f02e358c`. All are in `~/alphaS/WRemnants/.git`; worktree `/work/submit/lavezzo/wrem-pr-build`.

Merge order: **A, B, C, J** go straight to main, independent of each other and of everything else.
Then **D** after C. Then **E, F, H, I** after D, in parallel. **G** goes after E. Every PR is opened
against `main`, so CI runs; a stacked base gets no CI (`knowledge/20_frameworks/stacked_prs_and_ci.md`).
A dependent PR shows its prerequisite's commit until that merges, and the reviewer is told to read
the top commit only.

| PR | branch (local) | content | +/− LOC | depends on | review status |
|---|---|---|---|---|---|
| A | `ad-setuprabbit-fixes` | setupRabbit `--presel` flow fix; `--decorrRebin` edge lists | +35/−3 | – | ready. **Behaviour change**: `--presel` cuts now actually apply (the `:sum` form was a no-op on totals on main) |
| B | `ad-theorycorr-sidecars` | TheoryHelper `_Corr` separator + pdfvars/pdfas sidecar lookup; 10 `theory_corr_weight_map` entries (LatticeNPLambda4Bugfix_FranksVals*) | +64/−18 | wremnants-data MR with the correction files | code ready; **the files are not in wremnants-data**; the MSHT20aN3LO `_pdfvars` entry has `renorm=True` where its LatticeNPCoarse siblings have none (intended?) |
| C | `ad-response-inputs` | mz_dilepton `--responseGenBinning theoryCorr` (default **none**); UnfolderZ response axes + gen total; `get_corr_grid_edges`; setupRabbit `--storeResponseMatrix`; `scetlib_ad/response_matrix.py` | +474/−17 | – | ready; R/N_gen bit-identical to the PR on a real 4.5 GB histmaker output |
| D | `ad-pm-core` | `SCETlibADParamModel` (param_model, params, xsec_backend, response, scale_envelope, corr_config, README) + histmaker anchor meta + styles groups + cache tools (build, extract_rules, backend_check, base runcard) | +4039/−6 | C | ready for review after the doc trim (library 4473 → 3140 lines, narrative 44 % → 27 %); smoke test below |
| E | `ad-np-constraints` | `np_damping_wall.py` (NPDampingWall C² wall, NPDomainConstraints) + its test | +1817 | D | test 122/122 PASS (TF + rabbit only) |
| F | `ad-lattice-term` | `lattice_cs_term.py` (ASWZ lattice CS-kernel χ²) + its test | +1346 | D (duck-typed on the model), SCETlib `gamma-nu-points` | test 38/38 ALL PASS (gamma-nu-points build); data read from the group area only |
| G | `ad-np-plots` | `np_function_plots.py` | +732 | E | ready |
| H | `ad-validation-tools` | compare_to_scetlib_run, validate_variations, validate_reco, make_debug_card, validation_plots | +1698 | D | ready (needs external SCETlib) |
| I | `ad-cache-to-theorycorr` | `scripts/corrections/cache_to_theorycorr.py` (makes the `_adcorr` corrections) | +905 | D | decision: keep standalone or fold into make_theory_corr |
| J | `ad-ptzgen-corr-binning` | `ptZgen_binning_corr` += 110, 130, 250 | +4/−2 | – | decision: changes the correction-production binning for everyone |

Removed relative to #715:
- **Dead or forensics code:** `compare_to_np_model.py` imports `scetlib_np`, which is not on main. Also
  `validate_variations_reco.py`, study forensics that always loads the CT18Z correction whatever
  `--corr` says.
- **Superseded runcard:** `conf/Z_CT18Z_N3p0LL_analysis.conf`.
- **Rabbit bump:** upstream main is already at 2d9f380.
- **Unrelated revert:** the PR's undoing of upstream's `writer_kwargs` shim in setupRabbit.
- **Provisional or tautological code:** `--responseGenPtVExtend` (provisional) and
  `check_gen_grid_vs_correction` (a tautology at its only call site).
- **Metadata with no reader:** the `scetlib_np_lambda_central` meta (only `scetlib_corr_config` is
  read), the `corr_generator` auxiliary entry, `blind_additive` (rabbit 2d9f380 never reads it), and
  `KNOWN_BAD_RESPONSE`.
- **Unused helpers:** `seven_point_scale_spec` / `three_point_mur_scale_spec` and
  `FrozenEnvelope.factor_np` / `to_dict`.

### Review: top findings

1. **BLOCKER, the private lattice data are in the PR history.** 44f8a5c0 and b14f84f4 added the ASWZ
   tables (`scetlib_ad/data/lattice_aswz_{inputs,data}.{npz,json}`), and 3ef3efb9 changed them.
   Later commits delete them, but the commits are on the public fork branch and in WMass
   `refs/pull/715/head`.
   - The split branches are squashed, so the data never reaches upstream history.
   - Purging what is already public means force-pushing or deleting the fork branch, and GitHub
     support for `refs/pull/715`. That is **Luca's decision**, and possibly the ASWZ authors should
     be told.
2. **BLOCKER (fixed in C): `--responseGenBinning` defaulted to `theoryCorr`.**
   - Every `mz_dilepton --unfolding --poiAsNoi` run gained two large histograms and extra event-loop
     work.
   - With the default correction `scetlib_dyturbo_CT18Z_N3p0LL_N2LO`, whose Q edges are [10, 60,
     120], the response gen total silently got the cut 10 < m < 120 and was mis-normalised.
   - Fix: default `none`, and refuse a correction with more than one Q bin. All
     LatticeNPLambda4Bugfix corrections have a single [60, 120] bin.
   - **Luca's histmaker commands now need `--responseGenBinning theoryCorr`.**
3. **BLOCKER (fixed in A): the PR's `--presel` fix dropped the overflow** when the upper bound is the
   last edge, which `get_hist_slice_upper` defines as inclusive. Verified on a toy hist, then fixed.
4. **Tests that only work on the PR branch** (fixed):
   - The NP-wall test `git show`ed commit 2f1c3df4.
   - The lattice test `git show`ed 3ef3efb9, the leaked tables.
   - The lattice test also defaulted `--conf` to a personal ceph cache, compared against a logged
     study fit, and hard-coded the MIT path and fqdn.
5. **Not upstream material, removed:**
   - real-data postfit λ values and α_s shifts in units of σ in `np_damping_wall` comments;
   - a fitted α_s central value in the README;
   - personal paths (conf, test, error messages, the `agent_setup.sh` hint);
   - about 60 references to WRemnantsHelpers `studies/`, `knowledge/` and run labels.
6. **Docs contradicted the code** (fixed in the trim):
   - "all three resumTransition* frozen": only 1 and 3 are;
   - priors "off by default": they default to True;
   - α_s "in physical units": it is a unit nuisance of width 0.002;
   - "7-point" envelope: the default is 3 points;
   - "local quadratic" derivative injection: retired.
7. **Style.** The narrative share was 40–55 % against about 4 % in upstream modules. After the trim:
   param_model 24 %, params 31 %, xsec_backend 28 %, lattice term 14 %, NP wall (see Log).
   **Still open:** about 25 `print`s instead of `wums.logging`, kebab-case CLIs where the repo uses
   camelCase, and some stale `help=` strings in `build_scetlib_ad_cache.py`.
8. **External dependencies a reviewer will ask about.**
   - The SCETlib `autodiff-sigmaul` branch, and for F the `gamma-nu-points` branch. They are not
     pinned or version-checked from WRemnants.
   - None of the B-referenced correction files are in wremnants-data: all 85 Lambda4Bugfix files are
     untracked local files.
   - `xsec_backend._load_with_raw_rules` copies SCETlib loader internals; it belongs in SCETlib.
9. **Design points for the lattice term.**
   - It finds the fitter by walking the call stack (`_find_fitter`) and uses private model
     attributes (`_p_base_anchor`, `core.tf_fn._sing`). An explicit rabbit hook would be cleaner.
   - It carries legacy options: `pert=live`, `nfscheme=evolve`, `Jbt`, `direct_nf`.
10. **Small correctness issues, open:**
    - With `smallb=0`, the tanh_6 discriminant conditions still penalise λ2ν < 0 even when λ4ν ≥ 0
      (minor; harmless at the default `smallb=1`).
    - The wall always uses the correction anchor, even when a fit runs `anchor_override`.
    - GenFold and the scale envelope assume the gen-axis order (qT, |Y|) without asserting it.

### Decisions for Luca

- (a) Purge the leaked lattice data from the fork branch and `refs/pull/715`, or not, and whether to tell
  the ASWZ authors.
- (b) Close #715 in favour of A–J, or force-push the fork branch to `ad-pm-core` and reuse #715 for D.
- (c) Open a wremnants-data MR for the LatticeNPLambda4Bugfix and `_adcorr` corrections. Without it B is
  inert and the model cannot be run from upstream data.
- (d) The datacard auxiliary group and meta-key names (`scetlib_np`). Kept for card compatibility; rename
  them to model-neutral names?
- (e) J (binning) and I (cache_to_theorycorr) need sign-off from the theory-correction producers.
- (f) H: keep the validation scripts in WRemnants, or move them to WRemnantsHelpers?
- (g) Take the doc trim as is. It cuts about 2000 lines of narrative, which the original PR branch still holds.

---

## Findings

1. The ASWZ lattice data were committed and later deleted on the #715 branch: 44f8a5c0 and b14f84f4
   added them, 3ef3efb9 changed them, 1b3732bb and 1bc2bbaa deleted them. They are publicly reachable
   on the fork and in WMass `refs/pull/715/head`. Upstream-bound branches must be squashed. —
   (evidence: `git log --diff-filter=AD upstream/main..74c7e3e3 -- wremnants/postprocessing/scetlib_ad/data`)
2. WRemnants CI lint never checks paths containing "rabbit": `scripts/rabbit/**` and
   `rabbit_theory_helper.py`. Its `--exclude`/`--skip` patterns match any path component, and
   black's regex matches any substring. Lint those files explicitly. — (evidence:
   `.github/workflows/main.yml` linting job). Generalizes; should go into `knowledge/` (memory
   `wremnants_ci_linting.md`).
3. On main, `setupRabbit --presel <axis>:sum lo hi` does not cut: the bare slice moves the content
   into the flow bins, and `hist.sum` re-adds it. Fixed on `ad-setuprabbit-fixes`. Changes results
   for anyone using `--presel`. — (evidence: `scratchpad/presel_test.py` toy, Log)
4. A response gen total cut on the correction's Q range is only valid for a single-Q-bin correction.
   The default CT18Z correction has two Q bins ([10, 60, 120]), which the PR's default-on
   `--responseGenBinning` would have mis-normalised silently. — (evidence: Log)
5. `blind_additive` in the PR's param model is dead in rabbit 2d9f380. α_s, a unit nuisance of width
   0.002, is blinded additively by default with `blind_additive_scale = 1`. — (evidence:
   `rabbit/rabbit/blinding.py`)

---

## Open questions

- The PR #715 description is stale: it says κ_R is profiled, transition points have the wrong sign,
  and the rabbit bump is needed. The new PRs need fresh descriptions. The split branches' commit
  messages are written to serve as their first drafts.
- Not done here: a full-size reco fit from the merged split tree, as a regression against a
  production fit. That is one CPU fit of hours on the 770-bin cache. Worth doing before D is marked
  ready.
- Stale `help=` strings in `build_scetlib_ad_cache.py` were left as they are, because they are code
  and outside the doc-only trim: `--subset` mentions the removed `--card`, `--no-muf`/`--no-pdf`
  mention the retired muF pair, and `--fork-selftest` points to the absent `compare_caches.py`.
  `param_model` error strings still say "7-point".
