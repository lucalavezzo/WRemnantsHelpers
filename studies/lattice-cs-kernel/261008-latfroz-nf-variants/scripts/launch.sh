#!/usr/bin/env bash
# launch.sh <PF>: gate through the shared mem_gate.sh (GATE_GB, default 260 for the |Y|<=2.5 subset cache), log on ceph
# next to the fitresult, symlink the live log into the task logs/ AT LAUNCH. The gate runs detached (setsid).
set -u
PF=$1
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/lattice-cs-kernel/261008-latfroz-nf-variants
G=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/alphas-scan-discontinuity/scripts/mem_gate.sh
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261008_latfroz_nf_variants
mkdir -p "$OUT" "$T/logs"
[ -e "$OUT/fitresults_$PF.hdf5" ] && { echo "refusing: $OUT/fitresults_$PF.hdf5 exists"; exit 2; }
[ -s "$OUT/$PF.log" ] && { echo "refusing: $OUT/$PF.log exists (already launched?)"; exit 2; }
touch "$OUT/$PF.log"
ln -sfn "$OUT/$PF.log" "$T/logs/$PF.log"
echo "$PF $(date -Is) queued-into-gate" >> "$T/logs/launches.txt"
setsid bash "$G" "${GATE_GB:-260}" "$OUT/$PF.log" -- bash "$T/scripts/run_fit.sh" "$PF" >> "$T/logs/$PF.gate" 2>&1 < /dev/null &
echo "gate pid $!"
