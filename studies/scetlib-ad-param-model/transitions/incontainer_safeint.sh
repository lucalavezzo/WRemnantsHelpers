#!/bin/bash
# Container entry for the transition-point round: SCETlib from the isolated
# worktree /work/submit/lavezzo/alphaS/scetlib-safeint (branch
# muf-analytic-trans, off eb60a04 + the anlmuf DGLAP prototype) and its own
# build-safeint. scetlib-cms, build-fix, build-knots, build-trans, build-nak,
# build-5knot and build-anlmuf are NOT touched.
set -e
source /opt/venv/bin/activate
source /home/submit/lavezzo/alphaS/WRemnants/setup.sh > /dev/null
export SCETLIB_BUILD=/work/submit/lavezzo/alphaS/scetlib-safeint/build-safeint
source /work/submit/lavezzo/alphaS/scetlib-safeint/setup.sh > /dev/null
cd /home/submit/lavezzo/alphaS/WRemnants
exec "$@"
