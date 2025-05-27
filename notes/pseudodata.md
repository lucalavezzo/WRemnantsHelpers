# Pseudodata

The idea is to use the two different sets of toys in the fit: the first on the MC (from `nominal` histogram) to simulate the MC statistical uncertainties and, with the frequentist method, the systematic uncertainties, and the second again on the MC (from `nominal_asimov` histogram) which we use as an Asimov dataset, i.e. pretending that it is data, from which we generate toys.
The difference between the two is that for the MC uncertainties we use bootstrapping, i.e. for each event generate a Poisson-distributed weight, while for data uncertainties we generate a Poisson-distributed weight on the central value of the bin of the final histogram.
The first method is necessary for MC because we need to take into account the MC weights.

Added to the histmaker nominal histogram an axis with toys, as well as another histogram, `nominal_asimov`, which is the same as `nominal`, but without any toys.

```
python $WREM_BASE/scripts/histmakers/mz_dilepton.py --dataPath $NANO_DIR -o $MY_OUT_DIR/250510_toys -j -1 --maxFiles 100 --axes ptll yll --forceDefaultName --csVarsHist --unfolding --poiAsNoi --unfoldingAxes ptVGen absYVGen helicitySig --unfoldingInclusive --nToysMC 5 --randomSeedForToys 12345
```

In the setupCombine step, we select the MC toy via the `--select` option.

```
python $WREM_BASE/scripts/combine/setupCombine.py -i $MY_OUT_DIR/250510_toys/mz_dilepton.hdf5 -o $MY_OUT_DIR/250510_toys/ --fitvar 'ptll-yll-cosThetaStarll_quantile-phiStarll_quantile' --fitAlphaS --baseName nominal --pseudoData asimov --select 'toys 0.0j 1.0j' --postfix toys_0_1
```

In the combine fitting step, we generate the toys on the data, and use the frequentist method to randomize the systematic uncertainties on the MC.

```
combinetf2_fit.py $MY_OUT_DIR/250510_toys/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_toys_0_1/ZMassDilepton.hdf5 -o $MY_OUT_DIR/250510_toys/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_toys_0_1/ -t 1 --toysSystRandomize frequentist --toysDataRandomize poisson --toysDataMode observed
```

# Pseudodata for the theory fit

For the theory fit, we 