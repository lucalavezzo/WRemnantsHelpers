# Runlog — 260430_debug 1D vs 4D

## 2026-04-30 / 2026-05-01

### Goal
Reproduce each of the 9 fits in `$MY_OUT_DIR/260430_debug/` with `--fitvar ptll`
only, then compare λ₂/λ₄ pulls and saturated-projection p-values to the
existing 4D versions.

### What ran
- Wrapper: `/tmp/run_ptll_debug_fits.sh` — runs `setupRabbit.py` + `rabbit_fit.py`
  for each postfix, dropping `--computeSaturatedProjectionTests` (1D saturated
  covariance non-positive-definite).
- Initial run launched 2026-04-30 18:24 with `set -e`; aborted on first fit's
  Cholesky failure in `save_hists` from `--computeSaturatedProjectionTests`.
  Wrapper updated to `set +e` and the flag dropped, then re-launched
  2026-04-30 18:27. All 9 done by 18:47.
- Mid-session fix: `setupRabbit.py:941` `--fakelumi default=1.1` → `default=0`
  (bug — non-fakelumi variants were silently carrying a free `fakelumi` norm).
  All 9 fits re-launched 2026-05-01 08:43, done by 08:58.
- `_scetlibNoConstraint` reproducible only via local source patch in
  `wremnants/postprocessing/rabbit_theory_helper.py` (lines 751, 880, 979 —
  uncomment `noConstraint=True`). Patched, re-ran the single 1D fit
  2026-05-01 09:06–09:08, then reverted. Pulls now match expected
  unconstrained behaviour (large central value, large error).

### Output dirs
`$MY_OUT_DIR/260430_debug/ZMassDilepton_ptll_*` — 9 directories, each with
`ZMassDilepton.hdf5` and `fitresults.hdf5`.

### Logs
- `logs/ptll_debug_fits_260430_182451.log` — initial (crashed) attempt.
- `logs/ptll_debug_fits_260430_182736.log` — first full pass (later
  superseded by the fakelumi-fix re-run).
- `logs/ptll_debug_fits_260501_084355.log` — re-run after fakelumi fix.
- `logs/scetlibNoConstraint_260501_090633.log` — single-fit re-run with
  scetlib unconstrained patch.

### Extraction scripts
- `/tmp/extract_pulls.py` — pulls of `chargeVgenNP0scetlibNPZlambda{2,4}`.
- `/tmp/extract_pvalues.py` — 4D projection saturated chi2 from the
  per-fit `fitresults.hdf5` `mappings['Project ch0 ptll']`; 1D saturated
  chi2 from rabbit_fit log.

### Final products
- `results_table.tex` — combined pulls + saturated p-values, 7 rows
  (dropped: plain `LatticeNoConstraints`, and `_fakelumi_noAlphaS`).

### Key observations
- λ₂/λ₄ pulls in 1D are systematically smaller in magnitude than 4D
  (ptll alone has less constraining power on the NP shape parameters).
- `Unconstrained NP` 1D row exposes the genuinely unconstrained scetlibNP:
  λ₂ pull blows up to +20 ± 16 and λ₄ to +19 ± 26.
- Saturated p-values are consistently larger in 1D than in 4D for every
  configuration (1D fit has more freedom relative to the fewer bins).

## 2026-05-04

### Why σ(α_s) shrinks when SCETlib NP priors are removed (4D)

Question raised: in the 4D fit, scetlibNoConstraint gives Δσ(α_s) = −3.2 %
relative to nominal even though the only change is *removing* Gaussian
priors on λ₂/λ₄. Verified with `rabbit_print_impacts.py`:

- Nominal 4D Total σ(α_s) = 0.55164
- scetlibNoConstraint 4D Total σ(α_s) = 0.53407 (−3.2 %)
- Largest group reductions: `resum` 0.4294 → 0.4049,
  `resumNonpert` 0.3840 → 0.3554. `resumTransitionFOScale` rises
  0.0330 → 0.0851 (uncertainty migrates between groups, but with weaker
  α_s correlation on net).

In a purely linear/Gaussian profile-likelihood fit, removing a Gaussian
prior can never *reduce* σ(POI). The observed reduction is therefore a
non-linear effect, and the saturated projection p-value confirms it:
2.54 % (nominal) → 60.17 % (scetlibNoConstraint). The nominal fit is
in real tension with data; the priors are pinning λ₂/λ₄ at zero where
the SCETlib NP basis cannot describe the ptll shape, and the tension
sloshes into the resum/transition sector and into α_s.

When the priors are released, λ₂/λ₄ pull to (+3.4, −16.0), the model
fits the data well, and the local Hessian curvature is re-evaluated at
this new minimum. Cross-derivatives H_{α_s, resumNonpert} weaken
(the NP shape is now resolved by λ₂/λ₄ themselves rather than mediated
through α_s), so the global impact assigned to `resum*` drops and
σ(α_s) follows.

Interpretation: the −3.2 % is not a real gain in α_s sensitivity; it is
a re-evaluation at a non-linear minimum the priors are warning us
against. A model whose central NP basis cannot reach the data's
preferred shape will show inflated σ(α_s) at the prior, and an
artificially small σ(α_s) once the priors are removed. Promoted to
`agents/knowledge/20_frameworks/profile_likelihood_pitfalls.md`.

### Table v2: split 4D/1D, more NPs, physical-shift columns

`results_table.tex` rebuilt by `scripts/build_tables.py` so that:

- 4D and 1D are separate tables (1D row no longer crammed next to 4D).
- Six NP columns: λ₂, δλ₂, λ₄, γ_Λ₂, γ_Λ₄, γ_Λ∞ (was just λ₂, λ₄).
- Each NP cell is `pull / physical`. `Pull` is postfit value ± unc in
  units of the prior σ (prefit 0±1). `Physical` is `pull × kfactor_scale`
  in nominal-template σ units; cells with `kfactor_scale = 1` show
  only the pull (no `/`). This makes scaled configs comparable to
  unscaled — a 1σ pull in `Λs×5` is a 5× larger physical template
  shift than a 1σ pull in nominal.
- kfactor convention: γ NPs carry a baseline ×10 from
  `LatticeNoConstraints` (`add_gamma_np_uncertainties`). On top of
  that, `--scaleParams REGEX=FACTOR` multiplies the kfactor of any
  NP whose Up/Down name matches REGEX (`re.search`). So:
    * `chargeVgenNP0scetlibNPZlambda4Scale5p0`: `chargeV...lambda4` ×5 only.
    * `chargeVgenNP0scetlibNPScale5p0`: all 3 `chargeV...` NPs ×5.
    * `scetlibScale5p0`: all 6 NPs ×5 (so γ effective scale = ×50).
- 4D table includes the `Δpull(α_s)` and `Δσ(α_s)` columns (relative
  to Nominal). 1D table omits these (α_s is too poorly constrained
  in 1D to be informative across configs).

Driver scripts moved into the study (`scripts/`) so the build is
self-contained; no leftover `/tmp` dependencies.

### Grid expansion: 10 new 4D configs + Asimov column (2026-05-04)

Driver: `scripts/run_4d_grid.sh`. Idempotent (skip-if-exists per stage).
For each of 18 configs (8 existing + 10 new) the script runs:
  setupRabbit (skipped if `ZMassDilepton.hdf5` already there)
  → rabbit_fit `-t  0` → `fitresults.hdf5`
  → rabbit_fit `-t -1` → `fitresults_asimov.hdf5`
The asimov result is dropped into the same dir via `--outname` so the
input tensor isn't duplicated (~1 GB each).

10 new configs (all 4D, all `--npUnc LatticeNoConstraints`):
- `Λ4×5 + fakelumi`
- `all NP asym. + fakelumi`
- `all NP ×5 + fakelumi`
- `all NP unconstrained + fakelumi`
- `all NP ×5, γ_Λ∞ default` — `--scaleParams 'scetlib(?!.*LambdaInf)=5.0'`
- `all NP ×5, γ_Λ∞ default + fakelumi`
- `all NP unconstrained, γ_Λ∞ default` — `--noConstrainParams 'scetlibNP(?!.*LambdaInf)'`
- `all NP unconstrained, γ_Λ∞ default + fakelumi`
- `all NP ×2`
- `all NP ×2 + fakelumi`

Negative-lookahead regex `scetlib(?!.*LambdaInf)` matches the 5
non-Λ∞ NPs and lets `γ_Λ∞` keep its `LatticeNoConstraints` baseline
(kfactor = 10, prior θ ~ N(0,1)). All configurations now driven by
CLI flags only — no source patches required (uses the new
`--noConstrainParams` flag added to `setupRabbit.py` 2026-05-04).

Table: `build_tables.py` adds an "σ(α_s) Asimov" column (×2 for the
analysis 10⁻³ convention) sourced from `fitresults_asimov.hdf5` next
to each config's data result; missing fits show "—".

Launched in tmux session `260430_4d_grid` 2026-05-04 14:33 EDT, log
at `logs/run_4d_grid_260504_143327.log`.

Two issues hit and resolved during the run:

1. **`--fitvar` parsing bug.** Initial script used
   `--fitvar ptll yll cosThetaStarll_quantile phiStarll_quantile`
   (4 separate args). `setupRabbit.py:3320` does
   `fitvar = args.fitvar[i].split("-")` per channel — i.e., each entry
   is a *single channel's axes joined by `-`*. So the script silently
   produced 1D inputs (just `ptll`) for the 10 new configs, into
   1D-named dirs that couldn't be found by the 4D rabbit_fit step.
   Configs 1-8 were unaffected (their setupRabbit was skipped).
   Fixed by passing one dash-separated string:
   `--fitvar 'ptll-yll-cosThetaStarll_quantile-phiStarll_quantile'`.
   10 orphan 1D dirs were left in
   `$MY_OUT_DIR/260430_debug/ZMassDilepton_ptll_LatticeNoConstraints_<postfix>`
   (~42 MB total); safe to remove (don't collide with the original 9
   1D fits which use disjoint postfixes).

2. **Cholesky failure in saturated post-processing.** With
   `--computeSaturatedProjectionTests` enabled, heavily-stressed
   configs (`scetlibScale5p0_fakelumi`, expected to also affect
   `scetlibNoConstraint_fakelumi` and the LambdaInf-default variants)
   crash in `save_hists → fitter_saturated.edmval_cov` with
   "Hessian is not positive-definite" because the saturated covariance
   is singular. The crash truncated `fitresults.hdf5` to ~27 KB
   (only `meta`, no `results`). Same pathology the 1D fits hit — the
   README already noted dropping the flag for 1D. Fixed by removing
   `--computeSaturatedProjectionTests` from `COMMON_FIT_DATA` for the
   4D grid run; new configs show "—" for Sat. p in the table. The 8
   pre-existing 4D configs already have sat-p in their stored
   fitresults.hdf5 from earlier (Apr 30) so their column entries are
   preserved.

Final grid relaunched 18:42 EDT, log
`logs/run_4d_grid_260504_184249.log`.
