#!/usr/bin/env bash
# status.sh: one-screen status of the T8 fits.
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/walled-multistart-census/261006-t8-l4nu-lattice2d/logs
date
for f in T8B T8C5 T8C8 T8P5 T8P8 HESST8B; do
  [ -e $T/$f.log ] || continue
  echo "== $f"
  grep -E "start loss|Traceback|Error|exit=|minimizer status" $T/$f.log | sed 's/\x1b\[[0-9;]*m//g' | cut -c1-300
  grep -E "Iteration [0-9]+:" $T/$f.log | sed 's/\x1b\[[0-9;]*m//g' | awk '{print $3, $5, $6, $7}' | tail -2
  grep "trust-constr: opt" $T/$f.log | sed 's/\x1b\[[0-9;]*m//g' | tail -1 | cut -c20-200
  [ -e $T/$f.gate ] && tail -n 1 $T/$f.gate
done
