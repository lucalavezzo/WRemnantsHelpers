#!/bin/bash
# Run LR scan over alphaS for the inflated+regularizer (tau=5) fits.
# These existed only as flat fitresults.hdf5 with no LR scan; this fills that in.
# Launched inside the wmassdevrolling container via singularity.

set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

BASE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall
RABBIT=/home/submit/lavezzo/alphaS/main/WRemnants/rabbit/bin/rabbit_fit.py

# Per-config kfactors (from build_compare_table.py KFACTOR_OVERRIDES) — must
# match the --scaleParams used to build each ZMassDilepton.hdf5 so the
# regularizer's view of the physical NP value tracks the fit's view.
declare -A KFAC_LAMBDA2 KFAC_LAMBDA4 KFAC_BIG_LAMBDA2 KFAC_DELTA_LAMBDA2 KFAC_BIG_LAMBDA4
KFAC_LAMBDA2[Inflate2x_reg5]=5.24;  KFAC_LAMBDA4[Inflate2x_reg5]=2.24
KFAC_BIG_LAMBDA2[Inflate2x_reg5]=2.0; KFAC_DELTA_LAMBDA2[Inflate2x_reg5]=2.0; KFAC_BIG_LAMBDA4[Inflate2x_reg5]=2.0
KFAC_LAMBDA2[Inflate3x_reg5]=7.86;  KFAC_LAMBDA4[Inflate3x_reg5]=3.36
KFAC_BIG_LAMBDA2[Inflate3x_reg5]=3.0; KFAC_DELTA_LAMBDA2[Inflate3x_reg5]=3.0; KFAC_BIG_LAMBDA4[Inflate3x_reg5]=3.0
KFAC_LAMBDA2[Inflate5x_reg5]=13.1;  KFAC_LAMBDA4[Inflate5x_reg5]=5.60
KFAC_BIG_LAMBDA2[Inflate5x_reg5]=5.0; KFAC_DELTA_LAMBDA2[Inflate5x_reg5]=5.0; KFAC_BIG_LAMBDA4[Inflate5x_reg5]=5.0

for SUFFIX in Inflate2x_reg5 Inflate3x_reg5 Inflate5x_reg5; do
  CFG_DIR="$BASE/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_${SUFFIX}"
  IN_HDF5="$CFG_DIR/ZMassDilepton.hdf5"
  OUT_DIR="$CFG_DIR/data_lrscan"
  mkdir -p "$OUT_DIR"
  echo "=== $(date) Running LR scan for $SUFFIX (kfactors: lambda_2=${KFAC_LAMBDA2[$SUFFIX]} lambda_4=${KFAC_LAMBDA4[$SUFFIX]} Lambda_2=${KFAC_BIG_LAMBDA2[$SUFFIX]} Delta_Lambda_2=${KFAC_DELTA_LAMBDA2[$SUFFIX]} Lambda_4=${KFAC_BIG_LAMBDA4[$SUFFIX]}) ==="
  python "$RABBIT" \
    "$IN_HDF5" \
    -m Project ch0 ptll \
    -t 0 \
    -o "$OUT_DIR" \
    --freezeParameters scetlibNPgammaLambdaInf \
    -r 'wremnants.postprocessing.np_monotonicity.NPMonotonicityWall' \
       'wremnants.postprocessing.np_monotonicity.NPMonotonicityMapping' \
       "b" \
       "lambda_2=${KFAC_LAMBDA2[$SUFFIX]}" \
       "lambda_4=${KFAC_LAMBDA4[$SUFFIX]}" \
       "Lambda_2=${KFAC_BIG_LAMBDA2[$SUFFIX]}" \
       "Delta_Lambda_2=${KFAC_DELTA_LAMBDA2[$SUFFIX]}" \
       "Lambda_4=${KFAC_BIG_LAMBDA4[$SUFFIX]}" \
    --regularizationStrength '5.0' \
    --scan pdfAlphaS --scanRange '2.5' --scanPoints 21
  echo "=== $(date) Done $SUFFIX -> $OUT_DIR/fitresults.hdf5 ==="
done

echo "DONE_OK $(date)"
