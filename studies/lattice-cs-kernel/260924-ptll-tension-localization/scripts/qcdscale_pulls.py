import numpy as np
from rabbit import io_tools

r = io_tools.get_fitresult(
    "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260923_lattice_fits/l4zero_walled/fitresults_LATL4ZWALLCOLD.hdf5"
)
h = r["parms"].get()
n = [str(x) for x in h.axes[0]]
v = h.values()
e = np.sqrt(h.variances())
rows = [(n[i], v[i], e[i]) for i in range(len(n)) if n[i].startswith("QCDscaleZ")]
print("all QCDscaleZ with |pull|>0.5:")
for nm, a, b in sorted(rows, key=lambda x: -abs(x[1])):
    if abs(a) > 0.5:
        print(f"  {nm:48s} {a:+.2f} +- {b:.2f}")
print(
    "sum pull^2 by helicity:",
    {
        h_: round(sum(a * a for nm, a, b in rows if f"helicity_{h_}_" in nm), 2)
        for h_ in range(8)
    },
)
