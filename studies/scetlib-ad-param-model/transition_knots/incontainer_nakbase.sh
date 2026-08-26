#!/bin/bash
# Container entry for the near-anchor knot test: SCETlib from the isolated
# worktree /work/submit/lavezzo/alphaS/scetlib-nakbase (branch near-anchor-knots =
# fix-muf-member-coordinate + cherry-picked knot-spacing) and its own build-nakbase.
set -e
source /opt/venv/bin/activate
source /home/submit/lavezzo/alphaS/WRemnants/setup.sh > /dev/null
export SCETLIB_BUILD=/work/submit/lavezzo/alphaS/scetlib-nakbase/build-nakbase
source /work/submit/lavezzo/alphaS/scetlib-nakbase/setup.sh > /dev/null
cd /home/submit/lavezzo/alphaS/WRemnants
exec "$@"
