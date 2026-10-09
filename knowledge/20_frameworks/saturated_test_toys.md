# Toy-calibrating a saturated goodness-of-fit test in rabbit (with a ParamModel and a wall)

Use this when a Wilks p-value from `--computeSaturatedProjectionTests` is in doubt. That
happens when a one-sided regulariser (the NP damping wall) is active, parameters sit
against it, or the fit is strongly non-linear. The recipe and the result both come from
`studies/alphas-scan-discontinuity/260925-wall-sat-toys/` (2026-09-25 .. 27; card A, old
260827 AD cache, `NPDampingWall` at tau = 5).

## Result: at the walled minimum, Wilks holds

There were 112 toys, generated at the full walled postfit vector of `CCWALLWARMPF`, with the
wall on in every refit.

| statistic | toys: mean / sd | chi2(ndof): mean / sd | KS p | data | toy p | Wilks p |
|---|---|---|---|---|---|---|
| full 2D saturated | 784.8 / 39.2 | 779 / 39.5 | 0.13 | 742.89 | 0.875 +- 0.031 | 0.82 |
| projected ptll | 37.7 / 8.5 | 39 / 8.8 | 0.12 | 70.39 | 0/112 above: **< 2.6 % (95 % CL)**; scaled-chi2 tail 0.08 % | 0.15 % |

**Read.** Both statistics follow chi2 with the ndof rabbit prints, even with a one-sided
penalty active and the NP lambdas near the wall. So the printed Wilks p-values of walled
fits can be used at this level. **The walled fit's projected-ptll tension is real, not a
Wilks artefact.** That last statement is about this model and this card. Re-check it if the
model changes.

## Recipe

One rabbit process per random seed, `-t N` toys in sequence after a single cache load
(runner: `260925-wall-sat-toys/scripts/run_toys.sh`):

```
rabbit_fit.py <card> -t N --seed S --toysDataMode expected \
    --toysSystRandomize frequentist --toysDataRandomize poisson \
    -m Project ch0 ptll --computeSaturatedProjectionTests --saveHists --noChi2 --noHessian \
    <same -r / --regularizationStrength as the data fit> \
    --paramModel ... "xparam_default=<postfit ParamModel vector>" \
    --setConstraintMinimum <name> <value>   # once per card nuisance, all of them
```

- **Generation point = the full postfit vector, set through two handles.**
  - The model token `xparam_default=` covers the ParamModel parameters
    (`scripts/make_xparam.py`).
  - `--setConstraintMinimum` covers every card nuisance (`scripts/make_constraint_min.py`,
    3673 entries). It sets `theta0default` (`fitter.py:280`).
  - Each handle moves three things together: the fit start, the Asimov/toy generation
    point, and the frequentist throw centre. That makes this the textbook parametric
    bootstrap.
  - `make_constraint_min.py` refuses a card that has NOIs among the card nuisances, since
    those would be blinded values.
- **`--externalPostfit` cannot set the generation point.** `toyassign` builds the
  pseudo-data *before* the external postfit is read. It would also pull the blinded POI in.
  Each toy fit starts at the generation point anyway.
- **Blinding.** A stored POI value is in the blinded frame, so the POI is generated at the
  **cache anchor**. The toys are unblinded pseudo-data: never compare toy POI values with
  data fits. The POI is free and interior, so the statistic should not care where it sits.
  That is a stated assumption, not a measured one.
- **Frequentist mode re-throws the ParamModel priors too.** `Fitter.frequentistassign`
  (`fitter.py:881`) throws `x0 = x0default + sqrt(1/cw) N(0,1)` over the FULL vector
  [ParamModel params | card systs], wherever `cw > 0`. The saturated sub-fit keeps the
  thrown centres (`rabbit_fit.py:469`). Only unconstrained parameters (the POI) are not
  thrown.
- **Not reproducible:** the data fit's profiled Barlow-Beeston betas. Toys throw BB-stat
  around 1.
- **Closure first.** Use `-t -1` (Asimov at the generation point, not fitted). You should
  get `t_glob ~ 0.01`, and the projected sub-fit should open at loss ~1e-4.

## Cost traps

- **Do not include `-t -1` in production runs.** From an already-minimal point the
  projected sub-fit never terminates cleanly. trust-krylov crawls at 1e-5 loss, and the
  per-iteration time grows from 8 s to 171 s. In the task this burned 20 min before any toy
  had started.
- **Measured per toy** on the old cache, 128 threads: main fit 600-1355 s, plus a projected
  sub-fit of ~3250 s. The data's own projected sub-fit took 2.5 h, because the lambdas relax
  off the wall. Each process holds ~57 GB.
- **A process writes its fitresults only at exit.** Killing it loses every toy still in
  progress. To make room, pause instead: `kill -STOP` / `kill -CONT` (see
  `../10_environment/big_memory_jobs.md`). Harvest from the logs as you go
  (`scripts/harvest_logs.py`, values rounded to 0.01).

## Cross-references

- `saturated_gof_tests.md` — the theory behind both statistics, why their ndf are what they are,
  and the CCWALLWARMPF degeneracy check (alpha_s 97.8 % degenerate with the ptll scales, d = 0).
- `profile_likelihood_pitfalls.md` — reading sigma(POI) and saturated p-values across prior
  changes.
- `rabbit_minimizer_tolerances.md` — why `success`/`status` say nothing about a toy fit's
  convergence.
- `../30_physics_global/np_parametrization_constraints.md` — the wall itself.
