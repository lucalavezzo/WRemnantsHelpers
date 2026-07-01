#!/bin/bash
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

INFILE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260429_fitAlphaSRapidityDecorr/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_fitAlphaSRapidityDecorr_renamed_LambdaScale5p0/fitresults_unblindedAsGroup.hdf5

python3 studies/fitAlphaSRapidityDecorr/diff_alphaS_impacts.py \
    "$INFILE" \
    --poiRegex '^pdfCT18ZNNLO_pdfAlphaS_yll_decorr\d+$' \
    --topN 30
echo "DONE_OK $(date)"
