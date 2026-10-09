#!/usr/bin/env bash
# T6 profile fit runner: run_fit.sh PROF<pt><start>. Runs cmds/<pf>.cmd (built by build_cmds.py from NOMSTIFF's own
# meta_info command). stdout -> the gate log = $OUT/<pf>.log (log lives with the fitresult). Copied from the census.
set -uo pipefail
PF=$1
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
T=$H/studies/walled-multistart-census/261002-multistart-profile
W=$H/../WRemnants
CMD=$(cat "$T/cmds/$PF.cmd")
grep -q "if not vv.any():" "$W/scetlib-cms/py/scetlib_tf.py" || { echo "hvp zero-seed skip missing"; exit 2; }
grep -q "_parse_margin" "$W/wremnants/postprocessing/scetlib_ad/np_damping_wall.py" || { echo "margin keyword missing"; exit 2; }
echo "[run] $(date -Is) postfix=$PF host=$(hostname) WRemnants=$(git -C $W rev-parse --short HEAD) rabbit=$(git -C $W/rabbit rev-parse --short HEAD) scetlib=$(git -C $W/scetlib-cms rev-parse --short HEAD) wall_diff_md5=$(git -C $W diff -- wremnants/postprocessing/scetlib_ad/np_damping_wall.py | md5sum | cut -c1-32) wall_file_md5=$(md5sum $W/wremnants/postprocessing/scetlib_ad/np_damping_wall.py | cut -c1-32)"
echo "[run] cmd: $CMD"
export PYTHONUNBUFFERED=1
"$H/agent_setup.sh" --scetlib current -- bash -c "python3 $CMD" 2>&1
rc=$?
echo "[run] $(date -Is) exit=$rc"
