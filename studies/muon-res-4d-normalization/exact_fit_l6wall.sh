#!/bin/bash
# Reproduce Luca's tanh_6 + NP-damping-wall config (260714/260715 fits) on an
# arbitrary card. Same fit+hessian recipe as 260714_l6nu0p01_l60p01, card/-o swapped.
# Args: $1 = card hdf5 ; $2 = output dir
set -uo pipefail
CARD="$1"; DIR="$2"
mkdir -p "$DIR"
IMG=/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
RF=/home/submit/lavezzo/alphaS/WRemnants/rabbit/bin/rabbit_fit.py
MODEL="wremnants.postprocessing.scetlib_np.SCETlibNPParamModel np_model_nu_fit=tanh_6 np_model_fit=tanh_6 xparam_default=lambda6_nu=0.01,lambda6=0.01"
FREEZE="lambda_inf lambda_inf_nu lambda6 lambda6_nu ^scetlibNP.*"
WALL="-r wremnants.postprocessing.scetlib_np.np_damping_wall.NPDampingWall wremnants.postprocessing.scetlib_np.np_damping_wall.NPDampingMapping --regularizationStrength 5.0"
export SINGULARITYENV_CUDA_VISIBLE_DEVICES=""
export SINGULARITYENV_OMP_NUM_THREADS=48
echo "HOST=$(hostname)  CARD=$CARD  DIR=$DIR"
singularity run --bind /scratch/,/work/,/home/,/ceph/ "$IMG" bash -lc "
  export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=48
  source /opt/venv/bin/activate
  cd /home/submit/lavezzo/alphaS/WRemnantsHelpers && source setup.sh >/dev/null
  cd /home/submit/lavezzo/alphaS/WRemnants
  echo '===== FIT ====='
  python3 $RF '$CARD' -v 4 --paramModel $MODEL --freezeParameters $FREEZE $WALL --minimizerMaxiter 1000 -t 0 --noHessian -o '$DIR' || exit 1
  echo '===== HESSIAN ====='
  python3 $RF '$CARD' -v 4 --paramModel $MODEL hessian_straightthrough=1 hessian_gn=1 --freezeParameters $FREEZE $WALL --minimizerMaxiter 1000 -t 0 -o '$DIR' --externalPostfit '$DIR/fitresults.hdf5' --noFit --postfix HessianEDM || exit 1
  echo '===== ALL DONE ====='
"
