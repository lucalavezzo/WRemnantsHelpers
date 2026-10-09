import numpy as np, os, glob
from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
fits = {
    "2D Jul (260702_2D, SCETlibNP)": "260702_2D_l6nu0p01_l60p01/fitresults.hdf5",
    "4D Jul (260714, same nuisances)": "260714_l6nu0p01_l60p01/fitresults.hdf5",
    "4D Apr (260427_debug_allproj)": "260427_debug_allproj/fitresults.hdf5",
    "2D Sep LATL4ZWALLCOLD (AD model)": "260923_lattice_fits/l4zero_walled/fitresults_LATL4ZWALLCOLD.hdf5",
}
for lab, f in fits.items():
    p = f"{A}/{f}"
    try:
        r = io_tools.get_fitresult(p)
        h = r["parms"].get()
    except Exception as e:
        print(lab, "unreadable:", str(e)[:100])
        continue
    n = [str(x) for x in h.axes[0]]
    v = h.values()
    e = np.sqrt(h.variances())
    d = {
        n[i]: (v[i], e[i])
        for i in range(len(n))
        if n[i].startswith("QCDscaleZ") and n[i].endswith("SymAvg")
    }
    a0 = {k: x for k, x in d.items() if "helicity_0_" in k}
    other = sum(x[0] ** 2 for k, x in d.items() if "helicity_0_" not in k)
    print(
        f"== {lab}: {len(d)} QCDscaleZ SymAvg; sum A0 pull^2={sum(x[0]**2 for x in a0.values()):.2f}; others={other:.2f}"
    )
    for k in sorted(a0, key=lambda k: -abs(a0[k][0]))[:7]:
        print(f"    {k:50s} {a0[k][0]:+.2f} +- {a0[k][1]:.2f}")
