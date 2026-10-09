"""XL4ZSTIFF vs XWSTIFF: same card (A, no lattice), same objective (tau 8, margin 0); XL4Z = XW with lambda4_nu held at 0.
Blinded: alphaS theta difference only."""

import numpy as np
from rabbit import io_tools

O = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260930_stiff_wall_fits"
r = {}
for pf in ("XWSTIFF", "XL4ZSTIFF"):
    fr = io_tools.get_fitresult(f"{O}/fitresults_{pf}.hdf5", None)
    h = fr["parms"].get()
    names = [n.decode() if isinstance(n, bytes) else str(n) for n in h.axes[0]]
    i = names.index("alphaS")
    r[pf] = (float(fr["nllvalreduced"]), h.values()[i], np.sqrt(h.variances()[i]))
(nw, aw, sw), (nz, az, sz) = r["XWSTIFF"], r["XL4ZSTIFF"]
print(f"dNLL(XL4Z - XW) = {nz - nw:+.4f}  (2dNLL {2*(nz-nw):+.3f})")
print(
    f"d(alphaS)(XL4Z - XW) / sigma_XW = {(az-aw)/sw:+.4f} ; / sigma_XL4Z = {(az-aw)/sz:+.4f} ; sigma_XL4Z/sigma_XW = {sz/sw:.4f}"
)
