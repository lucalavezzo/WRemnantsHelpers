---
title: C2 wall test on real fits
slug: 261008-c2-wall-test
study: constrained-fit-strategy
status: done          # active | done | paused | abandoned
created: 2026-10-08
updated: 2026-10-08
owner: study-worker
---

# C2 wall test on real fits

**Task:** Does a C² (curvature-continuous) NP damping wall remove the trust-krylov crawl on REAL fits (main fit from the CENS03R mid-crawl snapshot, and the LATB8 projected-ptll saturated sub-fit), and should it become the default (dropping option (a), rabbit-internal τ-continuation)?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-10-08 17:30, orchestrator; DONE)

- **Main fit: C² removes the crawl.** From the CENS03R mid-crawl snapshot, C2A reaches NOMSTIFF + 1e-6 in 46 it / 1.11 h.
  relu² from the same point (R2A) stays at +430 (stopped after 1.69 h). C2A lands on NOMSTIFF: Δα_s +3.9e-6σ,
  ‖Δθ/σ‖ 3.3e-5, ΔNLL −1.86e-5 (predicted), and the L2 face sits at −2.4e-6 GeV² (overshoot 7.6e-4 of the NP exponent).
- **Saturated sub-fit: C² does NOT reduce iterations.** SATC2 takes 157 it / 3.49 h to −1e-6 (4.26 h total), against SATB8's
  153 it / 4.86 h (6.0 h). Same path iteration for iteration, same q = 78.4/39, final loss −4.9e-6 (the C² offset). The
  wall-time gain (11 vs 16 long steps) is partly node load. The sub-fit's cost is not the wall: see
  [../261008-saturated-subfit-diagnosis](../261008-saturated-subfit-diagnosis/LOGBOOK.md).
- **Decided (Luca, 2026-10-08):** `smooth=c2` is now the NPDampingWall default, WRemnants 692f9483 (pushed); τ-continuation
  is opt-in, WRemnantsHelpers 3c0a9fb. Option (a), rabbit-internal τ-continuation, is dropped.
---

## Log

### 2026-10-08
- **15:30 SATC2 finished (orchestrator).** Results `/ceph/.../261008_c2_wall_test/fitresults_SATC2.hdf5`. analyze.py: 161 rows,
  0 restarts, 157 it / 3.49 h to final − 1e-6, 11 steps with dt ≥ 300 s, final 337.4761572066 (SATB8 337.4761620581,
  Δ = −4.9e-6). Projected ptll q = 78.4/39 (p 0.02 %), full saturated 753.35/777, both identical to SATB8. Physics read:
  C² changes nothing in the saturated answer. It does not change the sub-fit's iteration path either, so the sub-fit's
  slowness is intrinsic to the saturated problem.
- **11:40 C2A finished (orchestrator).** Results in `/ceph/.../261008_c2_wall_test/fitresults_C2A.hdf5`; fit 6873 s, init
  942 s, 60 iterations, 0 restarts.

  | check | predicted | C2A |
  |---|---|---|
  | ΔNLL vs NOMSTIFF | −1.9e-5 | −1.86e-5 |
  | Δα_s | ~5e-6σ | +3.9e-6σ |
  | ‖Δθ/σ‖ (max) | ≲1e-2 | 3.3e-5 (2.6e-5) |
  | σ(α_s) ratio | 1 | 0.9999998 |
  | EDM | — | 5.2e-15 (NOMSTIFF 3.0e-14) |
  | L2(\|Y\|=2.5) | −2.40e-6 GeV² | −2.401e-6 GeV² (normalised −7.6e-4); NOMSTIFF −9.15e-7 |
  | full saturated | 753.23/778 | 753.23/778, p 73.2 % |

  analyze.py, to NOMSTIFF + 1e-6: C2A 46 it / 1.11 h; R2A never (stopped at +430 after 219 it / 1.69 h); CENS03R never
  (260 it / 4.5 h). **Physics read:** C² changes the minimiser's path, not the answer. The C² equilibrium shifts the
  active face by 1.5e-6 GeV², and the active-face slope maps that to 4e-6σ in α_s, which is what we see. The condition is
  held at the wall (overshoot 7.6e-4 of the NP exponent at b_max, within the 1e-3 tolerance), with no margin.
- 11:14 R2A stopped early (Luca), overriding the declared stop rule. Snapshot `snapshot_fitresults_R2A.hdf5` kept.
  SATC2 launched from the freed slot (gate 726093 → PID 942052).
- **09:43 both fits start minimising** after a slow cache load: 28 min, two 100 GB rule files read from ceph at once.
  SUBY25 took 35 s, with a warm page cache. **Iteration 0 loss = 806.5778129128407 in both, bit-identical to
  CENS03R's last logged loss.** So the subset cache plus the pinned priors reproduce CENS03R's objective exactly, and
  the C² penalty is 0 at the start, which sits on the slack side of L2(2.5). The C² wall armed on 5 conditions (λ4_ν is
  frozen at 0 and dropped as constant), with the widths of the table below.
  - At ~10 min, C2A was at it. 15, −0.029; R2A at it. 24, −0.0017.
- **10:09 interim** (`scripts/analyze.py` → [analysis.json](analysis.json)).
  - C2A: it. 34 at 377.0311007872, 2174 s fit wall time. Its descent was 806.55 (it. 16) → 777.5 (it. 25) → 465.2
    (it. 30) → 377.03 (it. 34); the steps were large and accepted, i.e. the radius grew.
  - R2A: it. 93 at 806.5681447047, 2231 s.
  - Gain-ratio fractions near 1 / near 2: C2A 0.04 / 0.69, R2A 0.45 / 0.00, CENS03R (historical) 0.13 / 0.45.
  - R2A is the frozen period-2 lock of Diagnosis 2. CENS03R's own log looked like the period-7 sawtooth instead, so
    the same point under relu² shows either form of the crawl.
  - CPU (utime + stime): C2A 2.90e5 s, R2A 2.90e5 s at 10:09. Equal CPU and equal wall time, but C2A is ~430 NLL
    further on.
- **09:15 launched C2A and R2A** through `mem_gate.sh 260` (both got load slots; avail 1364 GB, 0 then 1 of 2
  alive). Commands built by [scripts/build_cmds.py](scripts/build_cmds.py) from NOMSTIFF's own meta_info command
  ([cmds/C2A.cmd](cmds/C2A.cmd), [cmds/R2A.cmd](cmds/R2A.cmd), diff in [logs/build_cmds.log](logs/build_cmds.log)).
  Changes vs NOMSTIFF: subset cache `pdf62_y35_260921_y25` (bit-identical NOMSTIFF replay, SUBY25);
  `--externalPostfit snapshot_fitresults_CENS03R.hdf5`; τ = 8 directly; TMD priors pinned
  (`prior_sigmas=lambda2_nu=nan,lambda2=1,lambda4=1,delta_lambda2=1`); `--earlyStopping 20` (was 100); snapshots to
  this task's ceph dir. C2A only: `NPDampingMapping margin=0 smooth=c2 delta=1e-3`. SCETlib: in-tree 2dd978a
  (`agent_setup.sh --scetlib current`), the build NOMSTIFF and CENS03R ran on. Out dir
  `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261008_c2_wall_test/`.
- **Why R2A is run (and not CENS03R's log used as the control).** CENS03R's log ends exactly where its snapshot was
  taken, so it says nothing about what relu² does *from* that point. The surrogate predicts that relu² from the CENS03R
  point converges, slowly (238–265 evaluations, not a lock-in; `261006-diagnosis/followup_table.md`). Without R2A, a
  C2A success could not be told apart from "the crawl was about to end anyway". CENS03R also ran on the full cache with
  `--earlyStopping 15 --stallRelTol 1e-11 --maxRestarts 0`, and three days earlier on a differently loaded node. Run
  side by side, C2A and R2A share node load, so their wall and CPU times compare directly.
- Reference numbers ([ref.json](ref.json), `scripts/build_cmds.py`): NOMSTIFF loss 376.6146329237086, EDM 3.0e-14,
  σ(`alphaS`) = 0.5823 (in θ). CENS03R snapshot (`reason: signal-SIGTERM`): Δ`alphaS` = −0.175σ against NOMSTIFF,
  ‖Δθ/σ‖ = 29.3, last logged loss 806.5778 (+430). The point sits on the L2(|Y|=2.5) face, like NOMSTIFF.
- **C² wall implemented** (WRemnants 2f1c3df4, `np_damping_wall.py`). It is opt-in: `smooth=c2 [delta=] [bmax=]` on the
  `NPDampingMapping` line. The default `smooth=relu2` is unchanged, checked bitwise.
  - With x = bound − coeff, P = x³/(3d) for 0 < x < d and x² − dx + d²/3 for x ≥ d; it is written branch-free as
    clip(x,0,d)³/(3d) + y² + dy, with y = relu(x − d).
  - Every `Condition` now carries a `scale`, the NP exponent per unit of coeff at b_T = b_max. The raw width is
    d = delta / scale, with:
    - λ2_ν: b²;
    - λ4_ν: b⁴;
    - λ6_ν: b⁶;
    - λ_inf_ν: 1;
    - L2: 2b²;
    - the cubic 3λ∞²λ4 + L2³: 2b⁴/(3λ∞²), with λ∞ at its held anchor;
    - λ6: 2b⁶;
    - λ_inf: 2b.
  - The tanh_6 interior discriminants have no constant scale, so `smooth=c2` refuses them (NotImplementedError).
  - At the printed arm time the wall lists each active condition's width and its maximum extra overshoot.
  - Test: `WRemnants/scripts/tests/test_np_damping_wall_c2.py`, 78 PASS, 0 FAIL. It covers:
    - value, slope and curvature continuity at 0 and d, both analytically and by one-sided FD;
    - TF P′ and P″ against the analytic forms;
    - the per-face widths;
    - the full wall through the `-r` parse path: penalty against a numpy reference, gradient against central FD,
      HVP against FD of the gradient (worst relative errors 1e-7 and 3e-7);
    - the default against the old relu² sum, bitwise;
    - the 1D equilibrium;
    - the refusals.
  - Lint: container black, isort and flake8 (88 columns) are clean. Committed inside the container, so the pylint hook
    ran.

#### δ choice: δ̃ = 1e-3 in the NP exponent at b_max = 12.6 GeV⁻¹

| face | scale s (per unit) | raw width d | max extra overshoot d/2 | today's relu² leak at τ = 8 |
|---|---|---|---|---|
| L2(\|Y\|=0, 2.5) ≥ 0 [GeV²] | 2b² = 317.5 | 3.15e-6 GeV² | 1.57e-6 GeV² = 5e-4 in ln F at b_max; ≈ 8e-6 at the peak b ≈ 1.9 (×5.1) | 9.2e-7 GeV² (NOMSTIFF) |
| λ2_ν ≥ 0 [GeV²] | b² = 158.8 | 6.30e-6 GeV² | 3.15e-6 GeV², i.e. \|Δγ_ν\| ≤ 5e-4 at b_max | 7.4e-7–1.1e-6 (XL4Z, XW) |
| 3λ∞²λ4 + L2³ ≥ 0 [GeV⁶] | (2/3)b⁴ = 1.68e4 | 5.95e-8 GeV⁶ | 2.98e-8 GeV⁶ = 5e-4 in ln F at b_max | 2.0e-7 (XW B(2.5)) |
| λ4_ν ≥ 0 [GeV⁴] | b⁴ = 2.52e4 | 3.97e-8 GeV⁴ | 1.98e-8 GeV⁴, i.e. \|Δγ_ν\| ≤ 5e-4 at b_max | — (frozen in the nominal) |

- **Why 1e-3.**
  - The ramp has to be wide compared with the crawl's face-crossing step. The frozen radius gives a crossing of
    Δx ~ g/(2k) ≈ 9e-7 GeV² on L2(2.5). With d = 3.15e-6 a crossing costs kΔx³/(3d), about 10 % of relu²'s kΔx². That
    is well below the ~30 % that kept ρ < 0.75 in the lock-in.
  - It must also stay inside the physical tolerance that 261006-diagnosis proposes, max |c̃| ≤ 1e-3 in the exponent at
    b_max. With δ̃ = 1e-3 the worst case is 5e-4 + today's ≤ 3e-4.
  - The surrogate's raw d = 1e-6 and 1e-5 on L2 (both lock-in-free from all 6 starts) bracket 3.15e-6.
  - A single raw d is not an option: 1e-5 on the cubic face would leak ~0.05 in ln F at b_max.
- **Expected overshoot at NOMSTIFF's face** (data force g = 16.3, k = e¹⁶ = 8.9e6).
  - kd = 28 > g, so the equilibrium is inside the ramp: v = √(gd/k) = 2.40e-6 GeV², against 9.2e-7 for relu².
  - That is 7.6e-4 in ln F at b_max (relu²: 2.9e-4), or ≈ 1.2e-5 at b ≈ 1.9 (relu²: 4.7e-6).
  - Expected loss shift at the minimum: −(2/3)g·v − (−g²/4k) ≈ −2.6e-5 + 7.5e-6 = **−1.9e-5 (C² below relu²)**. This is
    the "δ/2 overshoot difference" to allow for in the ΔNLL ≤ 1e-4 success test. It is well inside the tolerance.

## Result

Caveats first: real data; α_s blinded (differences in σ only); C2A and R2A start from the CENS03R mid-crawl
snapshot (CENS03R's own log ends at that snapshot), and C2A and R2A run side by side on the same node and subset cache. SATC2 and SATB8 run on different
days, so their wall times carry node-load differences.

| run | wall | outcome |
|---|---|---|
| C2A | C² | NOMSTIFF + 1e-6 in 46 it / 1.11 h; Δα_s +3.9e-6σ, ‖Δθ/σ‖ 3.3e-5, ΔNLL −1.86e-5 (predicted) |
| R2A | relu² | +430 after 219 it / 1.69 h (stopped) |
| CENS03R | relu² | +430 after 260 it / 4.5 h (killed) |
| SATC2 | C² | 157 it / 3.49 h to −1e-6, q 78.4/39 |
| SATB8 | relu² | 153 it / 4.86 h to −1e-6, q 78.4/39 |

Physics read: C² changes the minimiser's path, not the answer. The face shifts by 1.5e-6 GeV², worth 4e-6σ in α_s through
the active-face slope. The condition is held at the wall with no margin (overshoot 7.6e-4 of the NP exponent at b_max).

---

## Findings

1. The C² ramp removes the trust-krylov crawl at a relu² wall face and reaches the same minimum (evidence: compare_points.json, analysis.json).
2. The saturated sub-fit's iteration path is unchanged by C², so its slowness is not the wall (evidence: analysis.json; see ../261008-saturated-subfit-diagnosis).

---

## Open questions

- C² from a fully cold start was not tested; the evidence is one mid-crawl snapshot.
