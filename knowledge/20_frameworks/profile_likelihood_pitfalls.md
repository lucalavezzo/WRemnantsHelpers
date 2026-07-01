# Profile-likelihood pitfalls in rabbit fits

Source: study `studies/260430_debug_1d_vs_4d/` (4D nominal vs
`scetlibNoConstraint`).
Last updated: 2026-05-04.

## Topic

How to read postfit σ(POI) and the rabbit `rabbit_print_impacts.py` group
impacts when constraints on nuisance parameters are added or removed.
Focused on the SCETlib non-perturbative shape (λ₂/λ₄), but the lesson is
generic.

## The pitfall

In a *purely linear / Gaussian* profile-likelihood fit, removing a
Gaussian prior on a nuisance parameter can only inflate or leave
unchanged σ(POI). Algebraically (collapsed schematic):

  σ²_POI ≈ 1 / [ H_PP − Σ_i H_PN_i (H_NN + δ_ij/σ²_prior)⁻¹ H_N_jP ]

Setting 1/σ²_prior = 0 makes the subtracted term larger, so σ²_POI
grows.

Therefore: **if you remove a Gaussian constraint and σ(POI) goes down,
the fit is non-linear and the postfit point has moved.** This is
diagnostic of model stress, not a real gain in sensitivity.

## Diagnostic signature

Observed in 260430_debug for the 4D fit:

| quantity                  | nominal | scetlibNoConstraint |
|---------------------------|---------|---------------------|
| Total σ(α_s) (impact)     | 0.55164 | 0.53407 (−3.2 %)    |
| `resum` group impact      | 0.4294  | 0.4049              |
| `resumNonpert` group impact | 0.3840 | 0.3554              |
| `resumTransitionFOScale`  | 0.0330  | 0.0851              |
| Saturated p (ptll proj.)  | 2.54 %  | 60.17 %             |
| λ₂ postfit                | +1.80 ± 0.94 | +3.37 ± 0.30   |
| λ₄ postfit                | −1.11 ± 0.93 | −15.97 ± 9.57  |

Two simultaneous signs of model stress at the prior:
1. Saturated p-value collapses (fit quality is poor at the priored point).
2. Released NPs run away to large pulls.

When σ(POI) drops by a few percent under prior removal, expect both.

## Why it happens

At the priored minimum the SCETlib NP basis cannot reach the data's
preferred shape, so the residual mis-modelling sloshes into the rest
of the resum/transition/PDF sector and into α_s. The Hessian's
H_{α_s, resumNonpert} cross terms are large at this stressed point,
and σ(α_s) is correspondingly inflated.

Releasing the priors lets λ₂/λ₄ absorb the data shape directly. The
fit moves to a different, well-fitting minimum. The local Hessian is
re-evaluated there: cross derivatives between α_s and `resumNonpert`
weaken (the NP shape is now resolved by the SCETlib NPs themselves
rather than mediated through α_s), so the impact assigned to
`resum*` drops and σ(α_s) follows.

## Rules of thumb

- A reduction in σ(POI) on prior removal is a **red flag for the
  prior's central value**, not a green light to drop the prior.
- The first thing to check after seeing such a reduction is the
  saturated p-value at both points. If it changes by orders of
  magnitude, you are reading off two different physical fits, not the
  same fit with looser uncertainties.
- The grouped impact table can mislead: total σ(POI) can go down while
  individual subgroup impacts go up (here `resumTransitionFOScale`
  more than doubles). Read the full table and the cross-correlations,
  not just `Total`.
- For interpretation/uncertainty quotation, use the priored fit (it is
  the model the analysis is committed to). Use the unconstrained fit
  as a *diagnostic* of model adequacy, not as a sensitivity baseline.

## Cross-references

- Study: `studies/260430_debug_1d_vs_4d/`
- Inputs: `$MY_OUT_DIR/260430_debug/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_LatticeNoConstraints*/`
- Tool: `rabbit_print_impacts.py -s` (sorted grouped impacts, default POI)
- Patch needed for `scetlibNoConstraint`: see study README — three
  `noConstraint=True` lines in `wremnants/postprocessing/rabbit_theory_helper.py`.
