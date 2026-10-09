#!/usr/bin/env bash
# T6 queue: keep at most MAXRUN (3) of OUR profile fits alive or gating (comm == python3 with --postfix PROF..,
# no self-match); launch the next one from LIST when one finishes. Order: the 3 starts of a point are adjacent,
# +-1 sigma first, then +-2 sigma. Each launch goes through mem_gate.sh. Rolling slots: a point's starts are
# launched together, but a slow fit does not hold back the next point.
# Stop it with: kill <pid in logs/queue.pid>  (running fits are NOT affected).
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/walled-multistart-census/261002-multistart-profile
MAXRUN=${MAXRUN:-3}
LIST=${LIST:-"PROFM1W PROFM1R PROFM1K PROFP1W PROFP1R PROFP1K PROFM2W PROFM2R PROFM2K PROFP2W PROFP2R PROFP2K"}
echo $$ > $T/logs/queue.pid
n_alive() { ps -eo comm=,args= | awk '$1=="python3" && /--postfix PROF[MP][12][WRK] /' | wc -l; }
n_gating() { ps -eo args= | awk '/mem_gate.sh 330 .*261002_multistart_profile\/PROF/ && !/awk/' | wc -l; }
for PF in $LIST; do
  while :; do
    a=$(n_alive); g=$(n_gating)
    avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)
    if [ $((a + g)) -lt $MAXRUN ] && [ "$avail" -ge 500 ]; then break; fi
    sleep 120
  done
  echo "[queue] $(date -Is) alive=$a gating=$g avail=${avail}GB: launching $PF"
  setsid bash $T/scripts/launch.sh $PF < /dev/null > /dev/null 2>&1 &
  sleep 240   # let the gate pick it up and the python process appear before re-counting
done
echo "[queue] $(date -Is) all launched"
