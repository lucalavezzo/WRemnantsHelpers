#!/usr/bin/env python3
"""Build the trust-constr fit commands from NOMSTIFF's OWN meta_info command.

Changes ONLY (printed as a token diff):
  script         -> the trust-constr rabbit worktree's bin/rabbit_fit.py
  -o / --postfix / --snapshotFile
  --externalPostfit  NOMSTIFF itself (TCA) or a census seed (TCB*)
  -r class       NPDampingWall -> npwall_tc.NPDampingWallTC (same mapping, margin=0; constraint_spec added)
  --earlyStopping 100 -> -1 (off; a restart would reset the barrier parameter to 0.1) ; --maxRestarts 0
  + --minimizerMethod trust-constr --minimizerGtol 1e-8 --minimizerXtol 1e-10 --minimizerBarrierTol 1e-9
    --minimizerMaxiter <N>
  + --noHessian --noEDM (covariance in separate --noFit passes; an EDM is meaningless at an active face)
--regularizationStrength 8 is kept for provenance: under trust-constr the penalty is NOT in the loss.
Hessian-pass commands (HESS_<pf>): NOMSTIFF's command, --noFit --externalPostfit <TC result>, default
trust-krylov, NO -r (pure data Hessian; stiff / projected covariances are built offline by Sherman-Morrison).
"""
import difflib
import os
import shlex
import sys

from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
REF = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
OUT = f"{A}/261005_trust_constr_nominal"
SEEDS = f"{A}/261001_census_nominal/seeds"
RT = "/work/submit/lavezzo/rabbit-trustconstr"
TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FITS = {
    "TCA": (
        f"{OUT}/seed_NOMSTIFF_nocov.hdf5",
        300,
    ),  # NOMSTIFF x without cov (--noHessian refuses a cov)
    "TCB1": (f"{SEEDS}/cold_000.hdf5", 600),
    "TCB2": (f"{SEEDS}/pert_000.hdf5", 600),
}
WALL = "wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingWall"

_, meta = io_tools.get_fitresult(REF, None, meta=True)
toks = shlex.split(meta["meta_info"]["command"])
os.makedirs(f"{TASK}/cmds", exist_ok=True)


def setval(new, flag, val, old=None):
    i = new.index(flag)
    assert new.count(flag) == 1, flag
    if old is not None:
        assert new[i + 1] == old, (flag, new[i + 1])
    new[i + 1] = val


def write(pf, new):
    with open(f"{TASK}/cmds/{pf}.cmd", "w") as fh:
        fh.write(" ".join(shlex.quote(t) for t in new) + "\n")
    print(f"=== {pf}")
    for d in difflib.unified_diff(toks, new, lineterm="", n=0):
        if d.startswith(("+", "-")) and not d.startswith(("+++", "---")):
            print("   ", d)


assert toks[0].endswith("rabbit/bin/rabbit_fit.py")
for pf, (seed, maxiter) in FITS.items():
    assert os.path.exists(seed), seed
    new = list(toks)
    new[0] = f"{RT}/bin/rabbit_fit.py"
    setval(new, "-o", OUT)
    setval(new, "--postfix", pf, old="NOMSTIFF")
    setval(new, "--snapshotFile", f"{OUT}/snapshot_fitresults_{pf}.hdf5")
    setval(new, "--externalPostfit", seed)
    setval(new, "--earlyStopping", "-1", old="100")
    r = new.index("-r")
    assert new[r + 1] == WALL and new[r + 3] == "margin=0", new[r : r + 4]
    new[r + 1] = "npwall_tc.NPDampingWallTC"
    assert new[new.index("--regularizationStrength") + 1] == "8"
    assert (
        "--minimizerMethod" not in new
        and "--noFit" not in new
        and "--unblind" not in new
    )
    new += [
        "--maxRestarts",
        "0",
        "--minimizerMethod",
        "trust-constr",
        "--minimizerGtol",
        "1e-8",
        "--minimizerXtol",
        "1e-10",
        "--minimizerBarrierTol",
        "1e-9",
        "--minimizerMaxiter",
        str(maxiter),
        "--noHessian",
        "--noEDM",
    ]
    write(pf, new)

    # data-only Hessian pass at the trust-constr result
    h = list(toks)
    h[0] = f"{RT}/bin/rabbit_fit.py"
    setval(h, "-o", OUT)
    setval(h, "--postfix", f"HESS{pf}", old="NOMSTIFF")
    setval(h, "--snapshotFile", f"{OUT}/snapshot_fitresults_HESS{pf}.hdf5")
    setval(h, "--externalPostfit", f"{OUT}/fitresults_{pf}.hdf5")
    r = h.index("-r")
    del h[r : r + 4]  # no regularizer: pure data Hessian
    i = h.index("--regularizationStrength")
    del h[i : i + 2]
    h += ["--noFit"]
    write(f"HESS{pf}", h)
