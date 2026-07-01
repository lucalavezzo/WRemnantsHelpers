# runlog — fitAlphaSRapidityDecorr_freeze_partial_LRT

## 2026-04-30 — study set up, freeze refits launched

### Reference
- Baseline (no freeze, decorrelated, blinded as group, fullNll on):
  `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260429_fitAlphaSRapidityDecorr/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_fitAlphaSRapidityDecorr_renamed_LambdaScale5p0/fitresults_unblindedAsGroup.hdf5`

Reference fit command (recovered from `meta_info.command`):
```
rabbit_fit.py .../ZMassDilepton.hdf5 --computeVariations \
  -m Project ch0 ptll yll -m Project ch0 ptll -m Project ch0 yll \
  -m Project ch0 cosThetaStarll_quantile -m Project ch0 phiStarll_quantile \
  --computeHistErrors --computeHistImpacts --doImpacts \
  -o .../ZMassDilepton_ptll_..._LambdaScale5p0/ \
  --globalImpacts --saveHists --saveHistsPerProcess \
  --blindingGroup '^.*AlphaS.*$' -v 4 -t 0 --postfix unblindedAsGroup --fullNll
```

### Driver pattern
For each group in `scripts/groups.yaml`, the driver `scripts/run_freeze_groups.py`:
1. parses the reference command from the baseline file's `meta_info`
2. strips `--postfix unblindedAsGroup` and any prior `--freezeParameters`
3. appends `--postfix freeze_<group>_decorr --freezeParameters <regex...>`
4. writes a wrapper to `/tmp/run_freeze_<group>_<stamp>.sh` (sources
   `/opt/venv` then `setup.sh`, prints BEGIN/DONE_OK)
5. launches via `nohup singularity run ...` with logs in
   `WRemnantsHelpers/logs/freeze_<group>_<stamp>.log`

Output lands in the same dir as the baseline, named
`fitresults_freeze_<group>_decorr.hdf5`.

### Groups (rationale)
Defined in `scripts/groups.yaml`, all motivated by top of `spread×pull` table
on the unfrozen baseline:
- `pdf_mb`: `mb_up`, `pdfMSHT20mbrange.*`
- `pdfCT18Z`: `pdf\d+CT18Z.*`
- `pdf_mb_and_CT18Z`: union of the two
- `scetlibNP`: `.*scetlibNP.*`, `chargeVgenNP.*`
- `resumTNP`: `resumTNP_.*`
- `prefire_stat`: `CMS_prefire_stat_.*`
- `pixel_multiplicity`: `pixel_multiplicity_.*`
- `fsr_photos`: `horacelophotos.*`, `.*FSR.*`
- `qcdscale_helicity`: `QCDscaleZfine_.*`
- `all_top_suspects`: union of all of the above

### Dry-run sanity (one wrapper inspected)
`/tmp/run_freeze_pdf_mb_260430_181412.sh` — `--freezeParameters` is
space-separated as required by `nargs="+"` (AGENTS.md gotcha), regex is
quoted, postfix is unique. OK to launch.

### Launch — 2026-04-30 18:15:23
All 10 groups launched in parallel via singularity-nohup. Logs in
`WRemnantsHelpers/logs/freeze_<group>_260430_181523.log`. Output dir is the
same as the baseline; filenames `fitresults_freeze_<group>_decorr.hdf5`.
Each fit confirmed past TF init at 18:15:24 (BEGIN line + cpu_feature_guard).
Expected ~10-15 min per fit (per `projection_pvalues` precedent).

Groups launched: pdf_mb, pdfCT18Z, pdf_mb_and_CT18Z, scetlibNP, resumTNP,
prefire_stat, pixel_multiplicity, fsr_photos, qcdscale_helicity,
all_top_suspects.

### Wave-1 results — 2026-04-30 18:43 (partial)

**Status of the 10 launched fits at +27 min:**
- DONE_OK (5): scetlibNP (18:36), pixel_multiplicity (18:40), prefire_stat
  (18:40), fsr_photos (18:41), resumTNP (18:41).
- CRASHED (2): `pdfCT18Z`, `qcdscale_helicity` — both with
  `pthread_create() failed (ret == 11 EAGAIN)` at 18:27. Cause: launching
  10 TF fits in parallel saturated the host's thread limit.
- STILL ITERATING (3): `pdf_mb`, `pdf_mb_and_CT18Z`, `all_top_suspects`.
  Loss has been pinned at `24902.20621712937` for >300 iterations
  (gradient-norm criterion not converging — the trust-krylov minimizer
  oscillates in numerical noise around the minimum). Output files exist
  only as 25 kB placeholders; `workspace.write` not yet reached. **These
  are the most interesting freeze groups (mb / PDF) per the spread×pull
  table; need to revisit how they're driven.**

**Per-group table from the 5 successful fits (NDF=20 POIs, baseline NLL_red
= 24897.26, spread = 0.448, rms = 0.107, median sigma_POI = 0.657):**

| group               | spread | rms   | spread/base | ΔNLL_red |
|---------------------|--------|-------|-------------|----------|
| baseline            | 0.448  | 0.107 | 1.00        | 0        |
| **scetlibNP**       | 0.643  | 0.190 | **+44%**    | **+61.6** |
| resumTNP            | 0.452  | 0.108 |  +1%        |  +0.1    |
| prefire_stat        | 0.458  | 0.109 |  +2%        |  +4.9    |
| **pixel_multiplicity** | 0.362 | 0.092 | **−19%**  | **+26.0** |
| fsr_photos          | 0.452  | 0.107 |  +1%        |  +0.9    |

**Interpretation:**
- **scetlibNP / chargeVgenNP** is doing real work in the baseline: ΔNLL_red
  = +61.6 when frozen, and the per-bin αS spread *increases* by 44%. This
  is the opposite of "absorbing" — the postfit pulls on scetlibNP/chargeVgenNP
  (>1σ on multiple parameters) are *helping* the fit accommodate y-dependent
  shape mismodeling. With them frozen, αS has to soak up that residual per
  bin → spread grows. So scetlibNP is *coupled* to the αS-y tension but is
  not the absorber that masking would make αS-y consistent.
- **pixel_multiplicity** is a small but real absorber: −19% spread, ΔNLL_red
  +26. Consistent with the +0.95σ pull on `pixel_multiplicity_syst_var47`
  in the impact ranking.
- **prefire_stat, resumTNP, fsr_photos** are essentially innocent of the
  per-bin αS tension. Their >1σ pulls (in `prefire_stat`) cost the fit
  +4.9 NLL but don't change the αS spread.

**Outstanding (require relaunch with sequential / smaller parallelism):**
- `pdf_mb`, `pdfCT18Z`, `pdf_mb_and_CT18Z`, `qcdscale_helicity`,
  `all_top_suspects`. These are the *most* informative groups per the
  impact ranking. Need either (a) sequential relaunch to avoid pthread
  saturation, (b) a thread cap (`OMP_NUM_THREADS=4` etc.) inside the
  wrapper, or (c) for the 3 stuck fits, an investigation into why the
  trust-krylov minimizer fails to converge on these freezes (could be a
  near-degenerate Hessian after freezing the m_b family).

### Root-cause for the 3 stuck fits — 2026-05-01

Investigating the stuck `pdf_mb`, `pdf_mb_and_CT18Z`, `all_top_suspects`
logs revealed a real bug in `rabbit/fitter.py:match_regexp_params`. The
log lines:
```
DEBUG:fitter.py: Freeze params with ['mb_up', 'pdfMSHT20mbrange.*', ...]
DEBUG:fitter.py: Updated list of frozen params: [b'mb_up']
```
showed every regex was silently dropped — only `mb_up` was actually frozen
(same for the two other groups, all of which had `mb_up` first as an exact
parameter name).

Reading [`rabbit/fitter.py:22-39`](../../../../main/WRemnants/rabbit/rabbit/fitter.py#L22-L39):
```python
exact_matches = [...]
if exact_matches:
    return exact_matches    # <-- returns *only* exact matches
# regex pass never runs
```
i.e. the helper is **all-exact-OR-all-regex**, not "exact-first then
regex" as `agents/knowledge/20_frameworks/nominal_workflow.md` claimed.

**Why the 5 successful fits worked:** every regex in their group lists was
non-exact (e.g. `'.*scetlibNP.*'`, `'CMS_prefire_stat_.*'`, etc.), so the
exact-match list was empty and the regex pass ran normally.

**Why the 3 looped:** with only `mb_up` frozen, the loss reached
`24902.20621712937` in 42 iterations (ΔNLL=+4.94 vs unfrozen baseline
24897.26 — exactly the cost of clamping a NOI with -1.5σ pull) and then
the trust-krylov minimizer ran for 217k+ iterations without certifying
the gradient-norm criterion. Loss bit-stable, gradient noise above
tolerance. Real but separate issue: when a NOI that wants to move is
frozen alone, the trust region collapses; freezing the *full* m_b family
should recondition the postfit Hessian.

**Fix applied 2026-05-01:**
- Patched `rabbit/fitter.py:match_regexp_params` to return the union of
  exact and regex matches (de-duplicated, parameter-order preserved).
  Unit-tested against mixed/all-exact/all-regex/single/empty/overlap
  cases.
- Updated `agents/knowledge/20_frameworks/nominal_workflow.md` to describe
  the new (correct) behavior plus a historical-bug note for users
  re-examining pre-2026-05-01 fits.

**Cleanup:** killed the 3 stuck PIDs (2345004, 2345062, 2345266 wrappers
+ 2345499, 2345543, 2345604 python children) at 2026-05-01 09:01.

### Sequential relaunch — 2026-05-01 09:07-09:35

Ran the 5 outstanding groups back-to-back inside one singularity instance
(new `--sequential` mode in the driver) — avoids the pthread saturation
that crashed the parallel pdfCT18Z and qcdscale_helicity earlier. Wall
times:

| group | start | end | duration |
|---|---|---|---|
| pdf_mb | 09:07:14 | 09:13:58 | 6m 44s |
| pdfCT18Z | 09:13:58 | 09:19:37 | 5m 39s (58 params frozen) |
| pdf_mb_and_CT18Z | 09:19:37 | 09:25:18 | 5m 41s (61 frozen) |
| qcdscale_helicity | 09:25:18 | 09:31:06 | 5m 48s |
| all_top_suspects | 09:31:06 | 09:35:45 | 4m 39s (~265 frozen) |

`DONE_SEQ_OK` at 09:35:45. All 10 fitresults files now ~200-235 MB each.

### Final freeze table — 2026-05-01 09:36

(Baseline: 20 POIs, NLL_red = 24897.26, spread = 0.448, rms = 0.107.)

| group | spread | spread/base | ΔNLL_red |
|---|---|---|---|
| baseline | 0.448 | 1.00 | 0 |
| **pdfCT18Z** | 0.351 | **0.78** (−22%) | **+1.0** |
| **pixel_multiplicity** | 0.362 | **0.81** (−19%) | +26.0 |
| resumTNP | 0.452 | 1.01 | +0.1 |
| fsr_photos | 0.452 | 1.01 | +0.9 |
| qcdscale_helicity | 0.452 | 1.01 | +17.0 |
| pdf_mb_and_CT18Z | 0.456 | 1.02 | +6.0 |
| prefire_stat | 0.458 | 1.02 | +4.9 |
| **pdf_mb** | 0.524 | **1.17** (+17%) | +4.2 |
| **all_top_suspects** | 0.633 | **1.41** (+41%) | **+432** |
| **scetlibNP** | 0.643 | **1.44** (+44%) | +62 |

**Interpretation:**

1. **pdfCT18Z** is the dominant *absorber*: −22% spread for almost zero
   NLL cost (+1.0). Translation: the CT18Z PDF eigendirections have
   non-trivial y-dependent shape that the per-bin α_S is using as a
   relief valve. The data has very weak preference for moving these
   directions, so removing them (a) is essentially free, and (b)
   collapses ~1/4 of the spread. **This is the canonical PDF–α_S
   entanglement result.**
2. **pixel_multiplicity** is a smaller but genuine absorber: −19% spread
   at modest cost (+26 NLL). Real localised effect, not masking.
3. **scetlibNP / chargeVgenNP** is *not* an absorber, it is a coupled
   axis competing with α_S for the same shape information. Freezing it
   alone increases the spread by 44% and costs +62 NLL. This is exactly
   the inverse of the impact-ranking intuition: large differential
   impact + large pull doesn't mean the parameter is masking — here it
   means it's load-bearing.
4. **m_b family alone** behaves like scetlibNP: +17% spread, +4 NLL.
   Coupled, not absorbing. The combined `pdf_mb_and_CT18Z` returns the
   spread to ~baseline (CT18Z tightens, m_b loosens, they cancel).
5. **all_top_suspects** (the everything-frozen sanity test): spread
   *blows up* by 41% and NLL increases by 432. Confirms the picture —
   the bulk of the per-bin α_S spread is being held *down* by NP/m_b
   freedom, with CT18Z + pixel_multiplicity providing a smaller real
   absorption channel.
6. **resumTNP, fsr_photos, prefire_stat, qcdscale_helicity** are
   essentially innocent of the spread (≤2% changes), though their NLL
   costs (4.9, 17) are non-trivial — those parameters are pulled by the
   data but the pulls don't translate into y-dependent α_S movement.

**Net answer to the original study question:** the per-bin α_S spread
is dominated by PDF–α_S entanglement through the CT18Z eigendirections
(real) and a modest pixel_multiplicity contribution. NP / m_b are *not*
the absorbers — they are coupled-but-load-bearing and the impact-ranking
heuristic over-attributed the spread to them.

### Open follow-ups
- The full Wilks LRT against an inclusive baseline (p ≈ 0%) attributes
  the per-bin preference to the *combination* of these directions; a
  proper partial-LRT against inclusive-frozen partner fits would split
  the LRT into "absorbed by group G" vs "remaining tension". Inclusive
  freeze refits not yet run; deferred.
- Worth checking whether PDF protocol (freeze CT18Z eigendirections, or
  switch to a single PDF set with an αs-correlated variation rather
  than the 29-direction CT18Z ensemble + MSHT20 m_b range hybrid)
  collapses the LRT. The freeze-CT18Z spread of 0.351 / median σ_POI
  of 0.66 = 0.53 — already inside 1σ, suggesting most of the
  decorrelation preference would go away under a tightened PDF
  treatment.

### Analysis once fits finish
```
python3 scripts/analyze_freeze_results.py \
  --baseline /ceph/.../fitresults_unblindedAsGroup.hdf5 \
  --frozen pdf_mb=/ceph/.../fitresults_freeze_pdf_mb_decorr.hdf5 \
           pdfCT18Z=/ceph/.../fitresults_freeze_pdfCT18Z_decorr.hdf5 \
           ...
  [--inclusive /ceph/.../inclusive_fitresults.hdf5]
```
Or, since all freeze outputs sit in the same dir:
```
DIR=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260429_fitAlphaSRapidityDecorr/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_fitAlphaSRapidityDecorr_renamed_LambdaScale5p0
python3 scripts/analyze_freeze_results.py \
  --baseline $DIR/fitresults_unblindedAsGroup.hdf5 \
  --frozen $(for g in pdf_mb pdfCT18Z pdf_mb_and_CT18Z scetlibNP resumTNP \
                       prefire_stat pixel_multiplicity fsr_photos \
                       qcdscale_helicity all_top_suspects; do \
              echo "${g}=${DIR}/fitresults_freeze_${g}_decorr.hdf5"; \
            done)
```

## 2026-05-03 — partial-LRT inclusive partner fits launched

### Motivation
Picked the study back up. The decorrelated freeze table tells us how
much each group moves the *spread*; the partial-LRT tells us how much
each group carries the *significance* of decorrelation in chi² units.

### Discovery
The `run_freeze_groups.py` driver claimed inclusive partner refits
"would require a different ParamModel / setupRabbit step" and refused
mode='inclusive'. Inspecting `meta_info.command` of the inclusive
baseline `_nominal_LambdaScale5p0/fitresults_unblindedAsGroup.hdf5` and
the decorr baseline shows the rabbit_fit.py command is *identical*
between the two — only the input ZMassDilepton.hdf5 differs (the
parameter model is baked into the histmaker output). So the driver was
already general enough; removed the NotImplementedError, added
`--mode inclusive` purely as a postfix/output-naming tag, point
`--baseline` at the inclusive baseline and the same freeze regexes
apply.

Inclusive baseline (1 POI, `pdfAlphaS`):
```
/ceph/.../260429_fitAlphaSRapidityDecorr/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_nominal_LambdaScale5p0/fitresults_unblindedAsGroup.hdf5
```

### Launch
Sequential wrapper:
```
agents/studies/fitAlphaSRapidityDecorr_freeze_partial_LRT/scripts/run_freeze_seq_260503_110202.sh
```
Log: `logs/freeze_seq_260503_110202.log`. Same 10 groups as the
decorr run; outputs: `fitresults_freeze_<group>_inclusive.hdf5` in the
`_nominal_LambdaScale5p0/` directory. Ran 11:02 → 12:09 EDT, 10/10 OK.

### Results — 2026-05-03 12:14

Baseline LR test (Λ5p0, NP priors widened ×5):
```
chi² = 2·(NLL_inc - NLL_dec) = 24.09,  ndf = 19,  p = 0.193
```

The decorrelation preference under Λ5p0 is **not significant**. The
runlog's earlier "p ≈ 0%" recollection was from the un-scaled fit;
the Λ-scale ×5 prior widening on SCETlib NP largely absorbed the LR
signal too.

Partial-LRT table (Δχ² = χ²(G frozen) − χ²(unfrozen); Δχ² > 0 ⇒ LRT
grew when G frozen ⇒ G was masking; Δχ² < 0 ⇒ LRT shrank ⇒ G was
carrying):

| group | χ²(frozen) | Δχ² | p | spread/base |
|---|---|---|---|---|
| baseline | 24.09 | — | 0.193 | 1.000 |
| pdf_mb | 25.20 | +1.10 | 0.154 | 1.169 |
| pdfCT18Z | 26.06 | +1.97 | 0.128 | 0.784 |
| pdf_mb_and_CT18Z | 27.42 | +3.33 | 0.095 | 1.017 |
| scetlibNP | 25.20 | +1.11 | 0.154 | 1.435 |
| resumTNP | 24.05 | −0.04 | 0.194 | 1.008 |
| prefire_stat | 24.32 | +0.23 | 0.184 | 1.021 |
| pixel_multiplicity | 22.84 | −1.26 | 0.245 | 0.808 |
| fsr_photos | 24.07 | −0.02 | 0.193 | 1.009 |
| qcdscale_helicity | 24.03 | −0.06 | 0.195 | 1.008 |
| **all_top_suspects** | **54.91** | **+30.82** | **2.4e-5** | 1.412 |

**Interpretation:**

1. **No single group carries significant LR preference** — all
   individual |Δχ²| ≤ 2 except all_top_suspects. The diffuse
   decorrelation preference is genuinely small under Λ5p0.
2. **PDF eigendirections + SCETlib NP are mild absorbers**
   (Δχ² > 0). CT18Z + m_b together absorb ~3.3 χ² of
   differential preference; SCETlib NP absorbs ~1 χ². Confirms the
   freeze-study's "load-bearing" label, now in χ² units.
3. **pixel_multiplicity is the only meaningful LR carrier**
   (Δχ² = −1.26): freezing it shrinks the LR preference. Small.
4. **all_top_suspects is qualitatively different**: Δχ² = +31,
   p ≈ 2·10⁻⁵. With every absorbing/load-bearing direction frozen,
   the residual differential preference is forced into the per-bin
   α_S POIs and the LR test becomes very significant. This is the
   "stat-only-style" comparison: it confirms there *is* differential
   information in the data, but Λ5p0 + the full nuisance model is
   already adequate to absorb almost all of it.

**Net answer to the original study question (under Λ5p0):** The data
does not significantly prefer per-bin α_S over a single common α_S.
The earlier "p ≈ 0" came from the un-scaled NP fit; the prophylactic
×5 widening on SCETlib NP λ-parameters is sufficient to bring the LR
test into the noise. CT18Z, m_b, and SCETlib NP are mild absorbers;
pixel_multiplicity is the only group with a (small) genuine LR
contribution. No further uncertainty inflation appears motivated for
the per-bin α_S story under this baseline.

**Open follow-ups:**
- Re-run the partial-LRT against the un-Λ-scaled fit to recover the
  large-LRT picture and identify which absorbers / carriers were
  active before the prior widening was applied. That would quantify
  what Λ5p0 actually fixed.
- The PDF protocol question (single PDF set + α_S-correlated
  variation, vs the CT18Z 29-direction + MSHT20 m_b range hybrid)
  remains as study 2; under Λ5p0 the urgency is lower since the LR
  preference is already non-significant.

### Analysis (after fits finish)
Extended `analyze_freeze_results.py` with `--inclusive-frozen
GROUP=PATH ...`. For each group it computes
`chi² = 2·(NLL_incl_G − NLL_decorr_G)` (ndf = 19) and prints
`Δchi² = chi²(G frozen) − chi²(unfrozen)`.

Reading guide (Δχ² = χ²(G frozen) − χ²(unfrozen)):
- **Δchi² < 0** (LRT shrank when G frozen) → G *carries* the
  decorrelation preference. Freezing it removes its contribution to
  the LR significance.
- **Δchi² ≈ 0** → G is innocent of the LRT (regardless of spread move).
- **Δchi² > 0** (LRT grew when G frozen) → G was *masking* / absorbing
  tension; load-bearing. Freezing it reveals more residual differential
  preference. Expectation from spread table: scetlibNP, mb.

(An earlier draft of this guide had the signs inverted — corrected
2026-05-03 after the fits ran. The interpretation in the results
section above is the corrected version.)

Run command once partial fits land:
```
DDIR=/ceph/.../_fitAlphaSRapidityDecorr_renamed_LambdaScale5p0
IDIR=/ceph/.../_nominal_LambdaScale5p0
python3 scripts/analyze_freeze_results.py \
  --baseline $DDIR/fitresults_unblindedAsGroup.hdf5 \
  --inclusive $IDIR/fitresults_unblindedAsGroup.hdf5 \
  --frozen $(for g in pdf_mb pdfCT18Z pdf_mb_and_CT18Z scetlibNP resumTNP \
                       prefire_stat pixel_multiplicity fsr_photos \
                       qcdscale_helicity all_top_suspects; do \
              echo "${g}=${DDIR}/fitresults_freeze_${g}_decorr.hdf5"; \
            done) \
  --inclusive-frozen $(for g in pdf_mb pdfCT18Z pdf_mb_and_CT18Z scetlibNP resumTNP \
                       prefire_stat pixel_multiplicity fsr_photos \
                       qcdscale_helicity all_top_suspects; do \
              echo "${g}=${IDIR}/fitresults_freeze_${g}_inclusive.hdf5"; \
            done)
```

## 2026-05-03 12:30 — corrected conclusion + cross-checks

### Headline finding (CORRECTED — supersedes the "p ≈ 0%" recollection)

The per-rapidity-bin α_S decorrelation LR test is **not significant
under either baseline**:

| baseline | χ² | ndf | p-value |
|---|---|---|---|
| un-scaled (`scaleParams=1`) | 22.6 | 19 | **0.18** |
| Λ5p0 (`chargeVgenNP0scetlibNP=5`) | 24.09 | 19 | **0.19** |

The Λ5p0 inflation barely moves the LR result (Δp ≈ 0.01). The two
baselines are both in the regime "mild residual tension, χ²/ndf ≈ 1.2,
not significant".

### Origin of the earlier "p ≈ 0%" recollection — script display artifact

`scripts/plotting/plot_alphaS_rapidity_decorr.py` has an MC-mode branch
that fires when `--data` is **not** passed:

```python
chi2_stat = 2 * (nll_inclusive - nll)        # the actual LR statistic
if args.result == "asimov":
    chi2_stat = 0
elif not args.data:                          # default for our invocation
    chi2_stat += ndf                         # 24.09 + 19 = 43.09
    chi2_label = r"\langle \chi^2/\mathrm{ndf} \rangle"
```

Without `--data`, the script adds `ndf` to the LR statistic before
computing the p-value, treating the input as if it were an Asimov
ΔNLL needing calibration to "expected real-data χ²". On a real-data
fit this *double-counts* the H₀ baseline:
- displayed χ² = 24.09 + 19 = 43.09 → p ≈ 0.0013 → "0%" rounded
- actual LR χ² = 24.09 → p = 0.193

The angle-bracket label `⟨χ²/ndf⟩` is the visual signal of the bumped
quantity. The user's original invocation hit this branch silently.

**Fix**: always pass `--data` to the plotting script for real-data
fits (`-t 0 --blindingGroup` in the rabbit_fit command). With it, the
plotting script and `analyze_freeze_results.py` agree to many digits.

### χ² independently verified three ways

For the Λ5p0 baseline (file `fitresults_unblindedAsGroup.hdf5` for
both decorr and inclusive):

```
LR test       : 2·(NLL_inc - NLL_dec)               = 24.09
Parm-level    : (α-α̂_WLS)' V_α^-1 (α-α̂_WLS)        = 24.092
Parm-level    : (α-α_inc·1)' V_α^-1 (α-α_inc·1)     = 24.092
```

All three agree. The WLS common α from the full 20×20 postfit
covariance comes out at **−9.0788**, matching the inclusive fit
(α = **−9.0790**) — a textbook Wilks asymptotic check.

Helper: `/tmp/check_chi2.py` (replicate by re-running it on the two
fitresults hdf5 files).

### The off-diagonal correlations are essential

Same fit, different metrics:

| metric | value | reading |
|---|---|---|
| spread / σ_total (extreme pair) | 0.68 | "looks consistent" |
| rms / σ_total (bulk) | 0.16 | "looks consistent" |
| **diagonal-only χ² with σ_total** | **0.5 / 19** | "wildly consistent" — *misleading* |
| **proper LR χ² (= full-cov parm χ²)** | **24.09 / 19** | mild tension, p=0.19 |

The 50× discrepancy between the diagonal-only and full-cov χ² is
because the 20 α POIs are heavily *anti-correlated* through shared
nuisances. A given nuisance shift moves all 20 POIs together, so the
*differences between bins* are measured ~5× more tightly than each
individual σ_α suggests. Naive bin-wise pulls (in either σ_total or
σ_stat) ignore this and systematically understate or overstate the
true tension.

**Practical guidance:**
- Per-bin (α_j − α_inc)/σ_j is fine as a **per-bin diagnostic** /
  visualization, in any sigma flavor.
- Σ_j pull_j² is **not** a hypothesis test of H₀; the proper test is
  the full-covariance form (= LR test).

### Robustness — partial-LRT freeze table

A 10-group freeze scan was performed by freezing each candidate
nuisance group in both inclusive and decorrelated fits and
recomputing χ². No single group changes the headline p-value by more
than ~0.10 either way:

- **Mild absorbers** (Δχ² > 0 when frozen, *not* the source of
  preference but soaking up some): `pdf_mb_and_CT18Z` +3.3,
  `pdfCT18Z` +2.0, `scetlibNP` +1.1, `pdf_mb` +1.1.
- **Mild carrier** (Δχ² < 0): `pixel_multiplicity` only, −1.3.
- **Innocent** (|Δχ²| ≤ 0.3): `resumTNP`, `prefire_stat`,
  `fsr_photos`, `qcdscale_helicity`.
- **Maximum freeze** (`all_top_suspects`, ~265 nuisances pinned):
  χ² = 55, p = 2·10⁻⁵ — confirms the data carries differential
  rapidity information that the unfrozen nuisance model adequately
  absorbs under H₀.

The result is therefore neither driven by, nor masked by, any single
identifiable nuisance group.

**Methodological note**: spread reduction does *not* track LR
reduction. `pdfCT18Z` reduced the bin-wise spread by 22% but actually
*increased* the LR by 2 χ² when frozen. Spread is a heuristic visual;
LR is the test. They can disagree.

### Net conclusion

> Under both the un-scaled and Λ5p0 baselines, the rapidity-decorrelated
> α_S fit returns 20 per-bin α_S values that are **statistically
> consistent with a single common α_S** (LR p = 0.18 / 0.19, χ²/ndf ≈
> 1.2). The χ² is verified independently by three methods. No single
> nuisance group is hiding a significant effect (all individual
> |Δχ²| ≤ 3.3); the data does carry differential rapidity information
> (max-freeze χ² = 55), which the unfrozen nuisance model absorbs
> adequately. **No further uncertainty inflation appears motivated for
> the per-bin α_S story.**

### Open follow-ups

- The PDF protocol study (single PDF set + α_S-correlated variation,
  vs CT18Z 29-direction + MSHT20 m_b range hybrid) remains as a
  separate study — under the now-confirmed mild baseline, urgency is
  low.
- If a future analysis configuration changes (e.g. higher stats, or
  removing Λ5p0), the LR may shift. The infrastructure in this study
  (drivers, analyzer, χ² cross-check) is reusable.
