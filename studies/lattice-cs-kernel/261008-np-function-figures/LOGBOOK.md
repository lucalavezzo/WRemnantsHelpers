---
title: NP function headline figures
slug: 261008-np-function-figures
study: lattice-cs-kernel
status: done          # active | done | paused | abandoned
created: 2026-10-08
updated: 2026-10-08
owner: study-worker
---

# NP function headline figures

**Task:** What do the fitted NP functions (CS kernel γ_ζ(b_T), CS and TMD damping factors, the (λ2_ν, λ4_ν) plane) look like for lattice only, the joint fit LATFROZ_V3 and the Z-only fit XWSTIFF, against the ASWZ lattice points? Deliverable: publication-quality headline figures for the study summary.

---

## START HERE (status as of 2026-10-08) — DONE

- **Answer:** four figures made (Result §1–§3), all CMS Preliminary, png + pdf + `.log` in this directory. No fitted α_s
  enters any of them: every kernel uses the frozen LATFROZ perturbative part (α_s(m_Z) = 0.1168, TNPs = 0).
- **Physics in one line:** the joint curve sits *above* (weaker damping than) the lattice-only band for b_T < 0.54 fm and
  *below* it (stronger, saturated damping) for b_T > 0.63 fm. That is the λ2_ν-low / λ4_ν-high pull of the Z data, which
  the PG = 13.5 / 2 dof (3.2σ) tension quantifies. Z only and Z + lattice give the **same total CS × TMD damping** at
  m_Z, Y = 0. The lattice moves damping from the TMD side to the CS side and leaves the product unchanged.
- **Next action:** none. Optional: remake L2(Y) on LATFROZ_V3 (§4).
- **Blocking on:** nothing. **Running:** nothing.

---

## Log

### 2026-10-08
- Read the study SUMMARY, its START HERE, 261008-latfroz-nf-variants (all) and 260923-scetlib-kernel-fit (`plot.py`,
  `kernel_space_comparison.png`, the pre-LATFROZ version of figure 1).
- **Stage 1** [scripts/compute.py](scripts/compute.py) ([logs/compute.log](logs/compute.log)): run in the container
  with the gamma-nu-points build (`agent_setup.sh --scetlib /work/.../scetlib-gamma-nu-points/scetlib-cms/build`).
  No cache load and no fit. It builds the LATFROZ_V3 lattice term offline: `LatticeCSNativeCore` at
  `frozen_reference(anchor, 0.1168)`, `syst=Jnf nfmatch=4.18 nfscheme=full`, the same way `compare_froz.py` does. It then
  - evaluates γ_ζ = ½γ_ν with `DrellYan.gamma_nu_points`, at p_ref with only (λ2_ν, λ4_ν) replaced;
  - reads the physical NP λ and their covariance from the three fitresults, using the NPDampingWall's θ → λ map (every
    map is a linear `unit` map; asserted against `WALL._physical`). α_s is never read or stored;
  - computes the bands by sampling 2000 Gaussian draws of (λ2_ν, λ4_ν) through the exact kernel (16–84 %). The linear
    J C Jᵀ check agrees to 0.02 for the fits, but not for the lattice-only band on the full range (0.68). That band runs
    into the tanh saturation, which is why the bands are sampled.
  - Output: [np_figs_data.npz](np_figs_data.npz), [np_figs_data.json](np_figs_data.json).
- **Reproduction checks** (against the study numbers):
  - lattice only (V3) λ = (0.18795, −0.00609), σ = (0.0426, 0.0035), ρ = −0.884, χ²_min = 6.682;
  - LATFROZ_V3 λ2_ν = 0.0383 ± 0.0303, λ4_ν = 0.0106 ± 0.0057, Δχ²_lat = 9.187;
  - all as in 261008-latfroz-nf-variants.
  - The NP part of SCETlib's kernel equals −(λ∞_ν/2)·tanh(P/λ∞_ν) at raw b_T to 1e-15. The perturbative part has the
    μ0 = 1 GeV floor (b0/b_max = 1 GeV): it is constant at −0.173 for b_T ≳ 0.4 fm.
- **Stage 2** [scripts/plot.py](scripts/plot.py) ([logs/plot.log](logs/plot.log)): wums frames (`figure`,
  `figureWithRatio` with a dummy hist frame, `add_cms_decor("Preliminary", loc=0)`) and `save_plot`. The form factors
  come from `np_function_plots.gamma_nu_curve` / `f_eff_curve` / `map22_F_eff` (branch `scetlib-np-param-model`
  worktree, prepended to PYTHONPATH). The curves are functions, not hists, so they are drawn on the wums axes with
  matplotlib.
  - **fitresult_lambdas.py does NOT read scetlib_ad fitresults.** It assumes physical λ in `parms` (scetlib_np
    convention), while scetlib_ad stores θ with λ = anchor + width·θ. So I wrapped it: stage 1 maps θ → λ and stage 2
    feeds the λ to the np_function_plots forms. As an in-script check, NPF's γ_ν/2 equals the NP part of SCETlib's own
    kernel.
- Layout fixed after the orchestrator's review: the legends moved out of the data, and the upper-panel x tick labels are
  hidden (shared x).

---

## Result

### 0. Caveats first (apply to every figure)
- **Blinding-safe by construction.** The perturbative part of every γ_ζ curve is the LATFROZ frozen kernel (α_s(m_Z) =
  0.1168, CS TNPs = 0, λ∞_ν = 2, b0/b_max = 1 GeV). Only (λ2_ν, λ4_ν) differ between curves, and no fitted α_s
  enters anywhere. These are therefore NOT the kernels "as in the fit": the joint fit's own kernel also carries its
  fitted α_s and TNPs (θ_γν = +0.44 in V3).
- **Real-data fits.** The bands use each fit's walled Hessian. **XWSTIFF (Z only) has λ2_ν on its λ2_ν ≥ 0 wall face**
  (σ = 0.0002 there is a wall artefact, not a measurement), so it is drawn as a central curve only, everywhere. Its
  λ4_ν = 0.044 ± 0.011 includes the registry ν priors (σ_θ = 1, i.e. σ(λ4_ν) = 0.5: negligible).
- **Lattice points.** These are raw − k̂1·a/b_T with k̂1 = 0.241, profiled at the lattice-only optimum (final C,
  including the V3 n_f row; ASWZ's own k1 = 0.213 is for their kernel). Error bars are stat only. The χ²_lat in the
  legends and the pulls profile each curve's own k̂1 (joint 0.145, Z only 0.204, NOMSTIFF 0.129).
- **Walled TMD faces.** LATFROZ_V3 and NOMSTIFF sit on the TMD L2(|Y| = 2.5) = 0 face. XWSTIFF sits on the TMD large-b
  face 3λ∞²λ4 + L2³ = 0 at |Y| = 2.5 (λ4 ≈ 0). The F^NP bands at |Y| = 2.5 are therefore pinched by the wall: a walled
  Hessian is the physical-side width, not a Gaussian error.

### 1. CS kernel vs the lattice points

![γ_ζ(b_T, 2 GeV) vs the 21 ASWZ points (k1-subtracted at the lattice-only optimum), with lattice only, Z + lattice (LATFROZ V3), NOMSTIFF and Z-only XWSTIFF central; pulls vs lattice only and vs joint](cs_kernel_vs_lattice.png)

*Caveat: perturbative part frozen at α_s = 0.1168, TNPs = 0 in every curve. Points are k̂1-subtracted at the
lattice-only optimum, while the pulls and χ²_lat use each curve's own k̂1. Z only has no band (λ2_ν on its wall face).
Pulls are diagonal-σ, and the points are correlated within an ensemble.*

![Same curves over the full b_T range up to 2.6 fm, lattice range shaded, b_T = 12.6 GeV^-1 marked](cs_kernel_full_range.png)

*Caveat: as above. Outside the shaded range the lattice-only curve is a pure extrapolation of the tanh_2 form. Its
λ4_ν < 0 makes the NP part change sign at b_T = 1.10 fm, i.e. anti-damping, which is unphysical.*

| b_T [fm] | lattice only (68 %) | Z + lattice V3 (68 %) | Z only | NOMSTIFF |
|---|---|---|---|---|
| 0.2 | −0.212 [−0.231, −0.192] | −0.144 [−0.158, −0.130] | −0.142 | −0.152 |
| 0.4 | −0.495 [−0.550, −0.436] | −0.339 [−0.381, −0.299] | −0.530 | −0.303 |
| 0.6 | −0.716 [−0.781, −0.643] | −0.732 [−0.835, −0.608] | −1.129 | −0.462 |
| 0.8 | −0.791 [−0.916, −0.644] | −1.114 [−1.156, −0.983] | −1.173 | −0.657 |

χ²_lat (21 points, k̂1 profiled, V3 covariance): lattice only 6.7, Z + lattice 15.9, NOMSTIFF 20.9, Z only 36.5.

### 2. The NP damping functions

![2x2: γ_ζ^NP(b_T); CS NP factor exp[γ_ν^NP ln(m_Z b_T/b0)]; F^NP(b_T, Y) at Y = 0 and 2.5 with MAP22; total CS × F^NP at Y = 0 — lattice only, Z + lattice, Z only](np_functions.png)

*Caveat: the CS factor uses the canonical rapidity log ln(m_Z b_T/b0) (ν_B = m_Z, ν_S = b0/b_T). This is an
illustration of the size of the CS damping at Z kinematics, not SCETlib's profile-scale evolution. The CS NP part enters
SCETlib as γ_ν^NP·ln(ν_B/ν_S), `ad_kernel.hpp`. Z only has no bands. MAP22 is the N3LL central replica with its CS
evolution factor stripped, a different scheme and b*, and is shown as a shape reference only.*

Values (b_T in GeV⁻¹, [np_functions_values.json](np_functions_values.json)):

| b_T | γ_ζ^NP lat / joint / Z | CS factor joint / Z | F^NP(Y=0) joint / Z | product joint / Z |
|---|---|---|---|---|
| 1 | −0.093 / −0.025 / −0.023 | 0.80 / 0.82 | 0.78 / 0.78 | 0.62 / 0.64 |
| 2 | −0.314 / −0.158 / −0.335 | 0.20 / 0.03 | 0.10 / 0.39 | 0.020 / 0.013 |
| 3 | −0.537 / −0.540 / −0.947 | 0.003 / 0.000 | 0.003 / 0.12 | 0 / 0 |

### 3. The (λ2_ν, λ4_ν) plane

![(λ2_ν, λ4_ν): lattice-only exact Δχ² 68/95 % contours and its Gaussian ellipse, LATFROZ V3 Hessian ellipses, XWSTIFF on the λ2_ν = 0 face, NOMSTIFF at λ4_ν = 0; unphysical region hatched; PG 13.5/2 dof](lambda_nu_plane.png)

*Caveats:*
- *The contours are 2D 68.3 / 95.4 % (Δχ² = 2.30 / 6.18), at λ∞_ν = 2 with the frozen perturbative part.*
- *The XWSTIFF dashed sliver is its walled Hessian, i.e. the wall, not a data constraint.*
- *NOMSTIFF had λ4_ν frozen at 0 and a 1D Gaussian lattice term, so it is drawn as a 1D interval.*
- *The PG is 13.48 / 2 dof against XWSTIFF with its ν priors removed (261008-latfroz-nf-variants §2b). Wilks is untested
  at a walled minimum.*

The exact lattice Δχ² contour is close to its Gaussian approximation 2H⁻¹ but not identical (tanh nonlinearity). The
lattice-only optimum sits at λ4_ν < 0, just outside the physical quadrant (≈ 1.7σ in λ4_ν).

### 4. L2(Y) (item 4, not remade)
[tmd-rapidity-shape/261007-y-shape-first-look `L2_of_Y.png`](https://submit.mit.edu/~lavezzo/alphaS/studies/#tmd-rapidity-shape/261007-y-shape-first-look)
already shows L2(Y) for LATB8 (its wall-free ±1σ band), NOMSTIFF, MAP22 and the AN nominal. It is LATB8-based, which the
brief counts as current, so it is reused as is. LATB8 and LATFROZ_V3 have nearly the same TMD tune (V3: λ2 = 0.048 ±
0.046, δλ2 = −0.0077 ± 0.0074; the same single active face). It does **not** include XWSTIFF (λ2 = 0.119, δλ2 = −0.0094).

### 5. Physics read
1. **Where the joint curve leaves the lattice band.** The joint γ_ζ lies above the lattice-only 68 % band (weaker
   damping) for b_T < 0.54 fm, by 0.07–0.16 at 0.2–0.4 fm, which is several band widths. It crosses at 0.54–0.63 fm and
   lies below the band (stronger, faster saturation) for b_T > 0.63 fm.
   - Point by point this is mild: the largest joint pull is 1.7, at 0.76 and 0.91 fm. In total it is Δχ²_lat = 9.2, the
     lattice part of the 3.2σ PG tension.
   - It is the λ2_ν-small / λ4_ν-large direction: the Z data want less CS damping at small b_T and a sharper onset at
     larger b_T. Z only goes further still (λ2_ν = 0 on the wall, λ4_ν = 0.044) and misses the lattice by χ² = 36.5.
2. **The Z data measure the product, not the split.** At m_Z, Y = 0 the total NP damping (CS factor × F^NP) of Z only
   and of Z + lattice agree to ≤ 2.6 % wherever the product is > 0.2 (b_T ≲ 1.5 GeV⁻¹; 9 % at product 0.1). Yet the CS factor and F^NP
   individually differ by ×5–10 at b_T = 2 GeV⁻¹. This is the ρ(λ2_ν, Λ2) ≈ −0.985 degeneracy (260923-qsplit-fisher)
   made visible: the lattice moves damping from the TMD side to the CS side at no cost to the Z shape. It is also why
   the lattice barely moves α_s once λ4_ν is treated alike (XL4ZSTIFF −0.013σ).
3. **The joint TMD factor is narrower than MAP22's.** F^NP at Y = 0 falls to 0.1 at b_T ≈ 2 GeV⁻¹ in the joint fit,
   against 3.4 GeV⁻¹ for MAP22 (intrinsic) and 3.1 GeV⁻¹ for Z only, which is closer to MAP22 (0.39 at 2 GeV⁻¹), because it has no CS damping
   at small b. Scheme caveat: MAP22 has a different b* and the evolution factor stripped.
4. **The lattice-only form is unphysical beyond the lattice range.** λ4_ν = −0.006 < 0 turns the lattice-only NP kernel
   positive beyond b_T = 1.10 fm. The CS factor then explodes at b_T ≳ 5 GeV⁻¹. Inside the Z fit the wall (λ4_ν ≥ 0)
   forbids this, and the joint optimum is interior (λ4_ν = +0.011). The 2D lattice-only χ² still allows λ4_ν ≥ 0 at
   ≈ 1.7σ.

---

## Findings

1. Headline figures: `cs_kernel_vs_lattice`, `cs_kernel_full_range`, `np_functions`, `lambda_nu_plane` (.png/.pdf) in
   this directory. They are built from [np_figs_data.npz](np_figs_data.npz) (compute.py) and drawn by plot.py.
2. The joint γ_ζ crosses the lattice band: above it for b_T < 0.54 fm, below it for b_T > 0.63 fm. The tension is a
   shape (λ2_ν vs λ4_ν) tension, not an offset — (evidence: np_figs_data.npz, §1 table).
3. Z only and Z + lattice give the same total CS × TMD NP damping at m_Z to ≤ 2.6 % where it is > 0.2. The lattice
   re-splits the damping between CS and TMD — (evidence: np_functions_values.json, scripts/check_numbers.py).
4. `fitresult_lambdas.py` (scetlib_np) does not read scetlib_ad fitresults (θ, not physical λ, in `parms`). A
   scetlib_ad-aware reader is the θ → λ part of compute.py `read_fit` — (evidence: scripts/compute.py). It is worth
   folding into the tool if these plots become routine.

---

## Open questions

- Remake L2(Y) on LATFROZ_V3 with XWSTIFF added? It needs only the TMD λ, which are in np_figs_data.npz.
- The CS factor panel uses canonical scales. A version through SCETlib's actual ν_S profile would need the node-level
  scales (`ns_ln_nu_nuS`), which are not exposed offline.
