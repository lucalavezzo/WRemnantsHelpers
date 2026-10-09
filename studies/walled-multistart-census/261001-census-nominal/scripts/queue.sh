#!/usr/bin/env bash
# Census queue: keep at most MAXRUN (3) of OUR census fits alive (comm == python3 with --postfix CENS, no
# self-match); launch the next CENS<NN> from the list when one finishes. Each launch goes through mem_gate.sh.
# Also refuses to launch while our user thread count would exceed ~26000 (mem_gate checks this too) or
# MemAvailable < 500 GB.  Stop it with: kill <pid in logs/queue.pid>  (running fits are NOT affected).
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/walled-multistart-census/261001-census-nominal
MAXRUN=${MAXRUN:-3}
LIST=${LIST:-"CENS01 CENS09 CENS02 CENS03 CENS04 CENS05 CENS06 CENS07 CENS08 CENS10"}
echo $$ > $T/logs/queue.pid
n_alive() { ps -eo comm=,args= | awk '$1=="python3" && /--postfix CENS[0-9][0-9]/' | wc -l; }
n_gating() { ps -eo args= | awk '/mem_gate.sh 330 .*261001_census_nominal\/CENS/ && !/awk/' | wc -l; }
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
