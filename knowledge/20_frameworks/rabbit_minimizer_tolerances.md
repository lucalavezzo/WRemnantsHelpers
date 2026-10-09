# rabbit minimizer tolerances are all zero — and what that breaks

Source: study `studies/np-wall-local-minima/` (CT18Z 2D `ct18z_noprior_trustconstr`,
2026-08-13). Verified against scipy 1.18.0 in the WRemnants container.
Extended 2026-09-22 from `studies/alphas-scan-discontinuity/` (what the reported
`success`/`status`/`nit` are worth, and why EDM is not the gradient).
Extended 2026-10-09 from `studies/constrained-fit-strategy/` (the trust-krylov crawl at a
relu² penalty face, trust-constr's warm-start and barrier problems, and full-scope spectral
preconditioning of ill-conditioned sub-fits).
Last updated: 2026-10-09.

## The fact

`Fitter.fit()` calls the minimizer with a hard-coded `tol=0.0`
(`rabbit/fitter.py`, the `scipy.optimize.minimize(...)` call), and builds
`sci_opts` from only `--minimizerMaxiter` / `--minimizerGtol` / `--minimizerFtol`.
scipy's `minimize` then fills every unset tolerance from `tol` via `setdefault`:

```python
if meth in ('bfgs','cg','l-bfgs-b','tnc','dogleg','trust-ncg','trust-exact','trust-krylov'):
    options.setdefault('gtol', tol)
if meth == 'trust-constr':
    options.setdefault('xtol', tol); options.setdefault('gtol', tol)
    options.setdefault('barrier_tol', tol)
```

So unless you pass a tolerance flag explicitly, **every convergence tolerance is
0.0**. All the quantities they are compared against (gradient norm, trust radius,
barrier parameter, constraint violation) are non-negative, so `< 0` is never true
and **no convergence test can fire**.

Two places in rabbit state the opposite and are wrong: the comment above the
`sci_opts` block ("run to the tightest internal criteria") and `--minimizerGtol`'s
help ("None (default) uses scipy's per-method default").

## Why it usually doesn't bite — **and why it DID, twice, on 2026-09-07**

The unconstrained trust methods — including rabbit's default `trust-krylov` — run
through `scipy/optimize/_trustregion.py`, whose loop has an escape hatch
independent of `gtol`:

```python
if predicted_reduction <= 0:
    warnflag = 2
    break
```

The claim used to be that this makes `trust-krylov` safe: once at the minimum the
model stops predicting improvement, so it exits. **That is wrong for a
SCETlib-backed reco fit, and the correction cost us two long runs.**

**Measured 2026-09-07, both on the 3673-nuisance reco card.** The minimum is
reached at **iteration 73**, after which the loss repeats to all 16 digits — and
the loop does *not* break. `tol=0.0` makes `gtol=0.0`, so the only remaining
ceiling is scipy's fallback `maxiter = len(x) * 200`, which at `len(x) = 3720` is
**744 000 iterations ≈ 14 days**. Two independent sightings:

* `toyA_tmpl` (210-bin card): converged at iteration 35 in 5 minutes, then ran
  **63 554 further iterations over 21.8 h** at a bit-identical loss before being
  killed. Nothing was recoverable — rabbit installs no signal handlers and writes
  its fitresult only at the end.
* `TOYF210_B`, run twice deliberately to check: minimum at iteration 73 both
  times; attempt 2 was at iteration 1439 / 4199 s when stopped.

So `predicted_reduction <= 0` is evidently not reached when the objective is flat
to round-off rather than genuinely curving — plausibly because a nonzero
predicted reduction survives in floating point even when the *actual* reduction is
zero. **Do not rely on that hatch.**

**What to do instead.** Pass `--earlyStopping 30` (or a real `--minimizerGtol`
matched to the model's accuracy — ~1e-4 for a SCETlib-backed prediction, NOT the
1e-6 that caused the 21.8 h run). Note `--earlyStopping < 20` silently aborts
`trust-constr`, so 30 is the safe floor. The quoted reco toy fit time of 594 s is
a time-to-early-stop, not a time-to-convergence; convergence itself is at
iteration 73.

## Corollary: `success` / `status` / `nit` carry NO convergence information

Added 2026-09-22 from `studies/alphas-scan-discontinuity/`.

Because `tol = 0.0` makes `gtol = 0.0`, **no convergence test can fire**, so
`trust-krylov` can only ever exit through the `predicted_reduction <= 0` hatch —
which scipy reports as `success: False, status: 2` ("A bad approximation caused
failure to predict improvement"). Measured: that pair appears on **70 of 70**
scan points across five scans of the 3720-parameter card A
(`260921-scan-convergence-audit/LOGBOOK.md` finding 1, `scan_convergence.csv`).
rabbit's own `minimizer_status` docstring says as much.

**So a dead-flat loss tail ending in `status: 2` is the documented signature of a
CONVERGED fit here, not of a stalled one.** Reading it the other way round is the
default mistake: an audit built on the log alone flagged 6 of 7 points of one arm
as stalled, and a real per-point EDM later showed **5 of those 6 were converged**
(EDM 1.9e-12 .. 1.8e-8). The one genuine stall (EDM 3.65e-3) cost 7.3e-3 in
2 dNLL. The log-only proxy over-condemns and does not under-certify: 5 of 6
condemnations false, 0 of 8 certifications false
(`260921-scanshift-detail/LOGBOOK.md` findings 1, 4, 5).

`nit` is also wrong whenever rabbit **restarts** the minimiser — it counts only the
final restart. Measured: 19 reported against 69 logged; 21 against 166. Count
iterations from the log, not from `nit`
(`260921-scan-convergence-audit/LOGBOOK.md` finding 7).

## EDM is not the gradient — and the gradient cannot rank convergence

`EDM = 0.5 g^T H^-1 g`. The `H^-1` is the whole point: a large gradient along a
**stiff** direction costs almost nothing in NLL, and a small one along a soft
direction can cost a lot. On this likelihood the curvature spans about **eight
decades** (stiffest eigenvalue ~ the total event count, 1.6e8), so gradient size
and distance-to-minimum are effectively unrelated.

Measured, two points of the same scan: sup-norm gradients within 6 % of each other
(1.37e-1 vs the stalled point's), **EDMs six orders of magnitude apart**. Only
`0.5 g^T H^-1 g` discriminates. Any convergence rule built on a gradient norm — or
worse, on the 4 of ~3720 gradient entries scipy prints — will misrank.
(`260921-scanshift-detail/LOGBOOK.md` finding 3.)

The practical consequence for scans, where no EDM is stored by default, is
`--scanSaveDetail`: see `likelihood_scans.md`.

**Where `edmval` lives.** It is not in `meta_info`, which holds only `time`, `command`,
`git_hash` and `git_diff`. It is a field of the fitresult's `results`:
`ws.results["edmval"]` (`rabbit_fit.py:876-881`). Read it with
`io_tools.get_fitresult(path, None)["edmval"]`.

**EDM also tells you how far apart two fits can be told apart.** Two converged fits of the
same problem differ in NLL by about the worse one's `edmval`. Measured: a control refit
from a randomly displaced seed landed -8.38e-7 away in NLL against a reported `edmval` of
8.385e-7, and 8.91e-4 away in theta. That is the floor below which "same solution" cannot
be distinguished from "different solution".
(`studies/alphas-scan-discontinuity/260921-two-solutions/` findings 2-3.)

## Is it a minimum? What a fitresult already certifies

- **A fit that wrote a full dense postfit `cov` through the Hessian path has already
  Cholesky-certified its Hessian as positive-definite.** `scipyhelpers.scipy_edmval_cov`
  runs a bare `scipy.linalg.cholesky` with no ridge, and raises "Hessian is not
  positive-definite" otherwise. With frozen parameters only the floating block is
  certified. Under `--noHessian` nothing is factorised, because cov rows come from CG.
- **The eigenvalues of the stored `cov` prove nothing on their own.** `cho_inv` builds it
  as `Cinv @ Cinv.T`, which is positive semi-definite by construction.
- **`1/lambda_max(cov)` gives lambda_min(H) essentially for free.** It matched a rigorous
  computation to 6 digits (see `likelihood_scans.md`).
- **To search for negative curvature without densifying H** (kappa ~ 1e9 here): plain
  `eigsh(which="SA")` on H is a trap, because the smallest eigenvalues sit in a relative
  gap of 1e-9.
  - Instead run Lanczos on the congruence `A = U H U^T`, with `cov = U^T U`. By Sylvester
    it has the same inertia as H, and `A ~ 1`, so it converged in ~31 HVPs / 200 s.
  - It is a *search*: Ritz values only bound lambda_min from above, so it cannot prove
    there is no negative curvature.
  - Always run a **negative control**, i.e. show the same code returns a negative value at
    a point known to have one. Confirm with a derivative-free second difference of the
    loss along the eigenvector.
  - Evidence: `studies/alphas-scan-discontinuity/260921-saddle-or-basin/` findings 6-9,
    `scripts/inertia.py`.

## Regularised fits: the penalty is baked in at trace time

rabbit's loss is a traced `tf.function`, and `len(self.regularizers)` is read **at trace
time**. Setting `fitter.regularizers = []` after the first call therefore does NOT remove
the penalty. A "walled minus unwalled at the same x" A/B done that way silently returns 0.
Compute the penalty eagerly instead: `reg.compute_nll_penalty(x, None) * exp(2*tau)`.
(`studies/alphas-scan-discontinuity/260922-curvature-followups/` finding 3.)

## Where it does bite: trust-constr

`trust-constr` has no such hatch. Its interior-point loop tests only

```python
if state.optimality < gtol and state.constr_violation < gtol:      status = 1
elif state.tr_radius < xtol and state.barrier_parameter < barrier_tol: status = 2
elif state.nit >= maxiter:                                          status = 0
```

so with zero tolerances the **only** exit is `maxiter`. Observed signature: the
logged loss goes bit-identical while iterations keep ticking, and the per-iteration
time drops to a small constant (the objective is no longer re-evaluated — you pay
only the constraint Jacobian and the trust-region subproblem). In the reference
case it converged at iteration ~115 of 1000 and then burned 5.7 h doing nothing.

**Fix:** pass `--minimizerGtol 1e-8`. Explicit options beat `tol` because scipy uses
`setdefault`. Note `xtol`/`barrier_tol` have no rabbit flag, so only the status-1
exit becomes reachable — which is the one you want anyway.

### Even with tolerances set, trust-constr is a certifier, not a default (2026-10-06)

Measured on the walled SCETlib-AD nominal fit (3719 parameters, five wall conditions as hard
constraints, rabbit branch `trust-constr-nominal`;
`studies/constrained-fit-strategy/261006-diagnosis/`, Diagnosis 3):

- **It throws away a warm start.** scipy hard-codes the slack initialisation
  `s0 = max(1.5*slack, 1)` in `tr_interior_point`, ignoring where you start. TCA, started
  *at* the minimum, was at **+333 NLL by iteration 3** and took 7.2 h to come back. Every
  warm/polish use pays an O(100 NLL) detour. Fixing it means copying scipy's interior-point
  driver.
- **The first barrier stage (mu0 = 0.1) is biased and may never end.** Its own solution sits
  ~mu/lambda inside the active face, with barrier forces of 0.4–3 on the inactive faces; it ends
  only on a sup-norm optimality < 0.1. TCB1 (cold start) spent all **600 iterations / 13.6 h**
  in that stage and stopped at -0.33 sigma(alpha_s), +0.38 NLL — mostly the stage's own answer.
- **Its projected CG is unpreconditioned with a loose forcing term** (3–10x residual
  reduction), so in the tail it runs 1–3 HVPs per step. rabbit refuses `--precondition` with
  trust-constr.
- Per-call costs from scipy's own counters (two equations, nfev and cg_niter): **~27 s per
  loss+grad, ~13 s per HVP** on the shared node — each iteration costs as much as a
  trust-krylov iteration or more.

Decision (Luca, 2026-10-06): trust-krylov stays the production minimiser; trust-constr only
as a warm certifier.

## `--earlyStopping` is NOT a safe substitute with trust-constr

The rule in `FitterCallback` is "stop if the loss N iterations ago was no worse than
now" (`loss[k-N] <= loss[k]` for `k > N`). trust-constr's early iterations are
**non-monotone** — the objective rises and falls while the barrier parameter and
trust radius adjust — so a small `N` fires almost immediately. Replayed over the
reference fit's own loss history:

| `--earlyStopping N` | fires at iteration | loss vs converged |
|---|---|---|
| 3 / 5 / 8 / 10 / 15 | 4 / 6 / 9 / 11 / 16 | **+0.15 … +0.19** |
| 20 / 25 / 30 | 135 / 140 / 145 | 0.0 |

And the abort is **silent**: it raises `ValueError`, which `fit()`'s `except
Exception` catches, restores `callback.xval`, and continues — so a badly
unconverged postfit is written and looks like a normal finish. **Use N ≥ 20 with
trust-constr**, or prefer a gtol plus a `--minimizerMaxiter` cap. Replay the rule
against an existing log before trusting a new N.

### …and it is not a reliable backstop either (measured 2026-08-13)

The rule tests `loss[k-N] <= loss[k]` — **no improvement at all**, not "improvement below a
tolerance". Near its minimum trust-constr does not stall cleanly, it dribbles: on the CT18Z 2D
run the loss sat exactly frozen for 4-7 iterations, then dropped ~1e-12, repeatedly (9 of 40
consecutive iterations improved, total gain 2.8e-9). Each 1e-12 step **resets the window**. It
did eventually fire (iteration 121, after 25 genuinely identical iterations), but only because
the loss finally went fully bit-frozen. Pair it with `--minimizerMaxiter` sized from a
known-good log rather than relying on it alone. A relative-improvement test
(`(loss[k-N]-loss[k])/|loss| < 1e-9`) would be robust; the exact `<=` is not.

## trust-constr + constraints SILENTLY BREAKS `--freezeParameters`

rabbit freezes with `tf.stop_gradient` (`frozen_params_mask` applied in `get_theta` /
`get_model_nui` / `get_poi`), which zeroes only the **objective** gradient — the parameter
stays in the vector handed to scipy. The hard-constraint Jacobian used by `trust-constr`
(`_constraint_val_jac`) is taken over the **full** vector with **no frozen mask**, so a frozen
parameter that appears in a regularizer's `constraint_spec` has zero objective cost and a
nonzero constraint gradient — and the minimizer moves it freely.

Measured 2026-08-13 (identical card and freeze list): BFGS + penalty held `lambda_inf` = 1 and
`lambda_inf_nu` = 1.6853 exactly; trust-constr + hard constraints drifted them to **12.5793**
and **4.0122**. The fit then reaches a lower NLL because it silently gained two degrees of
freedom.

**Until fixed: never combine `--minimizerMethod trust-constr` with `-r <regularizer>` and
`--freezeParameters`.** Every other method is on the penalty path, where freezing is sound.

## Does restarting from a fit's own postfit help? trust-krylov: no. trust-constr: yes.

Added 2026-09-29 (collected from two studies).

- **trust-krylov (reco default):** four data arms restarted from their own postfits
  (`studies/scetlib-ad-param-model/260910-basins/`, table under "experiment 1") moved at most
  7e-4 sigma, alpha_s at most 3.4e-4 sigma, and the loss by at most 2e-8. The EDM was unchanged in
  3 of 4 arms, **including the plain arm at 1.386e-3 -> 1.386e-3**, and halved in the ridge arm. The
  walled arm came back bit-identical. A new start rebuilds the Hessian and takes the same step,
  so it stops again where it stopped before. An EDM of ~1e-3 at a trust-krylov stop is a property
  of the point, not a collapsed trust radius. A self-seed also stops at once when the point is
  already a clean minimum (Y35ZWALLL4ZR, 2026-09-29: iteration 0, EDM 6.7e-17).
- **trust-constr:** the crawl measures the collapsing trust radius, not the distance to the
  minimum. Restarted from its own postfit, a saturated leg dropped **5.15 NLL units in one
  iteration** and 11 in three (`studies/trustconstr-np-fit/`, 2026-08-18 retraction).
- **Untested:** a trust-krylov stop with a much larger EDM. MSLATWALLWARM
  (`studies/msht20-ad-campaign/260929-fits-msht20/`) restarts one with EDM 0.067; record the outcome here.

## trust-krylov crawls at a relu² penalty face: a limit cycle of scipy's radius rule

Added 2026-10-09 from `studies/constrained-fit-strategy/` (tasks `261006-diagnosis`,
`261008-c2-wall-test`). Real walled SCETlib-AD fits (card A, nominal configuration,
`NPDampingWall` at tau = 8, margin 0), plus a quadratic surrogate: the real data-only Hessian
(3719²), the exact wall conditions, and an instrumented line-for-line copy of scipy 1.18's
`_trustregion.py` with the same trlib subproblem.

**What it looks like.** A walled fit sits for hours on a slowly falling plateau. Every step is
accepted and the loss falls by a near-constant amount per iteration, so it looks like a
sloppy convergence or a false minimum. It is neither. Seen: CMR1A, 1.5 h at 7.5e-6 per
iteration before escaping; CENS03, not converged after 390 iterations; its restart CENS03R,
260 iterations / 4.5 h at +430 NLL above the true minimum.

**Mechanism.** scipy's trust-region rule (and rabbit's own `rabbit/minimizer/base.py`, which
copies it verbatim): rho < 0.25 -> radius x1/4; rho > 0.75 **and** the step hits the
boundary -> x2; otherwise unchanged. A relu² penalty k·max(x,0)² is only C¹: its curvature
jumps from 0 to 2k at the face.

- A model built on the slack side has no wall curvature. Its boundary step crosses the face,
  the penalty eats ~30 % of the predicted gain, rho ~ 0.71: no growth.
- A model built on the violating side contains 2k·a aᵀ. Its step lands just back inside,
  *interior* (no boundary hit), rho ~ 1: no growth.

The radius freezes (3.8e-6 in theta on the surrogate at tau = 8, scaling as ~1/k) and the
iterate zig-zags across the face for ever. It is **not** the condition number: with the
active face eliminated exactly, the same kappa ~ 1e5 data Hessian converges in 9–45 iterations
from every start. It worsens steeply with stiffness (surrogate, 5 starts): tau <= 6 converges
in 15–45 iterations everywhere, tau = 7 in <= 174, tau = 8 locks in for 1 of 5, tau = 9 for
2 of 5, and at tau = 10 three of five do not converge in 20 000.

**How to recognise it from a log.** rabbit logs only the loss (the scipy callback gets
`(x, fun)`, no radius, rho or hits-boundary). Take the ratio of consecutive accepted gains:

- **the period-2 lock:** a large fraction of ratios ~ 1. 40–44 % in the crawls CENS03 and
  CMR1A against 1–9 % in eight census fits that converged normally; 78 % for relu² from the
  CENS03R snapshot (R2A) against 7.5 % for the C² wall from the same point (C2A), whose steps
  double instead (ratio ~ 2) as the radius grows;
- **a period-~7 sawtooth:** 4–5 accepted steps each gaining 2x the last, then 2–3 rejections
  when the doubled step crosses the face. The same point can show either form.

Scripts: `261006-diagnosis/scripts/analyze_logs.py`, `261008-c2-wall-test/scripts/analyze.py`.

**What does NOT fix it** (surrogate unless stated):

- **Restart-on-stall** (`--stallRelTol r --maxRestarts`). For r <= 1e-7 the stall test never
  fires: the crawl gains ~4e-7–6e-7 relative per window, which counts as progress. Where it
  does fire (r >~ 6e-7), the restart's fresh radius of 1 is cut back by the same
  face-crossing rejections into the same cycle: 361–662 restarts and no convergence on the
  lock-in start. The real CENS03R restart fell back in the same way.
- **`--precondition`.** The reference Hessian is taken at the start; at a feasible start relu²
  contributes no curvature, so the kink survives the change of variables. Whitening helped 2 of
  5 starts and hurt 3 (cold_000 95 -> 1181 evaluations, CENS03R 265 -> 1177).
- **rabbit's native `tf-trust-krylov` / `tf-trust-ncg` / `tf-trust-exact`**: same outer
  radius rule (read from the code, not run). A Steihaug-CG subproblem (`tf-trust-ncg`'s
  algorithm) is much worse: 1083–2079 evaluations against 32–238.

**What fixes it.**

- **A C² penalty.** Ramp the relu² curvature linearly over a width d: P = x³/(3d) on [0, d],
  x² − dx + d²/3 beyond. A face crossing by dx << d then costs k·dx³/(3d) instead of k·dx², so
  the boundary step keeps rho > 0.75 and the radius grows. Surrogate: lock-in gone from all 6
  starts (18–159 evaluations). Real fit: from the CENS03R snapshot C2A reached the reference
  minimum (NOMSTIFF, to 1e-6) in **46 iterations / 1.11 h**, while relu² run side by side
  (R2A) was still at +430 after 219 iterations / 1.69 h; the minimum is the same
  (Delta alpha_s = +3.9e-6 sigma). **This is the `NPDampingWall` default since WRemnants
  692f9483 (2026-10-08)**; widths, opt-out and overshoot in
  `../30_physics_global/np_parametrization_constraints.md` §21. Caveat: one real start (a
  mid-crawl snapshot); cold and perturbed starts were covered only on the surrogate.
- **tau-continuation** (tau = 5, then tau = 8 warm via `--externalPostfit`): all 6 surrogate
  starts in 35–72 evaluations, but two processes = two cache loads, and never run on a real
  fit. Opt-in: `workflows/fitterAD.sh --wall --tau-continuation` (WRemnantsHelpers 3c0a9fb).
- Not a fix: relu³ at the same literal tau is C² but ~850x softer (overshoot 7.8e-4 GeV² on
  L2(|Y|=2.5) instead of 9.2e-7) — a different wall.

**General rule.** Any C¹ penalty (relu², squared hinge) added to a rabbit objective can do
this under trust-krylov, and the stiffer it is the worse. Write new penalty regularizers C².

## Ill-conditioned sub-fits: full-scope spectral preconditioning

Added 2026-10-09 from `studies/constrained-fit-strategy/261008-saturated-subfit-diagnosis/`
(rabbit 2a59246; real data, LATB8 configuration).

**The case.** The projected-ptll saturated sub-fit (`-m Project ch0 ptll
--computeSaturatedProjectionTests`, 39 free bin scales on top of ~3720 parameters) took
153–158 iterations, ~2150 HVPs and 5–6 h (SATB8). 89–91 % of the time is HVPs, much of it
in a few late Krylov solves of up to ~270 HVPs that each gain only 35–40 % of what is left;
the tail below Delta q = 0.01 is 27–56 % of the run. The C² wall changes nothing here (2141
HVPs): the cost is not the wall.

**Why.** kappa = 1.3e10 at the sub-fit start, 2.0e9 at the end. Top of the spectrum: the
active wall face (1.78e8) and the 39 bin scales (3.5e5–9.4e5, = 4N_j in rabbit's sqrt(s)
parametrisation). Bottom: alpha_s-dominated directions, 97.9 % degenerate with the scales.
The sub-fit minimum lies 9.6 main-fit sigma away in alpha_s along a long, *curved* valley; the
soft curvature changes by 1e3–1e4 along it, and an exact Newton step diverges even 0.4 NLL
from the minimum (so a trust region is required).

**The fix:**

```
--precondition --preconditionParams '.*' --preconditionBlocks none --preconditionTransform spectral
```

SATP (SATB8 plus only this): **614 HVPs vs 2150, 71 loss+grad vs 156, 69 iterations vs 158**,
same minimum (Delta loss -1.7e-10, max |Delta x| 4e-8, q = 78.40/39 unchanged), about **3x
faster at equal node load** including the 306 s reference Hessian. Offline on the end
Hessian: kappa 2e9 -> 1.2e7, CG to 1e-6 needs 77 HVPs instead of 290.

- **The scope must be full.** Offline, partial preconditioning is *worse* than none: Jacobi
  (kappa 5.5e7, but 217–682 HVPs per solve); whitening only the scale block, or only rabbit's
  default scope (the unconstrained parameters), gives kappa ~ 1e12. Hence `'.*'` plus
  `--preconditionBlocks none`. Quote `'.*'`: unquoted, the shell globs it
  (`workflows/fitterAD.sh` runs with `set -f` for this reason).
- **What remains is a stale-curvature tail.** The transform is built once at the start; as the
  alpha_s curvature drifts along the valley, convergence turns linear again (SATP after q-to-go
  ~ 4: deep solves of up to 93 HVPs, against 267 without). A mid-fit rebuild would attack it;
  rabbit has none.
- **Do NOT loosen `--minimizerGtol` under it.** Under `--precondition` scipy's gtol tests
  |g_y| in the whitened frame, where the soft alpha_s curvature drifts to ~1e-3. A model of the
  stop error (`gtol_model.py`, using the dense end Hessian in the start-built frame) puts a
  gtol = 0.03 stop anywhere between Delta q ~ 1e-7 and 0.86; a guaranteed Delta q <= 0.01 needs
  gtol <~ 3e-3. Modelled, not observed: rabbit does not log |g_y|. A safe early stop needs an
  EDM-type test.
- **Nor a stall window.** Replaying `--earlyStopping N --stallRelTol r` on these logs: every
  setting that saves real time fires on a false plateau (q errors 0.36–20); settings late enough
  to be right save at most 27 %.

**The cost is fitter-wide: one dense Hessian per `fit()` call.** The flag applies to every fit
in the process: the main fit builds a transform at its start, and each saturated sub-fit (a
deep copy of the fitter) builds its own at its own start. A `--noFit` main step builds nothing.
Each build is one Hessian: 306 s (SATP), 650–870 s on a loaded node, so budget **5–15 min per
fit**. `workflows/fitterAD.sh` passes the flag for every fit since WRemnantsHelpers 1c5d93a
(2026-10-09), so main fits now pay it too.

**Untested** (state as of 2026-10-09): the effect on the walled *main* fit (the only
evidence is the relu² surrogate above, where start-built whitening helped 2 of 5 starts and
hurt 3; not measured with the C² wall on a real fit); the gain on toys, whose valley is
shorter (q ~ 39). Compare nfev/nhev before and after if a main fit looks slower.

**Measuring per-call cost.** From a log: t_f = median dt after a *rejected* step (trlib
hot-starts, so no new HVPs), then t_HVP = (sum dt − nfev·t_f)/nhev. Measured on the shared
node: t_f ~ 10–17 s and t_HVP ~ 6–10 s for the sub-fits (load-dependent; compare counts, not
hours). Do not time by repeating calls at the same point inside a job: the SCETlib-AD model
memoises repeated points, and HDIAG's 3.5 ms / 8.6 ms "timings" were cache hits.

## Stopping a running fit

There are **no signal handlers anywhere in rabbit**. `fit()` rescues the last
iterate (`xval = callback.xval`) only from an *exception raised inside*
`scipy.optimize.minimize`. Consequences:

- SIGTERM / SIGKILL on a long fit loses everything, including at the very end.
- SIGINT does not help either: `KeyboardInterrupt` derives from `BaseException`,
  which `except Exception` does not catch.
- The clean in-band stop is to raise **`StopIteration`** from the callback —
  trust-constr catches it explicitly and exits with `status = 3`, and the other
  methods honor it too, so `res` survives. rabbit currently raises `ValueError`
  instead, which works but throws `res` away (`minimizer_result = None`).

## Diagnostic gap worth closing

`FitterCallback` keeps only `intermediate_result.fun`, and `minimizer_status()`
records only `success/status/nit/nfev/message`. For trust-constr the result also
carries `optimality`, `constr_violation`, `tr_radius`, `barrier_parameter`,
`cg_niter` — none of which reach the output. Without them **nothing downstream can
distinguish "converged" from "pinned against a constraint boundary"**, which is
precisely the question a walled/constrained NP fit is asking.

The same gap hid the trust-krylov crawl (above): scipy's callback gets only `(x, fun)`, so
the trust radius, rho and the hits-boundary flag never reach the log, and the mechanism had
to be reconstructed on a surrogate. Logging the accepted step norm |x_k − x_{k−1}| per
iteration would expose a frozen radius directly. Under `--precondition`, |g_y| (what a gtol
would test) is not logged either.

## Cross-references

- `studies/np-wall-local-minima/LOGBOOK.md`, entry 2026-08-13 (the measurement).
- `studies/alphas-scan-discontinuity/LOGBOOK.md` Q5, and its tasks
  `260921-scan-convergence-audit/` and `260921-scanshift-detail/` (the 2026-09-22
  additions).
- `likelihood_scans.md` — what a `--scan` point stores, and `--scanSaveDetail`.
- `studies/constrained-fit-strategy/` (SUMMARY.pdf; tasks `261006-diagnosis/`,
  `261008-c2-wall-test/`, `261008-saturated-subfit-diagnosis/`) — the crawl, the C² wall,
  trust-constr's costs, and the saturated sub-fit preconditioning (the 2026-10-09 additions).
  Bulk outputs: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/{261006_constrained_fit_diagnosis,261008_c2_wall_test,261008_saturated_subfit_diag}/`.
- `saturated_test_toys.md` — the toy recipe, which carries the preconditioning flags.
- `profile_likelihood_pitfalls.md` — how to read σ(POI) once the fit has converged.
