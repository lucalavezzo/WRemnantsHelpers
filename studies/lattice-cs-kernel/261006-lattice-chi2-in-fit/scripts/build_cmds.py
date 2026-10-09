#!/usr/bin/env python3
"""Build the fit commands of this task from NOMSTIFF's OWN meta_info command (token diffs printed to stdout).

Changes vs NOMSTIFF (Luca's brief, 2026-10-06):
  card          cardA_latticeASWZ_l4zero_statsyst.hdf5 -> plain card A (no lattice external term; XWSTIFF's card)
  fit_params    += lambda4_nu (after lambda2_nu)
  prior_sigmas  lambda2_nu=nan -> lambda2_nu=nan,lambda4_nu=nan,lambda2=1,lambda4=1,delta_lambda2=1
                (TMD priors pinned: the WRemnants default went TMD-free at 10:40 today; sigma 1 in theta = the old default)
  -r            + lattice_cs_chi2.LatticeCSChi2 lattice_cs_chi2.LatticeCSMapping syst=J offset=min alphas=frozen inputs=<npz>
                (second regularizer next to NOMSTIFF's NPDampingWall margin=0; exp(2 tau) compensated inside the term)
  -o/--postfix/--snapshotFile  this task's ceph dir
Stages (trust-krylov, NOMSTIFF's minimiser and flags otherwise):
  LATCHI5  tau = 5, warm from the flat seed NOMSTIFF + lambda4_nu = 0, --noHessian --noEDM
  LATCHI8  tau = 8, warm from fitresults_LATCHI5.hdf5, with Hessian + EDM (NOMSTIFF's own setting)
"""
import difflib
import os
import shlex

import h5py
import numpy as np
from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
NOMSTIFF = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
CARD_1D = f"{A}/260923_lattice_fits/cards/cardA_latticeASWZ_l4zero_statsyst.hdf5"
CARD_A = (
    f"{A}/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5"
)
OUT = f"{A}/261006_lattice_chi2_in_fit"
SEED = f"{OUT}/seeds/seed_A_NOMSTIFF_l4nu0.hdf5"
HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
INPUTS = f"{TASK}/lattice_aswz_inputs.npz"
PM = "wremnants.postprocessing.scetlib_ad.SCETlibADParamModel"
WALL = "wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingWall"
PRIORS = "lambda2_nu=nan,lambda4_nu=nan,lambda2=1,lambda4=1,delta_lambda2=1"
LAT = [
    "-r",
    "lattice_cs_chi2.LatticeCSChi2",
    "lattice_cs_chi2.LatticeCSMapping",
    "syst=J",
    "offset=min",
    "alphas=frozen",
    f"inputs={INPUTS}",
]


def setval(new, flag, val, old=None):
    assert new.count(flag) == 1, flag
    i = new.index(flag)
    if old is not None:
        assert new[i + 1] == old, (flag, new[i + 1])
    new[i + 1] = val


def check_seed():
    fr = io_tools.get_fitresult(NOMSTIFF, None)
    h = fr["parms"].get()
    nN = [str(n) for n in h.axes[0]]
    xN = np.asarray(h.values(), float)
    with h5py.File(SEED, "r") as f:
        x, nm = f["x"][...], list(f["parms"][...].astype(str))
        assert "cov" not in f
    assert nm == nN + ["lambda4_nu"], "seed layout"
    assert (
        np.array_equal(x[:-1].view(np.uint64), xN.view(np.uint64)) and x[-1] == 0.0
    ), "seed values"
    print(
        f"[seed] {SEED}: NOMSTIFF vector bit-identical + lambda4_nu theta = 0 ({len(nm)} params)"
    )


def main():
    check_seed()
    _, meta = io_tools.get_fitresult(NOMSTIFF, None, meta=True)
    toks = shlex.split(meta["meta_info"]["command"])
    assert toks[0].endswith("WRemnants/rabbit/bin/rabbit_fit.py"), toks[0]
    base = list(toks)
    assert base[1] == CARD_1D, base[1]
    base[1] = CARD_A
    i = base.index("--paramModel")
    assert base[i + 1] == PM
    j = i + 2
    seen = set()
    while j < len(base) and not base[j].startswith("-"):
        t = base[j]
        if t.startswith("fit_params="):
            fp = t[len("fit_params=") :].split(",")
            assert "lambda4_nu" not in fp and "lambda2_nu" in fp
            fp.insert(fp.index("lambda2_nu") + 1, "lambda4_nu")
            base[j] = "fit_params=" + ",".join(fp)
            seen.add("fp")
        elif t.startswith("prior_sigmas="):
            assert t == "prior_sigmas=lambda2_nu=nan", t
            base[j] = "prior_sigmas=" + PRIORS
            seen.add("ps")
        j += 1
    assert seen == {"fp", "ps"}
    r = base.index("-r")
    assert base[r + 1] == WALL and base[r + 3] == "margin=0", base[r : r + 4]
    assert (
        base.count("-r") == 1
        and "--minimizerMethod" not in base
        and "--noFit" not in base
    )
    assert "--unblind" not in base and "--saturated" not in " ".join(base)
    base = base[: r + 4] + LAT + base[r + 4 :]
    setval(base, "-o", OUT)
    os.makedirs(f"{TASK}/cmds", exist_ok=True)
    stages = {
        "LATCHI5": dict(tau="5", seed=SEED, fast=True),
        # 2026-10-06 ~14:30: LATCHI5 was SIGKILLed (node memory overload + reboot, exit 137) at iteration 11.
        # LATCHI5R = LATCHI5 resumed from its last periodic snapshot (iteration 11, loss 375.9647), frozen as a seed
        # copy (md5 cb475d5c...). LATCHI8 now warms from LATCHI5R.
        "LATCHI5R": dict(
            tau="5", seed=f"{OUT}/seeds/seed_LATCHI5_snapshot_1245.hdf5", fast=True
        ),
        "LATCHI8": dict(tau="8", seed=f"{OUT}/fitresults_LATCHI5R.hdf5", fast=False),
    }
    for pf, o in stages.items():
        new = list(base)
        setval(new, "--postfix", pf, old="NOMSTIFF")
        setval(new, "--snapshotFile", f"{OUT}/snapshot_fitresults_{pf}.hdf5")
        setval(new, "--externalPostfit", o["seed"])
        setval(new, "--regularizationStrength", o["tau"], old="8")
        if o["fast"]:
            new += ["--noHessian", "--noEDM"]
        with open(f"{TASK}/cmds/{pf}.cmd", "w") as fh:
            fh.write(" ".join(shlex.quote(t) for t in new) + "\n")
        print(f"=== {pf}: diff vs NOMSTIFF's command")
        for d in difflib.unified_diff(toks, new, lineterm="", n=0):
            if d.startswith(("+", "-")) and not d.startswith(("+++", "---")):
                print("   ", d[:400])


if __name__ == "__main__":
    main()
