#!/bin/bash
# Render the postfit-NP comparison table from the canonical fitresults
# files on disk, including the inflate*_reg5 rows once their kfactor-aware
# LR scans have landed at <CFG>/data_lrscan/. Missing files are skipped
# gracefully by build_compare_table.py (the row is dropped with a WARN).
set -e

B=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall
P=ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_

OUT="${MY_PLOT_DIR}/260513_np_compare"
SCRIPT=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/260511_np_monotonicity_wall/scripts/build_compare_table.py

# Label=path mapping (label order is the reference-row order; SECTIONS
# governs final grouping). nominal must be first — it's the αS reference.
python "$SCRIPT" \
  "nominal=$B/${P}NPCS100pct/fitresults.hdf5" \
  "nominal_fakelumi=$B/${P}NPCS100pct_fakelumi/data_satp/fitresults.hdf5" \
  "nominal_reg=$B/${P}NPCS100pct/data_reg_satp/fitresults.hdf5" \
  "nominal_fakelumi_reg=$B/${P}NPCS100pct_fakelumi/data_reg_satp/fitresults.hdf5" \
  "inflatedV2=$B/${P}NPCS100pctV2/fitresults.hdf5" \
  "inflatedV2_fakelumi=$B/${P}NPCS100pctV2_fakelumi/data_satp/fitresults.hdf5" \
  "inflatedV2_reg=$B/${P}NPCS100pctV2/data_reg_satp/fitresults.hdf5" \
  "inflatedV2_fakelumi_reg=$B/${P}NPCS100pctV2_fakelumi/data_reg_satp/fitresults.hdf5" \
  "frozenNP=$B/${P}NPCS100pct/data_frozenNP_satp/fitresults.hdf5" \
  "frozenNP_fakelumi=$B/${P}NPCS100pct_fakelumi/data_frozenNP_satp/fitresults.hdf5" \
  "tight50_reg=$B/${P}NPCS50pct/data_reg_satp/fitresults.hdf5" \
  "tight50_fakelumi_reg=$B/${P}NPCS50pct_fakelumi/data_reg_satp/fitresults.hdf5" \
  "nominal_2D_ptll_yll=$B/ZMassDilepton_ptll_yll_NPCS100pct_2D_ptll_yll/data_satp/fitresults.hdf5" \
  "nominal_2D_ptll_yll_fakelumi=$B/ZMassDilepton_ptll_yll_NPCS100pct_2D_ptll_yll_fakelumi/data_satp/fitresults.hdf5" \
  "inflate5x_2D_ptll_yll=$B/ZMassDilepton_ptll_yll_Inflate5x_2D_ptll_yll/data_satp/fitresults.hdf5" \
  "inflate5x_reg5_2D_ptll_yll=$B/ZMassDilepton_ptll_yll_Inflate5x_2D_ptll_yll/data_reg_satp/fitresults.hdf5" \
  "inflate5x_2D_ptll_yll_fakelumi=$B/ZMassDilepton_ptll_yll_Inflate5x_2D_ptll_yll_fakelumi/data_satp/fitresults.hdf5" \
  "inflate5x_reg5_2D_ptll_yll_fakelumi=$B/ZMassDilepton_ptll_yll_Inflate5x_2D_ptll_yll_fakelumi/data_reg_satp/fitresults.hdf5" \
  "NPCS100pct_asym=$B/${P}NPCS100pct_asym/data_satp/fitresults.hdf5" \
  "NPCS100pct_asym_fakelumi=$B/${P}NPCS100pct_asym_fakelumi/data_satp/fitresults.hdf5" \
  "inflate2x=$B/${P}Inflate2x/fitresults.hdf5" \
  "inflate2x_fakelumi=$B/${P}Inflate2x_fakelumi/fitresults.hdf5" \
  "inflate2x_reg5=$B/${P}Inflate2x_reg5/data_satp/fitresults.hdf5" \
  "inflate3x=$B/${P}Inflate3x/fitresults.hdf5" \
  "inflate3x_fakelumi=$B/${P}Inflate3x_fakelumi/fitresults.hdf5" \
  "inflate3x_reg5=$B/${P}Inflate3x_reg5/data_satp/fitresults.hdf5" \
  "inflate5x=$B/${P}Inflate5x/fitresults.hdf5" \
  "inflate5x_fakelumi=$B/${P}Inflate5x_fakelumi/fitresults.hdf5" \
  "inflate5x_reg5=$B/${P}Inflate5x_reg5/data_satp/fitresults.hdf5" \
  "inflate5x_reg5_fakelumi=$B/${P}Inflate5x_reg5_fakelumi/data_satp/fitresults.hdf5" \
  "unconstrained=$B/${P}NPUnconstrained/data_satp/fitresults.hdf5" \
  "unconstrained_fakelumi=$B/${P}NPUnconstrained_fakelumi/data_satp/fitresults.hdf5" \
  "unconstrained_tau5=$B/${P}NPUnconstrained/data_tau5_satp/fitresults.hdf5" \
  "unconstrained_tau5_fakelumi=$B/${P}NPUnconstrained_fakelumi/data_tau5_satp/fitresults.hdf5" \
  "unconstrained_asym_reg5=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260520_AN_unconstrained_asym_reg_realdata/${P}AN_unconstrained_asym_reg_realdata/fitresults.hdf5" \
  "unconstrained_asym_reg5_fakelumi=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260520_AN_unconstrained_asym_reg_fakelumi_realdata/${P}AN_unconstrained_asym_reg_fakelumi_realdata/fitresults.hdf5" \
  -o "$OUT"
echo "Wrote $OUT/np_compare.pdf"
