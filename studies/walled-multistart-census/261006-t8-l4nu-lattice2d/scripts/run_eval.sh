#!/usr/bin/env bash
# run_eval.sh: step-2 evaluation (one cache load) in the container, trust-constr rabbit worktree first on PYTHONPATH.
set -uo pipefail
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
T=$H/studies/walled-multistart-census/261006-t8-l4nu-lattice2d
RT=/work/submit/lavezzo/rabbit-trustconstr
echo "[run] $(date -Is) eval_l4nu_pull WRemnants=$(git -C $H/../WRemnants rev-parse --short HEAD) rabbit_worktree=$(git -C $RT rev-parse --short HEAD)"
export PYTHONUNBUFFERED=1
"$H/agent_setup.sh" --scetlib current --prepend-pythonpath "$RT:$T/scripts" -- python3 $T/scripts/eval_l4nu_pull.py 2>&1
echo "[run] $(date -Is) exit=$?"
