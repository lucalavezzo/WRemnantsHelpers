#!/bin/bash
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

python << 'PY'
import os, sys, json
# Bypass HDF5 advisory locking so we can read a file the running rabbit_fit may
# also have open. Read-only and within the container only.
os.environ.setdefault('HDF5_USE_FILE_LOCKING', 'FALSE')
sys.path.insert(0, '/home/submit/lavezzo/alphaS/main/WRemnants/rabbit')
sys.path.insert(0, '/home/submit/lavezzo/alphaS/main/WRemnants/wums')
from rabbit.io_tools import get_fitresult
from scipy.stats import chi2 as chi2_dist
import numpy as np

with open('/home/submit/lavezzo/alphaS/WRemnantsHelpers/scripts/np_param_map.json') as f:
    PMAP = json.load(f)

path = '/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_Inflate2x_reg5/data_lrscan/fitresults.hdf5'
fr, _ = get_fitresult(path, meta=True)
parms = fr['parms'].get()
names = list(parms.axes[0])

# inflate2x kfactors (from build_compare_table.py KFACTOR_OVERRIDES)
KFAC = {
    'scetlibNPgammaLambda2':5.24,'scetlibNPgammaLambda4':2.24,'scetlibNPgammaLambdaInf':3.33,
    'chargeVgenNP0scetlibNPZlambda2':2.0,'chargeVgenNP0scetlibNPZdelta_lambda2':2.0,'chargeVgenNP0scetlibNPZlambda4':2.0,
}

def phys(nuis, theta, sigma, k=1.0):
    info = PMAP['nuisances'][nuis]
    nom, up, dn = info['nominal'], info['Up_template_value'], info['Down_template_value']
    d_up = (up - nom) * k
    d_dn = (nom - dn) * k
    val = nom + max(theta, 0)*d_up - max(-theta, 0)*d_dn
    slope = d_up if theta >= 0 else d_dn
    return val, abs(slope)*sigma

NPS = ['scetlibNPgammaLambda2','scetlibNPgammaLambda4','scetlibNPgammaLambdaInf',
       'chargeVgenNP0scetlibNPZlambda2','chargeVgenNP0scetlibNPZdelta_lambda2','chargeVgenNP0scetlibNPZlambda4']

print("\n=== Inflate2x_reg5 (kfactor-aware) postfit ===")
print(f"Path: {path}")
for nuis in NPS:
    i = names.index(nuis)
    theta = float(parms.values()[i])
    err = float(np.sqrt(parms.variances()[i]))
    k = KFAC.get(nuis, 1.0)
    v, ve = phys(nuis, theta, err, k=k)
    info = PMAP['nuisances'][nuis]
    print(f"  {info['param_AN']:<16s} θ={theta:+.4f}±{err:.4f}  k={k:<5}  → phys={v:+.4f}±{ve:.4f}")

# alphaS pull
i = names.index('pdfAlphaS')
a_val = float(parms.values()[i])
a_err = float(np.sqrt(parms.variances()[i]))
print(f"\n  pdfAlphaS θ={a_val:+.4f}±{a_err:.4f}  (Hessian σ; reg row → not to be quoted)")

# LR scan σ
def sigma_from_scan(h):
    ax = h.axes[0]
    xs = np.array([0.5*(ax.edges[i]+ax.edges[i+1]) for i in range(len(ax.edges)-1)])
    ys = h.values()
    ymin_i = int(np.argmin(ys))
    y2 = 2.0*(ys - ys[ymin_i])
    xmin = xs[ymin_i]
    def cross(xx, yy, t):
        yy = yy - t
        for i in range(len(yy)-1):
            if yy[i]*yy[i+1] < 0:
                return xx[i] + (xx[i+1]-xx[i])*(-yy[i])/(yy[i+1]-yy[i])
        return None
    xL = cross(xs[:ymin_i+1][::-1], y2[:ymin_i+1][::-1], 1.0)
    xR = cross(xs[ymin_i:], y2[ymin_i:], 1.0)
    if xL is None or xR is None: return None
    return 0.5*((xmin - xL) + (xR - xmin))

if 'nll_scan_pdfAlphaS' in fr:
    h = fr['nll_scan_pdfAlphaS'].get()
    sig_scan = sigma_from_scan(h)
    print(f"  pdfAlphaS LR-scan σ = {sig_scan:.4f}  →  σ_αS × 2 = {sig_scan*2:.4f}  [×10^-3]")
else:
    print("  NO LR scan in this file")

# ptll-projection saturated p-value
print()
if 'mappings' in fr:
    try:
        m = fr['mappings']['Project ch0 ptll']
        cs = float(m['chi2_saturated']); n = float(m['ndf'])
        p = chi2_dist.sf(cs, n)*100
        print(f"  Project ch0 ptll: chi2={cs:.3f}, ndf={n:.0f}, sat-p = {p:.2f}%")
    except (KeyError, TypeError) as e:
        print(f"  ptll mapping read error: {e}")
        print(f"  mappings keys: {list(fr['mappings'].keys())}")
else:
    print("  NO mappings in this file")
PY
echo "DONE_OK"
