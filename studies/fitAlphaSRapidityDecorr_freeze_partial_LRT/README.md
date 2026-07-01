# fitAlphaSRapidityDecorr_freeze_partial_LRT

## Study question
The per-rapidity-bin α_S decorrelation fit (260429) shows the per-bin α_S
values inconsistent with a common α_S value at p ≈ 0% via the Wilks LRT
χ² = 2·(NLL_inclusive − NLL_decorr) ~ χ²(N_y − 1). Decorrelated α_S is
therefore acting as a relief valve for *something* the global-α_S fit cannot
absorb. **Which nuisance group(s) are responsible?**

The diagnostic is a **partial-LRT**: re-run both the inclusive and decorrelated
fits with a candidate group G frozen at its prefit value (0). If the LRT
shrinks substantially, that group was supplying the y-dependent freedom that
the decorrelated α_S fit was using. If the LRT is unchanged, the group is
innocent.

A cheaper proxy that we run first is to refit only the **decorrelated** model
with each group G frozen, and look at how the spread of the per-bin α_S values
evolves. A group that absorbs y-dependent tension will let the per-bin α_S
collapse toward a common value when frozen elsewhere; a group that doesn't
will leave the spread roughly intact.

## Guiding questions
1. Does freezing PDF + m_b nuisances collapse the per-bin α_S spread?
   *(Top of the spread×pull table is dominated by `pdfMSHT20mbrange*`,
   `mb_up`, and `pdf*CT18Z*`.)*
2. Does freezing scetlibNP / chargeVgenNP do the same? Multiple parameters in
   that family are pulled past 1σ.
3. Are the >1σ pulls on `CMS_prefire_stat_*` and `pixel_multiplicity_syst_var47`
   contributing meaningfully, or are they cosmetic?
4. After the dominant absorber group is identified, does the LRT p-value
   become reasonable, or is there still residual y-dependent tension?

## Inputs
- Reference decorrelated baseline (provided by user, no-freeze):
  `/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260429_fitAlphaSRapidityDecorr/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_fitAlphaSRapidityDecorr_renamed_LambdaScale5p0/fitresults_unblindedAsGroup.hdf5`
- Input tensor for refits:
  `.../ZMassDilepton.hdf5` (same directory).
- Reference fit command recovered from `meta_info.command` of the baseline
  fit; freeze-refits use the same command + `--freezeParameters <regex...>`
  + a unique `--postfix freeze_<group>` so every output goes to a fresh file.

## Plan
1. Define groups in `groups.yaml` — one entry per category (pdf_mb, scetlibNP,
   prefire, fsr, qcdscale, …) listing the regexes to freeze.
2. `scripts/run_freeze_groups.py` loops over groups and launches each refit in
   the background via singularity wrapper (the verified pattern from
   AGENTS.md). Logs land in `logs/`.
3. `scripts/analyze_freeze_results.py` reads the fitresults files, prints a
   per-group table of:
     - α_S spread (max−min) and rms
     - LRT χ² against baseline inclusive fit (if path provided)
     - top-N differential nuisances remaining (uses
       `WRemnantsHelpers/studies/fitAlphaSRapidityDecorr/diff_alphaS_impacts.py`).

## Status
- 2026-04-30: Folder created; scripts under construction. Baseline LRT is
  p ≈ 0% (per user's `plot_alphaS_rapidity_decorr.py`).

## Next steps
- Define `groups.yaml`, launch refits, populate the per-group table.
- If a group collapses the spread, also run the inclusive partner refit (same
  freeze) so the partial-LRT χ² is computable.
