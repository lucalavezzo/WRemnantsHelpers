#!/usr/bin/env bash
# run_fit.sh <PF>: runs ../cmds/<PF>.cmd in the container with the scetlib-cms gamma-nu-points build
# (the native lattice term needs DrellYan.gamma_nu_points). NCHK runs nativecheck.py instead of rabbit_fit.
set -uo pipefail
PF=$1
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
T=$H/studies/lattice-cs-kernel/261007-lattice-term-native
W=$H/../WRemnants
SB=/work/submit/lavezzo/alphaS/scetlib-gamma-nu-points/scetlib-cms/build
CMD=$(cat "$T/cmds/$PF.cmd")
echo "[run] $(date -Is) postfix=$PF host=$(hostname) WRemnants=$(git -C $W rev-parse --short HEAD) WRemnants_diff_md5=$(git -C $W diff -- wremnants | md5sum | cut -c1-32) rabbit=$(git -C $W/rabbit rev-parse --short HEAD) rabbit_diff_md5=$(git -C $W/rabbit diff | md5sum | cut -c1-32) scetlib(branch build)=$(git -C $SB/.. rev-parse --short HEAD) scetlib_dirty=$(git -C $SB/.. status --porcelain --untracked-files=no | wc -l) term_md5=$(md5sum $W/wremnants/postprocessing/scetlib_ad/lattice_cs_term.py | cut -c1-32) data_md5=$(md5sum $W/wremnants/postprocessing/scetlib_ad/data/lattice_aswz_data.npz | cut -c1-32)"
echo "[run] cmd: $CMD"
export PYTHONUNBUFFERED=1
INNER=$T/logs/$PF.inner.sh
case "$PF" in SATCHK) RUN="python3 $T/scripts/satcheck.py" ;; NCHK2) RUN="env NCHK_OUT=nativecheck2.json python3 $T/scripts/nativecheck.py" ;; NCHK*) RUN="python3 $T/scripts/nativecheck.py" ;; *) RUN="python3 $CMD" ;; esac
printf '%s\n' 'python3 -c "import rabbit, scetlib_qT, scetlib_tf; print(\"[run] rabbit from\", rabbit.__file__, \"scetlib_qT from\", scetlib_qT.__file__, \"ScetlibGammaNuTF:\", hasattr(scetlib_tf, \"ScetlibGammaNuTF\"))"' "$RUN" > "$INNER"
"$H/agent_setup.sh" --scetlib "$SB" -- bash "$INNER" 2>&1
rc=$?
echo "[run] $(date -Is) exit=$rc"
