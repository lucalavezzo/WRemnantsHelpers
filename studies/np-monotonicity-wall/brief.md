---
study_id: np-monotonicity-wall
last_synced_runlog_updated: 2026-05-13
last_synced_at: 2026-05-13
auto_sections:
  - TL;DR
  - Status
  - Key Findings
  - Plots
  - Tables
  - Decisions To Date
  - Open Questions / Next
manual_sections: []
---

## TL;DR

How much do we need to inflate the SCETlib NP priors before postfit pulls fit inside the prior? Comparing nominal AN-lattice priors, V2 inflated priors, and the fully unconstrained fit shows the data wants much wider priors than V2 provided — especially on CS λ_2 / λ_4.

## Status

- 1 active hypothesis: V2 inflation is insufficient.

## Key Findings

- Unconstrained fit pulls CS λ_2 to θ=−3.66, CS λ_4 to θ=+3.28, TMD Λ_4 to θ=−3.35. V2 inflation captured none of these; CS λ_2 only moved from θ=+1.07 to θ=+0.71.
- σ(α_S) Hessian is ~0.5 in raw rabbit units (×2 → ~1.0 σ_AN) across all three configs. The LR-scan width on the unconstrained fit is **2.83 σ_AN**, much wider than the Hessian — this is the relevant uncertainty when priors are dropped.

## Plots

## Tables

| Configuration | γ_Λ_2 | γ_Λ_4 | γ_Λ_∞ | Λ_2 | ΔΛ_2 | Λ_4 |
|---|---|---|---|---|---|---|
| nominal | +0.122 | +0.009 | +1.685 | +0.136 | −0.014 | −0.044 |
| inflatedV2 | +0.110 | +0.006 | +1.685 | +0.154 | −0.014 | −0.100 |
| unconstrained | −0.035 | +0.029 | frozen | +0.357 | −0.014 | −0.108 |

(V2 Λ_4 cell corrected to account for `--scaleParams chargeVgenNP0scetlibNPZlambda4 × 2.5`.)

## Decisions To Date

- (None yet.)

## Open Questions / Next

- What should V3 inflation factors be? Roughly: CS λ_2 ×4, CS λ_4 ×4, TMD Λ_4 ×4.
