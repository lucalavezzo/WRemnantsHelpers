#!/bin/bash
# PRECONDITIONED blinded data fit, run in PARALLEL with the plain arm.
#
# Same card, same cache, same blinding (additive, 0f64bbb), same production
# config with the NP sector FREE -- the only differences are:
#   --precondition --preconditionBlocks auto   the #156 work, already compiled
#                                              into combined-156-157 and simply
#                                              not enabled on the plain arm
#   --stallRelTol 1e-5                         the #157 flag. The default 0.0
#                                              only fires on LITERALLY zero
#                                              improvement over the window, so
#                                              the plain arm's crawl (~5e-4 per
#                                              iteration at iteration 195) never
#                                              trips it. 1e-5 stops a crawl at
#                                              the point it has actually reached.
#   --snapshotFile                             so this one CAN be stopped and
#                                              resumed, unlike the plain arm.
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-blinding
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CACHE=$CEPH/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
CARD=$CEPH/study_scratch/260910-anchor-verify/card_none.hdf5
OUT=$CEPH/260910_blinding_final
MODEL=wremnants.postprocessing.scetlib_ad.SCETlibADParamModel
mkdir -p $OUT
exec $T/scripts/run.sh $T/logs/fit_DATAPC_$(date +%y%m%d_%H%M%S).log \
  rabbit_fit.py $CARD -v 4 --jitCompile off --noBinByBinStat -o $OUT \
    --postfix DATAPC -t 0 --earlyStopping 100 --stallRelTol 1e-5 \
    --precondition --preconditionBlocks auto \
    --snapshotFile $OUT/snapshot_DATAPC.hdf5 --snapshotInterval 0.25 \
    --saveHists --computeHistErrors --doImpacts \
    --paramModel $MODEL cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128
