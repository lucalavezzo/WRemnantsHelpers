#!/bin/bash
# Reversibility (hysteresis) check: continuation BACKWARD from cfrz@0.15 to 0.087.
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260911-freeze-cs
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CACHE=$CEPH/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
CARD=$CEPH/study_scratch/260910-anchor-verify/card_none.hdf5
OUT=$CEPH/260911_freeze_cs
MODEL=wremnants.postprocessing.scetlib_ad.SCETlibADParamModel
LOG=$T/logs/fit_BFRZ087_$(date +%y%m%d_%H%M%S).log
echo "$LOG" > $T/logs/LATEST_BFRZ087
exec $T/scripts/run.sh $LOG \
  rabbit_fit.py $CARD -v 4 --jitCompile off --noBinByBinStat -o $OUT \
    --postfix BFRZ087 -t 0 --earlyStopping 100 \
    --externalPostfit $OUT/seeds/seed_back_L087.hdf5 --noPostfitProfileBB \
    --freezeParameters lambda2_nu lambda4_nu \
    --snapshotFile $OUT/snapshot_BFRZ087.hdf5 --snapshotInterval 0.25 \
    --saveHists --computeHistErrors \
    --paramModel $MODEL cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128 \
      xparam_default=lambda2_nu=-0.63
