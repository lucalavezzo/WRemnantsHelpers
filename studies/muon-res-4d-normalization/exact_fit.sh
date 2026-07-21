#!/bin/bash
# EXACT reproduction of the 260623 baseline fit+hessian recipe on an arbitrary card.
# Args: $1 = card hdf5 ; $2 = output dir (created if needed)
# Same two rabbit_fit.py commands as the baseline meta_info, card/-o swapped.
set -uo pipefail
CARD="$1"; DIR="$2"
mkdir -p "$DIR"
IMG=/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
RF=/home/submit/lavezzo/alphaS/WRemnants/rabbit/bin/rabbit_fit.py
MODEL=wremnants.postprocessing.scetlib_np.SCETlibNPParamModel
export SINGULARITYENV_CUDA_VISIBLE_DEVICES=""
export SINGULARITYENV_OMP_NUM_THREADS=48
echo "HOST=$(hostname)  CARD=$CARD  DIR=$DIR"
singularity run --bind /scratch/,/work/,/home/,/ceph/ "$IMG" bash -lc "
  export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=48
  source /opt/venv/bin/activate
  cd /home/submit/lavezzo/alphaS/WRemnantsHelpers && source setup.sh >/dev/null
  cd /home/submit/lavezzo/alphaS/WRemnants
  echo '===== FIT ====='
  python3 $RF '$CARD' -v 4 --paramModel $MODEL --freezeParameters lambda_inf lambda_inf_nu --minimizerMaxiter 1000 -t 0 --noHessian --noEDM -o '$DIR' || exit 1
  echo '===== HESSIAN ====='
  python3 $RF '$CARD' -v 4 --paramModel $MODEL hessian_straightthrough=1 hessian_gn=1 --freezeParameters lambda_inf lambda_inf_nu --minimizerMaxiter 1000 -t 0 -o '$DIR' --externalPostfit '$DIR/fitresults.hdf5' --postfix HessianEDM || exit 1
  echo '===== ALL DONE ====='
"
