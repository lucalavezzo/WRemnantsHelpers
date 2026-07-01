# Z b-mass uncertainty study

## Study question
Define and implement an additional uncertainty on Z data to cover b-quark mass effects, using:
- nominal MiNNLO Z sample in 5 flavor scheme (5FS) with massless b quarks;
- alternate MiNNLO Z+bbar sample in 4 flavor scheme (4FS) with massive b quarks.

## Guiding questions
- What overlap region between 5FS and 4FS best represents the same heavy-flavor physics for a swap-based correction?
- Should the resulting nuisance be shape-only, or shape+rate?
- Which event definition (for example based on B hadrons) gives stable and interpretable behavior across `ptVgen` and `absYVgen`?
- Does `Zbb_MiNNLO` contain non-muon Z decays (for example `ee` or `tautau`) that could bias this study setup?
- How should the paper prescription in arXiv:1803.04336 (5FS B-veto + 4FS addback) map onto our current swap implementation?

## Current understanding
- The target is a robust nuisance construction that captures the difference in heavy-flavor treatment (massless-b 5FS vs massive-b 4FS) without double counting existing uncertainties.
- Theoretical references to anchor the prescription:
  - arXiv:1904.09382 (4FS/5FS matching logic for heavy flavor in Z+jets context).
  - arXiv:2404.08598 (NNLO+PS Z+bbar in 4FS with explicit b-mass effects).
- Current `bottom_sel` implementation in `w_z_gen_dists.py`:
  - Identify B hadrons using PDG-digit logic in `wremnants/include/theoryTools.hpp` (`isBHadron` + `finalStateBHadronIdx`).
  - Keep particles with `GenPart_status` in `{1,2}`.
  - Define `bottom_sel = (bHad_pt.size() >= 1)` (at least one final-state B hadron, with no additional B-hadron kinematic cuts).

## Decisions taken so far
- Create a dedicated study folder under `agents/studies/z_bmass_uncertainty/`.
- Track incremental progress in this README and in `runlog.md` during the session.
- Next technical step is to define a concrete template-based nuisance prescription (central/up/down) and normalization strategy.
- Revised approach (per discussion): do not introduce a separate histmaker path; instead extend the canonical `w_z_gen_dists.py` outputs and inspect distributions before changing any swap selection.
- Use B-hadron-based swap-region definition:
  - current: `bottom_sel = (bHad_pt.size() >= 1)`;
  - previous reference point: `bottom_sel = (subB_pt5 > 10)`.
- Keep using a fresh unique tag for every hist/plot iteration (for example `bhad_diag_<YYMMDD_HHMMSS>`).

## Latest iteration (2026-02-13, tag `bhad_diag_260213_143453`)
- Resolved a runtime bug in canonical histmaker:
  - in `$WREM_BASE/scripts/histmakers/w_z_gen_dists.py`, changed
    - `GenPart_pt[bHadIdx]` to `Take(GenPart_pt, bHadIdx)`;
  - reason: `bHadIdx` is an index vector; bracket access was interpreted as boolean-mask indexing and caused vector-size mismatch.
- Produced new tagged inputs:
  - `/scratch/submit/cms/alphaS/260213_gen_massiveBottom/w_z_gen_dists_maxFiles_20_hadronsSel_massive_bhad_diag_260213_143453.hdf5`
  - `/scratch/submit/cms/alphaS/260213_gen_massiveBottom/w_z_gen_dists_maxFiles_200_nnpdf31_hadronsSel_massless_bhad_diag_260213_143453.hdf5`
- Produced tagged plots:
  - `/home/submit/lavezzo/public_html/alphaS/260213_z_bb/hadrons/bhad_diag_260213_143453/`
- Key numbers from `nBhad_pt5`:
  - Nominal MiNNLO: `f(nB>=1)=0.0484`, `f(nB>=2)=0.0404`;
  - Massive-b MiNNLO: `f(nB>=1)=0.9333`, `f(nB>=2)=0.8137`.
- Swap-related fractions:
  - `% selected for swap` (massive): `0.8138`;
  - `% selected for swap` (massless): `0.0408`;
  - ratio of events with at least one b or bbar (massless/massive): `3.862`.
- Inclusive corrected/nominal shape ratio (from `nominal_gen` projections):
  - `ptVgen`: min/max/mean = `0.936 / 0.989 / 0.970`;
  - `absYVgen`: min/max/mean = `0.963 / 0.984 / 0.971`.
- Immediate interpretation:
  - 4FS `Zbb_MiNNLO` sample is heavily enriched in multi-B-hadron events relative to 5FS inclusive `Zmumu_MiNNLO`.
  - Current `bottom_sel` (`subB_pt > 5`) selects a large fraction in 4FS but a small tail in 5FS, indicating a strong normalization effect in any direct swap prescription.

## Latest iteration (2026-02-13, tag `bhad_sel10_260213_152614`)
- Updated swap selection in canonical histmaker:
  - `bottom_sel` changed from `(subB_pt > 5)` to `(subB_pt5 > 10.f)`.
  - This encodes the proposed region: at least two B hadrons with subleading `pT > 10 GeV`.
- Ran hist+plot with normalized swap (`--normalize`):
  - output plots:
    - `/home/submit/lavezzo/public_html/alphaS/260213_z_bb/hadrons/bhad_sel10_normswap_260213_152614/`
- Key normalization numbers:
  - selected fractions: `f4FS=0.5627`, `f5FS=0.0236`;
  - selected-yield ratio (`5FS/4FS`) from plot output: `3.235`.
- `pT_Z` impact for normalized swap (corrected/nominal):
  - overall min/max/mean: `0.9968 / 1.0223 / 0.9998`;
  - mean in bins:
    - `0-10 GeV`: `0.9974`
    - `10-30 GeV`: `0.9983`
    - `30-60 GeV`: `1.0050`
    - `60-100 GeV`: `1.0136`
- Reference (unnormalized swap) remained much larger:
  - overall mean `0.9841` for corrected/nominal `pT_Z`.
- Interpretation:
  - With tighter overlap definition plus normalization of selected component, the net `pT_Z` effect is modest and predominantly shape-like.

## Latest iteration (2026-02-13, tag `bhad_allvars_260213_160518`)
- Added broad diagnostic histogram set in canonical histmaker:
  - gen b-jets: `n_bjets`, `lead_bjet_pt`, `sublead_bjet_pt`, `lead_bjet_eta`, `sublead_bjet_eta`, `m_bb_jet`, `dR_bb_jet`;
  - LHE bb: `n_lhe_init_bbbar`, `n_lhe_fin_bbbar`, `n_lhe_bbbar`, `lhe_bbbar_fin_min_pt`, `lhe_bbbar_fin_max_pt`, `m_bb_lhe`, `dR_bb_lhe`.
- Updated `studies/z_bb/plot_narf.py` to include all these variables in `plot_specs`.
- Output plots:
  - `/home/submit/lavezzo/public_html/alphaS/260213_z_bb/hadrons/bhad_allvars_260213_160518/`
- First-pass physics outcome from new variables:
  - Strong difference in resolved gen b-jet activity:
    - `mean(n_bjets)`: `0.461` (4FS) vs `0.016` (5FS).
  - LHE-level bb kinematics are much closer in shape:
    - `mean(m_bb_lhe)`: `68.75` (4FS) vs `67.75` (5FS),
    - `mean(dR_bb_lhe)`: `2.685` (4FS) vs `2.673` (5FS).
  - LHE multiplicities indicate very different process composition:
    - `mean(n_lhe_fin_bbbar)`: `2.000` (4FS) vs `0.038` (5FS),
    - `mean(n_lhe_init_bbbar)`: `0.000` (4FS) vs `0.019` (5FS).
- Interpretation:
  - 4FS and inclusive 5FS differ strongly in heavy-flavor event composition at reco-like/object level, even when some LHE-shape projections look similar.

## Latest iteration (2026-02-14, tag `lepflv_260214_1`)
- Added dedicated massive-sample flavor check utility:
  - `studies/z_bb/check_massive_z_lepton_flavor.py`
  - counts LHE final-state lepton flavors (`e`, `mu`, `tau`) for `Zbb_MiNNLO`.
- Added container helper to run massive-only histmaker and flavor check together:
  - `agents/run_massive_lepton_flavor_check.sh`
- Ran massive-only histmaker + check (20 files):
  - hist output:
    - `/scratch/submit/cms/alphaS/260214_gen_massiveBottom/w_z_gen_dists_maxFiles_20_hadronsSel_massive_lepflv_260214_1.hdf5`
  - flavor result (`970000` events):
    - `mu-only (2 mu): 0`
    - `e-only (2 e): 970000`
    - `tau-only (2 tau): 0`
    - `mixed/other: 0`
- Interpretation:
  - The current `Zbb_MiNNLO` sample used here is purely `Z -> ee` at LHE final state, not `Z -> mumu`.
  - This confirms the suspicion that the massive sample is not muon-decay matched.

## Latest synthesis (2026-02-14, slide-backed conclusions)
- LHE-level conclusion:
  - Direct LHE-quark swapping is not a physically consistent nuisance construction here, because the comparison mixes flavor schemes (5FS vs 4FS) and currently also decay content (`Zmumu` vs `Zbb` sample that is `ee`-only in the tested files).
- Jet-level conclusion:
  - Jet-tagged handles are weak for this swap definition in current NanoAOD-level diagnostics: many events remain in zero-tag categories and differences are dominated by composition/normalization effects.
  - Switching jet tagging from hadron flavour to parton flavour gives qualitatively similar behavior, so it does not resolve the core issue.
- B-hadron-level conclusion:
  - B-hadron-based observables are the most stable basis for a swap-region definition in this study.
  - Shape ratios are comparatively flat, but normalization mismatch is large.
- Swap-on-`ptVgen` conclusion:
  - Unnormalized swap induces a too-large systematic shift.
  - Normalized swap yields a much flatter, mostly shape-like effect and is currently the more viable nuisance candidate, with the caveat that physical interpretation still needs agreement.

## Requested check (2026-02-16)
- Request: test a different swap-region definition that only requires one B hadron and does not apply additional B-hadron cuts.
- Implementation status:
  - Updated canonical histmaker selection to `bottom_sel = (bHad_pt.size() >= 1)`.
  - Completed with tagged run `bhad_ge1_260216_50thr` (including normalized and unnormalized comparisons).

## Latest iteration (2026-02-16, tag `bhad_ge1_260216_50thr`)
- Executed with requested thread count (`50`) and reduced-stat sample sizes (`20` massive, `200` massless):
  - hist files:
    - `/scratch/submit/cms/alphaS/260216_gen_massiveBottom/w_z_gen_dists_maxFiles_20_hadronsSel_massive_bhad_ge1_260216_50thr.hdf5`
    - `/scratch/submit/cms/alphaS/260216_gen_massiveBottom/w_z_gen_dists_maxFiles_200_nnpdf31_hadronsSel_massless_bhad_ge1_260216_50thr.hdf5`
  - plot outputs:
    - unnormalized: `/home/submit/lavezzo/public_html/alphaS/260216_z_bb/hadrons/bhad_ge1_260216_50thr/`
    - normalized: `/home/submit/lavezzo/public_html/alphaS/260216_z_bb/hadrons/bhad_ge1_260216_50thr_norm/`
- Selection-fraction diagnostics from `nominal_gen`:
  - `% selected for swap` (4FS massive): `1.0000`
  - `% selected for swap` (5FS nominal): `0.0574`
  - selected-yield ratio (`5FS/4FS`, selected region): `4.4254`
- Inclusive corrected/nominal ratios:
  - unnormalized swap:
    - `ptVgen`: min/max/mean = `0.9210 / 0.9786 / 0.9559`
    - `absYVgen`: min/max/mean = `0.9478 / 0.9738 / 0.9569`
  - normalized swap:
    - `ptVgen`: min/max/mean = `0.9850 / 1.0544 / 0.9995`
    - `absYVgen`: min/max/mean = `0.9763 / 1.0183 / 0.9980`
- Interpretation:
  - This `>=1` B-hadron selection is broader than the prior `subB_pt5 > 10` region and selects all events in the 4FS sample while still selecting only a small fraction of the 5FS sample.
  - As before, unnormalized swap is too rate-dominant; normalized swap remains the more viable nuisance-shape construction.

## Latest iteration (2026-02-16, tags `lepcheck_260216_50thr` and `lepcheck_aux_260216_50thr`)
- Request: compare dilepton mass and lepton kinematics for bare/postFSR leptons vs dressed leptons, and inspect boson variables (`mass`, `pT`, `|y|`).
- Technical updates in canonical histmaker (`$WREM_BASE/scripts/histmakers/w_z_gen_dists.py`):
  - fixed `--singleLeptonHists` + `--addBottomAxis` bug in `prefsr/postfsr` lepton hist booking (`bottom` -> `bottom_sel`);
  - added dressed single-lepton histograms in the `--singleLeptonHists` branch:
    - `nominal_dressedLepPt1/2`, `nominal_dressedLepEta1/2`.
- Produced fresh tagged files:
  - `/scratch/submit/cms/alphaS/260216_gen_massiveBottom/w_z_gen_dists_maxFiles_20_hadronsSel_massive_lepcheck_260216_50thr.hdf5`
  - `/scratch/submit/cms/alphaS/260216_gen_massiveBottom/w_z_gen_dists_maxFiles_200_nnpdf31_hadronsSel_massless_lepcheck_260216_50thr.hdf5`
  - `/scratch/submit/cms/alphaS/260216_gen_massiveBottom/w_z_gen_dists_maxFiles_10_hadronsSel_massive_lepcheck_aux_260216_50thr.hdf5`
  - `/scratch/submit/cms/alphaS/260216_gen_massiveBottom/w_z_gen_dists_maxFiles_100_nnpdf31_hadronsSel_massless_lepcheck_aux_260216_50thr.hdf5`
- Output plots:
  - `/home/submit/lavezzo/public_html/alphaS/260216_z_bb/leptons/lepcheck_aux_260216_50thr/`
- Key observations:
  - Bare/postFSR dilepton mass is very similar between samples (`mean_4FS/mean_5FS ~ 0.997` for `ew_mll`).
  - Bare/postFSR single-lepton kinematics are available and comparable (`nominal_ewLepPt{1,2}`, `nominal_ewLepEta{1,2}`).
  - Dressed-lepton observables are not physically comparable in current sample setup:
    - massive sample (`Zbb_MiNNLO`) is `Z->ee`-only in tested files;
    - dressed variable definition is muon-flavor based in this workflow;
    - this leads to strong artificial suppression/shape distortion in 4FS dressed quantities.
  - Boson-level checks (preFSR / EW-postFSR / dressed):
    - preFSR and EW-postFSR comparisons are usable for shape/scale diagnostics;
    - dressed boson observables inherit the same flavor-mismatch caveat as dressed lepton observables.

## Requested check (2026-02-16): use `ThePEG::PDT` for B-hadron classification
- Request:
  - Consider replacing the local `isBHadron` helper with an external classifier based on `ThePEG::PDT`.
- Quick implementation audit:
  - Current logic is in `$WREM_BASE/wremnants/include/theoryTools.hpp` (`isBHadron`, `finalStateBHadronIdx`) and is used by canonical histmaker path in `$WREM_BASE/scripts/histmakers/w_z_gen_dists.py`.
  - A similar `isBHadron` implementation also exists in `../WRemnants/wremnants/include/utils.hpp`.
  - No active `ThePEG::PDT` (or equivalent HepPID helper) usage was found in this analysis path.
- Decision for current study loop:
  - Keep the existing lightweight PDG-digit `isBHadron` logic for now (no external dependency change in this iteration).
  - Prefer a future cleanup that unifies duplicated B-hadron classification in one WRemnants helper before considering any heavier external dependency.

## Requested check (2026-02-16, follow-up): run with `PDT`-style B-hadron identifier
- Request:
  - Replace the current `isBHadron` behavior with a `ThePEG::PDT`-style B-content classification and rerun hist+plots for direct comparison against prior baseline.
- Planned implementation (this iteration):
  - Patch active helper in `$WREM_BASE/wremnants/include/theoryTools.hpp`.
  - Keep selection definition unchanged (`bottom_sel = (bHad_pt.size() >= 1)`) so only classifier behavior is varied.
  - Produce a new tagged run in reduced-stat mode (`20` massive, `200` massless) matching prior quick-comparison scale.

## Latest iteration (2026-02-16, tag `bhad_pdtstyle_260216_50thr`)
- Classifier implementation:
  - In `$WREM_BASE/wremnants/include/theoryTools.hpp`, split B-hadron logic into:
    - `isBHadronLegacy(...)` (previous implementation),
    - `isBHadronPDTStyle(...)` (digit-scan `PDT`-style flavor-content check),
    - selector switch `kBHadronIdMode` for easy toggling.
  - Active mode for this run: `BHadronIdMode::PDTStyleDigits`.
- Produced files:
  - hist files:
    - `/scratch/submit/cms/alphaS/260216_gen_massiveBottom/w_z_gen_dists_maxFiles_20_hadronsSel_massive_bhad_pdtstyle_260216_50thr.hdf5`
    - `/scratch/submit/cms/alphaS/260216_gen_massiveBottom/w_z_gen_dists_maxFiles_200_nnpdf31_hadronsSel_massless_bhad_pdtstyle_260216_50thr.hdf5`
  - plot outputs:
    - unnormalized: `/home/submit/lavezzo/public_html/alphaS/260216_z_bb/hadrons/bhad_pdtstyle_260216_50thr/`
    - normalized: `/home/submit/lavezzo/public_html/alphaS/260216_z_bb/hadrons/bhad_pdtstyle_260216_50thr_norm/`
- Key diagnostics (compare to baseline `bhad_ge1_260216_50thr`):
  - `% selected for swap` (4FS massive): `1.0000` (baseline `1.0000`)
  - `% selected for swap` (5FS nominal): `0.0599` (baseline `0.0574`)
  - selected-yield ratio (`5FS/4FS`, selected region): `4.6181` (baseline `4.4254`)
  - `nBhad_pt5` fractions:
    - Nominal MiNNLO: `f(nB>=1)=0.0487`, `f(nB>=2)=0.0405` (baseline about `0.048x/0.040x`)
    - Massive MiNNLO: `f(nB>=1)=0.9334`, `f(nB>=2)=0.8155` (baseline `0.9333/0.8137`)
- Interpretation:
  - Under this trial `PDT`-style identifier, the broad `>=1`-B-hadron selection behavior is very similar to baseline.
  - The largest visible change in quick diagnostics is a small upward shift in selected 5FS fraction and selected-yield ratio.

## Latest iteration (2026-02-16, tag `bhad_bothcmp_260216_50thr`): legacy vs PDT-style event disagreement
- Goal:
  - Evaluate both B-hadron classifiers in the same run and measure whether they disagree on event content.
- Instrumentation:
  - Added per-event dual outputs in canonical histmaker path:
    - `bHadIdx_legacy`, `bHadIdx_pdt`,
    - `nBhad_idx_symdiff`,
    - `bHad_any_disagree` (any index disagreement),
    - `bottom_sel_disagree` (`(nBhad>=1)` disagreement).
- Produced files:
  - `/scratch/submit/cms/alphaS/260216_gen_massiveBottom/w_z_gen_dists_maxFiles_20_hadronsSel_massive_bhad_bothcmp_260216_50thr.hdf5`
  - `/scratch/submit/cms/alphaS/260216_gen_massiveBottom/w_z_gen_dists_maxFiles_200_nnpdf31_hadronsSel_massless_bhad_bothcmp_260216_50thr.hdf5`
- Disagreement summary (weighted event fractions):
  - Massive sample (`Zbb_MiNNLO`):
    - `frac(event any index disagreement)` = `0.05666558`
    - `frac(event bottom_sel disagreement)` = `0.00000000`
    - `mean symmetric-diff count` = `0.05806189`
  - Nominal sample (`Zmumu_MiNNLO`):
    - `frac(event any index disagreement)` = `0.00488513`
    - `frac(event bottom_sel disagreement)` = `0.00250351`
    - `mean symmetric-diff count` = `0.00492208`
- Interpretation:
  - Yes, the two classifiers do disagree at event level.
  - For this broad selection (`bottom_sel = nBhad>=1`), disagreement in the selected/not-selected event flag is:
    - negligible in massive sample (`0`),
    - small but nonzero in nominal sample (`~0.25%` weighted).

## Slide update (2026-02-16): source-of-truth wording and `$b$` formatting cleanup
- Updated backup code slide wording to cite the library helper as source of truth:
  - `wremnants/include/theoryTools.hpp` is now explicitly referenced in slide-8 code header text.
- Fixed LaTeX title math escaping in slide generator:
  - in `scripts/study_slides.py`, title/subtitle now preserve inline math (`$...$`) instead of escaping `$`.
- Regenerated and compiled updated deck:
  - `agents/studies/z_bmass_uncertainty/slides/b_quark_mass.pdf`
  - copied to: `/home/submit/lavezzo/public_html/alphaS/260216_study_slides/b_quark_mass.pdf`

## Requested check (2026-02-18): read arXiv:1803.04336
- Request:
  - Resume the study and extract actionable guidance from `https://arxiv.org/pdf/1803.04336`.
- Status:
  - `answered`.
- Paper synthesis most relevant to this study:
  - Their recommended combination is not a direct event swap; it is:
    - `improved = (5FS with B-hadron veto) + (4FS inclusive bb)`.
  - They define the comparison in shape space via
    - `R(pT) = normalized(improved) / normalized(plain 5FS)`.
  - Reported impact on inclusive NC-DY `pT(ll)` is typically about `+-1%` near the Z peak, with stronger dependence away from the peak.
  - In their toy transfer to CC-DY, the induced `mW` shift from b-mass treatment is generally `< 5 MeV`.
- Implication for our current setup:
  - Our normalized-swap behavior is qualitatively aligned with their message (small, mostly shape-like correction), but our current construction should be reframed as a B-veto/addback-style decomposition rather than a raw sample replacement.
  - The large rate mismatch we repeatedly observed is expected if one does direct replacement without orthogonal region bookkeeping.
- Immediate follow-up to align with the paper:
  - Build explicit orthogonal components in our workflow:
    - `5FS_Bveto` (strict no-B-hadron region),
    - `4FS_Binclusive` (at least one B hadron),
    - and compare `R(ptVgen)` against plain `5FS` in fiducial-normalized form.

## Requested check (2026-02-18, follow-up): full-paper rigor pass and gap audit
- Request:
  - Re-read the full paper (Sections 1-6 + Appendix A) and identify what our current workflow may still miss.
- Status:
  - `answered`.
- Additional gaps identified beyond the first synthesis:
  - `R(pT)` normalization mismatch:
    - Paper Eq. (4.2) compares *fiducial-normalized shapes*.
    - Our current code ratio uses absolute scaled yields by default; `--normalize` rescales only the swapped component, not the final inclusive distributions to unit fiducial area.
  - Setup-consistency caveat:
    - Paper comparisons assume consistent leptonic setup across 4FS and 5FS samples.
    - Our tested 4FS sample is `Z->ee`-only while 5FS sample is `Zmumu`, so shape differences can absorb decay-content mismatch.
  - Uncertainty model incompleteness:
    - Paper emphasizes matching/PS-model uncertainty (`mu_sh`, POWHEG `h`, Pythia vs Herwig), often comparable to or larger than nominal bottom-mass shape effects.
    - Our nuisance prototyping currently uses one effective setup and no explicit envelope across matching/PS variations.
  - Bin dependence that can hide in inclusive plots:
    - Paper finds stronger dependence in dilepton-mass bins (up to `~+3-4%` at low mass, `~-1%` at high mass).
    - Our headline checks have mainly focused on inclusive `ptVgen` and `absYVgen`.
  - Formal target for CC transfer:
    - Paper propagates via a transfer function `R` and applies `1/R(pT)` in CC-like studies.
    - We have not yet built this transfer-function validation chain in the current study branch.

## Open points
- Exact observable basis for the nuisance (inclusive vs category-based vs differential in analysis bins).
- Whether to constrain normalization impact separately from shape impact.
- Mapping of the 4FS/5FS difference onto fit nuisance priors and correlations across channels.
- Validate Z-decay lepton flavor composition in the massive sample (`Zbb_MiNNLO`) and decide whether a muon-only filter is needed. Status: `answered` (`Zbb_MiNNLO` here is `ee`-only in tested files).
- Decide if normalized swap should be adopted as default nuisance construction, and document the associated physics caveat clearly.

## Knowledge and question tracker
- Learned:
  - With B-hadron selection (`subB_pt5 > 10`), selected fractions still differ strongly (`f4FS~0.56`, `f5FS~0.024`), and the selected-yield hierarchy remains a dominant effect.
  - This indicates selection-fraction mismatch and total-normalization hierarchy both matter for swap construction.
  - LHE-level swapping is not a reliable physical handle in the current sample configuration (5FS/4FS + decay-content mismatch).
  - Parton-flavour jet-tag diagnostics are qualitatively similar to hadron-flavour diagnostics, so they do not provide a materially better swap handle.
- Emerging questions:
  - Are B-hadron-only criteria sufficient to isolate a truly swappable overlap? Status: `partial` (best-performing option so far, but still normalization-dominated).
  - Would adding tighter topology constraints (for example on subleading B-hadron kinematics) improve normalized shape agreement? Status: `partial` (improved `pT_Z` behavior seen with `subB_pt5 > 10`, still needs higher-stat confirmation).
  - Is the residual mismatch mainly from physics-content differences between inclusive 5FS and dedicated 4FS Zbb samples? Status: `partial` (evidence supports this, but not yet isolated quantitatively).
  - Which massive-b dataset (or generator-level decay filter) should be used to enforce `Z -> mumu` consistency with the nominal sample? Status: `open`.
  - Should normalized swap be treated as shape-only nuisance or shape+rate nuisance with explicit prior? Status: `open`.

## Next steps
- Convert the observed large normalization mismatch into an explicit nuisance design choice:
  - either shape-only (normalized replacement) or shape+rate (with constrained prior).
- Run one higher-stat tagged iteration (same workflow, fresh tag) to reduce statistical noise in tails, focusing on normalized-swap stability in `ptVgen` and `absYVgen`.
- Compare additional category boundaries (for example `nBhad_pt5>=1` vs `>=2`) before changing `bottom_sel`.
- Clarify/replace the massive sample so decay channel matches (`Z -> mumu`) before finalizing nuisance prescription.

## Latest iteration (2026-02-18, tag `bhad_hiStat_260218_200thr`)
- Reviewed and validated user cleanup changes before production:
  - fixed `prefsr`-column filter wiring for new lepton fiducial selection under `--addBottomAxis`;
  - fixed LHE bb histogram column names (`m_bb_lhe`/`dR_bb_lhe`) in pre/post-selection blocks;
  - fixed B-hadron classifier compile issue in `theoryTools.hpp` (`isBHadronLegacy` -> `isBHadron`);
  - updated plotter to read both legacy and `presel_*` histogram names.
- High-stat run completed with requested settings:
  - massive: full (`--max-files-massive -1`);
  - massless: `1000` files;
  - threads: `200`.
- Outputs:
  - `/scratch/submit/cms/alphaS/260218_gen_massiveBottom/w_z_gen_dists_maxFiles_m1_hadronsSel_massive_bhad_hiStat_260218_200thr.hdf5`
  - `/scratch/submit/cms/alphaS/260218_gen_massiveBottom/w_z_gen_dists_maxFiles_1000_nnpdf31_hadronsSel_massless_bhad_hiStat_260218_200thr.hdf5`
  - plots:
    - unnormalized: `/home/submit/lavezzo/public_html/alphaS/260218_z_bb/hadrons/bhad_hiStat_260218_200thr/`
    - normalized: `/home/submit/lavezzo/public_html/alphaS/260218_z_bb/hadrons/bhad_hiStat_260218_200thr_norm/`
- Key printed diagnostics:
  - `% selected for swap` (4FS): `1.0`
  - `% selected for swap` (5FS): `0.06670`
  - selected-yield ratio (`5FS/4FS`, selected region): `3.81426`

## Requested check (2026-02-18): initial-state flavor composition histogram (Table-1-like)
- Request:
  - Add a preselection-only LHE-level histogram that classifies initial-state quark flavor (`ddbar`, `uubar`, `ssbar`, `ccbar`, `bbbar`, `other/mixed`).
- Implementation:
  - In canonical histmaker, added event-level code:
    - `lhe_init_flavor_bin = 0..5` from incoming LHE partons (`status==-1`, `|pdgId|<=5`), where:
      - `0=other/mixed`, `1=d`, `2=u`, `3=s`, `4=c`, `5=b`.
  - Added preselection histogram only:
    - `presel_lhe_init_flavor`.
  - Plotter update:
    - include `lhe_init_flavor` in `plot_specs`,
    - print table-like fractions for both samples from this histogram.
- Smoke validation (`1` massive + `1` massless file):
  - plot output:
    - `/home/submit/lavezzo/public_html/alphaS/260218_z_bb/hadrons/smoke_initflavor_260218/`
  - example fractions (smoke stats):
    - Nominal MiNNLO: `other~0.633`, `dd~0.146`, `uu~0.175`, `ss~0.039`, `cc~0.006`, `bb~0.0007`.
    - Massive Zbb MiNNLO: `other~0.939`, `dd~0.024`, `uu~0.029`, `ss~0.0056`, `cc~0.0015`, `bb~0.0`.

### Container run command
In the normal Singularity runtime, execute:
`bash agents/run_zbb_bhad_diag.sh bhad_diag_<new_tag>`

This runs both tagged histmakers and then `studies/z_bb/plot_narf.py` on the produced files.

## Requested check (2026-02-18): GenPart mother flavor for Z production
- Request:
  - Track quark flavor pair that directly forms the generated Z (GenPart mother-based), not only LHE initial-state flavor.
- Status:
  - `answered`.
- Implementation summary:
  - In `/home/submit/lavezzo/alphaS/gh/WRemnants/scripts/histmakers/w_z_gen_dists.py`:
    - added `z_mother_flavor_bin` from GenPart mother tracing of hard-process Z, with bins:
      - `0=other/mixed/unclassified`, `1=d`, `2=u`, `3=s`, `4=c`, `5=b`;
    - added histogram `presel_z_mother_flavor` (preselection).
  - In `studies/z_bb/plot_narf.py`:
    - added `z_mother_flavor` plot entry;
    - added printed fraction table for `z_mother_flavor` for both samples.
- Practical note:
  - This is more directly tied to “quarks that formed the generated Z” than LHE incoming-parton flavor, but is inherently more generator-record dependent.

## Requested tweak (2026-02-18): add preFSR dilepton mass window in bottom-axis filter
- Request:
  - Extend the existing preFSR lepton (`pt`, `absEta`) filter by requiring invariant mass within `15 GeV` of `91 GeV`.
- Status:
  - `answered`.
- Implemented cut (in `if args.addBottomAxis and isZ` block):
  - `std::fabs(prefsrV_mass - 91.) < 15.`
- Combined with existing requirements:
  - `prefsrLep_pt > 20`, `prefsrOtherLep_pt > 20`, `prefsrLep_absEta < 2.5`, `prefsrOtherLep_absEta < 2.5`.

## Latest iteration (2026-02-18, tag `bhad_hiStat_260218_200thr_genmother_m91w30`)
- Scope of this run:
  - included new preFSR bottom-axis filter mass window `|prefsrV_mass-91|<15`;
  - included new `presel_z_mother_flavor` histogram from GenPart mother tracing.
- Outputs:
  - `/scratch/submit/cms/alphaS/260218_gen_massiveBottom/w_z_gen_dists_maxFiles_m1_hadronsSel_massive_bhad_hiStat_260218_200thr_genmother_m91w30.hdf5`
  - `/scratch/submit/cms/alphaS/260218_gen_massiveBottom/w_z_gen_dists_maxFiles_1000_nnpdf31_hadronsSel_massless_bhad_hiStat_260218_200thr_genmother_m91w30.hdf5`
  - plots:
    - unnormalized: `/home/submit/lavezzo/public_html/alphaS/260218_z_bb/hadrons/bhad_hiStat_260218_200thr_genmother_m91w30/`
    - normalized: `/home/submit/lavezzo/public_html/alphaS/260218_z_bb/hadrons/bhad_hiStat_260218_200thr_genmother_m91w30_norm/`
- Key immediate observation:
  - `z_mother_flavor` is entirely in bin `0` for both samples (no resolved `dd/u u/ss/cc/bb`), so current GenPart mother matching did not find valid quark-pair assignments in this generator record.
- Consequence:
  - The histogram plumbing works end-to-end, but mother-pair extraction logic needs a refinement pass before physics interpretation.

## Latest iteration (2026-02-18, tag `bhad_hiStat_260218_200thr_genmother_iter2_m91w30`)
- Goal:
  - Fix GenPart mother-flavor extraction that previously returned only bin `0`.
- What changed:
  - `z_mother_flavor_bin` now uses hard-process `Z/gamma*` (`23` fallback `22`) and first non-boson ancestor flavor (`|pdgId|=1..5`).
- Outputs:
  - `/scratch/submit/cms/alphaS/260218_gen_massiveBottom/w_z_gen_dists_maxFiles_m1_hadronsSel_massive_bhad_hiStat_260218_200thr_genmother_iter2_m91w30.hdf5`
  - `/scratch/submit/cms/alphaS/260218_gen_massiveBottom/w_z_gen_dists_maxFiles_1000_nnpdf31_hadronsSel_massless_bhad_hiStat_260218_200thr_genmother_iter2_m91w30.hdf5`
  - plots:
    - `/home/submit/lavezzo/public_html/alphaS/260218_z_bb/hadrons/bhad_hiStat_260218_200thr_genmother_iter2_m91w30/`
    - `/home/submit/lavezzo/public_html/alphaS/260218_z_bb/hadrons/bhad_hiStat_260218_200thr_genmother_iter2_m91w30_norm/`
- Result:
  - Nominal sample now has populated GenPart flavor bins (non-zero `dd/u u/ss/cc/bb`).
  - Massive sample remains fully in `other/unclassified` for this definition.
- Interpretation:
  - The wiring and plotting are now functioning for nominal, but the massive sample generator record still does not expose a quark-ancestor handle compatible with this simple ancestor-based definition.

## Requested diagnostic (2026-02-18): `nBhad_weight` cross-check
- Request:
  - Use `nBhad_unity` and `nBhad_weight` to test whether event weights are unexpectedly distorting massive-sample normalization.
- Outcome:
  - `nBhad_weight` and `nBhad` are numerically identical in both samples in smoke tests.
  - Therefore `nominal_weight` does not add an extra hidden normalization effect relative to `weight` for this branch.
- Implication:
  - Normalization mismatch is not from an internal mismatch between `weight` and `nominal_weight`; dominant drivers remain sample-level normalization (`xsec/weight_sum`) and physics-content differences between `Zbb_MiNNLO` and inclusive `Zmumu_MiNNLO`.

## Requested plotting variant (2026-02-18): swapped-component factor `x2`
- Added reproducible plot control in `studies/z_bb/plot_narf.py`:
  - `--massive-scale <factor>` (default `1.0`).
- Regenerated from latest `iter2` hist files with:
  - `--massive-scale 2` (unnormalized and `--normalize` variants).
- Output dirs:
  - `/home/submit/lavezzo/public_html/alphaS/260218_z_bb/hadrons/bhad_hiStat_260218_200thr_genmother_iter2_m91w30_x2/`
  - `/home/submit/lavezzo/public_html/alphaS/260218_z_bb/hadrons/bhad_hiStat_260218_200thr_genmother_iter2_m91w30_x2_norm/`

## Slide refresh (2026-02-18): latest x2 swap plot
- Updated backup x2 figure in slides to latest replot output:
  - `/home/submit/lavezzo/public_html/alphaS/260218_z_bb/hadrons/bhad_hiStat_260218_200thr_genmother_iter2_m91w30_x2/inclusive_ptVgen_x2.png`.
- Recompiled and synced:
  - local: `agents/studies/z_bmass_uncertainty/slides/b_quark_mass.pdf`
  - shared: `/home/submit/lavezzo/public_html/alphaS/260216_study_slides/b_quark_mass.pdf`.

## Plot refresh (2026-02-18): non-x2 full replot and slide sync
- Regenerated full non-x2 plot set from latest hist files:
  - `/home/submit/lavezzo/public_html/alphaS/260218_z_bb/hadrons/bhad_hiStat_260218_200thr_genmother_iter2_m91w30_refresh/`
  - `/home/submit/lavezzo/public_html/alphaS/260218_z_bb/hadrons/bhad_hiStat_260218_200thr_genmother_iter2_m91w30_refresh_norm/`
- Updated slides to use refreshed non-x2 plots where available, and rebuilt `b_quark_mass.pdf`.
- Shared slide PDF updated at:
  - `/home/submit/lavezzo/public_html/alphaS/260216_study_slides/b_quark_mass.pdf`.

## Slide export refresh (2026-02-18)
- Updated slide date to `February 18, 2026`.
- Recompiled `b_quark_mass.pdf` and published a new dated output at:
  - `/home/submit/lavezzo/public_html/alphaS/260218_study_slides/b_quark_mass.pdf`.

## Requested check (2026-02-22): read arXiv:2510.18815 and extract "swapping" prescription
- Request:
  - Read the full paper and identify how the DY+bb vs DY+jet combination ("swapping") is defined.
- Status:
  - `answered`.
- Key result from arXiv:2510.18815:
  - The paper does not implement an event-by-event 5FS<->4FS swap in the style of our current study scripts.
  - Instead, in Sec. 6.2 it defines a **filtering/vetoed sum**:
    - build a DY+bb sample and a DY+jet sample;
    - remove from DY+jet the phase-space region already covered by DY+bb via a filter `phi(BB)=0`;
    - add the filtered pieces:
      - `d sigma_tot = d sigma_dy+bb + d sigma_dy+j |_{phi(BB)=0}`.
  - For the NNLOPS-matched setup they apply the same logic by removing inclusive-sample events with at least one bottom quark (`N_B >= 1`) before adding the dedicated `bb` component.
- Interpretation for this study:
  - Their "swap" is operationally a **region replacement by veto+addback** (exclusive partition), not event-level replacement.
  - The paper explicitly points to Ref. `[163]` for the Z+b-mass uncertainty construction details; arXiv:2510.18815 itself gives the combination framework and validation rather than a full nuisance recipe.

## Requested check (2026-02-22): read INSPIRE-hosted reference file and verify b-veto condition
- Request:
  - Read `https://inspirehep.net/files/04f61faf812ad2d2043add38f80a3a08` and confirm whether the overlap removal is based on events with one b quark.
- Status:
  - `answered`.
- Extracted prescription (Sec. 6.2, lines around Eq. 6.4 / Eq. 6.5 in the file):
  - The DY+jet (Powheg) component is split into:
    - events with **at least one** final-state bottom quark (`N_B >= 1`),
    - events with no final-state bottom quark (`N_B = 0`).
  - The improved combination keeps only the `N_B = 0` Powheg part and adds the dedicated DY+bb (`bbH`) contribution:
    - `sigma_improved = sigma_Powheg(N_B=0) + sigma_bbH`.
- Interpretation for this study:
  - This explicitly supports your reading: the overlap removal is not "exactly one b", but an inclusive veto on any bottom content (`>=1 b`) in the inclusive component.

## Requested check (2026-02-22): re-check Section 4.2 of arXiv:1803.04336
- Request:
  - Revisit Section 4.2 to verify whether the replacement excludes events with one bottom quark.
- Status:
  - `answered`.
- Extracted from local full-text notes (`/tmp/bmass_paper/1803.04336.txt`, produced in the 2026-02-18 paper pass):
  - The merged prediction uses orthogonal classes:
    - inclusive 5FS with B-hadron veto (`5FS-Bveto`);
    - plus 4FS heavy-flavor contribution.
  - Shape correction is then expressed as normalized ratio (paper Eq. 4.2):
    - `R(pT) = norm[dσ_mass/dpT] / norm[dσ_5FS/dpT]`.
- Interpretation for this study:
  - Section 4.2 is consistent with an inclusive veto/addback logic (`>=1 b` excluded from the inclusive component), not an "exactly one b" selection.

## Requested check (2026-02-22): identify cross-section conventions used in arXiv:1803.04336
- Request:
  - Verify which cross-section inputs/conventions are used in the paper, to debug normalization mismatches.
- Status:
  - `answered`.
- Extracted setup (Sec. 2 + Sec. 4.2 from local text extract):
  - Center-of-mass energy: `13 TeV`.
  - PDFs: `NNPDF 3.0 NLO`, `alpha_s(mZ)=0.118`.
  - `m_b = 4.7 GeV`, applied in `4FS` only.
  - Central ren/fact scale for NC DY and `llbb`: `mu = (1/4) * sqrt(M_ll^2 + pT_ll^2)`.
  - Fiducial cuts used for NC channels:
    - `pT(l) > 20 GeV`, `|eta(l)| < 2.5`, `|M_ll - mZ| < 15 GeV`;
    - generation cut `M_ll > 30 GeV`.
- Cross-section normalization detail relevant for swap/addback:
  - The merged prediction is taken as:
    - `d sigma_mass = d sigma_(5FS-Bveto) + d sigma_(4FS)` (paper Eq. 4.1),
    - i.e. no additional empirical scale factor in the additive term.
  - Their main correction observable is the **fiducial-normalized shape ratio**:
    - `R(pT) = [ (1/sigma_fid_mass) d sigma_mass/dpT ] / [ (1/sigma_fid_5FS) d sigma_5FS/dpT ]` (paper Eq. 4.2).
- Explicit 5FS flavor decomposition number quoted in the paper (Table 1):
  - total NC-DY fiducial cross section: `743.61 +- 0.22 pb`;
  - bottom-initiated contribution: `28.31 +- 0.05 pb` (`3.8%`).
- Interpretation for this study:
  - A direct absolute-yield comparison can disagree even with correct addback algebra if we do not mirror the paper's fiducial-normalized `R(pT)` workflow and input setup.

## Requested implementation (2026-02-22): explicit `sigma-difference` normalization mode
- Request:
  - Implement a mode where the 5FS B-veto component is normalized explicitly as `sigma(5FS)-sigma(4FS)` while the addback keeps `sigma(4FS)`.
- Status:
  - `answered`.
- Implemented changes:
  - `studies/z_bb/plot_narf.py`:
    - new option `--norm-mode {default,sigma-difference}`;
    - in `sigma-difference` mode:
      - rescale `5FS(bottom_sel=0)` shape to target `sigma_5FS_total - sigma_4FS_total`,
      - rescale `4FS(bottom_sel=1)` shape to target `sigma_4FS_total`,
      - build corrected distribution from these explicit targets;
    - print target-integral diagnostics per observable.
    - safety checks:
      - reject `--norm-mode sigma-difference` with `--normalize`;
      - reject `--norm-mode sigma-difference` with `--massive-scale != 1`.
  - `studies/z_bb/make_zbb_corr.py`:
    - new option `--norm-mode {default,sigma-difference}`;
    - same target-integral logic applied when building corrected templates.
- Validation:
  - syntax check passed:
    - `python -m py_compile studies/z_bb/plot_narf.py studies/z_bb/make_zbb_corr.py`.

## Latest iteration (2026-02-22, tag `bhad_hiStat_260218_200thr_genmother_iter2_m91w30_sigmaDiff`)
- Goal:
  - Run the new `sigma-difference` normalization mode end-to-end on latest high-stat inputs.
- Inputs:
  - `/scratch/submit/cms/alphaS/260218_gen_massiveBottom/w_z_gen_dists_maxFiles_m1_hadronsSel_massive_bhad_hiStat_260218_200thr_genmother_iter2_m91w30.hdf5`
  - `/scratch/submit/cms/alphaS/260218_gen_massiveBottom/w_z_gen_dists_maxFiles_1000_nnpdf31_hadronsSel_massless_bhad_hiStat_260218_200thr_genmother_iter2_m91w30.hdf5`
- Output plots:
  - `/home/submit/lavezzo/public_html/alphaS/260222_z_bb/hadrons/bhad_hiStat_260218_200thr_genmother_iter2_m91w30_sigmaDiff/`
- Printed normalization diagnostics:
  - `[sigma-difference:ptVgen] target_massive=1.499283e+08, target_5FS_bveto=8.178362e+09, total_5FS=8.328290e+09`
  - `[sigma-difference:absYVgen] target_massive=1.499283e+08, target_5FS_bveto=8.178364e+09, total_5FS=8.328292e+09`
- Notable selected-region fractions (same inputs):
  - `% selected for swap` (4FS): `1.0`
  - `% selected for swap` (5FS): `0.06709904773170555`
- Follow-up plotting update:
  - Added and produced B-hadron component-comparison plots with sigma-difference targets:
    - `5FS component` normalized to `sigma_5FS - sigma_4FS`,
    - `4FS component` normalized to `sigma_4FS`.
  - Generated PNGs:
    - `samples_comparison_nBhad_sigma_difference_components.png`
    - `samples_comparison_leadB_pt_sigma_difference_components.png`
    - `samples_comparison_subB_pt_sigma_difference_components.png`
    - `samples_comparison_m_bb_had_sigma_difference_components.png`
    - `samples_comparison_dR_bb_had_sigma_difference_components.png`

## Requested implementation (2026-02-23): Appendix-C-like FastJet fiducial selection
- Request:
  - Reproduce Appendix-C selection logic from arXiv:2404.08598 using FastJet reclustering (not NanoAOD GenJet inputs), while reusing existing dressed leptons.
- Status:
  - `answered`.
- Implemented interface:
  - histmaker option:
    - `--appendixCFastjet` in `/home/submit/lavezzo/alphaS/gh/WRemnants/scripts/histmakers/w_z_gen_dists.py`.
  - study launcher pass-through:
    - `--appendixc-fastjet` in `studies/z_bb/make_hists.py`.
- Behavior in this mode (for Z with `--addBottomAxis`):
  - anti-kt `R=0.4` FastJet clustering from visible stable GenPart;
  - b-jet tagging by ghost-associated b hadrons;
  - dressed-lepton SFOS Z selection (`pT>25`, `|eta|<2.4`, `71<mll<111`, leading `pT>35`);
  - lepton-bjet overlap removal (`DeltaR>0.4`);
  - `bottom_sel` defined as cleaned FastJet b-jet multiplicity `>=1`.
- Preselection diagnostics now produced:
  - `presel_cms_appc_pass_z`, `presel_cms_appc_n_lep`, `presel_cms_appc_n_bjets_clean`.
- Smoke output (1-file check):
  - `/tmp/appc_fj_smoke/w_z_gen_dists_maxFiles_1_appc_fj_smoke.hdf5`.

## Requested check (2026-03-02): switch overlap selection to `nLHE > 0`
- Request:
  - resume the b-mass study with overlap selection defined by LHE multiplicity (`nLHE > 0`);
  - rerun full pipeline and inspect corrected sample.
- Status:
  - `answered`.
- Implemented interpretation:
  - in `/home/submit/lavezzo/alphaS/gh/WRemnants/scripts/histmakers/w_z_gen_dists.py`:
    - `bottom_sel` changed to:
      - `bottom_sel = (n_lhe_bbbar > 0)`.
- Completed run in this session (via approved wrapper launcher):
  - hist outputs:
    - `/scratch/submit/cms/alphaS/260302_gen_massiveBottom_nlhe/w_z_gen_dists_maxFiles_m1_hadronsSel_massive_nlheSel_260302.hdf5`
    - `/scratch/submit/cms/alphaS/260302_gen_massiveBottom_nlhe/w_z_gen_dists_maxFiles_1000_nnpdf31_hadronsSel_massless_nlheSel_260302.hdf5`
  - corrected-sample plots:
    - unnormalized:
      - `/home/submit/lavezzo/public_html/alphaS/260302_z_bb/hadrons/nlheSel_260302/`
    - normalized:
      - `/home/submit/lavezzo/public_html/alphaS/260302_z_bb/hadrons/nlheSel_260302_norm/`
- Key resulting selection diagnostics:
  - selected-yield ratio (`massless/massive`, `bottom_sel==1`): `0.9532019550472046`
  - selected fraction in massive: `1.0`
  - selected fraction in massless: `0.038519512269219965`
- Corrected/nominal behavior summary:
  - unnormalized corrected:
    - `ptVgen` ratio `min/max/wmean = 0.997395 / 1.024550 / 1.001891`
    - `absYVgen` ratio `min/max/wmean = 1.001094 / 1.002323 / 1.001891`
  - normalized corrected:
    - `ptVgen` ratio `min/max/wmean = 0.996286 / 1.020497 / 1.000000`
    - `absYVgen` ratio `min/max/wmean = 0.999649 / 1.000764 / 1.000000`
