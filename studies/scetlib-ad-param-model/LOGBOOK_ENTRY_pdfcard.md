### 2026-08-26 — PDF UNCERTAINTY MOVED FROM TEMPLATES INTO THE MODEL: card built, swap verified, reco closure measured

**Luca's instruction: "PDF members must come from SCETlib not templates." Done at
the card level, and the swap is verified — but it is NOT normalisation-neutral,
which is a finding, not a bug.** Machinery + basic-physics validation only.

Build: the SCETlib snapshot `tmp/pdf62/scetlib_snapshot`,
`md5(libscet-qT.so) = 0c5dd7a92fea9e2ad0cb81639e9689a2` (verified), i.e.
near-anchor-knots `eb60a04`, the only tree with BOTH the muF member-coordinate
fix (92f1299) and the non-singular double-count fix (3a8db11). Cache
`pdf62_260826/merged_full` (53 params, n_eig 29) for BOTH arms, so every A/B
below is a one-variable change. Plots + provenance:
`~/public_html/alphaS/260826_scetlib_ad_pdf_in_model/`.

#### The new card

`/ceph/.../260826_Z_2D_card_scetlib_ad_pdf/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5`
— the previous `setupRabbit` command with ONE extra exclusion branch:

```
--excludeNuisances '^(resumTNP|scetlibNP|resumScaleZ|resumFOScaleZ|
                      resumTransitionFOScale|scetlib_dyturbo.*pdfas.*|
                      scetlib_dyturbo.*CT18Z.*pdfvars.*)'
```

**The `CT18Z` in that branch is load-bearing.** `--excludeNuisances` is
start-anchored `re.match` against the SYSTEMATIC name, which defaults to the
HISTNAME (D-006), and `add_quark_mass_vars` emits the m_b/m_c nuisances from
histnames that differ from the eigenvector one only in the PDF-set token. Tested
against the card's own 37 systematic names BEFORE building:

| exclusion branch | systematics matched | verdict |
|---|---|---|
| none (previous card) | 3 | reference |
| `scetlib_dyturbo.*CT18Z.*pdfvars.*` | 4 — adds only the CT18Z one | **USED** |
| `scetlib_dyturbo.*pdfvars.*` | 6 — also MSHT20mbrange, MSHT20mcrange | **REJECTED**, would repeat D-005 |

**Verified by set-diff, not by counting** (`tmp/pdfcard/carddiff.py`):

* vs the previous card (3731 -> 3673 nuisances): removed = **exactly** the 58
  `pdf{1..29}CT18ZSym{Avg,Diff}`; **added = 0**; every other group count identical.
* vs the untouched full-template card (3746): removed = exactly 73 = the 15 of
  D-R04 + these 58; added = 0.
* **`bcQuarkMass` = 5 in all three cards** (`mb_up` + the four
  `pdfMSHT20m{b,c}rangeSym*`) — 1 in the broken 260820 card. The new card has
  3673 nuisances against that card's 3669: the four MORE are exactly the m_b/m_c ones.
* `data_obs` bit-identical; `auxiliary["scetlib_np"]` **bit-identical** across all
  three cards (`R` md5 4241c14f5781 on (40,20,8,8,21,10)), so the pdf62 cache and
  every response-fold result stay valid.
* Groups that vanish: `pdfCT18Z`, `pdfCT18ZNoAlphaS` (58 -> absent);
  `theory` 247 -> 189, `theory_qcd` 239 -> 181 (-58 each).

#### The swap constructs and does not double count

```
arm A (templates)  ..._adexcl     fitting 18 of 53   Gaussian priors on 17
arm B (in model)   ..._adexclpdf  fitting 47 of 53   Gaussian priors on 46
```
47 = 53 - 5 `DEFAULT_FROZEN` - `resumTNP_b_qqDS` (still the only null column at
P = 53) = 18 + 29. **First fit in which `pdfEig0..28` float.**
`_check_double_counting()` passes on both: the `^pdf\d+` rule cannot fire in arm A
(no `pdfEig*` registered) and has nothing left to catch in arm B.
`pdfMSHT20m{b,c}rangeSym*` does not match `^pdf\d+` — no digit after "pdf" — so
keeping them is safe by construction.

One code change was needed and made: `pdfEig` added as a ParamModel impact group
(one line in `param_model.py`, mirroring the existing `resumTNP` line). The 29
coefficients previously belonged to no group, so `--doImpacts` produced no PDF
group in the model arm — and the total PDF impact is the ONLY quantity D-045 lets
us quote. Deliberately NOT named `pdfCT18ZNoAlphaS`: that label would be a lie on
a cache from another PDF set.

#### Reco-level eigenvector closure — the open item of D-046, now MEASURED

`validate_variations_reco.py`, all 97 directions in one run on the new card and
the pdf62 cache. The reference the eigenvectors needed does exist in the
histmaker: `nominal_ptll_yll_..._CT18Z_N3p0LL_N2LO_pdfvars_Corr` (59 vars).

| | max\|dev\| min / median / max | wmean median | rel. to own response med / worst |
|---|---|---|---|
| **58 PDF eigenvector members** | 2.57e-04 / **1.33e-03** / 2.93e-03 (pdf24) | 1.59e-04 | 0.025 / 0.124 |
| the 39 accepted directions, same run | ~0 / **7.42e-04** / 7.17e-03 (mufup) | 5.55e-05 | 0.013 / 0.199 |

**Honest read.** Inside the accepted envelope — 3 of the 39 are worse than the
worst eigenvector, 15 of 39 worse than the eigenvector median — but the
eigenvector median is **1.8x the accepted median**, so this is "same class,
slightly worse half", not "at the median" as the gen-level table read. And reco is
**1.5x WORSE than gen** for the eigenvectors (gen median 9.03e-04), the opposite
of the 39, which improved at reco. Consistent with the reco GRAIN term (pure
gen-binning granularity, D-038) adding on top of an already tiny CALC residual
instead of being diluted by smearing. The CALC/WGT/GRAIN split is unavailable for
the eigenvectors (no `pdfvars_CorrZ` gen reference is loaded), so only TOTAL is
quoted — which is what the fit uses.
Figure: `reco_eig_closure.png`.

#### THE SWAP IS NOT NORMALISATION-NEUTRAL — corrects the last sentence of D-044

D-044 showed the model's eigenvector RESPONSE matches the correction file's
members with no convention factor (log-slope 0.9993). That stands. It then
concluded the DATACARD swap is one-for-one. **It is not.** `add_pdf_uncertainty`
multiplies every member variation by
`scale = pdfMap["ct18z"]["scale"] * inflation_factor_alphaS = (1/1.645) * 1.0`
(`theory_utils.py:164`, "Convert from 90% CL to 68%") and then
`symmetrize="quadratic"` splits the asymmetric pair into `SymAvg = 0.5(u+d)` and
`SymDiff = 0.5*sqrt(3)*(u-d)` (`tensorwriter.py:361-386`). The model carries
NEITHER: `prior_sigma("pdfEig*") = 1.0` and `c_e = +-1` IS the raw 90% CL member.

Measured prefit, on the 780 reco bins — card side straight from the card's own
`logk[:, Zmumu, s]` in quadrature over all 58 PDF systs (permutation-free), model
side `sqrt(sum_e D_e^2)` with `D_e = 0.5*(ln r_up - ln r_dn)`, which IS the model's
linearised derivative in `c_e` (SCETlib's member interpolation is exact at 0 and
+-1, quadratic between) and which the model reproduces to 1.3e-03 per the table above:

| | yield-wmean | max over bins |
|---|---|---|
| card, 58 templates | 3.811e-02 | 7.254e-02 |
| model, 29 `pdfEig`, sigma = 1 | 4.507e-02 | 9.428e-02 |
| **card / model** | **0.845** | per-bin 0.756 … 0.936 |

**So the naive fear — "the model is 1.645x too wide" — is WRONG, for a
non-obvious reason:** the `sqrt(3)` of the quadratic split nearly cancels the
90%->68% conversion, `sqrt(3)/1.645 = 1.053`. What remains is that **the model arm
carries ~18% MORE prefit PDF uncertainty than the template arm.** A grouped-PDF-impact
difference of that size between the arms is EXPECTED and is not evidence about the model.

**Mechanism only PARTLY closed — do not publish it as closed.** Reconstructing the
card's `logk` from the histmaker members with exactly those two operations gives
4.95e-02 against the card's measured 3.811e-02 (1.30x high), and the
per-eigenvector identification is defeated by the collinearity of D-045 (a
best-match scan returns |corr| > 0.99 for several *wrong* members). Likely cause:
the card was built from the **ByHelicity** hist, whose datacard route contracts
through the MiNNLO angular coefficients, so the A/D I formed are not the objects
`setupRabbit` used. One piece IS clean: for eigenvector 0, `pdf1CT18ZSymDiff`
regresses on `ln(pdf1/pdf0)` with slope 0.960 at |corr| = 0.998 against 1.053
predicted for a perfectly antisymmetric pair, so `scale = 1/1.645` and
`diff_fact = sqrt(3)` are both confirmed present.
Figure: `pdf_prefit_band.png`.

**Luca's call, not the agent's:** whether the model's PDF prior should be
`sigma = 1` (90% CL, what SCETlib's member interpolation naturally gives) or
`sigma = 1/1.645` (68% CL, the convention every other PDF uncertainty in this card
uses). As shipped, arm B quotes a 90%-CL-wide PDF prior only partly compensated by
the absent `sqrt(3)`. Not a bug — an unmatched convention that changes
sigma(alpha_s).
