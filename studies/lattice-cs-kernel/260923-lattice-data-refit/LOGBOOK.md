---
title: Lattice per-ensemble refit and continuum-file audit
slug: 260923-lattice-data-refit
study: lattice-cs-kernel
status: done        # active | done | paused | abandoned
created: 2026-09-23
updated: 2026-09-24
owner: study-worker
---

# Lattice per-ensemble refit and continuum-file audit

**Task:** From the per-ensemble ASWZ lattice data with covariances, can we reproduce their (arXiv:2402.06725) continuum extrapolation? And what is the "continuum-extrapolated" file they sent us: how much uncertainty and correlation do we lose by using it instead of the per-ensemble data plus a lattice-spacing nuisance?

---

## START HERE (status as of 2026-09-24)

> **The continuum file is exactly raw − 0.213649·a/b_T: one fixed k1 at all 21 points, the raw diagonal σ, and no covariance. The paper's AIC-best (c0,k1) fit reproduces from the per-ensemble data in its central values, taking Eqs. (CSkernelparam) and (DNP) literally: c0 = 0.0324 vs 0.032, k1 = 0.213 vs 0.22, the file's k1 = 0.2136, and χ²/dof 0.385 vs 0.39. Our σ's are smaller than the quoted ones: σ(c0) 0.0060 vs 0.012 (2×), and σ(k1) 0.066 vs 0.08.**
> Fitting the continuum file with diagonal errors underestimates σ(c0) by 17% relative to the per-ensemble data with a free k1. B_NP is unconstrained: Δχ² < 0.7 over 1.0–2.5 GeV⁻¹, while c0 moves 0.097 → 0.028 across that range.
> **Main comparison figure:** `comparison_aswz_refit_scetlib.png` (the version without SCETlib is `comparison_aswz_refit.png`), embedded at the top of Result.
> **2026-09-24 RETRACTION:** the 2026-09-23 "c0 factor 2" claim was a bug in our D_res. See the Log.

- **Next action:** none. Task closed. Open item for the orchestrator: ask the authors how the quoted σ(c0) = 0.012 and σ(k1) = 0.08 were obtained.
- **Blocking on:** nothing.

---

## Log

### 2026-09-24 — clean comparison figure (Luca)
- Luca found the earlier figures confusing, for two reasons:
  - `paper_fig2_style.png` has a single a=0 line that is *our refit of their* parametrization.
  - The sibling task's `email_lattice_comparison.png` never draws the paper's own central curve.
- New script: `compare_figure.py`, which draws one panel with a provenance label on every legend entry. It **imports** the SCETlib curve from `../260923-scetlib-kernel-fit` (`kernel_fit.py`, `fit_l4zero.json`, `fit_results.json`, which in turn use `../260923-conventions-map/our_cs_kernel.py`); nothing is re-derived.
  - `comparison_aswz_refit_scetlib.png` is the full version.
  - `comparison_aswz_refit.png` omits the SCETlib curve; it is the variant for the theorist email.
- Restyled (same day, at Luca's request) to match the postfit-comparison plots.
  - **Data style:** the points use the plot.py style (ENS_COL, ENS_LAB, dx). The constants are read with `ast` from `../260923-scetlib-kernel-fit/plot.py`, because that file cannot be imported outside the container (it pulls in tensorflow).
  - **Curve colours:** SCETlib is drawn in #5790fc, ASWZ published in black with a grey band, and our refit in grey dashed.
  - **No further tweak was needed:** the L32 points stay legible against the #5790fc band because they are drawn opaque and on top.
- Check on the published curve: the numeric D_res and the paper's closed-form D_res differ by at most 0.025 over 0.03–1 fm, which is small against the band (≥0.05 beyond 0.4 fm). The figure uses the numeric one.

### 2026-09-24 — RETRACTION and rerun
- **RETRACTED: the 2026-09-23 conclusion "the paper's c0 multiplies −b_T·b\*, so there is a factor 2 between its quoted c0 and its equations".** It was wrong, caused by a bug in our `cs_fit.py`, and the orchestrator found it. The bug was in the non-cusp coefficients.
  - We coded `D = [0, 0, d2, d3]` and summed Σ D[n]·a_s^{n+1}, following the paper's supplement literally ("d_0 = d_1 = 0, d_2 = −56ζ3 + 1616/27 − 224/81 n_f, …").
  - That "d_2" is the two-loop coefficient C_F[C_A(404/27 − 14ζ3) − 112/27 T_F n_f], and it must multiply a_s². The paper's d-list has an index offset relative to its Γ_n list, which starts at a_s¹.
  - As coded, the 2-loop term sat at a_s³ and the 3-loop term at a_s⁴. That changed −2D_res at 0.9 fm from −0.382 (correct) to −0.633 (wrong). The b_T-shape error was absorbed by halving c0, which is where the apparent factor 2 came from.
  - The σ(c0) "match" to 0.012 under the factor-2 convention was a coincidence of the rescaling. σ(c0) of a linear fit depends only on the c0 column and the covariance, so rescaling the column by ½ doubles the error.
  - All 2026-09-23 numbers are superseded. They are kept below, marked, and can be reproduced with `--dshift-bug` → `fit_output_numeric_dshiftbug.txt`.
- **Fix:** `D = [0, d2, d3, 0]`, with a comment giving the physics reason. The old behaviour is behind `--dshift-bug`, for the record only. Our fixed D_res reproduces the orchestrator's monkeypatch exactly: (c0,k1) gives χ² 7.32, c0 = 0.0324(60), k1 = 0.2130 numeric, and c0 = 0.0346, k1 = 0.2143 with the paper's closed form.
- **Reran everything.** Outputs: `fit_output_{numeric,paper}.txt`, `explore_c0_norm_output.txt` (now σ and B_NP diagnostics; the factor-2 variant is removed) and `check_blny_output.txt`.
- **BLNY (g2 b², B_NP = 1.5), fit (g2,k1):** χ²/dof = 0.576, which now **matches** the quoted 0.58. The literal −2·g2 b² gives g2 = 0.0212(32), exactly ¼ of the quoted 0.085, and the σ is ⅛ of the quoted 0.026.
  - So BLNY reproduces up to a convention factor 4 on g2, plus the same 2× σ pattern.
  - A plausible reading is that their BLNY g2 enters as γ_NP = −g2 b²/2, the original BLNY normalization, rather than via Eq. (DNP). This is a hypothesis we have not checked.
- **New figure in the paper's Fig. 2 style**, with the paper's own figures copied to `paper_figs/` for side-by-side comparison. Deleted the old `per_ensemble_fit_c0_k1.*`.

### 2026-09-23
- Extracted the tarball into `data/`, removing the `._*` mac files. The per-ensemble δCS column equals √diag(cov) exactly (difference 0.0).
- Read the paper source (`arxiv.org/e-print/2402.06725`, `main.tex` L293–367 and the supplement L505–578).
  - Transcribed D_res twice: as a numerical 4-loop RGE (∫Γ_cusp + d(α_s(μ_b\*))), and as the paper's closed-form K + a_s expansion. — (`cs_fit.py`)
  - **[2026-09-24: the d-coefficient powers in this transcription were wrong; see above.]**
- Continuum-file hypothesis: shift/(a/b_T) = 0.213649 at all 21 points (std 2e-16), and the file's σ equals the raw per-point σ. **Confirmed; this finding still stands.** Note that b_T = n·a on every ensemble, so a/b_T = 1/n.
- ~~c0 factor-2 diagnosis~~ **RETRACTED 2026-09-24** (it was the bug).
- ~~BLNY not reproduced~~ **superseded 2026-09-24** (the χ² now reproduces; g2 matches up to a factor 4).
- Rerun: `PYTHONPATH=$WREM_BASE/wums python3 cs_fit.py [--dres numeric|paper] [--noplots] [--dshift-bug]` (plain python3, ~3 s).

---

## Result

### Comparison figure (2026-09-24)

![Comparison of the ASWZ published kernel, our refit of the ASWZ parametrization, and our SCETlib tanh_2 fit, against ASWZ lattice points with the continuum-file k1 subtracted.](comparison_aswz_refit_scetlib.png)

**The curves** (the style matches the postfit-comparison plots in `../260923-scetlib-kernel-fit/plot.py`):
- **Points:** the ASWZ per-ensemble data minus k1·a/b_T with **k1 = 0.2136**, the value ASWZ used to build their continuum file. They are filled circles, L32 blue, L48 orange and L64 red, with the plot.py x-offsets and raw diagonal errors.
- **Black, solid, grey band:** the **ASWZ published** kernel, i.e. Eq. (6)–(8) at a=0 with B_NP = 2 GeV⁻¹ and c0 = 0.032 ± 0.012 (their Eq. 9). The band is their quoted σ(c0).
- **Grey, dashed, lighter band:** **our refit of their Eq. (6)–(8)**, with c0 = 0.0324 ± 0.0060 and k1 = 0.213 from the full (c0,k1) covariance. At a=0 the k1 term vanishes, so the band is |∂γ/∂c0|·σ(c0). It lies on top of the black curve, which is the point: the paper's central values reproduce. Only the band widths differ, by a factor 2 in σ(c0) that we cannot explain.
- **Blue #5790fc, line and band:** **our SCETlib tanh_2 fit** from `../260923-scetlib-kernel-fit`, with λ∞_ν = 2, λ4_ν = 0 and λ2_ν = 0.1345 ± 0.031 (stat+syst). Its own k1 is 0.209. The thin dotted line in the same blue is the fit with λ2_ν and λ4_ν both free.

**Caveats:**
- The lattice covariance is assumed block-diagonal across ensembles.
- The SCETlib curve uses n_f = 5; the lattice kernel is n_f = 4. The sibling task estimates the offset from this at ≤ 0.03.
- Each fit has its own k1 (0.213 for the ASWZ-form refit, 0.209 for SCETlib), while the plotted points use 0.2136. So the points are only an approximate a=0 view for each curve.
- D_res for the ASWZ curves is our corrected numeric 4-loop evaluation. The paper's closed form differs from it by at most 0.025.

The theorist-email variant, `comparison_aswz_refit.png`, shows only the data, the ASWZ published curve and our refit:

![Theorist-email variant: data, ASWZ published, and our refit of the ASWZ parametrization only.](comparison_aswz_refit.png)

**Caveats first.**
- All fits fix B_NP = 2 GeV⁻¹ unless it is freed. The paper writes "2 GeV", but b_T is in GeV⁻¹.
- The paper fits at bootstrap level. We do a correlated GLS on the supplied covariance.
- We assume the covariance is block-diagonal across ensembles; the paper does not discuss cross-ensemble correlation.
- D_res is our own transcription, in two variants. They differ by +0.002 in c0 (0.4σ): `numeric` (exact 4-loop RGE) is the default, and `paper` is the paper's closed-form expansion.
- c0 is as in Eq. (DNP): γ ∋ −2·b_T·b\*·c0.

### 1. What the continuum file is
It is `CS_ASWZ = γ_lat(b_T, a) − k1·a/b_T`, with **k1 = 0.213649** at every point and σ equal to the raw per-point diagonal error, unchanged. It has no covariance and no k1 uncertainty.
- This k1 **matches our (c0,k1) refit**: 0.2130 (numeric) and 0.2143 (paper closed form).
- The quoted 0.22(8) is presumably the same number rounded differently, or from a bootstrap.
- So the file is "the per-ensemble data with the best-fit k1 subtracted". It is not an independent per-b_T continuum extrapolation, which the paper itself says (L293) it could not do without matched b_T values across ensembles.

### 2. Option A — the paper's parametrization and numbers (arXiv:2402.06725, `main.tex`)

- **Eq. (CSkernelparam)** (L314): γ_q^param(b_T, μ, a) = −2 D_res(b\*, μ) − 2 D_NP(b_T; B_NP, c0, c1) + k1·a/b_T + k2·a²/b_T².
- **Eq. (DNP)** (L323): D_NP = b_T b\* [c0 + c1 ln(b\*/B_NP)], with b\* = b_T/√(1 + b_T²/B_NP²).
- **Supp. Eq. (dres)** (L510): D_res = ½K(μ, μ_b\*) + d[α_s(μ_b\*)] = ∫_{μ_b\*}^{μ} dμ'/μ' Γ_cusp + d, where μ_b\* = 2e^{−γE}/b\*.
  - Γ_cusp is taken to 4 loops. The paper also mentions an approximate 5-loop term, which we do not include.
  - The non-cusp d is taken to 3 loops. **The supplement's "d_0 = d_1 = 0, d_2, d_3" must be read as the 1-, 2- and 3-loop coefficients at a_s¹, a_s² and a_s³, i.e. d = a_s²·d_2 + a_s³·d_3 in the paper's naming.**
  - Running is 4-loop, with α_s(2 GeV) = 0.293, n_f = 4, μ = 2 GeV, MSbar (L578).
- **AIC-best model** (L338–345): (c0,k1) free, with c1 = k2 = 0 and B_NP = 2 (GeV⁻¹). The quoted result is **c0 = 0.032(12), k1 = 0.22(8), χ²/dof = 0.39**.
  - No c0–k1 correlation is quoted. We find ρ = +0.43.
- Other quoted numbers:
  - (c0,k2) and (c0,k1,k2) give c0 consistent at 1σ, with σ within ≲10% (L360).
  - |k1| and |k2| lie in 0.1–0.3 (L361).
  - The comparisons are SV19 c0 = 0.043(11) with B_NP = 1.9(2), and ART23 c0 = 0.037(6) (L358).
  - BLNY: g2 = 0.085(26) at B_NP = 1.5, with χ²/dof = 0.58 (L364–366).

### 3. Reproduction: fit table
Per-ensemble data (21 points, 3 ensembles), full covariance, numeric D_res, B_NP = 2 GeV⁻¹ unless freed.

| model | χ²/ndf | AIC | c0 [GeV²] | k1 | other |
|---|---|---|---|---|---|
| **c0,k1** (paper AIC-best) | **7.32/19 = 0.385** | **11.32** | **0.0324(60)** | **0.213(66)** | ρ(c0,k1) = +0.43 |
| c0,k1, paper closed-form D_res | 7.37/19 = 0.388 | 11.37 | 0.0346(60) | 0.214(66) | |
| c0,k2 | 8.28/19 = 0.44 | 12.28 | 0.0272(55) | | k2 = 0.220(72) |
| c0,k1,k2 | 7.28/18 = 0.40 | 13.28 | 0.0337(85) | 0.27(27) | k2 = −0.06(29) |
| c0,c1,k1 | 7.31/18 = 0.41 | 13.31 | 0.0331(121) | 0.208(100) | c1 = 0.004(57) |
| c0,k1,B_NP | 7.07/18 = 0.39 | 13.07 | 0.0278(54) | 0.224(66) | B_NP = 2.40 (flat, see §5) |
| c0,c1,k1,k2,B_NP | 6.53/16 = 0.41 | 16.53 | 0.038(15) | 0.16(70) | B_NP at the 2.5 bound |
| c0 only (no lattice-artefact term) | 17.63/20 | 19.63 | 0.0240(54) | | |
| c0,k1, diagonal cov | 8.18/19 = 0.43 | 12.18 | 0.0309(57) | 0.213(66) | |

**What matches:**
- (c0,k1) is the AIC minimum. Single-term fits are preferred over (c0,k1,k2) by 2.0 AIC for k1 and 1.0 for k2.
- χ²/dof is 0.385 (paper 0.39).
- c0 is 0.0324 (numeric) or 0.0346 (closed form), against 0.032.
- k1 is 0.213, against the file's 0.2136 and the quoted 0.22.
- The (c0,k2) and (c0,k1,k2) c0 values are consistent at 1σ.
- The magnitudes of k1 and k2 are in 0.1–0.3, except in the degenerate (c0,k1,k2) fit.
- BLNY χ²/dof is 0.576 (paper 0.58).

**What does not match:**
- **Our σ(c0) is 0.0060, half the quoted 0.012.** Our σ(k1) is 0.066 against 0.08 (a factor 1.2).
- BLNY σ(g2) is likewise a factor 2 small once the factor-4 convention is applied.
- Scaling the whole covariance by 4 would reproduce σ(c0) but give σ(k1) = 0.13, so it is not a uniform error inflation.
- The paper's "σ within 10%" claim for (c0,k1,k2) does not hold for us: σ(c0) grows by +42%.
- Our χ² reproduces with the supplied covariance, so the quoted σ's likely come from the bootstrap spread of fitted parameters, possibly including variations we don't have. Unresolved; see Open questions.
- The paper's own lower-panel band matches ±0.012, the dotted line in the figure below, not our band.

![Paper Fig. 2 style reproduction. Upper: raw per-ensemble points, dashed γ(b_T,a) per lattice spacing, solid a=0. Lower: points with k̂1·a/b_T subtracted, a=0 curve with our full (c0,k1)-covariance 1σ band (red fill) and the paper-quoted σ(c0)=0.012 band (dotted). B_NP=2 GeV⁻¹, numeric 4-loop D_res.](paper_fig2_style.png)

*Caveat for the figure:* at a = 0 the k1 column vanishes, so the propagated (c0,k1) band is numerically the c0-only band. The paper's figures for side-by-side comparison are [`paper_figs/CS_fit_artifacts-1.png`](paper_figs/CS_fit_artifacts-1.png) (upper) and [`paper_figs/CS_fit_subtracted-1.png`](paper_figs/CS_fit_subtracted-1.png) (lower). The curves agree visually; the paper's band is the wider, dotted one.

![Paper Fig. 2 upper (ASWZ).](paper_figs/CS_fit_artifacts-1.png) ![Paper Fig. 2 lower (ASWZ).](paper_figs/CS_fit_subtracted-1.png)

### 4. What the continuum file loses
Every row fits c0 at a = 0 with B_NP = 2.

| input | c0 | σ(c0) | vs (b) |
|---|---|---|---|
| (b) per-ensemble, full cov, free k1 — **reference** | 0.0324 | 0.0060 | — |
| (a) continuum file, diagonal errors | 0.0310 | 0.0050 | σ −17%, central −0.2σ |
| (c) continuum file, full ensemble cov | 0.0324 | 0.0054 | σ −10% |
| (d) continuum file, diag + k1 ± 0.08 as a correlated (a/b_T) syst | 0.0309 | 0.0055 | |
| (e) continuum file, full cov + k1 ± 0.08 as a correlated syst | 0.0324 | 0.0058 | ≈(b), but double-counts k1 info |

The loss breaks into three parts:
1. **The k1 uncertainty**, about 60% of the σ deficit. It is a term σ_k1·a/b_T = 0.066/n, fully correlated across all points and ensembles: at b_T = a it is 61%, 55% and 36% of the stat error for L32, L48 and L64.
2. **The within-ensemble correlations**, about 40% of the deficit. Off-diagonal ρ has median 0.03, 0.01 and 0.05, with a maximum of +0.26 and a minimum of −0.15.
3. **The c0–k1 correlation** (+0.43), which is invisible in the file.

The central value is essentially unaffected, because the file's k1 is the best fit. **For Option B, use the per-ensemble files, the block-diagonal covariance and a free k1; do not use the continuum file.**

![Continuum file points vs the a=0 curve from the per-ensemble fit (black) and from a diagonal-error fit to the continuum file (red). B_NP=2 GeV⁻¹.](continuum_file_vs_fit.png)

![Per-ensemble correlation matrices (b_T in fm).](correlation_matrices.png)

### 5. B_NP, the b_T < 0.2 fm points and the 0.9 fm edge
- **B_NP is still unconstrained, now with a shallow interior minimum.**

  | B_NP [GeV⁻¹] | 1.0 | 1.5 | 2.0 | 2.4 | 2.5 |
  |---|---|---|---|---|---|
  | χ² (numeric D_res) | 7.77 | 7.49 | 7.32 | 7.07 | 7.27 |

  - Δχ² < 0.7 over the whole range. The curvature error quoted by the free-B_NP fit (±0.32) is local and not meaningful.
  - The upturn at 2.5 comes from μ_b\*(0.9 fm) approaching the 4-loop n_f = 4 Landau pole, about 0.47 GeV. With the paper's closed form, χ² falls monotonically to 2.5.
  - c0 is **strongly B_NP-dependent**: 0.097 at B_NP = 1.0, 0.051 at 1.5 and 0.028 at 2.4. So c0 = 0.032 is meaningful only together with B_NP = 2. Any Option-A use must carry the pair (B_NP = 2, c0), or propagate B_NP.
  - The previous "runs to the pole" statement is superseded: the data are flat in B_NP rather than pushing it to the pole.
- **Dropping b_T < 0.2 fm** (4 points): c0 = 0.0322(75) and k1 = 0.21(14), so σ(c0) rises by 25% and σ(k1) doubles. These points mostly calibrate the a/b_T artefact rather than the kernel, consistent with the theorist's remark that below 0.2 fm the lattice adds nothing beyond perturbation theory.
- **Restricting to b_T ≤ 0.8 fm:** c0 = 0.0334(62). The 0.84 and 0.9 fm points (σ = 0.73 and 0.37) barely matter, and nothing constrains the kernel beyond 0.9 fm.

---

## Findings

1. The ASWZ continuum file is exactly raw − 0.213649·a/b_T with the raw diagonal σ, where k1 is the best-fit value of the (c0,k1) fit. It carries no covariance and no k1 uncertainty. — (`fit_output_numeric.txt`)
2. The paper's (c0,k1) central values and χ²/dof reproduce from the per-ensemble data using Eqs. (CSkernelparam), (DNP) and (dres) literally, **provided the supplement's d_n are read as 1-, 2- and 3-loop coefficients** (its d_2 is the two-loop term at a_s²). Our σ(c0) is half the quoted value, and σ(k1) is 1/1.2 of it. — (`fit_output_numeric.txt`, `explore_c0_norm_output.txt`)
3. Fitting the continuum file with diagonal errors underestimates σ(c0) by 17%: about 60% of that comes from the dropped k1 term and 40% from the dropped correlations. ρ(c0,k1) = +0.43. — (`cs_fit.py` §5)
4. The per-ensemble covariances are close to diagonal (|ρ| ≤ 0.26). — (`correlation_matrices.png`)
5. B_NP is unconstrained (Δχ² < 0.7 over 1–2.5 GeV⁻¹) while c0 changes by 3.5× across that range, so c0 is only meaningful paired with B_NP. The b_T < 0.2 fm points mostly constrain k1. — (`explore_c0_norm_output.txt`)
6. **Retracted (2026-09-23 → 2026-09-24):** "the paper's c0 differs by a factor 2 from its equations". This was our bug.

---

## Open questions

- **How are the quoted σ(c0) = 0.012 and σ(k1) = 0.08 obtained?** Ours are 0.0060 and 0.066 from the supplied covariance, whose χ² reproduces the paper's. BLNY shows the same 2× pattern. Possibly they come from bootstrap parameter spread, or include renormalization, b^z_max or B_NP variations. This matters directly for how much weight Option A would carry. Ask the authors.
- The BLNY g2 convention: the quoted g2 equals 4× our literal Eq.(DNP)-style g2. Presumably γ_NP = −g2 b²/2 (the original BLNY normalization); unconfirmed.
- Is there a correlated systematic common to all ensembles (the perturbative uNNLL matching, α_s(2 GeV)) that the block-diagonal covariance misses?

---

## SUPERSEDED result (2026-09-23) — WRONG, kept for the record

> **SUPERSEDED 2026-09-24. Do not quote anything in this section.** Every number here was computed with the d_n index bug: the 2-loop non-cusp term sat at a_s³ and the 3-loop term at a_s⁴. See the RETRACTION in the Log. The "c0 factor 2 / c0_quoted" conclusion is **retracted**. The corrected results are in "Result" above. Rerun with `python3 cs_fit.py --dshift-bug` to reproduce these numbers (`fit_output_numeric_dshiftbug.txt`). The figure `per_ensemble_fit_c0_k1.png` referenced below was deleted; `continuum_file_vs_fit.png` has been overwritten with corrected numbers.

**Caveats first.**
- The comparison to the paper is to central fits with fixed B_NP = 2 GeV⁻¹. The paper writes "2 GeV", but b_T is in GeV⁻¹, so the unit must be GeV⁻¹. The paper fit at bootstrap level; we do a correlated GLS on the supplied covariance.
- We assume the covariance is block-diagonal across ensembles. The paper says nothing about cross-ensemble correlation: the ensembles are distinct MILC ensembles, and the renormalization-scale systematic is per-ensemble.
- Our D_res is our own transcription, in two variants. They move c0 by +0.003 (+0.006 in the quoted convention), about half a σ.
- **"c0_quoted" = 2 × c0 of Eq. (DNP) taken literally.** This is the only normalization that reproduces the paper's σ(c0).

### 1. What the continuum file is
It is `CS_ASWZ = γ_lat(b_T, a) − k1·a/b_T` with **k1 = 0.213649** at every point, and σ = the raw per-point stat⊕syst diagonal error, unchanged. It carries no covariance and no k1 uncertainty. Two things about that k1:
- It is **not** the quoted best fit k1 = 0.22(8), which would round from ≥0.215.
- It is not our (c0,k1) refit either (0.236). The closest configuration we found is (c0,c1,k1) at 0.2134, which may be a coincidence.

So it is "per-ensemble data with one fixed k1 subtracted". It is not an independent continuum extrapolation per b_T; the paper itself says (L293) that such an extrapolation would need matched b_T values across ensembles, which they don't have.

### 2. Option A — the paper's parametrization and numbers (arXiv:2402.06725, `main.tex`)

- **Eq. (CSkernelparam)** (L314): γ_q^param(b_T, μ, a) = −2 D_res(b\*, μ) − 2 D_NP(b_T; B_NP, c0, c1) + k1·a/b_T + k2·a²/b_T².
- **Eq. (DNP)** (L323): D_NP = b_T b\* [c0 + c1 ln(b\*/B_NP)], with b\* = b_T/√(1 + b_T²/B_NP²).
- **Supp. Eq. (dres)** (L510): D_res(b\*, μ) = ½K(μ, μ_b\*) + d[α_s(μ_b\*)] = ∫_{μ_b\*}^{μ} dμ'/μ' Γ_cusp + d. Here μ_b\* = 2e^{−γE}/b\*, with Γ_cusp at 4 loops (the paper also mentions an approximate 5-loop term) and d at 4 loops (d_0 = d_1 = 0; d_2 and d_3 are in the text). The running is 4-loop, with α_s(2 GeV) = 0.293 and n_f = 4 (L578); μ = 2 GeV and the scheme is MSbar.
- **AIC-best model** (L338–345): free (c0, k1), with c1 = k2 = 0 and B_NP = 2 (GeV⁻¹). The fit gives **c0 = 0.032(12), k1 = 0.22(8), χ²/dof = 0.39**.
  - **No c0–k1 correlation is quoted.** We find ρ(c0, k1) = +0.43.
  - The (c0,k2) and (c0,k1,k2) fits are said to give consistent c0, with σ within ≲10% (L360). |k1| and |k2| are in 0.1–0.3 (L361). Freeing B_NP or c1 gives consistent c0 with larger σ (L362).
  - The paper's comparisons are c0^SV19 = 0.043(11) with B_NP^SV19 = 1.9(2), and c0^ART23 = 0.037(6) (L358).
- **BLNY alternative** (L364–366): D_NP = g2 b², B_NP = 1.5, **g2 = 0.085(26)**, χ²/dof = 0.58. We could not reproduce this (see Log).

### 3. Reproduction: fit table
The table is per-ensemble data (21 points, 3 ensembles), numeric 4-loop D_res, and B_NP = 2 GeV⁻¹ unless freed. `(paper)` in the top row means the paper's closed-form D_res variant.

| model | cov | χ²/ndf | AIC | c0 (Eq. literal) | c0_quoted | k1 | k2 / other |
|---|---|---|---|---|---|---|---|
| **c0,k1** (paper AIC-best) | full | **7.31/19 = 0.385** | **11.31** | 0.0152(60) | **0.0305(120)** | 0.236(66) | — |
| c0,k1 (paper D_res) | full | 7.36/19 = 0.387 | 11.36 | 0.0182(60) | 0.0364(120) | 0.239(66) | — |
| c0,k2 | full | 8.77/19 = 0.46 | 12.77 | 0.0094(55) | 0.0188(110) | — | k2 = 0.240(72) |
| c0,k1,k2 | full | 7.15/18 = 0.40 | 13.15 | 0.0177(85) | 0.0353(171) | 0.34(27) | k2 = −0.12(29) |
| c0,c1,k1 | full | 7.22/18 = 0.40 | 13.22 | 0.0183(121) | 0.037(24) | 0.213(100) | c1 = 0.017(57) |
| c0,k1,B_NP | full | 7.16/18 | 13.16 | 0.0001(52) | 0.000(10) | 0.222(66) | B_NP → 2.5, **at the bound** |
| c0 only (no lattice term) | full | 19.93/20 | 21.93 | 0.0060(54) | 0.012(11) | — | — |
| c0,k1 | diag | 8.23/19 = 0.43 | 12.23 | 0.0138(57) | 0.0276(114) | 0.236(66) | — |

The paper's statements that we reproduce:
- (c0,k1) has the minimum AIC. The single-term fits are preferred over (c0,k1,k2) by 1.8 (k1) and 0.4 (k2) in AIC, matching the theorist's "mild AIC preference".
- χ²/dof = 0.39.
- σ(c0) = 0.012 in the quoted convention.
- c0 = 0.032 lies between our two D_res variants, 0.031 and 0.036.
- k1 = 0.236 against 0.22.

Where we do not match:
- σ(k1) is 0.066 for us against 0.08 in the paper (a bootstrap spread, perhaps).
- The paper says the (c0,k1,k2) σ(c0) is within 10%; ours is +43% larger.
- **B_NP is not constrained by the data.** χ² falls monotonically as B_NP grows, so B_NP runs until μ_b\*(0.9 fm) hits the 4-loop n_f = 4 Landau pole (about 0.47 GeV), so we cap it at 2.5 GeV⁻¹. Fits with B_NP free are therefore not meaningful as they stand.
- Some discretization term is clearly needed: the fit with no lattice term has Δχ² = 12.6 for one fewer parameter.

[old figure, removed: ASWZ per-ensemble data with the (c0,k1) fit at each a (dashed) and at a=0 (black, 1σ band from c0 only). B_NP=2 GeV⁻¹, numeric 4-loop D_res; c0 shown in both conventions.]

*Caveat for the figure:* the band is c0-only at a = 0. The dotted curve is −2D_res(b\*) alone. The yellow band marks b_T < 0.2 fm, where the lattice adds nothing beyond PT.

### 4. What the continuum file loses
Every row fits c0 at a = 0 with B_NP = 2, in the quoted convention.

| input | c0_quoted | σ(c0) | vs (b) |
|---|---|---|---|
| (b) per-ensemble, full cov, free k1 — **reference** | 0.0305 | 0.0120 | — |
| (a) continuum file, diagonal errors | 0.0257 | 0.0101 | σ −16%, central −0.4σ |
| (c) continuum file, full ensemble cov | 0.0287 | 0.0109 | σ −9% |
| (d) continuum file, diag + k1 ± 0.08 as a correlated (a/b_T) syst | 0.0268 | 0.0109 | — |
| (e) continuum file, full cov + k1 ± 0.08 as a correlated syst | 0.0298 | 0.0116 | ≈(b); double-counts k1 info |

The loss breaks into three parts:
1. **The k1 uncertainty** is the largest effect. It is a term σ_k1·a/b_T = 0.066/n, fully correlated across all points and ensembles. At the first point of each ensemble (b_T = a) it is 61%, 55% and 36% of the stat error for L32, L48 and L64. It accounts for half of the σ(c0) deficit.
2. **Correlations within an ensemble** are small. The off-diagonal correlations have median 0.03, 0.01 and 0.05 (L32, L48, L64), with a maximum of +0.26 (L64 near 0.54–0.63 fm) and a minimum of −0.15 (L48). This is the other half, about 9% of σ(c0).
3. **The c0–k1 correlation** of ρ = +0.43 is invisible in the file.

The central shift from using k1 = 0.2136 instead of refitting (0.236) is ≤ 0.022 per point, which is negligible. **For Option B, use the per-ensemble files, the block-diagonal covariance and a free k1 (or k1 plus a nuisance); do not use the continuum file.**

[old figure, removed: Continuum file points vs the a=0 curve from the per-ensemble fit (black) and from a diagonal-error fit to the continuum file (red).]

[old figure, removed: Per-ensemble correlation matrices (b_T in fm).]

### 5. The b_T < 0.2 fm points and the 0.9 fm edge
Fit (c0,k1), full covariance:

| b_T range [fm] | points | c0_quoted | k1 |
|---|---|---|---|
| all | 21 | 0.0305(120) | 0.236(66) |
| ≥ 0.2 | 17 | 0.032(15) | 0.25(14) |
| ≤ 0.8 | 19 | 0.032(12) | 0.24(7) |
| 0.2–0.8 | 15 | 0.034(16) | 0.27(14) |

- The b_T < 0.2 fm points (b_T = a, and b_T = 2a on L64) are exactly where a/b_T is largest. They carry **half the k1 constraint**: dropping them doubles σ(k1) and raises σ(c0) by 25%, while c0 itself barely moves.
- So the lattice points below 0.2 fm mainly calibrate the lattice artefact, not the kernel. That agrees with the theorist's "adds nothing beyond PT" for the kernel itself.
- The points above 0.8 fm (L32 at 0.9 and L48 at 0.84) have σ of 0.37 and 0.73 and hardly matter.
- Nothing constrains the kernel beyond 0.9 fm, and B_NP (the b\* saturation) is not determined by the data at all.

---

