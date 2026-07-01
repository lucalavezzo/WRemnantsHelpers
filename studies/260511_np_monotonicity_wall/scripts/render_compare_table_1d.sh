#!/bin/bash
# Render the 1D ptll-only and yll-only comparison tables (sister to
# render_compare_table.sh). Output: $MY_PLOT_DIR/260514_np_compare_1d/.
set -e

B=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall
SCRIPT=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/260511_np_monotonicity_wall/scripts/build_compare_table_1d.py
OUT="${MY_PLOT_DIR}/260514_np_compare_1d"

python "$SCRIPT" \
  "ptll:nominal=$B/ZMassDilepton_ptll_NPCS100pct_ptllonly/data/fitresults.hdf5" \
  "ptll:unconstrained=$B/ZMassDilepton_ptll_NPUnconstrained_ptllonly/data/fitresults.hdf5" \
  "ptll:inflate5x_reg5=$B/ZMassDilepton_ptll_Inflate5x_reg5_ptllonly/data/fitresults.hdf5" \
  "yll:nominal=$B/ZMassDilepton_yll_NPCS100pct_yllonly/data/fitresults.hdf5" \
  "yll:unconstrained=$B/ZMassDilepton_yll_NPUnconstrained_yllonly/data/fitresults.hdf5" \
  "yll:inflate5x_reg5=$B/ZMassDilepton_yll_Inflate5x_reg5_yllonly/data/fitresults.hdf5" \
  -o "$OUT"

echo "Wrote $OUT/np_compare_1d.pdf"
