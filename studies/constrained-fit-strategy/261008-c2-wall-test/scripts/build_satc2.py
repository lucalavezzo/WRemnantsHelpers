#!/usr/bin/env python3
"""SATC2 = SATB8's command (../../lattice-cs-kernel/261007-lattice-term-native/cmds/SATB8.cmd) with ONLY:
  -o / --postfix / --snapshotFile   this task's ceph dir, SATC2
  NPDampingMapping margin=0         -> margin=0 smooth=c2 delta=1e-3
Same unseeded start (LATB8's flat seed), same lattice term, same --earlyStopping 100, same subset cache; run with
the gamma-nu-points SCETlib build exactly as SATB8 ran (run_fit.sh SATC2 <that build>).
"""
import os, shlex, difflib

T = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/lattice-cs-kernel/261007-lattice-term-native/cmds/SATB8.cmd"
OUT = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261008_c2_wall_test"
toks = shlex.split(open(SRC).read())
new = list(toks)


def setval(flag, val):
    assert new.count(flag) == 1, flag
    new[new.index(flag) + 1] = val


setval("-o", OUT)
setval("--postfix", "SATC2")
setval("--snapshotFile", f"{OUT}/snapshot_fitresults_SATC2.hdf5")
assert new.count("margin=0") == 1
i = new.index("margin=0")
new[i + 1 : i + 1] = ["smooth=c2", "delta=1e-3"]
open(f"{T}/cmds/SATC2.cmd", "w").write(" ".join(shlex.quote(t) for t in new) + "\n")
for d in difflib.unified_diff(toks, new, lineterm="", n=0):
    if d.startswith(("+", "-")) and not d.startswith(("+++", "---")):
        print("   ", d[:300])
