## Problem

`--minimizerMethod trust-constr` with `--constraints` refused `--precondition`:

> --minimizerMethod trust-constr does not support --precondition (the constraint Jacobian is not transformed to internal coordinates)

So a constrained fit could not use the preconditioner, and ill-conditioned fits lost it. The case that matters is the projected saturated sub-fit (`--computeSaturatedProjectionTests`), which has a condition number of 1e9–1e10. There, full-scope spectral preconditioning cut trust-krylov from 2150 to 614 HVPs. scipy's trust-constr has no preconditioner of its own: its projected-CG subproblem sees whatever Hessian it is given.

## Fix: the chain rule

Under `--precondition` scipy iterates in y, with theta = theta_ref + T y and T = L^-T, block-wise (`rabbit/preconditioner.py`). theta is affine in y, so:

- **values:** c(theta(y)) gives the same numbers, and they already went through `to_physical`. Linear rows stay linear.
- **Jacobian:** J_y = J T. New `Preconditioner.jac_to_internal`, the column half of `hess_to_internal`.
- **constraint HVP:** T^T (sum v_i d2c_i) T p. The map is linear, so it adds no second-derivative term.

Other changes:

- `build_nonlinear_constraints` takes optional `jac_to_internal` / `hessp_to_internal`.
  - The Jacobian is transformed on every call rather than cached, because its cache is keyed on the physical point and a restart rebuilds T without moving it.
- `Fitter.build_scipy_constraints(transform=...)` looks up the *current* preconditioner on each call, so a rebuild on restart is followed.
- `fit()` passes the transform and no longer refuses the combination.

## What is frame-dependent

**Frame-independent:**

- constraint values and bounds
- the Lagrange multipliers: T^T (grad f + J^T v) = 0 if and only if grad f + J^T v = 0, since T is invertible
- per-row `keep_feasible` and start-on-face handling
- the slack scaling of the barrier subproblem
- the face-held post-fit, which is computed afterwards at the physical point

**Frame-dependent:** every norm scipy takes over the variables. Its trust radius, `xtol`, and the KKT residual `optimality` compared with `gtol` are all measured in y, i.e. roughly per sigma. So:

- `minimizer_status` now reports `optimality_frame` ("physical" / "preconditioned"). When preconditioned, it also reports `optimality_physical` = ||grad f + J^T v||_inf in the fitter's own units.
- scipy's gtol exit does not wait for the barrier parameter, so a gtol exit can come at a different mu in the two frames. The fit then sits ~mu/v inside each active face, with an NLL excess of ~mu per face. The tests compare losses to within 2 mu.
- The `--precondition` help says this.

## Tests (`tests/test_trust_constr.py`)

- `test_preconditioned_constraint_jacobian_and_hvp_follow_the_chain_rule`: J_y and the y-space constraint HVP are checked against the dense transform and against finite differences in y. Swapping the transform (a rebuild) is followed by the same constraint object.
- `test_preconditioning_does_not_move_the_constrained_fit`: an ill-conditioned polynomial background (cond(H) ~ 1e5) with a binding linear row and a binding convex nonlinear row.
  - The minimum, the multipliers and the face-held covariance are the same with and without full-scope spectral preconditioning (|dx| ~ 1e-9 sigma).
  - It needs fewer HVPs: 357 vs 474.
- `test_saturated_test_is_unchanged_by_preconditioning`: end to end through `rabbit_fit.py --computeSaturatedProjectionTests` with `--precondition --preconditionParams '.*' --preconditionBlocks none --preconditionTransform spectral`.

The full suite passes: 471 tests.

On the same toy, the HVP saving grows with the condition number (plain vs preconditioned trust-constr, both rows binding):

| cond(H) | plain: it / HVPs | preconditioned: it / HVPs |
|---|---|---|
| 2.9e3 | 40 / 303 | 42 / 293 |
| 1.1e5 | 57 / 474 | 53 / 357 |
| 4.5e6 | 169 / 1336 (xtol exit, not converged) | 96 / 594 |

## Real fit

LAT is the nominal CT18Z reco fit with the lattice CS-kernel term. Its projected-ptll saturated sub-fit (`-m Project ch0 ptll --computeSaturatedProjectionTests`) has about 3760 parameters and six NP-domain hard constraints, two of them active. It was rerun from LAT's minimum with the full-scope spectral preconditioner:

| | plain trust-constr | preconditioned + warm start |
|---|---|---|
| exit | status 2 (`xtol`), optimality 6.6e-4 | status 1 (`gtol`), optimality 2.5e-9 (1.6e-6 in the fitter's own units) |
| saturated q = 2 dNLL | 79.10694 | 79.10711 |
| iterations / HVPs | 226 / 4667 | 89 / 982 |
| wall time | 12.8 h | 3.6 h (3.9x faster) |

- The two runs end at the same point to within 1.3e-4 sigma, with the same active faces and multipliers.
- **Caveat: these numbers were measured with this change and the warm-start change applied together** (companion PR below). The run does not separate the two contributions.

**When to use it: precondition warm fits (e.g. the saturated sub-fit, which starts at the nominal minimum), not cold ones.**

- The transform is built from the Hessian at the starting point. From a cold start far from the minimum, the whitened trust region allows steps the local quadratic model does not support.
- A cold nominal fit was measurably slower with it, and a toy reproduces the slowdown even with a transform built at the minimum, under unconstrained trust-krylov as well. This is a property of preconditioning far from the minimum, not of this change.
- The `--precondition` help now says so.

## Companion PRs

Two companion PRs are being opened in parallel. All three are independent and branch off `main`; they are not stacked.

- **warm start for trust-constr** (branch `tc-warmstart`). It touches the same constraint plumbing, so a small rebase conflict in `scipy_adapter` / `build_scipy_constraints` is likely, whichever merges second.
- **face-held impacts** (branch `face-held-impacts`).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
