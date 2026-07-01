#!/bin/bash
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

OUT="${MY_PLOT_DIR}/260514_lrscans"
mkdir -p "$OUT"

# Unconstrained τ=3
python /home/submit/lavezzo/alphaS/main/WRemnants/rabbit/bin/rabbit_plot_likelihood_scan.py \
  /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_NPUnconstrained/data_lrscan/fitresults.hdf5 \
  -o "$OUT" -p unconstrained_tau3 --params pdfAlphaS

# Unconstrained τ=5 for comparison
python /home/submit/lavezzo/alphaS/main/WRemnants/rabbit/bin/rabbit_plot_likelihood_scan.py \
  /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_NPUnconstrained/data_tau5_lrscan/fitresults.hdf5 \
  -o "$OUT" -p unconstrained_tau5 --params pdfAlphaS

echo "DONE_OK $OUT"
