# Decisions — extending the response matrix's gen binning above qT 100 (2026-08-26)

Staged, not merged: `DECISIONS.md` and `LOGBOOK.md` are untouched by this round.
Narrative in `LOGBOOK_ENTRY_above100.md`.
Continues `DECISIONS_genbinning.md` (the variations) and
`DECISIONS_central_finegrid.md` (the central prediction), i.e. D-037..D-041 and
D-C1..D-C10.

Status key: **SETTLED** (evidence in hand) / **PROVISIONAL** (pending the
regenerated correction) / **OPEN**.

---

## D-A1 — the consistency question is REAL and it is worth ~7 %, not ~0 % — SETTLED

**What.** Above gen qT 100 the correction file has no bins and its flow bins are
exactly 1.0 (re-verified: Q under and over, qT under and over, absY over, all
`min = max = 1` bit-exact over 2106 cells), so the MiNNLO templates are
UNCORRECTED there while the differentiable model calculates a corrected cross
section. The size of that disagreement is not small in the region itself.

**Evidence.** The `N_gen`-weighted CorrZ central ratio over |Y| < 2.5 in the last
qT rows, from the correction file:

| gen qT | σ_theory/σ_MiNNLO | spread over abs(Y) | 38-variation envelope |
|---|---|---|---|
| 46-48   | 1.0205 | 1.0145-1.0299 | |
| 58-60   | 0.9766 | 0.9714-0.9816 | |
| 70-80   | 0.9314 | 0.9275-0.9336 | 10.84 % |
| 80-90   | 0.9255 | 0.9227-0.9304 | 12.61 % |
| 90-100  | 0.9372 | 0.9314-0.9410 | 13.81 % |

So at the edge of its support the correction is **6-7 % below 1** and still
moving (it bottoms out around 80-90 GeV and turns back up), and the theory
envelope on it is ~14 %. Treating everything above 100 as "correction = 1" is a
~7 % statement about 1.977 % of `N_gen`, not a rounding error, and the curvature
at the edge means it cannot be safely extrapolated either. **This is why option
(a) -- extend the corrections -- is the right call and not merely the tidier
one.** (Luca's decision, taken independently: "this is the most correct thing to
do.")

## D-A2 — but the CURRENT fit cannot see it: gen qT > 100 feeds 1.63e-07 of the fit's reco yield — SETTLED (measured)

**What.** Measured on `260826_Z_histmaker_respgrid` (the shipped response grid,
where gen qT > 100 is one resolved overflow column), at `acceptance = True`, over
the fit's 780 reco bins (reco ptll < 44, 39 x 20):

```
fit-range corrected-MC yield                        5.432660e+07
of which fed by gen qT > 100                        8.86e+00      -> 1.63e-07
per-bin fraction: median 0, max 2.24e-05 (one yll bin at reco ptll [37, 44])
number of fit reco bins with ANY gen qT > 100 feed: 5 of 39 ptll bins
reco ptll [44, 100] -- NOT in the fit -- fraction  2.81e-03
```

The 8.86 is a weight sum of order ten MC events: the above-100 column is
statistically empty inside the fit's reco range. Since the model's output is a
RATIO (`compute()` returns `rnorm(b) = σ_reco(λ)/σ_reco(λ_central)`), including
or excluding a λ-independent piece of size `f(b)` changes `rnorm` by
`f(b)·|rnorm-1|`, so with `f ≤ 2.24e-05` every treatment of the region agrees to
`≲ 1e-06` on `rnorm` -- 500x below the calculation floor (5.7e-04) and 30x below
the two-build floor.

**Consequence, stated plainly.** Extending the response above 100 is the CORRECT
thing to do and it is nearly free, but it is not a fix for a visible bias in
today's fit. Where it does matter is reco ptll [44, 100], at 2.81e-03 x 7 % =
2e-04 -- i.e. **if the fit's reco range is ever extended past 44 GeV, this stops
being bookkeeping**.

## D-A3 — the enforcement is an assertion, not a convention — SETTLED

**What.** `theory_corrections.check_gen_grid_vs_correction(gen_axes, generator)`
reads the correction file and refuses a gen grid that

1. has an edge inside the correction's range that is NOT a correction edge
   (a gen bin straddling a correction cell -> the fold bin-averages the applied
   weight), or
2. has any edge ABOVE the correction's last qT edge, unless
   `allow_uncorrected_above=True` is passed explicitly (which also logs a
   PROVISIONAL warning naming the offending edges).

Truncating below the correction's range is allowed and only logged (it is a
sub-union: |Y| stops at the gen acceptance 2.5 while the correction runs to 5.0).

**Where it is called.**

* `scripts/histmakers/mz_dilepton.py`, right after the response gen edges are
  built -- so a bad grid never reaches a histogram;
* `scripts/rabbit/scetlib_ad/prepare_cache_for_card.py::gen_axes_from_card` --
  the cache writes those very edges into the SCETlib runcard, so this is exactly
  where a mismatch would be inherited silently.

The second call is AUTOMATIC because the datacard now carries the correction's
name: `load_R` reads `responseGenBinning`/`theoryCorr` out of the histmaker's own
`meta_info` (`response_matrix.corr_generator_of`) and `setupRabbit` stores it in
the response auxiliary as `corr_generator`. An older card without that key
degrades to a printed warning, not an error.

**Evidence (unit test, all five cases as intended).** shipped 70x11 grid PASSES;
the coarser 21-bin unfolding grid PASSES (sub-union, `truncated_at 44` logged);
an edge at 0.25 RAISES; the extension above 100 RAISES without the opt-in and
passes with it, printing the PROVISIONAL warning.

## D-A4 — the histmaker flag is a temporary bridge, and the end state needs no flag — SETTLED

`mz_dilepton --responseGenPtVExtend <edges...>` appends edges above the
correction's last qT edge (validated strictly increasing and all above it). It
exists ONLY to build and measure before the regenerated correction exists.

Once the correction covers the wider grid, `--responseGenBinning theoryCorr`
reads the new grid straight out of the correction file: no flag, no code change,
and `check_gen_grid_vs_correction` then passes with `allow_uncorrected_above`
FALSE, which is the state the assertion is designed to protect.


## D-A5 — the production chain that has to carry the new edges — SETTLED (read out of the code and the file's own provenance)

**What.** `make_theory_corr.py` does not choose the correction's qT axis: it
rebins its inputs to their COMMON binning (`read_matched_scetlib_hist` via
`read_matched_scetlib_dyturbo_hist`, then `make_corr_from_ratio` ->
`rebin_corr_hists` -> `hh.rebinHistsToCommon`). An edge missing from ANY input is
therefore missing from the correction.

The four inputs, from the shipped file's own recorded command
(`meta_data["command"]` inside `..._CorrZ.pkl.lz4`), all still on disk:

| input | file | qT / ptVgen coverage today |
|---|---|---|
| SCETlib resummed | `.../com13_ct18z_newnps_n3+0ll_lattice_lambda4bugfix_franksvalsvars_fine/inclusive_Z_..._combined.pkl` | to 100 |
| SCETlib nnlo_sing | `.../..._fine_nnlo_sing/inclusive_Z_..._combined.pkl` | to 100 |
| DYTurbo fixed order | `.../DYTURBO/nnlo-scetlibmatch-13TeV-CT18Z-finer-bin/scalevariations/z0/results_z-2d-nnlo-vj-CT18ZNNLO-{scale}-scetlibmatch.txt`, 7 scale files | to 100 (last rows 65-70, 70-80, 80-90, 90-100) |
| MiNNLO denominator | `/scratch/submit/cms/areimers/wmass/gendistributions/w_z_gen_dists_maxFiles_m1_finePtAbsY.hdf5`, hist `nominal_gen` | **0.5 GeV steps to 100, then ONE bin [100, 13000]** |

**The one that is easy to miss is the fourth.** The MiNNLO gen file has a single
bin above 100, so even with all three theory inputs extended, the common
rebinning would collapse the whole above-100 region to one cell. It has to be
remade with ptVgen edges containing the new ones -- a gen-only histmaker pass,
the cheapest item on the list, but a blocking one.

**The model side needs nothing.** The cache's runcard is
`calculation_piece = matched`, `fixed_order = nnlo`, `fo_order2_analytic = yes`:
SCETlib computes its own fixed order analytically, so no external file caps the
model at 100. Confirmed by the build below.

## D-A6 — cost of the extension on OUR side, measured — SETTLED

The histmaker and the cache both take the new edges without a code change:

* histmaker, full Zmumu statistics (2779 files, `-j 128`): the response gen axis
  goes from 70 x 11 = 770 to 82 x 11 = 902 gen bins. See LOGBOOK for the wall
  time; the incremental cost of the extra columns is below the run-to-run spread.
* cache, `--grid-json` with qT [1, 1000] x 11 |Y| = 880 bins, `--no-pdf`,
  `--threads 200`: the 132 above-100 bins are the cheapest in the grid
  (the measured ladder is 0.0-0.2 min/bin above gen qT 3, against > 25 min for
  one bin below 0.5 GeV; D-C2).


## D-A7 — the model needs no new input above 100, and that is checked not assumed — SETTLED

The cache runcard (`cache_260825_p4/base_from_reference.conf`, the literal merge
of the reference SCETlib run's own cards) has
`calculation_piece = matched`, `fixed_order = nnlo`, `fo_order2_analytic = yes`,
`muf_max = 13000`, `Ecm = 13000`. The fixed-order piece is SCETlib's own analytic
O(as^2), not a DYTurbo file, so nothing in the model's inputs stops at 100 --
unlike the CORRECTION, whose fixed order IS a DYTurbo text file that ends at 100.

That asymmetry is precisely the inconsistency of D-A1 restated: the model can
calculate above 100 and the correction currently cannot, which is why the two
sides disagree there and why the fix is on the correction's side.


## D-A8 — the unfolding path is STILL byte-identical with the extension — SETTLED (measured)

Same A/B as D-037, one input file, `-j 1` (single-threaded, so atomic fill order
cannot differ), arm B = arm A + `--responseGenBinning theoryCorr
--responseGenPtVExtend 110 120 130 140 150 170 200 250 300 400 600 1000`:

```
histograms identical BIT FOR BIT : 464
histograms differing numerically :   0
histograms with different axes   :   0
only in B (the new outputs)      :   2   nominal_prefsr_yieldsResponse
                                         prefsr_response
only in A (LOST -- must be 0)    :   0
```

and the internal identity, which is the one that shows the extension is an EXACT
refinement rather than merely additive: the response hist coarsened onto the
unfolding grid -- where the unfolding axis' last group is its [44, inf) overflow,
so every new above-100 column plus the response's own (>1000) overflow is summed
into it -- equals the unfolding hist summed over its helicity partition:

```
acceptance=True   max|diff| 2.84e-14  (3.76e-16 of the largest bin), sums equal
                  to rel +0.000e+00
acceptance=False  max|diff| 8.88e-16  (4.03e-16 of the largest bin), same
```

The 2.84e-14 is the same number the unextended grid gave (D-037), so nothing was
lost or double-counted by adding the columns.


## D-A9 — everything below 100 is BIT-IDENTICAL, so no closure number can move — SETTLED (measured)

Three arms off ONE input file at `-j 1`: A = baseline, C = A + the response grid
(the shipped configuration), B = A + the response grid EXTENDED above 100.

```
A vs C  (re-verification of D-037)  464 bit-identical, 2 new, 0 lost
A vs B  (D-A8)                      464 bit-identical, 2 new, 0 lost
B restricted to gen qT < 100  vs  C
    nominal_prefsr_yieldsResponse   BITWISE EQUAL, max|diff| 0.000e+00
    prefsr_response                 BITWISE EQUAL, max|diff| 0.000e+00
C's DROPPED overflow column  vs  the SUM of B's new columns (+ B's own overflow)
    response (acceptance=True)      2.020931882  vs  2.020931882   rel +0.000e+00
    gen total N_gen                 1647.993728  vs  1647.993728   rel -1.11e-16
```

**Why this is the answer to "measure the closure and the granularity before and
after".** The extension adds columns and touches nothing else, bit for bit. Any
reco-level closure or granularity number defined on a gen region inside
qT < 100 -- which is every published number in this study, including the 0.128 %
shape / 0.146 % absolute central closure and the 15.7x granularity reduction --
is therefore UNCHANGED as an identity, not as a measurement that happened to come
out the same. There is no headroom for a regression to hide in.

B's own overflow (gen qT > 1000) is exactly 0.0: on this file nothing at all is
generated above 1 TeV, which is the first piece of the upper-edge argument.

