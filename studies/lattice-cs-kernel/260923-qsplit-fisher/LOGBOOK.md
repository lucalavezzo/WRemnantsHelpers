---
title: Q-split gen-level Fisher forecast of the CS-kernel / TMD degeneracy
slug: 260923-qsplit-fisher
study: lattice-cs-kernel
status: done
created: 2026-09-23
updated: 2026-09-23
owner: study-worker
---

# Q-split gen-level Fisher forecast of the CS-kernel / TMD degeneracy

**Task:** Does splitting mll [60,120] into Q windows break the degeneracy between the CS-kernel NP λ (λ2_ν, λ4_ν) and the TMD boundary-condition λ (Λ2, λ4, δλ2) in a gen-level Fisher forecast? How do σ(λ2_ν), ρ(λ2_ν, Λ2) and σ(α_s) change from Q-integrated → 3 windows → 5 windows?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-09-23)

> **No: splitting mll does not break the λ2_ν–Λ2 degeneracy. ρ(λ2_ν, Λ2) goes −0.998 → −0.993 → −0.991 (Q-integrated → 3 → 5 windows).
> But it does halve σ(λ2_ν) and σ(Λ2) (0.252 → 0.125 → 0.114 GeV²), and it cuts σ(α_s) by 35 %. It gets there by pulling the NP flat direction apart from α_s and the TNPs, not by the Q lever arm on λ2_ν/Λ2.**
> **Caveats first.** This is a gen-level, stat-only Fisher forecast at the physical cache anchor. PDF is fixed (no eigenvectors), so σ(α_s) is optimistic. It includes no detector smearing and no acceptance shape. The primary arm leaves the NP λ unconstrained, while the real card-A fits put N(0,1)-in-θ priors on them. With those real-fit priors the gain shrinks to −17 % on σ(λ2_ν) and −6 % on σ(α_s). With a lattice CS prior it is ≈ 1 %. Almost all of the gain comes already at 3 windows.

- **Next action:** none. Task closed. Whether it is worth a reco-level Asimov test with mll bins is Luca's call (see Result, physics read).
- **Blocking on:** nothing. Grid A is built and on ceph (12.3 min wall).

---

## Log

<!-- Newest first. What was tried, what happened, why — with an evidence path. -->

### 2026-09-23 — Fisher forecast
- `scripts/fisher.py --ndata 6766960 --ptcut 30 --point {anchor,lattice} --plots` → `forecast_{anchor,lattice}.out/.json`,
  plots `sigma_vs_nwin_*`, `rho_vs_nwin_*`, `deriv_ratio_vs_Q_*`. ε = 12 550 events/pb (σ_gen(qT<30) = 539.2 pb;
  σ_gen(qT<40) = 589.9 pb → 7.40 M events, cf. 7.24 M in card A for ptll < 44).
- F is non-singular in every arm. Its smallest eigenvalue is 0.13 (Q-integrated, NP free, θ units), so no null directions.
- Attribution (NP free, anchor; `forecast_anchor.out`, "attribution" block): with only the 5 NP λ floating,
  σ(λ2_ν) = 0.035 in every arm (Q split −3 %). Adding α_s and ONE of the normalisation-like TNPs (s, b_qqV,
  b_qg, b_qqS, h_qqV) lifts it to 0.11–0.15 Q-integrated. The Q split takes back ~1/3 of that (e.g. +s: 0.145 → 0.100).
  Removing any single nuisance from the full set changes little: the flat direction is collective.
- Added a variant with a Gaussian stand-in for the lattice CS constraint (λ2_ν 0.038, λ4_ν 0.0033, ρ −0.88, from
  260923-scetlib-kernel-fit), TMD λ free. There the Q split buys ~1 %.
- Real-data cross-check (`scripts/realfit_np_sigma.py`, CCKRYLOVWARM; α_s not read). Postfit σ(λ2_ν) = 0.0056 and
  ρ(λ2_ν, Λ2) = −0.28, at λ2_ν ≈ −0.091, λ4_ν ≈ +0.001 (anti-damping). That is 15× tighter than this forecast at the
  physical anchor (0.087 with the same priors). **Not comparable:** a different point in λ space (see Open questions), reco
  level with finer ptll bins, and PDF eigenvectors floating.

### 2026-09-23 — Jacobians + validation
- `scripts/extract_jacobians.py` → `jacobians.npz` (values + full 24-column J per window, two μ_R legs, FD checks).
  Output in `extract_jacobians.out`.
- Closure: the sum of the 5 windows reproduces the single-window [60,120] probe cache (4 low-qT forward cells) to
  **4.8e-5** (per cell ≤ 1.5e-4). `scripts/closure_vs_probe.py`. The costing task found 6e-5.
- AD vs finite difference, NP columns, all windows, both points: ≤ 4e-4 of max|J| (δλ2 3e-4, λ2_ν 1e-6).
- **The full lattice point (λ2_ν = 0.184, λ4_ν = −0.0059) cannot be evaluated on this cache.** My first FD
  check used a central step h = 0.002 in λ4_ν, which crosses λ4_ν < 0, and it failed (40×). `scripts/diag_np_fd.py` →
  `diag_np_fd.out`: at the anchor, one-sided FDs at h = 1e-4 match AD, but σ at λ4_ν = −0.004 has already moved by 3 %
  in the lowest qT bins, and at λ4_ν = −0.01 σ(qT 0–1) is **negative** (ratio −0.82). At the lattice point, forward and
  backward FDs at h = 1e-4 disagree by 20–100 % in the qT < 3 bins, so the cached value function is erratic there.
  That is the known negative-λ4 trap. The robustness point is therefore **λ2_ν = 0.184, λ4_ν = 0** (lattice λ2_ν,
  λ4_ν on its physical boundary), where FD vs AD is ≤ 2.4e-4.

### 2026-09-23 — grid A built
- All 5 exited 0. Wall per window: [60,76] 12:14, [76,86] 10:43, [86,96] 10:00 (200 threads), [96,106] 12:20,
  [106,120] 11:17. **Total wall 12.3 min** (13:19:52 → 13:32:12). Peak RSS ≤ 5.4 GB. Rules median 228–268
  nodes/bin, worst training residual ≤ 1.0e-5. Caches are 119–147 MB each. The X-Math `max_iterations` warnings
  are the same 10/process as in the probes. The cost model's ~0.5 h estimate was conservative by about 2.5×.
  (`logs/time_q*.txt`, `logs/build_q*.log`)

### 2026-09-23 — forecast set-up (checked, not guessed)
- **What the real card-A fits constrain** (from `meta/param_priors` of
  `260917_cc_fits_hvpfix/fitresults_CCKRYLOVWARM.hdf5`, plus `scetlib_ad/params.py`): fitted =
  alphaS (free) + λ2, λ4, δλ2, λ2_ν, λ4_ν + 9 TNPs + resumTransition2 + 29 pdfEig + 2 scale-envelope
  nuisances, **all but alphaS at N(0,1) in θ**. Physical widths (REPARAM): λ2, λ4, δλ2 0.5; λ2_ν 0.1;
  λ4_ν 0.5; x2 quad map (dx2/dθ = 0.2 at 0); alphaS θ-width 0.002. Frozen (DEFAULT_FROZEN): λ∞, λ∞_ν,
  b0/bmax_ν, tnp_b_qqDS (inert), x1, x3, κ_R, κ_F. λ6/λ6_ν are not in the cache (tanh_2 forms).
  **So the real fits do put priors on the NP λ.** The brief asks for NP unconstrained; I report that as
  the primary arm and the real-fit-prior arm alongside.
- Scale envelope: 3-point μ_R-only (κ_R = 0.5, 2), rabbit quadratic symmetrisation
  (k_avg, k_diff = ½√3(up−down)), hard-zeroed for gen bins with lower qT edge < 20 GeV, frozen at the
  anchor, linear — re-implemented from `scale_envelope.py` on the window caches.
- `fo_muf_poly = 0` (κ_F frozen, 3-point envelope does not move it: both conditions of
  `_check_fo_muf_poly` hold).
- ε: card A (real data, 60 < mll < 120, |yll| < 2.5, ptll 0–44) has N_data = 6 766 960 for ptll < 30
  and 7 243 186 for ptll < 44; Zmumu is 99.7 % of the prediction. The card's ptll edges have no 40, so ε
  is defined at the common edge 30: ε = N_data(ptll<30)/σ_gen(qT<30). (`scripts/ndata.py`)

### 2026-09-23 — grid A build launched
- Pre-launch check (13:19): load 165 / 768 cores, 1.3 TB mem free, my threads 264. Live: one areimers
  rabbit fit (~104 cores), nothing of mine. `scetlib-ad-param-model` and `alphas-scan-discontinuity`
  START HERE both say nothing running. No clash, so launched at full recipe size.
- Launched 13:19:52, 5 detached processes (setsid nohup) via `scripts/build_window.sh <lo> <hi> <threads>`:
  [60,76] 45, [76,86] 45, [86,96] 200, [96,106] 45, [106,120] 45 threads (380 total). Pin 2da973d
  scetlib-cms @ ca15aec, WRemnants `scetlib-ad-param-model` @ ede643dc, `--pdf-eig 0 --n-train 9`,
  base_1e3.conf. Logs `logs/build_q*.log`, `logs/time_q*.txt`. Output
  `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/qsplit_260923/q<lo>_<hi>/`.

---

## Result

**Comparability caveats, before any number.**
1. **Gen level, stat only.** V = Poisson on n = ε·σ_gen per bin, with one effective ε = 12 550 events/pb =
   N_data(card A, ptll < 30) / σ_gen(qT < 30). No detector smearing, no acceptance or efficiency shape, no bin-by-bin
   MC stat, no card nuisances. Gen binning is 5 |Y| × 15 qT (to 40 GeV); card A has 20 yll × 39 ptll.
2. **Fixed PDF**: grid A has no PDF eigenvectors (`--pdf-eig 0`, the α_s PDF pair is kept). **σ(α_s) is optimistic** and is
   not to be compared with any fit σ(α_s). The Q-integrated vs Q-split comparison is like-for-like: the same cache, with
   rows summed.
3. **Priors.** In the primary arm ("NP free") α_s and the 5 NP λ are unconstrained, as the brief asks. The 9 TNPs,
   resumTransition2 and the two μ_R-envelope nuisances are N(0,1), as in the real fit. **The real card-A fits also put
   N(0,1)-in-θ priors on the NP λ** (λ2, λ4, δλ2 ± 0.5; λ2_ν ± 0.1; λ4_ν ± 0.5), so that arm is shown too. Frozen as in
   the real fit: λ∞, λ∞_ν, b0/bmax_ν, tnp_b_qqDS, x1, x3, κ_R, κ_F.
4. **Local, at the physical anchor** (λ2_ν = 0.15, λ4_ν = 0, λ2 = λ4 = 0.4, δλ2 = 0). λ4_ν = 0 sits on the edge of a
   region (λ4_ν < 0) where the cached model is erratic (Log). So the Fisher σ(λ4_ν) ≈ 0.06–0.13 describes a quadratic
   the true likelihood does not follow on the negative side.
5. The robustness point is **(λ2_ν = 0.184, λ4_ν = 0)**, not the full lattice best fit: λ4_ν = −0.0059 cannot be
   evaluated on this cache.

**Forecast at the anchor** (σ in physical units: λ in GeV^n; `forecast_anchor.out`):

| arm | σ(λ2_ν) | σ(λ4_ν) | σ(Λ2) | σ(Λ4) | σ(δΛ2) | ρ(λ2_ν, Λ2) | σ(α_s) fixed-PDF | flattest NP dir, σ_θ |
|---|---|---|---|---|---|---|---|---|
| **NP free** Q-integrated | 0.252 | 0.130 | 0.478 | 0.102 | 0.0034 | −0.998 | 5.9e-4 | 2.71 |
| NP free, 3 windows | 0.125 | 0.069 | 0.237 | 0.100 | 0.0033 | −0.993 | 4.0e-4 | 1.34 |
| NP free, 5 windows | 0.114 | 0.064 | 0.215 | 0.100 | 0.0033 | −0.991 | 3.9e-4 | 1.22 |
| off-peak ×0.5, Q-int / 3 / 5 | 0.261 / 0.158 / 0.146 | 0.135 / 0.085 / 0.079 | 0.496 / 0.301 / 0.277 | 0.105 | 0.0035 | −0.998 / −0.995 / −0.994 | 6.0 / 4.4 / 4.3e-4 | 2.81 / 1.70 / 1.57 |
| **real-fit NP priors**, Q-int / 3 / 5 | 0.087 / 0.075 / 0.072 | 0.053 / 0.047 / 0.046 | 0.167 / 0.143 / 0.138 | 0.099 / 0.098 / 0.098 | 0.0034 | −0.985 / −0.980 / −0.979 | 3.77 / 3.58 / 3.55e-4 | 0.94 / 0.80 / 0.77 |
| lattice CS prior, TMD free, Q-int / 5 | 0.033 / 0.032 | 0.0030 / 0.0029 | 0.062 / 0.060 | 0.058 / 0.057 | 0.0034 | −0.913 / −0.907 | 3.37 / 3.33e-4 | 0.36 / 0.35 |
| NP only (α_s + all nuisances fixed), Q-int / 3 / 5 | 0.035 / 0.035 / 0.034 | | 0.052 / 0.051 / 0.051 | | | −0.983 / −0.983 / −0.983 | — | |

Robustness point (λ2_ν = 0.184, λ4_ν = 0; `forecast_lattice.out`). NP free: σ(λ2_ν) 0.303 → 0.131 → 0.118, ρ −0.999 →
−0.993 → −0.991, σ(α_s) 6.8 → 4.1 → 3.9e-4. Real-fit priors: 0.089 → 0.076 → 0.073, σ(α_s) 3.81 → 3.62 → 3.58e-4.
The pattern is the same as at the anchor.

**NP correlation matrix, NP free** (order Λ2, Λ4, δΛ2, λ2_ν, λ4_ν):
```
Q-integrated                                   5 windows
[ 1.    -0.198 -0.073 -0.998  0.978]           [ 1.    -0.114  0.006 -0.991  0.906]
[-0.198  1.     0.002  0.158 -0.364]           [-0.114  1.    -0.011  0.025 -0.452]
[-0.073  0.002  1.     0.07  -0.06 ]           [ 0.006 -0.011  1.    -0.013  0.028]
[-0.998  0.158  0.07   1.    -0.973]           [-0.991  0.025 -0.013  1.    -0.884]
[ 0.978 -0.364 -0.06  -0.973  1.   ]           [ 0.906 -0.452  0.028 -0.884  1.   ]
```
ρ(α_s, λ2_ν) = +0.82 → +0.53 → +0.49 and ρ(α_s, Λ2) = −0.83 → −0.56 → −0.52 (Q-int → 3 → 5). All the other arms and
matrices are in `forecast_anchor.out` / `.json`.

**Eigen-decomposition of the marginal NP covariance** (θ units, i.e. in units of the prior widths). The σ along the
five eigen-directions, NP free, are Q-int **2.71**, 0.212, 0.042, 0.019, 0.0067 and 5 windows **1.22**, 0.211, 0.042,
0.019, 0.0067. **Only the flattest direction tightens (×2.2).** Its direction does not change: θ = (Λ2 −0.35, λ2_ν
+0.93, λ4_ν −0.09), i.e. physically δλ2_ν : δΛ2 : δλ4_ν ≈ +0.093 : −0.176 : −0.047 GeV^n. That is the O(b²)
combination with ∂σ/∂λ2_ν ≈ 2 ∂σ/∂Λ2.

![sigma vs number of windows](sigma_vs_nwin_anchor.png)
*Gen level, stat only, fixed PDF, NP λ unconstrained, at the anchor. σ normalised to the Q-integrated arm. The λ2_ν
curve lies under the Λ2 one. Dashed: off-peak windows' yields ×0.5.*

![correlations vs number of windows](rho_vs_nwin_anchor.png)
*Same caveats. ρ(λ2_ν, Λ2) stays at −0.99. What moves is the correlation of the NP pair with α_s.*

![derivative ratio vs Q](deriv_ratio_vs_Q_anchor.png)
*(∂σ/∂λ2_ν)/(∂σ/∂Λ2) per Q window, summed over |Y| < 2.5, anchor. The qT 4–5 GeV curve sits near the zero crossing of
both derivatives, so its ratio is the least meaningful one.*

**Physics read.** In SCETlib's forms (AN-25-085 Eqs. npgamma/npf), at small b_T the TMD boundary condition gives
ln F ≈ −2Λ2 b_T², with no Q dependence. The CS kernel γ^NP ≈ −½λ2_ν b_T² enters multiplied by the rapidity log
~ln(Q²/μ0²). At fixed Q the two are therefore the same b_T² operator, with a relative weight set by L_Q. Across
[60,120], ln Q² changes by ln 4 = 1.39 on L ≈ 8–9, and 85 % of the events sit in the [86,96] window. So the ratio of
derivatives moves only by +10–15 % across the whole range (third plot; it is 1.98 → 2.19 at qT 0–1 GeV). That lever
arm is too small to break a ρ = −0.98 degeneracy. With everything else fixed, the Q split gains 3 %, and ρ(λ2_ν, Λ2)
stays at −0.99 in every arm.

What the split does buy is the α_s side. With α_s and the normalisation-like TNPs (s, b_qqV, b_qg, b_qqS, h_qqV)
floating, the flat NP direction picks up a component that they can partly fake at fixed Q: σ(λ2_ν) goes from 0.035 with
NP only to 0.25 with everything floating. Their Q dependence differs from that of a b_T² NP term, so separate windows
separate them again. ρ(α_s, λ2_ν) drops from 0.82 to 0.49, and σ(α_s) falls by a third (NP free). Three windows (peak
plus the two sides) capture ~90 % of the five-window gain. Halving the off-peak yields keeps ~80 % of it.

**Is the Q lever arm worth adding mll bins at reco?** It depends on what constrains the NP sector.
- **Free NP, or loose priors:** yes, it is worth an Asimov test. It is the largest effect here: σ(α_s) −35 % and σ(λ2_ν)
  ×0.45, and the cache cost is negligible (12 min).
- **Current real-fit priors (λ2_ν ± 0.1):** modest, −6 % on σ(α_s) and −17 % on σ(λ2_ν).
- **Lattice constraint on the CS kernel:** redundant, ≈ 1 %. The lattice fixes the direction the Q split would fix.

It never resolves λ2_ν from Λ2 on its own. That still takes the lattice (or another CS-kernel handle), which is this
study's premise. All of this is before smearing, the PDF eigenvectors and the card nuisances, each of which can only
dilute the gain.

## Findings

1. Splitting mll [60,120] into 3 or 5 windows does **not** break the λ2_ν–Λ2 degeneracy: ρ stays −0.99, and with NP
   only floating it gains 3 %. It halves σ(λ2_ν) and σ(Λ2) when α_s and the TNPs are profiled, and cuts the fixed-PDF
   σ(α_s) by 35 % (NP free). With the real-fit NP priors those become 17 % and 6 %; with a lattice CS prior, ≈ 1 %.
   — (evidence: `forecast_anchor.out`, `forecast_lattice.out`)
2. The flattest NP eigen-direction is ≈ 0.93 λ2_ν − 0.35 Λ2 − 0.09 λ4_ν (θ units), the O(b_T²) combination. A Q split
   shrinks only that eigenvalue (σ_θ 2.71 → 1.22), not the others. — (evidence: `forecast_anchor.out`)
3. (∂σ/∂λ2_ν)/(∂σ/∂Λ2) rises by only +10–15 % from the [60,76] to the [106,120] window, which is consistent with the
   ln Q² lever arm of the rapidity log. — (evidence: `deriv_ratio_vs_Q_anchor.png`)
4. A 5-window, 375-bin SCETlib AD cache without PDF eigenvectors builds in **12.3 min wall** on 380 threads. The costing
   model's 0.5 h estimate was ~2.5× conservative. — (evidence: `logs/time_q*.txt`). *Generalises → knowledge
   (scetlib_ad_cache_build_parallelism.md).*
5. On the 2da973d/ca15aec cache the value function for λ4_ν < 0 is erratic: σ(qT 0–1) is negative at λ4_ν = −0.01,
   and one-sided FDs disagree by 20–100 % at λ4_ν = −0.006. **An FD check that straddles λ4_ν = 0 fails for that
   reason, not because the AD is wrong.** At λ4_ν ≥ 0 AD = FD to ≤ 4e-4. — (evidence: `diag_np_fd.out`,
   `extract_jacobians.out`). *Generalises → knowledge (np_parametrization_constraints / negative-λ4 trap).*

## Open questions

- **The real-data postfit σ(λ2_ν) = 0.0056 with ρ(λ2_ν, Λ2) = −0.28** (CCKRYLOVWARM). This forecast gives 0.087 and
  −0.985 with the same priors at the physical anchor, 15× looser. The real fit sits at λ2_ν ≈ −0.09 (anti-damping),
  where the NP response may be much steeper. It is also reco level, with twice-finer low-ptll bins and PDFs floating.
  Is its Hessian a local artefact of the unphysical minimum? It bears directly on the study logbook's statement that
  "the Z fit is tighter than the lattice". I did not chase it.
- The full lattice point (λ4_ν = −0.0059) cannot be evaluated on this cache. Whether that is a cache (rule
  compression) limitation or a genuine b_T-integral pathology of tanh_2 with λ4_ν < 0 was not separated.
- Not done: a reco-level version (smearing through the card's response, with the 29 PDF eigenvectors). That is the
  honest test of "worth adding mll bins".
