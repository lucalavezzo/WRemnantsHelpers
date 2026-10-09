---
title: Stiff-wall refits
slug: 260930-stiff-wall-refits
study: walled-multistart-census
status: done        # active | done | paused | abandoned
created: 2026-09-30
updated: 2026-10-01
owner: study-worker
---

# Stiff-wall refits

**Task:** If the known walled minima (NOM = LATL4ZY35WALLWARM, XW = Y35ZWALLWARM, XL4Z = Y35ZWALLL4ZR) are re-minimised warm with wall margin 0 and a very stiff wall (τ = 8), where do they go, and how hard is it for trust-krylov? (Decides stiff wall vs porting trust-constr for the census.)

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-10-01)

> **The stiff wall is enough. All three fits are DONE (exit 0), converged under trust-krylov (EDM ≤ 3e-14), and landed
> exactly on true damping boundaries (overshoot ≤ 1e-6). `alphaS` moved ≤ 0.04σ, σ ≤ 0.1 %. Do not port trust-constr.**
> NOM → L2(|Y|=2.5) = 0 (Δ`alphaS` +0.012σ). XW → λ2_ν = 0 and B(2.5) = 0 (−0.038σ; B(0) slack only 4.9e-4 in λ4 units,
> next to the TMD cliff onset). XL4Z → λ2_ν = 0 (−0.024σ). Difficulty grows with the number of faces: 41/43 iterations for
> one face, 128 iterations (2.2 h) for two, as a staircase of radius-collapse plateaus. Blinded: differences only. These
> are **main fit + Hessian only** fitresults (no saturated test, impacts, or hists).

| fit | postfix | PID | started | finished | live log | gate log | reference |
|---|---|---|---|---|---|---|---|
| NOM | `NOMSTIFF` | 2324155 | 2026-09-30 14:32:54 | 15:57, exit 0 | [logs/NOMSTIFF.log](logs/NOMSTIFF.log) | [logs/NOMSTIFF.gate](logs/NOMSTIFF.gate) | LATL4ZY35WALLWARM |
| XW | `XWSTIFF` | 2327160 | 2026-09-30 14:33:16 | 17:03, exit 0 | [logs/XWSTIFF.log](logs/XWSTIFF.log) | [logs/XWSTIFF.gate](logs/XWSTIFF.gate) | Y35ZWALLWARM |
| XL4Z | `XL4ZSTIFF` | 2769323 | 2026-09-30 15:58:20 | 17:55, exit 0 | [logs/XL4ZSTIFF.log](logs/XL4ZSTIFF.log) | [logs/XL4ZSTIFF.gate](logs/XL4ZSTIFF.gate) | Y35ZWALLL4ZR |

Fitresults: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260930_stiff_wall_fits/fitresults_{NOM,XW,XL4Z}STIFF.hdf5`.
Analysis: `scripts/analyze.py` → `analysis.out`, `analysis.json`; plots: `scripts/plot_loss_history.py`.

- **Next action:** none; task closed. For the orchestrator: add the runs_ad.yaml rows (below), then T4 with this wall.
- **Blocking on:** nothing.

**Rows for `studies/alphas-scan-discontinuity/runs_ad.yaml`** (not added by me), in the "card A, new |Y|<=3.5 cache" block.
Each needs a comment: margin 0, τ 8, warm from the named row, no saturated test or impacts.
```
- name: "A+lattice new cache, wall m=0 tau=8 (warm)"
  dir: /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5
  seed: "A+lattice new cache, wall (warm)"
- name: "A new cache, wall m=0 tau=8 (warm)"
  dir: /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5
  seed: "A new cache, wall (warm)"
- name: "A new cache, wall m=0 tau=8, $\\lambda_4^\\nu$=0 (warm)"
  dir: /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260930_stiff_wall_fits/fitresults_XL4ZSTIFF.hdf5
  seed: "A new cache, wall, $\\lambda_4^\\nu$=0 (warm, resumed)"
```
None of these rows has a saturated test, so the table's GoF columns will be empty for them.
`runs_new.yaml` (np-wall-local-minima) is for the old MSHT20/btgrid family, so these rows do not go there.

---

## Log

<!-- Newest first. What was tried, what happened, why — with an evidence path. -->

### 2026-10-01
- XWSTIFF (17:03) and XL4ZSTIFF (17:55) finished exit 0 while this session was restarting. Ran `scripts/analyze.py`
  (→ `analysis.out`, `analysis.json`), `scripts/cross_xl4z_xw.py` (→ `cross_xl4z_xw.out`) and
  `scripts/plot_loss_history.py`. Cross-checked against the orchestrator's numbers (NOM +0.012σ, σ ratio 0.999; XW
  −0.038σ, faces λ2_ν and B(2.5); XL4Z −0.024σ; XL4Z−XW ΔNLL +0.955, +0.259σ): all agree. The orchestrator's
  "B(0) = 4.9e-4" is λ4 + L2³/(3λ_inf²), i.e. the wall's coefficient 1.46e-3 divided by 3.
- Fixed `plot_loss_history.py`: importing wums (inside save_plot) sets a global mplhep style, so every figure after the
  first came out with oversized labels. It now does `rcdefaults()` per figure, and all three plots were regenerated.

### 2026-09-30 (16:00) NOM done
- NOMSTIFF finished (exit 0, 5008 s total; minimize 4152 s, 41 iterations; Hessian 562 s). NLL 376.6146329237,
  EDM 3.0e-14. Moved onto the L2(|Y|=2.5) = 0 face (coeff −9.2e-7); Δ`alphaS` = +0.012 σ_ref. Details in Result
  (evidence: `analysis_NOM.out`, `analysis_NOM.json`, `loss_history_NOM.png`).
- XL4ZSTIFF auto-launched by `queue_third.sh` at 15:58:20 when NOM exited (PID 2769323).

### 2026-09-30
- Commands built by `scripts/build_cmds.py` from each reference fitresult's OWN `meta_info["command"]` (not from the
  runner scripts), written to `cmds/<postfix>.cmd`. Changed tokens only: `-o`, `--postfix`, `--snapshotFile`,
  `--regularizationStrength 5 → 8`, `-r W M` → `-r W M margin=0` (after the mapping class, per T1), `--externalPostfit`
  → the reference fitresult itself (full stored vector). Card, cache, `threads=128`, `fit_params` (freeze list),
  `prior_sigmas`, `--earlyStopping` (100 for NOM, none for XW/XL4Z, as in the references) unchanged.
- **Postfit products dropped (Luca via orchestrator, 14:32):** `-m Project ch0 ptll --computeSaturatedProjectionTests
  --doImpacts --globalImpacts --globalImpactsDisableJVP --saveHists --computeHistErrors` removed. In the references
  the saturated projection test alone took 13–20 h of the 14–22 h total. So these fitresults carry only the main fit +
  postfit Hessian (EDM, σ, cov): no saturated GoF, no impacts, no postfit hists.
- A first NOMSTIFF launch at 14:31 with the full flag set was killed by me during its cache load (nothing written) when
  that instruction arrived; its log is kept as `logs/NOMSTIFF_aborted_fullflags.log`. I removed the stale
  `/tmp/alphas_slot2.need` its killed gate left behind (it was mine).
- Launch: `scripts/launch.sh <postfix>` → `scripts/mem_gate.sh 330` (copy of the study-local v3 gate) →
  `scripts/run_fit.sh` → `agent_setup.sh --scetlib current -- python3 <cmd>`. Versions: WRemnants df3c30f7 +
  T1's uncommitted `np_damping_wall.py` diff (md5 of the diff 060a9a36…, recorded in each log's `[run]` line), rabbit
  2a59246, scetlib 2dd978a (same rabbit/scetlib as the references; NOM's reference ran on WRemnants ae9c6865, which
  differs from df3c30f7 only outside `scetlib_ad/`, rabbit and wums checkouts identical).
- Node at launch: 1158 GB available, the other ~250 GB fit (an MSHT20 lattice fit, not ours to touch) running;
  our threads 8659 after both launches.

---

## Result

**Comparability caveats first.**
- Real-data fits, `alphaS` BLINDED. Only θ differences (new − ref) of the same parameter in the same data family
  (integer reco counts, same card) are shown, in units of the reference σ. No absolute `alphaS` anywhere.
- The new and reference NLLs are **different objectives**: new = unwalled loss + e¹⁶·relu²(0 − coeff) (τ = 8, margin 0);
  ref = unwalled loss + e¹⁰·relu²(5e-3 − coeff) (τ = 5, margin 5e-3). The wall is a pure function of the NP λ's, so the
  unwalled "base" loss is recovered exactly from each stored NLL (T1: stored `nllvalreduced` = base + e^{2τ}·pen, diff
  0.0; here the NOM base reproduces T1's 376.69103432608273 to all digits). ΔNLL is quoted three ways:
  gain on the new objective (vs the ref vector evaluated under the new wall), Δbase (the data+constraint movement), and
  the new vector under the REF objective.
- These fitresults are **main fit + postfit Hessian only** (no saturated projection test, impacts, or postfit hists; see Log).
- Card per fit as in its reference: NOM = card A + lattice (λ4_ν held at 0, `prior_sigmas=lambda2_nu=nan`); XW = card A,
  λ4_ν free; XL4Z = card A, λ4_ν held at 0. All on `pdf62_y35_260921/merged_full_bin0xzero`.
- The references were not all started from their own configuration (NOM ref warm from XW's minimum; XW ref warm
  from an older-cache fit; XL4Z ref is a resume after SIGTERM), so their minimiser traces are shown for scale only.

### NOM (card A + lattice): NOMSTIFF vs LATL4ZY35WALLWARM

| quantity | value |
|---|---|
| NLL new (τ 8, m 0) | 376.6146329237 |
| NLL ref (τ 5, m 5e-3) | 376.6942441689 |
| ref vector under the new objective | 376.6910343261 (margin-0 wall is slack there: pen = 0) |
| **gain on the new objective** | **−0.0764** (2Δ = −0.153) |
| Δbase (unwalled data + constraints) | −0.0764 |
| new vector under the ref objective | 377.1655 (+0.471: it sits inside the 5e-3 cushion) |
| wall term at the new minimum, e¹⁶·pen₀ | 7.4e-6 |
| EDM new / ref | 3.0e-14 / 4.5e-15 |
| **Δ`alphaS` / σ_ref** | **+0.012** |
| σ_new / σ_ref (`alphaS`) | 0.9991 |
| largest |Δθ/σ_ref| of any parameter | λ2 −0.080 (then λ2_ν +0.039, δλ2 −0.028, b_qg −0.024) |

| λ (physical) | ref | new | Δ/σ_ref |
|---|---|---|---|
| λ2 | 0.029006 | 0.025581 | −0.080 |
| λ4 | 0.087324 | 0.087583 | +0.010 |
| δλ2 | −0.003902 | −0.004093 | −0.028 |
| λ2_ν | 0.063385 | 0.064270 | +0.039 |
| λ_inf, λ_inf_ν, λ4_ν | held 1, 2, 0 | held | — |

| armed condition (5 of 8; log: "armed on 5 of 8 condition(s) at margin=0") | coeff ref | coeff new | active @ m=0 (new) |
|---|---|---|---|
| λ2_ν ≥ 0 (CS small-b) | 0.06339 | 0.06427 | no |
| L2(|Y|=0) = λ2 ≥ 0 (TMD small-b) | 0.02901 | 0.02558 | no |
| TMD large-b at |Y|=0 | 0.2620 | 0.2628 | no |
| **L2(|Y|=2.5) = λ2 + 6.25 δλ2 ≥ 0 (TMD small-b)** | **0.004618** | **−9.2e-7** | **yes (the only face)** |
| TMD large-b at |Y|=2.5 | 0.2620 | 0.2627 | no |

**Physics read (NOM).** With the cushion gone, the nominal minimum slides onto the exact TMD small-b boundary at the edge
of the gen acceptance, L2(|Y| = 2.5) = 0: the data would like the b² term of the TMD NP function at |Y| = 2.5 to go
slightly negative (anti-damping), and the wall stops it exactly at zero. The τ = 8 overshoot is 9e-7 in the coefficient
and 7e-6 in the NLL, so the stiff relu² is a hard constraint for every practical purpose. The whole move is worth
ΔNLL = −0.076, and it is predicted by first order from the reference alone: the wall force at the reference,
g = 2e^{10}(5e-3 − 0.004618) = 16.8 per unit coefficient, times the distance to the face, 0.004618, gives 0.078. At the
new point the wall force is 2e¹⁶·9.2e-7 = 16.3, the same data pull. `alphaS` moves by +0.012 σ and its σ by −0.1 %:
**for the nominal configuration the 5e-3 margin is irrelevant to `alphaS`.** No other face comes near activation
(next-closest slack 0.026).

![NOM loss history](loss_history_NOM.png)

Caveat for the figure: each curve is relative to its own final loss, and the two are different objectives. The reference
started 150 NLL units away (warm from the no-lattice minimum), NOMSTIFF 0.076 away.

**Minimiser (NOM).** 41 iterations (scipy `nit`; the coordinator's "40" is the last iteration index), 13 rejected steps (longest run 4), no loss increase, 4152 s in `minimize()` (Hessian
562 s), scipy exit "A bad approximation caused failure to predict improvement" (the normal exit for these fits; the
reference ended the same way). Shape: the first Newton step crosses the face (the model has no wall curvature at a slack
point), so the radius is shrunk 4× four times in a row (these rejections are free, 0.01 s, since the same interior step
is re-proposed); then ~25 iterations of a reject/accept sawtooth gaining 1e-5 to 1e-3 each, while the trust region
learns the kink; once on the face the model is exact (relu² is quadratic on the violated side) and the last ~6
iterations converge quadratically to EDM 3e-14. So: slower per unit of loss than a smooth fit, but it converges, with no
restarts needed and no stall.

### XW (card A, λ4_ν free): XWSTIFF vs Y35ZWALLWARM

| quantity | value |
|---|---|
| NLL new (τ 8, m 0) | 371.3283651896 |
| NLL ref (τ 5, m 5e-3) | 371.4429641661 |
| ref vector under the new objective | 371.4379809686 (pen₀ = 0) |
| **gain on the new objective** | **−0.1096** (2Δ = −0.219) |
| Δbase (unwalled) | −0.1096 |
| new vector under the ref objective | 372.7058 (+1.263) |
| wall term at the new minimum, e¹⁶·pen₀ | 1.2e-5 |
| EDM new / ref | 7.4e-18 / 2.8e-17 |
| **Δ`alphaS` / σ_ref** | **−0.038** |
| σ_new / σ_ref (`alphaS`) | 0.9990 |
| largest |Δθ/σ_ref| | λ4 −1.04, λ2_ν −0.95, λ2 +0.17, λ4_ν +0.08; every non-NP parameter ≤ 0.013 |

| λ (physical) | ref | new | Δ/σ_ref |
|---|---|---|---|
| λ2 | 0.108657 | 0.118826 | +0.168 |
| λ4 | 0.001598 | −0.000072 | −1.044 |
| δλ2 | −0.009417 | −0.009410 | +0.001 |
| λ2_ν | 0.004531 | −0.0000011 | −0.953 |
| λ4_ν | 0.043563 | 0.044408 | +0.076 |
| λ_inf, λ_inf_ν | held 1, 2 | held | — |

| armed condition (6 of 8) | coeff ref | coeff new | active @ m=0 (new) |
|---|---|---|---|
| λ4_ν ≥ 0 (CS large-b) | 0.04356 | 0.04441 | no |
| **λ2_ν ≥ 0 (CS small-b)** | **0.004531** | **−1.1e-6** | **yes** |
| L2(|Y|=0) ≥ 0 (TMD small-b) | 0.1087 | 0.1188 | no |
| B(0) = 3λ_inf²λ4 + L2(0)³ ≥ 0 (TMD large-b, |Y|=0) | 0.006078 | **0.001461** | no, but close (see below) |
| L2(|Y|=2.5) ≥ 0 (TMD small-b) | 0.0498 | 0.0600 | no |
| **B(2.5) = 3λ_inf²λ4 + L2(2.5)³ ≥ 0 (TMD large-b, |Y|=2.5)** | **0.004919** | **−2.0e-7** | **yes** |

**Physics read (XW).** This is the W route, and margin 0 lets it go further down the same road. Both faces that held
it at the 5e-3 cushion are now exactly on their true boundaries: the CS small-b turn-on (λ2_ν = 0, so γ_ν^NP starts at
b⁴ through λ4_ν = 0.044) and the TMD large-b leading coefficient at the acceptance edge, B(2.5) = 0. λ4 goes to
−7e-5, slightly negative, which the large-b condition allows because L2³ pays for it. λ2 rises by 0.01 to keep B(2.5)
at zero. That is a 1σ move in λ4 and λ2_ν, and it buys ΔNLL = −0.110. `alphaS` moves by only −0.038σ, with σ
unchanged to 0.1 %.
**Flag (requested by the orchestrator):** B(0) is now 1.46e-3 in the wall's normalisation, i.e. λ4 + L2(0)³/(3λ_inf²)
= 4.9e-4 (the orchestrator's number; the two agree, the factor is 3λ_inf² = 3). That is where the TMD large-b "cliff"
starts (λ4 < 0 with too small an L2 turns the large-b_T damping into growth). It is not active, but it is the
next face along this route, and a census start that lowers λ2 would hit it.
Also note λ2_ν = −1.1e-6: the AD cache is exact only for λ2_ν ≥ 0
(`knowledge/20_frameworks/scetlib_ad_cache_validity.md` §1). The τ = 8 overshoot is negligible there, but at margin 0 every
fit on this face sits exactly on the cache's validity edge, where the 5e-3 cushion used to keep it 0.005 inside.

![XW loss history](loss_history_XW.png)

Caveat for the figure: each curve is relative to its own final loss; different objectives. The reference was warm
from an older-cache fit and started only 0.015 above its minimum, so its 10 iterations are not a like-for-like difficulty
benchmark.

**Minimiser (XW): the hardest of the three.** 128 iterations, 40 rejected (longest run 8), no loss increase, no restart,
7880 s in `minimize()` (reference: 10 iterations, 4032 s), Hessian 817 s, EDM 7.4e-18. The trace is a **staircase**:
four plateaus where the trust radius collapses (runs of 4 to 8 rejected steps) and is rebuilt, each ended by a
step down (iterations ~42, ~66, ~91, ~112). The plateaus are the minimiser sliding along one active face while the
second approaches. At the kink of the other face, the quadratic model, which has no curvature for a slack face, keeps
predicting steps that cross it. Once both faces are active, the model is exact and the last ~8 iterations converge
quadratically. Per-iteration cost stays low (median 38 s), because rejected steps reuse the Krylov space.

### XL4Z (card A, λ4_ν held at 0): XL4ZSTIFF vs Y35ZWALLL4ZR

| quantity | value |
|---|---|
| NLL new (τ 8, m 0) | 372.2832217253 |
| NLL ref (τ 5, m 5e-3) | 372.3500817672 |
| ref vector under the new objective | 372.3477099374 (pen₀ = 0) |
| **gain on the new objective** | **−0.0645** (2Δ = −0.129) |
| Δbase (unwalled) | −0.0645 |
| new vector under the ref objective | 372.8340 (+0.484) |
| wall term at the new minimum, e¹⁶·pen₀ | 4.9e-6 |
| EDM new / ref | 3.4e-17 / 6.7e-17 |
| **Δ`alphaS` / σ_ref** | **−0.024** |
| σ_new / σ_ref (`alphaS`) | 1.0002 |
| largest |Δθ/σ_ref| | λ2_ν −0.98, λ2 +0.14, λ4 +0.06; every non-NP parameter ≤ 0.021 |

| λ (physical) | ref | new | Δ/σ_ref |
|---|---|---|---|
| λ2 | 0.082378 | 0.090555 | +0.136 |
| λ4 | 0.118780 | 0.120497 | +0.059 |
| δλ2 | −0.009372 | −0.009358 | +0.002 |
| λ2_ν | 0.004672 | −0.0000007 | −0.984 |
| λ_inf, λ_inf_ν, λ4_ν | held 1, 2, 0 | held | — |

| armed condition (5 of 8) | coeff ref | coeff new | active @ m=0 (new) |
|---|---|---|---|
| **λ2_ν ≥ 0 (CS small-b)** | **0.004672** | **−7.4e-7** | **yes (the only face)** |
| L2(|Y|=0) ≥ 0 | 0.0824 | 0.0906 | no |
| B(0) | 0.3569 | 0.3622 | no |
| L2(|Y|=2.5) ≥ 0 | 0.0238 | 0.0321 | no |
| B(2.5) | 0.3564 | 0.3615 | no |

**Physics read (XL4Z).** With λ4_ν held at 0, the CS kernel's only small-b handle is λ2_ν, and the data push it to its
boundary: λ2_ν = 0 means γ_ν^NP vanishes identically at this point (λ2_ν = λ4_ν = 0, below the saturation). That is
the "TMD route": all the NP freedom is in the TMD sector, whose faces all have ≥ 0.03 of slack. ΔNLL = −0.064,
Δ`alphaS` = −0.024σ. As for XW, λ2_ν sits on the AD cache's validity edge.

**XL4Z vs XW on the same objective** (same card, same wall; XL4Z = XW with λ4_ν held at 0, so the two fits are nested;
`scripts/cross_xl4z_xw.py`, `cross_xl4z_xw.out`): ΔNLL = +0.955 (2ΔNLL = 1.91, vs 1.81 at the old wall in the study
logbook), Δ`alphaS`(XL4Z − XW) = **+0.259 σ_XW** (+0.240 σ_XL4Z), σ_XL4Z / σ_XW = 1.083. These match the orchestrator's
numbers. So with the exact wall, freezing λ4_ν costs 2ΔNLL ≈ 1.9 and moves `alphaS` by a quarter σ (input for T8).

![XL4Z loss history](loss_history_XL4Z.png)

Caveat for the figure: the reference is two logs, the 17-iteration fit that was SIGTERMed and its 1-iteration resume.
Each curve is relative to its own final loss.

**Minimiser (XL4Z).** 43 iterations, 21 rejected (longest run 11), no increase, no restart, 5909 s in `minimize()`
(reference: 17 + 1 iterations, ~4656 s + 1790 s), Hessian 859 s, EDM 3.4e-17. One face, so one long plateau (iterations
~5 to 25) and then quadratic convergence by iteration ~30. The final 12 iterations are rejected steps at the converged
loss (radius shrinking to nothing before the "bad approximation" exit). They cost about 10 s each, but one iteration at
the turn (iteration 30) took 1872 s of Krylov work.

### Summary across the three fits

| fit | gain on new obj | Δ`alphaS`/σ_ref | σ ratio | faces active at margin 0 | EDM | iters (ref) | `minimize()` s (ref) | rejected (longest run) |
|---|---|---|---|---|---|---|---|---|
| NOM | −0.076 | +0.012 | 0.999 | L2(2.5) | 3.0e-14 | 41 (28) | 4152 (5698) | 13 (4) |
| XW | −0.110 | −0.038 | 0.999 | λ2_ν, B(2.5) | 7.4e-18 | 128 (10) | 7880 (4032) | 40 (8) |
| XL4Z | −0.064 | −0.024 | 1.000 | λ2_ν | 3.4e-17 | 43 (17+1) | 5909 (~6446) | 21 (11) |

Total run time with the Hessian (no saturated test or impacts): 5008 s, 8994 s and 7015 s. Peak memory about 320 GB each.

### Recommendation: the stiff wall is enough for the census (T4). Do not port trust-constr (T2b).

All three re-minimisations converged under trust-krylov with the margin-0, τ = 8 wall:
- EDM between 7e-18 and 3e-14.
- No loss increases, no restarts, no stall that tripped early stopping.
- Each fit landed exactly on a true damping boundary: the overshoot is ≤ 1.1e-6 in the coefficient and ≤ 1.2e-5 in
  the NLL. So the relu² wall at τ = 8 acts as an exact equality constraint on the active faces, which is what
  trust-constr would give.
- The objective change does not distort the answer. `alphaS` moves ≤ 0.04σ from the 5e-3-margin minima, σ(`alphaS`)
  changes ≤ 0.1 %, and every non-NP nuisance moves ≤ 0.02σ.

The cost is real but bounded. Each face the fit has to find adds a plateau of radius collapses. One face costs about the
same as the reference (NOM, XL4Z: 41 to 43 iterations, about 1 to 1.6 h). Two faces (XW) took 128 iterations and 2.2 h.
A census start far from the faces may need more steps of the staircase.

For T4:
- (i) Budget about 3 h of minimisation per start.
- (ii) Do not set `--earlyStopping` below about 15 (rejected runs reached 11) unless the restart path is wanted, since a
  restart resets the radius and might even shorten the plateaus. This is untested.
- (iii) Read convergence from the EDM and the face list, not from scipy's `success` (it is False on every fit,
  including the references).

trust-constr would remove the kink-learning plateaus, but the knowledge note says it never converges at tol 0. That makes
it a worse trade than about 1.5× the iterations.

---


---

## Findings

<!-- One line each. A finding that generalizes beyond the parent study → tell the
     orchestrator; it belongs in ../../../knowledge/. -->

1. A relu² wall at margin 0 and τ = 8 acts as an exact constraint under trust-krylov: three warm refits converged
   (EDM ≤ 3e-14) onto true damping boundaries with overshoot ≤ 1.1e-6 in the coefficient and ≤ 1.2e-5 in the NLL —
   (evidence: `analysis.out`).
2. The difficulty is per active face: each new face costs a plateau of 4–11 rejected steps while the trust region learns
   the kink (the model has no curvature for a slack face). Rejected steps are cheap (reused Krylov space). With one face
   the fit costs about the same as a 5e-3 fit; with two (XW) it took 3× the iterations — (evidence: `loss_history_*.png`).
   Generalises: worth a line in `knowledge/20_frameworks/rabbit_minimizer_tolerances.md`.
3. Relative to the 5e-3 cushion, the margin-0 minima gain 0.06–0.11 NLL and move `alphaS` ≤ 0.04σ. The gain is predicted
   to first order by (wall force at the reference) × (cushion distance), e.g. NOM 16.8 × 0.0046 = 0.078 vs 0.076 measured —
   (evidence: `analysis.out`).
4. At margin 0, both no-lattice routes put λ2_ν exactly at 0, the edge of the AD cache's validity (exact for λ2_ν ≥ 0) —
   (evidence: `analysis.out`; `knowledge/20_frameworks/scetlib_ad_cache_validity.md`).
5. With the exact wall, freezing λ4_ν (XL4Z vs XW) costs 2ΔNLL = 1.91 and shifts `alphaS` by +0.26σ — (evidence:
   `cross_xl4z_xw.out`).

---

## Open questions

- XW now has B(0) slack of only 4.9e-4 (in λ4 + L2³/3 units), next to the TMD large-b cliff onset. A census start with
  lower λ2 may activate a third face, so expect a longer staircase there.
- Would `--earlyStopping ~10` (a restart resets the trust radius) shorten the plateaus? Untested.
- Fits that sit on λ2_ν = 0 are at the AD cache's validity edge. A small positive margin on that one condition only would
  keep them strictly inside, if Luca wants that. It needs a per-condition margin, which does not exist.
- The NOM lattice tension (λ2_ν = 0.064 vs the lattice 0.1345 ± 0.031) flagged by T1 is unchanged: λ2_ν moved +0.0009.
