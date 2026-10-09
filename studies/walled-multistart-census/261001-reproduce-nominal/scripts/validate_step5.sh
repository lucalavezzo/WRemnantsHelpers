#!/bin/bash
# PENDING-RUN validation of REPRODUCE.md step 5 (two cache loads, run one after the other, NO fit).
# Evaluates the step-5 fitter (scripts/step5_fit.sh + --noFit --noEDM) at two stored vectors.
# NOT --noHessian: with it rabbit allocates no covariance and load_fitresult REFUSES a seed that carries one.
#   VALNOM : NOMSTIFF's own postfit vector  -> nllvalreduced must equal 376.6146329237086
#   VALIT0 : NOMSTIFF's seed (LATL4ZY35WALLWARM postfit) -> must equal NOMSTIFF's "Iteration 0: loss"
#            376.69103432608273 (the margin-0 wall is slack there, so it is also the unwalled loss)
# Each load is gated through the shared mem_gate (peak ~310 GB via the extracted-rules fast path,
# steady ~327 GB) so it never collides with another big load. Outputs on ceph, logs symlinked here.
#   usage: validate_step5.sh            (from anywhere; detaches itself is NOT done -- run under setsid/nohup)
set -u
T=$(cd "$(dirname "$0")/.." && pwd)
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
GATE=$H/studies/alphas-scan-discontinuity/scripts/mem_gate.sh
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261001_reproduce_validation
NOM=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5
SEED=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260928_lattice_y35_fits/fitresults_LATL4ZY35WALLWARM.hdf5
mkdir -p $OUT $T/logs
for job in "VALNOM $NOM" "VALIT0 $SEED"; do
  set -- $job; PF=$1; X=$2; LOG=$OUT/$PF.log
  ln -sfn $LOG $T/logs/$PF.log
  echo "[validate] $(date -Is) $PF at $X" | tee -a $LOG
  # mem_gate returns once the load is done; then wait for the process to finish before the next load
  DONE_RE="cache loaded|Traceback|Killed" $GATE 330 $LOG -- \
    "$H/agent_setup.sh --scetlib current -- $T/scripts/step5_fit.sh $OUT $PF $X --noFit --noEDM; echo \"[validate] exit=\$? \$(date -Is)\""
  until grep -q "^\[validate\] exit=" $LOG; do sleep 30; done
done
$H/agent_setup.sh -- python3 $T/scripts/compare_validation.py $OUT 2>&1 | grep -v "^I0000\|^E0000" | tee $T/logs/compare_validation.log
