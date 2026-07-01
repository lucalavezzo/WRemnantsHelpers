#!/usr/bin/env bash
set -eo pipefail

singularity run --bind /scratch/,/work/,/home/,/ceph/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling\:latest /bin/bash -lc '
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh
workflows/histmaker.sh -p codex
'
