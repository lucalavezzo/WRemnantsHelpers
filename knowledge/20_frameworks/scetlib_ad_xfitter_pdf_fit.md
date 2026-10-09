# SCETlib-AD as a differentiable observable for PDF + α_s fits

**Status:** feasibility proposal, nothing built. Written 2026-08-27 as a handoff for a
collaborator working on xFitter. An **independent line of work** — a possible extension,
running alongside the α_s measurement, whose nominal fit is unaffected and proceeds as it is.
**Intended first host:** xFitter. **Deliverable:** deliberately framework-agnostic — a
library plus a documented data contract, so another framework either consumes it as-is or
needs only a thin plugin. §4 is that contract.
**Contact:** Luca Lavezzo (lavezzo@mit.edu). Context lives in
`WRemnantsHelpers/studies/scetlib-ad-param-model/`.

---

## 1. What is being proposed, and what is not

We have a version of SCETlib whose matched Drell–Yan prediction — resummation ⊕ fixed order —
is **algorithmically differentiable** in its theory parameters, wrapped so that a q_T–y bin's
cross section is a fast replay of a cached integration rule rather than a fresh adaptive
integral. The proposal is to extend that treatment to the PDF, so a global fitter can use a
**resummed, matched, low-q_T Drell–Yan prediction without calling a generator at every
minimiser step.**

Three things one could mean by "fit PDFs with this", and only the third is worth doing:

| | what it is | verdict |
|---|---|---|
| **A** | fit PDFs to *our* Drell–Yan data alone | already roughly what we do. Our current fit floats 29 PDF eigenvector coefficients with Gaussian priors from a global fit — that *is* a linearised PDF fit with a prior. Z p_T constrains a narrow x range at essentially one scale; 30+ PDF parameters are not determined by it, so the output would largely be a reparametrised prior. |
| **B** | rebuild a global PDF fit inside `rabbit` | **no.** Not because of the likelihood — `rabbit`'s nuisance machinery is fine, sum rules go in the parametrisation, positivity goes in as a penalty. Because of the two things we would have to own and have no reason to: the **curated dataset library** with its correlated systematics, and **DIS coefficient functions with a heavy-quark scheme**. Without DIS it is not a global fit. |
| **C** | expose SCETlib-AD as an observable *to* a global fitter | **this one.** The value is precisely the data we do not have. Global fits today either cut low q_T or use fixed order there, because resummation meant a generator call per step. A differentiable matched prediction removes that. |

So what a host framework buys us is **the rest of the world's data and the machinery that
makes it usable** — nothing else, and that is enough.

**A side benefit, worth knowing when weighing the cost.** The §3.1 work would also tidy our
own machinery: it removes a 14 h cache build, makes PDF dependence exact rather than a
3-point interpolation, and removes the μ_F interpolation residual described in §3.2. That is
an upside if this is pursued — not something the α_s measurement is waiting on.

---

## 2. What exists today

SCETlib branch `autodiff-sigmaul`, differentiated by **clad** (source transformation, not
finite differences), driven from WRemnants through
`wremnants/postprocessing/scetlib_ad/`.

**The prediction.** Matched: resummed at N³⁺⁰LL ⊕ non-singular (NNLO fixed order minus its
own singular expansion). Single run, both pieces on one shared outer node set. The
non-singular is taken to vanish below q_T = 0.1 GeV (its exact q_T → 0 limit).

**Parameters.** 53 in the current Z cache, in two classes, and the split is the crux of this
whole document:

| class | members | how the derivative is obtained |
|---|---|---|
| **on the AD tape** | non-perturbative λ (CS and TMD form factors), 9 resummation TNPs, κ_R, matching transition points | exact, from clad |
| **served by discrete members** | 29 PDF eigenvectors, α_s, μ_F | interpolated between pre-built samples |

The split is not a preference. A PDF member is a *numerical grid*; there is nothing to
differentiate through. So PDF, α_s and μ_F are handled by building the cache at sampled points
and interpolating (3-point Lagrange quadratic; at ±1σ the interpolant returns the stored
member bit-for-bit).

**The cache.** For each bin, SCETlib's adaptive quadrature runs once at an anchor parameter
point and the integration it chose is recorded: the outer (Q, y, q_T) nodes, the inner b_T
ladder, every weight — plus, at each node, the **PDF ⊗ beam-function convolutions frozen as
numbers**. At fit time nothing is integrated:

```
σ(bin; θ) = Σ_nodes  w_node × [ frozen(node) ⊗ analytic(node; θ) ]
```

For a 210-bin Z card:

| | |
|---|---|
| cache on disk / uncompressed | 2.13 GiB / 12 GiB |
| per bin | ~59 MB, ~360 integration nodes |
| exact at the anchor | ~8×10⁻¹⁵ (it is a replay of the same sum) |
| full value + Jacobian (53 params) | ≲3 s |
| **build cost, 62 members** | **~14 h, of which the fixed-order member sweep is 97%** |

62 members = 29 eigenvector pairs + the α_s pair + the μ_F pair. Each costs 13.7 min, because
it refills every frozen node at the new PDF.

**Validation, so the accuracy claims are not hand-waving.** Against the production theory
templates over 97 variation directions: worst 4.1×10⁻³, median 2.9×10⁻⁴ for q_T > 1 GeV.
Against a *direct live SCETlib evaluation* — a reference with no template floor — the 28
directions that route can serve agree to **≤7.7×10⁻⁵**, i.e. 0.00–0.01% of their own response.
Folded through a response matrix to 780 reco bins, the central prediction closes at 0.128%.

**Why it cannot fit PDFs as it stands.** The PDF is baked into a number, and
`set_pdf_keep_nodes` exists to re-bake it at 13.7 min a shot. Sixty-two pre-baked choices with
a quadratic interpolant is a fine model of PDF *uncertainty propagation* in a fixed eigenbasis
and useless for *determining* PDFs.

---

## 3. The physics work

### 3.1 SCETlib must return the kernel, not the convolution — this is the whole job

The beam function at a node is a convolution, and it is **linear in the PDF**:

```
B(node) = Σ_j ∫ dz  I_ij(z, b_T, μ)  f_j(x/z, μ)
```

`I_ij` is analytic and PDF-independent; only `f_j` varies. Insert an interpolation basis for
`f` and the convolution becomes a contraction:

```
B(node) = Σ_k  W_k(b_T, μ)  f(x_k, μ)
```

The weights `W_k` are computed once at build time and never again. Any PDF then contracts in
**exactly** — no interpolation error, no member limit.

**Be precise about the algebra, because it decides the grid's shape.** The *beam function* is
linear in the PDF, but the *cross section* carries one beam function per incoming direction,
so σ is **bilinear** in the PDF — quadratic, in `f(x₁) × f(x₂)`. That is exactly why standard
grid formats are indexed by (x₁, x₂). It does not make derivatives expensive: ∂σ/∂f is the
other beam's contraction, available at the same cost as the value. It does mean "linear in the
PDF" is wrong shorthand and should not be used with anyone who fits PDFs for a living.

This is the interpolation-grid technique that makes PDF fits fast in the first place. The work
is inside SCETlib's beam functions: today they hand back the convolution and they would need
to hand back the weights. **A real internals change, not a wrapper** — and the item on which
the whole idea stands or falls.

### 3.2 An evolution operator, because μ moves from node to node

This is why a resummed grid is harder than a fixed-order one. A fixed-order grid needs the PDF
at a handful of scales. A resummed calculation needs it at **μ_B(b_T) — a different scale at
every b_T node**, sweeping from ~M_Z down toward the non-perturbative region.

So an (x, μ) grid alone is not enough. You want a precomputed evolution operator,

```
f(x, μ_node) = E(μ_node ← μ₀) · f(x, μ₀)
```

so that everything stays a contraction and PDF-parameter derivatives fall out of it. Several
existing tools provide exactly this (EKO among them) and it should be adopted, not rebuilt.

The cheaper route is to let the host's own evolution (QCDNUM, APFEL) supply `f` on the grid
each iteration. Easier — but then PDF derivatives are the host's numerical ones, and the
property that makes this model worth coupling to has been given away.

**This is also where our worst current residual dies.** The μ_F error is amplified 9–12×
because the explicit `ln(μ_B/μ_F)` in the matching coefficients cancels against the PDF's
DGLAP evolution, and today we do the first analytically and the second by interpolating three
members. With a grid plus an evolution operator, both halves are exact and the cancellation is
clean.

### 3.3 α_s split by perturbative order

α_s enters three places: the resummation kernel (already on the tape, exact), the evolution,
and the hard and matching coefficients. For the latter two, store the grid per order and
contract with α_sⁿ at fit time. Standard — and half-validated already: our fixed-order α_s
expansion closes to **≤0.7%** doing exactly this, with the per-order pieces already on disk.

---

## 4. The interface contract — built host-agnostic on purpose

The deliverable should be a **library plus a documented artifact layout**, not an xFitter
plugin with a library hidden inside it. xFitter is the first consumer; anything else should
need only a thin adapter. Concretely, two phases:

**Build phase, once per binning + runcard.** Emit a serialisable artifact containing, per bin:
the outer nodes and quadrature weights, the b_T ladder, the per-node x-grid weight tensors
`W[flavour, x_k]` with the μ each node requires, and per-order pieces for α_s. Document the
layout so a reader outside SCETlib can parse it — this is what makes "out of the box" possible.

**Evaluate phase, once per iteration.** Inputs: a PDF, supplied either as values on the
requested (flavour, x_k, μ_node) grid or as `f(x, μ₀)` plus an evolution operator; α_s; the
theory-parameter vector. Outputs, all optional so a host takes only what it can use:

| output | why a host wants it |
|---|---|
| σ per bin | the prediction |
| ∂σ/∂f | **exact PDF gradients, from the contraction itself** |
| ∂σ/∂α_s | joint α_s fitting |
| ∂σ/∂θ for the NP λ, TNPs, κ_R, transitions | clad — the part no other framework can get |

**The consequence worth flagging to any host author.** Because σ is a contraction against the
PDF, **exact analytic PDF gradients come for free, whether or not the host does autodiff.** A
MINUIT-based fit on numerical derivatives can still be handed exact ∂σ/∂f. That materially
softens the concern that a non-differentiable host wastes this work: what such a host loses is
not the PDF gradients but the *theory-nuisance* gradients — and those are what let the
non-perturbative and resummation parameters float in the same fit rather than being frozen or
scanned.

Design rules that keep it agnostic, and they are cheap if adopted from the start:

- no host types in the library's public API — arrays in, arrays out
- the artifact layout documented and versioned, readable without SCETlib
- the host chooses whether it supplies evolved PDFs or an evolution operator
- every derivative optional, requested by flag, never mandatory
- bin definitions passed in, never inferred from a host's data format

---

## 5. Risks and open questions

1. **Can SCETlib expose `W_k` at all?** If the beam functions cannot be refactored to return
   weights, everything above is dead. Answer this first (§6).
2. **Grid density over a wide μ range.** What (x, μ) resolution reproduces a b_T integral to
   1×10⁻⁴ when μ_B sweeps from M_Z to the non-perturbative floor? Unknown, and it drives both
   size and accuracy.
3. **How low does μ_B go?** In our current configuration `b0_over_bmax_global = 0`, so
   b̄ ≡ b_T and μ_B is *not* saturated at large b_T. Evolving a PDF to arbitrarily low μ is
   unphysical, so a grid build almost certainly needs the b\* prescription switched on. We have
   never had to face this because the frozen convolutions absorbed it.
4. **The node set is frozen at the anchor.** That is the cache's one real approximation, and in
   a PDF fit the PDF moves *by design*. It deforms the integrand less violently than the
   non-perturbative λ do, but "less violently" is not "negligible" and it needs measuring.
5. **Size.** You trade 62 members for (flavours × x₁ × x₂) weights per node. Could be smaller,
   could be much larger. Measure, do not guess.
6. **Cache builds are not bit-reproducible.** The adaptive outcome depends on which bins shared
   a TBB thread, putting a floor of ~1×10⁻⁴ on values and ~3×10⁻³ on displaced Jacobians for
   any comparison *between two separately built caches*. Validation plans must respect that
   floor. See `scetlib_ad_cache_build_parallelism.md`.

---

## 6. Suggested order of work

**Stage 0 — one day, and it is a go/no-go.** One bin, one node. Check that
`Σ_k W_k f(x_k)` reproduces the stored convolution to target precision for two or three known
PDFs. If the kernel cannot be extracted, a day is lost instead of a month. Framework-independent.

**Stage 1 — the fixed-order piece first.** Ordinary collinear factorisation, exactly what grid
formats were built for, *and* where nearly all the member-loop cost lives (97%). Largest win,
smallest risk, and it stands alone: a gridded non-singular piece is useful even if the resummed
half is never done.

**Stage 2 — the resummed beam functions.** The hard part, for the μ_B(b_T) reason in §3.2.

**Stage 3 — adopt an evolution operator**, so PDF parameters are differentiable end to end
rather than numerically differenced.

**Stage 4 — the xFitter reaction module**, as the first consumer of the §4 contract.

Note that **the host choice is only needed at Stage 4.** Stages 0–3 are the same work whoever
consumes it, which is the point of §4.

---

## Appendix A — the NNPDF stack (Colibri / PineAPPL / EKO) as an alternative host

**Not a proposal to switch.** Recorded because it changes what Stage 4 costs, and because a
host-agnostic §4 makes the choice reversible. The description below is written from general
knowledge of that ecosystem and **may be out of date or wrong in detail — verify before acting
on it.**

Colibri is a PDF-fitting framework on the NNPDF stack: PineAPPL interpolation grids, EKO
evolution operators, JAX underneath, and support for Bayesian inference alongside
gradient-based optimisation.

**What it would collapse.** §3.2's evolution operator is EKO, used as-is. And a JAX host
consumes the theory-nuisance gradients too, not just the PDF ones that §4 gives away for free —
which is the difference between "faster" and "a joint fit that converges with the
non-perturbative sector floating".

**A physics argument with nowhere else to live.** Bayesian inference returns a PDF *posterior*
rather than a Hessian. That matters here specifically: the non-perturbative likelihood is known
to be **multimodal, with an unphysical global optimum** that we currently exclude with a damping
wall at Δχ² ≈ 16.6 (`studies/np-wall-local-minima/`). Profiling that against PDFs under a
Gaussian approximation is precisely the case where a Hessian misleads.

**The catch: grid-native is not the same as "our prediction fits in a standard grid".** A
PineAPPL grid is, per bin and per order, weights over (x₁, x₂, μ²). It has **no axis for a b_T
node**. Our structure is a b_T ladder with μ_B varying node to node, and κ_R and the matching
transition points sit on the AD tape *precisely because* they move μ_B per node.
Pre-integrating b_T to fit the format at fixed profile scales would freeze exactly the
parameters we worked hardest to make differentiable. So the realistic shape is: EKO for
evolution, grid-style weights for the x-convolution at each node, and the b_T contraction held
in the host's autodiff layer as a custom observable.

**Also to verify before treating xFitter's maturity as a non-advantage:** that the available
dataset collection covers what a competitive α_s determination needs. Case C's entire value is
the data we do not have.

**The counterweight is non-technical**, and not ours to weigh: the expertise in play is xFitter
expertise, switching frameworks spends someone else's time, and if this becomes a published
determination then community acceptance is a real consideration.

---

## Pointers

| what | where |
|---|---|
| the model as rabbit sees it | `wremnants/postprocessing/scetlib_ad/param_model.py` |
| parameters, priors, defaults | `wremnants/postprocessing/scetlib_ad/params.py` |
| cache build, and why bins split but members do not | `scripts/rabbit/scetlib_ad/build_cache_parallel.py` |
| cache format reader | `scetlib-cms/py/scetlib_cache.py` (SCETlib MR !10) |
| build parallelism, reproducibility floor | `knowledge/20_frameworks/scetlib_ad_cache_build_parallelism.md` |
| differentiable scales, and which are wrong | `knowledge/20_frameworks/scetlib_diff_scales_caveats.md` |
| validation set and its numbers | `studies/scetlib-ad-param-model/260827-authoritative-validation/` |
| study logbook | `studies/scetlib-ad-param-model/LOGBOOK.md` |
