import numpy as np, os
from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
fits = {
    "LATL4ZWALLCOLD (lattice, walled)": "260923_lattice_fits/l4zero_walled/fitresults_LATL4ZWALLCOLD.hdf5",
    "LATL4ZUNWCOLD (lattice, unwalled cold)": "260923_lattice_fits/l4zero_unwalled/fitresults_LATL4ZUNWCOLD.hdf5",
    "LATL4ZUNWWARM (lattice, unwalled warm)": "260923_lattice_fits/l4zero_unwalled_warm/fitresults_LATL4ZUNWWARM.hdf5",
    "CCWALLCOLDR (no lattice, walled)": "260917_cc_fits_wall/fitresults_CCWALLCOLDR.hdf5",
    "CCWALLWARMPF (no lattice, walled warm)": "260917_cc_fits_wall/fitresults_CCWALLWARMPF.hdf5",
    "CCKRYLOVWARM (no lattice, unwalled)": "260917_cc_fits_hvpfix/fitresults_CCKRYLOVWARM.hdf5",
    "CCCOLDSELF (no lattice, unwalled 2nd min)": "260917_cc_selfrestart/fitresults_CCCOLDSELF.hdf5",
}
keys = ["PtV5_7", "PtV7_9", "PtV9_11", "PtV15_20", "PtV40_13000"]
print(f"{'fit':42s} " + " ".join(f"{k:>9s}" for k in keys) + "  incl   sum(A0 pull^2)")
for lab, f in fits.items():
    p = f"{A}/{f}"
    if not os.path.exists(p):
        print(lab, "missing")
        continue
    try:
        h = io_tools.get_fitresult(p)["parms"].get()
    except Exception as e:
        print(lab, "unreadable", e)
        continue
    n = [str(x) for x in h.axes[0]]
    v = dict(zip(n, h.values()))
    a0 = [x for x in n if x.startswith("QCDscaleZ") and "helicity_0_" in x]
    vals = [v.get(f"QCDscaleZfine_{k}helicity_0_SymAvg", np.nan) for k in keys]
    print(
        f"{lab:42s} "
        + " ".join(f"{x:+9.2f}" for x in vals)
        + f"  {v.get('QCDscaleZinclusive_PtV0_13000helicity_0_SymAvg',np.nan):+.2f}   {sum(v[x]**2 for x in a0):.2f}"
    )
