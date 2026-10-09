#!/usr/bin/env bash
# launch.sh <POSTFIX>: gate the cache load through the shared mem_gate.sh (330 GB peak), log WITH the fitresult on
# ceph, symlink the live log into the task dir logs/ AT LAUNCH (Luca's rule).
set -u
PF=$1
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/walled-multistart-census/261005-tmd-priors-free
G=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/alphas-scan-discontinuity/scripts/mem_gate.sh
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261005_tmd_priors_free
mkdir -p "$OUT" "$T/logs"
[ -e "$OUT/fitresults_$PF.hdf5" ] && { echo "refusing: $OUT/fitresults_$PF.hdf5 exists"; exit 2; }
[ -s "$OUT/$PF.log" ] && { echo "refusing: $OUT/$PF.log exists (already launched?)"; exit 2; }
touch "$OUT/$PF.log"
ln -sfn "$OUT/$PF.log" "$T/logs/$PF.log"
echo "$PF $(date -Is) queued-into-gate" >> "$T/logs/launches.txt"
bash "$G" 330 "$OUT/$PF.log" -- bash "$T/scripts/run_fit.sh" "$PF" >> "$T/logs/$PF.gate" 2>&1
