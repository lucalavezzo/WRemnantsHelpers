---
title: "|Y| <= 2.5 subset AD cache"
slug: 261006-subset-cache-y25
study: ad-fit-memory-footprint
status: done          # active | done | paused | abandoned
created: 2026-10-06
updated: 2026-10-06
owner: study-worker
---

# |Y| <= 2.5 subset AD cache

**Task:** Can we build an exact 770-bin |Y|<=2.5 subset of the pdf62_y35_260921 `merged_full_bin0xzero` AD cache that reproduces the NOMSTIFF fit bit-for-bit, and how much RSS does it save?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-10-06 17:55)

> **Done. The exact 770-bin |Y| <= 2.5 subset is at
> `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/ad_scetlib_caches/pdf62_y35_260921_y25/`.**
> It runs NOMSTIFF at **242 GB steady (243 GB peak), against 331 / 335 GB** on the full cache: −89 GB, −27 %.
> NOMSTIFF's own command replayed on it (`--noFit`) gives `nllvalreduced` **bit-identical** (diff 0.0), parameters
> bit-identical, edmval agreeing to 4e-9 relative (not to the bit; why below) and the covariance to ≤ 1.2e-12.
> Static: every kept rule record and fixed-order block is byte-identical to the source (30/30 checks).

- **Caveat first:** valid **only** for cards whose gen grid is inside |Y| <= 2.5 (card A / NOMSTIFF-type response
  cards). Anything that needs |Y| up to 3.5 must stay on `merged_full_bin0xzero`. See "Usage" below.
- **Next action:** none. Task closed. Switching production fits over is the orchestrator's call.
- **Blocking on:** nothing.
- Nothing of mine is left running. SUBY25 (gate pid 1995657) exited 0 at 17:47, and its gate released the slot then.

---

## Log

### 2026-10-06
- **17:47 SUBY25 exit 0** (`logs/SUBY25.log`, 557 s wall).
  - The cache loaded in 34.6 s with **770 bins**, via the fast path ("rules from the extracted .../cache.rules.bin").
    The full cache's "280 of 1050 cache bins ... discarded" warning is gone.
  - Postfit Hessian 379.2 s, against MEMNOM's 632.3 s. The node load was different, so this is not a clean
    CPU benchmark.
  - Results: `scripts/compare_fitresults.py` -> `logs/compare_fitresults.log`, `compare_fitresults.json`.
  - RSS: `logs/SUBY25.mem.csv`, plot `rss_vs_time_subset_vs_full.png` (`scripts/plot_rss_compare.py`).
  - Header-based prediction: `walk_pred.json`.
- **17:38 SUBY25 launched** through `mem_gate.sh 300` (slot 2; avail 1047 GB; alive 2/2 with the lattice-cs-kernel
  ASIMLIVE fit, not mine). Gate pid 1995657, log `logs/SUBY25.log`, sampler `logs/SUBY25.mem.csv`
  (`/proc/<pid>/status` every 10 s). Command `cmds/SUBY25.cmd` = NOMSTIFF's own meta_info command
  (`scripts/build_cmd.py`) with only `cache=/conf=` -> subset, `-o/--postfix`, `--externalPostfit` = NOMSTIFF's
  snapshot (checked bit-identical to its postfit parms), `--noFit`, the pinned
  `prior_sigmas=lambda2_nu=nan,lambda2=1,lambda4=1,delta_lambda2=1`, snapshot args dropped. Token-for-token it
  is MEMNOM's command (`../261006-memory-breakdown/cmds/MEMNOM.cmd`) except cache/conf/out/postfix. It runs on plain
  rabbit_fit.py, without memprobe. WRemnants moved a008faa5 -> 44f8a5c0 during this session; that commit only ADDS
  `lattice_cs_chi2.py` + data + a test, none of which this command imports. rabbit unchanged (2a59246).
- **17:39 Static validation ALL PASS, 30/30** (`scripts/validate_static.py`, `logs/validate_static.log`,
  `validate_static.json`).
  - Every one of the 770 kept rule records is byte-identical to its source record, and each parses exactly with
    SCETlib's own `scetlib_cache._parse_rules`.
  - The header is byte-identical to the source's, and there are no extra bytes.
  - fo: the grid node blocks, the muF-poly blocks, all 60 members' 9-double deltas, the quadratic-form slices and
    the group-resolved rows are byte-identical per bin. The bin0xzero zeros are present (11 qT[0,0.5] bins,
    off-diagonal max 0.0).
  - The small npz members' raw .npy bytes are identical, and cache.conf differs only in the comment and the
    Grid_Y line.
- **17:37 Extract done** (`logs/extract.log`, 435 s inflate with zipfile's CRC check): `cache.rules.bin` md5
  5314435cdc7259bcea8d999e43723f85, **equal** to the md5 of the bytes the builder streamed into `rules.npy`.
- **17:27 npz written** (1305 s at ~85 MB/s, single-thread deflate-6; 35.9 GB vs the source's 50.3 GB). The
  `cache.conf` step then failed on a regex bug (`[^\[]*` stopped at the values list's `[`). I fixed it line-based
  and reran only that step (`--conf-only`). The npz was not touched.
- **17:40** `PROVENANCE.txt` and `README.txt` written into the cache dir (`scripts/write_provenance.sh`).
  The source npz md5 was recomputed today: e2e3a706..., matching its PROVENANCE.
- **17:05 Inputs checked** (`scripts/inspect_inputs.py`).
  - NOMSTIFF's own meta_info command uses `cache=/conf=` on the /scratch `merged_full_bin0xzero` mirror.
  - Its card (`260923_lattice_fits/cards/cardA_latticeASWZ_l4zero_statsyst.hdf5`) has response auxiliary
    `scetlib_np` with `gen_axes = [ptVGen, absYVGen]`, `absYVGen` edges `[0, 0.15, ..., 2, 2.5]` (11 bins) and
    `ptVGen` = the cache's 70 qT bins, `N_gen` of length 770. So the card's gen grid is exactly the 770 cache bins
    with Y_hi <= 2.5. No cache bin straddles 2.5.
  - Neither fingerprint contains `Grid_*`: `_rule_config_fingerprint` = fo fingerprint + parameter names, and
    `fo_cache_fingerprint` has no binning (`DrellYanAD.cpp:712`, `:10227`). WRemnants never reads `Grid_Y`
    for the model (only a comment in `np_damping_wall.py`, whose wall |Y| comes from the card). So cutting
    `Grid_Y` in `cache.conf` is bookkeeping, not load-bearing.
- **17:05 Dry run** (`logs/build_dryrun.log`): source rules walked (v13, 1050 records, end = file size), the header
  re-parsed by SCETlib's own `scetlib_cache.parse_rule_blob` on a zero-bin blob; the fo emitter
  (`scripts/cache_io.py:emit_fo`) reproduces the full 1054608271 B source fo blob **byte for byte** before it is
  used to subset. Subset rules payload 102.528 GB (71.4 % of 143.533), fo 734.1 MB (69.6 %). The one fo muF
  polynomial window keeps bins.
- **17:05 Build launched** (`scripts/run_build.sh` -> `logs/build.log`): streams the 770 kept records from
  `/scratch/.../merged_full_bin0xzero/cache.rules.bin` through a ZIP_DEFLATED writer into the new `cache.npz`
  (np.savez_compressed settings, members in source order, unchanged small members copied as raw .npy bytes),
  then `extract_cache_rules.py` on the result. Output:
  `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/ad_scetlib_caches/pdf62_y35_260921_y25/`
  (ceph 352 TB free; /scratch is 100 % full). NB the existing ceph cache tree is `scetlib_ad_caches/`;
  this one is under `ad_scetlib_caches/` as the brief specified (the /scratch spelling).

---

## Result

**Comparability caveats (read first):**
- **Two runs on the full cache.** NOMSTIFF is the real converged fit on the full 1050-bin cache.
  MEMNOM (`../261006-memory-breakdown`) replays it on the full cache with the same `--noFit` recipe, under
  `memprobe.py`. SUBY25 (this task) is the token-identical command with only `cache=`/`conf=` (and the output name)
  changed, run under plain `rabbit_fit.py`.
- **Code is the same as MEMNOM's in practice.** WRemnants moved a008faa5 → 44f8a5c0 between MEMNOM and SUBY25,
  but that commit only adds files that this command does not import. rabbit is 2a59246 for both.
- **All three runs use the same priors.** `prior_sigmas=lambda2_nu=nan,lambda2=1,lambda4=1,delta_lambda2=1` is
  pinned, which is NOMSTIFF's effective setting (the WRemnants default changed today).
- **Real data, blinded.** Only differences are printed. GB = 1e9 B. RSS is VmRSS from `/proc/<pid>/status`.
- **What `--noFit` does not exercise.** It evaluates at the NOMSTIFF minimum (loss, gradient, Hessian, EDM) and
  does not minimise. A minimisation on the subset visits other points. Exactness there follows from the static
  byte identity plus the fold argument below, not from a run.

### Exactness

| check | SUBY25 vs NOMSTIFF | SUBY25 vs MEMNOM |
|---|---|---|
| `nllvalreduced` | **bit-identical** (diff 0.0) | **bit-identical** |
| postfit parameters | bit-identical | bit-identical |
| `edmval` (both ~3.0e-14) | rel **4.0e-9** | rel 4.0e-9 |
| cov diagonal, max rel | 4.3e-13 | 5.7e-13 |
| cov, max \|Δ\|/√(C_ii C_jj) | 1.2e-12 | 1.1e-12 |
| σ, max rel | 2.1e-13 | 2.8e-13 |

The EDM is not bit-identical, and that is expected rather than a defect:
- The loss is bit-identical, and so are all 770 kept bins' C++ inputs.
- The dropped 280 bins only ever entered the fold as discarded columns. With 770 instead of 1050 columns, TF
  blocks the Jacobian contraction differently, so the gradient changes at the last-ulp level of its summed terms.
- At a converged minimum the gradient is itself tiny: EDM ~3e-14, so |g|·σ ~ 2e-7. A relative EDM change of
  4e-9 is an absolute 1.2e-22, far below anything that could mean anything.
- MEMNOM vs NOMSTIFF agree to 3e-14 because they use the same cache, so the same contraction shapes.

**Static validation, 30/30 PASS** (`validate_static.json`, `logs/validate_static.log`):
- **Rules.** The header up to n_bins is byte-identical. All 770 kept records are byte-identical to the source record
  with the same key, and each parses exactly with SCETlib's own `scetlib_cache._parse_rules`. There are no extra bytes.
- **Fixed order.** Identical version, fingerprint and meta. Per kept bin: the frozen grid node block, the muF-poly
  block, all 60 members' 9-double deltas, the quadratic-form slice `B[:, :, :, bin, :]` and the group-resolved
  (mu, data) rows are all byte-identical. The order is the same as the rules', which matters because
  `_fo_columns_mapped` indexes by rule position.
- **bin0xzero patch kept.** All 11 qT [0, 0.5] bins have their off-diagonal form entries at exactly 0.
- **npz.** The small members' raw `.npy` bytes are identical; `bins` = source `bins[Y_hi <= 2.5]` bitwise.
- **Fast-path file.** `extract_cache_rules.py` (CRC-checked inflate) reproduced the streamed payload: md5 equal.

### Memory

![VmRSS vs time, full y35 cache (MEMNOM) vs |Y|<=2.5 subset (SUBY25), NOMSTIFF card, --noFit + Hessian](rss_vs_time_subset_vs_full.png)

*Caveat for the figure:* the runs were 3 h apart on a shared node. MEMNOM ran under `memprobe.py` (its sampler gap
from 60 to 130 s is filled by in-process marks); SUBY25 is plain. The dashed lines are header predictions.

| | full cache (MEMNOM) | subset (SUBY25) | change |
|---|---|---|---|
| bins | 1050 | 770 | −26.7 % |
| rules blob | 143.53 GB | 102.53 GB | −41.0 GB |
| predicted muF-fit caches (nominal + member rows) | 13.4 + 167.9 GB | 9.6 + 120.0 GB | −51.8 GB |
| **steady VmRSS** | **330.9 GB** | **242.0 GB** | **−88.9 GB (−26.9 %)** |
| peak (VmHWM) | 335.3 GB | 243.2 GB | −92.1 GB |
| header prediction | 332 | 238 | measured − predicted = +3.6 GB for SUBY25 (prediction excludes the ~3 GB of runtime residuals, see T1) |
| cache load / Hessian | 43.4 s / 632 s | 34.6 s / 379 s | indicative only (different node load) |

This is what T1 predicted: −93 GB, 331 → ~238.

### Usage

- **How a fit switches.** Point the ParamModel at the subset:
  `cache=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/ad_scetlib_caches/pdf62_y35_260921_y25/cache.npz`
  `conf=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/ad_scetlib_caches/pdf62_y35_260921_y25/cache.conf`
  - Nothing else changes: same SCETlib build (`agent_setup.sh --scetlib current`, scetlib-cms 2dd978a, or the
    2da973d/ca15aec pin), same `fit_params`/priors. A warm start from a full-cache fit's `--seedFrom` vector is valid.
  - The fast path is picked up automatically: `cache.rules.bin` + `cache.rules.json` sit beside the npz and the
    sidecar matches.
  - `fitterAD.sh -c <dir>` takes the directory.
  - Budget **~245 GB** per fit in `mem_gate.sh`, not 335.
- **Valid for:** any card whose gen grid (the response auxiliary's `absYVGen`, or the channel axes for
  `gen_level=1`) lies within |Y| <= 2.5 on the cache's qT/Q binning. Card A (`cardA_latticeASWZ_l4zero_statsyst`,
  NOMSTIFF and the lattice/stiff-wall fits) qualifies: `absYVGen = [0, ..., 2, 2.5]`, 770 gen bins.
  - The results are identical to the full cache, because the dropped bins fold to nothing in those cards.
  - A card with a coarser |Y| grid inside 2.5 also works: the fold sums kept bins by value.
- **NOT valid for:** anything that needs |Y| > 2.5. That includes theory corrections and gen-level fits or
  predictions out to |Y| = 3.5 (the reason the y35 cache was built), and cards whose gen |Y| reaches beyond 2.5.
  - Such a card **fails loudly at model build**: `GenFold` raises "does not cover this card's gen binning"
    (`xsec_backend.py` ~l.455). It does not silently integrate less phase space, unless someone passes
    `partial=True`, which fits never do.
  - Use `merged_full_bin0xzero` for those.
- **Inherited caveats** are unchanged from the source, because it is the same bytes: the lambda2_nu < 0
  inaccuracy, the qT [0, 0.5] cross-term zeroing, and the MSHT20 caveats do not apply here (CT18Z).
  See `knowledge/20_frameworks/scetlib_ad_cache_validity.md`.
- **Files.**
  - `cache.npz` (35.9 GB, md5 0b92ce44…), `cache.rules.bin` (102.5 GB, md5 5314435c…), `cache.rules.json`,
    `cache.conf` (source runcard with Grid_Y cut to 2.5 plus a header comment).
  - `PROVENANCE.txt` (source md5 e2e3a706…, SCETlib 2dd978a, scripts and md5s, date), `README.txt`,
    `build_of_source_cache.log`.
  - There is no /scratch mirror (/scratch is full). The cache loads from ceph in 35 s.

---

## Findings

1. A |Y| subset of a v13/v14 SCETlib-AD cache is a pure gather and is exact. Bins are self-contained. The rules
   header, the fo fingerprint and the rule fingerprint contain no binning, and `Grid_*` in cache.conf is never
   read by the load or the fold. Recipe: `scripts/build_subset_cache.py` (streams the rules; peak RSS ~3 GB;
   ~22 min deflate + 7 min extract for 102 GB). (evidence: `validate_static.json`)
2. The NOMSTIFF replay on the subset is bit-identical in loss and parameters. The EDM moves at 4e-9 relative,
   from the different contraction shape: last-ulp gradient reassociation at an EDM of 3e-14. So "EDM bit-identical"
   is the wrong acceptance test for a change in bin count; NLL bit identity is the right one.
   (evidence: `compare_fitresults.json`)
3. Measured −88.9 GB steady (330.9 → 242.0 GB) and −92 GB peak per NOMSTIFF-type fit. The header prediction
   (rules + both muF caches) gets this to within 4 GB. (evidence: `logs/SUBY25.mem.csv`, `walk_pred.json`)
4. `mem_gate.sh` holds the slot for the whole job on a `--noFit` run (no "Iteration 0:" line). The slot was
   released at pid exit, as the brief expected. (evidence: `logs/SUBY25.gate.log`)
5. The `scetlib_cache.py` emitter used here (`scripts/cache_io.py:emit_fo`) round-trips the full fo v14 blob
   byte for byte. It could serve as an upstream `split_bin_cache` / inverse of `merge_bin_caches`.
   **→ orchestrator** (knowledge/ or an upstream MR, the orchestrator's call).

---

## Open questions

- A minimisation on the subset was not run. The `--noFit` replay plus byte identity make a difference
  implausible beyond last-ulp gradient noise, which could still shift the stopping iteration of a long minimisation
  by an iteration or so. A first production fit on the subset should be compared against its full-cache twin.
- The Hessian ran 40 % faster (379 vs 632 s), more than the 29 % fewer sites alone predicts. The node load differed
  between the runs, so the CPU saving is not cleanly measured.
- Naming: the brief put the cache under `.../alphaS/ad_scetlib_caches/` (the /scratch spelling), while every other
  ceph cache is under `.../alphaS/scetlib_ad_caches/`. I left it where the brief said. A move is the orchestrator's call
  (and it means updating PROVENANCE/README and the json sidecar's `source` field, which is informational only).
