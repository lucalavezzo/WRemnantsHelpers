#!/bin/bash
# Diff the α_S↔nuisance correlations between 2D (ptll-yll) and 4D (full)
# nominal fits. Nuisances with large |Δρ| are the ones whose α_S coupling
# changes when the angular observables (cosθ*, φ*) are added to the fit —
# i.e., the candidates that mediate the angular-observable α_S shift.
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
    "4D":          f"{B}/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_NPCS100pct/fitresults.hdf5",
    "2D ptll-yll": f"{B}/ZMassDilepton_ptll_yll_NPCS100pct_2D_ptll_yll/data_satp/fitresults.hdf5",
}

def aS_corr(path):
    fr, _ = get_fitresult(path, meta=True)
    cov_h = fr['cov'].get()
    names = list(cov_h.axes[0])
    cov = cov_h.values()
    if "pdfAlphaS" not in names:
        raise SystemExit(f"pdfAlphaS not in cov for {path}")
    i = names.index("pdfAlphaS")
    sd = np.sqrt(np.diag(cov))
    # Avoid div0 for frozen params
    sd_safe = np.where(sd > 0, sd, 1.0)
    corr_row = cov[i] / (sd[i] * sd_safe)
    corr_row = np.where(sd == 0, 0.0, corr_row)
    return dict(zip(names, corr_row))

c4 = aS_corr(FITS["4D"])
c2 = aS_corr(FITS["2D ptll-yll"])

common = sorted(set(c4) & set(c2))
rows = []
for n in common:
    if n == "pdfAlphaS":
        continue
    rho4 = c4[n]; rho2 = c2[n]
    drho = rho4 - rho2
    rows.append((n, rho2, rho4, drho))

# Sort by |Δρ| descending
rows.sort(key=lambda r: -abs(r[3]))

print("=" * 100)
print(f"{'Nuisance':<60s}  ρ(2D)   ρ(4D)   Δρ(4D-2D)")
print("=" * 100)
print()
print("Largest |Δρ(α_S, x)| under adding cosθ* and phi* on top of 2D ptll-yll (top 30):")
for n, r2, r4, dr in rows[:30]:
    flag = '  ←' if abs(dr) > 0.3 else ''
    print(f"  {n:<60s}  {r2:+.3f}  {r4:+.3f}  {dr:+.3f}{flag}")

print()
print("=" * 100)
print("Largest |ρ(α_S, x)| in 4D fit (top 20, for context):")
print("=" * 100)
rows_by_abs4D = sorted(rows, key=lambda r: -abs(r[2]))[:20]
for n, r2, r4, dr in rows_by_abs4D:
    print(f"  {n:<60s}  ρ_2D={r2:+.3f}  ρ_4D={r4:+.3f}  Δρ={dr:+.3f}")
PY
echo "DONE_OK"
