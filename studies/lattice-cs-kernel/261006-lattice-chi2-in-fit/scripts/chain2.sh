#!/usr/bin/env bash
# chain2.sh (2026-10-06 ~14:30, after the reboot killed LATCHI5 and chain.sh): waits (log polling only, never kills)
# for LATCHI5R to exit 0 with a fitresult, then launches LATCHI8 through launch.sh (mem_gate 400 GB; launch.sh refuses
# while any LATCHI* fit of this task is alive, so the two stages are never alive together).
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/lattice-cs-kernel/261006-lattice-chi2-in-fit
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261006_lattice_chi2_in_fit
echo "[chain2] $(date -Is) waiting for LATCHI5R"
until grep -q "^\[run\] .* exit=" "$OUT/LATCHI5R.log" 2>/dev/null; do sleep 60; done
sleep 30
if grep -q "exit=0" "$OUT/LATCHI5R.log" && [ -e "$OUT/fitresults_LATCHI5R.hdf5" ]; then
  echo "[chain2] $(date -Is) LATCHI5R done -> launching LATCHI8"
  bash "$T/scripts/launch.sh" LATCHI8
else
  echo "[chain2] $(date -Is) LATCHI5R did not finish cleanly; NOT launching LATCHI8"
fi
