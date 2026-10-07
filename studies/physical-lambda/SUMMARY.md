---
title: Physical-λ enforcement in the SCETlib NP param-model fit
slug: physical-lambda
status: done
period: 2026-06-30 – 2026-07-14
updated: 2026-10-07
covers: 2026-07-14
---

# Physical-λ enforcement in the SCETlib NP param-model fit

> **Freezing λ4_ν = 0 (one `--freezeParameters` entry; no wall, no reparametrization) makes the real-data Z fit converge to physical, damping NP form factors without changing σ(α_s), because λ4_ν is a redundant direction almost uncorrelated with α_s. Two checks were never closed: whether that fit used the corrected b_T grid, and a clean attribution of the soft wall's ~3 % effect on σ(α_s).**

## Why

The SCETlib NP parameter model floats the CS-kernel and TMD form-factor coefficients (AN-25-085 §3.2.5, Eqs. 8–9: λ2_ν, λ4_ν in γ_ν^NP; λ2, δλ2, λ4 in F_eff). Free real-data fits landed at unphysical λ (a form factor anti-damping at large b_T). The goal was a fit that **allows only physical (damping) λ without masking real data–model tension**, staying with `tanh_2`.

## What we did

All fits: real data on the 4D Z card (`260623_Zhistmaker`, ptll × yll × cosθ\* × φ\*, 49920 bins), CT18Z N3+0LL b_T-grid param model with `tanh_2` forms, λ∞ and λ∞_ν frozen, α_s blinded. σ(α_s) is the raw `pdfAlphaS` error from the straight-through Gauss–Newton cov pass. Remedies compared, each for EDM and σ(α_s): the `NPDampingWall` regularizer (relu² penalty on the damping conditions, strength τ), freezing λ4_ν, and a richer CS form.

| configuration | NP outcome | EDM | σ(α_s) | source |
|---|---|---|---|---|
| all λ floating, no wall | λ2_ν = −0.056 | 98 | 0.71, off-minimum | log 07-01 |
| floating, wall τ = 5 | λ2_ν = +0.082, λ4_ν = −0.0037 | n/a | n/a | F8 (06-30) |
| **λ4_ν = 0 frozen, no wall** | **λ2_ν = +0.045, physical** | 5.6e-14 | **0.442** | F10, log 07-01 |
| λ4_ν = 0.01 + wall τ = 5 | λ2_ν = 0.0046, at boundary | 6.4e-13 | 0.429 | log 07-02 |

## Findings

1. **Freezing λ4_ν = 0 is the fix.** The pathology was λ2_ν < 0, hidden by a perfect anti-correlation with λ4_ν. Freezing λ4_ν breaks it: λ2_ν moves to +0.045 by itself, γ_ν damps, and the negative-σ(qT) area returns to the λ_central baseline (6.46e-5). σ(α_s) is unchanged (0.4423 vs 0.44218) because ρ(α_s, λ4_ν) = 0.07; freezing a parameter shrinks σ(α_s) by about ρ²/2 [log 2026-06-30, F10]. *Caveat:* the floating fit behind 0.44218 is not identified, and the 2026-07-01 entry calls floating-λ4_ν covariances untrustworthy.

2. **The data constrain about two NP combinations, not five λ.** ρ(λ2_ν, λ4_ν) = ρ(λ2, δλ2) = −1.000. Only λ4 is genuinely measured: +0.138 ± 0.059, +2.4σ, physical. The free-fit λ2_ν < 0 is −0.4σ, i.e. noise [log 2026-06-30, F8]. Its negative σ(qT) (a ridge at qT = 0.5 GeV, −10.8 % of peak at |Y| = 2.5) is washed out by the gen binning, invisible to the minimizer [F9], so the constraint must be explicit (rabbit's `allowNegativeParam` is POI-only, a no-op for the λ [F7]).

3. **With λ4_ν floating, the fit never converged.** Its σ(α_s) = 0.710/0.638 came from points with EDM 98/236; pass 1 ran `--noEDM` and trust-krylov's "failure to predict improvement" exit was taken as convergence [log 2026-07-01]. This retracts the earlier "status 2 is benign" finding (F5). Rule: quote σ only when EDM ≪ 1.

4. **An active wall acts like fixing λ2_ν, and tightens σ(α_s) by about 3 %.** Data push λ2_ν onto the boundary (+0.0046 ± 0.0048; the honest interval is about +0.12/−0.005). σ(α_s) is 0.4293 with the wall, 0.4423 without it, and 0.4269 with λ2_ν fixed. A symmetric likelihood scan gives 0.426: the Hessian is fine for α_s [log 2026-07-02]. *Caveat:* the two fits differ in λ4_ν (0.01 vs 0). The clean comparison (λ4_ν = 0.01, no wall) never converged: EDM 5.3 [log 2026-07-10].

5. **The earlier σ(α_s) = 0.554 (`260611` setup) is not a valid reference.** The drop to 0.442 is almost entirely the NP-group impact on α_s (0.339 → 0.155). The old postfit sat at λ4 = −0.0207, just above an F_eff divergence at |Y| = 2.5 that sets in for λ4 ≲ −0.0225, so it was dropped [log 2026-07-01]. Near λ_central the current model closes to 0.005–0.05 % (λ-variations), 0.145 % (reco), 0.28 % (gen MC), 0.07 % (official SCETlib+DYTurbo, |Y| < 2.5) [log 2026-07-01, 2026-07-02]. *Caveat:* the λ-variation and official-prediction checks ran on the old b0 = 0 grid, and none were made at the postfit λ.

## What changed

- **Defaults:** no card/default change recorded here; later studies use λ4_ν = 0 in the nominal ([scetlib-ad-param-model](https://submit.mit.edu/~lavezzo/alphaS/studies/#scetlib-ad-param-model), [constrained-fit-strategy](https://submit.mit.edu/~lavezzo/alphaS/studies/#constrained-fit-strategy)).
- **WRemnants** (`scetlib-np-param-model`, ffbe5b46f): plotters/diagnostics evaluated the card's NP form, not the fit's override (σ_gen ≈ −7e45 for `tanh_6` fits); fixed via `lambda_central.read_np_models` [log 2026-07-03].
- **WRemnantsHelpers:** new `scripts/fit_summary_table.py`; `workflows/fitterSCETlibNP.py` no longer passes `--noEDM` to the Hessian step, which had made rabbit silently write fits without a covariance [log 2026-07-14].
- **knowledge/:** blinding semantics (constant offset: σ and Δ-central comparisons valid) in `20_frameworks/nominal_workflow.md` [log 2026-07-02].

## Conclusions and open items

In this setup physical NP costs nothing in σ(α_s); an active soft wall costs ~3 %. `tanh_6` with λ6_ν = 7e-4 (SCETlib's value) is a checked, unadopted alternative [F11].

**Open.** (1) *Grid of the 0.442 fit:* the logbook says the buggy b0 = 0 grid [log 2026-07-02], but the file's metadata (pass 1 run 2026-06-25, after the 06-24 grid swap, default grid) points to the fixed one; check before quoting. (2) Five 2026-07-10 runs lack cov passes. (3) Postfit-λ template closure deferred. (4) A data-only muon-calibration impact on α_s (0.267 vs 0.029 Asimov), not NP-routed, was not followed up [log 2026-07-02].

**Qualified by later work.** [np-wall-local-minima](https://submit.mit.edu/~lavezzo/alphaS/studies/#np-wall-local-minima): on the 2D `tanh_6` card the likelihood is multimodal with an unphysical global optimum and physicality costs Δχ² ≈ 16.6, so "physicality is free" holds for this 4D setup, not in general. `knowledge/30_physics_global/np_parametrization_constraints.md`: λ4_ν = 0 removes a real "delayed turn-on" direction at some NLL cost.

<small>Full record: [logbook](https://submit.mit.edu/~lavezzo/alphaS/studies/#physical-lambda:logbook) · bulk outputs: `/ceph/.../lavezzo/alphaS/260623_Zhistmaker/…_realdata_<tag>/`</small>
