# NNLOJET production — optimization backlog for the next run

Collected during the as118_ptz5 campaign (2026-07-14/15, see
`studies/nnlojet-lowqt-cut/LOGBOOK.md`). Ranked by expected payoff.
Status: IDEA (not started) / APPROVED / DONE / UPSTREAM (needs dokan PR).

## 1. Reuse warmup grids across variants — HIGH, saves ~1 day per run (IDEA)

The ptz5 warmup cost ~1 calendar day (serial VEGAS rounds, 8h-capped jobs).
That cost is per-*setup*, not per-run: the as116/as120 ptz5 variants have
nearly identical integrands (αs member change is a small perturbation), and
VEGAS grids affect efficiency only, never correctness — warm-starting from
this run's converged grids is standard practice. dokan has no built-in
warm-start; needs a small feature (copy `raw/warmup/<part>/` grid files +
seed DB rows) or a manual recipe. Prototype BEFORE launching the next
variant.

## 1b. Local-policy warmup phase — kills the whole grid-failure class (IDEA)

Warmup = ~200 serial single-core VEGAS chains → fits a 64-core submit node
(parallel across parts, serial within). Everything that hurt the ptz5 warmup
was grid-specific: evictions restarting rounds from zero (~12 h lost),
slow-node lottery (RRa_4/RRb_11 tails), schedd-blip zombies (the wedge).
Recipe: run warmup+preproduction with `--policy local --local-cores N`
(inside the container on a submit node), then kill and resubmit
`--policy htcondor` for production (policy is stored per job row; new jobs
take the config policy — verify on a test run dir first). Combine with item 1
(grid reuse) — reused grids may skip most rounds anyway. Mid-run contingency
this campaign: if a grid warmup job must be redone, run the round manually in
the container and `doctor --scan-dir` the output in, instead of respinning
the grid lottery.

## 2. Per-part production dispatch (kill the Entry barrier) — ~20 h per run (UPSTREAM)

`Entry.run()` waits for ALL parts' pre-production before dispatching any
production (`yield preprods` → `MergeAll` → dispatch). On this run LO/V/R/VV
sat idle ~20 h waiting for the last RRb warmups. `MergePart` is per-part, so
per-part dispatch looks feasible; the all-parts barrier appears to be a
design simplification. File with aykhuss.

## 3. Zombie-job reconcile (deadlock bug) — robustness (UPSTREAM)

Jobs that finish while the schedd is unreachable (SECMAN blips on an
overloaded submit06) miss their done-transition permanently: DBRunner only
queries the live queue, never condor_history nor the on-disk output. 11 such
zombies deadlocked the controller overnight (2026-07-15 01:43). Fix: DBRunner
fallback to condor_history and/or periodic reconcile-from-disk (the doctor
mechanism, run in-loop). Until fixed: watch for log-silence (wedged ≠ gone).

## 4. `periodic_remove` for hung jobs — one template line (DONE 07-15, Luca OK'd; in the ptz5 run template pre-fan-out)

RRa_4's glidein ran 19 h against an 8 h wall; needed a human `condor_rm`.
**Threshold caution (07-15):** legit RRb round-7 completions reached ~11.8 h
on slow glidein draws (the "8 h" sizing is an estimate from a different
node's rate — slow node ⇒ proportional overrun; the 2.4 h "round average" was
survivor bias from fast nodes). A 10 h cut would have killed jobs that were
about to finish (and RRb_11's 12 h removal was likely premature). Use ≥2× the
sizing wall: `periodic_remove = (JobStatus == 2) && (time() -
JobCurrentStartDate > 16*3600)`. Held-job lesson from RV_27: a held/hung condor
job's DB row stays `running` forever; resurrection only re-resolves after the
condor entry is removed → auto-removal also prevents that class of stall.

## 5. OpenMP NNLOJET build → multicore warmup — latency only (IDEA)

The binary in `wmassdevrolling:v46_patch0` (`/opt/nnlojet/bin/NNLOJET`) is
single-threaded (no libgomp/pthread linkage — checked 2026-07-15).
`RequestCpus = 1` is correct for it. An OMP-enabled rebuild would cut warmup
*round* wall-time ~N× (the serial-latency problem), useless for production
(already parallel across seeds; 1-core slots also schedule much better on the
busy pool). Only worth doing if warmup latency still hurts after item 1.

## 6. Warmup-specific runtime cap (IDEA)

RRa_28/RRb_15 stopped un-converged at RUNTIME: next round (1.6e7 pts) needed
~16 h vs the global 8 h `job_max_runtime`. A warmup-only longer cap (or
multicore, item 5) would let the hardest RR grids converge fully. Cost of not
doing it: efficiency loss on ~2/206 parts (production auto-compensates with
more jobs) — small; low priority.

## 7. Gen-level rapidity cut (PHYSICS DECISION, low priority)

Runcard has no `yz` selector: full |y| integrated, histograms bin to ±5.
|y|>2.5 carries ~10–15% of σ; |y|≳3 is invisible to the fit (muon acceptance)
and PDF-edge (x→1) sampling adds weight variance. A `select yz` cut would
save ~10–15% CPU and slightly concentrate the VEGAS grid — but y is a smooth
direction (no singular structure), warmup convergence evidence shows the
tails are NOT the hardness driver, and the cut touches make_theory_corr Y
coverage + SCETlib matching convention → validation cost likely exceeds the
win. Revisit only for a from-scratch campaign.

## 8. Eviction exposure (NOTE)

Warmup jobs don't checkpoint; an overnight eviction restarted 7 near-final
RRb rounds from scratch (~12 h lost). Shorter rounds (item 5) shrink the
exposure window. Site-level knobs (non-preemptible slots) unexplored.

## 9. Watcher hardening (DONE — v4 deployed 07-15)

mergewatch missed the deadlock: it checked process existence, but wedged ≠
gone. v3 added LOG_STALE>30 min — but that FALSE-POSITIVES in quiet phases:
the htcondor executor polls every 30 s and logs only on events, so long
silences with few in-flight jobs are normal. The true wedge signature is
**condor-queue count ≠ DB active count, sustained** (finished jobs sitting
uncollected = zombies). v4 triggers on MISMATCH over 2 consecutive ticks
(10 min) + MERGE/HELD/GONE; LOG_STALE is informational only.

## 3c. Dispatch-floor deadlock for low-success parts (FIXED in hdf5-prod 6997c0f; UPSTREAM PR needed)

Parts with nsuc < jobs_batch_unit_size/2 (e.g. single-probe pre-productions)
could never dispatch: 2x registration ramp caps their queue at ~2*(nsuc+
inflight) < the unit-size dispatch floor (10) → stuck QUEUED until the
end-of-budget drain. Hit 58 parts on as118_ptz5 (07-18). Fix (committed
6997c0f on hdf5-prod): per-part floor = min(unit_size, ramp ceiling).
ACTIVE ONLY AFTER the next controller restart from this worktree; until
then the config workaround jobs_batch_unit_size=2 covers the running
campaign (revert config to 10 at the restart that picks up the code fix).

## 3b. Per-cluster condor_q polling melts the schedd at scale (UPSTREAM, URGENT for big runs)

At ~530 in-flight batches, hdf5 dokan runs one `condor_q -json <cluster>` per
batch every `htcondor_poll_time` (default 30 s). Each query forks a ~4 GB
schedd worker that scans the ENTIRE queue (290k ads); the schedd caps at 40
workers; queries take minutes and stack up client-side (admin measured 143→157
concurrent condor_q in 30 s) — a feedback loop that saturated submit06 on
2026-07-16: collections stalled ~9 h (DBRunners blind), 2.8k completed jobs
unreaped, our running slots collapsed 4.7k→471, admins traced it to us.
Mitigation applied: poll_time 30→600 s — NOTE it is SNAPSHOTTED per batch in
job.tmp at dispatch; config change alone does not touch in-flight batches
(patched all 534 by editing job.tmp with the controller down).
Real fix (file with aykhuss): ONE batched `condor_q` for all clusters (or
`-constraint 'Owner==\"lavezzo\"'` once per cycle), shared across executors.

## 10a. Dispatch cadence — the old 25% duty cycle explained (DONE upstream)

Old fork `_dbdispatch.py:256`: at the concurrency cap the dispatcher slept
`0.1 * job_max_runtime` = **48 min** (8h jobs) before rechecking — slots
freed by finishing jobs sat idle for up to a refill cycle. hdf5 clamps all
dispatch/poll intervals to [10 s, 300 s] + wakes on merge signals → expect
much better than the as116/as120 ~25%. NOT wave-based: top-up model, no
global wait-for-slowest. Estimates don't throttle mid-run submission (1/√N
projection only stops the endgame), so "pessimizing estimates" is not a
utilization lever.

## 10b. Batch-tail utilization loss — measure first (IDEA)

Batches (~97 jobs at cap 10000 / 206 parts) are ATOMIC and single-part
(DBRunner raises on mixed part/mode; pre-production sizes every part's jobs
to the same ~8 h wall — slow parts get more jobs, not longer ones). A batch
holds its full concurrency claim until its SLOWEST member finishes, so
intra-batch spread (node heterogeneity ×1.5–2 on glideins + MC luck) wastes
maybe 20–40%. Likely the leading residual inefficiency post-hdf5. Signature
in utilization_trace: condor occupancy sags, DB QUEUED = 0, DBRunners holding
finished jobs. Fix if confirmed: smaller `jobs_batch_unit_size` (finer slot
release, more schedd transactions). Read the trace before touching it.

## 10. hdf5 `doctor` semantics (DONE — documented)

Not a passive check: shares the submit code path (clear log, purge queued,
RECOVER+resurrect) + doctor-specific deletions; safe ONLY with the controller
down. Piped blanket `y` answers made doctor *remove* in-flight jobs' DB rows
(2026-07-15) — answer prompts deliberately. `--scan-dir` re-imports on-disk
job output into the DB (the recovery tool for untracked-but-landed jobs).
Runbook item 1 rewritten accordingly; `tools/run_status.py` is the passive
check.
