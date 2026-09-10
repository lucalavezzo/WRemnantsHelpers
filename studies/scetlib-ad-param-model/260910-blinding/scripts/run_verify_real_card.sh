#!/bin/bash
# Verification 3: start invariance under arming, on the REAL 770-bin card.
# SCETlib is the frozen validated snapshot b66f8de (see ../260908-fit-770).
set -e
source /opt/venv/bin/activate
source /home/submit/lavezzo/alphaS/WRemnants/setup.sh > /dev/null
export SCETLIB_BUILD=/work/submit/lavezzo/alphaS/scetlib-ad-authval-260827/scetlib_snapshot/build
source /work/submit/lavezzo/alphaS/scetlib-ad-authval-260827/scetlib_snapshot/setup.sh > /dev/null
export PYTHONPATH="/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260908-fit-770/lib:$PYTHONPATH"

T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-blinding
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CACHE=$CEPH/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
# the config-carrying copy made for the anchor work
CARD=$CEPH/study_scratch/260910-anchor-verify/card_none.hdf5
cd /home/submit/lavezzo/alphaS/WRemnants
python3 -u "$T/scripts/verify_real_card.py" "$CARD" "$CACHE/cache.npz" "$CACHE/cache.conf" 2>&1 \
  | grep -v -e "absl::InitializeLog" -e "cpu_feature_guard" -e "To enable the following" \
            -e "cuda_platform" -e "^ch0 {" -e "^       " -e "beamfunc grids"
echo "REALCARD_DONE"
