# Decisions — PDF uncertainty moved from templates into the model (2026-08-26)

Task: build the reco 2D card with the 58 CT18Z eigenvector templates excluded so
the model's 29 `pdfEig*` parameters replace them, prove the swap is sound, and
measure what the fit does. Machinery + basic-physics validation, NOT a
measurement (Luca).

Build used for every number below: the SCETlib snapshot at
`/home/submit/lavezzo/.claude/jobs/140d052c/tmp/pdf62/scetlib_snapshot`,
`md5(libscet-qT.so) = 0c5dd7a92fea9e2ad0cb81639e9689a2` (verified, not assumed),
i.e. near-anchor-knots `eb60a04`, the only tree carrying BOTH the muF
member-coordinate fix (92f1299, MR !8) and the non-singular double-count fix
(3a8db11). Entered through `tmp/pdfcard/incontainer_nakfit.sh`, which is
`tmp/pdf62/incontainer_nak.sh` with `TF_NUM_INTRAOP_THREADS` 4 -> 32 and
`TF_NUM_INTEROP_THREADS` 2 -> 4, because the builder's thread clamp was chosen
for a 21-way shard fan-out and would throttle rabbit's own dense algebra.

Cache: `/ceph/.../scetlib_ad_caches/pdf62_260826/merged_full/{cache.npz,cache.conf}`
(210 gen bins x 62 members, 53 params, n_eig 29, has_as 1, has_muf 1). BOTH arms
use this same cache, so the A/B is a one-variable change.

---

## D-P01 — The systematic to exclude is `scetlib_dyturbo_...CT18Z...pdfvars_CorrByHelicity`, and the regex MUST carry `CT18Z` — SETTLED

**Decided.** The new exclusion regex is the old one with exactly one extra
branch:

```
^(resumTNP|scetlibNP|resumScaleZ|resumFOScaleZ|resumTransitionFOScale|scetlib_dyturbo.*pdfas.*|scetlib_dyturbo.*CT18Z.*pdfvars.*)
```

**Why.** `--excludeNuisances` is `re.match` against the SYSTEMATIC name, which
`addSystematic` defaults to the HISTNAME when no `name=` is given (D-006;
`datagroups.py:1408-1421`). `add_pdf_uncertainty` passes no `name=`, so the
systematic that emits all 58 `pdf{N}CT18ZSym{Avg,Diff}` nuisances is
`scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_pdfvars_CorrByHelicity`.

**Evidence, and the trap.** `add_quark_mass_vars` emits the m_b / m_c range
nuisances from histnames that differ only in the PDF-set token:
`..._MSHT20mbrange_N3p0LL_N2LO_pdfvars_CorrByHelicity` and `..._MSHT20mcrange_...`.
So the obvious branch `scetlib_dyturbo.*pdfvars.*` matches SIX systematics, not
four — it would delete the m_b/m_c uncertainty as well, re-committing D-005
exactly. Tested against the card's own 37 systematic names before building
(`tmp/pdfcard/` regex test):

| regex branch added | systematics matched | verdict |
|---|---|---|
| none (old card) | 3 | reference |
| `scetlib_dyturbo.*CT18Z.*pdfvars.*` | 4 (+1: the CT18Z pdfvars one) | **USED** |
| `scetlib_dyturbo.*pdfvars.*` | 6 (+3: also MSHT20mbrange, MSHT20mcrange) | **REJECTED** |

The `pdfas` branch was left byte-identical rather than also tightened to
`CT18Z`, so the diff against the previous card is exactly one branch.

**What would overturn it.** A cache that supplies an m_b/m_c parameter, or a
change of central PDF set (the `CT18Z` token is set-specific by design; on
another set the branch must be renamed, and the m_b/m_c collision recurs).

## D-P02 — Verification is by SET-DIFF against two reference cards, not by counting — SETTLED

**Decided.** The card is accepted only after a set-diff of the nuisance names,
the group memberships, `data_obs` and the response auxiliary against BOTH the
previous card (`adexcl`) and the untouched full-template card
(`260723_Z_2D_card_davidFix`). Tool: `tmp/pdfcard/carddiff.py`.

**Evidence.** New card
`/ceph/.../260826_Z_2D_card_scetlib_ad_pdf/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5`,
3673 nuisances.

* vs `adexcl` (3731): removed = exactly the 58 `pdf{1..29}CT18ZSym{Avg,Diff}`;
  ADDED = 0; every other group count identical; `data_obs` bit-identical.
* vs full-template (3746): removed = exactly 73 = the 15 of D-R04 + these 58;
  ADDED = 0.
* **the D-005 fingerprint is clean**: `bcQuarkMass` = 5 in the full-template
  card, 5 in `adexcl`, **5 in the new card** — and 1 in the over-broad 260820
  card. The new card carries 3673 nuisances against that card's 3669: four MORE,
  which are precisely `pdfMSHT20m{b,c}rangeSym{Avg,Diff}`.
* `auxiliary["scetlib_np"]` is **bit-identical** across all three cards
  (`R` md5 4241c14f5781 on (40,20,8,8,21,10), `N_gen` md5 551daf83717b), so the
  pdf62 cache and every response-fold result stay valid.

## D-P03 — The 4 quark-mass nuisances and `mb_up` are KEPT — SETTLED

The model has no m_b/m_c parameter. Excluding them would delete a real
uncertainty with no replacement — the D-005 failure mode. Confirmed present in
the new card (`bcQuarkMass` = 5).

## D-P04 — `pdfEig` is added as a ParamModel impact group — SETTLED

**Decided.** One-line addition in `param_model.py` mirroring the existing
`resumTNP` line: `groups["pdfEig"] = adp.pdf_group(self._param_order)`.

**Why.** The grouped PDF impact on alpha_s is the deliverable, and it is the
ONLY quantity the collinearity result (D-045) allows us to quote. Before this
patch the 29 eigenvector coefficients belonged to no group at all
(`IMPACT_GROUP_MEMBERS` is a static table and cannot hold a member list whose
length depends on the cache), so `--doImpacts` produced no PDF group in the
model arm.

**Why NOT named `pdfCT18ZNoAlphaS`** (which is the card group it replaces, and
which the file's own comment argues for): the label would be a lie on a cache
built from any other PDF set. The two are compared by number instead.

## D-P05 — The model constructs on the new card with all 47 parameters, and `_check_double_counting()` passes — SETTLED

Both arms constructed from the same 53-parameter pdf62 cache, one process each:

```
arm A (templates)  ...ZMassDilepton_ptll_yll_adexcl/     fitting 18 of 53   priors on 17
arm B (in model)   ...ZMassDilepton_ptll_yll_adexclpdf/  fitting 47 of 53   priors on 46
```

47 = 53 - 5 `DEFAULT_FROZEN` - 1 (`resumTNP_b_qqDS`, refused as singular, D-016
holds at P = 53) = 18 + 29. Arm B is the FIRST fit in which `pdfEig0..28` float.
The `^pdf\d+` conflict rule fired on neither arm, correctly: in arm A no
`pdfEig*` is registered so the rule does not apply, and in arm B the 58
`pdf{N}CT18ZSym*` are gone. `pdfMSHT20m{b,c}rangeSym*` does NOT match `^pdf\d+`
(no digit after "pdf"), so keeping them is safe by construction, not by luck.

## D-P06 — Reco-level eigenvector closure MEASURED; it was the open item in D-046 — SETTLED

`validate_variations_reco.py` on the new card, pdf62 cache, all 97 directions in
one run (the histmaker carries the needed reference,
`nominal_ptll_yll_..._CT18Z_N3p0LL_N2LO_pdfvars_Corr`, 59 vars).

| | max\|dev\| min / median / max | wmean median | rel. to own response, median / worst |
|---|---|---|---|
| 58 PDF eigenvector members | 2.57e-04 / **1.33e-03** / 2.93e-03 (worst pdf24) | 1.59e-04 | 0.025 / 0.124 |
| the 39 already-accepted directions, same run | ~0 / **7.42e-04** / 7.17e-03 (mufup) | 5.55e-05 | 0.013 / 0.199 |

**Read.** The eigenvectors sit INSIDE the accepted envelope — 3 of the 39 are
worse than the worst eigenvector — but their median is **1.8x the accepted
median**, so this is "same class, slightly worse half", not "at the median". At
gen level the same members gave 4.02e-04 … 2.43e-03, median 9.03e-04, so reco is
**1.5x worse than gen**, the opposite of what the 39 directions did (reco better
than gen, detector smearing diluting the one bad gen bin). Consistent with the
reco GRAIN term (gen-binning granularity, D-038) adding on top of an already
small CALC residual rather than diluting it.
The CALC / WGT / GRAIN split is NOT available for the eigenvectors (no
`pdfvars_CorrZ` gen reference is loaded), so only the TOTAL is quoted — which is
the number the fit uses.

## D-P07 — THE SWAP IS NOT NORMALISATION-NEUTRAL: the model arm carries ~18% MORE prefit PDF uncertainty — SETTLED (measurement), mechanism PARTLY OPEN

**This corrects D-044's last sentence.** D-044 established that the model's
eigenvector RESPONSE matches the correction file's members with no convention
factor (log-slope s = 0.9993). True, and unaffected. But it went on to conclude
"pdf{N}CT18ZSym{Avg,Diff} and pdfEig{N} are the same units, so the exclusion swap
is one-for-one — no factor is needed on either side". That is about the DATACARD,
and the datacard is not the correction file: `add_pdf_uncertainty` multiplies
every member variation by
`scale = pdfMap["ct18z"]["scale"] * inflation_factor_alphaS = (1/1.645) * 1.0`
(`theory_utils.py:164`, "Convert from 90% CL to 68%"), and then
`symmetrize="quadratic"` splits the asymmetric pair into
`SymAvg = 0.5(u+d)` and `SymDiff = 0.5*sqrt(3)*(u-d)` (`tensorwriter.py:361-386`).
The model carries NEITHER factor: `prior_sigma("pdfEig*") = 1.0` and c_e = +-1 IS
the raw 90% CL member.

**Measured, prefit, on the 780-bin reco spectrum.** Card side is the card's own
`logk[:, Zmumu, s]` summed in quadrature over all 58 PDF systs — permutation-free,
no assumption about which nuisance is which eigenvector. Model side is
`sqrt(sum_e D_e^2)` with `D_e = 0.5*(ln r_up - ln r_dn)` from the histmaker's own
reco members, which IS the model's linearised derivative in c_e (SCETlib's member
interpolation is exact at 0 and +-1 and quadratic between, so d/dc_e at 0 is
exactly the half-difference) and which the model reproduces to 1.3e-03 (D-P06).

| | yield-wmean | max over bins |
|---|---|---|
| card, 58 templates | 3.811e-02 | 7.254e-02 |
| model, 29 `pdfEig`, sigma = 1 | 4.507e-02 | 9.428e-02 |
| **card / model** | **0.845** | per-bin 0.756 … 0.936 |

**So the naive fear (the model is 1.645x too wide) is WRONG, and the reason is
not obvious**: the `sqrt(3)` of the quadratic split very nearly cancels the
90%->68% conversion, `sqrt(3)/1.645 = 1.053`. The residual is 0.845, i.e. the
model arm is 18% wider. That is the number to expect in the grouped PDF impact,
and a difference of that size between the arms is NOT evidence about the model.

**PARTLY OPEN — do not publish the mechanism as closed.** Reconstructing the
card's `logk` from the histmaker members with exactly those two operations gives
a band of 4.95e-02 against the card's measured 3.811e-02, i.e. 1.30x too large,
and the per-eigenvector slope test does not identify cleanly (the 58 members are
so collinear — D-045 — that a best-match scan returns |corr| > 0.99 for several
wrong members). The likely cause is that the card was built from the
**ByHelicity** hist, whose datacard route contracts the correction through the
MiNNLO angular coefficients, so my A/D are not the objects setupRabbit used. One
piece IS clean: for eigenvector 0, `pdf1CT18ZSymDiff` regresses on
`ln(pdf1/pdf0)` with slope 0.960 at |corr| = 0.998, against 1.053 predicted for a
perfectly antisymmetric pair — so `scale = 1/1.645` AND `diff_fact = sqrt(3)` are
both confirmed to be present.

**What this means for the analysis, and it is Luca's call, not mine.** Whether
the model's PDF prior should be sigma = 1 (90% CL, what SCETlib's member
interpolation naturally gives) or sigma = 1/1.645 (68% CL, matching the analysis
convention for every OTHER PDF uncertainty in the card) is a physics decision.
As shipped, arm B quotes a 90%-CL-wide PDF prior, only partly compensated by the
absence of the card's `sqrt(3)`. **Nothing here is a bug; it is an unmatched
convention, and it changes sigma(alpha_s).**

## D-P08 — `logk` reading validated on `lumi` before any conclusion was drawn from it — SETTLED

Every card-side number in D-P07 rests on reading `indata.logk[:, Zmumu, s]` as
`ln(variation/nominal)`. Checked against a nuisance whose size is known
independently: `lumi` gives `exp(logk) - 1 = +0.01200` exactly, flat to
3.0e-16 across all 780 bins (the 1.2% luminosity uncertainty). `CMS_background`
is identically 0 on the Zmumu column, as it must be. The reading is correct.

## D-P09 — The Asimov (`-t -1`) path has a large UNLOGGED pre-minimiser phase; a toy reaches the minimiser in ~2 min — OPEN (rabbit-side)

**Observed, not explained.** Four fits, same node, same cache, same build:

| fit | toys | time to the minimiser's first log line |
|---|---|---|
| `toyA_tmpl`, 18 floating | `-t 1` | ~2 min after the cache load (~4 min) |
| `toyB_model`, 47 floating | `-t 1` | ~2 min after the cache load |
| `armA_tmpl`, 18 floating | `-t -1` | **> 28 min and still silent** |
| `armB_model`, 47 floating | `-t -1` | **> 28 min and still silent** |

During that phase the process burns ~42 cores continuously and its MAIN thread
sits in a `futex` wait called from `libtensorflow_framework.so.2`, i.e. it is
blocked on TF's own thread pool inside a TF op — **not** in the SCETlib
`py_function`. So the cost is rabbit/TF, not the model. The same signature is in
the reference `kqt1` Asimov fit (P = 24, 9 floating), which took **11821 s total**
with an identically silent gap between the prior list and `edmval`.

**Consequence for planning:** the affordability estimate in D-047 (421 ms per warm
value+jacobian, 68.9 s Hessian) is about the MODEL and is correct, but it does not
bound an Asimov reco fit, which is dominated by this phase. Budget hours, not
minutes, for `-t -1` at this card size, and prefer a toy when the question is
about the minimiser.

**Not diagnosed further because:** the process runs inside singularity, so
`/proc/<pid>/exe` is unreadable from the host and neither `gdb` nor `eu-stack`
can resolve symbols. Cheap next step for whoever picks this up: run one Asimov
fit at `-v 4` (DEBUG turns on the `[timing]` lines that would name the phase),
which costs nothing extra.

## D-P10 — Card-side lint clean — SETTLED

The one-line `pdfEig` group addition passes the CONTAINER's `black`,
`isort --profile black` and `flake8 --select=E9,F63,F7,F82,F401`.

## D-P11 — D-045's collinearity is WORSE at reco level than at gen level — SETTLED

D-045 measured the eigenvector collinearity on the 210-bin GEN grid. The fit sees
the 780-bin (ptll, yll) RECO response, i.e. `d ln(R @ sigma_gen)/d c_e`. Measured
with the model itself (`tmp/pdfcard/reco_degeneracy.py`, 58 model evaluations at
`c_e = +-1`), same cache, same build:

| | gen (D-045) | **reco (this)** |
|---|---|---|
| pairs \|cos\| > 0.8 / 0.9 / 0.95 / 0.99, of 406 | 154 / 78 / 37 / 1 | **180 / 102 / 44 / 2** |
| worst pair | e5,e23 at 0.9964 | **e5,e23 at 0.9975** |
| cond of the normalised 29-column block | 2.72e+04 | **7.00e+04** |
| singular values above 1% of the largest | 8 of 29 | 8 of 29 |
| **participation ratio (effective # of shapes)** | **2.76** | **1.827** |
| shape fraction, median (normalisation projected out) | 0.553 | 0.522 |
| after projecting out normalisation: cond / PR | 1.34e+04 / — | 3.31e+04 / 2.609 |

**So the caveat gets STRONGER, not weaker, at the level the fit works at: 29
parameters carrying 1.8 effective shapes.** Folding through R averages over gen
bins and therefore removes distinguishing information, exactly as expected. The
column norms span 3.62e-02 … 6.48e-01, a factor 18, so the fit is not singular —
but per-eigenvector postfit values are prior-dominated and must not be reported.
Figure `reco_eig_degeneracy.png`.

**Bonus: the model's own prefit PDF band validates the D-P07 proxy.**
`sqrt(sum_e ||d ln sigma_reco/d c_e||^2)` from the model = **4.470e-02** wmean
(max 9.486e-02) against the histmaker-member proxy 4.507e-02 (9.428e-02) — 0.8%.
So D-P07's card/model ratio is **0.853**, i.e. the model arm carries **17% more**
prefit PDF uncertainty. Use 0.853, not the proxy's 0.845.

## D-P12 — Eigenvectors 0 and 3 are QUADRATIC, not linear, in c_e — and the two treatments handle that differently. NEW, and it pushes the OTHER way — SETTLED

Per eigenvector at reco level, with `D_e = 0.5(u-d)` (the antisymmetric part, which
IS the linearised derivative in `c_e`) and `A_e = 0.5(u+d)` (the symmetric part):

| eigenvector | members | \|\|A\|\|/\|\|D\|\| | \|\|D\|\| |
|---|---|---|---|
| **0** | pdf1 / pdf2 | **8.58** | 3.77e-02 |
| **3** | pdf7 / pdf8 | **8.29** | 3.72e-02 |
| 4 | pdf9 / pdf10 | 1.37 | 1.49e-01 |
| … median over the 29 | | 0.533 | |
| 15 (least asymmetric) | pdf31 / pdf32 | 0.159 | 2.26e-01 |

For eigenvectors 0 and 3 the CT18Z up and down members move the reco spectrum the
**same way**: the response is essentially quadratic in `c_e` with a tiny linear
part. Consequences, and they differ between the arms:

* **Templates:** `symmetrize="quadratic"` splits this off as its own nuisance,
  `pdf{1,4}CT18ZSymAvg = 0.5(u+d)`, so the card CARRIES it (times 1/1.645). Its
  norm is 8.58 x 3.77e-02 = 0.32, comparable to the LARGEST antisymmetric column
  (0.648) — this is not a small effect.
* **Model:** `compute()` is genuinely quadratic in `c_e` (SCETlib's member
  interpolation is exact at 0 and +-1), so the MINIMISER sees it. But the
  covariance, the reported sigma and the impacts all come from the Hessian, and at
  `c_e = 0` the first derivative is `D_e`, which for these two directions is ~1/8
  of the real +-1 sigma excursion. **The linearised PDF impact therefore
  UNDERSTATES eigenvectors 0 and 3.**

This pushes the OPPOSITE way from D-P07's 90%-CL effect, and it is a property of
the response, not of the implementation. It is also the strongest argument yet for
reading only the TOTAL PDF impact from either treatment.

**What would overturn it:** a postfit at which `c_0`, `c_3` sit far enough from 0
that the local derivative is no longer ~`D_e`; check the postfit values before
assuming the understatement persists in a real fit.
