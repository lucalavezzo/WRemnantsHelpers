---
title: Fit our SCETlib CS-kernel NP form to ASWZ lattice data
slug: 260923-scetlib-kernel-fit
study: lattice-cs-kernel
status: done        # active | done | paused | abandoned
created: 2026-09-23
updated: 2026-09-24
owner: study-worker
---

# Fit our SCETlib CS-kernel NP form to ASWZ lattice data

**Task:** What constraint does the ASWZ per-ensemble lattice CS-kernel data (arXiv:2402.06725) put on our SCETlib CS-kernel NP parameters (λ2_ν, λ4_ν, λ∞_ν, optionally λ6_ν) when we fit our full kernel plus lattice-spacing terms? How does it compare with our real-data Z postfit λ_ν and with the Tackmann/Cridge values in the AN?

---

## START HERE (status as of 2026-09-23, late)

> **NEW (λ4_ν = 0 refit, Luca's request).** The AD cache and the tanh_2 form break for λ4_ν < 0, so the fits must run with λ4_ν = 0. With λ4_ν = 0 and λ∞_ν = 2 frozen, fitting λ2_ν + k1 gives **λ2_ν = 0.1345 ± 0.020 (stat) ± 0.024 (syst) = ± 0.031 (tot) GeV²**, at χ²/ndf = 8.59/19.
> Freezing λ4_ν costs **Δχ² = 1.87** against the free-(λ2_ν, λ4_ν) fit (1.4σ). The card anchor, λ2_ν = 0.15, is +0.5σ from the constraint. The Tackmann λ2_ν centre of 0.087, placed on the λ4_ν = 0 slice, is −1.5σ (tot). The Gaussian conditional of the 2D fit, 0.108 ± 0.023, sits 0.9σ below this direct refit. Details are in Result §6.

The original result, unchanged:

> **The lattice data are well described by our full kernel (χ²/ndf = 6.7/18). With λ∞_ν frozen at 2, as in the fits, they give λ2_ν = 0.184 ± 0.038 GeV² and λ4_ν = −0.0059 ± 0.0033 GeV⁴ (ρ = −0.88). Systematics add about ±0.03 to λ2_ν.**
> The lattice data agree with the Tackmann/AN tune in kernel space (Δχ² = 3.2, 0.9σ) and with our card's own anchor, λ2_ν = 0.15 (1.0σ). **They are strongly incompatible with every current scetlib_ad real-data Z postfit:** Δχ² = 34 to 203, which is 5.5σ to 14σ.
> The two unwalled minima have an *anti-damping* CS kernel. The walled minima either switch the NP kernel off, or saturate it at its cap by 0.6 fm.
> Recommendation: an exact lattice χ² regularizer on λ_ν with k1 profiled, not a conditional Gaussian. Nothing was implemented.

- **Next action:** none. Task closed. Whether to use the constraint in-fit is the orchestrator's and Luca's call; see Result §5.
- **Blocking on:** nothing. The error model assumes no cross-ensemble correlations, which is an open author question, Q4.

---

## Log

### 2026-09-24: comparison figure for the email to the lattice authors (Luca)
- `email_plot.py` → [email_lattice_comparison.png](email_lattice_comparison.png) / `.pdf` (save_plot, plain label, no CMS logo).
  - ASWZ side: imported from `../260923-lattice-data-refit/cs_fit.py`, which now has the d_n index fix. The (c0,k1) reproduction gives c0 = 0.0324(60) and k1 = 0.2130(663), χ² = 7.32/19.
  - Our side: the l4zero nominal, λ2_ν = 0.1345 ± 0.031, with its own k1 = 0.21. The free-(λ2_ν, λ4_ν) fit is the thin dashed line.
- The two parametrizations agree within bands out to about 0.7 fm. Beyond that, ours with λ4_ν = 0 damps harder, while the free-λ4_ν fit turns over.

![ASWZ per-ensemble points minus k1 a/b_T (their k1=0.213), their Eq. (6)-(8) at a=0 with our-refit and paper-quoted c0 bands, and our SCETlib tanh_2 kernel at the lambda4_nu=0 fit](email_lattice_comparison.png)

*Caption:* γ_q(b_T, μ = 2 GeV). The lattice points are shown with k1·a/b_T subtracted using ASWZ's fitted k1 = 0.213; our fit has its own k1 = 0.21, so the points are exactly continuum points only under their k1. The error bars are the diagonal of the per-ensemble covariance, which is block-diagonal, with no cross-ensemble correlations. Our kernel is n_f = 5 against the lattice's n_f = 4, a scheme offset of at most 0.03. The band on our kernel is λ2_ν stat+syst.

### 2026-09-23 (late): λ4_ν = 0 refit (Luca, via the orchestrator)
- The AD cache and tanh_2 fail for λ4_ν < 0: bin-to-bin oscillation at low qT, σ < 0 near −0.007, and anti-damping beyond about 1.1 fm. So the fits run at λ4_ν = 0, and this task refits the lattice data with λ4_ν = 0 fixed.
- `l4zero.py` → [l4zero_output.txt](l4zero_output.txt), `fit_l4zero.json`, `bands_l4zero.npz`, `chain_l4zero.npy`. These are separate files: `fit_results.json` is read by `260923-lattice-fits/scripts/inject_aswz_cs_prior_theta.py`, so I left it untouched and checked it by md5. `compat.json` is also unchanged.
- `plot.py --only l4zero` → [kernel_space_l4zero.png](kernel_space_l4zero.png). This is a new function in the existing script; the earlier figures were not regenerated.
- The systematic follows the injector's construction: one shift per group (n_f scheme; k-form; b_T window), taking the larger shift in each group, and summing δδᵀ. In 1D that is a quadrature sum.

### 2026-09-23
- Read the study START HERE, the conventions-map and lattice-data-refit logbooks, and knowledge `np_parametrization_constraints.md` §10–12 and §18–20.
- **Postfit source (course correction from the orchestrator):** I first read eleven Aug-2026 `scetlib_np` fits from `np-wall-local-minima/runs_new.yaml`, `read_postfits.py` → `postfits.json`. Those fits are **superseded and not used in the comparison**. For the record, their lat-cov keepers sit at λ2_ν ≈ 0.044, λ4_ν ≈ 0.015 (λ∞_ν = 1.6853), and the prior-free walled ones at λ2_ν ≈ 0.005.
  - Switched to the latest scetlib_ad real-data fits of card A (`studies/alphas-scan-discontinuity`), read by `read_ad_postfits.py` → `ad_postfits.json`.
- **scetlib_ad λ are not stored physically.** They are stored as θ, with physical = anchor + width·θ (`scetlib_ad/params.py` REPARAM). The widths are 0.10 for λ2_ν and 0.50 for λ4_ν. The anchor is `cache.conf [Nonperturbative]`: λ2_ν = 0.15, λ4_ν = 0, λ∞_ν = 2 (tanh_2).
  - The `scetlib_np` reader `fitresult_lambdas.py` returns `parms` values as physical and knows nothing of REPARAM. On these files it would report θ (λ2_ν = −2.41) as λ, so I wrote a minimal reader instead.
  - The mapping was checked against the study logbook: the unwalled second minimum has λ2_ν = −0.083 and CCWALLSHIFT has +0.0025, both matching `alphas-scan-discontinuity` Q7.
- Fits in `kernel_fit.py` → [fit_output.txt](fit_output.txt), `fit_results.json`. The pert kernel comes from `our_cs_kernel.py` (n_f=5, μ=2 GeV, N3LL, α_s(m_Z) = 0.118). The data come from `cs_fit.py::load()`, per-ensemble with a block-diagonal covariance.
- Compatibility and MCMC posteriors in `compare.py` → [compat.txt](compat.txt), `compat.json`, `bands.npz`, `chain_*.npy`.
- Plots in `plot.py`, run in the container with the `scetlib-np-param-model` worktree (`wtree`, `/home/submit/lavezzo/alphaS/WRemnants-scetlib-np-param-model`) on PYTHONPATH.
  - Reused: `wums.plot_tools.figure`/`add_cms_decor`, `scetlib_np.plot_output.save_plot`, and from `np_function_plots` its `_band` and its `LATTICE_CS_MU/COV` constants. The script asserts those constants equal the AN numbers.
  - `np_function_plots` draws the NP part only, so the full kernel adds the `our_cs_kernel` pert table on top. No new NP-function plotter was written.

---

## Result

### Caveats first
1. **Error model.** The per-ensemble covariances are block-diagonal, and **no cross-ensemble correlations** are included (they are unknown; author question Q4). χ²/ndf is about 0.37 for every good fit, so the lattice errors look conservative, or correlated in a way the blocks do not show. The Δχ² and σ-equivalents below are therefore probably *under*-stated rather than over-stated.
2. **Scheme.** Our kernel is n_f=5 fixed-flavour, N3LL, with α_s(m_Z) = 0.118 fixed, the fit's μ0 floor and sextic b\*, at μ = 2 GeV. The lattice is n_f=4. The pert(n_f5) − pert(n_f4) offset is +0.030 flat above 0.3 fm; identifying the two schemes at μ = 1 GeV instead gives a −0.042 shift. Both are treated as variants below.
3. **Postfits.** These are the scetlib_ad card-A real-data fits.
   - The fit freezes λ∞_ν at 2, uses tanh_2 on the CS side, and applies Gaussian priors λ2_ν ~ N(0.15, 0.10) and λ4_ν ~ N(0, 0.5), because priors are on by default in `SCETlibADParamModel` and |θ| = 1 is 1σ.
   - No λ is frozen other than λ∞_ν (`freezeParameters []`).
   - **The λ are not blinded.** Only α_s is, and it is neither read nor quoted here.
   - The Tackmann tune has λ∞_ν = 1.6853. So λ-space comparisons between it and the postfits are across different λ∞_ν slices. **Kernel space is the fair comparison.**
4. The lattice χ² here constrains only our full kernel over 0.09–0.9 fm. λ∞_ν is extrapolation past about 0.9 fm (see §1).

### 1. Fit table (21 points, our kernel + lattice-spacing terms, full block cov)

| config | χ²/ndf | AIC | λ∞_ν | λ2_ν [GeV²] | λ4_ν [GeV⁴] | λ6_ν | k1 / k2 |
|---|---|---|---|---|---|---|---|
| tanh_2, λ∞ free, k1 | 6.46/17 | 14.46 | → ∞ (bound 50) | 0.176(48) | −0.0062(24) | – | k1 0.236(73) |
| tanh_2, λ∞ free, k2 | 7.02/17 | 15.02 | 1.14(26) | 0.073(84) | +0.013(18) | – | k2 0.210(78) |
| tanh_2, λ∞ free, k1+k2 | 6.31/16 | 16.31 | → ∞ | 0.189(90) | −0.0069(37) | – | 0.35(41) / −0.12(41) |
| tanh_2, λ∞ free, no k | 14.07/18 | 20.07 | 1.02(16) | −0.048(89) | +0.039(23) | – | – |
| **tanh_2, λ∞ = 2, k1** (fit config) | **6.71/18** | 12.71 | 2 | **0.184(38)** | **−0.0059(33)** | – | k1 0.241(70) |
| tanh_2, λ∞ = 1.6853, k1 (old lat-cov config) | 6.86/18 | 12.86 | 1.6853 | 0.185(43) | −0.0054(40) | – | k1 0.242(72) |
| tanh_2, λ4 = 0, λ∞ free, k1 | 6.82/18 | 12.82 | 1.32(34) | 0.163(39) | 0 | – | k1 0.232(71) |
| tanh_2, λ4 = 0, λ∞ = 2, k1 | 8.59/19 | **12.59** | 2 | 0.135(20) | 0 | – | k1 0.209(67) |
| tanh_6, λ∞ free, k1 | 6.33/16 | 16.33 | 1.6(2.6) | 0.14(14) | 0.005(44) | −0.0005(18) | k1 0.220(86) |
| tanh_6, λ∞ = 2, k1 | 6.34/17 | 14.34 | 2 | 0.148(71) | 0.002(13) | −0.0003(5) | k1 0.224(76) |

The errors are Hessian errors. The MCMC posteriors (flat priors) at λ∞ = 2 give λ2_ν = 0.173 [0.129, 0.215] and λ4_ν = −0.0044 [−0.0080, +0.0005] at 68 %, with ρ = −0.88. That is mildly non-Gaussian, from the tanh saturation. If the physical region λ2_ν, λ4_ν ≥ 0 is imposed, the result is λ2_ν = 0.113 ± 0.031 and λ4_ν = 0.0037 ± 0.0034.

**What the data decide:**
- **λ∞_ν is not needed and not determined** ([profile](profile_linf.png)). The profile χ² is flat within 0.5 from λ∞ ≈ 1.1 to ∞. The lattice gives only a lower bound: Δχ² = 1 at λ∞ ≈ 1.0 and Δχ² ≈ 4 at about 0.8. Freezing it at 2 or at 1.6853 costs Δχ² ≤ 0.4.
  - The free-λ∞ best fit runs to ∞ with λ4_ν < 0. That is a *turnover*: the NP kernel peaks near 0.75 fm and becomes anti-damping past about 1.05 fm, driven by the 0.9 fm L32 point. It is not significant: forcing λ4_ν = 0 costs Δχ² = 0.36 with λ∞ free and 1.9 with λ∞ = 2.
- **tanh_6 is not needed.** It gains Δχ² of 0.13 to 0.37 for one extra parameter, raises the AIC by 1.6 to 1.9, and leaves λ6_ν consistent with 0 at ρ(λ4, λ6) = −0.97.
- **k1 is preferred over k2**, by Δχ² 0.56 with λ∞ free and 1.26 with λ∞ = 2. k1 + k2 does not improve the AIC. k1 = 0.24 ± 0.07 agrees with ASWZ's own 0.22(8), and without any k the χ² doubles (14.1).
- **Flat directions.** At λ∞ = 2 the softest scaled-Fisher eigenvalue is 0.45, along (λ2_ν ↑, λ4_ν ↓, k1 ↓). That is the usual λ2/λ4 trade-off, not a true flat direction. With λ∞ free, the λ∞ direction is flat (see the profile). With tanh_6, λ4/λ6 are degenerate (0.24).
- **We follow the lattice shape** over 0.2–0.9 fm ([per-ensemble fit](lattice_fit_per_ensemble.png)). The perturbative kernel is flat above 0.3 fm, so all of that shape comes from the tanh, and a single b² term (λ2_ν only, λ∞ = 2) already gives χ² = 8.6/19.

### 2. Systematics (λ∞_ν = 2, tanh_2, k1 unless stated)

| variant | λ2_ν | λ4_ν | χ²/ndf |
|---|---|---|---|
| nominal | 0.184(38) | −0.0059(33) | 6.71/18 |
| n_f = 4 scheme | 0.167(37) | −0.0051(32) | 6.97/18 |
| n_f matched at μ = 1 GeV | 0.167(37) | −0.0052(32) | 7.03/18 |
| drop b_T < 0.2 fm | 0.192(55) | −0.0064(39) | 4.67/14 |
| k2 only | 0.148(34) | −0.0038(31) | 7.97/18 |
| k1 + k2 | 0.212(65) | −0.0074(42) | 6.41/17 |
| n_f syst δδᵀ added to cov | 0.186(42) | −0.0060(34) | 6.70/18 |

- **Spread in λ2_ν: −0.037 / +0.028**, comparable to the statistical error. The k-model choice dominates; the n_f scheme gives −0.017.
- λ4_ν ranges from −0.0074 to −0.0038.
- In kernel space the variants all sit inside the λ∞ = 2 band ([NP-part variants](np_part_variants.png)).
- The n_f systematic, folded into the covariance, inflates σ(λ2_ν) by only 10 %.

### 3. Comparison in kernel space (the fair one)

![Full CS kernel gamma_zeta(b_T, mu=2 GeV): lattice points (continuum-shifted by fitted k1), lattice-fit bands (blue), Tackmann/AN band (grey), and five scetlib_ad real-data Z postfits](kernel_space_comparison.png)

*Caveats for this figure:*
- The lattice points are the per-ensemble values shifted by the *fitted* k̂1·a/b_T (k̂1 = 0.24). The k1 uncertainty, fully correlated and about ±0.07·a/b_T, is not in the error bars. The fits themselves use the raw points with k1 floated.
- The bands are 68 %. The lattice bands are MCMC posteriors with flat priors, and "λ∞ free" means a flat prior on (0.05, 20].
- The postfit bands come from each fit's own Hessian over (λ2_ν, λ4_ν), with λ∞_ν = 2 frozen. They ignore the correlations of the CS λ with the TMD λ, which are sizeable: ρ(λ2_ν, λ2) runs from −0.17 to −0.86.
- Everything is n_f = 5, N3LL, α_s(m_Z) = 0.118. The block-diagonal lattice covariance applies (caveat 1).

**NP part γ_ζ^NP at b_T = 0.45 fm (68 %):**

| | value |
|---|---|
| lattice, λ∞ = 2 | −0.375 [−0.430, −0.318] |
| Tackmann/AN | −0.305 [−0.331, −0.276] |
| card anchor | −0.371 |
| unwalled main | **+0.218** (anti-damping) |
| walled main | −0.533, saturating to the cap −1.0 by 0.6 fm |
| walled cold-resumed | −0.018 |
| walled from 2nd | +0.002 |

**Compatibility with the lattice data** (tune fixed, k1 floated; Δχ² vs the best fit):

| tune | λ∞/λ2/λ4 | χ² (21 pts) | Δχ² vs free best (3 dof) | Δχ² vs best at same λ∞ (2 dof) | χ² incl. tune cov |
|---|---|---|---|---|---|
| Tackmann/Cridge (AN) | 1.6853/0.0870/0.0074 | 9.65 | 3.19 (0.9σ) | 2.79 (1.2σ) | 8.42 |
| card anchor (FranksVals) | 2/0.15/0 | 9.08 | 2.62 (0.7σ) | 2.37 (1.0σ) | – |
| unwalled main min, warm, CCKRYLOVWARM | 2/−0.0907/0.00107 | 209.8 | 203 (13.9σ) | 203 (14.0σ) | 193.6 |
| unwalled 2nd min, cold, CCCOLDSELF | 2/−0.0830/0.00091 | 198.6 | 192 (13.5σ) | 192 (13.6σ) | 153.7 |
| walled main, warm, CCWALLWARMPF | 2/0.0045/0.0434 | 40.6 | 34.2 (5.2σ) | 33.9 (5.5σ) | 33.1 |
| walled cold-resumed, CCWALLCOLDR | 2/0.0073/−0.0002 | 73.2 | 66.7 (7.6σ) | 66.4 (7.9σ) | 15.5 (its σ(λ2_ν) = 0.05) |
| walled from unwalled 2nd, CCWALLSHIFT | 2/0.0024/−0.0006 | 84.0 | 77.6 (8.3σ) | 77.3 (8.5σ) | 78.9 |

- The k2-only, n_f = 4 and n_f-syst-in-cov variants move these χ² by 5–20 % and change no verdict ([compat.txt](compat.txt)).
- The unwalled tunes can only reach even χ² ≈ 200 by driving k1 negative (−0.15). With k1 held to ASWZ's 0.22 ± 0.08 they would be worse still.

### 4. Comparison in λ space (λ∞_ν = 2 slice)

![lambda2_nu-lambda4_nu plane at lambda_inf_nu=2: lattice 1/2/3 sigma contours (k1 profiled), systematic-variant best fits, Tackmann marginal ellipse (at lambda_inf=1.6853), the scetlib_ad postfits with their 1 sigma ellipses, and the card anchor](lambda_space_linf2.png)

*Caveat:* the Tackmann ellipse is the 2D marginal of a λ∞ = 1.6853 fit, and the grey contour is our lattice fit at that same λ∞. The postfits and the blue contours are at λ∞ = 2.

- Tackmann sits about 2.3σ from our lattice best fit in λ2_ν at equal λ∞ (0.087 vs 0.185 ± 0.043). But it lies along the λ2/λ4 degeneracy, which is why the kernel-space Δχ² is only 2.8.
- The Z postfits are nowhere near the lattice region.
- **The Z data are "tighter" than the lattice, but in the wrong place.** The unwalled postfit has σ(λ2_ν) = 0.006 and σ(λ4_ν) = 1.2×10⁻⁴, against the lattice's 0.038 and 0.0033: 7× and 30× tighter. This is a within-model constraint at a single Q. It is strongly tied to the TMD boundary condition (ρ(λ2_ν, λ2) = −0.28 at the main minimum, −0.86 at the second) and to the saturation cap λ∞_ν = 2, which is fixed by hand.
  - It sits 14σ from the lattice kernel with the wrong sign.
  - So the Z fit is not measuring the CS kernel. It uses the CS λ to absorb something else: the basin/TMD/PDF–scale structure of `alphas-scan-discontinuity` and `scetlib-ad-param-model` §20.

### 5. Physics read and recommendation

- **vs Tackmann/AN:** *consistent* in kernel space (0.9σ). ASWZ 2024 data, fitted with our own pert kernel and a proper a/b_T nuisance, prefer a somewhat deeper NP kernel at 0.2–0.45 fm than the 2023-data Tackmann tune: γ^NP(0.3 fm) = −0.19 ± 0.04 vs −0.12 ± 0.02, about 1.5σ combined at that single b. This is λ2_ν about 2× larger, partly offset by a smaller λ4_ν.
  - Our card's anchor, λ2_ν = 0.15 and λ4_ν = 0, is *more* lattice-compatible than the Tackmann centre is.
  - This is consistent with knowledge §12's "card is 2.4× deeper than Tackmann" being no longer a tension with the lattice.
- **vs our Z postfits:** *inconsistent* in every basin, walled or not, at 5.5–14σ even with the conservative lattice errors. This matches `scetlib-ad-param-model`'s earlier Tackmann-covariance finding: the lattice excludes plain at 15σ and walled at 10σ. Here it is reproduced with the lattice data themselves.
  - The wall does not fix it. The wall enforces sign and monotonicity, while the lattice fixes the *depth*, and the walled solutions have the kernel either off or saturated early.
- **Implication for α_s:** the constraint is load-bearing. The only measured α_s–λ2_ν response is `np_parametrization_constraints.md` §20, dα_s/dλ2_ν = +8.3×10⁻³ GeV⁻². It was measured on a different card and fit (2026-09-11, CS-frozen scan over λ2_ν = 0–0.15), so it transfers only as an order of magnitude.
  - At that slope, one lattice σ(λ2_ν) of 0.04 corresponds to about 3×10⁻⁴ in α_s.
  - Moving from the unwalled postfit to the lattice region, Δλ2_ν ≈ +0.26, corresponds to about 2×10⁻³. That is an *extrapolation* of the slope beyond its scanned range, a difference and not a value, and about 2σ(α_s).
  - Expect the Z fit to resist: in the frozen-CS and lattice-arm studies the violation relocated into the TMD boundary condition (λ2 → −0.14).
- **Recommendation (not implemented): an exact χ² regularizer, not a conditional Gaussian.**
  - Form: R(λ_ν) = χ²_lat(λ_ν) − χ²_min, with k1 profiled analytically. It is linear in k1, so the profiling is one 1×1 solve. The pert kernel is a precomputed 21-point table, since ∂γ/∂α_s ≈ −3 is negligible. The covariance is the lattice cov plus δδᵀ for n_f. Attach it via `-r` like `NPDampingWall`.
  - Why not a Gaussian:
    - (a) The likelihood is visibly non-Gaussian: the posterior mean and σ differ from the Hessian values by 0.3σ and 40 % in λ4_ν. The fit minima sit 5–14σ away, where a quadratic extrapolation is meaningless.
    - (b) The exact form handles λ∞_ν free/frozen and tanh_6 without re-deriving anything. The current Tackmann lat-cov term is conditional on λ∞ = 1.6853, while the AD fits freeze λ∞ = 2, so it is already mismatched.
    - (c) It constrains the kernel shape, which is what the data measure, rather than a λ ellipse along a degenerate direction.
  - If Luca prefers knowledge §11's "bracket, don't prior", the same fit supplies the bracket. At λ∞ = 2 the 95 % range is λ2_ν ∈ [0.08, 0.25]; restricted to the physical region it is [0.04, 0.17], with the card anchor 0.15 inside both.
  - Either way, apply it with k1 as a nuisance, never with k1 fixed. Without k the lattice fit is poor (χ² 14) and pulls λ2_ν to −0.05.

### 6. λ4_ν = 0 refit (2026-09-23, late; the configuration the AD fits must run in)

**Caveats:** everything from §0–1 still holds: block-diagonal lattice covariance, χ²/ndf ≈ 0.4, n_f = 5, N3LL, α_s = 0.118. λ4_ν = 0 is imposed for **fit-machinery** reasons, because the AD cache and tanh_2 break for λ4_ν < 0. It is not a lattice preference: the lattice wants λ4_ν = −0.0059 ± 0.0033, 1.8σ below zero.

| config (λ4_ν = 0) | χ²/ndf | AIC | λ2_ν [GeV²] | other |
|---|---|---|---|---|
| **λ∞ = 2, k1 (nominal)** | **8.59/19** | 12.59 | **0.1345(201)** | k1 0.209(67) |
| λ∞ free, k1 | 6.82/18 | 12.82 | 0.163(39) | λ∞ 1.32(34) |
| λ∞ = 2, k2 | 8.82/19 | 12.82 | 0.117(17) | k2 0.222(72) |
| λ∞ = 2, k1 + k2 | 8.54/18 | 14.54 | 0.130(29) | k1 0.15(27), k2 0.06(30) |
| λ∞ = 2, k1, n_f = 4 scheme | 8.48/19 | 12.48 | 0.1225(190) | |
| λ∞ = 2, k1, n_f matched at μ = 1 GeV | 8.64/19 | 12.64 | 0.1215(189) | |
| λ∞ = 2, k1, drop b_T < 0.2 fm | 6.35/15 | 10.35 | 0.125(24) | k1 0.14(14) |
| λ∞ = 2, k1, n_f syst δδᵀ in cov | 8.58/19 | 12.58 | 0.134(23) | |
| λ∞ = 2, no k | 18.44/20 | 20.44 | 0.108(16) | |

- **Stat+syst σ(λ2_ν)**, built as in the injector:
  - n_f group: the μ = 1 GeV match, −0.0131 (the n_f = 4 scheme gives −0.0121).
  - k-form group: k2 only, −0.0177 (k1 + k2 gives −0.0051).
  - b_T window: −0.0095.
  - Result: **λ2_ν = 0.1345 ± 0.0201 (stat) ± 0.0240 (syst) = ± 0.0313 (tot)**.
  - Every shift is *negative*. The symmetric quadrature σ is therefore conservative on the upper side, and the systematics are one-sided toward lower λ2_ν.
- The MCMC posterior (flat prior) is λ2_ν = 0.137 [0.116, 0.159], i.e. Gaussian to about 10 %.
- λ∞ free is not determined: 1.32 ± 0.34, Δχ² = −1.8 for one extra parameter, AIC +0.2. Keep λ∞_ν = 2.

**What freezing λ4_ν costs:**
- Δχ²(λ4_ν = 0 vs free λ2_ν, λ4_ν; both at λ∞ = 2 with k1) = **1.87** for 1 dof, i.e. **1.4σ**. Against the λ∞-free global best it is 2.12.
- The lattice data therefore accept λ4_ν = 0 without strain.
- In kernel space the λ4_ν = 0 curve is indistinguishable from the free fit below about 0.6 fm, which is the α_s-relevant window ([figure](kernel_space_l4zero.png)). Above that, λ4_ν = 0 keeps damping to the λ∞/2 = 1 cap, while the free fit turns over.

**Direct refit vs the Gaussian conditional of the 2D fit:**
- Stat-only conditional: 0.1229 ± 0.0180.
- Stat+syst conditional, using the injector's covariance: **0.1080 ± 0.0234**, which reproduces Luca's ≈ 0.108 ± 0.023.
- The direct refit is **0.1345 ± 0.031**, higher by 0.027 = 0.9σ_tot.
- The difference comes from non-Gaussianity (tanh saturation) and from the 2D syst shifts lying along the λ2/λ4 degeneracy. Conditioning a 2D covariance on λ4 = 0 drags λ2_ν down more than refitting at λ4 = 0 does.
- **For an in-fit λ4_ν = 0 constraint, use the direct 1D refit, not the conditional.**

**Compatibility with the λ4_ν = 0 constraint** (tune fixed, k1 floated):

| tune | χ² | Δχ² vs λ4=0 best (1 dof) | Δχ² vs 2D best (2 dof) | pull (stat+syst 1D) |
|---|---|---|---|---|
| card anchor (λ2_ν = 0.15) | 9.08 | 0.50 (0.7σ) | 2.37 (1.0σ) | +0.49 |
| Tackmann/AN as is (λ∞ 1.6853, λ4 0.0074; not on this slice) | 9.65 | 1.06 (1.0σ) | 2.94 (1.2σ) | – |
| Tackmann λ2 centre 0.087 on λ4 = 0, λ∞ = 2 | 14.88 | 6.29 (2.5σ stat) | 8.17 (2.4σ) | −1.52 |
| Tackmann λ2 +1σ (0.1202) on λ4 = 0, λ∞ = 2 | 9.08 | 0.49 (0.7σ) | 2.37 (1.0σ) | −0.46 |
| λ2_ν = 0 (CS NP off) | 79.9 | 71.3 (8.4σ) | 73.2 (8.3σ) | −4.30 |

- The Z postfits are unchanged in substance: Δχ² vs the λ4 = 0 best is 32–201.
- Tackmann's λ2 is only lattice-compatible *with* its λ4 > 0. Moved onto λ4_ν = 0 at λ∞ = 2, its centre is 2.5σ (stat) or 1.5σ (tot) low.

![Full kernel: lambda4_nu=0 fit band (red; dark = stat 68%, light = stat+syst 1 sigma) vs the free-(lambda2_nu, lambda4_nu) band (blue hatched), card anchor and Tackmann central, with lattice points shifted by the lambda4_nu=0 fit's k1](kernel_space_l4zero.png)

*Caveats for this figure:*
- The points are shifted by k̂1 = 0.21 from the λ4_ν = 0 fit, and the k1 uncertainty is not in the error bars. The blue band comes from the free fit, whose own k̂1 is 0.24, so the points are shown in the red fit's frame.
- λ∞_ν = 2, tanh_2, n_f = 5, block-diagonal lattice covariance.
- Lattice-only plus reference tunes, so no CMS label.

---

## Findings

1. Our full SCETlib kernel (n_f=5, N3LL, fit μ0/b\*) + k1·a/b_T describes the ASWZ per-ensemble data with χ²/ndf = 6.7/18. At λ∞_ν = 2: λ2_ν = 0.184(38) GeV², λ4_ν = −0.0059(33) GeV⁴, ρ = −0.88. Systematic spread in λ2_ν is −0.037/+0.028. — (evidence: [fit_output.txt](fit_output.txt))
2. The lattice data do not determine λ∞_ν; they only bound it from below at about 1.0 (Δχ² = 1). tanh_6 and k2 are not supported by AIC. The minimal adequate model is tanh_2 with λ∞ frozen, plus k1. — (evidence: [profile_linf.png](profile_linf.png), [fit_output.txt](fit_output.txt))
3. Tackmann/AN tune vs the lattice data: Δχ² = 3.2 (0.9σ), consistent in kernel space. The card anchor (λ2_ν = 0.15, λ4_ν = 0) is at 1.0σ. — (evidence: [compat.txt](compat.txt))
4. All scetlib_ad card-A real-data postfits are 5.5σ–14σ incompatible with the lattice CS kernel. The unwalled minima are anti-damping, and the walled minima have the NP kernel off, or saturated at its cap by 0.6 fm. — (evidence: [compat.txt](compat.txt), [kernel_space_comparison.png](kernel_space_comparison.png))
5. scetlib_ad fitresults store λ as θ (physical = anchor + width·θ). The `scetlib_np` reader `fitresult_lambdas.py` would misreport them as physical. **For knowledge/:** reading AD λ needs the REPARAM widths plus the cache.conf anchor. — (evidence: [read_ad_postfits.py](read_ad_postfits.py))

6. With λ4_ν fixed at 0 (required by the AD cache), the lattice data give λ2_ν = 0.1345 ± 0.020 (stat) ± 0.024 (syst) GeV² at λ∞_ν = 2. Freezing λ4_ν costs Δχ² = 1.9. Use this 1D direct refit, not the Gaussian conditional of the 2D fit, which gives 0.108 ± 0.023 and is 0.9σ low. — (evidence: [l4zero_output.txt](l4zero_output.txt))

---

## Open questions

- Cross-ensemble correlations (author Q4). With χ²/ndf ≈ 0.37, a correlated or systematic component inside the quoted errors is likely. If they were decorrelated and shrunk, every Δχ² above would grow.
- The 0.9 fm L32 point drives the λ4_ν < 0 turnover. Is it trustworthy (large Pz extrapolation)? This ties to the 0.72 fm-at-a=0.09 question (author Q6).
- α_s response to a lattice regularizer: it needs a real fit (out of scope). The §20 slope is from a different card and does not cover λ2_ν < 0.
- The TMD–CS relocation: with a lattice term, which TMD b.c. does the Z fit land on, and does it stay physical?
- The postfit bands ignore CS–TMD correlations. A kernel-space band marginalised over the full NP covariance would be more honest for the postfits, but it does not change the verdict: the central offsets are 10–20× the band widths.
