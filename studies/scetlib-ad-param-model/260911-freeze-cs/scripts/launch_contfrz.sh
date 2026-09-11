#!/bin/bash
# CONTINUATION arm: the frozen scan stepped from the converged frzCS@0.087 arm
# instead of started cold, so the 0.15 / 0.19 points stay in the branch the
# three lower points share. See scripts/run_makeseeds2.sh for why the
# "warm from plain" seeds are not usable for this.
# usage: launch_contfrz.sh <150|190>
set -e
TAG=$1
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260911-freeze-cs
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CACHE=$CEPH/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
CARD=$CEPH/study_scratch/260910-anchor-verify/card_none.hdf5
OUT=$CEPH/260911_freeze_cs
MODEL=wremnants.postprocessing.scetlib_ad.SCETlibADParamModel
M="cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128"
case $TAG in
  150) TH=0.0 ;;
  190) TH=0.4 ;;
  *) echo "usage: launch_contfrz.sh <150|190>"; exit 2 ;;
esac
SEED=$OUT/seeds/seed_c087_L$TAG.hdf5
POSTFIX=CFRZ$TAG
LOG=$T/logs/fit_${POSTFIX}_$(date +%y%m%d_%H%M%S).log
echo "$LOG" > $T/logs/LATEST_$POSTFIX
echo "[contfrz] tag=$TAG theta=$TH seed=$SEED"
exec $T/scripts/run.sh $LOG \
  rabbit_fit.py $CARD -v 4 --jitCompile off --noBinByBinStat -o $OUT \
    --postfix $POSTFIX -t 0 --earlyStopping 100 \
    --externalPostfit $SEED --noPostfitProfileBB \
    --freezeParameters lambda2_nu lambda4_nu \
    --snapshotFile $OUT/snapshot_$POSTFIX.hdf5 --snapshotInterval 0.25 \
    --saveHists --computeHistErrors \
    --paramModel $MODEL $M xparam_default=lambda2_nu=$TH
