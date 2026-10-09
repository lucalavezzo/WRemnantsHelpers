---
title: Y-shape of the TMD NP function — first look
slug: 261007-y-shape-first-look
study: tmd-rapidity-shape
status: done          # active | done | paused | abandoned
created: 2026-10-07
updated: 2026-10-07
owner: study-worker
---

# Y-shape of the TMD NP function — first look

**Task:** Can we learn anything about the rapidity dependence L2(Y) = λ2 + δλ2·Y² of the TMD NP function from our fits: is Y² adequate, and how much does `alphaS` depend on the forward shape (slope dαS/dc at the active wall face c = L2(2.5))?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-10-07 22:10)

- **Answer:** the Y² form is adequate at our precision, and a Y⁴ / x-dependent term is **not worth building now**.
  - The active wall face c = L2(|Y| = 2.5) = 0 moves `alphaS` by **−0.032 σ_NOM per +0.01 GeV²** of c (Newton slope,
    wall-free Hessian at LATB8). Releasing the face would gain the data only **Δχ² = 0.50**.
  - **`alphaS` does not care about the rapidity SHAPE** (wall-free ρ(`alphaS`, L2(2.5) − L2(0)) = −0.025). It cares
    about the overall LEVEL of L2 (ρ = −0.44). The |Y| = 2.5 face binds because Λ2 is low (0.049 GeV²), not because
    the shape is off: δλ2 = −0.0078 ± 0.0078 agrees with the MAP22 x-dependence (−0.0079 ± 0.0011).
  - The postfit residuals show no forward-rapidity pattern.
- **Next action:** none. Task closed. Optional follow-ups are under Open questions.
- **Blocking on:** nothing.
- **Running:** nothing. YNOWALL8 finished at 21:31 with exit 0 ([logs/YNOWALL8.log](logs/YNOWALL8.log)).

---

## Log

### 2026-10-07 (21:05–22:10)
- Read the study logbook, `lattice-cs-kernel` (LATB8, the wall-face table, 261007-lattice-term-native), AN theory.tex
  l. 230–305 and uncerts.tex l. 203, and `knowledge/30_physics_global/np_parametrization_constraints.md` §16–16c (the
  MAP22 → (Λ2, ΔΛ2, Λ4) mapping and the 2026-08-03 decision "y parametrisation: NO more flexibility").
- **YNOWALL8** is the wall-free Hessian pass. It is LATB8's command
  ([cmds/YNOWALL8.cmd](cmds/YNOWALL8.cmd)) with these changes and nothing else: the `NPDampingWall` `-r` is dropped;
  `--noFit --saveHists`; the input is `--externalPostfit seeds/seed_LATB8_flat.hdf5` (LATB8's vector bit for bit, no
  covariance, so rabbit recomputes the Hessian); there is no snapshot file and no `--earlyStopping`. Kept as in LATB8:
  the `LatticeCSTerm` (syst=Jnf+Jbt, offset=min), τ = 8, the |Y| ≤ 2.5 subset cache `pdf62_y35_260921_y25`, and the 44
  priors with the TMD priors pinned.
  - Build: it runs on the scetlib-cms `gamma-nu-points` branch build (6ab371a), as LATB8 did, because the native
    lattice term needs `DrellYan.gamma_nu_points`. So the setting is `--scetlib <branch build>`, not `current`
    ([scripts/run_fit.sh](scripts/run_fit.sh)).
  - Versions: WRemnants 4e7e481e (LATB8 used b14f84f4; the only difference is the term's CompositeParamModel support,
    which the native task's SATCHK showed gives the same χ² bitwise). rabbit 2a59246.
  - Launched through mem_gate (260 GB, DONE_RE `edmval:`). A first try, without `--saveHists`, was killed by me after
    30 s and relaunched with it ([logs/YNOWALL8_try1_killed.log](logs/YNOWALL8_try1_killed.log)). I removed my stale
    `/tmp/alphas_slot1.need` afterwards. The Hessian took 503 s, and the job exited 0 at 21:31.
  - Consistency: the parameter vector is identical to LATB8's (max |Δθ| = 0). The saturated χ² is 753.35/777, as in
    LATB8, since the wall term at LATB8 is 7e-7 NLL. edm (without the wall) = 0.248.
  - Output: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261007_y_shape_first_look/fitresults_YNOWALL8.hdf5`
    (covariance + prefit/postfit/data hists).
- [scripts/slope.py](scripts/slope.py) → [slope.json](slope.json): the slope, the multiplier, and the identity
  cross-check. [scripts/plot_y_shape.py](scripts/plot_y_shape.py) → the three plots and
  [y_shape_plots.json](y_shape_plots.json). [scripts/residuals_numbers.py](scripts/residuals_numbers.py) gives the
  residual table. [scripts/map22_y4.py](scripts/map22_y4.py) → [map22_y4.json](map22_y4.json) gives the MAP22
  non-quadratic shape. It reuses `np-wall-local-minima/scripts/map_replicas.py` and its 251 replicas.
- Code reading for Y⁴ (SCETlib 2dd978a in `$WREM_BASE/scetlib-cms`; WRemnants 4e7e481e): see Result §4.

---

## Result

### 0. Caveats first
- Real data, `alphaS` **blinded**. Shifts are in σ_NOM = σ(`alphaS`) of NOMSTIFF (hessian), and no central value is used.
- Everything is evaluated at **LATB8's** point: card A, the |Y| ≤ 2.5 subset cache, the native lattice term, τ = 8, and
  λ4_ν floating. NOMSTIFF numbers come from its own walled covariance, through the identity in §1.
- **Newton slopes are local (linear) statements** at the physical point LATB8. The "full release" number is a Newton
  step INTO the unphysical region (L2(2.5) < 0 is forward anti-damping, where the AD cache is not validated). It is
  given only as a labelled orientation number, **not as a result**.
- The residuals in §2 use the data statistical error only. The pass had no `--computeHistErrors`, so they ignore the
  postfit, systematic and MC-stat uncertainties. They are normalised residuals, not pulls.
- NOMSTIFF has **no saved postfit hists** (no `--saveHists` in its run), so §2 covers LATB8 only. NOMSTIFF's predictions
  differ from LATB8 by −0.11σ_NOM in `alphaS`, with the same single active face. Getting its hists would need a
  `--noFit --saveHists` pass (one cache load, ~15 min), which was not run (task rule: no new fits for step 2).

### 1. Sensitivity of `alphaS` to the forward level L2(|Y| = 2.5)

The face is c = L2(2.5) = λ2 + 6.25·δλ2, linear in θ (λ2 = 0.4 + 0.5θ, δλ2 = 0.5θ). So the wall's Hessian is exactly
2k·g gᵀ with k = e^{2τ} = e^16. The slope comes from the WALL-FREE covariance C_f (data + priors + lattice) at LATB8:
S = C_f(`alphaS`, c)/V_f(c). The same ratio from LATB8's own walled covariance must agree for any k (Sherman–Morrison),
and it does.

| quantity | LATB8 | NOMSTIFF |
|---|---|---|
| **d`alphaS`/dc** [σ_NOM per GeV²] (wall-free Hessian YNOWALL8) | **−3.192** | – |
| same, from the walled covariance (identity) | −3.192 (agrees to 1e-10 rel.; C·g shape to 4e-7) | −2.574 |
| **per +0.01 GeV² of forward L2** | **−0.032 σ_NOM** | −0.026 σ_NOM |
| wall multiplier μ = d(NLL_rest)/dc, from the wall (2k·\|c*\|, c* = −2.8e-7) | 4.93 GeV⁻² | 16.3 GeV⁻² |
| μ from the wall-free edm (√(2·edm/V_f), edm 0.248) | 4.93 (agrees to 1e-9: the rest's gradient is purely along this one face) | – |
| wall-free σ(c), ρ(`alphaS`, c) | 0.143 GeV², −0.425 | – |
| σ(`alphaS`)/σ_NOM, wall-free → walled | 1.074 → 0.972 (×0.905) | – |
| **ORIENTATION ONLY (unphysical):** full release, Newton | Δc = −0.101 GeV², Δ`alphaS` = +0.32σ_NOM, Δχ² = −0.50 | – |

What the numbers mean:
- **The data barely push on the face.** Removing it entirely gains Δχ² = 0.50 (0.7σ), so this is not a tension. The
  multiplier is 3.3× smaller at LATB8 than at NOMSTIFF. A plausible reason, not tested: the lattice term holds λ2_ν,
  which is strongly anticorrelated with Λ2 (wall-free ρ = −0.90; lattice-cs-kernel finding 4).
- **The face matters for σ(`alphaS`)**, through the boundary. Wall-free σ(`alphaS`) is 7 % larger than NOMSTIFF's and
  10 % larger than walled LATB8's. In quadrature that is 0.46 σ_NOM of "freedom in c", which the physical boundary
  removes. It is the usual one-sided-boundary effect: the walled Hessian σ is the physical-side width, not a Gaussian
  one.
- **Scale in natural units:** moving the forward L2 from 0 to MAP22's forward value (0.052 GeV²) moves `alphaS` by
  −0.17σ_NOM, at a data cost of Δχ² ≈ 0.6. This is linear and on the physical side, so it is a legitimate local
  estimate.

### 2. Where in Y the data pull: no forward pattern

![Normalised residuals (data − postfit)/σ_data on the reco ptll × yll grid at LATB8; data stat only, not pulls](residual_map_LATB8.png)

![data/postfit − 1 vs ptll in five |yll| groups (±yll folded, ptll merged into 11 windows); LATB8, data-stat errors only](ratio_by_absy_LATB8.png)

*Both: LATB8's postfit (YNOWALL8, the same vector). Data statistical errors only. Residuals, not pulls.*

data/postfit − 1 in % (data-stat error), |yll| folded, by ptll window
([scripts/residuals_numbers.py](scripts/residuals_numbers.py)):

| \|yll\| | 0–4 GeV | 4–10 | 10–20 | 20–44 | Σr² / bins |
|---|---|---|---|---|---|
| 0–0.5 | +0.06 ± 0.17 | +0.06 ± 0.12 | −0.06 ± 0.13 | −0.01 ± 0.16 | 196.8 / 234 |
| 0.5–1.1 | +0.00 ± 0.16 | −0.10 ± 0.11 | +0.13 ± 0.12 | −0.15 ± 0.15 | 188.9 / 234 |
| 1.1–1.5 | +0.33 ± 0.20 | −0.07 ± 0.14 | −0.10 ± 0.15 | +0.01 ± 0.19 | 131.0 / 156 |
| 1.5–1.8 | +0.06 ± 0.28 | +0.08 ± 0.19 | +0.05 ± 0.20 | +0.16 ± 0.24 | 68.0 / 78 |
| 1.8–2.5 | −0.20 ± 0.33 | −0.02 ± 0.22 | −0.11 ± 0.22 | −0.02 ± 0.28 | 44.1 / 78 |

- Every window agrees with zero within 1.7σ, and no slice has Σr² above its bin count. The forward slice
  (1.8 < |yll| < 2.5) is the quietest. The residual map shows no structure in yll that is coherent in ptll.
- **What δλ2·Y² would absorb, and why it is not there:** lowering L2 forward means less Gaussian smearing at forward Y,
  i.e. a sharper low-ptll peak in the forward slices (an excess at ptll ≲ 4 GeV, a deficit at ~5–10 GeV). The forward
  slice shows −0.20 ± 0.33 % at 0–4 GeV, compatible with zero and of the opposite sign. This is consistent with Δχ² = 0.5
  for full release.
- **Shape vs level** (wall-free correlations at LATB8, physical units):

  | | value ± σ | ρ with `alphaS` |
  |---|---|---|
  | level L2(0) = Λ2 | 0.049 ± 0.135 GeV² | **−0.44** |
  | shape L2(2.5) − L2(0) = 6.25·δλ2 | −0.049 ± 0.049 GeV² | **−0.025** |
  | δλ2 | −0.0078 ± 0.0078 GeV² | −0.025 |

  ρ(Λ2, λ2_ν) = −0.90 and ρ(`alphaS`, Λ4) = +0.78. The rapidity shape is essentially uncorrelated with `alphaS`. The
  marginal slope is −0.55 σ_NOM/GeV² for the shape against −3.5 for the level. **The face at |Y| = 2.5 is a level
  constraint in disguise.** δλ2 only decides where in Y the floor L2 ≥ 0 bites first; with δλ2 = 0 the same floor
  would bind at all Y at once.

![L2(Y): LATB8 with its wall-free ±1σ band, NOMSTIFF, MAP22 (small-b, central replica), AN nominal](L2_of_Y.png)

*LATB8's ±1σ band is the wall-free covariance at LATB8's point, so it extends into the unphysical L2 < 0 region that
the wall forbids. MAP22 is the per-beam intrinsic part with its CS evolution stripped, combined as the two-beam product
at Z/13 TeV (knowledge §16). AN nominal runs to 1.03 GeV² at |Y| = 2.5 (off scale).*

**AN tune next to ours.**
- AN nominal: Λ2 = 0.25, ΔΛ2 = +0.125 ± 0.02 (prefit), Λ4 = 0.06, Λ∞ = 1 (theory.tex l. 294–303, uncerts.tex l. 203).
  So L2(2.5) = 1.03 GeV².
- **The AN tune violates and saturates nothing.** CS: λ2_ν = 0.087 ≥ 0, λ4_ν = 0.0074 ≥ 0, λ∞_ν = 1.69 > 0. TMD:
  L2(0) = 0.25, L2(2.5) = 1.03, 3Λ∞²Λ4 + L2³ = 0.196 at Y = 0 and 1.28 at Y = 2.5. Every condition has a wide margin.
- Our δλ2 = −0.0078 ± 0.0078 sits **17σ (ours) or 6.6σ (the AN's own ±0.02)** below the AN's +0.125. It agrees with
  the MAP22-derived −0.0079 ± 0.0011 (knowledge §16, converged Y grid) at 0.0σ. Knowledge §16b already records that
  the AN value is inherited from the mW analysis, and that rapidity-sensitive 2D fits land on the MAP22 sign.
- Our card's anchor has δλ2 = 0 and the fit's prior is θ ± 1, i.e. ±0.5 GeV². So δλ2 here is data-determined (the prior
  is 64× wider than σ), not prior-pulled.

### 3. Theory: why Y², and what an x-dependent f_NP implies

- **Kinematics.** At Born level x_{a,b} = (Q/√s)·e^{±Y}. For Q = m_Z and √s = 13 TeV, x = 7.0·10⁻³ at Y = 0, and at
  |Y| = 2.5 one beam is at x = 0.085 and the other at 5.8·10⁻⁴. So |Y| ≤ 2.5 spans 2.2 decades of x, and x_a·x_b = Q²/s
  is fixed: Y only spreads the pair at fixed geometric mean.
- **Why Y² is the leading term.** Write ln f^NP_beam ≈ −c(x) b²/4 per beam, so L2(Y) = [c(x_a) + c(x_b)]/8 (knowledge
  §16c). Expanding c in ℓ = ln(x/x0) around x0 = Q/√s, with c_n = dⁿc/dℓⁿ:
  L2(Y) = [2c0 + c2·Y² + c4·Y⁴/12 + …]/8. The odd terms cancel between the beams, so **ΔΛ2 = c2/8 is the leading
  term, and a Y⁴ coefficient δ4 = c4/96 is the next one.** Y² is therefore the first term of a symmetric ln x expansion,
  not a small-Y approximation. With |Y| up to 2.5 the expansion parameter is O(1), so Y² is adequate only if c(x) is
  smooth on the scale of one unit of ln x.
- **How big is the Y⁴ term for a realistic x dependence?** For MAP22 (all 251 replicas,
  [map22_y4.json](map22_y4.json)), c(x) is concave in ln x with a peak near x ≈ 0.02. Results:
  - L2 falls from 0.095 to 0.052 GeV² over Y = 0 → 2.5, and the local coefficient (L2(Y) − L2(0))/Y² runs from −0.0037
    to −0.0076.
  - A Y² + Y⁴ fit gives δ4 = −2.5·10⁻⁴ GeV² (68 %: −4.3·10⁻⁴ … +0.4·10⁻⁴). Y² alone misses the true L2(Y) by at most
    **0.0025 GeV²** (median), and by **0.0016 GeV²** at the |Y| = 2.5 edge.
  - Our wall-free σ of the shape is 0.049 GeV², 20–30× larger. Through §1's slope, a MAP22-sized edge error is
    **≤ 0.005–0.008 σ_NOM** in `alphaS`.
- **A linear-in-x width is not "Y² plus small corrections" either.** If the width varies linearly in x, the beam sum
  ∝ x_a + x_b = 2x0·cosh Y. This contains every even power, with δ4/ΔΛ2 = 1/12, so the Y⁴ term is 52 % of the Y² term at
  Y = 2.5. But the whole Y variation is then O(x0·(cosh 2.5 − 1)) ≈ 0.036 × (width difference): small at Z/13 TeV,
  because x0 is small. (This is algebra on the generic form, not a fit to any one extraction.)
- **Literature parametrisations** (stated from memory; check the exact forms before quoting):
  - **MAP22**, Bacchetta et al., [arXiv:2206.07598](https://arxiv.org/abs/2206.07598). Flavour-independent; f_NP is a
    sum of three Gaussian-like terms with widths g_i(x) ∝ x^{σ_i}(1−x)^{α_i²} normalised at x̂ = 0.1, times the CS factor
    exp(−g2² b² ln(ζ/Q0²)/4). The form is verified in the released replica code used above.
  - **SV19**, Scimemi–Vladimirov, [arXiv:1912.06532](https://arxiv.org/abs/1912.06532): width linear in x,
    (λ1(1−x) + λ2·x + λ5·x(1−x)), with a b² → b²/√(1 + λ3 x^{λ4} b²) softening. The form is to check.
  - **ART23**, Moos–Scimemi–Vladimirov–Zurita, [arXiv:2305.07473](https://arxiv.org/abs/2305.07473): flavour-dependent,
    with x-linear widths per flavour, ~1/cosh((λ1^f(1−x) + λ2^f x) b). The exact form is to check.
  - **MAP24** (flavour-dependent MAP): arXiv number to check (2405.13833?).
  - **Our form** (AN Eq. npf, from Cridge–Marinelli–Tackmann [arXiv:2506.13874](https://arxiv.org/abs/2506.13874)):
    flavour-averaged, with Y² only. The AN states (theory.tex l. 254–255) that x and flavour dependence is "subject of
    ongoing theoretical work".

  None of these fits parametrises in Y. All of them parametrise in x per beam, so in our language they generate every
  even power of Y. At Z/13 TeV and |Y| ≤ 2.5, the MAP22 case shows the beyond-Y² part is sub-resolution.

### 4. Y⁴ feasibility (code reading only)

- **Where L2(Y) enters.** SCETlib's AD kernel evaluates the NP factor **live at every replayed node**:
  `include/scetlib/qT/ad/ad_kernel.hpp` l. ~1658–1666 reads `eff_dl2 = pval(p, ad_g.ip_eff_dlam2, …)`, computes the
  node's Y_np = ½ ln(x_A/x_B), and calls `formulas::np_effective(Ynp, bT, model, linf, l2, l4, dl2, l6)`. In
  `include/scetlib/qT/NP_models_formulas.hpp` l. 55, `lambda2_Y = lambda2 + delta_lambda2*pow2(Y)`. Two more call sites
  read `eff_dl2`: `py/qT/DrellYanAD.cpp` l. 10988 and l. 11120. The NP factor is on the clad tape, so the gradient and
  Hessian of a new term come for free after a rebuild of the library.
- **Is a new parameter free? No. It is tied to the cache file.**
  - `Ad_evaluator::_build_registry` (`src/qT/ad/ad_context.cpp` l. ~171–190) adds `np_eff_*` names in order. Its own
    comment says that registering an extra parameter "shift[s] all later indices and invalidat[es] rules".
  - The rule file fingerprints the parameter NAMES in order (`_rule_config_fingerprint`, DrellYanAD.cpp l. ~10230) and
    stores the anchor vector, which is sized by the registry.
  - The rule file also stores `ad::GlobalData` as raw bytes and refuses any size mismatch (`layout_check`, l. ~10581;
    the comment at l. ~10440 names exactly this case, "adding a field to GlobalData … silently reinterprets every
    following byte").
  - A `delta4_lambda2` needs new `GlobalData` fields (value + index), so **every existing cache is refused**: a
    kRuleVersion bump and a **full cache rebuild** (770-bin build ≈ 25 h wall on the node; knowledge
    scetlib_ad_cache_build_parallelism.md).
  - In principle a rule-file migrator could avoid the rebuild: rewrite the layout, append δ4 = 0 to the anchor, update
    the fingerprint. The node data do not depend on the NP tune except through node placement at the anchor, and
    δ4 = 0 there. But it would bypass exactly the safety checks above and would need a bitwise replay validation. Not
    verified.
- **Param model (WRemnants `scetlib_ad/params.py`).** It needs entries for the new name in the name map (l. 30, the
  cache→fit names), `REPARAM` (l. 316, a unit width), the correction-anchor key table (l. 521; the correction runcard
  has no δ4, so an anchor of 0 must be allowed explicitly), and the prior lists (l. 146–162, 431–443). The rest of the
  model is name-driven. All of this is mechanical.
- **NPDampingWall.** With L2(u) = λ2 + δ2·u + δ4·u² (u = Y² ∈ [0, 6.25]), the current "evaluate at Y = 0 and Y_max"
  logic is **wrong**: L2 is no longer monotone in u, and for δ4 > 0 the minimum can sit at the interior vertex
  u* = −δ2/(2δ4). B = Λ4 + L2³/(3Λ∞²) is monotone in L2, so it is minimal at the same u. The wall must enforce
  min_{u ∈ [0, 6.25]} L2 ≥ margin and the B condition at that same u. There are two options:
  - (a) a dense u-grid (~26 points; smooth, trivially correct, cheap);
  - (b) endpoints plus a gated vertex term relu²(−L2(u*))·1[0 < u* < 6.25] (exact, but piecewise).

  `_TMD_LAMBDAS`, `damping_conditions`, the held-λ check and the docstring change too, as do `np_function_plots.py`,
  `fitresult_lambdas.py` and `param_model_diagnostics.py`.
- **Effort.** SCETlib ~1–2 days (formula, registry, GlobalData, pybind/runcard, validation of gradients vs FD and vs
  the class). WRemnants ~1 day. Cache rebuild ~1 day wall plus node contention. Refit + Hessian + validation ~1 day.
  **Total ≈ 1 week**, most of it the rebuild and its validation.

### 5. Physics read (3 lines)
1. In our fits the TMD rapidity shape is measured (δλ2 = −0.0078 ± 0.0078 GeV²), agrees with what MAP22's x dependence
   predicts (−0.0079), and is **uncorrelated with `alphaS`** (ρ = −0.025). The AN's +0.125 is strongly disfavoured by
   the rapidity-resolved data (17σ in the Gaussian approximation).
2. The only active wall face, L2(2.5) = 0, is a floor on the overall TMD smearing LEVEL Λ2. It costs the data Δχ² = 0.5
   and moves `alphaS` by −0.032 σ_NOM per +0.01 GeV² of forward L2. Raising it to MAP22's forward value would move
   `alphaS` by −0.17σ.
3. A realistic non-quadratic (Y⁴) shape is 20–30× below our resolution and worth ≤ 0.01 σ_NOM, while a Y⁴ term costs
   ~1 week plus a cache rebuild and needs a new interior-minimum wall. **Recommendation: do not build it.** If the NP
   systematic needs strengthening, the lever is the LEVEL of L2 (the Λ2 ↔ λ2_ν degeneracy and the floor's position),
   not its Y shape. This agrees with knowledge §16c (2026-08-03).

---

## Findings

1. Newton slope at LATB8: d`alphaS`/dL2(|Y|=2.5) = −3.19 σ_NOM/GeV² (−0.032 σ_NOM per 0.01 GeV²). The wall-free
   Hessian and LATB8's walled covariance agree to 1e-10 via Sherman–Morrison. — (evidence: [slope.json](slope.json))
2. **General technique (for knowledge/):** for a single active relu² wall face linear in θ, the constrained-response
   slope C_f(a,c)/V_f(c) can be read directly from the walled fit's covariance, with no wall-free Hessian pass; and the
   multiplier is μ = 2e^{2τ}·|c*| = √(2·edm_free/V_f). Here both agree to 1e-9. — (evidence: [slope.json](slope.json))
3. The face costs Δχ² = 0.50 (μ = 4.93 GeV⁻²); NOMSTIFF's multiplier is 3.3× larger (16.3). — (evidence: [slope.json](slope.json))
4. No forward-rapidity residual pattern at LATB8. All |yll| × ptll windows agree with 0 within 1.7σ (data stat). —
   (evidence: [ratio_by_absy_LATB8.png](ratio_by_absy_LATB8.png), [residual_map_LATB8.png](residual_map_LATB8.png))
5. Wall-free ρ(`alphaS`, shape) = −0.025 vs ρ(`alphaS`, level) = −0.44: the |Y| = 2.5 face is a level constraint.
   σ(δλ2) = 0.0078 GeV² wall-free. — (evidence: Result §2, from the YNOWALL8 covariance)
6. MAP22's L2(Y) is non-quadratic: δ4 = −2.5e-4 GeV², max deviation from the best Y² fit 0.0025 GeV², 0.0016 at the
   edge. — (evidence: [map22_y4.json](map22_y4.json))
7. Adding an NP parameter to SCETlib-AD changes `GlobalData`'s size and the parameter-name fingerprint, so every
   existing cache is refused (rebuild, or an unvalidated migrator). — (evidence: Result §4, DrellYanAD.cpp
   layout_check / fingerprint)
8. The AN nominal NP tune satisfies every damping condition with margin. — (evidence: Result §2)

---

## Open questions

- **σ(δλ2) = 0.0078 here vs 0.002 in the 2026-07/08 2D fits** (knowledge §16b: davidFix ±0.0019). It is a different
  model (btgrid, tanh_6 with λ6 = 0.01) and freeze list, while here λ4_ν and the lattice term float. I did not chase why
  the shape is 4× less constrained now.
- NOMSTIFF postfit hists do not exist. A `--noFit --saveHists` pass at NOMSTIFF would complete §2 (~15 min plus one
  cache load).
- If the NP systematic is revisited: a cheap probe of the LEVEL is to move the TMD floor (e.g. require
  L2(2.5) ≥ 0.05, MAP22's forward value). The Newton prediction is −0.17σ_NOM at Δχ² ≈ 0.6, and a real refit would
  confirm the linearity.
- The `alphaS`–Λ4 correlation (+0.78 wall-free) is the largest NP coupling of `alphaS` at LATB8. Not a Y question.
