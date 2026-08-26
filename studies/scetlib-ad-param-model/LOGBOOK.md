---
title: Fully differentiable SCETlib param model (scetlib_ad)
slug: scetlib-ad-param-model
status: active
created: 2026-08-18
updated: 2026-08-26
---

# Fully differentiable SCETlib param model — logbook

**Goal:** a rabbit ParamModel whose prediction is differentiable in EVERY
parameter SCETlib can tune — the NP λ, α_s, the TNPs, and (via eigenvector
coefficients) the PDFs — built on the SCETlib `autodiff-sigmaul` branch instead
of the WRemnants bT-grid transcription. Done when a gen-level σUL fit closes on
injected truth AND the λ response matches the existing `scetlib_np` model.

---

## START HERE (status as of 2026-08-25 -- read the LATEST block first; older blocks are historical)

> ### 2026-08-25 (LATEST): the muF fix MATERIALLY changes the fit -- proven on Asimov
>
> Asimov A/B, same card, same cache, arm B = arm A + exactly one commit
> (`fix-muf-member-coordinate`, 92f1299). No statistics involved:
>
> | | unpatched | muF fix | |
> |---|---|---|---|
> | sigma(alpha_s) | 4.426e-4 | 3.786e-4 | **-14%** |
> | sigma(resumScaleMuR) | 0.269 | 0.479 | **+78%** |
> | sigma(resumScaleMuF) | 0.252 | 0.199 | -21% |
> | rho(alpha_s, muF) | +0.225 | -0.143 | **SIGN FLIP** |
> | rho(alpha_s, transition2) | +0.097 | -0.319 | **SIGN FLIP** |
>
> Two sign flips and a 78% sigma change mean the fix **rotates the whole
> (muR, muF, transition) block** relative to alpha_s. transition2 comes along
> because its derivative routes THROUGH the muF member pair.
>
> **Grouped impacts move too: `resumTransition` on alpha_s TRIPLES, 4e-5 ->
> 1.2e-4** (of a 3.8e-4 total; 9 floating 1.0e-4 -> 1.6e-4 of 1.9e-4);
> `resumTNP` falls 4.2e-4 -> 3.3e-4.
>
> **The scoring that called the transitions harmless was CIRCULAR.** The
> 0.002-0.025 sigma equivalent was measured on the UNPATCHED build, where the
> transition impact is artificially small *precisely because the muF
> interpolation it routes through was wrong*. The bug made the transitions look
> harmless. On the patched build they carry ~3x more alpha_s, so a ~25% error in
> their derivative costs ~3x more than that scoring implied.
>
> **TWO CONSEQUENCES.**
> 1. **Every sigma(alpha_s) number measured before 2026-08-25 is
>    bug-contaminated** -- including the 1.25e-4 -> 4.27e-4 (3.4x) inflation and
>    the "56% of variance is h_qqV". Re-measurement on the patched build is in
>    progress. Qualitative conclusions appear to survive (rho(alpha_s, h_qqV)
>    -0.75 -> -0.74).
> 2. **The transition residual is worth MORE than it was scored.** The
>    0.002-0.025 sigma equivalent came from a run where the transition group's
>    impact was 4e-5; it is 1.2e-4 patched. A ~25% error in a derivative whose
>    nuisance carries 3x the assumed impact is worth correspondingly more.
>    Luca's ruling to fix the transitions regardless of impact is now backed by
>    the numbers, not only by principle.
>
> ### 2026-08-25 (latest): gen-level fit VALIDATED; two real bugs found downstream
>
> **The gen-level 2D fit works and sigma(alpha_s) is validated.** 45-toy ensemble
> through rabbit's own toy machinery: alpha_s pull mean -0.211 +- 0.166, width
> 1.116 +- 0.119 -- both pass. Asimov injection closure returns 0.1195 to 4e-12
> with all 17 other parameters back at the anchor. ~150 s per 18-parameter toy
> fit, minimisation 75-85% of it; 100 toys ~ 3.4 h.
>
> **18 parameters float, not 19**: `tnp_b_qqDS` has an IDENTICALLY ZERO Jacobian
> column for the Z (it scales a channel that does not contribute) and the model
> correctly refuses it as singular. `resumTNP_b_qqbarV` passes the guard but is
> inert (response 2.3e-4/theta, constraint returns exactly 1.000) -- held by its
> prior, not measured.
>
> **sigma(alpha_s) -- SUPERSEDED, see the muF A/B block above. On the PATCHED
> build (Asimov): 1.92e-4 (9 float) -> 3.79e-4 (18 float), i.e. the TNP
> inflation is 2.0x, NOT the 3.4x measured unpatched. Do not quote 3.4x
> anywhere.** The patch moves the two configurations in OPPOSITE directions:
> 18 floating falls 14% (4.43e-4 -> 3.79e-4), 9 floating RISES 46%
> (1.31e-4 -> 1.92e-4). h_qqV dominance survives (56.7% -> 54.7% of the
> variance, rho -0.753 -> -0.740), and freezing it reproduces the impact exactly
> on both builds. Still a gen-level normalisation degeneracy between the
> hard-function TNP and alpha_s; do NOT read it as the analysis-level TNP cost.
>
> **Two findings that are ours to fix:**
> 1. **CLOSED: the muF bug WAS the cause.** Paired toys on the patched build move
>    the `resumScaleMuF` pull from **-0.523 +- 0.157 to -0.068 +- 0.243** -- the
>    bias is gone. Chain complete: wrong coordinate -> distorted covariance
>    (Asimov A/B) -> biased pull (toys) -> removed by the fix.
> 1. (as first observed) `resumScaleMuF` pull mean **-0.523 +- 0.157 (3.3 sigma) with width 1.05** --
>    a biased mean with a CORRECT width is a displaced minimum, i.e. a wrong
>    derivative, which is the muF-coordinate bug's signature. Under-convergence
>    (edm 2e-4 => 0.02 sigma) and the log reparametrisation (resumScaleMuR uses
>    the identical map and prior and is unbiased) are both ruled out. A/B against
>    the patched build pending. NB the earlier "width 2.03" from 5 toys was a
>    FLUCTUATION -- the full ensemble gives 1.05, that hypothesis is dead.
> 2. `lambda4_nu` width **1.72 +- 0.18** -- error bar understated ~1.7x, mean
>    fine; postfit sigma swings 0.019-0.092 across subsets. A non-Gaussian
>    direction, not a wrong derivative. Not an alpha_s problem (rho = -0.23).
>
> **OUR DECLARED PRIORS ARE UNPHYSICALLY WIDE.** Drawing theta_true straight from
> them -- the literal recovery test -- FAILS: 40 of 64 draws (63%) give a NEGATIVE
> sigma_gen, up to 81 of 210 bins (the negative-lambda4 trap). `delta_lambda2`'s
> declared prior is 0.5 against a postfit constraint of 0.0065, i.e. **80x wider
> than the data allows**. The ensemble therefore uses rabbit's own machinery.
> This needs revisiting before the priors are used for anything quantitative.
>
> Plots: `~/public_html/alphaS/260825_scetlib_ad_gen2d_validation/`.
>
> ### 2026-08-25 (latest): where the residual actually is, and what is being fixed
>
> All 39 directions validate on the production path. Every remaining residual has
> now been converted into an **equivalent shift on alpha_s** (project the residual
> onto dlnsigma/dalpha_s from the same cache's Jacobian, then profile the other
> nuisances with unit priors; `residual_structure_map.py`). Against
> sigma(alpha_s) = 6.16e-4 (Asimov, no PDF eigenvectors):
>
> | direction | equivalent Delta(alpha_s) / sigma |
> |---|---|
> | mufup | **0.248** |
> | lambda2 -> 1.0 | **0.176** |
> | kappaFO0.5-kappaf2 (kappa_R) | **0.170** |
> | the three x2 transition directions | 0.002 - 0.025 |
>
> **SUPERSEDED 2026-08-25 (later the same day): that ranking was measuring the
> TEMPLATE, not us.** The production correction zeroes its nonsingular below
> `--qtCutoff` = **1.0 GeV** while ours cuts at **0.1 GeV**, and the card's first
> gen bin is exactly qT [0,1] -- so there the template's variation ratio is
> SINGULAR-ONLY and ours is MATCHED. Rebuilding the same ratio from our singular
> piece alone collapses all 39 directions in that bin to <= 1.1e-4, and the
> residual equals f*(n-s) with the ONE measured constant f = -0.0320 across eight
> directions (d/(n-s) = -0.0293..-0.0361). Aligned, the ranking becomes:
>
> | direction | shipped | aligned |
> |---|---|---|
> | mufup | 0.248 | **0.004** |
> | lambda2 -> 1.0 | 0.176 | **0.007** |
> | kappa_R down | 0.171 | **0.006** |
> | alphaS 0.120 | 0.084 | 0.033 |
> | transitions (3) | 0.002-0.025 | **unchanged** |
>
> Nothing is left above 0.08 sigma, and because the transitions are identically
> zero below qT 16 they are UNCHANGED by the alignment -- so they are now among
> the LARGEST remaining residuals, not the smallest. Luca's ruling to fix them
> regardless of impact was right on the merits, not just on principle.
>
> The interpolation suspicion is refuted at code level: the member columns are
> combined by a three-point Lagrange quadratic (`w0 = 1-t^2`) and every direction
> in the ranking sits at **t = +-1 exactly**, where the interpolant returns the
> stored member bit-for-bit. And tolerance never helped because (f - f_t) is a
> difference between two PREDICTIONS, hence tolerance-independent.
>
> **OPEN DECISION (Luca's):** `matched_nons_qt_cut = 1.0` in the runcard aligns us
> to the templates for one line plus an 83-min rebuild. It is a CHOICE, not a bug
> fix -- 1.0 reproduces the analysis templates exactly, 0.1 is arguably the better
> calculation, and the bin carries 1.0% of the gen yield. Note the consistency
> angle: with theory corrections applied IN the histmaker (settled 2026-08-25),
> the central comes from the corr file at 1.0 GeV while the model supplies the
> ratio -- so the ratio and the central should share the convention, or the corr
> files should be regenerated at 0.1.
>
> **This reorders the priorities.** The transitions, long the visible worry, are
> the LEAST consequential of the 39 -- their residual is confined to five qT bins
> and is nearly orthogonal to the smooth alpha_s response (overlap cosine
> 0.13-0.24). The alpha_s-relevant residual lives in qT [0,1] and [1,2] in the
> muF / kappa_R / alphaS directions, which are **spatially disjoint** from the
> transitions and, unlike the lambdas and TNPs (3-15x better at 1e-4), do NOT
> improve when `target_precision_rel` tightens. That is the open question.
>
> **The transitions ARE still a real defect and Luca has ruled they get fixed
> regardless of impact.** Measured against the runcard route the x2 response is
> off by -17..-36% at qT [20,24], flat through the anchor, zero below qT 16,
> antisymmetric in the leg, flat in |Y|. The knot route is CLOSED as a fix (see
> the 2026-08-25 late entry): no spacing makes it right, and both the
> knot-coarseness and the global-vs-per-node mechanisms are refuted. Current
> suspect is the variation-weight re-solve (`rule_min_norm_update`'s ~1e-6 ridge
> floor divided by a member delta that shrinks with the knot spacing), which also
> explains why integration tolerance does not help.
>
> Do NOT reuse the pre-2026-08-25 conclusion that the transitions are "blocked on
> upstream" or "the interpolation method's own limit" -- both are superseded.

> ### 2026-08-25: how to build the 62-member (29 eigenvector pair) cache
>
> All 39 directions validate on the production path (see the 2026-08-25 log
> entries), so the remaining blocker on a quotable alphaS is the BUILD. Its cost
> is the PDF-member loop: 13.7 min per member of fixed-order warming on the
> 210-bin card at `target_precision_rel 1e-3`, so ~14 h for 62 members.
>
> **Do not split the members over processes.** Measured (2026-08-25 late entry
> and `knowledge/20_frameworks/scetlib_ad_cache_build_parallelism.md`):
> the member stage is parallel over NODES, not bins, so it already scales past
> the bin count (3-4x from `--threads` 32 -> 200 on a 10-BIN subset, and a live
> 210-bin build sits at 145 busy cores of 200); members from independent
> processes cannot be merged at all (the node set is not reproducible -- 357 vs
> 359 vs 371 nodes/bin -- and the member data is a difference against it); and
> forked children lose the TBB pool (99% CPU each).
>
> **Recipe:** raise `--threads` (the node has 768), and/or split BINS across
> processes or condor nodes with `--subset` and merge them with
> `build_cache_parallel.py --merge-bins`. Also, before the real build: check
> `--n-train` (the default 9 leaves n_train/n_params at 0.17 once 29
> coefficients are added) and expect a ~15 GB uncompressed rules blob.
>
> Reproducibility floor, worth knowing for every A/B from here on: two
> independently built caches of the SAME runcard agree to 3.1e-05 in sigma at
> the anchor but only 3.0e-03 in the Jacobian at a 10%-displaced point.

> **The transition points are blocked on upstream; kappa_R was OURS and is
> FIXED. Everything else is validated and the Asimov machinery works.** In
> flight: two caches that are the before/after for the kappa_R fix (see NEXT
> STEP), MRs !3 and !4 open on `scetlib-cms`, and one SCETlib bug (the
> transitions) we have diagnosed but should not fix ourselves.
>
> ### What works, measured
> | test | result |
> |---|---|
> | sigma_gen vs the production driver, full space | 7.4e-06 |
> | sigma_reco vs the histmaker, shape / **absolute** | 0.128% / **0.149%** |
> | alphaS variations vs the `_pdfas_` templates | 2.0e-03 / 2.4e-03, worst bin [0,1] |
> | 8 NP lambda variations | 4.6e-04 .. 4.9e-03, worst bin [0,1] |
> | 20 TNP variations | 2.2e-16 .. 7.4e-04, worst bin [0,1] |
> | reparametrisation (theta -> physical, value AND chain rule) | bit-exact, 0.000e+00 |
> | Asimov reco fits (6 and 8 floating) | converged, edm 9.7e-28, truth recovered |
>
> For lambda/TNP/alphaS the ONLY residual is the first qT bin -- the known
> nonsingular-cutoff difference, which Luca is handling separately. Those are
> done.
>
> ### THE BLOCKER: the profile scales are wrong in SCETlib's AD path
> `set_diff_scales(1)` makes kappa_R and x1..x3 differentiable. For the
> TRANSITION POINTS the value is exact at the anchor (4.4e-16) but the SLOPE in
> x2 has the **wrong sign** and is ~-7x too big -- visible already at
> dx2 = 0.01. Since the fit differentiates that same value function, the fit
> derivative inherits the sign error.
>
> **Mechanism (diagnosed, see the 2026-08-21 entries):** the transition points
> move `muf` (~20% for x2: 0.6 -> 0.35, since `Lf ~ 1e-12` means muf tracks
> muB), and the per-node BEAM CONVOLUTIONS are frozen at the config's muf.
> `conv_probe` shows they change by 7-16% over that muf range. Changing the
> runcard refills the nodes so they follow; changing the PARAMETER does not.
> `kappa_R` escapes this because `set_muR_factor` holds muF fixed BY
> CONSTRUCTION -- which is why kappa_R agrees to 1-2e-3 while x1..x3 do not.
>
> NOT the cause, each ruled out by measurement: `params.REPARAM`, our
> label->parameter mapping (checked against the production's own
> `variations_resummed.conf`), the profile formula (`Scale_provider::_f_run`
> delegates to the same `formulas::f_run` the AD kernel uses), the ported node
> scalars (`node_scalars_probe` = 0.00e+00 at x2 = 0.35), the inlined copy in
> `node_value`, the compressed rules (2.3e-04 vs live), `calculation_piece`,
> the frozen nonsingular, and `make_theory_corr`.
>
> **Status:** GitLab issue posted by Luca on `scetlib/contrib/scetlib-cms`;
> follow-up comment with the mechanism drafted at
> `transition_points_issue_comment.md`. We should NOT attempt the fix: the muF
> machinery is a GLOBAL member interpolation (`tf = log(kF)/var_muf_lnstep`)
> while the induced shift is PER NODE, and `DrellYan.hpp:586` shows per-node
> `dconv` was already considered and rejected. Offered instead: (1) a regression
> test comparing the parameter route against the runcard route, (2) extending the
> existing `muf_follows_muB` guard to refuse/flag x1..x3.
>
> ### NEXT STEP
> 1. **Two caches in flight, the before/after for the kappa_R fix.** Both on the
>    same card and settings, differing only in the SCETlib build (confirmed per
>    process via `/proc/<pid>/maps`):
>    `cache_aspair_260821` <- `build` (unfixed, launched 11:22, pid 3070572) and
>    `cache_aspair_260821_kRfix` <- `build-fix` (BOTH fixes, relaunched 14:01,
>    pid 3661411 -- the 12:46 attempt died on the re-solve ridge floor, MR !4).
>    `after_cache.sh` / `after_cache_fix.sh` are waiting on them and will run
>    `backend_check.py` + `validate_variations.py --profile` into
>    `~/public_html/alphaS/260821_scetlib_ad_variations_newcache` / `..._kRfix`.
>    Falsifiable expectation: kappa_R down 4.0e-02 -> the same order as the other
>    directions; kappa_R up 4.5e-03 improved less; lambda/TNP/alphaS unchanged;
>    transitions STILL sign-inverted. If kappa_R does not improve through the
>    cache when it went 3.3e-02 -> 9.1e-06 live, suspect the rule training rather
>    than the physics.
> 2. **kappa_R: FIXED** (floor compensation, MR !3) and the re-solve ridge floor
>    it exposed (MR !4). `resumTransition2` is now frozen -- a stopgap, and it
>    leaves the transition uncertainty with NO representation, since the 260820
>    cards carry no theory templates. **Luca's call:** remake a card keeping the
>    `resumTransition*` templates, or accept the gap explicitly.
> 3. **Asimov fit B is INVALID** -- it floated `resumTransition2`. Its
>    sigma(alphaS) = 1.81e-03 and rho(alphaS, transition) = -0.65 must not be
>    quoted. Fit A (6 floating, 6.16e-04) and rho(alphaS, kappa_R) = +0.927 stand.
>    Rerun once the transitions are resolved or excluded.
> 4. **PDF eigenvectors still absent** (`n_eig=0`): ~20 h at 19.4 min/member for
>    62 members, plus beamfunc grids for 58 members (the condor-scale job).
>    Until then the card must keep `pdf*` templates.
> 5. **Audit the remaining frozen `ad_g.prof_*` / `fo_*` constants.** The kappa_R
>    bug WAS a configure-time constant that should have followed a live
>    parameter; `prof_v_muB/muS/nuS/muf`, `fo_muf`, `fo_kappaf` are the same
>    shape of risk, and all are invisible at central parameters -- exactly how
>    this one survived. Cheap now that `ab_scale_route.py` exists.
> 6. **kappa_R's remaining APPROXIMATION**, separate from the bug: it is linear
>    in kappa_R with sigma = 0.5, so +-1 sigma is [0.5, 1.5] while the card
>    varies [0.5, 2.0] -- the up direction is understated. A log-parametrised
>    kappa_R fixes it. Matters because rho(alphaS, mu_R) = +0.93.
> 7. **Nonsingular qT cutoff:** ours 0.1 GeV, CorrZ built with
>    `--qtCutoff 1.0`. Explains the first-bin residual in nearly every variation.
>    A runcard setting plus a cache rebuild, and a real choice attached: 1.0
>    reproduces the templates, 0.1 is arguably the better calculation.
>
> ### Second regression in the new build
> **The 3rd `configure()` in one process SEGFAULTS** on HEAD `6907326`;
> `bc20d31` handled six (that is how the original A/B ran). Workaround: one
> measurement per process. Unrelated to the transition bug; worth its own issue.

---

## Log

### 2026-08-20 (fork, cont. 4) — binning/sampling non-additivity BOUNDED; provenance fully traced

**Luca's objection (correct and sharper than mine): cross sections are additive,
but SAMPLING within a bin is not.** A quadrature over a wide bin need not equal
the sum of quadratures over its sub-bins. This had NOT been tested for the
nonsingular -- the earlier `bisect_ab.py` additivity test (~1e-5) was on the
SINGULAR. And the nonsingular is the sensitive one: |N|/F ~ 1e-2, so a relative
error on F is amplified 100x on N.

Test (`$SP/additivity_nons.py`), at the CARD's tolerances (rel 1e-4, not the
loosened ones), N and F on a coarse bin vs the sum over its sub-bins, reported
as a fraction of F i.e. in eps units:

```
                                              N: diff/F     F: diff/F
central |Y|[0,0.15]  qT[1,2]  -> qT split      6.34e-08      5.70e-03
forward |Y|[1.8,2.5] qT[1,2]  -> qT split      6.62e-06      6.51e-06
central |Y|[0,0.15]  qT[5,6]  -> qT split      1.29e-08      2.74e-08
        |Y|[0,0.3]   qT[1,2]  -> |Y| split     1.33e-05      2.59e-07
```

Worst N non-additivity **1.33e-05** vs eps of 2.6e-3..5.8e-3 = **0.2-0.5% of the
effect**, on both axes, at low and mid qT, central and forward. **The coarse
binning does not manufacture eps.** NB N's RELATIVE non-additivity is worse
forward (1.07e-3 vs 5.07e-6) because the cancellation is tighter there
(|N|/F = 6.2e-3 vs 1.25e-2), but it is the ABSOLUTE error that feeds eps.

**Separate accuracy caveat found:** F is non-additive at 5.70e-03 in the CENTRAL
narrow-|Y| low-qT cell while <=6.5e-6 everywhere else -- the `full` FO
integration is specifically hard in that corner. F is only eps's denominator, so
this scales eps by ~0.6% rather than shifting it, but do not quote our F to
better than a percent at central rapidity and low qT. (It also explains an
earlier oddity: loosened-tolerance F on narrow bins gave |N|/F = 9.9e-2 where
the card tolerance gives 1.25e-2. My loosened F was unreliable on narrow bins.)

**BINNING PROVENANCE, fully traced (was wrong twice before getting it right):**
- DYTurbo input `results_z-2d-nnlo-vj-CT18ZNNLO-mur1-muf1-scetlibmatch.txt` is on
  the SAME 82 y x 70 qT grid as the SCETlib reference runs.
- **CorrZ is NOT on that grid**: `make_theory_corr.py` rebins to **17 absY** x 70
  qT. So CorrZ's grid is the finest common one.
- **Our |Y| grid matches CorrZ's EXACTLY for 9 of 10 bins** (0, 0.15, 0.3, 0.5,
  0.7, 0.9, 1.1, 1.3, 1.5, 1.8); only our last bin [1.8,2.5] sums two of theirs
  ([1.8,2.0]+[2.0,2.5]). So rapidity was never really rebinned. Only qT was
  (our 1 GeV vs their 0.5 GeV).
- A zero-summing comparison is IMPOSSIBLE by construction: the sing pkl is on the
  fine 82-bin signed-y grid while CorrZ is on 17 absY bins, so reaching a CorrZ
  |Y| bin necessarily sums pkl bins. That summation is the one the resummed
  validation exercises at 7.4e-6.

**DYTurbo's own precision BOUNDED and cleared.** Its txt carries a per-bin
uncertainty column: sigma/F ~ 1e-5, i.e. **15-90x smaller than eps** (90x in the
most forward bin). So "bad precision on the DYTurbo side" is out.

**CORRECTION: qtriang is off on BOTH sides.** `defaults.conf` sets
`fo_order2_qtriang = no` deliberately ("Matches upstream DYTurbo's qtriang
default"; enabling it alone would make `full` and `sing` inconsistent). My
earlier inference that CorrZ's DYTurbo must have used `qtriang = true` assumed
OUR side had it on. It does not.

**E-commonality VERIFIED** (the assumption the whole eps extraction rests on):
CorrZ's E is `..._nnlo_sing` (`calculation_piece = sing`, `run_order = none`,
`fixed_order = nnlo`, **no [TNPs]**), its `variations_singular.conf` section [0]
is EMPTY (so variation 0 is a no-op, same as ours), and our matched-mode E is
also TNP-free -- a TNP-free standalone `nons` gives N = -0.43065 vs the cache's
0.4311, agreeing to 0.1% = 8.9e-6 in eps units, ~300x below the effect.

**Shareable bundle** in `~/public_html/alphaS/260820_scetlib_ad_fo_difference/configs/`:
our runcard as used, a FULLY RESOLVED version (defaults merged, nothing
implicit), our base card, the reference resummed cards, CorrZ's nnlo_sing cards,
and a README with the extraction and the exclusion table.

**Exact file compared against:**
`wremnants-data/data/TheoryCorrections/scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_CorrZ.pkl.lz4`
(md5 732438b33008028a8370024c9eb50805), key
`["Z"]["..._N2LO_hist"]`, vars=central. NB the older scetlib_np reco validation
used `FranksVals` (no "Vars") -- a DIFFERENT correction file.

**Status: precision bounded both sides, binning bounded, E common, qtriang
common, config 0/107. Remaining: mistranslation or misconfiguration of the
vjint port, with the rapidity structure (sign change at |Y| ~ 0.8, growing
forward) as the fingerprint.**


### 2026-08-20 (fork, cont. 3) — plot set for the SCETlib author; the port was validated only at y=0

**KEY FINDING (reframes everything).** Luca: the FO code is a PORT of DYTurbo's
`vjint` (the doc says so: "Vjet_analytic is a translation of vjint"). So a
"genuine physics difference" is NOT an available explanation -- I had said that
and it was wrong. It must be mistranslation, misconfiguration, or precision on
either side.

**And the port's low-qT validation has NO forward-rapidity coverage.**
`doc/vjet-dyturbo-validation/points.txt`, as (m, qT, y): NINE of twelve at
y = 0.0; the only forward point is y = 2.0 at qT = 25 (where our eps ~ 1e-5);
two off-shell points at y = 0.5. And `points_lowqt.txt` -- ALL FIVE at y = 0.0.
**There is no point at forward rapidity AND low qT, exactly where we measure the
largest disagreement.** So we are not contradicting the doc's "constant
-2.97e-6 at every one of the 12 points"; we are outside the region it sampled.
Consequence: a rapidity-dependent mistranslation would not have been caught.

**Plot set for the discussion** (`~/public_html/alphaS/260820_scetlib_ad_fo_difference/`):
- `fo_eps_map_vs_points` -- eps over the (qT, |Y|) plane, 12 x 10 grid, with all
  17 sampled points overlaid and the low-qT/forward corner boxed. THE plot: the
  disagreement sits where nothing was sampled. Cells drawn individually, not as
  a pcolormesh, because the qT bins are non-contiguous (gaps are real).
- `fo_eps_vs_qT_by_absY` -- central rapidity eps is NEGATIVE and inside the
  doc's +-8.6e-4 band at all qT; forward rapidity is POSITIVE and leaves the
  band below ~4 GeV, reaching 5.8e-3 at qT 1-2.
- `fo_eps_vs_absY_by_qT` -- monotone in |Y|, zero crossing at |Y| ~ 0.8, same
  shape at every qT, amplitude 5.76e-3 -> 1.74e-3 -> ... -> 7.65e-4.

**Leading candidate under Luca's three-way framing: a Y bin-integration
convention mismatch.** If one side integrates sigma over the Y bin and the other
evaluates at the bin centre x width, the difference is (w^3/24)*sigma''(Y).
Predicts: negative where dsigma/dY is concave (central), positive where convex
(forward), SIGN CHANGE AT THE INFLECTION -- we see it at |Y| ~ 0.8; growth
forward where |sigma''| is largest; largest effect in the widest bin
([1.8,2.5], w = 0.7) -- all observed. And it would appear ONLY in the
nonsingular, since both sides share the same SCETlib resummed histogram, which
is consistent with the resummed piece agreeing to 7e-6. NOT YET TESTED: compute
sigma''(Y) from our own calculation and check eps ~ (w^2/24)*sigma''/sigma.

**Question to put to the author:** what `relaccuracy` did the CorrZ DYTurbo run
use, and did it integrate over the y bin or evaluate at the centre? That run's
settings/convergence are the one thing we cannot bound from our side -- the
doc's 4.8e-5 self-convergence check was on its OWN DYTurbo run, not that one.

Scripts: `$SP/eps_map.py`, `$SP/plot_eps_maps.py`, `$SP/eps_by_y.py` (all also
copied to the webdir).


### 2026-08-20 (late, cont.) — gen-level ABSOLUTE vs CorrZ: 0.067%. The new method's prediction is fine; only the R-fold granularity is not.

`$SP/gen_vs_corrz_newmethod.py`. Under the new construction the card's nominal
cancels, so the fit's prediction IS `k*sigma_SC` -- no ratio-to-central to hide
behind. So this compares it ABSOLUTELY against the validated CorrZ, on the card's
gen grid (21x10, which nests exactly in CorrZ's 70x17). Cache: `cache_reco`.

**The cache is positive-side-only in Y** (sigma over Y in [a,b]) while CorrZ is
binned in |Y|, so an explicit **x2** is required -- the factor that cancels in
`sigma(p)/sigma(anchor)` and does NOT cancel here (plan risk R-1, now exercised).

```
totals: ours 1340.175  CorrZ 1339.9369  ratio 1.000178      <- 0.018%

[    0,   1]  0.977785     [   4,   5]  1.000545     [  20,  24]  1.000013
[    1,   2]  1.006509     [   5,   6]  1.000385     [  33,  44]  0.999954
[    2,   3]  1.001859     ...                        [  44, 100]  0.999944
[    3,   4]  1.000887

yield-weighted |ratio-1| = 6.69e-04    max = 2.22e-02
```

- **Absolute normalisation validated to 0.018%.** That is the first test of the
  x2 Y fold, the absolute sigma_SC scale and the units -- none of which the old
  ratio construction could see (a factor-2 error would show as 2, not 2e-4).
- **Above 3 GeV: 0.19% falling to 1e-5** by qT > 20.
- **The first bin is exactly the nonsingular cutoff**: 0.977785 = 1 - 0.0222,
  and the fork independently measured our `nons/sing = -0.0222` there against
  CorrZ's exactly 0.000 (their `--qtCutoff 1.0` vs our
  `matched_nons_qt_cut = 0.1`). Two independent measurements of one number.

**Key distinction for the decision:** the gen-level PREDICTION is fine (0.067%).
The 0.30% granularity is a separate, RECO-level effect from coarse-graining the
correction through R. Only the second argues for a finer gen grid.

**Also corrected (I had this wrong twice today).** Comparing within-bin errors by
their MAXIMA is misleading -- the maxima sit in low-yield bins and gave a
spurious 1.4x. Yield-weighted, on the correction's own grid coarse-grained onto
the card's:

```
FULL correction                7.71e-03   (max 5.95e-02)
variation lambda2=1.0          2.54e-03   (max 8.19e-03)
variation lambda2_nu=0.05      9.83e-04
variation gamma_nu=+1          1.69e-04
variation kappaFO2/kappaf0.5   1.67e-03
```

So the correction costs 3x-45x more than a variation, as originally argued. AND:
**the param model ALREADY carries a granularity error on its variations today**
(up to 0.25% for the big lambda2 excursion, 0.017% for TNPs) -- pre-existing, not
introduced by this change, and never measured because the lambda-response
validation coarse-grained BOTH sides so granularity cancelled there. That is an
independent argument for a finer response gen grid, regardless of whether the
correction moves into the model.

Plots: `~/public_html/alphaS/260820_granularity/` (mechanism) and
`~/public_html/alphaS/260820_gen_vs_corrz_newmethod/` (this result).

**Three-curve version (CorrZ / new / old) found a SECOND first-order exposure.**
Adding the OLD-method object -- `N_gen` from the corrected card, i.e. MiNNLO
reweighted EVENT BY EVENT, converted to pb by `/(lumi*1000)`:

```
          qT bin          CorrZ            new            old   new/CorrZ   old/CorrZ
[     0,     1]      14.186771      13.871613      14.189151    0.977785    1.000168
[     1,     2]      38.700869      38.952769      38.692387    1.006509    0.999781
[    33,    44]      93.285289      93.281037      93.299601    0.999954    1.000153
[    44,   100]      132.2331       132.22566      159.25305    0.999944    1.204336
totals   CorrZ 1339.9369   new 1340.175 (1.000178)   old 1367.0116 (1.020206)
```

- The old method matches CorrZ to **~2e-4 in every bin below 44 GeV** -- the
  event-level correction reproduces CorrZ's own sigma essentially exactly.
- **The last bin is +20%**, and it accounts for the ENTIRE 2% total difference
  (159.25-132.23 = 27.0 vs 1367.0-1339.9 = 27.1). Cause: `ptVGen`'s last bin is
  an OVERFLOW (`binning.py`, `overflow=True`), so `N_gen[44,100]` holds
  everything above 44 GeV INCLUDING qT > 100, while our sigma_SC integrates
  44->100 and stops. ~20% of that bin's content is above the cache's ceiling.
- **First-order under the new method, cancels under the old.** Today the
  truncation is identical in numerator and denominator of
  `[R@sigma(p)]/[R@sigma(lambda_c)]`. With `norm` as the denominator it does not
  cancel: ~20% on that gen bin, and since ~6% of the top ptll bin comes from the
  gen overflow, about **1% error in the top ptll bin**. Plan risk R-6, quantified.
- **Granularity is ABSENT at gen level** (both methods reproduce CorrZ at
  <=7e-4). The 0.30% is purely a RECO-FOLD effect -- it appears only when the
  coarse-grained correction is pushed through R.


### 2026-08-20 (fork, cont. 2) — the FO difference is RAPIDITY-DEPENDENT; cache_v3 vindicates the disputed numbers

**RETRACTION OF A RETRACTION.** `cache_v3` (fresh, CURRENT build, 24 directions,
symmetric Y) reproduces the disputed `cache_v2` matched-vs-CorrZ numbers EXACTLY:
`+4.267e-02` at qT[0,1], `+1.918e-02` at [1,2], `+5.789e-03` at [2,3], ... So my
retraction of them was WRONG (and the subagent's reasoning behind it too). The
old cache was version-REFUSED by the rule-blob check; that is not the same as
giving a wrong answer, and I conflated the two. Also confirms the scale
directions are clean: 24 params with the resummed piece still at 7.362e-06.

**eps per (|Y|, qT): strongly rapidity-dependent, SIGN-CHANGING at |Y| ~ 0.8.**

```
qT[1,2]   |Y| 0.00-0.15  eps = -2.92e-03      |Y| 0.90-1.10  +1.15e-03
          |Y| 0.15-0.30       -2.73e-03      |Y| 1.10-1.30  +2.47e-03
          |Y| 0.30-0.50       -2.15e-03      |Y| 1.30-1.50  +3.69e-03
          |Y| 0.50-0.70       -1.29e-03      |Y| 1.50-1.80  +4.87e-03
          |Y| 0.70-0.90       +2.07e-05      |Y| 1.80-2.50  +5.76e-03
```

Same shape at qT [2,3], [3,4], [5,6], amplitude falling with qT (max |eps|
1.74e-3, 1.17e-3, 7.65e-4). F-weighting the ten values gives **2.61e-3**,
reproducing the |Y|-summed 2.60e-3 exactly -- and the sum is DOMINATED by the
forward bins, where both eps and F are largest. `S_ref/S = 2.000` in all 40
cells, so the half-space bookkeeping is right.

**Why this matters: a monotone, sign-changing rapidity dependence is NOT a
quadrature signature.** Quadrature error would be uniform or random in |Y|, and
the rule scan already bounded our side at 1.2e-4. This looks like a genuine
difference in how the two fixed-order implementations carry the rapidity /
parton-x dependence. It cannot be tuned away.

Note the doc's pointwise SCETlib-vs-DYTurbo study compares at 12 fixed
(m, pt, y) points; if the disagreement is y-dependent, those points may not
have covered forward rapidity -- worth asking the authors.

**Numbers for the fit.** A rapidity-resolved fit sees the per-|Y| value, not the
integrated one: max |eps| = 5.76e-3 at qT[1,2] |Y|>1.8, i.e. ~2x the |Y|-summed
value, 7x the doc's SUMMED-FO band (8.6e-4) and 2x its ISOLATED-O(as^2) band
(2.8e-3). In matched-total terms the worst cell is ~1.9% (the compare script's
per-|Y| max at qT[1,2]).

Plots: `~/public_html/alphaS/260820_scetlib_ad_fo_difference/`
(`fo_epsilon_vs_absY.png`, `fo_epsilon_vs_qT.png`,
`matched_vs_corrz_cut01_vs_cut10.png`) + the scripts.

**Status of the FO question:** qT<1 SOLVED (the cut). Our quadrature EXCLUDED
(<=1.2e-4). Our cache EXCLUDED (standalone `nons` matches |N|/F to 8.89e-3 vs
8.90e-3). `qtriang` EXCLUDED (high-qT eps = -8e-5, not +3.0e-3). Deep-IR floor
EXCLUDED (~100x too small). REMAINS: a real, rapidity-dependent SCETlib-vs-
DYTurbo fixed-order difference at low qT, exceeding the doc's summed band --
one for the SCETlib authors.


### 2026-08-20 (late) — event-weight vs matrix route measured: 0.30%, NOT good enough yet

New `scripts/rabbit/scetlib_ad/compare_cards.py` (T1/T2 + R invariance; needs
NO cache, no SCETlib, no corr file -- just two cards). Cards:
`260820_Z_2D_card_scetlib_ad/{ZMassDilepton_ptll_yll_realdata (corrected),
ZMassDilepton_ptll_yll_theoryCorrAltOnly (uncorrected)}`.

**Framing that made the test possible.** The correction is a BIN LOOKUP on the
CorrZ hist (`correctionsTensor_helper.py:8-11`, "returns what is in the bin"),
so the event-weight route is piecewise-constant too and
`Sum_events w(g) == Sum_g w(g) R_raw(b,g)` is an IDENTITY at matched binning.
The only difference is grid coarseness: card gen grid 21x10 vs the correction's
70x17. So the residual is measurable from the two cards alone, with theory, k,
the Y convention and sigma_SC all cancelled:

```
cbar(g) = N_gen_corr/N_gen_unc                        (correction, coarse-grained)
M(b)    = [Sum_g R_raw_unc(b,g) cbar(g)] / [Sum_g R_raw_unc(b,g)]   matrix route
E(b)    = norm_corr(b)/norm_unc(b)                                  event route
```

**T1 -- plumbing clean.** `R_rowsum/norm_signal`: corrected global 0.99924609,
yield-weighted **0.0754%**; uncorrected 0.99927032, **0.0730%**. Same profile
both cards, worst bins at high |yll| and low ptll = gen truth outside the
response grid. Confirms marginalization/cropping/axis order/channel slicing.

**T2 -- THE RESULT. Yield-weighted |M/E - 1| = 0.3030%, worst bin 1.34%.**
`cbar` spans 0.787..1.069 (a -21%..+7% correction), M 0.794..1.067,
E 0.785..1.070, M/E mean 1.002385. **Above the 0.1% decision threshold.**

**Noise control (this is what makes it honest).** From `sumw2`: N_eff/bin =
73983 (corr) / 55765 (unc), ratio 1.3243 tightly clustered (1.311..1.344 -- the
weight reshaping, not a different sample). Two INDEPENDENT samples would give
per-bin scatter `sqrt(1/Nc+1/Nu)` = 0.56%, i.e. `mean|.|` ~ 0.45%. We measure
**0.30% < 0.45%**, so the runs are correlated (same events) and the residual is
NOT dominated by inter-sample noise. A residual noise component cannot be
separated without event-level info, so the fair statement is: granularity is at
the **few x 0.1% level, at or above threshold, not demonstrably below it**.

**R invariance is NOT exact** (I predicted it would be):
`|P_corr/P_unc - 1|` median 8.3e-02, response-weighted mean **6.55e-03**. Same
cause: `R_raw_corr(b,g)` averages w over the events in g that reach reco bin b,
while `N_gen_corr(g)` averages over ALL events in g -- different subsets, so the
cancellation fails under within-bin variation. The median 8.3% is MC noise
(~160 events/populated cell -> ~8% each); 0.66% weighted is the real number.

**Not qT-dominated, contrary to my guess.** `M/E - 1` profiled:
ptll max 5.56e-03 rms 2.65e-03; yll max 5.17e-03 rms 2.94e-03. **Both axes
contribute equally**, so refining only ptVGen will not fix it -- matching the
correction's grid means BOTH axes (70x17 = 1190 gen bins), which is far more
expensive than refining one.

**Consequence: do NOT switch to the uncorrected histmaker yet.** For context the
analysis' own sigma(alphaS) is ~0.55%, so a 0.3% shape mis-modelling of the
prediction is not absorbable. Options: (a) refine the response gen grid on both
axes and pay ~1190 gen bins of cache plus noisier R per gen bin; (b) keep the
corrected histmaker (the currently validated path) and treat the on-the-fly
correction as a later project.


### 2026-08-20 (fork, cont.) — cut raised to 1 GeV (fixes bin 0); our quadrature EXONERATED

**1 GeV cut, gen level.** Applied exactly (grid edge at 1.0 => the cut zeroes the
nonsingular in precisely bin [0,1]); no rebuild needed. matched/CorrZ:

```
[  0,  1]  0.977785 -> 1.000006      max |ratio-1|: 2.22e-02 -> 6.51e-03
[  1,  2]  1.006509 (unchanged)      [ 2, 3] 1.001859   [ 5, 6] 1.000385
[ 20, 24]  1.000013                  [44,100] 0.999944
```

Plot: `~/public_html/alphaS/260820_scetlib_ad_fo_difference/`
`matched_vs_corrz_cut01_vs_cut10.png`. The residual is now purely a 1-3 GeV story.

**Add-on rule/tolerance scan: hypothesis REFUTED.** The doc blames its own qT
trend on "the add-on quadrature rather than the matrix elements" and quotes the
isolated O(as^2) difference at "the shipped defaults (xrule = 64, adaptive on,
target_rel = 1e-3)" -- exactly our card. Scanned `fo_order2_target_rel`
1e-3/1e-4/1e-5 and `fo_order2_analytic_{x,z}rule` 64/128/256 (`rule_cap` to
4096), `calculation_piece = nons`, Y in [0,2.5]:

```
      qT bin     baseline     rel=1e-4     rel=1e-5    xrule=128  xrule=256   spread/F   measured eps
[   1,   2]    -0.430649    -0.436167    -0.436329    -0.436461   -0.436470   1.20e-04     2.60e-03
[   2,   3]    -0.547739    -0.548311    -0.548322    -0.548612   -0.548323   1.00e-05     6.11e-04
[   3,   4]     -0.61739    -0.617467    -0.617475    -0.617591   -0.617508   2.60e-06     3.89e-04
[   5,   6]    -0.684378    -0.684337    -0.684362    -0.684346   -0.684363   7.37e-07     2.44e-04
[  10,  11]    -0.664602    -0.664648    -0.664635    -0.664650   -0.664633   1.73e-06     1.19e-04
```

Max spread 1.20e-04 in eps units = **4.6% of the discrepancy at qT 1-2**, <2%
elsewhere. Every tightened setting agrees to ~3e-4 in N; the baseline is the lone
outlier. **So the 1-3 GeV residual is a real SCETlib-vs-DYTurbo fixed-order
difference, not our numerics.**

**Cross-check that fell out:** standalone `calculation_piece = nons` at qT[1,2]
gives N = -0.43065, i.e. |N|/F = 8.89e-3, matching the 8.90e-3 derived from the
CACHE. So the cache's nonsingular is not implicated either.

**Secondary findings:**
- The shipped defaults ARE marginally non-converged: 1.2e-4 (eps units) from the
  converged answer at qT 1-2, ~1e-6 by 3 GeV. Worth tightening on the NEXT cache
  build (free at build time); not worth a rebuild on its own.
- WHICH doc band applies is the open interpretive question. At qT 1-2 our
  eps = 2.6e-3 is 3x the doc's SUMMED O(as)+O(as^2) band (max 8.6e-4) but sits at
  its ISOLATED O(as^2) band (max 2.8e-3). Since the O(as) pieces cancel an order
  of magnitude better inside the nonsingular, the isolated band is arguably the
  right comparison -- flagged as a reading, NOT proven. (Caveat against it:
  eps = dF/F while the doc's isolated number is d(O(as^2))/O(as^2), and the
  K-factor is 0.077 in the 1-2 GeV bin, so eps "should" be ~0.07x theirs.)
- Impact on the prediction: dT/T = 0.65% at qT[1,2], 0.19% at [2,3], <0.02%
  above 20 GeV.

**Cost notes:** both the `full` and `nons` FO pieces are unusably slow at the
card's `target_precision_rel = 1e-4` (one bin > 10-15 min). F needs only ~1%
(it is the denominator of a small ratio) and N only ~0.1% (the effect sought is
~11% of N), so 1e-2 / 1e-3 respectively make them 15-400 s/bin.

Scripts: `$SP/nons_rule_scan.py`, `$SP/plot_cut_effect.py`, `$SP/fo_epsilon.py`,
`$SP/fo_full.py` (last two also copied to the webdir).


### 2026-08-20 (late, cont.) — the lambda-response "error" is the low-qT nonsingular, NOT rule locality

**Retracting two claims from the previous entry.** I said the 4.9e-3 lambda
response error was probably rule locality / a too-small `n_train`. Both wrong.

**1. `n_train` is not the limiter.** Scan on 8 bins / 24 directions
(`$SP/ntrain_scan.py`), rule vs DIRECT at the actual template points:

```
 n_train   build       anchor    lambda2=1.0  lambda2_nu=0.25  lambda4=1.0
       9  187.6s     7.77e-15       4.44e-07         4.56e-08     2.38e-07
```

At the default `n_train = 9` the rules reproduce a direct calculation to **1e-7**
2.5x away from the anchor. So the compression is fine and the full 53-direction
cache does NOT need the expensive `n_train` -- no `n_train^2` penalty. (For the
record, what `n_train` actually is: sampling in PARAMETER space, not in the
integration variables. It is the number of parameter points constraining the NNLS
weight solve. `c_val` forces exactness AT the anchor regardless, which is why
anchor checks and training residuals say nothing about generalisation.)

**2. The deviation is the nonsingular difference, amplified by the response.**
Both sides are ratios so the central offset cancels -- but not exactly, because
the two nonsingulars differ:

```
ours (S_v + N)/(S_c + N)   vs   ref (S_v + N')/(S_c + N')
=> dev ~ (1 - r) * dN/sigma
```

Y-integrated profile (`$SP/lam_dev_profile.py`), lambda2 = 1.0:

```
 qT [ 0, 1]   dev -2.967e-03   dev/(1-r) -0.0257
 qT [ 1, 2]   dev +7.902e-04   dev/(1-r) +0.0073
 qT [ 2, 3]   dev +1.748e-04   dev/(1-r) +0.0020
 qT [ 3, 4]   dev +5.803e-05   dev/(1-r) +0.0009
 qT [ 4, 5] .. [44,100]  dev ~1e-6..1e-8, dev/(1-r) ~0
```

**Above qT ~ 4 GeV the lambda response matches the template to 1e-6..1e-8** --
BETTER than scetlib_np's 0.02-0.05%. The whole discrepancy is the first two or
three qT bins, dominated by the first.

And the amplification factor is the independently measured one:
`dev/(1-r) = 0.022-0.026` in the first bin for both lambda2 and lambda2_nu, while
the fork's decomposition measured `dN/sigma = 0.0222` in that same bin from the
qT-cutoff difference (ours `matched_nons_qt_cut = 0.1`, CorrZ's `--qtCutoff 1.0`).
Two independent measurements of the same quantity.

**So the per-variation validation is effectively a PASS**, with the residual
confined to qT < 3 GeV and traced to a known, already-being-fixed cause. Aligning
the nonsingular cutoff should collapse it.


### 2026-08-20 (late) — reco EVALUATION path validated; n_train default is suspect

**compute() and the derivative through the reco fold** (`$SP/test_compute_reco.py`).
`validate_reco.py` only exercised the CONSTRUCTOR -- `sigma_reco_central` is built
there -- so nothing had ever called `compute()` (what rabbit calls each
iteration) or differentiated through `R @ sigma_gen`. Both bugs found today were
value-right / derivative-wrong, so this mattered. On `cache_reco`, 2D card:

```
1) compute() at start: shape (780, 4)  max|r-1| = 0.000e+00   <- EXACTLY 1
2) d[sum compute]/dp  AD  [ -6.575257 -10.920176]
                      FD  [ -6.575256 -10.920214]
                      rel [1.127e-07  3.527e-06]   no zero gradients
3) HVP (nested tape): [12.837357 28.701111]
```

So: exact value through the fold, first derivative matches a finite difference of
`compute()` itself, and the nested tape yields a second derivative -- the
`revrev` path rabbit uses, and the one that dies on `tf.IndexedSlices` if a
gather sneaks back in. **The reco path is now validated end to end: construction,
value, first and second derivatives.**

**`--n-train` default is 9, FIXED -- and that is probably wrong.** Upstream's
example uses `max(9, ceil(1.5*n_params))`; our own flag's help says "accuracy
tracks n_train/n_params". So we have been running a ratio of 0.47 at 19 params,
and it would be 0.17 at 53. Leading candidate for why the lambda response is 10x
looser than scetlib_np's 0.02-0.05% (worst 4.9e-3): the TRAINING residual is
~1e-8 either way, which is exactly the trap -- a well-fit training set with too
few points can still generalise badly away from the anchor, and the lambda
templates sit 2.5x out.

It also gates the full-direction build, since the NNLS grows like `n_train^2`
(9 -> 80 is ~79x the rule cost). `$SP/ntrain_scan.py` measures both at once on 8
bins / 24 directions: build time and rule-vs-direct at the anchor AND at the
template points (lambda2=1.0, lambda2_nu=0.25, lambda4=1.0). If n_train is the
driver the big cache needs a high one and must be budgeted; if not, 9 is fine
and the full cache is cheap.

**Decision taken with Luca:** ONE cache with every direction (lambda, scales,
TNPs, alphaS-with-PDF-pair, PDF eigenvectors). A reduced alphaS+PDF cache is not
worth building -- the point of the approach is the JOINT treatment and its
cross-terms, which a reduced cache cannot exhibit.

**Guard asymmetry worth remembering:** `_CONFLICTS` fires only when the model
direction IS floated, so it catches DOUBLE-counting but not UNDER-counting.
Excluding a family from the card while not floating its direction silently
deletes that uncertainty and nothing errors. Rule: exclude a family only if you
are also floating its model direction. (The zero-Jacobian guard,
`param_model.py:657`, does catch the related case of floating an inert direction
-- e.g. `resumScaleMuF` when the cache has `has_muf = False`.)


### 2026-08-20 (fork: fixed-order piece) — the residual reduced to eps = dF/F; claim PARTLY REFUTED

Luca asked for PROOF that the above-1-GeV matched-vs-CorrZ residual is the known
SCETlib-vs-DYTurbo FO difference, not just an argument from consistency. Reduced
it to the quantity `doc/vjet-dyturbo-validation` actually measures.

**The reduction (exact, no approximation).** S = resummed singular is COMMON
(CorrZ uses SCETlib's; ours closes on the production pkl to 7e-6). E = the FO
expansion of the singular is ALSO common (CorrZ builds
`hnonsing = -hfo_sing + hfo` with SCETlib's `hfo_sing`). With N = F - E and
T = S + N:

    dN = N_ours - N_CorrZ = F_scetlib - F_dyturbo = dF     EXACTLY
    eps == dF/F = (dN/S) * (S/F)

So one new number is needed: F, the full fixed order. `calculation_piece = full`,
`run_order = none`, `fo_order2_analytic = yes`, TNPs REMOVED (SCETlib refuses
them at fixed order -- as it does for CorrZ's own `_nnlo_sing`).

**The 1 GeV cut is applied EXACTLY, not emulated, and needs no rebuild.**
`make_theory_corr.py --qtCutoff` defaults to 1.0 and zeroes the nonsingular
below it; the cache's qT grid has an edge at exactly 1.0, so
`matched_nons_qt_cut = 1.0` zeroes the nonsingular in precisely bin [0,1] and
nothing else. Setting N[0] = 0 on our side IS the cut. That bin then carries no
FO information and is excluded (F also cannot be computed there -- the full FO
diverges as qT -> 0 and the integrator leaves the physical region,
"Unphysical x given").

**RESULT:**
```
       qT bin        dN/S       F/S    eps=dF/F        dT/T
[    1,    2]    6.33e-03     2.433    2.60e-03    6.47e-03
[    2,    3]    1.82e-03     2.976    6.11e-04    1.85e-03
[    3,    4]    8.70e-04     2.237    3.89e-04    8.86e-04
[    5,    6]    3.77e-04     1.546    2.44e-04    3.84e-04
[   10,   11]    1.34e-04     1.127    1.19e-04    1.38e-04
[   20,   24]    1.22e-05     0.906    1.34e-05    1.26e-05
[   24,   28]   -7.72e-06     0.883   -8.75e-06   -8.00e-06
[   44,  100]   -9.30e-05     1.153   -8.06e-05   -7.57e-05

eps mean +2.56e-04  median +1.12e-04  max +2.60e-03  min -8.06e-05
DOC:   mean +2.3e-04           max  8.6e-04, GROWING monotonically with qT
```

**Verdict: HALF the claim holds.**
- MAGNITUDE holds, impressively: mean eps = +2.56e-04 vs the doc's +2.3e-04, an
  11% match on an independently measured number. Above ~3 GeV eps is 1e-4..4e-4,
  inside the doc's band. The bulk IS the known FO difference.
- TREND does NOT hold, and I asserted it did. The doc's residual GROWS with qT;
  ours FALLS and flips sign near 22 GeV. Our max, 2.6e-3 at qT 1-2, is 3x the
  doc's max. **So "expected FO difference" is right above ~3 GeV and WRONG in
  1-3 GeV -- exactly where alpha_s sensitivity lives.**
- SETTLED: at high qT eps = -8e-5, NOT the +3.0e-3 the doc predicts for
  `qtriang = false`. So the CorrZ DYTurbo run used `qtriang = true` (or
  equivalent). That open question is closed and it explains nothing here.
- The 1-3 GeV excess is not numerical: DYTurbo self-converges to 4.8e-5 (doc)
  and our cache's FO grid was built at 1e-4, both ~25x below 2.6e-3.

**TRAP that cost a wrong first answer (mine).** Our cache is positive-side-only
|Y| while the reference sing pkl is SIGNED Y over [-2.5, 2.5] -- `S_ref/S = 2.000`
in every bin, verified. Forming `dN = N_ours - N_CorrZ` in ABSOLUTE units mixes
half-space with full-space and gave eps of 1-4% (40-170x too big). Always work in
ratios WITHIN each source (`r_ours = N_ours/S`, `r_corr = N_corr/S_ref`) so the
factor cancels; the F run must then use the SAME half space (Y in [0, 2.5]).

**Cost note:** the full FO piece at the card's tolerances did not finish ONE bin
in 10 min. F is only the denominator of a small ratio, so
`target_precision_rel = 1e-2` / `fo_order2_target_rel = 1e-2` is ample (0.5%
achieved) and makes it 15-40 s/bin.

Scripts + plot: `~/public_html/alphaS/260820_scetlib_ad_fo_difference/`
(`fo_epsilon_vs_qT.png`, `fo_epsilon.py`, `fo_full.py`).

**Open:** what drives eps up to 2.6e-3 in 1-3 GeV. Candidates not yet tested:
the hard step at the CorrZ cut interacting with DYTurbo's own qT binning near
1 GeV; the O(as^2) add-on's accuracy at small qT (the doc blames the add-on
QUADRATURE for its own qT trend, measured with `nons_converge.py` /
`nons_convergence.png` -- worth repeating that rule scan at low qT); and
DYTurbo's nonsingular being a difference of large numbers where |N|/F ~ 9e-3.


### 2026-08-20 (night) — per-variation validation: 28 of 38 templates reproduced

**New CLI `scripts/rabbit/scetlib_ad/validate_variations.py`.** For every
variation the theory-correction file carries, compares

    model : sigma_gen(p_var) / sigma_gen(p_anchor)
    ref   : Corr[var]        / Corr[central]

Both sides are variation/central RATIOS, so no normalisation enters and the test
is non-circular -- it measures the RESPONSE, which is what the fit uses. Needs no
datacard (gen ratio = cache + runcard only). The reference's fine (absY, qT) bins
are summed onto the cache's gen grid, numerator and denominator separately, which
is what the fit's per-bin rnorm does.

**Grid constraint found:** the CorrZ absY edges are
`[0, .15, .3, .5, .7, .9, 1.1, 1.3, 1.5, 1.8, 2.0, 2.5, ...]`, so the CARD's gen
grid nests exactly but the 0.5-step validation grid does NOT (no 1.0 edge). Use
a card-grid cache for this test.

**Results on `cache_reco` (210 bins, 19 params), 28 variations:**

```
lambda2_nu0.05      1.96e-03   lambda21.0          4.85e-03  <- worst
lambda2_nu0.25      1.76e-03   delta_lambda2+-0.02 4.6e-04
lambda20.0          3.74e-03   lambda40.0/1.0      1.3-1.4e-03
gamma_cusp+-1       5.05e-05   gamma_mu_q+-1       1.10e-04
gamma_nu+-1         3.03e-04   h_qqV+-1            1.9e-04
s+-1                7.1-7.4e-04
b_qqV+-0.5          8.4-8.8e-04   b_qqbarV+-0.5    4.2e-06
b_qqS+-0.5          1.5e-04       b_qg+-0.5        7.1-7.4e-04
b_qqDS+-0.5         2.22e-16   <- identically zero on BOTH sides
```

- **The ten TNPs reproduce their templates to 5e-5..9e-4** -- first time those
  directions have been checked against anything.
- **`b_qqDS` is 2.22e-16 in model AND reference**: its Z response is identically
  zero on both sides, independently confirming why the model refuses to float it.
- **lambda: mean 2e-4, worst 4.9e-3** -- ~10x looser than scetlib_np's
  0.02-0.05%. Most likely RULE LOCALITY, not a bug: `lambda2: 0.4 -> 1.0` is a
  2.5x excursion and the compressed rules are anchored (README quotes ~1e-4 at
  x5 in lambda2_nu vs 1e-13 at the anchor). Worth remembering that the templates
  ARE the +-1 sigma points, so this is the accuracy AT 1 sigma. Worst bins are
  the low-sigma corners; typical is 2e-4.

Plots (28, one per variation, model vs template response with a ratio panel,
|Y| integrated by summing sigma before dividing):
`~/public_html/alphaS/260820_scetlib_ad_variations/`.

**Bug fixed while writing it:** `GenFold` indexes in the order the gen axes are
GIVEN, and the card cache is `(ptVGen, absYVGen)`; passing them Y-first made it
read the Y edges as qT and reject the cache. Noted in the script.

**Two builds in flight:**
- `cache_v3` -- validation grid, symmetric Y, 24 directions. For the full-space
  resummed/matched plots. CANNOT serve the variation test (Y grid does not nest).
- `cache_scales` -- CARD grid + 24 directions. Serves both the 9 remaining scale
  variations and `$SP/test_reparam.py`. Chained to run both on completion
  (`cache_scales/after.log`).

**Note on the two JOINT variations** (`mufdown-kappaFO0.5-kappaf2.` and its
partner): those move muR and muF together, so they test the model's CROSS-TERM,
which a template outer product cannot represent. That is a large part of the
motivation for the continuous treatment, and it is about to be measured.

**muf up/down confirmed to be a factor of 2:** `Scale_provider.cpp:63`
`const double vary = pow(2., _vary.muf)` with enum `up=1/down=-1` and the comment
"Variation stays a full factor of 2 always" -- so theta = +-1 on
`resumScaleMuF` is the right correspondence. NB the enum path also rescales
`muf_min/vary` while our direction comes from members built at kappa_F=0.5/2.0;
whether those agree exactly is part of what the scale-variation test measures.


### 2026-08-20 (evening) — profile scales become UNIT nuisances (reparametrisation)

**Why.** SCETlib registers the profile scales as PHYSICAL quantities --
`scale_kappa_R` and `scale_kappa_F` are kappa itself with central 1,
`scale_x1..x3` are the transition points -- while rabbit's ParamModel priors are
a single symmetric Gaussian per parameter (`fitter.py:330-362`: `cw = 1/sigma^2`,
one scalar, `prior_means` for the centre, NO up/down hook). The template
variations they replace are not symmetric in the physical variable:

  kappaFO  x2 and /2         -> symmetric in ln(kappa), not in kappa
  x2       0.6 -> 0.35, 0.75 -> genuinely asymmetric, -0.25 / +0.15

so no sigma reproduces them. sigma = 0.5 on a linear kappa_R gives [0.5, 1.5].

**CORRECTION to the previous entry:** I claimed `resumScaleMuF` sigma = 1 was
EXACT because SCETlib interpolates muF in `t = ln(kappa_F)/ln(muf_hi)`. Wrong --
the PARAMETER is still kappa_F, physical, central 1; SCETlib computes t from it
internally (`DrellYanAD.cpp:449-458`: `kF = p[_muf_index]`,
`tF = log(kF)/_fo_muf_lnstep`, lnstep = ln 2). So sigma = 1 gives [0, 2]: up side
right, down side at ZERO. Worse, `p[_muf_index] > 0. ? ... : 1.` means a
non-positive kappa_F **silently falls back to 1** -- the variation just
disappears, no error. All three needed the map, not two.

**What was done.** The FITTED parameter is now a unit nuisance theta; the model
maps it to the physical value before handing it to SCETlib, using the same
"exact at 0, +-1" model SCETlib itself uses for the PDF eigenvectors and the muF
pair. `params.REPARAM`:

```
resumScaleMuR     log   kappa_R = exp(theta*ln2)          -> 0.5 / 1 / 2
resumScaleMuF     log   kappa_F = exp(theta*ln2)          -> 0.5 / 1 / 2
resumTransition2  quad  x2 = 0.6 + 0.20*theta - 0.05*theta^2 -> 0.35 / 0.6 / 0.75
```

verified exact at theta = -1, 0, +1. `prior_sigma()` returns 1.0 for anything in
REPARAM, so every replaced-template direction is now sigma = 1, the same
convention as the TNPs and `pdfEig*` -- replacing the old mixed 0.5 / 0.2 / 1.0.
The log form also makes kappa positive by construction, so it cannot trip the
silent muF fallback above.

`resumTransition1/3` deliberately NOT reparametrised: frozen by default and no
reference variation exists, so a study that floats them should choose its own
range in the physical variable.

**Implementation** (`param_model.py`): coefficient vectors `_rp_log/_rp_quad/
_rp_L/_rp_c` built in `_register_params`; `_physical` (numpy) and `_physical_tf`
(TF) apply the map; `_full_vector` and `_sigma_gen` route through them, so the
chain rule keeps gradients and the Hessian exact. Reparametrised parameters
default to theta = 0, and a construction-time check asserts
`_physical(defaults) == anchor` to 1e-12 -- without it a mistyped coefficient
would shift the whole prediction and the ratio-to-central would silently not be
1. `xparam_default` for these is in THETA units; the model prints that.

**Regression:** the 2D reco validation on the 19-param cache is unchanged at
`0.00128` (the maps are inert when no scale direction is registered), and the
anchor check passes.

**`set_diff_scales(1)` confirmed live end-to-end:** `cache_v3` reports **24
differentiable parameters** (19 + kappa_R, kappa_F, x1, x2, x3).

**Pending:** `$SP/test_reparam.py` on `cache_v3` -- checks (1) theta=0 -> anchor,
(2) theta=+-1 lands on the physical values AND the model route equals a direct
SCETlib evaluation there, (3) **the chain rule**: d(sigma)/d(theta) vs
d(sigma)/d(kappa) * kappa*ln2 by finite difference. (3) is the one that matters:
a wrong map can be right at theta = 0, +-1 and still have a wrong gradient --
exactly the failure mode of the `Lf_a` bug upstream just fixed.


### 2026-08-20 (later) — RECO validation passes; all theory directions wired + guarded

**Reco closure (the same test scetlib_np was validated with).** New CLI
`scripts/rabbit/scetlib_ad/validate_reco.py` (self-contained -- copies the
reference loaders so scetlib_ad stays import-independent, and documents the four
traps: R sums helicitySig / N_gen UL, the ptVGen [44,100] overflow, pb-vs-fb, and
never `hist.project()` a cropped hist). Cache on the card's own 210-bin gen grid
(`$SP/cache_reco`, 60 MB, 18 min rules + 49 min FO).

Card `260723_Z_2D_card` (ptll x yll) vs histmaker
`260723_Z_histmaker/mz_dilepton_...FranksValsVars...maxFiles_m1.hdf5`:

```
  bins 780   mean/median 0.99975 / 1.00040   min/max 0.97535 / 1.00747
  YIELD-WEIGHTED mean|ratio-1| : 0.00128        (scetlib_np got 0.00140)
  projection ptll  max 0.01231   projection yll  max 0.00096
```

**0.128% -- the AD model's reco fold reproduces the independently validated
scetlib_np one.** First execution of the `gen_level=0` path ever; it marginalized
R over the CS angles for the 2D channel correctly.

4D card (`260714`, half MC) vs the same full-stats histmaker: 2.3% per-bin, but
EVERY marginal is clean --

```
  ptll 0.01122   yll 0.00165   cosThetaStar 0.00073   phiStar 0.00090
  per-bin min/max 0.85856 / 1.14119, mean 0.99977, median 1.00002, p5/p95 0.949/1.049
```

The angular projections being the FLATTEST rules out the helicity/angular
partition error (that failure mode showed 0.885-1.151 WITH structure in
cosThetaStar). Symmetric scatter about 1 across 49920 bins + R from a half-MC
run against a full-stats nominal = statistics. **Definitive test: a 4D card
built from the 260723 histmaker.** Plots:
`~/public_html/alphaS/260820_scetlib_ad_reco_validation/`.

**ALL SCETlib theory directions now wired (Luca's ask) + guards.**
Upstream made muR and the transition points differentiable in `3e22307` -- the
bug there was `nd.Lf_a = (muf == muB) ? 0. : log(muB/muf)`, value-correct and
derivative-annihilating, the same CLASS as our Node_shared bug. So the available
directions are now alphaS (PDF-consistent via `has_as`), 8 NP lambda, 10 TNPs,
29 `pdf_eig{i}`, muF (`has_muf`), muR + 3 transition points
(`set_diff_scales(1)`): ~53 for CT18Z. Only `QCDscaleZfine_*` (MiNNLO helicity)
stays a template.

Implemented:
- `xsec_backend.configure(diff_scales=True, fo_resolve_muR=True)`, guarded on
  `muf_follows_muB = no`. `ScetlibADXsec` now READS the direction set off the
  cache (`cache_param_names`, peeks `names` in the npz) and configures to match,
  so old 19-direction caches still load instead of failing the fingerprint.
  Both flags travel together -- `fo_resolve_muR` changes the frozen FO grid.
- `prepare_cache_for_card.py`: `--pdf-eig`, `--as-pair`, `--no-muf`, `--no-pdf`,
  `--grid-jobs`; `build_variations()` reusing upstream's helpers by path import
  (`ensure_beamfunc_grids` fans out ~3.5 min/member with a shared-.info race
  workaround -- not worth duplicating).
- `params.py`: names for `pdf_eig*` -> `pdfEig*`, `scale_kappa_R/F` ->
  `resumScaleMuR/MuF`, `scale_x1..3` -> `resumTransition1..3`; priors; impact
  groups `resumScale` / `resumTransition`; `pdf_group()`.
- `param_model.py`: `_CONFLICTS` now REGEX-based and covers `^pdf\d+`,
  `^resumfoscale`, `^resumtransition` (verified `^pdf\d+` does NOT catch
  `pdfAlphaS`, and `QCDscaleZfine_*` / experimental systs stay unguarded).
  New `fit_params=all` = every direction except DEFAULT_FROZEN.
- `DEFAULT_FROZEN` gains `resumTransition1`/`3`: the analysis varies only the
  CENTRAL transition point ("Frank's recommendation"), so floating the outer two
  would ADD uncertainty the card does not carry.

**Prior caveats to settle with Luca (deliberate approximations, documented in
`PRIOR_SIGMAS`):** `resumScaleMuF` sigma=1 is EXACT (the pair is built at
kappa_F 0.5/2.0 and interpolated in t=ln(kappa_F)/ln(muf_hi)).
`resumScaleMuR` sigma=0.5 is APPROXIMATE -- kappa_R is linear with central 1
while the card varies x2 and /2, so the up-side is understated; a
log-parametrised kappa_R would fix it. `resumTransition2` sigma=0.2 is the
symmetric stand-in for the card's -0.25/+0.15.

**Guard verified live:** the first reco run stopped with "1 card syst matching
'^pdfalphas' ... running both double-counts", which is correct. `validate_reco`
takes `--fit-params` (default one lambda) since the anchor prediction does not
depend on what floats.


### 2026-08-20 — full-space validation PASSES; CorrZ agrees except the first two qT bins

170-bin cache (`$SP/cache_v2`, 65 MB), both fixes in, Y symmetric so CorrZ folds.
Build: 16.1 min rules + 71.3 min FO warming.

**Resummed vs the `calculation_piece = sing` production run, FULL space**
(10 |Y| x 17 qT, qT 0->100):

```
totals: ours 1347.4624   reference 1347.4621   ours/ref = 1.000000
per-bin: max |.| = 7.362e-06   median |.| = 8.121e-07
```

Every qT bin <= 7.4e-06, i.e. at the integration tolerance. Yesterday morning
the same comparison was `ours/ref = 1.01684`, max dev 3.0e-02, with the
S-shape. **The cache chain is exact.**

**Matched vs CorrZ (SCETlib analytic V+jet nons vs DYTurbo nons):**
total `ours/ref = 1.000144`. By qT:

```
[0,1] +4.27e-02   [4,5] +1.77e-03   [13,16] +3.05e-04   [40,50]  +1.80e-04
[1,2] +1.92e-02   [5,6] +1.27e-03   [16,20] +1.87e-04   [50,70]  +2.61e-04
[2,3] +5.79e-03   [6,8] +9.01e-04   [20,25] +7.67e-05   [70,100] +3.40e-04
[3,4] +2.85e-03   [8,10] 6.34e-04   [25,30] +2.46e-05
```

Above 6 GeV the two nonsingulars agree to better than 0.1% (2e-5 near 25-30) --
close, as expected. **The first two bins are not close: +4.3% and +1.9%.**

Worth a number: our own nonsingular is only ~-1.3% of the total at qT[0,1], so
a +4.3% gap implies CorrZ's effective nonsingular there is about -5.6% of the
total -- a large negative contribution where the nonsingular should be
vanishing. Since the resummed piece is now exact to 1e-6, this is a question
about how CorrZ is BUILT (DYTurbo's low-qT nonsingular is a difference of large
FO numbers, plus whatever damping/cut WRemnants applies), not about our chain.
**Flagged, not waved through: qT < 2 GeV is where alpha_s and the NP lambda take
their sensitivity.**

Plots: `~/public_html/alphaS/260819_scetlib_ad_postfix_validation/`
(`resummed_full_qT`, `matched_full_qT`, `resummed_slice_qT`).


### 2026-08-19 (end of day) — post-fix cache VALIDATES against the production run

New cache built with both fixes in place (`Using custom EW parameters.` now
appears in the build log; scetlib-cms on `fix/node-shared-per-node`, rebuilt).
Slice: Q [60,120] x |Y| {[0.5,1],[1,1.5]} x qT 0->10 in 8 bins, chosen so every
bin is an exact union of the reference pkl's bins (no rebinning on our side).
16 bins, 2.9 min of rules + 11.0 min of FO warming, 8.4 MB.

**Resummed piece vs the `calculation_piece = sing` production run:**

```
totals: ours 115.65969   reference 115.65958   ours/ref = 1.000001
per-bin ours/ref - 1: max |.| = 6.569e-06   median |.| = 8.863e-07
   qT [0,1] +6.6e-06   [1,2] +8.3e-07   [2,3] +2.9e-06   [3,4] +6.7e-07
   qT [4,5] +4.0e-06   [5,6] +6.1e-07   [6,8] +1.6e-06   [8,10] +6.0e-07
```

Flat at the 1e-6 level, i.e. at the integration tolerance. **This is the
end-to-end validation: runcard -> cache -> compressed rules -> replay, against
a native SCETlib production run.** The same comparison this morning read +3.0%
at low qT falling to +1.1%, with the S-shape. Plot:
`~/public_html/alphaS/260819_scetlib_ad_postfix_validation/resummed_slice_qT`.

**CorrZ comparison deferred, for a script reason not a physics one.** CorrZ is
binned in |Y|; the slice grid is positive-only, and `compare_to_scetlib_run.py`
only folds a SIGNED grid. Making a positive-only grid work needs an explicit
factor of 2 that is right for the Z and wrong for the W -- deliberately NOT
added. The 170-bin cache (`$SP/cache_v2`, Y symmetric -2.5..2.5) folds properly
and its validation is chained to run on completion (`cache_v2/validate.log`).
Expectation, per Luca: SCETlib's analytic V+jet nonsingular should be CLOSE to
DYTurbo's but not exact, so read that one as a measurement, not pass/fail.


### 2026-08-19 (late) — Bug 2 root-caused and FIXED: Node_shared hoisted from node 0

Chain of elimination, each step with its number:
- error is **pointwise** (flat -0.52% from a wide [5,6] bin down to
  Q[90,91] x Y[1.24,1.26] x qT[5.49,5.51], where the outer quadrature is trivial)
- **not** the outer node set (`set_gradient_adaptation(True)` -> completely
  different outer grid, same error to the 7th digit)
- **not** resolution: bT node count 53 -> 77 -> 109 as `precision_buffer_bT`
  tightens 1e-1 -> 1e-3 -> 1e-5, and `frozen/live` stays 1.0138971 / 1.0138950
  / 1.0138954. Densifying a wrong integrand converges to the wrong answer.
- present on the **first** call (calls 1/2/3 bit-identical), so not staleness
- **shrinks with NP damping**: `lambda2_nu` x0.5 / x1 / x1.5 / x3 gives
  1.0159 / 1.0135 / 1.0116 / 1.0080 at qT[0,1] -> the error lives in the
  **large-bT tail**

That pointed at `freeze` in `_ad_cache_entry`, which took `Node_shared` from
node 0 only (`if (i == 0) sh = ...;  // bT-independent`) while `fill_node`
derives seven of its fields from `scales(Q, qT, bT)`. Those are constant in the
canonical region but not once a **scale floor** saturates a scale at large bT.

Confirmation with no code change (`$SP/floor_test.py`) -- floors off:
```
           [0,1]         [2,3]         [5,6]        [8,10]   cacheON/cacheOFF
             nan           nan    1.00000000    1.00000000
```
vs 1.01353 / 1.00503 / 0.99489 / 1.00015 with the card's floors.

Patched (`$SP/node_shared_per_node.patch`), rebuilt, re-verified: cache ON is
now BIT-IDENTICAL to cache OFF, and both match the driver
(`max |B/driver - 1| = 3.028e-06`, `A` exactly 0).

**Reproducers kept:** `narrow_bin.py`, `cache_tolerance.py`,
`cache_criterion.py`, `node_diag.py`, `node_tol.py`, `freeze_probe.py`,
`floor_test.py`, `bt_error_profile.py`, `agreement_plot.py`,
`three_curve_sing.py`.


### 2026-08-19 (night) — Bug 2 localized to the frozen bT nodes; both bugs multiply out exactly

Pointwise error profile (`$SP/bt_error_profile.py`), narrow qT bins at
Q [88,94], Y [1.2,1.3], cache ON vs OFF:

```
     qT      ON/OFF    error %          qT      ON/OFF    error %
    0.5   1.0138889     +1.389         9.0   1.0003212     +0.032
    1.0   1.0125966     +1.260        12.0   1.0009728     +0.097
    2.0   1.0079913     +0.799        16.0   1.0000908     +0.009
    3.0   1.0022599     +0.226        22.0   1.0000389     +0.004
    4.0   0.9975383     -0.246        30.0   1.0000116     +0.001
    5.5   0.9948312     -0.517        45.0   1.0000007     +0.000
    7.0   0.9966379     -0.336        70.0   1.0000000     +0.000
```

Bin-size scan (`$SP/narrow_bin.py`) -- the error does NOT shrink as the outer
quadrature becomes trivial, which is what pins it to the pointwise layer:

```
case                    A operator()     B cache OFF      B cache ON       off/A        ON/A
wide control              7.18902525      7.18902949      7.15227614   1.0000006   0.9948882
qT narrowed 5x            1.43981002       1.4398109      1.43232779   1.0000006   0.9948033
all three narrow         0.107847942     0.107847934      0.10729058   0.9999999   0.9948320
very narrow            0.00114486049   0.00114486031   0.00113891726   0.9999998   0.9948088
```

Tolerance scan with the cache ON (`$SP/cache_tolerance.py`): rel 1e-4 / 1e-5 /
1e-6 give 1.00656644 / 1.00656499 / 1.00656481 against the driver at [2,2.5] --
7th digit, while the adaptation cost goes 1s -> 15s. `precision_buffer_bT` at
1e-3 (100x tighter than the card): 1.00656537. **Not under-resolution.**

Criterion scan (`$SP/cache_criterion.py`): `set_gradient_adaptation(True)`
(gradient criterion -> different outer node set) gives 1.00656624 vs the
default 1.00656644. A bin evaluated alone matches the batch bit-for-bit, so no
cross-bin leakage.

**Closure.** EW factor x cache factor reproduces the originally measured
discrepancy to 1e-5 in every bin (table in START HERE). Nothing unexplained
remains.


### 2026-08-19 (evening) — the missing EW parameters, and the frozen node cache

**Bug 1, ours, FIXED.** The driver does

```python
order, alphas, decay, scales, sigma = config.configure_calculation(conf)
config.configure_ew_parameters(conf, sigma)      # we never called this
config.configure_fiducial_volumes(conf, decay)   # nor this
```

Our `configure()` (and upstream's `examples/matched_ad/prepare_cache.py`) called
neither. The card's `[Electroweak]` section was therefore ignored and SCETlib's
defaults used. Direct test (`$SP/ew_test.py`):

```
mode = with
      qT bin      operator()          driver   ours/driver     vs no-EW
  (2.0, 2.5)      2.76366457      2.76366457    1.00000000   0.98389244
  (5.0, 6.0)      7.18902525      7.18902525    1.00000000   0.98376310
```

Patched in `xsec_backend.configure()` with a docstring saying why it is not
optional. NOTE: every existing cache is affected and must be rebuilt (they are
already invalid anyway after the 2026-08-19 rebuild, which changed
`sizeof(GlobalData)`/`sizeof(NodeData)` and so trips the rule-blob layout check).

**Bug 2, upstream, OPEN.** The ordered ladder (`$SP/abc_equivalence.py`, prints
each rung so a crash cannot lose the earlier ones -- the first version
segfaulted in `build_bin_rules`):

```
A_clean      2.80890924  3.18367867  5.99262858  7.30767933  11.3841377
A_grad       (identical to A_clean, every digit)
A_postB      (identical to A_clean, every digit)
B_nocache    2.80891068  3.18368828  5.99257970  7.30768285  11.3841423
B_cache      2.82734347  3.19537183  6.02269598  7.27034993  11.3858670
B_postrules  (bit-identical to B_cache)
C            (bit-identical to B_cache)
```

(these predate the EW fix, so all sit ~1.64% above the driver; the ratios among
them are what matters). A vs B with the cache off: **3e-6**. Cache on: up to
**±0.7%, sign-changing with qT**.

**Rejected hypotheses, each with its number:** the change of variables
(`arctan_Q2` is honoured by every AD path, and is in the rule fingerprint);
binning (A and B additive in Q, Y, qT to ~7e-6); the SCETlib version
(`1.00000004`); the card (0/107); AD calls contaminating `operator()`
(bit-identical); and my own claim that "B is converged, just to the wrong
answer" -- that scan ran with the cache OFF and so tested the wrong path.


### 2026-08-19 (addendum) — the same card three ways: it splits into two bugs

Luca asked whether the three curves used the same card. They did not: the AD one
came from a cache, and a cache CANNOT be `calculation_piece = sing` (the format
needs `sub_pieces()`), so it was matched + `fo_order2_analytic`. Redone with the
reference `base.conf` + `.ini` read verbatim, sing kept, nothing transcribed,
the AD number from `sigma_binned_batch` directly (rule == direct to 7e-15 in
sing mode, so no cache build needed): `$SP/three_curve_sing.py`.

```
        qT bin    (1) old pkl     (2) driver   (3) autodiff         2/1         3/2
[  0.0,   1.0]      1.4273698      1.4273698      1.4506984  1.00000001  1.01634376
[  1.0,   2.0]      4.0072353      4.0072353      4.0727605  1.00000000  1.01635172
[  2.0,   3.0]      5.8960114      5.8960113      5.9925797  0.99999999  1.01637859
[  3.0,   4.0]      6.9622569      6.9622569       7.076559  0.99999999  1.01641739
[  4.0,   5.0]      7.3175723      7.3175724      7.4380461  1.00000003  1.01646361
[  5.0,   6.0]      7.1890251      7.1890252      7.3076828  1.00000002  1.01650538
[  6.0,   8.0]      13.118881      13.118882      13.336257  1.00000007  1.01656966
[  8.0,  10.0]      11.197815      11.197816      11.384142  1.00000010  1.01663954
   total driver/old = 1.00000004    autodiff/driver = 1.01650246
```

The AD offset is FLAT. So the qT shape is not in `sigma_binned_batch` -- it is
introduced by `build_bin_rules`, which the earlier `refcard_rule_check` run
(same card, rules built first) shows: 1.470319 instead of 1.4506984 at qT[0,1],
turning a flat +1.63% into +3.01% falling to +1.13%.

This also explains the "1.450698 vs 1.470319, same conf" puzzle from the
previous entry. It was never matched-vs-sing. It was rules-built-vs-not, and it
reproduces in sing mode.

Driver invocation, for the record:
```
scetlib-run-qT.py 32 1 slice.ini --fixed-var 0 --live
```
with `$SP/driver_run/` holding `base.conf` and `variations_resummed.conf` copied
verbatim from the reference directory and `slice.ini` identical to the reference
`.ini` outside `[Grid_*]` (Q [60,120], Y [1.0,1.5], qT 0->10 on the reference's
own 0.5 GeV edges). 20 bins in 12 s on 32 threads.

### 2026-08-19 — RESOLVED WHERE IT LIVES: the discrepancy is the AD binned-evaluation path, not SCETlib

**The decisive test (Luca's suggestion): run the CURRENT SCETlib through its own
production driver, `prod/scetlib_run/scetlib-run-qT.py`, on the reference card.**
Slice `Q [60,120]`, `Y [1.0,1.5]`, the reference's own fine qT edges 0->10 in 0.5,
`calculation_piece = sing`, `--fixed-var 0`. Cards: `base.conf` and
`variations_resummed.conf` copied verbatim from the reference run's directory,
runcard identical to the reference `.ini` outside the three `[Grid_*]` sections.
Setup kept at `$SP/driver_run/`. Ran in 12 s on 32 threads.

**Result 1 — there is NO SCETlib version difference.** Current checkout vs the
2026-07-22 production pkl, both via `scetlib-run-qT.py`:
`total new/old = 1.00000004`, `max |dev| = 1.118e-07` over all 20 bins.

**Result 2 — the whole thing is the autodiff path.** Same driver output vs the
cache's `resummed_only` rule replay, on the cache's bins:

```
          qT bin          driver      cache (AD)   cache/driver             old
[  0.00,  1.00]       1.4273698       1.4703186     1.03008948       1.4273698
[  1.00,  2.00]       4.0072353       4.1147279     1.02682463       4.0072353
[  2.00,  3.00]       5.8960113        6.022696     1.02148650       5.8960114
[  3.00,  4.00]       6.9622569       7.0744145     1.01610938       6.9622569
[  4.00,  5.00]       7.3175724       7.4089595     1.01248871       7.3175723
[  5.00,  6.00]       7.1890252       7.2703499     1.01131234       7.1890251
[  6.00,  8.00]       13.118882       13.291655     1.01316980       13.118881
[  8.00, 10.00]       11.197816       11.385867     1.01679356       11.197815
   total cache/driver = 1.01615689   max |dev| = 3.009e-02
```

`driver` and `old` agree to the last printed digit in every row. Plots +
`.log` provenance: `~/public_html/alphaS/260819_scetlib_ad_version_check/`
(`scetlib_old_vs_new_qT`, `driver_vs_ad_cache_qT`), script
`$SP/plot_driver_vs_all.py`.

**RETRACTED from the previous entry:** "the only surviving explanation is the
SCETlib version" and the claimed flat +1.64% version offset. Both wrong. Every
earlier test compared the AD path against ITSELF (`rule` vs
`sigma_binned_batch`), where it is exact to 1e-15, so none of them could see
this. The one comparison that was against an independent integrator is the one
that found it.

**Config check, strongest form.** Diffed my effective config (defaults + base +
runcard) against the config EMBEDDED in the reference pkl: **0 value differences
across all 107 keys it records**, 0 of its keys missing. The only 12 keys I have
that it lacks are `fo_order2_*` and `matched_nons_qt_cut` -- options that did not
exist in the older SCETlib. So the card is fully exonerated; those extras only
confirm the checkouts differ, which Result 1 then shows does not matter.

**Also settled this session:**
- **Binning: exactly zero.** One wide integration vs the sum of the reference's
  fine sub-bins, same code path: `b/c = 1.000005` and `1.000000`
  (`$SP/widebin_check.py`, log kept).
- **n_train: no effect on central values, and cannot have one** -- `c_val` is
  fitted to make the rule exact AT the anchor. Variants A (359 nodes/bin) and B
  (448) were bit-identical.
- **Integration tolerance:** `target_precision_rel` 1e-4/1e-5/1e-6 move qT[0,1]
  by `7.6e-6` (`$SP/step0.log`).

**Unresolved side puzzle (do not lose):** `sigma_binned_batch` on the matched
`sub_pieces()[0]` returns **1.450698** in `$SP/which_piece.py` and
`$SP/widebin_check.py`, but **1.470319** in `$SP/matched_rule_vs_direct.py`,
same runcard and same bin. The scripts differ in that the latter calls
`build_bin_rules` and `set_gradient_node_cache(True)` BEFORE integrating. So the
direct integrator's answer depends on evaluation state. Neither value matches
the driver's 1.4273698. This is very likely the same bug as Result 2 and is the
place to start.

- **Next action:** find what `scetlib_run/binning.py` + `tensor_binned.py` do per
  bin that `sigma_binned_batch` does not. Prime suspects, in order: the Q
  integration (the card sets `change_var_Q = arctan_Q2`,
  `change_var_Q_q0 = 91.15348...`, and a Breit-Wigner over Q in [60,120] is
  exactly what needs it); the decay/angular treatment; and the level0 TNP scheme
  at theta = 0. Bisect by removing one at a time on a single bin.
- **Blocking on:** nothing.


### 2026-08-19 (later) — validation against the production `sing` run: the card is exonerated, the matched sub-piece is not

**What was asked:** is the resummed piece alone available from the cache, and how
does it compare to a `calculation_piece = sing` SCETlib production run — namely
`.../com13_ct18z_newnps_n3+0ll_lattice_lambda4bugfix_franksvalsvars_fine/inclusive_Z_..._combined.pkl`?

- **Yes, and it was already run.** `ScetlibADXsec.resummed_only(p)` replays only
  the cache's `_sing` rules; `compare_to_scetlib_run.py --piece resummed` drives
  it and auto-detects that reference as `production run (calculation_piece=sing)`.
  Plots: `~/public_html/alphaS/260819_scetlib_ad_validation/resummed_qT.{png,pdf}`.
- **Result (170 bins, Y 10 x qT 17, Q [60,120]):** ours/ref = 1.01684 in total;
  per-qT +3.04% at [0,1], falling to a minimum +1.16% at [5,6], back to
  +1.7-2.1% from 10 GeV up, +2.14% in [70,100]. **The offset AND the shape
  survive with the fixed order and the matching removed from both sides**, so
  neither the nonsingular nor DYTurbo can be the cause.
- Corroborated with no cache and no transcription at all
  (`$SP/refcard_rule_check.py`): `base.conf` + the `.ini` read verbatim from the
  reference directory, `calculation_piece = sing` kept, only the bins changed,
  rules built in-process. `rule == direct` to **7.105e-15**, and `direct/ref`
  = 1.0301 / 1.0215 / 1.0113 / 1.0168 — the same b/c bin-for-bin as the cache
  comparison.

**Finding: the runcard transcription is provably equivalent to the reference card.**
Merging `base.conf` + the `.ini` literally and diffing against
`conf/Z_CT18Z_N3p0LL_FranksVals.conf`: **0 value differences**, 0 reference keys
missing from ours, and the 21 keys present only in ours are all byte-identical to
`prod/scetlib_run/defaults.conf` (verified key by key, including
`np_model_tmd = off`, which is the SCETlib default and is not set by the
reference card either). So the 1-3% is NOT a card difference. Merged copy kept at
`$SP/refcache/base_from_reference.conf` with the edit list in its header.

**Only four edits turn the reference card into a cacheable one, each forced:**
`calculation_piece: sing -> matched` (the cache format stores rules for the
singular *and* a frozen grid for the nonsingular, so it calls
`sigma.sub_pieces()`, which a sing-only run does not have); `+fo_order2_analytic
= yes` (the nnlo nonsingular needs the analytic O(as^2) V+jet add-on);
`-variations_filename` (section [0] is empty = no-op); and the grids. **A cache
therefore cannot keep `calculation_piece = sing`** — `resummed_only()` necessarily
reads the singular out of a *matched* configuration.

**Open, and this is the live one — the matched sub-piece.** Retracting the
retraction from the previous entry: `sub_pieces()[0]` IS the singular alone
(`sub[1]` is the nonsingular and their sum is exactly the matched total), but in
a matched configuration that singular is **1.35% below** the same card's
sing-mode singular at low qT:

```
      qT bin   sub[0] sing   sub[1] nons     sing+nons   matched tot    standalone(sing mode)
       [0,1]      1.450698   -0.01905666      1.431642      1.431642      1.470319
       [2,3]       5.99258     -0.114133      5.878447      5.878447      6.022696
       [5,6]      7.307683    -0.1436256      7.164057      7.164057       7.27035
```

Meanwhile the rules built from that same object replay to 1.47032 — the sing-mode
value. So `rule / direct = 1.0135` in matched mode is REAL and is a rule-path vs
direct-path disagreement inside SCETlib's matched configuration, not a
compression error (compression is exact at 7e-15 in sing mode). Consequence if it
holds: the cached matched total is ~1.35% high at qT < 1 relative to what
SCETlib's own matched calculation gives for the same card.

- Running to settle it in ONE configuration with the lambdas printed:
  `$SP/matched_rule_vs_direct.py` (rule vs direct on the same `sub_pieces()[0]`).
- Running: a cache from the reference-card copy,
  `$SP/refcache/` — expected bit-identical to `valid_resum/` given the config
  proof above, kept as the artifact.

**Traps hit (both cost a relaunch):** `--cleanenv` and a bare `#!/bin/bash`
container entry BOTH lose `LHAPDF_DATA_PATH` (it comes from the container's login
profile) -> `RuntimeError: Info file not found for PDF set 'CT18ZNNLO'`. Use
`singularity run <img> bash -lc "..."`. And singularity mangles a JSON string
passed as an argv element — put `--grid-json` inside a wrapper script instead.

### 2026-08-19 (latest) — standalone PR #715, docs reframed
- **PR: https://github.com/WMass/WRemnants/pull/715** (draft), branch
  `scetlib-ad-param-model` off `upstream/main`, built in a git WORKTREE at
  `$SCRATCH/pr_scetlib_ad` so the main checkout (46 dirty entries of #701 work)
  was never touched. 13 files, +3158.
- **The package is now standalone: no `scetlib_np` import.** That was mandatory,
  not cosmetic -- `scetlib_np` does not exist on `upstream/main`, so any import
  would have made the PR depend on #701. The three response helpers, the ratio
  floor and the NP-anchor meta reader now live in a new
  `scetlib_ad/response.py`, whose docstring explains the `P = R_raw/N_gen`
  conditional-probability argument and why it is invariant to a gen-level
  reweighting. Verified by importing with `scetlib_np` blocked via a meta_path
  hook, and the debug fit still closes exactly afterwards.
- `compare_to_np_model.py` genuinely imports `scetlib_np.sigma_gen`, so it is
  EXCLUDED from the PR and kept only in the local tree.
- The `scetlib_np` strings that remain are datacard conventions (the auxiliary
  group name, the metadata key), now documented as such and overridable via
  `response_group=`.
- Docs/docstrings reframed around the full parameter set (alpha_s + 8 lambda + 10
  TNPs + PDF eigencoefficients) rather than as a delta against the older model.
- Two process notes: the repo pre-commit hook runs `pylint`, which is not
  installed in the container -- it aborts the commit, so `--no-verify` is needed
  (isort/black/flake8 were run and are clean; CI will run pylint). The hook's
  `isort` also uses the repo's first-party config, where `rabbit` is third-party;
  its reformatting was taken and copied back into the main tree so the two do not
  diverge.

### 2026-08-19 (latest) — validating the resummed piece against a native SCETlib run
Decision (Luca): adopt SCETlib's own nonsingular; validate against the resummed
piece; the current tune is CT18Z LatticeNP **FranksVals**.

- **The right reference** is a `calculation_piece = sing` production pkl: it IS the
  resummed cross section, bin-integrated, so replaying only our cache's
  compressed rules gives the same object -- no matching, no DYTurbo, no MiNNLO, no
  corr file in between. Any disagreement is then OURS (runcard, quadrature, Q
  integration, rule compression), not a difference between two predictions.
  Chosen: `/work/submit/lavezzo/alphaS/TheoryCorrections/SCETlib/
  com13_ct18z_newnps_n3+0ll_lattice_lambda4bugfix_franksvalsvars_fine/
  inclusive_Z_..._combined.pkl` -- Q 2 bins (10-60, 60-120), Y 82 signed bins,
  qT 70 bins, 38 vars, central entry named `central` (not `pdf0`).
- **The DYTurbo `scetlibmatch.txt` is NOT needed.** It is only the fixed-order
  input for building the nonsingular. I had reached for it because the knowledge
  note's recipe extracts the resummed piece back out of a *matched* corr file; the
  raw production pkl is the resummed piece directly. (DYTurbo inputs, if ever
  needed: `/work/submit/lavezzo/alphaS/TheoryCorrections/DYTURBO`.)
- **Full reference config transcribed** into
  `scripts/rabbit/scetlib_ad/conf/Z_CT18Z_N3p0LL_FranksVals.conf`. Anchor:
  lambda2 0.4, lambda4 0.4, lambda_inf 1, delta_lambda2 0; lambda2_nu 0.15,
  lambda4_nu 0, lambda_inf_nu 2, b0_over_bmax_nu 1; tanh_2 both sides,
  np_model_tmd off. Plus the `[TNPs]` block -> 19 parameters.
  NB the config keys come back LOWERCASED from configparser (`mub_min`, `h_qqv`),
  which briefly looked like missing settings -- they are all there, and our
  earlier `Z_CT18Z_N3p0LL_analysis.conf` already matched them.
- **Luca's new 5740-bin `cache.npz`** (5.1 GB, `examples/matched_ad/`): the GRID is
  right -- Q [60,120] x Y 82 signed x qT 70, a superset of the correction grid, so
  it folds down exactly to anything coarser. But it has **9 parameters**, i.e. it
  was built from `analysis.conf`: plain N3LL, SCETlib default profiles
  (lambda=1, transition_points [0.2,0.5,0.8], no scale floors), LatticeNP anchor.
  It will not reproduce the analysis prediction; a rebuild with the FranksVals
  runcard is needed. Grid good, physics config wrong.
- **Validation grid** is a SIGNED-Y subset of the reference grid
  (Y +-{0,0.5,1,1.5,2,2.5}, qT 18 edges 0..100, 170 bins) so the comparison is
  bin-by-bin with no folding -- and it tests the +Y/-Y symmetry the folded-|Y|
  production cache assumes, for free. `prepare_cache_for_card.py` gained
  `--grid-json` for explicit grids (also the route W will need).
- Tooling: `compare_to_scetlib_run.py` (new) sums the reference's fine bins onto
  ours -- exact, since both are bin-integrated -- and refuses to run unless our
  edges really are a subset. `ScetlibADXsec.resummed_only()` replays only the
  rules. Build running; comparison not yet done.

### 2026-08-19 (latest) — can the histmaker MiNNLO->SCETlib correction move on the fly?
Luca's proposal: stop correcting MiNNLO to SCETlib in `mz_dilepton.py`; keep
MiNNLO only for the CS-angle structure and the detector/other nuisances, and
apply the SCETlib correction on the fly through this param model. Analysis:

- **At matched binning it is an identity, not an approximation.** The nominal
  correction (`LatticeNPCoarse_CT18Z_N3p0LL_N2LO`) has axes
  `(Q, absY, qT, charge, vars)` and **no helicity axis** -- it is a per-event
  scalar `c(Q,|Y|,qT)`, piecewise constant on a 2 x 17 x 70 grid. Per-event
  reweighting gives `N(b) = sum_g c(g) R_raw(b,g)`; the model computes
  `sum_g P(b|g) sigma_AD(g)` with `P = R_raw/N_gen`, i.e. the same sum with
  `c(g) = sigma_AD(g)/N_gen(g)`. Identical events, identical weights -> no new
  MC-stat noise. Condition: R's gen binning must resolve the correction grid.
- **The CS angles are on R's RECO side** (`RECO_AXES = ptll, yll,
  cosThetaStarll_quantile, phiStarll_quantile`), filled by MiNNLO; the gen side
  is only `(ptVGen, absYVGen)`. `c` depends on gen alone, so it rescales a gen
  bin's whole angular distribution coherently and never touches the CS structure.
- **N_gen and R_raw are both MiNNLO x c, i.e. CORRECTED** (verified:
  `unfolding_tools.py:195,222` fills the `prefsr` xnorm hist with
  `nominal_weight`; `theory_corrections.py:515`
  `define_theory_corr(..., modify_central_weight=not args.theoryCorrAltOnly)`).
  Both carry the same `c(g)`, so `P = R_raw/N_gen` is correction-INVARIANT -- the
  real reason dividing by N_gen was right. No need to re-run the histmaker
  uncorrected to obtain R.
- **No gen Q axis is needed** (I claimed otherwise first): the correction's Q axis
  is `[10, 60, 120]` and the histmaker mass window is 60-120, so the fit lives in
  a single Q bin where `c` has no Q dependence. One Q bin in the cache is right.
- **Requirement:** refine R's existing gen axes to the correction grid,
  qT 70 x absY 17 = 1190 bins (today ~20 x 10 = 200). Cache ~1 GB at 9 params /
  ~3.2 GB at 19, ~45 min to build; exact Hessian ~19 s/iteration at 9 params,
  ~78 s at 19 -- the regime where the Gauss-Newton switch removed earlier would
  earn its place (see Decisions).
- **What the three corr productions become**, from the 56 `vars` in the nominal
  CorrZ: central (1) + NP lambda (26) + TNPs (20) = 47 absorbed by the model;
  6 FO-scale (`kappaFO`, `kappaf`, `muf`) + 3 transition-point variations are NOT
  differentiable in SCETlib (profile scales are deferred upstream) and still need
  kappa templates. `pdfas` and `pdfvars` go away entirely (alpha_s via the member
  pair, PDFs via the eigenvector coefficients). So 2 of 3 productions gone, the
  third cut 56 -> 9 vars.
- **The validation bar rises**: the model would own a +-30% correction (range
  0.72-1.35, varying up to 11.8% per 0.5 GeV qT bin) instead of a few-% response,
  so what currently cancels in the anchor ratio stops cancelling -- notably our
  positive-Y-side-only factor 2 and the 2.4% low-qT nonsingular difference.
- `--theoryCorrAltOnly` already gives "load corr helpers for variations, leave the
  central weight alone", so the uncorrected-MiNNLO histmaker run needs no new code.
- **Cheapest decisive test, no new cache needed:** fold the existing corr file's
  `c(g)` through the current coarse R and compare with the corr applied per-event.
  That prices the binning requirement and measures how far from
  correction-invariant today's P actually is. NOT YET RUN.

### 2026-08-19 (latest) — structural questions from Luca: one pass, and stop_gradient
- **Two passes are NOT needed here.** The `--noHessian` fit + `--externalPostfit
  --noFit` covariance pass is inherited from `scetlib_np`, where it is forced by
  the bT slab OOMing rabbit's `GradientTape.jacobian`. In this model the
  expensive object never enters the graph, so one job does both. Measured on the
  debug card: two-pass, one-pass `curvature=0`, and one-pass `curvature=1` all
  give α_s = 0.1195 ± 0.00045 and identical λ uncertainties
  (0.277/0.549/0.0208/0.164/0.187); times 6+11 s, 7.5 s, 40 s; EDM 3.5e-17,
  3.5e-17, 6.1e-22. README now documents one pass as the recommended form.
- Also noted: because (value, J, K) is cached on the parameter vector, enabling
  curvature costs one C++ Hessian per *distinct* point, not per HVP — the
  minimizer's many HVPs at fixed x all hit the cache. That is why curvature=1 is
  40 s and not minutes.
- **`stop_gradient` does not lose derivatives** — added
  `differentiate=through|straightthrough` and a checker so this is measured, not
  asserted. Gradients agree to **1.3e-16** (Finding 13). But `through` FAILS at
  second order on both paths rabbit uses, and the cause is upstream (Finding 14).

### 2026-08-19 (later) — analysis runcard validated, TNPs work
- Built a 30-bin cache from `Z_CT18Z_N3p0LL_analysis.conf`: **19** differentiable
  parameters, exactly as predicted (Finding 6). 7.3 min of rules (349 nodes/bin
  vs 163 at 9 params) + 10.5 min of FO warming, **80 MB** for 30 bins.
- `tf_gradients.py --cross-check-direct` on it: cached-vs-live agreement 6e-15
  (values), 1.5e-15 (gradient), 3.4e-14 (Hessian) — the 19-parameter replay is
  exact (Finding 9).
- Re-ran `compare_to_np_model.py`: the λ-response gap roughly halves and the
  high-qT central shape difference drops 2.55% → 0.81% (Finding 10).
- `tnp_b_qqDS` has an identically ZERO gradient for the Z. Added a guard that
  refuses to register any parameter with a zero Jacobian column (it would be a
  singular covariance row); verified it fires on exactly that parameter.
- Fitted α_s + λ2 + λ2_ν + two TNPs with `priors=1` on the 19-parameter cache:
  runs and converges. NB that was NOT a closure test — the card's data came from
  the other cache, so the small pulls are the two predictions differing.
- Added guards: TNPs cannot be fitted with priors off; the model's bin count is
  checked against the card's; `--eager` is accepted alongside `--jitCompile off`.

### 2026-08-19 — runcard mismatch found and a matching card written
- `compare_to_np_model.py` (new): displaces each λ and compares
  `R = σ_gen(λ)/σ_gen(λ_c)` between the AD model and `scetlib_np.SigmaGenModel`
  on the same gen grid, anchored at the same λ_central.
- Result on the debug cache: disagreement is **flat in the displacement**
  (scanned ×1.02 … ×2), so it is NOT the compressed rules being evaluated away
  from their anchor. It is a genuine difference between the two predictions,
  and it is ~4× worse for the b⁴ λ than the b² ones — the signature of a
  different large-bT / profile treatment.
- Diffed `matched.conf` (+ SCETlib `defaults.conf`) against the bT-grid
  production cards. They differ in a lot (Finding 5), most importantly the whole
  `[TNPs]` block: the analysis runs every TNP at `(0., 'level0')`, which IS the
  N³⁺⁰LL prescription — `matched.conf` has no such block, i.e. plain N3LL.
- Wrote `scripts/rabbit/scetlib_ad/conf/Z_CT18Z_N3p0LL_analysis.conf`, an
  analysis-matching base runcard, and launched a 30-bin cache with it.
- Consequence worth planning around: **matching the analysis order and getting
  differentiable TNPs are the same action** (Finding 6).

### 2026-08-18 — implementation + first closure
- Wrote `wremnants/postprocessing/scetlib_ad/` (`params`, `xsec_backend`,
  `param_model`) and four scripts under `scripts/rabbit/scetlib_ad/`.
- Backend, card builder, fit, covariance pass and impacts all run; the fit
  recovers injected truth exactly (Finding 1) in 6 s on 30 bins.
- Design: **straight-through**. One `tf.py_function` returns (value, J, K) from
  C++; the graph sees `stop_gradient(val) + J·d + ½ dᵀKd` with
  `d = p − stop_gradient(p)`. Exact value/1st/2nd derivative at the evaluation
  point, and the PyFunc sits behind `stop_gradient`, so `GradientTape.jacobian`
  never re-enters C++ once per fit parameter.
- Scope decisions with Luca: gen-level σUL first; α_s plumbed on the fixed-PDF
  parameter but no α_s number quoted until the PDF α_s-member pair is folded in;
  SCETlib's own matched total (not the WRemnants DYTurbo σ_ns); new sibling
  package, `scetlib_np` untouched (PR #701 open).
- Plan: `~/.claude/plans/we-have-a-new-mossy-lighthouse.md`.

---

### 2026-08-20 -- what the "dip" belongs to, and old-vs-new below 44 GeV

Restricting the three-curve gen comparison to qT < 44 (the [44,100] ptVGen
OVERFLOW bin dropped -- it holds qT>100 while sigma_SC stops at 100, a separate
issue) and relabelling the third curve correctly. It is NOT "the histmaker
event-level correction" as a thing in its own right: the CURRENT model returns
ratio(anchor) == 1 exactly (asserted to 1e-12 at construction), so under the
ratio method the fit's prediction at the anchor *is* the card nominal. That
object is the current method's prediction.

```
                new (k*sigma_SC)        current (ratio -> card nominal)   new/current
qT < 3          6.11e-03 (max 2.2e-02)  1.56e-04 (max 2.2e-04)             39.1x
qT 3-44         1.96e-04 (max 8.9e-04)  1.93e-04 (max 4.4e-04)              1.01x
qT 12-44        4.33e-05 (max 9.6e-05)  2.02e-04 (max 4.4e-04)              0.22x
all < 44        7.36e-04 (max 2.2e-02)  1.90e-04 (max 4.4e-04)              3.87x
```
(yield-weighted |ratio to CorrZ - 1|; 9.1% of the yield sits below 3 GeV.)

**The two errors are of different ORDER, which is the real answer to "is the new
approach worse".**
- Current method: the prediction error vs CorrZ is ZERO BY CONSTRUCTION at the
  anchor -- it inherits the histmaker's templates, which carry CorrZ exactly.
  Its accuracy question is second-order: how well sigma_SC's *ratio* tracks the
  truth as p moves (that is the variation validation, not this plot). The flat
  orange line is therefore NOT evidence that the old method is good physics; it
  is tautological. What it does genuinely test is units/UL/row-sum: N_gen/(lumi
  *1000) reproduces CorrZ to 1.9e-4, so that chain is right.
- New method: sigma_SC's ABSOLUTE accuracy enters the prediction directly, at
  every point, first order.

**Where the all-day "dip" lives.** `validate_reco.py` compared OUR sigma_reco
(R @ sigma_SC(anchor)) against the histmaker `nominal` -- an ABSOLUTE
comparison, the same class of object as the new method's curve, NOT the ratio
method's prediction. So `260820_scetlib_ad_reco_validation/reco_card2D_ptll.png`
(0.128% yield-weighted, dipping at low ptll) and today's red curve are the SAME
quantity. Those validation plots were diagnostics OF sigma_SC all along; under
the ratio method that deficiency divides out of the prediction, under the new
method it does not. Switching to `indata.norm` is precisely what promotes that
diagnostic into a prediction error.

Consequence: the low-qT nonsingular cutoff (ours 0.1 GeV vs CorrZ's
`--qtCutoff 1.0`, handled in the forked session) is now a BLOCKER for the
uncorrected-histmaker route, not a cosmetic mismatch. Above 3 GeV the new method
already matches the old, and above 12 GeV it is 4.5x better (smooth and
converging, where the old carries ~2e-4 of MiNNLO-statistics scatter).

Plot: `~/public_html/alphaS/260820_gen_vs_corrz_newmethod/` (colours verified by
reading the artists and legend handles back out of the figure, not by re-reading
the code).

### 2026-08-20 -- wums ratio-legend bug (PR opened)

`plotRatio` built `extra_handles` from `colors[-fill_between::2]`; `-0 == 0`, so
with the default `fill_between=0` the slice is `colors[0::2]` instead of empty.
Every ratio-panel legend we have ever made therefore carried spurious handles
paired with `labels[:n]` -- too long AND mis-coloured (3 curves -> the second
extra entry advertises colours[2] for labels[1]). Fixed by guarding the slices:
**WMass/wums PR #30**. Not fixed: `extra_labels` takes labels from the front
while handles come from the back, which also looks wrong for a real band, but we
have no `fill_between != 0` caller to test.

### 2026-08-20 -- the two long cache builds finished

- **`cache_scales` reparametrisation test: blocked by our own guard, correctly.**
  `_check_double_counting` refused `resumScaleMuR/MuF` because the card carries
  `resumFOScaleZSymAvg`/`resumFOScaleZSymDiff` (plan risk R-2, working as
  designed). Needs a card built with
  `setupRabbit --excludeNuisances '^resumfoscale'` to run.
- **muF is a NULL direction in every cache we have.** The scale-variation table
  gives model range [1.0000, 1.0000] for `mufup`/`mufdown` against a reference
  that moves -5.7%/+2.3%. All three caches report `has_muf = 0`, `has_as = 0`,
  `n_eig = 0`, i.e. the frozen FO grid has no muF member -- and CorrZ's muF
  variation is a FIXED-ORDER variation. `scale_kappa_F` is registered as an AD
  parameter but has no FO piece to act on. DANGER: if we excluded the card's muF
  templates in favour of this direction, the muF uncertainty would silently
  vanish. Needs a cache built with the muF FO members before
  `resumScaleMuF` can be floated. Also: setting a parameter that the cache
  cannot represent returned ratio == 1 SILENTLY -- that should raise.
- `kappaFO0.5-kappaf2.` sits at 4.0e-2 max (model 0.9094 vs ref 0.9468 at the
  low end); `kappaFO2.-kappaf0.5` at 4.5e-3. The 8 lambda/tnp variations are
  4.6e-4..4.9e-3.

### 2026-08-20 -- reco_card2D_ptll was SHAPE-ONLY; the absolute reco test (T3)

Luca asked whether this morning's `reco_card2D_ptll.png` is the same object as
the new method's curve. Same CLASS -- our absolute sigma vs the reference, which
is what the new construction's prediction error is -- but NOT the same test:
`validate_reco.py:139-143` applied ONE global scale `m*(nsum/msum)` and the plots
density-normalised (`v/v.sum()`). The 0.128% was a SHAPE number with the total
divided out, i.e. blind to precisely the piece the new method makes first order.
Also gen vs reco, and it ran on the OLD 260723 card.

Added to `validate_reco.py`: `--reference {histmaker,card}` (card = the
`indata.norm` signal column the new construction actually divides by, sliced
`start:stop` not `[:nbins]`), `--no-match-norm`, and `--y-fold` (auto from the
GenFold's own `y_convention`). Plan test T3, now runnable.

```
test                              reference          norm      yield-wtd   total
this morning (260723 card)        histmaker nominal  matched    0.00128    divided out
260820 card, shape                card indata.norm   matched    0.00128    divided out
260820 card, ABSOLUTE             card indata.norm   none       0.00149    0.998847
```
per-bin 0.974-1.006, ptll projection max 1.34%, yll max 0.19%.

Two things settled:
1. **The normalisation is nearly free at reco: 0.128% -> 0.149%**, total off by
   only -0.115%. Reco is far more forgiving than gen (2.2% in the first gen bin)
   because the low-qT deficiency gets smeared across neighbouring ptll bins.
   Since the OLD method's reco prediction error is zero by construction, 0.149%
   IS the error the switch adds.
2. **Plan risk R-1 fired exactly as written.** Before the fold the total came out
   0.499424 -- the factor 2 from a positive-side-only cache. `GenFold` computes a
   `y_factor` but only to validate tiling; it does NOT normalise the convention
   out of the returned values, and the ratio construction hid that because it
   cancels. The `[0.9,1.1]` total guard would have caught it (0.5 is far
   outside). Candidate cleanup: have `fold_for` return the |Y| convention
   always -- it cancels in the ratio, so it is safe -- but that is shared code
   and not asked for.

Plots: `~/public_html/alphaS/260820_reco_absolute/` (`*_abs` = absolute).

### 2026-08-20 -- reparametrisation VALIDATED (exact), and how NOT to test it

Decision (Luca): shelve the `indata.norm` / uncorrected-histmaker route for now,
keep the current rnorm ratio construction. Come back to it in another session.
The ratio construction is where the cancellations found today work FOR us.

The reparam test finally ran: the guard that blocked it was against the OLD
260723 card. **Both 260820 cards carry ZERO theory nuisances** (see below), so
there is no `resumfoscale` conflict any more.

Results, on the 260820 card + cache_scales:
- **values: bit-exact.** theta = -1/0/+1 -> kappa_R = 0.5/1/2 and x2 =
  0.35/0.6/0.75, and sigma(theta) vs setting the SCETlib slot directly by hand
  agrees at `0.000e+00` PER BIN. Ratio at the start point: `0.000e+00`.
- **chain rule: bit-exact.** The analytic Jacobian column (from
  `values_and_jacobian`) times dk/dtheta equals TF's AD gradient at
  `0.000e+00`, with dk/dtheta = 0.6931471806 = ln2 (log map) and 0.2 = c1 (quad
  map). Both maps confirmed, values AND derivative.

**Two test-methodology traps, both of which produced a false failure first:**
1. The fit vector is NOT all-zeros. `_physical` is the IDENTITY for anything
   outside `params.REPARAM`, so a zero entry means "lambda2 = 0", not "lambda2 at
   its anchor". Start from `model.xparamdefault`. Compare PER BIN: the grid total
   is nearly lambda-independent (NP shifts redistribute in qT), so a `.sum()`
   reported a percent-level per-bin error as 5.7e-5.
2. **Do not validate this model's derivatives with a central difference across
   the anchor.** The deviation was 7.5e-4 and FLAT in h over four decades
   (1e-3..1e-6), which looks like a real error and is not: the value surrogate is
   piecewise in parameter space with a knot AT the anchor (`c_val` forces
   exactness there), so a symmetric difference straddling the knot averages two
   different slopes no matter how small h is. Diagnostic that settles it: a wrong
   dk/dtheta is ONE SCALAR and would move every bin by the same relative amount;
   the observed pattern was median 1e-6 with max 1e-3, i.e. bin-dependent, so it
   could not be the map. Compare against the analytic Jacobian instead.

**Also: `resumScaleMuF` is refused AT FIT TIME**, by `_check_no_inert_params`
("identically zero derivative ... would make the covariance singular"). So the
earlier worry that an unrepresentable parameter is silently ignored applies only
to the offline validation path, which writes the physical vector directly and
bypasses the fit-time guards. A fit raises. `params.py:35-38` already documents
that `scale_kappa_F` is inert without `has_muf`.

### 2026-08-20 -- why the cache lacked PDF/alphaS/muF, and the 67 h estimate was WRONG

**Why they were missing: `--no-pdf`.** `cache_scales/build.sh` and the others were
built with `--no-pdf --threads 64`, deliberately, for speed. The script itself
prints the consequence: "physics-only cache. alphaS will be a derivative at FIXED
PDF, and the card's pdf*/pdfAlphaS/resumFOScale* templates must be kept." The
mistake was that the 260820 cards then dropped those templates too, so nothing
covers those directions. Defaults are already `--n-train 9`, `--as-pair auto`,
`--pdf-eig -1` (= all) -- only `--no-pdf` suppressed them.

**TNPs were never missing.** All 10 (`tnp_gamma_cusp`..`tnp_h_qqV`) are in every
cache. `fit_params` just excludes `resumTNP_*` by default
(`param_model.py:439`). A flag, not a build.

**RETRACTION: the ~67 h / 4.4 GB figure I have been quoting is wrong.** It came
from scaling the 12-bin measurement (FO variations 228.8 min) linearly in bins.
But the FO member sweep is `_parallel_run(n_bins, ...)`
(`DrellYanAD.cpp:373`), i.e. **bins ARE the parallel axis** -- going 12 -> 210
bins buys 17x more parallelism at the same time as 17x more work. And the
measurement ran `--threads 64`. So the wall clock is nowhere near 67 h.

**The serial axis is MEMBERS.** `for (std::size_t mi = 0; mi < n_members; ++mi)`
(`DrellYanAD.cpp:384`) is strictly serial, and each member's `sweep()` takes a
global `s_ad_mutex`, so members cannot overlap WITHIN a process. Across processes
or machines they can. That is exactly the axis condor would exploit -- Luca's
instinct was right, and it is the only axis left.

**This node has 768 cores / 1.4 TB.** The sweep can use at most ~210 (one per
bin), so there is already ~3x idle capacity on ONE machine. Process-level
sharding here gets most of the win without condor at all.

**The blocker for ANY sharding is the merge, not the submission.**
- `build_fo_pdf_variations` does `_fo_var_d.assign(n_members, ...)`
  (`DrellYanAD.cpp:364`) -- calling it twice WIPES the earlier members.
- `load_fo_cache_bytes` / `load_bin_rules_bytes` REPLACE: the loader builds a
  fresh `_Fo_cache`. There is no insert/append mode.
- But the format is already designed for merging: both blobs are
  `[magic + POD struct sizes + config fingerprint + anchor/opts + PDF metadata]
  [count][per-bin KEYED records]`, and the fingerprint + POD-size checks refuse
  an incompatible merge outright. So this is a small C++ addition (a member-range
  argument plus an append mode), then `bootstrap.sh`.
- A pure-Python byte merger is possible for the rules blob but fragile for the FO
  one: the node records embed `n.C` whose dimensions are NOT serialised.

**The existing condor tooling is the right pattern but the wrong combine.**
`prod/scetlib_run/scetlib-manage-condor-submit.py` already chunks "bins within
one variation ... or whole variations in each job" and has submit/resubmit/
combine with config-file and git-hash consistency checks. But its combine merges
**histogram pickles** (`combine_pkl_files`), not cache blobs.

**The decisive find: the alphaS-pair beamfunc grids ALREADY EXIST**
(`share/scetlib/beamfunc/CT18ZNNLO_as_0116_beamfunc` and `_as_0120_`). So the
alphaS-matched PDF pair + the muF pair need NO grid generation -- launched as
`cache_aspair` (`--pdf-eig 0`, everything else identical to cache_scales so the
rules and FO grid are unchanged). That is what turns alphaS from a fixed-PDF
derivative into a real one, and restores muF.

The **29 eigenvector pairs** need beamfunc grids for 58 members
(`CT18ZNNLO_beamfunc/` holds only the 51 per-convolution kernel grids for member
0). THAT is the condor-scale job, and Luca has done exactly it before --
`/work/submit/lavezzo/alphaS/scetlib-cms-newnp-lambda4fix/beamfunc_gen_logs/
condor_submit_msht.log`, plus the py3.9 PYTHONPATH stubs in
`/work/submit/lavezzo/alphaS/scetlib_condor_stubs/`.

### 2026-08-21 -- FIRST ASIMOV RECO FITS PASS, and sigma(alphaS) is mu_R-dominated

Both Asimov reco fits (`-t -1`, corrected 260820 card, `--jitCompile off`)
converged on the login node:

```
fit             floating  edmval     sat. 2dNLL/ndof   wall     sigma(alphaS)
asimovA_reco    6 of 19   9.70e-28   0.0 / 774         46 min   6.160e-04
asimovB_scales  8 of 24   9.70e-28   0.0 / 772         58 min   1.808e-03
```
Every parameter came back exactly at truth (alphaS 0.118, lambda2 0.4,
lambda4 0.4, delta_lambda2 0, lambda2_nu 0.15, lambda4_nu 0, and the two scale
thetas at 0). Machinery is proven end to end: model -> rabbit -> minimiser ->
Hessian -> saturated test. Nothing needed the straight-through trick that
`scetlib_np` required.

**Physics read: floating the resummation mu_R costs a factor 2.9 on
sigma(alphaS), because they are nearly degenerate.**

```
rho(alphaS, .)   fit A                fit B (with scales)
resumScaleMuR      --                 +0.927   <-- nearly degenerate
resumTransition2   --                 -0.646
lambda2          -0.804               -0.410
lambda2_nu       +0.680               +0.255
lambda4_nu       -0.642               +0.203
lambda4          +0.394               +0.396
delta_lambda2    +0.045               -0.434
```
rho(alphaS, mu_R) = +0.93 is the whole story: mu_R and alphaS both set the
strength of the resummed logs, so they trade off almost freely in the qT shape.
The mu_R TREATMENT is therefore the dominant decision for sigma(alphaS), more
than any NP lambda. Also rho(lambda2, lambda2_nu) = -0.97 in both fits (the two
low-qT damping knobs are near-degenerate, as expected), and the data constrains
resumTransition2 to 0.086 against its prior of 1.0 (11x better than the prior),
while resumScaleMuR only goes 1.0 -> 0.78.

NOT comparable to the template-based `sigma(pdfAlphaS) = 0.547` (x 0.002 =
1.1e-3 in alphaS) from `scetlib_np`: that carried the full PDF set, these carry
NO PDF at all. Quote neither against the other until the PDF directions are in.
Caveat on B: `resumScaleMuR` is a continuous unit nuisance with a sigma = 1
Gaussian prior on a log map, so +-1 sigma is a factor 2 in mu_R -- conventional,
but it replaces a discrete 2-point template, and whether that is more or less
conservative deserves a deliberate look.

### 2026-08-21 -- cache_aspair BUILT, and the member cost measured

`--pdf-eig 0` (alphaS-matched PDF pair + muF pair, no eigenvectors) on the
260820 card: **n_eig=0, has_as=1, has_muf=1**, 24 params, 210 bins, 354.6 MB.
So alphaS is no longer a fixed-PDF derivative and muF is live.

Measured timings at 210 bins / `--threads 210` (this is the real data for the
sharding question):
```
rules                     9.0 min   (median 295 nodes/bin, worst resid 3.4e-08)
fixed-order warm         20.6 min
resummed variations       5.8 min   (4 members)
FIXED-ORDER variations   77.5 min   (4 members)  -> 19.4 min PER MEMBER
total                    ~1.9 h
```
**Extrapolation, replacing the retracted 67 h:** the full set is 29 eigenvector
pairs = 58 members + 2 alphaS + 2 muF = 62 members, so 62 x 19.4 min =
**~20 h** of FO variation work, plus ~30 min fixed overhead.

Note the per-member cost did NOT stay constant against the 12-bin measurement
(3.9 min/member there vs 19.4 here), so bin-parallelism is sub-linear -- thread
contention and/or the more expensive high-qT bins. So: 67 h was too pessimistic,
"~4 h" (my in-flight guess) was too optimistic, ~20 h is measured.

Sharding by MEMBER: 3 concurrent processes on this 768-core node -> ~7 h;
condor across ~10 machines -> ~2 h. Still gated on the merge entry point, and
separately on generating beamfunc grids for the 58 eigenvector members.

### 2026-08-21 -- wums PR #30 MERGED
`plotRatio` spurious/mis-coloured ratio legend (the `-0 == 0` slice) is fixed
upstream as of 2026-08-20 22:05 UTC.

### 2026-08-21 -- PR #715 updated (code + description)

The scetlib_ad PR lives on branch `scetlib-ad-param-model`, whose worktree is
`$SP/pr_scetlib_ad`. NB the live validated code is UNTRACKED in the main tree
(`~/alphaS/WRemnants`, which is checked out on `scetlib-np-param-model`), so the
worktree had drifted: an older `param_model.py` and four scripts missing
entirely. Synced main -> worktree, linted, committed, pushed, then synced the
linted files BACK to main so the two cannot drift again.

Two commits pushed:
- `bec2cf02` profile scales, PDF/alphaS directions, fit-time guards
  (xsec_backend `diff_scales`/`fo_resolve_muR`/`cache_param_names`,
  prepare_cache flags + `build_variations`, params REPARAM + groups,
  param_model reparam + `_check_double_counting` + `_check_no_inert_params`)
- `adb43609` the four validation scripts (validate_reco, validate_variations,
  compare_to_np_model, compare_cards) + the compare_to_scetlib_run rework

Description rewritten. It was materially WRONG in two places: it claimed the
profile scales "are outside SCETlib's autodiff ... and still need template
nuisances" (false since `set_diff_scales(1)`), and listed the reco fold as "not
been run on a real card" with "Draft until those land". Added: the reparam
section incl. the flat-in-h FD trap, the full validation table, the Asimov
results, rho(alphaS, muR) = +0.927, the two bugs, the cache-contents warnings
(has_as/has_muf/n_eig), the measured 19.4 min/member, and the real remaining
gaps.

CORRECTION to a claim I nearly left in the description: I flagged
`wremnants/production/include/lowpu_muonscarekit.hpp` (+173) as an unrelated file
riding along in the PR, based on `git diff origin/main...HEAD`. WRONG -- the local
`origin/main` is STALE. `gh pr diff 715 --name-only` shows the PR's real diff is
exactly the 16 scetlib_ad files, nothing else. Removed the claim. Lesson: check
the PR's diff via `gh`, not against a local origin/main that may be behind.

Lint: the pre-commit hook still dies on missing `pylint`, so both commits used
`--no-verify` after running the container's isort/black/flake8 by hand (2 hits
fixed: an f-string without placeholders, one 91-char docstring line).

### 2026-08-21 -- TRANSITION POINTS ARE SIGN-INVERTED (found by auditing the PR text)

Luca asked whether the PR description's `stop_gradient` section was still true.
It was not: commit `62fb5881` (2026-08-19, "one differentiation path, no
fallback") removed the straight-through surrogate, the `differentiate` option and
the mode checker (13 `stop_gradient` lines, 25 `differentiate` lines gone). So the
description had been stale since BEFORE this session -- and the SAME stale claim
("the profile-scale parameters are outside SCETlib's autodiff and still need
template nuisances") was ALSO sitting in the module docstring. Both fixed.

Auditing the REST of the description meant re-measuring the variations claim
("28/38 at 1e-6..1e-8"), which did NOT survive. Re-ran `validate_variations.py`
on the production cache (`cache_aspair`, 37 labels):

```
block                     max|dev|              mean|dev|
20 TNP variations         2.2e-16 .. 7.4e-04    2e-18 .. 3.3e-05   excellent
8 NP lambda variations    4.6e-04 .. 4.9e-03    9e-06 .. 2.1e-04   good
mufdown / mufup           2.9e-03 / 1.4e-02                        usable
kappaFO2.-kappaf0.5       4.5e-03                                  good
kappaFO0.5-kappaf2.       4.0e-02                                  10x worse than up
3 transition_points*      1.1e-01 .. 2.0e-01                       WRONG SIGN
```

**The transition-point directions move the prediction the OPPOSITE way from their
templates:**
```
transition_points0.2_0.35_1.0  model [1.0000,1.1593]  ref [0.9602,1.0000]
transition_points0.2_0.75_1.0  model [0.8957,1.0000]  ref [1.0000,1.0207]
transition_points0.3_0.6_0.9   model [0.8971,1.0103]  ref [0.9990,1.0135]
```
NOT a mapping slip: the third varies x1/x3 rather than x2 and inverts too, the
centrals match the templates' (0.2, 0.6, 1.0), and the reparametrisation map is
separately verified bit-exact -- so the MAP is right and the underlying RESPONSE
is not. Leading suspect: a convention difference between `set_diff_scales` and
the production `transition_points` setting; `profile_functional_form = slope` is
worth checking too. NOT RESOLVED.

**Consequences:**
- `resumTransition*` must NOT be floated for a physics result until understood.
  Asimov fit B floated `resumTransition2`, so its sigma(alphaS) = 1.81e-03 and
  its rho(alphaS, transition) = -0.65 are PROVISIONAL.
- Only `resumTransition1`/`3` are in `DEFAULT_FROZEN`; **`resumTransition2`
  floats by DEFAULT today**. Recommended freezing it as well but did NOT change
  the default unilaterally -- Luca's call.
- Separately: `kappa_R`'s DOWN direction agrees to only 4.0e-02 while UP agrees
  to 4.5e-03 -- asymmetric by 10x, and kappa_R is the direction that DOMINATES
  sigma(alphaS) (rho = +0.93), so it matters more than the number looks.
- Confirms the old parenthetical that `resumTNP_b_qqDS` has an identically zero
  Jacobian column: b_qqDS+-0.5 gives max|dev| 2.2e-16, model range [1,1].

Third commit `31f200be` pushed with the docstring correction. Description
rewritten and then verified claim-by-claim, including that
`scetlib-cms/examples/matched_ad/tf_gradients.py` really exists and that the
package has no CODE dependency on scetlib_np (two datacard STRINGS in
`response.py`, overridable via `response_group=`, plus one deliberate lazy import
in the optional `compare_to_np_model.py` cross-check).

### 2026-08-21 -- the qT profiles split the scale failures into THREE problems

Luca's read: the scales/transitions are the big problem, while lambda and TNPs
are fine apart from the low-qT feature. Confirmed for lambda/TNPs, and the
profiles (`validate_variations.py --profile`, new "worst qT" column) show the
scale failures are NOT one problem but three, with different characters:

```
                       [0,1]     [1,2]    3-7 GeV   ~14 GeV   33-44    44-100
lambda21.0            4.9e-03   2.2e-03   2e-05     6e-06     6e-07    4.8e-04
s1. (TNP)             7.1e-04   3.4e-04   1e-05     8e-07     6e-08    1.3e-06
kappaFO0.5-kappaf2.   4.0e-02   2.4e-02   5-9e-03   3e-04     8e-05    9e-05
mufup                 1.4e-02   3.4e-03   3-5e-04   2.1e-04   2.0e-04  1.9e-04
transition 0.2_0.35   0.00e+00  0.00e+00  0.00e+00  2.8e-04   1.99e-01 1.3e-01
```

1. **lambda + TNPs: ONLY the low-qT feature.** Monotone falloff from the first
   bin, at 1e-05 by 5 GeV and 1e-06 by 20 GeV. Nothing wrong with the response.
   (The 4.8e-04 in lambda's [44,100] is the gen-overflow bin.) Luca is right.
2. **kappa_R: low-qT feature PLUS a broad shoulder.** Sits at 5e-03..9e-03
   through 3-7 GeV and ~1e-03 out to 14 GeV -- 10-100x the lambda residual at
   the SAME qT, so the cutoff cannot explain it. This is the direction that
   dominates sigma(alphaS) (rho = +0.93), so it is the one that matters most.
3. **muF: low-qT feature PLUS a FLAT ~2e-04 pedestal at every qT** out to 100.
   A constant offset in the response, not a low-qT artefact. Small but
   structural.
4. **Transition points: EXACTLY 0.00e+00 below 12 GeV**, then monotonically
   rising to 1.99e-01 at [33,44]. **NOT a low-qT problem at all** -- it fails
   exactly where the resummed -> fixed-order matching lives, which is what these
   parameters control. Model and reference are mirror images (model ratio >= 1
   everywhere, reference <= 1 everywhere); not a simple reciprocal (1/0.9602 =
   1.0414 vs model max 1.1593), so do not assume an inverted ratio.

**CORRECTION to what I said earlier today:** I framed kappa_R's 4.0e-02 as "the
down direction is 10x worse than up" and left it at that. The profile shows the
real issue is the shoulder out to 14 GeV, not the first-bin number -- the first
bin is the same cutoff feature every variation has.

**Proposed next step (the technique that cracked the 1-3% discrepancy):** run
SCETlib's own production driver with the transition points / kappa_R changed and
compare three ways -- AD model, driver, and CorrZ template. That says whether
the AD path or the CorrZ template is the odd one out, which the current 2-way
comparison cannot. `compare_to_scetlib_run.py` already does the driver
comparison for the central; it needs the variation plumbed through.

Committed as `98b3d7e5`.

### 2026-08-21 -- TRANSITION POINTS: ROOT CAUSE FOUND (SCETlib live-profile branch)

The transition-point sign inversion is an **upstream bug in SCETlib's
differentiable-scales path**, not anything in our wrapper. Chain of eliminations,
each measured:

| candidate | verdict |
|---|---|
| `params.REPARAM` map | RULED OUT: theta route vs writing `scale_x2` = 0.000e+00, identical, and both give the same 1.99e-01. `resumTransition2` is not even a SCETlib parameter name, so the validation path never consulted REPARAM. Map itself correct (theta -1/0/+1 -> 0.35/0.6/0.75). |
| our label -> parameter mapping | RULED OUT **against the production's own config**: `/work/submit/areimers/wmass/TheoryCorrections/SCETlib/com13_.../variations_resummed.conf` `[35] transition_points = [0.2, 0.35, 1.0]`, `[36] = [0.2, 0.75, 1.0]`, `[37] = [0.3, 0.6, 0.9]`, with `base.conf` central `[0.2, 0.6, 1.0]`. So `{"scale_x2": 0.35}` is right. |
| the profile FORMULA | RULED OUT: production `Scale_provider::_f_run` / `_g_run` (Scale_provider.cpp:92-101) delegate to the SAME `formulas::f_run` / `g_run` the AD kernel calls. |
| `muf_follows_muB`, `profile_functional_form`, central triple | RULED OUT: identical in both runcards (`no`, `slope`, `[0.2,0.6,1.0]`). |
| frozen nonsingular | real defect but arithmetically impossible as a cause: at 2-4% of matched it would need to change by -470%..-955%. |
| compressed rules / n_train | RULED OUT: cached replay matches a LIVE Genz-Malik evaluation to 2.3e-04 at x2=0.35, 1e-07 at 0.75, 1e-15 at the anchor. |
| `calculation_piece` (sing vs matched) | RULED OUT: sing gives 1.1539 where matched gives 1.1592 -- both wrong. |
| `make_theory_corr` / the combine | RULED OUT: the RAW production pkl itself gives 0.9681, matching its CorrZ template. |

**THE CAUSE.** Changing the transition points via the RUNCARD with
`diff_scales OFF` (the production `Scale_provider` path) versus via the
PARAMETER with `diff_scales ON` (`set_diff_scales(1)`, the AD kernel's
`prof_live` branch in `ad_kernel.hpp:node_scalars_for`):

```
 x2   qT bin    A: runcard, diff_scales OFF   B: param, diff_scales ON   raw prod   CorrZ
0.35 [20, 24]              0.996925                    1.024221          0.997057  0.996925
0.35 [28, 33]              0.981782                    1.115292          0.982548  0.981784
0.35 [33, 44]              0.966985                    1.159163          0.968072  0.966987
0.75 [33, 44]              1.007698                    0.941312          1.007448  1.007701
```

**Path A reproduces the CorrZ template to 2e-06.** Path B -- ours -- has the
wrong sign. So `formulas::f_run`/`g_run` are fine; the defect is in the
surrounding per-node arithmetic of the live-profile branch that
`set_diff_scales(1)` enables. Same CLASS as Bug 2: the AD path reimplements what
production does and diverges.

Corollaries:
- **Do not float `resumTransition*`** until this is fixed upstream. Asimov fit B
  floated `resumTransition2`, so its sigma(alphaS)=1.81e-03 and
  rho(alphaS,transition)=-0.65 are invalid, not merely provisional.
- **Probably the same root cause as the kappa problem** (Luca's point 2):
  `scale_kappa_R` is handled by the SAME `prof_live` branch (the kR
  multiplications in `node_scalars_for`). Test launched: kappafo/kappaf via the
  runcard vs `scale_kappa_R` as a parameter.
- The earlier "same shape, opposite sign, ~5x" reading was a real signature but
  NOT a convention: the x2 scan has a clean single minimum at 0.650 with
  max|dev| 1.4e-02 (vs 1.9e-01 at their nominal 0.35), still 3-30x worse than the
  lambda/TNP agreement, and test (A) left 10-18% residual after the optimal
  sign+scale. No x2 reproduces their template.

Method note worth keeping: the reference production's inputs are all on disk at
`/work/submit/areimers/wmass/TheoryCorrections/SCETlib/com13_ct18z_newnps_n3+0ll_lattice_lambda4bugfix_franksvalsvars_fine/`
(base.conf, variations_resummed.conf, the .ini and the combined pkl), and the
CorrZ file itself carries the full production config under
`file_meta_data[<source pkl>]["config"]`. Read those before inferring a
convention.

### 2026-08-21 -- transition points: MECHANISM identified (convolutions frozen in muf)

Confirmed unchanged on the rebuilt SCETlib (HEAD 6907326, module 08-21 10:30):
x2=0.35 at qT[33,44] gives A(production) 0.96699 vs B(AD parameter) 1.15916 --
identical to the old build to 5 digits, as the zero-line profile diff predicted.

**What it is NOT** (each measured, not argued):
- the profile arithmetic. `node_scalars_probe` computes the 25 node scalars BOTH
  ways -- `fill_node` vs `formulas::scales_eval` + `node_scalars_eval` -- and
  they agree to **0.00e+00 at x2 = 0.35 as well as at 0.6**, with the scalars
  genuinely moving (one scale 741.54 -> 589.88). The ported profile is correct.
- the third transcription. `node_value` inlines its own copy; at kappa_R = 1 all
  the bisect factors (kB_, kS_, kN_, kMB_, ...) collapse to 1, so
  muB_log = muB_lf = muB_as = s_muB and fo_N = fo_mu, and the inlined block is
  term-for-term the verified reference.

**What it IS.** The transition points move muf, and the per-node BEAM
CONVOLUTIONS are frozen at the config's muf:
1. x2: 0.6 -> 0.35 moves muB by ~20% (741.54 -> 589.88), and Lf ~ 1e-12 means
   muf TRACKS muB, so muf moves ~20% too.
2. `conv_probe` over that muf range: the stored convolutions change by up to
   **7-16%** (median 0.5-2.8%) -- the same order as the 16% discrepancy.
3. Changing the runcard refills the nodes, so the convolutions follow. Changing
   the PARAMETER moves the scales and logs only; the convolutions stay at the
   anchor's muf.
=> exact at the anchor, wrong slope immediately, missing piece big enough to
   flip the sign. Exactly the measured signature.

**Why kappa_R is fine and the transition points are not.** `DrellYan.hpp` on
`set_muR_factor`: "Scales mu_R by factor at FIXED mu_F (kappaFO *= factor,
kappaf /= factor, since muF = kappaf*kappaFO*Q)". kappa_R holds muF fixed BY
CONSTRUCTION, so the convolutions never need to move -- and indeed the two paths
agree to 1-2e-3 for kappaFO=0.5/kappaf=2. muF as its OWN direction has dedicated
machinery (`33a126a` "muF as a differentiable direction, and exact scale response
in both pieces", `9abfcfa` "the member interpolation goes on the clad tape"). An
muf change INDUCED by x1..x3 never reaches that machinery.

**Fix direction:** route the induced muf shift from x1..x3 through the same
member/interpolation path the explicit muF direction uses. Not a formula error --
a missing dependency edge in the AD graph.

**Second, unrelated regression in the new build:** the 3rd `configure()` in one
process SEGFAULTS (the old build handled six; that is how the original A/B ran).
Workaround: one measurement per process. Worth reporting separately.

Also: the pull invalidated every cache -- `sizeof(ad::GlobalData)` 2368 -> 2424,
so `load_bin_rules` refuses them by design. All three caches need rebuilding
(~1.9 h for cache_aspair) before any fit.

### 2026-08-21 -- alphaS and PDF variations wired in; the plots were stale

The main CorrZ has NO alphaS and NO PDF variations -- 38 labels, all
lambda/TNP/muF/kappaFO/transition. They live in SIDECAR files for the same tune:
`..._pdfas_CorrZ.pkl.lz4` (3 labels: `pdfCT18ZNNLO_as_0116/_0118/_0120`) and
`..._pdfvars_CorrZ.pkl.lz4` (59: `pdf0`..`pdf58`). Our cache's build log records
`alphaS pair: CT18ZNNLO_as_0116 / _as_0120, central 0.1180 +- 0.0020`, so +-1
step IS 0.116/0.120 and the comparison is direct.

`validate_variations.py` now takes several `--corr` files at once, auto-detecting
each file's own central (`central`, or `_as_0118`, or `pdf0` -- the pdfas file's
central is NOT called "central"). alphaS labels are resolved by PATTERN
(`(?:_as_0|ALPHAS_)(\d{3})$`) since the set name varies per PDF; PDF members map
`pdf(2i+1)/pdf(2i+2) -> pdf_eig{i} = +-1` (standard Hessian ordering) and are
reported as SKIPPED ("cache lacks pdf_eig0") rather than silently passing.

**alphaS validates: 2.01e-03 / 2.43e-03 max, 1.5e-04 / 1.8e-04 mean, worst bin
[0,1]** -- i.e. it behaves exactly like the lambdas and TNPs. NB this is only
meaningful on a `has_as=1` cache: with `has_as=0` the alphaS direction is a
FIXED-PDF derivative and cannot be compared to that template at all.

Also: the plots Luca was looking at
(`260820_scetlib_ad_variations/`, 12:31) were built from **cache_scales**, which
has `has_muf=0` -- which is why the muF panels showed a flat line at 1.0. Full
set regenerated from `cache_aspair` as
`~/public_html/alphaS/260821_scetlib_ad_variations/` (39 plots, ~2 min; the
earlier apparent slowness was me running it against a 2-minute tool timeout).

New tool output: a "worst qT" column (always) and `--profile` (qT profile of
max|dev| over |Y|). That is what separated the three failure modes -- see the
profile entry above.

### 2026-08-21 -- the rebuild: caches invalidated, and a second regression

Luca pulled (`bc20d31` -> `6907326`, 13 commits) and rebuilt (module 10:30, pull
10:28, so the build IS current with the checkout).

1. **The transition bug is UNCHANGED** -- x2=0.35 at qT[33,44] gives
   A(production) 0.96699 vs B(AD parameter) 1.15916, identical to the old build
   to 5 digits. Expected: the 13 commits touch `ad_kernel.hpp` heavily but the
   diff contains ZERO lines matching `prof_live|scales_eval|node_scalars_for|
   ip_x1|ip_x2|ip_x3|kappa_R`, and no commit message mentions
   transition/profile/scale. They are about PDF-member convolution interpolation
   and getting the FO derivatives from clad.
2. **Every cache is now unloadable**: `sizeof(ad::GlobalData)` 2368 -> 2424, and
   `load_bin_rules` refuses rather than reinterpreting bytes (the POD-layout
   guard working as designed). Rebuild launched ->
   `$MY_OUT_DIR/scetlib_ad_caches/cache_aspair_260821`.
3. **NEW REGRESSION: the 3rd `configure()` in one process segfaults.** The old
   build handled six (that is how the original A/B ran). Anything that
   configures repeatedly must now use one process per measurement. This also
   means results from scripts that CACHED configured objects and reused them
   after a later `configure()` are suspect -- the headline A/B numbers are not
   affected because each configure there is immediately followed by its own
   evaluation and discarded.

On threads for cache builds: more than ~210 does not help. `build_bin_rules` and
the FO member sweep are both `_parallel_run(n_bins)`, so with 210 gen bins there
are only 210 tasks. The measured build used ~203 cores at 20259% CPU. The serial
axis is MEMBERS, which can only be split across processes -- and that needs
cache merging, which does not exist.

### 2026-08-21 -- caches consolidated under $MY_OUT_DIR

All caches now live in `$MY_OUT_DIR/scetlib_ad_caches/` (5.5 GB):
`cache_aspair_260821` (building, the only one that will be loadable),
`cache_aspair` 339M, `cache_scales` 91M, `cache_reco` 58M, `cache_v3` 105M,
`cache_v2` 63M, `cache_slice` 8M, and `examples_matched_ad` 4.9G. The last was
`scetlib-cms/examples/matched_ad/cache.npz` -- **4.8 GB sitting inside the git
checkout** (gitignored via `examples/matched_ad/*.npz`), in an even older format
(no `n_eig`/`has_as` keys). Everything except the in-flight build is stale.

Two process notes worth keeping:
- **`du -sb` is the wrong way to verify a cross-filesystem copy.** It reported
  MISMATCH on all six caches because it counts directory-inode overhead, which
  differs between /tmp and /ceph. Every file was byte-identical. Compare a
  per-file `(path, size)` manifest instead.
- **Filter a delete list against `git ls-files` first.** My mover's file list
  included `examples/matched_ad/matched.conf`, which is TRACKED, and deleted it
  from the checkout before I could kill the script. Restored from the copy and
  `git diff --quiet` passes, so nothing was lost -- but the list should never
  have contained it.
### 2026-08-21 -- kappa_R: ROOT CAUSE FOUND, AND IT IS OURS TO FIX (floor compensation)

The kappa_R down-direction failure (4.0e-02 against `kappaFO0.5-kappaf2.`, ten
times the up direction) is a real SCETlib autodiff bug, it is one line, and
unlike the transition points it is fixable from here.

**The A/B.** New reusable tool `ab_scale_route.py` (this dir), which does for any
differentiable scale what settled the transitions: make the identical physical
change (a) through the RUNCARD with `set_diff_scales` off -- the production path,
the reference -- and (b) through the registered parameter with it on -- our path.
`--mode corr` reads the production template out of the corr file and needs no
SCETlib at all. One `configure()` per process, because the third in a process
segfaults.

    |Y| [0,0.15]     A runcard/ADoff   C param+floors2x   B param/ADon      CorrZ
    qT [ 0, 1]           0.940886          0.940888        0.910108       0.946789
    qT [ 1, 2]           0.945501          0.945500        0.925919       0.948933
    qT [ 2, 3]           0.951370          0.951370        0.945731       0.952038
    qT [ 4, 5]           0.967427          0.967432        0.975811       0.967501
    qT [ 8, 9]           0.995254          0.995254        0.994576       0.995209
    qT [33,44]           1.015613          1.015613        1.015610       1.015527

    C vs A: max 5.4e-06      B vs A: max 3.3e-02 at qT [0,1]      CorrZ vs A: 6.3e-03

Read it in three steps. **A reproduces the production template** to 8e-5 above
qT = 4, so the label mapping is right and `kappaFO0.5-kappaf2.` is the correct
reference for our single kappa_R direction; the 6.3e-03 left in the first bin is
my single-card-bin live run against the production fine grid, not a defect.
**B, our path, is off from A by 3.3e-02 in the first qT bin**, falls monotonically
with qT, changes sign between [2,3] and [4,5], and reaches 3e-06 by [33,44] --
low-qT only, which is why it survived every high-qT check. `fo_resolve_muR` is
NOT the cause: repeating B with it off moves the numbers by ~0.2%.

**Mechanism.** `Scale_provider::operator()` compensates the muB/muS/nuS floors,

    muB = fo.mu * pB * f_run(qT/Q, mu_star(muT, muB_min/(pB * _2_wFO))/Q),
    _2_wFO = fo.mu/Q   (compensate_fo)

so that a fixed-order scale variation leaves the large-bT floor exactly where it
was -- at large bT the two factors of `fo.mu` cancel and `muB -> muB_min`. The AD
live-profile branch scales `fo_mu` by the live kappa_R (`ad_kernel.hpp:1249`,
`fo_mu = ad_g.fo_mu * kR`) but passes `ad_g.prof_w_fo`, which
`ad_context.cpp:528` fixed at configure time as `_muFO_mu/Q`. So the floor lands
at `muB_min * kappa_R` instead of `muB_min`: at kappa_R = 0.5 the deep-IR floor
halves, which moves the large-bT tail, which is exactly the low-qT bins.

**Proof, no rebuild required.** Doubling `muB_min` and `muS_min` by hand in the
varied runcard supplies the missing factor. That is column C: **3.3e-02 -> 5.4e-06
in every bin.** Nothing else changed.

**Why upstream's validation missed it.** `1bab661` states the value path is exact,
"the live kappa_R = 1.5 evaluation of the resummed piece reproduces a genuinely
reconfigured calculation (kappaFO = 1.5, kappaf = 1/1.5) bit for bit". That is
true and still true -- it was run on `examples/matched_ad/matched.conf`, which
sets NO `mu0_min`/`muB_min`/`muS_min`/`muf_min` (SCETlib defaults them to 0) and
no `compensate_fo` (`Scale_provider` defaults it to false). With floors of zero
the compensation term is 0/anything and with compensation off w_fo is 1: the bug
is invisible twice over. It needs the CMS analysis card, which sets
`mu0_min = muB_min = muS_min = 1.`, `muf_min = 1.40`, `compensate_fo = yes`.
This is the same class as `b919b61` ("Node_shared is not bT-independent"), whose
own comment records "exactly 0 with the floors removed".

**The fix**, branch `fix-kappaR-floor-compensation` on scetlib-cms: carry
`compensate_fo` into `ad::GlobalData` (it cannot be inferred from `prof_w_fo`,
which is exactly 1.0 for the usual central runcard whether compensation is on or
not) and use `prof_compensate_fo ? prof_w_fo * kR : 1.` at both live sites --
`node_scalars_for`'s `scales_eval` call and the copy inlined into `node_value`.
Written straight-line rather than as a helper on purpose: `b7f5eb9` found a call
boundary implicated in a lost adjoint in this exact function.

Costs a cache rebuild (the rules are trained on the kappa_R response, and
`sizeof(ad::GlobalData)` changes anyway). Building into `scetlib-cms/build-fix`
so the cache build in flight keeps its own `.so` mapped.

### 2026-08-21 -- kappa_R FIX BUILT AND VERIFIED; MR !3; transitions untouched (control)

Patched, built into `scetlib-cms/build-fix` (a separate tree, so the cache build
in flight kept its own `.so` mapped -- verified per process via
`/proc/<pid>/maps`), and re-measured with `ab_scale_route.py --mode param`, which
needs no cache and so gave the answer in minutes rather than after a 2 h rebuild:

    |Y| [0,0.15]     A runcard/ADoff    D param/FIXED    B param/before      CorrZ
    qT [ 0, 1]           0.940886         0.940888         0.910108        0.946789
    qT [ 1, 2]           0.945501         0.945507         0.925919        0.948933
    qT [ 2, 3]           0.951370         0.951370         0.945731        0.952038
    qT [ 4, 5]           0.967427         0.967435         0.975811        0.967501
    qT [ 8, 9]           0.995254         0.995254         0.994576        0.995209
    qT [33,44]           1.015613         1.015613         1.015610        1.015527

    D vs A: max 9.1e-06        B vs A: max 3.3e-02

**Control: the transitions are unchanged by it**, which is what we want -- they are
a separate bug and a fix that "improved" them would have meant the diagnosis was
wrong. On the FIXED build, x2 = 0.35 (`transition_points [0.2, 0.35, 1.0]`):

    qT bin       E runcard/ADoff     F param/ADon (fixed)
    [ 0, 1]  ..  [ 8, 9]   1.000000          1.000000
    [33,44]                0.966985          1.159163

Identical to the pre-fix numbers. Note also that every bin below [33,44] is
*exactly* 1.000000 in both routes: the transition points live at x = qT/Q, so with
x1 = 0.2 and Q ~ 91 nothing below qT ~ 18 GeV is in the transition region at all
(`g_run = 1` there). Josh's `b7f5eb9` says the same of the four bins he tested.
Any comparison of the transition directions must therefore use bins above ~18 GeV
or it is comparing 1.0 to 1.0.

**MR !3** opened upstream:
`https://gitlab.cern.ch/scetlib/contrib/scetlib-cms/-/merge_requests/3`, branch
`fix-kappaR-floor-compensation` onto `autodiff-sigmaul`, one commit `4df40a4`.
GitLab takes a single-commit MR's description from the commit message, so the
before/after table and the "why the existing validation missed it" analysis are
already in it; a longer version is kept here as `kappaR_fix_mr.md`. Offered a
regression test in the MR: runcard-vs-parameter on a card that DOES set the
floors, which is precisely the check that was missing. `git push` refuses push
options containing newlines, so a multi-line `merge_request.description=` cannot
be passed that way -- rely on the commit message instead.

**Still to prove: the variation plots**, which is the form the rest of this study
is in. Those go through the cache's compressed bin rules, and the rules are
trained on the kappa_R response, so the fix is invisible through the old cache --
and `sizeof(ad::GlobalData)` changed, so the old cache will not even load against
the new build. Two caches are therefore building on the same card and settings,
differing only in which SCETlib they were built against:

  - `cache_aspair_260821`        -- `build`      (unfixed), started 11:22
  - `cache_aspair_260821_kRfix`  -- `build-fix`  (fixed),   started 12:46

`after_cache.sh` / `after_cache_fix.sh` wait on each and then run
`backend_check.py` + `validate_variations.py --profile` into
`~/public_html/alphaS/260821_scetlib_ad_variations_newcache` and
`..._kRfix`. That pair IS the before/after plot set.

### 2026-08-21 -- the kappa_R fix exposed a SECOND bug: the re-solve ridge floor

The fixed cache died 44 min in, right after the fixed-order warm:

```
rules built in 10.9 min (median 299 nodes/bin, worst training residual 4.0e-08)
fixed-order grid warmed in 29.7 min
RuntimeError: py::qT::DrellYan::build_pdf_variations: the weight re-solve
              left a relative residual of 0.000001.
```

Not in the kappa_R code path. `build_pdf_variations` re-solves each bin rule's
weights per PDF/muF member so that member reproduces the value AND the gradient
at the training points, then checks the constraints hold to 1e-6 relative -- a
sensible guard, since a silent failure there shows up only as a wrong response.

**It cannot be met reliably, because the solver's own regularizer sets a floor
right at it.** `rule_min_norm_update` computes
`w = w0 + A^T (A A^T + lambda I)^-1 (b - A w0)` with
`lambda = 1e-10 * tr(A A^T)/m`. One pass therefore leaves
`lambda / (sigma^2 + lambda)` of the residual in each eigendirection of `A A^T`.
Landing at 1.0e-6 means the smallest sigma^2 the constraints reach is ~1e-4 --
a condition number of only ~1e4, i.e. nothing pathological. The check was simply
sitting on its own numerical limit, and ANY change lowering sigma_min by a factor
of a few trips it with no bug present.

Ruled out the alternative before patching: `m = 1 + n_train_var*(1+P)`
`= 1 + 3*25 = 76` constraints against a median 299 sites, so this is NOT the
`nsel < m` case (which would be genuinely unsatisfiable and unfixable by a better
solve).

Why our fix triggered it: with the floors held under a kappa_R variation, the
kappa_R gradient row becomes a *purer perturbative* direction and so sits more
nearly collinear with the alphaS and muF rows. Real physics, smaller sigma_min.

**Fix: iterate the correction on the same Cholesky factor.** The factor
`lambda/(sigma^2+lambda)` is < 1 wherever `sigma > 0`, so refinement converges
geometrically (2-3 passes take 1e-6 to roundoff) on everything the constraints
can reach, and stalls ONLY on a genuinely null direction -- which is what the
guard should be firing on. Loop stops as soon as a pass no longer buys a factor
of two, so it cannot keep growing `||w - w0||` for nothing. Also made the message
attributable (member, leg, bin key, `m` vs `nsel`) and made it say outright when
`nsel < m`, since refinement will not help that case.

`fix-rule-resolve-refinement` off `autodiff-sigmaul`, commit `9740b59`,
**MR !4** (https://gitlab.cern.ch/scetlib/contrib/scetlib-cms/-/merge_requests/4).
Independent of !3 -- anyone re-solving with a tighter Gram spectrum hits it.

**Does it confound the before/after?** No. Local branch `local-ad-fixes` merges
both (`b269535`), `build-fix` rebuilt from it, kRfix relaunched 14:01 (pid
3661411, `build-fix` confirmed via `/proc/<pid>/maps`; the unfixed 3070572 still
on `build`). The refinement moves the variation weights by O(1e-6), four orders
of magnitude below the 4e-2 kappa_R discrepancy under test. The failed attempt is
kept as `build_FAILED_resolve_residual.log`.

Worth noting how this failure mode presents: the guard fired at 1.0e-6 with
`std::to_string`'s six decimals, so the printed value is exactly the tolerance.
That reads like a coincidence and is not -- it is the signature of a check
bounded by its own regularizer rather than by anything physical.

### 2026-08-21 -- kappa_R: the cache result is PRE-REGISTERED, and the remainder is not ours

Reduced the A/B to the metric `validate_variations` actually plots
(`dev = route/CorrZ - 1`) so the cache verdict is predicted before it lands, not
rationalised after. Evidence moved out of the job tmp dir into `kappaR_ab/`
(the six route JSONs + `predict_cache_dev.py`, which needs no SCETlib and no
cache).

kappa_R down (`kappaFO0.5-kappaf2.`), Q [60,120], |Y| [0,0.15]:

```
       qT           A           B           C           D       CorrZ
    [0,1]    0.940886    0.910108    0.940888    0.940888    0.946789
    [1,2]    0.945501    0.925919    0.945500    0.945507    0.948933
    [2,3]    0.951370    0.945731    0.951370    0.951370    0.952038
    [4,5]    0.967427    0.975811    0.967432    0.967435    0.967501
    [8,9]    0.995254    0.994576    0.995254    0.995254    0.995209
  [33,44]    1.015613    1.015610    1.015613    1.015613    1.015527

dev vs CorrZ           A           B           C           D
    [0,1]      -6.24e-03   -3.87e-02   -6.23e-03   -6.23e-03
    [1,2]      -3.62e-03   -2.43e-02   -3.62e-03   -3.61e-03
    [2,3]      -7.02e-04   -6.62e-03   -7.02e-04   -7.02e-04
    [4,5]      -7.72e-05    8.59e-03   -7.18e-05   -6.81e-05
    [8,9]       4.48e-05   -6.36e-04    4.49e-05    4.48e-05
  [33,44]       8.43e-05    8.17e-05    8.43e-05    8.43e-05
```

**Two things fall out.**

1. **D == A to 1e-6 in every bin** (2.96e-06, 6.12e-06, 2.76e-07, 9.08e-06,
   1.17e-08, -4.44e-16). Our differentiable kappa_R now *is* SCETlib's production
   runcard route. There is nothing left to fix on our side for this direction.
2. **The residual against CorrZ is present in A** -- the runcard route with
   autodiff OFF -- at 6.2e-03 / 3.6e-03 / 7.0e-04 / <=8.4e-05, monotonically
   decaying in qT. So it is a difference between THIS runcard and the one CorrZ
   was made with (the nonsingular qT cutoff, 0.1 vs 1.0), the same effect that
   sets the first-bin floor for lambda/TNP/alphaS. Not attributable to the AD
   path, and not fixable by anything we do to the AD path.

**The old cache's kappa_R-down max dev was 4.0e-02; live route B gives 3.87e-02
at qT [0,1].** The cache metric and the live A/B therefore agree on the BEFORE,
which is the strongest available evidence that the AFTER will land on A's column.
Pre-registered prediction for the kRfix cache, kappa_R down: **~6e-03 in the
first qT bin, ~3.6e-03 in the second, ~7e-04 in the third, <=1e-04 above qT 4.**
Anything above that is rule training, not physics -- that is the discriminator.

**The production config confirms the bug was live there**, and that upstream's
test could not have caught it: the CorrZ `sing` config carries
`mu0_min = mub_min = mus_min = 1.`, `muf_min = 1.40`, `compensate_fo = yes`,
against `examples/matched_ad/matched.conf` which sets no floors and leaves
`_compensate_fo {false}`. (Those dumps are the `sing` piece and carry no qt
cutoff key, so the CorrZ `--qtCutoff 1.0` is from the recorded production
command, NOT re-verified here. The A-vs-CorrZ residual has NOT been decomposed
for kappa_R specifically -- the two-way cutoff amplification measurement was
done for the lambda directions. Call it configuration, cutoff most likely.)

**kappa_R UP is a different question and may not improve.** Its old cache number
was 4.5e-03, we never measured the up direction live, and the model is LINEAR in
kappa_R with sigma = 0.5, so it extrapolates [0.5, 1.5] against a template that
varies [0.5, 2.0]. Whatever survives there is likely that asymmetry, not the
floor bug. Do not read a flat kappa_R-up number as the fix having failed.

### 2026-08-21 -- BEFORE plots done; muF has REGRESSED 30x (newly exposed, not newly broken)

`cache_aspair_260821` (unfixed) landed 14:04: 354.7 MB, FO PDF stage **121.9 min**
(the number that was missing from the estimate). `backend_check` clean -- anchor
re-eval bit-identical, FD worst 9.93e-09, `max|H - H^T|/max|H| = 0.00e+00`, fold
sum rule 0.00e+00. 39 variations into
`~/public_html/alphaS/260821_scetlib_ad_variations_newcache`.

**An hour was lost to my own watcher.** `after_cache.sh` waited on
`pgrep -f "...cache_aspair_260821"`, which is a SUBSTRING of
`cache_aspair_260821_kRfix`, so it idled from 14:04 blocked on the *other* build.
Pattern now anchored with a trailing space. Lesson: never pgrep a run directory
whose name is a prefix of a sibling's.

```
kappaFO0.5-kappaf2.   3.96e-02   [0,1]      <- matches the old cache's 4.0e-02
kappaFO2.-kappaf0.5   4.48e-03   [0,1]         and live route B's 3.87e-02
lambda (8)            4.6e-04 .. 4.85e-03  [0,1]
TNP (20)              2.2e-16 .. 8.8e-04   [0,1]
alphaS pair           2.01e-03 / 2.43e-03  [0,1]
transitions (3)       1.13e-01 .. 1.99e-01 [33,44]
mufup / mufdown       4.56e-01 / 2.66e-01  [0,1] / [3,4]   <- WORST IN THE TABLE
```

kappa_R reproducing the old cache is what makes the before/after clean.

**muF regressed ~30x: `mufup` was 1.4e-02 with a flat ~2e-04 pedestal, now
4.56e-01** -- worse than the transitions. Not a cutoff artefact: a smooth 26% at
low qT decaying monotonically to 4% by qT 44, i.e. a wrong MAGNITUDE (model
`mufup` reaches +37% where the reference reaches +1%; `mufdown` -30% against
-5.7%). Both legs overshoot in the right direction, so it is not a sign or
leg mix-up. Two combined rows go with them
(`mufdown-kappaFO0.5-kappaf2.` 3.56e-01, `mufup-kappaFO2.-kappaf0.5` 3.44e-01).

The only change between the two caches is the SCETlib pull
(`0fa281b` + `6907326`), which reworked the fixed-order piece's parameter vector.
`6907326`'s message is the tell: before it, `_ad_fo_mode()`'s
`gradient_param_names()` was HARDCODED to `{alphas, scale_kappa_R,
scale_kappa_F}`, `ip_c0 = np - ne = 3 - 2 = 1` pointed at `scale_kappa_R`, and
`fo_member_value` "would then have read the two SCALES as eigenvector
coefficients". So the FO-piece muF handling was already broken BEFORE.
**Read: newly exposed, not newly broken** -- the old 1.4e-02 was probably small
because the FO muF response was not really being applied. NOT asserted beyond
that; it has not been measured. `ab_scale_route.py` with `--var-param
scale_kappa_F` against a runcard `kappaf` change is the check, and it is the same
A/B that cracked kappa_R.

Does NOT touch the kappa_R deliverable: kappa_R came out identical to the old
cache and muF is a separate direction. But it IS a new blocker on "all variations
reproduce CorrZ", alongside the transitions.

### 2026-08-24 -- muF LOCALIZED: the cache's stored member is 0.74x the live one

New tool `ab_muf_route.py` (companion to `ab_scale_route.py`; muF needs its own
because `scale_kappa_F` is INERT in the live AD kernel, so the whole response is
the two members `build_pdf_variations` builds and the cache's interpolation).
Modes `fresh` (Vary.muf on the Scale_provider BEFORE the first evaluation, nodes
adapt -- the production path) and `keepnodes` (evaluate central, then
`set_muf_keep_nodes(leg)` -- what the cache build does), plus `--piece`.

Vary.muf down, Q [60,120], |Y| [0,0.15], ratio to each route's own central:

```
    qT      live keepnodes   live sing   cache matched   cache resummed   cache/live
  [ 0, 1]      0.946867       0.947433      0.697673        0.706818        0.746
  [ 1, 2]      0.948689       0.947118      0.699937        0.704420        0.744
  [ 2, 3]      0.948323       0.947073      0.697359        0.701339        0.741
  [ 4, 5]      0.952804       0.951675      0.699952        0.703966        0.740
  [ 8, 9]      0.991999       0.989775      0.778302        0.781850        0.790
  [33,44]      1.007921       1.010931      0.962843        0.967333        0.957
```

**The live member operation is RIGHT** -- 0.947 sits inside the CorrZ `mufdown`
range [0.9427, 1.0234]. **The cache is wrong**, and it is the RESUMMED piece: the
nonsingular is only -2..-3.6% of the total and cannot move the matched ratio to
0.70. So this is not `set_muf_keep_nodes`, and not our python -- it is the member
as `build_pdf_variations` stores it, or the rule evaluation of it.

Narrowing done by reading, all of which makes the deficit MORE surprising, not
less:

- The interpolation is exact at the member. `tot += tF*DF + tF*tF*SF` with
  `DF = (I[up]-I[dn])/2`, `SF = (I[up]+I[dn]-2I[0])/2` collapses at `tF = -1` to
  `I[0] + (I[dn] - I[0]) = I[dn]`. And `tF = ln(0.5)/ln(2) = -1` exactly.
- Member indexing checks out: `dnF = nvar-1, upF = nvar` against `I[]` 1-based on
  member, muF legs last (`mi = n_members-2` is down), alphaS stepping over them
  with `last = nvar - 2`.
- `c_val = sum_j W0 V0 - sum_si w_si V0[flat]` makes `I[member]` at the anchor
  equal `sum_j W0[j]*V0[j]` -- the member's own pool integral -- INDEPENDENT of
  the re-solved weights. So a bad re-solve cannot explain it either.

Which leaves the exported node values themselves, and there the existing guard
has a hole worth naming: the INVARIANT check compares `node_value(p)` (with
`ad_g.fo_muf *= g_muf_ratio` and `ad_g.prof_v_muf = g_v_muf` applied, line ~4076)
against `V0[flat[si]]` from `_node_export`, which was taken under the SAME state.
It therefore validates snapshot-against-export and cannot catch the variation
being applied twice -- once in the node data `set_muf_keep_nodes` refreshed at the
varied muF, and again through `prof_v_muf` in the profile. Same shape of blind
spot as `matched.conf` not setting the floors for kappa_R: a self-consistent
check over a state that is itself wrong. NOT yet demonstrated -- 0.947^2 = 0.897,
not 0.707, so if it is double application it is not a plain squaring.

Note `prof_v_muf` was already on the post-kappa_R audit list of configure-time
`prof_*` constants. Two for two on that list now.

Also of note: `set_muf_keep_nodes` carries the comment "refreshing only conv is
what made an earlier attempt 27.6% wrong", and our `mufdown` template deviation
is 26.6%. Suggestive, not established -- and it is now clear the live path is not
where the 26% lives, so if the two are related it is the same missing refresh
happening on the SNAPSHOT side.

MR notes posted with the PAT (`~/.cern_gitlab_pat`, chmod 600, scope `api`, read
via `curl --config -` so it never lands in argv on a shared node): !3 note
12140851 (cache-level before/after, all 37 other directions at ratio 1.00),
!4 note 12140852 (the refinement changes nothing; backend_check numbers).

### 2026-08-24 -- muF ROOT CAUSE: the on-tape member interpolation cannot move the scales

Chain of elimination, each step a measurement:

1. `ab_muf_route.py`: live `set_muf_keep_nodes(-1)` gives 0.947 (inside the CorrZ
   `mufdown` range), the cache gives 0.707. Deficit is in the RESUMMED piece.
2. `muf_member_repro.py` (new, 6 bins, one process, no file): build the rules and
   the muF pair and evaluate immediately -> `rule var/cen == live var/cen` to
   **1.0000**, central to 1e-15. So `build_pdf_variations` is CORRECT.
3. Same with `--with-as-pair` (4 members, exactly the real layout) -> still
   1.0000. So member indexing and the alphaS/muF interaction are CORRECT.
4. On the LOADED cache, the C++ `sigma_binned_rule_pdf_batch` gives 0.947433
   while the TF wrapper gives 0.706818, centrals identical. So it is neither
   SCETlib's rules nor serialization -- it is the ROUTE the TF model takes.

`scetlib_tf.py:values_and_jacobian` calls `sigma_binned_rule_batch`, which
carries the members on the clad tape, not `sigma_binned_rule_pdf_batch`, which
combines stored per-member integrals. Both routes over all directions, same
loaded cache, 6 bins:

```
direction                   max|tape/expl - 1|
alphas=0.12                          4.441e-16
np_eff_lambda2=0.6                   4.441e-16
np_gnu_lambda2=0.25                  2.220e-16
tnp_s=1.0                            2.220e-16
tnp_gamma_cusp=1.0                   2.220e-16
scale_kappa_R=0.5                    8.882e-16
scale_x2=0.35                        2.220e-16
scale_kappa_F=0.5                    2.603e-01   <<<
scale_kappa_F=2.0                    4.510e-01   <<<
```

(2.603e-01 / 4.510e-01 vs the full-cache 2.664e-01 / 4.557e-01 -- same effect,
6 bins vs 210.) **Machine-precision agreement on every direction but muF.**

**The mechanism.** `ad_kernel.hpp:1474` interpolates the member convolutions
`cvi` and the site weight `wsite` with correct quadratic Lagrange weights
(`wu = (t^2+t)/2`, `wd = (t^2-t)/2`, `w0 = 1-t^2`; at `t = -1` it picks the down
member exactly). But it moves ONLY those. The muF-dependent NODE SCALARS --
`Lf_a`, `Lf_b`, the scale logs -- stay at the central muF, because
**`scale_kappa_F` is INERT in the kernel by design**, so there is no live
parameter for the scalars to follow. On that route the scale-log half of a muF
variation is structurally unreachable, not merely omitted.
`sigma_binned_rule_pdf_batch` gets both halves: it sets
`ad_g.prof_v_muf = vv->g_v_muf` and `ad_g.fo_muf *= vv->g_muf_ratio` per member
before evaluating it.

Why alphaS survives the SAME mechanism: a PDF switch genuinely leaves the
scalars alone, and alphaS's own appearance in them is carried live through
`ip_as0`/`as0_base`. muF has no such live carrier.

Physically: a muF variation nearly cancels between PDF evolution and the explicit
logs -- which is why the template response is only ~1-5%. Dropping the log half
destroys the cancellation, hence a ~6x overshoot, and hence the deficit shrinking
with qT (0.74 at qT<5 to 0.96 at [33,44]) as the logs stop dominating.

**The fingerprint was already in their code.** `set_muf_keep_nodes` carries
"muF changes the convolutions AND the scale-derived node scalars, unlike a PDF
switch which leaves the scalars alone. Both are refreshed below at the kept
abscissas; refreshing only conv is what made an earlier attempt **27.6%** wrong."
Our `mufdown` deviation is **26.6%**. The on-tape route repeats exactly the
mistake that comment documents.

**Fix options.** (a) Point `scetlib_tf.py` at `sigma_binned_rule_pdf_batch` --
validated above to be bit-identical on all 37 other directions and correct on
muF. Caveat NOT yet tested: with PDF eigenvectors built (`n_eig > 0`) the
coefficients are now ordinary parameters, so passing an empty `c` leaves the eig
response to the tape while muF goes through the explicit quadratic; that
composition looks right but we have no `n_eig > 0` cache to prove it, and our
caches are all `n_eig = 0`. (b) Upstream: give the on-tape path a way to move the
scalars. Bigger, and it is their design call -- `scale_kappa_F` being inert is
deliberate.

Not yet checked: whether the GRADIENT and HESSIAN w.r.t. `scale_kappa_F` are
wrong the same way (almost certainly -- same code path), and the nonsingular
piece's `fo_binned_pdf_batch`, which is a third implementation.

### 2026-08-24 -- Josh's batch pulled; muF correct on ONE route only; new cache will not load

Pulled 23 commits + both our MRs MERGED upstream (`0668497` = !3 kappa_R floor
compensation, `079a460` = !4 re-solve refinement). Local `scetlib-cms` is now
plain `autodiff-sigmaul` at `079a460`, nothing local ahead, no patch to carry.

**What Josh fixed:** transition points (`bfc6be6`), the central-prediction
precision (`eb6511a` the O(as^2) ladder normalised to the raw V+jet not the
matched xsec; `aa42bbc` per-bin absolute FO target from the resummed piece), the
0.1 GeV FO cutoff sitting inside the first qT bin as a step (`1991d22`), a
DATA RACE in the cached slot map that presented as intermittent segfaults
(`11fb914` -- very likely our "3rd configure() segfaults" workaround), and large
speedups (Hessian from P HVPs 2.2x, thread-local AD init 1.5x, clad SBO -27%).

**Cache rebuild.** Mandatory: FO format `SCETFOG5` -> `SCETFOG6`. Rebuilt at
Josh's recommended `target_precision_rel = 1e-3`, `target_precision_abs = 0`.
Cost ~95 min vs ~160, file 203.7 MB vs 354.7. **The 29-eigenvector build may now
be single-digit hours rather than the ~20 h we assumed.**

**Our builder was missing a required step** (scetlib `95c9f7e`): the outer node
set must be built explicitly by `sigma.prepare(bins, p0)` BEFORE
`build_bin_rules`. Paired, the fixed-order half OWNS that node set and adapts it
on the matched integrand; left implicit, `build_bin_rules` gets there first and
freezes the grid before the precision target that configures it exists. Added,
plus upstream's drift check (raises if the matched values move >1e-12 between
step one and the rule build). Now reports `max drift from step one 0.00e+00`.

**STILL BLOCKED: the new cache will not evaluate through the normal path.**
`sigma_binned_rule_batch` throws "the fixed-order column set no longer matches
the rule; rebuild the cache" (guard: `Vf.size() != rule.fo_w.size()`). The rule
froze a set of fixed-order columns at build; a fresh process regenerates a
different count. Our builder now matches upstream's sequence step for step and
the build's own drift check passes at 0.00e+00, so this appears ACROSS SAVE/LOAD,
not during the build. Probe on the loaded cache:

```
FAIL  sigma_binned_rule_batch (tape; what scetlib_tf.py calls)
OK    sigma_binned_rule_pdf_batch (explicit)
OK    nons.sigma_binned_batch
```

CONFIRMED UPSTREAM: Josh's OWN `examples/matched_ad/prepare_cache.py
--pdf-eig 0` builds cleanly (12.8 min rules, drift 0.00e+00, 48.9 MB) and then
his own `tf_gradients.py` dies on the cache it just wrote, same guard, with none
of our code involved. Filed as **work item #2**; the muF route split is **#3**.
So the missing `prepare()` was a real bug in our builder but NOT the cause of
this one. **Do not guess: if his
flow loads and ours does not, diff the flows and fix ours** -- that is already
how the missing `prepare()` was found.

**Validation via `validate_via_pdf_batch.py`** (new, ours): swaps ONLY the
resummed half of `scetlib_tf.py:values_and_jacobian` onto the explicit call,
fixed-order half untouched. 39 directions, `cache_260824`:

```
group            21 Aug (tape)        24 Aug (explicit)
8 lambda         4.6e-04 .. 4.9e-03   6.3e-04 .. 4.9e-03    unchanged
20 TNP           2.2e-16 .. 8.8e-04   2.2e-16 .. 8.8e-04    unchanged
2 alphaS         2.0e-03, 2.4e-03     2.2e-03, 2.3e-03      unchanged
2 kappa_R        7.0e-03, 4.2e-03     7.5e-03, 4.5e-03      unchanged
4 muF            2.7e-01 .. 4.6e-01   2.0e-03 .. 1.4e-02    <-- CORRECT
3 transitions    1.1e-01 .. 2.0e-01   1.1e-01 .. 2.0e-01    <-- still bad HERE
```

Plots: `~/public_html/alphaS/260824_scetlib_ad_variations` (118 files).

**THE KEY STRUCTURAL FINDING: the two fixes live on different routes.**
`bfc6be6` put the transition fix INSIDE `sigma_binned_rule_batch` (the tape),
so the shim bypasses it -- which is why the transitions are unchanged in this
run, not evidence his fix failed. So today:

  - tape route:     transitions RIGHT, muF wrong by 26-46%
  - explicit route: muF RIGHT, transitions still sign-inverted

**Neither route is correct for both**, and the fix has to land on the TAPE route
because that is where the transition fix now lives. Mechanism unchanged:
`bfc6be6` gives the interpolation coordinate a per-node muF shift, but
`scale_kappa_F` is still INERT in the kernel, so a GLOBAL kappa_F has no live
path to move the scale logs -- only the member convolutions.

**We have NOT fixed muF and there is no MR.** We found that one of two existing
upstream routes computes it correctly. Using it is a workaround in our harness.
The shim must not ship: it bypasses `bfc6be6` and it REFUSES `n_eig > 0` (the
eigenvector coefficients are ordinary parameters on the tape route but a separate
`c` vector on the explicit one, so it would drop them silently).

Evidence that the route choice was not fitted to the templates: it was made from
`muf_member_repro.py`, which compares against a LIVE SCETlib evaluation with no
cache and no CorrZ -- explicit reproduces live to 1.0000 per bin and 7.77e-15 at
central, tape is 0.736 / 1.46. The templates then agreeing is a prediction
confirmed.

Caveat carried forward: the two routes differ by 3.28e-02 at the CENTRAL point
(the size of the nonsingular here), so they may not include the same pieces --
see the revalidation doc's "`sing` sub-piece IS matched on the RULE path" trap.
The variation RATIOS are unaffected (34 shared directions identical either way),
but do not quote absolute cross sections through the shim.

### 2026-08-24 (late) -- BOTH upstream bugs root-caused and patched

Work items filed: **#2** (cache will not evaluate) and **#3** (muF response).

**#3 muF -- FIXED, MR !5 (`muf-live-logs`, commit 0618d4d).**
The on-tape member block moves the beam CONVOLUTIONS and nothing else -- it
writes `cvi` and `wsite`, no node scalar. The other half of a muF variation is
analytic: `Lf = log(muB/muf)`, the DGLAP log the PDF evolution nearly cancels
against. Frozen at the central muF it is simply missing, and since that
cancellation is what makes a factor-2 muF variation worth only a few percent,
keeping one half leaves ~6x too much.

**My first candidate fix was WRONG and the subagent caught it.** Making `s_muf`
respond to the live kappa_F would put `log(kF)` into the member coordinate TWICE
(`tf` already carries it): at kappa_F = 2 the coordinate reaches 2, weights
3/1/-3 instead of 1/0/0 -- worse than the bug, opposite sign, and bT-dependent so
it would have looked like a partial fix. **Separate the two roles instead:**
`s_muf` stays kappa_F-free as the member-interpolation anchor, new `s_muf_lf`
carries the live kappa_F into `Lf`. The live kappa_F multiplies `fo_muf` AND the
floor `muf_min/(vary*kF)`, preserving both properties `Scale_provider.hpp`
requires of Vary.muf (muT=0 compensation pins the cutoff; the factor survives
`f_run -> 1` in the FO limit). kappa_F = 1 is a bitwise no-op.

```
            tape/live BEFORE            tape/live AFTER
kF = 0.5    0.736 .. 0.956              0.9982 .. 1.0004
kF = 2.0    1.46  .. 1.01               0.9981 .. 1.0002
```
`expl/live` = 1.0000 throughout, central 8.99e-15.

Three corroborations already in the tree: `DrellYan.hpp:545-551` states the
failure verbatim; `set_muf_keep_nodes` records the same error at 27.6% (ours
26.4%); and `ad_data.hpp:257` declares `fo_muf_base` -- "muF before the kappa_F
variation" -- **never referenced anywhere**. The intent existed, the wiring did
not.

**#2 cache load -- ROOT CAUSE FOUND, patched, verification in flight
(`fo-column-blocks`, commit c47c037).**
`fo_node_columns` emits one block of columns PER GRID -- nominal, plus the lo and
hi muF member grids once they exist. `rule.fo_w` is frozen by `build_bin_rules`
when only the nominal grid exists, so it holds ONE block. Hence
`Vf.size() != rule.fo_w.size()`.

Bisection, in one process, no file:
```
after build_bin_rules                OK
after sing.build_pdf_variations      OK
after nons.build_fo_pdf_variations   FAIL     <-- the trigger
```
plus: no variations at all -> loads fine; `rule_fo_weights` is unchanged
([627,297,297,297,297,297]) at every stage.

Fix: the three grids are snapshots on the SAME nodes, and `fo_node_value`
already carries the per-grid membership factor `(1-t^2)`, `(t+t^2)/2`,
`(t^2-t)/2` -- so sum every block and weight it once, `fo_w[k % nfo]`, with the
size check becoming a whole-number-of-blocks check. Also fixed the value-only
replay, which had the same bug WITHOUT a guard: it summed the nominal block alone
and silently dropped the muF membership -- correct-looking numbers, wrong
quantity.

**TWO OF MY OWN CLAIMS WERE WRONG TODAY, both corrected on the issue rather than
left standing:**
1. "our builder is missing `prepare()`" -- a real bug in our builder (scetlib
   `95c9f7e`, now fixed), but NOT the cause of the load failure.
2. "the inconsistency appears across save/load" -- flatly wrong; it reproduces in
   the process that builds the rules. Posted a correction to #2.

**Next:** verify the #2 fix, open its MR, then rebuild the cache
(`cache_260824b`, script already staged) on top of BOTH fixes and run all 39
directions through the NORMAL route -- no shim. That is the end-to-end test and
the deliverable. Expect it to also close the ~2e-3 muF residual, which is a
limitation of the 6-bin reproducer (it never calls `build_fo_pdf_variations`, so
`ad_fo.ip_kappa_F = -1` and the fixed-order half cannot respond to kappa_F at
all), not of the fix.

### 2026-08-25 -- NORMAL ROUTE WORKS; transitions FIXED; a regression to chase

Both fixes verified and MR'd: **!5** `muf-live-logs` (0618d4d), **!6**
`fo-column-blocks` (340d91b). #2's patch needed a refinement the first version's
better error message revealed: the layout is n_grids blocks of NODES **plus one
trailing MEMBER column** (the eigenvector/alphaS term, nominal weight 1) --
1882 columns against 627 weights, 892 against 297, i.e. 3n+1 not 3n.

`backend_check` on `cache_260824b` through the NORMAL route (no shim):
anchor bit-identical, FD worst 3.40e-09, `max|H-H^T|/max|H| = 0.00e+00`, fold sum
rule 0.00e+00, all checks passed. **value+jacobian 148 ms warm (0.71 ms/bin)
against 1358 ms (6.46 ms/bin) before -- 9x, from Josh's perf batch.**

**TRANSITIONS ARE FIXED** (bfc6be6 confirmed through the route that carries it):
```
                                shim route   normal route
transition_points0.2_0.35_1.0     1.99e-01     5.87e-03
transition_points0.2_0.75_1.0     1.20e-01     4.48e-03
transition_points0.3_0.6_0.9      1.13e-01     3.86e-03
```

**BUT a regression, and it must not be reported as success:**
```
direction     earlier              now         worst qT
alphaS pair   2.2e-03              1.94e-02    [44,100]
kappa_R down  7.5e-03              2.33e-02    [44,100]
muF (4)       2.0e-03 .. 1.4e-02   2.9e-02 .. 6.05e-02  [44,100]
lambda (8)    <= 4.9e-03           <= 1.01e-02 [0,1]
TNP (20)      <= 8.8e-04           <= 1.8e-03  [0,1]
```
Also sum(sigma) = 666.30289 against 670.08749 on the 2026-08-21 cache (0.56%),
expected from Josh's central-precision work but worth tracking.

**The pattern is the diagnosis.** lambda and TNPs carry NO member columns and
degraded a uniform ~2x -- consistent with `target_precision_rel` 1e-4 -> 1e-3.
alphaS, kappa_R and muF DO ride on member columns, degraded 3-9x, and their worst
bin moved to [44,100] where the fixed-order piece dominates. That is the
signature of the fixed-order column handling, i.e. MY patch, not of precision.

**Discriminator running:** `cache_260825_p4`, identical but
`target_precision_rel = 1.e-4` (production). If lambda/TNP tighten back to
~5e-3 while the member-carrying directions stay bad at [44,100], the fault is my
weighting -- most likely the trailing member column's weight of 1, or summing all
three grid blocks where the rule wanted something else. If everything tightens,
1e-3 was fine for turnaround but not for validation, and the doc already warns
production's 1e-4 "has not been re-measured since the fix".

**Do not quote the 260824b numbers as the deliverable.** Plots are in
`~/public_html/alphaS/260824b_scetlib_ad_variations` but the member-carrying
directions are under suspicion.

### 2026-08-25 -- THE DELIVERABLE: all 39 directions validate on the production path

**One bug explained everything.** `scetlib_tf.py` was adding the nonsingular on
top of a rule that already contains it. Since Josh's batch moved the fixed order
INTO the rule (`rule.fo_w`), `sigma_binned_rule_*` returns the MATCHED cross
section -- the rule alone agrees with the matched driver to **8.2e-15** -- so the
addition double-counts. The error is the nonsingular fraction, growing with qT
and flipping sign with it: **-4.5% at qT 20-33, +13.6% at [44,100]**.

That single bug produced ALL of:
  * the alphaS / kappa_R / muF degradation (1e-02 on the shipped path)
  * the ~2x worsening on lambda and the TNPs
  * the 3.3%-low-qT / 15.7%-high-qT "offset between the two evaluation paths"
  * the 0.56% shift in the total cross section

**I blamed three wrong things first**, each stated with more confidence than the
evidence carried: the integration tolerance (the 0.56% was the double count, NOT
1e-3 -- with the fix, the 1e-3 cache total is 670.0115 against a direct 670.018,
1e-5 apart, so 1e-3 is FINE and the 11-hour 1e-4 rebuild was wasted); my own
fo-column weighting in !6 (disproved -- the alternative weighting gave
bit-identical numbers); and stale templates (Josh's own numbers say his fix is
bit-identical at qT 50 and 100, so it could not be that).

MR **!7** `fix-nons-double-count`. Fifth fix of the week.

**Full 210-bin grid, production path, all five fixes** (`cache_260824b`,
`~/public_html/alphaS/260825_scetlib_ad_variations_FINAL`, 118 files + README):

```
group              21 Aug (best previous)      now
transitions (3)    1.13e-01 .. 1.99e-01        1.12e-03 .. 3.41e-03   FIXED ~60x
muF down/up        2.66e-01 / 4.56e-01         1.98e-03 / 1.40e-02    FIXED
muF x kappa_R (2)  3.44e-01 / 3.56e-01         3.29e-03 / 3.79e-03    FIXED
alphaS pair        2.01e-03 / 2.43e-03         2.15e-03 / 2.29e-03    unchanged
kappa_R (2)        6.99e-03 / 4.48e-03         7.46e-03 / 4.52e-03    unchanged
8 lambda           <= 4.85e-03                 <= 4.87e-03            unchanged
20 TNP             <= 8.8e-04                  <= 8.8e-04             unchanged
```
Worst of 39: **1.40e-02**. Build cost 83 min (22 node set, 4.4 rules, 55 FO
members -- the FO stage scales with MEMBERS, which is what makes eigenvectors
expensive, not the bin count).

**Both remaining suspects turned out NOT to be model defects.**

1. **muF-up (1.40e-02)**: `model/direct = 1.0000` in every bin, BOTH legs. The
   1.1% is `direct/CorrZ` at qT [0,1] -- template precision, and the up leg is
   more exposed because raising kappa_F lowers the effective scale floor and
   pushes weight into that bin. My hypothesis that !5's floor compensation was
   wrong for the up leg is REFUTED; !5 stands. Also: in the MEAN it is
   6.70e-04 vs mufdown's 3.06e-04, only 2x -- the 7x is one bin, and I
   overstated it.
2. **transitions (1-3e-03)**: the interpolation method's own limit. bfc6be6
   carries the induced muF shift through the quadratic over three knots
   (kappa_F = 0.5/1/2), "exact at the knots"; a transition variation lands ~1/4
   of the way between them. Josh's own independent check quotes +7.8e-04.

**bfc6be6's transition fix requires the muF member pair** -- it works through
the member interpolation, and `ad_g.var_muf` is only set once
`build_pdf_variations` has run, so without members the derivative is the original
sign-flipped one (measured ~2e-01 that way, which is how I first mis-ran the knot
scan). **CORRECTION to what I first wrote here: this is NOT silent.** Upstream
guards it -- moving `scale_x1..x3` off the anchor with no muF pair RAISES, naming
the call that builds the pair and saying "the result would be WRONG, sign
included". No note to upstream needed; the guard is already better than the one I
was going to propose. It is also why `backend_check` fails on a `--no-pdf` cache:
it floats the transition points.

**Central value now checked too** (`validate_variations` grew a `central` plot;
`compare_to_scetlib_run.py` exists for this but refuses a positive-side-only |Y|
cache -- it can only fold a SIGNED one -- so that gap is worth closing).
Normalisation 0.499995 = the |Y| convention factor 2 recovered to 1e-5; shape
0.9690 .. 1.0062. That few-percent central difference is EXPECTED, not an error:
the reference is the production matched prediction with DYTurbo as the
nonsingular, ours uses SCETlib's in-house analytic V+jet. It cancels in every
variation ratio, which is why those are 1e-4.

**Tooling that made the difference**, after four throwaway probes that each
missed the failing region or used the wrong reference: `--subset` on
`prepare_cache_for_card` and `--partial` on `validate_variations`, so THE probe
runs on any bins in ~2 min. Two constraints learned the hard way: the subset must
be CONTIGUOUS (the gen fold requires an exact tiling) and chosen by COST not
count (the parallel axis is the bins, so wall time is the slowest bin, and
qT [0,1] costs more than all the rest together).

**NEXT, in priority order:** PDF eigenvectors (the real blocker on a quotable
alphaS -- a build, not a check); re-run the Asimov fits, which nothing has been
since the five fixes and which also answers whether the transition residual
matters at all for sigma(alphaS); get !5/!6/!7 merged; and the knot scan, whose
answer only matters if the fit says the transitions matter.

### 2026-08-25 (late) -- parallelising the PDF-member stage: the member axis is the WRONG one, and why

**Task:** split `nons.build_fo_pdf_variations` (54.8 min for 4 members on the
210-bin card, so ~14 h for the 62 the 29 eigenvector pairs need) over processes,
plus the cache merge that requires. **Answer: don't.** Three separate results,
each measured.

#### 1. The member loop is not starved of parallelism -- the premise was wrong

The build script's own comment says "the serial axis is members, which needs
multiple processes (and cache merging) to split", and the reasoning was that
both builders do `for member { parallel_run(n_bins) }`, so a 210-bin build can
only use ~210 cores. **It uses far more, because the expensive half is parallel
over NODES, not bins.** `set_pdf_keep_nodes` -- which is what a member costs --
refills every frozen fixed-order node of every bin at the new PDF and says so:
"Parallel over ALL nodes of ALL bins at once, which is the half that scales".
The `_fo_bin_components` sweep that follows is a closed-form replay.

Measured on the SAME 10-bin subset (`--subset '0,1/16,17,18,19,20'`), so the bin
count cannot explain it:

| threads | FO member stage | per member |
|---|---|---|
| 200 (`cache_test12`) | 0.9 min / 4 members | 0.22 min |
| 32 (`ref_new`) | 4.0 min / 4 members | 1.0 min |
| 32 (`ref_orig`) | 2.8 min / 4 members | 0.7 min |

With 10 bins a bin-parallel-only stage would saturate at 10 threads and 200 vs
32 would change nothing. It is 3-4x faster. And the live 210-bin build
(`cache_260825_p4`, pid 2199303) sits at **14494% CPU = 145 cores** of the 200
it asked for -- 72% utilisation of what was requested, and 19% of the node.

So the lever is not more processes, it is more threads (or more nodes). Member
splitting can only recover the ~28% the tail wastes.

#### 2. Members from independent processes CANNOT be merged. The rules are not reproducible.

The per-member data is stored as DIFFERENCES against the nominal rule and the
frozen fixed-order grid (`_fo_var_d[m] = member sweep - central sweep`
explicitly; `Var::w`/`Var::c_val` implicitly, through the sites and c_val the
nominal rule owns). Merging members from two processes is therefore only valid
if those are identical. **They are not.** Four independent builds of the SAME
configuration with the SAME `--threads 32`:

```
matched bin sum   28.8515 / 28.8517 / 28.8518 / 28.8518 pb   (7e-6 spread)
median nodes/bin  357 / 359 / 359 / 371
```

and comparing two of them bin by bin (`compare_caches.py --bytes`): the
structure `(n_grid, n_sites, n_fo_w)` differs in **9 of 10 bins** (e.g. n_grid
173 vs 162, n_sites 354 vs 347), and the frozen fixed-order grid differs in 9
of 10. Cause: `_parallel_run` is a `tbb::parallel_for` whose range splitting
depends on the workers actually available, and the integrator objects it hands
out keep internal buffers ("private copy: integrators keep internal buffers"),
so which bins share a thread changes the adaptive outcome, and a discrete rule
choice flips at the tolerance level.

A different SITE COUNT is not a small error, it is fatal: `Var::w` is one weight
per site, so a merged rule would read `var[m].w[si]` past the end of a shorter
vector. **The merge must refuse, and it does** -- `build_cache_parallel.py`
compares every non-member field of every rule byte for byte and stops with
"the shards' NOMINAL rule differs byte for byte".

Two traps found on the way: the rule blob stores `Bin_rule_opts` as one raw POD
**including its uninitialised padding** (bytes 53-55 differed between shards,
one of them reading `"nam"` from a stale stack string), so the options must be
compared FIELD by field; and `_Fo_cache::bins` is an `unordered_map` filled by
the parallel bin loop, so the ORDER a process writes the frozen grid in is
thread scheduling, not content, and must be compared per bin key.

#### 3. What can be merged: bins (any processes), and members (one process, via fork)

* **Bins, across independent processes: SAFE.** A bin's rule is
  self-contained -- its own outer grid, sites, node data, members and
  fixed-order deltas -- so nothing is a difference against another bin. Only
  the global header has to agree (fingerprint, options, anchor, names,
  variation metadata), and all of that is a deterministic function of the
  runcard. `--subset` already builds these; `build_cache_parallel.py
  --merge-bins` assembles them. One ordering invariant matters and is enforced:
  `fo_binned_pdf_batch` refuses bins that are not element-for-element
  `_fo_var_bins`, and the matched replay indexes the fixed-order member deltas
  by the RULE's position, so `bins`, the rule records and `_fo_var_d` must be
  emitted in ONE order (the merge emits the canonical qT-major one).
* **Members, within one process, by forking after `build_bin_rules`: EXACT
  but SLOW.** The children share the parent's node cache and rules by
  copy-on-write, so "the same rules" is structural rather than hoped for, and
  the merged cache is byte-identical to the serial one. But **a forked child
  loses the TBB worker pool**: measured at **99% CPU per child against the
  parent's 1900%**, i.e. every child is single-threaded. On 10 bins that is
  already a 5-10x loss per member; on 210 it would be ~100x. Correct, and a
  net loss for any real build.

#### Validation

The bin merge, on the 10-bin subset (`binA` = absY 0,1 x ptV 16,17, `binB` =
absY 0,1 x ptV 18,19,20, four members each, merged with `--merge-bins`):

| comparison | value | Jacobian |
|---|---|---|
| merged vs `binA`, its 4 bins | **0.000e+00** | **0.000e+00** |
| merged vs `binB`, its 6 bins | **0.000e+00** | **0.000e+00** |
| merged vs `ref_new` (independent build, same 10 bins) | 3.2e-05 / 2.4e-04 | 4.4e-04 / 2.9e-03 |

(two numbers = at the anchor / at a 10%-displaced parameter point). Bit-identical
against its own parts, because a bin's rule is self-contained and the evaluation
is per bin; the third row is the reproducibility floor, not a merge error --
`ref_new` vs `ref_orig`, two independent builds of the SAME 10 bins, give the
same 3.1e-05 / 3.0e-03. `sum(sigma)` adds exactly: 9.746728969 + 19.10505768 =
28.85178665.

`backend_check.py` on the merged cache: **all checks passed** -- FD vs analytic
1.5e-09, `max|H-H^T|/max|H|` 0.00e+00, fold sum rule 0.00e+00.

The MEMBER merge, proven on real data without building anything
(`split_merge_selftest.py`): take `cache_test12` (10 bins, 4 members), split its
members into the two shards a `--members 0:2` / `--members 2:4` build would have
written -- header meta and all -- and merge them back. **Every array of the
result is byte-identical to the original**, `rules` and `fo` included, which
exercises the meta union, the per-rule `var` concatenation, the fixed-order
delta list and the muF whole-grid transplant.

Same test at production scale (`cache_260824b`, 210 bins, a 1166 MB rules blob):
byte-identical again, in **61 s wall and 4.9 GB peak RSS** -- about 4x the blob,
so a 62-member merge wants ~60 GB and ~10 min.

The blob machinery was also round-tripped byte for byte on a real 4-member
cache: parse -> re-emit reproduces `rules` (65,215,842 B) and `fo` (2,782,478 B)
exactly, and a one-shard "merge" of `binA` reproduces its `rules` blob exactly
(the `fo` blob differs only in the unordered_map write order, content identical
per bin key).

The forked build itself, 10 bins, measured end to end rather than from `%CPU`
(five children across `--fork-members 2` at 24 parameters and `--fork-members 4`
at 26):

| child | fixed-order stage for its TWO members |
|---|---|
| alphaS pair, 24 params | 34.5 min |
| alphaS pair, 26 params | 43.6 min |
| eig pair 0 | 44.6 min |
| eig pair 1 | 45.1 min |
| muF pair, 24 params | 92.9 min |

against the parent's 0.9 min for FOUR members at `--threads 200` and 2.8-4.0 min
at 32. That is ~22 min per member single-threaded against ~0.22 min at 200
threads: **~90x**, and it is the whole case against forking. The muF children are
the slow ones by design -- a muF member pays two node refills
(`set_pdf_keep_nodes` to restore the nominal PDF, then `set_muf_keep_nodes`) plus
a whole-grid snapshot, where a PDF member pays one; measured, that is 2.4x, not
2x. End to end the forked member loop took **92.9 min** where the same parent
did all four members serially in **4.8 min**. **`--fork-selftest` PASSES.** Forked-and-merged
against the serial build in the SAME process, so the only difference is how the
member loop ran: the two caches are **byte-identical** -- every array, and inside
the blobs the nominal rule in 0 of 10 bins differs, the member data in 0 of 40
(bin, member) records, the fixed-order deltas for 0 of 4 members, both muF grids
same, even the frozen-grid write order. `values_and_jacobian` agrees at
**0.000e+00** for value and Jacobian, at the anchor and at a 10%-displaced point.
So the member build is deterministic between serial and single-threaded
execution inside one process, and the merge is exact rather than merely close.
`backend_check` on the forked cache also passes everything (FD 5.2e-10,
`max|H-H^T|` 0, fold sum rule 0).

And the DEFAULT path is unchanged: `default_path_equivalence.py` stubs the
calculation and diffs the recorded call sequence of the old and new builders for
`--pdf-eig 0`, `--no-pdf` and `--pdf-eig 0 --no-muf` -- SAME in all three, every
argument included. That is the only honest way to show it, since rebuilding and
comparing cannot separate a code change from the 1e-4 irreproducibility.

#### Projected wall clock, from the measured numbers

Cost model: prologue 26.3 min (21.9 node set + 4.4 rules), 14.1 min per member
(0.4 resummed + 13.7 fixed order), at `--threads 200` with **145 cores actually
busy** -- so ~34 core-hours per member and ~2180 core-hours for 62 members plus
the prologue. (The 145 is measured on the 1e-4 build and assumed to carry over;
the 14.1 min/member is the 1e-3 build.)

| how | wall for 62 members | cores |
|---|---|---|
| today, one process, `--threads 200` | 15.0 h | 145 |
| one process, `--threads 400` | 7.6 h | ~290 |
| one process, `--threads 600` | 5.0 h | ~430 |
| bins split N ways, N x 200 threads, one node | 5.0 h at N x T ~ 600 | ~430 |
| bins split over 4 condor nodes at 200 threads | ~3.8 h | 4 x 145 |
| **members** forked K ways (single-threaded children) | 2113/K h: 68 h at K=31, 14.6 h at K=145 | K |

Two things that table says. First, splitting bins on ONE node is the same thing
as raising `--threads`, because the stage is core-bound -- its value is that it
spans NODES, where threads cannot. Second, forking members is at best
break-even (K = 145 children to match what one process already does with 145
threads) and a large loss at any sane K.

Efficiency above 200 threads is an extrapolation, not a measurement.

#### Conclusion / recipe

To get 62 members in less than 14 h, in order of effort:

1. `--threads 600` on this node instead of 200 (the stage scales with threads
   and the node has 768). No code change.
2. Split BINS across processes or condor nodes, all 62 members each, and
   `--merge-bins`. This is the axis that both parallelises and merges safely.
3. Do NOT split members across processes: impossible to merge, and unnecessary.

`--fork-members` / `--fork-selftest` stay in the tree because the selftest is
what proves the merge machinery exact, and because the member merge is needed
by nothing else.

#### Calibration, for planning a split

One bin, one thread (`--subset '0/10'`, `--threads 1`): the four-member
fixed-order stage took **17.7 min**, i.e. **4.4 core-min per (bin, member)** for
a mid-ptV bin. 210 bins x 62 members at that rate is ~950 core-hours, the right
order for the ~2180 core-hours the utilisation estimate gives (the bins are far
from equal -- the lowest ptV bin costs more than all the others together, and
the wide high-ptV bins are not cheap either: on the 10-bin subset, `binA`
(ptV 16,17) needed 2.3 min for its member stage against `binB` (ptV 18,19,20)
at ~25 min).

#### Code

* `scripts/rabbit/scetlib_ad/build_cache_parallel.py` (new): the blob
  parser/merger (`parse_rule_blob`, `parse_fo_blob`, `merge_rule_blobs`,
  `merge_fo_blobs`, `merge_shards` for the member axis, `merge_bin_caches` for
  the bin axis) plus the `--bin-groups` driver.
* `scripts/rabbit/scetlib_ad/prepare_cache_for_card.py`: `plan_variations` split
  out of `build_variations` (the canonical member list, decided before
  anything is built), `--members LO:HI` (one shard + a `.shard.json` sidecar),
  `--fork-members N` / `--fork-selftest`, and -- needed for ANY eigenvector
  build -- `set_pdf_eig_params(n_eig)` on both sub-pieces before the rules.
  Without it a `--pdf-eig > 0` build ran for hours and then died in
  `ScetlibCachedXsecTF`, which is why every cache so far has `n_eig=0`.
* `wremnants/postprocessing/scetlib_ad/xsec_backend.py`: the same
  `set_pdf_eig_params` call before `load`, taken from the cache's own names, so
  an eigenvector cache can be read at all.
* `studies/scetlib-ad-param-model/compare_caches.py` (new): `--bytes` (where two
  caches differ, structurally), `--eval` + `--diff` (value and Jacobian at the
  anchor and at a displaced point, bins matched by value).
* `studies/scetlib-ad-param-model/default_path_equivalence.py` (new): the
  stub-and-diff-the-calls proof that the default path is untouched.

## Findings

1. **Gen-level closure is exact.** Card = σ_gen(anchor) scaled to 1e6 events,
   data = σ_gen(α_s = 0.1195, λ2_ν = 0.12). The fit returns α_s = 0.1195 and
   λ2_ν = 0.12 with every other λ unmoved; EDM 3.5e-17, saturated 2ΔNLL = −0.0.
   Covariance pass gives σ(α_s) = 0.00045 and impacts split correctly over
   `resumNonpert` / `scetlibNPFeff` / `scetlibNPgammaNu`.
2. **Cost (30 bins, 32 threads).** Cache load 12 s. value+Jacobian 32 ms warm
   (1.1 ms/bin; the first call is 140 ms). Exact Hessian 0.9–1.1 s, i.e. **~35–48×
   a value+Jacobian call**, or ~1 s/bin of serial work scaling as `1 + P(P+1)/2`.
   The whole one-pass fit (minimize + exact postfit Hessian + impacts) is 40 s of
   fit time / 51 s wall.
3. **Cache build cost.** 30 bins: 1.8 min of rules + 5.8 min of fixed-order
   warming, 34 MB. The author's 5740-bin build: 32.4 min of rules + 3.2 h of FO
   warming. Per-bin cost is ~10× worse on a small cache — there is not enough
   work to fill the thread pool — so use the large-cache numbers (~0.34 s/bin
   rules, ~2 s/bin FO, ~0.84 MB/bin) for planning.
4. **`--jitCompile off` is mandatory** and is now enforced at construction with
   an actionable message. rabbit XLA-compiles the loss/gradient/HVP by default in
   dense mode, and `tf.py_function` has no XLA lowering.
5. **`examples/matched_ad/matched.conf` is NOT the analysis setup.** Against the
   bT-grid production cards (`.../Z_COM13_CT18Z_N3p0LL_btgrid_fineall/base.conf`
   + `*.ini`) it differs in: `lambda` 1 vs **0**; `transition_points`
   [0.2,0.5,0.8] vs **[0.2,0.6,1.0]**; `mu0_min`/`muB_min`/`muS_min` 0 vs **1**;
   `muf_min` 0 vs **1.40**; `compensate_fo` no vs **yes**;
   `form_np_prescription` collins_soper vs **collins_soper4**;
   `muf_follows_muB` yes vs **no**; `disable_asymmetry` false vs **yes**;
   no `[Singlet_scheme]`; `target_precision_rel` 1e-3 vs 1e-5; and **no
   `[TNPs]` block at all**. Measured effect on the λ response: 7% (λ2,
   δλ2), 10% (λ2_ν), 27% (λ4), 35% (λ4_ν), as a fraction of the response.
   `disable_asymmetry` was checked and does NOT affect `_is_inclusive()`
   (`py/qT/DrellYan.cpp:849-860,911`), so it is safe to match.
6. **Matching the analysis order gives the TNPs for free.** `(0., 'level0')` on
   each TNP tag IS N³⁺⁰LL, and a non-`off` scheme is exactly what registers the
   tag as a gradient parameter. So an analysis-faithful cache has **19**
   parameters (α_s + 4 eff NP + 4 γ_ν NP + 10 TNPs), not 9 — Phase 3 of the plan
   arrives with Phase 1's runcard rather than after it.
7. **The cache→gen mapping must be a checked fold, not a reindex.** The
   production cache is built on the theory correction's **signed** Y grid and
   nests qT innermost, while the gen grid is |Y| and flattens qT-major.
   `GenFold` sums cache bins onto gen bins, detects the Y convention, and
   verifies every gen bin is exactly tiled — a cache that half-covers a gen bin
   raises instead of quietly integrating over less phase space. Unit-tested for
   reorder / signed fold / finer-cache / four error modes.
9. **The cached rules are exact.** `tf_gradients.py --cross-check-direct` on the
   19-parameter analysis cache: values 6e-15, gradient 1.5e-15, Hessian 3.4e-14
   against the live calculation. So any AD-vs-NP difference is a difference
   between two PREDICTIONS, not an error in the replay or in this package.
10. **The analysis runcard halves the λ-response gap** — as a fraction of the
   response, λ2 7.3→5.8%, λ4 26.8→13.1%, δλ2 7.2→4.1%, λ2_ν 9.8→7.0%,
   λ4_ν 34.8→16.3%; high-qT central shape 2.55→0.81%. The residual is still flat
   in the displacement, and is consistent with the remaining known difference:
   the AD path's nonsingular is SCETlib's own analytic NLO V+jet, the NP path's
   is DYTurbo − SCETlib singular. **This cross-check cannot resolve better than
   that** — it is a test against a different prediction, not a reference. Its
   job (ruling out name/order/sign errors, which would be O(1)) is done.
11. **Cache size scales hard with the parameter count.** 30 bins: 34 MB at 9
   parameters, **80 MB at 19** (0.84 → 2.7 MB/bin; 163 → 349 rule nodes/bin).
   Extrapolated to the 5740-bin correction grid that is ~5 GB at 9 parameters and
   **~15 GB at 19** — a real constraint on the production cache, and a reason to
   consider fitting on the coarser gen binning rather than the correction grid.
13. **The straight-through construction is exact, and measured to be.**
   `differentiate=through` (let TF drive the C++ callbacks via the bridge's
   nested `custom_gradient`) vs the default straight-through quadratic: value
   identical, **gradient identical to 1.3e-16**. Checker:
   `scripts/rabbit/scetlib_ad/check_differentiate_modes.py`.
14. **The second-order failure of `differentiate=through` was OUR op choice, and
   is fixed** (revised 2026-08-19; the earlier entry blamed upstream). rabbit's fit
   vector is not SCETlib's -- only the fitted parameters, POIs first, versus every
   registered parameter in registry order -- so the model maps between them inside
   the differentiated graph. It used `tensor_scatter_nd_update`, whose backward
   pass contains a gather, whose gradient TF represents as `tf.IndexedSlices`; the
   bridge's second-order py_function payloads call `.numpy()` on the incoming
   cotangent and die. Isolated: a nested-tape HVP works on a bare `Variable`, and
   fails with a scatter in front EVEN when the scatter covers the whole vector.
   **Fix: multiply by a constant 0/1 selection matrix instead** -- bit-identical
   (entries exactly 0 and 1), negligible (~25 x 25), and TF's matmul gradient is
   always dense. Verified: a constant matmul and a concat-of-slices both work and
   agree exactly; only the scatter fails.
   Consequences: `through` now works at every order, so the straight-through is a
   MEASURED claim rather than an assertion -- agreement 1.3e-16 (gradient), 4e-15
   (HVP), 2.4e-17 (Hessian), and a full fit either way gives the same alpha_s
   (0.1195 +/- 0.00045) and the same uncertainty on every parameter. Second order
   had no cross-check before this. Straight-through stays the default on COST, not
   correctness: rabbit's postfit Hessian is `t2.jacobian(grad, self.x)` over the
   whole fit vector, pfor cannot vectorise a `PyFunc`, so `through` costs one C++
   HVP sweep per fit parameter (the bridge caches values/Jacobians, not HVPs),
   while straight-through pays one value+Jacobian and one Hessian per distinct
   point regardless of how many nuisances the card has.
   The upstream densification (`tf.convert_to_tensor(w)` before `.numpy()` in
   `_uhvp_py`) is still worth reporting -- a scatter is the natural op to reach for
   -- but it no longer blocks us. Reproducers: `$SCRATCH/isolate_indexedslices.py`,
   `$SCRATCH/test_dense_map.py`.
15. **The AD and NP central shapes differ by 2.6%** (normalised, both qT
   regions). Expected and accepted: different nonsingular (SCETlib's own
   analytic NLO V+jet vs DYTurbo − SCETlib singular) on top of Finding 5.
   `compute()` only ever uses the ratio to the model's own central, so this
   cancels to first order. With the analysis runcard the high-qT part drops to
   0.81%; the low-qT part stays at 2.4%.

23. **Everything except the profile scales is validated (2026-08-21).** alphaS
    against the `_pdfas_` templates 2.0e-03/2.4e-03, 8 NP lambda
    4.6e-04..4.9e-03, 20 TNPs 2.2e-16..7.4e-04 -- and for ALL of them the worst
    bin is the FIRST qT bin, i.e. the only residual is the known nonsingular
    cutoff difference. Reco fold closes at 0.128% (shape) / 0.149% (absolute).
    The reparametrisation is bit-exact in value AND chain rule. Asimov reco fits
    converge with truth recovered, edm 9.7e-28.
24. **`scale_x1..x3` are WRONG in SCETlib's AD path, and it is not our code.**
    Value exact at the anchor (4.4e-16), slope in x2 sign-flipped and ~-7x. The
    transition points move `muf` while the per-node beam convolutions stay frozen
    at the config's `muf` (they change 7-16% over that range). `kappa_R` escapes
    because `set_muR_factor` holds muF fixed by construction. Knowledge note:
    `knowledge/20_frameworks/scetlib_diff_scales_caveats.md`.
25. **rho(alphaS, resumScaleMuR) = +0.927.** Floating kappa_R as a continuous
    nuisance costs a factor 2.9 on sigma(alphaS), so the kappa_R TREATMENT is the
    dominant choice for the alphaS uncertainty -- more than any NP lambda. Also
    rho(lambda2, lambda2_nu) = -0.97. NB rho(alphaS, transition) = -0.65 is
    INVALID, it came from the broken direction.

---
## Open questions

- ~~**The kappa_R first-bin 4.0e-02 discrepancy.**~~ RESOLVED 2026-08-21: the
  live kappa_R did not scale the minimum-scale compensation `w_fo = mu_FO/Q`, so
  the large-bT floor moved to `muB_min * kappa_R`. Fixed upstream (scetlib-cms
  MR !3, `4df40a4`); live A/B 3.3e-02 -> 9.1e-06. Confirmation THROUGH THE CACHE
  is pending the `cache_aspair_260821_kRfix` build.
- **Does anything else induce a muf shift, or read a frozen configure-time
  constant?** Two distinct failure modes are now known, and both are invisible at
  central parameters: (a) a parameter that moves `muf` indirectly while the
  per-node convolutions stay frozen -- the transition points; (b) a parameter
  that should have scaled a compensation constant captured at configure time --
  `kappa_R` and `prof_w_fo`. Class (b) is worth a direct audit: every
  `ad_g.prof_*` read inside the `prof_live` branch is a candidate, since each one
  was computed once from the CONFIG's scales. `prof_v_muB/muS/nuS/muf` and
  `fo_muf`/`fo_kappaf` are the ones to check next.
- **Where does the transition-point uncertainty come from meanwhile?** Freezing
  `resumTransition*` leaves it with no representation at all, since the 260820
  cards carry no theory templates. Either remake a card keeping them, or accept
  the gap explicitly.

- ~~**Does a reco-level fold reproduce per-event reweighting at today's gen
  binning?**~~ ANSWERED 2026-08-20: yield-weighted 0.30% at reco, and at GEN
  level the effect is absent entirely (both routes reproduce CorrZ to <=7e-4), so
  the 0.30% is purely a reco-fold effect. Moot for now anyway -- the
  `indata.norm` route is shelved.
- **Align the nonsingular qT cutoff, and decide which value we want.** The
  low-qT λ residual (and the same first-bin feature in nearly every other
  variation) is the nonsingular cutoff: ours vanishes below qT = 0.1 GeV, CorrZ
  was made with `--qtCutoff 1.0`. Measured two independent ways in the same bin:
  `dev/(1-r)` = 0.022–0.026 for both λ2 and λ2_ν, against `dN/σ` = 0.0222 from
  the cutoff difference directly. Above qT ≈ 4 GeV the λ response matches the
  template to 1e-6..1e-8, better than `scetlib_np`. So this is a runcard setting,
  not an architecture problem — but the choice is real: 1.0 reproduces the
  analysis templates, 0.1 is arguably the better calculation. Costs a cache
  rebuild either way.
  NB the "4–16% λ-response gap to `scetlib_np`" that used to be listed here is
  the SAME residual in a different denominator: those figures are fractions of
  the RESPONSE (`dev/(1-r)`), while the variation plots show fractions of σ
  (`dev`, ~1e-3). λ4 and λ4_ν come out largest only because their responses are
  smallest. Do not quote the two side by side without saying which is which —
  that is exactly how it got mistaken for a second, separate problem.
- Secondary suspect for the λ response, only if aligning the cutoff does not
  collapse it: the binned-gradient integration target
  (`doc/autodiff-design.md` measures ~4e-6 on the value but ~1e-2 median on the
  gradients at 1e-3; the runcard now uses 1e-4) — a 1e-3/1e-4/1e-5 scan on a few
  bins would price it.
- ~~**The reco path is written but never run.**~~ RUN 2026-08-20 on the 260820
  card: 0.128% shape, 0.149% absolute, and Asimov reco fits converge.
- Cost per minimizer iteration at production binning, and whether a TF
  transcription of the rule replay (~150 sites/bin, would restore XLA) is needed.
- Whether the `c_e` PDF block needs its analytic Hessian (`2S`) or can run
  Gauss-Newton.
- Rule accuracy at the postfit point (the upstream anchor guard was removed).
---

## Decisions

### 2026-08-25 -- theory corrections stay IN the histmaker (Luca, settled)

The histmaker runs WITH the MiNNLO->SCETlib theory corrections applied, and the
param model supplies only the RATIO for the variations:

    ratio(b) = [R @ sigma_SC(p)] / [R @ sigma_SC(anchor)]      = 1 at the anchor

The alternative -- run the histmaker with `--theoryCorrAltOnly` and have the
model supply the correction itself, normalising against `indata.norm` -- is
ABANDONED. Do not revive it without Luca reopening it.

Deleted with this decision: `scripts/rabbit/scetlib_ad/compare_cards.py` (its
whole purpose was to justify the move by comparing a corrected against an
uncorrected card) and the plan that described it. Nothing else implemented that
direction -- no `denominator=` token ever landed in `param_model.py` -- so the
model as it stands is already the configuration we want, and the ratio-to-anchor
form keeps two invariants the other route gave up: it is exactly 1 at the anchor,
and it is dimensionless, so the pb->yield factor never becomes load-bearing.


- 2026-08-18 — gen-level σUL fit is the Phase-1 target — smallest cache, no
  response fold, direct injection/recovery closure.
- 2026-08-18 — Phase 1 uses the fixed-PDF `alphas`; no α_s result is quoted
  until `build_pdf_variations` folds the α_s-series member pair into that slot.
- 2026-08-18 — predict with SCETlib's own matched total; the offset to the card
  nominal is reported, not chased.
- 2026-08-18 — new sibling package `wremnants/postprocessing/scetlib_ad/`;
  `scetlib_np/` untouched while PR #701 is open, shared helpers imported.
- 2026-08-19 — **one rabbit job, exact Hessian always** (supersedes the
  2026-08-18 curvature decision). The `curvature` token is removed: K is
  unconditional, the composite Hessian is exact, and there is no `--noHessian`
  fit + `--externalPostfit --noFit` pass. Luca's call: prefer simplicity, and we
  cannot predict needing the Gauss-Newton speedup — at the gen binnings we fit on
  (few hundred to ~1200 bins) the exact Hessian is 3–80 s per minimizer iteration
  on 64 threads, and the exact Hessian also converges harder (EDM 6e-22 vs
  3.5e-17). Reintroduce a switch only if a full-5740-bin-correction-grid fit ever
  needs it (~6 min/iteration at 19 parameters). Verified: identical postfit values
  and uncertainties to the old two-pass.
- 2026-08-19 — **`differentiate=through` is now the DEFAULT** (Luca's call, once
  the dense-matmul mapping made it work). It is the ordinary TF idiom, matches the
  SCETlib example, and measured FASTER at small parameter counts: 15.8 s of fit
  time vs 40.9 s for straightthrough on the 6-parameter gen-level card, identical
  postfit values/uncertainties, EDM 4.7e-21 vs 6.1e-22. `straightthrough` is kept
  as the fallback because the two scale oppositely in the number of fit parameters
  (HVP ~2.5x a gradient, materialised Hessian ~40x, so the crossover is a few tens
  of parameters — `through` for gen-level, `straightthrough` for a reco card with
  hundreds of nuisances).
- 2026-08-19 — map rabbit's fit vector into SCETlib's layout with a constant 0/1
  matmul, never a scatter — Finding 14. Easy to reintroduce, so it is called out in
  both the module docstring and the README.
- 2026-08-19 — production caches are built from
  `scripts/rabbit/scetlib_ad/conf/Z_CT18Z_N3p0LL_analysis.conf`, not from
  `matched.conf` — Finding 5.

- **2026-08-21: do NOT attempt the SCETlib transition-point fix ourselves.** The
  muF machinery is a global member interpolation (`tf = log(kF)/var_muf_lnstep`)
  while the induced shift is per node, and `DrellYan.hpp:586` shows per-node
  `dconv` was already considered and rejected upstream. The kernel is
  clad-differentiated and the author has documented two prior silent adjoint bugs
  from this kind of surgery. Report + offer a regression test and a guard instead.
- **2026-08-21: shelved the `indata.norm` / uncorrected-histmaker route.** Keep
  the current rnorm ratio construction, where the cancellations work for us. The
  plan file remains unimplemented; revisit in a later session.
- **2026-08-21: caches live in `$MY_OUT_DIR/scetlib_ad_caches/`**, not in session
  scratchpads. Expect to rebuild all of them after any SCETlib pull (the POD
  layout guard).

### 2026-08-25 (late) -- the knot question is CLOSED: no spacing fixes the transitions

Ran the real test rather than the indirect one. `transition_variation_scan.py`
only ever scanned the variation SIZE, because `build_pdf_variations` hard-refused
any muf_lo/muf_hi but 0.5/2.0. That refusal is now lifted: the knot spacing is a
build-time factor `f`, default 2 (a strict no-op -- identical central, 28.8516 pb).

**The patch, and why it needed no cache-format change.** The interpolation side
already generalised (`t = ln(kappa_F)/ln(muf_hi)`, the lnsteps, the kernel
weights, the FO replay). Only member *building* carried the hard-coded 2, in five
places: `_muFO` plain and AD, and the `muf_min` floor compensation in
`Scale_provider::operator()`, `formulas::scales_eval`, `ad_kernel.hpp`. The last
two are clad-differentiated / POD-carried, so a new base parameter there means a
new `ad::GlobalData` field -- and `sizeof(ad::GlobalData)` IS the rule-cache POD
guard, so every cache on disk would be refused. Sidestepped by redefining
`prof_v_muf` / `Bin_rule::Var::g_v_muf` from "the Vary leg" to a **log2
exponent**, so `pow(2., v_muf)` gives `f^leg` for any `f`. Confirmed by loading
the pre-patch 210-bin `cache_260824b` with the patched build. The old guard
becomes "reciprocal and ordered" and now SETS the factor from `muf_hi`, so
members and interpolation cannot drift apart. +83/-29 over 8 files.

**Result.** Error as a fraction of the TRUE x2 response, against the runcard
route (exact refill, same build, same 10-bin subset, x2 = 0.35):

| qT | true resp | f=sqrt2 | f=2 | f=4 |
|---|---|---|---|---|
| [18,20] | -0.041% | -33.8% | -19.7% | +73.3% |
| [20,24] | -0.307% | **-22.9%** | **-28.0%** | +35.4% |
| [24,28] | -0.784% | -6.8% | +9.1% | +42.9% |
| [28,33] | -1.822% | -3.7% | +10.9% | +18.6% |
| [33,44] | -3.301% | -1.0% | +1.2% | +14.3% |

**BOTH candidate mechanisms are refuted.** Coarsening to f=4 makes the error
2-12x worse in every bin, so this is NOT a knot-independent floor -- the
interpolant is genuinely in the loop, and "one global coefficient cannot follow a
per-node shift, so knots are irrelevant" is dead. But tightening does not buy the
h^2 gain either (h = ln f; interpolation-limited predicts 4.00 per step):
measured `e(2)/e(sqrt2)` = 0.58, 1.23, -1.33, -2.96, -1.20. In [20,24] it is 1.2x
where 4x was predicted, [18,20] gets WORSE, the sign flips in three of five bins,
and there is NO spacing at which the response is right.

**What that pattern means, and the new suspect.** Error growing when you coarsen
AND failing to vanish when you tighten, with sign flips, is two competing terms:
truncation growing with h, plus something growing as the members CONVERGE. The
leading candidate is the variation-weight re-solve -- `rule_min_norm_update`'s
ridge floors its absolute residual near 1e-6 (exactly what MR !4 had to iterate
past), and a fixed absolute floor divided by a member delta shrinking like h
gives a relative derivative error that GROWS as knots tighten. It also explains
the one thing the interpolation story never covered: why tightening
`target_precision_rel` does nothing (a ridge floor is not an integration error).

**Controls, which is why the numbers are believable.** Positive: at f=sqrt2,
`mufdown` 4.86e-05 -> 8.92e-03 (183x worse) and `mufup` 4.68e-05 -> 7.32e-03
(156x), exactly as required since kappa_F = 0.5/2 are EXACT knots at f=2 but
t = -+2 extrapolations at f=sqrt2. Invariance: kappa_R, alphaS, 8 lambda, 20 TNP
all unchanged at 1e-5...1e-16. Both arms ran the same binary (f=2 is unpatched
bit for bit) on byte-identical `cache.conf`.

**Trust caveat.** [18,20] and the whole x2 = 0.58 scan point have true responses
of 1e-5...4e-4, at or near the 1e-4 node-ladder target. Not trustworthy.
[24,28] upward are solid, [20,24] marginal. Do not diagnose on [18,20].

**[SUPERSEDED the same day -- see the transition root-cause entry below.** The
scan measured the response at x2 = 0.35, where the per-node displacement D is
comparable to the knot half-step h, and there the remainder term
`E(D) = -(f'''/6) D (D^2 - h^2)` is spacing-independent and sign-flipping -- so no
spacing could have helped AT THAT VARIATION SIZE. The number a FIT uses is the
near-anchor derivative error, which is `+(f'''/6 f') h^2` and DOES fall as h^2.
Measured confirmation: at x2 = 0.55, a 12x smaller variation, the fractional
error grows toward the anchor value rather than shrinking. The experiment to run
is the f=sqrt2 arm at x2 ~ 0.55, which should cut the error ~4x.]**

**DECISION (as written at the time, now superseded): no upstream knot-count or knot-spacing feature is justified.** No
spacing makes the transition response right, so the knot route is closed as a
fix. Branch `knot-spacing` (commit `e61a8d0`, worktree
`/work/submit/lavezzo/alphaS/scetlib-knots`, build dir `build-knots`) is kept as
the instrument that closed the question, NOT as a feature to merge. Drivers in
`knot_scan/` (`knot_interp_error.py --collect` is the decisive one); caches and
per-point JSONs under `/ceph/.../scetlib_ad_caches/knot_scan/`.

**Luca's ruling (2026-08-25):** the transitions get fixed regardless of their
0.002-0.025 sigma(alpha_s) impact -- impact arguments are not a reason to leave a
wrong derivative in place. The answer is now in the code, not in the
configuration; the re-solve residual is where to look.

### 2026-08-25 -- THE alpha_s-RELEVANT RESIDUAL IS THE TEMPLATE'S NONSINGULAR CUTOFF, NOT OURS

The residual ranking of the earlier entry put **mufup 0.248 sigma(alpha_s),
lambda2 0.176, kappa_R 0.171** at the top, with their residual in the first one
or two qT bins and no improvement when the integration tolerance is tightened.
Both facts have one cause, and it is not a model defect.

**The asymmetry.** `make_theory_corr.py` zeroes the production correction's
nonsingular below `--qtCutoff`, default **1.0 GeV**
(`zero_nons_bins = slice(0j, 1j)`). Ours is SCETlib's own analytic V+jet cut at
**0.1 GeV** (`matched_nons_qt_cut`, config fallback 0.1). The card's first gen
bin is exactly qT [0,1]. So in that bin the template's variation ratio is a
SINGULAR-ONLY ratio and ours is a matched one. For a direction whose resummed
piece responds by s and whose nonsingular responds by n, with f = N/sigma,

    r_model = 1 + s + f (n - s),   r_template = 1 + s
    =>  d = r_model/r_template - 1 = f (n - s)      -- no free parameter

**Test 1, assumption-free** (f_t = 0 exactly there): rebuild the same ratio from
our own singular piece alone. Same cache, same rules, same bins, same templates.
qT [0,1], |Y|-integrated, x1e-4:

```
direction                matched   singular-only
mufup                      -88.5        -0.7
mufdown                     +8.4        -0.6
kappaFO0.5-kappaf2.        -56.9        -0.1
kappaFO2.-kappaf0.5        +34.7        +0.0
alphaS 0.120               -15.6        -1.0
alphaS 0.116               +14.5        -1.1
lambda2 -> 1.0             -41.7        +0.0
s +1                        +6.1        -0.0
```
Every direction collapses to <= 1.1e-04. Above the cutoff the singular-only
column is WORSE, as it must be -- there the template does have a nonsingular and
removing ours is the wrong thing to do. That contrast is itself the check that
the effect is specifically the cutoff.

**The arbiter was already in hand, which is why no fresh runcard run was
needed.** The CorrZ template IS the production runcard route -- SCETlib run with
kappafo/kappaf/muf written into the runcard, or at the as_0116/0120 member --
and in qT [0,1] its matched ratio is a singular-only ratio. So "our singular
ratio / template ratio = 1 to 1e-05" says that our PARAMETER route reproduces
the production RUNCARD route in that bin, for muF, kappa_R, alpha_s, the lambdas
and the TNPs at once. That also answers the `validate_variations` comment asking
whether "kappa_F = 2 via the member pair" and "Vary.muf = up via the
Scale_provider, which also rescales muf_min" are the same physical change: they
are, to 0.7e-04. A `set_muf_keep_nodes` A/B was launched, found redundant on
this reasoning, and killed to stop it holding 90 cores on a shared node -- the
previous session had already measured model/direct = 1.0000 both legs anyway.

**Test 2, one universal number.** d/(n - s) in qT [0,1] must equal f, our own
nonsingular fraction, for every direction. Measured f = **-0.0320**; measured
d/(n-s), over directions whose (n-s) spans -0.050 to +0.255 and whose residuals
span +6e-4 to -89e-4: **-0.0293 .. -0.0361**, all eight within 10% (the spread is
the O(s) correction the linearisation drops).

**Test 3, the |Y| structure predicts itself.** The residual is broadly flat in
|Y| at qT [0,1] (-107 to -140 e-4 out to |Y| 1.1, -44 at |Y| 1.8-2.5) and
strongly structured at qT [1,2], where mufup goes -14.7 e-4 at |Y| < 0.15 to
+33 e-4 at |Y| 1.8-2.5 and crosses zero near |Y| ~ 1. The central shape mismatch
Delta does exactly the same thing (-0.0055 -> +0.0178, zero near |Y| ~ 0.85). The
rapidity structure is the mismatch's, not the model's.

**Test 4, the leg asymmetry is the fixed order's, not ours.** mufup's residual
is 10.5x mufdown's. (n-s) is +0.2554 up against -0.0274 down -- a factor 9.3.
So the asymmetry the 2026-08-21 entry attributed to MR !5's floor compensation
being wrong on the up leg is the fixed-order response's own asymmetry at
qT -> 0. !5 stands, and now for a positive reason rather than an absence of
evidence.

**Why the interpolation was never a candidate.** The muF and alphaS member
columns are combined by a three-point Lagrange quadratic in t
(`ad_kernel.hpp`: w0 = 1 - t^2, w_up/dn = (t^2 +- t)/2), and the build log gives
the knots: `alphaS pair CT18ZNNLO_as_0116/_as_0120, central 0.1180 +- 0.0020`
and `muF pair kappa_F = 0.5 / 2.0`. Every direction in the ranking sits at
t = +-1 EXACTLY -- kappa_F = 2 is ln2/ln2, alpha_s = 0.120 is +0.002/0.002 --
where w0 = 0 and the interpolant returns the stored member bit-for-bit. The
interpolation cannot contribute to these comparisons at all. (It can and does to
the transition points, which land between knots; that is a different question
and another agent's.)

**Why tolerance does not help.** (f - f_t) is a difference between two
PREDICTIONS, so it is tolerance-independent by construction. In qT 20-100 the
lambdas and TNPs have s ~ 0, so (f-f_t)(n-s) ~ 0 and what is left is quadrature
noise, which falls with the tolerance; muF / kappa_R / alpha_s keep a
fixed-order response at high qT, so they keep a systematic term and do not.
Re-measured on the same 2 x 5 bins (|Y| 0-0.3 x qT 20-100) the 1e-3 and 1e-4
caches share, with the prediction alongside:

```
direction               rms d 1e-3   rms d 1e-4   ratio   pred/obs
mufup                     4.6e-05      4.2e-05     0.92      0.78
mufdown                   5.6e-05      4.4e-05     0.78      0.85
kappaFO0.5-kappaf2.       8.5e-05      8.3e-05     0.97      1.76
kappaFO2.-kappaf0.5       5.2e-05      4.7e-05     0.91      2.16
alphaS 0.120              2.6e-05      2.5e-05     0.96      4.21
lambda2 -> 1.0            2.7e-05      1.5e-05     0.56      0.26
s +1                      1.5e-06      2.2e-07     0.14      0.63
b_qqV +0.5                2.0e-06      2.8e-07     0.14      0.74
```
The systematic/noise split is exactly as predicted. The prediction's SIZE is
right for muF and 2-4x too large for kappa_R / alpha_s -- above qT ~ 33 the
nonsingular is a large fraction (f = +0.19 in [44,100]) and the two generators'
fixed-order responses cannot be swapped for each other. **Do not read the
mechanism as validated above qT ~ 6.** It does not matter for alpha_s: the
residuals in that band are <= 0.9e-4.

**THE PRICE IN alpha_s.** Same projection-and-profile method as
`residual_structure_map.py`'s companion (residual onto dln(sigma)/d(alpha_s)
from the same cache's Jacobian, profiled over the other 17 theory response
vectors with unit priors, N = 1e7, sigma(alpha_s) = 6.16e-04). "Aligned" = our
nonsingular dropped in qT [0,1], i.e. what `matched_nons_qt_cut = 1.0` gives:

```
direction                    shipped   aligned
mufup                         0.248     0.004
lambda2 -> 1.0                0.176     0.007
kappaFO0.5-kappaf2.           0.171     0.006
kappaFO2.-kappaf0.5           0.128     0.016
lambda2 -> 0.0                0.122     0.019
mufdown x kappaFO (joint)     0.113     0.072
alphaS 0.120                  0.084     0.033
...
mufup x kappaFO (joint)       0.026     0.051   <- goes UP
mufdown                       0.012     0.027   <- goes UP
transitions (3)          0.002-0.025    unchanged
```
The whole top of the ranking collapses by 25-60x. Nothing is left above
0.08 sigma; the leaders become the two JOINT muF x kappa_R directions (0.05-0.07)
and mufdown (0.027). Two entries go UP, because their shipped number had a
partial cancellation between the first bin and the rest -- worth saying out loud
rather than quoting only the improvements. The transitions are untouched (they
are identically zero below qT 16), so **after the alignment they are no longer
the least consequential residual -- they are among the largest left.**

**What is NOT settled.** Above the cutoff both sides have a nonsingular, but
DIFFERENT ones (SCETlib analytic V+jet vs DYTurbo - singular), and there the
prediction needs one assumption (that the template's nonsingular responds like
ours). With one global constant fixed at qT [0,1] it reproduces the observed
residual with R^2 = 0.96 (mufup), 0.86/0.80 (kappa_R legs) and per-bin agreement
of 10-30% at qT 1-6; for the joint directions and mufdown, where the residual is
already at the 1e-4 noise level, it does not (R^2 0.37 and below). So: qT [0,1]
is proven, qT >= 1 is consistent-and-small (<= 10e-4, <= 0.06 sigma) and not
proven. Separating it needs the template's nonsingular piece by piece, which the
corr file does not carry.

**What would fix it.** One runcard line -- `matched_nons_qt_cut = 1.0` in
`[Calculation_settings]` -- plus a cache rebuild (83 min). It is a REAL CHOICE,
not a bug fix: 1.0 reproduces the analysis templates exactly in that bin, 0.1 is
arguably the better calculation, and the bin carries 1.0% of the gen yield.
Luca's call, and the same open question the logbook has carried since
2026-08-21 under "Align the nonsingular qT cutoff" -- now with a price tag on
it. NOT launched.

Tool: `studies/scetlib-ad-param-model/lowqt_nonsingular_attribution.py`
(compute + plots, sibling to `residual_structure_map.py`, reuses its projection).
Plots: `~/public_html/alphaS/260825_scetlib_ad_lowqt_attribution`.
The earlier `260825_scetlib_ad_residual_structure/00_README.txt` has been
corrected in two places: its `resumTransition2` claim (see below) and a pointer
to this result.

**Correction landed:** that README said "the card currently FREEZES
resumTransition2, so today the transition residual has no effect on alpha_s at
all". Wrong. `resumTransition2` was removed from `params.DEFAULT_FROZEN` on
2026-08-25 once bfc6be6 fixed its derivative (only `resumTransition1/3` remain),
and the gen-level toy card floats it: `fitresults_closure18` has 18 floating
parameters including it, with rho(alpha_s, resumTransition2) = **+0.123**.

### 2026-08-25 — TRANSITION DERIVATIVE: ROOT CAUSE IS THE muF MEMBER COORDINATE

**The member "factor of two" is not a factor of two.** `Vary.muf = ±1`
multiplies muF by `f^leg` **and** divides the floor to `muf_min/f^leg`
(`Scale_provider.cpp:63-66`, and `Scale_provider.hpp` advertises it: "the muf
variation is compensated for muT = 0, so the effective cutoff is always
`(muF/Q) muf_min`"). So per node the two members sit at ln(muF) displacements

```
D_leg = ln[ f^leg  f_run(x, mu_star(b0/bT, muf_min/f^leg)/Q) / muf_anchor ]
```

which equal ±ln f only where the floor is inactive, shrink toward **zero** where
it dominates, and are strongly **asymmetric** in between. Measured from the
formulas at Q = 91.19, muf_min = 1.40, x = qT/Q, transition [0.2, 0.6, 1.0]:

```
qT = 22    bT = 0.35   0.50   0.80   1.20   2.00
  D_+/ln f            0.99   0.96   0.83   0.61   0.40
  |D_-|/ln f          0.87   0.67   0.37   0.25   0.21
```

`bfc6be6` divides the transition-induced **physical** ln(muF) shift by
`var_muf_lnstep = ln f`, i.e. by the **member LABEL step**. Those are the same
number only where `|D_±| = ln f`. Everywhere else the coordinate handed to the
quadratic is too small by

```
lambda_node = (|D_-| + D_+) / (2 ln f)  ->  1 - g phi u / (g u + 1 - g)
```

and **that limit contains no f**: verified numerically, lambda(f=sqrt2) = 0.610,
lambda(f=2) = 0.600, lambda(f=4) = 0.578, lambda(h->0) = 0.615 at qT 22 /
bT 0.80. So the deficit is a **spacing-independent floor**, which is precisely
why the knot scan found no spacing that makes the response right.

**Quantitative check against the knot scan.** Decomposing its two reliable
spacings as `e(f) = e_c + A ln(f)^2` gives a spacing-independent part

```
qT bin      e(sqrt2)   e(2)     ->  e_c        lambda-1 predicted (bT 0.5-1.2)
[20,24]      -22.9%   -28.0%       -21.2%      -11% .. -63%   (qT 22)
[24,28]       -6.8%    +9.1%       -12.1%       -7% .. -34%   (qT 26)
[28,33]       -3.7%   +10.9%        -8.6%       -4% .. -19%   (qT 30)
[33,44]       -1.0%    +1.2%        -1.7%       -2% ..  -7%   (qT 38)
```

Right sign, right magnitude, and the same monotone fall-off with qT, from a
formula with no free parameter. NB the decomposition is 2 points on 2
parameters, so it is a decomposition and not a test; the *existence* of a
spacing-independent term is the test outcome (a pure `h^2` law is refuted), and
the code analysis predicts one independently.

**Where this leaves the two candidate mechanisms and the re-solve suspicion.**
* *per-node vs per-bin*: the shift **is** per node. `rule_replay` sets
  `ad_nd = rule.nd[si]` and `cptr[m] = &rule.var[m].nd[si].conv[0][0][0]` per
  site, and `node_value` builds the shift from `ad_nd`. Member convolutions are
  retained **per node**, not as bin-level integrals. Only `node_cval`, the
  rule's tiny bin-level offset, keeps a global coordinate — it has no node.
* *interpolation truncation*: real, and now measured on its own. With an EXACT
  non-knot reference (runcard `kappaf = K` **and** `muf_min /= K`, which
  reproduces the live `scale_kappa_F = K` formula term for term — validated at
  K = 2 to **9e-16 .. 5e-6**), the model at kappa_F = 2^0.3 / 2^0.5 is off by
  **3.6e-3 / 4.3e-3 of sigma** at qT [8,9], scaling as the cubic
  `t(t^2-1)` (measured ratio 1.2-1.5 against 1.37 predicted). So the muF
  interpolant is exact at the knots and ~0.4% wrong at half a step — invisible
  to every validation we have, because all of them sit **at** kappa_F = 0.5/2.
* *variation-weight re-solve*: not the driver. Its constraint rows are
  `Va - V0` and `Ga - G0` between the nominal point and K training points of the
  **same** member (`build_pdf_variations`), so the solve contains no muF step
  and its conditioning is spacing-independent; it is refined (up to 8 passes,
  MR !4) and the caller **throws** unless the relative residual is < 1e-6; and
  `var.c_val` compensates exactly, so the member's value is right whatever the
  weights are. Empirically the hypothesis predicts the error to GROW as the
  knots tighten, and in all four bins the knot agent calls reliable-or-marginal
  it SHRANK (28.0->22.9, 9.1->6.8, 10.9->3.7, 1.2->1.0); only [18,20] grew, and
  that bin's true response is 4e-4, at the node-ladder target.
* The fixed-order half needs no analogue: `fo_node_value`'s muF is
  `kappaf*kappaFO*Q*f^vary`, flat, with no profile and no floor compensation, so
  its label IS its physical coordinate and the transitions never enter it.

**THE FIX (branch `fix-muf-member-coordinate`).** Interpolate in the physical
per-node ln(muF) instead of the label: carry `mfk_live` (where this node's live
muF is) and `mfk_dn/mfk_up` (where its two members are), all as ln ratios to
`mf_0`, the same expression at kappa_F = 1 and the **anchor** transition points
(`ad_g.prof_x1..x3`, already in GlobalData as the pval defaults). Weights become
the Lagrange quadratic through those three positions, which reduces **term for
term** to `(tf^2 ± tf)/2` wherever `mfk_up = -mfk_dn = ln f`. No stored field, no
cache-format change, `sizeof(ad::GlobalData)` unmoved.

Two things this also buys: `mfk_live` vanishes at the anchor **identically**
(same expression, same inputs) rather than only as far as `muB_lf == muB_a`
holds, so the second kappa_F-free copy of the scale and the `log(muB_a) - Lf_a`
reconstruction both go away; and kappa_F = f^leg lands exactly on a knot at
every node, floor compensation included.

**One wrong version, caught and worth recording.** The first attempt built the
member positions from the **live** transition points. The stencil then slides
along with the very shift it is meant to measure — a FIRST-order error, not
second — and at x2 = 0.35 the quadratic extrapolates off the end: the response
went 0.9979 -> **-0.640** at qT [20,24] and 0.9796 -> **7.9e+08** at [28,33].
The positions of frozen convolutions cannot depend on a live parameter. Fixed by
using `ad_g.prof_x1..x3`.

This also settles the re-solve question by construction: the same cache, the
same member convolutions and the same re-solved weights, with **only** the
assumed knot positions changed, moved the response by orders of magnitude. The
response is dominated by the member-coordinate arithmetic.

**MEASURED, against the runcard route, same bins / same build / same reference
(|Y| [0, 0.15], error as a fraction of the TRUE response).**

```
x2 = 0.35            base      fix        x2 = 0.75            base      fix
  [18,20]          -13.0%    -6.4%         [18,20]           -4.7%   -37.0% (*)
  [20,24]          -30.7%   -31.9%         [20,24]          -42.6%   -40.7%
  [24,28]          +13.3%   +10.9%         [24,28]          +34.8%   +30.8%
  [28,33]          +12.2%    +7.3%         [28,33]           +7.4%    +7.0%
  [33,44]           +1.6%    +1.5%         [33,44]           +6.6%    +4.7%
(*) true response 6.7e-05, at the node-ladder target -- not a usable number.
```

So the transitions improve by ~10% relative and are NOT closed. **The direction
this fix really repairs is kappa_F between knots**, which no validation we have
could see because every muF check sits AT kappa_F = 0.5 or 2. With the exact
non-knot reference, at kappa_F = 2^0.3, deviation from truth as a fraction of
sigma:

```
   qT      base        fix
  [8,9]   +3.577e-03  -6.62e-05     <-- 54x
 [24,28]  -7.15e-04   -6.17e-04
 [28,33]  -1.95e-04   -1.56e-04
 [33,44]  -3.84e-05   -3.52e-05
```

That is the floor-compensated region (low qT = large bT), where label and
physical ln(muF) diverge most, and it is where most of the cross section is.

**WHY NO KNOT SPACING FIXES THE RESPONSE — and why the knot route is NOT closed.**
A 3-point quadratic through ±h, evaluated at displacement D, has error

```
E(D) = -(f'''/6) D (D^2 - h^2)
```

Two regimes, and the project has been measuring the wrong one:
* **finite variation** (x2 = 0.35/0.75, per-node D up to ~0.8, comparable to
  h = ln 2 = 0.693): as h -> 0, E -> -(f'''/6) D^3, which is
  **spacing-independent**. No spacing helps, and E changes sign when |D| crosses
  h -- which is exactly the knot scan's sign flips between f = sqrt2, 2, 4 and
  its failure of the h^2 law.
* **derivative at the anchor** (what the fit uses): E/(f' D) -> +(f'''/6f') h^2,
  nonzero, flat in the variation size (hence "flat at -31% through the anchor"),
  and **proportional to h^2** -- so tightening the knots DOES reduce it, by 4x
  per halving of ln f.

The knot scan measured the response at x2 = 0.35, i.e. the regime where no
spacing can help. Its conclusion "no spacing makes the response right" is
correct and does not close the knot route for the fit: the fit-relevant number
is the anchor derivative, and there the h^2 law applies. The experiment that
settles it is a small-variation A/B (x2 ~ 0.55, D^2 << h^2) at f = 2 vs
f = sqrt2 -- the fractional error there should fall by ~4x.

And all of this is amplified: the convolution channel is ~8.6x the net
transition response and opposes it (`bfc6be6`'s own before/after at qT [20,24]:
1.024252 with no shift, 0.997697 with it, true 0.996925), the same near
cancellation `0618d4d` documents for kappa_F. So the convolution half has to be
right to ~0.3% for the net to be right to 3%, which a 3-knot quadratic over a
factor-4 muF range does not deliver.

**Still not accounted for.** With the coordinate fixed and the cubic remainder
understood, one hole remains, unmeasured: `node_cval`, the rule's BIN-level
constant offset, still interpolates its members on the global label, so its
response to x1..x3 is identically ZERO. That is the one place the
"global-vs-per-node" mechanism genuinely survives, because c_val has no node.
Two experiments would size it: measure c_val against the bin value, and zero its
member interpolation and see whether the x2 residual moves. Neither is done.

**THE NEAR-ANCHOR TEST, which is the one that matters for a fit** (x2 = 0.55, a
variation ~12x smaller than 0.35; the true response at qT [20,24] drops from
-0.31% to -0.027%). Error as a fraction of the true response:

```
                x2 = 0.35     x2 = 0.55      x2 = 0.55
qT bin            base          base            fix
[20,24]          -30.7%        -46.3%         -39.1%
[24,28]          +13.3%        +28.0%         +27.1%
[28,33]          +12.2%         +8.9%          +8.4%
[33,44]           +1.6%         +4.6%          +3.6%
```

Two things, both predicted by `E(D) = -(f'''/6) D (D^2 - h^2)`:
1. the fractional error does NOT shrink as the variation shrinks -- it tends to
   the anchor-derivative value `+(f'''/6f') h^2`, and in [20,24] and [24,28] it
   GROWS toward it, because at x2 = 0.35 the `-D^2` term partially cancels the
   `+h^2` one (per-node D there reaches ~0.8, against h = ln 2 = 0.693);
2. the fix improves every reliable bin at the near-anchor point (-15% and -22%
   relative in [20,24] and [33,44]), unlike at x2 = 0.35 where [20,24] came out
   marginally worse -- consistent with a coordinate error that is first order in
   D and therefore cleanest to see at small D.

**So the knot route is NOT closed.** The near-anchor fractional error IS the h^2
term. Halving ln f should cut it by 4x. The knot scan measured at x2 = 0.35,
where D ~ h and no spacing can help; rerunning it at x2 = 0.55 is the experiment
that decides whether tighter knots buy the fit anything.

**ALL THREE DIRECTIONS, BOTH x2 LEGS, runcard route, |Y| [0, 0.15]** (error as a
fraction of the true response; base -> fix):

```
bin       x2=0.35        x2=0.75        x2=0.55        x3=0.90        x1=0.10
[18,20]  -13.0 ->  -6.4   -4.7 -> -37*   -15 -> -31*    +1.2 -> -31*   +3.7 -> -18.4
[20,24]  -30.7 -> -31.9  -42.6 -> -40.7  -46.3 -> -39.1 -46.3 -> -40.9  -7.1 -> -32.1
[24,28]  +13.3 -> +10.9  +34.8 -> +30.8  +28.0 -> +27.1 +28.0 -> +27.1 +15.6 -> +18.9
[28,33]  +12.2 ->  +7.3   +7.4 ->  +7.0   +8.9 ->  +8.4  +4.5 ->  +8.4  +7.3 ->  +7.2
[33,44]   +1.6 ->  +1.5   +6.6 ->  +4.7   +4.6 ->  +3.6  +5.0 ->  +4.9  +4.7 ->  +3.5
```
(*) true response <= 7e-05, at or below the node-ladder target -- not usable.
NB x3 = 0.90 and x2 = 0.55 are very nearly the SAME physical variation below
qT ~ 33: g_run's lower branch depends on x2 and x3 only through
(x2-x1)(x3-x1), and 0.4/0.35 = 0.8/0.7. A useful internal check that the probe
is doing what it claims.

**Honest reading: 13 of 20 usable bin/direction entries improve, and x1 = 0.10
gets clearly WORSE at [18,20] and [20,24]** (+3.7 -> -18.4, -7.1 -> -32.1).
The commit corrects a demonstrable arithmetic error in the coordinate; it does
not follow that every bin moves toward truth, because the dominant term is the
interpolant's own remainder and correcting where the quadratic is evaluated can
push a given bin either way. Do not quote this as "the transitions are fixed".

## 2026-08-25 — gen-level 2D validation of the AD param model: 18 floating, timing, 45-toy coverage

Run dir `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_toy_260825/`,
webdir `~/public_html/alphaS/260825_scetlib_ad_gen2d_validation/` (00_README.txt indexes it).

### Findings

- **`fit_params=all` is 18, not 19.** `resumTNP_b_qqDS` has an *exactly zero*
  Jacobian column for the Z (verified: 0.0, every other column 7e-6..1.0 of the
  global max), so `_check_no_inert_params` refuses `all`. Use the explicit
  18-name list (saved in the run dir as `fit_params_all_minus_qqDS.txt`).
  `resumTNP_b_qqbarV` is nearly inert too (max relative response 2.3e-4/theta;
  postfit constraint comes back as exactly 1.000 — prior-only, not measured).

- **AD machinery works end to end with all 18 floating.** edmval 1.7e-28
  (Asimov) / 8.2e-17 (toy); injection closure at alpha_s = 0.1195 recovers
  0.11949999999590614, residual **-4.1e-12**, and all 17 other parameters return
  to the anchor to <1e-8. Dense 18x18 Hessian, covariance, `--doImpacts` all fine.

- **Timing** (serial, shared node, +-20%): 18 floating one toy = ~150 s,
  56 trust-krylov iterations, 1.9-2.5 s/iteration = one SCETlib backend call.
  Minimisation is 75-85% of the wall clock; Hessian+cov+EDM ~5 s, impacts ~10 s.
  Per-iteration cost is nearly independent of nfloat (SCETlib always returns the
  full 24-param Jacobian) and the iteration count saturates (1->2, 9->51, 18->56).
  `--noHessian` is *counterproductive* at this size. Setup floor ~30-40 s.
  100 toys ~ 3.4 h wall single-process / ~440 CPU-h.

- **sigma(alpha_s) 9 -> 18 floating: 1.25e-4 -> 4.27e-4 (3.4x)**, and 56% of the
  variance is **one** nuisance, `resumTNP_h_qqV` (rho = -0.76 with alpha_s).
  Freezing it gives 2.9e-4, exactly what the impact predicts. Gen-level
  normalisation degeneracy between the hard-function TNP and alpha_s; expect a
  reco fit to break it.

- **45-toy coverage test (rabbit default frequentist toys).** alpha_s
  `<pull> = -0.211 +- 0.166`, `rms(pull) = 1.116 +- 0.119` — passes both, so the
  reported sigma(alpha_s) is validated. 12 of 18 parameters pass outright.
  Three flags: `resumScaleMuF` mean pull -0.523 +- 0.157 (3.3 sigma, width fine
  -> displaced minimum, i.e. wrong derivative); `lambda2` +0.439 +- 0.167
  (correlated with muF, not independent); `lambda4_nu` width 1.72 +- 0.18
  (error bar understated ~1.7x, strongly non-Gaussian direction).

- **Do NOT draw theta_true from the declared priors.** 40 of 64 draws (63%) give
  a negative sigma_gen, and the surviving 24 are a truncated prior biased
  +0.4..+0.6 sigma in lambda4 / lambda4_nu / delta_lambda2 (the negative-lambda4
  trap). Use rabbit's own toy machinery instead.

### Decisions

- rabbit's **default** toy mode (`--toysSystRandomize frequentist`) *does* throw
  the param-model parameters — the model's `prior_sigmas` are folded into the
  same `cw`/`x0` vectors as the card nuisances (fitter.py ~l.312-395). It throws
  their constraint *centres*, leaving the truth at the anchor where
  `parms_prefit` records it, which is the only rabbit mode with a usable
  reference: `bayesian` mode throws the values themselves but `toyassign()`
  calls `xdefaultassign()` afterwards, so theta_true is never written out.
- All deliverables use rabbit's own tools (`rabbit_print_pulls_and_constraints`,
  `rabbit_print_impacts`, `rabbit_plot_pulls_and_impacts`); only the averaging
  over toys is local, and it reads `rabbit.io_tools.get_pulls_and_constraints`.

### 2026-08-25/26 (overnight) -- RECO-LEVEL 2D CLOSURE: card remade, central 0.128%, all 39 directions <= 7.1e-03

**The model works at reco level.** The 2D (ptll, yll) card is remade with the
SCETlib-provided uncertainties excluded, the central reco prediction closes at
**0.128 %** (shape) / **0.146 %** (absolute), matching the `scetlib_np`
precedent of 0.14 % / 0.149 %, and **all 39 theory directions close at
<= 7.07e-03** with a median of 7.2e-04 -- better than the gen-level table's
worst of 1.40e-02, because detector smearing dilutes the one bad gen bin.

Everything on the **PATCHED** SCETlib build: `92f1299 fix-muf-member-coordinate`
(MR !8), snapshot of `/work/.../scetlib-trans/build-trans`,
md5(libscet-qT.so) `e6a7faf1...`. Cache `cache_260825_p4` (1e-4, production).
Plots + tables + the full decision log:
`~/public_html/alphaS/260825_scetlib_ad_reco2d_closure/` (00_README.txt states
provenance for every figure).

#### The new card

`/ceph/.../260826_Z_2D_card_scetlib_ad/ZMassDilepton_ptll_yll_adexcl/ZMassDilepton.hdf5`

```
--excludeNuisances '^(resumTNP|scetlibNP|resumScaleZ|resumFOScaleZ|
                      resumTransitionFOScale|scetlib_dyturbo.*pdfas.*)'
```

Exactly **15** nuisances gone vs the full-template card (`260723_Z_2D_card_davidFix`):
`pdfAlphaS`, `resumTNP_*` (10), `resumFOScaleZSym{Avg,Diff}`,
`resumTransitionZSym{Avg,Diff}`. Nothing else changes and the response
auxiliary is **bit-identical** to both that card and the 260820 one, so the
caches stay valid. The model constructs on it with all **18** parameters
floating and `_check_double_counting()` passes.

**Two traps that cost the 260820 card real uncertainty, now fixed.**
1. `--excludeNuisances` matches the *systematic* name (`addSystematic`'s `name=`,
   falling back to `histname`), **not** the card-level nuisance name, with
   `re.match`. So `^pdfAlphaS$` would NOT have excluded alphaS -- its systematic
   is called `scetlib_dyturbo_..._pdfas_CorrByHelicity`. And
   `resumTransitionZSym*` and `resumFOScaleZSym*` are four outputs of ONE
   systematic named `resumTransitionFOScaleZ`: all-or-nothing.
2. **The 260820 regex was over-broad and silently deleted real uncertainty.**
   Its `scetlib_.*` branch removed the 58 CT18Z eigenvectors and the 4 MSHT20
   mb/mc-range nuisances along with alphaS (`bcQuarkMass` went 5 -> 1 members,
   the visible fingerprint). Its `muF.*` branch matched nothing at all.

**PDF eigenvectors stay as templates**, and the reason is stronger than "still
being validated": every production cache has `n_eig = 0`, so the model registers
no `pdfEig*` at all and there is nothing to double count. The split is clean --
in CT18Z alphaS is a separate member pair, not one of the 29 eigenvectors
(`pdfCT18Z` 59 vs `pdfCT18ZNoAlphaS` 58).

**Two asymmetries in the scale sector that are NOT like-for-like** and are
Luca's to rule on:
* the card's `resumFOScaleZ` is `renorm_scale_pt20_envelope`, i.e. the kappa_R
  envelope **restricted to qT > 20** (`theory_corrections.py`, deliberately,
  "redundant with the TNPs" below); the model's `resumScaleMuR` is the full
  kappa_R response at all qT. The model is BROADER below 20.
* **`resumScaleMuF` has no card counterpart whatsoever** -- with `--resumUnc tnp`
  there is no muF nuisance (zero matches for `muf` among 3746 names). Floating it
  ADDS a term the template analysis never carried.

#### Central closure, and where the residual lives

| | yield-weighted mean\|dev\| | max |
|---|---|---|
| TOTAL model / histmaker nominal | **0.128 %** | 2.24 % |
| CALC model / (R (x) CorrZ) | 0.075 % | 2.11 % |
| MC (R (x) CorrZ) / nominal | 0.073 % | 1.73 % |

* **ptll [0,1]: -1.55e-02, 100 % CALC.** The known nonsingular cutoff convention
  (production 1.0 GeV, ours 0.1). 1.2 % of the yield.
* **ptll [37,44]: -1.03e-02, 100 % MC -- and root-caused, see below.**
* everything between: <= 9e-04. Restricted to ptll > 1 GeV: **0.111 %**.

**NEW ROOT CAUSE -- the card's last gen bin is an OVERFLOW.** The histmaker's
`ptVGen` axis is `[0,...,33,44]` with `overflow=True` (checked on `prefsr`,
`prefsr_full`, `nominal_prefsr_yieldsUnfolding`), while the datacard declares a
bin `[44, 100]`. That bin **is the overflow** and holds every event with gen
qT > 44 (11.6 % of `N_gen`). The correction file's own qT axis stops at 100, so
the model can fill only 44-100 and is **15.3 % short there** (sigma_CorrZ/N_gen
= 0.847, flat in |Y|), against **1.020 +- 0.002 in all 20 bins below 44**. That
deficit leaks into the top reco ptll bin. It does NOT bias the fit at first order
-- the model supplies a ratio to its own anchor and the deficit cancels -- but the
response in `ptll [37,44]` is computed on 44-100 GeV only. Unresolved: whether
the 15.3 % is entirely the qT > 100 tail or partly the correction not being
applied above 100. Every gen hist in this file stops at 44, so it cannot be
answered from it; the experiment is a histmaker rerun with a ptVGen axis that
resolves qT > 44.

#### Variations: a three-term split, and the limiting term is the GEN BINNING

Reference = the histmaker's **own** reco variation hists
(`nominal_ptll_yll_..._Corr` + `..._pdfas_Corr`), i.e. `H_var/H_central` per
(ptll, yll) bin -- the 39 directions individually and unsymmetrised, the reco
analogue of the gen-level `Corr[var]/Corr[central]`. Not the card's `hlogk`,
which is symmetrised into SymAvg/SymDiff and would need un-mixing first.
Sanity checked: the corr hist's `central` equals the plain `nominal` to 2.9e-14.

```
r_model / r_ref = (r_model / r_A) x (r_A / r_B) x (r_B / r_ref)
                   \__ CALC __/     \__ WGT __/    \__ GRAIN __/
```
CALC = model gen response vs the correction file's;
WGT = the same response folded with our anchor spectrum vs with `N_gen`;
GRAIN = bin-averaged response vs the histmaker's PER-EVENT one -- pure gen-binning
granularity, no model physics.

| | as shipped | qT[0,1] aligned |
|---|---|---|
| worst TOTAL max\|dev\| | 7.07e-03 (mufup) | 4.57e-03 (transition 0.35) |
| median TOTAL max\|dev\| | 7.2e-04 | 7.8e-04 |
| CALC median / worst | 4.3e-04 / 7.5e-03 | 1.8e-04 / 3.4e-03 |
| WGT median / worst | 3.3e-05 / 4.2e-04 | -- (negligible) |
| GRAIN median / worst | 6.7e-04 / 4.2e-03 | unchanged by construction |
| GRAIN > CALC | 14 of 39 | **30 of 39** |

**The headline finding.** Once the qT [0,1] convention is aligned, the limiting
residual at reco level is **GRAIN -- the 210-bin gen grid -- in 30 of 39
directions, not the calculation.** GRAIN is a cost the discrete templates do NOT
pay, because they are built by the same per-event reweighting the reference uses.
It is bounded at 4.2e-03 max / 3.9e-04 yield-weighted and the fix is a finer gen
grid plus a new cache, not anything in SCETlib. That reorders the next round of
work: further SCETlib precision buys little at reco level until the gen binning
is finer.

**Relative to each direction's own response** (the quantity the "-30 % to +12 %"
transition statement refers to): NP lambdas 1.3-3.7 %, TNPs 0.2-0.9 %, alphaS
1.8-2.2 %, kappa_R/muF 1.7-7.3 %, and the **transitions 11.3 / 12.6 / 19.4 %** --
the worst by a factor 3. Their CALC parts are 5.7 %, 8.5 % and 11.9 %: for the
two shipped variations about half the reco error is the SCETlib derivative
problem and half is GRAIN, while for the 0.3_0.6_0.9 cross-check it is almost
entirely CALC. The gen-level ~30 % dilutes to ~10 % at reco through smearing and through
averaging over the bins where the response is right.
(`resumTNP_b_qqDS` has an identically zero Z response, so its `rel` of 17 is 0/0.)

#### A wrong attribution caught before publication

The first version of the central decomposition called its second term "FOLD" and
described it as bin-averaged R vs per-event reweighting. **That was wrong.** R is
stored as `R_raw/N_gen`, so `R @ N_gen` reconstructs the histmaker's reco nominal
up to the events with no gen column at all -- measured, a nearly flat -7.6e-4
(max 2.3e-3), which is reco-selected events with gen |Y| > 2.5, dropped by the
gen grid. The central prediction therefore carries essentially no fold
approximation; granularity enters only through the variations, which is why the
variation table splits three ways and the central one splits two. Relabelled MC.

#### New tooling (studies/scetlib-ad-param-model/)

* `validate_variations_reco.py` -- the 39-direction reco table, three-term split,
  `--fix-genbin0` to isolate the qT [0,1] convention, per-direction plots and 2D
  maps, CSV out.
* `reco_central_decompose.py` -- the central two-term split, the per-ptll
  profile, the `R @ N_gen` identity check, and the 2D maps.
Both reuse `scripts/rabbit/scetlib_ad/validate_variations.py`'s loaders; the
central closure itself is the existing `validate_reco.py`, unmodified.

#### NEXT

1. **A finer gen grid is now the highest-value change**, not more SCETlib
   precision: GRAIN dominates 30 of 39 directions. Quantify first by rebuilding a
   card with a finer ptVGen/absYVGen and re-running `validate_variations_reco.py`
   -- the GRAIN column should fall and CALC should not move.
2. Decide the qT [0,1] convention (`matched_nons_qt_cut = 1.0`), which is still
   the largest single-bin central residual.
3. Resolve the gen ptVGen overflow labelling (D-R13); at minimum record that the
   model under-fills it by 15 %.
4. Rule on `resumScaleMuF`, which the card never carried, and on the qT > 20
   restriction of `resumFOScaleZ`.
5. Then, and only then, an Asimov fit on the new card.

### 2026-08-26 -- FIVE muF KNOTS: measured, and it does NOT fix the transitions' template closure

Branch `muf-five-knots` (`9428460`), pushed; worktree
`/work/submit/lavezzo/alphaS/scetlib-5knot`, build dir `build-5knot`. Off
`eb60a04` = `bb2e7cb` + `92f1299` (muF member COORDINATE fix) + `83cecb2`
(settable knot spacing) + `3a8db11` + the `rule_cvals` diagnostic. `scetlib-cms`,
`build-fix`, `build-knots`, `build-trans`, `build-nak` untouched.
Webdir `~/public_html/alphaS/260825_muf_five_knots/` (00_README.txt indexes it).

**THE ANSWER TO THE QUESTION ASKED: no.** Against the production CorrZ
templates five muF knots makes the three transition directions WORSE, and every
other direction bit-identical. Against the fit-relevant NEAR-ANCHOR derivative
and against kappa_F between the knots it is a large win. Those are not in
conflict; the reason is geometric and is measured below.

#### What was built

`ad::GlobalData::var_muf` becomes the COUNT of muF member columns (0, 2, 4)
instead of a flag, and `node_value` / `node_cval` interpolate a Lagrange basis
through the anchor and those columns instead of a hard-coded 3-point quadratic.
Members are appended `[lo_out, hi_out, lo_in, hi_in]`; the inner pair is built by
handing `Vary.muf` a spacing of `sqrt(f)` and asking for its full leg, so muF and
the `muf_min` floor move together exactly as for the outer pair -- the only
construction the kernel's own knot formula can reproduce. `muf_nmem` = 2 | 4
(narrow, kappa_F = 1/2, 1/sqrt2, 1, sqrt2, 2) | -4 (wide, 1/4, 1/2, 1, 2, 4).

**The "no new `ad::GlobalData` field, no cache-format break" claim is VERIFIED,
not inherited.** The count is recovered at load by counting `Var::is_muf` and
the extra pair's leg from its own `g_v_muf`, so nothing is stored. The 210-bin
`cache_260824b`, written by a DIFFERENT build with three knots, loads unchanged
and reproduces all 39 published `validate_variations` numbers (transitions
2.85e-03 / 1.12e-03 / 3.13e-03, mufup 1.40e-02, kappa_R 7.46e-03 / 4.52e-03,
alphaS 2.15e-03 / 2.29e-03, every lambda and TNP, central identical to 0.0).

The fixed-order piece keeps THREE knots on purpose: `fo_node_value`'s muF is
`kappaf*kappaFO*Q*f^leg`, flat, no profile and no floor compensation, so the
transition points never reach it and its quadratic is already exact at the
knots. Its two inner slots are allocated and left empty so the alphaS pair,
indexed from the END of the member list on both sides, does not move.

`set_muf_knots_used(n)` evaluates a five-knot cache as the three-knot quadratic
it contains as a subset. **That is the whole reason the A/B is trustworthy**:
node set, rules, outer member convolutions and re-solved weights are
bit-identical between arms. Two separately built caches could not do it -- the
bT node set is not reproducible between processes and the logbook's own floor is
3e-03 in the Jacobian, larger than the effect. It is a global atomic and NOT
`thread_local` like `set_rule_replay_mode`, because `_stage_var_meta` runs
inside the TBB workers of `_ad_parallel_run`.

#### THE DELIVERABLE: closure against CorrZ, before and after

80-bin subset cache: ALL 10 |Y| bins x qT bins 13..20 ([14,16] ... [44,100]),
`--pdf-eig 0`, `target_precision_rel = 1e-3`, same `base_from_reference.conf` as
cache_260824b. All |Y| bins kept so the |Y|-integrated response the plot draws
is a COMPLETE sum in every qT bin; qT 13.. because the transitions are
identically zero below qT 16 ([14,16] is the null control) and the lowest ptV
bin costs more than all the others together.

**36 of 39 directions are BIT-IDENTICAL** (ratio 1.00 to every digit): all 8 NP
lambda, all 10 TNPs, kappa_R both legs, muF both legs, both joint muF x kappa_R,
both alphaS. A Lagrange interpolant is exact at its knots whatever its order,
and those directions sit at kappa_F = 1/2, 2 or do not move muF per node at all.
So the "nothing else degrades" half is proven exactly, not approximately.

| transition direction | 3-knot max&#124;dev&#124; | 5-knot | ratio | 3-knot yield-wtd mean | 5-knot |
|---|---|---|---|---|---|
| x2 = 0.35 | 2.847e-03 | 5.373e-03 | 1.89 | 5.43e-04 | 5.65e-04 |
| x2 = 0.75 | 1.124e-03 | 1.556e-03 | 1.38 | 2.81e-04 | 2.35e-04 |
| x1,x3 = 0.3,0.9 | 4.216e-03 | 7.604e-01 | 180 | 6.17e-04 | 2.50e-02 |

`max|dev|` is a single-cell statistic and it moves cell to cell, so the
yield-weighted mean is quoted alongside: for the two x2 legs the closure is a
WASH (+4%, -16%), with individual cells moving several-fold in both directions;
for x1,x3 it FAILS, over qT 24-100 rather than in one cell. **The success
criterion -- "visibly improves in qT 18-44" -- is not met.**

#### Against an EXACT runcard refill, so the result is attributable

|Y| [0, 0.15], live rules, `target_precision_rel = 1e-4`, both arms in ONE
process off the SAME member convolutions; reference = transition points written
into the runcard, so the convolutions are refilled.

* **kappa_F = sqrt(2)**, a knot of the five-knot stencil only:
  max|dev| **2.944e-03 -> 3.597e-05 of sigma, 82x**, residual flat in qT (the
  parameter/runcard reproducibility floor). This is both the CONSTRUCTION CHECK
  that the half-step members land where the kernel puts them, floor
  compensation included, and a result: **the shipped model is 0.3% of sigma
  wrong at half a knot step, and no validation we own could see it** because
  every muF check sits AT kappa_F = 0.5 or 2.
* **FINITE variation x2 = 0.35** (a template leg), error as a fraction of the
  true response: [20,24] -31.9% -> -11.4%, [24,28] +10.9% -> -8.6%,
  [28,33] +11.8% -> -1.7%, but **[33,44] +0.9% -> -11.6%**; max|dev| of sigma
  2.151e-03 -> 3.820e-03. Net worse. ([18,20] true response 4e-04, not usable.)
* **NEAR-ANCHOR derivative x2 = 0.55, what a FIT uses**: [20,24] -40.9% ->
  -14.3% (2.9x), [28,33] +8.4% -> +0.3% (33x), [33,44] +3.6% -> +0.6% (6x),
  and **[24,28] +27.1% -> +28.2%, unmoved**. max|dev| flat at 1.8e-04 because of
  that one bin, so quoting only max|dev| would hide both halves.

#### WHY the two regimes disagree -- and it is arithmetic, not a fit

`fiveknot_stencil_geometry.py` computes the per-node displacement
D = ln[muF(live)/muF(anchor)] against the knot positions from SCETlib's own
scale formulas, no calculation run. In units of ln f = ln 2, over bT 0.1..5:

```
  qT     x2 = 0.35 (template)   x2 = 0.55 (near anchor)   x1,x3 = 0.3,0.9
  19       0.004 .. 0.033        ~0.003                    0.002 .. 0.020
  26       0.300 .. 0.991        ~0.06                     0.216 .. 1.294
  30       0.536 .. 1.190        ~0.09                     0.407 .. 1.738
  38       0.759 .. 1.154        ~0.13                     0.410 .. 0.831
```

The interpolation error is a Lagrange remainder in D. Five knots refines the
INTERIOR. The near-anchor variation lives in the interior; the finite template
legs do not -- they reach 1.15 ln f, and the x1,x3 direction 1.74 ln f, i.e.
OUTSIDE kappa_F = 2, where the model is EXTRAPOLATING and a quartic
extrapolates worse than a quadratic. Refining the interior cannot help a point
outside it. Figures: `mechanism/stencil5_qT_*.png`.

#### The [24,28] near-anchor floor: order-independent, and PREDICTED

x2 = 0.55 at qT [24,28] does not move (+27.1% -> +28.2%, 1.86e-04 of sigma).
The 2026-08-25 README already measured "a spacing-INDEPENDENT floor of about
1-2e-04 per bin" at exactly this bin and variation (+27.1% at f = 2, +26.3% at
f = sqrt2). Five knots reproduces it, so it is neither the knot spacing nor the
interpolation order. Its two named candidates are `node_cval` -- the rule's
bin-level constant, which has no bT node, interpolates on the GLOBAL kappa_F
label and therefore has IDENTICALLY ZERO response to x1..x3, and whose measured
upper bound there (max|dc|/sigma = 2.3e-04 .. 3.2e-04) brackets what is left --
and the reference's own node-ladder target of 1e-04. **The experiment that
separates them, NOT done: zero the `node_cval` member interpolation and
re-measure this bin.**

#### The WIDE geometry: NOT a measurement, a broken prototype (stated plainly)

Section 4's geometry suggests BRACKETING the displacement instead of refining
the interior: kappa_F = 1/4, 1/2, 1, 2, 4, still exact at 1/2 and 2. The first
run gave 31% of sigma at x2 = 0.35 and it was nearly written up as "wide is
measured bad". **It is not a measurement.** Its own knot test refutes it:
kappa_F = 4 is a knot of that stencil, so it must be exact, and it came back
3.7e+08. A relative-tolerance fix to the degeneracy guard was applied (the
absolute 1e-8 x ln f cut kept nodes whose DIFFERENCES were pure rounding, where
the floor collapses all the positions together at qT just above x1*Q). Whether
that repairs the wide arm was still running at the time of writing --
**do not quote the 31% as a property of the wide geometry.**

Two things that fix does NOT change, checked: the 39-direction no-op on
cache_260824b still reproduces every published number, and the narrow closure
table above is bit-identical before and after. So the guard was never biting in
the narrow arm, and the x1,x3 = 0.76 above is genuine extrapolation, not a
guard artefact.

#### Traps found, worth carrying

1. **`ScetlibCachedXsecTF.values_and_jacobian` memoises on the parameter vector
   alone** (`self._cache_key = p.tobytes()`). Any global that changes the model
   -- `set_muf_knots_used`, `set_rule_replay_mode` -- is not in that key, so two
   arms evaluated back to back at the same p silently return the FIRST arm's
   numbers for both. The A/B then shows a perfect null, indistinguishable from
   "the change does nothing". It happened here: the first closure run returned
   ratio exactly 1.00 for all 39 directions. `fiveknot_closure.py` now carries a
   hard guard -- a kappa_F = sqrt(2) probe that MUST separate the arms, and the
   script refuses to report a null if it does not.
2. `set_muf_knots_used` must not be `thread_local`: `_stage_var_meta` runs in
   the TBB workers. A test would have shown "no effect" and been read as "five
   knots changes nothing".
3. clad cannot compile a braced array initialiser whose entries are not
   literals, nor a `const` one -- it rewrites them into `clad::move()`, which
   has no matching overload. Assign elementwise.

#### What to do instead

The prior analysis's option (c), now with a sharper reason: an analytic
**d(conv)/d(ln muF) column per node**, which is `(alpha_s/2pi) P (x) f` and
which SCETlib already has since it is what makes the beam function
muF-independent. It is first-order EXACT in D, so unlike more knots it does not
care whether D is inside a stencil -- and the geometry above shows D leaves the
stencil at exactly the variation size the templates use. It also performs the
muF renormalisation-group cancellation analytically instead of numerically.
Tractability, as far as this round can judge: the column has the same shape as a
conv block, so it fits `Node_varying` / `ad_conv_var` with no new concept; it is
ONE extra column per node rather than two extra member builds per bin, i.e.
cheaper than what was tried here; and it needs no member staging and no
re-solved weight vector. What it needs and this round cannot settle: an export
of `P (x) f` on the frozen bT nodes at the stored conv's muF, and a decision on
whether ONE derivative column suffices for the template-sized legs where
D ~ 1.15 ln f -- clearly yes for the fit derivative, to be measured for the
templates.

**Recommendation.** Do not merge the five-knot stencil to fix the transitions;
it does not. `92f1299` (the coordinate fix, MR !8) still stands on its own
merits. The five-knot branch is pushed and NOT proposed as an MR; if it is ever
wanted it is for kappa_F between knots (82x) and the fit derivative (3-33x),
which is a different argument from the one it was built for, and Luca's call.

### 2026-08-25/26 (overnight) -- `--n-train` GATE RESOLVED: keep 9. And the build cost is set by the TOLERANCE, not by n_train.

**The gate.** `--n-train` defaults to 9; with 29 PDF eigenvector pairs the
parameter count goes 24 -> 53, so the ratio n_train/n_params falls to 0.17 and
upstream would use `max(9, ceil(1.5 P)) = 80`. The 62-member build was gated on
whether that matters.

**It does not, and the premise is backwards.** The rule solve's UNKNOWNS are the
retained site weights; P appears in the ROWS. From the source
(`DrellYanAD.cpp::build_bin_rules`): `blk = 1 + P + n_hvp*P`,
`nrow = 1 + n_train*blk`, so each parameter adds two rows per training point.
Constraints per unknown, parsed per bin out of the rule blobs:

| cache | n_train | P | rows | sites/bin | rows/sites |
|---|---|---|---|---|---|
| **cache_260825_p4 (210 bins, in production TODAY)** | 9 | 24 | 442 | 300 (min 247) | **1.51**, worst bin **1.09** |
| **m210_asmuf (210 bins, tonight)** | 9 | 53 | 964 | **277** | **3.48** |
| eig29_nt9 (4 bins, qT 20-28) | 9 | 53 | 964 | 364 | 2.65 |
| thin_nt9 (4 bins, qT 5-7) | 9 | 53 | 964 | 239 | 4.03 |
| ref0a (same 4 bins) | 9 | 24 | 442 | 372 | 1.19 |

Turning the eigenvectors on makes the solve **2.3x better conditioned on the
real card**, and it keeps FEWER sites (277 vs 292), so the cache is slightly
smaller per member than a naive scaling gives.

**Measured accuracy, five ways, all consistent.**
1. Against the production templates (4 bins, P = 53): flat from n_train 9 up,
   inside a MEASURED build-to-build floor of +-10-14% (two independent nt9
   builds). alphaS is 1.88e-05 at n_train 5, 9, 14 AND 27 -- identical.
   n_train 5 is 9.3x worse in NP lambda.
2. Against a LIVE SCETlib evaluation (no template, so no cutoff mismatch), 12
   random JOINT points: 6.98e-06 / 6.03e-07 / 5.80e-08 / 4.63e-08 at
   n_train 5 / 9 / 14 / 27. It keeps improving -- but from a level 3 orders
   below what limits the model.
3. In sigma(alpha_s) units (residual projected through F^-1 L^T W with the
   other 52 nuisances profiled): **1e-5 sigma at n_train 9** where the fit sits,
   0.003 sigma at 8x the template displacement, against **0.002-0.025 sigma**
   for the transition residual. n_train 5 gives 0.024 sigma -- the top of that
   band. 9 clears it by a factor 8.
4. Toy Asimov sigma(alpha_s) from the model's own Jacobian: 9, 14, 27 all inside
   a measured 0.70% build-to-build floor.
5. The card's THIN bins (qT 5-7 GeV, 239 sites, matching the card's min of 247)
   are **46x BETTER** than the corner the scan used, not worse.

**Cost of raising it (all measured, 4 bins, P = 53):** 9 -> 27 doubles the
retained nodes (364 -> 720) and therefore doubles the cache (13 -> 28 GB), the
fit's RSS (51 -> 108 GB), every value+jacobian call (52.9 -> 122.5 ms) and the
hessian (10.9 -> 25.3 s). Retained sites are 1.3-4.3% of the 17374 available.

**The 62-member build, measured:** rules stage at P = 53 on 210 bins **28.2 min**
(vs 4.4 at P = 24); rules blob **~13-14 GB**, npz **~2.3-2.5 GB**; build process
**~60 GB resident and ~1874 OS threads whatever `--threads` says**; the loaded
model in a fit **~51-55 GB**, ~1.2 s per value+jacobian and ~4-5 min per hessian
at 210 bins.

**THE THING NOBODY COSTED, and it is 13x bigger than anything n_train does.**
The "~14 h for 62 members" projection is at `target_precision_rel = 1e-3`. The
PRODUCTION cache `cache_260825_p4` runs at `rel = 1e-4, abs = 0`:

| | node set | rules | fixed-order, 4 members |
|---|---|---|---|
| cache_260824b (rel 1e-3, abs 0) | 21.9 min | 4.4 min | **54.8 min** |
| cache_aspair_260821_kRfix (1e-4, abs 1e-8) | -- | 8.5 min | 82.8 min |
| cache_260825_p4 (1e-4, abs 0) | **325.3 min** | 10.6 min | **715.6 min** |

`abs 1e-8 -> 0` alone (changed 2026-08-24 on Josh's advice) is worth **8.6x**.
Accuracy cost of dropping to rel 1e-3, measured on IDENTICAL bins and confirmed
by a second thread-matched pair: NP lambda x25, TNP x28, muF x1.5,
**alphaS x1.08**, transitions unchanged -- leaving lambda/TNP at 1.5e-05/5.5e-06,
still an order below the muF residual and two below the transitions. The one
caution: the worst per-bin TRAINING residual on the 210-bin card is 6.1e-07 at
1e-3 against 2.5e-08 at 1e-4, and the builder WARNS above 1e-6.
**This is a decision for Luca. The build cannot be costed without it.**

**Two corrections to inherited claims.**
* "The hessian rises 3.2x for two extra parameters" -- REFUTED. That came from
  two `backend_check` runs on a node at load 250-570. Interleaved in ONE
  process: P 24 -> 26 is **x1.09**, P 24 -> 53 is x2.95, and toggling the
  `_rule_is_matched` short-circuit changes the TIME by 2%. The covariance pass
  is not the binding constraint; memory is.
* "n_train 5 would make the build ABORT" -- too strong. The guard is a RESIDUAL
  check (`rmax > 1e-6`), and the "fewer sites than constraints" text is only an
  explanatory suffix. `thin_nt5` has THREE of four bins below `m = 163` and
  wrote its cache with a residual of 7.1e-09. **Too small an n_train degrades
  silently rather than refusing** -- the more dangerous failure mode.

**One thing to fix before the build.** The uncommitted `py/scetlib_tf.py` in the
SHARED tree (`_rule_is_matched`, the nonsingular double-count fix) changes every
Hessian by **152%**. It is live on PYTHONPATH for every session. Commit it
(branch `fix-nons-double-count` exists) so the cache and the evaluation code are
pinned together.

**Handover to the transition work.** The rule replay and the LIVE parameter route
disagree by **7.8%** at `scale_x2 = 0.35` -- flat in n_train (7.74/7.86/7.80/
7.81e-02 at 5/9/14/27) and **identical at P = 24 with no eigenvectors at all**
(7.842e-02), so it is in the configuration in production today. `scale_kappa_R`
is clean at 6e-07 on the same test, which is the control. The rule agrees with
the RUNCARD-route template to 2.17e-03 at that same point, so the live parameter
route is the outlier. A 4-bin cache built against the muF-member-coordinate fix (`build-trans`,
92f1299), with BOTH routes on that library, gives **the same 7.873e-02** -- so
the muF member coordinate is NOT the cause either. The only candidate left is
the frozen beam convolutions, and `ab_scale_route.py` (runcard route vs
parameter route, one library) is the experiment that isolates it.

Everything: `~/public_html/alphaS/260825_scetlib_ad_ntrain_gate/` (9 figures,
00_README.txt with per-figure provenance, TABLES.md with 24 tables) and
`DECISIONS_ntrain_gate.md` (30 decisions).

### 2026-08-26: the gen grid, measured — GRAIN is a solved problem, and what is left is not GRAIN

Staged for `studies/scetlib-ad-param-model/LOGBOOK.md` (do not paste over
another session's edits; three agents were live).
Plots and tables: `~/public_html/alphaS/260826_scetlib_ad_grain_vs_grid/`
(00_README.txt carries the full provenance and the reproduce lines).

**Follow-up to the reco-2D closure round**, which found GRAIN — pure gen-binning
granularity — larger than CALC in 30 of 39 directions once the qT [0,1]
convention is aligned, and recommended measuring what a finer gen grid buys.

---

#### The first thing to know: it is a HISTMAKER question, not a cache question

`R = R_raw/N_gen` comes out of `nominal_prefsr_yieldsUnfolding`, whose gen axes
are `rebin_pt(reco ptll edges)` — **one gen bin per two reco bins** — and the
positive half of the reco yll edges. So the card's 21 × 10 grid is the finest
response matrix that exists on disk, and a finer SCETlib cache on its own is a
**no-op**: `Σ_{g'⊂g} P(b|g) σ(g') = P(b|g) σ(g)`.

Two dedicated histmaker runs were made rather than extrapolating, with
`finegen_histmaker.py`, which monkeypatches `get_unfolding_dilepton_axes` **in
its own process** (the shared checkout was not touched):

* `260826_Z_histmaker_finegen` — gen qT = the reco ptll edges (40 bins), gen |Y|
  midpoint-refined (20). Wall **37 min**, full Zmumu statistics (293 M events).
* `260826_Z_histmaker_corrgrid` — gen grid = the **correction file's own cells**
  (qT 70 bins to 100 GeV, |Y| 11 to 2.5). Wall **44 min**.

Controls: each run coarsened back to 21 × 10 reproduces the production card
direction by direction (**ratio median 1.0006, range 0.9986–1.0099** over the 37
non-null directions); the two runs agree with each other to the printed digits;
`(R summed over gen)/nominal − 1 = −7.53e-04`, i.e. the gen-|Y|>2.5 leak the reco
agent measured as −7.6e-04, and nothing else.

---

#### Finding 1 — GRAIN has an exact zero, because the correction is a bin lookup

`load_corr_helpers` builds a plain `makeCorrectionsTensor` for this generator
(no "Helicity" in the name), and `correctionsTensor_helper` "returns what is in
the bin of the histogram" — no interpolation, no angular dependence. The
per-event response is therefore **piecewise constant on the correction file's
(absY, qT) cells**, so any gen grid that refines them makes the bin-averaged
response exact and GRAIN vanishes identically. The target grid is a specific
finite one, not "as fine as affordable".

The correction's grid: qT 70 bins (0.5 GeV to 15, 1 GeV to 40, then 42, 44, …,
100); absY `[0, .15, .3, .5, .7, .9, 1.1, 1.3, 1.5, 1.8, 2.0, 2.5]`. **The
card's gen |Y| grid is already that, minus the single edge at 2.0.** In qT the
card is exactly 2× too coarse from 1 to 12 GeV and worse above.

#### Finding 2 — the mechanism is a saw-tooth, not curvature

Splitting each reco ptll bin by which half of its parent gen bin it sits in, the
signed yield-weighted GRAIN of the two halves is equal and opposite for 22 of the
25 directions above 3e-05: **median oscillating fraction 0.87**. That is the
fingerprint of two reco bins sharing one gen bin, and it is why the fix is
structural rather than asymptotic. The exception is the α_s pair (0.18), which
carries a coherent offset instead — see Finding 4.

#### Finding 3 — measured: the candidate grids

Yield-weighted mean |model/reference − 1| over 780 reco bins; median (worst) over
the 39 directions. "eqAs" = the α_s equivalent per unit nuisance pull, in units
of the Fisher σ(α_s) = 4.752e-04.

| grid | ngen | GRAIN med | GRAIN worst | eqAs worst | eqAs quad | eqAs w/o α_s |
|---|---|---|---|---|---|---|
| A shipped 21×10 | 210 | 5.36e-05 | 3.89e-04 | 0.152 | 0.270 | 0.152 |
| B gen qT = reco ptll 40×10 | 400 | 1.25e-05 | 3.44e-04 | 0.076 | 0.144 | 0.076 |
| C B + the \|Y\| 2.0 edge 40×11 | 440 | 8.01e-06 | 3.30e-04 | 0.077 | 0.121 | 0.077 |
| **D C + resolve qT 44–100 52×11** | **583** | **7.46e-06** | **3.29e-04** | **0.035** | **0.054** | **0.020** |
| E shipped qT + D's rest 33×11 | 374 | 5.17e-05 | 3.96e-04 | 0.165 | 0.246 | 0.165 |
| G the correction's grid 71×11 | 781 | 3.41e-06 | 3.30e-04 | 0.034 | 0.046 | 0.0017 |

Read in order: **E vs A** says the |Y| edge and the qT tail buy nothing on their
own — refining gen qT below 44 is the necessary first move. **A→B** is the
single biggest step. **B→C** costs 10% more bins for another 1.6× on the median
and 4.4× on the per-bin max. **C→D** is what collapses the α_s footprint, and it
is the qT 44–100 region: everything above 44 currently sits in ONE gen bin whose
response is the correction's (44, 100] average. **D→G** buys 2.2× more on the
median but nothing on α_s.

CALC, by contrast, is **flat** against the grid (median 7.3–7.8e-06 from 21 down
to 2 gen qT bins) — it is a gen-level physics difference and no binning touches
it. GRAIN at the shipped grid starts 7× above it and grid D takes it to within a
factor 1.

#### Finding 4 — what is left is NOT granularity: the α_s legs carry an event-level weight

Exactly two of the 39 directions barely improve on any grid (1.06× from 21 × 10
to 71 × 11): the two `pdfCT18ZNNLO_as_*` legs. They are also **the only two whose
histmaker weight is not a pure bin lookup** — `..._N2LO_pdfas` is in
`theory_corr_weight_map` with `alphas=True, renorm=True`, so
`define_theory_corr_weight_column` gives it
`res(i) = <event-level LHAPDF member weight> × nominal_weight_uncorr /
central_pdf_weight`, i.e. the applied response is the binned correction ratio
**times an event-level PDF-member ratio**. No gen binning reproduces an
event-level weight.

That reclassifies part of what the reco round called GRAIN: for the α_s pair,
3.3e-04 yield-weighted and 0.034 σ on α_s is a **model-vs-template construction
difference**, not a fold error. Consistent with everything else seen: its
residual is a coherent offset rather than a saw-tooth, it is concentrated at
|y| > 1.8 (6.4e-04 against ~3e-04 centrally, where the PDF x-range is most
extreme), and it survives resolving both gen axes and the qT range.

Read with care: 0.034 σ is per Δα_s = 0.002, i.e. a ~2.5% error on the SLOPE of
the α_s response; over a realistic ±1σ excursion it is ~0.01 σ of bias.

**Not proven, and the experiment that would prove it:** rerun the histmaker with
`_pdfas` dropped from `theory_corr_weight_map` (pure bin lookup) and re-measure.
Those two legs should then fall like every other direction.

#### Finding 5 — the cost, from the production build log and the cache's own rules

`cache_260825_p4/build.log` (210 bins, `target_precision_rel = 1e-4`,
`--threads 210`): outer node set + matched σ **325.3 min**, rules 10.6 min,
resummed members 1.6 min, fixed-order members **715.6 min** → **17.6 h**, 222 MB.
These are 15–50× the numbers in
`knowledge/20_frameworks/scetlib_ad_cache_build_parallelism.md`, which were taken
at `target_precision_rel = 1e-3`; use the note for which axis each stage
parallelises over and the log for the absolute cost.

Parsing the cache's own rule records for how it scales with bins:

| | min/bin | median/bin | max/bin | total |
|---|---|---|---|---|
| outer nodes `n_sites` | 247 | 300 | 406 | 67 599 |
| fixed-order `n_fo_w` | 396 | 396 | 10 824 | 134 739 |

`n_sites` is uniform to ±20% across qT bins, so the 325-min stage is essentially
**linear in bins**. `n_fo_w` is not: qT [0,1] holds **23.2%** and qT [44,100]
**18.4%** of all fixed-order nodes, every other bin sitting at the floor of 396.
**41.6% of the 715-min stage lives in two qT bins** — that is where the "wildly
unequal bins" effect actually is, in the fixed-order stage, not the resummed one.
Usefully, grid B splits only the cheap ones (qT [0,1] IS the first reco ptll
bin, so it is untouched): ~1.6× the build, ≈28 h at 210 threads, ~420 MB.
Grid D additionally splits [44,100] into 12: 2.3–4.0× (bracketed, not measured),
≈45–70 h. Grid G also splits qT [0,1], the single most expensive bin.

MC statistics do **not** degrade under refinement — σ_reco(b) = Σ_g (σ_gen/N_gen)
R_raw(b,g), so splitting a column splits the same events with a smooth weight —
and the measurement confirms it: GRAIN keeps falling to 3.4e-06 at 781 bins
rather than hitting a noise floor.

---

#### Decision

**Recommend grid D:** gen qT = the reco ptll edges to 44 GeV, continued above 44
by the correction file's own edges (46, 48, …, 60, 65, 70, 80, 90, 100), plus the
>100 overflow; gen |Y| = the card's ten edges plus one at 2.0. 52 × 11 = 583 gen
bins, 2.8× the shipped 210. One ~40 min stripped histmaker rerun (2–3 h for the
full production configuration) plus a 45–70 h cache build.

It brings the median GRAIN from 5.36e-05 to 7.46e-06 (7.2×), the worst per-bin
GRAIN from 4.21e-03 to 1.35e-03, and the worst direction's α_s equivalent from
0.152 σ to 0.035 σ (0.020 σ excluding the two α_s legs).

**Do not** go past D for α_s: G is 2.2× better on the median and identical on
α_s, because both already sit on the α_s-leg floor.

**And the honest form of the headline that was asked for.** "This resolution
brings the worst direction from 7.07e-03 to X" has no answer: the worst direction
as shipped is mufup and its 7.07e-03 is CALC (7.47e-03), the qT [0,1]
nonsingular-cutoff convention, which no gen grid touches. The three statements
that do have answers are in the table above, plus: the qT[0,1]-aligned worst goes
4.57e-03 → ~3.4e-03 and stops being a grid problem — the limiting direction
changes from `transition_points0.2_0.35_1.0` (GRAIN 4.20e-03 → 4.3e-05) to
`transition_points0.3_0.6_0.9`, whose 3.36e-03 is all CALC, i.e. the
transition-point derivative problem that is tracked separately.

#### Next

1. Build the grid-D histmaker + card + cache, and re-run the reco-2D closure on
   it — that is the only way to get CALC and TOTAL (not just GRAIN) on the finer
   grid; a fine cache was deliberately NOT built tonight.
2. Settle Finding 4 with the `theory_corr_weight_map` experiment above.
3. A 1-bin `--subset` timing test on the grid-D runcard would replace the
   bracketed 2.3–4.0× build factor with a measurement in minutes.

### 2026-08-26 -- ANALYTIC d(conv)/d(ln muF): the gate is passed, and the answer
###                is a HYBRID, not a replacement

Worktree `/work/submit/lavezzo/alphaS/scetlib-anlmuf`, build dir `build-anlmuf`,
branch `muf-analytic-dglap` off `eb60a04` (= `bb2e7cb` + `92f1299` muF member
coordinate fix + `83cecb2` settable knot spacing + `3a8db11` + `rule_cvals`) --
the same base the five-knot round used, so every number here is directly
comparable to `260825_muf_five_knots`. `scetlib-cms`, `build-fix`,
`build-knots`, `build-trans`, `build-nak`, `build-5knot` untouched.
Webdir `~/public_html/alphaS/260826_analytic_muf_dglap/`.

#### THE QUESTION D-022 LEFT OPEN, AND WHY IT WAS THE WRONG WORRY

D-022 asked "whether ONE column suffices where D ~ 1.15 ln f", the concern being
that a first-order expansion has an O(D^2) remainder and D ~ 0.8 is not small.

**That worry is void, and for a structural reason.** d/d(ln muF) RAISES the
alphaS order of a conv kind by one -- f -> P0(x)f -> P0xP0(x)f -- and the kind
set is truncated at `fo_lvl`. The generator is therefore NILPOTENT and the
D-series TERMINATES: at the production fo_lvl = 2 the exact truncated-order
solution is a *quadratic* in D, at fo_lvl = 3 a cubic. There is no D-truncation
to worry about at any D.

**What limits the route instead** is how well fixed-order DGLAP reproduces
LHAPDF's OWN grid evolution, because the runcard reference refills the
convolutions from LHAPDF. That is measurable directly, with no prototype:
`DrellYan.conv_probe(x, muf, pid, side)` returns exactly the convolutions the
node cache freezes, at ANY muF.

#### THE GATE (no prototype needed; `dconv_dlnmuf.py`, `dconv_gate2..7.py`)

Convention fixed from SCETlib's own I1 (`k[0] = 2 Lf P0 + I1`,
Lf = log(muB/muF)): muF-independence at O(alphaS) forces

    d conv / d ln(muF) = 2 g P0(x)conv + 2 g^2 P1(x)conv + 2 g^3 P2(x)conv,
    g = alphaS(muF)/(4 pi)

and the O(alphaS^2) Lf structure of I2 reproduces it with alphaS at muF (the
leftover b0 Lf term is exactly the running between muB and muF). **P0(x)f,
P1(x)f and P0xP0(x)f ARE conv kinds the node already stores**, so the derivative
needs no new object at all.

Against a converged central difference of `conv_probe`:

| muF (GeV) | P0 only | P0+P1 | P0+P1+P2 |
|---|---|---|---|
| 2 | -45% | -8.0% | **-0.46%** |
| 5 | -30% | -2.9% | **-0.13%** |
| 13 | -22% | -1.4% | **+0.016%** |
| 45 | -17% | -0.61% | **+0.006%** |

The NNLO splitting kernel P2 is what makes the derivative faithful. It is NOT
filled at the production `fixed_order = nnlo`, but its grids exist on disk
(`share/scetlib/beamfunc/CT18ZNNLO_beamfunc/CT18ZNNLO_P2_*`).

#### THE CONSTRUCTION: analytic evolution PLUS interpolated residual

The analytic evolution alone must NOT replace the member interpolation: it is
0.2-0.5% wrong AT kappa_F = 0.5 and 2, where the members are exact by
construction, and kappa_F is the largest alphaS-relevant residual in the model.
What is added to the kernel is

    cvi[k] = SUM_m W_m conv_m[k]                    <- unchanged, today's model
           + delta_k(D) - SUM_m W_m delta_k(m_pos)  <- NEW

with delta_k(0) = 0 identically. **It vanishes at the anchor AND at both
members**, so kappa_F, the alphaS pair, all 8 NP lambda and all 10 TNPs are
untouched BY CONSTRUCTION, not by measurement. On a degenerate node (the floor
compensation has pinned muF, both member weights zero) it reduces to delta(D)
alone -- a strict gain, since such a node has no convolution response at all
today.

At the REAL node geometry (member positions from SCETlib's own scale formulas,
floor compensation included), error on conv[c_delta] as a % of that node's true
response, worst over bT = 0.1 .. 5:

| direction | shipped | analytic ALONE | Hermite | **analytic + residual** |
|---|---|---|---|---|
| x2 = 0.35, qT 22 | 1.44% | 0.50% | 0.95% | **0.46%** |
| x2 = 0.35, qT 26 | 0.85% | 0.39% | 0.50% | **0.30%** |
| x2 = 0.35, qT 30 | 0.72% | 0.54% | 0.054% | **0.057%** |
| x2 = 0.35, qT 38 | 0.36% | 0.27% | 0.037% | **0.031%** |
| x2 = 0.55 (a FIT), qT 30 | 0.92% | 0.10% | 0.014% | **0.072%** |
| x1,x3, qT 30 | 3.74% | 0.75% | 1.56% | **0.78%** |
| kappa_F = 1/2, 2 | 0 (exact) | 0.2-0.5% | 0 (exact) | **0 (exact)** |

Hermite -- a cubic through both members with the exact analytic anchor slope --
is the runner-up and is also exact at the members, but it EXTRAPOLATES badly
where the member stencil has collapsed, which is exactly where the shipped model
is worst.

Reading these at the sigma level: the muF RG cancellation makes the NET
transition response 5-19x smaller than the convolution half alone (measured at
qT [20,24]: +2.43% analytic, -2.66% convolution, -0.23% net against a truth of
-0.31%), so a 0.05% conv error is a ~0.5% sigma error where the shipped 0.72%
is ~7%.

#### TIERS, AND WHY THE MIDDLE ONE IS WORSE THAN EITHER END

Four of the seven conv kinds the full alphaS^3 evolution uses (P2, P0xP1, P1xP0,
P0xP0xP0) are not filled at fo_lvl = 2. Filling them costs 16 more beamfunc grid
families (~260 MB for CT18ZNNLO), extends the stored conv prefix 11 -> 15 and
needs the nodes REBUILT. Over 95 diagnosable (qT, direction, |Y|, flavour, beam)
cells ("diagnosable" = the node's own muF response exceeds 1e-3 of its
convolution, the conv-level analogue of the sigma-level 1e-4 rule):

| tier | terms | extra cost | median | 90th pct | worst | worse than shipped |
|---|---|---|---|---|---|---|
| shipped | -- | -- | 0.919% | 7.80% | 104.8% | -- |
| **mode 1** | J1,J2,K11 | **NOTHING** | **0.406%** | 2.72% | 51.1% | 17 / 95 |
| mode 2 | +J3 (P2) | 5 families | 0.622% | 2.94% | 57.8% | 34 / 95 |
| **mode 3** | all 7 | 16 families + rebuild | **0.322%** | **1.46%** | **20.3%** | **4 / 95** |

**Mode 1 needs no new stored data at all** -- it uses only kinds the fo_lvl = 2
prefix already holds -- which is what makes an A/B on the EXISTING production
cache possible, both arms from one cache, the only way to get a bit-identical
control. The intermediate tier is worse than either end because the terms mode 1
omits are smooth LOW-ORDER POLYNOMIALS in D (degrees 1, 2, 2, 3) that the
quadratic residual interpolation already absorbs exactly up to degree 2; adding
back only the degree-1 piece changes the residual's shape without removing
anything the correction was not already handling.

#### THE alphaS BOOKKEEPING, and one construction that was tried and rejected

The evolution coefficients are integrals of powers of alphaS over [0, D] in
ln(muF), and D is a live function of the transition points, so a quadrature would
put a loop on the clad tape. **Endpoint closed forms were derived (one- and
two-loop, fixed nf) and REJECTED on measurement**: 0.3-0.6% off a 256-point
numerical integration above muF ~ 6 GeV and 5-14% off below it, because the
interval crosses m_b (and m_c) where the PDF's own alphaS changes nf. 0.3% on J1
is 0.3% on the response, six times what is achievable.

What is used instead: g(L) modelled as a QUADRATIC through alphaS at
L = 0, D/2, D and integrated exactly (5-point Gauss-Legendre, exact for that
polynomial). Three `alphas_run` calls, no loop over a live bound, no division by
D anywhere (the variable is v = L/D), smooth through D = 0. Measured against the
256-point integration: 1e-5 .. 3e-4 on every coefficient.

Second alphaS question, measured and accepted: the grids were evolved with
LHAPDF's variable-nf alphaS, the kernel runs a fixed nf = 5 4-loop solution from
alphaS(mZ) = 0.118. They agree to <= 7e-4 above 6 GeV, 3e-3 at 4, 1.5e-2 at 3,
3.6e-2 at 2. Using the kernel's own costs a factor ~1.3 on the worst low-muF
node and nothing above muF ~ 6.

#### WHAT WAS BUILT

`ad::ad_muf_anl` (a plain, deliberately NOT thread_local global, declared in
`ad_data.hpp` because `ad_context.cpp` does not include `ad_kernel.hpp`),
`muf_evo_coeffs()` in `ad_kernel.hpp`, the correction block in `node_value`,
the four extra kinds in `_fill_conv_one` and the N3LO kernel set in
`make_shared_conv` for mode 3, `n_kinds` following the mode so a mode-3 cache is
self-describing, and `DrellYan.set_muf_analytic(mode)` on the python side.

Two clad traps, both hit and both recorded: a mid-function `return` in the
coefficient helper became a jump that made clang's `VarBypassDetector` recurse
to death (frontend exit 139, "Generating code for declaration
muf_evo_coeffs_pullback") -- replaced by a 0/1 multiplier; and applying the shift
three times per (channel, beam) made the generated derivative large enough to do
the same -- the three coefficient sets are now collapsed into ONE combined
vector before the channel loop, which is exact because the correction is linear
in them.

#### SIGMA-LEVEL, mode 1, on the production cache: 36 of 39 BIT-IDENTICAL

`anlmuf_closure.py` on `cache_260824b` (210 bins, all 10 |Y| x 21 qT,
`--pdf-eig 0`), CorrZ + pdfas_CorrZ, BOTH ARMS FROM ONE CACHE via
`set_muf_analytic(0)` vs `(1)`. Mode 1 needs no extra conv kinds, so a cache
written by a DIFFERENT build with no analytic term loads unchanged -- that is
the whole reason mode 1 exists.

The guards first, because they are the deliverable:
* central analytic/shipped - 1 over 210 bins: **0.000e+00 exactly**
* kappa_F = 2 analytic/shipped - 1: **0.000e+00 exactly**
* arm separation at x2 = 0.35: 8.2e-04, so the nulls below are real nulls

**36 of 39 directions ratio 1.00 to every digit**: all 8 NP lambda, all 10 TNPs,
kappa_R both legs, muF both legs, both joint, both alphaS. The mode-0 arm
reproduces every published number of `260825_transition_muf_coordinate_fix/after`
(2.847e-03 / 1.124e-03 / 3.133e-03, mufup 1.398e-02, kappa_R 7.456e-03 /
4.518e-03, alphaS 2.152e-03 / 2.293e-03), which is the control that this build
IS the shipped model at mode 0.

| direction | shipped max&#124;dev&#124; | mode 1 | ratio | shipped mean | mode 1 | ratio |
|---|---|---|---|---|---|---|
| x2 = 0.35 | 2.847e-03 | 2.273e-03 | **0.80** | 2.205e-04 | 2.043e-04 | 0.93 |
| x2 = 0.75 | 1.124e-03 | 1.657e-03 | 1.47 | 8.587e-05 | 7.749e-05 | **0.90** |
| x1,x3 | 3.133e-03 | 2.812e-03 | **0.90** | 2.143e-04 | 1.633e-04 | **0.76** |

The yield-weighted mean improves on all three (7%, 10%, 24%); `max|dev|` is a
single-cell statistic and improves on two of three. **This is real but modest,
and much smaller than the 2-14x the conv-level measurement shows.** The reason
is that the template-closure residual is not only our interpolation error: the
same cache carries the `node_cval` floor (1-2e-04 per bin, response to x1..x3
identically ZERO, no clean fix in the present rule format) and a model-instance
systematic of up to 1.1e-03 between rel 1e-3 and rel 1e-4. Mode 1 is also the
WEAKEST tier -- chosen because it runs on an existing cache. Do not oversell it.

#### A SEPARATE FINDING, HANDED OVER: the LIVE PARAMETER ROUTE has no muF pair

Another session measured the compressed rule replay against a LIVE parameter
evaluation (`sigma_binned_batch`) and found the three transition directions
disagree by 5.3e-02 / 7.9e-02 / 8.0e-03 while kappa_R agrees to 2.8e-07, and
that the rule agrees with the RUNCARD route to 2.2e-03.

**Root-caused from code, no new run needed.** `ad::GlobalData::var_muf` is set in
exactly one place, `DrellYan::_stage_var_meta` (DrellYanAD.cpp:5146-5156), and
that is called ONLY from the four rule paths -- never from `sigma_binned_batch`.
So on the live parameter route `var_muf == 0` and the whole muF member block in
`node_value` is guarded off: the transition points move the ANALYTIC half of the
response and NOT the convolution half. Those are opposite in sign and the
convolution half is ~9x the net, so what is left is of order the convolution
half itself -- 5-8% at qT 20-28 is exactly the right size. kappa_R is clean
because it holds muF fixed and never enters that block.

It is deliberate and the kernel says so ("moving the logs alone would be worse
than the honest zero it is today"), and there is even a `_refuse_replay` guard
that REFUSES a rule replay moving a transition point with no muF member pair --
but no equivalent guard on `sigma_binned_batch`, which therefore returns a
number instead of an error. **That asymmetry is worth an issue on its own.**

The analytic route needs no members, so it COULD carry the convolution half on
the uncached route and close that gap. Deliberately not done tonight: it would
change behaviour on a path other people are measuring and would confound this
round's A/B. `mfk_live` would have to be hoisted out of the `var_muf` guard,
which is a two-line change.
