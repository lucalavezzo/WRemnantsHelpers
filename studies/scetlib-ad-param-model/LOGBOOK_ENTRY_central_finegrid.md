# Logbook entry (staged) — the CENTRAL prediction on the finer response-matrix gen grid

**2026-08-26.** Companion to `LOGBOOK_ENTRY_genbinning.md`, which measured the
VARIATION side of `mz_dilepton --responseGenBinning theoryCorr`. This is the
central side, which that round left unmeasured because it needs sigma_gen on the
correction's own gen grid and no such cache existed (D-041).

Staged only: `LOGBOOK.md` and `DECISIONS.md` are untouched. Decisions in
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

