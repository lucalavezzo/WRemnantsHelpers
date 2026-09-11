#!/bin/bash
# Saturated PROJECTION test on ptll for one arm, reusing a converged postfit.
#
#   $1  arm tag (UNWALL | WALL5)
#   $2  fitresult to load with --externalPostfit
#   $3+ extra rabbit args (the wall, for the walled arm)
#
# --noFit --externalPostfit reuses the converged postfit: nothing in the MAIN
# fit is re-minimised.  (The saturated block itself calls minimize()
# unconditionally -- it does NOT respect --noFit -- so if the composite model
# constructs, a cold-start refit of [alphaS+POUs+39 bin scales] follows.)
#
# --saveHists IS REQUIRED: the saturated-projection block lives inside
# save_hists()'s postfit mapping loop (bin/rabbit_fit.py:397), so without it
# --computeSaturatedProjectionTests is silently a no-op.
#
# NOT --noHessian: load_fitresult RAISES if the external fitresult carries a
# covariance and the fitter was built with --noHessian (fitter.py:550).  Both
# arms' fitresults do carry one, and the main-fit Hessian is skipped anyway
# when the external covariance loads (rabbit_fit.py:619).
#
# --noPostfitProfileBB IS REQUIRED here: load_fitresult() ends in
# _profile_beta() unless it is set, and with --noBinByBinStat the bbstat
# tensors are None, so the first attempt died with
# "ValueError: None values not supported" at fitter.py:1902.  Nothing is
# profiled away by setting it -- there are no bin-by-bin stat nuisances.
#
# --snapshotFile IS NOT OPTIONAL: rabbit's SIGTERM handler is a no-op without a
# filename (rabbit/snapshot.py).
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-saturated-ptll
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CACHE=$CEPH/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
CARD=$CEPH/study_scratch/260910-anchor-verify/card_none.hdf5
OUT=$CEPH/260910_saturated_ptll
MODEL=wremnants.postprocessing.scetlib_ad.SCETlibADParamModel
mkdir -p $OUT
TAG=$1; FR=$2; shift 2
$T/scripts/run.sh $T/logs/sat_${TAG}_$(date +%y%m%d_%H%M%S).log \
  rabbit_fit.py $CARD -v 3 --jitCompile off --noBinByBinStat -o $OUT \
    --postfix SAT$TAG -t 0 --noFit --externalPostfit $FR \
    --saveHists --computeHistErrors -m Project ch0 ptll --noPostfitProfileBB \
    --computeSaturatedProjectionTests \
    --snapshotFile $OUT/snapshot_SAT$TAG.hdf5 --snapshotInterval 0.25 \
    "$@" \
    --paramModel $MODEL cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=64
