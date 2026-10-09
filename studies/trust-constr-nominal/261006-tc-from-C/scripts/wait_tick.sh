#!/usr/bin/env bash
# wait_tick.sh [PF] [secs]: block up to <secs> (default 570) or until the fit's run_fit wrapper logs exit/Traceback;
# then print the last 3 trace lines. PID-free: watches the log only (the fit is identified by its own log file).
PF=${1:-TCC1}; N=${2:-570}
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/trust-constr-nominal/261006-tc-from-C
L=$T/logs/$PF.log
end=$((SECONDS+N))
while [ $SECONDS -lt $end ]; do grep -qE "Traceback|\[run\].*exit=" $L && break; sleep 15; done
$T/scripts/trace.sh $PF 3; grep -E "Traceback|\[run\].*exit=|minimizer status" $L | tail -3 | cut -c1-300; date +%H:%M
