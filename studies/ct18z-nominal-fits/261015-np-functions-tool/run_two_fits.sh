#!/usr/bin/env bash
# RETIRED 2026-10-15: scripts/np_functions/ was deleted (superseded by scetlib_ad/np_function_plots); kept as the record of the runs.
# Validation 2: the N-fit path through the workflow wrapper, defaults only (labels = keys, auto colours/bands).
A=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
exec bash $H/workflows/plotNPFunctions.sh \
  LATFROZ_V3=$A/261008_latfroz_nf_variants/fitresults_LATFROZ_V3.hdf5 \
  $A/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5 \
  -o $H/studies/ct18z-nominal-fits/261015-np-functions-tool/two_fits -e "--all" "$@"
