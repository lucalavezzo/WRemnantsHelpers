# SCETlib cache format versions, and which build may read which cache

Up to fo v13 a blob carried its format version in ONE ASCII char
(`magic[7] - '0'`). **At `2da973d` that is only still true of `fo`**: `rules`
now uses an 8-char magic ending in `V` followed by a `uint32` version
(`SCTRULEV` + u32, `kRuleVersion = 13`), and the `.npz` also carries a
top-level `format` member (3 at 2da973d). Read the versions of any cache
without loading it:

    python3 -c "
    import zipfile
    z=zipfile.ZipFile(PATH)
    with z.open('rules.npy') as f: h=f.read(300)
    i=h.find(b'SCTRULE'); mg=h[i:i+8]
    print('rules', mg, 'v%d' % (int.from_bytes(h[i+8:i+12],'little')
                                if mg[7:8]==b'V' else mg[7]-48))
    with z.open('fo.npy') as f: h=f.read(300)
    i=h.find(b'SCETFOG'); mg=h[i:i+8]
    print('fo', mg, 'v%d' % (mg[7]-48 if mg[7:8].isdigit() else mg[7]-ord('A')+10))"

`format`, `n_eig`, `has_as`, `has_muf`, `anchor`, `names`, `bins` are all tiny
members and can be read the same way — no need to touch the 35-100 GB `rules`.

## The pairing table (as of 2026-09-21, updated 2026-09-28)

> **Do not fit on the unpatched `pdf62_y35_260921/merged_full`.** Its qT [0, 0.5] FO
> eigenvector cross terms are wrong: at the old minimum sigma is driven negative, and the
> loss is 1990 instead of 365. Use `merged_full_bin0xzero`. Both caches (old and new) are
> also inaccurate for `lambda2_nu < 0`. See `scetlib_ad_cache_validity.md`.

| cache | rules / fo | build that may read it |
|---|---|---|
| `pdf62_corrgrid_260914/merged_full_v10patch` | v10 / v8 | `/work/.../scetlib-ad-260914/scetlib-cms` @ `7a12ca9`, tag `cache-260914-pin` |
| `pdf62_corrgrid_260827/merged_full` (md5-identical scratch mirror, faster to read: `/scratch/submit/cms/alphaS/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full/`, 2026-09-24) | v8 / v6 | `/work/.../scetlib-ad-authval-260827/scetlib_snapshot` (b66f8de) |
| `pdf62_y35_260921/merged_full` (**built 2026-09-23**, 50.3 GB, 1050 bins; **DEFECTIVE in qT [0, 0.5], superseded by the next row**) | **v13 / v14** (`SCTRULEV`+u32 / `SCETFOGE`), `format` 3 | `/work/.../scetlib-ad-2da973d/scetlib-cms` @ **`ca15aec`** (`fix-minnorm-svd-fallback`, = 2da973d + MR !13) |
| `pdf62_y35_260921/merged_full_bin0xzero` (**quick-patched copy, 2026-09-24 — use THIS one**; md5-identical /scratch mirror with extracted `cache.rules.bin`) | v13 / v14 | same as `merged_full`; also the in-tree `WRemnants/scetlib-cms` @ `2dd978a` |
| future rebuilds | v13 / v14 | `WRemnants/scetlib-cms` @ `autodiff-sigmaul` (>= 2da973d) |

Floors move, so old caches stop loading: `kRuleVersionMin` went 9 -> 10 -> **13**
and `kFoVersionMin` 8 -> **14** (both read off `DrellYanAD.cpp` at 2da973d, not
off a commit message: the commit that bumped the fixed-order blob says
"SCETFOGB -> SCETFOGC, v12", and later commits in the same range took it to
v14). The 260827 cache (rules v8, fo v6) is therefore
**unreadable by any current build** — every fit that uses it must source the
frozen authval snapshot.

## Upstream `2da973d` takes rules to v13 and fo to v14

`1d8ccf9 .. 2da973d` (107 commits, 2026-09-21) moves the fixed-order member rows
to group-resolved per-mu_R coefficients (fo `v13 -> v14`, `SCETFOGE`), persists
the fixed-order muF polynomial in the cache, and makes the file
self-describing ("a load configures itself"). So the pin discipline applies
again: a v12 cache needs a build at or past 2da973d, and the 260914 / 260827
caches still need their own frozen trees.

**A production build at this commit does not currently complete.** `2da973d`
adds a `rmax > 1e-6 * bmax` guard on the member weight re-solve (`e185f27`), and
a 1050-bin Z build hits it 90 min in on ONE (member, bin) cell — deterministically,
across runs with different node adaptations, and only at `--n-train 9`
(`--n-train` 7 and 11 both solve the same cell to ~1e-16). Reported upstream;
draft and full diagnosis in `studies/scetlib-ad-param-model/260921-cache-2da973d`.
Reproducer is 4 minutes: `--subset '9/22'` on that grid with `SCETLIB_NAN_DIAG=1`.

Two other practical consequences measured on that build
(`studies/scetlib-ad-param-model/260921-cache-2da973d`):

* **Caches are ~30 % bigger per bin** — 59.6 MB/bin against the 260914 cache's
  45.7 MB/bin — because the muF polynomial is now stored. The builder's own
  size projection is ~70x low and should be ignored.
* **`ensure_beamfunc_grids` writes into the SOURCE tree**, not into
  `config::data_dir`, so a fresh worktree regenerates the grids (~12 min) even
  when `scetlib_DATA_DIR` points at an existing set. The generated `.dat` files
  are byte-identical to the reference ones and the run-time interpolator still
  reads `DATA_DIR`, so this is wasted time, not a physics difference.

## Two v10s exist and they are INCOMPATIBLE

The one genuine trap here. MR !12 and upstream `1d8ccf9` fix the same
`Bin_rule_opts` blit bug two different ways and **both label the result v10**:

| | MR !12 (`7a12ca9`) | upstream (`1d8ccf9`) |
|---|---|---|
| approach | serialise field by field | remove `extra_train`, keep the blit |
| scalars | 68 B packed | 80 B (incl. 12 B padding) |
| `extra_train` | 8 B count + n x 8 B | not written |
| opts block, 11 x 53 training points | **4740 B** | **80 B** |

Both guards pass before the mismatch is reachable: the version check (10 is in
range) and `_rule_config_fingerprint`, which is read BEFORE the opts. The reader
then consumes its own idea of the opts length and the stream desynchronises with
no framing to catch it. With `extra_train` populated that is 4660 bytes and will
probably die loudly; with it EMPTY it is 76 B vs 80 B, a 4-byte skew that
misparses quietly.

MR !12 is closed, so its layout exists only in that local worktree — hence the
pin and the tag. See `/work/submit/lavezzo/alphaS/scetlib-ad-260914/PIN_README.md`.

**The physics is unaffected by which fix is used.** `extra_train` is a
build-time input: not in the rule, absent from `bin_rule_fingerprint`, never
read back. Upstream's new `stage0/validate_bin_rule_roundtrip.py` shows matched
values AND the Jacobian bitwise equal between populated and empty
`extra_train`. This is a serialisation-compatibility issue only.

## Nothing auto-selects a build

Neither `WRemnants/setup.sh` nor `WRemnantsHelpers/setup.sh` mentions scetlib.
The active build is whatever tree's `setup.sh` you source, and it honours a
pre-set `SCETLIB_BUILD` (`${SCETLIB_BUILD:-$SCETLIB_SRC/build}`):

    S=/work/submit/lavezzo/alphaS/scetlib-ad-260914/scetlib-cms
    export SCETLIB_BUILD=$S/build
    source $S/setup.sh

## Check the PYTHON EXTENSION, not `libscet*`

`DrellYanAD.cpp` — where the rule format, the version floors and the quadratic
form live — sits under `py/qT/` and compiles into
`scetlib_qT.cpython-*.so`, NOT into `libscet-qT.so`. Grepping
`/proc/<pid>/maps` for `libscet*` misses it entirely and will date a build
wrongly: in the 260914 pin `libscet-qT.so` is 09-14 09:12 while the extension
carrying the fix is 09-14 11:33. Always confirm with:

    grep -oE "/[^ ]*(libscet|scetlib)[^ ]*\.so" /proc/<pid>/maps | sort -u

## The muF polynomial dominates evaluation cost, and it is a runtime FLAG

Measured 2026-09-15 on the 770-bin `pdf62_corrgrid_260914` cache (rules v10 /
fo v8) against the 260827 one (rules v8 / fo v6), same card, same 53 params:

| | old 260827 | new, poly ON | new, poly OFF |
|---|---|---|---|
| cache load | 209 s | 343-679 s | 343-679 s |
| first value+jacobian | 0.88 s | **6200 s** | **8.8 s** |
| warm value+jacobian | 0.77 s | 7.30 s | **< 0.01 s** |
| sum(sigma) | 670.02837 | 670.0284 | 670.0284 |

`set_fo_muf_poly(0)` on both sub-pieces (`core._fn._sing` / `._nons`) turns it
off. Default is 6 (`_kFoMufPolyN`), switched on upstream in `77db3ba`
(2026-09-09) alongside `251812d` and `8df8503`.

WHY it is so expensive: the muF polynomial is **not stored in any cache**. It is
built on demand per (window, bin) around the live kappa_F
(`_fo_bin_grid_poly`), and building it means the V+jet analytic fixed-order
sweep at ~283k nodes -- the same `Vjet_analytic::orders_members` code that was
19.3 h of the build's 20.1 h quadratic form. Every process that opens the cache
rebuilds it from scratch, and it is paid even though `resumScaleMuF` is frozen,
because `values_and_jacobian(p)` has NO column-subset argument.

At kappa_F = 1 with the polynomial off, `_fo_bin_derivs` falls through to the
plain stored grid (`DrellYanAD.cpp:4309`), so the central value is the same
object either way. Do NOT read the docstring's "0 = the three frozen grids
interpolated quadratically" as a revert: `8df8503` deleted those grids from the
format (has_muf = 0), so off means kappa_F simply has NO response, and moving
kappa_F off 1 would BUILD a grid rather than interpolate a stored one.

WHAT IT COSTS, measured (8 high-qT bins, poly 6 vs 0):

    central sigma      max rel 2.0e-16   (last bit, different summation order)
    scale_x1/x2/x3     max|dJ| = 0.0e+00 EXACTLY   (|J| = 0.14 .. 0.27)
    scale_kappa_F      rel 1.00          (the column goes to zero)
    every other column moved by > 1e-10: NONE

So the transition points are untouched: the FO muF is `_muFO(Q)`, Q only
(`DrellYan.hpp:2509`), while it is the RESUMMED piece where muF = muB(bT)
follows the profile -- and that is a DIFFERENT polynomial, `set_muf_poly`,
which stays on. Two switches, do not confuse them.

TWO CONDITIONS for switching it off, both silently wrong if violated:
  * `resumScaleMuF` must stay frozen -- a floated one has a zero Jacobian
    column and a singular covariance. `_check_no_inert_params` only inspects
    the FITTED subset, so a frozen one passes and a floated one must be refused.
  * the scale envelope must stay 3-point (mu_R only). With `points=7` the
    kappa_F legs come out identical to nominal and the envelope is SILENTLY
    TOO NARROW.

Also: `cache_to_theorycorr.py`'s `nonpdf_points()` writes `mufdown` / `mufup`
and two combined muF legs, which become dead variations with the polynomial
off -- the same class as `b_qqDS`, which is inert for the Z anyway. A
dead-variation guard wants a RELATIVE tolerance, not `np.array_equal`: a
b_qqDS-style O(1e-16) response is not bit-identical and exact comparison misses it.

## Does a cache cross a solver change? Yes — the read path is what matters

Asked of `pdf62_y35_260921` (built at `ca15aec`) versus the branch tip
`2dd978a`, which rewrote `rule_min_norm_update`. Three independent reasons it
loads fine, in increasing order of how much they generalise:

1. the version constants are identical (`kRuleVersion`/`kRuleVersionMin` 13,
   `kFoVersionMin` 14, `kFoMagic` `SCETFOGE`);
2. `git diff` between the two commits touches NOTHING named `Bin_rule_opts`,
   `_rule_config_fingerprint`, `load_bin_rules` or `parse_fo` — which is the
   check that matters, because the two-incompatible-v10s trap above was exactly
   a silent layout change behind a passing version check;
3. `rule_min_norm_update` is **build-time** code. A cache load deserialises
   member weights; it never re-solves them. A solver change is unreachable from
   the read path by construction.

Generalise (3): ask whether the changed code runs at BUILD or at READ time
before worrying about a cache. Only the read path can break a load.

**Measured, not just argued** (2026-09-23): `backend_check.py` run on the same
50.3 GB cache with each library. Every printed digit agrees.

| check | pin `ca15aec` | tip `2dd978a` |
|---|---|---|
| load | 516.9 s | 481.6 s |
| `sum(sigma)` | 873.0154 | 873.0154 |
| anchor re-evaluation | bit-identical | bit-identical |
| analytic vs FD | 1.93e-08 | 1.93e-08 |
| `max|H-H^T|/max|H|` | 0.00e+00 | 0.00e+00 |
| gen-fold sum rule | 0.00e+00 | 0.00e+00 |

Caveat on what was tested: the tip-side library was the `progress-fo-bilinear`
worktree, i.e. `2dd978a` plus print statements — a faithful stand-in for read
compatibility, since the instrumentation adds no numerics, but not a pristine
tip build. Evidence:
`studies/scetlib-ad-param-model/260921-cache-2da973d/logs/crossread_2dd978a_backend_check.log`.

## Adding a parameter (e.g. a new NP λ) refuses every existing cache

Code reading, SCETlib `2dd978a` (`$WREM_BASE/scetlib-cms`), 2026-10-07, for a hypothetical Y⁴ TMD term
(`studies/tmd-rapidity-shape/261007-y-shape-first-look/LOGBOOK.md` §4). The NP factor itself is cheap: the AD kernel
evaluates it LIVE at every replayed node (`include/scetlib/qT/ad/ad_kernel.hpp` ~l. 1658, `formulas::np_effective`;
also `py/qT/DrellYanAD.cpp` l. 10988, 11120), and it is on the clad tape, so its gradient/Hessian come free. The
cache is what breaks, through three independent guards:

1. `Ad_evaluator::_build_registry` (`src/qT/ad/ad_context.cpp` ~l. 171) appends `np_eff_*` names in order; an extra
   name shifts every later index;
2. `_rule_config_fingerprint` (DrellYanAD.cpp ~l. 10230) hashes the parameter NAMES in order, and the stored anchor
   vector is sized by the registry;
3. a new parameter needs new `ad::GlobalData` fields (value + index), and `layout_check` (~l. 10581) refuses any
   `sizeof(GlobalData)` mismatch (the same POD guard as in `scetlib_diff_scales_caveats.md`).

So **adding one NP parameter = kRuleVersion bump + full cache rebuild** (~25 h of stages for 770 bins,
`scetlib_ad_cache_build_parallelism.md`); budget ≈ 1 week end to end with WRemnants `scetlib_ad/params.py`
plumbing, refit and validation. A rule-file migrator (rewrite the layout, append the new parameter = 0 to the
anchor, refingerprint) is conceivable because node placement depends on the tune only through the anchor, but it
bypasses exactly these safety checks and would need bitwise replay validation. Not built, not verified.
