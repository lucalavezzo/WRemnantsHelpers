# WZ Post-Unfolding 1:1 Comparison (mb/mc removed)

## Study question
Run both post-unfolding Z fit branches on the same unfolding input while removing the problematic mb/mc-related variations, then compare outputs.

## Guiding questions
- Can the `feedRabbitTheory` branch run to completion when mb/mc variations are removed?
- Can the `setupRabbit` (MC-events) branch run in an isolated output directory with the same mb/mc removal treatment?
- If one branch fails, is the failure from mb/mc nuisances or from a separate theory-correction binning incompatibility?

## Current understanding
- `setupRabbit` (MC branch) completes from Z-only unfolding input when run in isolated output dir and freezing `pdfMSHT20m[bc]rangeSym.*` at fit time.
- `feedRabbitTheory` branch currently fails before fit due incompatible `absYVGen` bin edges in theory variation handling.
- This confirms the blocker is an upstream theory-variation compatibility issue (not the final fit command itself).

## Decisions taken
- Use isolated output dir under `$MY_OUT_DIR` to avoid mixing with previous runs.
- Use Z-only unfolding input for faster iteration and cleaner reproduction.
- Apply mb/mc removal via `rabbit_fit.py --freezeParameters 'pdfMSHT20m[bc]rangeSym.*'` in MC branch.

## Open questions
- What is the minimal `feedRabbitTheory` configuration (or correction payload) that avoids the `absYVGen` incompatibility for this unfolding binning?
- Should this be solved by changing the correction source, unfolding binning, or patching `feedRabbitTheory` rebin behavior?
