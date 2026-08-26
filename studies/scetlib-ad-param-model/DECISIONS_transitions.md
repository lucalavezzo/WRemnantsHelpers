# scetlib_ad — decision record, TRANSITION-POINT round (analytic muF, end to end)
# 2026-08-26 (autonomous). STAGED for merge into DECISIONS.md.
# Numbering continues from D-030 of the analytic-muF block.
# Format: WHAT was decided, WHY, WHAT EVIDENCE, WHAT WOULD OVERTURN it.
#
# REGIME on every number below:
#   FINITE variation       x2 = 0.35 / 0.75, x1,x3 = 0.3,0.9 -- what the
#                          production templates carry.
#   NEAR-ANCHOR derivative x2 = 0.55, ~12x smaller -- what a FIT uses.
# Reference throughout: an EXACT runcard refill (the transition points written
# into the card, so SCETlib recomputes the beam convolutions at the shifted
# muF), |Y| [0, 0.15], live rules, n_train = 9, target_precision_rel = 1e-4.
# All arms of every A/B run in ONE process off ONE rule build and ONE reference.
#
# WHERE THE WORK IS: worktree /work/submit/lavezzo/alphaS/scetlib-anltrans,
# branch muf-analytic-trans off eb60a04, builds build-anltrans (ablations) and
# build-anltrans2 (ablations + the c_i1 evolution term). scetlib-cms, build-fix,
# build-knots, build-trans, build-nak, build-5knot and build-anlmuf were NOT
# touched. The anlmuf prototype was imported as commit 43342cd so it has a
# commit to build on; the anlmuf worktree still holds it uncommitted.

---

## 2026-08-26 session — the analytic DGLAP route, taken to sigma

### D-031 — The prior round's runcard-reference measurement EXISTS, was never
###          written up, and it changes the reading of the route — SETTLED

`~/public_html/alphaS/260826_analytic_muf_dglap/00_README.txt` promises its
sigma-level attribution in "sections 8-9", stops at section 7, and its
`runcard_ref/` directory is EMPTY. The measurement itself ran to completion at
01:01 that night and is on disk:
`.../jobs/140d052c/tmp/anlmuf/interp_{x2_035,x2_055,x1x3,x2_075}.json` +
`interp_queue.log`. Four variation points, modes 0 / 1 / 3, arms separated
(8.1e-04 and 7.5e-04 on the varied point, **0.000e+00** on the central one).

**It says two things the CorrZ closure cannot.**

1. **mode 3 == mode 1** to 1-2 percentage points of the response in every bin of
   all four variation points. Example, x2 = 0.35, dev as % of the true response:

   | qT | mode 0 | mode 1 | mode 3 |
   |---|---|---|---|
   | [20,24] | -31.6% | -39.2% | -38.1% |
   | [24,28] | +10.9% | **+3.0%** | +3.9% |
   | [28,33] | +9.2%  | **+4.8%** | +5.1% |
   | [33,44] | +1.5%  | **-0.8%** | -0.8% |

   **DECISION: do NOT build a mode-3 cache.** The 16 extra beamfunc grid
   families (~260 MB), the conv prefix 11 -> 15 and the full node REBUILD that
   mode 3 needs buy nothing at the sigma level, and in two bins of two points
   mode 3 is marginally WORSE. The conv-level tier table of D-027 (median
   0.406% -> 0.322%, worst 51% -> 20%) does not survive the bT integration.
   That saves the single most expensive item on the route's cost list.

2. The route is a large win at qT >= 24 and a consistent loss at qT <= 24, and
   the loss is the SAME SIZE at every variation size and both signs (-7.6 to
   -8.8 percentage points of the response). A constant fraction of the response
   is the signature of a missing FIRST-ORDER response, not of an interpolation
   remainder, which would scale as D^2 or D^3.

**Overturned by:** nothing about mode 3 short of a different observable; the
mode-1-vs-mode-0 numbers are re-measured independently below and reproduce.

### D-032 — `node_cval` and the discarded `rule.c_grad` are BOTH CLOSED as
###          candidates for the residual — SETTLED (measured, 4 orders down)

`rule_cvals()` extended to expose `c_grad` (the gradient of the rule's
compression residual, which the STAGED replay throws away: with variation
members present `sigma_binned_rule_batch` replaces the constant by
`node_cval(p)`, whose gradient runs only over the member coordinates, so
`d c/d x2 == 0` identically, whereas the un-staged branch adds `rule.c_grad`).

Measured on the runcard-reference bins, x2 = 0.35:

| qT | c_val / sigma | c_grad . dp / sigma | as % of the response |
|---|---|---|---|
| [18,20] | +2.3e-05 | -3.0e-14 | +0.0% |
| [20,24] | -1.6e-05 | -5.7e-12 | +0.0% |
| [24,28] | +9.7e-07 | -8.0e-11 | +0.0% |
| [28,33] | -7.8e-08 | -9.5e-10 | +0.0% |
| [33,44] | +7.5e-06 | -3.7e-09 | +0.0% |

A frozen constant dilutes the response by exactly `c_val/sigma`, so node_cval
can account for at most **2.3e-05** of the response -- against a shortfall of
0.32 of it. **Four orders of magnitude too small.** The discarded `c_grad` term
is 1e-14 .. 4e-09 of sigma, smaller again.

**This RETIRES the standing "node_cval is 10-40% of the shortfall" estimate**
and the open experiment D-021 named ("zero the node_cval member interpolation
and re-measure"). The earlier bound was the member SPREAD `max|dc|/sigma =
2.3e-4 .. 3.2e-4`, which is a bound on the kappa_F response of the constant, not
on its transition response -- and the transition response of a constant with no
bT node is not small, it is ZERO, so the only thing that matters is its SHARE of
the bin, which is 2e-5.

**Overturned by:** a bin where `c_val/sigma` is O(0.1). None of the 5 diagnosed
bins, at two variation sizes, is within 4 orders of that.

### D-033 — The ~9x RG cancellation is now MEASURED at the sigma level, per bin
###          — SETTLED

New diagnostic ablation `DrellYan.set_muf_ablate(mask)` (ad_data.hpp,
`ad_muf_abl`, non-thread_local): bit 1 drops the member interpolation of the
beam CONVOLUTIONS, bit 2 drops it for the per-SITE rule weights, bit 16 freezes
the explicit ln(muB/muF) of the beam matching coefficients at the ANCHOR
transition points (`Lf -> Lf + mfk_live`, which is exactly `log(muB_lf/mf_0)`
and so removes the muF transition dependence and keeps the muB one). Bits 1|16
remove the transition response of the whole muF sector: `s_muf_lf` enters
`node_value` ONLY through `lf_` and `mfk_live`, so the ablation is complete, not
approximate. Every mask is a 0/1 MULTIPLIER, so at mask 0 every expression
reduces term for term to what it was -- and the central value is 0.000e+00
different in all arms, which is the no-op proof.

x2 = 0.35, each half as a multiple of the NET true response:

| qT | true resp | Lf half | conv half | site weights |
|---|---|---|---|---|
| [18,20] | -4.1e-04 | -9.99 | +9.66 | +0.06 |
| [20,24] | -3.1e-03 | -8.60 | +8.57 | -0.01 |
| [24,28] | -7.8e-03 | -9.70 | +9.86 | -0.08 |
| [28,33] | -1.8e-02 | -7.43 | +7.40 | +0.02 |
| [33,44] | -3.3e-02 | -5.91 | +5.84 | +0.01 |

So the two halves are **+-(5.8 .. 10.0) x the net**, they cancel, and a 1%
error in either half is a 6-10% error in the answer. The precision demand on the
convolution half is therefore ~0.3% for a 3% answer -- which is the whole
motivation for doing the second half analytically too. The per-site weight
interpolation is a genuine but minor term, <= 8% of the response.

**Overturned by:** nothing; it is a direct measurement with an exact no-op
control.

### D-034 — REFUTED: the low-qT loss is NOT a collapsed-stencil numerical
###          blow-up — SETTLED (measured, and it was the leading hypothesis)

The five-knot round's wide-geometry failure was traced to the muf_min floor
collapsing the knot positions "at qT just above x1*Q, where their DIFFERENCES
are pure rounding", and `ad_nd.conv` is stored as FLOAT. The natural hypothesis
was that the same collapse degrades the three-knot stencil at exactly the qT
where the loss appears, with the Lagrange weights diverging like
`d^2/(m_up m_dn)` against nearly-equal float convolutions.

**Measured and false.** `stencil_conditioning.py` (pure arithmetic from
`scales_formulas.hpp`; no SCETlib, no cache) evaluates the three positions and
the three weights per bT node. Worst case over qT = 19..38 and bT = 0.05..8 at
x2 = 0.35: **max |w| = 2.5**, and the float-epsilon noise floor the weights
impose is 6e-08 .. 3.6e-07 against a node response of 5.6e-05 .. 4.1e-02, i.e.
noise/response <= 1e-3 everywhere. The positions DO collapse (at qT 19, bT 8:
m_dn = -7.1e-03, m_up = +1.4e-02 against ln f = 0.69) but the displacement D
collapses with them (D = +2.3e-02), so `d/|m_up|` only reaches 1.6 and the
weights stay O(1).

**Consequence:** the guard fix that the five-knot branch carries (relative
rather than absolute degeneracy tolerance) is NOT needed for the three-knot
production stencil, and the low-qT loss has to be explained by something else.

**Overturned by:** a node geometry with |D| >> |m_up|, |m_dn| by orders rather
than by 1.6 -- which the anchor-vs-template geometry does not produce.

### D-035 — REFUTED: the low-qT loss is NOT the model's frozen NONSINGULAR
###          — SETTLED (measured, matched vs resummed-only)

`fo_node_value` depends on kappa_R, alphaS and kappa_F and on nothing else, so
the model's fixed-order half has IDENTICALLY ZERO transition response, while the
runcard's nonsingular (fixed order minus the profiled singular expansion) has
one. That made the frozen nonsingular the natural second suspect.

**Measured and false where it matters.** The whole attribution re-run with
`calculation_piece = sing` (no nonsingular in either arm; `configure` and
`prepare` had to be made sub-piece-optional, since both live on the matched
wrapper):

| qT | matched shipped / anl1 | sing-only shipped / anl1 |
|---|---|---|
| [18,20] | -26.6% / -35.4% | **-26.6% / -35.4%** |
| [20,24] | -31.9% / -39.5% | **-31.9% / -39.4%** |
| [24,28] | +10.9% / +3.0%  | +23.7% / +15.8% |
| [28,33] | +5.5%  / +1.0%  | +11.8% / +7.4%  |
| [33,44] | +2.7%  / +0.4%  | +1.5%  / -0.8%  |

The two low-qT bins are IDENTICAL to 0.1 percentage points, so the nonsingular
contributes nothing to the loss there. It does matter at qT 24-33, where the
matched error is about HALF the resummed-only one -- i.e. the frozen nonsingular
partially CANCELS the resummed error in the matched calculation. That is luck,
not design, and worth knowing, but production is matched so the matched column
is the one to quote.

**Also from that run, two bins that were never measured:** [16,18] true response
9.1e-05 and [14,16] 1.3e-05, both at or below the "do not diagnose below 1e-4 of
sigma" line, and both duly nonsensical (-12.6% and -120.8%). And [44,100],
which IS usable: +0.4% shipped, -2.3% mode 1 -- inside the run-to-run scatter of
D-037, so no claim either way.

### D-036 — WHAT THE ROUTE DELIVERS. Mode 1 closes the transitions in
###          qT 24-44 by 3.6x to 6.8x and leaves qT 20-24 worse — SETTLED

Four variation points, three regimes, one process each, against the exact
runcard refill. dev as a % of the direction's own true response:

| qT | x2=0.35 | x2=0.75 | x2=0.55 (a FIT) | x1,x3=0.3,0.9 |
|---|---|---|---|---|
| | ship -> anl1 | ship -> anl1 | ship -> anl1 | ship -> anl1 |
| [18,20] | -26.6 -> -35.4 | -34.2 -> -44.0 | (resp 3e-05, unusable) | -9.5 -> -20.9 |
| [20,24] | -31.9 -> **-39.5** | -40.7 -> **-48.9** | -40.9 -> **-48.7** | -32.4 -> **-40.7** |
| [24,28] | +10.9 -> **+3.0** | +30.8 -> **+20.8** | +27.1 -> **+17.5** | -18.4 -> -26.1 |
| [28,33] | +5.5 -> **+1.0** | +7.0 -> **-1.2** | +8.4 -> **+0.9** | +38.7 -> **+27.3** |
| [33,44] | +2.7 -> **+0.4** | +7.0 -> **+1.4** | +3.5 -> **-1.6** | +6.5 -> **-0.2** |

**In absolute sigma units** (the closure metric), over the bins whose true
response exceeds 1e-4 of sigma:

| point | shipped max\|dev\| | mode 1 | shipped mean | mode 1 |
|---|---|---|---|---|
| x2 = 0.35 | 1.00e-03 | 1.21e-03 (1.2x WORSE) | 7.69e-04 | **3.86e-04 (2.0x)** |
| x2 = 0.55 (a FIT) | 1.79e-04 | **1.32e-04 (1.4x)** | 1.41e-04 | **8.10e-05 (1.7x)** |
| x1,x3 | 2.91e-03 | **2.06e-03 (1.4x)** | 1.07e-03 | **8.68e-04 (1.2x)** |

**Two results inside this that are worth naming.**
* **The [24,28] "order-independent floor" MOVES.** D-021/D-019 recorded it as
  unmoved by any knot count or spacing (+27.1% at f = 2, +26.3% at f = sqrt2,
  +28.2% at five knots, 1.86e-04 of sigma) and bracketed it by node_cval's
  bound. Mode 1 takes it to **+17.5%, 1.16e-04 of sigma** at x2 = 0.55 and
  +30.8% -> +20.8% at x2 = 0.75. So the floor is partly inside the muF sector
  after all, and node_cval is not what was in it (D-032).
* **qT [28,33] and [33,44] close to <= 1.6% of their own response in every one
  of the four directions**, from +2.7 .. +38.7%. Those two bins carry 5.4x and
  10.7x the response of [20,24], so this is where the direction actually lives.

**The loss at qT 20-24 is -7.6 to -8.8 percentage points of the response, the
SAME at every variation size and both signs, in all four directions and in the
resummed-only calculation.** A constant fraction of the response is a missing
FIRST-ORDER term, not an interpolation remainder (which would scale as D^2/D^3).

### D-037 — THE RUN-TO-RUN SCATTER OF THIS MEASUREMENT, and what it licenses
###          — SETTLED

Two independent runs of the SAME mode-0 measurement (the anlmuf round's
`interp_x2_035` and this round's `attr_x2_035`, same card, same seed, same
n_train):

| qT | anlmuf | this round | difference |
|---|---|---|---|
| [18,20] | -25.5% | -26.6% | 1.1 pp |
| [20,24] | -31.6% | -31.9% | **0.3 pp** |
| [24,28] | +10.9% | +10.9% | 0.0 pp |
| [28,33] | +9.2%  | +5.5%  | **3.7 pp** |
| [33,44] | +1.5%  | +2.7%  | 1.2 pp |

but the A/B DIFFERENCE mode 0 -> mode 1 reproduces to 0.1 pp in every bin
(-8.8, -7.6, -7.9, -4.5, -2.3 here against -8.8, -7.6, -7.9, -4.4, -2.3 there).

**So: quote A/B differences, not absolute levels.** Two independent adaptive
integrations (the reference at the varied card, the model's node set at the
anchor) each target 1e-4 relative per node; the bin sums nodes with partial
cancellation and the scatter comes out several times the target.

**[28,33] is the noisy bin and there is a reason:** at x2 = 0.35 the profile's
own x2 breakpoint sits at qT = x2*Q = 31.9 GeV, i.e. INSIDE that bin, so the
adaptive integrand has a derivative discontinuity in it. At the anchor x2 = 0.6
the same break is at 54.7 GeV, inside [44,100]. Moving x2 moves a kink across
bin boundaries, which is a thing to remember when reading any per-bin transition
number.

### D-038 — REFUTED: the qT [20,24] shortfall is NOT the integration target
###          — SETTLED (10x tighter node ladder, it does not move)

`target_precision_rel` 1e-4 -> 1e-5, same card, same variation, everything else
identical. That tightens BOTH the reference and the model's own node set by an
order of magnitude, so a quadrature-resolution limit has to shrink.

| qT | true resp (1e-4 / 1e-5) | shipped 1e-4 | shipped 1e-5 | anl1 1e-4 | anl1 1e-5 |
|---|---|---|---|---|---|
| [18,20] | -4.14e-04 / -4.09e-04 | -26.6% | **-94.5%** | -35.4% | -103.3% |
| [20,24] | -3.075e-03 / -3.084e-03 | -31.9% | **-30.0%** | -39.5% | -37.6% |
| [24,28] | -7.840e-03 / -7.841e-03 | +10.9% | +36.4% | +3.0% | +28.5% |
| [28,33] | -1.822e-02 / -1.822e-02 | +5.5% | +2.0% | +1.0% | -2.4% |
| [33,44] | -3.301e-02 / -3.301e-02 | +2.7% | +2.4% | +0.4% | +0.1% |

**[20,24] does not move: -31.9% -> -30.0%, on a reference whose own true
response reproduces to 0.3%.** So the shortfall is a property of the frozen node
PAYLOAD, not of how finely the bin is sampled -- and the only thing in that
payload that carries muF is the convolution block.

**[18,20] is hereby CLOSED as a diagnostic bin, with a number.** Its model
response is -3.04e-04 at 1e-4 and -2.28e-05 at 1e-5 -- a factor THIRTEEN between
two builds of the same card -- against a true response of 4.1e-04 that
reproduces to 1%. The "do not diagnose below ~1e-4 of sigma" rule is not
conservative there, it is generous.

**[24,28] and [28,33] move by 25 and 3.5 pp**, which is the D-037 scatter again
and is why only A/B differences are quoted. Note the mode-0 -> mode-1 difference
is -7.9 pp at 1e-4 and -7.9 pp at 1e-5 in [24,28], and -4.5 / -4.4 pp in
[28,33]: the A/B is target-independent even where the level is not.

### D-039 — The c_i1 evolution term is REQUIRED by the O(alphas^2) muF
###          cancellation, is LARGE in the analytic model, and is a NO-OP in the
###          shipped construction — SETTLED, and it explains why

The route evolves `c_delta` (into P0, P1, P0xP0) and `c_p0` (into P0xP0). It does
NOT evolve `c_i1_qq`/`c_i1_qg`, the O(alphas) beam matching coefficients, whose
derivative
    d(I1 (x) f)/d ln muF = 2 g I1 (x) P0 (x) f = 2 g c_i1p0
is O(alphas^2) -- the SAME order as the c_p1 and P0xP0 terms that are carried.
Omitting it breaks the muF cancellation at O(alphas^2), which is exactly the
order that matters at low qT where muF sits near its 1.4 GeV floor.

Implemented as `ad_muf_abl` bit 8. `c_i1p0` is stored at fo_lvl = 2 (conv index
6), so it costs NO new grid, NO new stored kind and NO cache change. It is stored
as a TOTAL over flavour paths rather than split into the parts multiplying
b_qqV and b_qg, so the whole of it is attributed to `c_i1_qq`; at the anchor TNPs
both multipliers are 1, so the VALUE is exact and only the transition x TNP
cross-derivative is misattributed, on a term that is itself O(alphas) of the
correction.

**In the shipped analytic+residual construction it does nothing.** Arms
separated (correction size 8.088e-04 -> 8.405e-04, a 4% change, so this is a
real null and not a cached one), and at sigma level, x2 = 0.35:

| qT | mode 1 | mode 1 + c_i1 |
|---|---|---|
| [20,24] | -39.5% | -39.7% |
| [24,28] | +3.0% | +2.7% |
| [28,33] | +7.4% | +7.2% |
| [33,44] | -0.8% | -0.9% |

**And the reason is structural, not accidental.** Writing r = conv - delta, the
construction is algebraically

    cvi = Lagrange[r](D) + delta(D),

because the member interpolation and the residual subtraction share the same
three weights. The c_i1 term is LINEAR in D, and a quadratic Lagrange
interpolant through three points reproduces any polynomial of degree <= 2
exactly -- so whatever the c_i1 term adds to delta, the residual subtraction
takes straight back out. This is the same mechanism D-027 identified for the
mode-2 tier, now confirmed on a different term.

**In the PURE analytic model (no residual, bit 1|8) the same term is enormous:**

| qT | pure analytic | pure analytic + c_i1 |
|---|---|---|
| [18,20] | -40.9% | **+7.3%** |
| [20,24] | -53.0% | **-16.6%** |
| [24,28] | -43.1% | **-4.9%** |
| [28,33] | -34.0% | **-0.6%** |
| [33,44] | -28.2% | -11.6% |

So the analytic DGLAP model of the convolutions' muF dependence, WITH the
O(alphas^2) I1 term, is good to 0.6-16.6% of the response on its own -- against
26.6-31.9% for the shipped member interpolation at qT <= 24. **At the two low-qT
bins the member information is not helping, it is hurting.**

**What that identifies.** The construction's error is the Lagrange remainder of
r, (D - m_dn) D (D - m_up) r'''/6, and it blows up when D leaves the stencil.
`Vary.muf` compensates the muf_min floor, so at qT just above x1*Q the three
member positions collapse to a fraction of ln f (at qT 22, bT >= 2:
m_dn = -0.14, m_up = +0.23 against ln f = 0.69) while the transition-induced D
does not (D = +0.35), and D/|m_up| reaches 1.5. The construction is then
EXTRAPOLATING a residual, which is the one thing it was chosen (over Hermite) to
avoid -- and the collapse means it does so at low qT too, not only on the
x1,x3 leg. Section D-040 tests the fix that follows.

### D-039b — The same at the NEAR-ANCHOR derivative (x2 = 0.55, what a FIT
###           uses), which is the regime that matters for alpha_s — SETTLED

| qT | true resp | shipped | mode 1 | mode 1 + c_i1 | PURE analytic + c_i1 |
|---|---|---|---|---|---|
| [20,24] | -2.70e-04 | -40.9% | -48.7% | -48.9% | **-20.2%** |
| [24,28] | -6.60e-04 | +27.1% | +17.5% | +17.2% | **+1.9%** |
| [28,33] | -1.61e-03 | +8.4%  | **+0.9%** | +0.7% | -1.1% |
| [33,44] | -4.01e-03 | +3.6%  | **-1.5%** | -1.6% | -9.9% |
| [44,100]| -5.98e-03 | +1.6%  | **-1.8%** | -1.9% | -10.8% |

**The [24,28] floor is essentially CLOSED by the pure analytic model with the
c_i1 term: +27.1% -> +1.9%, a factor 14.** And the crossover is sharp: pure
analytic wins by 2x-14x at qT 20-28, ties at [28,33], and loses by 6x at
qT >= 33.

**That is exactly the stencil geometry.** From `stencil_conditioning.py`, the
member positions in units of ln f = 0.693 at large bT:

| qT | m_dn | m_up | D (x2=0.35) | D/\|m_up\| |
|---|---|---|---|---|
| 19 | -0.007 | +0.014 | +0.023 | 1.6 |
| 22 | -0.138 | +0.230 | +0.353 | 1.5 |
| 26 | -0.358 | +0.471 | +0.687 | 1.5 |
| 30 | -0.495 | +0.578 | +0.825 | 1.4 |
| 38 | -0.614 | +0.651 | +0.800 | 1.2 |

The floor compensation shrinks the stencil to a FRACTION of ln f at low qT while
the transition displacement does not shrink with it. Where the stencil is
healthy (qT >= 33) the member convolutions are worth having; where it has
collapsed (qT <= 28) extrapolating a residual across it costs more than the
analytic model's own ~0.5% error.

### D-040 — THE UNIFYING IDENTITY: the analytic+residual construction is BLIND
###          to any improvement of delta that is polynomial in D to degree 2
###          — SETTLED (algebra, confirmed on three separate terms)

Writing r = conv - delta, the construction is exactly

    cvi = SUM_m W_m conv_m + delta(D) - SUM_m W_m delta(m_pos)
        = Lagrange[conv](D) - Lagrange[delta](D) + delta(D)
        = Lagrange[r](D) + delta(D),

because the member interpolation and the residual subtraction share the SAME
three weights. A quadratic Lagrange interpolant through three points reproduces
any polynomial of degree <= 2 EXACTLY. Therefore if delta is changed by any
polynomial of degree <= 2 in D, Lagrange[delta] changes by the same amount and
the total does not move at all.

**Three independent confirmations, all previously read as separate puzzles:**
* **mode 2** (adding J3 P2 only) was measured WORSE than either end at the conv
  level (D-027) and was explained as "adding back the degree-1 piece the
  quadratic already absorbed". Same identity.
* **mode 3** (the full alphas^3 set) equals mode 1 at the sigma level to 1-2 pp
  (D-031) even though at the conv level, at the real qT-22 node geometry, its
  delta is **200x better** (-0.03% against -6.96% for the mode-1 truncation,
  `gate2_lowmuf.py` part B). J3(D) ~ 2 g^3 D is linear in D: absorbed.
* **the c_i1 term** (D-039), linear in D: absorbed, 0.2 pp at sigma level.

**Consequence, and it is the single most useful thing this round found: any
future refinement of the analytic model that is polynomial in D to degree 2 --
which includes storing the TRUE per-node derivatives d(conv)/dlnmuF and
d2(conv)/dlnmuF^2 and Taylor-expanding them -- is a GUARANTEED NO-OP in this
construction.** To use a better delta you must change the construction: either
drop the residual (measured, D-039: much better at qT 20-33, much worse at
qT >= 33), or go to an interpolant with more than three conditions (e.g. a
quartic through the anchor value, slope and curvature plus the two member
values), or blend by stencil health.

### D-041 — What is LEFT at qT <= 24, bounded from two sides that DISAGREE
###          — SETTLED as a measurement, OPEN as an explanation

**Side one: the splitting series is not converged at the muF floor.** The
previous round's derivative gate stopped at muF = 2 GeV. Extended down to
`muf_min` = 1.40 GeV against a converged central difference of
`DrellYan.conv_probe` -- the SAME interpolant SCETlib itself uses, so this is not
an LHAPDF-versus-us question (`gate2_lowmuf.py`):

| muF (GeV) | alphaS | P0 | P0+P1 | P0+P1+P2 | \|P2 term\|/deriv |
|---|---|---|---|---|---|
| 1.40 | 0.361 | -56.3% | -13.3% | **-1.04%** | 12.2% |
| 1.50 | 0.348 | -54.7% | -13.7% | **-2.87%** | 10.8% |
| 1.90 | 0.308 | -46.5% | -8.5%  | -0.46% | 8.0% |
| 3.00 | 0.254 | -36.9% | -5.0%  | -0.32% | 4.7% |
| 8.00 | 0.188 | -25.5% | -1.9%  | +0.012% | 1.9% |
| 45.0 | 0.132 | -16.7% | -0.6%  | +0.006% | 0.6% |

The profile pins muF at that floor at large bT and that is exactly where the
qT 18-24 bins' response comes from (muF_anchor = 1.42 GeV at qT 19, 1.88 GeV at
qT 22, for bT >= 2). Above muF ~ 8 GeV the truncation is 1e-4, which is why the
route closes qT >= 24 and not below.

**Side two, and it does not agree.** At the real node geometry the CONVOLUTION
error at qT 22 is -0.03% .. +0.33% for the mode-3 analytic model and
-0.35% .. +1.44% for the shipped interpolation. Amplified by the measured 8.6x
RG cancellation those are 0.3% and 12% of the net response -- against the 16.6%
and 33% observed. **The conv-level error under-predicts the sigma-level residual
by ~5x for the shipped model and ~50x for the analytic one.**

**So a SECOND amplification exists between one bT node and the bin, and it is
none of the five things D-032/D-034/D-035/D-038 rule out.** The candidate,
unmeasured: at qT ~ 22 the Bessel oscillation has period 2pi/qT ~ 0.29 in bT, the
transition displacement is 0.026 ln f at the bT that dominate the first lobe and
0.35 at the large bT where the integrand oscillates, so the low-qT muF response
is a residue of the oscillatory TAIL while at qT >= 30 it comes from the
dominant lobe. **THE EXPERIMENT THAT WOULD SETTLE IT, not done: the
bT-RESOLVED, quadrature-weighted conv error -- sum over the bin's own sites of
w_s x (model conv error at that node), against the sigma-level residual.** That
is the missing link between every conv-level gate this project has run and every
sigma-level number, and it is why the conv-level tier table did not predict the
sigma-level tiers.

**Do not use conv-level gating to design the next construction.** It has now
mispredicted the sigma level three times (the tier table, the four-construction
table, and mode 3).

### D-042 — SHIP mode 1 + the c_i1 term, OFF BY DEFAULT; do NOT build a mode-3
###          cache — PROVISIONAL (needs Luca / kdlong)

**What to merge:** the analytic DGLAP evolution (mode 1) and the c_i1 term, the
`set_muf_ablate` diagnostics that made the attribution possible, and
`rule_cvals` exposing `c_grad`. `set_muf_analytic` stays DEFAULT 0 -- turning it
on is a change to the production prediction and is Luca's call, not mine.

**Why it is worth merging even though qT 20-24 gets worse:**
* strict improvement in mean |dev| in all four directions (2.0x, 2.1x, 1.7x,
  1.2x) and in the worst bin in three of four;
* the two bins carrying 90% of each direction's response close to <= 1.6% of the
  response, from +2.7% .. +38.7%;
* at the NEAR-ANCHOR derivative -- what a fit uses -- max 1.4x, mean 1.7x, and
  the [24,28] floor moves for the first time (+27.1% -> +17.5%, and +1.9% in the
  pure-analytic arm);
* the other 38 directions are untouched BY CONSTRUCTION and verified
  bit-identical, so it cannot regress alpha_s, kappa_R, kappa_F, the NP lambda
  or the TNPs;
* it costs nothing: no grid, no stored kind, no cache change,
  `sizeof(ad::GlobalData)` unmoved, existing caches load.

**Why the c_i1 term goes in even though it is a sigma-level no-op today:** it is
required for the muF cancellation at O(alphas^2); it is free; and on a
FLOOR-DEGENERATE node (wmf_dn = wmf_up = 0, the three members are the same
convolution) the residual subtraction vanishes and delta(D) is used bare -- there
it is NOT a no-op, and those are exactly the nodes the low-qT bins live on.

**Overturned by:** a construction that closes qT 20-24 without regressing
qT >= 28; the pure-analytic arm is the lead (D-039) but it loses 6-10x at
qT >= 33, so it needs the blend, and a blend needs the bT-resolved measurement
of D-041 first.

### D-043 — THE LOW-qT RESIDUAL IS THE CONSTRUCTION, AND IT IS DEMONSTRABLY
###          FIXABLE: qT [20,24] goes -31.9% -> -0.0% — SETTLED (measured)

D-040's identity says the construction is `Lagrange[r](D) + delta(D)` with
r = conv - delta. But `delta` is built to reproduce conv's VALUE, SLOPE and
CURVATURE at D = 0 to the truncated order, so

    r'(0) = r''(0) = 0,

and a QUADRATIC through r(m_dn), r(0), r(m_up) THROWS THAT AWAY -- it gives r a
spurious slope and curvature at the anchor, which is precisely a
FIRST-ORDER-in-D error, the signature the sigma-level residual has had all
along.

Imposing those two conditions as well makes the interpolant a QUARTIC with a
closed form and NO free parameter (`ad_muf_abl` bit 64):

    w_dn = D^3 (m_up - D) / ((m_up - m_dn) m_dn^3)
    w_up = D^3 (D - m_dn) / ((m_up - m_dn) m_up^3)

It is 1 at its own member and 0 at the other two, so knot exactness survives;
both weights vanish as D^3, so the anchor slope and curvature come from `delta`
alone. Same three members, same shape of code.

**Measured, x2 = 0.35, dev as a % of the true response:**

| qT | shipped | mode 1 | mode 3 | mode 3 PURE | mode1+Hermite | **mode3+Hermite** |
|---|---|---|---|---|---|---|
| [18,20] | -26.6 | -35.7 | -34.3 | +32.1 | **+0.2** | +25.6 |
| [20,24] | -31.9 | -39.7 | -38.6 | +2.0 | -19.2 | **-0.0** |
| [24,28] | +10.9 | **+2.7** | +3.7 | +16.2 | +7.7 | +30.4 |
| [28,33] | +11.8 | +7.2 | +7.5 | +16.8 | -15.6 | **+0.8** |
| [33,44] | +1.5 | **-0.9** | -0.8 | +2.5 | -9.7 | +1.7 |
| [44,100]| +1.8 | -0.9 | **-0.7** | +1.7 | -9.9 | +0.6 |

**qT [20,24], which nothing had moved in three rounds of work, goes to -0.0%,
and [28,33] to +0.8% and [44,100] to +0.6%.** So the low-qT loss is NOT an
irreducible limit of the analytic route, and it is NOT the muf_min DGLAP
truncation of D-041 either: it is the construction discarding information the
analytic model already has.

**And mode 3 becomes ESSENTIAL, reversing part of D-031.** mode 3 is a no-op in
the residual construction (its delta differs from mode 1's by a polynomial in D,
D-040) but decisive in the Hermite and pure ones: at [20,24] mode-1+Hermite is
-19.2% and mode-3+Hermite is -0.0%; pure mode 1 + c_i1 is -16.6% and pure mode 3
+ c_i1 is +2.0%. **So "no mode-3 rebuild" is correct ONLY for the construction
that ships today.**

**NOT SHIPPABLE AS IT STANDS.** [24,28] regresses to +30.4% and [18,20] to
+25.6%. The quartic's weights are ~5x the quadratic's at the real geometry
(w_up = 3.9 at qT 26, 4.9 at qT 22, against 0.78 and 0.23), so it amplifies both
the member convolutions' own spread and any error in `delta`. The next step is a
CONDITIONED version of the same construction, not a new idea: the two candidates
are (a) a degeneracy/conditioning guard on m_up^3 and m_dn^3 that falls back to
the quadratic when the stencil is too collapsed for a quartic, and (b) imposing
only r'(0) = 0 (a cubic, weights ~ D^2 rather than D^3), which is the
intermediate and was not tried.

**What this changes about the earlier constructions.** D-025 rejected "Hermite"
after a conv-level scan -- but that was a CUBIC through both members with the
exact analytic anchor SLOPE, not a quartic imposing slope AND curvature, and it
was scored at the conv level, which D-041 shows mispredicts sigma by 5-50x. The
quartic is a different object and it is the one that works.

### D-044 — REJECTED: clamping the interpolation coordinate to the stencil
###          — SETTLED (measured bad on the x1,x3 leg)

Bit 32, the identity inside the stencil and at the members. At x2 = 0.35 it is
roughly neutral ([20,24] -40.9% -> -43.4%, [28,33] +7.4% -> +3.3%), and at
x2 = 0.55 it does not separate AT ALL -- correct, and a good check: near the
anchor every node's displacement is inside its stencil, so a pure extrapolation
guard must be the identity there.

On the x1,x3 leg, where D reaches -1.74 ln f, it is BAD: [24,28] -18.4% ->
+14.2%, [28,33] +42.7% -> +90.7%, [18,20] -30.7% -> -162.7%. Holding the
residual constant beyond the stencil discards real displacement information that
the quadratic, wrong as it is, was at least using. Rejected; kept behind the bit
so it is neither re-derived nor believed.

### D-043b — The same at the NEAR-ANCHOR derivative, and the per-bin winner map
###           — SETTLED

x2 = 0.55, dev as a % of the true response:

| qT | shipped | mode 1 | mode 3 | mode3 PURE | mode1+Herm | mode3+Herm |
|---|---|---|---|---|---|---|
| [20,24] | -40.9 | -48.9 | -47.7 | **-1.7** | -16.8 | **+1.6** |
| [24,28] | +27.1 | +17.2 | +18.7 | +24.2 | **+7.8** | +30.1 |
| [28,33] | +8.4 | **+0.7** | +1.6 | +18.3 | -2.5 | +16.9 |
| [33,44] | +3.6 | **-1.6** | -1.1 | +6.4 | -9.1 | +7.2 |
| [44,100]| +3.2 | **-0.2** | +0.0 | +3.3 | -9.6 | +2.8 |

So the conclusion is regime-independent: **the residual-quadratic construction
owns qT >= 28 (0.2-1.6%), and the pure / quartic constructions with mode 3 own
qT [20,24] (1.6-2.0%). No single one of the six wins everywhere**, and the
crossover sits at [24,28], where mode1+Hermite is the best available (+7.8%, from
+27.1% shipped -- a 3.5x improvement on the bin that three previous rounds could
not move at all).

**That is the shape of the remaining work, and it is a conditioning problem on a
known construction, not an open physics question.** The quartic's weights are
~5x the quadratic's at the real geometry, so the natural next step is the
intermediate: impose only r'(0) = 0 (a CUBIC, weights ~ D^2 instead of D^3), or
guard the quartic on m_up^3 / m_dn^3 and fall back. Neither was tried.

### D-043c — CORRECTION to D-043's status: the quartic DIVERGES on the x1,x3
###           leg. It is a PROOF of mechanism, not a candidate implementation
###           — SETTLED (measured)

D-043 called the quartic "not shippable as it stands" on the strength of a
[24,28] regression. On the x1,x3 = 0.3,0.9 direction, where the induced
displacement reaches **D = -1.74 ln f**, it does not regress -- it explodes:

| qT | shipped | mode 1 | mode3 PURE | mode1+Herm | mode3+Herm |
|---|---|---|---|---|---|
| [18,20] | -17.3% | -28.9% | +77.7% | +3.5% | +9.4% |
| [20,24] | -32.4% | -40.9% | +13.6% | +105.0% | +149.7% |
| [24,28] | -18.4% | -26.2% | -27.7% | **-557%** | **-607%** |
| [28,33] | +42.7% | **+31.7%** | +59.3% | **-1172%** | **-1326%** |
| [33,44] | +12.3% | **+5.5%** | +21.3% | +14.3% | +38.4% |
| [44,100]| +14.2% | +9.4% | +29.5% | **+3.0e6%** | **+3.1e6%** |

The cause is in the construction's own definition and was flagged in the code
comment when it was written: the quartic's weights grow as D^4/m^3 outside the
stencil where the quadratic's grow as D^2, so at D = 1.74 ln f on a
floor-collapsed stencil they are astronomical. ([44,100] additionally has a true
response of -1.0e-03 that changes SIGN relative to the other bins, so its
percentage is not to be read as physics -- but -1172% at [28,33], whose response
is +7.5e-03, is.)

**So the correct status of the quartic is: a PROOF that the low-qT residual is
information the construction discards -- it takes qT [20,24] from -31.9% to
-0.0% at both x2 legs and both regimes -- and NOT a candidate implementation.**
Any implementation needs extrapolation control that the quadratic gets for free.
The clamp (bit 32) is the obvious pairing and is bad on this same leg on its own
(D-044); clamp-AND-quartic was not measured.

**This does not touch anything about mode 1**, which is monotone and safe on this
direction too (+42.7% -> +31.7% at [28,33], +12.3% -> +5.5% at [33,44], and
-32.4% -> -40.9% at [20,24] like everywhere else).

**And it sharpens the recommendation:** ship mode 1 + c_i1, which is validated,
bounded and cannot regress any other direction; treat the quartic as the measured
next lead with a named failure mode, and require it to be tested on the x1,x3 leg
FIRST, not last. That ordering is the lesson: every construction in this project
has been designed on the x2 legs and broken on x1,x3, which is the direction
whose displacement leaves the stencil by 74%.

### D-043d — The construction map holds on all THREE x2 legs — SETTLED

x2 = 0.75 (the fourth point), dev as a % of the true response:

| qT | shipped | mode 1 | mode 3 | mode3 PURE | mode1+Herm | mode3+Herm |
|---|---|---|---|---|---|---|
| [20,24] | -40.7 | -49.1 | -47.8 | **+2.1** | -14.1 | +5.2 |
| [24,28] | +30.8 | +20.6 | +22.1 | +24.7 | **+9.6** | +32.3 |
| [28,33] | +7.0 | **-1.4** | -0.3 | +19.9 | -0.9 | +19.3 |
| [33,44] | +4.7 | **-1.0** | -0.4 | +10.1 | -7.0 | +10.4 |
| [44,100]| +1.7 | -1.9 | -1.6 | +2.7 | -11.3 | **+1.3** |

Same map as D-043 and D-043b: **pure mode 3 closes [20,24] to ~2% on all three
x2 legs (2.0%, 2.1%, -1.7%) and in both regimes; mode 1 owns qT >= 28 (0.3-1.9%);
[24,28] is the crossover and mode1+Hermite is the best there on every leg
(+7.7% / +9.6% / +7.8% from +10.9% / +30.8% / +27.1%).** The x1,x3 leg is the
exception and is where the quartic diverges (D-043c).
