# NP-model parameter constraints (CS kernel and TMD b.c.)

Source: AN-25-085 `theory.tex` Eqs. \ref{eq:npgamma}, \ref{eq:npf} (lines 233–234), with our locally-added $\lambda_6,\Lambda_6$ extensions.
Last updated: 2026-07-28
Status: provisional — algebra derived, not yet implemented in the fit.

## 1. Functional forms

Define $L_2(y)\equiv\Lambda_2+\Delta\Lambda_2\,y^2$.

**CS kernel** (with $\lambda_6\,b_T^6$ added inside the tanh):
$$\tilde\gamma_\zeta^{\rm NP}(b_T) \;=\; -\frac{\lambda_\infty}{2}\,\tanh\!A(b_T),
\qquad A(b_T)=\frac{\lambda_2}{\lambda_\infty}b_T^2+\frac{\lambda_4}{\lambda_\infty}b_T^4+\frac{\lambda_6}{\lambda_\infty}b_T^6.$$

**TMD boundary condition** (with $\Lambda_6\,b_T^5$ added inside the tanh, paralleling the AN's odd-power TMD argument):
$$f^{\rm NP}(b_T,y) \;=\; \exp\!\big[-2\Lambda_\infty\,b_T\,\tanh B(b_T,y)\big],$$
$$B(b_T,y)\;=\;\frac{L_2(y)}{\Lambda_\infty}b_T+\frac{\Lambda_4}{\Lambda_\infty}b_T^3+\frac{L_2(y)^3}{3\Lambda_\infty^{3}}b_T^3+\frac{\Lambda_6}{\Lambda_\infty}b_T^5.$$

> **Cross-checked against SCETlib source** (`scetlib-cms-newnp-lambda4fix/include/scetlib/qT/NP_models.hpp`,
> `NP_model_effective::operator()`, case `tanh_6`, 2026-07-17): the cube term is
> `(1/3)·pow<3>(lambda2_Y·bT/lambda_inf)` = $L_2^3\,b_T^3/(3\Lambda_\infty^{3})$ — **three** powers of
> $\Lambda_\infty$ (an earlier version of this note wrote $/(3\Lambda_\infty)$, which was wrong). It is the
> leading **arctanh correction**: `B = arctanh(arg/Λ∞)` so that `tanh(B)` reproduces the un-saturated
> `identity` model `exp(−2·bT·arg)` (i.e. keeps the intended $\Lambda_4 b_T^4$ exponent coefficient,
> cancelling the tanh's own $-B^3/3$). The **CS kernel has no analogous term** (Gamma_nu.hpp tanh_6:
> `A = (λ2_ν b² + λ4_ν b⁴ + λ6_ν b⁶)/λ∞_ν` only) — there $\tilde\gamma$ is *linear* in the tanh, so
> $\tanh(A)\to A$ already gives the small-$b_T$ series with no correction needed. Consequence for the wall:
> the TMD interior coefficient is $B_{\rm wall}=\Lambda_4+L_2^3/(3\Lambda_\infty^2)$ (used in
> `np_damping_wall.py`), **not** just $\Lambda_4$.

In the current fit, $\lambda_6$ and $\Lambda_6$ are **fixed positive constants**; $\lambda_{2,4,\infty}$ and $\Lambda_{2,4,\infty},\Delta\Lambda_2$ float.

**Fixed values in use:**
- CS: $\lambda_6 = 0.0007$ (coefficient of $b_T^6/\lambda_\infty$).
- TMD: $\Lambda_6 = 0.016$ (coefficient of $b_T^5/\Lambda_\infty$).

(Units are inherited from the scetlib implementation — the numerical constraints below use the values face-value; check units before porting to another convention.)

## 2. What "sensible tanh" means

Three physical requirements drive every constraint below:

- **R1 — right asymptote.** $\tilde\gamma^{\rm NP}\to$ negative constant as $b_T\to\infty$ ⇒ $\tanh A\to+1$ ⇒ $A\to+\infty$. Similarly $\ln f^{\rm NP}\to-(\text{const})\cdot b_T$ ⇒ $B\to+\infty$.
- **R2 — small-$b_T$ OPE.** $\tanh(x)\to x$ recovers the OPE automatically; no constraint beyond keeping the lowest term linear in $b_T^2$ (CS) or $b_T$ (TMD).
- **R3 — sign-preservation OR monotonicity.** Two reasonable choices, **(a)** weaker and **(b)** stronger:
  - **(a)** $A(b_T)\ge 0$ and $B(b_T,y)\ge 0$ for all $b_T\ge 0$ (and all $y$). Keeps $\tilde\gamma^{\rm NP}\le 0$ and $\ln f^{\rm NP}\le 0$ everywhere, but allows non-monotonic dips.
  - **(b)** $A$ and $B$ are **monotonically non-decreasing** in $b_T$. The tanh argument never decreases, so the NP functions smoothly interpolate from 0 to their asymptotes without overshooting.

(b) ⇒ (a) but not the reverse. (b) is what is normally meant by "sensible tanh"; (a) is a softer wall. Both are derived below; the choice is a fit-implementation decision.

## 3. CS-kernel constraints

R1 ⇒ $\lambda_\infty>0$, $\lambda_2\ge 0$.

### Criterion (a) — sign preservation ($A\ge 0$)

By AM-GM, $\lambda_2 b_T^2 + \lambda_6 b_T^6 \ge 2\sqrt{\lambda_2\lambda_6}\,b_T^4$ (equality at $b_T^2=\sqrt{\lambda_2/\lambda_6}$). So
$$A(b_T)\lambda_\infty = \lambda_2 b_T^2+\lambda_4 b_T^4+\lambda_6 b_T^6 \ge \big(\lambda_4 + 2\sqrt{\lambda_2\lambda_6}\big)b_T^4,$$
and the bound is tight. Therefore $A\ge 0\;\forall b_T$ ⇔
$$\boxed{\;\lambda_4 \;\ge\; -2\sqrt{\lambda_2\lambda_6}\;=\;-\sqrt{4\lambda_2\lambda_6}\;}\qquad\text{(a, sign-preservation)}$$

### Criterion (b) — monotonicity ($dA/db_T\ge 0$)

Differentiating $A$ and substituting $u\equiv b_T^2\ge 0$:
$$\frac{dA}{db_T}=\frac{2b_T}{\lambda_\infty}\,P(u),\qquad P(u)\equiv\lambda_2+2\lambda_4 u+3\lambda_6 u^2.$$

R3(b) ⇔ $P(u)\ge 0$ $\forall u\ge 0$. With $\lambda_6>0$ fixed (quadratic in $u$ opening upward), the discriminant $\Delta_P=4\lambda_4^2-12\lambda_2\lambda_6\le 0$ gives the half-space N&S form
$$\boxed{\;\lambda_4 \;\ge\; -\sqrt{3\lambda_2\lambda_6}\;}\qquad\text{(b, monotonicity)}$$
(When $\lambda_4\ge 0$, $P$ has all non-negative coefficients and is trivially $\ge 0$ — no discriminant condition needed. The bound only bites on the negative side.)

### Relation between (a) and (b)

$\sqrt{3}<2$, so (b) is strictly stronger:
$$-\sqrt{3\lambda_2\lambda_6}\;>\;-2\sqrt{\lambda_2\lambda_6},$$
i.e. the $\lambda_4$ floor is higher under (b). The gap is the "γ stays negative but dips" region.

**Reduction check ($\lambda_6\to 0$):** recovers $\lambda_\infty>0,\,\lambda_2\ge 0,\,\lambda_4\ge 0$ — matches the AN's commented-out conditions (theory.tex lines 246–251).

## 4. TMD constraints

R1 ⇒ $\Lambda_\infty>0$. Take $y_{\max}=2.5$ so $y_{\max}^2=6.25$.

**Small-$b_T$ positivity** (constant term of $B$, ∀ y): $L_2(y)\ge 0$ ⇔
$$\Lambda_2\ge 0\quad\text{and}\quad \Delta\Lambda_2\ge -\Lambda_2/6.25.$$
(The second is binding only if $\Delta\Lambda_2<0$.)

Recall $c_1(y)\equiv 3\Lambda_4+L_2(y)^3$, and the argument is
$$B(b_T,y)\Lambda_\infty = L_2(y)\,b_T + \tfrac{c_1(y)}{3}\,b_T^3 + \Lambda_6\,b_T^5.$$

### Criterion (a) — sign preservation ($B\ge 0$)

AM-GM on outer two terms: $L_2(y)b_T + \Lambda_6 b_T^5 \ge 2\sqrt{L_2(y)\Lambda_6}\,b_T^3$ (equality at $b_T^4=L_2(y)/\Lambda_6$). So
$$B(b_T,y)\Lambda_\infty \;\ge\; \Big[\tfrac{c_1(y)}{3} + 2\sqrt{L_2(y)\Lambda_6}\Big]b_T^3,$$
and tight. Therefore $B\ge 0\;\forall b_T,\forall y$ ⇔
$$\boxed{\;c_1(y) \;\ge\; -6\sqrt{L_2(y)\,\Lambda_6}\;=\;-\sqrt{36\,L_2(y)\Lambda_6}\quad\text{at the binding }y\;}\qquad\text{(a)}$$

### Criterion (b) — monotonicity ($\partial B/\partial b_T \ge 0$)

Set $v\equiv b_T^2\ge 0$:
$$\frac{\partial B}{\partial b_T}=\frac{1}{\Lambda_\infty}Q(v;y),\qquad Q(v;y)\equiv L_2(y)+c_1(y)\,v+5\Lambda_6\,v^2.$$

R3(b) ⇔ $Q(v;y)\ge 0$ $\forall v\ge 0$, $\forall y$. Discriminant $c_1^2-20\Lambda_6 L_2\le 0$ gives the half-space N&S form
$$\boxed{\;c_1(y)\ge -\sqrt{20\,\Lambda_6\,L_2(y)}\quad\text{at the binding }y\;}\qquad\text{(b)}$$
(When $c_1\ge 0$ — automatic if $\Lambda_4\ge 0$ — the bound is trivially satisfied; only $\Lambda_4$ going negative enough to make $c_1<0$ at some $y$ activates the wall.)

### Binding $y$

"Binding $y$" = the $y$ minimizing $c_1(y)+\sqrt{k\,\Lambda_6 L_2(y)}$, with $k=36$ for (a) and $k=20$ for (b):
- $\Delta\Lambda_2\ge 0$: $L_2(y)^3$ smallest at $y=0$ ⇒ check $y=0$ with $L_2=\Lambda_2$.
- $\Delta\Lambda_2<0$: $L_2(y)$ smallest at $y=\pm 2.5$ ⇒ check the endpoint with $L_2=\Lambda_2+6.25\Delta\Lambda_2$.
- If $\Delta\Lambda_2$ may change sign during the fit, evaluate at both $y=0$ and $y=\pm 2.5$ and take the worst.

### Relation between (a) and (b)

$\sqrt{20}<\sqrt{36}$, so (b) is strictly stronger — same pattern as the CS kernel.

**Reduction check ($\Lambda_6\to 0$):** $Q$ becomes linear in $v$, requiring $L_2(y)\ge 0$ and $3\Lambda_4+L_2(y)^3\ge 0$ ∀ y — i.e. $\Lambda_4\ge -L_2(y)^3/3$ at the binding $y$. Matches the AN's original form.

## 5. Summary table

With $\lambda_6,\Lambda_6$ **fixed positive**, both criteria:

| Function | Asymptote | Small-$b_T$ | (a) sign-preservation | (b) monotonicity (stricter) |
|---|---|---|---|---|
| $\tilde\gamma^{\rm NP}$ | $\lambda_\infty>0$ | $\lambda_2\ge 0$ | $\lambda_4\ge -\sqrt{4\lambda_2\lambda_6}$ | $\lambda_4\ge -\sqrt{3\lambda_2\lambda_6}$ |
| $f^{\rm NP}$ | $\Lambda_\infty>0$ | $\Lambda_2\ge 0$, $\Delta\Lambda_2\ge -\Lambda_2/6.25$ | $c_1(y)\ge -\sqrt{36\Lambda_6 L_2(y)}$ at binding $y$ | $c_1(y)\ge -\sqrt{20\Lambda_6 L_2(y)}$ at binding $y$ |

with $L_2(y)=\Lambda_2+\Delta\Lambda_2 y^2$ and $c_1(y)=3\Lambda_4+L_2(y)^3$.

Both criteria collapse correctly to the AN's original conditions in the $\lambda_6,\Lambda_6\to 0$ limit.

## 6. Numerical headroom at AN central values

Plugging in:
- CS lattice central: $\lambda_\infty=1.6853$, $\lambda_2=0.0870$, $\lambda_4=0.0074$; with $\lambda_6=0.0007$.
- TMD nominal: $\Lambda_\infty=1$, $\Lambda_2=0.25$, $\Delta\Lambda_2=0.125$, $\Lambda_4=0.06$; with $\Lambda_6=0.016$.

**CS:** central $\lambda_4>0$, so both bounds are **non-binding** at central. Floors at central $\lambda_2=0.0870$:

| Criterion | Floor on $\lambda_4$ |
|---|---|
| (a) sign-preservation $-\sqrt{4\lambda_2\lambda_6}$ | $\approx -0.0156$ |
| (b) monotonicity $-\sqrt{3\lambda_2\lambda_6}$ | $\approx -0.0135$ |

AN lattice uncertainty $\sigma(\lambda_4)\approx 0.0066$, so the (b) floor sits at $\sim -2\sigma_{\rm lat}$ — non-binding inside the lattice prior but a sanity wall beyond. The window scales as $\sqrt{\lambda_2}$, so a downward pull on $\lambda_2$ tightens both floors.

**TMD:** central $\Lambda_4=0.06>0$, $\Delta\Lambda_2=+0.125>0$ ⇒ $c_1(y)>0$ everywhere ⇒ both bounds **non-binding** at central. Asymmetry $\Delta\Lambda_2\ge -\Lambda_2/6.25=-0.04$ also satisfied. Floors at $y=0$ (binding, since $\Delta\Lambda_2>0$ centrally), with $L_2(0)=\Lambda_2=0.25$:

| Criterion | $c_1$ floor | $\Lambda_4$ floor (subtract $\Lambda_2^3/3=0.0052$ then $/3$) |
|---|---|---|
| (a) $-\sqrt{36\Lambda_6 L_2}=-\sqrt{36\cdot 0.016\cdot 0.25}$ | $\approx -0.379$ | $\Lambda_4\gtrsim -0.131$ |
| (b) $-\sqrt{20\Lambda_6 L_2}=-\sqrt{20\cdot 0.016\cdot 0.25}$ | $\approx -0.283$ | $\Lambda_4\gtrsim -0.099$ |

AN alternative variation is $\Lambda_4{}_{-0.05}^{+0.1}$, so the (b) floor sits just past the existing $-0.05$ prior edge — useful wall just beyond the explored range.

**Net:** at central values, all four floors are inactive (good — central values are physical). They activate only when the fit pulls $\lambda_4$ or $\Lambda_4$ negative beyond the respective floor — exactly the "sensible tanh" wall.

## 7. Open items before fit implementation

- **Criterion to enforce.** Decision: **(b) monotonicity**. Both (a) and (b) are encoded in the regularizer (param-map `"criterion"` field, default `"b"`); switch is a one-line config flip.
- **TMD binding-$y$ handling.** Decision: evaluate at **both** $y=0$ and $y=y_{\max}=2.5$ and sum the penalties. Safest under floating $\Delta\Lambda_2$ (correct sign-handling without runtime case analysis).
- **Enforcement strategy.** Decision: **soft hinge-loss penalty** as a custom rabbit Regularizer. Strength controlled at fit time via `--regularizationStrength`. Implementation in `WRemnants/wremnants/postprocessing/np_monotonicity.py`.
- Confirm $y_{\max}=2.5$ matches the operational dilepton acceptance; revisit if a wider $y$ range is ever fit.

## 8. Implementation (provisional)

File: `WRemnants/wremnants/postprocessing/np_monotonicity.py`. Self-contained module.

**Hard-coded `PARAM_MAP`.** Single source of truth: for each of the six NP nuisances (`scetlibNPgammaLambda2/4/Inf`, `scetlibNPLambda2`, `scetlibNPDelta_Lambda2`, `scetlibNPLambda4`), store the physical `{nominal, up_value, down_value}` plus the matching `{hist_up_label, hist_down_label}` from the histmaker syst axis. Values are the AN-25-085 centrals plus the lattice-uncertainty templates (`rabbit_theory_helper.py:686-711` for CS LatticeNoConstraints; `:827-882` for TMD Delta_Lambda).

Linearization rabbit pull $\theta\to$ physical parameter:
$$\text{param}(\theta) = \text{nominal} + \max(\theta,0)(\text{up\_value}-\text{nominal}) - \max(-\theta,0)(\text{nominal}-\text{down\_value})$$
Piecewise form handles asymmetric $\Lambda_4$ ($0.06{\pm}^{0.10}_{0.05}$) and the **inverted CS convention** (Up template carries the *smaller* physical value, per `rabbit_theory_helper.py:706-710`) uniformly — delta_up/delta_down can be negative for the inverted case.

Sanity gate: `verify_param_map_against_hist(corr_hist)` cross-checks the hard-coded values against the actual syst-axis labels. Call this once from setupRabbit / rabbit_theory_helper.py so any drift in the histmaker templates surfaces as a loud error rather than silent regularizer mismatch.

**`NPMonotonicityMapping(BaseMapping)`** is vestigial: just stores `self.indata` and an optional criterion override (`"a"` or `"b"`). No JSON, no file paths.

**`NPMonotonicityWall(Regularizer)`** looks up each NP nuisance's index in `indata.systs` at init, then in `compute_nll_penalty(params, observables)` extracts the six pulls, maps to physical $\lambda/\Lambda$ via the piecewise form, evaluates
$$P = [\max(0, -\lambda_4-\sqrt{k_{\rm CS}\lambda_2\lambda_6})]^2 + \sum_{y\in\{0,y_{\max}\}} [\max(0,-c_1(y)-\sqrt{k_{\rm TMD}\Lambda_6 L_2(y)})]^2 + (\text{small-}b_T\text{ positivity hinges})$$
with $(k_{\rm CS},k_{\rm TMD})=(3,20)$ for criterion (b) (default) or $(4,36)$ for (a). Classes built lazily via PEP-562 `__getattr__`.

**Fit-time invocation:**
```
rabbit_fit.py <indata>.hdf5 ... \
  -r wremnants.postprocessing.np_monotonicity.NPMonotonicityWall \
     wremnants.postprocessing.np_monotonicity.NPMonotonicityMapping \
  --regularizationStrength <tau> \
  --noConstrainParams 'scetlibNPgamma.*|scetlibNPLambda.*|scetlibNPDelta_Lambda.*'
```
The penalty is multiplied by $e^{2\tau}$ inside `fitter.py:2491`, so $\tau$ controls wall hardness. `--noConstrainParams` drops the Gaussian priors on the NP nuisances so the regularizer is the sole constraint. To switch criterion: append a positional arg `a` after the mapping class name.

**Not yet wired:**
- One-line call to `verify_param_map_against_hist(self.corr_hist)` from `add_gamma_np_uncertainties` (or wherever the corr_hist is in hand) in `rabbit_theory_helper.py`. Guards against histmaker template drift.
- Removal of the existing `scale=10.0` blanket inflation on `LatticeNoConstraints` (`rabbit_theory_helper.py:738-739`). The user plans to drop it in favor of `--noConstrainParams` + regularizer.

## 9. The damping-fold forms (`tanh_6_abs`) — a wall-free alternative

Added 2026-07-28 (`WRemnants/wremnants/postprocessing/scetlib_np/btgrid_tf.py::abs_fold_tf`,
registry rows `tanh_6_abs` in `params.py`). The alternative to constraining $\lambda$
with a wall: constrain the FORM instead, by folding its damping exponent through
$\mathrm{fold}(x)=|x+m|-m$ (the shape constant $m\ge 0$ = `abs_margin` /
`abs_margin_nu`, which must be FROZEN — the model raises otherwise):

$$F_{\rm eff}=\exp\!\big[-\mathrm{fold}\big(2\Lambda_\infty b_T\tanh B\big)\big],\qquad
\tilde\gamma_\nu^{\rm NP}=-\mathrm{fold}\big(\lambda_\infty^\nu\tanh A\big).$$

The margin is the **allowed excursion of the FUNCTION**, so what you set is what the
form factor is capped at: `abs_margin` enters the exponent-space fold as $\ln(1+m)$ giving
$F_{\rm eff}\le 1+m$ (`abs_margin=0.2` $\Rightarrow$ $F_{\rm eff}\le1.2$), while the CS cap is
additive already, $\tilde\gamma_\nu\le m_\nu$. That is **exactly the constraint the deleted
`NPFunctionBound` regularizer tried to impose** ($F_{\rm eff}\le1.2$, $\tilde\gamma_\nu\le0.2$;
removed 2026-07-27 because the fit *railed against* its soft cap → boundary solution, EDM
$-7.5$, no usable covariance) — here as an **identity, not a penalty**, so there is no
threshold to rail against, no `--regularizationStrength`, and the gradient stays defined.

**What it guarantees, for every $\lambda$ of either sign (including $\Lambda_\infty<0$):**
- $F_{\rm eff}\le 1+m$ and $\tilde\gamma_\nu\le m_\nu$, **uniformly in $b_T$**, and the cap is
  TIGHT (a tune that wants to anti-damp saturates it: measured 1.01999 at $m=0.02$, 1.1999 at
  $m=0.2$). At $m=0$: $F_{\rm eff}\le1$, $\tilde\gamma_\nu\le0$ — the damping conditions of
  §2–4, by construction. Hence NO `NPDampingWall` term is needed; the wall accepts the form
  and contributes exactly 0.
- **Exact reduction**: wherever the exponent is $\ge -m$ — i.e. on the whole physical
  (damping) region — the fold is the identity, so `tanh_6_abs` IS `tanh_6`, bit-for-bit
  (verified: $\sigma_{\rm gen}$ ratio $=1$ on the gen grid, and both form factors to 0 ulp).
  So a card closure / $\lambda$-response validated under `tanh_6` carries over unchanged.
  Contrast `tanh_6_sigmoid`, which only reduces in the $b_T^{\rm cut}\to\infty$ limit.
- The fold sits on the **exponent**, not the tanh argument: at $m=0$ the two are the same
  function ($b_T,\Lambda_\infty>0$ give $|2\Lambda_\infty b\tanh B| = 2\Lambda_\infty b\tanh|B|$),
  but an argument-space margin permits anti-damping $\propto\exp(2\Lambda_\infty b_T\tanh m)$,
  which grows with $b_T$ — and our $b_T$ grid reaches 50 GeV$^{-1}$.

**What it does NOT give you — read this before calling a folded fit physical:**
- **The $\lambda$ are not made physical, only the prediction is.** A folded tune is a
  damping-but-KINKED form factor no physical-$\lambda$ `tanh_6` can produce (locally rising
  in $b_T$; measured 45–61 rising steps out of 2000 on $\Lambda_6<0$ / $\Lambda_2<0$ tunes).
  The fold therefore *enlarges* the accessible shape family rather than shrinking the model.
  Diagnose with `param_model_diagnostics.fold_activity` (fold-active $b_T$ fraction per side);
  fold INACTIVE ⇒ the tune really is a `tanh_6` tune.
- **$\sigma(q_T)\ge0$ is a separate condition and is NOT enforced.** Large $|B|$ saturates the
  tanh, so the folded $F_{\rm eff}\to\exp(-2\Lambda_\infty b_T)$: the maximal-damping limit.
  Measured on the study's $C+\delta\Lambda_2=-3.35$ tune: $F_{\rm eff}\le1$ ✓, but the matched
  native $\sigma(q_T)$ is 4% negative-area, $-49\%$ of peak at $q_T=75$ GeV inside $|Y|\le2.5$
  — the (negative) fixed-order nonsingular showing through an over-damped resummed piece.
- **Saturation flatness.** In that saturated region the $\lambda$-derivatives collapse
  ($|J|_{\max}\sim3\times10^{-6}$, $|K|_{\max}\sim10^{-9}$ vs $O(1)$ on physical tunes): finite
  and NaN-free (unlike the unfolded divergence), but $\lambda$-insensitive — expect huge
  postfit errors / near-degenerate directions if a fit lands there.
- **Exact mirror degeneracy at $m=0$.** Both tanh arguments are ODD under flipping
  $(\Lambda_2,\Lambda_4,\Lambda_6,\Delta\Lambda_2)$ (resp. $(\lambda_2,\lambda_4,\lambda_6)^\nu$)
  together, so $\mathrm{fold}$ makes the prediction EXACTLY invariant under $\lambda\to-\lambda$:
  two mirror minima, and the sign of a postfit $\lambda$ is a branch choice, not a measurement.
  $m>0$ breaks it (the offset is not producible by a polynomial vanishing at $b_T=0$).
- SCETlib cannot produce this form ⇒ it is a **numerator-only** (evaluation) form, never a
  card/denominator form: `--modelArgs np_model_fit=tanh_6_abs np_model_nu_fit=tanh_6_abs`.

**Fold margin $\ne$ wall margin — different quantity, opposite sign convention.** The
`NPDampingWall`'s `margin` (module default `NP_DAMPING_MARGIN` $=5\times10^{-3}$) is a cushion on
the **polynomial coefficients**, applied as `relu2(margin - coeff)`: **positive = STRICTER**
than physical, negative = permit anti-damping. The fold's margin caps the **function value**:
**positive = MORE permissive**. They coincide only at 0, where both mean "exactly damping" —
verified: over a random $\lambda$ scan, every point the wall accepts at margin 0 has
$\max_b F_{\rm eff}=1$ exactly, i.e. the wall's margin-0 feasible set IS the fold's identity
region. And a coefficient-space cushion does NOT bound the excursion — with $\Lambda_6$ frozen
at $+0.01$ (as in the 2D runs), the worst accepted $F_{\rm eff}$ is 1.49 at wall margin
$-0.02$, 2.77 at $-0.05$, 9.84 at $-0.10$; with $\Lambda_6$ FLOATING a negative wall margin
admits $\Lambda_6<0$ (where the `minQ` expression is not the true minimum) and the excursion is
unbounded ($2.7\times10^{43}$ hit in the scan). So "let it go a little negative" in wall units
is not a small excursion, and is not comparable to the same number as a fold margin.

Validation: `python -m wremnants.postprocessing.scetlib_np.validation.abs_fold`.

## 10. The CS kernel has a STRONG external constraint — use it (added 2026-07-29)

Everything in §2–4 above is *physicality* (sign/monotonicity). For the **CS kernel only**, there is
also a quantitative **magnitude** constraint, and it is tighter than any wall we have built.

**Do not describe γ_ν^NP as weakly constrained.** That is true of the TMD b.c. (Λ₂, ΔΛ₂, Λ₄) — the AN
says outright those "do not have robust external constraints". γ_ν^NP is the opposite: flavor- and
process-universal, lattice-computable, and AN-25-085 already carries its full 3×3 lattice covariance
(eq. `nplunc`, from Cridge–Marinelli–Tackmann [arXiv:2506.13874](https://arxiv.org/abs/2506.13874),
JHEP 12 (2025) 043, fitting Shu:2023cot / LatticePartonLPC:2023pdv / Avkhadiev:2023poz):

λ_∞ = 1.6853 ± 0.5069,  λ₂ = 0.0870 ± 0.0332 GeV²,  λ₄ = 0.0074 ± 0.0066 GeV⁴,
ρ = (λ_∞λ₂ +0.5212, λ_∞λ₄ −0.7249, λ₂λ₄ −0.9135).

**External corroboration (checked 2026-07-29):** [arXiv:2511.22547](https://arxiv.org/html/2511.22547)
gives a continuum + physical-mass lattice CS kernel over b⊥ ≈ 0.1–1 fm, monotone, agreeing with 8
independent pheno extractions (SV19, ART23, IFY23, EEC24, ASWZ24, MAPNN25, ART25, CFR25).
[arXiv:2510.26489](https://arxiv.org/abs/2510.26489) (first joint lattice+DY CSK fit) gives
g₂ = 0.167 ± 0.015 in the CSS form g_K(b) = 2g₂²b² ⇒ 2g₂² = 0.056 GeV², against our λ₂/2 = 0.044 GeV²
— consistent up to convention factors. **That CSS form is sign-definite by construction:** no
determination anywhere, lattice or pheno, has an anti-damping NP CS kernel.

**Lattice band on the FUNCTION** (propagated through eq. `npgamma` with the full covariance; bound the
function, not the parameters — ρ(λ₂,λ₄) = −0.91 makes the parameters near-degenerate):

| b_T [1/GeV] | b_T [fm] | −γ_ν^NP central | ±1σ | 3σ window (with λ₂≥0, λ₄≥0 floor) |
|---|---|---|---|---|
| 0.5 | 0.10 | 0.011 | 0.004 | [0.001, 0.020] |
| 1.0 | 0.20 | 0.047 | 0.014 | [0.010, 0.079] |
| 2.0 | 0.39 | 0.227 | 0.026 | [0.082, 0.303] |
| 3.0 | 0.59 | 0.569 | 0.047 | [0.082, 0.702] |
| ≳5 | ≳1.0 | 0.842 | 0.250 | [0.08, 1.35] |

Marginal 3σ parameter box: **λ₂_ν ∈ [0, 0.19] GeV², λ₄_ν ∈ [−0.012, +0.027] GeV⁴, λ_∞^ν ∈ (0, 3.2]**,
and −γ_ν^NP ≤ ~1.5 uniformly in b_T.

> ⚠️ **DO NOT USE THIS COVARIANCE AS A FIT PRIOR** (Luca, 2026-07-29, from the lattice authors
> directly: *the covariance is not ready to be trusted*). The table above is a **scale reference
> only** — how big the CS-kernel NP function is, and how narrow the b_T region that matters is. An
> earlier version of this section recommended a "3σ correlated lattice Gaussian" prior; that
> recommendation is **WITHDRAWN**. See §11 for what to do instead.

**Four facts that follow, and that keep getting forgotten:**
1. **The α_s-sensitive b_T window sits inside the lattice's range.** b_T ≈ 0.5–3 GeV⁻¹ = 0.1–0.6 fm,
   where the band is ±20–30%. Only λ_∞ (the b_T ≳ 5 GeV⁻¹ asymptote) is genuinely loose, and the qT
   spectrum barely probes it — by b_T = 5 GeV⁻¹ the tanh is already 86% saturated.
2. **The ×10-DECORRELATED "alternative" prior is what permits the sign flip.** σ(λ₂_ν) = 0.332 > the
   central 0.087, so the prior itself puts λ₂_ν = 0 only 0.26σ away. Under the **correlated**
   covariance the flip is 3.1σ down the λ₂-dominant eigendirection σ₂ (Δχ² ≈ 9.6 — comparable to the
   damping wall's ≈16.6). The correlated lattice prior is *already* an effective wall, and a smooth
   one. In the AN, ×10-decorrelated is a **cross-check**, never the nominal.
3. **Freezing λ_∞^ν removes the loose direction.** σ₁ (the largest eigenvalue) is 99.9% λ_∞. So a fit
   that freezes λ_∞^ν = 2 keeps only the *tight* directions σ₂, σ₃ — an argument against inflating
   what's left.
4. **The lattice bound is tighter than the monotonicity wall on λ₄_ν.** At λ₂_ν = 0.087, λ₆_ν = 0.01
   the §3(b) floor is −√(3·0.087·0.01) = −0.051, **4× looser** than the 3σ lattice floor −0.012. The
   wall was never the binding constraint on the b⁴ term. And **λ₆_ν has no lattice constraint at all**
   (the lattice fit used the tanh_2 form, λ₆ = 0) — freeze it, and never let a bound derived from it
   do load-bearing work.

**Known tension.** Our walled fits rail at λ₂_ν → 0⁺, i.e. the data want *less* CS-kernel NP damping
than the lattice central says (λ₂_ν = 0.0043 is −2.5σ_lat; λ₄_ν = +0.034 is +4.0σ_lat; the unwalled
optimum is −14σ_lat / +25σ_lat). Report that, don't bury it.

## 11. What to do instead of a lattice prior (2026-07-29)

Given §10's ⚠️ (covariance not trustworthy per its authors), the recommendation is **bracket, don't
prior**. Separate what we're confident about from what we aren't:

**Confident, needs NO covariance — the SIGN and SHAPE.** Every determination (continuum lattice over
0.1–1 fm; the 8 pheno extractions it is compared against) is one-signed and monotone, and the standard
CSS form g_K(b) = 2g₂²**b²** is *structurally* incapable of being wrong-sign. So:

> **The only CS-kernel bound defensible without a covariance:** λ₂_ν ≥ 0,
> λ₄_ν ≥ −√(3 λ₂_ν λ₆_ν), λ_∞^ν > 0 — i.e. −γ_ν^NP ≥ 0 and monotone in b_T.
> = the existing `NPDampingWall` CS block at margin 0. Zero cost at any physical tune.

**Confident to ~±30% — the CENTRAL magnitude**, from data-only routes that don't touch the distrusted
covariance: DY-only g₂ = 0.186 ± 0.033, lattice-only 0.152 ± 0.027, joint 0.167 ± 0.015
⇒ 2g₂² ≈ 0.045–0.069 GeV², vs our λ₂_ν = 0.087 GeV² (agreement at the "same ballpark, convention
factors unresolved" level — **the g₂ ↔ λ₂_ν mapping is NOT 1:1**, do not quote it as a range).

**NOT confident — the uncertainty/correlations.** So do not encode them at all.

**Prescription:**
1. Hard damping+monotonicity bound above. Nothing else.
2. **Freeze the CS λ; do not float them.** Take the α_s spread across a *scan of frozen values* as the
   NP-CS systematic. A frozen-variation systematic needs only centrals + a credible range — no
   covariance, no correlations — and cannot rail.
3. **Check first whether it matters:** our own fit has ρ(λ₄, λ₂_ν) = −0.996, ρ(λ₄, λ₄_ν) = −0.953. The
   wrong-sign CS pull may be a near-degenerate reshuffle against the TMD b⁴ term, not a CS-kernel
   statement. If freezing moves θ(α_s) ≪ σ(α_s), the bound question is moot. Item 2 gives this free.
4. **Build the frozen range from published FUNCTIONS, not covariances** (the piece of work still to do):
   fit our tanh_2 form to the published CS-kernel curves (SV19, ART23, MAPNN25, Nov-2025 lattice band)
   over b_T ≈ 0.5–3 GeV⁻¹ and read off the λ₂_ν spread. Expectation ~[0.05, 0.15] GeV², but **measure
   it, don't assert it.**

**The railing is physics, not a numerical problem.** If the data want λ₂_ν < 0 and you forbid it, you
get a boundary solution regardless of technique — wall, reparametrization (λ₂_ν = t² / e^t), or the
§9 `tanh_6_abs` fold. Freezing sidesteps it; nothing *solves* it. Report the frozen-fit α_s plus the
excursion as a systematic, and the free fit's preference for unphysical as a documented tension.

**If the lattice CENTRALS are also in doubt** (Luca's 2026-07-29 remark was about the covariance), then
only item 1 survives: fit free-inside-physical and report the boundary solution as such.

Study narrative: `studies/np-wall-local-minima/LOGBOOK.md` (2026-07-29 late entries).

## 12. The CS kernel is CAPPED, and our λ_∞^ν is frozen ⇒ the fit λ are turn-on-POSITION knobs

> **⚠️ READ §13 FIRST — γ̃_ν vs γ̃_ζ.** Everything in this section is written in the **γ̃_ζ**
> convention (the AN's eq. `npgamma`, and what lattice papers plot). **Our code and our plots use
> γ̃_ν = 2·γ̃_ζ**, so every number below doubles there. §13 has the mapping.

**Hard cap, exact, for any λ:** |tanh| ≤ 1 in eq. `npgamma` ⇒ **|γ̃_ζ^NP| ≤ λ_∞^ν/2** (equivalently
|γ̃_ν^NP| ≤ λ_∞^ν). So the question
"can the CS kernel exceed 1?" has a one-line answer for our fits: **λ_∞^ν is FROZEN at 2.0**
(`np_monotonicity_franks.py::LAMBDA_INF_NU_FIXED`) ⇒ the ceiling is **exactly 1.0** and cannot be
exceeded. Exceeding 1 needs λ_∞^ν > 2; the lattice gives λ_∞^ν = 1.6853 ± 0.5069 ⇒ cap 0.84 ± 0.25, so
a cap > 1 is a +0.6σ excursion — allowed, no evidence for, nothing physically special about 1. (The
"−γ_ν^NP ≤ ~1.5" in §10's 3σ box assumed λ_∞^ν FLOATING to 3σ; with it frozen, 1.0 is the operative
number.) NB the **full** CS kernel = perturbative + NP is a different object and is NOT capped by this.

**Consequence — this is the part that reframes the bound question.** With λ_∞^ν frozen, the depth is
fixed by hand and λ₂_ν/λ₄_ν only move *where* γ_ν^NP turns on. Every tune we have saturates the cap by
b_T ≈ 2.2–2.4 GeV⁻¹, spanning only ~10% in turn-on position:

| tune | cap = λ_∞^ν/2 | b_T @50% cap | @90% | −γ_ν^NP(b=2) | (b=3) |
|---|---|---|---|---|---|
| lattice central | 0.843 | 2.60 | 3.65 | 0.227 | 0.569 |
| card central (FranksVals) | 1.000 | 1.94 | 2.43 | 0.551 | 1.000 |
| walled 2D optimum | 1.000 | 1.97 | 2.38 | 0.535 | 1.000 |
| nowall / basin C | 1.000 | 1.85 | 2.16 | 0.733 | 1.000 |

So a "magnitude bound" on the CS kernel is largely moot while λ_∞^ν is frozen — the contested quantity
is the turn-on position, plus (unwalled) whether γ_ν^NP goes wrong-sign at small b_T first.

**Lattice centrals + the ±1σ the templates are built from** (`np_monotonicity.py:113-125`):

| | central | −1σ | +1σ |
|---|---|---|---|
| λ_∞^ν | 1.6853 | 1.1784 | 2.1922 |
| λ₂_ν | 0.0870 GeV² | 0.0538 | 0.1202 |
| λ₄_ν | 0.0074 GeV⁴ | 0.0008 | 0.0140 |

λ₆_ν: **no lattice value** (the lattice fit used the tanh_2 form).

**⚠️ OUR CARD DOES NOT SIT ON THE LATTICE CENTRALS.** FranksVals uses λ₂_ν = 0.15 (**+1.9σ_lat**),
λ₄_ν = 0.0 (**−1.1σ_lat**), λ_∞^ν = 2.0 (**+0.62σ_lat**). Yet the lattice *eigenvariation templates* ARE
built around the lattice centrals — the histmaker label strings prove it
(`theory_variation_labels.py::LATTICE_GAMMA_NP_UNCERTAINTIES`: Eigvar1 `lambda2_nu0.0696`/`0.1044`
straddle 0.0870; Eigvar2 `0.1153`/`0.0587` likewise). **So we vary around one central and evaluate at
another.** Net effect where it matters: the card's CS kernel is ~2.4× deeper than the lattice central at
b_T = 2 GeV⁻¹ (0.551 vs 0.227) and saturates 19% deeper. This is a **central-vs-central** discrepancy —
it stands regardless of §10's covariance-trust problem — and deserves a deliberate decision rather than
inheritance.

## 13. γ̃_ν vs γ̃_ζ — the factor 2, and where each convention is used (2026-07-31)

**Primary source: Cridge, Marinelli, Tackmann [arXiv:2506.13874](https://arxiv.org/abs/2506.13874)
Eq. (3.32)** — the paper that extracted the lattice data into OUR parametrization:

$$2\,\tilde\gamma_\zeta^{\rm np}(b_T) \;=\; \tilde\gamma_\nu^{\rm np}(b_T) \;=\; -\lambda_\infty
\tanh\!\Big(\tfrac{\lambda_2}{\lambda_\infty}b_T^2 + \tfrac{\lambda_4}{\lambda_\infty}b_T^4\Big)$$

| | expression | small-$b_T$ | saturation cap | used by |
|---|---|---|---|---|
| $\tilde\gamma_\nu^{\rm NP}$ | $-\lambda_\infty\tanh A$ | $-\lambda_2 b_T^2$ | $\lambda_\infty^\nu$ (=**2.0**) | **our code + plots** (`btgrid_tf.py:331,337`, `np_function_plots.py` y-label) |
| $\tilde\gamma_\zeta^{\rm NP}$ | $-\tfrac{\lambda_\infty}{2}\tanh A$ | $-\tfrac{\lambda_2}{2}b_T^2$ | $\lambda_\infty^\nu/2$ (=**1.0**) | **AN eq. `npgamma`**, the paper's $\gamma_\zeta$, and **what lattice papers plot** |

**Nothing is broken** — the code pairs $\tilde\gamma_\nu$ with the grid's $C_\nu$ consistently (hence the
0.14% validation). But **our plot is 2× the object a lattice paper shows**, and that is the first thing
to correct before concluding our CS kernel "looks wrong".

**To compare our curve to a lattice CS-kernel figure, three corrections, all required:**
1. **×½** — plot $\tilde\gamma_\zeta = \tilde\gamma_\nu/2$.
2. **Add the perturbative piece.** Paper Eq. (3.27): $\tilde\gamma_\zeta = \tilde\gamma_\zeta^{\rm pert}
   (b^*(b_T),\mu) + \tilde\gamma_\zeta^{\rm np}(b_T)$. Ours is the **np piece only** and vanishes at
   $b_T\to0$ by construction; the lattice full kernel does not. Our cached grid absorbs the perturbative
   part into `I_pert` (NP-off integrand), so it is NOT available standalone — getting it means going back
   to SCETlib.
3. **Units/range.** We plot $b_T$ in GeV⁻¹ out to 50; lattice papers use fm out to ~1
   (1 fm = 5.068 GeV⁻¹), so their whole x-range is our first 10%.

**The b\* prescription (paper Eq. 3.30)** — sextic, not the usual quadratic:
$b^*(b_T) = b_T\,(1 + b_T^6/b_{\max}^6)^{-1/6}$ with $b_0/b_{\max} = 1$ GeV ⇒ $b_{\max}\approx1.12$ GeV⁻¹.
Chosen so the perturbative result differs from canonical only at $O(b_T^6)$. **CHECKED 2026-07-31 —
our setup is EQUIVALENT; see §15.**

### Consequence for the damping wall: the margin is ~2× stronger on the CS side

`np_damping_wall.py` applies ONE `margin` to both sides' coefficient conditions (`minP` for CS, `minQ`
for TMD — same GeV² units, same algebraic role). Chaining each through to the integrand
($\ln$ integrand $\supset C_\nu\tilde\gamma_\nu + \ln F_{\rm eff}$, `btgrid_tf.py:404`), the $b_T^2$ and
both $\lambda_\infty$ cancel and the sensitivity ratio is **$C_\nu/2$**, measured from the grid:

| $b_T$ | dCS/dm | dTMD/dm | ratio ($=C_\nu/2$) |
|---|---|---|---|
| 0.5 | −0.853 | −0.499 | 1.71 |
| 1.0 | −4.047 | −1.995 | 2.03 |
| 2.0 | −16.868 | −7.222 | 2.34 |
| ≥3 | ~0 | ~0 | — (both tanh saturated by λ₆=λ₆_ν=0.01) |

So **one margin is ~2× stricter on CS than on TMD in prediction space.** For equal strictness the CS
margin should be ≈ half the TMD one ⇒ **split `margin` into per-side knobs.** (An earlier version of this
analysis used the AN's ½ and wrongly concluded the two sides were commensurate to 15% — the code has no ½.)
Other real asymmetries: the TMD side is charged at 2 Y points vs the CS side's 1, with **Y_MAX = 5 outside
the |Y| ≤ 2.5 acceptance**; and `wall(l6)`/`wall(l6_nu)` compare a GeV²-scale margin to GeV⁶ coefficients
(inert only because both are frozen at 0.01). Also **25% of grid points have $C_\nu = 0$** — the CS kernel
has no effect on the prediction there at all.

### Why the covariance "isn't ready" — the documentary reason

Eq. (3.34)/(3.35) (the λ **and** the correlation matrix) come from *"Using Ref. [66]"*, and
**Ref. [66] = B. Dehnadi, P. Ploessl, F. J. Tackmann, "Flavor thresholds and quark-mass effects in the
Collins-Soper kernel," 2025 — no arXiv number, in preparation.** The AN is carrying numbers from an
unpublished analysis. Consistent with what the lattice authors told Luca (2026-07-29).

The paper itself never calls them a prior: they are *"representative values for the CS kernel parameters
of our model"* for **Asimov pseudodata**, and imposing them *"helps guide the exploration of parameter
space"*. That is much weaker than a constraint — direct support for §11's bracket-don't-prior line.

**Which lattice data was fitted:** refs **[89–91]** = 2307.12359 (Avkhadiev et al.), 2306.06488 (LPC),
2302.06502 (Shu et al.) — exactly the AN's three. **[92] = 2402.06725** (Avkhadiev et al., PRL 132,
231901 — the same group's later determination, first with systematic control of quark mass, operator
mixing and discretization) is **cited but NOT in the fitted set**. So the AN's centrals rest on a
superseded vintage of one of their own inputs.

**How the covariance is derived** (asked 2026-07-31): it is the parameter covariance of a 3-parameter
fit of Eq. (3.32) to the [89–91] lattice data, done in Ref. [66]. The paper does **not** state the χ²,
how the three datasets' own uncertainties/inter-correlations were treated, the fitted b_T range, or
whether the errors are Hessian — all of that is in the unpublished Ref. [66]. What the numbers show:
eigenvalues 2.57e−1 / 8.19e−4 / 3.43e−6, a **75,000:1 spread (277:1 in σ)**. σ₁ is 99.9% λ_∞ (σ = 0.507
on 1.685 → 30%, essentially unconstrained); σ₃ is mostly λ₄ with σ = 0.0019. That is what fitting a
SATURATING function to data that stops at b_T ≲ 1 fm — where the tanh is only ~86% saturated — must
give: λ_∞ is extrapolated past the data, and λ₂/λ₄ carry the usual b²/b⁴ anti-correlation (ρ = −0.914).
A covariance with that condition number, from an undocumented fit, has off-diagonals sensitive to
choices you cannot inspect. **The CENTRAL curve is on much firmer ground than the band** — it is the
shape the data pin inside the fitted range.

## 14. `tanh_6_pos` — structural damping instead of a CS wall (2026-07-31)

Implemented (`btgrid_tf.pos_floor_tf` + registry row `tanh_6_pos`). The CS answer to §11: make damping
an IDENTITY rather than a penalty or a prior, so there is no boundary to rail against and no covariance
to trust.

$$\lambda_{2\nu}^{\rm eff} = \tfrac{1}{2}\big(\lambda_{2\nu} + \sqrt{\lambda_{2\nu}^2 + 4f^2}\big)$$

applied to λ₂_ν BEFORE it enters the tanh argument. **With λ₄_ν frozen at 0 and λ₆_ν frozen ≥ 0** every
coefficient of the argument is non-negative ⇒ γ_ν ≤ 0 and monotone hold for ANY λ₂_ν. λ₂_ν stays free on
(0, ∞) — the magnitude, which is what should be free.

**Why this map and not `t²` / `exp` / the `*_abs` fold:** `t²` and the fold are **EVEN**, so they
reintroduce the exact λ → −λ mirror degeneracy that made `tanh_6_abs` unusable at margin 0 (§9). This
map is MONOTONE ⇒ no mirror. And its Jacobian never vanishes, unlike `t²`/`exp` at the boundary.

Validated in-container (`gamma_nu_NP_tf`, λ_∞^ν = 2, λ₆_ν = 0.01, f = 3e−3):

| property | result |
|---|---|
| damping + monotone for λ₂_ν ∈ [−10⁶, 10⁶] | ALL PASS (max γ_ν ≤ −1e−26) |
| reduction to plain `tanh_6` on the physical region | rel. 1.6e−4 at λ₂_ν = 0.087, 8e−5 at 0.15 |
| mirror degeneracy | ABSENT (Δ = 0.48 between ±0.15; the abs fold gives 0) |
| gradient at/below the boundary | nonzero everywhere |

**Wiring:** `params.GNU_MODEL_PARAMS['tanh_6_pos']`; `pos_floor_nu` added to `CONST_PARAMS` (frozen, and
a HARD error if floated — it is exactly degenerate with λ₂_ν on the identity region);
`np_damping_wall.UNCONDITIONAL_FORMS` now includes it so the CS block is skipped. Because switching form
SILENCES the CS wall, `SCETlibNPParamModel._check_pos_form_preconditions` **refuses to run** unless λ₄_ν
is frozen at 0 and λ₆_ν frozen ≥ 0 — otherwise you get an unconstrained CS side that logs as
"structurally physical".

```
fitterSCETlibNP.py <card> \
  --modelArgs np_model_nu_fit=tanh_6_pos \
     xparam_default=lambda4_nu=0,lambda6_nu=0.01,pos_floor_nu=0.003 \
  --freeze lambda4_nu lambda6_nu pos_floor_nu lambda_inf_nu lambda_inf
```

**Caveats.** If the data really want λ₂_ν < 0 the fit sits on a flat plateau (λ₂_ν^eff → 0⁺): gradient
defined but ~10⁴× smaller by λ₂_ν = −0.5, and **the postfit λ₂_ν is then NOT meaningful — read the sign,
not the value**. `f` sets both the reduction accuracy and the plateau floor.

**TRY THE CHEAP TEST FIRST:** plain `tanh_6`, λ₄_ν frozen at 0, UNWALLED. Refitting the walled kernel
with λ₄_ν = 0 gives λ₂_ν = 0.118 (+0.9σ_lat) — if the fit lands positive, none of this machinery is
needed and the condition becomes a check. (Not a pure degeneracy though: rms 0.032, and at b_T = 1 the
walled tune is −0.024 vs −0.064, so λ₄_ν = 0 does remove a real "delayed turn-on" direction and will
cost some NLL. It is the direction lattice most disagrees with — walled λ₄/λ₂ = 7.8 vs lattice 0.085.)

### TMD side: keep the wall, fix two things

Decision (2026-07-31): the same trick does NOT extend to the TMD, so wall it — but
(1) **Y_MAX 5 → 2.5**, the acceptance (it is the only TMD term binding at the walled optimum, and it is
out of acceptance), and (2) give it **its own margin** (trivially separable now that the CS side does not
use the wall — this retires the §13 C_ν/2 asymmetry).

Why not structural: the TMD condition is genuinely 2-parameter — L₂(y) = Λ₂ + ΔΛ₂y² ≥ 0 needs Λ₂ ≥ 0
AND Λ₂ + ΔΛ₂y_max² ≥ 0, with ΔΛ₂ legitimately either sign — so one positivity map cannot cover it. And
unlike the CS kernel the TMD has NO external constraint (the AN says so), so the data should determine
it; a margin-0 wall bites only at the physical boundary, which is the right behaviour. The TMD terms are
already nearly inert; fixing Y_MAX may make the wall never bite, which is ideal.

**Principled upgrade if the TMD keeps escaping:** reparametrize L₂ by its two ANCHORS L₂(0) and L₂(2.5),
both through `pos_floor_tf`, instead of (Λ₂, ΔΛ₂). L₂ is linear in y², so non-negativity at the endpoints
guarantees it on the whole interval — exact, wall-free, and it retires the Y_MAX question by
construction. Cost: changes the fitted parameter basis (λ_central, tables, cards). Not done.

## 16. External reference for the TMD b.c.: MAP22 → our (Λ₂, ΔΛ₂, Λ₄) (2026-08-03)

§10-11 said the TMD b.c. has no external constraint. It now has an external *reference*.

**Source substitution — read this first.** Luca asked for [arXiv:2502.04166](https://arxiv.org/abs/2502.04166)
(MAP neural-network TMD extraction, "MAPNN25"). **That fit has NO numerical release** —
`mapcollaboration.github.io` serves only a 10–13 MB plot report of base64 PNGs, and there is no NN entry
in NangaParbat's `FitResults`. So the mapping uses **MAP22 at N3LL**, which IS fully released
(`MapCollaboration/NangaParbat-Legacy`, `FitResults/MAP22_N3LL`: 21-parameter closed form
`MAP22g52` + **251 replicas**), is the same collaboration / data / perturbative order, and is the
benchmark 2502.04166 itself compares against (NN χ² 0.97 vs MAP22 1.28, NN bands smaller). Treat these
numbers as the MAP22 approximation to the NN.

**The map.** MAP22g52 `ifunc<2` (TMD PDF) intrinsic part, with their evolution factor
`exp(−g₂²b²ln(ζ/Q₀²)/4)` **STRIPPED** — that is their CS kernel, which in our model is γ_ν^NP;
keeping it would double-count. Their f_int is PER HADRON, ours is the two-beam product, so the target is
$f_{\rm int}(x_1,b)\,f_{\rm int}(x_2,b)$ with $x_{1,2}=(Q/\sqrt s)e^{\pm Y}$ — **which is where ΔΛ₂ comes
from: predicted, not fitted.** At Z/13 TeV: x = 7.0e−3 at Y=0; x₁=0.085, x₂=5.8e−4 at Y=2.5.

### Y sampling — the only choice in the mapping fit that moves the answer (2026-08-03)

The b grid is immaterial (Λ₂ within 0.0006 over b<2…b<5). **Y is not**, because ΔΛ₂ multiplies Y² and the
true L₂(Y) is not quadratic — the fit compresses a curve into one number, so the sampling decides which
number. Measured (`scripts/ysampling.py`, central replica):

| Y sampling / weighting | Λ₂ | ΔΛ₂ | Λ₄ |
|---|---|---|---|
| uniform in Y, 6 pts (what `map_replicas.py` uses) | 0.0988 | −0.00746 | 0.00028 |
| uniform in Y, 26 pts | 0.0993 | −0.00782 | 0.00030 |
| uniform in Y, 101 pts | 0.0994 | **−0.00790** | 0.00031 |
| uniform in Y², 6 / 26 pts | 0.0988 / 0.0998 | −0.00756 / −0.00793 | 0.00024 / 0.00026 |
| weight ∝ 1−(Y/3)² | 0.0991 | −0.00784 | 0.00034 |
| weight ∝ exp(−Y²/2) | 0.0986 | −0.00765 | 0.00039 |
| **anchors only, Y = {0, 2.5}** | 0.0983 | **−0.00718** | 0.00018 |
| | | **spread 0.00075** (= replica σ 0.00076) | |

1. **The 6-point grid is UNDER-CONVERGED.** 6 → 26 → 101 pts: −0.00746 → −0.00782 → −0.00790.
   **Converged ΔΛ₂ = −0.0079.** Free fix: raise the point count in `map_replicas.py:52`.
2. **Scheme and physical weighting are immaterial** — uniform-Y vs uniform-Y² differ by 0.0001, a
   cross-section-like forward falloff by 0.0002. So the "weight by dσ/dY / by the full Hankel integrand"
   upgrade is **NOT needed**; it would change nothing at this precision.
3. **The 0.00075 spread belongs in the budget** ⇒ quote **ΔΛ₂ = −0.0079 ± 0.0011**, not
   −0.00743 ± 0.00076.
4. **Which definition is right depends on the use** (they differ by 0.0007, inside the uncertainty, so
   currently immaterial — but pick deliberately): *comparing to a fitted δλ₂* → least-squares over the
   acceptance (−0.0079), because that is what a fit does; *freezing/priorng δλ₂* so the model matches
   MAP's L₂ at the acceptance edges → **anchors** (−0.0072), which also lines up with the §14 anchor basis.

**Consequence for §16b:** with the converged value the agreement with the 2D fits is **0.7–0.9σ**, not the
0.5σ first quoted (davidFix −0.00599 ± 0.00193 → 0.86σ; `260702` −0.00634 ± 0.00201 → 0.68σ). Still good;
the earlier number compared against the under-converged −0.00743.

**Result — fit our tanh_6 F_eff to each of the 251 replicas** (`studies/np-wall-local-minima/scripts/
map_replicas.py`, replicas cached in `scripts/map22_replicas/`):

| | value | ±1σ (replica spread) | 68% |
|---|---|---|---|
| Λ₂ | **+0.0969** GeV² | 0.0063 | [0.0909, 0.1026] |
| ΔΛ₂ | **−0.00743** GeV² | 0.00076 | [−0.00809, −0.00672] |
| Λ₄ | **+0.00027** GeV⁴ | 0.00017 | [0.00010, 0.00043] |

ρ(Λ₂,ΔΛ₂) = −0.726, ρ(ΔΛ₂,Λ₄) = +0.458, ρ(Λ₂,Λ₄) = −0.035. Mapping quality: median rms on F_eff
**0.0051**, worst 0.0175. **This covariance is derived by us from the released replicas** — none of §13's
unpublished-provenance problem.

**Three findings:**
1. **λ₆ = 0.01 breaks the mapping.** With the card's λ₆ frozen at 0.01 the best fit is rms **0.108** and
   lands on a NON-MONOTONE tune; release λ₆ and it goes to **0** with rms **0.0045**. So our tanh family
   represents MAP22 excellently — but only at λ₆ = 0. **Second independent strike against λ₆ = 0.01**,
   after §12/§15 showed λ₆_ν = 0.01 saturates the CS kernel ~1.5× too early. (Λ_∞ is degenerate with Λ₂
   in the linear regime and runs away if floated — keep it frozen at 1.)
2. **ΔΛ₂ has the OPPOSITE SIGN to what we use.** L₂(Y) falls monotonically 0.2347 → 0.1956 over
   Y = 0 → 2.5, i.e. **less** TMD damping at forward rapidity ⇒ ΔΛ₂ < 0 in **251/251 replicas**. The AN
   nominal uses **+0.125** and our fits pull **+0.15**. Mechanism: MAP22's g₁(x) ∝ x^0.515, so the
   low-x beam (5.8e−4 at Y=2.5) damps less, and the two-beam product is less damped than at Y=0. Since
   δλ₂ is the basin-C escape route and our least-constrained λ, an external prediction disagreeing in
   SIGN matters.
3. **Λ₂ = 0.097 sits between the AN nominal (0.25) and our walled postfit (0.0073)** — a prior there
   pulls Λ₂ UP. Same direction as the CS finding that the card is over-damped.

**⚠️ These widths are VERY tight — do not use them at face value.** σ(ΔΛ₂) = 0.00076 is **26× tighter**
than the AN's own ±0.02 prefit variation, and it is centred ~0.16 away from where the fit wants to sit.
A face-width prior would effectively FREEZE ΔΛ₂ hundreds of σ from the fit's preference — a violent
constraint, not a gentle one. Inflate substantially, or use as a frozen alternative (§11's
bracket-don't-prior) rather than a prior.

**Residual scheme caveats:** MAP22 uses its own b\* (2502.04166 Eq. 4, with **b_min ≠ 0**, which we do
not have) at **N3LL** with MSHT2020; f_NP is by definition the remainder after a particular perturbative
piece, so their NP is not scheme-identical to ours. And the map is a shape match at Z kinematics only.

### 16b. ΔΛ₂ VALIDATED against the 2D fits — and the rule for what transfers (2026-08-03)

**Our rapidity-SENSITIVE fits already agree with the MAP22-derived ΔΛ₂ at 0.5σ:**

| source | ΔΛ₂ |
|---|---|
| 2D `260702_2D_l6nu0p01_l60p01` | **−0.00634 ± 0.00201** |
| 2D `260717_2D_wallmargin_0` | −0.00668 |
| 2D `260723_Z_2D` / `_davidFix` | −0.00596 / −0.00599 |
| MAP22-derived (§16) | **−0.00743 ± 0.00076** |

Two independent routes — our 2D fit to Z ptll×yll, and MAP22's x-dependence through Born kinematics +
the two-beam product — land on the same number. **There is NO ΔΛ₂ tension.** An earlier version of §16
framed "fitted +0.125 vs derived −0.0074" as a sign clash; that was wrong. The correct reading:

* **2D (has a yll axis): δλ₂ = −0.006 ± 0.002** — agrees with the external derivation.
* **1D ptll: +0.15** — from a fit with **ZERO rapidity information**, where δλ₂ is an absorber, not a
  measurement. Do not quote it as a determination of the y shape.
* **AN nominal +0.125** — inherited from the mW analysis (2412.13872), a different observable/setup.

This also **retires the flavour-blindness caveat** on the mapping: an independent fit reproducing the
number at 0.5σ says MAP22's flavour-independent f_NP is adequate *for this quantity*, and validates the
two-beam construction, the Born x₁,₂ = (Q/√s)e^{±Y} map, and the evolution-stripping.

**The right plot for this: divide the magnitude out.** Comparing F_eff curves directly OVERSTATES the
y disagreement, because our Λ₂ (0.165) and MAP's (0.097) differ by 2σ (see the CORRECTION below; an
earlier version said 11σ, which was wrong), so our curves have all decayed by
b_T ≈ 2.5 and the y spread is visually compressed. Plot **F_eff(b,y)/F_eff(b,0)** instead — that divides
out Λ₂ and leaves only the rapidity shape, the part that transfers. At b_T = 2:

| | y = 1.5 | y = 2.5 |
|---|---|---|
| MAP22 (external) | 1.126 | 1.428 |
| **2D ptll×yll postfit** | **1.104** | **1.319** |
| 1D ptll postfit | 0.117 | 0.049 |

⇒ 2D agrees with MAP22 to **2% (y=1.5) / 8% (y=2.5)**; 1D is inverted by a factor ~30.
Script: `studies/np-wall-local-minima/scripts/ydep_ratio.py` →
`~/public_html/alphaS/260803_map22_ydep/ydep_ratio_only.png`.

**Plot from `--fitresult`, never hand-typed λ** (Luca, 2026-08-03). Reference command:
```
python3 -m wremnants.postprocessing.scetlib_np.np_function_plots \
  --fitresult <run>/cov/fitresults.hdf5 --bT-max 4 --y 0 1.5 2.5 -o out.png
```
The `cov/` pass gives the postfit λ AND the 68% band; forms and freezes are read from the fit's
meta_info. Walled 2D davidFix: `260723_Z_2D_davidFix/cov/fitresults.hdf5` →
`~/public_html/alphaS/260803_map22_ydep/np_2D_davidFix_vs_map22.png`.

**Style rule (a real bug, fixed 2026-08-03):** the MAP22 reference shares the per-y colour ramp with the
plotted series *on purpose* (compare like y with like y), and `fitresult_lambdas` draws the PREFIT series
with `linestyle="--"`. The reference was originally dashed too ⇒ **indistinguishable from prefit**, and it
made me misread a plot (I attributed MAP22's y-spread to the prefit). Reference is now **DOTTED**
`(0,(1,1.3))`. Keep the three families distinct: dotted = external reference, dashed = prefit, solid =
postfit. (The CS-panel lattice reference does not have this problem — it is grey, not colour-ramped.)

**⚠️ The card's λ_central has δλ₂ = 0** — verified from the davidFix fit's prefit column, and consistent
with the FranksVals TRUTH dict in `scripts/rabbit/scetlib_np/closure_suite.py`. So the CARD HAS NO
RAPIDITY DEPENDENCE, and every bit of y structure in the model comes from the fit. The AN quotes
ΔΛ₂ = 0.125 GeV² as nominal, so the card does not implement the AN nominal — the same pattern as the CS
side (card λ₂_ν = 0.15 vs AN/lattice 0.087, §12). Internally consistent with FranksVals; inconsistent
with the AN.

**One residual difference, and it is λ₆ again:** above b_T ≈ 2.5 our ratio returns toward 1 while MAP's
keeps rising, because λ₆ = 0.01's b⁵ term saturates the tanh and saturation is y-INDEPENDENT, so all
rapidities converge. MAP has no b⁶ content. **Third independent appearance of λ₆ = 0.01 distorting the
model** (§12/§15 CS early saturation; §16 blocking the MAP mapping; here flattening the y dependence).
Low-leverage region, so it does not change the conclusion.

### ⚠️ CORRECTION (2026-08-03): "Λ₂ does not transfer / 11σ" was WRONG — all three agree ≤2σ

An earlier version of this section claimed Λ₂ was ~11σ discrepant and derived a rule from it
("take the y-shape, not the magnitude; keep Λ₂ free"). **Both are retracted.** The 11σ came from
dividing by **MAP's uncertainty alone**, ignoring our own postfit σ. Using both (Luca pushed back and was
right to — the scheme explanation was answering a discrepancy that did not exist):

| param | ours (2D davidFix) | MAP-derived | diff | σ_comb | **pull** |
|---|---|---|---|---|---|
| Λ₂ | 0.16284 ± 0.03137 | 0.09754 ± 0.00650 | 0.0653 | 0.0320 | **2.04σ** |
| ΔΛ₂ | −0.00599 ± 0.00193 | −0.00785 ± 0.00120 | 0.00186 | 0.00227 | **0.82σ** |
| Λ₄ | −0.01809 ± 0.04828 | 0.00029 ± 0.00020 | −0.01838 | 0.04828 | **−0.38σ** |

**Verified the Λ₂ difference is real, not a labelling artifact**: the local coefficient
−ln F/(2b²) — parametrization-independent — is FLAT for both (ours 0.159–0.172, MAP 0.0976–0.0982 over
b = 0.2…1.5), and the mapping reproduces MAP22 itself to 4 digits. So 0.163 vs 0.0975 is a genuine
function-level difference; it is simply a 2σ one. (Our 1D fit gives 0.0069 → 0.0352 over the same range,
i.e. NOT flat ⇒ λ₂ is not even a meaningful local coefficient there. Another reason 1D is unusable.)

> **REVISED RULE: use ALL THREE as priors.** Ordered by information gained:
> **Λ₄** σ 0.048 → 0.0002 (**240×**, tension 0.4σ) — by far the biggest gain, because our fit barely
> constrains λ₄ at all (central −0.018, error 0.048); **Λ₂** σ 0.031 → 0.0065 (4.8×, 2.0σ);
> **ΔΛ₂** σ 0.0019 → 0.0012 (1.6×, 0.8σ).
> What survives of the scheme argument: their b_min ≠ 0 / N3LL / MSHT20 mean their NP is not defined
> identically to ours, so some **inflation is prudent** — especially on Λ₂ where a 2σ tension already
> exists. That is a reason to widen, not to exclude.

### 16c. Should the y parametrization be made more flexible? NO (decided 2026-08-03)

1. **It is validated, not deficient** — see 16b: where the data can constrain δλ₂ it hits the external
   value at 0.5σ.
2. **Quadratic-vs-true shape error is 1.6% of L₂**, an order of magnitude below the fit's own
   σ(δλ₂) = 0.002. (The true L₂(Y) is not exactly quadratic — the local coefficient
   (L₂(Y)−L₂(0))/Y² runs −0.0040 at Y=0.5 to −0.0076 at Y=2, a factor ~2 — but that structure sits far
   below resolution.)
3. **1D has NO y information**, so extra y parameters there are pure unconstrained freedom, and
   ρ(α_s, δλ₂) = −0.4…−0.6 means it leaks straight into σ(α_s).
4. **δλ₂ is the basin-C escape route** (→ +1.37 unwalled, F_eff = 369). A second y lever = a second
   channel for the same escape.

If flexibility is ever genuinely needed, the route is NOT a bolted-on y⁴ term but the **anchor basis**
(§14): fit L₂ at anchors instead of (Λ₂, ΔΛ₂). Two anchors ≡ the present freedom but with positivity
structural; a third anchor then buys non-quadratic shape cheaply and safely.

**Mechanism of the y dependence, for reference.** x₁x₂ = Q²/s is FIXED; only x₁/x₂ = e^{2Y} moves, so
the Y dependence is what happens to the pair when it SPREADS at fixed geometric mean. With
ln f^NP ≈ −c(x)b²/4 one gets **L₂(Y) = [c(x₁)+c(x₂)]/8**. For a power law c ∝ x^p this is
2c(x̄)cosh(pY) — *always increasing*, so any power-law NP forces ΔΛ₂ > 0 (the usual intuition). MAP22's
c(x) is **not** a power law: it PEAKS near x ≈ 0.02 (dln c/dln x: +0.52 at 5.8e−4, +0.32 at 7e−3,
+0.008 at 0.02, −0.51 at 0.05). Our Y=0 sits at x = 7.0e−3, just below the peak, so as Y grows the
rising beam climbs to the peak by Y≈1 and then comes back DOWN while the falling beam loses
monotonically ⇒ the sum drops 45% ⇒ ΔΛ₂ < 0. **c(x) concave in ln x is the whole reason.** Analytic
small-b gives −0.00725 vs −0.00746 from the full fit. Script: `scripts/ydep.py` (in scratch; re-derive
from `map_replicas.py` if needed).

**Plotter:** `np_function_plots.py` now draws the MAP22 F_eff analogue on the TMD panel **by default**
(colour-matched per y, dashed), alongside the §13 lattice reference on the CS panel.
`--no-map22-reference`, `--map22-Q`, `--map22-sqrts` (defaults: on-shell Z, 13 TeV). The inverted
y-ordering between our fit and MAP22 makes finding 2 visible at a glance.

## 15. b\* check: our scale floors ARE the paper's b\* (2026-07-31) — a hypothesis that DIED

Ran against the actual bt-grid config (`btgrid_cache.load(...)['config']`) and the SCETlib source at
`/work/submit/lavezzo/alphaS/scetlib-cms-newnp-lambda4fix`.

**`b0_over_bmax = 0` does NOT mean "b\* off."** `Scale_provider.cpp:31-34` says outright: *"the b\*
prescription WILL compound with all minimum scales (except muf_min) unless the user sets b0_bmax = 0."*
The freeze is applied via the **scale floors**, through the same `_mu_star(mu, mu_min)` helper:
config has `mu0_min = mub_min = mus_min = 1.` GeV, and 1 GeV is exactly the paper's cutoff,
b_max = b₀/(1 GeV) = 1.1229 GeV⁻¹.

| b_T | b\*_eff (our scale floor) | b\*_paper (Eq. 3.30) |
|---|---|---|
| 0.5 | 0.4948 | 0.4989 |
| 1.0 | 0.8845 | 0.9340 |
| 2.0 | 1.0965 | 1.1171 |
| ≥5 | **1.1229** | **1.1229** |

Same cutoff, same value, same plateau; the forms differ (quartic `_mu_star` vs sextic b\*) so the
transition near b_T ≈ 1 differs by a few %. **No Landau pole, nothing for the NP kernel to absorb.**
Setting `b0_over_bmax = 0` here is CORRECT — enabling it would double-regulate. The hypothesis that the
anti-damping bump at b_T ≈ 1.2 came from an unfrozen perturbative↔NP handover is **dead**; do not
resurrect it without new evidence.

**Other facts the check nailed down:**
- **`b_bar == bT` exactly** in the grid (verified array-wise, max|Δ| = 0) ⇒ the NP functions take bare
  b_T, matching Eqs. (3.32)/(3.33). Open item closed. (`b0_over_bmax_nu = 1.` sits in the config but the
  exported `b_bar` is bare b_T — the export hands the NP evaluation to us.)
- **`nus_min = 0.`** — the rapidity scale ν_S is the ONLY unfloored scale (every virtuality plateaus at
  1 GeV). Measured signature: C_ν = 0.548·ln(b_T) + 4.69 over 3 < b_T < 50, residual rms 0.083 — a clean
  logarithm, no plateau. **Probably intentional, NOT a lead:** γ_ν^NP → −λ_∞ *is* the large-b_T rapidity
  regulator, so C_ν·γ_ν^NP → −λ_∞ ln b_T is power-law suppression; flooring ν too would leave the NP CS
  kernel with nothing to do at large b_T. Worth one sanity question to Frank, not a study.
- **Grid config NP block:** `np_model_nu = tanh_2`, `lambda6_nu = 0.0007`, `lambda_inf_nu = -2.`,
  `np_model = tanh_2`, `lambda6 = 0.016`, `lambda_inf = 1.`, all λ₂/λ₄ = 0. So the recorded CS λ₆_ν is
  **0.0007**, matching §1 — and **14× below the 0.01 the fits run**, on the b⁶ term, i.e. exactly the
  sharpest-turn-on knob §14 shows the data want. Caveat: this grid is the NP-OFF export, so those
  entries may be inert for `I_pert`/`C_nu`, and the operative λ_central comes from the histmaker
  meta_info — **resolve the numerator/denominator λ₆_ν mismatch before drawing conclusions from it.**

**Status of the shape finding (§14):** it stands on its own (the data want a later/sharper turn-on plus
an anti-damping bump no positive λ can make), but there is now **no mechanism explaining why**. Do not
substitute `nus_min` for the dead b\* story without evidence.

## 17. Why the postfit uncertainty band widens with b_T (2026-08-06)

Question from the interactive summary page ("why do the uncertainties blow up at large b_T?"). It is
the parametrization, not the band method: **the same λ multiply growing powers of b_T inside an
exponent**, so a constant σ(λ) is amplified by b_T², b_T⁴, b_T⁶.

Unsaturated (tanh B → B), from §1:

$$\ln f^{\rm NP}(b_T,y) \;\simeq\; -2\Big[L_2(y)\,b_T^2 + \big(\Lambda_4 + L_2^3/3\Lambda_\infty^2\big) b_T^4 + \Lambda_6 b_T^6\Big]
\;\Rightarrow\; \frac{\partial \ln f}{\partial \Lambda_2} = -2b_T^2,\quad \frac{\partial \ln f}{\partial \Lambda_4} = -2b_T^4 .$$

Measured on `cs2_tmdB_nowall_seedWalledFull` (2D MSHT20, CS lat-diag + TMD prior, no wall, warm;
2000 toys off the postfit covariance, y = 0), band = 16–84 percentile width of ln f:

| b_T | ln f | band(ln f) | Λ₂ term | Λ₄ term | envelope 2Λ∞b_T |
|---|---|---|---|---|---|
| 0.5 | −0.061 | 0.018 | 0.009 | 0.000 | 1.0 |
| 1.0 | −0.243 | 0.070 | 0.036 | 0.001 | 2.0 |
| 2.0 | −0.994 | 0.277 | 0.152 | 0.018 | 4.0 |
| 3.0 | −2.296 | 0.620 | 0.365 | 0.092 | 6.0 |
| 4.0 | −4.179 | 1.068 | 0.707 | 0.291 | 8.0 |

with σ(Λ₂) = 0.0179, σ(Λ₄) = 0.00057. The per-λ columns scale **exactly** as b_T² and b_T⁴ (Λ₄:
0.001 → 0.018 → 0.092 → 0.291 is 1 : 16 : 81 : 256), so Λ₂ dominates everywhere but Λ₄ closes the gap
fast; a σ(Λ₄) invisible below b_T ≈ 1.5 is a third of the width by b_T = 4. Since the plotted quantity
is $f = e^{\ln f}$, a linear growth of the band in ln f is decades in f — that is the "blow-up".

Two things bound it, and they differ between the sectors:

- **TMD b.c.**: bounded only by the saturation envelope $|\ln f| \le 2\Lambda_\infty b_T$, which itself
  GROWS linearly. A well-constrained run stays far inside it (1.07 vs 8 at b_T = 4 above); an
  unconstrained one (unwalled + fakelumi) fills it — F_eff band [e^−4, e^+4] at b_T = 2 — which is the
  honest statement that the data do not constrain the TMD b.c. there at all.
- **CS kernel**: $\tilde\gamma_\nu = -\lambda_\infty^\nu \tanh A$ is bounded by $\lambda_\infty^\nu$
  with **no b_T prefactor**, so its band peaks in the turn-on region and then CLOSES: same run, band
  0.178 at b_T = 2, 0.110 at b_T = 3, **0.000** at b_T = 4 where tanh A = 1.0000 and every toy gives
  −λ∞^ν exactly. A CS band that stays wide at large b_T means the tune has not saturated by b_T = 4,
  which is itself the diagnostic (cf. §12: our λ are turn-on-POSITION knobs).

Practical consequence: at large b_T compare the band BETWEEN runs, not against its own central curve —
the absolute width there is dominated by the b_T^n amplification and by extrapolation beyond where the
qT spectrum has any lever (b_T ≳ 2 GeV⁻¹ ↔ qT ≲ 0.5 GeV, below the first ptll bin).

## 18. Is the LATTICE CS kernel directly translatable to ours? (2026-08-11)

Short answer: **the full kernel yes, the NP piece we fit no.** Sourced from the Cridge–Marinelli–Tackmann
text itself ([arXiv:2506.13874](https://arxiv.org/abs/2506.13874) §3.3, pp. 19–21) and from
Avkhadiev–Shanahan–Wagman–Zhao [arXiv:2402.06725](https://arxiv.org/abs/2402.06725) (PRL 132, 231901).

**(a) The definitions DO line up — no hidden factor on the lattice side.**
Lattice def: $\gamma(b_T,\mu) = 2\,\mathrm{d}\ln \tilde f^{\rm TMD}/\mathrm{d}\ln\zeta$. Paper Eq. (3.25):
$\tilde f(\zeta) = \tilde f(\zeta_0)\exp[\tfrac12\tilde\gamma_\zeta\ln(\zeta/\zeta_0)]$ ⇒
$\tilde\gamma_\zeta = 2\,\mathrm{d}\ln\tilde f/\mathrm{d}\ln\zeta$ — **the same object, same sign, same
normalization**. Eq. (3.26): $\tilde\gamma_\zeta = \tilde\gamma_\nu/2$. So the ×½ of §13 is between *our
code* and the lattice, not a lattice-convention issue. Both are MS-bar quark kernels, flavor-, x-, and
hadron-independent (the lattice uses pion states; legitimate for exactly that reason), process-universal
(DY ↔ SIDIS). μ is not an obstruction in principle: $\mathrm{d}\tilde\gamma_\nu/\mathrm{d}\ln\mu =
-4\Gamma^q_{\rm cusp}$ (⇒ $-2\Gamma_{\rm cusp}$ for $\tilde\gamma_\zeta$) is perturbative and exact.
Beware OTHER conventions (Collins' $K$, Vladimirov's $\mathcal D$, CSS $g_K/g_2$) — those do differ by
factors/sign; check each one, and see §10 on why $g_2 \leftrightarrow \lambda_2$ is not 1:1.

**(b) What we fit is a SUBTRACTION REMAINDER, and it is scheme-dependent. Paper's own words** (p. 19,
under Eq. 3.27): the left-hand sides "are defined in full QCD. The separation into perturbative and
nonperturbative parts on the right-hand side is well defined, but **a priori not unique**. Namely, the
exact definition of the nonperturbative pieces … is **implicitly determined by the exact definition of
the perturbative pieces** … including all choices of boundary scales and cutoff prescriptions used to
avoid the Landau pole." For us that scheme is: $\tilde\gamma_\zeta^{\rm pert}(b^*(b_T),\mu)$ with the
sextic $b^*$ (Eq. 3.30, $b_0/b_{\max}=1$ GeV), at the paper's resummation order and boundary scales.
⇒ **you cannot read λ off any published CS-kernel curve, lattice or pheno, without redoing that exact
subtraction.** The one convention-light bridge is the OPE: $\tilde\gamma_\zeta^{\rm np} = \lambda^\zeta_2
b_T^2 + O(b_T^4)$ (Eq. 3.29), and the sextic $b^*$ was chosen so the perturbative piece "does not alter
the OPE below $O(b_T^6)$" ⇒ **λ₂ (and λ₄) are the b²/b⁴ OPE coefficients** (λ₂ ties to a gluon vacuum
condensate). Compare *those*, not the functions. **λ_∞ is NOT an OPE coefficient** — pure large-$b_T$
model, and no lattice data reaches there.

**(c) The stated blocker is MASSIVE QUARKS / FLAVOR THRESHOLDS.** p. 19: lattice "in principle … allows
one to obtain information on $\tilde\gamma_\zeta^{\rm np}(b_T)$ …, **for which a proper treatment of
massive quark corrections is however essential** [66]"; p. 21: "This **requires** properly accounting for
quark flavor thresholds and quark mass effects as will be discussed in Ref. [66]." Why it bites: over the
lattice window $b_T \approx 0.1$–1 fm the perturbative kernel lives at $\mu_b = b_0/b_T \approx$ 0.4–4 GeV,
straddling $m_c$ and $m_b$; 2402.06725 matches with **massless fixed $n_f=4$** and (per its text) has no
charm/bottom-mass or threshold discussion. The scale of the contamination is set by the same paper's own
App. A.3: fitting mass-effect-inclusive Asimov data with a massless 5-flavor model biases
$\alpha_s(m_Z)$ by **1.32×10⁻³**, "entirely driven by the bottom quark mass", because the α_s pull comes
from $q_T\sim5$ GeV $\sim m_b$ — i.e. the same $b_T$ region where we want to trust a lattice→λ mapping.
This is why Eq. (3.34) is not a plain fit to a lattice curve: it is the output of **Ref. [66] = Dehnadi,
Ploessl, Tackmann, "Flavor thresholds and quark-mass effects in the CS kernel" — still unpublished**.

**(d) And it is the WRONG VINTAGE of the lattice input.** Verified against the paper's bibliography:
Eq. (3.34) fits **[89–91]** = 2307.12359 (Avkhadiev '23, physical pion mass), 2306.06488 (LPC),
2302.06502 (Shu et al.) — exactly the AN's three (`theory.tex:257`). **2402.06725 is ref [92]**: it
appears only in the generic "can be accessed via lattice QCD [87–92]" list and is **NOT in the fitted
set**, even though it is the same group's superseded-predecessor-replacing determination (continuum
extrapolation over $a=0.15/0.12/0.09$ fm, $N_f=2+1+1$ HISQ at physical $m_\pi$, uNNLL matching + leading
renormalon subtraction, systematic control of quark mass / operator mixing / discretization). So
**"SCETlib took the constraint from 2402.06725" is not what happened** — our λ predate it.

**(e) b_T coverage is inverted relative to what we need.** Lattice reaches $b_T \lesssim 1.05$ fm on the
coarsest ensemble but only 0.63 fm on the finest, with discretization corrections $\propto a/b_T$ and
$a^2/b_T^2$ ⇒ **least precise at small $b_T$**, which is exactly the α_s window ($b_T\approx$ 0.5–3 GeV⁻¹
= 0.1–0.6 fm, §10). λ_∞ ($b_T\gtrsim5$ GeV⁻¹ = 1 fm) is pure tanh extrapolation beyond all data.

**Verdict / what a defensible translation requires:** (1) go to $\tilde\gamma_\zeta$ units (×½ off our
plots), (2) add back our $\tilde\gamma_\zeta^{\rm pert}(b^*,\mu)$ and compare **full** kernels at a common
μ, (3) with a matched flavor/quark-mass treatment, (4) over 0.1–0.6 fm only, or else compare **only** the
b²/b⁴ OPE coefficients. Anything short of that is a shape/ballpark statement, not a constraint — which is
consistent with the paper never calling Eq. (3.34) a prior ("representative values … for our model",
for Asimov pseudodata) and with §10 ⚠️/§11 (bracket, don't prior).
