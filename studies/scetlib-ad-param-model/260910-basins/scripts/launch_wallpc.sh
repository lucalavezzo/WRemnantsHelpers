#!/bin/bash
# EXPERIMENT 2 -- the walled fit WITH ridge preconditioning.
#
# THE QUESTION.  Four blinded data fits on the same card/cache/SCETlib/rabbit
# land on four DIFFERENT, all positive-definite minima:
#
#   plain DATABLIND   loss 405.561  sigma(as) 0.001321  sat p 2.33%  EDM 1.39e-03
#   ridge DATAPC2     loss 411.075  sigma(as) 0.000877  sat p 1.20%  EDM 4.91e-06
#   spectral DATASPEC loss 412.785  sigma(as) 0.000856  sat p 0.96%  EDM 1.46e-07
#   walled DATAWALL5  loss 411.991  sigma(as) 0.001097  sat p 1.07%  EDM 9.63e-07
#
# L2 over the 46 non-alphaS model parameters clusters {plain, walled} against
# {ridge, spectral}.  So there are (at least) two attractors, and which one you
# land in is currently decided by the NUMERICS -- the preconditioner -- not by
# any physics choice.  The wall is the one physics-motivated constraint we have.
#
# Does the wall PIN the basin?  Run the wall and the ridge TOGETHER:
#   - lands with DATAWALL5  -> the wall determines the basin; preconditioning is
#     then only a convergence aid, and quoting the walled arm is defensible.
#   - lands with DATAPC2/DATASPEC -> the basin is set by the numerics and the
#     wall does NOT resolve the ambiguity.  That is the worse answer.
#
# CONFIGURATION.  Exactly DATAWALL5 (../260910-wall-port/scripts/launch_wall_fit.sh)
# plus exactly DATAPC2's preconditioning block
# (../260910-blinding/scripts/launch_precond2.sh).  Same card, same cache, same
# SCETlib snapshot, same rabbit worktree, same threads=128, same
# --earlyStopping 100.  Two flags come from the ridge arm and are noted because
# they are the ONLY difference from DATAWALL5:
#
#   --stallRelTol 1e-5                  (DATAPC2 had it; DATAWALL5 did not.  It
#                                        gates the preconditioner REFRESH, so it
#                                        belongs with --precondition.)
#   --precondition --preconditionBlocks none --preconditionParams <47 model params>
#
# --doImpacts is NOT passed, matching DATAWALL5 and saving ~20 min.  Nothing in
# this comparison uses impacts; the cost is that the NP-group impact on alpha_s
# is again unmeasured under the wall.  Total wall clock is therefore comparable
# to DATAWALL5's 0:29:49 and NOT to DATAPC2's 1:11:02; minimize() seconds, nit
# and nhev are comparable to both.
#
# --snapshotFile IS NOT OPTIONAL: rabbit's SIGTERM handler is a no-op without a
# filename (rabbit/snapshot.py:161), so a fit launched without it cannot be
# stopped without losing everything.  Own -o directory and own snapshot file:
# two fits sharing one snapshot overwrite each other.
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-basins
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CACHE=$CEPH/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
CARD=$CEPH/study_scratch/260910-anchor-verify/card_none.hdf5
OUT=$CEPH/260910_basins
MODEL=wremnants.postprocessing.scetlib_ad.SCETlibADParamModel
WALL=wremnants.postprocessing.scetlib_ad.np_damping_wall
mkdir -p $OUT
LOG=$T/logs/fit_DATAWALLPC_$(date +%y%m%d_%H%M%S).log
echo "$LOG" > $T/logs/LATEST_WALLPC
exec $T/scripts/run.sh $LOG \
  rabbit_fit.py $CARD -v 4 --jitCompile off --noBinByBinStat -o $OUT \
    --postfix DATAWALLPC -t 0 --earlyStopping 100 --stallRelTol 1e-5 \
    --precondition --preconditionBlocks none \
    --preconditionParams 'alphaS' 'lambda.*' 'delta_lambda2' 'b0_over_bmax_nu' \
                         'resumTNP_.*' 'resumScale.*' 'resumTransition.*' 'pdfEig.*' \
    --regularizationStrength 5 \
    -r $WALL.NPDampingWall $WALL.NPDampingMapping \
    --snapshotFile $OUT/snapshot_DATAWALLPC.hdf5 --snapshotInterval 0.25 \
    --saveHists --computeHistErrors \
    --paramModel $MODEL cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128
