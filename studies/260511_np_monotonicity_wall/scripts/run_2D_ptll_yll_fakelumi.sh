#!/bin/bash
# 2D ptll-yll nominal fit + fakelumi (companion to the 2D nominal fit
# launched earlier). Measures the fakelumi shift on α_S without the
# angular observables in the fit.
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

BASE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall
HM=/scratch/submit/cms/areimers/alphas/histmaker/AlphaS/Unblinding/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4BugfixLambda6_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5
SETUP=$WREM_BASE/scripts/rabbit/setupRabbit.py
RABBIT=/home/submit/lavezzo/alphaS/main/WRemnants/rabbit/bin/rabbit_fit.py

POSTFIX=NPCS100pct_2D_ptll_yll_fakelumi
CFG_DIR="$BASE/ZMassDilepton_ptll_yll_${POSTFIX}"

echo "=== $(date) setupRabbit ${POSTFIX} ==="
python "$SETUP" \
  --fitvar 'ptll-yll' \
  --noi alphaS --npUnc LatticeNoConstraints --pdfUncFromCorr --realData \
  --axlim ptll 0j 44j \
  --fakelumi 1.1 \
  --scaleParams 'scetlibNPgammaLambda2=2.62' \
                'scetlibNPgammaLambda4=1.12' \
                'scetlibNPgammaLambdaInf=3.33' \
  -i "$HM" -o "$BASE" -p "${POSTFIX}"

WS="$CFG_DIR/ZMassDilepton.hdf5"
[[ -f "$WS" ]] || { echo "ERROR: workspace $WS missing"; exit 1; }
OUT="$CFG_DIR/data_satp"
mkdir -p "$OUT"
echo "=== $(date) rabbit_fit ==="
python "$RABBIT" "$WS" \
  -m Project ch0 ptll -m Project ch0 yll \
  -t 0 -o "$OUT" \
  --computeSaturatedProjectionTests \
  --saveHists --computeHistErrors
echo "=== $(date) DONE_OK ==="
