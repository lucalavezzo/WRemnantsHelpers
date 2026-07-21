# Sensitive points to review at the END of the reorg (Luca + Claude)

These are behavior subtleties / potential-issue spots encountered during the reorg.
The reorg itself is a PURE no-op (tests 1/2/3 numbers unchanged); everything here is
either (a) a pre-existing behavior we deliberately preserved, or (b) a physics/rebin
question to tackle AFTER the reorg. Nothing here is changed by the reorg unless noted.

## Confirmed from the baseline run (2026-07-02)
1. **Test 1 last ptVGen bin = 0.9858** (vs 0.9995 in the bulk): the [44,100] truncation
   overflow, summed over |Y|<5. Model integrates qT only to PTVGEN_OVERFLOW_EDGE=100 and
   drops qT>100. → the −16% overflow / truncation question (physics, defer).
2. **Test 2 worst bin −16.80% at (ptVGen=20, absYVGen=2)** = same truncation, in the gen
   overflow ptVGen bin. Global-norm 3.80% is that deficit smeared into a pedestal;
   resolved-qT bulk is 0.067%. → the norm-domain rule (deferred fix).

## Behavior subtleties preserved by the reorg (from the code audit)
3. **crop-into-flow + flow=False discipline** (`align_nominal`): out-of-fit-range ptll
   parked in flow, only correct because everything downstream uses flow=False. Fragile;
   a plain `.project()` would re-inflate. → replace with a real cut (deferred).
4. **gen card ptVGen plot asymmetry** (`run_card_diagnostics`): model scaled by
   resolved-only gscale but overflow bin still drawn (show-but-normalize-elsewhere).
   The sibling absY plot cuts overflow from both (honest). → fix per norm rule (deferred).
5. **center-based Q-window + |Y|-cut** (`theory_corr_projection`): selects by bin center,
   partial-bin risk; warns on |Y|-max/corr-edge mismatch. → edge-align (deferred).
6. **_merge_matrix matmul rebinning** (not hist-native): exact when edges align (enforced).
   De-duped in the reorg (was 2 copies); replacing with wums rebinHist is deferred.
7. **SystemExit in library fns** (`sigma_gen_at_lambda` loaders): poison for a shared lib;
   normalize to ValueError. (May address in reorg where it doesn't change passing output.)

## New points encountered during implementation
8. **`validate_agreement.py` keeps per-path flag names** (card `--outdir` vs histmaker
   `--plot-out`, etc.) — one argparse, `--reference` dispatches to `run_card`/`run_histmaker`
   (the old two main bodies, moved verbatim). Kept the names to preserve exact behaviour.
   A later "unify the flag set" (+ `--level`, cap-5 gen double-ratio) is a deliberate
   follow-up. Verified: card path reproduces the baseline exactly; both branches route.
9. **`param_model_diagnostics` still holds `run_card_diagnostics`/`compare_level`** (not
   only Layer-0). It's demoted to a LIBRARY (no `main`), but keeps the card comparison impl
   that `validate_agreement` imports. Fine — those fns lazy-import heavy deps so the in-fit
   guard path stays numpy-only. Could move them to `agreement.py` for cleaner layering, but
   that re-touches the tested path; deferred. If moved later, re-verify tests 2/3.
   (`histmaker_validation.py` was DELETED — its body is now `validate_agreement.run_histmaker`.)
10. **`SystemExit` still raised inside moved library fns** (`assemble_tune`,
    `theory_corr_projection`, `load_theory_corr_hist` in `agreement.py`) — moved VERBATIM
    to keep the no-op. Poison for a shared lib (a traceback-vs-clean-exit issue on the
    error path only). Normalize to ValueError/KeyError when we do the physics pass.

11. **`sigma_gen_at_lambda` and `validate_agreement` share the LOADER layer but not the
    COMPARE+PLOT layer.** Shared: `agreement.py` (loaders, tune resolvers,
    `theory_corr_projection`, `_merge_matrix`), `tf_to_hist`, `plot_output`, pathologies.
    NOT shared: (a) the model — `SigmaGenModel` core (cardless) vs `SCETlibNPParamModel`
    (datacard); this is intended. (b) the comparison stat — `sigma_gen_at_lambda` computes
    `model/corr` inline; `validate_agreement` uses `summarize`/`compare_level`/`_shape_residual`.
    (c) the plot — `make_projection_plot` (raw matplotlib, ratio + differential-diff panels)
    vs wums `plot_ptll_ratio` (density). Unifying (b)+(c) into one `shape_compare` +
    one plotter is the natural next consolidation, but it CHANGES plot output (not a no-op)
    and is entangled with the normalization/plotting decisions — do it in the physics pass.

## Verified NON-issues (checked, fine)
- `_merge_matrix` de-dup: the old `sigma_gen_at_lambda` copy (no tol, SystemExit) vs the
  shared `validation_plots` one (±tol via `bin_sum_matrix`, ValueError) give the SAME 0/1
  matrix for bin midpoints; differ only within tol of an edge (never hit) and on the error
  path. Test 1 byte-identical confirms.
- No circular imports; moved symbols resolve to the single shared copies (smoke test).
- `param_model_diagnostics` untouched → tests 2/3 identical by construction (confirmed).
