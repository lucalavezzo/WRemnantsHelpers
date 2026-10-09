# Reading a rabbit likelihood scan (`--scan <param>`)

What `rabbit_fit.py --scan` actually computes, what its curve does and does not
measure, what it costs, and how to get a parameter vector back out of it.

Established in `studies/alphas-scan-discontinuity/` (2026-09-21/22) on card
`260916_Z_2D_card_adcorr` — a 2D `ptll` x `yll` Z fit, 3720 parameters, 47 of them
through the SCETlib AD param model. Five scans, 70 points.
Last updated: 2026-09-22.

## A scan is a CONTINUATION, not a search

`rabbit.fitter.nll_scan` warm-starts each point from the **previous point's**
converged vector, resetting to the seed only when it switches from the negative to
the positive arm (`rabbit/rabbit/fitter.py:3283-3297`). So a scan **follows one
branch** of the profile; it does not look for the best solution at each value of
the scanned parameter.

Two consequences, both of which cost this study a wrong conclusion before they
were understood:

- **Where a scan curve jumps, the POSITION of the jump is not a measurable.**
  With more than one branch the true profile likelihood is the lower envelope, so
  two crossing branches give a kink, never a jump. A jump appears because the
  continuation tracks one branch until tracking fails, and where tracking fails
  depends on the step size and on the warm start. The branch STRUCTURE is
  physical; the snap POSITION is algorithmic. Do not quote it.
  (`studies/alphas-scan-discontinuity/LOGBOOK.md`, Q1 and Open questions.)
- **A scan cannot tell you whether two branches are two solutions.** Equal NLL is
  not equal parameters, and two curves that look separate need not be. The clean
  test is a **pair of fits at the same fixed parameter value, seeded from each
  candidate**, compared in the full parameter vector — freeze the parameter,
  `--externalPostfit` each seed, and diff. In this study two apparently distinct
  branches came out as the *same* solution at one test value (||dtheta|| = 1.35e-6),
  which no amount of scan-versus-scan comparison could have shown
  (`260921-two-solutions/LOGBOOK.md`).
  Useful floor for that test, measured on the same card: **two runs of the same
  fit from different starts differ by ||dtheta|| ~ 8.9e-4**. Anything below that is
  one solution; anything you want to call two must be well above it. And when a
  paired fit disagrees, check the EDM of both before concluding — an unconverged
  partner sits *above* the minimum and manufactures a difference (two of the three
  test values here were inconclusive for exactly that reason).

## Scans on different branches are on DIFFERENT grids

The step is scaled by **each branch's own** width:

```python
param_offsets = linspace(0, scanRange, scanPoints//2 + 1) * sqrt(cov[param, param])
```

so a scan seeded at a narrow branch takes smaller steps than one seeded at a broad
one and **no node coincides** (measured: 0.5215e-3 vs 0.2954e-3 in `alphaS` for the
two branches of card A). `--scanRangeUsePrefit` only changes the units, it cannot
align two grids. Two corollaries:

- `--scanRange 3.0` means three sigma **of the seed branch**, which is why a scan
  seeded at a narrow branch can sample a region far smaller than intended (and,
  in the other direction, put zero points inside one sigma on the side where the
  branch is about to end).
- To compare two solutions at the same parameter value, **freeze the parameter and
  seed from each**. Never interpolate a 3720-component parameter vector between
  scan nodes.

(Evidence: `260921-scan-extend/LOGBOOK.md` lines 88-97; `260921-two-solutions/LOGBOOK.md`.)

## Interpolate scan curves with a CUBIC, never linearly

Comparing two scans means interpolating one onto the other's grid (see above: the
grids differ). These curves are locally parabolic, so linear interpolation carries
a curvature error of order (step)^2 x curvature — which is *large* compared with
the agreement you are trying to measure.

Measured: the two unwalled scans of card A agree over their overlap to
**1.2e-6 NLL** under cubic interpolation. The same comparison done linearly gave
**0.0217**, and that number stood as a study conclusion for two days before it was
traced to the interpolation.
(`260921-scan-convergence-audit/LOGBOOK.md` finding 4, retiring the figure quoted
in `studies/scetlib-ad-param-model/260917-cachecorr-physics`.)

## Cost: every point is a full profile minimisation

A scan point is not a cheap continuation step; it is a complete minimisation over
all the other parameters, warm-started. Measured on card A (3720 parameters,
SCETlib AD param model, CPU): **28 non-central points in 19040 s = 11.3 min per
point**. Four cost estimates were made in this study and only the one built from a
measured point was right; the guesses ("20-40 min per scan", "~1 h") were out by an
order of magnitude. **Price a scan from a measured point of the same card, never
from intuition.** 15 points is hours, not minutes.
(`260921-scan-extend/LOGBOOK.md` finding 8.)

## What a scan stores — and `--scanSaveDetail`

By default `nll_scan` returns only `(scan_vals, dnlls)`. It stores **no per-point
parameter vector and no per-point EDM**; the `edmval` in the fitresult is the main
fit's, not any scan point's (`rabbit/rabbit/fitter.py:3262`). With `-v 4` the
per-point `OptimizeResult` and loss trace in the log are the only convergence
evidence that exists — and that evidence is a poor proxy, see
`rabbit_minimizer_tolerances.md`.

`--scanSaveDetail` fixes that: per point it stores the full parameter vector plus
`edmval`, gradient sup-norm, minimiser status, `nit`, `nfev` and wall time. It is
opt-in; the default path and `nll_scan`'s two-value return are unchanged.

**Where it lives (2026-09-22):** rabbit branch `feature/scan-save-detail`, commit
`4e90d32` ("Record parameters and convergence per likelihood-scan point"), off
`origin/main`, checked out in the worktree `/tmp/rabbit-scandetail`. **Not yet
PR'd to WMass/rabbit** — written for this study, to be upstreamed after use. The
commit is in the shared `WRemnants/.git/modules/rabbit` object store, so it
survives `/tmp`; `git worktree list` in `WRemnants/rabbit` finds it.

- The EDM is computed on the **floating subspace** (`edmval_hessfree_floating`, one
  CG solve, no dense Hessian). This matters: a full-space EDM at a scan point would
  report the scan's *depth* below the global minimum, not its *convergence*.
- Cost ~110 s/point, 10-15 % on top of the point's own minimisation.
- It is a pure observer: the re-run reproduced the original scan bit-identically
  (max |d(2 dNLL)| = 0.0 over 15 points, same host).
- Cross-check: `edmval_hessfree_floating` agrees with the dense-Hessian `edmval_cov`
  to 4 % (4.311e-10 vs 4.49e-10 at the same point).

(`260921-scanshift-detail/LOGBOOK.md` findings 2, 6, 7.)

## Reconstructing a scan point exactly (when the detail was not saved)

Verified bit-for-bit on card A: the reconstructed post-jump point came out at
373.55622344345 against the scan's 373.55622344344624.

1. Take the scan's **central** vector (that is the seed fitresult's postfit).
2. Overwrite the scanned parameter with the point's value,
   `linspace(0, scanRange, scanPoints//2 + 1)[k] * sqrt(cov[a, a])` off centre.
3. Write it as a flat `{x, parms}` hdf5.
4. Refit with `--externalPostfit <seed> --freezeParameters <param>`.

Only the k-th point of the arm the central vector belongs to is reachable this way
in one shot; deeper points need the chain, because the scan warm-starts from its
predecessor. Acceptance test before using any reconstructed point: its final
objective must match the scan's stored value to the last digits.
(`260921-jump-params/LOGBOOK.md` finding 7, `scripts/build_postjump_seed.py`.)

## Walled and unwalled scan curves are DIFFERENT OBJECTIVES

`nllvalreduced` — and therefore every point of a scan run with `-r` and
`--regularizationStrength` — **includes the regularizer penalty**
(`rabbit/fitter.py:2493-2512, 2534-2545, 3283`; `rabbit/bin/rabbit_fit.py:1181`).
A walled curve and an unwalled curve are minimising different functions, so their
depths are not comparable and they must not share a panel's vertical axis without
saying so. Reference each family to its own deepest minimum.
(`260921-scan-overlay-all/LOGBOOK.md` finding 2.)

## Cross-references

- `rabbit_minimizer_tolerances.md` — why `success`/`status`/`nit` from a scan point
  tell you nothing, and why only EDM ranks convergence.
- `profile_likelihood_pitfalls.md` — reading sigma(POI) once the fit has converged.
- `studies/alphas-scan-discontinuity/LOGBOOK.md` — the full narrative, and the
  physics case in which all of the above was established.

## Two mechanics worth knowing before you reconstruct a scan node

**A free curvature read-out.** `1/lambda_max(cov)` taken from any rabbit fitresult
reproduces the rigorously computed smallest Hessian eigenvalue to **6 digits** (validated
against the matrix-free Lanczos values 0.648 / 0.502 in
`studies/alphas-scan-discontinuity/260921-saddle-or-basin/`). So if a fit already saved its
covariance, you do not need a Hessian pass to ask "is this a minimum, and how soft".

**Seed a reconstruction from the TANGENT, not from the minimum.** A scan point deep in a
warm-start chain is far from the central minimum, and seeding a frozen-parameter refit there
makes trust-krylov crawl — starting loss ~1.8e4 in the measured case. Rabbit's default
`--stallRelTol=0.0` cannot detect a crawl (as opposed to a stall), so `--maxRestarts` never
fires and the fit simply grinds. Extrapolating a seed along the branch instead reproduced
five nodes to 1e-10. Evidence:
`studies/alphas-scan-discontinuity/260922-curvature-collapse/`.
