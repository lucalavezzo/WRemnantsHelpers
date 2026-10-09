#!/usr/bin/env bash
# launch_diag.sh: gate HDIAG through the shared mem_gate.sh (260 GB, |Y|<=2.5 subset cache), log on ceph, live log
# symlinked into logs/ at launch. The gate runs detached (setsid).
set -u
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/constrained-fit-strategy/261008-saturated-subfit-diagnosis
G=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/alphas-scan-discontinuity/scripts/mem_gate.sh
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261008_saturated_subfit_diag
mkdir -p "$OUT" "$T/logs"
[ -s "$OUT/HDIAG.log" ] && { echo "refusing: $OUT/HDIAG.log exists (already launched?)"; exit 2; }
touch "$OUT/HDIAG.log"
ln -sfn "$OUT/HDIAG.log" "$T/logs/HDIAG.log"
echo "HDIAG $(date -Is) queued-into-gate" >> "$T/logs/launches.txt"
DONE_RE="x_s: loss|Traceback|Killed" setsid bash "$G" 260 "$OUT/HDIAG.log" -- bash "$T/scripts/run_diag.sh" >> "$T/logs/HDIAG.gate" 2>&1 < /dev/null &
echo "gate pid $!"
