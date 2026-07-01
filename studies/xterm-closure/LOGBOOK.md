# Cross-term closure study — logbook

Turning the factorizability finding into a **fit-level α_s bias**: inject a
non-factorized truth (cross-terms baked in) as pseudodata, fit with the standard
*factorizing* model, read the α_s pull. Companion to `LOGBOOK.md` (the cross-term
*shape* study) and `WORKFLOW.md` (how the pieces connect).

**Goal.** Answer "by how much does the linear/multiplicative treatment of α_s/PDF/TNP
× λ non-factorization bias the measured α_s?" — the real profiled number, not the
analytic screen (which gave ~10–11% of σ(α_s) as a single-parameter upper bound).

---

## START HERE — current state & next action

The whole gen-level pipeline (point-mode SCETlib → converter → make_theory_corr →
feedRabbitSigmaUL → rabbit_fit) is BUILT, and the **λ×λ αs+λ-only worst-case** parity fit is wired.
(Full details newest-first in Decisions. Companions: `WORKFLOW.md` Part C, `LOGBOOK.md` SUMMARY.)

- ✅ Parity SCETlib run (point mode, validated btgrid grid, tanh_2) → `runcard_parity_pointspec.pkl`
     (10 vars: central + 8 single-λ + joint).
- ✅ Converter `wremnants/postprocessing/scetlib_np/point_to_binned.py` (validated).
- ⚠️ TRUTH correction `scetlib_dyturbo_parity_LxL_truth_CorrZ.pkl.lz4` — built, but `_hist` was
     **`Double` storage → REGENERATING** (converter Double→Weight fix; see newest Decision).
- ✅ `feedRabbitSigmaUL` + `theory_fit_writer` edited for the αs+λ-only fit — **TEMPORARY parity
     hacks**, unconditional, marked `revert later`. (Converter `point_to_binned.py` now emits Weight.)
- ▶ **NEXT: (user running) converter → re-run make_theory_corr → copy CorrZ to wremnants-data →
     re-run feedRabbitSigmaUL → `rabbit_fit` → read the αs pull.**

**This is Fit A (αs + λ only, WORST CASE):** templates = our single-λ (from the truth corr) +
**borrowed** αs (`scetlib_dyturbo_LatticeNP_CT18Z_N3p0LL_N2LO_pdfas`); pseudodata = the joint-λ var
(`--pseudodataVariation`); float αs (NOI) + λ, nothing else (PDF/TNP omitted → αs absorbs the full
λ×λ residual → pull ≥ realistic). Expected ≈ tens-of-% of σ (screen `--with-ll` λ×λ ~30% is the bound).

**Then:** (a) full-nuisance fit (realistic profiled bias; the Fit-A→full drop = profiling suppression);
(b) **Fit B** = param-model λ (needs `param_model.py` `gen_level` flag, code change 1, NOT yet done);
(c) **revert the TEMPORARY parity hacks**; (d) cross-GROUP closures (αs×λ, PDF×λ — reproduce pdfas/pdfvars
at our λ then). Truth config + per-eigenvector PDF strategy: see the 2026-06-17 "Step-(1) truth config".

---

## Plan (gen-level, point-mode, no histmaker)

```
point-mode SCETlib (SIMULTANEOUS variations across groups)
  → [converter: pack σ@bin-centers → {hist, bins}]      (issue 1, to write)
  → make_theory_corr.py            → TRUTH gen TheoryCorrection (cross-terms baked in)
  → feedRabbitSigmaUL.py   --pseudodataGenerator=TRUTH ;  templates = nominal corr + param model(λ)
  → rabbit_fit             → α_s pull = gen-level theory bias
```
All gen-level (unfolded σUL), all fast point mode. The param model's only role is its
normal one (continuous λ on the fly). Inject all cross-terms at once → net bias (1 fit);
inject one FAMILY at a time → per-group attribution (~6 fits, only screen-flagged ones).

**NOTE — the CURRENT step (λ×λ Fit A, worst case) deviates from this diagram:** no param model;
templates = our binned single-λ (from the truth corr) + borrowed αs; pseudodata = the joint-λ
var of the SAME truth correction (not a separate file). The param-model path above is Fit B /
the cross-group closures.

---

## Decisions (newest first)

- **2026-06-19** — **TNP×λ sweep: 3/10 done (all αs≈0), 4th (`s`) HUNG in the minimize → killed.**
  Results so far (all `pdfAlphaS` central ≈ 0, ±1.33; `resumTNP_<t>` stayed ~0 ⇒ free λ absorbed them —
  all CS-side/anomalous-dim, degenerate with λ, like γ_ν):
    - gamma_nu    pdfAlphaS −0.00072 ± 1.335
    - gamma_cusp  pdfAlphaS +0.004   ± 1.335
    - gamma_mu_q  pdfAlphaS +0.0069  ± 1.335
  **`s` (soft fn) HUNG:** ~41 min, 0 log lines after `Compiled cluster using XLA!` (the 3 others took
  ~4 min with full post-fit output), 4012 threads on 78 cores, burning CPU but not progressing.
  ROOT CAUSE = stuck in the `trust-krylov` minimize (NOT the Hessian): `s` is the first TNP NOT cleanly
  absorbed by free λ, so the minimize hits an ill-conditioned/near-flat landscape and trust-krylov's inner
  Krylov solver grinds (+ TF thread oversubscription). Killed via `pkill -f run_tnpxlambda_sweep.sh`.
  **NEXT (fix before re-running s / h_qqV / b_qqV/b_qqbarV/b_qqS/b_qqDS/b_qg):** the hard fits need help —
  options to try: (a) `--noHessian` (cheap, in case any Hessian cost compounds); (b) a different/ more
  robust minimizer or an iteration/tolerance cap (trust-krylov chokes on the degenerate landscape);
  (c) cap TF threads (`OMP_NUM_THREADS`/TF intra-op) to kill the 4012-thread thrashing; (d) since these
  loose degenerate fits only need the αs CENTRAL, a looser convergence tol is fine. Pattern hint: the
  CS-side TNP (γ_ν/cusp/μ_q) are all αs≈0 (λ-absorbed); the ORTHOGONAL ones (s, b_*) are both the harder
  minimizes AND the genuine cross-term tests (free λ can't absorb → resumTNP must activate). Tensors for
  all are already built (`tnpxl_<t>_…hdf5`); the correction has all 22 vars — NO new SCETlib/feedRabbit
  needed, just re-fit s/h_qqV/b_* once the minimizer is sorted. Sweep script + per-fit log:
  `run_tnpxlambda_sweep.sh` / `tnpxlambda_sweep.log`.

- **2026-06-19** — **Finishing the TNP×λ sweep (user) — script `run_tnpxlambda_sweep.sh`.** Decided to do
  the 9 remaining TNP (cheap: NO new SCETlib run, the correction already holds all 10 templates+truths).
  WHY worth it (not just rubber-stamping γ_ν): γ_ν passed only because it's degenerate with lambda2_nu
  (free λ absorbed it). The b_* beam-function + gamma_cusp/h_qqV TNP are largely ORTHOGONAL to the λ sector
  → free λ can't absorb → their template must activate → genuine cross-term test where αs could actually
  move. Script: per TNP, feedRabbit (`--npTemplates <t> --pseudodataVariation <t>_lambdaJ
  --outname tnpxl_<t>`) → rabbit_fit (`-t 0 --unblind --paramModel …gen_level=1 lambda_central=…json
  nonsingular_*=<dw> --freezeParameters lambda_inf lambda6 lambda4_nu lambda_inf_nu`) → print pdfAlphaS +
  resumTNP_<t>. READ: pdfAlphaS central = the bias; resumTNP_<t>→~+1 = activated (genuine test), ~0 = λ
  absorbed. Run: `bash xterm_validation/run_tnpxlambda_sweep.sh 2>&1 | tee …sweep.log`.

- **2026-06-19** — **FRAMING (first-principles, with user): what the closure fits establish.** GOAL =
  validate the factorizing-template treatment of SCETlib theory nuisances doesn't distort αs (NOT a math
  factorization proof — settle a systematic). The fit measures the EFFECT (αs shift) vs N_mult tables
  measuring the CAUSE (spectrum cross term); the fit is the FAITHFUL one because it accounts for PROFILING
  (nuisances float & absorb): λ×λ fit gave BIGGER bias (+0.58) than the screen (~30%) [table under-stated];
  γ_ν×λ fit gave ~0 [free λ absorbed]. The "free λ absorbs the partner" short-circuit is NOT a cheat — in
  the real fit λ float, so if a nuisance's non-fact gets soaked by λ and never reaches αs, the template is
  ADEQUATE for measuring αs (we don't measure λ). ESTABLISHED: method works (caught λ×λ decisively → a "≈0"
  from it is meaningful); γ_ν×λ no bias, robust. LIMITS (honest): gen-level + tiny-cov ⇒ loose αs (±1.34) ⇒
  pins CENTRAL bias not a tight upper bound; "negligible" for non-λ rests on triangulation (small N_mult +
  central αs≈0 + free-λ-absorbs robustness); tested one nuisance at a time at its template value (no
  multi-nuisance joints, no single-param nonlinearity — both higher-order/smaller). GAP: the
  free-λ-absorbs argument FAILS for **αs×λ** (partner is the POI, a direction λ can't soak up) → the one
  cross term that can still bias αs; the screen's ~10% most plausibly lives there. PLAN to close the
  systematic: do αs×λ; then write up "λ needs param model; other sectors negligible for αs (N_mult +
  closure fits)."

- **2026-06-19** — **RESOLVED: γ_ν×λ does NOT bias αs (αs central = −0.0007); data-cov path DROPPED.**
  User: we only care whether αs is biased, not measuring λ/TNP. Agreed + the no-bias conclusion is ROBUST
  (not a loose-fit artifact): (a) the CENTRAL αs (−0.0007) is the bias; the ±1.34 is constraining power, a
  separate thing; (b) free λ reproduce the γ_ν↑ data ~exactly (γ_ν↔lambda2_nu degenerate → λ absorbs it) →
  χ²≈0 AT αs≈0, and χ²=0 is the global min for ANY covariance, so the real data cov would NOT move the
  central → the data-cov machinery is unnecessary HERE. ⇒ **drop the real-data-cov build for this.**
  Other 9 TNP: integrated cross terms ALL ~1e-5 + TNP generically degenerate with NP λ → whole TNP×λ class
  very likely negligible; accept on γ_ν + that evidence (sweep optional). **CAVEAT — αs×λ / PDF×λ are NOT
  obviously safe:** the "free λ absorbs the partner" argument FAILS for αs×λ (the partner IS the POI, a
  distinct direction λ can't soak up) → a real αs pull can survive; the screen's ~10% likely lives there.
  NEXT (if continuing): set up αs×λ (separate αs-shifted runcard per §8) ± a lead PDF eigenvector; else
  close the cross-term study.

- **2026-06-19** — **CORRECTION (user): the λ have NO physics priors in the real analysis — they float
  FREE (no lattice/theory constraints). My `priors=1` recommendation was WRONG; RETRACTED.** Implications:
  (1) free λ IS the realistic treatment → the γ_ν×λ free-λ fit (αs=−0.0007±1.34) is the right λ config,
  NOT short-circuited by a missing prior. (2) The thing that pins free λ (and breaks the γ_ν↔lambda2_nu
  degeneracy) in the real fit is the **real unfolded-σUL DATA COVARIANCE** (→ σ(αs)=0.547), NOT priors.
  We feed a tiny theory-MC-stat cov → degeneracy unbroken → αs loose (±1.34), λ absorb γ_ν. (3) So αs≈0 is
  SUGGESTIVE (γ_ν×λ small, consistent w/ ~1e-5 integrated cross term + screen) but NOT tight. **Proper
  lever = real data covariance** (hybrid: inject theory-truth central + use measurement cov; feedRabbit
  `--infile` reads `hist_postfit_inclusive_cov` but also takes that file's data → needs a hybrid path).
  Fixed CLOSURE_WORKFLOW.md §8.1 (removed "match the analysis priors" → "no λ priors; use the data cov").
  OPEN DECISION for user: (1) build the real-cov path (proper, more work) vs (2) accept "TNP×λ ≈ 0,
  loosely" from free-λ fits and sweep the rest cheaply.

- **2026-06-19** — **First TNP×λ fit (γ_ν, FREE λ): αs = −0.0007 ± 1.34 ≈ 0, but free-λ MASKED the test.**
  [SUPERSEDED framing: "free-λ masked the test, re-run priored" — WRONG, λ are free in the real analysis;
  see the correction above. The free-λ fit IS realistic; what's missing is the real data covariance.]
  Result: λ2 0.898, λ4 0.888, λ2_nu 0.293, δλ2 0.0198 (≈toward joint truth), **pdfAlphaS −0.0007 ± 1.34**,
  **resumTNP_gamma_nu 0.0019 ± 0.999 (stayed at ~0, did NOT activate to +1)**. KEY: γ_ν (TNP) is nearly
  DEGENERATE with `lambda2_nu` (param-model NP γ_ν) — both shift CS rapidity evolution. With λ FREE, the
  fit absorbed γ_ν↑ into lambda2_nu (→0.293, past truth 0.25) rather than the PRIORED γ_ν nuisance (free
  λ cheaper) → cross term absorbed by λ, αs never saw it. Huge λ errors (λ4 ±11, λ2 ±2.3) + loose αs (±1.34)
  confirm degeneracy. ⇒ **free-λ αs≈0 is necessary but NOT sufficient** (test short-circuited). Real
  analysis PRIORS λ → lambda2_nu can't freely eat γ_ν → γ_ν nuisance engages → only then can a γ_ν×λ
  residual leak to αs. **NEXT: re-run with `priors=1 prior_sigmas=delta_lambda2=0.02` (realistic + the
  proper test); expect resumTNP_gamma_nu→~+1, tighter λ, αs = the real γ_ν×λ bias.** GOOD: the freeze WORKED
  (lambda_inf/lambda_inf_nu now ±0 — G5 space-sep fix confirmed). Lesson (free-vs-priored λ) applies to the
  whole TNP sweep.

- **2026-06-19** — **feedRabbit TNP-template wiring DONE (one-at-a-time, mirrored).** Correction
  `scetlib_dyturbo_tnpxlambda_truth_CorrZ.pkl.lz4` verified (Weight, 22 named vars incl. `gamma_nu` +
  `gamma_nu_lambdaJ`). Added: (1) writer method `add_np_template_variations(var_names)` — mirrored
  template nuisance per var, named `resumTNP_<var>` (NO `scetlibNP` substring → doesn't trip the param
  model's double-count guard; it's orthogonal to λ), groups=[resumTNP,resum,pTModeling,theory,theory_qcd];
  (2) `--npTemplates` arg (nargs+, functional value-arg); (3) main: COMMENTED OUT
  `add_resummation_and_np_variations` (param-model-λ state — λ comes from the model at fit time) + added
  `writer.add_np_template_variations(args.npTemplates)`. py_compile clean. RUN (per TNP, swap the var):
  feedRabbit `--predGenerator scetlib_dyturbo_tnpxlambda_truth --pseudodataVariation gamma_nu_lambdaJ
  --npTemplates gamma_nu --alphasGenerator …_pdfas` → rabbit_fit `-t 0 --unblind --paramModel
  …SCETlibNPParamModel gen_level=1 lambda_central=lambda_central_parity.json nonsingular_*=<dw>
  --freezeParameters lambda_inf lambda6 lambda4_nu lambda_inf_nu`. αs pull = the γ_ν×λ bias;
  resumTNP_gamma_nu→~+1. (lambda_central reused — TNP×λ run shares the tanh_2 central.) This is the first
  slice of the §9 hacks→flags refactor (λ-template line still a manual comment toggle for Fit A). `runcard_tnpxlambda_pointspec.pkl`
  (983 MB, 22 vars × 558360 pts) produced. **NAMING BUG (now §10 G8):** combined TNP+λ blocks [12–21] all
  got auto-named `lambda2_nu0.25-...` (TNP dropped from the name) → collided with [1]. PHYSICS FINE: per-var
  metadata confirms e.g. [12] = gamma_nu=(1.,'level0') + joint-λ; additive check σ(g↑,λJ)≈σ(λJ)+[σ(g↑)−σc]
  holds to ~1e-5 for all 10 → block order verified. Fixed by rewriting `d["vars"][k]["name"]` by block index
  → `runcard_tnpxlambda_pointspec_named.pkl` (names: central, lambdaJ, 10 TNP, 10 {TNP}_lambdaJ). PRELIM hint:
  TNP×λ cross term tiny at INTEGRATED level (~1e-5 non-factorization) → likely small αs bias, but the shape+αs
  projection (the fit) decides. NEXT: converter on the _named.pkl → make_theory_corr (-p tnpxlambda_truth) →
  feedRabbit. feedRabbit needs a TNP-template path (writer hard-codes the 4 λ) = §9 refactor piece.

- **2026-06-19** — **TNP×λ run SET UP** (first cross-GROUP closure). Created two files in `xterm_validation/`:
  `runcard_tnpxlambda.ini` (cloned from `runcard_parity.ini` — same btgrid grid, tanh_2 NP central, point
  mode — only `variations_filename` swapped) + `variations_tnpxlambda.conf` (22 blocks: [0] central, [1]
  joint-λ, [2–11] 10 TNP templates at λc, [12–21] 10 TNP×joint-λ truths). TNP magnitudes = production
  (`gamma_nu/gamma_cusp/gamma_mu_q/s/h_qqV=(1.,'level0')`; `b_qqV/b_qqbarV/b_qqS/b_qqDS/b_qg=(0.5,'relative')`);
  joint-λ = same as λ×λ study. TNP UP-only (one-sided; add 10 DOWN blocks if the fit needs a symmetric
  template). RUN: `python scetlib-run-qT.py <ncores> 1 xterm_validation/runcard_tnpxlambda.ini
  --point-spectrum --live` → `runcard_tnpxlambda_pointspec.pkl`. Heads-up: TNP vars may re-trigger the
  perturbative solve (anomalous-dim/hard/beam/soft), so slower than λ-only parity. DOWNSTREAM wrinkles:
  (a) TNP var names auto-generated by SCETlib → read from run output before feedRabbit; (b) wiring TNP
  templates into feedRabbit = part of the §9 hacks→flags refactor (writer currently hard-codes the 4 λ).

- **2026-06-18** — **Design simplification (user insight): the αs pull from fitting the genuine joint
  truth with factorizing templates IS the bias — no factorized-null needed.** If factorization held,
  individual templates would fit the joint exactly → αs=0; so any pull = the non-factorization leaking
  into αs (exactly what Fit A's +0.58 is). DROPPED the "factorized-null" control from §8.1 — it's
  redundant when templates share the truth's point run (fits to 0 by construction); the only artifact
  (param-model-λ vs point-run shape) is already bounded by λ×λ Fit B at αs=+0.002. Kept two caveats:
  (1) the pull's MAGNITUDE is config-dependent (λ priors + αs↔λ degeneracy — Fit A's λ4 ate by αs), so
  match the real analysis; (2) for cross-GROUP, fit with PARAM-MODEL λ (removes λ×λ exactly) not linear
  λ templates, else the pull mixes λ×λ + g×λ. Recipe per class: inject σ(g↑,λJ) → fit [param-model λ ⊕
  multiplicative g template], αs=NOI → pull = isolated g×λ bias. §8.1 updated.

- **2026-06-18** — **Cross-GROUP plan written into `CLOSURE_WORKFLOW.md` §8 (table + design).** Confirmed
  the SCETlib mechanics from the xterm configs: λ & TNP are `variations.conf` rows (in-place setters);
  αs & PDF feed the calc at construction → SEPARATE runcards (`[QCD] alphas_mu0` + matched `pdf_set`:
  CT18ZNNLO_as_0120/_as_0116 for αs↑/↓; `pdf_member=i` for PDF). 10 TNP pinned (gamma_nu/gamma_cusp/
  gamma_mu_q/s/h_qqV=(1.,'level0'); b_qqV/b_qqbarV/b_qqS/b_qqDS/b_qg=(0.5,'relative')). DESIGN: no "exact
  Fit B" for cross-GROUP (param model fixes λ×λ only; αs/PDF/TNP stay multiplicative) → use **test vs
  null**: inject genuine σ(g↑,λJ) → αs pull = bias; inject factorized product → αs≈0 (pipeline control);
  bias = test−null. RUNS (btgrid fine grid, NOT the coarse screen grid): TNP×λ = **1 run** (templates +
  truths, λ&TNP both rows); αs×λ = 2–3 runs; PDF×λ = N runs (CT18Z 58 members — start with 1–2 leading).
  σ_c = reuse parity central. Each class also needs the g-template built AT our λ (reproduce pdfas/pdfvars/
  TNP, not borrow). PRIORITY: TNP×λ first (cheapest), then αs×λ (build αs template at our λ; bias =
  αs(fit)−αs↑), then PDF×λ. Prereq: §9 hacks→flags refactor. (sibling of this logbook) — the reusable how-to:
  purpose (bias = αs(FitA linear) − αs(FitB param model)), pipeline diagram, input paths, exact
  commands for all 5 steps (SCETlib point run → `point_to_binned` → `make_theory_corr` → feedRabbit
  A/B → `rabbit_fit --unblind`), §8 how to extend to αs×λ/PDF×λ/TNP×λ, §9 the temporary hacks to turn
  into flags, §10 the 7 gotchas (Weight storage / blinding / lambda_central file / double-count guard /
  freeze space-sep / σ_ns-btgrid consistency / gen_level=1). `make_theory_corr` flags confirmed: `-c` =
  resum+FO-sing+DYTurbo, default `--outpath` = wremnants-data/data/TheoryCorrections (no copy needed).

- **2026-06-18** — **Observed-vs-predicted + next-steps decided.** Q1: the observed λ×λ bias (+0.58 NOI =
  0.76σ of the reduced fit, ~1.0σ vs full-analysis σ(αs)=0.547) is **~2.5–3.5× LARGER than the analytic
  screen predicted** (~30% of σ(αs) ≈ 0.16 NOI). Screen UNDER-predicted because it FIXED λ + linear
  single-param projection (pure cross-term residual only); the fit's αs↔λ4 degeneracy lets αs eat the λ4
  direction (λ4 pull 0.10 vs truth 1.0) → amplifies beyond the projection. Direction was flagged earlier;
  magnitude exceeded the ~30% "bound" → screen is triage, not a tight bound; closure fit is the trustworthy
  number. Q2 decisions: (a) NEXT cross-term classes = the cross-GROUP terms αs×λ, PDF×λ, TNP×λ (~10% screen)
  — these test a RESIDUAL multiplicative bias in the CURRENT method (param model fixes λ×λ only; αs/PDF/TNP
  still layered multiplicatively on the λ shape). Each needs the variation generated AT our λ (reproduce
  pdfas/pdfvars/TNP, NOT borrowed) so the truth carries the real cross term → more SCETlib work. (b) DOCUMENT
  FIRST: write `CLOSURE_WORKFLOW.md` (pipeline + gotchas: Weight storage, blinding offset, lambda_central
  file, double-count guard, freeze syntax space-sep, σ_ns/btgrid consistency) + turn the temporary
  feedRabbit/writer hacks into proper flags (revisits the earlier "no flags" call now the method is proven). — positive control PASSES; linear λ treatment biases αs by ≈+0.58.**
  Re-ran both with `--unblind`. Blinding offset (≈−1.42 on αs) was common & cancelled, as predicted.
  • **Fit A** (linear NP templates, old method): **αs = +0.583 ± 0.764** NOI units; λ2 0.91, λ4 **0.10**,
    λ2_nu 0.31, δλ2 0.020.
  • **Fit B** (NP param model, gen_level, λ free): **αs = +0.002 ± 0.046 ≈ 0**; λ2 0.96, λ4 **0.81**,
    λ2_nu 0.29, δλ2 0.020. (NaN unc was a BLINDING ARTIFACT — unblinded it's tight; Fit B is NOT degenerate.)
  CONCLUSIONS: (1) **Positive control passes** — param model recovers injected truth (αs≈0) → whole
  gen-level pipeline + `gen_level` validated end-to-end. (2) **Linear/multiplicative λ treatment biases αs
  by ≈+0.58 NOI units** (high); the exact param model removes it. (3) MECHANISM = αs↔λ4 degeneracy: linear
  λ4 template barely moves (0.10, αs eats it) vs param-model λ4→0.81 (αs stays). The exact nonlinear λ4
  shape is distinct from αs → breaks the degeneracy → removes bias AND tightens αs (0.046 vs 0.764).
  MAGNITUDE: +0.58 ≈ 0.76σ of Fit A's own error, ≈ σ(αs)-level vs full-analysis 0.547 → LARGE, strong
  justification for the param model. CAVEATS: worst-case αs+λ-only (no PDF/TNP, tiny theory-MC data cov) —
  full fit would refine; Fit A λ PRIORED vs Fit B λ FREE → for strict apples-to-apples re-run Fit B
  `priors=1 prior_sigmas=delta_lambda2=0.02` (or Fit A free-λ); bigger than the analytic screen (~0.16,
  30%·σ) because the screen FIXED λ while the fit lets priored-λ + free-αs trade. **My earlier blinded
  conclusions (−0.84/−1.42, "Fit B degenerate") are VOID.**


- **2026-06-18** — **⚠️ BLINDING GOTCHA: all fits so far ran WITHOUT `--unblind` → reported `pdfAlphaS`
  carries a blinding OFFSET; the central pulls (Fit A −0.84, Fit B −1.42) are NOT the true αs shifts.**
  My magnitude/sign conclusions from those numbers are VOID. Re-run everything with `--unblind` (user
  doing it). Caveats: (1) the αs **NaN uncertainty** (Fit B) is a Hessian property, blinding-independent
  → the αs↔λ under-determination read likely still holds (re-confirm unblinded). (2) IF blinding is a
  common additive constant across fits, it cancels in **Fit A − Fit B** — but unblind to be sure. STANDING
  RULE: pass `--unblind` (or account for the offset) before interpreting αs central values.


- **2026-06-18** — **Fit B RAN (param model, gen_level) — αs = −1.419 ± NaN; NOT ~0. Confirms αs↔λ
  degeneracy + Fit-A/Fit-B not yet apples-to-apples.** `gen_level` validated end-to-end: param model
  loaded λ_central from the json (prefit λ2=0.4 λ4=0.4 λ2_nu=0.15 λ_inf=1.0 λ_inf_nu=2.0 ✓), no R errors.
  Fit (λ FREE, no priors): λ2 0.4→0.96, λ4 0.4→0.81, λ2_nu 0.15→0.29, δλ2 0→0.020 (≈toward joint truth
  1.0/1.0/0.25/0.02), **pdfAlphaS −1.419 ± NaN**. lambda4_nu & lambda6 frozen (0±0); lambda_inf/_nu did
  NOT freeze (showed ±1.0/±1.414 — `--freezeParameters` only took on lambda6/lambda4_nu — investigate).
  INTERPRETATION: αs unc = **NaN** ⇒ αs on a near-flat direction (singular Hessian) ⇒ the αs↔λ degeneracy
  is real and the −1.419 central is NOT well-determined (minimizer stopped arbitrarily on the valley). λ
  unc also huge (~1 on scale-0.4 params) ⇒ whole fit under-determined. **Fit A had λ PRIORED (finite αs
  unc 1.22); Fit B ran λ FREE ⇒ not a clean comparison.** NEXT: re-run Fit B with `priors=1`
  `prior_sigmas=delta_lambda2=0.02` (match Fit A's template widths; λ2/λ4/λ2_nu defaults 0.5/0.5/0.10 ≈
  Fit A) to lift the flat direction + make αs finite. DEEPER: the αs+λ-only fit is degenerate either way —
  a trustworthy bias needs the degeneracy broken (real data covariance / restore PDF+TNP).


- **2026-06-18** — **Fit B (param-model λ) WIRED — `gen_level` flag implemented + inputs staged.**
  Implemented `gen_level` in `param_model.py` (`SCETlibNPParamModel`): spec token `gen_level=1` → reads
  the gen (qT,|Y|) binning from the fit channel, SKIPS the R/N_gen/σ_reco fold, and `compute()` returns
  the per-GEN-bin ratio σ_gen(λ)/σ_gen(λ_central). 4 touch points (ctor flag; R-block `if self.gen_level`;
  ratio-denominator block → `self.sigma_gen_central_flat`; `_ratio_from_param` branch). py_compile clean.
  Staged inputs: (a) `lambda_central_parity.json` (tanh_2, λ2=0.4 λ4=0.4 λ2_nu=0.15 δλ2=0 λ_inf=1.0
  λ_inf_nu=2.0) — EXTRACTED from the parity corr's `file_meta_data[...].config.Nonperturbative`; needed
  because the pseudodata-path tensor has NO `meta_info_input` (load_sigmaul_data returns None) so the
  param model's λ_central auto-detect can't fire. (b) σ_ns inputs = david_w's FO-sing + DYTurbo (exist).
  (c) btgrid at the param model's DEFAULT path `/scratch/submit/cms/wmass/scetlib_np/Z_COM13_CT18Z_N3p0LL_btgrid_fineall`
  → no btgrid_dir override. **feedRabbit main: COMMENTED OUT 184-188** (add_resummation_and_np_variations
  + PDF/bc/mb/EW) — the param model REFUSES if discrete scetlibNP* systs present (double-count guard), and
  the parity corr lacks pdfvars/bc/mb/EW anyway → Fit-B tensor = central + αs only. (NOTE feedRabbit had
  been edited to re-enable 185-188; those would've crashed on missing parity pdfvars.) **Run: feedRabbit
  `--outname parity_LxL_paramB` → rabbit_fit `-t 0 --paramModel …SCETlibNPParamModel gen_level=1
  lambda_central=<json> nonsingular_fo_sing=<dw> nonsingular_dyturbo=<dw> --freezeParameters
  lambda_inf,lambda6,lambda4_nu,lambda_inf_nu`.** EXPECT λ→joint truth, αs→~0 (≪ Fit-A −0.84); Fit-A−Fit-B
  αs = the linear-treatment bias. Caveat: σ_gen from btgrid vs pseudodata from point run → closure ~0.14%,
  not bit-exact.


- **2026-06-18** — **Fit A RESULT (αs+λ-only, `-t 0` on joint-λ pseudodata): αs pull = −0.838 ± 1.222 NOI
  units; λ2 +0.908, λ4 +0.095, λ2_nu +0.309, δλ2 +0.259.** User flagged the αs pull as "huge."
  DIAGNOSIS = mostly **αs↔λ4 degeneracy / under-constraint**, NOT a clean cross-term bias: (a) σ(αs)=1.22
  here vs **≈0.55 full-analysis** (NOI units) → 2.2× looser, nothing pins αs with only the σUL shape +
  tiny theory MC-stat data error; (b) **λ4 barely moved (+0.095) despite truth +1** → αs absorbed the λ4
  direction (λ2, distinct shape, pulled correctly to +0.91). So −0.84 is a worst-case UPPER BOUND
  inflated by degeneracy. `-t -1` semantics confirmed: −1=Asimov, 0=data, ≥1=toys (rabbit/parsing.py L356).
  **NEXT: (1) Asimov null `-t -1` (NO rebuild) → αs MUST ≈0 (pipeline manufacturing check); (2) break the
  degeneracy for the realistic number — biggest lever = use the REAL unfolded-σUL data covariance
  (`--infile` `hist_postfit_inclusive_cov`) instead of the tiny theory MC-stat we feed now, + restore
  PDF/TNP; (3) param-model Fit B as cross-check.** CAVEAT on Fit B (user asked "does param model →0?"):
  needs the gen-level param-model integration (not a quick run) AND may NOT give exactly 0 because of the
  same αs↔λ4 degeneracy — its value is as a DISENTANGLER (param pull≈0 ⇒ −0.84 is real non-factorization;
  param pull also large ⇒ mostly degeneracy). The Fit-A−FitB difference = the non-factorization piece.


- **2026-06-18** — **feedRabbit tensor BUILT cleanly (storage fix worked) → ready for rabbit_fit.**
  Re-ran make_theory_corr (Weight resum input) → copied CorrZ → feedRabbit wrote
  `parity_LxL_scetlib_dyturbo_parity_LxL_truth_alphaS.hdf5` (no variance crash). Tensor verified via
  h5py: `hprocs=['Zmumu']`; `hsystsnoconstraint=['pdfAlphaS']` + `hnoiidxs=[0]` → **αs = unconstrained
  NOI**; 4 constrained λ nuisances (`scetlibNPlambda2/lambda4/lambda2_nu/delta_lambda2`); PDF/bc/mb/EW
  correctly absent; systgroups = pdfCT18Z/pTModeling/resum/resumNonpert/theory/theory_qcd. (Big arrays
  need an HDF5 compression plugin absent in the bare shell — couldn't read data/pred values there, but
  structure is the intended αs+λ-only worst case + feedRabbit's own finite-check passed.)
  **NEXT: `rabbit_fit -t 0 --doImpacts --saveHists --computeHistErrors` → read `pdfAlphaS` postfit offset
  (= worst-case λ×λ→αs bias) + per-λ impacts.** Out dir `fit_parity_LxL`.


- **2026-06-17** — **Converter re-run CONFIRMED Weight storage.** User re-ran `point_to_binned` →
  `parity_resum_binned.pkl` now `storage=Weight`, `.variances()` finite & all-0, values finite, 10 λ-vars
  intact (axes Q1×Y82×qT70). NOTE: this file is NOT a TheoryCorrection — it's the resum INPUT to
  make_theory_corr (referenced by path, stays in `xterm_validation/`). Only the make_theory_corr OUTPUT
  (`scetlib_dyturbo_parity_LxL_truth_CorrZ.pkl.lz4`) goes into `wremnants-data/data/TheoryCorrections/`.
  **NEXT: re-run make_theory_corr → copy CorrZ → re-run feedRabbit.**


- **2026-06-17** — **First feedRabbit crash `1 NaN or Inf ... in variances for Zmumu!` — ROOT CAUSE =
  our `_hist` is `Double` storage, not `Weight`. Fixed in the converter (Double→Weight).** Diagnosed by
  loading the corr file directly (lz4+pickle, no ROOT needed): `scetlib_dyturbo_parity_LxL_truth_hist`
  is **`Double`**; the STANDARD `scetlib_dyturbo_*_hist` (e.g. `…_CT18Z_N2p1LL_N2LO`) is **`Weight`**.
  In the apptainer's boost_histogram a `Double` hist's `.variances()` returns **`None`**; tensorwriter
  `get_flat_variances` does `np.asarray(None).flatten().astype(f8)` → `array([nan])` (len **1**) → the
  "1 NaN". **NOT a bad bin** — all 1190 real + flow bins are finite (verified). (My local bh 1.6.1
  returns the *values* for Double, which is why a first hand-repro looked clean — version-dependent,
  both wrong for us.) Same defect silently gave the **pseudodata** a NaN data-variance via `add_data`.
  CAUSE: converter `point_to_binned.py` built the scetlib hist with `storage=Double()`; make_theory_corr
  propagates Double→Double `_hist` (variance dropped), whereas standard stays Weight.
  **FIX (in the converter, per user intuition — not a downstream band-aid):** emit `storage=Weight()` and
  fill `h.view()["value"]`, leaving **variance=0** (SCETlib is an analytic resummed calc, no MC stat) →
  matched `_hist` becomes Weight with MC-stat variance purely from DYTurbo/MiNNLO, identical to standard.
  Validated the fill pattern locally (Weight, `.variances()` finite & all-0, var-select stays finite).
  REMOVED the earlier no-op tensorwriter band-aid (`_zero_nonfinite_variances` + `import numpy`) — Double
  has no structured `variance` field so it never fired. `py_compile` clean (both files).
  **MUST REGENERATE (existing CorrZ is still Double):** re-run converter → make_theory_corr → copy CorrZ
  into `wremnants-data/data/TheoryCorrections/` → re-run the SAME feedRabbit command.


- **2026-06-17** — **Removed the `"parity"`-name guards (user: too hacky; no flag either).** The
  feedRabbit/writer parity behavior is now UNCONDITIONAL (script is parity-only until reverted),
  each block marked `TEMPORARY … revert later`: (1) `add_resummation_and_np_variations` always uses
  our 4 single-λ vars + `return` (standard NP/gamma/TNP/transition unreachable); (2) main: PDF/bc/mb/EW
  add_* commented out; (3) `_validate_args` call commented out; (4) `add_sigmaul_process` passes
  `nominal_entry="central"` (our baseline var name). Also REVERTED the `_select_baseline_variation`
  "central" fallback → back to plain default-`pdf0`-or-passed (user's preferred shape). `--pseudodataVariation`
  + `--alphasGenerator` kept (functional value-args, not guards/flags). [SUPERSEDED by the storage-fix
  Decision above: the existing CorrZ is `Double` and MUST be regenerated; converter→make_theory_corr→copy.]


- **2026-06-17** — **Reduced parity fit (αs+λ-only, worst case) — strategy + feedRabbit code changes.**
  Decided: αs+λ-only fit is a meaningful WORST-CASE bound (αs absorbs all the λ×λ residual since no
  PDF/TNP help → pull ≥ full-fit pull; full fit later = realistic, and the drop = profiling
  suppression). "Float" = profiled (αs=NOI unconstrained, λ profiled); nothing frozen — we just
  *omit* PDF/TNP from the tensor. **pdfas/pdfvars: BORROW (don't reproduce) for the parity** — the
  λ-dependence of αs/PDF templates IS the αs×λ/PDF×λ cross-term (separate, small), so borrowing only
  leaks that; and borrowing the matching-central source makes even that ~0. Reproduce-at-our-λ is
  deferred to the αs×λ/PDF×λ cross-group closures. **αs source = `scetlib_dyturbo_LatticeNP_CT18Z_N3p0LL_N2LO_pdfas`**
  (analysis's canonical αs; verified SAME gen binning as our truth: Q=1[60,120]/absY=17/qT=70; vars
  [as0118,as0116,as0120]=central/down/up). **Code changes** (gated by `"parity" in predGenerator` so
  normal runs are untouched — chose this over literal comment-out for safety):
  `theory_fit_writer.py`: (1) `_select_baseline_variation` "central" fallback (our central var is named
  `central` not `pdf0`); (2) `__init__` `alphas_generator` override; (3) `load_sigmaul_data`
  `pseudodata_variation` → pick a named var as pseudodata; (4) `add_alphas_variation` honors the
  override; (5) `add_resummation_and_np_variations` PARITY branch reads our 4 single-λ vars as NP
  nuisances, skips gamma/TNP/transition. `feedRabbitSigmaUL.py`: `--pseudodataVariation`/`--alphasGenerator`
  args; guard `_validate_args`; skip PDF/bc/mb/EW add_* for parity. Both `py_compile` OK. Copied truth
  corr → `wremnants-data/data/TheoryCorrections/`. systematicType left at feedRabbit default (`normal`)
  — may switch to `log_normal` to match the main fit. **NEXT: run feedRabbitSigmaUL → rabbit_fit → αs pull.**


- **2026-06-17** — **TRUTH CORRECTION BUILT + VERIFIED** ✅ `xterm_validation/scetlib_dyturbo_parity_LxL_truth_CorrZ.pkl.lz4`.
  Under key `Z`: `scetlib_dyturbo_parity_LxL_truth_minnlo_ratio` axes **(Q=1 [60,120], absY=17, qT=70,
  charge=1, vars=10 named λ)** — make_theory_corr folded signed-Y→absY + rebinned to the MiNNLO gen
  binning (17 absY) via rebinHistsToCommon. **ALL 11900 cells finite, 0 negatives** (matching cleaned
  the sing-only negatives + qT=0). **λ×λ cross-term PRESERVED end-to-end**: Nmult on the correction =
  +2.26e-2 @ low qT (== resum level). Named λ-vars survived (joint truth = last cat). **disableFlow
  crash is COSMETIC**: write_lz4 (make_theory_corr L416) completes BEFORE `disableFlow` (L420); crash is
  a wums `setAxisFlow` bug (passes `underflow=`/`circular=` to StrCategory, which only takes `overflow`)
  hit by our named-vars axis — kills only the post-write binning/normalization log + plots. File is
  whole (prod also writes corrh w/ flow). Options for clean re-runs: ignore (exit code only), or patch
  `wums.setAxisFlow` for category axes. **NEXT: feedRabbitSigmaUL** (Fit A: template λ, no param model;
  pseudodata = joint-truth var `lambda2_nu0.25-lambda21.0-lambda41.0-delta_lambda2Ext`).


- **2026-06-17** — **make_theory_corr matching SUCCEEDED** (flow fix worked): log shows "Minnlo norm
  in corr region 1951.42, corrh norm 1906.97" → the SCETlib+DYTurbo match + MiNNLO ratio computed
  (ratio ≈0.977). Next crash was metadata-only: `get_scetlib_config` (make_theory_corr L406, in a
  loop over minnlo+corrFiles) hard-requires a `"config"` key on each scetlib `.pkl`; ours had only
  `hist`/`var_names`, and the `except` catches only `ValueError` not the `KeyError`. **Fix:** converter
  now propagates `config` + `meta_data` from the point pkl (both present there). Re-run converter →
  make_theory_corr → expect `scetlib_dyturbo_parity_LxL_truth_CorrZ.pkl.lz4`.


- **2026-06-17** — **make_theory_corr crash = FLOW-bin mismatch; converter fixed.** First
  `make_theory_corr` run failed at `addHists(hresum, hnonsing)`: shapes (1,82,70,1,10) vs
  (3,84,72,1,10) — every spatial axis off by +2 = under/overflow. Cause: converter built axes
  `flow=False`; the production hists (verified: prod resum/fo_sing are `hist.Hist` with Q/Y/qT
  underflow=overflow=True, vars StrCategory overflow=True). `rebinHistsToCommon` aligned the REAL
  bins (1,82,70) but left flow flags → addHists can't broadcast. **Fix:** converter now builds Q/Y/qT
  Variable + vars StrCategory with DEFAULT flow (=True), matching production; real bins filled, flow
  stays 0. Re-run converter → re-run make_theory_corr. (Also seen, EXPECTED: "Zeroing bins slice(0,3)"
  = `--qtCutoff 1.0` zeroing the FO nonsingular at very low qT.)


- **2026-06-17** — **Named-vars converter re-run VALIDATED.** `parity_resum_binned.pkl` is now a
  `hist.Hist` (axes Q,Y,qT,vars), shape (1,82,70,10), Q[60,120], 82 absY × 70 qT, **vars = named
  StrCategory** (λ-names; joint truth = last cat `...delta_lambda2Ext`). 0 non-finite, 400 negatives
  (0.7%, physical sing-only → matching fixes). Per-var totals ~1910, cross-term Nmult intact (+2.3%
  low qT). Ready for `make_theory_corr` step 2.


- **2026-06-17** — **make_theory_corr inputs PINNED (via `print_command.py`) + 2 matching fixes.**
  Production cmd (from `scetlib_dyturbo_CT18Z_N3p0LL_N2LO_CorrZ.pkl.lz4`): `-g scetlib_dyturbo --proc z
  --axes Q Y qT --minnloh nominal_gen`, inputs (all in **david_w's** area, NP-independent → REUSE):
  • MiNNLO `-m` = `/home/submit/david_w/ceph/WMassAnalysis/results_histmaker/260521_z_gen/w_z_gen_dists.hdf5`
  • FO-sing = `/home/submit/david_w/work/TheoryCorrections/SCETlib/com13_ct18z_n3+0ll_fine_nnlo_sing/inclusive_Z_COM13_CT18Z_N3+0LL_fine_nnlo_sing_combined.pkl`
  • DYTurbo = `/home/submit/david_w/work/TheoryCorrections/DYTURBO/nnlo-scetlibmatch-13TeV-CT18Z-finer-bin/scalevariations/z0/results_z-2d-nnlo-vj-CT18ZNNLO-{scale}-scetlibmatch.txt`
  (the production resum was the PLAIN `com13_ct18z_n3+0ll_fine` — we SWAP it for `parity_resum_binned.pkl`.)
  **Fix 1 — Q auto-handled:** `read_matched_scetlib_hist` `rebinHistsToCommon` (L687-691) rebins Q/Y/qT to
  the common edge intersection → our 1-bin [60,120] forces the combine to [60,120]; NO `--axlim`.
  **Fix 2 — named vars:** our resum has 10 λ-vars, the FO carries scale vars; `read_matched` (L741-769)
  maps each resum var → central nonsingular via STRING ops (`"muf" in var`) → an Integer vars axis
  TypeErrors. Converter UPDATED to emit a `hist.Hist` with a **named StrCategory** vars axis (production
  format) → λ-vars cleanly map to central nonsingular + downstream can pick truth/templates by name.
  **Re-run the converter** (named-vars output), then `make_theory_corr` with `-p parity_LxL_truth`.


- **2026-06-17** — **Converter RAN clean in apptainer → `parity_resum_binned.pkl` written.**
  Output: grid 24Q×165Y×141qT → 1 Q[60,120]×82Y×70qT, zeroed 39260 non-finite, hist (10,1,82,70);
  **self-check `read_scetlib_hist` → axes=['Q','Y','qT','vars'], shape=(1,82,70,10)** ✓ (the exact
  make_theory_corr input format). Per-var integrated σ all ≈1910 (central 1910.1, joint 1910 → λ
  norm-conserving). Matches the tf-free validation. **NEXT: make_theory_corr** (this as `scetlib_resum`
  + FO-sing/DYTurbo, Q sliced to [60,120]).


- **2026-06-17** — **Converter RELOCATED to its canonical home** (user): now
  `wremnants/postprocessing/scetlib_np/point_to_binned.py` (alongside `btgrid_integrate`/
  `param_model`), scratch copy in `xterm_validation/` removed. Run it INSIDE the apptainer
  (user is already in it; no singularity wrapper needed) from `$WREM_BASE`:
  `python3 -m wremnants.postprocessing.scetlib_np.point_to_binned <point.pkl> -o <out.pkl>`.
  Apptainer base = `cmswmassdocker/wmassdevrolling:v15` + overlay
  `/work/submit/lavezzo/apptainer_overlays/wmassdevrolling_fastjet.img` (for reference; the
  `.img` is an overlay, needs `--overlay <base>`). Output → `xterm_validation/parity_resum_binned.pkl`.


- **2026-06-17** — **Converter WRITTEN + logic VALIDATED** (`point_to_binned.py`). Lightweight glue
  around `btgrid_integrate`: Q → `q_integrate_weights` (arctan-Q² Simpson over [60,120]) → 1 Q bin;
  Y,qT → `rebin_weights` (3-pt Simpson per experimental bin); experimental edges recovered as
  `grid[0::2]` (guarded by a midpoint check that they're edges not centers); qT=0 NaN→0; finite
  negatives pass through; Y kept SIGNED (make_theory_corr folds). Output = `{hist:(vars,Q,Y,qT),
  bins:[vars,[60,120],Yedges,qTedges], var_names}` → `read_scetlib_hist` dict format; built-in
  self-check parses it back. **Validated tf-free on the real pkl** (mirrored the exact numpy math):
  grid-parity OK → 82 Y × 70 qT bins; 39260 non-finite zeroed → 0 in output; shape (10,1,82,70);
  **binned Nmult matches point-level to ~1e-4** (cross-term preserved by the rebin); joint/central
  window-xsec ratio 0.99995 (λ norm-conserving shape). **ENV:** importing `btgrid_integrate` pulls
  `param_model`→tensorflow via the package `__init__`, so run the real converter INSIDE the WRemnants
  singularity (`source setup.sh`), not the bare shell. Output → `xterm_validation/parity_resum_binned.pkl`.
  **NEXT: wire `make_theory_corr`** (parity_resum_binned.pkl as `scetlib_resum` + FO-sing/DYTurbo
  matching, sliced to the single [60,120] Q bin).


- **2026-06-17** — **Parity run DONE + VALIDATED** (`runcard_parity_pointspec.pkl`, 447 MB, point mode).
  10 vars, λ assignments exact (vars metadata: central / λ2 1.0,0.0 / λ4 1.0,0.0 / λ2_nu 0.25,0.05 /
  δλ2 ±0.02 / joint=all-up), all tanh_2 λ6=0. Grid = 24 Q × 165 Y × 141 qT = 558,360 (the btgrid grid).
  Sanity: **Y-symmetry σ(Y)=σ(−Y) to 2e-16**, λ2 scan monotonic. **Physics confirmed:** λ×λ residual
  `Nmult=(1+R_joint)−Π(1+R_single)` peaks **+2.3% at low qT** (Q=90,Y=0.225), vanishes by qT≳25 —
  the cross-term the template fit will miss is present (≈ shape-study scale). **Two benign integrity
  items:** (1) **NaN only at qT=0.0** (3926 pts; differential spectrum ill-defined at qT=0, phys value
  0) → converter must set σ(qT=0)→0 or drop the edge for the first qT bin's 3-pt Simpson [0,0.5];
  framework cuts low-qT nonsingular anyway (`read_scetlib_hist` ">0.1", `zero_nons_bins`).
  (2) **Negative σ** (~0.4% at qT≤15, more at high qT) = physical `sing`-only (nonsingular dominates);
  matching `(DYTurbo−FO_sing)` fixes them, converter passes through (Simpson linear). Bad-mask
  **λ-independent** (var0 vs var9 agree 99.997%) → kinematic, cancels in ratios. `lambda6_nu=0.0007`
  in metadata is unused tanh_2 CS default (constant across vars → cancels). **Ready for converter;
  qT=0 first-bin handling is the one design point.**


- **2026-06-17** — **Matching inputs located (config level).** `TheoryCorrections/SCETlib/*` =
    CONFIGS only; actual output `.pkl`s live in `/ceph/.../zstuff/` (e.g. the reference
    `Z_COM13_CT18Z_..._Lambda6_Fine/combined_out/...combined.pkl` = the tanh_6 RESUMMED production).
    For our truth's `make_theory_corr` (reuse, λ-independent FO pieces): FO-singular = the
    `_nnlo_sing` companion (`com13_ct18z_newnps_n3+0ll_lattice_newvals_lambda6_fine_nnlo_sing`;
    combined pkl in a /ceph sibling); DYTurbo FO = `TheoryCorrections/DYTURBO/nnlo-scetlibmatch-13TeV-CT18Z-finer-bin/`.
    Both are FO (no NP) → reusing tanh_6 production is correct. **TODO: pin exact 3 paths via the
    production `make_theory_corr` command.** Bonus: `..._lambda6_fine_pdfas` config = the PDF+αs
    variation set for the later cross-GROUP closures. Q-binning caveat stands (prod 2 Q bins
    [10,60,120] vs our 1 bin [60,120] → slice to [60,120]).
- **2026-06-17** — **Converter spec WORKED OUT** (target binning resolved). `read_scetlib_hist`
    (`input_tools.py:113`) wants `{hist: ndarray(vars,Q,Y,qT), bins:[vars,Q_edges,Y_edges,qT_edges]}`
    on the **experimental** (Q,Y,qT) binning (signed Y) — NOT gen bins. `read_matched_scetlib_dyturbo_hist`
    (`:577`) adds our resummed piece to the λ-independent nonsingular `(dyturbo_fo − scetlib_fo_sing)`.
    ⇒ **Converter** (reuse `fz_int.rebin_weights` = `btgrid_integrate.rebin_weights(source_grid,
    target_edges)`, a (Ntarget,Nsource) Simpson matrix): qT `rebin_weights(141 btgrid qT → 71 exp qT
    edges)`=70 bins; Y `rebin_weights(165 btgrid Y → 83 exp Y edges)`=82 bins (signed; fold |Y|);
    Q = arctan-Q² Simpson over the 24 resonance pts → **1 Q bin [60,120]** (btgrid covers only the Z
    window, like the param-model Q integral). Output `{hist:(10,1,82,70), bins:[vars,[60,120],Yedges,
    qTedges]}` → passed as `scetlib_resum`. **Still need (λ-independent, reuse from nominal corr):**
    the FO-singular SCETlib `.pkl` + DYTurbo FO for the matching, and confirm their Q binning = single
    [60,120] bin. (`fz_int=btgrid_integrate`, `fz_tf=btgrid_tf` per `param_model.py:264-265`.)
- **2026-06-17** — **Grid sufficiency SETTLED by reusing the validated btgrid grid + Simpson.**
    User: don't assume sampling density — reuse the grid the param-model closure already validated.
    The btgrid runcard (`.../Z_COM13_CT18Z_N3p0LL_btgrid_fineall/inclusive_*.ini`) samples
    **edges + centers** of the experimental bins (qT 71+70=141, Y 83+82=165) + 24 resonance Q pts
    (60–120) *precisely so* the rebin is a **3-point Simpson per bin** (<0.05% shape residual —
    the runcard comments say so). `runcard_parity.ini` grids replaced with these EXACT values
    (FP-imprecise Y tails verbatim → dict-key match w/ btgrid pickles). Cost ≈ Q×Y perturbative
    solves (qT points reuse the same W(bT) kernel → nearly free; btgrid-mode runs locally, so does
    this) — my earlier "560k pts = condor-scale" was WRONG (user corrected). **Converter = REUSE the
    param model's Simpson rebin** (`param_model.py`: `fz_int.rebin_weights` for qT→target & |Y|→target
    via 3-pt Simpson; arctan-Q² Simpson for Q over [60,120]), NOT center-only (my earlier 0.14%
    sketch is superseded by <0.05% Simpson). **OPEN — converter target edges:** make_theory_corr's
    `read_matched_scetlib_dyturbo_hist` wants the EXPERIMENTAL SCETlib binning (the 70-qT/82-absY
    bins, Q integrated over [60,120]); param model targets GEN (ptVGen,absYVGen). Same `rebin_weights`,
    different target edges — confirm against `read_matched_scetlib_dyturbo_hist` + `feedRabbitSigmaUL`
    ingestion (post-run; does NOT block the SCETlib run).
- **2026-06-17** — **Switched parity runcard to POINT mode** (bin mode confirmed impractical:
    live run hit ~20–70 s *per bin* × ~11,500 bins × 10 vars ≈ day-scale; the production
    reference's condor logs span ~14 h for the same grid). `runcard_parity.ini` now `bins=false`
    with values = the production grid's BIN CENTERS (2 Q × 41 absY × 70 qT = 5,740 pts); run with
    `scetlib-run-qT.py <n> 1 xterm_validation/runcard_parity.ini --point-spectrum --live` →
    `runcard_parity_pointspec.pkl`. Point mode skips per-bin qT integration; 10 vars per point
    share the perturbative core. **Needs the converter** (point→{hist,bins} w/ production EDGES)
    for `make_theory_corr` — does NOT block the SCETlib run (post-run step). Center-density ≈
    bin-average for the smooth ratio (0.14% approx); MiNNLO bin-width cancels in truth/nominal.
- **2026-06-17** — **Parity-check SCETlib cards CONFIRMED (user signed off).** Config locked:
    production λ magnitudes (δλ2 ±0.02, λ4_nu FIXED, λ2/λ4 up=1.0), singles `[1]–[8]` KEPT as
    the self-contained **tanh_2 Fit-A templates** (the current fit has no binned λ templates —
    param model replaced them; the only existing binned λ templates are tanh_6 production →
    would contaminate; one SCETlib run makes baseline+templates+truth together), joint `[9]`
    = pseudodata, BIN mode. (Open: if a current *tanh_2* λ-template correction exists, Fit A
    could reuse it and this run would drop to central+joint — not pursued; defensive singles.)
    Cards: `variations_parity.conf` (central + 8 single-λ
    templates up/down + [9] joint truth) + `runcard_parity.ini` (tanh_2, NO λ6; EW/grid/
    integration copied verbatim from the production reference
    `/ceph/submit/data/user/l/lavezzo/zstuff/Z_COM13_CT18Z_..._Lambda6_Fine/`; inherits
    `xterm_validation/base.conf` → `sing`, CT18ZNNLO central, transition [0.2,0.6,1.0]).
    **Read the production variation card (`variations_lattice_allvars.conf`) → the ACTUAL
    old-treatment template magnitudes, which CORRECT the earlier param-model-prior guesses:**
    `lambda2`/`lambda4` up=1.0 down=0.0 (central 0.4 → +0.6/−0.4; was 0.9/+0.5);
    `lambda2_nu` 0.25/0.05 (±0.10, unchanged ✓);
    **`delta_lambda2` ±0.02 (NOT 0.20 — a 10× overstatement; CONFIRMS the memory caveat);**
    **`lambda4_nu` FIXED (no template, not floated — NOT 0.10).** The λ4_nu=0.1 the user
    asked for earlier belongs to the *param-model* truth (λ4_nu floats there); for the OLD-
    treatment parity it must stay FIXED, else the αs pull mixes λ×λ with an unmodeled-λ4_nu
    shift (no template to absorb it). **Truth [9] = all 4 floating λ at their UP nodes** →
    singles match exactly, only the λ×λ cross-term is unrepresentable → clean λ×λ pull,
    compare to screen `--with-ll` ~30%. **Mode = BIN** (mirrors the proven make_theory_corr
    input, no converter needed for this one-off; fine grid → split on condor or coarsen);
    point+converter deferred to the bulk PDF runs. Production reference also = source for
    EW params, fine (Q,Y,qT) grid, and the nominal correction's binning.
- **2026-06-17** — **FIRST RUN = λ×λ "parity / positive-control" pair** (user's call; replaces
  the trivial-λ-shift plumbing test in START HERE). Inject a JOINT multi-λ truth (≥2 λ's
  varied together, at the truth-config excursions λ2=0.9/λ4=0.9/…), then fit it two ways on
  the SAME pseudodata:
  • **Fit A — template λ only, NO param model** (revert to the pre-param-model treatment):
    KEEP the binned λ nuisances (do *NOT* `--excludeNuisances scetlibNPZ|scetlibNPgamma`),
    do *NOT* pass `--paramModel`. Expect a NON-ZERO α_s pull ≈ tens-of-% of σ — the screen's
    `--with-ll` λ×λ value (~30%) is the analytic prediction. = "the α_s bias the OLD linear λ
    treatment carried" (the param model's raison d'être, now quantified at fit level).
  • **Fit B — param-model λ** (planned setup): expect ~0. Confirms the fix; if the truth is
    from an INDEPENDENT SCETlib run (not the param model), Fit B is also a real
    param-model-vs-SCETlib cross-check (~0.14%). A−B = bias the param model removes.
  **Why first (positive control, not a null test):** a recover-truth-~0 closure could also
  return ~0 if the pipeline is broken; λ×λ-template GUARANTEES a known non-zero pull → (1)
  validates the whole gen pipeline (converter→make_theory_corr→feedRabbitSigmaUL→fit)
  against a known answer, (2) proves the closure DETECTS bias, (3) **measures the
  screen→profiled SUPPRESSION FACTOR** — if screen 30% → profiled X%, apply ~X/30 to the
  cross-group screen values (~10%→~6%) to estimate their real bias *before* running them
  (may settle "is 10% worrisome" outright). **Operationally easiest entry point:** Fit A
  needs ONLY the converter (code change 2), NOT the param-model gen_level flag (code change
  1). Design caveat: a SINGLE λ at its template node closes trivially (template spans it) →
  must vary ≥2 λ's jointly to expose the λ×λ residual.
- **2026-06-17** — **History + "is 10% of σ(α_s) worrisome?" framing.** The logic chain:
  λ×λ was found NOT to factorize (~5% shape) → that was alarming enough to **build the
  param model** (handles λ×λ exactly) → this survey is the follow-up ("are there *other*
  unhandled cross-terms of similar concern?"). So **λ×λ is the PRECEDENT, not a red
  herring**: run `impact_xterm.py --with-ll` and the *unhandled* λ×λ → **~30% of σ(α_s)** —
  the bias the user already judged worth a new model. The next-biggest *unhandled*
  cross-group terms (PDF×λ, α_s×λ) are **~10–11%**, i.e. **~1/3 of that precedent.**
  Disposition of ~10%: NOT alarming, NOT skippable. (1) It's a **bias** (0.1σ central
  shift), not an uncertainty — as an uncertainty it's quadrature-negligible (√(1+0.1²) →
  +0.5% on σ). (2) It's an **upper bound** (single-param, gen-level, no profiling) → real
  is smaller. (3) Once the closure *measures* the bias you **correct or assign-as-syst**
  (≈0.5% quadrature, trivial) — only an *unknown* bias is dangerous. (4) Watch **coherent
  stacking** across families (PDF×λ+α_s×λ+λ×TNP same sign → worst-case ~15–20%); the
  all-at-once net closure captures cancellation. ⇒ run ONE net closure fit to turn the
  upper bound into the real profiled number; expected outcome = dismiss-with-number or
  cheap systematic. Defensible answer to the inevitable "does λ factorize from PDF/α_s?" review Q.
- **2026-06-17** — **CLARIFIED why we bother with cross-GROUP terms at all** (the
  Nmult-table vs impact-screen confusion). Two *different* metrics: (1) **Nmult table** =
  worst-case SHAPE mismatch, max over (Q,Y,qT) — λ×λ ~5%, all cross-group <1%; **not a
  bias**. (2) **`impact_xterm.py`** = the "do we bother" number — projects Nmult onto the
  α_s response, σ-weighted: `δα_s = Δα·⟨Nmult,R_αs⟩/⟨R_αs,R_αs⟩`. **λ×λ's 5% is a red
  herring**: the param model computes the full bT-integral with both λ varied → λ×λ is
  exact, the fit never misses it (screen EXCLUDES it by default, `--with-ll` only as a
  scale-calibration control → ~30% of σαs). The **cross-group** terms (αs×λ, PDF×λ, λ×TNP)
  ARE missed (param model evaluates λ at *central* αs/PDF). A <1% shape term still lands at
  **~10–11% of σ(α_s)** because bias ∝ *overlap with the α_s shape*, not |Nmult|: (a) the
  full α_s response is only ~2.7% so <1% is a big fraction of it; (b) σ-weighting + good
  overlap with R_αs in the bulk; (c) σ(α_s)≈0.001 is tight (Δα=0.002 already 2σ). ⇒ the
  ~10% screen value (NOT the λ×λ 5%) is what motivates the closure; screen is a
  single-param, gen-level, frozen-nuisance UPPER BOUND → real profiled fit is smaller.
- **2026-06-17** — **Step-(1) truth config decided.** λ central (auto-detected; =
  closure-suite TRUTH): `lambda2=0.4, lambda4=0.4, lambda2_nu=0.15, lambda4_nu=0,
  delta_lambda2=0` (fixed: `lambda_inf=1, lambda_inf_nu=2, lambda6=0`). `DEFAULT_PRIOR_SIGMAS`
  (`param_model.py:309-314`, **OFF by default — all λ float unconstrained**): lambda2 0.50,
  lambda4 0.50, lambda2_nu 0.10, delta_lambda2 0.20; **lambda4_nu has NO entry (no prior)**.
  **Truth = λ shifted +1σ off central:** `lambda2=0.9, lambda4=0.9, lambda2_nu=0.25,
  lambda4_nu=0.1` (guess, no prior — user's call, matches the cross-term study), `delta_lambda2=0.20`.
  Cross-partners: αs +0.002 (matched CT18Z member); TNPs ±1/±0.5.
  **PDF: per-eigenvector, NOT all-at-once.** Setting all 29 eigenvectors to +1σ together is a
  coherent ~√29≈5σ unphysical point that grossly overstates; the PDF uncertainty is a quadrature
  of 29 INDEPENDENT directions with no single-config representation. ⇒ inject λ-shifted × each PDF
  member separately (we have all 58 runs) → δαs_k → quadrature over the 29 (the fit-level analogue
  of `analyze_pdf_xterm.py`'s Hess-comb). Sequencing: leading 2-4 eigenvectors (eig 19/22) first
  for plumbing + scale, then the full 29. **Net:** ONE combined fit for λ×αs / λ×TNP / αs×TNP;
  **×29 per-eigenvector fits** for PDF×{λ,TNP} (PDF is the one block that can't collapse to one fit).
- **2026-06-17** — **Two code changes to enable the gen-level fit (scoped).**
  (1) **Suppress the binned NP λ variations** in `feedRabbitSigmaUL` — they'd
  double-count λ (the param model handles it). **NO code change:** the writer
  (`theory_fit_writer.SigmaULTheoryFitWriter`) already filters via
  `--excludeNuisances` (regex → `_keep_systematic`). NP λ nuisance names (from
  `theory_variation_labels.py`): `chargeVgenNP0scetlibNPZLambda2/…Lambda4/…Delta_Lambda2`
  + `scetlibNPgamma`. ⇒ `--excludeNuisances 'scetlibNPZ|scetlibNPgamma'`. CAVEAT:
  `add_resummation_and_np_variations` (L473) also adds the TNPs — confirm TNP names
  don't contain `scetlibNP` so we don't over-exclude (we KEEP TNPs as factorized templates).
  (2) **Param model gen-level mode** — `param_model.py` currently always folds gen→reco.
  Add a guarded `gen_level` (default False) flag: in `_ratio_from_param` (L1205-1208)
  skip `sigma_reco = matvec(self.R, gen_flat)` and return `gen_flat/gen_central_flat`
  (both already exist; `self.sigma_gen_central` stored at L881); in `__init__` (L875-896)
  skip building R / N_gen / sigma_reco_central. Default-off ⇒ real reco fit unchanged.
  Gotchas: (a) the Hessian straight-through path (`_ratio_compact_jac/_hess`, L1260/1265)
  also folds → needs a gen branch IF using full-covariance Phase-B (defer for Asimov
  values/GN); (b) gen-mode `compute` returns the ratio on GEN (ptVGen,absYVGen) bins →
  param model must be built against the σUL fit's gen `indata` (confirm bin layout matches).
  `param_model.py` is LIVE main-tree code → guarded flag (or a worktree) keeps production safe.
- **2026-06-17** — **Do the closure at GEN level via `feedRabbitSigmaUL.py`**, not
  reco/histmaker. Confirmed it fits the unfolded σUL using TheoryCorrection hists as
  templates and takes `--pseudodataGenerator <name>` to use a corrections hist AS the
  σUL pseudodata. Rationale: (1) no histmaker/reco re-run; (2) **isolates the theory
  non-factorization** from reco smearing + acceptance (the thing we actually want);
  (3) **conservative** — reco smearing dilutes the low-qT region where cross-terms peak,
  so gen bias ≥ reco bias (gen negligible ⇒ reco negligible); (4) closure is all-MC
  anyway. `--infile` = an unfolded σUL fit result (the "data" side); `--paramModel` at
  the `rabbit_fit` step (as in `scetlib_np_closure_suite.py`).
- **2026-06-17** — **Feed `make_theory_corr.py` from POINT mode via a converter** (bin
  mode is too slow). `read_scetlib_hist` accepts either a `hist.Hist` or a dict
  `{hist: ndarray(vars,Q,Y,qT), bins: [vars,Q,Y,qT edges]}`. Converter = run point mode
  at the (Q,Y,qT) **bin centers**, pack σ into that array. **Caveat (benign):** point =
  center density vs bin = integral, but the correction is a smooth RATIO so center ≈
  bin-average — exactly the btgrid/param-model approximation already validated to 0.14%.
  DYTurbo FO side of `make_theory_corr` is unchanged. (`input_tools.read_scetlib_hist`.)
- **2026-06-17** — **Param model has NO special role in the closure** — it's only the
  normal fit ingredient for continuous λ. The pseudodata (truth) is built from SCETlib +
  `make_theory_corr`, independent of the param model. (Dropped an earlier over-engineered
  "use the param-model R matrix to fold gen→reco" idea — unnecessary given gen-level.)
- **2026-06-17** — **Inject the FULL non-factorized truth once → net α_s bias** (not one
  fit per pair). Per-FAMILY injection (~6) for attribution; the screen
  (`impact_xterm.py`) prioritizes (λ2×{PDF,α_s} dominate). Attribution is linear, so the
  Fisher-matrix decomposition is the cheap alternative (`WORKFLOW.md` C1).

## Inputs / grounded facts

- **σ(α_s) ≈ 0.001** (the user). Used only to express the pull as a fraction of the
  uncertainty; the closure fit also returns the postfit σ(α_s) directly.
- **ALL λ's float UNCONSTRAINED** (param-model default priors exist but are OFF by
  default). So *every* λ excursion in the screen (not just δλ2) is a rough ≈-postfit
  guess — the screen's λ magnitudes are all soft. The closure handles this natively: it
  floats the λ's, so it never needs the excursions. (This is the strongest reason to
  trust the closure over the analytic screen.)
- `feedRabbitSigmaUL.py` → `SigmaULTheoryFitWriter`; args `--infile`, `--pseudodataGenerator`,
  `--channelSigmaUL`, `--fitresultMapping "Select helicitySig:0"`, `--scalePDF`.
- `make_theory_corr.py`: `-g scetlib_dyturbo -c <resum.pkl> <fo_sing.pkl> <dyturbo_fo>`,
  `--proc z`, output `{gen}_Corr Z.pkl.lz4` keys `{gen}_minnlo_ratio` / `{gen}_hist` /
  `minnlo_ref_hist`, axes (Q, absY, qT, charge, vars).
- λ closure reference: `scripts/rabbit/scetlib_np_closure_suite.py` (rabbit_fit invocation,
  `--paramModel wremnants.postprocessing.scetlib_np.SCETlibNPParamModel`, `-t 0`).

## Status

- Cross-term **shape** study DONE (`LOGBOOK.md`): all {λ,TNP,α_s,PDF} pairs ≤0.84%
  worst-case `Nmult`. **Screen** (`impact_xterm.py`): σ-weighted αs-projected upper bound
  ~10–11% of σ(α_s) for PDF×λ, α_s×λ (λ×λ control 30%). Closure = the real number.
- Closure study — **λ×λ parity (αs+λ-only worst case): pipeline BUILT, about to run the fit.**
  Done: SCETlib parity run, converter, TRUTH correction (verified, λ×λ intact), feedRabbit/writer
  code hacks (TEMPORARY). **NEXT:** `feedRabbitSigmaUL` → `rabbit_fit` → αs pull. Then: full-nuisance
  fit (realistic) + Fit B (param-model λ, needs `gen_level` flag) + revert hacks + cross-GROUP
  (αs×λ, PDF×λ) closures.

## Open items / TODO

- [x] **Converter** point→`{hist,bins}` — DONE (`point_to_binned.py`, validated; cross-term preserved).
- [x] **Build TRUTH TheoryCorrection** — DONE (`scetlib_dyturbo_parity_LxL_truth_CorrZ.pkl.lz4`);
      inputs PINNED via `print_command.py` (MiNNLO / FO-sing / DYTurbo from david_w's area).
- [x] **σUL "data" mechanic** — `--pseudodataGenerator` + `--pseudodataVariation <joint var>` (no `--infile`).
- [ ] **Run** `feedRabbitSigmaUL` → `rabbit_fit` (αs+λ-only) → αs pull = **worst-case** λ×λ bias.
- [ ] **Full-nuisance fit** (realistic profiled bias); the Fit-A→full drop = profiling-suppression factor.
- [ ] **Fit B** (param-model λ) — needs `param_model.py` `gen_level` flag (code change 1, NOT done).
- [ ] **Revert TEMPORARY parity hacks** in `feedRabbitSigmaUL.py` / `theory_fit_writer.py` (do-it-properly pass).
- [ ] **Cross-GROUP closures** (αs×λ, PDF×λ): simultaneous SCETlib runs + **reproduce pdfas/pdfvars at our λ**
      (there the borrow is NOT valid — it's the cross-term under test); per-eigenvector PDF + quadrature.
- [ ] (cross-check) Fisher-matrix attribution (`WORKFLOW.md` C1) vs the closure total.
- [ ] (deferred, optional) patch `wums.setAxisFlow` for StrCategory so make_theory_corr exits clean.

## Files

- `WORKFLOW.md` — the generic SCETlib→fit workflow + this plan (Part C).
- `LOGBOOK.md` — cross-term shape study (Nmult, screen, impact_xterm.py).
- `impact_xterm.py` — analytic σ-weighted αs-projected screen (the upper bound to beat).
- `runcard_parity.ini` + `variations_parity.conf` — the λ×λ parity SCETlib run (point mode, tanh_2,
  validated btgrid grid; central + 8 single-λ + joint).
- `runcard_parity_pointspec.pkl` — parity point-spectrum output (447 MB; 10 vars).
- `scetlib_dyturbo_parity_LxL_truth_CorrZ.pkl.lz4` — the TRUTH correction (also copied to
  `wremnants-data/data/TheoryCorrections/` so feedRabbit finds it).
- `point_to_binned.py` — the converter, lives in `~/alphaS/main/WRemnants/wremnants/postprocessing/scetlib_np/`.
- **TEMPORARY parity hacks** in `~/alphaS/main/WRemnants`: `scripts/rabbit/feedRabbitSigmaUL.py`
  + `wremnants/postprocessing/theory_fit_writer.py` (marked `revert later`).
- `scripts/corrections/make_theory_corr.py`, `scripts/rabbit/scetlib_np_closure_suite.py`.
