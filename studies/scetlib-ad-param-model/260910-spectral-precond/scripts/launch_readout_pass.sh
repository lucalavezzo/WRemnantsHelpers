#!/bin/bash
# Hessian / EDM / sigma / saturated-chi2 at the point DATASPEC actually reached.
#
# WHY THIS EXISTS. The spectral arm did not converge. It was still descending at
# iteration 719 / 8594 s of minimize() (loss 412.7846), with single iterations
# costing 324 s and 599 s -- a Krylov inner solve of five to ten minutes per
# outer step, which is precisely the pathology preconditioning is supposed to
# remove. It was stopped with SIGTERM at 2:27:43 wall, against the plain arm's
# 1:04:19 and the ridge arm's 1:11:02, both of which had finished. Leaving it to
# run would not have changed the verdict and would have held ~184 GiB and 128
# threads against another session's work.
#
# rabbit's signal handler wrote 'signal-SIGTERM' to the snapshot (that is what
# --snapshotFile buys, and why it is not optional), so the reached point is
# recoverable exactly.
#
# THE RECIPE is rabbit's own documented two-pass one (bin/rabbit_fit.py:613-619):
# with --externalPostfit pointing at a file that carries NO covariance -- a
# snapshot does not -- and --noFit, the gate at :621 falls through and rabbit
# computes the exact Hessian, edmval and covariance AT THE LOADED POINT. So the
# numbers below are honest measurements at the stopping point; they are NOT
# measurements at a minimum, and must be quoted that way.
#
# --noPostfitProfileBB IS REQUIRED HERE, and the first attempt died without it:
#
#   File "rabbit/fitter.py", line 1902, in _profile_beta
#     self.bbstat.beta.assign(beta)
#   ValueError: None values not supported.
#
# load_fitresult() ends with `if profile: self._profile_beta()`
# (fitter.py:563-564) and `profile` is `not args.noPostfitProfileBB` --
# it is NOT gated on whether bin-by-bin stat exists. With --noBinByBinStat
# there is no `bbstat.beta` to assign, so ANY --externalPostfit run that also
# passes --noBinByBinStat crashes unless --noPostfitProfileBB is given too.
# The crash lands AFTER "Results written in file ...", so it leaves a 44 KB
# stub fitresult that looks like an output. Not a physics choice: there are no
# bin-by-bin parameters in this fit to profile, so the flag is a no-op here
# beyond avoiding the crash.
#
# --precondition is deliberately NOT passed: nothing is minimised here, and
# building the transform would cost an extra full Hessian for nothing. Every
# other flag matches the DATASPEC fit and the other three arms, --doImpacts
# included, so the postfit is like-for-like.
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-spectral-precond
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CACHE=$CEPH/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
CARD=$CEPH/study_scratch/260910-anchor-verify/card_none.hdf5
OUT=$CEPH/260910_spectral
MODEL=wremnants.postprocessing.scetlib_ad.SCETlibADParamModel
LOG=$T/logs/readout_DATASPECPF_$(date +%y%m%d_%H%M%S).log
echo "$LOG" > $T/logs/LATEST_PF
exec $T/scripts/run.sh $LOG \
  rabbit_fit.py $CARD -v 4 --jitCompile off --noBinByBinStat -o $OUT \
    --postfix DATASPECPF -t 0 \
    --noFit --externalPostfit $OUT/snapshot_DATASPEC.hdf5 \
    --noPostfitProfileBB \
    --snapshotFile $OUT/snapshot_DATASPECPF.hdf5 --snapshotInterval 0.25 \
    --saveHists --computeHistErrors --doImpacts \
    --paramModel $MODEL cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128
