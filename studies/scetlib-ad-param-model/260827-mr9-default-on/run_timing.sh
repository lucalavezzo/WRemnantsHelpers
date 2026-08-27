#!/bin/bash
set -u
D=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260827-mr9-default-on
C=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/cache_260824b
IMG=/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
SING="singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ $IMG"
NOISE='^X-Math|max_iterations|absl::|cpu_feature_guard|To enable the following|beamfunc::|^INFO:|WARNING: All log'
stdbuf -oL -eL $SING $D/incontainer_mr9.sh python3 -u $D/timing_paired.py \
  --cache "$C/cache.npz" --conf "$C/cache.conf" --threads 16 --rounds 6 \
  2>&1 | stdbuf -oL grep -avE "$NOISE"
