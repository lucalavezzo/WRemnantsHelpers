#!/usr/bin/env python3
"""How non-quadratic is an x-dependent TMD NP function in Y, at Z/13 TeV? (MAP22 N3LL replicas as the example.)

Small-b local coefficient of our form: ln F_eff(b,Y) = -2 L2(Y) b^2 + O(b^4). For MAP22 the two-beam intrinsic part
(CS evolution stripped, as in np-wall-local-minima/scripts/map_replicas.py, whose f_int and replica parser are reused)
gives L2_MAP(Y) = -ln[f(x1,b) f(x2,b)] / (2 b^2) at b -> 0, x_{1,2} = (Q/sqrt s) e^{+-Y}.
Fit L2_MAP(Y) on |Y| <= 2.5 (101 pts, uniform in Y) with a + b Y^2 and a + b Y^2 + c Y^4; report the Y^4 coefficient,
the max |quadratic - true| over the range, and the quadratic's error AT THE EDGE (L2(2.5), the wall face).
"""
import json, os, sys
import numpy as np

sys.path.insert(
    0,
    "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/np-wall-local-minima/scripts",
)
import map_replicas as M

Q, RS = 91.1876, 13000.0
Y = np.linspace(0.0, 2.5, 101)
x1, x2 = (Q / RS) * np.exp(Y), (Q / RS) * np.exp(-Y)


def L2map(p, b):
    return -np.log(M.f_int(x1, b, p) * M.f_int(x2, b, p)) / (2 * b * b)


out = dict(x_range=[float(x2[-1]), float(x1[0]), float(x1[-1])])
rows = []
for f in M.replica_files():
    p = M.parse(f)
    if p is None:
        continue
    L = L2map(p, 0.02)
    Lb = L2map(p, 0.05)
    A2 = np.vstack([np.ones_like(Y), Y**2]).T
    A4 = np.vstack([np.ones_like(Y), Y**2, Y**4]).T
    c2, *_ = np.linalg.lstsq(A2, L, rcond=None)
    c4, *_ = np.linalg.lstsq(A4, L, rcond=None)
    q = A2 @ c2
    rows.append(
        dict(
            L0=L[0],
            Ledge=L[-1],
            a2=c2[0],
            b2=c2[1],
            a4=c4[0],
            b4=c4[1],
            c4=c4[2],
            maxdev=np.max(np.abs(q - L)),
            edge_err=q[-1] - L[-1],
            bstab=np.max(np.abs(Lb - L)),
        )
    )
R = {k: np.array([r[k] for r in rows]) for k in rows[0]}
out["n_replicas"] = len(rows)
for k, v in R.items():
    out[k] = dict(
        median=float(np.median(v)),
        p16=float(np.percentile(v, 16)),
        p84=float(np.percentile(v, 84)),
    )
# central replica (replica_0 if present) curve for the logbook
p0 = M.parse(M.replica_files()[0])
L = L2map(p0, 0.02)
out["central_curve"] = dict(
    Y=Y[::10].tolist(),
    L2=L[::10].tolist(),
    local_coeff=[None] + ((L[10::10] - L[0]) / Y[10::10] ** 2).tolist(),
)
json.dump(
    out,
    open(
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "map22_y4.json"
        ),
        "w",
    ),
    indent=1,
)
print(json.dumps({k: v for k, v in out.items()}, indent=1))
