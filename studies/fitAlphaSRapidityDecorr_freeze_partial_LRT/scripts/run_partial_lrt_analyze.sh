#!/bin/bash
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

DDIR=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260429_fitAlphaSRapidityDecorr/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_fitAlphaSRapidityDecorr_renamed_LambdaScale5p0
IDIR=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260429_fitAlphaSRapidityDecorr/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_nominal_LambdaScale5p0

GS="pdf_mb pdfCT18Z pdf_mb_and_CT18Z scetlibNP resumTNP prefire_stat pixel_multiplicity fsr_photos qcdscale_helicity all_top_suspects"

FROZEN=""
for g in $GS; do FROZEN="$FROZEN ${g}=${DDIR}/fitresults_freeze_${g}_decorr.hdf5"; done

INCFROZEN=""
for g in $GS; do INCFROZEN="$INCFROZEN ${g}=${IDIR}/fitresults_freeze_${g}_inclusive.hdf5"; done

python3 studies/fitAlphaSRapidityDecorr_freeze_partial_LRT/scripts/analyze_freeze_results.py \
    --baseline "$DDIR/fitresults_unblindedAsGroup.hdf5" \
    --inclusive "$IDIR/fitresults_unblindedAsGroup.hdf5" \
    --frozen $FROZEN \
    --inclusive-frozen $INCFROZEN \
    --poiRegex '^pdfCT18ZNNLO_pdfAlphaS_yll_decorr\d+$'
echo "DONE_OK $(date)"
