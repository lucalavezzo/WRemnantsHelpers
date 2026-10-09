#!/usr/bin/env bash
# run_suby25.sh: runs ../cmds/SUBY25.cmd (NOMSTIFF's own command on the |Y|<=2.5 subset cache, --noFit) in the
# container, plain rabbit_fit.py (no instrumentation), with a passive /proc/<pid>/status sampler on the python pid.
set -uo pipefail
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
T=$H/studies/ad-fit-memory-footprint/261006-subset-cache-y25
W=$H/../WRemnants
PF=SUBY25
CMD=$(cat "$T/cmds/$PF.cmd")
echo "[run] $(date -Is) postfix=$PF host=$(hostname) WRemnants=$(git -C $W rev-parse --short HEAD) WRemnants_diff_md5=$(git -C $W diff -- wremnants | md5sum | cut -c1-32) rabbit=$(git -C $W/rabbit rev-parse --short HEAD) rabbit_diff_md5=$(git -C $W/rabbit diff | md5sum | cut -c1-32) scetlib=$(git -C $W/scetlib-cms rev-parse --short HEAD)"
echo "[run] cmd: $CMD"
export PYTHONUNBUFFERED=1
INNER=$T/logs/$PF.inner.sh
# $$ survives the exec, so the sampler watches the python process itself
printf '%s\n' "echo \"[run] python pid \$\$\"; echo \$\$ > $T/logs/$PF.pid; bash $T/scripts/sample_mem.sh \$\$ $T/logs/$PF.mem 10 0 & exec python3 $CMD" > "$INNER"
"$H/agent_setup.sh" --scetlib current -- bash "$INNER" 2>&1
rc=$?
echo "[run] $(date -Is) exit=$rc"
