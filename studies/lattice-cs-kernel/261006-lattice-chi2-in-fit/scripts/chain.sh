#!/usr/bin/env bash
# chain.sh: waits (PID / log polling only, never kills) for LATCHI5 to exit 0 with a fitresult, then launches LATCHI8.
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/lattice-cs-kernel/261006-lattice-chi2-in-fit
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261006_lattice_chi2_in_fit
echo "[chain] $(date -Is) waiting for LATCHI5"
until grep -q "^\[run\] .* exit=" "$OUT/LATCHI5.log" 2>/dev/null; do sleep 60; done
if grep -q "exit=0" "$OUT/LATCHI5.log" && [ -e "$OUT/fitresults_LATCHI5.hdf5" ]; then
  echo "[chain] $(date -Is) LATCHI5 done -> launching LATCHI8"
  bash "$T/scripts/launch.sh" LATCHI8
else
  echo "[chain] $(date -Is) LATCHI5 did not finish cleanly; NOT launching LATCHI8"
fi
