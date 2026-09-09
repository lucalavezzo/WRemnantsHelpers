#!/bin/bash
# Container entry for 260909-newcard-validation (same env as 260827-authoritative-
# validation, so every number here is directly comparable to that set).
# SCETlib comes from a PRIVATE SNAPSHOT of the MR !9 worktree build so that a
# concurrent rebuild anywhere else cannot move these numbers mid-run.
#   snapshot : /work/submit/lavezzo/alphaS/scetlib-ad-authval-260827/scetlib_snapshot
#   HEAD     : b66f8de (MR !9 default-on) -- ancestors 92f1299 (MR !8) and
#              3a8db11 (_rule_is_matched, MR !7) both verified.
set -e
source /opt/venv/bin/activate
source /home/submit/lavezzo/alphaS/WRemnants/setup.sh > /dev/null
export SCETLIB_BUILD=/work/submit/lavezzo/alphaS/scetlib-ad-authval-260827/scetlib_snapshot/build
source /work/submit/lavezzo/alphaS/scetlib-ad-authval-260827/scetlib_snapshot/setup.sh > /dev/null
cd /home/submit/lavezzo/alphaS/WRemnants
exec "$@"
