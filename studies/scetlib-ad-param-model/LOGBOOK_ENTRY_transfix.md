# Logbook entry (staged) — the safe residual interpolant: one bounded round, and the stop

**2026-08-26.** Follows the transition-points end-to-end round
(`LOGBOOK_ENTRY_transitions.md`, D-031..D-044,
`~/public_html/alphaS/260826_transition_analytic_e2e/`). That round merged the
analytic DGLAP muF evolution (MR !9, branch `muf-analytic-trans`, off by
default), which closes the transitions above qT 24 and costs a near-constant
-8 percentage points below it, and it left one named next step: find a residual
interpolant form that keeps the gain, removes the regression, and does not
explode on the x1,x3 leg the way the parameter-free quartic does (-1326% at
qT [28,33]). Three candidates were named: impose only `r'(0) = 0` (a cubic),
guard on `m^3`, or pair the quartic with a clamp.

**All three are dead, and so is the whole family, for a reason none of them
addresses.** Decisions in `DECISIONS_transfix.md` (D-T1..D-T8). Figures and the
full write-up: `~/public_html/alphaS/260826_transition_safe_interp/`.

Staged only: `LOGBOOK.md` and `DECISIONS.md` are untouched.

---

## What was built

Worktree `/work/submit/lavezzo/alphaS/scetlib-safeint`, branch
`muf-safe-interp` off MR !9's `a7392be` (which itself sits on MR !8's muF
member-coordinate fix — both are prerequisites), build dir `build-safeint`.
`scetlib-cms`, `build-fix`, `build-knots`, `build-trans`, `build-nak`,
`build-5knot` and every `build-anltrans*` were NOT touched.

A **residual-form field** in `ad_muf_abl` bits 7..9, `form = (abl >> 7) & 7`:
1 cubic, 2 quartic (identical to the existing bit 64), 3/4/5 conditioning-guarded
blends of quadratic and quartic, 6 the clipped quartic factor, 7 a guarded blend
of quadratic and cubic. No new field in `ad::GlobalData`, so `sizeof` is unmoved
and existing caches load; the form is read from the same free-standing global
`ad_muf_abl` that the previous round's ablation bits use.

Three new scripts, all under
`WRemnantsHelpers/studies/scetlib-ad-param-model/transitions/`:

| script | what it answers |
|---|---|
| `form_conditioning.py` | the amplification factors `A1`, `A2`, `A1c` per node from SCETlib's scale formulas alone — pure arithmetic, no SCETlib, no cache |
| `residual_forms.py` | the residual `r(D)` MEASURED with `conv_probe`, and every candidate form scored on it exactly, at mode 1 and (with `--mode3`) mode 3 |
| `residual_kinds.py` | the same, per conv KIND, so "is only `c_delta` interpolated well?" is answerable |
| `mechanism_check.py` | `(A1-1) e1 D + (A2-1) e2 D^2/2` predicted against measured, per node |

`trans_attribute.py` gains `--with-safe` and a `SAFE_ARMS` list; `trans_closure.py`
is unchanged and was not needed.

---

## The measurement that ended it, and it took twenty minutes

The previous round diagnosed the low-qT loss from an *identity*: the construction
is `Lagrange[r](D) + delta(D)` with `r = conv - conv(0) - delta`; `delta`
reproduces `conv`'s value, slope and curvature at `D = 0`; so `r'(0) = r''(0) = 0`
and the three-point quadratic throws that away. Every candidate form exists only
to impose `r'(0) = 0`.

Nobody had ever **measured `r`**. It is measurable: `DrellYan.conv_probe` gives
the convolution at any muF — the same interpolant SCETlib itself uses — and
`delta` can be replicated term for term from `muf_evo_coeffs`. Doing that gives,
immediately,

```
e1 = r'(0), as a fraction of the node's response slope
   mode 1 (P0, P1)     1.9% at muF = 6 GeV  ...  13.8% at the muf_min floor
   mode 3 (+ P2)      -0.04%                ...   2.05%
```

**`r'(0)` is not zero. It is the analytic model's own linear truncation error,
and at the muf_min = 1.40 GeV floor — which is exactly where the qT 18-24 bins
get their transition response — it is 13.8% of the node's response.** `gate2_lowmuf.py`
had measured the same truncation a different way — a pointwise central difference
of `conv_probe` against the splitting series — and interpolated to these muF its
P0+P1 column agrees with the numbers above to 0.2–0.7 pp, from two scripts with
no shared code.

Then the algebra of each form gives its price in closed form. Writing
`r(t) = e1 t + e2 t^2/2 + C t^3`:

* the **quadratic** renders `e1` and `e2` exactly and misses the cubic content;
* the **quartic** renders `C` exactly and renders `e1` with
  `A1 = D^2/(b-a)[(b-D)/a^2 + (D-a)/b^2]`, `e2` with `A2 = D(a+b-D)/(ab)`;
* the **cubic** renders `e2` and `C` exactly and renders `e1` with
  `A1c = D(D-a-b)/(ab)`.

`A1`, `A2`, `A1c` are pure stencil geometry. So `err_quart = (A1-1) e1 D +
(A2-1) e2 D^2/2`, and **that reproduces the measured quartic node error to max
0.018 / rms 0.007 of the node response over measured errors spanning 0.000 to
0.517** — a 29x range closed to under two percentage points, at both modes, on
three legs. `mechanism/mech_pred_vs_meas.png` is the figure; the points sit on
the diagonal and the mode-3 points collapse to the origin.

`A1` reaches **8.02** on the x1,x3 leg (2.04 at x2 = 0.35, 0.05 near the anchor),
because `Vary.muf` compensates the muf_min floor and collapses the member stencil
at large bT while the transition displacement does not collapse with it.
`8.02 x 13.8% = 111%` of the node response, times the muF sector's measured
6-10x RG cancellation, is ~900% of the net — which is the -607% / -1326% the
previous round recorded. **The explosion was never a conditioning accident. It is
`A1` times `e1`, and both factors were measurable before the quartic was built.**

The controlled experiment settles it: mode 1 -> mode 3 changes `e1` and nothing
about the geometry, and the quartic's worst node error on the x1,x3 leg goes
0.517 -> 0.060 (8.6x) while the quadratic's goes 0.018 -> 0.015 (unchanged, as
the identities require). At mode 3 every candidate collapses into the quadratic's
band.

---

## Why a guard cannot rescue it — an inequality, not a tuning failure

A guard caps `theta (A1 - 1) e1`. But the entire prize is the cubic content `C`
the quadratic misses, and **the quadratic's own node error, which IS that missed
content, is at most 1.8% of the node response anywhere on any leg at either
mode.** Maximum available gain 1.8%; minimum price at T = 0.3 about 2%. The trade
is never favourable at mode 1, for any tolerance, at any node.

And near the anchor — the regime a FIT uses — `A1 = 0.05`, so
`err_quart = -(1 - 0.05) e1 D`. The quartic does not amplify `e1` there, it
**discards** it. Imposing `r'(0) = 0` costs exactly `r'(0)`.

---

## The sigma-level gate, x1,x3 first as instructed

Ten arms in one process, one rule build, one runcard reference. dev as a % of the
bin's own true response, x1,x3 = 0.3,0.9:

```
qT bin     shipped    anl1    cubic    quartic   bq(0.3)   bq(1)   bq1a    clip    bc(1)
[20,24]     -32.4   -40.9    -12.0    +105.0     -42.1    -50.1   -44.3    +1.7   -18.0
[24,28]     +17.1    +8.2     -0.9     -20.1     -15.4    -30.8   -16.1   +24.2   +14.0
[28,33]     +42.7   +31.8    -40.0   -1172.5    +105.8    +66.9   +21.2  +116.2   +42.2
[33,44]      +6.5    -0.3     +0.7      +3.8      -5.6     -7.9    -8.3    -6.8    -0.3
[44,100]    -45.4   -40.5  +180426  -8890079     -40.1    -39.0   -37.8   -30.2   -37.8
```

At [28,33], the second-largest response on this leg, **every candidate but
`bq1a` is worse than the shipped quadratic, and `bq1a` pays for it at [33,44]**
(-8.3 against -0.3), which carries the largest. The raw cubic blows up at
[44,100] as badly as the quartic (`A1c` diverges as `1/(ab)`, `A1` as `1/a^2`, on
a near-degenerate stencil): the cubic is **not** the safe intermediate the
previous round hoped for. The guards do prevent the blow-up — every blended arm
is tame at [44,100] — they just buy nothing.

Control that passed: form field = 2 reproduces bit 64 to every digit including
-8890079.2%, so the field is wired right and this quartic is that quartic. And
`max |central_arm / central_shipped - 1| = 0.000e+00` EXACTLY for all nine arms —
the invariants hold for every form by construction, as they must, since each is
1 at its own member and 0 at the other two and any blend of two such forms is
too.

---

## The finding that outlives the stop

The quadratic member interpolation reproduces `conv[c_delta]` at the displaced
muF to **<= 1.8% of that node's own response at every node of every leg**, at
both modes. The sigma-level residual at qT [20,24] is -32% to -41%.

**So the low-qT shortfall does not live in the interpolation of the beam
convolution at all.** The quartic is 10x worse at the node level and 2x better in
sigma at [20,24]: it compensates an error elsewhere rather than correcting one
here. And the sigma-level dev is not even monotone in how much non-quadratic form
is mixed in (+31.8 -> +105.8 at T = 0.3 -> +66.9 at T = 1 -> -1172 at the full
quartic), while a `<= 2%` per-node change moves the bin by 74 percentage points.
The target is 3-20x more sensitive than the knob and not monotone in it. There is
nothing to tune.

The one loophole checked and closed on the way: `residual_kinds.py` shows the
quadratic is near-exact only on `c_delta`, and 5-95% off on `c_p1`, `c_i2_qqS`,
`c_p0`, `c_i1_qq` — but those are precisely the kinds the analytic model does NOT
evolve at mode 1, so for them `delta = 0`, `r` is the full response, `r'(0)` is
maximally non-zero, and the quadratic (exact on the linear and quadratic parts) is
the only defensible choice. That strengthens the conclusion rather than weakening
it.

---

## What to do next

1. Ship MR !9 as it stands, off by default, documented as *"closes qT >= 24,
   does not close qT < 24"* — and stop describing the low-qT bins as fixable by a
   better interpolant.
2. Never ship an `r'(0) = 0` form at mode 1.
3. Either of two things makes `e1 -> 0` and only then does the family become
   legitimate: **mode 3** (four extra conv kinds, a cache rebuild; measured to
   divide `e1` by 6.7x and to make every form safe) or **the stored grid
   derivative** (`d(conv)/d ln muF` as two extra conv kinds at cache-build time,
   which `conv_probe` already provides, making `r'(0) = 0` true by construction
   and costing less than mode 3). The second is the better ask.

The question for the author from D-044 stands and now carries a number: is
`muf_min = 1.40` intended to be deep enough that the truncated splitting series
is 13.8% off the grid's own evolution there, and if so should the differentiable
model take the derivative from the grid rather than from the series?
