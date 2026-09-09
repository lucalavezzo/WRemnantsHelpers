---
task: newcard-validation
updated: 2026-09-08
---

# The four validations and two fits, on the acceptance-fix card

## START HERE

**State.** All six ran on
`260908_Z_2D_card_acceptfix/ZMassDilepton_ptll_yll_adexclpdf` against
`260908_Z_histmaker_acceptfix` (verified: the card path was read back out of
each `fitresults_*.hdf5`, not assumed). Library `b66f8de`, cache
`pdf62_corrgrid_260827/merged_full`.

| | result |
|---|---|
| gen variations | 97 compared, worst **3.09e-02** (`mufup`) |
| sigma_reco, SHAPE | yield-wtd **0.00099**, ptll max **0.01557**, yll max **0.00110** |
| sigma_reco, ABSOLUTE | rerunning -- see the correction below |
| variations at reco | 100 figures, `reco_variations/` |
| Asimov fit | Exit 0, `fitresults_AS770.hdf5` |
| NP-frozen toy | Exit 0, 78 iterations, **edmval 9.35e-04** |

**Next step.** Two open items, both for Luca to call: (a) rebuild the cards
from the patched histmaker so the NP-anchor guard is live; (b) rerun the
frozen-NP toy with the old-card minimiser settings so its EDM is comparable.

**Blocking.** Nothing.

## Findings

### The toy's EDM is 27x looser than the old card's, and that is not yet explained

`edmval = 9.35e-04` over 78 minimiser iterations, against **3.49e-05** for the
old-card `TOY770NP`. The two are not directly comparable -- a different card
means different templates, so a different pseudodata throw -- and this run
dropped `--minimizerGtol 1e-4` per Luca's instruction to go back to `tol = 0`.
But 78 iterations at that EDM reads more like an early stop than a tight
convergence, so the honest statement is that the toy **ran to completion**, not
that it converged as well as the old one.

### The card carries no NP anchor, and the warning fired in every run

`[SCETlibADParamModel] WARNING: the card records no nonperturbative anchor, so
the cache anchor was NOT cross-checked.` appears in the Asimov fit, the toy and
the reco validation; the old card produced zero such lines. Nothing is computed
*from* the card's lambdas -- the model takes its anchor from `cache.conf` and
the card's copy exists only to prove the two agree -- so the numbers here are
sound, and what was lost is the proof rather than the calculation. Cause and
fix in [260908-acceptance-fix](../260908-acceptance-fix/LOGBOOK.md) and the
port in `scetlib_ad/lambda_central.py`.

## Log

**2026-09-08.** Ran all six on the new card.

**Correction, same day.** The `reco_abs` stage was launched as
`--reference histmaker --no-match-norm`, which is not the absolute test:
without `--reference card` the model never gets the physical `k = lumi*1000`
(nor the x2 |Y| fold), so it came out at ~3e-05 of the reference and the
"YIELD-WEIGHTED 0.99997" it printed was meaningless rather than a physics
result. The correct invocation is `--reference card --no-match-norm` with no
`--histmaker` at all, as in `260908-acceptance-fix/07_absolute.sh`. Fixed in
`stages.sh` with the reason in a comment and rerun. The authoritative absolute
number for this card, **0.999775**, comes from the acceptance-fix chain and is
unaffected.
