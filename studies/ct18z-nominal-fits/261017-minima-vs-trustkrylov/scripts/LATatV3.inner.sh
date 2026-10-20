#!/usr/bin/env bash
# LAT's objective (lattice + hard NPDomainConstraints, no NP priors), warm from LATFROZ_V3's minimum.
# Cross-evaluation: the logged 'trust-constr start loss' = the NEW objective at the OLD minimum (same card -> same 3720
# parameter names, read by --externalPostfit). Then a warm trust-constr refit (rabbit all3-local: warm start +
# spectral preconditioner) to see whether it returns to the new minimum. Args = the LAT/NOLAT launch (fitterAD.sh
# --constraints [--lattice], 261015-cold-tc-fits/logs/launches.txt) minus the postfit extras, plus --noHessian --noEDM.
# Launch: mem_gate.sh 260 $OUT/LATatV3.log -- agent_setup.sh --scetlib <gamma-nu build> -- bash <this file>
# Seed = the old fit's converged snapshot (x only, == its fitresult parms bit for bit; a seed carrying a cov is refused under --noHessian).
set -f
cd /tmp
RB=/work/submit/lavezzo/rabbit-all3
export PYTHONPATH=$RB:${PYTHONPATH:-}
echo "[run] $(date -Is) rabbit worktree $RB @ $(git -C $RB rev-parse --short HEAD); WRemnants $(git -C $WREM_BASE rev-parse --short HEAD)"; python3 -c "import rabbit; print('[run] rabbit from', rabbit.__file__)"
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261017_minima_vs_trustkrylov
CARD=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5
CACHE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_y35_260921_y25
python3 $RB/bin/rabbit_fit.py $CARD --jitCompile off -o $OUT -t 0 --postfix LATatV3 \
  --externalPostfit /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261008_latfroz_nf_variants/snapshot_fitresults_LATFROZ_V3.hdf5 \
  --regularizationStrength 8 -r wremnants.postprocessing.scetlib_ad.lattice_cs_term.LatticeCSTerm wremnants.postprocessing.scetlib_ad.lattice_cs_term.LatticeCSTermMapping \
  --constraints wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDomainConstraints margin=0 \
  --minimizerMethod trust-constr --earlyStopping -1 --maxRestarts 0 --minimizerGtol 1e-8 \
  --minimizerXtol 1e-10 --minimizerBarrierTol 1e-9 --minimizerMaxiter 600 --minimizerWarmStart auto \
  --precondition --preconditionParams '.*' --preconditionBlocks none --preconditionTransform spectral \
  --noHessian --noEDM \
  --snapshotFile $OUT/snapshot_fitresults_LATatV3.hdf5 --snapshotInterval 0.25 \
  --paramModel wremnants.postprocessing.scetlib_ad.SCETlibADParamModel \
  cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128 -v 4
echo "[run] $(date -Is) exit $?"
