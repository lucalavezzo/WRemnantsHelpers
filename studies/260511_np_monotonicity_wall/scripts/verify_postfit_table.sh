#!/bin/bash
# Inside-container verification: print raw postfit θ and independently
# recompute physical lambda values, cross-checking against the table.
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

python << 'PY'
import sys, json
sys.path.insert(0, '/home/submit/lavezzo/alphaS/main/WRemnants/rabbit')
sys.path.insert(0, '/home/submit/lavezzo/alphaS/main/WRemnants/wums')
from rabbit.io_tools import get_fitresult
import numpy as np

with open('/home/submit/lavezzo/alphaS/WRemnantsHelpers/scripts/np_param_map.json') as f:
    PMAP = json.load(f)

BASE = '/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall'
CONFIGS = [
    # (label, path, kfactors)
    ('nominal', f'{BASE}/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_NPCS100pct/data/fitresults.hdf5',
       {'scetlibNPgammaLambda2':2.62,'scetlibNPgammaLambda4':1.12,'scetlibNPgammaLambdaInf':3.33}),
    ('inflatedV2', f'{BASE}/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_NPCS100pctV2/fitresults.hdf5',
       {'scetlibNPgammaLambda2':4.32,'scetlibNPgammaLambda4':1.12,'scetlibNPgammaLambdaInf':3.33,'chargeVgenNP0scetlibNPZlambda4':1.55}),
    ('inflate2x', f'{BASE}/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_Inflate2x/fitresults.hdf5',
       {'scetlibNPgammaLambda2':5.24,'scetlibNPgammaLambda4':2.24,'scetlibNPgammaLambdaInf':3.33,'chargeVgenNP0scetlibNPZlambda2':2.0,'chargeVgenNP0scetlibNPZdelta_lambda2':2.0,'chargeVgenNP0scetlibNPZlambda4':2.0}),
    ('inflate3x', f'{BASE}/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_Inflate3x/fitresults.hdf5',
       {'scetlibNPgammaLambda2':7.86,'scetlibNPgammaLambda4':3.36,'scetlibNPgammaLambdaInf':3.33,'chargeVgenNP0scetlibNPZlambda2':3.0,'chargeVgenNP0scetlibNPZdelta_lambda2':3.0,'chargeVgenNP0scetlibNPZlambda4':3.0}),
    ('inflate5x', f'{BASE}/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_Inflate5x/fitresults.hdf5',
       {'scetlibNPgammaLambda2':13.1,'scetlibNPgammaLambda4':5.60,'scetlibNPgammaLambdaInf':3.33,'chargeVgenNP0scetlibNPZlambda2':5.0,'chargeVgenNP0scetlibNPZdelta_lambda2':5.0,'chargeVgenNP0scetlibNPZlambda4':5.0}),
    ('unconstrained', f'{BASE}/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_NPUnconstrained/data_lrscan/fitresults.hdf5', {}),
]

NUIS = list(PMAP['nuisances'].keys())

def phys(nuis, theta, sigma, k=1.0):
    info = PMAP['nuisances'][nuis]
    nom = info['nominal']
    up = info['Up_template_value']
    dn = info['Down_template_value']
    d_up = (up - nom) * k
    d_dn = (nom - dn) * k
    val = nom + max(theta, 0)*d_up - max(-theta, 0)*d_dn
    slope = d_up if theta >= 0 else d_dn
    return val, abs(slope)*sigma

for lab, path, kfacs in CONFIGS:
    print(f"\n=== {lab}  ({path}) ===")
    try:
        fr, _ = get_fitresult(path, meta=True)
        parms = fr['parms'].get()
        names = list(parms.axes[0])
    except Exception as e:
        print(f"  FAILED to read: {e}")
        continue
    for nuis in NUIS:
        info = PMAP['nuisances'][nuis]
        if nuis not in names:
            print(f"  {info['param_AN']:<16s} NOT FOUND")
            continue
        i = names.index(nuis)
        theta = float(parms.values()[i])
        err = float(np.sqrt(parms.variances()[i]))
        k = kfacs.get(nuis, 1.0)
        v, ve = phys(nuis, theta, err, k=k)
        # Sanity: theta=+1 should give v = nom + k*(Up-nom); theta=-1 should give v = nom - k*(nom-Dn)
        v_plus1 = info['nominal'] + k*(info['Up_template_value']-info['nominal'])
        v_minus1 = info['nominal'] - k*(info['nominal']-info['Down_template_value'])
        print(f"  {info['param_AN']:<16s} θ={theta:+.4f}±{err:.4f}  k={k:<5}  → phys={v:+.4f}±{ve:.4f}   [check: θ=+1→{v_plus1:+.4f}, θ=-1→{v_minus1:+.4f}; nom={info['nominal']:.4f}]")
PY
echo "DONE_OK $(date)"
