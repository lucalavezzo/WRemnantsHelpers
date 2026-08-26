---
slug: scetlib-ad-param-model / 260826-pdf-cl-scaling
updated: 2026-08-26
---

# PDF confidence-level scaling inside the differentiable param model

## START HERE

**State.** The 0.853 card/model prefit-band gap is **fully explained and closed**.
The card applies `1/1.645` to *both* halves of every eigenvector pair *and* a
`sqrt(3)` to the symmetric (`SymDiff`) half; the model carried neither. The CL
scale is now implemented in the model as a **coefficient** map
(`pdfEig{i} = theta`, SCETlib evaluated at `c_e = 0.6079*theta`), read from
`theory_utils.pdfMap` and therefore general over the PDF set. The `sqrt(3)` is
deliberately **not** ported: it is the template route's surrogate for a curvature
the model represents exactly.

**Next step.** Rerun arm B (`PDF in the model`) and toy B. Their PDF group impact
and sigma(alpha_s) were produced with `c_e = +-1` = the 90% CL member and a unit
prior, i.e. a linear PDF response 1.645x too large.

**Blocking.** Nothing.

**Code changed** (two files, both in `wremnants/postprocessing/scetlib_ad/`):
`params.py` adds `pdf_set_key` / `pdf_coeff_scale`; `param_model.py` adds the
`pdf_coeff_scale=` spec token, `_resolve_pdf_coeff_scale`, the `_rp_scale`
vector and its use in `_physical` / `_physical_tf`. Container CI lint (isort
--profile black, black, flake8 F-codes) passes on both.

**HAZARD to check first.** At the time of writing the working tree was on
`scetlib-np-param-model`, where `wremnants/postprocessing/scetlib_ad/` is
UNTRACKED (`git status` says `?? .../scetlib_ad/`). The scheduled switch to
`scetlib-ad-param-model`, where those files ARE tracked, will refuse or clobber
depending on how it is done. Verify `grep -c pdf_coeff_scale
wremnants/postprocessing/scetlib_ad/param_model.py` returns 12 after any branch
change.

---

## Findings

### F-1. The card's factor, measured from its own `logk`

Card `260826_Z_2D_card_scetlib_ad/ZMassDilepton_ptll_yll_adexcl`
(arm A -- arm B has the PDF templates *removed*, so it carries no PDF `logk` at
all; the brief pointed at the wrong one). Reference = the histmaker's own reco
`..._pdfvars_Corr` hist, 59 `vars`. `logk` reading validated on `lumi`:
`exp(logk)-1 = 0.012000 +- 3.8e-16`, flat.

With `D_e = 0.5(ln u - ln d)` (antisymmetric, the linear derivative) and
`A_e = 0.5(ln u + ln d)` (symmetric, the quadratic part):

| card nuisance | regressed on | slope, mean over 29 | min / max | vs source |
|---|---|---|---|---|
| `pdf{N}CT18ZSymAvg`  | `D_e`       | **-0.602510** (std 5.5e-03) | -0.6101 / -0.5827 | `1/1.645 = 0.60790` -> **0.9911** |
| `pdf{N}CT18ZSymDiff` | `A_e`       | **+1.048810** (std 6.7e-03) | +1.0297 / +1.0659 | `sqrt(3)/1.645 = 1.05292` -> **0.9961** |

`|corr|` is 0.999+ for 27 of 29 (worst 0.965, e6). The sign on `SymAvg` is a
member-ordering convention (setupRabbit's "up" is `pdf{2i+1}`), irrelevant to a
band. **Uniform**: 0.92% RSD across eigenvectors, and at bin level the median is
-0.60333 (1%/99% -0.884/-0.377, the tails being low-`|D|` bins and the
ByHelicity contraction).

### F-2. `SymDiff` is NOT zero. The `symm_diff = 0` line is in a different code path

`max|SymDiff logk| = 2.042e-02` against `max|SymAvg logk| = 3.340e-02`, and
**0 of 29** eigenvectors have a null `SymDiff`. The card's own metadata records
`symmetrizePdfUnc = quadratic`, `scalePdf = -1.0` (i.e. take the map's
inflation factor).

The `symm_diff = 0` line at `wremnants/postprocessing/syst_tools.py:1007` sits
inside `symmetrize_unc_matrix`, whose **only** caller in the whole tree is
`wremnants/postprocessing/postfit_pdf_helper.py:73` -- a postfit *reader*. The
card is written by `rabbit/rabbit/tensorwriter.py:372-386`, which is a separate
implementation and applies `diff_fact = sqrt(3)` live.

### F-3. Where the 0.853 came from, to 0.7%

`SymAvg` carries the linear half, `SymDiff` the quadratic half -- **not** the
other way round (rabbit stores `logkdown = -ln(down/nom)`, so
`0.5(logkup+logkdown)` is the *antisymmetric* combination despite being called
"Avg"). With that assignment:

```
card band  = (1/1.645) * sqrt( sum_e [ D_e^2 + 3 A_e^2 ] )
```

| per reco bin (relative), yield-weighted | wmean | max |
|---|---|---|
| card `logk` quadrature, all 58 | 3.81056e-02 | 7.25361e-02 |
| predicted `s*sqrt(D^2+3A^2)`  | **3.83561e-02** | 7.29520e-02 |
| predicted `s*sqrt(A^2+3D^2)` (the swapped assignment) | 4.99356e-02 | 1.02633e-01 |
| model proxy, sigma=1 at `c=+-1`, linearised (`=|D|`) | 4.50741e-02 | 9.42805e-02 |

**card / predicted = 0.99347**, per bin 0.978 .. 1.016. The previous round's
"1.30x high" reconstruction is exactly the swapped assignment:
`sqrt((3+r)/(1+3r)) = 1.299` at the measured `r = (|A|/|D|)^2 = 0.335`.

So `0.6079 (CL) x 1.4161 (the sqrt(3) on the quadratic half) x 0.9935
(ByHelicity route) = 0.855`, against the measured 0.8565. The 1.40 the
coordinator flagged as unexplained **is** the `sqrt(3)`, live and not dead code.

### F-4. The model side is not the one that is off

Model's own linearised band (`reco_degeneracy.py`, 58 evaluations through `R`):
`4.47022e-02` vs the histmaker proxy `4.50741e-02` -> **0.9917**. The per-pair
asymmetry agrees too: model `|A|/|D|` min 0.1588 / median 0.5275 / max 8.8669,
histmaker 0.159 / ~0.53 / 8.578. The model reproduces both halves of CT18Z's
members; only the convention was missing.

## Decisions

### D-PCL-1 -- The card's factor is `1/1.645` on the linear half and `sqrt(3)/1.645` on the quadratic half -- SETTLED (measured)
Evidence: F-1, F-2, F-3. Overturned by: a card built with
`--symmetrizePdfUnc average` or `--scalePdf` set explicitly, either of which
changes the recorded metadata, which is why the model reads the map rather than
a constant.

### D-PCL-2 -- Port the CL scale, do NOT port the `sqrt(3)` -- SETTLED
The `sqrt(3)` is not a physics convention. It is rabbit's variance surrogate for
a response a template cannot represent: a template morphs linearly in its
nuisance, so an asymmetric `+-` pair has to be split into two linear nuisances,
and the second is inflated so the pair's variance is conservative
(`tensorwriter.py`: "leads to a large variance"). The model evaluates
`I(c) = I_0 + c (I_+-I_-)/2 + c^2 (I_+ + I_- - 2 I_0)/2` (`DrellYan.hpp`, exact
at `c = 0, +-1`), so it carries the curvature itself. Porting the `sqrt(3)`
would double-count it.
Consequence, stated up front: the card's total PDF band stays ~1.4x the model's
*linearised* band after the fix, and that difference is the surrogate, not a
missing scale.

### D-PCL-3 -- Scale the COEFFICIENT, not the response -- SETTLED (Luca)
Template route: `response -> s * response`, forced, because that is the only
handle a fixed shape offers. Model route: `c_e = s * theta`, i.e. evaluate the
calculation at the 68% CL point in eigenvector space, which is what a 1 sigma
PDF displacement physically is.
They agree at `O(c)` and differ by `(s^2 - s) A_e = -0.3921 s A_e`, i.e. exactly
on the curvature. Cost/benefit quantified in F-5 below.

### D-PCL-4 -- Read the factor from `theory_utils.pdfMap`, never hard code it -- SETTLED
`params.pdf_coeff_scale(lha_name, noi)` composes
`pdf_inflation_factor(info, noi) * info["scale"]`, the same product
`postfit_pdf_helper.py:203-210` and `rabbit_theory_helper.add_pdf_uncertainty`
form. The LHAPDF set name comes from the cache runcard's own
`[Calculation_settings] pdf_set`, the `noi` from the datacard's own
`meta_info.args.noi`. An unknown set **raises**; it does not fall back to 1.
NB CT18Z is its own `pdfMap` entry (`"ct18z"`, `lha_name CT18ZNNLO`) with
`inflation_factor_alphaS = 1.0`; the `1.2` belongs to `"ct18"`, a different set.

### F-5. Evaluate-at-`s` vs scale-the-response: the curvature the templates could not carry

`||delta||/||response||` at `theta = +1`, per eigenvector, measured with the model
(58 + 58 evaluations through `R`):

| | median over 29 | e0 | e3 | max |
|---|---|---|---|---|
| relative difference | **0.181** | **0.561** | **0.743** | 0.743 |
| `||evaluate at s|| / ||s x response at 1||` | ~0.91 | 0.641 | 0.576 | -- |

So for the two curved eigenvectors the template convention overstates the `+1
sigma` reco excursion by 1.6x (e0) and 1.7x (e3), and even the *median*
eigenvector is off by 18%. `|A|/|D|` from the model: e0 8.867, e3 8.290, median
0.53, min 0.159 -- matching the histmaker halves (8.578 / 8.293 / 0.159) and the
earlier gen-level measurement.

### F-6. The proof: card / model is 1.000 on the like-for-like object

Yield-weighted mean over the 780 reco bins.

| prefit PDF band (relative) | wmean | vs card `SymAvg` |
|---|---|---|
| card, all 58 templates | 3.81056e-02 | -- |
| card, 29 `SymAvg` (the linear, 1 sigma response) | 2.71622e-02 | 1 |
| card, 29 `SymDiff` (the `sqrt(3)` quadratic surrogate) | 2.66512e-02 | 0.981 |
| model BEFORE (`c = +-1`, 90% CL, unit prior) | 4.47022e-02 | 1.646 |
| **model AFTER (`c = +-0.60790`)** | **2.71413e-02** | **1.00077** |
| model AFTER, full predictive sd `sqrt(D_s^2 + 2 A_s^2)` | 3.02083e-02 | 1.113 |

* **card `SymAvg` / model AFTER = 1.00077** yield-weighted, median 0.99927,
  per bin 0.981 .. 1.045; per eigenvector mean 1.00282, std 0.0109, min 0.978,
  max 1.025. The ~1% scatter is the ByHelicity contraction (F-1), not the scale.
* The 39 other directions are untouched **by construction**: `_rp_scale != 1` on
  exactly the 29 `pdfEig` slots of 47, `_physical` is bit-identical to the
  identity on all 18 others (0 violations on a random theta), and
  `_physical == _physical_tf` to 0.000e+00.
* card total / model AFTER = **1.404**, and that residual is named, not fudged:
  `1.404 = 1.113 x 1.261`. The 1.113 is genuine curvature the model carries in
  `compute()` but that an Asimov Hessian (exactly Gauss-Newton at the truth)
  cannot see; the 1.261 is the card's over-inflation of that same curvature. The
  card's quadratic amplitude is `sqrt(3)/s = 2.85x` the physical `s^2 A`, because
  `add_pdf_uncertainty` scales the member *variation* by `s` where a genuinely
  quadratic term scales by `s^2`, and then multiplies by `sqrt(3)` on top.

## Physics consequence

Asimov, 2D `ptll-yll`, real-data card, same cache both arms
(`ab_report.py` on `fitresults_arm{A,B}`):

| | sigma(alpha_s) | PDF group |
|---|---|---|
| arm A, PDF as templates | 1.49056e-03 | `pdfCT18ZNoAlphaS` 1.08338e-03 |
| arm B, PDF in model, **no CL scale** | 1.62004e-03 | `pdfEig` 1.25558e-03 |

* Non-PDF part in quadrature: **1.02375e-03 (A) vs 1.02374e-03 (B)** -- five
  digits. The arms really do differ only in the PDF treatment.
* The grouped impact tracks the prefit band to 1.2% (impact B/A 1.1589, band B/A
  1.1731), so the projection below is a linear extrapolation with a measured
  slope, not a guess.

**Projected after the fix** (response shrinks by 0.60716):
`pdfEig` impact **7.62e-04**, i.e. **0.704x** the template arm; sigma(alpha_s)
**1.276e-03**, **0.856x** arm A and **0.788x** arm B as run.

So: **the earlier "PDFs in the model" fit numbers must be redone.** As run they
carry a 90% CL PDF displacement with a unit prior -- a linear PDF response 1.645x
too large -- which is the whole of the 1.16x excess PDF impact and 1.087x excess
sigma(alpha_s) that arm B showed. Arm A (templates) is unaffected; nothing about
the card changed.

Read the projected 30% PDF-impact *reduction* relative to the templates with F-6
in hand. It is not a free gain: 1.26 of the 1.40 is the template route's
deliberately conservative quadratic surrogate, which the model should not carry;
the remaining 1.11 is real curvature that the model has and the Asimov Hessian
does not report. Quoting the model's linearised PDF impact therefore understates
the model's own PDF uncertainty by ~11%, concentrated in eigenvectors 0 and 3.

## Log

**2026-08-26** -- Measured the card convention off its own `logk` (F-1..F-3),
confirmed the model side is not the culprit (F-4), implemented the coefficient
map, verified (F-5, F-6), projected the impact. Figure:
`pdf_cl_scaling_band.png`. Code: `wremnants/postprocessing/scetlib_ad/params.py`
(`pdf_set_key`, `pdf_coeff_scale`) and `param_model.py`
(`_resolve_pdf_coeff_scale`, `_rp_scale`, `_physical`, `_physical_tf`, the
`pdf_coeff_scale=` spec token).

**OPEN, for Luca, not decided here.** Two things the agent deliberately did not
choose:
1. Whether to keep the model's PDF impact as the linearised Hessian number
   (understates its own curvature by 11%, F-6) or to quote something that
   includes it. This is a reporting question, not a modelling one.
2. Whether the analysis wants the model arm's *smaller* PDF uncertainty at all,
   given that it comes from dropping a conservatism the template route has always
   carried. The scaling itself is not optional -- 90% CL with a unit prior is
   simply wrong -- but the 1.26 is a choice about conservatism.
