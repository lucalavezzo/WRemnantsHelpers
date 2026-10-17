#!/usr/bin/env bash
# SATPC_NOLAT: the projected-ptll saturated sub-fit ONLY, preconditioned trust-constr (rabbit PR commit a606337,
# pinned worktree /work/submit/lavezzo/rabbit-tc-precond-val), started from NOLAT's final postfit (--externalPostfit
# --noFit). Same card / cache / SCETlib build / constraints / trust-constr tolerances as NOLAT (workflows/fitterAD.sh
# --constraints), plus the four full-scope spectral --precondition flags. Runs INSIDE the container (agent_setup.sh).
NOL=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261015_ct18z_nominal_fits
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261015_tc_precond_validation
CARD=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5
CACHE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_y35_260921_y25
RB=/work/submit/lavezzo/rabbit-tc-precond-val
export PYTHONPATH=$RB:$PYTHONPATH
RF=$(python -c 'import rabbit, os; print(os.path.dirname(os.path.dirname(rabbit.__file__)))')
[ "$RF" = "$RB" ] || { echo "[satpc] rabbit imports from $RF, not $RB: abort"; exit 1; }
echo "[satpc] $(date +%FT%T) rabbit=$(git -C $RB rev-parse --short HEAD) python rabbit from: $(python -c 'import rabbit; print(rabbit.__file__)')"
exec python $RB/bin/rabbit_fit.py "$CARD" --jitCompile off -o "$OUT" -t 0 \
  --postfix SATPC_NOLAT --externalPostfit "$NOL/fitresults_NOLAT.hdf5" --noFit --saveHists \
  --precondition --preconditionParams '.*' --preconditionBlocks none --preconditionTransform spectral \
  -m Project ch0 ptll --computeSaturatedProjectionTests \
  --constraints wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDomainConstraints margin=0 \
  --minimizerMethod trust-constr --earlyStopping -1 --maxRestarts 0 --minimizerGtol 1e-8 \
  --minimizerXtol 1e-10 --minimizerBarrierTol 1e-9 --minimizerMaxiter 600 \
  --snapshotFile "$OUT/snapshot_fitresults_SATPC_NOLAT.hdf5" --snapshotInterval 0.25 \
  --paramModel wremnants.postprocessing.scetlib_ad.SCETlibADParamModel \
  cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128 -v 4
