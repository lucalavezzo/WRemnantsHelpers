---
title: The theory correction as the anchor
slug: 260910-corr-anchor
study: scetlib-ad-param-model
status: done
created: 2026-09-10
updated: 2026-09-10
owner: orchestrator
---

# The theory correction as the anchor

**Task:** can the param model be made to take its parameter central values from
the theory correction the card's templates were built with, and refuse a card
that does not record them?

---

## START HERE (status as of 2026-09-10)

> **Yes. Implemented, and all 9 in-model cases behave as designed.**
> The anchor rebuilt from the correction's runcard is **bit-identical** on all 53
> registered parameters to the cache's own anchor, and `sigma_gen` at theta = 0
> is unchanged at **670.0283701** — so on the present pair this is bookkeeping,
> not a change of physics. The cache-vs-correction comparison finds **0
> refusing, 0 warning, 0 correction-only keys uncompared**.

- **Next action:** none — task closed. (Commits pending in the parent study.)
- **Blocking on:** nothing.

---

## Why

The model returns `rnorm = sigma_gen(p) / sigma_gen(p_anchor)` and rabbit
MULTIPLIES the card's templates by it. Those templates were reweighted by a
theory correction, so `rnorm = 1` at the fit start only if `p_anchor` is the
point *that correction* was computed at. Before this, `param_model` set
`self._anchor = self.core.anchor` — read from the **cache**, a different SCETlib
artefact — and the correction's values were only a warning-level check over ~16
NP lambdas which went inert whenever a card recorded nothing.

A wrong anchor is invisible: the ratio is 1 at the start either way, so every
prefit plot looks perfect and only the derivatives are wrong, perturbing around
the wrong origin. Same shape as the alphaS blinding bug found 2026-09-09
(SCETlib evaluated at alphaS = 1.7e-05, starting loss 4.6e7 against a converged
361, no check fired).

---

## Log

### 2026-09-10 — the survey, and one correction to it

Compared the cache runcard (A) against the correction's recorded resummed
runcard (B). Every physics-point key agrees byte for byte, so today's pair is
consistent and this work makes that *checked* rather than fixing a mismatch.

The plan's survey compared A as the bare `cache.conf` file and found **33
correction-only keys** that could not be compared at all — including exactly the
ones a build-default difference would hide (`lambda6`, `lambda6_nu`,
`lambda4_i`, `np_model_tmd`, the eleven per-flavour `lambda2_*`, `kappafo`,
`transition_type`, `scale_setting`). That understates what is checkable: the
cache's calculation is configured from `core.conf`, i.e. the runcard **layered
on SCETlib's `defaults.conf`**. Against the layered config **all 107 of the
correction's keys have a counterpart, and 0 are left uncompared** — the blind
spot closes. Residual asymmetry: those are *today's* defaults while the
correction side is the config SCETlib resolved when it ran, so a `defaults.conf`
edit since then reads as a real difference (which, for the cache, it is).

### 2026-09-10 — the key asymmetry, and where it lands

Layering `defaults.conf` under the cache runcard makes the *correction-only*
count 0, but the comparison iterates the CORRECTION's keys, so keys the cache
carries and the correction does not are never visited at all. That asymmetry is
real: a cache-only key can represent a physics difference no value-comparison
can see.

Measured, and the answer is reassuring — there are **12** such keys and **every
one** belongs to the fixed-order / matching machinery:

```
Calculation_settings.fo_order2_{analytic,analytic_xrule,analytic_zrule,
    adaptive,direct,guard_tol,kfactors,qtriang,rule_cap,target_abs,target_rel}
Calculation_settings.matched_nons_qt_cut
```

`fo_order2_analytic` is `yes` in the cache runcard, `no` in today's
`defaults.conf`, and **absent entirely** from the correction's resolved config —
i.e. the SCETlib build that made the correction predates the knob. So this is a
real cache-vs-correction difference in the fixed-order treatment.

It is also exactly the boundary already declared out of scope, and not a
scattering of accidental gaps: `calculation_piece` is `matched` (cache) against
`sing` (correction) BY CONSTRUCTION — the correction runs resummed-only and
takes its nonsingular from DYTurbo, while the cache computes the matched total
in one go — so every one of those 12 knobs exists precisely because of that
difference. "The correction is the authority" was already stated to hold for the
**resummed sector only**; this measurement is what makes that statement exact
rather than a hedge.

So the accurate claim is: **0 correction-only keys uncompared; 12 cache-only
keys never visited, all fixed-order/matching, all inside the declared FO
exclusion.**

### 2026-09-10 — the registry, measured rather than assumed

Printed `names` / `anchor` straight from the cache `.npz`: **53** entries =
1 `alphas` + 8 NP + 10 TNP + 5 profile/transition + 29 `pdf_eig`. Two things the
docstring-derived breakdown had wrong: this (tanh_2) cache registers **no**
`np_eff_lambda6` / `np_gnu_lambda6`, and `scale_kappa_F` sits at index 23,
*after* `scale_x3`. `params.uncovered_params()` returns `()` — every registered
name has a stated source.

### 2026-09-10 — harness, done wrong then right

Four failed launches, every cause already written down in
`knowledge/10_environment/runtime_bootstrap.md`, which I had not read: `/cvmfs/`
missing from the bind list (LHAPDF dies with `Info file not found for PDF set
'CT18ZNNLO'`, which reads as a missing set rather than a missing bind);
`--cleanenv` and a bare `#!/bin/bash` entrypoint both drop `LHAPDF_DATA_PATH`,
so it must be `bash -lc`; `set -u` in the wrapper makes `source setup.sh` exit
the shell silently (two empty logs); and two runs sharing one log file
interleaved, which made me misread one test's error. Wrapper now lives in
`scripts/` here, per the note.

---

## Result

The theory correction now defines the parameter central values, and a card that
does not record them is refused rather than silently anchored on the cache.

**Comparability, before the numbers.** All of this is on ONE cache/correction
pair (`pdf62_corrgrid_260827/merged_full` against
`scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_CorrZ`)
which the survey shows already AGREED on every declared key — so the passing
cases demonstrate the machinery, they do not discover a mismatch. The mismatch
cases are injected by hand into copies of the card. SCETlib is the frozen
validated snapshot b66f8de; rabbit is 9315f24 on `main-plus-ours`. No fit was
run: every case is a model CONSTRUCTION, which is where the anchor is resolved.

| # | case | expected | result |
|---|---|---|---|
| 1 | card records no config | refuse | PASS |
| 2 | same, `anchor_source=cache` | warn, proceed | PASS — sigma_gen 670.0283701, Δanchor 0 |
| 3 | config present | pass | PASS — 22 from runcard + 31 structural = 53; 0/0/0 |
| 4 | `pdf_set` swapped to NNPDF31 | refuse | PASS — caught in `QCD` |
| 5 | `lambda2` 0.4 -> 0.45 | warn, proceed | PASS — anchor FOLLOWS the correction; sigma_gen moves to 670.0230177 |
| 6 | `lambda2` key deleted | refuse | PASS — no `defaults.conf` fallback |
| 7 | same + `anchor_override=lambda2=0.4` | pass | PASS — 21 + 31 + 1 = 53; sigma_gen back to 670.0283701 |
| 8 | `applied_to_nominal = False` | refuse | PASS |
| 9 | retired `check_anchor=0` token | raise | PASS — lists the valid tokens |

(evidence: `logs/anchor_checks_260910_105804.log`)

**The physics read.** Case 5 is what shows this is not a decorative check. With
the correction's `lambda2` moved off the cache's, the anchor follows the
CORRECTION and `sigma_gen` genuinely changes: 670.0230177 against 670.0283701,
i.e. **-8.0e-6 relative for a +12.5 % shift in lambda2**. Small, and expected to
be: lambda2 is the quadratic coefficient of the b_T-space NP form factor, so it
reshapes the low-qT region while leaving the qT-integrated total nearly
invariant — consistent with `knowledge/30_physics_global/np_parametrization_constraints.md`
treating it as a shape rather than a normalisation parameter. The fit sees that
SHAPE, not this total, so a small change here is not a small change to the
likelihood. What matters for this task is only that it is NONZERO: the recorded
correction really does set the ratio's denominator.

Case 2 against case 3 is the safety argument in one line: both give a perfectly
healthy prefit — identical `sigma_gen`, ratio exactly 1 at the start — and only
one of them knows why. That is precisely the invisibility the alphaS blinding
bug exploited.

---

## Findings

1. The correction-derived anchor is **bit-identical** to the cache anchor on all
   53 parameters for the current pair, so `sigma_gen` at theta = 0 is unchanged —
   (evidence: `scripts/check_anchor.py`, and the standalone arithmetic check in
   the session log).
2. Comparing against `core.conf` (runcard layered on `defaults.conf`) rather
   than the bare runcard file takes the uncompared-key count from 33 to 0.
3. `scale_kappa_R` / `scale_kappa_F` are registered by
   `scetlib-cms/src/qT/ad/ad_context.cpp` with a **hardcoded** central of 1 —
   they are multiplicative factors on top of the runcard's `kappafo` / `kappaf`.
   So those two runcard keys ARE the central value of two registry parameters,
   and a difference there would move an anchor without moving any number a
   value-comparison would see. Added to the REFUSE list (beyond the plan's
   declared list, deliberately).
4. `lambda6_nu` can be recoverable from neither artefact: an older `tanh_6`
   build hardcoded the CS-side value at 0.0007 with no runtime key, while this
   checkout defaults it to 0. Hence **no `defaults.conf` fallback for an
   anchor-bearing value** — a missing one refuses, with `anchor_override=` as the
   one auditable escape.

---

## Open questions

- Verification 5 (an Asimov fit) was DROPPED, not skipped (Luca: *"why do we
  need to run the asimov"*). It had nothing to add: the anchor is
  bit-identical, and the normalisation is an exact linear reparametrisation
  whose only free numbers — the widths — each equal the old `PRIOR_SIGMAS`
  value exactly, so the physical prior is unchanged. An Asimov fit also never
  runs the minimiser (`ifit = -1`), so it cannot probe the one thing that IS
  unmeasured. See `scripts/launch_asimov.sh`, kept as the toy-arm recipe.
- **Unmeasured:** whether collapsing the curvature spread actually helps the
  minimiser. Needs a toy or data arm.
- The fixed-order half of a `scetlib_dyturbo` correction carries no runcard,
  and the 12 cache-only `fo_order2_*` keys above sit inside that gap, so "the
  correction is the authority" holds for the resummed sector only.
