# Theory Weights and Corrections — Final State (2026-04-20)

Describes the post-fix behavior of systematic histograms in `mz_dilepton` (and similar).
Each histogram is built in two steps: a **tensor weight** (constructed in
`theory_corrections.py` or related code) and a **fill weight** (applied in
`systematics.py` when booking the histogram). This note shows the formula at each step.

---

## 0. Notation

**Order of definition matters.** The weight columns are built by `build_weight_expr`,
which includes factors that exist as columns at the time of the call. So
`nominal_weight_uncorr` (defined early in `define_theory_corr`) does NOT include
`ew_theory_corr_weight` (defined later in `define_ew_theory_corr`). The later
columns (`nominal_weight`, `nominal_weight_pdf_uncorr`) DO include it.

Primitive weights:
- `w_raw` = `weight · exp_weight` (MC weight × experimental SFs; always present)
- `pdf_c` = `central_pdf_weight` (central member of `args.pdfs[0]`, helicity-smoothed if available)
- `tc` = `theory_corr_weight` (central of `theoryCorr[0]`; defined inside `define_theory_corr`)
- `ew_tc` = `ew_theory_corr_weight` (central of `ewTheoryCorr[0]`; defined in `define_ew_theory_corr`. `= 1` when no explicit EW-central correction)

Composite weight columns (in order of definition):

```
(in define_theory_corr, BEFORE ew_tc exists)
nominal_weight_uncorr             = w_raw · pdf_c                            (no tc, no ew_tc)
nominal_weight_pdf_theory_uncorr  = w_raw                                    (no pdf_c, no tc, no ew_tc)  ← NEW

(in define_ew_theory_corr, BEFORE ew_tc exists at the outer scope)
nominal_weight_ew_uncorr          = w_raw · pdf_c · tc                       (no ew_tc)

(in define_nominal_weight)
nominal_weight                    = w_raw · pdf_c · tc · ew_tc               (all four)

(in define_pdf_columns, AFTER ew_tc exists)
nominal_weight_pdf_uncorr         = w_raw · tc · ew_tc                       (no pdf_c)
```

In practice `ew_tc = 1` for typical analyses (no active EW-central correction), so
the distinction rarely matters numerically — but the formulas below use the precise
factors.

---

## 1. Two-step structure

For each histogram:

- **Step 1 — tensor**: a per-event array `tensor[...]` indexed by (variation axis[, helicity mode]).
  Built either as a column in `theory_corrections.py`, or via a correction helper that multiplies an input weight by pre-computed kinematic correction factors.

- **Step 2 — fill weight**: what's actually passed to `HistoBoost` as the per-event weight. For most histograms this is just the tensor itself (no extra factor), but some multiply the tensor by an additional "prefactor" column.

Below, each entry shows both steps. The final fill weight (per event, per variation bin) is the product shown at the bottom.

---

## 2. Histogram catalog

### 2.1 Plain `nominal` histogram

- **Step 1 — tensor**: n/a (scalar weight)
- **Step 2 — fill weight**: `nominal_weight = w_raw · pdf_c · tc · ew_tc`

Depends on `theoryCorr[0]`: yes (via `tc`, by design — this is the analysis nominal).

---

### 2.2 `{gen}_Corr` — base theory correction (not in `theory_corr_weight_map`)

From `define_theory_corr`. `{gen}_corr_weight` is aliased to `nominal_weight_uncorr`.

- **Step 1 — tensor** (via `makeCorrectionsTensor` helper, `tensor_weight=False`):
  ```
  {gen}Weight_tensor[i] = correction_helper(kin, {gen}_corr_weight)[i]
                        = correction[kin, i] · nominal_weight_uncorr
                        = correction[kin, i] · w_raw · pdf_c
  ```
  Yes, `pdf_c` IS in the fill weight — because the analysis nominal event weight
  already includes `pdf_c`, and this template represents "apply this correction to
  the analysis-nominal-weighted event". At i=0, `correction[kin, 0] = tc` (by the
  definition of `theory_corr_weight`), so this reduces to `tc · w_raw · pdf_c`.
  This matches the plain `nominal` weight (`w_raw · pdf_c · tc · ew_tc`) up to the
  missing `ew_tc` factor, which is 1.0 in typical runs.
- **Step 2 — fill weight**: `{gen}Weight_tensor[i]` (no extra factor)

Depends on `theoryCorr[0]`: no.

---

### 2.3 `{gen}_Corr` — pdfvars/pdfas (in `theory_corr_weight_map`)

From `define_theory_corr_weight_column` + `makeCorrectionsTensor` helper with `tensor_weight=True`.

#### What `entry_i` contains (from `expand_pdf_entries(pdf_of_correction, alphas, renorm)`)

Using `pdf_member_k = pdfBranch[first_entry + k]` = event-level PDF member k from the
**correction's own PDF set** (the `pdf` argument in `make_theory_corr_weight_info`):

| case | `entry_i` (after clamp) |
|---|---|
| non-alphas, non-renorm (typical `_pdfvars`) | `pdf_member_i` |
| alphas, non-renorm (rare) | `alphas_i` |
| alphas, renorm (typical `_pdfas`) | `(alphas_i / alphas_0) · pdf_member_0` |
| non-alphas, renorm (e.g. MSHT20mbrange) | `pdf_member_i` (the `/pdf_member_0 · pdf_member_0` cancels) |

Key point: `entry_i` carries the **correction's own PDF central** (`pdf_member_0`)
inside it, not `args.pdfs[0]`'s central (`pdf_c`). So the "template central" (i=0)
is anchored to the correction's PDF.

#### Weight formula

- **Step 1a — corr weight tensor** (per PDF/alphaS variation entry):
  ```
  {gen}_corr_weight[i] = entry_i · nominal_weight_pdf_theory_uncorr
                       = entry_i · w_raw
  ```
  Previously written as `entry_i · nominal_weight_uncorr / central_pdf_weight`
  (relied on `pdf_c` cancellation); cosmetic cleanup replaced it with the explicit
  column that excludes both `central_pdf_weight` and `theory_corr_weight` from the start.
- **Step 1b — correction tensor** (helper convolves correction with corr weight tensor):
  ```
  {gen}Weight_tensor[i] = correction[kin, i] · entry_i · w_raw
  ```
- **Step 2 — fill weight**: `{gen}Weight_tensor[i]` (no extra factor)

Explicit per case:
- **pdfvars** (non-renorm): `fill[i] = correction[kin, i] · pdf_member_i · w_raw`
  - At i=0: `correction[kin, 0] · pdf_central_of_correction · w_raw`
- **pdfas** (renorm, alphas): `fill[i] = correction[kin, i] · (alphas_i/alphas_0) · pdf_central_of_correction · w_raw`
  - At i=0: `correction[kin, 0] · pdf_central_of_correction · w_raw` (since `alphas_0/alphas_0 = 1`)

Depends on `theoryCorr[0]`: no (no `tc`). Depends on `args.pdfs[0]`: no — the correction's
own PDF central appears via `entry_i`, not `args.pdfs[0]`'s central.

---

### 2.4 `{gen}_EWCorr` — EW theory correction

From `define_ew_theory_corr`. Note: `ew_theory_corr_weight` is not yet defined at the point where this tensor is built, so `build_weight_expr(df)` picks up `weight, central_pdf_weight, theory_corr_weight, exp_weight`.

- **Step 1a — corr weight**:
  ```
  ew_{gen}corr_weight = build_weight_expr(df) = w_raw · pdf_c · tc
  ```
- **Step 1b — correction tensor**:
  ```
  {gen}Weight_tensor[i] = correction[kin, i] · ew_{gen}corr_weight
                        = correction[kin, i] · w_raw · pdf_c · tc
  ```
- **Step 2 — fill weight**: `{gen}Weight_tensor[i]`

Depends on `theoryCorr[0]`: yes (carries `tc` by design).

---

### 2.5 `{gen}_Corr` — quark mass correction

From `define_quark_mass_theory_corr`. Called after `nominal_weight` is defined.

- **Step 1 — correction tensor** (helper directly takes `nominal_weight` as input):
  ```
  {gen}Weight_tensor[i] = correction_QMC[kin, i] · nominal_weight
                        = correction_QMC[kin, i] · w_raw · pdf_c · tc · ew_tc
  ```
- **Step 2 — fill weight**: `{gen}Weight_tensor[i]`

Depends on `theoryCorr[0]`: yes.

---

### 2.6 `pdfXXX` — primary-PDF uncertainty eigenvectors (non-helicity)

From `define_pdf_columns`, for each `pdf` in `args.pdfs`.

- **Step 1 — tensor**:
  - renorm:
    ```
    {pdf}Weights_tensor[i] = (pdf_i / pdf_0) · nominal_weight
                           = (pdf_i / pdf_0) · w · pdf_c · tc
    ```
    (`pdf_0` = raw LHE-weight first entry of this PDF set)
  - non-renorm:
    ```
    {pdf}Weights_tensor[i] = pdf_i · nominal_weight_pdf_uncorr
                           = pdf_i · w · tc
    ```
- **Step 2 — fill weight**: `{pdf}Weights_tensor[i]`

Depends on `theoryCorr[0]`: yes.

---

### 2.7 `pdfXXXalphaS002` — primary-PDF alphaS variations (non-helicity)

From `define_pdf_columns`, for PDFs with an `"alphasRange"` entry.

- **Step 1 — tensor**:
  ```
  {pdf}ASWeights_tensor[i] = alphaS_i · nominal_weight_pdf_uncorr
                           = alphaS_i · w · tc
  ```
- **Step 2 — fill weight**: `{pdf}ASWeights_tensor[i]`

Depends on `theoryCorr[0]`: yes.

---

### 2.8 `pdfXXXByHelicity` — primary-PDF uncertainty, helicity-decomposed

From `add_pdfUncertByHelicity_hist(from_theory_corr=False)` — called for each `pdf` in `args.pdfs`.

- **Step 1a — helper tensor** (per helicity mode h, per variation i; helper called with `unity`):
  - renorm: `helicity{pdf_name}Weight_tensor[h, i] = (pdf_i / pdf_c)[h, kin]`
  - non-renorm: `helicity{pdf_name}Weight_tensor[h, i] = pdf_i[h, kin]`
- **Step 1b — clamp and prefactor** (`safeTensor = clamp(tensor) · prefactor`):
  - renorm: `safeTensor[h, i] = (pdf_i/pdf_c)[h] · nominal_weight = (pdf_i/pdf_c)[h] · w_raw · pdf_c · tc · ew_tc`
  - non-renorm: `safeTensor[h, i] = pdf_i[h] · nominal_weight_pdf_uncorr = pdf_i[h] · w_raw · tc · ew_tc`
- **Step 2 — fill weight**: `safeTensor[h, i]`

Depends on `theoryCorr[0]`: yes.

---

### 2.9 `{gen}_pdfvars_CorrByHelicity` — theory-correction PDF variation, helicity-decomposed

From `add_pdfUncertByHelicity_hist(from_theory_corr=True)` — called for each pdfvars entry in `--theoryCorr`.

Note: here `pdf_c` in the helper tensor refers to the **correction's own PDF central**
(from the skim file, which was built for that specific correction's PDF set), not
`args.pdfs[0]`'s central. Contrast with §2.8 where `pdf_c` IS `args.pdfs[0]`'s central.

- **Step 1a — helper tensor** (per helicity mode, per variation; helper called with `unity`):
  - renorm: `helicity{pdf_name}Weight_tensor[h, i] = (pdf_i / pdf_central_of_correction)[h, kin]`
  - non-renorm: `helicity{pdf_name}Weight_tensor[h, i] = pdf_i[h, kin]` (the correction's PDF members, helicity-decomposed)
- **Step 1b — clamp and prefactor** (excludes `tc` and `ew_tc`):
  - renorm: `safeTensor[h, i] = (pdf_i/pdf_central_of_correction)[h] · nominal_weight_uncorr = (pdf_i/pdf_central_of_correction)[h] · w_raw · pdf_c_args`
  - non-renorm: `safeTensor[h, i] = pdf_i[h] · nominal_weight_pdf_theory_uncorr = pdf_i[h] · w_raw`
- **Step 2 — fill weight**: `safeTensor[h, i]`

Note: in the **renorm** case the helicity prefactor still carries `pdf_c_args` (from
`nominal_weight_uncorr`), mixing the correction's own PDF (in the ratio) with
`args.pdfs[0]`'s PDF (in the prefactor). This is a pre-existing inconsistency vs
the non-helicity `{gen}_Corr` path in §2.3, which uses only the correction's own PDF.
For renorm theory corrections (e.g., MSHT20mbrange) the two histograms are not
numerically identical in absolute scale, though the ratio within either histogram
is correct.

Depends on `theoryCorr[0]`: no.

---

### 2.10 `{gen}_pdfas_CorrByHelicity` — theory-correction pdfas, helicity-decomposed

From `add_pdfAlphaSByHelicity_hist` — called for each pdfas entry in `--theoryCorr`.

- **Step 1a — helper tensor**: `{name}_helicityAlphaSWeight_tensor[h, i] = alphaS_ratio[h, kin, i]`
- **Step 1b — clamp and prefactor**:
  ```
  safeTensor[h, i] = alphaS_ratio[h, i] · nominal_weight_uncorr
                   = alphaS_ratio[h, i] · w_raw · pdf_c
  ```
- **Step 2 — fill weight**: `safeTensor[h, i]`

Depends on `theoryCorr[0]`: no.

---

### 2.11 `qcdScaleByHelicity` — QCD scale, helicity-decomposed

From `add_qcdScaleByHelicityUnc_hist`. Helper is called with `nominal_weight` directly.

- **Step 1 — tensor** (helper convolves with input weight):
  ```
  helicityWeight_tensor[h, i] = qcdScale_ratio[h, kin, i] · nominal_weight
                              = qcdScale_ratio[h, kin, i] · w_raw · pdf_c · tc · ew_tc
  ```
- **Step 2 — fill weight**: `helicityWeight_tensor[h, i]`

Depends on `theoryCorr[0]`: yes.

---

### 2.12 `qcdScale` — non-helicity QCD scale variations

- **Step 1 — tensor**:
  ```
  scaleWeights_tensor_wnom[i] = scaleWeights_tensor[i] · nominal_weight
                              = scaleWeights[i] · w_raw · pdf_c · tc · ew_tc
  ```
- **Step 2 — fill weight**: `scaleWeights_tensor_wnom[i]`

Depends on `theoryCorr[0]`: yes.

---

### 2.13 `breitwigner_{mass,width}Weight{Z,W}` — BW shape variations

From `define_breit_wigner_weights`. Called after `nominal_weight` is defined.

- **Step 1 — tensor**:
  ```
  breitwigner_{mass|width}Weight{label}_tensor[i]
      = bw_weight[i] · nominal_weight
      = bw_weight[i] · w_raw · pdf_c · tc · ew_tc
  ```
- **Step 2 — fill weight**: `breitwigner_...Weight{label}_tensor[i]`

Depends on `theoryCorr[0]`: yes.

---

### 2.14 `massWeight{Z,W}`, `widthWeight{Z,W}`, `sin2thetaWeight{Z,W}`, `massWeight_widthdecor{Z,W}`

From `define_mass_width_sin2theta_weights`. Called after `nominal_weight` is defined.

- **Step 1 — tensor** (example for mass):
  ```
  massWeight_tensor_wnom[i] = massWeight[i] · nominal_weight
                            = massWeight[i] · w_raw · pdf_c · tc · ew_tc
  ```
  Same pattern for width, sin2theta, and massWeight_widthdecor.
- **Step 2 — fill weight**: `{...}_tensor_wnom[i]`

Depends on `theoryCorr[0]`: yes.

---

### 2.15 Experimental systematics (`nominal_effStatTnP_*`, `nominal_muonL1Prefire*`, etc.)

Various experimental SF / prefire / calibration systematics built in `systematics.py`.
Each typically has:

- **Step 1 — tensor**: helper called with `nominal_weight` (or a related column) as input, producing per-variation weights.
- **Step 2 — fill weight**: the tensor. Contains `nominal_weight = w · pdf_c · tc`.

Depends on `theoryCorr[0]`: yes (experimental variations of the analysis nominal).

---

## 3. Summary table — dependence on `theoryCorr[0]`

| Histogram | Fill weight contains `tc`? |
|---|---|
| `nominal`, `nominal_{observable}` | yes (analysis nominal, by design) |
| `{gen}_Corr` base (non-helicity) | no |
| `{gen}_pdfvars_Corr` (non-helicity) | no (`pdf_c` cancels in step 1a) |
| `{gen}_pdfas_Corr` (non-helicity) | no (same cancellation) |
| `{gen}_pdfvars_CorrByHelicity` | **no** (fixed — step 1b prefactor excludes `tc`) |
| `{gen}_pdfas_CorrByHelicity` | no (was already correct) |
| `{gen}_EWCorr` | yes (template on top of nominal) |
| `{gen}_QMCCorr` | yes (template on top of nominal) |
| `pdfXXX` (primary, non-helicity) | yes |
| `pdfXXXByHelicity` (primary, helicity) | yes |
| `pdfXXXalphaS002` | yes |
| `qcdScale` (non-helicity) | yes |
| `qcdScaleByHelicity` | yes |
| `breitwigner_*` | yes |
| `massWeight*`, `widthWeight*`, `sin2thetaWeight*` | yes |
| Muon/experimental systematics | yes |

Rule of thumb: the only systematic histograms that omit `tc` are those tied to a
specific theory correction's own PDF/alphaS variation (i.e., the `{gen}_Corr` and
`{gen}_CorrByHelicity` family for pdfvars/pdfas corrections). Those should be
independent of which correction is placed first in `--theoryCorr`. Everything else is
an absolute template aligned to the analysis nominal.

---

## 4. Diff summary

### `wremnants/production/theory_corrections.py`
- **New column** `nominal_weight_pdf_theory_uncorr` = `w` (excludes both `central_pdf_weight` and `theory_corr_weight`), defined upfront in `define_theory_corr`.
- **Cosmetic cleanup** (mathematically identical):
  - `define_theory_corr_weight_column`: `nominal_weight_uncorr / central_pdf_weight` → `nominal_weight_pdf_theory_uncorr`.
  - `define_pdf_columns`: `nominal_weight / central_pdf_weight` → `nominal_weight_pdf_uncorr` (2 occurrences).

### `wremnants/production/systematics.py`
- `add_pdfUncertByHelicity_hist`: new `from_theory_corr=False` kwarg.
  - `from_theory_corr=True`: prefactor excludes `tc` (`nominal_weight_uncorr` / `nominal_weight_pdf_theory_uncorr`).
  - `from_theory_corr=False`: prefactor keeps `tc` (`nominal_weight` / `nominal_weight_pdf_uncorr`, OLD behavior).
- `add_theory_hists` (call site for the `pdf_from_corr` helpers): passes `from_theory_corr=True`.

No other files changed.

---

## 5. Validation (3-way: combined vs ct18z-only vs nnpdf31-only)

- **Theory-correction PDF variation histograms** (`{gen}_pdfvars_Corr`, `{gen}_pdfvars_CorrByHelicity`, `{gen}_pdfas_Corr`, `{gen}_pdfas_CorrByHelicity`): 136 match at 1e-10, **0 differ** ✓
- **Primary-PDF uncertainty histograms** (`pdfXXX`, `pdfXXXByHelicity`, `pdfXXXalphaS002`): 102 match (CT18Z side, same `theoryCorr[0]`), 51 differ (NNPDF31 side, different `theoryCorr[0]`) — **expected** since these include `tc` by design.
- **All other systematics** (BW, mass/width/sin2theta, qcdScale, EW, QMC, experimental): differ by the `tc` ratio across runs with different `theoryCorr[0]` — expected.

Verdict: fix is working as intended.
