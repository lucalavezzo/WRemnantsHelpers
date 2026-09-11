---
title: NP damping wall ported to scetlib_ad
slug: 260910-wall-port
study: scetlib-ad-param-model
status: done          # active | done | paused | abandoned
created: 2026-09-10
updated: 2026-09-10
owner: study-worker
---

# NP damping wall ported to scetlib_ad

**Task:** Can the NP damping wall be ported to the new `scetlib_ad` param model, where the
fitted lambdas are *unit nuisances* rather than physical lambdas — and does a walled
blinded data fit keep the NP lambdas in the physical (damping) region, at what cost in
loss / EDM / saturated p-value?

---

## START HERE (status as of 2026-09-10)

> **Ported, verified, and fitted. The wall works and it is worth having — but the tension
> is real, not a masked pathology.**
> The walled data fit fixes the serious violation (`lambda2_nu` −0.058 → **+0.0049**, so
> the CS kernel no longer anti-damps at small `b_T`) and the marginal TMD one
> (−0.0047 → **+0.372**), leaving 7 of 8 conditions satisfied. It costs
> **Δ(pure NLL) = +5.78, i.e. Δχ² = +11.6**, and the saturated p-value falls
> **2.33% → 1.07%**. It *improves* convergence by a lot: **EDM 1.39e-03 → 9.63e-07**
> (1439×) in 138 iterations instead of 221. `sigma(alpha_s)` tightens 0.001321 → 0.001097.
> One condition still fails, `lambda4_nu = −4.3e-4`, and the reason is measured, not
> mysterious: that direction carries ~5e7 of curvature, four orders of magnitude more than
> the wall's own 1.1e4.

- **Next action:** none — task closed. If the orchestrator wants the last violation closed,
  see *Open questions* (it needs a stronger tau or a hard reparametrisation, not a bug fix).
- **Blocking on:** nothing.

---

## Log

### 2026-09-10 — the port

Source: `PR710/WRemnants/wremnants/postprocessing/scetlib_np/np_damping_wall.py`
(added in `d1a26d24`). New file:
**`WRemnants/wremnants/postprocessing/scetlib_ad/np_damping_wall.py`** (untracked, **not
committed**). Same rabbit `Regularizer` mechanism and same relu² hinge walls. Four things
had to change — the brief named two, and the other two would have quietly changed the
answer.

**(1) theta → physical.** `8f6af64f` made every fitted parameter a unit nuisance,
`physical = anchor + width·theta`, and rabbit hands a `Regularizer` `get_x()`, i.e. theta.
The wall now maps theta→physical itself, taking the **width** from `params.REPARAM` and
the **anchor** from the card's recorded theory-correction runcard via
`params.corr_anchor_value` — the same authority the model's default
`anchor_source="correction"` uses. Nothing hardcoded. For this card:
`lambda2 = 0.4 + 0.5θ`, `lambda4 = 0.4 + 0.5θ`, `delta_lambda2 = 0 + 0.5θ`,
`lambda2_nu = 0.15 + 0.1θ`, `lambda4_nu = 0 + 0.5θ`.

*A subtlety that caught the first version of the **test**, not the code:* `lambda_inf` and
`lambda_inf_nu` have **no** `REPARAM` entry, so their fit coordinate **is** the physical
lambda and the fit *starts at the anchor*, not at 0 — exactly what
`param_model._register_params` does (`defaults[~self._rp_id] = 0.0` zeroes only the
reparametrised entries). Both are in `params.DEFAULT_FROZEN`, so the wall reads them as
held constants (1.0, 2.0) and reports them as such.

**(2) The forms.** There is no `indata.scetlib_np_param_model` here — the AD model does not
publish itself — so the wall reads `Nonperturbative.np_model` / `np_model_nu` off the same
recorded correction config (`response.corr_config_from_meta`). That is a safe authority:
`params.CORR_REFUSE_KEYS` already refuses a cache whose NP form differs from the
correction's. Both are `tanh_2`. Unknown forms still **raise** rather than guess, as in the
original, and so does `np_model_tmd` being on (a second, flavour-dependent NP factor these
walls do not cover).

**(3) The binding |Y| is now DERIVED, not a module constant.** The original left
`Y_MAX = 5.0` "UNDER TEST". That is not a detail: `L2 = lambda2 + delta_lambda2·Y²`, so the
`delta_lambda2` wall scales as `1/Y_max²` and 5.0 constrains it **four times** harder than
the 2.5 the analysis uses. The wall now takes it from the card's own gen rapidity axis
(`auxiliary[scetlib_np].edges__absYVGen` → **2.5**), which is the range the model evaluates
`sigma_gen` over — the cache's `Grid_Y` *is* the card's gen binning, per the header
`prepare_cache_for_card.py` writes into `cache.conf`. It agrees with
`knowledge/30_physics_global/np_parametrization_constraints.md` ("take y_max = 2.5").
Measured at the DATABLIND tune: bare penalty 0.0041 at ymax=2.5 versus **0.1038** at
ymax=5, with `d(penalty)/dθ(delta_lambda2)` going −0.004 → **−8.1**. An `ymax=` override
exists for a deliberate study.

**(4) Uniform conditions, resolved by name.** Every condition is now `coeff >= bound` with
penalty `relu2(bound − coeff)`, the interior discriminants included (their coeff
`4·l2nu·l6nu − relu2(−l4nu)` is self-gating and division-free). Algebraically identical to
the original; the gain is that one definition (`damping_conditions()`) serves the TF
penalty, the construction-time check on held lambdas, and the offline diagnostics.
Positions come **by name** from the fitter's `parms`, so a `poi_params` reorder and the
saturated path's `CompositeParamModel` are tracked automatically — the original had to
refuse a composite because it indexed `x[:nparams]` flat.

A condition that reads **only held lambdas** is a constant. Adding it to the loss would
offset the free-vs-walled Δloss that is the whole point, so it is checked once against the
**bare** condition (no margin, so freezing `lambda4_nu = 0` exactly — a legitimate physical
choice, cf. the `physical-lambda` study — is allowed) and then dropped, with a log line.
In this fit that drops the two `lambda_inf` floors: 6 of 8 conditions are armed.

Conditions re-derived against the SCETlib source the fit **links**
(`/work/submit/lavezzo/alphaS/scetlib-audit-b66f8de/include/scetlib/qT/`), not the AN's
normalised form:

- `gamma_nu_np_model`, tanh_2: `arg = (l2nu + l4nu·b²)·b²/linf_nu`, called with the **raw**
  `bT` (`Gamma_nu.cpp:117`; `bStar` feeds only the perturbative logarithm at line 102).
  ⇒ `linf_nu > 0`, `l2nu ≥ 0`, `l4nu ≥ 0`, and "for all b ≥ 0" is exact, not conservative.
- `np_effective`, tanh_2: `arg = (L2 + lambda4·b²)·b/linf + (L2·b/linf)³/3`. **The
  arctanh-correction cube term is present for tanh_2, not only tanh_6**, with **three**
  powers of `linf`. ⇒ `linf > 0`, `L2 ≥ 0`, `3·linf²·lambda4 + L2³ ≥ 0` at `Y = 0` and
  `Y = 2.5`. With `b0_over_bmax_global = 0` in `cache.conf`, b* is the identity here too.

Module constants kept as ported: `LAMBDA_INF_FLOOR = 1e-3`, `NP_DAMPING_MARGIN = 5e-3`.
Linted with the container's isort/black/flake8 (`scripts/lint.sh`).

### 2026-09-10 — verification BEFORE fitting

`scripts/verify_map.py` (evidence: `logs/verify_map_260910_164739.log`):

1. **theta = 0 → the correction's anchor**, exactly (≤1e-12) for all five reparametrised
   lambdas, and the two identity ones start at the anchor in their own coordinate. This is
   the model's *own* invariant — `_register_params` raises if its maps fail it — so a wall
   satisfying it with the same `REPARAM` widths is on the same coordinate as the model.
2. **DATABLIND postfit thetas → the quoted physical lambdas**, all five to <5.1e-4.
3. **The conditions at that point** — see Result.

`scripts/unit_wall.py` (evidence: `logs/unit_wall_260910_165020.log`) drives the wall
through rabbit's own loaders (`load_mapping` → `load_regularizer` →
`set_expectations(parms=…)` → `compute_nll_penalty`) on a synthesised x in the DATABLIND
layout, with no param model and so no 8.7 GB cache load. TF penalty == numpy penalty to
1e-14 relative in all four cases (anchor, postfit, `smallb=0`, `ymax=5`); the gradient is
finite, nonzero **only** on walled directions, and **exactly zero on the alphaS POI slot**
— the wall never touches the blinded coordinate. Eight refusals all fire with the intended
message: unsupported CS form, unsupported TMD form, `np_model_tmd` on, no gen |Y| axis, no
correction config, a held lambda violating its own condition, an unknown `-r` option, and
`parms` not passed.

### 2026-09-10 — the walled fit

`scripts/launch_wall_fit.sh` → `logs/fit_DATAWALL5_260910_165137.log`, fitresult
`/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260910_wall_port/fitresults_DATAWALL5.hdf5`.
Identical to the unwalled DATABLIND arm — same card `card_none.hdf5`, same cache
`pdf62_corrgrid_260827/merged_full`, SCETlib b66f8de
(`libscet-qT.so` md5 `71b5e68a…`), rabbit `rabbit-blinding` @ 0f64bbb (additive-blinding
assertion passed), `-t 0 --earlyStopping 100 -v 4 --jitCompile off --noBinByBinStat` —
plus `--regularizationStrength 5` and `-r …NPDampingWall …NPDampingMapping`, minus
`--doImpacts`. 1509 s of minimisation, 22 min wall clock.

tau = 5 (`exp(2tau) = 22026`) was chosen so the wall is a **barrier**: with the 5e-3 margin
the predicted equilibrium was `lambda2_nu ≈ +0.0048` and the `|Y|=2.5` cubic `≈ +0.0045`,
where tau = 3 (the old wall's value) would have left `lambda2_nu ≈ −3e-4`, i.e. a failed
test. The fit landed at `lambda2_nu = +0.004872` — the prediction was right to 1.5%.

The wall's own log lines confirm the resolution end-to-end: forms `tanh_2`/`tanh_2` from the
correction, `Binding |Y| = 2.5 from {'auxiliary[scetlib_np].absYVGen': 2.5}`, armed on 6 of
8 conditions, held `{'lambda_inf': 1.0, 'lambda_inf_nu': 2.0}`.

---

## Result

**Comparability caveats, first.** Blinded real data (`-t 0`), alphaS blinded **additively**;
no alphaS central value appears here or in any log in this directory. Same blinding family,
card, cache, SCETlib build and rabbit as the unwalled DATABLIND reference, so loss / EDM /
p-values are directly comparable. `--doImpacts` was dropped (nothing compared here uses it).
The walled `fun` **includes** the penalty, so every Δloss below has it removed. Both fits
stop at scipy `status: 2` ("a bad approximation caused failure to predict improvement"), so
both covariances are Hessians at a stopping point — but the walled one is 1439× better
converged, so its errors are the more trustworthy of the two. `lambda2_nu` is **railed at
the wall**, so its value is set by the 5e-3 margin and its σ is the wall's width, not a
measurement.

### Did the wall keep the lambdas physical? Almost — 7 of 8.

| physical lambda | anchor | unwalled | walled (tau=5) |
|---|---|---|---|
| `lambda2` | 0.4 | 0.300643 | **0.108109** |
| `lambda4` | 0.4 | −0.002666 | **+0.124033** |
| `delta_lambda2` | 0 | −0.024343 | −0.013023 |
| `lambda2_nu` | 0.15 | **−0.058284** | **+0.004872** (at the wall) |
| `lambda4_nu` | 0 | +0.053686 | **−0.000427** |
| `lambda_inf`, `lambda_inf_nu` | 1, 2 | held | held |

Damping conditions (`ymax=2.5`, `smallb=1`): **2 of 8 violated unwalled → 1 of 8 walled**.

| condition | unwalled | walled |
|---|---|---|
| `lambda2_nu ≥ 0` (CS small-b turn-on) | **−0.0583** | **+0.00487** |
| `3·linf²·lambda4 + L2³ ≥ 0` at |Y|=2.5 | **−0.00472** | **+0.372** |
| `lambda4_nu ≥ 0` (CS large-b leading) | +0.0537 | **−0.000427** |
| the other five | all ok | all ok |

### Physics read

**What was wrong before.** The unwalled minimum had `lambda2_nu = −0.058` with
`lambda4_nu = +0.054`, so `P(u) = l2nu·u + l4nu·u²` is negative for `b_T < 1.04 GeV⁻¹`:
over that whole range the tanh argument is negative and `gamma_nu^NP` is **positive**, up to
+0.016. The CS kernel *anti-damps* exactly where the TMD form factor is still O(1), which is
the sign-preservation requirement R1/R3(a) of
`knowledge/30_physics_global/np_parametrization_constraints.md` failing — the `lambda2 ≥ 0`
condition AN-25-085 states in the commented-out asymptotic block after Eq. (eq:npgamma).
That is the violation that matters, and the wall removes it (see
`np_form_factors.png`, top-right panel: the red bump is gone).

**`lambda4 < 0` was never the problem.** For `tanh_2` the TMD condition is
`3·linf²·lambda4 + L2(y)³ ≥ 0`, because `np_effective` carries the `L2³` arctanh
correction. At the unwalled tune that coefficient is **+0.019** at `Y = 0` and only turns
negative past `|Y| ≈ 2.05`, reaching −0.0047 at the 2.5 edge (`tmd_damping_vs_Y.png`). So
the pre-existing framing "lambda4 is negative, hence unphysical" is **wrong for this form**;
the honest statement is that `f^NP` was marginally anti-damping at large `b_T` in the
outermost rapidity bin only.

**What the wall costs, and what it buys.** Forced to be physical the fit moves a long way in
the NP block — `lambda2` halves, `lambda4` goes from ~0 to +0.124 — and the CS NP kernel is
driven **nearly off**: `gamma_nu^NP(3 GeV⁻¹)` goes from −1.9 (unwalled) to −0.01 (walled),
against −1.15 at the lattice anchor. So when the data may not have a wrong-sign CS kernel,
they prefer *no* CS kernel to the lattice tune. That is a physics statement worth the
orchestrator's attention: the CS-side lattice constraint
(`lambda2_nu = 0.15`) and this data are pulling in opposite directions, and `lambda2_nu`
railing at the wall is that pull hitting a hard stop.

**The residual violation is understood, not a bug.** `lambda4_nu = −4.3e-4` still fails
`≥ 0`, but it moves the anti-damping from `b_T < 1.04` to `b_T > 3.38 GeV⁻¹`, where the
walled `f^NP` has already suppressed the integrand by ~10⁻³ — a far less consequential
failure. It survives because the postfit `sigma(theta_lambda4_nu) = 1.42e-4`, i.e. ~5e7 of
curvature in that direction, against the wall's own `2·exp(2tau)·(dλ/dθ)² = 1.1e4`. The
wall is four orders of magnitude too weak *there*; no reasonable tau closes that gap, and
raising tau to try would wreck the conditioning. That stiff direction is not created by the
wall — the NP-block covariance has a near-null eigenvalue in **both** fits (1.35e-09
unwalled, 1.13e-08 walled) — it just happens to align with `lambda4_nu` at this minimum,
where unwalled it aligned with `lambda4`.

### Is the free-vs-walled Δ(loss) small or large? **Large — this is real tension.**

| | unwalled | walled (tau=5) |
|---|---|---|
| loss (`fun`) | 405.560874 | 411.991213 |
| wall penalty inside it | — | 0.6490 |
| **Δ(pure NLL)** | — | **+5.7813 → Δχ² = +11.563** |
| EDM | 1.3864e-03 | **9.6324e-07** (1439× better) |
| iterations / minimise | 221 / 2645 s | **138 / 1509 s** |
| saturated | 811.12/733, **p = 2.33%** | 823.98/733, **p = 1.07%** (1.16% penalty-removed) |
| linear χ² | 809/780, p = 22.90% | 818/780, p = 16.76% |
| card nuisances (3673) | max |pull| 1.219, 0 beyond 2σ | max |pull| 1.315, 0 beyond 2σ |
| σ(alpha_s) | 0.001321 | **0.001097** |
| full-cov condition number | 2.98e+09 | **2.06e+08** |

Δχ² ≈ 11.6 for what is effectively two enforced inequalities is **genuine tension**, in the
same class as the ≈16.6 the old `scetlib_np` wall showed
(`knowledge` note `np_wall_local_minima`). The data do want an unphysical NP function; the
wall is not tidying away a numerical artefact.

Three things are nevertheless clearly *better* walled. Convergence: EDM improves by 1439×
in 40% fewer iterations, and the full covariance's condition number by 14× — the wall
removes the flat unphysical directions that were stalling the minimiser, which is why the
walled fit was also 1.75× faster. The card sector stays impeccable either way (zero of 3673
nuisances beyond 2σ), so the tension lives entirely in the NP block and not in the
experimental model. And `sigma(alpha_s)` **tightens by 17%**, 0.001321 → 0.001097 — read
carefully: that is not new information, it is the removal of NP freedom that pointed into
unphysical territory, and `rho(alphaS, lambda4)` rises 0.45 → 0.63 as the block stiffens.

The saturated p-value falling 2.33% → 1.07% is the honest price: a physical NP function
describes this data worse than an unphysical one, and at ~1% it is a poor-but-not-excluded
fit. Both p-values come from the same `ndof = 733`; the walled one is quoted with the
penalty left in (1.07%) and removed (1.16%), since the saturated reference NLL is ≈0 in both
fits so the penalty enters the saturated χ² twice over.

**Figures.** `np_form_factors.png` — both form factors at anchor / unwalled / walled, with
a zoom on the small-`b_T` turn-on where the anti-damping lives.
`tmd_damping_vs_Y.png` — the two TMD coefficients versus rapidity, showing the unwalled
cubic crossing zero at `|Y| ≈ 2.05` and the wall being imposed at the two extremes only
(valid because both are monotonic in `Y²`).

---

## Findings

1. The port works: the theta→physical map is `anchor + width·theta` with the width from
   `params.REPARAM` and the anchor from the card's recorded correction runcard, and it
   reproduces the DATABLIND physical lambdas exactly — (evidence:
   `logs/verify_map_260910_164739.log`).
2. The walled fit keeps 7 of 8 damping conditions, fixing the consequential violation
   (`lambda2_nu` −0.058 → +0.0049) at Δχ² = 11.6 and a saturated p-value of 2.33% → 1.07%
   — (evidence: `logs/analyse_walled_260910_172452.log`, `logs/fit_DATAWALL5_260910_165137.log`).
3. **The wall improves convergence sharply**: EDM 1.39e-03 → 9.63e-07 (1439×) in 138
   instead of 221 iterations, and the full covariance condition number 2.98e+09 → 2.06e+08.
   The unphysical region was a set of flat directions the minimiser was stalling in —
   (evidence: same logs, `logs/cov_260910_172731.log`).
4. For `tanh_2`, SCETlib's `np_effective` **does** carry the `L2³/(3·linf³)·b³`
   arctanh-correction term, so the TMD damping condition is `3·linf²·lambda4 + L2³ ≥ 0`,
   not `lambda4 ≥ 0`. `lambda4 < 0` alone is therefore not unphysical — (evidence:
   `/work/submit/lavezzo/alphaS/scetlib-audit-b66f8de/include/scetlib/qT/NP_models_formulas.hpp:87-89`).
   AN-25-085 Eq. (eq:npf) writes one power of `Lambda_inf` where the source writes three;
   `linf = 1` here so it is numerically moot, but the note is the one to trust.
5. `lambda_inf`/`lambda_inf_nu` are **not** reparametrised: their fit coordinate is physical
   and their start value is the anchor, not 0. Any postfit tool that assumes "theta = 0 is
   the anchor" universally is wrong for them — (evidence: `logs/verify_map_260910_164739.log`,
   CHECK 1).
6. The binding |Y| is a first-class physics choice, not a nuisance constant: at the
   DATABLIND tune the bare penalty is 25× larger and the `delta_lambda2` gradient 2000×
   larger at `ymax=5` than at the card-derived `ymax=2.5` — (evidence:
   `logs/unit_wall_260910_165020.log`).
7. The NP block carries one near-null covariance direction in **both** fits (1.35e-09
   unwalled, 1.13e-08 walled). Which parameter it projects onto changes between minima
   (`lambda4` unwalled, `lambda4_nu` walled), so a tiny reported σ on one lambda is that
   direction, not a measurement of that lambda — (evidence: `logs/cov_260910_172731.log`).
8. `gamma_nu_np_model` is evaluated at the **raw** `bT`; `bStar` enters only the
   perturbative logarithm, and `b0_over_bmax_global = 0` makes b* the identity on the TMD
   side. So the wall's "for all b ≥ 0" conditions are exact, not conservative — (evidence:
   `scetlib-audit-b66f8de/src/qT/Gamma_nu.cpp:102,117`; `merged_full/cache.conf`).

*Findings 4, 5, 7 and 8 generalise beyond this study — they are facts about the model and
the SCETlib source, not about this fit. Candidates for `knowledge/`.*

---

## Open questions

- **The last violation.** `lambda4_nu = −4.3e-4` needs either a hard reparametrisation
  (fit `sqrt(lambda4_nu)`, or the `tanh_6_abs` damping fold already in the memory index) or
  a per-condition tau, because that direction's ~5e7 curvature is beyond any global tau
  that leaves the fit conditioned. It is also the *cheap* violation: the anti-damping sits
  at `b_T > 3.4 GeV⁻¹` where `f^NP ≈ 10⁻³`.
- **`lambda2_nu` is railed**, so its value is the margin (5e-3) and its σ (0.047 in theta)
  is `1/sqrt(2·exp(2tau)·width²)` — the predicted wall width to 1%, not data. Any downstream
  use of the walled NP tune must not read it as a measurement.
- **Is the CS-side lattice constraint compatible with this data at all?** The walled fit
  drives `gamma_nu^NP` to nearly zero against a lattice anchor of `lambda2_nu = 0.15`. A
  scan of the loss against `lambda2_nu` held at fixed physical values (0, 0.05, 0.10, 0.15)
  would separate "the data dislike the lattice tune" from "the data dislike damping".
- **The wall reads the *correction's* anchor.** A fit run with `anchor_source=cache` or
  `anchor_override=` moves the model's map without moving the wall's, and nothing in
  `indata` can detect it. The wall prints every anchor/width/held value it resolved so the
  mismatch is visible in the log, but it is not enforced. One line in `param_model.py`
  publishing the model's anchor on `indata` would close it — deliberately not done, since
  this task owned only the new file.
- **`NP_DAMPING_MARGIN = 5e-3` is applied to quantities of different dimension**
  (`lambda4_nu` and the cubic `3·linf²·lambda4 + L2³`), inherited from the original. Worth
  making dimensionally sensible before this becomes production.
- **The anchor sits on the wall.** This correction has `lambda4_nu = 0` exactly, so any
  nonzero margin mildly penalises the anchor itself (2.5e-5 bare = 0.55 in NLL at tau=5).
  Harmless at 1% of the prior width, but "penalty = 0 at the start" is not true here.
- **`--doImpacts` was not run walled**, so the NP-group impact on alpha_s under the wall is
  unmeasured. Worth one more fit if the walled tune is going to be quoted.
