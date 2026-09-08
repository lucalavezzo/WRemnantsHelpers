---
task: slides-validation
updated: 2026-09-08
---

# Slide material: reproducible commands for three validations and two fits

## START HERE

**State.** `COMMANDS.md` holds the five recipes Luca asked for, with the current
card / cache / histmaker / library paths and the measured result of each where
one exists. Validation 1 was **run here** and is recorded below. Validations 2
and 3 and both fits are unchanged configurations whose numbers already exist
elsewhere in this study; `COMMANDS.md` points at them rather than re-running.

**Two scripts had to reach the PR for the "pushed scripts only" constraint to
be satisfiable at all**, and both are now pushed:

| commit | what |
|---|---|
| `f479d015` | `validate_variations_reco.py` moved in from the study dir |
| `3ebc05bc` | `compare_to_scetlib_run.py` Y-convention fix + \|Y\| plot |

**Next step.** The card in `COMMANDS.md`
(`260908_Z_2D_card_corrgrid770`) is about to be superseded: the acceptance fix
landed as `7a3f4771` and its histmaker is running into
`260908_Z_histmaker_acceptfix/`. Every command here reruns verbatim against the
new card by changing `CARD` and `HM`; the **cache is unaffected** and does not
need rebuilding.

**Blocking.** Nothing. Note the fits still need SCETlib MR !11 (open) or the
`PYTHONPATH` override for the `hvp` fix -- see the last section of
`COMMANDS.md`.

## Findings

### Validation 1 -- sigma_gen vs the theory correction, on the correction's grid

Run 2026-09-08, 770-bin cache vs `..._CT18Z_N3p0LL_N2LO_CorrZ.pkl.lz4`, common
grid 11 x 70 (|Y| 0..2.5, qT 0..100). `--piece matched`.

| quantity | value |
|---|---|
| total, ours/ref | **1.000089** |
| per-bin \|ours/ref - 1\|, median | **7.2e-05** |
| per-bin, max | 5.2e-02, in qT [0, 0.5] |

The residual is a monotonically falling function of qT and nothing else:
5.2e-2, 3.1e-2, 2.8e-2, 1.2e-2, 7.0e-3 over the first five 0.5 GeV bins, under
1e-3 by qT ~ 6 GeV, under 3e-4 everywhere above 15 GeV, and rising only to
3.0e-4 by qT 80.

**Physics read.** Two distinct causes, both now quantified in
[260908-ptll-residual](../260908-ptll-residual/LOGBOOK.md), which chased the
same effect at reco level:

1. **Dominant, qT < 1 GeV: the nonsingular qT-cutoff convention.** We vanish
   the nonsingular below 0.1 GeV; the production template was made with
   `--qtCutoff 1.0`. Removing our nonsingular below the cut brings gen qT
   [0, 0.5] to model/template = 1.000063 and [0.5, 1] to 1.000009. Two
   independent routes agree on the reco bin-0 prediction to 9e-06.
2. **Smaller, above the cut: nonsingular accuracy** -- the model is +0.91 %
   high at gen qT [1, 1.5], DYTurbo's fixed order against SCETlib's analytic
   V+jet. No cutoff change touches it.

My first read of this run merged the two into "a different nonsingular", which
is true but not actionable: the fix for (1) is a cutoff value and the fix for
(2) is not. The total agreeing to 0.9e-4 says neither moves the integrated
cross section.

**The config cross-check does not cover this.** The run prints
`settings cross-check: OK`, but the cutoff is recorded in *neither* config --
ours is announced at runtime, the template's lives only in its production
command line -- and the compared whitelist is 13 keys, none of them the cutoff.
So the reassurance is real for what it covers and silent on the one setting
that produced the residual. Worth remembering before quoting "settings OK" as
evidence of a matched calculation.

**This is the same effect as the ptll shape residual**, which I had written off
as a different mechanism ("not concentrated at low qT") before
`260908-ptll-residual` reported. It is: the reco residual is the three lowest
`ptll` bins (-1.579e-02, -4.679e-03, -1.169e-03, then within 5.1e-04 above
2 GeV), it is the same cutoff convention, and the 2.25e-04 absolute-closure
deficit is the same gen-level effect integrated -- the low-`ptll` bins
contribute 126 % of it, partly offset by the +0.91 % excess at `ptll` 2-9.
So the two items Luca ranked first and second are one cause, and the gen-level
number here is the cleanest place to see it.

### The pushed scripts could not do this before today

`compare_to_scetlib_run.py` documents two references and could only run one of
them. Against a theory correction it exited with "the cache's Y grid is not
symmetric about 0, so it cannot be folded", because it assumed a *signed* cache
and folds by adding mirrored bins. The production cache is
**positive-side-only**: its Y edges already are |Y| edges, and it holds the
Y > 0 half of each, so the correct operation is a factor 2, not a fold. Since
this script compares absolute levels, getting that wrong is a 50 % error, not a
cosmetic one -- so the fix decides from the cache's own edges and raises, with
the edges printed, on a grid that is neither.

`validate_variations_reco.py` -- the reco-level variation validation carrying
the CALC/WGT/GRAIN split, i.e. the machinery behind the "GRAIN dominates CALC
in 46 of 97 directions" headline this study quotes most -- was living in the
study directory and could not be run from a checkout at all.

## Log

**2026-09-08.** Mapped Luca's five slide items onto pushed scripts. Items 2 and
3-gen had proven invocations in `260908-validate-card770/01_reco_central.log`
and `260827-authoritative-validation/02_gen_variations.log`; both fits had them
in `260908-fit-770/launch.sh`. Item 1 had never been run against a `Corr`
reference and item 3-reco had no pushed script. Fixed both, ran item 1, wrote
`COMMANDS.md`.

Dropped `--minimizerGtol 1e-4` from the toy recipe per Luca's instruction to go
back to the previous behaviour (`tol = 0.0`); it had been measured inert twice,
so the recorded TOY770NP numbers stand unchanged.
