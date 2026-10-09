#!/usr/bin/env bash
# After the first chain (pid $1) stops at its STOP file (TS16 skipped), run the remaining points one at a time.
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/ad-fit-memory-footprint/261007-thread-scaling
O=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261007_thread_scaling
p=$1; shift
while kill -0 $p 2>/dev/null; do sleep 15; done
rm -f $O/STOP
exec bash $T/scripts/chain.sh "$@"
