#!/bin/bash
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

python << 'PY'
import sys, h5py
sys.path.insert(0, '/home/submit/lavezzo/alphaS/main/WRemnants/rabbit')
sys.path.insert(0, '/home/submit/lavezzo/alphaS/main/WRemnants/wums')
from rabbit.io_tools import get_fitresult
import numpy as np

BASE = '/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall'
FITS = [
    ('Inflate2x_reg5',         f'{BASE}/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_Inflate2x_reg5/fitresults.hdf5'),
    ('Inflate3x_reg5',         f'{BASE}/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_Inflate3x_reg5/fitresults.hdf5'),
    ('Inflate5x_reg5',         f'{BASE}/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_Inflate5x_reg5/fitresults.hdf5'),
    ('NPUnconstrained/data_tau5', f'{BASE}/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_NPUnconstrained/data_tau5/fitresults.hdf5'),
    ('NPUnconstrained/data_lrscan', f'{BASE}/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_NPUnconstrained/data_lrscan/fitresults.hdf5'),
]

for lab, path in FITS:
    print(f"\n=== {lab} ===")
    # Inspect raw h5 keys to find tau
    try:
        with h5py.File(path, 'r') as h:
            def walk(g, depth=0):
                if depth > 3: return
                for k in g.keys():
                    try:
                        if isinstance(g[k], h5py.Dataset):
                            if 'tau' in k.lower() or 'reg' in k.lower() or 'penal' in k.lower():
                                v = g[k][()]
                                shape = getattr(v, 'shape', None)
                                if shape is None or (hasattr(shape, '__len__') and len(shape) == 0):
                                    print(f"   {g.name}/{k} = {v}")
                                else:
                                    print(f"   {g.name}/{k}  shape={shape}")
                        else:
                            walk(g[k], depth+1)
                    except Exception as e:
                        pass
            walk(h)
    except Exception as e:
        print(f"   h5 walk failed: {e}")
    try:
        fr, meta = get_fitresult(path, meta=True)
        # try common rabbit keys
        for key in ('tau', 'regularizationStrength', 'penalty', 'nll_penalty', 'lpenalty', 'nllvalreduced'):
            if key in fr:
                v = fr[key].get() if hasattr(fr[key], 'get') else fr[key]
                print(f"   fr[{key}] = {v}")
        # Also try printing all top-level keys
        print(f"   top-level fr keys: {list(fr.keys())}")
    except Exception as e:
        print(f"   get_fitresult failed: {e}")
PY
echo "DONE_OK"
