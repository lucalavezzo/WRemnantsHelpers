#!/bin/bash
# run a command inside the WRemnants container with venv + setup.sh, with the trust-constr rabbit
# worktree and this task's scripts/ (npwall_tc.py) PREPENDED to PYTHONPATH (after setup.sh, so they win).
RT=/work/submit/lavezzo/rabbit-trustconstr
S=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/trust-constr-nominal/261005-trust-constr-port/scripts
exec singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ \
  /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest \
  bash -c 'source /opt/venv/bin/activate && cd /home/submit/lavezzo/alphaS/WRemnantsHelpers && source setup.sh >/dev/null 2>&1; export PYTHONPATH='$RT:$S':$PYTHONPATH; cd - >/dev/null && "$@"' _ "$@"
