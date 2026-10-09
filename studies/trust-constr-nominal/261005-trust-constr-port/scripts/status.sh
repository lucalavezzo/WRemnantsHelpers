#!/usr/bin/env bash
# status.sh: one-screen status of the trust-constr fits (loss, last KKT state, start/exit lines, gate).
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/trust-constr-nominal/261005-trust-constr-port/logs
date
for f in TCA TCB1 TCB2 HESSTCA HESSTCB1 HESSTCB2; do
  [ -e $T/$f.log ] || continue
  echo "== $f"
  grep -E "start loss|Traceback|Error|exit=|minimizer status" $T/$f.log | sed 's/\x1b\[[0-9;]*m//g' | cut -c1-400
  grep -E "Iteration [0-9]+:" $T/$f.log | sed 's/\x1b\[[0-9;]*m//g' | awk '{print $3, $5, $6, $7}' | tail -2
  grep "trust-constr: opt" $T/$f.log | sed 's/\x1b\[[0-9;]*m//g' | tail -1 | cut -c20-200
  [ -e $T/$f.gate ] && tail -n 1 $T/$f.gate
done
