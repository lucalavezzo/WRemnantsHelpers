---
title: ptVGen overflow / qT>100 truncation — last-bin closure
slug: ptvgen-truncation
status: active
created: 2026-07-02
updated: 2026-07-03
---

# ptVGen overflow / qT>100 truncation — logbook

**Goal:** understand the last-ptll/last-ptVGen bin residuals in the ParamModel
validation, and decide what (if anything) to fix. Two audiences: (a) the FIT
(does it bias αs?), (b) THEORISTS (does the σ_gen integral reproduce SCETlib+DYTurbo,
esp. in the tail?).

---

## START HERE (2026-07-03) — ROOT CAUSE FOUND (fixable; earlier hypotheses were WRONG)

> **ROOT CAUSE of the high-qT resum deficit: the cache bT grid's LOWER LIMIT.**
> `[bT_grid] min = 1e-3` → the cache has NO nodes below bT=1e-3. At high qT the
> resummed σ is a tiny residual of a colossal oscillatory bT-Hankel cancellation
> (cumulative swings +158×, −1.9×, +78× before settling to 1× by bT~10). The integrand
> W(bT) *grows* toward small bT (W(1e-6)=2485 vs W(1e-3)=48), so the region
> [1e-6,1e-3] — though pointwise small — carries a NON-cancelling ~0.54×σ of the
> residual. Truncating it at 1e-3 gives 0.444×σ at qT=100; extend to bmin=1e-5→0.999,
> 1e-6→0.9997 (spline+analytic-J0 Hankel).
>
> **THE FIX NEEDS TWO CHANGES — verified end-to-end in the REAL production node-Simpson
> path (`verify_fix_{sample,recon}.py` → `btgrid_tf.reconstruct_batch_tf`):**
> ```
> grid            N  | qT=90    qT=95    qT=100    (dev% qT=100)
> current(1e-3) 2000 | 0.864    0.695    0.180     -82%  (node-Simpson; worse than spline's 0.44)
> 1e-6          4000 | 0.99884  0.98822  1.03879   +3.9%
> 1e-6          5000 | 1.00006  1.00014  1.00394   +0.39%
> 1e-6          6000 | 0.99999  0.99997  1.00003   +0.003%  <- CONVERGED
> 1e-6          8000 | 0.99999  0.99999  0.99997   -0.003%  (flat beyond)
> ```
> (1) `[bT_grid] min = 1e-6` (small-bT support) AND (2) `n_points ≈ 6000` (up from 2000).
> Production quadrature is composite Simpson over the RAW bT nodes with the J0 kernel baked
> in, so it must RESOLVE J0(qT·bT) across the support region (bT≲8) — the "density
> irrelevant" result held only for a spline that applies J0 analytically. Both levers
> required; either alone fails (1e-6 @ N=2000 → −8.4; 1e-3 @ any N → 0.18).
> COST: Nbt 2000→8000 = 4× the (Nbins,Nbt) I_pert/C_nu tensors → GPU memory (see OOM note).
> Tail is fit-subdominant + cancels in rnorm, so high-N may be needed only for the THEORIST
> closure plot, not the fit; a hybrid bT grid (log at small bT + fine in the J0-support
> region) could close with far fewer nodes. OPEN design choice for Luca.
>
> **Every earlier hypothesis was disproven (with evidence):**
> - NOT the NP application. `np_factorization_clincher.py` PROVES, point-by-point in bT,
>   that our `exp(C_nu·γ_ν^NP)·F_eff` == SCETlib's internal NP to ~1e-12 (toggling each
>   piece via `resummed_bT_integrand`; F_eff form, γ_ν form, C_nu decomposition, and the
>   multiplicative factorization all == 1.0 to 10–14 digits). The old
>   `scetlib_integrand_clincher.py` was BROKEN: `configure_calculation` sets the γ_ν model
>   but NOT `set_effective_model` (that lives in the variations flow), so F_eff defaulted
>   to identity (C++ `NP_model_effective` all-zero → 1) → undamped integrand → its simpson
>   Hankel blew up. That never tested the NP.
> - NOT "intrinsic cancellation / needs a SCETlib source change". A finite real-b Hankel
>   DOES reproduce SCETlib's DE integrator to 0.03% once the full bT range [1e-6,∞) is
>   included (`btgrid_range_isolation.py`).
> - NOT bT node density. 2000→64000 nodes over [1e-3,50] ALL give 0.4444; direct 400k
>   no-spline too (`btgrid_density_convergence.py`). The "quadrature already converged at
>   this density" card comment is true for density, wrong for the lower limit.
> - NOT bmax (integrand damped to 1e-35 by bT=40; `[1e-6,30]`→0.9999), NOT qT sampling,
>   NOT the cached I_pert/C_nu values (match SCETlib to ~1–2% on the cache nodes;
>   `compare_cache_vs_scetlib.py`), NOT b_bar convention (b_bar == b_star == bT exactly).
>
> Plot (theorist-facing): `~/public_html/alphaS/260703_btgrid_small_bT_rootcause/`.

- **IN PROGRESS (2026-07-03): validation regen (theorist-only, Luca's choice).**
  New run dir (copy of `..._qtdense60` with ONLY the bT grid changed to min=1e-6,
  n_points=6000): `/scratch/submit/cms/wmass/scetlib_np/Z_COM13_CT18Z_N3p0LL_btgrid_smallbt6k/`
  (card `inclusive_..._smallbt6k_b0nu1.ini` + base.conf + variations_btgrid.conf, all copied
  from qtdense60). Parses OK: 24×165×171 = 677,160 bins; bT [1e-6,50] 6000 log; b0nu1; sing.
  - RUN (v15, ~30 min @ 300 threads; ~65 GB shard + ~65 GB combined + ~18 GB npz — WATCH
    scratch, it was 100% / 471 GB free):
    `singularity exec --bind /scratch,/work,/home,/ceph,/cvmfs <v15> bash -c 'source /opt/env.sh;
     export PYTHONPATH=<study>/scripts/histstub:$PYTHONPATH;
     python3 /work/.../prod/scetlib_run/scetlib-run-qT.py 300 1 <CARD> --bt-grid'`
  - THEN validate vs theory-corr (auto-builds combined + factorized on first load):
    `python3 -m wremnants.postprocessing.scetlib_np.sigma_gen_at_lambda
     --btgrid <smallbt6k dir> --theory-corr <FranksVals CorrZ.pkl.lz4>
     --gen-edges-from <corr or datacard> --np-model tanh_2 --np-model-nu tanh_2`
     (fine_ratio_tail.py has HARDCODED old model values — do NOT reuse; recompute via the CLI.)
  - Prod decision DEFERRED by Luca: may run a fit with old vs new cache to confirm αs
    unchanged before adopting in prod. Options recorded: theorist-only (this), fit-too (4×
    → GPU mem via dedup), or hybrid bT grid (dense only in bT≈0.05–8). Verified end-to-end:
    `verify_fix_{sample,recon}.py`.
- **Fit impact:** small-bT is NP-flat (F_eff→1, γ_ν→0 as bT→0), so the missing piece is a
  ~λ-independent additive constant; it largely cancels in rnorm and the tail resum σ is
  FO/nonsingular-subdominant. Quantify after regen, but expected ≲1e-4 on αs. The theorist
  absolute-closure plot is the real beneficiary.
- **Evidence scripts (this turn):** `np_factorization_clincher.py`, `hankel_integrator_test.py`,
  `compare_cache_vs_scetlib.py`, `btgrid_density_convergence.py`, `btgrid_range_isolation.py`,
  `plot_small_bT_rootcause.py`. Env: v15 + `source /opt/env.sh` + hist stub + bind `/cvmfs`
  for scetlib_core; wremnants `latest` for btgrid_cache/fz_tf/plot.

**SUPERSEDED hypotheses (kept for the record; both WRONG):**
> ~~tiny residual of a 486× cancellation amplifying a sub-permille integrand difference;
> intrinsic, needs SCETlib source change, fit-irrelevant.~~ The cancellation is real but
> the difference is NOT sub-permille-everywhere — it's the fully-missing [<1e-3] bT region.
> ~~high-qT qT-SAMPLING problem tracking qT_unique coarsening; fix = finer qT above 60.~~
> qT sampling is irrelevant; the denser-qT run didn't move it. It's the bT lower limit.

**Earlier framing (still true):**
> The last-bin residuals are ONE root cause: the model's gen ptVGen grid tops out
> at the bt-grid qT ceiling = 100 GeV (overflow bin [44,100]). The theory
> correction (SCETlib+DYTurbo) ALSO stops at qT=100 (measured: corr qT axis top
> edge 100, overflow empty). The MC N_gen overflow is unbounded (qT∈(44,∞)).
> - **σ_gen vs theory-corr, −1.4% in [44,100]**: both ≤100, so this is a genuine
>   model-vs-theory residual in the wide tail bin → the theorist-plot target.
> - **σ_gen vs MC N_gen, −16%**: model[44,100] ÷ N_gen[44,∞); the MC has ~14–16%
>   of its qT>44 yield at qT>100 that neither the model nor the theory covers.
> - **Fit impact: negligible.** rnorm=σ(λ)/σ(λc) cancels the truncation — the
>   measured λ-response of the [44,100] bin is +0.36% for a huge lambda2 0.4→1.0
>   variation (vs −0.05% in [0,44)); qT>100 is even flatter (NP-free FO regime).
>   Residual fit bias ≲1e-4. (Consistent with validate_variation's 0.02–0.05%.)

- **Next action:** Luca is RUNNING the Stage-1 btgrid (denser qT in (60,100]) locally.
  Run dir (output lands here, next to the card):
  `/scratch/submit/cms/wmass/scetlib_np/Z_COM13_CT18Z_N3p0LL_btgrid_fineall_qtdense60/`
  (card `..._qtdense60_b0nu1.ini` + base.conf + variations_btgrid.conf; reviewed copy in
  `btgrid_run/`). Local cmd: `singularity exec --bind /scratch,/work,/home,/ceph
  <wmassdevrolling:v15> python3 <prod>/scetlib_run/scetlib-run-qT.py --bt-grid <CARD>`
  (v15, NOT latest; --start-bin/--stop-bin to chunk; runner = /work/.../prod/scetlib_run).
- **When grid ready:** combine shards → combined_btgrid.pkl; factorized .npz auto-rebuilds
  (mtime/size); then re-run `fine_ratio_tail.py` + theorist plot → confirm [44,100] closes.
- **Blocking on:** the btgrid run finishing.

## btgrid run setup (Stage 1 — the resum tail fix)
- Runcard: copy of the fineall b0nu1 card, **ONLY `[Grid_qT]` changed**: keep [0,60]
  identical (131 pts), replace the coarse tail {62.5,65,67.5,70,75,80,85,90,95,100}
  with **1-GeV points 61..100** (40 pts). 141→171 qT points; grid points 558k→677k
  (1.21×). No points past 100 (Stage 1 = resum fix; past-100 is the separate nonsingular
  chain — resum≈0 there). Everything else (Q, Y, bT 2000 pts, precision, NP b0nu1) identical.
- Rationale: the tail deficit is 100% the bt-grid resum under-integrated by 3-pt Simpson
  over the wide coarse-qT tail bins at the matching turn-off (qT≈Q); 1-GeV qT resolves it.
- Stage 2 (separate, if qT>100 wanted in R/fit): extend DYTurbo nonsingular past 100 +
  model overflow (`PTVGEN_OVERFLOW_EDGE`) + corr; NOT the btgrid. Fit doesn't need it.

---

## Log

### 2026-07-03 (cont.) — new small-bt6k grid: card validation + N_gen overflow cross-check
- **Small-bt grid RAN** (`Z_COM13_CT18Z_N3p0LL_btgrid_smallbt6k`, bT [1e-6,50] 6000 log).
  σ_gen vs theory-corr (`sigma_gen_at_lambda --theory-corr`, ptv to 100): tail closes.
- **Card validation** (`validate_agreement --reference card`, new grid):
  `~/public_html/alphaS/260703_new_btgrid/card_validation/`. σ_reco: bulk-good. σ_gen vs
  card N_gen: **exactly 1.000 in resolved ptVGen [0,44)** (new grid closed the resolved
  region!), then **0.83 in the single overflow bin [44,100-label]**.
- **Root of the 0.83 = the card N_gen overflow domain, NOT our model.** The gen ptVGen
  axis has resolved edges [0..44] + ONE overflow bin labelled [44,100]; but
  `response_matrix._append_axis_overflow` fills it from the histmaker AXIS overflow →
  qT ∈ (44, ∞). The model (and the theory corr) only reach qT=100. Documented in
  `param_model_diagnostics.run_card_diagnostics` docstring (L431-433).
- **CROSS-CHECK (Luca's ask): card N_gen vs the OFFICIAL theory correction directly**
  (`scripts/cardNgen_vs_theorycorr.py`, no model/bt-grid; `_R_info_from_auxiliary` → N_gen +
  gen edges; `theory_corr_projection` for SCETlib+DYTurbo on the same bins). Result:
  `~/public_html/alphaS/260703_new_btgrid/cardNgen_vs_theorycorr/`:
    resolved [0,44): N_gen/corr = **1.0000** (0.02–0.04%, agree by construction — both are
      SCETlib+DYTurbo there, since the histmaker gen is MiNNLO reweighted to the correction)
    overflow  [44,100-label]: N_gen/corr = **1.2043** (card is 20% ABOVE the official corr)
  1/1.2043 = 0.830 = the model/N_gen from the card plot → fully consistent.
  3-WAY (script now also overlays the bt-grid model σ_gen): **model/corr = 1.0002 in the
  overflow** (and ~1.0000 in every resolved bin) — the model tracks the official correction
  to <0.1% EVERYWHERE incl. overflow; the card N_gen is the sole outlier (both model & corr
  stop at qT=100, the card keeps the qT>100 MiNNLO tail). 3-curve plot in the same webdir.
- **Binning mechanics (why we see it):** the histmaker gen ptVGen axis ENDS at 44; qT>44
  goes to the hist OVERFLOW (unbounded). `_append_axis_overflow` pulls that overflow out as
  the trailing gen bin (needed so the model can supply σ_gen(qT>44) → feeds the qT>44→high-ptll
  reco migration, ~6% of the last reco bin); `_gen_edges` LABELS it [44,100] by appending
  PTVGEN_OVERFLOW_EDGE=100 (cosmetic, = what the model covers, NOT a cut). So the qT>100
  MiNNLO tail is folded INTO the [44,100]-labelled bin → the 20% excess.
- **Conclusion:** the high-qT card dropoff is the card's N_gen overflow carrying the
  qT>100 MiNNLO tail (~20% of the [44,∞) bin) that NEITHER the official SCETlib+DYTurbo
  correction NOR our model predicts (both stop at 100). It is NOT a bt-grid reconstruction
  deficiency — the new grid closes σ_gen vs theory-corr (<0.1%) and vs card N_gen in every
  resolved bin (1.000). Options (Luca deferred): (a) ACCEPT — fit-irrelevant (cancels in
  rnorm; the overflow bin's λ-response is tiny, ≲1e-4 on αs, established 2026-07-02); or
  (b) STAGE 2 — extend DYTurbo nonsingular + the correction + `PTVGEN_OVERFLOW_EDGE` past
  100 so the overflow domain is covered consistently. "let's wait."

### 2026-07-02 (cont.)
- Theorist plot produced: `~/public_html/alphaS/260702_scetlib_np_validation/`
  `fine_sigma_gen_vs_theorycorr_Ylt2p5.png` — dσ/dqT model vs SCETlib+DYTurbo on the
  corr's own fine qT binning, |Y|<2.5, + ratio panel (bulk flat at 1; tail dips to
  ~0.91 at [90,100]). Honest bulk-closure + tail-limitation figure. (fine_ratio_tail.py)
- Physics nuance: at qT≈90–100 for Z (Q≈91), qT≈Q is the resummation↔FO MATCHING
  region — resum is NOT negligible there. So the deficit could be the matched-prediction
  accuracy in the transition region, not purely the nonsingular. The `--no-nonsingular`
  test separates them. (Corrects the earlier "resum dead at high qT".)

### 2026-07-02
- Read `response_matrix.py:38-46`: gen ptVGen overflow bin = [44, PTVGEN_OVERFLOW_EDGE=100];
  `_append_axis_overflow` fills N_gen's overflow from the histmaker AXIS overflow →
  unbounded (44,∞). btgrid `fineall` qT max = 100 (model can't go past it).
- Ran `scripts/diagnose_qt_tail.py` on the FranksVals CorrZ: **theory-corr qT axis top
  edge = 100, overflow EMPTY** → the official SCETlib+DYTurbo prediction has NOTHING
  past 100. qT∈[44,100) is 9.87% of σ (|Y|<2.5), 8.90% (|Y|<5). λ-response (var/pdf0,
  |Y|<2.5): lambda2 0.4→1.0 gives [0,44)=0.99950, [44,100)=1.00363; lambda2_nu, lambda4
  ~flat. (evidence: tasks output bxtdc4t0r)
- Conclusion: the −16% (vs MC N_gen) is a domain mismatch (theory/model ≤100 vs MC ≤∞),
  NOT a model bug; the fit is unbiased (cancels in rnorm). The −1.4% (vs theory-corr,
  [44,100]) is the real model-vs-theory tail residual to improve for the theorist plot.

---

## Findings

1. Theory correction (SCETlib+DYTurbo) qT ceiling = 100 GeV; overflow empty — the
   truth itself does not exist past 100. (evidence: diagnose_qt_tail.py)
2. Model gen grid ceiling = btgrid `fineall` qT max = 100; overflow bin [44,100].
3. −16% (σ_gen vs N_gen overflow) = MC qT>100 (~14–16% of qT>44), a theory/MC domain
   mismatch, not a bug. Fit-irrelevant (rnorm cancels; measured ≲1e-4).
4. −1.4% (σ_gen vs theory-corr, [44,100]) is a real model-vs-theory residual in the
   single WIDE tail bin — the thing to reduce for the theorist-facing plot.
5. Fine binning: the tail deficit ACCELERATES toward qT=100 ([90,100]=−8.8%),
   tracking the qT-grid coarsening (1→2.5→5 GeV above 60). (fine_ratio_tail.py)
6. It is NOT b_T (grid has 2000 b_T pts) and NOT the Simpson rebin: `rebin_weights`
   is proper per-bin Simpson, which on a convex falling tail *over*-estimates — wrong
   sign for the −8.8% under-shoot. ⇒ the RECONSTRUCTED POINT VALUES at high qT are
   low. Resum is dead there, so prime suspect = the nonsingular (DYTurbo FO) term /
   cached-kernel precision at high qT. NOT fixable by output binning; needs the
   bt-grid / FO inputs regenerated with finer, accurate high-qT content (= Q2 lever).
   CONFIRMED via `--no-nonsingular` (resumonly_fine.log): at the ceiling the matched
   prediction is NONSINGULAR-DOMINATED — [90,100] matched=7.44, resum-only=0.56 (7%),
   nonsingular=6.88 (92%); corr=8.16 → −8.8%. So the deficit is in the nonsingular-
   dominated high-qT reconstruction (resum has died), where the qT grid is coarse
   (5 GeV). Rebin ruled out (Simpson over-estimates a convex tail = wrong sign). ⇒ the
   cached nonsingular (DYTurbo FO) content at high qT is what to regenerate (= Q2 lever).

---

## Open questions

- Q1 (finer sampling): is the [44,100] −1.4% an integration-granularity effect of the
  single wide overflow bin (Simpson over sparse btgrid qT points), or a real tail-shape
  diff? TEST: recompute σ_gen on the theory-corr's OWN fine qT edges in [44,100] and
  compare per fine bin. If per-fine-bin closes ≪1.4%, it's the wide-bin averaging.
- Q2 (extend past 100): would need a btgrid + DYTurbo FO computed past 100 — but BOTH
  the grid and the theory-corr stop at 100 (data-limited). Physically qT>100 is FO-only
  (resum→0), so a DYTurbo-FO extension could feed R's overflow / match MC N_gen — but
  it's a PRODUCTION task (re-run inputs), and unnecessary for the fit (cancels).

---

## CONFIRMED: entire tail deficit = bt-grid resum, from coarse-qT under-integration of the matching turn-off (2026-07-02)
`resum_vs_scetlib_tail.py` (model resum-only vs DIRECT SCETlib resummed pkl, fine edges,
|Y|<2.5): **[90,100] resum_model=0.559 vs resum_SCETlib=1.276 → deficit +0.717 = the
matched deficit 0.72.** So nonsingular cancels; the miss is 100% the resummed term.
Ratio degrades with qT-grid coarsening: [44,46]=0.997, [60,65]=0.991, [70,80]=0.977,
[80,90]=0.925, **[90,100]=0.438**. The cliff at [90,100] is the resummation turning off
(qT→Q≈91): 3-pt Simpson over {90,95,100} can't resolve the turn-off ⇒ under-integration.
FIX = finer qT sampling in [60,100] (denser Grid_qT), + extend past 100 for Q2. Bt-grid
Hankel point values are fine (2000 b_T, small-b_T-dominated at high qT), so this is a
SAMPLING fix, exactly the btgrid regen. (evidence: task bir0t8nuk)

## Point-mode reference VALIDATED vs binned truth (2026-07-03)
Cross-check (Luca's ask): point-mode σ Simpson'd to bins (pointmode_refine/{orig_3pt,dense_5pt})
vs the binned truth (franksvals resum combined.pkl, Q=[60,120] bin, var pdf0), qT-projected:
  5pt/truth = 0.9999–1.0000 through the bulk, and **0.9986 at [90,100]** (0.14%); 3pt was
  0.975 at [90,100] (2.5% off). So point-mode(5pt) reproduces the BINNED truth to 0.14% even
  in the deep tail ⇒ the point-mode reference used for the single-point inner-bT tests is GOOD.
  (Also confirms Luca's 3pt→5pt: the OUTER qT-Simpson needs 5pt in the tail — a separate,
  ~2.5%→0.14% effect, NOT the bt-grid's inner-bT problem.) [earlier 2.2× was my bug: summed
  both Q bins [10,60]+[60,120] of the truth.] Net: single (Q,Y,qT)-point comparison is the CLEAN
  isolation (no Y-int / qT-bin confounders); the reference is validated; the bt-grid's 0.44×
  at (91,0,100) is a real gap vs a trusted per-point truth (the NP factorization).

## SCETlib source dig (2026-07-03): it's the NP APPLICATION, not integration/convergence
Source (py/qT/DrellYan.cpp): the point σ.val integrand (get_integrand_x, L416-427) and the
cached `resummed_bT_integrand` (L435-447) call the SAME `_sigma.resummed(...).total()` with
identical Q,qT,b_star,Mu ⇒ perturbative integrand IDENTICAL. bT integrator `_int_bT` =
`integrator_de_oscillatory` (Ooura DE-for-Bessel), max_iterations 2→20 (L67, "wiggle
hypothesis: point/bin bT integral under-converged").
TESTS:
- Tight-precision point run (pm_default 1e-5 vs pm_tight 1e-9, current max_iter=20 build):
  σ.val IDENTICAL to 6 figs at every qT incl 100 ⇒ SCETlib's σ.val is CONVERGED, NOT
  under-converged. (Corrects the earlier "capped integrator" lead.) Still 2.25× our Hankel.
- Our Hankel converged (N 200k→6.4M + scipy.quad, 1e-11). So BOTH converged, differ 2.25×
  at qT=100, agree 0.06% in bulk.
- Clincher probe: the EXPOSED `resummed_bT_integrand` is NP-OFF (undamped; my Hankel of it
  →286). So the bt-grid caches the NP-off perturbative integrand and WE apply NP as a
  multiplicative factor exp(C_nu·γ_ν^NP)·F_eff; SCETlib's σ.val bakes NP into resummed().
⇒ CONCLUSION: perturbative integrand same + both integrations converged ⇒ the 2.25× gap is
the NP APPLICATION — our factorized bt-grid NP vs SCETlib's internal NP — a sub-0.25%
difference, invisible in the bulk, amplified ~500× by the deep-tail cancellation (486x at
qT=100). NOT quadrature, NOT precision, NOT bT grid, NOT config, NOT under-convergence.
OPEN (areimers/SCETlib): does exp(C_nu·γ_ν^NP)·F_eff on the NP-off integrand EXACTLY equal
SCETlib's NP-on resummed()? Needs the NP-on integrand exposed (a SCETlib code change) or the
author. (evidence: scetlib_clincher.log, pointmode_bT_converge.log, DrellYan.cpp L67/L416-447)

## (earlier framing) SCETlib σ.val ≠ real-b Hankel of its exposed integrand
`scripts/hankel_converge.py` — real-b Hankel of the CACHED (exact-at-nodes) integrand,
N-sweep 200k→6.4M + scipy.quad, Q=91: result/pm CONSTANT to 6 sig figs & quad agrees to
~1e-11: qT=90→0.905, qT=95→0.819, qT=100→0.444. So the integral is EXACTLY CONVERGED.
⇒ NOT a representation error (grid stores SCETlib's integrand exactly; node-invariant 2000→
16000) and NOT integration order (converged). The EXACT real-b Hankel of SCETlib's EXACT
integrand = 0.444×(SCETlib point value) at qT=100. So **SCETlib's σ(Q,Y,qT).val is NOT the
real-b Hankel of the `resummed_bT_integrand` it exposes** — the bt-grid factorization premise
(σ = ∫db bT J0(qT·b)·integrand) holds to 0.06% in the bulk but breaks in the deep tail.
The absolute gap is ~constant ≈0.0025 ≈0.25% of |C|max (pre-cancellation ~1.0); the 486×
cancellation turns 0.25% into 54% at qT=100. Likely origin = a different bT contour/prescription
in σ.val vs the real-line integral (what changes a delicately-cancelling oscillatory integral);
confirming needs SCETlib source (`resummed_bT_integrand` vs how σ.val integrates bT — areimers).
Earlier "cached-representation" wording RETRACTED. (evidence: hankel_converge.log task bd8ilitr7)

## (context) high-qT resum σ is a tiny residual of a huge bT cancellation
`scripts/hankel_cancellation.py` at Q=91,Y=0 — result = qT·∫g, |C|max = peak partial sum,
cancellation = |C|max/|result|:
  qT=20  res 1.355   |C|max 3.1   cancel 2.3x
  qT=60  res 0.160   |C|max 1.4   cancel 9x
  qT=90  res 0.0218  |C|max 1.04  cancel 47x
  qT=100 res 0.0021  |C|max 1.00  cancel 486x
The resummed σ at high qT is a TINY residual of a MASSIVE oscillatory bT-Hankel cancellation
(486x at qT=100). The cached integrand matches SCETlib to ~0.1% (bulk level); the cancellation
AMPLIFIES that by the cancellation factor: 0.1%×486 ≈ 50% = the observed tail deficit (0.44);
0.1%×47 ≈ 5% ≈ the qT=90 deficit (~9%). QUANTITATIVELY closes the loop.
⇒ CAUSE = a sub-permille cached-integrand-representation difference vs SCETlib's on-the-fly
integrand, amplified 100–500x by the deep-tail cancellation. NOT integration order (converged),
NOT bT grid, NOT qT, NOT config. INTRINSIC to reconstructing a 500x-cancelled residual from a
finite cache — needs the cache to match SCETlib to ≪0.1% (infeasible). Physically negligible
(res 0.002 vs peak ~35; FO-dominated matched σ; cancels in rnorm → fit unaffected).
This is the RESOLUTION of the study's question. (evidence: hankel_cancellation.log task b1z1bvqyw)

## Q-scan (2026-07-03): NOT clean qT/Q scaling; NOT integration-order
`scripts/hankel_check_Qscan.py` (Q=60,91,120, Y=0), ours(2000 Simpson)/hi(400k)/pm:
- Q=91 (peak): clean deficit from qT≈85, hi/pm 0.95(85)→0.91(90)→0.82(95)→0.44(100).
- Q=120: mild, hi/pm 0.93 at qT=100 (qT/Q=0.83).
- Q=60: goes WILD >1 above qT≈80 (hi/pm 1.9 at 85) — but resummed σ tiny there, small-# noise.
At the SAME qT/Q the deficit is worse at higher Q; at the same absolute qT it's worst at the
peak Q=91. So NOT a clean profile-transition (qT/Q) scaling — my earlier qT≈Q framing is only
partly right. FIRM: ours==hi until ~qT85 then both miss pm equally ⇒ NOT an integration-order
issue (400k-pt converged = 2000-pt Simpson up to ~qT85; more/smarter points can't fix it).
Answers Luca's "do we just need 7pt?": NO. (evidence: hankel_Qscan.log)
Next: cancellation analysis — is high-qT a tiny residual of a large oscillatory cancellation
(→ acutely method-sensitive, cached-integrand Hankel can't match SCETlib's internal value)?

## FINAL: a bigger bT grid does NOT help — intrinsic factorization limit at high qT (2026-07-02)
Scanned bT density {2000,8000,16000} × range {50,150} via `generate` (integrand) +
`scripts/btgrid_scan_reco.py` (reconstruct WITH NP vs point-mode SCETlib), Q=91,Y=0:
  hi/pm (high-accuracy Hankel of the integrand) is IDENTICAL for ALL four grids:
    qT=90 → 0.915,  qT=95 → 0.828,  qT=100 → 0.449.
So more/wider bT changes NOTHING — the Hankel CONVERGES (bT is fine) but converges to
0.45×point-mode at qT=100. ⇒ the deficit is NOT the bT grid; it's an intrinsic difference
between the factorized reconstruction (Hankel of cached I_pert×NP) and SCETlib's DIRECT
resummed spectrum in the profile-transition region qT≈Q. Corroborated by resummed-vs-
resummed (0.42 vs the franksvals resum pkl). The factorization closes 0.06% in the bulk,
breaks toward qT→Q. NOT fixable by any btgrid regen (density/range/qT all ruled out; config
matches). NP-off `generate` self-test is USELESS here (b0_over_bmax=0 → NP is the only
large-bT damping → bare Hankel diverges). Env to run generate: v15 + `source /opt/env.sh`
(LHAPDF) + hist stub (scripts/histstub). (evidence: btgrid_scan_reco.log, task bmd8baewn)
IMPACT unchanged: qT≳90 only, resum subdominant there, CANCELS in rnorm → fit unaffected;
only the theorist absolute-closure plot. Options: accept/document, OR investigate the
factorization vs SCETlib-direct near qT≈Q (deep; likely a genuine bt-grid-method limit).

## (superseded) DIAGNOSIS: high-qT resum miss attributed to the bT integration (2026-07-02)
`scripts/hankel_check.py` (fixed-API port of prod hankel_quadrature_check) at Q=91,Y=0,
per qT — ours(2000-node Simpson) vs hi(spline→400k linear) vs point-mode SCETlib:
  qT   ours/pm  hi/pm  ours/hi
  80   0.970    0.971  1.000
  90   0.866    0.905  0.956
  95   0.695    0.819  0.848
  100  0.180    0.444  0.405
TWO failures, both bT-integration, both cliff toward qT=100:
 (1) ours/hi<1 → our fixed 2000-node bT Simpson is BIASED at high qT (the J0 oscillation is
     undersampled on the log grid at large bT). Partly fixable model-side (better Hankel
     quadrature) with NO regen.
 (2) hi/pm<1 → even PERFECT integration of the stored 2000 nodes ≠ SCETlib → the bT
     node-set density/range is insufficient. Needs a bT REGEN ([bT_grid] n_points↑ from
     2000, maybe range). qT sampling & config already RULED OUT.
IMPACT: only qT≳85 (last 1–2 gen bins); resum is subdominant there (nonsingular-dominated)
and CANCELS in rnorm → fit unaffected; matters only for the theorist absolute-closure plot.
(evidence: task b1960zgob; hankel_check_tail.log)

## The deficit is in the RESUMMED (bt-grid) term (Luca, 2026-07-02) — CORRECTED

Earlier I wrote "nonsingular is the culprit" — WRONG, it used the circular assumption
corr_resum≈model_resum. Luca's correct point: the nonsingular (DYTurbo FO − SCETlib
singular) is the SAME on both sides, so it cancels:
  model − corr = resum_model − resum_corr.
At [90,100]: model−corr = 7.44−8.16 = −0.72; resum_model (resum-only run) = 0.56 →
**resum_corr ≈ 1.28**, i.e. the bt-grid resum is ~2× low there. ⇒ the deficit is the
RESUMMED term we supply from the bt-grid — exactly what a finer-qT btgrid run addresses.
Caveat: "nonsingular identical" assumes the model's `compute_nonsingular_gen` bins σ_ns
the same as `make_theory_corr` does; the clean confirmation is model resum vs DIRECT
SCETlib resum (resum_vs_scetlib_tail.py, running) — if resum_model is ~0.72 low at
[90,100], it's unambiguously the bt-grid, and native-vs-rebinned tells sampling vs
point-values (→ whether finer Grid_qT suffices).

## Decisions

- 2026-07-02 — the qT>100 truncation does NOT bias the fit (rnorm cancellation,
  measured) — so any extension past 100 is for absolute-closure / theorist-plot
  cosmetics, not αs correctness.
