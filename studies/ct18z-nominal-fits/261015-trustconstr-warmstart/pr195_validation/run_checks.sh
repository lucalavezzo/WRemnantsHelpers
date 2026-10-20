#!/usr/bin/env bash
# Before/after checks for WMass/rabbit PR #195 (trust-constr warm start) that CI does not
# cover. BASE = WMass main 2d9f380, NEW = the PR branch. Each check runs the same
# rabbit_fit command with both and compares the fitresults (compare_fitresults.py:
# bit-identical unless a tolerance is given). Run inside the WRemnants container:
#   agent_setup.sh -- bash run_checks.sh [OUTDIR]
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE=/work/submit/lavezzo/rabbit-base-2d9f380
NEW=/work/submit/lavezzo/rabbit-tc-warmstart
OUT=${1:-/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261017_pr_validation/local_checks}
mkdir -p "$OUT"
cd /tmp
export OMP_NUM_THREADS=8
echo "[checks] $(date -Is) BASE $(git -C $BASE rev-parse --short HEAD)  NEW $(git -C $NEW rev-parse --short HEAD)"

fit() {  # fit <base|new> <tag> args...
  local which=$1 tag=$2; shift 2
  local RB=$BASE; [ "$which" = new ] && RB=$NEW
  PYTHONPATH=$RB:$PYTHONPATH python $RB/bin/rabbit_fit.py "$@" -o "$OUT/$tag" > "$OUT/$tag.log" 2>&1 \
    || echo "[checks] FAILED: $tag (see $OUT/$tag.log)"
}
cmp_() {  # cmp_ <name> <tagA> <tagB> [compare args]
  local name=$1 a=$2 b=$3; shift 3
  local res
  res=$(PYTHONPATH=$NEW:$PYTHONPATH python $HERE/compare_fitresults.py "$OUT/$a/fitresults.hdf5" "$OUT/$b/fitresults.hdf5" "$@" 2>&1)
  local rc=$?
  echo "[check] $name: $([ $rc = 0 ] && echo PASS || echo FAIL) :: $(echo "$res" | head -1)"
  [ $rc = 0 ] || echo "$res" | sed -n '2,12p'
}

# tensors: the CI one (tests/make_tensor.py) and the small test-model one
PYTHONPATH=$NEW:$PYTHONPATH python $NEW/tests/make_tensor.py -o $OUT/ > $OUT/make_tensor.log 2>&1
CI=$OUT/test_tensor.hdf5
PYTHONPATH=$NEW:$PYTHONPATH python -c "
import sys; sys.path.insert(0, '$NEW')
from tests.test_sparse_fit import make_test_tensor
print(make_test_tensor('$OUT/small'))" > $OUT/small_tensor.log 2>&1
SM=$(tail -1 $OUT/small_tensor.log)
# a binding upper bound on bkg_norm (free minimum ~0)
TC="--minimizerMethod trust-constr --minimizerGtol 1e-10 --minimizerXtol 1e-10 --minimizerBarrierTol 1e-10 --minimizerMaxiter 500 --earlyStopping -1"
CON=(--constraints Bounds 'bkg_norm<=-0.3')

# 1. CI example configs (no constraints): untouched
CIMAP=(-m BaseMapping -m Select ch0 'x:rebin(-5,-2,2,5)' -m Project ch1 a -m Project ch1 b -m Project ch0_masked -m Normalize ch0 x)
for w in base new; do
  fit $w ci_nominal_$w $CI -t 0 --unblind --doImpacts --globalImpacts --saveHists --computeHistErrors "${CIMAP[@]}"
  fit $w ci_blinded_$w $CI -t 0 --setConstraintMinimum bkg_2_norm 0.5 --doImpacts --globalImpacts
  fit $w ci_toys_$w $CI -t 3 --unblind
  fit $w ci_satscan_$w $CI -t 0 --unblind --saveHists --computeSaturatedProjectionTests -m Project ch1 a --scan sig --scanPoints 5
done
cmp_ "CI nominal fit (impacts, mappings)" ci_nominal_base ci_nominal_new
cmp_ "CI blinded fit" ci_blinded_base ci_blinded_new
cmp_ "toys -t 3, default minimizer" ci_toys_base ci_toys_new
cmp_ "default minimizer: saturated test + scan" ci_satscan_base ci_satscan_new

# 2. trust-constr + constraints, cold: untouched
for w in base new; do fit $w tc_cold_$w $SM -t 0 $TC "${CON[@]}"; done
cmp_ "trust-constr+constraints cold fit" tc_cold_base tc_cold_new

# 3. --minimizerWarmStart off at every warm call site: untouched
for w in base new; do
  OFF=""; [ $w = new ] && OFF="--minimizerWarmStart off"
  fit $w tc_sat_off_$w $SM -t 0 $TC "${CON[@]}" --saveHists --computeSaturatedProjectionTests -m Project ch0 $OFF
  fit $w tc_ext_off_$w $SM -t 0 $TC "${CON[@]}" --externalPostfit $OUT/tc_cold_base/fitresults.hdf5 $OFF
  fit $w tc_scan_off_$w $SM -t 0 $TC "${CON[@]}" --scan sig --scanPoints 7 --scanRange 2 $OFF
  fit $w tc_toys_off_$w $SM -t 3 $TC "${CON[@]}" $OFF
done
cmp_ "off: saturated test" tc_sat_off_base tc_sat_off_new
cmp_ "off: --externalPostfit refit" tc_ext_off_base tc_ext_off_new
cmp_ "off: likelihood scan" tc_scan_off_base tc_scan_off_new
cmp_ "off: toys -t 3" tc_toys_off_base tc_toys_off_new

# 4. toys with trust-constr+constraints under the default auto (toys are cold): untouched
fit new tc_toys_auto_new $SM -t 3 $TC "${CON[@]}"
cmp_ "auto: toys -t 3 trust-constr+constraints" tc_toys_off_base tc_toys_auto_new

# 5. the warm call sites under auto: same answers (within the barrier gap), fewer iterations
fit new tc_sat_auto_new $SM -t 0 $TC "${CON[@]}" --saveHists --computeSaturatedProjectionTests -m Project ch0
fit new tc_ext_auto_new $SM -t 0 $TC "${CON[@]}" --externalPostfit $OUT/tc_cold_base/fitresults.hdf5
fit new tc_scan_auto_new $SM -t 0 $TC "${CON[@]}" --scan sig --scanPoints 7 --scanRange 2
cmp_ "auto vs before: saturated test (tol 1e-5)" tc_sat_off_base tc_sat_auto_new --atol 1e-5 --rtol 1e-5 --ignore meta time epoch minimizer_status
cmp_ "auto vs before: --externalPostfit refit (tol 1e-5)" tc_ext_off_base tc_ext_auto_new --atol 1e-5 --rtol 1e-5 --ignore meta time epoch minimizer_status
cmp_ "auto vs before: likelihood scan (tol 1e-5)" tc_scan_off_base tc_scan_auto_new --atol 1e-5 --rtol 1e-5 --ignore meta time epoch minimizer_status

# 6. scipy-internals guard: a warm-hinted fit with the guard failing is the cold fit
PYTHONPATH=$NEW:$PYTHONPATH python $HERE/check_guard.py "$SM" 2>&1 | grep "^\[check\]"
echo "[checks] $(date -Is) done"
