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
#   then waits (holding the lock) until logfile matches $DONE_RE (default: Iteration 0 / error) or 3 h.
#   Never more than MAXRUN (default 2) gated jobs alive at once; a further gate waits for one to exit.
set -u
need=$1; log=$2; shift 2; [ "$1" = "--" ] && shift
# NB no bare "Error": fitterAD echoes --computeHistErrors, which released the slot 30 s after launch (2026-09-25)
# v4 (2026-10-06): NO "cache loaded". With the y35 cache that line comes at ~146 GB, but SCETlib then allocates
# its muF-fit caches (~185 GB) on the FIRST evaluation, ~2 min later, so the gate never saw the real footprint
# (studies/ad-fit-memory-footprint/261006-memory-breakdown). Budget ~335 GB per y35 fit.
DONE_RE=${DONE_RE:-"Iteration 0:|Traceback|Killed"}
# v3 (2026-09-25 13:55): up to NSLOTS concurrent loads (default 3); slot 1 is the v2 lock, so gates queued
# under v2 keep their place. Each slot still re-checks MemAvailable before launching.
NSLOTS=${NSLOTS:-3}
# v4 (2026-10-06): RUN cap. The load slots only serialise the load; once released, any number of ~330 GB
# steady-state jobs could pile up, and on 2026-10-06 about five of them (1.6 TB) forced a node reboot.
# At most MAXRUN (default 2) gated jobs may be ALIVE at once, counted from /tmp/alphas_run/<pid>.
MAXRUN=${MAXRUN:-2}
RUNDIR=/tmp/alphas_run; mkdir -p $RUNDIR
nrun() { local n=0 f; for f in $RUNDIR/*; do [ -e "$f" ] || continue; if kill -0 "$(basename "$f")" 2>/dev/null; then n=$((n+1)); else rm -f "$f"; fi; done; echo $n; }
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
# run cap: check, launch and register under one global lock, so two gates cannot both take the last run slot
exec 8>/tmp/alphas_runcap.lock
while :; do
  flock 8
  r=$(nrun)
  [ "$r" -lt "$MAXRUN" ] && break
  flock -u 8
  echo "[mem_gate] $(date +%T) ${r}/${MAXRUN} gated jobs alive: waiting for one to finish"; sleep 60
done
echo $need > /tmp/alphas_slot$got.need
echo "[mem_gate] $(date +%FT%T) launching (avail ${avail} GB, alive ${r}/${MAXRUN})"
setsid bash -c "$*" >> "$log" 2>&1 < /dev/null 9>&- 8>&- &
pid=$!
touch $RUNDIR/$pid
flock -u 8; exec 8>&-
echo "[mem_gate] pid $pid"
t0=$(date +%s)
until grep -qE "$DONE_RE" "$log" 2>/dev/null || ! kill -0 $pid 2>/dev/null || [ $(( $(date +%s) - t0 )) -gt 10800 ]; do sleep 30; done
rm -f /tmp/alphas_slot$got.need
echo "[mem_gate] $(date +%FT%T) releasing lock (pid $pid alive: $(kill -0 $pid 2>/dev/null && echo yes || echo no))"
