# Decisions — response-matrix gen binning on the CorrZ grid (2026-08-26)

Staged for `DECISIONS.md`. Every entry: what, why, the evidence, and what would
overturn it. Numbers are measured in this round unless attributed.

Round: implement a **finer gen binning for the response matrix, matching the
CorrZ theory-correction file's own (qT, |Y|, Q) binning**, without disturbing the
unfolding binning. Luca's instruction of 2026-08-26, which supersedes the
previous night's "take grid D (52x11)" recommendation.

Code: `WRemnants` (branch `scetlib-np-param-model`, working tree), files
`wremnants/utilities/binning.py`, `wremnants/production/theory_corrections.py`,
`wremnants/production/unfolding_tools.py`,
`wremnants/postprocessing/scetlib_np/response_matrix.py`,
`scripts/histmakers/mz_dilepton.py`, `scripts/rabbit/setupRabbit.py`.
Study scripts: `response_binning_ab.py`, `response_grid_report.py`, and
`--joint/--gentot` added to `grain_finegrid.py`.

---

## D-G1 — the target grid is READ FROM the correction file, never hardcoded

`theory_corrections.get_corr_grid_edges(generator, "Z")` opens the correction
pickle and returns the edges of the kinematic axes of the very histogram the
histmaker looks up. `mz_dilepton --responseGenBinning theoryCorr` builds the
response gen axes from `args.theoryCorr[0]`.

**Why.** The applied correction weight is a bin lookup on that grid
(`TensorCorrectionsHelper4D::operator()` = `weight * get_value(hist, massVgen,
absYVgen, ptVgen, chargeVgen)` — no interpolation), so the grid is a property of
the file, not of our code. A hardcoded edge list silently rots the moment a new
correction file is produced.

**Evidence.** For
`scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_CorrZ`:
`Q` 1 bin `[60, 120]`; `absY` 17 bins to 5.0
`[0, .15, .3, .5, .7, .9, 1.1, 1.3, 1.5, 1.8, 2.0, 2.5, 2.75, 3, 3.25, 3.5, 4, 5]`;
`qT` 70 bins to 100 (0.5 GeV steps to 15, 1 GeV to 40, then 42, 44, ..., 60, 65,
70, 80, 90, 100). The `_pdfas` file has the identical kinematic axes.

**Overturned by** nothing in this repo: a different correction grid is picked up
automatically. If two `--theoryCorr` entries ever disagree on their grid the code
takes the first one's — currently they do not (checked, main and `_pdfas`).

## D-G2 — the shipped gen edges NEST in the correction's, so the fold can tile

Checked programmatically: every one of the card's 21 `ptVGen` edges
`[0,1,...,12,14,16,18,20,24,28,33,44]` and all 11 `absYVGen` edges are edges of
the correction's grid ("ALL NEST"), and so is every reco `ptll` edge
`[0,1,1.5,...,12,13,...,20,22,24,26,28,30,33,37,44,100]`.

**Why it matters.** `GenFold` refuses a cache whose bins do not exactly tile the
card's gen bins. Nesting means (a) the new grid is a strict refinement, so any
coarsening back to the shipped grid is an exact sum — which is what makes the
A/B controls below exact rather than approximate — and (b) a bin-sharded cache
build on the new grid can be merged and coarsened without holes.

**Overturned by** a correction file whose edges do not contain the reco binning;
then a refinement that tiles both would have to be the union of the two grids.

## D-G3 — |Y| truncated at the gen acceptance edge (2.5): exactly the CorrZ 11 bins

The response `absYVGen` axis takes the correction's edges up to 2.5 (11 bins,
i.e. the shipped 10 plus the edge at 2.0) with `overflow=True`, not the
correction's full 17 bins to 5.0.

**Why.** The gen fiducial selection is `prefsrV_absY < 2.5 && prefsrV_mass > 60
&& prefsrV_mass < 120` (logged by `select_fiducial_space`), and R is the
`acceptance = True` slice. Bins above 2.5 are therefore empty by construction —
measured **0.000e+00** yield at `acceptance=True` in the `absYVGen` overflow.
Storing them would cost bins in the histogram and, worse, invite a cache built
over |Y| up to 5 where the model has no acceptance.

**Overturned by** a decision to fold out-of-acceptance gen columns into R (see
D-G11): then the correction's 2.5–5 cells become live and should be stored.

## D-G4 — no Q (mass) axis is added, because the grid already resolves it exactly

**Why.** The correction's `Q` axis is a **single bin `[60, 120]`**, and the gen
acceptance *is* `60 < prefsrV_mass < 120`. So every event in R sits in that one Q
cell: there is no Q granularity left to resolve. Adding a 1-bin `massVGen` axis
would change nothing except the histogram's rank.

**Evidence.** Axes dump above; the fiducial selection string above; and the
measured Q flow content of the correction (next decision).

**Overturned by** a correction file with a differential Q axis — then Q joins the
response grid and this decision must be revisited, which is why the edges are
read from the file (D-G1) and the truncation is expressed against the acceptance,
not against a constant.

## D-G5 — qT keeps the correction's full range, so gen qT > 44 is RESOLVED

The response `ptVGen` axis is the correction's 70 bins to 100 GeV with
`overflow=True`. The shipped axis stops at 44 with an overflow that the datacard
mislabels `[44, 100]`.

**Why, and what it fixes.** Measured on the full-statistics runs: **11.65 %** of
`N_gen` has gen qT > 44 (11.6497 % as the shipped grid's overflow, 11.6507 % as
the resolved sum — the same events, two grids), and **1.977 %** has gen
qT > 100, i.e. **17.0 % of the shipped grid's last column**. The correction's own
flow bins are **exactly 1.0** (measured: Q under/over, qT over, absY over all
1.0), so those events carry *no* correction at all.

That closes the reco-2D round's open question. It measured
`sigma_CorrZ/N_gen = 0.847` in the last gen bin against `1.020 +- 0.002` below
44, i.e. a **17.0 %** relative deficit, and left open "whether the 15.3 % is
entirely the qT > 100 tail or partly the correction not being applied above 100".
It is **the tail, to three digits**: 1.977/11.651 = **16.97 %**, against the
measured 1 − 0.847/1.020 = **17.0 %**. Nothing is missing above 100 — there is
simply nothing there to apply.

**Overturned by** a correction file that extends past 100 GeV.

## D-G6 — additive and opt-in: the unfolding path is byte-identical

`--responseGenBinning` defaults to `none`. When set, `UnfolderZ` builds a
*second* set of gen axes and appends two histograms
(`nominal_<level>_yieldsResponse`, `<level>_response`); `self.unfolding_axes` is
never touched. `binning.get_unfolding_dilepton_axes` grew one optional
`edges_override=None` argument whose default path is the original code.

**Evidence (the hard requirement).** Same command, same single input file, `-j 1`
(single-threaded, so the atomic-fill summation order cannot differ), arm B = arm
A + the flag:

| | |
|---|---|
| histograms identical **bit for bit** | **464** |
| histograms differing numerically | 0 |
| histograms with different axes | 0 |
| only in B (the new outputs) | 2 |
| only in A (lost) | **0** |

`response_binning_ab.py` compares `values` and `variances` including flow, and
the axis signature (name, size, edges, flow traits) of every histogram of every
sample group.

**Overturned by** nothing short of a code change; rerun the A/B after any.

## D-G7 — the response histogram carries NO helicity axis

It is filled with `nominal_weight`, while the unfolding histogram is filled with
the `nominal_weight_helicity` partition.

**Why.** (i) The response is recovered by *summing* the helicity partition
(`response_matrix.load_R` projects, which sums `helicitySig`), so the two give
the same R while the un-partitioned one is 9x smaller. (ii) The helicity route
would require `make_helicity_weight_helper` to rebin `w_z_helicity_xsecs.hdf5`
onto the finer grid, and `UnfolderZ.__init__` *raises* unless the gen axes are a
subset of that file's — an entirely avoidable coupling.

**Evidence.** In the same file, the response histogram coarsened onto the
unfolding grid (an exact sum, by D-G2) equals the unfolding histogram projected
over `helicitySig`: max |difference| **2.8e-14** (3.8e-16 of the largest bin) at
`acceptance=True` and 8.9e-16 at `acceptance=False`; the sums agree to
`+0.000e+00` relative. Float round-off, i.e. an identity.

**Overturned by** a use of R that needs the angular partition per gen bin
(nothing in `scetlib_ad`/`scetlib_np` does).

## D-G8 — the response axes reuse the unfolding acceptance flag and selections

`get_unfolding_dilepton_axes` returns selections derived from its axes; for the
response axes those are **discarded** and `self.unfolding_selections` is used.

**Why.** The acceptance flag is a physics definition, not a binning artefact.
Deriving it from the override would silently move the fiducial region the day
someone widens the response |Y| range (the selection string is built from the
axis' last edge).

**Evidence.** The A/B (D-G6) — the acceptance column and every selection are
untouched; and the identity check passes at `acceptance=False` too, i.e. both
histograms partition the same events the same way.

## D-G9 — `load_R` drops the > 100 gen column rather than inventing a bin

`PTVGEN_OVERFLOW_EDGE = 100` exists so the shipped axis' overflow becomes a
trailing gen bin `(44, 100]`. On the new axis the last edge *is* 100, so
appending would create a degenerate `[100, 100]` bin. `load_R` now detects that
and drops the overflow instead.

**Evidence / cost.** Probed on a small run: `R` comes out `(40, 20, 21, 10)` for
the unfolding grid and `(40, 20, 70, 11)` for the response grid, with no gen bin
having `N_gen <= 0` (770 of 770 populated — no hole for `GenFold`). The dropped
column is 2.0 % of `N_gen` but only **7.8e-05** of the folded reco yield: gen
qT > 100 essentially never reconstructs below ptll = 100. Keeping it would
require the model to supply sigma_gen above 100, where the templates apply no
correction at all.

**Overturned by** a fit that uses reco ptll above 100 GeV.

## D-G10 — the response histogram inherits the run's reco axes, with no new knob

`nominal_axes` / `nominal_cols`, exactly as the unfolding histogram. A 2D
`--axes yll ptll` run gives 800 reco bins; a production `--csVarsHist` run gives
25600, i.e. 25600 x 852 x 2 = 43.6 M bins = 0.70 GB. That is affordable because
narf fills **one shared atomic histogram** when IMT is on
(`histutils._histo_boost`: `force_atomic = ROOT.ROOT.IsImplicitMTEnabled()`), not
one per slot — the production unfolding histogram is already 106 M bins.

**Overturned by** a memory problem in a production rerun; the fix would be a
reco-axis subset argument, not a redesign.

## D-G11 — RETRACTION: the residual left at the target grid is the GEN MASS WINDOW, not |Y| > 2.5

The reco-2D round recorded the `R @ N_gen` vs nominal offset (−7.5e-04) as
"reco-selected events with gen |Y| > 2.5, dropped by the gen grid". **That
attribution is wrong.** Splitting the `acceptance = False` yield in the fit's reco
range (ptll 1–44) by whether the gen |Y| overflow is populated:

| | fraction of the reco yield |
|---|---|
| `acceptance = True` | 99.925 % |
| `acceptance = False`, gen \|Y\| > 2.5 | **2.95e-06** |
| `acceptance = False`, gen \|Y\| in range (⇒ failed the gen mass window) | **7.47e-04** |
| total leak | 7.50e-04 |

So 99.6 % of the leak is events whose reco m(ll) is inside 60–120 while their
**preFSR** mass is not. For exactly those events the correction lookup lands in
the Q flow bin, where the file holds **1.0** — the template applies no
correction, and the fold has no gen column at all.

**This explains the entire residual left at the correction's own grid, with no
free parameter.** GRAIN must vanish identically on this grid (the fold is
algebraically the per-event sum when the weight is constant on the cells), and
what is measured instead of zero is

    residual(direction) ~= f_mass x |rho(direction) - 1| ,  f_mass = 7.47e-04

against the measured yield-weighted response of each direction:
**measured/predicted = 1.11 median, 1.01–1.14 (10th–90th pct), log-log
correlation +0.9989** over the 35 non-alpha_s directions (measured median
3.410e-06 against 3.240e-06 predicted). Both leak fractions are measured in the
same file, in the fit's reco range.

**A wrong hypothesis, recorded because it was tested and killed:** the first
version of this prediction used the |Y| > 2.5 leak with the correction's own
2.5–5 cells as `rho_out`. It predicts a median of **2.4e-07** against the
measured 3.4e-06 — 7 % of it. The |Y| explanation is dead; the mass-window one is
quantitative.

**Consequence.** The last 3.4e-06 is a *fiducial* mismatch, not a binning one,
and no gen binning can move it. It sits a factor 2 **below** the model's own
gen-level calculation error (CALC median 7.8e-06, flat against the grid), so it
limits nothing. If it is ever worth removing, the fix is to give the
out-of-gen-mass-window events a gen column whose response is frozen to 1, which
is what the templates do — not a finer grid.

**Overturned by** a measurement showing the ratio drifting away from 1 on a
different reco range, or by a gen definition change (postfsr instead of prefsr)
that moves `f_mass`.

## D-G12 — the two alpha_s legs are confirmed, by an independent route, as NOT granularity

The same prediction that lands within 14 % for all 35 other directions
under-predicts the two `pdfCT18ZNNLO_as_*` legs by a factor **23** (measured
3.303e-04 and 3.214e-04 against 1.410e-05 predicted). They are the only two
directions in `theory_corr_weight_map` with `alphas=True`, i.e. the only two
whose applied weight is the binned correction ratio **times an event-level LHAPDF
member ratio**. Last night's Finding 4 inferred this from the code plus the fact
that only these two failed to improve with resolution; here it falls out of a
quantitative prediction that works for everything else.

**Overturned by** the experiment already on the books: rerun with `_pdfas`
dropped from `theory_corr_weight_map` (pure bin lookup) and re-measure — those
two should then land on the same 1.1 ratio as the rest.

## D-G13 — what the new grid buys, and the cost that has to be decided

Measured (see `LOGBOOK_ENTRY_genbinning.md` for the tables). Granularity, which
the reco-2D round found to be the limiting term in 30 of 39 directions, is
**structurally eliminated**: yield-weighted median 5.357e-05 (shipped 21 x 10) ->
3.410e-06, per-bin max median 6.825e-04 -> 3.064e-05, and the count of directions
where GRAIN exceeds the calculation error 32/39 -> 4/39 (the two identically-zero
`b_qqDS` directions and the two alpha_s legs). The alpha_s footprint of the worst
direction goes 0.1516 sigma -> 0.0341 sigma, and excluding the two alpha_s legs
0.1516 -> 0.0017 sigma; in quadrature 0.2698 -> 0.0456 sigma. Composed with the
(grid-flat) CALC, the reco-level TOTAL becomes calculation-limited: alpha_s
equivalent worst 0.199 -> 0.092 sigma and quadrature 0.317 -> 0.185 sigma, both
equal to the CALC-alone values.

**The cost is the cache, and it is the decision to take.** 781 gen bins against
the shipped 210. From the shipped build log (17.6 h at 210 threads,
`target_precision_rel = 1e-4`) and the cache's own rule records, the outer-node
stage is linear in bins (~3.7x) while the fixed-order stage is dominated by two
qT cells (qT [0,1] 23.2 %, qT [44,100] 18.4 % of all nodes) which the new grid
splits: ~3–4.5x overall, **~55–80 h at 210 threads**, ~800 MB. A 1-bin
`--subset` timing test on the new runcard replaces that bracket with a
measurement in minutes and should be done before committing the build.

**Why the correction's grid rather than the cheaper compromise (grid D, 583
bins, ~45–70 h).** On alpha_s they are equal (0.034 vs 0.035 sigma — both sit on
the alpha_s-leg floor). The argument for the correction's grid is structural, not
numerical: on it the bin-averaged response *is* the applied per-event weight, for
every direction and for any future variation set, so granularity is identically
zero rather than merely small — as the 1.11-ratio prediction above demonstrates
by accounting for the whole remaining residual with an effect that has nothing to
do with binning. Grid D is a cost/benefit compromise that would have to be
re-derived whenever the variation set or the correction grid changes.

**Overturned by** the `--subset` timing test coming back far worse than the
bracket, in which case grid D is the fallback and the α_s conclusion is unchanged.
