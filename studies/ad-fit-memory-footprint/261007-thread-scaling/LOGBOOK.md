---
title: Thread scaling of SCETlib-AD fits
slug: 261007-thread-scaling
study: ad-fit-memory-footprint
status: done          # active | done | paused | abandoned
created: 2026-10-07
updated: 2026-10-07
owner: study-worker
---

# Thread scaling of SCETlib-AD fits

**Task:** How do the runtime and the memory of a SCETlib-AD rabbit fit scale with the param model's `threads=` setting?

---

## START HERE (status as of 2026-10-07 11:00)

> **Keep `threads=128`.** Runtime scales almost perfectly as 1/threads from 32 to 128 (CPU cost per phase flat to
> ~12 %); 256 is only 1.2× faster than 128 for 1.7× the CPU and pushes the node past its 384 physical cores. Memory
> barely depends on threads (~50 MB per thread: 241 GB at 32 → 244 at 128 → 253 at 256 peak).
> Caveat before any number: one run per point on a shared node, and the noise is large. The same TS128 job repeated
> under a heavier node load (630 vs 330) was 2.4× slower in the iterations and 1.85× in the Hessian at the same CPU
> use, so wall times are only comparable at similar load; the CPU-seconds column is the more robust measure.

- **Next action:** none. Task closed. (TS16 was not run; see the 10:01 log entry.)
- **Blocking on:** nothing.
- Nothing of mine is left running. Node time used: 09:34–10:50, ~76 min, strictly one job at a time.

---

## Setup

- **Command:** NOMSTIFF's own `meta_info` command (`/ceph/.../260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5`), built by
  `scripts/build_cmd.py`, with only these changes:
  - the |Y| ≤ 2.5 subset cache `ad_scetlib_caches/pdf62_y35_260921_y25/` (exact for this card, 770 bins);
  - `threads=` = the scanned value (NOMSTIFF ran 128);
  - priors pinned to NOMSTIFF's: `prior_sigmas=lambda2_nu=nan,lambda2=1,lambda4=1,delta_lambda2=1`;
  - start = a kicked copy of NOMSTIFF's converged snapshot (`/ceph/.../261007_thread_scaling/seed_NOMSTIFF_kick03.hdf5`):
    ±0.3 σ_postfit in alphaS, pdfEig0, pdfEig3, resumTNP_s, resumTNP_b_qqV (values not printed; blinded);
  - `--minimizerMaxiter 5` (trust-krylov, the default), then the postfit Hessian (+EDM from it) in the same job.
- **Measurement:** every log line is prefixed with a unix timestamp (`scripts/run_ts.sh`); `scripts/sample_proc.sh`
  samples `/proc/<pid>/status` (VmRSS, VmHWM, Threads), `/proc/<pid>/stat` (utime+stime) and `/proc/loadavg` every 5 s.
- **Concurrency:** strictly sequential (`scripts/chain.sh`), each job through the shared
  `studies/alphas-scan-discontinuity/scripts/mem_gate.sh 260`.

---

## Log

### 2026-10-07
- 10:50 **TS128r (repeat) and TS256 done**; analysis `scripts/analyze.py` → `table.md`, `table.json`, both plots.
  TS256 (10:29–10:37): build 118 s, iterations 49 s, Hessian 190 s, peak 253 GB, 238–242 cores busy. TS128r
  (10:37–10:50): build 150 s (same as TS128), but iterations 142 s and Hessian 413 s, against 59 / 223 s for TS128 at
  the same CPU use. The node load during it was 530–630, against 280–330. Noise is ×2 from the node load alone.
- 10:29 TS32 done: build 374 s, iterations 220 s, Hessian 1018 s; still on the 1/threads line.
- 10:01 **TS64 done**. Same iteration path to the last digit (loss sequence identical to TS128, so the work per run
  is identical). Build 240 s, 5 iterations 131 s, Hessian 520 s: 1.6×, 2.2×, 2.3× TS128, i.e. ~linear in 1/threads,
  at ~58–61 cores busy. Warm-cache load 33 s. RSS within 2 GB of TS128.
  - **Decision: TS16 dropped** (`STOP` file; chain stops before it). With 64→128 linear, TS16 extrapolates to
    ~55 min of node time for no new information, which would break the ~2 h budget. Queued instead (chain2, pid
    55970, waits for chain 1): TS256 (does it still scale?) and the TS128r noise repeat.
- 09:45 **TS128 done** (`logs/TS128.log`). Cache load 179 s (cold page cache: SUBY25 yesterday took 35 s; the load
  is I/O-bound on ceph, ~0.3 CPU cores busy), build + first eval 147 s at ~98 cores, 5 iterations 59 s at ~116 cores,
  Hessian 223 s at ~122 cores; RSS 105 GB after the load, 239 GB after the first eval (muF caches), peak 244 GB;
  nlwp 1792. Load average ~325.
  - The job then exits 1: `Cholesky decomposition failed, Hessian is not positive-definite` in the covariance step
    AFTER the Hessian (whose timing line is already written). Expected at a start this far from the minimum: the kick
    is "0.3 marginal σ" with everything else held, which through the strong correlations is far more in conditional
    σ (iteration-0 loss is ~270 above NOMSTIFF's). Irrelevant to the timing; kept the same seed for all runs so the
    work per run is identical. The chain goes on regardless of the exit code.
- 09:35 chain launched (TS128, TS64, TS32, TS16). Node load average ~210–290 on 768 hardware threads at launch.

---

## Result

**Comparability first.** All five runs use the same command (NOMSTIFF's, on the |Y| ≤ 2.5 subset cache) and the same
kicked seed, and they follow the *same* minimiser path: the loss sequence of the 5 trust-krylov iterations is
identical to the last printed digit in every run, so the work per run is identical and only `threads=` differs. But
the node is shared (2 × 192-core EPYC 9965, 768 hardware threads) and its load swung between ~170 and ~780 during the
runs; the load average below *includes our own threads*. Every job exits 1 after the Hessian (Cholesky fails at the
far-from-minimum start); the Hessian timing is written before that and is unaffected. The TS128 cache load (179 s) is a
cold page cache, not a thread effect; warm loads are 30–46 s at any thread count.

| run | threads= | load avg build / iters / Hessian | cache load [s] | build + 1st eval [s] | 5 iters [s] (per iter) | Hessian [s] | start -> Hessian done [s] | peak / steady RSS [GB] | nlwp | cores busy build / iters / Hessian | core-s iters / Hessian |
|---|---|---|---|---|---|---|---|---|---|---|---|
| TS32 | 32 | 257 / 169 / 327 | 30 | 374 | 220 (44) | 1018 | 1658 | 241.0 / 240.4 | 1696 | 29 / 31 / 30 | 6781 / 31006 |
| TS64 | 64 | 257 / 282 / 283 | 33 | 240 | 131 (26) | 520 | 934 | 241.4 / 240.5 | 1728 | 54 / 58 / 61 | 7623 / 31746 |
| TS128 | 128 | 386 / 330 / 280 | 179 | 147 | 59 (12) | 223 | 629 | 244.4 / 242.4 | 1792 | 98 / 116 / 122 | 6789 / 27212 |
| TS128r | 128 | 541 / 630 / 533 | 38 | 150 | 142 (28) | 413 | 755 | 244.7 / 242.4 | 1792 | 98 / 123 / 123 | 17369 / 50763 |
| TS256 | 256 | 620 / 484 / 358 | 46 | 118 | 49 (10) | 190 | 424 | 253.2 / 249.6 | 1920 | 125 / 238 / 242 | 11592 / 46056 |

(build = model build + first evaluation, which is the muF-cache build; RSS goes 103–108 → 237–245 GB in it.
"cores busy" = (utime+stime)/wall over the phase; "core-s" = CPU core-seconds, flat = perfect scaling.)

![Wall time, CPU utilisation and CPU cost per phase vs threads=; hollow markers are the TS128r repeat at node load 530-630](time_vs_threads.png)

*Single runs on a shared node; hollow = the 128 repeat at a heavier load. Wall time is load-dependent at the ×2 level.*

![VmRSS vs time for every run, and peak/steady RSS vs threads=](rss_vs_threads.png)

**Reading.**
- **32 → 128: ideal scaling.** The iterations cost 6.8–7.6 k core-s and the Hessian 27–32 k core-s at 32, 64 and 128
  threads: no measurable serial part in either (fit t = a + b/n gives a ≈ 15 s for the 5 iterations, ≈ 0 for the
  Hessian). The process keeps 90–95 % of its threads busy (116–122 of 128). The SCETlib batch replay (loss+grad and
  the HVPs) is the whole cost, and it is embarrassingly parallel.
- **The build has a serial part of ~80 s** (Amdahl fit: 80 s + 9.5 k core-s / n). This predicts 117 s at 256, and
  118 s is what we measured.
- **256: diminishing returns.** Iterations 49 s (Amdahl prediction 41 s) and Hessian 190 s (prediction 105 s): the run
  used 238–242 cores but each did less work, costing 1.7× the CPU of TS128. During TS256 the node load was 360–480 with
  our own 240 threads in it, i.e. above the 384 physical cores, so its threads were sharing cores with SMT siblings.
  That is the same mechanism as the TS128r repeat, which ran at its full 123 cores but at load ~630, and took 2.4× as
  long. On an idle node 256 might scale better. We will rarely have one.
- **Memory is not a reason to lower threads.** Steady RSS 240.4 (32), 240.5 (64), 242.4 (128), 249.6 GB (256): about
  +40–50 MB per thread, i.e. per-thread SCETlib scratch. It is negligible next to the 103 GB rules and the ~135 GB muF
  caches, which do not depend on threads. nlwp = 1664 + threads (TF's pools are fixed at ~1664 threads).

**Recommendation: keep `threads=128`** (the current setting) for production fits. It is on the ideal-scaling line, so
it is the fastest setting that wastes no CPU. One NOMSTIFF-type fit iteration costs ~12 s and a Hessian ~220 s at
moderate load. Two concurrent AD fits (the MAXRUN=2 cap) at 128 each use 256 of the 384 physical cores and leave room
for other users. 256 buys ≤ 20 % wall for 1.7× the CPU, and two such fits alone would oversubscribe the physical
cores. Drop to 64 only when the node is already past ~400 load: there, extra threads mostly buy SMT contention.

---

## Findings

1. SCETlib-AD fit iterations and the postfit Hessian scale as 1/threads from 32 to 128 (CPU core-seconds flat to
   ~12 %); the model build + first eval has a ~80 s serial part. — (evidence: `table.md`, `time_vs_threads.png`)
2. Past the node's 384 physical cores (our threads + others' load), per-thread speed drops about 2×: TS256 cost 1.7×
   the CPU of TS128 for 1.2× the speed, and a TS128 repeat at load 630 was 2.4× slower at the same CPU use. —
   (evidence: TS256 and TS128r rows)
3. RSS depends only weakly on `threads=` (~40–50 MB per thread); the 240 GB is the rules + muF caches. — (evidence:
   `rss_vs_threads.png`)
4. Wall-time comparisons of AD fits on submit82 are only meaningful at similar node load (factor ~2 noise); compare
   CPU-seconds, or pair runs back to back. — tell the orchestrator; candidate for `knowledge/10_environment/big_memory_jobs.md`.

---

## Open questions

- TS16 not run (budget; 32–128 already on the ideal line, so it extrapolates to ~2× TS32, about 55 min).
- Does 256 scale on an idle node? Not testable here without exclusive access. Not needed for the recommendation.
- `[minimize]` with `--minimizerMaxiter 5` from this seed leaves a non-positive-definite Hessian, so the jobs exit 1
  after the timing; if this recipe is reused for timing, use a smaller (conditional-σ) kick.
