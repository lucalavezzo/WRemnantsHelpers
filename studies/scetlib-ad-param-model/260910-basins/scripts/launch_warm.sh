#!/bin/bash
# EXPERIMENT 1 -- warm restarts.  Restart each of the four arms FROM ITS OWN
# POSTFIT, with that arm's own configuration otherwise, and ask how far each
# parameter then moves in units of its own postfit sigma.
#
# WHAT THIS TESTS -- and what it does NOT.  All four postfit covariances have
# already been eigendecomposed: zero negative eigenvalues, Cholesky clean
# (../260910-blinding/scripts/check_minimum.py, logs/mincheck.log).  So this is
# NOT a saddle-vs-minimum test.  It is a STABILITY test: a restart that moves
# nothing (|dx|/sigma << 1 everywhere) means the seed WAS the minimum and any
# residual EDM is a quadratic-model artefact; a restart that moves alpha_s by
# O(1) sigma means that stop was not usable as a measurement.
#
# usage: launch_warm.sh <plain|ridge|spectral|walled>
#
# THE SEED is the arm's own fitresult, loaded with --externalPostfit.  rabbit's
# load_fitresult() assigns self.x from the external file (fitter.py:546-548), so
# without --noFit the minimiser simply STARTS THERE.  The blinded internal
# coordinate is what is stored and what is loaded, so the blinding offset is
# carried through unchanged and the restart is in the same blinding family.
#
# --noPostfitProfileBB IS REQUIRED.  load_fitresult() ends with
# `if profile: self._profile_beta()` (fitter.py:563), and `profile` is
# `not args.noPostfitProfileBB` -- it is NOT gated on whether bin-by-bin stat
# exists.  With --noBinByBinStat there is no bbstat.beta to assign, so ANY
# --externalPostfit run that also passes --noBinByBinStat dies with
# "ValueError: None values not supported" in _profile_beta.  The crash lands
# AFTER "Results written in file", leaving a ~44 KB stub that looks like output.
# No bin-by-bin parameters exist in this fit, so the flag is a no-op otherwise.
#
# --doImpacts is NOT passed on any arm: nothing here uses impacts and each costs
# ~20 min.  Every other flag matches the arm being restarted, threads=128
# included -- deliberately, so that a nonzero |dx| cannot be blamed on a
# different threaded reduction order.
set -e
ARM=$1
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-basins
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CACHE=$CEPH/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
CARD=$CEPH/study_scratch/260910-anchor-verify/card_none.hdf5
OUT=$CEPH/260910_basins
MODEL=wremnants.postprocessing.scetlib_ad.SCETlibADParamModel
WALL=wremnants.postprocessing.scetlib_ad.np_damping_wall
PCP="alphaS lambda.* delta_lambda2 b0_over_bmax_nu resumTNP_.* resumScale.* resumTransition.* pdfEig.*"
mkdir -p $OUT

case $ARM in
  plain)
    # ../260910-blinding/scripts/launch_final_test.sh ARM 1.  No precondition,
    # no wall, no --stallRelTol.
    SEED=$CEPH/260910_blinding_final/fitresults_DATABLIND.hdf5
    POSTFIX=WARMPLAIN
    EXTRA=""
    ;;
  ridge)
    # ../260910-blinding/scripts/launch_precond2.sh.
    SEED=$CEPH/260910_blinding_final/fitresults_DATAPC2.hdf5
    POSTFIX=WARMRIDGE
    EXTRA="--stallRelTol 1e-5 --precondition --preconditionBlocks none --preconditionParams $PCP"
    ;;
  spectral)
    # ../260910-spectral-precond/scripts/launch_spectral.sh.  NOTE: the seed is
    # the READOUT-pass fitresult DATASPECPF, not DATASPEC -- the spectral fit was
    # stopped with SIGTERM while still descending and its own fitresult is a
    # 44 KB stub.  DATASPECPF is a --noFit --externalPostfit pass at exactly the
    # snapshot point, so it holds that point plus its exact Hessian.  This arm's
    # seed is therefore a STOPPING POINT, not a converged minimum, and it is the
    # one arm expected to move.
    SEED=$CEPH/260910_spectral/fitresults_DATASPECPF.hdf5
    POSTFIX=WARMSPEC
    EXTRA="--stallRelTol 1e-5 --precondition --preconditionBlocks none --preconditionTransform spectral --preconditionParams $PCP"
    ;;
  walled)
    # ../260910-wall-port/scripts/launch_wall_fit.sh.
    SEED=$CEPH/260910_wall_port/fitresults_DATAWALL5.hdf5
    POSTFIX=WARMWALL
    EXTRA="--regularizationStrength 5 -r $WALL.NPDampingWall $WALL.NPDampingMapping"
    ;;
  *) echo "usage: launch_warm.sh <plain|ridge|spectral|walled>"; exit 2 ;;
esac

LOG=$T/logs/warm_${POSTFIX}_$(date +%y%m%d_%H%M%S).log
echo "$LOG" > $T/logs/LATEST_$POSTFIX
echo "[warm] arm=$ARM seed=$SEED postfix=$POSTFIX"
exec $T/scripts/run.sh $LOG \
  rabbit_fit.py $CARD -v 4 --jitCompile off --noBinByBinStat -o $OUT \
    --postfix $POSTFIX -t 0 --earlyStopping 100 \
    --externalPostfit $SEED --noPostfitProfileBB \
    $EXTRA \
    --snapshotFile $OUT/snapshot_$POSTFIX.hdf5 --snapshotInterval 0.25 \
    --saveHists --computeHistErrors \
    --paramModel $MODEL cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128
