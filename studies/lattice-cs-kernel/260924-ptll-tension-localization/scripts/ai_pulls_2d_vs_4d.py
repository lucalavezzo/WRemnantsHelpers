import numpy as np, re, collections
from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
for lab, f in [
    ("2D Jul", "260702_2D_l6nu0p01_l60p01/fitresults.hdf5"),
    ("4D Jul", "260714_l6nu0p01_l60p01/fitresults.hdf5"),
    ("4D Apr", "260427_debug_allproj/fitresults.hdf5"),
]:
    h = io_tools.get_fitresult(f"{A}/{f}")["parms"].get()
    n = [str(x) for x in h.axes[0]]
    v = h.values()
    d = {
        n[i]: v[i]
        for i in range(len(n))
        if n[i].startswith("QCDscaleZ") and n[i].endswith("SymAvg")
    }
    by = collections.defaultdict(float)
    for k, x in d.items():
        by["A" + re.search(r"helicity_(\d)", k).group(1)] += x * x
    print(f"== {lab}: sum pull^2 by A_i:", {k: round(by[k], 2) for k in sorted(by)})
    for k in sorted(d, key=lambda k: -abs(d[k]))[:8]:
        if "helicity_0_" not in k:
            print(f"    {k:50s} {d[k]:+.2f}")
