## Impacts at an active `--constraints` face, with the faces held

When a trust-constr fit (#189) ends on an active hard-constraint face, the post-fit stores the face-held
covariance as `cov`. The Hessian-based impacts were then skipped (`--doImpacts`, `--gaussianGlobalImpacts`).
This PR computes them with the faces held and removes the skip.

### What was missing

`cov` was already face-held, but three things in the traditional impacts were not:

1. **Stat / binByBinStat covariances.** `_cov_stat_floating` inverts the Hessian's stat block (POI + POU +
   unconstrained) directly. That lets the fit move through the face.
2. **Singular group blocks.** A group's conditional uncertainty `v C_gg^-1 v^T` is singular whenever a face
   normal lies entirely inside the group: the face-held `C` has zero variance along that direction.
3. **0/0 for bound-held parameters.** For a bound on one parameter, the SVD null space leaves O(1e-17) in
   that parameter's row. Its ungrouped impact `C_pj / sqrt(C_jj)` was then round-off divided by round-off.

The `--gaussianGlobalImpacts` skip was never needed. `_dxdvars` already uses `self.cov`, and the face-held
covariance gives the exact first-order response of the constrained minimum: `dx = -C_held d(grad)/d(obs)`,
by the implicit-function theorem on the KKT system. The constraints do not depend on the global observables.

### The fix

- `constraints/postfit.py`
  - `face_tangent_basis`: an orthonormal basis of the directions along the faces. A coordinate pinned by a
    single-parameter row gets an exactly zero row, so a bound-held parameter has exactly zero (co)variance,
    as a frozen one does.
  - `face_held_inverse`: `Z (Z^T W Z)^-1 Z^T` on a block, with `W = H - sum mu d2c` (the Hessian of the
    Lagrangian).
  - `held_directions_in_group` / `face_held_group_impact`: a group is conditioned on the complement of the
    held directions that lie inside it. This is exact, because `C_gg` and `v` both vanish on those directions.
  - `active_faces` is factored out of `face_held_covariance`, with the same arithmetic. That function now
    also returns the active rows' Jacobian and the constraint Hessian.
- `Fitter.postfit_faces` is set by `constrained_postfit`, or by `postfit_faces_at` for an
  `--externalPostfit` covariance. `impacts_parms` branches to the face-held path only when a face is
  active; otherwise the existing graph runs unchanged.
- Global impacts at a **curved** face: `C W C = C` gives `sum_sources = diag(C H C) = diag(C) + diag(C Hc C)`.
  The data-stat remainder therefore gets `diag(C Hc C)` back. That term is zero for a face that is linear in
  the fit parameters, and `None` (the same graph as before) with no active face.
- `rabbit_fit.py`: the skip is removed. `postfit_faces` is reset at the start of every fit, so toys do not
  inherit it.
- `traditional_impacts.impacts_parms` gets an optional `group_impact_fn` hook. The default path is untouched.

### Tests (`tests/test_face_held_impacts.py`)

Each check compares against a reference that does not use the face-held algebra, evaluated at the same
point. They test the algebra to round-off, not the minimizers.

- **(a) Bound face == the parameter frozen on the bound.** Covered for an unconstrained nuisance, a
  constrained nuisance and a ParamModel POU. All six impact arrays (traditional, global, Gaussian global;
  ungrouped and grouped) agree to rtol 1e-9, and the held parameter's covariance row is exactly 0.
- **(b) Linear two-parameter face `a + 2b >= lb` == the eliminated ParamModel (`a = lb - 2b`).** Agreement
  to 1e-8, and `a`'s impact is minus `b`'s.
- **(c) Curved (disk) face,** where the Lagrangian term moves the stat-block variance by more than 1 %:
  - grouped impacts == `sqrt(sigma^2 - sigma^2[group frozen, face held])` from rabbit's own freeze path;
  - global per-source responses == finite-difference constrained refits (2e-3; the released covariance is
    10x further off);
  - the corrected global stat^2 == `diag(C H_data C)`.
- **(d) No active face:** impacts unchanged.

`test_trust_constr.py`: the "skipped" test becomes "written". At an active face, `--doImpacts`,
`--globalImpacts` and `--gaussianGlobalImpacts` are all written and finite, and the held parameter's own
impact is exactly 0. `test_sharded_fit.py`: the new driver call `postfit_faces_at` is classified as safe.
It is parameter-level, and `--constraints` is refused with `--nDevices > 1`.

Separately, `rabbit_fit` was run on the test tensor with no constraints and with an inactive constraint
(`--doImpacts --globalImpacts --gaussianGlobalImpacts --saveHists --computeHistErrors`). The output of this
branch is bit-identical to `main`, apart from the wall-clock `epoch_time`.

Full suite: 476 passed. CI's isort, flake8 and black pass.

### Real check

The post-fit of a real-data, blinded fit was rerun with `--externalPostfit <x only> --noFit`. The fit has
3720 parameters, a SCETlib NP param model and a lattice term. It has one weakly binding linear face on the
NP parameters: releasing it lowers the NLL by 0.46.

- The recomputed face-held covariance equals the stored one exactly, with the same EDM and multiplier.
- Traditional impacts are now present and finite, grouped and ungrouped. The NP groups contain both
  parameters of the face, so their blocks were the singular ones.
- The total is unchanged, 0.570 in rabbit's POI units (1.14 in the plotting convention, ×2). The traditional
  data stat is 0.43 (0.86 ×2).
- Global and traditional impacts agree for the constrained-nuisance groups (global <= traditional, within a
  few percent).

### Open points (not in this PR)

- **The global grouped `stat` remainder can still come out negative (NaN after the sqrt).** This happens when
  the non-prior part of the Hessian (data plus regularizers plus profiled bbb) is indefinite, and it does not
  depend on faces. In the real check the face is linear, so `C H C = C` holds to 1e-12. Even so,
  `var_total - var_x0 - var_beta0 = -0.022` (rabbit units), the small difference of O(300) terms. This PR
  does not change that case. `--gaussianGlobalImpacts` gives a data stat that is never negative.
- `global_impacts_obs` (global impacts on observables) has the same remainder. At a curved face it would need
  the analogous `diag(J C Hc C J^T)` term, which is not done here.

### Related

Two companion PRs on trust-constr are opened in parallel: `tc-precond-pr` (spectral preconditioning with
constraints) and `tc-warmstart` (consistent warm starts). Each is independent and branches off `main`.
They are not stacked; this PR touches only the post-fit and impacts code.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
