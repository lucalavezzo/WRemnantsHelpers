# Gen-Level (Direct-Theory sigmaUL) Fit With The SCETlib NP Param Model

## Scope
Fitting the SCETlib NP param model at GEN level: unfolded sigmaUL on
(ptVGen, absYVGen) instead of reco templates. Complements
`nominal_workflow.md` (the reco chain) and `frozen_nominal_spec.md`.

## Canonical Facts
- The chain is: `workflows/histmaker_unfolding.sh` -> `workflows/unfolder.sh`
  (setupRabbit `--analysisMode unfolding` + rabbit fit, writes
  `fitresults*_unfolded.hdf5`) -> `${WREM_BASE}/scripts/rabbit/feedRabbitSigmaUL.py`
  (the sigmaUL datacard, channel `chSigmaUL`, process `Zmumu`, data = the
  unfolded sigmaUL + its full covariance) -> the fit.
- `workflows/theoryFitDirect.sh` runs that last step WITHOUT the param model
  (discrete lambda templates float instead). `workflows/fitterSCETlibNP.py
  --genLevel` runs it WITH the param model, using the same step/inheritance
  machinery as the reco path.
- `--genLevel` adds the model spec token `gen_level=1`: no response matrix, no
  gen->reco fold, `compute()` returns the per-GEN-bin ratio
  sigma_gen(lambda)/sigma_gen(lambda_central). No `scetlib_np` auxiliary
  (R / N_gen) is needed; the gen binning is read from the fit channel's axes.
- The param model reads those axes **positionally**: `gen_axes[0]` is the qT
  edges, `gen_axes[1]` the |Y| edges (`SigmaGenModel`). An unfolded card gives
  (ptVGen, absYVGen); a `--pseudodataGenerator` card gives (qT, absY).
- The unfolded data carries a covariance (`hdata_cov_inv`), so the likelihood is
  the covariance chi2: every step needs rabbit's `--covarianceFit`.
- Because the likelihood is then Gaussian, the linear chi2 rabbit writes with
  `--saveHists` IS the exact goodness of fit; the saturated LRT adds nothing
  (hence `--genLevel` drops `saturated` from the default steps).

## Rules I Should Follow
- Build the card WITHOUT the discrete lambda templates the model replaces:
  `feedRabbitSigmaUL.py ... --excludeNuisances '^.*scetlibNP.*$'` (the model
  refuses to run otherwise; `'scetlib*'` also works but only by accident — as a
  regex it means "scetli" + zero-or-more "b").
- Check `lambda_central` is the runcard of the card's OWN `--predGenerator`
  before believing any postfit lambda (see the first pitfall).
- Read the fit with `scripts/rabbit/scetlib_np/fitresult_lambdas.py` /
  `param_model_diagnostics.py` exactly as on the reco side.

## Standard Commands
```bash
# card (from an unfolded fitresult), param-model ready
python $WREM_BASE/scripts/rabbit/feedRabbitSigmaUL.py \
    -i <.../fitresults_asimov_unfolded.hdf5> --infile-result asimov \
    --predGenerator scetlib_dyturbo_LatticeNP_CT18Z_N3p0LL_N2LO --pdfs ct18z \
    --systematicType log_normal --fitresultMapping 'Select helicitySig:0' \
    --channelSigmaUL ch0_masked --excludeNuisances '^.*scetlibNP.*$' -o <dir>

# fit + covariance pass (channel/axes/--covarianceFit come from --genLevel)
python workflows/fitterSCETlibNP.py <card.hdf5> --genLevel -d gen_fit
```

## Common Pitfalls
- **The NP anchor of a sigmaUL card is NOT the propagated histmaker one
  (verified 2026-07-29).** The model auto-detects `lambda_central` by walking the
  card metadata, and on a sigmaUL card that chain (card -> unfolding fitresult ->
  unfolding datacard -> histmaker `meta_info`) ends at the **reco histmaker's**
  theory correction — while the sigmaUL template and every theory variation in
  the tensor come from `feedRabbitSigmaUL --predGenerator`. Those differ whenever
  the unfolding and the prediction use different SCETlib NP runcards; e.g. the
  260729 unfolding used `..._LatticeNPLambda4Bugfix_FranksValsVars_...`
  (lambda2 0.4, lambda4 0.4, lambda2_nu 0.15, lambda_inf_nu 2.0) while the card
  predicted with `..._LatticeNP_...` (lambda2 0.25, lambda4 0.06,
  lambda2_nu 0.087, lambda4_nu 0.0074, lambda_inf_nu 1.6853). Anchored at the
  wrong central the ratio is still 1 at the start, so nothing looks broken — but
  the fitted lambdas are relative to a prediction the card does not contain and
  the shape response is evaluated at the wrong point. `feedRabbitSigmaUL.py` now
  writes the prediction's own runcard at the TOP level of the card meta (which
  wins `lambda_central._iter_meta_levels`), and `fitterSCETlibNP.py --genLevel`
  refuses a card where the anchor tag != `predGenerator`. Cards written before
  2026-07-29 must be remade.
- **A swapped axis order fails silently, not loudly.** The model only checks that
  the channel has 2 axes, so a (|Y|, qT) card would fit a transposed spectrum.
  `fitterSCETlibNP.py --genLevel` name-checks the order before launching.
- **The bT slab scales with the number of GEN bins.** An unfolded card
  (20 x 10 = 200 bins) is cheap; a `--pseudodataGenerator` card on the FINE corr
  binning (70 x 17 = 1190 bins) allocates ~33 GB per pass and takes ~20 s per
  minimizer iteration on CPU.
- **The `--pseudodataGenerator` path references the fine corr binning**, and the
  mb_fo / PDF blocks carry a coarser one -> `ValueError: Cannot rebin histogram
  due to incompatible edges for axis 'qT'`. Pre-existing limitation of that path
  (the cross-term closure study switched those blocks off); use
  `--keepNuisances` to build a minimal card.
- `-f/--extraFit` needs `-f=--unblind` (argparse eats a bare `--unblind` as an
  option).

## Last Updated
- 2026-07-29

## Source
- `workflows/fitterSCETlibNP.py --genLevel` (added 2026-07-29)
- `wremnants/postprocessing/scetlib_np/param_model.py` (`gen_level`)
- `studies/xterm-closure/CLOSURE_WORKFLOW.md` (the first gen-level fits, by hand)
