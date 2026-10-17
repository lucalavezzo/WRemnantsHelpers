#!/usr/bin/env bash
# The ported two-panel plotter (scetlib_ad/np_function_plots) on LATFROZ_V3 (num) + XWSTIFF (den), via the wrapper.
A=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
exec bash $H/workflows/plotNPFunctions.sh \
  "Z + lattice (LATFROZ V3)=$A/261008_latfroz_nf_variants/fitresults_LATFROZ_V3.hdf5" \
  "Z only (XWSTIFF)=$A/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5" \
  -o $H/studies/ct18z-nominal-fits/261015-np-functions-tool/two_panel "$@"
