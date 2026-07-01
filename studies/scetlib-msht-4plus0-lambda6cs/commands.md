# Reproduction commands — MSHT20an3lo N4+0LL lambda6cs runs

Concrete commands + paths to reproduce the four SCETlib runs that feed `make_theory_corr.py -g scetlib_nnlojet`. Designed to be portable — replace `$LAV`, `$CEPH`, `$TARS` with your own paths.

```bash
# Adjust these to your own checkout
LAV=/work/submit/lavezzo/alphaS                      # your work area
SCETLIB=$LAV/scetlib-cms-newnp-lambda4fix            # scetlib build (paths baked at compile time — see §0)
CFGROOT=$LAV/TheoryCorrections/SCETlib                # config dirs
CEPH=/ceph/submit/data/user/l/lavezzo/zstuff          # condor submit dirs (xrootd-reachable)
TARS=/ceph/submit/data/user/l/lavezzo/tarballs_scetlib # runtime tarballs
IMG=/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:v15
```

---

## §0. scetlib build

The `build/` tree must be built **with your own paths baked in** (`scetlib_DATA_DIR` is a CMake `STRING` baked into the binary at compile time). Copying someone else's `build/` will silently fail on grid workers — every kernel emits "Could not initialize convolution" on `.err` and every xsec is exactly 0.0, while jobs report `ExitCode=0`. Inside the singularity container:

```bash
cd $SCETLIB
rm -rf build && mkdir build && cd build
cmake .. && make -j32
# sanity:
strings bin/scetlib-beamfunc-make-grids | grep areimers   # should be empty
grep scetlib_DATA_DIR CMakeCache.txt                       # should point to your $SCETLIB
```

---

## §1. Generate beam-function tables (one-time per PDF set)

Two PDF sets are needed:
- `MSHT20an3lo_as118` (105 members) — for nominal, n3lo_sing, pdfvars
- `MSHT20an3lo_as_smallrange` (7 members, α_S central + 6 variations) — for pdfas

CT18Z beam-funcs come with scetlib so no generation needed there.

**Important: 2-phase pattern** required when seeding a fresh `_beamfunc/` tree — run member 0 alone first so it creates the 51 kernel subdirs, then parallelize members 1..N. Otherwise the binary's `mkdir` races and most members fail in <1 s.

```bash
# Each member call (inside singularity, run from share/scetlib/beamfunc/ so output lands in place):
cd $SCETLIB/share/scetlib/beamfunc
LD_LIBRARY_PATH=$SCETLIB/build/lib LHAPDF_DATA_PATH=/cvmfs/sft.cern.ch/lcg/external/lhapdfsets/current/:/usr/share/lhapdf/LHAPDF \
  $SCETLIB/build/bin/scetlib-beamfunc-make-grids <PDF_SET_NAME> <member_idx> N3LO qT_quark

# Phase 1: member 0
... <PDF_SET_NAME> 0 N3LO qT_quark
# Phase 2: members 1..N-1 in parallel (xargs -P N)
seq 1 $((NMEMBERS-1)) | xargs -P $((NMEMBERS-1)) -I {} bash -c '... <PDF_SET_NAME> {} N3LO qT_quark'
```

Wall: ~5 min per member at 4 threads. 104-way parallel for MSHT20an3lo_as118 → ~5.5 min total. 7-way for as_smallrange → ~5 min total.

Final layout:
- `$SCETLIB/share/scetlib/beamfunc/MSHT20an3lo_as118_beamfunc/` (1.6 GB, 51 kernels × 105 members)
- `$SCETLIB/share/scetlib/beamfunc/MSHT20an3lo_as_smallrange_beamfunc/` (~110 MB, 51 × 7)

---

## §2. Runtime tarballs

Two tarballs needed:
- `scetlib_runtime_submit_msht20an3lo.tar.gz` — as118 only (nominal, n3lo_sing, pdfvars)
- `scetlib_runtime_submit_msht20an3lo_both.tar.gz` — bundles both as118 + as_smallrange (pdfas)

```bash
# Tarball 1: as118 only (built from the nominal runcard's pdf_set alone)
mkdir -p $TARS
LHAPDF_DATA_PATH=/cvmfs/sft.cern.ch/lcg/external/lhapdfsets/current/:/usr/share/lhapdf/LHAPDF \
PYTHONPATH=$SCETLIB/build/lib LD_LIBRARY_PATH=$SCETLIB/build/lib \
singularity exec --bind /work/,/home/,/cvmfs/,/ceph/ "$IMG" \
  /opt/venv/bin/python3 "$SCETLIB/prod/scetlib_run/scetlib-manage-condor-submit.py" \
    -s "$SCETLIB" \
    -r "$CFGROOT/com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine/inclusive_Z_COM13_MSHT20aN3LO_N4+0LL_lattice_lambda4bugfix_lambda6_lambda6cs_fine.ini" \
    --runtime-tarball "$TARS/scetlib_runtime_submit_msht20an3lo.tar.gz" \
    --make-runtime-tarball-only

# Tarball 2: BOTH PDF sets (-p MSHT20an3lo_as_smallrange forces extra beamfunc bundling)
LHAPDF_DATA_PATH=/cvmfs/sft.cern.ch/lcg/external/lhapdfsets/current/:/usr/share/lhapdf/LHAPDF \
PYTHONPATH=$SCETLIB/build/lib LD_LIBRARY_PATH=$SCETLIB/build/lib \
singularity exec --bind /work/,/home/,/cvmfs/,/ceph/ "$IMG" \
  /opt/venv/bin/python3 "$SCETLIB/prod/scetlib_run/scetlib-manage-condor-submit.py" \
    -s "$SCETLIB" \
    -r "$CFGROOT/com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine/inclusive_Z_COM13_MSHT20aN3LO_N4+0LL_lattice_lambda4bugfix_lambda6_lambda6cs_fine.ini" \
    -p MSHT20an3lo_as_smallrange -a 0.116 \
    --runtime-tarball "$TARS/scetlib_runtime_submit_msht20an3lo_both.tar.gz" \
    --make-runtime-tarball-only --force-remake-runtime-tarball
```

Wall: ~7-12 min each (single-threaded gzip on /ceph).

---

## §3. SCETlib configs

All four config dirs live under `$CFGROOT/` (= `/work/submit/lavezzo/alphaS/TheoryCorrections/SCETlib/`):

### 3a. Nominal (resummed N4+0LL)
```
com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine/
├── base.conf
├── inclusive_Z_COM13_MSHT20aN3LO_N4+0LL_lattice_lambda4bugfix_lambda6_lambda6cs_fine.ini
└── variations_lattice_allvars.conf
```
Key params: `pdf_set = MSHT20an3lo_as118`, `np_model_nu = tanh_6` (lambda6cs CS-side), `np_model = tanh_6` (lambda6 TMD-side), `fixed_order = n3lo`, `run_order = n4ll`.

Bootstrapped from Arne's `com13_ct18z_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_fine/` with **only two changes**: `pdf_set = CT18ZNNLO → MSHT20an3lo_as118` (in `base.conf`), `np_model_nu = tanh_2 → tanh_6` (in `.ini`).

### 3b. Fixed-order singular (for NNLOjet matching)
```
com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine_n3lo_sing/
├── base.conf                       # nominal's base.conf MINUS the [TNPs] block
├── inclusive_Z_..._fine_n3lo_sing.ini
└── variations_lattice_fo.conf      # 7 FO scale variations, copied from Arne's _coarse_n3lo_sing/
```
3 deltas from nominal `.ini`:
- `run_order = n4ll → none`
- add `calculation_piece = sing`
- `variations_filename = variations_lattice_allvars.conf → variations_lattice_fo.conf`

NP block in `.ini` kept matching nominal (`tanh_6`/`tanh_6`/`delta_lambda2=0.0`) — singular calculation_piece sees NP, so it must match its paired resummed run. `[TNPs]` block **must** be dropped from `base.conf` (scetlib hard-rejects TNPs with `run_order=none`).

### 3c. pdfvars (105 PDF eigenvariations of MSHT20an3lo_as118)
```
com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine_pdfvars/
├── base.conf                            # same as nominal
├── inclusive_Z_..._fine_pdfvars.ini     # no variations_filename → NVARS=1
└── inclusive_Z_..._fine_pdfas.ini       # byte-identical to pdfvars.ini, kept for convention; NOT used (pdfas runs from a different dir, see 3d)
```

### 3d. pdfas (α_S variations using MSHT20an3lo_as_smallrange)
```
com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine_pdfas_smallrange/
├── base.conf                             # pdf_set = MSHT20an3lo_as_smallrange (only diff from nominal)
└── inclusive_Z_..._fine_pdfas.ini        # byte-identical to nominal pdfas.ini structurally
```
α_S variations submitted via `-p 0 3 6 -a 0.118 0.116 0.120` (central + ±2σ).

---

## §4. Submit commands

Each is a `submit` operation (writes condor.submit, no queueing) followed by an explicit `condor_submit`. Common flags: `-b 205 -j 4 -q workday --max-runtime 28800 --request-disk 2000000 --request-memory-mb 1000`.

### 4a. Nominal — 2800 jobs (50 vars × 56 bin-chunks × 1 pdf)
```bash
NOM_INI=$CFGROOT/com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine/inclusive_Z_COM13_MSHT20aN3LO_N4+0LL_lattice_lambda4bugfix_lambda6_lambda6cs_fine.ini
NOM_SUB=$CEPH/Z_COM13_MSHT20aN3LO_N4p0LL_NewNPs_Lattice_Lambda4Bugfix_Lambda6_Lambda6cs_Fine

LHAPDF_DATA_PATH=/cvmfs/sft.cern.ch/lcg/external/lhapdfsets/current/:/usr/share/lhapdf/LHAPDF \
PYTHONPATH=$SCETLIB/build/lib LD_LIBRARY_PATH=$SCETLIB/build/lib \
singularity exec --bind /work/,/home/,/cvmfs/,/ceph/ "$IMG" \
  /opt/venv/bin/python3 "$SCETLIB/prod/scetlib_run/scetlib-manage-condor-submit.py" \
    -s "$SCETLIB" -r "$NOM_INI" -b 205 -j 4 -f "$NOM_SUB" \
    -q workday --max-runtime 28800 --request-disk 2000000 --request-memory-mb 1000 \
    --runtime-tarball "$TARS/scetlib_runtime_submit_msht20an3lo.tar.gz" \
    submit
condor_submit "$NOM_SUB/condor.submit"
```

### 4b. n3lo_sing — 392 jobs (7 FO vars × 56 × 1)
```bash
SING_INI=$CFGROOT/com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine_n3lo_sing/inclusive_Z_COM13_MSHT20aN3LO_N4+0LL_lattice_lambda4bugfix_lambda6_lambda6cs_fine_n3lo_sing.ini
SING_SUB=$CEPH/Z_COM13_MSHT20aN3LO_N4p0LL_NewNPs_Lattice_Lambda4Bugfix_Lambda6_Lambda6cs_Fine_n3lo_sing

LHAPDF_DATA_PATH=/cvmfs/sft.cern.ch/lcg/external/lhapdfsets/current/:/usr/share/lhapdf/LHAPDF \
PYTHONPATH=$SCETLIB/build/lib LD_LIBRARY_PATH=$SCETLIB/build/lib \
singularity exec --bind /work/,/home/,/cvmfs/,/ceph/ "$IMG" \
  /opt/venv/bin/python3 "$SCETLIB/prod/scetlib_run/scetlib-manage-condor-submit.py" \
    -s "$SCETLIB" -r "$SING_INI" -b 205 -j 4 -f "$SING_SUB" \
    -q workday --max-runtime 28800 --request-disk 2000000 --request-memory-mb 1000 \
    --runtime-tarball "$TARS/scetlib_runtime_submit_msht20an3lo.tar.gz" \
    submit
condor_submit "$SING_SUB/condor.submit"
```

### 4c. pdfvars — 5880 jobs (1 var × 56 × 105 pdf members)
```bash
VARS_INI=$CFGROOT/com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine_pdfvars/inclusive_Z_COM13_MSHT20aN3LO_N4+0LL_lattice_lambda4bugfix_lambda6_lambda6cs_fine_pdfvars.ini
VARS_SUB=$CEPH/Z_COM13_MSHT20aN3LO_N4p0LL_NewNPs_Lattice_Lambda4Bugfix_Lambda6_Lambda6cs_Fine_pdfvars

LHAPDF_DATA_PATH=/cvmfs/sft.cern.ch/lcg/external/lhapdfsets/current/:/usr/share/lhapdf/LHAPDF \
PYTHONPATH=$SCETLIB/build/lib LD_LIBRARY_PATH=$SCETLIB/build/lib \
singularity exec --bind /work/,/home/,/cvmfs/,/ceph/ "$IMG" \
  /opt/venv/bin/python3 "$SCETLIB/prod/scetlib_run/scetlib-manage-condor-submit.py" \
    -s "$SCETLIB" -r "$VARS_INI" -b 205 -j 4 -p 105 -f "$VARS_SUB" \
    -q workday --max-runtime 28800 --request-disk 2000000 --request-memory-mb 1000 \
    --runtime-tarball "$TARS/scetlib_runtime_submit_msht20an3lo.tar.gz" \
    submit
condor_submit "$VARS_SUB/condor.submit"
```

### 4d. pdfas — 168 jobs (1 var × 56 × 3 paired (pdf,αS))
```bash
PDAS_INI=$CFGROOT/com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine_pdfas_smallrange/inclusive_Z_COM13_MSHT20aN3LO_N4+0LL_lattice_lambda4bugfix_lambda6_lambda6cs_fine_pdfas.ini
PDAS_SUB=$CEPH/Z_COM13_MSHT20aN3LO_N4p0LL_NewNPs_Lattice_Lambda4Bugfix_Lambda6_Lambda6cs_Fine_pdfas_smallrange

LHAPDF_DATA_PATH=/cvmfs/sft.cern.ch/lcg/external/lhapdfsets/current/:/usr/share/lhapdf/LHAPDF \
PYTHONPATH=$SCETLIB/build/lib LD_LIBRARY_PATH=$SCETLIB/build/lib \
singularity exec --bind /work/,/home/,/cvmfs/,/ceph/ "$IMG" \
  /opt/venv/bin/python3 "$SCETLIB/prod/scetlib_run/scetlib-manage-condor-submit.py" \
    -s "$SCETLIB" -r "$PDAS_INI" -b 205 -j 4 \
    -p 0 3 6 -a 0.118 0.116 0.120 \
    -f "$PDAS_SUB" \
    -q workday --max-runtime 28800 --request-disk 2000000 --request-memory-mb 1000 \
    --runtime-tarball "$TARS/scetlib_runtime_submit_msht20an3lo_both.tar.gz" \
    submit
condor_submit "$PDAS_SUB/condor.submit"
```

---

## §5. Recovery (transient cvmfs/xrootd failures)

A few % of jobs hit transient cvmfs/xrootd issues (cvmfs `transport endpoint is not connected`, or `[FATAL] Auth failed` on xrdcp). Pattern: `condor_release` lands them on a new worker, usually clears in 2-3 retries.

After the queue drains, identify remaining holes and resubmit:

```bash
# Replace <RUNCARD>, <SUBMITDIR>, and any -p/-a from the original submit:
LHAPDF_DATA_PATH=/cvmfs/sft.cern.ch/lcg/external/lhapdfsets/current/:/usr/share/lhapdf/LHAPDF \
PYTHONPATH=$SCETLIB/build/lib LD_LIBRARY_PATH=$SCETLIB/build/lib \
singularity exec --bind /work/,/home/,/cvmfs/,/ceph/ "$IMG" \
  /opt/venv/bin/python3 "$SCETLIB/prod/scetlib_run/scetlib-manage-condor-submit.py" \
    -s "$SCETLIB" -r <RUNCARD> -b 205 -j 4 [...same -p/-a/-f as original...] \
    --runtime-tarball <TARBALL> \
    resubmit
condor_submit <SUBMITDIR>/condor_resubmit.submit
```

Repeat until empty. **Crucial: use the SAME `-p`/`-a` flags as the original submit** — otherwise the script's `find_failed_jobs` will check for the wrong (pdf, αs) tuples (see Arne's "submit then resubmit" gotcha).

---

## §6. Combine

Once all per-job `.pkl`s exist, the `combine` op merges them into a single `_combined.pkl`. We point `-o` at the config dir so combined.pkl lands next to base.conf/`.ini` per convention.

```bash
# Example: nominal
LHAPDF_DATA_PATH=/cvmfs/sft.cern.ch/lcg/external/lhapdfsets/current/:/usr/share/lhapdf/LHAPDF \
PYTHONPATH=$SCETLIB/build/lib LD_LIBRARY_PATH=$SCETLIB/build/lib \
singularity exec --bind /work/,/home/,/cvmfs/,/ceph/ "$IMG" \
  /opt/venv/bin/python3 "$SCETLIB/prod/scetlib_run/scetlib-manage-condor-submit.py" \
    -s "$SCETLIB" -r "$NOM_INI" -b 205 -j 4 \
    -f "$NOM_SUB" \
    -o "$CFGROOT/com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine" \
    --runtime-tarball "$TARS/scetlib_runtime_submit_msht20an3lo.tar.gz" \
    combine
```
Same pattern for n3lo_sing, pdfvars (add `-p 105`), pdfas (add `-p 0 3 6 -a 0.118 0.116 0.120`).

---

## §7. Make TheoryCorrection .pkl.lz4

After all four `_combined.pkl` files exist:

```bash
# Inside the wmassdevrolling :latest container (NOT :v15) + WRemnants env
WREM_BASE=/home/submit/lavezzo/alphaS/main      # or wherever your WRemnants checkout lives

python3 $WREM_BASE/WRemnants/scripts/corrections/make_theory_corr.py \
  -m /scratch/submit/cms/areimers/wmass/gendistributions/w_z_gen_dists_maxFiles_m1.hdf5 \
  -g scetlib_nnlojet --proc z \
  -o $WREM_BASE/WRemnants/wremnants-data/data/TheoryCorrections/ \
  --axes Y qT \
  -c \
    $CFGROOT/com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine/inclusive_Z_..._fine_combined.pkl \
    $CFGROOT/com13_msht20an3lo_newnps_n4+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine_n3lo_sing/inclusive_Z_..._fine_n3lo_sing_combined.pkl \
    /scratch/submit/cms/alphaS/CMS_Z_NNLO_condor_msht20an3lo_as118_20260401_seedfix_clean_v2 \
  -p N4p0LLN3LO

python3 $WREM_BASE/WRemnants/utilities/rename_corr_file.py \
  $WREM_BASE/WRemnants/wremnants-data/data/TheoryCorrections/scetlib_nnlojetN4p0LLN3LOCorrZ.pkl.lz4 \
  $WREM_BASE/WRemnants/wremnants-data/data/TheoryCorrections/scetlib_nnlojet_MSHT20aN3LO_N4p0LL_N3LO_CorrZ.pkl.lz4 -a
```

The NNLOjet outputs dir is mine; collaborator should swap to his own NNLOjet output path. Same for `-m` (gen-distributions hdf5).
