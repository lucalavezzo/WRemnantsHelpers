#!/usr/bin/env bash
# run_fit.sh <PF>: runs ../cmds/<PF>.cmd in the container with the scetlib-cms gamma-nu-points build,
# exactly as LATB8 was run (studies/lattice-cs-kernel/261007-lattice-term-native/scripts/run_fit.sh):
# the native LatticeCSTerm needs DrellYan.gamma_nu_points, which only that branch build has.
set -uo pipefail
PF=$1
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
T=$H/studies/tmd-rapidity-shape/261007-y-shape-first-look
W=$H/../WRemnants
SB=/work/submit/lavezzo/alphaS/scetlib-gamma-nu-points/scetlib-cms/build
CMD=$(cat "$T/cmds/$PF.cmd")
echo "[run] $(date -Is) postfix=$PF host=$(hostname) WRemnants=$(git -C $W rev-parse --short HEAD) WRemnants_diff_md5=$(git -C $W diff -- wremnants | md5sum | cut -c1-32) rabbit=$(git -C $W/rabbit rev-parse --short HEAD) rabbit_diff_md5=$(git -C $W/rabbit diff | md5sum | cut -c1-32) scetlib(branch build)=$(git -C $SB/.. rev-parse --short HEAD) term_md5=$(md5sum $W/wremnants/postprocessing/scetlib_ad/lattice_cs_term.py | cut -c1-32)"
echo "[run] cmd: $CMD"
export PYTHONUNBUFFERED=1
INNER=$T/logs/$PF.inner.sh
printf '%s\n' "python3 $CMD" > "$INNER"
"$H/agent_setup.sh" --scetlib "$SB" -- bash "$INNER" 2>&1
rc=$?
echo "[run] $(date -Is) exit=$rc"
