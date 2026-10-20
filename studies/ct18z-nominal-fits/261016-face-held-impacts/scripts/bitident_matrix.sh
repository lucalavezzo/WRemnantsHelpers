#!/bin/bash
# PR #196: fits WITHOUT an active face must be bit-identical to WMass main (2d9f380).
# Runs rabbit_fit with the main checkout and the PR branch on the rabbit test tensors over a matrix of
# configurations (bbstat lite/full/off, dense/sparse, --chisqFit, no constraints / inactive constraint) with
# every impact flavour + hist errors, and compares every output (hists incl. variances, dict leaves).
# --chisqFit is NOT run-to-run deterministic even on main (two main runs differ), so it is compared with a
# tolerance (max relative difference of every impact hist) and against a second main run.
# Usage (inside the container): bitident_matrix.sh <workdir>
set -e
W=$1; mkdir -p $W; cd $W
BASE=/work/submit/lavezzo/rabbit-main-2d9f380
NEW=/work/submit/lavezzo/rabbit-face-impacts
echo "base $(git -C $BASE rev-parse --short HEAD)  new $(git -C $NEW rev-parse --short HEAD)"
PYTHONPATH=$NEW:$PYTHONPATH python -c "
import sys; sys.path.insert(0, '$NEW')
from tests.test_sparse_fit import make_test_tensor
print(make_test_tensor('$W')); print(make_test_tensor('$W', sparse=True))" > /dev/null
TC="--minimizerMethod trust-constr --minimizerGtol 1e-10 --minimizerXtol 1e-10 --minimizerBarrierTol 1e-10 --minimizerMaxiter 500"
IMP="--doImpacts --globalImpacts --gaussianGlobalImpacts --saveHists --computeHistErrors --computeHistImpacts"
declare -A CFG=(
  [lite]="test_dense.hdf5"
  [full]="test_dense.hdf5 --binByBinStatMode full"
  [nobbb]="test_dense.hdf5 --noBinByBinStat"
  [sparse]="test_sparse.hdf5 --globalImpactsDisableJVP"  # JVP global impacts crash on sparse on main too
  [chisq]="test_dense.hdf5 --chisqFit"
  [inactive]="test_dense.hdf5 $TC --constraints Bounds bkg_norm<=5"
  [inactive_nobbb]="test_dense.hdf5 --noBinByBinStat $TC --constraints Bounds bkg_norm<=5"
)
for c in "${!CFG[@]}"; do
  for tag in base new; do
    R=$BASE; [ $tag = new ] && R=$NEW
    set -f
    PYTHONPATH=$R:$PYTHONPATH python $R/bin/rabbit_fit.py $W/${CFG[$c]} -o $W/$tag -t 0 --postfix $c $IMP > $W/$tag.$c.log 2>&1 \
      || echo "FAIL $tag $c (see $W/$tag.$c.log)"
    set +f
  done
done
set -f; PYTHONPATH=$BASE:$PYTHONPATH python $BASE/bin/rabbit_fit.py $W/${CFG[chisq]} -o $W/base2 -t 0 --postfix chisq $IMP > $W/base2.chisq.log 2>&1; set +f
PYTHONPATH=$NEW:$PYTHONPATH python - <<PY
import numpy as np
from rabbit import io_tools
def walk(a, b, path, bad, n):
    if isinstance(a, dict):
        if set(a) != set(b): bad.append(path + " keys"); return
        for k in a: walk(a[k], b[k], path + "/" + str(k), bad, n)
    elif hasattr(a, "get"):
        ha, hb = a.get(), b.get(); n[0] += 1
        ok = np.array_equal(ha.values(), hb.values(), equal_nan=True)
        if ha.variances() is not None:
            ok &= np.array_equal(ha.variances(), hb.variances(), equal_nan=True)
        if not ok: bad.append(path)
    else:
        n[0] += 1
        if repr(a) != repr(b): bad.append(path)
for c in sorted("${!CFG[@]}".split()):
    a = io_tools.get_fitresult("$W/base/fitresults_%s.hdf5" % c)
    b = io_tools.get_fitresult("$W/new/fitresults_%s.hdf5" % c)
    a.pop("epoch_time", None); b.pop("epoch_time", None)
    bad, n = [], [0]
    walk(dict(a), dict(b), "", bad, n)
    imp = sorted(k for k in a if "impacts" in k)
    print(f"{c:16s} leaves {n[0]:4d}  impact hists {len(imp):2d}  non-identical: {len(bad) if bad else 'none'}")
    if c == "chisq":
        a2 = io_tools.get_fitresult("$W/base2/fitresults_chisq.hdf5")
        def mrd(x, y):
            vx, vy = x.get().values(), y.get().values()
            return float(np.max(np.abs(vx - vy) / np.maximum(np.abs(vy), 1e-300)))
        for k in imp + ["cov"]:
            print(f"    chisq {k:32s} max rel diff new-vs-main {mrd(b[k], a[k]):.1e}   main-vs-main {mrd(a2[k], a[k]):.1e}")
PY
