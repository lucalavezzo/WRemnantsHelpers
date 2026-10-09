---
title: LATFROZ — frozen-pert lattice kernel, three n_f conventions
slug: 261008-latfroz-nf-variants
study: lattice-cs-kernel
status: done          # active | done | paused | abandoned
created: 2026-10-08
updated: 2026-10-08
owner: study-worker
---

# LATFROZ — frozen-pert lattice kernel, three n_f conventions

**Task:** With the lattice-side CS kernel frozen in its perturbative part (α_s=0.1168, TNPs nominal; lattice constrains only λ2_ν, λ4_ν), how do α_s and the fit change vs NOMSTIFF (no lattice) and LATB8 (live kernel), for each of three n_f conventions (V1 native nfmatch=1, V2 old-table b-decoupled, V3 nfmatch=m_b) of the single n_f systematic row?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-10-08, after the PG follow-up) — DONE

- **PG tension (follow-up):** vs the Z-only minimum XWSTIFF (its λ_ν priors removed exactly), **PG = 13.5 / 2 dof,
  p = 0.12 %, 3.2σ** (V3; V1 13.75, V2 13.58). That is above the Δχ²_lat-only 2.6σ. Caveat: XWSTIFF is the lower of two
  walled Z-only minima (CMR1B: −1.35 in PG). Result §2b.
- **Answer:** freezing the lattice kernel's perturbative part (α_s 0.1168, TNPs 0; lattice constrains only λ2_ν, λ4_ν)
  moves `alphaS` by **−0.026 … −0.035 σ_NOM vs LATB8** (−0.138 … −0.148 vs NOMSTIFF) and widens σ(`alphaS`) by 0.8–0.9 %
  vs LATB8. The three n_f conventions span 0.009 σ_NOM. Newton predicted every fit to ≤ 0.0005 σ_NOM. Data–lattice
  tension Δχ²_lat ≈ 9.2–9.5 for 2 dof, p ≈ 1 % (2.6σ), the same in all three. Result §1–4.
- **Next action:** none for this task. Luca picks the nominal n_f convention (recommendation: V3, Result §4).
- **Blocking on:** nothing.
- **Running:** nothing. All three fits exited 0 (V1 14:53, V3 15:33, V2 16:31).

<!-- A resume block, not the write-up: the answer with its numbers and caveats goes in
     ## Result. A task that grows into a sub-study (several sessions, several results) also
     gets a SUMMARY.md, written by the study-summarizer when the orchestrator asks. -->

---

## Log

<!-- Newest first. What was tried, what happened, why — with an evidence path. -->

### 2026-10-08
- Read the study logbook (START HERE, 10-07/10-08, Decisions), 261007-lattice-term-native (all) and
  261007-lattice-term-design (§5-6).
- WRemnants **2ee7d998** (committed in the container; pushed 2026-10-08): `LatticeCSTerm` `pert=frozen alphas_frozen=0.1168`,
  `nfswitch=`, `nfscheme=evolve|full`. Unit tests 31/31 PASS ([logs/wrem_test_lattice_cs_term.log](logs/wrem_test_lattice_cs_term.log)).
- Offline validation [scripts/validate_nf.py](scripts/validate_nf.py) -> [validate_nf.json](validate_nf.json)
  ([logs/validate_nf.log](logs/validate_nf.log)).
- NCHKF (gated, one cache load, LATB8's command, data, blinding armed): exit 0 at 14:04 ([logs/NCHKF.log](logs/NCHKF.log),
  [nchk_froz.json](nchk_froz.json)). Replay −2.2e-11; frozen-term checks all pass; Newton predictions -> Result §3.
- 14:04 launched LATFROZ_V1/V2/V3 through mem_gate ([cmds/](cmds/), [scripts/build_cmds.py](scripts/build_cmds.py),
  diffs vs LATB8 in [logs/build_cmds.log](logs/build_cmds.log)); fitresults to
  `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261008_latfroz_nf_variants/`.
- V3 is the "whole kernel n_f = 4" variant (`nfscheme=full`), not the literal `nfmatch=4.18` (V3lit). Reason: the brief
  asked to check in the C++ what `mu_match` > 2 GeV does. `DrellYan::gamma_nu_points` (`py/qT/DrellYanAD.cpp`, nf_alt
  branch) uses `mu_match` ONLY as the start point of the n_f = 4 coupling, α_s^(4)(mu_match) := α_s^(5)(mu_match). The
  n_f = 4 β, cusp and boundary are used at every scale, and nothing depends on whether mu_match lies above or below μ.
  So the C++ does exactly what `_nf_shift`'s formula implies. But for mu_match = m_b that formula means
  alt = B5(μ0) + E5(μ0→m_b) + E4(m_b→2 GeV): an n_f = 5 boundary, n_f = 5 running UP to m_b and n_f = 4 running back
  DOWN to 2 GeV. That is not "n_f = 4 for everything below m_b". Its shift is +0.0104, flat, with the OPPOSITE sign to
  every other convention. The brief's physics, n_f = 4 below m_b with couplings identified at m_b, is the pure n_f = 4
  kernel z4(2 GeV; mu_match = m_b), which is now `nfscheme=full`. That variant was fitted. V3lit is reported from Newton
  only (§3), with no extra fit.
- V2 needed no C++ change. `_nf_shift` passed one number as both the switch scale (the μ at which z5 and z4 are
  evaluated) and the identification scale (`mu_match`), but `gamma_nu_points` takes them separately. `nfswitch=1
  nfmatch=4.18` is therefore native: n_f = 4 evolution from 1 to 2 GeV with α_s^(4) identified at m_b(m_b). So the
  gamma-nu-points build LATB8 used was kept for all three fits; no rebuild, and no V1 old-vs-new build check was needed.
- Follow-up (Luca via orchestrator): PG tension against the Z-only walled minimum XWSTIFF, from existing fits only
  ([scripts/pg_tension.py](scripts/pg_tension.py) → [pg_tension.json](pg_tension.json)). Result §2b.
- 16:31 all three fits done (EDM 3.4–3.6e-17). `compare_froz.py` → [compare_froz.json](compare_froz.json)
  ([logs/compare_froz.log](logs/compare_froz.log)).

---

## Result

### 0. Caveats first
- Real data, `alphaS` **blinded**: shifts are in σ_NOM = σ(`alphaS`) of NOMSTIFF, widths as ratios. Nothing is quoted
  at an α_s frame other than each fit's own point. The Newton rows were evaluated AT LATB8's blinded point, inside
  the fitter with blinding armed (NCHKF). No Δα_s = 0 version was computed.
- **Frozen-term values are publishable.** They depend on the public CS λs only, so the LATFROZ lattice Δχ² and the
  Z data+BB split are exact. In-fitter check: armed == disarmed, bitwise. For LATB8 (live term) the split is only the
  published α_s = 0.118 estimate (261007-lattice-term-native).
- **LATFROZ vs LATB8, like for like.** Card A, the same |Y| ≤ 2.5 subset cache (the same file, now spelled at its new
  path), SCETlib build, 44 model priors, relu² wall at τ = 8 with margin 0, minimiser and Hessian. The only change is the
  lattice term: `syst=Jnf+Jbt pert=live` → `syst=Jnf pert=frozen alphas_frozen=0.1168` plus the n_f variant. Each fit
  was warm-started from LATB8's fitresult at τ = 8 directly.
- **NOMSTIFF differs more:** λ4_ν is frozen at 0 there, and the lattice enters as the old 1D Gaussian card term
  (k-form systematic included).
- **Not like for like:** the lattice Δχ² of each fit uses that fit's own covariance (its own n_f row).

### 1. Results (fits)

| | NOMSTIFF | LATB8 (live, Jnf+Jbt) | **LATFROZ_V1** | **LATFROZ_V2** | **LATFROZ_V3** |
|---|---|---|---|---|---|
| n_f row | – (1D card) | native V1 + b_T window | V1: identified at 1 GeV | V2: 1→2 GeV n_f=4, α_s^(4) from m_b | V3: all n_f=4, from m_b |
| Δ`alphaS` / σ_NOM vs NOMSTIFF | 0 | −0.113 | **−0.148** | **−0.140** | **−0.138** |
| Δ`alphaS` / σ_NOM vs LATB8 | +0.113 | 0 | **−0.035** | **−0.027** | **−0.026** |
| Newton prediction vs LATB8 | – | – | −0.0345 | −0.0274 | −0.0259 |
| σ(`alphaS`) / σ_NOM | 1 | 0.972 | 0.979 | 0.981 | 0.981 |
| σ(`alphaS`) / σ(LATB8) | 1.029 | 1 | 1.008 (Newton 1.009) | 1.009 (1.009) | 1.009 (1.009) |
| λ2_ν | 0.064 ± 0.023 | 0.036 ± 0.030 | 0.038 ± 0.030 (Newton 0.0384) | 0.038 ± 0.030 (0.0385) | 0.038 ± 0.030 (0.0383) |
| λ4_ν | 0 (frozen) | 0.0111 ± 0.0054 | 0.0117 ± 0.0056 (0.0116) | 0.0108 ± 0.0058 (0.0108) | 0.0106 ± 0.0057 (0.0106) |
| θ_γν, θ_cusp | +0.69, −0.15 | +0.30, −0.06 | +0.44, −0.09 | +0.45, −0.09 | +0.44, −0.09 |
| EDM | 3.0e-14 | 5.2e-17 | 3.4e-17 | 3.5e-17 | 3.6e-17 |
| active wall face | L2(\|Y\|=2.5) = 0 | same | same | same | same |
| NLL total | 376.615 | 376.675 | 377.075 | 376.992 | 376.937 |
| Z data + BB (NLL) | 354.908 | ≈ 353.45 (lattice at α_s 0.118, published estimate) | 353.842 | 353.850 | 353.841 |
| lattice term (NLL) | 2.525 (1D Gaussian) | live, in the NLL | 4.753 | 4.642 | 4.594 |
| priors (card + 44 model) | 19.182 | 18.487 | 18.480 | 18.500 | 18.503 |
| **lattice Δχ²_lat (own C) / 2 dof, p** | – | (9.81 frozen-V1 at its λ) | **9.51, p = 0.86 %** | **9.28, p = 0.96 %** | **9.19, p = 1.01 %** |
| lattice χ²_lat,total / 18 (lattice GoF), p | – | – | 16.19, 58 % | 15.97, 59 % | 15.87, 60 % |

Evidence: [compare_froz.json](compare_froz.json) ([scripts/compare_froz.py](scripts/compare_froz.py)); fitresults
`/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261008_latfroz_nf_variants/fitresults_LATFROZ_V{1,2,3}.hdf5`; logs
[logs/LATFROZ_V1.log](logs/LATFROZ_V1.log), [logs/LATFROZ_V2.log](logs/LATFROZ_V2.log), [logs/LATFROZ_V3.log](logs/LATFROZ_V3.log).
Wall: every CS condition is slack; the only active face is the TMD L2(|Y| = 2.5) = 0 one, as in NOMSTIFF and LATB8.

### 2. The data–lattice tension (stated, not softened)
- At every LATFROZ minimum the lattice term sits **Δχ²_lat = 9.2–9.5 above its own lattice-only minimum**. Counted
  against the 2 NP parameters the lattice constrains, that is **p = 0.9–1.0 %, ≈ 2.6σ**, nearly the same in all three
  conventions.
- The n_f systematic does not absorb it: the stat-only Δχ² at the same points is 9.51–9.57.
- The lattice data themselves are fine: the total χ²_lat = 16 for 18 dof (p ≈ 60 %), and the lattice-only fit gives
  6.68/18.
- What the Z data want: λ2_ν = 0.038 ± 0.030 against the lattice-only 0.188 ± 0.04 (λ4_ν −0.006). The data prefer a
  much weaker small-b CS damping than the lattice.
- Δχ²_lat alone is only a lower bound on the parameter-goodness-of-fit tension, χ²_PG = Δχ²_lat + Δχ²_Z. The full PG
  number is in §2b: **PG = 13.5 / 2 dof, p = 0.12 %, 3.2σ** for V3.
- **Retraction.** An earlier version of this section said no like-for-like Z-only fit existed. That was wrong:
  XWSTIFF is one (pointed out by the orchestrator).

### 2b. PG tension against the Z-only minimum XWSTIFF (no new fit)
- **Definition.** PG = 2[NLL(joint minimum) − F_Z(Z-only minimum)] = Δχ²_Z + Δχ²_lat, with dof = 2 (λ2_ν, λ4_ν).
  - F_Z = Poisson data + BB + card constraints + the 44 common model priors + the relu² wall.
  - The lattice-only χ²_min is already removed by the term's `offset=min`, so nothing else is subtracted.
- **Reference: XWSTIFF**, `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5`
  (NLL 371.3284, EDM 7.4e-18, λ2_ν on its ≥ 0 face at θ = −1.5000, λ4_ν θ = +0.089). It is the LOWER of the two walled
  Z-only minima. The other, CMR1B (C seed), has F_Z 0.674 higher; using it would lower every PG by 1.35.
- **Term-by-term comparability** ([scripts/pg_tension.py](scripts/pg_tension.py) → [pg_tension.json](pg_tension.json),
  [logs/pg_tension.log](logs/pg_tension.log)):
  - Same card A, the same 3720-parameter list, the same wall command (`margin=0`, τ = 8, no `smooth=`, i.e. relu²;
    re-evaluated here with `smooth=relu2`, since the WRemnants default is now C², 692f9483).
  - The same 44 model priors. The difference: **XWSTIFF ran with the default registry priors on θ(λ2_ν) and θ(λ4_ν)**
    (σ = 1, mean 0; 46 priors), which LATFROZ/LATB8 drop (`prior_sigmas=lambda2_nu=nan,lambda4_nu=nan`).
    - These are subtracted exactly from XWSTIFF's vector: prior_ν = 1.1290 NLL, so F_Z(XW point) = 370.1994.
    - XW's point minimises F_Z + prior_ν, not F_Z. The residual from one Newton step (XW covariance with the prior
      Hessian removed; the λ2_ν wall is in that covariance, σ_θ = 0.0024) is −8e-6 NLL, negligible.
  - Cache: XWSTIFF used the full |Y| ≤ 3.5 cache, LATFROZ the |Y| ≤ 2.5 subset. These are bitwise-identical for card A
    (261006 SUBCHK8B: NLL(subset) − NLL(full) = 0 at LATCHI8's point; NOMSTIFF likewise).

| joint fit | PG (vs XWSTIFF, ν priors removed) | p (2 dof) | Gaussian z | = Δχ²_Z + Δχ²_lat | (XW incl. its ν priors) |
|---|---|---|---|---|---|
| LATFROZ_V1 | **13.75** | 0.10 % | 3.28σ | 4.25 + 9.51 | 11.49 (2.95σ) |
| LATFROZ_V2 | **13.58** | 0.11 % | 3.26σ | 4.30 + 9.28 | 11.33 (2.92σ) |
| LATFROZ_V3 | **13.48** | 0.12 % | 3.24σ | 4.29 + 9.19 | 11.22 (2.91σ) |
| LATB8 (live; approximate, see below) | 12.95 | 0.15 % | 3.17σ | – | 10.69 |

- **Against the Δχ²_lat-only number.** Δχ²_lat alone gave ≈ 2.6σ. Adding the Z data's own cost (Δχ²_Z ≈ 4.3) raises
  the tension to **3.2–3.3σ**. Roughly a third of the PG comes from the Z side. The Z data pay to move λ2_ν off its wall
  (Z-only: λ2_ν = 0 on the face) towards the lattice, and the lattice pays for the rest.
- **Caveats.**
  1. *Second minimum.* XWSTIFF is the lowest walled Z-only minimum we have. A lower, not-yet-found Z-only minimum would
     raise PG; using CMR1B instead would lower it by 1.35 (V3: 12.13, 3.0σ). Conversely, a lower joint minimum than the
     warm LATFROZ ones would lower PG.
  2. *Wall.* The Z-only minimum sits ON the λ2_ν ≥ 0 wall, so the Z-only likelihood is truncated there. PG is computed
     with the wall in both objectives, i.e. as the tension between the Z data restricted to the physical region and the
     lattice. 2 dof assumes Wilks, which a boundary minimum does not guarantee; toys would calibrate it.
  3. *LATB8.* Its live term also shares α_s and the CS TNPs with the Z data, and its offset is the lattice-only minimum
     at α_s 0.118, TNPs 0. So its PG has no clean dof count; the row is indicative only. (All NLLs used are already
     published; no α_s is involved.)
  4. With the ν priors kept in XWSTIFF's objective (last column), PG is 11.2–11.5 (2.9σ). That is the wrong reference
     because the joint fits have no such priors; it is shown only to bracket the bookkeeping.

### 3. Newton prediction (NCHKF, before the fits) vs the fits
Newton = one exact quadratic step from LATB8, at its blinded point, with LATB8's covariance and the lattice block
swapped. Δ`alphaS` vs LATB8, in σ_NOM ([nchk_froz.json](nchk_froz.json), [logs/NCHKF.log](logs/NCHKF.log)):

| row | Newton | fit | λ2_ν / λ4_ν (Newton) | Δχ²_lat at LATB8 → Newton point (fit) |
|---|---|---|---|---|
| live, Jnf only (drop the b_T window) | −0.0008 | – | 0.0358 / 0.01129 | – |
| frozen, stat only | −0.0349 | – | 0.0384 / 0.01162 | 9.83 → 9.50 |
| **frozen V1** | **−0.0345** | **−0.0348** | 0.0384 / 0.01158 | 9.81 → 9.49 (9.51) |
| **frozen V2** | **−0.0274** | **−0.0270** | 0.0385 / 0.01080 | 9.57 → 9.28 (9.28) |
| **frozen V3** | **−0.0259** | **−0.0256** | 0.0383 / 0.01063 | 9.46 → 9.19 (9.19) |
| frozen V3lit (literal `nfmatch=4.18`, not fitted) | −0.0343 | – | 0.0384 / 0.01156 | 9.80 → 9.49 |

- The prediction is good to ≤ 0.0005σ_NOM in `alphaS`, ≤ 0.0002 in λ, and ≤ 0.02 in Δχ²_lat.
- Decomposition: dropping the b_T window moves `alphaS` by −0.0008. **Freezing (stat only) moves it −0.034.** The n_f
  row then adds +0.0004 (V1), +0.0075 (V2), +0.009 (V3), +0.0006 (V3lit).
- In-fitter checks of the frozen term (NCHKF, all pass):
  - replaying LATB8's command with the new code reproduces its stored NLL to −2.2e-11;
  - the term's gradient is nonzero only at λ2_ν and λ4_ν (exactly 0 at `alphaS`, θ_γν and θ_cusp);
  - its value is bitwise the same armed and disarmed;
  - AD vs FD agree to ≤ 1e-8;
  - kernel snapshot status 1.
- The cache-free evaluation of the frozen term (`compare_froz.py`) equals the in-fitter value to all printed digits
  (e.g. 9.8088 at LATB8's λ).

### 4. The three n_f shifts (load time, at α_s 0.1168) and their validation
See the table in the mechanism section below.
- Each shift equals the explicit `gamma_nu_points` composition **bitwise**.
- It matches SCETlib's `qT::Gamma_nu` CLASS (an independent code path, same analytic RGE) to ≤ 4e-16.
- The NP part cancels exactly (2e-16).
- Against the exact-RGE numpy kernel (260923-conventions-map `our_cs_kernel.py`):
  - V2 and V3 agree to 2.4–2.7 % with the coupling identified at m_b, and to 3.2–4.3 % with 3-loop MSbar decoupling;
    so identification vs decoupling is a ≤ 1.6 % effect on the shift;
  - V1 differs by 23 %. That shift is small (pure coefficient n_f dependence), so the analytic-vs-exact RGE truncation is
    a large fraction of it.
- At α_s = 0.118 the native V2 is 0.950 × the old table's −0.0423. The old table used exact RGE and decoupling.
  Evidence: [validate_nf.json](validate_nf.json), [logs/validate_nf.log](logs/validate_nf.log).
- Mapped onto NP directions (`Jnf`):
  - J_NP·Δλ spans +0.0004 … +0.0072 (V1), +0.0016 … +0.031 (V2), +0.0017 … +0.031 (V3);
  - at most 0.08 / 0.36 / 0.35 σ_lat per point;
  - its sign is opposite to δ_nf, because the refit compensates the shift.
- σ(λ2_ν) of the lattice-only fit is 0.039 stat-only and with V1, 0.042 with V2 and 0.043 with V3.
- V2 and V3 encode the same physics: α_s^(4) taken from m_b, as in the lattice's own theory with α_s^(4)(2 GeV) = 0.293.
  They give the same Δλ to 5 % and the same `alphaS` to 0.0014σ. V1 identifies the couplings at 1 GeV, which no
  physical decoupling does. It gives a 4.6× smaller row and is the outlier, though by only 0.009σ.
- **Recommendation: V3** (`nfmatch=4.18 nfscheme=full`). It is literally the lattice's perturbative theory: n_f = 4
  throughout, with the coupling from m_b matching (identification = decoupling up to 0.08 % in α_s). It needs no
  arbitrary switch scale. V2 is equivalent within 0.0014σ if continuity with the old table is preferred.

### 5. Physics read
1. **What freezing does.** With the kernel's perturbative part frozen at the lattice's own α_s, the lattice no longer
   carries α_s information through its ∂γ_ζ/∂α_s lever. It only fixes the CS NP shape, and through the NP degeneracy
   (ρ(λ2_ν, Λ2) ≈ −0.985 in the Z data) it also pins the TMD sector.
   - The cost to α_s is small: σ(`alphaS`) +0.8–0.9 % vs LATB8, still 2 % tighter than NOMSTIFF.
   - The central value moves −0.03σ_NOM vs LATB8.
   - The CS TNPs relax from the lattice-pulled +0.30 back towards the Z-only +0.69 (now +0.44), because the lattice no
     longer pulls on them.
   - The NP picture is unchanged: λ2_ν ≈ 0.038, λ4_ν ≈ +0.011 (interior), the CS side on no wall, the same single TMD
     face.
2. **Consistency.** The frozen kernel and the data now use the same coupling (α_s(m_Z) = 0.1168 ↔ α_s^(4)(2 GeV) =
   0.293), so the open δγ / y(α_s) question of the live term (theorist Q3, physics-review finding) does not arise.
3. **The n_f convention is a sub-0.01σ question for α_s**: 0.009σ_NOM between the smallest (V1) and largest (V3) row.
   All the n_f effect acts through the NP covariance.
4. **The tension is the real message.** The Z data sit 9.2–9.5 in Δχ²_lat (2.6σ for 2 dof; the full PG against
   XWSTIFF is 13.5, 3.2σ, §2b) from the lattice optimum in every convention. No n_f row relaxes it materially, and the lattice data alone
   are statistically fine. Including the lattice term is therefore not a neutral constraint. It costs the data
   Δχ²_data ≈ −2.1 relative to NOMSTIFF here, but NOMSTIFF has λ4_ν frozen, so this is not a pure data comparison. The
   tension should be quoted with any lattice-constrained α_s.

### How the lattice term works (load time vs fit time)

*Self-contained; written for the study summary. Code: WRemnants `wremnants/postprocessing/scetlib_ad/lattice_cs_term.py`
(commit 2ee7d998), SCETlib `DrellYan::gamma_nu_points` (scetlib-cms branch `gamma-nu-points`, 069c326 + 6ab371a).*

**What it is.** The ASWZ lattice collaboration (arXiv:2402.06725) publishes 21 points y_i = γ_q(b_i, μ = 2 GeV) of the
Collins–Soper (CS) kernel, MSbar, n_f = 4, on three ensembles (lattice spacings a = 0.15, 0.12, 0.09 fm), with a
covariance per ensemble. γ_q is exactly SCETlib's γ_ζ = ½γ_ν. The term adds to the fit's NLL

    ½ [χ²_lat − χ²_min] ,   χ²_lat = min_k1 rᵀ C⁻¹ r ,   r_i = γ_ζ^SCETlib(b_i, 2 GeV; p) + k1·a_i/b_i − y_i ,

where k1·a/b is the lattice-artefact term prescribed by the authors (k1 profiled), C the lattice covariance plus
systematics, and p the SCETlib parameter vector. It is a rabbit regularizer (`-r`), so it shares the fit parameters
with the Z cross section; no extra fit parameter is introduced.

**Pipeline.**

```
LOAD TIME (once, when rabbit arms the regularizer: LatticeCSTerm._build -> LatticeCSNativeCore.__init__)
  data file lattice_aswz_data.npz  ->  y_i, b_i, a_i, C_stat (block-diagonal per ensemble)
  reference vector p_ref:
     pert=live   : the param model's anchor (alpha_s 0.118, TNPs 0, lambda_inf_nu 2)
     pert=frozen : the same with alpha_s(mZ) := 0.1168, CS TNPs := 0                     [frozen_reference]
  SCETlib kernel at p_ref (gamma_nu_points; coefficients = bitwise snapshot of the loaded cache rules)
     |-- n_f alternative kernel (nf=4, coupling identified at nfmatch) -> point shift delta_nf  [_nf_shift]
     |-- lattice-only refit of (lambda2_nu, lambda4_nu), k1 profiled, on C_stat:  lam_nom     [refit]
     |-- same refit with the kernel + delta_nf:                                   lam_alt
     |-- J_NP = d gamma_zeta / d(lambda2_nu, lambda4_nu) at lam_nom (SCETlib Jacobian)
     |-- systematic row  delta = J_NP (lam_alt - lam_nom)   ("Jnf": the n_f shift mapped onto NP directions)
     |-- C = C_stat + delta delta^T ;  M = profile matrix (k1 eliminated analytically)        [_profile_matrix]
     '-- offset chi2_min = lattice-only minimum with the final C   (the term is then 1/2 Delta chi2)
EVERY FIT EVALUATION (inside the TF graph: LatticeCSTerm.compute_nll_penalty)
  x (rabbit, physical frame) -> p_full = param_model.scetlib_full_vector_tf(x)  (the SAME tensor the cross section uses)
     pert=live   : p_kernel = p_full
     pert=frozen : p_kernel = p_ref*(1-m) + m*p_full ,  m = 1 on lambda2_nu, lambda4_nu only    [p_kernel_tf]
  gamma_zeta_i = 1/2 gamma_nu(b_i, 2 GeV; p_kernel)   SCETlib clad AD: value + exact gradient + Hessian  [ScetlibGammaNuTF]
  r0 = gamma_zeta - y ;  chi2 = r0^T M r0   (k1 profiled; M fixed since load)                  [chi2_tf]
  NLL += 1/2 (chi2 - chi2_min) * exp(-2 tau)   (rabbit multiplies every regularizer by exp(2 tau); divided back out
                                                with the live fitter.tau)
```

| step | when | where (file:function) |
|---|---|---|
| read data, C_stat | load | `lattice_cs_term.py: LatticeCSNativeCore.__init__` |
| reference vector (live anchor / frozen 0.1168) | load | `lattice_cs_term.py: frozen_reference`, `LatticeCSTerm._build` |
| kernel γ_ζ, Jacobian, Hessian at given p | load + every step | `lattice_cs_term.py: LatticeCSNativeCore.zeta` (numpy) / `scetlib_tf.py: ScetlibGammaNuTF` (TF) → C++ `py/qT/DrellYanAD.cpp: DrellYan::gamma_nu_points` → `ad::gnu_point_value/grad/hess` (= `ad::gamma_nu_resummed`, the function the cross section's AD kernel calls) |
| bitwise check kernel coefficients == cache rules | load | C++ `DrellYan::_gnu_snapshot` / `gamma_nu_snapshot_status` |
| n_f alternative and its shift δ_nf | load | `LatticeCSNativeCore._nf_shift` (C++ `gamma_nu_points(nf=4, mu_match)`) |
| lattice-only refits, J_NP, systematic row | load | `LatticeCSNativeCore.refit`, `__init__` |
| C = C_stat + δδᵀ, k1-profile matrix M, offset | load | `_profile_matrix`, `__init__`, `_build` |
| θ → physical SCETlib vector | every step | `param_model.py: SCETlibADParamModel.scetlib_full_vector_tf` |
| frozen mask (only CS NP λ live) | every step | `LatticeCSTerm.p_kernel_tf` |
| χ² with fixed M, k1 profiled | every step | `LatticeCSTerm.chi2_tf` |
| ½(χ² − χ²_min)·e^{−2τ} | every step | `LatticeCSTerm.compute_nll_penalty`; rabbit `fitter.py` (~l. 2258) multiplies by e^{2τ} |

So the expensive and the convention-laden parts (systematics, offset, covariance) are fixed numbers once the fit
starts; what changes at every step is only the kernel, recomputed by SCETlib at the current parameters, and a 21×21
quadratic form. With `pert=live` the kernel follows α_s and the CS TNPs (resumTNP_gamma_nu, gamma_cusp) as well as the
CS NP λs, so the lattice pulls on α_s; with `pert=frozen` only λ2_ν, λ4_ν reach the kernel, the term's derivative with
respect to α_s and every TNP is exactly zero, and the lattice constrains the NP sector only. The kernel is compared
with the lattice at α_s(m_Z) = 0.1168, the value that corresponds to the lattice's own α_s^(4)(2 GeV) = 0.293 under
m_b decoupling, so the data and the kernel use the same coupling.

**The three n_f conventions of the systematic row.** The lattice is n_f = 4 QCD; our kernel is fixed n_f = 5. The
alternative kernel replaces part of it by n_f = 4 (β, cusp and boundary coefficients), with α_s^(4) := α_s^(5) at an
identification scale (SCETlib has no flavour thresholds; at μ = m_b(m_b) identification equals 3-loop MSbar decoupling
up to the O(α_s²) constant 11/72·(α_s/π)², 0.08 % in α_s). The shift is computed once at the frozen reference
(α_s 0.1168) and is NP-independent (the NP part cancels exactly).

| variant | `-r` options | n_f = 4 used for | couplings identified at | shift δ_nf (21 points) | Δλ = (λ2_ν, λ4_ν) in σ_stat |
|---|---|---|---|---|---|
| V1 (current native) | `nfmatch=1` | evolution 1 → 2 GeV only (boundary at μ0 and running below 1 GeV n_f = 5) | 1 GeV | −0.0083, flat | (−0.09, +0.04) |
| V2 (old-table convention) | `nfmatch=4.18 nfswitch=1` | evolution 1 → 2 GeV only | m_b(m_b) = 4.18 GeV (so α_s^(4)(1 GeV) 0.438 vs α_s^(5) 0.391) | −0.0364, flat | (−0.40, +0.19) |
| V3 (n_f = 4 below m_b) | `nfmatch=4.18 nfscheme=full` | everything: boundary at μ0 and evolution μ0 → 2 GeV | m_b(m_b) | −0.0275 … +0.0025, b_T-dependent | (−0.42, +0.23) |
| (V3lit, literal `nfmatch=4.18`; not fitted) | `nfmatch=4.18` | evolution m_b → 2 GeV only (n_f = 5 up to m_b, back down in n_f = 4) | m_b(m_b) | **+0.0104**, flat (opposite sign) | (+0.12, −0.06) |

(α_s values: exact 4-loop running at α_s(m_Z) = 0.1168; σ_stat = the lattice-only statistical σ, 0.039 / 0.0034.)

---

## Findings

1. `pert=frozen` (WRemnants 2ee7d998): only the CS NP λs reach the lattice kernel. The gradient and Hessian with
   respect to α_s and the TNPs are exactly 0, in the unit tests and in the real fitter; `pert=live` is bitwise unchanged
   against 2f1c3df4. — (evidence: [logs/wrem_test_lattice_cs_term.log](logs/wrem_test_lattice_cs_term.log),
   [validate_nf.json](validate_nf.json), [nchk_froz.json](nchk_froz.json))
2. LATFROZ vs LATB8: Δ`alphaS` −0.035 / −0.027 / −0.026 σ_NOM (V1/V2/V3), σ(`alphaS`) +0.8–0.9 %; Newton predicted
   all three to ≤ 0.0005σ. — (evidence: Result §1, §3)
3. `gamma_nu_points(nf=4, mu_match)` uses mu_match only as the coupling's start point. So the single-scale formula with
   mu_match = m_b gives an n_f = 5-up / n_f = 4-down round trip (shift +0.010, opposite sign), not "n_f = 4 below m_b".
   The switch scale and the identification scale are separable without any C++ change. — (evidence: Log 2026-10-08,
   Result §4)
4. The n_f shift depends on the convention, with a sign flip: −0.008 (identified at 1 GeV), −0.036 (1→2 GeV, from m_b),
   −0.028 … +0.003 (all n_f = 4, from m_b), +0.010 (switch at m_b). Its α_s impact stays ≤ 0.009σ. — (evidence: Result
   §4, [validate_nf.json](validate_nf.json))
5. Data–lattice tension at the joint minimum: Δχ²_lat 9.2–9.5 / 2 dof (2.6σ), and the full PG against the Z-only
   minimum XWSTIFF is 13.5–13.75 / 2 dof, **p ≈ 0.1 %, 3.2–3.3σ**, convention-independent. The lattice GoF alone is fine
   (16/18). — (evidence: Result §2, §2b, [pg_tension.json](pg_tension.json))

---

## Open questions

- PG relies on XWSTIFF being the global walled Z-only minimum (CMR1B is 0.67 higher). Its Wilks calibration at a
  boundary (on-wall) minimum is untested; toys would settle it.
- The frozen reference sets only the CS TNPs (`tnp_gamma_cusp`, `tnp_gamma_nu`) to 0. The other TNPs do not enter the
  kernel (Jacobian exactly 0), so this is complete for the current registry. A new kernel parameter would need adding
  to `FROZEN_TNPS`.
- V1's shift differs by 23 % between SCETlib's analytic RGE and the exact-RGE numpy kernel. That is irrelevant for α_s,
  but it is a reminder that the 1 GeV-identified row is mostly truncation-sensitive coefficient effects.
- Toys for the p-values (study open item) would also calibrate the 2-dof assumption of the tension.
