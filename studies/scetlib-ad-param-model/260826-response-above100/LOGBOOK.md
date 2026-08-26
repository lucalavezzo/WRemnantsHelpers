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


## The specification, and what decided it

Three new qT edges: **110, 130, 250**. Q and absY unchanged, read out of the
existing correction file rather than retyped. Literal edge lists in the webdir as
`gen_binning_spec.{txt,json,py}`.

The upper edge is the interesting one. The MiNNLO gen yield does not end at 250 --
it runs to ~1 TeV -- but the part of it that RECONSTRUCTS does. The reco
efficiency falls smoothly from 0.40 at low qT to 0.040 at 90-100, 0.019 at
100-110, 0.0011 at 120-130 and **exactly zero above 250**, and the cause is the
analysis' own muon pT window, `pt = [34, 26.0, 60.0]`: a Z at qT ~ 100 puts its
muons at the top of the 26-60 GeV window and by ~130 both routinely exceed it.
250 GeV is therefore the smallest edge at which the dropped phase space
contributes exactly zero reconstructed yield to every reco bin we have -- the
fit's 780 and also reco ptll [44, 100]. And going higher is not free: capping the
cache's qT axis at 1000 instead of 100 took the shared adaptive node stage from
22.5 min to > 82 min for 17.6 % more bins.

The corollary is the one to remember: the whole above-100 region is nearly
invisible to this analysis because of the muon pT window, not because 1.98 % of
N_gen is small. Widen that window and every number here grows.

## Physics read

The extension is a correctness move and should be described as one. It removes a
real ~7 % misapplication of the correction on 1.977 % of N_gen -- which matters
in its own right, and matters to the FIT only at the 2e-04 level in reco ptll
[44, 100], a bin the fit does not currently use. What it also does is remove a
class of latent inconsistency: with the assertion in place, a gen grid that
straddles a correction cell or reaches past the correction's support is now
refused at the two points where it would otherwise propagate silently (the
histmaker and the cache's runcard), which is exactly the failure mode that cost
this study a night on the qT [0, 1] cell.

## START HERE (for the next session on this thread)

* **State:** the binning specification is delivered and unambiguous
  (`~/public_html/alphaS/260826_scetlib_ad_response_above100/`, three files). The
  response extension is implemented, default-off, with the unfolding path
  re-verified byte-identical (464 / 2 / 0) and the below-100 response proven
  bitwise unchanged. The assertion tying the response grid to the correction's
  grid is in the histmaker AND in the cache builder, unit-tested.
* **Blocking:** Luca's correction production on the new grid. Four inputs need
  the new edges, and the MiNNLO `w_z_gen_dists` file is the one easy to miss
  (single bin [100, 13000] today).
* **Next, once it exists:** rerun `mz_dilepton --responseGenBinning theoryCorr`
  with NO extension flag (the grid comes from the file, and
  `check_gen_grid_vs_correction` then passes with the opt-in FALSE); build the
  781-bin cache; then run `above100_model.py` for the real above-100 validation,
  which is only meaningful at that point.
* **A histmaker run on the final grid** was launched as
  `/ceph/.../260826_Z_histmaker_above100/` (`--responseGenPtVExtend 110 130 250`)
  and should be checked for completion; it uses the identical code path the
  -j 1 A/B verified.


## Decisions

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


## D-A10 — WHY the upper edge is 250 GeV: the analysis' own muon pT window closes the phase space — SETTLED (measured)

**What.** The response gen qT axis stops at **250 GeV**. Not because the MiNNLO
yield stops there (it runs to ~1 TeV) but because **nothing above 250 GeV
reconstructs**.

**Evidence 1 -- the reco efficiency, Σ_b R_raw(b,g) / N_gen(g), over ALL reco bins
including the ptll overflow, full 297 M-event sample:**

| gen qT | efficiency | | gen qT | efficiency |
|---|---|---|---|---|
| 0-4      | 0.400 | | 100-110 | 0.0191 |
| 10-13    | 0.379 | | 110-120 | 0.0055 |
| 37-40    | 0.198 | | 120-130 | 0.0011 |
| 44-46    | 0.165 | | 130-140 | 0.00058 |
| 58-60    | 0.124 | | 170-200 | 4.4e-05 |
| 70-80    | 0.091 | | 200-250 | 1.8e-05 |
| 80-90    | 0.067 | | **250-300** | **0.0 exactly** |
| 90-100   | 0.040 | | 300-1000 | 0.0 exactly |

Smooth and monotonic, no cliff -- and the cause is in the histmaker's own
arguments: **`pt = [34, 26.0, 60.0]`, i.e. 26 < pT(mu) < 60 GeV.** A Z at
qT = 100 GeV puts its muons near the top of that window; by qT ~ 130 both muons
routinely exceed 60 and the event is thrown away; above 250 GeV not a single
event out of the ~1.7e5 (weighted) generated there survives.

**Evidence 2 -- what dropping at each edge costs, measured per reco region:**

| drop everything above | N_gen fraction | reco ptll < 44 (the fit) | reco ptll [44, 100] |
|---|---|---|---|
| 100 | 1.9772e-02 | 1.630e-07 | 2.809e-03 |
| 110 | 1.5168e-02 | 6.477e-08 | 6.605e-04 |
| 120 | 1.1789e-02 | 2.330e-08 | 2.724e-04 |
| 130 | 9.2711e-03 | **0** | 1.148e-04 |
| 150 | 5.9226e-03 | 0 | 2.041e-05 |
| 200 | 2.2294e-03 | 0 | 1.586e-06 |
| **250** | **9.7602e-04** | **0** | **0** |
| 1000 | 1.0492e-06 | 0 | 0 |

So 250 GeV is the smallest edge at which the dropped phase space contributes
EXACTLY ZERO reconstructed yield to every reco bin we have -- the fit's 780 and
also reco ptll [44, 100], which the fit does not use today. Pushing higher would
add gen bins whose R column is identically zero: cache cost and a correction to
produce, with no possible effect on any prediction.

**The corollary worth keeping.** The reason the whole above-100 region is nearly
invisible (D-A2) is not the gen spectrum -- 1.98 % of N_gen is not small -- it is
the muon pT window. If that window is ever widened, the reco efficiency above 100
rises and every number in D-A2 grows with it.

## D-A11 — THREE bins: [100, 110], [110, 130], [130, 250] — SETTLED

Measured per bin on the full sample (from a 12-bin diagnostic extension; `R_raw`
is additive so a sub-union is an exact sum, so these are measurements):

| gen qT bin | N_gen fraction | reco feed, fit (ptll<44) | reco feed, ptll [44,100] |
|---|---|---|---|
| [100, 110] | 4.6045e-03 | 9.824e-08 (60 % of the total) | 2.148e-03 (76 %) |
| [110, 130] | 5.8966e-03 | 6.477e-08 (40 %) | 5.457e-04 (19 %) |
| [130, 250] | 8.2951e-03 | **0** | 1.148e-04 (4 %) |
| dropped, > 250 | 9.7602e-04 | 0 | 0 |

**Why these boundaries.**

* **10 GeV for the first bin.** It carries 60 % of the fit-range feed and 76 % of
  the ptll [44, 100] feed, and its reco efficiency (0.0191) is 3.5x the next
  bin's, so this is the only place above 100 where resolution can matter. 10 GeV
  also CONTINUES the correction's own pattern -- its last three bins are 70-80,
  80-90, 90-100, all 10 GeV -- so the grid does not change character at the
  boundary.
* **20 GeV for the second.** It takes the rest of the resolvable feed (40 % of the
  fit's, 19 % of [44, 100]'s) while the yield has already fallen 4x.
* **One wide bin to 250.** [130, 250] feeds EXACTLY ZERO of the fit's reco bins
  and 1.1e-04 of reco ptll [44, 100], so its internal granularity cannot matter
  at any precision this analysis works to; splitting it would buy nothing and
  cost Luca three more theory bins.
* **Statistics per bin** are ample for the MiNNLO denominator and the DYTurbo
  fixed order: 7.91e5, 1.01e6 and 1.43e6 in weight (0.46 %, 0.59 %, 0.83 % of
  N_gen).

Resulting grid: qT **73 bins** (70 + 3), |Y| 11 bins for the response ->
**803 gen bins** (from 770). Literal edge lists in the webdir
(`gen_binning_spec.{json,txt,py}`).

## D-A12 — full-statistics controls on the extended grid — SETTLED (measured)

On the 12-bin diagnostic run (`260826_Z_histmaker_ext100`, 2779 files, 52:38
wall, 21.1 GB peak RSS, 90.5 MB output, `-j 128`):

```
gen bins with N_gen > 0                      902 / 902   (exact tiling, no holes)
response coarsened onto the unfolding grid vs the unfolding hist
    in-range max|diff| 1.37e-09   =  1.54e-14 of the largest bin (8.87e+04)
    >44 overflow column max|diff| 2.11e-09
vs the UNEXTENDED full run (260826_Z_histmaker_respgrid), gen qT < 100
    R_raw max|diff| 8.08e-10  (~9e-15 relative)
    N_gen max|diff| 7.07e-08
    its single overflow column vs the SUM of the new columns
                              9.10e-13 of 5.4568e+03  =  1.7e-16 relative
```

Not bitwise here, and correctly so: both are `-j 128` runs filling one shared
atomic histogram, so summation order is not reproducible and float rounding is
the right expectation. The bitwise statement is the `-j 1` one in D-A9.


## D-A13 — a SECOND, independent reason to stop at 250: the cache's node stage — SETTLED (measured)

The SCETlib cache shares ONE adaptive outer node set across all gen bins, so the
hardest bin sets the node count for everything. Two builds off the SAME base
runcard, `--no-pdf`, `--threads 200`, differing only in how far the qT axis runs:

| grid | gen bins | `outer node set + matched cross sections` |
|---|---|---|
| qT [1, 100] x 11 abs(Y)  (`main_qt1_100`) | 748 | **22.5 min** (D-C10) |
| qT [1, 1000] x 11 abs(Y) (`ext_qt1_1000`) | 880 | **> 82 min and still running when killed** |

+17.6 % more bins, > 3.6x the node-stage cost. The b_T integrand oscillates on a
scale 1/qT, so a bin at qT ~ 1 TeV drags the shared node ladder up for the whole
grid. Since every gen bin above 250 has an identically zero R column (D-A10),
that cost buys nothing at all -- so the upper edge is set by the reco reach, and
the build confirms there is a price for going past it rather than merely no gain.

The build was killed rather than finished: it was in an uncheckpointed node stage,
nothing downstream needs it, and the number above is already the useful datum.
The deliverable cache is on the FINAL grid, qT [1, 250] (781 bins).


## D-A14 — the edges reach the SCETlib runcard verbatim; no cache-side code change — SETTLED

`prepare_cache_for_card.write_runcard` writes the gen axes straight into
`Grid_qT` / `Grid_Y`. Verified on a built runcard for the FINAL grid:

```
[Grid_qT]
values = [1, 1.5, ..., 80, 90, 100, 110, 130, 250]
```

`gen_axes_from_card` reads the same edges out of the card's response auxiliary and
is where the new assertion sits, so the card -> runcard step cannot inherit a
mismatch. (The card-side end of the chain was not re-run here: `setupRabbit`
on this stripped histmaker fails on an unrelated pre-existing issue -- it wants a
`pdfvars` correction hist the run does not carry -- and chasing it was out of
scope.)

## D-A15 — what is deliberately NOT measured — SETTLED (scope)

No number is quoted for the model above 100. No correction exists there, so any
such number is model-versus-nothing: a preview of what Luca's production will
produce, not a validation. `above100_model.py` is committed and ready to produce
it (implied correction anchored at the last corrected qT row, with the
credibility of the extrapolation measured by anchoring at qT 44 and predicting
44 -> 100 where truth exists) the moment the corrections land.

Neither cache was kept: both were cost probes (D-A13) and were killed once the
specification was in hand. A cache on the final 781-bin grid is a 30-60 min
`--no-pdf` job whenever wanted.
