# Staged logbook entry — response matrix on the CorrZ gen grid (2026-08-26)

Paste into `studies/scetlib-ad-param-model/LOGBOOK.md` (do not paste over another
session's edits). Decisions: `DECISIONS_genbinning.md`.
Plots, tables and per-figure provenance:
`~/public_html/alphaS/260826_scetlib_ad_response_genbinning/`.

### 2026-08-26: the response matrix now has its own, finer gen binning — the correction's own grid

**Luca's instruction, superseding the previous night's recommendation.** The
grain-vs-grid round measured the candidate grids and recommended "grid D"
(52 x 11 = 583 bins: reco ptll edges below 44, the correction's edges above,
plus one |Y| edge) as the α_s-optimal compromise. The instruction is instead to
use the **CorrZ theory-correction file's own (qT, |Y|, Q) binning**, and to do it
**without disturbing the unfolding binning**, which is a separate analysis path.
Both are now implemented, measured and proved.

---

#### What was built — one opt-in flag, two extra histograms, nothing else moved

`mz_dilepton --responseGenBinning theoryCorr` (default `none`) builds a **second**
set of gen axes from the first `--theoryCorr` file and writes two additional
histograms per unfolding level:

* `nominal_<level>_yieldsResponse` — reco x gen on the finer grid, with the
  `acceptance` flag, filled with `nominal_weight` (no helicity axis);
* `<level>_response` — the gen total `N_gen` on the same grid, from the same
  node and the same gen-level weight as the existing `<level>` xnorm hist.

`self.unfolding_axes` is never touched: `binning.get_unfolding_dilepton_axes`
grew one optional `edges_override=None` whose default path is the original code,
and the response axes reuse the unfolding acceptance flag and selections. The
consumption path is plumbed end to end: `load_R` takes the new names (and the
helicity axis is now optional), `setupRabbit --storeResponseMatrix
--responseMatrixGenBinning response` embeds it, and
`prepare_cache_for_card.py` already reads the gen axes out of the card's
auxiliary bundle, so a 781-bin runcard follows with no further code change.

#### The target grid, read from the file rather than assumed

`Q` **one bin [60, 120]**; `absY` 17 bins to 5.0; `qT` 70 bins to 100 GeV. Two of
those three need no work and one is the whole point:

* **Q is already exact.** The gen acceptance *is* `60 < prefsrV_mass < 120`, the
  correction's single Q cell. There is no Q granularity to resolve — so "matching
  the (qT, |Y|, Q) binning" means, for Q, matching a single bin we already match.
* **|Y| is truncated at the acceptance edge 2.5**, giving exactly the
  correction's 11 bins there (the shipped 10 plus the edge at 2.0). Above 2.5 the
  `acceptance = True` yield is measured to be **0.000e+00**.
* **qT takes the full range to 100**, which is the real change: the shipped axis
  stops at 44 with an overflow, so 11.65 % of `N_gen` sits in one column.

Every shipped gen edge, and every reco `ptll` edge, is an edge of the
correction's grid ("ALL NEST"), so the new grid is a strict refinement, coarsening
back to the shipped grid is an exact sum, and `GenFold`'s tiling requirement is
satisfiable.

#### Proof that the unfolding path is untouched (the hard requirement)

Same command, one input file, `-j 1` so that the atomic-fill summation order
cannot differ; arm B = arm A + the flag:

| | |
|---|---|
| histograms identical **bit for bit** | **464** |
| differing numerically / different axes | 0 / 0 |
| only in B (the two new outputs) | 2 |
| **only in A (lost)** | **0** |

and, in the same file, the internal identity that only exists once both grids are
present: the response histogram coarsened onto the unfolding grid equals the
unfolding histogram summed over the `helicitySig` partition to **2.8e-14**
(3.8e-16 of the largest bin) at `acceptance=True`, and 8.9e-16 at
`acceptance=False`. Same events, same weights, two binnings — an identity, so the
"no helicity axis" choice costs nothing. (`response_binning_ab.py`.)

#### Cost of the run

Measured: **32 min 17 s** wall, **21.7 GB** peak RSS, `-j 160`, full Zmumu
statistics (289.4 M events, 2779 files), event loop 28.8 min, graph build
2.8 min, output 90.4 MB. Stripped configuration -- Zmumu only, 2D reco
(`yll ptll`), two theory corrections, one PDF set, `--unfoldingLevels prefsr` --
but with `--unfoldingAxes ptVGen absYVGen helicitySig`, i.e. the **production**
unfolding path, untouched, so the run also exercises the coexistence.

The *incremental* cost of the flag is not resolvable from a full run against a
different night's node load; the controlled number is the `-j 1` A/B on one file:
4:42 -> 4:48 wall (**+1.9 %**), peak RSS +0.14 %, output +340 kB. A production
rerun (all processes, 5 `--theoryCorr`, 3 PDF sets, `--csVarsHist`, both
unfolding levels) is the 260723-style job: budget 2-3 h, and there the response
hist is 25600 x 852 x 2 = 43.6 M bins = 0.70 GB per level -- affordable because
narf fills ONE shared atomic histogram under IMT, not one per slot.

#### What it buys — granularity is now structurally zero, not merely small

Yield-weighted mean |folded / per-event − 1| over the fit's 780 reco bins, median
(worst) over the 39 theory directions. Measured on the full-statistics run; no
model and no cache enter, so nothing here can be moved by a SCETlib rebuild or by
the qT [0,1] cutoff convention.

| | shipped 21x10 | CorrZ grid 71x11 | factor |
|---|---|---|---|
| gen bins | 210 | 781 | 3.7x |
| GRAIN yield-weighted, median | 5.357e-05 | **3.410e-06** | 15.7x |
| GRAIN yield-weighted, worst | 3.886e-04 (`lambda2`->1) | 3.303e-04 (α_s leg) | -- |
| GRAIN per-bin max, median | 6.825e-04 | 3.064e-05 | 22x |
| GRAIN per-bin max, worst | 4.207e-03 | 1.355e-03 (α_s leg) | 3.1x |
| directions with GRAIN > CALC | 32/39 | **4/39** | |
| α_s equivalent, worst | 0.1516 σ | 0.0341 σ | 4.4x |
| α_s equivalent, worst w/o the α_s legs | 0.1516 σ | **0.0017 σ** | 89x |
| α_s equivalent, quadrature | 0.2698 σ | 0.0456 σ | 5.9x |

The four directions where GRAIN still exceeds CALC are the two identically-zero
`b_qqDS` directions (0/0 at machine precision) and the two α_s legs. **For every
direction whose applied weight is a pure bin lookup, GRAIN is now below the
calculation error.** Where the gain sits, in reco ptll: 1-12 GeV 3.1x, 12-20 GeV
5.7x, 20-44 GeV 20.4x, and 0-1 GeV 3.1x (the one bin the correction's grid still
splits while reco does not).

Composing that with the CALC measured on the shipped cache -- legitimate only
because CALC is measured **flat** against the gen grid -- and with the qT [0,1]
convention aligned:

| | shipped (measured) | new grid (composed) |
|---|---|---|
| TOTAL max\|dev\|, median | 7.770e-04 | 2.25e-04 |
| TOTAL max\|dev\|, worst | 4.572e-03 (transition 0.2_0.35_1.0) | 3.37e-03 (transition 0.3_0.6_0.9) |
| α_s equivalent, worst | 0.199 σ | 0.092 σ |
| α_s equivalent, quadrature | 0.317 σ | 0.185 σ |

Both new-grid α_s numbers equal the **CALC-alone** values (0.0912 σ and
0.1849 σ) to the digits shown: after this change the model's reco-level fidelity
is calculation-limited.

**The residual left at the target grid is not granularity, and it has a name.**
On the correction's own grid the fold is algebraically the per-event sum (the
applied weight is a bin lookup, so summing R_raw x rho over cells reproduces the
event-by-event reweighting exactly), i.e. granularity must vanish identically.
What is measured instead of zero is fully accounted for by a *fiducial* effect
with no free parameter:

    residual(direction) ~= f_mass x |rho(direction) - 1| ,  f_mass = 7.47e-04

**measured/predicted = 1.11 median, 1.01–1.14 (10th–90th percentile), log-log
correlation +0.9989** over the 35 non-α_s directions (measured median 3.410e-06
against 3.240e-06 predicted; both leak fractions measured in the same file).

`f_mass` is the fraction of the fit's reco yield whose **preFSR** mass is outside
60–120 while its reco m(ll) is inside: those events have no gen column in R
(`acceptance = False`) and the templates give them the correction's Q **flow**
bin, which the file holds at exactly **1.0**.

**RETRACTION.** The reco-2D round recorded this −7.5e-04 offset as
"reco-selected events with gen |Y| > 2.5". It is not: splitting the
`acceptance = False` yield in the fit's reco range gives **7.47e-04** with gen
|Y| in range (⇒ failed the gen mass window) against **2.95e-06** with gen
|Y| > 2.5. The |Y| story is wrong by a factor 250, and it was tested and killed
here: with that fraction the |Y| version of the prediction gives a median of
1.28e-08 against the measured 3.410e-06, i.e. 0.4 % of it.

**And the two α_s legs are confirmed as a construction difference, by an
independent route.** The same prediction under-shoots exactly those two by a
factor 23 (3.303e-04 and 3.214e-04 measured against 1.410e-05 predicted). They are
the only two directions whose applied weight is not a pure bin lookup
(`theory_corr_weight_map`, `alphas=True`: the binned ratio **times** an
event-level LHAPDF member ratio). Last night inferred that from the code plus
their failure to improve with resolution; here it is what is left over when a
quantitative prediction accounts for everything else.

#### What this means for the reco closure, and what still cannot be measured

The reco-2D round's three-term split was
`r_model/r_ref = CALC x WGT x GRAIN`. GRAIN was the limiting term in 30 of 39
directions once the qT [0,1] convention was aligned. It is now gone, and CALC —
the model's own gen-level calculation error against the correction file, measured
**flat** against the grid over a 10x coarsening range (median 7.3–7.8e-06) — is
the sole remaining limit. So:

* median direction, yield-weighted: GRAIN 5.36e-05 -> 3.4e-06, i.e. a factor 2
  **below** CALC's 7.8e-06 instead of 7x above it;
* the qT [0,1]-aligned worst direction stops being a grid problem: the limiting
  direction changes from `transition_points0.2_0.35_1.0` (GRAIN 4.20e-03) to
  `transition_points0.3_0.6_0.9`, whose 3.36e-03 is all CALC — the
  transition-point derivative problem, tracked separately;
* the shipped worst, `mufup` at 7.07e-03, is **unmoved**, because it is the
  qT [0,1] nonsingular-cutoff convention (CALC 7.47e-03) and no grid touches it.

**What today cannot deliver:** TOTAL and CALC on the new grid, because they need
sigma_gen evaluated on 781 gen bins and **no cache exists for that grid**. The
numbers above are GRAIN measured plus CALC carried over on the (measured) grounds
that it is grid-independent; that is a composition, and it is labelled as one.
Getting the real 39-direction TOTAL table — the "0.128 % / 7.07e-03 / 7.2e-04"
line rebuilt on the new grid — requires the cache build below.

#### The cost that has to be decided: the cache

781 gen bins against the shipped 210. From the shipped build log (17.6 h at 210
threads, `target_precision_rel = 1e-4`) and the cache's own rule records: the
outer-node stage is essentially linear in bins (~3.7x), while the fixed-order
stage is dominated by two qT cells (qT [0,1] holds 23.2 % and qT [44,100] 18.4 %
of all fixed-order nodes) which the new grid splits — **~3–4.5x, i.e. ~55–80 h at
210 threads, ~800 MB**. Bin-shard it in ascending bin order (a contiguous prefix
is a valid rectangle for `GenFold`; a hole is fatal), never split PDF members,
stage one base runcard and do not move it, and export
`TF_NUM_INTRAOP_THREADS=4 TF_NUM_INTEROP_THREADS=2` for the build processes.
**Do the 1-bin `--subset` timing test on the new runcard first**: it replaces the
3–4.5x bracket with a measurement in minutes.

#### Next

1. The `--subset` timing test, then the cache build. Only then does the reco
   closure (CALC, WGT, TOTAL) exist on this grid.
2. A production-configuration histmaker rerun (all processes, 5 `--theoryCorr`,
   3 PDF sets, `--csVarsHist`) with `--responseGenBinning theoryCorr`, so a real
   card can be built; budget 2–3 h. Or, for a validation card at zero histmaker
   cost, pass **both** the production output and this stripped one to
   `setupRabbit --responseMatrixGenBinning response`: only the latter carries the
   response histograms, so it supplies R while the production file supplies
   everything else.
3. Settle the α_s legs with the `theory_corr_weight_map` experiment (drop
   `_pdfas` from the map, rerun, re-measure): those two should then land on the
   same 1.11 ratio as the other 35.
4. Optional, and now the only granularity-free residual left: give the
   out-of-gen-mass-window events a gen column with the response frozen to 1
   (which is what the templates do). Worth 3.4e-06, i.e. half of CALC.
