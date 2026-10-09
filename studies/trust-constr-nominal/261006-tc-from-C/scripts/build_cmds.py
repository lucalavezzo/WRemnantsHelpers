#!/usr/bin/env python3
"""Build the trust-constr fit command from XWSTIFF's OWN meta_info command (card A, no lattice, lambda4_nu FREE,
pdf62_y35_260921/merged_full_bin0xzero cache, stiff wall tau=8 margin 0), seeded at C mapped into XWSTIFF's frame.

Changes ONLY (printed as a token diff):
  script         -> the trust-constr rabbit worktree's bin/rabbit_fit.py
  -o / --postfix / --snapshotFile
  --externalPostfit  seed_1b_C_in_XWSTIFF.hdf5 (flat x+parms, no cov; INFEASIBLE in lambda4_nu by 1.85e-4, used verbatim)
  -r class       NPDampingWall -> npwall_tc.NPDampingWallTC (same mapping, margin=0; constraint_spec added)
  + --earlyStopping -1 (XWSTIFF had rabbit's default 20; a restart would reset the barrier) ; --maxRestarts 0
  + --minimizerMethod trust-constr --minimizerGtol 1e-8 --minimizerXtol 1e-10 --minimizerBarrierTol 1e-9
    --minimizerInitialBarrier 1e-3 --minimizerMaxiter 600
  + --noHessian --noEDM
--regularizationStrength 8 is kept for provenance: under trust-constr the penalty is NOT in the loss.
Hessian pass (HESS<pf>): XWSTIFF's command, --noFit --externalPostfit <TC result>, default trust-krylov, NO -r
(pure data Hessian; stiff / projected covariances offline by Sherman-Morrison).
"""
import difflib
import os
import shlex
import sys

from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
REF = f"{A}/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5"
OUT = f"{A}/261006_tc_from_C"
RT = "/work/submit/lavezzo/rabbit-trustconstr"
TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# pf: (seed, maxiter, mu0, pin TMD priors explicitly)
# TCC1R (2026-10-06 12:30): TCC1 was OOM-killed at it 65; restart from its it-63 snapshot (copied to seed_TCC1_it63.hdf5),
# mu0 = 1e-4 (TCC1 had reached 4e-5), and the TMD priors pinned because the 10:40 WRemnants default freed them.
FITS = {
    "TCC1": (
        f"{A}/261005_cold_min_restart/seeds/seed_1b_C_in_XWSTIFF.hdf5",
        600,
        "1e-3",
        False,
    ),
    "TCC1R": (f"{OUT}/seed_TCC1_it63.hdf5", 600, "1e-4", True),
}
PRIORS = "prior_sigmas=lambda2=1,lambda4=1,delta_lambda2=1"
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
for pf, (seed, maxiter, mu0, pin) in FITS.items():
    assert os.path.exists(seed), seed
    new = list(toks)
    new[0] = f"{RT}/bin/rabbit_fit.py"
    setval(new, "-o", OUT)
    setval(new, "--postfix", pf, old="XWSTIFF")
    setval(new, "--snapshotFile", f"{OUT}/snapshot_fitresults_{pf}.hdf5")
    setval(new, "--externalPostfit", seed)
    assert "--earlyStopping" not in new
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
        "--earlyStopping",
        "-1",
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
        "--minimizerInitialBarrier",
        mu0,
        "--minimizerMaxiter",
        str(maxiter),
        "--noHessian",
        "--noEDM",
    ]
    if pin:
        assert not any(t.startswith("prior_sigmas=") for t in new)
        new.insert(new.index("threads=128") + 1, PRIORS)
    write(pf, new)

    # data-only Hessian pass at the trust-constr result
    h = list(toks)
    h[0] = f"{RT}/bin/rabbit_fit.py"
    setval(h, "-o", OUT)
    setval(h, "--postfix", f"HESS{pf}", old="XWSTIFF")
    setval(h, "--snapshotFile", f"{OUT}/snapshot_fitresults_HESS{pf}.hdf5")
    setval(h, "--externalPostfit", f"{OUT}/fitresults_{pf}.hdf5")
    r = h.index("-r")
    del h[r : r + 4]  # no regularizer: pure data Hessian
    i = h.index("--regularizationStrength")
    del h[i : i + 2]
    h += ["--noFit"]
    # 2026-10-06 10:40 the WRemnants default freed lambda2/lambda4/delta_lambda2 (no TMD priors; params.py FREE_PARAMS).
    # TCC1 and XWSTIFF ran with sigma=1 priors on them, so the Hessian pass must restore them explicitly.
    assert not any(t.startswith("prior_sigmas=") for t in h)
    ithr = h.index("threads=128")
    h.insert(ithr + 1, PRIORS)
    write(f"HESS{pf}", h)
