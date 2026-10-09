---
title: Rapidity dependence of the TMD NP model
slug: tmd-rapidity-shape
status: done          # active | paused | done | abandoned
created: 2026-10-07
updated: 2026-10-08
---

# Rapidity dependence of the TMD NP model — logbook

**Goal (Luca, 2026-10-07):** a small study of whether anything can be learned about the rapidity dependence of the TMD NP
function, L2(Y) = λ2 + δλ2·Y², from our fits. Is the Y² form adequate? How much does `alphaS` depend on it? Is a Y⁴ term (or
an x-dependent form) worth adding? Done when we can say how sensitive `alphaS` is to the forward shape, and whether a more
flexible form is warranted.

**Why:** in the nominal fits (NOMSTIFF, and the lattice-χ² fit LATB8) the ONLY active wall face is L2(|Y| = 2.5) = 0, the
edge of the Y² extrapolation. Our fitted δλ2 ≈ −0.004…−0.008 GeV², while the AN tune uses ΔΛ2 = +0.125 ± 0.02 GeV²
(theory.tex l. 297). The AN itself calls the Y-dependence an "effective flavour-averaged model", pending x/flavour
dependence (theory.tex l. 254). Theory reading: Y² is the leading term of an expansion in ln x (x_{a,b} = Q/√s·e^{±Y}).

---

## START HERE (status as of 2026-10-08)

> **T1 done: the Y² shape is adequate; `alphaS` is sensitive to the forward L2 LEVEL (the wall floor), not the Y shape.** See [261007-y-shape-first-look](261007-y-shape-first-look/LOGBOOK.md).

- **Next action:** none. CLOSED 2026-10-08 (Luca). Carried forward: the `alphaS` sensitivity to the forward TMD level L2(2.5) floor (raising it to MAP22's value: −0.17σ_NOM; the +0.32σ full release is orientation only, at an unphysical point), as a systematic question for the nominal.
- **Blocking on:** nothing.

---

## Log

### 2026-10-08
- Closed (Luca). SUMMARY.md + PDF written; knowledge promoted (np_parametrization_constraints §16d,
  cache-format note, new active_wall_face_sensitivity.md). Wording fixed per the summarizer: the 0.1–0.3σ range was
  replaced by −0.17σ, and "Δχ²_data" by the wall-free likelihood.

### 2026-10-07
- Opened at Luca's request.
- [261007-y-shape-first-look](261007-y-shape-first-look/LOGBOOK.md) DONE: **Y² is adequate; Y⁴ is not worth building.**
  - `alphaS` sees the forward LEVEL of L2 (ρ = −0.44), not the shape (ρ = −0.025).
  - The active face L2(2.5) = 0 acts as a floor on the level: slope −0.032 σ_NOM per +0.01 GeV²; Δχ² of the wall-free likelihood (data + priors + lattice)
    to release it is only 0.5.
  - δλ2 = −0.0078 ± 0.0078 matches MAP22 (−0.0079); the AN's +0.125 is 17σ away.
  - MAP22's non-quadratic shape is worth ≤ 0.008σ.
  - Y⁴ would need a full cache rebuild (the registry fingerprint), ~1 week.
  - Open: `alphaS` depends on the forward L2 floor (MAP22's L2(2.5) = 0.052 → −0.17σ; the full-release +0.32σ is orientation only).

---

## Findings

1. The Y² rapidity form is adequate: `alphaS` correlates with the shape at −0.025 and with the level at −0.44, and MAP22's non-quadratic shape is worth ≤ 0.008σ. A Y⁴ term would need a full cache rebuild and is not warranted. — [261007-y-shape-first-look](261007-y-shape-first-look/LOGBOOK.md)
2. The active wall face L2(|Y|=2.5) = 0 acts as a floor on the TMD level: −0.032 σ_NOM per +0.01 GeV², Δχ² 0.5 (wall-free likelihood: data + priors + lattice) to release; our δλ2 matches MAP22, while the AN's ΔΛ2 = +0.125 is 17σ away. — same

---

## Decisions

- 2026-10-08 — Close; no Y⁴ build. (Luca)
