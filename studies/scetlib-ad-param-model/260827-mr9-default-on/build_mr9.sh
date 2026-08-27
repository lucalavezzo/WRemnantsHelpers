#!/bin/bash
set -e
D=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260827-mr9-default-on
IMG=/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
SING="singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ $IMG"
$SING $D/incontainer_mr9.sh $D/configure_mr9.sh > $D/cfg.log 2>&1
$SING $D/incontainer_mr9.sh cmake --build /work/submit/lavezzo/alphaS/scetlib-mr9on/build-mr9on -j 32 > $D/build.log 2>&1
echo "BUILD DONE $(date)"
