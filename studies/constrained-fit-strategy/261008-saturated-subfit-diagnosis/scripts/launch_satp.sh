#!/usr/bin/env bash
set -u
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/constrained-fit-strategy/261008-saturated-subfit-diagnosis
G=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/alphas-scan-discontinuity/scripts/mem_gate.sh
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261008_saturated_subfit_diag
[ -e "$OUT/fitresults_SATP.hdf5" ] && { echo "refusing: fitresults_SATP exists"; exit 2; }
[ -s "$OUT/SATP.log" ] && { echo "refusing: $OUT/SATP.log exists"; exit 2; }
touch "$OUT/SATP.log"
ln -sfn "$OUT/SATP.log" "$T/logs/SATP.log"
echo "SATP $(date -Is) queued-into-gate" >> "$T/logs/launches.txt"
setsid bash "$G" 260 "$OUT/SATP.log" -- bash "$T/scripts/run_satp.sh" >> "$T/logs/SATP.gate" 2>&1 < /dev/null &
echo "gate pid $!"
