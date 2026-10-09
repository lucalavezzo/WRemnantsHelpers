#!/usr/bin/env bash
# launch.sh <PF> [scetlib] [peak_GB=260]: queue <PF> into the shared mem_gate (max 2 gated jobs alive), detached.
set -u
PF=$1; SC=${2:-current}; PEAK=${3:-260}
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/constrained-fit-strategy/261008-c2-wall-test
O=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261008_c2_wall_test
G=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/alphas-scan-discontinuity/scripts/mem_gate.sh
mkdir -p $O; touch $O/$PF.log; ln -sfn $O/$PF.log $T/logs/$PF.log
echo "$PF $(date -Is) queued-into-gate peak=$PEAK scetlib=$SC" >> $T/logs/launches.txt
setsid nohup bash $G $PEAK $O/$PF.log -- bash $T/scripts/run_fit.sh $PF $SC > $T/logs/$PF.gate 2>&1 < /dev/null &
echo "gate pid $!"
