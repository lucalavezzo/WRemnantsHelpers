#!/usr/bin/env bash
# chain4.sh (phase 2, after chain3 was stopped): wait for the (useless, -t -1 unminimised) ASIMLIVE to exit, then
# ASIMLIVE2 -> asimov_check (must PASS) -> LATLIVE5 -> LATLIVE8, one big job at a time, mem_gate 400 GB. Never kills.
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/lattice-cs-kernel/261006-lattice-chi2-in-fit
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261006_lattice_chi2_in_fit
until grep -q "^\[run\] .* exit=" "$OUT/ASIMLIVE.log" 2>/dev/null; do sleep 30; done
echo "[chain4] $(date -Is) ASIMLIVE exited ($(grep -o 'exit=[0-9]*' $OUT/ASIMLIVE.log | tail -1))"
run_stage() {
  local PF=$1
  echo "[chain4] $(date -Is) launching $PF"
  bash "$T/scripts/launch.sh" "$PF" || { echo "[chain4] launch of $PF refused; stopping"; exit 1; }
  until grep -q "^\[run\] .* exit=" "$OUT/$PF.log" 2>/dev/null; do sleep 60; done
  sleep 20
  grep -q "exit=0" "$OUT/$PF.log" || { echo "[chain4] $(date -Is) $PF did not exit 0; stopping"; exit 1; }
  echo "[chain4] $(date -Is) $PF exit 0"
}
run_stage ASIMLIVE2
"/home/submit/lavezzo/alphaS/WRemnantsHelpers/agent_setup.sh" --scetlib current -- python3 "$T/scripts/asimov_check.py" "$T/asimov_closure.json" > "$T/logs/asimov_check.log" 2>&1
grep -q "ASIMOV CLOSURE PASS" "$T/logs/asimov_check.log" || { echo "[chain4] $(date -Is) Asimov closure FAILED; stopping before LATLIVE"; exit 1; }
echo "[chain4] $(date -Is) Asimov closure PASS"
run_stage LATLIVE5
[ -e "$OUT/fitresults_LATLIVE5.hdf5" ] || { echo "[chain4] no LATLIVE5 fitresult; stopping"; exit 1; }
run_stage LATLIVE8
echo "[chain4] $(date -Is) all stages done"
