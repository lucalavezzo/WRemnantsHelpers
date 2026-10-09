#!/usr/bin/env python3
"""Build the T8 fit commands from NOMSTIFF's OWN meta_info command (printed as token diffs into ../logs/build_cmds.log).
Common change (common.to_2d_card): 2D-lattice card, lambda4_nu in fit_params, prior_sigmas lambda2_nu=nan,lambda4_nu=nan.
  T8A  trust-constr, warm from NOMSTIFF (seed A, lambda4_nu = 0 on the boundary), mu0 1e-5, maxiter 300
  T8B  trust-constr, from the W point (seed B = XWSTIFF by name), mu0 1e-5, maxiter 600
  T8C  trust-krylov + stiff wall (NOMSTIFF's minimiser and flags), warm from NOMSTIFF's fitresult
trust-constr changes (as trust-constr-nominal/261006-tc-from-C): worktree rabbit, -r class -> npwall_tc.NPDampingWallTC
(same mapping, margin=0; penalty NOT in the loss), --earlyStopping -1 --maxRestarts 0, --minimizerMethod trust-constr
--minimizerGtol 1e-8 --minimizerXtol 1e-10 --minimizerBarrierTol 1e-9 --minimizerInitialBarrier 1e-5, --noHessian --noEDM.
HESS<pf>: the 2D-card command, --noFit at the TC result, NO -r / --regularizationStrength (data + priors + lattice only).
"""
import difflib
import os
import shlex
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

WALL = "wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingWall"
toks = C.nomstiff_tokens()
base, changes = C.to_2d_card(toks)
os.makedirs(f"{C.TASK}/cmds", exist_ok=True)
FITS = {
    "T8A": dict(seed=f"{C.OUT}/seeds/seed_A_NOMSTIFF_l4nu0.hdf5", tc=True, maxiter=300),
    "T8B": dict(seed=f"{C.OUT}/seeds/seed_B_XWSTIFF_in_2D.hdf5", tc=True, maxiter=600),
    "T8C": dict(seed=C.NOMSTIFF, tc=False),
    # Luca 10:20: trust-krylov + stiff wall with tau-continuation (constrained-fit-strategy/261006-diagnosis R1)
    "T8C5": dict(
        seed=f"{C.OUT}/seeds/seed_A_NOMSTIFF_l4nu0.hdf5", tc=False, tau="5", fast=True
    ),  # flat seed: --noHessian refuses a cov
    # 12:45 after the OOM kill of T8C5 (essentially converged at tau 5): tau 8 warm from T8C5's last SNAPSHOT
    # (fitresults_T8C5.hdf5 is rabbit's startup stub, never a result)
    "T8C8": dict(seed=f"{C.OUT}/snapshot_fitresults_T8C5.hdf5", tc=False, tau="8"),
    "T8P5R": dict(
        seed=f"{C.OUT}/snapshot_fitresults_T8P5.hdf5", tc=False, tau="5", fast=True
    ),
    "T8P5": dict(
        seed=f"{C.OUT}/seeds/seed_P_pert000_l4nuU.hdf5", tc=False, tau="5", fast=True
    ),
    "T8P8": dict(
        seed=f"{C.OUT}/fitresults_T8P5R.hdf5", tc=False, tau="8", needs_seed=False
    ),
    # relaunch of T8A (stopped 10:14: loss rising 376.94 -> 390.5 over 22 iterations, tr_radius ~1e-2, mu stuck at 1e-5)
    "T8A2": dict(
        seed=f"{C.OUT}/seeds/seed_A2_NOMSTIFF_l4nu1e-4.hdf5",
        tc=True,
        maxiter=300,
        mu0="1e-3",
    ),
}


def setval(new, flag, val, old=None):
    assert new.count(flag) == 1, flag
    i = new.index(flag)
    if old is not None:
        assert new[i + 1] == old, (flag, new[i + 1])
    new[i + 1] = val


ONLY = set(
    sys.argv[1:]
)  # rebuild only these postfixes (launched commands must stay as they ran)


def write(pf, new):
    if ONLY and pf not in ONLY:
        return
    with open(f"{C.TASK}/cmds/{pf}.cmd", "w") as fh:
        fh.write(" ".join(shlex.quote(t) for t in new) + "\n")
    print(f"=== {pf}  (vs NOMSTIFF's command; common: {changes})")
    for d in difflib.unified_diff(toks, new, lineterm="", n=0):
        if d.startswith(("+", "-")) and not d.startswith(("+++", "---")):
            print("   ", d)


assert toks[0].endswith("rabbit/bin/rabbit_fit.py")
for pf, o in FITS.items():
    assert os.path.exists(o["seed"]) or o.get("needs_seed") is False, o["seed"]
    new = list(base)
    new[0] = f"{C.RT}/bin/rabbit_fit.py"
    setval(new, "-o", C.OUT)
    setval(new, "--postfix", pf, old="NOMSTIFF")
    setval(new, "--snapshotFile", f"{C.OUT}/snapshot_fitresults_{pf}.hdf5")
    setval(new, "--externalPostfit", o["seed"])
    r = new.index("-r")
    assert new[r + 1] == WALL and new[r + 3] == "margin=0", new[r : r + 4]
    assert new[new.index("--regularizationStrength") + 1] == "8"
    assert (
        "--minimizerMethod" not in new
        and "--noFit" not in new
        and "--unblind" not in new
    )
    if "tau" in o:
        setval(new, "--regularizationStrength", o["tau"], old="8")
    if o.get("fast"):
        new += [
            "--noHessian",
            "--noEDM",
        ]  # intermediate continuation stage: no covariance needed
    if o["tc"]:
        new[r + 1] = "npwall_tc.NPDampingWallTC"
        setval(new, "--earlyStopping", "-1", old="100")
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
            "--minimizerInitialBarrier",
            o.get("mu0", "1e-5"),
            "--minimizerMaxiter",
            str(o["maxiter"]),
            "--noHessian",
            "--noEDM",
        ]
    write(pf, new)
    if o["tc"]:
        h = list(base)
        h[0] = f"{C.RT}/bin/rabbit_fit.py"
        setval(h, "-o", C.OUT)
        setval(h, "--postfix", f"HESS{pf}", old="NOMSTIFF")
        setval(h, "--snapshotFile", f"{C.OUT}/snapshot_fitresults_HESS{pf}.hdf5")
        setval(h, "--externalPostfit", f"{C.OUT}/fitresults_{pf}.hdf5")
        r = h.index("-r")
        del h[r : r + 4]
        i = h.index("--regularizationStrength")
        del h[i : i + 2]
        h += ["--noFit"]
        write(f"HESS{pf}", h)
