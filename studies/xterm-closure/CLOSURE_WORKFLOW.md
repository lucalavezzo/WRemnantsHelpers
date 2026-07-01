# Gen-level NP cross-term closure — workflow

Reusable recipe for measuring **how much the linear/multiplicative treatment of an
NP cross term biases the measured α_s**, via a gen-level σUL closure fit.

Companion docs: `CLOSURE_LOGBOOK.md` (decisions/results, newest-first) and `LOGBOOK.md`
(the cross-term *shape* study). This file is the **how-to**; the logbook is the **why**.

The worked example throughout is the **λ×λ** closure (done 2026-06-18): the param model
handles λ×λ exactly, so it is the positive control. The same pipeline extends to the
cross-GROUP terms αs×λ / PDF×λ / TNP×λ (see §8).

---

## 1. What it measures

Inject a **non-factorized truth** (the cross term baked in) as gen-level σUL pseudodata,
then fit it two ways and compare the α_s pull:

- **Fit A** — the *approximate* treatment (linear/multiplicative templates).
- **Fit B** — the *exact* treatment (the NP param model, which captures λ×λ exactly).

```
bias(α_s)  =  α_s(Fit A)  −  α_s(Fit B)
```

Fit B is the positive control: if the exact model recovers the injected truth
(α_s ≈ 0), the pipeline is sound and the Fit-A shift is the real bias of the
approximation. Because the same blinding offset cancels in the difference, even
blinded fits give a meaningful **difference** (but always `--unblind` to read absolutes).

**λ×λ result (reference):** Fit A α_s = **+0.583 ± 0.764**, Fit B α_s = **+0.002 ± 0.046**
(NOI units) → bias ≈ **+0.58**, i.e. ~0.76σ of the reduced fit (≈ σ(α_s)-scale vs the
full-analysis 0.547). Mechanism: the linear λ4 template is shape-degenerate with α_s, so
α_s eats the λ4 direction; the exact nonlinear λ4 shape breaks that degeneracy.

---

## 2. Pipeline

```
point-mode SCETlib run            (central + single-λ up/down templates + JOINT-λ truth, one run)
  → point_to_binned.py            (point spectrum → binned hist.Hist, WEIGHT storage)        [§4]
  → make_theory_corr.py           (matched σ_gen = resum ⊕ (DYTurbo − FO_sing), Y→|Y|)        [§5]
       → scetlib_dyturbo_<postfix>_CorrZ.pkl.lz4   in wremnants-data/data/TheoryCorrections/
  → feedRabbitSigmaUL.py          (rabbit tensor; pseudodata = JOINT-λ var; α_s = NOI)        [§6]
       • Fit-A tensor:  WITH    λ templates   (add_resummation_and_np_variations ON)
       • Fit-B tensor:  WITHOUT λ templates   (param model supplies λ; templates OFF)
  → rabbit_fit.py --unblind       • Fit A: normal fit                                          [§7]
                                  • Fit B: --paramModel …SCETlibNPParamModel gen_level=1
  → rabbit_print_pulls_and_constraints.py   → read the pdfAlphaS pull                          [§7]
```

Everything is gen-level (unfolded σUL on (qT, |Y|) bins) and fast (point mode).

---

## 3. Inputs (paths used for λ×λ)

| What | Path |
|---|---|
| Study dir (`$XD`) | `/work/submit/lavezzo/alphaS/scetlib-cms-newnp-lambda4fix/prod/scetlib_run/xterm_validation` |
| WRemnants (`$WREM_BASE`) | `/home/submit/lavezzo/alphaS/main/WRemnants` |
| btgrid grid | `…/Z_COM13_CT18Z_N3p0LL_btgrid_fineall` (point run is done ON this grid: edges+centers) |
| SCETlib runcard | `$XD/runcard_parity.ini` (tanh_2, `bins=false`, on the btgrid grid) |
| SCETlib variations | `$XD/variations_parity.conf` (central + 8 single-λ + joint truth) |
| MiNNLO gen (`-m`) | `/home/submit/david_w/ceph/WMassAnalysis/results_histmaker/260521_z_gen/w_z_gen_dists.hdf5` |
| FO-singular (`-c`) | `/home/submit/david_w/work/TheoryCorrections/SCETlib/com13_ct18z_n3+0ll_fine_nnlo_sing/inclusive_Z_COM13_CT18Z_N3+0LL_fine_nnlo_sing_combined.pkl` |
| DYTurbo (`-c`) | `/home/submit/david_w/work/TheoryCorrections/DYTURBO/nnlo-scetlibmatch-13TeV-CT18Z-finer-bin/scalevariations/z0/results_z-2d-nnlo-vj-CT18ZNNLO-{scale}-scetlibmatch.txt` |
| Borrowed α_s correction | `scetlib_dyturbo_LatticeNP_CT18Z_N3p0LL_N2LO_pdfas` (a standard `_pdfas`, same gen binning) |
| btgrid combined pkl | `/scratch/submit/cms/wmass/scetlib_np/Z_COM13_CT18Z_N3p0LL_btgrid_fineall/combined_btgrid.pkl` (param model default) |

**λ config (tanh_2):** central λ2=0.4, λ4=0.4, λ2_nu=0.15, δλ2=0, λ_inf=1.0, λ_inf_nu=2.0.
**Joint truth (injected):** λ2=1.0, λ4=1.0, λ2_nu=0.25, δλ2=0.02 (others at central).
Joint var name: `lambda2_nu0.25-lambda21.0-lambda41.0-delta_lambda2Ext`.

---

## 4. Step 1 — SCETlib point run → converter

Run SCETlib in **point mode** on the btgrid grid (one run, all variations):
```bash
# inside the apptainer, from the scetlib run area
scetlib-run-qT.py <n> 1 xterm_validation/runcard_parity.ini --point-spectrum --live
# → $XD/runcard_parity_pointspec.pkl   (~427 MB)
```
The run must be on the btgrid grid (= union of experimental bin EDGES and CENTERS) so each
experimental bin holds (edge, center, edge) → a 3-point Simpson rebin (<0.05%).

Convert the point spectrum to a binned hist:
```bash
cd $WREM_BASE
python3 -m wremnants.postprocessing.scetlib_np.point_to_binned \
  $XD/runcard_parity_pointspec.pkl \
  -o $XD/parity_resum_binned.pkl
```
Self-check should print `read_scetlib_hist -> axes=['Q','Y','qT','vars'], shape=(1,82,70,10)`.
**Storage MUST be `Weight`** (the converter sets variance=0) — see Gotcha G1.

---

## 5. Step 2 — make_theory_corr (matched σ_gen → TheoryCorrection)

Swap the production resum input for our `parity_resum_binned.pkl`; FO-sing + DYTurbo + MiNNLO
are λ-independent and reused.
```bash
cd $WREM_BASE
python3 scripts/corrections/make_theory_corr.py \
  -g scetlib_dyturbo --proc z --axes Q Y qT --minnloh nominal_gen --qtCutoff 1.0 \
  -m /home/submit/david_w/ceph/WMassAnalysis/results_histmaker/260521_z_gen/w_z_gen_dists.hdf5 \
  -c $XD/parity_resum_binned.pkl \
     /home/submit/david_w/work/TheoryCorrections/SCETlib/com13_ct18z_n3+0ll_fine_nnlo_sing/inclusive_Z_COM13_CT18Z_N3+0LL_fine_nnlo_sing_combined.pkl \
     '/home/submit/david_w/work/TheoryCorrections/DYTURBO/nnlo-scetlibmatch-13TeV-CT18Z-finer-bin/scalevariations/z0/results_z-2d-nnlo-vj-CT18ZNNLO-{scale}-scetlibmatch.txt' \
  -p parity_LxL_truth
```
`-c` = resum pkl, FO-singular pkl, DYTurbo txt. Writes
`scetlib_dyturbo_parity_LxL_truth_CorrZ.pkl.lz4` to `--outpath` (**default** =
`wremnants-data/data/TheoryCorrections/`, where feedRabbit reads — no copy needed unless you
redirect `--outpath`). Q is auto-rebinned to [60,120] by `rebinHistsToCommon` (the 1-bin
correction forces it); Y is folded to |Y|.

---

## 6. Step 3 — feedRabbitSigmaUL (build the tensors)

Two tensors from the **same** correction, differing only in whether the λ templates are added.
The λ-template / PDF-block toggles live in `feedRabbitSigmaUL.py` `main()` (currently manual
comment toggles — see §9). The α_s correction is **borrowed** via `--alphasGenerator`.

**Fit A — WITH λ templates** (`writer.add_resummation_and_np_variations()` enabled):
```bash
cd $WREM_BASE
python3 scripts/rabbit/feedRabbitSigmaUL.py \
  --predGenerator       scetlib_dyturbo_parity_LxL_truth \
  --pseudodataGenerator scetlib_dyturbo_parity_LxL_truth \
  --pseudodataVariation 'lambda2_nu0.25-lambda21.0-lambda41.0-delta_lambda2Ext' \
  --alphasGenerator     scetlib_dyturbo_LatticeNP_CT18Z_N3p0LL_N2LO_pdfas \
  --pdfs ct18z --nois alphaS \
  --outname parity_LxL --outfolder $XD
# → $XD/parity_LxL_scetlib_dyturbo_parity_LxL_truth_alphaS.hdf5
```

**Fit B — WITHOUT λ templates** (comment out `add_resummation_and_np_variations` + the
PDF/bc/mb/EW calls; param model supplies λ and REFUSES if scetlibNP* systs present — Gotcha G4).
Same command, `--outname parity_LxL_paramB`:
```bash
python3 scripts/rabbit/feedRabbitSigmaUL.py \
  --predGenerator scetlib_dyturbo_parity_LxL_truth \
  --pseudodataGenerator scetlib_dyturbo_parity_LxL_truth \
  --pseudodataVariation 'lambda2_nu0.25-lambda21.0-lambda41.0-delta_lambda2Ext' \
  --alphasGenerator scetlib_dyturbo_LatticeNP_CT18Z_N3p0LL_N2LO_pdfas \
  --pdfs ct18z --nois alphaS \
  --outname parity_LxL_paramB --outfolder $XD
# → $XD/parity_LxL_paramB_scetlib_dyturbo_parity_LxL_truth_alphaS.hdf5
```

---

## 7. Step 4 — fit & read the α_s pull

**Always pass `--unblind`** (Gotcha G2). `-t 0` fits the injected pseudodata.

**Fit A (linear templates, normal fit):**
```bash
rabbit_fit.py $XD/parity_LxL_scetlib_dyturbo_parity_LxL_truth_alphaS.hdf5 \
  -o $XD/fit_parity_LxL -t 0 --unblind
rabbit_print_pulls_and_constraints.py $XD/fit_parity_LxL/fitresults.hdf5
```

**Fit B (param model, gen-level):**
```bash
rabbit_fit.py $XD/parity_LxL_paramB_scetlib_dyturbo_parity_LxL_truth_alphaS.hdf5 \
  -o $XD/fit_parity_LxL_paramB -t 0 --unblind \
  --paramModel wremnants.postprocessing.scetlib_np.SCETlibNPParamModel \
      gen_level=1 \
      lambda_central=$XD/lambda_central_parity.json \
      nonsingular_fo_sing=/home/submit/david_w/work/TheoryCorrections/SCETlib/com13_ct18z_n3+0ll_fine_nnlo_sing/inclusive_Z_COM13_CT18Z_N3+0LL_fine_nnlo_sing_combined.pkl \
      'nonsingular_dyturbo=/home/submit/david_w/work/TheoryCorrections/DYTURBO/nnlo-scetlibmatch-13TeV-CT18Z-finer-bin/scalevariations/z0/results_z-2d-nnlo-vj-CT18ZNNLO-{scale}-scetlibmatch.txt' \
  --freezeParameters lambda_inf lambda6 lambda4_nu lambda_inf_nu
rabbit_print_pulls_and_constraints.py $XD/fit_parity_LxL_paramB/fitresults.hdf5
```

The **`pdfAlphaS`** line is the α_s pull (NOI units). bias = α_s(Fit A) − α_s(Fit B). For a
strictly apples-to-apples λ constraint, add `priors=1 prior_sigmas=delta_lambda2=0.02` to Fit B
so its λ priors match Fit A's template widths (λ2/λ4/λ2_nu defaults 0.5/0.5/0.10 already match).

`lambda_central_parity.json` (extracted from the correction's `file_meta_data` — Gotcha G3):
```json
{"eff_params": {"np_model":"tanh_2","lambda_inf":1.0,"lambda2":0.4,"lambda4":0.4,"lambda6":0.0,"delta_lambda2":0.0},
 "gnu_params": {"np_model_nu":"tanh_2","lambda2_nu":0.15,"lambda4_nu":0.0,"lambda_inf_nu":2.0}}
```

---

## 8. Plan — the cross-GROUP terms (αs×λ, PDF×λ, TNP×λ)

These are the ~10%-of-σ(α_s) terms the screen flagged. **Key difference from λ×λ:** the param
model fixes λ×λ *exactly*, but αs/PDF/TNP are still layered **multiplicatively** on the λ shape
even with the param model. So these closures test a **residual** bias in the *current* method —
there is no "exact Fit B" that removes it. The design changes accordingly (§8.1).

### 8.1 Closure design (how it differs from λ×λ)

The core test is the same as λ×λ: **inject the genuine joint truth `σ(g↑, λJ)`, fit with the
factorizing treatment, and read α_s.** If factorization held, the individual templates *could*
reproduce the joint → perfect fit → α_s = 0. So **any α_s pull = the non-factorization leaking
into α_s — that is the bias, directly.** (No separate "factorized-null" injection is needed:
with templates built from the same point run as the truth it would fit exactly → 0 by
construction. The only residual artifact is the param-model-λ vs point-run shape mismatch, already
bounded by the λ×λ Fit B at α_s = +0.002 — negligible.)

Two points specific to the cross-GROUP case:

1. **Fit with the param model for λ, NOT linear λ templates.** It removes λ×λ *exactly*, so
   fitting `σ(g↑, λJ)` isolates the pure **g×λ** term. With linear λ templates the pull would mix
   λ×λ + g×λ and you couldn't attribute it.
2. **The pull's magnitude is configuration-dependent.** The λ have **NO physics priors** in the real
   analysis (no lattice/theory constraints) — they float free, pinned only by the **real unfolded-σUL
   data covariance**. Do NOT add λ priors to mimic the analysis (there are none). Instead, what makes
   the closure realistic is using that **data covariance** (inject the theory truth as the central, use
   the measurement covariance) — not the tiny theory-MC-stat covariance the pseudodata path defaults to.
   With the tiny covariance the free λ + degenerate nuisances (e.g. γ_ν↔lambda2_nu) leave α_s loose and
   the cross term gets absorbed by λ rather than projected onto α_s, so the α_s pull is only suggestive.
   The robust bias needs the real data covariance (a hybrid: real cov + injected-truth central).

Recipe per class: inject `σ(g↑, λJ)` → fit `[param-model λ ⊕ multiplicative g template]`, α_s = NOI
→ α_s pull = the isolated g×λ bias. For **αs×λ**, `g = α_s` is the NOI itself, so the bias is
`α_s(fit) − αs↑`; for **TNP×λ / PDF×λ**, `g` is a constrained nuisance and the cross term leaks
into the floating α_s.

All runs use the **btgrid fine grid** (the `[Grid_Q/Y/qT]` from `runcard_parity.ini`), NOT the
coarse grid the shape-screen `runcard_xterm*` used — the converter + param model need it.

### 8.2 SCETlib runs

**How to read the "variation blocks" column.** One SCETlib run outputs the spectrum at its
runcard's central settings, plus one extra spectrum for each numbered block `[0], [1], …` in the
`variations.conf` it points to. Each block just lists the parameter(s) to override relative to
central; the run emits one spectrum per block, cheaply (they share the perturbative solve). The
column below is therefore "which blocks this run's `variations.conf` must contain." Example
`variations.conf`:

```
[0]
# central — no overrides
[1]
lambda2 = 1.0                 # one spectrum with λ2 → 1.0, all else central
[2]
gamma_nu = (1., 'level0')     # one spectrum with the γ_ν TNP shift
[3]
lambda2 = 1.0
gamma_nu = (1., 'level0')     # one spectrum with BOTH → the joint λ2×γ_ν point
```

Block shorthand used in the table:
- **central-λ** = a block at tanh_2 central (`lambda2=0.4, lambda4=0.4, lambda2_nu=0.15, delta_lambda2=0`; `lambda_inf=1, lambda_inf_nu=2, lambda4_nu=0, lambda6=0`) — i.e. the `[0]` baseline.
- **joint-λ** = one block with all four joint-λ values set (`lambda2=1.0, lambda4=1.0, lambda2_nu=0.25, delta_lambda2=0.02`) — same joint as the λ×λ study.
- **one TNP** = a block applying one of the 10 TNP shifts (λ central): `gamma_nu, gamma_cusp, gamma_mu_q, s, h_qqV` = `(1.,'level0')`; `b_qqV, b_qqbarV, b_qqS, b_qqDS, b_qg` = `(0.5,'relative')`.
- **one TNP + joint-λ** = a block with that TNP shift AND the joint-λ values together (the genuine joint truth for that TNP).

Note: **αs and PDF live in the runcard `[QCD]` block, not in `variations.conf`** (they rebuild the
calc, so they need a separate run) — that's why their runs carry only the 2 λ blocks. **TNP and λ
are both `variations.conf` rows**, so the entire TNP×λ class fits in one run's blocks.

| Class | Run | `[QCD] alphas_mu0` | `[QCD] pdf_set` (member) | `variations.conf` blocks (1 spectrum each) | Produces / role |
|---|---|---|---|---|---|
| *(shared)* | `xc_nominal` * | 0.118 | CT18ZNNLO (0) | central-λ, joint-λ | σ_c (central) + σ(αs_c,λJ) — *reuse the parity run's `[0]` + joint var; no re-run* |
| **TNP×λ** | `xc_tnp` | 0.118 | CT18ZNNLO (0) | central-λ; joint-λ; +10 "one TNP"; +10 "one TNP + joint-λ"  → **22 blocks** | **one run = whole class**: the 10 TNP templates σ(TNP_k↑,λc) and the 10 truths σ(TNP_k↑,λJ) |
| **αs×λ** | `xc_asUp` | **0.120** | **CT18ZNNLO_as_0120** (0) | central-λ; joint-λ | αs template σ(αs↑,λc) + truth σ(αs↑,λJ) |
| **αs×λ** | `xc_asDn` (opt) | **0.116** | **CT18ZNNLO_as_0116** (0) | central-λ; joint-λ | down side for symmetrization |
| **PDF×λ** | `xc_pdf{i}` (×N) | 0.118 | CT18ZNNLO (**member i**) | central-λ; joint-λ | per-eigenvector σ(pdf_i,λc) + σ(pdf_i,λJ) |

\* `xc_nominal` is just the existing parity central — no new run. αs/PDF runs = clone
`runcard_xterm_asUp.ini`'s `[QCD]` block onto the btgrid grid with `[Nonperturbative]` = central-λ.

### 8.3 Per-class fit setup & effort

Each class: build the truth correction (§4–5) from the relevant `σ(g↑, λJ)` var, build the
`g`-template correction from `σ(g↑, λc)` (this is the "reproduce pdfas/pdfvars/TNP **at our λ**"
step — do NOT borrow), then fit (param-model λ via `gen_level=1`, §7) and read the α_s pull
against the factorized-null.

- **TNP×λ — easiest, do FIRST.** 1 SCETlib run. TNP enter the fit as constrained nuisances (the
  `add_resummation_and_np_variations` TNP block — already supported by the writer). Per-TNP
  attribution from the 10 `[TNP_k + λJ]` truths, or an all-TNP-up×λJ var for the net.
- **αs×λ — medium.** 2–3 runs. Must build the α_s template at our λ_c (replaces the *borrowed*
  `--alphasGenerator`); α_s is the NOI, so the bias = `α_s(fit) − αs↑`.
- **PDF×λ — heaviest.** N runs (CT18Z = 58 error members / 29 eigenvector pairs). Start with the
  1–2 eigenvectors the shape screen flags as most α_s-correlated; full set only if warranted.

Prereq for all: the §9 hacks→flags refactor (so the Fit-A/Fit-B and template/no-template tensor
builds, and the `--alphasGenerator`/template sourcing, are options not comment-toggles).

---

## 9. Current code state — TEMPORARY hacks to refactor

These were quick unconditional edits (marked "revert later"); for repeatable cross-term runs
turn them into proper options:

- `feedRabbitSigmaUL.py` `main()` — manual comment-toggle of `add_resummation_and_np_variations`
  (λ templates) and the PDF/bc/mb/EW blocks. → a `--noLambdaTemplates` / parity-mode flag.
- `theory_fit_writer.py` `add_resummation_and_np_variations` — hard-coded to emit the 4 parity
  single-λ nuisances then `return` (standard NP/gamma/TNP/transition unreachable). → gate on a flag.
- `theory_fit_writer.py` `add_sigmaul_process` — baseline var hard-coded `nominal_entry="central"`.
- `feedRabbitSigmaUL.py` — `_validate_args` call commented (parity name lacks the PDF string).
- `--pseudodataVariation`, `--alphasGenerator` are clean value-args (keep).

`point_to_binned.py` (Weight storage) and `param_model.py` (`gen_level`) are **permanent,
general** improvements — keep.

---

## 10. Gotchas (each cost a debug cycle)

- **G1 — converter must use `Weight` storage.** `Double` storage → `hist.variances()` returns
  `None` in the apptainer's boost_histogram → tensorwriter coerces it to a single NaN →
  `"1 NaN or Inf values encountered in variances for Zmumu!"`. The converter emits `Weight`
  with variance=0 (SCETlib is analytic); make_theory_corr then propagates DYTurbo/MiNNLO
  MC-stat into a `Weight` `_hist`, like the standard path.
- **G2 — blinding.** Without `--unblind`, rabbit applies a (large) offset to `pdfAlphaS`; the
  printed pull is NOT the true shift, and its uncertainty can even read `NaN`. The offset is a
  common additive constant, so it cancels in Fit A − Fit B, but always `--unblind` to read
  absolutes.
- **G3 — λ_central must be passed for the param model.** The pseudodata-path tensor carries no
  `meta_info_input` (`load_sigmaul_data` returns None), so the param model can't auto-detect
  λ_central → pass `lambda_central=<json>`. Extract values from the correction pkl:
  `file_meta_data[<basename>].config.Nonperturbative`.
- **G4 — double-counting guard.** `SCETlibNPParamModel` refuses to run if discrete `scetlibNP*`
  λ templates are in the tensor → the Fit-B tensor must omit them.
- **G5 — `--freezeParameters` is space-separated regexes** (`nargs="+"`, `re.match` start-anchored,
  matched against `param_model.params + indata.systs`). Comma-joining silently freezes nothing.
  Note `lambda6`/`lambda4_nu` are inert in tanh_2 (zero sensitivity → read `0±0` whether or not
  frozen — not evidence the freeze worked).
- **G6 — σ_ns / btgrid consistency.** The param model rebuilds σ_gen from the btgrid + its own
  σ_ns; pass the SAME FO-sing/DYTurbo as make_theory_corr used. Closure is ~0.14% (btgrid vs
  point run), not bit-exact — small λ deviations from truth are expected; α_s recovery is robust.
- **G7 — `gen_level=1` is required** for the param model in the σUL fit (skips the reco R fold;
  reads the gen (qT,|Y|) binning from the fit channel).
- **G8 — combined-override blocks lose part of their auto-name.** When a `variations.conf` block sets
  BOTH a TNP and λ (or any two groups), SCETlib's auto-namer keeps only the λ part → the TNP×λ truth
  blocks all collide on the same name as the λ-only block, which breaks the converter's named `vars`
  axis and feedRabbit's by-name selection. The *spectra are correct* (verify with the additive check
  σ(g↑,λJ) ≈ σ(λJ) + [σ(g↑)−σ_c]); only the names are wrong. Fix: rewrite `d["vars"][k]["name"]` by
  the known block order into a `_named.pkl` before the converter (one-off script; the block→param order
  is fixed by your `variations.conf` and confirmed by the additive check). Affects TNP×λ; αs×λ / PDF×λ
  are unaffected (their group lives in the runcard, so their blocks are λ-only).
```
