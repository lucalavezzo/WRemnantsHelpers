#!/bin/bash
# Container entry for the analytic d(conv)/dln(muF) work: SCETlib from the
# isolated worktree /work/submit/lavezzo/alphaS/scetlib-anlmuf (branch
# muf-analytic-dglap, off eb60a04) and its own build-anlmuf.
set -e
source /opt/venv/bin/activate
source /home/submit/lavezzo/alphaS/WRemnants/setup.sh > /dev/null
export SCETLIB_BUILD=/work/submit/lavezzo/alphaS/scetlib-anlmuf/build-anlmuf
source /work/submit/lavezzo/alphaS/scetlib-anlmuf/setup.sh > /dev/null
cd /home/submit/lavezzo/alphaS/WRemnants
exec "$@"
