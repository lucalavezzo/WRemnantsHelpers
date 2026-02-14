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

## Current understanding
- The target is a robust nuisance construction that captures the difference in heavy-flavor treatment (massless-b 5FS vs massive-b 4FS) without double counting existing uncertainties.
- Theoretical references to anchor the prescription:
  - arXiv:1904.09382 (4FS/5FS matching logic for heavy flavor in Z+jets context).
  - arXiv:2404.08598 (NNLO+PS Z+bbar in 4FS with explicit b-mass effects).
- Current `bottom_sel` implementation in `w_z_gen_dists.py`:
  - Identify B hadrons using PDG-digit logic in `wremnants/include/theoryTools.hpp` (`isBHadron` + `finalStateBHadronIdx`).
  - Keep particles with `GenPart_status` in `{1,2}`.
  - Build leading/subleading B-hadron pT from those particles above `5 GeV`.
  - Define `bottom_sel = (subB_pt5 > 10)` (at least two B hadrons above `5 GeV`, with subleading B hadron above `10 GeV`).

## Decisions taken so far
- Create a dedicated study folder under `agents/studies/z_bmass_uncertainty/`.
- Track incremental progress in this README and in `runlog.md` during the session.
- Next technical step is to define a concrete template-based nuisance prescription (central/up/down) and normalization strategy.
- Revised approach (per discussion): do not introduce a separate histmaker path; instead extend the canonical `w_z_gen_dists.py` outputs and inspect distributions before changing any swap selection.
- Use B-hadron-based swap-region definition:
  - `bottom_sel = (subB_pt5 > 10)`.
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

### Container run command
In the normal Singularity runtime, execute:
`bash agents/run_zbb_bhad_diag.sh bhad_diag_<new_tag>`

This runs both tagged histmakers and then `studies/z_bb/plot_narf.py` on the produced files.
