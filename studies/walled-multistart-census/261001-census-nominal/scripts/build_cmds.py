#!/usr/bin/env python3
"""Build the T4 census commands from NOMSTIFF's OWN meta_info command (pattern: T2 build_cmds.py).

Changes ONLY: -o, --postfix CENS<NN>, --snapshotFile, --externalPostfit <seed>, --earlyStopping 100 -> 20.
Everything else (card A + lattice, bin0xzero cache, tau 8, -r ... margin=0, fit_params freeze list, prior_sigmas,
threads, -v 4) is NOMSTIFF's own. Main fit + postfit Hessian only (NOMSTIFF already had no saturated/impacts/hists).
Writes cmds/CENS<NN>.cmd and cmds/seedmap.csv; prints the token diff.
"""
import csv
import difflib
import os
import shlex

from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
REF = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
OUT = f"{A}/261001_census_nominal"
SEEDS = f"{OUT}/seeds"
TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = [(f"CENS{i+1:02d}", f"{SEEDS}/pert_{i:03d}.hdf5") for i in range(8)] + [
    ("CENS09", f"{SEEDS}/cold_000.hdf5"),
    ("CENS10", f"{SEEDS}/cold_001.hdf5"),
]

_, meta = io_tools.get_fitresult(REF, None, meta=True)
toks = shlex.split(meta["meta_info"]["command"])
os.makedirs(f"{TASK}/cmds", exist_ok=True)
for pf, seed in MAP:
    assert os.path.exists(seed), seed
    new = list(toks)

    def setval(flag, val, old=None):
        i = new.index(flag)
        assert new.count(flag) == 1, flag
        if old is not None:
            assert new[i + 1] == old, (flag, new[i + 1])
        new[i + 1] = val

    setval("-o", OUT)
    setval("--postfix", pf, old="NOMSTIFF")
    setval("--snapshotFile", f"{OUT}/snapshot_fitresults_{pf}.hdf5")
    setval("--externalPostfit", seed)
    setval("--earlyStopping", "20", old="100")
    # sanity: configuration untouched
    assert new[new.index("--regularizationStrength") + 1] == "8"
    r = new.index("-r")
    assert new[r + 3] == "margin=0", new[r : r + 4]
    assert "--noFit" not in new and "--unblind" not in new and "-m" not in new
    assert "--doImpacts" not in new and "--computeSaturatedProjectionTests" not in new
    with open(f"{TASK}/cmds/{pf}.cmd", "w") as fh:
        fh.write(" ".join(shlex.quote(t) for t in new) + "\n")
    print(f"=== {pf}  seed {seed}")
    for d in difflib.unified_diff(toks, new, lineterm="", n=0):
        if d.startswith(("+", "-")) and not d.startswith(("+++", "---")):
            print("   ", d)
with open(f"{TASK}/cmds/seedmap.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["postfix", "seed"])
    w.writerows(MAP)
