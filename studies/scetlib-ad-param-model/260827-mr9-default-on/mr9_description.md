## Analytic DGLAP muF evolution of the beam convolutions

muF cannot be differentiated analytically in the AD kernel because it changes a
numerical PDF input, so the beam convolutions' muF dependence was frozen at three
samples (kappa_F = 1/2, 1, 2) with a quadratic through them. That is fine for
kappa_F itself, which sits AT those samples, and wrong for the resummation
transition points, which reach the beam functions only through an induced
per-node muF shift D that at the production variation size reaches
**1.15 x ln f** (1.74 for the x1,x3 leg) -- outside the sampled range. The model
was extrapolating, and the error survived undamped: muF is unphysical, the
explicit `ln(muB/muF)` in the beam matching coefficients and the PDF's evolution
to muF cancel to the order computed, and this MR makes the second half analytic
so the cancellation happens **before** the numerics.

**How big that cancellation is, measured at the sigma level per bin rather than
argued:** the two halves are **+-(5.8 .. 10.0) x the net transition response**.
A 1% error in the numerical half is a 6-10% error in the answer.

### What it does, and what it does not touch

`DrellYan::set_muf_analytic(mode)` -- **1 = on, and now the DEFAULT.**
`set_muf_analytic(0)` restores the interpolation-only model exactly and is kept
as **the A/B arm every number below is measured as**, not as a fallback: it is
what made all of this measurable, and it is what a reviewer needs to reproduce
any of it.

* **mode 1** uses only conv kinds the `fo_lvl = 2` prefix already holds
  (P0, P1, P0xP0): no extra grids, no extra stored kinds, **existing caches load
  unchanged** and `sizeof(ad::GlobalData)` is unmoved.
* **mode 3** additionally fills c_p2, c_p0p1, c_p1p0, c_p0p0p0 (16 more beamfunc
  grid families) and so needs the nodes rebuilt, or live rules.

`d/d ln muF` raises the alphaS order of a conv kind by one and the kind set is
truncated at `fo_lvl`, so the generator is **nilpotent** and the truncated-order
solution TERMINATES -- at `fo_lvl = 2` it is a quadratic in D, with no
truncation error in D at any displacement.

What is added is `delta(D) - SUM_m W_m delta(m_pos)` with `delta(0) = 0`
identically, so it **vanishes at the anchor and at both members**. kappa_F =
1/f, 1, f return the stored convolutions bit for bit and every direction that
sits at a knot -- kappa_F itself, the alphaS pair, all 8 NP lambda, all 10 TNPs
-- is untouched BY CONSTRUCTION.

`set_muf_analytic_i1(bool)`, default on, also evolves the O(alphas) beam
coefficients (`d(I1 (x) f)/dlnmuF = 2 g c_i1p0`), which is O(alphas^2) -- the
same order as the c_p1 and P0xP0 terms already carried -- and is therefore
required for the cancellation to close at that order. `c_i1p0` is already stored,
so it is free.

### Validation

**39-direction closure against the production `CorrZ` templates, 210-bin cache,
BOTH ARMS READ FROM ONE CACHE** (so node set, rules, members and re-solved
weights are bit-identical between them) -- re-verified **after the flip**, because
"on by default" means these now hold for everyone rather than only for callers
who opted in:

* built-in default read back through pybind: `muf_analytic() == 1`
* central, max |on/off - 1| over the covered gen bins: **0.000e+00**
* kappa_F = 1/2 response: **0.000e+00**; kappa_F = 2 response: **0.000e+00**
* **36 of the 39 mapped directions at max |on/off - 1| = 0.000e+00 exactly**, and
  the 3 that move are the 3 transition directions and nothing else -- all 8 NP
  lambda, all 10 TNPs, kappa_R both legs, muF both legs, both joint
  muF x kappa_R and both alphaS are exactly zero, not merely small.
* `sizeof(ad::GlobalData)` = **2424** bytes, as the pre-MR cache's own rule
  header records it, and that cache **loads** under the default-on build -- which
  is the check, since `load_bin_rules`' `layout_check` refuses a file that
  disagrees by a single byte. `Bin_rule::Site` 24, `ad::HardData` 592 and
  `ad::NodeData` 3208 are unmoved too.
* **arm separation proved rather than assumed**: three arms (mode 0, mode 1, mode
  1 + `set_muf_ablate(32)`) give three *different* sums at x2 = 0.35 --
  665.5413453161 / 665.6428816932 / 665.6445736511. `values_and_jacobian`
  memoises on the parameter vector **alone**, so an A/B that forgets to drop that
  key returns a perfect and wrong null; this once returned exactly 1.00 across
  all 39 directions.

**Against an EXACT runcard refill** (the transition points written into the card,
so SCETlib recomputes the convolutions at the shifted muF -- no templates, no
nonsingular mismatch, no cache), dev as a % of the direction's own response:

| qT | x2=0.35 | x2=0.75 | x2=0.55 (a FIT) | x1,x3=0.3,0.9 |
|---|---|---|---|---|
| [24,28] | +10.9 -> **+3.0** | +30.8 -> **+20.8** | +27.1 -> **+17.5** | -18.4 -> -26.1 |
| [28,33] | +5.5 -> **+1.0** | +7.0 -> **-1.2** | +8.4 -> **+0.9** | +38.7 -> **+27.3** |
| [33,44] | +2.7 -> **+0.4** | +7.0 -> **+1.4** | +3.5 -> **-1.6** | +6.5 -> **-0.2** |
| [20,24] | -31.9 -> -39.5 | -40.7 -> -48.9 | -40.9 -> -48.7 | -32.4 -> -40.7 |

In absolute sigma units over the bins whose true response exceeds 1e-4 of sigma,
mean |dev| improves in all four directions (2.0x, 2.1x, 1.7x, 1.2x) and the worst
bin in three of four.

### The same thing in absolute cross-section terms

Percentages of a response say nothing about size, and the two regressing bins
have tiny responses. Per bin, at x2 = 0.35, against the same runcard reference:

| qT | true response | error before -> after | change in sigma |
|---|---|---|---|
| [18,20] | -0.041% | (response below the 1e-4 diagnostic floor) | **-3e-05** (loss) |
| [20,24] | -0.31% | -28% -> -36% | **-2.5e-04** (loss) |
| [28,33] | -1.8% | +11.6% -> <= 1.6% | **+1.8e-03** (gain) |
| [33,44] | -3.3% | +2.3% -> <= 1.6% | **+2.3e-04** (gain) |

The gain at [28,33] alone is **~7x the largest loss**, and mean |dev| improves in
**all four** template directions by 1.2x-2.1x. The low-qT regression is real and
is 1e-05 .. 1e-04 of sigma.

### What it does to alpha_s -- and the one number that does NOT improve

The residual's size is not what a fit feels; its **overlap with dlnsigma/dalphaS**
is. So the model/template residual of each transition direction was projected
onto dlnsigma/dalphaS taken from the same cache's Jacobian, with the other
nuisances profiled out (same solve, same nuisance basis and same
**sigma(alphaS) = 6.16e-04** as the earlier rounds, so the ranking is
comparable), before and after, from one cache in one process.

**It gets worse, and that is reported rather than buried.** In quadrature over
the three transition directions:

| | qT < 24 | qT >= 24 | all bins |
|---|---|---|---|
| before | 0.0943 sigma | 0.0845 sigma | **0.0371 sigma** |
| after | 0.1124 sigma | **0.0237 sigma** | **0.1247 sigma** |
| after/before | 1.19x | **0.28x** | **3.36x WORSE** |

The decomposition is exact -- the projection is linear in the residual at fixed
mask, weighting and basis -- and it says precisely what happened:

* **In the window the correction acts on, qT >= 24, the alpha_s-equivalent
  improves 3.6x** (0.0845 -> 0.0237 sigma), consistently in all three
  directions (-0.047 -> +0.021, +0.040 -> +0.001, +0.058 -> +0.011 sigma).
* **The pre-correction total was an accidental cancellation.** In every one of
  the three directions the qT < 24 and qT >= 24 halves carried *opposite* signs
  of near-equal size (+0.075/-0.047, -0.015/+0.040, -0.055/+0.058 sigma), so the
  total came out near zero for a reason that has nothing to do with the model
  being right. Fixing the high-qT half destroys the cancellation and **exposes**
  the low-qT half.
* Of the 0.1124 sigma that is left below qT 24, **0.0943 sigma was already there
  before this MR** and 0.0181 sigma is the -8 pp this MR adds.

So the honest statement is: this correction does **not** reduce the
alpha_s-equivalent of the transition residual -- it moves the total from a
cancelling pair to an uncancelled low-qT residual of **0.125 sigma(alphaS)**
(7.7e-05 in alphaS), which is the same order as the transition group's own impact
on alphaS (~1.2e-04 of a 3.8e-04 total). That is a number worth naming and worth
closing, and it is an argument for finishing the low-qT construction, not for
keeping a model whose high-qT half is known to be wrong and whose apparent
alpha_s neutrality was a coincidence between two errors.

Caveat on the levels, stated because it matters: the *reference* here is the
production `CorrZ` templates, whose central shape differs from ours (DYTurbo
nonsingular vs SCETlib's analytic V+jet), so the absolute levels carry a
reference-dependent floor. The **arm difference** is clean -- one cache, one
process, three separated arms -- and it is what the qT >= 24 improvement and the
qT < 24 regression above are read from.

Against those same templates, mean |dev| over the covered bins improves in all
three transition directions (2.21e-04 -> 2.06e-04, 8.59e-05 -> 7.81e-05,
2.14e-04 -> 1.63e-04) and max |dev| in two of three -- i.e. the residual does get
smaller; it just gets smaller in the directions alpha_s does not care about.

### What it costs

Nobody had measured this. Warm, same process, same cache (210 bins, 24 params),
16 threads, arms **interleaved round by round** so the statistic is a paired
ratio and any load drift slower than one round cancels -- the first, blocked
attempt could not tell 0% from 15%, because this login node carries other jobs.

| | off | on | paired on/off (6 rounds) |
|---|---|---|---|
| `values_and_jacobian` | 0.538 s | 0.552 s | median **1.020**, mean 1.011 +- 0.022 |
| `hessian` | 48.00 s | 48.31 s | median **1.009**, mean 1.013 +- 0.016 |

**It is free**: ~1% on both, which is inside the +-2% scatter of the measurement
itself. That is what the construction predicts -- the added term reuses conv
kinds the `fo_lvl = 2` prefix already holds, so there is no new grid, no new
stored kind, no extra PDF call and no change to the node set. The [24,28] "order-independent floor" that no knot count or
spacing could move (recorded at +27.1% at f = 2, +26.3% at f = sqrt2, +28.2% at
five knots) **moves for the first time**.

### The honest limit, stated plainly

**This MR closes the transitions above the sign flip at ~24 GeV. Below it the
residual grows by ~8 percentage points of a response that is itself 1e-05 ..
1e-04 of sigma, and the remaining low-qT shortfall is the RG cancellation
described above -- it is NOT removed by this change.**

In detail: **qT [20,24] and below gets worse, by a near-constant -8 percentage
points of the response**, identically at every variation size, both signs, all four directions,
and in a resummed-only calculation. That is a missing first-order term, and it is
a DIFFERENT defect from the one this MR fixes. Five candidates were tested and
all five are dead: the rule's bin-level constant `node_cval` (its share of the
bin is 2e-05, four orders too small), the `rule.c_grad` the staged replay
discards (1e-14 .. 4e-09 of sigma), a collapsed-stencil numerical blow-up (the
Lagrange weights stay O(1); max 2.5), the model's transition-frozen nonsingular
(a `calculation_piece = sing` re-run is identical to 0.1 pp there), and the
integration target (1e-4 -> 1e-5 moves it -31.9% -> -30.0%).

It is, however, **demonstrably the construction, not a limit of the route**. The
construction is algebraically `Lagrange[conv - delta](D) + delta(D)`, and since
`delta` reproduces conv's value, slope and curvature at D = 0, the residual has
`r'(0) = r''(0) = 0` -- which the three-point quadratic discards. Imposing them
makes the interpolant a quartic with a closed form and no free parameter
(available here behind `set_muf_ablate(64)`), and with mode 3 it takes
**qT [20,24] from -31.9% to -0.0%** and [28,33] to +0.8%. It is not enabled
because it regresses [24,28] to +30.4%: the quartic's weights are ~5x the
quadratic's at the real node geometry, so it needs a conditioning guard first.
That also means **mode 3, which is a sigma-level no-op in the shipped
construction (its `delta` differs from mode 1's by a polynomial in D, and a
quadratic through three points absorbs any polynomial of degree <= 2 exactly),
becomes essential in the quartic one.**

### Diagnostics included (all no-ops by default)

`DrellYan::set_muf_ablate(mask)`: 1 drops the member interpolation of the
convolutions, 2 the same for the per-site rule weights, 16 freezes the explicit
`ln(muB/muF)` at the anchor transition points, 32 clamps the interpolation
coordinate to the stencil, 64 is the quartic residual above. `s_muf_lf` enters
`node_value` only through `lf_` and `mfk_live`, so **1|16 removes the transition
response of the whole muF sector exactly** -- which is what turned this from an
argument into a measurement. `rule_cvals()` also reports the rule's `c_grad`.

Both new globals are deliberately NOT `thread_local`: they are set from the
driver thread and read inside the TBB workers.

### Why the mechanism, not the numbers, is what makes this principled

The varied-anchor test measured the two halves of the cancellation separately at
the sigma level, per bin: a displaced evaluation is **-7.9 x dS** with the nodes
frozen and no muF members, and **+8.6 x dS** with them, netting **+0.68 x dS**.
That is the renormalisation-group cancellation between the explicit ln(muB/muF)
and the PDF's evolution to muF, measured rather than argued. A ~4% error on
either half is **32% of the answer**. Supplying the derivative analytically is
exactly how a small numerical error stops being amplified twelvefold inside that
cancellation -- which is the reason to turn this on, independent of any single
bin's percentage.

### Full write-up

`~/public_html/alphaS/260826_transition_analytic_e2e/00_README.txt` -- every
number above with its provenance, the four eliminated routes, the figures, and
the run-to-run scatter that limits the absolute levels (0.3-3.7 pp; A/B
differences reproduce to 0.1 pp).