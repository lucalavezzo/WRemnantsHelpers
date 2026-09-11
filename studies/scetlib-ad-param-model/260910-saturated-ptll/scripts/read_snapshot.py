"""Progress probe: how far have the 39 saturated bin scales moved from 1 toward
their closed-form single-bin optima r_j = D_j/N_j?  Reads only the snapshot, so
it costs nothing and does not disturb the running fit."""

import sys

import h5py
import numpy as np

npz = np.load(sys.argv[2])
rj = npz[sys.argv[3]]
with h5py.File(sys.argv[1], "r") as f:
    keys = list(f.keys())
    x = f["x"][...] if "x" in f else None
    parms = f["parms"][...].astype(str) if "parms" in f else None
print("snapshot keys:", keys)
if x is None:
    sys.exit("no x in snapshot")
sat = np.array([i for i, n in enumerate(parms) if n.startswith("saturated_")])
print(f"{len(sat)} saturated params at indices {sat.min()}..{sat.max()}")
v = x[sat]
print(f"  value  min {v.min():.5f} max {v.max():.5f}")
print(f"  target min {rj.min():.5f} max {rj.max():.5f}  (single-bin optimum)")
print(
    f"  fraction of the way from 1 to r_j: "
    f"{np.mean((v - 1) / (rj - 1)):.4f} (mean), "
    f"{np.median((v - 1) / (rj - 1)):.4f} (median)"
)
print(f"  max |value - r_j| = {np.abs(v - rj).max():.2e}")
