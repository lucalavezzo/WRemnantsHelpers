import numpy as np
from scipy.stats import chi2
from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
for lab, f in [
    ("CCKRYLOVWARM (unwalled)", "260917_cc_fits_hvpfix/fitresults_CCKRYLOVWARM.hdf5"),
    (
        "CCCOLDSELF (unwalled 2nd min)",
        "260917_cc_selfrestart/fitresults_CCCOLDSELF.hdf5",
    ),
    ("CCWALLWARMPF (walled)", "260917_cc_fits_wall/fitresults_CCWALLWARMPF.hdf5"),
    ("CCWALLCOLDR (walled)", "260917_cc_fits_wall/fitresults_CCWALLCOLDR.hdf5"),
    (
        "LATL4ZUNWWARM (lattice unwalled warm)",
        "260923_lattice_fits/l4zero_unwalled_warm/fitresults_LATL4ZUNWWARM.hdf5",
    ),
    (
        "LATL4ZWALLCOLD (lattice walled)",
        "260923_lattice_fits/l4zero_walled/fitresults_LATL4ZWALLCOLD.hdf5",
    ),
]:
    r = io_tools.get_fitresult(f"{A}/{f}")
    mp = r.get("mappings", {}).get("Project ch0 ptll", {})
    q = mp.get("chi2_saturated")
    ndf = mp.get("ndf_saturated")
    edm = mp.get("edmval_saturated")
    h = r["parms"].get()
    n = [str(x) for x in h.axes[0]]
    v = dict(zip(n, h.values()))
    a0 = v.get("QCDscaleZfine_PtV15_20helicity_0_SymAvg")
    print(
        f"{lab:40s} NLL {float(r['nllvalreduced']):9.3f}  proj q={q if q is None else round(q,2)}/{ndf} p={'' if q is None else '%.3g'%chi2.sf(q,ndf)} subEDM={edm}  A0_15_20={a0:+.2f}"
    )
