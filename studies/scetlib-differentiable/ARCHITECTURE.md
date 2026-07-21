# `scetlib.fit` — coding architecture proposal

*Companion to PROPOSAL.md (the physics case). This document specifies the
software design: what moves into SCETlib, the package layout, the data and
API contracts, and the migration path for WRemnants. Draft 2026-07-08.*

## 1. Scope and boundary

One sentence: **SCETlib gains a Python subpackage that turns its own cached
b_T-grids into a differentiable σ(parameters) on a (q_T, Y) grid; experiments
consume that tensor and own everything detector-related.**

```
                    SCETlib                      |        experiment (WRemnants)
                                                 |
runcard → C++ grid production → bt_grid_v2       |
shards → scetlib.fit.SigmaModel                  |
   → σ(λ, θ_TNP, α_s, m_V; q_T, Y)  ── tensor ──→|→ response fold R·σ → rnorm ratio
     (differentiable, fp64)                      |  → rabbit ParamModel (priors,
                                                 |    Hessian J/K, damping wall)
```

Explicitly out of scope for SCETlib: response matrices, reco binning, fit
priors/constraints, the straight-through Hessian wrapper, datacard plumbing.
Explicitly in scope: the closures, the Hankel/Q reassembly, the grid schema,
interpolation of the grids in α_s, and the validation that the reconstruction matches
native SCETlib.

## 2. Package layout

New subpackage in the SCETlib repo (final name/location up to the authors;
`py/fit/` or `prod/scetlib_run/scetlib_fit/` both plausible):

```
scetlib/fit/
├── schema.py        # bt_grid_v2: array names, dtypes, invariants, versioning,
│                    #   provenance (scetlib version, runcard hash), staleness
├── grids.py         # shard discovery, combine, derived-layout cache
│                    #   (row dedup, C-sub-dedup, weighted J0 kernel, memoized npz)
├── closures/
│   ├── np_models.py     # F_eff / gamma_nu^NP forms (tanh_2/6, frac, exp, …)
│   ├── tnp.py           # exp(θ·C) exponent, (1+θ·r) boundary, beam polynomial
│   └── ew.py            # Breit-Wigner (m_V, Γ_V) Q-prefactor
├── backends/
│   ├── numpy_ref.py     # REFERENCE implementation — defines correctness
│   ├── tf.py            # TensorFlow: same math, AD-safe (frozen-eq masks)
│   └── jax.py           # (later; contract identical)
├── reconstruct.py   # fixed-grid Hankel (Simpson-as-matmul), arctan-Q² Q
│                    #   integral, Y-fold, rebin to requested edges
├── model.py         # SigmaModel front-end (§4)
└── validate.py      # closure-vs-native + backend-parity test drivers (CI)
```

Provenance of each piece: `grids.py`/`reconstruct.py`/`backends/tf.py` are the
WRemnants `btgrid_cache` / `btgrid_integrate` / `btgrid_tf` modules, upstreamed;
`backends/numpy_ref.py` and much of `closures/` already exist in the fork as
`prod/scetlib_run/factorize.py`. The convergence of those two codepaths — one
math, two backends, parity-tested — is the core of the port.

## 3. C++ / production additions

New pybind accessors (siblings of the existing `resummed_bT_integrand`,
`gamma_nu_NP_log_coeff`, `b_star_global` in `py/qT/DrellYan`):

```cpp
// exponent coefficient of an anomalous-dimension TNP (gamma_cusp, gamma_mu_q,
// gamma_nu → returns the delta-gamma_nu factor multiplying the cached C_nu)
std::vector<double> tnp_exponent_coeff(TnpName, Q, Y, qT, const std::vector<double>& bT);
// relative boundary coefficient: r = deltaX/X0 for h_qqV (Q-only) and s
std::vector<double> tnp_boundary_ratio(TnpName, Q, Y, qT, const std::vector<double>& bT);
// channel-summed beam coefficients: linear l_c, quadratic q_cc (and pairwise),
// as ratios to the nominal channel-summed product
BeamCoeffs        tnp_beam_coeffs(TnpName [, TnpName2], Q, Y, qT, const std::vector<double>& bT);
```

`grid.py` (production driver) emits these into the shards alongside I_pert.
**Bootstrap fallback needing zero C++:** for any parameter entering one
ingredient linearly-in-exponent, C = ln[I(θ=1)/I(θ=0)] pointwise from two
`resummed_bT_integrand` runs (exact — ln I is exactly linear in θ); a θ=2 run
asserts no leak. Boundary ratios analogously from the linear difference. The
accessors are the tidy long-term route; the ln-ratio route unblocks pilots.

The singular fixed-order expansion is also linear in each θ; production emits
its per-TNP linear coefficients (no b_T axis) so the consumer can build
σ_ns(θ) for matching.

## 4. The API contract

```python
import scetlib.fit as sf

model = sf.SigmaModel(
    grid_dir,                  # one directory per (process, PDF member) — or
    alphas_grids={...: dir},   #   several, keyed by alpha_s value
    backend="tf",              # "numpy" (reference) | "tf" | later "jax"
)

model.params        # registry: name → (kind, central, prior metadata)
                    #   kinds: np_lambda | tnp_adm | tnp_boundary | tnp_beam |
                    #          alphas | ew
model.central       # the central parameter point (θ=0, λ_central, α_s^0)
model.sigma_ns(params)         # matched nonsingular on the same grid
sigma = model.sigma(params, binning)   # → (N_Y, N_qT) tensor, differentiable
                                       #    in every entry of `params`
```

Rules of the contract:

- `sigma()` is **exact** in every closure-class parameter (λ, all TNPs, m_V,
  Γ_V) and interpolation-accurate in α_s between the sampled α_s values. No
  parameter is ever
  discretized except α_s/PDF.
- All arrays fp64; the (Q, Y, q_T, b_T) sampling is identical across every
  array, α_s point and member (schema invariant, checked at load).
- The numpy backend is normative: tf/jax must match it to a stated parity
  tolerance (≤1e-12 relative away from cancellation-dominated tail bins,
  rtol+atol metric as in our factorized-parity harness).
- Semantic versioning of the schema; `SigmaModel` refuses grids whose schema
  or provenance it does not understand.

## 5. Numerics requirements (non-negotiable, learned in production)

1. Fixed quadrature everywhere; adaptivity only at grid *production* time.
2. fp64 throughout — the high-q_T Hankel tail is cancellation-dominated
   (Simpson condition number up to ~1e6).
3. AD-safe branches: comparisons feeding `where`-masks take `stop_gradient`
   inputs (nested forward-mode breaks otherwise — needed for Hessians).
4. Deterministic memory layout: dedup verified bit-exact at load, achieved
   factor logged (degeneracy depends on the profile transition points).
5. No hidden truncation: qT/Q coverage limits recorded in schema metadata.

## 6. Consumer migration (WRemnants)

- `sigma_gen.SigmaGenModel` → thin wrapper over `sf.SigmaModel` (constructor
  translates datacard metadata → params/central; keeps the WRemnants-side
  σ_ns file handling until production emits it).
- `param_model.SCETlibNPParamModel` keeps its exact current shape: `self.core`
  becomes the wrapper; Steps 3–4 (R fold, rnorm, guard), the straight-through
  J/K, and the damping wall are untouched.
- New rabbit item: N(0,1) constraints on the TNP subset of ParamModel
  parameters (λ stay free); design with the rabbit maintainer.
- Datacard: template nuisances owned by the model get `--excludeNuisances`,
  as done for the NP variations.

## 7. Testing / CI

| test | where | asserts |
|---|---|---|
| closure vs native | SCETlib CI | reconstruction at a parameter point == native spectrum run (≤ numerical floor, ~0.06%) |
| backend parity | SCETlib CI | tf (jax) == numpy_ref, ≤1e-12 rtol+atol |
| θ-linearity | SCETlib CI | ln I exactly linear across θ∈{0,±1,±2} per TNP |
| gradient parity | SCETlib CI | AD gradient == finite-difference on numpy_ref |
| template cross-check | WRemnants | model variation == existing conf template (the λ check, 0.02–0.05%, repeated per TNP) |
| injection closure | WRemnants | fit recovers injected (λ, θ, α_s) truth |

## 8. Phasing

- **P0 (now, WRemnants tree):** γ_ν TNP pilot via the ln-ratio route; validate
  against conf [17]/[18] templates + θ=±2 + injection fit. Produces the
  evidence for the author discussion. No C++, no upstream dependency.
- **P1:** C++ accessors + bt_grid_v2 schema land in SCETlib (author-side
  deliverable); remaining resummation TNPs + h/s.
- **P2:** the reconstruction library moves upstream (`scetlib.fit`), numpy
  reference + tf backend + CI; WRemnants `sigma_gen` becomes the wrapper.
- **P3:** beam TNPs (channel-sum accessors, memory re-budget) + σ_ns
  coefficients in production.
- **P4:** α_s grid points (production campaign, α_s interpolation in `model.py`,
  GPU memory rework) and per-PDF-member wiring.

## 9. Open questions for the SCETlib authors

1. Package location/name; is a TensorFlow *optional* dependency acceptable
   (numpy core mandatory, `pip install scetlib-fit[tf]` style)?
2. Analytic accessor vs ln-ratio extraction as the *supported* coefficient
   route (we propose: accessors, with ln-ratio kept as a cross-check).
3. Beam TNP internals: is the channel-summed linear/quadratic export the
   preferred factorization, or would they rather expose channel-resolved
   grids and let the closure do the sums?
4. Release cadence / schema ownership once an experiment's central prediction
   depends on the package.
5. Interest in extending the same contract to other SCETlib modules (pTjet).
