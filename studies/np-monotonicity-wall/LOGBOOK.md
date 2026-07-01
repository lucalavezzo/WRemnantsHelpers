---
id: np-monotonicity-wall
title: NP-monotonicity-wall regularizer and prior-inflation comparison
status: running
question: How much do we need to inflate the NP priors (or drop them entirely) before the data is no longer hitting the prior, and what does that imply for σ(α_S)?
owner: lavezzo
created: 2026-05-13
updated: 2026-05-15
preferred_run: null
tags: [np, alphaS, priors, regularizer]
parent: null
investigates_regions: []
investigates_methods: []
investigates_fits: []
investigates_background_estimates: []
investigates_uncertainties: []
next_action: Decide how to report σ(α_S) given that wide-prior inflation gives high ptll p-values but unphysical λ_2 ≪ 0 in the fit.
current_hypotheses:
  - V2 inflation is insufficient — data still wants larger CS λ_2 / λ_4 pulls.
success_criteria:
  - Produce a single-page PDF comparison table at $MY_PLOT_DIR/260513_np_compare/.
blockers: []
pending_signoffs: []
---

## Status

2026-05-14: two bugs found and fixed in the wall infrastructure. (1) `np_monotonicity.py`'s regularizer mapped θ → physical NP value using the bare PARAM_MAP step (kfactor = 1), ignoring per-config `--scaleParams`. On inflated-prior configs the wall never fired (penalty was 0 at the postfit; the runlog's earlier "regularizer changes nothing at τ=5" was the symptom). Fix: `NPMonotonicityMapping.parse_args` now accepts positional `<param>=<kfactor>` args, plumbed through `NPMonotonicityWall._physical_value` as a per-nuisance kfactor on `(Up−nom)` and `(nom−Down)`. Verified: Inflate2x_reg5 LR scan with kfactors lambda_2=5.24, lambda_4=2.24, Lambda_2=Δ_Lambda_2=Lambda_4=2.0 now pushes λ_2 from −0.20 (no reg) to −0.0004 (wall pinning) with `lpenalty ≈ 0.003` chi2 units. Inflate3x_reg5 / 5x_reg5 LR scans queued in the same chain.

(2) `build_compare_table.py::_sigma_from_scan` was reading `hist.axes[0].edges` (bin indices 0,1,…,n) on the rabbit `nll_scan_<param>` hist, which has axis type `StrCategory` whose categories are the actual θ values as strings. σ-from-scan was a factor `(n-1)/(2·scanRange)` ≈ 4× too large. The "Hessian underestimates σ by 8×" claim in the prior runlog entry was the direct artifact. With the fix (cast `np.array(list(ax))` to float, so the labels carry θ), σ_LR(α_S) for unconstrained τ=3 = 1.053 × 10⁻³, matching σ_Hess = 1.054 × 10⁻³ to <0.1%. Rabbit's own `rabbit_plot_likelihood_scan.py` confirms visually: black scan curve overlays red Hessian parabola exactly. The "NP–α_S degenerate direction blows up the scan" narrative is retracted.

Table now drops the LR-scan σ column (it agrees with Hessian, side-by-side display was clutter); for future fits we'll add `--contourScan pdfAlphaS --contourLevels 1` so σ is stored deterministically rather than interpolated. Inflate2x_reg5 (kfac) row landed in the table. All four "missing sat-p ptll" rows are missing only because their fit command omitted `--computeSaturatedProjectionTests` — none failed. Wall plotted in 1D at `$MY_PLOT_DIR/260514_wall_1d/wall_penalty_1d.png` (constraint function f and penalty `Σ max(0,−f)²`); inflate×5 CS-kernel comparison vs AN at `$MY_PLOT_DIR/260514_np_kernel_inflate5x/` shows γ̃^NP positive over b_T ∈ (0, 2.7) GeV⁻¹ — clearly unphysical, the wall would prevent it.

All open tasks resolved as of 2026-05-15 13:30. Headline 4D table at `$MY_PLOT_DIR/260513_np_compare/np_compare.pdf` now includes 28+ rows spanning {nominal, inflatedV2, inflate2x/3x/5x, tight50, frozenNP, unconstrained} × {no fakelumi, +fakelumi} × {no wall, +wall} + a fakelumi-pull % column (regenerator: `render_compare_table.sh`). 1D ptll-only / yll-only diagnostic tables at `$MY_PLOT_DIR/260514_np_compare_1d/`. CS-kernel and TMD plots at `$MY_PLOT_DIR/260514_np_kernels/`. Correlation matrices at `$MY_PLOT_DIR/260515_corr_matrices/`. Wall penalty 1D plot at `260514_wall_1d/`.

**Headline conclusion**: the AN's α_S precision (σ ≈ 1×10⁻³) is stable across all NP-prior choices when NPs are floating. The wall fixes CS-kernel physicality cleanly without other side effects. The yield-vs-shape compromise on α_S is irreducible at ~2σ — neither tightening NP priors (tight50) nor widening them (inflate5x) reduces the fakelumi-induced shift; only fully freezing NPs (frozenNP) reduces it, and that ruins the fit. **Suggested AN central**: nominal + wall (τ=5). Quote the fakelumi-on result as a "shape-only" cross-check showing ~+2 × 10⁻³ shift.

**Next:** writeup. Pending user/sub-detector review of which framing to adopt.

## Guiding Question

Compare postfit NP physical values and σ(α_S) across nominal-AN-priors, V2-inflated, and unconstrained-LR-scan fits to determine how much prior inflation is needed to match data preference.

## Hypotheses

- V2 inflation (CS×1.5, TMD Λ_4×2.5) is insufficient: postfit pulls on CS λ_2/λ_4 are still O(1σ) on the inflated prior, indicating the data wants a wider prior. [active]

## Ideas / Methods Explored

- Use np_param_map.json linearization to convert rabbit θ pulls to physical NP values.
- Use the existing build_tables.py (260430_debug_1d_vs_4d) as the LaTeX-table model.

## Dead-Ends

- (None yet.)

## Findings

- 2026-05-13 — Unconstrained fit pulls: CS λ_2 θ=−3.66, CS λ_4 θ=+3.28, TMD Λ_4 θ=−3.35 — far beyond V2 inflation widths. (Caveat: these came from `NPUnconstrained/data_lrscan/fitresults.hdf5`; user clarified the canonical "today's three configs" are `NPCS100pct/data`, `NPCS100pctV2`, and `NPUnconstrained/data_lrscan`. Earlier comparison incorrectly used `NPUninflated` and `NPInflatedV2` instead — needs to be redone with the right files.)
- 2026-05-13 — Initial `build_compare_table.py` cell for inflatedV2 TMD Λ_4 was off by 2.5× because the script didn't apply the `--scaleParams chargeVgenNP0scetlibNPZlambda4=2.5` kfactor; added per-config kfactor overrides (`KFACTOR_OVERRIDES` dict) to fix.
- 2026-05-13 — Correct file mapping verified via `print_command`: NPCS100pct scaleParams = `λ_2=2.62 λ_4=1.12 λ_∞=3.33`; NPCS100pctV2 = same + `λ_2→4.32` and `TMD Λ_4=1.55`; NPUnconstrained = no scaleParams, `noConstrainParams 'scetlibNPgamma|scetlibNPZlambda|scetlibNPZdelta_lambda'`. Comparison PDF at `$MY_PLOT_DIR/260513_np_compare/np_compare.pdf` regenerated with correct files.
- 2026-05-13 — Hessian σ(α_S) for unconstrained-prior fits underestimates by ~8× (Hessian = 1.05 × 10⁻³ vs LR-scan = 8.00 × 10⁻³). Cause: regularizer hinge + NP–α_S degenerate direction makes the local curvature unrepresentative. Decision: in the comparison table, the unconstrained rows show **scan σ** with an asterisk; constrained rows keep Hessian σ.
- 2026-05-13 — Inflation chain results (×2, ×3, ×5 of nominal kfactors, λ_∞ left alone): ptll saturated p-value goes 0.87% → 3.41% → 8.68% → **20.66%** as priors widen. But λ_2 (CS) gets dragged further into unphysical territory: −0.06 → −0.20 → −0.34 → **−0.54 GeV²**. Conclusion: wide Gaussian priors centered at AN nominal do NOT anchor the fit in the physical region — they just let the data pull farther without prior penalty. **The colleague's "10× CS + 2× TMD" with p~10% likely also had λ_2 negative; they may not have noticed.**
- 2026-05-13 — At τ=5, adding the regularizer on top of inflated-Gaussian-prior configs **changes nothing** (λ_2 = −0.1977 with or without reg, identical to 4 digits). Only effect: regularizer's `--freezeParameters λ_∞` pins λ_∞ at 1.685. The hinge penalty is ~0.04 chi2 units at the postfit, ×τ multiplier ~5 → still <<1 chi2, easily overwhelmed by data preference. Implication: at the inflated-prior level the regularizer is not doing useful work; it only matters under unconstrained priors where the data preference is similar but no prior anchor exists. **Superseded 2026-05-14**: the regularizer wasn't "overwhelmed" — it never saw the right λ_2 because `_physical_value` ignored `--scaleParams`. See below.
- 2026-05-14 — **kfactor-aware regularizer fix.** `_physical_value` in `np_monotonicity.py` mapped θ → physical via `nominal + θ·(Up−nominal)` with `Up`/`Down` taken straight from PARAM_MAP, i.e. k = 1, ignoring the actual `--scaleParams` kfactor used at workspace setup. Result: at the inflated-prior postfit (θ ≈ −1.5, k = 5–13), the fit's λ_2 ≈ −0.2 to −0.5, but the regularizer's view of λ_2 was `0.087 − 1.5·0.033 ≈ +0.04` — positive, no wall violation, penalty = 0. The unconstrained config (k = 1) was unaffected, which is why the wall appeared to work there but not on inflated configs. Fix: `NPMonotonicityMapping.parse_args` now accepts positional `<param>=<kfactor>` tokens (allowed names: lambda_2, lambda_4, Lambda_2, Delta_Lambda_2, Lambda_4), threaded through `NPMonotonicityWall._physical_value` to multiply `(Up−nominal)` and `(nominal−Down)` by k. (evidence: `Inflate2x_reg5/data_lrscan/fitresults.hdf5` postfit λ_2 = −0.0004 ± 0.0048 with kfactors plumbed, vs −0.1976 ± 0.1121 in the previous buggy run.)
- 2026-05-14 — **σ-from-LR-scan extractor bug** (and retraction of the 2026-05-13 "8× discrepancy" claim). `build_compare_table.py::_sigma_from_scan` was reading `hist.axes[0].edges` on the rabbit `nll_scan_<param>` hist, but rabbit stores the scan on a `hist.axis.StrCategory` whose categories are `str(θ_value)` — so the edges are bin indices, not θ. σ-from-scan was inflated by a factor ≈ `(n_points−1)/(2·scanRange)` (= 4 for our scans), giving 7.99×10⁻³ where the true value is 2.00×10⁻³. Combined with the existing `×2` to convert to AN σ units, the table showed σ ≈ 8×10⁻³ for unconstrained rows. **The Hessian σ and LR-scan σ actually agree to <0.1%** (unconstrained τ=3: σ_Hess = 1.054, σ_LR = 1.053 × 10⁻³). Confirmed visually with `rabbit_plot_likelihood_scan.py` at `$MY_PLOT_DIR/260514_lrscans/nll_scan_pdfAlphaS_unconstrained_tau3.png` — scan curve overlays Hessian parabola exactly. The 2026-05-13 "NP–α_S degenerate direction makes the local curvature unrepresentative" claim is **retracted**.
- 2026-05-14 — Wall is a squared-hinge (ReLU²) per constraint: penalty = `Σ_i max(0, −f_i(θ))²`, multiplied by `exp(2τ)` upstream (`fitter.py:2491`). Five constraints: CS λ_2 ≥ 0, CS λ_4 ≥ −√(3·λ_2·λ_6), TMD L_2(y) ≥ 0 at y ∈ {0, y_max}, TMD c_1(y) ≥ −√(20·Λ_6·L_2(y)) at y ∈ {0, y_max}. 1D scan with others frozen at AN central in `$MY_PLOT_DIR/260514_wall_1d/wall_penalty_1d.png` — only the CS λ_2 ≥ 0 wall is binding for all real-data postfits seen so far; TMD Λ_4 wall is just barely contacted by unconstrained τ=3.
- 2026-05-14 — Inflate×5 (no reg) postfit lands in clearly unphysical CS-kernel territory: γ̃^NP(b_T) is positive over b_T ∈ (0, 2.7) GeV⁻¹, peaking at +0.47, before crossing zero to the correct asymptote. Driven by A(b_T) going negative (dip to ≈ −0.6 around b_T ≈ 2). Violates both criterion (a) sign-preservation and (b) monotonicity. TMD side (B, f^NP) remains well-behaved at all y. Plots: `$MY_PLOT_DIR/260514_np_kernel_inflate5x/`. Implication: any inflation that produces λ_2 < 0 is buying p-value with a wrong-sign CS kernel. The kfactor-aware wall now prevents this (Inflate2x_reg5 result above).
- 2026-05-14 — Sat-p (ptll) missing rows in the comparison table all come from the fit command missing `--computeSaturatedProjectionTests`, not from Cholesky / convergence failures. Affected: nominal_fakelumi, inflatedV2_fakelumi, inflate2x_reg5 (data_lrscan), unconstrained τ=3 (data_lrscan), inflate3x/5x_reg5 (when they land). Need quick satp re-runs per config; no impacts needed.
- 2026-05-14 — `NPUnconstrained_fakelumi/fitresults.hdf5` (τ=3, no postfix subdir) is incomplete: only `meta` key present, no `results_asimov`. Original fit aborted partway; needs full re-run if that row is wanted.
- 2026-05-14 — Wall has **6** constraints, not 5 as initially stated: CS λ_2 ≥ 0, CS λ_4 floor, TMD L_2(y) ≥ 0 at y∈{0, y_max}, TMD c_1(y) floor at y∈{0, y_max} (positivity and monotonicity are each evaluated at both y values on the TMD side). Final 1D scan plot at `$MY_PLOT_DIR/260514_wall_1d/wall_penalty_1d.png` shows just the penalty `P = Σ max(0, −f_i)²` per parameter scan; the constraint-function `f_i` curves were dropped on user request after I explained the formulas in chat. Explicit formulas now in the runlog Status; refer to them rather than re-deriving.
- 2026-05-14 — Each panel of `wall_penalty_1d.png` now carries an in-axes text box with the constraint expression(s) that vary with the scanned parameter (e.g. λ_4 ≥ −√(3 λ_2 λ_6) on the λ_4 panel). Readers don't need to flip to the runlog to know which wall they're looking at.
- 2026-05-14 — **Doing a "1D ptll-only" or "yll-only" fit requires rebuilding the workspace with `setupRabbit --fitvar <obs>`.** I initially tried `rabbit_fit.py ... -m Project ch0 ptll` thinking that restricted the fit, but `-m` is the *projection / mapping* hook for downstream chi² / saved-hist outputs, NOT a fit-observable selector. With a 4D-built workspace, rabbit_fit always fits the 4D distribution regardless of `-m`. The fix is to rerun `setupRabbit.py` with `--fitvar ptll` (or `yll`), which produces a workspace whose data/predictions are the 1D ptll (or yll) projection. Then rabbit_fit on that workspace is the real 1D fit. Caught + killed an in-flight run that had this mistake.
- 2026-05-14 — Companion gotcha for the 1D rebuild: `--axlim` only accepts fit variables. For yll-only the `ptll [0, 44 GeV]` window must be applied via `--presel ptll 0j 44j` instead of `--axlim ptll 0j 44j`. (`--axlim` restricts the binning of a fit axis; `--presel` restricts a non-fit axis before projection.) Wrapper now picks the right flag based on `--fitvar`.
- 2026-05-14 — **First 1D-ptll-only diagnostic landed.** NPCS100pct (AN priors) fit only against the ptll projection (rebuilt workspace via `setupRabbit --fitvar ptll`): saturated chi²/ndf = 52.34/38 → **p = 6.07 %**. The same dataset projected from the 4D fit gave only 0.87 % — a 7× improvement. Strong evidence that the 4D fit is sacrificing ptll fit quality to satisfy yll/cosθ*/φ*: ptll *alone* is fit well by NPs sitting within the AN priors, but the 4D fit pulls NPs to a compromise that hurts ptll. Source: `$BASE/ZMassDilepton_ptll_NPCS100pct_ptllonly/data/fitresults.hdf5`.
- 2026-05-14 — **Full 1D ptll/yll diagnostic complete (6 fits).** Three configs (NPCS100pct AN priors, NPUnconstrained τ=5, Inflate5x_reg5 τ=5) × {ptll, yll}. Headline numbers:

  *ptll-only*: NPCS100pct sat-p 6.07 %, λ_2 = −0.039; Unconstrained 4.85 %, λ_2 = −0.0005; Inflate5x_reg5 **15.02 %**, λ_2 = −0.0004. σ(α_S) ≈ 1.34–1.43 × 10⁻³.

  *yll-only*: NPCS100pct sat-p 11.47 %, λ_2 = +0.093; Unconstrained **3.28 %** with λ_4 = +12.5, Λ_4 = −20.3 (runaway, yll has too little NP info); Inflate5x_reg5 12.61 %, λ_2 = +0.21. σ(α_S) ≈ 4.5 × 10⁻³ — too weak to pin α_S.

  Diagnostic conclusion: ptll and yll **do prefer different NP values inside the physical region** (ptll wants λ_2 ≈ −0.04, yll wants λ_2 ≈ +0.09 at AN priors — opposite halves of the prior). The 4D-fit's projected-ptll p-value problem is a real observable-vs-observable tension, not just tight priors. Most of α_S sensitivity is in ptll; yll-alone is too weak.

  **Inflate5x_reg5 ptll-only gives the cleanest single answer: sat-p 15 %, λ_2 = 0 (wall on), σ(α_S) = 1.40 × 10⁻³.** Wall keeps the CS kernel physical, p-value is good, σ is the same as nominal Hessian to <2 %. Likely candidate for the AN's central α_S quote, with the 4D fit's projected-ptll p-value reported as the model-tension number.

  Outputs: `$BASE/ZMassDilepton_{ptll,yll}_{NPCS100pct,NPUnconstrained,Inflate5x_reg5}_{ptll,yll}only/data/fitresults.hdf5`.
- 2026-05-15 — **fakelumi diagnostic chain** (motivation: how shape-driven is the α_S extraction? fakelumi releases the absolute normalization constraint; a small Δα_S means α_S is determined from shape, a large one means it leans on yield). Floating-NP fits show **~+2 × 10⁻³ shift (~2σ) under fakelumi κ=1.1** essentially independent of NP prior choice:
    - nominal (AN-100% priors): Δα_S(fakelumi) = +2.30 × 10⁻³
    - inflatedV2: +2.15
    - inflate5x (no wall): +1.33 — λ_2 also moves, so NPs partially absorb
    - inflate5x_reg5 (wall on): +2.09
    - tight50_reg (50% priors + wall, new 2026-05-15): +2.07
  Yet **frozenNP** (all 6 NPs pinned at AN central, only α_S floating) shifts by only **+0.59 × 10⁻³ (~0.7σ)** — confirming that the yield-shape compromise is mediated through NP freedom. The fact that **tight50 shows essentially the same shift as nominal AN-100%** despite halving the prior widths means the knee in "fakelumi-sensitivity vs prior width" is far closer to "frozen" than to "tight" — i.e., the NPs need to be effectively pinned to make α_S shape-driven. Outputs: `data_reg_satp/` and `data_frozenNP_satp/` subdirs of NPCS100pct, NPCS100pct_fakelumi, NPCS100pctV2, NPCS100pctV2_fakelumi, NPCS50pct, NPCS50pct_fakelumi.
- 2026-05-15 — **Correlation-matrix diagnostic** (`$MY_PLOT_DIR/260515_corr_matrices/`, via `rabbit_plot_cov.py --correlation`). For nominal+reg+fakelumi: α_S↔fakelumi = −0.65, α_S↔Λ_2 = −0.62, α_S↔Λ_4 = +0.61 — three large correlations forming a tight (α_S, Λ_2, Λ_4, fakelumi) eigenmode. The α_S↔Λ correlations are *similarly strong* with and without fakelumi (fakelumi doesn't "steal" the shape correlation, it adds a parallel one). CS γ-family is decoupled (|ρ| ≤ 0.13) once the wall is on. Reproducer: `agents/studies/260511_np_monotonicity_wall/scripts/plot_corr_matrix.sh` (uses `plot_config.py` for display names; `--customFigureWidth 11 --scaleTextSize 0.5 --title "" --subtitle ""` to avoid the Rabbit corner label).
- 2026-05-15 — Tight50 (50%-of-AN prior widths) deteriorates ptll sat-p to **0.11 %** (vs nominal 0.87 %) and shifts α_S central by +1.11 × 10⁻³ relative to nominal *even without fakelumi*. The data wants more NP shape freedom than the AN-100% priors give it, so halving the priors is a worse fit and pushes α_S further from the data preference. Combined with the unchanged fakelumi shift, the conclusion is **α_S sensitivity to NP-shape modeling × yield-prior interplay is irreducibly ≈2σ** in this analysis — you cannot make it small without making the data fit terrible. Suggested AN treatment: quote floating-NP α_S as central, fakelumi-on as a "shape-only" cross-check (Δα_S ≈ +2σ), and accept that ≈2σ of effective α_S uncertainty arises from the NP-yield interplay.
- 2026-05-14 — **inflate{2,3,5}x_reg5 postfits all converge to the same minimum once the wall bites.** With kfactor-aware regularizer at τ=5: λ_2 pinned to (−0.0004, −0.0005, −0.0007) for inflate2x/3x/5x respectively; TMD Λ_2≈+0.28, Λ_4≈−0.085 in all three; σ(α_S) = (1.032, 0.994, 1.013) × 10⁻³ — agreeing to <4 %. Same minimum is reached by NPUnconstrained at τ=5 (σ=1.030, λ_2=−0.0007). Interpretation: once λ_2 is constrained to the wall, the data has selected its preferred NP configuration, and the prior width on the other nuisances is no longer load-bearing — they're pulled to the same data-preferred location. Implies the V3 inflation question reduces to: pick any inflation factor ≥ 2× and turn on the wall, the result is the same.
- 2026-05-14 — **ptll-projection p-value with wall on is ~2 %** (inflate2x_reg5: 1.81 %, 3x: 2.37 %, 5x: 2.65 %; unconstrained τ=5: 2.06 %), recovering ~2× over the AN-prior nominal (0.87 %) but still markedly worse than the loosen-without-wall 5x case (20.66 %). The remaining ~2 % tension *is* the model-can't-fit-data signal in the physical region; loosen-without-wall buys p-value by going into the unphysical CS-kernel regime (λ_2 < 0). Net: the regularized fit yields a defensible α_S (σ ≈ 1.0×10⁻³, identical to AN-prior Hessian) but with ptll-projection p ~2 %, which is the honest goodness-of-fit at the boundary of the physical region.

## Open Questions

- What is the right V3 inflation: ~4× on CS λ_2, ~4× on CS λ_4, ~3.5× on TMD Λ_4?
- Inflation widens priors but doesn't enforce physicality. To force λ_2 ≥ 0, do we need a *harder* wall (criterion (a) sign-preservation, or a barrier instead of hinge), or do we accept that the SCETlib NP parametrization can't fit the data without going negative and report a model-level systematic from the unconstrained-vs-constrained α_S spread?
- **ptll/yll tension diagnosis** — projected-ptll p-value from the 4D nominal fit is 0.87% while the global 4D saturated p is fine (~60%) and a 1D ptll fit alone is reasonable. The 4D fit appears to sacrifice ptll fit quality to satisfy yll/cosθ*/φ*. Plan: run 1D ptll-only and 1D yll-only fits (task #7) and compare their postfit NP values. If they prefer significantly different NP nuisances, the tension is observable-vs-observable (parametrisation too rigid / mis-modelled angular distributions). If they agree, the data really does want NPs that are mutually incompatible with the AN priors. Evidence already in hand: unconstrained τ=3 ptll-projection p = 2.93% (3× better than the 0.87% nominal), supporting "AN priors hold NPs away from ptll-preferred values".

## Decisions

- 2026-05-14 — Satp re-runs should compute the saturated projection test for **ptll only** (`-m Project ch0 ptll` + `--computeSaturatedProjectionTests`, no other mappings, no impacts). Reason: the only sat-p we care about for the comparison table is the 1D ptll projection; computing it for all 5 projections took ~30 min/fit and we don't use the others. Reduces per-fit wall time to ≲5 min. Affects upcoming runs for unconstrained τ=3, nominal_fakelumi, inflatedV2_fakelumi, inflate{2,3,5}x_reg5.

## Next Action

Build the side-by-side comparison PDF; review with user; decide on V3 inflation factors.
