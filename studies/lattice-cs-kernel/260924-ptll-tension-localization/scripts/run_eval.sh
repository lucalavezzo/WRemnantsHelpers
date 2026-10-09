#!/usr/bin/env bash
# Re-evaluate a converged fit at its own postfit (--externalPostfit, --noFit) and save the ptll AND yll projections.
# No minimisation, no saturated sub-fit. Same card / model args / wall as the original fit.
#   run_eval.sh <TAG> <CARD> <FITRESULT> <walled|unwalled> [fit_params-list]
set -uo pipefail
TAG=$1; CARD=$2; POST=$3; MODE=$4; FP=${5:-}
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
A=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CACHE=/scratch/submit/cms/alphaS/ad_scetlib_caches/pdf62_corrgrid_260827/merged_full
OUT=$A/260925_postfit_eval/$TAG
W=wremnants.postprocessing.scetlib_ad.np_damping_wall
mkdir -p $OUT
WALL=(); [ "$MODE" = walled ] && WALL=(--regularizationStrength 5 -r $W.NPDampingWall $W.NPDampingMapping)
MA=(threads=64); [ -n "$FP" ] && MA+=(fit_params=$FP prior_sigmas=lambda2_nu=nan)
export OMP_NUM_THREADS=64 TF_NUM_INTRAOP_THREADS=64 TF_NUM_INTEROP_THREADS=2
"$H/agent_setup.sh" --scetlib authval -- rabbit_fit.py $CARD --jitCompile off -o $OUT -t 0 --postfix $TAG \
  --noFit --externalPostfit $POST --saveHists -m Project ch0 ptll -m Project ch0 yll "${WALL[@]}" \
  --paramModel wremnants.postprocessing.scetlib_ad.SCETlibADParamModel cache=$CACHE/cache.npz conf=$CACHE/cache.conf \
  "${MA[@]}" -v 3 2>&1 | tee -a $OUT/fit_$TAG.log
