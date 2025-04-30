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

# Comparison to gen-level distributions

Now we want to compare to the fit done with the gen-level distributions.

First, generate the gen-level histograms,

```
python $WREM_BASE/scripts/histmakers/w_z_gen_dists.py --dataPath /scratch/submit/cms/wmass/NanoAOD/ -o $MY_OUT_DIR/250430_gen/ -j -1 --maxFiles -1 --filterProcs ZmumuPostVFP --useUnfoldingBinning --theoryCorrections --helicity
```

Then setup the fit on these,

```
python $WREM_BASE/scripts/combine/setupCombine.py -i $MY_OUT_DIR/250430_gen/w_z_gen_dists_scetlib_dyturboCorr_maxFiles_m1.hdf5 -o $MY_OUT_DIR/250430_gen/  --fitAlphaS --baseName nominal_gen --fitvar ptVgen-absYVgen --filterProcGroups Zmumu
```

Finally run the fit,

```
combinetf2_fit.py $MY_OUT_DIR/250430_gen/ZGen_ptVgen_absYVgen/ZGen.hdf5 -t -1 --computeVariations --computeHistErrors --doImpacts -o $MY_OUT_DIR/250430_gen/ --globalImpacts --saveHists --saveHistsPerProcess --verbose 4
```

