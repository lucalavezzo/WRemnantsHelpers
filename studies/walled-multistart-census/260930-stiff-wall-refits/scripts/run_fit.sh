#!/usr/bin/env bash
# T2 stiff-wall refit runner: run_fit.sh <POSTFIX>   (POSTFIX in NOMSTIFF XWSTIFF XL4ZSTIFF)
# Runs the command built by build_cmds.py (= the reference fit's own meta_info command with ONLY -o, --postfix,
# --snapshotFile, --regularizationStrength 5->8, "-r W M" -> "-r W M margin=0", --externalPostfit <ref fitresult>).
# Writes to stdout; launch through mem_gate.sh with the gate log = $OUT/$POSTFIX.log (log lives with the fitresult).
set -uo pipefail
PF=$1
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
T=$H/studies/walled-multistart-census/260930-stiff-wall-refits
W=$H/../WRemnants
CMD=$(cat "$T/cmds/$PF.cmd")
grep -q "if not vv.any():" "$W/scetlib-cms/py/scetlib_tf.py" || { echo "hvp zero-seed skip missing"; exit 2; }
grep -q "_parse_margin" "$W/wremnants/postprocessing/scetlib_ad/np_damping_wall.py" || { echo "margin keyword (T1 diff) missing"; exit 2; }
echo "[run] $(date -Is) postfix=$PF WRemnants=$(git -C $W rev-parse --short HEAD) rabbit=$(git -C $W/rabbit rev-parse --short HEAD) scetlib=$(git -C $W/scetlib-cms rev-parse --short HEAD) wall_diff_md5=$(git -C $W diff -- wremnants/postprocessing/scetlib_ad/np_damping_wall.py | md5sum | cut -c1-32)"
echo "[run] cmd: $CMD"
export PYTHONUNBUFFERED=1
"$H/agent_setup.sh" --scetlib current -- bash -c "python3 $CMD" 2>&1
rc=$?
echo "[run] $(date -Is) exit=$rc"
