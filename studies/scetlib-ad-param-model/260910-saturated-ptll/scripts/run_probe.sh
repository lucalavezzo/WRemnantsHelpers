#!/bin/bash
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-saturated-ptll
CARD=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/study_scratch/260910-anchor-verify/card_none.hdf5
$T/scripts/run.sh $T/logs/probe_$(date +%y%m%d_%H%M%S).log \
  python3 $T/scripts/probe_saturated.py $CARD ch0 ptll
