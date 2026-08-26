#!/bin/bash
# Shared container entry for the scetlib_ad work: venv + WRemnants + SCETlib.
#
# The login shell has neither TensorFlow nor scetlib_qT, so anything that
# touches the model or the calculation must go through here:
#
#   SING="singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ \
#     /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest"
#   $SING ./incontainer.sh python3 ab_scale_route.py --mode param ...
#
# scetlib-cms/setup.sh is the one that is easy to forget: without it the import
# fails with "No module named 'scetlib_qT'". It also lifts the stack limit.
set -e
source /opt/venv/bin/activate
source "${WREM_BASE:-/home/submit/lavezzo/alphaS/WRemnants}/setup.sh" > /dev/null
source "${WREM_BASE:-/home/submit/lavezzo/alphaS/WRemnants}/scetlib-cms/setup.sh" > /dev/null
cd "${WREM_BASE:-/home/submit/lavezzo/alphaS/WRemnants}"
exec "$@"
