#!/bin/bash
set -e
SING="singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest"
CACHE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/cache_260824b
CORR=/home/submit/lavezzo/alphaS/WRemnants/wremnants-data/data/TheoryCorrections/scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_CorrZ.pkl.lz4
$SING /home/submit/lavezzo/.claude/jobs/140d052c/tmp/$2 \
  python3 -u /home/submit/lavezzo/.claude/jobs/140d052c/tmp/model_vs_template_perbin.py \
  --cache "$CACHE/cache.npz" --conf "$CACHE/cache.conf" --corr "$CORR" \
  --threads 16 -o "$1"
