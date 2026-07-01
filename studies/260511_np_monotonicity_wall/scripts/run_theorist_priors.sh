#!/bin/bash
# Approximates the theorist-suggested NP priors with rabbit's --scaleParams +
# --freezeParameters. The 3 "fixed" theorist values are frozen at AN nominal
# (CS λ_4 → 0.0074 vs theorist 0; CS λ_∞ → 1.685 vs theorist 2; Δ_Λ_2 → 0).
# The 3 priored values get scaleParams chosen so the σ matches the theorist
# specification:
#   CS λ_2  k=3.0  → σ_phys ≈ 0.10  (matches theorist 0.1)
#   TMD Λ_2 k=2.0  → σ_phys ≈ 0.5   (avg of theorist +0.6/−0.4)
#   TMD Λ_4 k=10   → σ_phys +0.6/−0.5 (natural asymmetry, ~theorist +0.6/−0.4)
#
# Runs two fits sharing one workspace: no fakelumi, +fakelumi.
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

BASE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall
HM=/scratch/submit/cms/areimers/alphas/histmaker/AlphaS/Unblinding/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4BugfixLambda6_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5
SETUP=$WREM_BASE/scripts/rabbit/setupRabbit.py
RABBIT=/home/submit/lavezzo/alphaS/main/WRemnants/rabbit/bin/rabbit_fit.py

# Three "fixed" parameters frozen at AN nominal.
FROZEN=(scetlibNPgammaLambda4 scetlibNPgammaLambdaInf chargeVgenNP0scetlibNPZdelta_lambda2)

THEORY_SCALE=(--scaleParams
  'scetlibNPgammaLambda2=3.0'
  'chargeVgenNP0scetlibNPZlambda2=2.0'
  'chargeVgenNP0scetlibNPZlambda4=10.0')

build_ws() {
  local postfix="$1"; shift
  local extra=("$@")
  echo "=== $(date) setupRabbit ${postfix} ==="
  python "$SETUP" \
    --fitvar 'ptll-yll-cosThetaStarll_quantile-phiStarll_quantile' \
    --noi alphaS --npUnc LatticeNoConstraints --pdfUncFromCorr --realData \
    --axlim ptll 0j 44j \
    "${THEORY_SCALE[@]}" \
    "${extra[@]}" \
    -i "$HM" -o "$BASE" -p "${postfix}"
}

fit_satp() {
  local postfix="$1"
  local cfg="$BASE/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_${postfix}"
  local out="$cfg/data_satp"
  mkdir -p "$out"
  echo "=== $(date) rabbit_fit ${postfix} ==="
  python "$RABBIT" "$cfg/ZMassDilepton.hdf5" \
    -m Project ch0 ptll -t 0 -o "$out" \
    --computeSaturatedProjectionTests \
    --saveHists --computeHistErrors \
    --freezeParameters "${FROZEN[@]}"
  echo "=== $(date) DONE ${postfix} ==="
}

# Fit 1: no fakelumi
build_ws TheoristPriors
fit_satp TheoristPriors

# Fit 2: + fakelumi
build_ws TheoristPriors_fakelumi --fakelumi 1.1
fit_satp TheoristPriors_fakelumi

echo "=== $(date) DONE_OK ==="
