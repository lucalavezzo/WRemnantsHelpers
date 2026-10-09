#!/bin/bash
# Build one Q window of grid A (260923-qsplit-cache-cost recipe): 5 |Y| x 15 qT bins,
# --pdf-eig 0 (alphaS PDF pair kept), n-train 9, base_1e3.conf, pin 2da973d/ca15aec.
# usage: build_window.sh <Qlo> <Qhi> <threads>
set -u
QLO=$1; QHI=$2; THREADS=$3
TAG=q${QLO}_${QHI}
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/lattice-cs-kernel/260923-qsplit-fisher
PIN=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260921-cache-2da973d
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/qsplit_260923/$TAG
BASE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/ntrain_gate/base_1e3.conf
IMG=/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
mkdir -p $OUT
LOG=$T/logs/build_$TAG.log
echo "=== build $TAG Q=[$QLO,$QHI] threads=$THREADS start $(date -Is)" > $LOG
/usr/bin/time -v -o $T/logs/time_$TAG.txt singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ $IMG \
  $PIN/scripts/incontainer.sh python3 -u \
  /home/submit/lavezzo/alphaS/WRemnants/scripts/rabbit/scetlib_ad/build_scetlib_ad_cache.py \
  --base-conf "$BASE" \
  --q-edges $QLO $QHI \
  --y-edges 0 0.5 1.0 1.5 2.0 2.5 \
  --qt-edges 0 1 2 3 4 5 6 8 10 12 14 17 20 25 30 40 \
  -o $OUT --outname cache --threads $THREADS --pdf-eig 0 --n-train 9 >> $LOG 2>&1
echo "=== exit $? $(date -Is)" >> $LOG
