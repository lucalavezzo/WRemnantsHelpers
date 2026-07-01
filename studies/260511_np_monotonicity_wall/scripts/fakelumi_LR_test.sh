#!/bin/bash
# Likelihood-ratio test for fakelumi as nested-parameter:
#   2 * (NLL_no_fakelumi − NLL_with_fakelumi) ~ χ²₁
# Large value → adding fakelumi (1 extra free parameter) significantly
# improves the fit, i.e. the data wants a yield pull away from the prior.
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

python << 'PY'
import sys
sys.path.insert(0, '/home/submit/lavezzo/alphaS/main/WRemnants/rabbit')
sys.path.insert(0, '/home/submit/lavezzo/alphaS/main/WRemnants/wums')
from rabbit.io_tools import get_fitresult
from scipy.stats import chi2 as chi2_dist
import numpy as np

B = '/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260511_npwall'
P = 'ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_'

# (label, no-fakelumi path, with-fakelumi path)
PAIRS = [
    ("nominal (4D, no reg)",       f"{B}/{P}NPCS100pct/fitresults.hdf5",
                                   f"{B}/{P}NPCS100pct_fakelumi/data_satp/fitresults.hdf5"),
    ("nominal + reg (4D)",         f"{B}/{P}NPCS100pct/data_reg_satp/fitresults.hdf5",
                                   f"{B}/{P}NPCS100pct_fakelumi/data_reg_satp/fitresults.hdf5"),
    ("frozenNP (4D)",              f"{B}/{P}NPCS100pct/data_frozenNP_satp/fitresults.hdf5",
                                   f"{B}/{P}NPCS100pct_fakelumi/data_frozenNP_satp/fitresults.hdf5"),
    ("inflate2x (4D, no wall)",    f"{B}/{P}Inflate2x/fitresults.hdf5",
                                   f"{B}/{P}Inflate2x_fakelumi/fitresults.hdf5"),
    ("inflate2x_reg5 (4D, wall)",  f"{B}/{P}Inflate2x_reg5/data_satp/fitresults.hdf5",
                                   "MISSING"),  # no inflate2x_reg5_fakelumi
    ("inflate3x (4D, no wall)",    f"{B}/{P}Inflate3x/fitresults.hdf5",
                                   f"{B}/{P}Inflate3x_fakelumi/fitresults.hdf5"),
    ("inflate3x_reg5 (4D, wall)",  f"{B}/{P}Inflate3x_reg5/data_satp/fitresults.hdf5",
                                   "MISSING"),  # no inflate3x_reg5_fakelumi
    ("inflate5x (4D, no wall)",    f"{B}/{P}Inflate5x/fitresults.hdf5",
                                   f"{B}/{P}Inflate5x_fakelumi/fitresults.hdf5"),
    ("inflate5x_reg5 (4D, wall)",  f"{B}/{P}Inflate5x_reg5/data_satp/fitresults.hdf5",
                                   f"{B}/{P}Inflate5x_reg5_fakelumi/data_satp/fitresults.hdf5"),
]

def read_nll(path):
    fr, _ = get_fitresult(path, meta=True)
    obj = fr['nllvalreduced']
    if hasattr(obj, 'get'):
        return float(obj.get())
    try:
        return float(obj[()])
    except TypeError:
        return float(obj)

print(f"\n{'='*100}")
print(f"{'Pair':<35s}  {'NLL(no fl)':>14s}  {'NLL(+fl)':>14s}  {'2·ΔNLL':>10s}  {'p (χ²₁)':>10s}  Interp")
print(f"{'='*100}")
for lab, p_nofl, p_fl in PAIRS:
    if p_fl == "MISSING":
        print(f"{lab:<35s}  (no +fakelumi run available — skip)")
        continue
    try:
        n0 = read_nll(p_nofl)
        n1 = read_nll(p_fl)
        dnll2 = 2.0 * (n0 - n1)
        # χ²₁ p-value (upper tail)
        pval = chi2_dist.sf(dnll2, df=1)
        # Interpretation
        if dnll2 < 1.0:
            interp = "OK (fakelumi not informative, <1σ)"
        elif dnll2 < 3.84:
            interp = "mild tension (<2σ)"
        elif dnll2 < 6.63:
            interp = "TENSION (>2σ, <3σ)"
        elif dnll2 < 10.83:
            interp = "STRONG TENSION (>3σ)"
        else:
            interp = "VERY STRONG TENSION (>3.3σ)"
        print(f"{lab:<35s}  {n0:>14.3f}  {n1:>14.3f}  {dnll2:>10.3f}  {pval:>10.2e}  {interp}")
    except Exception as e:
        print(f"{lab:<35s}  read error: {e}")
print()
print("Note: 2·ΔNLL ~ χ²₁ where df=1 corresponds to adding fakelumi as a single free parameter.")
print("Critical values: 1 (1σ), 3.84 (2σ / 95% CL), 6.63 (3σ / 99% CL).")
PY
echo "DONE_OK"
