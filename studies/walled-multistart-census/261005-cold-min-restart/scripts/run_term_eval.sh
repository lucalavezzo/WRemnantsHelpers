#!/usr/bin/env bash
# term split for CMR1B: data / constraints / BB / wall vs XWSTIFF, at CMR1B's minimum and at the 1b seed (= C), XWSTIFF's own objective.
set -uo pipefail
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
T=$H/studies/walled-multistart-census/261005-cold-min-restart
A=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
echo "[run] $(date -Is) term_eval WRemnants=$(git -C $H/../WRemnants rev-parse --short HEAD) rabbit=$(git -C $H/../WRemnants/rabbit rev-parse --short HEAD)"
export PYTHONUNBUFFERED=1
"$H/agent_setup.sh" --scetlib current -- python3 $T/scripts/term_eval.py --ref $A/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5 \
  --seeds $A/261005_cold_min_restart/fitresults_CMR1B.hdf5 $A/261005_cold_min_restart/seeds/seed_1b_C_in_XWSTIFF.hdf5 \
  --out $T/term_split_CMR1B.json 2>&1
echo "[run] $(date -Is) exit=$?"
