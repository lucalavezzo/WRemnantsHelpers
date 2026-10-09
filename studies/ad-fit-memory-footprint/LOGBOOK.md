---
title: Memory footprint of SCETlib-AD fits
slug: ad-fit-memory-footprint
status: active        # active | paused | done | abandoned
created: 2026-10-06
updated: 2026-10-06
---

# Memory footprint of SCETlib-AD fits — logbook

**Goal (Luca, 2026-10-06):** understand why every rabbit fit with the SCETlibADParamModel on the new
`pdf62_y35_260921/merged_full_bin0xzero` cache sits at ~320 GB resident, and cut it. On 2026-10-06 about 5 such fits
together (1.6 TB) overloaded the 1.45 TB shared node, which had to be paused and rebooted. Done when the ~320 GB is
attributed component by component and the cheap reductions are identified, with a measured saving for each.

**Known going in** (`knowledge/10_environment/big_memory_jobs.md`):
- the rules blob is 143.5 GB in memory (private per process);
- ~180 GB is unattributed;
- the old 260827 cache ran at ~50 GB steady with 770 bins, the new one at ~320 GB with 1050 bins: ~6× for 1.4× the bins;
- the stock loader makes 3 copies at load (the raw-rules fast path avoids that).

Candidate fixes: mmap the rules so processes share them; run several starts per process; drop duplicates/precision.

---

## START HERE (status as of 2026-10-06)

> **Opened.** T1 delegated: [261006-memory-breakdown](261006-memory-breakdown/LOGBOOK.md).

- **Next action:** Luca's choice of reductions (subset cache first?), and the mem_gate release-point fix (shared script; needs his OK).
- **Blocking on:** nothing.

---

## Log

### 2026-10-08
- Luca: one cache-tree name. Moved the subset cache to `/ceph/.../alphaS/scetlib_ad_caches/pdf62_y35_260921_y25/` and
  renamed `/scratch/submit/cms/alphaS/ad_scetlib_caches` to `scetlib_ad_caches`. `ad_scetlib_caches` is now a compat
  symlink in both places, so the old paths in fitresults meta_info and logbooks still resolve. SATC2 (cache already in
  memory, no open fds) was unaffected. Updated the knowledge notes (big_memory_jobs, cache_format_versions) and the
  WRemnants `scripts/tests/test_lattice_cs_term.py` default path (uncommitted).

### 2026-10-07
- [261007-thread-scaling](261007-thread-scaling/LOGBOOK.md) DONE (~76 min of node time, one job at a time).
  - Iterations and the Hessian scale linearly 32 → 128 threads, with no measurable serial part. 256 gives only ~1.2× more
    speed for 1.7× the CPU.
  - Memory is flat (~240–250 GB on the subset, +40–50 MB per thread).
  - **Keep threads=128.** Two fits (the run cap) then use 256 of the 384 physical cores.
  - Wall time varies ~2× with node load; compare CPU-seconds.
- Luca: a quick check of how runtime and memory scale with `threads=`. Delegated as
  [261007-thread-scaling](261007-thread-scaling/LOGBOOK.md): threads 16/32/64/128 on the subset cache, 5-iteration fits
  plus one Hessian, one job at a time, ≤ ~2 h of node time.

### 2026-10-06
- [261006-subset-cache-y25](261006-subset-cache-y25/LOGBOOK.md) DONE.
  - Path: `/ceph/.../alphaS/ad_scetlib_caches/pdf62_y35_260921_y25/`, 770 bins.
  - Static check: byte-identical to the source in all 30 tests.
  - NOMSTIFF `--noFit` replay: nllvalreduced bit-identical; covariance ≤ 1.2e-12.
  - Memory: steady **242 GB vs 331**, peak 243 vs 335.
  - Valid only for gen |Y| ≤ 2.5 cards (card A, NOMSTIFF, lattice/stiff). Anything else fails loudly at model build
    (GenFold "not exactly tiled").
- Luca: build the subset cache; fix mem_gate; ask the collaborators about the muF cache.
  - mem_gate v4 committed (Helpers 904ffc9, not pushed): `DONE_RE` is now "Iteration 0:|Traceback|Killed", and there is a
    MAXRUN=2 run cap. Tested with two dummy jobs: the second waited until the first exited.
  - Subset cache delegated: [261006-subset-cache-y25](261006-subset-cache-y25/LOGBOOK.md).
  - muF cache: it exists because `resumTransition2` is fitted (`set_diff_scales` → prof_live → μF moves per node).
    Freezing it would skip ~181 GB per fit, but that is untested. Luca is asking the collaborators.
- T1 DONE ([261006-memory-breakdown](261006-memory-breakdown/LOGBOOK.md); measured on one instrumented NOMSTIFF Hessian
  pass, closes to 1.1 %). Steady 331 GB, peak 335 GB.
  - Breakdown: rules 144.6 GB (1.0× the blob); SCETlib runtime muF-fit caches 181 GB (member rows 168, nominal 13),
    allocated at the FIRST evaluation and not stored in the cache file; Python/TF/datacard 1.5 GB.
  - Everything is private anonymous memory; only the rules are shareable.
  - Old vs new cache, per bin, is 4.85×, all from build-version changes: conv tables went float → double in 5547155, and
    the muF caches arrived with daddef7/8b2db4f.
  - Reductions, ranked:
    - a 770-bin |Y| ≤ 2.5 subset cache: −93 GB, exact, low effort;
    - mmap/shared rules: −145 GB per extra process, medium (SCETlib loader + alignment);
    - live-slot-only conv: −56 GB, exact;
    - nominal muF compaction: −8 GB.
  - Ops: mem_gate releases its slot on "cache loaded" (146 GB), but the muF caches add +185 GB ~130 s later. The gate never
    sees the real peak, which likely fed today's overload. Fix: release on "Iteration 0:" and budget 335 GB.
  - smaps_rollup under-reports by up to 88 % on this kernel; use /proc/pid/status.
- Opened after the node overload. Concurrency rule until this is solved: at most 2 big AD jobs alive at once (the
  orchestrator sequences them; the shared mem_gate has no run cap).

---

## Findings

---

## Decisions
