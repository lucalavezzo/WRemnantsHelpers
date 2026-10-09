"""Delta alpha_s / sigma between pairs of fitresults (blinded: differences only)."""

import sys
import numpy as np
from rabbit import io_tools


def get(p):
    h = io_tools.get_fitresult(p)["parms"].get()
    n = [str(x.decode() if isinstance(x, bytes) else x) for x in h.axes[0]]
    i = n.index("alphaS")
    return h.values()[i], np.sqrt(h.variances()[i])


a = dict(t.split("=", 1) for t in sys.argv[1:])
v = {k: get(p) for k, p in a.items()}
ks = list(v)
for i in ks:
    for j in ks:
        if i < j:
            d = v[i][0] - v[j][0]
            print(
                f"{i} - {j}: Dalpha_s/sigma_{j} {d/v[j][1]:+.3f}  /sigma_{i} {d/v[i][1]:+.3f}"
            )
