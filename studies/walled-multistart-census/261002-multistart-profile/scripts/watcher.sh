#!/usr/bin/env bash
# watcher.sh: babysit the relaunched fits (chains PROFM2R, PROFM2K, PROFP2W; heads PROF..S as launched by the
# orchestrator on 2026-10-04). Every 5 min, for each chain head:
#   done  = [run] exit=0 AND fitresults_<head>.hdf5 > 1 MB (rabbit writes a ~99 kB stub at start)
#   dead  = [run] exit=<nonzero>, OR (no [run] exit line AND no live python/run_fit/mem_gate process), seen twice in a row
# A dead head is relaunched ONCE per death from its latest periodic snapshot, as the next suffix (S -> S2 -> S3),
# through scripts/launch.sh (mem_gate + log symlink). At most MAXRELAUNCH (2) relaunches per chain by this watcher;
# beyond that it only reports. It never restarts a fit that is alive (a crawl is reported by a human, not looped).
# Exits once every chain head is done. Events -> logs/watcher.log (+ logs/launches.txt via launch.sh).
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/walled-multistart-census/261002-multistart-profile
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261002_multistart_profile
MAXRELAUNCH=${MAXRELAUNCH:-2}
HEADS=${HEADS:-"PROFM2RS PROFM2KS PROFP2WS"}
LOG=$T/logs/watcher.log
echo $$ > $T/logs/watcher.pid
say() { echo "[watcher] $(date -Is) $*" >> $LOG; }
declare -A head nrel dead1
for h in $HEADS; do base=${h%S*}; head[$base]=$h; nrel[$base]=0; dead1[$base]=0; done
say "start, chains: ${!head[*]} heads: ${head[*]}"
alive() {  # any process for this postfix: python fit, run_fit wrapper, or mem_gate waiting for it
  ps -eo comm=,args= | awk -v p="--postfix $1 " -v r="run_fit.sh $1" -v g="$OUT/$1.log" \
    '($1=="python3" && index($0,p)) || (substr($0, length($0)-length(r)+1)==r) || ($1=="bash" && index($0,"mem_gate.sh") && index($0,g))' | grep -q .
}
next_name() { local h=$1; if [[ $h =~ S([0-9]+)$ ]]; then echo "${h%${BASH_REMATCH[1]}}$((BASH_REMATCH[1]+1))"; else echo "${h}2"; fi; }
while :; do
  ndone=0
  for base in "${!head[@]}"; do
    h=${head[$base]}; L=$OUT/$h.log; fr=$OUT/fitresults_$h.hdf5
    ex=$(grep -m1 "^\[run\].*exit=" "$L" 2>/dev/null | sed -E 's/.*exit=//')
    if [ "$ex" = "0" ] && [ -e "$fr" ] && [ $(stat -c %s "$fr") -gt 1000000 ]; then ndone=$((ndone+1)); continue; fi
    isdead=0
    if [ -n "$ex" ] && [ "$ex" != "0" ]; then isdead=1
    elif [ -n "$ex" ] && [ "$ex" = "0" ]; then say "$h exit=0 but no full fitresult -- REPORT, not relaunching"; ndone=$((ndone+1)); continue
    elif ! alive $h; then isdead=1; fi
    if [ $isdead = 0 ]; then dead1[$base]=0; continue; fi
    if [ ${dead1[$base]} = 0 ] && [ -z "$ex" ]; then dead1[$base]=1; say "$h looks dead (no exit line, no process); confirming next round"; continue; fi
    dead1[$base]=0
    if [ ${nrel[$base]} -ge $MAXRELAUNCH ]; then say "$h DEAD (exit=${ex:-none}); relaunch cap reached -- REPORT"; ndone=$((ndone+1)); continue; fi
    snap=$OUT/snapshot_fitresults_$h.hdf5
    if [ ! -s "$snap" ]; then snap=$(grep -m1 -oE "externalPostfit [^ ]+" $T/cmds/$h.cmd | cut -d' ' -f2); say "$h has no own snapshot; reusing its start $snap"; fi
    n=$(next_name $h)
    sed -e "s#--postfix $h #--postfix $n #" -e "s#snapshot_fitresults_$h.hdf5#snapshot_fitresults_$n.hdf5#" \
        -e "s#--externalPostfit [^ ]*#--externalPostfit $snap#" $T/cmds/$h.cmd > $T/cmds/$n.cmd
    lastloss=$(grep -E "Iteration [0-9]+: loss" $L | tail -1 | sed -E 's/.*(Iteration [0-9]+: loss [^ ]+).*/\1/')
    say "$h DEAD (exit=${ex:-none}, last: $lastloss); relaunching as $n from $snap (snapshot mtime $(stat -c %y $snap | cut -c1-19))"
    setsid bash $T/scripts/launch.sh $n < /dev/null > $T/logs/launch_$n.out 2>&1 &
    head[$base]=$n; nrel[$base]=$((nrel[$base]+1))
  done
  if [ $ndone -ge ${#head[@]} ]; then say "all chain heads finished: ${head[*]}; exiting"; exit 0; fi
  sleep 300
done
