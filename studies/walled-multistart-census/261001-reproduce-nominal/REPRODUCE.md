# How to reproduce the nominal alpha_s fit (2026-10-01)

**For collaborators.** Everything needed to rebuild the CURRENT nominal fit from scratch:
software versions, the SCETlib builds, the AD cache build with every flag explained, the
card, the fit command, and the reference numbers to check against.

This supersedes [`alphas-scan-discontinuity/260922-reproduce`](../../alphas-scan-discontinuity/260922-reproduce/REPRODUCE.md)
for the nominal. That guide stays correct for what it describes (the unwalled CCKRYLOVWARM fit
on the old `pdf62_corrgrid_260827` cache), and steps 2-4 of this guide reuse its card recipe
unchanged. [What changed](#what-changed-relative-to-the-260922-guide) lists the differences.

Raw markdown of this page:
<https://submit.mit.edu/~lavezzo/alphaS/studies/walled-multistart-census/261001-reproduce-nominal/REPRODUCE.md>

<!-- Every command below was taken from the meta_info, log or script of the file it produced,
     not retyped from memory. Where a command was NOT recorded and had to be reconstructed, it
     says so and lists it under Known gaps. -->

---

## START HERE

> **The nominal fit is a 2D `ptll` x `yll` profile-likelihood fit to real Z->mumu data.** The
> theory prediction is evaluated live inside the minimiser by differentiable SCETlib
> (N3+0LL + NNLO, CT18ZNNLO), read from a precomputed AD cache. Its configuration:
>
> - **card A** plus the **ASWZ lattice Collins-Soper constraint**: lambda4_nu frozen at 0, and a 1D
>   external likelihood term on lambda2_nu = 0.1345 +- 0.0313;
> - the **`pdf62_y35_260921/merged_full_bin0xzero` cache** (|Y| <= 3.5). It was built with
>   scetlib-cms `ca15aec` and read at fit time by `2dd978a`, and it carries the qT-bin-0 cross-term quick patch;
> - the **NPDampingWall** at **margin 0**, `--regularizationStrength 8`.
>
> **Reference fitresult:**
> `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5`.
> Reduced NLL `376.6146329237086`, EDM `3.0e-14`, 3719 parameters. This file is **main fit + Hessian
> only**: it has no saturated tests, no impacts and no postfit hists. See [section 3](#3-reference-fitresults-which-one-to-validate-against-for-what) for which file
> to check what against.
>
> **To refit only, go to [step 5](#step-5--the-fit)**: the card and the cache are on ceph.

**Before you compare any number, three caveats:**

1. **`alphaS` is blinded.** Only differences and uncertainties are meaningful, and this page
   prints no central value. See [section 6](#6-blinding-what-you-will-and-will-not-see).
2. **"Nominal" here means the study-level nominal Luca fixed on 2026-09-30.** It is not the AN's
   documented nominal. AN-25-085 (`uncerts.tex`, Sec. NP model) constrains the CS kernel with three
   eigenvariations of (lambda_inf_nu, lambda2_nu, lambda4_nu). Here the constraint is 1D, on
   lambda2_nu only: our own refit of the ASWZ lattice data at lambda4_nu = 0 and lambda_inf_nu = 2.
3. **A walled fit and an unwalled fit minimise different objectives.** So do two walls with
   different tau or margin. Their NLLs cannot be compared directly.

**Validation status (2026-10-01).** Two steps are checked byte for byte against the production
files, and the step-5 command is checked option by option. The NLL at the stored vector has
**not been re-evaluated yet**: the node had no memory free. See [section 5](#5-validation).

- **Questions:** Luca Lavezzo (lavezzo@mit.edu).
- **Parent study:** [walled-multistart-census](../LOGBOOK.md). This task's record: [LOGBOOK.md](LOGBOOK.md).

---

## 1. Versions

Everything runs in the WMass container:

```
/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
  -> /cvmfs/unpacked.cern.ch/.flat/b4/b4198c00f8d2f7c2ab8049e7598e0cd282c060ed3f7bd0d1bc8d0652cb68c99a
```

`:latest` is a rolling tag. The flat path above is the image every build and fit below used: the
symlink has pointed there since 2026-07-03. Pin that path if `:latest` has moved. Inside it:
Python 3.13.14, TensorFlow 2.21.0, numpy 2.4.6, scipy 1.18.0, h5py 3.14.0, hist 2.10.1,
clang 22.1.6.

| component | where | commit | state at the NOMSTIFF fit |
|---|---|---|---|
| `WRemnants` | `github.com/lucalavezzo/WRemnants`, branch `scetlib-ad-param-model` | **`df3c30f7`** | **dirty: `np_damping_wall.py`**, see below. `df3c30f7` is **not pushed**: the remote branch is at `ae9c6865`. |
| `rabbit` (submodule) | `github.com/WMass/rabbit` | **`2a59246`** (`main-plus-ours`) | clean. **Not pushed**: it is upstream `main` @ `2a64346` (the WMass/rabbit #178 merge) plus one local merge of `4e90d32` ("Record parameters and convergence per likelihood-scan point", `--scanSaveDetail`). |
| `wums` (submodule) | `v0.2.0-3-g29c884d` | `29c884d2` | 1 file modified (`ioutils.py`, `proxy.get()`). Cosmetic for the fit. |
| `narf` (submodule) | | `8ab9de67` | clean |
| `wremnants-data` (submodule) | | `cc04f6e7` | plus the generated correction pkl files (step 2) |
| `scetlib-cms`, **reader** (fit time) | `gitlab.cern.ch:7999/scetlib/contrib/scetlib-cms`, branch `autodiff-sigmaul` | **`2dd978a`** | clean (2 untracked example files). In-tree at `WRemnants/scetlib-cms`, built 2026-09-23 17:05. |
| `scetlib-cms`, **builder** (cache time) | same repo, branch `fix-minnorm-svd-fallback` | **`ca15aec`** (= `2da973d` + MR !13) | clean. Tree at `/work/submit/lavezzo/alphaS/scetlib-ad-2da973d/scetlib-cms`. |
| clad | `github.com/bendavid/clad`, branch `scetlib-fixes` | `d93318b5cf6afe893a3ef208c30ba639357a87fd` | the `bootstrap.sh` pin. Both SCETlib builds reuse `WRemnants/clad-install`. |
| `WRemnantsHelpers` | this repo | `18bda4a` | `workflows/fitterAD.sh` modified (the wall default, below) |

The histmaker and card (steps 3 and 4) are older and ran on `WRemnants` `c838fc63` + a recorded
patch. That is card A, exactly as in the 260922 guide.

### Where the version record comes from, and a trap

rabbit's `meta_info` records the git hash and diff of **wums**, not of rabbit or WRemnants.
NOMSTIFF's `meta_info["git_hash"]` is `29c884d2…`, the wums commit. So the WRemnants, rabbit and
SCETlib commits of the fit come from the `[run]` header the launcher wrote into the fit log:

```
[run] 2026-09-30T14:32:54-04:00 postfix=NOMSTIFF WRemnants=df3c30f7 rabbit=2a59246 scetlib=2dd978a wall_diff_md5=060a9a3669fa635ca2b561b0e3014420
```

The card and histmaker `meta_info` (`meta_info_input`, `meta_info_input/meta_info_input`) do
record WRemnants (`c838fc63`) with its full `git diff`, as described in the 260922 guide.

### The uncommitted wall change, which is now the default

NOMSTIFF ran `df3c30f7` with an uncommitted diff to
`wremnants/postprocessing/scetlib_ad/np_damping_wall.py`: the `margin=` keyword on
`NPDampingMapping`, from T1 of this study. The diff's md5 is `060a9a36…`, as recorded in the
`[run]` line.

On 2026-10-01 a second uncommitted edit made margin 0 the **default**: `NP_DAMPING_MARGIN` went
from 5e-3 to 0, and only the docs changed besides. A matching edit in `workflows/fitterAD.sh`
makes `--wall` mean `--regularizationStrength 8 -r … NPDampingMapping margin=0`. **Neither edit
is committed as of 2026-10-01.**

The step-5 command passes `margin=0` explicitly. So it gives the same fit on either tree, and on
any future commit whatever its default. It also records the margin in the fit's `meta_info`.
Always pass it explicitly. And to reproduce a pre-2026-10-01 walled fit on today's tree, pass
`margin=5e-3`.

### Source patches and bundles (ceph, not on this page)

```
/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261001_reproduce_patches/
  wremnants_np_damping_wall_AS_RUN_BY_NOMSTIFF.patch          md5 060a9a36  (= the [run] line)
  wremnants_np_damping_wall_DEFAULT_MARGIN0_2026-10-01.patch  md5 81d32026  (today's working tree)
  helpers_fitterAD_wall_default.patch
  wums_worktree_at_fit.patch
  wremnants_df3c30f7.bundle            git bundle: scetlib-ad-param-model ^ae9c6865 (the unpushed commits)
  rabbit_2a59246_main-plus-ours.bundle git bundle: main-plus-ours ^2a64346
  rabbit_2a59246_vs_upstream_2a64346.patch
  corrections/  ..._adcorrAV_CorrZ.pkl.lz4 (card A's), ..._adcorrY35_CorrZ.pkl.lz4
  scripts_snapshot/  the study scripts the chain calls that are NOT tracked in git (see Known gaps)
/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260922_reproduce_patches/
  wremnants_worktree_at_histmaker.patch, wremnants_worktree_at_card.patch   (card A, still valid)
```

These are deliberately kept off this web page: `~/public_html` has no authentication, and these
are CMS-internal sources. To use a bundle: `git fetch <bundle> scetlib-ad-param-model:repro`
inside a WRemnants clone that already has `ae9c6865` and WMass `main`.

---

## 2. SCETlib: two builds, and which one may read the cache

**Two libraries are involved, and they are not the same commit.**

- **Builder `ca15aec`** (`fix-minnorm-svd-fallback` = upstream `2da973d` + MR !13, the SVD
  fallback in `rule_min_norm_update`). It built the cache. Upstream `2da973d` alone **cannot**
  complete this build: it aborts 90 min in, on one (member, bin) cell, at the `rmax > 1e-6 * bmax`
  guard (`e185f27`). The failure is deterministic and happens only at `--n-train 9`.
  MR !13 is the fix (details: `scetlib-ad-param-model/260921-cache-2da973d`).
- **Reader `2dd978a`** (`autodiff-sigmaul`, = `ca15aec` + upstream's rewrite of MR !13 as
  SVD-only). It evaluated the cache in every fit. Pairing these two is safe, both by argument and by
  measurement:
  - `kRuleVersion`/`kRuleVersionMin` are 13 and `kFoVersionMin` 14 at both commits.
  - `git diff ca15aec 2dd978a` touches nothing on the read path: no `Bin_rule_opts`,
    `_rule_config_fingerprint`, `load_bin_rules` or `parse_fo`.
  - The changed solver is build-time code. A load never re-solves weights.
  - `backend_check.py` on the cache gives every printed digit identical with both libraries:
    `sum(sigma)` 873.0154, anchor bit-identical, FD 1.93e-08
    (`scetlib-ad-param-model/260921-cache-2da973d/logs/crossread_2dd978a_backend_check.log`).

Library md5s, so a build can be identified from `/proc/<pid>/maps`. Check the **python
extension**: the rule format lives in `DrellYanAD.cpp`, which compiles into
`scetlib_qT.cpython-*.so`, not `libscet-qT.so`.

| build | `scetlib_qT.cpython-313-x86_64-linux-gnu.so` | built |
|---|---|---|
| builder `ca15aec` (`/work/.../scetlib-ad-2da973d/scetlib-cms/build`) | `62c2e930e0984810f6185a6088d76e5d` | 2026-09-21 22:22 |
| reader `2dd978a` (`WRemnants/scetlib-cms/build`) | `e422bcb324ba94033dfa2f483d3efa58` | 2026-09-23 17:06 |

**How they were built.** The recipe is `scetlib-ad-param-model/260921-cache-2da973d/scripts/build_lib.sh`,
with a snapshot in `scripts_snapshot/`. The in-tree reader was built the same way
(`alphas-scan-discontinuity/260923-y35-fit-prep/scripts/build_intree_lib.sh`). Inside the container:

```bash
cmake -S $SRC -B $SRC/build -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER=$(command -v clang) -DCMAKE_CXX_COMPILER=$(command -v clang++) \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -Dscetlib_enable_clad=ON \
  -DCLAD_INSTALL_DIR=$PREFIX/clad-install \
  -Dscetlib_enable_doxygen=OFF -Dscetlib_enable_mathematica=OFF \
  -Dscetlib_DATA_DIR=/home/submit/lavezzo/alphaS/WRemnants/scetlib-cms/share/scetlib
cd $SRC && ./bootstrap.sh -p $PREFIX -j 96
```

- **clad.** clad is a compile-time Clang plugin only: `bootstrap.sh` clones and builds
  `bendavid/clad@d93318b5` unless `clad-install` already exists, and both builds reused it.
  Moving that pin without care is how you get silently wrong gradients.
- **The data directory.** `scetlib_DATA_DIR` is compiled in, and it is the directory the run-time
  reads the beamfunc grids from. It is pinned to the main tree's `share/scetlib` so every build
  reads the identical grid files. Symlink the `*_beamfunc` grid sets into a fresh tree first
  (`build_lib.sh` does). Otherwise `prepare_cache` regenerates 937 MB of byte-identical grids
  (~12 min) into a directory nothing then reads.
- **Cost.** A library rebuild is ~100 s at `-j 96`; it is compile-bound on two translation units.

**Would a current upstream build read this cache?** Upstream `autodiff-sigmaul` was at `f1780aa`
on 2026-10-01, 20 commits past `2dd978a`. Its version constants are unchanged (rules v13, fo v14,
`SCETFOGE`), so it is *expected* to read the cache. **That is not measured.** Only `ca15aec` and
`2dd978a` have been run on it. The 20 commits include three that matter here:
- **MR !14**, the clad comma-declaration fix in the `n_bilin <= 1` fixed-order fallback. This cache
  carries the bilinear block, so the production branch runs, and that branch is bitwise unchanged
  by the fix.
- **MR !16**, the bin-0 fix. It is build-time only.
- **`7988d5e`**, "rules: keep every training point inside the NP models' domain". This one is also
  build-time, but it means a *rebuild* at the tip is a different cache (see step 1).

If you fit with any other build, record which, next to the fit. Use the pairing table in
`knowledge/20_frameworks/scetlib_cache_format_versions_and_pins.md`. Two mutually incompatible
"v10"s exist, and that is the trap to remember.

**The 0.49 % `alphaS` x `pdfEig` Jacobian bug from the 260922 guide does not apply here.** It
was the clad comma-declaration family on the frozen `b66f8de` build. On `2dd978a` with a cache that
carries the quadratic-form block, the production path is clean by construction
(`knowledge/20_frameworks/scetlib_diff_scales_caveats.md`).

**The 260922 guide's HVP zero-seed skip is already in both builds** (upstream since `1d8ccf9`). No
backport is needed.

---

## 3. Reference fitresults: which one to validate against for what

| you want to check | validate against | why |
|---|---|---|
| the minimum: NLL, every parameter, sigma, covariance, EDM, at the nominal settings | **`260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5`** | the nominal objective: tau = 8, margin 0. Main fit + Hessian only. |
| goodness of fit (full saturated test and the `ptll` projection), impacts, postfit hists | **`260928_lattice_y35_fits/fitresults_LATL4ZY35WALLWARM.hdf5`** | the only full-product fit in this configuration. It used the OLD wall (tau = 5, margin 5e-3), so its NLL is a different objective. |
| that you can reproduce LATL4ZY35WALLWARM itself | its own `meta_info["command"]`, plus `margin=5e-3` on the `-r` line | the default margin changed on 2026-10-01 |

Both are under `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/`.

**NOMSTIFF**, read with `rabbit.io_tools.get_fitresult`:

| quantity | value |
|---|---|
| `nllvalreduced` | `376.6146329237086` |
| `edmval` | `3.0046e-14` |
| `ndfsat` | 778 (= 780 bins - 2 free ParamModel parameters) |
| n parameters | 3719 (46 param-model: 44 SCETlib + 2 scale-envelope; plus 3673 card nuisances) |
| first loss of the fit (`Iteration 0`, at the LATL4ZY35WALLWARM vector) | `376.69103432608273` |
| iterations / time | 41 trust-krylov iterations, 4152 s minimise, 562 s Hessian, 5008 s total |
| `lumi` | `-1.462574991 +- 0.931859` |
| `resumTransition2` | `+0.623053594 +- 0.667212` |
| `lambda2_nu` (theta; physical = 0.15 + 0.1 theta) | `-0.857300033 +- 0.229313` (physical 0.06427) |
| `pdfEig0` | `-0.134563569 +- 1.149275` |
| sigma(`alphaS`) in theta units (1 unit = 0.002 in alpha_s) | `0.582304` |
| `alphaS` central value | **not printed** (section 6) |
| the active wall face | L2(\|Y\| = 2.5) = lambda2 + 6.25 delta_lambda2 = -9.2e-7, i.e. ON the TMD small-b boundary; wall term e^16 pen = 7.4e-6 |

scipy reports `success: False`, status 2 ("A bad approximation caused failure to predict
improvement"). That is the normal exit for these fits; certify a minimum by its EDM instead
(`knowledge/20_frameworks/rabbit_minimizer_tolerances.md`).

**LATL4ZY35WALLWARM**, the full-product sibling: `nllvalreduced` `376.6942441689123`, EDM
4.5e-15, the same 3719 parameters.
- Full saturated test: 2ΔNLL = 753.39 on 778 dof, p = 73.0 %.
- `ptll` projection: 80.73 on 39 dof, p = 0.01 %.
- Total time 61591 s (17.1 h). The postfit is 52460 s of that, mostly the saturated projection test.
- Against NOMSTIFF: Δ`alphaS` = -0.012 σ, σ ratio 1.001. **NLLs not comparable**: different wall.

**How close you should expect to land:**

1. **Same cache, same builds, `--noFit` at the stored vector:** bitwise or ~1e-12. **Pending**,
   see section 5.
2. **Refit warm from the same seed** (LATL4ZY35WALLWARM): `Iteration 0` must reproduce
   `376.69103432608273` exactly, since that is a pure function evaluation. The end point should be
   the same minimum at EDM ~1e-14. The minimiser path is not guaranteed bitwise, because multithreaded
   TF reductions are not deterministic by default. Compare at the EDM scale, not to the 16th digit.
3. **Rebuilt cache:** see step 1. A rebuild is not bit-reproducible, so do not expect the NLL to
   the 12th digit.
4. **Seeding matters.** The likelihood has had more than one minimum in every configuration
   studied so far (see `alphas-scan-discontinuity`, `walled-two-minima`). NOMSTIFF is the end of a
   warm-start chain:

   CCWALLWARMPF (old cache) → Y35ZWALLWARM → LATL4ZY35WALLWARM → NOMSTIFF.

   Whether a cold or randomised start lands in the same place is exactly what this study's census
   (T4, `261001-census-nominal`) is measuring. It is running as of 2026-10-01. Until it reports,
   seed from NOMSTIFF or LATL4ZY35WALLWARM, and always say how a fit was seeded when you quote it.

---

## 4. The chain

All commands are shown as they ran. Each assumes the container, with the venv active and
`WRemnantsHelpers/setup.sh` sourced. Steps 1 and 5 also need `SCETLIB_BUILD` set.

```bash
singularity run --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ \
  /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
source /opt/venv/bin/activate
cd WRemnantsHelpers && source setup.sh
```

`WRemnantsHelpers/agent_setup.sh --scetlib current -- <cmd>` does all of this
non-interactively, and sets `SCETLIB_BUILD` to the in-tree `2dd978a` build. `--scetlib <dir>`
takes any other build directory.

### Step 1 — the SCETlib AD cache (`pdf62_y35_260921/merged_full`)

```
/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_y35_260921/merged_full/
    cache.npz   50 320 007 254 B    the UNPATCHED build. Do NOT fit on it (step 1b).
    cache.conf  the resolved runcard: keep it next to the cache; the fit needs it
    build.log   the build's own log, stage by stage
```

**The command.** This is `scetlib-ad-param-model/260921-cache-2da973d/scripts/build_cache.sh <outdir>`,
with nothing passed on its command line. The build log's `=== extra args:` line is empty.
Expanded, it runs:

```bash
taskset -c 0-383 singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ $IMG \
  260921-cache-2da973d/scripts/incontainer.sh python3 -u \
  $WREM_BASE/scripts/rabbit/scetlib_ad/build_scetlib_ad_cache.py \
  --base-conf /ceph/.../scetlib_ad_caches/ntrain_gate/base_1e3.conf \
  --y-edges 0 0.15 0.3 0.5 0.7 0.9 1.1 1.3 1.5 1.8 2 2.5 2.75 3 3.25 3.5 \
  -o /ceph/.../scetlib_ad_caches/pdf62_y35_260921/merged_full --outname cache \
  --threads 384 --pdf-eig 29 --n-train 9
```

`incontainer.sh` points `SCETLIB_SRC`, `SCETLIB_BUILD`, `PYTHONPATH` and `LD_LIBRARY_PATH` at the
**builder** tree `ca15aec`, sets `TF_NUM_INTRAOP_THREADS=4 TF_NUM_INTEROP_THREADS=2` and
`ulimit -s unlimited`, and `cd`s to `WRemnants`. The builder script has not changed since
`1ab951c9` (2026-09-17), so today's copy is the one that ran.

**Every flag, and why it has that value.** The values were read back from `cache.conf` and from
the cache header (section 7 has the reader), not restated.

| flag / setting | value | what it does, and why this value |
|---|---|---|
| `--base-conf` | `ntrain_gate/base_1e3.conf` | The physics runcard. It is a literal merge of the SCETlib reference run behind the shipped corrections (`com13_ct18z_newnps_n3+0ll_lattice_lambda4bugfix_franksvalsvars_fine`), with three edits: `calculation_piece` sing → **matched** (the cache stores both sub-pieces), `fo_order2_analytic = yes` (needed by the NNLO nonsingular), and the variations file dropped. Physics: N3LL resummation (`run_order = n3ll`) + NNLO fixed order, CT18ZNNLO, alpha_s(mZ) 0.118, nf 5, profile transitions [0.2, 0.6, 1.0], muF floor 1.40, NP `tanh_2` for both TMD (lambda2 = lambda4 = 0.4, lambda_inf = 1) and CS (lambda2_nu = 0.15, lambda4_nu = 0, lambda_inf_nu = 2, b0/bmax_nu = 1). **The NP values are the ANCHOR**: the cache is a Taylor-plus-rules object around it. |
| `target_precision_rel` (in the conf) | `1e-3` | The node-ladder target, relative to the matched cross section at each node. Every production cache since 260827 uses it. At 1e-4 the re-adapted answer equals the 1e-3 one to <= 0.01 % (0.08 % in qT 0-0.5) (`knowledge/.../scetlib_ad_cache_validity.md`). |
| `--y-edges` | 15 rows, 0 … 3.5 | Gen \|Y\| bins. These are the builder's default edges with the 3.5-4 and 4-5 rows dropped (Luca, 2026-09-21). Stopping at 3.5 leaves +0.017 % on the corrected inclusive gen total, inside the +0.240 % unattributable xnorm drift. The 4-5 row is not trustworthy: \|Y\| = 4.96 is the kinematic limit at 13 TeV, and DYTurbo edge noise shows there. For the Z dimuon fit the reach buys nothing: reco acceptance bounds it, and truncating at 2.5 moves the reco nominal by <= 4e-6. It buys the gen-total normalisation. |
| `--qt-edges` (default) | 70 bins, 0 … 100 GeV | The shipped corrections' qT grid. |
| `--q-edges` (default) | `[60, 120]`, one bin | The Z mass window the corrections use. |
| ⇒ bins | 15 x 70 x 1 = **1050** | `bins.npy` (1050, 6). The fit's card uses 770 of them, the \|Y\| <= 2.5 rows. The other 280 are evaluated and discarded; the fit log warns about this, and it is harmless. |
| `--pdf-eig 29` | all 29 CT18Z eigenvector pairs | 58 eigenvector members. With `--as-pair auto` (the default) the builder adds `CT18ZNNLO_as_0116/_as_0120`, central 0.118 ± 0.002. That makes **60 PDF members**, despite the directory name "pdf62". There is no muF member pair (`has_muf = 0`): from fo v8 on, the muF response is a polynomial persisted in the fixed-order blob. Header: `n_eig = 29`, `has_as = 1`, `as_step = 0.002`. 53 differentiable parameters = 24 physics + 29 eigenvectors. |
| `--n-train 9` | 9 | Training points for the rule compression. **Kept at 9 to match the 260914 production**, NOT upstream's default `max(9, ceil(1.5 n_params))` = 80. The rule solve grows ~n_train², and 27 would double the cache size and every fit's RSS. Moving off 9 would have to be declared on every number. 9 is also the only value at which unpatched `2da973d` aborts, which is why the builder is `ca15aec`. |
| hard-coded upstream (header `Bin_rule_opts`) | `n_hvp 1`, `seed 4242`, `scale 0.15`, `orthogonal 1`, `zero_absolute 1`, `tol 1e-12`, `resid_target 1e-7`, `max_iter_mult 10` | Set in `examples/matched_ad/prepare_cache.py::build_prologue` and in the C++ defaults, not on the command line. `scale 0.15` means training points at `p_i (1 + 0.15 d_i)`, or `0.15 d_i` absolute for a zero anchor. That is why the cache is exact only near the anchor in NP space (step 5 caveats). |
| explicit training points | 11 | `scetlib_cache.rule_training_points`. They pin the piecewise parameters: the transition points and kappa_F, with their pairwise directions. |
| `--threads 384` + `taskset -c 0-383` | 384 of 768 cores | Luca's standing 50 % node cap, with threads matched to the CPU mask. The expensive member loop is parallel over **nodes of all bins at once**, so `--threads` is the lever and it scales past the bin count. **Do not renice**: an unprivileged renice is irreversible, and a reniced build got ~51 of 600 cores. |
| topology | ONE process, no `--subset`, no merge | At build time the bin merge (`merge_bin_caches`) dropped the fixed-order quadratic-form (cross-term) block silently. `2dd978a` now carries it through a bin merge, but that path has never been validated on a production cache. A single process needs no merge at all. `--subset` is for test caches and crash granularity only. |
| `--outname cache` | | writes `cache.npz` + `cache.conf` |

**Read back from the finished cache** (`cache.npz` zip members, no full load):

```
rules.npy  SCTRULEV + u32 version 13     143 532 855 383 B uncompressed (49.7 GB compressed)
fo.npy     SCETFOGE  (fo v14)              1 054 608 399 B
format 3   n_eig 29   has_as 1   has_muf 0   53 params   bins (1050, 6)
anchor: alphas 0.118, np_eff (lambda_inf 1, lambda2 0.4, lambda4 0.4, delta_lambda2 0),
        np_gnu (lambda_inf 2, lambda2 0.15, lambda4 0, b0_bmax 1), all TNPs 0,
        scale_kappa_R 1, x1 0.2, x2 0.6, x3 1, kappa_F 1, pdf_eig* 0
```

**Cost: 32.9 h wall** at 384 threads, single process, on a quiet node (load 45 at launch), with exit 0:

| stage | wall |
|---|---|
| outer node set + matched cross sections | 23.2 min (sum 873.015 pb) |
| bin rules | 113.4 min (median 378 nodes/bin, worst training residual 5.9e-07) |
| fixed-order grid verify | 48 s |
| 29 eigenvector pairs, resummed | 69.1 min |
| 29 eigenvector pairs, fixed order | 163.7 min |
| **exact quadratic form (FO cross terms)** | **1561.0 min = 26.0 h, 79 %** (V+jet half 84 348 s, singular half 9 041 s) |
| npz write | to 50.3 GB on ceph |

**Never cost a build from a high-qT subset.** The builder's own startup projection (~882 MB,
"~35 min") was low by **57x** on size. The low-qT rows dominate every stage.

The build ran `backend_check.py` and printed `all checks passed`:
- load 516.9 s; anchor re-evaluation bit-identical; analytic vs FD 1.93e-08;
- `max|H - H^T|/max|H|` = 0; the gen-fold sum rule is exact;
- `sum(sigma)` 873.0154. That agrees with 871.4 pb predicted from the shipped correction's rapidity
  profile to 0.2 %.

**A rebuild is NOT bit-reproducible.** `_parallel_run` is a `tbb::parallel_for` whose range
splitting depends on the workers actually available, and each thread keeps private integrator
buffers. So the adaptive node ladder, and the discrete rule choices at the tolerance, change from
run to run. Measured on two independent builds of the same runcard (10-bin test, older library):

| | max / scale |
|---|---|
| sigma at the anchor | 3.1e-05 |
| Jacobian at the anchor | 2.8e-04 |
| sigma, 10 %-displaced point | 1.7e-04 |
| Jacobian, 10 %-displaced point | 3.0e-03 |

Matched bin sums of four builds agreed to 1e-5 relative; the rule structure differed in 9 of 10 bins.
So **a rebuilt cache will not give NOMSTIFF's NLL to the 12th digit**. How much the fitted
`alphaS` moves under a rebuild has never been measured. Use the ceph cache if you want the
reference numbers. (`knowledge/20_frameworks/scetlib_ad_cache_build_parallelism.md`.)

**If you rebuild at a newer SCETlib:**
- At `ca15aec` or `2dd978a` you get the same defect as production, so apply step 1b.
- At the upstream tip (MR !16 merged) the qT-bin-0 cross terms come out correct and step 1b is
  unnecessary. But the cache is then *not* the nominal one: the genuine bin-0 cross terms are
  +2.7e-4 … +4.9e-4 of sigma at the seed's eigenvector displacement, and `7988d5e` changes the
  training set.

### Step 1b — the qT-bin-0 quick patch (`merged_full_bin0xzero`)

**Why.** `scetlib-cms` up to `2dd978a` has a bug in `_fo_bilin_vjet_all`, the V+jet half of the
fixed-order PDF cross terms B_ef. It did not apply the 0.1 GeV nonsingular cutoff that the
per-node evaluator honours. So in the one production bin that has nodes below the cut,
qT [0, 0.5], it added raw, log-divergent V+jet to combinations whose singular half was zero.

How the bug showed:
- Any single eigenvector displaced alone is exact.
- Displacing all 29 scales as t² and drives sigma **negative**: -176 % at \|Y\| < 0.15.
- A warm fit at the old minimum started at loss 1989.95 instead of ~365.5.

The fix is scetlib-cms **MR !16** (`1da6b2e`, now merged upstream). The quick patch zeroes the
damaged block in the existing cache instead of rebuilding
(`alphas-scan-discontinuity/260924-bilin-nons-cut`).

```bash
# (a) zero the cross terms of the 15 qT [0, 0.5] bins in the fo blob (in place, at B's byte offset)
python3 260924-bilin-nons-cut/scripts/zero_bin0_crossterms.py \
  /ceph/.../pdf62_y35_260921/merged_full/cache.npz \
  /ceph/.../pdf62_y35_260921/merged_full_bin0xzero/tmp/fo.npy          # --cut 0.1 (default)
# (b) re-assemble: every other member copied RAW (zip --copy), only fo.npy replaced
bash 260924-bilin-nons-cut/scripts/assemble_cache.sh
```

- **What is zeroed.** In the 15 bins it zeroes 376 650 of 27 244 350 B entries:
  - every off-diagonal entry `d1 != d2 >= 1`, eigenvectors *and* the alphaS direction, in all 3
    muF slots;
  - the kappa_F-shift slots 1 and 2 of `B[0][e]`, `B[e][0]`, `B[e][e]`.
- **What is untouched.** `B[0][0]`, slot 0 of the linear and diagonal entries, the member rows,
  the rules and the node grid. So a one-eigenvector move at kappa_F = 1 is bit-identical to
  `merged_full`.
- **What it costs.** It drops the genuine cross terms in that row: +2.7e-4 … +4.9e-4 of sigma at
  the seed's displacement, growing as c².
- **Time.** (a) takes ~1 min; (b) took 50 min on ceph.

Output, the cache every nominal fit uses:

```
/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_y35_260921/merged_full_bin0xzero/
    cache.npz   50 318 341 563 B   md5 e2e3a706e035ed2efabcbe6ad33afdfc   (master copy)
    cache.conf  md5 a8679bbf0349f7cb64f3bd8430d56158   (identical to merged_full's)
    README.txt, build_of_source_cache.log
```

**Do not fit on the unpatched `merged_full`.**

### Step 1c — a fast-loading copy (optional, but you want it)

The stock loader holds the 143.5 GB rules blob three times. It peaks at **~520 GB** and takes
16-107 min, enough to OOM-kill a job on a shared node. The fix is to extract the rules once to a
flat file next to the cache. The loader uses it only if its CRC sidecar still matches the cache.
After that, a load takes 36-217 s and peaks at ~309 GB (fast path: WRemnants `ae9c6865`,
WMass/WRemnants #715).

```bash
# copy to fast local disk (8-stream dd + md5 check): 260924-bilin-nons-cut/scripts/copy_to_scratch.sh
python3 $WREM_BASE/scripts/rabbit/scetlib_ad/extract_cache_rules.py <cachedir>/cache.npz   # ~20 min
#  -> <cachedir>/cache.rules.bin (143 532 855 255 B) + cache.rules.json (crc32 3957982386)
```

NOMSTIFF read the md5-identical mirror
`/scratch/submit/cms/alphaS/ad_scetlib_caches/pdf62_y35_260921/merged_full_bin0xzero/`, which
carries `cache.rules.bin`. Its log reports "cache loaded in 35.7 s".

### Steps 2-4a — card A (unchanged from the 260922 guide)

The nominal still uses **card A**:

```
/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5
md5 013135fa14aebd3856eeff92cb48a845
```

Its three commands, the theory correction, the histmaker and `setupRabbit.py`, are exactly the
260922 guide's steps 2, 3 and 4. They are re-confirmed today from NOMSTIFF's own `meta_info_input`
chain, and they ran on WRemnants `c838fc63` + the recorded patches. **Card A was not rebuilt
for the new cache.**

Its central theory correction, `…_adcorrAV`, came from the **old** `pdf62_corrgrid_260827` cache
with the frozen `b66f8de` SCETlib. That is the only remaining use of the old snapshot. It was
reused, rather than rebuilt from the y35 cache, because the y35 correction (`…_adcorrY35`)
matches it closely:
- max \|r - 1\| = 2.3e-05 over all 770 cells at \|Y\| <= 2.5 (median 7e-09; none above 1e-3);
- above \|Y\| = 2.5, card A applies no correction (weight 1), and the reco effect of that is
  <= 4e-6;
- `--excludeNuisances` drops every correction variation, because the param model supplies them.

So the card takes only the central weight from the correction (Luca's < 1e-3 rule,
`alphas-scan-discontinuity/260923-y35-fit-prep`, 2026-09-23 18:05). The param model takes its NP
anchor from this correction's runcard ("22 of 53 central values read from its runcard"), and that
runcard equals the y35 cache's anchor: "largest shift from the cache's own anchor: alphaS 0".

Two ways to get card A:
- **Exact card A:** follow the 260922 guide's steps 2-4 at `c838fc63` + its patch. Step 2 needs the
  260827 cache and the `b66f8de` snapshot, or just the correction file itself, which is copied to
  `261001_reproduce_patches/corrections/` (md5 `8cb4ec2b…`).
- **From the y35 cache instead** (never run end to end, so treat it as untested):
  `260923-y35-fit-prep/scripts/c2t_run_y35.sh`, which is `cache_to_theorycorr.py` on
  `merged_full`, name `…_adcorrY35`. Then `histmaker_adcorry35.sh` and `card_adcorry35.sh`. These
  are the card A commands with only the correction name and the paths changed. Expect a card that
  is close to card A but not byte-identical.

### Step 4b — the ASWZ lattice CS constraint (`cardA_latticeASWZ_l4zero_statsyst.hdf5`)

The lattice term is a rabbit **external likelihood term**, written into a copy of card A. Card A
itself is not modified.

```bash
python3 studies/lattice-cs-kernel/260923-lattice-fits/scripts/inject_aswz_cs_prior_theta.py \
  /ceph/.../260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5 \
  -o /ceph/.../260923_lattice_fits/cards/cardA_latticeASWZ_l4zero_statsyst.hdf5 \
  --l4zero          # --syst default (stat+syst); reads ../260923-scetlib-kernel-fit/fit_l4zero.json
```

**This argv was not recorded.** It is reconstructed from the injector's log and its argparse.
Re-running it today gives a file **byte-identical** to the production card: md5
`7664e88509486563bf0250cfb40c8bbf`. It needs no cache load and takes about a minute.

- **The constraint.** Our direct fit of the SCETlib `tanh_2` CS kernel to the ASWZ lattice data
  (arXiv:2402.06725) at lambda4_nu = 0 and lambda_inf_nu = 2, with the lattice-spacing term k1
  profiled: **lambda2_nu = 0.134549**, sigma_stat 0.020071, sigma_syst 0.023984,
  **sigma_tot 0.031275** (study `lattice-cs-kernel`, task `260923-scetlib-kernel-fit`).
- **The systematic.** One shift per group, the larger in the stat metric: n_f matched at mu = 1
  (-0.0131), k2 only (-0.0177), and drop b_T < 0.2 fm (-0.0095). All three are negative, so the
  systematic is one-sided.
- **Not the 2D Gaussian conditional.** The conditional of the 2D (lambda2_nu, lambda4_nu) fit at
  lambda4_nu = 0 gives 0.108, which is biased low.
- **In the model's theta** (lambda2_nu = 0.15 + 0.1 theta): mu = -0.154506, sigma = 0.312747,
  H = 10.2238, g = 1.5796, const 0.122033. rabbit reads back its own const and matches it.
- **Why it is an external term, and why `prior_sigmas=lambda2_nu=nan`.** The term *replaces*
  the model's default N(0, 1) prior on lambda2_nu, so step 5 switches that prior off. It is only
  ~3x the default prior's precision.
- **lambda4_nu is frozen at its anchor, 0.** It is left out of `fit_params`, so it never reaches
  rabbit. The constraint is valid only on that slice, and the injector refuses a card whose
  lambda4_nu anchor is not 0.

### Step 5 — the fit

`scripts/step5_fit.sh` in this directory is the NOMSTIFF command with the paths made variables:

```bash
CARD=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260923_lattice_fits/cards/cardA_latticeASWZ_l4zero_statsyst.hdf5
CACHE=/scratch/submit/cms/alphaS/ad_scetlib_caches/pdf62_y35_260921/merged_full_bin0xzero   # or the ceph master
WALL=wremnants.postprocessing.scetlib_ad.np_damping_wall
FIT_PARAMS=alphaS,lambda2,lambda4,delta_lambda2,lambda2_nu,resumTNP_gamma_cusp,resumTNP_gamma_mu_q,resumTNP_gamma_nu,resumTNP_s,resumTNP_b_qqV,resumTNP_b_qqbarV,resumTNP_b_qqS,resumTNP_b_qg,resumTNP_h_qqV,resumTransition2,pdfEig0,pdfEig1,pdfEig2,pdfEig3,pdfEig4,pdfEig5,pdfEig6,pdfEig7,pdfEig8,pdfEig9,pdfEig10,pdfEig11,pdfEig12,pdfEig13,pdfEig14,pdfEig15,pdfEig16,pdfEig17,pdfEig18,pdfEig19,pdfEig20,pdfEig21,pdfEig22,pdfEig23,pdfEig24,pdfEig25,pdfEig26,pdfEig27,pdfEig28

rabbit_fit.py $CARD --jitCompile off -o $OUT -t 0 --postfix NOMSTIFF \
  --regularizationStrength 8 -r $WALL.NPDampingWall $WALL.NPDampingMapping margin=0 \
  --snapshotFile $OUT/snapshot_fitresults_NOMSTIFF.hdf5 --snapshotInterval 0.25 \
  --paramModel wremnants.postprocessing.scetlib_ad.SCETlibADParamModel \
    cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128 \
    fit_params=$FIT_PARAMS prior_sigmas=lambda2_nu=nan \
  -v 4 --earlyStopping 100 \
  --externalPostfit /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260928_lattice_y35_fits/fitresults_LATL4ZY35WALLWARM.hdf5
```

Run it as
`./agent_setup.sh --scetlib current -- studies/walled-multistart-census/261001-reproduce-nominal/scripts/step5_fit.sh <outdir> <postfix> <seed>`.
`scripts/check_step5_argv.py` parses this command and NOMSTIFF's stored `meta_info["command"]`
with rabbit_fit's own parser. **Every option is identical** except the run-local `-o`,
`--postfix` and `--snapshotFile`.

**Every flag, and why:**

| flag | why |
|---|---|
| `-t 0` | the real-data fit, and therefore **blinded** (section 6). `-t -1` is Asimov. |
| `--jitCompile off` | **mandatory.** The param model reaches SCETlib through a `tf.py_function`, which XLA cannot lower. |
| `--regularizationStrength 8` | the wall stiffness tau: the penalty is e^{2 tau} relu²(margin - coeff) = 8.9e6 relu². At tau = 8 the overshoot past a face is g/(2e^16) ~ 1e-6. Measured: 9.2e-7 in the coefficient and 7.4e-6 in the NLL at NOMSTIFF, so it is a hard constraint for every practical purpose. |
| `-r …NPDampingWall …NPDampingMapping margin=0` | the NP damping wall: a rabbit Regularizer that walls the exact damping boundary of the CS and TMD NP functions. It reads the NP forms and \|Y\| = 2.5 from the card. Here it arms **5 of 8 conditions**: lambda2_nu >= 0, L2 >= 0 at \|Y\| = 0 and 2.5, and the TMD large-b condition at \|Y\| = 0 and 2.5. The three conditions on held lambdas (lambda_inf, lambda_inf_nu, lambda4_nu) are satisfied and dropped as constant. `margin=` must come **after** the mapping class. It is read at construction, so `fitterAD.sh -f` cannot pass it. **Why the wall at all:** an AD cache is exact only for lambda2_nu >= 0. Its nodes are adapted at the anchor, and it is wrong by percent to tens of percent for lambda2_nu < 0. Unwalled fits on these caches are therefore not trusted (Luca, 2026-09-27). **Why margin 0** (since 2026-10-01): the old 5e-3 cushion hid faces the data push against. Removing it moves the nominal `alphaS` by +0.012 σ and σ by -0.1 % (`260930-stiff-wall-refits`). |
| `--snapshotFile … --snapshotInterval 0.25` | **not optional.** rabbit's SIGTERM handler is a no-op without a filename, and these fits run for hours. It also makes a fit resumable: `--externalPostfit <snapshot>`. |
| `--paramModel …SCETlibADParamModel cache= conf=` | the live SCETlib prediction: sigma_reco = R · sigma_gen(theta), where R is the response matrix stored in the card. `conf` must be the cache's own `cache.conf`. |
| `threads=128` | SCETlib evaluation threads. Each fit process is ~1613 OS threads in total (XLA ignores thread caps), against a 32768 per-user ceiling. |
| `fit_params=<44 names>` | the SCETlib parameters rabbit floats: alphaS (the POI); lambda2, lambda4, delta_lambda2, lambda2_nu; the 9 resummation TNPs; resumTransition2; pdfEig0-28. That is the model's default fitted set **minus lambda4_nu**, which is held at its anchor 0. Also held, by the model default: lambda_inf, lambda_inf_nu, b0/bmax_nu, the outer transition points, b_qqDS (inert for the Z), and the profile scales muR/muF. The scales are replaced by a frozen **3-point (mu_R-only) scale envelope**, `resumFOScaleEnvSymAvg/Diff`, for qT >= 20 GeV. That is the model default since 2026-09-11 ("copy the datacard one": the production card's `resumFOScaleZ` is mu_R-only). The AN text describes a 7-point (mu_R, mu_F) envelope, and the two differ: measured on this card, the 7-point one is +45 % in `SymAvg`. So rabbit sees 44 + 2 = 46 ParamModel parameters. |
| `prior_sigmas=lambda2_nu=nan` | switches off the default N(0, 1) prior on lambda2_nu, because the external lattice term in the card replaces it (step 4b). Every other model parameter keeps its unit Gaussian. alphaS is free. |
| `-v 4` | debug logging: the per-iteration loss and `[timing]` lines. |
| `--earlyStopping 100` | stop after 100 iterations without improvement. **Never < 20**: that silently aborts trust-krylov (`rabbit_minimizer_tolerances.md`). |
| `--externalPostfit <seed>` | **warm start**, from the full parameter vector of the seed fit. Never seed lambda-only. See section 3, caveat 4. |

For the **full product** (saturated tests, impacts, postfit hists), add
`-m Project ch0 ptll --computeSaturatedProjectionTests --computeHistErrors --doImpacts --globalImpacts --globalImpactsDisableJVP --saveHists`.
`workflows/fitterAD.sh <card> -c <cachedir> --wall -f "threads=128 fit_params=… prior_sigmas=lambda2_nu=nan -v 4 --earlyStopping 100 --externalPostfit <seed>"`
does exactly that. It adds about 15 h of postfit, and **`--globalImpactsDisableJVP` is then
required**: the JVP route silently returns a *zero* tangent through the `tf.py_function`, and the
binByBinStat global impact then comes out garbage. No full-product reference exists yet at
tau = 8, margin 0.

**Resources.** Runs on CPU.
- Steady RSS ~327 GB per fit. The load peaks ~309 GB with `cache.rules.bin`, and ~520 GB without.
- Gate concurrent loads through `studies/alphas-scan-discontinuity/scripts/mem_gate.sh`
  (`knowledge/10_environment/big_memory_jobs.md`).
- Keep to fewer than ~18-20 concurrent TF processes per user, or `pthread_create` fails with EAGAIN.

**Where the fit is valid.** The cache is exact for lambda2_nu >= 0, and the wall keeps the fit
there. At NOMSTIFF, lambda2_nu = 0.064 (physical), well inside. Separately, NOMSTIFF's lambda2_nu
sits 2.2 σ below the lattice value ((0.1345 - 0.0643)/0.0313). That is the known `ptll`-shape tension (study
`lattice-cs-kernel`), not a card error.

---

## 5. Validation

| check | how | result |
|---|---|---|
| step-5 command = NOMSTIFF's | `scripts/check_step5_argv.py`, which compares both through rabbit_fit's parser | **PASS**: identical except the run-local options (`logs/check_step5_argv.log`) |
| step 4b reproduces the production card | re-ran the injector to a scratch file | **PASS**: md5 `7664e885…`, byte-identical (`logs/reinject_l4zero.log`) |
| step 1b reproduces the production patch | re-ran `zero_bin0_crossterms.py` on `merged_full` | **PASS**: `fo.npy` CRC32 2635307314 = the `bin0xzero` member; all other members CRC-identical to `merged_full` (`logs/repatch_bin0xzero.log`) |
| step-5 fitter at NOMSTIFF's stored vector | `scripts/validate_step5.sh`: two gated `--noFit --noEDM` loads, at NOMSTIFF's vector and at its seed | **PENDING.** Memory: three census fits at ~327 GB each left 385 GB. One load needs ~310 GB + the gate's 150 GB margin. |

The pending check asserts the following, to 1e-10:
- reduced NLL at NOMSTIFF's vector = `376.6146329237086`;
- reduced NLL at the LATL4ZY35WALLWARM vector = `376.69103432608273`, NOMSTIFF's `Iteration 0`.

`--noHessian` must NOT be added: rabbit then allocates no covariance, and `load_fitresult` refuses
a seed that carries one. Run the check when the census frees memory:
`setsid nohup scripts/validate_step5.sh > logs/validate_step5.out 2>&1 &`. It runs one load after
the other, logs to `/ceph/.../261001_reproduce_validation/`, and symlinks the logs into `logs/`.

An earlier check covers part of this. T1 (`260930-wall-margin-keyword`) rebuilt this fitter from
LATL4ZY35WALLWARM's `meta_info` command on the same trees. At that vector it got the margin-0,
tau-8 loss `376.69103432608273`, equal to NOMSTIFF's `Iteration 0` to all digits. It also got the
stored tau-5 loss to 0.0. That is the seed-point half of the pending check, done through rabbit's
internals rather than through this script.

---

## 6. Blinding: what you will and will not see

- **What is blinded:** only the POI `alphaS`, in every `-t 0` fit and in every
  `--toysDataMode observed` toy. The NP lambdas, PDF eigenvectors, TNPs and card nuisances are
  printed in their true frame.
- **How.** The offset is additive in the POI's fit unit, theta_αs = (alpha_s - 0.118)/0.002. The
  draw is N(0, 5) with a seed of `sha256("alphaS" + "_data")`, so the smearing is ±0.010 in
  alpha_s (`rabbit/blinding.py`).
  - The `_data` suffix is added when **every** `data_obs` bin of the card is an integer.
    Real data is; card A is integral in 780 of 780 bins. An Asimov or MC card, which is not
    integral, gets a different offset, so blinded values from the two families are never
    comparable.
  - The offset lives only in the difference between rabbit's internal `x` and the physical
    parameters, and it is never written into the fitresult.
- **What you will see.** `alphaS ± σ` in the fitresult and logs is the BLINDED value. σ is real.
  The difference of two fits' blinded values is real, but only within one family: same card
  family, same POI name, integer data.
- **What you will not see.** The absolute alpha_s.
- **What this page does not print.** The blinded central value: the offset is a deterministic
  function of public code, so a blinded value on an unauthenticated page is effectively an
  unblinded one. To check a reproduction, compare your blinded `alphaS` to the reference file's
  blinded `alphaS` **by difference**, in code, without printing either.

---

## 7. Known traps, in one list

1. **Fit only on `merged_full_bin0xzero`**, never on the unpatched `merged_full`.
2. **The cache is only exact for lambda2_nu >= 0.** Never trust an unwalled fit on it.
3. **Pass `margin=` explicitly.** The default changed on 2026-10-01, in a still-uncommitted diff.
4. **Builder and reader are different commits**, `ca15aec` and `2dd978a`. Unpatched `2da973d`
   cannot build this cache at all.
5. **Cache rebuilds are not bit-reproducible** (step 1). A tip rebuild is a different cache: it
   has MR !16 and the training-point change.
6. **rabbit `meta_info` records wums's git state**, not rabbit's or WRemnants'. Keep the launcher's
   `[run]` header, or write the commits down yourself.
7. **Multiple minima.** Seed from the reference, and say how a fit was seeded.
8. **`build_scetlib_ad_cache.py --help` crashes** (`ValueError: unsupported format character 'C'`).
   The cause is the bare `%` in the `--fork-members` help ("99% CPU"). Read the argparse block in
   the source instead.
9. **The stock cache loader peaks at ~520 GB.** Extract `cache.rules.bin` first (step 1c).
10. **Do not export `TF_NUM_*_THREADS` for fits.** It is right for cache builds, wrong for fits.
11. **MSHT20 is a different story.** If you swap the PDF, the mb-threshold staircase makes EDM
    unusable while `resumTransition2` floats (`scetlib_ad_cache_validity.md` §3). This does not
    apply to CT18Z.

Read a cache's versions without loading it:

```python
import zipfile, struct, io, numpy as np
z = zipfile.ZipFile(PATH)
with z.open("rules.npy") as f: h = f.read(4000)
i = h.find(b"SCTRULE"); b = h[i:]
print("rules", b[:8], struct.unpack_from("<i", b, 8)[0] if b[7:8] == b"V" else b[7] - 48)
with z.open("fo.npy") as f: h = f.read(400)
i = h.find(b"SCETFOG"); print("fo", h[i:i+8])
for n in ("format", "n_eig", "has_as", "has_muf"):
    print(n, np.load(io.BytesIO(z.open(n + ".npy").read())))
```

The `Bin_rule_opts` fields (n_train, scale, seed …) follow the anchor in the rules header, in the
80-byte v10+ layout (`scetlib-cms/py/scetlib_cache.py::_OPTS_LAYOUTS`).

---

## 8. Known gaps

Things that could not be pinned down, stated rather than papered over:

1. **The NLL-at-stored-vector check is pending** (section 5): no memory today.
   `scripts/validate_step5.sh` is ready.
2. **The step-4b injector argv was not recorded.** It was reconstructed, and it is verified
   byte-identical by re-running.
3. **The step-1b `zero_bin0_crossterms.py` argv was not logged.** It was reconstructed from its
   usage line, and it is verified CRC-identical by re-running.
4. **No record binds the cache-building `.so` to `ca15aec` by hash.**
   - `PROVENANCE.txt` in `/work/.../scetlib-ad-2da973d` lists `.so` md5s from the *first*
     (`2da973d`, 14:24) build. They do not match today's extension, `62c2e930…`.
   - The library was rebuilt from the cleaned MR !13 tree at 22:22 and committed as `ca15aec` at
     22:33, and the cache build launched at 22:36.
   - The binding rests on those timestamps and the task logbook. The `[minnorm] SVD fallback` lines
     in the build log prove the MR !13 code ran.
   - The build header's `pin=2da973d` is a hard-coded echo in `build_cache.sh`.
5. **The cache build's peak RSS was not recorded.**
6. **`df3c30f7` (WRemnants) and `2a59246` (rabbit) are not on any remote.** Bundles are on ceph.
   `4e90d32` exists on `lucalavezzo/rabbit` only as a rebased copy (`46843e4` on
   `feature/scan-save-detail`).
7. **Several scripts the chain calls are untracked in WRemnantsHelpers:**
   - `inject_aswz_cs_prior_theta.py` and its `fit_l4zero.json` input;
   - `zero_bin0_crossterms.py` and `assemble_cache.sh`;
   - the 260921 `build_cache.sh`, `build_lib.sh` and `incontainer.sh`;
   - `mem_gate.sh`.

   A snapshot is in `261001_reproduce_patches/scripts_snapshot/`. Committing them is Luca's call.
8. **Card A rebuilt from the y35 cache (adcorrY35 route) has never been run.** Neither has a card
   A rebuild at today's WRemnants `df3c30f7`. The only exact route is `c838fc63` + patch, with
   the old-cache correction.
9. **Upstream-tip (`f1780aa`) read compatibility with this cache is not measured** (section 2).
10. **No full-product reference exists at the nominal wall** (tau = 8, margin 0). GoF and impacts
    come from LATL4ZY35WALLWARM, at tau = 5 and margin 5e-3.
11. **Uniqueness of the minimum is open.** NOMSTIFF is the end of a warm-seed chain, and the
    census (T4) is running.
12. **How much a cache rebuild moves the fitted `alphaS` was never measured.** Only prediction-level
    floors exist, from a 10-bin test on an older library.
13. **The clad build time and its LLVM pairing are not recorded here.** clad was reused from
    `WRemnants/clad-install`, which was built against the same image's LLVM.

---

## What changed relative to the 260922 guide

| | 260922 guide | this guide |
|---|---|---|
| reference fit | CCKRYLOVWARM, **unwalled**, card A, NLL 365.488 | **NOMSTIFF**, walled tau = 8 margin 0, card A + lattice, NLL 376.615. Full-product sibling: LATL4ZY35WALLWARM. |
| cache | `pdf62_corrgrid_260827/merged_full`: 770 bins, \|Y\| <= 2.5, rules v8 / fo v6, 8.7 GB, built as 45 bin shards | `pdf62_y35_260921/merged_full_bin0xzero`: 1050 bins, \|Y\| <= 3.5, rules v13 / fo v14, 50.3 GB, **one process**, plus the bin-0 patch |
| SCETlib | frozen `b66f8de` snapshot, plus the HVP zero-seed backport | builder `ca15aec`, reader `2dd978a`. Both upstream; no backport needed. |
| rabbit | `f77f10e` + 2 files (#181 fix) | `2a59246` = upstream `2a64346` (contains #179/#180/#181) + `--scanSaveDetail`. Clean tree. |
| WRemnants at fit | `c838fc63` + patch | `df3c30f7` + the uncommitted wall-margin diff |
| NP constraints | default CS priors | lambda4_nu frozen at 0, 1D ASWZ lattice external term on lambda2_nu, its prior off |
| wall | optional, tau = 5, 5e-3 cushion | **required**, tau = 8, margin 0 |
| member count | "62" | 60 PDF members; muF is a polynomial (`has_muf = 0`) |
| `alphaS` x `pdfEig` Jacobian bug (0.49 % σ) | present | absent on this build and cache |
| blinded `alphaS` value printed | yes | no (section 6) |
| cache load | ~209 s | 36 s with `cache.rules.bin` (fast path, `ae9c6865`); 16-107 min / ~520 GB peak without |
| fit cost | — | 1.4 h main fit + Hessian; ~17 h with the full product |
