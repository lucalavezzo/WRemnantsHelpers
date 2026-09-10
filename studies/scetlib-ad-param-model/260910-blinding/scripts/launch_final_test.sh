#!/bin/bash
# THE FINAL TEST for the blinding change: a real BLINDED data fit, plus the
# unblinded Asimov arm that gives the sigma(alpha_s) reference to compare it to.
#
# Production config, NP sector FREE (Luca, 2026-09-10). If the NP sector stalls
# it is the KNOWN pre-existing NP-function pathology recorded in
# ../260908-fit-770 (EDM 0.608, |grad|inf 6.49 with NP free) -- NOT a blinding
# failure. sigma(alpha_s) is only trustworthy if the fit converges, so read the
# convergence numbers before the sigma.
#
# SEQUENTIAL, not parallel: the AS770 arm peaked at 184 GiB.
#
# -v 3 not -v 4, deliberately: the log lands in a web-published study directory
# and ~/public_html has NO authentication. At -v 3 nothing in rabbit_fit's path
# prints a parameter value; -v 4 would print scipy's OptimizeResult (which is
# the BLINDED coordinate, so still safe, but there is no reason to widen it).
#
# WHAT IS SAFE TO PUBLISH: sigma(alpha_s), the impacts, the chi2/p-value, the
# convergence numbers. NOT the central value -- and it is blinded in the
# fitresult by construction, since rabbit writes the internal coordinate.
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-blinding
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CACHE=$CEPH/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
# The config-carrying card: the unmodified one now REFUSES, by design, after
# this morning's anchor work.
CARD=$CEPH/study_scratch/260910-anchor-verify/card_none.hdf5
OUT=$CEPH/260910_blinding_final
MODEL=wremnants.postprocessing.scetlib_ad.SCETlibADParamModel
M="cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128"
# --snapshotFile IS NOT OPTIONAL. rabbit installs a SIGTERM/SIGINT handler that
# writes the current iterate (rabbit/snapshot.py:161), but it is a no-op without
# a filename -- `if snapshotter.filename is None: yield; return`. Launch without
# it and a running fit cannot be stopped without losing everything: the
# fitresult is held OPEN for writing, so killing leaves a truncated file and no
# postfit to restart from.
#
# Learned the expensive way twice now: snapshot.py's own docstring records a
# preempted 22-hour fit that "wrote 33 periodic snapshots and zero signal ones",
# and on 2026-09-10 a 1h05m data fit here had to be run to completion rather
# than stopped, because this flag was missing.
# Per-arm snapshot file, NOT a shared one: two fits pointing at one snapshot
# overwrite each other (the same hazard as the saturated-fit path).
COMMON="-v 4 --jitCompile off --noBinByBinStat -o $OUT --snapshotInterval 0.25"
mkdir -p $OUT
TS=$(date +%y%m%d_%H%M%S)

echo "############ ARM 1/2: BLINDED DATA FIT (-t 0), production config, NP free"
$T/scripts/run.sh $T/logs/fit_DATABLIND_$TS.log \
  rabbit_fit.py $CARD $COMMON --postfix DATABLIND -t 0 --earlyStopping 100 \
    --snapshotFile $OUT/snapshot_DATABLIND.hdf5 \
    --saveHists --computeHistErrors --doImpacts --paramModel $MODEL $M
echo "############ ARM 1 DONE"

echo "############ ARM 2/2: UNBLINDED ASIMOV (-t -1) -- the sigma reference"
$T/scripts/run.sh $T/logs/fit_ASIMOV_$TS.log \
  rabbit_fit.py $CARD $COMMON --postfix ASIMOV -t -1 \
    --snapshotFile $OUT/snapshot_ASIMOV.hdf5 \
    --saveHists --computeHistErrors --doImpacts --paramModel $MODEL $M
echo "############ ARM 2 DONE"
echo "FINAL_TEST_DONE"
