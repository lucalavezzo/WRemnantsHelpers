#!/usr/bin/env python3
"""Build C2A / R2A from NOMSTIFF's OWN meta_info command (recipe of
../../ad-fit-memory-footprint/261006-subset-cache-y25/scripts/build_cmd.py). Changes vs NOMSTIFF:
  cache= / conf=          the exact |Y|<=2.5 subset cache (bit-identical NOMSTIFF replay, SUBY25)
  -o / --postfix          this task's ceph dir, C2A / R2A
  --externalPostfit       CENS03R's SIGTERM snapshot (stopped mid-crawl; x only, no cov)
  --snapshotFile          this task's ceph dir (interval 0.25 h kept)
  prior_sigmas            lambda2_nu=nan -> lambda2_nu=nan,lambda2=1,lambda4=1,delta_lambda2=1
                          (WRemnants a008faa5 made the TMD lambdas prior-free by default; pin NOMSTIFF's)
  --earlyStopping         100 -> 20 (Luca, 2026-10-08)
  C2A only                NPDampingMapping margin=0 -> margin=0 smooth=c2 delta=1e-3
Also writes ref.json: NOMSTIFF's loss / alphaS / sigma / lambdas and the CENS03R snapshot's lambdas.
alphaS is blinded: only differences in sigma are written.
"""
import difflib
import json
import os
import shlex

import h5py
import numpy as np
from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
NOM = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
SNAP = f"{A}/261001_census_nominal/snapshot_fitresults_CENS03R.hdf5"
SUB = f"{A}/ad_scetlib_caches/pdf62_y35_260921_y25"
OUT = f"{A}/261008_c2_wall_test"
TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIORS = "lambda2_nu=nan,lambda2=1,lambda4=1,delta_lambda2=1"
LAMS = ["lambda2", "lambda4", "delta_lambda2", "lambda2_nu"]

fr, meta = io_tools.get_fitresult(NOM, None, meta=True)
h = fr["parms"].get()
nN = [str(n) for n in h.axes[0]]
xN = np.asarray(h.values(), float)
sN = np.sqrt(np.asarray(h.variances(), float))
with h5py.File(SNAP, "r") as f:
    x, nm = f["x"][...], list(f["parms"][...].astype(str))
    attrs = {
        k: (v.decode() if isinstance(v, bytes) else str(v)) for k, v in f.attrs.items()
    }
assert nm == nN, "snapshot layout != NOMSTIFF layout"
ia = nN.index("alphaS")
ref = dict(
    nomstiff=dict(
        file=NOM,
        nllvalreduced=float(fr["nllvalreduced"]),
        nllvalfull=float(fr["nllvalfull"]) if "nllvalfull" in fr else None,
        edmval=float(fr["edmval"]),
        sigma_alphaS=float(sN[ia]),
        lambdas_theta={n: float(xN[nN.index(n)]) for n in LAMS},
    ),
    cens03r_snapshot=dict(
        file=SNAP,
        attrs=attrs,
        dalphaS_over_sigma_vs_nomstiff=float((x[ia] - xN[ia]) / sN[ia]),
        lambdas_theta={n: float(x[nN.index(n)]) for n in LAMS},
        norm_dtheta_over_sigma=float(np.linalg.norm((x - xN) / sN)),
    ),
)
json.dump(ref, open(f"{TASK}/ref.json", "w"), indent=1)
print(json.dumps(ref, indent=1))

toks = shlex.split(meta["meta_info"]["command"])
os.makedirs(f"{TASK}/cmds", exist_ok=True)
os.makedirs(OUT, exist_ok=True)
for pf, c2 in (("C2A", True), ("R2A", False)):
    new = list(toks)

    def setval(flag, val):
        assert new.count(flag) == 1, flag
        new[new.index(flag) + 1] = val

    def settok(prefix, val):
        j = [k for k, t in enumerate(new) if t.startswith(prefix)]
        assert len(j) == 1, prefix
        new[j[0]] = prefix + val

    setval("-o", OUT)
    setval("--postfix", pf)
    setval("--externalPostfit", SNAP)
    setval("--snapshotFile", f"{OUT}/snapshot_fitresults_{pf}.hdf5")
    setval("--earlyStopping", "20")
    j = [k for k, t in enumerate(new) if t.startswith("prior_sigmas=")]
    assert len(j) == 1 and new[j[0]] == "prior_sigmas=lambda2_nu=nan"
    new[j[0]] = "prior_sigmas=" + PRIORS
    settok("cache=", f"{SUB}/cache.npz")
    settok("conf=", f"{SUB}/cache.conf")
    assert new.count("margin=0") == 1
    if c2:
        i = new.index("margin=0")
        new[i + 1 : i + 1] = ["smooth=c2", "delta=1e-3"]
    for bad in ("--noHessian", "--noEDM", "--noFit", "--stallRelTol", "--maxRestarts"):
        assert bad not in new, bad
    open(f"{TASK}/cmds/{pf}.cmd", "w").write(
        " ".join(shlex.quote(t) for t in new) + "\n"
    )
    print(f"--- {pf} vs NOMSTIFF:")
    for d in difflib.unified_diff(toks, new, lineterm="", n=0):
        if d.startswith(("+", "-")) and not d.startswith(("+++", "---")):
            print("   ", d[:300])
