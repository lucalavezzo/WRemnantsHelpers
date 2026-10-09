---
title: AD fit memory breakdown
slug: 261006-memory-breakdown
study: ad-fit-memory-footprint
status: done          # active | done | paused | abandoned
created: 2026-10-06
updated: 2026-10-06
owner: study-worker
---

# AD fit memory breakdown

**Task:** Why does a rabbit fit with SCETlibADParamModel on `pdf62_y35_260921/merged_full_bin0xzero` sit at ~320 GB resident? Which component holds how much, and what can be cut?

---

## START HERE (status as of 2026-10-06 15:10)

> **Attributed, closes to 1.1 %. Measured steady state 331 GB (peak 335 GB in the Hessian). It is two things of
> about the same size. (1) The parsed rules, 144.6 GB, which is 1.0x the 143.5 GB blob: on the fast path there is no
> duplicate copy any more. (2) Two runtime muF-fit caches that SCETlib allocates on the FIRST evaluation, 184.6 GB.
> They are not in the cache file and have existed only since 2026-09-11/19.**
> The other ~3 GB is everything else: Python, TF, the datacard and the rabbit Hessian.
> The old 260827 cache has neither cache and stores conv in float. That gives its ~65 MB/bin against 315 MB/bin now.

- **Caveat first:** one instrumented job (`--noFit` + Hessian), one card (NOMSTIFF, card A + lattice, |Y| < 2.5 gen).
  The minimiser was not run. The LATCHI fit, measured passively (card A, a real minimisation), sits at 334-336 GB,
  which is the same number. The old 260827 steady ~50 GB is **not re-measured**: it is predicted from its blob plus
  the source at `b66f8de`.
- **Sanity:** `nllvalreduced` bit-identical to NOMSTIFF's (diff 0.0), edmval rel 3e-14, cov diagonal rel 3e-13.
- **Next action:** none. Task closed. The reductions are ranked below, and none is implemented.
- **Blocking on:** nothing.
- Left running by me: the passive sampler on the LATCHI fit (`scripts/sample_mem.sh 96968 ...`, 20 s reads of
  `/proc/96968/status`). It exits by itself with that pid. MEMNOM (pid 123582) has exited, exit 0.

---

## Result

**Comparability caveats:**
- GB here means 1e9 B. The in-process marks print GiB and are converted.
- Measured on one configuration: 46 ParamModel params floated (44 SCETlib + 2 envelope), `threads=128`, all 29 PDF
  eigenvector pairs + the alphaS pair profiled.
- Every member-dependent item scales with the member count.

### Memory vs time

![VmRSS vs time of the MEMNOM job with phase bands and predicted levels](rss_vs_time_MEMNOM.png)

*How to read it:*
- The black curve is VmRSS from `/proc/pid/status`.
- The external sampler had a gap from 60 to 130 s (see the Log), which the in-process marks (dots) cover.
- The orange band is the **first** `values_and_jacobian`. That single call takes the process from 146 to 331 GB in 130 s.
- The dashed lines are the static predictions from the blob headers.

### Attribution table (steady state after model build: 330.9 GB; peak 335.3 GB in the Hessian)

| component | predicted | measured | evidence | shareable by mmap? |
|---|---|---|---|---|
| python + TF + libs (1664 threads) | – | 1.04 | mark `instrumented` | partly (file-backed .so) |
| datacard (hlogk 0.09 GB, R 0.32 GB) | 0.41 | 0.42 | `datacard_read` | no |
| SCETlib configure | – | 0.09 | `scetlib_configure` | no |
| **rules: member NodeData `Var::nd`** (1050 rules x 362 sites x 60 rows x 6152 B) | **140.35** | ⎫ | `walk_y35.json` | **yes** (read-only at replay) |
| rules: nominal `nd`, g/h, grid, sites, weights, c_hess | 3.18 | ⎬ 144.64 (load mark) | walker components | yes |
| fixed-order cache (`fo.npy`, parsed) | ~1.05 | ⎭ | `cache_load_raw_rules` | yes |
| load transient (fo `np.load` + `.tobytes()` + istringstream) | ~3.2 | +3.9 (HWM in phase) | load-phase HWM 139.80 GiB vs end 136.15 GiB | – |
| **member-row muF fit cache `Bin_rule::muf_fit_var`** (float, 460 live slots x 4 coeffs per site x row) | **167.91** | ⎫ 184.60 (first v+J); **172.5 of it mmap-served** (glibc `hblkhd` +160.6 GiB) | `sl.values_and_jacobian#0`, mallinfo2 | **no** (mutable, lazily filled per muF cell) |
| nominal muF fit cache `Bin_rule::muf_fit` (double, 736 slots x 6) | 13.43 | ⎭ | same | no |
| rest of first call: 60 member conv providers (LHAPDF + beamfunc per member), thread_local `row_cheb` (2.1 MB x 128) | – | ~3.3 (residual) | 184.6 − 181.3 | no |
| scale envelope, fitter init, `load_fitresult` | – | +0.3 | marks | no |
| postfit Hessian (rabbit; 41-50 C++ HVPs of ~18.6 s each, 632 s) | – | +2.6 GiB retained (malloc free list 2.9 GiB), peak +4.3 GB | `Fitter.loss_val_grad_hess#0` | no |
| **total** | **327.5** | **330.9 steady / 335.3 peak** | closes to **1.1 %** (steady) | 144.6 GB shareable, ~186 GB private |

What is behind each row:
- **Everything is private anonymous memory.** RssFile is only 0.03-0.07 GiB.
- **The rules row is read-only during a fit.** The replay reads `rule.nd` / `rule.var[m].nd` through const references
  (`DrellYanAD.cpp` ~9150 and ~9310). The only fields it writes are the `mutable` muF-cache vectors.
- **`threads` does not matter.** The whole per-thread part is inside the 3.3 GB residual, so 128 against 32 threads
  could save at most ~3 GB. I did not run the second (threads) job, as the brief allowed.
- **The stock loader's 3x copy is gone.** Load-phase HWM is 1.03x the blob (139.8 GiB), and the load took 43 s.

### Why the old cache is ~5x smaller per bin (not 6x: 65 vs 315 MB/bin)

Both runcards are identical except for `Grid_Y`, which goes to 3.5 in the new one. Both builds use n_train 9, the same
precision and the same CT18ZNNLO set. The difference is all build version, and it is not the loader:

| | 260827 (rules v8, `b66f8de`, 08-27) | y35 (rules v13, `ca15aec`) | ratio |
|---|---|---|---|
| `sizeof(NodeData)` | 3208 B (`float conv`) | 6152 B (`double conv`, `5547155`, 09-12) | 1.92 |
| sites/bin (mean; same-bin median ratio 1.14) | 313 | 362 (353 in \|Y\|<2.5, 388 beyond) | 1.16 |
| member rows | 62 (incl. muF pair) | 60 (muF pair dropped) | 0.97 |
| **rules blob / bin** | **64.0 MB** | **136.7 MB** | **2.14** |
| nominal muF fit cache | absent (added `daddef7`, 09-11) | 12.8 MB/bin | – |
| member-row muF fit cache | absent (added `8b2db4f`, 09-19: "replay 0.608 -> 0.031 s") | 159.9 MB/bin | – |
| **steady / bin** | **~65 MB** (49.3 GB blob + ~1.5 GB, predicted) | **315 MB** (measured) | **4.85** |

On top of that the new cache has 1050 bins instead of 770. The 280 bins with |Y| > 2.5 are outside the gen range of
every |Y| < 2.5 card, and NOMSTIFF's log says so: "280 of 1050 cache bin(s) ... evaluated on every call and
discarded". They hold **28.6 %** of all sites.

### Reductions, ranked by GB saved per effort (per process unless stated; none implemented)

| # | change | saving | effort / risk | where |
|---|---|---|---|---|
| 1 | **Drop the 280 out-of-acceptance bins** for \|Y\|<2.5 cards: a 770-bin subset cache | **−93 GB/process** (331 → ~238), and −29 % replay CPU | **low**, exact. Bins are self-contained (merge_bin_caches is the inverse operation). The FO blob must be subset in the same order, because `_fo_columns_mapped(which[nb])` indexes FO member deltas by rule position | offline tool next to `scetlib_cache.merge_bin_caches` (`scetlib-cms/py/scetlib_cache.py:1168`) + `parse_fo_blob`; the rules side can stream-filter the flat `cache.rules.bin` by the offsets `scripts/walk_rules.py` already walks |
| 2 | **Share the rules between processes**: an aligned rules file in `/dev/shm` (724 GB tmpfs, empty) or local `/tmp`, `mmap(PROT_READ, MAP_SHARED)`, `Var::nd`/`nd` as non-owning spans | **−144.6 GB for every process after the first** (−103 GB after #1). 5 fits: 1.65 TB → 0.95 TB; with #1, 0.76 TB | **medium.** The current v13 stream is **not** 8-byte aligned: NodeData payload offsets mod 8 measured 0-7, because of the uint8 `has_asym` arrays, the u32 `n_iter` and the u8 `capped`. That needs a padded layout (v14, or an aligned side file written by `extract_cache_rules.py`) and `std::vector<NodeData>` → span in `Bin_rule` (`py/qT/DrellYan.hpp:874-970`), `_load_bin_rules` (`DrellYanAD.cpp:10542`). Today the C++ side copies everything (`rule_get_vec` → `vector::resize` + read) | SCETlib (upstream MR) |
| 2b | Same sharing **without a format change**: one parent loads the rules (no TF import, no TBB parallel region yet) and then `fork()`s N fit children, which COW-share the never-written NodeData | as #2 | low-medium, **untested risk:** a child forked after TBB is initialised runs single-threaded (measured in the build, `scetlib_ad_cache_build_parallelism.md`). Must check that `configure`/`load` leave TBB uninitialised. Can be done as a wrapper like `scripts/memprobe.py`, with no checkout edits | driver in task/study dir |
| 3 | **Compress member NodeData:** only the 460 live of 736 conv slots (exact), drop the 264 B of scalars duplicated from the nominal | −56 GB (140.4 → 84.0); with float deltas against the nominal −98 GB (→ 42.0) | medium-high. Needs a format change plus a per-site decompress into the dense `ad_conv_var` scratch. Float deltas need a value/Jacobian validation (the double switch `5547155` was for BUILD determinism, not replay; the same float-delta scheme in `muf_fit_var` measured 1e-10 value / ≤3e-6 gradient rel) | `Bin_rule::Var`, replay `DrellYanAD.cpp:~9310` |
| 4 | Nominal muF cache to live slots x 4 coeffs (as the member cache already is) | −7.8 GB (13.4 → 5.6) | low, exact | sizing `DrellYanAD.cpp:9108-9118`, reads at 9274 and `nomc` at 9364 |
| 5 | Member-row muF cache (168 GB) | switching it off (`set_muf_member_cache(False)`) saves 168 GB but makes the replay ~20x slower (8b2db4f) → **no**. `set_muf_member_exact_n(<4)` saves **nothing** today: the allocation uses `kMufExactN`, not `mem_mn` (`DrellYanAD.cpp:9127`, stride `mc` at 9356). fp16/bf16 deltas would halve it (−84 GB), at an unvalidated accuracy risk | – | – |
| 6 | Several starts per process (sequential) | saves a whole ~331 GB per extra start | rabbit runs one data fit per process; needs a driver. Starts in parallel threads would not run in parallel anyway, because `sigma_binned_rule_batch` takes the static `s_ad_mutex` | driver |
| 7 | Dropping members | ~98 % of the memory scales with the member-row count (60) | only if PDF eigenvectors are frozen in a configuration; **not** for the nominal fit, which uses all 60 | – |
| 8 | float32 / fewer threads elsewhere | < 3 GB in total | not worth it | – |

**Operational consequence, now and independent of any code change:** `mem_gate.sh` is mis-tuned for these jobs. It
releases its slot on `"cache loaded"` (here at t = 59 s, 146 GB), but **56 % of the memory (185 GB) arrives 130 s
later**, during the first evaluation. Two fits gated 1 minute apart therefore both pass the `MemAvailable` check
before either has allocated its muF caches. This likely contributed to the 1.6 TB overload. The fix is to release on
`"Iteration 0:"` (or a post-first-call marker) only, and to budget a steady state of 335 GB, not a load peak.

---

## Log

### 2026-10-06
- **14:20 Static analysis.**
  - The rules blob was walked header by header (seeks only, no load):
    `scripts/walk_rules.py`, which mirrors `_load_bin_rules` at 2dd978a. End offset = payload bytes exactly.
    y35: 1050 rules, 380 229 sites, 60 member rows, **var_nd = 140.35 GB of 143.53**.
    260827 (streamed from the npz with a v8 layout switch, `--old-v8 --opts-size 56`): 770 rules, NodeData 3208 B,
    62 rows, var_nd 47.97 of 49.26 GB.
    Evidence: `/ceph/.../261006_memory_breakdown/walk_y35.json`, `walk_260827.{json,log}`.
  - Runtime caches found in the code: `Bin_rule::muf_fit` / `muf_fit_var` (DrellYan.hpp:910-940), sized on the
    first replay (DrellYanAD.cpp:9108-9145). Predicted 13.43 + 167.91 GB. Neither exists in b66f8de
    (`git log -S`: daddef7 09-11, 8b2db4f 09-19), and `conv_t` went float → double in 5547155 (09-12).
- **14:30 Passive sampler on the LATCHI fit (PID 96968, not mine to touch, read-only `/proc` reads).**
  The first version used `smaps_rollup` and showed "oscillations" 175 ↔ 280 GB. **That was an artefact:** checked
  side by side, `smaps_rollup` Rss read 36-277 GB while `/proc/pid/status` VmRSS stayed at 311.6 GiB. On this kernel
  (5.14), `smaps_rollup` under-counts for processes that are allocating. Sampler v2 uses `status` as primary;
  the v1 csvs are kept as `*.v1_rollup_unreliable.csv`. LATCHI steady: 334.0-335.9 GB.
- **14:39 MEMNOM launched** through `mem_gate.sh 400` (slot 1, avail 1025 GB, gate pid 122530, python pid 123582).
  - Command: NOMSTIFF's meta_info command (`cmds/MEMNOM.cmd`, built by `scripts/build_cmd.py`) with
    `--externalPostfit snapshot_fitresults_NOMSTIFF.hdf5` (checked bit-identical to the NOMSTIFF postfit parms,
    no cov, so the Hessian IS recomputed), `--noFit`,
    `prior_sigmas=lambda2_nu=nan,lambda2=1,lambda4=1,delta_lambda2=1`, and no snapshot args.
  - Run under `scripts/memprobe.py` (monkeypatched phase marks + glibc `mallinfo2`, VmHWM reset per phase; no
    checkout edited). `tf.config.experimental.get_memory_info('CPU:0')` is **not available** on CPU ("Allocator
    stats not available"), so TF allocator stats could not be logged. mallinfo2 is used instead.
  - Log: `logs/MEMNOM.log` → `/ceph/.../261006_memory_breakdown/MEMNOM.log`.
  - I killed my own v1 sampler with `pkill -f "sample_mem.sh 96968"`, which self-matched and killed my shell
    (memory: pkill self-match pitfall). No other process was affected. Samplers were restarted by pid.
- **14:54 MEMNOM exit 0, total 869 s.** Phases:
  - load 43.4 s → 146.2 GB;
  - first v+J 130.4 s → 330.8 GB;
  - envelope 9.9 s;
  - Hessian 632.3 s → peak 335.3 GB.

  NLL / edm / cov agree with NOMSTIFF, see START HERE.
  Gate log: `logs/MEMNOM.gate.log` (slot released at 14:40:24, i.e. before the first-call allocation).
- **15:05** Plot `rss_vs_time_MEMNOM.png` (`scripts/plot_rss.py`, via `save_plot`).

---

## Findings

1. Steady RSS of a y35 AD fit = 1.0x rules (144.6 GB) + **184.6 GB of runtime muF-fit caches allocated on the first
   evaluation** + ~3 GB rest. Closes to 1.1 % against header-based predictions. (evidence: `MEMNOM.log` marks,
   `walk_y35.json`)
2. 97.8 % of the rules blob is the per-member copy of `NodeData` (`Var::nd`). 276 of its 736 conv slots are always
   zero, and its 264 B of scalars duplicate the nominal's. (evidence: walker components; `_muf_live_slot_list`
   comment "460 of 736")
3. The old/new per-bin gap (65 → 315 MB/bin, 4.85x) is entirely build-version state: float→double conv (1.92x),
   +14 % sites/bin, and the two muF caches that did not exist at b66f8de. It is not the loader and not the cache.conf.
4. 28.6 % of the y35 cache (280 bins, |Y|>2.5) is dead weight for |Y|<2.5 cards: ~93 GB per process.
5. `mem_gate.sh` releases on "cache loaded", before 56 % of the memory is allocated. Its accounting window misses
   the real peak. **→ knowledge/10_environment/big_memory_jobs.md** (orchestrator).
6. On kernel 5.14 `/proc/<pid>/smaps_rollup` badly under-reports (by up to 88 %) for these allocating processes.
   Use `/proc/<pid>/status`. **→ knowledge/10_environment/big_memory_jobs.md** (orchestrator).
7. `tf.config.experimental.get_memory_info` does not work for CPU devices. glibc `mallinfo2` (ctypes) is the usable
   in-process allocator probe. (evidence: `MEMNOM.log` first line)
8. The rules payload offsets in `cache.rules.bin` are not 8-byte aligned, so a zero-copy mmap needs a new layout.
   (evidence: alignment check in the Log, offsets mod 8 = 0..7)

---

## Open questions

- Is the TBB pool still uninitialised after `configure` + `load_bin_rules`? That decides whether fork-after-load (2b)
  is a cheap way to share the rules. A 10-bin test cache would answer it in minutes.
- How many distinct muF cells does a full minimisation visit? If it is ~1, the member-row muF cache could be
  persisted at the anchor cell and mmap-shared like the rules, which would make the whole 331 GB shareable.
- `set_muf_member_exact_n` allocates for `kMufExactN` regardless of its value (`DrellYanAD.cpp:9127`). Is this
  intended, or an upstream bug worth reporting?
- 260827 steady ~50 GB was not re-measured here, only predicted (blob 49.3 GB + baseline).
