#!/bin/bash
# CPU fit for the muon-res-4d-normalization study (login node, no GPU).
# Args: $1 = datacard hdf5 ; $2 = fitdir (relative -> nests under card dir, optional)
set -uo pipefail
CARD="$1"; FITDIR="${2:-}"
IMG=/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
WRAP=/home/submit/lavezzo/alphaS/WRemnantsHelpers/workflows/fitterSCETlibNP.py
DARG=""; [ -n "$FITDIR" ] && DARG="-d $FITDIR"
THREADS="${THREADS:-32}"

echo "HOST=$(hostname)  CPU fit  CARD=$CARD  FITDIR=${FITDIR:-<carddir>}  THREADS=$THREADS"
export SINGULARITYENV_CUDA_VISIBLE_DEVICES=""   # force CPU: hide any GPU
export SINGULARITYENV_OMP_NUM_THREADS="$THREADS"
export SINGULARITYENV_THREADS="$THREADS"
# NOTE: no --nv, so the container runs TensorFlow on CPU.
singularity run --bind /scratch/,/work/,/home/,/ceph/ "$IMG" bash -lc "
  export CUDA_VISIBLE_DEVICES=''
  export OMP_NUM_THREADS=$THREADS
  export THREADS=$THREADS
  source /opt/venv/bin/activate
  cd /home/submit/lavezzo/alphaS/WRemnantsHelpers && source setup.sh >/dev/null
  cd /home/submit/lavezzo/alphaS/WRemnants
  python3 '$WRAP' '$CARD' -s fit,hessian --freeze lambda_inf lambda_inf_nu $DARG
"
echo "DONE CPU fit for $CARD (exit $?)"
