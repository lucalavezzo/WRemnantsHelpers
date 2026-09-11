#!/bin/bash
# BACKWARD continuation seed: step from the converged cfrz@0.15 arm back DOWN to
# lambda2_nu = 0.087.  If the chain is a genuine single-valued one-parameter
# family, this must return to the frzCS@0.087 solution; if it does not, the
# frozen scan has hysteresis and the spread quoted from it is not a systematic
# but a path.
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260911-freeze-cs
exec $T/scripts/run.sh $T/logs/makeseeds3_$(date +%y%m%d_%H%M%S).log \
  python3 $T/scripts/make_seed.py \
    /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260911_freeze_cs/fitresults_CFRZ150.hdf5 \
    /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260911_freeze_cs/seeds/seed_back_L087.hdf5 \
    "lambda2_nu=-0.63,lambda4_nu=0.0"
