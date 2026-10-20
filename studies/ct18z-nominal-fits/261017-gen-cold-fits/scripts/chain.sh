#!/usr/bin/env bash
# Driver: gate -> pass 1 (fit) -> wait for exit -> check output -> gate -> pass 2 (postfit). Run detached.
# usage: chain.sh GEN_NOLAT|GEN_LAT
PF=$1
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
T=$H/studies/ct18z-nominal-fits/261017-gen-cold-fits
GATE=$H/studies/alphas-scan-discontinuity/scripts/mem_gate.sh
SC=/work/submit/lavezzo/alphaS/scetlib-gamma-nu-points/scetlib-cms/build
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261017_gen_nominal_fits
mkdir -p $OUT
runpass() { # $1 = log name, $2 = inner script, $3 = optional DONE_RE for the gate
  local log=$OUT/$1.log
  if [ -n "${3:-}" ]; then export DONE_RE="$3"; else unset DONE_RE; fi
  ln -sf $log $T/logs/$1.log
  echo "$1 $(date -Is) :: $GATE 260 $log -- $H/agent_setup.sh --scetlib $SC -- bash $2 $PF" >> $T/logs/launches.txt
  $GATE 260 $log -- $H/agent_setup.sh --scetlib $SC -- bash $2 $PF > $OUT/$1.gate 2>&1
  local pid=$(sed -n 's/^\[mem_gate\] pid \([0-9]*\).*/\1/p' $OUT/$1.gate | tail -1)
  echo "$1 pid $pid ($(date -Is))" >> $T/logs/launches.txt
  [ -n "$pid" ] || return 1
  while kill -0 $pid 2>/dev/null; do sleep 60; done
  echo "$1 ended $(date -Is): $(grep '^\[run\].*exit' $log | tail -1)" >> $T/logs/launches.txt
}
runpass $PF $T/scripts/run_fit.sh || exit 1
[ -s $OUT/fitresults_$PF.hdf5 ] || { echo "$PF: no fitresults, not running the postfit" >> $T/logs/launches.txt; exit 1; }
runpass ${PF}_PF $T/scripts/run_pf.sh "edmval|Iteration 0:|Traceback|Killed"
