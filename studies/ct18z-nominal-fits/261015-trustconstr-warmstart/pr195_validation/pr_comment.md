## Validation of this PR (claim → test → result)

Since the first version, this PR has a new commit, **117cc67**. When a warm leg stops on a face the loss wants to leave, it now leaves that face *warm*: a Newton release step along the releasing face's normal, with the binding faces held, followed by a new centred warm leg. scipy's own start (barrier 0.1) is now only a last resort. In the first version it was the fallback, and on a real fit it walked away from the minimum and cost about an hour to come back. Every check below is on 117cc67 and compares against `main` 2d9f380.

### 1. Does it solve the problem? A real fit, this PR only (no preconditioner)

The case: the saturated ptll-projection sub-fit of a SCETlib-AD reco fit (NP domain as 6 hard constraints), warm-started from the main fit's minimum with `--noFit`. This is exactly the case that exposed the old fallback. After the saturation parameters move, a curved NP face (multiplier -1.48 at slack 1.6e-9) wants to be released, and the warm leg stops on it at status 2. The reference is the same sub-fit run with the first version of this PR **plus** the trust-constr preconditioner companion PR.

| claim | test | result |
|---|---|---|
| a releasing face is left without a walk-away | sequence of legs, loss and violation | legs `warm, release-step, warm`; scipy's start is never used. The release step *lowers* the loss (335.5372832 → 335.5370706). Neither leg ever rises above its own start loss, and the maximum constraint violation is 0 throughout. The old fallback went 335.537 → 335.92 with a violated face (3.4e-3). |
| same answer | q = 2 dNLL and the saturated-fit parameters vs the reference | q **68.363489** vs **68.363489** (diff 3.4e-7); loss 335.5369528 vs 335.5369526; all 3759 parameters agree to ≤ 8.6e-5 σ; same constraint values and active faces |
| converged | scipy status | status 2 (trust radius < xtol with barrier < barrier_tol), optimality 6.6e-4, after the dual-sign check passed. The reference, which had the preconditioner, reached status 1 (gtol). |
| cost | iterations and wall time | 237 iterations / 13.0 h on a shared node at load average ~600: 125 + 112 iterations, of which ~38 in each leg are the trust-radius collapse tail. The reference with the preconditioner took about 173 iterations / ~2.7 h. The plain sub-fit of this fit never finished, so there is no plain number for this case. |

How to read this: the PR fixes the *correctness* problem here (no frozen status-2 stop on the face, no walk-away, same answer). The *speed* on this fit comes mostly from the preconditioner.

**Second real check (added 2026-10-19): the LAT sub-fit, this PR only (no preconditioner).** The start is centred on the main fit's final barrier (4.1e-10). It uses one warm leg; no face releases.

| | status | q = 2 dNLL | sat. loss | iterations / wall | point |
|---|---|---|---|---|---|
| plain (`main`) | 2, frozen on the active face (slack 9e-6) | 79.10694 | 336.9191733 | 226 / 12.8 h | — |
| **this PR only** | 2 (radius < xtol, barrier 4e-10), optimality 3.0e-4, no violation | **79.10711** | **336.9190863** | **115 / 11.3 h** | ≤ 2.5e-6 σ from the combined run |
| this PR + preconditioner | 1, optimality 2.5e-9 | 79.10711 | 336.9190862 | 89 / 3.6 h | reference |

The plain run's frozen stop leaves it 8.7e-5 higher in loss and 1.7e-4 lower in q. This PR alone reaches the same minimum as the combined run (Δq 6e-8) in half the plain run's iterations. The wall time is similar to the plain run's because the shared node was loaded. Neither case regresses.

### 2. Did it break anything CI does not cover? Before/after on `main` vs this PR

These are `rabbit_fit.py` runs on the CI test tensor and on the small test-model tensor. Every stored result leaf in every results group (data, asimov, each toy) is compared.

| claim | test | result |
|---|---|---|
| default minimizer untouched | CI nominal fit (impacts + 6 mappings), CI blinded fit, toys `-t 3`, saturated test + scan | **bit-identical** (worst \|diff\| 0)¹ |
| cold trust-constr + constraints untouched | `-t 0 --constraints Bounds 'bkg_norm<=-0.3'` | **bit-identical** |
| `--minimizerWarmStart off` restores the old behaviour | at every warm call site: saturated test, `--externalPostfit` refit, likelihood scan, toys | **bit-identical** |
| toys unaffected | `-t 3`, trust-constr + constraints, default `auto` (toys start cold) | **bit-identical** |
| scipy-internals guard really falls back | guard monkeypatched to fail; warm-hinted fit vs cold fit | **bit-identical** (Δx 0, nit 34 = 34) |
| warm sites give the same answers | `auto` vs before | saturated test: \|diff\| ≤ 3.9e-10, sub-fit 38 iterations (status 1) vs 69 (status 2). `--externalPostfit` refit: identical, 1 iteration vs 5. Likelihood scan: same curve to 3.2e-5 in dNLL, every point lower or equal (the old cold restarts stop with a larger barrier gap), 3-4 iterations per point vs 11-26 |
| test suite | `pytest tests` in the analysis container | 483 passed, 1 failed: a wall-clock assertion in `test_snapshot.py`, 19.9 s > 15 s at load average 680; it passes when rerun alone. isort / black / flake8 (CI selection) clean |

¹ The CI blinded config is nondeterministic from run to run on `main` too. The first `main` run converged at trust-krylov status 2; three repeats each of `main` and this PR all stalled and restarted. The parameters are identical either way, so that row compares everything except `minimizer_status`.

### Caveats

- The real checks are two sub-fits of one analysis (NOLAT, LAT). The faster real-fit numbers quoted in the PR description come from the run *combined* with the preconditioner PR, and the two contributions are not separated.
- On a hard face, `status 2` is what a warm leg ends on once the gradient left is below the loss noise (~1e-12). `minimizer_status` records `warm_start_legs`, `warm_start_releasing` and `warm_start_barrier`, so this can be audited per fit.
- The guard checks the scipy internals at run time. A scipy upgrade that changes them makes the warm start fall back to the cold start with a warning, and the pinned tests fail.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

