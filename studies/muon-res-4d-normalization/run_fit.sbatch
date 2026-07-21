#!/bin/bash
#SBATCH --partition=submit-gpu
#SBATCH --gres=gpu:1
#SBATCH --time=03:00:00
#SBATCH --mem=64G
#SBATCH --cpus-per-task=8
#SBATCH --job-name=ztt_fit
#SBATCH --output=/home/submit/lavezzo/alphaS/WRemnantsHelpers/logs/ztt_fit_%x_%j.log

# Phase-3 fit for the muon-res-4d-normalization study.
# Args: $1 = datacard hdf5 ; $2 = fitdir (relative -> nests under card dir)
# Runs fitterSCETlibNP.py fit+hessian, reproducing the 260623 baseline recipe
# (--freeze lambda_inf lambda_inf_nu; hessian = straight-through GN).

set -euo pipefail
CARD="$1"
FITDIR="${2:-}"
IMG=/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
WRAP=/home/submit/lavezzo/alphaS/WRemnantsHelpers/workflows/fitterSCETlibNP.py

DARG=""
if [ -n "$FITDIR" ]; then DARG="-d $FITDIR"; fi

echo "HOST=$(hostname)  CARD=$CARD  FITDIR=${FITDIR:-<carddir>}"
nvidia-smi -L || true

singularity run --nv --bind /scratch/,/work/,/home/,/ceph/ "$IMG" bash -lc "
  source /opt/venv/bin/activate
  cd /home/submit/lavezzo/alphaS/WRemnantsHelpers && source setup.sh >/dev/null
  cd /home/submit/lavezzo/alphaS/WRemnants
  python3 '$WRAP' '$CARD' -s fit,hessian --freeze lambda_inf lambda_inf_nu $DARG
"
echo "DONE fit for $CARD"
