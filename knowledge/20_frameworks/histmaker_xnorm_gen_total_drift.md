# The `prefsr` xnorm gen total drifted +0.240% between WRemnants revisions

Measured 2026-08-27 (`studies/scetlib-ad-param-model/260827-authoritative-validation`,
`n748/04_attribute_offset.log`, `n748/05_fillroute.log`).

## What moved

Two full-statistics `mz_dilepton --unfolding` runs over the same
`Zmumu_2016PostVFP` events, one at WRemnants `71076fe` (2026-07-23), one at
`ffbe5b4` (2026-08-26). Comparing the **same hist names on the same 20 x 10 POI
gen grid**, with no coarsening anywhere:

| hist, ratio Aug-run / Jul-run | |
|---|---|
| `nominal` (reco) | 7.498672 |
| `nominal_prefsr_yieldsUnfolding`, acceptance = True | 7.498572 |
| `nominal_prefsr_yieldsUnfolding`, acceptance = False | 7.499562 |
| **`prefsr`** (gen total, UL of `csAngularMoments`) | **7.480608** |

The bulk factor 7.4987 is just `--noScaleToData` on one side. What matters is
that every **reco-side** hist carries it to within **1.3e-4** while **`prefsr`
alone is 0.240% off**. In the gen plane that 0.240% is flat: +/-2.9e-4 over the
20 qT rows, +/-1.8e-4 over the 10 |Y| columns.

## What was excluded

* **Not `scale_to_data`.** `wremnants/production/histmaker_tools.py` computes one
  `scale = lumi*1000*xsec*gen_filter_eff/weight_sum` and applies it to **every**
  histogram in `result["output"]`, no exceptions -- it can only be uniform.
  (Side fact worth knowing: `lumi` is summed over the **data** datasets, so a run
  with `--filterProcs <one MC process>` and *without* `--noScaleToData` scales
  with `lumi = 1`.)
* **Not flow assignment / binning.** Retested with no `hist.project()` anywhere
  and explicit per-axis in-range slices, because the original attribution used
  `project()` (which folds the *summed* axes' flow back in) together with
  `values(flow=False)` (which drops the *kept* axes' flow), and a flow difference
  would have been invisible to it:

  | | flow excluded | flow included |
  |---|---|---|
  | `prefsr` Aug/Jul | 7.48060754 | 7.48069255 |
  | R_raw Aug/Jul | 7.49857176 | 7.49867080 |
  | **ratio of ratios** | **1.00240144** | **1.00240329** |

  Unchanged at 2e-6. Both runs also have identical axis traits (`ptVGen`
  overflow True, `absYVGen` overflow True, no underflow -- both ran
  `--poiAsNoi`, and `flow_y = self.poi_as_noi`,
  `wremnants/production/unfolding_tools.py:397`), flow fractions agreeing to
  1e-5 (+13.187% of in-range, all `ptVGen` overflow), and **zero** `absYVGen`
  overflow content, i.e. |Y| > 2.5 dropped at fill by `V_absY < edges[-1]` in
  both.
* **Not the SUM-vs-UL fill route.** Within one run the two routes are the *same
  object*: `nominal_prefsr_yieldsResponse` (`nominal_weight`) coarsened equals
  `nominal_prefsr_yieldsUnfolding` (the `nominal_weight_helicity` partition,
  summed) at **1.00000000**, and `prefsr_response` equals `prefsr` UL at
  **1.00000000**; a reco projection through both agrees to 1.5e-14; and their
  flow-INCLUSIVE totals are both 171892943.9 exactly.

## Unattributable, and why that is final

`71076fe` is gone from the object DB -- `git cat-file -t` fails after a fresh
`git fetch origin`, `git reflog --all` has 0 hits, and the surviving branch holds
one commit in the 2026-07-20 -> 08-27 window. There is no history to bisect on
either side. The honest terminus is: **a flat +0.240% normalisation change in the
`prefsr` xnorm histogram between those two revisions, cause unattributed, flag
and fill-route positively excluded.**

## The rule

**Never compare gen totals -- or anything normalised by one -- across histmaker
outputs from different WRemnants revisions without re-checking the xnorm
normalisation first.** Cheap check: take the ratio of a reco-side hist and of
`prefsr` between the two runs; they must agree. If they do not, the difference
lands directly on `R = R_raw/N_gen` and therefore on every folded sigma_reco.

This bites the SCETlib response fold in particular, which divides `R_raw` by
exactly this gen total (`wremnants/postprocessing/scetlib_ad/response_matrix.py`,
`param_model.py`: `self.R = R_raw / N_gen`). A splice that takes `R_raw` from one
run and compares against templates from another inherits the offset whole.

Two further cautions from the same measurement:

* the offset is flat only when **reduced over gen rows**. Per reco bin the
  run-to-run difference is **2.2e-03 yield-weighted, max 2.5e-02**, which no
  normalisation matching removes -- so it does not cancel in a shape closure
  either.
* 0.240% is **larger than the reco closure such work is trying to measure**
  (0.128% on the 210-bin grid), so this is not a rounding concern.

## Last updated

2026-08-27
