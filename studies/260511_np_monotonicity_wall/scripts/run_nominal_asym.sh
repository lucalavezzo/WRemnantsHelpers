#!/bin/bash
# Same as nominal (NPCS100pct, AN-100% priors) but with the SCETlib NP
# templates kept ASYMMETRIC (default rabbit setup symmetrizes them). Two
# fits sharing the no-fakelumi workspace and the +fakelumi workspace.
#
# --noSymmetrize 'scetlibNPgamma|scetlibNPZlambda|scetlibNPZdelta_lambda'
# keeps the natural template asymmetry intact (notably Λ_4 with +0.06/−0.05).
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

BASE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall
HM=/scratch/submit/cms/areimers/alphas/histmaker/AlphaS/Unblinding/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4BugfixLambda6_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5
SETUP=$WREM_BASE/scripts/rabbit/setupRabbit.py
RABBIT=/home/submit/lavezzo/alphaS/main/WRemnants/rabbit/bin/rabbit_fit.py

ASYM_NP='scetlibNPgamma|scetlibNPZlambda|scetlibNPZdelta_lambda'

build_ws() {
  local postfix="$1"; shift
  local extra=("$@")
  echo "=== $(date) setupRabbit ${postfix} ==="
  python "$SETUP" \
    --fitvar 'ptll-yll-cosThetaStarll_quantile-phiStarll_quantile' \
    --noi alphaS --npUnc LatticeNoConstraints --pdfUncFromCorr --realData \
    --axlim ptll 0j 44j \
    --noSymmetrize "$ASYM_NP" \
    --scaleParams 'scetlibNPgammaLambda2=2.62' \
                  'scetlibNPgammaLambda4=1.12' \
                  'scetlibNPgammaLambdaInf=3.33' \
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
    --saveHists --computeHistErrors
  echo "=== $(date) DONE ${postfix} ==="
}

build_ws NPCS100pct_asym
fit_satp NPCS100pct_asym

build_ws NPCS100pct_asym_fakelumi --fakelumi 1.1
fit_satp NPCS100pct_asym_fakelumi

echo "DONE_OK $(date)"
