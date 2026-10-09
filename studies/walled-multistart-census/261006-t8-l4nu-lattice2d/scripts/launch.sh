#!/usr/bin/env bash
# launch.sh <PF>: gate through the shared mem_gate.sh (330 GB), log on ceph next to the fitresult, symlink the live log
# into the task logs/ AT LAUNCH. The gate runs detached (setsid) and logs to logs/<PF>.gate.
set -u
PF=$1
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/walled-multistart-census/261006-t8-l4nu-lattice2d
G=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/alphas-scan-discontinuity/scripts/mem_gate.sh
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261006_t8_l4nu_lattice2d
mkdir -p "$OUT" "$T/logs"
[ -e "$OUT/fitresults_$PF.hdf5" ] && { echo "refusing: $OUT/fitresults_$PF.hdf5 exists"; exit 2; }
[ -s "$OUT/$PF.log" ] && { echo "refusing: $OUT/$PF.log exists (already launched?)"; exit 2; }
touch "$OUT/$PF.log"
ln -sfn "$OUT/$PF.log" "$T/logs/$PF.log"
echo "$PF $(date -Is) queued-into-gate" >> "$T/logs/launches.txt"
setsid bash "$G" ${GATE_GB:-400} "$OUT/$PF.log" -- bash "$T/scripts/run_fit.sh" "$PF" >> "$T/logs/$PF.gate" 2>&1 < /dev/null &
echo "gate pid $!"
