#!/usr/bin/env python3
"""Phase-3 commands (pert=live: alpha_s + CS-kernel TNPs), from LATLIVE8Y's command (subset cache |Y|<=2.5).
Changes vs LATLIVE8Y: syst=Jnf+Jbt+pert -> syst=<SYST> (default Jnf+Jbt: mu0 scale variation dropped), alphas=live ->
pert=live (WRemnants 3ef3efb9).
  LATFULL5   tau 5, warm from LATLIVE8Y (flat seed), --noHessian --noEDM ; LATFULL8 tau 8 warm from LATFULL5, Hessian
  ASIMFULL   one non-randomised expected toy (-t 1 --toysDataMode expected --toysDataRandomize none
             --toysSystRandomize none), lattice ydata=asimov offset=0, tau 8, --noHessian; start displaced:
             alphaS +1, lambda2_nu -0.5, lambda4_nu +0.01, resumTNP_gamma_nu +1, resumTNP_gamma_cusp -1
  BLINDFULL  the LATFULL8 command for blindcheck.py (alpha_s and TNP source checks, never minimised)
  LATDNF5/8  as LATFULL5/8 with syst=direct_nf+Jbt (only if the Newton comparison asks for it)
"""
import difflib
import os
import shlex

import h5py
import numpy as np
from rabbit import io_tools, snapshot

OUT = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261006_lattice_chi2_in_fit"
TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = shlex.split(open(f"{TASK}/cmds/LATLIVE8Y.cmd").read())
fr = io_tools.get_fitresult(f"{OUT}/fitresults_LATLIVE8Y.hdf5", None)
h = fr["parms"].get()
names = np.array([str(n) for n in h.axes[0]])
xL = np.asarray(h.values(), float)
sL = f"{OUT}/seeds/seed_LATLIVE8Y_flat.hdf5"
if not os.path.exists(sL):
    snapshot.write_snapshot(
        sL,
        names,
        xL,
        meta=dict(source="fitresults_LATLIVE8Y.hdf5", rule="flat copy (no cov)"),
    )
nl = list(names)
xa = np.zeros(len(names))
for k, v in (
    ("alphaS", 1.0),
    ("lambda2_nu", -0.5),
    ("lambda4_nu", 0.01),
    ("resumTNP_gamma_nu", 1.0),
    ("resumTNP_gamma_cusp", -1.0),
):
    xa[nl.index(k)] = v
sa = f"{OUT}/seeds/seed_ASIMFULL_displaced.hdf5"
if not os.path.exists(sa):
    snapshot.write_snapshot(
        sa,
        names,
        xa,
        meta=dict(
            source="zeros (Asimov truth) displaced",
            rule="aS+1 l2nu-.5 l4nu+.01 tnpnu+1 tnpcusp-1",
        ),
    )
for p, x in ((sL, xL), (sa, xa)):
    with h5py.File(p, "r") as f:
        assert (
            np.array_equal(f["x"][...].view(np.uint64), x.view(np.uint64))
            and "cov" not in f
        )


def setval(new, flag, val, old=None):
    assert new.count(flag) == 1, flag
    i = new.index(flag)
    if old is not None:
        assert new[i + 1] == old, (flag, new[i + 1])
    new[i + 1] = val


def make(pf, tau, seed, syst="Jnf+Jbt", extra=(), asimov=False):
    new = list(src)
    i = new.index("syst=Jnf+Jbt+pert")
    new[i] = f"syst={syst}"
    new[new.index("alphas=live")] = "pert=live"
    setval(new, "--postfix", pf, old="LATLIVE8Y")
    setval(new, "--snapshotFile", f"{OUT}/snapshot_fitresults_{pf}.hdf5")
    setval(new, "--externalPostfit", seed)
    setval(new, "--regularizationStrength", tau, old="8")
    if asimov:
        setval(new, "-t", "1", old="0")
        k = new.index("offset=min")
        new[k : k + 1] = ["offset=0", "ydata=asimov"]
        extra = list(extra) + [
            "--toysDataMode",
            "expected",
            "--toysDataRandomize",
            "none",
            "--toysSystRandomize",
            "none",
        ]
    new += list(extra)
    open(f"{TASK}/cmds/{pf}.cmd", "w").write(
        " ".join(shlex.quote(t) for t in new) + "\n"
    )
    print(f"=== {pf}: diff vs LATLIVE8Y")
    for d in difflib.unified_diff(src, new, lineterm="", n=0):
        if d.startswith(("+", "-")) and not d.startswith(("+++", "---")):
            print("   ", d[:300])


make("LATFULL5", "5", sL, extra=["--noHessian", "--noEDM"])
make("LATFULL8", "8", f"{OUT}/fitresults_LATFULL5.hdf5")
make("BLINDFULL", "8", sL)
make("ASIMFULL", "8", sa, extra=["--noHessian"], asimov=True)
make("LATDNF5", "5", sL, syst="direct_nf+Jbt", extra=["--noHessian", "--noEDM"])
make("LATDNF8", "8", f"{OUT}/fitresults_LATDNF5.hdf5", syst="direct_nf+Jbt")
