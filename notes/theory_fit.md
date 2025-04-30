# Theory fit

Run the theory fit first to create the signal model, here we select only the unpolarized term in the signal model (via `'Select ch0_masked helicitySig:0'`). We keep the helicityAxis for compatibility with the data histogram, but it only has one bin.

```
combinetf2_fit.py /scratch/submit/cms/dwalter/combineResults/250426_mz_unfolding_full/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/ZMassDilepton.hdf5 -o /home/submit/lavezzo/cms/alphaS/250430_mz_unfolding_full/ --binByBinStatType normal -t -1 --doImpacts --globalImpacts --saveHists --computeHistErrors --computeHistImpacts --computeHistCov -m Select ch0_masked 'helicitySig:slice(0,1)' --postfix asimov 
```

Set up the card:

The first .hdf5 file (`-i`) is only used for the expected unfolded histograms, selected via `--baseName prefsr`.
Data used is the unfolded one from the `--fitresult`.
We select the channel we defined above via `'Select ch0_masked helicitySig:0'`, and we restrict the fit to only the first bin of the helicitySig histogram via `--fitvar helicitySig-ptVGen-absYVGen --axlim -1 0`.

```
python scripts/combine/setupCombine.py -i /scratch/submit/cms/alphaS/histmaker_output_250425/mz_dilepton_scetlib_dyturboCorr_maxFiles_m1.hdf5 -o /home/submit/lavezzo/cms/alphaS/250430_mz_unfolding_full/ --fitresult /home/submit/lavezzo/cms/alphaS/250430_mz_unfolding_full/fitresults_asimov.hdf5 'Select helicitySig:slice(0,1)' ch0_masked --fitvar helicitySig-ptVGen-absYVGen --axlim -1 0 --fitAlphaS --postfix theoryfit --baseName prefsr
```

And finally run the fit,

```
combinetf2_fit.py /home/submit/lavezzo/cms/alphaS/250430_mz_unfolding_full//ZMassDilepton_helicitySig_ptVGen_absYVGen_theoryfit//ZMassDilepton.hdf5 -o /home/submit/lavezzo/cms/alphaS/250430_mz_unfolding_full//ZMassDilepton_helicitySig_ptVGen_absYVGen_theoryfit/ --doImpacts --globalImpacts --saveHists --computeHistErrors --computeVariations --chisqFit --externalCovariance -t 0 -m Basemodel -m Project ch0 ptVGen -m Project ch0 absYVGen
```

`--chisqFit` necessary here since the bin by bin data is not uncorrelated, due to the unfolding procedure.