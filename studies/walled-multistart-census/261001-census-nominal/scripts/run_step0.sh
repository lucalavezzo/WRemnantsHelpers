#!/usr/bin/env bash
# step-0 runner, launched through mem_gate.sh (330 GB) by launch_step0.sh
set -uo pipefail
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
T=$H/studies/walled-multistart-census/261001-census-nominal
O=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261001_census_nominal/seeds
REF=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5
S=""
for k in 000 001 002; do S="$S $O/step0/a_nponly_$k.hdf5 $O/step0/b_nonnponly_$k.hdf5 $O/step0/c0_both_noalphas_$k.hdf5"; done
for k in 000 001 002 003 004 005 006 007; do S="$S $O/pert_$k.hdf5"; done
S="$S $O/cold_000.hdf5 $O/cold_001.hdf5"
echo "[run] $(date -Is) step0 WRemnants=$(git -C $H/../WRemnants rev-parse --short HEAD) rabbit=$(git -C $H/../WRemnants/rabbit rev-parse --short HEAD)"
export PYTHONUNBUFFERED=1
"$H/agent_setup.sh" --scetlib current -- python3 $T/scripts/step0_eval.py --ref $REF --seeds $S --out $T/step0_seed_cost.json 2>&1
echo "[run] $(date -Is) exit=$?"
