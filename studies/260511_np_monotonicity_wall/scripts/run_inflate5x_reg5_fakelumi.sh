#!/bin/bash
# Final robustness test: Inflate5x_reg5 (kfactor-aware wall, τ=5) + fakelumi.
# Tests whether the wall-bound NP minimum is shape-driven (robust to a free
# overall normalization) or partly yield-driven (fragile).
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

BASE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall
HM=/scratch/submit/cms/areimers/alphas/histmaker/AlphaS/Unblinding/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4BugfixLambda6_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5
SETUP=$WREM_BASE/scripts/rabbit/setupRabbit.py
RABBIT=/home/submit/lavezzo/alphaS/main/WRemnants/rabbit/bin/rabbit_fit.py

POSTFIX=Inflate5x_reg5_fakelumi
CFG_DIR="$BASE/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_${POSTFIX}"

echo "=== $(date) setupRabbit ${POSTFIX} ==="
python "$SETUP" \
  --fitvar 'ptll-yll-cosThetaStarll_quantile-phiStarll_quantile' \
  --noi alphaS --npUnc LatticeNoConstraints --pdfUncFromCorr --realData \
  --axlim ptll 0j 44j \
  --fakelumi 1.1 \
  --scaleParams \
    'scetlibNPgammaLambda2=13.1' \
    'scetlibNPgammaLambda4=5.60' \
    'scetlibNPgammaLambdaInf=3.33' \
    'chargeVgenNP0scetlibNPZlambda2=5.0' \
    'chargeVgenNP0scetlibNPZdelta_lambda2=5.0' \
    'chargeVgenNP0scetlibNPZlambda4=5.0' \
  -i "$HM" -o "$BASE" -p "${POSTFIX}"

WS="$CFG_DIR/ZMassDilepton.hdf5"
[[ -f "$WS" ]] || { echo "ERROR: workspace not found $WS"; exit 1; }

OUT="$CFG_DIR/data_satp"
mkdir -p "$OUT"
echo "=== $(date) rabbit_fit (ptll satp, wall on) -> $OUT ==="
python "$RABBIT" "$WS" \
  -m Project ch0 ptll -t 0 -o "$OUT" \
  --computeSaturatedProjectionTests \
  --saveHists --computeHistErrors \
  --freezeParameters scetlibNPgammaLambdaInf \
  -r 'wremnants.postprocessing.np_monotonicity.NPMonotonicityWall' \
     'wremnants.postprocessing.np_monotonicity.NPMonotonicityMapping' \
     "b" \
     "lambda_2=13.1" "lambda_4=5.60" \
     "Lambda_2=5.0" "Delta_Lambda_2=5.0" "Lambda_4=5.0" \
  --regularizationStrength '5.0'

echo "=== $(date) DONE_OK ==="
