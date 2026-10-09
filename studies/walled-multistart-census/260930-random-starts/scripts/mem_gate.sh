#!/usr/bin/env bash
# Shared launch gate for anything that loads a SCETlib-AD cache (fits, toys, direct evaluations > 50 GB).
# The node has ~1.45 TB RAM, swap is FULL, and several workers launch at once: a stock cache load peaks at
# ~3x the rules blob (old 260827 cache ~150 GB, new y35 cache ~520 GB; steady ~50 / ~320 GB).
#
# Up to NSLOTS (3) launches at a time each hold a slot lock (/tmp/alphas_bigload2*.lock) from "enough memory" until the job's log shows the load
# finished, so two loads never peak together. Also refuses while the user's thread count is near the ceiling.
#
# usage: mem_gate.sh <peak_GB> <logfile> -- <command ...>
#   runs <command> detached (setsid, stdout+stderr >> logfile) once MemAvailable >= peak_GB + 150 GB,
#   then waits (holding the lock) until logfile matches $DONE_RE (default: loaded / Iteration 0 / error) or 3 h.
set -u
need=$1; log=$2; shift 2; [ "$1" = "--" ] && shift
# NB no bare "Error": fitterAD echoes --computeHistErrors, which released the slot 30 s after launch (2026-09-25)
DONE_RE=${DONE_RE:-"cache loaded|Iteration 0:|Traceback|Killed"}
# v3 (2026-09-25 13:55): up to NSLOTS concurrent loads (default 3); slot 1 is the v2 lock, so gates queued
# under v2 keep their place. Each slot still re-checks MemAvailable before launching.
NSLOTS=${NSLOTS:-3}
echo "[mem_gate] $(date +%FT%T) waiting for a load slot (need ${need} GB peak) for: $*"
while :; do
  for k in $(seq 1 $NSLOTS); do
    lf=/tmp/alphas_bigload2.lock; [ $k -gt 1 ] && lf=/tmp/alphas_bigload2_slot$k.lock
    exec 9>$lf
    if flock -n 9; then got=$k; break 2; fi
    exec 9>&-
  done
  sleep 15
done
echo "[mem_gate] $(date +%T) got slot $got"
# In-flight accounting: other slots' peaks that are still loading count against MemAvailable.
inflight() { local t=0 f; for f in /tmp/alphas_slot*.need; do [ -f "$f" ] && [ "$f" != "/tmp/alphas_slot$got.need" ] && t=$((t + $(cat "$f"))); done; echo $t; }
while :; do
  avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)
  thr=$(ps -o nlwp= -u "$USER" | awk '{s+=$1} END{print s+0}')
  infl=$(inflight)
  if [ "$avail" -ge $((need + 150 + infl)) ] && [ "$thr" -lt 26000 ]; then break; fi
  echo "[mem_gate] $(date +%T) avail ${avail} GB, in-flight ${infl} GB, threads ${thr}: waiting"; sleep 60
done
echo $need > /tmp/alphas_slot$got.need
echo "[mem_gate] $(date +%FT%T) launching (avail ${avail} GB)"
setsid bash -c "$*" >> "$log" 2>&1 < /dev/null 9>&- &
pid=$!
echo "[mem_gate] pid $pid"
t0=$(date +%s)
until grep -qE "$DONE_RE" "$log" 2>/dev/null || ! kill -0 $pid 2>/dev/null || [ $(( $(date +%s) - t0 )) -gt 10800 ]; do sleep 30; done
rm -f /tmp/alphas_slot$got.need
echo "[mem_gate] $(date +%FT%T) releasing lock (pid $pid alive: $(kill -0 $pid 2>/dev/null && echo yes || echo no))"
