#!/usr/bin/env bash
# run_memnom.sh <PF> [threads]: runs ../cmds/<PF>.cmd (built by build_cmd.py from NOMSTIFF's meta_info command)
# under memprobe.py (in-process phase markers) in the container. Optional threads overrides threads= in the cmd.
set -uo pipefail
PF=$1; THR=${2:-}
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
T=$H/studies/ad-fit-memory-footprint/261006-memory-breakdown
W=$H/../WRemnants
CMD=$(cat "$T/cmds/MEMNOM.cmd")
[ -n "$THR" ] && CMD=$(echo "$CMD" | sed "s/ threads=128 / threads=$THR /; s/--postfix MEMNOM/--postfix $PF/")
echo "[run] $(date -Is) postfix=$PF host=$(hostname) WRemnants=$(git -C $W rev-parse --short HEAD) WRemnants_diff_md5=$(git -C $W diff -- wremnants | md5sum | cut -c1-32) rabbit=$(git -C $W/rabbit rev-parse --short HEAD) rabbit_diff_md5=$(git -C $W/rabbit diff | md5sum | cut -c1-32) scetlib=$(git -C $W/scetlib-cms rev-parse --short HEAD) memprobe_md5=$(md5sum $T/scripts/memprobe.py | cut -c1-32)"
echo "[run] cmd: $CMD"
export PYTHONUNBUFFERED=1
INNER=$T/logs/$PF.inner.sh
printf '%s\n' "python3 $T/scripts/memprobe.py $CMD" > "$INNER"
"$H/agent_setup.sh" --scetlib current -- bash "$INNER" 2>&1
rc=$?
echo "[run] $(date -Is) exit=$rc"
