#!/usr/bin/env bash
# PROPOSED, NOT LAUNCHED: NOLAT's full postfit (Hessian + face-held cov, impacts, ptll saturated test) from its
# converged main-fit snapshot, with the C recipe (warm-start fix + spectral preconditioner, rabbit satdiag-ws-pc 0395383).
# The snapshot has no covariance, so rabbit recomputes the main Hessian at the loaded point (~8 min) -> face-held cov,
# --doImpacts skipped at an active face (global impacts run). --noFit: the main fit is not redone, so the
# preconditioner (fitter-wide flag) is built only for the saturated sub-fit, at its warm start.
# Launch (through the gate):  MAXRUN=2 mem_gate.sh 260 $OUT/NOLAT_PF.log -- agent_setup.sh --scetlib $SC -- bash <this file>
set -f
cd /tmp
RB=/work/submit/lavezzo/rabbit-satdiag-wspc
export PYTHONPATH=$RB:${PYTHONPATH:-}
NOL=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261015_ct18z_nominal_fits
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261016_saturated_subfit_diagnosis
CARD=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5
CACHE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_y35_260921_y25
python3 $RB/bin/rabbit_fit.py $CARD --jitCompile off -o $OUT -t 0 --postfix NOLAT_PF \
  --externalPostfit $NOL/snapshot_fitresults_NOLAT.hdf5 --noFit \
  -m Project ch0 ptll --computeSaturatedProjectionTests --computeHistErrors \
  --doImpacts --globalImpacts --globalImpactsDisableJVP --saveHists \
  --constraints wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDomainConstraints margin=0 \
  --minimizerMethod trust-constr --earlyStopping -1 --maxRestarts 0 --minimizerGtol 1e-8 \
  --minimizerXtol 1e-10 --minimizerBarrierTol 1e-9 --minimizerMaxiter 600 \
  --precondition --preconditionParams '.*' --preconditionBlocks none --preconditionTransform spectral \
  --snapshotFile $OUT/snapshot_fitresults_NOLAT_PF.hdf5 --snapshotInterval 0.25 \
  --paramModel wremnants.postprocessing.scetlib_ad.SCETlibADParamModel \
  cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128 -v 4
