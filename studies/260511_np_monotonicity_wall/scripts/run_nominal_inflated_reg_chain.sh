#!/bin/bash
# Add the regularizer (kfactor-aware, τ=5) on top of the four nominal/inflated
# Gaussian-prior configs that don't currently have a wall companion.
# All four workspaces already exist (built by setupRabbit at study start);
# this is just rabbit_fit with the regularizer + ptll satp, no impacts.
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

BASE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall
P=ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_
RABBIT=/home/submit/lavezzo/alphaS/main/WRemnants/rabbit/bin/rabbit_fit.py
REG_CLS=(wremnants.postprocessing.np_monotonicity.NPMonotonicityWall
         wremnants.postprocessing.np_monotonicity.NPMonotonicityMapping)

run_reg() {
  # $1=label  $2=workspace-suffix  $3..=kfactor tokens
  local label="$1"; local suffix="$2"; shift 2
  local cfg="$BASE/${P}${suffix}"
  local ws="$cfg/ZMassDilepton.hdf5"
  local out="$cfg/data_reg_satp"
  mkdir -p "$out"
  if [[ ! -f "$ws" ]]; then
    echo "ERROR: workspace not found at $ws"; exit 1
  fi
  echo "=== $(date) BEGIN $label  →  $out ==="
  python "$RABBIT" "$ws" \
    -m Project ch0 ptll -t 0 -o "$out" \
    --computeSaturatedProjectionTests \
    --saveHists --computeHistErrors \
    --freezeParameters scetlibNPgammaLambdaInf \
    -r "${REG_CLS[@]}" "b" "$@" \
    --regularizationStrength '5.0'
  echo "=== $(date) DONE $label ==="
}

# kfactors mirror the per-config --scaleParams used at setupRabbit time
# (see build_compare_table.py::KFACTOR_OVERRIDES).
NPCS_KFAC=(lambda_2=2.62 lambda_4=1.12 Lambda_2=1.0 Delta_Lambda_2=1.0 Lambda_4=1.0)
INFV2_KFAC=(lambda_2=4.32 lambda_4=1.12 Lambda_2=1.0 Delta_Lambda_2=1.0 Lambda_4=1.55)

# 1. nominal + reg
run_reg "nominal+reg"            NPCS100pct             "${NPCS_KFAC[@]}"
# 2. nominal + fakelumi + reg
run_reg "nominal+fakelumi+reg"   NPCS100pct_fakelumi    "${NPCS_KFAC[@]}"
# 3. inflated (V2) + reg
run_reg "inflatedV2+reg"         NPCS100pctV2           "${INFV2_KFAC[@]}"
# 4. inflated (V2) + fakelumi + reg
run_reg "inflatedV2+fakelumi+reg" NPCS100pctV2_fakelumi "${INFV2_KFAC[@]}"

echo "DONE_OK $(date)"
