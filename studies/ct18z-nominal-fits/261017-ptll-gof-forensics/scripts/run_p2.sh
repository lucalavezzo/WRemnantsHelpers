#!/usr/bin/env bash
# P2: warm refit of LAT with a prior-inflated card (setupRabbit --scaleParams / --lumiUncertainty; P2 cards in $OUT/cards)
# and, for the FO scale envelope (a ParamModel parameter), the model's prior_sigmas token. Warm start from LAT's minimum
# (--externalPostfit, minimizer warm start auto) with the full-scope spectral preconditioner; then the postfit Hessian
# (face-held cov), the full saturated GoF and the ptll saturated-projection sub-fit.
# usage (gate): mem_gate.sh 260 $OUT/P2_<V>_LAT.log -- agent_setup.sh --scetlib <build> --prepend-pythonpath /work/submit/lavezzo/rabbit-all3 -- bash run_p2.sh <V> [modelArgs-extra]
set -f
V=$1; MEXTRA=${2:-}
cd /tmp
RB=/work/submit/lavezzo/rabbit-all3
echo "[run] $(date -Is) $(hostname) rabbit worktree $RB @ $(git -C $RB rev-parse --short HEAD) variant $V model-extra '$MEXTRA'"; python3 -c "import rabbit; print('[run] rabbit from', rabbit.__file__)"
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261018_ptll_gof_tests
CARD=$OUT/cards/ZMassDilepton_ptll_yll_adexclpdf_$V/ZMassDilepton.hdf5
CACHE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_y35_260921_y25
EXT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261016_face_held_impacts/fitresults_LAT_facefix.hdf5
ls -la $CARD || exit 2
python3 $RB/bin/rabbit_fit.py $CARD --jitCompile off -o $OUT -t 0 --postfix P2_${V}_LAT \
  --externalPostfit $EXT --saveHists --computeHistErrors \
  -m Project ch0 ptll --computeSaturatedProjectionTests \
  --regularizationStrength 8 -r wremnants.postprocessing.scetlib_ad.lattice_cs_term.LatticeCSTerm wremnants.postprocessing.scetlib_ad.lattice_cs_term.LatticeCSTermMapping \
  --constraints wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDomainConstraints margin=0 \
  --minimizerMethod trust-constr --earlyStopping -1 --maxRestarts 0 --minimizerGtol 1e-5 \
  --minimizerXtol 1e-10 --minimizerBarrierTol 1e-9 --minimizerMaxiter 600 --minimizerWarmStart auto \
  --precondition --preconditionParams '.*' --preconditionBlocks none --preconditionTransform spectral \
  --snapshotFile $OUT/snapshot_fitresults_P2_${V}_LAT.hdf5 --snapshotInterval 0.25 \
  --paramModel wremnants.postprocessing.scetlib_ad.SCETlibADParamModel \
  cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128 $MEXTRA -v 4
echo "[run] $(date -Is) exit $?"
