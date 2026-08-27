---
title: MR !9 — analytic DGLAP muF correction ON BY DEFAULT
slug: mr9-default-on
status: active
created: 2026-08-27
updated: 2026-08-27
---

# MR !9 default-on — logbook

**Goal:** flip `ad_muf_anl` from 0 to 1 on MR !9's branch (`muf-analytic-trans`),
re-verify the invariants now that they hold for everyone rather than only for
opt-in callers, price the residual in alpha_s before and after, measure what the
correction costs, and put all of that in the MR description. The decision that
it goes on is Luca's and is not re-opened here (D-049 shipped it off by default;
this round is the flip).

---

## START HERE (status as of 2026-08-27)

> **Flipped, built, invariants re-verified, alpha_s projection and timing measured
> from ONE cache in ONE process. See `run_mr9.log` for every number.**
> The flip is three files (`ad_state.cpp` default, plus the `ad_data.hpp` and
> pybind docstrings that state it); `set_muf_analytic(0)` is unchanged and is
> still the A/B arm. Isolated worktree `/work/submit/lavezzo/alphaS/scetlib-mr9on`
> (detached at a7392be), build `build-mr9on`. Nothing under `scetlib-cms`,
> `scetlib-anltrans` or any other agent's build dir was touched.

- **Next action:** nothing outstanding for this round. If anyone picks up the
  low-qT construction (D-050/D-051), F-2 is the number to move: 0.1124 σ(α_s)
  below 24 GeV, of which only 0.0181 σ came from this MR.
- **Read F-2 before quoting any "the correction improves α_s" line.** It does not;
  it improves the window it targets by 3.6× and leaves an uncancelled 0.125 σ
  total.
- **Blocking on:** nothing. Do NOT merge (MR !8 is a prerequisite and is open).

---

## Log

### 2026-08-27
- MR !9 description rewritten and PUT via the API (MR still `opened`, sha
  b66f8de, target `autodiff-sigmaul`; nothing merged — MR !8 is a prerequisite
  and is still open). Copy kept at `mr9_description.md`.
- Worktree `/work/submit/lavezzo/alphaS/scetlib-mr9on` added **detached** at
  a7392be, on purpose: `muf-analytic-trans` is checked out in
  `scetlib-anltrans`, which is another round's tree, and git will not hand the
  same branch to two worktrees. The commit is pushed with
  `git push origin HEAD:muf-analytic-trans`, so the REMOTE branch (what the MR
  reads) advances while the local branch ref stays where the other worktree
  expects it. If you later want the local ref, fetch it; do not `update-ref` it
  under the other worktree.
- The change: `int ad_muf_anl = 0` -> `1` in `src/qT/ad/ad_state.cpp`, plus the
  `ad_data.hpp` doc block and the `set_muf_analytic` pybind docstring saying so
  and saying that mode 0 is kept as the A/B arm, not as a fallback.
- One measurement script, `mr9_default_on.py`, does all four checks in ONE
  process on ONE cache (`cache_260824b`, 210 bins, 24 params). That is not
  tidiness: two runs of the same baseline scatter by 0.3-3.7 pp of the response
  and two independently built caches part by up to 1.9e-03 in sigma at a
  displaced muF, while an in-cache A/B reproduces to 0.1 pp.
- Arm separation is proved, not assumed: THREE arms (mode 0, mode 1 = the new
  default, mode 1 + abl 32) give three different sums at x2 = 0.35
  (665.5413453161 / 665.6428816932 / 665.6445736511). `values_and_jacobian`
  memoises on the parameter vector alone, so `set_arm` drops `_cache_key` and
  `_hess_cache_key`; without that the A/B returns a perfect and wrong null.

---

## Findings

### F-1 — The invariants hold with the default ON, as numbers (`run_mr9.log`)
| check | value |
|---|---|
| built-in `ad_muf_anl` (read back through pybind) | **1** |
| central, max \|on/off − 1\| over covered gen bins | **0.000e+00** |
| κ_F = 0.5 response | **0.000e+00** |
| κ_F = 2 response | **0.000e+00** |
| mapped directions at exactly 0.000e+00 | **36 of 39** |
| directions that move | **3**, all `transition_points*`; **0** non-transition |
| `sizeof(ad::GlobalData)` in the pre-MR cache's rule header | **2424** B, and that cache LOADS (so this build's sizeof equals it — `layout_check` refuses a one-byte disagreement). Site 24, HardData 592, NodeData 3208 also unmoved. |
| arm separation, Σ over gen bins at x2 = 0.35 | off 665.5413453161 / on 665.6428816932 / clamp 665.6445736511 — **three arms, three sums** |

### F-2 — THE α_s PROJECTION GOES THE WRONG WAY, and the decomposition says why
This is the one number that does not improve, and it is the finding of the round.
Projection of the model/template residual onto dlnσ/dα_s from the same cache's
Jacobian, other nuisances profiled, σ(α_s) = 6.16e-04, quadrature over the three
transition directions (`alphas_attribution.py`):

| | qT < 24 | qT ≥ 24 | all bins |
|---|---|---|---|
| before | 0.0943 σ | 0.0845 σ | **0.0371 σ** |
| after | 0.1124 σ | **0.0237 σ** | **0.1247 σ** |
| after/before | 1.19× | **0.28×** | **3.36× WORSE** |

The split is EXACT, not a re-fit: the projection is linear in the residual at
fixed mask, weighting and basis, so `project(d) = project(d·1_lo) +
project(d·1_hi)` — verified column by column (`lo+hi` reproduces `total` to every
digit printed).

**Why the total worsens while the targeted window improves 3.6×:** the
pre-correction total was an ACCIDENTAL CANCELLATION. In every one of the three
directions the two windows carried opposite signs of near-equal size
(+0.075/−0.047, −0.015/+0.040, −0.055/+0.058 σ). Closing the high-qT half
destroys the cancellation and exposes the low-qT half. Of the 0.1124 σ left below
24 GeV, **0.0943 σ was already there before this MR**; 0.0181 σ is the −8 pp this
MR adds. So the correct reading is "the correction relocates the total from a
cancelling pair to an uncancelled low-qT residual of 0.125 σ(α_s) = 7.7e-05 in
α_s" — the same order as the transition group's own impact (~1.2e-04 of a 3.8e-04
total) — **not** "the correction breaks α_s".

**Caveat that must travel with the levels:** the reference is the production
`CorrZ` templates, whose central shape differs from ours (DYTurbo nonsingular vs
SCETlib's analytic V+jet), so the ABSOLUTE levels carry a reference-dependent
floor. The arm DIFFERENCE is clean (one cache, one process, arms proved
separated), and that is what the qT ≥ 24 gain and the qT < 24 loss are read from.

Against the same templates, mean |dev| improves in all three transition
directions (2.21e-04 → 2.06e-04, 8.59e-05 → 7.81e-05, 2.14e-04 → 1.63e-04) and
max |dev| in two of three. The residual DOES get smaller — it gets smaller in the
directions α_s does not care about. Absolute size never captured the overlap, and
here it disagrees with it.

### F-3 — The correction is FREE (`run_timing.log`)
Warm, one process, one cache (210 bins, 24 params), 16 threads, arms interleaved
round by round so the statistic is a paired ratio and load drift slower than one
round cancels.

| | off | on | paired on/off, 6 rounds |
|---|---|---|---|
| `values_and_jacobian` | 0.538 s | 0.552 s | median 1.020, mean 1.011 ± 0.022 |
| `hessian` | 48.00 s | 48.31 s | median 1.009, mean 1.013 ± 0.016 |

~1% on both, inside the ±2% scatter of the measurement itself — as the
construction predicts, since the added term reuses conv kinds the `fo_lvl = 2`
prefix already holds (no new grid, no new stored kind, no extra PDF call, no node
rebuild).

**Method note, worth keeping:** the first attempt timed all the off reps then all
the on reps and returned on/off = 0.90 for value+jacobian and 1.14 for the
Hessian — i.e. it could not distinguish 0% from 15%, because this login node
carries other jobs and the two blocks saw different load. The blocked design was
the problem, not the timer. Interleave.

---

## Decisions

- **Reported the α_s regression loudly rather than burying it** (F-2), with the
  decomposition that makes it interpretable and the caveat on the reference. The
  decision to turn the correction on is unaffected: the residual it leaves below
  24 GeV pre-existed it, and its apparent α_s neutrality before the flip was a
  coincidence between two errors of opposite sign, which is not a property worth
  preserving. It does raise the priority of the low-qT construction (D-050/D-051).
- **The off switch stays.** `set_muf_analytic(0)` is what let every number in
  this round and the last be measured as a clean A/B, and a reviewer will want
  it. The docstring now says it is an A/B arm rather than a fallback, so nobody
  reads "0" as the safe choice.
- **No new knob.** No env var, no config field, no WRemnants-side plumbing: the
  pybind setter already exists and is the documented route.
