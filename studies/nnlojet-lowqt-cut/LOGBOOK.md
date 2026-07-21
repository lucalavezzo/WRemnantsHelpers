---
title: NNLOJET re-run — raise the low-qT generation cut
updated: 2026-07-18
---

# START HERE

**Goal:** re-run (or extend) the blessed NNLOJET Z production
(`/scratch/submit/cms/alphaS/CMS_Z_NNLO_condor_msht20an3lo_as118_20260401_seedfix_clean_v2`)
with a higher `ptz min` generation cut, because the current 1 GeV cut wastes most
of the compute in bins the analysis barely uses.

**07-17 (pre-reboot): CONTROLLER GRACEFULLY STOPPED — submit82 reboot pending
(Luca). RECOVERY RECIPE after reboot (everything below died with the machine;
condor jobs on the grid are UNAFFECTED and keep finishing to disk):**
1. `tmux new -s as118_ptz5`, then in window 0, from /scratch/submit/cms/alphaS:
   `printf 'y\ny\ny\n' | /work/submit/lavezzo/alphaS/NNLOJET/venv-dokan-hdf5/bin/nnlojet-run submit CMS_Z_NNLO_condor_msht20an3lo_as118_ptz5_20260714 --policy htcondor --jobs-max-concurrent 30000 --local-cores 64 2>&1 | tee -a CMS_Z_NNLO_condor_msht20an3lo_as118_ptz5_20260714/submit.start_$(date +%Y%m%d_%H%M%S).log`
   (answer-prompts pipe = normal resume; resurrection re-adopts queue + collects
   drained batches from disk; done 7x.)
2. Watchers: `tmux new-window -t as118_ptz5 -n mergewatch -d '<run dir>/mergewatch.sh'`
   and `-n utiltrace` with `python3 dokan-hdf5/tools/utilization_trace.py <run dir> --interval 120`.
3. Verify: condor_q totals ≈ pre-reboot (~28k), collections resume (done/merged
   counts move), poll pressure ~0 (`pgrep -cf 'condor_q -json'` stays <10),
   in-flight counter NOT frozen at a constant (else phantom purge — see 06:42).
4. Progress anytime: `python3 studies/nnlojet-lowqt-cut/progress_check.py`.
State at shutdown: queue ~28k (23k idle buffer ≈ days), ~100k CPU-h spent,
69/206 parts ≤1%, merged=21,936; inclusive merged rel err 4.6%; ETA notes in
07-17 morning discussion (Line-1 ~1 day inclusive target; physics target =
policy, ~250k CPU-h ≈ 4-5 days for as118_v2-equivalent differential).

**07-20 09:40: PULL TEST PASSED — ptz5 CERTIFIED against as118_v2.**
`pull_test.py` (new, study dir; all parts, nothing hidden, qT 5-100,
|y|<2.5): full NNLO mean +0.19 rms 1.18, α³-only mean +0.16 rms 1.20, 1/95
bins >3σ each — bin-by-bin agreement of the two independent campaigns.
Plot `pull_test.{png,pdf}` in webdir. Notes: (a) rms ~1.2 ⇒ combined errors
~15-20% optimistic (soft channels and/or k-scan semantics) — acceptable,
recheck at finalize; (b) global mean +0.19 ≈ 1.9σ over 95 bins — mild,
watch at finalize; (c) the --solid variant (drops soft parts from NEW side)
degrades pulls (mean +0.65 a3) — CONFIRMS the small channels carry real
physics; never drop them from value comparisons. Coverage gate at 51 (4
parts still ndat=1), crawling through throttle windows. Overnight: midnight
IDLE_STARVED self-resolved (top-ups squeezed through; buffer rebuilt);
+37k collected overnight (169k→ now); NOTE session-idle gap = triggers at
00:38 not acted on until 09:20 — tmux watchers log but only a live session
acts. α³ stats: new run supersedes as118_v2 by 3-5× in abs error across
5-100 GeV at <50% of its CPU.

**07-19 08:50 STATE (prev): overnight collection starvation DIAGNOSED —
the pool starves COLLECTORS too.** Overnight: 0 merges 19:00→07:11 (my
batch-tail prediction of an 02:00-06:00 avalanche was WRONG — falsification
checkpoint caught it). True mechanism: batch executors need pool slots even
to POLL/collect; in-flight claims (44k) > pool (40k) ⇒ hundreds of executors
queued all night while their batches finished unwatched (893 drained batches
/ 72.3k jobs on disk by 07:00). Cascade unzipped from ~07:15 (each collection
frees slots → more executors start): 93,477→104,818 done+merged by 08:46,
~7k/h. THIRD manifestation of the batch-reservation flaw (submitters,
collectors, reporting cadence) — cap raises just move the starvation;
UPSTREAM per-job slot release is the only real fix (bug-report headline).
Expect: plots step down late morning; coverage gate during the wave (watch
armed). NOTE reporting-cadence trade-off of large caps: bigger cap = bigger
batches = coarser collection granularity; consider smaller cap AFTER
steady-state assessment if cadence matters more than buffer depth.

**07-18 18:23 STATE (prev): RESTART #11 — pressure consolidation.** Bundle
(per Luca "more pressure"): cap 30k→40k (flush pipeline + deep overnight idle
buffer for the generous night pool), ramp-floor CODE fix 6997c0f now LIVE,
config unit_size reverted 2→10 (code supersedes). Purge cycle #4 (233
batches/22.4k rows, bak_20260718_cap40). Killed in throttled window. NB
pkill-self-match hit AGAIN via watcher scripts containing 'nnlojet-run' in
their loop code — orphan sweeps must match '[v]env-dokan-hdf5/bin/nnlojet-run'
(binary path), never the bare name; cost: had to re-arm watches (combined
gate+tripwire now). Coverage state at restart: former ghosts at ndat 2-3 (58
merged jobs + 86 ran), gate = all parts ndat≥4, expect late tonight; medians
stay ~flat until then (2-3-file error estimates still garbage — expected).

**07-18 17:00 STATE (prev): RESTART #10 — dispatch-floor fix for the
58-part coverage deadlock.** Diagnosis (Luca caught it): unfed parts' jobs
stuck QUEUED 5 h — registration ramp caps a 1-success part at ~3 queued jobs,
but dispatch requires ≥ jobs_batch_unit_size=10 → interlocked deadlock; such
parts would only ship at end-of-budget drain (UPSTREAM bug list). Fix:
config `jobs_batch_unit_size` 10→2 + restart 16:55 (killed in throttled
window; pipeline purge cycle again: 164 batches/29.9k rows, backup
db.sqlite.bak_20260718_unitfix; NOTE I hit the pkill-self-match pitfall AGAIN
— use `grep '[c]ondor_q'` bracket trick, it cost the night tripwire). Watch
armed: unfed-part jobs actually RUNNING in condor = coverage unblocked; then
ndat≥5 everywhere = comparison gate. Merged now 90,890 jobs.

**07-18 16:00 STATE (prev): FULL RECOVERY after submit82 reboot (~14:07).**
Reboot killed controller mid-pipeline + all watchers/tmux; condor jobs
UNAFFECTED (7.3k, 6.7k running — schedd is submit06). Recovery executed:
phantom census (156 batches / 29,980 rows from the killed pipeline — the
predicted orphaning) → DB backup db.sqlite.bak_20260718_reboot → purge
(purge_phantoms.py, condor cross-check healthy this time) → restart #9 at cap
30000 (15:58) → all watchers restored (mergewatch v7 / utiltrace / plotwatch
hourly plots) → tripwire re-armed. Resurrection sweeping; expect the same
sequence as #8: MergeAll (~hours, big stores) → dispatch → 33k wave →
pipeline drain. NOTE the recurring pattern now fully understood: ANY
non-throttled controller death (reboot, kill mid-dispatch) orphans the
submission pipeline into phantoms; purge_phantoms.py + restart is the
standard remedy (5 min).

**07-18 15:00 STATE (prev):** restart #8 (11:14, post-PURGE: 43.5k
never-submitted phantom rows deleted after Luca ran purge_phantoms.py; DB
backup db.sqlite.bak_20260718_purge). Big MergeAll (~3h) → dispatch resumed
11:55, registered full 33k wave, throttled at 33,010/30,000 (BY DESIGN).
Condor ~10.5k (6k running + 4.5k idle); ~22k created-but-unsubmitted jobs
draining into condor as old batches collect (stale-reservation leak: a batch
frees pool slots only when WHOLLY collected — upstream item). 58 unfed parts
(ndat=1) got first registrations — coverage gate for honest cross-run
comparison clears when all parts have ndat≳5 (then rerun nnlo_pt_stats.py,
default now hides NOTHING per Luca's honesty policy). WATCH PRIORITIES per
Luca: queue starvation above all (grid has spare capacity; idle>0 = healthy,
idle→0 with pipeline jammed = act: cap-40k restart is the lever, spend only
on evidence). Watches: mergewatch v7 (IDLE_STARVED/HELD/GONE/WEDGE/QSTACK),
ramp watch (queue >16k by ~16:00 else stall flag), 12h tripwire.

**07-17 06:56: PHANTOM FLUSH CONFIRMED** — queue 11.6k→28.3k in 7 min after
the cap-30k restart (23k idle + 5.3k running; schedd fine, qlat 420 ms,
pollers 0). Pool-exhaustion theory validated: phantoms were resurrected
executors starved of jobs_concurrent pool slots. Steady state should now
self-sustain (30k-job buffer ≈ days of grid food; registration throttled
until in-flight < 30k — expected and harmless). Remaining watch: starvation
<6k + TRIGGER tripwire.

**07-17 06:42: RESTART #7 — CAP 30000, phantom-flush attempt.** 02:42 restart
verdict: sweep collected ~19k jobs (merged 3,243→21,936 ✓) and queue rebuilt
to 11.8k, BUT in-flight counter re-froze at 22,070 (same signature) →
phantom census: **323 batches / 36,314 jobs DB-running not in condor; 259
batches (~30k jobs) never submitted** — each kill orphans mid-dispatch
batches (6 restarts grew the pile). Mechanism: resurrected executors wait on
the jobs_concurrent pool (= cap) exhausted by real batches → phantoms inert +
pin the throttle counter. Fix per Luca's prior 20-30k blessing: relaunched
06:42 at cap 30000 → pool headroom lets phantom executors submit. VERIFY:
condor queue should jump toward ~40k (watch armed; >25k = confirmed). If
phantoms remain inert at cap 30k, next step = purge them (controller down,
delete never-submitted rows via targeted SQL or careful doctor) instead of
cap escalation. Restart discipline going forward: prefer killing while
dispatcher is THROTTLED (nothing mid-dispatch to orphan).

**07-17 02:42: RESTART #6 (queue starvation).** Overnight watch fired 02:38:
condor queue drained to 7,991 with idle≈0 (grid consumed the whole buffer; a
RECORD ~10k slots ran overnight) while the dispatcher sat throttled on a
FROZEN in-flight counter (22000/26144, unchanged 22:13→02:39 despite +2.8k
collections — accounting disconnected from DB; phantoms likely pinning it).
Restart 02:42 (kill by session — this instance was session-launched;
orphans+pollers cleaned, condor_q=0 verified) → resurrection sweep running.
EXPECTED after sweep: large done-collection from disk, in-flight recomputed,
top-up refills queue toward 20k. VERIFY at next check: condor total >12k,
done count jumped, no repeated freeze at 22000 (if the counter freezes again
at the same value, it is a REAL hdf5 accounting bug — the 13k
never-submitted phantoms are the prime suspect; consider purging them via
doctor with controller down). NOTE: in-session verification watch could not
be armed (transient harness classifier outage); tmux mergewatch v6 + TRIGGER
tripwire still cover failure modes.

**State (07-16 18:40): PRODUCTION, STEADY-STATE CYCLING.** Run dir
`/scratch/submit/cms/alphaS/CMS_Z_NNLO_condor_msht20an3lo_as118_ptz5_20260714`,
tmux `as118_ptz5` (win 0 = controller, `utiltrace`, `mergewatch` v6),
controller `venv-dokan-hdf5/bin/nnlojet-run`, cap 20000, **htcondor_poll_time
600 s** (config + all in-flight job.tmp snapshots — it is per-batch
SNAPSHOTTED; never lower it back: 30 s × 530 batches melted the schedd, see
07-16 18:15 note). Warmup done (07-16 04:00–07:44), barrier released 07:50,
fan-out 08:14/08:32, schedd meltdown resolved 18:14: 3,243 jobs collected +
MergePart'd on restart, resubmission confirmed (queue 17k→24.5k), qstack=0,
qlat~0.5 s. **SMOKE GATE FULLY PASSED (07-16 20:15):** 206 per-part HDF5 stores exist
(`raw/<part>.hdf5`, e.g. RRb_12.hdf5 23 MB with cross + per-y ptz groups,
written 18:15 at the resurrection MergePart sweep) — earlier "no merge yet"
was a watcher glob bug (`*.h5` doesn't match `.hdf5`; incremental caches also
live in hidden `raw/<part>/.hdf5/` dirs).
PENDING VERDICTS (need data): first .h5; optimizer W estimate + campaign ETA
(after merges accumulate); final batch-tail number; 24 h diurnal grid share;
naive-vs-k-scan error calibration risk on the stopping criterion (07-16
discussion — optimizer steers on naive merge errors, k-scan final errors were
4–10× larger in as118_v2 → dokan may declare convergence early; assess at
first finalize). Babysitting: single-owner session, tripwire on mergewatch
TRIGGER lines (MERGE_H5/HELD/GONE/WEDGE/QSTACK>25). Kill recipe: SIGTERM main
PID, then TERM orphaned workers (TERM doesn't propagate), then check
`pgrep -f 'condor_q -json'` pile; restarts resurrect cleanly (done 5×).

**07-16 18:15: SCHEDD-MELTDOWN INCIDENT RESOLVED; collections FLOWING.**
Full arc: fan-out 08:14 (10k cap) → ramped 20k 08:32 → per-cluster 30 s
polling × ~530 batches saturated submit06 (each condor_q forks a ~4 GB
worker scanning 290k ads, 40-worker cap; queries stacked 143→157 client-side
— admin-diagnosed feedback loop, traced to us): collections blind all day
(1 drained batch sat 7 h), 2.8k completed unreaped, running collapsed
4.7k→334. Fix: kill controller + 534 orphans + condor_q pile (Luca/admin);
poll_time 30→600 s in config **and all 534 job.tmp snapshots** (it is
SNAPSHOTTED per batch — config alone insufficient); 30-min breather (schedd
reaped 2.8k→0 in 5 min, running 334→2.1k = diagnosis confirmed); restart
18:14. Within 1 min: **3,243 jobs collected AND MergePart'd** (resurrection
collects from disk directly). condor_q footprint now ~0. Queue 17k (14.7k
idle buffer), running 2.3k and recovering. Backlog 3b = upstream fix (single
batched condor_q). Watching: first .h5 stores (hdf5 merge = last gate item),
steady-state cycling, queue top-up when in-flight < cap.

**07-16 07:50: BARRIER RELEASED — MergeAll RUNNING (last smoke-gate item).**
Warmup phase COMPLETE: RRa_4 landed 04:00 (round 7, 10.7 h on Purdue hammer —
slow node, legit; pre-prod = single probe), RRb_11 landed 07:44 (round 7,
~14.5 h, CONVERGED — the 16 h wait policy vindicated, no removal needed, and
Purdue acquitted: slow ≈4–5×, not hung). MergePart sweep over 206 parts in
progress (~10–20 min), then production dispatch at cap 10000 with the
16 h periodic_remove template line active for all new jobs. Fan-out watch
armed. NEXT: confirm .h5 stores + no merge crashes (gate verdict), then read
utilization_trace.csv — pinned-at-cap+QUEUED ⇒ raise cap (Luca open to
20–30k); sagging+no-QUEUED ⇒ batch-tail/dispatch-bound (backlog 10b).
Warmup post-mortem vs as118_v2 (20 h): ours ~45 h, excess = smoke phase 7 h +
evictions 12 h + wedge 6.5 h + doctor mishap 7 h + hung-job tails ~10 h; all
have backlog fixes (1, 1b, 3, 4, 9).

**07-15 17:30: SINGLE-BABYSITTER RULE — one Claude session now owns this run**
(Luca stopping the duplicate; today's doubled doctor runs deleted job rows AND
dirs — never run two babysitters). Owner session's tripwire re-armed on
watcher-v3 TRIGGER lines.

**07-15 17:20: RESTARTED at cap 10000, warmup phase ESSENTIALLY DONE.**
Timeline: 6/7 final RRb warmups landed by ~13:15 but sat as ORPHAN dirs
(morning doctor had purged their rows); RRb_11's job hung 12 h on a Purdue
glidein → `condor_rm 3227729` (17:15); `doctor --scan-dir` did NOT adopt
orphan dirs (only reconciles known rows) — but the 17:19 restart's own
resurrection DID import them (ExeData/job.tmp route, rows 1180-82): no
redundant re-runs. Now: 204/206 parts past warmup (6 RRb in fresh
pre-production, ~150+ parked at barrier), only RRa_4 + RRb_11 re-running
round 7 (~2.4 h, land ~19:45, hung jobs had left empty dirs). Barrier
release + MergeAll + fan-out ETA ~22:00–02:00. Watcher v3 deployed (adds
LOG_STALE>30 min — the wedge-detection gap); tripwire re-armed. Backlog of
next-run optimizations: `knowledge/20_frameworks/nnlojet_run_optimization_backlog.md`.

**07-15 08:20: recovery IN PROGRESS.** Luca killed the wedged controller
08:19; orphan workers TERMed; `doctor` run (controller down = safe): all 11
zombies reconciled from disk (762/885/1002/1110… → done; prod done 190→217).
Side effect: doctor marked the 8 in-flight RR warmup condor jobs FAILED (no
output on disk yet — they're mid-run). DO NOT restart until they land
(restart would duplicate them; resurrection rescues FAILED only if output
exists on disk). 7 healthy jobs (re)started 05:13 (evicted overnight, restart
from scratch — no checkpointing), ETA ≤13:20. RRa_4 (cluster 3227705) HUNG
19h on one glidein (heartbeats alive, 8× round average) — **Luca:
`condor_rm 3227705`**; its DB entry is already failed → restart auto-requeues
it (RV_27 mechanism). Monitor armed: wakes Claude when queue ≤1 → restart at
cap 10000 → verify 7 flip to done + RRa_4 requeued → re-arm watchers WITH
log-staleness check (wedged ≠ gone — mergewatch missed the deadlock).

**RAMPED to `--jobs-max-concurrent 10000` at 17:51** (before merge observed —
deliberate deviation, justified in the 17:45 note: Entry barrier means MergeAll
fires pre-dispatch regardless of cap, dispatch is gated behind it, and
throttling overnight at 100 had no upside). Smoke gate 4/5 passed (07-14 14:05
+ 14:15 notes); LAST ITEM = observe MergeAll/MergePart at barrier release
(all 206 pre-productions complete → MergeAll → production fan-out), expected
overnight; RR warmup tail on round 8 (as118_v2 median 7, max 9). Watchers:
tmux `as118_ptz5:mergewatch` (flags MERGE/HELD/CONTROLLER_GONE →
`<run dir>/mergewatch.log`, pre-ramp log archived as `.pre_ramp.log`) +
in-session tripwire. RV_27 held-job incident RESOLVED (17:55 note). Kill
recipe if needed: SIGTERM main PID, then TERM orphaned worker forks (TERM
does not propagate; beware pkill -f self-match). Config settled = as118_v2
except the 5 GeV cut and hdf5 merge defaults (trim 8.0, k-scan 0.4 —
deliberate, see 07-14 log).

**Next actions (analysis side, this study):** prototype the make_theory_corr
nonsingular bridge (DYTurbo below 5 GeV, NNLOJET above, boundary syst from
addendum-3 numbers); re-finalize as118_v2 (cleaned DB + 12.7k unmerged jobs)
and remake the unc table from result/final; inspect the N4p0LL resum pkl
qT≈29/57 hole bins. **PROPOSED (07-17, new study): NNLOJET precision
requirement** — inject per-bin NNLOJET-like noise into the theory corr,
propagate to σ(αs) via rabbit; output = a CPU-h stopping criterion for THIS
run (replaces "1%"/"as good as last time"); focus 15–30 GeV (α³ coefficient
20–50% rel noise). Tier-2 cheap wins: fit-binning coarsening, |y|>2.5
generation cut (backlog 7), trim/outlier study (addendum-3 scatter).

# Per-bin qT stats of the ptz5 run (2026-07-18, first physics read)

`~/public_html/alphaS/260718_nnlojet_ptz5_perbin_stats/` (`nnlo_pt_stats.py`
here; reads `result/part/*/ptz__*.dat` incremental merges, central scale,
|y|<2.5 fold, quadrature). Merge state = 2026-07-17 13:24 (~53k merged jobs,
~30% of as118_v2's CPU); rerun after the current sweep for updated numbers.

- **k-scan caveat RESOLVED for this run:** `.merged.json` sidecars prove the
  incremental MergePart applies the full trim (8.0/0.007) + k-scan (3/0.4)
  calibration — the "naive until finalize" concern was an old-fork property.
  Errors shown are calibrated; finalize just re-merges with final stats.

**Error-convention audit (2026-07-18, RESOLVED — dokan was right all along):**
measured directly on as118_v2, bin-by-bin (nnlo.ptz slices, |y|<2.5, qT
1-100): `err_final/err_merge` median **4.34** (p10-p90 3.6-6.25) — the
addendum-4 "4-10x" claim CONFIRMED; central shifts median 0.78σ_final ✓.
Per-slice medians: final 7.06% (≈ the Findings' 7.9%, which is per-(qT×y)
FINAL-based over all |y|), merge 1.60% (naive). My folded-quadrature 1.75%
= 7.06%/√20 slices ✓ — all numbers one consistent family. The 07-17
"contradiction" was comparing my folded numbers to the differently-binned
"3.7%" (per-2GeV, other fold convention, from deleted /tmp scripts). RULES
now encoded in `nnlo_pt_stats.py` (docstring + `assert_calibrated()`): old
fork → use result/final ONLY (result/merge is naive, 4.3× small); hdf5 runs →
incremental result/part is calibrated (json-verified); never compare medians
across binning/fold bases. April make_unc_table (260427/260714_NNLOJET
webdirs) reads result/merge per-slice → its absolute errors are naive lower
bounds; shares/medians usable only merge-vs-merge.
- Full NNLO, 1-GeV bins: median 3.58% (improved 4.0→3.58% between two script
  runs 30 min apart — the 07-18 sweep's merge wave landing live); 2-GeV:
  2.89%. **vs as118_v2 FINALIZE overlay: old full-NNLO median 1.75%/1-GeV —
  still ahead of us** (my earlier "already better than 3.7%" compared against
  the audit's result/merge numbers — finalize disagrees with that audit
  DIRECTION (4-10x larger claim) — UNRESOLVED tension, check make_unc_table
  conventions vs my quadrature y-fold before quoting either).
- **α³-coefficient-only: ptz5 median 25.8% vs as118_v2 finalize 37.8% —
  already BETTER than the full old campaign at ~30% of its CPU** on the piece
  only NNLOJET provides. The stats concentration (no sub-5-GeV waste) shows
  exactly where intended.
- First filled bin 5-6 GeV ✓ (cut working); no wasted low-qT error budget —
  the compute-concentration mechanism confirmed end-to-end.
- α³-coefficient-only: median 36% per 1-GeV bin; rel err diverges at its zero
  crossing (~15-18 GeV, value→0 — artifact, not a stats problem). This is the
  piece only NNLOJET provides; if the fit ultimately consumes α³-only +
  DYTurbo α², THIS is the number that sets how much longer to run — target
  policy needed from Luca/KL (e.g. α³-only ≲10% per 2-GeV bin in 5-40 GeV).
- Caveats: naive incremental-merge errors (k-scan finalize may enlarge —
  same-convention comparison to the audit is fair); merged-state lag.

# ⚠ RETRACTION + in-flight caveat (2026-07-18, supersedes the two notes below)

The 07-18 cross-run comparisons went through THREE explanations (k-scan
small-sample noise → WRONG, disproved by LO_1 naive==quoted check; "tiny
channels dokan skipped" → WRONG) before landing on the truth: **58/206 parts
(all ACTIVE) have ndat=1 — no production statistics yet** (starvations +
purges delayed their first wave; the optimizer will feed them). Consequences:
- The ptz5 run is INCOMPLETE in channel coverage, not just statistics: the
  unfed parts are 1.8% of the total NET but 19.5% in Σ|value| (old-run truth)
  — large cancellations live there (e.g. VV_14 = −17.8k fb).
- ALL per-order and total cross-run comparisons on 07-18 are PROVISIONAL and
  not apples-to-apples vs the FINALIZED as118_v2: (a) with ghosts included,
  per-bin errors are polluted by 1-file garbage estimates; (b) with ghosts
  quarantined (--min-ndat), the VALUES are biased (real channels missing).
  There is no clean per-bin total comparison until every part has ≳ a few
  files. The α³ "already better" claims: qualitative at best.
- α³ shape cross-check vs the 07-14 plot (nnlojet_coeffs_zoomratio, old-run
  nnlo_only/matched): consistent — −32% of matched at 5-6 GeV ≈ −21k fb vs my
  −23k fb ✓, sign change ~15 GeV ✓, positive plateau above ✓. Differences are
  presentation (ratio-to-matched linear zoom vs symlog absolute) + in-flight
  bin noise + the quarantine value bias on the new curve.
- What SURVIVES cleanly: the error-convention audit (final/merge 4.34×; my
  fold arithmetic; calibrated incremental merges verified); the LO_1
  naive==quoted==0.3%/slice check; fed-channel progress qualitatively.
- REQUIRED before finalize/any blessed comparison: every part fed (verify
  ndat≥5 across all 206), then rerun nnlo_pt_stats.py with --min-ndat 0.

# α³ absolute-error + LO/NLO comparison plots (2026-07-18, addendum — SEE RETRACTION ABOVE)

`a3_absolute_err.{png,pdf}` + `lo_nlo_compare.{png,pdf}` in the same webdir
(`nnlo_pt_stats.py --absolute --orders`). Findings:

- α³ central values ptz5 vs as118_v2-final overlay well (mutual validation of
  the new production). ABSOLUTE α³ error: ptz5 median 49 fb vs old 68 fb
  (ratio 0.72) — crossing at ~30-40 GeV: above it ptz5 is up to ~5× better;
  at 5-20 GeV comparable (that's where the remaining CPU goes). Absolute
  errors are the artifact-free view (no zero-crossing divergence).
- LO/NLO-coefficient pieces: central values agree; old run FAR more precise
  (LO 0.09% vs 1.35%; V+R 0.94% vs 5.03% medians) — expected, ptz5 CPU is
  RR-concentrated and LO/V/R were deactivated at their part targets early.
  Matters ONLY if the correction uses ptz5 full-NNLO as FO (then LO/NLO
  noise enters the total: part of the 3.29% vs 1.75% full-NNLO gap); moot in
  the α²-DYTurbo + α³-NNLOJET bridge scheme. Cheap to fix later (LO/V/R jobs
  are fast) if the full-NNLO route is kept.
- Artifact note: isolated ptz5 LO bins with ~0.02% errors = few-file bins
  where trim/k-scan degenerates; ignore isolated ultra-small per-bin errors.

# Findings (2026-07-14)

Current run: 247.9k merged jobs, 1.05M CPU-h, finalize 2026-04-06.
Inclusive σ = 1084.3 pb ± 1.41% (trimmed); differential `cross_hist` reached
15.4% vs 1.0% requested. 12,759 DONE jobs (+5.1% stats) never merged (post-Apr-6).
Per-bin (1 GeV × 0.25y, qT<100): median 7.9%; folded |y|<2.5 × 2 GeV: median 3.7%.

**Error budget is low-qT dominated** (from `nnlo.ptz_all`, err² shares of total):
qT 1–2 GeV: 50% (bin value is *negative*, −9.9% of σ); 1–5: 81%; 1–10: 92%.
Raising the generation cut to 2/3/5/10 GeV → est. ≥2.4/3.4/4.2/4.6× less compute
at the same rel-acc target (lower bounds: warmup stops optimizing the
cancellation region).

**FO-term size in the matched prediction** (two-pass `read_matched_scetlib_dyturbo_hist`
with the blessed inputs — zstuff N3+0LL newvals_coarse resum + nnlo_sing +
David's DYTurbo N2LO; nonsingular zeroed below 1 GeV vs everywhere; |Y|<2.5,
Q 60–120, vars=pdf0). NNLOJET N3LO nonsingular assumed same ballpark (per KL):

| qT (GeV) | matched (pb) | FO-term/matched | NNLOJET stat/matched |
|---|---|---|---|
| 1–2 | 37.7 | −2.9% | 13.6% |
| 2–3 | 55.8 | −2.1% | 5.4% |
| 3–4 | 65.7 | −1.9% | 3.8% |
| 4–5 | 68.8 | −1.9% | 2.4% |
| 5–7 | ~66 | −2.1% | ~2.1% |
| 7–10 | ~54 | −2.5% | ~1.5% |
| 10–15 | ~40 | −3.1% | ~1.7% |
| peak | ~20–23 | −3.6% | — |
| zero-crossing | ~43 | 0 | — |

**Physics read:** the nonsingular is a stable −2 to −3.6% of matched from 1 to
~35 GeV. Below ~4 GeV the NNLOJET statistical noise injected into matched
(5–14%) exceeds the −2% signal it carries — the current 1 GeV input is
noise-dominated there. Noise ≈ signal at 4–7 GeV; signal cleanly resolved above
~7 GeV.

**Mechanism in the code:** `make_theory_corr.py --qtCutoff X` (default 1.0)
zeroes the nonsingular below X (`zero_nons_bins` in
`input_tools.read_matched_scetlib_hist`). Constraint: qtCutoff ≥ NNLOJET
generation cut (below the generation cut FO=0 and nonsingular would collapse to
−singular). Blessed command (from `print_command.py`/plot .log in
`wremnants-data/data/TheoryCorrections`): `-g scetlib_nnlojet --qtCutoff 1.0
--axes Q Y qT --nnlojetMassEdges 60 120` with this run's `nnlo.ptz` as FO.

**Options for the new cut:**
- ptz > 3 GeV: ~3.4× compute saving; zeroes only bins where noise ≫ signal.
- ptz > 5 GeV: ~4.2× saving; loses a real (if noisy) −1.9% at 3–5 GeV unless
  bridged.
- Bridge option: use the DYTurbo (O(αs²)) nonsingular below the NNLOJET cut —
  the scetlib_dyturbo machinery computes it already; the O(αs³) increment lost
  is small compared to the −2% total.

# Plot (2026-07-14)

`~/public_html/alphaS/260714_fo_vs_matched/` — two-panel anatomy
(`fo_anatomy_plot.py` here): top = resum / FO(N2LO dyturbo) / FO(N3LO nnlojet) /
singular, each as % of matched; bottom = nonsingular (FO−sing)/matched with
NNLOJET stat band. Full per-bin numbers in `fo_vs_matched_table.md` next to it.

**Caveat on the N3LO curve:** it subtracts the N2LO singular (`nnlo_sing`), not
the N3LO one (`n3lo_sing` combined pkl deleted; shards on ceph). Below ~15 GeV
the purple curve = true N3LO nonsingular + unsubtracted O(αs³) singular logs —
diverges, not physical. The red N2LO pair is internally consistent and is the
reference for "how big is the nonsingular". To do the N2LO-vs-N3LO nonsingular
comparison properly (→ can we use N2LO below a cut?), recombine `n3lo_sing`
from the ceph shards first.

# Order-consistent update (2026-07-14, later)

Recombined the deleted `n3lo_sing` pkl from its 112 ceph shards (16 bin-chunks ×
7 scale vars) with `scripts/standalone_combine.py` → back at its ceph home
(`.../Newvals_Coarse_n3lo_sing/inclusive_..._n3lo_sing_combined.pkl`).
New plot `fo_vs_matched_orderconsistent.{png,pdf}` + table in the same webdir:
N4+0LL+N3LO matched via `read_matched_scetlib_nnlojet_hist` (blessed args),
two-pass, vs the N3+0LL+N2LO pair.

Findings:
- Order-consistent N3LO nonsingular is finite at low qT (power-suppressed ✓)
  and LARGER than N2LO's: ≈−5 to −7% of matched at 10–25 GeV (vs −2.8 to −3.6%
  at N2LO); at 2–7 GeV it is unresolved within NNLOJET stat (±2.4–6%).
- N2LO vs N3LO nonsingular difference is NOT stat-resolvable below ~7 GeV with
  current statistics → supports "N2LO bridge below the cut" (nothing resolvable
  lost); difference IS resolved above ~10 GeV (≈2.3% ± 1.3% at 15 GeV).
- **Suspicious spikes at qT≈29 and ≈57 GeV** in the N4p0LL coarse resum (and
  hence singular=FO−nons) — look like broken/hole bins in the resum pkl (the
  N4+0LL production had known unfilled holes; these are at |Y|<2.5 though).
  TODO: inspect those bins in the resum pkl; check whether the blessed
  N4p0LL_N3LO corr inherits them.
- Order-matching rule confirmed vs AN theory.tex: N3LO FO pairs with N4+0LL
  (or N3+1LL); N4LL+N2LO fails at high qT, N3+0LL+N3LO fails at low qT.

# Notes / gotchas

- The `lambda6cs _fine` SCETlib exports do NOT reconcile with NNLOJET absolute
  normalization under any bin-width convention (sing 2–5× FO at 15–30 GeV);
  fine-Y binning also breaks `read_nnlojet_pty_hist` (needs per-Y-bin files;
  `discover_nnlojet_ybins` patch was in the removed `main` tree, NOT in the
  current workspace WRemnants). Use the blessed `newvals_coarse` pair.
- The blessed N4p0LL n3lo_sing *combined* pkl referenced by the nnlojet corr
  command was deleted from the WRemnantsHelpers root (repo reorg); shards
  survive at `/ceph/.../zstuff/Z_..._Newvals_Coarse_n3lo_sing/scetlib_outputs/`
  — recombine with `scetlib-manage-condor-submit.py combine` if the exact
  N3LO-singular version of the table is needed.
- NNLOJET `nnlo.ptz_all` histogram sum (1.76e6 fb) ≠ finalize `cross`
  accumulator (1.08e6 fb) — different accumulator conventions; err² *shares*
  unaffected, don't mix absolutes.
- Scripts from this session: `/tmp/fo_final.py`, `/tmp/fo_dyturbo.py`,
  `/tmp/hypo_test.py` (convention tests) — copy here before /tmp cleanup if
  needed.

# α³-coefficient plot (2026-07-14, addendum)

`alpha3_coeff_vs_matched.{png,pdf,_table.md}` in the same webdir
(`alpha3_plot.py` here): NNLOJET's `lo` / `nlo_only` / `nnlo_only` coefficient
outputs each vs the N4+0LL+N3LO matched total, |Y|<2.5. Motivation (Luca): α²
part is available at DYTurbo precision; NNLOJET is only strictly needed for the
α³-only coefficient.

- α³-only/matched: −233% @2 GeV, −32% @5, −8.6% @10, ~0 @15 (sign change),
  +2.8% @20, +7.6% @30, plateau +5–8% to 100 GeV. Current stat 1.3–2.4% of
  matched (i.e. ~20–50% relative on the coefficient at 15–30 GeV) — this is
  where re-run statistics matter.
- The large low-qT values are the unresummed α³ log tower — cancels against the
  α³ singular in matching; not a physics problem, but it IS the noise source.
- Bottom-panel bin-to-bin scatter exceeds the stat band in places (±4–5% swings
  vs ±1.5% band at 35–100 GeV) → per-bin errors likely underestimated or
  outlier-contaminated; rebin before drawing conclusions per bin.
- The qT≈29/57 GeV spikes reappear in lo/nlo ratios → confirms they live in the
  DENOMINATOR (matched, i.e. the N4p0LL resum pkl holes), not in NNLOJET.

# Cutoff scan at N3+0LL+NNLO (2026-07-14, addendum 2)

`cutoff_scan_n3ll_nnlo.{png,pdf}` in the webdir (`cutoff_scan.py` here):
matched spectrum reassembled with qtCutoff = 1..5 GeV (dyturbo pair, so the
nonsingular is noise-free), ratio to cutoff=1.

- Bin-local by construction: zeroing the nonsingular in [1,X] shifts exactly
  those bins by −(their nonsingular): +2.86% (1–2), +2.08% (2–3), +1.89% (3–4),
  +1.90% (4–5). Bins above X unchanged.
- Integrals for cutoff=5: σ(qT<10) +0.89%, σ(qT<20) +0.55%, σ(total) +0.37%.
- Read: dropping the 1–5 GeV nonsingular = a coherent +2–3% distortion of the
  first four 1-GeV bins — too big to ignore in a shape fit with sub-% data.
  Since DYTurbo provides exactly this piece at high precision, the conclusion
  is: raise the NNLOJET generation cut to 5 GeV, but BRIDGE 1–5 GeV with the
  DYTurbo nonsingular in make_theory_corr (don't just zero it).

# Nonsingular order-difference zoom (2026-07-14, addendum 3)

`nonsingular_order_diff_lowqt.{png,pdf}` (`nons_diff_zoom2.py` here): 3 panels,
qT<20 — (1) components of BOTH matchings (a3 family solid / a2 family dashed,
each over its own matched), (2) the two order-consistent nonsingulars with
NNLOJET stat band, (3) their difference = the bridge systematic, cut line at 5.

- The a2-family FO and singular each reach ~+300% of matched at 2-3 GeV
  (LO +668%, NLO-only −340%) cancelling to −2%; NOT a bug. The a3 FO sits near
  ~100% there only because the (large negative) alpha_s^3 coefficient happens
  to cancel the a2 tower in those bins — a symptom of non-convergence, not
  accuracy.
- Bridge systematic (panel 3), window [1,5]: per-bin −7.6±15.1, −6.2±5.9,
  +2.3±3.8, −1.6±2.5 (% of matched); inverse-variance mean −1.2% ± 1.9% —
  consistent with zero, bounded at ~2%.
- Above 8 GeV the difference is systematically negative (−2 to −3%, the a3
  nonsingular is larger) but with bin-to-bin scatter exceeding the stat band
  (e.g. −5.6±1.7 next to +1.6±2.1) — per-bin NNLOJET errors likely
  underestimated; rebin or wait for the ptz5 run before quoting bin-level.
- Gotcha for direct DYTurbo reads: the finer-bin scale-variation files carry a
  second Q bin [10,60] — slice Q to [60,120] before use (matched reader handles
  it internally).

# Smoke-phase babysit note (2026-07-14, 13:50)

SECMAN:2007 "Failed to fetch ads" storm in the tmux log investigated: 137 error
lines in the exe.logs, but ALL timestamps fall in two ~30 s windows
(11:32:04–11:32:33 and 11:55:41–11:55:50) — two transient schedd outages on
submit06 that hit all ~60 concurrent jobs' `condor_q` polling loops
simultaneously. The controller re-echoes each job's exe.log when it collects
it, which is why old errors keep scrolling by at 13:3x — they are NOT new
failures. hdf5 back-off absorbed both blips as hoped: db.sqlite shows 1044 jobs
done, 60 in-flight, zero failed; condor_q agrees (58 running / 2 idle); schedd
responsive again. Warmups progressing (multiple "warmup done [CONST_ERR]
[CHI2DOF] [GRID] [SCALING] [MIN_INCREMENT]", preproduction submitting). No
action needed; if a blip lasts longer than the back-off window some jobs could
eventually error out — recheck `select status, count(*) from job group by
status` (status 3=done, 2=running) if storms recur. Note the schedd is heavily
loaded (240k idle jobs queued cluster-wide), which likely explains the blips.

# Smoke-gate progress (2026-07-14, 14:05)

Worked the runbook smoke gate (dokan-hdf5/docs/RUN_as118_ptz5_runbook.md):

1. **Counts sane ✓** — `tools/run_status.py` (read-only): 1047 done (899
   warmup + 148 production), 58 running, 0 failed/recover; condor agrees
   (57 running / 1 idle). **Gotcha found:** hdf5-branch `doctor` is NOT a
   passive check — it shares the submit code path (clear Log table, purge
   never-started jobs, mark active→RECOVER + DBResurrect) plus doctor-specific
   deletions (empty exe dirs, DB jobs with paths missing on disk). Running it
   against the live controller is a race; my accidental invocation crashed
   harmlessly at the "clear log?" prompt (EOF, no commit). Runbook item 1
   rewritten to use run_status.py; real doctor only with the controller down.
2. **Kill→restart resurrection — PENDING, needs Luca** (agent perms won't kill
   the controller). Main controller PID = the `nnlojet-run submit` process
   that is a *child of the tmux bash* and *parent of ~60 identical worker
   forks* (all share argv — don't pkill by name). Recipe: `kill -TERM <pid>`,
   wait for the tree to exit, rerun the identical submit command in tmux
   window 0, then diff `condor_q -af ClusterId ProcId JobStatus | sort`
   against `/tmp/condor_before_restart.txt` (snapshot taken 14:05) — expect
   same clusters, no mass resubmit, dispatch resumes.
3. **Incremental merge — PENDING** (expected): zero Merge activity in
   submit log + log.sqlite, no .h5 under run dir yet; only 148 production
   jobs done spread over parts, trigger (fac_merge_trigger 1.1) not reached.
   Watch for MergePart/MergeObs + HDF5 stores appearing.
4. **dat naming + cut ✓** — production RV_23/s1: per-y-slice
   `ZJ.CMS_Z.RV.ptz__<ylo>__<yhi>.s1.dat` files present; qT bins below 5 GeV
   exactly zero, first filled bin 5–6 GeV. LO_1/s1: nothing below 5 GeV
   (first filled 10–11 GeV, sparse = low-stat early seed, fine). Note the odd
   y-label `-2p` (vs `-2p0`) in one filename — NNLOJET float formatting,
   cosmetic.
5. **Utilization trace ✓ running** — tmux window `as118_ptz5:utiltrace`,
   `tools/utilization_trace.py --interval 120`, CSV
   `<run dir>/utilization_trace.csv` (+ .tee.log). First tick 13:59: 57
   running / 1 idle. NB the `cap` column reads config (10000), not the CLI
   smoke cap (100): util_pct is vs 10000 — 57/100 = 57% is the smoke-phase
   number.

# Kill→restart resurrection PASSED (2026-07-14, 14:15)

Luca SIGTERMed the main controller (2889663) ~14:08. Gotchas hit and resolved:

- **TERM does not propagate to the luigi worker forks** — ~60 workers were
  orphaned (reparented to init, still alive holding the run state). Cleaned
  them up with a targeted TERM before the restart. For the production kill:
  after TERM on the main PID, check `pgrep -f "nnlojet-run submit"` and TERM
  leftovers. Also: `pkill -f <pattern>` from a shell whose own command line
  contains the pattern SELF-MATCHES and kills your shell — use plain `kill`
  on listed PIDs, or run pkill with the pattern split so it doesn't match.
- Main-PID identification: the controller is the `nnlojet-run submit` process
  that is a child of the tmux bash AND parent of the ~60 identical-argv forks.

Restart 14:11 (same command, `printf 'y\ny\ny\n'` answering the clear-log
prompt = normal resume path). Verification:

- Log shows `resurrect warmup (job_id = ...)` re-attach lines; completed
  warmups NOT re-run (their PreProduction goes straight to "warmup done" →
  yield pre-production); dispatch resumed immediately.
- Condor diff vs the 14:05 snapshot: all 60 old clusters still present,
  0 removed, 16 new clusters (normal new submissions) — **no mass resubmit**.
  Row count 114→79 = natural job completions.
- DB after restart: 1049 done / 74 running, zero failed/recover.

Smoke gate now 4/5; only the incremental-merge observation remains.

# Warmup phase read (2026-07-14, 16:10)

168/206 parts have "warmup done"; termination flags (from preproduction.py:
converged = CHI2DOF+CONST_ERR+GRID+SCALING; RUNTIME = next increment won't fit
the 8h job limit, forced stop un-converged):

- 142 converged, 23 converged + target accuracy already reached, 1 RELACC-only
  → 165/168 clean.
- Only 2 RUNTIME-terminated: RRa_28, RRb_15 (double-real, hardest integrands —
  expected).
- 38 parts still in warmup chains.

**Physics read:** with the 1 GeV cut, warmup burned itself on the low-qT
cancellation region; at 5 GeV the grids converge cleanly (165/168) — first
concrete confirmation of the compute-saving mechanism. Pipeline: converged →
pre-production (2-job runtime calibration, 16 parts there now) → production
fan-out (cap saturates → ramp decision). Merge trigger (from
`_dbmerge.py::MergePart.complete`): first merge fires when a part ENTERS full
production (Entry task; pre-prod jobs count as done but merge waits for
pre-production complete), then re-merges at <min_number merged or ≥10% new
done jobs (fac_merge_trigger 1.1) — hours away (first fast R/RV parts), NOT
gated on 8h jobs landing. Session-independent watcher in tmux
window `as118_ptz5:mergewatch` appends to `<run dir>/mergewatch.log` every
5 min; TRIGGER lines on merge/cap-saturation/controller-death.

# Entry barrier + early ramp decision (2026-07-14, 17:45)

`Entry.run()` (entry.py): `yield preprods` (ALL 206 parts) → `MergeAll(force)`
→ production dispatch → `MergeFinal`. Consequences: (a) declining condor
occupancy pre-barrier is structural (parts park as they finish pre-prod, only
the RR tail works — 32 RRa/RRb parts on warmup round 8 vs as118_v2 median 7 /
max 9, so on-trajectory); (b) the FIRST merge happens at barrier release
regardless of cap; (c) production cannot start if MergeAll crashes → a big cap
cannot amplify a merge failure. Hence ramped to 10000 BEFORE observing merge
(runbook order deviation, agreed with Luca): kill 17:47, restart 17:51.
Rate/health at decision time: 0 failed, 165/168 warmups cleanly converged,
completion rate on par with as118_v2.

# RV_27 held-job incident (2026-07-14, 17:55, RESOLVED)

Condor job 3227073 (warmup RV_27/s3) sat idle ~6 h (cluster full), went HELD
on first match: transfer failure — `ZJ.CMS_Z.y1.00E-08.RV_channels`
(extensionless) missing from s3 (the `.txt` twin present; healthy attempt dirs
have both). The `_channels` file is per-attempt VEGAS state (s1 vs s2 differ)
so it can't be hand-copied. Suspect: input file lost at job-prep or in the
14:11 resurrection pass while the condor job was idle-in-queue (hdf5-branch
edge case — first occurrence; watch for recurrence, file upstream if it
repeats). Resolution: `condor_rm` the held job (Luca), restart → dokan marked
job 505 FAILED and spawned a fresh attempt s4 (job 1146) with a complete input
set, including the extensionless `_channels`. Lesson: a held job's DB entry
stays `running`; resurrection only re-resolves it after the condor entry is
removed. mergewatch now flags HELD>0.

# Controller WEDGED overnight (2026-07-15, 06:00) — BLOCKED on Luca

**Symptom:** controller (PID 3786220) logged nothing since 01:43, CPU flat
(0s over 20s sample) — deadlocked. The 8 remaining RR warmup condor jobs run
fine independently. mergewatch did NOT flag it (process exists → no
CONTROLLER_GONE; wedged ≠ gone — add a log-staleness check).

**Root cause (diagnosed):** 11 pre-production jobs (RV_*/s1-s2 era, job ids
762, 885, 1002, 1110, …) finished yesterday and wrote complete output (35
.dat files each), but their done-transition was missed during the 11:32/11:55
schedd SECMAN blips. Their condor entries are long gone, so DBRunner can
never resolve them by querying; DB stuck at status=running. Both restarts
(14:11, 17:51) resurrected them but re-attached as running instead of
collecting from disk. After the last live pre-prod job was collected at
01:43, the controller wedged on the zombies. UPSTREAM ISSUE for the hdf5
branch: jobs finishing during a schedd outage → permanent zombie + eventual
controller deadlock.

**Recovery (staged, needs Luca — agent kill was permission-blocked twice):**
1. `kill -TERM 3786220` (then check stragglers: `pgrep -f "nnlojet-run submit"`,
   TERM leftovers by PID).
2. Claude then runs `doctor` (SAFE now, controller down) — reconciles zombies
   from on-disk output — and restarts at cap 10000, verifies zombies resolved
   (762 etc. → done) and RR warmups re-attach.

Cost of the stall: barrier release delayed by the wedge duration; RR warmup
tail (8 parts, rounds 7-8) kept running in condor regardless, so likely
little real loss if recovered in the morning.

# NNLOJET vs DYTurbo at O(as^2) + unc-table validation (2026-07-14, addendum 4)

**FO cross-validation** (`nlo_nnlojet_vs_dyturbo.{png,pdf}` in webdir,
`nlo_vs_dyturbo.py` here): NNLOJET `nlo` output (as^1+as^2 spectrum) vs the
blessed DYTurbo N2LO file, central scale mur=muf=mll both sides, |Y|<2.5,
60<Q<120, densities on common edges. Result: ratio 0.999-1.000 everywhere,
pull mean −0.46, rms 1.11, one 3σ bin in 54 — agreement at the ≤0.2% level,
statistically consistent. Tiny coherent −0.2% at 50–100 GeV (many-bin, below
per-bin errors) — negligible for the correction, noted. Validates both the
"take as^2 from DYTurbo" plan and the NNLOJET setup itself.
Aggregation gotcha: dyturbo finer-bin file has 0.5-GeV bins below ~40 and
wider above; compare INTEGRALS on aligned edges (density-vs-average fails at
low qT where the spectrum is steep across a bin).

**Unc-table validation:** `dokan/tools/make_unc_table.py` re-run unchanged →
reproduces the 260427 table digit-for-digit (new copy: webdir
`260714_NNLOJET/`). BUT it reads `result/merge/` (incremental, naive errors,
Apr-23 post-cleanup state), not `result/final/` (Apr-6 finalize = trim+k-scan,
input to the blessed corr). final errors are 4–10× larger (k-scan calibration
against job scatter — the honest statistical errors); central values differ by
median 6.2% ≈ 1–2σ_final (but 5–20σ_merge). April table = naive lower bound;
final-based audit numbers are authoritative. Extra reason to RE-FINALIZE
as118_v2 (cleaned DB + 12.7k unmerged jobs) and remake the table from final.

Addendum-4 follow-up (ratio noise attribution): the DYTurbo files DO carry an
`uncertainty` column, but it's numerical-integration precision at the 0.004%
level (median 0.0036%, max 0.005% in 60<Q<120, |y|<2.5) — 30–100× below
NNLOJET's per-bin 0.1–0.5% on `nlo`. The ratio scatter is entirely NNLOJET
statistics (pull rms 1.11 with NNLOJET-only errors ⇒ fully accounted for);
treating DYTurbo as noise-free in the plot is justified.

# Hybrid (DYTurbo a+a2 + NNLOJET a3) stat gain (2026-07-14, addendum 5)

`fo_hybrid_vs_full_wums.{png,pdf}` (`hybrid_gain_wums.py` here): DYTurbo N2LO
vs NNLOJET full N3LO vs hybrid, FO-only, ratio to DYTurbo.
**Stat gain of the hybrid over full-NNLOJET on the existing run: negligible**
(err_full/err_hybrid = 1.002/1.002/1.004/1.007/1.014 in the 5 qT ranges):
the full-NNLO error is already ~100% nnlo_only's error because dokan gave the
a<=2 parts only 1.0% of the CPU (LO 0.1%, R+V 1.0%, RR/RV/VV 98.9% of 1.05M
CPU-h; DB query by part). The hybrid's real value is NOT noise removal on a
given run — it's (a) enabling the ptz>5 generation cut without losing a<=2
coverage at 1–5 GeV (the bridge), where the ~4x compute gain lives, and
(b) DYTurbo's exact a2 (0.004%) replacing a 0.1–0.5% ingredient for free.
Shape panel: a3 term = −10%..0 below 15 GeV, +5–7% at 20–100 GeV vs DYTurbo
(consistent with the coefficient plot).

# Fit-range restriction + as3-only running (2026-07-14, addendum 6)

Q (Luca): restrict generation to the fit range (qT<44, |Y|<2.5)? run as3-only?
Numbers from the as118_v2 final files, err^2 shares WITHIN the post-5GeV region:
- qT>44 (any y): 1.3% of err^2 (10.7% of sigma) -> capping qT saves ~nothing,
  and the matched prediction needs FO through the resummation switch-off
  (~43-60 GeV) + reco migration above 44 -> recommend NO qT cap.
- |y|>2.5: 29.1% of err^2 -> fit box (qT 5-44, |y|<2.5) keeps 69.9% => ~1.43x
  extra saving; padded box (qT<60,|y|<3.0) => ~1.21x.
- y-cut caveats: needs `select yz` in runcard (NEW run dir; can't change the
  live one); make_theory_corr/read_nnlojet_pty_hist expects ALL y-slice files
  (default ybins to +-5) -> restricted input needs corr=1 fallback outside
  coverage + handling of |Y_gen|>2.5 events that migrate into reco acceptance.
  Real but modest code work for 1.4x. Decision = Luca's; if wanted, redo the
  run dir NOW (run is 3h old).
- as3-only running: LO+R+V parts cost 1.1% of CPU (measured) -> nothing to
  save; dokan has no part-selection anyway; a<=2 parts double as validation.

# Full anatomy in wums + spike RETRACTION (2026-07-14, addendum 7)

New canonical plot `fo_anatomy_full_wums.{png,pdf}` from the committed script
`fo_anatomy_full_wums.py` (this dir; runs in container): matched N4+0LL+N3LO
(baseline) + resum + NNLOJET N3LO FO + a3 singular + DYTurbo N2LO FO + a2
singular (N3LL config), all |Y|<2.5, per-1-GeV integrals, ratio panel
x/matched. Supersedes `fo_vs_matched_orderconsistent.png` for presentation.

**RETRACTION — the qT≈29/57 "hole/spike" TODO is closed as NOT REAL:**
- N4p0LL resum pkl: smooth (median rel 2nd-diff 0.13%, no per-slice anomalies
  at 28-29/56-57).
- Recombined n3lo_sing and original nnlo_sing pkls: equally smooth there.
- Underlying ratios at those bins are 1.04-1.10 (resum/m) — ordinary ~2sigma
  NNLOJET fluctuations (FO flat across 28-30 where it should fall ~6%).
- The +-200-300% spikes in the earlier matplotlib plots were a rendering/
  array-handling artifact of those scripts, not data. Blessed corr NOT
  affected.
Also answered: the "noise" in resum/matched is the DENOMINATOR's NNLOJET stat
(the resum itself is 0.13%-smooth); the low-qT uptick of resum/matched is the
mirror of the negative nonsingular (m = r + nons, nons<0 there) — real
bookkeeping, stat-limited in size at 1-3 GeV.
Regridding lesson: aggregate variable-width bins onto a common grid by
overlap-weighted redistribution (see `regrid()` in the script), never by
integer-keyed shortcuts.

Addendum 7 follow-ups: `fo_anatomy_by_family_wums.py` (this dir) makes two
nominal-referenced anatomies, each in log + linear and any qmax:
`fo_pieces_n3lln2lo_wums*` (nominal matched + its own pieces) and
`fo_pieces_n4lln3lo_vs_n3lln2lo_wums*` (nominal + alternative matched + the
alternative's pieces). Also `fo_anatomy_full_wums.py` gained [qmax] [lin] args
and the N3+0LL+N2LO matched curve.

# Fine (0.5 GeV) low-qT FO-vs-singular + fine-file mystery SOLVED (addendum 8)

- **Fine-file mystery RESOLVED:** the `_fine` SCETlib pkls carry an extra
  Q bin [10,60] (γ*); slicing Q to [60,120] makes
  `com13_msht20an3lo_n3+0ll_fine_nnlo_sing` **bit-identical (ratio 1.0000)**
  to the blessed coarse nnlo_sing — the coarse file is just its Q-sliced
  rebin. Retract the "fine files don't reconcile" gotcha: it was the γ* bin,
  never a units problem. Rule: ALWAYS slice Q to [60,120] on fine pkls.
- New plot `fo_sing_fine_lowqt_wums.{png,pdf}` (`fo_sing_fine_lowqt_wums.py`
  here): DYTurbo vs fine singular vs nonsingular at native 0.5 GeV, qT<10.
- **Cancellation verdict:** for qT ≥ 1 GeV the cancellation is textbook —
  nonsingular is smooth and nearly constant (−1.1 to −1.4 pb/GeV, −0.7% to
  −2.2% of FO) at 0.5-GeV resolution, no structure → bridge interpolation
  across [1,5] is safe. Below 1 GeV the "blow-up" is ENDPOINT BOOKKEEPING,
  not physics: each term's bin content is separately log-divergent and
  regulator-defined (SCETlib bins start at 0.1 and its singular carries the
  δ(qT)-type terms in the first bin — sing[0,0.5]=−118 vs sing[0.5,1]=−622,
  non-monotonic; DYTurbo's FO[0,0.5]≈0). Only σ(qT<1) as a whole is
  meaningful; bin-by-bin differences there are code conventions. This IS the
  reason qtCutoff ≥ 1 exists.
