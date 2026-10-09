"""Same blinding frame across rabbit versions? Prints ONLY the DIFFERENCE of the stored (blinded) alphaS between
two fitresults evaluated at the same parameter vector. Never prints a value."""

import sys, numpy as np
from rabbit import io_tools

v = []
for p in sys.argv[1:3]:
    h = io_tools.get_fitresult(p)["parms"].get()
    names = [str(n.decode() if isinstance(n, bytes) else n) for n in h.axes[0]]
    v.append(h.values()[names.index("alphaS")])
print(
    f"stored alphaS difference (new rabbit - old rabbit, same vector) = {v[0] - v[1]:+.3e} (theta units)"
)
