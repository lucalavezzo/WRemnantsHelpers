# How to build a SCETlib AD cache

A general recipe for building the autodiff (AD) cache that the SCETlib-AD param model and the
cache-derived theory corrections read. To reproduce the specific cache behind the current
nominal fit, see [REPRODUCE.md](REPRODUCE.md) instead.

## What the cache is

`build_scetlib_ad_cache.py` (WRemnants, `scripts/rabbit/scetlib_ad/`) is a thin wrapper around
SCETlib's own `examples/matched_ad/prepare_cache.py`. For every gen bin (Q, |Y|, qT) it stores two pieces:

- **resummed piece:** compressed *rules*, i.e. node weights that reproduce σ and its derivatives around an anchor tune;
- **fixed-order (nonsingular) piece:** a frozen grid with the PDF / α_s / scale responses, including the PDF cross terms.

At fit time the model evaluates σ and its exact Jacobian from the cache in seconds instead of rerunning
SCETlib. The cache is **valid only for the bins it was built on, and accurate only near its anchor**.

## What you need

| piece | where |
|---|---|
| the builder | WRemnants, branch `scetlib-ad-param-model`: [github.com/lucalavezzo/WRemnants](https://github.com/lucalavezzo/WRemnants/tree/scetlib-ad-param-model), `scripts/rabbit/scetlib_ad/build_scetlib_ad_cache.py` |
| SCETlib with AD | `gitlab.cern.ch/scetlib/contrib/scetlib-cms`, branch `autodiff-sigmaul` (SCETlib group access) |
| clang and clad | `bootstrap.sh` builds the pinned clad unless `clad-install` already exists |
| a runcard | e.g. `scetlib-cms/examples/matched_ad/matched.conf`, or your own (below) |
| the container | `/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest` |

## 1. Build SCETlib (≈ 2 min)

```bash
cmake -S $SRC -B $SRC/build -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER=$(command -v clang) -DCMAKE_CXX_COMPILER=$(command -v clang++) \
  -Dscetlib_enable_clad=ON -DCLAD_INSTALL_DIR=$PREFIX/clad-install \
  -Dscetlib_enable_doxygen=OFF -Dscetlib_enable_mathematica=OFF
cd $SRC && ./bootstrap.sh -p $PREFIX -j 96
```

- clad generates every gradient, so keep its pin. A different clad version can change the derivatives without any error.
- Use a build that contains **MR !16** (the qT < 0.1 GeV nonsingular cut in the V+jet PDF cross terms). Older builds
  corrupt the cross terms of the lowest qT bin; see "Pitfalls".

## 2. The runcard (`--base-conf`)

The builder takes the physics from the runcard and replaces its `Grid_*` sections with the grid you pass.
The runcard must have:

- `calculation_piece = matched` (the cache stores both pieces);
- `fo_order2_analytic = yes` (needed by the NNLO nonsingular);
- the orders, PDF set, α_s and the NP model and its values you want.

**The NP values in the runcard are the cache's anchor.** The rules are trained around it, so put the anchor where
your fits will be. Accuracy degrades away from it, and is known to break for λ2_ν < 0.

`target_precision_rel` in `[Integration]` sets the node-ladder accuracy; `1e-3` is what the productions use.

## 3. Build the cache

```bash
export SCETLIB_SRC=<scetlib-cms> SCETLIB_BUILD=<scetlib-cms>/build
export TF_NUM_INTRAOP_THREADS=4 TF_NUM_INTEROP_THREADS=2; ulimit -s unlimited
taskset -c 0-<N-1> python3 -u scripts/rabbit/scetlib_ad/build_scetlib_ad_cache.py \
  --base-conf my.conf -o <outdir> --threads <N> [options]
```

Run `--dry-run` first: it writes the runcard and prints the bin count and a projected cost.

| option | default | what it does / how to choose |
|---|---|---|
| `--y-edges` | the shipped corrections' \|Y\| grid | Gen rapidity edges. A cache that feeds a **theory correction** must cover the whole gen phase space it corrects; anything above the last edge stays uncorrected. A cache that only feeds a fit needs only the bins the response folds. Signed edges switch off \|Y\| folding, as needed for W. |
| `--qt-edges` | the shipped corrections' 70 bins, 0–100 GeV | Gen qT edges. |
| `--q-edges` | `60 120` | The single Q bin. |
| `--pdf-eig` | all pairs of the set | Number of PDF eigenvector pairs to make differentiable. `0` keeps only α_s. |
| `--as-pair` | `auto` | Finds `<set>_as_0116/_as_0120`, so α_s also moves the PDF. `off` makes α_s move the calculation only. |
| `--n-train` | 9 | Training points of the rule compression. More is more accurate, but the solve grows ~n_train², and so do the cache size and the RAM. |
| `--threads` | 0 (all cores) | **The main lever.** The expensive stage is parallel over the nodes of all bins together. Match it to a `taskset` CPU mask on a shared node, and do not renice. |
| `--subset 'iy…/iqt…'` | all bins | Contiguous index ranges in \|Y\| and qT. Use it for **test caches** and for crash granularity (there is no checkpointing). It is not for speed, and a subset cache on its own is not for a fit. |
| `--no-pdf` | off | Physics-only cache with no PDF or α_s members. Fast, but its α_s is a fixed-PDF derivative, so don't quote it. |
| `--outname` | `cache` | Writes `<outname>.npz` and the resolved runcard `<outname>.conf`. Keep the two together; the fit needs both. |

Build in **one process** with enough threads, rather than in subsets that you then merge. `scetlib_cache.merge_bin_caches`
exists, but merging is the least-validated path.

**Cost.** Cost is dominated by the fixed-order quadratic form (the PDF cross terms) and by the **lowest-qT bins**. As a
scale: ~1000 Z bins with 29 CT18Z pairs took ~33 h on 384 threads and wrote a ~50 GB file. Never extrapolate the cost
from a high-qT subset; one such estimate was low by 57×.

## 4. Make it fast to load (recommended)

```bash
python3 scripts/rabbit/scetlib_ad/extract_cache_rules.py <outdir>/cache.npz
```

This writes `cache.rules.bin` plus a CRC sidecar. The loader picks it up automatically, and a load drops from 16–107 min and
~520 GB peak RAM to a few minutes and ~310 GB. Copy the cache to local disk if you can.

## 5. Check it

- The build ends with `backend_check.py` and should print `all checks passed`: the anchor re-evaluation, analytic vs
  finite-difference gradients, Hessian symmetry and the gen-fold sum rule.
- Compare σ against a direct SCETlib run at a tune *away* from the anchor, at the tunes your fits actually reach. A
  derivative that is correct at the anchor says nothing about one elsewhere.

## Pitfalls

- **Builds and caches must match.** The file carries format versions (`SCTRULEV`+u32 for the rules, `SCETFOG?` for the
  fixed order), and builds refuse caches below their minimum version. Record which SCETlib commit built a cache and which
  one reads it. See `knowledge/20_frameworks/scetlib_cache_format_versions_and_pins.md` in WRemnantsHelpers.
- **Lowest qT bin, with SCETlib older than MR !16.** The V+jet PDF cross terms in qT [0, 0.5] come out wrong, which drives
  σ negative when several eigenvectors move at once. Rebuild with a fixed SCETlib, or zero that block.
- **Rebuilds are not bit-identical.** TBB task splitting changes the adaptive nodes. Expect ~3e-5 relative in σ at the
  anchor, and up to ~3e-3 in Jacobians away from it.
- **Memory.** Loading a full cache peaks at hundreds of GB. Gate concurrent loads on a shared node.
- `build_scetlib_ad_cache.py --help` currently crashes on a stray `%` in one help string. The options above are the full list.
