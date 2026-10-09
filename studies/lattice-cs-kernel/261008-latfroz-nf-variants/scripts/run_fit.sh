#!/usr/bin/env bash
# run_fit.sh <PF>: runs ../cmds/<PF>.cmd (rabbit_fit) or, for NCHKF, scripts/nchk_froz.py, in the container with the
# scetlib-cms gamma-nu-points build (the one LATB8 used; the LATFROZ code needs no SCETlib change).
set -uo pipefail
PF=$1
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
T=$H/studies/lattice-cs-kernel/261008-latfroz-nf-variants
W=$H/../WRemnants
SB=/work/submit/lavezzo/alphaS/scetlib-gamma-nu-points/scetlib-cms/build
CMD=$(cat "$T/cmds/$PF.cmd")
echo "[run] $(date -Is) postfix=$PF host=$(hostname) WRemnants=$(git -C $W rev-parse --short HEAD) WRemnants_diff_md5=$(git -C $W diff -- wremnants | md5sum | cut -c1-32) rabbit=$(git -C $W/rabbit rev-parse --short HEAD) rabbit_diff_md5=$(git -C $W/rabbit diff | md5sum | cut -c1-32) scetlib(branch build)=$(git -C $SB/.. rev-parse --short HEAD) scetlib_dirty=$(git -C $SB/.. status --porcelain --untracked-files=no | wc -l) term_md5=$(md5sum $W/wremnants/postprocessing/scetlib_ad/lattice_cs_term.py | cut -c1-32)"
echo "[run] cmd: $CMD"
export PYTHONUNBUFFERED=1
INNER=$T/logs/$PF.inner.sh
case "$PF" in NCHKF) RUN="python3 $T/scripts/nchk_froz.py" ;; *) RUN="python3 $CMD" ;; esac
printf '%s\n' 'python3 -c "import rabbit, scetlib_qT, scetlib_tf; print(\"[run] rabbit from\", rabbit.__file__, \"scetlib_qT from\", scetlib_qT.__file__)"' "$RUN" > "$INNER"
"$H/agent_setup.sh" --scetlib "$SB" -- bash "$INNER" 2>&1
rc=$?
echo "[run] $(date -Is) exit=$rc"
