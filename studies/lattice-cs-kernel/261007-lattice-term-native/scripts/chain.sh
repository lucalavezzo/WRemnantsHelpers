#!/usr/bin/env bash
# chain.sh: when LATB5 exits 0 with its fitresult on ceph, launch LATB8 (warm from LATB5) through the gate.
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/lattice-cs-kernel/261007-lattice-term-native
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261007_lattice_term_native
echo "[chain] $(date -Is) waiting for LATB5"
until grep -qE "\[run\] .* exit=" "$OUT/LATB5.log"; do sleep 30; done
if grep -qE "\[run\] .* exit=0" "$OUT/LATB5.log" && [ -s "$OUT/fitresults_LATB5.hdf5" ]; then
  echo "[chain] $(date -Is) LATB5 exit 0 -> launching LATB8"
  bash "$T/scripts/launch.sh" LATB8
else
  echo "[chain] $(date -Is) LATB5 FAILED: not launching LATB8"
fi
