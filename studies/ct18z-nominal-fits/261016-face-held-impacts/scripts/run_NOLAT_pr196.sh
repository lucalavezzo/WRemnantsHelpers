#!/bin/bash
# PR #196 validation on NOLAT (two active faces: lambda2_nu >= 0 bound + the curved TMD large-b cubic at |Y|=2.5).
#   held   : NOLAT postfit (Hessian, face-held cov, impacts) with the PR branch, at NOLAT's minimum
#   frozen : the same, with lambda2_nu FROZEN (--freezeParameters) at the same point. Holding the bound face must
#            equal freezing lambda2_nu: impacts identical (the cubic face is held in both).
# Same card / cache / model / constraints as NOLAT (no lattice). No fit, no saturated test.
# usage: run_NOLAT_pr196.sh held|frozen
set -f
MODE=$1
RB=/work/submit/lavezzo/rabbit-face-impacts
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261017_pr_validation
NOL=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261015_ct18z_nominal_fits
CARD=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5
CACHE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_y35_260921_y25
EXTRA=""; [ "$MODE" = frozen ] && EXTRA="--freezeParameters lambda2_nu"
echo "[run] $(date -Is) mode $MODE, rabbit $RB @ $(git -C $RB rev-parse --short HEAD)"
exec /home/submit/lavezzo/alphaS/WRemnantsHelpers/agent_setup.sh \
  --scetlib /work/submit/lavezzo/alphaS/scetlib-gamma-nu-points/scetlib-cms/build --prepend-pythonpath $RB -- \
  python $RB/bin/rabbit_fit.py $CARD --jitCompile off -o $OUT -t 0 --postfix PR196_NOLAT_$MODE \
  --externalPostfit $NOL/snapshot_fitresults_NOLAT.hdf5 --noFit $EXTRA \
  --doImpacts --globalImpacts --globalImpactsDisableJVP \
  --constraints wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDomainConstraints margin=0 \
  --minimizerMethod trust-constr --earlyStopping -1 --maxRestarts 0 --minimizerGtol 1e-8 \
  --minimizerXtol 1e-10 --minimizerBarrierTol 1e-9 --minimizerMaxiter 600 \
  --paramModel wremnants.postprocessing.scetlib_ad.SCETlibADParamModel \
  cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128 -v 4
