---
id: ct18z-3p0-newvals-tanh6-lambda6scan
title: CT18Z N3+0LL fine SCETlib production at newvals NP with tanh_6 + TMD lambda6 scan + lambda4 negative excursion
status: running
question: Produce a SCETlib `_combined.pkl` for CT18ZNNLO at N3+0LL with the newvals NP centrals (lambda2=0.4, lambda4=0.4, lambda_inf=1, lambda2_nu=0.15, lambda4_nu=0, lambda_inf_nu=2), `np_model = tanh_6` on both sides, and additional variations on TMD lambda_6 ∈ {0.05, 0.1, 0.2, 0.5}, TMD lambda_4 = -0.4, TMD lambda_inf = 2.0, so the franks-vals-fit study can validate its data-preferred linearized lambda_4 against explicit SCETlib templates and probe the lambda_6 (tanh_6 vs tanh_2) parametrization freedom.
owner: lavezzo
created: 2026-05-20
updated: 2026-05-25
preferred_run: null
tags: [scetlib, ct18z, n3+0ll, tanh_6, lambda6, lambda4-negative, theory-correction, franks-vals-followup]
parent: franks-vals-fit
investigates_regions: []
investigates_methods: []
investigates_fits: []
investigates_background_estimates: []
investigates_uncertainties: [uncertainty:scetlibNP]
next_action: Decide retry strategy for 61 hung jobs (all 56 var-5 + 5 tail + 2 var-4) — relaxed Cuba precision / split bins / drop var-5 / source-level debug. Resubmit file ready at condor_resubmit.submit. Then combine → _combined.pkl → downstream chain (scetlib_dyturbo).
current_hypotheses:
  - Promoting the hardcoded TMD lambda_6 constant (NP_models.hpp:88 = 0.016) to a runtime `lambda6` member with default 0.016 leaves existing tanh_6 configs bit-equivalent, while enabling the requested {0.05, 0.1, 0.2, 0.5} variation scan in a single condor submission.
  - The newvals NP centrals (already validated in MSHT20an3lo via com13_msht20an3lo_newnps_n3+0ll_lattice_newvals_coarse) port cleanly to CT18Z by swapping pdf_set=CT18ZNNLO + adopting the existing CT18Z 3+0 fine grids + flipping np_model/np_model_nu from tanh_2 to tanh_6.
  - Explicit SCETlib templates at lambda_4 = -0.4 (and the lambda_6 scan) will let the franks-vals-fit linearization (data preferring lambda_4 ≈ -0.78) be validated or refuted against a non-linear NP shape, addressing the open question franks-vals-fit closed with.
success_criteria:
  - scetlib rebuilds clean with the NP_models.hpp lambda6-runtime patch; default lambda6 = 0.016 reproduces existing tanh_6 output bit-equivalent.
  - `inclusive_Z_COM13_CT18Z_N3+0LL_newvals_lambda6_fine_combined.pkl` exists and loads, with histogram axes covering all requested variations.
  - lambda_6 scan templates ({0.05, 0.1, 0.2, 0.5}) show monotonically larger NP contribution; lambda_4 = -0.4 template runs without crashing.
  - Downstream consumer wired into a WRemnants histmaker config (chain decision recorded under ## Decisions).
blockers: []
pending_signoffs: []
---

## By-helicity TheoryCorrections (Step 2 of downstream chain)

After producing the 3 standard TheoryCorrection `.pkl.lz4` files, the by-helicity HDF5 versions are produced by running the **gen histmaker** (`w_z_gen_dists.py`) with `--theoryCorr <pred> --addHelicityAxis`. Two wrappers in `$WREM_BASE/scripts/corrections/corrs_by_helicity/`:
- `make_pdf_from_corr_gen_hists.py` — for pdfvars
- `make_alphaS_gen_hists.py` — for pdfas

### Registration

> **2026-05-26 correction**: I originally also added the BARE nominal (`scetlib_dyturbo_NewVarsCT18ZLambda6_N3p0LL_N2LO`) to `theory_corr_weight_map`. That was the bug that crashed v3 (see "tensor_weight registration bug" under `## Known hacks / caveats`). The bare nominal must NOT be in `theory_corr_weight_map`; the existing baseline `LatticeNP_CT18Z` only registers `_pdfvars`/`_pdfas` for that reason. Current (correct) state of the dict:

1. `$WREM_BASE/wremnants/production/theory_corrections.py` (`theory_corr_weight_map` — controls whether the weight column is a scalar (`tensor_weight=False`, default for nominal) or a tensor (`tensor_weight=True`, needed for pdfvars/pdfas which broadcast over PDF members)):
   ```python
   "scetlib_dyturbo_NewVarsCT18ZLambda6_N3p0LL_N2LO_pdfvars": make_theory_corr_weight_info("ct18z"),
   "scetlib_dyturbo_NewVarsCT18ZLambda6_N3p0LL_N2LO_pdfas": make_theory_corr_weight_info("ct18z", alphas=True, renorm=True),
   ```
   The bare `scetlib_dyturbo_NewVarsCT18ZLambda6_N3p0LL_N2LO` is intentionally absent — that makes `define_theory_corr_weight_column` fall through to `df.Alias(corr_weight, nominal_weight_uncorr)`, so the helper sees a scalar weight and doesn't constrain the corrh's `vars`-axis size.
2. `$WREM_BASE/scripts/corrections/corrs_by_helicity/make_pdf_from_corr_gen_hists.py` `THEORY_PREDS` dict:
   ```python
   "scetlib_dyturbo_NewVarsCT18ZLambda6_N3p0LL_N2LO_pdfvars": {"pdf": "ct18z"},
   ```
3. `$WREM_BASE/scripts/corrections/corrs_by_helicity/make_alphaS_gen_hists.py` `THEORY_PREDS` dict:
   ```python
   "scetlib_dyturbo_NewVarsCT18ZLambda6_N3p0LL_N2LO_pdfas": {"pdf": "ct18z"},
   ```

### Invocation (2026-05-23)

```bash
source setup.sh
OUT=$MY_OUT_DIR/$(date +%y%m%d)_pdfsFromCorrByHelicity_NewVarsCT18ZLambda6_v3/
mkdir -p $OUT
nohup singularity exec ... bash -c 'source /opt/venv/bin/activate; cd <WRemnantsHelpers>; source setup.sh; \
  python3 $WREM_BASE/scripts/corrections/corrs_by_helicity/make_pdf_from_corr_gen_hists.py \
    --preds scetlib_dyturbo_NewVarsCT18ZLambda6_N3p0LL_N2LO_pdfvars \
    -o $OUT --skim --bosons Z' > <log> 2>&1 &
```
Same pattern for pdfas with `make_alphaS_gen_hists.py`.

### Important hack — wrong workflow scripts originally

There are TWO sets of `corrs_by_helicity/` workflow scripts in lavezzo's tree:
- ❌ `/home/submit/lavezzo/alphaS/WRemnantsHelpers/workflows/corrs_by_helicity/` (stale; passes obsolete `--useCorrByHelicityBinning` flag that current histmaker rejects; THEORY_PREDS entries are short outdated names that don't match `valid_theory_corrections()`)
- ✅ `$WREM_BASE/scripts/corrections/corrs_by_helicity/` (the correct, in-WRemnants pair)

The WRemnantsHelpers ones look authoritative because they're "yours" (lavezzo) but are out of sync with WRemnants. **Use the WRemnants scripts.** I patched both, but only the WRemnants ones matter for actual runs.

### Output files

For each pdfvars/pdfas pred, two files written to `$OUT/`:
- `w_z_gen_dists_<pred>_Corr_maxFiles_m1.hdf5` (full)
- `w_z_gen_dists_<pred>_Corr_maxFiles_m1_skimmed.hdf5` (filtered to `nominal_gen_*_Corr` + `nominal_gen_pdf_uncorr`, or `nominal_gen_theory_uncorr` for pdfas)

### pdfvars by-helicity result (2026-05-23)

Run with `--bosons Z` (skipped W since our scetlib correction is Z-only — only `_CorrZ.pkl.lz4` exists, no `_CorrW.pkl.lz4`). Event loop wall-time: 442 s (~7.5 min). Outputs at `$MY_OUT_DIR/260523_pdfsFromCorrByHelicity_NewVarsCT18ZLambda6_v3/`:
- full: `w_z_gen_dists_scetlib_dyturbo_NewVarsCT18ZLambda6_N3p0LL_N2LO_pdfvars_Corr_maxFiles_m1.hdf5` (64 MB)
- skimmed: `..._skimmed.hdf5` (13 MB)

### pdfas by-helicity result (2026-05-23)

Same recipe, `--bosons Z`. Finished ~12:22 same day. Outputs at `$MY_OUT_DIR/260523_alphaSByHelicity_NewVarsCT18ZLambda6_v3/`:
- full: `w_z_gen_dists_scetlib_dyturbo_NewVarsCT18ZLambda6_N3p0LL_N2LO_pdfas_Corr_maxFiles_m1.hdf5`
- skimmed: `..._skimmed.hdf5`

### Histmaker dilepton run (2026-05-25)

Forked `workflows/histmaker.sh` → `workflows/histmaker_newvars_ct18z_lambda6.sh`. Same template, but `--theoryCorr` list swaps the standard `LatticeNP_CT18Z` trio for our `NewVarsCT18ZLambda6` trio:
```
--theoryCorr 'scetlib_dyturbo_NewVarsCT18ZLambda6_N3p0LL_N2LO' \
             'scetlib_dyturbo_NewVarsCT18ZLambda6_N3p0LL_N2LO_pdfvars' \
             'scetlib_dyturbo_NewVarsCT18ZLambda6_N3p0LL_N2LO_pdfas' \
             'scetlib_dyturbo_LatticeNP_MSHT20mbrange_N3p0LL_N2LO_pdfvars' \
             'scetlib_dyturbo_LatticeNP_MSHT20mcrange_N3p0LL_N2LO_pdfvars'
```
(mbrange/mcrange kept from upstream since they're orthogonal — quark-mass uncertainty PDFs.)

**v1 (14:37 UTC) — killed**: launched without copying by-helicity skimmed files. Histmaker emitted WARNINGS like:
> `theory_corrections.py: File .../wremnants-data/data/TheoryCorrections/ByHelicity/AlphaS/<our_pdfas_skimmed>.hdf5 does not exist. Not creating histogram of variations by helicities.`

**Important discovery — silent silent-downgrade**: the histmaker would have COMPLETED but with the by-helicity variation decomposition DROPPED. Only a WARNING, no error. Would have wasted hours of compute on a partial result.

**Fix (the hack)**: by-helicity skimmed files must live in
- `$WREM_BASE/wremnants-data/data/TheoryCorrections/ByHelicity/AlphaS/` for pdfas
- `$WREM_BASE/wremnants-data/data/TheoryCorrections/ByHelicity/PDFsFromCorrs/` for pdfvars

NOT just at `$MY_OUT_DIR/...` where the workflow scripts write them. The `make_alphaS_gen_hists.py` / `make_pdf_from_corr_gen_hists.py` wrappers write to `$MY_OUT_DIR` but the histmaker reads from `$WREM_BASE/wremnants-data/...`. **Manual copy/symlink required** between the two steps. Hardcoded path in WRemnants — no flag to override.

```bash
cp $MY_OUT_DIR/260523_pdfsFromCorrByHelicity_NewVarsCT18ZLambda6_v3/w_z_gen_dists_scetlib_dyturbo_NewVarsCT18ZLambda6_N3p0LL_N2LO_pdfvars_Corr_maxFiles_m1_skimmed.hdf5 \
   $WREM_BASE/wremnants-data/data/TheoryCorrections/ByHelicity/PDFsFromCorrs/
cp $MY_OUT_DIR/260523_alphaSByHelicity_NewVarsCT18ZLambda6_v3/w_z_gen_dists_scetlib_dyturbo_NewVarsCT18ZLambda6_N3p0LL_N2LO_pdfas_Corr_maxFiles_m1_skimmed.hdf5 \
   $WREM_BASE/wremnants-data/data/TheoryCorrections/ByHelicity/AlphaS/
```

**v2 (14:39 UTC) — running**: with files in place. Output dir: `$MY_OUT_DIR/260525_histmaker_dilepton_NewVarsCT18ZLambda6/`. Monitor: `b5j7e7tsj`. No more "does not exist" warnings.

### Known gap

Between 2026-05-23 ~12:22 (pdfas by-helicity finished) and 2026-05-25 14:37 (histmaker launched), **the histmaker run was sitting waiting** — I had not set up an auto-chain from pdfas → histmaker, so the chain stalled when my pdfas monitor exited. ~2 days lost on this step. The auto-chain monitor for pdfvars → pdfas worked correctly; the chain just stopped at pdfas.

## TheoryCorrection generation recipe (CT18Z lambda6 → scetlib_dyturbo)

The chain that produced `scetlib_dyturbo_NewVarsCT18ZLambda6_N3p0LL_N2LO_{,pdfvars_,pdfas_}CorrZ.pkl.lz4` (2026-05-23):

```bash
# 1. combine per production (writes <ini_stem>_combined.pkl in CWD)
scetlib-manage-condor-submit.py -s $SCETLIB -r <ini> -b 205 -j 2 -f <submitdir> \
  --runtime-tarball $TARBALL combine
# (for pdfvars: add -p 59)
# (for pdfas:   add -p CT18ZNNLO_as_0116 CT18ZNNLO_as_0118 CT18ZNNLO_as_0120 -a 0.116 0.118 0.120)

# 2. make_theory_corr.py with required args:
python3 $WREM_BASE/scripts/corrections/make_theory_corr.py \
  -m /ceph/submit/data/user/a/areimers/alphas/gendistributions/w_z_gen_dists_maxFiles_m1_msht20an3lo_finePtAbsY_Z_Fullstats.hdf5 \
  -g scetlib_dyturbo --proc z \
  --eras 13TeVGen --qtCutoff 1.0 --minnloh nominal_gen \
  -o $WREM_BASE/wremnants-data/data/TheoryCorrections/ \
  --axes Q Y qT \
  -c <resummed_combined.pkl> <nnlo_sing_combined.pkl> \
     '/home/submit/david_w/work/TheoryCorrections/DYTURBO/nnlo-scetlibmatch-13TeV-CT18Z-finer-bin/scalevariations/z0/results_z-2d-nnlo-vj-CT18ZNNLO-{scale}-scetlibmatch.txt' \
  -p NewVarsCT18ZLambda6_N3p0LL_N2LO
```

**Critical args I had to debug** (none of these are documented in the older MSHT-lambda6cs recipe in [[scetlib-msht-4plus0-lambda6cs]]):
- `--eras 13TeVGen` (the script defaults match an older sample naming; new gendist files require this flag)
- `--minnloh nominal_gen` (histogram name in the MiNNLO gendist)
- `--qtCutoff 1.0` (zeros out bins with qT<1 GeV in the singular subtraction)
- `--axes Q Y qT` (3D, not just Y qT)
- 3rd `-c` arg: David Walter's DYTURBO scale-variations txt template at `/home/submit/david_w/work/TheoryCorrections/DYTURBO/nnlo-scetlibmatch-13TeV-CT18Z-finer-bin/.../{scale}-scetlibmatch.txt` — PDF-set specific (CT18ZNNLO) but NP-independent, so reusable across NP-variation productions.

Gendist file: `/ceph/submit/data/user/a/areimers/alphas/gendistributions/w_z_gen_dists_maxFiles_m1_msht20an3lo_finePtAbsY_Z_Fullstats.hdf5` worked fine for CT18Z output (gendist holds MiNNLO MC samples that get PDF-reweighted to whatever the scetlib pkl's pdf_set is).

For `scetlib_nnlojet` mode (N4+0LL + N3LO matching), use `-g scetlib_nnlojet` and replace the DYTURBO txt with the NNLOjet `result/final/nnlo.ptz` path; also pass `--nnlojetMassEdges 60 120`.

## Known hacks / caveats

- **2026-05-23 — Mixed-precision combine hack**: The nominal CT18Z lambda6 production was first run with `target_precision_rel = 1.e-5` (cluster 2690810); during the retry-everything-that-hung phase, the submitdir `.ini` was edited to `1.e-3` for clusters 2701217 + 2718416 + 2746278 + the local rerun. Same for pdfvars (item 223 retry at 1e-3 vs the rest at 1e-5). Result: `scetlib-manage-condor-submit.py combine` rejects the heterogeneous pkls with "Found different config files! Cannot combine." because the embedded `[Integration]` block in the pkl's config differs. **Workaround applied: ran a one-off Python script that walks every pkl, loads it with `pickle`, deletes `target_precision_rel` + `target_precision_abs` from the embedded `config['Integration']` dict, and writes the pkl back in place.** Histogram data is untouched. Effect on the combined output: none (Cuba precision affected how the integration was done, not what number was produced). Consequence: the pkls no longer record their original precision setting — provenance loss. For future productions, set a uniform precision up front, OR fix the strict config check in `combine_pkl_files` to ignore precision-only diffs.

- **2026-05-25 — Vars-axis-mismatch silent-drop bug (NVARS=43 vs 49)**. The original CT18Z lambda6 production (cluster 2690810) ran with `variations_lattice_allvars.conf` containing 43 entries: `[0]`–`[41]` standard + `[42]` Ext-block validation. After we added 6 alignment variations to match Arne's franksvals (`[43]`–`[48]`: `delta_lambda2 ±0.02`, `muf ±`, paired `kappa×muf`) and submitted them as cluster 2746278, the resulting submitdir had a mix of **43-var pkls** (from 2690810 + earlier resubmits, 2408 of 2744) and **49-var pkls** (from 2746278, 336 of 2744). The vendor combine in `scetlib-manage-condor-submit.py` does `combh += otherh` after a `shape == shape` check, which silently fails (boost-histogram rejects "axes not mergable") only if the StrCategory axes differ in length; **but in this codebase the earlier combine appears to have first-pkl-won the axis size as 43, then silently dropped the 6 alignment vars from every 49-var pkl** (combine ran without error, output was 43 vars). The downstream `make_theory_corr.py` then produced `scetlib_dyturbo_NewVarsCT18ZLambda6_N3p0LL_N2LO_CorrZ.pkl.lz4` with 43 vars — missing all the alignment vars we explicitly added. The mz_dilepton histmaker happily consumed the 43-var CorrZ. Discovered when we tried to extend the *MSHT* 36-var pkls 36→42 with the new 6 vars and hit the same axis-mismatch, then verified the CT18Z corr also had 43 vars instead of 49.
  - **Recovery applied (2026-05-25)**:
    1. Wrote `scripts/extend_vars_axis_sidecar_v2.py` (originally drafted in `/tmp/`, now persisted in the repo) — extends 43-var pkls to 49 vars by inserting the 6 new labels at positions [42]–[47] BEFORE the Ext block (which slots from old [42] → new [48], matching the canonical axis order observed in the originally-49-var pkls). Writes to a sidecar dir `scetlib_outputs_v49/` instead of mutating in place. 2408 extended; 336 copied as-is.
    2. Wrote `scripts/standalone_combine.py` (originally drafted in `/tmp/`, now persisted in the repo) — minimal combine that mirrors `scetlib-manage-condor-submit.py`'s `combine_pkl_files`/`combine_jobs` but does NOT import `scetlib_core` (which is only available in `:v15` where the pkls' embedded numpy version is incompatible). Pkls were saved with numpy 2.x (`numpy._core`) in `:latest` and read fine there; the combine script reads/writes with `pickle` directly. Supports `--ignore-config-diff` to bypass the strict `config != config` check (needed because alphas_mu0/pdf_member popping is order-dependent across heterogeneous runs).
    3. Re-combined → new `scetlib_outputs/inclusive_..._combined.pkl` (49 vars, shape `(2,82,70,49)`).
    4. Renamed old CorrZ → `.bak_43var`, ran `make_theory_corr.py` → new 49-var `scetlib_dyturbo_NewVarsCT18ZLambda6_N3p0LL_N2LO_CorrZ.pkl.lz4`.
    5. Relaunched histmaker as `_v3` with `-j 200` (v2 OOM-killed at 25min).
  - **Same bug also affected MSHT20aN3LO N4+0LL and N3+0LL Newvals_Coarse productions.** Extend was done 36→42; MSHT has no Ext block at end, so the append-at-tail extension was canonically correct. Combined.pkls regenerated 2026-05-25 (42 vars each, alignment vars at positions 36–41). The existing `scetlib_nnlojet_NewVars_MSHT20aN3LO_N4p0LL_N3LO_CorrZ.pkl.lz4` was still 36-var → renamed to `.bak_36var_before_42var_extend`; needs `make_theory_corr.py -g scetlib_nnlojet` regeneration. MSHT N3+0LL nominal CorrZ doesn't exist at production path yet.
  - **Where this bug bit silently**: the vendor combine's `combh += otherh` after a `shape == shape` check is supposed to be safe, but the StrCategory axes have `growth=True` in our newer pkls, which I now suspect changed the equality semantics. For future productions: explicitly verify the combined `vars` axis labels match the union of the variations.conf, not just the count.

- **2026-05-26 — tensor_weight registration bug for NewVarsCT18ZLambda6 nominal**. The CT18Z lambda6 histmaker v3 crashed at 15min into the event loop with: `RDataFrame: type mismatch: column "scetlib_dyturbo_NewVarsCT18ZLambda6_N3p0LL_N2LO_corr_weight" is being used as Eigen::Sizes<61> but the Define or Vary node advertises it as Eigen::Sizes<59>`. Root cause: when I added the new corr names to `wremnants/production/theory_corrections.py`'s `theory_corr_weight_map`, I registered ALL THREE variants (bare nominal + `_pdfvars` + `_pdfas`). The existing baseline `LatticeNP_CT18Z` only registers `_pdfvars`/`_pdfas` — not the bare nominal. Registering the bare nominal in this map forces `tensor_weight=True` in `define_theory_corr_weight_column`, which `Define`s a `_corr_weight` column with `Sizes<len(values)>=Sizes<59>` (CT18Z PDF entries from theory_utils.pdfMap). But `TensorCorrectionsHelper4D` is templated on the corr histogram's tensor type (after `postprocess_corr_hist` envelope appends → 49 + 12 = 61). 59 ≠ 61, so the RDataFrame column types disagree. Fix applied 2026-05-26: removed the bare entry from `theory_corr_weight_map`. The nominal now goes through the `Alias(.., "nominal_weight_uncorr")` branch → `tensor_weight=False` → helper's `nominal_weights` arg becomes a scalar `double`, which doesn't constrain corrh's vars-axis size. Histmaker relaunched as v4 — **finished successfully 2026-05-26 10:32** in 2h end-to-end (event loop 1h40m, write ~10m), output at `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260526_histmaker_dilepton_NewVarsCT18ZLambda6/mz_dilepton_v4.hdf5` (6.5 GB).

- **2026-05-26 — Two fitter.sh / rabbit pitfalls when running the v4 fit**.
  - `--npUnc LatticeNoConstraints` (fitter.sh default) requires lattice-style lambda variations (`lambda2_nu0.1202`, `lambda4_nu0.014`, ...) which the NewVars corrh doesn't have — we have the franks-style `lambda2_nu0.25` / `lambda2_nu0.05`. Setup raises `ValueError: Using the lattice NP model without constraints on gamma parameters, but could not find the 3 Eigenvariations for gamma in hist ...`. Fix: pass `-e '--npUnc LatticeNoConstraintsFranks'` to fitter.sh (or call setupRabbit directly with that flag). The Franks variant uses only `scetlibNPgammaLambda2` (lambda2_nu only) on the CS side, consistent with the newvals NP setup.
  - HDF5 file-locking on cephfs sporadically blocks the tensorwriter create call with `BlockingIOError: [Errno 11] Unable to synchronously create file`. Fix: `export HDF5_USE_FILE_LOCKING=FALSE` before launching `setupRabbit.py` / `rabbit_fit.py`. This is benign — the locking system call cephfs returns EAGAIN on isn't doing anything load-bearing for these writes.
  - Side gotcha: `fitter.sh` captures `setup_output=$(setupRabbit ... 2>&1)` into a variable, which means stdout/stderr buffer until the command exits. If setupRabbit crashes mid-way, the script swallows the error silently — the log just stops at the launch line and the chain "ends." When diagnosing a silent fit failure, re-run setupRabbit directly with `python -u` so each line flushes as it's emitted.
- **CT18Z lambda6 fit closure (Asimov, 2026-05-26 12:57)**: setupRabbit produced `ZMassDilepton.hdf5` (1.0 GB) in 149s; rabbit_fit (defaults: `--noi alphaS --pdfUncFromCorr --npUnc LatticeNoConstraintsFranks --axlim ptll 0j 44j`, no `--scaleParams` inflation) converged in 105s with NLL = 0, χ²/ndf = 0/39, p-value = 100%. Asimov closure expected to be exact; this confirms the new 49-var CorrZ + extended pkls + tensor_weight registration fix are mutually consistent. `fitresults.hdf5` at `/ceph/.../260526_fit_NewVarsCT18ZLambda6/ZMassDilepton_..._NewVarsCT18ZLambda6_v4_franks/fitresults.hdf5` (115 MB). Real-data fit would add `-t 0` to rabbit_fit.

## Runbook — how to drive this chain by hand

This section is a takeover guide: paths, commands, and how to recover from each step. Everything runs inside the `wmassdevrolling:latest` singularity container with `/opt/venv` activated and `setup.sh` sourced (use `:v15` only for scetlib *production* / rebuild — combine + corrections + histmaker all run in `:latest`).

### Standard environment header (paste at the top of any session)

```bash
singularity run --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/,/tmp/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers && source setup.sh
```

After this, `$WREM_BASE` resolves to the WRemnants checkout and `$MY_OUT_DIR` resolves to the ceph output root.

### Helper scripts (durable in repo `scripts/`)

Persisted under `/home/submit/lavezzo/alphaS/WRemnantsHelpers/scripts/`:

- `scripts/extend_vars_axis_sidecar_v2.py` — extends 43-var CT18Z pkls to 49 vars by inserting the 6 alignment labels at positions [42]–[47] and pushing Ext to [48]. Writes to a sidecar dir, never mutates the source. Usage: `python3 scripts/extend_vars_axis_sidecar_v2.py <src_dir> <dst_dir>`.
- `scripts/extend_vars_axis.py` — older 36→42 MSHT version (no Ext-block reslot, just appends). Already applied to MSHT N3 and N4 in place.
- `scripts/standalone_combine.py` — minimal SCETlib combine that bypasses `scetlib_core` import. Usage: `python3 scripts/standalone_combine.py <pkl_dir> <runcard_stem> <out_pkl> [--ignore-config-diff] [--skip-missing] [--pdfs <csv>]`. Pass `--ignore-config-diff` for any heterogeneous-precision submitdir.

### Where everything lives

- **WRemnants** + wremnants-data: `/home/submit/lavezzo/alphaS/main/WRemnants` (`$WREM_BASE`)
- **TheoryCorrection pkls** (read by mz_dilepton): `$WREM_BASE/wremnants-data/data/TheoryCorrections/`
- **By-helicity HDF5 files**: `$WREM_BASE/wremnants-data/data/TheoryCorrections/ByHelicity/{AlphaS,PDFsFromCorrs}/`
- **Histmaker output**: `$MY_OUT_DIR/<YYMMDD>_histmaker_dilepton_NewVarsCT18ZLambda6/` (= `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/...`)
- **Logs**: `/home/submit/lavezzo/alphaS/WRemnantsHelpers/logs/`
- **SCETlib submitdirs** (one per production):
  - CT18Z lambda6 nominal: `/ceph/submit/data/user/l/lavezzo/zstuff/Z_COM13_CT18Z_N3p0LL_NewNPs_Lattice_Newvals_Lambda6_Fine`
  - CT18Z lambda6 nnlo_sing: `..._nnlo_sing`
  - CT18Z lambda6 pdfvars / pdfas: `..._pdfvars` / `..._pdfas`
  - MSHT N4+0LL Newvals nominal: `/ceph/submit/data/user/l/lavezzo/zstuff/Z_COM13_MSHT20aN3LO_N4p0LL_NewNPs_Lattice_Newvals_Coarse`
  - MSHT N3+0LL Newvals nominal: `/ceph/submit/data/user/l/lavezzo/zstuff/Z_COM13_MSHT20aN3LO_N3p0LL_NewNPs_Lattice_Newvals_Coarse`
- **CT18Z lambda6 sidecar v49 outputs** (extended): `Z_COM13_CT18Z_N3p0LL_NewNPs_Lattice_Newvals_Lambda6_Fine/scetlib_outputs_v49/`. Source `scetlib_outputs/` was *not* mutated — if you want to revert to 43-var combine, use that dir.
- **Backups of mutated corr pkls**:
  - `.../scetlib_dyturbo_NewVarsCT18ZLambda6_N3p0LL_N2LO_CorrZ.pkl.lz4.bak_43var` (replaced by 49-var)
  - `.../scetlib_nnlojet_NewVars_MSHT20aN3LO_N4p0LL_N3LO_CorrZ.pkl.lz4.bak_36var_before_42var_extend` (current production CorrZ at .lz4 NOT YET regenerated to 42-var; needs `make_theory_corr.py -g scetlib_nnlojet`)
- **Authored physics docs**: `cooper/working/scetlib_msht_n4p0_procedure/procedure.md` has the MSHT N4 `make_theory_corr -g scetlib_nnlojet` recipe + rename-step.

### 1. Re-combine a SCETlib submitdir (after extending pkls or after a re-run)

```bash
SUBMIT=/ceph/submit/data/user/l/lavezzo/zstuff/Z_COM13_CT18Z_N3p0LL_NewNPs_Lattice_Newvals_Lambda6_Fine
INI_STEM=inclusive_Z_COM13_CT18Z_N3+0LL_newvals_lambda6_fine   # NO .ini suffix
OUT=$SUBMIT/${INI_STEM}_combined.pkl
python3 $MY_WORK_DIR/scripts/standalone_combine.py $SUBMIT/scetlib_outputs_v49 $INI_STEM $OUT --ignore-config-diff
```

For MSHT just change `SUBMIT` and `INI_STEM` (no sidecar — N3/N4 were extended in place, so pass `$SUBMIT/scetlib_outputs`). The script prints the final `vars` axis labels — verify the alignment vars are present and at the right positions before moving on.

### 2. Re-make a TheoryCorrection `.pkl.lz4` after a new combined.pkl

CT18Z lambda6 nominal (dyturbo + DYTURBO scale-vars text file):

```bash
GENDIST=/ceph/submit/data/user/a/areimers/alphas/gendistributions/w_z_gen_dists_maxFiles_m1_msht20an3lo_finePtAbsY_Z_Fullstats.hdf5
RESUMM=/ceph/submit/data/user/l/lavezzo/zstuff/Z_COM13_CT18Z_N3p0LL_NewNPs_Lattice_Newvals_Lambda6_Fine/scetlib_outputs/inclusive_Z_COM13_CT18Z_N3+0LL_newvals_lambda6_fine_combined.pkl   # (note: ended up in scetlib_outputs/, not submitdir root)
NNLO_SING=/home/submit/lavezzo/alphaS/WRemnantsHelpers/inclusive_Z_COM13_CT18Z_N3+0LL_newvals_lambda6_fine_nnlo_sing_combined.pkl
DYTURBO_FO='/home/submit/david_w/work/TheoryCorrections/DYTURBO/nnlo-scetlibmatch-13TeV-CT18Z-finer-bin/scalevariations/z0/results_z-2d-nnlo-vj-CT18ZNNLO-{scale}-scetlibmatch.txt'
# Back up the old corr first!
mv $WREM_BASE/wremnants-data/data/TheoryCorrections/scetlib_dyturbo_NewVarsCT18ZLambda6_N3p0LL_N2LO_CorrZ.pkl.lz4{,.bak_$(date +%y%m%d_%H%M)}
python3 $WREM_BASE/scripts/corrections/make_theory_corr.py \
  -m $GENDIST -g scetlib_dyturbo --proc z \
  --eras 13TeVGen --qtCutoff 1.0 --minnloh nominal_gen \
  -o $WREM_BASE/wremnants-data/data/TheoryCorrections/ \
  --axes Q Y qT \
  -c $RESUMM $NNLO_SING "$DYTURBO_FO" \
  -p NewVarsCT18ZLambda6_N3p0LL_N2LO
```

MSHT N4 nominal (nnlojet + NNLOjet dir, two-step with `rename_corr_file.py`): see `cooper/working/scetlib_msht_n4p0_procedure/procedure.md`.

### 3. Refresh by-helicity HDF5 files (consumed by histmaker for pdfvars + pdfas)

Live in `$WREM_BASE/wremnants-data/data/TheoryCorrections/ByHelicity/{AlphaS,PDFsFromCorrs}/`. The mz_dilepton silently downgrades to a WARNING if these files are missing — always verify they exist for the corr names listed in `workflows/histmaker_*.sh`. Regenerate with `$WREM_BASE/scripts/corrections/corrs_by_helicity/make_pdf_from_corr_gen_hists.py` (pdfvars) or `make_alphaS_gen_hists.py` (pdfas), then copy the `_skimmed.hdf5` output into `ByHelicity/`. **Do not use** the wrapper at `WRemnantsHelpers/workflows/corrs_by_helicity/` — those have a stale `--useCorrByHelicityBinning` flag.

### 4. Run the histmaker

```bash
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
# v4 form:
bash workflows/histmaker_newvars_ct18z_lambda6.sh -p v5 -e '-j 200'
# In background with logging:
nohup bash workflows/histmaker_newvars_ct18z_lambda6.sh -p v5 -e '-j 200' \
  > logs/histmaker_NewVarsCT18ZLambda6_v5_$(date +%y%m%d_%H%M%S).log 2>&1 &
```

User cap: max 200 CPUs. The default `-j 0` ("all threads") is what OOM-killed v2. Always pass `-e '-j 200'`.

Quick health checks while running:

```bash
# is it still alive?
pgrep -af "mz_dilepton" | grep -v shell-snapshot
# latest log progress
tail -20 $(ls -t logs/histmaker_NewVarsCT18ZLambda6_v*.log | head -1)
# event-loop progress line (every 5 min)
grep "processed files" logs/histmaker_NewVarsCT18ZLambda6_v*.log | tail
# any crash signatures?
grep -E "Traceback|Killed|Error:|FAILED|OOM" logs/histmaker_NewVarsCT18ZLambda6_v*.log | tail
```

### 5. Registering a new corr name in WRemnants

When you make a new CorrZ.pkl.lz4 with a new label (e.g. `NewVarsCT18ZLambda6 → NewerThing`), three edits are needed (all already in place for the current name):

1. `wremnants/production/theory_corrections.py` `theory_corr_weight_map` — **only** the `_pdfvars` and `_pdfas` variants. **Do NOT add the bare nominal** (that forced tensor_weight=True and broke v3; see hack note above).
2. `scripts/corrections/corrs_by_helicity/make_pdf_from_corr_gen_hists.py` `THEORY_PREDS` dict — only the `_pdfvars` form.
3. `scripts/corrections/corrs_by_helicity/make_alphaS_gen_hists.py` `THEORY_PREDS` dict — only the `_pdfas` form.

### 6. Pending MSHT chain

State as of 2026-05-26:

- ✅ MSHT N4+0LL Newvals combined.pkl: 42 vars at `Z_COM13_MSHT20aN3LO_N4p0LL_NewNPs_Lattice_Newvals_Coarse/inclusive_..._combined.pkl`.
- ✅ MSHT N3+0LL Newvals combined.pkl: 42 vars at `Z_COM13_MSHT20aN3LO_N3p0LL_NewNPs_Lattice_Newvals_Coarse/inclusive_..._combined.pkl`.
- ❌ MSHT N4 `scetlib_nnlojet_NewVars_MSHT20aN3LO_N4p0LL_N3LO_CorrZ.pkl.lz4` — current production file is still 36-var (`.bak_36var_before_42var_extend` is the same file pre-our-changes). Needs `make_theory_corr.py -g scetlib_nnlojet` against the new 42-var combined.pkl (recipe in `cooper/working/scetlib_msht_n4p0_procedure/procedure.md`). Don't forget the `rename_corr_file.py` second step.
- ❌ MSHT N3 nominal CorrZ — doesn't exist at production path. Need to decide whether to use scetlib_dyturbo or scetlib_nnlojet (3+0LL doesn't need N3LO matching, so dyturbo + DYTURBO FO text file analogous to CT18Z).
- ❌ MSHT by-helicity files — existing ones may be from old 36-var pkls; regenerate after the new CorrZ files exist.
- ❌ MSHT histmaker(s) — same wrapper pattern as CT18Z, just different `--theoryCorr` names.

### 7. If you discover the alignment vars are missing again

It means a combine somewhere first-pkl-won the axis at the smaller size and dropped the rest. The fingerprint:

```bash
# Quick check on any CorrZ.pkl.lz4:
python3 -c "import lz4.frame,pickle;d=pickle.load(lz4.frame.open('<CorrZ.pkl.lz4>','rb'));h=next(v for k,v in d['Z'].items() if 'hist' in k);print(len(list(h.axes['vars'])),list(h.axes['vars'])[-8:])"
```

If the last 8 don't include `delta_lambda2-0.02` ... `mufup-kappaFO2.-kappaf0.5`, you're back at the broken state. Re-run the extend → re-combine → re-make_theory_corr → re-launch chain in §1–§4.

## Status

2026-05-20 — End-of-prep snapshot. **Everything is staged for the user to `condor_submit`** when they return:

- **Patch** applied + plumbed (4 files, +6/−1 lines): `NP_models.hpp:88` hardcoded `0.016` → runtime `lambda6` member (default 0.016) + pybind11 binding + defaults.conf + variations.py. Existing tanh_6 configs untouched at default. Scetlib rebuilt clean in `:v15` container; pybind smoke test passes.
- **Config** at `/work/submit/lavezzo/alphaS/TheoryCorrections/SCETlib/com13_ct18z_newnps_n3+0ll_lattice_newvals_lambda6_fine/` with newvals NP centrals + tanh_6 + 43-entry variations file (6 new entries: lambda4=-0.4, lambda_inf=2.0, lambda6 ∈ {0.05, 0.1, 0.2, 0.5}; validation block [42] = old lambda6cs setup; plus standard FO/TNP/transition-point variations).
- **Single-bin smoke test at bin 100** ran cleanly for 6/7 tested variations (central + lambda6 scan + validation + lambda_inf=2). All xsecs finite, deltas physically reasonable, lambda6 scan mostly monotonic with a tanh-saturation turning point between 0.2 and 0.5.
- **Tarball + condor.submit ready**: `/ceph/.../scetlib_runtime_submit_ct18z_lambda6.tar.gz` (built in :v15 with patched scetlib + CT18ZNNLO_beamfunc) and `/ceph/.../Z_COM13_CT18Z_N3p0LL_NewNPs_Lattice_Newvals_Lambda6_Fine/condor.submit` (43 vars × 56 bin-steps × 1 PDF = **2408 jobs**, workday queue, 8h cap).
- **var 5 lambda4=-0.4 slowness verdict**: bin-specific (not universal). At central bin 8690 it took 91s (4× central's 24s). The off-shell forward corner was the bad case. Production should fit within workday queue.

**Submitted as cluster 2690810** at 2026-05-20 22:18 UTC; 2347/2408 (97.5%) succeeded. **61 jobs hung** with zero output (all 56 var-5 + 5 tail-bin + 2 var-4) and were `condor_rm`'d at 2026-05-21 ~06:55 UTC. Resubmit file at `condor_resubmit.submit` ready but NOT submitted — same config re-hangs. **Next action**: user picks strategy (relaxed precision / split bins / drop var-5 / source-level debug) for the 61-job retry. Once strategy chosen, edit a per-bin override in the .ini or fork the variations file, rebuild tarball if needed, condor_submit the resubmit batch. Once all 2408 pkls exist, run `combine` op → `_combined.pkl`. Then decide downstream chain (scetlib_dyturbo + nnlo_sing companion).

## Guiding Question

Produce a SCETlib `_combined.pkl` for CT18ZNNLO at N3+0LL with newvals NP + tanh_6 model + a TMD lambda_6 scan + lambda_4 = -0.4 excursion, so franks-vals-fit can validate its linearized data preference and probe the tanh_6 parametrization.

## Hypotheses

- Promoting the hardcoded TMD lambda_6 constant (NP_models.hpp:88 = 0.016) to a runtime `lambda6` member with default 0.016 leaves existing tanh_6 configs bit-equivalent, while enabling the requested {0.05, 0.1, 0.2, 0.5} variation scan in a single condor submission. [active]
- The newvals NP centrals port cleanly to CT18Z by swapping pdf_set + adopting CT18Z 3+0 fine grids + flipping np_model/np_model_nu to tanh_6. [active]
- Explicit SCETlib templates at lambda_4 = -0.4 (and the lambda_6 scan) will let the [[study:franks-vals-fit]] linearization be validated or refuted against a non-linear NP shape. [active]

## Ideas / Methods Explored

- Starting from MSHT20an3lo's `com13_msht20an3lo_newnps_n3+0ll_lattice_newvals_coarse/` as the closest existing config (newvals NP block already in place; just need PDF swap + grid swap + tanh_2 → tanh_6).
- Variations file built by additively layering 6 new entries (lambda_4 = -0.4, lambda_inf = 2.0, lambda_6 × 4) on top of the MSHT newvals_coarse variations file.
- Beamfuncs reusable: CT18ZNNLO_beamfunc already present at /work/submit/lavezzo/alphaS/scetlib-cms-newnp-lambda4fix/share/scetlib/beamfunc/ (verified 2026-05-20).

## Dead-Ends

- (None yet.)

## Findings

- 2026-05-20 — Both TMD and CS sides of scetlib have a separate hardcoded lambda_6 in their respective tanh_6 cases. TMD: `NP_models.hpp:88` adds `0.016 * pow<5>(bT) / lambda_inf`. CS: `Gamma_nu.hpp:102` adds `0.0007 * pow<3>(bT2) / lambda_inf_nu`. User's spec varies the TMD one; CS stays at hardcoded default. (evidence: scetlib-cms-newnp-lambda4fix/include/scetlib/qT/{NP_models.hpp:87-91, Gamma_nu.hpp:101-104})
- 2026-05-20 — TMD-side NP plumbing: `NPModelEffective` (C++ struct in NP_models.hpp) ← pybind11 binding in `py/qT/qT.cpp:158-164` ← variations.py reads it from `.ini` Nonperturbative section via `nonp_fields` list (line 77) + `set_effective_model` assigns into pybind struct (line 226). Default values pre-populated from `defaults.conf:88-92` if a variation block doesn't override. Adding lambda6 requires 6 edits: 1× header (struct member), 1× header (formula), 1× pybind binding, 1× defaults.conf, 1× variations.py nonp_fields, 1× variations.py set_effective_model.
- 2026-05-20 — CT18ZNNLO_beamfunc available at /work/submit/lavezzo/alphaS/scetlib-cms-newnp-lambda4fix/share/scetlib/beamfunc/CT18ZNNLO_beamfunc (also as_0116/0118/0120 siblings) — no regeneration needed for the new run. Same rebuilt scetlib binary will pick them up.
- 2026-05-20 — Source patch landed: NP_models.hpp:88 promoted hardcoded `0.016` → runtime member `lambda6` (default 0.016 on the C++ struct, default 0.016 in `defaults.conf`). 4 files / +6/-1 lines: NP_models.hpp (struct + formula), py/qT/qT.cpp (pybind binding), prod/scetlib_run/defaults.conf, prod/scetlib_run/scetlib_run/variations.py (nonp_fields + set_effective_model). Existing tanh_6 configs that don't set lambda6 stay bit-equivalent.
- 2026-05-20 — Config dir `com13_ct18z_newnps_n3+0ll_lattice_newvals_lambda6_fine/` scaffolded with base.conf + inclusive_Z .ini + variations_lattice_allvars.conf (42 entries + central). Validation block [42] reproduces the old lambda6cs setup (tanh_6 + old NP centrals + lambda6=0.016) for cross-check against existing lambda6cs templates.
- 2026-05-20 — Container ABI dependency: scetlib must be built inside `wmassdevrolling:v15` (Python 3.10, gsl 2.7.1) to match the production condor wrapper (`wrap-scetlib-run-qT.sh`). My first build in `:latest` (Python 3.13, gsl 2.8) loaded fine in :latest but failed in :v15 with `ImportError: libgsl.so.28: cannot open shared object file`. Switched to :v15 build (clean rebuild after `mv build → build_latest_<ts>; mkdir build && cd build && cmake .. && make -j32` inside :v15). Result: `.cpython-310-x86_64-linux-gnu.so` files matching the runtime wrapper. Pre-patch build preserved at `build_old_1778790090/` for reference.
- 2026-05-20 — CMake required `-DCMAKE_POLICY_VERSION_MINIMUM=3.5` override on cached :latest configure due to gtest CMakeLists `cmake_minimum_required` violation (CMake ≥ 3.5 dropped pre-3.5 compatibility). In :v15 the cmake version is older so no override needed.
- 2026-05-20 — Local single-bin smoke test at bin 100 (Q={10,60}, Y={-4.0,-3.5}, qT={15,16}) — variation [0] central (newvals + tanh_6 + lambda6=0.016) → xsec = 4.6491663308 ± 3.8e-5 in 22s. Reproducible across two independent runs (same xsec to all printed digits). pybind11 binding exposes `NPModelEffective.lambda6` with default 0.016 and settable. **Validation against unpatched scetlib bit-equivalence**: not verifiable through the full pipeline because the pre-patch build (`build_old_1778790090/`) lacks the `lambda6` member that the patched `variations.py:236` now tries to set; would require temporarily reverting variations.py to test. By inspection of the diff (literal `0.016` → variable `lambda6 = 0.016`), the values are mathematically identical when lambda6 defaults to 0.016.
- 2026-05-20 — **lambda4 = -0.4 variation [5] slowness is bin-specific** (mostly): at bin 100 (off-shell, forward-rapidity, mid-qT) Cuba did not converge in 12+ min on single-CPU; at bin 8690 (on-shell, Y~0, qT~5 GeV) it took **91s vs 24s for central → ~4× slower**. xsec at central bin = 0.3514594928 vs central 0.3775415856 → −6.9% (sensible ~2σ-below-zero excursion). For the production: average per-bin overhead for var 5 is bounded; worst case a job that happens to slice into the off-shell forward corner for var 5 might run 30+ min/bin, but on 4 CPUs (`-j 4`) per job × 205 bins, total per-job runtime estimate is in the 1–5 h range — comfortable under the 8h workday cap. **Decision: submit as-is.** If any var-5 jobs hit the runtime cap, resubmit with `-q tomorrow` queue. (evidence: evidence_lambda6_test/var5_test_bin8690.log)
- 2026-05-20 — **Local single-bin scan at bin 100, all fast variations** (scan2, ~3 min total wall):
  | var | NP override | xsec at bin 100 | Δ vs central | wall |
  |-----|-------------|-----------------|--------------|------|
  | 0   | central (newvals + tanh_6 + lambda6=0.016) | 4.6491663308 | 0 | 20s |
  | 9   | lambda6 = 0.05 | 4.6475263461 | −0.00164 | 20s |
  | 10  | lambda6 = 0.1  | 4.6448198875 | −0.00435 | 21s |
  | 11  | lambda6 = 0.2  | 4.6393854102 | −0.00978 | 30s |
  | 12  | lambda6 = 0.5  | 4.6401009714 | −0.00907 | 45s |
  | 42  | validation (old NP centrals + tanh_6 + lambda6=0.016) | 4.6132258731 | −0.0359 | 22s |
  | 6   | lambda_inf = 2.0 | 4.6483371790 | −0.00083 | 22s |
  All variations finite, no crashes. lambda6 scan is mostly monotonic with a turning point between 0.2 and 0.5 (tanh saturates → less further NP suppression at large lambda6). All Δ much larger than Cuba σ ≈ 4e-5 → real effects. Validation block [42] gives a meaningfully different xsec (−0.78% vs central) reflecting the NP-central shift, sensible for switching newvals → old lambda6cs values. (evidence: evidence_lambda6_test/scan2_bin100.log)
- 2026-05-20 — Runtime tarball + condor.submit produced and ready:
  - tarball: `/ceph/submit/data/user/l/lavezzo/tarballs_scetlib/scetlib_runtime_submit_ct18z_lambda6.tar.gz` (built fresh against :v15 with patched scetlib + CT18ZNNLO_beamfunc + variations.py with lambda6 plumbed in)
  - submit file: `/ceph/submit/data/user/l/lavezzo/zstuff/Z_COM13_CT18Z_N3p0LL_NewNPs_Lattice_Newvals_Lambda6_Fine/condor.submit`
  - Job count: NPDF=1, NVARS=43, NBINS=11480, NBinsPerJob=205 → **NProcesses = 43 × 56 × 1 = 2408 jobs** (queue=workday, 8h cap, 2GB disk, 1GB mem, **2 CPU/job** per user request)
- 2026-05-20 — **Submitted: cluster 2690810, 2408 jobs** (user request after reviewing local-test results; -j 4 → -j 2 to ease scheduler footprint). All jobs initially idle, queue moving fast (~400 running across user's clusters at submission time).
- 2026-05-21 — **Cluster 2690810 hung pattern**: 2347 jobs produced pkls (97.5%), 61 jobs hung running ~8h+ without producing any output (0-byte .err growth over 60s confirms genuine dead-lock, not slow convergence). Hang pattern:
  - **All 56 var-5 jobs (lambda4=-0.4) hung** on every bin range, including central on-shell bins. Universal failure for that variation. (Misread the local-test result: at central bin 8690 var 5 took 91s/bin which seemed manageable, but production NCPU=2 + bin-range scan triggers a hang per bin range — likely a specific bin within each range hits Cuba's max_iterations limit and the threaded worker stalls there.)
  - **5 of 6 other failures are on the LAST bin range (11275..11480)** — high-Y/high-qT tail bins where physics integrand is harshest. Affected variations: 18 (kappaFO=2), 25 (h_qqV=-1), 35 (b_qqDS=-0.5), 39 (transition_points). Not a TMD/CS NP issue — these are FO/TNP/transition variations failing at the grid corner.
  - **2 var-4 jobs (lambda4=0.0)**: one at bin range 5740..5945 (mid-Q on-shell), one at the tail 11275..11480. Probably the lambda4 in the TMD-PDF kernel struggles with specific bins; not universally broken (54/56 var-4 jobs succeeded).
  - **.err signature for hung jobs**: hundreds of `X-Math Warning max_iterations: Reached maximum of 2 iterations.` lines followed by the suppression message ("max_iterations occurred 10 times: Further warnings of this type will be suppressed"). Pattern repeats forever as new warning types reset suppression.
- 2026-05-21 — **Action taken**: `condor_rm` of the 61 hung jobs (consuming cluster slots indefinitely with no progress). Resubmit file `condor_resubmit.submit` generated by `scetlib-manage-condor-submit.py resubmit` listing the 61 missing (var, bin-range, pdf) tuples. **Not auto-submitted** — same settings would re-hang. User decision needed on strategy: (a) relax `target_precision_rel` from 1e-5 to 1e-3 or so for the retry batch, (b) further tighten Cuba's `max_iterations` or split bins into smaller per-job chunks (so a hang on one bin doesn't stall the rest of the range — but won't help with var 5 since every bin range hangs), (c) drop var 5 from the variations file and handle separately with a custom Cuba config, (d) investigate WHY var-5 systemically fails (might require a source-level look at how Cuba is called for the NP integrand with negative lambda4).

## Open Questions

- Downstream chain: which WRemnants histmaker config will consume the new TheoryCorrection? Does the analysis use `scetlib_dyturbo` (needs an nnlo_sing companion run) or `scetlib_nnlojet` (would need n3lo_sing + NNLOjet, not in scope here)? Default plan: scetlib_dyturbo at 3+0 to match franks-vals-fit's existing scetlib_dyturbo input.
- Job count: MSHT newvals_coarse has ~13 variation entries → 6 new + base ≈ ~22 NP+scale entries; at CT18Z fine NBINS=11480 and NBinsPerJob=205 → ~22 × 56 = ~1232 jobs (smaller than MSHT 4+0 fine since fewer variations than the 50-var msht config). Verify NVARS count once variations file is finalized.
- lambda_4 = -0.4: physical meaning at the SCETlib level. Does tanh argument go through zero / does the model develop a wall? Single-bin local test should catch any blowups before condor submission.

## Decisions

- 2026-05-20 — Patch TMD-side lambda_6 (NP_models.hpp:88), NOT CS-side (Gamma_nu.hpp:102) — reason: user's variation scan {0.016 central, +0.05, 0.1, 0.2, 0.5} matches the TMD hardcoded value 0.016 and is requested explicitly for the TMD side. CS lambda_6_nu = 0.0007 stays at its hardcoded default per user spec (no CS-side variation requested).
- 2026-05-20 — Default the new runtime `lambda6` member to 0.016 (the existing hardcoded value) — reason: keeps all existing tanh_6 configs bit-equivalent without requiring them to add a `lambda6 = 0.016` line. New configs explicitly set lambda6 in their Nonperturbative block.
- 2026-05-20 — Parent study is `franks-vals-fit` — reason: this work directly addresses franks-vals-fit's recorded Next Action ("generate explicit SCETlib templates at the data-preferred Lambda_4"). franks-vals-fit stays `status: running` (multiple parallel studies are OK per user feedback).

## Next Action

1. **Now**: Patch the 6 plumbing points (NP_models.hpp struct member + formula site, py/qT/qT.cpp pybind binding, defaults.conf, variations.py nonp_fields + set_effective_model).
2. Create the new config dir `com13_ct18z_newnps_n3+0ll_lattice_newvals_lambda6_fine/` (clone MSHT newvals_coarse, swap to CT18Z grids + pdf_set + tanh_6 + lambda6=0.016 explicit, write base.conf + inclusive_Z .ini).
3. Write the variations file: layer 6 new entries on top of MSHT newvals_coarse variations.
4. **Pause for user review** of the source diff + the new variations file before rebuilding scetlib or submitting condor jobs.
5. After user signoff: clean rebuild scetlib in lavezzo's tree → local single-bin test (verify central reproduces previous tanh_6 output, lambda_6 scan gives sensible variation) → rebuild runtime tarball → prep_submit → user runs condor_submit.
