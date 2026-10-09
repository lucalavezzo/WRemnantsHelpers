#!/usr/bin/env bash
# (chain6 = chain5 with SUBCHK8 -> SUBCHK8B, which adds --noEDM: the --noFit pass of SUBCHK8 sat in the EDM CG)
# chain6.sh (2026-10-07): on the |Y|<=2.5 SUBSET cache (pdf62_y35_260921_y25, 242 GB; mem_gate budget 260):
#   SUBCHK8B   LATCHI8's own command on the subset cache, --noFit --noHessian at LATCHI8's vector: its NLL must equal
#             LATCHI8's (subset-vs-full like-for-like check; |dNLL| < 1e-6 or the chain stops)
#   LATLIVE5Y tau 5, live term (syst=Jnf+Jbt+pert), warm from LATCHI8, --noHessian --noEDM
#   LATLIVE8Y tau 8, warm from LATLIVE5Y, Hessian + EDM
# One big job at a time (launch.sh refuses otherwise). Polls logs only, never kills.
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/lattice-cs-kernel/261006-lattice-chi2-in-fit
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261006_lattice_chi2_in_fit
export GATE_GB=260
run_stage() {
  local PF=$1
  echo "[chain6] $(date -Is) launching $PF"
  bash "$T/scripts/launch.sh" "$PF" || { echo "[chain6] launch of $PF refused; stopping"; exit 1; }
  until grep -q "^\[run\] .* exit=" "$OUT/$PF.log" 2>/dev/null; do sleep 60; done
  sleep 20
  grep -q "exit=0" "$OUT/$PF.log" || { echo "[chain6] $(date -Is) $PF did not exit 0; stopping"; exit 1; }
  echo "[chain6] $(date -Is) $PF exit 0"
}
run_stage SUBCHK8B
"/home/submit/lavezzo/alphaS/WRemnantsHelpers/agent_setup.sh" --scetlib current -- python3 -c "
from rabbit import io_tools
a = float(io_tools.get_fitresult('$OUT/fitresults_LATCHI8.hdf5', None)['nllvalreduced'])
b = float(io_tools.get_fitresult('$OUT/fitresults_SUBCHK8B.hdf5', None)['nllvalreduced'])
print(f'SUBCHK NLL(subset) - NLL(LATCHI8, full cache) = {b - a:+.3e}')
print('SUBCHK', 'PASS' if abs(b - a) < 1e-6 else 'FAIL')
" > "$T/logs/subchk.log" 2>&1
grep "SUBCHK" "$T/logs/subchk.log"
grep -q "SUBCHK PASS" "$T/logs/subchk.log" || { echo "[chain6] $(date -Is) subset-vs-full check FAILED; stopping"; exit 1; }
run_stage LATLIVE5Y
[ -e "$OUT/fitresults_LATLIVE5Y.hdf5" ] || { echo "[chain6] no LATLIVE5Y fitresult; stopping"; exit 1; }
run_stage LATLIVE8Y
echo "[chain6] $(date -Is) all stages done"
