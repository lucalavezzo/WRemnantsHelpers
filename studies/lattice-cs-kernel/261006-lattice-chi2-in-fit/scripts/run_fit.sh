#!/usr/bin/env bash
# run_fit.sh <PF>: runs ../cmds/<PF>.cmd (built by build_cmds.py from NOMSTIFF's own meta_info command) in the container
# with this task's scripts/ (lattice_cs_chi2.py) prepended to PYTHONPATH. Main rabbit tree (as NOMSTIFF).
set -uo pipefail
PF=$1
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
T=$H/studies/lattice-cs-kernel/261006-lattice-chi2-in-fit
W=$H/../WRemnants
CMD=$(cat "$T/cmds/$PF.cmd")
grep -q "_parse_margin" "$W/wremnants/postprocessing/scetlib_ad/np_damping_wall.py" || { echo "margin keyword missing"; exit 2; }
echo "[run] $(date -Is) postfix=$PF host=$(hostname) WRemnants=$(git -C $W rev-parse --short HEAD) WRemnants_diff_md5=$(git -C $W diff -- wremnants | md5sum | cut -c1-32) rabbit=$(git -C $W/rabbit rev-parse --short HEAD) rabbit_diff_md5=$(git -C $W/rabbit diff | md5sum | cut -c1-32) scetlib=$(git -C $W/scetlib-cms rev-parse --short HEAD) plugin_md5(task copy)=$(md5sum $T/scripts/lattice_cs_chi2.py | cut -c1-32) wrem_plugin_md5=$(md5sum $W/wremnants/postprocessing/scetlib_ad/lattice_cs_chi2.py | cut -c1-32) wrem_inputs_md5=$(md5sum $W/wremnants/postprocessing/scetlib_ad/data/lattice_aswz_inputs.npz | cut -c1-32) inputs_md5=$(md5sum $T/lattice_aswz_inputs.npz | cut -c1-32)"
echo "[run] cmd: $CMD"
export PYTHONUNBUFFERED=1
INNER=$T/logs/$PF.inner.sh
case "$PF" in BLIND*) RUN="python3 $T/scripts/blindcheck.py $T/cmds/$PF.cmd" ;; *) RUN="python3 $CMD" ;; esac
printf '%s\n' 'python3 -c "import rabbit, lattice_cs_chi2; print(\"[run] rabbit from\", rabbit.__file__, \"plugin from\", lattice_cs_chi2.__file__)"' "$RUN" > "$INNER"
"$H/agent_setup.sh" --scetlib current --prepend-pythonpath "$T/scripts" -- bash "$INNER" 2>&1
rc=$?
echo "[run] $(date -Is) exit=$rc"
