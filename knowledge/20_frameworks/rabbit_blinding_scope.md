# What rabbit's blinding hides, and what it does not

## Scope
Real-data (`-t 0`) rabbit fits, in particular `--poiAsNoi` unfoldings, where the physics
result is a histogram (the masked channel), not a parameter.

## Canonical Facts
- Rabbit (checked at 2a59246) blinds by an additive, deterministic offset on each POI and on
  each NOI: `θ_physical = θ_stored + offset`. The offset is N(0, 5) seeded by
  `sha256(name + "_data")` (`rabbit/blinding.py`). Constrained nuisances are not offset.
- The model and the likelihood see `θ_physical`. The saved `parms` are `θ_stored`, so
  **parameter values are blinded**. Covariance, uncertainties and impacts come out exactly
  unblinded (a translation has unit Jacobian).
- **Saved histograms are NOT blinded.** `save_hists` → `fitter.expected_events` evaluates the
  model at `θ_physical`, so every `hist_postfit_inclusive` is the true post-fit prediction.
  That includes the masked-channel unfolded cross sections and the derived
  `AngularCoefficients`.
  - Verified on the 261001 Z data unfolding: corr(post − prefit, offset) = +0.012, and adding
    the offset to `θ_stored` raises the correlation with post − prefit from 0.76 to 0.84
    (`studies/z-data-unfolding/261001-unfold-data-iter0/scripts/blinding_check.py`).
- Consequences:
  - A rabbit unfolding plotted from `hist_postfit_inclusive` shows unblinded unfolded data.
  - `feedRabbitSigmaUL.py` and histmaker `--fitresult` reweighting read those histograms, so
    they get the true spectrum. Downstream blinding has to come from the downstream fit's own
    POI blinding.

- **Iterated unfoldings leak through the prior.** After histmaker `--fitresult` reweighting,
  the MC prior *is* the previous unfolded data result. So, for the next card:
  - its Asimov "prediction" and "unfolded" plots draw the unblinded result;
  - its relative-uncertainty plots (σ / prefit) encode MC/unfolded.

  Found on the 261008 Z iteration, which needed a second quarantine.

## Rules I Should Follow
- **Current α_s-analysis policy (Luca, 2026-10-09):** the Z unfolding (unfolded σ_UL / A_i)
  may be shown unblinded; only the α_s value stays blinded. The rules below apply when a
  quantity IS meant to be blind.
- Treat any post-fit histogram of a real-data fit as unblinded. Never publish one to the web
  without an explicit unblinding decision. `workflows/unfoldingDiagnostics.sh -b` skips them
  unless `-U` is given.
- On a reweighted (iterated) card, treat the Asimov and every prior-normalised plot as unblinded.
- Do not argue from "the NOIs are blinded" to "the unfolded result is blinded".

## Last Updated
- 2026-10-09

## Source
- `rabbit/blinding.py`, `rabbit/fitter.py` (`get_theta`, `get_poi`), `bin/rabbit_fit.py`
  (`save_hists`).
- studies/z-data-unfolding (correction of 2026-10-08).
