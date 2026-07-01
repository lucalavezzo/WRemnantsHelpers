# NP-model parameter constraints (CS kernel and TMD b.c.)

Source: AN-25-085 `theory.tex` Eqs. \ref{eq:npgamma}, \ref{eq:npf} (lines 233–234), with our locally-added $\lambda_6,\Lambda_6$ extensions.
Last updated: 2026-05-11
Status: provisional — algebra derived, not yet implemented in the fit.

## 1. Functional forms

Define $L_2(y)\equiv\Lambda_2+\Delta\Lambda_2\,y^2$.

**CS kernel** (with $\lambda_6\,b_T^6$ added inside the tanh):
$$\tilde\gamma_\zeta^{\rm NP}(b_T) \;=\; -\frac{\lambda_\infty}{2}\,\tanh\!A(b_T),
\qquad A(b_T)=\frac{\lambda_2}{\lambda_\infty}b_T^2+\frac{\lambda_4}{\lambda_\infty}b_T^4+\frac{\lambda_6}{\lambda_\infty}b_T^6.$$

**TMD boundary condition** (with $\Lambda_6\,b_T^5$ added inside the tanh, paralleling the AN's odd-power TMD argument):
$$f^{\rm NP}(b_T,y) \;=\; \exp\!\big[-2\Lambda_\infty\,b_T\,\tanh B(b_T,y)\big],$$
$$B(b_T,y)\;=\;\frac{L_2(y)}{\Lambda_\infty}b_T+\frac{\Lambda_4}{\Lambda_\infty}b_T^3+\frac{L_2(y)^3}{3\Lambda_\infty}b_T^3+\frac{\Lambda_6}{\Lambda_\infty}b_T^5.$$

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
