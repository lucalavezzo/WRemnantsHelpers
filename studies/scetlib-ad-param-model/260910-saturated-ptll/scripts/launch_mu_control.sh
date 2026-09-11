#!/bin/bash
# CONTROL: does rabbit's --computeSaturatedProjectionTests machinery itself
# work on this card?  Same card, same data, same mapping -- but the default
# 'Mu' param model instead of SCETlibADParamModel.  Mu has npoi = 0 on this
# card (no signal-strength POI declared), so CompositeParamModel sees exactly
# ONE POI-carrying submodel (the saturated one) and the allowNegativeParam vote
# is unanimous.  If this run produces a projected saturated p-value, the
# machinery is sound and the obstacle is our model's allowNegativeParam=True.
#
# No SCETlib, no cache: this is a plain linear template fit of the card's 3673
# nuisances, so it is cheap.
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-saturated-ptll
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CARD=$CEPH/study_scratch/260910-anchor-verify/card_none.hdf5
OUT=$CEPH/260910_saturated_ptll
mkdir -p $OUT
$T/scripts/run.sh $T/logs/mu_control_$(date +%y%m%d_%H%M%S).log \
  rabbit_fit.py $CARD -v 3 --jitCompile off --noBinByBinStat -o $OUT \
    --postfix MUCTRL -t 0 --earlyStopping 100 \
    --saveHists -m Project ch0 ptll --noPostfitProfileBB \
    --computeSaturatedProjectionTests \
    --snapshotFile $OUT/snapshot_MUCTRL.hdf5 --snapshotInterval 0.25
