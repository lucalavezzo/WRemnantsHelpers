#!/usr/bin/env bash
# run_fit_seed.sh <PF>: as run_fit.sh, but with the rabbit worktree /work/submit/lavezzo/alphaS/rabbit-satseed
# (branch saturated-subfit-seed, --saturatedSeed) first on PYTHONPATH. Separate file so the running SATB8's
# run_fit.sh is never edited under it.
set -uo pipefail
PF=$1
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
T=$H/studies/lattice-cs-kernel/261007-lattice-term-native
W=$H/../WRemnants
R=/work/submit/lavezzo/alphaS/rabbit-satseed
SB=/work/submit/lavezzo/alphaS/scetlib-gamma-nu-points/scetlib-cms/build
CMD=$(cat "$T/cmds/$PF.cmd")
echo "[run] $(date -Is) postfix=$PF WRemnants=$(git -C $W rev-parse --short HEAD) rabbit(worktree)=$(git -C $R rev-parse --short HEAD) dirty=$(git -C $R status --porcelain --untracked-files=no | wc -l) scetlib=$(git -C $SB/.. rev-parse --short HEAD)"
echo "[run] cmd: $CMD"
export PYTHONUNBUFFERED=1
INNER=$T/logs/$PF.inner.sh
printf '%s\n' 'python3 -c "import rabbit, rabbit.snapshot as s; print(\"[run] rabbit from\", rabbit.__file__, \"seed_by_name:\", hasattr(s, \"seed_by_name\"))"' "python3 $CMD" > "$INNER"
"$H/agent_setup.sh" --scetlib "$SB" --prepend-pythonpath "$R" -- bash "$INNER" 2>&1
rc=$?
echo "[run] $(date -Is) exit=$rc"
