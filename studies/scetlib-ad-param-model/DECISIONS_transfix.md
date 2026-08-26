# Decisions — the SAFE residual interpolant, and why there is not one (2026-08-26)

One bounded round on the question the previous round left open: find a residual
interpolant form that keeps the analytic-DGLAP route's qT >= 24 gain, removes the
qT < 24 regression, and does not explode on the x1,x3 leg.

**The answer is that no such form exists at `ad_muf_anl = 1`, and the reason is
not conditioning.** The stop rule fires. Narrative in
`LOGBOOK_ENTRY_transfix.md`; figures and tables in
`~/public_html/alphaS/260826_transition_safe_interp/`.

Staged, not merged: `DECISIONS.md` and `LOGBOOK.md` are untouched by this round.
(Copies also live at `~/.claude/jobs/140d052c/tmp/safeint/staged/` and in the
round's web directory, because a parallel session has twice deleted staged files
from the study directory.)

Continues D-031..D-044 of `DECISIONS_transitions.md`. Status key: **SETTLED**
(evidence in hand) / **PROVISIONAL** / **OPEN** (needs Luca).

---

## D-T1 — the premise of every candidate form is FALSE at mode 1, by 13.8% — **SETTLED**

**What.** The previous round's diagnosis was: the construction is
`Lagrange[r](D) + delta(D)` with `r = conv - conv(0) - delta`; `delta` is built
to reproduce `conv`'s value, slope and curvature at `D = 0`; therefore
`r'(0) = r''(0) = 0`; therefore a three-point quadratic, which does not know
that, gives `r` a spurious slope. Every candidate — quartic, cubic, clamped,
blended — exists only to impose `r'(0) = 0`.

`r'(0)` is not zero. It is the analytic model's **own linear truncation error**,
and it is now measured per node, directly, against SCETlib's own convolution
interpolant (`DrellYan.conv_probe`), with `delta` replicated term for term from
`muf_evo_coeffs`:

```
e1 / (node response slope)      mode 1 (P0, P1)   mode 3 (+ P2, alphas^3)
  muF = 1.42 GeV (the floor)         13.8%              2.05%
  muF = 1.69                          9.9%              0.5%
  muF = 1.88                          9.2%              0.5%
  muF = 3.43                          4.9%              0.3%
  muF = 6.07                          2.7%             -0.04%
```

**Why it is believable.** `gate2_lowmuf.py` measured the same truncation a
completely different way — a converged central difference of `conv_probe`
against `2g P0 + 2g^2 P1 (+ 2g^3 P2)`, POINTWISE, no finite `D` and no cross
terms. Interpolated to the muF above, its P0+P1 column reads
13.1 / 10.1 / 8.6 / 4.4 / 2.6% against the 13.8 / 9.9 / 9.2 / 4.9 / 2.7% here —
**agreeing to 0.2–0.7 pp** from two scripts with no shared code. With P2 it reads
1.04% at the floor, 0.46% at 1.90 and 0.32% at 3.00 against 2.05 / 0.5 / 0.3%
here: within a factor two at the floor (mine is the finite-`D` residual *with*
the `K12`, `K21`, `T111` cross terms; gate2's is the pointwise truncation
*without* them) and to 0.05 pp above it. Both say 1–2%, not 14%.

**Consequence.** The profile pins muF at the 1.40 GeV floor at large bT, which is
exactly where the qT 18-24 bins get their transition response. So the very bins
the quartic was built for are the ones where the premise is worst.

---

## D-T2 — each form's error is closed-form in the stencil geometry, and it is validated to 1.8 pp over a 29x range — **SETTLED**

**What.** Write `r(t) = e1 t + e2 t^2/2 + C t^3 + ...`. Then each candidate's
rendering of each power is exact arithmetic in the three member positions
`(a, 0, b)`:

| form | basis | exact on | amplifies |
|---|---|---|---|
| quadratic | `D, D^2` | `e1`, `e2` | nothing; misses the cubic content entirely |
| cubic | `D^2, D^3` | `e2`, `C` | `e1` by `A1c = D(D-a-b)/(ab)` |
| quartic | `D^3, D^4` | `C` (and `D^4`) | `e1` by `A1 = D^2/(b-a)[(b-D)/a^2 + (D-a)/b^2]`, `e2` by `A2 = D(a+b-D)/(ab)` |

so

```
err_quart = (A1 - 1) e1 D + (A2 - 1) e2 D^2 / 2,
```

with `A1` and `A2` **pure stencil geometry** — no PDF, no SCETlib, computable
from `scales_formulas.hpp` alone.

**Validated.** Predicted against measured, per node, at both modes and on three
legs: max `|pred - meas| = 0.018`, rms `0.0065`, as fractions of the node's own
true response, over measured errors spanning `0.000 .. 0.517`. A 29x dynamic
range closed to under two percentage points
(`mechanism/mech_pred_vs_meas.png`).

**So the quadratic is the unique three-point form that does not amplify the
analytic model's own truncation error at all**, and any other form pays
`(A1 - 1) e1`.

**And "unique" is a theorem, not a survey.** `A1 = 1` and `A2 = 1` read

```
w_dn a   + w_up b   = D          (render e1 x exactly)
w_dn a^2 + w_up b^2 = D^2        (render e2 x^2/2 exactly)
```

two linear equations in `(w_dn, w_up)` with determinant `ab(b-a)`, non-zero on
any non-degenerate stencil. The solution is unique, it *is* the quadratic
Lagrange pair, and knot exactness follows rather than being imposed. There is no
other three-point form that leaves `e1` and `e2` alone.

---

## D-T3 — the x1,x3 explosion was never a numerical accident — **SETTLED**

`A1` reaches **8.02** on the x1,x3 leg (2.04 on x2 = 0.35, 0.05 near the
anchor), because `Vary.muf` compensates the muf_min floor and collapses the
member stencil at large bT while the transition displacement does not collapse
with it (`mechanism/A1_geometry.png`).

`8.02 x 13.8% = 111%` of the node's own response; the muF sector's measured
6-10x RG cancellation turns that into ~900% of the NET response. That is the
-607% / -1326% the previous round recorded at qT [24,28] and [28,33]. **Both
factors were already measurable before the quartic was ever built.**

**The controlled experiment.** Mode 1 -> mode 3 changes `e1` and nothing about
the geometry:

```
max |node error| / R, x1,x3 leg      mode 1    mode 3
  quartic                             0.517     0.060      8.6x
  quadratic                           0.018     0.015      unchanged
```

The quadratic is unmoved because the identities above require it — the mode
cannot help a form that was already exact on `e1` and `e2`. At mode 3 EVERY
candidate collapses into the quadratic's band
(`mechanism/form_node_errors.png`).

---

## D-T4 — no conditioning guard can win, and that is an inequality between two measured numbers — **SETTLED**

A guard that blends quadratic and quartic with `theta` caps the damage at
`~theta (A1 - 1) e1`. But the **entire prize** is the cubic content `C` that the
quadratic misses — and the quadratic's own node error, which IS that missed
content, is at most **1.8%** of the node response anywhere on any leg at either
mode.

```
maximum available gain      1.8%   (the quadratic's whole node-level error)
minimum price at T = 0.3    ~2%    (theta (A1-1) e1 at the nodes that carry it)
```

The trade is never favourable at mode 1, for any tolerance, at any node. Not a
tuning failure — an inequality.

**Near the anchor it is even simpler.** There `A1 = 0.05`, so
`err_quart = -(1 - 0.05) e1 D`: the quartic does not amplify `e1`, it
**discards** it. Imposing `r'(0) = 0` costs exactly `r'(0)`, which is up to 13.8%
of the node response. That is the regime a FIT uses.

---

## D-T5 — the sigma-level gate, x1,x3 FIRST: every candidate regresses — **SETTLED**

`trans_attribute.py --with-safe`, 10 arms in ONE process off one rule build and
one runcard reference; residual form in `ad_muf_abl` bits 7..9. dev = arm/runcard
- 1 as a % of the bin's own true response, x1,x3 = 0.3,0.9:

```
qT bin     shipped    anl1    cubic    quartic   bq(0.3)   bq(1)   bq1a    clip    bc(1)
[18,20]     -30.7   -42.8    +45.1     +25.1     -40.1    -18.2    -7.4   +30.0   -11.4
[20,24]     -32.4   -40.9    -12.0    +105.0     -42.1    -50.1   -44.3    +1.7   -18.0
[24,28]     +17.1    +8.2     -0.9     -20.1     -15.4    -30.8   -16.1   +24.2   +14.0
[28,33]     +42.7   +31.8    -40.0   -1172.5    +105.8    +66.9   +21.2  +116.2   +42.2
[33,44]      +6.5    -0.3     +0.7      +3.8      -5.6     -7.9    -8.3    -6.8    -0.3
[44,100]    -45.4   -40.5  +180426  -8890079     -40.1    -39.0   -37.8   -30.2   -37.8
```

The two bins that carry this direction's response are [33,44] (1.16e-02) and
[28,33] (7.54e-03). **At [28,33] every candidate but `bq1a` is worse than the
shipped quadratic, and `bq1a` pays for it at [33,44] (-8.3 against -0.3).** The
raw cubic and the raw quartic both blow up at [44,100] (`A1c` and `A1` diverge as
`1/(ab)` and `1/a^2` on a near-degenerate stencil): the cubic is NOT the safe
intermediate the previous round hoped for.

**The guards do work as designed** — every blended arm is tame at [44,100]
(-37.8 to -40.1 against the quadratic's -40.5), so the conditioning cap does
prevent the blow-up. It simply buys nothing.

**Control that passed.** `anl1quart` (form field = 2) reproduces `anl1herm`
(bit 64) to every digit in all six bins, including -8890079.2%. The form field is
wired correctly and this quartic IS the previous round's quartic.

---

## D-T6 — the invariants hold for every form, by construction and by measurement — **SETTLED**

`max |central_arm / central_shipped - 1| = 0.000e+00` EXACTLY, for all nine arms,
in every bin. Every form here is 1 at its own member and 0 at the other two, so
`kappa_F = 1/f, 1, f` return the stored convolutions bit for bit — and so does
ANY blend of two such forms, for ANY blend fraction, which is what lets the blend
fraction depend on `D`, `mfk_dn` and `mfk_up` however it likes.

`sizeof(ad::GlobalData)` is unmoved: the form is read from the existing
free-standing `ad::ad_muf_abl` global, no new field, so existing caches load.

---

## D-T7 — the low-qT shortfall does not live in the interpolation at all — **SETTLED**, and it is the finding that matters most

The quadratic member interpolation reproduces `conv[c_delta]` at the displaced
muF to **<= 1.8% of that node's own response at EVERY node of EVERY leg**, at
both modes (`mechanism/form_node_errors.png`, `quad` column). The sigma-level
residual at qT [20,24] is -32% (shipped) to -41% (mode 1).

So the shortfall is not a failure to interpolate the beam convolution, and a form
that improves qT [20,24] in sigma while making the node-level convolution worse
— which is exactly what the quartic does, 10x worse at the node level and 2x
better in sigma — is **compensating** an error elsewhere, not correcting one here.
That is the honest reading of the previous round's "-31.9% -> -0.0%".

Corollary, measured: a `<= 2%` per-node change in the convolution moves the
[28,33] bin response by **74 percentage points** (`bq(0.3)`, +31.8 -> +105.8),
and the sigma-level dev is **not monotone** in how much non-quadratic form is
mixed in (+31.8 -> +105.8 at T = 0.3 -> +66.9 at T = 1 -> -1172 at full
quartic). The target is 3-20x more sensitive than the knob, and not monotone in
it. **There is nothing to tune here.**

---

## D-T8 — what to do instead — **OPEN** (needs Luca / the author)

1. **Ship MR !9 as it stands**: mode 1 + the quadratic + the `c_i1` term, off by
   default. It is a strict improvement on the mean `|dev|` in all four directions
   and closes the two bins that carry 90% of each direction's response to
   `<= 1.6%`. Document the limitation as *"closes qT >= 24, does not close
   qT < 24"* — do not describe the low-qT bins as fixable by a better
   interpolant.
2. **Do not ship any `r'(0) = 0` form at mode 1**, at any tolerance, with any
   clamp. Its error is `(A1 - 1) e1` with `A1` up to 8 from geometry alone and
   `e1` up to 13.8% measured.
3. **The exact request upstream**, now with a measured justification rather than
   a hypothesis. Either of these makes `e1 -> 0`, and only then does any
   `r'(0) = 0` form become legitimate:
   - **mode 3**: the full `alphas^3` evolution (`P2`, `P0xP1`, `P1xP0`,
     `P0xP0xP0` — four extra conv kinds, conv prefix 11 -> 15, a cache rebuild).
     Measured to divide `e1` by 6.7x on the max and to make every interpolant
     form safe, including on the x1,x3 leg.
   - **the stored grid derivative**: `d(conv)/d ln muF` from a finite difference
     of the grid's OWN interpolant, stored as two extra conv kinds at cache-build
     time. `conv_probe` already provides it. This makes `r'(0) = 0` true by
     construction rather than by truncation, and it is cheaper than mode 3.
   The question to put to the author is unchanged from D-044 but now has a
   number attached: *is `muf_min = 1.40` intended to be deep enough that the
   truncated splitting series is 13.8% off the grid's own evolution there, and if
   so should the differentiable model use the grid's own derivative instead?*
