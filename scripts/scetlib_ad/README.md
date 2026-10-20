# scetlib_ad helper tools

Moved here from the WRemnants `ad-validation-tools` split PR (2026-10-20, Luca's decision: the
cache-checking tools `compare_to_scetlib_run.py` and `validate_reco.py` stay in WRemnants under
`scripts/rabbit/scetlib_ad/`; these two are analysis-side tools).

- `validate_variations.py`: the model's response to each theory variation vs the Corr templates it
  replaces (cache + runcard only, no datacard).
- `make_debug_card.py`: a small gen-level rabbit card whose template is sigma_gen at the cache anchor,
  for closure / injection tests.

Both import `wremnants.postprocessing.scetlib_ad` (needs D, WMass/WRemnants #739, and for
`validate_variations.py` the `validation_plots` helpers from the `ad-validation-tools` PR) and the
external SCETlib (`source <scetlib-cms>/setup.sh`).
