#!/usr/bin/env bash
# run_diag.sh: hess_diag.py in the container with the scetlib-cms gamma-nu-points build that LATB8/SATB8 ran on
# (the native lattice term needs DrellYan.gamma_nu_points), rabbit = the main checkout (2a59246, as SATB8).
set -uo pipefail
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
T=$H/studies/constrained-fit-strategy/261008-saturated-subfit-diagnosis
W=$H/../WRemnants
SB=/work/submit/lavezzo/alphaS/scetlib-gamma-nu-points/scetlib-cms/build
echo "[run] $(date -Is) HDIAG host=$(hostname) WRemnants=$(git -C $W rev-parse --short HEAD) WRemnants_diff_md5=$(git -C $W diff -- wremnants | md5sum | cut -c1-32) rabbit=$(git -C $W/rabbit rev-parse --short HEAD) rabbit_diff_md5=$(git -C $W/rabbit diff | md5sum | cut -c1-32) scetlib(branch build)=$(git -C $SB/.. rev-parse --short HEAD) scetlib_dirty=$(git -C $SB/.. status --porcelain --untracked-files=no | wc -l)"
export PYTHONUNBUFFERED=1
INNER=$T/logs/HDIAG.inner.sh
printf '%s\n' 'python3 -c "import rabbit, scetlib_qT, scetlib_tf; print(\"[run] rabbit from\", rabbit.__file__, \"scetlib_qT from\", scetlib_qT.__file__, \"ScetlibGammaNuTF:\", hasattr(scetlib_tf, \"ScetlibGammaNuTF\"))"' "python3 $T/scripts/hess_diag.py" > "$INNER"
"$H/agent_setup.sh" --scetlib "$SB" -- bash "$INNER" 2>&1
rc=$?
echo "[run] $(date -Is) exit=$rc"
