---
title: Lattice CS-kernel constraints (ASWZ 2024) in the alpha_s fit
slug: lattice-cs-kernel
status: active
created: 2026-09-23
updated: 2026-10-09
---

# Lattice CS-kernel constraints (ASWZ 2024) — logbook

**Goal:** decide whether, and how, the lattice CS kernel of Avkhadiev–Shanahan–Wagman–Zhao
([arXiv:2402.06725](https://arxiv.org/abs/2402.06725)) can constrain SCETlib's NP CS kernel
in our alpha_s fit — **Option A** (their continuum parametrization + fitted values) vs
**Option B** (fit our SCETlib kernel directly to the per-ensemble lattice data, with
lattice-spacing nuisances as in [arXiv:2510.26489](https://arxiv.org/abs/2510.26489)).
Done when we have (i) a convention map proving the lattice object == our SCETlib object
(or the exact conversion), (ii) a recommendation A/B/reference-only with the reason, and
(iii) if feasible, a prototype constraint on the λ_ν that can enter the fit.

---

## START HERE (status as of 2026-10-09)

> Summary: [SUMMARY.pdf](SUMMARY.pdf) (covers 2026-10-09).

- **Nominal = LATFROZ_V3, the LatticeCSTerm default since WRemnants 3841ee42 (pushed).** The exact ASWZ χ² is fitted with
  the Z data. The lattice-side kernel is frozen at α_s(m_Z) = 0.1168 with TNPs = 0, so the lattice constrains only λ2_ν and
  λ4_ν. One n_f row (`Jnf`, V3 convention; the conservative choice), no b_T window. The table-based term is retired
  (1b3732bb). The Gaussian-card producers survive only as study scripts; the cards stay on ceph for provenance.
- **Results:** vs the no-lattice XWSTIFF Δα_s +0.245σ_XW (σ ×1.05); vs XL4ZSTIFF −0.013σ. n_f systematic ≈ 0.01σ.
  Z–lattice tension PG 13.5/2 dof, 3.2σ, a shape tension (see the NP-function figures).
- **Open:** toys for the PG and saturated p-values (on hold, Luca); the theorist email (Q1, Q3a; Luca sends); λ∞_ν rows
  (deferred); the AN's lattice section.
- **Running:** nothing.

## Earlier state (2026-09-24 → 2026-10-06, kept for history)

> **PAUSED 2026-10-06 ~13:30 (Luca):** node memory overloaded, everything stopped, reboot pending. Our gated fits were
> SIGKILLed (exit 137) between about 12:05 and 13:20: T8C5, T8P5, TCC1 and LATCHI5. T8B has no exit line. The cause:
> mem_gate serialises only load PEAKS, so about 5 jobs at ~320 GB steady state stacked up, plus other users' jobs.
> Snapshots are on ceph. /tmp (gate locks, scratchpad) will NOT survive the reboot. Restart plan: at most 2 of our big
> jobs alive at once, in priority order; see the walled-multistart-census study log, 2026-10-06.

> **Lattice CS-kernel constraints can enter the α_s fit, and with them α_s is stable.** On card A (old AD cache
> `pdf62_corrgrid_260827`), the ASWZ lattice constraint moves α_s by ≤0.7σ against the old walled fits (walled lattice fit:
> +0.01σ vs its like-for-like cold reference). It removes the CS kernel as an α_s uncertainty source (gammaNu impact
> 0.5–0.8 → 0.05 ×1e-3). The data pay Δχ²_data ≈ +4–5 for it.

**What was established, in order**
1. **Same object.** The lattice γ_q (MSbar, μ=2 GeV) is exactly SCETlib's γ̃_ζ = ½·Gamma_nu. The only scheme mismatch is
   n_f=5 (ours) vs 4 (lattice), a coherent ≤0.03 offset carried as a systematic. The α_s dependence of the perturbative
   kernel is negligible against the lattice errors. Recipe and validated evaluator: `260923-conventions-map`.
2. **The data.** Use the three per-ensemble files with their covariances plus a free k1·a/b_T. The "continuum" csv is just
   raw − 0.2136·a/b_T with stat-only errors. We reproduce the paper's fit (χ², c0 = 0.032, k1 = 0.213), once a
   d_n power-of-a_s bug on our side is fixed (the earlier "c0 factor 2" was that bug, now retracted). Only the quoted σ's differ. `260923-lattice-data-refit`.
3. **Option B chosen:** fit OUR kernel to the lattice data. Option A (their c0/B_NP form) is a different NP form, is
   would need re-mapping, and has quoted σ's that we can't reproduce.
   - Our tanh_2 kernel + k1 fits well (χ² 6.7/18). λ∞_ν is unconstrained and tanh_6 is not needed.
   - With λ4_ν fixed at 0: **λ2_ν = 0.135 ± 0.031** (stat+syst, λ∞_ν=2), at a cost of Δχ²=1.9 vs free λ4_ν.
   - It agrees with the Tackmann/AN tune and with the card anchor, and is 5.5–14σ from all old Z postfits.
   - `260923-scetlib-kernel-fit`.
4. **Why the constraint matters.** At the physical point the Z data see only one NP combination (ρ(λ2_ν,Λ2) ≈ −0.985),
   and Z alone is LOOSER on λ2_ν than the lattice. Splitting mll 60–120 does not break this. A lattice prior does,
   also pins the TMD Λ2 through the degeneracy, and decouples α_s from the NP sector. `260923-qsplit-fisher`
   (gen-level Fisher, stat only).
5. **Real-data fits** (λ4_ν frozen at 0 + 1D λ2_ν external term replacing the CS prior; walled and unwalled; table below):
   - The CS kernel becomes physical: λ2_ν 0.06–0.09, which is 1.4–2.3σ below the lattice.
   - A CS-only constraint relocates the unphysical behaviour into the TMD (unwalled optimum: TMD λ2 = −0.078,
     anti-damping), as in 260911. The wall keeps both physical for ΔNLL 1.2.
   - Cold vs warm matters: the cold unwalled fit stopped 6.9 above the warm one. `260923-lattice-fits`.
6. **Cache validity.** The AD-cache prediction is invalid where the large-b damping reaches ~0 (CS λ4_ν ≲ −0.002; TMD
   Λ4 + L2³/3 ≲ 0). Minimisers converge onto these artefacts: the cold unwalled lattice fit, and the old reference
   CCCOLDSELF. `260924-unwcold-xsec-validity`.

**Caveats.**
- The lattice covariance is assumed block-diagonal across ensembles (author Q4).
- λ∞_ν is frozen at 2 and λ4_ν at 0.
- The fits use the old cache/card A and rabbit 2a59246 (checked bit-identical to the references' f77f10e).
- No reference fit was validity-checked (Luca's call).
- The ptll projection stays poor in all fits (p ≲ 0.1%).

- **Next action:**
  - Luca reruns the lattice fits (walled + warm-unwalled, same design) on the new |Y|≤3.5 cache (`pdf62_y35_260921`) once
    its chain works. Recipe and cards: `260923-lattice-fits` (scripts/run_fit_l4zero.sh, the injector in `--l4zero` mode).
  - Then fold in the theorist's answers.
- **Blocking on:** the new cache chain (another session), and the theorist's reply (email 2026-09-23; priority Q2
  uncertainty method, Q4 cross-ensemble correlations; Q1 "c0 factor 2" was OUR bug, so send the theorist a correction).
- **At close:** run `knowledge-curator`. Candidate notes: the lattice↔SCETlib matching recipe; cache validity (the large-b
  damping rule); update np_parametrization_constraints.md §10 (the old "don't use lattice cov" warning concerns the Tackmann
  translation, not the ASWZ per-ensemble data); the b*/μ0 statement there; Q-split AD cache build costs; scetlib_ad
  fitresults store λ as θ, which fitresult_lambdas.py mis-reads. Remove the worktree
  `/home/submit/lavezzo/alphaS/WRemnants-scetlib-np-param-model` when no longer needed.

Web: https://submit.mit.edu/~lavezzo/alphaS/studies/#lattice-cs-kernel

---

## Key results

### Summary table: lattice vs no-lattice fits on card A (2026-09-24)
Reference for all Δ = CCWALLCOLDR (old walled, cold). Δα_s in units of σ(α_s) of CCWALLCOLDR (1.290e-3), blinded differences only.
The CCWALLWARM Δα_s is derived from the two new-vs-old numbers (±0.01σ rounding).

| fit | wall | lattice | start (seed) | NLL | Δχ²_data | Δα_s | σ(α_s) [1e-3] | full sat. p | proj. ptll p | λ2_ν | TMD | valid xsec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CCWALLCOLDR | ✓ | – | cold (resumed CCWALLCOLD) | 372.67 | 0 | 0 | 1.290 | 80.2% | 0.095% | 0.007 (on wall) | physical | not checked |
| CCWALLWARM(PF) | ✓ | – | warm: PR174 unwalled postfit | 371.44 | +0.3 | −0.26σ | 1.085 | 81.9% | 0.15% | 0.005 (on wall) | physical, on margin | not checked |
| LATL4ZWALLCOLD | ✓ | ✓ | cold | 376.72 | +5.0 | +0.01σ | 1.158 | 77.3%* | 0.009% | 0.063 (−2.3σ lat) | physical, on wall | ✓ |
| LATL4ZUNWWARM | – | ✓ | warm: LATL4ZWALLCOLD minimum | 375.53 | +4.0 | +0.34σ | 1.163 | 76.5%* | 0.02% | 0.091 (−1.4σ lat) | unphysical (λ2 −0.078) | ✓ |
| LATL4ZUNWCOLD | – | ✓ | cold | 382.43 | +19.8 | −1.87σ | 1.062 | 63.2%* | sub-fit failed | 0.107 | invalid | ✗ (artefact) |
| CCKRYLOVWARM | – | – | warm: PR174 unwalled postfit | 365.49 | −8.4 | −1.04σ | 1.217 | – | 3.8% | −0.091 (anti-damp) | physical | not checked |
| CCCOLDSELF | – | – | cold (self-restart of CCKRYLOV) | 379.20 | −1.7 | −4.90σ | 0.690 | – | – | −0.083 (anti-damp) | λ4 −0.018 | ✗ (artefact) |

\* lattice term removed (−2·lext). Loss comparisons: walled NLL includes the wall penalty and lattice NLL includes lext; Δχ²_data compares the data term only.
(evidence: 260923-lattice-fits/LOGBOOK.md Result §1–2; 260924-unwcold-xsec-validity)

![Lattice vs our kernel, λ4_ν = 0 vs free](260923-scetlib-kernel-fit/kernel_space_l4zero.png)
*Our SCETlib kernel fitted to the ASWZ per-ensemble data (points shown with k̂1·a/b_T subtracted). λ4_ν = 0 (used in the
fits) vs free. Block-diagonal lattice covariance assumed.*

---


## Lattice-term systematics: what, why, impact (consolidated 2026-10-07)

The term: r_i = pert_i(α_s) + ½γ_ν^NP(b_i; λ2_ν, λ4_ν) + k1·a_i/b_i − y_i, χ²_lat = rᵀC⁻¹r, with k1 profiled analytically.
Statistics alone fix λ2_ν to ±0.039 and λ4_ν to ±0.0034 (ρ −0.89). Each systematic is a shift δ of the 21 points, added as
δδᵀ to C, which is identical to a profiled N(0,1) nuisance. Numbers come from
[261006-lattice-chi2-in-fit](261006-lattice-chi2-in-fit/LOGBOOK.md) (`phase2_newton.json`).

| systematic | what | why | shift (λ2_ν, λ4_ν) / σ_stat | status |
|---|---|---|---|---|
| n_f scheme | redo the lattice fit with our pert kernel matched n_f = 5 → 4 at μ = 1 GeV (the pure-n_f = 4 alternative agrees to 3 %; one kept) | the lattice is an n_f = 4 theory, our SCETlib kernel is n_f = 5; the n_f5 − n_f4 gap is +0.030 at μ = 2 GeV and −0.012 when matched at 1 GeV. Its size and sign depend on the matching scale, which is the ambiguity | −0.47, +0.23 | kept |
| b_T window | redo the fit without the points at b_T < 0.2 fm | there b_T is only a few lattice spacings, so discretisation artefacts beyond the modelled k1·a/b_T term are largest; this tests sensitivity to unmodelled artefacts | +0.19, −0.14 | kept |
| pert scale | our perturbative kernel with its b-space boundary scale μ0 → 2μ0 or ½μ0 (½ is larger), as a direct point shift (≤ 0.53 σ_lat per point) | the NP part is whatever our N3LL perturbative kernel misses relative to the lattice, so missing higher orders in the pert kernel are absorbed into λ unless they are given an uncertainty. This is needed once α_s is live, otherwise the lattice would constrain α_s with no theory error on γ_pert | +0.70 (λ2_ν), +0.38 (λ4_ν), in quadrature | kept (new) |
| k-form | k2·a²/b_T² instead of k1·a/b_T | — | −0.97, +0.66 | **removed**: the k1·a/b_T form is the theorists' prescription (Luca, 2026-10-06) |

Total σ(λ2_ν): 0.039 stat → 0.044 with n_f + b_T window → 0.051 with all three kept.

**Impact on `alphaS`** (Newton steps from LATCHI8, α_s frozen, Δ vs NOMSTIFF in σ_NOM): stat-only −0.127, +n_f −0.124,
+b_T −0.126, n_f + b_T −0.123, **n_f + b_T + pert −0.117**, old set with k-form −0.111. σ(`alphaS`) ratio is 0.981 in every
case. **So the whole systematic choice spans 0.016σ in `alphaS`.** Removing the k-form from NOMSTIFF's own 1D card would move
it by +0.031σ.

**α_s in the lattice term.** pert_i is SCETlib's N3LL n_f = 5 kernel at μ = 2 GeV: a boundary term at
μ0 = ((b0/b_T)⁴ + 1 GeV⁴)^¼ plus the running to 2 GeV, all driven by α_s(m_Z).
- *Frozen:* a table at 0.118.
- *Live:* pert_i(0.118) + (α_s − 0.118)·∂pert_i/∂α_s(m_Z). The derivative ranges −3.0 … +2.7 and changes sign with b_T;
  it is linear to 2e-3 σ_lat over ±0.002. α_s is taken from the param model's physical (unblinded-internal) frame.
- Effect: a +0.07σ pull on `alphaS` (predicted +0.074, measured +0.069).
- Net for the full treatment (LATLIVE8Y) is **−0.04σ_NOM**.

## Log

### 2026-10-09
- Luca: wait on toys. All commits pushed (WRemnants 3841ee42, WRemnantsHelpers 1c5d93a). Summary refresh dispatched.
- WRemnants 1b3732bb retires the table-based term: lattice_cs_chi2, its lattice_aswz_inputs.npz/.json, and its test.
  3841ee42 makes LATFROZ_V3 the LatticeCSTerm default (bitwise equal to the V3 fit's term, test 38/38) and adds a hard
  error when tau is missing. Both pushed 2026-10-09. The Gaussian-card producers live only in study scripts; the cards on ceph
  are kept, because existing fitresults reference them (paths in the session report: 260923_lattice_fits/cards/, MSHT20 and
  260722/260723 card dirs).
- Luca: estimate the n_f systematic's size and how much the row form matters with real fits: LATFROZ_V3D
  (syst=direct_nf) and V3N (syst=none), delegated to [261008-latfroz-nf-variants](261008-latfroz-nf-variants/LOGBOOK.md).
- n_f row fits DONE ([261008-latfroz-nf-variants](261008-latfroz-nf-variants/LOGBOOK.md) Result §6): the n_f systematic is
  negligible for α_s in either form. Total impact V3 − V3N = +0.0096σ_NOM, row form V3D − V3 = −0.0028σ_NOM, and its
  σ(α_s) contribution ≤ 0.05σ_NOM in quadrature. PG stays 3.2–3.3σ. The J-mapped default is kept.
- Luca: preconditioning added to fitterAD.sh and to the toy recipe (WRemnantsHelpers 1c5d93a). No rabbit change; the main
  fit pays the Hessian.

### 2026-10-08
- NP-function figures DONE ([261008-np-function-figures](261008-np-function-figures/LOGBOOK.md)): γ_ζ vs lattice points
  (lattice only / joint / NOMSTIFF / Z only), full b_T range, NP functions with MAP22, and the (λ2_ν, λ4_ν) plane. The
  tension is a shape tension: the joint kernel has weaker damping below 0.54 fm and stronger beyond 0.63 fm. The Z data
  fix the product of the CS and TMD damping, and the lattice moves damping from the TMD side to the CS side.
- Summary refreshed in the new LaTeX format (SUMMARY.tex/.pdf) as the format test for Luca.
- LATFROZ done ([261008-latfroz-nf-variants](261008-latfroz-nf-variants/LOGBOOK.md)). The frozen lattice-side kernel moves α_s
  by −0.026 to −0.035σ vs LATB8. The n_f conventions span 0.009σ (worker recommends V3, the full n_f = 4 kernel with
  coupling from m_b). The data–lattice tension is Δχ²_lat ≈ 9.2–9.5 for 2 dof (p ≈ 1 %) in every convention. The
  mechanism section (load vs fit time) is in that task logbook.
- **Correction (orchestrator): NOMSTIFF is NOT a no-lattice fit.** It has the old 1D Gaussian card lattice term with
  λ4_ν = 0. The no-lattice references are XWSTIFF (λ4_ν free) and XL4ZSTIFF (λ4_ν = 0), both in
  `/ceph/.../260930_stiff_wall_fits/`. The orchestrator computed (blinded, σ of the reference; scratch script dalpha.py):
  - vs XWSTIFF: LATFROZ V1/V2/V3 +0.235/+0.244/+0.245σ, LATB8 +0.273σ, NOMSTIFF +0.394σ; σ ratios 1.04–1.07.
  - vs XL4ZSTIFF: V3 −0.013σ, LATB8 +0.012σ, NOMSTIFF +0.124σ; σ ratios 0.96–0.99.
  XWSTIFF and XL4ZSTIFF both sit on the λ2_ν ≥ 0 wall face (θ = −1.5000, physical λ2_ν = 0). The lattice moves λ2_ν off
  that face to ~0.038, so σ(α_s) grows relative to XWSTIFF. Caveat: without lattice and with λ4_ν free there is a second
  walled minimum (C / CMR1B), so XWSTIFF as a reference needs that caveat. The tension worker's "no Z-only reference fit
  exists" is wrong: XWSTIFF is that reference.
- Luca: go for LATFROZ, testing all three n_f conventions. Delegated as
  [261008-latfroz-nf-variants](261008-latfroz-nf-variants/LOGBOOK.md): lattice-side kernel frozen at α_s(m_Z) = 0.1168 and
  nominal TNPs, so only (λ2_ν, λ4_ν) are constrained by the lattice; no window systematic; one Jnf row in three
  conventions (V1 identified at 1 GeV; V2 old table, decoupled at m_b with n_f=4 from 1 GeV; V3 `nfmatch` = m_b). Three
  fits warm from LATB8, relu² wall, no saturated test.
- **Luca: the study SUMMARY must explain the mechanism**: what the lattice term computes once at load vs at every fit
  evaluation, where in the code, and the three n_f conventions. The LATFROZ worker writes that section; the summarizer
  brief must require it.
- `scetlib_tf_native.py` stale NP model ids (261007-lattice-term-design, Open questions): fixed in draft MR
  https://gitlab.cern.ch/scetlib/contrib/scetlib-cms/-/merge_requests/18 (CS and effective-model ids now match the C++, raises
  on unknown ids; tested per node against the build to ≤1e-12). NB: the module's own σ-level test already fails on the
  current build, independent of this fix. Not used by our fits.
- Physics review of the native term (physics-reviewer, read-only): APPROVE WITH FIXES. The machinery and LATB8's numbers
  are confirmed. Not yet supported is "systematics negligible for α_s": the window and n_f rows act only along NP
  directions, the data's own α_s dependence (δγ, ASWZ Eq. 13) is not modelled, and the "−0.020σ RGE" row mixes in the old
  table's expansion error. Also flagged: a blinding inference path (the same Newton row at two α_s frames), a stale study
  record, and the §10 knowledge warning. Findings are in the session report; summary held until resolved.
- Luca's decision: **drop the b_T window systematic** (`Jbt`). Nominal `syst=Jnf`, all 21 points, no artefact term, no
  dropped-small-b cross-check.
- Proposed (awaiting Luca): new nominal LATFROZ. Lattice-side kernel frozen at the lattice's α_s(m_Z) = 0.1168, so the
  lattice constrains NPs only and δγ needs no modelling. Jnf row recomputed with m_b-decoupled α_s^(4) (shift −0.042
  vs −0.0092). Warm from LATB8; compared with NOMSTIFF and LATB8.
- Draft MR opened: https://gitlab.cern.ch/scetlib/contrib/scetlib-cms/-/merge_requests/17 (gamma-nu-points → autodiff-sigmaul; merges cleanly).
- SATB8 (unseeded) and SATB8SA (seeded) had both already exited 0 overnight (00:42 / 00:49), so there was nothing to stop.
  Nothing of this study is running.
- Pushed (Luca: push everything):
  - scetlib-cms `gamma-nu-points` (069c326, 6ab371a) to gitlab origin, no MR yet;
  - WRemnants b14f84f4 + 4e7e481e to `scetlib-ad-param-model`;
  - rabbit `saturated-subfit-seed` (9bfe73f) to the luca fork, no PR.
- Luca wants toys to recompute the p-values, especially the saturated one. Open design question: generation at a walled
  postfit, and the lattice pseudo-data.
- Native-term follow-ups DONE: composite support (WRemnants 4e7e481e), SATCHK passes. Seeding test: rabbit 9bfe73f, branch
  `saturated-subfit-seed`, `--saturatedSeed`.
  - **RETRACTION (orchestrator):** "LATB8's Z data+BB ≈ +1.9 NLL worse than NOMSTIFF" was wrong (a units mix). LATB8's Z
    data+BB is ≈ 1.46 NLL BETTER (χ²: 706.90 vs 709.82).
  - The full-saturated equality (753.35 vs 753.23) is a coincidence, not like-for-like: each fit carries its own
    lattice term in its one leg (5.05 vs ≈ 9.48 in χ²).
  - Projected ptll for LATB8: q = 78.40/39, p = 0.019 %. The tension is unchanged (LATL4ZY35WALLWARM: 80.73/39).
  - Seeding (scope `all`) halves the sub-fit time (to 1e-6: 8 598 s vs 17 511 s; restarts 6 vs 15) and reaches the same
    minimum. The projection-only scope is rejected (degenerate with lumi-type nuisances).

### 2026-10-07
- SATB8 is slow (iteration 100 after 2 h). The saturated sub-fit is a full re-minimisation at τ = 8, with no
  τ-continuation, showing the crawl/restart staircase. The node is also overloaded (load ~600 / 384 cores).
  - Luca: test (b), seeding the sub-fit from a previous projected-saturated result. If that works, build (a), a general
    τ-continuation inside rabbit's sub-fit.
  - Delegated to the native-term worker (SATB8S vs SATB8).
- Composite support: WRemnants 4e7e481e; SATCHK passes. **Full saturated test: LATB8 753.35/777 (p 72.2 %) vs NOMSTIFF
  753.23/778 (p 73.2 %)**, so the Z goodness of fit is essentially identical.
  - The orchestrator's earlier estimate (LATB8's data+BB ≈ +1.9 NLL worse, from subtracting a lattice term evaluated at
    α_s = 0.118 out of the lumped data_bb) is likely wrong; the worker is asked to explain.
  - The projected-ptll test (SATB8) is running. The worker was resumed after its session ended.
- Y-shape (Luca): the Y² term is the leading term of an ln x expansion (AN: an "effective flavour-averaged model";
  ΔΛ2 = +0.125 in the AN, ours ≈ −0.008). The only active wall is at its |Y| = 2.5 edge.
  - Proposal: a Newton slope d`alphaS`/dc at LATB8 (all evaluated at the physical point; no unphysical extrapolation
    quoted) + a registry check + a Y⁴ term (analytic in F_eff) with the wall checking min over |Y| ≤ 2.5.
  - Awaiting Luca's go.
- Wall faces (orchestrator, from the fitresult covariances): NOMSTIFF and LATB8 are both pinned on exactly ONE face,
  L2(|Y|=2.5) = 0 (to 1e-6). Every other condition is slack:
  - LATB8: λ2_ν 1.2σ, λ4_ν 2.1σ, L2(0) 1.1σ, B 2.7σ;
  - NOMSTIFF: λ2_ν 2.8σ, L2(0) 0.6σ, B 3.2σ.
  The CS side is on no wall in either fit.
- Composite support for LatticeCSTerm + the saturated test on LATB8: the native-term worker was resumed (Luca approved).
- [261007-lattice-term-native](261007-lattice-term-native/LOGBOOK.md) DONE: option B built and validated.
  - Commits (nothing pushed): scetlib-cms 069c326 + 6ab371a (branch gamma-nu-points); WRemnants b14f84f4
    (`lattice_cs_term.LatticeCSTerm`).
  - **LATB8 vs NOMSTIFF −0.113σ_NOM, σ ratio 0.972**, λ4_ν 0.0111 ± 0.0054, EDM 5e-17. vs LATFULL8 −0.027σ (Newton
    predicted −0.026).
  - Impacts: analytic vs exact RGE −0.020σ (largest); b_T window +0.0004σ; native n_f +0.0003σ. So both theorist
    questions are low-stakes for α_s.
  - Native n_f shift −0.0092, 4.6× smaller than the old m_b-decoupled −0.042.
  - ASWZ: MSbar at μ = 2 GeV, n_f = 4, matching at α_s(2 GeV) = 0.293. The data's own α_s dependence is NOT modelled
    (question Q3, impact unknown).
  - Open: the term refuses CompositeParamModel, so there is no saturated test with it yet.
- LATFULL8 DONE (phase 3: pert fully live = α_s + γ_ν/cusp TNPs; systematics Jnf+Jbt; λ4_ν free; subset cache).
  - **Δ`alphaS` −0.09σ_NOM vs NOMSTIFF**; σ ratio 0.979; EDM 1.2e-17.
  - vs LATLIVE8Y −0.044σ: TNP coupling −0.055, dropping μ0 +0.011.
  - λ2_ν 0.036 ± 0.030, λ4_ν +0.0098 ± 0.0056.
  - CS TNPs barely pulled (θ_γν 0.44 → 0.31), no added constraint.
  - Caveat: it still uses the exact-RGE table, ≈ −0.004σ vs the cache's analytic RGE (design-task estimate); superseded by
    LATB.
  - WRemnants 2a8825be + 3ef3efb9 pushed (agreed order).
- Luca approved the design, minus the double-counting guards.
  - Same kernel as the cache (analytic RGE).
  - SCETlib-native n_f alternative.
  - b_T window kept for now.
  - Theorist questions to be compiled with their impacts after a first implementation; nothing sent.
  - Build delegated as [261007-lattice-term-native](261007-lattice-term-native/LOGBOOK.md): scetlib-cms branch (not
    pushed), WRemnants commit (not pushed), validation, an LATB chain on the subset cache, an impact table, and draft
    questions.
- [261007-lattice-term-design](261007-lattice-term-design/LOGBOOK.md) DONE (scoping + proposal).
  - SCETlib has no Python-callable CS kernel, but `ad::gamma_nu_resummed` is already in the clad kernel, so only a thin
    entry point is needed. A prototype works: it matches qT::Gamma_nu to 5e-16, the Hessian matches FD, 13 ms for 21
    points.
  - **Finding:** the shipped table is the EXACT-RGE kernel, while the fit's cache.conf uses the ANALYTIC RGE. Difference
    ≤ 1.9e-3 (≤ 0.019 σ_lat); ∂/∂α_s differs by 8.5 % on the plateau; live pull ×0.946 (≈ −0.004σ). This confirms Luca's
    objection to shipped tables; option B removes the mismatch by construction.
  - Proposal: ~3.5–4 days of work plus ~1 day of fits. Decisions for Luca: accept the analytic-RGE kernel (= the cache's),
    the SCETlib-native n_f alternative, the b_T-window default, and the interface (`-r` now).
- Luca rejects shipped theory tables. Direction: option B, the CS kernel at the lattice points computed by SCETlib at
  every step, via an `_XsecTFBase` subclass (exact second order, like the cross section). No double counting: one
  likelihood per dataset, shared parameters; guards are needed against the Gaussian lattice cards and λ_ν priors.
  Scoping + full lattice-handling proposal delegated as [261007-lattice-term-design](261007-lattice-term-design/LOGBOOK.md).
  The current plugin stays a validation reference; do NOT promote it to nominal.
- Luca: try `direct_nf` (point-wise pert(n_f 5 matched at 1 GeV) − pert(n_f 5)) instead of the J-mapped `Jnf`. The J-mapped
  form is fixed Δλ shifts linearised at the lattice best fit; only θ_nf is profiled. The worker adds a Newton comparison,
  and a real LATFULL `direct_nf` chain only if `alphaS` moves ≥ 0.01σ or the λs move > 0.3σ. Default unchanged until Luca
  decides.
- Luca questions the pert-scale (μ0 × 2, ½) systematic. Missing higher orders in SCETlib are handled by the TNPs
  (resumTNP_gamma_nu, gamma_cusp, …), not by scale variations. **Orchestrator view:** the consistent treatment is to make
  the lattice term TNP-live (pert_i depending on the CS-kernel TNPs, like α_s-live), so one set of nuisances moves both the
  Z prediction and the lattice comparison; then drop the μ0 variation.
  - Size: at NOMSTIFF's postfit TNPs the points shift by ≤ 0.0044 (≤ 0.05 σ_lat), vs ≤ 0.53 σ_lat for μ0 × ½. So the μ0
    variation is far larger than the analysis' own MHO treatment of the same kernel.
  - b_T window: our own robustness choice (260923-lattice-data-refit §5: the b_T < 0.2 fm points mainly calibrate the
    k1·a/b_T artefact, consistent with the theorist's remark that they "add nothing beyond PT"). It was not a theorist
    recommendation; Luca will ask.
  - **Decided (Luca):** pert_i becomes fully live: it depends on α_s AND the CS-kernel TNPs, linearised. The μ0 variation
    is dropped from the default (opt-in only). The b_T window stays until the theorist answers. Worker phase 3: implement,
    test, fit LATFULL.
- LATLIVE8Y DONE: exact lattice χ², α_s-live, systematics Jnf+Jbt+pert, λ4_ν free, subset cache.
  - **Δ`alphaS` −0.04σ_NOM vs NOMSTIFF; σ ratio 0.985; EDM 2.1e-17.**
  - vs LATCHI8 (frozen): +0.069σ, predicted +0.074. The λ4_ν float (−0.11σ) and the live α_s pull (+0.07σ) largely cancel.
  - λ2_ν 0.034 ± 0.030, λ4_ν +0.0080 ± 0.0053 (interior). Same single active face.
  - Blinding: the term uses the param model's offset-applied α_s (difference 0); nothing α_s-dependent is published.
  - The pert-scale systematic is the largest lattice systematic (+0.70 σ_stat on λ2_ν).
  - Plugin is WRemnants 44f8a5c0, already pushed by the orchestrator on 10-06.
  - Open: adopt it as the nominal (Luca; physics review first); retire the k-form Gaussian cards.
- Overnight, chain4 stopped at 18:59 with "Asimov closure FAILED". That was a script bug: the wrong result key
  ('results_asimov' vs 'results_toy1'). The orchestrator re-ran the check correctly: **PASS**, all θ back to 0 within 2.7e-7,
  EDM 1.4e-13. LATLIVE never ran. The worker was resumed to fix the script and launch the LATLIVE chain on the |Y| ≤ 2.5
  subset cache, with a subset-vs-full NLL cross-check at LATCHI8's point.

### 2026-10-06
- **Decision (Luca):** remove the k-form systematic. The k1·a/b_T form is the theorists' prescription, not our choice. The
  lattice systematics become n_f scheme + b_T window. Applied in the exact-χ² plugin, and the worker redoes closure, Newton
  and LATLIVE with it. The existing 1D/2D Gaussian cards (incl. NOMSTIFF's) still carry the k-form; they are being replaced
  by the exact term, and the worker gives the Newton size of the change for NOMSTIFF.
- Luca: the theorist did not ask for our three lattice systematics (n_f scheme, k-form, b_T window); what does dropping
  them do? Known so far: they widen the constraint by about 1.5× (2D: σ(λ2_ν) 0.038 stat vs 0.057 stat+syst; 1D l4zero
  0.020 vs 0.031), and the k-form dominates. Exact Δχ²_lat at NOMSTIFF is 17.1 stat-only vs 7.2 stat+syst. The worker
  adds cache-free Newton estimates of Δ`alphaS` per systematic, before the live fit.
- [261006-lattice-chi2-in-fit](261006-lattice-chi2-in-fit/LOGBOOK.md) DONE: exact lattice χ² in the fit (LATCHI8: τ 5 → 8,
  λ4_ν floating, TMD priors pinned).
  - Δ`alphaS` −0.11σ_NOM, σ ratio 0.98, EDM 3e-17.
  - λ4_ν = +0.0073 ± 0.0045 (interior, not on the wall), λ2_ν = 0.030 ± 0.030. Same single active face as NOMSTIFF.
  - The exact χ²_lat sits 6.9 above the lattice-only minimum (NOMSTIFF's point: 7.2).
  - Caveat: the perturbative table is frozen at α_s = 0.118, which drops a lattice pull on α_s of ≈ +0.08σ. The `live`
    option exists but has not been run.
  - The Gaussian-2D comparison (−0.07σ) comes from an uncertified T8C5 snapshot only.
  - Open for Luca: α_s-live variant; moving the plugin into WRemnants; λ4_ν float as nominal; lattice systematics as
    nuisances.
- 261006-lattice-chi2-in-fit interim: plugin `LatticeCSChi2` built, adding ½χ²_lat as a second `-r` regularizer.
  - k1 is profiled analytically; the systematics enter as a covariance through the CS Jacobian.
  - Closure is exact against 260923-scetlib-kernel-fit: χ² 6.713/18, λ2_ν 0.18443, λ4_ν −0.00592.
  - Exact vs Gaussian Δχ²: W − NOM is +17.8 exact vs +549 Gaussian. Near NOMSTIFF the exact term pulls λ4_ν up 1.6×
    harder.
  - Newton step: Δ`alphaS` −0.09σ, λ4_ν +0.0036.
  - **Open physics choice:** the perturbative kernel is frozen at α_s 0.118. Making it live would add a lattice pull on
    α_s of ~+0.11σ at NOMSTIFF.
  - LATCHI5 (τ 5) is running; LATCHI8 (τ 8 + Hessian) is chained, gated at 400 GB.
- Reopened. Luca wants the EXACT lattice χ² inside the α_s fit, i.e. a simultaneous fit of the ASWZ points with the Z data,
  instead of the Gaussian summary. The summary is about 30× too steep away from the lattice best fit
  (walled-multistart-census T8).
- Delegated as [261006-lattice-chi2-in-fit](261006-lattice-chi2-in-fit/LOGBOOK.md):
  - a rabbit regularizer plugin adding ½χ²_lat, with k1 profiled and the systematics as a covariance;
  - closure against 260923-scetlib-kernel-fit;
  - one nominal fit with λ4_ν floating, τ 5 → 8, TMD priors pinned, compared with NOMSTIFF.


- 2026-09-30 — **Authors confirm the coherent-shift bootstrap is a bug** (email exchange, Luca). Their quoted σ(c0) = 0.012 and σ(k1) = 0.08 are overestimated by about 2×. The covariance-based values from [260929-aswz-notebook](260929-aswz-notebook/LOGBOOK.md) are the right ones: σ(c0) = 0.006 and σ(k1) = 0.066. **Our constraint is unaffected**: it is built from the covariance and already uses the correct errors, so no rerun is needed. Sherpa question: the central values are right; only a group that uses the paper's quoted σ gets a band that is about 2× too wide, which is conservative. The authors may want to tell that group, and consider an erratum.

- 2026-09-30 — Theorist asked whether another group putting their CS-kernel results into Sherpa conflicts with our use. Assessment: no conflict, since we use the published per-ensemble data in our own SCETlib parametrization. Two things to keep in mind. (1) If a Sherpa prediction that uses the ASWZ kernel is ever compared with or combined with our result, the two share the lattice input and are not independent. (2) The pitfalls we hit also apply to the other group: the d_n / a_s power reading behind the factor-2 in c0, n_f=4 vs 5, the a/b_T term, the coherent-shift uncertainty rule (σ(c0) 0.012 vs 0.006), and the fact that the NP part is defined relative to a specific perturbative kernel (order, scheme, b*). α_s circularity is negligible (∂γ/∂α_s ≈ −3, i.e. 1/25 σ_lat per 0.001).

- 2026-09-29 — [260928-lattice-wall-warm-y35](260928-lattice-wall-warm-y35/LOGBOOK.md) done: warm-from-no-lattice lands on the cold walled lattice minimum (ΔNLL 0.03, Δα_s +0.04σ), unchanged on the new cache; projected ptll still 80.7/39. The walled lattice minimum looks unique.

- 2026-09-28 — launched [260928-lattice-wall-warm-y35](260928-lattice-wall-warm-y35/LOGBOOK.md): lattice + wall (λ4_ν = 0) on the |Y|≤3.5 cache, warm from the no-lattice walled Y35ZWALLWARM (Luca). Tests walled-minimum uniqueness and the new cache in one go.

### 2026-09-24 — ptll-tension localisation done → [260924-ptll-tension-localization](260924-ptll-tension-localization/LOGBOOK.md)
- The ptll projected-saturated tension of the walled lattice fit is at ptll < 15 GeV and common to all yll bands.
  yll also has its own tension, and α_s moves ~2–3.5σ depending on which marginal is freed.

### 2026-09-23
- Study opened. Theorist's statements (email, via Luca): kernel is MSbar, μ = 2 GeV, n_f = 4
  (2+1+1 physical-mass ensembles), α_s(2 GeV) = 0.293 used internally; γ_q = 2 dln f/dln ζ
  ≡ SCETlib γ̃_ζ ≡ Collins K̃ ≡ −2D (ART23); b_T ∈ ~[0.1, 0.9] fm; below 0.2 fm lattice adds
  nothing beyond PT; no data beyond 0.9 fm. Continuum extrapolation tried with k1·a/b_T and
  k2·(a/b_T)^2; mild AIC preference for one term only.
- First look at the files (orchestrator): the "continuum" csv (21 rows) is **not** an
  independent continuum dataset — it is the per-ensemble points (L32 a=0.15, L48 a=0.12,
  L64 a=0.09 fm) shifted by a constant k1·a/b_T with k1 ≈ 0.2136, carrying the **raw
  per-point stat errors and no covariance** (e.g. L32 b=0.15: 0.1417 → −0.0719, σ 0.1079
  unchanged). So it drops the k1 uncertainty and all correlations. To be confirmed by T2.
- Dispatched: `260923-conventions-map` (is the lattice γ_q the same object as SCETlib's full
  γ̃_ζ, and how do we evaluate ours at μ=2 GeV, n_f=4?) and `260923-lattice-data-refit`
  (reproduce their continuum extrapolation from the per-ensemble data).
- Luca: the AN's lattice numbers (Cridge–Marinelli–Tackmann 2506.13874) came from a simple
  study that isn't robust, and its methods were never published. It is a precedent only, not
  a recipe. This study is meant to be the first careful version. Conventions worker
  redirected: build the recipe from first principles (ASWZ + SCETlib source).
- lattice-data-refit DONE: the continuum file is confirmed to be raw − 0.213649·a/b_T with
  stat-only diagonal errors. The paper's (c0, k1) fit reproduces from the per-ensemble data
  with full covariance, but only if c0 multiplies −b_T·b* instead of −2·b_T·b* as the
  paper's equations read, a factor-2 ambiguity to ask the authors about. B_NP is
  unconstrained by the data, and the continuum file underestimates σ(c0) by 16%. So for
  Option B, use the per-ensemble data plus k1. (Evidence:
  [260923-lattice-data-refit/LOGBOOK.md](260923-lattice-data-refit/LOGBOOK.md))
- conventions-map DONE: the lattice γ_q is the same object as SCETlib γ̃_ζ = ½·Gamma_nu, with
  no blocker found. The only mismatch is the flavour scheme: n_f=5 (ours) vs n_f=4 (lattice),
  a coherent ≤0.03 offset whose sign depends on μ. The perturbative kernel is flat for
  b_T ≳ 0.3 fm (μ0 floor at 1 GeV), so the lattice window probes the NP tanh.
  ∂γ/∂α_s(mZ) ≈ −3, i.e. ~1/25 of a lattice σ per 0.001, so the α_s–λ correlation is weak.
  The lattice's α_s(2 GeV)=0.293 ↔ α_s(mZ)=0.1168. `our_cs_kernel.py` is validated against
  SCETlib's Gamma_nu to 5e-11. (Evidence:
  [260923-conventions-map/LOGBOOK.md](260923-conventions-map/LOGBOOK.md))
- Orchestrator checked the c0 factor-2 claim against the arXiv source (2402.06725 main.tex).
  Eqs. L314–324 are the ART23 (Moos:2023yfa) form verbatim, γ = −2D_res(b*) − 2·b_T·b*·[c0+…],
  and the SV19 and ART23 c0 they compare to (L358) are in that same convention. The Fisher
  σ(c0) of a (c0, k1) linear fit to the per-ensemble files with block-diagonal covariance
  depends only on the design, not on D_res. It comes out 0.0060 with the literal −2·c0·b·b*
  and 0.0120 with −c0·b·b*; the paper quotes 0.012. The central value is also about 2×
  (0.015–0.018 literal vs 0.032). Caveat: σ(k1) = 0.066 vs the paper's 0.08, so their error
  procedure is not exactly this Hessian and the "exactly 2" is not airtight. Still a question
  for the authors, but now a well-posed one.
- Luca emailed the theorist (2026-09-23). Questions, with equation numbers from the v1 PDF:
  (1) c0 normalization in Eq. (7) vs (6); (2) how the uncertainties are computed (σ(k1) 0.066
  vs 0.08; (c0,k1,k2) σ(c0) +43% vs the paper's ≲10%); (3) is k1=0.2136 in the continuum file
  their unrounded best fit; (4) correlations across ensembles; (5) how the points move with
  α_s; (6) the 0.72 fm point at a=0.09 (Table I says b_T/a ≤ 7); (7) BLNY g2. Priority is 1, 2, 4.
  Note: k1=0.2136 is exactly constant over all 21 points (spread 2e-16), so the continuum file
  is a single k1·a/b_T subtraction, as the paper describes near Eq. (9).
- Luca: go on T3. Dispatched `260923-scetlib-kernel-fit`: fit our tanh kernel (n_f=5, fit μ0/b*)
  to the per-ensemble data + k1/k2, and compare to our real-data postfit λ_ν and to the
  Tackmann/Cridge values. Context passed on: np-wall-local-minima showed the CS lattice prior
  is load-bearing in the real-data fits (with no prior, λ2_ν → −0.499), so the size and centre
  of this constraint matter for α_s.
- Luca corrected the T3 brief (worker told): fit model = our kernel(λ) + k1·a/b_T + k2·(a/b_T)²,
  fit jointly. Float λ∞_ν and consider tanh_6. Compare against the LATEST scetlib_ad real-data fits
  (card A, alphas-scan-discontinuity: CCKRYLOVWARM main, CCCOLDSELF second, CCWALL* walled), not
  the August np-wall registry, and show the wall/minimum spread. Reuse np_function_plots.py /
  fitresult_lambdas.py, which are on branch `scetlib-np-param-model`, not the checked-out
  `scetlib-ad-param-model`.
- scetlib-kernel-fit DONE. Our kernel + k1·a/b_T fits the per-ensemble data well
  (χ² 6.7/18), with k1 matching ASWZ. λ∞_ν is unconstrained (flat above ~1.1) and tanh_6 is
  not needed (AIC +1.6). In kernel space the fit agrees with the Tackmann/AN tune (0.9σ) and
  with the AD card anchor (λ2_ν=0.15, 1.0σ). Every current scetlib_ad real-data postfit is
  5.5–14σ away: the unwalled minima anti-damp (λ2_ν≈−0.09), and the walled ones sit at ~0 or
  saturate. Recommends the exact lattice χ² as a `-r` regularizer with k1 profiled. (Evidence:
  [260923-scetlib-kernel-fit/LOGBOOK.md](260923-scetlib-kernel-fit/LOGBOOK.md))
  ![kernel space](260923-scetlib-kernel-fit/kernel_space_comparison.png)
  *Points are raw − k̂1·a/b_T. Lattice covariance assumed block-diagonal. Postfit bands ignore CS–TMD correlations.*
- **Orchestrator correction to that task:** its "+2e-3 α_s, ~2σ" estimate (a slope from a
  different card, extrapolated) is superseded by a direct measurement it did not know about.
  [`scetlib-ad-param-model/260911-lattice-constraints`](../scetlib-ad-param-model/260911-lattice-constraints/LOGBOOK.md)
  already ran an in-fit lattice (Tackmann) prior on the AD model. Results: λ2_ν −0.058 → +0.126;
  α_s moves +0.005σ vs the free arm, i.e. within a basin α_s barely depends on the NP tune
  (260911-crossarm). Cost Δχ²_data = +11.7 (~3σ). The CS-only constraint pushed the violation
  into the TMD side (λ2 → −0.138, anti-damping). My brief omitted that task.

- Discussion with Luca on uncertainties:
  - The Z-fit λ_ν Hessian ellipses are computed correctly (Δχ²=2.30 from rabbit's marginal cov), but they are
    not valid CIs for the true kernel. The likelihood is far from Gaussian: the old 260911 arm paid only
    Δχ²_data=11.7 to reach the lattice region, because the TMD λ re-adjust. On top of that the model is
    misspecified. Luca: no profile scan needed.
  - Why the Z fit is tighter than the lattice: γ^NP is multiplied by ln(Q²/μ0²)≈9, so the stats are huge,
    but that precision holds only within the model. At fixed Q, λ2_ν and Λ2 are degenerate at O(b²).
  - Idea (Luca): split mll 60–120 into 3–5 Q bins to break the degeneracy (reco side is fine). J comes from
    `SCETlibADParamModel.core.values_and_jacobian`, but the current cache has one Q bin ([60,120]) and took
    ~2 days to build. Dispatched `260923-qsplit-cache-cost` (estimate only, no build).
- qsplit-cache-cost DONE: a 5-Q-window cache (375 bins: 5 Q × 5 |Y| × 15 qT to 40 GeV) takes
  ~0.5 h (≤1.5 h) on ≤384 cores **without PDF eigenvectors**, and ~10–15 h with them. Cost follows
  the Breit–Wigner, so 5 windows cost 1.14× one window; it sits almost entirely at qT<2 GeV. Early
  hint from the probe Jacobians: (∂σ/∂λ2_ν)/(∂σ/∂Λ2) goes 1.98→2.20 across the windows, ±5% around
  the peak, so the Q lever arm may be modest. (Evidence:
  [260923-qsplit-cache-cost/LOGBOOK.md](260923-qsplit-cache-cost/LOGBOOK.md))
- Luca: go. Dispatched `260923-qsplit-fisher`: build grid A (5 windows, no eigenvectors, into
  `scetlib_ad_caches/qsplit_260923/`), then a gen-level stat-only Fisher forecast of Q-integrated vs 3 vs 5 windows.
- qsplit-fisher DONE (build took 12 min): **the mll split does NOT break the λ2_ν–Λ2 degeneracy**
  (ρ −0.998→−0.991). It only helps by separating the NP flat direction from α_s and the TNPs when the NP
  sector is loose. With the fit's NP priors or a lattice prior it adds little to nothing. (Evidence:
  [260923-qsplit-fisher/LOGBOOK.md](260923-qsplit-fisher/LOGBOOK.md))
- **Retraction (orchestrator):** I told Luca that the Z data are intrinsically much tighter on λ2_ν than the
  lattice (0.006 vs 0.04, "like ART23 vs lattice"). The forecast at the physical anchor gives
  σ(λ2_ν)=0.25 (NP free) or 0.087 (with the card's NP priors) at gen level, stat only, i.e. LOOSER than the
  lattice's 0.038. The 0.006 is the curvature at the unphysical unwalled minimum (λ2_ν≈−0.09, reco, finer
  bins, PDF eigenvectors). Not like-for-like, but the "Z is tighter" claim is unsupported at the physical point.
- Luca: the anti-damping (unwalled) minima give an unphysical CS kernel (γ^NP > 0, growing with b_T), so their λ, σ
  and correlations are not a CS-kernel measurement, and comparing the forecast with them is meaningless. There is no
  physical-region data fit on the new model yet. Dropped the proposed CCKRYLOVWARM Fisher check.
- Fisher, lattice CS prior (σ 0.038/0.0033, ρ −0.88, TMD free): σ(λ2_ν) 0.033, σ(Λ2) 0.062 (vs 0.167 with the
  current priors: through the degeneracy the lattice also pins the TMD), ρ(α_s, λ2_ν) 0.44→0.11, σ(α_s) −11%
  (fixed PDF). Q binning on top of it: 1–3%. So a lattice constraint beats mll bins, and with it the bins are redundant.
  (260923-qsplit-fisher/forecast_anchor.out)
- Luca: go on the lattice-constrained real-data fits, walled and unwalled, COLD start; seed tests later. Decided:
  the ASWZ 2×2 (λ∞_ν=2, k1 marginalised, + syst cov) enters as a rabbit external term (full cov, in θ).
  It REPLACES the diagonal CS priors (`prior_sigmas=lambda2_nu=nan,lambda4_nu=nan`), no params.py change.
  λ∞_ν stays frozen at 2; its choice is a later systematic. Dispatched `260923-lattice-fits`.
- Luca (mid-dispatch): use the NEW cache `pdf62_y35_260921` (|Y|≤3.5, pin scetlib-ad-2da973d) and the latest SCETlib.
  Another agent is building its consumer chain (corr → histmaker → card) now. The worker is told to prepare but NOT
  launch until that card exists. The lattice-free cold reference arms must also exist on the new card.
- Luca reverted: use the OLD setup (card A, cache pdf62_corrgrid_260827, same build as alphas-scan-discontinuity) for
  easy comparison and no waiting. CCCOLDSELF / CCWALLCOLDR are the references again. New-cache version deferred.
- lattice-fits PAUSED. The production cache is unusable for λ4_ν ≲ −0.002 (O(1) low-qT bin-to-bin oscillation, σ<0 near
  −0.007), and the lattice prefers −0.006. Physics read (orchestrator): tanh_2 with λ4_ν<0 flips γ^NP to anti-damping beyond
  b_T≈1.1 fm, i.e. the negative-λ4 trap on the CS side. Unwalled arm held. Walled arm LATWALLCOLD running at risk; the
  wall-vs-lattice balance is at λ4_ν≈−0.0015. Cards + injector done and checked (stat+syst: ±0.0567/0.0040, ρ −0.911).
  Proposed to Luca: freeze λ4_ν=0 + a 1D lattice λ2_ν term refit at λ4_ν=0 for BOTH arms, then kill and relaunch cold.
  Awaiting a decision. (Evidence: [260923-lattice-fits/LOGBOOK.md](260923-lattice-fits/LOGBOOK.md))
- Luca: kill the fits (a fit is meaningless if the xsec can't be evaluated where it goes). LATWALLCOLD kill requested,
  with the last λ state recorded first. Requested a refit of the lattice data at λ4_ν=0 fixed (λ∞_ν=2, k1) in
  260923-scetlib-kernel-fit, to compare with the free-λ4_ν fit. Note: all reference fits have λ4_ν in the safe region
  (≥ −0.0006). The lattice term is the first thing pulling λ4_ν negative.
- LATWALLCOLD killed at iteration 294, not converged (loss 1131 vs ref 373, still falling). At the kill: λ2_ν railed on the wall
  floor (0.0056, ~3σ below the lattice), λ4_ν −0.0001, TMD λ4 −0.107. Not a result. ~~The direction matches the data's
  known pull away from the lattice.~~ (retracted 2026-09-24: mid-descent, carries no information) (260923-lattice-fits/logs/snapshot_LATWALLCOLD_at_kill.txt)
- Lattice refit at λ4_ν=0 (λ∞_ν=2, k1): **λ2_ν = 0.1345 ± 0.020 (stat) ± 0.024 (syst) = ± 0.031**, χ² 8.59/19.
  Freezing λ4_ν costs Δχ²=1.87 (1.4σ), so the lattice accepts λ4_ν=0. The band matches the free fit below ~0.6 fm.
  Card anchor 0.15 is 0.5σ away; λ2_ν=0 is 4.3σ. Use this direct 1D refit, not the Gaussian conditional (0.108, biased low).
  ([260923-scetlib-kernel-fit/LOGBOOK.md](260923-scetlib-kernel-fit/LOGBOOK.md) §6)
  ![λ4_ν=0 vs free](260923-scetlib-kernel-fit/kernel_space_l4zero.png)
- Luca approved: relaunch both arms cold (LATL4ZUNWCOLD, LATL4ZWALLCOLD) on card A / the old setup, with λ4_ν frozen at 0,
  a 1D external term on λ2_ν = 0.1345 ± 0.031 (stat+syst), and `prior_sigmas=lambda2_nu=nan`. Runs sequentially if memory is tight.

### 2026-09-24
- **Retraction (orchestrator):** on 09-23 I told Luca that the killed LATWALLCOLD's λ2_ν on the wall "suggests the data and the
  lattice genuinely disagree". Wrong: the worker showed cold card-A fits take ~1700 iterations, and at iteration 294 it was
  mid-descent. Its λ state carries no information.
- LATL4ZUNWCOLD (lattice λ4_ν=0 + 1D λ2_ν, unwalled, cold) DONE: EDM 6.3e-7, 1486 iterations, saturated p=62.5%.
  λ2_ν = 0.107 ± 0.025 (pull −0.87 vs lattice): **the CS kernel is physical and lattice-compatible**. The cost is
  Δχ²_data = +18 vs CCCOLDSELF, +28 vs the global main minimum CCKRYLOVWARM, and +20 vs CCWALLCOLDR. **TMD goes
  unphysical at forward rapidity:** λ2 0.052, δλ2 −0.013, so L2(|Y|=2.5) = −0.031 < 0 (the 260911 relocation pattern
  again). Δα_s = −0.9σ vs CCKRYLOVWARM, −1.9σ vs CCWALLCOLDR, +5.7σ vs CCCOLDSELF. σ(α_s) 0.00106.
  LATL4ZWALLCOLD launched 04:33. (Evidence: [260923-lattice-fits/logs/analyze_unw.log](260923-lattice-fits/logs/analyze_unw.log))
- LATL4ZWALLCOLD main fit converged (08:26 check): loss **376.72** (incl. lattice + wall), EDM 3.7e-17, 685 iterations,
  saturated p=73%. From the snapshot: λ2_ν 0.063 (−2.3σ vs lattice), TMD λ2 0.028, δλ2 −0.0037 (L2(2.5)≈+0.005, on the
  wall), λ4 0.087, lumi −1.46. **Its loss is 5.7 below the UNWALLED lattice fit (382.4), so the cold unwalled fit is a local
  minimum**, and its λ2_ν / Δχ² / TMD-negative read is not its configuration's optimum. Proposed: a warm unwalled rerun from
  the walled minimum. The ptll-projection saturated sub-fit is still running; the fitresult (Δχ²_data, Δα_s) comes after it.
- Luca approved LATL4ZUNWWARM (unwalled, seeded from the LATL4ZWALLCOLD minimum), launched 08:31. The worker builds a comparison
  table vs the old refs (CCWALLCOLDR, CCWALLWARM, CCKRYLOVWARM, CCCOLDSELF): GoF full/projected, impacts, Δα_s in σ.
- LATL4ZUNWCOLD's ptll-projection sub-fit failed (trust-krylov "bad approximation", EDM 0.026, no restart in sub-fits).
  Dispatched `260924-unwcold-xsec-validity`, on this fit only: (1) the stored postfit yields (needs no α_s); (2) model
  evaluation at anchor α_s (blinding-safe), plus a TMD L2 scan to find the validity edge.
- 09:15 — LATL4ZUNWWARM main fit converged: 17 iterations / 8 min, EDM 3.6e-16, **loss 375.53** (< walled 376.72 < cold 382.43),
  saturated p 75%. λ2_ν 0.091 (−1.4σ vs lattice). **TMD fully anti-damping: λ2 −0.078, L2 = −0.078 / −0.138 at |Y| = 0 / 2.5**
  (the 260911 relocation, stronger). Walled is only +1.2 in loss (incl. penalty), so the data barely resist physicality
  (Δ(2NLL) ≲ 2.4). The validity worker was retargeted to prioritise this point. The projection sub-fits are still running for both.
- unwcold-xsec-validity DONE (α_s held at the anchor, gen level):
  - **LATL4ZUNWCOLD is invalid.** It sits on an AD-cache artefact in the most forward bin: 2<|Y|<2.5, qT<0.5 GeV has σ at 0.52× its smooth
    value, with a see-saw up to 1.5 GeV. TMD λ4 is parked on a ~1e-4-wide kink at 0, 0.003 in L2 from σ<0.
  - **LATL4ZUNWWARM is numerically valid** (smooth, AD=FD) but physically anti-damps (f^NP up to 1.11 at small b).
  - **Validity is set by the TMD large-b damping, Λ4 + L2³/3 > 0 with margin, not by the sign of L2.**
  - **LATL4ZWALLCOLD is clean.**
  - **The old reference CCCOLDSELF is itself in an artefact region** (TMD λ4 −0.018), so comparisons against it are suspect.
    CCKRYLOVWARM and CCWALLCOLDR are unchecked.
  (Evidence: [260924-unwcold-xsec-validity/LOGBOOK.md](260924-unwcold-xsec-validity/LOGBOOK.md))
- **Walled + lattice vs old walled:** same basin. Δχ²_data +5.0 (vs CCWALLCOLDR) / +4.7 (vs CCWALLWARM). **Δα_s +0.01σ / +0.32σ.**
  σ(α_s) 1.158e-3 (old: 1.290 / 1.085). Full saturated p 77% (lattice term removed). Projected ptll 80.9/39, p=0.009%
  (old: 72.3 / 70.4 on 39). λ2_ν comes off the wall: 0.005 → 0.063 ± 0.023. Impacts: gammaNu (trad) 0.52–0.82 → 0.05; Feff 0.78.
  Caveat: the new fits ran on rabbit 2a59246 (the shared tree was switched by another session on 09-23 at 18:07). Cross-checked
  bit-identical on the CCWALLWARMPF vector (NLL, saturated, blinded α_s). (Evidence: 260923-lattice-fits/logs/analyze_walled.log, Result §1)
- Luca: no validity checks on the old references (CCKRYLOVWARM, CCWALLCOLDR). Only the LATL4ZUNWWARM row is still pending.
- LATL4ZUNWWARM complete. NLL 375.534, Δχ²_data +4.0 / +3.7 vs CCWALLCOLDR / CCWALLWARM, projected ptll 78.7/39 (p 0.02%),
  σ(α_s) 1.163e-3. **Δα_s +0.37σ vs the walled lattice fit, +0.34/+0.71σ vs the old walled fits, +1.46σ vs CCKRYLOVWARM.**
  The TMD is unphysical (λ2 −0.078). **All three l4zero fits are done; `260923-lattice-fits` is closed.** (Evidence:
  [260923-lattice-fits/LOGBOOK.md](260923-lattice-fits/LOGBOOK.md) Result §1–2)
- **Study paused (Luca).** It has reached a good point. Next steps: (a) Luca reruns the lattice fits on the new
  |Y|≤3.5 cache once that chain works; (b) wait for the theorist's reply. START HERE / Findings / Open questions / Decisions rewritten
  as the study summary. Key results table moved to the top.
- **RETRACTION (orchestrator): the "c0 factor 2" is OUR bug, not the paper's.** `260923-lattice-data-refit/cs_fit.py` put
  the paper's non-cusp coefficients one power of a_s too high: the 2-loop d at a_s³ and the 3-loop at a_s⁴, following the
  paper's supplementary text "d_0 = d_1 = 0, d_2 = …" literally. That d_2 is the 2-loop d^(2,0) and belongs at a_s², so
  the paper has an index offset. It is a big effect: −2D_res(b*) at 0.9 fm goes −0.63 → −0.38. Corrected (c0,k1) at
  B_NP=2: χ² 7.32/19, **c0 = 0.0324(60) in the literal Eq. (6)–(7) convention (paper 0.032), k1 = 0.213** (continuum
  file 0.2136; closed-form D_res gives 0.2143). What remains is only σ(c0), ours 0.0060 vs the paper's 0.012 (exactly 2×),
  and σ(k1) 0.066 vs 0.08. **Q1 of the 09-23 email to the theorist is wrong and needs a correction.** Unaffected: our
  SCETlib kernel fit, the lattice λ2_ν constraint, and the real-data fits, which all use `our_cs_kernel.py` (validated
  against SCETlib's Gamma_nu). The refit worker is fixing, rerunning and replotting in the paper's Fig. 2 style.
- lattice-data-refit rerun DONE with the fix: the paper reproduces (χ²/dof 0.385, c0 0.0324 / 0.0346 closed-form, k1 0.213),
  and the figure matches the paper's Fig. 2. Still unmatched: quoted σ(c0) is 2× ours, σ(k1) 1.2× (not a uniform scale).
  BLNY g2 = 0.0212 = ¼ of the quoted value, a convention question. Continuum file: σ(c0) 17% too small. B_NP: flat χ² over
  1–2.5 GeV⁻¹, but c0 depends strongly on it, so c0 is meaningful only paired with B_NP=2.
  (Evidence: [260923-lattice-data-refit/LOGBOOK.md](260923-lattice-data-refit/LOGBOOK.md))
  ![repro in paper Fig. 2 style](260923-lattice-data-refit/paper_fig2_style.png)
- Email comparison figure for the theorist (their data with their k1 subtracted, their Eq. 6–8 fit + band, our SCETlib
  λ4_ν=0 fit + band): [260923-scetlib-kernel-fit/email_lattice_comparison.png](260923-scetlib-kernel-fit/email_lattice_comparison.png).
  The two agree within their bands to ~0.7 fm. Update email drafted for Luca: it corrects Q1, re-asks the σ / BLNY / cross-ensemble questions,
  and shares no α_s-fit numbers.
  **Superseded by a clearer figure** (Luca: the old one never drew the published ASWZ curve):
  ![ASWZ data, ASWZ published fit, our refit, our SCETlib fit](260923-lattice-data-refit/comparison_aswz_refit_scetlib.png)
  *Points: per-ensemble data minus k1·a/b_T with k1 = 0.2136 (the value ASWZ used for their continuum file). Dark-blue solid:
  ASWZ published, Eq. (6)–(8), c0 = 0.032 ± 0.012 (Eq. 9), B_NP = 2 GeV⁻¹. Light-blue dashed: our refit of the same form,
  c0 = 0.0324 ± 0.0060; it coincides with the published curve, and only the σ differs. Red: our SCETlib tanh_2 fit (n_f=5, λ∞_ν=2,
  λ4_ν=0, λ2_ν = 0.1345 ± 0.031); dotted: free (λ2_ν, λ4_ν). Caveats: block-diagonal covariance; n_f 5-vs-4 offset ≤0.03 for
  the red curve; each fit has its own k1. Email variant without SCETlib: `260923-lattice-data-refit/comparison_aswz_refit.png`.*
- Orchestrator re-read the whole paper (main text + supplement, arXiv source) at Luca's request, to check the reproduction.
  - **Preferred model confirmed:** (c0,k1) with c1 = k2 = 0 and B_NP = 2 (main.tex L338). The lower panel of Fig. 2 subtracts
    k1·a/b_T only (L347). No k2 in the reference fit.
  - **The paper's own typos that we handled:** (i) the d_n index offset (supplement); (ii) "B_NP = 2 GeV" must be GeV⁻¹
    (b* formula; SV19's 1.9 is GeV⁻¹). Our reproduction uses both corrections and matches c0 and k1.
  - **Not stated anywhere:** how the fit uncertainties are computed. The per-ensemble kernels are "bootstrap-level weighted
    averages" over Γ, P^z pairs and x∈[0.3,0.7] (L296), and the Z-factor systematic is added in quadrature (L263). So
    bootstrap-level fits are plausible but unconfirmed.
  - **Possible cross-ensemble correlation source:** the perturbative matching δγ (uNNLL) is common to all ensembles.
    That is relevant to Q4.
  - **BLNY:** D_NP = g2·b², with B_NP in D_res. Our ¼ factor is still unexplained, but the paper compares its g2 to IFY23's
    (same convention), so it is a convention issue for them, not for us.



### 2026-09-29
- **Theorist replied** to the 09-23 email:
  - Q1 (c0 factor 2): "some issues about a factor of 2", checking with the student. Our side: the central value
    was our d_n bug, already retracted. The factor 2 that remains is in σ(c0).
  - Q2: uncertainties from a parametric bootstrap, i.e. correlated Gaussians thrown from the lattice covariance.
  - Q3: the only common systematic is the RG-scale variation in the renormalisation. It enters only through small
    Z-mixing corrections and is negligible, so the ensembles are effectively independent and block-diagonal is fine.
  - Q4: the α_s dependence is "small by the same logic".
- **Orchestrator check of Q2:** a parametric bootstrap from the files' covariance reproduces OUR Hessian σ exactly:
  σ(c0) = 0.0060, σ(k1) = 0.066 over 20k throws. That must hold for a model linear in (c0, k1) at fixed B_NP. A
  diagonal-weighted fit with correlated throws gives the same (0.0061 / 0.066). **So their stated method does not
  explain σ(c0) 2× / σ(k1) 1.2×.** Something else must enter their bootstrap (B_NP or D_res variations per throw? a
  different covariance than the files?). Follow-up question for the theorist.
- Candidate explanations tested for the σ mismatch (parametric bootstrap, 3k throws):
  - B_NP varied per throw inflates ONLY σ(c0): U[1.5, 2.5] → 0.0096; profiled in [1, 2.5] → 0.032. σ(k1) stays 0.067–0.068.
  - A factor-2 normalisation slip in propagating σ(c0), e.g. errors computed with −c0·b·b* while the central value uses
    the literal form, would give exactly 0.012. It cannot touch σ(k1).
  - These are hypotheses, NOT a claim that their errors are wrong. Equally likely: their bootstrap includes legitimate
    extra variations, in which case OUR covariance-only σ is too small. **That matters for us:** our lattice λ2_ν
    constraint uses the files' covariance for its stat part (±0.020). If the true uncertainty is ~2× larger, the constraint
    should inflate (total ±0.031 → ~±0.047). The question to the theorist is phrased neutrally ("what else enters").
  - **Neither explains σ(k1) = 0.08 vs 0.066.** That needs a ~1.2× larger data covariance (an extra systematic?), unless
    it is rounding: 0.08 ⇐ [0.075, 0.085] → ratio 1.13–1.28. Luca has not yet sent the correction email; the follow-up question goes into it.
- Luca sent the correction + a light uncertainty question. **Theorist's reply:** they fit their ORIGINAL bootstrap samples, not the
  covariances they shared, and included an RG-scale renormalisation variation (small). The difference is bigger than they expected,
  possibly model averaging; the student may share the actual fit. They sent their Mathematica notebook
  (`/work/submit/lavezzo/cs_kernel/MILC_all_phys_beam_25.nb`, 80 MB, "no warranty"). Dispatched `260929-aswz-notebook`: parse the
  notebook as text (no Mathematica here), compare the fit function, data and uncertainty procedure with ours. Confidential: extracts go
  to /work/.../cs_kernel/notebook_extract/, not the public study dir.
- aswz-notebook DONE: **σ mismatch explained.**
  - Their fit function, data and χ² equal ours. Their python-transcribed (c0,k1) fit reproduces to all printed digits:
    c0 = 0.0330, k1 = 0.21365, χ²/dof 0.3868. It confirms γ_NP = −2c0·b·b*, B_NP in GeV⁻¹, and 2-loop d at a_s², so our
    09-24 fix and retraction stand.
  - **Their error rule is not a covariance resampling.** Each pseudo-fit shifts ALL points of an ensemble by ONE common
    N(0,1) scalar times Corr_e·σ_e, i.e. fully coherent within the ensemble; they quote the 68% half-width over 200 refits.
    Orchestrator verified analytically with our cs_fit: σ(c0) 0.0115, σ(k1) 0.070 (the notebook prints 0.0117 / 0.0676,
    the paper 0.012 / 0.08); correct resampling gives 0.0060 / 0.066. The same rule explains the paper's "(c0,k1,k2) σ
    within 10%" claim.
  - **BLNY:** the notebook fits −g·b² (g = 0.0427); the paper's g2 = 2g, so the ×4 is a convention.
  - **Their minor bugs** (not affecting Eq. 9): a unit mismatch in the c1 log, and a squared variance in the model average.
  - **Impact on us** (orchestrator, linearised, λ4_ν=0, λ∞_ν=2, k1): if the coherent within-ensemble shift is a REAL
    systematic, our λ2_ν stat σ goes 0.020 → 0.037 and the total 0.031 → ~0.044. If it is a bug (an intended MVN draw),
    our constraint stands. Question for the authors.
  (Evidence: [260929-aswz-notebook/LOGBOOK.md](260929-aswz-notebook/LOGBOOK.md); private extracts in /work/submit/lavezzo/cs_kernel/notebook_extract/)
- **On Q4:** their argument is about Z-factor mixing, but the α_s dependence enters mainly through the quasi-TMD matching
  correction δγ (uNNLL, Eq. 2), which adds directly to every estimator and is common to all ensembles. Rough one-loop
  estimate: δγ = O(α_s·C_F/π·logs) ~ 0.1, so a Δα_s(2 GeV) ~ 0.01 moves the points by ~0.005, negligible vs σ ~0.1.
  The conclusion probably holds; the reasoning should be confirmed.

---

## Findings

**Since 2026-10-06 (current line):**
- The exact lattice χ² sits in the fit as a rabbit regularizer (`LatticeCSTerm`). The kernel comes from SCETlib at every
  step and is the same function as in the cache; k1 is profiled analytically and the systematics enter as δδᵀ
  ([261007-lattice-term-native](261007-lattice-term-native/LOGBOOK.md); physics review: APPROVE WITH FIXES).
- With the lattice-side kernel frozen at α_s(m_Z) = 0.1168 (LATFROZ), the lattice constrains only λ2_ν and λ4_ν. α_s moves
  −0.026…−0.035σ vs the live LATB8, and the n_f conventions span 0.009σ
  ([261008-latfroz-nf-variants](261008-latfroz-nf-variants/LOGBOOK.md)).
- NOMSTIFF is not a no-lattice fit. Against the no-lattice XWSTIFF (λ4_ν free; λ2_ν on its wall) LATFROZ_V3 moves α_s by
  +0.245σ_XW with σ ×1.05. Against XL4ZSTIFF (λ4_ν = 0) the shift is −0.013σ (evidence:
  [scripts/orch_dalpha_vs_nolattice.out](scripts/orch_dalpha_vs_nolattice.out)).
- Precision on (λ2_ν, λ4_ν): lattice only 0.188 ± 0.043, −0.0061 ± 0.0035 (ρ −0.88); joint V3 0.038 ± 0.030,
  0.0106 ± 0.0057. The Z data alone sit on the λ2_ν ≥ 0 face, so their walled σ is meaningless (evidence:
  [scripts/orch_lambda_precision.out](scripts/orch_lambda_precision.out), `scripts/orch_lattice_only_cov.py`).
- Z–lattice tension: PG 13.5 for 2 dof, p 0.12 %, 3.2σ (V3 vs XWSTIFF). The lattice-only part is 9.2 (2.6σ). The Z data
  want weaker small-b CS damping than the lattice.

**Before 2026-10-06:**

1. **The lattice CS kernel is the same object as SCETlib's.** γ_q = 2 dln f/dln ζ at μ=2 GeV (MSbar) ≡ γ̃_ζ = ½·Gamma_nu,
   with no sign or factor difference. The only mismatch is n_f=5 (fit) vs 4 (lattice): a coherent ≤0.03 offset whose sign
   depends on μ, carried as one correlated systematic. The perturbative kernel is flat for b_T ≳ 0.3 fm (μ0 floor 1 GeV),
   so the lattice window probes the NP tanh. ∂γ/∂α_s(mZ) ≈ −3, i.e. ~1/25 σ_lat per 0.001. — (evidence: 260923-conventions-map)
2. **Use the per-ensemble data plus a free k1·a/b_T.** The "continuum" csv is raw − 0.2136·a/b_T with stat-only diagonal
   errors: it loses the k1 uncertainty and the correlations (σ(c0) 16% too small). B_NP (their b* scale) is unconstrained
   by the data. — (evidence: 260923-lattice-data-refit)
3. **We reproduce the paper's fit** once the non-cusp d_n are placed at the right powers of a_s (the paper's appendix
   has an index offset). (c0,k1): χ² 7.32/19, c0 = 0.032 (literal convention), k1 = 0.213 = the continuum file's value.
   Only the quoted uncertainties differ: σ(c0) 0.012 vs our 0.006, σ(k1) 0.08 vs 0.066. *(Supersedes the earlier
   "c0 factor 2" finding, which was our bug.)* Irrelevant for Option B. — (evidence: orchestrator check 2026-09-24;
   260923-lattice-data-refit, rerun pending)
4. **Our tanh_2 kernel + k1 describes the lattice** (χ² 6.7/18; k1 preferred over k2; tanh_6 not needed; λ∞_ν
   unconstrained, flat above ~1.1). **With λ4_ν = 0 (as used in the fits): λ2_ν = 0.1345 ± 0.020 (stat) ± 0.024 (syst)**
   at λ∞_ν=2, at a cost of only Δχ²=1.9. The kernel is unchanged below 0.6 fm. It is consistent with the Tackmann/AN tune
   and the card anchor, and 5.5–14σ from all old Z postfits. — (evidence: 260923-scetlib-kernel-fit)
5. **The Z postfit λ_ν "precision" is not a CS-kernel measurement.** At the physical point a gen-level Fisher gives
   σ(λ2_ν) = 0.25 (NP free) / 0.087 (card priors), looser than the lattice's 0.031–0.038. ρ(λ2_ν, Λ2) ≈ −0.985 (the O(b²)
   fixed-Q degeneracy). The tight Hessian σ of the old fits sit at unphysical anti-damping minima. — (evidence: 260923-qsplit-fisher)
6. **Splitting mll 60–120 into Q windows does not break the CS–TMD degeneracy** (ρ −0.998 → −0.991). A lattice CS prior
   does most of the job (σ(Λ2) 0.167 → 0.062, ρ(α_s, λ2_ν) 0.44 → 0.11) and makes Q binning redundant (≤3%). A no-eigenvector
   5-window AD cache builds in ~12 min. — (evidence: 260923-qsplit-cache-cost, 260923-qsplit-fisher)
7. **With the lattice term in the card-A real-data fit, α_s is stable.** Walled lattice vs old walled cold: Δα_s +0.01σ,
   Δχ²_data +5.0. Walled vs warm-unwalled lattice: 0.37σ. Both are within 0.7σ of the old walled fits. σ(α_s) ≈ 1.16e-3.
   The gammaNu impact drops 0.5–0.8 → 0.05 (×1e-3). The CS kernel becomes physical but sits 1.4–2.3σ below the lattice
   (mild data–lattice tension). — (evidence: 260923-lattice-fits Result §1–2)
8. **A CS-only constraint does not keep the NP model physical.** The unwalled optimum moves the violation into the TMD
   boundary condition (λ2 = −0.078, L2 < 0 at every |Y|, F_eff up to ~1.1), reproducing 260911 on the current model. The
   wall restores physicality at ΔNLL 1.2. — (evidence: 260923-lattice-fits)
9. **The AD cache is invalid wherever the large-b NP damping reaches ~0:** CS λ4_ν ≲ −0.002 (O(1) low-qT oscillation,
   σ<0 near −0.007), and TMD Λ4 + L2³/3 ≲ 0 with margin; the sign of L2 alone is not the criterion. Minimisers converge
   onto these artefacts (cold unwalled lattice fit; old CCCOLDSELF). tanh_2 with λ4_ν<0 is also physically anti-damping
   beyond ~1.1 fm. — (evidence: 260923-lattice-fits λ4_ν probe, 260924-unwcold-xsec-validity)
10. **Cold card-A fits are slow and can stop in worse local minima.** ~1500 iterations / 3–6 h; the cold unwalled lattice
    fit ended 6.9 above its warm counterpart, which converged in 17 iterations. Always check a cold result against a warm
    seed from a neighbouring minimum. — (evidence: 260923-lattice-fits)

---

## Open questions

**For the theorist** (email 2026-09-23; priority 1, 2, 4):
1. ~~Is c0 the coefficient of −b_T·b* or −2·b_T·b*?~~ RETRACTED 2026-09-24: our bug. It needs a correction email. The remaining question is why the quoted σ(c0) is 2× ours, and σ(k1) 1.2×, which folds into Q2.
2. How are the uncertainties computed (σ(k1) 0.066 vs 0.08; (c0,k1,k2) σ(c0) +43% vs the paper's ≲10%)?
3. Is k1 = 0.2136 in the continuum file the unrounded best fit?
4. ~~Are there correlations across ensembles (a common matching or α_s systematic)?~~ Answered 2026-09-29: negligible (only an RG-scale Z-mixing piece); block-diagonal is fine.
5. How do the points move with α_s through the matching (their 0.293 ↔ α_s(mZ) 0.117)?
6. Is the 0.72 fm point at a=0.09 (b_T/a = 8, beyond Table I) the same kind of determination?
7. Why can't we reproduce BLNY g2 = 0.085?

**Physics / method**
- **The new cache.** Do the conclusions hold on `pdf62_y35_260921` (|Y|≤3.5)? The TMD δλ2·Y² lever arm grows with the
  Y range, so the TMD relocation could change.
- **Walled minimum uniqueness.** Is LATL4ZWALLCOLD the walled optimum? Test: a walled fit seeded from LATL4ZUNWWARM (not run).
- **λ∞_ν systematic.** The lattice doesn't fix it and the fits freeze it at 2. Rerun at e.g. 1.5 and 3 with the lattice
  term refit at each value.
- **Data–lattice tension.** λ2_ν sits 1.4–2.3σ below the lattice. Is this real, or a symptom of the TMD form or other
  mismodelling? It would change if the authors' answer to Q4 inflates the errors.
- **TMD boundary condition.** It has no DY-free external constraint; CS-only constraints push the violation there.
  Deferred by Luca; the MAP22 mapping in np_parametrization_constraints.md §16 is the existing reference.
- **A validity guard in the model.** Nothing stops a minimiser entering the cache's invalid region (no positivity or
  damping guard in compute()). This is needed before unwalled fits can be trusted.
- **Projected-ptll GoF** is poor in every fit (p ≲ 0.1%). A toy calibration of that test is not done.
- **Charm threshold.** The n_f 4→3 effect below m_c in the kernel scheme comparison is not quantified.
- **AN.** The lattice section (theory.tex L257–292) uses the Tackmann numbers. Replace it with this study's determination
  once the theorist answers and the new-cache fits are in.

---

## Decisions
- 2026-10-09 (Luca): take the conservative n_f row. By the α_s measures that is the current default `Jnf`: larger
  total impact than `direct_nf` (+0.0096 vs +0.0068σ_NOM against no row) and the larger σ(α_s) contribution (0.051 vs
  0.034σ_NOM). No code change. Only `direct_nf` is (marginally) more forgiving on the PG (13.41 vs 13.48).
- 2026-10-09 (Luca): **V3 is the default** of LatticeCSTerm (pert=frozen, alphas_frozen=0.1168, syst=Jnf, nfmatch=4.18,
  nfscheme=full). Retire the table-based term (lattice_cs_chi2) and its inputs, and the Gaussian 1D/2D lattice cards (no longer
  used or produced; the card files stay on ceph for provenance). λ∞_ν rows
  deferred. Lattice-derived priors are fine; TMD boundary-condition λ stay free (no Tackmann priors). knowledge §10 scope
  clarified.
- 2026-10-08 (superseded 10-09: adopted): LATFROZ_V3 as the nominal lattice configuration (`pert=frozen alphas_frozen=0.1168
  syst=Jnf nfmatch=4.18 nfscheme=full`). The code defaults (`DEFAULT_SYST = Jnf+Jbt`, `pert=live`) still need changing.
- 2026-10-08 (Luca): keep the simultaneous (exact χ²) lattice fit; do not switch to fixing the CS λs.
- 2026-10-08 (Luca): the b_T window systematic is dropped from the lattice term.

- 2026-10-07 — Lattice term: theory from SCETlib at every step (option B), no shipped theory tables; same (analytic-RGE) kernel as the cache; SCETlib-native n_f systematic; no μ0 variation; no k-form; b_T window pending the theorist; no double-counting guards. (Luca)

- 2026-10-06 — Lattice systematics = n_f scheme + b_T window; k-form NOT varied (theorists' prescription). (Luca)

- 2026-09-24 — Pause the study; rerun on the new cache later (Luca). No validity checks on the old references (Luca).
- 2026-09-24 — Unwalled lattice fits must be warm-started (the cold one stopped in a local minimum on a cache artefact).
- 2026-09-23 — First real-data lattice fits use the OLD setup (card A, cache pdf62_corrgrid_260827), for direct comparison
  with alphas-scan-discontinuity. New-cache version deferred (Luca; supersedes the same-day switch to the new cache).
- 2026-09-23 — The lattice enters as a rabbit external likelihood term (full covariance, in θ) that REPLACES the default
  CS priors (`prior_sigmas=lambda2_nu=nan`), with no params.py change. λ∞_ν stays frozen at 2.
- 2026-09-23 — Don't add mll Q bins for this purpose: the Fisher forecast shows no degeneracy breaking and redundancy with
  the lattice prior.
- 2026-09-23 — Option B (fit our kernel to the per-ensemble data, with k1 nuisance) over Option A (their parametrization):
  a different NP form, the c0 ambiguity, and the continuum file loses information.
- 2026-09-23 — In-fit lattice constraint = λ4_ν frozen at 0 + 1D lattice term on λ2_ν (direct refit, 0.1345 ± 0.031). Reasons: the AD cache and tanh_2 are invalid for λ4_ν ≲ −0.002; the lattice accepts λ4_ν=0 (Δχ²=1.9); the kernel is unchanged below 0.6 fm (supersedes the 2D-Gaussian design of the same date).

- 2026-09-23 — TMD boundary condition is out of scope for now. Focus on the CS kernel in the current setup (Luca: "much left to be understood for our current setup").
- 2026-09-23 — 260911-lattice-constraints conclusions stand qualitatively but were on an older fit; any in-fit lattice arm must be redone on the current param model (Luca).

- 2026-09-23 — The AN/Cridge lattice λ values are not a reference to validate against; derive the SCETlib↔lattice matching from first principles — they aren't robust and their methods were never published (Luca).
