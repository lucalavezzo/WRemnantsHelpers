#!/usr/bin/env python3
"""Four-way read of the preconditioning arms: plain / ridge / spectral / walled.

Convergence and cost come from the run logs (nit, nhev, minimize(s), edm are not
all in the fitresult); the NP tune, the damping conditions and sigma(alpha_s)
come from each fitresult.

POLICY: alphaS's CENTRAL value is blinded and is never printed. sigma IS safe
under additive blinding -- that is the whole point of 0f64bbb.

usage: compare_arms.py [spectral_fitresult.hdf5]
"""
import os
import shutil
import sys
import time

import numpy as np
from scipy import stats

CEPH = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
CARD = f"{CEPH}/study_scratch/260910-anchor-verify/card_none.hdf5"

# Everything here is read off the arm's own log; the log path is recorded so a
# reader can check any number. `walled` carries a wall penalty in `fun`, so its
# loss is NOT on the same footing as the three unwalled ones -- flagged below.
ARMS = [
    dict(
        tag="plain",
        postfix="DATABLIND",
        fit=f"{CEPH}/260910_blinding_final/fitresults_DATABLIND.hdf5",
        fun=405.5608736721634,
        nit=221,
        nfev=209,
        nhev=766,
        minimize_s=2645.4,
        edm=1.3863650682068962e-3,
        sat_2dnll=811.12,
        sat_ndof=733,
        lin_chi2=809.0,
        lin_ndof=780,
        sat_p=2.33,
        lin_p=22.66,
        load0=789.17,
        wall="1:04:19",
        precond=None,
        walled=False,
        log="../260910-blinding/logs/fit_DATABLIND_260910_151034.log",
    ),
    dict(
        tag="ridge",
        postfix="DATAPC2",
        fit=f"{CEPH}/260910_blinding_final/fitresults_DATAPC2.hdf5",
        fun=411.07536511212595,
        nit=292,
        nfev=290,
        nhev=2087,
        minimize_s=4048.6,
        edm=4.90898326250476e-6,
        sat_2dnll=822.15,
        sat_ndof=733,
        lin_chi2=820.0,
        lin_ndof=780,
        sat_p=1.20,
        lin_p=15.74,
        load0=278.01,
        wall="1:11:02",
        precond="ridge 0.0593 x max|diag|",
        walled=False,
        log="../260910-blinding/logs/fit_DATAPC2_260910_162332.log",
    ),
    dict(
        tag="spectral",
        postfix="DATASPEC",
        # STOPPED, NOT CONVERGED. SIGTERM at iteration 719 / 8593.6 s of
        # minimize(), still descending. scipy therefore never returned an
        # OptimizeResult, so nfev/njev/nhev do not exist for this arm -- the
        # one cost number that is load-independent is the one we cannot have.
        # EDM / sigma / saturated chi2 come from the two-pass readout at the
        # reached point (--noFit --externalPostfit <snapshot>).
        fit=f"{CEPH}/260910_spectral/fitresults_DATASPECPF.hdf5",
        fun=412.7846233862512,
        nit=719,
        nfev=None,
        nhev=None,
        minimize_s=8593.6,
        edm=1.4571366798984388e-7,
        sat_2dnll=825.57,
        sat_ndof=733,
        lin_chi2=775.0,
        lin_ndof=780,
        sat_p=0.96,
        lin_p=54.17,
        load0=284.23,
        wall="2:27:43 (SIGTERM)",
        precond="spectral",
        walled=False,
        log="logs/fit_DATASPEC_260910_173516.log",
    ),
    dict(
        tag="walled",
        postfix="DATAWALL5",
        fit=f"{CEPH}/260910_wall_port/fitresults_DATAWALL5.hdf5",
        fun=411.9912132618329,
        nit=138,
        nfev=137,
        nhev=624,
        minimize_s=1509.2,
        edm=9.632386862470065e-7,
        sat_2dnll=823.98,
        sat_ndof=733,
        lin_chi2=818.0,
        lin_ndof=780,
        sat_p=1.07,
        lin_p=16.54,
        load0=339.71,
        wall="0:29:49 (no --doImpacts)",
        precond=None,
        walled=True,
        log="../260910-wall-port/logs/fit_DATAWALL5_260910_165137.log",
    ),
]

from rabbit import inputdata, io_tools  # noqa: E402

from wremnants.postprocessing.scetlib_ad import np_damping_wall as wall  # noqa: E402

WIDTH_AS = 0.002  # alphaS: theta -> Delta(alpha_s) per unit theta
MODEL_PREFIXES = (
    "alphaS",
    "lambda",
    "delta_lambda",
    "b0_over_bmax",
    "resumTNP_",
    "resumScale",
    "resumTransition",
    "pdfEig",
)


SCRATCH = "/tmp/spectral_precond_arms"


def _local_copy(path):
    """Copy a FINISHED fitresult to /tmp and read that instead.

    Why not read it in place: another session's saturated-projection job holds
    these same files, and h5py then fails with BlockingIOError (errno 11).
    `cp` takes no HDF5 lock, so a copy always succeeds and cannot perturb the
    other job. Only ever used on files that are complete -- a fit still running
    holds its own output open for writing and a copy of THAT would be torn.
    """
    os.makedirs(SCRATCH, exist_ok=True)
    dst = os.path.join(SCRATCH, os.path.basename(path))
    if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(path):
        shutil.copy2(path, dst)
        print(
            f"[copy] {os.path.basename(path)} -> {dst} "
            f"({os.path.getsize(dst) / 1e6:.0f} MB)"
        )
    return dst


def read(path, tries=40, wait=15.0):
    """Read one fitresult, waiting out contention rather than forcing it.

    Another session runs saturated-projection jobs that load these same
    fitresults with --externalPostfit, and a fit still in progress holds its own
    output open for writing. Both show up as an h5py open failure. Retry.

    Do NOT "fix" this with HDF5_USE_FILE_LOCKING=FALSE: tried, and it turns a
    clean BlockingIOError into a half-consistent read ("bad object header
    version number"), i.e. it replaces waiting with silently wrong data.
    """
    last = None
    for k in range(tries):
        try:
            res = io_tools.get_fitresult(_local_copy(path))
            h = res["parms"].get()
            names = [str(n) for n in h.axes[0]]
            return names, h.values(), np.sqrt(h.variances())
        except (BlockingIOError, OSError) as ex:
            last = ex
            if k == 0:
                print(
                    f"[wait] {os.path.basename(path)} is busy ({ex}); "
                    f"retrying every {wait:g}s"
                )
            time.sleep(wait)
    raise RuntimeError(f"could not read {path} after {tries} tries: {last}")


def main():
    if len(sys.argv) > 1:
        ARMS[2]["fit"] = sys.argv[1]

    inp = wall.resolve_wall_inputs(inputdata.FitInputData(CARD))
    conds = wall.damping_conditions(inp["np_model"], inp["np_model_nu"], inp["ymax"])

    live = []
    for a in ARMS:
        # A fit still in flight has created its output but written almost
        # nothing (rabbit holds it open and writes at the end), so size is the
        # reliable "is this arm finished" test -- not existence.
        if not os.path.exists(a["fit"]) or os.path.getsize(a["fit"]) < 10_000_000:
            state = (
                "no fitresult yet"
                if not os.path.exists(a["fit"])
                else f"fitresult still being written "
                f"({os.path.getsize(a['fit']) / 1e6:.1f} MB)"
            )
            print(f"[skip] {a['tag']:9s} {state}: {a['fit']}")
            continue
        names, vals, errs = read(a["fit"])
        a["names"], a["vals"], a["errs"] = names, vals, errs
        a["theta"] = {n: float(vals[i]) for i, n in enumerate(names)}
        a["sig"] = {n: float(errs[i]) for i, n in enumerate(names)}
        a["phys"] = {
            n: (
                float(wall.physical_from_theta(inp["specs"][n], a["theta"][n]))
                if n in a["theta"]
                else float(inp["anchors"][n])
            )
            for n in inp["names"]
        }
        live.append(a)

    W = 13

    def row(label, fmt, key=None, fn=None):
        cells = []
        for a in live:
            v = fn(a) if fn else a.get(key)
            if v is None:
                cells.append("n/a".rjust(W))
            elif fmt == "s":
                cells.append(str(v)[: W - 1].rjust(W))
            else:
                cells.append(format(v, fmt).rjust(W))
        print(f"  {label:34s}" + "".join(cells))

    print("=" * (36 + W * len(live)))
    print("CONVERGENCE AND COST")
    print("=" * (36 + W * len(live)))
    print("  " + "arm".ljust(34) + "".join(a["tag"].rjust(W) for a in live))
    print("  " + "postfix".ljust(34) + "".join(a["postfix"].rjust(W) for a in live))
    print("-" * (36 + W * len(live)))
    row("loss (fun)", ".4f", "fun")
    row(
        "  [spectral: STOPPED, not converged]",
        "s",
        fn=lambda a: "STOPPED" if a["tag"] == "spectral" else "",
    )
    row(
        "  [walled: includes wall penalty]",
        "s",
        fn=lambda a: "yes" if a["walled"] else "",
    )
    row("iterations (nit)", "d", "nit")
    row("Hessian-vector products (nhev)", "d", "nhev")
    row(
        "nhev / nit",
        ".2f",
        fn=lambda a: (a["nhev"] / a["nit"]) if a["nhev"] and a["nit"] else None,
    )
    row("minimize() [s]", ".0f", "minimize_s")
    row(
        "  s / iteration",
        ".1f",
        fn=lambda a: (
            (a["minimize_s"] / a["nit"]) if a["minimize_s"] and a["nit"] else None
        ),
    )
    row("loadavg at launch", ".0f", "load0")
    row("total wall clock", "s", fn=lambda a: a["wall"] or None)
    print("    (walled ran WITHOUT --doImpacts: not like-for-like)")
    row("EDM", ".3e", "edm")
    row("saturated 2*dNLL", ".2f", "sat_2dnll")
    row("saturated p-value [%] (as logged)", ".2f", "sat_p")
    row("linear chi2 / 780", ".0f", "lin_chi2")
    row("linear p-value [%] (as logged)", ".2f", "lin_p")
    print("-" * (36 + W * len(live)))
    row("sigma(theta_alphaS)", ".6f", fn=lambda a: a["sig"]["alphaS"])
    row("sigma(alpha_s)", ".6f", fn=lambda a: a["sig"]["alphaS"] * WIDTH_AS)
    print("  [alphaS CENTRAL VALUE IS BLINDED - not printed]")

    # ---- loss deltas, in chi2 units, against the plain arm
    base = next((a for a in live if a["tag"] == "plain"), None)
    if base and base["fun"]:
        print()
        print("--- loss relative to the plain arm (chi2 = 2 x NLL) ---")
        for a in live:
            if a["fun"] is None:
                continue
            pen = 0.0
            if a["walled"]:
                pen = sum(
                    float(c.penalty(a["phys"], wall.numpy_relu2)) for c in conds
                ) * np.exp(2 * 5.0)
            d = a["fun"] - pen - base["fun"]
            note = f"  (wall penalty {pen:.4f} removed)" if a["walled"] else ""
            print(
                f"  {a['tag']:9s} Delta(pure NLL) {d:+8.4f}   "
                f"Delta(chi2) {2 * d:+8.3f}{note}"
            )

    # ---- where in NP space did each arm stop?
    print()
    print("=" * (36 + W * len(live)))
    print("PHYSICAL NP TUNE  (anchor + width*theta)")
    print("=" * (36 + W * len(live)))
    print(
        "  "
        + "lambda".ljust(20)
        + "anchor".rjust(10)
        + "".join(a["tag"].rjust(W) for a in live)
    )
    print("-" * (36 + W * len(live)))
    for n in inp["names"]:
        cells = "".join(format(a["phys"][n], ".6f").rjust(W) for a in live)
        held = "" if n in live[0]["theta"] else "  (held)"
        print(f"  {n:20s}{float(inp['anchors'][n]):10.5f}{cells}{held}")

    print()
    print("--- damping conditions: how many are UNPHYSICAL (coeff < 0) ---")
    for a in live:
        bad = [
            (c.label, float(c.value(a["phys"], wall.numpy_relu2)))
            for c in conds
            if float(c.value(a["phys"], wall.numpy_relu2)) < 0.0
        ]
        pen = sum(float(c.penalty(a["phys"], wall.numpy_relu2)) for c in conds)
        print(
            f"  {a['tag']:9s} {len(bad)}/{len(conds)} unphysical, "
            f"bare penalty {pen:.6g}"
        )
        for lab, v in bad:
            print(f"      {lab:62s} {v:+13.6g}")

    print()
    print("--- CS kernel sign structure  P(u) = l2nu*u + l4nu*u^2 ---")
    for a in live:
        l2, l4 = a["phys"]["lambda2_nu"], a["phys"]["lambda4_nu"]
        root = -l2 / l4 if l4 != 0 else np.inf
        if root > 0:
            side = "b_T <" if l2 < 0 else "b_T >"
            print(
                f"  {a['tag']:9s} l2nu={l2:+.6g} l4nu={l4:+.6g}  -> "
                f"anti-damping for {side} {np.sqrt(root):.3g} GeV^-1"
            )
        else:
            print(
                f"  {a['tag']:9s} l2nu={l2:+.6g} l4nu={l4:+.6g}  -> "
                "P >= 0 everywhere"
            )

    # ---- how far apart are the arms in the full 47-parameter model space?
    print()
    print(
        "--- model-parameter distance between arms (theta units, "
        "alphaS EXCLUDED so nothing unblinds) ---"
    )
    keys = [
        n for n in live[0]["names"] if n.startswith(MODEL_PREFIXES) and n != "alphaS"
    ]
    print("  " + " " * 12 + "".join(a["tag"].rjust(W) for a in live))
    for a in live:
        cells = []
        for b in live:
            d = np.array([a["theta"][k] - b["theta"][k] for k in keys])
            cells.append(format(np.linalg.norm(d), ".3f").rjust(W))
        print(f"  {a['tag']:12s}" + "".join(cells))
    print(f"  (L2 over {len(keys)} model parameters)")

    print()
    print("--- card nuisances ---")
    for a in live:
        cn = [n for n in a["names"] if not n.startswith(MODEL_PREFIXES)]
        cv = np.array([a["theta"][n] for n in cn])
        i = int(np.argmax(np.abs(cv)))
        print(
            f"  {a['tag']:9s} n={len(cv)}  max|pull| {abs(cv[i]):.3f} "
            f"({cn[i]})   >2sig: {int((np.abs(cv) > 2).sum())}   "
            f">3sig: {int((np.abs(cv) > 3).sum())}"
        )

    print("COMPARE_ARMS_DONE")


if __name__ == "__main__":
    main()
