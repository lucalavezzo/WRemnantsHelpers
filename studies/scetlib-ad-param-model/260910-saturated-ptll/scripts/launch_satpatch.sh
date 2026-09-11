#!/bin/bash
# The projected saturated test with the STUDY-PATCHED driver
# (patched/rabbit_fit_satpatch.py, diff in patched/satpatch.diff):
#   1. SaturatedProjectModel gets the parent model's allowNegativeParam;
#   2. blinding is re-armed and the composite fit is WARM-started at the main
#      postfit (bin scales at 1) instead of cold from the anchor.
# Everything else -- card, cache, SCETlib build, rabbit worktree, flags -- is
# identical to scripts/launch_sat.sh, so the two are directly comparable.
#
# --unblind 'saturated_.*' leaves alphaS BLINDED and unblinds only the 39 bin
# scale factors, whose additive offsets would otherwise be random N(0,5) draws
# that make the reported r_j unreadable. Check the log for
# "Unblinding 39 parameters" -- it must be 39, and it must not name alphaS.
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-saturated-ptll
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CACHE=$CEPH/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
CARD=$CEPH/study_scratch/260910-anchor-verify/card_none.hdf5
OUT=$CEPH/260910_saturated_ptll
MODEL=wremnants.postprocessing.scetlib_ad.SCETlibADParamModel
mkdir -p $OUT
TAG=$1; FR=$2; shift 2
$T/scripts/run.sh $T/logs/satpatch_${TAG}_$(date +%y%m%d_%H%M%S).log \
  python3 $T/patched/rabbit_fit_satpatch.py $CARD -v 3 --jitCompile off \
    --noBinByBinStat -o $OUT \
    --postfix SATPATCH$TAG -t 0 --noFit --externalPostfit $FR \
    --saveHists --computeHistErrors -m Project ch0 ptll --noPostfitProfileBB \
    --computeSaturatedProjectionTests --earlyStopping 100 \
    --unblind 'saturated_.*' \
    --snapshotFile $OUT/snapshot_SATPATCH$TAG.hdf5 --snapshotInterval 0.25 \
    "$@" \
    --paramModel $MODEL cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=64
