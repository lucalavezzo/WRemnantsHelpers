#!/usr/bin/env bash
# status.sh: one line per census fit -- state, PID, start, iterations, last loss (NLL is not blinded), exit.
# Read-only. Run from anywhere, outside the container.
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261001_census_nominal
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/walled-multistart-census/261001-census-nominal
printf "%-7s %-9s %-8s %-20s %6s %-18s %s\n" fit state pid started iters last_loss note
for i in $(seq -w 1 10); do
  PF=CENS$i; L=$OUT/$PF.log
  if [ ! -e "$L" ]; then printf "%-7s %-9s\n" $PF queued; continue; fi
  pid=$(ps -eo pid=,comm=,args= | awk -v p="--postfix $PF " '$2=="python3" && index($0,p){print $1}' | head -1)
  st=$(grep -m1 "^\[run\].*postfix=" "$L" | awk '{print $2}' | cut -c1-19)
  it=$(grep -c "Iteration [0-9]*: loss" "$L")
  ll=$(grep "Iteration [0-9]*: loss" "$L" | tail -1 | sed -E 's/.*loss ([^ ]+).*/\1/')
  ex=$(grep -m1 "^\[run\].*exit=" "$L" | sed -E 's/.*exit=//')
  if [ -n "$ex" ]; then state="exit=$ex"; [ -e "$OUT/fitresults_$PF.hdf5" ] && state="$state,fr"
  elif [ -n "$pid" ]; then state=running; grep -q "Results written\|loss_val_grad_hess" "$L" && state=hessian
  else state=gating; fi
  note=$(grep -m1 -E "Traceback|Killed|EAGAIN|restarting" "$L" | cut -c1-40)
  printf "%-7s %-9s %-8s %-20s %6s %-18s %s\n" $PF "$state" "${pid:--}" "${st:--}" "$it" "${ll:--}" "$note"
done
echo "queue: $(cat $T/logs/queue.pid 2>/dev/null) alive=$(kill -0 $(cat $T/logs/queue.pid) 2>/dev/null && echo yes || echo no); $(tail -1 $T/logs/queue.out)"
echo "node: $(awk '/MemAvailable/{print int($2/1048576)" GB avail"}' /proc/meminfo), my threads $(ps -o nlwp= -u $USER | awk '{s+=$1} END{print s+0}')"
