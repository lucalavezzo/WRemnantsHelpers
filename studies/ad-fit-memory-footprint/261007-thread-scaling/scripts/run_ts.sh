#!/usr/bin/env bash
# run_ts.sh <postfix>: runs ../cmds/<postfix>.cmd in the container (plain rabbit_fit.py), every output line
# prefixed with a unix timestamp, plus a passive /proc sampler on the python pid. Bulk log on ceph.
set -uo pipefail
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
T=$H/studies/ad-fit-memory-footprint/261007-thread-scaling
O=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261007_thread_scaling
W=$H/../WRemnants
PF=$1
CMD=$(cat "$T/cmds/$PF.cmd")
echo "[run] $(date -Is) postfix=$PF host=$(hostname) load=$(cat /proc/loadavg) WRemnants=$(git -C $W rev-parse --short HEAD) WRemnants_diff_md5=$(git -C $W diff -- wremnants | md5sum | cut -c1-32) rabbit=$(git -C $W/rabbit rev-parse --short HEAD) rabbit_diff_md5=$(git -C $W/rabbit diff | md5sum | cut -c1-32) scetlib=$(git -C $W/scetlib-cms rev-parse --short HEAD)"
echo "[run] cmd: $CMD"
export PYTHONUNBUFFERED=1
INNER=$O/$PF.inner.sh
# $$ survives the exec, so the sampler watches the python process itself; stdout goes through a timestamper
printf '%s\n' "echo \"[run] python pid \$\$ t0=\$(date +%s.%N)\"; echo \$\$ > $O/$PF.pid; bash $T/scripts/sample_proc.sh \$\$ $O/$PF.proc.csv 5 & exec > >(perl -MTime::HiRes=time -ne 'BEGIN{\$|=1} printf(\"%.2f %s\", time, \$_)') 2>&1; exec python3 $CMD" > "$INNER"
"$H/agent_setup.sh" --scetlib current -- bash "$INNER" 2>&1
rc=$?
echo "[run] $(date -Is) exit=$rc"
