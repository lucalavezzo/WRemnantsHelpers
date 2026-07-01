#!/bin/bash
# 2D ptll-yll for inflate5x scaleParams, NO fakelumi. Companion to the
# +fakelumi versions already on disk. Two fits sharing one workspace:
#   1. inflate5x (no wall)
#   2. inflate5x_reg5 (wall τ=5, kfactors aware)
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

BASE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall
HM=/scratch/submit/cms/areimers/alphas/histmaker/AlphaS/Unblinding/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4BugfixLambda6_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5
SETUP=$WREM_BASE/scripts/rabbit/setupRabbit.py
RABBIT=/home/submit/lavezzo/alphaS/main/WRemnants/rabbit/bin/rabbit_fit.py
REG_CLS=(wremnants.postprocessing.np_monotonicity.NPMonotonicityWall
         wremnants.postprocessing.np_monotonicity.NPMonotonicityMapping)

POSTFIX=Inflate5x_2D_ptll_yll
CFG="$BASE/ZMassDilepton_ptll_yll_${POSTFIX}"

echo "=== $(date) setupRabbit ${POSTFIX} (no fakelumi) ==="
python "$SETUP" \
  --fitvar 'ptll-yll' \
  --noi alphaS --npUnc LatticeNoConstraints --pdfUncFromCorr --realData \
  --axlim ptll 0j 44j \
  --scaleParams 'scetlibNPgammaLambda2=13.1' \
                'scetlibNPgammaLambda4=5.60' \
                'scetlibNPgammaLambdaInf=3.33' \
                'chargeVgenNP0scetlibNPZlambda2=5.0' \
                'chargeVgenNP0scetlibNPZdelta_lambda2=5.0' \
                'chargeVgenNP0scetlibNPZlambda4=5.0' \
  -i "$HM" -o "$BASE" -p "${POSTFIX}"

WS="$CFG/ZMassDilepton.hdf5"
[[ -f "$WS" ]] || { echo "ERROR: workspace missing"; exit 1; }

# Fit 1: no wall
OUT="$CFG/data_satp"
mkdir -p "$OUT"
echo "=== $(date) rabbit_fit (no wall) ==="
python "$RABBIT" "$WS" \
  -m Project ch0 ptll -m Project ch0 yll -t 0 -o "$OUT" \
  --computeSaturatedProjectionTests --saveHists --computeHistErrors

# Fit 2: wall τ=5
OUT="$CFG/data_reg_satp"
mkdir -p "$OUT"
echo "=== $(date) rabbit_fit (wall τ=5) ==="
python "$RABBIT" "$WS" \
  -m Project ch0 ptll -m Project ch0 yll -t 0 -o "$OUT" \
  --computeSaturatedProjectionTests --saveHists --computeHistErrors \
  --freezeParameters scetlibNPgammaLambdaInf \
  -r "${REG_CLS[@]}" "b" \
     "lambda_2=13.1" "lambda_4=5.60" \
     "Lambda_2=5.0" "Delta_Lambda_2=5.0" "Lambda_4=5.0" \
  --regularizationStrength '5.0'

echo "=== $(date) DONE_OK ==="
