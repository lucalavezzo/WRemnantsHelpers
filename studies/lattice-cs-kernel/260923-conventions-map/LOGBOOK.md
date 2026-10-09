---
title: Lattice CS kernel vs SCETlib gamma_zeta conventions map
slug: 260923-conventions-map
study: lattice-cs-kernel
status: done
created: 2026-09-23
updated: 2026-09-23
owner: study-worker
---

# Lattice CS kernel vs SCETlib γ̃_ζ: conventions map

**Task:** Is the ASWZ 2024 lattice CS kernel γ_q(b_T; μ=2 GeV) ([arXiv:2402.06725](https://arxiv.org/abs/2402.06725)) the same object as SCETlib's full γ̃_ζ(b_T, μ) = pert + NP *as our fits build it*? If not, what exact recipe puts our kernel at the lattice's point (μ, n_f, α_s, order, b*, logs)?

---

## START HERE (status as of 2026-09-23)

> **Same object. Lattice γ_q = SCETlib γ̃_ζ = ½ γ̃_ν (the thing `Gamma_nu::operator()` returns), with no sign change and no
> extra factor. The one real mismatch is the flavour scheme: our fit runs n_f=5 throughout, the lattice is n_f=4.**
> [`our_cs_kernel.py`](our_cs_kernel.py) returns our full kernel at μ = 2 GeV in either scheme. It agrees with SCETlib's own C++ `Gamma_nu` to 5e-11
> (exact RGE) and to ≤1.9e-3 against the analytic RGE the fit uses ([test output](test_our_cs_kernel.txt)).
> For b_T ≥ 0.3 fm the n_f=5 perturbative kernel sits **+0.030** above the n_f=4 one at μ = 2 GeV. The offset depends on μ
> (**−0.012** at μ = 1 GeV). It is about 0.3σ of a single lattice point, but it shifts all points together. The α_s dependence
> is weak: 0.003–0.005 per 0.001 in α_s(m_Z).

- **Next action:** none, task closed. The study's T3 (fit our full kernel to the per-ensemble lattice data) can call
  `our_cs_kernel(..., scheme=...)` directly. Recommended treatment is in [Result §4](#4-recipe).
- **Blocking on:** nothing. Nothing found rules out using the lattice kernel with SCETlib; the caveats are in Result §6.

---

## Log

### 2026-09-23
- Fetched and read 2402.06725, 2506.13874 and 2510.26489 (text dumps in `papers/`; the PDFs are kept off the web dir because one is 12 MB).
- **Scope change from the orchestrator (Luca):** the Cridge–Marinelli–Tackmann (CMT) lattice numbers used in the AN come from a
  non-robust, unpublished study. They are recorded below as an *unverified precedent*, not used as the recipe. The recipe
  here is built from first principles, from the ASWZ paper plus the SCETlib source.
- SCETlib source read at the pinned AD tree `/work/submit/lavezzo/alphaS/scetlib-ad-2da973d/scetlib-cms`. `Gamma_nu.cpp`
  is byte-identical (md5) to `scetlib-cms-newnp-lambda4fix`, `scetlib-ad-260914` and `scetlib-audit-b66f8de`. The header and
  `Scale_provider.cpp` differ only by the refactor into `*_formulas.hpp`, and the physics is unchanged.
- Fit configuration read from `base.conf`. The two copies agree: the AD cache's
  `/ceph/.../scetlib_ad_caches/ntrain_gate/base_1e3.conf` and the theory-correction card
  `TheoryCorrections/SCETlib/com13_ct18z_newnps_n3+0ll_lattice_coarse/base.conf`.
- Wrote a C++ driver ([driver/gamma_zeta_driver.cpp](driver/gamma_zeta_driver.cpp)) against the pinned build. It calls the
  real `qT::Gamma_nu` with the fit's μ0 prescription, NP models and TNPs, and it can dump the β, cusp and γ_ν coefficients.
  Built in the WRemnants container with clang++.
- Wrote [our_cs_kernel.py](our_cs_kernel.py) (numpy/scipy, both flavour schemes) and validated it against the driver
  ([test_our_cs_kernel.py](test_our_cs_kernel.py) → [test_our_cs_kernel.txt](test_our_cs_kernel.txt)). All 9 checks pass.
- Produced the numbers ([analysis_numbers.txt](analysis_numbers.txt)) and one figure with [analysis.py](analysis.py).

---

## Result

**Caveats first.**
(i) The only λ tune shown is the AN / CMT tune (λ∞ = 1.6853, λ2 = 0.0870 GeV², λ4 = 0.0074 GeV⁴). It came from a fit to
the *2023* lattice sets, and its method is unpublished and flagged non-robust. It is used here as a reference curve only.
(ii) The lattice points are the orchestrator's "continuum" csv: per-ensemble points shifted by k1·a/b_T, with raw
per-point errors and **no correlations**. So every χ² quoted below is indicative only; the refit belongs to the sibling task `260923-lattice-data-refit`.
(iii) All of our numbers are at N3LL (= N3+0LL with TNPs θ = 0), α_s(m_Z) = 0.118, with the fit's scale settings.

### 1. Convention map

| quantity | lattice (ASWZ 2402.06725) | SCETlib, as our fits build it | conversion / evidence |
|---|---|---|---|
| definition | γ_q = 2 d ln f / d ln ζ (Eq. 1) | `Gamma_nu::operator()` returns γ̃_ν. The TMD evolution is exp[½ γ̃_ζ ln(ζ/ζ0)] (CMT Eq. 3.25), so γ̃_ζ = 2 d ln f/d ln ζ = ½ γ̃_ν (CMT Eq. 3.26) | **γ_q = γ̃_ζ = ½ γ̃_ν.** Verified by coefficients: ½·C_F·γ_ν^(1) = 14.93 + 5.53 n_f = −2·d2 of the lattice paper (Suppl. Eq. 25). Verified by μ-dependence: d γ̃_ζ/d ln μ = −2Γ_cusp with Γ0 = 4C_F, which the test reproduces to 4e-8. Also equals Collins K̃ and −2D (ASWZ Eq. 6 uses −2D_res − 2D_NP). 2510.26489 plots its K directly against the lattice points (Fig. 2) |
| sign / normalisation of NP piece | — | γ̃_ν^NP = −λ∞ tanh(λ2 b²/λ∞ + λ4 b⁴/λ∞ [+ λ6 b⁶/λ∞]) (`Gamma_nu.hpp:84-123`, newer tree `Gamma_nu_formulas.hpp`) | **γ̃_ζ^NP = −(λ∞/2) tanh(…)**, as in AN `theory.tex` Eq. (npgamma). The λ are in γ_ν units, so the small-b_T limit is γ̃_ζ^NP ≈ −(λ2/2) b_T² |
| scheme | MS-bar (RI/xMOM converted to MS-bar, Eq. 2) | MS-bar | same |
| μ | 2 GeV (Fig. 1 panel labels; Suppl. "α_s(μ0 = 2 GeV)") | any μ: `operator()(bT, mu0, mu)` is FO(μ0) plus cusp evolution μ0→μ | evaluate our kernel at μ = 2 GeV. The NP piece does not depend on μ |
| n_f | 4: 2+1+1 HISQ sea with physical masses, massless n_f = 4 matching (Suppl. "n_f = 4", N_m = 0.552 for n_f = 4) | **5, fixed flavour**, massless, no thresholds (`base.conf nf = 5`; `RunningCoupling` is fixed-n_f) | n_f = 4 everywhere, with α_s^(4) from α_s^(5)(m_Z) via decoupling at m_b(m_b). This is `scheme="lattice"`; `scheme="fit"` reproduces the fit |
| α_s | α_s^(4)(2 GeV) = 0.293, used only in the matching δγ and in their parametrisation | α_s^(5)(91.1876) = 0.118 (runcard; a fit parameter in scetlib_ad), 4-loop running at `alphas_order = n3ll`, analytic solution, Landau regulator off (`lambda = 0`) | α_s^(5)(2) = 0.2901, α_s^(4)(2) = 0.3015. **0.293 corresponds to α_s(m_Z) = 0.1168** |
| perturbative order | data points: matching at uNNLL + LRR (independent of how D_res is written). Their fitted curve: D_res at N3LL | N3+0LL: γ_ν boundary constant through α_s³, cusp through Γ3 (4 loops), 4-loop β. The TNPs θ_γν (added to the 3-loop constant) and θ_cusp (added to Γ3) are fit parameters (`variations.py:make_tnps`) | compare the data points, which do not depend on D_res, with our kernel at *our* order |
| treatment of large b_T in the pert kernel | only in their fitted curve: D_res(b*, μ), Eq. 8 with B_NP = 2 GeV | FO boundary at **μ0 = ((b0/b_T)⁴ + (1 GeV)⁴)^¼** (`Scale_provider.cpp:34,49`, collins_soper4, `mu0_min = 1`, `b0_over_bmax = 0`). Logs L_b = ln(μ0² b*²/b0²) with the **sextic b\***, b0/b_max = 1 GeV (`Gamma_nu.cpp:102-103`, `bStar` at `Gamma_nu.hpp:79-82`). NP piece at **bare b_T** (`Gamma_nu.cpp:117`) | for the data points, nothing to convert. **Never reuse their (B_NP, c0).** Their NP piece is defined relative to *their* D_res, and ours relative to *ours* (CMT p. 19–20) |
| b_T units | fm | GeV⁻¹ | 1 fm = 5.0677 GeV⁻¹ |
| discretisation | per ensemble: γ(b_T, a) = γ_cont + k1 a/b_T (+ k2 a²/b_T²), Eq. 6 | — | handled on the data side (sibling task) |

### 2. How SCETlib evaluates the perturbative kernel at large b_T (Q1)

It is **neither pure fixed order at μ_b nor frozen b\* alone. It is a fixed-order boundary at a floored scale, followed by
resummed cusp evolution** (`Gamma_nu.cpp:82-120`):

γ̃_ν = −4 ∫_{μ0}^{μ} Γ_cusp[α_s] d ln μ′ + C_F Σ_n a_s(μ0)^{n+1} γ_ν^{(n)}(L_b) + γ̃_ν^NP(b_T)

The pieces are as follows.
- The boundary scale μ0 is the b_T-space canonical scale b0/b_T, floored at 1 GeV by the quartic form. It goes 2.24 → 1.26 → 1.07 → 1.01 → 1.001 GeV at b_T = 0.1 / 0.2 / 0.3 / 0.45 / 0.9 fm.
- The log L_b uses the sextic b\*, not b_T. At large b_T, L_b → ln(1 GeV² · 1 GeV⁻²) = 0; in the transition region (0.1–0.3 fm) it is small and nonzero, because the quartic floor and the sextic b\* do not coincide.
- The evolution μ0 → μ is resummed (analytic re-expanded solution by default).

At b_T = 0.9 fm (μ_b = b0/b_T = 0.25 GeV) the boundary therefore sits at **α_s^(5)(1.0 GeV) = 0.406 with L_b ≈ 0**. It is
never evaluated at 0.25 GeV. The consequence is that **for b_T ≳ 0.3 fm the perturbative kernel is flat** at
−0.178 (n_f=5) / −0.208 (n_f=4) at μ = 2 GeV. All the b_T dependence of our full kernel across the lattice window 0.3–0.9 fm
comes from the NP tanh. The nominal order is N3+0LL (run order N3LL, above). N4+0LL adds the 4-loop γ_ν constant; SCETlib's
exact RGE solvers stop at N3LL (`BetaRGESolverNumeric` throws), so N4LL only runs with the analytic solution.

### 3. n_f and α_s (Q2)

| μ [GeV] | α_s^(5) (fit) | α_s^(4) (4-loop, 3-loop decoupling at m_b(m_b) = 4.18) |
|---|---|---|
| 1.00 | 0.4065 | 0.4611 |
| 1.25 | 0.3591 | 0.3916 |
| 2.00 | 0.2901 | **0.3015** |

- The lattice value α_s^(4)(2 GeV) = 0.293 is **not** what α_s(m_Z) = 0.118 gives (0.3015). It corresponds to
  **α_s(m_Z) = 0.1168**, about 1.3× the PDG uncertainty below the world average. Moving the threshold to 4.0 or 4.78 GeV
  changes α_s^(4)(2) by −0.0007 / +0.002, so this is not a threshold-convention effect. The value enters only their
  O(α_s) matching δγ (and their D_res curve). Its impact on the data points is not quantifiable from the paper (see Open questions).
- Evaluating our kernel consistently with the lattice needs n_f = 4 in *all three* places: the β function, the cusp, and
  the boundary coefficients (`_COEFFS[4]` in the module). The coupling must be decoupled at m_b. Flipping `nf` alone
  and restarting 0.118 at m_Z is wrong.
- The size of the flavour-scheme difference (pert only, μ = 2 GeV) is:

| b_T [fm] | 0.1 | 0.15 | 0.2 | 0.3 | 0.45–0.9 |
|---|---|---|---|---|---|
| pert, n_f=5 (fit) | +0.058 | −0.050 | −0.122 | −0.171 | −0.178 |
| pert, n_f=4 (lattice scheme) | +0.059 | −0.060 | −0.142 | −0.201 | −0.208 |
| n_f5 − n_f4 at μ = 2 GeV | −0.001 | +0.010 | +0.021 | +0.029 | **+0.030** |
| n_f5 − n_f4 at μ = 1 GeV | −0.043 | −0.032 | −0.022 | −0.013 | −0.012 |

  The difference is well below one lattice error per point (≈0.1). But it is coherent across points, and its size and even its
  sign depend on the μ at which one asks for n_f5 = n_f4. That μ-dependence is the honest measure of the scheme ambiguity.

### 4. Recipe

To put our kernel at the lattice point, call
`our_cs_kernel(bT_fm, lambdas, alphas_mz, mu=2.0, scheme=..., order="n3ll", np_model_nu=..., tnp_nu=θ_γν, tnp_cusp=θ_cusp)`.
The call does four things:
1. It converts b_T from fm to GeV⁻¹ (×5.0677).
2. It computes μ0 = ((b0/b_T)⁴ + 1)^¼ GeV and L_b = 2 ln(μ0 · b\*/b0), with the sextic b\* at b0/b_max = 1 GeV. These are exactly the fit's settings; changing them changes what "NP" means.
3. It computes ½[−4η_Γ(μ0→2 GeV) + C_F Σ a_s(μ0)^{n+1} γ_ν^{(n)}(L_b)] at N3LL, with the TNPs.
4. It adds ½γ̃_ν^NP(λ; bare b_T) and compares the sum to the lattice data points (data only, never their fitted D_NP).

`scheme="fit"` (n_f = 5) is what the fit's cross section uses. `scheme="lattice"` (n_f = 4, decoupled α_s) is the lattice's
flavour scheme.

**Recommendation.** Our λ are defined relative to the n_f=5 perturbative kernel, so a constraint that feeds our fit should use
`scheme="fit"` as the prediction. The flavour mismatch should enter as one fully correlated systematic with shape
`pert_fit − pert_lattice` at μ = 2 GeV (+0.030 flat above 0.3 fm). Cross-check it with the μ = 1 GeV version (−0.012), which has the opposite sign.
This extends `knowledge/30_physics_global/np_parametrization_constraints.md` §19 step 4 with a proper decoupling instead of a bare `nf` flip.

### 5. α_s dependence of the perturbative part (Q3)

∂γ̃_ζ^pert/∂α_s(m_Z) at μ = 2 GeV (central finite difference, ±0.001):

| b_T [fm] | 0.1 | 0.2 | 0.3 | 0.45 | 0.6 | 0.9 |
|---|---|---|---|---|---|---|
| fit scheme (n_f=5) | +2.1 | −1.9 | −3.0 | −3.0 | −2.9 | −2.9 |
| lattice scheme (n_f=4) | +2.3 | −3.1 | −4.6 | −4.5 | −4.4 | −4.3 |

So δα_s(m_Z) = 0.001 moves the kernel by **0.003–0.005** over 0.2–0.9 fm, about 1/20–1/30 of one lattice error.
Translated into λ2 via γ̃_ζ^NP ≈ −(λ2/2) b² at 0.45 fm, that is δλ2 ≈ 0.0015 per 0.001 in α_s, against σ_lat(λ2) ≈ 0.03 (AN).
**A lattice term on the full kernel therefore correlates only weakly with α_s directly.** Any α_s–λ_ν correlation in the fit will
come from the qT spectrum, not from the lattice term.

Other perturbative sensitivities at b_T ≥ 0.3 fm, for comparison:
- θ_γν = 1 gives +0.006;
- θ_cusp = 1 gives ≤ 0.001;
- N4LL − N3LL = +0.014;
- NNLL − N3LL = −0.024.

The order dependence of the kernel is therefore about 0.015, which is comparable to the n_f mismatch.

### 6. Incompatibilities / what could block using the lattice kernel

None of these blocks the comparison; each is a caveat to state.
1. **Flavour scheme (n_f 5 vs 4):** quantified above, ≤ 0.03 and coherent. Treat it as a correlated systematic.
2. **Charm:** the lattice has massive physical charm in the sea but massless n_f=4 matching, while we have massless charm
   everywhere. Below μ ~ m_c neither side is right. That is the lattice's systematic and our NP absorbs it. The effect is not quantified here (it would
   need an n_f 4→3 threshold between μ0 = 1 GeV and m_c, which the module does not implement). CMT say a proper
   massive-quark treatment is "essential" and cite Dehnadi–Ploessl–Tackmann, which is still unpublished.
3. **The lattice's α_s (0.293 ↔ 0.1168)** enters their matching. The effect on the points is unknown and probably small (see Open questions).
4. **Their fitted parametrisation is not transferable.** (B_NP, c0) and g2 (2510.26489) are defined relative to their own
   D_res(b*, B_NP) at N3LL with n_f=4 and α_s = 0.293. Only the data points are convention-free.
5. **The shape of our perturbative kernel is flat above 0.3 fm** (μ0 floor). So a lattice fit of our λ constrains how NP(b_T) differs from
   its value at 0.3 fm, together with a constant pert-level offset. That offset is exactly where items 1–3 live.

### 7. Unverified precedent: Cridge–Marinelli–Tackmann (2506.13874), not robust

CMT §3.3 (pp. 19–22) fit SCETlib's tanh form (their Eq. 3.32) to the 2023 lattice sets [89–91], "Using Ref. [66]"
(Dehnadi–Ploessl–Tackmann, unpublished) to handle flavour thresholds and quark masses. The result is their Eqs. 3.34–3.35, which is
the AN's tune. They state the sextic b\* (Eq. 3.30, b0/b_max = 1 GeV) but *not* the order, μ, n_f or α_s used against the
lattice. **Not reverse-engineered, per scope.**

### 8. 2510.26489 lattice-spacing treatment (Q4)

This paper uses the same ASWZ data at two levels.
- **(a) Continuum csv:** 21 points, uncorrelated χ² (their Eq. 7).
- **(b) Per-ensemble data:** n = 6 / 7 / 8 points for a = 0.15 / 0.12 / 0.09 fm, each set with its own covariance Σ_i. The prediction is shifted by replacing g_K → g_K − k1 a/b − k2 a²/b² (Eq. 12). Equivalently K_latt(a) = K_cont + k1 a/b + k2 (a/b)², with k1 and k2 **shared across ensembles**.
- **Reweighting:** k1 ~ N(0.22, 0.08) is taken from ASWZ, and k2 ~ N(0, 0.1) is a hand-assigned width, because ASWZ dropped k2 by AIC. Both are sampled per replica. The posteriors of k1 and k2 come back equal to their priors. g2 = 0.165 ± 0.020 (finite-a), in agreement with 0.164 ± 0.020 (continuum).
- **Simultaneous fit:** 482 DY + 21 lattice points with full Σ_i, g2 = 0.167 ± 0.015. The letter does not say whether k1 and k2 float or are sampled in that fit. Their K is plotted at μ = 2 GeV, and n_f/α_s for the MAP perturbative K are not stated in the letter.

### Figure

![Our full CS kernel at mu=2 GeV (AN tune, nf=4 solid / nf=5 dashed) and perturbative-only kernel, against the ASWZ 2024 a/bT-corrected lattice points](cs_kernel_ours_vs_lattice.png)

*Caveats for this figure:*
- The AN tune is the CMT 2023-lattice fit, which is unverified and not robust.
- The lattice points are the csv: a/b_T-shifted, raw errors, no correlations.
- The curves are N3LL, α_s(m_Z) = 0.118.

Diagonal χ² of the AN tune against the 21 csv points is 11.1 (n_f=4) / 10.9 (n_f=5), and 88 for perturbative-only. This is indicative only (see caveat ii).
The AN tune already describes the new data reasonably well, and the n_f=4 vs n_f=5 curves differ by far less than the data errors.

---

## Findings

1. Lattice γ_q ≡ SCETlib γ̃_ζ = ½ × `Gamma_nu::operator()`, with the same sign. The NP part is γ̃_ζ^NP = −(λ∞/2) tanh(…) with λ in γ_ν units — (evidence: 2402.06725 Eq. 1 + Suppl. Eq. 25; 2506.13874 Eqs. 3.25–3.26; `Gamma_nu.cpp:82-120`; test d/dlnμ check in [test_our_cs_kernel.txt](test_our_cs_kernel.txt)).
2. SCETlib's perturbative CS kernel at large b_T uses FO at μ0 = ((b0/b_T)⁴ + 1 GeV⁴)^¼ with a sextic-b\* log, followed by resummed cusp evolution. It is flat for b_T ≳ 0.3 fm (−0.178 at μ = 2 GeV, n_f = 5) — (evidence: `Scale_provider.cpp:34,49`, `Gamma_nu.cpp:102-117`, `base.conf`; [analysis_numbers.txt](analysis_numbers.txt)).
3. Flavour-scheme mismatch n_f=5 (fit) vs n_f=4 (lattice): +0.030 at μ = 2 GeV and −0.012 at μ = 1 GeV, flat for b_T ≥ 0.3 fm — (evidence: [analysis_numbers.txt](analysis_numbers.txt)).
4. ∂γ̃_ζ^pert/∂α_s(m_Z) ≈ −3 (n_f=5) / −4.5 (n_f=4) over 0.3–0.9 fm. A lattice constraint barely correlates with α_s — (evidence: same).
5. The lattice's α_s^(4)(2 GeV) = 0.293 corresponds to α_s(m_Z) = 0.1168. At 0.118 the value is 0.3015 — (evidence: same).
6. `our_cs_kernel.py` reproduces SCETlib's C++ Gamma_nu to 5e-11 (exact RGE, both n_f, TNPs, tanh_2/tanh_6) and to ≤ 1.9e-3 against the fit-default analytic RGE — (evidence: [test_our_cs_kernel.txt](test_our_cs_kernel.txt)).
7. For the knowledge curator: `np_parametrization_constraints.md` §19 says μ_b is "floored at 1 GeV" by the sextic b\*. In fact two prescriptions act, the quartic μ0 floor (`mu0_min = 1`, collins_soper4) and the sextic b\* inside L_b, and at 0.2 fm they give 1.26 GeV vs 1.19 GeV. §19 step 4 should also say that n_f = 4 needs decoupled α_s AND n_f = 4 coefficients.

---

## Open questions

- How much does the lattice's α_s = 0.293 (vs 0.3015) move the lattice points through the uNNLL matching δγ? Ask the ASWZ authors, or rerun their matching.
- Charm threshold: nobody has quantified the n_f 4→3 effect between μ0 = 1 GeV and m_c, and our Coupling class has no multi-threshold η integration.
- Table I of 2402.06725 lists 0 ≤ b_T/a ≤ 7, which gives at most 0.63 fm at a = 0.09. The csv has an 8th a = 0.09 point at 0.72 fm. The sibling data task should check this.
- N4LL in the python module omits the 5-loop cusp and agrees with SCETlib's analytic N4LL to 1.1e-3. That is fine for a cross-check but was not validated further.
- In 2510.26489's simultaneous fit, do k1 and k2 float? The letter does not say.
