#!/bin/bash
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1
export HDF5_USE_FILE_LOCKING=FALSE

echo "[$(date +%H:%M:%S)] waiting for setupRabbit PID 3633387..."
while kill -0 3633387 2>/dev/null; do sleep 60; done
echo "[$(date +%H:%M:%S)] setupRabbit done"

if [ ! -f "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS//260526_fit_NewVarsCT18ZLambda6_lambda4neg//ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_NewVarsCT18ZLambda6_v4_lambda4neg/ZMassDilepton.hdf5" ]; then echo "ERROR: carrot missing at /ceph/submit/data/group/cms/store/user/lavezzo/alphaS//260526_fit_NewVarsCT18ZLambda6_lambda4neg//ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_NewVarsCT18ZLambda6_v4_lambda4neg/ZMassDilepton.hdf5"; ls /ceph/submit/data/group/cms/store/user/lavezzo/alphaS//260526_fit_NewVarsCT18ZLambda6_lambda4neg//ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_NewVarsCT18ZLambda6_v4_lambda4neg; exit 1; fi

echo "[$(date +%H:%M:%S)] launching rabbit_fit -t 0"
rabbit_fit.py "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS//260526_fit_NewVarsCT18ZLambda6_lambda4neg//ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_NewVarsCT18ZLambda6_v4_lambda4neg/ZMassDilepton.hdf5" -t 0 --computeVariations -m Project ch0 ptll --computeHistErrors --computeHistImpacts --doImpacts -o "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS//260526_fit_NewVarsCT18ZLambda6_lambda4neg//ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_NewVarsCT18ZLambda6_v4_lambda4neg" --globalImpacts --saveHists --saveHistsPerProcess > /home/submit/lavezzo/alphaS/WRemnantsHelpers/logs/rabbit_fit_lambda4neg_realdata_260526_144335.log 2>&1
echo "[$(date +%H:%M:%S)] rabbit_fit done"

FITRES=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS//260526_fit_NewVarsCT18ZLambda6_lambda4neg//ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_NewVarsCT18ZLambda6_v4_lambda4neg/fitresults.hdf5
if [ ! -f "$FITRES" ]; then echo "ERROR: fitresults missing"; exit 1; fi

echo "[$(date +%H:%M:%S)] rendering tables (augmented w/ fixed params)"
NEW_TBL=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/ct18z-3p0-newvals-tanh6-lambda6scan/scripts/build_table_lambda4neg.py
python "$NEW_TBL" "nominal=$FITRES" --mode physical -o "/home/submit/lavezzo/public_html/alphaS//260526_NewVarsCT18ZLambda6_v4_lambda4neg_table/"
python "$NEW_TBL" "nominal=$FITRES" --mode theta    -o "/home/submit/lavezzo/public_html/alphaS//260526_NewVarsCT18ZLambda6_v4_lambda4neg_table/"
