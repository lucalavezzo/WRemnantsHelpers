#!/usr/bin/env bash
# run_fit.sh <PF>: runs cmds/<PF>.cmd (built by build_cmds.py from XWSTIFF's own meta_info command) inside the
# container, with the trust-constr rabbit worktree and this task's scripts/ (npwall_tc.py) prepended to PYTHONPATH.
set -uo pipefail
PF=$1
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
T=$H/studies/trust-constr-nominal/261006-tc-from-C
W=$H/../WRemnants
RT=/work/submit/lavezzo/rabbit-trustconstr
CMD=$(cat "$T/cmds/$PF.cmd")
grep -q "if not vv.any():" "$W/scetlib-cms/py/scetlib_tf.py" || { echo "hvp zero-seed skip missing"; exit 2; }
grep -q "_parse_margin" "$W/wremnants/postprocessing/scetlib_ad/np_damping_wall.py" || { echo "margin keyword missing"; exit 2; }
echo "[run] $(date -Is) postfix=$PF host=$(hostname) WRemnants=$(git -C $W rev-parse --short HEAD) rabbit_worktree=$(git -C $RT rev-parse --short HEAD) rabbit_worktree_diff_md5=$(git -C $RT diff | md5sum | cut -c1-32) scetlib=$(git -C $W/scetlib-cms rev-parse --short HEAD) wall_diff_md5=$(git -C $W diff -- wremnants/postprocessing/scetlib_ad/np_damping_wall.py | md5sum | cut -c1-32) npwall_tc_md5=$(md5sum $T/scripts/npwall_tc.py | cut -c1-32) params_diff_md5=$(git -C $W diff -- wremnants/postprocessing/scetlib_ad/params.py | md5sum | cut -c1-32)"
echo "[run] cmd: $CMD"
export PYTHONUNBUFFERED=1
# the inner command goes through a file: quoted -c strings do not survive the container re-entry
INNER=$T/logs/$PF.inner.sh
printf '%s\n' 'python3 -c "import rabbit, npwall_tc; print(\"[run] rabbit from\", rabbit.__file__, \"npwall_tc from\", npwall_tc.__file__)"' "python3 $CMD" > "$INNER"
"$H/agent_setup.sh" --scetlib current --prepend-pythonpath "$RT:$T/scripts" -- bash "$INNER" 2>&1
rc=$?
echo "[run] $(date -Is) exit=$rc"
