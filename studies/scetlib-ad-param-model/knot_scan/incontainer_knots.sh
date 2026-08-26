#!/bin/bash
# Container entry for the muF KNOT SPACING test.
#
# Same as ../incontainer.sh except that SCETlib comes from the isolated
# worktree /work/submit/lavezzo/alphaS/scetlib-knots (branch knot-spacing) and
# its own build-knots, so nothing here can disturb the shared scetlib-cms
# checkout or build-fix, which other sessions are using. The worktree is
# bb2e7cb (= autodiff-sigmaul + MRs !5 !6) plus a cherry-pick of !7 plus the
# knot-spacing patch, i.e. byte-identical physics to the shared tree at the
# default knot factor 2.
set -e
source /opt/venv/bin/activate
source /home/submit/lavezzo/alphaS/WRemnants/setup.sh > /dev/null
export SCETLIB_BUILD=/work/submit/lavezzo/alphaS/scetlib-knots/build-knots
source /work/submit/lavezzo/alphaS/scetlib-knots/setup.sh > /dev/null
cd /home/submit/lavezzo/alphaS/WRemnants
exec "$@"
