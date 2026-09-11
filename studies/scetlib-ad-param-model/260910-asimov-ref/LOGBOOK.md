---
title: Unblinded Asimov reference for additive blinding
slug: 260910-asimov-ref
study: scetlib-ad-param-model
status: done          # active | done | paused | abandoned
created: 2026-09-10
updated: 2026-09-10
owner: study-worker
---

# Unblinded Asimov reference for additive blinding

**Task:** Does an UNBLINDED Asimov fit on the same card/cache give the same sigma(alpha_s) as the blinded data arm (0.00132)? I.e. does additive blinding leave the uncertainty exact?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-09-10)

> **Ran, converged, and it agrees. Additive blinding leaves sigma(alpha_s) intact.**
> The unblinded Asimov reference converges perfectly (EDM **1.577e-27**, 0 of 3720
> negative Hessian eigenvalues, Cholesky OK, exit 0) and gives
> **sigma(alpha_s) = 0.001371**, against the blinded data arm's **0.001321** —
> agreement to **3.8 %**. Read the caveat first: this is Asimov against DATA, so
> only the sigma is comparable, and the data arm did not converge (EDM 1.4e-3)
> with its NP sector unphysical, which is enough to account for a few percent.
> What the test excludes is the bug it was built for: the old multiplicative
> blinding would have rescaled sigma by a random factor of order `e^±5`.

- **Next action:** none — task closed. The one cleaner test left is listed under
  Open questions (same-dataset blinded-vs-`--unblind`, which would show exactness
  to machine precision rather than to 3.8 %).
- **Blocking on:** nothing

---

## Log

<!-- Newest first. What was tried, what happened, why — with an evidence path. -->

### 2026-09-10 — finished and read out

- Exit 0 at 16:39:36, **5:13 wall**, peak RSS **184.6 GiB** (as predicted). Much
  faster than the ~25 min expected: initialisation took **169 s** rather than the
  ~1086 s of the AS770 arm, because the 8.7 GB cache was already warm in page
  cache from the concurrent `DATAPC2` fit. Breakdown: 169 s init, 1.8 s prefit,
  122.9 s "fit" (which for `ifit = -1` is the covariance/Hessian pass, no
  minimiser), 4.7 s postfit; 298.5 s total.
  (evidence: `logs/fit_ASIMOVREF_260910_163356.log`)
- Fitresult:
  `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260910_blinding_final/fitresults_ASIMOVREF.hdf5`
  (110.8 MB).
- Convergence and sigma read out with `scripts/run_readout.sh`, which runs this
  task's `readout_convergence.py` and then the blinding task's
  `read_postfit.py` **verbatim** (run, never edited — it belongs to
  `../260910-blinding`), so that both arms' sigmas come out of the same code path
  and the same 0.002 width conversion.
  (evidence: `logs/readout_ASIMOVREF.log`)
- The eigenvalue spectrum had to be recovered post-hoc: the fit-770 arms got
  theirs from a harness that monkey-patches `Fitter.edmval_cov`, and this arm ran
  plain `rabbit_fit.py` on purpose so as to match the DATABLIND command exactly.
  `cov` is saved, and `eig(H) = 1/eig(cov)` sign for sign, so the count is
  recoverable — and `cov` existing at all already proves rabbit's Cholesky on H
  succeeded, since a failure raises `LinAlgError` (potrf) and writes nothing.
- Blinded arm's sigma re-read to 6 digits for the comparison (theta sigma
  0.660363 -> 0.001321); only its **sigma** was extracted, its central value
  stays blinded (evidence: `logs/readout_DATABLIND_sigma.log`).

### 2026-09-10 — launched ASIMOVREF

- Own harness written (the previous attempt at this arm never started: the driver
  script was edited while bash was executing it, and bash reads a script by byte
  offset, so it resumed mid-word). `scripts/run.sh` + `scripts/incontainer.sh`
  are copies of the 260910-blinding pair; the ONLY change is `D=` in run.sh,
  repointed at this task's scripts dir. `incontainer.sh` is byte-identical on
  purpose — its own `D=` points at `260908-fit-770/lib`, whose `scetlib_tf.py`
  carries the hvp zero-seed skip (without it the postfit Hessian pass costs ~77x
  more), and it prepends the rabbit-blinding worktree to PYTHONPATH and asserts
  the imported `rabbit.fitter` carries the blinding change.
- Harness smoke-tested with `true` before spending 25 min on it
  (evidence: `logs/smoke_260910_163241.log`). Env stamp confirms:
  rabbit `0f64bbb` (`blinding-additive`), additive POI blinding present True,
  physical-start frame shift present True, `libscet-qT.so` md5 `71b5e68a…`
  (the validated b66f8de snapshot), zero-skip present True.
- Launched `scripts/launch_asimov_ref.sh` detached at 16:33:56
  (evidence: `logs/fit_ASIMOVREF_260910_163356.log`, symlinked `logs/LATEST`).
  Command identical to the DATABLIND arm except `-t -1` and the per-arm postfix
  and snapshot filename.
- Node was busy (loadavg ~400, a concurrent `DATAPC2` data fit of the
  orchestrator's) but memory was ample (~833 GB free, ~1291 GB available against
  a ~184 GiB expected peak). Only this one arm launched.
- Prefit block confirms the Asimov setup: `Linear chi2 ndof 780, chi2 = 0,
  p-value 100.0%`. That is the Asimov signature, not a suspiciously good fit —
  the Asimov dataset IS the prediction at the anchor, so the prefit residual is
  identically zero. (The printout labelled `chi2/ndf` is the raw chi2; that
  mislabel is a known rabbit printout trap, not a number to divide again.)
- `edmval: 1.5771526635172484e-27` at 16:37, i.e. **1.577e-27** — equal to the
  reference AS770 Asimov arm's EDM to every digit quoted in the study logbook
  (`../260908-fit-770/LOGBOOK.md:253`). Same card, same cache, same anchor, so
  this is the expected reproduction and a check that nothing about the blinding
  branch perturbed the Asimov path.
- Blinding mechanics read off the source rather than inferred
  (`/work/submit/lavezzo/alphaS/rabbit-blinding/rabbit/fitter.py`):
  `get_poi()` returns `poi * _blinding_offsets_poi + _blinding_offsets_poi_add`
  (`:788`), and the additive mode leaves the multiplicative slot at 1. So the
  map physical = blinded + offset is a **translation, with unit Jacobian**, and
  the covariance, the uncertainties and the impacts are preserved exactly; the
  multiplicative form instead divides all of them by the random factor `B`.
  `blinded_fits = [f == 0 or (f > 0 and toysDataMode == "observed") for f in fits]`
  (`bin/rabbit_fit.py:874`) is False for `-t -1`, which is what makes an Asimov
  fit an unblinded reference.

---

## Result

### The caveats, before the numbers

1. **Asimov against DATA.** Only the **sigma** is expected to agree. The central
   values are not comparable and neither is the chi2: the Asimov dataset *is* the
   prediction at the anchor, so its chi2 is identically 0 and its p-value 100 %,
   which is arithmetic and not a measure of fit quality.
2. **The data arm did not converge.** DATABLIND stopped at EDM **1.386e-03** with
   scipy `success: False, status: 2, "A bad approximation caused failure to
   predict improvement"`, and its NP sector is unphysical (lambda2_nu and lambda4
   negative in physical units). Its sigma is therefore a curvature at a point
   that is neither the minimum nor physical. The Asimov sigma carries none of
   that.
3. **The two Hessians are evaluated at different parameter points.** The Asimov
   arm sits at the anchor with all 47 fitted parameters exactly 0; the data arm
   sits displaced, in the region where the NP form factor is most nonlinear.
   Curvature genuinely differs between those points, so a few percent is the
   *expected* level of agreement, not a defect.
4. **This arm is unblinded by construction and its alphaS central value is not a
   measurement.** `blinded_fits = [f == 0 or (f > 0 and toysDataMode ==
   "observed") for f in fits]` (`bin/rabbit_fit.py:874`) is False for `-t -1`.
   The value the fit sits at is the Asimov *input* — the anchor, 0.118 — so
   nothing here is a result to be blinded. Nothing from the blinded arm's central
   value was read or recorded.

### Convergence first

| | ASIMOVREF (`-t -1`, unblinded) |
|---|---|
| exit status | **0** |
| minimiser message / status | **none — `ifit = -1`, the minimiser is never invoked** |
| EDM | **1.5771526635172484e-27** |
| negative Hessian eigenvalues | **0 of 3720** (0 as computed, 0 above the 3.15e-14 roundoff floor) |
| Cholesky | **succeeded** — rabbit's own (a covariance exists) and an independent recheck on `cov` |
| saturated chi2 | 0.0 / 733 dof, p = 100 % (Asimov arithmetic) |
| wall / peak RSS | 5:13, 184.6 GiB |

The EDM reproduces the reference AS770 Asimov arm's **1.577e-27** to every digit
quoted in `../260908-fit-770/LOGBOOK.md:253`, and the negative-eigenvalue count
reproduces its **0 of 3720**.

### The number, and the comparison that is the point

| arm | data | theta sigma | sigma(alpha_s) |
|---|---|---|---|
| **ASIMOVREF** (unblinded) | Asimov at the anchor | 0.685291 | **0.001371** |
| **DATABLIND** (blinded) | real data | 0.660363 | **0.001321** |

**Ratio 1.0377, i.e. agreement to 3.8 %** (absolute difference 0.000050 on
alpha_s).

### What it means

**Additive blinding leaves the uncertainty intact.** The claim is established on
two legs, and they are different in kind:

* **Analytically, it is exact.** `get_poi()` returns
  `poi * _blinding_offsets_poi + _blinding_offsets_poi_add`
  (`rabbit-blinding/rabbit/fitter.py:788`); in additive mode the multiplicative
  slot stays at 1, so physical = blinded + offset is a **translation**. A
  translation has **unit Jacobian**, so the covariance, the uncertainties and the
  impacts are unchanged *exactly* — as `fitter.py:684-688` itself now states. The
  multiplicative form instead sends sigma to sigma/`B`, leaving only *relative*
  uncertainties usable, which is what made sigma(alpha_s) unreadable before the
  change and is why this mattered: sigma(alpha_s) is a headline number of
  `AN-25-085`, quotable before unblinding, and it was readable under the template
  `pdfAlphaS` treatment (a NOI, hence additively blinded) that the model
  parameter replaced.
* **End-to-end, this arm confirms nothing else rescales it.** The analytic
  argument covers `get_poi`; the fit exercises the whole path through to the
  written `cov` and impacts. The observed 3.8 % is what Asimov-vs-data plus a
  non-converged, unphysical data point should give. The failure mode being
  tested would look nothing like it: with `ln B ~ N(0,5)`, a multiplicative
  blind would typically put the reported theta sigma somewhere between 0.0046
  and 102 instead of 0.66, and the chance it would land within the observed
  3.8 % of the truth is **0.6 %**.

The honest limit of the test: it demonstrates agreement to 3.8 %, not exactness.
Exactness is the analytic statement; measuring it would need the *same* dataset
blinded and unblinded (see Open questions).

---

## Findings

<!-- One line each. A finding that generalizes beyond the parent study → tell the
     orchestrator; it belongs in ../../../knowledge/. -->

1. The unblinded Asimov reference converges cleanly on the blinding branch —
   EDM 1.577e-27, 0 of 3720 negative eigenvalues, Cholesky OK, exit 0 — i.e. the
   additive-blinding change did not perturb the Asimov path
   (evidence: `logs/fit_ASIMOVREF_260910_163356.log`, `logs/readout_ASIMOVREF.log`).
2. sigma(alpha_s) = 0.001371 (Asimov, unblinded) vs 0.001321 (data, blinded):
   **3.8 %**, with the data arm non-converged and NP-unphysical. Additive
   blinding leaves the uncertainty readable; the multiplicative form it replaced
   would have rescaled it by a factor of order `e^±5`
   (evidence: `logs/readout_ASIMOVREF.log`, `logs/readout_DATABLIND_sigma.log`).
3. An Asimov fit's chi2 is identically 0 with p = 100 %, and its prefit
   `Linear chi2` prints the same. That is arithmetic — the Asimov dataset is the
   prediction — and must not be read as fit quality. (Also: the field labelled
   `chi2/ndf` in that printout is the raw chi2, a known rabbit mislabel.)
4. The postfit Hessian's smallest eigenvalue is **+0.7046**, i.e. *below* the
   unit-prior floor, and that is correct rather than alarming: rabbit applies
   Gaussian priors to **46 of the 47** model parameters and alphaS, the single
   POI, has **none**, so its direction takes curvature from data alone and is not
   floored at 1. Worth knowing because a smallest eigenvalue below 1 is otherwise
   a natural thing to flag as a saddle
   (evidence: `logs/fit_ASIMOVREF_260910_163356.log`, the `[paramPriors]` line).
5. Practical: the eigenvalue spectrum of a plain `rabbit_fit.py` run is
   recoverable post-hoc from the saved `cov` (`eig(H) = 1/eig(cov)`, sign for
   sign) — the 260908-fit-770 harness monkey-patch is not needed just to count
   negative directions, and "a covariance exists at all" already *is* the
   statement that rabbit's Cholesky on the Hessian succeeded
   (evidence: `scripts/readout_convergence.py`).

---

## Open questions

- **The exactness test this arm cannot do.** Agreement here is 3.8 %, limited by
  Asimov-vs-data, not by blinding. The definitive test is the *same* dataset
  fitted twice, blinded and with `--unblind` (the flag exists —
  `bin/rabbit_fit.py:432` passes `unblind=args.unblind` into
  `fitter.py:599`): sigma should then match to machine precision. A blinded toy
  (`-t 1 --toysDataMode observed`, which `blinded_fits` marks blinded) against
  the same seed with `--unblind` would do it without unblinding real data. Cheap
  next task if the exactness claim needs to be measured rather than argued.
- **Why the smallest Hessian eigenvalue differs from the AS770 reference.** This
  arm gives +0.7046; the AS770 arm was recorded at +0.9999998. Finding 4 explains
  why a value below 1 is legitimate here, but not why the two differ — and the
  two numbers are not the same measurement (AS770's came from a harness
  monkey-patch calling `eigh` on H directly, mine from `1/max(eig(cov))`), nor
  necessarily the same card. Flagged rather than chased; it does not touch the
  verdict, since both arms give 0 negative eigenvalues and a successful Cholesky.
- **The blinding offset was deliberately not computed.** The multiplicative
  counterfactual could be made exact rather than probabilistic, since the offset
  is `deterministic_random_from_string(seed)` and so a fixed number — but
  deriving it would hand over the means to unblind the central value, so the
  comparison is left as the `N(0,5)` statement instead.
- No figures were produced: the result is two numbers and a spectrum, and a plot
  of it would be decoration rather than evidence.
