"""Diagnose AD vs finite-difference for the CS-kernel NP columns (peak window cache)."""

import numpy as np
from wremnants.postprocessing.scetlib_ad.xsec_backend import ScetlibADXsec

D = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/qsplit_260923/q86_96"
core = ScetlibADXsec(f"{D}/cache.conf", f"{D}/cache.npz", threads=32, fo_muf_poly=0)
nm = list(core.param_names)
a = core.anchor.copy()
i2, i4 = nm.index("np_gnu_lambda2"), nm.index("np_gnu_lambda4")
sel = [0, 5, 10, 1, 6, 20, 40, 70]  # bins
print("bins (Qlo,Qhi,Ylo,Yhi,qTlo,qThi):")
print(core.bins[sel])


def val(p):
    return np.asarray(core.values_and_jacobian(p)[0])


for tag, p0 in [("anchor", a), ("lattice", None)]:
    if p0 is None:
        p0 = a.copy()
        p0[i2] = 0.184
        p0[i4] = -0.0059
    v0, J = core.values_and_jacobian(p0)
    v0 = np.asarray(v0)
    J = np.asarray(J)
    for i, name, hs in [(i4, "l4nu", [1e-4, 1e-3, 4e-3]), (i2, "l2nu", [1e-3, 5e-3])]:
        print(f"--- {tag} {name}: AD dS/S per bin")
        print("   AD", np.round(J[sel, i] / v0[sel], 4))
        for h in hs:
            pp = p0.copy()
            pp[i] += h
            pm = p0.copy()
            pm[i] -= h
            fp = (val(pp) - v0) / h
            fm = (v0 - val(pm)) / h
            print(f"   h={h:g} fwd", np.round(fp[sel] / v0[sel], 4))
            print(f"   h={h:g} bwd", np.round(fm[sel] / v0[sel], 4))
# scan sigma in lambda4_nu
print("--- sigma(bin0,bin20)/anchor vs lambda4_nu at anchor lambda2_nu")
for l4 in [-0.01, -0.004, -0.001, 0, 0.001, 0.004, 0.01, 0.05]:
    p = a.copy()
    p[i4] = l4
    v = val(p)
    print(f"   l4nu={l4:+.3f}", np.round(v[sel] / val(a)[sel], 6))
