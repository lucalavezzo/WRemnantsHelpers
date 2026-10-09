#!/usr/bin/env bash
# run_fit.sh CMR1A|CMR1B : runs cmds/<PF>.cmd (built by build_cmds.py from the reference's own meta_info command).
# stdout -> the gate log = $OUT/<PF>.log (log lives with the fitresult). Pattern: 261001-census-nominal/scripts/run_fit.sh
set -uo pipefail
PF=$1
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
T=$H/studies/walled-multistart-census/261005-cold-min-restart
W=$H/../WRemnants
CMD=$(cat "$T/cmds/$PF.cmd")
grep -q "if not vv.any():" "$W/scetlib-cms/py/scetlib_tf.py" || { echo "hvp zero-seed skip missing"; exit 2; }
grep -q "_parse_margin" "$W/wremnants/postprocessing/scetlib_ad/np_damping_wall.py" || { echo "margin keyword missing"; exit 2; }
echo "[run] $(date -Is) postfix=$PF host=$(hostname) WRemnants=$(git -C $W rev-parse --short HEAD) rabbit=$(git -C $W/rabbit rev-parse --short HEAD) scetlib=$(git -C $W/scetlib-cms rev-parse --short HEAD) wall_diff_md5=$(git -C $W diff -- wremnants/postprocessing/scetlib_ad/np_damping_wall.py | md5sum | cut -c1-32)"
echo "[run] cmd: $CMD"
export PYTHONUNBUFFERED=1
"$H/agent_setup.sh" --scetlib current -- bash -c "python3 $CMD" 2>&1
rc=$?
echo "[run] $(date -Is) exit=$rc"
