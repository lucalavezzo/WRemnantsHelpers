#!/usr/bin/env bash
# P1: saturated projection tests on NESTED coarse ptll rebinnings (k = 3 c 6 c 10 piecewise-constant free shapes, flat in yll),
# from the existing minimum (--externalPostfit --noFit; covariance read, no Hessian). Each mapping runs its own warm,
# spectrally preconditioned saturated sub-fit. q39 is already known for the same M0 point (LAT 79.1071 SATWSPC; NOLAT 68.3635).
# usage (gate): mem_gate.sh 260 $OUT/P1_<TAG>.log -- agent_setup.sh --scetlib <build> --prepend-pythonpath /work/submit/lavezzo/rabbit-all3 -- bash run_p1.sh <LAT|NOLAT>
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
python3 $RB/bin/rabbit_fit.py $CARD --jitCompile off -o $OUT -t 0 --postfix P1_$TAG \
  --externalPostfit $EXT --noFit --saveHists --computeSaturatedProjectionTests \
  -m Select ch0 'ptll:rebin(0,5,15,44),yll:sum' \
  -m Select ch0 'ptll:rebin(0,2,5,10,15,22,44),yll:sum' \
  -m Select ch0 'ptll:rebin(0,1,2,3.5,5,7,10,12,15,22,44),yll:sum' \
  $LATARGS \
  --constraints wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDomainConstraints margin=0 \
  --minimizerMethod trust-constr --earlyStopping -1 --maxRestarts 0 --minimizerGtol 1e-8 \
  --minimizerXtol 1e-10 --minimizerBarrierTol 1e-9 --minimizerMaxiter 600 --minimizerWarmStart auto \
  --precondition --preconditionParams '.*' --preconditionBlocks none --preconditionTransform spectral \
  --snapshotFile $OUT/snapshot_fitresults_P1_$TAG.hdf5 --snapshotInterval 0.25 \
  --paramModel wremnants.postprocessing.scetlib_ad.SCETlibADParamModel \
  cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128 -v 4
echo "[run] $(date -Is) exit $?"
