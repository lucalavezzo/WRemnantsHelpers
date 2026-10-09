# Running several 100-500 GB jobs on the shared login node

This applies to fits, toys and direct SCETlib evaluations that load an AD cache. The node
has ~1.45 TB of RAM, and in late Sep 2026 its swap was full. A stock AD-cache load peaks at
~3x the rules blob:

| cache | stock peak | steady state |
|---|---|---|
| old 260827 | ~150 GB | ~50 GB |
| new `pdf62_y35_260921` | ~520 GB | ~320 GB |

That peak is what kills jobs. On 2026-09-23 a 520 GB process was OOM-killed during its load
while three running fits held ~830 GB between them. The fits survived.
Evidence: `studies/alphas-scan-discontinuity/260923-y35-fit-prep/` and `260923-oldmin-loss-gap/`.

The node's user thread ceiling (see memory: thread ceiling) is the other limit.

## Gate every big load: `studies/alphas-scan-discontinuity/scripts/mem_gate.sh` (v3)

`mem_gate.sh <peak_GB> <logfile> -- <command>` works like this:

1. Take one of `NSLOTS` (3) `flock` slots.
2. Wait until `MemAvailable >= peak + 150 GB + (peaks of other slots still loading)` and
   the user's thread count is < 26000.
3. Launch the command detached (`setsid`).
4. Hold the slot until the job's log matches `DONE_RE`, or the pid dies, or 3 h pass.

This way two loads never peak together. It is study-local; copy it rather than depending
on its path. Four things in it are load-bearing:

- **Close the lock fd in the child: `setsid bash -c "$*" ... 9>&-`.** Without it, the
  launched job inherits fd 9 and holds the `flock` for its whole lifetime, not just its
  load. The slot then never frees.
- **In-flight accounting.** Each slot writes its peak to `/tmp/alphas_slot<k>.need` and
  deletes it on release. `MemAvailable` does not yet show a load that has only just
  started, so a gate that checks only `MemAvailable` lets a second loader in right behind
  the first.
- **`DONE_RE` must not match the job's own echoed command line.** The first version
  included a bare `Error`. `fitterAD.sh` echoes `--computeHistErrors`, so the slot was
  released 30 s after launch (2026-09-25), mid-load. The current value is
  `"cache loaded|Iteration 0:|Traceback|Killed"`.
- **Keep old lock names when you change the scheme.** v3 kept slot 1 on the v2 lock file,
  so gates already queued under v2 kept their place. Killing a waiting gate also means
  re-issuing its command. In `260925-ptll-gt1p5-fit`, two cancelled v2 gates were never
  re-queued, and nothing ran for an hour.

## Pause, don't kill

A rabbit toy/fit process writes its fitresults **only at exit**, so killing it loses all
in-progress work. To free CPU for a higher-priority job, `kill -STOP <pids>` and later
`kill -CONT`. This does not free the memory, which stays resident. Save the pids to a file
first. It was used without loss on 2026-09-25 (`260925-wall-sat-toys`).

## Load time is mostly the loader, not the disk

- **Stock `ScetlibCachedXsecTF.load` makes three copies of the rules blob** (numpy array,
  `.tobytes()`, C++ string). For the 143.5 GB y35 blob this is serial and memory-bound, and
  took 16-107 min.
  - Single-core inflate at ~129 MiB/s accounts for only ~18 min of that.
  - Raw /scratch reads run at ~1 GB/s.
  - So moving the cache to faster disk did not help: the /scratch copy loaded *slower*
    (107 min) on a busy node.
- **The fix is the raw-rules fast path** (see
  `../20_frameworks/scetlib_ad_cache_build_parallelism.md`, "Loading a large cache").
  Loads drop to 1-4 min at ~310 GB peak.
- **Mirror on /scratch, and record the provenance.**
  `/scratch/submit/cms/alphaS/scetlib_ad_caches/<cache>/` holds md5-identical copies of the
  260827 and `merged_full_bin0xzero` caches, each with a `PROVENANCE.txt`. A copy with 8
  parallel `dd` streams took 3 min (`260924-bilin-nons-cut/scripts/copy_to_scratch.sh`).
- **One cache tree name: `scetlib_ad_caches/`** on both ceph and /scratch (unified 2026-10-08). `ad_scetlib_caches`
  is a compatibility symlink only, so old fitresults meta_info and logbook commands still resolve. Never write new caches
  under it.
- **Slow ceph reads of one file:** you see zip blocked in `folio_wait_bit_common` while
  writes to the same filesystem stay fast. That pattern is consistent with slow objects on
  a recovering OSD. 8 parallel `dd` readers of the same file (`scripts/prefetch.sh`,
  89 MB/s aggregate) unblocked it (2026-09-24).
- **Check for your own stray crawlers** before you blame the disk. A day-old
  `bfs / -name ...` left behind by an agent's file search was found crawling the filesystem
  on 2026-09-24.
