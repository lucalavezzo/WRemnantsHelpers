#!/bin/bash
# Sequential ptll-only saturated-projection-test fits to fill in the missing
# sat-p column of np_compare.pdf. No NLL scans, no impacts.
#
# Configs (in order):
#   1. NPUnconstrained/data_satp           (regularizer τ=3, kfactors=1)
#   2. NPCS100pct_fakelumi/data_satp       (no regularizer)
#   3. NPCS100pctV2_fakelumi/data_satp     (no regularizer)
#   4. Inflate2x_reg5/data_satp            (regularizer τ=5, kfac 2x)
#   5. Inflate3x_reg5/data_satp            (regularizer τ=5, kfac 3x)
#   6. Inflate5x_reg5/data_satp            (regularizer τ=5, kfac 5x)
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

BASE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall
P=ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_
RABBIT=/home/submit/lavezzo/alphaS/main/WRemnants/rabbit/bin/rabbit_fit.py
REG_CLS=(wremnants.postprocessing.np_monotonicity.NPMonotonicityWall
         wremnants.postprocessing.np_monotonicity.NPMonotonicityMapping)

run_satp_only() {
  # $1=label   $2=cfg-suffix   $3=tau (empty for no reg)   $4..=kfactor tokens (e.g. lambda_2=5.24 ...)
  local label="$1"; local suffix="$2"; local tau="$3"; shift 3
  local cfg="$BASE/${P}${suffix}"
  local infile="$cfg/ZMassDilepton.hdf5"
  local out="$cfg/data_satp"
  mkdir -p "$out"
  echo "=== $(date) $label  →  $out ==="
  if [[ -z "$tau" ]]; then
    python "$RABBIT" "$infile" \
      -m Project ch0 ptll -t 0 -o "$out" \
      --computeSaturatedProjectionTests \
      --saveHists --computeHistErrors
  else
    python "$RABBIT" "$infile" \
      -m Project ch0 ptll -t 0 -o "$out" \
      --computeSaturatedProjectionTests \
      --saveHists --computeHistErrors \
      --freezeParameters scetlibNPgammaLambdaInf \
      -r "${REG_CLS[@]}" "b" "$@" \
      --regularizationStrength "$tau"
  fi
  echo "=== $(date) Done $label ==="
}

run_satp_only "unconstrained τ=3"  NPUnconstrained        "3.0"
run_satp_only "nominal+fakelumi"   NPCS100pct_fakelumi    ""
run_satp_only "inflatedV2+fakelumi" NPCS100pctV2_fakelumi ""
run_satp_only "Inflate2x_reg5"     Inflate2x_reg5         "5.0" \
  "lambda_2=5.24" "lambda_4=2.24" "Lambda_2=2.0" "Delta_Lambda_2=2.0" "Lambda_4=2.0"
run_satp_only "Inflate3x_reg5"     Inflate3x_reg5         "5.0" \
  "lambda_2=7.86" "lambda_4=3.36" "Lambda_2=3.0" "Delta_Lambda_2=3.0" "Lambda_4=3.0"
run_satp_only "Inflate5x_reg5"     Inflate5x_reg5         "5.0" \
  "lambda_2=13.1" "lambda_4=5.60" "Lambda_2=5.0" "Delta_Lambda_2=5.0" "Lambda_4=5.0"

echo "DONE_OK $(date)"
