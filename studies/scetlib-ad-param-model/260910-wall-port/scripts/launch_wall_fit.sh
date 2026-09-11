#!/bin/bash
# THE WALLED DATA FIT. Identical to the unwalled DATABLIND arm of
# ../260910-blinding/scripts/launch_final_test.sh -- same card, same cache, same
# SCETlib snapshot, same rabbit worktree, same flags -- with exactly two
# additions:
#
#   --regularizationStrength 5   tau; rabbit multiplies the penalty by exp(2 tau)
#   -r ...NPDampingWall ...NPDampingMapping
#
# and one removal, --doImpacts, which this task does not need and which costs
# time. So the loss / EDM / saturated p-value are directly comparable to
# DATABLIND's 405.5609 / 1.386e-03 / 2.33%.
#
# WHY tau = 5 (exp(2 tau) = 22026). The wall is meant to be a BARRIER: with the
# 5e-3 margin, the soft-wall equilibrium then sits ~5e-4 inside the physical
# region on the two conditions the unwalled fit violates (estimated from the
# postfit sigmas: lambda2_nu lands at ~+0.0048, the |Y|=2.5 cubic at ~+0.0045).
# tau = 3, which the old scetlib_np wall used, would leave lambda2_nu at ~-3e-4
# -- still negative, i.e. a failed test. The cost is curvature: the penalty adds
# ~440 in the lambda2_nu theta direction and ~1e5 in lambda4's, against the
# likelihood's own 1.7 and 7561. So a degraded EDM here is partly the wall's,
# not necessarily new tension; read the postfit lambdas first.
#
# NP sector FREE otherwise (production config, Luca 2026-09-10).
# --snapshotFile IS NOT OPTIONAL: rabbit's SIGTERM handler is a no-op without a
# filename, so a fit launched without it cannot be stopped without losing
# everything (rabbit/snapshot.py:161).
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-wall-port
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CACHE=$CEPH/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
CARD=$CEPH/study_scratch/260910-anchor-verify/card_none.hdf5
OUT=$CEPH/260910_wall_port
MODEL=wremnants.postprocessing.scetlib_ad.SCETlibADParamModel
M="cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128"
WALL=wremnants.postprocessing.scetlib_ad.np_damping_wall
COMMON="-v 4 --jitCompile off --noBinByBinStat -o $OUT --snapshotInterval 0.25"
mkdir -p $OUT
TS=$(date +%y%m%d_%H%M%S)

echo "############ WALLED BLINDED DATA FIT (-t 0), tau=5"
$T/scripts/run.sh $T/logs/fit_DATAWALL5_$TS.log \
  rabbit_fit.py $CARD $COMMON --postfix DATAWALL5 -t 0 --earlyStopping 100 \
    --snapshotFile $OUT/snapshot_DATAWALL5.hdf5 \
    --regularizationStrength 5 \
    -r $WALL.NPDampingWall $WALL.NPDampingMapping \
    --saveHists --computeHistErrors --paramModel $MODEL $M
echo "WALL_FIT_DONE"
