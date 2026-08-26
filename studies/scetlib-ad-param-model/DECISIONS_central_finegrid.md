# Decisions — the CENTRAL prediction on the finer response-matrix gen grid (2026-08-26)

Companion to `DECISIONS_genbinning.md` (which measured the VARIATION side).
Staged, not merged: `DECISIONS.md` and `LOGBOOK.md` are untouched by this round.

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
Narrative in `LOGBOOK_ENTRY_central_finegrid.md`.

Status key: **SETTLED** (evidence in hand) / **PROVISIONAL** / **OPEN** (needs Luca).

---

## D-C1 — the cache for a CENTRAL comparison is built with `--no-pdf`, not `--pdf-eig 0`

**What.** The fine-grid caches carry NO variation members at all.

**Why.** sigma_gen at the anchor is the replay of the compressed bin rules plus the
frozen fixed-order grid; the PDF/alphaS/muF member loop only builds the
*variation* columns and cannot move the anchor value. On the shipped 210-bin
production cache the split was, from its own build log:

```
outer node set + matched cross sections    325.3 min      <- needed
rules built                                 10.6 min      <- needed
0 PDF eigenvector pairs, resummed piece      1.6 min
   ... and the fixed-order piece            715.6 min      <- NOT needed
                                    total  ~1052 min = 17.6 h
```

so `--pdf-eig 0` still pays 68 % of the build for columns a central-value
comparison never reads. `--no-pdf` drops that stage entirely.

**Evidence.** `cache_260825_p4/build.log`; and the fine caches built here
reproduce the shipped cache's region integral to the integration tolerance
(see D-C6), which is the only thing the anchor needs to be right.

**Overturned by** wanting the Jacobian (i.e. the variation table, alphaS
sensitivity) on the fine grid — that needs the member loop and is a separate,
much larger build.

## D-C2 — the whole cost is gen qT < 2 GeV, so the region starts at 1 GeV

**What.** Measured per-bin cost on the fine grid, one bin per build, `--no-pdf`,
48-64 threads, from the `outer node set + matched cross sections` line:

| fine gen qT bin | node stage |
|---|---|
| [0, 0.5]    | **> 25 min** (killed, unfinished) |
| [1, 1.5]    | 1.3 min |
| [1.5, 2]    | 0.7 min |
| [2, 2.5]    | 0.4 min |
| [3, 3.5]    | 0.2 min |
| [4, 4.5]    | 0.2 min |
| [6, 6.5]    | 0.2 min |
| [12, 12.5]  | 0.2 min |
| [30, 31]    | 0.0 min |
| [44, 46]    | 0.1 min |
| [90, 100]   | 0.1 min |
| [30, 31] x \|Y\| [2.0, 2.5] | 0.1 min |

Whole-bin wall time (including ~20 s of process start-up, LHAPDF and the
beamfunc grid read) was 25-58 s for every bin at or above 1.5 GeV.

**Why it matters.** The D-041 bracket of 55-80 h assumed the member loop; with
`--no-pdf` and the cost concentrated in the two cells below 1 GeV, the *central*
build is minutes-to-hours, not days. The region is therefore taken as
`qT >= 1 GeV` with the [0, 1] cell built as a separate small cache — which is
also where the known nonsingular-cutoff convention difference lives, so it wanted
separating anyway.

**Overturned by** nothing measured; the ladder is a direct measurement.

## D-C3 — the reference for a gen-restricted comparison is `sum_{g in S} R_raw(b, g)`, and it is EXACTLY grid-independent

**What.** With the comparison restricted to a gen rectangle `S`, the reference at
reco level is taken to be the corrected-MC reco yield fed by that gen region,

```
ref^S(b) = sum_{g in S} R_raw(b, g)   ( = [R (x) N_gen] restricted to S )
```

rather than the histmaker's own `nominal`.

**Why this is the right choice, and why it makes the before/after clean.**
`R = R_raw / N_gen`, so `ref^S` is a plain sum of the raw reco x gen yield, and
`R_raw` is additive under gen rebinning. Refining the gen grid therefore CANNOT
move `ref^S` — the two arms share one reference bit for bit. All of the
difference between the arms lives in the numerator

```
sigma_reco^S(b) = sum_{g in S} [R_raw(b, g) / N_gen(g)] sigma(g)
```

where the coarse grid spreads sigma inside a gen cell in proportion to `N_gen`
and the fine grid resolves it. The measurement is therefore pure gen
granularity of the CENTRAL prediction, with no reference-side confounder.

**Evidence.** Measured on the region `qT [1, 44] x |Y| [0, 2.5]`:
`max |ref_fine / ref_shipped - 1| = 1.8e-14` over the 780 reco bins. The
underlying coarsening identity, per reco bin and per shipped gen bin, is
`1.2e-13` — an independent reproduction of the `2.8e-14` control in D-037.

**Consequence to keep in mind.** `ref^S` is NOT the histmaker `nominal`: it drops
reco-selected events whose gen bin is outside `S` (including the `acceptance =
False` fiducial leak of D-039). `--nominal-ref` reports both, so the connection
to the published 0.128 % is explicit rather than assumed.

## D-C4 — both arms come out of ONE histmaker file, because the production file is a DIFFERENT event sample

**What.** The shipped-grid arm is re-measured on `260826_Z_histmaker_respgrid`
(the run that carries both gen grids), not taken from the published number that
used `260723_Z_histmaker_davidFix`.

**Why.** The two files are not the same MC. Measured:

| | 260723 (production) | 260826 respgrid |
|---|---|---|
| `event_count` | 393 749 797 | 297 324 977 |
| `weight_sum`  | 33 650 105 | 251 726 049 |
| reco `nominal` total | 7.509e+06 | 5.631e+07 |
| `sum(R_raw/N_gen)` | 85.334 | 85.563 |

The yields differ by an overall ~7.5x (different `weight_sum` normalisation) but
the per-gen-bin `N_gen` ratio is NOT constant: it spans 7.4688-7.4929, a 0.32 %
spread. The response `R_raw/N_gen` itself differs by 0.27 % in its total. Using
the shipped R from one file and the fine R from the other would put a 0.3 %
statistics difference inside a 0.1 % measurement.

**Evidence.** `control_hm.py` / `control_hm2.py` in the scratch dir; the
published 0.128 % / 0.075 % / 0.073 % reproduce exactly on the 260723 file with
the unmodified `reco_central_decompose.py` (rerun today), so the published number
is anchored and the respgrid re-measurement is the honest "before" for THIS
comparison.

**Overturned by** re-running the respgrid histmaker on the 260723 file list, at
which point the two would be directly comparable.

## D-C5 — the region: gen qT [1, 44] x |Y| [0, 2.5] for the headline, [0, 1] and [1, 100] separately

**What.** Three rectangles, all with their edges on shipped-grid edges (so each
coarsens onto a whole number of shipped bins exactly):

| region | shipped gen bins | fine gen bins | refinement | share of the card's reco yield |
|---|---|---|---|---|
| **R1** qT [1, 44] x \|Y\| [0, 2.5] | 190 | 605 | 3.18x | **98.51 %** |
| **R2** qT [0, 1] x \|Y\| [0, 2.5]  | 10  | 22  | 2.20x | (the convention cell) |
| **R3** qT [1, 100] x \|Y\| [0, 2.5]| 200 | 748 | 3.74x | (adds the shipped OVERFLOW column) |

**Why R1 is the headline.** It excludes the two things that would otherwise
dominate and that are not gen granularity: the qT [0, 1] nonsingular-cutoff
convention (D-R\*; production zeroes its nonsingular below 1.0 GeV, ours below
0.1) and the shipped grid's [44, 100] OVERFLOW column, whose `N_gen` includes gen
qT > 100 while the model can only fill 44-100 (D-040). It still carries 98.5 % of
the reco yield, so it is not a corner: the headline is a statement about the
analysis, not about a slice of it.

**Why R2 separately.** On the fine grid that cell is SPLIT into [0, 0.5] and
[0.5, 1], so the affected phase space narrows -- and the arm-to-arm comparison of
the MODEL there is convention-free (both arms use our own cutoff), which makes it
the one place where granularity at very low qT can be measured cleanly even
though the closure against the corrected MC cannot.

**Why R3 separately.** It is where the two grids are genuinely different physics
rather than different granularity: the shipped column [44, 100] is the histmaker
overflow.

**Overturned by** nothing; but a region that also resolved gen qT < 1 in the
closure (not only in the arm-to-arm difference) needs the cutoff convention
settled first.

## D-C6 — the central granularity is measured TWICE, once with no cache at all — SETTLED

**What.** Besides the cache-based arm-to-arm comparison, the same quantity is
measured with no cache, no SCETlib and no build, by folding the PRODUCTION CorrZ
spectrum through `R_raw/N_gen` on the two gen grids:

```
CEN_GRAIN(b) = [ sum_g R_raw(b,g) sigma_CorrZ(g)/N_gen(g) ]
             / [ sum_G R_raw(b,G) sigma_CorrZ(G)/N_gen(G) ]
```

**Why it is legitimate and why it matters.** The model's sigma_gen agrees with
sigma_CorrZ to 0.075 % at gen level (the CALC term), so substituting one for the
other changes the *granularity* of the fold at second order. In exchange the
measurement becomes free and unlimited in reach: it covers all 770 fine gen bins
including the two cells below 1 GeV and the overflow column, which no affordable
cache does. It is the central analogue of the `grain_finegrid.py` GRAIN used for
the variations, and it BOUNDS what the cache-based number can be -- anything
beyond it is the two builds' own reproducibility, not binning.

**Result (yield-weighted mean |dev| over the 780 reco bins, shape):**

| gen region | shipped -> fine gen bins | reco-yield share | wmean\|dev\| | max |
|---|---|---|---|---|
| qT [1, 44]  | 190 -> 605 | 0.9851 | **1.79e-04** | 1.06e-03 |
| qT [0, 44]  | 200 -> 627 | 0.9983 | 1.79e-04 | 1.06e-03 |
| qT [0, 1]   | 10 -> 22   | 0.0146 | 2.18e-04 | 5.47e-03 |
| qT [0, 100] | 210 -> 770 | 1.0000 | 5.50e-04 | 1.79e-02 |

Controls: the CorrZ total is identical on the two grids to `-2.2e-16` (the merge
is an exact sum on both), and the total fine/shipped shift on qT [1, 44] is
`+6.1e-06`.

**Reading.** Against the published central closure of `1.28e-03`, the gen
granularity of the CENTRAL prediction on the analysis region is `1.79e-04`, i.e.
**14 % of the residual and 0.018 % of the prediction**. The [0, 100] row is NOT
granularity: it is dominated by the shipped grid's [44, 100] OVERFLOW column,
whose `N_gen` includes gen qT > 100 that the model cannot fill (D-040) -- it shows
up as a single `+1.06 %` step in reco ptll [37, 44] and nowhere else.

**Overturned by** the cache-based arm-to-arm number coming out materially larger
than 1.79e-04 on the same region, which would mean sigma_model has within-cell
structure that sigma_CorrZ does not.

## D-C7 — MEASURED: the finer gen grid does NOT move the central closure on the analysis region — SETTLED

**What.** Cache-based before/after on gen qT [1, 44] x |Y| [0, 2.5] (190 -> 605 gen
bins, 98.51 % of the card's reco yield), yield-weighted mean |dev| over the 780
reco bins, shape:

| term | shipped | fine | ratio | shipped max | fine max |
|---|---|---|---|---|---|
| TOTAL model / corrected MC | 7.96e-04 | 8.19e-04 | 1.03 | 1.113e-02 | 1.128e-02 |
| CALC model / (R (x) CorrZ) | 5.86e-04 | 5.73e-04 | 0.98 | 1.078e-02 | 1.106e-02 |
| MC (R (x) CorrZ) / corrected MC | 4.06e-04 | 4.45e-04 | 1.10 | 1.925e-03 | 1.767e-03 |

The central prediction itself changes by **1.94e-04 yield-weighted, 1.33e-03
max**, with the region total shifting by only `-3e-06`.

**And the change is NOT DIRECTIONAL, which is what makes this a result rather
than an absence of one.** Of the 780 reco bins the fine grid is closer to the MC
in **392 -- 50.3 % by count, 51.0 % by yield**, a coin flip. The correlation
between the shipped residual and the shift the fine grid applies is **+0.15**,
i.e. the shift does not oppose the residual. And the metric moves by +2.3e-05
while the per-bin shift is 1.94e-04, eight times larger: a reshuffle, not a fix
and not a degradation. The same three statistics on gen qT [1, 100] (D-C8), where
there IS a real correction, read -0.69 correlation and a -2.27e-04 metric
improvement -- so the statistics do discriminate.

**Why this is a result and not a non-result.** It is the prediction that was
worth testing: granularity cancels in a RATIO, which is why it dominated the
variation comparison, whereas the central closure is set by two things no gen
grid touches -- the different nonsingular generator (CALC, 0.075 % as published)
and the MC term (0.073 %). The measurement confirms it quantitatively: the
granularity of the central prediction is 14 % of the residual and 0.018 % of the
prediction, it has no trend across reco ptll (a +/-2e-04 wiggle against the
closure's smooth +8e-04 -> +2e-04 curve), and it is largest exactly where the
shipped gen bins are widest (reco ptll 20-33 GeV, +/-0.05-0.10 %). **The fine grid
buys accuracy where it was needed and costs nothing where it was not.**

**Evidence that it is not build noise.** In-situ two-build floor (coarsening the
fine sigma_gen back onto the shipped region grid): median |dev| 6.1e-07,
p95 5.5e-06, max 1.7e-05, N_gen-weighted 1.5e-06 -- 20x below the published
3.1e-05 sigma floor and two orders of magnitude below the 1.94e-04 effect. Arm
separation proven (two ScetlibADXsec objects, 210 vs 748 cache bins, region
sigma_gen 597.03225 vs 597.03269 pb). Independent cache-free route agrees to 8 %
(D-C6).

**Overturned by** a fit-level measurement showing a sigma(alpha_s) or bias change
larger than this residual implies -- which would mean the central enters the fit
more strongly than the closure metric suggests.

## D-C8 — MEASURED: the real central gain is the top reco ptll bin, and it is the OVERFLOW, not resolution — SETTLED

**What.** The same comparison over gen qT [1, 100] x |Y| [0, 2.5] (200 -> 748 gen
bins), i.e. including the shipped grid's last gen column [44, 100], which is the
histmaker OVERFLOW (D-040):

| term | shipped | fine | ratio |
|---|---|---|---|
| TOTAL wmean | 1.044e-03 | 8.17e-04 | 0.78 |
| TOTAL max | 1.773e-02 | 1.128e-02 | 0.64 |
| MC wmean | 7.18e-04 | 4.45e-04 | 0.62 |
| MC max | 1.738e-02 | 1.764e-03 | **0.10** |
| reco ptll [37, 44], TOTAL | -1.09e-02 | -3.94e-04 | **28x** |

**Why.** On the shipped grid that column's `N_gen` holds every gen qT > 44,
including the 16.97 % of it above 100 that the correction file cannot cover, so
the model under-fills it and the deficit leaks into reco ptll [37, 44]. The fine
grid resolves 44-100 and gives qT > 100 its own column, which `load_R` drops --
so the model is never asked for a cross section it does not have.

**Note that the reference is no longer exactly identical between the arms on this
region** (`max |ref_fine/ref_shipped - 1| = 2.24e-05`, against 1.8e-14 on
qT [1, 44]) precisely because the shipped overflow contains the > 100 events. That
2.24e-05 is the size of the physics difference, and it is 500x smaller than the
1.09e-02 improvement it produces, because those events reconstruct almost nowhere
in the fit's ptll range.

**Overturned by** nothing measured; but the same argument says the fix matters
only for the last reco bin, so its fit impact should be checked rather than
assumed.

## D-C9 — the published 0.128 % is reproduced and the ladder to the region number is closed — SETTLED

Re-run today with the unmodified `reco_central_decompose.py` on the published
inputs: TOTAL **1.277e-03**, CALC **7.48e-04**, MC **7.13e-04**, against the
published 1.28e-03 / 7.5e-04 / 7.3e-04, with the per-ptll profile matching
(ptll [0,1] -1.55e-02, ptll [37,44] -1.03e-02).

And the respgrid MC gives the **same three numbers to the printed digits**
(1.277e-03 / 7.48e-04 / 7.13e-04) under the published definition, so D-C4's
sample difference, while real, does not matter at this precision. Swapping the
reference from the histmaker `nominal` to `R (x) N_gen` costs 2e-05 (it removes
the -7.53e-04 fiducial leak, max 2.42e-03, i.e. D-039's gen mass window).

**Guard-rail recorded.** A REGION-restricted prediction must NOT be compared to
the histmaker `nominal`: on gen qT [1, 44] that gives 2.38e-02 with a max of 0.61,
because reco ptll [0, 1] is fed almost entirely by gen qT < 1, which the region
excludes. `--nominal-ref` prints it so the trap is visible rather than latent.

## D-C10 — COST REPORT: the main build came in cheap, the gen qT [0, 1] cache did not — SETTLED (measured)

**Main build, as predicted by the ladder.** gen qT [1, 100] x all 11 |Y| = 748
bins, `--no-pdf`, `--threads 200`: **56 min 15 s wall**, 632 722 CPU-s
(176 CPU-hours), 175.4 MB. Node set 22.5 min (sum 663.144 pb), rules 33.1 min
(median 340 nodes/bin, worst training residual 2.7e-08), fixed-order drift from
step one exactly 0. Against the shipped 210-bin production cache's 17.6 h, of
which 325.3 min was the node set and 715.6 min the member loop. So the D-041
bracket of 55-80 h is retired **for the central case**; it still applies to a
variation cache, which needs the member loop.

**The gen qT [0, 1] cache is the exception, and it was flagged before it started.**
22 bins, `--threads 200`, and its node stage was still running after **> 65 min**
-- longer than the 748-bin main build took end to end. Consistent with the ladder
(a single [0, 0.5] bin ran > 25 min at 64 threads and was killed unfinished), and
the reason the region was defined to start at 1 GeV in the first place (D-C5).
Nothing in this round depends on it: the [0, 1] number is the cache-free route
(D-C6), and the cache-based confirmation is a bonus that will land when it lands.

**Practical consequence for anyone building on the correction's grid:** budget the
two sub-1-GeV qT rows separately from the rest of the grid, and expect them to
cost more than the other 68 rows combined.

---
