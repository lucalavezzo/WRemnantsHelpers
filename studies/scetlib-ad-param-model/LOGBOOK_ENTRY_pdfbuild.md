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
