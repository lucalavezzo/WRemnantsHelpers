# Logbook entry (staged) — the CENTRAL prediction on the finer response-matrix gen grid

**2026-08-26.** Companion to `LOGBOOK_ENTRY_genbinning.md`, which measured the
VARIATION side of `mz_dilepton --responseGenBinning theoryCorr`. This is the
central side, which that round left unmeasured because it needs sigma_gen on the
correction's own gen grid and no such cache existed (D-041).

Staged only: `LOGBOOK.md` and `DECISIONS.md` are untouched. Decisions in

> **Provenance correction (2026-08-26 13:15, added after the fact).** This round
> wrote ONLY the two staged files and never edited `DECISIONS.md` or `LOGBOOK.md`.
> A PARALLEL session twice merged this content verbatim into `DECISIONS.md`
> (as "Central closure on the fine gen grid (agent, 2026-08-26)", D-C1..D-C10,
> and marked D-041 SUPERSEDED) and into `LOGBOOK.md`, and both times deleted the
> staged copies from `studies/scetlib-ad-param-model/`. The content is intact in
> the merged notes; only the staged filenames keep disappearing. The canonical
> copies of these two files therefore also live at
> `~/.claude/jobs/140d052c/tmp/central_fine/` and in the round's web directory
> `~/public_html/alphaS/260826_scetlib_ad_central_genbinning/`, which no sweep
> touches. The line above claiming the main notes are untouched was true when
> written and is no longer.
`DECISIONS_central_finegrid.md`. Plots and tables:
`~/public_html/alphaS/260826_scetlib_ad_central_genbinning/`.

---

## What was measured, and how it is like-for-like

The response-grid histmaker output carries BOTH gen grids side by side, so both
arms are literally the same events with the same weights:

```
shipped   nominal_prefsr_yieldsUnfolding + prefsr           21 x 10 gen bins
fine      nominal_prefsr_yieldsResponse  + prefsr_response  70 x 11 gen bins
```

The comparison is restricted to a contiguous gen rectangle whose edges are
shipped-grid edges, so it is the SAME phase space on both grids (the fine edges
are a strict refinement). The reference at reco level is the corrected-MC reco
yield fed by that gen region,

```
ref^S(b) = sum_{g in S} R_raw(b, g)
```

which is **exactly grid-independent** because `R_raw` is additive under gen
rebinning — measured, `max |ref_fine / ref_shipped - 1| = 1.8e-14`. All of the
arm-to-arm difference therefore lives in the numerator

```
sigma_reco^S(b) = sum_{g in S} [R_raw(b, g) / N_gen(g)] sigma(g)
```

i.e. it IS the gen granularity of the central prediction, with no reference-side
confounder. The two-term split is the closure round's:
`mod/ref = (mod/fld) x (fld/ref) = CALC x MC` with
`fld = R (x) sigma_CorrZ`.

## Cost: the central build is cheap, because the member loop is not needed

The D-041 bracket of 55-80 h assumed a full variation cache. sigma_gen at the
anchor needs only the node set, the matched cross sections and the compressed bin
rules; the PDF/alphaS/muF member loop builds only the variation columns. On the
shipped production cache that loop was **715.6 of 1052 min (68 %)**. With
`--no-pdf` the fine-grid central build is minutes-to-hours (see D-C1, D-C2).

## Result 1 — the cache-free measurement, which covers the WHOLE grid

Folding the production `sigma_CorrZ` through `R_raw/N_gen` on the two grids
isolates the granularity of the central prediction exactly (the two folds share
their denominator, D-C3), needs no cache, and therefore reaches every gen bin:

| gen region | shipped -> fine gen bins | reco-yield share | wmean\|dev\| | max |
|---|---|---|---|---|
| qT [1, 44]  | 190 -> 605 | 0.9851 | **1.79e-04** | 1.06e-03 |
| qT [0, 44]  | 200 -> 627 | 0.9983 | 1.79e-04 | 1.06e-03 |
| qT [0, 1]   | 10 -> 22   | 0.0146 | 2.18e-04 | 5.47e-03 |
| qT [0, 100] | 210 -> 770 | 1.0000 | 5.50e-04 | 1.79e-02 |

**The central prediction barely moves.** Against the published central closure of
1.28e-03 (0.128 %), the whole gen-granularity content of the central prediction on
the analysis region is 1.79e-04, i.e. 14 % of the residual and 0.018 % of the
prediction itself. The per-reco-ptll profile is a structureless +/-2e-04 wiggle
with no trend, against the published closure profile's smooth +8e-04 -> +2e-04
curve: the shape of the central residual is NOT binning.

Where it is largest is where it should be -- reco ptll 20-33 GeV, where the
shipped gen qT bins are 4-5 GeV wide -- and it reaches only +/-0.05 to 0.1 %
there (`central_grain_nocache_map`).

The qT [0, 100] row is a different effect and must not be read as granularity:
it is dominated by the shipped grid's [44, 100] OVERFLOW column, whose `N_gen`
holds gen qT > 100 that the model cannot fill (D-040). It appears as a single
**+1.06 % step in reco ptll [37, 44]** and nowhere else -- which is the fine
grid's real gain at high qT, and is a physics fix (the column stops being an
overflow), not a resolution one.

Controls: the CorrZ total is identical on the two grids to `-2.2e-16`; the total
fine/shipped shift on qT [1, 44] is `+6.1e-06`; the coarsening identity of
`R_raw` per reco bin and per shipped gen bin is `1.2e-13`; the reference identity
`max |ref_fine/ref_shipped - 1|` is `1.8e-14`.

## Result 2 — the cache-based before/after, with the real model

748-bin fine cache (`finegrid_260826/main_qt1_100`, `--no-pdf`, same base runcard
and same SCETlib build as the shipped production cache) against
`cache_260825_p4`. Yield-weighted mean |dev| over the 780 reco bins, shape:

**Headline region, gen qT [1, 44] x |Y| [0, 2.5]** (190 -> 605 gen bins, 98.51 %
of the card's reco yield):

| term | shipped | fine | ratio | shipped max | fine max |
|---|---|---|---|---|---|
| TOTAL model / corrected MC | 7.96e-04 | 8.19e-04 | 1.03 | 1.113e-02 | 1.128e-02 |
| CALC model / (R (x) CorrZ) | 5.86e-04 | 5.73e-04 | 0.98 | 1.078e-02 | 1.106e-02 |
| MC (R (x) CorrZ) / corrected MC | 4.06e-04 | 4.45e-04 | 1.10 | 1.925e-03 | 1.767e-03 |

arm-to-arm change of the central prediction: **1.94e-04 wmean, 1.33e-03 max**,
region total shifted by `-3e-06`. The cache-free route on the same region gave
1.79e-04 / 1.06e-03 -- the two agree to 8 % from opposite directions (one has the
real model on a limited region, the other has a proxy spectrum on the whole grid).

**The change is not directional.** Fine is closer to the MC in 392 of 780 reco
bins (50.3 % by count, 51.0 % by yield); corr(shipped residual, applied shift)
= **+0.15**; the metric moves +2.3e-05 against a per-bin shift of 1.94e-04. On
gen qT [1, 100], where there is a real correction, the same statistics read
corr **-0.69** and a metric change of **-2.27e-04**. So the statistics
discriminate, and on the analysis region they say "reshuffle".

**Including the shipped OVERFLOW column, gen qT [1, 100]** (200 -> 748 gen bins):

| term | shipped | fine | ratio |
|---|---|---|---|
| TOTAL wmean | 1.044e-03 | 8.17e-04 | 0.78 |
| TOTAL max | 1.773e-02 | 1.128e-02 | 0.64 |
| MC wmean | 7.18e-04 | 4.45e-04 | 0.62 |
| MC max | 1.738e-02 | 1.764e-03 | **0.10** |
| reco ptll [37, 44] TOTAL | -1.09e-02 | -3.94e-04 | **28x** |

That is the whole R3 improvement: `central_ptll_R3_qt1_100` shows the shipped
model 1.1 % low in the last reco bin and the fine model on top of the MC. Note
the reference is no longer bitwise identical between arms there
(`max |ref_fine/ref_shipped - 1| = 2.24e-05`, vs 1.8e-14 on qT [1, 44]), precisely
because the shipped overflow holds gen qT > 100 -- which IS the effect.

## Controls, all passed

* coarsening identity of `R_raw`, per reco bin and per shipped gen bin: `1.2e-13`
  (independent reproduction of D-037's `2.8e-14`);
* reference identity on qT [1, 44]: `1.8e-14`;
* CorrZ region total identical on the two grids: rel `-2.2e-16`;
* ARM SEPARATION: two `ScetlibADXsec` objects, 210 vs 748 cache bins, region
  sigma_gen 597.03225 vs 597.03269 pb (rel `+7.3e-07`). The
  `values_and_jacobian` memoisation trap (D-023) cannot apply;
* TWO-BUILD FLOOR, measured in situ by coarsening the fine sigma_gen back onto
  the shipped region grid: median |dev| `6.1e-07`, p95 `5.5e-06`, max `1.7e-05`,
  N_gen-weighted `1.5e-06` -- 20x below the published `3.1e-05` sigma floor and
  two orders of magnitude below the effect reported. (The `3.0e-03` Jacobian floor
  does not enter: no Jacobian is read.)

## The ladder back to the published 0.128 %

| definition | TOTAL | CALC | MC |
|---|---|---|---|
| published (260723 MC, `nominal` ref, whole grid) | 1.28e-03 | 7.5e-04 | 7.3e-04 |
| reproduced today, unmodified tool | 1.277e-03 | 7.48e-04 | 7.13e-04 |
| respgrid MC, `nominal` ref, whole grid | 1.277e-03 | 7.48e-04 | 7.13e-04 |
| respgrid MC, `R (x) N_gen` ref, whole grid | 1.296e-03 | -- | 7.11e-04 |
| respgrid MC, `R (x) N_gen` ref, gen qT [1, 100] | 1.044e-03 | 5.85e-04 | 7.18e-04 |
| respgrid MC, `R (x) N_gen` ref, gen qT [1, 44] | 7.96e-04 | 5.86e-04 | 4.06e-04 |

The respgrid MC reproduces the published number to the printed digits despite
being a different event sample (D-C4), so that caveat is real but immaterial here.
The reference swap costs 2e-05 (it removes the -7.53e-04 fiducial leak, max
2.42e-03 = D-039's gen mass window). The remaining drop is dropping the two
convention/overflow cells.

**Guard-rail:** a region-restricted prediction must not be compared to the
histmaker `nominal` -- on gen qT [1, 44] that reads 2.38e-02 with max 0.61,
because reco ptll [0, 1] is fed almost entirely by gen qT < 1 which the region
excludes. `--nominal-ref` prints it so the trap is visible.

## The gen qT [0, 1] cell, separately

Convention-contaminated against the corrected MC (production zeroes its
nonsingular below 1.0 GeV, ours below 0.1; that one gen column drives reco
ptll [0, 1] to -1.55e-02, 100 % CALC), but the ARM-TO-ARM comparison there is
convention-free because both arms use our own cutoff. Cache-free, 10 -> 22 gen
bins: **2.18e-04 yield-weighted, 5.47e-03 max**, on 1.46 % of the reco yield --
the largest per-bin granularity anywhere, as expected for the steepest part of
the spectrum, and still small in the yield-weighted sense. The convention itself
is untouched by any gen grid.

## Cost, measured (supersedes the D-041 bracket for the CENTRAL case)

748-bin fine cache, `--no-pdf`, `--threads 200`: **56 min 15 s wall**,
632 722 CPU-s (176 CPU-hours), 175.4 MB; node set 22.5 min (sum 663.144 pb),
rules 33.1 min (median 340 nodes/bin, worst training residual 2.7e-08),
fixed-order drift from step one 0.00e+00. Against the shipped 210-bin production
cache's 17.6 h, of which 325.3 min was the node set and **715.6 min the member
loop this build never runs**.

The per-bin ladder (D-C2) says the whole cost is gen qT < 2 GeV and overwhelmingly
the [0, 0.5] cell: the separate 22-bin `qT [0, 1]` cache was still in its node
stage after > 62 min at 200 threads when this was written. That is why the
[0, 1] number above is the cache-free route.

## What this changes, and what it does not

* **Does not change:** the case for the correction's gen grid. That case was
  always the variations (granularity was the limiting term in 30 of 39
  directions; alpha_s-equivalent worst case 0.152 -> 0.034 sigma) and it stands.
* **Adds:** the central prediction is confirmed insensitive to the change at the
  0.02 % level, so switching grids cannot silently move the central. That is a
  prerequisite for adopting the finer grid, and it is now measured rather than
  assumed.
* **Adds:** one genuine central gain, the top reco ptll bin, -1.09e-02 ->
  -3.94e-04, from the overflow column being resolved.
* **Retires:** the D-041 cost bracket, for the central case. 56 min, not 55-80 h.
  A full VARIATION cache on the fine grid still needs the member loop and that
  bracket still applies to it.

## NEXT

1. The variation cache on the fine grid is still the expensive open item
   (D-041 for the Jacobian). The member loop is the barrier, not the bins.
2. The gen qT [0, 1] cache is still building; when it lands, confirm the
   cache-free 2.18e-04 with the real model.
3. Decide the `matched_nons_qt_cut` convention -- still the largest single-bin
   central residual, and no gen grid touches it.

## Loose end left running (2026-08-26 12:24)

The `gen qT [0, 1]` 22-bin cache
(`/ceph/.../scetlib_ad_caches/finegrid_260826/low_qt0_1`) was still in its node
stage after **98 min at 200 threads** -- for 22 bins, longer than the 748-bin
main build took end to end. It is a BONUS: the [0, 1] number in this entry is the
cache-free route, which needs no cache. A watcher chain is still running and will
write the cache-based region-R2 comparison into
`$HOME/.claude/jobs/140d052c/tmp/central_fine/chain_low.log` when the build
finishes; the expected number to confirm is 2.18e-04 yield-weighted / 5.47e-03
max.
