#!/usr/bin/env bash
# launch.sh NAME : queue cmds/NAME.inner.sh through the shared mem_gate (260 GB, MAXRUN=3 = NOLAT + 2 of ours)
set -u
NAME=$1
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/ct18z-nominal-fits/261016-saturated-subfit-diagnosis
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261016_saturated_subfit_diagnosis
G=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/alphas-scan-discontinuity/scripts/mem_gate.sh
SC=/work/submit/lavezzo/alphaS/scetlib-gamma-nu-points/scetlib-cms/build
[ -e "$OUT/fitresults_$NAME.hdf5" ] && { echo "refusing: fitresults_$NAME exists"; exit 2; }
[ -s "$OUT/$NAME.log" ] && { echo "refusing: $OUT/$NAME.log exists"; exit 2; }
touch "$OUT/$NAME.log"
ln -sfn "$OUT/$NAME.log" "$T/logs/$NAME.log"
ln -sfn "$OUT/$NAME.gate" "$T/logs/$NAME.gate"
cp "$T/cmds/$NAME.inner.sh" "$OUT/$NAME.inner.sh"
echo "$NAME $(date -Is) helpers_md5=$(md5sum < $T/cmds/$NAME.inner.sh | cut -c1-12) :: MAXRUN=${MAXRUN:-3} mem_gate.sh 260 $OUT/$NAME.log -- agent_setup.sh --scetlib $SC -- bash $OUT/$NAME.inner.sh" >> "$T/logs/launches.txt"
MAXRUN=${MAXRUN:-3} setsid bash "$G" 260 "$OUT/$NAME.log" -- /home/submit/lavezzo/alphaS/WRemnantsHelpers/agent_setup.sh --scetlib $SC -- bash $OUT/$NAME.inner.sh >> "$OUT/$NAME.gate" 2>&1 < /dev/null &
echo "gate pid $!"
