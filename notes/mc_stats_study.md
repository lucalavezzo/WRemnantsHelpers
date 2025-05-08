# MC Stats Study

We suspect the fit is spuriously constraining uncertainties.
We can verify this by running the fit with half and full MC stats, and suppressing the MC statistical uncertainties (`--noBinByBinStat`).

We ran the histmaker with half the MC files with, (unfolding enabled in case we want to check that too)
```
python $WREM_BASE/scripts/histmakers/mz_dilepton.py --dataPath $NANO_DIR -o $MY_OUT_DIR/250505_oneMCfileEvery2 -j -1 --maxFiles -1 --axes ptll yll --forceDefaultName --csVarsHist --oneMCfileEveryN 2 --unfolding --poiAsNoi --unfoldingAxes ptVGen absYVGen helicitySig --unfoldingInclusive
```

The fitting was done as normal, but with the `--noBinByBinStat` option added to the `fit` command.
The `fitter.sh` script was used, and ran with `mc_stats_study.sh` to iterate over full/half MC stats, with/without MC statistical uncertainties, different rebinning options.

## Checking the unfolding

We want to check if this over-constraining to the MC stats is also happening in the unfolding.

Run the unfolding,

```
python $WREM_BASE/scripts/combine/setupCombine.py -i $MY_OUT_DIR/250505_oneMCfileEvery2/mz_dilepton.hdf5 -o $MY_OUT_DIR/250505_oneMCfileEvery2/250507_unfolding/ --analysisMode unfolding --poiAsNoi --fitvar 'ptll-yll-cosThetaStarll_quantile-phiStarll_quantile' --genAxes 'ptVGen-absYVGen-helicitySig' --scaleNormXsecHistYields '0.05' --allowNegativeExpectation --realData --systematicType normal
```

Run the fit,

```
combinetf2_fit.py $MY_OUT_DIR/250505_oneMCfileEvery2/250507_unfolding//ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile//ZMassDilepton.hdf5 -o $MY_OUT_DIR/250505_oneMCfileEvery2/250507_unfolding//ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/ --binByBinStatType normal -t -1 --doImpacts --globalImpacts --saveHists --computeHistErrors --computeHistImpacts --computeHistCov -m Select ch0_masked 'helicitySig:slice(0,1)' --postfix asimov 
```

Setup the card, we are actually using the full MC stats to fit here, only the unfolding was done with half the MC stats,

```
python $WREM_BASE/scripts/combine/setupCombine.py -i /scratch/submit/cms/alphaS/histmaker_output_250425/mz_dilepton_scetlib_dyturboCorr_maxFiles_m1.hdf5 -o $MY_OUT_DIR/250507_unfolding//ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/ --fitresult $MY_OUT_DIR/250505_oneMCfileEvery2/250507_unfolding//ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults_asimov.hdf5 'Select helicitySig:slice(0,1)' ch0_masked --fitvar ptVGen-absYVGen-helicitySig --axlim -1000 1000 -1000 1000 -1 0 --fitAlphaS --postfix theoryfit --baseName prefsr
```

Finally run the fit,

```
combinetf2_fit.py $MY_OUT_DIR/250430_mz_unfolding_full/ZMassDilepton_helicitySig_ptVGen_absYVGen_theoryfit//ZMassDilepton.hdf5 -o $MY_OUT_DIR/250430_mz_unfolding_full/ZMassDilepton_helicitySig_ptVGen_absYVGen_theoryfit/ --doImpacts --globalImpacts --saveHists --computeHistErrors --computeVariations --chisqFit --externalCovariance -t -1 -m Basemodel -m Project ch0 ptVGen -m Project ch0 absYVGen
```