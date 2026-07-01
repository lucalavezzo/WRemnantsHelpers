#!/bin/bash
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

python << 'PY'
import os, sys, json
sys.path.insert(0,'/home/submit/lavezzo/alphaS/main/WRemnants/rabbit')
sys.path.insert(0,'/home/submit/lavezzo/alphaS/main/WRemnants/wums')
from rabbit.io_tools import get_fitresult
from scipy.stats import chi2 as chi2_dist
import numpy as np

with open('/home/submit/lavezzo/alphaS/WRemnantsHelpers/scripts/np_param_map.json') as f:
    PMAP = json.load(f)

BASE='/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall'
CONFIGS=[
    # label,                kfactors (per nuisance) for physical-value mapping
    ('NPCS100pct',          {'scetlibNPgammaLambda2':2.62,'scetlibNPgammaLambda4':1.12,'scetlibNPgammaLambdaInf':3.33}),
    ('NPUnconstrained',     {}),
    ('Inflate5x_reg5',      {'scetlibNPgammaLambda2':13.1,'scetlibNPgammaLambda4':5.60,'scetlibNPgammaLambdaInf':3.33,
                             'chargeVgenNP0scetlibNPZlambda2':5.0,'chargeVgenNP0scetlibNPZdelta_lambda2':5.0,'chargeVgenNP0scetlibNPZlambda4':5.0}),
]
NPS=list(PMAP['nuisances'].keys())

def phys(nuis, theta, sigma, k=1.0):
    info=PMAP['nuisances'][nuis]; nom=info['nominal']; up=info['Up_template_value']; dn=info['Down_template_value']
    d_up=(up-nom)*k; d_dn=(nom-dn)*k
    val=nom + max(theta,0)*d_up - max(-theta,0)*d_dn
    slope=d_up if theta>=0 else d_dn
    return val, abs(slope)*sigma

for obs in ('ptll','yll'):
    print(f"\n========= 1D {obs}-only ============")
    print(f"{'Config':<22} {'γ_Λ2':>16} {'γ_Λ4':>16} {'Λ2':>14} {'ΔΛ2':>14} {'Λ4':>14} {'sat-p':>9} {'σ_αS':>10}")
    for lab, kf in CONFIGS:
        path=f'{BASE}/ZMassDilepton_{obs}_{lab}_{obs}only/data/fitresults.hdf5'
        if not os.path.exists(path):
            print(f"{lab:<22}  <missing>")
            continue
        fr,_=get_fitresult(path, meta=True)
        parms=fr['parms'].get(); names=list(parms.axes[0])
        # alphaS
        ia=names.index('pdfAlphaS')
        a=float(parms.values()[ia]); ae=float(np.sqrt(parms.variances()[ia]))
        # sat-p
        nllv=float(fr['nllvalreduced'].get()) if hasattr(fr['nllvalreduced'], 'get') else float(fr['nllvalreduced'][()])
        ndf=int(fr['ndfsat'].get()) if hasattr(fr['ndfsat'], 'get') else int(fr['ndfsat'][()])
        chi2v=2.0*nllv; sp=chi2_dist.sf(chi2v, ndf)*100
        # NP values (skip λ_∞ which is mostly frozen)
        cells=[]
        for nuis in ('scetlibNPgammaLambda2','scetlibNPgammaLambda4','chargeVgenNP0scetlibNPZlambda2','chargeVgenNP0scetlibNPZdelta_lambda2','chargeVgenNP0scetlibNPZlambda4'):
            if nuis not in names:
                cells.append('---'); continue
            i=names.index(nuis); th=float(parms.values()[i]); te=float(np.sqrt(parms.variances()[i]))
            k=kf.get(nuis,1.0); v,ve=phys(nuis,th,te,k=k)
            cells.append(f"{v:+.4f}±{ve:.4f}")
        sigma_aS=ae*2  # in 10^-3 AN units
        print(f"{lab:<22} {cells[0]:>16} {cells[1]:>16} {cells[2]:>14} {cells[3]:>14} {cells[4]:>14} {sp:>7.2f}% {sigma_aS:>9.4f}")
PY
echo "DONE_OK"
