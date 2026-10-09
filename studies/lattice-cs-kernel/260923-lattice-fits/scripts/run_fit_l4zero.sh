#!/usr/bin/env bash
# One lattice-constrained COLD fit, l4zero design: 1D ASWZ lambda2_nu term (card) + lambda4_nu FROZEN at its anchor 0
# by exclusion from fit_params (the same mechanism that holds lambda_inf_nu: never reaches rabbit).
#
# Identical to the reference arms' launchers
#   studies/scetlib-ad-param-model/260915-cachecorr-ab/scripts/fit.sh       (CCKRYLOV -> CCCOLDSELF)
#   studies/scetlib-ad-param-model/260915-cachecorr-ab/scripts/fit_wall.sh  (CCWALLCOLD -> CCWALLCOLDR)
# i.e. agent_setup.sh --scetlib authval (b66f8de, the only build that reads the
# 260827 cache) -> workflows/fitterAD.sh, cache pdf62_corrgrid_260827/merged_full,
# threads=128, -v 4, trust-krylov, --computeSaturatedProjectionTests, --doImpacts,
# --globalImpacts. The walled arm adds fitterAD.sh --wall (tau=5, NPDampingWall +
# NPDampingMapping) and --earlyStopping 100, exactly as CCWALLCOLD did; the
# unwalled arm keeps the default --earlyStopping (20), exactly as CCKRYLOV did.
#
# The ONLY two differences from the references (the measurement):
#   1. the card: card A + external_terms/lattice_cs (diff_cards.py: nothing else)
#   2. prior_sigmas=lambda2_nu=nan,lambda4_nu=nan  (the lattice REPLACES the
#      default N(0,1)-in-theta CS priors instead of stacking on them)
# NO --externalPostfit: cold start.
#
# usage: run_fit.sh <card> <postfix> <outdir> [--wall]
set -uo pipefail
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
T=$H/studies/lattice-cs-kernel/260923-lattice-fits
CARD=$1; POSTFIX=$2; OUT=$3; WALL=${4:-}
CACHE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
AUTHVAL=/work/submit/lavezzo/alphaS/scetlib-ad-authval-260827/scetlib_snapshot
grep -q "if not vv.any():" "$AUTHVAL/py/scetlib_tf.py" || { echo "hvp zero-seed skip missing"; exit 2; }
mkdir -p "$OUT"
LOG=$OUT/fit_${POSTFIX}.log
{
  echo "[stamp] $(date +%FT%T) host $(hostname) loadavg $(cut -d' ' -f1-3 /proc/loadavg)"
  echo "[stamp] card $CARD md5 $(md5sum "$CARD" | cut -c1-32)"
  echo "[stamp] libscet-qT.so md5 $(md5sum $AUTHVAL/build/lib/libscet-qT.so | cut -c1-32)"
  echo "[stamp] scetlib_tf.py md5 $(md5sum $AUTHVAL/py/scetlib_tf.py | cut -c1-32)"
  W=/home/submit/lavezzo/alphaS/WRemnants
  echo "[stamp] WRemnants HEAD $(git -C $W rev-parse --short HEAD) ($(git -C $W rev-parse --abbrev-ref HEAD))"
  for f in param_model.py params.py np_damping_wall.py xsec_backend.py scale_envelope.py response.py; do
    echo "[stamp]   scetlib_ad/$f md5 $(md5sum $W/wremnants/postprocessing/scetlib_ad/$f | cut -c1-32)"
  done
  echo "[stamp] rabbit HEAD $(git -C $W/rabbit rev-parse --short HEAD), local diff md5 $(git -C $W/rabbit diff | md5sum | cut -c1-32)"
  echo "[stamp] rabbit_fit.py md5 $(md5sum $W/rabbit/bin/rabbit_fit.py | cut -c1-32)  fitter.py md5 $(md5sum $W/rabbit/rabbit/fitter.py | cut -c1-32)"
} > "$LOG"
FP=$(tail -1 $T/logs/fit_params_l4zero.txt)
[ $(echo "$FP" | tr , "\n" | wc -l) -eq 44 ] || { echo "bad fit_params list"; exit 2; }
echo "$FP" | grep -q "lambda4_nu" && { echo "lambda4_nu in fit_params"; exit 2; }
EXTRA="threads=128 fit_params=$FP prior_sigmas=lambda2_nu=nan -v 4"
WALLARG=""
if [ "$WALL" == "--wall" ]; then
  WALLARG="--wall"; EXTRA="$EXTRA --earlyStopping 100"
fi
export PYTHONUNBUFFERED=1
"$H/agent_setup.sh" --scetlib authval -- \
  /usr/bin/time -v "$H/workflows/fitterAD.sh" "$CARD" -c "$CACHE" -o "$OUT" -p "$POSTFIX" $WALLARG \
    -f "$EXTRA" >> "$LOG" 2>&1
echo "[stamp] DONE rc=$? $(date +%FT%T)" >> "$LOG"
