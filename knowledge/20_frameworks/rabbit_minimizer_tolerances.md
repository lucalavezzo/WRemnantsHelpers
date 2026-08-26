# rabbit minimizer tolerances are all zero — and what that breaks

Source: study `studies/np-wall-local-minima/` (CT18Z 2D `ct18z_noprior_trustconstr`,
2026-08-13). Verified against scipy 1.18.0 in the WRemnants container.
Last updated: 2026-08-13.

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

## Why it usually doesn't bite

The unconstrained trust methods — including rabbit's default `trust-krylov` — run
through `scipy/optimize/_trustregion.py`, whose loop has an escape hatch
independent of `gtol`:

```python
if predicted_reduction <= 0:
    warnflag = 2
    break
```

Once you are at the minimum the model stops predicting improvement, so they exit
(with `success=False` and a "bad approximation" message, which is benign here).

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

## Cross-references

- `studies/np-wall-local-minima/LOGBOOK.md`, entry 2026-08-13 (the measurement).
- `profile_likelihood_pitfalls.md` — how to read σ(POI) once the fit has converged.
