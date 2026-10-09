#!/usr/bin/env bash
# chain2.sh (12:45, replaces chain.sh after the OOM): SERIALISED launches, at most ONE of this task's cache loads at a time,
# gate 400 GB (orchestrator). Steps, in order, each waiting for its trigger AND for the previous launch to have finished
# loading (its log matches cache loaded|Iteration 0:|Traceback|Killed|exit=):
#   T8P5R   after T8C8 loaded
#   HESST8B after T8B exit 0 (with a fitresult)
#   T8P8    after T8P5R exit 0
# Never kills anything. Logs to ../logs/chain2.log.
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/walled-multistart-census/261006-t8-l4nu-lattice2d
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261006_t8_l4nu_lattice2d
LOADED="cache loaded|Iteration 0:|Traceback|Killed|exit="
last=T8C8
loaded() { grep -qE "$LOADED" "$OUT/$1.log" 2>/dev/null; }
ok() { grep -q "exit=0" "$OUT/$1.log" 2>/dev/null && [ -e "$OUT/fitresults_$1.hdf5" ]; }
ended() { grep -q "exit=" "$OUT/$1.log" 2>/dev/null; }
declare -A DONE=()
while [ ${#DONE[@]} -lt 3 ]; do
  if loaded "$last"; then
    if [ -z "${DONE[T8P5R]:-}" ]; then
      echo "$(date -Is) T8C8 loaded -> T8P5R"; bash $T/scripts/launch.sh T8P5R; DONE[T8P5R]=1; last=T8P5R
    elif [ -z "${DONE[HESST8B]:-}" ] && ended T8B; then
      DONE[HESST8B]=1
      if ok T8B; then echo "$(date -Is) T8B done -> HESST8B"; bash $T/scripts/launch.sh HESST8B; last=HESST8B
      else echo "$(date -Is) T8B ended without success ($(grep exit= $OUT/T8B.log | tail -1)); HESST8B NOT launched"; fi
    elif [ -z "${DONE[T8P8]:-}" ] && ended T8P5R; then
      DONE[T8P8]=1
      if ok T8P5R; then echo "$(date -Is) T8P5R done -> T8P8"; bash $T/scripts/launch.sh T8P8; last=T8P8
      else echo "$(date -Is) T8P5R ended without success ($(grep exit= $OUT/T8P5R.log | tail -1)); T8P8 NOT launched"; fi
    fi
  fi
  sleep 60
done
echo "$(date -Is) chain2 done"
