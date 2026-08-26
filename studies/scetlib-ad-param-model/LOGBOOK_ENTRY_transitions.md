## 2026-08-26 — The transition points, taken end to end: the analytic DGLAP route works above qT 24 and the residual below it is a DIFFERENT defect

**Plots:** `~/public_html/alphaS/260826_transition_analytic_e2e/`
**MR:** !9, `muf-analytic-trans` -> `autodiff-sigmaul` (a7392be),
https://gitlab.cern.ch/scetlib/contrib/scetlib-cms/-/merge_requests/9
**Decisions:** `DECISIONS_transitions.md`, D-031 .. D-042.
**Code:** worktree `/work/submit/lavezzo/alphaS/scetlib-anltrans`, branch
`muf-analytic-trans` off `eb60a04`, builds `build-anltrans` (ablations) /
`build-anltrans2` (+c_i1) / `build-anltrans3` (+clamp) / `build-anltrans4` (the
final shape). `scetlib-cms`, `build-fix`, `build-knots`, `build-trans`,
`build-nak`, `build-5knot` and `build-anlmuf` were not touched. The anlmuf
round's prototype was sitting UNCOMMITTED in `scetlib-anlmuf`; it is imported
here as `43342cd`.

### The headline

**The analytic DGLAP evolution of the beam convolutions closes the transition
directions above qT ~ 24 GeV and cannot close qT 20-24, and the two halves of
that sentence have different causes.**

Above qT 24 it works, in all four directions the templates carry and in both
regimes: the error falls from +2.7% .. +38.7% of the direction's own response to
**<= 1.6%** in qT [28,33] and [33,44], the two bins that hold ~90% of each
direction's response. At the NEAR-ANCHOR derivative -- what a fit uses -- max
|dev| improves 1.4x and mean 1.7x, and the [24,28] "order-independent floor"
that no knot count or spacing could move goes **+27.1% -> +17.5%** (and +1.9% in
the pure-analytic arm).

Below qT 24 it makes things worse by a near-constant **-8 percentage points** of
the response, identically at every variation size, both signs, all four
directions, and in a resummed-only calculation. A constant fraction of the
response is a missing FIRST-ORDER term, not an interpolation remainder. **Five
candidate causes were tested and all five are dead** (section below), and what
is left is bounded from two sides that disagree by a factor 5-50 -- which is
itself the finding, and the reason the next construction must not be designed on
conv-level gating.

### What was already on disk and had never been read

`260826_analytic_muf_dglap/00_README.txt` promises its sigma-level attribution in
"sections 8-9", stops at section 7, and its `runcard_ref/` is an empty directory.
The measurement ran to completion at 01:01 that night and sits in
`.../tmp/anlmuf/interp_*.json`. It says **mode 3 == mode 1 to 1-2 pp of the
response in every bin of all four variation points.** So the 16 extra beamfunc
grid families, the conv prefix 11 -> 15 and the full node REBUILD that mode 3
needs buy nothing at sigma level. That was the single most expensive item on the
route's cost list and it is now off it (D-031). Re-measured independently here
with live rules (which fill the mode-3 kinds in-process, no cache needed) and it
reproduces.

### The new instrument, and why it made the difference

`DrellYan.set_muf_ablate(mask)` -- bit 1 drops the member interpolation of the
CONVOLUTIONS, bit 2 that of the per-SITE rule weights, bit 16 freezes the
explicit `ln(muB/muF)` of the beam coefficients at the ANCHOR transition points
(`Lf -> Lf + mfk_live`, identically `log(muB_lf/mf_0)`), bit 32 clamps the
interpolation coordinate to the stencil. `s_muf_lf` enters `node_value` ONLY
through `lf_` and `mfk_live`, so **bits 1|16 remove the transition response of
the whole muF sector exactly**, and that is what turned the problem from
argument into measurement. Every mask is a 0/1 multiplier; at mask 0 the
39-direction CorrZ closure reproduces the anlmuf round's table to every digit
and the central value differs by 0.000e+00 in every arm.

### The muF cancellation, measured at sigma level

Per bin, each half as a multiple of the NET true response (x2 = 0.35):
[18,20] -10.0 / +9.7, [20,24] -8.6 / +8.6, [24,28] -9.7 / +9.9,
[28,33] -7.4 / +7.4, [33,44] -5.9 / +5.8. **So the two halves are +-(6..10)x the
answer and cancel.** A 1% error in the numerical half is a 6-10% error in the
response. That is why this direction was worth the effort, and it is now a
number rather than an estimate. (`mechanism/muf_cancellation.png`.)

The sector supplies only 0.5% .. 63% of the transition response depending on the
bin; the rest comes through muB, muS and nuS, which the kernel does
analytically. That decomposition is what makes the sector's accuracy measurable:
shipped / mode 1 = 0.31 / 0.15 at [20,24], 1.21 / 1.06 at [24,28],
1.11 / 1.02 at [28,33], 1.07 / 1.01 at [33,44].

### Five dead candidates, each with a number

1. **`node_cval`** -- the rule's bin-level constant, transition response
   identically zero. A frozen constant dilutes the response by exactly
   `c_val/sigma`, and that is **2.3e-05 .. 9.7e-07**. Four orders too small.
   This retires the standing "10-40% of the shortfall" estimate: the old bound
   was the member SPREAD, which bounds the constant's kappa_F response, not its
   transition response. `rule_cvals()` extended to report it.
2. **`rule.c_grad`**, the exact gradient of the compression residual, which the
   STAGED replay silently discards. Now exposed: `c_grad.dp/sigma` =
   1e-14 .. 4e-09.
3. **A collapsed-stencil numerical blow-up.** The leading hypothesis, and false:
   `stencil_conditioning.py` gives max|w| = 2.5 over qT 19..38, bT 0.05..8, with
   a float-epsilon noise floor 1e-3 below the node's own response. The positions
   DO collapse but D collapses with them. The five-knot branch's relative
   degeneracy guard is therefore not needed for the three-knot stencil.
4. **The model's frozen NONSINGULAR** (`fo_node_value` has no transition
   dependence at all). Re-running everything with `calculation_piece = sing`
   gives -31.9% / -39.4% at [20,24] against -31.9% / -39.5% matched: identical
   to 0.1 pp. It DOES matter at qT 24-33, where the matched error is about half
   the resummed-only one -- the frozen nonsingular partially cancels the
   resummed error there. Luck, not design.
5. **The integration target.** 1e-4 -> 1e-5, tightening the reference AND the
   model's node set tenfold: [20,24] goes -31.9% -> -30.0%. The same run closes
   [18,20] as a diagnostic bin with a number -- its model response moves by a
   factor THIRTEEN between the two builds.

### The identity that explains three separate puzzles at once

The construction is algebraically `Lagrange[conv - delta](D) + delta(D)`, because
the member interpolation and the residual subtraction share the same three
weights. **A quadratic through three points reproduces any polynomial of degree
<= 2 exactly, so any change to `delta` that is polynomial in D to degree 2 is a
guaranteed no-op.** That is why mode 2 was worse than either end, why mode 3
equals mode 1 at sigma level despite its `delta` being **200x better** at the
conv level (-0.03% against -6.96% at the qT-22 node geometry), and why the new
`c_i1` term moves sigma by 0.2 pp. **Anything built next on stored true
derivatives will be a no-op too unless the construction changes.**

### The c_i1 term: required, free, and decisive only in the pure model

`d(I1 (x) f)/dlnmuF = 2g c_i1p0` is O(alphas^2) -- the same order as the c_p1 and
P0xP0 terms already carried -- so omitting it breaks the muF cancellation at
that order. `c_i1p0` is already in the fo_lvl = 2 prefix, so it costs nothing.
In the residual construction it is a no-op (above). With the member
interpolation DROPPED it is transformative: [20,24] -53.0% -> **-16.6%**,
[28,33] -34.0% -> **-0.6%**, and at the near-anchor derivative [24,28]
+27.1% -> **+1.9%**, a factor 14. **At qT 20-33 the three frozen member
convolutions are not helping, they are hurting** -- the floor compensation
shrinks the stencil to a fraction of ln f while the transition displacement does
not shrink with it (at qT 22, bT >= 2: m_dn = -0.14, m_up = +0.23 against
ln f = 0.69, D = +0.35), so the residual is being extrapolated everywhere below
qT ~ 30. Clamping the coordinate to the stencil was tried and is not the answer
either ([20,24] -40.9% -> -43.4%, though [28,33] +7.4% -> +3.3%).

### What is left, bounded from two sides that disagree

At the muF FLOOR the splitting series is not converged. Extending the previous
round's derivative gate from 2 GeV down to `muf_min` = 1.40 GeV, against a
converged central difference of `conv_probe` (the SAME interpolant SCETlib uses,
so this is not an LHAPDF-versus-us question): P0+P1+P2 is off by **-1.04% at
1.40 GeV, -2.87% at 1.50, -0.46% at 1.90**, and the P2 term itself is 8-12% of
the whole derivative there. Above 8 GeV the truncation is 1e-4 -- which is
exactly why the route closes qT >= 24 and not below. The profile pins muF at
that floor at large bT and that is where the low-qT response comes from
(muF_anchor = 1.42 GeV at qT 19, 1.88 at qT 22).

But at the real node geometry the CONV-level error at qT 22 is
-0.03% .. +0.33% (mode-3 analytic) and -0.35% .. +1.44% (shipped). Times the
measured 8.6x cancellation that is 0.3% and 12% of the net -- against 16.6% and
33% observed. **The conv level under-predicts sigma by ~5x for the shipped model
and ~50x for the analytic one, so a SECOND amplification exists between one bT
node and the bin.** The candidate, unmeasured: at qT ~ 22 the Bessel oscillation
has period 2pi/qT ~ 0.29 in bT and the displacement is 0.026 ln f at the bT that
dominate the first lobe against 0.35 in the oscillatory tail, so the low-qT muF
response is a residue of the TAIL while at qT >= 30 it comes from the lobe.
**The experiment that would settle it, NOT done: the bT-resolved,
quadrature-weighted conv error -- sum over the bin's own sites of
w_s x (conv error at that node) -- against the sigma-level residual.** That is
the missing link between every conv-level gate this project has run and every
sigma-level number.

### THE LOW-qT LOSS IS THE CONSTRUCTION, AND IT IS FIXABLE

The identity above says the construction is `Lagrange[r](D) + delta(D)`. But
`delta` reproduces conv's VALUE, SLOPE and CURVATURE at D = 0, so
r'(0) = r''(0) = 0 -- and a quadratic through three points THROWS THAT AWAY,
giving r a spurious slope and curvature at the anchor. That is a
first-order-in-D error, which is exactly the signature the residual has.

Imposing both conditions makes the interpolant a QUARTIC with a closed form and
no free parameter, still 1 at its own member and 0 at the other two (so knot
exactness survives), with both weights vanishing as D^3 so the anchor slope and
curvature come from `delta` alone:

    w_dn = D^3 (m_up - D) / ((m_up - m_dn) m_dn^3)
    w_up = D^3 (D - m_dn) / ((m_up - m_dn) m_up^3)

With mode 3 it takes **qT [20,24] from -31.9% to -0.0%** (and [28,33] to +0.8%,
[44,100] to +0.6%) at the finite variation, and to +1.6% at the near-anchor
derivative. **So the low-qT loss is neither irreducible nor the muf_min DGLAP
truncation -- it is information the construction was discarding.**

Not shippable, and on one direction much worse than that: at x2 = 0.35 it
regresses [24,28] to +30.4%, and on the **x1,x3 leg, where D reaches -1.74 ln f,
it EXPLODES** -- [24,28] -18.4% -> -607%, [28,33] +42.7% -> -1326%. The cause is
in its own definition and was in the code comment before it was measured: the
quartic's weights grow as D^4/m^3 outside the stencil where the quadratic's grow
as D^2. **So the quartic is a PROOF that the low-qT residual is information the
construction discards, not a candidate implementation** -- any implementation
needs the extrapolation control the quadratic gets for free (impose only
r'(0) = 0 for a cubic with D^2 weights; or guard on m_up^3/m_dn^3; or pair it
with the clamp). And test on x1,x3 FIRST: every construction in this project has
been designed on the x2 legs and broken on x1,x3. Mode 1 is monotone and safe
there (+42.7% -> +31.7%, +12.3% -> +5.5%), which is why it is the thing to
merge. And it makes **mode 3 essential**, reversing
half of the "no rebuild" verdict: mode 3 is a no-op in the residual construction
by the degree-2 identity and decisive in the quartic and pure ones (mode1+Hermite
is -19.2% at [20,24] where mode3+Hermite is -0.0%).

No single construction wins everywhere. The residual quadratic owns qT >= 28
(0.2-1.6%), the pure and quartic constructions with mode 3 own [20,24]
(1.6-2.0%), and the crossover is [24,28], where mode1+Hermite is the best
available (+7.8% from +27.1%). **The remaining work is conditioning a known
construction -- impose only r'(0) = 0 for a cubic with D^2 weights, or guard the
quartic on m_up^3 / m_dn^3 -- not an open physics question.** Neither was tried.

Also rejected on the way, with numbers: clamping the interpolation coordinate to
the stencil. Neutral at x2 = 0.35, correctly a no-op at x2 = 0.55 (near the
anchor every node sits inside its own stencil, so a pure extrapolation guard MUST
be the identity there -- a good check that the bit does what it says), and bad on
the x1,x3 leg where D reaches -1.74 ln f ([28,33] +42.7% -> +90.7%).

### Recommendation

Merge mode 1 + the c_i1 term, keep `set_muf_analytic` DEFAULT 0 until Luca
rules, and do not build a mode-3 cache YET (the quartic construction is the
reason to build one later, and that reason is now measured). It improves the mean |dev| in all four
directions (2.0x / 2.1x / 1.7x / 1.2x) and the worst bin in three of four, it
closes the two bins that carry the response, the other 38 directions are
untouched BY CONSTRUCTION and verified bit-identical, and it costs nothing --
no grid, no stored kind, no cache change, `sizeof(ad::GlobalData)` unmoved.

### Physics read

The transitions move the resummation profile, and the profile moves every scale.
Four of those scales -- muB, muS, nuS and the explicit `ln(muB/muF)` -- are
analytic in the kernel and therefore exact. The fifth, muF, acts on a numerical
PDF, and it is unphysical: its explicit logs in the beam matching coefficients
and the PDF's DGLAP evolution to muF cancel to the order computed. The model was
doing the first half analytically and the second by interpolating three frozen
samples, so the interpolation error survived at full size inside an answer 6-10x
smaller. Supplying the second half as DGLAP too makes the cancellation happen
before the numerics, and above qT 24 -- where muF is above ~6 GeV and the
splitting series is converged to 1e-4 -- that is enough to close the direction.
Below qT 24 the profile has pushed muF onto its 1.40 GeV floor, where alphaS is
0.36 and the NNLO splitting term is still 12% of the derivative; there the
differentiable model is asking fixed-order QCD for something fixed-order QCD does
not have. That is a statement about where the profile puts muF, not about the
autodiff construction, and it is the right thing to put to the author.
