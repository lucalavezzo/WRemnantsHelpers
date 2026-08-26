# scetlib_ad — decision record

One line per decision, newest block first. Every entry says WHAT was decided,
WHY, WHAT EVIDENCE backed it, and WHAT WOULD OVERTURN it. This exists so a
review can check the reasoning, not just the outcome. Narrative lives in
`LOGBOOK.md`; this file is only decisions.

Status key: **SETTLED** (evidence in hand) / **PROVISIONAL** (acting on it, could
flip) / **OPEN** (needs Luca) / **SUPERSEDED** (kept for the audit trail).

---

## 2026-08-25 overnight session (autonomous, ~21:30 -> 08:00)

### D-005 — The 260820 card's exclusion regex was OVER-BROAD; card remade — SETTLED
**Why:** its `scetlib_.*` branch silently deleted the 58 PDF eigenvector
nuisances and the 4 mb/mc ones, while its `muF.*` branch matched nothing.
**Evidence:** `bcQuarkMass` 5 -> 1 is the fingerprint; set-diff against the
full-template card `260723_Z_2D_card_davidFix` on the NEW card shows exactly the
intended 15 removed and nothing else.
**Consequence:** any fit run on the 260820 card was missing the PDF and quark-mass
uncertainties entirely. New card:
`260826_Z_2D_card_scetlib_ad/ZMassDilepton_ptll_yll_adexcl/`.

### D-006 — `--excludeNuisances` matches the SYSTEMATIC name, not the nuisance — SETTLED
`re.match` against `addSystematic`'s `name=` (falling back to `histname`), so
`^pdfAlphaS$` would NOT have worked. The transition and FO-scale nuisances are
four outputs of ONE systematic, hence all-or-nothing. Recorded because this is
the single most error-prone step in building the reco card.

### D-007 — D-004 CONFIRMED by fact, not by schedule — SETTLED
PDF eigenvectors stay as templates because every production cache has
`n_eig = 0`, so the model registers no `pdfEig*` and nothing can double count.
**Overturned by:** a production eigenvector cache landing — at which point the
58 `pdf{N}CT18ZSym*` MUST be excluded or they double count.

### D-008 — Reference for reco variations = the histmaker's OWN reco variation
hists, not the card's `hlogk` — SETTLED
**Why:** `hlogk` is symmetrised into SymAvg/SymDiff and would need un-mixing;
the histmaker hists carry the 39 directions individually and unsymmetrised.
**Evidence:** that hist's `central` equals plain `nominal` to 2.9e-14.

### D-009 — RETRACTION: the second central term is MC, not a fold error — SETTLED
First attributed to the gen fold. It is not: `R @ N_gen` reconstructs the
histmaker nominal up to a nearly flat -7.6e-4 (reco events with gen |Y| > 2.5,
dropped by the gen grid), so the central carries essentially no fold
approximation. The term is the corrected-MC gen spectrum against the correction
file. Recorded as a retraction because it was nearly published.

### D-018 — TWO ASYMMETRIES BETWEEN CARD AND MODEL — OPEN (needs Luca)
1. The card's `resumFOScaleZ` is the kappa_R envelope restricted to **qT > 20**,
   while the model's `resumScaleMuR` is **all-qT**. The model is BROADER below 20.
2. **`resumScaleMuF` has no card counterpart at all** under `--resumUnc tnp`, so
   floating it ADDS an uncertainty the template analysis never carried.
Neither is a bug; both are choices about what the analysis's uncertainty should
be, and they change the quoted sigma(alpha_s). Not relitigated by the agent.



Luca is away until 08:00 and asked for maximum progress plus a careful record of
every decision. Three agents live at handover: five-knot muF stencil, `n_train`
study, reco-2D closure.

### D-001 — Launch the full 62-member PDF cache once `n_train` is settled — PROVISIONAL
**Why:** Luca: "gate the launch of the full PDF members cache on that result."
That is explicit authorisation to launch AFTER the n_train answer, not before.
**Evidence:** eigenvector path validated at ~1e-6 against templates on
|Y|<0.3, qT[20,28] (`260825_scetlib_ad_eigenvectors`); build cost 9-15 h.
**Overturned by:** an n_train answer that implies a different build parameter, or
a five-knot decision that would change the member set (five knots CHANGES the
muF members, so a cache built at three knots would need rebuilding — see D-002).

### D-002 — Do NOT let the five-knot work block the PDF cache build — PROVISIONAL
**Why:** they touch different member groups. The PDF cache's 58 eigenvector
members are unaffected by the muF stencil; only the 2 muF members would change.
Rebuilding 2 of 62 members is ~1 h, against 9-15 h for the whole cache.
**Risk accepted:** if five knots ships, the muF members must be rebuilt and
merged. The member merge within a single build is byte-identical, but members
from INDEPENDENT builds are unmergeable (builder not reproducible), so this may
in practice mean a full rebuild. Flagged for Luca rather than assumed away.

### D-003 — Reco closure runs as ONE agent, not two — SETTLED
**Why:** central closure and variation closure share a large, error-prone setup
(response matrix, gen fold, card conventions, the three known traps). Two agents
would independently rediscover the same traps.
**Revisit:** once the card exists and the setup is proven, the variation work is
parallelisable and should be split.

### D-004 — PDF eigenvectors stay as TEMPLATES in the reco card for now — PROVISIONAL
**Why:** the model does not yet provide them continuously in a production cache,
so excluding them from the card would silently delete a real uncertainty.
**Overturned by:** the full eigenvector cache landing and validating on the full
grid. Delegated to the reco agent to confirm and justify explicitly.

---

## 2026-08-25 daytime — decisions already taken

### D-010 — Theory corrections stay applied IN the histmaker — SETTLED (Luca)
The param model supplies only the RATIO for variations. Work in the other
direction was deleted (`compare_cards.py`).

### D-011 — Fix the transitions regardless of alpha_s impact — SETTLED (Luca)
Overruled an impact-based deprioritisation. **Vindicated by measurement:** the
0.002-0.025 sigma scoring was CIRCULAR — measured on the build where the muF
interpolation the transitions route through was wrong, which made them look
harmless. Patched, the transition group carries ~3x more alpha_s.

### D-012 — Leave the non-singular qT cutoff mismatch alone — SETTLED (Luca)
Production corrections zero their non-singular below 1.0 GeV, we cut at 0.1.
Affects only qT [0,1]. Aligning is one runcard line + an 83-min rebuild; not
worth it now. Report that bin separately, never fold into a headline.

### D-013 — Never split PDF members across processes — SETTLED
The builder is not reproducible: four identical-configuration builds gave
357/359/359/371 nodes/bin, structure differing in 9 of 10 bins. A cross-build
member merge is invalid and would be SILENTLY wrong if counts coincided. Split
BINS instead (validated exact, 0.000e+00 in value and Jacobian).

### D-014 — No knot RE-SPACING; the proposal is MORE knots — SETTLED
f=sqrt2 improves the transitions ~4x but kappa_F = 0.5 and 2 stop being exact
samples and muF degrades 150-180x. Five samples (1/2, 1/sqrt2, 1, sqrt2, 2)
keep 0.5 and 2 exact. **Supersedes** the earlier "no knot feature is justified",
which was measured with the wrong member coordinate.

### D-015 — `resumTransition1/3` stay frozen; `resumTransition2` floats — SETTLED
Physics choice: the analysis varies only the central transition point.
`resumTransition2` left DEFAULT_FROZEN once its derivative was fixed.

### D-016 — `tnp_b_qqDS` cannot float for the Z — SETTLED (measured)
Its Jacobian column is EXACTLY 0.0 (every other column 7e-6..1.0 of the max);
it scales a channel that does not contribute. The model correctly refuses it as
singular. So `fit_params=all` is 18 parameters, not 19.

### D-017 — Declared priors are unphysically wide — OPEN
Drawing truth from them gives a NEGATIVE cross section in 63% of draws (up to 81
of 210 bins). `delta_lambda2`'s prior is 0.5 against a postfit constraint of
0.0065 — 80x wider than the data allows. Toy ensembles therefore use rabbit's
own machinery. **Needs Luca before the priors are used quantitatively.**

---

## Reco 2D closure (agent, 2026-08-25 night)

# Decisions — reco-level 2D (ptll, yll) closure of the scetlib_ad param model

Session: overnight 2026-08-25/26. Agent: reco-closure workstream.
Staged for folding into `studies/scetlib-ad-param-model/DECISIONS.md`.
(D-004, PDF eigenvectors stay as templates, was taken by the coordinator; it is
confirmed with evidence in D-R07 below.)

---

## D-R01 — Reference histmaker: `260723_Z_histmaker_davidFix`, NOT `260820_Z_histmaker`

**Decided.** The new card is built from
`/ceph/.../260723_Z_histmaker_davidFix/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5`.

**Why.** Three reasons, in order of force:
1. The settled configuration (logbook 2026-08-25) is *theory corrections stay
   applied IN the histmaker*. `260820_Z_histmaker/mz_dilepton_maxFiles_m1.hdf5`
   is the `--theoryCorrAltOnly` run — its central weight carries NO SCETlib
   correction — so it is the histmaker of the ABANDONED route. Using it would
   silently revive the deleted configuration.
2. Both production caches (`cache_260824b`, `cache_260825_p4`) were built with
   `prepare_cache_for_card.py --card .../260820_Z_2D_card_scetlib_ad/ZMassDilepton_ptll_yll_realdata/ZMassDilepton.hdf5`,
   and THAT card was built from the 260723_davidFix histmaker. Keeping the same
   histmaker keeps the gen grid (21 qT x 10 |Y| = 210 bins) bit-identical, so no
   cache rebuild is needed.
3. The template card used as the variation reference
   (`260723_Z_2D_card_davidFix`) is built from the same histmaker, so the model
   card and the reference card differ ONLY by the exclusion regex.

**Evidence.** `meta_info.command` of both 260820 cards (dumped 2026-08-25):
the `realdata` one reads `-i .../260723_Z_histmaker_davidFix/...Corr_maxFiles_m1.hdf5`;
the `theoryCorrAltOnly` one reads `-i .../260820_Z_histmaker/mz_dilepton_maxFiles_m1.hdf5`
plus `--resumUnc none`.

**What would overturn it.** A decision to move the correction out of the
histmaker (explicitly reopened by Luca), or a gen-binning change that forces a
cache rebuild anyway.

---

## D-R02 — `--excludeNuisances` matches the *systematic* name, not the nuisance name

**Decided.** The exclusion regex is written against the `name=`/`histname`
argument of `Datagroups.addSystematic`, because that is what
`Datagroups.isExcludedNuisance` is called on
(`wremnants/postprocessing/datagroups/datagroups.py:1420` — `if self.isExcludedNuisance(name): return`,
where `name` falls back to `histname`), and the match is `re.match`
(start-anchored), not `re.search`.

**Consequence, and it is the single biggest trap in this task.** The card-level
names one sees in `hsysts` are *outputs* of a systematic and cannot all be
targeted directly. In particular:

* `resumTransitionZSymAvg/SymDiff` and `resumFOScaleZSymAvg/SymDiff` are FOUR
  nuisances produced by ONE `addSystematic` whose name is
  `resumTransitionFOScaleZ` (`rabbit_theory_helper.py:1287`). They are
  all-or-nothing: no regex can drop the transition and keep the FO scale.
* The alphaS nuisance is called `pdfAlphaS` in the card but its systematic is
  named by its histname,
  `scetlib_dyturbo_..._CT18Z_N3p0LL_N2LO_pdfas_Corr[ByHelicity]`
  (`rabbit_theory_helper.py:1236`, `addSystematic(**as_args)` with no `name=`).
  A regex `^pdfAlphaS$` would NOT exclude it.

**Evidence.** Source reading above, plus the 260820 card: its regex
`^(.*scetlibNP.*|pdf.*|resumTNP_.*|resumTrans.*|muF.*|resum.*|scetlib_.*)$`
left `hnoiidxs` EMPTY and no `pdf*` nuisance in `hsysts` — i.e. it was the
`scetlib_.*` branch, not `pdf.*`, that removed alphaS, and the same branch also
removed the 58 CT18Z eigenvectors and the MSHT20 mb/mc-range nuisances.

**What would overturn it.** A change to `isExcludedNuisance` to match final
nuisance names.

---

## D-R03 — The 260820 exclusion list is REJECTED as over-broad; a narrow one replaces it

**Decided.** Do not reuse
`^(.*scetlibNP.*|pdf.*|resumTNP_.*|resumTrans.*|muF.*|resum.*|scetlib_.*)$`.

**Why.** Measured against the full-template card
(`260723_Z_2D_card_davidFix`, 3746 nuisances) the 260820 regex silently deletes
real uncertainties the model does not provide:

| dropped by 260820 | n | provided by the model? |
|---|---|---|
| `pdf{1..29}CT18ZSym{Avg,Diff}` (CT18Z Hessian eigenvectors) | 58 | NO — cache has `n_eig = 0` |
| `pdfMSHT20mbrangeSym{Avg,Diff}`, `pdfMSHT20mcrangeSym{Avg,Diff}` | 4 | NO — no m_b/m_c parameter exists |

`bcQuarkMass` went from 5 members (template card) to 1 (`mb_up` only) in the
260820 card — that is the visible fingerprint of the over-broad cut.
Also `muF.*` in that regex matches NOTHING (there is no card systematic whose
name starts with `muF`), which is harmless but misleading.

**What would overturn it.** A cache with `n_eig = 29` and a validated eigenvector
response; then `pdf{N}CT18Z` joins the exclusion list.

---

## D-R04 — The exclusion list (the deliverable table)

Regex used:

```
--excludeNuisances '^(resumTNP|scetlibNP|resumScaleZ|resumFOScaleZ|resumTransitionFOScale|scetlib_dyturbo.*pdfas.*)'
```

(start-anchored `re.match`, so no trailing `.*` is needed)

| card systematic (`addSystematic` name) | card nuisances it produces | n | EXCLUDED / KEPT | reason |
|---|---|---|---|---|
| `scetlib_dyturbo_..._pdfas_Corr[ByHelicity]` | `pdfAlphaS` (NOI, unconstrained) | 1 | **EXCLUDED** | model parameter `alphaS`, continuous, PHYSICAL units, built on the same CT18Z `as_0116`/`as_0120` member pair (cache `has_as=1`, central 0.1180 +- 0.0020) |
| `resumTNP` | `resumTNP_{gamma_cusp,gamma_mu_q,gamma_nu,s,h_qqV,b_qqV,b_qqbarV,b_qqS,b_qqDS,b_qg}` | 10 | **EXCLUDED** | model parameters `resumTNP_*`, one-for-one, same names, sigma = 1 |
| `resumTransitionFOScaleZ` | `resumTransitionZSym{Avg,Diff}` | 2 | **EXCLUDED** | model parameter `resumTransition2` (quad reparam through 0.35 / 0.6 / 0.75) |
| `resumTransitionFOScaleZ` (same call) | `resumFOScaleZSym{Avg,Diff}` | 2 | **EXCLUDED** | model parameter `resumScaleMuR` (log reparam, theta = +-1 -> kappa_R = 2 / 0.5). See caveat C-1. |
| `scetlibNP` | (none — `--npUnc none`) | 0 | **EXCLUDED** (belt and braces) | model parameters `lambda2, lambda4, delta_lambda2, lambda_inf, lambda2_nu, lambda4_nu, lambda_inf_nu, b0_over_bmax_nu` |
| `resumScaleZ`, `resumFOScaleZ` (the `--resumUnc scale` route) | (none — `--resumUnc tnp`) | 0 | **EXCLUDED** (belt and braces) | would be the muB/nuB/muS/nuS envelope + kappa/muF pair; superseded by the model |
| `scetlib_dyturbo_..._pdfvars_Corr[ByHelicity]` | `pdf{1..29}CT18ZSym{Avg,Diff}` | 58 | **KEPT** | model provides NOTHING here: production caches have `n_eig = 0`. Excluding would delete the PDF uncertainty outright. Confirms D-004. |
| `scetlib_dyturbo_..._MSHT20m{b,c}range_..._pdfvars_Corr` | `pdfMSHT20m{b,c}rangeSym{Avg,Diff}` | 4 | **KEPT** | m_b / m_c mass-range uncertainty; the model has no quark-mass parameter |
| (MiNNLO) | `mb_up` | 1 | **KEPT** | same |
| `qcdScaleByHelicity` | `QCDscaleZ*helicity_*_Sym{Avg,Diff}` | 176 | **KEPT** | MiNNLO fixed-order / angular-coefficient scale variations. The model varies the SCETlib resummed+matched prediction only; the MiNNLO helicity decomposition that carries the correction to reco is untouched by it. |
| `helicity_shower_kt` | `pythia_shower_kt` | 1 | **KEPT** | parton-shower k_T, not a SCETlib parameter |
| EW block | `weak_{default,aem,ps}`, `horaceqedew_FSR_Corr0`, `horacelophotosmecoffew_FSR_Corr0`, `pythiaew_ISR_Corr0` | 6 | **KEPT** | electroweak, orthogonal to the model |
| — | `massShiftZ2p1MeV`, `widthZ`, `sin2thetaZ` | 3 | **KEPT** | Z lineshape/couplings, not SCETlib |
| — | everything experimental (`effStat*`, `effSyst*`, `Scale_correction*`, `Resolution_correction*`, `ScaleClos*`, `pixel_multiplicity*`, `CMS_prefire*`, `lumi`, `CMS_background`, `CMS_PhotonInduced`) | ~3480 | **KEPT** | detector, untouched |

Caveat **C-1 — the scale sector is NOT a like-for-like swap, and this must not be
read as one.** The card's `resumFOScaleZ` is the envelope over
{central, `kappaFO0.5-kappaf2.`, `kappaFO2.-kappaf0.5`} **restricted to qT > 20 GeV**
(`wremnants/production/theory_corrections.py:757,795` — `renorm_scale_pt20_envelope`,
`slice_axis="qT", slice_val=20.0`), deliberately, "to neglect the part at low pt
which should be redundant with the TNPs". The model's `resumScaleMuR` is the full
kappa_R response at ALL qT. Direction-for-direction the model is BROADER below
qT 20.

Caveat **C-2 — `resumScaleMuF` has no card counterpart at all.** With
`--resumUnc tnp` the card carries no muF nuisance whatsoever (verified: zero
matches for `muf` in the 3746 names of the template card). Floating the model's
`resumScaleMuF` therefore ADDS an uncertainty the template analysis never had; it
is not double counting, it is a new term. Whether it should float is a physics
decision for Luca, not a card decision. (It is also why the 260820 regex's
`muF.*` branch matched nothing.)

---

## D-R05 — `--noi alphaS` is kept, and is inert

**Decided.** Keep `--noi alphaS` on the setupRabbit command even though the
alphaS systematic is excluded.

**Why.** It makes the new card differ from the card the caches were built
against (`260820_.../ZMassDilepton_ptll_yll_realdata`) in the exclusion regex and
nothing else — a clean single-variable change. `--noi alphaS` only affects the
alphaS systematic (scale 0.002 instead of 0.0015, `noConstraint=True`,
`symmetrize="average"`), which is excluded, so it has no effect on the card.

**Evidence.** The 260820 card carries `--noi alphaS` AND excludes the alphaS
systematic, and its `hnoiidxs` is an empty array — no crash, no NOI.

**What would overturn it.** Nothing physical; drop the flag for tidiness whenever
the card is next remade.

---

## D-R06 — `--npUnc none` retained

**Decided.** Keep `--npUnc none`, as both prior cards do. The eight NP lambdas
are model parameters. The regex entry `scetlibNP` is redundant with it and is
kept only so the card is safe if someone changes `--npUnc`.

---

## D-R07 — CONFIRMING D-004: PDF eigenvectors stay as templates

**Confirmed, with evidence, not merely accepted.**

The operative fact is not "the eigenvectors are still being validated" but
something stronger and checkable: **the production caches register no eigenvector
parameters at all.** `ScetlibADXsec.cache_param_names(cache_260825_p4)` returns
24 names and `n_eig = 0` in the npz; there is no `pdfEig*` among them. So there
is literally nothing in the model that could double count against
`pdf{N}CT18ZSym*`, and excluding them would delete the single largest theory
uncertainty on alpha_s with no replacement.

The alphaS/eigenvector split is clean, which is what makes this safe: in CT18Z
the alpha_s variation is a separate member pair (`as_0116`/`as_0120`), not one of
the 29 Hessian eigenvectors — the card shows `pdfCT18Z` with 59 members against
`pdfCT18ZNoAlphaS` with 58. So excluding `pdfAlphaS` while keeping all 58
eigenvector nuisances double counts nothing and drops nothing.

**What would overturn it.** A cache built with `--pdf-eig 29` whose eigenvector
response is validated across the full grid (currently ~1e-6 in one window only).
At that point `scetlib_dyturbo_..._pdfvars_Corr` joins the exclusion list and
`pdfEig{0..28}` float instead.

---

## D-R08 — SCETlib build: the PATCHED one (92f1299, MR !8)

**Decided.** All model evaluations in this workstream use
`SCETLIB_BUILD=<scratch>/scetlib_build_92f1299`, a byte-identical snapshot
(`md5(libscet-qT.so) = e6a7faf186b4fbf11974ca6fc65b924b`) of
`/work/submit/lavezzo/alphaS/scetlib-trans/build-trans`, whose worktree is clean
at `92f1299 qT/ad: the muF members are three muF samples, so interpolate in muF`.

**Why.** (1) The 2026-08-25 Asimov A/B shows the fix materially rotates the
(muR, muF, transition) block against alpha_s — two correlation sign flips and a
+78% sigma(resumScaleMuR) — so any number produced on the unpatched build is
already known to be contaminated. (2) It changes no stored quantity, so the
existing caches remain valid (`92f1299` is `bb2e7cb` plus ONE header,
`include/scetlib/qT/ad/ad_kernel.hpp`; `py/` is identical, so mixing the shared
tree's `py/` with this build's `lib/` is safe).
(3) The snapshot is taken so that another agent rebuilding `build-trans` cannot
change my results mid-run.

**What would overturn it.** MR !8 being revised before merge.

---

## D-R09 — Variation reference: the histmaker's OWN reco variation hists

**Decided.** For the reco variation closure the reference is
`nominal_ptll_yll_scetlib_dyturbo_..._CT18Z_N3p0LL_N2LO_Corr` (and its
`_pdfas_Corr` sibling for the alpha_s pair) read from the 260723_davidFix
histmaker: reference response = `H_reco[var] / H_reco[central]`, per (ptll, yll)
bin.

**Why, rather than the template card's `hlogk`.** The card's theory nuisances are
symmetrised into `SymAvg`/`SymDiff` combinations and rescaled (alphaS by
0.002/0.002, TNPs by `--scaleTNP`), so a card-level logk column is a LINEAR
COMBINATION of two directions, not a direction. Comparing per-direction model
responses against it would require undoing the symmetrisation, adding a step that
can itself be wrong. The histmaker `vars` axis carries the 39 directions
individually and unsymmetrised, exactly as the gen-level `validate_variations.py`
reference (`Corr[var]/Corr[central]`) does — so the reco table is reported in the
same terms as the gen table, which is what was asked for.

**What it costs.** The reference fold is per-event (each event weighted by the
correction ratio at its own gen qT, y), while the model folds with the
bin-averaged response matrix R. The residual therefore contains a genuine
"R-granularity" term. It is second order in the ratio (R cancels to first order)
and is bounded by the central closure, where the same effect appears at first
order.

**What would overturn it.** Finding that the histmaker's `vars` hist is stored
after helicity smoothing while the model is not, in which case the smoothing
would have to be applied to the model side too.

---

## D-R10 — RETRACTION, made before publication: the second term is NOT a fold error

**What I first wrote, and why it was wrong.** The first version of the central
decomposition labelled its second term "FOLD" and described it as "our
bin-averaged R against the histmaker's per-event reweighting". That is wrong, and
the error is worth recording because it is exactly the kind of confident
misattribution this study has published before.

**The identity that settles it.** The datacard stores `R = R_raw / N_gen`, and
the histmaker's reco nominal is `sum_g R_raw(b, g)`. Therefore

    R @ N_gen  ==  histmaker nominal   up to events with no gen column

Measured: a nearly FLAT `-7.6e-4` (per-bin max `2.3e-3`, range `-6.3e-4` at
central rapidity to `-1.2e-3` at `|yll| > 1.8`). That deficit is the reco-selected
events whose GEN `|Y|` exceeds 2.5 -- the card's gen grid stops at 2.5 and the
`absYVGen` overflow is dropped. Because it is nearly constant, the shape
comparison divides it out, and the CENTRAL prediction carries **essentially no
fold approximation**. Checked numerically at the top of both scripts, not
assumed. (I first wrote "~1e-16" in the script docstring before measuring it;
that was corrected before publication.)

**What the term actually is.** `(R @ sigma_CorrZ) / nominal` measures whether the
CORRECTED MC's own gen spectrum `N_gen(g)` has the same shape as the correction
file's `sigma(g)` on this 210-bin gen grid. It is nonzero because the histmaker
applies the correction through helicity moments on a MiNNLO sample (not the same
operation as multiplying a binned unpolarised spectrum) and because MiNNLO's
residual (Q, y, qT) correlation survives inside a gen bin. Relabelled **MC**.

**Where granularity genuinely lives: the VARIATIONS.** There the reference
reweights per event inside a gen bin while the model multiplies the whole bin, so
a real granularity term exists. The variation table therefore splits three ways
(D-R11) instead of two.

**What would overturn it.** The identity check failing (it does not: see the
number quoted in `00_README.txt`).

---

## D-R11 — The variation residual is reported as a three-term split

**Decided.** Per direction the residual is factorised exactly as

    r_model / r_ref = (r_model / r_A) x (r_A / r_B) x (r_B / r_ref)
                       \__ CALC __/     \__ WGT __/    \__ GRAIN __/

with `r_A` the correction file's gen response folded with the MODEL's anchor
spectrum as the gen weight, and `r_B` the same response folded with the MC's
`N_gen`.

* **CALC** — the model's gen-level response error. The reco image of the
  gen-level table. Fixed in SCETlib / the cache.
* **WGT** — the same response folded against two different gen weights. Nonzero
  only where the model's gen spectrum and the MC's differ in shape INSIDE a reco
  bin.
* **GRAIN** — bin-averaged response against per-event. Zero iff the correction
  ratio is constant inside every gen bin. Pure gen-binning granularity, no model
  physics. **It is a cost the discrete templates do not pay**, because those are
  built by the same per-event reweighting the reference uses.

**Why it matters and is not bookkeeping.** A single total says nothing about
whether the calculation or the binning is at fault, and the two are fixed by
different work (a SCETlib change versus a finer gen grid and a new cache).
Measured: once the qT [0,1] convention is aligned, GRAIN exceeds CALC in 32 of
39 directions. The limiting factor at reco level is the gen binning, not the
calculation.

**What would overturn it.** A card with a finer gen grid whose GRAIN term does
not fall.

---

## D-R12 — The qT [0,1] convention is reported separately, never folded into a headline

**Decided.** Every variation table is produced twice: as shipped, and with
`--fix-genbin0`, which replaces the model's gen qT [0,1] response by the
correction file's before folding. The difference between the two IS that bin's
contribution, so it is quantified rather than argued about.

**Why not just exclude the bin.** At reco level the gen qT [0,1] bin is smeared
across many reco ptll bins, so there is no reco bin to exclude. Substituting the
reference's response in that one gen row is the only clean way to isolate it.

**Evidence it is the right knob.** In the central closure the reco ptll [0,1] bin
is the single worst bin and its residual is 100% CALC (-1.55e-2) with MC
consistent with zero (-5.6e-5) -- the signature of a gen-level calculation
convention, not of anything downstream.


---

## D-R13 — ROOT CAUSE: the card's last gen bin is an OVERFLOW, not [44, 100]

**Found, and it explains the single largest central residual outside qT [0,1].**

The reco `ptll [37, 44]` bin closes at only `-1.03e-2`, and the decomposition
puts 100 % of that in the MC term (`CALC = +1.7e-4`). Cause:

* The histmaker's gen `ptVGen` axis is
  `[0, 1, 2, ..., 28, 33, 44]` with `overflow=True` -- verified on `prefsr`,
  `prefsr_full` and `nominal_prefsr_yieldsUnfolding`. Every gen histogram in the
  file stops at 44.
* The datacard's `edges__ptVGen` nevertheless declares 21 bins ending
  `..., 33, 44, 100`. The bin labelled **[44, 100] IS the overflow** and contains
  every event with gen `qT > 44` -- 11.6 % of `N_gen`.
* The correction file's own `qT` axis stops at **100 GeV** (checked: last edges
  70, 80, 90, 100), so the model can only fill 44-100.
* Measured consequence: `sigma_CorrZ / N_gen` on the gen grid is **1.020 +- 0.002
  in all 20 bins with qT < 44** (flat in `|Y|` to 0.4 %) and **0.847 in the
  overflow bin** -- a 15.3 % deficit, flat in `|Y|` (0.8425 at `|Y| < 0.15`,
  0.8586 at `|Y| > 1.8`).

**Consequence for the fit, stated plainly.** The model under-fills one gen bin by
15 %, and that bin feeds the top reco `ptll` bin. It does NOT bias the fit at
first order, because the model supplies the RATIO to its own anchor and the same
deficit sits in numerator and denominator. What it does mean is that the
*response* in `ptll [37, 44]` is computed on 44-100 GeV only while the data bin
also contains `qT > 100`.

**What I could NOT separate, and the experiment that would.** Whether the 15.3 %
is entirely the `qT > 100` tail, or partly the correction not being applied above
100 GeV in the histmaker. Every gen histogram in this histmaker file stops at 44
with an overflow, so the question cannot be answered from it. The experiment:
rerun the histmaker with a `ptVGen` axis that resolves `qT > 44` explicitly (e.g.
`..., 44, 100, 13000`) and re-measure `sigma_CorrZ / N_gen` bin by bin.

**What would overturn it.** A gen axis that genuinely ends at 100 with the
overflow separate; then the ratio in that bin should return to ~1.02.

---

## D-R14 — Reported metrics: absolute AND relative to each direction's response

**Decided.** Every variation row carries both `TOTAL yield-weighted mean|dev|`
(absolute, comparable to the gen-level table) and `rel = TOTAL / (this
direction's own yield-weighted mean |response - 1|)`.

**Why.** A residual of 1e-3 is negligible on a 3 % response and serious on a
0.06 % one. Reporting only the absolute number would have made the transition
points look like the best-behaved directions in the table when they are the
worst: absolute 2.5-4.6e-3 (middle of the pack) but 11-19 % of their own
response (the largest by a factor 3).

**One trap in the column.** `resumTNP_b_qqDS` has an identically zero response
for the Z, so `rel` is 0/0 and prints as 17.1. It is flagged in the README; do
not read it as a failure.
