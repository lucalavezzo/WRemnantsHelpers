#!/usr/bin/env python3
"""Build the T6 profile commands from NOMSTIFF's OWN meta_info command (pattern: census build_cmds.py).

Changes ONLY: -o, --postfix PROF<pt><start>, --snapshotFile, --externalPostfit <seed>,
--earlyStopping 100 -> 15, and ADDS --stallRelTol 1e-11 --maxRestarts 0 --freezeParameters alphaS.
Asserts that NOMSTIFF's command has no --freezeParameters / --stallRelTol / --maxRestarts of its own
(the param model's fit_params only decides which SCETlib directions exist in rabbit's vector; it does
not use rabbit's freeze mask, so `--freezeParameters alphaS` cannot collide with it).
Writes cmds/PROF*.cmd and cmds/seedmap.csv; prints the token diff.
"""
import csv
import difflib
import os
import shlex

from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
REF = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
OUT = f"{A}/261002_multistart_profile"
SEEDS = f"{OUT}/seeds"
TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDER = [f"PROF{pt}{st}" for pt in ("M1", "P1", "M2", "P2") for st in ("W", "R", "K")]

_, meta = io_tools.get_fitresult(REF, None, meta=True)
toks = shlex.split(meta["meta_info"]["command"])
for flag in (
    "--freezeParameters",
    "--stallRelTol",
    "--maxRestarts",
    "--noFit",
    "--unblind",
    "--doImpacts",
    "--computeSaturatedProjectionTests",
    "--scan",
):
    assert flag not in toks, f"NOMSTIFF command already has {flag}"
fp = [t for t in toks if t.startswith("fit_params=")]
assert len(fp) == 1 and "alphaS" in fp[0].split("=", 1)[1].split(","), fp
os.makedirs(f"{TASK}/cmds", exist_ok=True)
rows = []
for pf in ORDER:
    seed = f"{SEEDS}/{pf}.hdf5"
    assert os.path.exists(seed), seed
    new = list(toks)

    def setval(flag, val, old=None):
        assert new.count(flag) == 1, flag
        i = new.index(flag)
        if old is not None:
            assert new[i + 1] == old, (flag, new[i + 1])
        new[i + 1] = val

    setval("-o", OUT)
    setval("--postfix", pf, old="NOMSTIFF")
    setval("--snapshotFile", f"{OUT}/snapshot_fitresults_{pf}.hdf5")
    setval("--externalPostfit", seed)
    setval("--earlyStopping", "15", old="100")
    new += [
        "--stallRelTol",
        "1e-11",
        "--maxRestarts",
        "0",
        "--freezeParameters",
        "alphaS",
    ]
    assert new[new.index("--regularizationStrength") + 1] == "8"
    r = new.index("-r")
    assert new[r + 3] == "margin=0", new[r : r + 4]
    with open(f"{TASK}/cmds/{pf}.cmd", "w") as fh:
        fh.write(" ".join(shlex.quote(t) for t in new) + "\n")
    print(f"=== {pf}  seed {seed}")
    for d in difflib.unified_diff(toks, new, lineterm="", n=0):
        if d.startswith(("+", "-")) and not d.startswith(("+++", "---")):
            print("   ", d)
    rows.append((pf, seed))
with open(f"{TASK}/cmds/seedmap.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["postfix", "seed"])
    w.writerows(rows)
