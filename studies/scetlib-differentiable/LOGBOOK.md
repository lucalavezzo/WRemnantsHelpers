---
title: Differentiable predictions in SCETlib proper
slug: scetlib-differentiable
status: active
created: 2026-07-08
updated: 2026-07-08
---

# Differentiable predictions in SCETlib proper — logbook

**Goal:** design, with the SCETlib author, how to port the WRemnants NP
param-model ideas (differentiable predictions w.r.t. fitted parameters) back
into SCETlib itself, and extend differentiability beyond the NP λ to the other
parameters we typically fit (α_s, TNPs, m_V/Γ_V, PDF nuisances).

---

## START HERE (status as of 2026-07-08)

> **Discussion phase — two documents drafted.** `PROPOSAL.md` = the physics
> case (factorized closures, cross-term matrix, asks, γ_ν TNP pilot).
> `ARCHITECTURE.md` = the software design (scetlib.fit package layout, API +
> schema contracts, C++ accessors, numerics rules, CI, P0–P4 phasing, open
> questions for the authors). Ownership decided: reassembly/reconstruction
> lives in SCETlib (numpy reference normative, tf backend); WRemnants keeps
> Steps 3–4 (R fold, rnorm, rabbit, J/K Hessian). `index.html` in this dir
> renders the .md files when the dir is symlinked into public_html.

- **Next action:** Luca reviews/edits `PROPOSAL.md`, sends to SCETlib author;
  optionally pre-arm with the θ=±2 linearity smoke test and one N_ab
  cross-class pair (TNP×λ) for a measured motivation number.
- **Blocking on:** author discussion.

---

## Log

### 2026-07-08 (latest) — implementation sketch (discussed, not built)
- Three layers: (1) SCETlib: new accessors (tnp_exponent_coeff /
  tnp_boundary_ratio / tnp_beam_coeffs, siblings of gamma_nu_NP_log_coeff) +
  bt_grid_v2 shard schema; pilot needs ZERO C++ (ln-ratio of θ=0,1
  resummed_bT_integrand runs). (2) cache: combined pickle + factorized.npz
  gain per-param arrays; resum-TNP coeffs share C_ν's degeneracy (sub-dedup
  table, ~30MB each); beam TNP grids are the memory item (full (Nu,Nbt)
  footprint each); α_s knots = ×K constants (~14GB at K=3) → GPU budget redo.
  (3) fit model: one-line change in reconstruct_batch_factorized_tf
  (extra exponent terms + multiplicative brackets on M); params.py registry
  grows; TNPs need N(0,1) constraints on ParamModel params (rabbit design
  item — NPDampingWall shows penalties pluggable, proper constraint cleaner);
  σ_ns per-TNP linear coeffs from varied _nnlo_sing files; J/K straight-
  through just widens (8→~25 params, K pairs 36→~300, still one-off eager).
- Phasing: γ_ν TNP pilot (days, no C++, validate vs conf [17]/[18] + θ=±2 +
  injection fit) → other resum TNPs + h/s via ln-ratio → C++ accessors/schema
  (the SCETlib deliverable) → beam TNPs + σ_ns → α_s knots. Pilot evidence
  lands BEFORE the API discussion must conclude.

### 2026-07-08 (later still) — variation-class audit
- Audited the full variation set we take from SCETlib
  (`/work/submit/lavezzo/alphaS/TheoryCorrections/SCETlib/com13_msht20an3lo_newnps_n4+0ll_lattice_newvals_coarse/variations_lattice_allvars.conf`
  + α_s / pdfvars files) against the factorization taxonomy.
- CONFIRMED in source: every TNP enters exactly linearly —
  `coeff*(1.+theta)` in `include/scetlib/core/TNPs.hpp` (TNP_adm anomalous-dim
  + TNP_bc boundary variants); qT TNP container in `include/scetlib/qT/TNPs.hpp`
  (gamma_cusp, gamma_mu_q, gamma_mu_g, gamma_nu, s, b_qqV/qqbarV/qqS/qqDS/qg…).
- Classification: EXACT-CLOSURE class = λ NP (done) · resummation TNPs
  γ_cusp/γ_μq/γ_ν (evolution-exponent coefficient grids, C_ν pattern verbatim)
  · h_qqV (Q-only ratio grid) · s (ratio grid, C_ν footprint) · beam TNPs
  (exact but hardest: per-flavor-channel B_a·B_b product → degree-2 polynomial
  in each θ; route = SCETlib does channel sums at production, emits
  linear+quadratic(+pairwise) coefficient grids — avoids 9× channel storage).
  KNOT class = α_s (3–5 integrand-level knots), PDF members (per-member grids —
  the shard layout already is this). LEAVE-AS-TEMPLATES = FO scales
  κ_FO/κ_f/μ_f (DGLAP blocks a closure; interlocked with paired DYTurbo scale
  grids) and transition points (reshape the kernel + dedup structure; envelope).
- KEY FIND: the γ_ν TNP shares the already-cached C_ν rapidity-log coefficient
  (it shifts γ_ν^pert multiplying the same logs as γ_ν^NP) → near-zero-cost
  pilot: closure exp(C_ν·θ·δγ_ν⁽ⁿ⁾(b*)), only new object is δγ_ν⁽ⁿ⁾ on the grid.
  Also physically the TNP most entangled with λ_ν.
- Caveat for ALL exact classes: the singular-FO expansion (hence
  σ_ns = DYTurbo − sing-FO) is also linear in θ → needs its own coefficient
  grids, else the closure is only exact where resummation dominates.
- Proposed attack order: γ_ν TNP pilot → γ_cusp/γ_μq → h,s → beam TNPs (+σ_ns
  terms) → α_s knots → PDF members. Pre-work: (i) θ=±2 linearity smoke test
  vs ±1 templates; (ii) N_ab cross-term audit on cross-class pairs
  (TNP×λ, α_s×TNP) to measure which cross terms templates actually get wrong.

### 2026-07-08 (later) — genericity framing
- Luca's point: per-parameter knot grids (e.g. I_pert/C_ν at α_s up/down) fix
  α_s×λ but are not generic; the real failure mode of the template approach is
  the OUTER-PRODUCT assumption on the joint response (λ×λ was just the first
  pair to break it).
- Framing settled for the author discussion: **the SCET factorization theorem
  IS the differentiability structure.** σ ~ H·B·B·S·exp(U)·F_NP is a product
  of factors and an exp of sums, so any parameter living inside ONE ingredient
  (linearly or in the exponent) gets EXACT JOINT dependence with all others of
  that kind from per-parameter cached objects — no tensor grids. Tier 1 = NP λ,
  anomalous-dim TNPs (exponent coefficient grids, the C_ν pattern), boundary
  TNPs (factor-linear ratio grids), m_V/Γ_V (analytic BW prefactor in Q).
- Design consequence (CLARIFIED 2026-07-08 late): I_pert/C_ν stay collapsed
  exactly as today — we do NOT export H/B/S separately. Each parameter adds
  one coefficient grid RELATIVE to the nominal (ratio δX/X₀ for boundary
  TNPs, exponent coefficient C_i for resummation TNPs); the factorization
  theorem only DERIVES what each coefficient is. Fit-time integrand =
  I_pert × Π(1+θ·r) × exp(Σθ·C) × existing NP closures — pipeline untouched.
  Only the beam TNPs need SCETlib to look inside a product at production
  (flavor-channel sums for the linear/quadratic coefficients), but the export
  is still ratio grids vs the nominal.
- Tier 2 (kernel-revaluing: α_s, PDF member, profile shape) = knot grids;
  Tier2×Tier1 cross terms exact at each knot; the ONLY residual approximation
  is Tier2×Tier2 (small enumerable set — α_s×PDF via correlated sets; audit
  the rest with the N_ab factorizability machinery). Tier 3 = differentiable
  kernel rewrite, only needed if the audit fails.
- Caveats recorded: nonsingular/matching (DYTurbo−sing FO) also Tier-2
  dependent → per-knot FO inputs; quadrature grids must be parameter-
  independent (export contract); dedup degeneracy depends on profile
  transition points.

### 2026-07-08
- Read-up session. Key structural insight to carry into the discussion: the
  WRemnants model works because the fitted λ enter the bT integrand only as
  (a) a multiplicative factor F_eff and (b) a coefficient-times-parameter
  exponent C_ν·γ_ν^NP — everything else is cached λ-independent
  (I_pert, C_ν, b*, J₀ kernel, Simpson weights). Differentiability was
  obtained by transcribing only the cheap closures into TF, on a FIXED
  quadrature grid.
- Taxonomy of how fitted parameters enter σ (candidate generalization):
  multiplicative-in-b (NP F factors, exact, done) · exponent-linear
  (γ_ν^NP-like; TNPs in anomalous dims) · linear-in-coefficient (TNPs in
  matching/hard coefficients) · analytic kinematic factors (m_V, Γ_V via BW)
  · genuinely nonlinear-global (α_s, PDF) → local Taylor/derivative grids.
- SCETlib fork already has the needed decoupling accessors
  (`py/qT/DrellYan.hpp:170-185`: `resummed_bT_integrand`,
  `gamma_nu_NP_log_coeff`, `b_star_global`) plus `prod/scetlib_run/`
  (config/factorize/grid/variations) with the pure-numpy NP transcriptions.
- Engineering lessons worth porting (from docs/FACTORIZED_RECON.md and
  docs/HESSIAN_PLAN.md): fixed quadrature (adaptive error control is not
  AD-friendly), fp64 throughout, `stop_gradient` on branch masks for nested
  forward-mode, low-rank straight-through J/K for Hessians, dedup/memory
  factorization of cached grids.

---

## Findings

### Cross-term matrix (2026-07-08)

How each pair's cross term is handled under the proposed scheme.
Legend: EXACT = true functional form via closures, never approximated ·
KNOT = exact in the closure direction, interpolation-accuracy in α_s /
per-PDF-member · STD = standard correlated treatment (α_s-series PDF sets,
linear Hessian combination — same assumption as today) · OP = outer-product
templates, unchanged, must be audited (N_ab).

| | λ NP | resum TNP | h/s TNP | beam TNP | α_s | PDF | FO scales | trans. pts |
|---|---|---|---|---|---|---|---|---|
| λ NP | EXACT (done) | EXACT | EXACT | EXACT | KNOT | KNOT | OP | OP |
| resum TNP | | EXACT | EXACT | EXACT | KNOT | KNOT | OP | OP |
| h/s TNP | | | EXACT | EXACT | KNOT | KNOT | OP | OP |
| beam TNP | | | | EXACT¹ | KNOT | KNOT | OP | OP |
| α_s | | | | | KNOT² | STD³ | OP | OP |
| PDF | | | | | | STD⁴ | OP | OP |
| FO scales | | | | | | | OP⁵ | OP |
| trans. pts | | | | | | | | OP |

¹ needs the pairwise quadratic coefficient grids (10 for 5 TNPs), else OP.
² diagonal = α_s self-nonlinearity, captured by knot interpolation.
³ dominant part via the correlated α_s-series PDF sets, as now.
⁴ linear Hessian-member combination, standard PDF assumption, unchanged.
⁵ partially covered discretely by the paired κ_FO×κ_f×μ_f templates
  (conf [40]/[41]).

Reading: the entire λ+TNP block becomes exact by construction (where λ×λ broke
and where correlations are strongest, e.g. γ_ν TNP × λ_ν sharing C_ν); α_s and
PDF become exact against that block (the α_s×λ fix, generalized). Residual OP
is confined to FO scales + transition points vs everything — the set the N_ab
audit must price; a targeted tensor template is the fallback if a pair fails.

### α_s/PDF knots work because the kernel is NP-free
The btgrid is produced with force_np_off — no λ imprint in I_pert/C_ν
(λ_central enters only as the fit-time rnorm denominator). So per-α_s-knot /
per-PDF-member kernels carry the FULL λ/TNP closure at any parameter value;
interpolate the GRIDS pointwise in α_s (smooth, differentiable), closures on
top. Only approximation = kernel interpolation in α_s. σ_ns needs per-knot /
per-member FO inputs too.

### TNP closures need no TF transcription
TNPs are exactly linear in their ingredient (`coeff*(1.+theta)`), so the
fit-time factor is exp(θ·C_i) (resum TNPs) or (1+θ·r) (boundary TNPs) — the
perturbative content lives entirely in the cached kinematic coefficient grid.
Coefficient extractable with zero C++ changes: ln-ratio of two NP-off integrand
grids at θ=0,1 (exact, since ln I is exactly linear in θ); θ=2 run as the
leak check. Dedicated accessor (sibling of gamma_nu_NP_log_coeff) is the tidy
long-term route.

## Decisions

(none yet)
