#!/usr/bin/env python3
"""Build the two restart commands from the references' OWN meta_info commands (pattern: 261001-census-nominal).

CMR1A = NOMSTIFF's command (card A + lattice, lambda4_nu frozen at 0, bin0xzero cache, tau 8, margin=0)
CMR1B = XWSTIFF's command  (card A, no lattice, lambda4_nu free,   bin0xzero cache, tau 8, margin=0)
Changes ONLY: -o, --postfix, --snapshotFile, --externalPostfit <seed>, --earlyStopping -> 20
(NOMSTIFF had 100; XWSTIFF had none = rabbit default 20, so 1b's is made explicit at the same value).
Main fit + its postfit Hessian (neither reference ran saturated/impacts/hists).
"""
import difflib
import os
import shlex

from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
OUT = f"{A}/261005_cold_min_restart"
TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOBS = [
    (
        "CMR1A",
        "NOMSTIFF",
        f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5",
        f"{OUT}/seeds/seed_1a_C_in_NOMSTIFF.hdf5",
    ),
    (
        "CMR1B",
        "XWSTIFF",
        f"{A}/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5",
        f"{OUT}/seeds/seed_1b_C_in_XWSTIFF.hdf5",
    ),
]
os.makedirs(f"{TASK}/cmds", exist_ok=True)
for pf, refname, ref, seed in JOBS:
    assert os.path.exists(seed), seed
    _, meta = io_tools.get_fitresult(ref, None, meta=True)
    toks = shlex.split(meta["meta_info"]["command"])
    new = list(toks)

    def setval(flag, val, old=None):
        assert new.count(flag) == 1, flag
        i = new.index(flag)
        if old is not None:
            assert new[i + 1] == old, (flag, new[i + 1])
        new[i + 1] = val

    setval("-o", OUT)
    setval("--postfix", pf, old=refname)
    setval("--snapshotFile", f"{OUT}/snapshot_fitresults_{pf}.hdf5")
    setval("--externalPostfit", seed)
    if "--earlyStopping" in new:
        setval("--earlyStopping", "20", old="100")
    else:
        new += ["--earlyStopping", "20"]
    assert new[new.index("--regularizationStrength") + 1] == "8"
    r = new.index("-r")
    assert new[r + 3] == "margin=0", new[r : r + 4]
    assert "--noFit" not in new and "--unblind" not in new and "-m" not in new
    assert (
        "--doImpacts" not in new
        and "--computeSaturatedProjectionTests" not in new
        and "--noHessian" not in new
    )
    with open(f"{TASK}/cmds/{pf}.cmd", "w") as fh:
        fh.write(" ".join(shlex.quote(t) for t in new) + "\n")
    print(f"=== {pf} (from {refname})  seed {seed}")
    for d in difflib.unified_diff(toks, new, lineterm="", n=0):
        if d.startswith(("+", "-")) and not d.startswith(("+++", "---")):
            print("   ", d)
