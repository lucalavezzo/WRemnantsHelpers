#!/bin/bash
set -e
D=/home/submit/lavezzo/.claude/jobs/140d052c/tmp/safeint
IMG=/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
SING="singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ $IMG"
tag="${1:-0}"
$SING $D/incontainer_safeint.sh $D/configure_safeint.sh > $D/cfg_$tag.log 2>&1
$SING $D/incontainer_safeint.sh cmake --build /work/submit/lavezzo/alphaS/scetlib-safeint/build-safeint -j 24 > $D/build_$tag.log 2>&1
echo "BUILD $tag DONE $(date)"
