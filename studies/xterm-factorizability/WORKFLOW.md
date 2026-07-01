# SCETlib theory predictions → rabbit fit: workflow & cross-term-impact plan

Generic reference for how a SCETlib prediction reaches the α_s/W-mass fit, why
bin-mode is the bottleneck, and the plan to turn the factorizability study into a
fit-level α_s-bias number. File refs are in `~/alphaS/main/WRemnants`.

---

## Part A — how a SCETlib prediction reaches the fit (two parallel paths)

### A1. Binned theory CORRECTIONS  (the PDF / α_s / TNP / scale path — BIN mode, slow)

1. **Generate** — `scripts/corrections/make_theory_corr.py`.
   - Inputs: MiNNLO gen file (denominator) + SCETlib **resummed** (binned) + SCETlib
     **FO-singular** (binned) + **DYTurbo** FO nonsingular. SCETlib read via
     `io_tools/input_tools.read_matched_scetlib_dyturbo_hist` — **BINNED**, axes
     (Q, Y, qT, vars).
   - Output: `{gen}_Corr{Z|W}.pkl.lz4`, keys `{gen}_minnlo_ratio` (the correction),
     `{gen}_hist`, `minnlo_ref_hist`. Axes `(Q, absY, qT, charge, vars)`. The **`vars`**
     axis holds the variations: `[central, pdf1..58, alphaS±, TNP±, …]`.
2. **Apply** — `wremnants/production/theory_corrections.py::load_corr_helpers`
   (L191-250) → `correctionsTensor_helper.makeCorrectionsTensor` → histmaker
   (`scripts/histmakers/…`, `define_theory_corr`) reweights MiNNLO **per event, per
   `vars`**. Output: reco templates with a `vars` axis; `vars[0]` = nominal,
   `vars[i>0]` = systematic template *i*.
   → This is **bin mode** and is the slow step.

### A2. The NP PARAM MODEL  (the λ path — ON-THE-FLY, fast at fit time)

- `wremnants/postprocessing/scetlib_np/param_model.py::SCETlibNPParamModel`.
- Inputs: a **btgrid** (NP-OFF perturbative bT-integrand, binned in (Q,Y,qT,bT),
  `combined_btgrid.pkl`), an **unfolding HDF5** (gen→reco response **R** =
  `nominal_prefsr_yieldsUnfolding`, + gen-total `N_gen`), and `λ_central` (from fit
  metadata).
- `compute(λ)` at fit time: bT-Hankel integral with the NP form factor at the current
  λ → σ_resum(λ) → +nonsingular → σ_gen(λ) → **fold through R** → σ_reco(λ) → ratio to
  λ_central → `rnorm(reco bin)`. Rabbit multiplies the signal template by `rnorm`
  bin-by-bin. **λ is exact + differentiable; no binned λ template.** (Validated vs the
  histmaker to 0.14% — see `scetlib_np_param_model_histmaker_validation.py`.)
- The btgrid is built **once, at central PDF/α_s** (it's NP-independent). So the
  on-the-fly λ prediction is evaluated at *central* PDF/α_s — this is precisely why
  λ×PDF / λ×α_s don't factorize in the fit (the λ response can't track a PDF/α_s pull).

### A3. The fit & pseudodata  (rabbit)

- `setupRabbit.py` assembles the rabbit tensor: nominal + the `vars` templates (A1) +
  the param model (A2) for λ. Systematics combine **multiplicatively**
  (`--systematicType log_normal`, default): `expected = rnorm(λ)·exp(Σ_j θ_j logk_j)·norm`
  (`rabbit/rabbit/fitter.py:1606-1718`).
- **Pseudodata / injection:**
  - `--pseudoData <hist> --pseudoDataAxes vars --pseudoDataIdxs k` → use the `vars[k]`
    slice as Asimov.
  - `--pseudoDataFile <f>` → read an **alternative histmaker file** as the Asimov.
  - `-t 0` = Asimov; `-t N` = toys.
  (`datagroups.addPseudodataHistograms`.)
- **Closure (exists, for λ):** `scripts/rabbit/scetlib_np_closure_suite.py` — truth λ
  baked into the datacard, fit start shifted via `xparam_default=…`, Asimov
  (`-t 0 --pseudoData nominal`), fit with the param model, check postfit recovers truth.

---

## Part B — bin vs point mode: the bottleneck and the bridge

- **BIN mode** (`make_theory_corr.py`, `read_matched_scetlib_dyturbo_hist`) is slow.
  **POINT mode** (`scetlib-run-qT.py --point-spectrum`) is fast. There are now **two
  bridges** from a fast point run to the fit:
- **Bridge 1 — point→binned converter (`point_to_binned.py`, see B1):** turns a point
  pickle into the binned `{hist}` pickle `make_theory_corr` reads, so a point run can feed
  **bin-mode** `make_theory_corr` directly. (Obsoletes the earlier note that no such
  converter existed.)
- **Bridge 2 — fold through R:** the param model's gen→reco response **R** (the unfolding
  HDF5) turns a **gen-level point-mode prediction into a reco-level one WITHOUT bin-mode**
  `make_theory_corr` — it's exactly param-model "Step 3" (fold σ_gen through R).
- ⇒ For anything that only needs a **reco-level reweighting** (our cross-term closure
  does), use Bridge 2: stay in fast point mode and fold through R; skip `make_theory_corr`.
  When you specifically want a binned **`{gen}_Corr{Z\|W}.pkl.lz4`** correction (Part A1),
  use Bridge 1.

### B1. The point→binned converter (`point_to_binned.py`)

`wremnants/postprocessing/scetlib_np/point_to_binned.py` — converts a **point-spectrum
SCETlib pickle** (`{spectra: {var: {(Q,Y,qT,lep): σ}}, vars, config, meta_data}`) into a
**binned `{hist}` pickle** that `make_theory_corr` reads via `read_scetlib_hist` /
`read_matched_scetlib_dyturbo_hist`. Lightweight glue — it does **no integration of its
own**, reusing the param model's validated `btgrid_integrate` Simpson machinery so the
rebin is grid/method-consistent with the param model.

- **What it integrates:**
  - **Q** → arctan-Q² Simpson over the mass window (`q_integrate_weights`) → **one** Q bin
    `[--qlo, --qhi]` (default `[60, 120]`).
  - **Y, qT** → 3-point Simpson per experimental bin (`rebin_weights`).
- **Bin↔edge step (`edges_from_grid`):** the point run must be on the **btgrid grid =
  union of the experimental bin EDGES and CENTERS** (so each bin holds exactly
  (edge, center, edge) = 3 samples → a 3-pt Simpson, the <0.05% rebin the btgrid runcard
  is built for). The converter **recovers the experimental bin edges as every-other grid
  point** (`grid[0::2]`), guarded by a midpoint check that `[0::2]` really are edges, not
  centers (errors out otherwise). Grid must have an ODD point count (edges+centers).
- **Output:** `{hist, var_names, config, meta_data}`, where `hist` is a `hist.Hist` with
  axes **(Q, Y, qT, vars)** matched to a production SCETlib hist:
  - `vars` is a **named `StrCategory`** (not Integer) — `read_matched_scetlib_hist` string-
    maps each non-scale λ var to the central nonsingular (Integer vars → `TypeError`), and
    `feedRabbitSigmaUL` picks truth/templates by name.
  - Q/Y/qT are `Variable` axes with **flow=True** (the production default) — `flow=False`
    leaves real bins aligned but drops flow bins, so `read_matched_scetlib_hist`'s
    `addHists` can't broadcast vs the (flow=True) nonsingular: shape `(1,82,70)` vs
    `(3,84,72)`.
  - **`Weight` storage with variance ≡ 0** (not `Double`). `make_theory_corr` propagates
    the storage type: a `Double` scetlib → a `Double` matched `_hist`, whose
    `.variances()` is `None` in newer boost_histogram → the rabbit tensor writer coerces it
    to a single NaN and rejects it. SCETlib is analytic (no MC stats) so variance=0 is
    correct; the matched hist's MC-stat variance then comes purely from DYTurbo/MiNNLO.
  - `config` + `meta_data` are carried from the point pkl (`get_scetlib_config` hard-
    requires the `config` key).
- **Two benign `calculation_piece = sing` integrity items, handled in-converter:**
  - **qT = 0 is NaN** (differential spectrum ill-defined; physical limit 0) → zeroed so the
    first qT bin's Simpson is well-defined.
  - **Negative sing-only σ** (nonsingular-dominated region) are **physical** and pass
    through unchanged; `make_theory_corr`'s `DYTurbo − FO_sing` matching corrects them
    (Simpson is linear, so rebinning negatives is fine).
- **Y stays SIGNED** (the production resummed pkl is signed Y); `make_theory_corr` does the
  `|Y|` fold, exactly as for the real input.
- **Usage** (inside the WRemnants apptainer with `setup.sh` sourced, from `WREM_BASE` — the
  package `__init__` pulls in TensorFlow, so it must run in the WRemnants env, not the
  SCETlib singularity):

      python3 wremnants/postprocessing/scetlib_np/point_to_binned.py \
          <point_spectrum.pkl> -o <out_binned.pkl> [--qlo 60 --qhi 120]

  Prints a per-var window-integrated σ table and, unless `--no-selfcheck`, re-parses the
  output through `read_scetlib_hist` (expect axes `['Q','Y','qT','vars']`).

---

## Part C — factorizability cross-terms → fit-level α_s bias (the plan)

**Study status (see `LOGBOOK.md`):** every cross-term among {λ, TNP, α_s, PDF} measured
in point mode via `--point-spectrum` + the `Nmult` metric. All ≤0.84% worst-case shape;
σ-weighted αs-projected screen (`impact_xterm.py`) → ~10–11% of σ(α_s) upper bound for
PDF×λ, α_s×λ (λ×λ control 30%, param-model-handled). The screen is a single-parameter
gen-level UPPER BOUND; we want the real profiled, reco-level number.

### C1. Attribution — Fisher-matrix projection (CHEAP, no new runs/fits)
`δα_s = (M⁻¹)_{α_s,b}⟨t_b, Δ⟩`, `M_ab=⟨t_a,t_b⟩` the full Fisher matrix over all fit
templates `t_b` (α_s/PDF/TNP/λ — the analysis already has these), `Δ` = the cross-term
fields. Linear ⇒ **decomposes per group for free** (which family is the problem) and
folds in the joint profiling the screen ignored. Needs: the analysis templates + one
nominal-fit covariance. This upgrades `impact_xterm.py`.

### C2. Definitive — point-mode closure injection (NO bin mode)
1. Run the **joint** variations (the cross-terms) in **point mode on the fit's GEN
   binning** (fast — this is why point mode matters). Joint = ≥2 nuisances set in one
   SCETlib run; we already do this (pairs card, asUp×λ, PDF-member×λ).
2. Build the gen-level **non-factorized reweighting** = factorized × (1 + Σ cross-terms).
3. **Fold through R** (unfolding HDF5) → reco-level non-factorized **pseudodata**.
4. **Inject** via `--pseudoDataFile`; fit with the standard factorizing model
   (param-model λ + binned PDF/α_s/TNP templates), float α_s + all nuisances.
5. **α_s pull = the bias.** Inject all cross-terms at once → net bias (one fit); inject
   one FAMILY at a time → per-group attribution (~6 fits, only the flagged ones).
   Profiling + reco smearing + the unconstrained δλ2 (floats) are all handled by the fit.

### Inputs still needed
- **σ(α_s)** — the measurement's expected total uncertainty (the denominator for "does
  it matter"; the screen used 0.001 as a placeholder).
- **δλ2 has no prior** → it floats freely; the closure handles this automatically (no
  excursion guess needed). The screen's δλ2 rows are at an arbitrary scale — ignore them.
- The fit's **gen binning** (to run point mode on) and the **unfolding R HDF5** (the fold).

### What we do NOT need
- Bin-mode `make_theory_corr` for the closure — we inject at reco via R.
- Per-PAIR fits — attribution is the linear decomposition (C1) or per-FAMILY injection (C2).

---

## File map (quick ref)

| step | file |
|---|---|
| make binned corr | `scripts/corrections/make_theory_corr.py` |
| point→binned converter | `wremnants/postprocessing/scetlib_np/point_to_binned.py` (Part B1) |
| read binned SCETlib | `wremnants/utilities/io_tools/input_tools.py::read_matched_scetlib_dyturbo_hist` |
| apply corr → templates | `wremnants/production/theory_corrections.py` + `correctionsTensor_helper.py` |
| NP param model (on-the-fly λ) | `wremnants/postprocessing/scetlib_np/param_model.py` |
| param-model validation | `wremnants/postprocessing/scetlib_np_param_model_histmaker_validation.py` |
| fit + pseudodata | `scripts/rabbit/setupRabbit.py` (`--pseudoData*`), `rabbit/rabbit/fitter.py` |
| λ closure suite | `scripts/rabbit/scetlib_np_closure_suite.py` |
| point-mode SCETlib | `prod/scetlib_run/scetlib-run-qT.py --point-spectrum` |
| cross-term study | `prod/scetlib_run/xterm_validation/` (LOGBOOK.md) |
