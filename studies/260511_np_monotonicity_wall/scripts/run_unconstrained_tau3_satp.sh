#!/bin/bash
# Unconstrained τ=3 fit with --computeSaturatedProjectionTests but WITHOUT
# --doImpacts (Cholesky issue with the regularizer when computing impacts).
# Lands the ptll sat-p that was missing from the data_lrscan run.

set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

BASE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall
CFG_DIR="$BASE/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_NPUnconstrained"
IN_HDF5="$CFG_DIR/ZMassDilepton.hdf5"
OUT_DIR="$CFG_DIR/data_satp"
mkdir -p "$OUT_DIR"

RABBIT=/home/submit/lavezzo/alphaS/main/WRemnants/rabbit/bin/rabbit_fit.py

echo "=== $(date) Running unconstrained τ=3 + sat-p (no impacts) ==="
python "$RABBIT" \
  "$IN_HDF5" \
  -m Project ch0 ptll yll -m Project ch0 ptll -m Project ch0 yll \
  -m Project ch0 'cosThetaStarll_quantile' -m Project ch0 'phiStarll_quantile' \
  -t 0 \
  -o "$OUT_DIR" \
  --computeSaturatedProjectionTests \
  --saveHists --computeHistErrors \
  --freezeParameters scetlibNPgammaLambdaInf \
  -r 'wremnants.postprocessing.np_monotonicity.NPMonotonicityWall' \
     'wremnants.postprocessing.np_monotonicity.NPMonotonicityMapping' \
  --regularizationStrength '3.0'
echo "=== $(date) Done -> $OUT_DIR/fitresults.hdf5 ==="
