# scetlib_np validation-scripts reorganization — HANDOFF

updated: 2026-07-02

## START HERE

**Goal:** centralize the overlapping logic across the scetlib_np validation/diagnostic
scripts into ONE shared library + thin CLIs, covering the 5 capabilities below.

**STATUS 2026-07-02: pure-refactor reorg IMPLEMENTED + VERIFIED no-op (tests 1/2/3
physics-identical, TF-log noise only).** Physics/rebin fixes (the sensitive points) are
deliberately DEFERRED — see `SENSITIVE_POINTS.md`, to review with Luca.

**TWO user endpoints (agreed with Luca, collapse done):**
- `validate_agreement.py` — `--reference {card,histmaker}` (all datacard/histmaker checks)
- `sigma_gen_at_lambda.py` — theory-corr / arbitrary-λ / cardless (distinct)
Plus a `README.md` in the module documenting ALL user entry points (these two + the
analysis tools `fitresult_lambdas`/`np_function_plots`/… + the `validation/` dev checks +
the library modules).

**What was done (all in the working tree on `scetlib-np-param-model`):**
- `validation/agreement.py` (NEW, Layer 1): the shared reference-loading library —
  histmaker loaders/aligners (`load_nominal`/`align_nominal`/`load_gen_hist`/`align_gen`/
  `_parse_variation_label`/`validate_variation`) + theory-corr loader/projection +
  λ-tune resolvers (`resolve_base_lambda`/`assemble_tune`/`resolve_gen_axes`/
  `load_theory_corr_hist`/`theory_corr_projection`), moved VERBATIM from the two scripts.
- `validate_agreement.py` (NEW, option A): the unified CLI. `run_card` = the old
  `param_model_diagnostics` main body (build model, `run_card_diagnostics`); `run_histmaker`
  = the old `histmaker_validation` main body (moved verbatim). One argparse, `--reference`
  dispatches. Card flags: `--datacard`/`--btgrid`/`--signal-proc`/`--outdir`; histmaker
  adds `--histmaker`/`--sample`/`--gen-histmaker`/`--variation`/… (per-path flag names kept
  to preserve exact behaviour — a later unify-flags pass could tidy this).
- `param_model_diagnostics.py`: **demoted to a library** — `main`/`__main__` REMOVED (no
  longer a CLI); keeps Layer-0 (`run_reco_guard`, pathology detectors, card refs,
  `_shape_residual`, `reco_offending_bins`) AND `run_card_diagnostics`/`compare_level` (the
  card comparison impl `validate_agreement` calls). Fit still imports `run_reco_guard`;
  `sigma_gen_at_lambda` still imports the pathology fns. Docstring updated to say "library".
- `validation/histmaker_validation.py`: **DELETED** (its main body folded into
  `validate_agreement.run_histmaker`; loaders already in `agreement`).
- `sigma_gen_at_lambda.py`: imports shared loaders from `agreement`; `_merge_matrix`
  de-duped to `validation_plots` (one copy).

**Verification (re-done after the collapse):** tests 1/2/3 via the new
`validate_agreement --reference card` + `sigma_gen_at_lambda` are physics-identical to
the baseline (only TF startup + memory-pressure warnings differ). baselines in `baseline/`
(INVARIANTS.md), after-run in `after/`, `scripts/run_validation_tests.sh {baseline,after}`
+ `scripts/diff_baseline_after.sh` (filters TF log noise). Structure smoke test:
`param_model_diagnostics` has no `main`, keeps `run_card_diagnostics`+`run_reco_guard`;
`validate_agreement` has `run_card`+`run_histmaker`; no circular deps.

**Next (with Luca):** (1) review `SENSITIVE_POINTS.md` and decide which physics/rebin
fixes to do; (2) optionally deepen `validate_agreement` from pass-through to a genuinely
unified flag set (+ `--level`, cap-5 gen double-ratio); (3) commit the prereq + reorg
scoped to `scetlib_np/`; (4) update recipe docs that name the old CLIs.

---
### (original analysis, retained)
**Analysis DONE and AUDITED against the code (2026-07-02).**

**Do first / context:** immediately before this, the scetlib_np scripts were refactored
to drop hardcoded paths (btgrid → `sigma_gen._default_btgrid_dir()`, `--datacard`/
`--histmaker` → `required=True`). **Working-tree status (verified 2026-07-02):** on
branch `scetlib-np-param-model`, `param_model_diagnostics.py` / `sigma_gen_at_lambda.py`
/ `np_function_plots.py` are modified-uncommitted, and the whole `validation/` package
plus `validation_plots.py` / `plot_output.py` / `point_to_binned.py` / `docs/` are
**untracked** (never committed). The tree also carries UNRELATED pending edits
(`theory_fit_writer.py`, `theory_corrections.py`, `feedRabbitSigmaUL.py`, narf bump) —
scope the prereq commit to `wremnants/postprocessing/scetlib_np/`, don't `commit -a`.

**Blocking decisions (Luca to pick):**
1. CLI shape — **(A)** one `validate_agreement.py --reference {card,histmaker}` + keep
   `sigma_gen_at_lambda.py`; or **(B)** three thin CLIs. Audit reaffirms **(A)**: card vs
   histmaker differ only in the reference loader; `sigma_gen_at_lambda` is genuinely
   distinct (gen-only, arbitrary-λ, theory truth). Bonus for (A): the recipe commands
   quoted in `studies/{physical-lambda,btgrid-precision}/LOGBOOK.md` and
   `studies/xterm-factorizability/WORKFLOW.md` only go stale for the two merged scripts.
2. Shared-library location — audit recommends a **new `validation/agreement.py`**
   (loaders + compare), keeping `validation_plots.py` plotting-only and — key change vs
   the original plan — **NOT moving the guard/pathology functions at all** (see
   "Layering" below).

**Next step after the pick:** implement the 3-layer split below. Since nearly everything
is uncommitted/untracked, renames are cheap NOW — do the reorg before this lands in
PR #701, not after.

## Audit: every normalization / cut / projection op in the comparison code
**(the "tricks" review — Luca 2026-07-02. Verdict: no dishonest scaling; the issues are
FRAGILITY and NON-hist-native ops, plus ONE genuine asymmetry in the gen card ptVGen plot.)**

Empirically verified (login-node hist 2.9.2), the behaviors everything hinges on:
- integer slice WITHOUT `sum` (`h[i0:i1]`) → removed bins are PARKED IN FLOW, not dropped
  (kept 33 visible / 105 with-flow == original total).
- `h.project(ax)` → FOLDS IN the summed axis's flow (104 vs 5). So a plain `.project()`
  on a cropped hist silently re-adds the hidden out-of-range content.
- slice WITH `sum` (`h[i0:i1:sum]`) → excludes flow of the reduced range (correct).
- model hists (`tf_to_hist`) are built `underflow=False, overflow=False` → **the model has
  NO flow bins**; every flow subtlety below is on the REFERENCE side only.
- model qT domain is FINITE: last ptVGen bin is `[44,100]` (`PTVGEN_OVERFLOW_EDGE=100`),
  qT>100 DROPPED. So `flow=False` on the reference is CORRECT domain-matching, not flow=True.

**Governing principle (Luca):** don't pick flow=True/False by default — define ONE explicit
domain (Q∈[60,120], |y|≤y_max, qT≤100) and restrict BOTH sides to it by construction, so
flow is irrelevant. Prefer hist-native slicing/rebinning; normalize only at plot time.

| path | normalize | cut / domain | project | verdict |
|---|---|---|---|---|
| **A. σ_gen vs theory-corr** (`sigma_gen_at_lambda`) | default OFF (absolute overlay); `--theory-corr-normalize` opt-in + labeled | vars/charge native; **Q window + |y| cut by bin CENTER** ⚠; merge-matrix drops qT>ceiling; all `flow=False` | model `.sum(axis=other)` numpy; corr `_merge_matrix` **matmul rebin** ⚠ | **HONEST, domain-matched.** Subtleties: center-based Q/|y| select (partial-bin risk; warns on |y| edge mismatch), non-native rebin, model qT>100 drop (the −16% overflow, physics not norm) |
| **B. σ_reco vs card/histmaker** (`param_model_diagnostics`,`histmaker_validation`) | `_unit`/`density` at plot (over flow=False domain) ✓; `summarize` Σscale over ALL reco bins | `align_nominal` **crop-into-flow** ⚠ then `project_inrange` flow=False compensates | `project_inrange` (hist, flow-safe) ✓ | **CORRECT because flow=False everywhere; FRAGILE** — a plain `.project()` would re-inflate. Fix: DROP out-of-range bins, don't park in flow |
| **C. σ_gen vs card** (`run_card_diagnostics`) | ptVGen plot: model×`gscale` (resolved-only scale) but overflow bin SHOWN ⚠ **asymmetry**; absY plot: overflow ZEROED in both + density ✓ | resolved-qT = drop overflow from the scale | reshape only | **MIXED.** absY plot honest (cut from both); **ptVGen plot is the one show-but-normalize-elsewhere asymmetry** → fix per the norm rule |
| **D. σ_gen vs gen-MC** (`align_gen`) | `summarize` Σscale over all | helicity/mass native index ✓; merge **matmul rebin** ⚠ | `project` (folds flow, but charge/others meant to sum) | **HONEST; non-native rebin** |
| **E. variation double-ratio** (`validate_variation`) | NONE (ratio/ratio) ✓ | `align_nominal` crop-into-flow + `project_inrange` | flow-safe | **CLEANEST** — normalization-free; the model for cap 5 |

**Against Luca's 3 principles → refactor targets:**
1. *cut with hist-native slicing*: replace (a) `_merge_matrix` matmul with `wums.boostHistHelpers.rebinHist`
   (native, edge-based; already used in `native_validation`); (b) center-based Q/|y| selection
   with edge-aligned slicing; (c) crop-into-flow with a real DROP of out-of-range bins.
2. *normalize only when plotting*: remove `run_card_diagnostics`'s pre-plot `gen_model*gscale`;
   density-normalize at plot time over the domain bins. (Numeric `summarize` scale is fine as
   an explicit numeric summary, but state its domain.)
3. *project via hist logic*: unify on `project_inrange`; drop numpy `.sum(axis=other)` +
   matmul in the theory-corr other-axis in favor of hist slice+sum / rebinHist.

**Still to VERIFY by running (needs data-load in container), not just code-read:**
- do the corr Q edges include 60 & 120 exactly (else the center-based window clips a partial bin)?
- magnitude of the |y|-max-vs-corr-edge mismatch (the warned case) on a real corr file;
- is model qT>100 actually negligible, or is the −16% overflow leaking into the [44,100] bin?

## The 5 capabilities (Luca's ask)
1. validate param-model **σ_reco** vs datacard (or histmaker)
2. validate param-model **σ_gen** vs datacard (or histmaker)
3. check **pathologies**
4. validate **σ_gen** vs a **theory correction**
5. validate **σ_gen** vs **theory-correction variations** wrt nominal

## Current scripts — scope / I/O (analysis 2026-07-02, audited)

| | `param_model_diagnostics.py` | `validation/histmaker_validation.py` | `sigma_gen_at_lambda.py` |
|---|---|---|---|
| reference | the **datacard** (`indata.norm`, `N_gen` aux) | external **histmaker** (`nominal`, gen-MC, `Corr[var]`) | official **TheoryCorrection** (`{gen}_hist`+vars) |
| level | reco + gen | reco + gen | gen only (no R) |
| model | full `SCETlibNPParamModel` | full `SCETlibNPParamModel` | datacard-free `SigmaGenModel` (core) |
| λ point | λ_central | λ_central | **any tune** (base + `--lambdas`/`--fitresult`) |
| checks | central shape + **pathologies** + in-fit reco guard | central shape + reco-level **variation** vs Corr[var] | central + **absolute overlay** at any vars label |
| caps | 1,2,3 (vs card) | 1,2 (vs histmaker) + reco-variation | 4, partial 5 |
| key fns | np_damping_ok, spectrum_negativity, np_physical_report, _shape_residual, card_reco_reference, card_gen_reference, reco_offending_bins, run_reco_guard, compare_level, run_card_diagnostics | load_nominal, align_nominal, load_gen_hist, align_gen, _parse_variation_label, validate_variation | resolve_base_lambda, assemble_tune, resolve_gen_axes, load_theory_corr_hist, theory_corr_projection, _merge_matrix, make_projection_plot |

Note: `sigma_gen_at_lambda` **already** `import param_model_diagnostics as ppd` for
pathologies — cap 3 is de-facto shared already.

**Cap-5 clarification (audit, discussed with Luca 2026-07-02):** two distinct checks.
(i) EXISTS: `sigma_gen_at_lambda --lambdas … --theory-corr-var lambda21.0` compares
σ_gen(λ′) vs the corr λ′ entry **absolutely** at that λ point (`rcorr = model/corr`,
sigma_gen_at_lambda.py:643) — so a varied λ CAN be validated today (two runs + hand
division give the wrt-nominal ratio). (ii) MISSING: a single-shot **double ratio**
(model `σ_gen(λ′)/σ_gen(λc)` vs corr `var/pdf0`), the gen analogue of
`validate_variation`. The ratio matters beyond convenience: the absolute check's floor
is the central-closure floor (~0.1%, common shape errors don't cancel), while the reco
ratio validated the response to 0.02–0.05% — and rnorm is what the fit applies. The
shared `variation_rnorm` primitive should support both levels; a small addition.

**Out of scope (explicit):** `validation/{native_validation, resum_validation,
export_spectrum, factorized_parity, gen_level_smoke, truth_start_grid, timing,
damping_wall_dispatch}.py`. But `resum_validation` is exactly a 4th reference provider
(SCETlib resummed `combined.pkl` → gen grid), so design the provider interface such that
it can be folded in later without touching the compare layer.

## The real structure (3 axes, not 2 scripts)
Every check ∈ **{level: gen|reco} × {reference: card|histmaker|theory-corr} × {kind: central|variation|pathology}**.
Verified duplication to remove:
- **`_merge_matrix` exists twice**, drifted: `validation_plots.py:21` (raises ValueError,
  delegates to `params.bin_sum_matrix`) vs `sigma_gen_at_lambda.py:98` (own loop, raises
  `SystemExit`). Same math; delete the sigma_gen copy.
- **`compare_level` computes the same comparison twice**: it calls
  `validation_plots.summarize` (prints scale + ratio stats + per-axis tables) AND
  `_shape_residual` (same global-scale + ratio, different stats dict). Merge:
  `_shape_residual` is the computation, `summarize` becomes a formatter over its output.
- **three align-to-model-grid paths**: `align_nominal` (hist-level reorder + crop
  superset axes), `align_gen` (helicity select, mass window, project, merge-rebin),
  `theory_corr_projection` (vars select, Q window, charge sum, other-axis cut,
  merge-rebin). They share the subrange-select + merge-rebin core but each handles a
  genuinely different input layout — so they belong WITH their reference loader, built
  on shared `subrange`/`_merge_matrix` helpers, not force-unified.
- **build model/core; plot** (`validation_plots`, `plot_output`) — all three.

**Normalization policy (Luca's rule, 2026-07-02 — SETTLED).**
Governing principle: **the normalization domain == the comparison/display domain — one
set of bins.** Never normalize over a set different from what you show; showing a bin but
excluding it from the scale (or vice-versa) smears its deficit across the rest and is
dishonest ("lying"). Density and the Σref/Σmodel global scale are the SAME per-bin ratio;
what matters is that BOTH the sum and the drawn bins use that one domain. This
SUPERSEDES the earlier "exclude model-incomplete bins from the scale but still show them"
half-measure (retracted — that was exactly the asymmetry). Consequences:
1. both sides theory σ on the identical phase space → compare on that whole domain
   (absolute, or equivalently density over it; `--theory-corr-normalize` stays opt-in).
2. reference is an MC yield → one scale over the SHOWN domain (density over the drawn
   bins gives this for free — see plotting note).
3. central+variation pair present → **ratio-to-central** (normalization-free; rnorm is
   what the fit transports). Best precision, cap 5.
4. a bin the model can't predict (gen ptVGen overflow: qT beyond the grid ceiling; the
   reco top ptll [37,44]: qT>100 truncation) is a DOMAIN decision, not a scale knob:
   either CUT it (not shown, not normalized — clean bulk-shape check) or KEEP it (shown
   AND normalized — deficit appears in place, honest). Not "show-but-drop-from-scale".

Per-path application of the rule:
- **reco vs card/histmaker:** [37,44] is INSIDE the fit domain (ptll fit → 44), so KEEP
  it — normalize over all fit bins, let the deficit trip the guard in place (the guard's
  "known [37,44] truncation" message already does this honestly). *Reverses the earlier
  audit note that proposed excluding it from the reco scale.* → guard threshold/closure
  numbers UNCHANGED; no re-baselining. (Genuinely excluding [37,44] would be a FIT-level
  decision, not a normalization one.)
- **gen vs card (`run_card_diagnostics`):** CURRENT CODE VIOLATES the rule — it normalizes
  on resolved-qT but still DRAWS the overflow bin as a step. Fix → CUT the overflow bin
  from the display too (domain = resolved qT, shown == normalized). The bulk closure
  number is then honestly "resolved-qT shape" and doesn't move; only the plot loses the
  cosmetic step.
- **gen vs theory-corr / MC:** already drops out-of-range fine bins in the rebin — the
  shown/normalized domains already coincide. OK.

Other behavior drift to fix while merging:
- error style: `sigma_gen_at_lambda` library fns raise `SystemExit` (poison for a shared
  lib); normalize to ValueError/KeyError in the library, exit codes only in CLIs.

**Plotting layer — wums normalization (Luca, 2026-07-02; corrected).**
wums has TWO normalizations and they are NOT the same:
- `binwnorm` (bin-WIDTH; `plot_ptll_ratio` already passes 1.0) → per-GeV density for
  variable bins. Does NOT equalize the two curves' total integrals — not shape norm.
- `density=True` (unit-INTEGRAL, the shape norm) → EXISTS ONLY on `makeStackPlotWithRatio`,
  NOT on `makePlotWithRatioToRef`, which is the function `plot_ptll_ratio` actually calls
  (verified full signature). THIS is why the script hand-rolls `_unit` — the function we
  use has no unit-normalize.
So "wums does it, we don't have to" holds only if we SWITCH functions. The trade:
- keep `makePlotWithRatioToRef` (the natural fit — one reference, ratio-to-ref is exactly
  our case): no native unit-norm → pre-normalize the hist (`h / h.sum()`, == `_unit`). A
  one-liner, not real duplication; keep it. Cleanest.
- switch to `makeStackPlotWithRatio(density=True)`: native unit-norm, drop `_unit`, but
  it's stack/data-MC oriented (`no_stack`, `normalize_to_data`) — must verify unstacked
  2-curve + ratio-to-ref still looks right before adopting.
Either way, apply Luca's rule by building the hist from ONLY the domain bins first, so
shown==normalized regardless of which normalizer runs. Recommend: keep
`makePlotWithRatioToRef` + the `h/h.sum()` one-liner (don't inherit stack semantics for a
2-curve plot). Retracts the earlier "density for free" claim — only true under the switch.

## Layering (audit correction to the original plan)
The original plan moved the pathology fns + `run_reco_guard` INTO `validation/agreement.py`.
**Don't.** `param_model.py:857-867` (the fit, core) imports `run_reco_guard` lazily in the
constructor, default-on; `param_model_diagnostics` is deliberately numpy-only for that
path. Moving the guard into the validation package inverts the dependency (fit →
validation) and entangles the in-fit import with reference-loader deps. Instead:

- **Layer 0 — fit-side numpy core (STAYS `param_model_diagnostics.py`):** `run_reco_guard`,
  `reco_offending_bins`, `_shape_residual`, `card_reco_reference`, `card_gen_reference`,
  `np_damping_ok`, `spectrum_negativity`, `np_physical_report`. Zero import churn for
  `param_model.py` / `np_damping_wall` / existing recipes. What LEAVES this module is the
  CLI + plotting half (`run_card_diagnostics`, `compare_level`, `main`).
- **Layer 1 — `validation/agreement.py`:** reference providers, each → `(values,
  axes_meta)` on the model grid: `ref_card_reco`, `ref_card_gen` (wrap Layer 0) ·
  `ref_histmaker_reco`, `ref_gen_mc`, `ref_corr_variation` · `ref_theory_corr` (+ later
  `ref_scetlib_resum`); `shape_compare` (Layer-0 `_shape_residual` + policy knobs +
  summary formatting), `variation_rnorm(level={reco,gen})` (closes cap 5).
- **Layer 2 — CLIs + plots:** `validate_agreement.py` (option A) + kept
  `sigma_gen_at_lambda.py`; `validation_plots.py` stays plotting-only.

## Pointers
- Scripts: `wremnants/postprocessing/scetlib_np/{param_model_diagnostics.py,
  sigma_gen_at_lambda.py, validation/histmaker_validation.py, validation_plots.py,
  plot_output.py}`; guard call site `param_model.py:857-867`.
- Prereq (uncommitted): btgrid/datacard hardcode cleanup on `scetlib-np-param-model` —
  `git diff` to see; commit scoped to `scetlib_np/` only.
- Recipe docs quoting these CLIs (update after the rename): `studies/physical-lambda/LOGBOOK.md`,
  `studies/btgrid-precision/LOGBOOK.md`, `studies/xterm-factorizability/WORKFLOW.md`.
- Related: [[physical-lambda]] (uses the diagnostics/guard), [[btgrid-precision]] (b0=1
  grid the scripts default to via `_default_btgrid_dir()`).
- Fit uses `param_model_diagnostics.run_reco_guard` at fit time (default-on) — under this
  plan it does not move, so nothing to break.

## Log
- **2026-07-02 (discussion with Luca, round 2 — normalization SETTLED):** Luca's rule =
  normalization domain == display domain, one set; "show-but-drop-from-scale" is the lie.
  This RETRACTS the round-1 "exclude [37,44] from the reco scale" idea: [37,44] is in the
  fit domain → keep it in norm, let the deficit trip the guard in place. ⇒ NO reco
  re-baselining; guard threshold + 0.14% closure UNCHANGED (the round-1 OPEN sign-off is
  moot). Real fix is gen-side: `run_card_diagnostics` draws the overflow bin while
  normalizing on resolved-qT — cut it from the display (domain = resolved qT). Also: use
  wums native `density` (makeStackPlotWithRatio) instead of the hand-rolled `_unit` —
  density-over-passed-bins IS the rule for free. See the Normalization + Plotting blocks.
- **2026-07-02 (discussion with Luca, round 1):** (1) layering fix agreed — guard/pathologies
  stay in `param_model_diagnostics`, only the CLI half moves. (2) Cap 5 clarified:
  the absolute σ_gen(λ′)-vs-corr check exists (`--theory-corr-var`); the single-shot
  double ratio is the (small) missing piece — see the cap-5 block. (3) Normalization
  policy first pass (SUPERSEDED by round 2 above).
- **2026-07-02 (audit):** verified the function inventory and duplication claims against
  the code — all accurate. Corrections folded in above: (1) guard/pathologies must NOT
  move into the validation package (fit→validation dependency inversion; keep Layer 0 in
  place and strip the CLI half out instead); (2) cap 5 was over-credited — the gen-level
  variation/central ratio doesn't exist yet, it's new work in `variation_rnorm`; (3) the
  card-gen overflow-exclusion normalization and the SystemExit-vs-ValueError drift are
  behavior differences the shared compare must parameterize, not average away; (4) the
  whole `validation/` package + `validation_plots.py` are untracked, so renames are free
  until this lands in #701; (5) `histmaker_validation` still hardcodes setup-specific
  defaults (`SIGNAL_SAMPLE`, the CT18Z `VARIATION_HIST` tag) — derive the variation-hist
  name from the datacard meta (as λ_central already is) while touching it.
