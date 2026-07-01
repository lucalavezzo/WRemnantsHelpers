#!/bin/bash
# Plot correlation matrices using rabbit_plot_cov.py for the
# nominal+reg and nominal+reg+fakelumi fits.
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

BASE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall
P=ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_
PLOT=/home/submit/lavezzo/alphaS/main/WRemnants/rabbit/bin/rabbit_plot_cov.py
CONFIG=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/260511_np_monotonicity_wall/scripts/plot_config.py

OUT="$MY_PLOT_DIR/260515_corr_matrices"
mkdir -p "$OUT"

# λ_∞ is frozen (no row/column in the cov) so omit it.
# fakelumi appears only in the fakelumi-enabled fit.
PARAMS_NOFL=(
  pdfAlphaS
  scetlibNPgammaLambda2
  scetlibNPgammaLambda4
  chargeVgenNP0scetlibNPZlambda2
  chargeVgenNP0scetlibNPZdelta_lambda2
  chargeVgenNP0scetlibNPZlambda4
)
PARAMS_FL=("${PARAMS_NOFL[@]}" fakelumi)

python "$PLOT" \
  "$BASE/${P}NPCS100pct/data_reg_satp/fitresults.hdf5" \
  -o "$OUT" -p nominal_reg \
  --params "${PARAMS_NOFL[@]}" \
  --config "$CONFIG" \
  --correlation --showNumbers \
  --customFigureWidth 11 --scaleTextSize 0.5 \
  --title "" --subtitle "" \
  --noEnergy

python "$PLOT" \
  "$BASE/${P}NPCS100pct_fakelumi/data_reg_satp/fitresults.hdf5" \
  -o "$OUT" -p nominal_reg_fakelumi \
  --params "${PARAMS_FL[@]}" \
  --config "$CONFIG" \
  --correlation --showNumbers \
  --customFigureWidth 11 --scaleTextSize 0.5 \
  --title "" --subtitle "" \
  --noEnergy

# Drop in the index.php for browsing
SRC=$MY_PLOT_DIR/260514_np_kernels/index.php
[ -f "$SRC" ] && cp "$SRC" "$OUT/index.php"

echo "DONE_OK $OUT"
