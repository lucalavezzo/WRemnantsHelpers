#!/usr/bin/env bash
set -eo pipefail
source /home/submit/lavezzo/alphaS/WRemnantsHelpers/setup.sh >/tmp/wrh_setup_impacts_extract.log 2>&1
FIT=/scratch/submit/cms/alphaS/260213_histmaker_dilepton/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_codex/fitresults.hdf5
echo traditional_scaled
python /home/submit/lavezzo/alphaS/gh/WRemnants/rabbit/bin/rabbit_print_impacts.py "$FIT" --scale 2.0 | awk '/Total:/{print; exit}'
echo global_scaled
python /home/submit/lavezzo/alphaS/gh/WRemnants/rabbit/bin/rabbit_print_impacts.py "$FIT" --globalImpacts --scale 2.0 | awk '/Total:/{print; exit}'
