#!/usr/bin/env bash
# run_satp.sh: SATP = SATB8 + full-scope spectral preconditioning (+ explicit smooth=relu2, since the wall default is C2
# from WRemnants 692f9483). Container + the scetlib-cms gamma-nu-points build SATB8 ran on; rabbit = main checkout.
# The command text is pasted into the inner script verbatim so bash parses its quoting ('.*' must not glob).
set -uo pipefail
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
T=$H/studies/constrained-fit-strategy/261008-saturated-subfit-diagnosis
W=$H/../WRemnants
SB=/work/submit/lavezzo/alphaS/scetlib-gamma-nu-points/scetlib-cms/build
CMD=$(cat "$T/cmds/SATP.cmd")
echo "[run] $(date -Is) postfix=SATP host=$(hostname) WRemnants=$(git -C $W rev-parse --short HEAD) WRemnants_diff_md5=$(git -C $W diff -- wremnants | md5sum | cut -c1-32) wall_md5=$(md5sum $W/wremnants/postprocessing/scetlib_ad/np_damping_wall.py | cut -c1-32) rabbit=$(git -C $W/rabbit rev-parse --short HEAD) rabbit_diff_md5=$(git -C $W/rabbit diff | md5sum | cut -c1-32) scetlib(branch build)=$(git -C $SB/.. rev-parse --short HEAD) scetlib_dirty=$(git -C $SB/.. status --porcelain --untracked-files=no | wc -l)"
echo "[run] cmd: $CMD"
export PYTHONUNBUFFERED=1
INNER=$T/logs/SATP.inner.sh
{ echo 'python3 -c "import rabbit, scetlib_qT, scetlib_tf; print(\"[run] rabbit from\", rabbit.__file__, \"scetlib_qT from\", scetlib_qT.__file__, \"ScetlibGammaNuTF:\", hasattr(scetlib_tf, \"ScetlibGammaNuTF\"))"'; echo "python3 $CMD"; } > "$INNER"
"$H/agent_setup.sh" --scetlib "$SB" -- bash "$INNER" 2>&1
rc=$?
echo "[run] $(date -Is) exit=$rc"
