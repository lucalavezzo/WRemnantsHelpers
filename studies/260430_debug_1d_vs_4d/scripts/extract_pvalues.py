"""Extract saturated-projection p-values from 4D fits and saturated p-values from 1D fits."""

import os
import re
from scipy.stats import chi2 as chi2_dist
from rabbit.io_tools import get_fitresult

OUT = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260430_debug"

POSTFIXES = [
    "LatticeNoConstraints",
    "LatticeNoConstraints_ScetlibNoSymmetrize",
    "LatticeNoConstraints_chargeVgenNP0scetlibNPScale5p0",
    "LatticeNoConstraints_chargeVgenNP0scetlibNPScale5p0_fakelumi",
    "LatticeNoConstraints_chargeVgenNP0scetlibNPZlambda4Scale5p0",
    "LatticeNoConstraints_fakelumi",
    "LatticeNoConstraints_fakelumi_noAlphaS",
    "LatticeNoConstraints_scetlibNoConstraint",
    "LatticeNoConstraints_scetlibScale5p0",
]


def fourd_dir(p):
    return f"{OUT}/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_{p}/fitresults.hdf5"


def oned_dir(p):
    return f"{OUT}/ZMassDilepton_ptll_{p}/fitresults.hdf5"


# Parse 1D saturated chi2 from log (between postfix= header and DONE marker)
LOG = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/logs/ptll_debug_fits_260501_084355.log"
with open(LOG) as fh:
    text = fh.read()

oned_sat = {}
for p in POSTFIXES:
    pat = re.compile(
        r"postfix=" + re.escape(p) + r"\s*\n(.*?)--- DONE.*?postfix=" + re.escape(p),
        re.DOTALL,
    )
    m = pat.search(text)
    if not m:
        oned_sat[p] = (None, None, None)
        continue
    block = m.group(1)
    sat = re.search(
        r"Saturated chi2:.*?ndof:\s*(\d+).*?2\*deltaNLL:\s*([\d.]+).*?p-value:\s*([\d.]+)%",
        block,
        re.DOTALL,
    )
    if sat:
        oned_sat[p] = (int(sat.group(1)), float(sat.group(2)), float(sat.group(3)))
    else:
        oned_sat[p] = (None, None, None)

print(f"{'postfix':<70} | {'4D proj sat':>22} | {'1D sat':>22}")
print(f"{'':<70} | {'ndf  chi2     p-val':>22} | {'ndf  chi2     p-val':>22}")
print("-" * 120)
for p in POSTFIXES:
    f4 = fourd_dir(p)
    s4 = "  (no 4D file)"
    if os.path.exists(f4):
        try:
            fr = get_fitresult(f4)
            mp = fr["mappings"]["Project ch0 ptll"]
            ndf4 = int(mp["ndf_saturated"])
            chi24 = float(mp["chi2_saturated"])
            pv4 = chi2_dist.sf(chi24, ndf4) * 100
            s4 = f"{ndf4:>3}  {chi24:>6.2f}  {pv4:>6.2f}%"
        except Exception as e:
            s4 = f"  (err: {type(e).__name__}: {e})"[:22]
    nd1, c1, p1 = oned_sat[p]
    if nd1 is not None:
        s1 = f"{nd1:>3}  {c1:>6.2f}  {p1:>6.2f}%"
    else:
        s1 = "  (not found)"
    print(f"{p:<70} | {s4:>22} | {s1:>22}")
