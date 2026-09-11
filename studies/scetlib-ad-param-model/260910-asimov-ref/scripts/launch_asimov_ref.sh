#!/bin/bash
# THE UNBLINDED ASIMOV REFERENCE ARM (ASIMOVREF) for the additive-blinding test.
#
# WHY THIS ARM EXISTS. The acceptance criterion for the additive-blinding change
# (rabbit 0f64bbb on `blinding-additive`) is "central value hidden, uncertainty
# intact". The blinded data arm DATABLIND supplied the first half and a
# sigma(alpha_s); this arm supplies the REFERENCE the sigma is compared to. An
# Asimov fit is never blinded -- rabbit sets
#   blinded_fits = [f == 0 or (f > 0 and toysDataMode == "observed")]
# so `-t -1` is False -- which is exactly what makes it the reference. If the
# two sigmas agree, additive blinding leaves the uncertainty exact.
#
# IDENTICAL to the DATABLIND arm in every respect except `-t -1` (and the
# postfix / snapshot filename that must differ per arm). Same card, same cache,
# same model, same --earlyStopping, same verbosity.
#
# ON -v 4 AND THE WEB. The log lands in a web-published study directory and
# ~/public_html has NO authentication. It is safe HERE and only here: this arm
# is unblinded by construction, so the alphaS value in it is the Asimov INPUT
# (the anchor, 0.118), not a measurement of data. Nothing from the BLINDED
# arm's central value is read or printed by this script.
#
# --snapshotFile IS NOT OPTIONAL. rabbit's SIGTERM/SIGINT handler is a no-op
# without a filename (rabbit/snapshot.py: `if snapshotter.filename is None:
# yield; return`), and the filename only defaults when --snapshotInterval > 0.
# A fit launched without it cannot be stopped without losing everything -- that
# cost an hour on 2026-09-10. Per-arm file, never shared: two fits pointing at
# one snapshot overwrite each other.
#
# ONE ARM ONLY. A concurrent fit (DATAPC2) is running and the AS770 arm peaked
# at ~184 GiB RSS. Do not add arms to this script; do not run it twice at once.
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-asimov-ref
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CARD=$CEPH/study_scratch/260910-anchor-verify/card_none.hdf5
CACHE=$CEPH/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
OUT=$CEPH/260910_blinding_final
MODEL=wremnants.postprocessing.scetlib_ad.SCETlibADParamModel
M="cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128"
mkdir -p $OUT
TS=$(date +%y%m%d_%H%M%S)
LOG=$T/logs/fit_ASIMOVREF_$TS.log
ln -sfn $LOG $T/logs/LATEST

echo "############ UNBLINDED ASIMOV (-t -1) -- the sigma(alpha_s) reference"
$T/scripts/run.sh $LOG \
  rabbit_fit.py $CARD -v 4 --jitCompile off --noBinByBinStat -o $OUT \
    --postfix ASIMOVREF -t -1 --earlyStopping 100 \
    --snapshotFile $OUT/snapshot_ASIMOVREF.hdf5 --snapshotInterval 0.25 \
    --saveHists --computeHistErrors --doImpacts \
    --paramModel $MODEL $M
echo "ASIMOVREF_DONE rc=$?"
