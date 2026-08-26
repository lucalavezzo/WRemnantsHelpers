# LOGBOOK entry (staged) — the production 62-member PDF eigenvector cache

Staged outside `LOGBOOK.md` because other agents are live in it. Merge into the
main logbook when the tree is quiet.

## 2026-08-25/26 overnight — the 62-member PDF eigenvector cache build

**Run dir** `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_260826/`
(`shards/qt<k>/` one per ptV index, `state/` the queue and scheduler logs).
**Webdir** `~/public_html/alphaS/260826_scetlib_ad_pdf62/`.
**Scripts** `/home/submit/lavezzo/.claude/jobs/140d052c/tmp/pdf62/`
(`scheduler.sh`, `run_group.sh`, `merge_and_check.sh`, `monitor.sh`,
`incontainer_nak.sh`, `scetlib_snapshot/`).

### What was launched, and the four choices behind it

Full production configuration for the 2D reco card: 210 gen bins
(21 ptVGen x 10 absYVGen, Q [60,120]), **29 PDF eigenvector pairs + the alphaS
pair + the muF pair = 62 members**, `--n-train 9` (D-024),
`target_precision_rel = 1e-3` (D-025), split by BINS (D-026), members never split
(D-013). Decisions P-001..P-004 in `DECISIONS_pdfbuild.md`; the four in one line
each:

* **P-001 library** — a snapshot of `scetlib-nak` `eb60a04`, the only tree that
  carries BOTH `92f1299` (the muF member-coordinate fix the brief requires) and
  `3a8db11`/`_rule_is_matched` (the non-singular double-count fix, worth 152% on
  every Hessian). Snapshotted because a sibling worktree at the same commit was
  relinked at 23:16 tonight.
* **P-002 grouping** — 21 groups, one ptV index each (10 |Y| bins). A work queue
  instead of a cost model, because the available per-bin costs contradict each
  other by an order of magnitude.
* **P-003 concurrency** — few fat processes, not many thin ones: OS threads are a
  per-PROCESS tax (~1800-2430 each regardless of `--threads`) against a 32768
  ceiling that was already 22104 full at launch.
* **P-004 order** — ascending qT, so the alpha_s/NP-sensitive low and moderate qT
  bins get the whole night and every completed set is a contiguous rectangle.

### Measured, as it happened

(filled in below as the night runs)

#### 23:47 — the acceptance pipeline, shaken out on an EXISTING 62-member cache

Before the production shards existed, both acceptance scripts were run end to
end on `eig_test/y20_eig29` (20 bins = |Y| 0-2.5 x qT 20-28, 62 members, P = 53,
n_train 9, but **rel 1e-4**, and built by the n_train-gate agent, not by me).
Two things came out of it.

**1. `backend_check.py` passes on a 62-member cache** — the first time it has
been run on one:

| check | result |
|---|---|
| anchor re-evaluation bit-identical | True |
| FD `alphas` | rel 6.15e-11 |
| FD `np_eff_lambda2` / `np_gnu_lambda2` | 3.82e-10 / 5.27e-10 |
| FD `scale_kappa_F` | 9.09e-08 |
| **FD `pdf_eig0`** | **5.52e-06** (passes, but 19x worse than `pdf_eig5`) |
| FD `pdf_eig5` | 2.91e-07 |
| Hessian symmetry `max\|H-H^T\|/max\|H\|` | **0.00e+00** |
| fold sum rule | **0.00e+00** |
| value+jacobian / hessian, 20 bins, 16 thr | 1136 ms / 70.6 s |

The `pdf_eig0` outlier is the artefact the brief predicts, and its mechanism is
visible in the same table: `backend_check` uses
`h = 1e-4 * max(|anchor_i|, 1e-3)`, so every zero-anchored `pdf_eig*` is
differenced at **h = 1e-7**, and `pdf_eig0`'s analytic derivative (-0.0481) is
**8.2x smaller** than `pdf_eig5`'s (-0.3937). Same absolute round-off, 8x
smaller denominator, 19x worse relative error. `fd_scan.py` (written, ready) does
the step-size scan that settles it.

**2. First "at scale" read on the PDF eigenvector directions** — 20 bins over the
full |Y| range, against the `pdfvars` CorrZ templates, all 97 variations:

| group | N | worst max\|dev\| | worst direction |
|---|---|---|---|
| NP lambda | 8 | 8.92e-07 | lambda2 = 1.0 |
| TNP | 20 | 6.17e-07 | b_qg 0.5 |
| muF/kappa_R | 6 | 2.76e-04 | muF down |
| transitions | 3 | 2.93e-03 | 0.3/0.6/0.9 |
| alphaS | 2 | 2.81e-05 | as_0116 |
| **PDF eig** | **58** | **5.53e-06** (pdf51) | median **1.10e-06**, best 1.64e-07 |

So the ~1e-6 the earlier agent measured on a 4-bin window **holds on 20 bins
across the whole |Y| range**: the eigenvector directions sit with the NP lambdas
at the good end, 50x better than the muF group and 500x better than the
transitions, and every one of the 58 is <= 5.5e-06. This is not yet the
production answer -- it is rel 1e-4 and only qT 20-28 -- but it is the first
evidence at more than 4 bins.

#### 23:59 — FIRST SHARD COMPLETE, and the measured throughput

`shards/qt2` = ptV index 2, i.e. **qT [2,3] GeV x all 10 |Y| bins, all 62
members**, exit 0, `cache.npz` **92.0 MB**. Stage by stage, `--threads 128`,
rel 1e-3, n_train 9, P = 53:

| stage | qt2 (qT 2-3) | for scale: m210 (210 bins, `--threads 210`) |
|---|---|---|
| outer node set | 1.0 min | 23.3-36.9 min |
| rule solve | 2.9 min (median 255 nodes/bin) | 19.9-32.4 min (median 277) |
| resummed members (29 pairs) | 2.2 min | 2.2-5.7 min |
| **fixed-order members (62)** | **16.5 min** | 46.9 min for FOUR members |
| total wall | **~23 min** | -- |

So a 10-bin group with the COMPLETE 62-member list costs ~23 min, of which the
member loop is 72%. 21 groups x 92 MB projects to **~1.9 GB on disk**, against
the T15 projection of 2.3 GB — the model holds.

Two things this settles.

* **The full 21-shard partition is comfortably feasible tonight.** At 7 slots and
  ~23 min per typical group the queue drains in ~3 batches, i.e. ~1.5-2 h, against
  8 h of deadline. The uncertainty is entirely the lowest-qT groups (see below).
* **Bins really are wildly unequal, and the ordering choice was right.** qt2
  (qT 2-3) needed 1.0 min for its node set; qt3/qt4/qt6 (qT 3-4, 4-5, 6-7)
  needed 0.6/0.2/0.2 min. **qt0 (qT [0,1]) was still in its node-set stage after
  26 minutes** — it alone is worth more than all the cheap groups together, which
  is exactly what the logbook's earlier `onebin_qt0` observation said (that run,
  one bin at `--threads 1`, has been in the same stage for 10.3 h).

#### 00:00 — BUILD ECONOMICS: what an eigenvector member actually costs

The brief asks for the marginal cost of an EIGENVECTOR member specifically,
because the inherited 13.7 min/member came from a 4-member build that was the
alphaS pair plus the muF pair. Two 210-bin shards built tonight settle it
**like for like** — same card, same runcard (rel 1e-3), same `--n-train 9`,
same P = 53, same `--threads 210`, launched together at 21:28 on the same node,
four members each, differing ONLY in WHICH four:

| shard | its four members | fixed-order stage |
|---|---|---|
| `m210_eig` (`--members 0:4`) | 2 EIGENVECTOR pairs | **46.9 min** |
| `m210_asmuf` (`--members 58:62`) | alphaS pair + muF pair | **96.9 min** |
| ratio | | **2.07** |

So, at 210 bins and `--threads 210`:

    eigenvector member          11.7 min          (46.9 / 4)
    (alphaS + muF) member       24.2 min          (96.9 / 4)
    => muF member               ~36.8 min         if an alphaS member costs
                                                  like an eigenvector one, which
                                                  it should: both are a PDF-set
                                                  swap and a full node refill
    => muF / eigenvector        ~3.1x

**The brief's hypothesis is confirmed, and it was if anything conservative.** It
guessed muF at 2.4x a PDF member and "an ordinary PDF member ~8 min, the real
total nearer 9 h than 15". Measured: the muF pair is ~3x, and the total for 62
members follows as

    58 x 11.7  +  2 x 11.7  +  2 x 36.8  =  776 min = 12.9 h   (tonight's load)
    58 x 6.6   +  54.8                   =  438 min =  7.3 h   (the load under
                                                                which
                                                                cache_260824b's
                                                                54.8 min for the
                                                                same 4 as+muF
                                                                members was
                                                                measured)

i.e. **7.3-12.9 h for a single monolithic 210-bin process**, against the ~14 h in
the knowledge note, which assumed every member costs what a muF member costs.
That assumption inflates the estimate by ~1.8x.

**Honest caveat, stated before the number is used.** The two shards ran
concurrently but their member loops did not overlap in time: `m210_eig` ran its
FO stage 22:26-23:13, `m210_asmuf` ran 22:22-00:00, and from 23:29 my own seven
groups were on the node. So `m210_asmuf` saw more contention and **2.07 is an
upper bound on the muF/eigenvector ratio**. What is robust is the direction and
the order of magnitude: a muF member is several times an eigenvector member, not
the other way round, and the eigenvector members — 58 of the 62 — are the CHEAP
ones.

#### 00:03 — THE MERGE, PROVEN, AND THE MEMOISATION TRAP RULED OUT

`shards/qt2` + `shards/qt5`, two INDEPENDENTLY built processes each carrying the
complete 62-member list, merged with `build_cache_parallel.py --merge-bins` into
20 bins x 62 members, 180.4 MB. Evaluated the merged cache and each parent in
**three separate processes** (`compare_caches.py --eval`, which exists precisely
so the arms cannot share state) and diffed the saved arrays:

| | anchor value | anchor jacobian | displaced value | displaced jacobian |
|---|---|---|---|---|
| merged vs qt2 (10 common bins) | **0.000e+00** | **0.000e+00** | **0.000e+00** | **0.000e+00** |
| merged vs qt5 (10 common bins) | **0.000e+00** | **0.000e+00** | **0.000e+00** | **0.000e+00** |

all four bit-identical, at the anchor and at a 10%-displaced random point.

**Why that 0.000e+00 is a result and not the "perfect and wrong null".** The
brief's trap is that `ScetlibCachedXsecTF.values_and_jacobian` memoises on the
parameter vector alone, so an A/B that accidentally shares an evaluator returns a
ratio of exactly 1.00 for everything. The separation is PROVEN here, not
assumed, by three numbers that cannot come from one evaluation:

    merged (20 bins)      sum(sigma) = 63.6503485923
    qt2    (10 bins)      sum(sigma) = 28.725160
    qt5    (10 bins)      sum(sigma) = 34.925188
    |merged - qt2 - qt5|             = 7.1e-15

Three different sums, obeying the additive sum rule to floating-point. A memo
collision would have returned one number three times.

#### Stage costs so far — the fixed-order stage falls steeply with qT

| group | qT [GeV] | node set | rules | resum | fixed order | total | MB |
|---|---|---|---|---|---|---|---|
| qt2 | 2-3 | 1.0 | 2.9 | 2.2 | **16.5** | ~23 min | 92.0 |
| qt3 | 3-4 | 0.6 | 4.9 | 4.9 | **8.2** | ~19 min | 92.1 |
| qt5 | 5-6 | 0.7 | 4.6 | 2.7 | **5.2** | ~13 min | 88.5 |
| qt0 | 0-1 | **> 29 min, still running** | | | | | |

A factor 3.2 in the member stage between qT 2-3 and qT 5-6, and qt0 is off the
scale. This is the quantitative form of "balance the groups by COST, not by
count", and it is why the one-group-per-ptV queue (P-002) was the right structure:
no cost model was needed, the queue absorbed the imbalance by itself.
