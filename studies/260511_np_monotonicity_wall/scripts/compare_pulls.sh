#!/bin/bash
# Compare postfit pulls between nominal+reg and nominal+reg+fakelumi.
# Highlight nuisances that change pull significantly when fakelumi is on —
# those are the systematics that absorb yield freedom alongside fakelumi.
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

python << 'PY'
import sys, os
sys.path.insert(0, '/home/submit/lavezzo/alphaS/main/WRemnants/rabbit')
sys.path.insert(0, '/home/submit/lavezzo/alphaS/main/WRemnants/wums')
from rabbit.io_tools import get_fitresult
import numpy as np

B = '/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall'
P = 'ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_'

FITS = {
    "nominal+reg":         f"{B}/{P}NPCS100pct/data_reg_satp/fitresults.hdf5",
    "nominal+reg+fakelumi": f"{B}/{P}NPCS100pct_fakelumi/data_reg_satp/fitresults.hdf5",
}

def read_parms(path):
    fr, _ = get_fitresult(path, meta=True)
    parms = fr['parms'].get()
    names = list(parms.axes[0])
    vals  = parms.values()
    errs  = np.sqrt(parms.variances())
    return {n: (float(vals[i]), float(errs[i])) for i, n in enumerate(names)}

a = read_parms(FITS["nominal+reg"])
b = read_parms(FITS["nominal+reg+fakelumi"])

common = sorted(set(a) & set(b))
rows = []
for n in common:
    ta, ea = a[n]; tb, eb = b[n]
    dt = tb - ta
    rows.append((n, ta, ea, tb, eb, dt))

# Skip the POI itself for the table (we know it shifted)
rows = [r for r in rows if r[0] != "pdfAlphaS"]

# Group 1: largest |pull| in either fit (|θ| > 0.5)
big_pull = sorted([r for r in rows if abs(r[1]) > 0.5 or abs(r[3]) > 0.5],
                  key=lambda r: -max(abs(r[1]), abs(r[3])))[:25]

# Group 2: largest |Δθ| between the two fits (shifted ≥ 0.3σ)
big_shift = sorted([r for r in rows if abs(r[5]) > 0.3],
                   key=lambda r: -abs(r[5]))[:25]

def fmt(r):
    n, ta, ea, tb, eb, dt = r
    return f"  {n:<60s} θ_noFL={ta:+.3f}±{ea:.3f}   θ_+FL={tb:+.3f}±{eb:.3f}   Δθ={dt:+.3f}"

print("=" * 100)
print("LARGE PULLS (|θ| > 0.5 in either fit)  — top 25")
print("=" * 100)
for r in big_pull:
    print(fmt(r))

print()
print("=" * 100)
print("LARGE SHIFT under fakelumi (|Δθ| > 0.3) — top 25")
print("=" * 100)
for r in big_shift:
    print(fmt(r))

# Quick category breakdown
print()
print("=" * 100)
print("Category breakdown of large shifts (|Δθ| > 0.3):")
print("=" * 100)
cats = {}
for r in big_shift:
    n = r[0]
    if "scetlibNP" in n: cat = "SCETlib NP"
    elif "resum" in n.lower() or "scetlib" in n.lower(): cat = "SCETlib resum"
    elif "minnlo" in n.lower() or "qcdscale" in n.lower(): cat = "QCD scale / MiNNLO"
    elif "pdf" in n.lower(): cat = "PDF"
    elif "muon" in n.lower() or "CMS_eff" in n or "CMS_recoil" in n: cat = "Detector / muon"
    elif "fake" in n.lower(): cat = "Fakelumi / fake"
    elif "ew" in n.lower() or "renesance" in n.lower() or "horace" in n.lower(): cat = "EW / FSR"
    elif "mass" in n.lower() or "width" in n.lower() or "weak" in n.lower() or "sin2" in n.lower(): cat = "Z props"
    elif "tnp" in n.lower(): cat = "TNP"
    else: cat = "other"
    cats.setdefault(cat, []).append(r[0])
for c, ns in sorted(cats.items(), key=lambda x: -len(x[1])):
    print(f"  {c}: {len(ns)} nuisances")
    for n in ns[:5]:
        print(f"     - {n}")
PY
echo "DONE_OK"
