# bt-grid precision / accuracy study — logbook

**Goal:** make the bt-grid + on-the-fly param-model σ_gen reproduce direct
high-precision *binned* SCETlib runs as closely as possible — understand and
reduce the residuals seen in `plot_precision_compare.py` overlays. Active focus:
a **~0.5% "wiggle" in the lowest qT bins** (param-model export vs binned SCETlib
reference), in-acceptance.

**Tooling**
- `plot_precision_compare.py` (this dir) — overlays SCETlib spectrum runs at
  various `target_precision_rel` vs the bt-grid param-model export, ratio panel.
  (Fixed a Q-underflow flow-leak in `project()` → use `slice(...,sum)`; compare
  with `--yslice 0 2.5`, the fit acceptance.)
- `scetlib_np_param_model_export_spectrum.py` (WRemnants) — exports the param
  model's native resum-only `sigma_YqT_central` onto a SCETlib run's (Q,Y,qT)
  edges via committed `btgrid_integrate.rebin_weights`. Run with
  `CUDA_VISIBLE_DEVICES=""` (CPU; avoids GPU OOM at high bT).
- Fit gen grid: `ptVGen∈[0,100]` ([44,100] is a folded overflow bin),
  `absYVGen∈[0,2.5]` with **no |Y| overflow** → forward Y never enters the fit.

---

## ✅ RESOLVED — FINAL SUMMARY (2026-06-24)

**The low-qT "wiggle" was a config bug: the bt-grid was generated with
`b0_over_bmax_nu = 0` instead of the FranksVals value `1`.** The `btgrid_fineall`
runcard had no `[Nonperturbative]` section, so it silently inherited `0` from
`prod/scetlib_run/defaults.conf`. `b0_over_bmax_nu` sets the b\* prescription
*inside the perturbative γ_ν evolution* (`Gamma_nu.cpp:102-103`), and `force_np_off`
(bt-grid mode) KEEPS it — so the stored `I_pert`/`C_ν` used the wrong rapidity
kernel. Fix = add `[Nonperturbative]\n b0_over_bmax_nu = 1.\n np_model_nu = tanh_2`
to the runcard and regenerate. **Result: in-acceptance wiggle 1.011 % → 0.006 %
(flat).** Binned, point-mode, and the corrected bt-grid now all agree.

**Diagnostic chain (each step ruled something out — details in the sections below):**
sampling (v2 bT/qT/Y, qx2 Q) → our integration layer (B2: point-mode binned ==
binned run) → our bT-Hankel quadrature (B3 `hankel_quadrature_check`: ours == fine
grid to 1e-5) → bT range (truncation scan) → low-bT edge/sampling → SCETlib's bT
integrator (`_int_bT` DE-oscillatory `max_iter` 2→20: bit-identical, already
converged) → **`b0_over_bmax_nu` mismatch** (verified: point run at b0_nu=0 matches
our recon to 0.99999; b0_nu=1 gives the wiggle; regen at b0_nu=1 → flat).

**Two residuals remain, both benign:**
- **Flat −0.05 % "Simpson-rebin floor":** the export & `point_to_binned` integrate
  each experimental bin with a 3-node (edge+center+edge) Simpson on the grid's
  samples; that's 4th-order accurate but leaves ~0.05 % vs SCETlib's exact adaptive
  bin integral. Flat in qT (a normalization, largely absorbed by R). Improvable by
  more nodes/bin (5-node ⇒ ~10-100× smaller) at the cost of a bigger grid — a knob
  for the grid-density optimization, not a bug.
- **High-qT (>~30 GeV) bt-grid drift** (green falls below 1 while point-mode stays
  flat): the σ→0 amplification of a tiny bounded reconstruction residual in the
  cancellation-dominated tail. **b0-INDEPENDENT** (b0nu0 == b0nu1 for qT≥15) and in
  the region where the resummed-only `sing` piece is matched away (→ DYTurbo), so it
  does not propagate to the fit (covered by the 0.14 % reco closure).

**Production grid replaced (2026-06-24):** the corrected b0_nu=1 grid now lives at
the official path `/scratch/submit/cms/wmass/scetlib_np/Z_COM13_CT18Z_N3p0LL_btgrid_fineall/`
`combined_btgrid.pkl` (17.9 GB, `config b0_over_bmax_nu=1` verified on load). The old
buggy grid is preserved alongside as `combined_btgrid.pkl.b0nu0_OLD_PREFIX` (17.5 GB).
Source grid: `/ceph/.../zstuff/Z_COM13_CT18Z_N3p0LL_btgrid_fineall_b0nu1/`. Corrected
config: `TheoryCorrections/SCETlib/com13_ct18z_btgrid_fineall_b0nu1/`.

**Plots (`~/public_html/alphaS/`):** `260624_b0nu1_fix_validation/b0nu1_fix_*.png`
(old wiggle vs fixed-flat) and `…/final_binned_point_btgrid_*.png` (binned +
point-mode + corrected bt-grid, all agree). Earlier diagnostics in
`260624_pointmode_vs_binned_btgrid/`.

**Tools:** `point_mode_compare.py`, `hankel_quadrature_check.py` (+`--npoff`),
`lowbt_edge_check.py`, `plot_point_mode_wiggle.py` (this dir); committed
`point_to_binned.py` + `scetlib_np_param_model_export_spectrum.py` (WRemnants);
`scetlib-run-qT.py --point-spectrum [--force-np-off]` (the `--force-np-off` flag was
added this session).

**Remaining (see TODO):** revert the inert `DrellYan.cpp:67` max_iter 20→2;
propagate the `[Nonperturbative]` fix to the canonical runcard / any other production
grids; reclaim ceph (delete the redundant `…_b0nu1` source dir); grid-density
optimization vs the corrected grid.

---

## 2026-06-28 — consolidated 3-mode overlay (binned tolerances + point + bt-grid)

Regenerated a single overlay of all three calculation modes with `plot_precision_compare.py`,
ratio = **reldiff [%]** vs the 1e-5 binned reference, in the fit window (Q∈[60,120], |Y|<2.5):
- **Binned, 3 tolerances:** `…franksvals_fine` (1e-5, ref), `…_rel1em4` (1e-4), `…_rel1em3`
  (1e-3, the Jun-26 re-run `…_pdf0_bins_000_11480.pkl`).
- **Point mode:** `pointmode_binned`.   **bt-grid:** `paramodel_btgrid_b0nu1` (corrected b0_nu=1).

**Result (reproduces the resolved picture):** all binned tolerances + point-mode lie within
**<0.05 %** of the 1e-5 ref across qT and Y; bt-grid is flat to ~30 GeV then drifts to **−1.3 %**
by qT≈70 (the σ→0 matched-away tail). dσ/dy (summed over qT): 3-node point-mode **−0.045 %** flat,
bt-grid **−0.20 %** flat (Simpson-rebin floor + folded tail). Plots (tag `binned_point_btgrid`):
`~/public_html/alphaS/260628_scetlib_binned_point_btgrid/binned_point_btgrid_{pt_Q60-120_y0_2.5,pt_Q60-120,y_Q60-120}.png`.

**5-node point-mode variant (`pointmode_refine/dense_5pt_binned.pkl`, tag `binned_point5pt_btgrid`):**
the 5-node Simpson-per-bin **erases the −0.045 % rebin floor** — the point-mode curve now lies on
the binned ref at **0 %** across the whole acceptance (dips only to ~−0.1 % at |Y|>4, out of accept.),
confirming the TODO prediction (5-node ⇒ 10–100× smaller floor). Same `…/260628…/binned_point5pt_btgrid_*.png`.

**Hard-zoom full-Y dσ/dpₜ reldiff (tag `binned_point5pt_btgrid_zoom`, ratio ±0.02 %):** measured the
actual deviations vs the 1e-5 ref (full Y, Q[60,120], `measure_reldiff.py`): **binned 1e-4 = ±0.004 %,
binned 1e-3 = ±0.005 %** (loosest tol → most low-qT jitter, all settle to ~0 above qT≈25 ⇒ the binned
calc is tolerance-converged, even 1e-3 is plenty); **point 5-node = −0.013 %→0** (residual 5-node floor);
point 3-node = −0.11…−0.20 %; bt-grid = −0.17…−0.27 % (off-scale at this zoom). Plot
`…/260628…/binned_point5pt_btgrid_zoom_{pt,y}_Q60-120.png`. Caveat reaffirmed: full-Y folds in
out-of-acceptance forward rapidity, so it is NOT the fit-relevant view (use the `_y0_2.5` acceptance plot).

**Two gotchas fixed in the tooling (`plot_precision_compare.py`):**
1. **`--ref` substring trap:** `franksvals_fine` is a substring of `…_rel1em3`/`…_rel1em4`, so
   `--ref <dirname>` matches the wrong (first) run. **Pass `--ref <full combined.pkl path>`** →
   falls through to the `samefile` check and pins the true reference.
2. **Misleading error bands:** the stored "variance" is SCETlib's `target_precision_rel` estimate
   for binned runs (so the 1e-3 band is only ±0.1 %), **0** for point-mode, and **NaN/placeholder**
   for the bt-grid export — NOT statistical MC error. Added a **`--no-bands`** flag (default keeps
   the old behavior) for a clean central-value overlay; used it for the 260628 plots.

**Point-mode accuracy scaling (2026-06-28, controlled `pointmode_refine` 3-node vs 5-node from
the SAME point run):** point mode has two stages. (1) The SCETlib `--point-spectrum` evaluation is
**~insensitive to `target_precision_rel`** — outer Q/Y/qT bin integrals don't run, only the (already-
converged) bT-Hankel does; accuracy is grid-bound. (2) The point→binned Simpson rebin scales as
**O(h⁴)** in grid density: halving node spacing (3→5 node) shrinks the rebin floor **×18.7 in full Y**
(−0.170 %→−0.0091 %; ideal Simpson = ×16) and **×7.1 in |Y|<2.5** (−0.044 %→−0.0062 %; shallower because
central Y is flat → small f⁗ → already near a sub-leading non-Simpson residual). So the accuracy lever
in point mode is GRID DENSITY (cost ~linear in nodes), not tolerance — vs bin mode where accuracy is
tolerance-guaranteed at power-law cost. See [[scetlib_point_vs_bin_precision]].

**Which axis is the Simpson floor? (2026-06-28) — it's qT (in acceptance), NOT Q/Y/bT.**
`point_to_binned`/export rebin = Q (arctan-Q² Simpson → 1 bin, FIXED by grid, not the node knob)
+ Y (3-pt Simpson/bin) + qT (3-pt Simpson/bin); `--subsample` touches ONLY Y+qT. The 3→5-node ×16
floor drop therefore localizes the floor to **Y+qT rebin** (NOT Q: untouched yet floor vanishes; NOT
bT: point mode does the Hankel internally → shared floor is post-bT). Per-rapidity-slice 3-node floor
(median bulk-qT reldiff vs 1e-5 ref): **|Y|<2.5 = −0.044 %, |Y| 2.5–3.5 = −0.052 %, |Y| 3.5–5.0 = −1.40 %**
(all shrink ~×7–40 at 5-node). ⇒ **in the fit acceptance (|Y|<2.5) the floor is essentially ALL qT**
(Simpson over the sharp Sudakov peak; central Y smooth → adds ~nothing); the forward |Y|>3.5 blow-up is
the Y-rebin choking on dσ/dY near the kinematic edge |Y|→5 — **OUT of acceptance, irrelevant to the fit**.
NB: the earlier "−0.17 % full-Y floor" was forward-Y contamination; the honest in-acceptance number is
−0.04 %. Lever to reduce it = more qT nodes near the peak (not Q/Y/bT).

**bt-grid vs point-mode, same node density (2026-06-28):** the apparent "bt-grid ≫ point mode" gap in
the overlays is an APPLES-TO-ORANGES artifact — the plotted point curve was 5-node, the bt-grid carries
a 3-node Simpson rebin. Measured vs the 1e-5 ref, bulk qT(1,30): point-3node −0.044 % / bt-grid −0.053 %
(accept.), −0.170 % / −0.183 % (full Y). **bt-grid MINUS point-3node = −0.008 % flat in BOTH projections**
⇒ the genuine bt-grid-reconstruction penalty (our fixed log-bT J₀-Simpson Hankel + our NP `F_eff` vs
SCETlib's internal adaptive Hankel+NP) is only ~0.008 %; the rest is the SHARED 3-node Simpson rebin floor.
bt-grid regenerated at 5-node density would match point-5-node. bt-grid's reason to exist is NOT accuracy
but **differentiability in the NP λ's** (apply F_eff/γ_ν^NP at reconstruction → vary λ in-fit w/ gradients,
no SCETlib re-run); see [[scetlib_np_simpson_rationale]]. Simpson error scales E∝h⁴∝1/N⁴ (N pts/bin),
cost∝N → a decade of accuracy ≈ 1.8× points.

**Timing (what's recorded, 2026-06-28):** only the **1e-3 binned** run was profiled
(`…_rel1em3/timing_1e3.log`, `/usr/bin/time -v`): **8:44 wall = 524 s** @ ~200 cores
(CPU 19961 %, 104k CPU-s, 522 MB RSS, single variation). 1e-4 and 1e-5 binned were NOT
profiled (wall time is dominated by `target_precision_rel`, so 1e-5 ≫ 1e-3). Point-mode
SCETlib run ~20 s (logbook); bt-grid *export* onto the binning ~2 min (TF start + 8.5 s grid
load + integrate); the expensive bt-grid step is the one-time grid *generation* (study grids:
v2 1528 s, qx2 1079 s @ 200 thr — bigger than the franksvals_fine binning). Memory has no
SCETlib spectrum-run timings (fit/Hessian only). TODO if a tradeoff table is wanted: re-run
1e-4/1e-5 single-var binned under `/usr/bin/time -v`.

---

## STATUS / current understanding (2026-06-24) — HISTORICAL (pre-resolution; see FINAL SUMMARY above)

- **In-acceptance accuracy is good:** within |Y|≤2.5, bt-grid vs high-precision
  SCETlib agree to **−0.2%**, with a residual **~0.5% wiggle in the lowest qT bins**.
- **The wiggle is NOT a sampling/resolution problem — DEFINITIVELY.** v2 (below)
  doubled bT (2000→4000), went to 5-node qT (141→201), with `target_precision_rel=1e-5`,
  and the wiggle was **unchanged**. The earlier "bT / large-bT dominant" hypothesis
  is **REFUTED**.
- So the reconstructed low-qT **value** is ~0.5% off the binned calc, *density-
  independent*. Leading suspect = **(3) what we integrate** (factorized assembly /
  NP application), not where/how we sample or integrate. Two experiments in flight
  to localize: **Q-double** and **point-mode reference**.

### Possible causes (taxonomy)
1. **Sampling** — our fixed bt-grid (Q,Y,qT,bT) nodes vs SCETlib's adaptive points.
   qT & bT shown converged; **Q is the one untested axis** → Q-double test.
2. **Our integration / method** — our bT-Hankel Simpson, arctan-Q² Q Simpson, qT
   rebin (+ any bug/non-convergence) vs SCETlib's native integration.
3. **What we integrate (LEADING).** `--bt-grid` runs **NP-OFF** and stores
   `I_pert`/`C_ν`; *we* apply `F_eff`/`γ_ν^NP`/`b*` at reconstruction; the binned
   reference ran **NP-ON** natively. If the factorized assembly isn't bit-equivalent
   (or `--bt-grid` mode doesn't store exactly the integrand the binned run uses),
   the per-point dσ differs regardless of sampling/integration — most consistent
   with the density-insensitivity, and largest at low qT (large bT = NP-dominated).
4. *(minor)* **Comparison bookkeeping** — Q-window/|Y|/helicity(UL vs sum)/var-slot/
   point-vs-bin. Would be ~flat, not a low-qT shape → low likelihood.

### Diagnostic logic
- **Q-double** → wiggle shrinks ⇒ Q-integration under-resolved (find converged Q);
  unchanged ⇒ Q converged too.
- **Point-mode** (our per-(Q,Y,qT) differential vs a point-mode SCETlib run at the
  *same* fixed Q, no integration either side) → match ⇒ per-point reconstruction
  (bT-Hankel + NP) correct, so the wiggle lives in the integration layer (Q);
  mismatch ⇒ the per-point reconstruction itself is off (a (2) bug or a (3)
  factorization difference — point-mode localizes but doesn't separate those two).

---

## Log

### 2026-06-24 — baseline (v1 grid: bT 2000, qT 141, Y 165)
- In-acceptance (|Y|≤2.5) −0.2%; the alarming inclusive −2% is an artifact of
  summing out to |Y|=5 (out of acceptance + v1 forward-Y incomplete).
- v1 forward-Y (|Y|≥3.75) incomplete: condor jobs at the Y=+5↔−5 wraparound
  stalled at the x→1 edge (Q≈88–92) and were wall-time-killed before writing,
  taking neighbor cells with them (~11k missing). Irrelevant to the fit.
- Low-qT wiggle decomposed from `residuals_fineall_{point,simpson}.npz`: point vs
  simpson differ only ~0.2% (qT-rebin small); the ~0.5% bulk is a *value* offset
  present even in point mode. [Then mis-attributed to bT/large-bT → refuted by v2.]

### 2026-06-24 — v2 brute-force grid (bT 4000, qT 201, Y 189)
- Config `…/SCETlib/com13_ct18z_btgrid_fineall_v2/`; NBINS 911,736. Ran **locally**
  on submit82 (768 cores, 1.4 TB) — single `scetlib-run-qT.py`, 200 threads,
  **1528 s**, wrote a 58 GB pickle.
- **Did NOT hang** (earlier worry): the x→1 forbidden cells **errored fast → NaN**
  and the pool completed (so local chunk+timeout was unnecessary; the real issue
  was NaN-in-grid, not a hang).
- Validation: bT 4000 ✓, 24/189/201 ✓; **|Y|<2.5 COMPLETE** (0 bad/670536),
  |Y|<3.5 complete; only **7638 bad cells, all |Y|≥4.6** (Y=4.75/5.0 at high Q,
  x>1). Cleaner than v1 (no collateral loss).
- **BUG+FIX:** NaN forbidden cells broke `dedup_grid_rows` (hash-group verify
  fails — NaN≠NaN). Fixed in `param_model.py` right after `btgrid_cache.load`:
  sanitize non-finite `I_pert`/`C_ν` → 0 (their true value — forbidden = zero σ),
  with a printed count. (v1 didn't hit this: condor shards for forbidden cells were
  *absent* → dense_index_map 0-filled; a single-process run writes them as NaN.)
- **KEY RESULT: v2 ≈ v1, low-qT wiggle UNCHANGED** ⇒ not bT, not qT, not
  target_precision. Sampling/resolution ruled out → pivot to Q-double + point-mode.

---

## Active experiments

### A. Q-double (qx2) — isolate the Q-integration
Config `…/SCETlib/com13_ct18z_btgrid_qx2/` = **v1 binning** (bT 2000, qT 141,
Y 165) with **Grid_Q doubled 24→47** (midpoints inserted). Only Q changes vs the
validated v1. NBINS 47×165×141 = **1,093,455** (~35 GB @ bT 2000).
```
# generate (container, ~30 min @ 200 threads):
OUT=/ceph/submit/data/user/l/lavezzo/zstuff/Z_COM13_CT18Z_N3p0LL_btgrid_qx2
mkdir -p $OUT; cp <qx2 cfg>/{*.ini,base.conf,variations_btgrid.conf} $OUT/; cd $OUT
python3 …/scetlib-run-qT.py 200 1 inclusive_…_fineall.ini \
   --no-datfiles --start-bin 0 --stop-bin 1093455 --fixed-var 0 --pdf-member 0 --bt-grid
# export (Q grid read from bt-grid → auto 47-pt arctan-Q² Simpson; NaN sanitizer handles forbidden):
CUDA_VISIBLE_DEVICES="" python3 -m wremnants.postprocessing.scetlib_np_param_model_export_spectrum \
   --btgrid $OUT --out …/scetlib_run/paramodel_btgrid_qx2
# overlay vs v1 + ref, |Y|<2.5:
./plot_precision_compare.py com13_…_franksvals_fine paramodel_btgrid_resum paramodel_btgrid_qx2 \
   --ref com13_…_franksvals_fine --qmin 60 --qmax 120 --yslice 0 2.5 --tag precision_compare_qx2
```
Outcome → wiggle shrinks ⇒ Q under-resolved; unchanged ⇒ Q converged, go to B.

**RESULT (2026-06-24): Q-integration is CONVERGED — wiggle UNCHANGED.** Ran locally
(submit82, 200 threads, 1079 s, 35 GB pkl, all 1,093,455 bins clean; 9306 forbidden
|Y|≥4.6 cells NaN→0). Export in the **`latest` wmass container** (numpy 2.4.6 — the
v15 container's numpy 1.23 CANNOT read the numpy-2.x 260623 datacard: `numpy._core`;
also needs `source /opt/env.sh` first for `hist`/TF). Per-qT ratio (|Y|≤2.5, Q∈[60,120]),
qx2 (47 Q) vs v1 (24 Q): the **wiggle is bit-identical in shape** (dip→0.992 at qT→0,
bump→1.002 at qT≈4, settle ~0.999). The only difference is a **flat +0.04 % norm offset**
((qx2−v1)/ref ≈ +0.0004, constant across ALL qT); max|qx2−v1|/ref = 7e-4, a smooth
monotonic drift, NOT the wiggle. ⇒ **Q-sampling ruled out.** With v2 (qT/bT ruled out)
this eliminates ALL sampling axes (taxonomy cause 1). → go to B.

**Also ruled out a config red-herring (λ₆):** point-mode `vars[0]` echoes `lambda6=0.016`,
`lambda6_nu=0.0007` (SCETlib internal defaults; neither my point-mode `.ini` nor
TheoryCorrections `defaults.conf` set them) while the param model uses λ₆=0 (card 1's
`[Nonperturbative]` omits λ₆ → propagated as 0). HARMLESS: `np_model=tanh_2` does NOT use
λ₆ — `F_eff_tf` `tanh_2` branch (btgrid_tf.py:173-175) is `arg_inf+⅓(λ₂bT/λ∞)³`, the
`λ₆·bT⁵` term is only in `tanh_6` (line 177); ν-side identical (λ₆ᵥ only in `tanh_6`,
line 222-223). Card (1)'s active NP tune (λ₂=0.4,λ₄=0.4,λ∞=1,δλ₂=0; λ₂ᵥ=0.15,λ₄ᵥ=0,
λ∞ᵥ=2) == point-mode == param model. The point-mode test subsumes this anyway.

### B. Point-mode reference — isolate the per-point reconstruction
Compare our per-(Q,Y,qT) differential (Hankel of stored `I_pert × F_eff`, *no*
Q-integration, *no* qT-binning) to a **point-mode SCETlib run at the franksvals
(NP-ON) tune** at the bt-grid (Q,Y,qT) points. Match ⇒ per-point recon correct
(wiggle is the integration layer); mismatch ⇒ per-point recon is the issue.

**RESULT (2026-06-24): the wiggle is in OUR bt-grid reconstruction, not the binning. DECISIVE.**
(Wording note: "per-point reconstruction" = our bt-grid Hankel evaluated point-by-point;
the wiggle = OUR bt-grid vs SCETlib, same whether kept per-point or binned. It is NOT a
statement that per-point and binned disagree — SCETlib's own binned and point views agree,
see the direct check below.)
Point-mode run `…/zstuff/Z_COM13_CT18Z_N3p0LL_franksvals_pointmode` (`--point-spectrum`,
franksvals NP-ON tune, 558,360 pts = the v1 24Q×165Y×141qT grid, `calculation_piece=sing`
— same as ours; 20 s). Tooling: **`point_mode_compare.py`** (constructs the model on the
v1 bt-grid, takes `sigma_flat` from `reconstruct_batch_factorized_tf` → `sparse_to_dense_tf`
= per-(Q,Y,qT) σ BEFORE `integrate_over_Q`, maps the point-mode dict `{(Q,Y,qT,None):σ}`
onto the same grid — 0 unmatched) + **`plot_point_mode_wiggle.py`** (overlay). Run in the
`latest` container.
- Per-point ratio ours/point-mode (|Y|≤2.5): **dip 0.9923 @qT→0, bump 1.0024 @qT≈4,
  dip 0.9990 @qT≈7.5** — i.e. the SAME wiggle as the binned spectrum, same shape AND
  magnitude. Scatter across all (Q,Y) at fixed qT is **tiny (std 1e-5–5e-4)** ⇒ the
  wiggle is a **pure function of qT**, essentially Q- and Y-independent.
- The per-point ratio sits a **uniform +0.04 %** above the binned ratio (paramodel export
  / franksvals_fine). That flat offset = the Q-integral + qT-rebin + |Y|-fold layer
  (consistent with the qx2 +0.04 % Q-convergence shift). So the residual cleanly
  decomposes: **wiggle (≤0.8 %, qT-shaped) = per-point bT-Hankel reconstruction;
  flat ~0.04 % = integration/binning layer (negligible).**
- Plot: `point_mode_wiggle.png` (the two wiggles lie on top of each other). npz dump:
  `point_mode_compare.npz` (sigma_dense, pm, Q, Y, qT).

**⇒ The wiggle lives in our per-point bT-Hankel of `I_pert × F_eff`, not the integration
layer.** Point-mode localizes but does NOT separate cause (2) [our bT-Hankel *method*:
fixed log bT-grid + precomputed J0 kernel + Simpson, vs SCETlib's adaptive/oscillatory
Hankel] from cause (3) [the NP form `F_eff(bT)`/`b*`/transition applied by us vs SCETlib].
**Key constraint: v2 already ruled out bT *density*** (2000→4000 unchanged; Simpson is
4th-order so a resolution error would have shrunk 16×) ⇒ NOT a quadrature-resolution
problem. Remaining suspects, density-independent + qT-shaped: **(a) bT-range truncation
(`bT_max=50`)** — low qT ↔ large bT, the qT→0 dip (we run LOW) fits a missing large-bT
tail; **(b) a fixed bT-Hankel *method* bias** (J0-kernel/Simpson vs SCETlib oscillatory
quadrature); **(c) an `F_eff`/integrand definition difference.**

### B2. DIRECT binned-vs-point-mode (3-way overlay) — confirms binned ≈ point-mode
Binned the NP-on point run with the committed `point_to_binned.py` (reuses the SAME
`btgrid_integrate` Simpson machinery as the bt-grid export: `q_integrate_weights` Q→1 bin,
`rebin_weights` 3-node Simpson for Y & qT; derives the 82Y×70qT edges from the grid's
interleaved edges+centers; zeros the qT=0 NaN). Output `pointmode_binned/pointmode_binned.pkl`,
overlaid on `plot_precision_compare.py` against franksvals_fine (binned) + paramodel_btgrid_resum
(bt-grid), |Y|≤2.5. **Result (per-qT, |Y|≤2.5):**
- **point-mode / binned = 0.99955, FLAT (spread 0.014% over qT 2–40), NO wiggle.** The two
  SCETlib views agree to a constant −0.045% = the Simpson-rebin floor (`point_to_binned`
  docstring: the btgrid runcard is designed for <0.05% rebin).
- **bt-grid / binned = the wiggle** (0.992@qT→0, 1.002@qT≈4, 0.999; spread 0.385% over 2–40,
  growing at high qT).
⇒ binned ≈ point-mode is now MEASURED (was inferred); 100% of the wiggle is our bt-grid Hankel.
Plots: `~/public_html/alphaS/260624_pointmode_vs_binned_btgrid/` (full + _zoom).

### Next discriminating test (2 vs 3) — NP-off
Compare our reconstruction with **`lambda_inf=0` (F_eff≡1, pure perturbative bT-integral)**
to a **point-mode SCETlib run with NP OFF** at the same points. Wiggle persists ⇒ it's the
perturbative bT-Hankel *method/range* (cause 2); wiggle vanishes ⇒ it's `F_eff` (cause 3).
Cheap (point-mode run ~20 s; our side is a flag flip). Optionally also bump `bT_max` 50→200
on a small grid to test truncation (a) directly.
STATUS: NP-off point run generated (`…/zstuff/Z_COM13_CT18Z_N3p0LL_pointmode_npoff`, λ∞=0,
λ∞ᵥ=0, 558,360 pts, validated) + `point_mode_compare.py --npoff` wired; comparison was
launched then interrupted, NOT yet read. DE-PRIORITIZED (see B3): F_eff is analytic +
λ-response-validated; user not worried about it. Run later to formally close cause (3).

### B3. Suspect narrowing (2026-06-24) — what the 3-way plot rules out, and the plan
What the binned/point-mode/bt-grid overlay (B2) establishes, logically:
1. **NOT a (Q,Y,qT) sampling issue.** Point-mode is evaluated on the SAME (Q,Y,qT) grid and
   binned with the SAME Simpson rebin as the bt-grid, yet matches the binned run (SCETlib's
   finer adaptive internal sampling) to a flat 0.045 %. If that grid were too coarse to
   sample/integrate, point-mode-binned would itself deviate from binned. It doesn't.
2. **NOT the Q / Y / qT integral, sampling, or bounds.** Those operations (`q_integrate_weights`
   over [60,120], `rebin_weights` Y & qT) are byte-identical for point-mode-binned and
   bt-grid-binned; point-mode-binned goes through all of them with no wiggle ⇒ they add
   nothing (and cancel exactly in bt-grid-vs-point-mode).
3. **Narrowed to the bT integral.** The ONLY step differing between bt-grid and point-mode is
   the bT reconstruction: {our stored `I_pert`/`C_ν` on our bT grid + our `F_eff` + our
   J₀-Simpson Hankel} vs SCETlib's internal bT integration.

**Suspect refinement inside the bT integral:**
- `I_pert`/`C_ν` are **literally SCETlib's own bT-space integrand** (the `--bt-grid` mode just
  writes SCETlib's perturbative pieces at our nodes; we do NOT recompute the physics). So the
  "stored integrand" suspect is NOT a physics/definition difference — it reduces to
  load/interpolation correctness + the bT **node set & range** we evaluate it on.
- `F_eff` application: analytic, λ-response-validated, user not worried ⇒ de-prioritized
  (NP-off test in the section above will formally confirm later).
- ⇒ **Leading suspect = how we do the bT integral**: the J₀-Simpson **quadrature method** and
  the bT **range/endpoints**, NOT density (v2 excluded density).

**Subtlety worth flagging (the real puzzle):** Simpson on a smooth integrand should converge to
the TRUE Hankel as node density →∞, and v2 (2000→4000) shows we ARE converged on our grid —
yet we still disagree with SCETlib (the wiggle), density-independently. Converging on our grid
to a *different* answer than SCETlib points at either (i) a J₀-Simpson **method bias** that more
nodes don't cure (e.g. J₀-kernel/endpoint handling of the oscillatory integral), or (ii) a bT
**range/endpoint** difference (our ∫ over [1e-3, 50] vs SCETlib's internal range / bT→0 / bT→∞
treatment). Both are density-independent + qT-shaped, consistent with everything seen.

**PLAN — check the quadrature/Hankel first (NEXT):** take the SAME stored `I_pert × F_eff` and
recompute the Hankel a *different, high-accuracy* way (finer spline interpolation of the
integrand and/or a dedicated oscillatory method; optionally extend bT range), then compare
that to (a) our `reconstruct_batch` result and (b) the point-mode.
  - high-acc Hankel == point-mode (wiggle gone) ⇒ our `reconstruct_batch` J₀-Simpson is the
    culprit (method bias) — fixable in the reconstruction.
  - high-acc Hankel still wiggles vs point-mode ⇒ it's the bT node-set/range/endpoints of the
    stored grid vs SCETlib's internal integral (then test extended `bT_max`, bT→0 handling).

**RESULT (2026-06-24): our quadrature is EXONERATED — it's NOT the Hankel integration.**
Tool: **`hankel_quadrature_check.py`** (loads the raw v1 grid via `btgrid_cache.load` — 6.6 s;
builds W(bT)=`I_pert`·exp(`C_ν`·γ_ν)·`F_eff` for Q=91,Y=0 from the stored rows + analytic NP;
integrates `qT·∫bT·J₀(qT·bT)·W` two ways: our log-2000-node `simpson_weights` Simpson vs a
**400k-point fine LINEAR grid** Simpson (`scipy.integrate.simpson`) with exact `scipy.special.j0`,
W cubic-splined). Plot `hankel_quadrature_check.png` (also in the webdir).
- **ours / hi = 1.00000** for ALL qT≤58 (1.0000 to 5 dp; only 0.999 at qT≈80 where σ→0).
- BOTH reproduce the SAME wiggle vs point-mode (dip 0.9927@qT→0, bump 1.0023@qT≈4, dip 0.999).
⇒ Given W on [1e-3, 50], our Simpson computes the Hankel correctly; the J₀-Simpson method and
the log-grid resolution are NOT the problem. **The wiggle is in WHAT we integrate (the stored
`I_pert`/`C_ν` and/or the bT range), not HOW.** This test holds W & range fixed, so it
*exonerates the quadrature* by elimination — it does not itself test range/integrand-fidelity.

**Clue (worth following):** the residual (ours−pm)/pm is itself ~one oscillation in qT, zero
crossings ≈ qT 2.5 & 6.2, period ≈ 7–8 GeV ⇒ by Fourier conjugacy the our-vs-SCETlib integrand
difference is concentrated near **bT ≈ 2π/8 ≈ 0.8 GeV⁻¹** — a MODERATE bT (core of the
resummation region), NOT the large-bT tail (`bT_max=50`) nor bT→0. So a range/endpoint cause
is *disfavored*; it looks like a difference in the stored integrand itself at moderate bT
(bt-grid-mode assembly vs point-mode internal assembly of the `sing` piece).

### Range sensitivity RESULT (2026-06-24): range RULED OUT; wiggle lives at bT ≲ 1 GeV⁻¹
Added to `hankel_quadrature_check.py` (re-integrate our Simpson over truncated bT windows,
fraction of full σ at qT=1/4/8/15):
- **`bT_max` 50→30→20→10: σ = 1.00000 unchanged.** The [10,50] tail contributes NOTHING ⇒
  the `bT_max=50` cutoff is irrelevant; the whole integral (and the wiggle) is below bT≈10.
- bT support: [1,50]→keeps ~0% of σ; [0.1,50]→keeps ~75–83% ⇒ the integral is **dominated by
  bT ≲ 1 GeV⁻¹** (small-to-moderate bT), exactly where the Fourier clue (bT≈0.8) points.
  (bT_min=1e-3 is fine: the missing [0,1e-3] piece ~∫bT·W ~ W(0)·(1e-3)²/2 → negligible.)

**CONSOLIDATED CONCLUSION (wiggle hunt).** The ≤0.8% low-qT wiggle is, by elimination:
NOT (Q,Y,qT) sampling [B2], NOT the Q/Y/qT integral or bounds [B2], NOT our bT-Hankel
quadrature/resolution [B3 hankel check, ours==hi to 1e-5], NOT the bT range/`bT_max` [B3 range
scan]. ⇒ It is a **difference in the stored `--bt-grid` integrand `I_pert`/`C_ν` vs SCETlib's
`--point-spectrum` internal integrand of the `sing` piece, localized at bT ≈ 0.1–1 GeV⁻¹.**
Now a SCETlib-internals question (`--bt-grid` write vs `--point-spectrum` assembly), the
user's domain — our reconstruction code is fully cleared.

### Low-bT edge/sampling RESULT (2026-06-24): NOT the edge, NOT low-bT sampling
Tool: `lowbt_edge_check.py` (Q=91,Y=0). Log-grid puts **851/2000 nodes below bT=0.1, 426 below
0.01** ⇒ low bT is the OVER-sampled region (v2 also confirmed density-independence). Per-decade
fraction of σ: [1e-3,1e-2] = +0.2%(qT1)…+2.7%(qT15); [1e-2,1e-1] = 16…142%; **[1e-1,1] = 83…−45%
(dominant)**; [1,10]≈0; [10,50]≈0 ⇒ the integral lives in **bT ∈ [1e-2, 1], dominated by
[1e-1, 1]** (= the Fourier-clue bT≈0.8). The MISSING [0,1e-3] piece (extrapolate W flat,
∫₀^b0 bT dbT) = **1.5e-5 of σ at qT<4** (100× below the wiggle) and **smooth/monotonic in qT**
(1.5e-5→8.7e-4 over qT 0.5→30) ⇒ wrong size AND wrong shape (no oscillation). So the lower edge
and low-bT sampling are excluded; consistent with the Fourier argument (edge bT~1e-3 ↔ qT-period
~6000 GeV = flat, vs the wiggle's ~8 GeV period ↔ bT~0.8).

### High-qT divergence (2026-06-24): SAME phenomenon as the wiggle, NOT a new clue
User noticed bt-grid vs point-mode also diverges as qT grows (down to ~0.97 by qT~80). Checked
from `point_mode_compare.npz` (Q=90,Y=0):
- **Q-scaling:** ours/pm at fixed RAW qT is ~Q-independent (qT=10→0.9997, qT=30→0.9993 for
  Q=70..120), NOT a function of qT/Q ⇒ **NOT the profile transition** (which lives in qT/Q).
- **Denominator test:** the LOCAL ratio (o−p)/p grows (+0.0023@qT4 → −0.031@qT80), but the
  ABSOLUTE difference (o−p)/peakσ stays small & bounded (+2.3e-3@qT4 → −4e-4@qT80 — actually
  SMALLER than the low-qT wiggle), while σ_pm/peak → 0.013@qT80. ⇒ the "divergence" is purely
  the resummed-only σ **vanishing** (high qT = the matching/fixed-order region), amplifying a
  tiny bounded difference.
⇒ Low-qT wiggle and high-qT drift are ONE phenomenon: a single small integrand difference
(δW at bT≈0.8), whose Hankel transform is a bounded function of qT (|o−p|/peak ≲ 2e-3
everywhere). Reads as a wiggle where σ is large, as a blow-up where σ→0. NOT physically
relevant at high qT (resummed-only is matched away there). Plot:
`…/260624_pointmode_vs_binned_btgrid/highqt_divergence_is_denominator.png`.

### FIX VALIDATED (2026-06-24): regenerated bt-grid with b0_over_bmax_nu=1 → WIGGLE GONE
Card: `TheoryCorrections/SCETlib/com13_ct18z_btgrid_fineall_b0nu1/` (= fineall + a
`[Nonperturbative]` block with `b0_over_bmax_nu = 1.`, `np_model_nu = tanh_2`; everything else
byte-identical). Regenerated the grid (558,360 bins, bT 2000; first write truncated at 17.5 GB
because the ceph quota was full — the user freed space; clean re-run = 17.9 GB, "Wrote bT-grid
pickle" OK). Exported (`paramodel_btgrid_b0nu1`) + overlaid vs franksvals_fine and the OLD
b0nu0 export (`paramodel_btgrid_resum`), |Y|≤2.5. **RESULT:**
- OLD (b0nu0)/ref: dip 0.9918@qT→0, bump 1.0019@qT≈4, dip 0.9985 — **1.011% wiggle**.
- NEW (b0nu1)/ref: **FLAT 0.99949 across qT 0.2–15 — 0.006% wiggle (GONE)**. The −0.05% flat
  offset is the Simpson-rebin floor (`point_to_binned` <0.05% by design).
- High-qT convergence of both (~0.996@qT≈51) = the σ→0 denominator artifact (matched away).
Plot: `~/public_html/alphaS/260624_b0nu1_fix_validation/b0nu1_fix_pt_Q60-120_y0_2.5.png`.
⇒ The entire wiggle was `b0_over_bmax_nu=0` (defaulted) vs franksvals `1`. CONFIRMED + FIXED.

**REMAINING (apply the fix broadly):** add `[Nonperturbative] b0_over_bmax_nu=1, np_model_nu=tanh_2`
to the PRODUCTION bt-grid runcard and regenerate the grid the fit actually uses (and v2/qx2 if
kept). Revert `DrellYan.cpp:67` → `2` (the max_iter bump was inert). Then the grid-coarsening
optimization can proceed against the corrected grid (separate study).

### ROOT CAUSE FOUND (2026-06-24): bt-grid built with b0_over_bmax_nu=0, franksvals uses 1
Chain: (1) `_int_bT` max_iter test — bumped `DrellYan.cpp:67` 2→20, rebuilt, re-ran point mode:
**bit-identical** to max_iter=2 ⇒ the DE-oscillatory bT integrator was ALREADY converged (exits
on errd≤errh before the cap). Quadrature-under-convergence REFUTED. (2) Then found the real
cause: `force_np_off` KEEPS `b0_over_bmax_nu` (the b\* prescription INSIDE the perturbative γ_ν
evolution, `Lb=2log(mu0·bstar)`; docstring: "Setting it to 0 silently corrupts the perturbative
resummation kernel saved in the bT-grid"). **`btgrid_fineall` has NO `[Nonperturbative]` section
⇒ inherits `b0_over_bmax_nu=0` from `prod/scetlib_run/defaults.conf:79`; franksvals sets `1`.** So
the stored `I_pert`/`C_ν` used b0_nu=0, the franksvals reference uses b0_nu=1 → different
perturbative γ_ν kernel → the wiggle.
**VERIFICATION (decisive):** force-np-off point run with `b0_over_bmax_nu=0` (matching the bt-grid)
vs our `I_pert` Hankel → **ours/pm = 0.99999 FLAT, ±2% wiggle GONE** (vs b0_nu=1 which gave the
±2%). `hankel_b0nu0.log`. So the NP-off ±2% is 100% the b0_nu 0-vs-1 mismatch. (NP-on b0_nu=0
check running.)
**THE FIX:** regenerate the bt-grid with `b0_over_bmax_nu = 1` in the runcard `[Nonperturbative]`
(don't let it default to 0). Then the bt-grid perturbative kernel matches franksvals and the
wiggle should vanish. NB also check the param model's NP γ_ν path uses b0_nu=1 consistently
(`gamma_nu_NP_tf` takes b_bar=b\*(bT) with b0_over_bmax=0, NOT b0_over_bmax_nu — verify the NP
side is consistent with a b0_nu=1 regen). REVERT `DrellYan.cpp:67` back to `2` (the bump was
inert anyway). Earlier "SCETlib-internals / our-reconstruction" framings are SUPERSEDED: it's a
runcard config bug in the bt-grid production, not the reconstruction or SCETlib's integrator.

### (superseded) Remaining handle (SCETlib-side)
Direct integrand comparison: dump SCETlib's point-mode *internal* bT integrand and compare to
the stored `I_pert`/`C_ν` at the same bT (look near bT ~0.1–1 GeV⁻¹). Needs a SCETlib hook into
the `--point-spectrum` path. Practically: the wiggle is ≤0.2% integrated in-acceptance,
within the validated fit accuracy — academic for the fit, but worth a SCETlib bug-report/check.

---

## TODO / later

**Immediate follow-ups from the b0_nu fix (2026-06-24):**
- [ ] **Revert** `py/qT/DrellYan.cpp:67` `_int_bT.set_max_iterations(20)` → `2` and rebuild
  (the bump was inert — it didn't change the integrator output — but don't leave it in the build).
- [ ] **Propagate the `[Nonperturbative] b0_over_bmax_nu=1` fix** to the canonical
  `com13_ct18z_btgrid_fineall` runcard (and v2/qx2 if ever regenerated) so a future regen
  can't silently re-inherit `0`. Or treat `…_b0nu1` as the canonical config going forward.
- [ ] **Reclaim ceph quota:** the source `…/zstuff/Z_COM13_CT18Z_N3p0LL_btgrid_fineall_b0nu1/`
  (~36 GB: raw shard + combined) is redundant now that the official /scratch grid is swapped.
  Also delete the old `…/Z_COM13_CT18Z_N3p0LL_btgrid_fineall_v2` (~109 GB) and `…_qx2` (~66 GB)
  study grids (conclusions logged). Old official `combined_btgrid.pkl.b0nu0_OLD_PREFIX` can be
  removed once the b0_nu=1 grid is confirmed in a fit.
- [ ] **Improve the 0.05 % Simpson-rebin floor IF wanted:** add interior nodes per experimental
  bin (5-node Simpson) — trades against grid size; fold into the grid-density study below.

**Pre-existing:**
- [ ] **Grid-density optimization** (NOW vs the corrected b0_nu=1 grid; hold b0_nu=1 fixed):
  coarsen bT (the memory/size driver — 2000 already converged, likely room to ~few hundred),
  Q (24 converged), checking the reconstruction stays within tolerance vs the fine b0_nu=1
  baseline (NOT vs franksvals — isolate grid effects). qT/Y are constrained by the 3-node
  Simpson-per-bin structure (`point_to_binned`). Subsumes the old "adaptive-node grid" idea.
- [ ] **Adaptive-node grid** (smart vs brute force): run SCETlib BINNED mode and
  dump the quadrature nodes it uses to hit `target_precision_rel`, to design a
  minimal non-uniform grid (cuts size + reconstruction memory). Needs a hook to
  extract SCETlib's internal points.
- [ ] **Built-in gen closure (datacard-only)**: `SCETlibNPParamModel.gen_closure()`
  comparing bt-grid `sigma_gen_central` to the datacard's `N_gen` (histmaker gen
  prediction) per gen bin — self-contained standing check (no external refs).
  Residual folds in recon accuracy + N_gen carrying the matched correction
  (MiNNLO_MC==MiNNLO_ref) + UL/units. Coarse gen grid → integrated only, won't
  resolve the fine wiggle. (Idea 2026-06-24.)
- [ ] Recover/skip the x→1 forbidden forward-Y cells (kinematic guard) only if
  |Y|>3.5 is ever wanted (it isn't, for the fit).

---

## 2026-06-29 — forVale_290626: points-mode reference cloned from btgrid_fineall settings

Built `prod/scetlib_run/forVale_290626/` to re-validate the **new** btgrid run
`/scratch/submit/cms/wmass/scetlib_np/Z_COM13_CT18Z_N3p0LL_btgrid_fineall/`
(the b0nu1-prefix regen, Jun 24–26) against the validated forVale_180626 point
reference. Three config files, laid out exactly like forVale_180626:
  * `base.conf`           — byte copy of btgrid_fineall/base.conf.
  * `runcard_npoff.ini`   — btgrid `inclusive_…_b0nu1.ini` transformed for POINTS
    mode: dropped `[bT_grid]`, added the full NP-off `[Nonperturbative]` baseline
    (all λ=0, tanh_2 both sides, `b0_over_bmax_nu=1.0`), repointed
    `variations_filename`. Grid_Q/Y/qT (24×165×141), EW, Integration (rel=1e-5)
    kept byte-identical to the btgrid card.
  * `variations_npoff.conf` — exact copy of forVale_180626's 7 vars
    ([0]NP-off [1]nominal [2]λ2ν↑ [3]λ2↑ [4]λ4↑ [5]δλ2↑ [6]all-4↑).

Settings diff (btgrid .ini vs forVale_180626 runcard) = ONLY the mode-defining
bits ([bT_grid] vs full [Nonperturbative]) + cosmetic `# GeV` inline comments;
all physics identical.

**Validation (single-point compute, bin 267493 = Q91/Y0/qT4):** new vs
forVale_180626 are **bit-identical** — var0(NP-off)=3.783616599934,
var1(nominal)=3.767169183522, rel.diff 0. NP-on/off=0.9957 (variations active).
⇒ btgrid_fineall settings reproduce the validated point reference; the full
old-vs-new diff is expected ≈0.

Gotchas found:
  * `--dry-run --point-spectrum` prints NOTHING to stdout — the bin list goes to
    the per-runcard **log file** (`runcard_npoff.log`, 558381 lines), not stdout.
    Only the C++ beamfunc init message leaks to stdout. Same for the run itself
    unless `--live` is passed. Not a config bug (forVale_180626 behaves identically).
  * `--fixed-var M` filenames zero-pad: `…_var_000_pointspec.pkl`, not `_var_0_`.

Run the full reference (558360 pts × 7 vars), from prod/scetlib_run/:
  ./wrap-scetlib-run-qT.sh /work/submit/lavezzo/alphaS/scetlib-cms-newnp-lambda4fix \
      <NCORES> 1 forVale_290626/runcard_npoff.ini --point-spectrum --live
  -> forVale_290626/runcard_npoff_pointspec.pkl

**Verified by file diff (2026-06-29):** old vs new btgrid *source* configs on ceph
(`…/zstuff/Z_COM13_CT18Z_N3p0LL_btgrid_fineall` vs `…_b0nu1`): base.conf IDENTICAL,
variations_btgrid.conf IDENTICAL, .ini = ONE pure addition of the `[Nonperturbative]`
block (`b0_over_bmax_nu = 1.`, `np_model_nu = tanh_2`) — no other edits. Since
`np_model_nu = tanh_2` == defaults.conf:85, the ONLY effective change is
`b0_over_bmax_nu = 1.`. forVale_180626 ALREADY carried `b0_over_bmax_nu = 1.0`, so
forVale_290626 is bit-identical to it (nothing new to import).

**Full run + old-vs-new diff DONE (2026-06-29):** launched from the HOST submit82
(NOT inside the container — the wrapper *starts* singularity, so a nested call from
a `Singularity>` shell fails `singularity: command not found`). 200 threads,
3,908,520 evals (558360 pts × 7 vars) in ~75 s (~6 ms/pt). Output
`forVale_290626/runcard_npoff_pointspec.pkl` (312,748,777 B). Diff vs
forVale_180626 (variation λ-metadata MATCH all 7):
  * var0 NP-off: BIT-IDENTICAL everywhere.
  * vars1-6 NP-on, physics region |Y|≤2.5 & σ>1e-6: max|rel| ≈ 2.6e-5 == SCETlib
    `target_precision_rel=1e-5` (independent adaptive-quadrature runs, not bit-repro
    for NP-on integrands). Worst |abs| 1.2e-5 at (91,0,0.75), both=0.9441.
  * The only ~1e-3 rel diffs are the |Y|=5 deep tail (σ~1e-9, at `target_precision_abs`
    floor) — physically irrelevant, outside acceptance.
  ⇒ new btgrid-derived points reference reproduces the validated forVale_180626 to
  integrator precision; b0_over_bmax_nu=1 import confirmed consistent.

## 2026-07-02 — re-confirmed while validating the NEW fit's σ_gen (see [[physical-lambda]])

Came at this fresh from the σ(αs) validation thread (studies/physical-lambda) — chasing a
"gen-level disagreement" — and re-derived what THIS study already resolved. Recording so it
doesn't happen again:

- **GRID-PATH LESSON (important):** `/ceph/submit/data/user/l/lavezzo/zstuff/Z_COM13_CT18Z_N3p0LL_btgrid_fineall/`
  is the **OLD BUGGY b0=0** source. The **FIXED b0=1 grid is the production one at
  `/scratch/submit/cms/wmass/scetlib_np/Z_COM13_CT18Z_N3p0LL_btgrid_fineall/`** (`combined_btgrid.pkl`,
  b0nu0 preserved as `.b0nu0_OLD_PREFIX`); fixed source also at `…/zstuff/…fineall_b0nu1/`. The code
  defaults (`export_spectrum.py`, `sigma_gen_at_lambda.py` BTGRID_DIR) already point at the /scratch
  fixed grid, and the production fit inherits it. **ALWAYS use /scratch/.../wmass; never zstuff/…fineall.**
- **Re-confirmation:** `sigma_gen_at_lambda --theory-corr <FranksVals CorrZ.pkl.lz4> --meta-from <260623 dc>
  --plot-axis ptVGen --absy-edges 0,2.5`, matched σ_gen vs official SCETlib+DYTurbo, var=pdf0:
  buggy grid → lowest-ptV bin 0.9925 (**−0.75%** wiggle), min 0.9925; **fixed grid → 0.9995 (−0.05%),
  min 0.9981, range 0.9981–0.9995** (flat Simpson-rebin floor only). Σmodel/Σcorr=0.99933 both.
  ⇒ reproduces the 2026-06-24 resolution (wiggle 1.011%→0.006%); the −0.05% floor is the 3-node rebin
  (5-node erases it). Resum-only precision plots (buggy grid, for the record):
  `~/public_html/alphaS/260702_resum_precision/`; fixed-grid closure `official_closure_FIXEDgrid_absy2p5.png` there.
- **TIMING RED FLAG (corrected):** `_default_btgrid_dir()` → `/scratch/.../wmass/…fineall/` (the fit's
  default; the NEW fit passed no `btgrid_dir`). combined_btgrid.pkl there is **b0=1 dated Jun 24 20:50**,
  but the **b0=1 fix was swapped in at 20:50 — AFTER the NEW 260623 fit ran (Jun 24 08:39 pass-1 →
  13:56 cov)**. At fit time the combined was the Jun-9 **b0=0 buggy** grid (now `.b0nu0_OLD_PREFIX`).
  ⇒ **the production σ(αs)=0.442 fit was computed on the BUGGY b0=0 grid** (low-qT wiggle present,
  laundered to reco); uses **3-node** (not 5-node). A fit re-run TODAY would pick up the fixed grid.
- **OPEN / TODO:** re-run the 260623 λ4_ν-frozen fit with the current fixed b0=1 grid and compare
  σ(αs) + central to 0.442 — to check the b0_nu bug's (likely small, laundered) impact on the number.
  Do NOT assume it's negligible without this check. (5-node remains an optional prediction-fidelity
  nicety, separate from the b0=1 correctness fix.)

---

## 2026-07-15 — triangulation extended to the POSTFIT tune (points file, tanh_6, λ2<0)

First check of the reconstruction at the **real-data postfit λ** (not λ_central). The fit
`260702_2D_l6nu0p01_l60p01_nowall` (datacard `260701_Z_2D/…_realdata/ZMassDilepton.hdf5`)
lands on the awkward tune **tanh_6: λ2=−0.498, δλ2=−0.024, λ4=−0.035, λ6=0.01; λ2ν=0.320,
λ4ν=0.019, λ6ν=0.01; λ∞=1, λ∞ν=2** — verified to match the SCETlib run's `config[Nonperturbative]`
exactly (same parametrization, no conversion). Areimers ran a direct SCETlib **points** run at
that tune: `…_postfitLambda60p01_nowall_points/…_combined.pkl` (`calculation_piece=sing`, N3LL,
b0_over_bmax_nu=1 — matches the production bt-grid).

**Tool (committed to this study):** `compare_postfit_sigma_gen.py`. Reuses `SigmaGenModel` (the
`sigma_gen_at_lambda` core, `include_nonsingular=False`) evaluated at the postfit λ read from
`--fitresult` with the fit's tanh_6 numerator forms, vs the SCETlib points file projected to the
fit gen grid (ptVGen 21 bins [0,44]+overflow, |Y|≤2.5). Plots via `make_projection_plot`. Runs
CPU in the container. Outputs: `~/public_html/alphaS/260702_2D_l6nu0p01_l60p01_nowall/`
(`…_ptZ.png` absolute, `…_ptZ_shape.png` shape-normalized).

**KEY GOTCHA — the "points" file is DIFFERENTIAL, not bin-integrated.** Unlike the "fine"
*spectrum* correction-input pkl (raw sum over |Y|≤2.5,Q∈[60,120] ≈ 1347 pb = physical σ, which
`_merge_matrix`/`resum_from_correction` plain-sums), this points file stores d³σ/(dQ dY dqT)
sampled on a fine grid (raw sum ≈ 168k). So it must be width-INTEGRATED (∫v·ΔQ·ΔY·ΔqT), with Q
clipped to [60,120] and |Y| to ≤2.5, and qT folded into ptVGen by center-membership (0.1-GeV
source bins). `read_scetlib_hist` returns it as-is (no width weighting); `makeAbsHist(…,'Y')`
also FAILS here because the Y grid is centered on 0 (0 is a sample, edges ±0.05) → sum signed-Y
|center|≤2.5 instead (grid is Y-symmetric).

**RESULT.**
- **Shape (robust):** shape-normalized, the param model reproduces the SCETlib N3LL resum qT
  spectrum to **~0.5–1.3 % through the resummation peak (qT ≲ 30 GeV)**; mean-abs dev over all
  21 ptVGen bins = 2.0 %. Outliers: the lowest-qT **[0,1] GeV bin is +10 %** (model high), and
  the coarse high-qT bins (ptVGen ≳ 30, incl. the [37,44]/overflow) are ±3–5 % (partly real
  high-qT resum drift, partly the center-membership rebin where the SCETlib qT grid coarsens to
  0.4–1 GeV). The (model−corr) panel tracks the spectrum → the residual is multiplicative, not
  an additive pedestal.
- **Absolute normalization: NOT trustworthy from this file.** Σmodel/Σscetlib = 0.948 (model
  ~5 % low), BUT the points file's **Q grid is too coarse to integrate the Breit-Wigner**:
  dσ/dQ near the peak = (88→48, 89.75→186, **91→339**, 92.25→236, 94→55), and integrating it
  gives 1429 (midpoint) / 1460 (cubic-spline) / 1501 (np.trapz) — a **±5 % ambiguity by itself**.
  The qT-integral, by contrast, is method-insensitive (0.9999). So the ~5–7 % offset is dominated
  by MY Q-integration of the coarse-Q differential file, not a reconstruction failure. The
  trustworthy absolute check remains the λ_central "fine"-file triangulation (0.2 %, see the 2026-07-02
  entry). To validate the absolute norm at the postfit tune one needs a bin-integrated *spectrum*
  file (or a much finer Q grid), not this points file.

**Physics read (integrated view).** At the postfit tune — which the point-mode diagnostics call
"broken" (low-qT ringing, F_eff blow-up at |Y|>2.65; see [[physical-lambda]] / the fitpoint-breakdown
note) — the integrated comparison tracks a direct SCETlib run to ~1 % in the qT SHAPE inside the fit
acceptance (|Y|≤2.5, qT≲30), with a ~5 % absolute offset that is NOT interpretable (Q-integration
ambiguity). But the integrated view is the wrong tool here — see the point-mode resolution below.

### RESOLVED via POINT MODE (same day) — the reconstruction is essentially PERFECT at the postfit tune

The right way to answer "does the reconstruction hold at the postfit tune?" is to **remove all
integration** — exactly the btgrid-precision experiment-B logic (`point_mode_compare.py`). Tool:
`compare_postfit_sigma_dense.py` (this dir). It reconstructs the param model's native
`sigma_dense` = d³σ/(dQ dY dqT) at each bt-grid node BEFORE the Q-integral/|Y|-fold/qT-rebin
(replicating `sigma_YqT_native` up to `sparse_to_dense_tf`) at the postfit λ, and compares it to the
SCETlib points differential at the **(Q,Y,qT) nodes the two grids share EXACTLY** — no integration,
no interpolation. The grids overlap generously: **14 shared Q (incl. the peak Q=91), 119 Y, 66 qT**.

**Result (|Y|≤2.5, per-node param/SCETlib):**
- **qT ≲ 16 GeV: ratio = 0.9996–1.0001, std ~1e-4 — agreement to ≈0.04 %.** qT≈24 → 0.998 (0.2 %).
- Overall **median = 0.99975** (−0.025 %); the mean/std are meaningless (contaminated by qT≳48 nodes
  where resum-only σ→0 and the ratio is 0/0 noise — physically irrelevant, resum-only is not a
  prediction there).
- Plot `sigma_dense_point_compare.png` (σ vs qT at Q=91,Y=0 overlays exactly; ratio flat at 1.000).
- **Forward-Y spot check (Y=2, Q=91):** qT≤16 GeV mean 0.99991, range [0.99933, 1.00009] — i.e.
  ~0.07 %, same as Y=0; wider spread only for qT 16–40 (resum-only σ falling). So the ~0.04 %
  agreement is not special to Y=0, it holds across the acceptance. Plot `sigma_dense_point_compare_Y2.png`.

NB on "no integration" (what the point check actually does): the bt-grid reconstruction still does
the **bₜ (Hankel) integral** ∫dbₜ Iₚₑᵣₜ(bₜ)·F_eff(bₜ;λ)·J₀(bₜ qT) — that IS the resummation and is
exactly where the NP form factors enter; it is unavoidable and is the thing being validated. What is
skipped is the OUTER Q / qT / |Y| integration+rebin. SCETlib's node value likewise already contains
its own internal bₜ integral. So the check = "our bₜ-integral+NP" vs "SCETlib's bₜ-integral+NP" at
the same (Q,Y,qT) node and same λ — nothing else in between.

**⇒ Conclusion. The ~5 % "offset" in the integrated comparison was ENTIRELY the coarse-Q points
file's Breit-Wigner Q-integration artifact — NOT a reconstruction failure. Point-by-point, the
bt-grid + on-the-fly NP (tanh_6, λ2<0, δλ2<0, λ6/λ6ν=0.01) reproduces the direct SCETlib run to
~0.04 % through the resummation region at the fitted tune.** The λ_central triangulation (0.2 %,
2026-07-02) and this postfit point-mode check (0.04 %) now BOTH confirm the reconstruction; the NP
form (tanh_6), δλ2 and b\* conventions, and the on-the-fly F_eff/γ_ν all match SCETlib exactly even
at the awkward postfit tune. LESSON: to compare against a SCETlib **points** file, compare at shared
nodes (point mode) — never Q-integrate it (its Q grid can't resolve the BW; ±5 %).
