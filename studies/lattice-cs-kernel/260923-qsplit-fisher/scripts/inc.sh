#!/bin/bash
# Run a command inside the WRemnants container with the 2da973d/ca15aec SCETlib pin env.
exec singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ \
  /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest \
  /home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260921-cache-2da973d/scripts/incontainer.sh "$@"
