#!/bin/bash
# One point of the lambda-wall margin scan: full fit -> hessian(cov) -> saturated.
#   $1 = margin value (signed; coefficient units, applied to min-of-polynomial)
#   $2 = output dir on ceph
#   $3 = mode: "plain" (default) or "dl2frozen" (freeze delta_lambda2=0)
# THREADS caps TF so several points coexist on the shared node.
# Launch (per point, from login node):
#   setsid nohup singularity exec --bind /scratch/,/work/,/home/,/ceph/ <img> \
#     bash wall_scan_point.sh <margin> <outdir> [dl2frozen] > logs/<name>_<ts>.log 2>&1 < /dev/null &
MARGIN="$1"; OUTDIR="$2"; MODE="${3:-plain}"
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh
export THREADS="${THREADS:-24}"
CARD=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260701_Z_2D/ZMassDilepton_ptll_yll_realdata/ZMassDilepton.hdf5
XPARAM="lambda6_nu=0.01,lambda6=0.01"
FREEZE="lambda_inf lambda_inf_nu lambda6 lambda6_nu"
if [ "$MODE" = "dl2frozen" ]; then
  XPARAM="${XPARAM},delta_lambda2=0"
  FREEZE="${FREEZE} delta_lambda2"
fi
echo "[wall_scan_point] margin=${MARGIN} outdir=${OUTDIR} mode=${MODE} THREADS=${THREADS}"
python workflows/fitterSCETlibNP.py "$CARD" \
  -d "$OUTDIR" \
  -m np_model_nu_fit=tanh_6 np_model_fit=tanh_6 xparam_default=${XPARAM} \
  --freeze ${FREEZE} \
  --wall damping smallb=1 margin=${MARGIN} --wallStrength 5.0 \
  --steps fit,hessian,saturated
