# Decisions — production 62-member PDF eigenvector cache build (overnight 2026-08-25/26)

Staged separately from `DECISIONS.md` because other agents are live in that file.
Owner: the PDF-cache build agent (single-babysitter rule). Run directory
`/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_260826/`.

Inherited and NOT relitigated: D-013 (never split members across processes),
D-024 (`--n-train 9`), D-025 (`target_precision_rel = 1e-3`), D-026 (split by BINS).

---

### P-001 — SCETlib library: a SNAPSHOT of `scetlib-nak` `eb60a04`, not the shared checkout — SETTLED
**What:** build and evaluate against
`/home/submit/lavezzo/.claude/jobs/140d052c/tmp/pdf62/scetlib_snapshot`, a copy of
`/work/submit/lavezzo/alphaS/scetlib-nak` (branch `near-anchor-knots`, `eb60a04`,
`build-nak`, md5(libscet-qT.so) `0c5dd7a92fea9e2ad0cb81639e9689a2`).
**Why that commit:** `eb60a04` = `bb2e7cb` (per-grid fixed-order weights)
+ **`92f1299`** (the muF member-COORDINATE fix the brief requires)
+ `83cecb2` (settable muF knot spacing, default 2.0 — verified inert: the header
comment and `_muf_vary_factor {2.0}` default, and `prepare_cache_for_card` passes
kappa_F 0.5/2.0, so the stencil is the three-knot one D-014 settled on)
+ **`3a8db11`** (the `_rule_is_matched` non-singular double-count fix; without it
"every Hessian changes by 152%", cc4ece2).
It is the ONLY tree that has both 92f1299 and `_rule_is_matched`:
`scetlib-cms/build-fix` (what the n_train gate used) has `_rule_is_matched` but
NOT 92f1299 (its own README says so); `scetlib-trans/build-trans` has 92f1299 but
its `py/scetlib_tf.py` has zero occurrences of `_rule_is_matched`.
**Why a snapshot:** `scetlib-anlmuf`, the sibling worktree at the same commit, was
relinked at 23:16 tonight by another agent. A relink or a `git checkout` in a
shared tree during an 8 h job is a real risk; 12 MB of copy removes it.
**Checked, not assumed:** `92f1299` touches only
`include/scetlib/qT/ad/ad_kernel.hpp` — the evaluation kernel — which is the
mechanical confirmation of the brief's "nothing stored changed", so the choice of
library does not change the cache contents, only how they are read.
**Beamfunc grids:** the snapshot's own `share/` is empty, but `build-nak`'s
compiled-in `config::data_dir` is
`/home/submit/lavezzo/alphaS/WRemnants/scetlib-cms/share/scetlib`, which carries
all 59 CT18ZNNLO members (60 files per kernel dir = .info + 0000..0058) plus the
two alphaS sets. Verified before launch.
**Overturned by:** evidence that `83cecb2` or `eb60a04`'s `rule_cvals` diagnostic
is not inert in the build path.

### P-002 — Bin groups = ONE ptV index each (10 |Y| bins), 21 groups — SETTLED
**Why not 4-5 big cost-balanced groups:** balancing needs a per-bin cost model,
and the one available is contradictory — the same 4-member stage is 17.7 core-min
on ptV 10, 32.0 on ptV 20, 2.3 min on the (ptV 16,17) pair, and ptV 0 at
`--threads 1` has been in its node-set stage for 9.8 h. Fine groups make the cost
model unnecessary: 21 groups over 4 slots is a work queue, so balance is automatic
and the makespan is set by the queue, not by my guess.
**Why it costs nothing:** the node-set and rules stages are per-BIN work, so their
total core-time is independent of how the bins are grouped (~36 core-min/bin,
~124 core-hours over the card either way). The only per-GROUP cost is process
startup (PDF/beamfunc `.info` reads), which is why the launches are staggered 90 s.
**Why 10 bins is still enough work to fill a fat thread pool:** the parallelism
note measures the member stage on a 10-bin subset at 0.22 min/member with
`--threads 200` against 0.7-1.0 at 32 — the stage is parallel over NODES
(10 bins x ~300 nodes = ~3000), not over bins.
**Bonus:** finer groups mean more of them complete before the deadline, which is
the entire point of D-026.

### P-003 — 4 concurrent processes x `--threads 128`, not many thin ones — SETTLED
**Why:** the binding constraint is the 32768-threads-per-user ceiling, not RAM.
At launch the user already held **22,104** OS threads (three 210-bin diagnostic
shards at ~1880-2430 each, three rabbit fits at ~1680, two histmakers), leaving
~10,600. A build process spawns ~1800-1880 threads *whatever `--threads` says*
(measured: `--threads 24` -> 1697, `--threads 210` -> 1874), so OS threads are a
per-PROCESS tax and requested cores are free. Four processes = ~7,500 threads
(~3,100 margin) and 512 requested cores; eight thin processes would cost twice the
threads for the same cores and would break the ceiling.
**Live knob:** the scheduler re-reads `state/slots.txt` and `state/threads.txt`
every 30 s, so concurrency is raised as the other jobs exit rather than fixed now.
**Overturned by:** `pthread_create` EAGAIN in any log, which means back off at once.

### P-004 — Queue order = ASCENDING qT index — SETTLED (deliberate trade-off)
**The trade-off the brief asks to be explicit about.** Sensitivity to alpha_s and
the NP lambdas lives at low and moderate qT, and those are also the expensive bins.
Ascending order puts them FIRST, so they get the whole night rather than whatever
is left. The high-qT tail (ptV 19-20 = qT [33,44] and [44,100]) is expensive too —
`onebin_qt20` needed 32.0 core-min against 17.7 for ptV 10 — but it carries the
least alpha_s information, so it is the right thing to lose if something must be.
**Second reason, structural:** the gen fold requires the cache to tile a rectangle
exactly, so a deliverable partial cache must be CONTIGUOUS in qT. With one group
per ptV index and a queue in index order, the completed set is a contiguous run by
construction (and if a group in the middle lags, the largest contiguous run is
still a valid rectangle — it simply need not start at qT = 0).
**Overturned by:** a measured throughput that says everything finishes anyway, in
which case the order is irrelevant.

### P-005 — Cap TensorFlow's thread pools in the builder: 1665 OS threads -> 135 — SETTLED (measured)
**What:** `TF_NUM_INTRAOP_THREADS=4`, `TF_NUM_INTEROP_THREADS=2` in the container
entry, for the CACHE BUILD only (not for fits, which really do use TF).
**Why it matters:** the 32768-threads-per-user ceiling was the binding constraint
of the night — 22104 threads were already held at launch and a single build
process costs 1800-2430 of them "whatever `--threads` says", which is the
observation the parallelism note records but does not explain.
**The explanation, measured in-container tonight:**

| after `import tensorflow` | total threads | `tf_Compute` | `python3` |
|---|---|---|---|
| uncapped | **1665** | 768 (= one per core) | 895 |
| `TF_NUM_INTRAOP_THREADS=4`, `TF_NUM_INTEROP_THREADS=2` | **135** | -- | -- |

So ~1530 of every build process's ~1800 threads belonged to TensorFlow, which
`prepare_cache_for_card.py` never uses: it imports `argparse`, `configparser`,
`h5py`, `numpy` and the scetlib_ad backend, and TF arrives only transitively
through the `wremnants` package. The thread tax is 12.3x larger than it needs
to be, and it is charged per PROCESS, i.e. exactly against the axis D-026 asks
us to parallelise over.
**Consequence:** the "handful of concurrent build processes" limit is an
artefact, not physics. With the cap the same ceiling allows several times more
concurrent bin groups.
**Evidence:** in-container A/B, same image, same imports, one `env -u` apart.
**Overturned by:** a measurable slowdown of the build itself — checked by
comparing the stage times of capped groups against qt0/qt1/qt2, which were
launched uncapped, on the same card and thread count.

### P-006 — qt0 (qT [0,1]) split by |Y| into FIVE sub-shards, as a HEDGE — SETTLED
**The problem, measured:** every other bin group finished its outer node set in
0.2-1.0 min; **qt0 was still in that stage at 29 min**, having burnt 19.4 CPU-hours,
and running at only **40 of the 128 cores it asked for**. It is not saturated, it
is starved: ten bins is too little to feed 128 threads while the node ladder
adapts. This is the same pathology as `par_test/onebin_qt0` (one bin,
`--threads 1`, still in its node set after 10.3 h).
**What was done:** `--subset '0,1/0'`, `'2,3/0'`, `'4,5/0'`, `'6,7/0'`, `'8,9/0'`
— five sub-shards of two |Y| bins each, all 62 members, `--threads 96`, each with
its own thread pool. They tile |Y| 0..9 at ptV 0 exactly, so they merge into
precisely the cache one qt0 shard would have produced (the bin merge is validated
bit-exact at P = 53 with 62 members, 0.000e+00 in value and Jacobian).
**Why FIVE and not two or ten:** two halves is only a 2x hedge on the one bin
that sets the wall time; ten single-|Y| shards multiplies a fixed per-process
cost (startup, PDF/beamfunc `.info` reads, its own rules stage) by ten on the
most expensive bin of the card. Five is the point where each sub-shard still has
two bins to parallelise over, and — the deciding practical reason — **five can be
staged in waves against the OS-thread budget** where three cannot be re-split
later: the partition of |Y| has to be fixed before the first sub-shard starts,
so the finer choice is the one that keeps the launch schedule free. Three were
launched at 00:02 (threads then 26254 of 32768); the other two go in the next
thread window.
**Why HEDGE and not switch:** the node-set stage is not checkpointed, so killing
qt0 at 29 min throws away 19.4 CPU-hours for certain in exchange for a speedup
that is expected but unmeasured. The TF cap (P-005) is what makes running both
affordable at all. Whichever lands first is used; the loser is killed.
**At merge time: use EITHER `qt0` OR the five sub-shards, never both** — they
cover the same bins, and `merge_bin_caches` raises on a duplicate bin key
("bin ... claimed twice"), which is a safe failure rather than a silent one.
**Overturned by:** qt0 printing its node set before the sub-shards pass it.

### P-007 — CORRECTION to P-006's premise: splitting qt0 by |Y| does NOT add cores — MEASURED
**The premise was:** qt0 runs at ~40 of the 128 cores it asked for, so ten bins
is too few to feed the thread pool and sub-shards with their own pools will get
more. **That is wrong, and here is the measurement that says so** — cores per
BIN, taken live at 00:07 across every running process:

| process | subset | cores | bins | **cores/bin** |
|---|---|---|---|---|
| qt0 (node-set stage) | `*/0` | 34.1 | 10 | **3.41** |
| qt0y01 (node-set stage) | `0,1/0` | 8.5 | 2 | **4.23** |
| qt0y23 (node-set stage) | `2,3/0` | 5.5 | 2 | **2.75** |
| qt0y45 (node-set stage) | `4,5/0` | 6.3 | 2 | **3.15** |
| for contrast, groups in their MEMBER stage | `*/1`, `*/10` | 90.3, 84.6 | 10 | 9.04, 8.46 |

The outer node-set stage on the qT [0,1] bins is limited to **~3-4 cores per bin**
whatever the arena size — the adaptive node ladder inside one bin has that much
parallelism and no more. Five sub-shards therefore get 5 x (2 bins x ~3.4) =
the same ~34 cores qt0 already has, at the same rate, having started 34 min later.
**So the split cannot overtake qt0 and is not a speedup.** The member stage is
the one that scales with threads (9 cores/bin, and the note's "parallel over ALL
nodes of ALL bins at once"); the node-set stage is not.
**What the sub-shards ARE worth, and why they stay running for now:** insurance.
qt0 is the single point of failure for the whole 21-shard partition (`GenFold`
refuses a hole), it is one of the three PRE-TF-CAP processes still holding 1808
threads, and it is therefore the one most exposed to another `pthread_create`
abort. The node has spare capacity right now (load 714 of 768) and the hedge
costs ~20 cores. **Kill the sub-shards the moment qt0 prints its node set.**
**This also generalises:** do NOT expect a bin split to accelerate a build whose
cost sits in the node-set stage. Split bins for PARTIAL-RESULT SAFETY and for the
member loop; the node set scales with bins, not with threads.
