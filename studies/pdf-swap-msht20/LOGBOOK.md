---
title: PDF swap (CT18Z → MSHT20) — does a different central PDF shape help the ptll GOF
slug: pdf-swap-msht20
status: active
created: 2026-07-17
updated: 2026-07-20
---

# PDF swap (CT18Z → MSHT20) — logbook

**Goal:** the real-data Z ptll α_S fit is "~reasonable overall but small p-value on the
ptll projection", and the NP model is poorly theory-constrained so it walks unphysical
(see [[../np-wall-local-minima/LOGBOOK.md]], [[../physical-lambda/LOGBOOK.md]]). Hypothesis:
part of the mismodeling is the central-PDF *shape*, not just the NP freedom. Swap the
baseline PDF CT18Z → **MSHT20** (methodologically independent; unlike PDF4LHC21 which
*contains* CT18Z) and see whether the ptll GOF improves and/or the NP λ move. `done` =
a matched CT18Z-vs-MSHT20 comparison of postfit {ptll GOF, NP λ (physicality), α_S central
+ NP-treatment spread} with a physics read.

---

## START HERE (status as of 2026-07-20)

> **RESOLVED: the λ4 bug WAS the cause of the MSHT20 low-qT σ_gen discrepancy. Rebuilding the MSHT20
> correction with the fixed SCETlib closes the validation to 0.2% — IDENTICAL to CT18Z.**
> Apples-to-apples (same btgrid, same nonsingular inputs, only the correction swapped, |Y|<2.5):
> - OLD (buggy-λ4) correction: model/corr = [0.9966, 1.0130], **bin0 = 1.013** (low-qT wiggle).
> - NEW (fixed-λ4) correction: model/corr = [0.9981, 0.9996], **bin0 = 0.9995**, flat (CT18Z baseline = [0.9981,0.9995], bin0 0.9995).
> - The shift (bin0 1.013→0.9995, −0.34% at qT~1.75→flat) matches the DIRECT NEW/OLD resum ratio (+1.5% bin0,
>   −0.3% at 3–4 GeV) → the λ4 fix accounts for the whole low-qT wiggle.
>
> **RETRACTION (honest):** my earlier "+11% bin0 / +9.6% nonsingular leak" does NOT reproduce in a clean,
> consistent setup — today's OLD-correction comparison is only +1.3% at bin0. The +11% was a STALE-SETUP
> artifact (pre-btgrid-fix run / concurrent combined-pkl corruption), NOT a real nonsingular problem. The
> nonsingular is λ4-blind (still true) and is NOT broken.
>
> **Mechanism (confirmed):** λ4 bug lives only in `NP_model_effective` (F_eff, resummed NP form factor);
> `nnlo_sing` is `run_order=none` so its NP block is inert (pre/post-fix CT18Z singular IDENTICAL). Timeline:
> λ4 fix = SCETlib commit `2e17676` (**Apr 22 2026**); MSHT20 resummed Mar 31 + nnlo_sing Jan 15 were PRE-fix;
> CT18Z remade May (post-fix). The btgrid needs NO remake (NP-off I_pert, correct λ4 in Python).

**NEW MSHT20 fixed-λ4 correction (central-only):**
`wremnants-data/data/TheoryCorrections/scetlib_dyturbo_LatticeNPLambda4Bugfix_MSHT20_N3p0LL_N2LO_CorrZ.pkl.lz4`
(resummed `com13_msht20_newnps_n3+0ll_lattice_lambda4bugfix_central/` regenerated with the fixed build,
combined, `make_theory_corr` via `studies/pdf-swap-msht20/make_theory_corr_zmumu_only.py` [Zmumu-only:
gendist has no Zmumu10to50, negligible in Z window] + gendist `/scratch/submit/cms/areimers/wmass/gendistributions/w_z_gen_dists_maxFiles_m1_msht20_finePtAbsY.hdf5`).
Closure plots: `260720_MSHT20_fixedlambda4_matched_absY2p5.png` (flat) vs `..._OLDbuggy_...` (wiggle).

- **NEXT (the actual study goal):** setupRabbit with the MSHT20 histmaker + this new fixed-λ4 correction →
  fit; compare postfit {ptll GOF p-value, NP λ physicality, αs central + NP-treatment spread} vs CT18Z.
  NB the param-model in the fit must point at the MSHT20 nonsingular (nnlo_sing + finer-bin DYTurbo), not
  the CT18Z `_NONSING_*_DEFAULT`. NEW correction is central-only (1 var) — for the full fit we'll also need
  the NP/scale/pdf variations regenerated (the study only needed central to validate).
- **Env notes (hard-won):** run in `:latest`, `source /opt/venv/bin/activate` + literal
  `PYTHONPATH=/home/submit/lavezzo/alphaS/WRemnants:.../narf:.../rabbit:.../wums` — do NOT `source setup.sh`
  (clobbers env; WREM_BASE/vars vanish) and do NOT use shell vars inside `bash -c` (intermittent empty
  expansion). `make_theory_corr` writes CorrZ to wremnants-data (NOT `-o`, which is the plot dir) and then
  crashes on a cosmetic `hh.disableFlow` StrCategory bug AFTER the write — CorrZ is complete.

--- OLDER NOTES (superseded by the RESOLVED block above) ---

- **RESULT (2026-07-20): λ4-fix effect on the MSHT20 resum QUANTIFIED, and it is MODEST.**
  Regenerated the MSHT20 resummed central-only pkl with the fixed build (11480 bins, rel 1e-3, EXIT 0;
  `com13_msht20_newnps_n3+0ll_lattice_lambda4bugfix_central/..._combined.pkl`). Direct NEW/OLD resum
  ratio at the SAME central tune (pickle-only, `_cmp_resum.py`; plot `260720_MSHT20_lambda4_resum_OLDvsNEW.png`):
  **bin0 (qT≈0.25) = +1.5%, qT≈3–4 GeV = −0.3%, tail ≈ 0, total Σ unchanged (1.00000).** So the λ4 bug is
  a small low-qT SHAPE distortion of the resummed term (where F_eff·λ4 at large bT acts), NOT a normalization shift.
- **CAUSAL VERDICT (honest):** the λ4 bug explains the ~+1.3% low-qT RESUM tilt we saw (our correct-λ4
  btgrid vs the OLD buggy-λ4 correction, resum-only bin0 = 1.013 ≈ the +1.5% here). It does **NOT** explain the
  large +11% full-σ_gen bin0 — that is dominated by the NONSINGULAR/DYTurbo-binning issue (~+9.6%), which is
  λ4-BLIND (proven). So λ4 is confirmed but is only PART of the story: real for the resum, irrelevant to the bin0 breakage.
- **BLOCKED — full step-5 closure (btgrid vs new correction) not done:** `make_theory_corr` fails at
  `read_mu_hist_combine_tau` → "Got cross section of 0" (the msht20an3lo `..._Fullstats.hdf5` gendist's
  `Zmumu_13TeVGen` has xsec=0; only that sample present). Needs the right gendist / `--minnloh` / `--eras`.
  Secondary: `wremnants` import from /home is FLAKY (intermittent NFS `ModuleNotFoundError`); pickle-only
  (venv, no wremnants) is reliable — `setup.sh` clobbers the env, use hardcoded `PYTHONPATH=$WREM_BASE`.
- **Next:** (1) resolve the gendist xsec=0 (Luca knows which gendist the CT18Z corr actually used) → finish
  make_theory_corr → sigma_gen_at_lambda closure. (2) Separately chase the nonsingular/DYTurbo bin0 (+9.6%,
  the real dominant breakage). (3) Then setupRabbit(MSHT20) → fit; compare {ptll GOF, NP λ, αs} vs CT18Z.

**Assets / reproduction recipe:**
- Fixed build: `/work/submit/lavezzo/alphaS/scetlib-cms-newnp-lambda4fix` (runner `prod/scetlib_run/scetlib-run-qT.py`
  auto-binds `build/lib`; beamfunc `share/scetlib/beamfunc/MSHT20nnlo_as118_beamfunc` = 51 kernels).
- New resummed work dir: `/work/submit/lavezzo/alphaS/TheoryCorrections/SCETlib/com13_msht20_newnps_n3+0ll_lattice_lambda4bugfix_central/`
  (base.conf pdf_set=MSHT20nnlo_as118; `.ini` = old resummed card w/ rel=1e-3 + `variations_central.conf`=`[0]`).
- Launch wrapper: `/tmp/scetlib_msht20_central.sh <threads> <cuba> <args>` (container :v15 + PYTHONPATH/LD_LIBRARY_PATH→build/lib).
- combine: `scetlib-manage-condor.py -r <ini> -b 11480 -f <workdir> combine -o <workdir>`.
- make_theory_corr: `-m <msht20an3lo gendist hdf5> -g scetlib_dyturbo --proc z --eras 13TeVGen --qtCutoff 1.0
  --minnloh nominal_gen --axes Q Y qT -c <new_resummed_combined.pkl> <msht20 nnlo_sing_combined.pkl>
  '<msht20-finer-bin DYTurbo .../results_z-2d-nnlo-vj-MSHT20nnlo-{scale}-scetlibmatch.txt>' -p LatticeNPLambda4Bugfix_MSHT20_N3p0LL_N2LO`.
- btgrid `/scratch/submit/cms/wmass/scetlib_np/Z_COM13_MSHT20_N3p0LL_btgrid_fineall`. Plots: `~/public_html/alphaS/260720_pdf_swap_msht20/`.

---

## Log

### 2026-07-20 (eve) — PDF-driven param-model inputs + full fixed-λ4 production launched

**Code (done):** `theory_correction.py` (new) + `param_model.py` (4 edits). The param model now
resolves its PDF-dependent inputs from the correction the datacard picked: reads
`{pdf_set, nnlo_sing, dyturbo}` from that CorrZ's own build metadata (`read_corr_inputs(tag)`,
tag from `lambda_central`), and the btgrid from a `pdf_set→btgrid` map (`PDF_BTGRID`) + a
`base.conf` pdf_set guard. Explicit ctor args still win; no-tag → CT18Z defaults; works for ANY
correction tag (no per-tag maintenance). CT18Z is behavior-preserving (nnlo_sing byte-identical to
old default). Accepted risk (documented): reads the CorrZ at fit time — the FO/singular paths live
nowhere else for now; freezing σ_ns into the datacard is the deferred proper fix. Smoke-tested
(both tags resolve, guard OK, param_model imports). sigma_gen.py untouched.

**Runcards (done):** mirrored the old MSHT20 lattice_fine runcards into
`TheoryCorrections/SCETlib/com13_msht20_newnps_n3+0ll_lattice_lambda4bugfix_fine[/_pdfvars]`
(content identical to areimers' old ones; ONLY change = `target_precision_rel` 1e-5→1e-3). Z only.

**Full production LAUNCHED (2026-07-20 21:46, detached, overnight):**
`run_msht20_full_production.sh` (THREADS=320, fixed build, rel 1e-3) — RUNS only:
resummed (56 NP vars) → pdfas (members 0,2,5) → pdfvars (members 0..64), 11480 bins each.
Monitor `/tmp/msht20_overnight.progress`; sentinel `/tmp/msht20_overnight.done`.
**Morning:** combine each stage (`scetlib-manage-condor.py combine`, pdf stages need the
member→vars merge) → `make_theory_corr` (central + pdfvars + pdfas, mirror the old MSHT20 recipe:
`-m <msht20 gendist> -g scetlib_dyturbo --proc z --eras 13TeVGen --qtCutoff 1.0 --minnloh nominal_gen
--axes Q Y qT`, Zmumu-only copy `make_theory_corr_zmumu_only.py`, nnlo_sing REUSED (λ4-blind),
DYTurbo reused) → full `LatticeNPLambda4Bugfix_MSHT20` correction → histmaker → setupRabbit → fit vs CT18Z.
NB member counts: pdfvars=65, pdfas=3; resummed vars=56.


### 2026-07-20 — ROOT CAUSE of the low-qT residual: TRUNCATED beamfunc grid (order arg)

- Real-MSHT20-grid validation closed the resum tilt + (with MSHT20 nonsingular) the high-qT bias,
  but left a low-qT residual: bin0 +11%, 2–6 GeV −3%, tail ~−1%. CT18Z baseline via the SAME tool
  closes FLAT to 0.2% (min 0.9973/max 0.9982, no spike/dip) → the residual is a real MSHT20 bug, not
  the method floor. bin0 is below qt_cutoff (pure resum) → the fault is in the btgrid `I_pert`.
- Config + λ both confirmed matching areimers' MSHT20 resummed (b0_over_bmax_nu=1, precision 1e-5,
  tanh_2, λ2=0.25/λ4=0.06/λ2ν=0.087/…, TNPs) → NOT a config/λ bug.
- **ROOT CAUSE: the `MSHT20nnlo_as118_beamfunc` grid is INCOMPLETE — 19 kernels vs CT18ZNNLO's 51**
  (missing all the high-order ones: P2_*, P0xP0xP0_*, P0xP1/P1xP0_*, pT_I2xP0_*, pT_I3_*, pT_I1xP1_*).
  Truncated beam function → wrong perturbative `I_pert` at low qT → the spike/dip.
- **The beamfunc order arg = the N3LL beam-function order, `N3LO` for EVERY PDF** (not the PDF's DGLAP
  order). CT18ZNNLO=51, MSHT20an3lo (N3LO)=51, MSHT20nnlo (generated w/o order per my WRONG advice)=19.
  **CORRECTION to the 2026-07-17 entry below:** the order is `N3LO`, NOT "no arg / NNLO". My "drop N3LO"
  advice truncated the grid.
- **FIX:** `rm -rf MSHT20nnlo_as118_beamfunc; scetlib-beamfunc-make-grids MSHT20nnlo_as118 0 N3LO qT_quark`
  (→ 51 kernels), then regenerate the btgrid shard, recombine (auto), revalidate → expect ~0.2% closure.

### 2026-07-17 — new-PDF btgrid prerequisite: beam-function grids (no rebuild)

- After flipping `pdf_set=MSHT20nnlo_as118`, the btgrid gen (`scetlib-run-qT.py … --bt-grid`) failed:
  `beamfunc::ConvInterpolator: Could not initialize convolution: f … for PDF MSHT20nnlo_as118`.
  Cause: SCETlib reads PDF⊗kernel convolutions from precomputed grids in
  `share/scetlib/beamfunc/<PDF>_beamfunc/`; the `MSHT20nnlo_as118_beamfunc/` dir was EMPTY
  (install has CT18ZNNLO + MSHT20an3lo, not plain nnlo-as118).
- **NO rebuild** — `build/bin/scetlib-beamfunc-make-grids` is already compiled; grids are runtime data.
  Generate (member 0 suffices for the btgrid; `--pdf-member 0`), CWD = `share/scetlib/beamfunc`:
  `LHAPDF_DATA_PATH=/cvmfs/sft.cern.ch/lcg/external/lhapdfsets/current/:/usr/share/lhapdf/LHAPDF LD_LIBRARY_PATH=$SCETLIB/build/lib $SCETLIB/build/bin/scetlib-beamfunc-make-grids MSHT20nnlo_as118 0 qT_quark`
- **GOTCHA — order arg:** match CT18Z = NO order arg (NNLO). The `N3LO` in `beamfunc_gen_logs/gen_msht_beamfunc.sh`
  was because THAT PDF was MSHT20aN3LO; passing N3LO for the nnlo PDF would mismatch CT18Z's DGLAP order.
- Template: user's own `beamfunc_gen_logs/gen_msht_beamfunc.sh` (loops members 1..104 for the PDF error set —
  not needed here; PDF unc comes from the correction pdfvars, not btgrid member variations).

### 2026-07-17 — ROOT CAUSE: the "MSHT20" btgrid is actually CT18Z (pdf_set never flipped)

- Phase-0 (added `--nonsingular-fo-sing`/`--nonsingular-dyturbo` to `sigma_gen_at_lambda.py`,
  reran with areimers' MSHT20 singular+DYTurbo) only moved the peak ratio 1.09→1.065. Nonsingular
  = real but minor (~2.5%). A ~6.5% resum-region tilt REMAINED.
- **Diagnosed:** the btgrid `/scratch/.../Z_COM13_MSHT20_N3p0LL_btgrid_fineall/` `base.conf` still
  says `pdf_set = CT18ZNNLO`, and the raw shard's EMBEDDED config confirms `pdf_set=CT18ZNNLO`.
  The grid is CT18Z content in an MSHT20-named dir — the `pdf_set` edit was missed. The 6.5% tilt
  = the true CT18Z→MSHT20 resummed PDF difference. All other perturbative settings already match
  areimers' MSHT20 resummed (`muf_min=1.40`, transition [0.2,0.6,1.0], αs 0.118, n3ll, nf5) →
  **`pdf_set` is the ONLY fix** (muf_min worry was a red herring).
- **FIX:** in the generation `base.conf`, `pdf_set = CT18ZNNLO` → `MSHT20nnlo_as118`; regenerate +
  recombine (was generated as ONE all-bins shard `..._bins_000_558360_...`, not condor fan-out).
- Phase-0 code change (nonsingular override args) is correct & kept — needed for a consistent
  MSHT20 σ_gen. After the real MSHT20 grid lands, rerun the validation (`validate_msht20_matched.log`
  command) → expect sub-% closure like CT18Z. THEN resume Phase-1 (metadata-driven PDF mechanism).
- Bonus for Phase 1: lavezzo's `TheoryCorrections/DYTURBO/nnlo-scetlibmatch-13TeV-<PDF>-finer-bin/`
  has a per-PDF layout (CT18Z, MSHT20, NNPDF40, PDF4LHC21, mb/mc ranges) → clean registry source.

### 2026-07-17 — σ_gen has 3 PDF-dependent inputs; only btgrid was swapped (validation tilt)

- MSHT20 btgrid validation (`sigma_gen_at_lambda.py`, LatticeNP_MSHT20 corr) does NOT close:
  ratio(model/ref) tilts 1.09→1.00 low→high qT, residual peaks at the xsec peak and →0 by ~30 GeV
  (plot `~/public_html/alphaS/260717_MSHT20_btgrid/sigma_gen.png`). Transition-region shape = a
  **nonsingular** (FO−singular) mismatch, not resum.
- **Root cause:** `σ_gen = σ_resum(btgrid) + [DYTurbo_FO − SCETlib_singular]` has THREE PDF-dependent
  inputs. Only the btgrid was swapped to MSHT20; the other two default to **CT18Z**
  (`sigma_gen._NONSING_FO_SING_DEFAULT`, `_NONSING_DYTURBO_DEFAULT`; also the param_model.py:396-397
  constructor defaults). ⇒ affects the **actual fit** too, not just validation.
- **MSHT20 inputs located** (via `print_command.py` on the corr — thanks Luca; they're in areimers' area, world-readable):
  - singular pkl: `/work/submit/areimers/wmass/TheoryCorrections/SCETlib/com13_msht20_newnps_n3+0ll_lattice_fine_nnlo_sing/inclusive_Z_COM13_MSHT20_N3+0LL_lattice_fine_nnlo_sing_combined.pkl`
  - DYTurbo 2d-vj FO: `/work/submit/areimers/wmass/TheoryCorrections/DYTURBO/nnlo-scetlibmatch-13TeV-MSHT20-finer-bin/scalevariations/z0/results_z-2d-nnlo-vj-MSHT20nnlo-{scale}-scetlibmatch.txt` (all 7 scales present)
- **Plumbing gap:** param model constructor takes `nonsingular_fo_sing`/`nonsingular_dyturbo` kwargs
  (fit-overridable via `--modelArgs` TODAY), but `sigma_gen_at_lambda.py` exposes only `--no-nonsingular`
  (no path override). Plan: PDF registry + metadata-driven auto-resolution (see Decisions/Open questions).

### 2026-07-17 — btgrid validation: use the LatticeNP corr, NOT plain MSHT20

- MSHT20 btgrid was built (grid at `/scratch/.../Z_COM13_MSHT20_N3p0LL_btgrid_fineall/`).
  Validating via `sigma_gen_at_lambda.py` crashed `KeyError: 'np_model'` in
  `lambda_central._parse_section` when given `scetlib_dyturbo_MSHT20_N3p0LL_N2LO_CorrZ` (plain).
- **Cause:** the *plain* `MSHT20` correction's `[Nonperturbative]` section is the OLD
  `omega`/`c_nu`/`delta_omega` NP parametrization (`np_model=None`) — the mW-analysis model,
  unreadable by the new-tanh-NP tooling. The `LatticeNP_MSHT20` correction is `np_model=tanh_2`
  (same family as the `FranksVals_CT18Z` baseline) and carries `lambda2/4`, `lambda2_nu/4_nu`, `lambda_inf*`.
- **Fix:** `--theory-corr .../scetlib_dyturbo_LatticeNP_MSHT20_N3p0LL_N2LO_CorrZ.pkl.lz4` (this is
  also the histmaker/fit primary corr → self-consistent validation). General rule: btgrid/param-model
  tooling needs the `LatticeNP*`/`FranksVals*` (tanh) corrections, never the plain `<PDF>` corr.

### 2026-07-17 — bt-grid regen recipe (MSHT20) + the b0nu1 trap

- **Copy the CORRECTED config from `/scratch`, NOT `/work`.** The `/work/.../com13_ct18z_btgrid_fineall/inclusive_..._fineall.ini` is the OLD card with NO `[Nonperturbative]`
  section → silently inherits `b0_over_bmax_nu = 0` → wrong perturbative γ_ν kernel (root cause
  of the ~0.8% low-qT / ~2% NP-off wiggle; fixed 2026-06-24, see scetlib
  `scetlib_run/BTGRID_PRECISION_LOGBOOK.md`). The card that built the current DEFAULT grid is
  `/scratch/submit/cms/wmass/scetlib_np/Z_COM13_CT18Z_N3p0LL_btgrid_fineall/inclusive_..._fineall_b0nu1.ini`,
  which adds `[Nonperturbative] b0_over_bmax_nu = 1.` / `np_model_nu = tanh_2`. Copy base.conf + b0nu1 ini from /scratch.
- **The one edit:** `base.conf` `[QCD]` `pdf_set = CT18ZNNLO` → `MSHT20nnlo_as118`. `alphas_mu0=0.118`
  stays (as118 central); b*/geometry/NP are PDF-orthogonal. (`pdf_set` in base.conf; the b0nu1
  `[Nonperturbative]` block in the ini — both needed.)
- **Production:** condor, ~1148 shards (558,360 cells) via `scetlib-manage-condor(-submit).py -r <ini> --bt-grid ... submit`
  → `condor_submit`; then `combine -o <dir>` → `combined_btgrid.pkl` (what WRemnants loads;
  `.factorized.npz` is auto-memoized by the param model). NOT a couple-min local run. Mind the
  py3.9 login-node + PYTHONPATH-stub condor workaround (5 TeV W run).
- **Consume in the fit:** `_default_btgrid_dir()` hardcodes the CT18Z path → MSHT20 fit needs
  `--modelArgs btgrid_dir=<new grid dir>` (confirm exact arg name when wiring the fit).
- Suggested output dir name: `Z_COM13_MSHT20_N3p0LL_btgrid_fineall` (matches the `msht20` WRemnants tag).

### 2026-07-17 — kickoff: physics rationale + discovery

- **Physics rationale (from discussion).** Baseline PDF is **CT18Z** (N3p0LL, N2LO).
  Expectation: a central-PDF swap likely won't *resolve* the NP pathology (that's rooted
  in the NP functional form + resummation, per np-wall), but forward rapidity is where
  PDFs diverge most (low-x sea/gluon) and where F_eff blows up — so a different central
  shape *could* move where the NP sits and relieve the localized ptll tension. Worth doing
  as a robustness check reviewers want regardless. MSHT20 chosen over PDF4LHC21 because
  PDF4LHC21 is a Hessian combination that *includes* CT18 → weak contrast; MSHT20 is an
  independent global fit. NNPDF4.0 is the more extreme contrast if we want to bracket.
- **bt-grid PDF dependence (point #1, RESOLVED analytically).** `I_pert` is PDF-*loaded*
  (the reconstruction has no PDF convolution → the beam-function/collinear-PDF conv is baked
  into `I_pert`; `param_model.py:46-49,60-61`). The NP response is a ratio σ(λ)/σ(λ_c); to
  first order in a PDF distortion ε(b)=δI_pert/I_pert:
  **δRatio/Ratio = ⟨ε⟩_λ − ⟨ε⟩_{λc} = Cov_bT(ε, η)** under the central weighting, where
  η(b) is the NP variation's bT-reweighting. So only the bT-*flat* part of ε (PDF norm)
  cancels exactly; the surviving term is a covariance, second-order but NOT safely negligible
  because both ε (grows at large bT / low μ_b) and η (damping at large b*) peak at large bT.
  ⇒ For rigor, regenerate the grid per PDF; the residual is only ignorable when ε is bT-flat
  over the NP-relevant range. (Candidate for promotion to knowledge/.)
- **Discovery — corrections on disk** (`wremnants-data/data/TheoryCorrections/`):
  - baseline: `scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksVals_CT18Z_N3p0LL_N2LO_{,pdfas,pdfvars}_CorrZ.pkl.lz4`
  - MSHT20 available: `scetlib_dyturbo_LatticeNP_MSHT20_N3p0LL_N2LO_{,pdfas,pdfvars}_CorrZ.pkl.lz4`
    and plain `scetlib_dyturbo_MSHT20_N3p0LL_N2LO_{,pdfas,pdfvars}_CorrZ.pkl.lz4`. Also
    `LatticeNP_CT18Z` (matched-pair partner) exists. **No `FranksVals_MSHT20`.**
  - ByHelicity AlphaS/PDFsFromCorrs inputs exist for MSHT20 (`.../ByHelicity/AlphaS/w_z_gen_dists_scetlib_dyturbo_LatticeNP_MSHT20_N3p0LL_N2LO_pdfas_..._skimmed.hdf5`, etc.).
- **Baseline artifacts:** histmaker `260623_Zhistmaker/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksVals_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5`;
  current fits in np-wall `runs.yaml` (260716/260717 `2D_*`, `funcboundScan_*`, `priors_*`).
  Resolved-physical config = freeze `lambda4_nu=0`; σ(αs)=0.4423 (EDM 5.6e-14). α_S is
  NP-treatment-dominated (spans ~2.5–3σ across walled/unwalled).

---

## Findings

1. MSHT20 SCETlib+DYTurbo corrections (nominal+pdfas+pdfvars) already exist on disk → the
   PDF swap needs no new SCETlib production on the `LatticeNP`/plain route. — (evidence: `ls wremnants-data/data/TheoryCorrections/`)
2. The param-model postfit is ≈ independent of the NP-central reference (λ_central) because
   prediction(λ)=R·σ_gen(λ); so `LatticeNP_MSHT20` ≈ a nonexistent `FranksVals_MSHT20` for
   the PDF question, to param-model accuracy (<0.05%). — (evidence: port-doc factorization + physical-lambda λ-response validation)
3. bt-grid PDF residual in the NP response = `Cov_bT(ε,η)`, second-order but co-located at
   large bT → regenerate per PDF for rigor. — (evidence: this logbook 2026-07-17)

---

## Open questions

- Does swapping to MSHT20 improve the ptll-projection GOF, and where (peak=NP/resummation
  vs tail=PDF-friendly)?
- Do the postfit NP λ stay unphysical under MSHT20 (⇒ pathology PDF-robust) or move
  (⇒ PDF↔NP degeneracy)?
- Does α_S central + its NP-treatment spread shift with the PDF?

---

## Decisions

- 2026-07-17 — MSHT20 as the test PDF (not PDF4LHC21) — independent global fit; PDF4LHC21 contains CT18Z (weak contrast).
- 2026-07-17 — reuse CT18Z bt grid for the first pass; regenerate under MSHT20 as a cross-check — grid PDF residual is second-order Cov(ε,η).
