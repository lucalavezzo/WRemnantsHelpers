---
title: Wall margin keyword
slug: 260930-wall-margin-keyword
study: walled-multistart-census
status: done        # active | done | paused | abandoned
created: 2026-09-30
updated: 2026-09-30
owner: study-worker
---

# Wall margin keyword

**Task:** Can the NP damping wall's margin be set from the `-r` line (`margin=<float>`), with margin = 0 reproducing the intended loss exactly, while the default behaviour (margin 5e-3) stays bit-identical?

---

## START HERE (status as of 2026-09-30)

> **Yes. `margin=<float>` is a new `NPDampingMapping` keyword. The default stays bit-identical, and margin = 0 gives exactly the intended loss on the real nominal fit.**
> On LATL4ZY35WALLWARM, the default wall at τ = 5 reproduces the stored `nllvalreduced` with **diff = 0.0**. At the same x,
> loss(margin 0, τ 8) − loss(default, τ 5) matches e¹⁶·pen₀ − e¹⁰·pen₅ to **1.0e-14**. With margin 0, **no condition is active** at
> this point. With the default margin, one condition is active: L2 at |Y| = 2.5, coefficient 4.62e-3 < 5e-3, which contributes 3.21e-3 to the loss.
> The change is **uncommitted** in the WRemnants working tree, as instructed. Container lint (black 26.5.1, isort, flake8) passes.

- **Next action:** none. T2 can use the `-r` syntax given below. **Put `margin=0` after the MAPPING class, and do not use `fitterAD.sh --wall`.**
- **Blocking on:** nothing. Luca should review and commit the diff.

---

## Result

**Comparability caveats first.**
- Every number here is the loss at ONE fixed parameter vector: the stored postfit x of the blinded real-data fit
  LATL4ZY35WALLWARM (card A + lattice term, λ4_ν held at 0, `pdf62_y35_260921/merged_full_bin0xzero`).
- No minimisation was run, so none of this says where a margin-0 fit will land. That is T2.
- `alphaS` stayed blinded, with the offsets armed as in the fit, and is never printed. The NP λ below are POUs, which rabbit does not blind.

### Step 1: unit level, no cache (`scripts/unit_check_margin.py`, output `unit_check_margin.out`)

Setup for these checks:
- Every supported form pair × smallb ∈ {0, 1}.
- 207 λ points: a lattice-like tune, all λ set to 0, set to the margin, just past the margin, and at −0.05, plus 200 random points spanning both sides of every boundary.

What was checked:
- "default≠orig" compares against the **pre-change HEAD blob** (`scripts/np_damping_wall_orig.py`), with exact `==` on labels, names, bounds and penalties, in both numpy and TF.
- "pen≠relu2" checks each penalty against `relu2(bound − coeff)`, for margin = 5e-3 and margin = 0. Here bound = margin for margin-carrying conditions, `LAMBDA_INF_FLOOR` for the λ_inf floors, and 0 for the tanh_6 interior discriminants.

| np_model | np_model_nu | smallb | #cond | #margin-carrying | #λ points | default≠orig (bits) | pen≠relu2(bound−coeff) | max abs dev |
|---|---|---|---|---|---|---|---|---|
| tanh_2 | tanh_2 | 1 | 8 | 6 | 207 | 0 | 0 | 0.0e+00 |
| tanh_2 | tanh_2 | 0 | 5 | 3 | 207 | 0 | 0 | 0.0e+00 |
| tanh_2 | tanh_6 | 1 | 9 | 6 | 207 | 0 | 0 | 0.0e+00 |
| tanh_2 | tanh_6 | 0 | 6 | 3 | 207 | 0 | 0 | 0.0e+00 |
| tanh_6 | tanh_2 | 1 | 10 | 6 | 207 | 0 | 0 | 6.8e-21 |
| tanh_6 | tanh_2 | 0 | 7 | 3 | 207 | 0 | 0 | 6.8e-21 |
| tanh_6 | tanh_6 | 1 | 11 | 6 | 207 | 0 | 0 | 6.8e-21 |
| tanh_6 | tanh_6 | 0 | 8 | 3 | 207 | 0 | 0 | 6.8e-21 |

| -r mapping args | mapping.margin | key | key == pre-change key |
|---|---|---|---|
| `(none)` | 0.005 | `NPDampingMapping smallb=1` | True |
| `smallb=0` | 0.005 | `NPDampingMapping smallb=0` | True |
| `ymax=2.5` | 0.005 | `NPDampingMapping smallb=1 ymax=2.5` | True |
| `smallb=0 ymax=2.5` | 0.005 | `NPDampingMapping smallb=0 ymax=2.5` | True |
| `margin=0` | 0.0 | `NPDampingMapping smallb=1 margin=0` | n/a (new key) |
| `margin=0.0` | 0.0 | `NPDampingMapping smallb=1 margin=0` | n/a (new key) |
| `margin=1e-4 smallb=0` | 0.0001 | `NPDampingMapping smallb=0 margin=0.0001` | n/a (new key) |
| `margin=5e-3` | 0.005 | `NPDampingMapping smallb=1 margin=0.005` | n/a (new key) |

| refused input | error |
|---|---|
| `margin=-1e-3` | np_damping_wall: margin must be finite and >= 0, got '-1e-3'. A negative margin would wall a region PAST the d |
| `margin=nan` | np_damping_wall: margin must be finite and >= 0, got 'nan'. A negative margin would wall a region PAST the dam |
| `margin=inf` | np_damping_wall: margin must be finite and >= 0, got 'inf'. A negative margin would wall a region PAST the dam |
| `margin=-0.0001` | np_damping_wall: margin must be finite and >= 0, got '-0.0001'. A negative margin would wall a region PAST the |
| `margin=abc` | np_damping_wall: margin must be a number, got 'abc' |
| `margin=` | np_damping_wall: margin must be a number, got '' |

margin=-0 parses to -0.0 (== 0.0: True); relu2 identical.
pre-change module refuses margin=0 as expected: NPDampingMapping: unknown key 'margin'; only 'smallb' and 'ymax' are supported (the lambda_inf floor and the damping margin are fixed module constants).

TOTAL FAILURES: 0

The 6.8e-21 max deviation appears only for tanh_6 TMD. It is the difference between the TF and numpy evaluators (`tf.square` vs `**2` inside the self-gating discriminant). It is not a margin effect: the default-vs-orig comparison is exactly 0 in both evaluators separately.

### Step 2: one gated cache load on the real nominal fit (`scripts/margin_loss_gate.py`, output `margin_loss_gate.json`, log `logs/margin_loss_gate.log`)

How the fitter was rebuilt:
- The Fitter was rebuilt from the fitresult's own `meta_info` command: same card (md5 as in the fit log), cache, `fit_params`, and `prior_sigmas=lambda2_nu=nan`. The lattice term is in the card, and the freeze list follows from `fit_params`.
- Three flags were dropped: `-o`, `--snapshotFile` and `--snapshotInterval`, so that nothing could write next to the stored fit.
- τ and the regulariser were set before the first trace, then `defaultassign` → arm, `set_nobs(data)`, blinding on, `load_fitresult`.
- The job ran through `mem_gate.sh` with a 330 GB request. The cache loaded in 35 s via the raw-rules fast path.
- Every "fresh" loss is a new `tf.function` trace of `_compute_nll`, because the regulariser list is read at trace time.

| quantity | value |
|---|---|
| stored `nllvalreduced` | 376.6942441689123 |
| **(a)** `reduced_nll()`, default wall, τ = 5 | 376.6942441689123 (**diff 0.0**) |
| same, fresh trace | 376.6942441689123 (diff 0.0) |
| unwalled base loss (fresh trace, no regulariser) | 376.69103432608273 |
| pen₅ = `reg5.compute_nll_penalty(x)` (eager) | 1.4572663901e-07 |
| pen₀ = `reg0.compute_nll_penalty(x)` (eager) | 0.0 |
| **(b)** loss(margin 0, τ 8), fresh trace | 376.69103432608273 |
| **(b)** lhs = loss(m0, τ8) − loss(def, τ5) | −3.2098428295626e-03 |
| **(b)** rhs = e¹⁶·pen₀ − e¹⁰·pen₅ | −3.2098428295726e-03 |
| **(b) lhs − rhs** | **+1.0e-14** |
| loss(def, τ5) − (base + e¹⁰·pen₅) | 0.0 |
| loss(m0, τ8) − (base + e¹⁶·pen₀) | 0.0 |

The rhs uses the eager penalties and the lhs uses the traced losses. The 1e-14 residual is the float64 rounding of a 376-sized loss (ulp ≈ 5.7e-14).

**(c) Conditions at this x.**
- Physical λ at the fitted point: λ2 = 0.02901, λ4 = 0.08732, δλ2 = −0.003902, λ2_ν = 0.06339.
- Held: λ_inf = 1, λ_inf_nu = 2, λ4_ν = 0.
- The three held-only conditions (the two λ_inf floors and λ4_ν ≥ 0) are dropped as constants under both margins. The drop check uses the bare condition, as before, so λ4_ν held exactly at 0 stays legal at any margin.

| condition (armed) | coeff | margin 5e-3: pen × e¹⁰ | margin 0: pen × e¹⁶ | active @5e-3 | active @0 |
|---|---|---|---|---|---|
| λ2_ν ≥ m (CS small-b) | 0.06339 | 0 | 0 | no | no |
| λ2 + δλ2·Y² ≥ m at \|Y\|=0 | 0.02901 | 0 | 0 | no | no |
| 3λ_inf²λ4 + L2³ ≥ m at \|Y\|=0 | 0.26200 | 0 | 0 | no | no |
| **λ2 + δλ2·Y² ≥ m at \|Y\|=2.5** | **0.004618** | **3.21e-3** | **0** | **yes** | no |
| 3λ_inf²λ4 + L2³ ≥ m at \|Y\|=2.5 | 0.26197 | 0 | 0 | no | no |

**Physics read.**
- The nominal walled minimum rails on exactly one wall: the **TMD small-b turn-on at the edge of the gen acceptance**, L2(|Y| = 2.5) = λ2 + 6.25·δλ2.
- It sits 3.8e-4 past the 5e-3 cushion. That is the soft-wall equilibrium past the knee described in the module docstring, and it is still inside the true damping region (L2 > 0).
- With margin 0 that wall is slack at this x, and the loss drops by 3.21e-3. So a margin-0 re-minimisation (T2) starts at a point whose only walled pull is gone. The data then decide whether L2(2.5) moves toward 0 or past it, where the τ = 8 wall takes over.
- Expected: the shift is small. A 3.2e-3 loss change is far below 1σ, and the other four conditions have ≥ 0.029 of slack.
- The CS side does not interact with the margin at this point: λ2_ν = 0.063 is well inside its wall, and λ4_ν is held.

**(d) The trace-time trap, demonstrated on the real fitter.**
- After the fitter's regulariser list was swapped to the margin-0 wall and τ set to 8, `f.reduced_nll()` returned 377.98597734612 = base + e¹⁶·pen₅ exactly.
- So the traced loss still carries the **default-margin** wall, while τ (a `tf.Variable`) is read at run time.
- A margin change is therefore only valid at fitter construction, i.e. on the `-r` line. That matches `knowledge/20_frameworks/rabbit_minimizer_tolerances.md`.

### The `-r` syntax for T2 (`scripts/check_r_syntax.py`, output `check_r_syntax.out`)

rabbit parses `-r` as `nargs="+", action="append"`:
- `margs[0]` is the regulariser class.
- `margs[1]` is the mapping class.
- `margs[2:]` go to `NPDampingMapping.parse_args`.

So `margin=0` must come after the mapping class:

```
--regularizationStrength 8 \
-r wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingWall \
   wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingMapping margin=0
```

Other orderings, checked against rabbit's own `make_parser()`:

| line | parsed as | outcome |
|---|---|---|
| `-r …NPDampingWall …NPDampingMapping margin=0` | mapping args `['margin=0']` | correct |
| `-r …NPDampingWall margin=0 …NPDampingMapping` (the example order in the task) | mapping class `'margin=0'` | loud `ValueError: Class margin=0 not found` |
| `fitterAD.sh --wall -f "margin=0 …"` | `margin=0` lands in `--paramModel`'s token list | loud `TypeError` (unknown spec token) from `SCETlibADParamModel`; the wall stays at 5e-3 and τ at 5 |
| `fitterAD.sh` **without** `--wall`, with `-f "<paramModel tokens> … --regularizationStrength 8 -r W M margin=0"` | correct | correct |

Two more things to watch:
- rabbit's default `--regularizationStrength` is **0.0**, meaning a weight of e⁰ = 1 and not a stiff wall. Always state τ explicitly.
- Confirm the fit log shows `[NPDampingWall] armed on … at margin=0`. The mapping key also gains ` margin=0`, but only when the keyword is given; default keys are unchanged.

### The diff (uncommitted, `WRemnants` branch `scetlib-ad-param-model`, only `np_damping_wall.py` touched)

Lint: the container's `black` (26.5.1), `isort --profile black --line-length 88` and `flake8 --select=F4,F6,F7,F8,F901` all pass. black reformatted one line of the edit (the `self.margin = _parse_margin(...)` call). No test file exists for this module in WRemnants, so none was added. The unit check lives in this task dir. Saved copy: `np_damping_wall_margin.diff`.

```diff
diff --git a/wremnants/postprocessing/scetlib_ad/np_damping_wall.py b/wremnants/postprocessing/scetlib_ad/np_damping_wall.py
index c36e52c7..c02f22f4 100644
--- a/wremnants/postprocessing/scetlib_ad/np_damping_wall.py
+++ b/wremnants/postprocessing/scetlib_ad/np_damping_wall.py
@@ -151,13 +151,22 @@ asymptote. ``smallb=0`` drops them, leaving only the limiting/interior
 behaviour and the lambda_inf floors -- then use the postfit sigma(qT) >= 0
 check as the real guard.
 
+``margin=<float>`` sets the cushion every margin-carrying condition is enforced
+at (``coeff >= margin`` instead of ``coeff >= 0``; see ``NP_DAMPING_MARGIN``).
+The default is ``NP_DAMPING_MARGIN`` = 5e-3, so a -r line without it is
+unchanged. ``margin=0`` walls the EXACT damping boundary; pair it with a stiff
+``--regularizationStrength``, since a soft relu^2 wall at margin 0 settles
+slightly past the boundary. The lambda_inf floors and the tanh_6 interior
+discriminants do not carry the margin, and the held-lambda drop check always
+uses the bare condition, whatever the margin.
+
 Invoke (nothing on the -r line repeats the model spec):
 
     rabbit_fit.py ... \\
       --regularizationStrength 5 \\
       -r wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingWall \\
          wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingMapping \\
-         [smallb=0] [ymax=<float>]
+         [smallb=0] [ymax=<float>] [margin=<float>]
 
 References:
   AN-25-085 theory.tex Eqs. eq:npgamma, eq:npf
@@ -216,18 +225,37 @@ ABSY_AXIS_NAMES = ("absYVGen", "absYVgenSig", "yVGen")
 # the TMD conditions below are incomplete. Values we accept as "not on".
 _NP_MODEL_TMD_OFF = ("off", "none", "")
 
-# Fixed knobs. Only smallb and ymax are exposed on the -r line; these two are
-# constants to keep that line minimal, and they are the values the old wall
-# ran with.
+# Knobs. smallb, ymax and margin are exposed on the -r line; the lambda_inf
+# floor is a fixed constant to keep that line minimal. Both defaults are the
+# values the old wall ran with.
 LAMBDA_INF_FLOOR = 1e-3  # positive floor on the lambda_inf saturation scales
-NP_DAMPING_MARGIN = 5e-3  # positive cushion: enforce each damping coeff >= this
+NP_DAMPING_MARGIN = 5e-3  # DEFAULT cushion: enforce each damping coeff >= this
 #              rather than >= 0, so the soft wall's equilibrium -- which sits a
 #              hair PAST the knee, where the penalty gradient vanishes -- still
 #              lands in the damping region. NB this cache's correction anchors
 #              lambda4_nu at exactly 0, i.e. ON the boundary, so at theta = 0
 #              the wall already contributes margin^2 = 2.5e-5 (times exp(2 tau))
 #              and biases lambda4_nu up by >= 5e-3 physical = 0.01 theta, one
-#              percent of its prior width. Set to 0 to switch the cushion off.
+#              percent of its prior width. Override per fit with margin=<float>
+#              on the -r line (NPDampingMapping); margin=0 switches the cushion
+#              off and walls the exact boundary. Must be finite and >= 0.
+
+
+def _parse_margin(value):
+    """A validated damping margin: a finite float >= 0, or raise."""
+    try:
+        margin = float(value)
+    except (TypeError, ValueError):
+        raise ValueError(
+            f"np_damping_wall: margin must be a number, got {value!r}"
+        ) from None
+    if not np.isfinite(margin) or margin < 0.0:
+        raise ValueError(
+            f"np_damping_wall: margin must be finite and >= 0, got {value!r}. "
+            "A negative margin would wall a region PAST the damping boundary, "
+            "i.e. admit anti-damping lambdas as 'physical'."
+        )
+    return margin
 
 
 def resolve_form(form, side):
@@ -453,7 +481,9 @@ def damping_conditions(
     ``ymax`` is the binding |Y| (:func:`_binding_absY`). The TMD conditions are
     emitted twice, at Y = 0 and Y = ymax, because L2 is monotonic in Y^2 and so
     the binding rapidity is one extreme or the other depending on the sign of
-    delta_lambda2 -- which the fit is free to flip.
+    delta_lambda2 -- which the fit is free to flip. ``margin`` is the bound of
+    every condition except the lambda_inf floors (``floor``) and the tanh_6
+    interior discriminants (always 0); callers validate it (``_parse_margin``).
     """
     conds = []
 
@@ -641,26 +671,35 @@ def _make_mapping_class():
                            is the range the model evaluates sigma_gen over. Only
                            override for a deliberate study, and record why -- the
                            delta_lambda2 wall scales as 1/ymax^2.
+            margin=<float> the cushion each margin-carrying condition is
+                           enforced at, coeff >= margin (default
+                           NP_DAMPING_MARGIN = 5e-3). Finite and >= 0;
+                           ``margin=0`` walls the exact damping boundary. The
+                           lambda_inf floors, the tanh_6 interior discriminants
+                           and the held-lambda drop check never use it.
 
         The NP forms and the lambda anchors are derived from the card's recorded
         theory correction (see the module docstring); nothing on the -r line
         repeats the ``--paramModel`` spec.
         """
 
-        def __init__(self, indata, key, smallb=True, ymax=None):
+        def __init__(
+            self, indata, key, smallb=True, ymax=None, margin=NP_DAMPING_MARGIN
+        ):
             super().__init__(indata, key)
             self.indata = indata
             self.smallb = bool(smallb)
             self.ymax = None if ymax is None else float(ymax)
+            self.margin = _parse_margin(margin)
 
         @classmethod
         def parse_args(cls, indata, *args):
-            smallb, ymax = True, None
+            smallb, ymax, margin = True, None, None
             for a in args:
                 if "=" not in a:
                     raise ValueError(
-                        f"NPDampingMapping: args are 'smallb=<0|1>' and "
-                        f"'ymax=<float>', got '{a}'"
+                        f"NPDampingMapping: args are 'smallb=<0|1>', "
+                        f"'ymax=<float>' and 'margin=<float>', got '{a}'"
                     )
                 k, v = a.split("=", 1)
                 k = k.strip()
@@ -668,16 +707,26 @@ def _make_mapping_class():
                     smallb = v.strip().lower() not in ("0", "false", "no", "off")
                 elif k == "ymax":
                     ymax = float(v)
+                elif k == "margin":
+                    margin = _parse_margin(v)
                 else:
                     raise ValueError(
-                        f"NPDampingMapping: unknown key '{k}'; only 'smallb' and "
-                        "'ymax' are supported (the lambda_inf floor and the "
-                        "damping margin are fixed module constants)."
+                        f"NPDampingMapping: unknown key '{k}'; only 'smallb', "
+                        "'ymax' and 'margin' are supported (the lambda_inf floor "
+                        "is a fixed module constant)."
                     )
-            key = f"{cls.__name__} smallb={int(smallb)}" + (
-                f" ymax={ymax:g}" if ymax is not None else ""
+            key = (
+                f"{cls.__name__} smallb={int(smallb)}"
+                + (f" ymax={ymax:g}" if ymax is not None else "")
+                + (f" margin={margin:g}" if margin is not None else "")
+            )
+            return cls(
+                indata,
+                key,
+                smallb=smallb,
+                ymax=ymax,
+                margin=NP_DAMPING_MARGIN if margin is None else margin,
             )
-            return cls(indata, key, smallb=smallb, ymax=ymax)
 
     return NPDampingMapping
 
@@ -697,7 +746,7 @@ def _make_regularizer_class():
             self.mapping = mapping
             self.indata = mapping.indata
             self.enforce_small_b = bool(getattr(mapping, "smallb", True))
-            self.margin = NP_DAMPING_MARGIN
+            self.margin = _parse_margin(getattr(mapping, "margin", NP_DAMPING_MARGIN))
             self.floor = LAMBDA_INF_FLOOR
 
             self.inputs = resolve_wall_inputs(
@@ -817,7 +866,8 @@ def _make_regularizer_class():
                 dropped.append((cond.label, val))
             print(
                 f"[NPDampingWall] armed on {len(self._active)} of "
-                f"{len(self.conditions)} condition(s); fitted lambdas "
+                f"{len(self.conditions)} condition(s) at margin="
+                f"{self.margin:g}; fitted lambdas "
                 f"{sorted(self._idx)}, held at the correction's anchor "
                 f"{self._held}."
                 + (
```

---

## Log

### 2026-09-30
- Snapshotted the pre-change HEAD blob to `scripts/np_damping_wall_orig.py` (md5 72ba6a3c…), edited `np_damping_wall.py`, and ran the container lint. It passes.
- Step 1 unit check: 0 failures across 8 form/smallb combinations × 207 λ points, plus the mapping parse and refusal cases (evidence: `unit_check_margin.out`).
- Step 2: gated load (`scripts/mem_gate.sh 330`, slot released after 60 s, cache load 35 s, 157 s including model build). Gate (a) diff 0.0; (b) residual 1.0e-14; (c) and (d) as above (evidence: `margin_loss_gate.json`, `logs/margin_loss_gate.log`).
- `-r` parsing checked against rabbit's parser; found the `fitterAD.sh --wall` pitfall (evidence: `check_r_syntax.out`).

---

## Findings

1. `margin=<float>` on `NPDampingMapping` works. The default path is bit-identical to HEAD (exact equality on bounds and penalties; stored NLL reproduced with diff 0.0) — (evidence: `unit_check_margin.out`, `margin_loss_gate.json`).
2. At the nominal walled minimum, the only active wall is TMD L2(|Y|=2.5) ≥ 5e-3. Its coefficient is 4.62e-3, so it is inside true damping but past the cushion, and it contributes 3.21e-3 to the loss. Under margin 0 nothing is active at this x — (evidence: `margin_loss_gate.json`).
3. The margin can only be changed at fitter construction. Swapping regularisers on a traced fitter keeps the old wall, while τ updates live — (evidence: (d) above).
4. `fitterAD.sh --wall` cannot carry `margin=`, because `-f` tokens land in `--paramModel` and fail loudly. For T2, pass the whole wall via `-f` without `--wall` — (evidence: `check_r_syntax.out`).

---

## Open questions

- `margin=-0` parses to −0.0. The penalty is identical, but the mapping key shows `margin=-0`. This is cosmetic and was left alone.
- Outside scope, not chased: at this nominal lattice fit λ2_ν = 0.0634 physical, against the lattice term 0.1345 ± 0.031, a pull of about −2.3σ. The orchestrator may want to confirm that this is the known CMS-vs-lattice tension, and not a mismatch in the lattice term's centre or width in the card.
- `fitterAD.sh` could grow a `--wall-args` or `--tau` option so T2-style fits do not have to hand-assemble `-f`. That lives in WRemnantsHelpers/workflows and is not part of this task.
