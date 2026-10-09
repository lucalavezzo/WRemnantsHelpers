#!/usr/bin/env python3
"""Build the T2 stiff-wall refit commands from each reference fit's OWN meta_info command.

Changes ONLY: -o, --postfix, --snapshotFile, --regularizationStrength (5 -> 8), the -r block
(appends margin=0 after the mapping class) and --externalPostfit (-> the reference fitresult).
SPEED (Luca via orchestrator, 2026-09-30): also DROPS the postfit products -- "-m Project ch0 ptll",
--computeSaturatedProjectionTests, --doImpacts, --globalImpacts, --globalImpactsDisableJVP, --saveHists,
--computeHistErrors -- keeping the main fit + postfit Hessian (EDM, sigma, cov). NOT full-product fitresults.
Writes one line per fit to cmds/<POSTFIX>.cmd (shell-quoted) and prints a token diff.
"""
import os
import shlex

from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
OUT = f"{A}/260930_stiff_wall_fits"
TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WALL = "wremnants.postprocessing.scetlib_ad.np_damping_wall"
REFS = {
    "NOMSTIFF": f"{A}/260928_lattice_y35_fits/fitresults_LATL4ZY35WALLWARM.hdf5",
    "XWSTIFF": f"{A}/260924_y35_bin0xzero_fits/fitresults_Y35ZWALLWARM.hdf5",
    "XL4ZSTIFF": f"{A}/260929_l4zero_fits/fitresults_Y35ZWALLL4ZR.hdf5",
}


def build(postfix, ref):
    _, meta = io_tools.get_fitresult(ref, None, meta=True)
    toks = shlex.split(meta["meta_info"]["command"])
    new = list(toks)
    seen = set()

    def setval(flag, val):
        i = new.index(flag)
        new[i + 1] = val
        seen.add(flag)

    setval("-o", OUT)
    setval("--postfix", postfix)
    setval("--snapshotFile", f"{OUT}/snapshot_fitresults_{postfix}.hdf5")
    i = new.index("--regularizationStrength")
    assert new[i + 1] == "5", new[i + 1]
    new[i + 1] = "8"
    # exactly one -r block, W then M, nothing after M
    ridx = [k for k, t in enumerate(new) if t == "-r"]
    assert len(ridx) == 1, ridx
    r = ridx[0]
    assert (
        new[r + 1] == f"{WALL}.NPDampingWall"
        and new[r + 2] == f"{WALL}.NPDampingMapping"
    )
    assert new[r + 3].startswith("-"), new[r + 3]  # no mapping args in the reference
    new.insert(r + 3, "margin=0")
    setval("--externalPostfit", ref)
    # drop the postfit products (speed)
    k = new.index("-m")
    assert new[k + 1 : k + 4] == ["Project", "ch0", "ptll"], new[k : k + 4]
    del new[k : k + 4]
    for flag in (
        "--computeSaturatedProjectionTests",
        "--doImpacts",
        "--globalImpacts",
        "--globalImpactsDisableJVP",
        "--saveHists",
        "--computeHistErrors",
    ):
        new.remove(flag)
        assert flag not in new
    assert "-m" not in new
    # sanity: no --noFit, blinded (no --unblind), same card
    assert "--noFit" not in new and "--unblind" not in new
    return toks, new


os.makedirs(f"{TASK}/cmds", exist_ok=True)
for pf, ref in REFS.items():
    old, new = build(pf, ref)
    # the executable: keep the absolute rabbit_fit.py path from meta
    line = " ".join(shlex.quote(t) for t in new)
    with open(f"{TASK}/cmds/{pf}.cmd", "w") as f:
        f.write(line + "\n")
    print(f"=== {pf}  (ref {ref})")
    for k, (a, b) in enumerate(zip(old, new[: len(old)])):
        pass
    import difflib

    for d in difflib.unified_diff(old, new, lineterm="", n=1):
        if d.startswith(("+", "-")) and not d.startswith(("+++", "---")):
            print("   ", d)
