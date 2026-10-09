#!/usr/bin/env bash
# run_fit.sh <PF> [scetlib]: runs ../cmds/<PF>.cmd in the container (agent_setup.sh --scetlib <scetlib>, default
# current = in-tree 2dd978a, the build that ran NOMSTIFF/CENS03R), plain rabbit_fit.py, with a passive CPU/RSS sampler
# on the python pid (logs/<PF>.cpu.csv). Log: ceph out dir, symlinked as logs/<PF>.log.
set -uo pipefail
PF=$1; SC=${2:-current}
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
T=$H/studies/constrained-fit-strategy/261008-c2-wall-test
W=$H/../WRemnants
CMD=$(cat "$T/cmds/$PF.cmd")
echo "[run] $(date -Is) postfix=$PF host=$(hostname) WRemnants=$(git -C $W rev-parse --short HEAD) WRemnants_diff_md5=$(git -C $W diff -- wremnants | md5sum | cut -c1-32) wall_md5=$(md5sum $W/wremnants/postprocessing/scetlib_ad/np_damping_wall.py | cut -c1-32) rabbit=$(git -C $W/rabbit rev-parse --short HEAD) rabbit_diff_md5=$(git -C $W/rabbit diff | md5sum | cut -c1-32) scetlib_arg=$SC"
echo "[run] cmd: $CMD"
export PYTHONUNBUFFERED=1
INNER=$T/logs/$PF.inner.sh
LOG=$(readlink -f $T/logs/$PF.log)
printf '%s\n' "echo \"[run] python pid \$\$\"; echo \$\$ > $T/logs/$PF.pid; bash $T/scripts/sample_cpu.sh \$\$ $LOG $T/logs/$PF.cpu.csv 30 & exec python3 $CMD" > "$INNER"
"$H/agent_setup.sh" --scetlib "$SC" -- bash "$INNER" 2>&1
rc=$?
echo "[run] $(date -Is) exit=$rc"
