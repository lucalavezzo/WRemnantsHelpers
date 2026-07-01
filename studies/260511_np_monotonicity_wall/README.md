# 260511 — NP monotonicity wall, first run

## Guiding question
Does the tanh-monotonicity regularizer (`np_monotonicity.NPMonotonicityWall`, criterion (b)) on the LatticeNoConstraints CS card plus the Delta_Lambda-family TMD nuisances behave correctly as the **sole** constraint on the six NP parameters, with the analysis's lattice Gaussian priors fully dropped?

## Configuration
- Histmaker input: `/scratch/submit/cms/areimers/alphas/histmaker/AlphaS/Unblinding/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4BugfixLambda6_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5`
- setupRabbit: `--npUnc LatticeNoConstraints --pdfUncFromCorr --realData --axlim ptll 0j 44j` plus
  - `--scaleParams 'scetlibNPgamma=0.1'` (undo helper's internal 10× CS inflation; net kfactor = 1)
  - `--noConstrainParams 'scetlibNPgamma|scetlibNPZlambda|scetlibNPZdelta_lambda'` (drop Gaussian priors on all 6 NP nuisances)
- rabbit_fit: 4D fit `ptll-yll-cosThetaStarll_quantile-phiStarll_quantile`, `-t 0` (real data), `--doImpacts --globalImpacts`, regularizer `NPMonotonicityWall + NPMonotonicityMapping`, `--regularizationStrength 0.0`.
- Output: `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_NPMonotonicity/`

## Headline numbers
- Fit converged: edm = 7.9e-13, saturated p-value 61.66%, total 609s.
- Regularizer integrated: `nllvalreduced − (ln+lc+lbeta) = 0.047`, exactly matches the per-term hinge accounting.

## Postfit pulls (real data, τ=0)
| Nuisance | θ | physical value |
|---|---|---|
| `scetlibNPgammaLambda2`        | +9.14  | λ₂ = −0.217 |
| `scetlibNPgammaLambda4`        | −8.08  | λ₄ = +0.061 |
| `scetlibNPgammaLambdaInf`      | −259.2 | λ∞ = +133.08 |
| `chargeVgenNP0scetlibNPZlambda2`        | +2.16  | Λ₂ = +0.790 |
| `chargeVgenNP0scetlibNPZdelta_lambda2`  | −0.76  | ΔΛ₂ = +0.110 |
| `chargeVgenNP0scetlibNPZlambda4`        | −5.53  | Λ₄ = −0.216 |
| `pdfAlphaS`                    | (blinded; carries random offset) | absolute pull NOT meaningful — only Δ between configs and σ_post are informative |

## Wall-term breakdown at the postfit point (criterion b)
| Term | Penalty | Status |
|---|---|---|
| CS λ₂ ≥ 0 (small-bT positivity hinge) | **0.047** | fires — λ₂ = −0.217 |
| CS λ₄ ≥ −√(3 λ₂ λ₆) monotonicity | 0 | satisfied; floor = 0 after λ₂-clamp, λ₄ > 0 |
| TMD c₁(y=0) ≥ −√(20 Λ₆ L₂(0)) | 0 | margin +0.347 |
| TMD c₁(y=2.5) ≥ −√(20 Λ₆ L₂(2.5)) | 0 | margin +3.258 |
| TMD L₂(y) ≥ 0 at both y | 0 | L₂(0)=0.79, L₂(2.5)=1.48 |

## Findings
**Mechanics**: the regularizer module loads, classes resolve via rabbit's importlib path, parameter lookup against `indata.systs` succeeds, gradient flows through to a converged minimum. End-to-end pipeline works.

**Physics — criterion (b) alone is too permissive as a sole constraint.** Once λ₂ is clamped to 0 inside the CS wall's sqrt, the monotonicity wall for λ₄ becomes "λ₄ ≥ 0" (trivially satisfied here). The TMD c₁(y)³ term *grows fast* with L₂(y), so as the fit pushes Λ₂ up (it went to 0.79), the floor on c₁ (which is what bounds Λ₄ from below) loosens — Λ₄ can drift very negative without triggering. The fit found a corner of the feasible region with: λ₂ slightly negative (only term that fires), λ∞ off the charts, Λ₄ negative, and pdfAlphaS pulled by ~5σ — none caught by criterion (b).

**τ=0 issue**: even where the wall fires, the multiplier is e²·⁰=1 and the violation² is O(0.05) NLL units against data NLL ~22k — essentially noise. To make the wall matter we need τ ≳ 2–3 just to register against fluctuations, more like 4–5 to dominate.

## Implications for next steps
- Bumping τ alone won't fix the pathology — the wall is happy where the fit landed; it just allows physically unreasonable values that satisfy the (loose) monotonicity geometry. We need additional constraint structure.
- Note: (b) monotonicity is **strictly tighter** than (a) sign-preservation on both walls ($\sqrt{3}<\sqrt{4}$ and $\sqrt{20}<\sqrt{36}$ ⇒ (b)'s floor is higher / closer to zero). So switching to (a) would *loosen* the wall, not tighten it — opposite of what we want. (Earlier draft of this README incorrectly said (a) is tighter; corrected.)
- Plausible next moves:
  1. Add a soft Tikhonov restraint (per-nuisance Gaussian-like penalty with σ much wider than the lattice prior, say σ=5–10 in rabbit-θ units) on top of the wall. Anchors parameters in the physical neighborhood without re-imposing the lattice constraint.
  2. Re-introduce the Gaussian priors selectively — e.g. only on λ∞, ΔΛ₂ (which the wall doesn't constrain at all) — keeping λ₂, λ₄, Λ₂, Λ₄ free except for the wall.
  3. Bump τ to (e.g.) 4–5 so the existing hinges have teeth, then iterate from there. Won't catch the pathology where the wall is silent, but at least the λ₂≥0 hinge and the (small) TMD c₁(y=0) violation get pushed back.

## Pointers
- Regularizer module: `main/WRemnants/wremnants/postprocessing/np_monotonicity.py`
- Derivation: `agents/knowledge/30_physics_global/np_parametrization_constraints.md`
- Setup script used: `/tmp/test_np_monotonicity_setup.sh` (rebuildable from this README)
- Fit script used: `/tmp/test_np_monotonicity_fit.sh`
- Inputs: `/ceph/submit/.../260511_npwall/ZMassDilepton.hdf5` and `.../fitresults.hdf5`
