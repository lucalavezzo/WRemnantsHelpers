#!/bin/bash
# Retry the failed frozenNP + fakelumi fit. Previous run crashed with
# "Cholesky decomposition failed, Hessian is not positive-definite" inside
# save_hists. We don't need the saved histograms — only the α_S central
# value to compute the fakelumi shift — so drop --saveHists and
# --computeHistErrors. parms (α_S value + variance) is written regardless.
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

BASE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall
P=ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_
RABBIT=/home/submit/lavezzo/alphaS/main/WRemnants/rabbit/bin/rabbit_fit.py

CFG="$BASE/${P}NPCS100pct_fakelumi"
WS="$CFG/ZMassDilepton.hdf5"
OUT="$CFG/data_frozenNP_satp"
mkdir -p "$OUT"

FROZEN=(
  scetlibNPgammaLambda2
  scetlibNPgammaLambda4
  scetlibNPgammaLambdaInf
  chargeVgenNP0scetlibNPZlambda2
  chargeVgenNP0scetlibNPZdelta_lambda2
  chargeVgenNP0scetlibNPZlambda4
)

echo "=== $(date) frozenNP NPCS100pct_fakelumi (retry, no saveHists/computeHistErrors) ==="
python "$RABBIT" "$WS" \
  -m Project ch0 ptll -t 0 -o "$OUT" \
  --computeSaturatedProjectionTests \
  --freezeParameters "${FROZEN[@]}"
echo "=== $(date) DONE_OK ==="
