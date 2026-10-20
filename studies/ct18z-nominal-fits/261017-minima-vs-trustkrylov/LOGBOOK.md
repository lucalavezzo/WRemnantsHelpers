---
title: Are the cold trust-constr minima (LAT, NOLAT) the old trust-krylov + wall minima?
slug: 261017-minima-vs-trustkrylov
study: ct18z-nominal-fits
status: done          # active | done | paused | abandoned
created: 2026-10-17
updated: 2026-10-18
owner: study-worker
---

# Are the cold trust-constr minima (LAT, NOLAT) the old trust-krylov + wall minima?

**Task:** Are LAT and NOLAT (cold trust-constr + hard `NPDomainConstraints`, no NP priors) the same minima as the earlier trust-krylov + NP damping wall fits (LATFROZ_V3 / V2, XWSTIFF, NOMSTIFF / C2A) — same point, same basin shifted by the configuration change, or a different minimum?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-10-18) — DONE

- **Answer:** SAME BASIN; each new minimum is its old counterpart moved only by removing the NP priors. LAT =
  LATFROZ_V3 (= V2) minus the TMD priors; NOLAT = XWSTIFF minus the five NP priors. Warm rabbit refits in the new
  objectives, seeded at the old minima, land ON the cold minima (LAT to 2e-8σ, NOLAT to 5e-6σ). rabbit's start losses
  equal the offline cross-evaluations to all printed digits. Δα_s −0.017σ (LAT − V3), +0.017σ (NOLAT − XWSTIFF).
  NOMSTIFF/C2A solve a different objective, so they have a different minimum, via the known chain.
- **Next action:** none — task closed.
- **Blocking on:** nothing.
- **Running:** nothing (LATatV3 exit 0 at 23:50, NOLATatXW exit 0 at 21:30).

---

## Log

### 2026-10-17
- Read: study LOGBOOK, 261015-cold-tc-fits Result, LATFROZ (lattice-cs-kernel/261008-latfroz-nf-variants), V2
  (trust-constr-nominal/261013-constraints-class-validation), XWSTIFF/NOMSTIFF (walled-multistart-census/260930-stiff-wall-refits),
  NOMTMDFREE (…/261005-tmd-priors-free), CMR1B (…/261005-cold-min-restart), C2A (constrained-fit-strategy/261008-c2-wall-test).
- Exact commands of every fit from their `meta_info` ([logs/dump_meta.log](logs/dump_meta.log), [scripts/dump_meta.py](scripts/dump_meta.py)).
  All the card-A fits (LAT, NOLAT, V3, V2, XWSTIFF, CMR1B) have the same 3720-parameter list (47 model params incl.
  `resumFOScaleEnvSymAvg/Diff`); NOMSTIFF / C2A / NOMTMDFREE have 3719 (λ4_ν frozen) on the lattice card
  `cardA_latticeASWZ_l4zero_statsyst`.
- Converged snapshots = fitresult `parms` bit for bit (checked for LAT, V3, XWSTIFF) → used as x-only seeds.
- 10:56 launched LATatV3 and NOLATatXW through mem_gate (commands in [logs/launches.txt](logs/launches.txt), scripts
  [scripts/LATatV3.inner.sh](scripts/LATatV3.inner.sh), [scripts/NOLATatXW.inner.sh](scripts/NOLATatXW.inner.sh)): the new
  objective (LAT / NOLAT args from 261015 launches.txt, minus the postfit extras, + `--noHessian --noEDM`), rabbit
  worktree `rabbit-all3` (all3-local d573c1d: warm start + spectral preconditioner), `--externalPostfit` = old snapshot.
  The first logged `trust-constr start loss` IS the cross-evaluation; the end point says whether a warm refit returns
  to the new minimum. Still queued at 11:50.
- Offline (cache-free) analysis [scripts/compare_minima.py](scripts/compare_minima.py) → [compare_minima.json](compare_minima.json),
  [logs/compare_minima.log](logs/compare_minima.log): NLL split per fit, physical λ, constraint rows, the new objectives
  evaluated at the old points, the old objectives at the new points, and a one-step Newton prediction old → new.
  Figure [scripts/plot_newton.py](scripts/plot_newton.py). Result below.
- 21:30 **NOLATatXW DONE** (gate wait 10 h; 740 s init, 1674 s fit, exit 0; [logs/NOLATatXW.log](logs/NOLATatXW.log)).
  rabbit's `trust-constr start loss = 369.7209821630` = the offline F_NOLAT(x_XWSTIFF) 369.7209821630219 to all printed
  digits → the cache-free data+BB split is exact across the code revisions (XWSTIFF: full cache, Sept code). The warm
  refit (warm start, barrier 1e-9, preconditioned) went 369.72098 → 369.71877 (it 1) → 369.7186971 (it 3–4), then the
  xtol tail; status 2, optimality 1.4e-6, 30 it. End point vs cold NOLAT ([scripts/compare_refit.py](scripts/compare_refit.py),
  [logs/compare_refit_NOLATatXW.log](logs/compare_refit_NOLATatXW.log)): ΔNLL −1.5e-8, max |Δθ/σ| 4.8e-6 (λ2), Δα_s
  −2.3e-6σ, max |Δθ| 2.7e-6, λ2_ν on its face (multiplier −32.45 vs NOLAT −32.4). **Same point.**
- 23:50 **LATatV3 DONE** (655 s init, 2446 s fit, exit 0; [logs/LATatV3.log](logs/LATatV3.log)). `trust-constr start loss =
  376.4748904804` = offline F_LAT(x_V3) 376.47489048039694. Warm refit: 376.47489 → 376.47286 (it 1) → 376.4726428
  (it 3), then the xtol tail; status 2, optimality 1.1e-8, 33 it, one active face L2(|Y|=2.5) with multiplier −6.41 (LAT:
  −6.41). End vs cold LAT (face-held cov, [logs/compare_refit_LATatV3.log](logs/compare_refit_LATatV3.log)): ΔNLL −7e-10,
  max |Δθ/σ| 2.1e-8, Δα_s −2.9e-9σ, max |Δθ| 1.3e-8. **Same point.**

---

## Result

**Caveats first.**
- Real data, `alphaS` BLINDED: every fit here is a reco fit on card A's integer data (blinding frame `auto` → data,
  same per-name offset `sha256(name + "_data")` in all rabbit versions used; none used `--blindingFrame`). Only
  differences are quoted, in σ of the new fit (face-held covariance for LAT/NOLAT; old fit's walled covariance in
  brackets). No absolute α_s or offset was computed.
- The objectives DIFFER, so the NLLs are not directly comparable. "Same minimum" is tested as: (i) the NEW objective at
  the OLD point (and vice versa) — if the old point were lower in the new objective, the new fit missed it; (ii) a
  one-step Newton prediction from the old minimum to the new objective (old NP priors subtracted, the old fit's walled
  Hessian kept, so its active faces stay held), compared with the actual new minimum over all 3720 parameters.
- These cross-evaluations are cache-free: data+BB at each point = stored NLL − wall − lattice − card constraints −
  ParamModel priors (each recomputed at the stored x with that fit's own settings: relu² wall for the pre-C² fits, C²
  δ=1e-3 for C2A; frozen V3 `LatticeCSTerm`; the 1D card term for NOMSTIFF/C2A). That assumes the data+BB part is the
  same function of x across the WRemnants/rabbit revisions involved. Supporting evidence: LAT's cold start loss equals
  V2's to all digits (114396.0578614644), V2 reproduces V3 to 1.6e-6 net of the wall, and the |Y| ≤ 2.5 subset cache
  equals the full one (261008 PG task). **Checked directly in rabbit**: its start loss at XWSTIFF's
  point and at V3's point equals the offline value to all 10 printed decimals (NOLATatXW, LATatV3).
- XWSTIFF ran on the full `merged_full_bin0xzero` cache, the rest on its |Y| ≤ 2.5 subset (identical predictions).

**What differs between old and new (from the fitresults' meta_info).**

| | LAT | LATFROZ_V3 | V2 | NOLAT | XWSTIFF | NOMSTIFF / C2A |
|---|---|---|---|---|---|---|
| card | A | A | A | A | A | A + 1D lattice external term |
| lattice | frozen native (V3 = default) | same, explicit args | same | none | none | 1D Gaussian card term |
| NP region | hard `NPDomainConstraints` m=0 | relu² wall τ=8 m=0 | hard | hard | relu² wall τ=8 m=0 | relu² (C2A: C², δ 1e-3) |
| NP priors (σ on θ) | none | TMD 1 | TMD 1 | none | TMD 1 + CS 1 | TMD 1 |
| λ4_ν | free | free | free | free | free | frozen 0 |
| minimiser / start | trust-constr, cold | trust-krylov, warm (LATB8) | trust-constr, cold | trust-constr, cold | trust-krylov, warm | trust-krylov, warm |
| cache | y25 subset | y25 | y25 | y25 | full | full (C2A y25) |

**Results, LAT side** ([compare_minima.json](compare_minima.json) `pairs`):

| | LAT | LATFROZ_V3 | V2 |
|---|---|---|---|
| NLL (own objective) | 376.4726427 | 376.9370397 | 376.9370405 |
| = data+BB / card / 41 priors / NP priors / lattice / wall | 353.9212 / 14.8372 / 3.1801 / 0 / 4.5342 / 0 | 353.8407 / 14.8540 / 3.1866 / 0.4622 / 4.5936 / 7.9e-7 | 353.8407 / 14.8540 / 3.1866 / 0.4622 / 4.5936 / 0 |
| λ2 / λ4 / δλ2 | 0.04551 / 0.07196 / −0.00728 | 0.04815 / 0.07256 / −0.00770 | same as V3 |
| λ2_ν / λ4_ν | 0.03950 / 0.01051 | 0.03829 / 0.01063 | same as V3 |
| active face | L2(\|Y\|=2.5) (6e-11) | L2(\|Y\|=2.5), 3.0e-7 PAST it (relu² overshoot) | L2(\|Y\|=2.5) (1.9e-9) |
| **LAT objective at this point** | 376.4726427 | **376.4748905 (+0.00225)** | 376.4748924 (+0.00225) |
| old (V3) objective at LAT's point − V3 min | | +0.00226 | |
| Δα_s (LAT − old) / σ_LAT [σ_old] | | **−0.0175** [−0.0174] | −0.0175 |
| σ(α_s) ratio LAT / old | | 0.9985 | (V3 cov) |
| max \|Δθ\| ; max \|Δθ/σ\| (3720 params) | | 0.0139 (pdfEig14); 0.057 (λ2, δλ2) | same |
| params moving > 0.01σ / > 0.1σ | | 9 / 0 | |
| Newton from V3: predicted NLL; ‖actual − pred‖/σ | | 376.4726372 (actual −5.5e-6 above); 3.4e-4 (of ‖Δ‖ = 0.106) | |
| **rabbit warm refit in LAT's objective from this point** | | **start 376.4748904804 (= offline); ends ON LAT: ΔNLL −7e-10, max \|Δθ/σ\| 2e-8** | |

**Results, NOLAT side:**

| | NOLAT | XWSTIFF | CMR1B (2nd Z-only minimum) |
|---|---|---|---|
| NLL (own objective) | 369.7186971 | 371.3283652 | 371.9980462 |
| = data+BB / card / 41 priors / NP priors / wall | 352.5205 / 14.2545 / 2.9437 / 0 / 0 | 352.5684 / 14.2323 / 2.9203 / 1.6074 / 1.2e-5 | 352.0842 / 14.9382 / 3.2664 / 1.4696 / 0.2397 |
| λ2 / λ4 / δλ2 | 0.11474 / −0.00006 / −0.00938 | 0.11883 / −0.00007 / −0.00941 | 0.0933 / 0.1204 / −0.0093 |
| λ2_ν / λ4_ν | 0 (face) / 0.04484 | −1.1e-6 (face) / 0.04441 | −2e-7 / **−0.00016** |
| active faces | λ2_ν ≥ 0; cubic(\|Y\|=2.5) | the same two, 1.1e-6 / 2.0e-7 PAST them | λ2_ν ≥ 0, λ4_ν ≥ 0 (violated by 1.6e-4) |
| **NOLAT objective at this point** | 369.7186971 | **369.7209822 (+0.00229)** | 370.2887 (+0.570) |
| old objective at NOLAT's point − old min | | +0.00237 | −0.667 (XWSTIFF's basin is lower) |
| Δα_s (NOLAT − old) / σ_NOLAT [σ_old] | | **+0.0168** [+0.0168] | −0.349 [−0.316] |
| σ(α_s) ratio NOLAT / old | | 1.0001 | 0.907 |
| max \|Δθ\| ; max \|Δθ/σ\| | | 0.041 (b_qg); 0.068 (λ2) | 0.24 (λ4); λ4 hundreds of σ |
| params moving > 0.01σ / > 0.1σ | | 13 / 0 | 109 / 11 |
| Newton from old: predicted NLL; ‖actual − pred‖/σ | | 369.7186617; 8.3e-3 (of 0.124) | 370.2867 (stays in its own basin) |
| **rabbit warm refit in NOLAT's objective from this point** | | **start 369.7209821630 (= offline); ends ON NOLAT: ΔNLL −1.5e-8, max \|Δθ/σ\| 4.8e-6** | not run |

![Actual shift vs one-step Newton prediction, all 3720 parameters](newton_vs_actual_shift.png)

*Real data, blinded (α_s only as a difference). x: the Newton step from the old minimum with the old NP priors removed
and the old walled Hessian (faces held); y: the actual new − old. Every one of the 3720 parameters sits on the diagonal.
The one visible off-diagonal point (λ2_ν, right) is the relu² overshoot: XWSTIFF sits 1.1e-6 past the λ2_ν ≥ 0 face, the
Newton point 1.8e-6 past it, NOLAT exactly on it — 1e-6 in λ2_ν.*

**Verdicts.**
1. **LAT vs LATFROZ_V3 / V2: same basin, shifted by the TMD-prior removal.** In LAT's own objective V3's point is
   0.00225 HIGHER than LAT (and LAT's point is 0.00226 higher in V3's objective): each is the minimum of its own
   objective, and nothing lower was missed. A warm trust-constr refit in LAT's objective from V3's point returns to
   LAT to 2e-8σ. The whole shift (‖Δθ/σ‖ = 0.106, largest λ2/δλ2 at 0.057σ along the
   held L2(|Y|=2.5) face) is predicted by one Newton step to 3.4e-4σ and the NLL to 5.5e-6. Same single active face.
   The other changes (hard constraints vs stiff relu² wall, trust-constr vs trust-krylov, cold vs warm, rabbit/
   WRemnants revisions) contribute nothing visible: V2 already showed the wall → constraints swap is worth 1.6e-6 in
   NLL and 1e-6σ in α_s. V3's point violates the hard L2(|Y|=2.5) row by 3.0e-7 (the relu² overshoot).
2. **NOLAT vs XWSTIFF: same basin, shifted by removing the five NP priors.** The new objective at XWSTIFF's point is
   +0.00229 above NOLAT; Newton from XWSTIFF predicts NOLAT to 8e-3σ (norm over 3720 params) and its NLL to 3.5e-5
   (≈ the relu² overshoot term: the Newton point keeps XWSTIFF's 1.8e-6 overshoot of the λ2_ν face, multiplier 32.4).
   Same two active faces (λ2_ν = 0, TMD cubic at |Y| = 2.5). The CS priors do no work there (λ2_ν is on its face, so
   its prior force is absorbed by the multiplier); the TMD λ2 moves by −0.0041 (−0.068σ). XWSTIFF's point violates the
   hard rows by 1.1e-6 (λ2_ν) and 2.0e-7 (cubic). A warm refit in NOLAT's objective from XWSTIFF's point returns to
   NOLAT to 5e-6σ (ΔNLL −1.5e-8). NOLAT is NOT the second known Z-only minimum CMR1B: that one sits
   +0.570 higher in NOLAT's objective, violates λ4_ν ≥ 0, and its basin stays there under the Newton step — so the cold
   NOLAT fit found the lower basin, the one used as the Z-only reference of the 261008 PG tension.
3. **LAT vs NOMSTIFF / C2A (and NOMTMDFREE): a different minimum, because a different objective** (1D Gaussian card
   lattice term, λ4_ν frozen at 0). Neither contains the other: LAT's objective at NOMSTIFF's point is +4.24 (of which
   the native lattice term +2.56, data+BB +0.99), NOMSTIFF's objective at LAT's point (λ4_ν dropped to 0) +0.41. The
   α_s shift LAT − NOMSTIFF = −0.159σ_LAT (−0.156σ_NOMSTIFF) is the known chain: NOMSTIFF → LATB8 (native live term,
   λ4_ν free) −0.113, → LATFROZ_V3 (frozen kernel) −0.026, → LAT (TMD priors off) −0.017 σ_NOM. C2A = NOMSTIFF (to 1e-6).

**Physics read.** The cold trust-constr fits reproduce the old trust-krylov + wall minima; nothing concluded from the
old fits changes. The only physical difference is the deliberate removal of the NP priors, and its effect is the one
261005-tmd-priors-free measured in the NOMSTIFF configuration (−0.020σ there, −0.017σ here; the TMD priors were
≥ 12× looser than the data). The Z–lattice tension is unchanged: 2(NLL_LAT − NLL_NOLAT) = 13.51 vs the 261008 PG of
13.48 (V3 vs XWSTIFF with its ν priors removed by a Newton step) — the 0.03 is the TMD-prior removal and the Newton
estimate of the ν-prior removal. The NP picture is the same: with the lattice, CS kernel on the lattice side
(λ2_ν 0.039, λ4_ν 0.011) and the TMD small-b term on its |Y| = 2.5 face; without it, λ2_ν on its bound and the TMD
large-b cubic on its |Y| = 2.5 face.

---

## Findings

1. LAT ≡ LATFROZ_V3 / V2 basin; LAT − V3 = the TMD-prior removal (Newton-exact to 3.4e-4σ; Δα_s −0.017σ). — (evidence:
   [compare_minima.json](compare_minima.json), [newton_vs_actual_shift.png](newton_vs_actual_shift.png))
2. NOLAT ≡ XWSTIFF basin; NOLAT − XWSTIFF = the five-NP-prior removal (Newton to 8e-3σ; Δα_s +0.017σ); not CMR1B
   (+0.57 higher in NOLAT's objective). — (same)
3. The cache-free NLL split (data+BB = NLL − wall − lattice − card − priors, each recomputed at the stored x) evaluates
   a new objective at an old fit's point exactly: rabbit's start loss agreed to 1e-10 for both pairs, across the
   Sept/Oct WRemnants + rabbit revisions and the full vs |Y| ≤ 2.5 cache. — (evidence: logs/LATatV3.log, logs/NOLATatXW.log)
4. Removing priors from a walled/constrained minimum is predicted by one Newton step with the old walled Hessian to
   ≤ 1e-2σ: no refit is needed to know where a prior-free fit lands (generalises 261005-tmd-priors-free). — (same)

---

## Open questions

- None for the question asked. Side note: both warm refits stopped with status 2 (xtol) and a ~30-iteration
  rejected-step tail after converging in 3–4 iterations, the same tail as the cold fits (261015-cold-tc-fits).
