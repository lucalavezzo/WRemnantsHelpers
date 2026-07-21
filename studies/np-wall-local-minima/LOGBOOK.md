---
title: NP damping-wall local minima & wall softening
slug: np-wall-local-minima
status: active
created: 2026-07-16
updated: 2026-07-17
---

# NP damping-wall local minima & wall softening — logbook

**Goal:** understand why the walled SCETlib-NP fit reaches a *lower* NLL than the
unwalled one (counterintuitive), characterize the multimodal likelihood this
exposed, and decide how (if at all) to soften/reshape the physical-damping wall
so the reported α_s uses a defensible NP treatment. Deliverable: an
α_s-vs-NP-treatment comparison table + a recommended wall.

Related: [[physical-lambda]] (RESOLVED via freezing λ4_ν=0 — a *different*, earlier
fix); `knowledge/30_physics_global/np_parametrization_constraints.md`;
wall code `WRemnants/wremnants/postprocessing/scetlib_np/np_damping_wall.py`.

---

## Orientation (read this if you're new to the study)

This is about the **non-perturbative (NP) form factors** in the SCETlib prediction of
the Z p$_T$ (ptll) spectrum, used in the α_s fit. Physics ref: `AN-25-085` (theory.tex,
Eqs. eq:npgamma/eq:npf) and `knowledge/30_physics_global/np_parametrization_constraints.md`.

**The NP model** (`scetlib_np/param_model.py`, `tanh_6` forms here) has two form factors —
functions of impact parameter b$_T$ (and boson rapidity Y), driven by the fit λ:
- **F_eff(b_T, Y)** — TMD form factor. Physical ⇔ it *damps* (≤1, decays in b_T). λ: `lambda2`, `lambda4`, `delta_lambda2` (=δλ2, the Y² coefficient of λ2), `lambda_inf`, `lambda6`.
- **γ_ν^NP(b_T)** — CS rapidity-anomalous-dimension NP piece. Physical ⇔ ≤0. λ: `lambda2_nu`, `lambda4_nu`, `lambda_inf_nu`, `lambda6_nu`.

Unphysical (wrong-sign) λ make a form factor **anti-damp / blow up** at large b_T; the
b_T (Hankel/Bessel) integral then gives an oscillating, partly **negative differential
σ(qT)**. The coarse qT→ptVGen gen-binning *averages that away* ("**laundering**"), so the
binned fit stays finite and the minimizer can't see the pathology — which is why an
explicit constraint is needed.

**The wall** = `np_damping_wall.py::NPDampingWall`, a rabbit regularizer that penalizes
non-damping λ at fit time (penalty × `exp(2·--regularizationStrength)`). "walled" = ran with it.

**Run shorthand used throughout** (all real-data 2D Z, ptll×yll, `260701_Z_2D` card, tanh_6;
freeze λ_inf, λ_inf_ν, λ6, λ6_ν → 5 floating λ + the α_s NOI `pdfAlphaS`):
- **walled** — physical (damping) solution: `260702_2D_l6nu0p01_l60p01`, nll 363.5, λ2=+0.17.
- **nowall / A** — unconstrained: `260716_2D_l6nu0p01_l60p01_nowall_matchedStartingPoint`, nll 366.9, λ2=−0.48 (unphysical, a shallow local min).
- **C** — the deep, unphysical, best-NLL optimum (unwalled, seeded from walled): `260716_2D_seedWalledFull_nowall`, nll 355.2, λ2=+1.10, λ4=−0.61.
- **θ(α_s)** = postfit `pdfAlphaS` pull (BLINDED by a common offset → only compare *differences* across runs). **σ(α_s)** = its postfit error (needs a covariance/hessian pass). **ptll sat-p** = the ptll-projection saturated-model goodness-of-fit p-value (low = poor fit).

Cross-run numbers are assembled with `scripts/fit_summary_table.py --spec studies/np-wall-local-minima/runs.yaml` (see Reproduce).

---

## START HERE (status as of 2026-07-17)

> **The NP treatment is a DOMINANT systematic on α_s — not cosmetic.** Across
> treatments the α_s pull spans **−7.6 (A) → −8.4 (physical/capped) → −10.1 (C, best
> NLL)**, i.e. ~2.5–3σ with σ(α_s)≈0.50–0.68. And the ptll saturated-test p-value
> splits them the "wrong" way — physical walled **3.5%** (poor) vs unphysical C
> **43%** (good): the data *prefer* the unphysical description, so there's a real
> ptll tension the NP is resolving unphysically (probably via the laundered ringing).
>
> **Leading lead:** C's TMD blowup is **entirely δλ2<0** — with δλ2=0 the SAME
> λ2=1.10, λ4=−0.61 make F_eff damp at every Y (onset was Y≈1.8). δλ2 is an
> approximate, near-degenerate term (ρ(λ2,δλ2)≈−1) we can drop. The δλ2=0 fit tests
> whether removing it lands a PHYSICAL, low-NLL, good-ptll-GOF fit → potential clean
> resolution. **Watch its ptll sat-p specifically.**

- **Next action:** read the 6 running fits as they land (watchers armed):
  Relaunched 2026-07-17 PM (after killing everything for a *then-postponed* submit82 reboot):
  `260717_2D_priors_sig0p5` (cov+sat resume), `260717_2D_C_dl2frozen0` (unwalled δλ2=0,
  seeded at C — the key "does δλ2=0 tame C" test), and the **λ-wall margin scan**
  `260717_2D_wallmargin_{plus0p005,0,minus0p02,minus0p05,minus0p10}` + `260717_2D_wall_dl2frozen0`
  (all fit→cov→sat, THREADS=8; wrapper `scripts/wall_scan_point.sh`). Then rebuild the table:
  `python3 scripts/fit_summary_table.py --spec studies/np-wall-local-minima/runs.yaml -o <webdir> --compile` (OUTSIDE the container).
  Key questions: does α_s move as margin crosses 0 (the physical edge) into anti-damping, or is it
  stable within physical space? does δλ2=0 give a physical + good-ptll fit? margin=0 doubles as the
  end-to-end smoke test of the rewritten wall (expect physical, clean EDM, nll≈363).
- **Blocking on:** the 8 fits (fit step ~1–2 h at THREADS=8; + cov/sat).
- **Func-bound scan DROPPED** (see today's log): its EDM is *structurally* broken (boundary-pinned →
  non-PD Hessian → negative edmval), so no trustworthy σ(α_s). Replaced by the λ-wall margin scan —
  same physics question, clean EDM.

**Reasonable-solution stance (2026-07-17):** the λ are correlated (ρ(λ2,δλ2)≈−1),
poorly-constrained *nuisances* — chasing "physical central λ" is the wrong frame.
What matters is α_s + σ(α_s) + GOF. Preferred direction: **shrink the NP model** to
the principled, data-constrainable set (freeze δλ2, λ4_ν) so the fit is stable and
physical *without* a wall/prior threshold we can't motivate (no theory σ exists),
rather than tuning a wall/prior. The δλ2=0 fit is step one of exactly this.

### Plan of attack (agreed 2026-07-16)
1. **[DONE] Step 1 — wall-condition readout** at the walled postfit (which walls bind, how close). See "Step 1 table" below.
2. **σ(qT) diagnostic** — point-mode differential σ at walled/C/A; where (if) it goes negative. Scopes step 4, tests the "negative-σ laundered by rebin" mechanism (never yet proven).
3. **Function-bound wall** — pragmatic NP-magnitude prior: γ_ν^NP(b) ≤ 0.2, F_eff(b,y) ≤ 1.2 (=1+0.2 excursion), grid-based `relu²`, threshold on the `-r` line. **Scan the threshold** and track σ(α_s). New class, labeled a *prior*, not "physicality".
4. **σ(qT)≥0 wall** — principled, threshold-free. Feasibility caveat: penalty needs the *differential* σ (point mode) in the fit forward pass, not the (already-≥0) binned yields — confirm cost first (the step-2 diagnostic finds out).
5. **Assemble the deliverable table**: for each config {unwalled A, unwalled C, coeff-wall, function-bound×thresholds, σ≥0-wall} record `{nll, central α_s, σ(α_s), NP λ, σ(qT)≥0?, physical?}`. The physics question is how much α_s moves with the NP treatment.

---

## Log

<!-- newest first -->

### 2026-07-20 — fullNll re-fits of A / C / margin-0 launched (fit step only)

Luca asked for `nllvalfull` on the key configs (the table's NLL column was "---"
everywhere: rabbit only stores it under `--fullNll`, which the wrapper's fit step
now always passes). Re-running the three configs, fit step ONLY, exact same
settings as the originals (recovered from their meta commands, verified with
`--dryRun`), fresh dirs:

- `260717_2D_wallmargin_0` → `260720_2D_wallmargin_0_fullNll`
- `260716_2D_l6nu0p01_l60p01_nowall_matchedStartingPoint` (A) → `260720_2D_l6nu0p01_l60p01_nowall_matchedStartingPoint_fullNll`
- `260716_2D_seedWalledFull_nowall` (C) → `260720_2D_seedWalledFull_nowall_fullNll`
  (same seed: `--externalPostfit 260702_2D_l6nu0p01_l60p01/fitresults_t0.hdf5`, passed
  via the wrapper's `-f` since only the fit step runs)

Wrapper: `scripts/refit_fullnll_260720.sh` (sequential, THREADS=24).
Log: `logs/refit_fullnll_260720_260720_135251.log`. Launched 13:52.

**DONE (same day, ~21:00). All three re-fits reproduce their originals
BIT-IDENTICALLY** (max|Δλ|=0, Δnllvalreduced=0 exactly — deterministic minimizer,
same start). Full NLLs (2ΔNLL(full)): wallmargin_0 **4424.47**, no-wall A
**4428.05**, seedWalledFull C **4416.32** — same ordering as reduced (C best by
~8–12), constants shift all by ~+3698. Since the postfit points are identical,
the originals' cov/ + saturated/ outputs were SYMLINKED into the 260720 dirs
(rigorous: same point; provenance visible in the links and the files' own meta),
and `runs.yaml` now points the three rows at the 260720 dirs. Table rebuilt:
`~/public_html/alphaS/260720_fit_summary/fit_summary.pdf` — NLL (full) column
populated for these three rows; remaining rows fill in as runs are remade
through the updated wrapper (fit step now always passes `--fullNll`).
Watch-out for future babysitting: rabbit writes a LOCKED 38KB meta stub at
startup — "fitresults.hdf5 exists" does NOT mean the fit is done; watch the
process, not the file.

### 2026-07-17 (PM) — func-bound EDM structurally broken; natural-units margin on the λ-wall; margin scan launched
**Func-bound wall dropped as a covariance source.** Its postfit EDM is NEGATIVE
(260716 funcboundMax: nll 361.9, **edmval −7.5**; the earlier grid-sum was −90.6). This is
*not* "not-yet-converged" — the minimizer stopped (grad≈0), but the Hessian isn't
positive-definite there, so the CG Newton-decrement (`edmval = ½·gᵀH⁻¹g` via Hessian-*vector*
products, `fitter.py::edmval_cov_rows_hessfree` — no dense Hessian, so **no OOM**; the OOM in
param_model's docstring is the separate full-cov step, which uses `hessian_straightthrough=1`)
returns <0. Cause: the func-bound fit **rails onto the cap** — an active-constraint/boundary
solution *below* the physical valley (361.9 < walled 363.5), on the downhill slope toward C where
the DATA Hessian has negative curvature. A hard function cap the fit leans on can't give a clean
EDM by construction.
**Why the λ-wall's EDM IS clean (corrected — my "inactive" claim was wrong):** several λ-wall
terms sit on/at their knees (λ2_ν active at 0.0043<0.005 margin; Y=5 interior minQ=−0.0015<0). It's
clean because (a) its physical solution is a genuine data-likelihood local MIN (valley, PD data-Hessian:
walled nll 363.47 ≈ unwalled-physical 363.46), and (b) active λ-wall terms are relu² of ~linear coeffs
→ contribute PSD (∇g∇gᵀ) curvature, can't break PD. So it's interior-vs-boundary, not the relu² itself.
**Natural-units margin implemented** (`np_damping_wall.py`): `margin=<float>` is now a `-r`/`--wall`
token (default `NP_DAMPING_MARGIN`=0.005), applied to the **minimum of the argument polynomial**
`minQ = λ2_Y − relu(−B)²/(4λ6)` (B=λ4+λ2_Y³/3λ∞²), which *unifies* the small-b endpoint (Q(0)=λ2_Y) and
the interior vertex into one coefficient-unit quantity — instead of the old scale-carrying discriminant
`relu²(−cubic)−bound` (that mismatch is why an additive margin meant different things per term). One cushion,
same meaning for turn-on & interior. Verified in numpy: **margin=0 ≡ the old feasible set exactly**
(minQ<0 ⟺ old disc>0, all 3 terms), and it reproduces the baseline's binding terms; C¹ in B → EDM-friendly.
tanh_2 and smallb=0 paths unchanged. margin>0 stricter, =0 physical edge, <0 controlled anti-damping.
**Relaunched after a (postponed) submit82 reboot scare:** killed all fits cleanly (ceph outputs survive;
only in-progress cov/sat + C's descent lost), then relaunched priors cov/sat + C_dl2frozen0 (clean, no `_t0`
this time) + the margin scan (5 pts) + wall+δλ2=0. submit82 = **768 cores**; the load is dominated by
*our own* nnlojet production (~229 cores) + others, ~60 cores headroom → capped fits at `THREADS=8` so ~6 coexist.
Container launch gotcha: `singularity run <img> wrapper.sh` fails `FATAL: permission denied` if the wrapper
isn't +x (it tries to *exec* it); use `singularity exec <img> bash wrapper.sh` (and dangerouslyDisableSandbox
for the setuid starter). Watchers armed; results pending.

### 2026-07-17 — α_s IS sensitive to the NP treatment (σ + ptll GOF); the decisive result
Pulled the cov-bearing rows (blinded common α_s offset):

| run | θ(α_s) | σ(α_s) | EDM | ptll sat-p | full χ²/ndf |
|---|---|---|---|---|---|
| walled (physical) | −8.413 | 0.501 | 5e-12 | **3.5%** | 727/770 |
| no wall A (λ2<0) | −7.583 | 0.538 | 1e-10 | 0.8% | 734/770 |
| **C (best NLL 355)** | **−10.115** | 0.675 | 3e-12 | **43.4%** | 710/770 |

- α_s central spans −7.6→−10.1 across treatments = **~2.5–3σ** (σ≈0.5–0.68). NP treatment
  is a DOMINANT systematic on the central value, not cosmetic.
- **ptll GOF splits them the wrong way**: physical=3.5% (poor), C=43% (good) → data prefer
  the unphysical description (via the F_eff-blowup ringing that binning launders). Real ptll tension.
- Good news: within the **capped/physical band** α_s is stable — func-bound F_eff≤1.2 gave
  θ=−8.46 ≈ walled −8.41. Only the full blowup (C) shifts it. So any *reasonable* constraint → ~−8.4.

### 2026-07-17 — C's TMD blowup is ENTIRELY δλ2<0 (Luca's hypothesis, confirmed)
Evaluated F_eff(bT,Y) at C (λ2=1.10, λ4=−0.61) with δλ2=−0.011 vs 0:
`maxF: Y=1.5→1.0, Y=2→10, Y=2.5→985, Y=5→22026 (=e¹⁰ cap)` for δλ2=C; **maxF=1.000 at ALL Y
for δλ2=0**. Mechanism: `λ2_Y=λ2+δλ2·Y²`; C sits at the damping edge at Y=0 (λ4=−0.61 puts
B²=0.027 just under the 0.044 bound), and δλ2<0 pulls λ2_Y down → discriminant flips at **Y≈1.8**.
δλ2 is degenerate (ρ(λ2,δλ2)≈−1) *and* an approximate rapidity-dependence term → strong drop
candidate. `260717_2D_C_dl2frozen0` (δλ2=0, λ seeded at C, unwalled) tests whether removing it
lands physical at low NLL — running.

### 2026-07-17 — function-bound wall fixed (sum→max); it RAILS against the cap
- Grid-SUM penalty (~400 relu²) made a ~400× too-stiff barrier → the first run crawled to
  maxiter at 378.6 (non-converged, edm<0). **Fixed to one hinge per function on the PEAK**:
  `relu²(max_b γ_ν − tcs) + relu²(max_{b,Y} F_eff − (1+ttmd))`. Recompiled.
- Seeded-from-walled (ttmd0.2) converges, **maxF=1.2000 exactly** → pins on the cap; nll 361.9
  (< walled 363.5, the looser tcs=0.2 CS freedom). **The fit rails against whatever cap you set**
  → a magnitude cap gives a *threshold-determined* answer (no interior data preference upward).
- Scan `ttmd 0/0.1/0.4/1.0` all **seeded from walled** → they can only probe F_eff≤2.0, which is
  ≪ C's F_eff~985, so they map the *near-physical* band only (α_s ~−8.4, flat). To map the slide
  toward C, must **seed from C** (queued).

### 2026-07-17 — Gaussian priors as the alternative constraint
Built into the param model (`priors=1 prior_sigmas=lambda2=…,…`; prior MEAN defaults to the card
λ_central — `param_model.py:781-792`; runs natively through `fitterSCETlibNP --modelArgs`). Soft →
restoring gradient everywhere → interior MAP (no railing, unlike the wall). BUT to hold physicality
against the Δχ²≈16.6 pull needs an **informative** σ (est. ≲0.3: prior cost of the full move ≈
1.75/σ² must beat ~16); σ=0.5 is too loose → drifts unphysical. Same fundamental tension as the wall,
just smooth. And **no theory σ exists yet** → the width is unpinned; must scan σ and report the
α_s(σ) dependence. σ=0.5 fit running as the loose anchor.

### 2026-07-17 — tooling: fit_summary_table `--spec` + fixes; fitterSCETlibNP named walls
- `scripts/fit_summary_table.py`: added `--spec` (YAML/JSON `{name: dir}` / `[{name,dir}]`) for
  DESCRIPTIVE row labels; fixed `is_fit_pass` to key on **`noFit`** not `ext is None` (seeded fits
  — C, funcbound — were being dropped); canonical-chain dedup in named mode (one name → one row);
  `pdflatex` FileNotFoundError caught (writes .tex, warns); math-aware `tex_escape` (`$…$` verbatim,
  so `$F_{eff}$`/`$\Delta\lambda_2$` subscript properly); HDF5 locking off + hdf5plugin so it reads
  outside/inside container and skips in-progress fits cleanly. Spec: `studies/np-wall-local-minima/runs.yaml`.
- `workflows/fitterSCETlibNP.py`: `--wall` now takes a NAME (`WALLS` registry): `--wall damping …`
  (default, backward-compat) or `--wall funcbound tcs=0.2 ttmd=0.2`. hessian/saturated inherit it.

### 2026-07-16 — function-bound wall (NPFunctionBound): grid-sum run failed to converge; fixed sum→max
Wrote `np_function_bound.py` (`NPFunctionBound`): caps the ACTUAL form factors on a
(bT,Y) grid — `γ_ν ≤ tcs` (0.2), `F_eff ≤ 1+ttmd` (1.2), thresholds on the -r line.
Separate class; `NPDampingWall` untouched. Also added `--native-points` to
`sigma_gen_at_lambda.py` (plot the requested axis on its native grid, no rebin;
other axes integrated over the specified edges — reveals the laundered σ(qT) ringing).
- **First run FAILED to converge** (grid-SUM penalty, default start, strength 5,
  `260716_2D_funcbound_tcs0p2_ttmd0p2`): 1000 iters / 1.8 h, `nllvalreduced=378.6`
  (worse than all basins), `jac[0]=1.13`≠0, `edmval=−90.6` (non-PD). Penalty=0 at the
  endpoint, `maxF=1.200` exactly → pinned on the `F_eff≤1.2` boundary (wall IS binding).
- **Cause:** penalty summed relu² over ~400 grid points → ~400× too-stiff barrier →
  glacial crawl along the boundary, never reached the feasible physical basin (walled
  363.5 at F_eff=1.0 is allowed under the bound).
- **FIX (Luca's point):** one hinge per function on the PEAK, `relu²(max_grid f − thr)`
  — 2 terms not ~400. Recompiled. Rerun pending (default + seed-from-walled).
- **Physics to expect:** `F_eff≤1.2` is LOOSER than the damping wall (≈F_eff≤1), so its
  converged min should sit BELOW 363.5, in ~[355, 363.5] — the price of mild anti-damping.
- **bT-blowup → σ(qT):** confirmed the un-damped large-bT F_eff tail Bessel-transforms to
  high-qT ringing + negative σ(qT), worst at HIGH Y (because λ2_Y=λ2+δλ2·Y² with δλ2<0
  strengthens the anti-damping with Y); clean under |Y|≤2.5. This is out-of-acceptance,
  coupling to the fit only via gen→reco migration — the crux of the Y_MAX=5-vs-2.5 debate.

### 2026-07-16 — Step 1: wall-condition readout at the walled postfit
Evaluated every tanh_6/tanh_6 wall requirement at the **walled** postfit
(`260702_2D_l6nu0p01_l60p01/fitresults_t0.hdf5`) with current constants
(`eps=1e-3`, `margin=5e-3`, `Y_MAX=5`, τ=5 → ×22026). Only **two** of ~14
requirements are active, both *barely*:
- **CS small-b λ2_ν = 0.00431**, just under the 5e-3 margin → Δnll ≈ 0.011 (soft-wall equilibrium parked at the margin knee, by design).
- **TMD interior discriminant at Y=5**: c²=0.00291 vs bound 0.00241 → tipped over, Δnll ≈ 0.0055.
- At **Y=0 and Y=2.5 (inside |Y|≤2.5 acceptance) the TMD interior has wide slack** (bound 0.059, 0.045 ≫ c²). The Y=5 binding is driven by δλ2<0 shrinking λ2_Y to 0.0067 there.
Total active penalty ≈ 0.016 (matches walled 363.473 − wall-off-at-that-point 363.457).
**Takeaway:** the wall touches our best fit only via (a) the CS margin and (b) the
Y=5 (out-of-acceptance) interior — exactly the two conservative pieces flagged for
softening. Small penalty ≠ loose wall (tension is Δχ²≈16.6, below).

### 2026-07-16 — form-factor check at C (B2 postfit)
Evaluated the *actual* forms (btgrid_tf, b*=identity) at C over the fit range:
- CS γ_ν^NP **anti-damps for b ≲ 1.4 GeV⁻¹** (driven by λ2_ν=−0.36) — the high-weight small-b region.
- TMD F_eff **anti-damps at Y=2 (b≈2.7–3.8) and Y=2.5 (b≈2.4–4.3)** — *inside* the acceptance.
So C genuinely anti-damps in the measured region (form-factor level; σ(qT)-level not yet checked). No margin can rescue C: the violations sit in the **interior-discriminant** terms, which the margin does not touch (margin only relaxes the leading/small-b `wall()` terms).

### 2026-07-16 — B1/B2: proof of local minimum + a deeper unphysical basin (C)
Seeded the unwalled fit from the FULL walled postfit via `--externalPostfit`
(restores λ AND all nuisances; earlier Test 2 only seeded the 9 λ via
`xparam_default`, left 3746 nuisances at 0 → not a real seed, slid back to A).
- **B1** (`--noFit`, `260716_2D_evalAtWalled_nowall`): wall-off data-NLL *at* the walled point = **363.457** < 366.9. Direct proof (no penalty-subtraction) that the unwalled minima are local, not global.
- **B2** (fit, `260716_2D_seedWalledFull_nowall`): descended to a **third, deeper, UNPHYSICAL** basin **C**: nll **355.18**, λ2=+1.10, λ4=−0.61, λ2_ν=−0.36, edm 3e-12.
**Landscape (wall-off data-NLL; lower = better data fit):** C 355.18 (unphysical) < physical 363.46 < A 366.9 (unphysical). Deeper ⇒ more unphysical. **Tension physical↔C: Δχ² ≈ 2×(363.457−355.18) ≈ 16.6.**
**Correction:** a mid-session read ("physical is the global optimum") was REFUTED by B2 — the global optimum (deepest found) is unphysical.

### 2026-07-16 — the original puzzle + first tests
Two fits, 2D Z real data (`260701_Z_2D`, ptll×yll), tanh_6/tanh_6, freeze
lambda_inf/lambda_inf_nu/lambda6/lambda6_nu:
- **walled** (`260702_2D_l6nu0p01_l60p01`, `-r NPDampingWall … --regularizationStrength 5`): nll 363.47, λ2=+0.165, edm 5e-12.
- **nowall** (`260702_2D_l6nu0p01_l60p01_nowall`): nll 367.39, λ2=−0.498, edm 1.3e-12. (nowall start also had `xparam_default=…,lambda4_nu=0.01` — a config diff beyond the wall.)
Puzzle: walled nll < nowall nll (constrained beats free). Cause: `nllvalreduced`
*includes* the regularizer penalty (`fitter.py:2118-2119`), but the walled penalty
is tiny (~0.016), so 363.47 ≈ pure data-NLL at a physical point → the comparison is
genuine and the free fit is worse.
- **Test 1** (nowall, matched start, drop lambda4_nu=0.01; `…_matchedStartingPoint`): nll 366.91, λ2=−0.476 — same basin as nowall (the lambda4_nu seed only nudged it to a marginally different local point).
- **Test 2** (nowall, seed λ=walled via xparam_default only; `…_seedWalled`): nll 366.91 — slid away from the walled λ because nuisances were left at 0 (recipe flaw; superseded by B1/B2).

---

## Findings

1. **The unwalled SCETlib-NP fit is stuck in a local minimum.** A lower point of the same (wall-off) objective exists — the walled solution evaluates to 363.457 < the 366.9 the free fits converge to (edm≈0). — (evidence: B1, `260716_2D_evalAtWalled_nowall`)
2. **The likelihood is multimodal and its global optimum is UNPHYSICAL.** ≥3 basins: C 355.18 (unphysical) < physical 363.46 < A 366.9 (unphysical). — (evidence: B2, `260716_2D_seedWalledFull_nowall`)
3. **The wall enforces physicality against a real data pull, it does NOT find the global optimum.** Tension physical↔deepest-unphysical Δχ² ≈ 16.6. — (evidence: B1/B2)
4. **`nllvalreduced` includes the regularizer penalty** (`fitter.py:2109-2124`); at the walled tune the penalty is ~0.016, so its value is essentially the pure data-NLL at a physical point.
5. **The margin (`NP_DAMPING_MARGIN`, currently 5e-3) is a *positive cushion* (stricter), global to all `wall()` leading/small-b terms, and does NOT touch the interior discriminant or λ∞ floors.** No margin value (even a negative tolerance) can make C satisfy the wall, because C's violations are in the interior terms. — (evidence: per-term penalty breakdown at C)
6. **The wall is a sufficient-not-necessary (conservative) physicality condition:** damping ∀b, evaluated to Y_MAX=5 (vs |Y|≤2.5 acceptance). At the walled best fit its only binding is the CS margin + the Y=5 (out-of-acceptance) interior. — (evidence: Step 1 table)
7. **C genuinely anti-damps inside the acceptance** (CS b≲1.4 GeV⁻¹; TMD Y≈2–2.5, b≈2.4–4.3) — not merely tripping conservative strictness. σ(qT)-level confirmation still pending. — (evidence: btgrid_tf form-factor eval)
8. **α_s is NP-treatment-dominated.** Pull −7.6 (A) / −8.4 (physical/capped) / −10.1 (C) — spread ~2.5–3σ vs σ(α_s)≈0.5–0.68. The NP treatment is the dominant systematic on the central value; it is NOT decoupled/cosmetic. — (evidence: cov passes, 2026-07-17 table)
9. **The ptll GOF prefers the *unphysical* fit:** physical walled ptll-sat p=3.5% (poor) vs C p=43% (good). A real ptll data–model tension the NP resolves unphysically (laundered ringing). — (evidence: saturated passes)
10. **C's TMD blowup is entirely δλ2<0.** δλ2=0 → F_eff damps at all Y (same λ2=1.10, λ4=−0.61); onset Y≈1.8; mechanism λ2_Y=λ2+δλ2·Y² tipping the discriminant. δλ2 is degenerate (ρ(λ2,δλ2)≈−1) + an approximate term → drop candidate. — (evidence: btgrid_tf eval, 2026-07-17)
11. **The function-bound wall rails against its cap** (postfit maxF=1+ttmd exactly); it does not attract to physical, so a magnitude cap gives a threshold-determined answer. Within any reasonable cap (F_eff≤1–2) α_s is stable ~−8.4; C needs F_eff~10³. — (evidence: 260716 funcboundMax_seedWalled, scan)
12. **Gaussian priors** are built into the param model (`priors=1 prior_sigmas=…`, mean=λ_central, `param_model.py:394,781`) → soft interior MAP (no railing), but need an informative σ (≲0.3) to hold physical vs the 16.6 pull; no theory σ exists → scan the width, report the α_s(σ) dependence. — (reference)

---

## Step 1 table (wall requirements @ walled postfit, tanh_6/tanh_6, eps=1e-3, margin=5e-3, Y_MAX=5, ×22026)

postfit λ: `λ2=+0.1651 λ4=−0.0180 δλ2=−0.0063 λ2_ν=+0.00431 λ4_ν=+0.0336 λ6=λ6_ν=0.010 λ∞=1 λ∞_ν=2`

| side | requirement | value | condition | status | Δnll |
|---|---|---|---|---|---|
| CS  | λ∞_ν floor | 2.000 | >1e-3 | ok | 0 |
| CS  | leading λ6_ν | 0.010 | ≥margin | ok (+0.005) | 0 |
| CS  | interior disc. | λ4_ν=+0.034 | λ4_ν≥0 or disc | ok | 0 |
| CS  | **small-b λ2_ν** | **0.00431** | ≥0.005 | **⚠ at margin** | **0.011** |
| TMD | λ∞ floor | 1.000 | >1e-3 | ok | 0 |
| TMD | interior Y=0 | c²=0.0024 vs 0.0594 | c²≤bound | ok (wide) | 0 |
| TMD | interior Y=2.5 | c²=0.0027 vs 0.0452 | c²≤bound | ok (wide) | 0 |
| TMD | **interior Y=5** | **c²=0.00291 vs 0.00241** | c²≤bound | **⚠ tipped** | **0.0055** |
| TMD | small-b/leading (all Y) | λ2_Y≥0.0067, λ6=0.010 | ≥margin | ok | 0 |

(Y=2.5 shown for insight; the code only evaluates Y=0 and Y_MAX=5.)

---

## Open questions

1. **Does removing δλ2 resolve it?** `260717_2D_C_dl2frozen0`: with δλ2=0, does the fit land PHYSICAL, at low NLL, with a GOOD ptll sat-p (like C's 43%, not walled's 3.5%)? If yes → clean resolution (drop the approximate δλ2). If it just drives λ4<−0.65 (regains all-Y anti-damping) → pathology shifted. **The key test running now.**
2. *Why* does the physical model fit ptll at only 3.5% while unphysical C reaches 43%? Is C's advantage genuine or the laundered-ringing artifact? (finer qT/Y binning should shrink it if artifact.)
3. Is the α_s shift (−8.4↔−10.1) driven by the same unphysical freedom? Map it with a **C-seeded** func-bound cap scan (walled-seeded can't — caps ≤2.0 ≪ C's 985).
4. Answered at the form-factor level (Finding 7,10): the anti-damping is real in-acceptance and driven by δλ2 (TMD) / λ2_ν<0 (CS). Still open: the *binned* σ(qT)<0 confirmation, and whether a σ(qT)≥0 wall is cheap enough per-iteration (needs differential σ in the forward pass).
5. Does the priors σ-scan (0.1–1.0) give a smooth α_s(σ), and where does it cross from physical to unphysical?

---

## Reproduce

- Read any fitresult λ/nll/edm: `python3` with `wums.ioutils.pickle_load_h5py(f['results'])` (needs `hdf5plugin`; runs on login node, no container). See in-session scripts.
- B1/B2 recipe (wall off, seed full walled solution):
  `rabbit_fit.py <260701_Z_2D card> --paramModel …SCETlibNPParamModel np_model_nu_fit=tanh_6 np_model_fit=tanh_6 xparam_default=lambda6_nu=0.01,lambda6=0.01 --freezeParameters lambda_inf lambda_inf_nu lambda6 lambda6_nu --externalPostfit 260702_2D_l6nu0p01_l60p01/fitresults_t0.hdf5 [--noFit --noPostfitProfileBB] -t 0 --noHessian`
- Run dirs: `/ceph/…/alphaS/260716_2D_{evalAtWalled,seedWalledFull}_nowall/`, `…/260716_2D_l6nu0p01_l60p01_nowall_{matchedStartingPoint,seedWalled}/`.
