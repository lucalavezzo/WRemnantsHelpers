# SCETlib nuisance factorizability — study logbook

**Goal.** Validate whether the full SCETlib prediction *factorizes* between the
fit's nuisance groups: does varying two nuisances jointly equal the sum of the
individual template variations, or is there a cross-term the linear nuisance
model misses? Motivation: the NP λ's were found NOT to factorize among
themselves (→ the on-the-fly param model). We now check cross-terms between λ
and the other SCETlib nuisances (TNP, scale, PDF, αs).

**Metric.** Per point (qT, Y, Q), `R_X = σ_X/σ_central − 1`:
- `N_ab = R_ab − (R_a + R_b)` — **additive** nonlinearity (the original metric).
- `floor = R_a·R_b` — the value `N` takes if the two combine as a pure PRODUCT.
- **`Nmult = N − R_a·R_b = (1+R_ab) − (1+R_a)(1+R_b)`** — **multiplicative residual.**

**Which metric is fit-relevant: `Nmult`.** rabbit combines systematics
MULTIPLICATIVELY (`systematic_type=log_normal`, the DEFAULT — `setupRabbit.py:1084`):
`expected = rnorm(λ)·exp(Σ_j θ_j·logk_j)·norm` (`fitter.py:1606-1718`). λ enters via
`rnorm` (param model, exact); αs/TNP enter as systematics inside the `exp()`, with
their `logk` template built ONCE at central λ. So the fit's model of any pair is the
pure product `(1+R_a)(1+R_b)` → it ALREADY captures the floor `R_a·R_b`; the cross-term
it MISSES is `Nmult`. `|N|/floor ≈ 1` → truth is multiplicative (fit is right, Nmult≈0);
`≫ 1` → truth MORE coupled than multiplicative (fit misses, Nmult≈N); `≪ 1` → truth is
ADDITIVE, fit OVER-couples by ≈floor (fit misses, Nmult≈floor). Computed offline
(`analyze_xterm.py`, sorted by max|Nmult|) from a `--point-spectrum` card.
(Caveat: if a fit ever passes `--systematicType normal`, the αs/TNP piece is additive
and the missed term is the full `N` instead. Default is `log_normal`.)

**σ split (key to the strategy).** full = singular(resummed) + nonsingular(FO).
- **Cancellation rule.** The nonsingular (FO) is independent of λ (NP) and of the
  TNPs (resummation). In `N(X,Y)` it cancels whenever it is independent of *either*
  factor. ⇒ **singular-only is RIGOROUS for any pair with a λ or TNP factor:**
  λ×λ, λ×TNP, TNP×TNP, **αs×λ, αs×TNP, PDF×λ, PDF×TNP, transition×{λ,TNP},
  FOscale×{λ,TNP}**. The nonsingular only fails to cancel when **both** factors are
  FO-affecting (αs, PDF, FO-scale, transition) — e.g. αs×PDF, αs×transition — and
  only those need the matched (DYTurbo) nonsingular (`param_model.compute_nonsingular_gen`).
- Caveat for singular-only: at high qT (≈Q) the singular is extrapolated past its
  validity → ratios are artifacts there; the cross-terms live at low qT, ignore qT≈Q.

---

## Fit nuisances (from `setupRabbit.py` → `TheoryHelper`, default `--resumUnc tnp`, transition on)

| nuisance | members | leg |
|---|---|---|
| 10 TNPs | `gamma_cusp, gamma_mu_q, gamma_nu, h_qqV, s, b_qqV, b_qqbarV, b_qqS, b_qqDS, b_qg` | resummation → **singular** |
| NP λ (`--npUnc Delta_Lambda`) | `lambda2_nu, lambda4_nu(*), lambda2, lambda4, delta_lambda2` | **singular** |
| `resumTransitionZ` | `transition_points [0.2,0.75,1.0] / [0.2,0.35,1.0]` (middle point 0.6→0.75/0.35) | **nonsingular varies** |
| `resumFOScaleZ` | `renorm_scale_pt20_envelope` Up/Down (composite) | **nonsingular varies** |
| PDF, αs, MiNNLO | — | separate |

(*) `lambda4_nu` was fixed in one screenshotted config but floats in general.

NP central (tanh_2 / Franks card, from the fit's λ table):
`lambda2_nu=0.15, lambda2=0.4, lambda4=0.4, delta_lambda2=0`; held
`lambda4_nu=0, lambda_inf_nu=2, lambda6=0, lambda_inf=1`.

---

## Decisions (newest first)

- **2026-06-16** — **λ×PDF: use ONE runcard + `--pdf-member` loop (NOT 58 runcards).**
  Checked how the production pdfvars correction was made (`print_command.py` on the
  meta / the `.log` in `wremnants-data/.../TheoryCorrections`): condor looped
  `scetlib-run-qT.py … --pdf-member $(PdfNum)` over `-p 59`. `scetlib-run-qT.py` has
  `--pdf-member N` (overwrites the card's `[QCD] pdf_member`, line 112-118) AND
  auto-appends `_pdf{N}` to the output (line 118 → `_pdfN_pointspec.pkl`, line 450). So
  one runcard suffices. Replaced the 58 per-member cards (and `gen_pdf_runcards.py`) with
  a single `runcard_xterm_singles.ini` (nominal `[QCD]` from base.conf, `variations_singles.conf`).
  Run: `for m in $(seq -w 1 58); do scetlib-run-qT.py <th> 1 xterm_validation/runcard_xterm_singles.ini
  --point-spectrum --pdf-member $m --live; done` → `runcard_xterm_singles_pdf{01..58}_pointspec.pkl`.
  Aggregate: `analyze_pdf_xterm.py runcard_xterm_pointspec.pkl --kind lambda --qtmax 40`
  (glob `*_pdf<N>_pointspec.pkl`) → per-knob worst-single-member + Hessian-combined
  (quadrature over the 29 eigenvector pairs) cross-term. Same Run loop also gives PDF×TNP.
  Beam-function cache has all 59 members (`CT18ZNNLO_beamfunc/<chan>/*_0000…0058.dat`),
  no regen. (`--pdf-member` non-numeric → sets `pdf_set`; αs runs also need `alphas_mu0`,
  so they keep `runcard_xterm_asUp/asDn.ini`.) Singular-only rigorous (cancellation rule).
- **2026-06-16** — **rabbit combines MULTIPLICATIVELY → switched the headline metric
  to `Nmult`.** Confirmed in `fitter.py:_compute_yields_noBBB` (1606-1718): default
  `systematic_type=log_normal` (`setupRabbit.py:1084`) gives
  `expected = rnorm(λ)·exp(Σθ·logk)·norm`. λ rides in `rnorm` (param model, exact),
  αs/TNP in the `exp()` with `logk` frozen at central λ → the fit models every pair as
  the product `(1+R_a)(1+R_b)`. So the fit ALREADY captures the floor `R_a·R_b`; the
  miss is `Nmult = N − R_a·R_b`. `analyze_xterm.py` now computes/sorts by `Nmult` (both
  pairs & `--shifted` modes), keeping `max|N|` + `|N|/floor` as columns; `plot_pair.py`
  gained the multiplicative-prediction curve, an `Nmult` residual panel, and a
  `--shifted` two-pickle mode. **Subtlety this exposed (see Results): TNP×TNP raw `N`≈0
  (machine precision) — the truth is ADDITIVE (level0 TNPs are linear), but the
  log_normal fit applies them multiplicatively → it OVER-couples by ≈floor (`Nmult`≈floor
  ≤0.05%). Raw `N` hid this entirely.**
- **2026-06-16** — **αs×{λ,TNP} scaffolding BUILT (ready to run).** Confirmed the
  αs run pattern from the repo: CT18Z `alphasRange="002"` → ±0.002 around 0.118 →
  members `as0116`/`as0120`, central `as0118` (`rabbit_theory_helper.add_pdf_alphas_variation`,
  L1196-1202); the fit moves the **PDF member with αs** (PDFs fit at fixed αs) and
  rescales the ±0.002 template to a 0.0015 prior when αs is a constrained nuisance
  (`target_variation = 0.002 if noi else 0.0015`) — a scale on N, not a shape. The
  αs-series LHAPDF sets `CT18ZNNLO_as_011{6,8}/_as_0120` **and** their SCETlib
  `..._beamfunc` tables are already on disk → no beamfunc regen. Built:
  `runcard_xterm_asUp.ini` (αs=0.120, `pdf_set=CT18ZNNLO_as_0120`) +
  `runcard_xterm_asDn.ini` (0.116, `_as_0116`), both pointing at the new
  `variations_singles.conf` (central+15 singles, NO pairs — `gen_variations.py
  --singles-only`; indices match the full card so `xterm_index.json` is reused).
  `analyze_xterm.py` got a `--shifted <pklB> --xlabel <name>` two-pickle mode:
  `N(X×v)=R(X,v)−R(X)−R(v)`, all R vs Run A central, prints the trivial
  `R_X·R_v` floor (additive metric always shows it → genuine non-factorization is
  `|N|≫floor`). **One Run B covers αs×λ AND αs×TNP.** Singular-only rigorous
  (cancellation rule). TO RUN (singularity shell, from `prod/scetlib_run/`):
  `python scetlib-run-qT.py <threads> 1 xterm_validation/runcard_xterm_asUp.ini --point-spectrum --live`
  then `python xterm_validation/analyze_xterm.py xterm_validation/runcard_xterm_pointspec.pkl
  --shifted xterm_validation/runcard_xterm_asUp_pointspec.pkl --xlabel alphaS_up --qtmax 40`.
- **2026-06-16** — **TNP variation sizes validated against the fit.** Our card
  uses ±1 for `gamma_cusp/gamma_mu_q/gamma_nu/h_qqV/s` and ±0.5 for the 5 beam
  TNPs — exactly `theory_variation_labels.TNP_UNCERTAINTIES`. `--scaleTNP` default
  = 1 (no rescaling). So TNP sizes match the analysis. (Still confirm the live fit
  command doesn't override `--scaleTNP`/`--scaleNPLambda4`.)
- **2026-06-16** — **λ excursion caveat (open).** The λ "up" shifts are +1σ of the
  `param_model.py` priors: λ2,λ4 +0.5; λ2_nu +0.10; **δλ2 +0.2** (flagged in-code
  as "wide default, no theorist value"); **λ4_nu +0.10** (no σ defined — a guess).
  `theory_variation_labels.py` suggests δλ2 ≈ ±0.02 (10× smaller). Since δλ2 drives
  the LARGEST λ×TNP cross-terms (`δλ2×b_qqV` = 0.84%), the λ×TNP *magnitude* is
  uncertain at the ~10× level pending the fit's real `prior_sigmas`. TNP sizes are
  solid; λ excursions are not yet (TODO below).
- **2026-06-16** — Card scope: run **λ×TNP + TNP×TNP** singular-only. These are
  rigorous from the singular alone: the nonsingular is FO → carries no NP and no
  resummation TNPs (SCETlib *throws* if TNPs are set at FO), so it cancels in
  `N`'s numerator. Full-prediction cross-term = `N_sing × σ_sing/σ_full ≤ N_sing`.
  No nonsingular run, no guessing. Scales/PDF/αs deferred (see TODO).
- **2026-06-16** — λ×λ KEPT as a **methodology parity check** (positive control):
  they are known non-factorizable (the reason the param model exists), so the
  metric MUST show them clearly non-zero. In the fit they're handled exactly by
  the param model → not a fit-relevant cross-term, just a validation of the method.
- **2026-06-16** — NP model = **tanh_2** (up to λ4, no λ6 / no hardcoded λ6_nu),
  matching the fit's floated CS params {lambda2_nu, lambda4_nu, lambda_inf_nu}.
- **2026-06-16** — "No guessing" on the nonsingular: SCETlib `full`+resummation is
  disallowed and its nonsingular is NLO-only; the analysis uses the **DYTurbo**
  NNLO nonsingular. So we do NOT use an NLO-SCETlib proxy; matched runs (where
  needed) use the DYTurbo nonsingular. → `nons/` and `runcard_xterm_full.ini` are SUPERSEDED.
- **2026-06-16** — `lambda6_nu` build mismatch: `config.py:114` / `variations.py:324`
  set `model_nu.lambda6_nu` but the compiled `NPModelGammaNu` has no setter
  (hardcoded 0.0007). Guarded both with `hasattr` (no-op once a build exposes it;
  tanh_2 doesn't use λ6_nu anyway).

## SUMMARY — complete cross-term map (2026-06-16)

Worst-case fit-missed cross-term `max|Nmult|` (qT≤40), i.e. what rabbit's
multiplicative (log_normal) linear-template model misses. All pairs among the
{λ, TNP, αs, PDF} fit-nuisance families are DONE and singular-only **rigorous**
(cancellation rule):

| pair | `max|Nmult|` | note |
|---|---|---|
| λ×λ | 5.5% | **exact via param model — NOT a fit error** (benchmark) |
| λ×PDF (Hess-comb) | **0.84%** | largest linearized; eig 19/22 (memb 38/44) dominate |
| αs×λ | 0.69% | δλ2 (caveat); λ2 0.31% |
| λ×TNP | 0.26% | δλ2×b_qqV; λ2×b_qqV 0.13% |
| PDF×TNP (Hess-comb) | 0.26% | b_qg |
| αs×TNP | 0.18% | b_qqV |
| TNP×TNP | 0.05% | truth ADDITIVE, fit multiplicative → over-couples by ≈floor |

**Bottom line:** every linearized cross-term ≤0.84% worst-case *shape*, all at the
low-qT/high-Y/off-Z-peak corner, all a factor of **~3–8× below** the λ×λ effect
handled exactly by the param model. NOT "order of magnitude" — "a factor of a few."
**Caveats:** worst-case shape, NOT yet σ-weighted/ptll-binned (the capstone TODO);
δλ2 prior ~10× uncertain; αs is asUp only; Hess-comb is a conservative proxy
(max-of-±/point, quadrature over 29 eigenvectors). Remaining: transition/FOscale
×{λ,TNP} (singular-only, cheap), FO×FO pairs (need DYTurbo), σ-weighted impact.

## Results

- **2026-06-16** — **σ-weighted αs-projected IMPACT metric (`impact_xterm.py`).**
  `δαs = Δαs·⟨Nmult,R_αs⟩/⟨R_αs,R_αs⟩`, weight = central yield (σ×cell-vol), `R_αs`
  from asUp, Δαs=0.002. Single-parameter linear gen-level UPPER-BOUND screen (real
  profiled+reco fit smaller). **Family totals (% of ref σαs=0.001, qT≤40):** λ×λ **30%**
  (control, see below) ≫ PDF×λ **11%**, αs×λ **10%**, λ×TNP 6%, PDF×TNP 4%, αs×TNP 2%,
  TNP×TNP 0.5%. Leading single rows: λ2×δλ2 (control) 27.5%; then PDF×δλ2 7.9%, PDF×λ2 7.8%,
  αs×δλ2 7.3%, αs×λ2 6.5%. **Not ≪1% → NOT trivially negligible at screen level.**
  σ-weighting moved the action off the qT=0.2 corner onto mid-qT/Z-peak (real overlap).
  Gating: (1) real σ(αs) [table scales 1/σαs]; (2) δλ2 prior [top rows ~10× uncertain →
  robust leader λ2×{PDF,αs} ~7%]; (3) upper bound (profiling+reco+coarse-Q shrink it).
- **2026-06-16** — **λ×λ CONTROL for the impact metric (`--with-ll`) — PASSES.** λ×λ
  tops everything (family 30%, λ2×δλ2=27.5%), as it must (most non-factorizable, the
  param-model raison d'être) → metric calibrated, not deflating. Quantifies the param
  model's payoff: linearizing λ×λ would bias αs ~0.3σ; the param model removes it exactly
  (zero in the fit). Sobering: non-δλ2 λ×λ pairs (λ2nu×λ2 5.7%, λ2×λ4 4.5%) are
  COMPARABLE to the linearized PDF×λ/αs×λ leaders → the assumed-factorized cross-terms
  are in the same screen-level ballpark as the one we model exactly. → motivates the
  closure test (folds in profiling/smearing that suppress the upper bound).
- **2026-06-16** — **PDF×TNP — ALL 58 members (qT≤40), `Nmult`.** Smallest block:
  Hess-combined ≤ **0.26%** (b_qg, memb 57), b_qqV 0.13%, s 0.07%, rest <0.05%;
  b_qqDS = 0 (null direction — its single response vanishes, as in TNP×TNP). Member 38
  again dominates most knobs. Well below λ×PDF and λ×TNP. (Fixed an `analyze_pdf_xterm.py`
  crash on null knobs: `wmemb=None` → format guard.)
- **2026-06-16** — **λ×PDF — ALL 58 CT18Z members (qT≤40), `Nmult`.** Per-member
  worst single = ~0.2–0.33% (λ2, member 38) — same sub-% scale as λ×αs.
  **Hessian-combined** (quadrature over all 29 eigenvector pairs): δλ2 = **0.84%**
  (qT=8,Y=3,Q=80), λ2 = **0.54%**, λ2_nu = 0.39%, λ4_nu/λ4 = 0.31%. Coupling
  CONCENTRATES in a couple of eigenvectors — member 38 (eig 19, − side) dominates
  4/5 knobs, member 44 (eig 22, −) the δλ2 one — not spread across the Hessian.
  **λ×PDF-combined is the LARGEST linearized cross-term** (slightly > λ×αs), but
  still ~3× (robust λ2) – ~6× (δλ2) below the λ×λ effect handled exactly by the
  param model. "Order of magnitude" does NOT apply here — "a factor of a few below
  λ×λ." Hess-comb is a conservative proxy (max ±/point, quadrature); worst-case
  SHAPE, not yet a σ(αs) bias. PDF×TNP available from the same runs (drop --kind).
- **2026-06-16** — **αs×{λ,TNP} (Run B asUp, qT≤40), re-read through `Nmult`.**
  Pure αs(+0.002, matched PDF member) response: max|R_X| = 2.69%. Fit-missed
  cross-term `max|Nmult|` (the log_normal fit's error): **δλ2×αs = 0.69%** (qT=8,Y=3,Q=80;
  ~10× excursion caveat), **λ2×αs = 0.31%**, λ2_nu×αs = 0.20%; TNP side small
  (b_qqV×αs = 0.18%, s×αs = 0.15%, γ_ν×αs = 0.10%, rest <0.05%). All at the
  low-qT/high-Y/off-peak corner. `|N|/floor` ≈ 1.8–5.4 for these → truth is MORE
  coupled than multiplicative (real coupling, fit misses ≈ the residual). **αs×λ is
  the largest fit-relevant cross-term block measured.** Still TODO: σ-weight + bin
  into the fit's ptll grid (peaks at single low-qT points → dilutes), run asDn for
  the ± symmetry, confirm δλ2 prior.
- **2026-06-16** — **λ×TNP / TNP×TNP re-read through `Nmult`.** λ×TNP fit-miss
  `max|Nmult|` ≤ 0.26% (δλ2×b_qqV; caveat) / ≤0.13% (λ2×b_qqV, robust): the
  multiplicative fit captures most of the old `max|N|`≤0.84%, leaving the small
  residual. **TNP×TNP: raw `N`≈1e-9–1e-15 (machine zero) → the true SCETlib level0
  combination is ADDITIVE, NOT multiplicative.** But the log_normal fit multiplies
  them, introducing a spurious `R_a·R_b` → `max|Nmult|` ≤ 0.052% (s×b_qqV). Small, but
  a *systematic* direction (fit always over-couples TNP×TNP). Open question for the
  analysis: whether the SCETlib TNPs (additive by construction) would be better entered
  as `--systematicType normal`; log_normal keeps yields positive, and 0.05% is tiny, so
  not pursued — flagged only. λ×λ control: `max|Nmult|` up to 5.5% (handled EXACTLY by
  the param model → not a fit cross-term, just validates the metric).
- **2026-06-16** — First singular-only pass (incl. scales, 228-pt grid):
  **λ×TNP cross-terms ≤ ~0.7% in the fit region; γ_ν×λ_ν ≈ 0.1%** — small.
  High-qT (qT≈Q) entries are singular-only artifacts (singular extrapolated past
  validity; `X-Math max_iterations` warnings) → ignore. λ×TNP factorizes well;
  the full prediction is at least as clean.
- **2026-06-16** — λ×TNP + TNP×TNP card (121 vars incl. λ×λ control, sing-only,
  qT≥0.2). **Parity check PASSES:** λ×λ control lights up at the top
  (`lambda2×delta_lambda2` = 8.3%, block 0.5–8.3%) — ~10× the worst λ×TNP
  (0.84%) and ~240× the worst TNP×TNP (0.034%). So the small λ×TNP / TNP×TNP are
  GENUINE factorization, not a blind metric. All peak at qT=0.2/Y=3/off-peak Q;
  ordering physical (δλ2 is the Y² modifier of λ2 → `λ2×δλ2` biggest).
  γ_ν×λ_ν = 0.11%. **Conclusion: λ×TNP and TNP×TNP factorize at the sub-percent
  level; full prediction at least as clean (singular-only rigorous here).**
  Remaining to make it a Δσ(α_s) statement: the σ-weighted impact metric (TODO).
- **2026-06-16** — **Pipeline validated against the old `scetlib-np-linearity.py`
  plot.** Re-ran OUR point-spectrum setup with the OLD variations
  (`lambda2:0→1.0`, `lambda4:0→1.0`; `runcard_lval.ini`/`variations_lval.conf`/
  `lval_index.json`). At Q=91 Y-avg the single `lambda2^up/nominal` peaks **+5.7%
  at qT≈8** — lands exactly on the old plot — and `N(λ2×λ4)` reproduces the old
  oscillation (+10% low-qT → −3.6% dip at qT≈4–5 → +1% at qT≈8 → 0 by ~15).
  max|N| = 16.6% (Y=3,Q=80 corner) vs 1.9% at 0.4→0.9 — the ~9× is *entirely*
  the excursion (0→1.0 from NP-off vs 0.4±0.5 at the fit point). Confirms the
  small λ×TNP numbers are real, not a blind metric.
- **2026-06-16** — `plot_pair.py` added: reproduces the old 2-panel view
  (σ_var/σ_nom for a, b, combined + linear prediction; bottom = residual N) vs qT
  for ANY pair, from our pickle. Verified `lambda2 × b_qqV` at its peak bin
  (Q=80, Y=3): max|N| = 0.40% at qT=0.2, same oscillation shape as λ×λ scaled
  ~25× down → the analyzer row checks out. Plot copied to webdir
  `public_html/alphaS/260616_scetlib_np_factorizability/`.

## Open items / TODO

- [ ] **Scales** (resummation `muB/nuB/muS/nuS`) × λ/TNP — deferred. NB: with
      `--resumUnc tnp` these are NOT fit nuisances (TNPs replace them) → informational only.
- [ ] **`resumTransitionZ` × {λ, TNP}**: by the cancellation rule these are
      **singular-only rigorous** (λ/TNP factor → nonsingular cancels) — NO DYTurbo
      (corrects an earlier note). `transition_points` is a variation-card key, so
      these can just be added to the main card. Use the fit's values
      `[0.2,0.75,1.0]` / `[0.2,0.35,1.0]`.
- [ ] **`resumFOScaleZ` × {λ, TNP}**: also singular-only rigorous; the only snag is
      reproducing the `renorm_scale_pt20_envelope` (a composite, not a single SCETlib
      knob). Only transition×FOscale / ×αs / ×PDF would need the matched nonsingular.
- [x] **PDF × λ — DONE** (all 58 members via `--pdf-member` loop; one runcard, NOT
      per-member). See Results. Hess-combined ≤0.84%.
- [x] **αs × λ — DONE** (asUp; Run B = αs0.120 + matched member). αs×TNP came free
      from the same run. TODO: asDn for ± symmetry (optional).
- [x] **PDF × TNP — DONE** (same 58 pickles, `--kind tnp`). Hess-combined ≤0.26% (b_qg).
- [ ] **FO×FO pairs needing DYTurbo nonsingular** (cancellation rule does NOT apply —
      both factors hit the nonsingular): αs×PDF-eigenvector, transition×{αs,PDF,FOscale}.
      The dominant αs×PDF *correlation* is already folded into the αs run (matched member);
      this is the residual eigenvector-level coupling. Separate work package.
- [ ] **tanh_6 (Lattice card)** variant: re-run if the analysis uses the Lattice
      NP card (`gen_variations.py --model tanh6`).
- [ ] **σ-weighted (fit-impact) metric** in `analyze_xterm.py`: weight `N` by the
      central spectrum → "biases σ(αs) by < Y%" alongside worst-case `max|N|`.
- [ ] **Confirm λ prior σ's** — the fit's real `prior_sigmas`, not the
      `param_model.py` wide defaults. Esp. **δλ2** (we used 0.2; may be 0.02 →
      ~10× smaller λ×TNP) and **λ4_nu** (we used 0.10, a guess). This sets the
      λ×TNP *magnitude*; TNP sizes are already confirmed.

## NEXT — remaining work (the {λ,TNP,αs,PDF} cross-term MAP is COMPLETE; see SUMMARY)

In priority order:

1. **σ-weighted / αs-projected impact metric — the CAPSTONE.** Convert worst-case
   shape `Nmult` → bias on the *measured* σ(αs): `δαs ≈ ⟨Nmult, R_αs⟩ / ⟨R_αs, R_αs⟩`,
   σ-weighted by the central spectrum. Ingredients already in hand: central spectrum
   (Run A var-0), αs response `R_αs` (asUp var-0), all `Nmult`. **No new SCETlib runs.**
   Turns "0.5–0.84% shape at qT=0.2" into "biases σ(αs) by < X%" — the number for the
   meeting. (Will collapse the worst-case corners, which carry little αs sensitivity.)
2. **transition (`resumTransitionZ`) × {λ,TNP} and FOscale (`resumFOScaleZ`) × {λ,TNP}** —
   the other two fit-nuisance families. Singular-only RIGOROUS. transition is easy
   (`transition_points` is a variation-card key → add to the singles card; fit values
   `[0.2,0.75,1.0]`/`[0.2,0.35,1.0]`); FOscale needs reproducing the composite
   `renorm_scale_pt20_envelope`.
3. **FO×FO pairs** (αs×PDF eigenvector-level, transition/FOscale ×{αs,PDF}, transition×FOscale)
   — need the DYTurbo nonsingular (cancellation rule does NOT apply). Heavier, separate.
4. Optional: αs **asDn** for ± symmetry; confirm λ `prior_sigmas` (δλ2/λ4_nu); tanh_6 Lattice card.

## Files (`xterm_validation/`)

- `WORKFLOW.md` — generic SCETlib→fit workflow (corrections vs param model, bin vs point
  mode, the gen→reco R "bridge") + the cross-term→αs-bias plan (Fisher attribution + point-mode closure).
- `CLOSURE_LOGBOOK.md` — the follow-on closure study (gen-level via feedRabbitSigmaUL; inject
  non-factorized truth, fit factorizing model, read αs pull). This LOGBOOK = shape; that = fit impact.

- `gen_variations.py` — generates the variation card + index (`--model tanh2|tanh6`).
- `variations_xterm.conf` / `xterm_index.json` — the λ×TNP + TNP×TNP card.
- `runcard_xterm.ini` — singular-only point-spectrum runcard (`run_order=n3ll`, `piece=sing`).
- `analyze_xterm.py` — `N`, `floor`, **`Nmult`** per pair (sorts by max|Nmult|);
  pairs mode + `--shifted <pklB> --xlabel` two-pickle αs/PDF mode (`--qtmax/--kind/--top/--csv`).
- `plot_pair.py` — 2-panel (σ_var/σ_nom with multiplicative + linear predictions; bottom =
  `N` and `Nmult` vs qT) for any pair (`--a --b --Q --Y`); `--shifted <pklB> --xlabel` for αs/PDF.
- `variations_singles.conf` — central + 15 singles (Run B for αs/PDF; `gen_variations.py --singles-only`).
- `runcard_xterm_asUp.ini` / `runcard_xterm_asDn.ini` — αs±0.002 + matched CT18Z member (Run B).
- `runcard_xterm_singles.ini` — nominal-`[QCD]` singles runcard; loop `--pdf-member N` for λ×PDF
  (one runcard, NOT 58) → `runcard_xterm_singles_pdf{NN}_pointspec.pkl`.
- `analyze_pdf_xterm.py` — aggregate all PDF-member pickles → per-knob worst-single-member +
  Hessian-combined cross-term (`--kind lambda|tnp`, `--qtmax`); glob `*_pdf<N>_pointspec.pkl`.
- `runcard_xterm_pointspec.pkl` — singular-only results (main card).
- `xterm_N.csv` — per-point N table for the main card.
- `runcard_lval.ini` / `variations_lval.conf` / `lval_index.json` / `runcard_lval_pointspec.pkl`
  — parity check vs the old plot (λ2,λ4 = 0→1.0).
- `runcard_xterm_full.ini`, `nons/` — SUPERSEDED (full+resum disallowed; use DYTurbo).
- webdir: `~/public_html/alphaS/260616_scetlib_np_factorizability/` (plots).
