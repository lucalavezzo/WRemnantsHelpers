#!/bin/bash
# Saturated PROJECTION test on ptll, reusing a converged postfit via
# --externalPostfit --noFit so no refit is needed.
set -e
source /opt/venv/bin/activate
source /home/submit/lavezzo/alphaS/WRemnants/setup.sh > /dev/null
export SCETLIB_BUILD=/work/submit/lavezzo/alphaS/scetlib-ad-authval-260827/scetlib_snapshot/build
source /work/submit/lavezzo/alphaS/scetlib-ad-authval-260827/scetlib_snapshot/setup.sh > /dev/null
export PYTHONUNBUFFERED=1
export PYTHONPATH="/work/submit/lavezzo/alphaS/rabbit-blinding:/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260908-fit-770/lib:$PYTHONPATH"
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CACHE=$CEPH/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
CARD=$CEPH/study_scratch/260910-anchor-verify/card_none.hdf5
OUT=$CEPH/260910_saturated_try
mkdir -p $OUT
cd /home/submit/lavezzo/alphaS/WRemnants
# Fails fast at composite-model construction if the allowNegativeParam clash is real.
rabbit_fit.py $CARD -v 3 --jitCompile off --noBinByBinStat -o $OUT \
  --postfix SATTRY -t 0 --noFit --externalPostfit "$1" \
  --computeSaturatedProjectionTests -m Project ch0 ptll \
  --snapshotFile $OUT/snapshot_SATTRY.hdf5 --snapshotInterval 0.25 \
  --paramModel wremnants.postprocessing.scetlib_ad.SCETlibADParamModel \
    cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=64 2>&1 | tail -40
echo "SATTRY_RC=$?"
