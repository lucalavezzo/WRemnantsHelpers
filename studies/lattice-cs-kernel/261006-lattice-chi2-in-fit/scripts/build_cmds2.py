#!/usr/bin/env python3
"""Phase-2 commands (alpha_s-live lattice term), built from LATCHI5R's command (itself NOMSTIFF's meta command with the
phase-1 changes; see build_cmds.py). Changes vs LATCHI5R:
  -r lattice term -> the COMMITTED WRemnants module (44f8a5c0) wremnants.postprocessing.scetlib_ad.lattice_cs_chi2,
     package-data inputs, syst=Jnf+Jbt+pert (Luca: no k-form; + pert-kernel scale variation), alphas=live, offset=min
  LATLIVE5  tau 5, warm from LATCHI8 (flat seed: LATCHI8 carries a covariance), --noHessian --noEDM
  LATLIVE8  tau 8, warm from LATLIVE5, Hessian + EDM
  ASIMLIVE  -t -1 (Asimov of card A at the model default), lattice ydata=asimov offset=0, tau 8, --noHessian (EDM via
            CG); start displaced from the truth: alphaS theta +1, lambda2_nu theta -0.5, lambda4_nu theta +0.01
  BLINDCHK  the LATLIVE8 command, consumed by blindcheck.py (fitter built, never minimised)
Seeds written to <OUT>/seeds/."""
import difflib
import os
import shlex

import h5py
import numpy as np
from rabbit import io_tools, snapshot

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
OUT = f"{A}/261006_lattice_chi2_in_fit"
TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = "wremnants.postprocessing.scetlib_ad.lattice_cs_chi2"
src = shlex.split(open(f"{TASK}/cmds/LATCHI5R.cmd").read())


def setval(new, flag, val, old=None):
    assert new.count(flag) == 1, flag
    i = new.index(flag)
    if old is not None:
        assert new[i + 1] == old, (flag, new[i + 1])
    new[i + 1] = val


# seeds
fr = io_tools.get_fitresult(f"{OUT}/fitresults_LATCHI8.hdf5", None)
h = fr["parms"].get()
names = np.array([str(n) for n in h.axes[0]])
x8 = np.asarray(h.values(), float)
s8 = f"{OUT}/seeds/seed_LATCHI8_flat.hdf5"
if not os.path.exists(s8):
    snapshot.write_snapshot(
        s8,
        names,
        x8,
        meta=dict(source="fitresults_LATCHI8.hdf5", rule="flat copy (no cov)"),
    )
xa = np.zeros(len(names))
nl = list(names)
xa[nl.index("alphaS")] = 1.0
xa[nl.index("lambda2_nu")] = -0.5
xa[nl.index("lambda4_nu")] = 0.01
sa = f"{OUT}/seeds/seed_ASIM_displaced.hdf5"
if not os.path.exists(sa):
    snapshot.write_snapshot(
        sa,
        names,
        xa,
        meta=dict(
            source="zeros (Asimov truth) displaced", rule="aS+1, l2nu-0.5, l4nu+0.01"
        ),
    )
for p, x in ((s8, x8), (sa, xa)):
    with h5py.File(p, "r") as f:
        assert (
            np.array_equal(f["x"][...].view(np.uint64), x.view(np.uint64))
            and "cov" not in f
        )

r = [i for i, t in enumerate(src) if t == "-r"][1]
assert src[r + 1] == "lattice_cs_chi2.LatticeCSChi2", src[r : r + 8]
j = r + 2
while not src[j].startswith("-"):
    j += 1
base = (
    src[:r]
    + [
        "-r",
        f"{MOD}.LatticeCSChi2",
        f"{MOD}.LatticeCSMapping",
        "syst=Jnf+Jbt+pert",
        "alphas=live",
        "offset=min",
    ]
    + src[j:]
)
assert "--noHessian" in base and "--noEDM" in base
base = [t for t in base if t not in ("--noHessian", "--noEDM")]
STAGES = {
    "LATLIVE5": dict(tau="5", seed=s8, extra=["--noHessian", "--noEDM"]),
    "LATLIVE8": dict(tau="8", seed=f"{OUT}/fitresults_LATLIVE5.hdf5", extra=[]),
    "BLINDCHK": dict(tau="8", seed=s8, extra=[]),
    "ASIMLIVE": dict(tau="8", seed=sa, extra=["--noHessian"], asimov=True),
    # rabbit never minimises -t -1 (bin/rabbit_fit.py: dofit = ifit >= 0), so ASIMLIVE only evaluated the truth point.
    # ASIMLIVE2 = the same, as ONE non-randomised expected toy: fitted, unblinded (toysDataMode expected).
    "ASIMLIVE2": dict(
        tau="8",
        seed=sa,
        extra=[
            "--noHessian",
            "--toysDataMode",
            "expected",
            "--toysDataRandomize",
            "none",
            "--toysSystRandomize",
            "none",
        ],
        asimov=True,
        ntoy="1",
    ),
}
for pf, o in STAGES.items():
    new = list(base)
    setval(new, "--postfix", pf, old="LATCHI5R")
    setval(new, "--snapshotFile", f"{OUT}/snapshot_fitresults_{pf}.hdf5")
    setval(new, "--externalPostfit", o["seed"])
    setval(new, "--regularizationStrength", o["tau"], old="5")
    if o.get("asimov"):
        setval(new, "-t", o.get("ntoy", "-1"), old="0")
        k = new.index("offset=min")
        new[k : k + 1] = ["offset=0", "ydata=asimov"]
    new += o["extra"]
    open(f"{TASK}/cmds/{pf}.cmd", "w").write(
        " ".join(shlex.quote(t) for t in new) + "\n"
    )
    print(f"=== {pf}: diff vs LATCHI5R")
    for d in difflib.unified_diff(src, new, lineterm="", n=0):
        if d.startswith(("+", "-")) and not d.startswith(("+++", "---")):
            print("   ", d[:300])
