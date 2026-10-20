### Validation of this PR beyond CI

**Did it solve the problem it claims to solve, and did it introduce new ones?**

- Each check below runs the same `rabbit_fit.py` config from two worktrees, `main` (2d9f380) and this PR (c76c226).
- The comparison walks every stored leaf of `results`: hist values and variances, covariances, `minimizer_status`, and every scalar. Only wall-clock leaves are skipped.
- Test tensors are made as CI makes them (`tests/make_tensor.py`), plus the order-8 polynomial toy from `tests/test_preconditioner.py`.

| claim / risk | test | result |
|---|---|---|
| no change to unconstrained fits | CI "nominal fit" config (impacts, global impacts, hists, cov, variations, 4 mappings), trust-krylov | **bit-identical** (231 leaves) |
| no change to `--precondition` under trust-krylov | same + `--precondition --preconditionParams '.*' --preconditionBlocks none --preconditionTransform spectral` | **bit-identical** (226 leaves) |
| no change with a penalty term (`-r`) | CI regularization config `-r SVD Select ch0_masked` + the same preconditioner | **bit-identical** (40 leaves) |
| no change on an ill-conditioned toy | polynomial toy, preconditioned trust-krylov | **bit-identical** (24 leaves) |
| no change to trust-constr without `--precondition` | binding `--constraints Bounds 'bkg_2_norm<=-0.2'` + `--computeSaturatedProjectionTests` | **bit-identical** (77 leaves); only new key `minimizer_status/optimality_frame = "physical"` |
| multi-device | trust-constr + constraints + preconditioner + `--nDevices 2` | refused up front, as on `main` ("--constraints is not supported (not tested) with --nDevices > 1") |
| face-held post-fit under the transform | the trust-constr config above, with vs without the preconditioner | same active face and multiplier (−3.405695017 both); face-held cov equal to 2e-8 relative; parameters equal to 1.4e-9 σ; NLL +2e-9 (barrier offset) |
| it does what it claims (toy) | same pair, CI tensor | plain trust-constr saturated sub-fit **hits maxiter** (500 it, optimality 1.2e-4); preconditioned **converges in 48 it** (gtol); main fit 53 → 27 it |
| constraint Jacobian/HVP are right on real constraints | the 6 NP-domain rows (including cubic ones) of our analysis, at a real fit iterate, dense spectral T over 3720 parameters | y-frame J·p vs finite differences ≤ 3.4e-8 relative; Tᵀ∇²cT·p ≤ 2e-11 |

**Real fit, this PR alone.** Saturated ptll sub-fit of our nominal Z fit: about 3760 parameters, 6 hard constraints, 2 active. Each run starts from the same postfit and uses the same flags; the only difference is the rabbit commit.
- HVP = projected-CG iterations (`cg_niter`), which are about 90% of the cost.
- Wall times are not comparable because of node contention (the isolated run's cache load took 2.4 h, against 31 s for the combined run). Use the counts.

| | plain trust-constr (main) | **this PR only** | this PR + warm-start PR |
|---|---|---|---|
| exit | `xtol` (status 2), optimality 6.6e-4 | **`gtol` (status 1), optimality 1.6e-9** (1.1e-6 in fitter units) | `gtol`, optimality 2.5e-9 |
| iterations / HVPs | 226 / 4667 | **167 / 1504** | 89 / 982 |
| iterations spent at the first barrier stage μ₀ = 0.1 | 101 | **39** | 0 (starts at small μ) |
| saturated q = 2ΔNLL | 79.10694 | **79.10711** | 79.10711 |
| distance from the combined run's minimum | max 1.3e-4 σ (plain is not converged) | **max 3e-8 σ**, Δq = −5e-8 | — |

Same active faces and multipliers in all three (−207.46 and −1.913).

What this shows:
- This PR alone cuts the HVPs 3.1× and turns an `xtol` stop into a converged `gtol` exit at the better minimum.
- It shortens scipy's μ₀ = 0.1 stage but does not remove it; that is the warm-start PR's job. Together: 4.75× in HVPs.
- The barrier-ladder tail of rejected steps at small μ (71 rejected steps here) is still there with the preconditioner.

**Known limitation: cold starts are slower.** From a cold start, preconditioning is slower: our cold nominal fit trailed the unpreconditioned one at equal time.
- The transform comes from the Hessian at the start point, and far from the minimum the whitened trust region allows steps the local model does not support.
- A toy reproduces this even with T built at the minimum, and also under unconstrained trust-krylov, so it is a property of preconditioning far from the minimum, not of this PR.
- Documented in the `--precondition` help: precondition warm fits (e.g. the saturated sub-fit), not cold ones.

The full suite passes on the PR branch (471).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
