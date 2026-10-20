#!/usr/bin/env bash
# Pass 2: full postfit from the pass-1 minimum (--externalPostfit --noFit): face-held Hessian/cov, traditional (face-held)
# + global impacts, hists, ptVGen and absYVGen saturated projections. Warm start + full-scope spectral preconditioner
# (warm legs only: the saturated sub-fits).
# usage: run_pf.sh GEN_NOLAT|GEN_LAT
set -f
PF=$1
source /home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/ct18z-nominal-fits/261017-gen-cold-fits/scripts/common.sh
cd /tmp; hdr
python3 $RB/bin/rabbit_fit.py $CARD --jitCompile off -o $OUT -t 0 --postfix ${PF}_PF \
  --externalPostfit $OUT/fitresults_$PF.hdf5 --noFit \
  $GEN $BLIND $CONSTR $(latargs $PF) --minimizerWarmStart auto \
  --precondition --preconditionParams '.*' --preconditionBlocks none --preconditionTransform spectral \
  --saveHists --computeHistErrors -m BaseMapping -m Project chSigmaUL ptVGen -m Project chSigmaUL absYVGen \
  --computeSaturatedProjectionTests --doImpacts --globalImpacts --globalImpactsDisableJVP \
  --snapshotFile $OUT/snapshot_fitresults_${PF}_PF.hdf5 --snapshotInterval 0.25 \
  $MODEL -v 4
rc=$?; echo "[run] $(date -Is) exit $rc"; exit $rc
