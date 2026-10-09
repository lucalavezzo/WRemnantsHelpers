"""Logbook number checks (product agreement, F^NP = 0.1 crossings); run like plot.py."""

import os, numpy as np, sys

sys.argv = ["x"]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plot as P

bT = np.linspace(1e-3, 12.6, 4000)
L = np.log(P.MZ * bT / P.B0)
r = {}
for k in ("LATFROZ_V3", "XWSTIFF"):
    g, e = P.np_set(k)
    cs = np.exp(P.NPF.gamma_nu_curve(bT, g) * L)
    f = P.NPF.f_eff_curve(bT, 0.0, e)
    r[k] = (cs, f, cs * f)
    print(k, "F=0.1 at", bT[np.argmax(f < 0.1)])
print("MAP22 F=0.1 at", bT[np.argmax(P.NPF.map22_F_eff(bT, 0.0) < 0.1)])
t1, t2 = r["LATFROZ_V3"][2], r["XWSTIFF"][2]
for thr in (0.5, 0.2, 0.1):
    m = t1 > thr
    print(
        f"product>{thr}: b<{bT[m].max():.2f}, max rel diff {np.max(np.abs(t2[m]/t1[m]-1)):.3f}"
    )
