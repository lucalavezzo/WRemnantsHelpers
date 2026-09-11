#!/bin/bash
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260911-freeze-cs
exec $T/scripts/run.sh $T/logs/makeseeds_$(date +%y%m%d_%H%M%S).log bash -c '
S=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260910_blinding_final/fitresults_DATABLIND.hdf5
O=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260911_freeze_cs/seeds
D=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260911-freeze-cs/scripts
for pair in "000:-1.5" "050:-1.0" "087:-0.63" "150:0.0" "190:0.4"; do
  tag=${pair%%:*}; th=${pair##*:}
  python3 $D/make_seed.py $S $O/seed_plain_L$tag.hdf5 "lambda2_nu=$th,lambda4_nu=0.0"
done
'
