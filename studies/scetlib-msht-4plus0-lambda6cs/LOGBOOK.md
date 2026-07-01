---
id: scetlib-msht-4plus0-lambda6cs
title: SCETlib MSHT20an3lo N4+0LL lattice lambda4bugfix lambda6 lambda6cs production → scetlib_nnlojet TheoryCorrection
status: running
question: Produce `scetlib_nnlojet_MSHT20aN3LO_N4p0LL_N3LO_CorrZ.pkl.lz4` (and pdfvars/pdfas siblings) so the WRemnants analysis can validate the N4+0LL method against the current 3+0 baseline.
owner: lavezzo
created: 2026-05-14
updated: 2026-05-21
preferred_run: null
tags: [scetlib, msht20an3lo, n4+0ll, lambda6cs, newvars, theory-correction, nnlojet, dyturbo, rescale]
parent: null
investigates_regions: []
investigates_methods: []
investigates_fits: []
investigates_background_estimates: []
investigates_uncertainties: []
next_action: Wait for 13 active clusters to drain (9 originals + 4 straggler resubmits, monitor_msht tmux). Then for each NP setup (NewVars, lambda6cs): combine SCETlib pieces → make_theory_corr.py -g scetlib_nnlojet (nominal) → make_theory_corr.py -g scetlib_dyturbo (pdfvars + pdfas at matched NP, N3+0LL coarse Y) → make_rescaled_theory_corr.py -c <dyturbo_pdfvars> -r <nnlojet_nominal> → final pdfvars/pdfas TheoryCorrection pkls.
current_hypotheses:
  - The colleague's lambda6 → lambda6cs delta (1-line `np_model_nu = tanh_2 → tanh_6` in the `.ini`) plus a pdf_set swap is sufficient to bootstrap an MSHT20an3lo 4+0 lambda6cs config from his ct18z 4+0 lambda6 config.
  - scetlib_nnlojet recipe (3 inputs: resummed pkl + n3lo_sing pkl + NNLOjet dir) at N4+0LL+N3LO yields a TheoryCorrection drop-in equivalent to existing `scetlib_nnlojet_CT18Z_N4p0LL_N3LO_CorrZ.pkl.lz4`, modulo the PDF-set and lambda6cs changes.
success_criteria:
  - `inclusive_Z_COM13_MSHT20aN3LO_N4+0LL_lattice_lambda4bugfix_lambda6_lambda6cs_fine_combined.pkl` exists and loads.
  - `..._fine_n3lo_sing_combined.pkl` exists and loads (the fixed-order singular piece for NNLOjet matching).
  - `scetlib_nnlojet_MSHT20aN3LO_N4p0LL_N3LO_CorrZ.pkl.lz4` produced and usable by WRemnants downstream consumers.
  - Sanity-check vs the existing CT18Z 3+0 TheoryCorrection: shape should change in PDF-sensible way at N4+0; lambda6cs changes the CS NP profile but not by orders of magnitude.
blockers: []
pending_signoffs: []
---

## Pipeline recipe — full chain to the final TheoryCorrection file

**Goal**: produce `scetlib_nnlojet_MSHT20aN3LO_N4p0LL_N3LO_CorrZ.pkl.lz4` (+ pdfvars + pdfas siblings).

**Why nnlojet (not dyturbo)**: colleague's current 3+0 baseline uses `scetlib_dyturbo` (DYTurbo handles FO+singular subtraction internally, no separate `_n3lo_sing` needed). At **N4+0LL we need NNLOjet** (provides the N3LO fixed-order piece for matching), and the NNLOjet workflow REQUIRES a separate SCETlib `_n3lo_sing` run to subtract the singular piece (otherwise it's double-counted between SCETlib resummed and NNLOjet FO).

### Inputs to `make_theory_corr.py -g scetlib_nnlojet`

| # | What | Status | Path |
|---|------|--------|------|
| 1 | SCETlib resummed `_combined.pkl` (lattice NP variations) | ⏳ in flight | submit dir: `/ceph/submit/data/user/l/lavezzo/zstuff/Z_COM13_MSHT20aN3LO_N4p0LL_NewNPs_Lattice_Lambda4Bugfix_Lambda6_Lambda6cs_Fine/`; will combine into `inclusive_Z_COM13_MSHT20aN3LO_N4+0LL_lattice_lambda4bugfix_lambda6_lambda6cs_fine_combined.pkl` |
| 2 | SCETlib fixed-order singular `_n3lo_sing.pkl` | ✗ **not yet created** | will live at `/work/submit/lavezzo/alphaS/TheoryCorrections/SCETlib/com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine_n3lo_sing/inclusive_Z_COM13_MSHT20aN3LO_N4+0LL_lattice_lambda4bugfix_lambda6_lambda6cs_fine_n3lo_sing_combined.pkl` |
| 3 | NNLOjet outputs dir | ✓ user provided | `/scratch/submit/cms/alphaS/CMS_Z_NNLO_condor_msht20an3lo_as118_20260401_seedfix_clean_v2` |
| -m | gen-distributions hdf5 | ✓ reuse colleague's | `/scratch/submit/cms/areimers/wmass/gendistributions/w_z_gen_dists_maxFiles_m1.hdf5` |

### How to make the `_n3lo_sing` config (deltas from the nominal `_fine` config)

Source: diff of colleague's `com13_ct18z_newnps_n4+0ll_lattice_coarse` vs `_coarse_n3lo_sing`, **modified** per 2026-05-15 discussion: colleague's input that NP enters the singular calculation_piece means we must keep our nominal's NP settings in the singular (NOT use colleague's older `tanh_2` / `delta_lambda2=0.125`). This reduces the recipe to **3 deltas** in the `.ini`, with the `[TNPs]` block in `base.conf` kept (inert with `run_order=none`, but kept for safety / to match the nominal config structure).

- **`inclusive_Z_..._fine_n3lo_sing.ini`** (3 deltas only):
  - `run_order = n4ll` → `run_order = none` (no resummation)
  - add line `calculation_piece = sing` (singular only)
  - `variations_filename = variations_lattice_allvars.conf` → `variations_lattice_fo.conf`
- **`base.conf`**: copy nominal verbatim. Keep the `[TNPs]` block (inert under `run_order=none`, but harmless and matches the nominal).
- **NP block in the `.ini` kept matching nominal**: `np_model_nu = tanh_6`, `np_model = tanh_6`, `delta_lambda2 = 0.0`, all `lambda*_nu` central values inherited from nominal. NP must be consistent between resummed and singular so the FO-singular subtraction in `make_theory_corr.py` is self-consistent.
- **`variations_lattice_fo.conf`**: only 7 variations (FO scale variations `kappaFO`/`kappaf`); copy from colleague's `_coarse_n3lo_sing` dir verbatim — these are PDF-/NP-independent.

### Final command (after both pkls exist)

```bash
# inside WRemnants env (singularity :latest + /opt/venv + setup.sh)
python3 $WREM_BASE/WRemnants/scripts/corrections/make_theory_corr.py \
  -m /scratch/submit/cms/areimers/wmass/gendistributions/w_z_gen_dists_maxFiles_m1.hdf5 \
  -g scetlib_nnlojet --proc z \
  -o /home/submit/lavezzo/alphaS/main/WRemnants/wremnants-data/data/TheoryCorrections/ \
  --axes Y qT \
  -c \
    /work/submit/lavezzo/alphaS/TheoryCorrections/SCETlib/com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine/inclusive_Z_COM13_MSHT20aN3LO_N4+0LL_lattice_lambda4bugfix_lambda6_lambda6cs_fine_combined.pkl \
    /work/submit/lavezzo/alphaS/TheoryCorrections/SCETlib/com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine_n3lo_sing/inclusive_Z_COM13_MSHT20aN3LO_N4+0LL_lattice_lambda4bugfix_lambda6_lambda6cs_fine_n3lo_sing_combined.pkl \
    /scratch/submit/cms/alphaS/CMS_Z_NNLO_condor_msht20an3lo_as118_20260401_seedfix_clean_v2 \
  -p N4p0LLN3LO

# then rename per WRemnants convention
python3 $WREM_BASE/WRemnants/utilities/rename_corr_file.py \
  $WREM_BASE/WRemnants/wremnants-data/data/TheoryCorrections/scetlib_nnlojetN4p0LLN3LOCorrZ.pkl.lz4 \
  $WREM_BASE/WRemnants/wremnants-data/data/TheoryCorrections/scetlib_nnlojet_MSHT20aN3LO_N4p0LL_N3LO_CorrZ.pkl.lz4 -a
```

(`$WREM_BASE` = `/home/submit/lavezzo/alphaS/main` or whatever `setup.sh` resolves it to.)

## Production inventory — SCETlib productions authored by lavezzo

Identified by `(set difference: lavezzo's TheoryCorrections/SCETlib/ dirs) − (areimers's TheoryCorrections/SCETlib/ dirs)`. Anything also present in Arne's tree is NOT lavezzo's (copied/synced from his work) and is omitted here. All paths under `/work/submit/lavezzo/alphaS/TheoryCorrections/SCETlib/` unless noted.

Status tags (set 2026-05-21):
- **finished** — full chain done, final TheoryCorrection pkls on disk, ready for fits
- **deprecated** — superseded by another production OR chain never completed and won't be revived
- **in progress** — actively being computed (jobs running or partial outputs on disk)
- **archival** — admin/validation/backup directories, kept for reference

---

### 1. MSHT20aN3LO, **N4+0LL**, NewVars (new NP, `tanh_2`, theorist's centrals), coarse Y — **STATUS: FINISHED**

The official MSHT20aN3LO production to push forward with.

**N4+0LL pieces (this session):**

| Piece | Config dir tag | `_combined.pkl`? |
|---|---|---|
| nominal | `com13_msht20an3lo_newnps_n4+0ll_lattice_newvals_coarse` | ✓ (14 missing-bin holes at \|Y\|>3.5, outside fiducial) |
| n3lo_sing | `..._newvals_coarse_n3lo_sing` | ✓ |
| (pdfvars scaffold) | `..._newvals_coarse_pdfvars` | not submitted — pdfvars done at N3+0LL instead |
| (pdfas scaffold) | `..._newvals_coarse_pdfas_smallrange` | not submitted — pdfas done at N3+0LL instead |

**Matched-NP N3+0LL pieces (this session, used as dyturbo rescale sources):**

| Piece | Config dir tag | `_combined.pkl`? |
|---|---|---|
| nominal (bonus standalone) | `com13_msht20an3lo_newnps_n3+0ll_lattice_newvals_coarse` | ✓ |
| nnlo_sing | `..._newvals_coarse_nnlo_sing` | ✓ |
| pdfvars (-p 105) | `..._newvals_coarse_pdfvars` | ✓ |
| pdfas_smallrange | `..._newvals_coarse_pdfas_smallrange` | ✓ |

**Final TheoryCorrection pkls** (in `wremnants-data/data/TheoryCorrections/`):
- `scetlib_nnlojet_NewVars_MSHT20aN3LO_N4p0LL_N3LO_CorrZ.pkl.lz4` (nominal)
- `scetlib_nnlojet_NewVars_MSHT20aN3LO_N4p0LL_N3LO_pdfvars_CorrZ.pkl.lz4`
- `scetlib_nnlojet_NewVars_MSHT20aN3LO_N4p0LL_N3LO_pdfas_CorrZ.pkl.lz4`

Intermediate dyturbo refCorrs (used by rescale step; can be cleaned if disk pressure):
- `scetlib_dyturbo_NewVars_MSHT20aN3LO_N3p0LL_N2LO_pdfvars_CorrZ.pkl.lz4`
- `scetlib_dyturbo_NewVars_MSHT20aN3LO_N3p0LL_N2LO_pdfas_CorrZ.pkl.lz4`

---

### 2. MSHT20aN3LO, **N4+0LL**, Lambda6cs (old NP, `tanh_6`), fine Y + N3+0LL coarse — **STATUS: DEPRECATED**

Superseded by NewVars (#1) as the official MSHT20aN3LO production. Kept on disk for cross-checks but not the deliverable.

**N4+0LL fine pieces (prior sessions ~2026-05-14/15):**

| Piece | Config dir tag | `_combined.pkl`? |
|---|---|---|
| nominal | `com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine` | ✓ |
| n3lo_sing | `..._lambda6cs_fine_n3lo_sing` | ✓ |
| pdfvars (-p 105) | `..._lambda6cs_fine_pdfvars` | ✓ |
| pdfas_smallrange | `..._lambda6cs_fine_pdfas_smallrange` | ✓ |

**Matched-NP N3+0LL pieces (this session, used as dyturbo rescale sources):**

| Piece | Config dir tag | `_combined.pkl`? |
|---|---|---|
| nnlo_sing | `com13_msht20an3lo_newnps_n3+0ll_lattice_lambda6cs_coarse_nnlo_sing` | ✓ |
| pdfvars (-p 105) | `..._lambda6cs_coarse_pdfvars` | ✓ |
| pdfas_smallrange | `..._lambda6cs_coarse_pdfas_smallrange` | ✓ |

**Final TheoryCorrection pkls** (produced this session, kept for cross-checks):
- `scetlib_nnlojet_Lambda6cs_MSHT20aN3LO_N4p0LL_N3LO_CorrZ.pkl.lz4` (nominal)
- `scetlib_nnlojet_Lambda6cs_MSHT20aN3LO_N4p0LL_N3LO_pdfvars_CorrZ.pkl.lz4`
- `scetlib_nnlojet_Lambda6cs_MSHT20aN3LO_N4p0LL_N3LO_pdfas_CorrZ.pkl.lz4`

Intermediate dyturbo refCorrs:
- `scetlib_dyturbo_Lambda6cs_MSHT20aN3LO_N3p0LL_N2LO_pdfvars_CorrZ.pkl.lz4`
- `scetlib_dyturbo_Lambda6cs_MSHT20aN3LO_N3p0LL_N2LO_pdfas_CorrZ.pkl.lz4`

---

### 3. CT18Z, **N4+0LL**, Lambda6cs, fine Y — **STATUS: DEPRECATED**

Incomplete: only `nominal` + `pdfvars` were combined in an older session; no `n3lo_sing` ever produced, so no matching to NNLOjet was ever done. Will not be revived.

| Piece | Config dir tag | `_combined.pkl`? |
|---|---|---|
| nominal | `com13_ct18z_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine` | ✓ (older session) |
| pdfvars | `..._lambda6cs_fine_pdfvars` | ✓ (older session) |

---

### 4. CT18Z, **N3+0LL**, franksvals + tanh_6 hybrid, fine Y — **STATUS: DEPRECATED**

Scaffold only, never submitted. Will not be revived.

| Piece | Config dir tag | `_combined.pkl`? |
|---|---|---|
| nominal | `com13_ct18z_newnps_n3+0ll_lattice_lambda4bugfix_franksvals_tanh6_fine` | (scaffold only) |

---

### 5. CT18Z, **N3+0LL**, newvals + lambda6, fine Y — **STATUS: IN PROGRESS**

Active local production: corresponds to the `local_parallel_runner_cuba.py` runner at `/work/submit/lavezzo/alphaS/ct18z_lambda6_retry/`. Independent CT18Z investigation, not part of the MSHT NewVars deliverable.

| Piece | Config dir tag | `_combined.pkl`? |
|---|---|---|
| nominal | `com13_ct18z_newnps_n3+0ll_lattice_newvals_lambda6_fine` | (scaffold + active runner producing pkls) |

---

### 6. CT18Z, N3+0LL, Lambda6cs — validation — **STATUS: ARCHIVAL (finished)**

| Piece | Config dir tag | `_combined.pkl`? |
|---|---|---|
| validation outputs | `_validation_ct18z_n3p0_lambda6cs` | ✓ (validation only, not a TheoryCorrection input) |

---

### 7. Backup directory — **STATUS: ARCHIVAL**

| Dir | Purpose |
|---|---|
| `_backup_n3p0ll_setup` | Files moved aside when N3+0LL config dirs were re-purposed for the NewVars / lambda6cs coarse chains this session |

---

### Storyline across sessions

1. **Prior sessions (~2026-05-14/15)**: built MSHT20aN3LO N4+0LL Lambda6cs fine (now production #2, deprecated). Original goal: stand-alone lambda6cs TheoryCorrection.
2. **This session (2026-05-18 → 2026-05-21)**:
   - 2026-05-18: theorist (Frank) supplied updated NP centrals (`tanh_2` setup) → spun up the NewVars parallel track (production #1). NewVars becomes the official MSHT setup; Lambda6cs becomes the deprecated cross-check.
   - 2026-05-19: built matched-NP N3+0LL coarse dyturbo sources for both NewVars and Lambda6cs (now subsections of #1 and #2).
   - 2026-05-19: applied colleague's `discover_nnlojet_ybins` patch → unblocked the Lambda6cs (fine-Y) nnlojet matching without re-running anything.
   - 2026-05-20–21: completed NewVars N4+0LL nominal (modulo 14 unfilled holes at \|Y\|>3.5 outside fiducial), combined all pieces, ran the full `make_theory_corr.py` (`scetlib_nnlojet` for nominals, `scetlib_dyturbo` for pdfvars/pdfas) + `make_rescaled_theory_corr.py` chain → 6 final + 4 intermediate TheoryCorrection pkls (3 NewVars + 3 Lambda6cs nominals/pdfvars/pdfas).
3. **Separate CT18Z investigations (other sessions, independent of MSHT chain)**: production #3 (deprecated, incomplete), #4 (deprecated, never run), #5 (in progress, active runner).

## Current state checklist

- [x] Configs created: nominal `_fine` + `_fine_pdfvars` (under `/work/submit/lavezzo/alphaS/TheoryCorrections/SCETlib/com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine{,_pdfvars}/`)
- [x] Beamfuncs generated: `MSHT20an3lo_as118_beamfunc` (105 mem, 1.6 GB) AND `MSHT20an3lo_as_smallrange_beamfunc` (7 mem, ~100 MB) under `share/scetlib/beamfunc/`
- [x] scetlib rebuilt clean in lavezzo's tree (no more `/work/submit/areimers/...` paths baked in)
- [x] Runtime tarball: `/ceph/submit/data/user/l/lavezzo/tarballs_scetlib/scetlib_runtime_submit_msht20an3lo.tar.gz` (built with new binaries, MSHT20an3lo_as118 beamfuncs only)
- [⏳] Nominal submission cluster **2639995** (2800 jobs): in flight — 13 still running, ~309 missing-pkl retries pending
- [ ] **Resubmit op + condor_submit the ~309 missing jobs** (auto-staged in tmux `msht_resubmit` — fires `resubmit` when cluster drains)
- [ ] Validate all 2800 pkls present → run `combine` op → produces resummed `_combined.pkl`
- [x] Create `_fine_n3lo_sing` config (3 deltas above) and `variations_lattice_fo.conf` — present at `/work/submit/lavezzo/alphaS/TheoryCorrections/SCETlib/com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine_n3lo_sing/`
- [ ] Submit n3lo_sing (~392 condor jobs, much smaller) → combine → singular `_combined.pkl`
- [ ] Run `make_theory_corr.py -g scetlib_nnlojet --proc z --axes Y qT -p N4p0LLN3LO ...` (full command above) → `.pkl.lz4`
- [ ] Rename to canonical name `scetlib_nnlojet_MSHT20aN3LO_N4p0LL_N3LO_CorrZ.pkl.lz4`
- [ ] Sanity-check vs existing CT18Z 3+0 TheoryCorrection (drop into a fit, compare prefit shapes)
- [ ] **pdfvars + pdfas**: rebuild tarball with both `MSHT20an3lo_as118` + `MSHT20an3lo_as_smallrange` beamfuncs; submit pdfvars `_fine_pdfvars` (~5880 jobs); figure out exact `-p` / `-a` syntax for pdfas (script's behavior with string vs int `-p` entries needs a small local test); submit pdfas; produce `_pdfvars_CorrZ.pkl.lz4` and `_pdfas_CorrZ.pkl.lz4` analogues.



## Status

2026-05-20: scope of this study has broadened from lambda6cs-only to **two parallel NP-setup productions** sharing the same N4+0LL + NNLOjet matching machinery:

1. **lambda6cs** (tanh_6 + Arne's centrals — historical baseline). Nominal + n3lo_sing SCETlib outputs were combined in a prior session at fine Y. Was blocked from `make_theory_corr.py -g scetlib_nnlojet` by a Y-grid mismatch (NNLOjet only publishes coarse ~33-bin Y, SCETlib runs at fine Y). **Colleague's `discover_nnlojet_ybins` patch (now applied to `wremnants/utilities/io_tools/input_tools.py`, +47 -7) auto-discovers NNLOjet's intrinsic edges and unblocks nnlojet matching on the existing fine-Y outputs — no re-run needed.** lambda6cs nominal TheoryCorrection is now producible standalone for nominal-only fits.

2. **NewVars** (theorist's updated tanh_2 + new NP centrals: lambda2=0.4±, lambda4=0.4±, lambda_inf=1, lambda2_nu=0.15±, lambda4_nu=0, lambda_inf_nu=2). Submitted as a parallel coarse-Y production at N4+0LL+N3LO (matching NNLOjet's intrinsic grid from the start).

For pdfvars/pdfas at N4+0LL, the full chain is: nnlojet correction (from N4+0LL resummed + n3lo_sing + NNLOjet) → `make_rescaled_theory_corr.py -c <dyturbo_pdfvars> -r <nnlojet_nominal>` extracts the per-bin PDF/αs variation factor from a **matched-NP N3+0LL dyturbo source** and applies it to the nnlojet nominal. Arne does not have an MSHT20aN3LO N3+0LL lambda6cs chain (only CT18Z), so we are producing **both** NewVars and lambda6cs matched-NP N3+0LL coarse-Y dyturbo chains in this session.

**13 active clusters at 2026-05-20**: 9 originals (NewVars N4+0LL nominal/n3lo_sing + NewVars N3+0LL nominal/nnlo_sing/pdfvars/pdfas + lambda6cs N3+0LL nnlo_sing/pdfvars/pdfas, all coarse Y) + 4 straggler resubmits at `-j 4 -q tomorrow --request-memory-mb 2000 +MaxRuntime=86400` covering the slow-tail procs from the N4+0LL nominal and pdfvars sets. No silent failures: every completed job across the 9 originals exited JobStatus=4 — slow tail is preemption-induced eviction (workday queue 8h walls), not config error.

**Current Next Action**: wait for clusters to drain (monitor_msht tmux, 30-min poll, auto-release held), then run the combine + make_theory_corr + make_rescaled_theory_corr chain per NP setup to produce final pdfvars/pdfas TheoryCorrection pkls. See `## Next Action` below.

## Guiding Question

Produce a SCETlib `_combined.pkl` for MSHT20an3lo_as118 at N4+0LL with lattice variations + lambda4bugfix + lambda6 (TMD) + lambda6cs (CS) so WRemnants can pick it up as a new theory-correction baseline.

## Hypotheses

- The colleague's lambda6 → lambda6cs delta (1-line `np_model_nu = tanh_2 → tanh_6` in the `.ini`) plus a pdf_set swap is sufficient to bootstrap an MSHT20an3lo 4+0 lambda6cs config from his ct18z 4+0 lambda6 config. [confirmed]
- The scetlib_nnlojet recipe (3 inputs: resummed `_combined.pkl` + `_n3lo_sing.pkl` + NNLOjet dir) at N4+0LL+N3LO with `_n3lo_sing` mirroring the nominal's NP settings (rather than colleague's older `_coarse_n3lo_sing` defaults) yields a TheoryCorrection drop-in equivalent to `scetlib_nnlojet_CT18Z_N4p0LL_N3LO_CorrZ.pkl.lz4`, modulo the PDF-set + lambda6cs changes. [active]
- Colleague's `discover_nnlojet_ybins` patch (auto-discover NNLOjet's intrinsic Y edges from disk) is sufficient to unblock `make_theory_corr.py -g scetlib_nnlojet` on the existing lambda6cs fine-Y SCETlib outputs without any re-run. [active]
- For matched-NP pdfvars/pdfas at N4+0LL, a coarse-Y N3+0LL dyturbo chain at the SAME NP centrals as the N4+0LL nominal is sufficient to feed `make_rescaled_theory_corr.py` — no rebin shim needed because the nnlojet correction already lives on NNLOjet's coarse Y after the patch. [active]
- The N3+0LL nominal scetlib_dyturbo cluster is NOT strictly required for the rescale chain — `make_rescaled_theory_corr.py` extracts the central from PDF member 0 inside the refCorr pdfvars file. (Confirmed by reading `make_rescaled_theory_corr.py`: only `-c <refCorr> -r <rescaleCorr>` args.) [confirmed]
- Resubmitting stragglers with `-j 4 -q tomorrow` (4 cores × 24h walls) drains the tail faster than waiting for repeated 8h preemptions in workday queue — SCETlib parallelizes 1 bin per core (enforced by `ncpu <= bins_per_job`), so 4 cores ⇒ ~4× faster per attempt ⇒ much less likely to hit eviction. [active]

## Ideas / Methods Explored

- Started from colleague's `com13_ct18z_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_fine` triple as the closest existing config to the target (4+0, lattice variations, lambda4bugfix, lambda6 on TMD side already enabled).
- Source verification: `Gamma_nu.hpp:98-104` shows `tanh_6` adds a fixed `0.0007 · b⁶ / λ∞_nu` term inside the tanh argument — fully hard-coded, no new free parameter or new variation needed in `variations_lattice_allvars.conf`.
- Generation pattern: local 104-way `xargs -P` driver running `singularity exec` per member with `LD_LIBRARY_PATH=$SCETLIB/build/lib` to find `libscet-pTjet.so`. CWD set to `share/scetlib/beamfunc/` so per-kernel output directories land in the right place.

## Dead-Ends

- (None yet.)

## Findings

- 2026-05-14 — `tanh_6` adds a hard-coded `0.0007·b⁶/λ∞_nu` (CS-side) or analogous (TMD-side) term, no new free parameter — so variations_lattice_allvars.conf is identical between lambda6 and lambda6cs configs. Verified by byte-identical diff of colleague's 3+0 lambda6 vs 3+0 lambda6cs variations files. (evidence: scetlib-cms-newnp-lambda4fix/include/scetlib/qT/Gamma_nu.hpp:98-104)
- 2026-05-14 — The pdfvars and pdfas `.ini` files in colleague's `_pdfvars/` directory are byte-identical; the submit script differentiates pdfas-vs-pdfvars by *filename* + CLI flags (`--pdf-members`, `--alphas`, `--make-vars-per-pdf`), not by `.ini` content. (evidence: md5sum check on `/work/submit/areimers/.../com13_ct18z_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_fine_pdfvars/*.ini`)
- 2026-05-14 — `scetlib-manage-condor-submit.py submit` does NOT call `condor_submit`; it only writes `condor.submit` and prints the command for the user to run. So running `submit` IS the dry-run. (evidence: prod/scetlib_run/scetlib-manage-condor-submit.py:602-606)
- 2026-05-14 — Generated condor.submit (MSHT20an3lo 4+0 lambda6cs nominal): NBINS=11480, NVARS=50, NPDF=1, NBinsPerJob=205 ⇒ 2800 jobs. (evidence: /ceph/submit/data/user/l/lavezzo/zstuff/Z_COM13_MSHT20aN3LO_N4p0LL_NewNPs_Lattice_Lambda4Bugfix_Lambda6_Lambda6cs_Fine/condor.submit)
- 2026-05-14 — `scetlib-manage-condor-submit.py` imports `hist` and requires `/opt/venv/bin/python3`, not the container's default `/usr/bin/python3`. (evidence: `ModuleNotFoundError: No module named 'hist'` when invoking with bare `python3`; fixed by using `/opt/venv/bin/python3`)
- 2026-05-14 — `scetlib-beamfunc-make-grids` writes its output to `<CWD>/<pdf_set>_beamfunc/<kernel>/<file>` (relative to invocation CWD), not to `share/scetlib/beamfunc/` automatically. Wrappers must `cd share/scetlib/beamfunc/` first so output lands in the standard location.
- 2026-05-14 — MSHT20an3lo_as118 has 105 PDF members (1 central + 104 eigenvariations + N3LO K-factors), per LHAPDF .info file. CT18ZNNLO has 59. (evidence: /cvmfs/sft.cern.ch/lcg/external/lhapdfsets/current/MSHT20an3lo_as118/MSHT20an3lo_as118.info `NumMembers: 105`)
- Compile-time path bug: lavezzo's build/ was a verbatim copy of areimers' build/ (byte-identical binaries, CMakeCache showed scetlib_DATA_DIR=/work/submit/areimers/...). On grid workers, singularity only bind-mounted /srv→/work/submit/lavezzo/..., so scetlib looked for beamfunc grids at the baked-in /work/submit/areimers/.../share/scetlib/beamfunc/ path which didn't exist inside the container. Symptom: all 51 kernels emitted 'Could not initialize convolution' on .err and every xsec was exactly 0.0 — the jobs printed 'Done' anyway, so condor reported them complete. First 116/2800 of cluster 2631969 were unusable before catching this. (evidence: condor_out/Job1.err and scetlib_outputs/*.log from cluster 2631969 (now removed))
- Resubmission as cluster 2639995 (replaces killed 2631969). 2800 jobs, all idle initially. submit06.mit.edu schedd had a transient outage right around resubmit time; condor_submit fired successfully (cluster 2639995, 2800 jobs submitted) just before the outage, jobs sat queued during the down period, schedd recovered ~28 min later (21:00:40Z) and matchmaking resumed. By 17:13Z, 17 jobs running and confirmed healthy via .out + .err inspection. (evidence: /work/submit/lavezzo/alphaS/scetlib-cms-newnp-lambda4fix/beamfunc_gen_logs/build_tarball_msht.log; cluster 2639995 in submit06's queue)
- 2026-05-15 — Cluster 2639995 history: 2469 jobs ExitCode=0 (clean .pkl produced), 308 ExitCode=255 (cvmfs `transport endpoint is not connected` failures — singularity image unreachable on bad workers), 1 ExitCode=1 (`Can't find a valid PDF MSHT20an3lo_as118/0` on one worker). All failure modes are pure worker-side flakiness, no systemic config issue. The ~309 missing-pkl jobs need to be resubmitted; expected to mostly succeed on round 2 since they'll land on different workers.
- 2026-05-15 — `find_failed_jobs` in `scetlib-manage-condor-submit.py` checks for per-job `.pkl` files (not `.log`) matching every expected (pdf, var, bin) tuple. The `resubmit` operation generates a new `*resubmit.submit` containing only the missing proc indices; user must `condor_submit` it. After completion, repeat resubmit if any still fail, then `combine`. (evidence: prod/scetlib_run/scetlib-manage-condor-submit.py:205-260)
- 2026-05-15 — TheoryCorrection recipe for N4+0LL+N3LO uses `-g scetlib_nnlojet` (NOT `scetlib_dyturbo` like colleague's current 3+0 work). nnlojet needs **3 inputs**: resummed `_combined.pkl` + fixed-order singular `_n3lo_sing.pkl` + NNLOjet outputs dir. dyturbo doesn't need a separate singular file because DYTurbo handles FO+sing internally. Colleague's `_combined.pkl`s for lambda6cs lack a `_n3lo_sing` companion because his chain is dyturbo-based at 3+0. (evidence: print_command.py on `scetlib_nnlojet_CT18Z_N4p0LL_N3LO_CorrZ.pkl.lz4` showed full make_theory_corr.py invocation with all 3 inputs; colleague's `wremnants-data/data/TheoryCorrections/` directory listing shows only `scetlib_dyturbo_*` files since Feb 2026)
- 2026-05-15 — `_n3lo_sing` config deltas from nominal `_fine` (verified by diff of colleague's `com13_ct18z_newnps_n4+0ll_lattice_coarse` vs `_coarse_n3lo_sing`): drop entire `[TNPs]` block from base.conf; in .ini set `run_order = none`, add `calculation_piece = sing`, swap `variations_filename` to `variations_lattice_fo.conf`, set `delta_lambda2 = 0.125`. The `variations_lattice_fo.conf` has only 7 variations (FO scale variations) → singular run is ~392 condor jobs total, much smaller than the 2800-job nominal.
- 2026-05-15 — Generated `MSHT20an3lo_as_smallrange` beamfuncs (7 members covering αs ∈ {0.114, 0.115, 0.116, 0.117, **0.118 central**, 0.119, 0.120}) for the eventual pdfas leg, ~5 min wall in 2-phase tmux (member 0 alone first to create kernel dirs, then 1..6 in 7-way parallel). All members rc=0. **Gotcha**: first attempt with all 7 in parallel from scratch failed in 1 s — `mkdir` race on kernel subdirs in scetlib-beamfunc-make-grids. 2-phase pattern is required when seeding a new PDF set. (evidence: gen_msht_as_smallrange_beamfunc.log)
- 2026-05-15 — NNLOjet outputs (user-provided): `/scratch/submit/cms/alphaS/CMS_Z_NNLO_condor_msht20an3lo_as118_20260401_seedfix_clean_v2`. gen-distributions hdf5 (reused from colleague): `/scratch/submit/cms/areimers/wmass/gendistributions/w_z_gen_dists_maxFiles_m1.hdf5`.
- 2026-05-15 — `make_theory_corr.py` ALSO requires a `_sing` pkl for the `scetlib_dyturbo` workflow — not just nnlojet. Verified by `print_command.py` on a recent `scetlib_dyturbo_..._N4p0LL_N2LO_CorrZ.pkl.lz4`: 2nd `-c` argument is a `_nnlo_sing_combined.pkl`. The order of the singular file matches the FO generator's order (nnlojet → n3lo_sing for N3LO, dyturbo → nnlo_sing for N2LO), NOT the resummation order. Our case (N4+0LL + NNLOjet + N3LO matching) → need `n3lo_sing`. (evidence: print_command.py output on `/work/submit/areimers/wmass/WRemnants/wremnants-data/data/TheoryCorrections/scetlib_dyturbo_LatticeNPCoarse_CT18Z_N4p0LL_N2LO_CorrZ.pkl.lz4`)
- 2026-05-15 — **NP matters for the singular term too** (per colleague). So `_n3lo_sing` config must mirror the nominal's NP settings (`np_model_nu = tanh_6`, `np_model = tanh_6`, `delta_lambda2 = 0.0`), NOT colleague's older `_coarse_n3lo_sing` defaults (`tanh_2`, `delta_lambda2 = 0.125`). Earlier reasoning that "NP is inert under `run_order=none`" was wrong; safer assumption is that NP enters the singular calculation_piece too. This makes the singular config self-consistent with its paired resummed config — the dangerous thing would be to use different NP in the two halves of the FO-singular subtraction.
- 2026-05-15 — Reusability rules for a `_sing.pkl`: (a) `fixed_order` must match the resummed pair (n3lo here); (b) PDF set must match (we use MSHT20an3lo_as118); (c) **Grids (Q, Y, qT) must match exactly** — colleague's existing `com13_msht20an3lo_newnps_n4+0ll_lattice_coarse_n3lo_sing` has 1.3 MB combined.pkl but uses coarse grids, can NOT be reused against our fine resummed; (d) NP block must match the resummed (per the previous finding); (e) `[TNPs]` block is inert under `run_order=none` and can be dropped OR kept, no numerical effect.
- 2026-05-15 — Created `com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine_n3lo_sing/` config in lavezzo's tree. 3 ini deltas from nominal (`run_order = none`, `+calculation_piece = sing`, `variations_filename = variations_lattice_fo.conf`); NP block + grids + pdf_set inherited from nominal; `[TNPs]` block kept in `base.conf` (inert but safe); `variations_lattice_fo.conf` copied from `/work/submit/areimers/.../com13_ct18z_newnps_n4+0ll_lattice_coarse_n3lo_sing/`. (evidence: `/work/submit/lavezzo/alphaS/TheoryCorrections/SCETlib/com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine_n3lo_sing/`)
- All three remaining batches submitted: pdfvars cluster 2640440 (5880 jobs, NPDF=105 × NBinSteps=56), pdfas cluster 2656146 (336 jobs, NVARS=1 × NBinSteps=56 × 6 alphas pairs). pdfas-smallrange config staged at /work/submit/lavezzo/alphaS/TheoryCorrections/SCETlib/com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine_pdfas_smallrange/ with pdf_set=MSHT20an3lo_as_smallrange in base.conf and -p 1..6 -a 0.114..0.120 paired (skipping member 0 = 0.118 = nominal central). Tarball-both at /ceph/.../scetlib_runtime_submit_msht20an3lo_both.tar.gz (602 MB) bundles as118 + as_smallrange beamfuncs. Local pdfas syntax test against /tmp/lavezzo_pdfas_test confirmed --pdf-member N --alphas X with pdf_set=as_smallrange yields nonzero physical xsec and correctly loads as_smallrange beamfuncs.
- n3lo_sing combine produced /work/submit/lavezzo/alphaS/TheoryCorrections/SCETlib/com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine_n3lo_sing/inclusive_Z_..._n3lo_sing_combined.pkl (3.0 MB, hist shape (2,82,70,7) = Q×Y×qT×FO-variations). Local single-bin test prior to condor submission validated the recipe: had to drop the [TNPs] block from base.conf (scetlib rejects TNPs with run_order=none — 'Theory-nuisance parameters are not available at fixed order' ValueError). With block dropped, n3lo_sing produces nonzero/negative-as-expected singular xsec values. Cluster 2640244 ran 392 jobs in ~1 h wall, all rc=0. (evidence: /work/submit/lavezzo/alphaS/scetlib-cms-newnp-lambda4fix/beamfunc_gen_logs/{local_test_n3lo_sing,combine_n3lo_sing}.log)
- 2026-05-18 — Theorist (Frank) supplied updated NP centrals + uncertainties for a tanh_2/tanh_2 setup that replaces the lambda6cs (tanh_6) family: `lambda2 = 0.4 +0.6 -0.4`, `lambda4 = 0.4 +0.6 -0.4`, `lambda_inf = 1`, `lambda2_nu = 0.15 ± 0.1`, `lambda4_nu = 0`, `lambda_inf_nu = 2`. We tagged this "NewVars" in our config tree. The lambda6cs production becomes the "Old NP values" parallel track. (evidence: theorist email — see `cooper/refs/`)
- 2026-05-19 — Applied colleague's `discover_nnlojet_ybins` patch to `/home/submit/lavezzo/alphaS/main/WRemnants/wremnants/utilities/io_tools/input_tools.py` (+47 -7 lines). New function auto-discovers NNLOjet's intrinsic Y edges from on-disk `.dat` filenames and returns them; the call site in `read_matched_scetlib_nnlojet_hist` no longer demands `hresum.axes["Y"].edges`. Unblocks `make_theory_corr.py -g scetlib_nnlojet` for any SCETlib Y grid (including the existing lambda6cs fine-Y outputs) — no re-run needed for the historical production. (evidence: git diff `wremnants/utilities/io_tools/input_tools.py` in `/home/submit/lavezzo/alphaS/main/WRemnants/`)
- 2026-05-19 — `make_theory_corr.py -g scetlib_nnlojet` outputs are binned on NNLOjet's coarse Y (~33 bins) regardless of input SCETlib Y grid after the patch. Implication: `make_rescaled_theory_corr.py` (which extracts pdfvars/pdfas ratios from a dyturbo refCorr and applies them to the nnlojet rescaleCorr per-bin) needs the dyturbo refCorr on the same coarse Y — otherwise a rebin shim is required. **Decision-relevant**: run matched-NP N3+0LL dyturbo chains on coarse Y from the start rather than fine Y (saves ~2× jobs AND eliminates the rebin shim risk).
- 2026-05-19 — Matched-NP pdfvars/pdfas for an N4+0LL nnlojet TheoryCorrection cannot be assembled from Arne's CT18Z N3+0LL — the dyturbo refCorr's NP centrals must match the nnlojet rescaleCorr's NP. So for MSHT20aN3LO we must produce our own N3+0LL coarse-Y dyturbo chain at each NP setup of interest (NewVars AND lambda6cs).
- 2026-05-19 — `make_rescaled_theory_corr.py` (script in `/home/submit/lavezzo/alphaS/main/WRemnants/scripts/corrections/`) takes only `-c <refCorr>` (dyturbo pdfvars or pdfas pkl) and `-r <rescaleCorr>` (nnlojet nominal pkl); it extracts the per-bin ratio of each PDF/αs variation to PDF member 0 INSIDE the refCorr and multiplies onto the rescaleCorr. No separate "dyturbo nominal" cluster is required for the rescale chain — member 0 of the pdfvars file is the central. (evidence: script source `def main` around `parser.add_argument('-c')` / `parser.add_argument('-r')`)
- 2026-05-19 — Submitted **NewVars** coarse-Y production at N4+0LL + matched N3+0LL chain: 6 clusters covering 2657318 (N4+0LL nominal, 576 jobs) + 2657319 (N4+0LL n3lo_sing, 112 jobs) + 2657358 (N3+0LL nominal — bonus, 576 jobs) + 2657357 (N3+0LL nnlo_sing, 112 jobs) + 2657360 (N3+0LL pdfvars `-p 105`, 1680 jobs) + 2657359 (N3+0LL pdfas `-p 0 3 6 -a 0.118 0.116 0.120`, 48 jobs). All on coarse Y matching NNLOjet (33 bins: -5..-3.5..-3..-0.25..0..3.5..5 with 0.25 step in [-3.5, 3.5]). Configs under `/work/submit/lavezzo/alphaS/TheoryCorrections/SCETlib/com13_msht20an3lo_newnps_n[34]+0ll_lattice_newvals_coarse*/`.
- 2026-05-19 — Submitted **lambda6cs Old-NP** coarse-Y N3+0LL matched-NP dyturbo chain: 3 clusters covering 2657403 (nnlo_sing, 112 jobs) + 2657404 (pdfas_smallrange `-p 0 3 6 -a 0.118 0.116 0.120`, 48 jobs) + 2657405 (pdfvars `-p 105`, 1680 jobs). NP block in each .ini swapped from NewVars (tanh_2) to lambda6cs (tanh_6 / Arne centrals) via a Python in-place edit of the `[Nonperturbative]` section. Skipped a lambda6cs N3+0LL nominal cluster — not needed (see prior finding). Configs under `/work/submit/lavezzo/alphaS/TheoryCorrections/SCETlib/com13_msht20an3lo_newnps_n3+0ll_lattice_lambda6cs_coarse_*/`.
- 2026-05-20 — `scetlib-manage-condor-submit.py` enforces `ncpu <= bins_per_job` because "SCETlib runs 1 bin per core" — meaning `-b 200 -j 4` parallelizes 200 bins across 4 cores per job and finishes each attempt in roughly 1/4 the wall time. (evidence: `prod/scetlib_run/scetlib-manage-condor-submit.py:514-515`)
- 2026-05-20 — `scetlib-manage-condor-submit.py resubmit` scans for missing output files based on the PDF-member pattern implied by the CLI args. For pdfvars clusters, the resubmit invocation MUST include `-p 105` — otherwise the script reports "0 failed" even when ~60 procs have missing pdf1..pdf104 outputs. Same for pdfas (`-p 0 3 6 -a 0.118 0.116 0.120`). For non-PDF clusters (nominal, n3lo_sing) the resubmit call needs no `-p` flag.
- 2026-05-20 — The auto-generated `condor_resubmit.submit` copies the original submit body verbatim, so `NCPU = 1` and `+MaxRuntime = 28800` from the originating submission carry over even if the new CLI specified `-j 4` and a longer queue. Manual sed patch required after generation: `NCPU = 4`, `RequestMemory = 2000`, `+MaxRuntime = 86400`. The `-q tomorrow` flag DOES cleanly override `+JobFlavour`. (evidence: comparing `condor_resubmit.submit` to the original `condor.submit` in `/ceph/submit/data/user/l/lavezzo/zstuff/Z_COM13_MSHT20aN3LO_N4p0LL_NewNPs_Lattice_Newvals_Coarse/`)
- 2026-05-20 — Submitted 4 straggler-resubmit clusters with the patched `condor_resubmit.submit`: 2672783 (113 jobs, covers 2657318 stragglers) + 2672784 (28 jobs, 2657358) + 2672785 (63 jobs, 2657360 pdfvars `-p 105`) + 2672786 (56 jobs, 2657405 pdfvars `-p 105`). All `-j 4 -q tomorrow --request-memory-mb 2000 +MaxRuntime=86400`. Originals (2657318/58/60/405) left running on purpose — if both resubmit and original finish, SCETlib output is deterministic and written atomically so the overwrite is idempotent. Skipped resubmits for clusters with ≤3 jobs left (2657359, 2657404) — not worth the rerun overhead.
- 2026-05-20 — Cross-cluster `condor_history -af JobStatus | uniq -c` confirms **zero silent failures** across the 9 originally-submitted clusters (NewVars + lambda6cs N3+0LL chains): every completed job exited JobStatus=4. Slow tail is preemption-induced eviction (workday queue 8h walls, SCETlib N4+0LL nominal jobs near or above that ceiling) → `NumJobStarts` is 2-3 on stragglers, `RemoteWallClockTime` accumulates across attempts. Not a config bug; the resubmit-with-more-CPUs strategy is pure throughput optimization.

## Open Questions

- After cluster 2639995 (nominal) drains and the resubmit batch lands, will any (bin, var) tuples remain missing after a 2nd round? If so, need a 3rd resubmit cycle before `combine`. Typically transient flake retries succeed, but worth being explicit.
- For the `_fine_n3lo_sing` submission: keep `-b 205` (consistent with nominal) or increase bins-per-job since per-bin compute is cheaper for pure FO-singular? Could reduce job count from ~392 to ~few-dozen, but starting with `-b 205` is safest (no validation surprises).
- pdfas (alternate-αs) command syntax in `scetlib-manage-condor-submit.py`: the script accepts `-p <member-ints> -a <alphas-floats>` paired, but with MSHT20an3lo_as_smallrange the natural choice is to use **members of one alternate set** (since the alphas are members of a single PDF set, not separate sets) — need to verify the script treats numeric `-p` entries as members of the runcard's `pdf_set` vs requiring string entries (PDF set names). Could pre-test with a single-bin local run before committing the condor batch.
- Tarball for n3lo_sing submission: the existing `scetlib_runtime_submit_msht20an3lo.tar.gz` already has the correct rebuilt scetlib + MSHT20an3lo_as118 beamfuncs, **should be directly reusable** for the n3lo_sing run since same PDF / same build. Confirm at submission time.
- At the rescale step (`make_rescaled_theory_corr.py -c <dyturbo_pdfvars> -r <nnlojet_nominal>`), will the coarse-Y dyturbo pkl and the auto-discover-coarse-Y nnlojet pkl agree on axis names AND edges? If there's a subtle Y vs y or off-by-one edge difference, the colleague's earlier rebin shim may still be required. Verify by inspecting both pkls' axes before the rescale call.
- Which "production version" of the TheoryCorrections do we ship in the analysis — NewVars (theorist's currently preferred), lambda6cs (historical baseline), or both for comparison fits? Likely both for a while.
- After the lambda6cs N3+0LL coarse-Y matched-NP chain lands, do we still want a standalone lambda6cs scetlib_dyturbo N3+0LL nominal TheoryCorrection? Skipped intentionally (not needed for the rescale chain) but might be useful as a sanity-check baseline against Arne's CT18Z N3+0LL dyturbo.

## Decisions

- 2026-05-14 — Bootstrap MSHT 4+0 lambda6cs configs from colleague's CT18Z 4+0 lambda6 (+ pdfvars) — reason: closest existing baseline (4+0 fine + lattice + lambda4bugfix + lambda6 on TMD all already set), needing only `np_model_nu` flip and `pdf_set` swap.
- 2026-05-14 — Generate MSHT20an3lo beam-funcs locally (104-way parallel) rather than on condor — reason: one-time cost, simpler than wrapping `scetlib-beamfunc-make-grids` for condor, output dir is shared-mutable across members which is trivial for local threads but awkward across condor jobs.
- 2026-05-14 — Keep CT18Z lambda6cs configs on disk as reference rather than deleting — reason: user request, useful for cross-PDF comparisons later.
- 2026-05-14 — Submitted MSHT20an3lo 4+0 lambda6cs nominal to condor cluster 2631969 (2800 jobs) — User go-ahead after preflight checks passed (x509 proxy 304h, tarball at expected ceph path, condor.submit byte-identical to colleague's wrapper); workday queue with 8h max runtime per job
- 2026-05-14 — Clean-rebuild scetlib in lavezzo's tree (mv build → build_old_<ts>, cmake .. && make -j32 inside singularity); rebuild runtime tarball with --force-remake-runtime-tarball; re-prep submit; resubmit — Hack option (re-bind /srv→/work/submit/areimers/...) would persist forever and break when colleague rebuilds his tree. Clean rebuild was only ~1.5 min wall in the container (CPU not a bottleneck) so the proper fix is cheap. Verified: strings | grep areimers is empty on new binary; CMakeCache now has scetlib_DATA_DIR=/work/submit/lavezzo/...; grid jobs from new cluster 2639995 confirm 'Using beamfunc grids in /work/submit/lavezzo/.../MSHT20an3lo_as118_beamfunc/' with zero 'Could not initialize' errors.
- 2026-05-15 — `_n3lo_sing` recipe: only **3 ini deltas** from nominal (`run_order = none`, add `calculation_piece = sing`, `variations_filename = variations_lattice_fo.conf`); keep `[TNPs]` block in `base.conf`; keep NP block matching nominal (`np_model_nu = tanh_6`, `np_model = tanh_6`, `delta_lambda2 = 0.0`) — **NOT colleague's older defaults**. Reason: per colleague, NP enters the singular calculation_piece, so the singular must use the same NP as the nominal to make the FO-singular subtraction in `make_theory_corr.py` self-consistent. `[TNPs]` block is inert under `run_order=none` but kept for symmetry with nominal (no numerical effect, harmless).
- 2026-05-15 — Run monitor_msht.sh in tmux across all 4 active clusters (2639995, 2640435, 2640440, 2656146); auto-release held jobs with NumHolds<5 brake; auto-exit when queue empty. Lets the run drain unattended overnight. — User stepping away; held-job recovery without manual condor_release; brake prevents endless retry on workers with persistent issues
- 2026-05-18 — pdfas convention corrected per collaborator review: use -p 0 3 6 -a 0.118 0.116 0.120 (central + ±2σ, MUST include member 0/αs=0.118), NOT my initial -p 1..6 -a 0.114..0.120 — make_theory_corr.py needs the central pdfas member to define the baseline against which the ±2σ variations are computed; skipping member 0 thinking it was redundant with nominal pdfvars central was wrong (supersedes: 2026-05-15)
- 2026-05-18 — Open a parallel "NewVars" production at theorist's tanh_2 + updated NP centrals alongside the lambda6cs Old-NP track — reason: theorist supplied new central+uncertainty values intended to supersede the older lambda6cs setup as the analysis-preferred NP model; running both lets us deliver the current best-recommendation TheoryCorrection while keeping the historical baseline available for cross-checks.
- 2026-05-19 — Apply colleague's `discover_nnlojet_ybins` patch to the working WRemnants tree even though we don't strictly need it for the NewVars coarse-Y chain — reason: unblocks the lambda6cs fine-Y nominal TheoryCorrection without re-running anything, and is a no-op for coarse-Y configs (auto-discover returns the same edges that were being passed explicitly).
- 2026-05-19 — Run the matched-NP N3+0LL dyturbo chains (both NewVars and lambda6cs) on coarse Y from the start — reason: nnlojet correction lands on NNLOjet's coarse Y after the patch, so pairing dyturbo on the same grid eliminates the need for a rebin shim at the `make_rescaled_theory_corr.py` step AND saves ~2× condor jobs vs fine Y on the pdfvars-heavy clusters.
- 2026-05-19 — Skip the lambda6cs N3+0LL dyturbo nominal cluster (only submit nnlo_sing + pdfvars + pdfas) — reason: `make_rescaled_theory_corr.py` extracts the central from PDF member 0 inside the refCorr pdfvars file, so no separate dyturbo nominal is required for the rescale chain. (For NewVars we DID keep the bonus N3+0LL nominal cluster running — it'll be a usable standalone dyturbo nominal artifact for cross-checks even though it's not strictly needed for the chain.)
- 2026-05-20 — Resubmit stragglers with `-j 4 -q tomorrow` (4-core / 24h walls) instead of `condor_rm` + replace — reason: SCETlib parallelizes 1 bin per core (enforced by `ncpu <= bins_per_job` in `scetlib-manage-condor-submit.py:514-515`), so 4 cores cuts per-attempt wall to ~1/4 and the 24h `tomorrow`-queue ceiling makes preemption-before-completion much less likely. Originals left running because duplicate finishes overwrite the same output deterministically (zero downside, possible upside if originals beat the resubmits on a slot-shortage day).
- 2026-05-20 — Patch the auto-generated `condor_resubmit.submit` with sed for `NCPU`, `RequestMemory`, `+MaxRuntime` rather than modify `scetlib-manage-condor-submit.py` to honor the new CLI flags — reason: the upstream script's resubmit op copies the original submit body verbatim by design (so resubmit defaults to the same resource shape), and changing that contract is out of scope for this study. Three-line sed in the submit driver is the right local fix.

## Next Action

1. **Now**: wait for 13 active clusters to drain. `monitor_msht` tmux session polls every 30 min, auto-releases held jobs with `NumHolds<5`, exits when queue empty. Active set: 9 originals (2657318/19/57/58/59/60/403/04/05) + 4 resubmits (2672783/84/85/86). Slow tail is preemption-induced eviction, no config error. Resubmits at `-j 4 -q tomorrow` will drain the tail much faster than waiting on the originals.

2. **Combine** each (NP-setup, piece) cluster into a `_combined.pkl` via `scetlib-manage-condor-submit.py ... combine` (one invocation per cluster, in its submit dir). Targets:
   - **NewVars N4+0LL nominal** (combines outputs of 2657318 ∪ 2672783)
   - **NewVars N4+0LL n3lo_sing** (2657319, already drained)
   - **NewVars N3+0LL nominal** (2657358 ∪ 2672784; bonus, optional but useful)
   - **NewVars N3+0LL nnlo_sing** (2657357, already drained)
   - **NewVars N3+0LL pdfvars** (2657360 ∪ 2672785; needs `-p 105`)
   - **NewVars N3+0LL pdfas** (2657359; needs `-p 0 3 6 -a 0.118 0.116 0.120`)
   - **lambda6cs N3+0LL nnlo_sing** (2657403, already drained)
   - **lambda6cs N3+0LL pdfvars** (2657405 ∪ 2672786; needs `-p 105`)
   - **lambda6cs N3+0LL pdfas** (2657404; needs `-p 0 3 6 -a 0.118 0.116 0.120`)
   - (lambda6cs N4+0LL nominal + n3lo_sing already combined from prior session)

3. **Per NP setup, run `make_theory_corr.py -g scetlib_nnlojet`** with the N4+0LL nominal `_combined.pkl` + N4+0LL n3lo_sing `_combined.pkl` + NNLOjet outputs dir → nnlojet nominal TheoryCorrection:
   - For **NewVars**: produces `scetlib_nnlojet_NewVars_MSHT20aN3LO_N4p0LL_N3LO_CorrZ.pkl.lz4` (rename via `utilities/rename_corr_file.py`).
   - For **lambda6cs**: produces the lambda6cs-tagged analogue. Patch from this session unblocks this even though SCETlib outputs are fine-Y (auto-discover lands on NNLOjet coarse Y).

4. **Per NP setup, run `make_theory_corr.py -g scetlib_dyturbo`** with the N3+0LL nominal-via-pdfvars-member-0 + N3+0LL nnlo_sing → dyturbo nominal "_combined" TheoryCorrection pkl, separately for pdfvars (refCorr) and pdfas (refCorr).

5. **Per (NP setup, variation type), run `make_rescaled_theory_corr.py -c <dyturbo_pdfvars_refCorr> -r <nnlojet_nominal_rescaleCorr>`** → final pdfvars TheoryCorrection. Repeat with the pdfas dyturbo refCorr → pdfas TheoryCorrection. End state: 4 final correction files in `wremnants-data/data/TheoryCorrections/`:
   - `scetlib_nnlojet_NewVars_MSHT20aN3LO_N4p0LL_N3LO_pdfvars_CorrZ.pkl.lz4`
   - `scetlib_nnlojet_NewVars_MSHT20aN3LO_N4p0LL_N3LO_pdfas_CorrZ.pkl.lz4`
   - `scetlib_nnlojet_Lambda6cs_MSHT20aN3LO_N4p0LL_N3LO_pdfvars_CorrZ.pkl.lz4` (or analogous naming)
   - `scetlib_nnlojet_Lambda6cs_MSHT20aN3LO_N4p0LL_N3LO_pdfas_CorrZ.pkl.lz4`

6. **Validation**: drop each TheoryCorrection into a histmaker/fitter cycle. Compare prefit shapes between NewVars and lambda6cs (should differ in the CS NP profile region but not by orders of magnitude), and vs Arne's CT18Z N3+0LL dyturbo baseline as a sanity anchor.

7. **If Y-axis mismatch at step 5**: revisit `make_rescaled_theory_corr.py` for a rebin shim (the colleague's earlier workaround). Likely not needed because both pkls live on NNLOjet's coarse Y, but verify by inspecting `.axes` on both pkls before the rescale call.
