# Logbook entry (staged) — the response matrix above gen qT 100

**Date** 2026-08-26. **Study** `scetlib-ad-param-model`.
**Staged, not merged**: `LOGBOOK.md` and `DECISIONS.md` untouched.
Decisions in `DECISIONS_above100.md` (D-A1..). Web artefact:
`~/public_html/alphaS/260826_scetlib_ad_response_above100/`.

## What this round was

The response matrix now lives on the theory correction's own gen grid (D-037),
which resolved gen qT up to 100 and gave everything above it one column that
`load_R` drops. The question raised before building anything: the correction
stops at 100 and its flow bin is exactly 1.0, so the MiNNLO templates are
UNCORRECTED above 100 while the differentiable model would happily calculate a
CORRECTED cross section there. Adding gen bins above 100 without doing anything
else would put the two sides computing different things in the same bin -- the
same failure mode as the qT [0, 1] cell, where every variation looked wrong until
the ratio was rebuilt from the singular piece alone.

Two consistent options: (a) extend the corrections above 100, (b) keep the region
explicitly uncorrected on both sides. **Luca chose (a)** -- "let's extend the
response matrix, and I can produce the theory corrs with the same binning we
choose. this is the most correct thing to do." So the deliverable became a
BINNING SPECIFICATION his production can be run against, plus the mechanics.

## The physics read

**The disagreement is worth ~7 %, not ~0 %.** At the edge of its support the
correction is not close to 1: `N_gen`-weighted over |Y| < 2.5 it is 1.0205 at
qT 46-48, falls to 0.9255 at 80-90 and turns back up to 0.9372 at 90-100, with a
38-variation envelope of 13.8 % in that last row. So "correction = 1 above 100"
is a ~7 % statement on 1.977 % of `N_gen`, and the curvature at the edge says it
should be CALCULATED rather than extrapolated. That is the physics case for (a),
independent of any fit-level number.

**But today's fit cannot see it.** Gen qT > 100 feeds 1.63e-07 of the corrected-MC
yield in the fit's 780 reco bins (ptll < 44): 8.86 in weight against 5.43e+07,
i.e. of order ten MC events, with a per-bin median of exactly zero and a worst
single bin of 2.24e-05. Because the model hands rabbit a RATIO, any treatment of
a λ-independent piece of size f(b) shifts `rnorm` by f(b)·|rnorm−1|, so all
choices agree to ≲1e-06 -- far under the 5.7e-04 calculation floor. Where it does
bite is reco ptll [44, 100], at 2.81e-03 of that bin's yield: **the moment the
fit's reco range goes past 44 GeV, this becomes a real 2e-04 effect.** Worth
saying out loud rather than selling the extension as a bias fix.

## What was built

* `theory_corrections.check_gen_grid_vs_correction` -- refuses a gen grid that
  splits a correction cell or reaches past the correction's support (opt-in for a
  declared PROVISIONAL grid). Called from `mz_dilepton` when the response axes are
  built, and from `prepare_cache_for_card.gen_axes_from_card`, which is the place
  a mismatch would otherwise be inherited silently into the SCETlib runcard.
* the datacard now carries `corr_generator` in its response auxiliary (read from
  the histmaker's own `meta_info`), which is what makes the cache-side check
  automatic instead of something to remember.
* `mz_dilepton --responseGenPtVExtend` -- the temporary bridge. Once the
  correction covers the wider grid it is not needed: `--responseGenBinning
  theoryCorr` reads the grid out of the file.


## Order of work, and why each step exists

1. **Verified the premise before touching anything.** All flow bins of the CorrZ
   `minnlo_ratio` are exactly 1.0 (`min == max == 1` over the qT overflow's 2106
   cells, and separately for Q under/over and absY over). So the templates really
   are uncorrected above 100 -- not approximately, exactly.
2. **Measured the size of the disagreement** from the correction itself (the
   0.9372 at 90-100 above) and the size of its reach into the fit
   (1.63e-07). Reported the second immediately, because it is the number that
   says the extension is a correctness move rather than a bias fix.
3. **Traced the production chain** to find which inputs need the new edges. The
   surprise was the MiNNLO denominator: one bin [100, 13000], so it has to be
   remade too or `hh.rebinHistsToCommon` collapses the region.
4. **Put the consistency requirement in code** (D-A3) before generating any grid,
   so the specification cannot silently drift from what gets built.
5. **Then the mechanics**: A/B, the full histmaker on the diagnostic grid, the
   cache, the closure.

## Why a fine DIAGNOSTIC extension and not the final one straight away

The histmaker run uses twelve bins above 100 (110, 120, 130, 140, 150, 170, 200,
250, 300, 400, 600, 1000) rather than the two or three we will ship. `R_raw` is
additive under gen rebinning, so any candidate grid whose edges are a sub-union
of those twelve is obtained by SUMMING columns -- one 30-minute run therefore
scores every candidate exactly, and the yield fraction and reco feed quoted per
candidate bin are measurements, not interpolations. Same for the cache: sigma_gen
is additive too, so the 880-bin cache gives sigma on any candidate grouping.


## Traps that were live in this round

* **The A/B could have been a false pass.** Arm B differs from arm A by two
  histograms *and* by a longer gen axis; comparing only the 464 shared ones would
  have missed a silently truncated column. The restriction control (B cut at
  gen qT < 100 must be C, bitwise) is what closes that, and the pairing of C's
  dropped overflow against the sum of B's new columns (rel exactly 0) is what
  shows the extension resolves the same events rather than adding different ones.
* **`pkill -f "<string>"` matched this session's own shell** and killed it
  mid-command, which is the trap already recorded in memory. The relaunch used
  `setsid nohup` and an explicit PID check instead.
* **`cd X && nohup A & sleep; nohup B &`** backgrounds the `cd` as part of the
  first job, so the second launch ran in the wrong directory and died on
  `incontainer.sh: no such file`. Absolute paths since.
* **`--maxFiles` defaults to booking 900 of 2779 files**, not all of them: the
  first full run was silently at 32 % statistics and was relaunched with
  `--maxFiles -1`. Worth knowing for anyone comparing against
  `260826_Z_histmaker_respgrid`, which passed `-1` explicitly.

