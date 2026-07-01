---
id: franks-vals-fit
title: Fit FranksVals histmaker with asymmetric NP nuisances
status: running
question: Does the FranksVals NP-variation set (np_model tanh_2 with lambda_2=0.4 +0.6/-0.4, lambda_4=0.4 +0.6/-0.4; np_model_nu tanh_2 with lambda_2_nu=0.15 +/- 0.1) give a sensible alphaS fit when the NP nuisances are treated asymmetrically (no symmetrization)?
owner: lavezzo
created: 2026-05-19
updated: 2026-05-20
preferred_run: 260519_franks_vals_asym_realdata
tags: [franks-vals, NP, asymmetric, quadratic, wall, fakelumi, alphaS, scetlib_dyturbo, validation]
parent: null
investigates_regions: []
investigates_methods: []
investigates_fits: []
investigates_background_estimates: []
investigates_uncertainties: [uncertainty:scetlibNP]
next_action: Decide how to report sigma(alphaS) and the systematic uncertainty given that (a) Lambda_4 always wants to be very negative, (b) walling it on the physical side surfaces a 6sigma fakelumi tension, and (c) the underlying SCETlib NP form (tanh_6cs OR tanh_2) likely cannot reach the data-preferred shape. Concrete options to discuss with colleagues: extend the parametrization or generate explicit SCETlib templates at the data-preferred Lambda_4 to validate the linearization.
current_hypotheses:
  - Frank's wider TMD-BC variation (lambda_2 0.0 -- 1.0, lambda_4 0.0 -- 1.0 vs the prior 0.0 -- 0.5 and 0.01 -- 0.12) gives the fit enough room to absorb shape; pulls Lambda_4 to a (linear-extrapolated) ~3x past the Down template. [confirmed]
  - With only lambda_2_nu varying on the CS gamma side, the fit's NP-vs-alphaS degeneracy reduces and sigma(alphaS) tightens. [ruled-out] -- sigma actually WIDENS under asym/quadratic (0.80 -> 1.06 / 1.13 * 10^-3) compared to avg-sym (0.80); avg-sym was hiding ~30% of the NP shape uncertainty by collapsing the asymmetric direction.
  - The "Lambda_4 ~ -3 sigma in both AN and FranksVals fits" is a deep numerical coincidence pointing to a postfit-display bug. [ruled-out] -- it reflects the Gaussian-prior penalty vs data preference balance point (~4.5 NLL units = 3 sigma cost) AND the fact that both NP parametrizations drive ptll-shape in the same direction; not a bug, but a hint that the data wants a shape neither parametrization captures cleanly.
  - The wall regularizer cures the unphysical-Lambda_4 problem without side effects. [ruled-out] -- adding the wall just relocates the data preference into fakelumi (6 sigma yield-vs-shape tension in FranksVals asym_reg + fakelumi).
success_criteria:
  - rabbit_fit.py completes without "could not find variation" errors.
  - prefit and postfit projections look physical; NP pulls within +/- a few sigma.
  - sigma(alphaS) recorded in the runlog.
blockers: []
pending_signoffs: []
---

## Status

2026-05-20 (end-of-day rollup). Fourteen fits landed across two
histmaker families (FranksVals + AN/LatticeNoConstraints), spanning
the cross product of {avg-sym | quadratic-sym | asymmetric}, with
without {NP priors x5, wall regularizer (tau=5), fakelumi}. All real
data, alpha_S blinded.

**Headline findings (see ## Findings for details):**

1. **Symmetrization matters.** The framework default for NP
   `addSystematic` calls is `symmetrize="average"` (not quadratic) --
   `--symmetrizeTheoryUnc=quadratic` never reaches the NP-adder paths
   in `rabbit_theory_helper.py`. We patched this in a local
   `setupRabbit_quadTest.py` wrapper. Quadratic captures the asymmetric
   SymDiff direction as a separate nuisance, recovering most of the
   gain that "asym" gives over "avg-sym".
2. **FranksVals NP templates give the fit access to large negative
   Lambda_4** (postfit physical -0.78 vs AN's -0.08). The data
   strongly prefers that direction (~3 sigma in theta-space).
3. **The 3-sigma pull is the same in AN and FranksVals fits** -- not
   a postfit-value bug. Within-histmaker plots show Frank's Lambda_4
   templates carry ~3x the AN template's shape strength (not 8x as
   the label ratio 1.0/0.12 implies). The "theta = -3" coincidence
   is the Gaussian-prior penalty vs data-benefit balance point.
4. **The Lambda_4 = -0.78 "physical value" is a linear extrapolation
   ~3x past the Down template.** It is NOT validated against SCETlib
   at that point; the fit only sees the linearization of three
   templates (nominal/Up/Down). Calling it a physical Lambda_4 is
   misleading.
5. **Walling Lambda_4 to the physical floor relocates the strain
   into fakelumi**: FranksVals asym + wall + fakelumi shows
   `fakelumi LR = 37.6 chi2 (6.1 sigma)`, AN equivalent shows
   2.4 sigma. So the data preference doesn't go away when Lambda_4
   is constrained -- it just hides in the yield knob instead.
6. **sigma(alpha_S) was being artificially shrunk** by avg-sym.
   Under proper asym/quadratic NP treatment sigma(alpha_S) widens
   from 0.80 (avg) to ~1.06 (asym) / 1.13 (quadratic) * 10^-3.

**Output state:**

- 14 fitresults.hdf5 files on `$MY_OUT_DIR/260519_franks_vals_*` and
  `$MY_OUT_DIR/260520_franks_vals_*` and `$MY_OUT_DIR/260520_AN_unconstrained_asym_reg*`.
- FranksVals tables (12 rows, organized by symmetrization section,
  prefit row shows asymmetric Lambda ranges) at
  `$MY_PLOT_DIR/260519_franks_vals_compare/np_compare_franks{,_theta}.{tex,pdf}`.
- AN/np-monotonicity-wall table updated with the two
  `unconstrained_asym_reg5{,_fakelumi}` rows at
  `$MY_PLOT_DIR/260513_np_compare/np_compare.pdf`.
- CS gamma and TMD f^NP functions plotted from the FranksVals asym
  postfit at `$MY_PLOT_DIR/260519_franks_vals_np_kernel/asym_postfit_np_kernel.png`.
- Lambda-template comparison plots (AN vs FranksVals,
  same-label cross + within-histmaker) at
  `$MY_PLOT_DIR/260520_AN_vs_franks_ptll/`.
- All ptll-postfit + pulls/impacts plots per config under
  `$MY_PLOT_DIR/260519_franks_vals_*_realdata/`.
- Lambda templates from fitresults (rabbit_plot_hists --prefit
  --varNames, for quad and asym side-by-side) at
  `$MY_PLOT_DIR/260519_franks_vals_lambda_templates_from_fitresults/`.

**Known numerical wrinkles** (worth documenting for future
reproduction):

- The saturated-model `edmval/cov` step in
  `rabbit_fit.py:444-446` triggers Cholesky-not-positive-definite on
  some configs (quadratic+fakelumi, AN unconstrained+asym+reg+fakelumi).
  Workaround: re-run without `--computeSaturatedProjectionTests`;
  loses sat_p_ptll on that row but everything else lands. Same
  family of issue as the "Cholesky issue with the regularizer when
  computing impacts" comment in
  `agents/studies/260511_np_monotonicity_wall/scripts/run_unconstrained_tau3_satp.sh`.
- `--noHessian` is broken for our setup: hits
  `'Fitter' has no attribute 'poi_model'` in the no-Hessian
  primary-fit edmval/cov path. Cannot be used as workaround.
- Wall + asymmetric NPs + `--doImpacts` produces a
  TF `Op:MatrixInverse Input is not invertible` error; same
  workaround (drop `--doImpacts`/`--globalImpacts`/
  `--computeHistImpacts` on configurations that combine wall + asym).
- The chain-wrapper pgrep loop is bug-prone: must `grep -v "^$$ "`
  to avoid self-matching deadlock. Fixed in
  `run_AN_unconstrained_asym_reg_chain.sh`.

**Next action:** discuss the headline conclusions (Lambda_4 wants a
shape no parametrization captures cleanly; sigma(alpha_S) widens
under proper symmetrization) with colleagues and decide a reporting
strategy.

## Guiding Question

How does the fit respond to Frank's NP-variation set under asymmetric
treatment (no symmetrization)? Specifically: does the larger TMD prior
window (0.0--1.0 for lambda_2 / lambda_4 versus the AN's 0.0--0.5 /
0.01--0.12) eliminate the NP-wall behavior observed in `np-monotonicity-wall`,
and how does sigma(alphaS) compare?

## Hypotheses

- Frank's wider TMD-BC variations give the fit enough room to absorb
  shape so the wall behavior from `np-monotonicity-wall` is not
  triggered. [confirmed] -- the saturated p(ptll) jumps from 0% to
  61% under FranksVals asym, but the achieved Lambda_4 is in the
  linear-extrapolation regime, not validated against SCETlib.
- With only lambda_2_nu varying on the CS gamma side, the
  NP-vs-alphaS degeneracy reduces and sigma(alphaS) tightens.
  [ruled-out] -- sigma actually WIDENS under asym/quadratic NPs
  (0.80 -> 1.06 / 1.13 * 10^-3); the default avg-sym was masking
  ~30% of the genuine NP shape uncertainty.
- The "Lambda_4 ~ -3 sigma in both AN and FranksVals fits" is a
  postfit-display bug. [ruled-out] -- it reflects the Gaussian-prior
  penalty vs data preference balance point AND that both NP
  parametrizations drive the data's preferred shape in the same
  direction. The "physical" Lambda_4 values displayed are just
  linear extrapolations past the templates and are not validated
  against SCETlib.
- The data prefers a shape that no current SCETlib NP
  parametrization (tanh_2 OR tanh_6cs) can produce cleanly within
  the wall-physical region. [active] -- followups: extend the
  parametrization, generate SCETlib templates at the data-preferred
  Lambda_4, or float Lambda_6 to relax the wall.
- Walling Lambda_4 cures the unphysical postfit without side
  effects. [ruled-out] -- the data preference relocates into
  fakelumi (6 sigma in FranksVals asym + wall + fakelumi).

## Ideas / Methods Explored

- Treat NP nuisances quadratically symmetrized (default
  `--symmetrizeTheoryUnc=quadratic`) vs asymmetric
  (`--noSymmetrize 'scetlibNP'`). Per user direction
  2026-05-19 14:25, run quadratic first to validate
  against colleague; asymmetric variant queued as a
  follow-up.

## Dead-Ends

(none yet)

## Findings

- 2026-05-19 — Corr-hist NP variations in FranksVals file
  (evidence: `/scratch/submit/cms/areimers/alphas/histmaker/AlphaS/Theorymodels/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksVals_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5`,
  `vars` axis): `lambda20.0`, `lambda21.0` (TMD Lambda_2); `lambda40.0`,
  `lambda41.0` (TMD Lambda_4); `delta_lambda2-0.02`, `delta_lambda20.02`
  (TMD Delta_Lambda_2); `lambda2_nu0.05`, `lambda2_nu0.25` (CS
  gamma lambda_2). No `lambda_inf`, `lambda4_nu`, or `lambda_inf_nu`
  variations (those are fixed per Frank's config).

- 2026-05-19 — FlavDepNP-hist labels match: `pdf0`, `lambda20.0`,
  `lambda21.0`, `delta_lambda2-0.02`, `delta_lambda20.02`,
  `lambda40.0`, `lambda41.0`. CS-gamma variations live only in the
  `_Corr` hist (consistent with `add_gamma_np_uncertainties` reading
  the Corr hist, not FlavDepNP).

- 2026-05-19 14:35 — `LatticeNoConstraintsFranks` wiring validated
  through setupRabbit: `setupRabbit.py ... --npUnc LatticeNoConstraintsFranks`
  ran clean and wrote `ZMassDilepton.hdf5` at
  `$MY_OUT_DIR/260519_franks_vals_quad/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_franks_vals_quad/`.
  No "could not find variation" error from
  `add_gamma_np_uncertainties` (CS side picked up the new
  `lambda2_nu0.05/0.25` labels) and no failure from
  `add_uncorrelated_np_uncertainties` (TMD side auto-detected
  `lambda20.0/1.0`, `lambda40.0/1.0`,
  `delta_lambda2-0.02/0.02` via the regex fallback).

- 2026-05-19 14:30 — Quadratic-symmetrized fit completed in 195 s
  (Asimov, by mistake -- fitter.sh doesn't default to --realData).
  Total pdfAlphaS impact (scale=2 -> sigma_AN units) = 1.105.
  Discarded as a result; superseded by real-data runs after the
  user clarified the fit should be on real data (blinded).

- 2026-05-19 15:25 — Real-data quadratic fit (avg-sym actually --
  see 2026-05-20 below for the framework misnomer) validates
  colleague's setup. Output:
  `$MY_OUT_DIR/260519_franks_vals_quad_realdata/.../fitresults.hdf5`.
  pdfAlphaS Total impact 0.796 * 10^-3, postfit Lambda_4 pull
  ~ -3 sigma (theta), saturated p(ptll) ~ 0%.

- 2026-05-19 16:19 / 16:30 — Asym, asym+inflate5x, inflate5x runs
  land. asym saturated p(ptll) jumps to 61% (vs 0% in quad/avg);
  Lambda_4 theta pull ~ -3 sigma in all of them.

- 2026-05-19 17:16 — Fakelumi chain (3 configs) lands. Quad+fakelumi
  has fakelumi LR ~ 4 chi2 (2 sigma) -- meaningful yield-vs-shape
  tension. Asym+fakelumi has fakelumi LR ~ 0.4 sigma -- yield-vs-
  shape tension VANISHES under asym (the Lambda_4 NP absorbs it).

- 2026-05-19 17:45 — Asym + inflate5x reaches saturated p(ptll) ~
  74% (best of any FranksVals config). The two knobs are
  complementary -- wider priors + asymmetric templates jointly
  reach the deepest data shape.

- 2026-05-20 09:44 — Asym + wall (tau=5) NPMonotonicityFranksWall
  lands. Sat p(ptll) drops to 0% again. The wall pegs Lambda_4 ~ 0
  (data-preferred region blocked), pegs lambda_2_nu ~ 0 too.

- 2026-05-20 10:32 — Quadratic NP fit lands (via
  `setupRabbit_quadTest.py` monkey-patch that overrides
  `Datagroups.addSystematic` default `symmetrize="average"` to
  `"quadratic"` for `scetlibNP*` calls). REVELATION: the framework
  default for NP nuisances was `average`, NOT `quadratic`. The
  `--symmetrizeTheoryUnc=quadratic` setupRabbit flag never reaches
  `add_gamma_np_uncertainties` / `add_uncorrelated_np_uncertainties`
  in `rabbit_theory_helper.py`. Quadratic splits each shape syst
  into a `SymAvg` (symmetric direction) + `SymDiff` (asymmetric
  direction) nuisance pair. The fit's `Lambda_4 SymDiff = +1.66
  sigma` (robust under fakelumi) directly captures the asymmetric
  template direction that avg-sym throws away. sigma(alpha_S)
  WIDENS from 0.80 (avg) to 1.13 (quad) -- avg-sym was hiding ~30%
  of the NP shape uncertainty.

- 2026-05-20 11:46 — AN/LatticeNoConstraints unconstrained + asym +
  reg(tau=5) lands at sigma(alpha_S) = 1.04. The Lambda_4 theta
  pull is ~ -2.8 sigma -- nearly identical theta magnitude to
  FranksVals asym (-2.99). The "physical" Lambda_4 = -0.081 reading
  is misleading: it is a linear extrapolation 3x past the AN Down
  template (0.01), not a SCETlib-validated value.

- 2026-05-20 12:30 — Within-histmaker Lambda_4 template comparison
  plots produced (`compare_AN_franks_within_ratios.sh`,
  `$MY_PLOT_DIR/260520_AN_vs_franks_ptll/`). At low ptll: AN's
  Up/Down templates give a ~+/-1% excursion from nominal; Frank's
  give ~+/-3%. So Frank's templates carry ~3x the AN shape strength
  (NOT 8x as the Lambda_4 label ratio 1.0/0.12 would imply). The
  "theta = -3 sigma in both fits" is therefore NOT a postfit-display
  bug: both fits land at the Gaussian-prior-penalty vs data-benefit
  balance point (~4.5 NLL units = 3 sigma cost), and the fact that
  the Lambda_4 templates drive the data's preferred shape direction
  in both means the optimizer settles at similar theta.

- 2026-05-20 12:26 — Cross-histmaker plots (`compare_AN_franks_ptll.sh`)
  show that the Frank-vs-AN ratio at fixed template label
  (nominal, Lambda_4-Up, Lambda_4-Down) has essentially the same
  shape -- the difference between AN and FranksVals at the same
  template label is dominated by the theory-corr-file baseline
  (LatticeNPLambda4BugfixLambda6 vs LatticeNPLambda4Bugfix), NOT
  by the Lambda_4 value itself.

- 2026-05-20 — sigma(alpha_S) widens with proper symmetrization:
  avg-sym 0.80 -> asym 1.06 -> quadratic 1.13 -> asym+wall 0.93
  -> asym+wall+fakelumi 1.06 * 10^-3. The avg-sym number is
  artificially shrunk by template asymmetry collapse.

- 2026-05-20 — Walling Lambda_4 to physical produces a 6 sigma
  fakelumi LR in FranksVals (asym + wall + fakelumi: LR = 37.6
  chi2). The yield-vs-shape tension that asym "hides" via
  unphysical Lambda_4 resurfaces immediately when the wall blocks
  that direction. AN equivalent shows 2.4 sigma fakelumi LR,
  smaller but in the same direction.

- 2026-05-20 — Bottom-line table (12 rows FranksVals, organized
  by symmetrization schema; AN table augmented with 2 unconstrained
  + asym + reg5 rows). Both physical and theta tables produced.
  Prefit row formatted with asymmetric +/- to reflect actual
  histmaker template ranges. Output:
  `$MY_PLOT_DIR/260519_franks_vals_compare/np_compare_franks{,_theta}.{tex,pdf}`,
  `$MY_PLOT_DIR/260513_np_compare/np_compare.{tex,pdf}`.

## Open Questions

- After this fit lands, compare to the AN-nominal CT18Z 3+0 result
  in `260513_np_compare/np_compare.pdf`. Does Frank's variation set
  give a different alphaS shift than the AN's lattice constraints?

- Should a follow-up fit use quadratic symmetrization for direct
  comparison against the AN-nominal setup?

## Decisions

- 2026-05-19 — Add a new `LatticeNoConstraintsFranks` np-model
  branch rather than patching the existing `LatticeNoConstraints` —
  preserves the AN-nominal flow while letting us A/B test Frank's
  variation set side-by-side.
- 2026-05-19 — Use `--noSymmetrize 'scetlibNP'` so all
  scetlibNP-prefixed nuisances stay asymmetric in the tensor.
- 2026-05-19 14:25 — Run the quadratic-symmetrized variant *first*
  for colleague validation; defer the asymmetric variant until the
  quad numbers match. (supersedes the earlier "asymmetric first"
  plan.)
- 2026-05-19 14:25 — All fits real data, blinded. Wrapper passes
  `--realData` to setupRabbit AND `-t 0` to rabbit_fit (the latter
  is REQUIRED -- rabbit_fit defaults to `-t -1` Asimov).
- 2026-05-19 15:14 — Use ptll-only `Project ch0 ptll` mapping (not
  the full 4-axis bundle); the saturated test runs per-Project, so
  one mapping == one saturated fit instead of five.  Massive wall-
  time saving with no information loss (we only need ptll
  saturated p anyway).
- 2026-05-20 09:20 — Wrote `NPMonotonicityFranksWall` in
  `wremnants.postprocessing.np_monotonicity_franks` (parallel to
  the AN's `NPMonotonicityWall`) with the tanh_2 walls
  (lambda_2_nu >= 0; L_2(y) >= 0; c_1(y) >= 0 at y in {0, 2.5}) --
  the AN's tanh_6cs walls collapse to these when Lambda_6 = 0.
- 2026-05-20 09:38 — `setupRabbit_quadTest.py` wrapper monkey-
  patches `Datagroups.addSystematic` to default
  `symmetrize="quadratic"` for `scetlibNP*` calls.  Discovered
  the framework default is "average" (NOT quadratic), and
  `--symmetrizeTheoryUnc=quadratic` never reaches the NP-adder
  paths -- so all our "quad" runs prior to this point were
  actually avg-sym.  Tables relabeled accordingly.
- 2026-05-20 10:20 — Prefit table row formatting changed to show
  the actual histmaker template ranges (asymmetric +/- where
  applicable) instead of a symmetric +/- sigma_theta=1 band.
- 2026-05-20 11:00 — Table organized into three sections by
  symmetrization scheme (avg sym, quadratic sym, asymmetric).
- 2026-05-20 12:30 — Verified via within-histmaker
  Lambda_4 template plots that Frank's templates carry ~3x the
  AN shape strength (not 8x as the label ratio suggested).  The
  "Lambda_4 = -0.78" reading in FranksVals is a linear
  extrapolation ~3x past the Down template, not SCETlib-validated.

## Next Action

Decide reporting strategy with colleagues given the central
finding: **the data prefers a ptll shape that the current SCETlib
NP parametrizations (tanh_2 OR tanh_6cs) cannot produce within
their physical wall region**.  Concrete sub-questions to discuss:

1. Is the negative-Lambda_4 shape genuinely a feature of QCD that
   the parametrization doesn't capture (i.e. extend the
   parametrization -- floating Lambda_6, add b_T^7, ...), or
   is it pointing to a non-NP mis-modeling that the fit is
   absorbing into the wrong nuisance?
2. Should we generate explicit SCETlib templates at the
   data-preferred Lambda_4 to test whether the linearization at
   |theta| ~ 3 is even close to the real SCETlib prediction?
3. Float Lambda_6 in the fit (and/or lambda_6 on the CS side):
   currently both are fixed.  With nonzero Lambda_6 the
   monotonicity wall on Lambda_4 is relaxed
   (c_1(y) >= -sqrt(20 * Lambda_6 * L_2(y))), so Lambda_4 can
   reach more-negative physical values without violating the
   wall.  Worth a dedicated fit.
4. How to quote sigma(alpha_S): under FranksVals asym we get 1.06
   * 10^-3, under avg-sym we got 0.80, under the wall 0.93.  The
   range itself is part of the systematic uncertainty story.

Suggested concrete next runs (once strategy is set):

- Float Lambda_6 (TMD) and/or lambda_6 (CS gamma) as new nuisances,
  re-fit and check whether Lambda_4 lands in a wall-physical
  region.  Histmaker side may need a new variation if Lambda_6 isn't
  already included as a template.
- Generate SCETlib templates at e.g. Lambda_4 = -0.2 and check the
  linearization vs the actual template.  If the linearization is
  bad, the fit's Lambda_4 = -0.78 reading really is meaningless.
