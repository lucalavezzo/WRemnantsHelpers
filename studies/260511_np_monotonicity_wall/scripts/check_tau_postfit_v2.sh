#!/bin/bash
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

python << 'PY'
import sys
sys.path.insert(0, '/home/submit/lavezzo/alphaS/main/WRemnants/rabbit')
sys.path.insert(0, '/home/submit/lavezzo/alphaS/main/WRemnants/wums')
from rabbit.io_tools import get_fitresult
import numpy as np

BASE = '/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall'
FITS = [
    ('Inflate2x_reg5',         f'{BASE}/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_Inflate2x_reg5/fitresults.hdf5'),
    ('Inflate5x_reg5',         f'{BASE}/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_Inflate5x_reg5/fitresults.hdf5'),
    ('NPUnconstrained/data_tau5', f'{BASE}/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_NPUnconstrained/data_tau5/fitresults.hdf5'),
    ('NPUnconstrained/data_lrscan', f'{BASE}/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_NPUnconstrained/data_lrscan/fitresults.hdf5'),
]

for lab, path in FITS:
    print(f"\n=== {lab} ===")
    fr, _ = get_fitresult(path, meta=True)
    parms = fr['parms'].get()
    names = list(parms.axes[0])
    # search for tau-like names
    matches = [n for n in names if 'tau' in n.lower() or 'reg' in n.lower() or 'penal' in n.lower()]
    print(f"  tau/reg-like names: {matches}")
    print(f"  total parms: {len(names)}")
    # also try parms_prefit
    try:
        pre = fr['parms_prefit'].get()
        prenames = list(pre.axes[0])
        prematches = [n for n in prenames if 'tau' in n.lower()]
        print(f"  parms_prefit tau-like: {prematches}")
    except Exception as e:
        print(f"  parms_prefit error: {e}")
    # print first/last few names
    print(f"  first 5 names: {names[:5]}")
    print(f"  last  5 names: {names[-5:]}")
PY
echo "DONE_OK"
