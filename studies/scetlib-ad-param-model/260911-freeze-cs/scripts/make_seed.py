#!/usr/bin/env python3
"""Build a warm-start seed: the plain arm's postfit with the CS pair moved.

WHY THIS EXISTS. The cold frozen scan changes two things at once -- the frozen
CS value AND, potentially, which minimum the cold minimiser walks to. This
study has already measured that alpha_s on this card is basin-dependent at the
3.5 sigma level (../260910-basins), and the cold frzCS@0.15 arm landed 2.1-2.9
away in L2 from every other arm, so its alpha_s is not a clean CS response.

A warm start from the PLAIN arm's own postfit, with only the two CS parameters
moved to the frozen target, removes that confound: it is exactly "stand at the
plain minimum, fix the CS kernel, and reminimise", which is the operational
form of section 11 item 3's question.

MECHANISM. rabbit's `load_fitresult` accepts a FLAT layout -- an hdf5 with
datasets `x` (the parameter vector) and `parms` (the names) -- and assigns
`self.x` on the intersection of names (fitter.py:515-547). No covariance is
written, so the fit recomputes its own Hessian. Note the ORDER: freeze_params()
runs in Fitter.__init__ but load_fitresult() runs after, so a frozen parameter
is pinned at whatever the SEED holds, not at xparamdefault -- which is exactly
why the target value has to be written into the seed rather than passed as
xparam_default.

The seed is in the BLINDED internal coordinate, unchanged from the source
fitresult, so the warm arm stays in the same blinding family. It is written to
ceph, never into the (web-published) task directory.

usage: make_seed.py <source fitresult.hdf5> <out.hdf5> <name=theta,...>
"""
import os
import shutil
import sys

import h5py
import numpy as np

SCRATCH = "/tmp/frzcs_read"
from rabbit import io_tools  # noqa: E402


def local_copy(path):
    os.makedirs(SCRATCH, exist_ok=True)
    dst = os.path.join(SCRATCH, os.path.basename(path))
    if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(path):
        shutil.copy2(path, dst)
    return dst


src, out, spec = sys.argv[1], sys.argv[2], sys.argv[3]
res = io_tools.get_fitresult(local_copy(src))
h = res["parms"].get()
names = np.array([str(n) for n in h.axes[0]])
x = np.array(h.values(), dtype=np.float64)

idx = {n: i for i, n in enumerate(names)}
for tok in spec.split(","):
    if not tok:
        continue
    k, v = tok.split("=")
    if k not in idx:
        raise KeyError(f"{k} not in the source fitresult")
    old = x[idx[k]]
    x[idx[k]] = float(v)
    print(f"  {k}: theta {old:+.6f} -> {float(v):+.6f}")

os.makedirs(os.path.dirname(out), exist_ok=True)
with h5py.File(out, "w") as f:
    f.create_dataset("x", data=x)
    f.create_dataset("parms", data=np.array([n.encode() for n in names]))
print(f"wrote {out}  ({len(names)} parameters, source {os.path.basename(src)})")
print("MAKESEED_DONE")
