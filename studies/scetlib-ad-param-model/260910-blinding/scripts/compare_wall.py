#!/usr/bin/env python3
"""Compare walled vs unwalled blinded fits.

BLINDING POLICY. Both fits used the SAME deterministic offset (seeded from the
parameter name), so the DIFFERENCE of the two alphaS values is offset-free and
safe to report -- it says how much the wall moved alpha_s. Neither absolute
value is printed, and the offset is never computed.
"""
import sys

import numpy as np

sys.path.insert(0, "/work/submit/lavezzo/alphaS/rabbit-blinding")
from rabbit import io_tools  # noqa: E402

WIDTH = 0.002  # alphaS: physical = anchor + WIDTH * theta

out = {}
for label, path in (("unwalled", sys.argv[1]), ("walled", sys.argv[2])):
    res, meta = io_tools.get_fitresult(path, meta=True)
    h = res["parms"].get()
    names = [str(n) for n in h.axes[0]]
    i = names.index("alphaS")
    d = dict(
        theta=float(h.values()[i]),
        sig_theta=float(np.sqrt(h.variances()[i])),
    )
    for key in ("nllvalreduced", "nllvalfull", "edmval", "satndf", "ndfsat"):
        if key in res:
            try:
                d[key] = float(np.asarray(res[key]))
            except Exception:
                pass
    # chi2 / p-value blocks, whatever they are called in this build
    for k in res.keys():
        kl = str(k).lower()
        if "chi2" in kl or "pval" in kl or "ndf" in kl:
            try:
                d[str(k)] = float(np.asarray(res[k]))
            except Exception:
                d[str(k)] = "<non-scalar>"
    out[label] = d

u, w = out["unwalled"], out["walled"]
print("=" * 68)
print("alphaS  (SAME blinding offset in both, so only the DIFFERENCE is shown)")
print("=" * 68)
print(
    f"  sigma(alpha_s)   unwalled {u['sig_theta'] * WIDTH:.6f}"
    f"   walled {w['sig_theta'] * WIDTH:.6f}"
    f"   ratio {w['sig_theta'] / u['sig_theta']:.4f}"
)
d_theta = w["theta"] - u["theta"]
print(
    f"  SHIFT from the wall: d(alpha_s) = {d_theta * WIDTH:+.6f}"
    f"   ({d_theta / u['sig_theta']:+.3f} sigma of the unwalled uncertainty)"
)
print()
print("=" * 68)
print("goodness of fit and convergence")
print("=" * 68)
keys = sorted(set(u) | set(w))
for k in keys:
    if k in ("theta", "sig_theta"):
        continue
    fu, fw = u.get(k, "-"), w.get(k, "-")
    fmt = lambda v: f"{v:.6g}" if isinstance(v, float) else str(v)
    print(f"  {k:24s} unwalled {fmt(fu):>14s}   walled {fmt(fw):>14s}")
