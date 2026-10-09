#!/usr/bin/env bash
# chain7.sh (phase 3, 2026-10-07): subset cache, mem_gate 260 GB, one big job of this task at a time, never kills.
#   BLINDFULL (alpha_s + TNP source checks; must print A = 0 and E = 0) -> ASIMFULL (Asimov closure of pert=live; must
#   PASS) -> LATFULL5 -> LATFULL8 -> [LATDNF5 -> LATDNF8 only if $T/RUN_LATDNF exists when LATFULL8 is done]
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/lattice-cs-kernel/261006-lattice-chi2-in-fit
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261006_lattice_chi2_in_fit
export GATE_GB=260
run_stage() {
  local PF=$1
  echo "[chain7] $(date -Is) launching $PF"
  bash "$T/scripts/launch.sh" "$PF" || { echo "[chain7] launch of $PF refused; stopping"; exit 1; }
  until grep -q "^\[run\] .* exit=" "$OUT/$PF.log" 2>/dev/null; do sleep 60; done
  sleep 20
  grep -q "exit=0" "$OUT/$PF.log" || { echo "[chain7] $(date -Is) $PF did not exit 0; stopping"; exit 1; }
  echo "[chain7] $(date -Is) $PF exit 0"
}
run_stage BLINDFULL
grep -q "^\[chk A\] .* = +0.000e+00" "$OUT/BLINDFULL.log" || { echo "[chain7] BLINDFULL check A failed; stopping"; exit 1; }
[ "$(grep -c '^\[chk E\] .*term - model = +0.000e+00' "$OUT/BLINDFULL.log")" = 2 ] || { echo "[chain7] BLINDFULL check E failed; stopping"; exit 1; }
echo "[chain7] $(date -Is) BLINDFULL checks A and E pass"
run_stage ASIMFULL
"/home/submit/lavezzo/alphaS/WRemnantsHelpers/agent_setup.sh" --scetlib current -- python3 "$T/scripts/asimov_check.py" "$T/asimov_closure_full.json" ASIMFULL "$OUT/seeds/seed_ASIMFULL_displaced.hdf5" > "$T/logs/asimov_check_full.log" 2>&1
grep -q "ASIMOV CLOSURE PASS" "$T/logs/asimov_check_full.log" || { echo "[chain7] $(date -Is) Asimov closure (pert=live) FAILED; stopping"; exit 1; }
echo "[chain7] $(date -Is) Asimov closure (pert=live) PASS"
run_stage LATFULL5
[ -e "$OUT/fitresults_LATFULL5.hdf5" ] || { echo "[chain7] no LATFULL5 fitresult; stopping"; exit 1; }
run_stage LATFULL8
if [ -e "$T/RUN_LATDNF" ]; then
  run_stage LATDNF5
  [ -e "$OUT/fitresults_LATDNF5.hdf5" ] || { echo "[chain7] no LATDNF5 fitresult; stopping"; exit 1; }
  run_stage LATDNF8
else
  echo "[chain7] $(date -Is) RUN_LATDNF not set: direct_nf chain skipped"
fi
echo "[chain7] $(date -Is) all stages done"
