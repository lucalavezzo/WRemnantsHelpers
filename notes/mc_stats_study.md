# MC Stats Study

We suspect the fit is spuriously constraining uncertainties.
We can verify this by running the fit with half and full MC stats, and suppressing the MC statistical uncertainties (`--noBinByBinStat`).

We ran the histmaker with half the MC files with,
```
python $WREM_BASE/scripts/histmakers/mz_dilepton.py --dataPath $NANO_DIR -o $MY_OUT_DIR/250505_oneMCfileEvery2 -j -1 --maxFiles -1 --axes ptll yll --forceDefaultName --csVarsHist --oneMCfileEveryN 2
```

The fitting was done as normal, but with the `--noBinByBinStat` option added to the `fit` command.
The `fitter.sh` script was used, and ran with `mc_stats_study.sh` to iterate over full/half MC stats, with/without MC statistical uncertainties, different rebinning options.