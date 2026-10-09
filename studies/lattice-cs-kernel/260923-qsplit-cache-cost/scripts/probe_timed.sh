#!/bin/bash
# Timing probe for a Q-split forecast cache. Builds a 4-bin LOW-qT subset
# (qT rows 0,1 = [0,1],[1,2] GeV x |Y| rows 3,4 = [1.5,2],[2,2.5]) of the
# candidate forecast grid, one Q window per process, --pdf-eig ${PDFEIG:-0} (alphaS pair
# kept, so no eigenvector members and no quadratic form).
# usage: probe.sh <tag> <Qlo> <Qhi> <cpuset> [threads]
set -u
TAG=$1; QLO=$2; QHI=$3; CPUSET=$4; THREADS=${5:-64}
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/lattice-cs-kernel/260923-qsplit-cache-cost
PIN=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260921-cache-2da973d
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/qsplit_probe_260923/$TAG
BASE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/ntrain_gate/base_1e3.conf
IMG=/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
mkdir -p $OUT
LOG=$T/logs/probe_$TAG.log
echo "=== probe $TAG subset=${SUBSET:-3,4/0,1} pdfeig=${PDFEIG:-0} Q=[$QLO,$QHI] threads=$THREADS cpuset=$CPUSET start $(date -Is)" > $LOG
/usr/bin/time -v -o $T/logs/time_$TAG.txt taskset -c "$CPUSET" singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ $IMG \
  $PIN/scripts/incontainer.sh python3 -u \
  /home/submit/lavezzo/alphaS/WRemnants/scripts/rabbit/scetlib_ad/build_scetlib_ad_cache.py \
  --base-conf "$BASE" \
  --q-edges $QLO $QHI \
  --y-edges 0 0.5 1.0 1.5 2.0 2.5 \
  --qt-edges 0 1 2 3 4 5 6 8 10 12 14 17 20 25 30 40 \
  --subset "${SUBSET:-3,4/0,1}" \
  -o $OUT --outname cache --threads $THREADS --pdf-eig ${PDFEIG:-0} --n-train 9 >> $LOG 2>&1
echo "=== exit $? $(date -Is)" >> $LOG
