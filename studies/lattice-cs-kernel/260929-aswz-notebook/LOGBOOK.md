---
title: ASWZ authors' Mathematica notebook vs our CS-kernel refit
slug: 260929-aswz-notebook
study: lattice-cs-kernel
status: done        # active | done | paused | abandoned
created: 2026-09-29
updated: 2026-09-29
owner: study-worker
---

# ASWZ authors' Mathematica notebook vs our CS-kernel refit

**Task:** What does the lattice authors' own Mathematica notebook (`MILC_all_phys_beam_25.nb`) do for the CS-kernel fit? And does it explain why their quoted σ(c0) = 0.012 and σ(k1) = 0.08 (Eq. 9) are larger than our 0.0060 and 0.066 from the per-ensemble covariances?

> **Confidentiality.** The notebook is the authors' unpublished private code, and this page is public. Below I only summarise what the code does and quote a few short formulas. The parsed notebook, the transcription of their kernel and all intermediate dumps are in
> `/work/submit/lavezzo/cs_kernel/notebook_extract/`, which is not published.

---

## START HERE (status as of 2026-09-29)

> **The σ mismatch is explained. Their fit and data are the same as ours; their error procedure is not.**
> - **Data and χ²:** they fit the same per-ensemble central values, total σ and correlations we have (the correlations agree to 1e-16). The χ² is the same correlated χ² we use.
> - **The error:** each pseudo-experiment shifts all the points of an ensemble by one common Gaussian number times (Corr·σ). That is a fully coherent shift within each ensemble, not a draw from the stated covariance. They then quote the 68% half-width over 200 refits.
> - **Our re-implementation of that rule:** σ(c0) = 0.0115 and σ(k1) = 0.070. Their notebook prints 0.0117 and 0.0676; the paper quotes 0.012 and 0.08.
> - **A correct resampling of the covariance** gives back our 0.0060 and 0.066.
> - **Central values:** our python transcription of their perturbative kernel reproduces their (c0,k1) fit to every printed digit: c0 = 0.032999, k1 = 0.213649, χ²/dof = 0.386788.

- **Next action:** none; the task is closed. The orchestrator decides what goes back to the authors (see Open questions).
- **Blocking on:** nothing. No Mathematica was needed.

---

## Log

### 2026-09-29
- **Parsing.** The notebook is Mathematica 12.1 box format, 80 MB. I wrote a box→text parser (`notebook_extract/nbparse.py`), which gave 5479 cells: 1294 Input, 581 Output, 3393 Print, and 31 subsections. The ~28 / 123 / 1464 counts in the brief are too low; each input cell holds several statements, and there are many plot cells.
  - Structure: Perturbative Part → Simple version (dispersion relation, WF plots, Read-in, a series of "Fit Functions X / Fit X" pairs) → "Too complicated".
  - "Too complicated" is an older, abandoned approach: per-(P^z₁, P^z₂) CS data with explicit power corrections, χ²/dof 2–6. It is not what the paper uses.
- **Data check.** The fit reads `CS_Pz_x_ave_L{32,48,64}.csv` plus `_correlations.csv` and `_stat_vs_total_uncertainty.csv`.
  - It builds a covariance as follows: the stat covariance is (ratio·σ)(ratio·σ)ᵀ∘Corr, and the diagonal is then topped up to the total σ² (a systematic that is diagonal only).
  - Their printed full correlation matrices equal the correlations of our `*_covariance.csv` files to 1.1e-16, and their printed Around[] tables match our CSV central values and σ. **So our tarball is exactly their fit input.** (evidence: `notebook_extract/cells.pkl` cells 560/583/602 vs `../260923-lattice-data-refit/data`)
- **No bootstrap samples of the CS kernel appear anywhere in the notebook, embedded or read in.** Raw bootstraps are read only upstream, in the wave-function and renormalisation cells, from the authors' local disk. Nothing embedded is worth extracting.
- **The error procedure.** The notebook defines a function χ2boot, the same in all 8 fit sections:
  - It is the ordinary correlated χ², with the data vector of ensemble e shifted by `z_e · (Corr_e · σ_e)`.
  - `z_e` is a **single** `RandomVariate[NormalDistribution[0,1]]`, a scalar, drawn once per ensemble per pseudo-fit.
  - NMinimize evaluates the objective symbolically first, so the three z's are frozen for each fit.
  - The procedure repeats this for Nboot = 200 (30 in the model-average runs, 10 in the free-B_NP run) and quotes `CI[x] = ½(Q_84.13% − Q_15.87%)`, or StandardDeviation in the model-average function.
- **Re-implemented** analytically and with a 200-sample MC. `sigma_repro.py` reuses our `cs_fit.py` design matrix; output in `sigma_repro_output.txt`. Its results are in the Result table.
  - Control 1: a proper full-covariance bootstrap with the same estimator gives our GLS σ back.
  - Control 2: a per-point (vector) draw times Corr·σ gives σ(c0) = 0.0074, which does not match. So the scalar-per-ensemble reading is the one the numbers support.
- **Central values.** I transcribed their `CSKnew[3,b]` and the fit into `notebook_extract/nb_dres_repro.py` (private). The (c0,k1), (c0,k2), c0-only and BLNY fits reproduce the notebook's printed c0, k and χ²/dof to all printed digits. (evidence: `notebook_extract/nb_dres_repro_output.txt`)

---

## Result

**Caveats first.**
- Everything here is at fixed B_NP (2 GeV⁻¹, or 1.5 for BLNY). The model is then linear, so every σ below depends only on the design and the covariance, not on D_res.
- The covariance is block-diagonal across ensembles, both in the notebook and in ours.
- The notebook is a snapshot, not necessarily the exact state that produced the paper. The paper's k1 = 0.22(8) is not printed by any (c0,k1) run in it; see §4.
- MC estimates with 200 samples carry about 5% estimator noise (the 16–84% band over seeds is given).

### 1. What their fit function is (vs ours)

| ingredient | notebook | our `260923-lattice-data-refit/cs_fit.py` | same? |
|---|---|---|---|
| model | γ = γ_pert(b*) + γ_NP + k·lTerm(a,b) | same | ✓ |
| γ_NP normalisation | −2·b_T·b*·(c0 + c1 ln(b*/B_NP)) | −2·b_T·b*·c0 (literal Eq. DNP) | ✓ confirms the 09-24 retraction: no factor 2 |
| b* | b_T/√(1+b_T²/B_NP²), B_NP in **GeV⁻¹** | same | ✓ the paper's "B_NP = 2 GeV" is a unit typo |
| μ_b* | 2e^{−γE}/b*, ħc = 0.1973 | 2e^{−γE}/b*, ħc = 0.19733 | ✓ (BLNY cells use 0.197326) |
| cusp | Γ0…Γ3, i.e. 4-loop cusp ("N3LL") | Γ0…Γ3 | ✓ |
| non-cusp | 2-loop d20 at a_s², 3-loop d30 at a_s³ | same, after the 09-24 fix | ✓ **our d_n fix is what they do** |
| 5-loop cusp Γ4, 4-loop d40 | present in the code but used only at N4LL, which no fit uses | absent | ✓ |
| α_s | closed-form N3LO expansion in X = 1 + a0·b0·ln(μ²/4) with α_s(2 GeV) = 0.293 and n_f = 4 | numeric 4-loop RGE ("numeric"), or the same closed form ("paper") | ≈ |
| resummed K | closed-form N3LL η(μ_b*, μ) with expansion parameter **a_s(μ_b*)** | numeric ∫Γ ("numeric"); our "paper" variant expands in a_s(μ) | ≈ this is why our "paper" c0 = 0.0346 ≠ their 0.0330 |
| μ | 2 GeV | 2 GeV | ✓ |
| lattice terms | k1·a/b_T; k2·(a/b_T)²; k1 and k2 together; also (a/b_T)² + (a/b_T)⁴ | k1, k2 | ✓ |
| χ² | correlated χ², per-ensemble full covariance, block-diagonal | same | ✓ |

The perturbative ingredients differ from ours only in the truncation of α_s and K. That moves c0 by 0.0006 (0.1σ): our numeric 0.0324 against their 0.0330.

### 2. Their data
- It is the same 21 points (L32: 6, L48: 7, L64: 8) with the same σ and the same correlations as our tarball.
- The total σ = stat ⊕ a diagonal-only systematic. The files that define that split (`*_stat_vs_total_uncertainty.csv`) are produced outside this notebook, so **what the systematic contains is not visible here.**
- The only renormalisation-scale variation the notebook itself shows is upstream, in the wave-function cells. There the Z-factor error is its stat error ⊕ half the range over ξ_R ∈ {2,3,4} × p_R ∈ {6,8,10} (L48: {8,10,12}), and it is propagated by Gaussian-sampling Z into the 200 WF bootstrap samples.
- **So the "RG-scale variation" from the email is already in the per-point σ we have.** Whether it sits in the stat or in the diagonal part cannot be told from the notebook.
- For L32 the stat fraction is only 17–32% of the total σ; the ratio vector is printed only for L32. The uncertainty budget is therefore dominated by a systematic that the covariance treats as uncorrelated from one b_T point to the next.
- A commented-out older version of the tables (2-digit, L32 without the 0.9 fm point) is also present. Refitting it with the current correlations gives c0 = 0.034 and k1 = 0.224, so it does not single out the paper's 0.032 (`notebook_extract/old_data_check.py`).

### 3. Their uncertainty procedure, and the reproduction

The fit is ordinary. Only the error comes from pseudo-experiments, in which each ensemble e is shifted coherently:

  y_e → y_e − z_e · (R_e σ_e),   z_e ~ N(0,1), **one scalar per ensemble**  (R_e = correlation matrix)

(R_e σ_e)_i / σ_i ranges from 1.0 to 2.4 (L64 up to 2.4), so every point of an ensemble moves by about its full σ, all in the same direction. The implied parameter covariance is Σ_e (A u_e)(A u_e)ᵀ with u_e = R_e σ_e, a rank-3 covariance. It is not the covariance used in the χ².

| fit (B_NP) | param | our GLS (stated cov) | **their rule, analytic** | their rule, MC 200 (16–84% over seeds) | **notebook printed** (CI-200 / SD-30) | paper |
|---|---|---|---|---|---|---|
| c0,k1 (2) | c0 | 0.0060 | **0.0115** | 0.0114 (0.0108–0.0121) | **0.0117** / 0.0108 | 0.012 |
| | k1 | 0.066 | **0.070** | 0.070 (0.066–0.074) | **0.068** / 0.060 | 0.08 |
| | ρ(c0,k1) | +0.43 | **−0.94** | | | – |
| c0,k2 (2) | c0 | 0.0055 | 0.0131 | 0.0130 (0.0123–0.0139) | 0.0121 / 0.0137 | "σ within 10%" |
| | k2 | 0.072 | 0.075 | 0.075 (0.070–0.079) | 0.069 / 0.079 | |
| c0,k1,k2 (2) | c0 | 0.0085 | 0.0124 | 0.0122 (0.0115–0.0130) | 0.0138 | "σ within 10%" |
| | k1 | 0.27 | 0.11 | 0.11 (0.104–0.119) | 0.096 | |
| c0 only (2) | c0 | 0.0054 | 0.0141 | 0.0140 | – / 0.0126, 0.0129 | |
| BLNY g,k1 (1.5) | g (γ_NP = −g b²) | 0.0065 | 0.0124 | 0.0123 (0.0115–0.0131) | 0.0119 | g2 = 0.085(26) = 2g |
| | k1 | 0.064 | 0.082 | 0.082 | 0.072 | |

(evidence: `sigma_repro_output.txt`, `sigma_repro.json`; notebook prints in `notebook_extract/cells.txt`)

**Physics read.**
- **σ(c0).** The coherent per-ensemble shift behaves like a nuisance that is 100% correlated across b_T within an ensemble, with a size of about its total σ. A shift that is flat or rising in b_T cannot be absorbed by k1·a/b_T, which falls with b_T. It maps almost entirely onto the c0·b_T·b* column, and that is what doubles σ(c0).
  - The a/b_T term absorbs shifts at small b_T, so σ(k1) barely changes (0.066 → 0.070).
  - The sign of the c0–k1 correlation flips (+0.43 → −0.94).
- **This also explains the paper's statement that σ(c0) of (c0,k1,k2) is "within 10%"** of (c0,k1). Under their rule it is +8% (0.0124 vs 0.0115). With the stated covariance it is +42%, which is what puzzled us before.
- **Is it a bug or a deliberate error model?** The code cannot tell us.
  - Read literally, it is not a bootstrap of the given covariance.
  - The deliberate reading: the dominant non-stat component (about 90–97% of the variance on L32; its content is not visible in the notebook) is plausibly coherent across b_T. Then a coherent shift is a more realistic error model than the diagonal systematic that is in the covariance.
  - The small χ²/dof = 0.39 fits that picture: diagonal systematics that are really correlated inflate the per-point errors.
  - Only the authors can say which reading they intended.
- **What it means for us.** Our GLS σ is the correct σ *for the covariance they gave us*. Their σ corresponds to a different, unstated error model, and it cannot be written as a usable χ² covariance, since it is rank 3.
  - If the coherent reading is the physically right one, the lattice constraint on the NP CS kernel is weaker than our current Option-B prior in the c0-like, large-b_T direction, by up to about 2×.
  - The right fix is the stat/syst split with the systematic's b_T correlation, not a rescaling.

### 4. Every fit result the notebook prints (fixed B_NP = 2 GeV⁻¹ unless stated)

| section | model | c0 (or other) | k | χ²/dof |
|---|---|---|---|---|
| Fit l1 (a/bT) | c0 | 0.02459 ± 0.0129 (SD-30) | – | 0.886 |
| | c0,c1 † | c0 = 0.196 ± 0.052, c1 = 0.092 ± 0.033 | – | 0.614 |
| | **c0,k1** | **0.032999 ± 0.0117 (CI-200)**; 0.0330 ± 0.0108 (SD-30) | **k1 = 0.213649 ± 0.0676** (0.0601 SD-30) | **0.386788** |
| | c0,c1,k1 † | c0 = 0.0396 ± 0.077, c1 = 0.0037 ± 0.044 | k1 = 0.209 ± 0.089 | 0.408 |
| | AIC model average over the 4 above † ‡ | c0 = 0.0471 ± 0.0201 | k1 = 0.212 ± 0.066 | – |
| | c0,k1,B_NP (10 samples) | c0 = 0.027 ± 0.49, B_NP = 2.46 ± 1.16 | k1 = 0.222 ± 0.157 | 0.401 |
| Fit l1 (a/bT)² | c0,k2 | 0.02773 ± 0.0121 (CI-200); ± 0.0137 (SD-30) | k2 = 0.220354 ± 0.0688 (**0.0786** SD-30) | 0.4375 |
| | c0,c1,k2 † | c0 = 0.099 ± 0.055, c1 = 0.039 ± 0.031 | k2 = 0.177 ± 0.074 | 0.422 |
| | AIC average † ‡ | c0 = 0.0675 ± 0.0211 | k2 = 0.206 ± 0.068 | – |
| l1 (a/bT) + l2 (a/bT)² | c0,k1,k2 | 0.03397 ± 0.0138 | k1 = 0.236 ± 0.096, k2 = −0.037 ± 0.107 | 0.4084 § |
| l1 (a/bT)² + l2 (a/bT)⁴ | c0,k2,k4 | 0.03146 ± 0.0126 | 0.521 ± 0.119, −0.327 ± 0.056 | 0.3998 |
| Fit l1 (a/bT) BLNY (B_NP = 1.5) | γ_NP = −g b², k1 | g = 0.042746 ± 0.0119 (√g = 0.207 ± 0.029) | k1 = 0.1487 ± 0.072 | 0.578629 |
| BLNY MAP (MAP b*, B = 2e^{−γE}) | γ_NP = −2g² b², k1 | g = 0.1586 ± 0.022 (0.0196 with 10 samples) | k1 = 0.188 ± 0.086 | 0.627 |
| BLNY MAP + k2 | g, k1, k2 | g = 0.1517 ± 0.027 | k1 = −0.003 ± 0.166 | 0.620 |
| "Ted" (HSO form, m_K = 0.3) | b_K, k1 | b_K = 0.633 ± 0.190 | k1 = 0.229 ± 0.069 | 0.3847 |

† The c1 term is coded as c1·ln(b*/B_NP) with **b\* in fm and B_NP in GeV⁻¹**. That is a unit slip: it adds c1·ln(0.1973) = −1.62·c1 to the meaning of c0. It leaves χ² unchanged, but the printed c0 of every c1 fit is shifted.
- Converted to the consistent convention, the (c0,c1,k1) c0 is 0.0396 − 1.62·0.0037 = 0.0336, against our 0.0331.
- The model averages mix these shifted c0 values in.

‡ In the model-average function the between-model spread is a weighted variance, which is then squared again when combined, `√(err² + var²)`. It should be `√(err² + var)`. The effect is negligible here, since var is tiny.

§ Their NMinimize stopped short of the minimum in the (c0,k1,k2) fit: the true minimum is χ² = 7.306 (ours and our transcription), while they report 7.350, along the ρ ≈ −0.99 k1–k2 valley. The same under-convergence plausibly explains the low 0.096 for σ(k1) in that fit, against the 0.11 their rule predicts.

**Mapping to the paper.**
- **Eq. 9, c0 = 0.032(12).** This is the (c0,k1) fit, 0.0330 ± 0.0117. The notebook would round to 0.033(12); the paper has 0.032.
- **k1 = 0.22(8).** No (c0,k1) run prints σ(k1) = 0.08; they print 0.068 and 0.060, and their rule predicts 0.070 (MC band 0.066–0.074), so 0.08 is outside estimator noise. The printed "0.220354 ± 0.0786" is the (a/b_T)² (c0,k2) fit.
  - The paper's k1 = 0.22(8) therefore looks like it was taken from the k2 fit, or from an earlier notebook state. **Not settled; ask the authors.**
  - The central value 0.2136 is the one used in their continuum file.
- **BLNY g2 = 0.085(26), χ²/dof 0.58.** The notebook fits γ_NP = −g·b² and gets g = 0.0427(119), χ²/dof 0.5786. The paper's number is 2g, i.e. the paper's convention is γ_NP = −(g2/2)·b², and its σ ≈ 2 × 0.0124–0.0119.
  - Relative to our literal "−2·D_NP, D_NP = g2 b²", this is the factor 4 we found: our g2 = 0.0212 = g/2 = g2_paper/4. **Confirmed.**
  - The notebook's pheno curves use γ ∋ −g2·b² (gKBLNY is redefined from g2/2·b² to g2·b²). The doubling to the quoted 0.085 is inferred from the numbers; no cell shows it.
- **SV19 and ART23 comparisons** use the same −2·c0·b·b* form, so the comparison with the ART23 c0 = 0.037(6) is like-for-like.

### 5. Other discrepancies with our reproduction
- **d_n indexing:** their code puts the 2-loop d at a_s² and the 3-loop d at a_s³, so our 09-24 fix is right. The off-by-one exists only in the supplement's text.
- **B_NP units:** GeV⁻¹ in the code, as we assumed.
- **Model averaging:** it exists in the notebook but is **not** what Eq. 9 quotes. The averages (0.047 and 0.068) are inflated by the c1 unit slip.
- **"Fit the original bootstraps" (email):** not in this notebook. The CS-kernel fits use central values, σ and correlation plus the synthetic coherent shifts described above. If the paper's numbers really came from per-bootstrap fits, that code is not here.

---

## Findings

1. The notebook's CS-kernel fit uses exactly our per-ensemble data and covariance (correlations equal to 1e-16), the literal Eq. (DNP) −2·c0·b_T·b\*, B_NP in GeV⁻¹, the 4-loop cusp, and 2- and 3-loop non-cusp terms at a_s² and a_s³. Our python transcription reproduces c0 = 0.032999, k1 = 0.213649 and χ²/dof = 0.386788 exactly. — (`notebook_extract/nb_dres_repro_output.txt`)
2. **Their quoted σ come from pseudo-experiments that shift each ensemble coherently by one N(0,1) scalar times Corr·σ, not from the stated covariance.** The analytic version of that rule gives σ(c0) = 0.0115 and σ(k1) = 0.070 (notebook 0.0117 and 0.068; paper 0.012 and 0.08). A proper resampling gives our 0.0060 and 0.066. — (`sigma_repro_output.txt`)
3. Their rule also explains the paper's "(c0,k1,k2) σ within 10%" claim (+8% under the rule, +42% with the true covariance), and the BLNY σ.
4. The BLNY g2 quoted in the paper is 2× the notebook's fitted γ_NP = −g·b² coefficient, which is 4× our literal convention. The χ²/dof matches (0.5786).
5. The notebook has a unit slip in the c1 term (ln of fm over GeV⁻¹), a variance-squared line in the model average, and one under-converged NMinimize (in c0,k1,k2). None of these affects Eq. 9.
6. The paper's σ(k1) = 0.08 is not produced by any (c0,k1) run in the notebook. It matches the (c0,k2) run's printed "0.220354 ± 0.0786".

---

## Open questions

These are for the orchestrator or Luca to take to the authors:

- Is the coherent per-ensemble shift (one scalar z per ensemble) intentional, i.e. a model for a b_T-correlated renormalisation systematic, or should it have been a vector draw from the covariance?
- If it is intentional, can they give us the stat/syst split for L48 and L64 (the `*_stat_vs_total_uncertainty.csv` files; only the L32 ratios are printed) and the b_T correlation of the systematic? Then we can build a proper covariance instead of either extreme.
- Where does k1 = 0.22(8) come from: the (c0,k2) run, or a different notebook state?
- Their email says they fit "original bootstraps", but this notebook does not. Is there another code path behind the paper?
- For our Option-B prior (`260923-scetlib-kernel-fit`, λ2_ν = 0.1345 ± 0.031): if the coherent reading holds, the lattice σ in the large-b_T NP direction may be up to 2× larger. That is not evaluated here; it is out of scope.

**Files.**
- Published, in this task directory: `sigma_repro.py`, `sigma_repro_output.txt`, `sigma_repro.json`. They use only our own data and design matrix, plus a description of the rule.
- Private, in `/work/submit/lavezzo/cs_kernel/notebook_extract/`: `nbparse.py` (box parser); `cells.txt` and `cells.pkl` (the parsed notebook); `nb_dres_repro.py` and its output (transcription of their kernel); `old_data_check.py`.
