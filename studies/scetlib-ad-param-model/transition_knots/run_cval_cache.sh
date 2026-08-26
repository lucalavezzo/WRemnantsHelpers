#!/bin/bash
set -e
SING="singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest"
C=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/cache_260824b
$SING /home/submit/lavezzo/.claude/jobs/140d052c/tmp/incontainer_nak_lean.sh \
  python3 -u /home/submit/lavezzo/.claude/jobs/140d052c/tmp/cval_from_cache.py \
  --cache $C/cache.npz --conf $C/cache.conf --threads 6 \
  -o /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/knot_scan/nak/cval_cache.json
