#!/bin/bash
# Passive sampler (v3 of ../../261006-memory-breakdown/scripts/sample_mem.sh): every INTERVAL s until <pid> exits,
#   /proc/<pid>/status  VmRSS, RssAnon, VmHWM, Threads (mm counters, exact; NOT smaps_rollup, which under-reports here)
#   /proc/<pid>/stat    utime+stime (clock ticks, fields 14+15; CPU utilisation = d(ticks)/CLK_TCK/dt)
#   /proc/loadavg       1-min load average of the node
# Usage: sample_proc.sh <pid> <out.csv> [interval=5]
pid=$1; csv=$2; iv=${3:-5}
echo "t_unix,vmrss_kb,rssanon_kb,vmhwm_kb,threads,cpu_ticks,load1" > $csv
while kill -0 $pid 2>/dev/null; do
  now=$(date +%s.%N | cut -c1-14)
  s=$(awk '/^VmRSS:/{a=$2}/^RssAnon:/{b=$2}/^VmHWM:/{e=$2}/^Threads:/{h=$2}END{print a","b","e","h}' /proc/$pid/status 2>/dev/null)
  c=$(sed 's/.*) //' /proc/$pid/stat 2>/dev/null | awk '{print $12+$13}')   # fields 14,15 after stripping "pid (comm) "
  l=$(cut -d' ' -f1 /proc/loadavg)
  [ -n "$s" ] && echo "$now,$s,$c,$l" >> $csv
  sleep $iv
done
echo "$(date +%s),EXIT" >> $csv
