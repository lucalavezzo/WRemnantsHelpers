---
title: NP functions, lattice-constrained prefit vs walled warm postfit
slug: 261005-np-forms-lattice
study: walled-multistart-census
status: done
created: 2026-10-05
updated: 2026-10-05
owner: orchestrator (quick request from Luca)
---

# NP functions: lattice-constrained prefit vs walled warm postfit

## START HERE (status as of 2026-10-05)

> **Done.** CS kernel γ_ν^NP(b) and TMD F_eff(b, Y) for:
> - the **prefit**: the CS kernel from the lattice constraint in the card (λ2_ν = 0.1345 ± 0.031, λ4_ν = 0, λ∞_ν = 2);
>   the TMD at the card anchor (λ2 = λ4 = 0.4, δλ2 = 0);
> - the **postfit** NOMSTIFF (nominal: card A + lattice, new cache, margin 0, τ 8), with a 68 % band from Gaussian draws of
>   its Hessian covariance;
> - the **postfit** LATL4ZY35WALLWARM (same, but margin 5e-3, τ 5), as a line.

- **Next action:** none.
- **Blocking on:** nothing.

## Result

Made with the existing plotter `wremnants.postprocessing.scetlib_np.np_function_plots` in raw-λ mode
(`scripts/run_np_function_plots.sh`):
- num = postfit, den = lattice-constrained prefit;
- the black dashed line and grey band are the plotter's default lattice reference (the 2506.13874 fit);
- the dotted lines are MAP22.

Postfit LATL4ZY35WALLWARM (walled warm lattice fit, margin 5e-3, τ 5):

![prefit vs LATL4ZY35WALLWARM](np_functions_prefit_vs_LATL4ZY35WALLWARM.png)

Postfit NOMSTIFF (the same fit at margin 0, τ 8):

![prefit vs NOMSTIFF](np_functions_prefit_vs_NOMSTIFF.png)

| λ (physical) | prefit | NOMSTIFF | LATL4ZY35WALLWARM |
|---|---|---|---|
| λ2 | 0.4 | 0.0256 ± 0.0427 | 0.0290 ± 0.0429 |
| λ4 | 0.4 | 0.0876 ± 0.0272 | 0.0873 ± 0.0272 |
| δλ2 | 0 | −0.0041 ± 0.0068 | −0.0039 ± 0.0068 |
| λ2_ν | 0.1345 ± 0.031 (lattice) | 0.0643 ± 0.0229 | 0.0634 ± 0.0229 |
| λ4_ν, λ∞, λ∞_ν | 0, 1, 2 (held) | held | held |

**Read.**
- The postfit CS kernel is about half as steep as the lattice prefit: γ_ν(4) is −0.95 against −1.58, and λ2_ν is 2.3σ
  below the lattice value. This is the known ptll-shape tension (lattice-cs-kernel/260923-lattice-fits).
- The postfit F_eff is far less damped than the anchor below b ≈ 3 GeV⁻¹ (λ2 → 0.026), and joins the same exp(−2λ∞ b)
  tail.
- The two postfits are indistinguishable at this scale: removing the margin changes nothing visible.

**Caveats.**
- γ_ν is SCETlib's convention, = 2 γ̃_ζ (AN eq:npgamma).
- Bands (added 2026-10-05, Luca): the plotter got a `--num-cov` / `--den-cov` option (raw-λ mode; JSON covariance in
  physical λ; toys around the point). The prefit band is λ2_ν ± 0.031 (the lattice refit; TMD has no band). The postfit bands
  come from each fit's Hessian covariance of (λ2, λ4, δλ2, λ2_ν) (`cov_*.json`), 1000 toys. The change is UNCOMMITTED in
  WRemnants-scetlib-np-param-model `np_function_plots.py`. Caveat: the walled Hessian band is one-sided in reality at the active
  face L2(|Y|=2.5) = 0.
- Previously: no postfit bands, because the plotter's toy bands need a scetlib_np fitresult, not scetlib_AD. (A first, custom version with
  Gaussian bands, `scripts/np_forms_prefit_postfit.py`, is superseded by the standard tool at Luca's request.)
- (superseded) The custom version's postfit band came from Gaussian draws of the WALLED Hessian. NOMSTIFF sits on the face L2(|Y|=2.5) = 0, where the
  real constraint is one-sided, so the band's lower side in that direction is not physical.
- There is no prefit TMD band: the TMD priors (width 0.5) are far wider than the plot range.
- The forms come from the scetlib_np plotter (btgrid_tf tanh_2), validated in walled-two-minima/260930-np-forms against the
  scetlib-cms formulas.

## Check: toy CS band vs exact λ2_ν ± σ (2026-10-05, Luca)
`scripts/check_cs_band.py` → `check_cs_band.out`. It uses the same toy generator as the plotter (`_raw_toys`, seed 0) and
compares the 16/84 % range with γ_ν evaluated exactly at λ2_ν ± σ.
- With 1000 toys (as plotted) the band edges sit 3–8 % of the half-width INSIDE the exact curves, uniformly in b. That is
  percentile noise (~5 % expected at n = 1000) plus 16/84 instead of 15.87/84.13 (0.55 %).
- With 100k toys the agreement is ≤ 1.1 % (prefit) and ≤ 0.5 % (NOMSTIFF).
→ The toys are right. The plotted 1000-toy bands are slightly narrow from MC noise. Use exact ±1σ curves for the CS kernel,
  or ≥ 20k toys.

## Reproduce
1. `scripts/dump_np_cov.py np_lambdas_cov.json`: main tree, via `WRemnantsHelpers/agent_setup.sh --scetlib current --`.
2. `scripts/np_forms_prefit_postfit.py --json np_lambdas_cov.json -o .`: in the param-model tree, as in
   walled-two-minima/260930-np-forms/scripts/run_overlay.sh.
