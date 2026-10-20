#!/usr/bin/env bash
# PR #194 checks CI does not cover: run the same rabbit_fit.py configs with WMass/rabbit main (2d9f380) and with the PR
# (c76c226), each from its own worktree, and compare the outputs (compare_results.py). Runs INSIDE the container.
set -f
MAIN=/work/submit/lavezzo/rabbit-main-2d9f380
PR=/work/submit/lavezzo/rabbit-tc-precond-val
O=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261017_pr_validation/checks
mkdir -p $O/main $O/pr $O/tensors
cd $O
# test tensors exactly as CI makes them (from the PR tree: tests/make_tensor.py is unchanged by the PR)
PYTHONPATH=$PR:$PYTHONPATH python $PR/tests/make_tensor.py -o $O/tensors/ > $O/make_tensor.log 2>&1 || { echo make_tensor failed; exit 1; }
PYTHONPATH=$PR:$PYTHONPATH python -c "
import sys; sys.path.insert(0, '$PR')
from tests.test_preconditioner import make_polynomial_tensor
print(make_polynomial_tensor('$O/tensors', order=8))" >> $O/make_tensor.log 2>&1
TT=$O/tensors/test_tensor.hdf5
TP=$O/tensors/test_poly.hdf5
PC="--precondition --preconditionParams .* --preconditionBlocks none --preconditionTransform spectral"
TC="--minimizerMethod trust-constr --earlyStopping -1 --maxRestarts 0 --minimizerGtol 1e-10 --minimizerXtol 1e-10 --minimizerBarrierTol 1e-10 --minimizerMaxiter 500"
CI_NOMINAL="-t 0 --unblind --doImpacts --globalImpacts --saveHists --saveHistsPerProcess --computeHistErrors --computeHistErrorsPerProcess --computeHistCov --computeHistImpacts --computeVariations -m BaseMapping -m Project ch1 a -m Project ch1 b -m Project ch0_masked -m Normalize ch0 x"
run() {  # tree label postfix tensor args...
  local tree=$1 lab=$2 pf=$3 ten=$4; shift 4
  ( export PYTHONPATH=$tree:$PYTHONPATH; python $tree/bin/rabbit_fit.py $ten -o $O/$lab --postfix $pf "$@" > $O/$lab/$pf.log 2>&1; echo "$lab $pf rc=$?" )
}
for side in main:$MAIN pr:$PR; do
  lab=${side%%:*}; tree=${side#*:}
  # (a) unconstrained trust-krylov, CI nominal config, without and with the full-scope spectral preconditioner
  run $tree $lab A0_ci_nominal $TT $CI_NOMINAL
  run $tree $lab A1_ci_nominal_pc $TT $CI_NOMINAL $PC
  # (a) penalty term (-r) + preconditioner under trust-krylov: CI regularization config (without the L-curve scan)
  run $tree $lab A2_svd_reg_pc $TT -t 0 --unblind -r SVD Select ch0_masked --saveHists $PC
  # (a) the ill-conditioned polynomial toy, preconditioned, trust-krylov
  run $tree $lab A3_poly_pc $TP -t 0 --unblind --saveHists $PC
  # (b) trust-constr WITHOUT --precondition, binding bound, with the saturated projection test
  run $tree $lab B0_tc_bound $TT -t 0 --unblind --saveHists -m Project ch1 a --computeSaturatedProjectionTests $TC --constraints Bounds 'bkg_2_norm<=-0.2'
done
# (e) face-held post-fit under the transform: PR only, trust-constr + binding bound WITH the preconditioner
run $PR pr E1_tc_bound_pc $TT -t 0 --unblind --saveHists -m Project ch1 a --computeSaturatedProjectionTests $TC --constraints Bounds 'bkg_2_norm<=-0.2' $PC
# (d) multi-device: constraints + preconditioner + --nDevices 2 must be refused up front
run $PR pr D1_multidevice $TT -t 0 $TC --nDevices 2 --constraints Bounds 'bkg_2_norm<=-0.2' $PC
