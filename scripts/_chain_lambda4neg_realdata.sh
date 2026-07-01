#!/bin/bash
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1
export HDF5_USE_FILE_LOCKING=FALSE
echo "[$(date +%H:%M:%S)] waiting for setupRabbit PID 3820984..."
while kill -0 3820984 2>/dev/null; do sleep 60; done
echo "[$(date +%H:%M:%S)] setupRabbit done"
if [ ! -f "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS//260526_fit_NewVarsCT18ZLambda6_lambda4neg_realdata//ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_NewVarsCT18ZLambda6_v4_lambda4neg_realdata/ZMassDilepton.hdf5" ]; then echo "ERROR: carrot missing"; ls /ceph/submit/data/group/cms/store/user/lavezzo/alphaS//260526_fit_NewVarsCT18ZLambda6_lambda4neg_realdata//ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_NewVarsCT18ZLambda6_v4_lambda4neg_realdata; exit 1; fi
echo "[$(date +%H:%M:%S)] launching rabbit_fit -t 0 (REAL DATA, carrot has --realData)"
rabbit_fit.py "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS//260526_fit_NewVarsCT18ZLambda6_lambda4neg_realdata//ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_NewVarsCT18ZLambda6_v4_lambda4neg_realdata/ZMassDilepton.hdf5" -t 0 --computeVariations -m Project ch0 ptll --computeHistErrors --computeHistImpacts --doImpacts -o "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS//260526_fit_NewVarsCT18ZLambda6_lambda4neg_realdata//ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_NewVarsCT18ZLambda6_v4_lambda4neg_realdata" --globalImpacts --saveHists --saveHistsPerProcess > /home/submit/lavezzo/alphaS/WRemnantsHelpers/logs/rabbit_fit_lambda4neg_realdata2_260526_145842.log 2>&1
echo "[$(date +%H:%M:%S)] rabbit_fit done"
FITRES=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS//260526_fit_NewVarsCT18ZLambda6_lambda4neg_realdata//ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_NewVarsCT18ZLambda6_v4_lambda4neg_realdata/fitresults.hdf5
if [ ! -f "$FITRES" ]; then echo "ERROR: fitresults missing"; exit 1; fi
echo "[$(date +%H:%M:%S)] rendering augmented table"
python "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/ct18z-3p0-newvals-tanh6-lambda6scan/scripts/build_table_lambda4neg.py" "realdata=$FITRES" --mode physical -o "/home/submit/lavezzo/public_html/alphaS/260526_NewVarsCT18ZLambda6_v4_lambda4neg_realdata_table/"
python "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/ct18z-3p0-newvals-tanh6-lambda6scan/scripts/build_table_lambda4neg.py" "realdata=$FITRES" --mode theta    -o "/home/submit/lavezzo/public_html/alphaS/260526_NewVarsCT18ZLambda6_v4_lambda4neg_realdata_table/"
echo "[$(date +%H:%M:%S)] CHAIN COMPLETE"
