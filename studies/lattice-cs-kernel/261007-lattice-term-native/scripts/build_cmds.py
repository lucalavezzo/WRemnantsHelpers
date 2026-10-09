#!/usr/bin/env python3
"""Commands for the native lattice term, built from 261006's LATFULL5 / LATFULL8 / ASIMFULL commands. The ONLY changes:
  -r ...lattice_cs_chi2.LatticeCSChi2 ...LatticeCSMapping syst=Jnf+Jbt pert=live offset=<x> [ydata=asimov]
  -> -r ...lattice_cs_term.LatticeCSTerm ...LatticeCSTermMapping syst=Jnf+Jbt offset=<x> [ydata=asimov]
  plus postfix, output dir (this task's ceph dir), snapshot file, --externalPostfit seed.
  LATB5    tau 5, warm from LATFULL8 (flat seed: LATFULL8's full vector, no cov), --noHessian --noEDM
  LATB8    tau 8, warm from LATB5, Hessian
  ASIMNAT  Asimov closure: one non-randomised expected toy, ydata=asimov offset=0, tau 8, --noHessian, start displaced
           (the 261006 seed: alphaS +1, lambda2_nu -0.5, lambda4_nu +0.01, resumTNP_gamma_nu +1, resumTNP_gamma_cusp -1)
  NCHK     the LATFULL8 command (old term) for nativecheck.py (replay + blinding checks, never minimised)
All run with the scetlib-cms gamma-nu-points build (run_fit.sh)."""
import difflib
import os
import shlex

import h5py
import numpy as np
from rabbit import io_tools, snapshot

OLD = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261006_lattice_chi2_in_fit"
OUT = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261007_lattice_term_native"
TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLDTASK = os.path.join(os.path.dirname(TASK), "261006-lattice-chi2-in-fit")
os.makedirs(f"{OUT}/seeds", exist_ok=True)
os.makedirs(f"{TASK}/cmds", exist_ok=True)

fr = io_tools.get_fitresult(f"{OLD}/fitresults_LATFULL8.hdf5", None)
h = fr["parms"].get()
names = np.array([str(n) for n in h.axes[0]])
x8 = np.asarray(h.values(), float)
s8 = f"{OUT}/seeds/seed_LATFULL8_flat.hdf5"
if not os.path.exists(s8):
    snapshot.write_snapshot(
        s8,
        names,
        x8,
        meta=dict(source="fitresults_LATFULL8.hdf5", rule="flat copy (no cov)"),
    )
with h5py.File(s8, "r") as f:
    assert (
        np.array_equal(f["x"][...].view(np.uint64), x8.view(np.uint64))
        and "cov" not in f
    )
sa = f"{OLD}/seeds/seed_ASIMFULL_displaced.hdf5"

OLD_R = [
    "wremnants.postprocessing.scetlib_ad.lattice_cs_chi2.LatticeCSChi2",
    "wremnants.postprocessing.scetlib_ad.lattice_cs_chi2.LatticeCSMapping",
]
NEW_R = [
    "wremnants.postprocessing.scetlib_ad.lattice_cs_term.LatticeCSTerm",
    "wremnants.postprocessing.scetlib_ad.lattice_cs_term.LatticeCSTermMapping",
]


def setval(new, flag, val, old=None):
    assert new.count(flag) == 1, flag
    i = new.index(flag)
    if old is not None:
        assert new[i + 1] == old, (flag, new[i + 1])
    new[i + 1] = val


def make(pf, src_pf, seed, swap=True):
    src = shlex.split(open(f"{OLDTASK}/cmds/{src_pf}.cmd").read())
    new = list(src)
    if swap:
        i = new.index(OLD_R[0])
        assert new[i + 1] == OLD_R[1]
        new[i : i + 2] = NEW_R
        new.remove("pert=live")
    setval(new, "--postfix", pf, old=src_pf)
    setval(new, "-o", OUT, old=OLD)
    setval(new, "--snapshotFile", f"{OUT}/snapshot_fitresults_{pf}.hdf5")
    setval(new, "--externalPostfit", seed)
    open(f"{TASK}/cmds/{pf}.cmd", "w").write(
        " ".join(shlex.quote(t) for t in new) + "\n"
    )
    print(f"=== {pf}: diff vs {src_pf}")
    for d in difflib.unified_diff(src, new, lineterm="", n=0):
        if d.startswith(("+", "-")) and not d.startswith(("+++", "---")):
            print("   ", d[:300])


make("LATB5", "LATFULL5", s8)
make("LATB8", "LATFULL8", f"{OUT}/fitresults_LATB5.hdf5")
make("ASIMNAT", "ASIMFULL", sa)
make("NCHK", "LATFULL8", s8, swap=False)
