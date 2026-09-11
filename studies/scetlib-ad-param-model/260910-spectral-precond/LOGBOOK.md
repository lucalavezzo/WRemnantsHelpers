---
title: Spectral preconditioning — does |H| whitening beat the ridge?
slug: 260910-spectral-precond
study: scetlib-ad-param-model
status: done          # active | done | paused | abandoned
created: 2026-09-10
updated: 2026-09-10
owner: study-worker
---

# Spectral preconditioning — does |H| whitening beat the ridge?

**Task:** does `--preconditionTransform spectral` beat both the plain (unpreconditioned)
and the ridge-preconditioned blinded data fit — in convergence, in cost, and in the
minimum it lands on?

---

## START HERE (status as of 2026-09-10)

> **No. Spectral preconditioning beats neither arm.** It is the slowest of the
> four by a wide margin — **719 iterations / 8594 s of `minimize()`**, against
> plain's 221 / 2645 s and ridge's 292 / 4049 s — and it lands on the
> **highest** loss of the three unwalled arms (412.785 vs 411.075 vs 405.561).
> It loses per iteration *and* per second, with the machine load running against
> the conclusion (plain ran at 2.8x spectral's loadavg and still won).
>
> The hypothesis was right about the mechanics and wrong about the consequence:
> spectral *did* do exactly what it promised at the reference point — condition
> number **4.22e+04 -> 1**, exactly, with **0 floored**, where the ridge managed
> only 1.75e+04. Reducing kappa to 1 made the fit slower. The reason the two do
> not follow from each other is that the transform is built **once, at the start
> point, where 25 of the block's 47 eigenvalues are negative**, and rabbit
> refreshes it only on a stall that never fired. See *Result*.
>
> Two things spectral **is** best at, and they should not be buried: **EDM
> 1.457e-07**, the best of all four (9500x plain's), and the mildest NP
> violation of the three unwalled arms (bare penalty 1.16e-04 against plain's
> 4.10e-03). It bought a *cleaner* minimum, not a *better* one, at 3.2x the cost.

- **Next action:** none for this arm — the question is answered. The one
  experiment that follows directly is in *Open questions* (§1): the same fit
  with a `--stallRelTol` large enough to actually fire, so the transform is
  rebuilt away from the saddle. That is a one-flag change.
- **Blocking on:** nothing.

---

## Comparability, stated first

Everything below shares:

- **card** `study_scratch/260910-anchor-verify/card_none.hdf5` (the anchor-carrying card)
- **cache** `scetlib_ad_caches/pdf62_corrgrid_260827/merged_full`
- **SCETlib** `b66f8de`, `libscet-qT.so` md5 `71b5e68a0cfed89326ff4ed521d37300`
- **model file** `260908-fit-770/lib/scetlib_tf.py` md5 `e60ed9304569bfb496988ef729885469`
  (the hvp zero-seed skip; without it the postfit Hessian pass costs ~77x more)
- **fitter** `rabbit.fitter` from the `blinding-additive` worktree at `0f64bbb`
  (additive POI blinding + physical-start frame shift, both asserted at launch)
- **data**, `-t 0`, production config with the NP sector **FREE**

Three caveats that do bear on the numbers:

1. **Wall time is confounded by machine load.** The four arms started at 1-minute
   loadavg 789 (plain), 278 (ridge), 340 (walled) and 284 (spectral) on a shared login
   node. The load-free cost metric is `nhev` — the count of Hessian-vector products,
   which is exactly what the Krylov inner solve spends and what preconditioning is
   supposed to reduce (`~sqrt(kappa)` per solve). Read `nhev` and `nhev/nit`, and treat
   seconds as corroboration only.
2. **The walled arm is not a like-for-like wall-clock comparison.** `DATAWALL5` ran
   *without* `--doImpacts` and without `--stallRelTol`, so its 29:49 total is short by
   the impacts pass the other arms paid (~20 min). Its `minimize()` time and `nhev` are
   comparable; its total wall is not.
3. **The walled arm's loss carries the wall penalty**, so its `fun` is not on the same
   footing as the three unwalled losses. From `../260910-wall-port`, its pure-NLL
   excess over plain is +5.78, i.e. `Delta(chi2) = +11.6`.

**Blinding:** `alphaS`'s central value is never printed here. `sigma(alpha_s)`, losses,
EDM, chi2 and p-values are all safe under additive blinding.

---

## Why this arm exists

`DATAPC2` — ridge preconditioning, the same 47-parameter scope this arm uses — made the
fit **worse**: loss 411.08 against the plain arm's 405.56, in 292 iterations instead of
221 and 4049 s of `minimize()` instead of 2645 s. Its own report says why:

```
all block has lam_min=-1.09e+03 (max|diag|=2.03e+04);
  ridge from the spectrum: 0.0593 x max|diag|
Preconditioning all block of 47 parameters from the reference Hessian
  (ridge 0.0593 x max|diag|): condition number 4.22e+04 -> 1.75e+04,
  of which degeneracy 1.08e+05, at the reference point
```

Two things are in that block. The reference Hessian is **indefinite** at the start point
(`lam_min = -1.09e+03 < 0`), so the Cholesky failed at the default `1e-8` ridge and the
code escalated to **5.9 % of max|diag|** to make it factorise at all. And
`rabbit/preconditioner.py` names that exact failure mode: a single scalar ridge
*"swamps every direction softer than |lam_min| and leaves them near-null"* — i.e. it
annihilates precisely the soft, near-degenerate directions (scale-free degeneracy
`1.08e+05`) that preconditioning was meant to fix. Hence a mere 2.4x on kappa, bought
with 82.5 s of reference-Hessian build and a worse minimum.

`spectral` factorises `|H| = Q |Lambda| Q^T` instead: each eigendirection gets its own
scale, the floor comes from the numerical **rank** rather than from a scalar
`--preconditionRidge`, and the **sign** of negative curvature survives (trust-krylov
uses negative curvature to escape saddles). That is the hypothesis.

### How to read the report — one trap

The after-side "degeneracy" is not printed, and on the spectral path it *could not*
meaningfully be: `preconditioner.py` shows that `B` and `|B|` share eigenvectors, so with
`|B| = L L^T` the congruence sends `Lambda` to its own signature and the **true kappa is
identically 1** for any block in which nothing was floored. A correlation number computed
from the Cholesky factor instead picks up the arbitrary orientation between `L` and the
eigenbasis, and reads 1.7 at m=5, 7.7 at m=12, 21 at m=30, 34 at m=60 — growing with
block size, i.e. worst exactly where `--preconditionBlocks none` sends you. So judge this
arm on the **before**-side kappa, on `n_floored`, and on the actual convergence. Not on
the after-side number.

---

## Log

### 2026-09-10 — launch

Command in `scripts/launch_spectral.sh`: byte-for-byte `DATAPC2` plus
`--preconditionTransform spectral`. `--preconditionBlocks none`,
`--preconditionFrom hessian` (default) and `--preconditionRidge` (default, ignored on
this path) are all left as they were — which is also what `preconditioner.py`'s
CHOOSING THE OPTIONS recommends under spectral: a larger block is always better or equal
there, since it whitens the cross-terms exactly where splitting discards them.

Accepted values checked in `rabbit/parsing.py` before launching, not assumed:
`--preconditionTransform` takes `choices=["ridge", "spectral"]`.

Harness copied from `../260910-blinding/scripts/`, `D=` repointed at this task's
`scripts/`, `incontainer.sh` left byte-identical (md5 `f6f87d5222a4d7d0342e3a940ea8f81e`)
so its rabbit-blinding assertion is preserved. The launch log confirms it fired:
`additive POI blinding present : True`, `physical-start frame shift : True`.

Own `-o` directory (`/ceph/.../260910_spectral`) and own `--snapshotFile`: `DATAPC2` was
still writing its postfit into `260910_blinding_final` when this launched, and two fits
sharing one snapshot overwrite each other.

- evidence: `logs/fit_DATASPEC_260910_173516.log`

### 2026-09-10 — the preconditioner report, verbatim

```
DEBUG:fitter.py: Preconditioner reference matrix (hessian) took 77.5 s
DEBUG:preconditioner.py: Preconditioning all block of 47 parameters by spectral
  whitening of |H| (lam in [-1.09e+03, 2.9e+04], 25 negative, 0 floored):
  condition number 4.22e+04 -> 1, of which degeneracy 1.08e+05,
  at the reference point  [alphaS, lambda2, lambda4, delta_lambda2, lambda2_nu,
  lambda4_nu, resumTNP_gamma_cusp, resumTNP_gamma_mu_q, ... +39 more]
INFO:preconditioner.py: Preconditioned 1 of 1 block(s), 47 parameters;
  condition number median 4.22e+04, worst 4.22e+04 -> median 1, worst 1
  at the reference point; of which degeneracy (scale-free) median 1.08e+05,
  worst 1.08e+05
```

Against the ridge arm's line, same 47 parameters and demonstrably the **same
reference matrix** — identical before-side `kappa = 4.22e+04` and identical
degeneracy `1.08e+05`, so the two arms differ *only* in the whitening:

| | ridge (`DATAPC2`) | spectral (`DATASPEC`) |
|---|---|---|
| floor | `ridge 0.0593 x max|diag|` (escalated from 1e-8) | none: **0 floored** |
| kappa at the reference point | 4.22e+04 -> **1.75e+04** | 4.22e+04 -> **1** |
| degeneracy arriving | 1.08e+05 | 1.08e+05 |
| reference Hessian build | 82.5 s | 77.5 s |

Three things worth stating.

**The block is violently indefinite, not marginally so.** `lam in [-1.09e+03,
2.9e+04], 25 negative` — **25 of 47** eigenvalues are negative at the start
point. This is a saddle region, not a neighbourhood of a minimum. That is the
whole reason the ridge had to escalate to 5.9 %: one scalar has to exceed
`|lam_min|` to restore definiteness, and doing so flattens the 25 negative
directions *and* every positive direction softer than 1.09e+03.

**The `-> 1` is exact here, not the documented artefact.** The artefact caveat
in `preconditioner.py` is about the after-side **degeneracy** (correlation
number), which is deliberately not reported. The after-side number that *is*
reported is the true condition number (`_cond_true`), and the docstring's
identity — `B` and `|B|` share eigenvectors, so the congruence sends `Lambda`
to its own signature and true kappa is identically 1 — holds *"only where
nothing was floored"*. `0 floored` is printed, so the condition is met and
`kappa = 1` is the real value. Ridge, by contrast, reached only 1.75e+04, a
2.4x reduction on a 4.22e+04 problem.

**Start point is controlled.** All four arms report the identical prefit linear
chi2 `804/780, p = 26.61%`, and plain and spectral report the identical
iteration-0 loss `4751.520787280669`. (Ridge's iteration-0 loss is 4183.8
because its first trust-region step was *accepted*; walled's is 4752.07 because
its loss carries the wall penalty. Neither indicates a different start.)

`--preconditionParams 'b0_over_bmax_nu' matched no parameters` — same benign
warning as the ridge arm; that knob is not a fitted parameter on this card, and
the scope is 47 parameters in both arms.

- evidence: `logs/fit_DATASPEC_260910_173516.log`

### 2026-09-10 — the three reference arms, read from their own logs

`nhev` is the number the preconditioner is judged on. Per iteration it is **2.1x worse**
under the ridge (7.15 vs 3.47) — the inner Krylov solve became *harder*, which is the
direct signature of near-null whitened directions, not of a reduced kappa.

| arm | `fun` | nit | nfev | nhev | nhev/nit | minimize | s/nit | EDM | sat. p |
|---|---|---|---|---|---|---|---|---|---|
| plain `DATABLIND` | 405.561 | 221 | 209 | 766 | 3.47 | 2645 s | 12.0 | 1.386e-03 | 2.33 % |
| ridge `DATAPC2` | 411.075 | 292 | 290 | 2087 | 7.15 | 4049 s | 13.9 | 4.909e-06 | 1.20 % |
| walled `DATAWALL5` | 411.991\* | 138 | 137 | 624 | 4.52 | 1509 s | 10.9 | 9.632e-07 | 1.07 % |

\* includes the wall penalty; pure-NLL excess over plain is +5.78.

All three exit `status: 2`, *"A bad approximation caused failure to predict improvement"*,
`success: False`, and all three then complete their postfit with `Exit status: 0`.

**The arms are not landing in the same basin.** Plain sits 5.51 in NLL *below* the ridge
arm (`Delta(chi2) = 11.0`) and 5.78 below the walled arm's pure NLL
(`Delta(chi2) = 11.6`) — and yet has an EDM 280x *worse* than the ridge arm and 1440x
worse than the walled one. That pattern is already on record for this likelihood
(`knowledge/`, `np-wall-local-minima`): it is **multimodal, with the deeper optimum in
the unphysical NP region**. So a lower loss is not automatically the better fit here, and
"does spectral win?" has to be answered on convergence *and* on where in the NP space it
stops — not on `fun` alone.

- evidence: `../260910-blinding/logs/fit_DATABLIND_260910_151034.log`,
  `../260910-blinding/logs/fit_DATAPC2_260910_162332.log`,
  `../260910-wall-port/logs/fit_DATAWALL5_260910_165137.log`

### 2026-09-10 — postfit curvature: all reference arms sit at genuine minima

`rabbit` does not report this on the iterative path — its Cholesky
positive-definiteness check lives in the `--forceLinear` quadratic branch only
(`fitter.py:2675`) — but the saved covariance *is* `H^-1` at the postfit point,
and a symmetric matrix and its inverse have eigenvalues of the same sign. So
counting negative eigenvalues of `cov` counts them in the postfit Hessian
(`scripts/postfit_curvature.py`):

| arm | neg. eigenvalues of postfit cov (3720 params) | neg./NaN variances | kappa(cov) |
|---|---|---|---|
| plain | **0** | 0 / 0 | 2.98e+09 |
| ridge | **0** | 0 / 0 | 4.62e+10 |
| walled | **0** | 0 / 0 | 2.06e+08 |

So the 25-of-47 negative eigenvalues are a property of the **start point**, not of
where any arm stopped: every arm ends on a positive-definite Hessian and no sigma
is NaN. The `status: 2` exits are a trust-region step-quality complaint, not a
failure to reach a minimum. (Note the walled arm's postfit is also the
best-conditioned of the three, by an order of magnitude over plain and two over
ridge.)

- evidence: `logs/curvature_260910_174734.log`

### 2026-09-10 — the trajectory, which is where spectral shows its hand

Loss at matched iteration count, read from the four run logs:

| iteration | plain | ridge | walled | spectral |
|---|---|---|---|---|
| 25 | 878.5 | 695.3 | 730.7 | 854.4 |
| 50 | 566.5 | 522.6 | 566.2 | **679.5** |
| 75 | 425.3 | 480.5 | 427.3 | **610.9** |
| 100 | 414.7 | 454.4 | 412.2 | **597.9** |

Spectral is the **slowest of the four per outer iteration** from iteration ~50
onward — despite being the only arm whose reference-point condition number is
exactly 1. That is the opposite of what `~sqrt(kappa)` Krylov cost predicts, and
it is the central result of this task.

- evidence: `loss_trajectories.png` / `.pdf` (+ `.log` with the exact command),
  `scripts/plot_trajectories.py`

### 2026-09-10 — it loses on the time axis too, and NOT because its steps are rejected

Two things had to be checked before calling the per-iteration result a verdict.

**(1) Are spectral's iterations cheaper?** Yes, by 2x — 5.8 s/iteration against
plain's 12.0 — so per-iteration progress could in principle have been the wrong
axis. It is not. Loss at matched **elapsed seconds** inside `minimize()`:

| elapsed | plain | ridge | walled | spectral |
|---|---|---|---|---|
| 500 s | 576.9 | 479.9 | 454.0 | **602.5** |
| 900 s | 427.1 | 451.6 | 412.2 | **536.2** |
| 1500 s | 410.7 | 426.6 | 412.0 | — |
| 2000 s | 405.6 | 414.3 | — | — |

Spectral is last on both axes. And the load confound runs *against* the
conclusion, not for it: the plain arm ran at loadavg **789** against spectral's
**284** on the same shared node, and still beat it at every mark.

**(2) Is it just rejecting more steps?** No — and this is the informative part.
Counting iterations whose loss is bit-identical to the previous one (a rejected
trust-region step):

| arm | iterations | accepted | rejected |
|---|---|---|---|
| plain | 221 | 169 (76.8 %) | 51 (23.2 %) |
| ridge | 292 | 236 (81.1 %) | 55 (18.9 %) |
| walled | 138 | 101 (73.7 %) | 36 (26.3 %) |
| spectral | 720 | **606 (84.3 %)** | **113 (15.7 %)** |

*(the spectral row is the FINAL count, filled in after the run; the interim
figure quoted here earlier was ~24 %, from the first 135 iterations.)*

Spectral rejects the **fewest** steps of the four and still makes the least
progress: its steps are **accepted and short**. That rules out the obvious story
— whitening producing wild steps the trust region threw away — and points at a
different one, see *Result*.

### 2026-09-10 — DATASPEC stopped at 2 h 28 m, still descending

It did not converge. Final state of the minimizer, from its own log:

```
Iteration 714: loss 412.78495386441267  [dt=323.72s elapsed=7954.30s]
Iteration 717: loss 412.7846234158764   [dt=599.45s elapsed=8576.26s]
Iteration 719: loss 412.7846233862512   [dt=13.97s  elapsed=8593.60s]
Wrote parameter snapshot (signal-SIGTERM) to .../snapshot_DATASPEC.hdf5
Elapsed (wall clock) time: 2:27:43      Exit status: 143
Maximum resident set size: 193290648 kbytes (184 GiB)
```

Single outer iterations were costing **324 s and 599 s** at the end — a Krylov
inner solve of five to ten minutes per outer step — while the loss moved by
3e-4. That is *exactly* the symptom the preconditioner module's docstring opens
with: *"outer iterations that cost minutes and return a bit-identical loss."*
Spectral preconditioning did not remove it; by the endgame it is producing it.

It was stopped with SIGTERM at **8594 s of `minimize()`**, against the plain
arm's 2645 s and the ridge arm's 4049 s — both of which had *finished* — and at
a loss of **412.785**, above both. Letting it run could not have changed the
verdict, and it was holding 184 GiB and 128 threads against another session's
work. `--snapshotFile` is what made stopping safe: rabbit wrote a
`signal-SIGTERM` snapshot, so the reached point is recoverable exactly.

**One number is unavailable for this arm and cannot be recovered:** scipy never
returned an `OptimizeResult`, so there is no `nhev` — the single
load-independent cost metric is the one the stop costs us. `nit` and the
`minimize()` clock are from rabbit's own callback and are exact.

EDM, `sigma(alpha_s)` and the saturated chi2 come from rabbit's documented
two-pass recipe (`bin/rabbit_fit.py:613-619`): `--noFit --externalPostfit` on a
file carrying no covariance — a snapshot does not — makes rabbit compute the
exact Hessian, `edmval` and covariance **at the loaded point**. Those numbers
are therefore honest measurements at the *stopping* point and are **not**
measurements at a minimum. `scripts/launch_readout_pass.sh`.

- evidence: `logs/fit_DATASPEC_260910_173516.log`,
  `logs/readout_DATASPECPF_260910_200407.log`

---

## Result

**Read the caveats first.** All four arms share card, cache, SCETlib `b66f8de`,
`rabbit 0f64bbb`, real data, `-t 0` additive blinding, production config with
the NP sector free. Three differences do bear on the numbers:

1. **Spectral did not converge on its own; it was stopped.** SIGTERM at
   iteration 719 / 8594 s, still descending, `Exit status: 143`. Its loss and
   iteration count are exact (rabbit's own callback); its **`nhev` does not
   exist**, because scipy never returned an `OptimizeResult` — so the one
   load-independent cost metric is missing for exactly the arm being judged.
2. **Spectral's postfit numbers come from a second process**, rabbit's two-pass
   `--noFit --externalPostfit <snapshot>` recipe, not from the fit process. For
   EDM, the covariance and `sigma(alpha_s)` that is equivalent by construction
   (the same exact Hessian at the same point). For the **linear chi2 it may not
   be** — see the anomaly flagged below.
3. **Wall clock is load-confounded** (loadavg at launch: plain 789, ridge 278,
   spectral 284, walled 340) and the **walled arm ran without `--doImpacts`**,
   so its total wall is short by ~20 min. `minimize()` seconds and iteration
   counts are the comparable cost numbers; the walled arm also carries a wall
   penalty inside its loss.

### The four-way comparison

| | plain `DATABLIND` | ridge `DATAPC2` | **spectral `DATASPEC`** | walled `DATAWALL5` |
|---|---|---|---|---|
| loss (`fun`) | **405.561** | 411.075 | 412.785 *(stopped)* | 411.991 (incl. penalty) |
| `Delta(chi2)` vs plain | 0 | +11.03 | **+14.45** | +11.56 (penalty removed) |
| iterations | 221 | 292 | **719** | 138 |
| `nhev` | 766 | 2087 | *(unavailable)* | 624 |
| `minimize()` | 2645 s | 4049 s | **8594 s** | 1509 s |
| total wall | 1:04:19 | 1:11:02 | **2:27:43** (SIGTERM) | 0:29:49 (no impacts) |
| exit | status 2, rc 0 | status 2, rc 0 | **rc 143** | status 2, rc 0 |
| **EDM** | 1.386e-03 | 4.909e-06 | **1.457e-07** | 9.632e-07 |
| postfit Hessian: neg. eigenvalues | 0 | 0 | **0** | 0 |
| saturated `2*dNLL` / 733 | 811.12 | 822.15 | **825.57** | 823.98 |
| saturated p | **2.33 %** | 1.20 % | **0.96 %** | 1.07 % |
| `sigma(alpha_s)` | 0.001321 | 0.000877 | **0.000856** | 0.001097 |
| NP conditions violated | 2/8 | 2/8 | 3/8 | 1/8 |
| NP bare penalty | 4.10e-03 | 1.22e-02 | **1.16e-04** | 2.95e-05 |

Minimizer message, identical for the three that ran to a scipy exit:
*"A bad approximation caused failure to predict improvement"*, `success: False`,
`status: 2` — a trust-region step-quality complaint, not a failure to reach a
minimum. The **Cholesky question has a clean answer**: every arm's postfit
covariance has **zero negative eigenvalues and zero NaN variances**, so all four
sit on positive-definite Hessians. The 25-of-47 negative eigenvalues belong to
the **start point** only.

### So: does spectral beat either arm?

**On cost, no, decisively.** 3.2x plain's `minimize()` time and 2.1x ridge's,
for 3.3x and 2.5x the iterations. And the confound runs against it: plain ran
at loadavg 789, spectral at 284.

**On the minimum found, no.** 412.785 is the highest of the three unwalled
losses, `Delta(chi2) = +14.45` above plain.

**On convergence quality, yes — and this is the one real win.** EDM
**1.457e-07**, best of all four: 9500x plain's 1.386e-03, 34x ridge's, 6.6x the
walled arm's. Spectral genuinely nailed its minimum. It just picked a worse one
and took 2.4 h to do it.

### Why kappa = 1 did not help

The transform did exactly what the module promises, and this is worth stating
plainly because it *exonerates the implementation*: `4.22e+04 -> 1` with
`0 floored`, on the same block and the same reference matrix the ridge saw
(identical before-side kappa and identical degeneracy `1.08e+05`), where the
ridge managed only `1.75e+04`. The theory that `sqrt(kappa)` bounds the Krylov
work then predicts spectral should have been the *fastest*. It was the slowest.

Three measurements narrow the reason.

- **Its steps are not being rejected — it rejects the fewest of the four.**
  Counting iterations whose loss is bit-identical to the previous: walled
  26.3 %, plain 23.2 %, ridge 18.9 %, **spectral 15.7 %**. It accepts the most
  steps and makes the least progress, so its steps are **accepted and short**.
- **Its iterations are not individually expensive** — 12.0 s/iteration, exactly
  plain's — until the endgame, where single iterations cost **324 s and 599 s**
  while the loss moves by 3e-4. That late blow-up is the *classic* Krylov
  pathology, appearing in the arm that was supposed to cure it.
- **The transform is never refreshed.** `Preconditioner reference matrix` appears
  **once** in the log and `restarting` **zero** times, in every arm. rabbit
  rebuilds only when `--earlyStopping`/`--stallRelTol` fires, and at
  `1e-5 x |ref|` over a 100-iteration window that test never came close to
  firing on any arm.

Put together, the most economical reading — and it is a **hypothesis, not a
measurement**: whitening by `|H|` at a point where **25 of 47 eigendirections
are negative** sends every one of them to curvature `-1`, the same *magnitude*
as the positive directions. The docstring presents sign-preservation as the
feature (*"trust-krylov exploits negative curvature to escape saddles"*), and it
is — when negative curvature is a minority report. Here it is the majority, and
after whitening it is no longer subdominant in magnitude either, so the
subproblem has no interior Newton solution and every step is a boundary step of
length `Delta`, the trust radius, grown only by factors of 2 on success. In the
unwhitened coordinates the 22 stiff positive directions dominate the Krylov
solve and the fit takes long interior steps instead. The distances below support
this: preconditioning of *either* kind moved the fit out of the basin the
unpreconditioned fit finds.

### Two basins, not four points

L2 distance between arms over the 46 model parameters (alphaS excluded so
nothing unblinds):

| | plain | ridge | spectral | walled |
|---|---|---|---|---|
| plain | 0 | 4.19 | 4.06 | **1.34** |
| ridge | 4.19 | 0 | **1.26** | 4.08 |
| spectral | 4.06 | **1.26** | 0 | 4.06 |
| walled | 1.34 | 4.08 | 4.06 | 0 |

Two clusters: `{plain, walled}` and `{ridge, spectral}`, ~4 apart. **Both
preconditioned arms found the same, different basin** — which is a statement
about preconditioning as a physics intervention, not only a numerical one. It is
also consistent with the known multimodality of this likelihood
(`knowledge/30_physics_global/np_parametrization_constraints.md` §11, and the
`np-wall-local-minima` study).

### The physics read

Against `AN-25-085` `detector_extraction.tex` Tab. `z-reco-ho-results`, which
quotes `alpha_s(mZ) = 0.11800 +/- 0.00099` for SCETlib N3+0LL + DYTurbo NNLO and
`+/- 0.00098` for CT18Z: our four `sigma(alpha_s)` are 0.000856-0.001321, the
right order. **They are not comparable to the AN number** — that is a 4D
`(ptll, yll, cosTheta*, phi*)` template fit with the NP model *not* free, this
is a 2D `ptll x yll` 780-bin SCETlib-AD fit on blinded data with 8 NP lambdas
floating — so the agreement in magnitude is reassurance, not a cross-check.

The number that matters here is the **spread**: `sigma(alpha_s)` varies by
**54 %** across the four arms (0.000856 to 0.001321), and the variation is
entirely *which local minimum the optimizer stopped in*. With the NP sector free
on this card, `sigma(alpha_s)` is **not yet a well-defined quantity**; it is a
property of the basin. The tighter values (0.00086, 0.00088) belong to the
preconditioned basin, and are tighter precisely because the NP directions are
better determined there — the same basin whose saturated p-value is *worse*
(0.96-1.20 % against plain's 2.33 %). A tighter error bar from a worse-fitting
point is not a better measurement.

On the NP functions themselves, the spectral tune is the **mildest unwalled
violation** found so far: 3/8 conditions negative but a bare penalty of
**1.16e-04**, 35x smaller than plain's 4.10e-03 and 105x smaller than ridge's
1.22e-02, and within a factor 4 of the *walled* arm's 2.95e-05. Its CS kernel
anti-damps only above `b_T = 10.8 GeV^-1`, far outside the region the data
constrain, where the plain arm's anti-damps below `1.04 GeV^-1` — inside it.
So the preconditioned basin is the more physical one, at `Delta(chi2) = +14.4`.
That is the same tension the `np-wall-local-minima` study recorded and the NP
constraints note calls *"physics, not a numerical problem"*: the data prefer an
unphysical NP tune, and every route to a physical one costs roughly this much
likelihood.

### One number I do not believe, and am reporting anyway

The **linear chi2** does not follow the loss. Spectral reads **775/780
(p = 54.17 %)** against plain 809 (22.66 %), ridge 820 (15.74 %), walled 818
(16.54 %) — i.e. spectral looks like *by far* the best fit on that statistic
while having the **highest** saturated `2*dNLL` (825.57, the worst) and the
highest NLL. Those two cannot both be right. Two candidate explanations, neither
tested: spectral's postfit ran in a separate `--noFit --externalPostfit` process
(a different code path from the other three), and rabbit prints the raw chi2
under the label `chi2/ndf`, a known reporting trap in this codebase. **Trust the
saturated `2*dNLL`** — it is the likelihood-ratio test, it is computed from the
same machinery in all four arms, and it orders the arms exactly as the loss
does.


---

## Findings

1. `--preconditionTransform spectral` reduces the block's true condition number
   **exactly to 1** (`4.22e+04 -> 1`, `0 floored`) where the ridge reaches only
   `1.75e+04` — the implementation does what it claims — **and the fit gets
   slower, not faster**: 719 iterations / 8594 s against plain's 221 / 2645 s.
   kappa at the reference point is not predictive of cost here. —
   (evidence: `logs/fit_DATASPEC_260910_173516.log`, `loss_trajectories.png`)
2. The `-> 1` on the spectral path is a **real measurement, not the documented
   artefact**. `preconditioner.py` flags the *degeneracy* (correlation number)
   as an artefact after whitening; the number actually printed after the arrow is
   `_cond_true` of the whitened block, and the identity that makes it 1 holds
   *"only where nothing was floored"* — `0 floored` is printed. —
   (evidence: `rabbit/preconditioner.py:581-621`, log line)
3. The reference Hessian is **indefinite on more than half the block**: `lam in
   [-1.09e+03, 2.9e+04]`, **25 of 47 negative**, at the start point. That, not a
   badly chosen ridge parameter, is why `DATAPC2`'s ridge had to escalate to
   5.9 % of `max|diag|`. —
   (evidence: `logs/fit_DATASPEC_260910_173516.log`)
4. **The transform is built once and never rebuilt.** rabbit refreshes it only
   when `--earlyStopping`/`--stallRelTol` fires (`fitter.py:2620-2634`, whose own
   comment says a transform built at the start *"no longer conditions anything"*
   once the fit has moved). At `--stallRelTol 1e-5` over 100 iterations that test
   fired **zero times in any arm**. Every preconditioning result recorded here is
   therefore a result about *start-point* whitening. —
   (evidence: `grep -c restarting` = 0 in all four logs)
5. **Preconditioning changes which minimum you get.** L2 over the 46 model
   parameters clusters the arms as `{plain, walled}` and `{ridge, spectral}`,
   ~4 apart — both preconditioned arms found the same *different* basin, worse in
   NLL (`Delta(chi2)` +11.0 / +14.4) but **more physical** in the NP sector
   (bare penalty 1.16e-04 vs 4.10e-03) and tighter in `sigma(alpha_s)`
   (0.00086 vs 0.00132). A preconditioner is not a neutral numerical device here. —
   (evidence: `logs/compare_260910_202620.log`)
6. **`sigma(alpha_s)` spans 54 % across arms** (0.000856-0.001321) on identical
   inputs, purely by basin. With the NP sector free on this card it is a property
   of where the optimizer stopped, not of the data. —
   (evidence: same)
7. All four arms end on **positive-definite** postfit Hessians (0 negative
   eigenvalues in `cov`, 0 NaN variances), so `status: 2` is a step-quality
   complaint and not a convergence failure. rabbit does not report this on the
   iterative path — its Cholesky check is in the `--forceLinear` branch only —
   but `cov = H^-1` makes it a one-line measurement. —
   (evidence: `logs/curvature_final_260910_202813.log`,
   `scripts/postfit_curvature.py`)
8. **rabbit bug worth an upstream issue:** `--externalPostfit` together with
   `--noBinByBinStat` crashes with `ValueError: None values not supported` in
   `_profile_beta` — `load_fitresult` ends with `if profile: self._profile_beta()`
   (`fitter.py:563`) gated on `--noPostfitProfileBB` rather than on whether
   bin-by-bin stat exists. It crashes *after* `"Results written in file ..."`, so
   it leaves a 44 KB stub that looks like output. Workaround: pass
   `--noPostfitProfileBB`. —
   (evidence: `logs/readout_DATASPECPF_260910_200407.log`)

---

## Open questions

1. **The experiment this one implies.** Rerun spectral with a `--stallRelTol`
   that actually fires (1e-3, say, with `--maxRestarts` left at its -1 default),
   so the transform is **rebuilt** at the point the fit has reached rather than
   at a 25-negative-eigenvalue saddle. Every conclusion here is about whitening
   at the *start point*; the rebuild path exists, costs one Hessian (~80 s), and
   has never been exercised on this model. This is the single highest-value
   follow-up and it is a one-flag change.
2. **Is the `{ridge, spectral}` basin the one we should be fitting in?** It is
   worse in NLL by `Delta(chi2) ~ 11-14` but markedly more physical in the NP
   sector and tighter in `sigma(alpha_s)`, and the walled arm pays almost the
   same `Delta(chi2)` (+11.6) to get somewhere else again. Four points, three
   basins, one wall: which is the fit we quote is now a live question and is not
   this task's to settle.
3. **The linear-chi2 anomaly** (spectral 775/780 vs its own worst-in-class
   saturated 825.57). Reproducible in one command: rerun any converged arm's
   postfit through `--noFit --externalPostfit` and see whether its linear chi2
   moves. If it does, the statistic is path-dependent and nothing should be
   quoted from it.
4. **Does `--preconditionBlocks auto` change the picture under spectral?** The
   docstring says a larger block is always better or equal under spectral, which
   is why `none` was used — but that argument is about kappa, and kappa turned out
   not to predict cost. A block decomposition would leave fewer negative
   directions whitened to `-1` in any single subproblem.
