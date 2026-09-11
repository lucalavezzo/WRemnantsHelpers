#!/bin/bash
# CONTINUATION seeds.  The "warm from plain" seeds turned out NOT to be warm:
# lambda4_nu is an extremely stiff direction (postfit sigma(theta) = 0.024), so
# setting it to 0 while holding the rest of the plain postfit lands at a loss of
# 1e3-2e6, i.e. FARTHER from any minimum than the cold start's ~3425.
#
# A continuation seed fixes that.  Seed from the CONVERGED frzCS@0.087 arm --
# which already has lambda4_nu = 0 and whose remaining 3718 parameters are tuned
# to that -- and move ONLY lambda2_nu, a soft direction (sigma(theta) = 0.77).
# The step stays inside the branch the three lower points share, which is exactly
# what the cold 0.15 / 0.19 arms failed to do.
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260911-freeze-cs
exec $T/scripts/run.sh $T/logs/makeseeds2_$(date +%y%m%d_%H%M%S).log bash -c '
S=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260911_freeze_cs/fitresults_FRZCSL087.hdf5
O=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260911_freeze_cs/seeds
D=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260911-freeze-cs/scripts
for pair in "150:0.0" "190:0.4"; do
  tag=${pair%%:*}; th=${pair##*:}
  python3 $D/make_seed.py $S $O/seed_c087_L$tag.hdf5 "lambda2_nu=$th,lambda4_nu=0.0"
done
'
