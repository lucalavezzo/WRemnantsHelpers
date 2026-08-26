# Building a SCETlib autodiff cache: which axis parallelises, and what may be merged

Branch `autodiff-sigmaul`, build `scetlib-cms/build-fix`. Measured 2026-08-25 on
the 210-bin Z card (`ZMassDilepton_ptll_yll_realdata`, CT18ZNNLO, N3+0LL,
`target_precision_rel = 1e-3`) and on its 10-bin subset
`--subset '0,1/16,17,18,19,20'`.

## Stage costs, 210 bins

| stage | cost | axis it parallelises over |
|---|---|---|
| `sigma.prepare` (outer node set + matched xsec) | 21.9 min | bins AND nodes within a bin |
| `sing.build_bin_rules` | 4.4 min | bins |
| `sing.build_pdf_variations` | 0.40 min / member | bins, then nodes in the refill |
| `nons.build_fo_pdf_variations` | **13.7 min / member** | nodes of all bins at once |

62 members (29 eigenvector pairs + the alphaS pair + the muF pair) is therefore
~14 h, and the fixed-order member loop is 97% of it.

## The member loop is NOT starved of parallelism -- give it threads, not processes

What a member costs is `set_pdf_keep_nodes`, which refills every frozen
fixed-order node of every bin at the new PDF, and it is parallel over NODES:
"Parallel over ALL nodes of ALL bins at once, which is the half that scales"
(`DrellYanAD.cpp`). The `_fo_bin_components` sweep that follows is a closed-form
replay, parallel over bins.

So the often-repeated "a 210-bin build can only use ~210 cores" is wrong. On the
**10-bin** subset, where a bin-parallel-only stage would saturate at 10 threads:

| `--threads` | fixed-order member stage | per member |
|---|---|---|
| 200 | 0.9 min / 4 members | 0.22 min |
| 32 | 2.8-4.0 min / 4 members | 0.7-1.0 min |

A live 210-bin build sat at **145 busy cores of the 200 requested** (72%). The
lever for wall time is `--threads` (the node has 768) or more nodes.

## The build is NOT bit-reproducible. Two caches of the same runcard differ.

`_parallel_run` is a `tbb::parallel_for` whose range splitting depends on the
workers actually available, and it hands each thread a private integrator that
"keeps internal buffers", so which bins share a thread changes the adaptive
outcome and a discrete rule choice flips at the tolerance. Four independent
builds, same configuration, same `--threads 32`:

```
matched bin sum   28.8515 / 28.8517 / 28.8518 / 28.8518 pb
median nodes/bin  357 / 359 / 359 / 371
```

Bin by bin between two of them, the rule structure `(n_grid, n_sites, n_fo_w)`
differs in **9 of 10 bins** and the frozen fixed-order grid in 9 of 10.

In PREDICTIONS (24 parameters, same anchor, 10 bins), two independently built
caches of the same runcard differ by

| | max/scale |
|---|---|
| sigma at the anchor | 3.1e-05 |
| Jacobian at the anchor | 2.8e-04 |
| sigma at a 10%-displaced point | 1.7e-04 |
| Jacobian at a 10%-displaced point | 3.0e-03 |

**Consequence for validation:** any A/B between two separately built caches has
a floor of ~1e-4 (values) to ~3e-3 (derivatives away from the anchor). A
difference at that level is not a physics difference. Rebuild-and-compare cannot
show byte-identity of a code change either -- diff the CALLS instead (see
`studies/scetlib-ad-param-model/default_path_equivalence.py`).

## Which merges are legitimate

The cache is one `.npz`: `rules` (the compressed bin rules, `SCTRULE8`) and `fo`
(the frozen fixed-order grid, `SCETFOG6`) as raw blobs, plus `bins`, `anchor`,
`names`, `n_eig`, `has_as`, `has_muf`. Both blobs are parseable and spliceable
from Python (`scripts/rabbit/scetlib_ad/build_cache_parallel.py`).

* **BINS, across independent processes: SAFE.** A bin's rule is self-contained
  (its own outer grid, sites, `GlobalData`/`HardData`/`NodeData`, PDF members
  and fixed-order deltas), so nothing in it is a difference against another
  bin. Only the global header must agree -- configuration fingerprint, rule
  options, anchor, parameter names, variation metadata -- and each is a
  deterministic function of the runcard and the flags. Build with `--subset`,
  merge with `build_cache_parallel.py --merge-bins`.
* **MEMBERS, across independent processes: IMPOSSIBLE.** The member data is
  stored as differences against the nominal rule (`_fo_var_d[m]` = member sweep
  - central sweep; `Var::w`/`Var::c_val` anchored on the nominal sites), and the
  nominal side is not reproducible (above). Worse, a different site COUNT makes
  the merged cache structurally invalid: `Var::w` is one weight per site, so the
  replay would read past the end of a shorter vector.
* **MEMBERS, within one process, by forking after `build_bin_rules`: EXACT but
  SLOW.** Children share the parent's node cache and rules by copy-on-write, so
  the merge is exact -- verified, not assumed: forked-and-merged against a
  serial build in the SAME process is **byte-identical** (0 of 10 bins differ in
  the nominal rule, 0 of 40 (bin, member) records, 0 of 4 fixed-order delta
  sets, both muF grids identical), and `values_and_jacobian` agrees at
  **0.000e+00** for value and Jacobian at the anchor and off it. But a forked
  child loses the TBB worker pool (measured **99% CPU per child against the
  parent's 1900%**), i.e. it is single-threaded: on ten bins the forked member
  loop took **92.9 min** where the same parent did all four members serially in
  **4.8 min**. `prepare_cache_for_card --fork-members N --fork-selftest` exists
  because the selftest is what proves the merge machinery right, not to make a
  build faster.

### Three ordering invariants any merge must respect

1. Members are `[eig0 up, eig0 down, ..., alphaS dn, alphaS up, muF lo, muF hi]`.
   The fixed-order evaluation indexes the alphaS pair from the END
   (`i_as_dn = size - n_muf - 2`); the resummed kernel indexes eigenvectors
   forward from 0. A pair may not be split.
2. `fo_binned_pdf_batch` refuses bins that are not element-for-element
   `_fo_var_bins`, and the matched replay indexes the fixed-order member deltas
   by the RULE's position (`_fo_columns_mapped(which[nb], ...)` ->
   `_fo_stage_members(ibin)`). So `bins`, the rule records and
   `_fo_var_bins`/`_fo_var_d` must be emitted in ONE order.
3. `kMaxEigVar = 48` (so `kMaxFoMembers = 100`) and `kMaxParams = 64`. 29
   eigenvector pairs = 62 members and 24 + 29 = 53 parameters: inside both, but
   not by much.
4. A shard's OWN `_pdf_n_eig` is not the cache's, and the merge must overwrite
   it. Observed on real `--pdf-eig 2` shards: each of the two eigenvector-pair
   shards stores `n_eig = 1` (the pairs inside THAT shard) with
   `as_step = muf_lnstep = 0`, while the alphaS-pair shard stores `n_eig = 0`,
   `as_step = 0.002`. Concatenating them while keeping the first shard's header
   would give a cache claiming ONE eigenvector pair with four eigenvector member
   records in each rule -- the kernel would interpolate one coefficient and
   silently ignore the rest. The header has to be rebuilt from the plan (the
   full `n_eig`, and the alphaS/muF metadata from whichever shard built those
   pairs), which is what `merge_shards` does from the `.shard.json` sidecar.

### Two traps in the blob format

* `Bin_rule_opts` is written as one raw POD **including uninitialised padding**
  (bytes 53-55 differed between two shards, one reading `"nam"` from a stale
  stack string). Compare the FIELDS, never the raw bytes.
* `_Fo_cache::bins` is an `unordered_map` filled by the parallel bin loop, so
  the ORDER the frozen grid is written in is thread scheduling, not content.
  Compare per bin key.

## Other things to know before a 62-member build

* `set_pdf_eig_params(n_eig)` must be called on BOTH sub-pieces BEFORE the rules
  are built (it extends the parameter vector, hence the anchor, the training
  points and the rule fingerprint) and again before `load` on the evaluation
  side. `prepare_cache_for_card.py` and `xsec_backend.ScetlibADXsec` do this as
  of 2026-08-25; without it a `--pdf-eig > 0` build dies at save time.
* Size: the 210-bin, 4-member rules blob is 1166 MB uncompressed (203 MB in the
  npz). Each member adds ~240 MB, so 62 members is ~15 GB uncompressed / ~2.5 GB
  on disk -- and the fit loads the uncompressed form.
* Merge cost, measured on that 4-member 210-bin cache: 61 s wall and 4.9 GB peak
  RSS to split it into two member shards, merge them back and verify. That is
  ~4x the blob in memory, so a 62-member merge wants ~60 GB and ~10 min.
* `n_train` defaults to 9 in `prepare_cache_for_card.py` while upstream scales it
  as `max(9, ceil(1.5 * n_params))`. With 29 eigenvector pairs the parameter
  count goes 24 -> 53, so the default leaves n_train/n_params at 0.17; raising
  it costs roughly n_train^2 in the rule solve.

## The ~1800 threads per build process are a TensorFlow artefact — and removable

Measured 2026-08-26 in-container, same image, one `env -u` apart:

```
uncapped, right after `import tensorflow`:
    1665 threads = 768 tf_Compute (one per core) + 895 python3
with TF_NUM_INTRAOP_THREADS=4, TF_NUM_INTEROP_THREADS=2:
     135 threads
```

`prepare_cache_for_card.py` **never uses TensorFlow**. It imports argparse,
configparser, h5py, numpy and the `scetlib_ad` backend; TF arrives only
transitively through the `wremnants` package. So roughly **1530 of every build
process's ~1800 OS threads are pure waste**, and they are charged against
exactly the axis we parallelise the build over.

Confirmed on a real 21-shard build, not just on the import: three groups
launched before the fix sit at 1808 / 2432 / 2429 threads; groups launched after
it sit at **262-902 threads for the same work at the same `--threads 128`**.

**Why it matters.** The ceiling is **32768 OS threads per user**, and the failure
mode is silent and misattributed: a build that needs a new thread mid-stage dies
with `pthread_create has failed: Resource temporarily unavailable`, exit 134 --
and it lands on whichever process next ASKS for a thread, not on the one that
took the last of them. Capped, the practical limit goes from ~15 concurrent
build processes to several times that.

```bash
export TF_NUM_INTRAOP_THREADS=4
export TF_NUM_INTEROP_THREADS=2
```

**Do NOT export these for rabbit fits.** Those really do use TensorFlow, and
capping the pools there would slow the minimiser.

## Members are NOT all the same price — an eigenvector member is the cheap kind

The "~13.7 min per member at 210 bins" figure elsewhere in this note came from a
FOUR-member build that was the alphaS pair plus the muF pair. Both of those are
expensive kinds. Measured 2026-08-26, same card, same runcard, same threads,
launched together, four members each:

```
m210_eig     2 PDF eigenvector pairs      fixed-order stage  46.9 min
m210_asmuf   alphaS pair + muF pair       fixed-order stage  96.9 min
```

Ratio **2.07**, i.e. at 210 bins an eigenvector member is **~11.7 min** and a muF
member **~36.8 min**. A muF member pays two node refills (`set_pdf_keep_nodes`
to restore the nominal PDF, then `set_muf_keep_nodes` for the scale) plus a
whole-grid snapshot, against one refill for a PDF member.

**Consequence for planning.** A 62-member build is 58 eigenvector members, one
alphaS pair and one muF pair -- overwhelmingly the cheap kind. Costing it at the
muF rate over-counts badly: the true monolithic total is **7.3-12.9 h** depending
on node load, not ~14 h.

*Caveat, stated:* the two fixed-order stages did not overlap in time, so 2.07 is
an UPPER bound on the ratio.

## Measured per-shard throughput (10 bins x 62 members, rel 1e-3, n_train 9, P=53)

```
group  qT [GeV]  node set  rules  resum  fixed order   total    size
qt2      2-3       1.0      2.9    2.2      16.5      ~23 min   92.0 MB
qt3      3-4       0.6      4.9    4.9       8.2      ~19 min   92.1 MB
qt5      5-6       0.7      4.6    2.7       5.2      ~13 min   88.5 MB
```

The fixed-order stage **falls steeply with qT** (16.5 -> 8.2 -> 5.2 min), so the
high-qT tail is much cheaper still and a naive equal-count bin split is badly
unbalanced. The lowest ptV bin (qT 0-1) is pathological: >27 min in the OUTER
NODE SET stage alone, against 0.2-1.0 min for every other shard, and it
under-utilises its threads (~43 of 128 cores) because 10 bins cannot feed them.
Split that one further by |Y|.

## A bin split does NOT accelerate the node-set stage — the limit is per BIN

Tempting and wrong: "this shard is using only 43 of its 128 threads, so give it
fewer bins per process and it will go faster." Measured live 2026-08-26 on the
qT [0,1] shard and five |Y| sub-shards of the SAME ptV bin, all in their
node-set stage:

```
qt0     `*/0`     34.1 cores / 10 bins = 3.41 cores/bin
qt0y01  `0,1/0`    8.5 cores /  2 bins = 4.23
qt0y23  `2,3/0`    5.5 cores /  2 bins = 2.75
qt0y45  `4,5/0`    6.3 cores /  2 bins = 3.15
contrast: groups in their MEMBER stage      9.04, 8.46 cores/bin
```

Every sub-shard runs at the same ~3-4 cores per bin the parent already got. Five
of them sum to the same ~34 cores at the same rate, having started later — so
the split **cannot overtake the parent**. The adaptive node ladder within a
single qT bin carries only ~3-4 cores of parallelism and no more.

**The rule.** The node-set stage scales with BINS, not with threads. It is the
MEMBER loop that scales with threads ("parallel over ALL nodes of ALL bins at
once"). So:

* split bins for **partial-result safety** (a contiguous run is a usable cache)
  and to parallelise the **member loop** across processes -- both real wins;
* do NOT split bins expecting to accelerate a build still in its node set;
* the only lever on a node-set-bound bin is to **start it first**. The qT [0,1]
  bin is pathological (>27 min in node set against 0.2-1.0 min for every other
  ptV shard) and sets the wall time of the whole partition.

A sub-shard hedge on such a bin is still worth running as INSURANCE — the
lowest-qT shard is a single point of failure, since `GenFold` refuses a merged
cache with a hole — but it should be justified as insurance, not as speed.
