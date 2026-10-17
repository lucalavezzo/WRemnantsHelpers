#!/bin/bash
# Inactive-face / no-constraint fits must be bit-identical between production rabbit (2d9f380+196bfca)
# and the face-held-impacts branch. Runs rabbit_fit on the rabbit test tensor with each checkout and
# compares every dataset of the fitresults. Usage (inside the container): bitident_check.sh <workdir>
set -e
W=$1; mkdir -p $W; cd $W
PROD=/home/submit/lavezzo/alphaS/WRemnants/rabbit
NEW=/work/submit/lavezzo/rabbit-face-impacts
PYTHONPATH=$NEW:$PYTHONPATH python -c "
import sys; sys.path.insert(0, '$NEW')
from tests.test_sparse_fit import make_test_tensor
print(make_test_tensor('$W'))"
TC="--minimizerMethod trust-constr --minimizerGtol 1e-10 --minimizerXtol 1e-10 --minimizerBarrierTol 1e-10 --minimizerMaxiter 500"
IMP="--doImpacts --globalImpacts --gaussianGlobalImpacts --saveHists --computeHistErrors"
for tag in prod new; do
  R=$PROD; [ $tag = new ] && R=$NEW
  PYTHONPATH=$R:$PYTHONPATH python $R/bin/rabbit_fit.py $W/test_dense.hdf5 -o $W/$tag -t 0 --postfix plain $IMP > $W/$tag.plain.log 2>&1
  PYTHONPATH=$R:$PYTHONPATH python $R/bin/rabbit_fit.py $W/test_dense.hdf5 -o $W/$tag -t 0 --postfix inactive $IMP $TC \
      --constraints Bounds 'bkg_norm<=5' > $W/$tag.inactive.log 2>&1
done
python - <<PY
import h5py, numpy as np
from rabbit import io_tools
for post in ("plain", "inactive"):
    a = io_tools.get_fitresult("$W/prod/fitresults_%s.hdf5" % post)
    b = io_tools.get_fitresult("$W/new/fitresults_%s.hdf5" % post)
    keys = sorted(set(a) | set(b))
    bad = []
    for k in keys:
        if k not in a or k not in b:
            bad.append((k, "missing")); continue
        va, vb = a[k], b[k]
        if hasattr(va, "get") and not isinstance(va, dict):
            ha, hb = va.get(), vb.get()
            same = np.array_equal(ha.values(), hb.values(), equal_nan=True) and (
                ha.variances() is None or np.array_equal(ha.variances(), hb.variances(), equal_nan=True))
        else:
            same = repr(va) == repr(vb)
        if not same:
            bad.append((k, "differs"))
    print(post, "datasets:", len(keys), "non-identical:", bad)
PY
