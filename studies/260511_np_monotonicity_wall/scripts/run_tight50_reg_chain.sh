#!/bin/bash
# Tight50 (50% of AN-100pct prior widths) + wall, with and without fakelumi.
# Tests whether tightening the NP priors reduces the α_S-fakelumi shift —
# i.e., confirms NPs are the mediator of the yield-shape compromise.
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

# 50% of AN-100pct prior widths.
# CS: half of 2.62 / 1.12 / 3.33. TMD: half of default k=1 → 0.5 each.
TIGHT_SCALEPARAMS=(
  --scaleParams
  'scetlibNPgammaLambda2=1.31'
  'scetlibNPgammaLambda4=0.56'
  'scetlibNPgammaLambdaInf=1.665'
  'chargeVgenNP0scetlibNPZlambda2=0.5'
  'chargeVgenNP0scetlibNPZdelta_lambda2=0.5'
  'chargeVgenNP0scetlibNPZlambda4=0.5'
)
# Matching wall kfactors (regularizer needs to know the actual prior width).
TIGHT_KFAC=(
  lambda_2=1.31  lambda_4=0.56
  Lambda_2=0.5   Delta_Lambda_2=0.5  Lambda_4=0.5
)

run_pair() {
  # $1=postfix tag   $2=extra setupRabbit args (e.g. "--fakelumi 1.1")
  local postfix="$1"; shift
  local cfg="$BASE/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_${postfix}"

  echo "=== $(date) setupRabbit ${postfix} ==="
  python "$SETUP" \
    --fitvar 'ptll-yll-cosThetaStarll_quantile-phiStarll_quantile' \
    --noi alphaS --npUnc LatticeNoConstraints --pdfUncFromCorr --realData \
    --axlim ptll 0j 44j \
    "${TIGHT_SCALEPARAMS[@]}" \
    "$@" \
    -i "$HM" -o "$BASE" -p "${postfix}"

  local ws="$cfg/ZMassDilepton.hdf5"
  [[ -f "$ws" ]] || { echo "ERROR: workspace $ws missing"; exit 1; }
  local out="$cfg/data_reg_satp"
  mkdir -p "$out"

  echo "=== $(date) rabbit_fit (wall on, ptll satp) ${postfix} ==="
  python "$RABBIT" "$ws" \
    -m Project ch0 ptll -t 0 -o "$out" \
    --computeSaturatedProjectionTests \
    --saveHists --computeHistErrors \
    --freezeParameters scetlibNPgammaLambdaInf \
    -r "${REG_CLS[@]}" "b" "${TIGHT_KFAC[@]}" \
    --regularizationStrength '5.0'
  echo "=== $(date) DONE ${postfix} ==="
}

run_pair NPCS50pct
run_pair NPCS50pct_fakelumi --fakelumi 1.1

echo "DONE_OK $(date)"
