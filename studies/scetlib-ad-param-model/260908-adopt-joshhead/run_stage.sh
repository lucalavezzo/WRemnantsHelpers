#!/bin/bash
# usage: run_stage.sh <logfile> <cmd...>   (singularity -> incontainer.sh -> cmd)
D=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260908-adopt-joshhead
IMG=/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
LOG=$1; shift
NOISE='^X-Math|max_iterations|absl::|cpu_feature_guard|To enable the following|beamfunc::|^INFO:|WARNING: All log|^2026-|oneDNN|TF-TRT'
singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ $IMG \
  $D/incontainer.sh /usr/bin/time -v "$@" 2>&1 | grep -avE --line-buffered "$NOISE" > $LOG
echo "STAGE DONE rc=$? $(date) -> $LOG"
