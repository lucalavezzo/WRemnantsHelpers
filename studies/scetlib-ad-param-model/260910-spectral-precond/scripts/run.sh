#!/bin/bash
# usage: run.sh <logfile> <cmd...>
D=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-spectral-precond/scripts
IMG=/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
NOISE='^X-Math|max_iterations|absl::|cpu_feature_guard|To enable the following|beamfunc::|^INFO:|WARNING: All log|oneDNN|TF-TRT'
LOG=$1; shift
{ echo "[run] START $(date +%FT%T) loadavg=$(cut -d' ' -f1-3 /proc/loadavg)"
  echo "[run] free -g: $(free -g | sed -n 2p)  swap: $(free -g | sed -n 3p)"; } > $LOG
singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ $IMG \
  $D/incontainer.sh /usr/bin/time -v "$@" 2>&1 | grep -avE --line-buffered "$NOISE" >> $LOG
echo "[run] DONE rc=$? $(date +%FT%T) loadavg=$(cut -d' ' -f1-3 /proc/loadavg)" >> $LOG
echo "[run] DONE $(date +%FT%T) -> $LOG"
