---
title: Saturated sub-fit diagnosis
slug: 261016-saturated-subfit-diagnosis
study: ct18z-nominal-fits
status: active        # active | done | paused | abandoned
created: 2026-10-16
updated: 2026-10-16
owner: study-worker
---

# Saturated sub-fit diagnosis

**Task:** Why are the projected-saturated (ptll) sub-fits so slow and why do they not converge — warm start, hard constraints / wall, lattice term, missing preconditioner, or the minimizer itself? Attribute the cost quantitatively to each factor.

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-10-16 17:00)

- **Phase 1 answer (done, Result below):** plain trust-constr sub-fit slow = mu0 = 0.1 barrier restart on an
  ill-conditioned Hessian; C (warm start + spectral precond) converges (gtol) in 3.2 h vs 12.6 h, q = 79.1071 (LAT).
- **Phase 2 (NOLAT full postfit, all3 branch) — ANOMALY in the saturated sub-fit:** main postfit fine (NLL = snapshot,
  faces lambda2_nu + cubic(2.5), traditional impacts computed). The WARM leg of the ptll sub-fit stopped at status 2
  (xtol) at loss 335.537283 after 83 it / 567 HVPs / 1.52 h, sitting ON the cubic(|Y|=2.5) face with a RELEASING
  multiplier (+1.48); NOLAT's stopped plain sub-fit had reached a LOWER 335.536953 with that face released (lambda4 =
  1.8e-4, cubic(2.5) = 5.5e-4). The dual-sign check fired correctly and started the "release" leg from scipy's own
  interior-point start (mu0 = 0.1, scipy slacks): that leg walked away (loss up to 335.92, lambda2 0.14 -> 0.24,
  lambda2_nu 0 -> 0.04, cubic(2.5) violated by 3.4e-3) — the plain-ladder behaviour, likely hours. See Log 16:40.
- **Running:** NOLAT_PF (gate pid 1627133, job pid 1627151), log [logs/NOLAT_PF.log](logs/NOLAT_PF.log); release leg
  since 16:39. The fitresult (and so all deliverables) is written only at the end. NOT killed — orchestrator's call.
- **Next action:** orchestrator to choose: (a) let the release leg run; (b) stop it, get the deliverables from a postfit
  without the saturated test (~45 min) and redo the ptll test separately; (c) fix the release leg to start warm.
- **Blocking on:** orchestrator decision.

---

## Log

<!-- Newest first. What was tried, what happened, why — with an evidence path. -->

### 2026-10-16 14:00 — phase 2: all-three branch, NOLAT full postfit, deliverables
- Branch `all3-local` in NEW worktree `/work/submit/lavezzo/rabbit-all3` = `satdiag-ws-pc` 0395383 + face-held-impacts
  e50a872, bf9dfb1 cherry-picked (no conflicts) → fc01d8d, **d573c1d**. Local only.
- Targeted tests (worktree prepended to PYTHONPATH, import verified): `test_trust_constr.py`,
  `test_trust_constr_warmstart.py`, `test_face_held_impacts.py`, `test_preconditioner.py`: **85 passed** in 446 s
  ([logs/pytest_all3_targeted.log](logs/pytest_all3_targeted.log)). Full suite running.
- 14:16 launched NOLAT_PF ([cmds/NOLAT_PF.inner.sh](cmds/NOLAT_PF.inner.sh)): `--externalPostfit snapshot_fitresults_NOLAT.hdf5`
  (converged main minimum, 2026-10-15 17:35, unchanged) `--noFit`, NOLAT's card/cache/model/constraints args, no lattice,
  `--minimizerWarmStart auto`, the four `--precondition*` flags, `--doImpacts --globalImpacts --globalImpactsDisableJVP
  --saveHists --computeHistErrors -m Project ch0 ptll --computeSaturatedProjectionTests`; MAXRUN=2 gate.
- Full suite on all3 (worktree prepended): **493 passed** in 797 s ([logs/pytest_all3_full.log](logs/pytest_all3_full.log)).
- NOLAT_PF main postfit (log): cache load ~25 min; Hessian 303 s at the snapshot point, loss there = 369.7186970935704
  (= NOLAT's minimum exactly). Faces: lambda2_nu >= 0 (2.6e-10, multiplier 32.45, release ΔNLL 15.63) and the TMD
  large-b cubic at |Y| = 2.5 (1.6e-9, multiplier 4.10, release ΔNLL inf). edmval on the faces 3.8e-16; released EDM
  "undefined (the loss Hessian is not positive definite across the faces)". **Traditional impacts computed** (298 s, no
  skip); global impacts at the curved face: curvature term diag(C Hc C) = 7.8e-5 added to sigma² (POI). Full saturated
  2ΔNLL 739.44 / 774, p 80.92 % (= NOLAT's); ptll linear chi2 66/39, p 0.4 %.
- Sub-fit: warm barrier mu0 = 8.57e-9; preconditioner Hessian 299 s, |H| in [-163, 9.45e5], 4 negative, kappa 1.72e7 -> 1;
  started 15:02 from loss 369.7186970936.
- **16:40 NOLAT_PF sub-fit anomaly.** Warm leg: status 2 (xtol, tr_radius 7e-11) at loss 335.53728316594936, nit 83,
  nfev 126, cg_niter 567, 5467 s, optimality 3.7e-7; rows: lambda2_nu 2.6e-10 (v −1.02), L2(2.5) 6.2e-7 (v −0.10),
  cubic(2.5) 1.6e-9 (v **+1.48**, releasing sign), others inside. It descended fast (q-to-go ~0 by 2900 s at
  335.53737) and then froze at the loss-noise floor on the cubic face. NOLAT's own stopped plain sub-fit
  (`snapshot_fitresults_NOLAT_saturated_Project_ch0_ptll.hdf5`, it 227) is 3.3e-4 LOWER (335.536953) with lambda4 =
  1.84e-4 > 0, cubic(2.5) = 5.5e-4 (face released), the rest within ~4e-4 internal units (alphaS 5.6e-5 internal,
  blinded difference) ([scripts/compare_snapshots.py](scripts/compare_snapshots.py)). So the true saturated minimum
  is a small move off the cubic face; Δq between the two points = 6.7e-4 (physically negligible).
  The warm start's dual-sign check caught it and launched the release leg with scipy's cold interior-point start:
  preconditioner rebuilt (296 s, kappa 3.25e7, 1 negative eigenvalue), mu0 = 0.1, and the first ~30 iterations
  walk away from the minimum (snapshot 16:54, it 33: loss 335.918, lambda2 0.241, lambda4 −1.5e-3, lambda2_nu 0.040,
  lambda4_nu 0.060, cubic(2.5) = −3.4e-3 violated; constr_violation ~2e-3–3e-2). That is effect (a)+(b) of
  261015-trustconstr-warmstart, now in the release leg: expect the plain ladder's hours. Design point for the warm
  start: the release leg should itself start warm (centred barrier, consistent slacks) with only the releasing row
  freed, not from scipy's cold start.
- 17:02 release leg: iteration 40 (1314 s into the leg), feasible again (constr_violation 0), barrier cut to 0.02, loss 335.675
  (still 0.14 above the warm leg's 335.537). Still running; orchestrator's call pending.
- LAT face-held impacts plots: `pullsAndImpacts.sh fitresults_LAT_facefix.hdf5 -P alphaS` →
  [../261015-cold-tc-fits/LAT/impacts_faceheld/](../261015-cold-tc-fits/LAT/impacts_faceheld/) (rc 0; traditional
  grouped: total 1.14, Nonperturbative 0.93, Data stat. 0.86, scetlibNPFeff 0.83, pdfEig 0.79, TNP 0.76, ×1e-3 on alphaS).

### 2026-10-16 12:37 — C (SATWSPC_LAT) done: converged, 3.9x faster
- Log [logs/SATWSPC_LAT.log](logs/SATWSPC_LAT.log); fitresult `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261016_saturated_subfit_diagnosis/fitresults_SATWSPC_LAT.hdf5`;
  comparison [compare_SATWSPC_vs_LAT.json](compare_SATWSPC_vs_LAT.json) ([scripts/compare_sat.py](scripts/compare_sat.py), run in the container);
  per-iteration [tc_legs_SATWSPC.json](tc_legs_SATWSPC.json).
- Cache load 130 s (page cache warm), preconditioner reference Hessian 407 s (|H| spectrum [-34, 9.45e5], 2 negative,
  kappa 2.66e7 -> 1), warm start: `warm_start_legs = ['warm']`, no releasing rows, mu0 = 4.0956e-10 (= LAT's final barrier,
  as predicted), one barrier stage the whole fit.
- Minimiser: status 1 (gtol), nit 89, nfev 112, njev 66, **cg_niter 982**, 11525 s, optimality 2.5e-9 (preconditioned
  frame; `optimality_physical` 1.6e-6), 23 rejected steps (32 % of time). Whole sub-fit pass (save_hists) 12961 s;
  job total 13121 s.
- Faces: lambda4_nu = 1.95e-12 (multiplier -207.46), L2(|Y|=2.5) = 6.49e-11 (multiplier -1.913), all other rows inside
  with |v| <= 7e-9: complementarity v*s = 4.0e-10 and 1.2e-10 <= mu, i.e. ON the central path, NLL gap ~5e-10.
- q = 2 (376.472642734532 - 336.9190862332205) = **79.10711** vs LAT's 79.10694: **dq = +1.74e-4** — exactly the
  under-minimisation estimated from LAT's frozen complementarity (~2e-4). p-value unchanged (0.02 %).
- Same minimum: max |dx| = 6.2e-5 (internal), largest |dx|/sigma_sat = 1.3e-4 (lambda4); alphaS differs by 1.8e-5 sigma
  (blinded difference only). Saturated `edmval` = 2.508 again although the fit is converged: it is the unconstrained EDM,
  dominated by the lambda4_nu face gradient — confirms reading 3 of the forensics.
- Time to q-to-go thresholds (vs C's final loss; LAT's plain sub-fit in brackets): q < 1 at 0.80 h (2.77 h), < 0.1 at
  1.65 h (9.82 h), < 0.01 at 2.25 h (10.63 h), < 0.001 at 2.45 h (11.17 h); LAT never got below 1.7e-4.

![C vs LAT sub-fit](subfit_progress_C_vs_LAT.png)

*Same problem, same start (LAT's minimum), same card/cache/SCETlib build/flags; only the rabbit branch and the
preconditioner flags differ. Node load differed somewhat (LAT ran next to NOLAT; C next to other users' jobs), but the
time per loss-or-HVP call is similar (9.4 s LAT, 10.5 s C), so the gain is in the counts.*

### 2026-10-16 08:55 — scope change; A and D stopped; C launched
- Orchestrator (Luca): drop the factorial; one real sub-fit C = both fixes; D only as fallback, ask first.
- Stopped my A = SATWS_LAT (pid 529319) and D = SATKP_LAT (pid 529414) with SIGTERM at 08:57 (snapshots written). What
  they had shown: A started at mu0 = 4.1e-10 (centred barrier = LAT's final barrier), iteration 1 took 480 s and reached
  loss 349.670 (LAT's own sub-fit: 349.692 at it 1, at mu 0.1) — no information on the plateau yet. D was still
  building its preconditioner Hessian. Nothing else from them; logs kept in [logs/](logs/).
- Both workers' tests on the combined branch (`tests/test_trust_constr.py` + `tests/test_trust_constr_warmstart.py`):
  **40 passed** in 400 s ([logs/pytest_wspc.log](logs/pytest_wspc.log)).
- 08:58 launched **C = SATWSPC_LAT** ([cmds/SATWSPC_LAT.inner.sh](cmds/SATWSPC_LAT.inner.sh)): LAT's flags (trust-constr,
  NPDomainConstraints margin=0, LatticeCSTerm tau 8, gtol 1e-8, xtol 1e-10, barrier_tol 1e-9, maxiter 600) +
  `--precondition --preconditionParams '.*' --preconditionBlocks none --preconditionTransform spectral`,
  `--minimizerWarmStart` at its default `auto` (= warm for the saturated sub-fit), `--externalPostfit fitresults_LAT.hdf5 --noFit`.
- NOLAT was stopped by Luca at 08:57:51 (34 s after my SIGTERM of A/D, which went only to pids 529319/529414); the
  SATPC_NOLAT launcher then refused to launch (no 'total time' line) — cancelled by the orchestrator.

### 2026-10-16 — forensics of the LAT / NOLAT trust-constr sub-fits (logs only, no cache load)

Parser [scripts/parse_tc_log.py](scripts/parse_tc_log.py) → [tc_legs.json](tc_legs.json) (per-iteration loss, dt,
optimality, barrier mu, trust radius; "rejected" = loss unchanged and radius shrunk). Counters from the scipy result
printed in the logs. HVP = Hessian-vector product = one projected-CG iteration (`cg_niter`); each one is a
`loss_val_grad_hessp` call. Time per HVP is node-load dependent, so counts are the like-for-like measure.

**Caveat before the numbers:** the trust-krylov references (SATB8, SATP; `constrained-fit-strategy/261008-saturated-subfit-diagnosis`)
ran a DIFFERENT configuration (card/cache the same, but relu² wall at tau 8 instead of hard constraints, TMD priors
pinned, LatticeCSTerm `syst=Jnf+Jbt offset=min`, start = the flat LATB8 seed; q = 78.40 there vs 79.11 here). They show
the cost of the same kind of sub-fit, not of this exact problem (the like-for-like trust-krylov run D was stopped after the scope change).

![sub-fit progress](subfit_progress_forensics.png)

*q still to go = 2(loss − final) vs wall time (left) and iteration (middle); dt per iteration (right). LAT/NOLAT:
trust-constr + hard constraints (this study). SATB8/SATP: trust-krylov + relu² wall, older config (see caveat). NOLAT
is still running and is measured against its best loss so far.*

| sub-fit | minimizer | iterations | nfev | HVPs (`cg_niter`/`nhev`) | wall | rejected steps (time) | status |
|---|---|---|---|---|---|---|---|
| LAT saturated ptll | trust-constr, no precond | 226 | 152 | **4667** | 12.57 h | 118 (37.5 %) | 2 (xtol), optimality 6.6e-4 |
| NOLAT saturated ptll | trust-constr, no precond | 199+ (running) | — | — | 14.3 h+ | 70+ | running |
| LAT main fit (cold!) | trust-constr | 113 | 75 | 1173 | 4.79 h | 63 (41 %) | 1 (gtol) |
| NOLAT main fit (cold) | trust-constr | 62 | 59 | 1107 | 7.38 h | 10 | 1 (gtol) |
| SATB8 (old config) | trust-krylov | 158 | 156 | 2150 | 5.82 h | 21 | converged |
| SATP (old config) | trust-krylov + spectral precond | 69 | 71 | 614 | 1.32 h (+306 s) | — | converged |

- t_HVP ≈ 8.9 s, t_f ≈ 24 s in the LAT sub-fit (152 t_f + 4667 t_HVP = 45242 s; the tail's rejected steps, ~1 fev +
  ~1 HVP each, take 27–37 s, consistent). So **~92 % of the sub-fit is HVPs**, as under trust-krylov (89–91 %).
- **The warm sub-fit costs 4× the HVPs of the cold main fit** (4667 vs 1173) and 2.2× SATB8's.

**Where the 12.57 h of the LAT sub-fit go** (barrier stage = one value of mu; [scratch_trace.txt](scratch_trace.txt)):

| phase | iterations | wall | share | what happens |
|---|---|---|---|---|
| mu = 0.1, descent to q-to-go < 1 | 1–25 | 2.77 h | 22 % | real progress: 79.1 → 1.0 |
| **mu = 0.1, plateau** | 26–101 | **6.55 h** | **52 %** | q-to-go 0.3–0.8, oscillating, no net progress after it ~50: a 3-step cycle (deep step: optimality jumps to 20–150; cheap step: back to 0.2–0.8; rejected step with a deep CG solve). The stage only ends when optimality < barrier_tol = 0.1 (it 101). |
| mu = 0.02 → 3.2e-5 | 102–125 | 2.48 h | 20 % | one deep CG solve per stage (773–1893 s) + cheap polish: q-to-go 0.48 → ~0 |
| mu ≤ 6.4e-6, certification tail | 126–225 | 0.78 h | 6 % | ~11 rejected steps per stage, x never moves again; ends at mu 4.1e-10 by xtol (tr_radius 1e-11) = status 2 |

NOLAT's sub-fit has the same anatomy: its mu = 0.1 stage is 81 iterations / 10.3 h = 75 % of its first 13.8 h, plateau
at q-to-go 0.15–0.7 from ~3 h to ~10 h. LAT's main fit spent only 29 iterations / 1.16 h at mu = 0.1 (from COLD), with
its own plateau-free descent, and its tail is the same rejected-step certification (it 67–113, 1.3 h).

**Reading.**
1. The plateau is the barrier-displaced optimum of the mu = 0.1 subproblem: at the end of each stage q-to-go is 0.48
   (mu 0.1), 0.11 (0.02), 0.017 (4e-3), 0.0032 (8e-4), 0.0005 (1.6e-4): Δloss ≈ 1.5–2.5 mu, i.e. the barrier gap of
   ~2 strongly pulled rows. Polishing that subproblem to optimality < 0.1 is useless work for the physics answer and
   costs half the sub-fit. scipy restarts the barrier at mu0 = 0.1 because rabbit's sub-fit is started like a cold fit
   (cause (b) of 261015-trustconstr-warmstart).
2. Why polishing it is so expensive here and not in the main fit: the sub-fit Hessian is the ill-conditioned one (39 free
   bin scales at curvature ~1e6, the curved alphaS valley at ~1e-2, kappa 1e9–1e10, 261008 study), and the optimality
   test is an inf-norm on the raw gradient. Each long step along the soft valley disturbs the stiff directions
   (optimality → 20–150), a short step repairs them (→ 0.2–0.8), and the next long step is rejected — a zig-zag that
   does not converge to < 0.1 for 75 iterations. The face pull adds a second stiff block: in the saturated model
   lambda4_nu runs to its face with multiplier 207, so at mu = 0.1 its barrier curvature is v²/mu ≈ 4e5, on a parameter
   that is part of the alphaS valley.
3. The final status 2 is a certification failure, not a wrong q: complementarity at the end is v·s = 207 × 3.3e-7 =
   6.9e-5 (lambda4_nu) and 1.9 × 9.3e-6 = 1.8e-5 (L2(2.5)), i.e. the iterate is frozen at the mu ≈ 3e-5 central-path
   point (it 125), and every later stage rejects all steps (the loss-noise trap (e) of 261015-trustconstr-warmstart).
   NLL excess ≈ Σ v·s ≈ 9e-5 → q low by ~2e-4 (estimate; A/D will measure it). The saved `edmval` 2.51 of the
   saturated fit is the UNconstrained EDM (it includes the face gradient 207 ∇c), so it is not a convergence measure.
4. Lattice: not a factor. LAT and NOLAT sub-fits share the anatomy (mu = 0.1 stage 74 % / 75 %); NOLAT is slower per
   iteration (more deep CG solves). NOLAT's own sub-fit (and SATPC_NOLAT) is the lattice-off comparison, so no extra
   lattice on/off run is needed.

**Launched (08:12):** A = SATWS_LAT (warm-start fix) and D = SATKP_LAT (trust-krylov + C² wall + spectral precond),
both from LAT's final result, commands [cmds/](cmds/), launch record [logs/launches.txt](logs/launches.txt).
- `--externalPostfit fitresults_LAT.hdf5 --noFit` without `--noHessian`: LAT's file carries a covariance, so rabbit
  loads it (`external_cov_loaded`) and does NOT recompute the main Hessian (bin/rabbit_fit.py `recompute_cov`); the
  sub-fit still computes its own Hessian at its end (its `cov`/`edmval`).
- `--blindingFrame` (196bfca) is absent from the branch worktrees, but `auto` = the old behaviour, so the blinded
  alphaS of all runs is in one frame (differences only).
- Prepared C: worktree `/work/submit/lavezzo/rabbit-satdiag-wspc`, branch `satdiag-ws-pc` = f84e0a8 + a606337
  cherry-picked (conflicts in `build_nonlinear_constraints`/`build_scipy_constraints` signatures resolved by keeping
  both `hold_feasible` and `transform`; committed `--no-verify` as 0395383, local only, pylint absent on the host).
  Tests: [logs/pytest_wspc.log](logs/pytest_wspc.log).

---

## Result

**Caveats first.** Real data, alphaS blinded (only differences quoted). One problem (LAT = CT18Z nominal, lattice on,
hard NP constraints) and one start (LAT's own minimum), one run per recipe: no scatter. The factorial was dropped (Luca,
08:55), so the warm-start fix and the preconditioner were tested TOGETHER only; their separate shares below are inferred
from the logs and the older trust-krylov study, not measured. The trust-krylov numbers (SATB8/SATP) come from an older
configuration (relu² wall, pinned TMD priors, other lattice settings; q = 78.40 there).

**1. Why the plain sub-fit is slow and does not converge (LAT, 12.57 h, 226 it, 4667 HVPs, status 2).**
- 92 % of the time is HVPs (t_HVP ≈ 8.9 s), as under trust-krylov. The warm sub-fit needs 4x the HVPs of LAT's own
  COLD main fit (1173).
- **Barrier restart (dominant):** scipy restarts the interior-point barrier at mu0 = 0.1 although the sub-fit starts at a
  minimum. That one stage is 74 % of the sub-fit (9.3 h): 2.8 h of real descent, then **6.6 h (52 %) on a plateau** at
  q-to-go 0.3–0.8 — the barrier-displaced optimum (Δloss ≈ 2 mu) — polishing it to optimality < 0.1 in a 3-step zig-zag
  (long step disturbs the stiff directions, short step repairs them, next long step rejected). The later stages
  (mu 0.02 → 3e-5) re-solve the problem with one deep CG solve each: 2.5 h (20 %).
- **Conditioning (amplifier):** the zig-zag and the deep solves are the ill-conditioning of the saturated model
  (39 free bin scales at curvature ~1e6 against the curved alphaS valley, kappa 1e9–1e10; lambda4_nu running to its face
  with multiplier 207 adds a barrier block of curvature v²/mu ≈ 4e5 at mu = 0.1).
- **Certification tail (6 %) and the false status 2:** after it 125 the iterate never moves (all steps rejected at the
  loss-noise floor); it stays at the mu ≈ 3e-5 central-path point (v·s = 6.9e-5 and 1.8e-5) and ends by xtol at
  optimality 6.6e-4. The q it reports is low by only 1.7e-4 (measured by C).
- **Lattice:** not a factor (NOLAT's sub-fit has the same anatomy, 75 % in the mu = 0.1 stage). **Wall vs hard
  constraints:** not tested separately (D dropped); the hard rows matter only through the barrier above.
- Consistent with the old trust-krylov study: there the preconditioner alone took SATB8's 2150 HVPs / 5.82 h to SATP's
  614 / 1.32 h (~3x at equal load). Plain trust-constr needed 2.2x SATB8's HVPs, which is roughly the cost of the
  mu = 0.1 plateau (~2400 HVPs).

**2. The fix: warm start (rabbit f84e0a8) + full-scope spectral preconditioner (a606337), together = PASS.**

| sub-fit from LAT's minimum | status | iterations | nfev | HVPs | minimiser | whole sub-fit pass | optimality | q | faces (multiplier) |
|---|---|---|---|---|---|---|---|---|---|
| LAT plain trust-constr | 2 (xtol), not converged | 226 | 152 | 4667 | 12.57 h | 12.82 h | 6.6e-4 | 79.10694 | lambda4_nu (−207.45), L2(2.5) (−1.91), off the central path |
| **C warm + precond** | **1 (gtol)** | **89** | **112** | **982** | **3.20 h** | **3.60 h** (+407 s precond Hessian) | **2.5e-9** | **79.10711** | lambda4_nu (−207.46), L2(2.5) (−1.91), on the central path |

Same minimum (max |dx| 1.3e-4 sigma; alphaS 1.8e-5 sigma), same faces and multipliers. **Physics read:** the
saturated-projection test of the LAT fit is q = 79.107 for 39 dof, p = 0.02 %: the CT18Z nominal does not describe the
ptll projection (linear chi2 92/39 agrees). LAT's own q (79.107 − 1.7e-4) was already right to far below the 0.01 that
matters; the plain sub-fit's "not converged" flag did not change the physics, only the time and the confidence.
The saturated `edmval` (2.5 in both) is the unconstrained EDM and is not a convergence measure at an active face; use
the minimizer status, optimality and the multipliers × slacks.

**3. Recommended sub-fit recipe:** trust-constr + `--constraints` with rabbit carrying both commits
(`--minimizerWarmStart auto`, the default on that branch) and `--precondition --preconditionParams '.*'
--preconditionBlocks none --preconditionTransform spectral` (warm fits only — the precondition worker showed it hurts a
COLD main fit). Combined branch: `satdiag-ws-pc` 0395383 in `/work/submit/lavezzo/rabbit-satdiag-wspc` (local, not
pushed; cherry-pick conflict resolved by keeping both `hold_feasible` and `transform`); both workers' tests pass on it
(40/40). For the NOLAT postfit: [cmds/NOLAT_PF.proposed.sh](cmds/NOLAT_PF.proposed.sh) (from
`snapshot_fitresults_NOLAT.hdf5`, its converged 17:35 main minimum, which has no covariance, so the main Hessian is
recomputed at the loaded point; `--noFit`; impacts + ptll saturated test; through mem_gate). It is still ~1.6x
SATP's HVP count (different config), so trust-krylov + C² wall + precond (D) remains the faster-in-principle fallback;
not run.

---

## Findings

1. Plain trust-constr restarts its barrier at mu0 = 0.1 even when started at a minimum; on the saturated ptll sub-fit
   that one stage is 74–75 % of the time (LAT/NOLAT), most of it polishing a barrier-displaced point. — (evidence: Log
   forensics, [tc_legs.json](tc_legs.json))
2. Warm start (f84e0a8) + full spectral preconditioner (a606337) together converge the same sub-fit to gtol in 89 it /
   982 HVPs / 3.2 h vs 226 it / 4667 HVPs / 12.6 h, same minimum, q +1.7e-4. — (evidence: [compare_SATWSPC_vs_LAT.json](compare_SATWSPC_vs_LAT.json))
3. A trust-constr status 2 at the end of a barrier ladder can be a frozen iterate: check v·s against the final barrier;
   LAT's sub-fit sat at v·s ~ 7e-5 for 100 iterations. — (evidence: LAT.log sub-fit result block; generalizes →
   `knowledge/20_frameworks/rabbit_minimizer_tolerances.md`)
4. The saved saturated-fit `edmval` is the unconstrained EDM: 2.51 at a gtol-converged constrained minimum with an active
   face of multiplier 207. Not a convergence measure under `--constraints`. — (evidence: C log `edmval: 2.508`;
   generalizes → `knowledge/20_frameworks/saturated_gof_tests.md` or the tolerances note)
5. `--externalPostfit <result with a covariance> --noFit` does NOT recompute the main Hessian (rabbit `recompute_cov`);
   only a covariance-less input (snapshot) triggers it. — (evidence: bin/rabbit_fit.py; C log has no postfit Hessian)

---

## Open questions

- Separate shares of the warm start and the preconditioner were not measured (factorial dropped). A (warm only) reached
  349.670 at its first iteration in 480 s before being stopped; nothing more.
- D (trust-krylov + C² wall + precond on this config) not run: whether it beats C's 982 HVPs here is open (SATP needed
  614 on the older config).
- C still has a 3-step zig-zag in its q-to-go 0.1→0.01 range (23 rejected steps, 32 % of its time): the stale-curvature
  tail seen in SATP; a mid-fit preconditioner rebuild could shorten it.
- The combined branch is local only; the two PRs (warm start, precond) need to be stacked/rebased for upstream.
