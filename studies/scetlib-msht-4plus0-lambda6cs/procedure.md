# MSHT20an3lo N4+0LL lambda6cs SCETlib → TheoryCorrection procedure

**Goal.** Produce `scetlib_nnlojet_MSHT20aN3LO_N4p0LL_N3LO_CorrZ.pkl.lz4` (and `_pdfvars` / `_pdfas` companions) for the WRemnants Z analysis, matching N4+0LL SCETlib resummation to NNLOjet's N3LO fixed-order. Sign-off requested on the choices below.

Builds on Arne Reimers' SCETlib infrastructure (`scetlib-cms-newnp-lambda4fix` + `scetlib-manage-condor-submit.py`). All my paths under `/work/submit/lavezzo/alphaS/`.

---

## 1. Config tree — what I made and why

Three SCETlib configs, all in `/work/submit/lavezzo/alphaS/TheoryCorrections/SCETlib/`:

### 1a. Resummed (nominal) — `com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine/`

Bootstrapped from Arne's `com13_ct18z_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_fine/` (his closest existing 4+0 + lattice + lambda4bugfix + lambda6-on-TMD config). Two changes from his version:

- `base.conf`: `pdf_set = CT18ZNNLO → MSHT20an3lo_as118`
- `.ini`: `np_model_nu = tanh_2 → tanh_6` (turns on the lambda6cs piece on the CS side)

Everything else copied verbatim from Arne's lambda6 fine: grids (fine Y/qT), `[TNPs]` block in `base.conf`, `variations_lattice_allvars.conf` (50 variations: lattice NP eigenvars + FO scale vars + TNPs + transition points), `np_model = tanh_6` (lambda6 on TMD side, already in his config).

Sibling `_pdfvars/` dir has the byte-identical `pdfvars.ini` and `pdfas.ini` files per his convention (the submit script differentiates by `-p`/`-a` flags, not by `.ini` content). pdfas-with-MSHT needed a custom path — see §1c.

### 1b. Fixed-order singular — `com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine_n3lo_sing/`

Needed for the `scetlib_nnlojet` matching workflow (subtract the singular piece from NNLOjet's N3LO FO). Sourced from a diff of Arne's `com13_ct18z_newnps_n4+0ll_lattice_coarse` vs `_coarse_n3lo_sing`. **3 deltas in the `.ini`:**

- `run_order = n4ll → none`
- add `calculation_piece = sing`
- `variations_filename = variations_lattice_allvars.conf → variations_lattice_fo.conf` (only 7 FO scale variations)

**Key choices flagged for sign-off:**

- **NP block matches the nominal `_fine`**, NOT Arne's older `_coarse_n3lo_sing` settings. So I have `np_model_nu = tanh_6`, `np_model = tanh_6`, `delta_lambda2 = 0.0` in the singular's `.ini`, paired with the same `lambda*_nu` central values as the nominal. Rationale: NP can enter the singular calculation, so the singular has to use the same NP as its paired resummed file for the subtraction to be self-consistent.
- **`[TNPs]` block dropped from `base.conf`.** Initially tried keeping it for "safety", but scetlib errors out:
  ```
  ValueError: py::qT::DrellYan: Theory-nuisance parameters are not available at fixed order.
  ```
  With `run_order=none`, the `[TNPs]` block must be removed. Same as Arne's `_coarse_n3lo_sing` recipe.
- `variations_lattice_fo.conf` copied verbatim from Arne's `_coarse_n3lo_sing/` (7 FO scale variations, PDF/NP-independent).

### 1c. pdfas alphas variations — `com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine_pdfas_smallrange/`

For pdfas I need PDF members with **different α_S** values. CT18Z had separate per-α_S PDF sets (e.g. `CT18ZNNLO_as_0116`); MSHT only ships one alternate-α_S set, `MSHT20an3lo_as_smallrange` (7 members covering α_S ∈ {0.114..0.120}, central = 0.118).

So pdfas needs a separate config dir with `pdf_set = MSHT20an3lo_as_smallrange` (vs `MSHT20an3lo_as118` in the nominal/pdfvars). Otherwise byte-identical to `_pdfvars/`.

**Corrected per collaborator review (2026-05-18):** submission uses **`-p 0 3 6 -a 0.118 0.116 0.120`** (central + ±2σ, 3 paired members), NOT my initial `-p 1..6 -a 0.114..0.120`. The central (member 0, αs=0.118) **must** be included — `make_theory_corr.py` needs it to define the pdfas baseline against which the ±2σ variations are computed.

Validated with a local single-job test (5 bins, ~6 min wall): scetlib correctly picked up `as_smallrange_beamfunc/` and produced nonzero physical xsec.

---

## 2. Beam functions

`MSHT20an3lo_*_beamfunc/` didn't exist anywhere when I started, so I generated locally:

- `MSHT20an3lo_as118_beamfunc/` (105 members, 1.6 GB, 51 kernels × 105 .dat files): ~5.5 min wall, 104-way parallel via `xargs -P 104` against `scetlib-beamfunc-make-grids <pdf> <member> N3LO qT_quark`.
- `MSHT20an3lo_as_smallrange_beamfunc/` (7 members, ~100 MB): ~5 min wall, **2-phase**: member 0 alone first (creates 51 kernel subdirs), then members 1..6 in parallel. **Required** because `make-grids` does not handle the `mkdir` race when several members try to seed a fresh `_beamfunc/` tree simultaneously.

Both under `/work/submit/lavezzo/alphaS/scetlib-cms-newnp-lambda4fix/share/scetlib/beamfunc/`.

---

## 3. scetlib build

**Important fix that bit us once.** The `build/` directory I started with had been copied verbatim from Arne's tree (binaries byte-identical, `CMakeCache.txt` showed `scetlib_BINARY_DIR = /work/submit/areimers/...`, `scetlib_DATA_DIR = /work/submit/areimers/.../share/scetlib`). At grid time, singularity bind-mounted `/srv → /work/submit/lavezzo/...`, but the binaries' baked-in `scetlib_DATA_DIR` path doesn't exist inside the container → all 51 kernels emitted `"Could not initialize convolution"` on `.err` and every xsec was exactly 0.0, while the job still printed `"Done"` and condor reported it `ExitCode=0`. First ~116 jobs of the first cluster were silent garbage before I caught it.

Fix: clean rebuild in lavezzo's tree (`mv build → build_old_<ts>; cmake .. && make -j32` inside singularity). 1.5 min wall. Verified after: `strings build/bin/scetlib-beamfunc-make-grids | grep areimers` is empty, `CMakeCache.txt` has `scetlib_DATA_DIR = /work/submit/lavezzo/.../share/scetlib`, grid `.out` files now report `"Using beamfunc grids in /work/submit/lavezzo/.../MSHT20an3lo_as118_beamfunc/"`.

**Flagging for awareness** in case you've seen this pattern before. Cmake's `scetlib_DATA_DIR` is a compile-time `STRING`, so even an `--prefix` install would still bake the path.

---

## 4. Condor runtime tarballs

Two tarballs on `/ceph/.../l/lavezzo/tarballs_scetlib/`:

- `scetlib_runtime_submit_msht20an3lo.tar.gz` (565 MB): `build/lib` + as118 beamfuncs. Used for nominal + pdfvars submissions.
- `scetlib_runtime_submit_msht20an3lo_both.tar.gz` (602 MB): same + as_smallrange beamfuncs. Used for pdfas.

Both built via `scetlib-manage-condor-submit.py ... --make-runtime-tarball-only`, with the runcard's `pdf_set` (plus optional extra `-p <set>` flags) controlling which beamfuncs get bundled. Wall: ~7-12 min single-threaded gzip per tarball.

---

## 5. Condor submissions

Standard pattern: `scetlib-manage-condor-submit.py ... submit` (writes `condor.submit` without queueing) then `condor_submit condor.submit` (queues). All use Arne's wrapper `wrap-scetlib-run-qT-submit.sh` and his `condor_template_submit`.

| Submission | NVARS | NPDF | NBinsPerJob | Total jobs |
|---|---:|---:|---:|---:|
| Nominal | 50 | 1 | 205 | 2800 |
| Singular (n3lo_sing) | 7 | 1 | 205 | 392 |
| pdfvars | 1 | 105 | 205 | 5880 |
| pdfas | 1 | 3 (members 0, 3, 6) | 205 | 168 |

Per-job: 4 cpus, 1 GB RAM, 2 GB disk, max 8 h wall, `workday` flavor, `analysis.lavezzo` accounting group, same `+DESIRED_Sites` list Arne uses.

**Failure mode** I'm chasing: a few percent of jobs hit transient cvmfs/xrootd issues on grid workers (`ExitCode=255: transport endpoint is not connected`, or `[FATAL] Auth failed: No protocols left to try` on xrdcp of the runtime tarball). Pattern: each `condor_release` lands the job on a new worker, usually clears in 2-3 retries. Currently running a monitor that polls every 30 min, releases held jobs with `NumHolds < 5` brake. Once the queue drains, run `scetlib-manage-condor-submit.py ... resubmit` to find any still-missing pkls; condor_submit the generated `condor_resubmit.submit`; repeat until full.

State at time of writing: nominal 2784/2800, pdfvars 4461/5880, pdfas 261/336; second resubmit round of the gaps currently in flight (clusters 2657064/2657067/2657069). Singular run is **complete and combined**.

---

## 6. Combining → TheoryCorrection

Once all four batches are pkl-complete:

```bash
# inside WRemnants env (singularity :latest + /opt/venv + setup.sh)
python3 $WREM_BASE/WRemnants/scripts/corrections/make_theory_corr.py \
  -m /scratch/submit/cms/areimers/wmass/gendistributions/w_z_gen_dists_maxFiles_m1.hdf5 \
  -g scetlib_nnlojet --proc z \
  -o $WREM_BASE/WRemnants/wremnants-data/data/TheoryCorrections/ \
  --axes Y qT \
  -c \
    .../com13_..._fine/inclusive_Z_..._fine_combined.pkl \
    .../com13_..._fine_n3lo_sing/inclusive_Z_..._fine_n3lo_sing_combined.pkl \
    /scratch/submit/cms/alphaS/CMS_Z_NNLO_condor_msht20an3lo_as118_20260401_seedfix_clean_v2 \
  -p N4p0LLN3LO

python3 $WREM_BASE/WRemnants/utilities/rename_corr_file.py \
  $WREM_BASE/WRemnants/wremnants-data/data/TheoryCorrections/scetlib_nnlojetN4p0LLN3LOCorrZ.pkl.lz4 \
  $WREM_BASE/WRemnants/wremnants-data/data/TheoryCorrections/scetlib_nnlojet_MSHT20aN3LO_N4p0LL_N3LO_CorrZ.pkl.lz4 -a
```

(Recipe lifted from `print_command.py` on the existing CT18Z `scetlib_nnlojet_CT18Z_N4p0LL_N3LO_CorrZ.pkl.lz4`. Reusing Arne's `gen-distributions hdf5` and my NNLOjet output dir.)

For `_pdfvars`/`_pdfas` companions: same command, but `-c` points at the pdfvars/pdfas combined pkls instead of the nominal one, and rename to `..._pdfvars_CorrZ.pkl.lz4` / `..._pdfas_CorrZ.pkl.lz4` per convention.

---

## Specific questions for sign-off

1. **MSHT pdfas convention** (§1c): ~~is "use `MSHT20an3lo_as_smallrange` members 1-6 as paired-with-α_S=(0.114..0.120)" the right CMS-side convention~~ — **Resolved (2026-05-18)**: use `-p 0 3 6 -a 0.118 0.116 0.120`. Now in flight (cluster 2657086).
2. **NP in the singular** (§1b): you mentioned NP enters the singular calculation_piece. Does it specifically mean I want `tanh_6 + delta_lambda2=0.0` (matching my nominal) and NOT `tanh_2 + delta_lambda2=0.125` (Arne's older `_coarse_n3lo_sing`)? Anything else NP-side I should mirror?
3. **3-deltas-only `_n3lo_sing` recipe** (§1b): is dropping `[TNPs]` + the 3 ini changes the complete set, or should I additionally strip anything (e.g. `b0_over_bmax_nu`)?
4. **gen-distributions hdf5** (§6): OK to reuse Arne's nominal `w_z_gen_dists_maxFiles_m1.hdf5`, or should I regenerate one specifically targeting MSHT20an3lo?
5. **make_theory_corr.py `--axes Y qT`**: same axes as Arne's existing CT18Z N4p0LL/N3LO command — correct for our 1D ptll-projection use case?
