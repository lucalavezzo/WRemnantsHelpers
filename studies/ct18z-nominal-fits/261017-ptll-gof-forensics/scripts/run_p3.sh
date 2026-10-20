#!/usr/bin/env bash
# P3: postfit-only rerun (no minimisation, no Hessian: the covariance is read from the external result) that saves the
# ptll postfit COVARIANCE and the ptll x signed-yll-band projection (+ yll), for the exact decomposition of the linear chi2.
# usage (through the gate): mem_gate.sh 260 $OUT/P3_<TAG>.log -- agent_setup.sh --scetlib <build> --prepend-pythonpath /work/submit/lavezzo/rabbit-all3 -- bash run_p3.sh <LAT|NOLAT>
set -f
TAG=$1
cd /tmp
RB=/work/submit/lavezzo/rabbit-all3
echo "[run] $(date -Is) $(hostname) rabbit worktree $RB @ $(git -C $RB rev-parse --short HEAD)"; python3 -c "import rabbit; print('[run] rabbit from', rabbit.__file__)"
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261018_ptll_gof_tests
CARD=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5
CACHE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_y35_260921_y25
if [ "$TAG" = LAT ]; then
  EXT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261016_face_held_impacts/fitresults_LAT_facefix.hdf5
  LATARGS="--regularizationStrength 8 -r wremnants.postprocessing.scetlib_ad.lattice_cs_term.LatticeCSTerm wremnants.postprocessing.scetlib_ad.lattice_cs_term.LatticeCSTermMapping"
else
  EXT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261016_nolat_postfit/fitresults_NOLAT_PF.hdf5
  LATARGS=""
fi
python3 $RB/bin/rabbit_fit.py $CARD --jitCompile off -o $OUT -t 0 --postfix P3_$TAG \
  --externalPostfit $EXT --noFit --saveHists --computeHistErrors --computeHistCov \
  -m Project ch0 ptll \
  -m Select ch0 'yll:rebin(-2.5,-1.5,-0.7,0,0.7,1.5,2.5)' \
  -m Project ch0 yll \
  $LATARGS \
  --constraints wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDomainConstraints margin=0 \
  --minimizerMethod trust-constr --earlyStopping -1 --maxRestarts 0 \
  --paramModel wremnants.postprocessing.scetlib_ad.SCETlibADParamModel \
  cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128 -v 4
echo "[run] $(date -Is) exit $?"
