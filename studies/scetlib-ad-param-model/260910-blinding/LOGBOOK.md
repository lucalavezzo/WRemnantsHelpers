---
title: Blinding — give alphaS the form the template had
slug: 260910-blinding
study: scetlib-ad-param-model
status: active
created: 2026-09-10
updated: 2026-09-10
owner: orchestrator
---

# Blinding — give alphaS the form the template had

**Task:** can the fit hand SCETlib the true alpha_s while the value we read
stays blinded — and with the *uncertainty* readable, as it was under the
template treatment?

---

## START HERE (status as of 2026-09-10)

> **Implemented; verification running.** The requirement turned out to be
> narrower than it first looked: rabbit *already* hands the model the physical
> value, and this morning's normalisation (`8f6af64f`) already fixed the
> catastrophic start. The one real defect left was that alphaS is a **POI**,
> and rabbit blinds POIs *multiplicatively*, which divides the reported
> **sigma** by a random factor.

- **Next action:** read out `logs/LATEST`, then commit.
- **Blocking on:** nothing.

---

## Why — and a correction to the initial diagnosis

I began from the wrong model of how rabbit blinds, and it is worth recording
because the wrong version is the intuitive one.

**Wrong:** "rabbit blinds the value before `compute()`, so the offset reaches
SCETlib and corrupts the physics; the fix is to blind at the report instead and
audit every exit path."

**Right:** blinding is a **change of variables inside the likelihood**.
`get_poi()` returns `x * B` and *that* is what reaches `compute()`
(`fitter.py:1688-1691`) and the constraint (`:2028`). So `self.x` — the
minimiser's coordinate, and what is written to `parms` — is the **blinded**
quantity, while the model gets the **physical** one. Outputs are blinded *by
construction* because they write raw `x`. The design already did what we wanted.

**What actually broke** was the *start point*. `self.x` is initialised to
`x0default`, whose POI block is the model's `xparamdefault`
(`fitter.py:363-370`, `:782-785`), so iteration 0 hands the model
`xparamdefault * B`. With the old physical parametrisation that was
`0.118 * B` — outside SCETlib's domain, loss 4.6e7 against a converged 361.
`8f6af64f` set `xparamdefault[alphaS] = 0`, and `0 * B = 0`, so the start became
correct **as a side effect**.

### The one defect left

alphaS now has the same *shape* as the template nuisance it replaced (central 0,
`|theta| = 1` = `Delta(alpha_s) = 0.002`) but is registered as a **POI**,
because the SCETlib model owns it. rabbit blinds its blocks differently:

| block | central | blinding |
|---|---|---|
| POI (`npoi`) — default `Mu`, a signal strength | 1 | `* exp(N(0,5))` (`fitter.py:708-719`) |
| theta, NOI subset | 0 | `+ N(0,5)` (`fitter.py:680-691`) |
| POU (`npou`) | — | **never blinded** (`:693-706`) |

The template `pdfAlphaS` was a **NOI** — a datacard systematic flagged
`noi=True` — so it got the additive form. Our alphaS *cannot* be a NOI (NOIs are
card systematics; a model parameter is POI or POU), so it sits on the POI side
and inherits the blind designed for signal strengths.

Consequence, and the whole motivation: the reported coordinate is
`theta_true / B`, so curvature goes as `B^2` and **sigma comes out divided by
`B`** — along with the POI row of `cov` and every impact on alphaS. Only the
*relative* uncertainty survives. Under templates we could read sigma(alpha_s)
before unblinding, and it is the headline number in the AN.

Not about the central value being 0 rather than 1: writing `alphaS = anchor * r`
with `r` centred at 1 and blinding it gives `anchor * r * B` — the original
failure again. The distinction is **what the POI multiplies**. `Mu` scales
yields, which stay evaluable at any value; alphaS feeds a calculation with a
restricted domain.

---

## Log

### 2026-09-10 — the change

`blind_additive`, an opt-in boolean on `ParamModel` (default False, so every
other analysis is byte-for-byte unchanged), switching that model's POIs to
additive blinding with **no scale** — the offset is the same `N(0,5)` draw a NOI
gets, applied in the parameter's own fit units. For alphaS that is 5 in theta =
0.01 in alpha_s, roughly 20x sigma.

Two scale designs were rejected, recorded so they are not re-proposed:

- a per-parameter `{name: scale}` table (the parked `stash@{0}` design) invites
  a units error: `scale = 0.002` reads as "alpha_s units" but multiplies theta,
  giving an offset of 2e-5 in alpha_s — *below* sigma, under-blinding by ~500x
  while the fit still looks healthy.
- auto-deriving the scale from the prefit uncertainty fails outright:
  `prefit_variance` gives unconstrained parameters `unconstrained_err**2` and
  `prefit_unconstrained_nuisance_uncertainty` defaults to **0.0**
  (`fitter.py:169`), while alphaS has no prior — so the scale would be zero and
  blinding would silently not happen. Caught before implementing.

The start-point handling came with it, and was **not optional**: with
`get_poi() = x + A` and `x` starting at 0, the model would be handed
`anchor + 0.002 * A` at iteration 0 — an ~8% shift in alpha_s. We would have
traded an accidentally-correct start for a definitely-wrong one. So
`set_blinding_offsets` now holds the physical point fixed across a change of
frame (shift `x` by `off_old - off_new`, self-idempotent), and
`xdefaultassign` is frame-aware so the result does not depend on the driver's
ordering.

### 2026-09-10 — deviation from the approved plan

The plan called for refusing a `--blindingGroup` that mixes additive and
multiplicative members. **Not implemented, deliberately.** A group spanning a
POI and a NOI already does not share an offset today — the POI gets
`exp(value)`, the NOI gets `value` — so the "relative differences survive"
promise is already block-local. This change does not worsen it, and for an
additive model it actually makes a POI and a NOI in one group share the *same*
offset. Adding a refusal for a pre-existing quirk is logic the scope decision
excluded.

### 2026-09-10 — how rabbit's tests are actually run (I got this wrong twice)

Not a repo problem, contrary to what I first wrote: `pytest tests/` failing to
COLLECT `test_external_nll_constant.py` was my wrong harness. CI runs these as
**scripts** — `python tests/<file>` (`.github/workflows/main.yml:162`) — not
under pytest, and running as a script puts `tests/` on `sys.path[0]`, which is
what makes that file's absolute `from test_external_term import ...` resolve.

Then a second mistake in the other direction: three files use RELATIVE imports
(`from .test_sparse_fit import ...`) and need `python -m tests.X` instead. Those
are `test_preconditioner`, `test_restart` and `test_snapshot` — all from our own
preconditioner work, normally run under pytest. So TWO styles coexist, and the
verification wrapper dispatches per file by grepping for `^from \.`.

Also: CI's matrix is only 5 files, so `test_snapshot`, `test_restart`,
`test_preconditioner*` and `test_external_nll_constant` are not covered by CI at
all. The wrapper runs the full `tests/test_*.py` set: 12 files, all pass.

### 2026-09-10 — a 22-minute fit that silently tested the OLD code

Worth recording because it failed in the safest-looking way possible.

The blinding change was uncommitted in the shared `rabbit` submodule checkout.
A parallel session committed it (`0f64bbb` on `blinding-additive`, worktree
`/work/submit/lavezzo/alphaS/rabbit-blinding`) and switched the shared checkout
to `combined-156-157`, which does not contain it. The first "final test" data
fit therefore ran for 22 minutes against **multiplicative** blinding.

Nothing crashed, and that is the point: the model declares `blind_additive`, and
a rabbit without the change reads it as `getattr(pm, "blind_additive", False)`
and ignores it. **Default-False means no crash — and no fix.** The opt-in design
that protects other analyses is exactly what let this pass unnoticed.

The evidence was in the log from minute one and I did not read it —
`incontainer.sh` already echoes the rabbit commit, and it printed
`rabbit @ 2f2a6bc (combined-156-157)`.

Fixed structurally rather than by resolving to be more careful:
`incontainer.sh` now prepends the `blinding-additive` worktree to `PYTHONPATH`
and then **asserts** that the imported `rabbit.fitter` actually contains
`_blinding_offsets_poi_add` and the frame shift, exiting non-zero under `set -e`
before any fit starts. It also logs `inspect.getsourcefile(fitter)`, so which
rabbit ran is in the record rather than inferable from a branch name.

The shared checkout was deliberately NOT modified — a parallel session owns it
(single-babysitter rule), so pointing `PYTHONPATH` at the worktree is the
non-destructive route.

Second, smaller lesson: the first run used `-v 3` for log hygiene, on the
reasoning that the log lands in a world-readable study directory. But rabbit's
per-iteration output is DEBUG-only, so `-v 3` produces a silent ~20-minute gap
that looks like a hung job. `-v 4` prints scipy's `x`, which is the BLINDED
coordinate, so there was nothing to protect. Use `-v 4`.

---

## Findings

1. rabbit's blinding is a change of variables *inside* the likelihood, not an
   output-time offset — `self.x` is blinded, `get_x()` is physical. Every
   physics term reads the model frame; the written outputs read the internal
   one — (evidence: `fitter.py:680-725`, `:1688-1691`, `:2028`).
2. The 2026-09-09 alpha_s catastrophe was a **start-point** bug, not an offset
   reaching SCETlib: `x` is initialised to `xparamdefault` in the *blinded*
   frame, so iteration 0 evaluated `xparamdefault * B`.
3. **There is no secret.** The offset is `sha256(param_name [+ b"_data"])`-seeded
   with a hardcoded `std=5.0` (`fitter.py:591-610`) — recomputable by anyone with
   the source. Blinding here rests on good behaviour, not cryptography.
4. "Blind both multiplicatively and additively" cannot work: with
   `physical = x*B + A` the derivative is still `B`, so sigma stays scaled. Any
   multiplicative component defeats the requirement.
5. The model is the one place that can unblind us by accident, since
   `compute()` legitimately receives the truth. Audited: every print in
   `scetlib_ad/param_model.py` is construction-time and the compute path has
   none. Now stated as a rule in the module docstring.

---

## Wall vs no wall, on blinded data

Same card, cache, SCETlib snapshot (b66f8de) and rabbit (`0f64bbb`); production
config, NP sector free; both stop at scipy `status: 2`. The wall port and its own
numbers are [260910-wall-port](../260910-wall-port/LOGBOOK.md).

| | unwalled (`DATABLIND`) | walled (`DATAWALL5`) |
|---|---|---|
| **EDM** | 1.386e-03 | **9.632e-07** (1439x better) |
| iterations | 221 | 138 |
| saturated chi2 p-value | 2.33 % | **1.16 %** (penalty-removed; 1.07 % as printed) |
| linear chi2 p-value | 26.61 % | 26.61 % (prefit, identical by construction) |
| **sigma(alpha_s)** | 0.001321 | **0.001097** |
| **shift in alpha_s from the wall** | -- | **-1.68e-04 = -0.127 sigma** |
| pure NLL | -- | **Delta = +5.78 -> Delta(chi2) = +11.6** |
| NP conditions physical | 6 of 8 | **7 of 8** |
| `lambda2_nu` (physical) | **-0.0583** (anti-damps for all b_T < 1.04 GeV^-1) | **+0.0049** |

`Delta(chi2)` is quoted with the wall's own 0.649 penalty REMOVED from the
walled `fun`; comparing `nllvalreduced` directly gives 12.86 and double-counts
the penalty as if it were data.

### How to read it, and three things not to over-read

**The wall fixes convergence, and that is the headline.** EDM 1.4e-03 -> 9.6e-07
crosses this page's 1e-5 bar in 40 % fewer iterations. The NP sector wandering
unphysical was what made the likelihood pathological; constraining it to the
physical region gives a well-behaved fit.

**The tension is REAL, not a masked pathology.** Delta(chi2) = +11.6 and the
saturated p-value halving (2.33 % -> 1.16 %) is the cost of physicality. That is
the free-vs-walled tension test, and it says the data would rather sit outside
the physical region than in it.

**sigma(alpha_s) tightening 17 % is NOT a gain.** It is NP freedom that pointed
into unphysical territory being removed, and rho(alphaS, lambda4) rises
0.45 -> 0.63 as the block stiffens. Read it as the NP sector being stiffened,
not as a better measurement.

**The walled NP tune must not be quoted as measured.** `lambda2_nu` is RAILED at
the wall: its +0.0049 IS the 5e-3 margin and its sigma is the wall's width
(predicted to 1 %), not data-determined.

**The residual `lambda4_nu` = -4.3e-04 is not closable and not consequential.**
It anti-damps only past b_T 3.4 GeV^-1, where f^NP ~ 1e-3; sigma(theta) there is
1.4e-04, i.e. ~5e7 curvature against the wall's 1.1e4, so no sane tau closes it.

Neither p-value is comfortable. A 1-2 % saturated p-value says the model does
not describe this data especially well REGARDLESS of the wall, which is a
separate question from blinding or NP physicality.

### All four postfits are genuine MINIMA -- so the alpha_s split is real

Eigendecomposed the postfit covariance of every arm (`scripts/check_minimum.py`,
`logs/mincheck.log`). A negative eigenvalue of `cov` is a negative eigenvalue of
H, i.e. a direction still going down; EDM alone cannot tell a minimum from a
saddle, since both are stationary.

| arm | min(eig cov) | max(eig cov) | negative | kappa(cov) |
|---|---|---|---|---|
| `DATABLIND` | +5.14e-10 | 1.529 | **0** | 3.0e+09 |
| `DATAPC2` | +5.57e-11 | 2.574 | **0** | 4.6e+10 |
| `DATAWALL5` | +8.57e-09 | 1.764 | **0** | 2.1e+08 |
| `ASIMOVREF` | +2.85e-05 | 1.419 | **0** | 5.0e+04 |

Zero negative eigenvalues everywhere -- not even below the roundoff floor -- and
Cholesky succeeds on all four. **Every arm is a genuine local minimum.**

**Consequence, and it is the serious one.** `DATABLIND` and `DATAPC2` differ by
**3.5 sigma in alpha_s** on the SAME data with the SAME blinding offset, and
both are genuine minima. So this is not an unconverged fit: the likelihood is
MULTIMODAL in alpha_s, and which value comes out depends on the path the
minimiser takes. That is `studies/np-wall-local-minima`'s finding appearing
directly on alpha_s in a data fit rather than on the NP lambdas.

An unwalled alpha_s from this configuration is therefore **basin-dependent at
the 3.5 sigma level**. The walled arm is the only one with a principled reason to
prefer its basin, and it sits 0.127 sigma from the plain arm.

**Second reading of the same table.** kappa(cov) is 3.0e+09 on data against
5.0e+04 on Asimov -- five orders worse. Since `cov = H^-1`, the tiny minimum
eigenvalue is an extremely STIFF direction, and 3.0e+09 matches the 3.3e+09
block recorded in the preconditioner work. The data basin is pathologically
anisotropic in a way the Asimov one is not, which is the same illness the
degeneracy number reports and the wall partially cures (2.1e+08, an order
better than unwalled).

### Preconditioning: NOT negative -- it converged, but to a different minimum

CORRECTION to an earlier reading of this page. `DATAPC2` was judged a negative
result from a MID-FLIGHT snapshot on loss alone. It finished at iteration 291 /
4262 s with **EDM 4.909e-06** against the plain arm's 1.386e-03 -- 282x better,
and below this page's 1e-5 bar. Preconditioning DID converge the fit.

What it did not do is find the same place: loss 411.08 against 405.56, and
alpha_s **3.5 sigma** away (see above). Judge it on that, not on the loss.

The reason is NOT that preconditioning cannot address degeneracy: block
whitening decorrelates, so it targets exactly that. It is the **ridge**. Ours was
`0.0593 x max|diag|` -- 5.9 %, enormous -- and `preconditioner.py`'s own
docstring names the failure mode: a single scalar ridge *"swamps every direction
softer than |lam_min| and leaves them near-null"*, which are precisely the
degenerate directions. Hence kappa 4.22e+04 -> 1.75e+04, only 2.4x, against
degeneracy 1.08e+05. A 5.9 % ridge also says the block is badly indefinite at
the reference point, or the Cholesky would not have needed it.

So the untried path is `--preconditionTransform spectral`, which derives its
floor from the numerical RANK of the block instead of a scalar ridge.

### An unenforced gap in the wall port

The wall resolves its anchors from the card's recorded correction runcard, but
the model does not register `indata` for it, so a fit using
`anchor_source=cache` or `anchor_override=` would shift the model's map WITHOUT
shifting the wall's, undetectably from `indata`. The wall prints every anchor it
resolves, so the mismatch is visible in the log -- but it is not enforced.

---

## Next steps (Luca, 2026-09-10)

Once the blinding validation is settled, in this order:

1. **Turn the preconditioner on** and see whether it helps. Note there is
   nothing to pull from another worktree, contrary to how this was first framed:
   `blinding-additive` sits on `combined-156-157`, which already merges #156
   (preconditioner) and #157 (stall threshold). It is compiled in and simply not
   enabled -- add `--precondition --preconditionBlocks auto`, optionally
   `--preconditionTransform {ridge,spectral}`. The earlier
   `260909-data-fit/run_data_fit_{pc,free,mild}.sh` arms are the precedent.
2. **If the NP sector blows up, apply the damping wall.** Reachability checked
   ahead of time, because it is NOT in this tree: only stale `.pyc` survives in
   `scetlib_np/__pycache__/`, since `scetlib_np` is untracked on this branch.
   The source is at `PR710/WRemnants/wremnants/postprocessing/scetlib_np/np_damping_wall.py`,
   and on branches `scetlib-np-param-model` / `np-active-params` (added in
   `d1a26d24`). It is a rabbit Regularizer, passed via `-r/--regularization`.
3. **Check whether anything ELSE is blowing up** -- the 46 POUs are reported
   UNBLINDED (rabbit never blinds the `npou` block), so their postfit values and
   pulls are directly readable. alphaS is the only blinded parameter.

---

## Open questions

- Deferred with the scope decision: the alpha_s **domain guard** (nothing in
  SCETlib validates alpha_s — no positivity or Landau check in `alphas_run`, and
  the PDF alpha_s member pair extrapolates unbounded), a **blinding test
  suite** (none exists), and three unrelated leak paths (saturated-projection
  fit, the limits driver, blinded `--pseudoData` solvability).
- This ships a blinding change with **no regression test**; the default-False
  path in the verification is the only guard for other analyses.
