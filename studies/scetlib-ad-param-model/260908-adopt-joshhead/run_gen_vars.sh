#!/bin/bash
# Gen-level variations with the NEW library, same cache/reference as
# 260908-slides-validation/02_gen_vars (b66f8de: 97 vars, worst 3.09e-02 mufup).
# The muF and transition directions are where MR !8/!9 lived, so this is the
# comparison that decides whether adoption is value-neutral for the RESPONSE.
set -e
S=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260908-adopt-joshhead
CORRDIR=/home/submit/lavezzo/alphaS/WRemnants/wremnants-data/data/TheoryCorrections
BASE=scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO
CACHE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
python3 scripts/rabbit/scetlib_ad/validate_variations.py \
    --corr $CORRDIR/${BASE}_CorrZ.pkl.lz4 \
           $CORRDIR/${BASE}_pdfas_CorrZ.pkl.lz4 \
           $CORRDIR/${BASE}_pdfvars_CorrZ.pkl.lz4 \
    --cache $CACHE/cache.npz --conf $CACHE/cache.conf \
    --threads 48 --profile --plot-dir $S/gen_variations
