#!/bin/bash
# Container entry for the MR !9 default-on round. SCETlib from the ISOLATED
# worktree /work/submit/lavezzo/alphaS/scetlib-mr9on (detached at a7392be plus
# the default flip) and its own build-mr9on. scetlib-cms, build-fix,
# build-knots, build-trans, build-nak, build-5knot and build-anltrans* are NOT
# touched, and neither is the scetlib-anltrans worktree.
set -e
source /opt/venv/bin/activate
source /home/submit/lavezzo/alphaS/WRemnants/setup.sh > /dev/null
export SCETLIB_BUILD=/work/submit/lavezzo/alphaS/scetlib-mr9on/build-mr9on
source /work/submit/lavezzo/alphaS/scetlib-mr9on/setup.sh > /dev/null
cd /home/submit/lavezzo/alphaS/WRemnants
exec "$@"
