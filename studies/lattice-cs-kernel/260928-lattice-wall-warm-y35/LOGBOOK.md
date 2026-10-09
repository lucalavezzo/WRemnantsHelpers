---
title: Lattice + wall on the |Y|<=3.5 cache, warm from the no-lattice walled minimum
slug: 260928-lattice-wall-warm-y35
study: lattice-cs-kernel
status: done        # active | done | paused | abandoned
created: 2026-09-28
updated: 2026-09-29
owner: main session (orchestrator babysits)
---

# Lattice + wall on the |Y|<=3.5 cache, warm from the no-lattice walled minimum

**Task:** Started warm from the walled no-lattice minimum, where does the walled lattice fit (λ4_ν frozen at 0) land on the new cache? Is the cold `LATL4ZWALLCOLD` minimum the walled optimum (the open "walled minimum uniqueness" item), and do the lattice conclusions survive the new cache?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-09-29)

> **Done. Warm from the no-lattice walled minimum, the lattice + wall fit lands on the same minimum as the cold
> LATL4ZWALLCOLD, and the new cache does not move it.** NLL 376.694 vs 376.722 (old cache, cold). Physical λ agree to
> ≤0.001 (λ2 0.029/0.028, λ4 0.087, δλ2 −0.004, λ2_ν 0.063). Δα_s (warm new − cold old) = +0.04σ. σ(α_s) 1.166 vs 1.158e-3.
> GoF unchanged: full 2D 753.4/778 (p 73 %); projected ptll **80.73/39 (p 0.01 %)** vs 80.9. The ptll tension is untouched.
> Caveat: start and cache changed together. Because both land on the same point, that doesn't matter here.

- **Next action:** none. Task closed. In `runs_ad.yaml` as "A+lattice new cache, wall (warm)".
- **Blocking on:** nothing.

---

## Log

### 2026-09-29
- 05:00 — finished (exit 0). The saturated projection sub-fit took 52460 s of postfit, because two fits shared the node. Numbers above from
  `~/public_html/alphaS/260925_fit_summary_ad/fit_summary.tex` (rebuilt 05:02). Against the no-lattice walled fit on the same
  cache (Y35ZWALLWARM): 2ΔNLL = +10.5 (the lattice term's cost), Δα_s = +0.32σ, λ4_ν 0.044 → 0 (frozen), λ2_ν 0.005 → 0.063.

### 2026-09-28
- 17:25 — full 2D saturated 753.39/778 (p 73.0 %). The projected-ptll saturated sub-fit is still running (5.5 h wall-clock so far).
- 15:10 — main fit converged: loss **376.6942** after 27 iterations, EDM 4.5e-15. Now in the projected-ptll saturated sub-fit.
  For reference, cold LATL4ZWALLCOLD (OLD cache) converged to 376.7216 (684 iterations, EDM 3.7e-17). The caches differ, so this
  is not yet a like-for-like uniqueness test.
  **Retraction:** the "336.30" I quoted earlier as LATL4ZWALLCOLD's final loss was the last iteration of its SATURATED sub-fit,
  not of the main fit (main = 376.72).
- Launched `scripts/run_fit.sh` → `/ceph/.../alphaS/260928_lattice_y35_fits/` (log `LATL4ZY35WALLWARM.log` there; symlinked as `logs/LATL4ZY35WALLWARM.log`).
- Start confirmed: cache loaded in 117.6 s via the fast loader (1050 bins); Iteration 0 loss **529.33** vs
  **71190** for the cold LATL4ZWALLCOLD. So the seed was loaded; the gap from 529 down is
  λ4_ν reset to 0 plus the new lattice term. Iteration 1: 456.85.
  Seed choice: Y35ZWALLWARM rather than the old-cache CCWALLWARMPF, since it is the same cache (Luca: "use the new cache").

---

## Result

<!-- The answer, and what it means physically. State comparability caveats BEFORE the
     numbers: blinding family, Asimov vs data, PDF/order swap, card or freeze-list
     difference, excluded points. Check the read against AN-25-085 / knowledge/, not
     against the code. A number without a physics read is not a finished task. -->

---

## Findings

<!-- One line each. A finding that generalizes beyond the parent study → tell the
     orchestrator; it belongs in ../../../knowledge/. -->

1. <finding> — (evidence: <path>)

---

## Open questions

- <what this task turned up but did not chase>
