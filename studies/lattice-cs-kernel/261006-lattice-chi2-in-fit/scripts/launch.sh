#!/usr/bin/env bash
# launch.sh <PF>: gate through the shared mem_gate.sh (400 GB; was 330 until 2026-10-06 12:40, raised after the node OOM-killed three fits 12:05-12:23), log on ceph next to the fitresult, symlink the live log
# into the task logs/ AT LAUNCH. GATE_GB overrides the 400 GB (260 for the |Y|<=2.5 subset cache, 2026-10-07). The gate runs detached (setsid) and logs to logs/<PF>.gate.
set -u
PF=$1
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/lattice-cs-kernel/261006-lattice-chi2-in-fit
G=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/alphas-scan-discontinuity/scripts/mem_gate.sh
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261006_lattice_chi2_in_fit
mkdir -p "$OUT" "$T/logs"
[ -e "$OUT/fitresults_$PF.hdf5" ] && { echo "refusing: $OUT/fitresults_$PF.hdf5 exists"; exit 2; }
[ -s "$OUT/$PF.log" ] && { echo "refusing: $OUT/$PF.log exists (already launched?)"; exit 2; }
# at most ONE cache load of this task at a time: refuse while any rabbit_fit (or blindcheck) of this task is alive
pgrep -f "^python3 .*(rabbit_fit.py .*261006_lattice_chi2_in_fit|261006-lattice-chi2-in-fit/scripts/blindcheck.py)" >/dev/null && { echo "refusing: a fit/check of this task is still running"; exit 2; }
touch "$OUT/$PF.log"
ln -sfn "$OUT/$PF.log" "$T/logs/$PF.log"
echo "$PF $(date -Is) queued-into-gate" >> "$T/logs/launches.txt"
setsid bash "$G" "${GATE_GB:-400}" "$OUT/$PF.log" -- bash "$T/scripts/run_fit.sh" "$PF" >> "$T/logs/$PF.gate" 2>&1 < /dev/null &
echo "gate pid $!"
