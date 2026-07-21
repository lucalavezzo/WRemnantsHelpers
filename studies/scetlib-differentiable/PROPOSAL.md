# Differentiable SCETlib predictions via factorized parameter closures

*L. Lavezzo (MIT) — discussion draft for SCETlib authors/users, 2026-07-08*

## What we built (CMS W/Z p_T fits)

Profile-likelihood fits (m_W, α_s) need the theory prediction as a *continuous,
differentiable* function of its parameters. The standard approach — one SCETlib
run per parameter up/down, log-linear template interpolation in the fit —
assumes the joint response factorizes into an outer product of 1-D responses.
For the nonperturbative parameters this failed: the λ×λ cross terms are O(1).

Our fix, now validated in production, is a **b_T-grid export** we added in a
SCETlib fork (accessors `resummed_bT_integrand`, `gamma_nu_NP_log_coeff`,
`b_star_global` — not yet ported upstream): SCETlib runs **once** with NP off
and tabulates the parameter-independent content of the integrand — the
perturbative b-space integrand I_pert and the rapidity-log coefficient C_ν —
on a fixed (Q, Y, q_T, b_T) quadrature sampling. We call this bundle, the
fixed sampling plus all arrays tabulated on it, *the b_T-grid*. At fit time
we rebuild, in TensorFlow,

    σ(q_T; λ) = q_T ∫ db_T  b_T J₀(q_T b_T) · I_pert · exp[C_ν · γ_ν^NP(b*; λ_ν)] · F_eff(Y, b*; λ_eff)

with fixed-grid Simpson quadrature. Only the small analytic NP closures are
transcribed; all λ enter as free differentiable fit parameters, **jointly
exact** — no templates, no cross-term approximation. Validated against native
SCETlib to 0.06–0.14% (numerical floor); fast enough to sit inside a
~3750-parameter likelihood with exact gradients and Hessian.

## The proposal: extend this treatment to the other varied parameters

Today, every parameter other than the NP λ reaches the
fit as up/down templates: SCETlib runs at ±1 variations with all other parameters
frozen at their central values, and the fit multiplies interpolated 1-D responses — which
both linearizes each response and drops all cross-nuisance terms. **We propose to change what SCETlib delivers to a fit: not predictions evaluated at chosen parameter points, but the prediction as an exact, differentiable function of its parameters.**
Concretely, this costs one small additional array per parameter next to the b_T-grid of the export mode above which represents the exact rule for how that parameter enters the integrand. The fit then evaluates the true σ(all parameters, jointly) at every minimizer step. This extends the mechanism already built and validated for the NP λ to the TNPs, and (by interpolating the b_T-grid in α_s) to α_s and the PDF.

The b_T-space cross section is a
product of ingredients, times an exponential:

    σ ~ H · B_a B_b S · exp(U) · F_NP ,

- **H**(Q; μ_H) — hard function: |Wilson coefficient|² at μ_H ~ Q.
- **B_a, B_b**(x, b_T; μ_B, ν_B) — beam functions: TMD PDFs of the two
  protons, perturbatively matched onto the collinear PDFs.
- **S**(b_T; μ_S, ν_S) — soft function: Wilson-line matrix element.
- **exp(U)** — μ/ν-RGE evolution factor resumming the q_T/Q logs; U is built
  from the anomalous dimensions Γ_cusp, γ_μ, γ_ν.
- **F_NP**(Y, b*; λ) — large-b_T nonperturbative factors: F_eff, and γ_ν^NP
  entering through U.

Each varied parameter is the unknown piece of exactly **one** of these
ingredients, and — by SCETlib's own TNP definition, `coeff·(1+θ)`
(core/TNPs.hpp) — enters it *linearly* (boundary functions) or *linearly in
the exponent* (anomalous dimensions). For such a parameter the integrand
splits, exactly, into a θ-independent part times a simple factor whose
functional form in θ is known — both still inside the b_T integral. For
example, the hard-function TNP: H(Q;θ) = H₀(Q) + θ·δH(Q) is the entire
θ-dependence, so

    I(θ) = H(Q;θ) · [B_a B_b S e^U]  =  I_pert · (1 + θ·r_H(Q)) ,   r_H = δH/H₀

— an identity valid at any θ, not an expansion. So the θ=0 integrand I_pert
(unchanged, still the fully collapsed integrand — we never split it into
H/B/S pieces) plus the ratio r_H reproduces the integrand at every θ. Note
there is never a grid *in* the parameter: the new array lives on the same
kinematic (Q,Y,q_T,b_T) axes, and θ stays a continuous, differentiable
symbol. The NP λ already work exactly this way (I_pert produced with NP off;
C_ν is the cached rule that reattaches exp(C_ν·γ_ν^NP(λ)) for any λ).

The fit evaluates the product of all the
reattached factors simultaneously — the true formula, not a sum of 1-D
responses — and products of factors and exponentials of sums compose exactly.
So every cross term among parameters treated this way (λ×λ, λ×TNP, TNP×TNP)
is automatically correct, at per-parameter cost, with no 2-D scans.

**What each parameter class needs cached:**

- **anomalous-dimension TNPs** (γ_cusp, γ_μ, γ_ν): U(θ) = U₀ + θ·C_i →
  cache the exponent coefficient C_i(Q,q_T,b_T); fit-time factor `exp(θ·C_i)`.
  The γ_ν TNP multiplies the already-cached C_ν.
- **boundary TNPs** (h, s): as the worked example — cache the ratio
  r(Q[,q_T,b_T]); fit-time factor `(1 + θ·r)`.
- **beam TNPs**: linear per beam, per flavor channel; the channel-summed
  B_a·B_b product is degree-2 per θ → SCETlib does the channel sums at
  production and emits linear + quadratic (+ pairwise) coefficient grids,
  again as ratios to the nominal.
- **m_V, Γ_V**: analytic Breit-Wigner prefactor in Q, factored out of the grid.

The fit-time integrand is then I_pert × Π(1+θ·r) × exp(Σθ·C) × [NP closures]:
the existing b_T-grid, quadrature and pipeline are untouched.

Parameters that change the b_T-grid itself, rather than entering one
ingredient, are treated by **interpolating the b_T-grid in α_s**. The full
grid — I_pert, C_ν, and all coefficient arrays — is produced at 3–5 values of
α_s on identical sampling; at fit time the current α_s is turned into
interpolation weights w_k(α_s) and each array is replaced by its element-wise
weighted sum, Ĩ = Σ_k w_k(α_s)·I⁽ᵏ⁾ — each grid entry is a smooth function of
α_s, so a low-order polynomial is accurate. The interpolation is only ever
between α_s versions of the same grid entry; nothing is interpolated in Q, Y,
q_T or b_T (the kinematic sampling stays fixed, the quadrature exact). The
λ/TNP closures then multiply the interpolated grid, so at every α_s the fit
applies the exact closure to the grid appropriate to that α_s — which is
precisely where the α_s×λ and α_s×TNP cross terms enter. PDF Hessian members
enter as per-member grids.
Versus today's α_s templates (final spectra at α_s±δ with all other theory
parameters frozen at central, log-linearly interpolated) this (i) removes
the central-NP-slice approximation of the α_s response, which matters most
exactly where the α_s–NP degeneracy lives; (ii) captures the α_s
self-nonlinearity beyond two-point linearization; (iii) interpolates the
smooth b-space arrays instead of the folded spectrum.

FO scale variations and profile transition points stay as
discrete envelope templates (they reshape the whole grid; not fit
continuously).
The singular-FO expansion is also linear in the TNPs, so the
matching/nonsingular piece gets the same coefficient-grid treatment.

**Resulting cross-term coverage** (diagonal = the parameter's own
nonlinearity):

| | λ NP | resum TNP | h/s TNP | beam TNP | α_s | PDF | FO scales | trans. pts |
|---|---|---|---|---|---|---|---|---|
| **λ NP** | exact (done) | exact | exact | exact | interp | interp | OP | OP |
| **resum TNP** | | exact | exact | exact | interp | interp | OP | OP |
| **h/s TNP** | | | exact | exact | interp | interp | OP | OP |
| **beam TNP** | | | | exact¹ | interp | interp | OP | OP |
| **α_s** | | | | | interp | std² | OP | OP |
| **PDF** | | | | | | std³ | OP | OP |
| **FO scales** | | | | | | | OP⁴ | OP |
| **trans. pts** | | | | | | | | OP |

- *exact* = true functional form via closures, never approximated.
- *interp* = exact in the closure direction, interpolation-accuracy in α_s / per-PDF-member.
- *std* = standard correlated treatment, unchanged from today.
- *OP* = outer-product templates, unchanged — to be audited numerically (we have machinery measuring pairwise non-factorizability of the full prediction).

¹ with the pairwise quadratic grids.
² correlated α_s-series PDF sets.
³ linear Hessian-member combination.
⁴ paired κ×μ_f combos exist discretely.

The residual approximation is confined to the last two columns — a small,
enumerable set; if the audit flags a pair, the targeted fix is one tensor
template, not a redesign.

## What we would ask of SCETlib

1. Promote the b_T-grid export (the NP-off arrays on a fixed, parameter-
   independent quadrature sampling) to a designed API.
2. Per declared fit parameter, emit its **coefficient grid**: exponent
   coefficient (adm TNPs), boundary ratio (h/s), channel-summed polynomial
   coefficients (beam TNPs). Zero-C++ pilot exists: ln-ratio of two NP-off
   integrand grids at θ = 0, 1 is exact (ln I is exactly linear in θ).
3. A reference (numpy) implementation of the fit-time closures could live in
   SCETlib itself — our TF forms are framework-agnostic math.

**Numerics constraints learned the hard way:** fixed quadrature (adaptive
error control is not differentiable), fp64 throughout (the high-q_T Hankel
tail is cancellation-dominated), frozen comparisons in branch masks for
higher-order AD, and expose the low-rank parameter structure for Hessians
rather than trusting generic reverse-mode.

**Proposed pilot:** the γ_ν TNP — coefficient grid ≈ already cached, closure
is one line, and it is the TNP most entangled with λ_ν (both multiply C_ν),
so it directly tests the cross-term claim against existing ±1 templates.
