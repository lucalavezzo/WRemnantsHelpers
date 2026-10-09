#!/usr/bin/env bash
# Cold 1D fit on a 1D card-A variant. Flags copied from the card-A references:
#   walled   = CCWALLCOLDR (wall, strength 5, --earlyStopping 100)
#   unwalled = CCKRYLOV
# minus -m Project ch0 ptll (in 1D the full saturated test is the projection test); cache from the /scratch mirror.
#   run_1d.sh <VAR ptll|yll> <walled|unwalled> <TAG> [extra model args, e.g. fit_params=...]
set -uo pipefail
VAR=$1; MODE=$2; TAG=$3; shift 3; EXTRA=("$@")
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
A=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CACHE=/scratch/submit/cms/alphaS/ad_scetlib_caches/pdf62_corrgrid_260827/merged_full
CARD=$A/260925_Z_1D_card_adcorr/ZMassDilepton_${VAR}_adexclpdf/ZMassDilepton.hdf5
OUT=$A/260925_1d_fits/$TAG
W=wremnants.postprocessing.scetlib_ad.np_damping_wall
mkdir -p $OUT
WALL=()
if [ "$MODE" = walled ]; then WALL=(--regularizationStrength 5 -r $W.NPDampingWall $W.NPDampingMapping); ES=(--earlyStopping 100); else ES=(); fi
export OMP_NUM_THREADS=64 TF_NUM_INTRAOP_THREADS=64 TF_NUM_INTEROP_THREADS=2
"$H/agent_setup.sh" --scetlib authval -- rabbit_fit.py $CARD --jitCompile off -o $OUT -t 0 --postfix $TAG \
  --computeHistErrors --doImpacts --globalImpacts --globalImpactsDisableJVP --saveHists "${WALL[@]}" \
  --snapshotFile $OUT/snapshot_$TAG.hdf5 --snapshotInterval 0.25 \
  --paramModel wremnants.postprocessing.scetlib_ad.SCETlibADParamModel cache=$CACHE/cache.npz conf=$CACHE/cache.conf \
  threads=64 "${EXTRA[@]}" -v 4 "${ES[@]}" 2>&1 | tee -a $OUT/fit_$TAG.log
