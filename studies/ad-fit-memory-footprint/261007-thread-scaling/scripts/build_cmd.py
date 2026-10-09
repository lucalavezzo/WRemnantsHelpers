#!/usr/bin/env python3
"""Build the thread-scaling commands from NOMSTIFF's OWN meta_info command (recipe of
../../261006-subset-cache-y25/scripts/build_cmd.py). Changes vs NOMSTIFF:
  cache= / conf=        the |Y|<=2.5 subset cache (exact for this card)
  threads=              the scanned value (NOMSTIFF: 128)
  prior_sigmas          lambda2_nu=nan -> lambda2_nu=nan,lambda2=1,lambda4=1,delta_lambda2=1 (pin NOMSTIFF's)
  -o / --postfix        this task's ceph dir, TS<threads>[suffix]
  --externalPostfit     a KICKED copy of NOMSTIFF's converged snapshot (x only, no cov): +-0.3 sigma_postfit
                        in 5 non-NP parameters, so trust-krylov has real work to do
  --minimizerMaxiter 5  short minimisation; the postfit Hessian (+EDM from it) stays ON in the same job
  --snapshotFile/Interval dropped
Usage: build_cmd.py <threads> [suffix]
"""
import os, shlex, sys
import h5py, numpy as np
from rabbit import io_tools

THR = int(sys.argv[1])
SUF = sys.argv[2] if len(sys.argv) > 2 else ""
A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
NOM = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
SNAP = f"{A}/260930_stiff_wall_fits/snapshot_fitresults_NOMSTIFF.hdf5"
SUB = f"{A}/ad_scetlib_caches/pdf62_y35_260921_y25"
OUT = f"{A}/261007_thread_scaling"
KICKED = f"{OUT}/seed_NOMSTIFF_kick03.hdf5"
TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIORS = "lambda2_nu=nan,lambda2=1,lambda4=1,delta_lambda2=1"
KICK = {
    "alphaS": +0.3,
    "pdfEig0": -0.3,
    "pdfEig3": +0.3,
    "resumTNP_s": -0.3,
    "resumTNP_b_qqV": +0.3,
}
PF = f"TS{THR}{SUF}"

fr, meta = io_tools.get_fitresult(NOM, None, meta=True)
if not os.path.exists(KICKED):
    h = fr["parms"].get()
    names = [str(n) for n in h.axes[0]]
    sig = np.sqrt(np.asarray(h.variances(), float))
    with h5py.File(SNAP, "r") as f:
        x, nm = f["x"][...].copy(), f["parms"][...]
    assert [n.decode() if isinstance(n, bytes) else str(n) for n in nm] == names
    for p, k in KICK.items():
        i = names.index(p)
        assert np.isfinite(sig[i]) and sig[i] > 0, p
        x[i] += k * sig[i]
        print(
            f"[seed] kicked {p} by {k:+.1f} sigma_postfit"
        )  # values not printed (blinding)
    with h5py.File(KICKED, "w") as f:
        f["x"] = x
        f["parms"] = nm
        f.attrs["provenance"] = (
            f"NOMSTIFF snapshot + kicks {KICK} (units of NOMSTIFF postfit sigma)"
        )
toks = shlex.split(meta["meta_info"]["command"])
new = list(toks)


def setval(flag, val):
    assert new.count(flag) == 1, flag
    new[new.index(flag) + 1] = val


def settok(prefix, val):
    j = [k for k, t in enumerate(new) if t.startswith(prefix)]
    assert len(j) == 1, prefix
    new[j[0]] = prefix + val


setval("-o", OUT)
setval("--postfix", PF)
if "--externalPostfit" in new:
    setval("--externalPostfit", KICKED)
else:
    new += ["--externalPostfit", KICKED]
for fl in ("--snapshotFile", "--snapshotInterval"):
    if fl in new:
        i = new.index(fl)
        del new[i : i + 2]
j = [k for k, t in enumerate(new) if t.startswith("prior_sigmas=")]
assert len(j) == 1 and new[j[0]] == "prior_sigmas=lambda2_nu=nan"
new[j[0]] = "prior_sigmas=" + PRIORS
settok("cache=", f"{SUB}/cache.npz")
settok("conf=", f"{SUB}/cache.conf")
settok("threads=", str(THR))
for fl in ("--noHessian", "--noEDM", "--noFit", "--minimizerMaxiter"):
    assert fl not in new, fl
new += ["--minimizerMaxiter", "5"]
os.makedirs(f"{TASK}/cmds", exist_ok=True)
open(f"{TASK}/cmds/{PF}.cmd", "w").write(" ".join(shlex.quote(t) for t in new) + "\n")
import difflib

for d in difflib.unified_diff(toks, new, lineterm="", n=0):
    if d.startswith(("+", "-")) and not d.startswith(("+++", "---")):
        print("   ", d[:200])
