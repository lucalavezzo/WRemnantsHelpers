#!/usr/bin/env bash
# status.sh: one line per T6 profile fit -- state, PID, start, iterations, iteration-0 and last loss (NLL is not
# blinded), exit. Read-only. Run from anywhere, outside the container.
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261002_multistart_profile
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/walled-multistart-census/261002-multistart-profile
printf "%-8s %-11s %-8s %-20s %6s %-14s %-18s %s\n" fit state pid started iters loss_it0 last_loss note
for PF in $(for b in PROFM1W PROFM1R PROFM1K PROFP1W PROFP1R PROFP1K PROFM2W PROFM2R PROFM2K PROFP2W PROFP2R PROFP2K; do echo $b; ls $OUT/${b}S*.log 2>/dev/null | xargs -rn1 basename | sed "s/.log$//" | sort -V; done); do
  L=$OUT/$PF.log
  if [ ! -e "$L" ]; then printf "%-8s %-11s\n" $PF queued; continue; fi
  pid=$(ps -eo pid=,comm=,args= | awk -v p="--postfix $PF " '$2=="python3" && index($0,p){print $1}' | head -1)
  st=$(grep -m1 "^\[run\].*postfix=" "$L" | awk '{print $2}' | cut -c1-19)
  it=$(grep -c "Iteration [0-9]*: loss" "$L")
  l0=$(grep -m1 "Iteration 0: loss" "$L" | sed -E 's/.*loss ([^ ]+).*/\1/')
  ll=$(grep "Iteration [0-9]*: loss" "$L" | tail -1 | sed -E 's/.*loss ([^ ]+).*/\1/')
  ex=$(grep -m1 "^\[run\].*exit=" "$L" | sed -E 's/.*exit=//')
  if [ -n "$ex" ]; then state="exit=$ex"; [ -e "$OUT/fitresults_$PF.hdf5" ] && [ $(stat -c %s "$OUT/fitresults_$PF.hdf5") -gt 1000000 ] && state="$state,fr"
  elif [ -n "$pid" ]; then state=running; grep -q "Results written\|loss_val_grad_hess" "$L" && state=hessian
  else state=gating; fi
  note=$(grep -m1 -E "Traceback|Killed|EAGAIN|restarting|still stalling" "$L" | cut -c1-40)
  printf "%-8s %-11s %-8s %-20s %6s %-14s %-18s %s\n" $PF "$state" "${pid:--}" "${st:--}" "$it" "${l0:--}" "${ll:--}" "$note"
done
echo "queue: $(cat $T/logs/queue.pid 2>/dev/null) alive=$(kill -0 $(cat $T/logs/queue.pid 2>/dev/null) 2>/dev/null && echo yes || echo no); $(tail -1 $T/logs/queue.out 2>/dev/null)"
echo "watcher: $(cat $T/logs/watcher.pid 2>/dev/null) alive=$(kill -0 $(cat $T/logs/watcher.pid 2>/dev/null) 2>/dev/null && echo yes || echo no); $(tail -1 $T/logs/watcher.log 2>/dev/null)"
echo "node: $(awk '/MemAvailable/{print int($2/1048576)" GB avail"}' /proc/meminfo), my threads $(ps -o nlwp= -u $USER | awk '{s+=$1} END{print s+0}')"
