---
title: Face-held traditional and global impacts at an active constraint face
slug: 261016-face-held-impacts
study: ct18z-nominal-fits
status: done          # active | done | paused | abandoned
created: 2026-10-16
updated: 2026-10-16
owner: study-worker
---

# Face-held traditional and global impacts at an active constraint face

**Task:** Can rabbit compute traditional impacts (ungrouped and grouped), and the grouped global impacts' `stat` remainder, when the fit sits on an active hard-constraint face, and do they agree with an exact reference?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-10-16)

- **Answer:** yes. rabbit branch `face-held-impacts` (bf9dfb1, 2 commits on WMass main 2d9f380, worktree
  `/work/submit/lavezzo/rabbit-face-impacts`, NOT pushed, no PR) computes traditional impacts (ungrouped + grouped)
  and Gaussian global impacts at an active face with the faces held; exact against frozen / eliminated / frozen-group
  references; no-face fits bit-identical. On LAT the traditional impacts now exist (Data stat 0.86, total 1.14, alpha_s
  x1e-3). LAT's GLOBAL Data stat stays undefined (NaN) -- not a face effect (the face is linear), see Result.
- **PR:** https://github.com/WMass/rabbit/pull/196 (approved by Luca; head lucalavezzo:face-held-impacts = e50a872 +
  bf9dfb1, base WMass main 2d9f380, not stacked). Body: `scripts/pr_body.md`.
- **Next action:** review on #196; orchestrator: how the global "Data stat." is presented on LAT (Open questions).
- **Blocking on:** nothing.
- **Running:** nothing (LAT_facefix pid 774253 finished; results written).

---

## Log

<!-- Newest first. What was tried, what happened, why — with an evidence path. -->

### 2026-10-16
- Worktree `/work/submit/lavezzo/rabbit-face-impacts`, branch `face-held-impacts` off WMass main 2d9f380 (has #189).
- **What was missing (code read).** At an active face `cov` is already face-held, but (i) `impacts_parms` builds the
  stat-block covariances as the PLAIN inverse of the Hessian's stat block (`_cov_stat_floating`), (ii) each group's
  conditional uncertainty `v C_gg^-1 v^T` is singular whenever a face normal lies entirely inside the group (the
  face-held C has a null direction there), (iii) for a bound face the SVD null space leaves O(1e-17) in the held
  parameter's row, so its ungrouped impact C_pj/sqrt(C_jj) is 0/0 noise. `report_constrained_postfit` therefore
  skipped `--doImpacts` AND `--gaussianGlobalImpacts`. The gaussian skip was unnecessary: `_dxdvars` already uses
  `self.cov` (face-held), which is the exact KKT response dx = -C_held d(grad)/d(obs) (constraints do not depend on
  the global observables).
- **Why LAT's grouped global `stat` is NaN — NOT the face algebra.** LAT's face (`lambda2 + delta_lambda2*Y^2 >= 0`
  at |Y| = 2.5) is LINEAR in the fit coordinates (NP lambdas are `unit` reparametrisations, physical = anchor +
  width*theta), so the constraint-curvature term is zero and C H C = C holds: checked on the stored matrices,
  (C H C)_pp = 0.3250792316618 vs C_pp = 0.3250792316620 (H = inverse of `cov_released`). The remainder is
  var_total 0.32508 - var_x0 0.33586 - var_beta0 0.01136 = **-0.02215** because H_rest = H - diag(cw) (data +
  lattice + profiled bbb, i.e. everything that is not a Gaussian prior) is INDEFINITE (lowest eigenvalues -0.55,
  -0.30, -0.27, ...), so diag(C H_rest C) can be negative: it is -0.0108 held (+0.0129 released), a cancellation
  between O(300) block terms. So the "data stat" global impact of alpha_s is ~0 here either way and the face
  projection pushes it below zero. (evidence: scratch inspection of `fitresults_LAT.hdf5`, numbers above)
- At a CURVED face (NOLAT's TMD cubic) there IS a face term: C W C = C with W = H - Hc gives
  sum_sources = diag(C H C) = diag(C) + diag(C Hc C); the remainder alone charges -diag(C Hc C) to the data.
- Implemented (uncommitted at this point): `postfit.face_tangent_basis` (exact zero rows for pinned coordinates),
  `face_held_inverse`, `held_directions_in_group`, `face_held_group_impact`, `active_faces` (factored out, same
  arithmetic); `Fitter.postfit_faces` set by `constrained_postfit` / `postfit_faces_at`; `impacts_parms` branches to
  `_face_held_impacts_parms` only when a face is active; `global_impacts_parms` adds diag(C Hc C) back to the stat
  remainder (None without a face -> same graph); skip removed in `rabbit_fit.py`; traditional_impacts gets an
  optional `group_impact_fn` hook (default path untouched).
- **Committed** `face-held-impacts` e50a872 (not pushed). All 7 new tests pass; `test_trust_constr.py` (skip test
  replaced by `test_impacts_are_written_at_an_active_face`: impacts / global / gaussian written, finite, the held
  parameter's own impact exactly 0) + `test_constraints_postfit.py`: 30 passed. Container black/isort/CI-flake8 clean.
- Curved-face test needed a STRONGLY curved face to be sensitive: with `a*b >= lb` the Lagrangian term moved the
  stat variance by only 1e-6 (the face curvature is tiny against the likelihood's). Replaced by a disk of radius 2
  sigma centred 3 sigma away: now W vs H changes the stat-block variance by > 1 % (asserted), and the FD refits
  (shift x0 of a constrained nuisance by 1e-3, refit) give dx_POI/dx0 = C_held cw to 2e-3, 10x closer than the
  released C. NB: an FD refit started ON the face (warm) gave a wrong response (0.36e-3 vs 0.89e-3) -- the known
  trust-constr warm-start defect (261015-trustconstr-warmstart, cause c); refits are started from the interior.
  Also hit: a start at the disk centre (row gradient 0) makes `build_scipy_constraints` drop the row silently.
- **Bit-identity, no active face** (`scripts/bitident_check.sh`): rabbit_fit on the rabbit test tensor with
  `--doImpacts --globalImpacts --gaussianGlobalImpacts --saveHists --computeHistErrors`, (i) no constraints,
  (ii) an inactive `Bounds bkg_norm<=5` under trust-constr: production (2d9f380+196bfca) vs branch, every dataset
  of fitresults identical (all hists incl. variances, mappings leaf by leaf) except `epoch_time` (wall clock).
- 09:36 launched the LAT postfit rerun (one job, mem_gate slot 1, pid 774253):
  `scripts/run_LAT_postfit.sh`, `--externalPostfit LAT_x_only.hdf5 --noFit --doImpacts --globalImpacts
  --globalImpactsDisableJVP --saveHists --computeHistErrors -m Project ch0 ptll`, same card/cache/model/
  constraints/lattice as LAT. `LAT_x_only.hdf5` = x of fitresults_LAT.hdf5 (identical to
  snapshot_fitresults_LAT.hdf5, max diff 0): with LAT's covariance loaded `--doImpacts` refuses (it needs the
  Hessian), so the external result carries x only and the Hessian is recomputed. Log: `logs/LAT_facefix.log`.
- ~10:00 LAT_facefix done (postfit 689 s; impacts_parms 610 s, global 7.5 s): same edmval 2.3e-17, multiplier 6.41,
  cov identical to LAT's. Traditional impacts finite; global Data stat NaN as predicted (remainder -0.0221).
  `scripts/lat_impacts_table.py` -> `LAT_impacts_table.txt`; plots `workflows/pullsAndImpacts.sh ... -o LAT_impacts
  -P alphaS` (rc 0, traditional + global, grouped + ungrouped) -> [LAT_impacts/](LAT_impacts/).
- Full suite: 475 passed, 1 failed (`test_every_driver_called_fitter_method_is_classified_for_sharding`: the new
  driver call `postfit_faces_at` unclassified) -> added to `_SHARDED_SAFE` (bf9dfb1), test_sharded_fit.py 43 passed.
- PR (Luca approved, via orchestrator): WMass main still 2d9f380 (0 new commits); full suite with the worktree
  prepended (import path checked) 476 passed; CI lint commands (isort/flake8/black on the whole repo) clean; pushed
  `face-held-impacts` to lucalavezzo/rabbit; opened https://github.com/WMass/rabbit/pull/196 against main (body
  `scripts/pr_body.md`; real check quoted in rabbit units + x2 convention, no alpha_s value).
- Tests `tests/test_face_held_impacts.py`: (a) bound on freeB / normC / POU a == frozen fit, (b) linear a + 2b face
  == eliminated ParamModel, (c) curved a*b face vs frozen-group held fits, FD refits, diag(C H_data C), (d) inactive
  face unchanged. First run: (a) freeB, normC pass at rtol 1e-9 on every impact array.

---

## Result

**Caveats first.** LAT = real-data, blinded fit (alpha_s value never printed; sigmas/impacts only), CT18Z, lattice
term in the likelihood, one active face that is WEAKLY binding (releasing it lowers the NLL by 0.456 < 0.5): the
face-held impacts describe the fit with the face held, and any interval along the face direction is one-sided (scan).
Impacts below are as plotted by `pullsAndImpacts.sh` (alpha_s in 1e-3, i.e. 2x rabbit's POI units). The LAT postfit
was recomputed from LAT's minimum (x only), not refitted: the recomputed face-held covariance equals the stored one
exactly (max |C - C_LAT| = 0), same edmval 2.3e-17 and multiplier 6.41.

**What was missing.** At an active face the stored `cov` was already face-held, but the traditional impacts used the
plain inverse of the Hessian's stat block for `stat`/`binByBinStat`, the grouped (conditional) impacts were singular
for any group containing a whole face normal (on LAT: the NP groups, which hold both lambda2 and delta_lambda2), and a
bound-held parameter had O(1e-17) instead of zero variance (0/0 ungrouped impact). So rabbit skipped `--doImpacts`
and, needlessly, `--gaussianGlobalImpacts` (their response dx = -C_held d(grad)/d(obs) was already the exact KKT one).

**Fix** (`rabbit/constraints/postfit.py`, `rabbit/fitter.py`, `rabbit/impacts/*`, `bin/rabbit_fit.py`): every
covariance in the impacts is taken with the faces held -- stat block (with and without bbb) =
Z (Z^T W Z)^-1 Z^T on the stat block with W = H - sum mu d2c; groups conditioned on the complement of the face
directions that lie inside the group; bound-pinned coordinates exactly zero. Global impacts: at a CURVED face the
sources add up to diag(C H C) = diag(C) + diag(C Hc C), so `stat` gets diag(C Hc C) back (zero for a linear face).
Skip removed. Without an active face nothing changes (bit-identical, checked end to end vs production).

**Validation** (tests/test_face_held_impacts.py, all at the same point so they test the algebra to round-off):
(a) bound face on an unconstrained nuisance / a constrained one / a model parameter == the fit with it frozen: all
six impact arrays (traditional, global, Gaussian; ungrouped + grouped) to rtol 1e-9; (b) linear face a + 2b >= lb ==
the eliminated ParamModel (a = lb - 2b) to 1e-8, a's impact = -b's; (c) curved (disk) face, where the Lagrangian
term moves the stat variance by > 1 %: grouped impacts == sqrt(sigma^2 - sigma^2[group frozen, face held]) from
rabbit's own freeze path (1e-6), global source response == finite-difference constrained refits (2e-3; the released
C is 10x worse), corrected `stat`^2 == diag(C H_data C) (1e-8); (d) no face: identical. Full suite 476 passed
(one sharding-classification failure for the new driver call, fixed in bf9dfb1, that file 43/43), container
black/isort/flake8 clean.

**LAT, traditional impacts with the face held** (alpha_s in 1e-3):
total 1.14; Data stat. 0.86; Nonperturbative 0.93, scetlibNPFeff 0.83, scetlibNPgammaNu 0.08; pdfEig 0.79; TNP 0.76;
Luminosity 0.44; Theory (EW) 0.38; b,c masses 0.34; resumScale 0.29; angular coeffs 0.22; Simulation stat. 0.14.
With all constrained nuisances frozen sqrt(0.864^2 + 0.143^2) = 0.875, so the constrained-nuisance part is
sqrt(1.140^2 - 0.875^2) = 0.73. The traditional "Data stat." floats every prior-free parameter (POI, NP lambdas,
POUs), so it contains the NP freedom; the NP groups (0.93/0.83) overlap it. (numbers: `LAT_impacts_table.txt`)

![LAT traditional grouped impacts, face held (weakly binding face; alpha_s blinded, impacts only)](LAT_impacts/traditional_impacts_grouped_alphaS.png)

**LAT, global impacts**: unchanged by the fix (linear face -> no curvature term): pdfEig 0.76, TNP 0.57, lumi 0.41,
EW 0.34, b/c 0.25, sim stat 0.21, ... and **Data stat. still undefined (NaN, drawn 0.00)**. Reason, from the stored
matrices: remainder var_total - var_x0 - var_beta0 = 0.3251 - 0.3359 - 0.0114 = -0.0221 (rabbit units). Since
C H C = C holds exactly here (checked to 1e-12), this is diag(C H_rest C) - var_beta0 with H_rest = H - diag(cw)
(data + lattice + profiled bbb) INDEFINITE (lowest eigenvalues -0.55, -0.30, ...); diag(C H_rest C) is -0.0108 held vs
+0.0129 released, the small difference of O(300) block terms. In the likelihood-based global decomposition the priors
alone already account for > 100 % of the face-held variance; the face only tips a ~0 remainder below zero. No
face-held construction can make it positive. Global and traditional agree where they should (constrained
nuisances: pdfEig 0.76 vs 0.79, lumi 0.41 vs 0.44, global <= traditional); prior-free NP groups are 0 in global by
construction.

![LAT grouped global impacts (Data stat. NaN, drawn 0: not a face effect, see text)](LAT_impacts/global_impacts_grouped_alphaS.png)

**Physics read.** With the face held, alpha_s on LAT is dominated by the NP form (Nonperturbative 0.93 of 1.14 in the
traditional decomposition, consistent with the study's picture that alpha_s and the prior-free NP lambdas are
strongly correlated in the reco ptll fit), then data stat (0.86, which already contains the NP freedom), PDF (0.79)
and TNP (0.76). These traditional numbers are now well-defined at the face; because the face is weakly binding they
are those of the fit ON the face, and the released fit has a larger total (sigma 0.641 vs 0.570 in rabbit units, i.e.
1.28 vs 1.14 in 1e-3).

---

## Findings

1. At an active face, traditional impacts must use the face-held stat-block covariance (Lagrangian Hessian on the
   face directions) and condition groups on the complement of in-group face directions; then they equal the
   frozen / eliminated fits exactly. Gaussian global impacts were already correct with the face-held cov.
   — (evidence: tests/test_face_held_impacts.py, branch face-held-impacts bf9dfb1)
2. Global impacts at a CURVED face: sources sum to diag(C H C) = diag(C) + diag(C Hc C); the data-stat remainder must
   get diag(C Hc C) back. Zero for faces linear in the fit coordinates (the NP `unit`-reparametrised bounds and the
   L2(Y) rows), non-zero for the TMD large-b cubic. — (evidence: test_curved_face_global_impacts)
3. LAT's NaN global "Data stat." is NOT a face artefact: H minus the priors is indefinite on this fit and the
   remainder is a ~0 difference of O(300) terms, -0.022 held. — (evidence: Log 2026-10-16, LAT_impacts_table.txt)
4. LAT postfit recomputed from x only reproduces the stored face-held covariance bit for bit. — (LAT_impacts_table.txt)
5. Generalizable (knowledge/, orchestrator's call): a trust-constr refit warm-started ON a face gave a wrong
   finite-difference response (warm-start defect, cause c of 261015-trustconstr-warmstart); a start where a
   constraint row has zero gradient silently drops the row in build_scipy_constraints.

---

## Open questions

- How to present the global "Data stat." on LAT (and any fit where diag(C H_rest C) < 0): the Gaussian global data
  stat (`--gaussianGlobalImpacts`, sum (dx/dn)^2 var(n), always >= 0, now allowed at a face) was NOT run on the real
  fit (not in the approved flags; its jacobian over 3720 parameters through the SCETlib model may be memory-heavy);
  or quote the traditional one.
- `global_impacts_obs` (global impacts on observables) has the same remainder and would need diag(J C Hc C J^T) at a
  curved face; not touched.
- NOLAT (curved TMD cubic face active) is the first real case where the curvature correction is non-zero; rerun its
  postfit with this branch once NOLAT is final.
- impacts_parms took 610 s on LAT, almost all of it the profile=False Hessian, as before; not a new cost.
- PR opened: https://github.com/WMass/rabbit/pull/196 (independent of the tc-precond-pr / tc-warmstart PRs).
