#!/usr/bin/env bash
# launch.sh <POSTFIX> : gate the cache load through mem_gate.sh (330 GB peak, fast-path loader), log with the fitresult,
# symlink into the task dir's logs/.
set -u
PF=$1
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/walled-multistart-census/260930-stiff-wall-refits
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260930_stiff_wall_fits
mkdir -p "$OUT" "$T/logs"
[ -e "$OUT/fitresults_$PF.hdf5" ] && { echo "refusing: $OUT/fitresults_$PF.hdf5 exists"; exit 2; }
ln -sfn "$OUT/$PF.log" "$T/logs/$PF.log"
bash "$T/scripts/mem_gate.sh" 330 "$OUT/$PF.log" -- bash "$T/scripts/run_fit.sh" "$PF" >> "$T/logs/$PF.gate" 2>&1
