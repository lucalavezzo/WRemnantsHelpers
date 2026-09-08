#!/bin/bash
# ITEM 1 for the slides: sigma_gen from the AD cache vs the THEORY CORRECTION,
# on the correction's OWN binning, in qT and |Y|.
#
# This is compare_to_scetlib_run.py's second documented reference: our matched
# total against "the MATCHED prediction the analysis actually uses". Both sides
# are bin-integrated and are summed onto their COMMON bin edges (exact, no
# interpolation); the script refuses unless each side tiles that grid exactly.
# Since the 770-bin cache was built ON the correction's grid, the common grid IS
# the correction's grid -- which is what makes this the "original theory corr
# binning" comparison.
#
# --piece matched, NOT resummed: this build carries 3a8db11, where
# resummed_only() returns the matched total, so --piece resummed would be
# silently 34% wrong against a sing reference.
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260908-slides-validation
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CACHE=$CEPH/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
CORR=/home/submit/lavezzo/alphaS/WRemnants/wremnants-data/data/TheoryCorrections/scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_CorrZ.pkl.lz4
python3 scripts/rabbit/scetlib_ad/compare_to_scetlib_run.py \
    --conf $CACHE/cache.conf --cache $CACHE/cache.npz \
    --reference $CORR --piece matched \
    --threads 48 --plot-dir $T/gen_vs_corr --tag gen_vs_corr
