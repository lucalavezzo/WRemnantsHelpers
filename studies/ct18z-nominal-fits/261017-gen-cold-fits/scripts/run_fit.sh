#!/usr/bin/env bash
# Pass 1: the COLD main fit (no preconditioner: harmful from cold). trust-constr + hard NPDomainConstraints, no NP priors.
# usage: run_fit.sh GEN_NOLAT|GEN_LAT
set -f
PF=$1
source /home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/ct18z-nominal-fits/261017-gen-cold-fits/scripts/common.sh
cd /tmp; hdr
python3 $RB/bin/rabbit_fit.py $CARD --jitCompile off -o $OUT -t 0 --postfix $PF \
  $GEN $BLIND $CONSTR $(latargs $PF) --noHessian --noEDM \
  --snapshotFile $OUT/snapshot_fitresults_$PF.hdf5 --snapshotInterval 0.25 \
  $MODEL -v 4
rc=$?; echo "[run] $(date -Is) exit $rc"; exit $rc
