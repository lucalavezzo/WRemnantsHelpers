#!/usr/bin/env python3
"""Build MR !9's new description from the old one, so the prose that was already
right is preserved and only the default-on parts are rewritten."""
import pathlib
import sys

src = pathlib.Path("/tmp/mr9_desc.md").read_text()
timing = pathlib.Path(sys.argv[1]).read_text() if len(sys.argv) > 1 else "TIMING_PENDING"


def sub(old, new):
    global src
    assert src.count(old) == 1, f"anchor not unique/found: {old[:60]!r}"
    src = src.replace(old, new)


sub("`DrellYan::set_muf_analytic(mode)` -- **0 = off, and still the default**.",
    """`DrellYan::set_muf_analytic(mode)` -- **1 = on, and now the DEFAULT.**
`set_muf_analytic(0)` restores the interpolation-only model exactly and is kept
as **the A/B arm every number below is measured as**, not as a fallback: it is
what made all of this measurable, and it is what a reviewer needs to reproduce
any of it.""")

sub("""* central analytic/shipped - 1, max over 210 bins: **0.000e+00** exactly
* kappa_F = 2 analytic/shipped - 1: **0.000e+00** exactly
* arm separation at x2 = 0.35: 8.5e-04, so the nulls below are real nulls
* **36 of 39 directions at ratio 1.00 to every digit printed** -- all 8 NP
  lambda, all 10 TNPs, kappa_R both legs, muF both legs, both joint
  muF x kappa_R, both alphaS.""",
    """re-verified **after the flip**, because "on by default" means these now hold for
everyone rather than only for callers who opted in:

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
  all 39 directions.""")

# ---- the absolute-sigma table, the alpha_s projection and the cost ---------
ANCHOR = """In absolute sigma units over the bins whose true response exceeds 1e-4 of sigma,
mean |dev| improves in all four directions (2.0x, 2.1x, 1.7x, 1.2x) and the worst
bin in three of four."""
sub(ANCHOR, ANCHOR + """

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

""" + timing.rstrip())

sub("""### The honest limit, stated plainly

**qT [20,24] and below gets worse, by a near-constant -8 percentage points of the
response**,""",
    """### The honest limit, stated plainly

**This MR closes the transitions above the sign flip at ~24 GeV. Below it the
residual grows by ~8 percentage points of a response that is itself 1e-05 ..
1e-04 of sigma, and the remaining low-qT shortfall is the RG cancellation
described above -- it is NOT removed by this change.**

In detail: **qT [20,24] and below gets worse, by a near-constant -8 percentage
points of the response**,""")

sub("""### Full write-up""",
    """### Why the mechanism, not the numbers, is what makes this principled

The varied-anchor test measured the two halves of the cancellation separately at
the sigma level, per bin: a displaced evaluation is **-7.9 x dS** with the nodes
frozen and no muF members, and **+8.6 x dS** with them, netting **+0.68 x dS**.
That is the renormalisation-group cancellation between the explicit ln(muB/muF)
and the PDF's evolution to muF, measured rather than argued. A ~4% error on
either half is **32% of the answer**. Supplying the derivative analytically is
exactly how a small numerical error stops being amplified twelvefold inside that
cancellation -- which is the reason to turn this on, independent of any single
bin's percentage.

### Full write-up""")

out = pathlib.Path("/tmp/mr9_desc_new.md")
out.write_text(src)
print(f"wrote {out} ({len(src)} chars)")
