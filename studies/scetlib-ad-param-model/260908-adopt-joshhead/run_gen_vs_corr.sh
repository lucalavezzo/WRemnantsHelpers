#!/bin/bash
# Item 1 with the NEW library, same cache and same reference, so the ONLY
# difference from 260908-slides-validation/01 is the library.
set -e
S=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260908-adopt-joshhead
CACHE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
CORR=/home/submit/lavezzo/alphaS/WRemnants/wremnants-data/data/TheoryCorrections/scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_CorrZ.pkl.lz4
python3 scripts/rabbit/scetlib_ad/compare_to_scetlib_run.py \
    --conf $CACHE/cache.conf --cache $CACHE/cache.npz \
    --reference $CORR --piece matched \
    --threads 48 --plot-dir $S/gen_vs_corr --tag joshhead
