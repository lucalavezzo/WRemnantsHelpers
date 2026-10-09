#!/bin/bash
# Passive memory sampler (v2): /proc/<pid>/status every INTERVAL s until the pid exits.
#  PRIMARY: VmRSS / RssAnon / RssFile / RssShmem / VmHWM / VmSwap from /proc/<pid>/status (mm counters, exact).
#  SECONDARY: Rss/Pss from /proc/<pid>/smaps_rollup every 6th sample -- UNRELIABLE on this kernel (5.14):
#  measured 36-277 GB against a steady 311.6 GB VmRSS on the same process (2026-10-06). Kept only as a flag.
#  Top mappings from /proc/<pid>/smaps every FULL_EVERY samples (0 = never; same caveat).
# Usage: sample_mem.sh <pid> <outprefix> [interval=10] [full_every=0]
pid=$1; out=$2; iv=${3:-10}; fe=${4:-0}
csv=$out.csv; top=$out.smaps_top.txt
echo "t_unix,vmrss_kb,rssanon_kb,rssfile_kb,rssshmem_kb,vmhwm_kb,vmswap_kb,vmsize_kb,threads,rollup_rss_kb,rollup_pss_kb" > $csv
i=0
while kill -0 $pid 2>/dev/null; do
  now=$(date +%s)
  s=$(awk '/^VmRSS:/{a=$2}/^RssAnon:/{b=$2}/^RssFile:/{c=$2}/^RssShmem:/{d=$2}/^VmHWM:/{e=$2}/^VmSwap:/{f=$2}/^VmSize:/{g=$2}/^Threads:/{h=$2}END{print a","b","c","d","e","f","g","h}' /proc/$pid/status 2>/dev/null)
  r=","
  if (( i % 6 == 0 )); then r=$(awk '/^Rss:/{a=$2}/^Pss:/{b=$2}END{print a","b}' /proc/$pid/smaps_rollup 2>/dev/null); fi
  [ -n "$s" ] && echo "$now,$s,$r" >> $csv
  if (( fe > 0 && i % fe == 0 )); then
    { echo "### t=$now"; awk '/^[0-9a-f]+-[0-9a-f]+ /{name=$6; if(name=="")name="[anon]"; range=$1} /^Rss:/{print $2, range, name}' /proc/$pid/smaps 2>/dev/null | sort -rn | head -25; } >> $top
  fi
  i=$((i+1)); sleep $iv
done
echo "$(date +%s),EXIT" >> $csv
