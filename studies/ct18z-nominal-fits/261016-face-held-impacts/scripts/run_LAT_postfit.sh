#!/bin/bash
# LAT postfit only (no fit, no saturated test) with the face-held-impacts rabbit branch.
# Same card / cache / model / constraints / lattice as LAT (261015-cold-tc-fits, LAT.log line 3);
# --externalPostfit is an x-only copy of fitresults_LAT.hdf5 (identical to snapshot_fitresults_LAT.hdf5),
# so the Hessian, the face-held covariance and the impacts are recomputed at LAT's minimum.
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261016_face_held_impacts
CACHE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_y35_260921_y25
exec /home/submit/lavezzo/alphaS/WRemnantsHelpers/agent_setup.sh \
  --scetlib /work/submit/lavezzo/alphaS/scetlib-gamma-nu-points/scetlib-cms/build \
  --prepend-pythonpath /work/submit/lavezzo/rabbit-face-impacts -- \
  python /work/submit/lavezzo/rabbit-face-impacts/bin/rabbit_fit.py \
  /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5 \
  --jitCompile off -o $OUT -t 0 --postfix LAT_facefix \
  --externalPostfit $OUT/LAT_x_only.hdf5 --noFit \
  -m Project ch0 ptll --computeHistErrors --doImpacts --globalImpacts --globalImpactsDisableJVP --saveHists \
  --regularizationStrength 8 \
  -r wremnants.postprocessing.scetlib_ad.lattice_cs_term.LatticeCSTerm wremnants.postprocessing.scetlib_ad.lattice_cs_term.LatticeCSTermMapping \
  --constraints wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDomainConstraints margin=0 \
  --minimizerMethod trust-constr --earlyStopping -1 --maxRestarts 0 --minimizerGtol 1e-8 --minimizerXtol 1e-10 \
  --minimizerBarrierTol 1e-9 --minimizerMaxiter 600 \
  --paramModel wremnants.postprocessing.scetlib_ad.SCETlibADParamModel cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128 \
  -v 4
