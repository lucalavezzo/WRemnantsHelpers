#!/usr/bin/env python3
"""Build the MEMNOM command from NOMSTIFF's OWN meta_info command.

Changes vs NOMSTIFF:
  -o / --postfix          this task's ceph dir, MEMNOM
  --externalPostfit       NOMSTIFF's converged snapshot (x only, no cov -> the Hessian IS recomputed);
                          checked bit-identical to NOMSTIFF's postfit parms below
  --noFit                 added: load + model build + loss/grad + postfit Hessian, no minimisation
  prior_sigmas            lambda2_nu=nan -> lambda2_nu=nan,lambda2=1,lambda4=1,delta_lambda2=1
                          (WRemnants a008faa5 made TMD lambdas prior-free by default; pin the old default)
  --snapshotFile/Interval dropped (no minimisation)
"""
import difflib, os, shlex, sys
import h5py, numpy as np
from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
NOM = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
SNAP = f"{A}/260930_stiff_wall_fits/snapshot_fitresults_NOMSTIFF.hdf5"
OUT = f"{A}/261006_memory_breakdown"
TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIORS = "lambda2_nu=nan,lambda2=1,lambda4=1,delta_lambda2=1"

fr, meta = io_tools.get_fitresult(NOM, None, meta=True)
h = fr["parms"].get()
nN = [str(n) for n in h.axes[0]]
xN = np.asarray(h.values(), float)
with h5py.File(SNAP, "r") as f:
    x, nm = f["x"][...], list(f["parms"][...].astype(str))
    assert "cov" not in f
assert nm == nN, "snapshot layout"
same = np.array_equal(x.view(np.uint64), xN.view(np.uint64))
print(
    f"[seed] snapshot vs NOMSTIFF postfit parms: bit-identical={same}  max|dx|={np.max(np.abs(x-xN)):.3e}"
)
for k in ("nllvalfull", "nllval", "satnllvalfull", "edmval"):
    if k in fr:
        print(f"[ref] NOMSTIFF has {k}")
toks = shlex.split(meta["meta_info"]["command"])
new = list(toks)


def setval(flag, val):
    assert new.count(flag) == 1, flag
    new[new.index(flag) + 1] = val


setval("-o", OUT)
setval("--postfix", "MEMNOM")
setval("--externalPostfit", SNAP)
i = new.index("--snapshotFile")
del new[i : i + 2]
i = new.index("--snapshotInterval")
del new[i : i + 2]
j = [k for k, t in enumerate(new) if t.startswith("prior_sigmas=")]
assert len(j) == 1 and new[j[0]] == "prior_sigmas=lambda2_nu=nan"
new[j[0]] = "prior_sigmas=" + PRIORS
assert "--noHessian" not in new and "--noEDM" not in new
new += ["--noFit"]
os.makedirs(f"{TASK}/cmds", exist_ok=True)
open(f"{TASK}/cmds/MEMNOM.cmd", "w").write(" ".join(shlex.quote(t) for t in new) + "\n")
for d in difflib.unified_diff(toks, new, lineterm="", n=0):
    if d.startswith(("+", "-")) and not d.startswith(("+++", "---")):
        print("   ", d[:300])
