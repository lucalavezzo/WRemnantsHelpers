# Saturated and projected-saturated goodness-of-fit tests: theory, dof counting, and rabbit

What `rabbit_fit.py` prints as "Saturated chi2" (full) and what
`--computeSaturatedProjectionTests` prints per mapping (projected) measure, why their ndf are
what they are, and the one case where rabbit's projected ndf is wrong. Worked out and checked
against the code and a real fit on 2026-09-29 (rabbit `2a59246`). For toy calibration of
either statistic, see `saturated_test_toys.md`.

## 1. The full saturated test

Rabbit's reduced NLL is

    L(θ) = Σ_i [ν_i − n_i − n_i ln(ν_i/n_i)]  +  ½ Σ_k (θ_k − θ̃_k)²/σ_k²  (+ BB terms, + regularizer)

The Poisson part is half the Baker–Cousins deviance, so it is 0 at ν = n. Read each Gaussian
constraint as a **pseudo-measurement** θ̃_k of θ_k. The saturated model then fits every real bin
and every pseudo-datum exactly, with L = 0, and the test statistic is

    q_sat = 2 L(θ̂)

This is a likelihood ratio of nested models. By Wilks, ndf = (number of measurements) −
(number of fitted parameters):

    ndf = (N_bins + N_constr) − (N_free + N_constr) = N_bins − N_free

- **A constrained parameter costs zero dof**, whether it is a card nuisance or a ParamModel
  parameter with a prior: it adds one parameter and one pseudo-datum. The same holds for each
  Barlow–Beeston β. **Only unconstrained, non-frozen parameters are charged.**
- The one-sided NP wall is **not** a pseudo-measurement. When it is inactive it changes
  nothing. When it is active it is a boundary, so the reference becomes a χ² mixture (Chernoff
  1954; Self & Liang 1987) and has to be settled with toys.

## 2. The projected saturated test

Take a mapping that only selects and sums input bins, e.g. `Project ch0 ptll`, with J output
bins. Build M₁ by multiplying the prediction in every input bin i by a free scale s_{j(i)},
where j(i) is the output bin that i falls into. Input bins outside the mapping get scale 1.
M₀ (the analysis model) is M₁ with every s_j = 1, so the two are nested, and

    q_proj = 2 [L_M₀ − L_M₁]

In words: how much the fit improves when the projected (ptll) shape is completely free while the
remaining structure (the yll shape inside each ptll bin) stays as the model predicts. This is
**not** a GoF test of the 1D ptll histogram on its own. θ is still fitted to the full 2D data in
both models.

### Degrees of freedom

In the linearized Gaussian limit, whiten the data (including the pseudo-data). Then
q_proj = rᵀ(P₁ − P₀) r, where r is the whitened residual and P₀, P₁ are the projectors onto the
tangent spaces of M₀ and M₁. It is therefore exactly χ² with

    ndf = rank(M₁) − rank(M₀) = J − d,     d = dim( span(S) ∩ span(J_free) )

- S is the J scale directions: ν restricted to the input bins of each output bin.
- J_free is the Jacobian of ν with respect to the **unconstrained** parameters.
- **Constrained parameters never contribute to d.** Their tangent vector has a component along
  their own pseudo-datum, while span(S) lives purely in data space, so the two cannot coincide.
  A constrained nuisance that is fully degenerate with S just relaxes to its prior in M₁, and q
  correctly includes the pull it no longer pays.
- **Only exact degeneracy counts.** A free parameter whose effect is *almost* a pure
  per-projected-bin rescaling still leaves rank(M₁) − rank(M₀) = J. Near-degeneracy does not
  lower the ndf. What it does do is make M₁ explore that parameter over a much wider range, so
  the *linear* approximation behind Wilks is stressed (see section 4).
- **The textbook d = 1 case:** a free overall normalization (a `Mu`-type POI, a free rate, an
  unconstrained norm nuisance) with a projection that covers the whole channel. The sum of the
  s_j reproduces it, so the true ndf is J − 1.

### The chain decomposes

M₀ ⊂ M₁ ⊂ M_sat are nested, so the deviances partition ("partitioning chi-squared", Agresti):

    q_sat = q_proj + q_resid,     q_resid = 2 L_M₁ ~ χ²(N_bins − N_free − J + d)

and q_proj and q_resid are asymptotically independent. q_proj is the part of the misfit that lives
in the projected shape, and q_resid is the rest. Example, the walled data fit `CCWALLWARMPF` (card
A, old cache): 742.89 = 70.39 + 672.50 with 779 = 39 + 740 dof. The whole tension is in the ptll
shape (p = 0.15 %), and the within-ptll yll structure is fine (χ²(740) p ≈ 0.96).

### External validation (independent of rabbit)

- **The J − d rule, in a tool CMS already uses: Combine's `ChannelCompatibilityCheck`.** It fits
  one free signal strength r per channel (the alternative) against one common r (the null) and
  refers q = −2 ln[L(r̂)/L({r̂_i})] to **χ²(N_c − 1)**: CMS, *The CMS statistical analysis and
  combination tool: COMBINE*, arXiv:2404.06614, Eq. (39) and the text after it. That is exactly
  this construction: free per-group scale factors on top of the model, with one dof removed
  because the common free r is exactly the sum direction of the per-channel r_i (d = 1). Nuisances
  are constrained and profiled in both fits, and they are **not** subtracted.
- **Nested-model deviance differences, the general statistics result.**
  - Agresti, *Categorical Data Analysis*: G²(M₀|M₁) = G²(M₀) − G²(M₁), with df = the difference
    in residual df, and "partitioning chi-squared".
  - McCullagh & Nelder, *Generalized Linear Models*: analysis of deviance, and aliasing.
    Exactly degenerate (aliased) parameters do not count, which is where d comes from.
- **Constraints as auxiliary measurements, so they cost no dof.** Cranmer, *Practical
  Statistics for the LHC*, arXiv:1503.07622 (auxiliary measurements and global observables).
  Combine's saturated test (arXiv:2404.06614, Eq. (38)) cites Cousins, arXiv:1807.05996, and is
  meant to be used with frequentist toys. The "N_bins − N_free" count is what follows from that
  formalism plus Wilks. It is also measured directly here: toys have mean 784.8 ± 3.7 against 779
  (`saturated_test_toys.md`).
- **The saturated construction:** Baker & Cousins, NIM 221 (1984) 437; Cousins, "Generalization
  of Chisquare Goodness-of-Fit Test for Binned Data Using Saturated Models" (UCLA note).
- **Related but different:** Maydeu-Olivares & Joe's limited-information M_r statistics (JASA 100
  (2005) 1009; Psychometrika 71 (2006) 713). They are quadratic forms in *marginal* residuals
  alone, so every fitted parameter is charged. Here only the exactly degenerate ones are, because
  the full table still informs θ in both models.

## 3. How rabbit implements it (`WRemnants/rabbit` `2a59246`)

| | code | verdict |
|---|---|---|
| full q | `2·reduced_nll()`, `bin/rabbit_fit.py:1038` | ✔ |
| full ndf | `size(nobs) − Fitter.nfreeparms` (`cw == 0` and not frozen, over [ParamModel \| systs]), `rabbit_fit.py:1035`, `fitter.py:704` | ✔ matches section 1 |
| scales | `SaturatedProjectModel` (`param_models/param_model.py:470`): one free scale per mapping output bin, stored as √s (s ≥ 0), unused input bins held at 1; bins from `Mapping.output_indices()` | ✔ |
| projected fit | deep-copied fitter, composite [analysis \| scales] model, toy x0 kept, regularizers and blinding re-armed, **warm start** at the main minimum with s = 1 (so q ≥ 0) | ✔ |
| projected q | `2·(nll_main − nll_sat)`, both from `reduced_nll()` | ✔ |
| projected ndf | `saturated_model.npoi` = J, `rabbit_fit.py:603` | **≈ ✔: does not subtract d** |

- **Rabbit only warns about output bins with no input.** It does not detect a free parameter
  that is exactly degenerate with the scales.
- **The tell is the singular M₁ Hessian:** the log line "Could not compute the covariance of the
  saturated fit" (`rabbit_fit.py:597`). If you see it, the printed ndf is probably one or more
  too high and the p-value too optimistic.
- **A possible fix:** compute d as rank([J_free | S]) − rank(J_free) in the whitened space, or
  from the rank deficiency of the M₁ Hessian, and print `ndf = J − d`.

## 4. Checked on a real fit: `CCWALLWARMPF` (2026-09-29)

`/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260917_cc_fits_wall/fitresults_CCWALLWARMPF.hdf5`
has both covariances: `results/cov` for M₀ and
`results/mappings/Project ch0 ptll/saturated_fit/cov` for M₁.

- **Full test:** ndfsat = 779 = 780 bins − 1 free (`alphaS`). The 46 NP/resum ParamModel
  parameters carry priors, and no card nuisance is unconstrained. q_sat = 742.89.
- **Projected test:** J = 39, q = 70.39, edm = 1.6e-8. **d = 0 and ndf = 39 is formally right.**
- **Rank check, rank([J_free | S]) − rank(J_free), in Fisher-information form.** The per-bin
  Jacobian is not saved, but the M₁ covariance holds the same information.
  - Invert the [α_s | S] block of `saturated_fit/cov`. That gives the Fisher information on
    (α_s, s) with every constrained parameter profiled, i.e. the Gauss–Newton [ĵ_α | S]ᵀ W̃ [ĵ_α | S].
  - Normalized to unit diagonal, its smallest eigenvalue is 2.95e-5. Rank 40 = 1 + 39, so d = 0.
    The small eigenvalue is a direction among the scales themselves (2.95e-5 for S alone),
    absorbed by constrained parameters, which cost no dof.
  - α_s's own information orthogonal to span(S): 1 − ρ² = 0.016 from this block, and 0.022 from
    σ_M0/σ_M1. The two differ because the Hessians are taken at different minima, which is itself
    a measure of nonlinearity.
  - Caveat: this is the exact Hessian at the M₁ minimum, not a pure Jacobian rank. Residual
    curvature can in principle lift an exact degeneracy slightly. A rank taken straight from
    ∂ν/∂α_s would need a cache load.
- **But α_s is 97.8 % degenerate with the scales.** σ(α_s) grows from 0.543 to 3.64 (×6.71), so
  ρ²(α_s, scales | rest) = 1 − (0.543/3.64)² = 0.978, and max |corr(α_s, s_j)| = 0.974.
  - Almost all of α_s's constraining power in this card is ptll shape. What survives in M₁ is the
    ~2 % that comes from its yll dependence.
  - Constrained parameters inflate too, which is harmless for the dof count: λ₄ ×109, λ₂^ν ×17,
    δλ₂ ×2.7, λ₂ ×2.2.
- **Consequence: the ndf is fine, and the linear approximation is what's stressed.** M₁ explores α_s
  over a range ~7× wider, and λ₂^ν moves −1.45 → −0.51, i.e. 20 of its M₀ σ's and deep into the
  λ₂^ν < 0 region where AD caches are not exact (`scetlib_ad_cache_validity.md`). Wilks then
  depends on the model being linear over that whole range. The toys are the arbiter:
  - Projected-ptll toys gave mean 37.7 ± 0.8 and sd 8.5, against χ²(39) with mean 39 and sd 8.8,
    and a KS p of 0.12 (`saturated_test_toys.md`).
  - That is consistent with 39, and 112 toys cannot tell 39 from 38. Separating them at 3σ on the
    mean needs ~700 toys.
  - It is immaterial for the conclusion: p = 0.15 % with ndf 39, 0.11 % with ndf 38.
- **Recipe to repeat this on another fit** (numpy only, outside the container, but not from `/tmp`:
  a stray `/tmp/grp.py` shadows the stdlib):

```
from wums import ioutils; import h5py, numpy as np
r = ioutils.pickle_load_h5py(h5py.File(path)["results"])
C  = r["cov"].get().values();  n  = list(r["parms"].get().axes[0])
sf = r["mappings"]["Project ch0 ptll"]["saturated_fit"]
Cs = sf["cov"].get().values(); ns = list(sf["parms"].get().axes[0])
# d = 0 iff sf has a "cov" (M1 Hessian invertible); near-degeneracy of free p:
rho2 = 1 - C[n.index(p), n.index(p)] / Cs[ns.index(p), ns.index(p)]
```

## 5. Were the toys thrown correctly? Audit of `260925-wall-sat-toys` (2026-09-29)

The yardstick is the parametric bootstrap for GoF: generate at the best fit, throw the global
observables around their fitted values, and refit with the identical likelihood. That is Combine's
`--toysFrequentist` (arXiv:2404.06614, sec. on pseudo-data generation) and the ATLAS+CMS 2011
Higgs-combination prescription.

| check | where | verdict |
|---|---|---|
| truth = walled postfit vector | `xparam_default` (46 ParamModel params) + `--setConstraintMinimum` × 3673 card nuisances, both move `x0default`; `defaultassign()` puts x there before `toyassign` | ✔ |
| pseudo-data | `toyassign`: `frequentistassign()` changes x0/β0 only, then `data_nom = expected_yield()` at x = truth, β = 1, then Poisson | ✔ |
| global observables | x0 = truth + σ·N(0,1) wherever cw > 0 (ParamModel priors and card nuisances); BB β0 thrown (gamma: Poisson(kstat·β)/kstat) | ✔ |
| saturated sub-fit keeps the thrown centres | `rabbit_fit.py:469–496` | ✔ |
| same likelihood as the data | same card, cache (md5-identical /scratch copy), `SCETlibADParamModel`, `NPDampingWall` τ = 5, `-m Project ch0 ptll`; wall `set_expectations` is start-independent | ✔ |
| blinding | generated with blinding disarmed (`defaultassign`), fitted armed; a reparametrization, so the NLL minimum is unchanged | ✔ |
| seeds | 18 processes, distinct seeds 1001…2802, 2+2+12×7+4×6 = 112 toys | ✔ |
| main-fit convergence | EDM median 4e-12, 2/114 above 1e-3 (max 5e-3, i.e. Δq ≲ 0.01) | ✔ |
| projected sub-fit convergence | `--noHessian`, so no EDM; `epoch_loss` flat, change over the last 5 iterations ≤ 4e-5 in all 112 | ✔ (plateau, not a certificate) |
| α_s generated at the cache anchor, not α̂_s | blinding forces it | assumption. The truth point is still on the model, but not a conditional MLE (Combine would profile the nuisances at fixed POI) |
| BB β generated at 1, not β̂ | data-fit β̂ not reproducible | small approximation |

**Verdict:** a correct frequentist parametric bootstrap, with the two stated approximations.

## Cross-references

- `saturated_test_toys.md`: toy calibration of both statistics with a ParamModel + wall.
- `profile_likelihood_pitfalls.md`: why saturated p-values from two different prior choices are
  two different fits.
- `rabbit_minimizer_tolerances.md`: `success`/`status` do not certify the M₁ minimum. Use the
  saved `saturated_fit/edmval`. An under-converged M₁ biases q_proj low.
- `scetlib_ad_cache_validity.md`: the λ₂^ν < 0 caveat that M₁ runs into.
