#!/bin/bash
# Diff postfit pulls between 4D nominal and 2D ptll-yll nominal.
# Nuisances with large |Δθ| are the ones that the angular observables
# (cosθ*, phi*) shift when added to the fit. Combined with the α_S
# correlation matrix (small but nonzero ρ for many helicity-coeff and
# detector nuisances), these are the candidates that mediate the α_S
# central-value shift between 2D and 4D.
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

B = '/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall'
FITS = {
    "2D ptll-yll": f"{B}/ZMassDilepton_ptll_yll_NPCS100pct_2D_ptll_yll/data_satp/fitresults.hdf5",
    "4D":          f"{B}/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_NPCS100pct/fitresults.hdf5",
}
def read_parms(path):
    fr, _ = get_fitresult(path, meta=True)
    parms = fr['parms'].get()
    names = list(parms.axes[0])
    vals  = parms.values()
    errs  = np.sqrt(parms.variances())
    return {n: (float(vals[i]), float(errs[i])) for i, n in enumerate(names)}

a = read_parms(FITS["2D ptll-yll"])
b = read_parms(FITS["4D"])
common = sorted(set(a) & set(b))
rows = []
for n in common:
    if n == "pdfAlphaS":
        continue
    ta, ea = a[n]; tb, eb = b[n]
    dt = tb - ta
    rows.append((n, ta, ea, tb, eb, dt))

rows.sort(key=lambda r: -abs(r[5]))
print("=" * 110)
print(f"{'Nuisance':<60s}   θ(2D)        θ(4D)          Δθ(4D - 2D)")
print("=" * 110)
print()
print("Top 30 by |Δθ| between adding cosθ* and phi* (4D − 2D ptll-yll):")
for r in rows[:30]:
    n, ta, ea, tb, eb, dt = r
    flag = ' ←' if abs(dt) > 0.5 else ''
    print(f"  {n:<60s}  {ta:+.3f}±{ea:.3f}   {tb:+.3f}±{eb:.3f}   {dt:+.3f}{flag}")

# Category breakdown of large shifts
print()
print("=" * 110)
print("Category breakdown of |Δθ| > 0.3:")
print("=" * 110)
big = [r for r in rows if abs(r[5]) > 0.3]
cats = {}
for r in big:
    n = r[0]
    nl = n.lower()
    if "scetlibNPgamma" in n or "ZNP" in n or "scetlibNPZ" in n: cat = "SCETlib NP"
    elif "qcdscale" in nl and "helicity" in nl: cat = "QCDscaleZ helicity"
    elif "qcdscale" in nl: cat = "QCDscale other"
    elif "resum" in nl or "scetlib" in nl: cat = "SCETlib resum / TNP"
    elif "pdf" in nl or "mb_" in nl or "mc_" in nl: cat = "PDF / m_b / m_c"
    elif "effsyst" in nl or "tnp" in nl: cat = "Eff/TNP"
    elif "scale_correction" in nl or "resolution_correction" in nl or "pixel_multiplicity" in nl or "muon" in nl: cat = "Muon scale/resolution"
    elif "prefire" in nl: cat = "Prefire"
    elif "ew" in nl or "renesance" in nl or "horace" in nl or "pythia" in nl: cat = "EW / FSR / ISR"
    elif "mass" in nl or "width" in nl or "weak" in nl or "sin2" in nl: cat = "Z props / EW"
    elif "fake" in nl: cat = "Fake / fakelumi"
    elif "lumi" in nl: cat = "Lumi"
    elif "ch0" in nl or "channel" in nl: cat = "Channel"
    elif n.startswith("BBB"): cat = "BBB"
    else: cat = "other"
    cats.setdefault(cat, []).append((n, r[5]))

for c, nuis in sorted(cats.items(), key=lambda x: -len(x[1])):
    print(f"\n  {c}: {len(nuis)} nuisances")
    nuis.sort(key=lambda x: -abs(x[1]))
    for n, dt in nuis[:6]:
        print(f"     Δθ={dt:+.3f}  {n}")
PY
echo "DONE_OK"
