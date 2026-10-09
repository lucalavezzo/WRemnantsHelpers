import sys, h5py, numpy as np

f = h5py.File(sys.argv[1], "r")
names = [n.decode() if isinstance(n, bytes) else str(n) for n in f["parms"][...]]
x = f["x"][...]
th = dict(zip(names, x))
spec = {
    "lambda2": (0.4, 0.5),
    "lambda4": (0.4, 0.5),
    "delta_lambda2": (0.0, 0.5),
    "lambda2_nu": (0.15, 0.1),
    "lambda4_nu": (0.0, 0.5),
}
for n, (a, w) in spec.items():
    print(f"{n:14s} theta {th[n]:+.6f}  physical {a + w * th[n]:+.6f}")
for n in ["resumScaleMuF", "resumTNP_b_qg", "pdfEig23"]:
    print(f"{n:14s} theta {th[n]:+.4f}")
