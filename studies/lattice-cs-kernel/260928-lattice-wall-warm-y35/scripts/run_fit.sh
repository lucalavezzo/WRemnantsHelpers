#!/usr/bin/env bash
# LATL4ZY35WALLWARM: lattice (l4zero) + wall on the NEW |Y|<=3.5 cache, WARM from the no-lattice walled
# new-cache minimum Y35ZWALLWARM (Luca 2026-09-28).
#   = LATL4ZWALLCOLD's recipe (run_fit_l4zero.sh: lattice card, fit_params without lambda4_nu -> frozen at
#     its anchor 0, prior_sigmas=lambda2_nu=nan, --wall, --earlyStopping 100)
#   + Y35ZWALLWARM's cache/build (fit_y35.sh: bin-0 quick-patched cache from the /scratch copy with the
#     extracted rules -> fast loader; in-tree SCETlib via agent_setup.sh --scetlib current)
#   + --externalPostfit Y35ZWALLWARM (full vector; rabbit matches by name, so lambda4_nu is simply absent
#     and stays at 0; theta scaling does not depend on prior_sigmas).
set -uo pipefail
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
A=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CARD=$A/260923_lattice_fits/cards/cardA_latticeASWZ_l4zero_statsyst.hdf5
CACHE=/scratch/submit/cms/alphaS/ad_scetlib_caches/pdf62_y35_260921/merged_full_bin0xzero
SEED=$A/260924_y35_bin0xzero_fits/fitresults_Y35ZWALLWARM.hdf5
OUT=$A/260928_lattice_y35_fits
POSTFIX=LATL4ZY35WALLWARM
FP=$(tail -1 $H/studies/lattice-cs-kernel/260923-lattice-fits/logs/fit_params_l4zero.txt)
[ $(echo "$FP" | tr , "\n" | wc -l) -eq 44 ] || { echo "bad fit_params list"; exit 2; }
echo "$FP" | grep -q "lambda4_nu" && { echo "lambda4_nu in fit_params"; exit 2; }
grep -q "if not vv.any():" "$H/../WRemnants/scetlib-cms/py/scetlib_tf.py" || { echo "hvp zero-seed skip missing"; exit 2; }
mkdir -p "$OUT"; LOG=$OUT/$POSTFIX.log
W=$H/../WRemnants
echo "[run] $(date -Is) card=$CARD md5 $(md5sum $CARD | cut -c1-32) cache=$CACHE seed=$SEED WRemnants=$(git -C $W rev-parse --short HEAD) rabbit=$(git -C $W/rabbit rev-parse --short HEAD) scetlib=$(git -C $W/scetlib-cms rev-parse --short HEAD)" | tee -a "$LOG"
export PYTHONUNBUFFERED=1
"$H/agent_setup.sh" --scetlib current -- \
  "$H/workflows/fitterAD.sh" "$CARD" -c "$CACHE" -o "$OUT" -p "$POSTFIX" --wall \
    -f "threads=128 fit_params=$FP prior_sigmas=lambda2_nu=nan -v 4 --earlyStopping 100 --externalPostfit $SEED" 2>&1 | tee -a "$LOG"
echo "[run] $(date -Is) exit=${PIPESTATUS[0]}" | tee -a "$LOG"
