# scetlib_ad — decision record

One line per decision, newest block first. Every entry says WHAT was decided,
WHY, WHAT EVIDENCE backed it, and WHAT WOULD OVERTURN it. This exists so a
review can check the reasoning, not just the outcome. Narrative lives in
`LOGBOOK.md`; this file is only decisions.

Status key: **SETTLED** (evidence in hand) / **PROVISIONAL** (acting on it, could
flip) / **OPEN** (needs Luca) / **SUPERSEDED** (kept for the audit trail).

---

## 2026-08-25 overnight session (autonomous, ~21:30 -> 08:00)

### D-019 — DO NOT merge five knots to fix the transitions — SETTLED (measured)
**Why:** it makes the transition closure against CorrZ WORSE, and the mechanism
is now measured rather than argued. At the FINITE variation the templates carry,
the per-node muF displacement D reaches **1.15 x ln f** (and 1.74 x ln f for the
x1,x3 leg) -- i.e. OUTSIDE kappa_F = 2. The model is EXTRAPOLATING there, and a
quartic extrapolates worse than a quadratic. More interior knots refine the
interior; the template legs are not in it.
**Evidence:** 80-bin closure, one cache read two ways so node set, rules and
members are bit-identical between arms.
  x2=0.35   2.85e-03 -> 5.37e-03
  x2=0.75   1.12e-03 -> 1.56e-03
  x1,x3     4.22e-03 -> **7.60e-01**
36 of 39 directions are BIT-IDENTICAL, so nothing else degrades.
**Overturned by:** a stencil wide enough to contain D at the template legs -- but
see D-020, the one wide geometry tried is not validated.

### D-020 — RETRACTION: the wide (kappa_F 1/4..4) geometry is NOT a measurement — SETTLED
It was first written up as "measured bad" at 31% of sigma. It fails its own knot
test (kappa_F = 4 must be exact; returns -3.7e+08). Kept behind `muf_nmem = -4`,
labelled UNVALIDATED. Chasing it did find a real bug -- the degeneracy guard was
absolute rather than relative to the node's spread -- and fixing that left the
no-op check and the narrow closure bit-identical, so the narrow numbers stand.

### D-021 — The five-knot work is still valuable, just not for the transitions — SETTLED
At kappa_F = sqrt2, against an exact runcard refill: **2.94e-03 -> 3.60e-05 of
sigma, 82x**. That doubles as the construction check AND reveals that the SHIPPED
model is **0.3% of sigma wrong at half a knot step** -- invisible to every
existing validation, all of which sit AT kappa_F = 0.5/2. Near-anchor derivative
(x2 = 0.55, what a fit uses) improves 2.9x / 33x / 6x in three bins; [24,28] does
not move, an order-independent floor already known to be spacing-independent and
bracketed by node_cval's measured bound.
Branch `muf-five-knots` (`61123f2`) pushed, **no MR opened**.

### D-022 — Next route for the transitions: the analytic d(conv)/d(ln muF) column — PROVISIONAL
**Why it is now better motivated than before:** it is first-order exact in D, so
unlike knots it does not care that D leaves the stencil at exactly the template's
variation size. One column per node instead of two member builds per bin; no
member staging, no re-solved weights.
**Open question it must answer:** whether ONE column suffices where D ~ 1.15 ln f.

### D-023 — Two traps to keep — SETTLED
1. `ScetlibCachedXsecTF.values_and_jacobian` memoises on the parameter vector
   ALONE. A first closure run returned ratio exactly 1.00 for all 39 directions
   -- a perfect and WRONG null. Any A/B between two builds must prove the arms
   are separated before reporting agreement.
2. Any global the kernel reads must NOT be `thread_local`: `_stage_var_meta`
   runs inside the TBB workers.

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

---

## Five-knot muF stencil (agent, 2026-08-25 night)

# Decision log — staged for studies/scetlib-ad-param-model/DECISIONS.md
# Agent: FIVE-KNOT muF STENCIL (transition-point closure vs CorrZ)
# Started 2026-08-25 evening.

## 0. READ THIS FIRST — APPARENT MIS-ROUTED INSTRUCTION (flagged, not silently ignored)

The overnight coordinator message asks this agent to complete the **right-hand
panel of `~/public_html/alphaS/260825_scetlib_ad_eigenvectors/eigenvector_validation.png`
(accuracy vs `n_train`)** and to "report `use n_train = N`" because it gates a
9-15 h 62-member PDF cache build.

**That is not this agent's brief and I have not switched to it.** My brief is:
prototype a five-knot muF stencil in SCETlib and prove or disprove that it
improves the transition-point variations' closure against the production CorrZ
templates. Nothing in it mentions `n_train`, PDF eigenvectors, or the 62-member
build; the two tasks share only the study slug.

I am flagging rather than obeying because:
 * switching would abandon the five-knot deliverable with nothing to show, and
 * an `n_train` answer produced as a by-product of a muF-knot A/B would be
   measured on a 5-10 bin subset cache with `--pdf-eig 0`, i.e. with **zero**
   eigenvector coefficients. `n_train` matters precisely through
   `n_train / n_params` once 29 coefficients are added (logbook, 2026-08-25).
   A number from an `n_eig = 0` cache would not bear on the question at all,
   and quoting it would be worse than saying nothing.

**If the coordinator does want this agent on `n_train`, say so explicitly and I
will stop the knot work.** Otherwise the `n_train` scan needs its own agent with
a cache built at `--pdf-eig > 0`.

The two generic requirements in that message DO apply and are being followed:
this file (one entry per decision, with what would overturn it), and a webdir
with a `00_README.txt` naming figure / reference / build / cache / bin count.

---

## 1. Base commit for the prototype: `near-anchor-knots` (eb60a04), own worktree

**Decided.** New worktree `/work/submit/lavezzo/alphaS/scetlib-5knot`, new branch
`muf-five-knots`, new build dir `build-5knot`. Base = `eb60a04`
= `bb2e7cb` + `92f1299` (muF member COORDINATE fix) + `83cecb2` (settable knot
spacing) + `3a8db11` + the `rule_cvals()` diagnostic.

**Why.** The brief names the coordinate fix a prerequisite, and the knot-spacing
commit already generalised `prof_v_muf` / `Bin_rule::Var::g_v_muf` from "the
Vary leg" to a **log2 exponent** — which is exactly the generalisation five
knots needs (fractional legs +-1/2 are then expressible with no new POD field).
Reimplementing it would have cost a day and would have diverged from the branch
the author already has.

**Evidence.** `git show 83cecb2` and `git show 92f1299` read in full before
writing any code; `git log --graph` confirms eb60a04 contains both.

**Would overturn it.** If the author rejects `92f1299` (MR !8), the five-knot
commit still applies but its measured "before" arm changes.

**Not touched, on purpose:** `scetlib-cms`, `build-fix`, `build-knots`,
`build-trans`, `build-nak`, `build-nakbase`, and every file under WRemnants.

---

## 2. The five-knot stencil needs NO new `ad::GlobalData` field — VERIFIED, not assumed

**Decided.** Implement five knots by (a) redefining `ad::GlobalData::var_muf`
from a FLAG to the COUNT of muF member columns (0, 2 or 4) and (b) fixing the
inner knots at HALF the outer log step, so `var_muf_lnstep` still describes the
whole stencil. No field added, no field widened.

**Why.** `sizeof(ad::GlobalData)` is written into every rule-cache file and
checked on load; any new field refuses every cache on disk. The prior analysis
asserted this was avoidable. It is, and the two ingredients above are how.

**Evidence (measured, not argued).** The 210-bin production cache
`cache_260824b` — written by a DIFFERENT build, with the three-knot stencil —
loads unchanged under the five-knot binary and reproduces the published
three-knot arm on all 39 directions:

| direction | published `after/` arm | five-knot build, 2 knots |
|---|---|---|
| transition x2 = 0.35 | 2.847e-03 | 2.85e-03 |
| transition x2 = 0.75 | 1.124e-03 | 1.12e-03 |
| transition x1,x3 | 3.133e-03 | 3.13e-03 |
| mufup | 1.398e-02 | 1.40e-02 |
| mufdown | 1.979e-03 | 1.98e-03 |
| kappa_R down / up | 7.456e-03 / 4.518e-03 | 7.46e-03 / 4.52e-03 |
| alphaS 0.116 / 0.120 | 2.152e-03 / 2.293e-03 | 2.15e-03 / 2.29e-03 |
| all 8 lambda, all 10 TNPs | — | every one identical to 3 s.f. |

Central cross section identical to 0.000e+00 relative.
Log: `tmp/noop_260824b.log`.

**What would overturn it.** Adding any further field to `ad::GlobalData` (e.g.
storing the inner knot spacing separately instead of fixing it at half a step)
would break every cache on disk and this claim with it.

**Rejected alternative:** a separate `var_muf_lnstep_inner`. Rejected for the
POD-guard reason above; the cost is that the inner knots cannot be moved
independently of the outer ones. That is not a loss for the intended use --
the outer knots are pinned at kappa_F = 1/2, 2 by the production templates.

---

## 3. Half-step members are BUILT by handing `Vary.muf` a spacing of sqrt(f)

**Decided.** An inner member (kappa_F = f^+-1/2) is built by
`set_muf_vary_factor(sqrt(f))` followed by `set_muf_keep_nodes(+-1)`, then
restoring the factor to `f`.

**Why.** `Vary.muf` scales muF by the factor AND divides `muf_min` by the same
factor, and only doing BOTH keeps the large-bT floor at `(muF/Q) muf_min` --
the compensation `Scale_provider.hpp` advertises. Inventing a fractional
`Vary_scale`, or scaling `kappaf` by hand, would move muF without moving the
floor, and the member would then sit somewhere the kernel's own knot formula
cannot reproduce. This way the inner knots are built by exactly the same
mechanism as the outer ones.

**Evidence.** The kernel builds each knot's position from the SAME expression
with `fo_muf` scaled by `f^leg` and the floor divided by `vary*f^leg`; the
member's own `g_v_muf` (a log2 exponent since commit 83cecb2) carries
`leg * ln f / ln 2`, which the AD context turns back into that same factor. The
three-knot no-op above is the check that the two constructions agree where they
overlap.

**What would overturn it.** A measured disagreement between the model at
kappa_F = f^-1/2 and an exact runcard refill at `kappaf = f^-1/2`,
`muf_min /= f^-1/2` (the non-knot reference the 2026-08-25 entry validated at
K = 2 to 9e-16). That test is the next one to run.

---

## 4. The A/B is ONE cache read two ways, not two caches

**Decided.** Added `DrellYan::set_muf_knots_used(n)` -- a documented A/B
instrument that holds the kernel's knot count down to `n`. The BEFORE arm is a
five-knot cache evaluated with `n = 2`; the AFTER arm is the same cache with
`n = 0` (all).

**Why.** Two separately built caches cannot isolate the stencil. The bT node set
is not reproducible between processes (357 / 359 / 371 nodes per bin measured,
logbook 2026-08-25), and the logbook's own reproducibility floor between two
builds of the SAME runcard is 3.1e-05 in sigma but **3.0e-03 in the Jacobian at
a displaced point** -- larger than the transition residual being measured
(1e-03 .. 3e-03 of sigma). With one cache the node set, the rules, the outer
member convolutions and the re-solved weights are bit-identical between arms and
the ONLY difference is the interpolation order.

**Evidence it is faithful.** At `n = 2` the five-knot binary reproduces the
published three-knot numbers on the production cache (decision 2), and in the
live-rule test below the `n = 2` arm reproduces the previously published
three-knot deviations bin by bin.

**Implementation note worth keeping.** The flag is a **global atomic**, not
`thread_local` like `set_rule_replay_mode`: `_stage_var_meta` runs inside the TBB
workers of `_ad_parallel_run`, so a thread-local set on the calling thread would
silently do nothing. That was caught by reading the call site, not by a test --
a test would have shown "no effect" and been read as "five knots changes
nothing".

**What would overturn it.** If `n = 2` on a five-knot cache and a separately
built three-knot cache disagreed by more than the known reproducibility floor,
the clamp would not be a faithful stand-in.

---

## 5. The inner members are CORRECT — proven at kappa_F = sqrt(2), 82x

**The sharp test.** kappa_F = sqrt(2) is a knot of the five-knot stencil and
NOT of the three-knot one, so the five-knot arm must be exact there and the
three-knot arm must not. Reference: a runcard refill with `kappaf = sqrt2` AND
`muf_min /= sqrt2` (the non-knot reference the 2026-08-25 logbook validated at
K = 2 to 9e-16). |Y| [0, 0.15], live rules, `n_train = 9`,
`target_precision_rel = 1e-4`, both arms from the SAME build and the SAME
member convolutions.

```
  qT bin      true resp    dev 3-knot    dev 5-knot     (dev = model/runcard - 1,
 [  8,  9]   -4.49e-05     +6.04e-05     -8.43e-06       as a fraction of sigma)
 [ 18, 20]   +3.40e-03     +1.44e-03     -1.83e-05
 [ 20, 24]   +7.81e-04     +2.94e-03     -2.53e-05
 [ 24, 28]   +2.16e-03     -1.00e-03     -2.46e-05
 [ 28, 33]   +1.22e-03     -1.46e-04     -3.02e-05
 [ 33, 44]   +1.30e-03     +3.13e-06     -3.60e-05
  max|dev|                  2.944e-03     3.597e-05      82x
```

**Read it as two things.**
1. A CONSTRUCTION CHECK: the half-step members land exactly where the kernel's
   knot formula puts them, floor compensation included. The residual 3.6e-05 is
   flat in qT and is the parameter-route / runcard-route reproducibility floor,
   not an interpolation error. Decision 3 is confirmed.
2. A RESULT IN ITS OWN RIGHT: the shipped model is **0.3% of sigma wrong at
   kappa_F = sqrt(2)** and no validation we own could see it, because every muF
   check sits AT kappa_F = 0.5 or 2 where a quadratic returns the stored member
   bit for bit. Five knots removes that.

**What would overturn it.** Nothing in the same measurement; a different
reference construction (e.g. forgetting to scale `muf_min`) would.

---

## 6. The five-knot stencil does NOT fix the transitions at the TEMPLATE variation, and the geometry says why

**Measured**, x2 = 0.35 (the FINITE leg the CorrZ templates carry), same
process, same rules, model against an exact runcard refill:

```
  qT bin      true resp     dev 3-knot   % of resp    dev 5-knot   % of resp
 [ 18, 20]   -4.136e-04    +1.099e-04     -26.6%     -1.081e-04     +26.1%   (*)
 [ 20, 24]   -3.075e-03    +9.801e-04     -31.9%     +3.493e-04     -11.4%
 [ 24, 28]   -7.840e-03    -8.539e-04     +10.9%     +6.775e-04      -8.6%
 [ 28, 33]   -1.822e-02    -2.151e-03     +11.8%     +3.144e-04      -1.7%
 [ 33, 44]   -3.301e-02    -3.040e-04      +0.9%     +3.820e-03     -11.6%
  max|dev|                  2.151e-03                 3.820e-03
```
(*) [18,20]'s true response is 4e-04, at the node-ladder target -- not usable.

Three of five bins improve (by 2.8x, 1.3x, 7x), [33,44] gets **12x worse**, and
the worst bin over the set goes 2.15e-03 -> 3.82e-03. **Net: worse.**

**The 3-knot column reproduces the previously published numbers**
(-26.6 / -29.2 / +10.9 / +11.8 / +1.5 % in the 2026-08-25 webdir README) bin by
bin, which is the check that the `knots_used = 2` clamp is faithful on a live
build as well as on a cache.

**WHY -- and this is the finding, not the number.** `fiveknot_stencil_geometry.py`
computes, from SCETlib's own scale formulas and with no calculation run, the
per-node displacement D = ln[muF(x2 = 0.35)/muF(anchor)] against the knot
positions. In units of ln f = ln 2:

```
  qT     D/ln f over bT = 0.1 .. 5        where the model is evaluating
  19       0.004 .. 0.033                 deep INSIDE the inner knots
  22       0.085 .. 0.510                 inner..outer, extrapolating at bT >= 2
  26       0.300 .. 0.991                 at the OUTER knot by bT 0.8
  30       0.536 .. 1.190                 EXTRAPOLATING from bT 0.5 up
  38       0.759 .. 1.154                 EXTRAPOLATING at essentially every node
  60       0.241 .. 0.282                 back inside
```

At the template's own variation size the transition-induced shift **reaches and
exceeds the outer knot** for qT ~ 26-44. There the model is not interpolating
between knots, it is EXTRAPOLATING past kappa_F = 2 -- and a quartic
extrapolates worse than a quadratic, which is exactly the sign and the location
of the [33,44] degradation.

**So "more knots" is the right medicine for the wrong ailment at this variation
size.** Interior knots refine the interior; the finite template leg is outside.

**What would overturn it.** A five-knot arm that improved [33,44] -- it does
not -- or a demonstration that the dominant bT nodes at qT 38 are the small-bT
ones where D/ln f < 1 (the geometry says D/ln f = 0.76 already at bT = 0.1).

**The prediction this makes, and which is being tested next:** at the
NEAR-ANCHOR variation (x2 = 0.55, ~12x smaller, what a FIT actually uses) D is
~12x smaller, so every node is deep inside the inner knots and five knots must
be uniformly better. If that comes out, the honest summary is "five knots helps
the fit derivative and kappa_F between knots, and does not help the template
closure", which is a different -- and more useful -- statement than either
"it works" or "it does not".

---

## 7. NEAR-ANCHOR (the regime a FIT uses): five knots nearly removes the interpolation error, and EXPOSES a separate floor

x2 = 0.55, ~12x smaller than the template leg. Same process, same rules, same
runcard reference; error as a fraction of the TRUE response.

```
  qT bin      true resp    3-knot    5-knot      gain
 [ 18, 20]   -3.47e-05    -36.5%     -4.2%       (true resp 3e-05: NOT USABLE)
 [ 20, 24]   -2.70e-04    -40.9%    -14.3%       2.9x
 [ 24, 28]   -6.60e-04    +27.1%    +28.2%       1.0x  <-- does not move
 [ 28, 33]   -1.61e-03     +8.4%     +0.3%       33x
 [ 33, 44]   -4.01e-03     +3.6%     +0.6%       6x
  max|dev| of sigma        1.79e-04  1.86e-04
```

**Three of four usable bins fall to <= 0.6% .. 14% of their own response**; one
does not move at all. `max|dev|` is therefore FLAT, and quoting only that number
would hide both halves of the result.

**[24,28] is an order-INDEPENDENT floor, and it was predicted.** The 2026-08-25
webdir README already measured a "spacing-independent floor of about 1-2e-04 per
bin" at exactly this bin and this variation (+27.1% at f = 2, +26.3% at
f = sqrt2). Five knots reproduces it (+28.2%) at 1.86e-04 of sigma. So it is not
the interpolation ORDER and not the knot SPACING. The two named candidates, from
the same README, are:
  * `node_cval`, the rule's bin-level constant, which has no bT node and so
    interpolates on the GLOBAL kappa_F label -- its response to x1..x3 is
    identically ZERO. Its measured upper bound at qT [24,28], |Y| < 0.5, is
    max|dc|/sigma = 2.3e-04 .. 3.2e-04, which BRACKETS the 1.86e-04 left over.
  * the reference's own node-ladder target, 1e-04 relative.
**The experiment that separates them:** zero the `node_cval` member
interpolation and re-measure this bin. If the 1.86e-04 moves, it is c_val; if it
does not, it is the reference. Neither has been done -- this is named as the
next measurement, not as a conclusion.

**What would overturn the rest of it.** A finer reference (target_precision_rel
below 1e-4) that moved [28,33] or [33,44]; they are quoted at 0.3% and 0.6% of
their own response, which is close enough to the floor to be worth checking.

---

## 8. WHY the two regimes disagree, in one sentence, with the figure that shows it

The interpolation error is a Lagrange remainder in the per-node displacement D.
Five knots refines the INTERIOR of the stencil. The near-anchor variation lives
in the interior (|D| <= 0.13 ln f at qT 38); the finite template leg does not
(|D| reaches 1.15 ln f at qT 38, i.e. outside kappa_F = 2). Refining the
interior cannot help a point outside it, and a quartic extrapolates worse than a
quadratic -- so the same change improves one regime and degrades the other.

Figure: `mechanism/stencil5_qT_*.png` -- per-node D against all three knot
bands, arithmetic from SCETlib's scale formulas, no calculation run.

**Decision taken from it:** test a WIDE five-knot geometry, kappa_F = 1/4, 1/2,
1, 2, 4, which keeps 1/2 and 2 exact (the templates' and the fit's points) and
BRACKETS the finite variation instead of refining the interior. Implemented as
`muf_nmem = -4`; the sign, rather than a new field, carries the geometry because
`sizeof(ad::GlobalData)` is the rule-cache guard. Prototype encoding, flagged as
such in the code: if wide is what ships it should become a real field with a
cache version bump.

---

## 9. The WIDE geometry (kappa_F = 1/4, 1/2, 1, 2, 4) is DEAD

**Measured**, x2 = 0.35, same script, same reference, same process:

```
  qT bin      true resp     dev 3-knot   % of resp   dev 5-knot WIDE   % of resp
 [ 18, 20]   -4.136e-04    +1.099e-04     -26.6%      -1.720e-02       +4158%
 [ 20, 24]   -3.075e-03    +9.725e-04     -31.6%      -1.036e-01       +3368%
 [ 24, 28]   -7.840e-03    -8.539e-04     +10.9%      -2.601e-01       +3318%
 [ 28, 33]   -1.822e-02    -2.151e-03     +11.8%      -3.145e-01       +1726%
 [ 33, 44]   -3.301e-02    -4.129e-04      +1.3%      -3.092e-01        +936%
  max|dev| of sigma          2.15e-03                  3.15e-01
```

Not a degradation: a failure. **31% of sigma.** The 3-knot column of the same
run reproduces the earlier three-knot numbers, so the build and the clamp are
fine and the failure is in the wide arm alone.

**It is NOT numerical conditioning.** The wide knot positions at
qT 38 / bT 5 are {-1.167, -0.614, 0, +0.651, +1.324} -- well separated, and the
Lagrange weights at the actual displacement d = 0.80 are O(1)
(+0.05, +1.11, -0.22, +0.08, -0.01, summing to 1). Computed by hand from
`fiveknot_stencil_geometry.py`.

**The likely reason, stated as a hypothesis with its test.** The kernel does not
interpolate a physical function alone: it interpolates the member convolutions
AND the rule's per-site weights `Var::w`, which are RE-SOLVED per member by
`rule_min_norm_update`. Those weights are a numerical artefact of the rule, not
a smooth function of ln muF, and a quartic through five of them spread over a
factor of SIXTEEN in muF has no reason to behave. Narrow keeps every member
close to the anchor and does not provoke it.
**The test that would settle it** (not yet run): interpolate the conv blocks at
5 knots while holding `wsite` at the 3-knot quadratic, and see whether the 31%
survives. If it does, the conv side is to blame; if it does not, the re-solved
weights are.

**Decision.** Do not pursue the wide geometry. It is kept in the branch behind
`muf_nmem = -4`, documented as measured-bad, so that nobody re-derives it.

**What would overturn it.** A version that stabilises the weight interpolation
(e.g. re-solving ONE weight vector against all members jointly instead of one
per member) might make a wide stencil viable. That is a much larger change than
"two more members" and is not what was proposed.

---

## 10. Threads and node conditions (for reproducing any of this)

The node carried SEVEN other heavy SCETlib cache builds all evening (another
session's `ntrain_gate` jobs); load average 400-600 of 768 cores and 23000 of
the 32768 per-user threads in use.
 * live-rule interpolation tests (`fiveknot_interp_error.py`,
   `fiveknot_kappaF_error.py`): `--threads 16` for the first two, `--threads 8`
   afterwards. 4 min each on an idle node, 10-25 min under this load.
 * the 80-bin subset cache: `--threads 64`.
 * `validate_variations` / `fiveknot_closure`: `--threads 32`.
Nothing here is thread-count sensitive in its RESULT -- both arms of every A/B
run in the SAME process -- but the wall times below are not reproducible on an
idle node.

---

## 11. RETRACTION: entry 9 said "the WIDE geometry is DEAD (measured bad)". IT IS NOT MEASURED AT ALL.

**What entry 9 claimed:** the wide stencil (kappa_F = 1/4, 1/2, 1, 2, 4)
returns 31% of sigma at x2 = 0.35, therefore the geometry is bad.

**Why that was wrong.** The wide stencil FAILS ITS OWN KNOT TEST. kappa_F = 4
is one of its knots, so the model must be exact there; it returns **-3.7e+08**
(`runcard_ref/kf4_wide_v2.log`). A stencil that cannot reproduce its own knot
is not measuring the geometry, it is reporting a defect in the prototype. The
31% is a symptom of that defect and must not be quoted as a property of the
wide geometry.

**What was fixed along the way, and what it did NOT fix.** Chasing it found a
real defect: the member-degeneracy guard used an ABSOLUTE tolerance
(1e-8 x ln f). Where the muf_min floor dominates -- qT just above x1*Q, where
1 - g falls through 1e-4 -- every knot position collapses together while
staying far above that cut, so the DIFFERENCES the Lagrange denominators are
built from are pure rounding. Three knots survives because its guard also tests
the outer separation; five does not. The guard is now relative to the spread the
node actually has. **It does not repair the wide arm** (kappa_F = 4 still
-3.7e+08), so there is a second defect that this round did not localise.

**What the fix does not change, re-run and checked:** the 39-direction no-op on
cache_260824b still reproduces every published number, and the narrow closure
table is BIT-IDENTICAL before and after. So the guard was never biting in the
narrow arm; the narrow results stand, and the x1,x3 -> 7.6e-01 there is genuine
extrapolation, not a guard artefact.

**Status of the wide geometry: UNVALIDATED.** Kept behind `muf_nmem = -4`,
labelled as such in the code and the commit message.

**What would settle it.** Localise the second defect -- the two candidates are
the per-member re-solved `Var::w` (a numerical artefact of the rule rather than
a smooth function of ln muF, here interpolated across a factor of sixteen) and
the `-4` encoding path itself, which is the least-exercised code in the patch.
The separating experiment is the one already named in entry 9: interpolate the
conv blocks at five knots while holding `wsite` at the three-knot quadratic.

**Why this is recorded rather than quietly corrected.** Several wrong
diagnoses have already been published in this study, one needing a public
correction. Entry 9 was written before the knot test existed and was one edit
away from going into the logbook as a measurement.

---

## 12. What NOT to do next, and what to do

**Do not merge five knots to fix the transitions.** It does not. `92f1299`, the
muF member coordinate fix (MR !8), still stands on its own merits and is
unaffected.

**The branch `muf-five-knots` (61123f2) is pushed and NO merge request was
opened.** The brief said to prepare one if it worked; on the question asked it
did not. If it is ever wanted it is for a different reason -- kappa_F between
knots (82x) and the fit derivative (3-33x) -- and that is Luca's call, not a
consequence of this measurement.

**The measurement that should come next, in order:**
 1. `node_cval` at qT [24,28], x2 = 0.55: zero its member interpolation and see
    whether the 1.86e-04 order-independent floor moves. Cheap, decisive, and it
    is the last unexplained piece of the near-anchor error.
 2. The analytic `d(conv)/d(ln muF)` column. Its case is now stronger than
    before, for a specific reason: the stencil geometry shows the displacement
    LEAVES the stencil at exactly the variation size the templates use, and a
    first-order-exact construction is the only one that does not care.
    Open question it must answer: whether ONE column suffices where
    D ~ 1.15 ln f, or a second derivative is wanted.
