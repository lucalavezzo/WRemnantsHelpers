---
title: Cost of a Q-split SCETlib AD cache for a Fisher forecast
slug: 260923-qsplit-cache-cost
study: lattice-cs-kernel
status: done
created: 2026-09-23
updated: 2026-09-23
owner: study-worker
---

# Cost of a Q-split SCETlib AD cache for a Fisher forecast

**Task:** How long would a SCETlib AD cache with mll in [60,120] split into 3-5 Q bins take to build, coarse enough to be affordable for a gen-level Fisher forecast of the lambda2_nu / Lambda2 degeneracy, and what is the cheapest binning that still answers it? (Estimate only; no production build.)

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-09-23)

> **A 5-way Q-split cache without PDF eigenvectors is cheap: grid A (5 Q × 5 |Y| × 15 qT = 375 bins) costs
> about 0.5 h wall on ≤384 cores, 1.5 h at the pessimistic bound. It is not 5× a Q-integrated build.**
> Splitting [60,120] into 5 windows costs 1.14× the single window for the same (|Y|, qT) cells. Almost all
> of the cost of the production cache (32.9 h) comes from the 29 PDF eigenvector pairs: the exact quadratic
> form is 79 % of it and the member loop ~12 %. Dropping them (`--pdf-eig 0`, which keeps the α_s PDF pair)
> is the lever, not the bin count. **Caveat first:** these costs come from 4-cell timing probes (qT < 2 GeV,
> where the cost lives) and a factorised model. The model underpredicts the production node-set + rules
> stages by 1.2–2.1×, so a ×2 safety factor is included. Without PDF eigenvectors the forecast's σ(α_s) is
> at fixed PDF and optimistic. The Q-integrated vs Q-split comparison stays like-for-like.

- **Next action:** Luca decides whether to build grid A (recipe under Result). Nothing was launched beyond
  the probes. Every probe has finished or been stopped; none are running.
- **Blocking on:** nothing.

---

## Log

### 2026-09-23 — timing probes (all finished; nothing of mine is running)
- Read `knowledge/20_frameworks/scetlib_ad_cache_build_parallelism.md`,
  `scetlib_cache_format_versions_and_pins.md`, the 260827 shard logs, and the 260921 (|Y| ≤ 3.5, 1050-bin)
  production log. **The 260827 per-row costs are not usable here:** in that build the node set (b66f8de)
  took 6–13 h per qT [0,0.5] row, while at 2da973d the whole 1050-bin node set took 23 min. So I measured
  on the current pin instead of extrapolating.
- Builder: `WRemnants/scripts/rabbit/scetlib_ad/build_scetlib_ad_cache.py` driving the pin
  `/work/submit/lavezzo/alphaS/scetlib-ad-2da973d/scetlib-cms` @ `ca15aec` through
  `scetlib-ad-param-model/260921-cache-2da973d/scripts/incontainer.sh`. Settings: `base_1e3.conf`,
  `--n-train 9`, `--pdf-eig 0` (α_s pair kept, **P = 24** differentiable parameters: α_s, 4 TMD λ, 4 CS λ,
  10 TNPs, 5 scale/transition). The same settings as production except for the PDF eigenvectors.
- **The wrapper takes exactly one Q bin (`--q-edges LO HI`).** So a Q split means one process per window.
  `backend_check.py` (`gen_axes_from_bins`) and the ParamModel's `GenFold` both assume a single Q window
  too. The forecast therefore has to drive `ScetlibADXsec.values_and_jacobian` directly, which it does
  anyway. No merge is needed: J rows from per-window caches just concatenate.
- Probes: the candidate grid Q∈{[60,76],[76,86],[86,96],[96,106],[106,120]} plus [60,120] as control,
  |Y| = [0,.5,1,1.5,2,2.5], qT = [0,1,2,3,4,5,6,8,10,12,14,17,20,25,30,40]. Each probe is a 4-cell
  `--subset`, 64 threads, wrapped in `/usr/bin/time -v`. Scripts: `scripts/probe*.sh`. Logs:
  `logs/probe_*.log`, `logs/time_*.txt`. Caches (1.5–2 MB/bin):
  `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/qsplit_probe_260923/`.

  | probe (4 cells) | Q | qT, \|Y\| | node / rules / α_s-pair FO (min wall) | core-min per cell |
  |---|---|---|---|---|
  | t_q60_76 | 60–76 | 0–2, 1.5–2.5 | 1.5 / 1.2 / 1.5 | 46.9 |
  | t_q76_86 | 76–86 | 0–2, 1.5–2.5 | 1.1 / 1.1 / 1.5 | 34.6 |
  | t_q86_96 | 86–96 | 0–2, 1.5–2.5 | 4.2 / 2.3 / 2.8 | **150.7** |
  | t_q96_106 | 96–106 | 0–2, 1.5–2.5 | 1.0 / 1.1 / 1.5 | 26.8 |
  | t_q106_120 | 106–120 | 0–2, 1.5–2.5 | 1.4 / 1.2 / 1.7 | 38.2 |
  | **sum of the 5 windows** | | | | **297.2** |
  | t_q60_120 (control) | 60–120 | 0–2, 1.5–2.5 | 6.9 / 3.9 / 4.6 | **260.9** |
  | t_q86_96_loqt_c | 86–96 | 0–2, 0–1 | 1.5 / 1.4 / 1.7 | 36.0 |
  | t_q86_96_midqt_c | 86–96 | 6–10, 0–1 | 0.0 / 0.2 / 0.0 | 3.4 |
  | t_q86_96_midqt_f | 86–96 | 6–10, 1.5–2.5 | 0.0 / 0.2 / 0.0 | 3.6 |
  | t_q86_96_hiqt | 86–96 | 25–40, 0–1 | 0.1 / 0.3 / 0.0 | 4.4 |

  Core-min is (user+sys)/60/4. It includes TBB spin, so it is if anything an over-count. Two probes ran at
  48 threads, the rest at 64.
- Closure: summed over the 5 windows, σ of the 4 control cells is 10.2275 pb against 10.2281 pb for the
  single [60,120] window (6e-5, inside the 1e-3 target). The peak window holds 84 % of it.
- **P-dependence of the node set and rules:** the same 4 cells with `--pdf-eig 29` (P = 53) took
  1.3 / 1.2 min against 1.5 / 1.2 at P = 24. Those two stages do not depend on the gradient dimension. The
  P = 53 probe then spent 15.8 min in the 58-member fixed-order loop (the α_s pair alone takes 1.5 min) and
  entered the exact quadratic form. That stage ran on **~2.4 cores** (145 cpu-s per 60 s) for 4 bins, so
  it could not be timed in minutes. **I stopped it (my own process, PID 2166038) after 26 min in that
  stage.** Its per-cell cost is therefore not measured. The with-PDF rows below are scaled from production.
- Feasibility of the forecast path: `scripts/probe_jacobian.py` loads each probe cache (0.3 s) and returns
  `values_and_jacobian` at the anchor (0.6 s), with non-zero `np_gnu_lambda2` and `np_eff_lambda2`
  columns (`probe_jacobian.out`). See Open questions for what the ratio of those two columns shows.
- Cost model: `scripts/cost_model.py` → `cost_model.out`. Cell cost = C_Q[window] × g(|Y|) × h(qT), with
  C_Q the measured low-qT forward cost per window, and g, h measured in the peak window only and
  log-interpolated. **Validation:** applied to the production grids, the model predicts 240 core-h (770
  bins) and 388 core-h (1050 bins) for node set + rules. The 1050-bin production spent 460–820 core-h on
  those stages (two runs of the same build: rules 54 vs 113 min). So the model is low by 1.2–2.1×, and I
  apply ×2 in the recommendation.

---

## Result

**Caveats, before the numbers.**
1. These are **estimates**. The measurements are 4-cell probes at the expensive corner (qT < 2 GeV,
   |Y| 1.5–2.5), plus three shape probes in the peak window. The rest is a factorised model, validated
   against production only to a factor of ~2.
2. **No PDF eigenvectors (`--pdf-eig 0`).** α_s still moves the PDF through the CT18ZNNLO_as_0116/0120 pair,
   but the 29 Hessian directions are absent. So σ(α_s) from this forecast is **fixed-PDF and optimistic**,
   and cannot be quoted against the fit. The Q-integrated vs Q-split *comparison* is like-for-like, and
   the question asked (σ(λ2_ν), ρ(λ2_ν, Λ2)) is mainly an NP question.
3. Unlike the 260827 cache, this uses the **2da973d/ca15aec** library and cache format (rules v13 / fo v14).
   Build and evaluate with that pin.
4. The Q-integrated arm comes from the **same** cache, by summing J rows over the Q windows (closure 6e-5
   above). The 3-window merges ([60,86],[86,96],[96,120]) are also row sums. One build serves every arm.

**Cost structure (answers Do-2):**
- **A Q bin does not cost the same as a Y bin.** Each window is an independent SCETlib bin, but its cost
  follows the Breit–Wigner. Off-peak windows cost 27–47 core-min per low-qT cell and the [86,96] peak costs
  151. The whole [60,120] window costs 261, so the 5-way split costs **1.14×** the integrated build of the
  same (|Y|, qT) cells, not 5×.
- **qT sets the cost.** In the peak window, a qT 0–2 cell costs 36 (central) to 151 (forward) core-min,
  against 3–4 for qT 6–40. So rebinning above ~5 GeV saves nothing, and every extra qT < 2 GeV or forward
  |Y| cell is what you pay for. At low qT, forward |Y| costs 4× central.
- **The gradient dimension barely matters for the node set and rules** (P 24 vs 53: same wall). What
  costs is the **PDF eigenvector members** and especially the **exact quadratic form**. In the 1050-bin
  production the form took 26.0 h of 32.9 h (79 %), and the eigenvector member loop 3.9 h. `--pdf-eig 0`
  removes both, because `prepare_cache.build_variations` builds the form only `if n_eig`. Dropping TNPs
  is not available: `gradient_param_names()` is compiled in. It would also only shrink the rules stage,
  which is P-insensitive anyway.

**Candidate binnings.** Wall = core-h / (250–330 effective of a 384-core cap), no PDF eigenvectors, one
process per Q window, threads split roughly in proportion to cost (peak window ~200, the others ~45 each).
"Model ×2" includes the safety factor; "upper" prices every cell as the most expensive (low-qT forward) cell.

| grid | Q × \|Y\| × qT | bins | model ×2 (core-h) | upper (core-h) | wall, model ×2 | wall, upper | disk |
|---|---|---|---|---|---|---|---|
| **A (recommended)** | [60,76,86,96,106,120] × [0,.5,1,1.5,2,2.5] × [0,1,2,3,4,5,6,8,10,12,14,17,20,25,30,40] | 375 | ~110 | 371 | **~0.4–0.5 h** | 1.1–1.5 h | ~0.7 GB |
| B (minimal) | same Q × [0,.8,1.6,2.5] × [0,2,4,6,8,10,13,16,20,30,40] | 150 | ~36 | 149 | ~0.15 h | 0.5–0.6 h | ~0.3 GB |
| C (rich) | same Q × [0,.4,…,2.0,2.5] (6) × 20 qT to 40 | 600 | ~136 | 594 | ~0.5–0.6 h | 1.8–2.4 h | ~1.1 GB |
| ref: Q-integrated A | [60,120] × A's \|Y\|, qT | 75 | ~96 | 326 | ~0.3–0.4 h | 1.0–1.3 h | ~0.15 GB |
| A **with** 29 PDF eig, no quadratic form | A | 375 | ~5× no-PDF | — | ~2–7 h | — | ~18 GB |
| A with 29 PDF eig + quadratic form | A | 375 | production-like | — | **~10–15 h** | — | ~18 GB |

- Wall-time floor: the peak window's qT < 2 GeV forward cells need ~10–15 min however many cores are
  given. Add a few minutes for startup and cache write. The beamfunc grids for CT18ZNNLO and both α_s sets
  are already in the pin tree, so no ~12 min regeneration.
- The with-PDF rows are **not measured**. "~5×" is the 60–76 probe's cost up to the end of the 58-member
  fixed-order loop (≈225 core-min per cell against 47). The quadratic-form row scales the production form
  (26 h for 1050 bins, which grows with nodes × μ_R, not with n_eig²) to 375 bins. Neither is needed for
  J at the anchor: the cross terms enter only second derivatives. But skipping the form while keeping
  eigenvectors needs a study-side rebind of `build_variations`. The wrapper supports that pattern, but I
  have not tested it.
- Forecast-side cost: load < 1 s and values+jacobian ~1 s per 4 bins here. With the fixed-order muF
  polynomial on (default), the first call on the full grid rebuilds it (6200 s at 770 bins in production).
  So call `set_fo_muf_poly(0)` and keep κ_F frozen, following the two conditions in
  `knowledge/20_frameworks/scetlib_cache_format_versions_and_pins.md`.

**Recommendation: grid A, no PDF eigenvectors, 5 processes.** It costs about an hour and answers both arms
and the 3-window merge from one build. Grid B saves only minutes, because the cost is in qT < 2 GeV, and B
keeps a single [0,2] qT bin, which blurs the Sudakov-peak shape where the NP sensitivity is. So B is not
worth it. Recipe, if Luca says go (per window W = lo hi, threads T_W):
```
build_scetlib_ad_cache.py --base-conf .../ntrain_gate/base_1e3.conf --q-edges <lo> <hi> \
  --y-edges 0 0.5 1.0 1.5 2.0 2.5 --qt-edges 0 1 2 3 4 5 6 8 10 12 14 17 20 25 30 40 \
  --pdf-eig 0 --n-train 9 --threads <T_W> -o <ceph>/qsplit_fisher_<date>/q<lo>_<hi>
```
Use `scripts/probe_timed.sh` without `--subset` as the template.

**Cheaper alternatives (Do-4).**
- *Direct AD without a cache* (`DrellYan.sigma_binned_batch(bins, p)` returns values and the full P-column
  gradient): this skips only the rules stage, about 1/4–1/3 of the no-PDF cost, and loses the α_s PDF pair,
  since the pair lives in the member build. It saves minutes on an hour, down an unvalidated path. **Not
  worth it.**
- *Restricting the gradient to {NP λ, α_s, a few TNPs}*: **not possible** without a SCETlib code change,
  and it would not help, since node set and rules are P-insensitive.
- *Coarser qT above 5 GeV or fewer Q windows*: essentially free either way. Fewer windows cost 1.14× →
  ~1.0×.

---

## Findings

1. A no-PDF-eigenvector SCETlib AD build (`--pdf-eig 0`, α_s pair kept) skips the exact quadratic form and
   the eigenvector member loop, which were 91 % of the 1050-bin production (32.9 h). Node set and rules
   cost the same at P = 24 and P = 53. — (evidence: `logs/probe_q60_76_eig29.log` vs
   `logs/probe_t_q60_76.log`; `/ceph/.../pdf62_y35_260921/merged_full/build.log`)
2. Splitting Q ∈ [60,120] into 5 windows costs 1.14× the single window for the same cells. The
   Z-peak window carries ~50 % of the split cost and 84 % of σ. — (evidence: `cost_model.out`,
   `logs/time_t_q*.txt`)
3. At the current pin, cost per cell falls ~10× (central |Y|) to ~40× (forward |Y|) from qT 0–2 to qT ≥ 6 GeV, and is 4× higher at forward
   |Y| for low qT. The old 260827 per-row costs (6–13 h per qT [0,0.5] row) no longer describe the
   current library. — (evidence: probe table above; `/ceph/.../pdf62_corrgrid_260827/shards/*/build.log`)
4. The quadratic-form stage runs on ~2.4 cores for a 4-bin subset, so it cannot be timed on a small
   probe. — (evidence: `logs/probe_q60_76_eig29.log`, measured cpu rate)
5. `build_scetlib_ad_cache.py`, `backend_check.py` and `GenFold` all assume one Q window. A Q-split cache
   is built as one process per window and consumed through `values_and_jacobian`. — (evidence:
   `build_scetlib_ad_cache.py --q-edges nargs=2`; `backend_check.gen_axes_from_bins`)

Findings 1–4 generalise and belong in `knowledge/20_frameworks/scetlib_ad_cache_build_parallelism.md`
(for the orchestrator or the knowledge-curator).

---

## Open questions

- **Teaser, not a forecast** (4 cells, no stat weights, no profiling): the ratio
  (∂σ/∂λ2_ν)/(∂σ/∂Λ2) goes from 1.98 → 2.07 → 2.11 → 2.15 → 2.20 across the five Q windows (qT 0–1,
  |Y| 1.5–2). The relative λ2_ν response stays at −0.520 in every window, while the Λ2 one falls from
  −0.263 to −0.236. So the Q lever arm is real but ~±5 % around the peak, where 84 % of the events are.
  The ratio also moves by a similar amount between qT 0–1 and 1–2 (2.11 vs 1.95) at fixed Q. The
  degeneracy is therefore already partly broken by the qT shape, and the Fisher forecast may find that a
  Q split adds only modestly. That is exactly what grid A would quantify. (`probe_jacobian.out`)
- The with-PDF costs are extrapolated, not measured, and so is the option of skipping the form by
  rebinding `build_variations`.
- Should the forecast float the PDF eigenvectors at all? If σ(α_s) matters, grid A without them is
  optimistic, and a with-PDF build is ~10–15 h, or ~2–7 h if the form is skipped.
