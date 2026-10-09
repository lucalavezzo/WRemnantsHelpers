#!/bin/bash
# Passive CPU/RSS sampler: every IV s until <pid> exits, writes
#   t_unix, cpu_s (utime+stime of the whole process, all threads), vmrss_gb, threads, last logged iteration, its loss
# Usage: sample_cpu.sh <pid> <fit log> <out.csv> [iv=30]
pid=$1; log=$2; csv=$3; iv=${4:-30}
tck=$(getconf CLK_TCK)
echo "t_unix,cpu_s,vmrss_gb,threads,last_it,last_loss" > $csv
while kill -0 $pid 2>/dev/null; do
  now=$(date +%s)
  cpu=$(awk -v t=$tck '{print ($14+$15)/t}' /proc/$pid/stat 2>/dev/null)
  mem=$(awk '/^VmRSS:/{a=$2/1048576}/^Threads:/{b=$2}END{printf "%.2f,%d", a, b}' /proc/$pid/status 2>/dev/null)
  it=$(tail -c 20000 $log 2>/dev/null | grep -aoE "Iteration [0-9]+: loss [-+0-9.eE]+" | tail -1 | awk '{gsub(":","",$2); print $2","$4}')
  [ -n "$cpu" ] && echo "$now,$cpu,$mem,${it:-,}" >> $csv
  sleep $iv
done
echo "$(date +%s),EXIT,,,," >> $csv
