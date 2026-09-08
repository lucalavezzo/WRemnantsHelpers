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

**Physics read.** This is the signature the reference is chosen to expose, not
a defect. Our cache computes its own matched total with SCETlib's in-house
analytic V+jet rather than DYTurbo's nonsingular, and takes the nonsingular to
vanish below qT = 0.1 GeV; the correction file carries DYTurbo's. A difference
of nonsingular treatment can only show up where the nonsingular is a
significant fraction of the matched total relative to the resummed piece, and
at qT << M it is power-suppressed -- so the disagreement is bounded to the
lowest bins and dies as qT grows, which is what is measured. The
`compare_to_scetlib_run.py` docstring states this in advance: this reference
"measures the deliberate change of nonsingular as well as everything the
resummed test covers". The total agreeing to 0.9e-4 says the change of
nonsingular does not move the integrated cross section.

Not to be confused with the ptll shape residual under investigation in
`260908-ptll-residual`: that one is at **reco** level after the response fold
and is 1.6 % at its worst, two orders larger than anything here, and it is not
concentrated at low qT.

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
