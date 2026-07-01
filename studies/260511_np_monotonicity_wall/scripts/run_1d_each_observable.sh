#!/bin/bash
# 1D-fit diagnostic batch: fit only ptll, then only yll, on three configs.
# Tells us whether the two observables prefer the same NP nuisance values.
# No projection tests needed — the global saturated chi2 on a 1D fit IS the
# 1D goodness-of-fit. No impacts, no scans.
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

BASE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall
P=ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_
RABBIT=/home/submit/lavezzo/alphaS/main/WRemnants/rabbit/bin/rabbit_fit.py
REG_CLS=(wremnants.postprocessing.np_monotonicity.NPMonotonicityWall
         wremnants.postprocessing.np_monotonicity.NPMonotonicityMapping)

run_1d() {
  # $1=label   $2=suffix   $3=obs (ptll|yll)   $4=tau ("" for none)   $5..=kfactor tokens
  local label="$1"; local suffix="$2"; local obs="$3"; local tau="$4"; shift 4
  local cfg="$BASE/${P}${suffix}"
  local infile="$cfg/ZMassDilepton.hdf5"
  local out="$cfg/data_${obs}only"
  mkdir -p "$out"
  echo "=== $(date) $label / ${obs}-only  →  $out ==="
  if [[ -z "$tau" ]]; then
    python "$RABBIT" "$infile" \
      -m Project ch0 "$obs" -t 0 -o "$out" \
      --saveHists --computeHistErrors
  else
    python "$RABBIT" "$infile" \
      -m Project ch0 "$obs" -t 0 -o "$out" \
      --saveHists --computeHistErrors \
      --freezeParameters scetlibNPgammaLambdaInf \
      -r "${REG_CLS[@]}" "b" "$@" \
      --regularizationStrength "$tau"
  fi
  echo "=== $(date) Done $label / ${obs} ==="
}

# 1. nominal AN priors — ptll and yll
run_1d "nominal" NPCS100pct ptll ""
run_1d "nominal" NPCS100pct yll  ""

# 2. unconstrained τ=5 — ptll and yll  (regularizer on, kfactors=1)
run_1d "unconstrained_tau5" NPUnconstrained ptll "5.0"
run_1d "unconstrained_tau5" NPUnconstrained yll  "5.0"

# 3. Inflate5x_reg5 — ptll and yll  (regularizer on, kfactors 5x)
KFAC=(lambda_2=13.1 lambda_4=5.60 Lambda_2=5.0 Delta_Lambda_2=5.0 Lambda_4=5.0)
run_1d "Inflate5x_reg5" Inflate5x_reg5 ptll "5.0" "${KFAC[@]}"
run_1d "Inflate5x_reg5" Inflate5x_reg5 yll  "5.0" "${KFAC[@]}"

echo "DONE_OK $(date)"
