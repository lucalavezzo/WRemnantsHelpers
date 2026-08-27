---
name: fit-queue
description: Manage the alphaS/NP fit queue — launch fits (warm-started), track what is running/finished/held, and refresh the results views after any fit step. Use whenever launching a rabbit/SCETlibNP fit, when asked "what is running / what is in the queue / is the queue updated", or when a fit or hessian completes.
---

# Managing the fit queue

Procedure for running the SCETlibNP fit campaigns. This file holds **process**; the live **state**
lives in `studies/<slug>/QUEUE.md`. Keep that split — do not copy state into here, and do not copy
process into QUEUE.md.

Two hard conventions:

- **`QUEUE.md` = practical run log only** — what is RUNNING, FINISHED, HELD/DEAD. No physics.
- **`LOGBOOK.md` = the numbers and the physics** — α_s, σ, NLL, GoF, interpretation.

Luca has asked for both explicitly. Putting numbers in QUEUE.md is a mistake; so is leaving a
finished run undocumented.

## 1. Status check ("what's running?", "is the queue updated?")

```
bash studies/<slug>/scripts/queue_status.sh
```

Prints running fits/hessians (role, elapsed, latest loss), cov state (**real vs placeholder**), toy
progress, thread usage, and which runs are in `runs_new.yaml` but have no cov yet. Reconcile
`QUEUE.md` against that output — if they disagree, QUEUE.md is wrong; fix it.

Never answer "what's running" from memory or from QUEUE.md alone; both drift.

## 2. Launching a fit

Fits run via a per-config runner in `studies/<slug>/scripts/run_*.sh`. Copy the nearest existing
runner — they already carry the thread gate, the serialized-hessian gate, and the cov skip-guard.

Then:

1. **Launch WARM by default** (Luca): add `--seedFrom <fitresult|dir>` to the fit step. That passes
   `--externalPostfit` *without* `--noFit`, so rabbit loads the FULL parameter vector (λ + α_s +
   every nuisance) and keeps minimizing.
   - **The seed must be the SAME configuration** — same NP form, same freeze list, same datacard —
     **differing at most in the wall.** The canonical case is "this exact fit, but WITH a wall".
     Seeding across NP forms / cards / freeze lists mixes incompatible parameter vectors and the
     loaded numbers mean something else. `--seedFrom` now VALIDATES this and refuses a mismatch
     (`--seedForce` overrides); it also prints whether the seed was WALLED or UNWALLED.
   - **Never seed λ-only** (`xparam_default`): measured to return the *identical* (shallower) cold
     minimum, and slower. Full-vector is the only seed that works.
   - The runner scripts themselves stay **cold by default** — seeding is an explicit per-launch flag
     so a bare script run is reproducible.
   - For unwalled / negative-margin (multimodal) configs, keep the **cold** run too and take the
     **lowest-NLL** of {cold, warm}.
2. **Distinct output dir** for a seeded variant (e.g. `…/nowall_seedWalledFull`) so the cold result
   is never overwritten.
3. **Add it to `runs_new.yaml` immediately** — unlisted = invisible to both results views. **Label
   the seed in the name**, e.g. `"No wall 1D $p_T^{\ell\ell}$ (full-seed from walled)"`. A seeded and
   a cold run of the "same" config can be different minima; they must never look identical.
   **Keep names SHORT** (Luca, twice: "some of these names got too big"). A name states only what
   DEVIATES from its family's baseline — never a full setting dump, and never a `[dirname]` suffix
   (the `dir:` line right below carries it). Each spec file's own header defines its baseline; for
   `studies/np-wall-local-minima/runs_new.yaml` the 2D MSHT20 baseline is lattice CS init,
   λ∞^ν = lattice, MAP22 TMD init, cold, wall @ ymax 2.5, tanh_2. Everything a short name leaves
   out is already on the interactive page as a facet derived from the fit's own provenance
   (`λ init (CS kernel)`, `λ init (TMD bc)`, `constraint (CS kernel)`, `constraint (TMD bc)`,
   `start`, wall/margin, PDF, …) — the CS kernel and the TMD boundary condition are kept apart, so
   either sector can be filtered or coloured on its own. Spelling settings into the name buys
   nothing. **Do not write a bulk relabeler that expands names again** — one did
   that on 2026-08-05 and the shortening had to be redone.
4. **Add it to QUEUE.md** under RUNNING.

Launch detached, from OUTSIDE the container, wrapping in singularity — and `cd` to the repo
**before** `source setup.sh` (omitting the `cd` silently produces an empty log):

```
setsid singularity exec --bind /scratch/,/work/,/home/,/ceph/ "$IMG" bash -lc "
  cd /home/submit/lavezzo/alphaS/WRemnantsHelpers && source /opt/venv/bin/activate && source setup.sh \
    && bash studies/<slug>/scripts/run_<config>.sh
" > studies/<slug>/scripts/run_<config>.out 2>&1 < /dev/null &
```

**Logs live WITH the fitresult** (Luca 2026-07-30): every step must tee its output into the step's
own output directory on ceph, next to `fitresults.hdf5` — not only into `scripts/*.out`. Idiom inside
a runner (works with `set -uo pipefail`, so the `&&`/`||` status check still sees python's exit code):

```
mkdir -p "$OUT"
python3 "$FITTER" ... --steps fit ... 2>&1 | tee -a "$OUT/fit.log"   && echo ok || { ...; exit 1; }
python3 "$FITTER" ... --steps hessian ... 2>&1 | tee -a "$OUT/hessian.log" && ...
```

Why: a result you find on disk months later should carry its own log. It also stops two launches of
the same runner from interleaving into one shared `scripts/*.out` — which happened on 2026-07-30 and
made the gen-level progress unreadable.

**Never delete/move an output file while its process is alive.** rabbit holds the fd, so the fit keeps
writing to an unlinked inode and the result NEVER appears in the directory (this wasted ~50 min on the
gen-level fit). Kill the process first, then clean up, then relaunch. Check with
`ls -l /proc/<pid>/fd | grep '(deleted)'`.

Then confirm from the log that it really started: `WARM-STARTED` vs `cold start`, the freeze list,
and that it reached `Iteration 1`.

## 3. When a fit step finishes — the refresh checklist

```
bash studies/<slug>/scripts/queue_refresh.sh          # steps 1-3, and tells you what changed
```

1. run is present in `runs_new.yaml` (with seed label)
2. rebuild the **interactive UI** (primary view)
3. rebuild the **LaTeX table**
4. update **QUEUE.md** (move the row RUNNING → FINISHED) and put the numbers in **LOGBOOK.md**

Both views run **inside the container**, with **`/cvmfs` in the bind list** (the table step needs the
TeX there) — i.e. `--bind /cvmfs/,/scratch/,/work/,/home/,/ceph/`. (Historically the table was run on
the host; that is no longer needed.)

Steps 1–3 are the script; step 4 is yours. Do all four every time — Luca has called out drift twice.

## 3b. Minimizer / threads policy (measured 2026-07-30)

- **GEN-LEVEL: BFGS + 64 threads, by DEFAULT** (`--extraFit="--minimizerMethod BFGS ... --noEDM"`,
  already the default in `run_genlevel.sh`). trust-krylov is hopeless there: 184 iters / 97 min still
  at nll 4695, vs BFGS reaching the same minimum (107.30797047, matching to ~1e-13) in 103 iters /
  12 min. The gen fit has only **79 nuisances** vs 3746 at reco, which is why BFGS wins so big.
- **RECO: keep trust-krylov as default**; use BFGS opt-in for a slow or repeated fit. Measured on
  CT18Z ptll walled: BFGS/64 = 1182 s (211 iters, 5.6 s/iter) vs trust-krylov/8 = 2043 s (85 iters,
  24.0 s/iter) -> only ~1.7x, and BFGS's EDM is ~400x looser (2.2e-15 vs 4.9e-18) with
  `success: False` ("precision loss") so its status flag is NOT a convergence test. Not worth trading
  that away on a 30-min fit.
- **More threads do NOT help reco**: trust-krylov went 24.0 -> 37.4 s/iter from 8 -> 64 threads (39
  bins do not parallelize far, and the extra threads add contention). The BFGS gain at reco is the
  MINIMIZER, not the threads. At matched 64 threads BFGS iterations are ~6.6x cheaper.
- **`--noEDM` for anything whose fit-step EDM CG stalls** (fully-frozen-CS fits: 11 h; gen fits: never
  finished). rabbit writes NOTHING until that step completes, so a 12-min minimization can yield zero
  output. sigma comes from the hessian pass regardless.
- BFGS reaches the SAME minimum where tested: reco Δnll 7e-10 / Δα_s 2e-9 / all λ ≲1e-9; gen matching
  to ~1e-13. So it is safe, the caveats are about convergence *diagnostics*, not the answer.

## 4. Traps that have actually bitten

- **A cov file existing is NOT "done".** rabbit writes a ~54 KB placeholder when the hessian
  *starts*; a finished lightened cov is ~100 MB. Require **> 1 MB**. (This produced a false
  "FIT_COMPLETED" and a wrong status report.)
- **The GEN-LEVEL hessian must be `--noImpacts`.** `--genLevel`'s default hessian (impacts +
  per-process hists) reached **1084 GB of 1447 GB** and had to be killed mid-run to protect the other
  jobs (2026-07-29). Bin count is NOT the cost driver — the impacts machinery is — so "it's only 200
  gen bins, it'll be cheap" is wrong. Lightened reco hessians are ~300 GB; budget accordingly and
  keep the `avail >= 500 GB` gate.
- **Watch memory, not just threads, when a FULL hessian runs.** `queue_status.sh` reports MemAvailable;
  if it collapses, find the offender with `ps -eo rss,pid,args --sort=-rss | head`.
- **Thread ceiling**, not CPU or RAM, is usually the binding limit: `ulimit -u` = 32768/user and each TF
  process holds **~1613 threads** (XLA sizes to ncores, ignoring `THREADS=8`). Above ~20 concurrent
  processes a new fit dies in XLA compile with `pthread_create ... EAGAIN`. Gate every launch on
  `ps -o nlwp= -u $USER` and stagger launches. Node has 768 cores, so load ≫ 100 is normal and fine.
- **The per-runner hessian gate RACES.** Each runner checks `hess == 0` independently, so two runners
  can pass at the same instant and run ~300 GB hessians concurrently. Survivable on an idle node, NOT
  when another user appears: on 2026-07-30 two 300 GB hessians + another user's ~120 GB + 8 toys drove
  MemAvailable to **46 GB** and one hessian had to be killed. The real fix is a shared `flock` mutex
  around the gate (the pattern `run_queue.sh` already uses for fits), not a bigger `avail` threshold.
  Until the runners are converted, WATCH for two hessians at once.
- **Hessians must be serialized** (~300 GB each) and the gate MUST filter `comm=="python3"` — a bare
  `pgrep`/`grep` on the pattern self-matches the watcher/agent shell and deadlocks the gate.
- **Both results scripts run inside the container, but the bind list must include `/cvmfs`** or the
  table step fails (it needs the TeX from there).
- **`fit_summary_table.py` prints "MISSING: cov/sigma_alphaS"** for many runs — a bug in that script,
  not missing data; the plotly UI reads σ from the same covs. Use the UI for σ.
- **ALWAYS BLIND — never unblind** (Luca, 2026-07-30: "we are always blinding! important!"). Do not add or use an `--unblind` path.
- **Fits are BLINDED by default.** Every fit logs `Blind parameter b'pdfAlphaS'` /
  `Unblind parameters with []` unless rabbit's `--unblind` is passed (not exposed by
  `fitterSCETlibNP.py` as of 2026-07-30). The offset is `deterministic_random_from_string('pdfAlphaS')`
  The offset is seeded on the PARAMETER NAME **plus a `_data` suffix when `data_obs` are integers**,
  drawn ~N(0, std=5). So it is the same only WITHIN a family: all reco (integer-count) data fits share
  one offset and their differences are meaningful, but a GEN-LEVEL/unfolded fit (continuous data) or a
  differently-named parameter (`pdfAlphaSSymAvg`) gets a DIFFERENT offset — **never compare α_s across
  those boundaries**. σ(α_s), NLL and GoF are unaffected by blinding and always comparable.
  **NEVER compute or reconstruct the offset** — it defeats the blinding (Luca was emphatic, 2026-07-30).
- **Asimov fits are NOT blinded** (`blinded_fits = f == 0 or an "observed" toy`), so an Asimov postfit
  shows the true value (0 for a closure test) while every data fit is blinded — never put the two in
  the same comparison.
- **Data vs Asimov: rabbit's `-t` is `-1: asimov, 0: fit to DATA, >=1: toy`.** `-t 0` (our default) is
  a real-data fit. For an unfolded/gen-level card also check the UPSTREAM unfolding: its card
  (`setupRabbit … --realData`) and its fit (`toys=[0]`, `pseudoData=None`).
- **rabbit's printed saturated `ndof` ignores the freeze list** — freezing a parameter does not change
  it, so the printed p-value is wrong for frozen-parameter fits. Prefer the toy-calibrated p.
- A fit whose loss decreases **linearly and decelerates** is stuck, not slow (the tanh_6_abs case:
  168k→119k over 397 iters). Healthy fits cliff-drop to O(10) in ~100 iters. Compare against a
  known-good log before concluding "it's just slow", and compare **iterations**, not wall-clock
  (per-iteration time swings with node load).

## 5. Held / dead runs

Record them in QUEUE.md's HELD/DEAD table with a one-line reason and whether to rerun. A killed run
that looks merely "missing" gets silently relaunched by the next person.
