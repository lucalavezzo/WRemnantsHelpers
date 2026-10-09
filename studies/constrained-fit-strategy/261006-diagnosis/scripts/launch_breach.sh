#!/usr/bin/env bash
# One gated cache load: b_T reach of the y35 cache rules. Detached; log in logs/cache_breach.log.
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/constrained-fit-strategy/261006-diagnosis
G=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/alphas-scan-discontinuity/scripts/mem_gate.sh
DONE_RE="cache constructed|Traceback|Killed" setsid bash $G 330 $T/logs/cache_breach.log -- \
  "/home/submit/lavezzo/alphaS/WRemnantsHelpers/agent_setup.sh -- python3 $T/scripts/cache_breach.py; echo exit=\$?" \
  > $T/logs/cache_breach.gate 2>&1 < /dev/null &
echo "gate pid $!"
