#!/bin/bash
# Two 2D ptll-yll fits with inflate5x scaleParams + fakelumi:
#   1. inflate5x + fakelumi (no wall)
#   2. inflate5x + fakelumi + reg (τ=5, wall on, with kfactors)
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

INF5_SCALE=(--scaleParams
  'scetlibNPgammaLambda2=13.1'
  'scetlibNPgammaLambda4=5.60'
  'scetlibNPgammaLambdaInf=3.33'
  'chargeVgenNP0scetlibNPZlambda2=5.0'
  'chargeVgenNP0scetlibNPZdelta_lambda2=5.0'
  'chargeVgenNP0scetlibNPZlambda4=5.0')
INF5_KFAC=(lambda_2=13.1 lambda_4=5.60 Lambda_2=5.0 Delta_Lambda_2=5.0 Lambda_4=5.0)

build_ws() {
  local postfix="$1"
  echo "=== $(date) setupRabbit ${postfix} ==="
  python "$SETUP" \
    --fitvar 'ptll-yll' \
    --noi alphaS --npUnc LatticeNoConstraints --pdfUncFromCorr --realData \
    --axlim ptll 0j 44j \
    --fakelumi 1.1 \
    "${INF5_SCALE[@]}" \
    -i "$HM" -o "$BASE" -p "${postfix}"
}

fit_nowall() {
  local postfix="$1"
  local cfg="$BASE/ZMassDilepton_ptll_yll_${postfix}"
  local out="$cfg/data_satp"
  mkdir -p "$out"
  echo "=== $(date) rabbit_fit (no wall) ${postfix} ==="
  python "$RABBIT" "$cfg/ZMassDilepton.hdf5" \
    -m Project ch0 ptll -m Project ch0 yll -t 0 -o "$out" \
    --computeSaturatedProjectionTests --saveHists --computeHistErrors
  echo "=== $(date) DONE ${postfix} ==="
}

fit_wall() {
  local postfix="$1"
  local cfg="$BASE/ZMassDilepton_ptll_yll_${postfix}"
  local out="$cfg/data_reg_satp"
  mkdir -p "$out"
  echo "=== $(date) rabbit_fit (wall τ=5) ${postfix} ==="
  python "$RABBIT" "$cfg/ZMassDilepton.hdf5" \
    -m Project ch0 ptll -m Project ch0 yll -t 0 -o "$out" \
    --computeSaturatedProjectionTests --saveHists --computeHistErrors \
    --freezeParameters scetlibNPgammaLambdaInf \
    -r "${REG_CLS[@]}" "b" "${INF5_KFAC[@]}" \
    --regularizationStrength '5.0'
  echo "=== $(date) DONE ${postfix} (wall) ==="
}

# Fit 1: inflate5x + fakelumi (no wall)
build_ws Inflate5x_2D_ptll_yll_fakelumi
fit_nowall Inflate5x_2D_ptll_yll_fakelumi

# Fit 2: inflate5x_reg5 + fakelumi (wall on) — uses the SAME workspace
# (the inflated scaleParams are the same; the wall is just a rabbit_fit-time flag).
fit_wall Inflate5x_2D_ptll_yll_fakelumi

echo "DONE_OK $(date)"
