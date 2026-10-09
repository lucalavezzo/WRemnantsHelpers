#!/bin/bash
# run a command inside the WRemnants container with the venv + setup.sh
# usage: incontainer.sh <cmd ...>
exec singularity exec --bind /scratch/,/work/,/home/,/ceph/ \
  /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest \
  bash -c 'source /opt/venv/bin/activate && cd /home/submit/lavezzo/alphaS/WRemnantsHelpers && source setup.sh >/dev/null 2>&1 && cd - >/dev/null && "$@"' _ "$@"
