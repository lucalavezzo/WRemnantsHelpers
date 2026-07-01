#!/bin/bash
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

B=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall
RABBIT=/home/submit/lavezzo/alphaS/main/WRemnants/rabbit/bin/rabbit_fit.py
CFG="$B/ZMassDilepton_ptll_yll_Inflate5x_2D_ptll_yll_fakelumi"
OUT="$CFG/data_reg_satp"
mkdir -p "$OUT"

echo "=== $(date) retry rabbit_fit wall+fakelumi (no saveHists) ==="
python "$RABBIT" "$CFG/ZMassDilepton.hdf5" \
  -m Project ch0 ptll -m Project ch0 yll -t 0 -o "$OUT" \
  --computeSaturatedProjectionTests \
  --freezeParameters scetlibNPgammaLambdaInf \
  -r 'wremnants.postprocessing.np_monotonicity.NPMonotonicityWall' \
     'wremnants.postprocessing.np_monotonicity.NPMonotonicityMapping' \
     "b" "lambda_2=13.1" "lambda_4=5.60" \
     "Lambda_2=5.0" "Delta_Lambda_2=5.0" "Lambda_4=5.0" \
  --regularizationStrength '5.0'
echo "=== $(date) DONE_OK ==="
