# Z b-mass uncertainty study

## Study question
Define and implement an additional uncertainty on Z data to cover b-quark mass effects, using:
- nominal MiNNLO Z sample in 5 flavor scheme (5FS) with massless b quarks;
- alternate MiNNLO Z+bbar sample in 4 flavor scheme (4FS) with massive b quarks.

## Guiding questions
- What overlap region between 5FS and 4FS best represents the same heavy-flavor physics for a swap-based correction?
- Should the resulting nuisance be shape-only, or shape+rate?
- Which event definition (for example based on B hadrons) gives stable and interpretable behavior across `ptVgen` and `absYVgen`?

## Current understanding
- The target is a robust nuisance construction that captures the difference in heavy-flavor treatment (massless-b 5FS vs massive-b 4FS) without double counting existing uncertainties.
- Theoretical references to anchor the prescription:
  - arXiv:1904.09382 (4FS/5FS matching logic for heavy flavor in Z+jets context).
  - arXiv:2404.08598 (NNLO+PS Z+bbar in 4FS with explicit b-mass effects).
- Current `bottom_sel` implementation in `w_z_gen_dists.py`:
  - Identify B hadrons using PDG-digit logic in `wremnants/include/theoryTools.hpp` (`isBHadron` + `finalStateBHadronIdx`).
  - Keep particles with `GenPart_status` in `{1,2}`.
  - Build leading/subleading B-hadron pT from those particles.
  - Define `bottom_sel = (subB_pt > 5)` (effectively requires at least two B hadrons above threshold).

## Decisions taken so far
- Create a dedicated study folder under `agents/studies/z_bmass_uncertainty/`.
- Track incremental progress in this README and in `runlog.md` during the session.
- Next technical step is to define a concrete template-based nuisance prescription (central/up/down) and normalization strategy.
- Revised approach (per discussion): do not introduce a separate histmaker path; instead extend the canonical `w_z_gen_dists.py` outputs and inspect distributions before changing any swap selection.
- Keep physics selection unchanged while diagnostics are being established:
  - `bottom_sel` remains `(subB_pt > 5)`.
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

## Open points
- Exact observable basis for the nuisance (inclusive vs category-based vs differential in analysis bins).
- Whether to constrain normalization impact separately from shape impact.
- Mapping of the 4FS/5FS difference onto fit nuisance priors and correlations across channels.

## Knowledge and question tracker
- Learned:
  - With current selection (`subB_pt > 5`), selected fractions differ strongly (`~0.81` in 4FS vs `~0.04` in 5FS), but cross-section-scaled selected yield is still larger in 5FS by about `4x`.
  - This indicates selection-fraction mismatch and total-normalization hierarchy both matter for swap construction.
- Emerging questions:
  - Are B-hadron-only criteria sufficient to isolate a truly swappable overlap? Status: `open`.
  - Would adding tighter topology constraints (for example on subleading B-hadron kinematics) improve normalized shape agreement? Status: `partial` (new hadron-level `m_bb`/`ΔR_bb` diagnostics added in current run; interpretation pending).
  - Is the residual mismatch mainly from physics-content differences between inclusive 5FS and dedicated 4FS Zbb samples? Status: `partial`.

## Next steps
- Convert the observed large normalization mismatch into an explicit nuisance design choice:
  - either shape-only (normalized replacement) or shape+rate (with constrained prior).
- Run one higher-stat tagged iteration (same workflow, fresh tag) to reduce statistical noise in tails.
- Compare additional category boundaries (for example `nBhad_pt5>=1` vs `>=2`) before changing `bottom_sel`.

### Container run command
In the normal Singularity runtime, execute:
`bash agents/run_zbb_bhad_diag.sh bhad_diag_<new_tag>`

This runs both tagged histmakers and then `studies/z_bb/plot_narf.py` on the produced files.
