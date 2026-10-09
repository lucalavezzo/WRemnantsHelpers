#!/usr/bin/env bash
# chain.sh: detached watcher. When a stage's log shows exit=0 AND its fitresult exists, launch the next stage:
#   T8C5 -> T8C8 ; T8P5 -> T8P8 ; T8B -> HESST8B. Logs to ../logs/chain.log. Never kills anything.
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/walled-multistart-census/261006-t8-l4nu-lattice2d
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261006_t8_l4nu_lattice2d
declare -A NEXT=([T8C5]=T8C8 [T8P5]=T8P8 [T8B]=HESST8B)
declare -A DONE=()
while [ ${#DONE[@]} -lt ${#NEXT[@]} ]; do
  for s in "${!NEXT[@]}"; do
    [ -n "${DONE[$s]:-}" ] && continue
    if grep -q "exit=" "$OUT/$s.log" 2>/dev/null; then
      DONE[$s]=1
      if grep -q "exit=0" "$OUT/$s.log" && [ -e "$OUT/fitresults_$s.hdf5" ]; then
        echo "$(date -Is) $s finished OK -> launching ${NEXT[$s]}"; bash "$T/scripts/launch.sh" "${NEXT[$s]}"
      else
        echo "$(date -Is) $s ended WITHOUT success ($(grep exit= $OUT/$s.log | tail -1)); ${NEXT[$s]} NOT launched"
      fi
    fi
  done
  sleep 60
done
echo "$(date -Is) chain done"
