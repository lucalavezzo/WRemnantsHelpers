#!/usr/bin/env bash
# chain3.sh (phase 2): BLINDCHK -> ASIMLIVE -> LATLIVE5 -> LATLIVE8, strictly sequential (one big job of this task
# at a time; launch.sh refuses otherwise), each through mem_gate (400 GB). Polls logs only, never kills.
# Stops if a stage does not exit 0, or if BLINDCHK's check A is not exactly 0.
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/lattice-cs-kernel/261006-lattice-chi2-in-fit
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261006_lattice_chi2_in_fit
run_stage() {
  local PF=$1
  echo "[chain3] $(date -Is) launching $PF"
  bash "$T/scripts/launch.sh" "$PF" || { echo "[chain3] launch of $PF refused; stopping"; exit 1; }
  until grep -q "^\[run\] .* exit=" "$OUT/$PF.log" 2>/dev/null; do sleep 60; done
  sleep 20
  grep -q "exit=0" "$OUT/$PF.log" || { echo "[chain3] $(date -Is) $PF did not exit 0; stopping"; exit 1; }
  echo "[chain3] $(date -Is) $PF exit 0"
}
run_stage BLINDCHK
grep -q "^\[chk A\] .* = +0.000e+00" "$OUT/BLINDCHK.log" || { echo "[chain3] BLINDCHK check A not exactly 0; stopping"; exit 1; }
grep -q "^\[chk B\] .*: True" "$OUT/BLINDCHK.log" || { echo "[chain3] BLINDCHK check B failed; stopping"; exit 1; }
run_stage ASIMLIVE
run_stage LATLIVE5
[ -e "$OUT/fitresults_LATLIVE5.hdf5" ] || { echo "[chain3] no LATLIVE5 fitresult; stopping"; exit 1; }
run_stage LATLIVE8
echo "[chain3] $(date -Is) all stages done"
