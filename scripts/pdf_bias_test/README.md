# PDF Bias Test Scripts

This directory contains helper scripts used to perform PDF bias tests in the dilepton fit.
We test each PDF set as a central PDF set, and fit it using as pseudodata the nominal prediction from another PDF set.
The resulting shift in the fitted $\alpha_s$ value is recorded is the figure of merit we are studying.

- `run_histmakers.py` runs the `histmaker.sh` workflow over a grid of central and comparison PDF sets, producing the histogram inputs for later fits. We need to run the histmaker once per central PDF set, with all the other PDF sets we want to use as pseudodata as alternate PDF sets.
- `run_fitter.py` consumes the histmaker outputs and fits each configuration, selecting as pseudodata the alternate PDF sets. One script is called per histogram output (central PDF set): in each, the fit is repeated for each pseudodata PDF set.
- `plot_results.py` plot the pulls in $\alpha_s$ for each configuration.