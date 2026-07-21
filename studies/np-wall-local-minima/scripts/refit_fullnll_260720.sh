#!/bin/bash
# Re-run three wall-study fit configurations (FIT STEP ONLY) so the results
# carry nllvalfull (--fullNll is now part of fitterSCETlibNP.py's fit step).
# Sequential; same configs as the 260716/260717 originals, fresh 260720 dirs:
#   260717_2D_wallmargin_0                              -> 260720_2D_wallmargin_0_fullNll
#   260716_2D_l6nu0p01_l60p01_nowall_matchedStartingPoint -> 260720_2D_l6nu0p01_l60p01_nowall_matchedStartingPoint_fullNll
#   260716_2D_seedWalledFull_nowall                     -> 260720_2D_seedWalledFull_nowall_fullNll
# Launch (from login node):
#   setsid nohup singularity exec --bind /scratch/,/work/,/home/,/ceph/ <img> \
#     bash studies/np-wall-local-minima/scripts/refit_fullnll_260720.sh \
#     > logs/refit_fullnll_260720_<ts>.log 2>&1 < /dev/null &
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh
export THREADS="${THREADS:-24}"

CARD=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260701_Z_2D/ZMassDilepton_ptll_yll_realdata/ZMassDilepton.hdf5
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
MODELARGS="np_model_nu_fit=tanh_6 np_model_fit=tanh_6 xparam_default=lambda6_nu=0.01,lambda6=0.01"

echo "===== 1/3 wallmargin_0 (lambda-wall, margin=0) ====="
python workflows/fitterSCETlibNP.py "$CARD" -s fit \
  -d $OUT/260720_2D_wallmargin_0_fullNll \
  -m $MODELARGS \
  --freeze lambda_inf lambda_inf_nu lambda6 lambda6_nu \
  --wall damping smallb=1 margin=0 --wallStrength 5.0

echo "===== 2/3 nowall matchedStartingPoint (config A) ====="
python workflows/fitterSCETlibNP.py "$CARD" -s fit \
  -d $OUT/260720_2D_l6nu0p01_l60p01_nowall_matchedStartingPoint_fullNll \
  -m $MODELARGS \
  --freeze lambda_inf lambda_inf_nu lambda6 lambda6_nu '^scetlibNP.*'

echo "===== 3/3 seedWalledFull_nowall (config C: unwalled, walled-postfit seed) ====="
python workflows/fitterSCETlibNP.py "$CARD" -s fit \
  -d $OUT/260720_2D_seedWalledFull_nowall_fullNll \
  -m $MODELARGS \
  --freeze lambda_inf lambda_inf_nu lambda6 lambda6_nu \
  -f '--externalPostfit /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260702_2D_l6nu0p01_l60p01/fitresults_t0.hdf5'

echo "===== all three fits done ====="
