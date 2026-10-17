#!/usr/bin/env python3
"""Compare two rabbit parameter snapshots / fitresult saturated vectors: NP lambdas, alphaS (blinded: difference only).
usage: compare_snapshots.py A.hdf5 B.hdf5"""
import sys, numpy as np, h5py

try:
    from wums import ioutils
except ImportError:
    ioutils = None


def load(p):
    f = h5py.File(p, "r")
    if "x" in f and "parms" in f:  # rabbit snapshot (rabbit/snapshot.py)
        return (
            np.array(f["parms"][...]).astype(str),
            np.array(f["x"][...]),
            dict(f.attrs),
        )
    r = ioutils.pickle_load_h5py(f["results"])
    if "parms" in r and "mappings" not in r:
        h = r["parms"].get()
    elif "mappings" in r:
        h = r["mappings"]["Project ch0 ptll"]["saturated_fit"]["parms"].get()
    else:
        raise RuntimeError(list(r.keys()))
    return np.array(h.axes["parms"]).astype(str), h.values(), r


na, xa, ra = load(sys.argv[1])
nb, xb, rb = load(sys.argv[2])
print("keys A:", list(ra.keys())[:10])
print("keys B:", list(rb.keys())[:10])
for k in ("nllvalreduced", "loss", "nllval"):
    for nm, r in (("A", ra), ("B", rb)):
        if k in r:
            print(nm, k, r[k])
common = [n for n in na if n in set(nb)]
ia = {n: i for i, n in enumerate(na)}
ib = {n: i for i, n in enumerate(nb)}
d = np.array([xb[ib[n]] - xa[ia[n]] for n in common])
o = np.argsort(-np.abs(d))
print("n common", len(common), "max |dx|", np.abs(d).max())
for i in o[:15]:
    print(f"  {common[i]:30s} dx={d[i]: .4e}")
lam = {
    "lambda2": (0.4, 0.5),
    "lambda4": (0.4, 0.5),
    "delta_lambda2": (0, 0.5),
    "lambda2_nu": (0.15, 0.1),
    "lambda4_nu": (0, 0.5),
}
for nm, x, idx in (("A", xa, ia), ("B", xb, ib)):
    L = {k: a + b * x[idx[k]] for k, (a, b) in lam.items()}
    L2y = lambda y: L["lambda2"] + L["delta_lambda2"] * y * y
    print(
        nm,
        {k: round(v, 6) for k, v in L.items()},
        "L2(2.5)=%.3e cubic(0)=%.3e cubic(2.5)=%.3e"
        % (L2y(2.5), 3 * L["lambda4"] + L2y(0) ** 3, 3 * L["lambda4"] + L2y(2.5) ** 3),
    )
print(
    "alphaS dx (B-A, internal units, blinded difference):",
    xb[ib["alphaS"]] - xa[ia["alphaS"]],
)
