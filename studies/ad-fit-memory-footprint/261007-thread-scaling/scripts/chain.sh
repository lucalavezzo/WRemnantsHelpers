#!/usr/bin/env bash
# chain.sh <postfix>...: one job at a time through the shared mem_gate (peak 260 GB, MAXRUN=2). Each gate call
# returns when its job logs "Iteration 0:"; we then wait for the job's PID to exit before the next one.
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/ad-fit-memory-footprint/261007-thread-scaling
O=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261007_thread_scaling
G=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/alphas-scan-discontinuity/scripts/mem_gate.sh
for PF in "$@"; do
  [ -f $O/STOP ] && { echo "[chain] $(date -Is) STOP file, stopping before $PF"; break; }
  ln -sf $O/$PF.log $T/logs/$PF.log; ln -sf $O/$PF.proc.csv $T/logs/$PF.proc.csv
  echo "[chain] $(date -Is) gating $PF"
  bash $G 260 $O/$PF.log -- bash $T/scripts/run_ts.sh $PF > $T/logs/$PF.gate.log 2>&1
  pid=$(awk '/\[mem_gate\] pid/{print $3}' $T/logs/$PF.gate.log)
  echo "[chain] $(date -Is) $PF gate pid $pid; waiting for exit"
  while kill -0 $pid 2>/dev/null; do sleep 15; done
  echo "[chain] $(date -Is) $PF done: $(tail -1 $O/$PF.log)"
done
