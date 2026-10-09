---
title: Lattice term from live SCETlib (option B design)
slug: 261007-lattice-term-design
study: lattice-cs-kernel
status: done          # active | done | paused | abandoned
created: 2026-10-07
updated: 2026-10-07
owner: study-worker
---

# Lattice term from live SCETlib (option B design)

**Task:** How should the ASWZ lattice CS-kernel term be computed from SCETlib itself at every fit step (an `_XsecTFBase` subclass, no shipped theory tables), what does SCETlib expose today, and what is the full lattice-data handling design (inputs, likelihood, systematics, guards, interface, effort)?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-10-07 14:40)

- **Answer:** SCETlib has no Python-callable CS kernel today. The function itself, `ad::gamma_nu_resummed`, already
  exists in the clad AD kernel; the cross section calls it. A ~10-line clad wrapper exposes it.
  - A prototype built against the current build reproduces `qT::Gamma_nu` to 5e-16, and its clad gradient and Hessian
    agree with finite differences (FD-limited, ≤1e-5).
  - Taking the kernel from SCETlib moves it relative to the shipped table by ≤1.9e-3 (≤0.019 σ_lat), because the fit's
    SCETlib uses the *analytic* RGE and the table used the *exact* one. The α_s derivative changes by 8.5 %. So the
    target "agree with the table to 1e-10" cannot be met by construction; the right targets are given below.
  - The full design is in Result §3–§7.
- **Next action:** Luca decides the open choices (Result §8). Then the implementation goes in the order of §6.
- **Blocking on:** Luca's decisions; the theorist's answer on the b_T window (only affects one systematic).
- **Running:** nothing.

---

## Log

### 2026-10-07
- Read the study logbook (consolidated systematics section, 10-06/07 entries) and 261006-lattice-chi2-in-fit in full.
- Code read (scetlib-cms 2dd978a under `$WREM_BASE/scetlib-cms`; WRemnants 3ef3efb9):
  - SCETlib: `Gamma_nu.hpp/.cpp`, `Gamma_nu_formulas.hpp`, `NP_models.hpp`, `ad/ad_kernel.hpp`, `ad/ad_data.hpp`,
    `ad/ad_context.{hpp,cpp}`, `ad/ad_derivs{.hpp,_clad.cpp}`, `py/qT/qT.cpp` (pybind), `py/qT/DrellYanAD.cpp`
    (mutexes, staging), `py/scetlib_tf.py`, `py/scetlib_tf_native.py`.
  - WRemnants: `scetlib_ad/{lattice_cs_chi2,param_model,params}.py`.
  - rabbit 2a59246: `fitter.py` `_compute_nll_components` and `_compute_nll`, `external_likelihood.py`.
  - Cache config: `/ceph/.../scetlib_ad_caches/pdf62_y35_260921/merged_full_bin0xzero/cache.conf`.
- Prototype [proto/](proto/): [gz_clad.cpp](proto/gz_clad.cpp) is a clad TU (only `ad_kernel.hpp` included, as in
  `ad_derivs_clad.cpp`) that differentiates `gamma_nu_resummed`. [gz_proto.cpp](proto/gz_proto.cpp) stages `ad_g` and
  compares against the `qT::Gamma_nu` class. Build: [build.sh](proto/build.sh), in the container, against the current
  build, with no change to the checkout.
  - Outputs: [out_anchor.txt](proto/out_anchor.txt) (α_s 0.118, TNPs 0, λ_ν = (2, 0.15, 0));
    [out_displaced.txt](proto/out_displaced.txt) (α_s 0.120, θ_cusp +1, θ_γν −1, λ2_ν 0.05, λ4_ν 0.008).
  - Runtime 13 ms for all 21 points, including every FD loop.
- [compare_table.py](compare_table.py) → [compare_table.json](compare_table.json) / [compare_table.txt](compare_table.txt):
  SCETlib (analytic) vs the shipped table (exact RGE), and the effect on the lattice-only fit. Everything is at the
  public anchor α_s = 0.118; no fit result was used.

---

## Result

### 0. Caveats first
- No fit was run. Every number here is at the **public anchor** (α_s(m_Z) = 0.118, TNPs = 0) or at hand-picked
  displaced points. Nothing is blinded and nothing depends on a fit result.
- The prototype stages SCETlib's `GlobalData` **by hand**, from the same SCETlib coefficient functions that
  `Ad_evaluator::_build_global` uses, and only for the γ_ν fields. In production the staging is the param model's own
  `Ad_evaluator::global()` (§3). The prototype shows that the kernel function and its clad derivatives are right; it
  does not show that the staging is right. That is validation item V2.
- The "≈ −0.004 σ_NOM" effect on `alphaS` below is a first-order scaling of the measured +0.07σ live pull. It is not a fit.

### 1. What SCETlib exposes today
- **No Python callable gives γ_ν(b_T, μ) or its derivatives.** pybind exposes `set_gamma_nu_model_params` and the
  cross-section batches only. `RunningCoupling` is bound, `qT::Gamma_nu` is not (`py/qT/qT.cpp`, `py/core/core.cpp`).
- **The function exists, clad-ready, inside the AD kernel:** `ad::gamma_nu_resummed(p, bT, mu0, fz_mu0, fz_mu)`
  (`include/scetlib/qT/ad/ad_kernel.hpp:630-703`). It is a transcription of `Gamma_nu::operator()` and shares
  `Gamma_nu_formulas.hpp` with the class. It reads everything else from the thread-local `ad_g`:
  - α_s(m_Z) at `ip_as0`, with fixed-n_f analytic running (`alphas_run`);
  - the cusp coefficients `Gq`/`Guniv` and the γ_ν boundary constants `gnu[0..3]`, each an `Affine` in its TNP θ;
  - the NP model `np_gnu_*` with its λ indices.

  `node_value` calls it three times per node, for the beam a/b and the soft evolution, so it is already
  clad-differentiated and validated as part of the cross section. **The cross section and an option-B lattice term
  would share one kernel function.**
- **Existing `_XsecTFBase` subclasses** (`py/scetlib_tf.py`):
  - `ScetlibXsecTF`: live evaluation. `DrellYan.sigma_batch` / `sigma_binned_batch` give value + clad gradient, and
    `hessian_*` / `hvp_*` give clad reverse-over-forward second derivatives.
  - `ScetlibCachedXsecTF`: the fit's path. It replays the compressed rules (`sigma_binned_rule_batch`,
    `sigma_grad_hess_binned_rule_batch`, `hvp_binned_rule_batch`). Each rule entry restages its own stored `GlobalData`
    (`ad::ad_g = entry->g`, `DrellYanAD.cpp:3385, 3536, 3598`), and clad differentiates `node_value` on the tape.
  - Both return values and derivatives over the full SCETlib registry vector (`gradient_param_names()`, e.g. `alphas`,
    `np_gnu_lambda2`, `tnp_gamma_nu`, `tnp_gamma_cusp`; at most `kMaxParams` = 64).
  - `scetlib_tf_native.ScetlibXsecNativeTF` is a separate pure-TF transcription, not an `_XsecTFBase`. Do not use it
    here: it is **stale for every CS NP form other than tanh_2** (see Open questions).
- **Settings** that γ_ζ at the lattice points depends on, all in `cache.conf` and all already inside the param
  model's calculation:

  | setting | value in `merged_full_bin0xzero/cache.conf` |
  |---|---|
  | `run_order` / `alphas_order` | n3ll |
  | n_f | 5 (`[QCD] nf`) |
  | α_s start | `alphas_mu0` 0.118 at `mu0` 91.1876 |
  | **`alphas_solution`, `rge_solution`** | **analytic** |
  | μ0 profile | `form_np_prescription` collins_soper4, `mu0_min` 1, `b0_over_bmax` 0 |
  | freeze-out `lambda` | 0 |
  | `b0_over_bmax_global` | 0, so b̄ = b_T |
  | NP | `np_model_nu` tanh_2, λ∞_ν 2, `b0_over_bmax_nu` 1 (sextic b* in L_b) |
  | TNPs | `gamma_cusp` / `gamma_nu` level0, orders n_cusp = 3 / n_noncusp = 2 (`variations.py make_tnps`) |

### 2. Cheap checks: the prototype and SCETlib vs the shipped table

| check | anchor | displaced |
|---|---|---|
| A. `gamma_nu_resummed` vs `qT::Gamma_nu` (analytic), max abs (γ_ν), full / pert | 4.7e-16 / 4.6e-16 | 5.6e-16 / 5.6e-16 |
| B. clad gradient vs central FD of the class, max rel (6 params) | 1.0e-6 | 9.5e-6 |
| C. clad Hessian vs FD of the clad gradient, max rel | 1.3e-6 | 2.3e-6 |
| class with the **exact** RGE vs the shipped table `pert` | 1.4e-12 | – |
| **SCETlib (analytic) − shipped table**, γ_ζ | −2.3e-4 … +1.9e-3; ≤ 0.019 σ_lat (diag stat) | – |
| ∂γ_ζ/∂α_s(m_Z), plateau (b_T ≥ 0.3 fm) | −2.68 (SCETlib) vs −2.93 (table): −8.5 % | – |
| ∂γ_ζ/∂θ_γν, ∂γ_ζ/∂θ_cusp | agree to 6.6e-5 / 1.4e-4 absolute (values ≤ 6e-3 / 1e-3) | – |
| NP value, NP Jacobian (λ2_ν, λ4_ν) vs the plugin's tanh | 8.6e-13; 4.7e-11 / 4.2e-10 | – |

- **The table matches SCETlib with the exact RGE (1.4e-12), not SCETlib as the fit runs it (analytic, 1.9e-3).** The
  plugin docstring says the table is "validated against SCETlib's Gamma_nu to 5e-11". That is true only against the
  exact-RGE configuration. 260923-conventions-map recorded the 1.9e-3 gap but did not carry it into the plugin. So the
  current term's perturbative kernel is not the one in the Z prediction it is fitted with.
- Effect on the lattice-only fit (`Jnf+Jbt`, λ∞_ν = 2, k1 profiled):
  - minimum: χ²_min 6.713 → 6.703; λ2_ν 0.1844 → 0.1855 (+0.025σ); λ4_ν −0.00592 → −0.00597 (−0.014σ);
  - χ² at the NOMSTIFF and LATCHI8 points: +0.20 and +0.14 in absolute χ², i.e. about +0.2 in Δχ² against each
    set's own minimum.
- ∂χ²_lat/∂α_s at LATCHI8's CS point: −284 (table) → −269 (SCETlib), ratio 0.946. Scaling LATLIVE8Y's live α_s pull
  (+0.069σ_NOM) gives **≈ −0.004σ_NOM** from switching to SCETlib's kernel. That is first order; the fit is the
  measurement (V7).
- Cost: all 21 points (value + clad gradient + 6×6 clad Hessian, plus the FD checks) take 13 ms. In the fit loop the
  term is negligible.

**Physics read.** The λ_ν are defined relative to a specific perturbative kernel (260923-conventions-map; CMT
pp. 19–20). The one that matters is the kernel the Z prediction uses, i.e. SCETlib with the cache's `analytic`
running and RGE. The shipped table used a different truncation of the same N3LL kernel: numerically exact running
and evolution. The difference is beyond N3LL, ≤ 2e-3 in γ_ζ, and 8.5 % in the α_s slope. It is invisible against the
lattice errors, but it is an inconsistency between the two halves of the likelihood that option B removes by
construction. With live α_s and live TNPs, both halves move under exactly the same SCETlib function.

### 3. Proposed SCETlib entry point

**C++ (scetlib-cms, MR on the `autodiff-sigmaul` line).** No kernel change, no rule or cache format change, so
existing caches stay readable.
1. `src/qT/ad/ad_derivs_clad.cpp`: two wrappers over `gamma_nu_resummed`, reading the point from a new thread-local
   `GnuPointData {bT, mu0, fz_mu0, fz_mu}` (clad cannot take struct arguments), plus
   - `double gnu_point_grad(const double* p, double* grad, int n)` (`clad::gradient`);
   - `double gnu_point_hess(const double* p, double* hess, int n)` (`clad::hessian`, bucketed 8 / 24 / 64 with one
     wrapper per range, exactly as `node_value_hess`).

   Declarations go in `ad_derivs.hpp`, and an FD fallback in `ad_derivs_unavailable.cpp`. This is what
   [proto/gz_clad.cpp](proto/gz_clad.cpp) does.
2. `Ad_evaluator::gnu_point_scalars(double bT, double mu, double* out4)` (`ad_context.cpp`): b̄ = b*_global(b_T) as
   in `fill_node`, μ0 from the evaluator's own `Scale_provider` (`sc.mu0`; it is b-space only, so independent of Q,
   q_T and every fit parameter), `fz_mu0 = _fz(mu0)`, `fz_mu = _fz(mu)`. One place, no fourth transcription of the
   profile.
3. `py::qT::DrellYan` (DrellYanAD.cpp + pybind in qT.cpp):

   ```
   gamma_nu_points(bT: (N,), mu: float, p: (P,), order: 0|1|2) -> {"value": (N,), "value_pert": (N,),
                                                                    "grad": (N,P), "hess": (N,P,P)}
   ```

   - It returns γ_ν in SCETlib normalisation; the caller halves it to γ_ζ. `value_pert` is the same call with the NP
     term off, for diagnostics.
   - The parameter vector is the full registry vector, the same layout as `sigma_binned_rule_batch`'s `p`.
   - Exactness: `hessian_is_exact()` like the cross section.
4. **Which `GlobalData`.** The replay stages each rule entry's own snapshot, so the entry point should snapshot the γ_ν
   fields **once**, at the first call (or an explicit `gamma_nu_points_prepare(bT, mu)`), from `_ad().global()`.
   - At that point it asserts, bitwise, that these fields equal those of the first loaded rule entry: `ip_as0`,
     `as0_base`, `mu0_start`, `run_lvl`, `beta`, `Gq`, `Guniv`, `gnu`, `color_casimir`, `np_gnu_*`, `ip_gnu_*`,
     `prof_*`. This proves the lattice term uses exactly the coefficients the replayed cross section uses.
   - It also stores the 4 point scalars per b_T, which are constants.
5. **Thread safety.**
   - The kernel state (`ad_g`, `ad_beta`) is `thread_local`. API entry points serialise on the file-static
     `s_ad_mutex` (DrellYanAD.cpp:653) and restage `ad_g` at every entry.
   - `_ad().global()` is a reference to a member that `prepare_point(Q, Y)` mutates. So **copy it under `s_ad_mutex`**,
     once, at the snapshot. Every evaluation then uses the private copy:
     1. save the calling thread's `ad_g` / `ad_beta`;
     2. stage the copy;
     3. evaluate;
     4. restore.
   - With that, no shared mutable state is touched at evaluation and no lock is needed. The restore makes the call
     invisible to any later kernel call on the same TF inter-op thread. Today every path restages anyway, but the
     restore removes the dependence on that.
   - Hold the GIL, like `sigma_binned_rule_batch`: it is microseconds.
   - Do not call `muf_poly_clear()`: γ_ν reads no convolution or muF state.
6. **Refusals** (in C++, so every caller gets them):
   - `b0_over_bmax_global != 0`: the lattice b_T would then be ambiguous between bare b_T and b̄. Today it is 0.
   - FO-only pieces (`_ad_fo_mode()`), which have no γ_ν.
   - No message may contain a parameter value (blinding).

Effort: ~150 lines of C++ plus pybind, and C++ tests (A–C of §2 moved into `testing/qT`). About 1 day including a
rebuild and the MR.

### 4. Proposed TF wrapper: `ScetlibGammaNuTF(_XsecTFBase)` in `py/scetlib_tf.py`
- `__init__(sing, bT_gev, mu=2.0)`; `param_names = sing.gradient_param_names()`; `n_points = len(bT)`;
  `n_params = P`.
- `values_and_jacobian(p)` and `hessian(p)` come from `gamma_nu_points` with a one-entry memo keyed on `p.tobytes()`.
  `hvp(p, v) = hessian(p) @ v`, and `_hessian_matrix_available() = True`: the full Hessian is (21, ≤64, ≤64) and
  costs microseconds, so the hoisted-Hessian path is always right.
- `values_jacobian_hessian(p)` comes from one call.
- Inherits the three-level `custom_gradient`, so nested tapes and forward-over-reverse both work. The test is the same
  as `stage0/test_tf_second_order.py`.
- About 80 lines plus a test; ½ day.

### 5. Blinding: the parameter vector and what must never be printed
- **Source.** rabbit hands every regularizer `get_x() = [get_poi(), get_model_nui(), get_theta()]`, and the param model
  `[get_poi(), get_model_nui()]`. `get_poi()` is the offset-applied **physical** frame (verified in 261006, BLINDCHK B).
- **New rule: no second map.** The param model gains one public method, `scetlib_full_vector_tf(param)`, factored out
  of `_sigma_gen` (param_model.py:1428-1451). It applies `held + S · _physical_tf(param[:n_scetlib])`, the same
  constant 0/1 matmul (not a scatter, so second order survives).
  - The term calls `pm.scetlib_full_vector_tf(params[:pm.nparams])`. The α_s, TNP and λ_ν it hands SCETlib are then the
    **same tensor expression** the cross section gets.
  - This replaces today's re-derivation of the α_s/TNP maps from `_rp_c` and of the λ maps from `NPDampingWall`
    (`resolve_wall_inputs`). The current plugin keeps two separate implementations of the θ→physical map; this keeps
    one.
  - Keep the slot check: `pm.params == names[:pm.nparams]`.
- **Blinding check (BLINDCHK analogue):** (A) `p_full[alphas]` of the term − of the model = 0 exactly; (B) armed vs
  disarmed; (C) AD vs FD in `x[alphaS]`; (E) the TNP identity. Only exactly-zero differences and FD agreements are
  printed.
- **Never print, log or put in an exception message:**
  - anything evaluated at the live vector: γ_ζ at the points, `p_full` entries, χ²_lat, k̂1, residuals, ∂χ²/∂α_s;
  - the lattice term's own NLL contribution. It stays inside the total loss, as in 261006 B2.

  Allowed: the anchor-α_s load-time quantities (offset, systematic shift vectors, lattice-only λ_best), names, maps,
  settings. Domain checks in TF use `tf.Assert` with constant strings, as the param model's docstring already demands.

### 6. Full lattice-data handling proposal (the deliverable)

**6.1 Inputs.**
- *Ships as DATA* (WRemnants `scetlib_ad/data/lattice_aswz_data.npz` + `.json`):
  - per point: b_T [fm], a [fm], ensemble id (L32/L48/L64), y = γ_q [MSbar, μ = 2 GeV];
  - the three per-ensemble covariance blocks;
  - provenance: arXiv:2402.06725, the md5 of the six author files in
    `260923-lattice-data-refit/data/CS_lattice_results/`, the ensemble spacings and their source, the
    block-diagonal statement (author-confirmed 2026-09-29), and μ = 2 GeV.
- *Constant*: ħc for fm → GeV⁻¹.
- *Computed from SCETlib* (nothing else):
  - γ_ν(b_i, 2 GeV) and all its derivatives, at every step;
  - at load: the lattice-only reference minimum (offset), the systematic shift vectors (6.3), and the k1 profiling
    matrix.
- *Deleted from the shipped file:* `pert`, `pert_nf4`, `pert_nf5_mu1match`, `syst_J`, `syst_direct_nf`, `syst_pert`,
  `pertvar_*`, `dpert_*`, `jac_ref*`, `card2d_*`. The old file stays only with the old plugin, as a validation
  reference.

**6.2 The likelihood term.**
- r_i = ½γ_ν^SCETlib(b_i, 2 GeV; p_full) + k1·a_i/b_i − y_i, with C = C_stat + Σ_g δ_g δ_gᵀ.
- −ln L = ½χ², with χ² = min_k1 rᵀC⁻¹r = r0ᵀ M r0, M = W − (Wv)(Wv)ᵀ/(vᵀWv), W = C⁻¹, v = a/b. Gaussian in the 21 points.
- k1 is profiled analytically. That is identical to a free parameter (261006 Finding 2), and rabbit regularizers cannot
  own parameters. If rabbit ever routes this through a likelihood plugin that can own parameters (6.6), k1 becomes a
  real parameter.
- Offset: χ²_min of the lattice-only fit at the anchor (α_s 0.118, TNPs 0, λ∞_ν = 2), from SCETlib at load. It is
  cosmetic: it makes the term ½Δχ².
- **exp(2τ):** rabbit multiplies every regularizer by exp(2τ). Divide it back out with the live `fitter.tau`, as now.
  This stays the one fragile point of the `-r` route (6.6).

**6.3 Systematics** (each a shift δ_g of the 21 points added as δδᵀ to C, i.e. a profiled N(0,1) nuisance):
- **n_f scheme** (lattice n_f = 4 vs our n_f = 5). Both forms come from SCETlib at load:
  - the alternative kernel is SCETlib with n_f = 5 at μ = 1 GeV plus the n_f = 4 cusp evolution from 1 to 2 GeV:
    `RunningCoupling(nf=4)` started at (α_s^(5)(1 GeV), 1 GeV), and `gamma_nu_points` with an n_f = 4 snapshot, or the
    `Gamma_nu` class at load;
  - `direct_nf`: δ = alt − nominal at each point. Today this is a constant −0.042, because both pieces are b-independent
    above μ0 = 1 GeV;
  - `Jnf` (default, as now): d = λ̂_alt − λ̂_nom from two lattice-only refits at load, mapped as δ = J_NP(λ̂_nom)·d with
    J_NP the SCETlib Jacobian columns.
  - **Definitional change, to be signed off:** the current table's n_f = 4 coupling comes from 3-loop MSbar decoupling at
    m_b, which SCETlib cannot do (no flavour thresholds in `RunningCoupling`). "Identified at 1 GeV" is the literal
    SCETlib-native version of the table's own label. Expect it to differ from today's shift at the few-% level of
    the shift. Effect on `alphaS`: below the 0.007σ separation between direct_nf and Jnf.
  - Load-time is enough. The shift's α_s dependence is second order, and direct_nf vs Jnf already moves `alphaS` by
    only 0.007σ_NOM (261006 §7). Per-step is possible later, at the cost of a second live snapshot.
- **b_T window** (pending the theorist): d = λ̂(b_T ≥ 0.2 fm) − λ̂(all), from a lattice-only refit at load on SCETlib's
  kernel, then J-mapped. No tables. A switch `btwindow=on|off` defaults to on until the theorist answers.
- **NO μ0 variation.** Missing higher orders are the TNPs' job, and they are now live in the kernel itself. Not
  implemented in the new term at all.
- **NO k-form.** k1·a/b_T is the lattice authors' prescription. Not implemented.

**6.4 Fit parameters it sees and correlations with the Z prediction.**
- The term depends on exactly these, all **shared** with the Z prediction through the same `p_full`:
  - α_s(m_Z): fully non-linear here. Today's plugin uses a 2nd-order expansion.
  - `resumTNP_gamma_nu`, `resumTNP_gamma_cusp`: exact.
  - λ2_ν, λ4_ν (λ6_ν for tanh_6), and λ∞_ν / `b0_over_bmax_nu` if they are ever floated.
- Lattice-only: k1 (profiled) and the systematic nuisances (in C).
- **Test (V3):** the Jacobian must be exactly zero in every other column (TMD λ, PDF eigenvectors, other TNPs, κ_R,
  transition points). μ0 is b-space only, so it is independent of the profile parameters.
- Correlation mechanism, unchanged in kind from LATFULL: the Z data constrain one NP combination (ρ(λ2_ν, Λ2) ≈ −0.985).
  The lattice breaks it, and through it pins the TMD Λ2. α_s and the two CS TNPs are pulled by both halves
  coherently.

**6.5 Double-counting guards** (all hard refusals at `set_expectations`, before any offset is armed, with
parameter-name-only messages):
- **G1** The card carries an external term whose `params` intersect {λ∞_ν, λ2_ν, λ4_ν, λ6_ν}
  (`indata.external_terms`; this catches `cardA_latticeASWZ_*`).
- **G2** The param model has a finite `prior_sigmas` entry on λ2_ν, λ4_ν, λ6_ν or λ∞_ν, as the default registry gives
  one. The fit must pass `prior_sigmas=lambda2_nu=nan,lambda4_nu=nan[,lambda6_nu=nan]`, as the LATCHI/LATFULL commands
  already do.
- **G3** A second lattice term among `fitter.regularizers`, including the old `LatticeCSChi2`.
- **G4** Any μ0-scale systematic requested together with live TNPs. The new term has no μ0 option, so this guard
  belongs in the **old** plugin: refuse `mu0scale` with `pert=live` there.
- **G5** No `SCETlibADParamModel` on the fitter (no SCETlib calculation to share), or a name/slot mismatch between
  `get_x()` and the model.
- **G6** `b0_over_bmax_global != 0` (§3.6).

**6.6 Interface.**

| route | pros | cons |
|---|---|---|
| **(a) rabbit `-r` Regularizer** (as now) | no rabbit change; composes with the wall; gets `get_x()`; path proven under blinding (BLINDFULL, ASIMFULL) | the exp(2τ) un-scaling via the fitter found on the call stack; regularizer-specific rabbit bugs hit it (the walled + saturated + blinded crash); its NLL share is not stored in the fitresult; a likelihood labelled "regularizer" |
| (b) inside `SCETlibADParamModel` | one object owns all SCETlib | rabbit's ParamModel API has no NLL hook, so it needs a rabbit change anyway |
| (c) rabbit "external likelihood plugin" (`--externalLikelihood module.Class args`), added unscaled next to `lext` in `_compute_nll` | first-class likelihood: no τ hack; stored in the NLL breakdown; could own k1 later | a rabbit PR (≈100 lines + tests), review latency, and the stacked-PR CI trap |
| (d) lattice points as a card channel | – | rabbit channels are Poisson, and γ_ζ can be negative: rejected |

**Recommendation: (a) now, with the SCETlib-driven core; (c) as an upstream rabbit follow-up once the method is
final.** The core class is written backend-agnostic (`LatticeCSLikelihood(core=ScetlibGammaNuTF, data, syst)`), so
moving it from (a) to (c) is a thin adapter.

**6.7 Effort and ordering.**

| step | what | effort |
|---|---|---|
| 0 | Luca signs off §8 (analytic-RGE consistency change, the n_f definition, the b_T window default) | – |
| 1 | SCETlib entry point + C++ tests (§3); rebuild; MR | 1 d |
| 2 | `ScetlibGammaNuTF` + second-order tests (§4) | ½ d |
| 3 | WRemnants: data-only npz/json; `scetlib_full_vector_tf` on the param model; the new term `lattice_cs_term.py` (load-time SCETlib computations, guards G1–G6); offline tests V1–V4 | 1–1.5 d |
| 4 | cache-free Newton prediction of LATFULL8 → new term | ¼ d |
| 5 | replay at LATFULL8's vector on the subset cache (V5), BLIND (V6), Asimov (V7); one gated load each, ~1 h | ½ d wall |
| 6 | LATB5 → LATB8 (τ 5 → 8 + Hessian), warm from LATFULL8 (V8) | ~2 h wall, gated |
| 7 | retire the theory arrays from the shipped npz; the old plugin becomes validation-only | ¼ d |

**Total ≈ 3½–4 working days plus about a day of gated fits.** No cache rebuild. No new big-memory job: the term
shares the param model's already-loaded calculation and adds < 1 MB.

### 7. Validation plan (targets that can actually be met)
- **V1, kernel identity.**
  - `gamma_nu_points` vs the `qT::Gamma_nu` class in the cache's (analytic) configuration: ≤ 1e-14, at the anchor and
    displaced points (α_s ± 0.004, θ_cusp/θ_γν ± 2, λ4_ν < 0, tanh_6).
  - Separately, the class with the exact RGE vs `our_cs_kernel.py` / the shipped table: ≤ 1e-11 (done: 1.4e-12).
  - Together these close the chain table ↔ SCETlib to 1e-11 **in each configuration**. The residual analytic − exact
    (≤ 1.9e-3, slope −8.5 %) is the intended change and is reported, not hidden.
  - **The "agree with the table to ~1e-10" target in the task is not reachable by construction.** It would need the
    entry point in exact-RGE mode, which the AD kernel does not have.
- **V2, staging.** The snapshot fields equal the loaded rule's `entry->g`, bitwise (§3.4). `value_pert` at the anchor
  equals the V1 class value.
- **V3, derivatives.**
  - clad gradient vs Richardson FD ≤ 1e-8.
  - Hessian vs FD of the gradient ≤ 1e-7.
  - The TNP–TNP Hessian block is exactly 0: they are affine, as the prototype shows.
  - The Jacobian is exactly 0 outside {alphas, tnp_gamma_nu, tnp_gamma_cusp, np_gnu_*}.
  - Both TF second-order routes vs the analytic composition.
- **V4, term level, offline.**
  - At public α_s (0.116, 0.118, 0.120) and the λ/TNPs of NOMSTIFF, LATCHI8 and LATFULL8: new term vs old term
    (`pert=live`). The difference must equal the old term evaluated with the SCETlib `pert` and derivatives (≤ 1e-10),
    i.e. it must come only from the kernel swap.
  - The lattice-only minimum reproduces §2 (6.703, 0.1855, −0.00597).
- **V5, replay.** LATFULL8's command with the old term swapped for the new one, `--noFit --noHessian --noEDM` at
  LATFULL8's vector (subset cache).
  - The data+BB and prior components must be bitwise unchanged; only the total loss moves.
  - Check that the new SCETlib build reads the cache bit-identically: the same SUBCHK replay with the lattice term
    off gives ΔNLL = 0.
- **V6, blinding.** BLINDCHK A–E analogue on data with blinding armed (§5).
- **V7, Asimov closure.**
  - `ydata=asimov` built from the **SCETlib** kernel at the truth (anchor λ, k1_asimov 0.2);
    `-t 1 --toysDataMode expected --toysDataRandomize none --toysSystRandomize none`;
  - displaced start (α_s θ +1, λ2_ν θ −0.5, λ4_ν θ +0.01, θ_γν +1, θ_cusp −1);
  - every θ back within 1e-6, EDM < 1e-12.
- **V8, LATLIVE8Y / LATFULL reproduce.**
  - New-term fit LATB8 vs LATFULL8: Δ`alphaS` within ±0.01σ_NOM of the step-4 Newton prediction (≈ −0.004σ from the
    slope change, plus the λ-minimum shift); λ2_ν and λ4_ν within 0.1σ; σ ratio within 0.5 %; EDM < 1e-12; same active
    wall face.
  - LATLIVE8Y is reproduced in the same sense through LATFULL8. LATLIVE8Y differs from LATFULL8 only in pert-mode and
    systematic set, both already measured.
  - Blinded differences only.

### 8. Decisions for Luca
1. Accept that the lattice term's perturbative kernel becomes SCETlib's **analytic**-RGE kernel, the one the Z
   prediction uses. It moves the kernel by ≤ 1.9e-3 and the α_s slope by −8.5 % against the table. Recommended: yes.
   That is the consistency option B buys.
2. The n_f alternative defined SCETlib-natively as "identified at 1 GeV", instead of m_b decoupling (§6.3).
3. The b_T window: default on until the theorist answers.
4. Route (a) now, (c) later (§6.6).

---

## Findings

1. SCETlib's AD kernel already contains a clad-differentiable γ_ν (`ad::gamma_nu_resummed`), shared with the cross
   section. A 2-wrapper clad TU gives exact gradient and Hessian. It agrees with `qT::Gamma_nu` to 5e-16, and all 21
   points take < 13 ms. — (evidence: [proto/out_anchor.txt](proto/out_anchor.txt), [proto/out_displaced.txt](proto/out_displaced.txt))
2. **The shipped lattice pert table is the exact-RGE SCETlib kernel (1.4e-12), while the fit's SCETlib runs analytic
   (`cache.conf` `alphas_solution = rge_solution = analytic`).** The difference is ≤ 1.9e-3 in γ_ζ (≤ 0.019 σ_lat) and
   −8.5 % in ∂γ_ζ/∂α_s on the plateau. The lattice-only minimum moves by +0.025σ (λ2_ν), and the live α_s pull scales
   by 0.946 (≈ −0.004σ_NOM). The plugin docstring's "validated to 5e-11" refers to the exact configuration only. —
   (evidence: [compare_table.json](compare_table.json))
3. In the AD kernel the CS TNPs are exactly affine (zero diagonal Hessian), and α_s × TNP cross terms are nonzero. That
   confirms 261006's "TNPs enter exactly linearly" with SCETlib's own derivatives. — (evidence: proto Hessian block in
   [proto/out_anchor.txt](proto/out_anchor.txt))
4. For knowledge/ (SCETlib AD): a new kernel entry point must snapshot `GlobalData` under `s_ad_mutex` (because
   `prepare_point` mutates `_ad().global()`) and save/restore the thread-local `ad_g`. The replay restages each rule
   entry's own `g`, so the snapshot should be checked against `entry->g`. — (evidence: DrellYanAD.cpp:604-618, 653,
   3385; ad_context.cpp:599-633)

---

## Open questions

- **`scetlib_tf_native.py` is stale for CS NP forms other than tanh_2.** Its `_gnu_model` uses the pre-tanh_6 model
  ids: id 2 is frac_1 there but tanh_6 in C++, and 3–6 are shifted. It also has no λ6_ν. `Gamma_nu_formulas.hpp`
  warns about exactly this shift. A native-TF fit with tanh_6 / frac / exp CS forms would silently use the wrong form.
  It does not affect our fits (they use `ScetlibCachedXsecTF` with tanh_2). Not chased.
- The default registry puts a prior on λ2_ν (`params.prior_sigma`). Every lattice fit must override it (G2). Should the
  default change once the lattice term is nominal?
- k1 as a real fit parameter only becomes possible on route (c). Is the analytic profile acceptable for the impacts
  breakdown? (k1 then never appears as an impact.)
